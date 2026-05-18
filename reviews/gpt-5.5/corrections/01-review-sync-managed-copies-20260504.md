---
id: gpt-5.5-correction-01-20260504
title: Correction sync reviews - variantes non rebroadcast et copies gerees
date: 2026-05-04
status: applied
agent: gpt-5.5
review_kind: corrections
scope: scripts/sync_reviews.py, reviews/*/handoff
synopsis: >
  Correction du bug detecte pendant la validation : les fichiers
  `__sync-conflict-*` etaient repris comme handoffs normaux et rebroadcastes,
  produisant une cascade de variantes. Le sync distingue maintenant les copies
  gerees des sources et ignore les variantes pendant collect/broadcast.
---

# Probleme

Le script `scripts/sync_reviews.py` respectait la regle "ne pas ecraser si digest different" mais traitait ensuite les variantes `__sync-conflict-*` comme des handoffs normaux.

Effet observe :
- creation de variantes multiples pour un meme handoff
- rebroadcast des variantes vers tous les agents
- impossibilite d'obtenir deux runs de sync stables

# Correction appliquee

- Ajout de detection `_is_sync_variant`.
- Exclusion des variantes pendant `collect_handoffs` et `broadcast_handoffs`.
- Ajout de copies gerees avec metadata `sync_managed_copy`, `sync_source_path`, `sync_source_digest`, `sync_source_body_digest`, `sync_source_metadata_digest`.
- Rafraichissement automatique d'une copie geree seulement si elle n'a pas ete modifiee localement.
- Conservation du comportement demande pour les vrais conflits : si un fichier independant existe avec digest different, creation d'une variante versionnee avec resume de diff en frontmatter.
- Nettoyage cible des variantes generees par le run defectueux et regeneration des miroirs depuis `reviews/global_handoff/`.

# Garanties

Les sources `reviews/global_handoff/00-zack-arbitrage-q1-q5-20260503.md` et `reviews/global_handoff/01-zack-arbitrage-d1-d6-20260504.md` n'ont pas ete supprimees.

Les fichiers supprimes etaient des miroirs agent generes dans `reviews/*/handoff/` ou des variantes parasites `__sync-conflict-*`, puis ils ont ete regeneres par le sync.

# Validation

- `python3 scripts/sync_reviews.py` : 8 diffusions, 0 variantes, 0 derives.
- `python3 scripts/sync_reviews.py` : 0 diffusion, 0 variante, 0 derive.
- `find reviews -name '*__sync-conflict-*' -type f` : aucun resultat.
- `python3 -m compileall scripts` : OK.
