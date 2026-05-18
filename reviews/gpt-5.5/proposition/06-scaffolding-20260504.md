---
id: gpt-5.5-proposition-06-20260504
title: P1 scaffolding initial de la skill coding-best-practices
date: 2026-05-04
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: skill/SKILL.md.tmpl, skill/README.md, skill/hosts, skill layout
synopsis: >
  Premier livrable P1 : structure `skill/` materialisee, template minimal,
  README de perimetre et notes host Claude/Codex/gstack. Aucun check, trigger,
  generateur ou setup n'est implemente dans ce livrable. Correction de cadrage :
  la cible est une augmentation gstack-compatible, pas une plomberie concurrente.
validation:
  - "find skill -maxdepth 3 -> layout P1 present"
  - "python3 -m compileall scripts -> OK"
---

# Contenu livre

- `skill/SKILL.md.tmpl`
- `skill/README.md`
- `skill/hosts/claude.md`
- `skill/hosts/codex.md`
- `skill/hosts/gstack.md`
- `skill/catalog/.gitkeep`
- `skill/checks/.gitkeep`
- `skill/triggers/.gitkeep`
- `skill/scripts/.gitkeep`
- `skill/tests/.gitkeep`
- `skill/bin/.gitkeep`

# Decisions respectees

- D5 : `catalog/` reserve a une copie generee, pas a un symlink
- D6 : pas de promesse d'acceptation sans smoke test dynamique futur
- D1 : extension gstack-compatible, sans modification durable du clone `gstack/` tant qu'un fork upstream n'est pas decide
- P1 strict : pas de checks P2, pas de generateur P4, pas de setup P6

# Next step

P2 peut commencer avec les premieres familles de checks :

1. `A_atomic_write`
2. `B_cascade_failure`
3. `D_iteration_semantics`
4. `E_llm_hallucination`
