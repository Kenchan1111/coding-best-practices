# Host Claude Code

Claude Code est le host primaire pour la Phase 1.

## Installation cible

```text
~/.claude/skills/coding-best-practices/
```

## Notes Phase 1

- `SKILL.md` est genere depuis `SKILL.md.tmpl`
- Installation via `bash skill/setup --host claude --yes`
- Les hooks Claude restent hors scope Phase 1 ; la skill fonctionne comme artefact Markdown installe.
- La parite comportementale live avec un vrai agent reste a verifier en P8/P9.

## Comportement attendu

Claude doit utiliser cette skill comme un garde-fou de contexte :

- Avant une modification de code, identifier si un trigger s'applique.
- Lire uniquement le trigger pertinent puis les checks references par `calls_checks`.
- Ne pas charger les 18 checks d'un coup.
- Produire la phrase de preflight demandee avant d'editer ou de publier un finding.
- Traiter les budgets `45s` / `60s` comme des limites de concision, pas comme une garantie runtime.

## Modes de travail

- Mode implementation : prioriser A, B, C, F, G, H, I, K, L, N, O.
- Mode review ou handoff : prioriser D, E, J, M, P, Q, R.
- Mode destructif : toujours combiner avec la discipline gstack `/careful` ou `/guard`.

## Limites connues

- Phase 1 ne fournit pas de hook `PreToolUse`; Claude peut ignorer la skill.
- Le E2E P7 prouve le routing d'artefact via mock, pas la compliance d'un Claude live.
- Le contenu principal reste en francais ; le `SKILL.md` contient seulement un contrat anglais court pour les hosts anglophones.
