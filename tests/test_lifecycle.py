import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from chronotrace_memory import lifecycle as m


def event(value, recorded, valid=None, **kw):
    x = dict(entity="alice", attribute="home_city", qualifier="", value=value, quote=value,
             kind="ASSERT", target_quote="", cardinality="single", past_only=False,
             recorded_at=recorded, valid_start=valid, valid_end=None, request=None,
             session=None, position=0, start=0, end=len(value), source_id=value)
    x.update(kw)
    x["id"] = m.digest(x)
    return x


class LifecycleTests(unittest.TestCase):
    def test_current_and_previous(self):
        old, new = event("Paris", 100), event("Berlin", 200)
        self.assertEqual(m.project([old, new], "current")[0], [new])
        self.assertEqual(m.project([old, new], "past")[0], [old])

    def test_valid_time_differs_from_record_time(self):
        old, new = event("Paris", 300, 100), event("Berlin", 200, 150)
        self.assertEqual(m.project([old, new], "current")[0], [new])
        self.assertEqual(m.project([old, new], "past", as_of=125)[0], [old])
        self.assertEqual(m.project([old, new], "past", as_of=125, known_at=250)[0], [])

    def test_late_correction_and_known_at(self):
        old = event("Paris", 100, 50)
        correction = event("Lyon", 300, 50, kind="CORRECT", target_quote="Paris")
        selected, relations, _ = m.project([old, correction], "past", as_of=100)
        self.assertEqual(selected, [correction])
        self.assertEqual(len(relations), 1)
        self.assertEqual(m.project([old, correction], "past", 100, 200)[0], [old])
        self.assertEqual(len(m.project([old, correction], "history")[0]), 2)

    def test_undated_late_correction_inherits_target_validity(self):
        old, actual_change = event("Paris", 100), event("Berlin", 200)
        correction = event("Lyon", 300, kind="CORRECT", target_quote="Paris")
        chosen, links, status = m.project([old, actual_change, correction], "current")
        self.assertEqual([e["value"] for e in chosen if status[e["id"]] == "selected_current"], ["Berlin"])
        self.assertEqual(links[0]["derived_effective_start"], 100)
        self.assertEqual(m.project([old, actual_change, correction], "past", as_of=150)[0], [correction])
        self.assertEqual(m.project([old, actual_change, correction], "past", as_of=150, known_at=250)[0], [old])

    def test_correction_chain_inherits_original_validity(self):
        a = event("Paris", 100)
        b = event("Lyon", 300, kind="CORRECT", target_quote="Paris")
        c = event("Nice", 400, kind="CORRECT", target_quote="Lyon")
        state = event("Berlin", 200)
        chosen, links, status = m.project([c, state, b, a], "current")
        self.assertEqual([e["value"] for e in chosen if status[e["id"]] == "selected_current"], ["Berlin"])
        self.assertTrue(all(x["derived_effective_start"] == 100 for x in links))

    def test_unresolved_correction_target_is_not_current_state(self):
        a = event("Paris", 100)
        b = event("Lyon", 300, kind="CORRECT", target_quote="unknown quote")
        chosen, links, status = m.project([a, b], "current")
        self.assertEqual(len(chosen), 2)
        self.assertEqual(links, [])
        self.assertEqual(set(status.values()), {"unresolved_correction_target"})

    def test_correction_chain_inherits_valid_end(self):
        a = event("Paris", 100, 50, valid_end=150)
        b = event("Lyon", 300, 50, kind="CORRECT", target_quote="Paris")
        c = event("Nice", 400, 50, kind="CORRECT", target_quote="Lyon")
        self.assertEqual([e for e in m.project([c, b, a], "current", as_of=200)[0] if e["kind"] == "ASSERT"], [])
        self.assertFalse(any(v == "selected_current" for v in m.project([c, b, a], "current", as_of=200)[2].values()))

    def test_shared_keywords_do_not_merge_ownership_or_slots(self):
        a = event("Paris", 100)
        b = event("Berlin", 200, entity="bob")
        c = event("Rome", 300, attribute="work_city")
        d = event("Madrid", 400, qualifier="vacation_home")
        self.assertEqual(len(m.project([a, b, c, d], "current")[0]), 4)

    def test_ambiguous_order_is_not_latest_wins(self):
        a, b = event("Paris", None), event("Berlin", None)
        chosen, _, status = m.project([a, b], "current")
        self.assertEqual(len(chosen), 2)
        self.assertEqual(set(status.values()), {"unresolved_order"})

    def test_multivalued_attribute_retained(self):
        a, b = event("cat", 100, cardinality="multi"), event("dog", 200, cardinality="multi")
        self.assertEqual(len(m.project([a, b], "current")[0]), 2)

    def test_foreign_slot_correction_cannot_retract(self):
        a = event("Paris", 100)
        b = event("Berlin", 200, entity="bob", kind="CORRECT", target_quote="Paris")
        self.assertEqual(len(m.project([a, b], "current")[0]), 2)
        self.assertEqual(m.project([a, b], "current")[1], [])

    def test_undated_former_state_not_current(self):
        a = event("Paris", 300, past_only=True)
        b = event("Berlin", 200)
        self.assertEqual(m.project([a, b], "current")[0], [b])
        self.assertEqual(m.project([a, b], "past")[0], [a])

    def test_one_current_state_does_not_prove_previous(self):
        self.assertEqual(m.project([event("Paris", 100)], "past")[0], [])

    def test_expired_or_future_valid_state_excluded(self):
        old = event("Paris", 100, 50, valid_end=150)
        future = event("Berlin", 100, 300)
        self.assertEqual(m.project([old, future], "current", as_of=200)[0], [])

    def test_conflicting_provenance_is_unknown(self):
        a = event("Paris", 100, request="r", session="s", position=2)
        b = event("Berlin", 200, request="r", session="s", position=1)
        self.assertIsNone(m.later(a, b))

    def test_budget_and_source_metadata(self):
        old = dict(source_id="a", start=0, end=3, header="[user] ", body="old", timestamp=100)
        new = dict(source_id="b", start=0, end=3, header="[user] ", body="new", timestamp=200)
        result = m.prioritize([new], [old], budget=10)
        self.assertEqual(result, [new])
        self.assertEqual(result[0]["timestamp"], 200)

    def test_raw_event_and_ledger_immutable(self):
        a = event("Paris", 100)
        before = copy.deepcopy(a)
        m.project([a, event("Berlin", 200)], "current")
        self.assertEqual(a, before)
        with tempfile.TemporaryDirectory() as folder:
            ledger = m.Ledger(Path(folder) / "derived.sqlite3")
            ledger.append("assertions", "user", a)
            with self.assertRaises(sqlite3.IntegrityError):
                ledger.db.execute("DELETE FROM assertions")
            with self.assertRaises(sqlite3.IntegrityError):
                ledger.db.execute("UPDATE assertions SET payload='{}'")
            ledger.db.close()

    def test_provenance_and_date_validation(self):
        pool = [dict(source_id="s", body="My home city is Paris.", start=0, role="user", speaker="Alice", timestamp=100)]
        raw = dict(entity="@speaker", attribute="home_city", qualifier="", value="Paris", quote=pool[0]["body"],
                   source=0, kind="ASSERT", valid_from="", valid_to="", target_quote="", past_only=False, cardinality="single")
        good, rejected = m.validate_events({"events": [raw]}, pool)
        self.assertEqual((len(good), rejected), (1, []))
        bad = {**raw, "value": "Berlin"}
        self.assertEqual(len(m.validate_events({"events": [bad]}, pool)[0]), 0)
        bad = {**raw, "source": -1}
        self.assertEqual(len(m.validate_events({"events": [bad]}, pool)[0]), 0)
        self.assertRaises(ValueError, m.explicit_date, "2026-01-01", "yesterday")


if __name__ == "__main__":
    unittest.main()
