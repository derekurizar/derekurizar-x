// Piezas comunes de las páginas. C(R, P) devuelve el contexto que recibe cada PAGINAS.<tipo>(P, ctx):
//   cab(derecha)        encabezado corrido (kicker del informe a la izquierda)
//   pie(izquierda)      pie de página: texto, número de página y badge X + handle
//   bloques(lista)      bloques de cuerpo: titulo · texto · figura · figuras · tabla · cita · caja · lectura
//   fig(f) / tabla(t)   una figura o una tabla con su número y su pie («Fuente: …»)
// La numeración (P._n, f._n, t._n), las referencias {fig:id}/{pag:id}, el índice y las cifras de
// método ya llegan resueltas por scripts/informe.py: aquí solo se dibuja.
const C = (R, P) => {
  const M = R.meta, md = I.md, esc = I.esc;
  const marca = () => '<div class="marca"><div class="x">X</div><span class="handle">' + esc(M.handle) + "</span></div>";
  const cab = (der, opc) => '<div class="corrido' + (opc && opc.color ? " sobre-color" : "") + '"><span class="k acento">' + esc((opc && opc.izq) || M.corrido) + '</span><span class="k">' + esc(der || "") + "</span></div>";
  const pie = (izq, opc) => {
    const o = opc || {};
    return '<div class="pie-pag' + (o.color ? " sobre-color" : "") + '"><span class="mono">' + esc(izq || M.pie) + '</span><div class="autor">' +
      (P._mostrar_numero === false ? "" : '<span class="mono" style="font-weight:500">' + esc(P._n_texto) + "</span>") + (o.sin_marca ? "" : marca()) + "</div></div>";
  };

  const leyenda = (items) => !items || !items.length ? "" : '<div class="leyenda">' + items.map((it) =>
    '<span><i class="' + (it.forma === "linea" ? "linea" : "") + '" style="background:' + (it.forma === "linea" && (it.estilo || "base") === "base" ? "var(--fig-fuerte);opacity:.55" : { dest: "var(--fig-dest)", base: "var(--fig-base)", fuerte: "var(--fig-fuerte)" }[it.estilo || "base"]) + '"></i>' + esc(it.texto) + "</span>").join("") + "</div>";

  const fig = (f, opc) => {
    const o = opc || {}, tipo = f.tipo || "papel", compacto = !!o.compacto;
    const cap = '<figcaption><span class="figno">' + esc(f._n) + "</span><span>" + md(f.pie || "") +
      (tipo === "panel" ? "" : (f.pie ? " " : "") + "Fuente: " + esc(f.fuente) + ".") + (f.derivado ? " Incluye cálculo propio." : "") + "</span></figcaption>";
    if (tipo === "tarjeta") {
      return '<figure class="fig fig--tarjeta"' + (f.ancho ? ' style="width:' + f.ancho + 'px"' : "") + '><img class="tarjeta-img" src="' + esc(f._src) + '" alt="' + esc(f.alt || f.titular || "") + '">' + cap + "</figure>";
    }
    const vars = tipo === "panel" ? "--fig-dest:var(--a1);--fig-base:rgba(var(--ink-rgb),.45);--fig-fuerte:var(--ink)" : "--fig-dest:var(--barra);--fig-base:rgba(12,21,32,.2);--fig-fuerte:#0C1520";
    const titular = f.titular ? '<span class="titular' + (tipo === "panel" && !compacto ? " grande" : "") + '">' + md(Array.isArray(f.titular) ? f.titular.join("\n") : f.titular).replace(/\n/g, "<br>") + "</span>" : "";
    let cuerpo;
    if (!f.lista) cuerpo = I.grafico(f.grafico, tipo, f.alto);
    else {
      cuerpo = '<div style="display:flex;gap:32px;margin-top:20px"><div style="flex:none;width:' + (f.grafico.ancho || 400) + 'px">' + I.grafico(f.grafico, tipo, f.alto) + '</div><div style="flex:1;min-width:0;display:flex;flex-direction:column">' +
        '<div class="lista-reglas" style="border-top-width:1px">' + f.lista.map((it) =>
          '<div style="display:grid;grid-template-columns:22px minmax(0,1fr) auto;gap:10px;align-items:center;padding:9px 0"><span class="marcador">' + esc(it.n) + '</span><span style="font:' + (it.destacar ? 800 : 600) + ' 14px/1.25 Archivo,sans-serif">' + esc(it.nombre) + '</span><span style="font:700 ' + (it.destacar ? 14 : 12) + "px/1 'JetBrains Mono',monospace" + (it.destacar ? ";color:var(--tinta)" : "") + '">' + esc(it.valor) + "</span></div>").join("") +
        "</div>" + leyenda(f.leyenda).replace('class="leyenda"', 'class="leyenda" style="flex-direction:column;gap:8px;margin-top:18px;font:500 12px/1.3 \'JetBrains Mono\',monospace"') + "</div></div>";
    }
    const nota = f.nota ? '<span class="nota">' + md(f.nota) + "</span>" : "";
    const pieFig = tipo === "panel" ? '<div class="pie-fig"><span class="mono">Fuente: ' + esc(f.fuente) + "</span>" + marca() + "</div>" : "";
    return '<figure class="fig fig--' + tipo + '" style="' + vars + (o.estilo ? ";" + o.estilo : "") + '"><div class="marco' + (tipo === "panel" ? " panel" + (compacto ? " compacto" : "") : "") + '"' + (o.estilo ? ' style="flex:1"' : "") + ">" +
      (f.kicker ? '<span class="k acento">' + esc(f.kicker) + "</span>" : "") + titular + (f.lista ? "" : leyenda(f.leyenda)) + cuerpo + nota + pieFig + "</div>" + cap + "</figure>";
  };

  const tabla = (t) => {
    const cols = t.columnas;
    const th = cols.map((c) => '<th class="' + (c.num ? "num" : "") + '" style="text-align:' + (c.num ? "right" : "left") + (c.ancho ? ";width:" + c.ancho + "px" : "") + '">' + esc(c.t).replace(/\n/g, "<br>") + "</th>").join("");
    const filas = t.filas.map((f) => '<tr class="' + (f.dest ? "dest" : "") + (f.total ? " total" : "") + (f.detalle ? " con-detalle" : "") + '">' + f.c.map((v, i) => {
      const b = (f.b || []).includes(i) || (f.dest && i === 0);
      const chip = typeof v === "object" && v && v.chip;
      const contenido = chip ? '<span class="chip' + (v.chip === "ajustada" ? " borde" : "") + '">' + esc(v.chip) + "</span>" : esc(v == null ? "—" : v);
      return '<td class="' + (cols[i].num ? "num" : "") + (b ? " b" : "") + '"' + (f.dest && cols[i].num ? ' style="color:var(--tinta)"' : "") + ">" + contenido + "</td>";
    }).join("") + "</tr>" +
      // detalle: una segunda línea a lo ancho bajo la fila (qué encontramos, fuente), sin la columna del id
      (f.detalle ? '<tr class="detalle' + (f.dest ? " dest" : "") + '"><td></td><td colspan="' + (cols.length - 1) + '">' + md(f.detalle) + "</td></tr>" : "")).join("");
    const notas = t.notas && t.notas.length ? '<div class="notas-tabla">' + t.notas.map((n) => "<span><b>" + esc(n.m) + "</b> · " + md(n.texto) + "</span>").join("") + "</div>" : "";
    return '<figure class="fig tabla">' + (t.titulo ? '<span class="k acento">' + esc(t.titulo) + "</span>" : "") + '<table class="t">' + "<thead><tr>" + th + "</tr></thead><tbody>" + filas + "</tbody></table>" +
      '<figcaption><span class="figno">' + esc(t._n) + "</span><span>" + md(t.pie || "") + (t.pie ? " " : "") + "Fuente: " + esc(t.fuente) + ".</span></figcaption>" + notas + "</figure>";
  };

  const parrafos = (B) => I.lista(B.parrafos || B.texto).map((s, i) => i === 0 && B.capitular
    ? '<p class="p"><span class="capitular">' + esc(s[0]) + "</span>" + md(s.slice(1)) + "</p>"
    : '<p class="p">' + md(s) + "</p>").join("");

  const bloque = (B) => {
    switch (B.b) {
      case "titulo": return '<h3 class="t3">' + md(B.texto) + "</h3>";
      case "texto":
        if (B.margen) return '<div class="con-margen"><div class="texto">' + parrafos(B) + '</div><div class="margen">' +
          B.margen.map((m) => "<span><b>" + esc(m.termino) + "</b> · " + md(m.texto) + "</span>").join("") + "</div></div>";
        return parrafos(B);
      case "figura": return fig(B);
      case "figuras": return '<div class="dos">' + B.items.map((f) => fig(f, { compacto: true })).join("") + "</div>";
      case "tabla": return tabla(B);
      case "cita": return '<blockquote class="cita"><span class="k acento">' + esc(B.etiqueta) + '</span><span class="frase">' + md(B.texto) + "</span></blockquote>";
      case "caja": return '<div class="caja"><span class="k acento">' + esc(B.etiqueta) + '</span><div class="items">' + B.items.map((s) => "<span>" + md(s) + "</span>").join("") + "</div></div>";
      case "lectura": return '<div class="caja vertical lectura"><span class="k acento">' + esc(B.titulo) + '</span><div class="pasos">' +
        B.items.map((it) => '<div class="paso"><span class="marcador">' + esc(it.n) + "</span><span>" + md(it.texto) + "</span></div>").join("") + "</div>" +
        (B.nota ? '<span class="mono" style="color:rgba(12,21,32,.72)">' + md(B.nota) + "</span>" : "") + "</div>";
      default: throw new Error("bloque desconocido: " + B.b);
    }
  };
  const bloques = (lista) => I.lista(lista).map(bloque).join("");
  return { M, md, esc, cab, pie, marca, fig, tabla, bloques, bloque, leyenda };
};
