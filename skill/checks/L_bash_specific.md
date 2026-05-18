---
family: L
name: bash_specific
severity: high
languages: [bash]
triggers:
  - bash_script
  - shell_pipeline
  - sudo_script
  - lock_fd
patterns_matched:
  - 'set -euo pipefail with grep returning 1'
  - 'local used outside function'
  - 'sudo inside already-root script'
  - 'notify-send without fallback'
  - 'declare -A populated in pipeline subshell'
  - 'fd 200 lock not closed before fork'
fix_pattern: bash_portability_guardrails
gstack_integration: review_bash_specific
---

# L - Bash-specific failure modes

## When this check applies

Use this check when writing or reviewing Bash scripts, especially scripts with `set -euo pipefail`, pipelines, `sudo`, desktop notifications, network inspection, associative arrays, or `flock`.

## Avoid

```bash
set -euo pipefail
count=$(grep -c pattern file)
```

`grep` exits `1` when there are zero matches, which can abort the script under `set -e`.

```bash
cat input | while read -r key value; do
  declare -A seen
  seen["$key"]="$value"
done
```

The loop runs in a subshell in many shells; mutations are lost after the pipe.

## Required review steps

1. For every `grep` used as a count or optional match, add `|| true` or use a construct that treats no-match as expected.
2. Verify `local` appears only inside functions.
3. If the script may run under `sudo`, avoid nested `sudo`; check `id -u` at the start.
4. Treat `notify-send` and GUI tools as optional: redirect errors and continue.
5. Never use `resolvectl monitor` in automation because it can trigger auth prompts.
6. Do not trust `ss` alone for forensic claims; cross-check `/proc/net/tcp` when adversarial hooks matter.
7. Keep associative-array mutation out of pipeline subshells.
8. Close lock fd 200 before spawning long-lived children.

## Preferred fixes

```bash
count=$(grep -c pattern file || true)
```

```bash
while read -r key value; do
  seen["$key"]="$value"
done < input
```

```bash
if [ "$(id -u)" -ne 0 ]; then
  exec sudo "$0" "$@"
fi
```

## Fix-first classification

AUTO-FIX most local Bash mechanics when behavior is clear.

ASK when the fix changes privilege boundaries, process model, forensic guarantees, or monitoring behavior.

## Sources catalogue

- L1: `grep` no-match crashed under `set -euo pipefail`.
- L2: `local` outside function crashed Bash.
- L3: parser expected the wrong number of IFS fields.
- L4: double `sudo` failed without TTY.
- L5: `notify-send` failed without DBus.
- L6: `resolvectl monitor` triggered polkit.
- L7-L8: `ss` output was incomplete and user-space hookable.
- L9: `declare -A` mutations were lost in a pipeline subshell.
- L10: fd 200 lock was inherited by a child.
- gstack relation: fills a known gstack gap for Bash-heavy repos.
