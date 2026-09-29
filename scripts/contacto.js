#!/usr/bin/env node
/*
 * Hilos · Hoja de contacto: todos los tuit_N.png de una carpeta en una rejilla.
 * ==========================================================================
 * Uso:
 *   node scripts/contacto.js <carpeta> [--out contacto.png] [--celda 540]
 *
 * Toma los tuit_N.png (orden numérico), arma una rejilla (2 columnas si ≤ 4
 * tarjetas, 3 si más) con el número del tuit en una esquina, fondo #F6F2E8, y
 * hace un screenshot a <carpeta>/contacto.png (deviceScaleFactor 1). Sin
 * peticiones externas: solo file:// (cualquier otra se aborta y el proceso sale 1).
 * Salida: 0 ok · 1 error · 2 uso incorrecto
 */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const PROTOCOLOS_LOCALES = /^(file|data|blob|about):/;

function parseArgs(argv) {
  const o = { carpeta: null, out: null, celda: 540 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") o.out = argv[++i];
    else if (a === "--celda") o.celda = parseInt(argv[++i], 10);
    else if (!o.carpeta) o.carpeta = a;
    else { console.error(`ERROR: argumento inesperado ${a}`); process.exit(2); }
  }
  return o;
}

function tarjetas(carpeta) {
  return fs.readdirSync(carpeta)
    .map((f) => { const m = f.match(/^tuit_(\d+)\.png$/); return m ? { n: parseInt(m[1], 10), f } : null; })
    .filter(Boolean)
    .sort((a, b) => a.n - b.n);
}

function html(items, carpeta, celda) {
  const cols = items.length <= 4 ? 2 : 3;
  const gap = Math.round(celda * 0.06);
  const marg = Math.round(celda * 0.08);
  const filas = Math.ceil(items.length / cols);
  const w = marg * 2 + cols * celda + (cols - 1) * gap;
  const h = marg * 2 + filas * celda + (filas - 1) * gap;
  const celdas = items.map((it) => {
    const src = "file://" + path.join(carpeta, it.f);
    return `<div class="c"><img src="${src}" alt="tuit ${it.n}"><span class="n">${it.n}</span></div>`;
  }).join("");
  return `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Hoja de contacto</title>
<style>
  html, body { margin: 0; background: #F6F2E8; }
  body { width: ${w}px; height: ${h}px; overflow: hidden; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .g { display: grid; grid-template-columns: repeat(${cols}, ${celda}px); gap: ${gap}px; padding: ${marg}px; }
  .c { position: relative; width: ${celda}px; height: ${celda}px; }
  .g { overflow: visible; }
  .c img { width: ${celda}px; height: ${celda}px; display: block; border-radius: 6px; box-shadow: 0 2px 10px rgba(12,21,32,.14); }
  .n { position: absolute; top: -14px; left: -14px; min-width: 44px; height: 44px; padding: 0 12px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; border-radius: 22px; background: #0C1520; color: #F6F2E8; font-size: 28px; font-weight: 700; line-height: 1; }
</style></head><body><div class="g">${celdas}</div></body></html>`;
}

async function main() {
  const o = parseArgs(process.argv.slice(2));
  if (!o.carpeta || !Number.isFinite(o.celda) || o.celda < 100) {
    console.error("Uso: node scripts/contacto.js <carpeta> [--out contacto.png] [--celda 540]");
    process.exit(2);
  }
  const carpeta = path.resolve(o.carpeta);
  if (!fs.existsSync(carpeta) || !fs.statSync(carpeta).isDirectory()) { console.error(`ERROR: no existe la carpeta ${o.carpeta}`); process.exit(1); }
  const items = tarjetas(carpeta);
  if (!items.length) { console.error(`ERROR: no hay tuit_N.png en ${o.carpeta}`); process.exit(1); }
  const out = path.resolve(o.out || path.join(carpeta, "contacto.png"));
  const tmp = path.join(carpeta, ".contacto.html");
  fs.writeFileSync(tmp, html(items, carpeta, o.celda));

  const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
  const externas = [];
  try {
    const page = await browser.newPage({ viewport: { width: 800, height: 600 }, deviceScaleFactor: 1 });
    await page.route("**", (route) => {
      const url = route.request().url();
      if (PROTOCOLOS_LOCALES.test(url)) return route.continue();
      externas.push(url);
      return route.abort();
    });
    await page.goto("file://" + tmp, { waitUntil: "load", timeout: 15000 });
    const rotas = await page.evaluate(() => Array.from(document.images).filter((i) => !i.complete || !i.naturalWidth).map((i) => i.alt));
    if (rotas.length) { console.error(`ERROR: imágenes que no cargaron: ${rotas.join(", ")}`); process.exitCode = 1; }
    await page.screenshot({ path: out, fullPage: true });
    await page.close();
  } finally {
    await browser.close();
    try { fs.unlinkSync(tmp); } catch (e) { /* nada */ }
  }
  if (externas.length) {
    console.error("ERROR dependencia externa (PROHIBIDO):");
    for (const u of [...new Set(externas)]) console.error("  " + u);
    process.exit(1);
  }
  if (process.exitCode) process.exit(process.exitCode);
  console.log(`OK -> ${path.relative(process.cwd(), out)} (${items.length} tarjetas, ${items.length <= 4 ? 2 : 3} columnas)`);
}

main().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
