// Captura de votaciones nominales y del padrón de diputados en congreso.gob.gt (/congreso).
// Se pega TAL CUAL con javascript_tool en una pestaña de https://www.congreso.gob.gt/ (Incapsula bloquea las
// descargas fuera del navegador; dentro de la pestaña, fetch del mismo origen funciona). Solo lectura: GET a páginas
// públicas, sin clics. Guía: referencias/congreso/captura.md.
//
// Uso (en la consola de la pestaña, vía javascript_tool):
//   1) pegar este archivo completo (define window.CG)
//   2) CG.correr({desde: "2026-10-30"})        → sesiones con fecha ≥ desde, sus votaciones y los 160 votos de cada una
//      CG.correr({padron: true})               → los 160 perfiles (nombre, bloque, distrito, foto)
//      CG.correr({fotos: ["929", "840"]})       → retratos (miniatura de la portada) de esos perfiles como dataURL
//      CG.correr({textos: ["/noticias_congreso/17397/2026/4"]})   → texto y og:image de notas oficiales
//      CG.correr({pdfs: ["/assets/uploads/info_legislativo/iniciativas/….pdf"]})   → PDFs como dataURL
//   3) consultar window.CG.estado hasta "listo"; el JSON queda en el <textarea id="cg-salida"> arriba a la izquierda
//      → computer left_click (150, 60) → key cmd+a, cmd+c → pbpaste > archivo → scripts/congreso.py importar|padron|fotos
(() => {
  const W = window;
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const html = async (url) => {
    for (let i = 0; i < 3; i++) {
      try {
        const r = await fetch(url, { credentials: "same-origin" });
        if (r.ok) return new DOMParser().parseFromString(await r.text(), "text/html");
      } catch (e) { /* reintento */ }
      await espera(800 * (i + 1));
    }
    throw new Error("no se pudo leer " + url);
  };
  const limpio = (s) => (s || "").replace(/\s+/g, " ").trim();
  // «No. 56, Fase 1, Fecha 03/11/2026 12:57:59» → "2026-11-03 12:57:59"
  const iso = (s) => {
    const m = (s || "").match(/(\d{2})\/(\d{2})\/(\d{4})\s+(\d{1,2}:\d{2}(?::\d{2})?)/);
    return m ? `${m[3]}-${m[2]}-${m[1]} ${m[4].length === 5 ? m[4] + ":00" : m[4]}` : "";
  };
  const VOTO = { "A FAVOR": "favor", "FAVOR": "favor", "CONTRA": "contra", "EN CONTRA": "contra",
    "AUSENTE": "ausente", "AUSENCIA": "ausente", "LICENCIA / EXCUSA": "licencia", "LICENCIA/EXCUSA": "licencia" };

  async function sesiones(desde) {
    const d = await html("/seccion_informacion_legislativa/votaciones_pleno");
    const out = [];
    for (const tr of d.querySelectorAll("table tr")) {
      const a = tr.querySelector('a[href*="eventos_votaciones/"]');
      if (!a) continue;
      const c = [...tr.cells].map((x) => limpio(x.innerText || x.textContent));
      const fecha = iso(c[2]);
      if (desde && fecha.slice(0, 10) < desde) continue;
      out.push({ id_sesion: a.href.split("/").pop(), tipo_sesion: c[0], no_sesion: c[1], fecha_sesion: fecha, descripcion: c[2] });
    }
    return out;
  }

  async function votaciones(s) {
    const d = await html("/eventos_votaciones/" + s.id_sesion);
    const out = [];
    for (const tr of d.querySelectorAll("table tr")) {
      const a = tr.querySelector('a[href*="detalle_de_votacion/"]');
      if (!a) continue;
      const c = [...tr.cells].map((x) => limpio(x.textContent));
      const partes = a.getAttribute("href").split("/");
      out.push({ id_votacion: partes[partes.length - 2], pregunta: c[0], no_votacion: c[1], fecha_votacion: iso(c[2]),
        url: a.href, pdf: (tr.querySelector('a[href*="pdf_resultado_votacion"]') || {}).href || "" });
    }
    return out;
  }

  async function detalle(v) {
    const d = await html(v.url);
    const filas = [];
    for (const t of d.querySelectorAll("table")) {
      for (const tr of t.querySelectorAll("tbody tr")) {
        const c = [...tr.cells].map((x) => limpio(x.textContent));
        if (!c[0]) continue;
        const crudo = (c[2] || c[1] || "").toUpperCase();
        filas.push({ nombre: c[0], estado: c[1] || "", voto: VOTO[crudo] || crudo.toLowerCase() });
      }
    }
    const cab = limpio((d.body.textContent.match(/Pregunta:[^\n]*?Número:\s*\d+/) || [""])[0]);
    return { filas, cabecera: cab };
  }

  // Las tarjetas de la portada traen nombre, bloque, distrito y la miniatura de los 160 («Bloque: CABAL Distrito: …»);
  // el perfil no dice el bloque. La foto grande se baja solo para los nombrados (fotos()).
  async function padron() {
    const d = await html("/");
    const vistos = new Map();
    for (const a of d.querySelectorAll('a[href*="perfil_diputado/"]')) {
      const id = a.href.split("/").pop();
      if (vistos.has(id)) continue;
      // cada tarjeta es un .event-box; los independientes no llevan «Bloque:» («… INDEPENDIENTE Distrito: …»)
      const c = a.closest(".event-box");
      if (!c) continue;
      const t = limpio(c.textContent);
      const m = t.match(/^(.*?)\s*(?:Bloque:\s*(.*?)|(INDEPENDIENTE))\s*Distrito:\s*(.*?)\s*VER PERFIL/i);
      if (!m) continue;
      const img = c.querySelector("img");
      vistos.set(id, { id, nombre: m[1], bloque: m[2] || m[3] || "", distrito: m[4],
        miniatura: img ? (img.getAttribute("data-src") || img.getAttribute("src") || "").split("?")[0] : "",
        url: location.origin + "/perfil_diputado/" + id });
    }
    return [...vistos.values()];
  }

  // retratos para el avatar: la miniatura de la portada (cara y hombros, recortada por el Congreso); el perfil trae la
  // foto de cuerpo entero con la bandera, que en un círculo no se reconoce
  async function fotos(ids) {
    const pad = new Map((await padron()).map((x) => [x.id, x]));
    const out = {};
    for (const id of ids) {
      const src = (pad.get(String(id)) || {}).miniatura;
      if (!src) { out[id] = null; continue; }
      const b = await (await fetch(src)).blob();
      out[id] = { url: src, data: await new Promise((r) => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b); }) };
      CG.estado = `fotos ${Object.keys(out).length}/${ids.length}`;
    }
    return out;
  }

  // textos de páginas del sitio (notas oficiales: qué buscaba la ley, cómo se aprobó) con su og:image
  async function textos(urls) {
    const out = {};
    for (const u of urls) {
      const d = await html(u);
      d.querySelectorAll("script,style,noscript").forEach((e) => e.remove());
      const og = (d.querySelector('meta[property="og:image"]') || {}).content || "";
      const tit = ((d.querySelector('meta[property="og:title"]') || {}).content || (d.querySelector("title") || {}).textContent || "").trim();
      const cuerpo = [...d.querySelectorAll("p")].map((p) => limpio(p.textContent)).filter((x) => x.length > 40).join("\n\n");
      let foto = null;
      if (og) {
        const b = await (await fetch(og)).blob();
        foto = { url: og, data: await new Promise((r) => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b); }) };
      }
      out[new URL(u, location.origin).href] = { titulo: tit, texto: cuerpo, foto };
    }
    return out;
  }

  // PDFs del sitio (la iniciativa): dataURL; congreso.py leer saca el texto con pdftotext
  async function pdfs(urls) {
    const out = {};
    for (const u of urls) {
      const b = await (await fetch(u)).blob();
      out[new URL(u, location.origin).href] = await new Promise((r) => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b); });
    }
    return out;
  }

  function salida(obj) {
    let ta = document.getElementById("cg-salida");
    if (!ta) {
      ta = document.createElement("textarea");
      ta.id = "cg-salida";
      ta.style.cssText = "position:fixed;left:10px;top:10px;width:300px;height:100px;z-index:2147483647;font:10px monospace";
      document.body.appendChild(ta);
    }
    ta.value = JSON.stringify(obj);
    CG.bytes = ta.value.length;
  }

  const CG = (W.CG = { estado: "inactivo", bytes: 0, error: null });
  CG.correr = (op) => {
    CG.estado = "corriendo"; CG.error = null;
    (async () => {
      try {
        const res = { origen: location.origin, capturado: new Date().toISOString() };
        if (op.padron) res.padron = await padron();
        if (op.fotos) res.fotos = await fotos(op.fotos);
        if (op.textos) res.textos = await textos(op.textos);
        if (op.pdfs) res.pdfs = await pdfs(op.pdfs);
        if (op.desde || op.sesiones) {
          let ss = await sesiones(op.desde);
          if (op.sesiones) ss = ss.filter((s) => op.sesiones.includes(s.id_sesion));
          for (const s of ss) {
            s.votaciones = await votaciones(s);
            for (const v of s.votaciones) {
              Object.assign(v, await detalle(v));
              CG.estado = `sesión ${s.no_sesion} · votación ${v.no_votacion}/${s.votaciones.length}`;
              await espera(120);
            }
          }
          res.sesiones = ss;
        }
        salida(res);
        CG.estado = "listo";
      } catch (e) { CG.error = String(e); CG.estado = "error"; }
    })();
    return "corriendo";
  };
  return "CG listo";
})();
