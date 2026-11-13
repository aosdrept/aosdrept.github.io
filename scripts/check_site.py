"""Check generated pages, not templates. Run after scripts/build.py."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1] / "dist"
REQUIRED_POLICY = {
    "default-src": "'none'", "script-src": "'self'", "style-src": "'self'",
    "img-src": "'self'", "font-src": "'self'", "connect-src": "'none'",
    "object-src": "'none'", "frame-src": "'none'", "base-uri": "'none'",
    "form-action": "'none'",
}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.links, self.errors = set(), [], []
        self.policy, self.referrer, self.in_script = {}, None, False
        self.feed(path.read_text(encoding="utf-8"))
        for directive, value in REQUIRED_POLICY.items():
            if self.policy.get(directive) != value:
                self.errors.append(f"Missing or unsafe Content Security Policy: {directive}")
        if self.referrer != "no-referrer":
            self.errors.append("Missing referrer protection")

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "content-security-policy":
            for directive in attrs.get("content", "").split(";"):
                parts = directive.strip().split(None, 1)
                if len(parts) == 2:
                    self.policy[parts[0]] = parts[1]
        if tag == "meta" and attrs.get("name") == "referrer":
            self.referrer = attrs.get("content")
        if any(name.startswith("on") for name in attrs):
            self.errors.append("Inline event handler is not allowed")
        if tag == "style" or "style" in attrs:
            self.errors.append("Inline styling is not allowed")
        if tag == "script":
            self.in_script = True
            source = urlsplit(attrs.get("src", ""))
            if source.scheme or source.netloc or Path(source.path).name != "site.js":
                self.errors.append("Only the local site.js script is allowed")
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f'Duplicate ID: {attrs["id"]}')
            self.ids.add(attrs["id"])
        if tag == "img" and "alt" not in attrs:
            self.errors.append("Image is missing alternative text")
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])

    def handle_data(self, data):
        if self.in_script and data.strip():
            self.errors.append("Inline script is not allowed")

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False


def check():
    pages = {path: Page(path) for path in ROOT.rglob("*.html")}
    errors = []
    for path, page in pages.items():
        errors.extend(f"{path.relative_to(ROOT)}: {e}" for e in page.errors)
        if "<!-- GENERATED:" in path.read_text(encoding="utf-8"):
            errors.append(f"Unrendered content marker: {path}")
        for link in page.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path.startswith("/"):
                target = ROOT / unquote(parsed.path).lstrip("/")
            else:
                target = path.parent / unquote(parsed.path) if parsed.path else path
            target = target.resolve()
            if not target.is_relative_to(ROOT.resolve()):
                errors.append(f"{path.relative_to(ROOT)}: link escapes public output: {link}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{path.relative_to(ROOT)}: missing {link}")
            elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f"{path.relative_to(ROOT)}: missing anchor {link}")
    for name in ("index.html", "evenimente.html"):
        if pages[ROOT / name].ids != pages[ROOT / "en" / name].ids:
            errors.append(f"Bilingual anchors differ: {name}")
    # Only the explicit public build belongs in the deployment artifact.
    for forbidden in ("content", "scripts", "tests", "templates", ".git", ".pages.yml"):
        if (ROOT / forbidden).exists():
            errors.append(f"Source file in deployment: {forbidden}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Checked {len(pages)} pages: links, assets, anchors, image alternatives, browser policy and public output.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
