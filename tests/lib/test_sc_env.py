import os
import unittest
from unittest import mock

from src.lib import config
from src.lib.env import resolve


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.setting = config.PARSE_ITEMS_OUT  # SC_PARSE_ITEMS_OUT / generated/items.json

    def test_default_used_when_no_cli_and_no_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve(None, self.setting), "generated/items.json")

    def test_env_used_when_no_cli(self):
        with mock.patch.dict(os.environ, {self.setting.env: "from_env.json"}, clear=True):
            self.assertEqual(resolve(None, self.setting), "from_env.json")

    def test_cli_overrides_env(self):
        with mock.patch.dict(os.environ, {self.setting.env: "from_env.json"}, clear=True):
            self.assertEqual(resolve("from_cli.json", self.setting), "from_cli.json")

    def test_empty_env_falls_back_to_default(self):
        with mock.patch.dict(os.environ, {self.setting.env: ""}, clear=True):
            self.assertEqual(resolve(None, self.setting), "generated/items.json")

    def test_cli_value_coerced_to_str(self):
        from pathlib import Path
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve(Path("a/b.json"), self.setting), str(Path("a/b.json")))

    def test_all_settings_unique_env_names(self):
        names = [s.env for s in config.ALL_SETTINGS]
        self.assertTrue(all(n.startswith("SC_") for n in names))


if __name__ == "__main__":
    unittest.main()
