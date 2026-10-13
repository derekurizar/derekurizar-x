#!/usr/bin/env node
/*
 * Hilos · Render de un informe (investigacion/) → PDF Letter con Playwright
 * ==========================================================================
 * Uso:
 *   node scripts/render_informe.js <informe.html> [--pdf salida.pdf] [--png DIR] [--check] [--dsf N]
 *
 * Mismas garantías que render.js: cero peticiones externas (las fuentes salen de design/fonts/ por
 * scripts/fuentes_ruta.js), un error de JavaScript es fatal, se espera body[data-listo] y se comprueba
 * que las tres familias estén cargadas. El PDF respeta el tamaño de cada hoja (@page carta / apaisada).
 * --png escribe pagina_NN.png (una por hoja, para el QA visual).
 *
 * --check (sobre la página maquetada, antes del PDF):
 *   P1 texto por debajo del piso del documento (tokens.documento.pisoPx, 12 px)
 *   P2 contenido que se sale de su hoja (.pagina)
 *   P3 figura o tabla sin «Fuente:» en su pie
 *   P4 dependencia externa (siempre: también sin --check)
 *   P5 dos bloques de texto solapados (>25 % del menor) en la misma hoja
 */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");
const { rutaFuentes } = require("./fuentes_ruta");

const RAIZ = path.dirname(__dirname);
const TOKENS = JSON.parse(fs.readFileSync(path.join(RAIZ, "design", "tokens.json"), "utf8"));
const DOC = TOKENS.documento || { pisoPx: 12 };
const FAMILIAS = ["400 72px 'Instrument Serif'", "500 12px 'JetBrains Mono'", "400 16px Archivo"];

function parseArgs(argv) {
  const o = { pdf: null, png: null, check: false, dsf: 2, input: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--pdf") o.pdf = argv[++i];
    else if (a === "--png") o.png = argv[++i];
    else if (a === "--check") o.check = true;
    else if (a === "--dsf") o.dsf = parseFloat(argv[++i]);
    else if (!o.input) o.input = a;
    else { console.error("ERROR: un solo informe por llamada"); process.exit(2); }
  }
  return o;
}

/* Corre DENTRO de la página. Devuelve fallos (vacío = OK). */
function comprobaciones({ minPx }) {
  const fallos = [];
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const corto = (s) => s.replace(/\s+/g, " ").trim().slice(0, 40);
  document.querySelectorAll(".pagina").forEach((pag, ip) => {
    const n = ip + 1, rp = pag.getBoundingClientRect();
    const conTexto = [];
    for (const el of pag.querySelectorAll("*")) {
      const propio = Array.from(el.childNodes).filter((x) => x.nodeType === 3).map((x) => x.textContent).join("").trim();
      if (propio && visible(el)) conTexto.push({ el, texto: propio });
    }
    // P1
    for (const { el, texto } of conTexto) {
      const fsCss = parseFloat(getComputedStyle(el).fontSize);
      let escala = 1;
      const svg = el.ownerSVGElement;
      if (svg && svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.height > 0) escala = svg.getBoundingClientRect().height / svg.viewBox.baseVal.height;
      const real = fsCss * escala;
      if (real < minPx - 0.01) fallos.push(`P1 pág. ${n}: texto a ${real.toFixed(1)}px (< ${minPx}) — "${corto(texto)}"`);
    }
    // P2
    if (pag.scrollHeight > pag.clientHeight + 1 || pag.scrollWidth > pag.clientWidth + 1)
      fallos.push(`P2 pág. ${n}: el contenido mide ${pag.scrollWidth}×${pag.scrollHeight} y la hoja ${pag.clientWidth}×${pag.clientHeight}`);
    for (const el of pag.querySelectorAll("*")) {
      if (!visible(el)) continue;
      const tieneTexto = Array.from(el.childNodes).some((x) => x.nodeType === 3 && x.textContent.trim());
      if (!tieneTexto && el.children.length && el.tagName.toLowerCase() !== "img") continue;
      const r = el.getBoundingClientRect();
      if (r.bottom > rp.bottom + 0.5 || r.right > rp.right + 0.5 || r.top < rp.top - 0.5 || r.left < rp.left - 0.5) {
        fallos.push(`P2 pág. ${n}: <${el.tagName.toLowerCase()}> fuera de la hoja${tieneTexto ? ` "${corto(el.textContent)}"` : ""}`);
        break;
      }
    }
    // P3
    pag.querySelectorAll("figure.fig").forEach((f, k) => {
      if (!/Fuente:\s*\S/.test(f.textContent)) fallos.push(`P3 pág. ${n}: la figura ${k + 1} no lleva «Fuente: …»`);
    });
    // P5
    for (let i = 0; i < conTexto.length; i++) for (let j = i + 1; j < conTexto.length; j++) {
      const a = conTexto[i], b = conTexto[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const ra = a.el.getBoundingClientRect(), rb = b.el.getBoundingClientRect();
      const sx = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      const sy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (sx <= 1 || sy <= 1) continue;
      const area = sx * sy, menor = Math.min(ra.width * ra.height, rb.width * rb.height);
      if (menor > 0 && area / menor > 0.25) fallos.push(`P5 pág. ${n}: texto solapado ${((area / menor) * 100).toFixed(0)}% — "${corto(a.texto).slice(0, 28)}" ↔ "${corto(b.texto).slice(0, 28)}"`);
    }
  });
  return fallos;
}

async function main() {
  const o = parseArgs(process.argv.slice(2));
  if (!o.input) {
    console.error("Uso: node scripts/render_informe.js <informe.html> [--pdf salida.pdf] [--png DIR] [--check] [--dsf N]");
    process.exit(2);
  }
  const abs = path.resolve(o.input);
  if (!fs.existsSync(abs)) { console.error(`ERROR: no existe ${o.input}`); process.exit(2); }
  let huboFallos = false;
  const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
  try {
    const page = await browser.newPage({ viewport: { width: 1100, height: 1100 }, deviceScaleFactor: o.dsf });
    const errores = [];
    page.on("pageerror", (e) => errores.push(e.message));
    page.on("console", (m) => { if (m.type() === "error") errores.push("console.error: " + m.text()); });
    const { externas, fuentesFaltantes } = await rutaFuentes(page);
    await page.emulateMedia({ media: "print" });
    await page.goto("file://" + abs, { waitUntil: "load", timeout: 20000 });
    let listo = true;
    try { await page.waitForSelector("body[data-listo]", { timeout: 15000, state: "attached" }); } catch { listo = false; }
    const errorDATA = await page.evaluate(() => document.body.dataset.error || null);
    const fuentesOk = await page.evaluate((fams) => fams.map((f) => [f, document.fonts.check(f)]), FAMILIAS);
    if (fuentesFaltantes.length) { huboFallos = true; console.error(`ERROR fuentes ausentes en design/fonts/: ${[...new Set(fuentesFaltantes)].join(", ")}`); }
    for (const [f, ok] of fuentesOk) if (!ok) { huboFallos = true; console.error(`ERROR tipografía no cargada: ${f}`); }
    if (errorDATA) { huboFallos = true; console.error(`ERROR al construir el informe: ${errorDATA}`); }
    else if (!listo) { huboFallos = true; console.error("ERROR el informe nunca marcó body[data-listo]"); }
    if (errores.length) { huboFallos = true; console.error("ERROR de JavaScript:"); for (const e of [...new Set(errores)]) console.error("  " + e); }

    const nPaginas = await page.evaluate(() => document.querySelectorAll(".pagina").length);
    if (o.check && listo && !errorDATA) {
      const fallos = await page.evaluate(comprobaciones, { minPx: DOC.pisoPx || 12 });
      if (fallos.length) { huboFallos = true; console.error(`FALLO --check: ${o.input}`); for (const f of fallos) console.error("  " + f); }
    }
    if (o.png && listo) {
      fs.mkdirSync(o.png, { recursive: true });
      const hojas = await page.$$(".pagina");
      for (let i = 0; i < hojas.length; i++) await hojas[i].screenshot({ path: path.join(o.png, `pagina_${String(i + 1).padStart(2, "0")}.png`) });
    }
    if (o.pdf && listo) await page.pdf({ path: o.pdf, preferCSSPageSize: true, printBackground: true });
    await page.close();

    if (externas.length) {
      huboFallos = true;
      console.error("FALLO P4 dependencia externa (PROHIBIDO):");
      for (const u of [...new Set(externas)]) console.error("  " + u);
    }
    if (!huboFallos) console.log(`OK -> ${o.pdf ? path.relative(process.cwd(), o.pdf) : o.input} · ${nPaginas} páginas${o.check ? " · P1–P5" : ""}`);
  } finally {
    await browser.close();
  }
  if (huboFallos) process.exit(1);
}

main().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
