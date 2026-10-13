// barras_v · periodos o grupos en columnas, una destacada (Fig. «casos a la SE 35», «edades»).
//   etiquetas[], valores[], destacar (índice; -1 = última), rotular "todas"|"destacada",
//   nivel (índice: línea punteada a la altura de esa barra), banda {desde, hasta, texto},
//   marcadores [{i, n}] (círculos numerados para una lectura guiada), formato.
G.barras_v = (el, S, { ancho, alto, col }) => {
  const n = S.valores.length;
  H.assert(n >= 2 && n <= 16 && S.etiquetas.length === n, "barras_v: 2 a 16 barras con etiquetas");
  const W = ancho, Hh = alto || 250, arriba = 22, abajo = 22, base = Hh - abajo;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const max = Math.max(...S.valores) || 1, slot = W / n, bw = Math.min(40, slot * 0.6);
  const hi = GX.indice(S.destacar == null ? -1 : S.destacar, n);
  const y = (v) => base - (v / max) * (base - arriba);
  if (S.banda) {
    const x0 = S.banda.desde * slot, x1 = (S.banda.hasta + 1) * slot;
    GX.rect(svg, x0, 0, x1 - x0, base, col.dest, { "fill-opacity": 0.1 });
    if (S.banda.texto) GX.t(svg, x0 + 10, 18, S.banda.texto, GX.MONO_B, col.tinta || col.texto);
  }
  if (S.nivel != null) GX.linea(svg, 0, y(S.valores[S.nivel]), W, y(S.valores[S.nivel]), col.dest, { "stroke-dasharray": "4 4" });
  S.valores.forEach((v, i) => {
    const x = i * slot + (slot - bw) / 2, d = i === hi;
    GX.rect(svg, x, y(v), bw, base - y(v), d ? col.dest : col.base);
    if (S.rotular !== "destacada" || d) GX.t(svg, x + bw / 2, y(v) - 8, GX.fmt(v, S.formato), d ? GX.MONO_D : GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": "middle" });
    GX.t(svg, x + bw / 2, Hh - 4, S.etiquetas[i], d ? GX.MONO_B : GX.MONO, col.texto, { "text-anchor": "middle" });
  });
  GX.linea(svg, 0, base, W, base, col.linea);
  for (const m of S.marcadores || []) {
    const x = m.i * slot + slot / 2 + (m.lado === "derecha" ? bw / 2 + 18 : 0);
    GX.marcador(svg, x, Math.max(14, y(S.valores[m.i]) - (m.lado === "derecha" ? 0 : 34)), m.n, col);
  }
};

// barras_h · ranking con nombre a la izquierda y valor al final de la barra.
//   items [{nombre, valor}], destacar (índice), formato, orden "dado"|"desc".
G.barras_h = (el, S, { ancho, col }) => {
  const items = S.orden === "desc" ? S.items.slice().sort((a, b) => b.valor - a.valor) : S.items.slice();
  const n = items.length, fila = 30, Hh = n * fila;
  H.assert(n >= 2 && n <= 12, "barras_h: 2 a 12 items");
  const hi = GX.indice(S.destacar == null ? 0 : S.destacar, n);
  const etiq = Math.ceil(Math.max(...items.map((it) => H.medir(it.nombre, GX.SANS_D)))) + 16;
  const valW = Math.ceil(Math.max(...items.map((it) => H.medir(GX.fmt(it.valor, S.formato), GX.MONO_D)))) + 10;
  const W = ancho, util = W - etiq - valW, max = Math.max(...items.map((it) => it.valor)) || 1;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  items.forEach((it, i) => {
    const d = i === hi, w = (it.valor / max) * util, yy = i * fila;
    GX.t(svg, 0, yy + 20, it.nombre, d ? GX.SANS_D : GX.SANS, col.texto);
    GX.rect(svg, etiq, yy + 7, w, 16, d ? col.dest : col.base);
    GX.t(svg, etiq + w + 8, yy + 20, GX.fmt(it.valor, S.formato), d ? GX.MONO_D : GX.MONO_B, d ? (col.tinta || col.dest) : col.texto);
  });
  GX.linea(svg, etiq, 0, etiq, Hh, col.linea, { "stroke-width": 1 });
};

// divergente · cambios con signo; nombre encima de cada barra (cabe a media página).
//   items [{nombre, valor}], destacar (índice), formato (signo/sufijo).
G.divergente = (el, S, { ancho, col }) => {
  const n = S.items.length, fila = 31, Hh = n * fila;
  const hi = GX.indice(S.destacar == null ? 0 : S.destacar, n);
  const vals = S.items.map((it) => it.valor), min = Math.min(0, ...vals), max = Math.max(0, ...vals);
  const W = ancho, margen = 44, util = W - margen * (min < 0 && max > 0 ? 2 : 1);
  const esc = util / ((max - min) || 1), x0 = (min < 0 ? (max > 0 ? margen : margen) : 0) + (-min) * esc;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  S.items.forEach((it, i) => {
    const d = i === hi, yy = i * fila, w = Math.abs(it.valor) * esc, x = it.valor < 0 ? x0 - w : x0;
    GX.t(svg, 0, yy + 11, it.nombre, d ? "800 13px Archivo, sans-serif" : "600 13px Archivo, sans-serif", d ? col.dest : col.texto);
    GX.rect(svg, x, yy + 15, w, 11, d ? col.dest : col.base);
    const lab = GX.fmt(it.valor, S.formato);
    GX.t(svg, it.valor < 0 ? x - 6 : x + w + 6, yy + 24, lab, GX.MONO_B, d ? col.dest : col.texto, { "text-anchor": it.valor < 0 ? "end" : "start" });
  });
  GX.linea(svg, x0, 0, x0, Hh, col.linea);
};

// columnas · dos series por periodo en columnas verticales (p. ej. año completo frente a SE 35); valores null = sin dato.
//   Solo documento (la plantilla de tarjeta `agrupadas` es horizontal y tiene su propio G.agrupadas).
//   etiquetas[], series [{nombre, valores, estilo "base"|"fuerte"}], destacar {serie, i},
//   rotular [[serie, i], …] (qué valores llevan cifra), formato.
G.columnas = (el, S, { ancho, alto, col }) => {
  const n = S.etiquetas.length, k = S.series.length, W = ancho, Hh = alto || 326, arriba = 30, base = Hh - 26;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const max = Math.max(...S.series.flatMap((s) => s.valores.filter((v) => v != null))) || 1;
  const slot = W / n, bw = Math.min(20, (slot * 0.7) / k), gap = 2, grupo = k * bw + (k - 1) * gap;
  const y = (v) => base - (v / max) * (base - arriba);
  const rot = new Set((S.rotular || []).map((p) => p.join(":")));
  S.etiquetas.forEach((et, i) => {
    const gx = i * slot + (slot - grupo) / 2;
    S.series.forEach((s, j) => {
      const v = s.valores[i];
      if (v == null) return;
      const d = S.destacar && S.destacar.serie === j && S.destacar.i === i;
      const x = gx + j * (bw + gap);
      GX.rect(svg, x, y(v), bw, base - y(v), d ? col.dest : s.estilo === "fuerte" ? col.linea : col.base);
      if (rot.has(j + ":" + i) || d) GX.t(svg, x + bw / 2, y(v) - 8, GX.fmt(v, S.formato), d ? GX.MONO_D : GX.MONO_B, d ? col.dest : col.texto, { "text-anchor": "middle" });
    });
    GX.t(svg, i * slot + slot / 2, Hh - 6, et, i === n - 1 ? GX.MONO_B : GX.MONO, col.texto, { "text-anchor": "middle" });
  });
  GX.linea(svg, 0, base, W, base, col.linea);
};
