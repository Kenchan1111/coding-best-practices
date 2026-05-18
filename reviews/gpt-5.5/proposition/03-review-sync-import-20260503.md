---
id: gpt-5.5-proposition-03-20260503
title: Import du mecanisme de sync review depuis Depollution_Sols, adapte a ce repo
date: 2026-05-03
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: scripts/sync_reviews.py, scripts/knowledge_os.py, watcher review sync, sorties knowledge et mcp
synopsis: >
  Import du mecanisme de synchronisation documentaire observe dans
  Depollution_Sols, adapte a l'arborescence `reviews/` de ce repo. Le point
  cle de cette adaptation est la prevention explicite des ecrasements: toute
  collision de nom avec contenu different est refusee et remontee en erreur.
validation:
  - "python3 -m compileall scripts -> OK"
  - "python3 scripts/sync_reviews.py -> OK, 0 collision, 0 derive, 0 erreur"
sources:
  - /home/zack/Documents/Depollution_Sols /scripts/sync_reviews.py
  - /home/zack/Documents/Depollution_Sols /scripts/knowledge_os.py
  - /home/zack/Documents/Notebook_LLM_Tana/scripts/sync_reviews_watch.py
---

# Ce qui a ete importe

- `scripts/knowledge_os.py`
- `scripts/sync_reviews.py`
- `scripts/sync_reviews_watch.py`
- `install-review-sync-user-service.sh`
- `systemd/dict-ai-coding-review-sync-watch.service`
- `REVIEW_SYNC.md`

# Adaptations par rapport a la source

1. Port de `review/` vers `reviews/`
2. Port des agents vers `claude-opus`, `claude-sonnet`, `gpt-5.5`
3. Sorties generees dans `knowledge/80_summaries/` et `mcp/catalog.json`
4. Ajout d'un refus explicite d'ecrasement sur collision de nom + digest different
5. Retour code non nul en cas de collision ou de frontmatter invalide

# Verification anti-ecrasement

Le script ne remplace jamais un document source existant.

Comportement implemente :
- cible absente -> copie
- cible presente avec meme digest -> noop
- cible presente avec digest different -> collision, sync refuse, aucun ecrasement

# Premier resultat de sync

Execution validee sur ce repo :
- `3` diffusions de `reviews/global_handoff/00-zack-arbitrage-q1-q5-20260503.md`
- creation des dossiers `reviews/<agent>/handoff/`
- creation de `knowledge/80_summaries/team_review_{latest,digest,changelog}.md`
- creation de `mcp/catalog.json`

Aucun document n'a ete ecrase pendant cette execution.

# Next step recommande

1. Claude relit le mecanisme de collision et le placement des sorties
2. Si le cadrage est accepte, utiliser `python3 scripts/sync_reviews.py` comme commande standard
3. Optionnel ensuite : activer le watcher systemd pour la sync continue
