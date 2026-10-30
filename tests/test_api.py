import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from chronotrace_memory import query_bundle


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "alice.json"


class SnapshotApiTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def query(self, **overrides):
        options = dict(entity="Alice", attribute="home_city", intent="current", as_of="2026-08-01")
        options.update(overrides)
        return query_bundle(self.bundle, **options)

    def test_current_state_is_not_late_correction(self):
        result = self.query()
        self.assertEqual(result["answer_values"], ["Berlin"])
        self.assertEqual(result["resolution"], "resolved")
        self.assertEqual(len(result["relations"]), 1)

    def test_historical_state_uses_correction_target_interval(self):
        result = self.query(intent="past", as_of="2026-02-01")
        self.assertEqual(result["answer_values"], ["Lyon"])
        self.assertEqual(result["evidence"][0]["source_id"], "s3")

    def test_recorded_time_blocks_future_knowledge(self):
        result = self.query(intent="past", as_of="2026-02-01", known_at="2026-03-01")
        self.assertEqual(result["answer_values"], ["Paris"])
        self.assertEqual(result["relations"], [])

    def test_history_keeps_incorrect_assertion_and_all_sources(self):
        result = self.query(intent="history", as_of=None)
        self.assertEqual(result["answer_values"], ["Paris", "Berlin", "Lyon"])
        self.assertEqual({e["source_id"] for e in result["evidence"]}, {"s1", "s2", "s3"})
        self.assertIn("corrected_or_retracted", result["statuses"].values())

    def test_entity_and_attribute_filters_remain_separate(self):
        self.assertEqual(self.query(attribute="work_city")["answer_values"], ["Rome"])
        self.assertEqual(self.query(entity="Bob")["answer_values"], ["Madrid"])

    def test_raw_sources_and_events_are_unchanged(self):
        before = copy.deepcopy(self.bundle)
        self.assertTrue(self.query()["raw_sources_unchanged"])
        self.assertEqual(self.bundle, before)

    def test_unanchored_value_is_reported_and_not_selected(self):
        self.bundle["events"][1]["value"] = "Invented city"
        result = self.query()
        self.assertTrue(any(x["reason"] == "unanchored_value" for x in result["rejected"]))
        self.assertNotIn("Invented city", result["answer_values"])

    def test_append_only_ledger_is_separate_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "derived.sqlite3"
            self.query(ledger_path=path)
            self.query(ledger_path=path)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM assertions").fetchone()[0], 5)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM relations").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM projections").fetchone()[0], 1)
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("DELETE FROM assertions")

    def test_cli_refuses_source_file_as_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.json"
            source.write_bytes(EXAMPLE.read_bytes())
            before = source.read_bytes()
            run = subprocess.run([sys.executable, "-m", "chronotrace_memory", "--input", str(source),
                                  "--ledger", str(source)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("different files", run.stderr)
            self.assertEqual(source.read_bytes(), before)

    def test_invalid_date_and_duplicate_source_id_fail_explicitly(self):
        with self.assertRaises(ValueError):
            self.query(as_of="not-a-date")
        self.bundle["sources"][1]["source_id"] = "s1"
        with self.assertRaisesRegex(ValueError, "unique"):
            self.query()


if __name__ == "__main__":
    unittest.main()
