import os
import unittest
from unittest import mock

from src.commands import parse_translations as cmd


class ParseTranslationsCommandTests(unittest.TestCase):
    def test_run_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("parse_translations.main", return_value=0) as m:
                code = cmd.run()
        self.assertEqual(code, 0)
        self.assertEqual(
            m.call_args.args[0],
            [
                "--data", "unpacked/data.cdb",
                "--lang-dir", "unpacked/extra/lang",
                "--out", "generated/i18n",
            ],
        )

    def test_lang_dir_env(self):
        with mock.patch.dict(os.environ, {"SC_PARSE_TRANSLATIONS_LANG_DIR": "langs"}, clear=True):
            with mock.patch("parse_translations.main", return_value=0) as m:
                cmd.run()
        self.assertIn("langs", m.call_args.args[0])

    def test_dry_run(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("parse_translations.main", return_value=0) as m:
                cmd.run(dry_run=True)
        self.assertIn("--dry-run", m.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
