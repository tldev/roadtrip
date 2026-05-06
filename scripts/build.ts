// Frontend asset build: copy public files into dist/ with content-hash
// filenames, copy HTML/favicon as-is, write a logical→hashed manifest
// the server reads at boot to inject the correct URLs into HTML.

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync, cpSync, rmSync } from "node:fs";
import { dirname } from "node:path";

const HASHED = [
  "app.js",
  "app.css",
  "admin/admin.js",
  "admin/admin.css",
] as const;

const PASSTHROUGH = [
  "index.html",
  "admin/index.html",
  "favicon.svg",
] as const;

const SRC = "src/public";
const OUT = "dist/public";

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });

const manifest: Record<string, string> = {};

for (const logical of HASHED) {
  const buf = readFileSync(`${SRC}/${logical}`);
  const hash = createHash("sha256").update(buf).digest("hex").slice(0, 8);
  const dot = logical.lastIndexOf(".");
  const stem = logical.slice(0, dot);
  const ext = logical.slice(dot);
  const hashed = `${stem}.${hash}${ext}`;
  const outPath = `${OUT}/${hashed}`;
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, buf);
  manifest[logical] = `/${hashed}`;
}

for (const file of PASSTHROUGH) {
  const dst = `${OUT}/${file}`;
  mkdirSync(dirname(dst), { recursive: true });
  cpSync(`${SRC}/${file}`, dst);
}

writeFileSync(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 2) + "\n");

console.log("[build] dist/public:");
for (const [k, v] of Object.entries(manifest)) console.log(`  ${k.padEnd(20)} -> ${v}`);
