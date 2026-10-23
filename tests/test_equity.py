import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from equity import buyout, vesting
from equity.captable import CapTable, Holder


class BuyoutTests(unittest.TestCase):
    def test_pieces_add_up_exactly(self):
        units = buyout.split_by_payment({"a": 400, "b": 250, "c": 100}, 100_000)
        self.assertEqual(sum(units.values()), 100_000)

    def test_proportional(self):
        units = buyout.split_by_payment({"a": 260, "b": 240, "c": 150, "d": 100}, 150_000)
        self.assertEqual(units, {"a": 52_000, "b": 48_000, "c": 30_000, "d": 20_000})

    def test_rejects_zero(self):
        with self.assertRaises(ValueError):
            buyout.split_by_payment({"a": 0}, 100)


class VestingTests(unittest.TestCase):
    start = date(2026, 11, 1)

    def test_nothing_before_cliff(self):
        self.assertEqual(vesting.vested_units(48_000, self.start, date(2027, 10, 31)), 0)

    def test_quarter_at_cliff(self):
        self.assertEqual(vesting.vested_units(48_000, self.start, date(2027, 11, 1)), 12_000)

    def test_monthly_after_cliff(self):
        self.assertEqual(vesting.vested_units(48_000, self.start, date(2027, 12, 1)), 13_000)

    def test_fully_vested(self):
        self.assertEqual(vesting.vested_units(48_000, self.start, date(2030, 11, 1)), 48_000)

    def test_month_end_clamp(self):
        self.assertEqual(vesting.add_months(date(2026, 1, 31), 1), date(2026, 2, 28))

    def test_83b_rolls_past_weekend(self):
        # Nov 1, 2026 + 30 days = Dec 1, 2026 (a Tuesday)
        self.assertEqual(vesting.deadline_83b(date(2026, 11, 1)), date(2026, 12, 1))
        # Nov 6, 2026 + 30 days = Dec 6 (a Sunday), so the deadline moves to Monday Dec 7
        self.assertEqual(vesting.deadline_83b(date(2026, 11, 6)), date(2026, 12, 7))


class CapTableTests(unittest.TestCase):
    def table(self):
        return CapTable("X", 1_000_000, [
            Holder("ceo", founder_units=400_000, vesting_start="2026-11-01"),
            Holder("cto", founder_units=200_000, vesting_start="2026-11-01"),
        ])

    def test_voting_exceeds_diluted_when_reserve_exists(self):
        ct = self.table()
        ceo = ct.holders[0]
        self.assertAlmostEqual(ct.fully_diluted_pct(ceo), 40.0)
        self.assertAlmostEqual(ct.voting_pct(ceo), 66.6667, places=3)

    def test_control_report(self):
        c = self.table().control_report()
        self.assertEqual(c["solo_majority"], ["ceo"])
        self.assertEqual(c["supermajority_group"], ["ceo"])

    def test_validate_catches_over_issuance(self):
        ct = CapTable("X", 100, [Holder("a", purchased_units=150)])
        self.assertTrue(any("exceed" in p for p in ct.validate()))

    def test_validate_requires_vesting_start(self):
        ct = CapTable("X", 100, [Holder("a", founder_units=10)])
        self.assertTrue(any("vesting start" in p for p in ct.validate()))


class EndToEnd(unittest.TestCase):
    def test_sample_run_writes_outputs(self):
        with tempfile.TemporaryDirectory() as out:
            r = subprocess.run([sys.executable, os.path.join(ROOT, "run.py"), "--out", out],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("cap_table.md", "members_consent.md", "cap_table.csv"):
                self.assertTrue(os.path.exists(os.path.join(out, f)))
            with open(os.path.join(out, "cap_table.md")) as f:
                self.assertIn("Avery Chen", f.read())


if __name__ == "__main__":
    unittest.main()
