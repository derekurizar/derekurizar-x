// linea · una o más series en el tiempo; la destacada gruesa en el acento, el resto en tinta atenuada.
//   Mismo contrato que templates/graficos/linea.html: etiquetas (o etiquetasX; informe.py copia una en la otra) [≥ 3],
//   series[1–4] {nombre, valores (null = hueco: corta la línea), destacar}, yDesdeCero (true; false ⇒ nota «Eje desde N»),
//   ejeY (false oculta eje y rejilla), valoresBajoEje (true y n ≤ 12: la serie destacada bajo cada etiqueta),
//   rotularFin (null = nombre + valor de todas las series al final · [nombres] = solo esas · false = ninguna),
//   hitos[≤ 1] {i, texto} (línea vertical punteada con el texto arriba), periodos [{desde, hasta, nombre}] (≤ 4).
//   Propios del documento: max (techo del eje), sufijo del eje ("%"), anotaciones [{serie, i, texto, lado "arriba"|"izq"}].
//   Alto por defecto 340. Sin destacada, la primera serie lleva el acento. Las etiquetas X se ralean cuando no
//   caben (la última siempre va).
G.linea = (el, S, { ancho, alto, col }) => {
  const E = S.etiquetas || S.etiquetasX;
  H.assert(Array.isArray(E) && E.length >= 3, "etiquetasX necesita ≥3 puntos");
  H.assert(Array.isArray(S.series) && S.series.length >= 1 && S.series.length <= 4, "linea admite de 1 a 4 series");
  const n = E.length;
  S.series.forEach((s) => {
    H.assert(s && s.nombre && Array.isArray(s.valores) && s.valores.length === n, "cada serie necesita nombre y " + n + " valores (null = hueco)");
    s.valores.forEach((v) => H.assert(v === null || typeof v === "number", "valores: número o null"));
    H.assert(s.valores.filter((v) => v !== null).length >= 2, "la serie «" + s.nombre + "» tiene menos de 2 valores");
  });
  H.assert(!S.hitos || S.hitos.length <= 1, "como máximo un hito");
  const P = H.validarPeriodos(S.periodos, n);
  const hito = S.hitos && S.hitos.length ? S.hitos[0] : null;
  if (hito) H.assert(Number.isInteger(hito.i) && hito.i >= 0 && hito.i < n, "hito.i fuera de rango");
  const rf = S.rotularFin;
  if (Array.isArray(rf)) rf.forEach((nm) => H.assert(S.series.some((s) => s.nombre === nm), "rotularFin: «" + nm + "» no está en series"));
  const hi = Math.max(0, S.series.findIndex((s) => s.destacar));
  const f = (v) => GX.fmt(v, S.formato) + (S.sufijo || "");
  const todos = S.series.flatMap((s) => s.valores.filter((v) => v !== null));
  const desdeCero = S.yDesdeCero !== false;
  const dom = H.dominio(todos, desdeCero);
  if (S.max != null) { H.assert(S.max >= Math.max(...todos), "doc: max (" + S.max + ") queda por debajo del dato"); dom[1] = S.max; }
  const tk = H.ticks(dom[0], dom[1], 4).filter((t) => t >= dom[0] - 1e-9 && t <= dom[1] + 1e-9);
  const esc = (S.formato && S.formato.escala) || 1;
  const fEje = Object.assign({}, S.formato || {}, { decimales: H.decimalesDe(tk.map((t) => t / esc), Math.max(2, (S.formato && S.formato.decimales) || 0)) });
  const tickTxt = tk.map((t) => H.num(t, fEje) + (S.sufijo || ""));
  const ejeY = S.ejeY !== false, valoresBajo = S.valoresBajoEje === true && n <= 12, sb = S.series[hi];
  const W = ancho, Hh = alto || 340;
  const ultimo = (s) => { let u = n - 1; while (u > 0 && s.valores[u] === null) u--; return u; };
  const fin = S.series.map((s, j) => { const u = ultimo(s); return { j, u, v: s.valores[u], rot: rf == null || rf === true || (Array.isArray(rf) && rf.includes(s.nombre)) }; });
  const finW = Math.ceil(Math.max(8, ...fin.filter((p) => p.rot).map((p) => Math.max(H.medir(S.series[p.j].nombre, GX.MONO_B), H.medir(f(p.v), GX.MONO_D)) + 12)));
  const ejeW = ejeY ? Math.ceil(Math.max(...tickTxt.map((s) => H.medir(s, GX.MONO)))) + 8 : 6;
  const arriba = 10 + (P.length ? 16 : 0) + (hito ? 16 : 0), base = Hh - 30 - (valoresBajo ? 16 : 0);
  const x0 = ejeW, x1 = W - finW;
  H.assert(x1 - x0 >= 100, "doc: no queda sitio para las líneas (" + Math.round(x1 - x0) + " px): quita rótulos finales (rotularFin) o acorta los nombres");
  const x = (i) => x0 + (i * (x1 - x0)) / (n - 1), sy = H.escala(dom, [base, arriba]);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  if (!desdeCero) GX.anotar(el, "Eje desde " + H.num(dom[0], fEje) + (S.sufijo || "") + ".");
  if (P.length) { const h = (x1 - x0) / (n - 1) / 2; GX.periodos(svg, P, (i) => [Math.max(x0, x(i) - h), Math.min(x1, x(i) + h)], arriba - 4, base, 12, col); }
  if (ejeY) {
    tk.forEach((t, k) => {
      const yy = sy(t);
      if (Math.abs(yy - base) > 1) GX.linea(svg, x0, yy, x1, yy, col.suave, { "stroke-width": 1 });
      GX.t(svg, ejeW - 6, yy + 4, tickTxt[k], GX.MONO, col.texto, { "text-anchor": "end" });
    });
    GX.linea(svg, x0, base, x1, base, col.linea);
  } else GX.linea(svg, x0, base, x1, base, col.linea, { "stroke-dasharray": "4 5" });
  if (hito) {
    const hx = x(hito.i), txt = String(hito.texto || ""), der = hx + 6 + H.medir(txt, GX.MONO) <= W;
    GX.linea(svg, hx, arriba - 6, hx, base, col.texto, { "stroke-width": 1, "stroke-dasharray": "3 4", "stroke-opacity": 0.5 });
    if (txt) GX.t(svg, der ? hx + 6 : hx - 6, P.length ? 28 : 12, txt, GX.MONO, col.texto, { "text-anchor": der ? "start" : "end" });
  }
  // Etiquetas X: se ralea a un paso que quepa (la última siempre); un rótulo que se saldría del lienzo se ancla al borde.
  const ralear = (paso, prioridad) => { const out = []; for (const i of prioridad.concat(Array.from({ length: n }, (_, i) => i).filter((i) => i % paso === 0))) if (out.every((j) => Math.abs(i - j) >= paso)) out.push(i); return new Set(out); };
  const ancla = (xc, w) => (xc - w / 2 < 0 ? ["start", 0] : xc + w / 2 > W ? ["end", W] : ["middle", xc]);
  const etW = Math.max(...E.map((e) => H.medir(String(e), GX.MONO_B))) + 6;
  const valW = valoresBajo ? Math.max(...sb.valores.filter((v) => v !== null).map((v) => H.medir(f(v), GX.MONO))) + 6 : 0;
  const vis = ralear(Math.max(1, Math.ceil(Math.max(etW, valW) / ((x1 - x0) / (n - 1)))), [n - 1]);
  E.forEach((et, i) => {
    if (!vis.has(i)) return;
    const fe = i === n - 1 ? GX.MONO_B : GX.MONO, [an, ax] = ancla(x(i), H.medir(String(et), fe));
    GX.t(svg, ax, valoresBajo ? Hh - 24 : Hh - 8, String(et), fe, col.texto, { "text-anchor": an });
    if (valoresBajo && sb.valores[i] !== null) { const sv = f(sb.valores[i]), [a2, x2] = ancla(x(i), H.medir(sv, GX.MONO)); GX.t(svg, x2, Hh - 8, sv, GX.MONO, col.texto, { "text-anchor": a2 }); }
  });
  // Series: primero las atenuadas (.55 / .4 / .3), la destacada encima; null corta la línea.
  const orden = S.series.map((s, j) => j).sort((a, b) => (a === hi ? 1 : 0) - (b === hi ? 1 : 0));
  let k = 0;
  const op = S.series.map((s, j) => (j === hi ? 1 : [0.55, 0.4, 0.3][Math.min(k++, 2)]));
  for (const j of orden) {
    const s = S.series[j], d = j === hi;
    let dd = "", abierto = false;
    s.valores.forEach((v, i) => { if (v === null) { abierto = false; return; } dd += (abierto ? " L" : " M") + x(i).toFixed(1) + " " + sy(v).toFixed(1); abierto = true; });
    H.svgEl("path", { d: dd.trim(), fill: "none", stroke: d ? col.dest : col.texto, "stroke-opacity": op[j], "stroke-width": d ? 3 : 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    H.svgEl("circle", { cx: x(fin[j].u), cy: sy(fin[j].v), r: d ? 4.5 : 3.5, fill: d ? col.dest : col.texto, "fill-opacity": op[j] }, svg);
  }
  // Rótulos finales (nombre + valor, dos líneas): se empujan para no solaparse (H.antiSolape es puro).
  const rot = fin.filter((p) => p.rot).map((p) => ({ j: p.j, y: sy(p.v), v: p.v }));
  H.antiSolape(rot, { minGap: 30, min: arriba + 2, max: base - 8 });
  for (const r of rot) {
    const d = r.j === hi, tc = d ? (col.tinta || col.dest) : col.texto, ex = d ? {} : { "fill-opacity": 0.75 };
    GX.t(svg, x1 + 10, r.y - 2, S.series[r.j].nombre, GX.MONO_B, tc, ex);
    GX.t(svg, x1 + 10, r.y + 14, f(r.v), d ? GX.MONO_D : GX.MONO_B, tc, ex);
  }
  for (const a of S.anotaciones || []) {
    const s = S.series[a.serie];
    H.assert(s && typeof s.valores[a.i] === "number", "doc: anotación fuera de rango (serie " + a.serie + ", i " + a.i + ")");
    const v = s.valores[a.i], d = a.serie === hi, izq = a.lado === "izq";
    if (d) H.svgEl("circle", { cx: x(a.i), cy: sy(v), r: 4, fill: col.dest }, svg);
    GX.t(svg, izq ? x(a.i) - 8 : x(a.i), izq ? sy(v) - 4 : sy(v) - 11, a.texto, GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": izq ? "end" : "middle" });
  }
};

// multiples · pequeños múltiplos: 4–9 mini-líneas en la MISMA escala, con el último valor en la cabecera de cada panel.
//   Mismo contrato que templates/graficos/multiples.html: etiquetasX[4–30], paneles[4–9] {nombre, valores (null = hueco)},
//   destacar (índice del panel clave), referencia {valor, texto} (punteada en todos), yDesdeCero (false ⇒ «Eje desde N»).
//   Rejilla 2×2 / 2×3 / 3×3 (a ancho < 480, dos columnas); alto por defecto filas × 120 + 30 y nunca menos de
//   filas × 80 + 30 (un panel por debajo de 80 px no se lee). Ticks solo en la primera columna; etiquetas X (primera y
//   última) solo bajo el último panel de cada columna.
G.multiples = (el, S, { ancho, alto, col }) => {
  const E = S.etiquetasX || S.etiquetas;
  H.assert(Array.isArray(E) && E.length >= 4 && E.length <= 30, "etiquetasX necesita de 4 a 30 puntos");
  H.assert(Array.isArray(S.paneles) && S.paneles.length >= 4 && S.paneles.length <= 9, "multiples admite de 4 a 9 paneles");
  const n = E.length, m = S.paneles.length;
  S.paneles.forEach((p) => {
    H.assert(p && typeof p.nombre === "string" && p.nombre.trim() && Array.isArray(p.valores) && p.valores.length === n, "cada panel necesita nombre y " + n + " valores (null = hueco)");
    p.valores.forEach((v) => H.assert(v === null || typeof v === "number", "valores: número o null"));
    H.assert(p.valores.filter((v) => v !== null).length >= 2, "el panel «" + p.nombre + "» tiene menos de 2 valores");
  });
  H.assert(S.referencia == null || (typeof S.referencia.valor === "number" && typeof S.referencia.texto === "string"), "referencia: {valor, texto} o null");
  const hi = GX.indice(S.destacar, m), f = (v) => GX.fmt(v, S.formato), desdeCero = S.yDesdeCero !== false;
  const todos = S.paneles.flatMap((p) => p.valores.filter((v) => v !== null)).concat(S.referencia ? [S.referencia.valor] : []);
  const dom = H.dominio(todos, desdeCero);
  let tk = H.ticks(dom[0], dom[1], 3);
  if (tk.length > 4) tk = H.ticks(dom[0], dom[1], 2);
  const esc = (S.formato && S.formato.escala) || 1;
  const fEje = Object.assign({}, S.formato || {}, { decimales: H.decimalesDe(tk.map((t) => t / esc), Math.max(2, (S.formato && S.formato.decimales) || 0)) });
  const W = ancho, cols = W < 480 || m <= 4 ? 2 : 3, filas = Math.ceil(m / cols), gapX = 10, gapY = 10, abajo = 20;
  const Hh = alto ? Math.max(alto, filas * 80 + 30) : filas * 120 + 30;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  GX.anotar(el, (S.referencia ? "Línea punteada: " + S.referencia.texto + ". " : "") + "Misma escala en todos los paneles." + (desdeCero ? "" : " Eje desde " + H.num(dom[0], fEje) + "."));
  const izq = Math.ceil(Math.max(...tk.map((t) => H.medir(H.num(t, fEje), GX.MONO)))) + 6;
  const pw = (W - izq - (cols - 1) * gapX) / cols, ph = (Hh - abajo - (filas - 1) * gapY) / filas, cabH = 22, pad = 6;
  const ultimoDeColumna = (c) => { let u = -1; for (let i = 0; i < m; i++) if (i % cols === c) u = i; return u; };
  S.paneles.forEach((p, i) => {
    const c = i % cols, r = Math.floor(i / cols), d = i === hi;
    const x = izq + c * (pw + gapX), y = r * (ph + gapY);
    const px0 = x + pad, px1 = x + pw - pad, py0 = y + cabH + 6, py1 = y + ph - 8;
    const sx = H.escala([0, n - 1], [px0, px1]), sy = H.escala(dom, [py1, py0]);
    GX.rect(svg, x, y, pw, ph, col.suave);
    let u = n - 1; while (u > 0 && p.valores[u] === null) u--;
    const val = f(p.valores[u]), fv = d ? GX.MONO_D : GX.MONO_B, wV = H.medir(val, fv);
    const fn = H.encajar(p.nombre, d ? [GX.SANS_D, "800 12px Archivo, sans-serif"] : [GX.SANS, GX.SANS_S], pw - 2 * pad - wV - 6);
    H.assert(fn, "el nombre «" + p.nombre + "» no cabe en su panel: acórtalo");
    GX.t(svg, px0, y + 16, p.nombre, fn, col.texto);
    GX.t(svg, px1, y + 16, val, fv, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": "end" });
    tk.forEach((t) => {
      const yt = sy(t);
      GX.linea(svg, px0, yt, px1, yt, col.linea, { "stroke-width": 1, "stroke-opacity": Math.abs(t - dom[0]) < 1e-9 ? 0.5 : 0.15 });
      if (c === 0) GX.t(svg, x - 4, yt + 4, H.num(t, fEje), GX.MONO, col.texto, { "text-anchor": "end" });
    });
    if (S.referencia) { const yr = sy(S.referencia.valor); GX.linea(svg, px0, yr, px1, yr, col.texto, { "stroke-width": 1, "stroke-dasharray": "3 3", "stroke-opacity": 0.6 }); }
    let dd = "", abierto = false;
    p.valores.forEach((v, j) => { if (v === null) { abierto = false; return; } dd += (abierto ? " L" : " M") + sx(j).toFixed(1) + " " + sy(v).toFixed(1); abierto = true; });
    H.svgEl("path", { d: dd.trim(), fill: "none", stroke: d ? col.dest : col.texto, "stroke-width": d ? 2.5 : 1.5, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    H.svgEl("circle", { cx: sx(u), cy: sy(p.valores[u]), r: d ? 4 : 3, fill: d ? col.dest : col.texto }, svg);
    if (i === ultimoDeColumna(c)) {
      GX.t(svg, px0, y + ph + 14, String(E[0]), GX.MONO, col.texto);
      GX.t(svg, px1, y + ph + 14, String(E[n - 1]), GX.MONO_B, col.texto, { "text-anchor": "end" });
    }
  });
};

// combinado · barras (eje izquierdo, desde cero) + línea (eje derecho) para dos magnitudes en el tiempo.
//   Mismo contrato que templates/graficos/combinado.html: etiquetas[3–12], barras {nombre, valores ≥ 0, formato},
//   linea {nombre, valores, formato, desdeCero}, destacar (índice; −1 = el último), rotular (null = todas si ≤ 8
//   periodos, si no destacada + primero + último · "todas" | "destacada"). Alto por defecto 300. Títulos de eje MONO
//   encima de cada eje (en dos filas si no caben juntos); el rótulo de la línea lleva halo y, si choca con el de la
//   barra, baja; si aun así pisa, cae el de la barra (la línea manda).
G.combinado = (el, S, { ancho, alto, col }) => {
  const E = S.etiquetas || S.etiquetasX;
  H.assert(Array.isArray(E) && E.length >= 3 && E.length <= 12, "combinado admite de 3 a 12 periodos");
  const n = E.length;
  for (const k of ["barras", "linea"]) {
    const s = S[k];
    H.assert(s && typeof s.nombre === "string" && s.nombre.trim() && s.nombre.length <= 30, k + ".nombre: 1–30 caracteres (serie y unidad)");
    H.assert(Array.isArray(s.valores) && s.valores.length === n, k + ".valores necesita " + n + " valores");
    s.valores.forEach((v) => H.assert(typeof v === "number" && isFinite(v), k + ".valores: números"));
  }
  S.barras.valores.forEach((v) => H.assert(v >= 0, "barras.valores: ≥ 0 (las barras parten de cero)"));
  const hi = GX.indice(S.destacar == null ? -1 : S.destacar, n);
  const fB = S.barras.formato || S.formato, fL = S.linea.formato || S.formato;
  const ejeFmt = (fm, tk) => { const e = (fm && fm.escala) || 1; return Object.assign({}, fm || {}, { decimales: H.decimalesDe(tk.map((t) => t / e), Math.max(2, (fm && fm.decimales) || 0)) }); };
  const desdeCero = S.linea.desdeCero !== false;
  const domB = H.dominio(S.barras.valores, true), domL = H.dominio(S.linea.valores, desdeCero);
  const tkB = H.ticks(domB[0], domB[1], 4), tkL = H.ticks(domL[0], domL[1], 4);
  const fEB = ejeFmt(fB, tkB), fEL = ejeFmt(fL, tkL);
  const W = ancho, Hh = alto || 300;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  GX.anotar(el, "Dos escalas: barras a la izquierda desde cero; línea a la derecha" + (desdeCero ? "" : " desde " + H.num(domL[0], fEL)) + ".");
  // Títulos de eje con su marca (cuadro = barras, trazo = línea); en dos filas si no caben juntos.
  const wTR = H.medir(S.linea.nombre, GX.MONO), yT2 = 14 + H.medir(S.barras.nombre, GX.MONO) + 16 + 22 + wTR > W ? 26 : 12;
  GX.rect(svg, 0, 3, 10, 10, col.base);
  GX.t(svg, 14, 12, S.barras.nombre, GX.MONO, col.texto);
  GX.linea(svg, W - wTR - 22, yT2 - 4, W - wTR - 6, yT2 - 4, col.texto, { "stroke-width": 2 });
  GX.t(svg, W, yT2, S.linea.nombre, GX.MONO, col.texto, { "text-anchor": "end" });
  const izq = Math.ceil(Math.max(...tkB.map((t) => H.medir(H.num(t, fEB), GX.MONO)))) + 8;
  const der = Math.ceil(Math.max(...tkL.map((t) => H.medir(H.num(t, fEL), GX.MONO)))) + 8;
  const y0 = yT2 + 26, y1 = Hh - 22, x0 = izq, x1 = W - der;
  H.assert(x1 - x0 >= 90 && y1 - y0 >= 80, "doc: no queda sitio para el gráfico a " + W + "×" + Hh + " px");
  const syB = H.escala(domB, [y1, y0]), syL = H.escala(domL, [y1, y0]);
  tkB.forEach((t) => { const yy = syB(t); if (t > 0) GX.linea(svg, x0, yy, x1, yy, col.suave, { "stroke-width": 1 }); GX.t(svg, x0 - 6, yy + 4, H.num(t, fEB), GX.MONO, col.texto, { "text-anchor": "end" }); });
  GX.linea(svg, x0, y1, x1, y1, col.linea);
  tkL.forEach((t) => { const yy = syL(t); GX.linea(svg, x1 + 1, yy, x1 + 4, yy, col.linea, { "stroke-width": 1 }); GX.t(svg, x1 + 7, yy + 4, H.num(t, fEL), GX.MONO, col.texto); });
  // Barras y etiquetas X (raleadas si no caben; la destacada y la última tienen prioridad).
  const slot = (x1 - x0) / n, bw = Math.min(56, slot * 0.68), xc = (i) => x0 + i * slot + slot / 2;
  const ralear = (paso, prioridad) => { const out = []; for (const i of prioridad.concat(Array.from({ length: n }, (_, i) => i).filter((i) => i % paso === 0))) if (out.every((j) => Math.abs(i - j) >= paso)) out.push(i); return new Set(out); };
  const vis = ralear(Math.max(1, Math.ceil((Math.max(...E.map((e) => H.medir(String(e), GX.MONO_B))) + 4) / slot)), [hi, n - 1]);
  S.barras.valores.forEach((v, i) => {
    const d = i === hi;
    GX.rect(svg, xc(i) - bw / 2, syB(v), bw, y1 - syB(v), d ? col.dest : col.base);
    if (vis.has(i)) GX.t(svg, xc(i), Hh - 6, String(E[i]), d ? GX.MONO_B : GX.MONO, col.texto, { "text-anchor": "middle" });
  });
  H.svgEl("path", { d: S.linea.valores.map((v, i) => (i ? " L" : "M") + xc(i).toFixed(1) + " " + syL(v).toFixed(1)).join(""), fill: "none", stroke: col.texto, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
  S.linea.valores.forEach((v, i) => H.svgEl("circle", { cx: xc(i), cy: syL(v), r: i === hi ? 4.5 : 3.5, fill: col.texto, stroke: col.sobre, "stroke-width": 1.5 }, svg));
  // Rótulos por columna: barra encima de su barra; línea encima del punto (si chocan, baja; si aun así pisa, cae el de la barra).
  const rotulada = (i) => (S.rotular === "todas" ? true : S.rotular === "destacada" ? i === hi : n <= 8 || i === hi || i === 0 || i === n - 1);
  const solapan = (a, b) => a[0] < b[1] && b[0] < a[1];
  const ancla = (i, w) => (w <= bw ? ["middle", xc(i)] : i === 0 ? ["start", x0] : i === n - 1 ? ["end", x1] : ["middle", xc(i)]);
  S.barras.valores.forEach((v, i) => {
    if (!rotulada(i)) return;
    const d = i === hi, vl = S.linea.valores[i], yb = syB(v), yl = syL(vl);
    const sB = GX.fmt(v, fB), sL = GX.fmt(vl, fL), wB = H.medir(sB, GX.MONO_B), wL = H.medir(sL, GX.MONO_B);
    const clave = d || i === 0 || i === n - 1, anchoCol = slot - 4;
    let pintarB = clave || wB <= anchoCol;
    const pintarL = clave || wL <= anchoCol;
    const yB = yb - 5, cajaB = [yB - 12, yB + 2];
    let yL = yl - 9, cajaL = [yL - 12, yL + 2];
    if (pintarB && pintarL && solapan(cajaB, cajaL)) {
      const abajo = yl + 18, cajaAbajo = [abajo - 12, abajo + 2];
      if (abajo <= y1 + 2 && !solapan(cajaB, cajaAbajo)) { yL = abajo; cajaL = cajaAbajo; } else pintarB = false;
    }
    if (pintarB) { const [a, xx] = ancla(i, wB); GX.t(svg, xx, yB, sB, GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": a, style: "font:" + GX.MONO_B + ";" + GX.halo(col) }); }
    if (pintarL) { const [a, xx] = ancla(i, wL); GX.t(svg, xx, yL, sL, GX.MONO_B, col.texto, { "text-anchor": a, style: "font:" + GX.MONO_B + ";" + GX.halo(col) }); }
  });
};
