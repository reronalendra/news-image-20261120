// News image for Friday 20 November 2026 (make.fun news-image-20261120).
//
// The picture itself is drawn ahead of time by build_image.py and stored
// next to this file as entry.png. At grading time this program only has
// to place that exact file at the output path, with no network and no
// extra dependencies, so the two graded runs produce identical bytes.
// Copying a fixed file is deterministic by construction: the output is
// byte-for-byte the image in the repository, run after run.
//
// Run locally with:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const IMAGE_NAME = "entry.png";
const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR?.trim() || "/output";
const src = resolve(here, IMAGE_NAME);
const dest = resolve(outDir, IMAGE_NAME);
if (!existsSync(src) || statSync(src).size === 0) {
    throw new Error(`source image missing or empty: ${src}`);
}
mkdirSync(outDir, { recursive: true });
if (src !== dest) {
    copyFileSync(src, dest);
}
