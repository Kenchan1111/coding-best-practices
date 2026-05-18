# Review Sync

Ce repo peut maintenant synchroniser ses reviews sans copier-coller manuel.

## Source de verite

- Les documents source restent dans `reviews/<agent>/...`
- Le handoff commun reste dans `reviews/global_handoff/`

## Commande manuelle

```bash
python3 scripts/sync_reviews.py
```

Sorties generees :
- `knowledge/80_summaries/team_review_latest.md`
- `knowledge/80_summaries/team_review_digest.md`
- `knowledge/80_summaries/team_review_changelog.md`
- `mcp/catalog.json`

## Watcher optionnel

```bash
python3 scripts/sync_reviews_watch.py
```

Ou en service user systemd :

```bash
bash install-review-sync-user-service.sh
```

## Garantie anti-ecrasement

Le sync ne remplace jamais un document source existant.

Cas couverts :
- si le fichier cible n'existe pas, il est copie
- si le fichier cible existe avec le meme digest, rien n'est fait
- si le fichier cible existe avec un contenu different, le sync cree une variante versionnee au lieu d'ecraser

## Variantes explicites

Quand deux fichiers ont le meme nom mais un contenu different :

- le fichier deja present reste intact
- le nouveau fichier est copie sous un nom versionne
- le frontmatter de la variante est enrichi avec :
  - le chemin source
  - le digest source
  - le chemin du fichier en conflit
  - le digest du fichier en conflit
  - un resume de diff

Le but est d'eviter les duplicatas implicites. Si les fichiers sont differents, la divergence devient explicite.

Cette protection vaut pour :
- la collecte `reviews/<agent>/handoff -> reviews/global_handoff`
- la diffusion `reviews/global_handoff -> reviews/<agent>/handoff`
