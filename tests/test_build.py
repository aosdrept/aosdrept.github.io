"""Regression checks for future editors adding, changing or hiding activities."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import tempfile
import unittest

from scripts import build


class ActivityPublishingTests(unittest.TestCase):
    def setUp(self):
        # A self-contained fixture: editors may freely change the real entries.
        self.entry = {
            "id": "proces-simulat-drept-civil-2026", "visible": True,
            "featured": True, "kind": "event", "status": "announced",
            "published_date": "2026-11-05", "date": "2026-12-08",
            "registration_deadline": "2026-11-14T23:59",
            "registration_url": "https://example.org/register",
            "source_url": "https://example.org/announcement",
            "deadlines": [{"date": "2026-11-21T23:59", "label_ro": "Speță", "label_en": "Case"}],
            "ro": {"title": "Proces simulat", "summary": "Rezumat", "body": "<p>Detalii.</p>"},
            "en": {"title": "Civil law", "summary": "Summary", "body": "<p>Details.</p>"},
        }

    def test_migrated_event_keeps_dates_and_languages(self):
        build.validate(self.entry)
        for lang, title, month in (("ro", "Proces simulat", "noiembrie"), ("en", "Civil law", "November")):
            rendered = build.event_html(self.entry, lang)
            self.assertIn(title, rendered)
            self.assertIn(f"14 {month} 2026, 23:59", rendered)
            self.assertIn(f"21 {month} 2026, 23:59", rendered)
            self.assertIn('2026-11-14T23:59:00+02:00', rendered)
            self.assertIn('id="proces-simulat-drept-civil-2026"', rendered)

    def test_missing_translation_stops_publication(self):
        self.entry["en"]["title"] = ""
        with self.assertRaisesRegex(ValueError, "title"):
            build.validate(self.entry)

    def test_empty_rich_text_is_not_a_completed_translation(self):
        self.entry["en"]["body"] = "<p><br></p><p>&nbsp;</p>"
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            build.validate(self.entry)

    def test_invalid_date_and_reversed_range_stop_publication(self):
        self.entry["date"] = "2026-02-30"
        with self.assertRaises(ValueError):
            build.validate(self.entry)
        self.entry["date"] = "2026-12-08"
        self.entry["end_date"] = "2026-12-07"
        with self.assertRaises(ValueError):
            build.validate(self.entry)

    def test_hidden_entries_are_not_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            content = root / "content/activities"
            content.mkdir(parents=True)
            (content / "hidden.json").write_text(json.dumps({"visible": False}))
            (content / "visible.json").write_text(json.dumps(self.entry))
            self.assertEqual([e["id"] for e in build.load_entries(root)], ["visible"])

    def test_multiple_entries_get_unique_headings_and_year_groups(self):
        other = deepcopy(self.entry)
        other.update(id="another-project", kind="project", date="2027-02-01")
        result = build.events_html([other, self.entry], "en")
        self.assertIn('id="year-2027"', result)
        self.assertIn('id="year-2026"', result)
        self.assertIn('id="another-project-title"', result)
        self.assertEqual(result.count('id="proces-simulat-drept-civil-2026-title"'), 1)

    def test_featured_choice_is_predictable_and_has_fallback(self):
        newer = {**self.entry, "id": "newer", "published_date": "2026-11-13", "featured": False}
        self.assertEqual(build.featured_entry([self.entry, newer])["id"], self.entry["id"])
        self.entry["featured"] = False
        self.assertEqual(build.featured_entry([self.entry, newer])["id"], "newer")
        self.assertIsNone(build.featured_entry([]))
        self.assertIn("Anunțurile", build.events_html([], "ro"))

    def test_links_and_rich_text_cannot_inject_script(self):
        for url in ("javascript:alert(1)", "data:text/html,test", "https://example.org\n", "https://name:secret@example.org"):
            with self.assertRaises(ValueError):
                build.safe_url(url)
        for html in ('<script>alert(1)</script>', '<a href="javascript:alert(1)">Click</a>', '<img src="https://example.org/pixel">'):
            with self.assertRaises(ValueError):
                build.rich_text(html)
        self.assertEqual(build.rich_text('<p onclick="bad()">Safe &amp; sound</p>'), '<p>Safe &amp; sound</p>')
        self.assertEqual(build.rich_text('<h2>Details</h2>'), '<h4>Details</h4>')

    def test_photos_need_existing_upload_and_both_descriptions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            images = root / "assets/uploads"
            images.mkdir(parents=True)
            (images / "photo.jpg").write_bytes(b"fixture")
            self.entry["photos"] = [{"image": "/assets/uploads/photo.jpg", "alt_ro": "Descriere"}]
            with self.assertRaisesRegex(ValueError, "alt_en"):
                build.validate(self.entry, root)
            self.entry["photos"][0]["alt_en"] = "Description"
            build.validate(self.entry, root)
            self.entry["photos"][0]["image"] = "/assets/uploads/../../private.jpg"
            with self.assertRaises(ValueError):
                build.validate(self.entry, root)

    def test_cancelled_event_keeps_source_but_not_registration_action(self):
        self.entry["status"] = "cancelled"
        html = build.event_html(self.entry, "en")
        self.assertIn("Cancelled", html)
        self.assertIn(self.entry["source_url"], html)
        self.assertNotIn(self.entry["registration_url"], html)

    def test_full_build_handles_new_projects_and_an_empty_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ("pages", "assets", "documents"):
                shutil.copytree(build.ROOT / name, root / name)
            for name in ("style.css", "site.js", "COPYRIGHT.txt"):
                shutil.copy2(build.ROOT / name, root / name)
            content = root / "content/activities"
            content.mkdir(parents=True)
            second = deepcopy(self.entry)
            second.update(kind="project", published_date="2027-01-01", date="2027-02-01")
            second["ro"]["title"] = "Proiect nou"
            second["en"]["title"] = "New project"
            (content / "first-event.json").write_text(json.dumps(self.entry))
            (content / "new-project.json").write_text(json.dumps(second))
            uploads = root / "assets/uploads"
            uploads.mkdir(exist_ok=True)
            (uploads / "unused.jpg").write_bytes(b"draft upload")
            (uploads / "included.jpg").write_bytes(b"included upload")
            self.entry["photos"] = [{"image": "/assets/uploads/included.jpg", "alt_ro": "Descriere", "alt_en": "Description"}]
            (content / "first-event.json").write_text(json.dumps(self.entry))
            build.build(root)
            self.assertTrue((root / "dist/assets/uploads/included.jpg").exists())
            self.assertFalse((root / "dist/assets/uploads/unused.jpg").exists())
            for lang, title in (("ro", "Proiect nou"), ("en", "New project")):
                base = root / "dist" if lang == "ro" else root / "dist/en"
                self.assertIn(title, (base / "index.html").read_text())
                archive = (base / "evenimente.html").read_text()
                self.assertIn('id="first-event"', archive)
                self.assertIn('id="new-project"', archive)
                self.assertNotIn("<!-- GENERATED:", archive)
            self.assertFalse((root / "dist/content").exists())
            for path in content.glob("*.json"):
                path.write_text(json.dumps({"visible": False}))
            build.build(root)
            self.assertNotIn('class="event-entry" id=', (root / "dist/evenimente.html").read_text())

    def test_summer_times_use_romanian_daylight_saving_offset(self):
        self.assertIn('2027-07-01T10:30:00+03:00', build.time_html("2027-07-01T10:30", "en"))


if __name__ == "__main__":
    unittest.main()
