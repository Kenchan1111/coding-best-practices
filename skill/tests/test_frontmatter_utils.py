from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from frontmatter_utils import parse_frontmatter_file


class FrontmatterUtilsTest(unittest.TestCase):
    def test_parse_frontmatter_file_accepts_yaml_lists_and_strings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text(
                """---
name: sample
fires_on:
  - code_pattern: 'assert|expect'
  - text_pattern: '[A-Z]+'
preflight_budget: 45s
---

Body line.
""",
                encoding="utf-8",
            )

            metadata, body = parse_frontmatter_file(path)

        self.assertEqual(metadata["name"], "sample")
        self.assertEqual(
            metadata["fires_on"],
            ["code_pattern: assert|expect", "text_pattern: [A-Z]+"],
        )
        self.assertEqual(metadata["preflight_budget"], "45s")
        self.assertIn("Body line.", body)

    def test_parse_frontmatter_file_rejects_non_mapping_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text(
                """---
- not
- a
- mapping
---

Body line.
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "must decode to a mapping"):
                parse_frontmatter_file(path)


if __name__ == "__main__":
    unittest.main()
