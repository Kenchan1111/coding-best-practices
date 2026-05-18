---
family: E
name: llm_hallucination
severity: critical
languages: [markdown, python, bash, javascript, typescript]
triggers:
  - review_claim
  - file_line_citation
  - reproduction_example
  - proposed_refix
patterns_matched:
  - 'finding cites file:line not read in current session'
  - 'claim references code block that does not exist'
  - 'proposed fix already exists'
  - 'reproduction example not executed or not reproducing'
fix_pattern: verify_before_claiming
gstack_integration: review_claim_gate
---

# E - LLM hallucination in reviews

## When this check applies

Use this check before publishing any review finding, handoff, correction note, or architectural claim that cites a file, line number, code behavior, reproduction example, or already-existing fix.

This is the key meta-skill check. It prevents reviewers from working from memory.

## Hard rule

No finding with `file:line` may be emitted unless the cited file was read in the current session and the cited lines still support the claim.

## Required review steps

1. Read the cited file around the cited line before writing the finding.
2. If the claim is behavioral, run or sketch a minimal reproduction and state whether it was executed.
3. Search for the proposed fix before recommending it. Do not refix code that already exists.
4. If using examples, verify the examples actually reproduce the defect.
5. Do not convert uncertainty into precision. If line evidence is missing, say that explicitly and downgrade to a question.

## Avoid

```markdown
High: catalog.py:358-362 mutates METHOD_CATALOG in a loop.
```

This is invalid if the file was not read or the block does not exist.

## Preferred evidence format

```markdown
Evidence read:
- path/to/file.py:120 shows direct write with Path.write_text(...)
- path/to/test_file.py:88 does not cover the lower branch

Reproduction:
- command run: python3 -m pytest tests/test_limit.py -k lower
- result: fails before fix, passes after fix
```

If no command was run, write `Reproduction not run` and explain why.

## Fix-first classification

AUTO-FIX stale citations and remove false claims immediately.

ASK when the underlying behavior is uncertain or reproduction requires domain input.

## Sources catalogue

- E1: cited file:line referenced code that did not exist.
- E2: proposed fixes already existed in code or tests.
- E3: reproduction examples did not reproduce the bug.
- E4: opaque imports hid real dependencies.
- gstack relation: strengthens `Search before building` and `/review` outside-diff reading into an explicit claim gate.
