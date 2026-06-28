import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "src" / "public"


class SpaStructureTests(unittest.TestCase):
    def test_single_html_entry_in_public(self):
        htmls = sorted(p.name for p in PUBLIC.glob("*.html"))
        self.assertEqual(htmls, ["index.html"])

    def test_old_server_dir_removed(self):
        self.assertFalse((ROOT / "server").exists(), "legacy server/ dir still present")

    def test_old_pages_shell_removed(self):
        self.assertFalse((ROOT / ".github" / "pages" / "index.html").exists())

    def test_no_cross_page_html_links(self):
        for html in PUBLIC.glob("*.html"):
            text = html.read_text(encoding="utf-8")
            self.assertNotRegex(
                text, r'<a\s[^>]*href="[^"]*\.html"', f"{html.name} links to another .html"
            )

    def test_single_shell_structure(self):
        # One shell serves both local and Pages: data base is the sibling generated/.
        text = (PUBLIC / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="app"', text)
        self.assertIn('data-data-base="./generated"', text)
        self.assertRegex(text, r'<script[^>]*type="module"[^>]*src="\./app\.js"')


if __name__ == "__main__":
    unittest.main()
