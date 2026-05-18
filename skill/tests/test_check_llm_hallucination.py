import unittest

from test_helpers import (
    find_file_line_citations,
    frontmatter_list,
    load_check,
    load_trigger,
    unread_citations,
)


class LlmHallucinationCheckTest(unittest.TestCase):
    def test_unread_file_line_citation_is_detected(self):
        review_text = (
            "High: catalog.py:358 mutates METHOD_CATALOG in a loop. "
            "Fix by moving the status assignment."
        )

        self.assertEqual(find_file_line_citations(review_text), [("catalog.py", 358)])
        self.assertEqual(unread_citations(review_text, set()), [("catalog.py", 358)])
        self.assertEqual(unread_citations(review_text, {"catalog.py"}), [])

    def test_check_requires_reading_file_before_file_line_claim(self):
        metadata, body = load_check("E_llm_hallucination")
        patterns = frontmatter_list(metadata, "patterns_matched")

        self.assertIn("finding cites file:line not read in current session", patterns)
        self.assertIn("No finding with `file:line` may be emitted", body)
        self.assertIn("stale_fix_search", load_trigger("on_review_claim")[1])

    def test_review_trigger_loads_evidence_neighbors(self):
        metadata, body = load_trigger("on_review_claim")
        calls = frontmatter_list(metadata, "calls_checks")

        self.assertIn("E_llm_hallucination", calls)
        self.assertIn("J_bidir_test_coverage", calls)
        self.assertIn("P_contract_consistency", calls)
        self.assertIn("Evidence:", body)


if __name__ == "__main__":
    unittest.main()
