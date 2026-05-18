---
id: 15-internal-skill-corrections-review-20260511
title: Review des corrections internes de coding-best-practices
date: 2026-05-11
status: proposed
agent: gpt-5.5
scope: skill/SKILL.md, skill/checks, skill/triggers, skill/setup, skill/uninstall, skill/tests, skill/README.md, skill/hosts, ARCHITECTURE.md
synopsis: "Revue ancree sur l'etat courant de la skill coding-best-practices. Les validations code passent ; les corrections appliquees portent sur les derives documentaires P6/P7 et le layout reel."
reviewed_revision: "2d9163f9dccca00b78f7d69c379714a72fa46962+dirty"
---

# Review des corrections internes

## Snapshot

- Repo : `/home/zack/Documents/Divers/Dict_AI_Coding`
- Date locale : 2026-05-11T18:30:02+02:00
- HEAD : `2d9163f9dccca00b78f7d69c379714a72fa46962`
- Etat : dirty, avec beaucoup de fichiers non suivis ; verdict ancre en `HEAD+dirty`.

## Verdict

Les corrections de code de la skill sont globalement bonnes pour le niveau Phase 1/P7 :

- generation deterministe OK,
- validation structurelle OK,
- setup/uninstall idempotents et protecteurs contre ecrasement non gere,
- tests unitaires OK,
- E2E mock OK,
- limite du mock correctement declaree.

Je n'ai pas trouve de bug bloquant dans le code de `skill/setup`, `skill/uninstall`, `scripts/validate.ts`, `scripts/gen-skill-docs.ts`, `scripts/sync-catalog.ts` ou le harness E2E.

## Findings courants

### Low - Documentation Phase 1 stale apres P6/P7

Etat : `confirmed_current`, corrige dans cette session.

Evidence :

- `skill/README.md` indiquait encore P1-P5 livres, 13 tests, et P6 restant.
- `skill/hosts/claude.md` et `skill/hosts/codex.md` indiquaient encore que le setup final arrivait en P6.
- `ARCHITECTURE.md` gardait des traces de pre-arbitrage : nom a arbitrer, layout `skill/scripts/`, et host `opencode.md` non livre.

Impact :

- Les reviewers pouvaient croire que P6/P7 n'etaient pas livres.
- Les futurs agents pouvaient chercher les scripts au mauvais endroit.

Correction appliquee :

- `skill/README.md` pointe maintenant vers `../scripts/`, `scripts/sync-catalog.ts`, et indique P1-P7 livres + P8 pending.
- `skill/hosts/claude.md` et `skill/hosts/codex.md` documentent l'installation actuelle et la limite live-LLM.
- `ARCHITECTURE.md` aligne statut, nom final, 70 sous-patterns, hosts livres, et scripts racine.

## Limites restantes

- P7 reste un E2E mock deterministe, pas une preuve que Claude/Codex/Kimi declenchent la skill en live.
- P8 sign-off Opus/Sonnet/Kimi reste ouvert.
- La note `14-cross-host-skill-synthesis-20260511.md` est utile pour Phase 2/P9+, mais ne repondait pas au cadrage exact de cette review interne.

## Validation executee

- `npm run validate` : OK.
- `npm run gen:skill-docs -- --dry-run` : OK, `FRESH: skill/SKILL.md`.
- `npm test` : 19 tests OK.
- `python3 -m unittest discover -s skill/tests -p 'test_*.py'` : 19 tests OK.
- `bash skill/tests/e2e/run.sh` : OK, `result.json` produit.
- `python3 -m compileall scripts skill/tests` : OK.
- `bash -n skill/setup skill/uninstall skill/tests/e2e/run.sh` : OK.
- `git diff --check` : OK.

## Recommendation

Ne pas rouvrir P1-P7 pour du code sauf finding externe nouveau. La prochaine etape correcte reste P8 review/sign-off, avec une attention particuliere sur :

- est-ce que les triggers sont suffisamment utilisables par un vrai LLM pendant le coding ;
- est-ce que le mock P7 est accepte comme preuve Phase 1 ;
- est-ce qu'on planifie P9 `trigger metadata v2` apres P8.
