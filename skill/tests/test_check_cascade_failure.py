import unittest

from test_helpers import ROOT, frontmatter_list, load_check, lower_join


class CascadeFailureCheckTest(unittest.TestCase):
    def test_cascade_check_targets_success_after_internal_failure(self):
        metadata, body = load_check("B_cascade_failure")
        fixture = (
            ROOT
            / "skill/tests/fixtures/planted-bugs/cascade_failure_bad.py"
        ).read_text(encoding="utf-8")
        patterns = lower_join(frontmatter_list(metadata, "patterns_matched"))

        self.assertIn("subprocess.run", fixture)
        self.assertIn("return 0", fixture)
        self.assertIn("main() returns 0", patterns)
        self.assertIn("subprocess.run", patterns)
        self.assertIn("return 1", body)
        self.assertIn("failed step name", body)


if __name__ == "__main__":
    unittest.main()
