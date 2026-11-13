"""Security regressions using local fixtures only; no live attack requests."""
from pathlib import Path
import tempfile
import unittest

from scripts import build, check_site


class SecurityTests(unittest.TestCase):
    def test_only_https_and_explicit_email_links_are_accepted(self):
        for url in ("http://example.org/", "//example.org/", "https://example.org\\@other.invalid/",
                    "https://example.org:bad/", "https://example.org/\x7f", "javascript&#58;alert(1)"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                build.safe_url(url)
        self.assertEqual(build.safe_url("https://example.org/?a=1&b=2"), "https://example.org/?a=1&b=2")
        self.assertEqual(build.safe_url("mailto:team@example.org", allow_email=True), "mailto:team@example.org")

    def test_upload_paths_cannot_be_external_encoded_or_traversing(self):
        for path in ("//assets/uploads/photo.jpg", "assets/uploads/photo.jpg",
                     "/assets/uploads/../photo.jpg", "/assets/uploads/%2e%2e/photo.jpg",
                     "/assets/uploads/a\\photo.jpg", "/assets/uploads/a.jpg?x=1",
                     "/assets/uploads/a.jpg#fragment", "/assets/uploads/payload.svg"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                build.upload_path(path)
        self.assertEqual(build.upload_path("/assets/uploads/2026/my-photo.webp"), "assets/uploads/2026/my-photo.webp")

    def test_uploads_check_file_type_and_reject_symlinks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            uploads = root / "assets/uploads"
            uploads.mkdir(parents=True)
            photo = uploads / "photo.jpg"
            photo.write_bytes(b"<html><script>test</script></html>")
            with self.assertRaisesRegex(ValueError, "image format"):
                build.validate_photo("/assets/uploads/photo.jpg", root)
            photo.write_bytes(b"\xff\xd8\xff" + b"fixture")
            build.validate_photo("/assets/uploads/photo.jpg", root)
            (uploads / "alias.jpg").symlink_to(photo)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                build.validate_photo("/assets/uploads/alias.jpg", root)
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                build.reject_public_symlinks(root)

    def test_browser_parser_payloads_cannot_survive_rich_text_filter(self):
        for value in ('<svg><script>alert(1)</script></svg>', '<math><mtext>bad</mtext></math>',
                      '<iframe src="https://example.org"></iframe>', '<base href="https://example.org">',
                      '<a href="java&#x09;script:alert(1)">click</a>',
                      '<a href="javascript&#58;alert(1)">click</a>', '<form action="https://example.org"></form>'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build.rich_text(value)
        cleaned = build.rich_text('<p id="main-nav" style="position:fixed" onclick="bad()">Text &lt;script&gt;</p>')
        self.assertEqual(cleaned, '<p>Text &lt;script&gt;</p>')

    def test_page_checks_reject_policy_regressions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.html"
            path.write_text('<html><script src="https://example.org/x.js"></script><p onclick="bad()">Text</p></html>')
            errors = check_site.Page(path).errors
            self.assertTrue(any("Content Security Policy" in error for error in errors))
            self.assertIn("Inline event handler is not allowed", errors)
            self.assertIn("Only the local site.js script is allowed", errors)
        for path in (build.ROOT / "pages").rglob("*.html"):
            self.assertEqual(check_site.Page(path).errors, [], str(path))


if __name__ == "__main__":
    unittest.main()
