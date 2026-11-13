"""Build the bilingual site from Pages CMS entries; Python 3.9+, no packages.

Only pages, public assets and approved documents enter dist/. CMS content and
maintainer files stay in the repository. A validation failure stops deployment.
"""
from datetime import date, datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from string import Template
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BUCHAREST = ZoneInfo("Europe/Bucharest")
LANGUAGES = ("ro", "en")
MONTHS = {
    "ro": "ianuarie februarie martie aprilie mai iunie iulie august septembrie octombrie noiembrie decembrie".split(),
    "en": "January February March April May June July August September October November December".split(),
}
LABELS = {
    "ro": {
        "featured": "Anunț în prim-plan", "published": "Publicat la",
        "details": "Detalii și participare", "registration": "Înscriere",
        "deadline": "Termen de înscriere", "location": "Locul desfășurării",
        "source": "Anunțul original", "links": "Participare și informații",
        "external": "Linkurile duc la platforme externe. Formularele și datele trimise prin acestea sunt gestionate pe platforma de destinație.",
        "timezone": "Orele sunt exprimate în ora locală a României.",
        "empty": "Anunțurile și activitățile vor fi publicate aici. Urmărește și canalele sociale AOSD pentru noutăți.",
        "announced": "Anunțat", "ongoing": "În desfășurare", "completed": "Încheiat", "cancelled": "Anulat",
        "event": "Eveniment", "project": "Proiect",
    },
    "en": {
        "featured": "Featured announcement", "published": "Published on",
        "details": "Details and participation", "registration": "Registration",
        "deadline": "Registration deadline", "location": "Location",
        "source": "Original announcement", "links": "Participation and information",
        "external": "These links open external platforms. Forms and any responses are handled on the destination platform.",
        "timezone": "All times are local to Romania.",
        "empty": "Announcements and activities will appear here. Follow AOSD’s social channels for updates too.",
        "announced": "Announced", "ongoing": "Ongoing", "completed": "Completed", "cancelled": "Cancelled",
        "event": "Event", "project": "Project",
    },
}


def text(value):
    """Escape plain editor text for HTML, including attribute values."""
    return escape(str(value), quote=True)


def safe_url(value, allow_email=False):
    if not isinstance(value, str) or re.search(r"[\s\x00-\x1f]", value):
        raise ValueError("Linkurile nu pot conține spații sau caractere de control.")
    url = urlsplit(value)
    if url.scheme in ("https", "http") and url.netloc and not url.username and not url.password:
        return value
    if allow_email and url.scheme == "mailto" and url.path and "@" in url.path:
        return value
    raise ValueError("Folosește un link complet care începe cu https://.")


class RichText(HTMLParser):
    """Keep normal editor formatting, without scripts, embeds or attributes.

    Photo uploads have their own fields so both alternative texts are required.
    Editor headings become h4 below an event's h3, preserving the outline.
    """
    allowed = {"p", "strong", "b", "em", "i", "u", "s", "ul", "ol", "li", "blockquote", "br", "hr", "a", "code", "pre", "span", "div", "table", "thead", "tbody", "tr", "td", "th"}
    void = {"br", "hr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if re.fullmatch(r"h[1-6]", tag):
            tag = "h4"
        elif tag not in self.allowed:
            raise ValueError(f"Element HTML neacceptat: {tag}. Folosește editorul de text și câmpurile pentru fotografii.")
        attributes = ""
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href:
                attributes = f' href="{text(safe_url(href, allow_email=True))}"'
        self.output.append(f"<{tag}{attributes}>")
        if tag not in self.void:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if re.fullmatch(r"h[1-6]", tag):
            tag = "h4"
        if tag in self.void:
            return
        if not self.stack or self.stack[-1] != tag:
            raise ValueError("Formatarea textului nu este validă; corectează textul în editor.")
        self.stack.pop()
        self.output.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)

    def handle_data(self, data):
        self.output.append(text(data))


def rich_text(value):
    parser = RichText()
    parser.feed(value or "")
    parser.close()
    if parser.stack:
        raise ValueError("Textul formatat are un element HTML neînchis.")
    return "".join(parser.output)


def parse_date(value, with_time=False):
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}" if with_time else r"\d{4}-\d{2}-\d{2}"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError("Data trebuie salvată prin selectorul de dată din editor.")
    return datetime.fromisoformat(value).replace(tzinfo=BUCHAREST) if with_time else date.fromisoformat(value)


def time_html(value, lang):
    with_time = "T" in value
    parsed = parse_date(value, with_time)
    label = f"{parsed.day} {MONTHS[lang][parsed.month - 1]} {parsed.year}"
    if with_time:
        label += f", {parsed:%H:%M}"
    return f'<time datetime="{parsed.isoformat()}">{label}</time>'


def required_string(data, field):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Câmp obligatoriu lipsă: {field}.")
    return value


def validate(entry, root=ROOT):
    """Validate publishable entries before building either language."""
    if not isinstance(entry, dict):
        raise ValueError("Înregistrarea trebuie să fie un obiect JSON.")
    for key in ("visible", "featured"):
        if key in entry and type(entry[key]) is not bool:
            raise ValueError(f"{key} trebuie să fie o opțiune da/nu.")
    if not entry.get("visible", False):
        return
    if entry.get("kind") not in ("event", "project"):
        raise ValueError("Selectează Eveniment sau Proiect.")
    if entry.get("status") not in ("announced", "ongoing", "completed", "cancelled"):
        raise ValueError("Selectează stadiul activității.")
    parse_date(required_string(entry, "published_date"))
    for key in ("date", "end_date"):
        if entry.get(key):
            parse_date(entry[key])
    if entry.get("end_date") and (not entry.get("date") or entry["end_date"] < entry["date"]):
        raise ValueError("Data de sfârșit trebuie să fie după data de început.")
    if entry.get("registration_deadline"):
        parse_date(entry["registration_deadline"], True)
    for key in ("registration_url", "source_url"):
        if entry.get(key):
            safe_url(entry[key])
    for lang in LANGUAGES:
        translation = entry.get(lang, {})
        if not isinstance(translation, dict):
            raise ValueError(f"Completează secțiunea {lang}.")
        required_string(translation, "title")
        required_string(translation, "summary")
        rich_text(required_string(translation, "body"))
    for deadline in entry.get("deadlines") or []:
        parse_date(required_string(deadline, "date"), True)
        for lang in LANGUAGES:
            required_string(deadline, "label_" + lang)
    for photo in entry.get("photos") or []:
        path = required_string(photo, "image")
        image = (root / path.lstrip("/")).resolve()
        upload_root = (root / "assets/uploads").resolve()
        if not image.is_relative_to(upload_root) or image.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") or not image.is_file():
            raise ValueError("Fotografia trebuie încărcată în directorul de imagini al editorului.")
        for lang in LANGUAGES:
            required_string(photo, "alt_" + lang)


def load_entries(root=ROOT):
    entries = []
    for path in sorted((root / "content/activities").glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.stem):
                raise ValueError("Numele fișierului trebuie să conțină doar litere mici, cifre și cratime.")
            validate(entry, root)
            if entry.get("visible", False):
                entries.append({**entry, "id": path.stem})
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError(f"{path.name}: {error}") from error
    return sorted(entries, key=lambda e: (e.get("date") or e["published_date"], e["id"]), reverse=True)


def render_template(name, **values):
    return Template((ROOT / "templates" / name).read_text(encoding="utf-8")).substitute(values)


def featured_entry(entries):
    candidates = [e for e in entries if e.get("featured")] or entries
    return max(candidates, key=lambda e: (e["published_date"], e["id"])) if candidates else None


def date_range(entry, lang):
    if not entry.get("date"):
        return ""
    value = time_html(entry["date"], lang)
    if entry.get("end_date") and entry["end_date"] != entry["date"]:
        value += " – " + time_html(entry["end_date"], lang)
    return value


def announcement(entry, lang):
    labels = LABELS[lang]
    if not entry:
        return f'<p class="announcement-card">{labels["empty"]}</p>'
    deadline = ""
    if entry.get("registration_deadline"):
        deadline = f'<p class="deadline"><strong>{labels["deadline"]}</strong><br>{time_html(entry["registration_deadline"], lang)}</p>'
    return render_template("announcement.html", featured_label=labels["featured"],
        published_label=labels["published"], published_date=time_html(entry["published_date"], lang),
        title=text(entry[lang]["title"]), summary=text(entry[lang]["summary"]),
        deadline=deadline, id=entry["id"], details_label=labels["details"])


def event_html(entry, lang):
    labels = LABELS[lang]
    translation = entry[lang]
    facts = []
    if translation.get("location"):
        facts.append((labels["location"], text(translation["location"])))
    if entry.get("registration_deadline"):
        facts.append((labels["deadline"], time_html(entry["registration_deadline"], lang)))
    for deadline in entry.get("deadlines") or []:
        facts.append((text(deadline["label_" + lang]), time_html(deadline["date"], lang)))
    fact_html = '<dl class="event-dates event-facts">' + "".join(f"<div><dt>{key}</dt><dd>{value}</dd></div>" for key, value in facts) + "</dl>" if facts else ""
    if entry.get("registration_deadline") or entry.get("deadlines"):
        fact_html += f'<p class="note">{labels["timezone"]}</p>'
    photos = []
    for photo in entry.get("photos") or []:
        caption = photo.get("caption_" + lang, "")
        credit = photo.get("credit", "")
        caption = " · ".join(part for part in (caption, credit) if part)
        photos.append(f'<figure><img src="{text(photo["image"])}" alt="{text(photo["alt_" + lang])}" loading="lazy">' + (f'<figcaption>{text(caption)}</figcaption>' if caption else "") + "</figure>")
    photos_html = '<div class="event-photos">' + "".join(photos) + "</div>" if photos else ""
    links = []
    # Preserve past registration links as references without advertising registration after cancellation.
    if entry.get("registration_url") and entry["status"] not in ("completed", "cancelled"):
        links.append(f'<a class="button dark" href="{text(entry["registration_url"])}">{labels["registration"]}</a>')
    if entry.get("source_url"):
        links.append(f'<a class="text-link" href="{text(entry["source_url"])}">{labels["source"]}</a>')
    links_html = f'<section class="event-registration"><h4>{labels["links"]}</h4><div class="event-actions">' + "".join(links) + f'</div><p class="note">{labels["external"]}</p></section>' if links else ""
    return render_template("event.html", id=entry["id"], title=text(translation["title"]),
        status=labels[entry["kind"]] + " · " + labels[entry["status"]], date=date_range(entry, lang),
        summary=text(translation["summary"]), facts=fact_html, body=rich_text(translation["body"]),
        photos=photos_html, links=links_html, published_label=labels["published"],
        published_date=time_html(entry["published_date"], lang))


def events_html(entries, lang):
    if not entries:
        return f'<p class="event-entry">{LABELS[lang]["empty"]}</p>'
    parts, current_year = [], None
    for entry in entries:
        year = (entry.get("date") or entry["published_date"])[:4]
        if year != current_year:
            if current_year:
                parts.append("</section>")
            parts.append(f'<section class="event-year" aria-labelledby="year-{year}"><h2 id="year-{year}">{year}</h2>')
            current_year = year
        parts.append(event_html(entry, lang))
    return "\n".join(parts) + "</section>"


def build(root=ROOT, destination=None):
    entries = load_entries(root)  # Validate first; never replace a good build with bad content.
    destination = destination or root / "dist"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(root / "pages", destination)
    for folder in ("assets", "documents"):
        shutil.copytree(root / folder, destination / folder)
    for file in ("style.css", "site.js", "COPYRIGHT.txt"):
        shutil.copy2(root / file, destination / file)
    featured = featured_entry(entries)
    for lang in LANGUAGES:
        directory = destination if lang == "ro" else destination / "en"
        replacements = {
            "<!-- GENERATED:ANNOUNCEMENT -->": announcement(featured, lang),
            "<!-- GENERATED:EVENTS -->": events_html(entries, lang),
            "<!-- GENERATED:ARCHIVE-PREVIEW -->": f'<p class="archive-date">{date_range(featured, lang)}<br>{text(featured[lang]["title"])}</p>' if featured else "",
        }
        for name in ("index.html", "evenimente.html"):
            path = directory / name
            html = path.read_text(encoding="utf-8")
            for marker, value in replacements.items():
                html = html.replace(marker, value)
            path.write_text(html, encoding="utf-8")
    return entries


if __name__ == "__main__":
    try:
        entries = build()
        print(f"Built dist/: {len(entries)} published activities, Romanian and English.")
    except (ValueError, TypeError, KeyError) as error:
        print(f"Publicarea a fost oprită / Publication stopped: {error}", file=sys.stderr)
        sys.exit(1)
