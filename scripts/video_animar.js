#!/usr/bin/env node
/*
 * Video · gate V7: la animación termina exactamente en la tarjeta
 * ===============================================================
 * Uso:
 *   node scripts/video_animar.js --check <tarjeta.html> [más.html ...] [--medio DIR] [--cuadrada]
 *
 * Por cada tarjeta ensamblada (tuit_N.html o una de la galería):
 *   A  render del HTML original (1080×1080 @1x)
 *   B  copia con video/animar.js inyectado antes de </body>, llevada al final con __seek(999, T)
 * y compara A con B píxel a píxel (canvas en la página, sin dependencias nuevas). Pasa si difieren
 * ≤ 0.1 % de los píxeles (antialiasing). Por defecto los dos renders llevan video/vertical.css (el modo
 * vertical que usa el video, inyectado cuando la tarjeta ya se dibujó, igual que escena.html); con --cuadrada
 * se comparan las tarjetas tal cual. Con --medio DIR guarda además un cuadro intermedio (__seek(0.9, T))
 * como DIR/<nombre>.medio.png para revisar a ojo que anime con sentido.
 *
 * Salida: 0 todas pasan · 1 alguna falla (o error de JavaScript) · 2 uso incorrecto.
 */
const path = require("path");
const fs = require("fs");
const os = require("os");
const { chromium } = require("playwright");
const { rutaFuentes } = require("./fuentes_ruta");

const RAIZ = path.dirname(__dirname);
const ANIMAR = fs.readFileSync(path.join(RAIZ, "video", "animar.js"), "utf8");
const VERTICAL = fs.readFileSync(path.join(RAIZ, "video", "vertical.css"), "utf8");
const T = { tit: 0, ini: 0.5, nota: 1, valores: {}, linea_fin: 2 };
const TOLERANCIA = 0.001;
const AYUDA = fs.readFileSync(__filename, "utf8").split("*/")[0].replace(/^#!.*\n\/\*\n?/, "").replace(/^ \* ?/gm, "");

function parseArgs(argv) {
  const o = { check: false, medio: null, cuadrada: false, inputs: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--check") o.check = true;
    else if (a === "--cuadrada") o.cuadrada = true;
    else if (a === "--medio") o.medio = argv[++i];
    else if (a === "--help" || a === "-h") { console.log(AYUDA); process.exit(0); }
    else if (a.startsWith("--")) { console.error("Opción desconocida: " + a); process.exit(2); }
    else o.inputs.push(a);
  }
  if (!o.check || !o.inputs.length || (o.medio === undefined)) { console.error("Uso: node scripts/video_animar.js --check <tarjeta.html>... [--medio DIR]"); process.exit(2); }
  return o;
}

// Abre un HTML, espera a que la tarjeta termine (data-listo + fuentes) y devuelve la página; con `vertical`
// inyecta después video/vertical.css (como hace escena.html en el iframe): la tarjeta ya midió su espacio
async function abrir(browser, archivo, errores, vertical) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => errores.push(e.message));
  await rutaFuentes(page);
  await page.goto("file://" + archivo, { waitUntil: "load", timeout: 15000 });
  await page.waitForSelector("body[data-listo]", { timeout: 8000, state: "attached" });
  await page.evaluate(() => document.fonts.ready);
  if (vertical) await page.addStyleTag({ content: VERTICAL });
  return page;
}

const foto = (page) => page.screenshot({ clip: { x: 0, y: 0, width: 1080, height: 1080 } });

// Diferencia entre dos PNG: píxeles distintos y delta máximo por canal (en una página aparte)
async function comparar(browser, a, b) {
  const page = await browser.newPage();
  const r = await page.evaluate(async ([ua, ub]) => {
    const cargar = (u) => new Promise((ok) => { const im = new Image(); im.onload = () => ok(im); im.src = u; });
    const [ia, ib] = await Promise.all([cargar(ua), cargar(ub)]);
    const datos = (im) => { const c = document.createElement("canvas"); c.width = im.width; c.height = im.height;
      const x = c.getContext("2d"); x.drawImage(im, 0, 0); return x.getImageData(0, 0, im.width, im.height).data; };
    const da = datos(ia), db = datos(ib);
    let n = 0, max = 0;
    for (let i = 0; i < da.length; i += 4) {
      const d = Math.max(Math.abs(da[i] - db[i]), Math.abs(da[i + 1] - db[i + 1]), Math.abs(da[i + 2] - db[i + 2]));
      if (d > 0) { n++; if (d > max) max = d; }
    }
    return { n, max, total: da.length / 4 };
  }, ["data:image/png;base64," + a.toString("base64"), "data:image/png;base64," + b.toString("base64")]);
  await page.close();
  return r;
}

(async () => {
  const o = parseArgs(process.argv.slice(2));
  if (o.medio) fs.mkdirSync(o.medio, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "video-animar-"));
  const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
  let fallos = 0;
  try {
    for (const input of o.inputs) {
      const abs = path.resolve(input), nombre = path.basename(abs, ".html");
      const plantilla = (fs.readFileSync(abs, "utf8").match(/plantilla: ([\w-]+) ·/) || [])[1] || "?";
      const errores = [];
      try {
        const pa = await abrir(browser, abs, errores, !o.cuadrada);
        const A = await foto(pa); await pa.close();
        const copia = path.join(tmp, path.basename(path.dirname(abs)) + "-" + nombre + ".html");
        fs.writeFileSync(copia, fs.readFileSync(abs, "utf8").replace(/<\/body>/i, "<script>\n" + ANIMAR + "\n</script>\n</body>"));
        const pb = await abrir(browser, copia, errores, !o.cuadrada);
        if (o.medio) {
          await pb.evaluate((T) => window.__seek(0.9, T), T);
          fs.writeFileSync(path.join(o.medio, path.basename(path.dirname(abs)) + "-" + nombre + ".medio.png"), await foto(pb));
        }
        await pb.evaluate((T) => window.__seek(999, T), T);
        // __caja (el foco de escena.html) nunca debe lanzar, con cualquier clave
        const caja = await pb.evaluate(() => { try { return window.__caja("0") === null ? "null" : "caja"; } catch (e) { return "ERROR " + e.message; } });
        if (caja.startsWith("ERROR")) errores.push("__caja lanza: " + caja.slice(6));
        const B = await foto(pb); await pb.close();
        if (o.medio) fs.writeFileSync(path.join(o.medio, path.basename(path.dirname(abs)) + "-" + nombre + ".final.png"), B);
        const r = await comparar(browser, A, B);
        const ok = !errores.length && r.n <= r.total * TOLERANCIA;
        if (!ok) fallos++;
        console.log(`${ok ? "ok   " : "FALLO"} ${input} [${plantilla}] · ${r.n} px distintos (${(100 * r.n / r.total).toFixed(3)} %), delta máx ${r.max}`
          + (errores.length ? " · JS: " + [...new Set(errores)].join(" | ") : ""));
      } catch (e) {
        fallos++;
        console.log(`FALLO ${input} [${plantilla}] · ${e.message.split("\n")[0]}` + (errores.length ? " · JS: " + errores.join(" | ") : ""));
      }
    }
  } finally {
    await browser.close();
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  console.log(`[video_animar] ${o.inputs.length - fallos}/${o.inputs.length} tarjetas terminan igual que su render${o.cuadrada ? "" : " (modo vertical)"}`);
  process.exit(fallos ? 1 : 0);
})();
