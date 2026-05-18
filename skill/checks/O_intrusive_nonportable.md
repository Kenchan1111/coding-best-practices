---
family: O
name: intrusive_nonportable
severity: medium
languages: [python, bash, javascript, typescript]
triggers:
  - terminal_ui
  - import_path_hack
  - portability_review
  - script_runtime
patterns_matched:
  - 'os.system("clear") in TUI'
  - 'sys.path points to project root for script import'
  - 'terminal escape behavior leaks into redirected output'
  - 'cwd-dependent import side effect'
fix_pattern: portable_runtime_boundary
gstack_integration: devex_and_distribution
---

# O - Intrusive and non-portable runtime behavior

## When this check applies

Use this check when code clears terminals, mutates import paths, assumes a current working directory, emits terminal control sequences, or depends on local shell/terminal behavior.

## Avoid

```python
os.system("clear")
```

This pollutes redirected output and depends on terminal behavior.

```python
sys.path.insert(0, str(ROOT))
```

This can make imports work by cwd accident rather than by package structure.

## Required review steps

1. Check whether output may be redirected, logged, tested, or consumed by another program.
2. Avoid terminal control commands unless TTY is detected and the behavior is optional.
3. Verify imports work from the documented invocation path, not only from the current shell cwd.
4. Prefer package/module execution or explicit script directory imports over broad root path hacks.
5. Add a smoke test that runs the script from a different cwd when portability matters.

## Preferred fixes

```python
if sys.stdout.isatty():
    print("\n" * 50)
```

```python
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
```

## Fix-first classification

AUTO-FIX local non-portable terminal behavior when the intended output is clear.

ASK when import layout, packaging, or invocation contract changes.

## Sources catalogue

- O1: `os.system("clear")` polluted redirected TUI output.
- O2: `sys.path` pointed at root rather than the needed scripts directory.
- gstack relation: complements `/devex-review` and Distribution & CI/CD checks.
