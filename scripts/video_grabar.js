#!/usr/bin/env node
/*
 * Video · graba cada escena cuadro a cuadro (estado = seek(t)) y la pasa a ffmpeg (H.264 1080×1920)
 * =================================================================================================
 * Uso (lo llama `scripts/video.py grabar`):
 *   node scripts/video_grabar.js --dir <TRABAJO> --hilo <carpeta del hilo> [--fps 30] [--solo 1,3] [--formato 9:16|4:5] [--paralelo N]
 *   node scripts/video_grabar.js --dir <TRABAJO> --hilo <carpeta del hilo> --portadas <json>   (solo cuadros sueltos)
 *
 * Lee TRABAJO/escenas.json y escribe TRABAJO/clips/eN.mp4. Las páginas se sirven desde un origen
 * ficticio http://video.local/ con page.route (mismo origen para que escena.html controle la tarjeta
 * del iframe): video/comun.css y video/comun.js (hoja y módulo común V de todas las páginas de escena),
 * video/escena.html (tarjeta), video/golpe.html (gancho y golpes), video/cierre.html,
 * video/animar.js, video/vertical.css (modo vertical de la tarjeta; escena.html lo inyecta en el iframe cuando
 * la tarjeta ya se dibujó), video/mapa.html (la tarjeta de mapa a pantalla completa) con h.js (bloque H de
 * templates/base.html) y geometria.js (GEOMETRIA de templates/graficos/mapa.html), video/explica.html con
 * video/animaciones/<id>.js (la biblioteca de animaciones de la escena explica), design/fonts/*.woff2,
 * TRABAJO/escenas.json y tarjeta_N.html = el tuit_N.html del hilo con animar.js inyectado. La plantilla de cada
 * escena la decide su `tipo` (gancho|tarjeta|golpe|definicion|adivina|mapa|ranking|escala|tiempo|explica|cierre).
 * Cualquier otra petición se aborta (cero dependencias externas, como las tarjetas).
 * `--paralelo N` graba N escenas a la vez en N páginas del mismo navegador (por defecto min(4, núcleos/4)): el
 * estado de cada página es solo seek(t), así que los clips salen idénticos a la grabación en serie.
 * `--portadas <json>`: [{nombre, n, t, archivo} | {nombre, pagina: "portada", archivo}] → un PNG por entrada, la escena en t
 * con `&portada=1` (sin subtítulos ni barra de progreso) o video/portada.html (portada de texto). No graba clips.
 *
 * Salida: 0 ok · 1 error de página o de ffmpeg · 2 uso incorrecto.
 */
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const os = require("os");
const { chromium } = require("playwright");

const RAIZ = path.dirname(__dirname);
const ORIGEN = "http://video.local/";
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2", ".css": "text/css", ".svg": "image/svg+xml" };

function args(argv) {
  const o = { fps: 30, solo: null, formato: "9:16", paralelo: Math.min(4, Math.max(1, Math.floor(os.cpus().length / 4))) };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dir") o.dir = argv[++i];
    else if (a === "--hilo") o.hilo = argv[++i];
    else if (a === "--fps") o.fps = Number(argv[++i]);
    else if (a === "--solo") o.solo = argv[++i].split(",").map(Number);
    else if (a === "--formato") o.formato = argv[++i];
    else if (a === "--paralelo") o.paralelo = Number(argv[++i]);
    else if (a === "--portadas") o.portadas = argv[++i];
    else if (a === "--help" || a === "-h") { console.log(fs.readFileSync(__filename, "utf8").split("*/")[0]); process.exit(0); }
    else { console.error("Opción desconocida: " + a); process.exit(2); }
  }
  if (!o.dir || !o.hilo || !(o.fps > 0) || !(o.paralelo >= 1)) { console.error("Uso: node scripts/video_grabar.js --dir TRABAJO --hilo HILO [--fps 30] [--solo 1,3] [--paralelo N]"); process.exit(2); }
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
  if (nombre === "h.js") {  // el bloque H de templates/base.html (helpers compartidos con la tarjeta y el informe)
    const base = fs.readFileSync(path.join(RAIZ, "templates", "base.html"), "utf8");
    const mh = base.match(/\/\/ H:INICIO[^\n]*\n([\s\S]*?)\n\/\/ H:FIN/);
    return mh ? { tipo: TIPOS[".js"], cuerpo: mh[1] } : null;
  }
  if (nombre === "geometria.js") {  // GEOMETRIA de los 22 departamentos, de templates/graficos/mapa.html
    const mapa = fs.readFileSync(path.join(RAIZ, "templates", "graficos", "mapa.html"), "utf8");
    const mg = mapa.match(/\/\/ MAPA:GEOMETRIA:INICIO[^\n]*\n([\s\S]*?)\n\/\/ MAPA:GEOMETRIA:FIN/);
    return mg ? { tipo: TIPOS[".js"], cuerpo: mg[1] } : null;
  }
  let archivo = null;
  if (/^fonts\/[^/]+\.woff2$/.test(nombre)) archivo = path.join(RAIZ, "design", nombre);
  else if (/^iconos\/[a-z0-9-]+\.svg$/.test(nombre)) archivo = path.join(RAIZ, "design", nombre);   // biblioteca fija de iconos
  else if (/^animaciones\/[a-z0-9-]+\.js$/.test(nombre)) archivo = path.join(RAIZ, "video", nombre);   // animaciones de la escena explica
  else if (["escena.html", "golpe.html", "cierre.html", "mapa.html", "ranking.html", "escala.html", "tiempo.html", "portada.html", "explica.html", "comun.js", "comun.css", "animar.js", "vertical.css"].includes(nombre)) archivo = path.join(RAIZ, "video", nombre);
  else if (nombre === "escenas.json") archivo = path.join(o.dir, nombre);
  if (!archivo || !fs.existsSync(archivo)) return null;
  return { tipo: TIPOS[path.extname(archivo)] || "application/octet-stream", cuerpo: fs.readFileSync(archivo) };
}

// una página lista para grabar: viewport, captura de errores y el origen ficticio servido con page.route
async function prepararPagina(browser, o, F45, errores) {
  const page = await browser.newPage({ viewport: { width: 1080, height: F45 ? 1350 : 1920 }, deviceScaleFactor: 1 });
  page.on("pageerror", (e) => errores.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errores.push(m.text()); });
  await page.route("**", (route) => {
    const url = route.request().url();
    if (!url.startsWith(ORIGEN)) { errores.push("petición externa bloqueada: " + url); return route.abort(); }
    const r = servir(o, url.slice(ORIGEN.length - 1));
    if (!r) { errores.push("no existe: " + url); return route.fulfill({ status: 404, body: "" }); }
    return route.fulfill({ status: 200, contentType: r.tipo, body: r.cuerpo, headers: { "Cache-Control": "no-store" } });
  });
  return page;
}

function urlDe(e, F45) {
  const tipo = e.tipo || (e.plantilla === "cierre" ? "cierre" : "tarjeta");
  const propia = ["mapa", "ranking", "escala", "tiempo", "explica"].includes(tipo);   // escenas a pantalla completa con página propia
  const pagina = tipo === "cierre" ? "cierre.html?" : tipo === "tarjeta" ? `escena.html?n=${e.n}` : propia ? `${tipo}.html?n=${e.n}` : `golpe.html?n=${e.n}`;
  return ORIGEN + pagina + (F45 ? "&f=45" : "");
}

// graba una escena cuadro a cuadro en la página dada → la línea de resumen, o null si hubo error
async function grabarEscena(page, o, e, F45, CLIPS, errores) {
  await page.goto(urlDe(e, F45), { waitUntil: "load", timeout: 20000 });
  await page.evaluate(() => window.__listo);
  if (errores.length) return null;
  const salida = path.join(o.dir, CLIPS, `e${e.n}.mp4`);
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
  return `e${e.n} · ${n} cuadros · ${e.dur.toFixed(2)} s`;
}

(async () => {
  const o = args(process.argv.slice(2));
  if (!["9:16", "4:5"].includes(o.formato)) { console.error("--formato 9:16 | 4:5"); process.exit(2); }
  const F45 = o.formato === "4:5", CLIPS = F45 ? "clips_4x5" : "clips";   // 4:5 = 1080×1350 para el feed, sin zona segura
  const E = JSON.parse(fs.readFileSync(path.join(o.dir, "escenas.json"), "utf8")).escenas;
  const cola = E.filter((e) => !o.solo || o.solo.includes(e.n));
  const browser = await chromium.launch();
  const errores = [], lineas = new Map();
  if (o.portadas) {  // cuadros sueltos sin subtítulos ni barra: las portadas
    const page = await prepararPagina(browser, o, F45, errores);
    for (const p of JSON.parse(fs.readFileSync(o.portadas, "utf8"))) {
      const e = E.find((x) => x.n === p.n);
      const url = p.pagina === "portada" ? ORIGEN + "portada.html?n=1&portada=1" : urlDe(e, F45) + "&portada=1";
      await page.goto(url, { waitUntil: "load", timeout: 20000 });
      await page.evaluate(() => window.__listo);
      await page.evaluate((t) => window.seek(t), p.t || 0);
      if (errores.length) break;
      await page.screenshot({ type: "png", path: p.archivo });
      console.log(`portada ${p.nombre || "gancho"} · ${path.basename(p.archivo)}`);
    }
    await browser.close();
    if (errores.length) { errores.forEach((x) => console.error("ERROR:", x)); process.exit(1); }
    return;
  }
  fs.mkdirSync(path.join(o.dir, CLIPS), { recursive: true });
  let k = 0;
  // N trabajadores toman escenas de la cola en orden; al primer error, los demás dejan de tomar
  const trabajador = async () => {
    const page = await prepararPagina(browser, o, F45, errores);
    while (k < cola.length && !errores.length) {
      const e = cola[k++];
      const linea = await grabarEscena(page, o, e, F45, CLIPS, errores);
      if (linea) lineas.set(e.n, linea);
    }
    await page.close();
  };
  await Promise.all(Array.from({ length: Math.max(1, Math.min(o.paralelo, cola.length)) }, trabajador));
  await browser.close();
  for (const e of cola) if (lineas.has(e.n)) console.log(lineas.get(e.n));
  if (errores.length) { errores.forEach((x) => console.error("ERROR:", x)); process.exit(1); }
})().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
