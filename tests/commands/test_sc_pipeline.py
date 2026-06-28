import unittest
from unittest import mock

from src.commands import pipeline as cmd


class PipelineTests(unittest.TestCase):
    def test_step_names_in_order(self):
        names = [name for name, _ in cmd.STEPS]
        self.assertEqual(names, [
            "parse-items", "parse-craft", "parse-workshops", "parse-contracts",
            "parse-item-categories", "parse-space-objects", "parse-factions",
            "parse-translations", "generate-icons",
            "generate-icons-categories", "generate-icons-factions",
        ])

    def test_runs_all_steps(self):
        with mock.patch("src.commands.parse_items.run", return_value=0), \
             mock.patch("src.commands.parse_craft.run", return_value=0), \
             mock.patch("src.commands.parse_workshops.run", return_value=0), \
             mock.patch("src.commands.parse_contracts.run", return_value=0), \
             mock.patch("src.commands.parse_item_categories.run", return_value=0), \
             mock.patch("src.commands.parse_space_objects.run", return_value=0), \
             mock.patch("src.commands.parse_factions.run", return_value=0), \
             mock.patch("src.commands.parse_translations.run", return_value=0), \
             mock.patch("src.commands.generate_icons.run", return_value=0):
            self.assertEqual(cmd.run(), 0)

    def test_aborts_on_first_failure(self):
        # All steps before the failing one must be mocked too, otherwise they run
        # for real against unpacked/ (absent in CI) and abort with the wrong code.
        with mock.patch("src.commands.parse_items.run", return_value=0), \
             mock.patch("src.commands.parse_craft.run", return_value=0), \
             mock.patch("src.commands.parse_workshops.run", return_value=0), \
             mock.patch("src.commands.parse_contracts.run", return_value=0), \
             mock.patch("src.commands.parse_item_categories.run", return_value=0), \
             mock.patch("src.commands.parse_space_objects.run", return_value=0), \
             mock.patch("src.commands.parse_factions.run", return_value=0), \
             mock.patch("src.commands.parse_translations.run", return_value=3), \
             mock.patch("src.commands.generate_icons.run", return_value=0) as gen:
            code = cmd.run()
        self.assertEqual(code, 3)
        gen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
