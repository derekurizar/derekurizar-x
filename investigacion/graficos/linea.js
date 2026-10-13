// linea · una o más series en el tiempo; la destacada gruesa en el acento, el resto en tinta atenuada.
//   etiquetas[], series [{nombre, valores, destacar}], max (techo del eje; por defecto el dato),
//   sufijo del eje ("%"), anotaciones [{serie, i, texto, lado "arriba"|"izq"}], formato.
G.linea = (el, S, { ancho, alto, col }) => {
  const n = S.etiquetas.length, W = ancho, Hh = alto || 340;
  const ejeW = 40, finW = 64, arriba = 10, base = Hh - 30, x0 = ejeW, x1 = W - finW;
  const todos = S.series.flatMap((s) => s.valores.filter((v) => v != null));
  const tope = S.max || H.dominio(todos, true)[1];
  const ticks = H.ticks(0, tope, 4).filter((v) => v <= tope + 1e-9);
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const x = (i) => x0 + (i * (x1 - x0)) / (n - 1), y = (v) => base - (v / tope) * (base - arriba);
  for (const tk of ticks) {
    if (tk > 0) GX.linea(svg, x0, y(tk), x1, y(tk), col.suave, { "stroke-width": 1 });
    GX.t(svg, 0, y(tk) + 4, H.num(tk, { decimales: H.decimalesDe(ticks) }) + (S.sufijo || ""), GX.MONO, col.texto);
  }
  GX.linea(svg, x0, base, x1, base, col.linea);
  const orden = S.series.map((s, j) => j).sort((a, b) => (S.series[a].destacar ? 1 : 0) - (S.series[b].destacar ? 1 : 0));
  // Rótulos finales (nombre + valor, dos líneas de 12 px): se empujan para no solaparse (H.antiSolape es puro).
  const rot = S.series.map((s) => { const ult = s.valores.length - 1; return { y: y(s.valores[ult]), v: s.valores[ult] }; });
  H.antiSolape(rot, { minGap: 30, min: 14, max: base - 2 });
  for (const j of orden) {
    const s = S.series[j], d = !!s.destacar;
    const pts = s.valores.map((v, i) => (v == null ? null : x(i) + "," + y(v))).filter(Boolean).join(" ");
    H.svgEl("polyline", { points: pts, fill: "none", stroke: d ? col.dest : col.texto, "stroke-opacity": d ? 1 : 0.55, "stroke-width": d ? 3.5 : 2, "stroke-linejoin": "round" }, svg);
    const ult = s.valores.length - 1, v = s.valores[ult], yr = rot[j].y;
    H.svgEl("circle", { cx: x(ult), cy: y(v), r: d ? 5 : 4, fill: d ? col.dest : col.texto, "fill-opacity": d ? 1 : 0.55 }, svg);
    const tc = d ? (col.tinta || col.dest) : col.texto;
    GX.t(svg, x1 + 10, yr - 2, s.nombre, GX.MONO_B, tc, d ? {} : { "fill-opacity": 0.75 });
    GX.t(svg, x1 + 10, yr + 14, GX.fmt(v, S.formato) + (S.sufijo || ""), d ? GX.MONO_D : GX.MONO_B, tc, d ? {} : { "fill-opacity": 0.75 });
  }
  for (const a of S.anotaciones || []) {
    const s = S.series[a.serie], v = s.valores[a.i], d = !!s.destacar;
    if (d) H.svgEl("circle", { cx: x(a.i), cy: y(v), r: 4, fill: col.dest }, svg);
    const izq = a.lado === "izq";
    GX.t(svg, izq ? x(a.i) - 8 : x(a.i), izq ? y(v) - 4 : y(v) - 11, a.texto, GX.MONO_B, d ? (col.tinta || col.dest) : col.texto, { "text-anchor": izq ? "end" : "middle" });
  }
  S.etiquetas.forEach((et, i) => GX.t(svg, x(i), Hh - 8, et, i === n - 1 ? GX.MONO_B : GX.MONO, col.texto, { "text-anchor": "middle" }));
};
