// Gráficos pequeños para el tablero de cifras clave.

// chispa · la serie como columnas mínimas; la destacada (por defecto la última) en el acento.
G.chispa = (el, S, { ancho, col }) => {
  const n = S.valores.length, W = ancho, Hh = 64, base = 46, tope = 2;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const max = Math.max(...S.valores) || 1, slot = W / n, bw = Math.min(26, slot * 0.64);
  const hi = GX.indice(S.destacar == null ? -1 : S.destacar, n);
  S.valores.forEach((v, i) => {
    const h = Math.max(1, (v / max) * (base - tope));
    GX.rect(svg, i * slot + (slot - bw) / 2, base - h, bw, h, i === hi ? col.dest : col.base);
  });
  GX.linea(svg, 0, base, W, base, col.linea, { "stroke-width": 1 });
  GX.t(svg, 0, 62, S.etiquetas[0], GX.MONO, col.texto);
  GX.t(svg, W, 62, S.etiquetas[n - 1], GX.MONO_B, col.texto, { "text-anchor": "end" });
};

// cuadros · una fila de N cuadros con los marcados en el acento (p. ej. 10 de 29 áreas en alerta).
G.cuadros = (el, S, { ancho, col }) => {
  const W = ancho, Hh = 64, paso = Math.min(11, W / S.total), lado = paso - 2;
  const svg = GX.lienzo(el, W, Hh, S.aria);
  for (let i = 0; i < S.total; i++) GX.rect(svg, i * paso, 14, lado, 18, i < S.marcados ? col.dest : col.base);
  if (S.texto) GX.t(svg, 0, 56, S.texto, GX.MONO, col.texto);
};

// comparacion · dos o tres barras horizontales en HTML con su rótulo (periodos distintos, declarados).
G.comparacion = (el, S, { ancho, col }) => {
  const max = Math.max(...S.items.map((it) => it.valor)) || 1, util = ancho - 92 - 10 - 40;
  el.innerHTML = '<div style="height:64px;display:flex;flex-direction:column;justify-content:center;gap:8px">' +
    S.items.map((it) => '<div style="display:flex;align-items:center;gap:10px;font:500 12px/1 \'JetBrains Mono\',monospace">' +
      '<span style="flex:none;width:92px">' + I.esc(it.nombre) + '</span>' +
      '<span style="width:' + ((it.valor / max) * util).toFixed(1) + 'px;height:12px;background:' + (it.destacar ? col.dest : col.base) + '"></span>' +
      '<span style="font-weight:' + (it.destacar ? 700 : 500) + '">' + I.esc(GX.fmt(it.valor, S.formato)) + '</span></div>').join("") + "</div>";
};
