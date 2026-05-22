#!/usr/bin/env node
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = process.env.SKILL_PROJECT_ROOT
  ? resolve(process.env.SKILL_PROJECT_ROOT)
  : resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const SKILL_DIR = join(ROOT, "skill");
// Must be kept in sync with findings/01_bug_catalog.md families.
// When adding a new family, update this list and add the corresponding check file.
export const EXPECTED_FAMILIES = "ABCDEFGHIJKLMNOPQR".split("");

export function readText(path) {
  return readFileSync(path, "utf8");
}

export function sha256Short(content) {
  return createHash("sha256").update(content).digest("hex").slice(0, 12);
}

export function atomicWrite(path, content) {
  const tmp = `${path}.tmp.${process.pid}`;
  writeFileSync(tmp, content, "utf8");
  renameSync(tmp, path);
}

export function listMarkdownFiles(dir) {
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".md") && !entry.name.startsWith("."))
    .map((entry) => join(dir, entry.name))
    .sort();
}

export function relativePath(path) {
  return relative(ROOT, path).replaceAll("\\", "/");
}

export function parseFrontmatterFile(path) {
  return parseFrontmatter(readText(path), path);
}

export function parseFrontmatter(text, pathForError = "<memory>") {
  if (!text.startsWith("---\n")) {
    throw new Error(`${pathForError}: missing frontmatter`);
  }
  const end = text.indexOf("\n---", 4);
  if (end === -1) {
    throw new Error(`${pathForError}: unterminated frontmatter`);
  }
  const raw = text.slice(4, end);
  const body = text.slice(text.indexOf("\n", end + 4) + 1);
  return {
    metadata: parseSimpleYaml(raw),
    rawFrontmatter: raw,
    body,
  };
}

export function stripFrontmatter(text) {
  if (!text.startsWith("---\n")) return text.trim();
  const end = text.indexOf("\n---", 4);
  if (end === -1) return text.trim();
  return text.slice(text.indexOf("\n", end + 4) + 1).trim();
}

export function parseSimpleYaml(raw) {
  const result = {};
  let currentKey = null;

  for (const line of raw.split(/\r?\n/)) {
    if (!line.trim()) continue;

    const keyMatch = line.match(/^([A-Za-z0-9_-]+):(?:\s*(.*))?$/);
    if (keyMatch) {
      const [, key, restRaw = ""] = keyMatch;
      const rest = restRaw.trim();
      currentKey = key;
      if (!rest) {
        result[key] = [];
      } else if (rest.startsWith("[") && rest.endsWith("]")) {
        result[key] = parseInlineList(rest);
        currentKey = null;
      } else {
        result[key] = stripQuotes(rest);
        currentKey = null;
      }
      continue;
    }

    const listMatch = line.match(/^\s*-\s*(.+)$/);
    if (listMatch && currentKey) {
      if (!Array.isArray(result[currentKey])) {
        result[currentKey] = [];
      }
      result[currentKey].push(stripQuotes(listMatch[1].trim()));
    }
  }

  return result;
}

export function parseInlineList(value) {
  const inner = value.slice(1, -1).trim();
  if (!inner) return [];
  return inner.split(",").map((item) => stripQuotes(item.trim())).filter(Boolean);
}

export function stripQuotes(value) {
  if (
    (value.startsWith("'") && value.endsWith("'")) ||
    (value.startsWith('"') && value.endsWith('"'))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

export function yamlList(items, indent = "") {
  return items.map((item) => `${indent}- ${item}`).join("\n");
}

export function extractCatalogIds(content) {
  const ids = new Set();
  for (const match of content.matchAll(/^### ([A-R]\d+)\./gm)) {
    ids.add(match[1]);
  }
  for (const match of content.matchAll(/^\| (L\d+) \|/gm)) {
    ids.add(match[1]);
  }
  return [...ids].sort((left, right) => {
    const familyCompare = left[0].localeCompare(right[0]);
    if (familyCompare !== 0) return familyCompare;
    return Number(left.slice(1)) - Number(right.slice(1));
  });
}

export function firstParagraphAfterHeading(body, heading) {
  const marker = `## ${heading}`;
  const start = body.indexOf(marker);
  if (start === -1) return "";
  const after = body.slice(start + marker.length).split(/\r?\n/);
  const lines = [];
  for (const line of after) {
    if (line.startsWith("## ")) break;
    if (!line.trim() && lines.length === 0) continue;
    if (!line.trim() && lines.length > 0) break;
    lines.push(line.trim());
  }
  return lines.join(" ");
}
