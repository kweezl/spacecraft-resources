import unittest

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()

EXPECTED_COMMANDS = [
    "extract",
    "parse-items",
    "parse-craft",
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
        for name in EXPECTED_COMMANDS:
            self.assertIn(name, result.output)

    def test_no_args_shows_usage(self):
        result = runner.invoke(app, [])
        self.assertIn("Usage", result.output)

    def test_command_help_works(self):
        result = runner.invoke(app, ["parse-items", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--data", result.output)


if __name__ == "__main__":
    unittest.main()
