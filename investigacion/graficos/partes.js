// Partes · el reparto de un todo o de una cadena: dona, treemap, hemiciclo y embudo.
// Mismo contrato que las plantillas de tarjeta (templates/graficos/dona.html, treemap.html, hemiciclo.html,
// embudo.html) y la misma aritmética compartida de H (squarify, asientos, mayoria, etiquetaEmbudo): el documento
// y la tarjeta calculan el mismo número. Un solo acento (col.dest) para la parte que importa.

// dona · reparto del todo en 2–5 partes: aro de arcos en SVG, cifra en el centro y lista con swatch.
//   partes[2–5] {nombre, valor ≥ 0}, destacar (índice), centro {valor, texto} (opcional: por defecto la destacada),
//   formato (decimales de los %). Aro de radio 90 y grosor 28 a la izquierda con la lista a la derecha; a menos de
//   400 px el aro va centrado y la lista debajo (+18·n). Alto 200.
G.dona = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.partes) && S.partes.length >= 2 && S.partes.length <= 5, "dona admite de 2 a 5 partes");
  S.partes.forEach((p) => H.assert(p && p.nombre && typeof p.valor === "number" && p.valor >= 0, "cada parte necesita nombre y valor ≥ 0"));
  const total = S.partes.reduce((s, p) => s + p.valor, 0);
  H.assert(total > 0, "la suma de las partes es 0");
  const n = S.partes.length, hi = GX.indice(S.destacar || 0, n), dec = (S.formato && S.formato.decimales) || 0;
  const W = ancho, abajo = W < 400, Hh = 200 + (abajo ? n * 18 : 0), R = 90, r = R - 28;
  const cx = abajo ? W / 2 : 100, cy = 100;
  // El resto de las partes en la tinta con opacidades decrecientes (sin pisar el acento).
  const OP = [0.85, 0.6, 0.4, 0.25];
  let k = 0;
  const estilo = S.partes.map((_, i) => (i === hi ? { fill: col.dest } : { fill: col.texto, "fill-opacity": OP[Math.min(k++, OP.length - 1)] }));
  const svg = GX.lienzo(el, W, Hh, S.aria);
  // Arcos desde las 12 en sentido horario; una parte del 100 % es un anillo entero.
  const pt = (rad, a) => (cx + rad * Math.sin(a)).toFixed(2) + " " + (cy - rad * Math.cos(a)).toFixed(2);
  let a0 = 0;
  S.partes.forEach((p, i) => {
    const fr = p.valor / total;
    if (fr <= 0) return;
    const a1 = a0 + fr * 2 * Math.PI;
    if (fr >= 0.9999) H.svgEl("circle", { cx, cy, r: (R + r) / 2, fill: "none", stroke: estilo[i].fill, "stroke-width": R - r, "stroke-opacity": estilo[i]["fill-opacity"] }, svg);
    else {
      const grande = fr > 0.5 ? 1 : 0;
      const d = "M" + pt(R, a0) + " A" + R + " " + R + " 0 " + grande + " 1 " + pt(R, a1) + " L" + pt(r, a1) + " A" + r + " " + r + " 0 " + grande + " 0 " + pt(r, a0) + " Z";
      H.svgEl("path", Object.assign({ d, stroke: col.sobre, "stroke-width": 1 }, estilo[i]), svg);
    }
    a0 = a1;
  });
  // Centro: la cifra en serif y el texto en mono, partido por palabras en la cuerda del hueco (≤ 2 líneas).
  const c = S.centro || { valor: Math.round((S.partes[hi].valor / total) * 100), texto: S.partes[hi].nombre };
  const vTxt = typeof c.valor === "number" ? H.pct(c.valor) : String(c.valor);
  const cuerda = (dy) => (r > dy ? 2 * Math.sqrt(r * r - dy * dy) - 8 : 0);
  const lineas = [];
  if (c.texto && String(c.texto).trim()) {
    const pal = String(c.texto).trim().split(/\s+/);
    let linea = "";
    for (const w of pal) {
      const prueba = linea ? linea + " " + w : w, ancho = cuerda(lineas.length === 0 ? 18 : 32);
      if (H.medir(prueba, GX.MONO) <= ancho) linea = prueba;
      else { H.assert(linea && lineas.length < 1, "doc: el texto del centro de la dona no cabe en el hueco: acórtalo"); lineas.push(linea); linea = w; }
    }
    H.assert(H.medir(linea, GX.MONO) <= cuerda(lineas.length === 0 ? 18 : 32), "doc: el texto del centro de la dona no cabe en el hueco: acórtalo");
    lineas.push(linea);
  }
  GX.t(svg, cx, lineas.length ? cy - 6 : cy + 11, vTxt, GX.serif(32), col.texto, { "text-anchor": "middle" });
  lineas.forEach((l, i) => GX.t(svg, cx, cy + 14 + i * 14, l, GX.MONO, col.texto, { "text-anchor": "middle" }));
  // Lista: swatch, nombre y %; la destacada en negrita y con el % en el acento.
  const pctTxt = S.partes.map((p) => H.pct((p.valor / total) * 100, dec));
  const wP = Math.ceil(Math.max(...pctTxt.map((t) => H.medir(t, GX.MONO_B)))) + 8;
  const SANS_HI = "800 12px Archivo, sans-serif";
  const item = (i, x, yBase, ySw, maxW) => {
    const p = S.partes[i], d = i === hi;
    const fn = H.encajar(p.nombre, d ? [GX.SANS_D, SANS_HI] : [GX.SANS, GX.SANS_S], maxW);
    H.assert(fn, "doc: el nombre «" + p.nombre + "» no cabe en la lista de la dona: acórtalo");
    GX.rect(svg, x, ySw, 10, 10, estilo[i].fill, estilo[i]["fill-opacity"] == null ? {} : { "fill-opacity": estilo[i]["fill-opacity"] });
    GX.t(svg, x + 16, yBase, p.nombre, fn, col.texto);
    GX.t(svg, W, yBase - 1, pctTxt[i], GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": "end" });
  };
  if (!abajo) {
    const x = 220, filaH = Math.min(30, 180 / n), y0 = cy - (n * filaH) / 2;
    S.partes.forEach((_, i) => { const yy = y0 + i * filaH + filaH / 2; item(i, x, yy + 5, yy - 5, W - x - 16 - wP); });
  } else {
    S.partes.forEach((_, i) => { const yy = 200 + i * 18; item(i, 0, yy + 13, yy + 4, W - 16 - wP); });
  }
};

// treemap · reparto del todo con más de 5 partes: área = proporción (H.squarify, compartido con la tarjeta).
//   partes[3–12] {nombre, valor > 0}, destacar (nombre, o índice tras ordenar de mayor a menor), minimo_rotulo
//   (% bajo el cual las partes se agrupan en «Todo lo demás» si son 2 o más; además se agrupan, una a una, las
//   chicas que no caben con nombre), formato. Rect destacado en col.dest; el resto en la rampa de mayor a menor
//   («Todo lo demás» en el tono más claro). Alto 300. doc: a media página (ancho < 400) son «chicas» las partes < 10 %.
G.treemap = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.partes) && S.partes.length >= 3 && S.partes.length <= 12, "treemap admite de 3 a 12 partes");
  S.partes.forEach((p) => H.assert(p && typeof p.nombre === "string" && typeof p.valor === "number" && p.valor > 0, "cada parte necesita nombre y valor > 0"));
  const total = S.partes.reduce((s, p) => s + p.valor, 0);
  const minimo = S.minimo_rotulo == null ? 2 : S.minimo_rotulo;
  const ordenadas = S.partes.slice().sort((a, b) => b.valor - a.valor);
  const nombreHi = typeof S.destacar === "string" ? S.destacar : ordenadas[GX.indice(S.destacar == null ? 0 : S.destacar, ordenadas.length)].nombre;
  H.assert(ordenadas.some((p) => p.nombre === nombreHi), "destacar: «" + S.destacar + "» no es una de las partes");
  const W = ancho, Hh = alto || 300, G2 = 2, PAD = 8, FN = [14, 12];
  const fuente = (px, peso) => peso + " " + px + "px Archivo, sans-serif";
  // Rótulo de un rect, de más a menos holgado: nombre en una línea y % debajo · nombre en dos líneas y % debajo ·
  // nombre y % en una línea (rect bajo y ancho). null si nada cabe.
  const rotulo = (r, p, esHi) => {
    const w = r.w - G2 - 2 * PAD, h = r.h - G2, pc = (p.valor / total) * 100, tP = H.pct(pc, pc < 10 ? 1 : 0);
    const wP = H.medir(tP, GX.MONO_B), pal = p.nombre.split(/\s+/);
    if (wP > w) return null;
    for (const peso of esHi ? [800, 600] : [600]) {   // la destacada cede la negrita antes que el nombre (ya va en el acento)
      const mide = (t, s) => H.medir(t, fuente(s, peso));
      const px = FN.find((s) => mide(p.nombre, s) <= w);
      if (px && h >= px + 36) return { px, peso, tP, lineas: [p.nombre] };
      for (const s of FN) {
        let mejor = null;
        for (let q = 1; q < pal.length; q++) {
          const ls = [pal.slice(0, q).join(" "), pal.slice(q).join(" ")], a = Math.max(...ls.map((l) => mide(l, s)));
          if (a <= w && (!mejor || a < mejor.a)) mejor = { ls, a };
        }
        if (mejor && h >= Math.round(s * 2.15) + 36) return { px: s, peso, tP, lineas: mejor.ls };
      }
      const px1 = FN.find((s) => mide(p.nombre, s) + 8 + wP <= w);
      if (px1 && h >= px1 + 12) return { px: px1, peso, tP, lineas: [p.nombre], enLinea: true };
    }
    return null;
  };
  // Agrupa: primero las de menos de `minimo` % (si son 2 o más); luego, una a una, las chicas que no caben con nombre.
  let sueltas = ordenadas.slice(), grupo = [];
  const chicas = sueltas.filter((p) => (p.valor / total) * 100 < minimo && p.nombre !== nombreHi);
  if (chicas.length >= 2) { grupo = chicas; sueltas = sueltas.filter((p) => !chicas.includes(p)); }
  const armar = () => (grupo.length ? sueltas.concat([{ nombre: "Todo lo demás", valor: grupo.reduce((s, p) => s + p.valor, 0), resto: true }]) : sueltas.slice()).sort((a, b) => b.valor - a.valor);
  // doc: con un cuarto del área de la tarjeta, se agrupan (si no caben con nombre) las partes < 10 %, no < 5 %.
  const umbral = Math.max(10, minimo);
  const chica = (p) => (p.valor / total) * 100 < umbral;
  let partes, rects, falla;
  for (let vuelta = 0; vuelta < 12; vuelta++) {
    partes = armar(); rects = H.squarify(partes, total, W, Hh);
    falla = rects.filter((r) => !rotulo(r, partes[r.i], partes[r.i].nombre === nombreHi)).map((r) => partes[r.i]);
    if (!falla.length) break;
    let movibles = falla.filter((p) => !p.resto && p.nombre !== nombreHi && chica(p));
    // Si lo que no cabe es «Todo lo demás» o una parte que no se agrupa (la destacada, una mediana), se agrupa la
    // suelta chica más pequeña para recomponer el reparto (mientras queden > 3 sueltas).
    if (!movibles.length) movibles = sueltas.length > 3 ? sueltas.filter((p) => p.nombre !== nombreHi && chica(p)) : [];
    if (!movibles.length) break;
    const menor = movibles.reduce((a, b) => (b.valor < a.valor ? b : a));
    grupo.push(menor); sueltas = sueltas.filter((p) => p !== menor);
  }
  H.assert(!falla.length, "treemap: no caben con nombre " + falla.map((p) => "«" + p.nombre + "»").join(", ") + ": acorta los nombres o usa barras-h");
  H.assert(partes.length >= 3, "treemap: tras agrupar quedan " + partes.length + " rectángulos (< 3): usa dona o barras-h");
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const hiIdx = partes.findIndex((p) => p.nombre === nombreHi);
  const rampa = GX.rampa(Math.max(2, partes.length - (hiIdx >= 0 ? 1 : 0)), col).reverse();
  let k = 0;
  const colorDe = partes.map((p, i) => (i === hiIdx ? col.dest : p.resto ? rampa[rampa.length - 1] : rampa[Math.min(k++, rampa.length - 1)]));
  for (const r of rects) {
    const p = partes[r.i], c = colorDe[r.i], tc = GX.textoSobre(c, col), lab = rotulo(r, p, r.i === hiIdx);
    const x = r.x + G2 / 2, y = r.y + G2 / 2, est = fuente(lab.px, lab.peso);
    GX.rect(svg, x, y, r.w - G2, r.h - G2, c);
    if (lab.enLinea) {
      const yN = y + Math.min(PAD + lab.px, (r.h - G2) / 2 + lab.px * 0.36);
      GX.t(svg, x + PAD, yN, p.nombre, est, tc);
      GX.t(svg, x + PAD + H.medir(p.nombre, est) + 8, yN, lab.tP, GX.MONO_B, tc);
    } else {
      const lh = Math.round(lab.px * 1.15);
      lab.lineas.forEach((l, q) => GX.t(svg, x + PAD, y + PAD + lab.px + q * lh, l, est, tc));
      GX.t(svg, x + PAD, y + PAD + lab.px + (lab.lineas.length - 1) * lh + 18, lab.tP, GX.MONO_B, tc);
    }
  }
  if (grupo.length) GX.anotar(el, "«Todo lo demás» agrupa " + (grupo.length <= 4 ? grupo.map((p) => p.nombre).join(", ") : grupo.length + " partes") + ".");
};

// hemiciclo · curules por bloque en semicírculo con la línea de mayoría (H.asientos y H.mayoria, compartidos).
//   total (10–300), bloques[2–8] {nombre, curules} de izquierda a derecha (suman total), mayoria "simple"|
//   "calificada"|null, destacar (índice), formato. Columna de bloques a la derecha si ancho ≥ 480; si no, leyenda
//   debajo (+18 por fila). «N · mayoría simple» en el hueco si cabe, si no en el extremo de la línea.
//   Alto: ancho × 0.52 + 40. doc: a media página (ancho < 400) caben ≤ 160 curules.
G.hemiciclo = (el, S, { ancho, alto, col }) => {
  H.assert(Number.isInteger(S.total) && S.total >= 10 && S.total <= 300, "total debe ser un entero entre 10 y 300");
  H.assert(Array.isArray(S.bloques) && S.bloques.length >= 2 && S.bloques.length <= 8, "hemiciclo admite de 2 a 8 bloques");
  S.bloques.forEach((b) => H.assert(b && typeof b.nombre === "string" && b.nombre.trim() && Number.isInteger(b.curules) && b.curules >= 0, "cada bloque necesita nombre y curules entero ≥ 0"));
  const suma = S.bloques.reduce((s, b) => s + b.curules, 0);
  H.assert(suma === S.total, "los bloques suman " + suma + ", no total (" + S.total + "): añade un bloque «Vacantes» o corrige las cifras");
  H.assert(S.mayoria == null || S.mayoria === "simple" || S.mayoria === "calificada", "mayoria debe ser \"simple\", \"calificada\" o null");
  const W = ancho, n = S.bloques.length, hi = GX.indice(S.destacar, n), f = (v) => GX.fmt(v, S.formato);
  H.assert(W >= 400 || S.total <= 160, "doc: a media página caben ≤ 160 curules");
  const columna = W >= 480, Ha = alto || Math.round(W * 0.52) + 40;
  const R = Math.min(Math.round(W * 0.38), Ha - 40, columna ? Math.floor((W - 130) / 2) : Infinity), r0 = Math.round(0.42 * R);
  const cx = columna ? R + 6 : W / 2, cy = Ha - 8;
  const arco = H.asientos(S.total, R, r0, cx, cy, 30, 7);
  H.assert(arco, "no caben " + S.total + " curules en el arco: dale más alto a la figura o toda la columna");
  const SANS_HI = "800 12px Archivo, sans-serif";
  const rampa = GX.rampa(Math.max(2, n - (hi >= 0 ? 1 : 0)), col).reverse();
  let k = 0;
  const colores = S.bloques.map((_, i) => (i === hi ? col.dest : rampa[Math.min(k++, rampa.length - 1)]));
  // Sin columna: leyenda en filas de 18 px bajo el arco (el total como primer item).
  let ley = [], Hh = Ha;
  if (!columna) {
    const tot = f(S.total) + " curules";
    ley = [{ txt: tot, w: H.medir(tot, GX.MONO_B) }].concat(S.bloques.map((b, i) => {
      const fn = i === hi ? SANS_HI : GX.SANS_S, val = f(b.curules);
      return { i, fn, val, w: 14 + H.medir(b.nombre, fn) + 5 + H.medir(val, GX.MONO_B) };
    }));
    let x = 0, fila = 0;
    ley.forEach((it) => { if (x > 0 && x + it.w > W) { x = 0; fila++; } it.x = x; it.fila = fila; x += it.w + 14; });
    Hh = Ha + 6 + (fila + 1) * 18;
  }
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const s = arco.s, rPunto = 0.36 * s;
  let pos = 0;
  S.bloques.forEach((b, i) => { for (let j = 0; j < b.curules; j++) { const a = arco.asientos[pos++]; H.svgEl("circle", { cx: a.x.toFixed(1), cy: a.y.toFixed(1), r: rPunto.toFixed(2), fill: colores[i] }, svg); } });
  // Mayoría: marcador radial entre el asiento m−1 y m; el rótulo en el hueco si cabe, si no en el extremo de la línea.
  if (S.mayoria) {
    const m = H.mayoria(S.total, S.mayoria), A = arco.asientos;
    const th = m < A.length ? (A[m - 1].th + A[m].th) / 2 : A[A.length - 1].th;
    const ra = r0 - s / 2, rb = R + 0.7 * s;
    GX.linea(svg, cx + ra * Math.cos(th), cy - ra * Math.sin(th), cx + rb * Math.cos(th), cy - rb * Math.sin(th), col.texto, { "stroke-width": 1.5, "stroke-dasharray": "4 4" });
    const etiq = f(m) + " · mayoría " + S.mayoria, wE = H.medir(etiq, GX.MONO_B);
    const rIn = r0 - 1.2 * rPunto, dy = 18;
    const cuerda = rIn > dy ? 2 * Math.sqrt(rIn * rIn - dy * dy) - 8 : 0;
    if (wE <= cuerda) GX.t(svg, cx, cy - 6, etiq, GX.MONO_B, col.texto, { "text-anchor": "middle" });
    else {
      // Encima del arco (nunca sobre los asientos), a la altura horizontal del extremo de la línea y dentro del arco.
      const xe = cx + rb * Math.cos(th), lo = Math.max(0, cx - R) + wE / 2, hi2 = Math.min(W, cx + R) - wE / 2;
      const x = lo > hi2 ? cx : Math.max(lo, Math.min(hi2, xe)), y = Math.max(12, cy - R - rPunto - 6);
      GX.t(svg, x, y, etiq, GX.MONO_B, col.texto, { "text-anchor": "middle" });
    }
  }
  if (columna) {
    const xCol = cx + R + 16, xNom = xCol + 16;
    GX.t(svg, xCol, 14, f(S.total) + " curules", GX.MONO_B, col.texto);
    const filaH = Math.min(28, (Hh - 30) / n);
    S.bloques.forEach((b, i) => {
      const d = i === hi, yy = 30 + filaH * i + filaH / 2, val = f(b.curules), wV = H.medir(val, GX.MONO_B);
      const fn = H.encajar(b.nombre, d ? [GX.SANS_D, SANS_HI] : [GX.SANS, GX.SANS_S], W - xNom - wV - 8);
      H.assert(fn, "el nombre «" + b.nombre + "» no cabe en la columna: acórtalo");
      H.svgEl("circle", { cx: xCol + 5, cy: yy, r: 5, fill: colores[i] }, svg);
      GX.t(svg, xNom, yy + 5, b.nombre, fn, col.texto);
      GX.t(svg, W, yy + 4, val, GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": "end" });
    });
  } else {
    ley.forEach((it) => {
      const yy = Ha + 6 + it.fila * 18;
      if (it.i == null) { GX.t(svg, it.x, yy + 13, it.txt, GX.MONO_B, col.texto); return; }
      const d = it.i === hi;
      H.svgEl("circle", { cx: it.x + 5, cy: yy + 9, r: 5, fill: colores[it.i] }, svg);
      GX.t(svg, it.x + 14, yy + 13, S.bloques[it.i].nombre, it.fn, col.texto);
      GX.t(svg, it.x + 14 + H.medir(S.bloques[it.i].nombre, it.fn) + 5, yy + 13, it.val, GX.MONO_B, d ? (col.tinta || col.dest) : col.texto);
    });
  }
};

// embudo · cadena de atrición: cuántos llegan de una etapa a la siguiente (H.etiquetaEmbudo, compartido).
//   etapas[2–6] {nombre, valor} (no crecientes), porcentaje "inicio"|"anterior"|"ninguno" (siempre calculado aquí),
//   misma_cohorte (boolean obligatorio; false añade la nota), formato. Filas de 44 px: nombre arriba a la izquierda,
//   barra proporcional a la primera etapa (col.base; la última en col.dest) con el valor dentro o fuera, y la
//   etiqueta «N de cada 100» a la derecha (sube a la línea del nombre si chocaría con el valor). Alto: 44·n.
G.embudo = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.etapas) && S.etapas.length >= 2 && S.etapas.length <= 6, "embudo admite de 2 a 6 etapas");
  S.etapas.forEach((e, i) => {
    H.assert(e && typeof e.nombre === "string" && typeof e.valor === "number" && e.valor >= 0, "cada etapa necesita nombre y valor numérico ≥ 0");
    if (i) H.assert(e.valor <= S.etapas[i - 1].valor, "embudo: «" + e.nombre + "» supera a la etapa anterior (las etapas no pueden crecer)");
  });
  H.assert(S.etapas[0].valor > 0, "la primera etapa debe ser > 0");
  H.assert(typeof S.misma_cohorte === "boolean", "misma_cohorte debe ser true o false (¿las etapas siguen a los mismos casos?)");
  const modo = S.porcentaje || "inicio";
  H.assert(["inicio", "anterior", "ninguno"].includes(modo), "porcentaje: inicio | anterior | ninguno");
  const E = S.etapas, n = E.length, base = E[0].valor, W = ancho, fila = 44, Hh = n * fila, barH = 16;
  const f = (v) => GX.fmt(v, S.formato), SANS_HI = "800 12px Archivo, sans-serif";
  const svg = GX.lienzo(el, W, Hh, S.aria);
  E.forEach((e, i) => {
    const ult = i === n - 1, top = i * fila, yB = top + 20, yT = yB + barH / 2 + 4;
    const w = Math.max(4, (e.valor / base) * W);
    GX.rect(svg, 0, yB, w, barH, ult ? col.dest : col.base);
    const val = f(e.valor), wV = H.medir(val, GX.MONO_B), dentro = wV + 12 <= w;
    GX.t(svg, dentro ? w - 6 : w + 6, yT, val, GX.MONO_B, dentro && ult ? GX.textoSobre(col.dest, col) : col.texto, dentro ? { "text-anchor": "end" } : {});
    const etiq = H.etiquetaEmbudo(E, i, modo), wE = etiq ? H.medir(etiq, GX.MONO) : 0;
    const enBarra = !etiq || (dentro ? w : w + 6 + wV) + 10 <= W - wE;
    let fn = ult ? GX.SANS_D : GX.SANS;
    if (!enBarra) {
      fn = H.encajar(e.nombre, [fn, ult ? SANS_HI : GX.SANS_S], W - wE - 10);
      H.assert(fn, "doc: la etapa «" + e.nombre + "» y su etiqueta no caben en " + W + " px: acorta el nombre");
    }
    GX.t(svg, 0, top + 13, e.nombre, fn, col.texto);
    if (etiq) GX.t(svg, W, enBarra ? yT : top + 13, etiq, GX.MONO, col.tinta || col.dest, { "text-anchor": "end" });
  });
  if (!S.misma_cohorte) GX.anotar(el, "Etapas del mismo periodo, no de los mismos casos.");
};
