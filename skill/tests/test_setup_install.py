import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_helpers import ROOT


SETUP = ROOT / "skill" / "setup"
UNINSTALL = ROOT / "skill" / "uninstall"
SKILL = ROOT / "skill"


class SetupInstallTest(unittest.TestCase):
    def run_script(self, script: Path, *args: str, home: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            ["bash", str(script), *args],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_setup_and_uninstall_syntax(self):
        for script in (SETUP, UNINSTALL):
            result = subprocess.run(["bash", "-n", str(script)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_setup_dry_run_does_not_create_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_script(
                SETUP,
                "--host",
                "all",
                "--dry-run",
                "--skip-validate",
                home=home,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY-RUN", result.stdout)
            self.assertFalse((home / ".claude").exists())
            self.assertFalse((home / ".codex").exists())
            self.assertFalse((home / ".kimi").exists())

    def test_setup_installs_managed_links_idempotently(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            first = self.run_script(SETUP, "--host", "all", "--yes", "--skip-validate", home=home)
            second = self.run_script(SETUP, "--host", "all", "--yes", "--skip-validate", home=home)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            for target in (
                home / ".claude" / "skills" / "coding-best-practices",
                home / ".codex" / "skills" / "coding-best-practices",
                home / ".kimi" / "skills" / "coding-best-practices",
            ):
                self.assertTrue(target.is_symlink(), target)
                self.assertEqual(target.resolve(), SKILL.resolve())

    def test_setup_refuses_unmanaged_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            target = home / ".codex" / "skills" / "coding-best-practices"
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text("unmanaged", encoding="utf-8")

            result = self.run_script(SETUP, "--host", "codex", "--yes", "--skip-validate", home=home)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not managed", result.stderr)
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "unmanaged")

    def test_uninstall_removes_only_managed_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            install = self.run_script(SETUP, "--host", "all", "--yes", "--skip-validate", home=home)
            self.assertEqual(install.returncode, 0, install.stderr)

            other = home / ".codex" / "skills" / "other-skill"
            other.mkdir(parents=True)
            (other / "SKILL.md").write_text("keep", encoding="utf-8")

            result = self.run_script(UNINSTALL, "--host", "all", "--yes", home=home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".claude" / "skills" / "coding-best-practices").exists())
            self.assertFalse((home / ".codex" / "skills" / "coding-best-practices").exists())
            self.assertFalse((home / ".kimi" / "skills" / "coding-best-practices").exists())
            self.assertTrue(other.exists())
            self.assertEqual((other / "SKILL.md").read_text(encoding="utf-8"), "keep")

    def test_setup_installs_kimi_host_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            result = self.run_script(SETUP, "--host", "kimi", "--yes", "--skip-validate", home=home)

            self.assertEqual(result.returncode, 0, result.stderr)
            kimi_target = home / ".kimi" / "skills" / "coding-best-practices"
            self.assertTrue(kimi_target.is_symlink(), kimi_target)
            self.assertEqual(kimi_target.resolve(), SKILL.resolve())
            self.assertFalse((home / ".claude").exists())
            self.assertFalse((home / ".codex").exists())


if __name__ == "__main__":
    unittest.main()
