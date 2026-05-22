#!/usr/bin/env node
import { existsSync } from "node:fs";
import { join } from "node:path";
import {
  EXPECTED_FAMILIES,
  ROOT,
  atomicWrite,
  extractCatalogIds,
  parseFrontmatter,
  readText,
  sha256Short,
  yamlList,
} from "./skill-lib.ts";

const SOURCE = join(ROOT, "findings/01_bug_catalog.md");
const TARGET = join(ROOT, "skill/catalog/bug_catalog.md");
const ACCEPT_ID_CHANGE = process.argv.includes("--accept-id-change");

function extractExistingIds() {
  if (!existsSync(TARGET)) return [];
  const parsed = parseFrontmatter(readText(TARGET), TARGET);
  return Array.isArray(parsed.metadata.catalog_ids) ? parsed.metadata.catalog_ids : [];
}

function renderGeneratedCatalog(sourceContent, ids) {
  const sourceDigest = sha256Short(sourceContent);
  const families = [...new Set(ids.map((id) => id[0]))];
  return `---
generated_from: findings/01_bug_catalog.md
source_digest: ${sourceDigest}
pattern_count: ${ids.length}
families:
${yamlList(families, "  ")}
catalog_ids:
${yamlList(ids, "  ")}
---

<!-- AUTO-GENERATED from findings/01_bug_catalog.md - do not edit directly -->
<!-- Regenerate: node scripts/sync-catalog.ts -->

${sourceContent.trim()}
`;
}

function main() {
  const sourceContent = readText(SOURCE);
  const ids = extractCatalogIds(sourceContent);
  const families = [...new Set(ids.map((id) => id[0]))];
  const missingFamilies = EXPECTED_FAMILIES.filter((family) => !families.includes(family));

  if (missingFamilies.length > 0) {
    throw new Error(`catalog missing families: ${missingFamilies.join(", ")}`);
  }

  const existingIds = extractExistingIds();
  if (existingIds.length > 0 && existingIds.join("\n") !== ids.join("\n") && !ACCEPT_ID_CHANGE) {
    throw new Error(
      "catalog IDs changed. Re-run with --accept-id-change only after review approval."
    );
  }

  atomicWrite(TARGET, renderGeneratedCatalog(sourceContent, ids));
  console.log(`Catalog sync OK - ${ids.length} IDs, ${families.length} families.`);
}

main();
