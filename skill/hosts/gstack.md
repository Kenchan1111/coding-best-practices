# Contrat de greffe gstack

`coding-best-practices` augmente gstack. Le clone `../gstack/` reste la reference de plomberie, pas une dependance vendoree modifiee en douce.

## Points de greffe

- Generation : s'aligner sur `gstack/scripts/gen-skill-docs.ts` et ses resolvers.
- Hosts : reutiliser le modele `gstack/hosts/*.ts` pour Claude, Codex, Factory, OpenCode et autres hosts.
- Review : enrichir `gstack/review/` avec les familles non couvertes par gstack, sans dupliquer les checks deja forts.
- Safety : garder les operations destructrices coherentes avec `gstack/careful/` et `gstack/guard/`.
- Slop scan : reutiliser `gstack/slop-scan.config.json` et `gstack/scripts/slop-diff.ts` si le stack Bun est adopte.

## Regle de non-divergence

Avant d'ajouter un script dans `skill/scripts/`, verifier si gstack a deja l'equivalent. Si oui, adapter ou envelopper le pattern existant. Creer du nouveau code seulement quand le besoin est propre au catalogue A-R.

## Source durable

Les changements Phase 1 vivent dans ce repo. Modifier directement `../gstack/` exige une decision explicite de fork ou de PR upstream.
