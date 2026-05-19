from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_helpers import ROOT


SCRIPT = ROOT / "scripts" / "local_git_guard.py"


def run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


class LocalGitGuardTest(unittest.TestCase):
    def init_repo(self, repo: Path) -> None:
        repo.mkdir(parents=True, exist_ok=True)
        git(repo, "init")
        git(repo, "config", "user.email", "tests@example.com")
        git(repo, "config", "user.name", "Tests")

    def write_policy(self, repo: Path) -> None:
        (repo / "ops").mkdir(parents=True, exist_ok=True)
        policy = {
            "version": "1",
            "policy_name": "local_git_manifested",
            "description": "test policy",
            "local_roots": [
                {
                    "name": "change_sessions",
                    "path": "change_sessions",
                    "classification": "local_git_manifested",
                    "reason": "change proof",
                },
                {
                    "name": "knowledge_summaries",
                    "path": "knowledge/80_summaries",
                    "classification": "local_git_manifested",
                    "reason": "generated summaries",
                },
                {
                    "name": "mcp",
                    "path": "mcp",
                    "classification": "local_git_manifested",
                    "reason": "local mcp state",
                },
            ],
            "manifest_dir": "ops/local_git_manifests",
            "summary_manifest": "ops/local_git_manifests/index.json",
            "pushable_manifest": "ops/local_git_manifests/pushable_tracked.json",
            "exclude_from_pushable_manifest": [
                "ops/local_git_manifests/"
            ],
            "ignore_rules": [
                "change_sessions/",
                "knowledge/80_summaries/",
                "mcp/",
            ],
        }
        (repo / "ops" / "local_git_policy.json").write_text(
            json.dumps(policy, indent=2) + "\n",
            encoding="utf-8",
        )

    def write_gitignore(self, repo: Path) -> None:
        (repo / ".gitignore").write_text(
            "change_sessions/\nknowledge/80_summaries/\nmcp/\n",
            encoding="utf-8",
        )

    def seed_files(self, repo: Path) -> None:
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "change_sessions" / "s1").mkdir(parents=True)
        (repo / "change_sessions" / "s1" / "closeout.md").write_text("closeout\n", encoding="utf-8")
        (repo / "knowledge" / "80_summaries").mkdir(parents=True)
        (repo / "knowledge" / "80_summaries" / "latest.md").write_text("latest\n", encoding="utf-8")
        (repo / "mcp").mkdir(parents=True)
        (repo / "mcp" / "catalog.json").write_text("{\"ok\": true}\n", encoding="utf-8")
        (repo / "mcp" / "link").symlink_to(repo / "src")

    def test_build_manifests_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.init_repo(repo)
            self.write_policy(repo)
            self.write_gitignore(repo)
            self.seed_files(repo)
            git(repo, "add", ".gitignore", "ops/local_git_policy.json", "src/app.py")
            git(repo, "commit", "-m", "initial")

            build = run([sys.executable, str(SCRIPT), "build-manifests", "--repo-root", str(repo)], cwd=repo)
            self.assertEqual(build.returncode, 0, build.stderr)

            verify = run(
                [sys.executable, str(SCRIPT), "verify", "--repo-root", str(repo), "--strict"],
                cwd=repo,
            )
            self.assertEqual(verify.returncode, 0, verify.stderr)
            self.assertIn("LOCAL_GIT_OK", verify.stdout)

            root_manifest = json.loads(
                (repo / "ops" / "local_git_manifests" / "mcp.json").read_text(encoding="utf-8")
            )
            self.assertEqual(root_manifest["symlink_count"], 1)
            self.assertEqual(root_manifest["symlinks"][0]["path"], "link")

    def test_verify_detects_tracked_local_git_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.init_repo(repo)
            self.write_policy(repo)
            self.write_gitignore(repo)
            self.seed_files(repo)
            git(repo, "add", ".gitignore", "ops/local_git_policy.json", "src/app.py")
            git(repo, "add", "-f", "mcp/catalog.json")
            git(repo, "commit", "-m", "bad-initial")

            build = run([sys.executable, str(SCRIPT), "build-manifests", "--repo-root", str(repo)], cwd=repo)
            self.assertEqual(build.returncode, 0, build.stderr)

            verify = run(
                [sys.executable, str(SCRIPT), "verify", "--repo-root", str(repo), "--strict"],
                cwd=repo,
            )
            self.assertEqual(verify.returncode, 1)
            self.assertIn("tracked files remain under local_git roots", verify.stderr)

    def test_verify_detects_stale_local_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.init_repo(repo)
            self.write_policy(repo)
            self.write_gitignore(repo)
            self.seed_files(repo)
            git(repo, "add", ".gitignore", "ops/local_git_policy.json", "src/app.py")
            git(repo, "commit", "-m", "initial")

            build = run([sys.executable, str(SCRIPT), "build-manifests", "--repo-root", str(repo)], cwd=repo)
            self.assertEqual(build.returncode, 0, build.stderr)

            (repo / "knowledge" / "80_summaries" / "latest.md").write_text("changed\n", encoding="utf-8")
            verify = run(
                [sys.executable, str(SCRIPT), "verify", "--repo-root", str(repo), "--strict"],
                cwd=repo,
            )
            self.assertEqual(verify.returncode, 1)
            self.assertIn("knowledge/80_summaries: mismatch for merkle_root", verify.stderr)

    def test_hook_check_refreshes_and_stages_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.init_repo(repo)
            self.write_policy(repo)
            self.write_gitignore(repo)
            self.seed_files(repo)
            git(repo, "add", ".gitignore", "ops/local_git_policy.json", "src/app.py")
            git(repo, "commit", "-m", "initial")

            hook = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "hook-check",
                    "--repo-root",
                    str(repo),
                    "--hook",
                    "pre-commit",
                    "--refresh",
                    "--stage-manifests",
                    "--strict",
                ],
                cwd=repo,
            )
            self.assertEqual(hook.returncode, 0, hook.stderr)

            staged = run(["git", "diff", "--cached", "--name-only"], cwd=repo)
            self.assertIn("ops/local_git_manifests/index.json", staged.stdout)
            self.assertIn("ops/local_git_manifests/pushable_tracked.json", staged.stdout)

    def test_install_hooks_sets_core_hookspath(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            self.init_repo(repo)
            self.write_policy(repo)
            self.write_gitignore(repo)
            (repo / ".githooks").mkdir()
            (repo / ".githooks" / "pre-commit").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (repo / ".githooks" / "pre-push").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")

            install = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "install-hooks",
                    "--repo-root",
                    str(repo),
                    "--set-hooks-path",
                ],
                cwd=repo,
            )
            self.assertEqual(install.returncode, 0, install.stderr)
            hookspath = run(["git", "config", "--get", "core.hooksPath"], cwd=repo)
            self.assertEqual(hookspath.stdout.strip(), ".githooks")


if __name__ == "__main__":
    unittest.main()
