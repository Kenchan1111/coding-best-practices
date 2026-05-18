import unittest

from test_helpers import ROOT, frontmatter_list, load_check, load_trigger, lower_join


class AtomicWriteCheckTest(unittest.TestCase):
    def test_atomic_write_check_fires_on_direct_json_state_write(self):
        metadata, body = load_check("A_atomic_write")
        fixture = (
            ROOT
            / "skill/tests/fixtures/planted-bugs/atomic_write_bad.py"
        ).read_text(encoding="utf-8")
        patterns = lower_join(frontmatter_list(metadata, "patterns_matched"))

        self.assertIn("write_text(json.dumps", fixture)
        self.assertIn("write_text(json.dumps", patterns)
        self.assertIn("tmp.replace(path)", body)
        self.assertIn("AUTO-FIX", body)
        self.assertIn("ASK", body)

    def test_state_file_trigger_loads_atomic_and_failure_checks(self):
        metadata, body = load_trigger("on_write_state_file")
        calls = frontmatter_list(metadata, "calls_checks")
        fires_on = lower_join(frontmatter_list(metadata, "fires_on"))

        self.assertIn("A_atomic_write", calls)
        self.assertIn("B_cascade_failure", calls)
        self.assertIn("latest|index|catalog|manifest|state", fires_on)
        self.assertIn("State-write preflight", body)


if __name__ == "__main__":
    unittest.main()
