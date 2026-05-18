from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_helpers import ROOT


class E2EHarnessTest(unittest.TestCase):
    def test_mock_e2e_installs_skill_and_fires_required_checks(self):
        run_sh = ROOT / "skill/tests/e2e/run.sh"
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(run_sh), "--output-dir", tmp],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
            payload = json.loads((Path(tmp) / "result.json").read_text(encoding="utf-8"))

        summary = payload["summary"]
        self.assertTrue(payload["skill_loaded"])
        self.assertEqual(payload["agent"], "mock")
        self.assertIn("A_atomic_write", summary["checks_fired"])
        self.assertIn("B_cascade_failure", summary["checks_fired"])
        self.assertIn("C_scan_loop_safe", summary["checks_fired"])
        self.assertIn("on_write_state_file", summary["triggers_fired"])
        self.assertEqual(summary["clean_control_findings"], 0)


if __name__ == "__main__":
    unittest.main()
