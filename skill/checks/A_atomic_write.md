---
family: A
name: atomic_write
severity: critical
languages: [python, bash, javascript, typescript]
triggers:
  - file_write_to_state
  - json_write
  - catalog_write
  - manifest_write
patterns_matched:
  - 'Path.write_text(json.dumps('
  - 'open(path, "w") on state files'
  - 'fs.writeFileSync(...JSON.stringify'
  - 'jq ... > state.json'
fix_pattern: tmp_rename_same_directory
gstack_integration: review_critical_pass
---

# A - Atomic writes and crash safety

## When this check applies

Use this check before writing trusted state: `latest.json`, `index.json`, `catalog.json`, manifests, run pointers, audit indexes, timelines, or any file read by a later step as authoritative state.

Do not surface this check for append-only logs, test fixtures, or caches that are explicitly regenerable and never treated as proof.

## Avoid

```python
path.write_text(json.dumps(state), encoding="utf-8")
```

```bash
jq '.items += [$item]' state.json > state.json
```

These patterns can leave a truncated file after crash, signal, full disk, or interrupted shell redirection.

## Required review steps

1. Identify whether the target file is state, proof, index, cache, or fixture.
2. If it is state or proof, require a temp file in the same directory and an atomic replace.
3. If JSON loading catches `JSONDecodeError`, verify it does not silently return empty state. Preserve the corrupt file or fail with a clear recovery path.
4. If the file is an audit timeline or hash chain, ask whether it must be append-only instead of rewritten.

## Preferred fix

```python
def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
```

For high-value evidence, also consider `fsync` on the file and parent directory. Treat that as ASK unless the project already has an fsync helper.

## Fix-first classification

AUTO-FIX only when adding or reusing a small existing helper for a new write path.

ASK when changing persistence semantics, recovery behavior, audit timelines, or anything that can discard existing state.

## Sources catalogue

- A1: non-atomic writes on trusted JSON state.
- A2: corrupt JSON silently replaced by empty state.
- A3: rewritten timeline loses immutable hash-chain property.
- gstack gap: gstack has cleanup safety, but no dedicated atomic state-write check.
