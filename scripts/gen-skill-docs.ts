#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { basename, join } from "node:path";
import {
  ROOT,
  SKILL_DIR,
  atomicWrite,
  firstParagraphAfterHeading,
  listMarkdownFiles,
  parseFrontmatterFile,
  readText,
  relativePath,
  stripFrontmatter,
} from "./skill-lib.ts";

const TEMPLATE = join(SKILL_DIR, "SKILL.md.tmpl");
const OUTPUT = join(SKILL_DIR, "SKILL.md");
const DRY_RUN = process.argv.includes("--dry-run");

function ensureCatalog() {
  execFileSync(process.execPath, [join(ROOT, "scripts/sync-catalog.ts")], {
    cwd: ROOT,
    stdio: "inherit",
  });
}

function renderCatalog() {
  const catalogPath = join(SKILL_DIR, "catalog/bug_catalog.md");
  if (!existsSync(catalogPath)) {
    throw new Error("skill/catalog/bug_catalog.md missing after catalog sync");
  }
  const { metadata } = parseFrontmatterFile(catalogPath);
  const families = Array.isArray(metadata.families) ? metadata.families.join(", ") : "A-R";
  return [
    "- Source portable : `catalog/bug_catalog.md`",
    `- Source canonique : \`${metadata.generated_from}\``,
    `- Digest source : \`${metadata.source_digest}\``,
    `- Couverture : ${metadata.pattern_count} IDs documentes, familles ${families}`,
    "- Lire le catalogue seulement quand un check demande la preuve source ou le detail historique.",
  ].join("\n");
}

function renderTriggers() {
  const files = listMarkdownFiles(join(SKILL_DIR, "triggers"));
  return files
    .map((path) => {
      const { metadata, body } = parseFrontmatterFile(path);
      const calls = (metadata.calls_checks || []).map((check) => `\`${check}\``).join(", ");
      const fires = (metadata.fires_on || []).slice(0, 4).map((item) => `  - ${item}`).join("\n");
      return [
        `### ${metadata.trigger}`,
        "",
        `- Fichier : \`${relativePath(path).replace("skill/", "")}\``,
        `- Phase : \`${metadata.phase}\``,
        `- Intent : ${metadata.intent}`,
        `- Checks : ${calls}`,
        "- Signaux principaux :",
        fires,
        "",
        stripFrontmatter(body),
      ].join("\n");
    })
    .join("\n\n");
}

function renderChecks() {
  const files = listMarkdownFiles(join(SKILL_DIR, "checks"));
  return files
    .map((path) => {
      const { metadata, body } = parseFrontmatterFile(path);
      const when = firstParagraphAfterHeading(body, "When this check applies");
      const fixFirst = firstParagraphAfterHeading(body, "Fix-first classification");
      return [
        `### ${basename(path, ".md")}`,
        "",
        `- Fichier : \`${relativePath(path).replace("skill/", "")}\``,
        `- Famille : \`${metadata.family}\``,
        `- Nom : \`${metadata.name}\``,
        `- Severite : \`${metadata.severity}\``,
        `- Integration gstack : \`${metadata.gstack_integration}\``,
        `- Quand lire : ${when}`,
        `- Fix-First : ${fixFirst}`,
      ].join("\n");
    })
    .join("\n\n");
}

function insertGeneratedHeader(content) {
  const marker = "\n---";
  const end = content.indexOf(marker, 4);
  if (end === -1) {
    throw new Error("template frontmatter is unterminated");
  }
  const insertAt = content.indexOf("\n", end + marker.length) + 1;
  const header = [
    "<!-- AUTO-GENERATED from SKILL.md.tmpl - do not edit directly -->",
    "<!-- Regenerate: node scripts/gen-skill-docs.ts -->",
    "",
  ].join("\n");
  return content.slice(0, insertAt) + header + content.slice(insertAt);
}

function renderSkill() {
  ensureCatalog();
  let content = readText(TEMPLATE);
  content = content
    .replace("{{CATALOG}}", () => renderCatalog())
    .replace("{{TRIGGERS}}", () => renderTriggers())
    .replace("{{CHECKS}}", () => renderChecks());

  if (content.includes("{{")) {
    throw new Error("unresolved template placeholder remains in SKILL.md");
  }

  return insertGeneratedHeader(content).trimEnd() + "\n";
}

function main() {
  const content = renderSkill();
  if (DRY_RUN) {
    const existing = existsSync(OUTPUT) ? readText(OUTPUT) : "";
    if (existing !== content) {
      console.error("STALE: skill/SKILL.md");
      process.exit(1);
    }
    console.log("FRESH: skill/SKILL.md");
    return;
  }

  atomicWrite(OUTPUT, content);
  console.log("GENERATED: skill/SKILL.md");
}

main();
