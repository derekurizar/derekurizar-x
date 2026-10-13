// Comunes de los gráficos del informe. Cada G.<tipo>(el, spec, ctx) dibuja UN <svg> (o HTML) dentro de
// `el`; ctx = { ancho, alto, col } y col es el esquema de color del lugar (I.esquema: papel o panel):
//   texto · base (marcas atenuadas) · dest (la marca que importa) · linea (ejes) · suave · sobre (fondo)
//   · tinta (solo en papel: acento para texto, papel_tinta)
// Las cifras llegan crudas y en la unidad de la fuente; el formato lo pone spec.formato.
// Regla: un G.* pinta SOLO con col.* y GX.*; nunca con H.color/H.rampa/H.halo/H.periodos/H.textoSobre
// (leen las variables CSS de la tarjeta) ni con los helpers que tocan el DOM de la tarjeta
// (H.espacio, H.lienzo, H.leyenda, H.anotar, H.cabecera, H.verificar). Lo vigila check_workflows W8.
const GX = (() => {
  const fmt = (v, f) => {
    if (v == null) return "—";
    const ff = Object.assign({ decimales: H.decimalesDe([v], 2), miles: true }, f || {});
    return H.num(v, ff);
  };
  const lienzo = (el, w, h, aria) => {
    el.innerHTML = "";
    const svg = H.svgEl("svg", { viewBox: "0 0 " + w + " " + h, width: w, height: h, role: "img", "aria-label": aria || "" }, el);
    return svg;
  };
  const rect = (svg, x, y, w, h, fill, extra) => H.svgEl("rect", Object.assign({ x, y, width: Math.max(0, w), height: Math.max(0, h), fill }, extra || {}), svg);
  const linea = (svg, x1, y1, x2, y2, stroke, extra) => H.svgEl("line", Object.assign({ x1, y1, x2, y2, stroke, "stroke-width": 1.5 }, extra || {}), svg);
  const t = (svg, x, y, s, font, fill, extra) => H.texto(svg, x, y, s, Object.assign({ style: "font:" + font, fill }, extra || {}));
  // Tipografías del documento (piso 12 px, tokens.documento.pisoPx).
  const MONO = "500 12px 'JetBrains Mono', monospace", MONO_B = "700 12px 'JetBrains Mono', monospace", MONO_D = "700 14px 'JetBrains Mono', monospace";
  const SANS = "600 14px Archivo, sans-serif", SANS_D = "800 14px Archivo, sans-serif", SANS_S = "600 12px Archivo, sans-serif";
  const serif = (px) => "400 " + px + "px 'Instrument Serif', Georgia, serif";
  const indice = (d, n) => (d == null ? -1 : ((d % n) + n) % n);
  const marcador = (svg, cx, cy, n, col) => {
    H.svgEl("circle", { cx, cy, r: 11, fill: col.texto }, svg);
    t(svg, cx, cy + 4.5, String(n), MONO_B, col.sobre, { "text-anchor": "middle" });
  };
  // Rampa secuencial de n clases (2–9) de la MÁS BAJA a la MÁS ALTA, según el lugar:
  //   panel → H.rampa (lee --bg/--ink del body, que informe.py define para la paleta);
  //   papel → de un tinte claro de col.dest (≥ 1.5:1 sobre el papel) a col.tinta, en RGB lineal (H.mezcla).
  const rampa = (n, col) => {
    n = Math.max(2, Math.min(9, Math.round(n)));
    if (!col.tinta) return H.rampa(n);
    let t0 = 0.25, a = H.mezcla(col.sobre, col.dest, t0);
    while (H.contraste(a, col.sobre) < 1.5 && t0 < 0.9) a = H.mezcla(col.sobre, col.dest, (t0 += 0.05));
    return Array.from({ length: n }, (_, k) => H.mezcla(a, col.tinta, k / (n - 1)));
  };
  // Color de texto legible sobre un relleno: el de más contraste entre texto, fondo y los dos neutros.
  const textoSobre = (relleno, col) => [col.texto, col.sobre, "#F6F2E8", "#0C1520"].reduce((m, c) => (H.contraste(relleno, c) > H.contraste(relleno, m) ? c : m));
  // Halo del color del fondo para texto que pisa barras o líneas (paint-order).
  const halo = (col) => "paint-order:stroke;stroke:" + col.sobre + ";stroke-width:4px;stroke-linejoin:round";
  // Nota automática del gráfico (redondeo, agrupación, dos escalas): un <span class="nota"> tras el SVG,
  // dentro de .grafico (base.html ya la viste a 12 px mono en papel y en panel). Espejo de H.anotar.
  const anotar = (el, texto) => {
    if (!texto) return;
    let n = el.querySelector(":scope > span.nota");
    if (!n) { n = document.createElement("span"); n.className = "nota"; n.style.display = "block"; el.appendChild(n); }
    n.textContent = (n.textContent ? n.textContent + " " : "") + texto;
  };
  // Periodos (linea, barras_v): bandas alternas con nombre arriba, a 12 px. P = H.validarPeriodos(...);
  // bordes(i) → [xIzq, xDer] del hueco de la marca i. Llamar ANTES de dibujar las marcas.
  const periodos = (svg, P, bordes, yTop, yBot, yNombre, col) => {
    P.forEach((p, k) => {
      const xa = bordes(p.desde)[0], xb = bordes(p.hasta)[1];
      if (k % 2 === 0) rect(svg, xa, yTop, xb - xa, yBot - yTop, col.suave);
      else linea(svg, xa, yTop, xa, yBot, col.linea, { "stroke-width": 1, "stroke-dasharray": "3 5", "stroke-opacity": 0.5 });
      const w = H.medir(p.nombre, MONO);
      H.assert(w <= xb - xa - 6, "periodo «" + p.nombre + "» no cabe en su banda (" + Math.round(w) + "px > " + Math.round(xb - xa - 6) + "): acórtalo");
      t(svg, (xa + xb) / 2, yNombre, p.nombre, MONO, col.texto, { "text-anchor": "middle" });
    });
  };
  // Patrón rayado «sin dato» (mapa, calor); devuelve la url(#id) y lo define una sola vez por svg.
  const sinDato = (svg, col) => {
    const id = "sinDato" + Math.random().toString(36).slice(2, 7);
    const defs = H.svgEl("defs", {}, svg);
    const pat = H.svgEl("pattern", { id, width: 8, height: 8, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    H.svgEl("rect", { width: 8, height: 8, fill: col.suave }, pat);
    H.svgEl("line", { x1: 0, y1: 0, x2: 0, y2: 8, stroke: col.base, "stroke-width": 2 }, pat);
    return "url(#" + id + ")";
  };
  return { fmt, lienzo, rect, linea, t, MONO, MONO_B, MONO_D, SANS, SANS_D, SANS_S, serif, indice, marcador, rampa, textoSobre, halo, anotar, periodos, sinDato };
})();
