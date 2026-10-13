// Apiladas · el reparto del todo por fila, a lo largo de una serie o en dos lados: apilada, area_apilada y piramide.
// Mismo contrato que las plantillas de tarjeta (templates/graficos/apilada.html, area-apilada.html, piramide.html):
// los porcentajes los calcula el gráfico, la parte destacada va en col.dest y el resto en la rampa de GX
// (de oscuro a claro), con el mismo tono en las marcas y en la leyenda.

// apilada · barras horizontales apiladas por fila (años o categorías), 100 % o absolutos.
//   etiquetas[2–8], partes[2–5] {nombre, valores}, normalizar (true: cada fila suma 100 %; false: absolutos con el
//   total al final), destacar (índice de la parte clave), rotular "todas"|"destacada", formato.
//   Filas de 34 px con segmentos de 18; leyenda de partes en una fila bajo el gráfico. Alto: 34·n + 30 (+18 por
//   fila extra de leyenda).
G.apilada = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.etiquetas) && S.etiquetas.length >= 2 && S.etiquetas.length <= 8, "apilada admite de 2 a 8 filas (etiquetas)");
  H.assert(Array.isArray(S.partes) && S.partes.length >= 2 && S.partes.length <= 5, "apilada admite de 2 a 5 partes");
  const n = S.etiquetas.length, m = S.partes.length;
  S.partes.forEach((p) => {
    H.assert(p && typeof p.nombre === "string" && Array.isArray(p.valores) && p.valores.length === n, "cada parte necesita nombre y " + n + " valores");
    p.valores.forEach((v) => H.assert(typeof v === "number" && v >= 0, "valores: números ≥ 0"));
  });
  const norm = S.normalizar !== false, hi = GX.indice(S.destacar == null ? 0 : S.destacar, m);
  const totales = S.etiquetas.map((_, r) => S.partes.reduce((s, p) => s + p.valores[r], 0));
  totales.forEach((t, r) => H.assert(t > 0, "la fila «" + S.etiquetas[r] + "» suma 0"));
  const pct = (r, j) => (S.partes[j].valores[r] / totales[r]) * 100;
  const W = ancho, fila = 34, barH = 18;
  const rampa = GX.rampa(Math.max(2, m - 1), col).reverse();
  let k = 0;
  const colorDe = S.partes.map((_, j) => (j === hi ? col.dest : rampa[Math.min(k++, rampa.length - 1)]));
  // Leyenda: swatch 10×10 + nombre, en filas de 18 px (se parte si no cabe en una).
  const ley = S.partes.map((p, j) => ({ j, w: 16 + H.medir(p.nombre, GX.MONO) }));
  let lx = 0, lfila = 0;
  ley.forEach((it) => { if (lx > 0 && lx + it.w > W) { lx = 0; lfila++; } it.x = lx; it.fila = lfila; lx += it.w + 16; });
  const Hh = n * fila + 30 + lfila * 18;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const colIzq = Math.ceil(Math.max(...S.etiquetas.map((e) => H.medir(String(e), GX.SANS)))) + 12;
  const totW = norm ? 0 : Math.ceil(Math.max(...totales.map((t) => H.medir(GX.fmt(t, S.formato), GX.MONO_B)))) + 10;
  const maxT = Math.max(...totales), util = W - colIzq - totW;
  S.etiquetas.forEach((e, r) => {
    const cy = r * fila + fila / 2, y = cy - barH / 2;
    GX.t(svg, 0, cy + 5, String(e), GX.SANS, col.texto);
    const largo = norm ? util : (totales[r] / maxT) * util;
    let x = colIzq;
    S.partes.forEach((p, j) => {
      const w = (p.valores[r] / totales[r]) * largo, wDib = Math.max(0, w - (j === m - 1 ? 0 : 1));   // filo de 1 px
      if (wDib > 0) GX.rect(svg, x, y, wDib, barH, colorDe[j]);
      if (S.rotular !== "destacada" || j === hi) {
        const txt = norm ? H.pct(pct(r, j)) : GX.fmt(p.valores[r], S.formato);
        if (H.medir(txt, GX.MONO_B) <= wDib - 6) GX.t(svg, x + wDib / 2, cy + 4, txt, GX.MONO_B, GX.textoSobre(colorDe[j], col), { "text-anchor": "middle" });
      }
      x += w;
    });
    if (!norm) GX.t(svg, x + 8, cy + 4, GX.fmt(totales[r], S.formato), GX.MONO_B, col.texto);
  });
  const ly = n * fila + 8;
  ley.forEach((it) => {
    const yy = ly + it.fila * 18;
    GX.rect(svg, it.x, yy + 1, 10, 10, colorDe[it.j]);
    GX.t(svg, it.x + 16, yy + 10, S.partes[it.j].nombre, GX.MONO, col.texto);
  });
  if (norm && S.etiquetas.some((_, r) => S.partes.reduce((s, _p, j) => s + Math.round(pct(r, j)), 0) !== 100))
    GX.anotar(el, "Los porcentajes no suman 100 por redondeo.");
};

// area_apilada · bandas apiladas a lo largo de una serie, 100 % o absolutos con eje a la izquierda.
//   etiquetasX[5–30], partes[2–5] {nombre, valores} (partes[0] va abajo), normalizar, destacar (índice), formato.
//   Canal derecho fijo de 120 px con nombre + valor final (una línea si cabe, si no dos); a la izquierda el % inicial
//   (en absolutos, el eje). Etiquetas X: primera, última y cada ⌈n/6⌉ (o más espaciadas si no caben). Alto 260.
G.area_apilada = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.etiquetasX) && S.etiquetasX.length >= 5 && S.etiquetasX.length <= 30, "area-apilada admite de 5 a 30 puntos (etiquetasX)");
  H.assert(Array.isArray(S.partes) && S.partes.length >= 2 && S.partes.length <= 5, "area-apilada admite de 2 a 5 partes");
  const n = S.etiquetasX.length, m = S.partes.length;
  S.partes.forEach((p) => {
    H.assert(p && typeof p.nombre === "string" && p.nombre.trim() && Array.isArray(p.valores) && p.valores.length === n, "cada parte necesita nombre y " + n + " valores");
    p.valores.forEach((v) => H.assert(typeof v === "number" && isFinite(v) && v >= 0, "valores de «" + p.nombre + "»: números ≥ 0"));
  });
  const norm = S.normalizar !== false, hi = GX.indice(S.destacar == null ? 0 : S.destacar, m);
  const totales = S.etiquetasX.map((_, c) => S.partes.reduce((s, p) => s + p.valores[c], 0));
  totales.forEach((t, c) => H.assert(t > 0, "el punto «" + S.etiquetasX[c] + "» suma 0"));
  const acum = S.etiquetasX.map((_, c) => { let s = 0; return S.partes.map((p) => (s += p.valores[c])); });
  const altura = (c, j) => (j < 0 ? 0 : norm ? acum[c][j] / totales[c] : acum[c][j]);
  const pctDe = (c, j) => (S.partes[j].valores[c] / totales[c]) * 100;
  const rampa = GX.rampa(Math.max(2, m - 1), col).reverse();
  let k = 0;
  const colorDe = S.partes.map((_, j) => (j === hi ? col.dest : rampa[Math.min(k++, rampa.length - 1)]));
  const etiqIni = S.partes.map((p, j) => (norm ? H.pct(pctDe(0, j)) : GX.fmt(p.valores[0], S.formato)));
  const etiqFin = S.partes.map((p, j) => (norm ? H.pct(pctDe(n - 1, j)) : GX.fmt(p.valores[n - 1], S.formato)));
  const W = ancho, Hh = alto || 260, canal = 120, top = 10, y1 = Hh - 24, x1 = W - canal;
  const SANS_HI = "800 12px Archivo, sans-serif";
  S.partes.forEach((p) => H.assert(H.medir(p.nombre, GX.SANS_S) <= canal - 12, "doc: el nombre «" + p.nombre + "» no cabe en el canal derecho (120 px): acórtalo"));
  const unaLinea = S.partes.every((p, j) => H.medir(p.nombre, j === hi ? SANS_HI : GX.SANS_S) + H.medir(" " + etiqFin[j], GX.MONO_B) <= canal - 12);
  let dom = [0, 1], tk = [], fEje = S.formato;
  if (!norm) { dom = H.dominio(totales, true); tk = H.ticks(dom[0], dom[1], 4); fEje = H.formatoEje(S.formato, tk); }
  const izq = Math.ceil(norm ? Math.max(...etiqIni.map((s) => H.medir(s, GX.MONO))) : Math.max(...tk.map((t) => H.medir(H.num(t, fEje), GX.MONO)))) + 10;
  const x0 = izq;
  const sx = H.escala([0, n - 1], [x0, x1]), sy = H.escala(dom, [y1, top]);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  if (!norm) for (const t of tk) {
    if (t > 0) GX.linea(svg, x0, sy(t), x1, sy(t), col.suave, { "stroke-width": 1 });
    if (t > 0) GX.t(svg, x0 - 6, sy(t) + 4, H.num(t, fEje), GX.MONO, col.texto, { "text-anchor": "end" });
  }
  // Bandas: path cerrado (borde superior de ida, inferior de vuelta) y filo de 1 px del fondo entre bandas.
  const px = (c) => sx(c).toFixed(1), py = (c, j) => sy(altura(c, j)).toFixed(1);
  const borde = (j) => S.etiquetasX.map((_, c) => (c ? "L" : "M") + px(c) + " " + py(c, j)).join(" ");
  S.partes.forEach((_, j) => {
    const vuelta = S.etiquetasX.map((_, c) => "L" + px(n - 1 - c) + " " + py(n - 1 - c, j - 1)).join(" ");
    H.svgEl("path", { d: borde(j) + " " + vuelta + " Z", fill: colorDe[j] }, svg);
  });
  for (let j = 0; j < m - 1; j++) H.svgEl("path", { d: borde(j), fill: "none", stroke: col.sobre, "stroke-width": 1, "stroke-linejoin": "round" }, svg);
  if (norm) for (const q of [0.25, 0.5, 0.75]) GX.linea(svg, x0, sy(q), x1, sy(q), col.sobre, { "stroke-width": 1, "stroke-dasharray": "3 6", "stroke-opacity": 0.5 });
  GX.linea(svg, x0, y1, x1, y1, col.linea, { "stroke-width": 1 });
  // Rótulos en el centro de cada banda; si el anti-solape los mueve, una guía fina los une a su banda.
  const centro = (c, j) => (sy(altura(c, j)) + sy(altura(c, j - 1))) / 2;
  const colocar = (c, gap, xBorde, xGuia, pinta) => {
    const its = S.partes.map((_, j) => ({ j, yo: centro(c, j), y: centro(c, j) }));
    H.antiSolape(its, { minGap: gap, min: top + (gap > 14 ? 14 : 8), max: y1 - (gap > 14 ? 16 : 8) });
    for (const it of its) {
      if (Math.abs(it.y - it.yo) > 6) GX.linea(svg, xBorde, it.yo, xGuia, it.y, col.suave, { "stroke-width": 1 });
      pinta(it);
    }
  };
  if (norm) colocar(0, 14, x0 - 1, x0 - 5, (it) => GX.t(svg, x0 - 6, it.y + 4, etiqIni[it.j], GX.MONO, col.texto, { "text-anchor": "end" }));
  colocar(n - 1, unaLinea ? 14 : 28, x1 + 1, x1 + 6, (it) => {
    const d = it.j === hi, tc = d ? (col.tinta || col.dest) : col.texto, nombre = S.partes[it.j].nombre, fn = d ? SANS_HI : GX.SANS_S;
    if (unaLinea) {
      const t = H.svgEl("text", { x: x1 + 8, y: it.y + 4, style: "font:" + fn + ";fill:" + tc }, svg);
      H.svgEl("tspan", {}, t).textContent = nombre;
      H.svgEl("tspan", { style: "font:" + GX.MONO_B }, t).textContent = " " + etiqFin[it.j];
    } else {
      GX.t(svg, x1 + 8, it.y - 2, nombre, fn, tc);
      GX.t(svg, x1 + 8, it.y + 12, etiqFin[it.j], GX.MONO_B, tc);
    }
  });
  // Etiquetas X: primera, última y cada ⌈n/6⌉; más espaciadas si no caben a 12 px.
  const wX = Math.max(...S.etiquetasX.map((e) => H.medir(String(e), GX.MONO_B))), pasoPx = (x1 - x0) / (n - 1);
  const paso = Math.max(1, Math.ceil(n / 6), Math.ceil((wX + 8) / pasoPx));
  const idx = []; for (let c = 0; c < n; c += paso) idx.push(c);
  if (idx[idx.length - 1] !== n - 1) { while (idx.length && (n - 1 - idx[idx.length - 1]) * pasoPx < wX + 8) idx.pop(); idx.push(n - 1); }
  for (const c of idx) GX.t(svg, sx(c), Hh - 8, String(S.etiquetasX[c]), c === n - 1 ? GX.MONO_B : GX.MONO, col.texto, { "text-anchor": "middle" });
  if (norm && [0, n - 1].some((c) => S.partes.reduce((s, _p, j) => s + Math.round(pctDe(c, j)), 0) !== 100))
    GX.anotar(el, "Los porcentajes no suman 100 por redondeo.");
};

// piramide · distribución en dos lados con la misma escala (edades por sexo, grupos por zona).
//   grupos[4–12] (de arriba abajo), izquierda {nombre, valores}, derecha {nombre, valores}, destacar (índice del
//   grupo clave; null = ninguno), rotular null|"todos"|"destacado" (null: todos si ≤ 8 grupos y ancho ≥ 480, si no
//   solo el destacado), formato. Columna central con los grupos; barras col.base (la derecha al 70 %) y el grupo
//   destacado en col.dest a ambos lados; valores fuera de la barra. Alto: 24·n + 30 (nombres de lado arriba).
G.piramide = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.grupos) && S.grupos.length >= 4 && S.grupos.length <= 12, "piramide admite de 4 a 12 grupos");
  const n = S.grupos.length;
  for (const lado of ["izquierda", "derecha"]) {
    const L = S[lado];
    H.assert(L && typeof L.nombre === "string" && Array.isArray(L.valores) && L.valores.length === n, lado + " necesita nombre y " + n + " valores");
    L.valores.forEach((v) => H.assert(typeof v === "number" && v >= 0, lado + ": valores numéricos ≥ 0"));
  }
  const W = ancho, fila = 24, cab = 30, Hh = n * fila + cab, barH = 15;
  const hi = GX.indice(S.destacar, n);
  const rotTodos = S.rotular ? S.rotular === "todos" : (n <= 8 && W >= 480);
  const f = (v) => GX.fmt(v, S.formato);
  const todos = S.izquierda.valores.concat(S.derecha.valores), max = Math.max(...todos) || 1;
  const colC = Math.ceil(Math.max(...S.grupos.map((g) => H.medir(String(g), GX.MONO_B)))) + 16;
  const labW = Math.ceil(Math.max(...todos.map((v) => H.medir(f(v), GX.MONO_B)))) + 8;   // hueco del valor fuera de la barra
  const lado = (W - colC) / 2, util = lado - labW - 6, xc0 = lado, xc1 = lado + colC;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  GX.t(svg, xc0 - 6, 14, S.izquierda.nombre, GX.SANS, col.texto, { "text-anchor": "end" });
  GX.t(svg, xc1 + 6, 14, S.derecha.nombre, GX.SANS, col.texto);
  S.grupos.forEach((g, i) => {
    const d = i === hi, cy = cab + i * fila + fila / 2, y = cy - barH / 2;
    GX.t(svg, (xc0 + xc1) / 2, cy + 4, String(g), d ? GX.MONO_B : GX.MONO, col.texto, { "text-anchor": "middle" });
    const vi = S.izquierda.valores[i], vd = S.derecha.valores[i], wi = (vi / max) * util, wd = (vd / max) * util;
    GX.rect(svg, xc0 - 6 - wi, y, wi, barH, d ? col.dest : col.base);
    GX.rect(svg, xc1 + 6, y, wd, barH, d ? col.dest : col.base, d ? {} : { "fill-opacity": 0.7 });
    if (rotTodos || d) {
      const tc = d ? (col.tinta || col.dest) : col.texto;
      GX.t(svg, xc0 - 12 - wi, cy + 4, f(vi), GX.MONO_B, tc, { "text-anchor": "end" });
      GX.t(svg, xc1 + 12 + wd, cy + 4, f(vd), GX.MONO_B, tc);
    }
  });
};
