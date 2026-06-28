import re
import unittest

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()

# Typer renders help via Rich, which styles each character span with ANSI codes
# (so "--data" can arrive split across escape sequences). Strip them before
# asserting on the plain text so the tests don't depend on color settings.
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def plain(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)

EXPECTED_COMMANDS = [
    "extract",
    "parse-items",
    "parse-craft",
    "parse-workshops",
    "parse-contracts",
    "parse-item-categories",
    "parse-space-objects",
    "parse-factions",
    "parse-translations",
    "generate-icons",
    "deduplicate-icons",
    "pipeline",
    "serve",
]


class CliTests(unittest.TestCase):
    def test_help_lists_all_commands(self):
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        output = plain(result.output)
        for name in EXPECTED_COMMANDS:
            self.assertIn(name, output)

    def test_no_args_shows_usage(self):
        result = runner.invoke(app, [])
        self.assertIn("Usage", plain(result.output))

    def test_command_help_works(self):
        result = runner.invoke(app, ["parse-items", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--data", plain(result.output))


if __name__ == "__main__":
    unittest.main()
