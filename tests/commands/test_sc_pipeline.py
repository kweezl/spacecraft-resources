import unittest
from unittest import mock

from src.commands import pipeline as cmd


class PipelineTests(unittest.TestCase):
    def test_runs_all_steps_in_order(self):
        calls = []
        with mock.patch("src.commands.parse_items.run", side_effect=lambda **k: calls.append("parse-items") or 0), \
             mock.patch("src.commands.parse_translations.run", side_effect=lambda **k: calls.append("parse-translations") or 0), \
             mock.patch("src.commands.generate_icons.run", side_effect=lambda **k: calls.append("generate-icons") or 0), \
             mock.patch("src.commands.deduplicate_icons.run", side_effect=lambda **k: calls.append("deduplicate-icons") or 0):
            code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            calls,
            ["parse-items", "parse-translations", "generate-icons", "deduplicate-icons"],
        )

    def test_aborts_on_first_failure(self):
        with mock.patch("src.commands.parse_items.run", return_value=0), \
             mock.patch("src.commands.parse_translations.run", return_value=3), \
             mock.patch("src.commands.generate_icons.run", return_value=0) as gen, \
             mock.patch("src.commands.deduplicate_icons.run", return_value=0):
            code = cmd.run()
        self.assertEqual(code, 3)
        gen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
