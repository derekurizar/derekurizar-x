// Páginas de lectura sobre papel: cuerpo (bloques), anexo (bloques con título de anexo),
// apaisada (texto lateral + una figura ancha) y cronología.

// cuerpo · seccion (encabezado derecho), bloques [...]
PAGINAS.cuerpo = (P, X) => '<section class="pagina">' + X.cab(P.seccion) + X.bloques(P.bloques) + X.pie(P.pie) + "</section>";

// anexo · seccion, titulo, lead, bloques
PAGINAS.anexo = (P, X) => '<section class="pagina">' + X.cab(P.seccion) +
  '<h2 class="t2">' + X.md(P.titulo) + "</h2>" + (P.lead ? '<p class="p">' + X.md(P.lead) + "</p>" : "") +
  X.bloques(P.bloques) + X.pie(P.pie) + "</section>";

// apaisada · seccion, lateral [bloques: titulo, texto, notas], figura (panel o papel)
PAGINAS.apaisada = (P, X) => {
  const lat = I.lista(P.lateral).map((B) => {
    if (B.b === "titulo") return '<h3 class="t3" style="margin-top:0">' + X.md(B.texto) + "</h3>";
    if (B.b === "texto") return I.lista(B.parrafos).map((s) => '<p class="p" style="font-size:15px;line-height:1.6">' + X.md(s) + "</p>").join("");
    if (B.b === "notas") return '<div class="margen" style="width:auto;margin-top:auto">' + B.items.map((m) => "<span><b>" + X.esc(m.termino) + "</b> · " + X.md(m.texto) + "</span>").join("") + "</div>";
    return X.bloque(B);
  }).join("");
  const f = Object.assign({}, P.figura);
  return '<section class="pagina apaisada">' + X.cab(P.seccion) +
    '<div style="flex:1;display:flex;gap:40px;margin-top:32px;min-height:0"><div style="flex:none;width:272px;display:flex;flex-direction:column">' + lat + "</div>" +
    '<div style="flex:1;min-width:0;display:flex">' + X.fig(f, { estilo: "margin-top:0;flex:1" }) + "</div></div>" +
    X.pie(P.pie) + "</section>";
};

// cronologia · seccion, titulo, lead, eventos [{fecha, sub, texto, detalle, destacar, pendiente}], fuente
PAGINAS.cronologia = (P, X) => {
  const ev = P.eventos.map((e, i) => {
    const ult = i === P.eventos.length - 1;
    const punto = e.destacar ? '<span style="flex:none;width:16px;height:16px;margin-top:4px;border-radius:50%;background:var(--barra)"></span>'
      : '<span style="flex:none;width:12px;height:12px;margin-top:6px;border-radius:50%;box-sizing:border-box;border:2px ' + (e.pendiente ? "dashed rgba(12,21,32,.5)" : "solid #0C1520") + ';background:var(--papel)"></span>';
    const color = e.destacar ? "color:var(--tinta)" : e.pendiente ? "color:rgba(12,21,32,.62)" : "";
    return '<div style="display:grid;grid-template-columns:128px 24px minmax(0,1fr);gap:0 16px">' +
      '<div style="display:flex;flex-direction:column;gap:4px;padding-bottom:26px"><span style="font:400 24px/1 \'Instrument Serif\',Georgia,serif;' + color + '">' + X.esc(e.fecha) + '</span><span class="mono" style="font-weight:' + (e.destacar ? 700 : 500) + ";" + color + '">' + X.esc(e.sub || "") + "</span></div>" +
      '<div style="display:flex;flex-direction:column;align-items:center">' + punto + (ult ? "" : '<span style="flex:1;width:2px;background:rgba(12,21,32,.25)"></span>') + "</div>" +
      '<div style="padding-bottom:26px;display:flex;flex-direction:column;gap:6px;font:400 15px/1.5 Archivo,sans-serif' + (e.pendiente ? ";color:rgba(12,21,32,.72)" : "") + '">' +
      '<span style="font-weight:' + (e.destacar ? 700 : 400) + '">' + X.md(e.texto) + "</span>" + (e.detalle ? "<span>" + X.md(e.detalle) + "</span>" : "") + "</div></div>";
  }).join("");
  return '<section class="pagina">' + X.cab(P.seccion) + '<h3 class="t3" style="margin-top:36px">' + X.md(P.titulo) + "</h3>" +
    (P.lead ? '<p class="p">' + X.md(P.lead) + "</p>" : "") + '<div style="display:flex;flex-direction:column;margin-top:32px">' + ev + "</div>" +
    X.pie("Fuentes: " + P.fuente) + "</section>";
};
