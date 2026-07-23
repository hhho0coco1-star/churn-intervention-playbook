# -*- coding: utf-8 -*-
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_playbook as cp

SRC_MD = os.path.join(os.path.dirname(__file__), "..", "references", "public-sources.md")
FIX = os.path.join(os.path.dirname(__file__), "..", "examples", "fixtures")


class TestSourceParser(unittest.TestCase):
    def test_parses_all_source_ids(self):
        rows = cp.parse_sources(SRC_MD)
        ids = {r["id"] for r in rows}
        self.assertTrue({"B1", "C1", "V1", "P1"}.issubset(ids))
        for r in rows:
            self.assertIn("url", r)


class TestJudgmentLinter(unittest.TestCase):
    def test_good_passes(self):
        fails = cp.lint_playbook(os.path.join(FIX, "good_playbook.md"))
        self.assertEqual(fails, [])

    def test_ungated_coupon_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_ungated.md"))
        self.assertTrue(any("게이트" in f for f in fails))

    def test_coupon_without_source_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_nosource.md"))
        self.assertTrue(any("출처" in f for f in fails))

    def test_coupon_but_no_routing_table_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_noheader.md"))
        self.assertTrue(any("찾지 못함" in f for f in fails))

    def test_missing_guardrail_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_missing_guardrail.md"))
        self.assertTrue(any("holdout" in f for f in fails))
        self.assertTrue(any("손익분기" in f or "breakeven" in f.lower() for f in fails))

    def test_fake_source_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_fake_source.md"))
        self.assertTrue(any("B9" in f for f in fails))

    def test_g3_fail_coupon_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_g3fail_coupon.md"))
        self.assertTrue(any("G3" in f for f in fails))

    def test_g2_fail_coupon_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_g2fail_coupon.md"))
        self.assertTrue(any("G2" in f for f in fails))

    def test_priority_nonselective_fails(self):
        fails = cp.lint_playbook(os.path.join(FIX, "bad_priority.md"))
        self.assertTrue(any("우선순위" in f for f in fails))

    def test_valid_source_ids_loaded(self):
        ids = cp.valid_source_ids()
        self.assertTrue({"B1", "P1", "V1"}.issubset(ids))
        self.assertNotIn("B9", ids)


if __name__ == "__main__":
    unittest.main()
