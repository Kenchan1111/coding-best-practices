---
id: gpt-5.5-proposition-09-20260504
title: P4 generation et validation de la skill
date: 2026-05-04
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: package.json, scripts/*.ts, skill/SKILL.md, skill/catalog/bug_catalog.md
synopsis: >
  P4 livre la generation deterministe du catalogue, la generation du SKILL.md
  et la validation structurelle checks/triggers/catalog/SKILL. Les commandes
  package sont compatibles `bun run`. Validation initiale effectuee via Node/NPM,
  puis validation litterale Bun cloturee le 2026-05-05 via Conda.
validation:
  - "node scripts/sync-catalog.ts -> Catalog sync OK - 70 IDs, 18 families"
  - "node scripts/gen-skill-docs.ts -> GENERATED: skill/SKILL.md"
  - "node scripts/validate.ts -> Validation OK"
  - "node scripts/gen-skill-docs.ts --dry-run -> FRESH: skill/SKILL.md"
  - "npm run validate -> OK"
  - "npm run gen:skill-docs -- --dry-run -> OK"
  - "2026-05-05 conda run -n coding-best-practices bun run validate -> OK"
  - "2026-05-05 conda run -n coding-best-practices bun run gen:skill-docs -- --dry-run -> OK"
  - "2026-05-05 conda run -n coding-best-practices bun run test -> 13 tests OK"
---

# Contenu livre

- `package.json`
- `scripts/skill-lib.ts`
- `scripts/sync-catalog.ts`
- `scripts/gen-skill-docs.ts`
- `scripts/validate.ts`
- `skill/catalog/bug_catalog.md`
- `skill/SKILL.md`

# Decisions techniques

Les scripts sont `.ts` pour rester alignes avec le plan gstack, mais ils utilisent une syntaxe JavaScript compatible Node 22 et zero dependance externe.

Le `package.json` expose :

```json
{
  "sync:catalog": "node scripts/sync-catalog.ts",
  "validate": "node scripts/validate.ts",
  "gen:skill-docs": "node scripts/gen-skill-docs.ts"
}
```

Donc `bun run validate` et `bun run gen:skill-docs` devraient appeler les memes scripts quand Bun est installe.

# Guarantees P4

- `sync-catalog.ts` extrait 70 IDs A-R depuis `findings/01_bug_catalog.md`, y compris les L1-L10 documentes dans le tableau Bash.
- Le catalogue genere conserve `source_digest`, `pattern_count`, `families`, `catalog_ids`.
- Si les IDs changent entre deux runs, le script bloque sauf `--accept-id-change`.
- `validate.ts` verifie 18 checks, 5 triggers, `calls_checks`, absence de checks orphelins, catalogue genere et `skill/SKILL.md`.
- `gen-skill-docs.ts` genere un `SKILL.md` compact : triggers detailles, checks sous forme d'index actionnable, catalogue en ressource portable.

# Mise a jour 2026-05-05

Bun a ete installe dans un environnement Conda dedie `coding-best-practices`,
sans `sudo` et sans installateur `curl | sh`, en suivant la discipline
forensic-evidence : env isole, `conda-forge`, channel priority stricte, dry-run
avant creation effective.

```bash
conda run -n coding-best-practices bun run validate
conda run -n coding-best-practices bun run gen:skill-docs -- --dry-run
conda run -n coding-best-practices bun run test
```

Resultat : P4 est cloture. Les fichiers `environment.yml` et
`environment.lock.linux-64.txt` documentent la recreation de l'environnement ; le
lock contient les URLs Conda exactes avec SHA256.
