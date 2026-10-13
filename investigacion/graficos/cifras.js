// cifra · waffle · pictograma: el número héroe y las proporciones «de 100» (brief 4d) y «K de N» (brief 5e).
//   En la tarjeta son HTML/CSS; en el documento van en UN svg (GX.lienzo) con los mismos campos y límites
//   que templates/graficos/{cifra,waffle,pictograma}.html. El número grande va en col.tinta || col.dest (un
//   solo acento); lo demás en col.texto; las marcas atenuadas en col.base. Piso 12 px.
//   Alturas: cifra 120 (170 con comparación) · waffle 10·celda + 27 · pictograma filas·celda + huecos; si la
//   columna de texto necesita más (frase o leyenda envueltas a media página), la figura crece.
const GXC = (() => {
  // Parte un texto en líneas que caben en maxW (palabras enteras; una palabra más larga que maxW va sola).
  const envolver = (str, font, maxW) => {
    const out = [];
    let linea = "";
    for (const p of String(str == null ? "" : str).trim().split(/\s+/).filter(Boolean)) {
      const prueba = linea ? linea + " " + p : p;
      if (!linea || H.medir(prueba, font) <= maxW) linea = prueba;
      else { out.push(linea); linea = p; }
    }
    if (linea) out.push(linea);
    return out;
  };
  // Cuerpo serif más grande de la lista en el que `str` cabe en maxW (H.encajar); si ninguno, el menor.
  const serifQueCabe = (str, pxs, maxW) => {
    const fn = H.encajar(str, pxs.map(GX.serif), maxW);
    return fn ? pxs[pxs.map(GX.serif).indexOf(fn)] : pxs[pxs.length - 1];
  };
  // Columna de texto alineada abajo: cifra grande (serif 40→34→28), frase SANS envuelta y leyenda MONO con
  // muestra de 10 px. o = { num, numFill, texto, leyenda: [{ texto, muestra(svg, x, y, lado) }] }.
  // Sin svg solo mide: devuelve el alto que necesita.
  const columna = (svg, x, maxW, abajo, o, col) => {
    const px = serifQueCabe(o.num, [40, 34, 28], maxW);
    const lineas = envolver(o.texto, GX.SANS, maxW);
    const ley = (o.leyenda || []).map((it) => ({ it, lineas: envolver(it.texto, GX.MONO, maxW - 16) }));
    const hNum = Math.round(px * 0.85), hTexto = lineas.length * 18, hLey = ley.reduce((s, l) => s + Math.max(1, l.lineas.length) * 16, 0);
    const total = hNum + 8 + hTexto + (ley.length ? 10 + hLey : 0);
    if (!svg) return total;
    let y = abajo - total;
    GX.t(svg, x, y + Math.round(px * 0.8), o.num, GX.serif(px), o.numFill);
    y += hNum + 8;
    lineas.forEach((s, i) => GX.t(svg, x, y + 14 + i * 18, s, GX.SANS, col.texto));
    y += hTexto + (ley.length ? 10 : 0);
    for (const l of ley) {
      l.it.muestra(svg, x, y + 3, 10);
      l.lineas.forEach((s, i) => GX.t(svg, x + 16, y + 13 + i * 16, s, GX.MONO, col.texto));
      y += Math.max(1, l.lineas.length) * 16;
    }
    return total;
  };
  // Silueta de la tarjeta (::before cabeza 42 % · ::after cuerpo 64 %) en una caja de 100 × 145.
  const PERSONA = "M50 0a21 21 0 1 1 0 42a21 21 0 1 1 0-42zM0 141v-53a50 35 0 0 1 100 0v53a4 4 0 0 1-4 4H4a4 4 0 0 1-4-4z";
  // Una unidad del pictograma: punto (círculo), cuadro (esquinas suaves) o persona (1 × 1.45), de `lado` px.
  const forma = (svg, x, y, lado, tipo, fill) => {
    if (tipo === "cuadro") return GX.rect(svg, x, y, lado, lado, fill, { rx: Math.max(1, lado / 8) });
    if (tipo === "persona") return H.svgEl("path", { d: PERSONA, fill, transform: "translate(" + x + " " + y + ") scale(" + (lado / 100).toFixed(4) + ")" }, svg);
    return H.svgEl("circle", { cx: x + lado / 2, cy: y + lado / 2, r: lado / 2, fill }, svg);
  };
  return { envolver, serifQueCabe, columna, forma };
})();

// cifra · número héroe sin gráfico (ancla del T1 o cierre).
//   cifra {valor, texto}, contexto (≤ 60), tendencia "sube"|"baja"|null (flecha de 8 px en el acento),
//   comparacion {etiqueta, valor, etiqueta_hero} (dos barras de 12 px proporcionales al mayor; la del héroe en
//   col.dest, la otra en col.base), formato. Alto 120 · 170 con comparación.
G.cifra = (el, S, { ancho, alto, col }) => {
  H.assert(S.cifra && typeof S.cifra.valor === "number", "cifra.valor debe ser un número");
  H.assert(typeof S.cifra.texto === "string" && S.cifra.texto.trim(), "cifra.texto vacío");
  H.assert(!S.contexto || S.contexto.length <= 60, "contexto > 60 caracteres");
  const C = S.comparacion;
  if (C) H.assert(typeof C.valor === "number" && C.etiqueta, "comparacion necesita etiqueta y valor");
  const W = ancho, acento = col.tinta || col.dest, f = (v) => GX.fmt(v, S.formato);
  const numTxt = f(S.cifra.valor), px = GXC.serifQueCabe(numTxt, [48, 40, 32], W);
  const lineas = GXC.envolver(S.cifra.texto, GX.SANS, W);
  const hayCtx = !!(S.contexto || S.tendencia);
  let filas = [];
  if (C) {
    const max = Math.max(Math.abs(S.cifra.valor), Math.abs(C.valor)) || 1;
    filas = [{ lab: String(C.etiqueta).toUpperCase(), v: C.valor, fill: col.base },
             { lab: String(C.etiqueta_hero || "ahora").toUpperCase(), v: S.cifra.valor, fill: col.dest, hero: true }];
    filas.forEach((r) => { r.val = f(r.v); r.p = Math.abs(r.v) / max; });
  }
  // Fila de contexto 30 (la caja del serif sube ~1 em sobre su base: P5) · número px·0.85 · frase 18 por línea ·
  // comparación 12 + 2 filas de 22; el bloque se centra en vertical.
  const hCtx = hayCtx ? 30 : 0, hNum = Math.round(px * 0.85), hTxt = lineas.length * 18, hComp = C ? 12 + filas.length * 22 : 0;
  const contenido = hCtx + hNum + 10 + hTxt + hComp;
  const Hh = Math.max(alto || (C ? 170 : 120), contenido);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  let y = Math.floor((Hh - contenido) / 2);
  if (hayCtx) {
    let x = 0;
    if (S.tendencia) {
      H.svgEl("path", { d: S.tendencia === "baja" ? "M0 5l4 8 4-8z" : "M0 13l4-8 4 8z", fill: col.dest, transform: "translate(0 " + y + ")" }, svg);
      x = 14;
    }
    if (S.contexto) GX.t(svg, x, y + 13, S.contexto, GX.MONO, col.texto);
    y += hCtx;
  }
  GX.t(svg, 0, y + Math.round(px * 0.8), numTxt, GX.serif(px), acento);
  y += hNum + 10;
  lineas.forEach((s, i) => GX.t(svg, 0, y + 14 + i * 18, s, GX.SANS, col.texto));
  y += hTxt;
  if (C) {
    y += 12;
    const labW = Math.ceil(Math.max(...filas.map((r) => H.medir(r.lab, GX.MONO)))) + 10;
    const valW = Math.ceil(Math.max(...filas.map((r) => H.medir(r.val, GX.MONO_B)))) + 8;
    const util = Math.max(20, W - labW - valW);
    for (const r of filas) {
      const w = Math.max(3, r.p * util);
      GX.t(svg, 0, y + 15, r.lab, GX.MONO, col.texto);
      GX.rect(svg, labW, y + 5, w, 12, r.fill);
      GX.t(svg, labW + w + 8, y + 15, r.val, GX.MONO_B, r.hero ? acento : col.texto);
      y += 22;
    }
  }
};

// waffle · proporción de 100: cuadrícula 10 × 10 a la izquierda (celda = min(18, (W/2 − 40)/10), hueco 3), a la
//   derecha la cifra, la frase y la leyenda. porcentaje (0, 100] (celdas al entero; si no es entero, nota),
//   cifra {valor, texto}, etiqueta_dentro, etiqueta_resto, formato. Alto 10·celda + 27.
G.waffle = (el, S, { ancho, alto, col }) => {
  H.assert(typeof S.porcentaje === "number" && S.porcentaje > 0 && S.porcentaje <= 100, "porcentaje debe estar en (0, 100]");
  H.assert(S.cifra && typeof S.cifra.valor === "number" && S.cifra.texto, "cifra necesita valor y texto");
  const llenas = Math.round(S.porcentaje), W = ancho, hueco = 3;
  let celda = Math.min(18, (W / 2 - 40) / 10);
  if (alto) celda = Math.min(celda, (alto - 27) / 10);
  H.assert(celda >= 6, "doc: no hay sitio para la cuadrícula del waffle (celda de " + celda.toFixed(1) + " px)");
  const lado = 10 * celda + 9 * hueco, x0 = Math.round(lado) + 24, colW = W - x0;
  const muestra = (fill) => (svg, x, y, l) => GX.rect(svg, x, y, l, l, fill);
  const o = { num: GX.fmt(S.cifra.valor, S.formato), numFill: col.tinta || col.dest, texto: S.cifra.texto,
              leyenda: [{ texto: S.etiqueta_dentro || "", muestra: muestra(col.dest) }, { texto: S.etiqueta_resto || "", muestra: muestra(col.base) }] };
  const Hh = Math.max(Math.round(lado), Math.ceil(GXC.columna(null, x0, colW, 0, o, col)));
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const y0 = Hh - lado;
  for (let i = 0; i < 100; i++) GX.rect(svg, (i % 10) * (celda + hueco), y0 + Math.floor(i / 10) * (celda + hueco), celda, celda, i < llenas ? col.dest : col.base);
  GXC.columna(svg, x0, colW, Hh, o, col);
  if (llenas !== S.porcentaje) GX.anotar(el, "Celdas redondeadas al entero: " + H.num(S.porcentaje, { decimales: 1 }) + "% → " + llenas + " de 100.");
};

// pictograma · K de N unidades contables, una forma por unidad, en una cuadrícula a la izquierda; a la derecha
//   K grande, «de N …» y la leyenda. total (entero 2–200), destacado (0–total), texto (≤ 60; completa «K de N …»),
//   etiqueta_destacado, etiqueta_resto, forma "punto"|"cuadro"|"persona", por_fila (null = automático), formato.
//   Misma búsqueda de columnas que la tarjeta (candidatos 2–25; prefiere celda grande, fila completa, múltiplo
//   de 5, más columnas); celda máxima 24 px y mínima 12 (doc). Alto filas·celda + huecos.
G.pictograma = (el, S, { ancho, alto, col }) => {
  H.assert(Number.isInteger(S.total) && S.total >= 2 && S.total <= 200, "total debe ser un entero de 2 a 200 (para proporciones usa waffle)");
  H.assert(Number.isInteger(S.destacado) && S.destacado >= 0 && S.destacado <= S.total, "destacado debe ser un entero entre 0 y total");
  H.assert(typeof S.texto === "string" && S.texto.trim() && S.texto.length <= 60, "texto: 1–60 caracteres (completa «K de N …»)");
  const forma = S.forma || "punto";
  H.assert(["punto", "cuadro", "persona"].includes(forma), "forma debe ser punto, cuadro o persona");
  H.assert(S.por_fila == null || (Number.isInteger(S.por_fila) && S.por_fila >= 2 && S.por_fila <= 25), "por_fila: null o entero de 2 a 25");
  const W = ancho, ratio = forma === "persona" ? 1.45 : 1, hueco = forma === "persona" ? 4 : 3;
  const gridMax = Math.round(W * 0.6), celdaMax = 24, altoMax = alto || 220, f = (v) => GX.fmt(v, S.formato);
  const cands = S.por_fila ? [S.por_fila] : Array.from({ length: 24 }, (_, i) => i + 2);
  const mejorQue = (a, b) => { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] > b[i]; return false; };
  let mejor = null;
  for (const c of cands) {
    const filas = Math.ceil(S.total / c);
    const celda = Math.floor(Math.min((gridMax - hueco * (c - 1)) / c, (altoMax - hueco * (filas - 1)) / filas / ratio, celdaMax));
    const puntos = [celda, S.total % c === 0 ? 1 : 0, c % 5 === 0 ? 1 : 0, c];
    if (!mejor || mejorQue(puntos, mejor.puntos)) mejor = { c, filas, celda, puntos };
  }
  const { c, filas, celda } = mejor;
  H.assert(celda >= 12, "doc: no caben " + S.total + " unidades a este ancho: usa waffle");
  const altoCelda = Math.round(celda * ratio), gridW = c * celda + (c - 1) * hueco, gridH = filas * altoCelda + (filas - 1) * hueco;
  const x0 = gridW + 24, colW = W - x0;
  const muestra = (fill) => (svg, x, y, l) => GXC.forma(svg, x, y, l, forma, fill);
  const o = { num: f(S.destacado), numFill: col.tinta || col.dest, texto: "de " + f(S.total) + " " + S.texto.trim(),
              leyenda: [{ texto: S.etiqueta_destacado || "", muestra: muestra(col.dest) }, { texto: S.etiqueta_resto || "", muestra: muestra(col.base) }] };
  const Hh = Math.max(gridH, Math.ceil(GXC.columna(null, x0, colW, 0, o, col)));
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const y0 = Hh - gridH;
  for (let i = 0; i < S.total; i++) GXC.forma(svg, (i % c) * (celda + hueco), y0 + Math.floor(i / c) * (altoCelda + hueco), celda, forma, i < S.destacado ? col.dest : col.base);
  GXC.columna(svg, x0, colW, Hh, o, col);
};
