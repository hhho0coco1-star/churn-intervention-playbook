# -*- coding: utf-8 -*-
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import breakeven as be


class TestBreakeven(unittest.TestCase):
    def test_normal_case_matches_hand_calc(self):
        r = be.breakeven(40000, 0.30, 0.10)
        self.assertFalse(r["auto_block"])
        self.assertAlmostEqual(r["threshold"], 0.5, places=6)

    def test_discount_ge_margin_flags_auto_block(self):
        r = be.breakeven(40000, 0.30, 0.30)
        self.assertTrue(r["auto_block"])
        self.assertIsNone(r["threshold"])

    def test_discount_gt_margin_flags_auto_block(self):
        r = be.breakeven(40000, 0.20, 0.30)
        self.assertTrue(r["auto_block"])
        self.assertIsNone(r["threshold"])

    def test_larger_discount_needs_more_incremental(self):
        t1 = be.breakeven(40000, 0.40, 0.10)["threshold"]
        t2 = be.breakeven(40000, 0.40, 0.20)["threshold"]
        self.assertLess(t1, t2)

    def test_invalid_inputs_raise(self):
        for bad in [(-1, 0.3, 0.1), (40000, 0, 0.1), (40000, 1.2, 0.1),
                    (40000, 0.3, 0), (40000, 0.3, 1.0)]:
            with self.assertRaises(ValueError):
                be.breakeven(*bad)

    def test_output_carries_disclaimer(self):
        r = be.breakeven(40000, 0.30, 0.10)
        self.assertIn("holdout", r["note"].lower())


if __name__ == "__main__":
    unittest.main()
