---
trigger: on_review_claim
phase: before_publishing_review
intent: Prevent file:line hallucinations, stale fixes, and unreproduced review claims.
fires_on:
  - user_request: 'review|audit|check my diff|finding|sign-off|handoff|correction'
  - text_pattern: '[A-Za-z0-9_./-]+:\d+'
  - text_pattern: 'already fixed|reproduce|does not exist|bug at|line'
calls_checks:
  - E_llm_hallucination
  - J_bidir_test_coverage
  - P_contract_consistency
  - D_iteration_semantics
  - K_architecture_smells
suppress_when:
  - no_file_or_line_claims
preflight_budget: 60s
---

# Trigger - Review Claim

## Activation rule

If the next response publishes a review finding, correction, handoff, or sign-off with a `file:line`, code behavior claim, reproduction example, or proposed refix, run this trigger before writing the claim.

This trigger must fire even if the reviewer is confident. Confidence from memory is not evidence.

## 60-second preflight

1. Load `E_llm_hallucination` for every cited `file:line`.
2. Read the cited file around the cited line in the current session.
3. Search whether the proposed fix already exists before recommending it.
4. If the claim is about test adequacy, load `J_bidir_test_coverage`.
5. If the claim is about public values, status, schema, or config precedence, load `P_contract_consistency`.
6. If the claim is about latest/first/sort/slice/iteration, load `D_iteration_semantics`.
7. If the claim is about architecture, layering, side effects, public contracts, or refactoring, load `K_architecture_smells`.

## Required LLM behavior

Each finding must include an evidence state:

```text
Evidence: read=<file:line or range>; reproduced=<command|not_run>; stale_fix_search=<done|not_applicable>.
```

If the file was not read in the current session, do not cite a line number. Downgrade to an open question.

## Do not trigger

- High-level planning notes without file claims.
- User-visible summaries that do not assert code behavior or line evidence.
