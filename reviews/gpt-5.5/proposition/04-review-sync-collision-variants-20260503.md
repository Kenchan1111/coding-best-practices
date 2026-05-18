---
id: gpt-5.5-proposition-04-20260503
title: Correction du comportement de collision du review sync
date: 2026-05-03
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: scripts/sync_reviews.py, scripts/knowledge_os.py, REVIEW_SYNC.md
synopsis: >
  Le review sync ne bloque plus sur collision de nom avec digest different.
  Il cree maintenant une variante versionnee avec frontmatter enrichi, ce qui
  rend les divergences explicites sans ecraser le document deja present.
validation:
  - "python3 -m compileall scripts -> OK"
  - "test de collision controle -> variante versionnee creee, aucun ecrasement"
  - "python3 scripts/sync_reviews.py -> OK apres nettoyage du test"
---

# Changement

Avant :
- collision de nom + digest different -> refus, code non nul

Maintenant :
- collision de nom + digest different -> creation d'une variante versionnee
- ajout d'un resume de diff dans le frontmatter
- aucun ecrasement du fichier deja present

# Rationale

Deux fichiers de meme nom mais de contenu different ne sont pas des duplicatas.
Les ignorer silencieusement ou les traiter comme erreur terminale masque une
divergence documentaire reelle.

# Effet concret

Le sync produit des fichiers du type :

- `...__sync-conflict-v01-<digest>.md`

Le frontmatter de la variante ajoute notamment :

- `sync_source_path`
- `sync_source_digest`
- `sync_conflicts_with_path`
- `sync_conflicts_with_digest`
- `sync_diff_summary`

# Next step recommande

Porter la meme logique dans `Depollution_Sols /scripts/sync_reviews.py`.
