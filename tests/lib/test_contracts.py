import json
import tempfile
import unittest
from pathlib import Path

from src.lib import contracts


def make_cdb(lines):
    return {"sheets": [{"name": "contract", "lines": lines}]}


class ParseContractTests(unittest.TestCase):
    def test_full_contract_excludes_title_and_guid(self):
        row = {
            "id": "Tuto", "guid": "#abc", "title": "Module Kit Sample",
            "client": "Stellar", "npc": "CorpoContract_Tuto", "level": 1, "duration": 0,
            "creditFormula": 57.75, "creditFormula__f": "contractCredits",
            "items": [{"item": "ModuleCasing1", "qty": 3}],
            "rewards": [{"count": 60, "item": "CorpoCredits"}],
            "props": {"creditFactor": 0.5},
        }
        self.assertEqual(contracts.parse_contract(row), {
            "id": "Tuto", "client": "Stellar", "npc": "CorpoContract_Tuto",
            "level": 1, "duration": 0, "creditFormula": 57.75,
            "items": [{"item": "ModuleCasing1", "qty": 3}],
            "rewards": [{"item": "CorpoCredits", "count": 60}],
            "props": {"creditFactor": 0.5},
        })

    def test_empty_items_rewards_props_omitted(self):
        rec = contracts.parse_contract({"id": "X", "items": [], "rewards": [], "props": {}})
        self.assertNotIn("items", rec)
        self.assertNotIn("rewards", rec)
        self.assertNotIn("props", rec)

    def test_missing_id_returns_none(self):
        self.assertIsNone(contracts.parse_contract({"title": "x"}))


class ParseContractsTests(unittest.TestCase):
    def _run(self, lines):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps(make_cdb(lines)), encoding="utf-8")
            return contracts.parse_contracts(path)

    def test_envelope_and_count(self):
        result = self._run([
            {"id": "A"}, {"id": "B"}, {"title": "no id"}, "not-a-dict",
        ])
        self.assertEqual(result["sheet"], "contract")
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["skipped"], 2)
        self.assertEqual(set(result["contracts"]), {"A", "B"})

    def test_duplicate_id_raises(self):
        with self.assertRaises(ValueError):
            self._run([{"id": "A"}, {"id": "A"}])

    def test_missing_sheet_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.cdb"
            path.write_text(json.dumps({"sheets": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                contracts.parse_contracts(path)


if __name__ == "__main__":
    unittest.main()
