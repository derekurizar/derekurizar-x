#!/usr/bin/env node
/*
 * Carrusel · renderiza las láminas de /carrusel a PNG y comprueba CA9–CA12
 * =========================================================================
 * Uso (lo llama `scripts/carrusel.py render`):
 *   node scripts/carrusel.js --dir <TRABAJO> --out <carpeta> [--formato 4:5|9:16] [--check] [--solo 1,3]
 *
 * Lee TRABAJO/laminas.json (lo escribe carrusel.py render desde carrusel.json) y escribe <out>/lamina_NN.png
 * (1080×1350 en 4:5, 1080×1920 en 9:16; deviceScaleFactor 1). Las páginas se sirven desde un origen ficticio
 * http://carrusel.local/ con page.route (mismo origen: la lámina mide la tarjeta de su iframe): lamina.html y
 * carrusel.css (templates/carrusel/), comun.css y vertical.css (video/), fonts/*.woff2 (design/fonts/), laminas.json y
 * tarjeta_N.html (= TRABAJO/tarjetas/tuit_N.html, la tarjeta rearmada en Noche por carrusel.py preparar). Cualquier
 * otra petición se aborta (cero dependencias externas).
 *
 * Checks de página (con --check, una falla sale con 3; sin --check se imprimen como aviso):
 *   CA9  lienzo: body[data-listo] sin data-error; cada texto fuera de la tarjeta ≥ 28 px y dentro del lienzo; ninguna
 *        petición externa ni archivo que falte; las 3 familias Noche cargadas (JetBrains Mono, Archivo, Archivo condensada)
 *   CA10 miniatura (portada): cifra ≥ 220 px y título ≥ 96 px, los dos dentro del recorte 3:4 central (4:5: x 34–1046;
 *        9:16: y 240–1680); en 9:16 todo lo visible (textos y la tarjeta) en la zona segura del modo foto (x 57–1023,
 *        y 215–1645, y fuera de la columna de íconos: x ≤ 900 desde y 1070)
 *   CA11 ≤ 1 texto en el acento fuera de la tarjeta; templates/carrusel/* sin colores hex ni https
 *   CA12 pie: «Fuente: …» (menos en el cierre), el handle y el contador n/N
 *
 * Salida: 0 ok · 1 error de página · 2 uso incorrecto · 3 CA9–CA12.
 */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const RAIZ = path.dirname(__dirname);
const ORIGEN = "http://carrusel.local/";
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2", ".css": "text/css" };
const PLANTILLAS = path.join(RAIZ, "templates", "carrusel");
const FORMATOS = { "4:5": { h: 1350, f: "" }, "9:16": { h: 1920, f: "&f=916" } };

function args(argv) {
  const o = { formato: "4:5", check: false, solo: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dir") o.dir = argv[++i];
    else if (a === "--out") o.out = argv[++i];
    else if (a === "--formato") o.formato = argv[++i];
    else if (a === "--check") o.check = true;
    else if (a === "--solo") o.solo = argv[++i].split(",").map(Number);
    else if (a === "--help" || a === "-h") { console.log(fs.readFileSync(__filename, "utf8").split("*/")[0]); process.exit(0); }
    else { console.error("Opción desconocida: " + a); process.exit(2); }
  }
  if (!o.dir || !o.out || !FORMATOS[o.formato]) { console.error("Uso: node scripts/carrusel.js --dir TRABAJO --out CARPETA [--formato 4:5|9:16] [--check]"); process.exit(2); }
  return o;
}

function servir(o, ruta) {
  const nombre = decodeURIComponent(ruta.replace(/^\/+/, "").split("?")[0]);
  let archivo = null;
  const m = nombre.match(/^tarjeta_(\d+)\.html$/);
  if (m) archivo = path.join(o.dir, "tarjetas", `tuit_${m[1]}.html`);
  else if (/^fonts\/[^/]+\.woff2$/.test(nombre)) archivo = path.join(RAIZ, "design", nombre);
  else if (["lamina.html", "carrusel.css"].includes(nombre)) archivo = path.join(PLANTILLAS, nombre);
  else if (["comun.css", "vertical.css"].includes(nombre)) archivo = path.join(RAIZ, "video", nombre);
  else if (nombre === "laminas.json") archivo = path.join(o.dir, nombre);
  if (!archivo || !fs.existsSync(archivo)) return null;
  return { tipo: TIPOS[path.extname(archivo)] || "application/octet-stream", cuerpo: fs.readFileSync(archivo) };
}

// CA11 (lint): las plantillas del carrusel sin colores escritos ni dependencias externas
function lint() {
  const f = [];
  for (const nombre of fs.readdirSync(PLANTILLAS)) {
    const s = fs.readFileSync(path.join(PLANTILLAS, nombre), "utf8");
    const hex = s.match(/#[0-9a-fA-F]{3,8}\b/g), ext = s.match(/https?:\/\//g);
    if (hex) f.push(`CA11 templates/carrusel/${nombre} tiene colores hex (${[...new Set(hex)].join(", ")}): solo variables`);
    if (ext) f.push(`CA11 templates/carrusel/${nombre} tiene una dirección https: cero dependencias externas`);
  }
  return f;
}

// los checks que corren dentro de la página (una función pura de lo dibujado)
function medir({ formato, handle }) {
  const W = innerWidth, H = innerHeight, f = [], F916 = formato === "9:16";
  const body = document.body, n = Number(new URLSearchParams(location.search).get("n"));
  if (!body.dataset.listo) f.push("CA9 la lámina no terminó (body sin data-listo)");
  if (body.dataset.error) f.push("CA9 error en la lámina: " + body.dataset.error);
  const cajas = [];
  const w = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  for (let t = w.nextNode(); t; t = w.nextNode()) {
    const p = t.parentElement;
    if (!t.textContent.trim() || !p || p.closest("script, style")) continue;
    const r = document.createRange(); r.selectNodeContents(t);
    const b = r.getBoundingClientRect(), fs = parseFloat(getComputedStyle(p).fontSize);
    const txt = t.textContent.trim().slice(0, 30);
    cajas.push({ b, p, txt });
    if (fs < 27.5) f.push(`CA9 «${txt}» a ${fs.toFixed(0)} px: fuera de la tarjeta todo texto va ≥ 28 px`);
    if (b.left < -0.5 || b.top < -0.5 || b.right > W + 0.5 || b.bottom > H + 0.5) f.push(`CA9 «${txt}» se sale del lienzo (${[b.left, b.top, b.right, b.bottom].map(Math.round)})`);
    if (p.scrollWidth > p.clientWidth + 2 && getComputedStyle(p).overflow === "hidden") f.push(`CA9 «${txt}» queda cortado en su caja`);
  }
  const cargadas = new Set([...document.fonts].filter((x) => x.status === "loaded").map((x) => x.family.replace(/["']/g, "")));
  for (const fam of ["JetBrains Mono", "Archivo"]) if (!cargadas.has(fam)) f.push(`CA9 la familia ${fam} no se cargó`);
  if (!document.fonts.check("extra-condensed 900 120px Archivo")) f.push("CA9 Archivo condensada no se cargó");
  // CA10 miniatura (portada)
  const crop = F916 ? [0, 240, 1080, 1680] : [34, 0, 1046, 1350];
  const dentro = (b, c) => b.left >= c[0] - 0.5 && b.top >= c[1] - 0.5 && b.right <= c[2] + 0.5 && b.bottom <= c[3] + 0.5;
  for (const [sel, min, nombre] of [[".portada .cifra", 220, "la cifra"], [".portada .titulo", 96, "el título"]]) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < min - 0.5) f.push(`CA10 ${nombre} de la portada a ${fs.toFixed(0)} px: mínimo ${min} (se lee en la miniatura)`);
    const r = document.createRange(); r.selectNodeContents(el); const b = r.getBoundingClientRect();
    if (!dentro(b, crop)) f.push(`CA10 ${nombre} de la portada sale del recorte 3:4 de la miniatura (${[b.left, b.top, b.right, b.bottom].map(Math.round)})`);
  }
  if (F916) {
    const zona = (b) => b.left >= 57 && b.top >= 215 && b.right <= 1023 && b.bottom <= 1645 && !(b.right > 900 && b.bottom > 1070);
    for (const { b, txt } of cajas) if (!zona(b)) f.push(`CA10 «${txt}» fuera de la zona segura del modo foto (${[b.left, b.top, b.right, b.bottom].map(Math.round)})`);
    const c = window.__cajaTarjeta;
    if (c && !zona({ left: c[0], top: c[1], right: c[2], bottom: c[3] })) f.push(`CA10 la tarjeta sale de la zona segura del modo foto (${c})`);
  }
  // CA11 una sola cosa en el acento fuera de la tarjeta
  const sonda = document.createElement("span"); sonda.style.color = "var(--acento)"; body.appendChild(sonda);
  const acento = getComputedStyle(sonda).color; sonda.remove();
  const enAcento = new Set(cajas.filter(({ p }) => getComputedStyle(p).color === acento).map(({ p }) => p));
  if (enAcento.size > 1) f.push(`CA11 ${enAcento.size} textos en el acento (${[...enAcento].map((p) => "«" + p.textContent.trim().slice(0, 20) + "»").join(", ")}): uno por lámina`);
  // CA12 pie
  const pie = document.getElementById("pie"), tipo = (document.querySelector("main.lam") || { classList: [] }).classList[1];
  if (!pie) f.push("CA12 la lámina no tiene pie");
  else {
    const fuente = pie.querySelector(".fuente");
    if (tipo !== "cierre" && !(fuente && /^Fuente: \S/.test(fuente.textContent))) f.push("CA12 el pie no lleva «Fuente: …»");
    if (fuente && fuente.scrollHeight > fuente.clientHeight + 2) f.push("CA12 la fuente no cabe en dos líneas: acórtala");
    const cont = pie.querySelector("#contador");
    if (!cont || !new RegExp("^" + n + "/\\d+$").test(cont.textContent.trim())) f.push(`CA12 el contador no dice ${n}/N (dice «${cont ? cont.textContent : ""}»)`);
    const h = pie.querySelector("#handle");
    if (!h || h.textContent.trim() !== handle) f.push(`CA12 el pie no lleva el handle ${handle}`);
  }
  return f;
}

async function main() {
  const o = args(process.argv.slice(2));
  const L = JSON.parse(fs.readFileSync(path.join(o.dir, "laminas.json"), "utf8"));
  const { h, f: qf } = FORMATOS[o.formato];
  fs.mkdirSync(o.out, { recursive: true });
  const fallas = lint();
  const browser = await chromium.launch();
  let error = false;
  try {
    for (const lam of L.laminas) {
      if (o.solo && !o.solo.includes(lam.n)) continue;
      const errores = [];
      const page = await browser.newPage({ viewport: { width: 1080, height: h }, deviceScaleFactor: 1 });
      page.on("pageerror", (e) => errores.push(e.message));
      page.on("console", (m) => { if (m.type() === "error") errores.push(m.text()); });
      await page.route("**", (route) => {
        const url = route.request().url();
        if (url.startsWith("data:") || url.startsWith("about:")) return route.continue();
        if (!url.startsWith(ORIGEN)) { errores.push("CA9 petición externa bloqueada: " + url); return route.abort(); }
        const r = servir(o, url.slice(ORIGEN.length - 1));
        if (!r) { errores.push("CA9 no existe: " + url); return route.fulfill({ status: 404, body: "" }); }
        return route.fulfill({ status: 200, contentType: r.tipo, body: r.cuerpo, headers: { "Cache-Control": "no-store" } });
      });
      await page.goto(`${ORIGEN}lamina.html?n=${lam.n}${qf}`, { waitUntil: "load" });
      await page.waitForFunction(() => document.body && document.body.dataset.listo, null, { timeout: 30000 });
      const f = await page.evaluate(medir, { formato: o.formato, handle: L.handle });
      const nombre = `lamina_${String(lam.n).padStart(2, "0")}.png`;
      await page.screenshot({ path: path.join(o.out, nombre), clip: { x: 0, y: 0, width: 1080, height: h } });
      await page.close();
      const todas = [...errores, ...f].map((x) => `lámina ${lam.n} (${lam.tipo}): ${x}`);
      if (errores.some((x) => !x.startsWith("CA9"))) error = true;
      fallas.push(...todas);
      console.log(`${todas.length ? "FALLA" : "OK   "} ${nombre} · ${lam.tipo}`);
    }
  } finally {
    await browser.close();
  }
  for (const x of fallas) console.log((o.check ? "FALLA " : "AVISO ") + x);
  if (error) process.exit(1);
  if (o.check && fallas.length) process.exit(3);
  console.log(`[carrusel.js] ${L.laminas.length} láminas ${o.formato} → ${path.relative(RAIZ, o.out) || o.out}${fallas.length ? " · " + fallas.length + " aviso(s)" : ""}`);
}

main().catch((e) => { console.error("ERROR:", e.message); process.exit(1); });
