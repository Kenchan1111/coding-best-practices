#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import difflib
import hashlib
import json
import re
import sys
from typing import Any

from knowledge_os import (
    GLOBAL_HANDOFF_DIR,
    REVIEW_ROOT,
    ROOT,
    atomic_write,
    discover_agents,
    file_digest,
    load_markdown_document,
    load_review_documents,
    markdown_link,
    parse_date_like,
    render_markdown_document,
)

SUMMARY_FILE = ROOT / "knowledge/80_summaries/team_review_latest.md"
DIGEST_FILE = ROOT / "knowledge/80_summaries/team_review_digest.md"
CHANGELOG_FILE = ROOT / "knowledge/80_summaries/team_review_changelog.md"
CATALOG_FILE = ROOT / "mcp/catalog.json"

REQUIRED_FRONTMATTER = {"id", "title", "date", "status"}
SYNC_VARIANT_RE = re.compile(r"__sync-conflict-v\d{2}-[0-9a-f]{12}$")
SYNC_METADATA_PREFIX = "sync_"


def _short_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _is_sync_variant(path: Path) -> bool:
    return SYNC_VARIANT_RE.search(path.stem) is not None


def _strip_sync_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metadata.items()
        if not str(key).startswith(SYNC_METADATA_PREFIX) and value is not None
    }


def _metadata_digest(metadata: dict[str, Any]) -> str:
    payload = json.dumps(
        _strip_sync_metadata(metadata),
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return _short_digest(payload)


def _body_digest(body: str) -> str:
    return _short_digest(body.rstrip())


def _variant_base_stem(path: Path) -> str:
    return SYNC_VARIANT_RE.sub("", path.stem)


def _variant_candidates(target: Path) -> list[Path]:
    base_stem = _variant_base_stem(target)
    pattern = f"{base_stem}__sync-conflict-v*-*{target.suffix}"
    return sorted(candidate for candidate in target.parent.glob(pattern) if candidate.is_file())


def _is_unmodified_managed_copy(target: Path) -> bool:
    document = load_markdown_document(target, infer_review=True)
    if not bool(document.metadata.get("sync_managed_copy", False)):
        return False

    expected_body_digest = str(document.metadata.get("sync_source_body_digest") or "")
    expected_metadata_digest = str(document.metadata.get("sync_source_metadata_digest") or "")
    return (
        expected_body_digest == _body_digest(document.body)
        and expected_metadata_digest == _metadata_digest(document.metadata)
    )


def _write_managed_copy(source: Path, target: Path) -> None:
    document = load_markdown_document(source, infer_review=True)
    metadata = _strip_sync_metadata(dict(document.metadata))
    metadata["sync_managed_copy"] = True
    metadata["sync_source_path"] = source.relative_to(ROOT).as_posix()
    metadata["sync_source_digest"] = file_digest(source)
    metadata["sync_source_body_digest"] = _body_digest(document.body)
    metadata["sync_source_metadata_digest"] = _metadata_digest(metadata)
    atomic_write(target, render_markdown_document(metadata, document.body))


def _managed_source_path(path: Path) -> str | None:
    document = load_markdown_document(path, infer_review=True)
    if not bool(document.metadata.get("sync_managed_copy", False)):
        return None
    source_path = str(document.metadata.get("sync_source_path") or "")
    return source_path or None


def _find_existing_variant(source: Path, target: Path) -> Path | None:
    source_rel = source.relative_to(ROOT).as_posix()
    source_digest = file_digest(source)

    for candidate in _variant_candidates(target):
        document = load_markdown_document(candidate, infer_review=True)
        if (
            str(document.metadata.get("sync_source_path") or "") == source_rel
            and str(document.metadata.get("sync_source_digest") or "") == source_digest
        ):
            return candidate

    return None


def _next_variant_path(target: Path, source_digest: str) -> tuple[Path, int]:
    version = 1
    base_stem = _variant_base_stem(target)
    while True:
        candidate = target.with_name(
            f"{base_stem}__sync-conflict-v{version:02d}-{source_digest}{target.suffix}"
        )
        if not candidate.exists():
            return candidate, version
        version += 1


def _diff_summary(existing: Path, source: Path) -> dict[str, object]:
    existing_lines = existing.read_text(encoding="utf-8", errors="replace").splitlines()
    source_lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    diff_lines = list(
        difflib.unified_diff(
            existing_lines,
            source_lines,
            fromfile=existing.name,
            tofile=source.name,
            n=1,
            lineterm="",
        )
    )
    added_lines = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    removed_lines = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
    changed_hunks = sum(1 for line in diff_lines if line.startswith("@@"))

    preview: list[str] = []
    for line in diff_lines:
        if line.startswith(("---", "+++")):
            continue
        preview.append(line)
        if len(preview) >= 12:
            break

    return {
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "changed_hunks": changed_hunks,
        "preview": preview,
    }


def _write_variant_copy(source: Path, target: Path) -> tuple[Path, str]:
    existing_digest = file_digest(target)
    source_digest = file_digest(source)
    diff_summary = _diff_summary(target, source)

    existing_variant = _find_existing_variant(source, target)
    if existing_variant is not None:
        return existing_variant, (
            "VARIANTE deja presente: "
            f"{existing_variant.relative_to(ROOT).as_posix()} "
            f"(source: {source.relative_to(ROOT).as_posix()})"
        )

    variant_path, version = _next_variant_path(target, source_digest)
    document = load_markdown_document(source, infer_review=True)
    metadata = _strip_sync_metadata(dict(document.metadata))

    base_id = str(metadata.get("sync_base_id") or metadata.get("id") or document.stable_id)
    base_title = str(metadata.get("sync_base_title") or metadata.get("title") or document.title)
    metadata["id"] = f"{base_id}__sync-conflict-v{version:02d}"
    metadata["title"] = f"{base_title} [sync conflict v{version:02d}]"
    metadata["sync_base_id"] = base_id
    metadata["sync_base_title"] = base_title
    metadata["sync_variant"] = True
    metadata["sync_variant_version"] = version
    metadata["sync_variant_created_at"] = datetime.now().isoformat(timespec="minutes")
    metadata["sync_variant_reason"] = "filename-collision-different-digest"
    metadata["sync_original_filename"] = target.name
    metadata["sync_source_path"] = source.relative_to(ROOT).as_posix()
    metadata["sync_source_digest"] = source_digest
    metadata["sync_conflicts_with_path"] = target.relative_to(ROOT).as_posix()
    metadata["sync_conflicts_with_digest"] = existing_digest
    metadata["sync_diff_summary"] = diff_summary

    atomic_write(variant_path, render_markdown_document(metadata, document.body))
    return variant_path, (
        "VARIANTE creee: "
        f"{variant_path.relative_to(ROOT).as_posix()} "
        f"(source: {source.relative_to(ROOT).as_posix()}, "
        f"conflit: {target.relative_to(ROOT).as_posix()}, "
        f"+{diff_summary['added_lines']}/-{diff_summary['removed_lines']})"
    )


def _copy_without_overwrite(source: Path, target: Path) -> tuple[bool, str | None]:
    if source.resolve() == target.resolve():
        return False, None

    target.parent.mkdir(parents=True, exist_ok=True)
    source_rel = source.relative_to(ROOT).as_posix()
    source_digest = file_digest(source)

    if not target.exists():
        _write_managed_copy(source, target)
        return True, None

    target_document = load_markdown_document(target, infer_review=True)
    if bool(target_document.metadata.get("sync_managed_copy", False)):
        target_source = str(target_document.metadata.get("sync_source_path") or "")
        if target_source == source_rel:
            if not _is_unmodified_managed_copy(target):
                _variant_path, message = _write_variant_copy(source, target)
                return True, message

            if str(target_document.metadata.get("sync_source_digest") or "") == source_digest:
                return False, None

            _write_managed_copy(source, target)
            return True, None

    if source_digest == file_digest(target):
        return False, None

    _variant_path, message = _write_variant_copy(source, target)
    return True, message


def collect_handoffs(agents: tuple[str, ...]) -> tuple[int, list[str]]:
    collected = 0
    variant_notes: list[str] = []
    GLOBAL_HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

    for agent in agents:
        agent_handoff_dir = REVIEW_ROOT / agent / "handoff"
        if not agent_handoff_dir.exists():
            continue

        for handoff_file in sorted(agent_handoff_dir.glob("*.md")):
            if _is_sync_variant(handoff_file) or _managed_source_path(handoff_file):
                continue
            copied, collision = _copy_without_overwrite(
                handoff_file, GLOBAL_HANDOFF_DIR / handoff_file.name
            )
            if copied:
                collected += 1
            if collision:
                variant_notes.append(collision)

    return collected, variant_notes


def broadcast_handoffs(agents: tuple[str, ...]) -> tuple[int, list[str]]:
    broadcasted = 0
    variant_notes: list[str] = []
    if not GLOBAL_HANDOFF_DIR.exists():
        return broadcasted, variant_notes

    for handoff_file in sorted(GLOBAL_HANDOFF_DIR.glob("*.md")):
        if _is_sync_variant(handoff_file):
            continue

        original_source = _managed_source_path(handoff_file)
        for agent in agents:
            target_dir = REVIEW_ROOT / agent / "handoff"
            target = target_dir / handoff_file.name
            if original_source == target.relative_to(ROOT).as_posix():
                continue

            copied, collision = _copy_without_overwrite(
                handoff_file, target
            )
            if copied:
                broadcasted += 1
            if collision:
                variant_notes.append(collision)

    return broadcasted, variant_notes


def collect_propositions(agents: tuple[str, ...]) -> tuple[list[dict], list[str], list[str]]:
    propositions: list[dict] = []
    warnings: list[str] = []
    errors: list[str] = []

    for document in load_review_documents("proposition", agents):
        metadata = document.metadata

        if not document.has_frontmatter:
            errors.append(f"{document.relative_path}: frontmatter manquant")
        else:
            missing = REQUIRED_FRONTMATTER - set(metadata.keys())
            if missing:
                errors.append(
                    f"{document.relative_path}: champs requis manquants: {', '.join(sorted(missing))}"
                )

        title = str(metadata.get("title") or document.title)
        date = str(metadata.get("date") or "N/A")
        status = str(metadata.get("status") or "draft")
        agent = str(metadata.get("agent") or "unknown")
        identifier = str(metadata.get("id") or document.stable_id)

        if date == "N/A":
            warnings.append(f"{document.relative_path}: date manquante")

        must_read = bool(metadata.get("must_read", False))

        propositions.append(
            {
                "agent": agent,
                "title": title,
                "id": identifier,
                "status": status,
                "date": date,
                "path": document.relative_path,
                "has_frontmatter": "yes" if document.has_frontmatter else "no",
                "synopsis": document.synopsis,
                "digest": file_digest(document.path),
                "must_read": must_read,
            }
        )

    propositions.sort(
        key=lambda item: (
            parse_date_like(item["date"]) or datetime.min,
            item["agent"],
            item["title"],
        ),
        reverse=True,
    )
    return propositions, warnings, errors


def write_summary(
    propositions: list[dict],
    warnings: list[str],
    errors: list[str],
    variant_notes: list[str],
    collected: int,
    broadcasted: int,
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Rapport global des reviews",
        f"Derniere mise a jour : {timestamp}",
        "",
        f"- Handoffs collectes : {collected}",
        f"- Handoffs diffuses : {broadcasted}",
        f"- Propositions actives : {len(propositions)}",
        f"- Variantes creees : {len(variant_notes)}",
        "",
    ]

    if propositions:
        lines += [
            "| Agent | Titre | ID | Statut | Date | Frontmatter |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for proposition in propositions:
            target = REVIEW_ROOT.parent / proposition["path"]
            link = markdown_link(target, SUMMARY_FILE, proposition["title"])
            lines.append(
                f"| {proposition['agent']} | {link} | {proposition['id']} | "
                f"`{proposition['status']}` | {proposition['date']} | {proposition['has_frontmatter']} |"
            )
    else:
        lines.append("Aucune proposition active detectee.")

    if variant_notes:
        lines += ["", "## Variantes de collision (aucun ecrasement effectue)", ""]
        lines += [f"- {item}" for item in variant_notes]

    if errors:
        lines += ["", "## Erreurs (frontmatter non conforme, bloquant)", ""]
        lines += [f"- {item}" for item in errors]

    if warnings:
        lines += ["", "## Warnings", ""]
        lines += [f"- {item}" for item in warnings]

    atomic_write(SUMMARY_FILE, "\n".join(lines) + "\n")


def write_digest(propositions: list[dict]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Digest des reviews",
        f"Mis a jour : {timestamp}",
        "",
        "_Une entree par proposition avec synopsis._",
        "_Pour le detail complet, suivre les liens vers les fichiers source._",
        "",
    ]

    by_agent: dict[str, list[dict]] = defaultdict(list)
    for proposition in propositions:
        by_agent[proposition["agent"]].append(proposition)

    for agent, docs in sorted(by_agent.items()):
        lines.append(f"## {agent.upper()}")
        lines.append("")
        for doc in docs:
            target = REVIEW_ROOT.parent / doc["path"]
            link = markdown_link(target, DIGEST_FILE, doc["title"])
            must_read_flag = " - LECTURE INTEGRALE REQUISE" if doc.get("must_read") else ""
            lines.append(f"### {link}{must_read_flag}")
            lines.append(
                f"**Statut :** `{doc['status']}` | **Date :** {doc['date']} | **ID :** `{doc['id']}`"
            )
            synopsis = doc.get("synopsis", "").strip()
            if synopsis:
                lines.append("")
                lines.append(f"> {synopsis}")
            lines.append("")

    atomic_write(DIGEST_FILE, "\n".join(lines) + "\n")


def append_changelog(
    propositions: list[dict],
    warnings: list[str],
    errors: list[str],
    variant_notes: list[str],
    collected: int,
    broadcasted: int,
) -> None:
    CHANGELOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"\n## Sync {timestamp}",
        f"- Handoffs collectes : {collected}",
        f"- Handoffs diffuses : {broadcasted}",
        f"- Propositions indexees : {len(propositions)}",
        f"- Variantes creees : {len(variant_notes)}",
        f"- Warnings : {len(warnings)} | Erreurs : {len(errors)}",
    ]
    if variant_notes:
        lines.append("- Variantes de collision : " + " | ".join(variant_notes[:5]))
    if errors:
        lines.append("- Erreurs bloquantes : " + " | ".join(errors[:5]))
    with open(CHANGELOG_FILE, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_catalog(
    propositions: list[dict],
    warnings: list[str],
    errors: list[str],
    variant_notes: list[str],
    collected: int,
    broadcasted: int,
) -> list[str]:
    drift: list[str] = []

    if CATALOG_FILE.exists():
        try:
            previous = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
            prev_by_id = {item["id"]: item for item in previous.get("propositions_active", [])}
            current_ids = {item["id"] for item in propositions}

            for identifier, previous_item in prev_by_id.items():
                if identifier not in current_ids:
                    drift.append(
                        "DISPARU depuis dernier sync: "
                        f"{identifier} ({previous_item.get('agent')}) - {previous_item.get('path')}"
                    )

            current_by_id = {item["id"]: item for item in propositions}
            for identifier, previous_item in prev_by_id.items():
                current = current_by_id.get(identifier)
                if current and previous_item.get("digest") and previous_item.get("digest") != current.get("digest"):
                    drift.append(
                        "MODIFIE depuis dernier sync: "
                        f"{identifier} ({current.get('agent')}) - {current.get('path')}"
                    )
        except Exception as exc:
            drift.append(f"Impossible de lire le catalog precedent : {exc}")

    counts_by_agent: dict[str, int] = defaultdict(int)
    for proposition in propositions:
        counts_by_agent[proposition["agent"]] += 1

    payload = {
        "last_sync": datetime.now().isoformat(timespec="seconds"),
        "stats": {
            "collected": collected,
            "broadcasted": broadcasted,
            "propositions": len(propositions),
            "warnings": len(warnings),
            "errors": len(errors),
            "variants": len(variant_notes),
            "drift": len(drift),
            "by_agent": dict(sorted(counts_by_agent.items())),
        },
        "propositions_active": propositions,
        "drift": drift,
        "variant_notes": variant_notes,
        "errors": errors,
        "warnings": warnings,
    }
    atomic_write(CATALOG_FILE, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return drift


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronise les reviews et handoffs du repo.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executer un cycle de sync puis sortir. C'est le comportement par defaut.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv)
    agents = discover_agents()
    collected, collect_variant_notes = collect_handoffs(agents)
    broadcasted, broadcast_variant_notes = broadcast_handoffs(agents)
    variant_notes = collect_variant_notes + broadcast_variant_notes
    propositions, warnings, errors = collect_propositions(agents)

    write_summary(propositions, warnings, errors, variant_notes, collected, broadcasted)
    write_digest(propositions)
    append_changelog(propositions, warnings, errors, variant_notes, collected, broadcasted)
    drift = write_catalog(propositions, warnings, errors, variant_notes, collected, broadcasted)

    print(
        f"Review sync OK - {collected} collectes, {broadcasted} diffusions, "
        f"{len(propositions)} propositions, {len(variant_notes)} variantes, "
        f"{len(drift)} derives detectees."
    )

    if drift:
        print("\n[DRIFT] Documents modifies ou disparus depuis le dernier sync :")
        for item in drift:
            print(f"  - {item}")

    if variant_notes:
        print("\n[VARIANTE] Documents divergents copies sous nom versionne :")
        for item in variant_notes:
            print(f"  - {item}")

    if errors:
        print(f"\n[ERREUR] {len(errors)} proposition(s) sans frontmatter conforme :")
        for item in errors:
            print(f"  - {item}")

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
