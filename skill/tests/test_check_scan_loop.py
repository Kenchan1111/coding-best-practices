import unittest

from test_helpers import ROOT, frontmatter_list, load_check, load_trigger, lower_join


class ScanLoopCheckTest(unittest.TestCase):
    def test_scan_loop_check_fires_on_yaml_parse_inside_batch_loop(self):
        metadata, body = load_check("C_scan_loop_safe")
        fixture = (
            ROOT
            / "skill/tests/fixtures/planted-bugs/scan_loop_bad.py"
        ).read_text(encoding="utf-8")
        patterns = lower_join(frontmatter_list(metadata, "patterns_matched"))

        self.assertIn("for path in sorted", fixture)
        self.assertIn("yaml.safe_load", fixture)
        self.assertIn("single malformed item aborts whole scan", patterns)
        self.assertIn("README.md", body)
        self.assertIn("skip+report", body)

    def test_scan_loop_trigger_loads_ordering_and_failure_neighbors(self):
        metadata, body = load_trigger("on_write_scan_loop")
        calls = frontmatter_list(metadata, "calls_checks")

        self.assertIn("C_scan_loop_safe", calls)
        self.assertIn("D_iteration_semantics", calls)
        self.assertIn("B_cascade_failure", calls)
        self.assertIn("Scan-loop preflight", body)


if __name__ == "__main__":
    unittest.main()
