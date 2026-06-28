import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
PAGES_ENTRY = ROOT / ".github" / "pages" / "index.html"


class SpaStructureTests(unittest.TestCase):
    def test_single_html_entry_in_server(self):
        htmls = sorted(p.name for p in SERVER.glob("*.html"))
        self.assertEqual(htmls, ["index.html"])

    def test_old_pages_removed(self):
        self.assertFalse((SERVER / "items.html").exists())
        self.assertFalse((SERVER / "recipes.html").exists())

    def test_no_cross_page_html_links(self):
        for html in SERVER.glob("*.html"):
            text = html.read_text(encoding="utf-8")
            self.assertNotRegex(
                text, r'<a\s[^>]*href="[^"]*\.html"', f"{html.name} links to another .html"
            )

    def test_entry_shells_in_sync(self):
        for entry in (SERVER / "index.html", PAGES_ENTRY):
            text = entry.read_text(encoding="utf-8")
            self.assertIn('id="app"', text)
            self.assertIn("data-data-base", text)
            self.assertRegex(text, r'<script[^>]*type="module"[^>]*src="\./app\.js"')
