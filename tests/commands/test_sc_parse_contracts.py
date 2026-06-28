import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.commands import parse_contracts as cmd

SAMPLE = {"source": "x", "sheet": "contract", "count": 0, "skipped": 0, "contracts": {}}


class ParseContractsCommandTests(unittest.TestCase):
    def test_run_resolves_default_data(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.contracts.parse_contracts", return_value=SAMPLE) as m:
                code = cmd.run(out=os.devnull, dry_run=True)
        self.assertEqual(code, 0)
        self.assertEqual(m.call_args.args[0], "unpacked/data.cdb")

    def test_env_then_cli_precedence(self):
        with mock.patch.dict(os.environ, {"SC_DATA": "env.cdb"}, clear=True):
            with mock.patch("src.lib.contracts.parse_contracts", return_value=SAMPLE) as m:
                cmd.run(out=os.devnull, dry_run=True)
                self.assertEqual(m.call_args.args[0], "env.cdb")
                cmd.run(data="cli.cdb", out=os.devnull, dry_run=True)
                self.assertEqual(m.call_args.args[0], "cli.cdb")

    def test_dry_run_writes_nothing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.contracts.parse_contracts", return_value=SAMPLE):
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "contracts.json"
                    cmd.run(out=str(out), dry_run=True)
                    self.assertFalse(out.exists())

    def test_writes_json_to_resolved_out(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.contracts.parse_contracts", return_value=SAMPLE):
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "sub" / "contracts.json"
                    cmd.run(out=str(out))
                    self.assertTrue(out.exists())
                    self.assertEqual(
                        json.loads(out.read_text(encoding="utf-8"))["sheet"], "contract")

    def test_returns_1_on_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("src.lib.contracts.parse_contracts", side_effect=ValueError("boom")):
                code = cmd.run(out=os.devnull, dry_run=True)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
