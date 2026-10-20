#!/usr/bin/env node
/*
 * Video · graba cada escena cuadro a cuadro (estado = seek(t)) y la pasa a ffmpeg (H.264 1080×1920)
 * =================================================================================================
 * Uso (lo llama `scripts/video.py grabar`):
 *   node scripts/video_grabar.js --dir <TRABAJO> --hilo <carpeta del hilo> [--fps 30] [--solo 1,3]
 *
 * Lee TRABAJO/escenas.json y escribe TRABAJO/clips/eN.mp4. Las páginas se sirven desde un origen
 * ficticio http://video.local/ con page.route (mismo origen para que escena.html controle la tarjeta
 * del iframe): video/escena.html (tarjeta), video/golpe.html (gancho y golpes), video/cierre.html,
 * video/animar.js, design/fonts/*.woff2, TRABAJO/escenas.json y tarjeta_N.html = el tuit_N.html del hilo
 * con animar.js inyectado. La plantilla de cada escena la decide su `tipo` (gancho|tarjeta|golpe|cierre).
 * Cualquier otra petición se aborta (cero dependencias externas, como las tarjetas).
 *
 * Salida: 0 ok · 1 error de página o de ffmpeg · 2 uso incorrecto.
 */
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const { chromium } = require("playwright");

const RAIZ = path.dirname(__dirname);
const ORIGEN = "http://video.local/";
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2" };

function args(argv) {
  const o = { fps: 30, solo: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dir") o.dir = argv[++i];
    else if (a === "--hilo") o.hilo = argv[++i];
    else if (a === "--fps") o.fps = Number(argv[++i]);
    else if (a === "--solo") o.solo = argv[++i].split(",").map(Number);
    else if (a === "--help" || a === "-h") { console.log(fs.readFileSync(__filename, "utf8").split("*/")[0]); process.exit(0); }
    else { console.error("Opción desconocida: " + a); process.exit(2); }
  }
  if (!o.dir || !o.hilo || !(o.fps > 0)) { console.error("Uso: node scripts/video_grabar.js --dir TRABAJO --hilo HILO [--fps 30] [--solo 1,3]"); process.exit(2); }
  return o;
}

// ruta pedida → contenido servido
function servir(o, ruta) {
  const nombre = decodeURIComponent(ruta.replace(/^\/+/, "").split("?")[0]);
  const m = nombre.match(/^tarjeta_(\d+)\.html$/);
  if (m) {
    const html = fs.readFileSync(path.join(o.hilo, `tuit_${m[1]}.html`), "utf8");
    return { tipo: TIPOS[".html"], cuerpo: html.replace(/<\/body>/i, '<script src="animar.js"></script>\n</body>') };
  }
  let archivo = null;
  if (/^fonts\/[^/]+\.woff2$/.test(nombre)) archivo = path.join(RAIZ, "design", nombre);
  else if (["escena.html", "golpe.html", "cierre.html", "animar.js"].includes(nombre)) archivo = path.join(RAIZ, "video", nombre);
  else if (nombre === "escenas.json") archivo = path.join(o.dir, nombre);
  if (!archivo || !fs.existsSync(archivo)) return null;
  return { tipo: TIPOS[path.extname(archivo)] || "application/octet-stream", cuerpo: fs.readFileSync(archivo) };
}

(async () => {
  const o = args(process.argv.slice(2));
  const E = JSON.parse(fs.readFileSync(path.join(o.dir, "escenas.json"), "utf8")).escenas;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errores = [];
  page.on("pageerror", (e) => errores.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errores.push(m.text()); });
  await page.route("**", (route) => {
    const url = route.request().url();
    if (!url.startsWith(ORIGEN)) { errores.push("petición externa bloqueada: " + url); return route.abort(); }
    const r = servir(o, url.slice(ORIGEN.length - 1));
    if (!r) { errores.push("no existe: " + url); return route.fulfill({ status: 404, body: "" }); }
    return route.fulfill({ status: 200, contentType: r.tipo, body: r.cuerpo, headers: { "Cache-Control": "no-store" } });
  });
  fs.mkdirSync(path.join(o.dir, "clips"), { recursive: true });
  for (const e of E) {
    if (o.solo && !o.solo.includes(e.n)) continue;
    const tipo = e.tipo || (e.plantilla === "cierre" ? "cierre" : "tarjeta");
    const url = ORIGEN + (tipo === "cierre" ? "cierre.html" : tipo === "tarjeta" ? `escena.html?n=${e.n}` : `golpe.html?n=${e.n}`);
    await page.goto(url, { waitUntil: "load", timeout: 20000 });
    await page.evaluate(() => window.__listo);
    if (errores.length) break;
    const salida = path.join(o.dir, "clips", `e${e.n}.mp4`);
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(o.fps), "-i", "-",
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium", "-r", String(o.fps), salida],
      { stdio: ["pipe", "inherit", "inherit"] });
    const cerrado = new Promise((r) => ff.on("close", r));
    const n = Math.round(e.dur * o.fps);
    for (let i = 0; i < n; i++) {
      await page.evaluate((t) => window.seek(t), i / o.fps);
      ff.stdin.write(await page.screenshot({ type: "png" }));
    }
    ff.stdin.end();
    const codigo = await cerrado;
    if (codigo) errores.push(`ffmpeg salió con ${codigo} en e${e.n}`);
    console.log(`e${e.n} · ${n} cuadros · ${e.dur.toFixed(2)} s`);
    if (errores.length) break;
  }
  await browser.close();
  if (errores.length) { errores.forEach((x) => console.error("ERROR:", x)); process.exit(1); }
})().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
