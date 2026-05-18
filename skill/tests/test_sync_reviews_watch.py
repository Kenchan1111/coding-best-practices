import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WATCHER_PATH = ROOT / "scripts" / "sync_reviews_watch.py"


def load_watcher_module():
    sys.path.insert(0, str(WATCHER_PATH.parent))
    spec = importlib.util.spec_from_file_location("sync_reviews_watch", WATCHER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SyncReviewsWatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.watcher = load_watcher_module()

    def test_watches_markdown_and_review_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            markdown = root / "note.md"
            receipt = root / "note.md.receipt.json"
            change_receipt = root / "note.md.change-receipt.json"
            ignored_json = root / "catalog.json"
            ignored_tmp = root / "note.md.tmp.123"
            for path in (markdown, receipt, change_receipt, ignored_json, ignored_tmp):
                path.write_text("x", encoding="utf-8")

            self.assertTrue(self.watcher.should_watch_path(markdown))
            self.assertTrue(self.watcher.should_watch_path(receipt))
            self.assertTrue(self.watcher.should_watch_path(change_receipt))
            self.assertFalse(self.watcher.should_watch_path(ignored_json))
            self.assertFalse(self.watcher.should_watch_path(ignored_tmp))

    def test_skips_cache_and_git_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git_file = root / ".git" / "shadow.md"
            cache_file = root / "__pycache__" / "shadow.md"
            git_file.parent.mkdir()
            cache_file.parent.mkdir()
            git_file.write_text("x", encoding="utf-8")
            cache_file.write_text("x", encoding="utf-8")

            self.assertFalse(self.watcher.should_watch_path(git_file))
            self.assertFalse(self.watcher.should_watch_path(cache_file))

    def test_iter_watch_paths_prunes_skipped_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            watched = root / "reviews" / "note.md"
            ignored = root / ".git" / "shadow.md"
            watched.parent.mkdir()
            ignored.parent.mkdir()
            watched.write_text("x", encoding="utf-8")
            ignored.write_text("x", encoding="utf-8")

            paths = {path.relative_to(root).as_posix() for path in self.watcher.iter_watch_paths(root)}

            self.assertEqual(paths, {"reviews/note.md"})

    def test_skips_generated_sync_summaries(self):
        generated = ROOT / "knowledge" / "80_summaries" / "team_review_latest.md"

        self.assertFalse(self.watcher.is_watch_filename(generated))


if __name__ == "__main__":
    unittest.main()
