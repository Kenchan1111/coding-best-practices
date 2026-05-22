from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_OS_PATH = ROOT / "scripts" / "knowledge_os.py"


def load_knowledge_os_module():
    sys.path.insert(0, str(KNOWLEDGE_OS_PATH.parent))
    spec = importlib.util.spec_from_file_location("knowledge_os", KNOWLEDGE_OS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class KnowledgeOsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.knowledge_os = load_knowledge_os_module()

    def test_default_agents_include_kimi(self):
        self.assertIn("kimi", self.knowledge_os.DEFAULT_AGENTS)
        discovered = self.knowledge_os.discover_agents()
        self.assertIn("kimi", discovered)


if __name__ == "__main__":
    unittest.main()
