---
family: B
name: cascade_failure
severity: critical
languages: [python, bash, javascript, typescript]
triggers:
  - cli_main
  - orchestration_pipeline
  - subprocess_call
  - save_document
patterns_matched:
  - 'main() returns 0 after failed step'
  - 'subprocess.run(...) without check or handled returncode'
  - 'except Exception: print(...) then continue'
  - 'save_document(...) without OSError handling'
fix_pattern: fail_closed_with_step_status
gstack_integration: review_critical_pass
---

# B - Cascade failure and masked errors

## When this check applies

Use this check for CLI entrypoints, batch jobs, sync scripts, pipelines, and save/export flows where one failed step can make downstream evidence stale or misleading.

## Avoid

```python
def main() -> int:
    build_archive()
    build_anchor()
    build_timeline()
    return 0
```

This is unsafe when any internal step can fail while downstream code or the caller still observes success.

## Required review steps

1. Trace every step called by `main()` or the orchestrator.
2. Verify each failing step either raises to a top-level failure handler or returns a status that is checked.
3. Verify the process exit code is non-zero when required evidence was not regenerated.
4. For `subprocess.run`, require `check=True` or explicit `returncode` handling.
5. For user-facing saves, catch `OSError` and return an actionable message without pretending success.

## Preferred fix

```python
def main() -> int:
    try:
        build_archive()
        build_anchor()
        build_timeline()
    except Exception as exc:
        print(f"error: pipeline failed: {exc}", file=sys.stderr)
        return 1
    return 0
```

For multi-step pipelines, include the failed step name in the error. Do not continue to publish derived files after a required upstream step failed.

## Fix-first classification

ASK for critical orchestration behavior, because changing failure propagation can alter user-visible workflows.

AUTO-FIX is acceptable for small local improvements that only make an already-failing command return non-zero or print a clearer error.

## Sources catalogue

- B1: `main()` returned success while an internal forensic step failed.
- B2: `subprocess.run` failure surfaced as an unhandled crash instead of a controlled message.
- B3: `save_document()` did not handle disk or permission failures.
- gstack relation: aligns with `/investigate` root-cause discipline and `/review` critical pass.
