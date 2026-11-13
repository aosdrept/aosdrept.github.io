"""Check generated pages, not templates. Run after scripts/build.py."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1] / "dist"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.links, self.errors = set(), [], []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f'Duplicate ID: {attrs["id"]}')
            self.ids.add(attrs["id"])
        if tag == "img" and "alt" not in attrs:
            self.errors.append("Image is missing alternative text")
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


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
    print(f"Checked {len(pages)} pages: links, assets, anchors, image alternatives and public output.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
