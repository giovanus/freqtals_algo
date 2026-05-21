#!/usr/bin/env node
import { parse } from "@babel/parser";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";

const [inputPath, outputPath] = process.argv.slice(2);

if (!inputPath || !outputPath) {
  console.error("Usage: npm run convert -- <input-file-or-dir> <output-dir>");
  process.exit(1);
}

const NODE_EXTENSIONS = new Set([".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"]);
const SKIPPED_KEYS = new Set([
  "type",
  "start",
  "end",
  "loc",
  "range",
  "extra",
  "comments",
  "errors",
  "leadingComments",
  "innerComments",
  "trailingComments"
]);

await mkdir(outputPath, { recursive: true });

const files = await collectSourceFiles(inputPath);
for (const file of files) {
  const source = await readFile(file, "utf8");
  const ast = parse(source, {
    sourceType: "unambiguous",
    errorRecovery: true,
    plugins: [
      "jsx",
      "typescript",
      "classProperties",
      "classPrivateProperties",
      "classPrivateMethods",
      "decorators-legacy",
      "dynamicImport",
      "importMeta",
      "objectRestSpread",
      "optionalChaining",
      "nullishCoalescingOperator",
      "topLevelAwait"
    ]
  });

  const document = ast.program;
  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<SourceFile FullName="${escapeXml(file)}" Language="JavaScript" LineNr="1">`,
    renderNode(document, 1),
    "</SourceFile>",
    ""
  ].join("\n");

  const relative = path.relative(inputPath, file);
  const outputName = relative.replace(/\.[^.]+$/, ".xml").replace(/[\\/]/g, "__");
  await writeFile(path.join(outputPath, outputName), xml, "utf8");
  console.log(`Wrote ${path.join(outputPath, outputName)}`);
}

async function collectSourceFiles(entryPath) {
  const stat = await import("node:fs/promises").then((fs) => fs.stat(entryPath));
  if (stat.isFile()) {
    return NODE_EXTENSIONS.has(path.extname(entryPath)) ? [entryPath] : [];
  }

  const entries = await readdir(entryPath, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const fullPath = path.join(entryPath, entry.name);
    if (entry.isDirectory()) return collectSourceFiles(fullPath);
    if (entry.isFile() && NODE_EXTENSIONS.has(path.extname(entry.name))) return [fullPath];
    return [];
  }));

  return nested.flat().sort();
}

function renderNode(node, depth) {
  const tag = sanitizeTag(node.type);
  const line = node.loc?.start?.line ?? 0;
  const children = [];

  for (const [key, value] of Object.entries(node)) {
    if (SKIPPED_KEYS.has(key) || value == null) continue;
    const rendered = renderField(key, value, depth + 1);
    if (rendered) children.push(rendered);
  }

  const indent = "  ".repeat(depth);
  if (children.length === 0) return `${indent}<${tag} LineNr="${line}"/>`;
  return [
    `${indent}<${tag} LineNr="${line}">`,
    ...children,
    `${indent}</${tag}>`
  ].join("\n");
}

function renderField(key, value, depth) {
  const tag = sanitizeTag(key);
  const indent = "  ".repeat(depth);

  if (Array.isArray(value)) {
    const children = value
      .filter(Boolean)
      .map((item) => renderValue(item, depth + 1))
      .filter(Boolean);
    if (children.length === 0) return "";
    return [`${indent}<${tag} LineNr="${fieldLine(value)}">`, ...children, `${indent}</${tag}>`].join("\n");
  }

  if (isAstNode(value)) {
    return [`${indent}<${tag} LineNr="${value.loc?.start?.line ?? 0}">`, renderNode(value, depth + 1), `${indent}</${tag}>`].join("\n");
  }

  if (typeof value === "object") {
    const children = Object.entries(value)
      .filter(([childKey, childValue]) => !SKIPPED_KEYS.has(childKey) && childValue != null)
      .map(([childKey, childValue]) => renderField(childKey, childValue, depth + 1))
      .filter(Boolean);
    if (children.length === 0) return "";
    return [`${indent}<${tag} LineNr="0">`, ...children, `${indent}</${tag}>`].join("\n");
  }

  return `${indent}<${tag} LineNr="0">${escapeXml(String(value))}</${tag}>`;
}

function renderValue(value, depth) {
  if (isAstNode(value)) return renderNode(value, depth);
  if (value == null || typeof value === "object") return "";
  const indent = "  ".repeat(depth);
  return `${indent}<value LineNr="0">${escapeXml(String(value))}</value>`;
}

function isAstNode(value) {
  return value && typeof value === "object" && typeof value.type === "string";
}

function fieldLine(values) {
  const firstNode = values.find(isAstNode);
  return firstNode?.loc?.start?.line ?? 0;
}

function sanitizeTag(value) {
  return value.replace(/[^A-Za-z0-9_.-]/g, "_").replace(/^[^A-Za-z_]/, "_$&");
}

function escapeXml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}
