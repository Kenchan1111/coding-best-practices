# coding-best-practices

Extension gstack-compatible de coding best practices pour reduire les erreurs recurrentes observees dans les reviews LLM.

## Ce que contient ce dossier

- `SKILL.md.tmpl` : template source du `SKILL.md` genere
- `catalog/` : copie generee du catalogue canonique
- `checks/` : 18 familles de checks
- `triggers/` : contextes qui chargent les checks
- `../scripts/` : generation et validation
- `tests/` : tests unitaires et fixtures
- `hosts/` : notes d'installation par host
- `bin/` : utilitaires runtime futurs

## Relation avec gstack

Ce dossier ne doit pas devenir une deuxieme plomberie de skill. La Phase 1 produit un contenu portable et greffable sur gstack :

- generation alignee sur `gstack/scripts/gen-skill-docs.ts`
- hosts alignes sur `gstack/hosts/`
- review discipline alignee sur `gstack/review/`
- operations destructrices coherentes avec `gstack/careful/` et `gstack/guard/`

Le clone `../gstack/` est une reference ignoree par ce repo. Ne pas le modifier comme source durable sans decider explicitement d'un fork upstream.

## Source de verite

Le catalogue canonique reste `findings/01_bug_catalog.md`.

Phase 1 utilise une copie generee dans `skill/catalog/` pour garder une skill installable et portable. Le script `scripts/sync-catalog.ts` regenere cette copie depuis la source canonique.

## Installation

Pour installer la skill dans Claude Code, Codex et Kimi :

```bash
bash skill/setup --host all --yes
```

Pour verifier sans modifier les repertoires d'agents :

```bash
bash skill/setup --host all --dry-run
```

Pour desinstaller uniquement les liens geres par ce repo :

```bash
bash skill/uninstall --host all --yes
```

Pour le developpement local, utiliser l'environnement Conda isole du repo :

```bash
conda activate coding-best-practices
bun run validate
bun run gen:skill-docs -- --dry-run
bun run test
```

Recreation de l'environnement :

```bash
conda create -y -n coding-best-practices -c conda-forge --strict-channel-priority bun=1.3.11 "nodejs>=22,<23" "python>=3.13,<3.14"
```

Pour une reproduction Linux stricte, preferer `environment.lock.linux-64.txt`,
qui contient les URLs Conda exactes et les SHA256.

Installations ciblees Phase 1 :

- `~/.claude/skills/coding-best-practices/`
- `~/.codex/skills/coding-best-practices/`
- `~/.kimi/skills/coding-best-practices/`
- compatible avec installation gstack comme skill additionnelle ou sous-skill dediee

## Statut

P1-P7 livres : scaffolding, 18 checks, 5 triggers contextuels, generation,
validation Bun, setup/install/uninstall idempotents, et E2E mock deterministe.
La Phase 1 attend encore P8 : reviews croisees Opus/Sonnet/Kimi et sign-off.
