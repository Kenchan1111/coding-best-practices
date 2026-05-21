#!/usr/bin/env node
import { existsSync } from "node:fs";
import { basename, join } from "node:path";
import {
  EXPECTED_FAMILIES,
  ROOT,
  SKILL_DIR,
  extractCatalogIds,
  listMarkdownFiles,
  parseFrontmatterFile,
  readText,
  relativePath,
} from "./skill-lib.ts";

const EXPECTED_TRIGGERS = [
  "on_write_state_file",
  "on_write_test",
  "on_write_scan_loop",
  "on_review_claim",
  "on_destructive_op",
];
const CHECK_REQUIRED = [
  "family",
  "name",
  "severity",
  "languages",
  "triggers",
  "patterns_matched",
  "fix_pattern",
  "gstack_integration",
];
const TRIGGER_REQUIRED = [
  "trigger",
  "phase",
  "intent",
  "fires_on",
  "calls_checks",
  "suppress_when",
  "preflight_budget",
];
const VALID_SEVERITIES = new Set(["critical", "high", "medium", "low"]);
const REGEX_SIGNAL_KEYS = new Set([
  "bash_command",
  "code_pattern",
  "file_path_regex",
  "javascript_pattern",
  "python_pattern",
  "text_pattern",
  "user_request",
]);

const errors = [];

function requireKeys(path, metadata, keys) {
  for (const key of keys) {
    if (!(key in metadata)) {
      errors.push(`${relativePath(path)}: missing frontmatter key '${key}'`);
    }
  }
}

function requireNonEmptyList(path, metadata, key) {
  if (!Array.isArray(metadata[key]) || metadata[key].length === 0) {
    errors.push(`${relativePath(path)}: '${key}' must be a non-empty list`);
  }
}

function splitSignal(item) {
  const match = String(item).match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
  if (!match) return null;
  let value = match[2].trim();
  if (
    (value.startsWith("'") && value.endsWith("'")) ||
    (value.startsWith('"') && value.endsWith('"'))
  ) {
    value = value.slice(1, -1);
  }
  return { key: match[1], value };
}

function validateTriggerPatterns(path, metadata) {
  for (const item of metadata.fires_on || []) {
    const signal = splitSignal(item);
    if (!signal || !REGEX_SIGNAL_KEYS.has(signal.key)) continue;
    try {
      new RegExp(signal.value);
    } catch (error) {
      errors.push(
        `${relativePath(path)}: invalid ${signal.key} regex '${signal.value}': ${error.message}`
      );
    }
  }
}

function validateChecks() {
  const checksDir = join(SKILL_DIR, "checks");
  const files = listMarkdownFiles(checksDir);
  const byStem = new Map();
  const families = new Set();

  for (const path of files) {
    const stem = basename(path, ".md");
    const { metadata, body } = parseFrontmatterFile(path);
    byStem.set(stem, metadata);
    requireKeys(path, metadata, CHECK_REQUIRED);

    const family = String(metadata.family || "");
    const expectedName = stem.replace(/^[A-R]_/, "");
    families.add(family);

    if (!stem.startsWith(`${family}_`)) {
      errors.push(`${relativePath(path)}: filename must start with '${family}_'`);
    }
    if (metadata.name !== expectedName) {
      errors.push(`${relativePath(path)}: name '${metadata.name}' must equal '${expectedName}'`);
    }
    if (!VALID_SEVERITIES.has(String(metadata.severity))) {
      errors.push(`${relativePath(path)}: invalid severity '${metadata.severity}'`);
    }
    for (const key of ["languages", "triggers", "patterns_matched"]) {
      requireNonEmptyList(path, metadata, key);
    }
    if (!body.includes("## When this check applies")) {
      errors.push(`${relativePath(path)}: missing '## When this check applies' section`);
    }
    if (!body.includes("## Fix-first classification")) {
      errors.push(`${relativePath(path)}: missing '## Fix-first classification' section`);
    }
    if (!body.includes("## Sources catalogue")) {
      errors.push(`${relativePath(path)}: missing '## Sources catalogue' section`);
    }
  }

  for (const family of EXPECTED_FAMILIES) {
    if (!families.has(family)) {
      errors.push(`skill/checks: missing family ${family}`);
    }
  }
  if (files.length !== EXPECTED_FAMILIES.length) {
    errors.push(`skill/checks: expected ${EXPECTED_FAMILIES.length} files, found ${files.length}`);
  }

  return byStem;
}

function validateTriggers(checksByStem) {
  const triggersDir = join(SKILL_DIR, "triggers");
  const files = listMarkdownFiles(triggersDir);
  const triggerNames = new Set();
  const calledChecks = new Set();

  for (const path of files) {
    const stem = basename(path, ".md");
    const { metadata, body } = parseFrontmatterFile(path);
    triggerNames.add(stem);
    requireKeys(path, metadata, TRIGGER_REQUIRED);

    if (metadata.trigger !== stem) {
      errors.push(`${relativePath(path)}: trigger '${metadata.trigger}' must equal filename '${stem}'`);
    }
    for (const key of ["fires_on", "calls_checks", "suppress_when"]) {
      requireNonEmptyList(path, metadata, key);
    }
    validateTriggerPatterns(path, metadata);
    for (const check of metadata.calls_checks || []) {
      calledChecks.add(check);
      if (!checksByStem.has(check)) {
        errors.push(`${relativePath(path)}: calls unknown check '${check}'`);
      }
    }
    if (!body.includes("## Required LLM behavior")) {
      errors.push(`${relativePath(path)}: missing '## Required LLM behavior' section`);
    }
    if (!body.includes("preflight")) {
      errors.push(`${relativePath(path)}: trigger body must contain a preflight instruction`);
    }
  }

  for (const trigger of EXPECTED_TRIGGERS) {
    if (!triggerNames.has(trigger)) {
      errors.push(`skill/triggers: missing trigger ${trigger}`);
    }
  }
  for (const check of checksByStem.keys()) {
    if (!calledChecks.has(check)) {
      errors.push(`skill/checks/${check}.md: orphan check, not referenced by any trigger`);
    }
  }
}

function validateCatalog() {
  const catalogPath = join(SKILL_DIR, "catalog/bug_catalog.md");
  const sourcePath = join(ROOT, "findings/01_bug_catalog.md");
  if (!existsSync(catalogPath)) {
    errors.push("skill/catalog/bug_catalog.md: missing, run node scripts/sync-catalog.ts");
    return;
  }
  if (!existsSync(sourcePath)) {
    errors.push("findings/01_bug_catalog.md: missing canonical source for catalog validation");
    return;
  }

  const expectedIds = extractCatalogIds(readText(sourcePath));
  const expectedFamilies = new Set(expectedIds.map((id) => id[0]));
  for (const family of EXPECTED_FAMILIES) {
    if (!expectedFamilies.has(family)) {
      errors.push(`findings/01_bug_catalog.md: missing family ${family}`);
    }
  }

  const { metadata } = parseFrontmatterFile(catalogPath);
  if (Number(metadata.pattern_count) !== expectedIds.length) {
    errors.push(
      `skill/catalog/bug_catalog.md: pattern_count must match canonical source count ${expectedIds.length}`
    );
  }
  if (!Array.isArray(metadata.catalog_ids)) {
    errors.push("skill/catalog/bug_catalog.md: catalog_ids must be a list");
    return;
  }

  const actualIds = metadata.catalog_ids.map((item) => String(item));
  if (actualIds.length !== expectedIds.length) {
    errors.push(
      `skill/catalog/bug_catalog.md: catalog_ids must contain ${expectedIds.length} canonical entries`
    );
  }
  if (actualIds.join("\n") !== expectedIds.join("\n")) {
    errors.push(
      "skill/catalog/bug_catalog.md: catalog_ids drift from findings/01_bug_catalog.md, run node scripts/sync-catalog.ts"
    );
  }
}

function validateGeneratedSkill() {
  const skillPath = join(SKILL_DIR, "SKILL.md");
  if (!existsSync(skillPath)) {
    errors.push("skill/SKILL.md: missing, run node scripts/gen-skill-docs.ts");
    return;
  }
  const text = readText(skillPath);
  const { metadata } = parseFrontmatterFile(skillPath);
  if (metadata.name !== "coding-best-practices") {
    errors.push("skill/SKILL.md: frontmatter name must be coding-best-practices");
  }
  if (text.includes("{{")) {
    errors.push("skill/SKILL.md: unresolved template placeholder");
  }
  if (!text.includes("AUTO-GENERATED from SKILL.md.tmpl")) {
    errors.push("skill/SKILL.md: missing generated header");
  }
  for (const required of ["## Runtime workflow", "## Triggers", "## Checks"]) {
    if (!text.includes(required)) {
      errors.push(`skill/SKILL.md: missing ${required}`);
    }
  }
}

function main() {
  const checksByStem = validateChecks();
  validateTriggers(checksByStem);
  validateCatalog();
  validateGeneratedSkill();

  if (errors.length > 0) {
    console.error(`Validation failed with ${errors.length} error(s):`);
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  console.log("Validation OK - 18 checks, 5 triggers, catalog, generated SKILL.md.");
}

main();
