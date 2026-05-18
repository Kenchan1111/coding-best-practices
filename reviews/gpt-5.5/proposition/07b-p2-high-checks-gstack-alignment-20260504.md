---
id: gpt-5.5-proposition-07b-20260504
title: P2 second lot de checks haute priorite gstack-compatible
date: 2026-05-04
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: skill/checks/F-G-H-K-L, TODOS.md
synopsis: >
  Second lot P2 : cinq familles haute priorite materialisees en checks Markdown,
  toujours comme contenu greffable a gstack et non comme moteur concurrent.
validation:
  - "frontmatter checks A/B/D/E/F/G/H/J/K/L parse OK"
  - "python3 -m compileall scripts -> OK"
  - "python3 scripts/sync_reviews.py twice -> 0 variantes, 0 derives on second run"
---

# Contenu livre

- `skill/checks/F_race_conditions.md`
- `skill/checks/G_shell_token_filtering.md`
- `skill/checks/H_silent_override.md`
- `skill/checks/K_architecture_smells.md`
- `skill/checks/L_bash_specific.md`

# Checks implementes

## F - Race conditions

Couvre les IDs timestamp a la seconde, les singletons module-level sous multi-worker, les locks fd 200 herites par enfants et les ressources partagees sans verrou explicite.

Integration gstack : branchement naturel sur `/review` Race Conditions & Concurrency.

## G - Shell token filtering

Couvre les tokens shell de controle incomplets, les faux positifs substring sans word-boundary, les shells non parses et les sandboxes qui tombent a `none` sans fail closed.

Integration gstack : etend Shell Injection et reste coherent avec `/guard`.

## H - Silent override

Couvre les overrides silencieux de parametres explicites utilisateur, les filtres qui masquent des suppressions, les limites d'index sans signal et les actions manquantes par rapport a la spec.

Integration gstack : deplace la frontiere de confiance vers la preservation de l'intent utilisateur, pas seulement la validation de sorties LLM.

## K - Architecture smells

Couvre monolithes, duplications, fonctions au nom pur avec IO, coupling planning/execution, contrats publics en `dict[str, Any]` et raccourcis de preuve type Merkle duplicate-last.

Integration gstack : complete maintainability specialist et `/devex-review`.

## L - Bash-specific

Couvre les bugs Bash historiquement resolus : `grep` sous `set -e`, `local` hors fonction, double sudo, `notify-send`, `resolvectl monitor`, `ss`, subshell pipeline, fd 200.

Integration gstack : comble une lacune explicite pour les repos Python/CLI/Bash.

# Limites

- Toujours pas de moteur statique executable.
- Triggers P3 non encore crees.
- Generateur P4 non encore adapte au pipeline gstack.
- Les checks sont prets pour review LLM et generation future, pas pour sign-off Phase 1.
