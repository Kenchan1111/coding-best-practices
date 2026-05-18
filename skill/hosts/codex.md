# Host Codex

Codex est vise comme host compatible par artefact en Phase 1.

## Installation cible

```text
~/.codex/skills/coding-best-practices/
```

## Notes Phase 1

- Installation via `bash skill/setup --host codex --yes`
- Le layout reste lisible sans dependance Claude-only.
- Le setup P6 est livre ; l'E2E P7 reste un mock deterministe, pas une preuve de comportement LLM live.
- La parite comportementale Codex est Phase 2.

## Relation avec les skills Codex existantes

`coding-best-practices` est complementaire, pas prioritaire sur le skillstack Codex.

- `repo-change-guard` reste la source de discipline pour closeout, baseline et post-change checks.
- `repo-review-snapshot` reste la source de discipline pour snapshot, repro et labels de review.
- `review-code-canon` reste la source de standards generaux de review et qualite.
- `coding-best-practices` ajoute le catalogue empirique A-R et les triggers contextuels.

Quand plusieurs skills s'appliquent, utiliser `repo-change-guard` ou `repo-review-snapshot` pour la preuve globale, puis charger les checks A-R seulement pour le risque local.

## Modes de travail Codex

- Implementation : A, B, C, F, G, H, I, K, L, N, O.
- Review, handoff ou sign-off : D, E, J, M, P, Q, R.
- Operations destructrices : I avec `repo-change-guard` et les regles systeme Codex de non-destruction.

## Langue et portabilite

Le contenu principal de la skill est en francais parce que le catalogue source et les reviews du repo le sont.
Pour Codex, le `SKILL.md` contient un contrat anglais court ; une generation complete `SKILL.md.en` reste Phase 2.

## Limites connues

- Aucune preuve Phase 1 que Codex declenche spontanement les triggers.
- Les patterns `fires_on` sont des conventions textuelles host-neutral, pas une API Codex.
- Les regex de patterns sont lintes par `scripts/validate.ts`, mais le matching live reste a verifier par smoke test Codex.
