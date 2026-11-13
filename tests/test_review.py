"""Review the whole unpublished batch, including withdrawals and changed photos."""
from datetime import datetime
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from scripts import build, review


class PublicationReviewTests(unittest.TestCase):
    def test_baseline_skips_waiting_rejected_and_inactive_deployments(self):
        responses = {
            "repos/a/b/deployments?environment=github-pages&per_page=100&page=1": [
                {"id": 4, "sha": "draft"}, {"id": 3, "sha": "rejected"},
                {"id": 2, "sha": "inactive"}, {"id": 1, "sha": "live"}],
            "repos/a/b/deployments/4/statuses?per_page=1": [{"state": "waiting"}],
            "repos/a/b/deployments/3/statuses?per_page=1": [{"state": "failure"}],
            "repos/a/b/deployments/2/statuses?per_page=1": [{"state": "inactive"}],
            "repos/a/b/deployments/1/statuses?per_page=1": [{"state": "success"}],
        }
        self.assertEqual(review.live_revision("a/b", responses.__getitem__), "live")
        self.assertIsNone(review.live_revision("a/b", lambda _: []))

    def test_review_identifies_withdrawal_deletion_and_replaced_photo(self):
        old = {
            "hidden.json": {"visible": True}, "deleted.json": {"visible": True},
            "photo.json": {"visible": True, "photos": [{"image": "/assets/uploads/event.jpg"}]},
        }
        new = {
            "hidden.json": {"visible": False}, "draft.json": {"visible": False},
            "photo.json": old["photo.json"],
        }
        changes = {path: status for path, status, _, _ in review.entry_changes(old, new, {"assets/uploads/event.jpg"})}
        self.assertIn("Removed", changes["hidden.json"])
        self.assertIn("Removed", changes["deleted.json"])
        self.assertIn("Draft excluded", changes["draft.json"])
        self.assertIn("Updated", changes["photo.json"])

    def test_time_warnings_do_not_reclassify_events(self):
        entry = {"status": "announced", "published_date": "2026-11-15",
                 "date": "2026-11-10", "registration_deadline": "2026-11-09T23:59"}
        now = datetime(2026, 11, 13, 12, tzinfo=build.BUCHAREST)
        self.assertEqual(len(review.timing_notes(entry, now)), 3)
        self.assertEqual(entry["status"], "announced")

    def test_report_compares_all_saves_since_live_and_escapes_draft_titles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def run(*args):
                return subprocess.check_output(["git", *args], cwd=root).decode().strip()
            def commit():
                run("add", ".")
                run("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Fixture")
                return run("rev-parse", "HEAD")
            run("init", "-q")
            content = root / "content/activities"
            content.mkdir(parents=True)
            (root / "README.md").write_text("Initial")
            base = commit()
            (content / "first.json").write_text(json.dumps({"visible": False, "ro": {"title": "<img src=x onerror=bad>"}}))
            commit()
            (content / "second.json").write_text(json.dumps({"visible": False}))
            head = commit()
            result = review.report(root, "a/b", base, head)
            self.assertIn("first.json", result)
            self.assertIn("second.json", result)
            self.assertIn(f"compare/{base}...{head}", result)
            self.assertIn("&lt;img", result)
            self.assertNotIn("<img src=x", result)
            entry = {
                "visible": True, "kind": "event", "status": "announced",
                "published_date": "2026-11-13",
                "ro": {"title": "Titlu RO", "summary": "Rezumat", "body": "<p>Descriere RO.</p>"},
                "en": {"title": "EN title", "summary": "Summary", "body": "<p>EN description.</p>"},
            }
            (content / "included.json").write_text(json.dumps(entry))
            head = commit()
            result = review.report(root, "a/b", base, head)
            self.assertIn("Descriere RO.", result)
            self.assertIn("EN description.", result)
            self.assertIn(f"blob/{head}/content/activities/included.json", result)


if __name__ == "__main__":
    unittest.main()
