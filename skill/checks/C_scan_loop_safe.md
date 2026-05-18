---
family: C
name: scan_loop_safe
severity: high
languages: [python, bash, javascript, typescript]
triggers:
  - scan_loop
  - batch_read
  - markdown_frontmatter_scan
  - archive_scan
patterns_matched:
  - 'single malformed item aborts whole scan'
  - 'README.md included in review document scan'
  - 'yaml.safe_load inside loop without per-item handling'
  - 'batch loop returns exit 1 for ignorable file'
fix_pattern: isolate_item_failures
gstack_integration: review_batch_resilience
---

# C - Scan loops must survive one bad item

## When this check applies

Use this check when code scans many files, parses many documents, indexes archives, loads frontmatter, or processes a batch where one corrupt item should not prevent all later items from being seen.

## Avoid

```python
for path in sorted(root.glob("*.md")):
    metadata = yaml.safe_load(path.read_text())
    documents.append(metadata)
```

One malformed file aborts the whole scan.

## Required review steps

1. Decide whether one bad item should fail the whole run or be reported while the scan continues.
2. If continuation is expected, use a `skip+report` policy: catch parse errors per item, record the path and error, then keep scanning.
3. Exclude known non-doc files such as `README.md` when frontmatter is mandatory.
4. Return a status that distinguishes complete success, partial success with warnings, and hard failure.
5. Include the count of skipped or failed items in the result.

## Preferred fix

```python
errors = []
for path in sorted(root.glob("*.md")):
    if path.name.upper() == "README.md":
        continue
    try:
        documents.append(load_document(path))
    except Exception as exc:
        errors.append({"path": str(path), "error": str(exc)})
```

## Fix-first classification

AUTO-FIX simple exclusions like `README.md` and per-item error collection when the caller already supports warnings.

ASK if changing a hard-fail scan to partial success can affect compliance, security, or proof guarantees.

## Sources catalogue

- C1: malformed YAML in one `.md` killed the entire archive scan.
- C2: `README.md` without frontmatter caused permanent sync failure.
- gstack relation: complements `/review` completeness and operational resilience checks.
