// barras_v · periodos o grupos en columnas, una destacada (Fig. «casos a la SE 35», «edades»).
//   Contrato de la tarjeta barras-v: etiquetas[], valores[] (con negativos el eje queda en el cero y el rótulo
//   va bajo la barra), destacar (índice; -1 = última), rotular "todas"|"destacada", referencia {valor, texto}
//   (línea punteada en el acento con rótulo), periodos [{desde, hasta, nombre}] (≤ 4 bandas con nombre arriba),
//   formato. Extensiones del documento: nivel (índice: línea punteada a la altura de esa barra), banda {desde,
//   hasta, texto}, marcadores [{i, n, lado}] (círculos numerados para una lectura guiada), claves (nombres
//   largos de las etiquetas; no se dibujan). Alto por defecto 250. De 2 a 12 barras (doc: hasta 16 si el ancho
//   es ≥ 560). Si los rótulos no caben en su hueco se rotula solo la destacada (y se anota); si las etiquetas
//   no caben, se escriben alternas conservando la de la destacada.
G.barras_v = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.etiquetas) && Array.isArray(S.valores) && S.etiquetas.length === S.valores.length, "etiquetas y valores deben tener la misma longitud");
  const n = S.valores.length;
  H.assert(n >= 2 && (n <= 12 || (n <= 16 && ancho >= 560)), n > 12 && n <= 16 ? "doc: barras_v admite hasta 16 barras solo con ancho ≥ 560 px (aquí " + ancho + ")" : "barras-v admite de 2 a 12 barras");
  S.valores.forEach((v) => H.assert(typeof v === "number" && isFinite(v), "valores debe ser numérico"));
  const P = H.validarPeriodos(S.periodos, n), R = S.referencia || null;
  if (R) H.assert(typeof R.valor === "number" && isFinite(R.valor) && typeof R.texto === "string" && R.texto.trim(), "referencia necesita valor numérico y texto");
  const W = ancho, Hh = alto || 250, arriba = P.length ? 40 : 22, abajo = 22, base = Hh - abajo;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const vals = S.valores, hi = GX.indice(S.destacar == null ? -1 : S.destacar, n);
  const dom = H.dominio(vals.concat(R ? [R.valor] : []), true);
  // Con negativos, 16 px bajo la barra más baja para su rótulo (va debajo de la barra, como en la tarjeta).
  const minV = Math.min(...vals);
  if (minV < 0) { const r = 16 / (base - arriba); dom[0] = Math.min(dom[0], (minV - r * dom[1]) / (1 - r)); }
  const y = H.escala(dom, [base, arriba]), yz = y(0);
  const slot = W / n, bw = Math.min(40, slot * 0.6);
  const fV = (i) => GX.fmt(vals[i], S.formato), fontV = (i) => (i === hi ? GX.MONO_D : GX.MONO_B), fontE = (i) => (i === hi ? GX.MONO_B : GX.MONO);
  // Rótulos de valor: todos si dos vecinos no se pisan; si no, alternos (con la destacada); si ni así, solo la destacada.
  const wV = vals.map((v, i) => H.medir(fV(i), fontV(i)));
  const caben = (p) => wV.every((w, i) => i + p >= n || (w + wV[i + p]) / 2 <= p * slot - 4);
  let rotular = S.rotular === "destacada" ? "destacada" : "todas", pasoV = 1;
  if (rotular === "todas" && !caben(1)) {
    if (caben(2)) pasoV = 2;
    else { rotular = "destacada"; GX.anotar(el, "Se rotula solo la barra destacada: las cifras no caben a este ancho."); }
  }
  const etW = S.etiquetas.map((e, i) => H.medir(String(e), fontE(i)));
  let paso = 1;
  if (etW.some((w) => w > slot - 2)) {
    paso = 2;
    H.assert(etW.every((w) => w <= 2 * slot - 2), "doc: las etiquetas no caben a " + W + " px: acórtalas o usa menos barras");
  }
  const bordes = (i) => [i * slot, (i + 1) * slot];
  if (P.length) GX.periodos(svg, P, bordes, 16, base, 12, col);
  if (S.banda) {
    const x0 = S.banda.desde * slot, x1 = (S.banda.hasta + 1) * slot, yb = P.length ? 16 : 0;
    GX.rect(svg, x0, yb, x1 - x0, base - yb, col.dest, { "fill-opacity": 0.1 });
    if (S.banda.texto) GX.t(svg, x0 + 10, yb + 18, S.banda.texto, GX.MONO_B, col.tinta || col.texto);
  }
  if (S.nivel != null) GX.linea(svg, 0, y(vals[S.nivel]), W, y(vals[S.nivel]), col.dest, { "stroke-dasharray": "4 4" });
  vals.forEach((v, i) => {
    const x = i * slot + (slot - bw) / 2, d = i === hi, yv = y(v);
    GX.rect(svg, x, Math.min(yv, yz), bw, Math.abs(yz - yv), d ? col.dest : col.base);
    if (d || (rotular === "todas" && (i - hi) % pasoV === 0)) GX.t(svg, x + bw / 2, v < 0 ? yv + (d ? 15 : 13) : yv - 8, fV(i), fontV(i), d ? (col.tinta || col.dest) : col.texto, { "text-anchor": "middle" });
    if ((i - hi) % paso === 0) GX.t(svg, x + bw / 2, Hh - 4, String(S.etiquetas[i]), fontE(i), col.texto, { "text-anchor": "middle" });
  });
  GX.linea(svg, 0, yz, W, yz, col.linea);
  if (R) {
    const yr = y(R.valor);
    GX.linea(svg, 0, yr, W, yr, col.dest, { "stroke-dasharray": "5 4" });
    GX.t(svg, W, yr - 5, R.texto.trim() + " · " + GX.fmt(R.valor, S.formato), GX.MONO_B, col.tinta || col.dest, { "text-anchor": "end" });
  }
  for (const m of S.marcadores || []) {
    const x = m.i * slot + slot / 2 + (m.lado === "derecha" ? bw / 2 + 18 : 0);
    GX.marcador(svg, x, Math.max(14, y(vals[m.i]) - (m.lado === "derecha" ? 0 : 34)), m.n, col);
  }
};

// barras_h · ranking con nombre a la izquierda y valor al final de la barra (tarjeta barras-h).
//   items [{nombre, valor, valor_texto?}] (valor_texto sustituye al número formateado), destacar (índice tras
//   ordenar), orden "desc" (defecto) | "dado", formato. De 2 a 12 items; alto fijo n × 30. Los nombres ocupan
//   hasta el 45 % del ancho (los que no caben bajan a 12 px).
G.barras_h = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.items) && S.items.length >= 2 && S.items.length <= 12, "barras_h: 2 a 12 items");
  S.items.forEach((it) => H.assert(it && typeof it.nombre === "string" && typeof it.valor === "number", "cada item necesita nombre y valor numérico"));
  const items = S.orden === "dado" ? S.items.slice() : S.items.slice().sort((a, b) => b.valor - a.valor);
  const n = items.length, fila = 30, Hh = n * fila, W = ancho;
  const hi = GX.indice(S.destacar == null ? 0 : S.destacar, n);
  const txt = (it) => (it.valor_texto != null && it.valor_texto !== "" ? String(it.valor_texto) : GX.fmt(it.valor, S.formato));
  const maxN = Math.floor(W * 0.45) - 16;
  const fontN = items.map((it, i) => {
    const fn = H.encajar(it.nombre, [i === hi ? GX.SANS_D : GX.SANS, GX.SANS_S], maxN);
    H.assert(fn, "doc: «" + it.nombre + "» no cabe en la columna de nombres (" + maxN + " px): acórtalo");
    return fn;
  });
  const etiq = Math.ceil(Math.max(...items.map((it, i) => H.medir(it.nombre, fontN[i])))) + 16;
  const valW = Math.ceil(Math.max(...items.map((it, i) => H.medir(txt(it), i === hi ? GX.MONO_D : GX.MONO_B)))) + 10;
  const util = W - etiq - valW, max = Math.max(...items.map((it) => Math.abs(it.valor))) || 1;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  items.forEach((it, i) => {
    const d = i === hi, w = Math.max(2, (Math.abs(it.valor) / max) * util), yy = i * fila;
    GX.t(svg, 0, yy + 20, it.nombre, fontN[i], col.texto);
    GX.rect(svg, etiq, yy + 7, w, 16, d ? col.dest : col.base);
    GX.t(svg, etiq + w + 8, yy + 20, txt(it), d ? GX.MONO_D : GX.MONO_B, d ? (col.tinta || col.dest) : col.texto);
  });
  GX.linea(svg, etiq, 0, etiq, Hh, col.linea, { "stroke-width": 1 });
};

// divergente · cambios con signo; nombre encima de cada barra (cabe a media página). Tarjeta divergente.
//   items [{nombre, valor}], destacar (índice tras ordenar), orden "desc" (defecto: de mayor a menor) | "dado",
//   formato (signo siempre; sufijo). De 2 a 10 items; alto fijo n × 31.
G.divergente = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.items) && S.items.length >= 2 && S.items.length <= 10, "divergente admite de 2 a 10 items");
  S.items.forEach((it) => H.assert(it && typeof it.nombre === "string" && typeof it.valor === "number", "cada item necesita nombre y valor numérico"));
  const items = S.orden === "dado" ? S.items.slice() : S.items.slice().sort((a, b) => b.valor - a.valor);
  const n = items.length, fila = 31, Hh = n * fila, W = ancho;
  const hi = GX.indice(S.destacar == null ? 0 : S.destacar, n);
  const fmt = Object.assign({ signo: true }, S.formato || {}), lab = (it) => GX.fmt(it.valor, fmt);
  const vals = items.map((it) => it.valor), min = Math.min(0, ...vals), max = Math.max(0, ...vals);
  const labW = Math.ceil(Math.max(...items.map((it) => H.medir(lab(it), GX.MONO_B)))) + 8;
  const xL = min < 0 ? labW : 0, xR = W - (max > 0 ? labW : 0);
  const esc = (xR - xL) / ((max - min) || 1), x0 = xL + (-min) * esc;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  items.forEach((it, i) => {
    const d = i === hi, yy = i * fila, w = Math.abs(it.valor) * esc, x = it.valor < 0 ? x0 - w : x0;
    GX.t(svg, 0, yy + 11, it.nombre, d ? "800 13px Archivo, sans-serif" : "600 13px Archivo, sans-serif", d ? (col.tinta || col.dest) : col.texto);
    GX.rect(svg, x, yy + 15, Math.max(2, w), 11, d ? col.dest : col.base);
    GX.t(svg, it.valor < 0 ? x - 6 : x + w + 6, yy + 24, lab(it), GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": it.valor < 0 ? "end" : "start" });
  });
  GX.linea(svg, x0, 0, x0, Hh, col.linea);
};

// agrupadas · 2–3 series por categoría en barras horizontales desde cero (tarjeta agrupadas).
//   etiquetas[2–6], series[2–3] {nombre, valores (≥ 0, uno por categoría), destacar?} (≤ 1 destacada; sin ella,
//   la última), rotular "todas" (defecto) | "destacada" | null (sin cifras), referencia {valor, texto} (línea
//   vertical punteada con rótulo), formato. Leyenda de series en una fila arriba dentro del SVG; la destacada
//   en el acento, las otras en tinta (.85) y tinta atenuada. Los nombres ocupan hasta el 40 % del ancho (bajan
//   a 12 px o a dos líneas). Alto por defecto n × (k × 14 + 16) + 24 (+ 18 con referencia).
G.agrupadas = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.etiquetas) && S.etiquetas.length >= 2 && S.etiquetas.length <= 6, "agrupadas admite de 2 a 6 categorías");
  H.assert(Array.isArray(S.series) && S.series.length >= 2 && S.series.length <= 3, "agrupadas admite de 2 a 3 series");
  const n = S.etiquetas.length, k = S.series.length, W = ancho;
  S.series.forEach((s) => {
    H.assert(s && typeof s.nombre === "string" && s.nombre.trim() && Array.isArray(s.valores) && s.valores.length === n, "cada serie necesita nombre y " + n + " valores");
    s.valores.forEach((v) => H.assert(typeof v === "number" && isFinite(v) && v >= 0, "valores de «" + s.nombre + "»: números ≥ 0"));
  });
  H.assert(S.series.filter((s) => s.destacar).length <= 1, "solo una serie puede llevar destacar: true");
  let hi = S.series.findIndex((s) => s.destacar); if (hi < 0) hi = k - 1;
  const R = S.referencia || null;
  if (R) H.assert(typeof R.valor === "number" && isFinite(R.valor) && typeof R.texto === "string" && R.texto.trim(), "referencia necesita valor numérico y texto");
  const rot = S.rotular === undefined || S.rotular === "todas" ? "todas" : S.rotular === "destacada" ? "destacada" : null;
  let o = 0;
  const estilo = S.series.map((s, j) => (j === hi ? { fill: col.dest, op: 1 } : [{ fill: col.texto, op: 0.85 }, { fill: col.base, op: 1 }][Math.min(o++, 1)]));
  const f = (v) => GX.fmt(v, S.formato);
  // Leyenda: swatch 10×10 + nombre; pasa a una segunda fila si no cabe.
  const ley = []; let lx = 0, lf = 0;
  S.series.forEach((s, j) => {
    const w = 14 + H.medir(s.nombre, GX.MONO);
    if (lx > 0 && lx + w > W) { lx = 0; lf++; }
    ley.push({ j, x: lx, fila: lf }); lx += w + 16;
  });
  const yTop = 24 + lf * 16 + (R ? 18 : 0), grupoH = k * 14 - 2, def = yTop + n * (k * 14 + 16);
  const Hh = Math.max(alto || 0, def), filaH = (Hh - yTop) / n;
  // Nombres: 14 px, 12 px o dos líneas de 12 px partidas por el espacio que mejor equilibra.
  const maxN = Math.floor(W * 0.4);
  const ajustar = (s) => {
    const fn = H.encajar(s, [GX.SANS, GX.SANS_S], maxN);
    if (fn) return { lineas: [s], font: fn };
    const p = s.split(" "); let mejor = null;
    for (let i = 1; i < p.length; i++) {
      const a = p.slice(0, i).join(" "), b = p.slice(i).join(" ");
      if (H.encajar(a, [GX.SANS_S], maxN) && H.encajar(b, [GX.SANS_S], maxN)) {
        const dif = Math.abs(H.medir(a, GX.SANS_S) - H.medir(b, GX.SANS_S));
        if (!mejor || dif < mejor.dif) mejor = { lineas: [a, b], font: GX.SANS_S, dif };
      }
    }
    return mejor;
  };
  const nom = S.etiquetas.map((e) => { const a = ajustar(String(e)); H.assert(a, "doc: la categoría «" + e + "» no cabe en " + maxN + " px: acórtala"); return a; });
  const colIzq = Math.ceil(Math.max(...nom.map((a) => Math.max(...a.lineas.map((l) => H.medir(l, a.font)))))) + 12;
  const labW = rot ? Math.ceil(Math.max(...S.series.flatMap((s) => s.valores.map((v) => H.medir(f(v), GX.MONO_B))))) + 8 : 0;
  const x0 = colIzq, x1 = W - labW, max = Math.max(...S.series.flatMap((s) => s.valores), R ? R.valor : 0) || 1;
  const sx = (v) => x0 + (v / max) * (x1 - x0);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  ley.forEach((it) => {
    const y = 3 + it.fila * 16;
    GX.rect(svg, it.x, y, 10, 10, estilo[it.j].fill, { "fill-opacity": estilo[it.j].op });
    GX.t(svg, it.x + 14, y + 9, S.series[it.j].nombre, GX.MONO, col.texto);
  });
  if (R) {
    const x = sx(R.valor), txt = R.texto.trim() + " · " + f(R.valor), cabe = x + 6 + H.medir(txt, GX.MONO_B) <= W;
    GX.linea(svg, x, yTop - 4, x, Hh, col.texto, { "stroke-width": 1, "stroke-dasharray": "4 4" });
    GX.t(svg, cabe ? x + 6 : x - 6, yTop - 7, txt, GX.MONO_B, col.texto, { "text-anchor": cabe ? "start" : "end" });
  }
  S.etiquetas.forEach((e, i) => {
    const top = yTop + i * filaH + (filaH - grupoH) / 2, cy = top + grupoH / 2, a = nom[i];
    if (a.lineas.length === 1) GX.t(svg, 0, cy + 5, a.lineas[0], a.font, col.texto);
    else a.lineas.forEach((l, q) => GX.t(svg, 0, cy - 2 + q * 13, l, a.font, col.texto));
    S.series.forEach((s, j) => {
      const y = top + j * 14, v = s.valores[i], w = Math.max(2, sx(v) - x0), d = j === hi;
      GX.rect(svg, x0, y, w, 12, estilo[j].fill, { "fill-opacity": estilo[j].op });
      if (rot === "todas" || (rot === "destacada" && d)) GX.t(svg, x0 + w + 6, y + 10, f(v), GX.MONO_B, d ? (col.tinta || col.dest) : col.texto);
    });
  });
  GX.linea(svg, x0, yTop, x0, Hh, col.linea, { "stroke-width": 1 });
};

// bullet · valor contra meta o referencia, una fila por item (tarjeta bullet).
//   items[1–6] {nombre, valor (≥ 0), meta?}, meta (común), texto_meta, maximo (tope; null = el mayor entre
//   valores y metas), destacar (índice), formato. Fila de 44 px: nombre (+ meta propia a la derecha) y valor al
//   final de la línea; pista hasta el tope, barra de 12 px hasta la meta, exceso rayado y marcador de meta.
//   Con meta común, «texto_meta · valor» al pie. Alto por defecto n × 44 + 20.
G.bullet = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.items) && S.items.length >= 1 && S.items.length <= 6, "bullet admite de 1 a 6 items");
  const items = S.items.map((it) => {
    H.assert(it && typeof it.nombre === "string" && typeof it.valor === "number" && it.valor >= 0, "cada item necesita nombre y valor numérico ≥ 0");
    const meta = typeof it.meta === "number" ? it.meta : S.meta;
    H.assert(typeof meta === "number" && meta > 0, "«" + it.nombre + "» no tiene meta: usa `meta` común o `meta` por item");
    return { nombre: it.nombre, valor: it.valor, meta };
  });
  const n = items.length, hi = S.destacar == null ? -1 : GX.indice(S.destacar, n);
  const maxDato = Math.max(...items.flatMap((it) => [it.valor, it.meta]));
  const max = S.maximo == null ? maxDato : S.maximo;
  H.assert(max >= maxDato, "maximo (" + max + ") es menor que algún valor o meta (" + maxDato + ")");
  const metaComun = items.every((it) => it.meta === items[0].meta), txtMeta = (S.texto_meta || "meta").trim();
  const f = (v) => GX.fmt(v, S.formato);
  const W = ancho, fila = 44, Hh = Math.max(alto || 0, n * fila + 20), filaH = (Hh - 20) / n;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const sx = (v) => (v / max) * W;
  // Rayado (del color del fondo) sobre el tramo que excede la meta.
  const pid = "bl" + Math.random().toString(36).slice(2, 7);
  const pat = H.svgEl("pattern", { id: pid, width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, H.svgEl("defs", {}, svg));
  H.svgEl("rect", { width: 3, height: 6, fill: col.sobre, "fill-opacity": 0.75 }, pat);
  items.forEach((it, i) => {
    const d = i === hi, top = i * filaH + (filaH - fila) / 2, yN = top + 14, yP = top + 20;
    const vTxt = f(it.valor), fontV = d ? GX.MONO_D : GX.MONO_B;
    let xDer = W - H.medir(vTxt, fontV) - 10;
    if (!metaComun) {
      const m = txtMeta + " " + f(it.meta) + " ·";
      GX.t(svg, xDer, yN, m, GX.MONO, col.texto, { "text-anchor": "end" });
      xDer -= H.medir(m, GX.MONO) + 8;
    }
    const fontN = H.encajar(it.nombre, [d ? GX.SANS_D : GX.SANS, GX.SANS_S], xDer - 8);
    H.assert(fontN, "«" + it.nombre + "»: nombre, meta y valor no caben en una línea");
    GX.t(svg, 0, yN, it.nombre, fontN, col.texto);
    GX.t(svg, W, yN, vTxt, fontV, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": "end" });
    GX.rect(svg, 0, yP, W, 16, col.suave);
    const xv = sx(it.valor), xm = sx(it.meta), fill = d ? col.dest : col.base;
    GX.rect(svg, 0, yP + 2, Math.max(2, Math.min(xv, xm)), 12, fill);
    if (xv > xm) { GX.rect(svg, xm, yP + 2, xv - xm, 12, fill); GX.rect(svg, xm, yP + 2, xv - xm, 12, "url(#" + pid + ")"); }
    GX.rect(svg, Math.min(W - 2, xm - 1), yP, 2, 16, col.texto);
  });
  if (metaComun) {
    const xm = sx(items[0].meta), t = txtMeta + " · " + f(items[0].meta), w = H.medir(t, GX.MONO);
    const anc = xm + w / 2 > W ? "end" : xm - w / 2 < 0 ? "start" : "middle";
    GX.t(svg, anc === "end" ? W : anc === "start" ? 0 : xm, Hh - 4, t, GX.MONO, col.texto, { "text-anchor": anc });
  }
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
