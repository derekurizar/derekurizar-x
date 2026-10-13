// Gráficos de relación del informe: dos variables por unidad (dispersion), filas × columnas en rampa (calor) y
// hitos con fecha y magnitud (linea_tiempo). Mismo contrato que sus plantillas de tarjeta
// (templates/graficos/dispersion.html, calor.html, linea-tiempo.html); los límites propios del documento llevan «doc:».

// dispersion · puntos[8–22] {nombre, x, y}, ejeX, ejeY (títulos ≤ 40), formatoX, formatoY, rotular[≤ 4],
//   destacar (nombre), guias {x, y, texto}, desdeCero. Alto por defecto 320. Rótulos SANS_S con halo colocados en la
//   mejor de 4 posiciones alrededor del punto y empujados en y (H.antiSolape) si comparten columna; a ancho < 400
//   (media página) se rotulan ≤ 2 puntos además del destacado.
G.dispersion = (el, S, { ancho, alto, col }) => {
  H.assert(Array.isArray(S.puntos) && S.puntos.length >= 8 && S.puntos.length <= 22, "dispersion admite de 8 a 22 puntos");
  S.puntos.forEach((p) => H.assert(p && typeof p.nombre === "string" && typeof p.x === "number" && typeof p.y === "number", "cada punto necesita nombre, x e y numéricos"));
  H.assert(typeof S.ejeX === "string" && S.ejeX.trim() && S.ejeX.length <= 40, "ejeX: título del eje horizontal (≤ 40)");
  H.assert(typeof S.ejeY === "string" && S.ejeY.trim() && S.ejeY.length <= 40, "ejeY: título del eje vertical (≤ 40)");
  const rot = (S.rotular || []).slice();
  H.assert(rot.length <= 4, "rotular: como máximo 4 nombres");
  if (S.destacar && !rot.includes(S.destacar)) rot.push(S.destacar);
  for (const r of rot) H.assert(S.puntos.some((p) => p.nombre === r), "rotular/destacar: «" + r + "» no está en puntos");
  H.assert(ancho >= 400 || rot.filter((r) => r !== S.destacar).length <= 2, "doc: a media página rotula ≤ 2 puntos (más el destacado)");
  const g = S.guias || null;
  if (g) H.assert(typeof g.x === "number" || typeof g.y === "number", "guias necesita x y/o y numéricos");
  const fX = S.formatoX || S.formato, fY = S.formatoY || S.formato;
  const ejeFmt = (fm, tk) => { const e = (fm && fm.escala) || 1; return Object.assign({}, fm || {}, { decimales: H.decimalesDe(tk.map((t) => t / e), Math.max(2, (fm && fm.decimales) || 0)) }); };
  const W = ancho, Hh = alto || 320;
  H.assert(H.medir(S.ejeY, GX.MONO) <= W && H.medir(S.ejeX, GX.MONO) <= W, "doc: el título de un eje no cabe a este ancho: acórtalo");
  const xs = S.puntos.map((p) => p.x).concat(g && typeof g.x === "number" ? [g.x] : []);
  const ys = S.puntos.map((p) => p.y).concat(g && typeof g.y === "number" ? [g.y] : []);
  // Dominio con 4 % de aire a cada lado: ningún punto queda montado en un eje.
  const aire = (vals) => { const a = Math.min(...vals), b = Math.max(...vals), d = (b - a || Math.abs(a) || 1) * 0.04; return S.desdeCero ? vals.concat([b + d]) : vals.concat([a - d, b + d]); };
  const domX = H.dominio(aire(xs), !!S.desdeCero), domY = H.dominio(aire(ys), !!S.desdeCero);
  const tkX = H.ticks(domX[0], domX[1], W < 400 ? 4 : 5), tkY = H.ticks(domY[0], domY[1], 4);
  const fEX = ejeFmt(fX, tkX), fEY = ejeFmt(fY, tkY);
  const izq = Math.ceil(Math.max(...tkY.map((t) => H.medir(H.num(t, fEY), GX.MONO)))) + 8;
  const x0 = izq, x1 = W - 8, y0 = 24, y1 = Hh - 36;
  const sx = H.escala(domX, [x0, x1]), sy = H.escala(domY, [y1, y0]);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  if (!S.desdeCero) GX.anotar(el, "Ejes sin cero.");
  const anclaX = (xc, w) => (xc - w / 2 < 0 ? ["start", 0] : xc + w / 2 > W ? ["end", W] : ["middle", xc]);
  tkY.forEach((t) => { GX.linea(svg, x0, sy(t), x1, sy(t), col.suave, { "stroke-width": 1 }); GX.t(svg, x0 - 6, sy(t) + 4, H.num(t, fEY), GX.MONO, col.texto, { "text-anchor": "end" }); });
  tkX.forEach((t) => { const s = H.num(t, fEX), [an, ax] = anclaX(sx(t), H.medir(s, GX.MONO)); GX.linea(svg, sx(t), y0, sx(t), y1, col.suave, { "stroke-width": 1 }); GX.t(svg, ax, y1 + 14, s, GX.MONO, col.texto, { "text-anchor": an }); });
  GX.linea(svg, x0, y1, x1, y1, col.linea);
  GX.linea(svg, x0, y0, x0, y1, col.linea);
  GX.t(svg, 0, 12, S.ejeY, GX.MONO, col.texto);
  GX.t(svg, W, Hh - 4, S.ejeX, GX.MONO, col.texto, { "text-anchor": "end" });
  const capaGuias = H.svgEl("g", {}, svg);   // las guías van debajo de los puntos
  // Puntos comunes; los rotulados y el destacado se dibujan al final, encima de los rótulos.
  const etiquetas = [];
  for (const p of S.puntos) {
    const cx = sx(p.x), cy = sy(p.y), d = p.nombre === S.destacar;
    if (!rot.includes(p.nombre)) H.svgEl("circle", { cx, cy, r: 4, fill: col.base, "fill-opacity": 0.7, stroke: col.texto, "stroke-opacity": 0.35, "stroke-width": 1 }, svg);
    else etiquetas.push({ p, cx, cy, d, r: d ? 6 : 5, t: p.nombre, w: H.medir(p.nombre, GX.SANS_S) });
  }
  // Colocación: el destacado primero; cada rótulo prueba derecha, izquierda, arriba y abajo y se queda con la que menos
  // pisa puntos y rótulos ya puestos sin salirse del lienzo ni invadir el eje Y.
  const solape = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  const circ = S.puntos.map((q) => ({ q, c: [sx(q.x) - 6, sy(q.y) - 6, sx(q.x) + 6, sy(q.y) + 6] }));
  const puestas = [];
  etiquetas.sort((a, b) => (b.d ? 1 : 0) - (a.d ? 1 : 0));
  for (const e of etiquetas) {
    let mejor = null;
    [{ x: e.cx + e.r + 4, y: e.cy + 4, anc: "start" }, { x: e.cx - e.r - 4, y: e.cy + 4, anc: "end" }, { x: e.cx, y: e.cy - e.r - 4, anc: "middle" }, { x: e.cx, y: e.cy + e.r + 13, anc: "middle" }].forEach((o, k) => {
      const caja = o.anc === "start" ? [o.x, o.y - 10, o.x + e.w, o.y + 3] : o.anc === "end" ? [o.x - e.w, o.y - 10, o.x, o.y + 3] : [o.x - e.w / 2, o.y - 10, o.x + e.w / 2, o.y + 3];
      // Fuera del lienzo, del eje Y o encima de los ticks: penalización graduada (gana la que menos se sale).
      const fuera = Math.max(0, x0 - 2 - caja[0]) + Math.max(0, caja[2] - W) + Math.max(0, y0 - 8 - caja[1]) + Math.max(0, caja[3] - (y1 + 4));
      let costo = k * 5 + (fuera > 0 ? 1e4 + fuera * 100 : 0);
      for (const c of circ) if (c.q !== e.p) costo += solape(caja, c.c) * (rot.includes(c.q.nombre) ? 30 : 2);
      for (const o2 of puestas) costo += solape(caja, o2) * 20;
      if (!mejor || costo < mejor.costo) mejor = Object.assign({ costo, caja }, o);
    });
    Object.assign(e, mejor);
    puestas.push(mejor.caja);
  }
  // Rótulos que comparten columna: empuje vertical (H.antiSolape) y una guía desde el punto si se movieron.
  const grupo = etiquetas.map((_, i) => i), raiz = (i) => (grupo[i] === i ? i : (grupo[i] = raiz(grupo[i])));
  etiquetas.forEach((a, i) => etiquetas.forEach((b, j) => { if (j > i && a.caja[0] < b.caja[2] + 4 && b.caja[0] < a.caja[2] + 4) grupo[raiz(i)] = raiz(j); }));
  const grupos = {};
  etiquetas.forEach((e, i) => { (grupos[raiz(i)] = grupos[raiz(i)] || []).push(e); });
  for (const gr of Object.values(grupos)) if (gr.length > 1) { const antes = gr.map((e) => e.y); H.antiSolape(gr, { minGap: 14, min: y0 + 2, max: y1 - 2 }); gr.forEach((e, k) => { e.movida = Math.abs(e.y - antes[k]) > 0.5; }); }
  // Guías (líneas punteadas): su rótulo va al extremo con menos puntos y rótulos encima.
  if (g) {
    const est = { "stroke-width": 1, "stroke-dasharray": "4 4", "stroke-opacity": 0.5 };
    const txt = String(g.texto || "promedio").trim(), wT = H.medir(txt, GX.MONO);
    const cajas = circ.map((c) => c.c).concat(etiquetas.map((e) => e.caja));
    const choques = (c) => cajas.filter((b) => b[0] < c[2] && b[2] > c[0] && b[1] < c[3] && b[3] > c[1]).length;
    const mejor = (ops) => ops.reduce((a, b) => (choques(b.caja) < choques(a.caja) ? b : a));
    const pone = (o) => GX.t(svg, o.x, o.y, txt, GX.MONO, col.texto, { "text-anchor": o.anc, style: "font:" + GX.MONO + ";" + GX.halo(col) });
    if (typeof g.x === "number") GX.linea(capaGuias, sx(g.x), y0, sx(g.x), y1, col.texto, est);
    if (typeof g.y === "number") {
      const yg = sy(g.y);
      GX.linea(capaGuias, x0, yg, x1, yg, col.texto, est);
      pone(mejor([
        { x: x1 - 2, y: yg - 5, anc: "end", caja: [x1 - 2 - wT, yg - 15, x1 - 2, yg - 2] },
        { x: x0 + 6, y: yg - 5, anc: "start", caja: [x0 + 6, yg - 15, x0 + 6 + wT, yg - 2] },
        { x: x1 - 2, y: yg + 13, anc: "end", caja: [x1 - 2 - wT, yg + 3, x1 - 2, yg + 16] },
        { x: x0 + 6, y: yg + 13, anc: "start", caja: [x0 + 6, yg + 3, x0 + 6 + wT, yg + 16] },
      ]));
    } else {
      const xg = sx(g.x), lado = xg + 6 + wT <= x1, xx = lado ? xg + 6 : xg - 6, anc = lado ? "start" : "end";
      const c = (y) => (lado ? [xg + 6, y - 10, xg + 6 + wT, y + 3] : [xg - 6 - wT, y - 10, xg - 6, y + 3]);
      pone(mejor([{ x: xx, y: y0 + 12, anc, caja: c(y0 + 12) }, { x: xx, y: y1 - 6, anc, caja: c(y1 - 6) }]));
    }
  }
  for (const e of etiquetas) {
    if (e.movida) GX.linea(svg, e.cx, e.cy, e.anc === "start" ? e.x - 2 : e.anc === "end" ? e.x + 2 : e.x, e.y - 4, col.texto, { "stroke-width": 1, "stroke-opacity": 0.6 });
    GX.t(svg, e.x, e.y, e.t, GX.SANS_S, e.d ? (col.tinta || col.dest) : col.texto, { "text-anchor": e.anc, style: "font:" + GX.SANS_S + ";" + GX.halo(col) });
  }
  for (const e of etiquetas.slice().reverse()) H.svgEl("circle", { cx: e.cx, cy: e.cy, r: e.r, fill: e.d ? col.dest : col.texto, stroke: col.sobre, "stroke-width": 1.5 }, svg);
};

// calor · filas[1–12] × columnas[2–12], valores[f][c] (null = sin dato), clases (3–7), destacar {fila, col}.
//   Celdas cuadradas de min(40, lo que quepa) con la rampa GX.rampa sobre [mín, máx] en intervalos iguales; el valor va
//   dentro solo con ≤ 6 filas y celda ≥ 34 px. Las etiquetas de columna se ralean si no caben (una de cada N, la última
//   siempre). Alto = filas × celda + 44 (sale del ancho, como el mapa; ignora `alto`).
G.calor = (el, S, { ancho, col }) => {
  H.assert(Array.isArray(S.filas) && S.filas.length >= 1 && S.filas.length <= 12, "filas: de 1 a 12");
  H.assert(Array.isArray(S.columnas) && S.columnas.length >= 2 && S.columnas.length <= 12, "columnas: de 2 a 12");
  const nf = S.filas.length, ncol = S.columnas.length;
  H.assert(Array.isArray(S.valores) && S.valores.length === nf, "valores necesita " + nf + " filas");
  S.valores.forEach((fila, i) => {
    H.assert(Array.isArray(fila) && fila.length === ncol, "valores[" + i + "] necesita " + ncol + " valores (null = sin dato)");
    fila.forEach((v) => H.assert(v === null || (typeof v === "number" && isFinite(v)), "valores: número o null"));
  });
  const planos = S.valores.flat().filter((v) => v !== null);
  H.assert(planos.length >= 2, "calor necesita al menos 2 valores");
  const nc = Math.max(3, Math.min(7, Math.round(S.clases || 5)));
  const hiC = S.destacar && typeof S.destacar === "object" ? S.destacar : null;
  if (hiC) H.assert(Number.isInteger(hiC.fila) && Number.isInteger(hiC.col) && hiC.fila >= 0 && hiC.fila < nf && hiC.col >= 0 && hiC.col < ncol, "destacar: {fila, col} fuera de rango");
  const f = (v) => GX.fmt(v, S.formato), min = Math.min(...planos), max = Math.max(...planos);
  const cs = GX.rampa(nc, col);
  const colorDe = (v) => (max > min ? cs[Math.min(nc - 1, Math.max(0, Math.floor(((v - min) / (max - min)) * nc)))] : cs[nc - 1]);
  const W = ancho, gap = 2;
  const labW = Math.ceil(Math.max(...S.filas.map((s) => H.medir(String(s), GX.MONO)))) + 10;
  const celda = Math.min(40, (W - labW - gap * (ncol - 1)) / ncol);
  H.assert(celda >= 16, "doc: las columnas no caben a este ancho");
  const paso = Math.max(1, Math.ceil((Math.max(...S.columnas.map((c) => H.medir(String(c), GX.MONO))) + 4) / (celda + gap)));
  H.assert(paso <= Math.max(1, Math.floor(ncol / 2)), "doc: las columnas no caben a este ancho");
  const ralear = (p, prioridad) => { const out = []; for (const i of prioridad.concat(Array.from({ length: ncol }, (_, i) => i).filter((i) => i % p === 0))) if (out.every((j) => Math.abs(i - j) >= p)) out.push(i); return new Set(out); };
  const vis = ralear(paso, [ncol - 1]);
  const y0 = 18, Hh = y0 + nf * celda + (nf - 1) * gap + 28, x0 = labW;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  if (paso > 1) GX.anotar(el, "Se rotula una columna de cada " + paso + ".");
  const mostrarValor = nf <= 6 && celda >= 34, sinDato = planos.length < nf * ncol ? GX.sinDato(svg, col) : null;
  S.columnas.forEach((c, j) => { if (vis.has(j)) GX.t(svg, x0 + j * (celda + gap) + celda / 2, 12, String(c), GX.MONO, col.texto, { "text-anchor": "middle" }); });
  S.filas.forEach((nombre, i) => {
    const y = y0 + i * (celda + gap);
    GX.t(svg, x0 - 6, y + celda / 2 + 4, String(nombre), GX.MONO, col.texto, { "text-anchor": "end" });
    S.valores[i].forEach((v, j) => {
      const x = x0 + j * (celda + gap);
      if (v === null) {
        GX.rect(svg, x, y, celda, celda, sinDato, { rx: 3 });
        if (mostrarValor) GX.t(svg, x + celda / 2, y + celda / 2 + 4, "—", GX.MONO, col.texto, { "text-anchor": "middle", "fill-opacity": 0.5 });
        return;
      }
      const c = colorDe(v);
      GX.rect(svg, x, y, celda, celda, c, { rx: 3 });
      if (mostrarValor) { const s = f(v); if (H.medir(s, GX.MONO) <= celda - 4) GX.t(svg, x + celda / 2, y + celda / 2 + 4, s, GX.MONO, GX.textoSobre(c, col), { "text-anchor": "middle" }); }
    });
  });
  if (hiC) {  // contorno de la destacada: halo del fondo + acento de 2 px, por dentro de la celda
    const x = x0 + hiC.col * (celda + gap), y = y0 + hiC.fila * (celda + gap);
    H.svgEl("rect", { x: x + 1, y: y + 1, width: celda - 2, height: celda - 2, rx: 2, fill: "none", stroke: col.sobre, "stroke-width": 4 }, svg);
    H.svgEl("rect", { x: x + 1, y: y + 1, width: celda - 2, height: celda - 2, rx: 2, fill: "none", stroke: col.dest, "stroke-width": 2 }, svg);
  }
  // Leyenda: mín · rampa · máx (y «sin dato» a la derecha si hay nulos)
  const ly = Hh - 8, sw = 18, sh = 10, tMin = f(min), tMax = f(max);
  let lx = x0;
  GX.t(svg, lx, ly, tMin, GX.MONO, col.texto);
  lx += H.medir(tMin, GX.MONO) + 6;
  cs.forEach((c, k) => GX.rect(svg, lx + k * sw, ly - sh + 1, sw - 1, sh, c));
  lx += nc * sw + 5;
  GX.t(svg, lx, ly, tMax, GX.MONO, col.texto);
  if (sinDato) {
    const wS = H.medir("sin dato", GX.MONO), xs = W - wS - 6 - sw;
    H.assert(lx + H.medir(tMax, GX.MONO) + 10 <= xs, "doc: la leyenda no cabe a este ancho: menos clases");
    GX.rect(svg, xs, ly - sh + 1, sw, sh, sinDato, { rx: 2 });
    GX.t(svg, W, ly, "sin dato", GX.MONO, col.texto, { "text-anchor": "end" });
  }
};

// linea_tiempo · eventos[3–8] {fecha (empieza por AAAA), nombre ≤ 40, valor ≥ 0, sub ≤ 40, valor_texto}, proporcional,
//   forma "barra" | "circulo" | "ninguna", destacar (índice). Alto por defecto n × 44 (filas iguales, o centradas según
//   el año si proporcional). Columnas: fecha serif 22 (+ sub MONO si cabe en los 110 px) · espina punteada con círculo ·
//   nombre SANS (14 → 12) · magnitud y valor. Si los sub no caben en la columna de fecha van bajo el nombre y la
//   columna se estrecha a la fecha más ancha; si la magnitud no tiene ≥ 80 px (media página), el nombre va arriba y la
//   barra debajo, en la misma columna.
G.linea_tiempo = (el, S, { ancho, alto, col }) => {
  const E = S.eventos;
  H.assert(Array.isArray(E) && E.length >= 3 && E.length <= 8, "linea-tiempo admite de 3 a 8 eventos");
  E.forEach((e) => {
    H.assert(e && typeof e.fecha === "string" && /^\d{4}/.test(e.fecha.trim()), "cada evento necesita fecha (texto que empieza por el año AAAA)");
    H.assert(typeof e.nombre === "string" && e.nombre.trim() && e.nombre.length <= 40, "cada evento necesita nombre de 1 a 40 caracteres");
    H.assert(typeof e.valor === "number" && isFinite(e.valor) && e.valor >= 0, "cada evento necesita valor numérico ≥ 0 («" + e.nombre + "»)");
    H.assert(e.sub == null || (typeof e.sub === "string" && e.sub.length <= 40), "sub de «" + e.nombre + "»: texto de ≤ 40 caracteres");
  });
  const forma = S.forma == null ? "barra" : S.forma;
  H.assert(["barra", "circulo", "ninguna"].includes(forma), "forma debe ser barra, circulo o ninguna");
  const prop = S.proporcional === true, n = E.length, hi = GX.indice(S.destacar, n);
  const W = ancho, Hh = alto || n * 44;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  GX.anotar(el, prop ? "Intervalos proporcionales al tiempo." : "Intervalos no proporcionales al tiempo.");
  // Centros de fila: equidistantes, o según la fecha (año y mes) si proporcional.
  let cys;
  if (prop) {
    const t = E.map((e) => { const m = /^(\d{4})(?:-(\d{2}))?/.exec(e.fecha.trim()); return +m[1] + (m[2] ? (+m[2] - 1) / 12 : 0); });
    for (let i = 1; i < n; i++) H.assert(t[i] >= t[i - 1], "con proporcional:true los eventos van en orden cronológico («" + E[i].fecha + "»)");
    const sy = H.escala([t[0], t[n - 1]], [22, Hh - 22]);
    cys = t.map(sy);
  } else { const fila = Hh / n; cys = E.map((_, i) => i * fila + fila / 2); }
  const hueco = Math.min(...cys.slice(1).map((y, k) => y - cys[k]));
  // Columnas y modo: en línea (nombre y magnitud en columnas) o apilado (nombre arriba, barra debajo).
  const subEnFecha = E.every((e) => !e.sub || H.medir(e.sub, GX.MONO) <= 98);
  // La columna de fecha mide 110 px cuando lleva los sub; si no, solo lo que pide la fecha más ancha.
  const fechaW = subEnFecha ? 110 : Math.min(110, Math.ceil(Math.max(...E.map((e) => H.medir(e.fecha, GX.serif(22))))) + 14);
  const xSpine = fechaW + 10, xName = xSpine + 12;
  const etiq = E.map((e) => (e.valor_texto != null ? String(e.valor_texto) : GX.fmt(e.valor, S.formato)));
  const fontsN = (d) => (d ? [GX.SANS_D, "800 12px Archivo, sans-serif"] : [GX.SANS, GX.SANS_S]);
  const labW = Math.ceil(Math.max(...etiq.map((s, i) => H.medir(s, i === hi ? GX.MONO_D : GX.MONO_B)))) + 8;
  const magW = forma === "ninguna" ? 0 : 80;
  let nameMax = W - xName - labW - magW - 12;
  let fuentes = E.map((e, i) => H.encajar(e.nombre, fontsN(i === hi), nameMax));
  const cabeSub = (max) => E.every((e) => !e.sub || subEnFecha || H.medir(e.sub, GX.MONO) <= max);
  const apilado = fuentes.some((x) => !x) || !cabeSub(nameMax);
  if (apilado) {
    nameMax = W - xName;
    fuentes = E.map((e, i) => H.encajar(e.nombre, fontsN(i === hi), nameMax));
    E.forEach((e, i) => H.assert(fuentes[i], "doc: el nombre «" + e.nombre + "» no cabe a este ancho: acórtalo"));
    E.forEach((e) => H.assert(!e.sub || subEnFecha || H.medir(e.sub, GX.MONO) <= nameMax, "doc: el sub «" + e.sub + "» no cabe a este ancho: acórtalo"));
  }
  const subBajoNombre = !subEnFecha && E.some((e) => e.sub && e.sub.trim());
  const minFila = apilado ? (subBajoNombre ? 44 : 34) : subBajoNombre ? 36 : 30;
  const par = cys.findIndex((y, k) => k > 0 && y - cys[k - 1] < minFila - 0.5);
  H.assert(par < 0, "doc: hitos a menos de " + minFila + " px (" + (par > 0 ? E[par - 1].fecha + " y " + E[par].fecha : "") + "): " + (prop ? "usa proporcional:false" : "sube alto"));
  const nameW = apilado ? 0 : Math.max(...E.map((e, i) => Math.max(H.medir(e.nombre, fuentes[i]), e.sub && !subEnFecha ? H.medir(e.sub, GX.MONO) : 0)));
  const x0m = apilado ? xName : xName + nameW + 12, x1m = W - labW;
  const max = Math.max(...E.map((e) => e.valor)) || 1;
  const rMax = apilado ? 7 : Math.max(6, Math.min(16, hueco / 2 - 4));
  GX.linea(svg, xSpine, cys[0], xSpine, cys[n - 1], col.suave, { "stroke-width": 2, "stroke-dasharray": "2 4" });
  E.forEach((e, i) => {
    const d = i === hi, cy = cys[i], fill = d ? col.dest : col.texto, conSub = !!(e.sub && e.sub.trim()), subAqui = conSub && subEnFecha;
    GX.t(svg, fechaW - 10, subAqui ? cy - 2 : cy + 7, e.fecha, GX.serif(22), col.texto, { "text-anchor": "end" });
    if (subAqui) GX.t(svg, fechaW - 10, cy + 15, e.sub, GX.MONO, col.texto, { "text-anchor": "end", "fill-opacity": 0.75 });
    H.svgEl("circle", { cx: xSpine, cy, r: d ? 6 : 5, fill }, svg);
    const tc = d ? (col.tinta || col.dest) : col.texto;
    let yBar, hBar, yVal;
    if (apilado) {
      const tres = conSub && !subAqui;
      GX.t(svg, xName, tres ? cy - 12 : cy - 4, e.nombre, fuentes[i], col.texto);
      if (tres) GX.t(svg, xName, cy + 2, e.sub, GX.MONO, col.texto, { "fill-opacity": 0.75 });
      hBar = 8; yBar = tres ? cy + 9 : cy + 4; yVal = yBar + 8;
    } else {
      GX.t(svg, xName, conSub && !subAqui ? cy - 2 : cy + 5, e.nombre, fuentes[i], col.texto);
      if (conSub && !subAqui) GX.t(svg, xName, cy + 14, e.sub, GX.MONO, col.texto, { "fill-opacity": 0.75 });
      hBar = d ? 14 : 12; yBar = cy - hBar / 2; yVal = cy + 4;
    }
    let xLab = x0m;
    if (forma === "barra") {
      const w = Math.max(2, (e.valor / max) * (x1m - x0m));
      GX.rect(svg, x0m, yBar, w, hBar, d ? col.dest : col.base);
      xLab = x0m + w + 6;
    } else if (forma === "circulo") {
      const r = Math.max(1.5, rMax * Math.sqrt(e.valor / max));
      H.svgEl("circle", { cx: x0m + rMax, cy: yBar + hBar / 2, r, fill: d ? col.dest : col.base }, svg);
      xLab = x0m + 2 * rMax + 8;
    }
    GX.t(svg, xLab, yVal, etiq[i], d ? GX.MONO_D : GX.MONO_B, tc);
  });
};
