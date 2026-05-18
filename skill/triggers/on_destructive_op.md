---
trigger: on_destructive_op
phase: before_destructive_edit_or_command
intent: Avoid irreversible data loss and preserve auditability.
fires_on:
  - bash_command: 'rm -r|rm -rf|git reset --hard|git checkout \.|git restore \.|mv |truncate|DROP TABLE|DROP DATABASE'
  - python_pattern: 'shutil\.move|unlink\(|rmtree\(|remove\(|replace\('
  - code_pattern: 'overwrite|delete|promote|archive|truncate|drop|reset'
calls_checks:
  - I_irreversible_ops
  - H_silent_override
  - R_audit_trail
  - A_atomic_write
  - M_drift_detection
  - G_shell_token_filtering
  - L_bash_specific
  - F_race_conditions
suppress_when:
  - generated_cache_cleanup
  - ignored_build_artifact_cleanup
  - user_explicitly_approved_exact_target
preflight_budget: 45s
---

# Trigger - Destructive Operation

## Activation rule

If the next edit or command deletes, moves, overwrites, truncates, promotes, resets, or replaces data that might be source, user input, review evidence, state, or proof, run this trigger before acting.

This trigger complements gstack `/careful` and `/guard`. It applies to code changes too, not only shell commands.

## 45-second preflight

1. Load `I_irreversible_ops` and identify the source of truth that could be lost.
2. Load `H_silent_override` if an explicit user ID, mode, catalog, or action can be replaced by automatic behavior.
3. Load `R_audit_trail` if original parameters or timestamps are dropped during the operation.
4. Load `A_atomic_write` if the operation replaces a state or proof file.
5. Load `M_drift_detection` if the operation changes a catalog, latest snapshot, or baseline.
6. Load `G_shell_token_filtering` if the operation is shell-mediated or sandboxed.
7. Load `L_bash_specific` if the operation is inside a Bash script or pipeline.
8. Load `F_race_conditions` if concurrent writers, locks, or child processes are involved.

## Required LLM behavior

Before acting, write:

```text
Destructive preflight: target=<path/id>; reversible=<yes|no>; backup_or_copy=<yes|no>; checks=<I,H,R,A,M,G,L,F subset>; approval=<not_needed|needed|already_explicit>.
```

If `reversible=no` and approval is not explicit for the exact target, ask the user.

## Do not trigger

- Cleanup of generated build artifacts such as `node_modules`, `dist`, `build`, `.pytest_cache`, `__pycache__`, or coverage output.
- Deletion of files created by the same failed command when the target is exact, untracked, and non-source.
