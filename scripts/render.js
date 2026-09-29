#!/usr/bin/env node
/*
 * Hilos · Render HTML → PNG con Playwright (tarjetas 1080×1080 @2x)
 * ==================================================================
 * Uso:
 *   node scripts/render.js <ruta.html> [más.html ...] [--out salida.png] [--check] [--dsf N]
 *
 * Sin --out cada PNG se guarda junto a su HTML con el mismo nombre.
 *
 * Garantías (heredadas de guate-en-un-dato, ampliadas):
 *   - CERO dependencias externas: cualquier petición que no sea file:/data:/blob:
 *     se aborta y el proceso sale 1. Excepción: `**\/fonts/*.woff2` se sirve
 *     desde design/fonts/ con cabeceras CORS (Chromium aplica CORS a las fuentes
 *     de file://). Así los visuales cargan tipografía desde cualquier carpeta.
 *   - Un error de JavaScript es fatal (un PNG a medio construir pasaría el QA).
 *   - Se espera a body[data-listo] (lo pone la base al terminar render()) y se
 *     comprueba que las 3 familias tipográficas estén realmente cargadas.
 *
 * --check (sobre la página maquetada, antes del screenshot):
 *   R1 texto por debajo del piso tipográfico (17 px; incluye escala del viewBox)
 *   R2 elemento visible fuera del lienzo
 *   R3 dos bloques de texto solapados (>25 % del menor)
 *   R4 <svg> a 300×150 (tamaño por defecto) o más de un <svg>
 *   R5 el pie no contiene «Fuente:»
 *   R6 #grafico sin hijos visibles o con menos de 200 px de alto
 */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const RAIZ = path.dirname(__dirname);
const TOKENS = JSON.parse(fs.readFileSync(path.join(RAIZ, "design", "tokens.json"), "utf8"));
const FONTS_DIR = path.join(RAIZ, "design", "fonts");
const PROTOCOLOS_LOCALES = /^(file|data|blob|about):/;
const RE_FUENTE = /\/fonts\/([^/?#]+\.woff2)(\?.*)?$/;
const FAMILIAS = ["400 88px 'Instrument Serif'", "500 20px 'JetBrains Mono'", "600 24px Archivo"];

function parseArgs(argv) {
  const o = { out: null, check: false, dsf: TOKENS.canvas.dsf || 2, inputs: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") o.out = argv[++i];
    else if (a === "--check") o.check = true;
    else if (a === "--dsf") o.dsf = parseFloat(argv[++i]);
    else o.inputs.push(a);
  }
  return o;
}

/* Corre DENTRO de la página (sin Node). Devuelve fallos (vacío = OK). */
function comprobaciones({ width, height, minPx }) {
  const fallos = [];
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const conTexto = [];
  for (const el of document.body.querySelectorAll("*")) {
    const propio = Array.from(el.childNodes).filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join("");
    if (propio && visible(el)) conTexto.push({ el, texto: propio });
  }
  // R1
  for (const { el, texto } of conTexto) {
    const fsCss = parseFloat(getComputedStyle(el).fontSize);
    let escala = 1;
    const svg = el.ownerSVGElement;
    if (svg && svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.height > 0) escala = svg.getBoundingClientRect().height / svg.viewBox.baseVal.height;
    const real = fsCss * escala;
    if (real < minPx - 0.01) fallos.push(`R1 texto a ${real.toFixed(1)}px (< ${minPx}) — <${el.tagName.toLowerCase()}> "${texto.slice(0, 40)}"`);
  }
  // R2
  for (const el of document.body.querySelectorAll("*")) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    const tieneTexto = Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!tieneTexto && el.children.length) continue;
    if (r.bottom > height + 0.5 || r.right > width + 0.5 || r.top < -0.5 || r.left < -0.5)
      fallos.push(`R2 fuera del lienzo ${width}x${height} — <${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}> x[${r.left.toFixed(0)},${r.right.toFixed(0)}] y[${r.top.toFixed(0)},${r.bottom.toFixed(0)}]${el.textContent.trim() ? ` "${el.textContent.trim().slice(0, 40)}"` : ""}`);
  }
  // R3
  for (let i = 0; i < conTexto.length; i++) for (let j = i + 1; j < conTexto.length; j++) {
    const a = conTexto[i], b = conTexto[j];
    if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
    const ra = a.el.getBoundingClientRect(), rb = b.el.getBoundingClientRect();
    const sx = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
    const sy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
    if (sx <= 1 || sy <= 1) continue;
    const area = sx * sy, menor = Math.min(ra.width * ra.height, rb.width * rb.height);
    if (menor > 0 && area / menor > 0.25) fallos.push(`R3 texto solapado ${((area / menor) * 100).toFixed(0)}% — "${a.texto.slice(0, 28)}" ↔ "${b.texto.slice(0, 28)}"`);
  }
  // R4
  const svgs = document.querySelectorAll("svg");
  if (svgs.length > 1) fallos.push(`R4 hay ${svgs.length} <svg>; la tarjeta admite uno solo`);
  for (const svg of svgs) {
    const r = svg.getBoundingClientRect();
    if (Math.round(r.width) === 300 && Math.round(r.height) === 150) fallos.push("R4 <svg> a 300x150 (tamaño por defecto)");
  }
  // R5
  const pie = document.querySelector(".pie");
  if (!pie || !/Fuente:\s*\S/.test(pie.textContent)) fallos.push("R5 el pie no lleva «Fuente: …»");
  // R6
  const g = document.getElementById("grafico");
  if (!g) fallos.push("R6 no existe #grafico");
  else {
    const r = g.getBoundingClientRect();
    const hijos = Array.from(g.querySelectorAll("*")).filter(visible).length;
    if (r.height < 200) fallos.push(`R6 #grafico mide ${r.height.toFixed(0)}px de alto (< 200)`);
    if (!hijos) fallos.push("R6 #grafico no tiene hijos visibles");
  }
  return fallos;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.inputs.length) {
    console.error("Uso: node scripts/render.js <ruta.html> [más.html ...] [--out salida.png] [--check] [--dsf N]");
    process.exit(2);
  }
  if (opts.out && opts.inputs.length > 1) { console.error("ERROR: --out solo vale con un único HTML."); process.exit(2); }

  const width = TOKENS.canvas.w, height = TOKENS.canvas.h, minPx = TOKENS.canvas.pisoPx || 17;
  let huboFallos = false;
  const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
  try {
    for (const input of opts.inputs) {
      const abs = path.resolve(input);
      const out = opts.out ? path.resolve(opts.out) : abs.replace(/\.html?$/i, ".png");
      if (!fs.existsSync(abs)) { console.error(`ERROR: no existe ${input}`); huboFallos = true; continue; }
      const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: opts.dsf });
      const errores = [], externas = [], fuentesFaltantes = [];
      page.on("pageerror", (e) => errores.push(e.message));
      page.on("console", (m) => { if (m.type() === "error") errores.push("console.error: " + m.text()); });

      await page.route("**", (route) => {
        const url = route.request().url();
        const mf = url.match(RE_FUENTE);
        if (mf) {
          const archivo = path.join(FONTS_DIR, mf[1]);
          if (!fs.existsSync(archivo)) { fuentesFaltantes.push(mf[1]); return route.abort(); }
          return route.fulfill({ status: 200, contentType: "font/woff2", body: fs.readFileSync(archivo), headers: { "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store" } });
        }
        if (PROTOCOLOS_LOCALES.test(url)) return route.continue();
        externas.push(url);
        return route.abort();
      });

      await page.goto("file://" + abs, { waitUntil: "load", timeout: 15000 });
      let listo = true;
      try { await page.waitForSelector("body[data-listo]", { timeout: 8000, state: "attached" }); }
      catch { listo = false; }
      const errorDATA = await page.evaluate(() => document.body.dataset.error || null);
      const fuentesOk = await page.evaluate((fams) => fams.map((f) => [f, document.fonts.check(f)]), FAMILIAS);

      if (fuentesFaltantes.length) { huboFallos = true; console.error(`ERROR fuentes ausentes en design/fonts/: ${[...new Set(fuentesFaltantes)].join(", ")}`); }
      for (const [f, ok] of fuentesOk) if (!ok) { huboFallos = true; console.error(`ERROR tipografía no cargada: ${f}`); }
      if (errorDATA) { huboFallos = true; console.error(`ERROR en render() de ${input}: ${errorDATA}`); }
      else if (!listo) { huboFallos = true; console.error(`ERROR ${input} nunca marcó body[data-listo] (¿falta DATA/render() o quedó colgado?)`); }
      if (errores.length) { huboFallos = true; console.error(`ERROR de JavaScript en ${input}:`); for (const e of [...new Set(errores)]) console.error("  " + e); }

      if (opts.check) {
        const fallos = await page.evaluate(comprobaciones, { width, height, minPx });
        if (fallos.length) { huboFallos = true; console.error(`FALLO --check: ${input}`); for (const f of fallos) console.error("  " + f); }
      }

      await page.screenshot({ path: out, clip: { x: 0, y: 0, width, height } });
      await page.close();

      if (externas.length) {
        huboFallos = true;
        console.error(`ERROR dependencia externa (PROHIBIDO) en ${input}:`);
        for (const u of [...new Set(externas)]) console.error("  " + u);
      } else if (!errores.length && !errorDATA && listo) console.log("OK ->", path.relative(process.cwd(), out));
      else console.log("PNG (con fallos) ->", path.relative(process.cwd(), out));
    }
  } finally {
    await browser.close();
  }
  if (huboFallos) process.exit(1);
}

main().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
