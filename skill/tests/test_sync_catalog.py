from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from frontmatter_utils import parse_frontmatter_file
from test_helpers import ROOT


class SyncCatalogScriptTest(unittest.TestCase):
    def run_sync(self, project_root: Path, *args: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["SKILL_PROJECT_ROOT"] = str(project_root)
        return subprocess.run(
            ["node", str(ROOT / "scripts/sync-catalog.ts"), *args],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def copy_project_fixture(self, target: Path) -> None:
        shutil.copytree(ROOT / "skill", target / "skill")
        findings_dir = target / "findings"
        findings_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "findings/01_bug_catalog.md", findings_dir / "01_bug_catalog.md")

    def source_catalog_ids(self, project_root: Path) -> list[str]:
        content = (project_root / "findings/01_bug_catalog.md").read_text(encoding="utf-8")
        ids = {match.group(1) for match in re.finditer(r"^### ([A-R]\d+)\.", content, re.MULTILINE)}
        ids.update(match.group(1) for match in re.finditer(r"^\| (L\d+) \|", content, re.MULTILINE))
        return sorted(ids, key=lambda item: (item[0], int(item[1:])))

    def test_sync_catalog_matches_canonical_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.copy_project_fixture(project)

            result = self.run_sync(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            metadata, _ = parse_frontmatter_file(project / "skill/catalog/bug_catalog.md")
            expected_ids = self.source_catalog_ids(project)

        self.assertEqual(int(metadata["pattern_count"]), len(expected_ids))
        self.assertEqual([str(item) for item in metadata["catalog_ids"]], expected_ids)

    def test_sync_catalog_rejects_id_drift_without_explicit_accept(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.copy_project_fixture(project)
            target = project / "skill/catalog/bug_catalog.md"
            text = target.read_text(encoding="utf-8")
            target.write_text(text.replace("  - A1", "  - A999", 1), encoding="utf-8")

            result = self.run_sync(project)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--accept-id-change", result.stderr)


if __name__ == "__main__":
    unittest.main()
