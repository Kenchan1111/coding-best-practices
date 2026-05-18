---
family: G
name: shell_token_filtering
severity: high
languages: [python, bash]
triggers:
  - shell_filter
  - command_sandbox
  - command_allowlist
  - text_classifier
patterns_matched:
  - 'SHELL_CONTROL_TOKENS missing redirects'
  - 'short term matched with substring search'
  - 'extract_shell_payload recognizes only bash'
  - 'sandbox selected none but command still executes'
fix_pattern: fail_closed_shell_policy
gstack_integration: review_shell_injection_and_guard
---

# G - Shell token filtering and incomplete input control

## When this check applies

Use this check when code filters shell commands, extracts shell payloads, classifies text by substring, selects a sandbox, or relies on allowlists before executing user or LLM-controlled input.

## Avoid

```python
SHELL_CONTROL_TOKENS = ("&&", "||", ";", "|", "$(", "`")
```

This misses redirects such as `>`, `>>`, `<`, `>&`, `2>`, and `2>&1`.

```python
if term in haystack:
    return match
```

Short tokens create false positives without word boundaries.

## Required review steps

1. Treat shell parsing as security-sensitive. If the code uses a denylist, verify redirection, subshell, pipe, newline, and fd-control tokens are covered.
2. Verify every supported shell form is parsed or rejected. Do not silently disable filtering when the shell is `dash`, `ksh`, `fish`, or `bash --`.
3. If sandbox selection falls back to `none`, check whether policy still permits execution. Network-deny policy must fail closed if no sandbox can enforce it.
4. For text classifiers, require word-boundary matching for short terms and explicit tests for known false positives.
5. Search for call sites that assume a `None` extraction means safe. It may mean unparsed.

## Preferred fixes

Fail closed when the shell cannot be parsed or sandboxed:

```python
payload = extract_shell_payload(command)
if payload is None and policy.requires_shell_filter:
    raise PolicyError("unsupported shell invocation")
```

Use boundary-aware matching for short terms:

```python
if len(term) <= 3:
    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    return bool(pattern.search(haystack))
return term.lower() in haystack.lower()
```

## Fix-first classification

ASK for security policy, sandbox fallback, and command execution changes.

AUTO-FIX only for adding missing mechanical test cases or extending a clearly intended token list without changing policy semantics.

## Sources catalogue

- G1: shell control tokens missed redirects.
- G2: substring matching without word boundaries caused false positives.
- G3: shell whitelist was incomplete and disabled filtering.
- G4: sandbox fallback `none` still executed under deny policy.
- gstack relation: extends `/review` Shell Injection beyond Python `shell=True` and aligns with `/guard`.
