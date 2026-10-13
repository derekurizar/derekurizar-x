// Gráficos de cambio: dos fechas por categoría (pendiente, pesas), dos cifras (antes_despues) y acumulados
// (cascada). Mismo contrato que las plantillas de tarjeta; la aritmética compartida (píldora, acumulados)
// la pone H, nunca el gráfico.

// pendiente · cambio entre dos fechas para 2–6 categorías (slope, tarjeta pendiente).
//   fechas[2], items[2–6] {nombre, a, b}, destacar (índice; línea gruesa en el acento), formato.
//   Ejes a 1/4 y 3/4 del ancho (se acercan si los rótulos no caben; los nombres bajan a 12 px), fechas arriba;
//   «nombre valor» a la izquierda y el valor a la derecha, empujados con H.antiSolape. Dominio sin cero.
//   Alto por defecto 280.
G.pendiente = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.fechas) && S.fechas.length === 2, "fechas debe tener exactamente 2 valores");
  H.assert(Array.isArray(S.items) && S.items.length >= 2 && S.items.length <= 6, "pendiente admite de 2 a 6 items");
  S.items.forEach((it) => H.assert(it && it.nombre && typeof it.a === "number" && typeof it.b === "number", "cada item necesita nombre, a y b numéricos"));
  const n = S.items.length, hi = GX.indice(S.destacar || 0, n), W = ancho, Hh = alto || 280;
  const f = (v) => GX.fmt(v, S.formato);
  const medidaIzq = (fn) => Math.max(...S.items.map((it, i) => H.medir(String(it.nombre), fn(i)) + 6 + H.medir(f(it.a), GX.MONO_B))) + 8;
  let fN = (i) => (i === hi ? GX.SANS_D : GX.SANS), izqW = medidaIzq(fN);
  if (izqW > W / 4) { fN = () => GX.SANS_S; izqW = medidaIzq(fN); }
  const derW = Math.max(...S.items.map((it) => H.medir(f(it.b), GX.MONO_B))) + 8;
  const x0 = Math.max(W / 4, izqW), x1 = Math.min((W * 3) / 4, W - derW);
  H.assert(x1 - x0 >= 60, "doc: pendiente no cabe en " + W + " px: acorta los nombres o usa menos items");
  const y0 = 26, y1 = Hh - 8;
  const sy = H.escala(H.dominio(S.items.flatMap((it) => [it.a, it.b]), false), [y1, y0]);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  GX.linea(svg, x0, y0, x0, y1, col.linea, { "stroke-width": 1, "stroke-opacity": 0.5 });
  GX.linea(svg, x1, y0, x1, y1, col.linea, { "stroke-width": 1, "stroke-opacity": 0.5 });
  GX.t(svg, x0, 12, String(S.fechas[0]), GX.MONO_B, col.texto, { "text-anchor": "middle" });
  GX.t(svg, x1, 12, String(S.fechas[1]), GX.MONO_B, col.texto, { "text-anchor": "middle" });
  const izq = S.items.map((it, i) => ({ i, y: sy(it.a) })), der = S.items.map((it, i) => ({ i, y: sy(it.b) }));
  H.antiSolape(izq, { minGap: 16, min: y0 + 4, max: Hh - 8 });
  H.antiSolape(der, { minGap: 16, min: y0 + 4, max: Hh - 8 });
  const orden = S.items.map((_, i) => i).sort((a, b) => (a === hi) - (b === hi));
  for (const i of orden) {
    const it = S.items[i], d = i === hi, c = d ? col.dest : col.base, tc = d ? (col.tinta || col.dest) : col.texto;
    GX.linea(svg, x0, sy(it.a), x1, sy(it.b), c, { "stroke-width": d ? 3 : 1.5, "stroke-linecap": "round" });
    H.svgEl("circle", { cx: x0, cy: sy(it.a), r: d ? 4.5 : 3, fill: c }, svg);
    H.svgEl("circle", { cx: x1, cy: sy(it.b), r: d ? 4.5 : 3, fill: c }, svg);
    const yi = izq.find((p) => p.i === i).y + 4, yd = der.find((p) => p.i === i).y + 4, va = f(it.a);
    GX.t(svg, x0 - 8, yi, va, GX.MONO_B, tc, { "text-anchor": "end" });
    GX.t(svg, x0 - 8 - H.medir(va, GX.MONO_B) - 6, yi, String(it.nombre), fN(i), tc, { "text-anchor": "end" });
    GX.t(svg, x1 + 8, yd, f(it.b), GX.MONO_B, tc);
  }
};

// pesas · dos fechas por categoría, puntos unidos (dumbbell, tarjeta pesas).
//   fechas[2], items[2–8] {nombre, a, b}, destacar (índice tras ordenar), orden "dado" (defecto) | "desc" (por b),
//   desdeCero (false: eje desde el mínimo, anotado «Eje desde N»), formato. Filas de 30 px; las fechas como
//   leyenda arriba, rejilla con ticks al pie; punto a en tinta y punto b en el acento; valores fuera de los puntos.
//   Los nombres ocupan hasta el 40 % del ancho. Alto por defecto n × 30 + 40.
G.pesas = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.fechas) && S.fechas.length === 2, "fechas debe tener exactamente 2 valores");
  H.assert(Array.isArray(S.items) && S.items.length >= 2 && S.items.length <= 8, "pesas admite de 2 a 8 items");
  S.items.forEach((it) => H.assert(it && typeof it.nombre === "string" && typeof it.a === "number" && typeof it.b === "number", "cada item necesita nombre, a y b numéricos"));
  const items = S.orden === "desc" ? S.items.slice().sort((x, y) => y.b - x.b) : S.items.slice();
  const n = items.length, hi = GX.indice(S.destacar || 0, n), W = ancho;
  const yTop = 24, Hh = Math.max(alto || 0, n * 30 + 40), filaH = (Hh - 40) / n, yBot = yTop + n * filaH;
  const f = (v) => GX.fmt(v, S.formato), wLab = (v) => H.medir(f(v), GX.MONO_B);
  const maxN = Math.floor(W * 0.4);
  const fontN = items.map((it, i) => {
    const fn = H.encajar(it.nombre, [i === hi ? GX.SANS_D : GX.SANS, GX.SANS_S], maxN);
    H.assert(fn, "doc: «" + it.nombre + "» no cabe en la columna de nombres (" + maxN + " px): acórtalo");
    return fn;
  });
  const colN = Math.ceil(Math.max(...items.map((it, i) => H.medir(it.nombre, fontN[i])))) + 12;
  const dom = H.dominio(items.flatMap((it) => [it.a, it.b]), S.desdeCero !== false);
  const tk = H.ticks(dom[0], dom[1], W - colN < 220 ? 2 : 4), fEje = H.formatoEje(S.formato, tk);
  // Reservas: a la derecha, el valor del extremo derecho; a la izquierda, lo que exija el valor del extremo
  // izquierdo que más se acerque a la columna de nombres (x(v) − 12 − ancho ≥ colN + 2, resuelto en cerrado).
  const x1 = W - (Math.max(...items.map((it) => wLab(Math.max(it.a, it.b)))) + 12);
  let res = 0;
  items.forEach((it) => {
    const v = Math.min(it.a, it.b), t = (v - dom[0]) / (dom[1] - dom[0]);
    if (t < 0.999) res = Math.max(res, (14 + wLab(v) - t * (x1 - colN)) / (1 - t));
  });
  const x0 = colN + Math.ceil(Math.max(0, res));
  H.assert(x1 - x0 >= 60, "doc: pesas no cabe en " + W + " px: acorta los nombres o usa escala en formato");
  const sx = H.escala(dom, [x0, x1]);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  H.svgEl("circle", { cx: 5, cy: 8, r: 5, fill: col.texto }, svg);
  GX.t(svg, 16, 12, String(S.fechas[0]), GX.MONO, col.texto);
  const xf = 16 + H.medir(String(S.fechas[0]), GX.MONO) + 18;
  H.svgEl("circle", { cx: xf + 6, cy: 8, r: 6, fill: col.dest }, svg);
  GX.t(svg, xf + 18, 12, String(S.fechas[1]), GX.MONO, col.texto);
  let prevR = -Infinity;
  for (const tick of tk) {
    const x = sx(tick), s = H.num(tick, fEje), w = H.medir(s, GX.MONO);
    GX.linea(svg, x, yTop, x, yBot, col.suave, { "stroke-width": 1 });
    if (x - w / 2 >= prevR + 6 && x - w / 2 >= colN - 10 && x + w / 2 <= W) { GX.t(svg, x, Hh - 2, s, GX.MONO, col.texto, { "text-anchor": "middle" }); prevR = x + w / 2; }
  }
  GX.linea(svg, x0, yBot, x1, yBot, col.linea, { "stroke-width": 1 });
  items.forEach((it, i) => {
    const d = i === hi, cy = yTop + i * filaH + filaH / 2, xa = sx(it.a), xb = sx(it.b);
    GX.t(svg, 0, cy + 5, it.nombre, fontN[i], col.texto);
    GX.rect(svg, Math.min(xa, xb), cy - 3, Math.abs(xb - xa), 6, col.base);
    H.svgEl("circle", { cx: xa, cy, r: 5, fill: col.texto }, svg);
    H.svgEl("circle", { cx: xb, cy, r: 6, fill: col.dest }, svg);
    const izq = it.a <= it.b ? ["a", xa] : ["b", xb], der = it.a <= it.b ? ["b", xb] : ["a", xa];
    const cv = (q) => (d && q === "b" ? (col.tinta || col.dest) : col.texto);
    GX.t(svg, izq[1] - 12, cy + 4, f(it[izq[0]]), GX.MONO_B, cv(izq[0]), { "text-anchor": "end" });
    GX.t(svg, der[1] + 12, cy + 4, f(it[der[0]]), GX.MONO_B, cv(der[0]));
  });
  if (S.desdeCero === false) GX.anotar(el, "Eje desde " + H.num(dom[0], fEje) + ".");
};

// antes_despues · dos cifras grandes, flecha y píldora ×N o ±% calculada (tarjeta antes-despues), en SVG.
//   antes {etiqueta, valor, sub}, despues {etiqueta, valor, sub}, pildora "factor"|"porcentaje"|"ninguna",
//   decimales_pildora, formato. Dos columnas: etiqueta, número en serif (48 → 40 → 32 hasta caber en
//   ancho/2 − 40), sub y barra proporcional de 10 px; la píldora la calcula H.pildora (la misma aritmética que
//   la tarjeta) y va sobre el acento. Alto fijo 150.
G.antes_despues = (el, S, { ancho, col }) => {
  for (const k of ["antes", "despues"]) H.assert(S[k] && typeof S[k].valor === "number" && S[k].etiqueta, k + " necesita etiqueta y valor numérico");
  const W = ancho, Hh = 150, colW = (W - 40) / 2, maxNum = W / 2 - 40;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const max = Math.max(Math.abs(S.antes.valor), Math.abs(S.despues.valor)) || 1;
  const txtP = H.pildora(S.antes.valor, S.despues.valor, S.pildora || "factor", S.decimales_pildora);
  const columna = (D, x, d) => {
    GX.t(svg, x, 12, String(D.etiqueta).toUpperCase(), GX.MONO, col.texto);
    const s = GX.fmt(D.valor, S.formato), fn = H.encajar(s, [GX.serif(48), GX.serif(40), GX.serif(32)], maxNum);
    H.assert(fn, "doc: la cifra «" + s + "» no cabe en " + Math.round(maxNum) + " px ni a 32 px: usa escala en formato");
    GX.t(svg, x, 60, s, fn, d ? (col.tinta || col.dest) : col.texto);
    if (D.sub) GX.t(svg, x, 82, String(D.sub), GX.SANS_S, col.texto);
    GX.rect(svg, x, 92, Math.max(3, (Math.abs(D.valor) / max) * colW), 10, d ? col.dest : col.base);
  };
  columna(S.antes, 0, false);
  columna(S.despues, colW + 40, true);
  const xa = colW + 6, xb = colW + 34, ya = 48;
  GX.linea(svg, xa, ya, xb - 6, ya, col.texto, { "stroke-width": 2 });
  H.svgEl("polygon", { points: (xb - 8) + "," + (ya - 5) + " " + xb + "," + ya + " " + (xb - 8) + "," + (ya + 5), fill: col.texto }, svg);
  if (txtP) {
    const w = H.medir(txtP, GX.MONO_D) + 20;
    GX.rect(svg, 0, 114, w, 26, col.dest, { rx: 10 });
    GX.t(svg, w / 2, 132, txtP, GX.MONO_D, GX.textoSobre(col.dest, col), { "text-anchor": "middle" });
  }
};

// cascada · del inicio al fin sumando y restando (waterfall horizontal, tarjeta cascada).
//   inicio {nombre, valor} | null, pasos[2–8] {nombre, valor ≥ 0, efecto suma|resta}, fin {nombre, valor?} | null,
//   destacar "inicio"|"fin"|índice de paso (defecto: fin, o el último paso), formato. Los acumulados los calcula
//   H.cascada (la misma aritmética que la tarjeta): fin.valor, si va, se coteja; si falta, se anota «calculado».
//   Filas de 30 px, eje cero vertical, barras flotantes de 16 px con conectores punteados; el rótulo con signo
//   va fuera del extremo móvil y nunca cruza el eje cero. Los nombres ocupan hasta el 40 % del ancho.
//   Alto por defecto n × 30.
G.cascada = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.pasos) && S.pasos.length >= 2 && S.pasos.length <= 8, "cascada admite de 2 a 8 pasos");
  S.pasos.forEach((p) => {
    H.assert(p && typeof p.nombre === "string" && p.nombre.trim(), "cada paso necesita nombre");
    H.assert(typeof p.valor === "number" && isFinite(p.valor) && p.valor >= 0, "paso «" + p.nombre + "»: valor numérico ≥ 0 (el signo va en efecto)");
    H.assert(p.efecto === "suma" || p.efecto === "resta", "paso «" + p.nombre + "»: efecto debe ser suma o resta");
  });
  const ini = S.inicio || null, fin = S.fin || null;
  H.assert(ini || fin, "cascada necesita inicio y/o fin");
  if (ini) H.assert(typeof ini.nombre === "string" && ini.nombre.trim() && typeof ini.valor === "number" && isFinite(ini.valor), "inicio necesita nombre y valor numérico");
  if (fin) H.assert(typeof fin.nombre === "string" && fin.nombre.trim() && (fin.valor == null || (typeof fin.valor === "number" && isFinite(fin.valor))), "fin necesita nombre (y valor numérico si va)");
  const { filas, calculado } = H.cascada(ini, S.pasos, fin, S.formato);
  const n = filas.length, np = S.pasos.length;
  H.assert(n <= 10, "cascada: como máximo 10 filas (inicio + pasos + fin)");
  const des = S.destacar == null ? (fin ? "fin" : np - 1) : S.destacar;
  const esHi = (r) => (des === "inicio" && r.tipo === "inicio") || (des === "fin" && r.tipo === "fin") || (Number.isInteger(des) && r.tipo === "paso" && r.i === ((des % np) + np) % np);
  H.assert(filas.some(esHi), "destacar debe ser \"inicio\", \"fin\" o el índice de un paso");
  const W = ancho, Hh = Math.max(alto || 0, n * 30), filaH = Hh / n, barH = 16, maxN = Math.floor(W * 0.4);
  // Nombres: 14 px, 12 px o dos líneas de 12 px (la fila de 30 px las admite) partidas por el espacio que mejor equilibra.
  const partir = (s, fuentes) => {
    const fn = H.encajar(s, fuentes, maxN);
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
  filas.forEach((r) => {
    r.nom = partir(r.nombre, esHi(r) ? [GX.SANS_D, GX.SANS_S] : [GX.SANS, GX.SANS_S]);
    H.assert(r.nom, "«" + r.nombre + "» no cabe en la columna de nombres: acórtalo");
    r.lado = r.hasta >= r.desde ? "der" : "izq";
    r.wl = H.medir(r.rotulo, GX.MONO_B);
  });
  const colIzq = Math.ceil(Math.max(...filas.map((r) => Math.max(...r.nom.lineas.map((l) => H.medir(l, r.nom.font)))))) + 12;
  const labW = Math.ceil(Math.max(...filas.map((r) => r.wl))) + 10;
  const todos = filas.flatMap((r) => [r.desde, r.hasta]), dom = [Math.min(0, ...todos), Math.max(0, ...todos)];
  if (dom[1] === dom[0]) dom[1] = dom[0] + 1;
  // El rótulo va fuera del extremo móvil y nunca cruza el eje cero ni pisa la columna de nombres: si no cabe
  // en su lado pasa al otro extremo de la barra; solo los que no caben en ninguno exigen reserva a la izquierda
  // (resuelta en cerrado y aplicada en una segunda pasada).
  const colocar = (res) => {
    const x0 = colIzq + res, x1 = W - (filas.some((r) => r.lado === "der") ? labW : 0);
    const sx = H.escala(dom, [x0, x1]), xz = sx(0), cruza = (a, b) => a < xz + 3 && b > xz - 3;
    let falta = 0;
    const pos = filas.map((r) => {
      const xa = sx(r.desde), xb = sx(r.hasta), x = Math.min(xa, xb), w = Math.max(2, Math.abs(xb - xa));
      const cabeIzq = x - 8 - r.wl >= colIzq && !cruza(x - 8 - r.wl, x - 8), cabeDer = x + w + 8 + r.wl <= W && !cruza(x + w + 8, x + w + 8 + r.wl);
      let lado = r.lado;
      if (lado === "izq" && !cabeIzq && cabeDer) lado = "der";
      else if (lado === "der" && !cabeDer && cabeIzq) lado = "izq";
      if (lado === "izq" && x - 8 - r.wl < colIzq) {
        const t = (Math.min(r.desde, r.hasta) - dom[0]) / (dom[1] - dom[0]);
        if (t < 0.999) falta = Math.max(falta, (8 + r.wl - t * (x1 - colIzq)) / (1 - t));
      }
      return { x, w, lado };
    });
    return { x0, x1, sx, xz, pos, falta };
  };
  let L = colocar(0);
  if (L.falta > 0) L = colocar(Math.ceil(L.falta));
  H.assert(L.x1 - L.x0 >= 60, "doc: cascada no cabe en " + W + " px: acorta los nombres o usa escala en formato");
  const svg = GX.lienzo(el, W, Hh, S.aria);
  if (calculado) GX.anotar(el, fin.nombre + " calculado desde los pasos.");
  GX.linea(svg, L.xz, 0, L.xz, Hh, col.linea);
  filas.forEach((r, k) => {
    const cy = k * filaH + filaH / 2, hi = esHi(r), resta = r.tipo === "paso" && r.hasta < r.desde, { x, w, lado } = L.pos[k];
    if (r.nom.lineas.length === 1) GX.t(svg, 0, cy + 5, r.nom.lineas[0], r.nom.font, col.texto);
    else r.nom.lineas.forEach((l, q) => GX.t(svg, 0, cy - 2 + q * 13, l, r.nom.font, col.texto));
    GX.rect(svg, x, cy - barH / 2, w, barH, hi ? col.dest : r.tipo !== "paso" ? col.texto : col.base, { "fill-opacity": !hi && resta ? 0.55 : 1 });
    GX.t(svg, lado === "der" ? x + w + 8 : x - 8, cy + 4, r.rotulo, GX.MONO_B, hi ? (col.tinta || col.dest) : col.texto, lado === "der" ? {} : { "text-anchor": "end" });
    if (k < n - 1) { const xc = L.sx(r.hasta); GX.linea(svg, xc, cy + barH / 2, xc, cy + filaH - barH / 2, col.suave, { "stroke-width": 1, "stroke-dasharray": "3 3" }); }
  });
};
