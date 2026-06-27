import unittest
from pathlib import Path

from src.lib import config

ENV_EXAMPLE = Path(__file__).resolve().parent / ".env.example"


class EnvExampleTests(unittest.TestCase):
    def test_documents_every_setting(self):
        text = ENV_EXAMPLE.read_text(encoding="utf-8")
        for setting in config.ALL_SETTINGS:
            self.assertIn(setting.env, text, f"{setting.env} missing from .env.example")

    def test_contains_no_uncommented_assignments(self):
        # Every SC_ line must be commented so the file carries no real values.
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("SC_"):
                self.fail(f"Uncommented assignment in .env.example: {line!r}")


if __name__ == "__main__":
    unittest.main()
