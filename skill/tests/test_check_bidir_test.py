import unittest

from test_helpers import ROOT, frontmatter_list, load_check, load_trigger, lower_join


class BidirTestCoverageCheckTest(unittest.TestCase):
    def test_bidir_check_rejects_upper_only_regression_shape(self):
        _metadata, body = load_check("J_bidir_test_coverage")
        fixture = (
            ROOT
            / "skill/tests/fixtures/planted-bugs/bidir_test_bad.py"
        ).read_text(encoding="utf-8")

        self.assertIn('side="upper"', fixture)
        self.assertNotIn('side="lower") <', fixture)
        self.assertIn("side=\"upper\"", body)
        self.assertIn("side=\"lower\"", body)
        self.assertIn("would fail before the fix", body)

    def test_write_test_trigger_loads_domain_and_contract_neighbors(self):
        metadata, body = load_trigger("on_write_test")
        calls = frontmatter_list(metadata, "calls_checks")
        fires_on = lower_join(frontmatter_list(metadata, "fires_on"))

        self.assertIn("J_bidir_test_coverage", calls)
        self.assertIn("Q_numerical_precision", calls)
        self.assertIn("P_contract_consistency", calls)
        self.assertIn("test_", fires_on)
        self.assertIn("Test preflight", body)


if __name__ == "__main__":
    unittest.main()
