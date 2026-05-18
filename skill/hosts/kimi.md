# Host Kimi

Kimi est vise comme reviewer systemique et consommateur optionnel de la skill.

## Installation cible

```text
~/.kimi/skills/coding-best-practices/
```

## Installation

```bash
bash skill/setup --host kimi --yes
```

## Comportement attendu

- Utiliser `coding-best-practices` comme catalogue empirique A-R pendant les reviews systemiques.
- Garder les findings Kimi separes des findings Claude/Codex jusqu'a la synthese.
- Charger uniquement les checks references par le trigger actif.
- Pour les claims `file:line`, appliquer `E_llm_hallucination` avant publication.

## Limites connues

- Phase 1 installe un artefact Markdown ; elle ne prouve pas que Kimi charge automatiquement la skill.
- Il n'y a pas encore de smoke test live Kimi.
- La parite comportementale multi-host reste Phase 2.
