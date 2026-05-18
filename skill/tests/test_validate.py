import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_helpers import ROOT


class ValidateScriptTest(unittest.TestCase):
    def run_validate(self, project_root: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["SKILL_PROJECT_ROOT"] = str(project_root)
        return subprocess.run(
            ["node", str(ROOT / "scripts/validate.ts")],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def copy_project_fixture(self, target: Path) -> None:
        shutil.copytree(ROOT / "skill", target / "skill")

    def test_validate_accepts_current_generated_skill(self):
        result = self.run_validate(ROOT)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validation OK", result.stdout)

    def test_validate_rejects_check_without_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.copy_project_fixture(project)
            bad_check = project / "skill/checks/A_atomic_write.md"
            body = bad_check.read_text(encoding="utf-8").split("---", 2)[-1].lstrip()
            bad_check.write_text(body, encoding="utf-8")

            result = self.run_validate(project)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing frontmatter", result.stderr)

    def test_validate_rejects_trigger_referencing_unknown_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.copy_project_fixture(project)
            trigger = project / "skill/triggers/on_write_test.md"
            text = trigger.read_text(encoding="utf-8")
            trigger.write_text(
                text.replace("  - J_bidir_test_coverage", "  - Z_missing_check"),
                encoding="utf-8",
            )

            result = self.run_validate(project)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown check 'Z_missing_check'", result.stderr)

    def test_validate_rejects_invalid_trigger_regex(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.copy_project_fixture(project)
            trigger = project / "skill/triggers/on_write_test.md"
            text = trigger.read_text(encoding="utf-8")
            trigger.write_text(
                text.replace(
                    "  - code_pattern: 'assert|expect|pytest|unittest|describe\\(|it\\('",
                    "  - code_pattern: 'assert|expect|pytest|unittest|describe(|it('",
                ),
                encoding="utf-8",
            )

            result = self.run_validate(project)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid code_pattern regex", result.stderr)


if __name__ == "__main__":
    unittest.main()
