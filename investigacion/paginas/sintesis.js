// Páginas de síntesis: índice (se genera solo), resumen, tablero de cifras clave y conclusiones.

// indice · titulo; _entradas [{clase, numero, titulo, desc, pag}] · _anexos · _figuras [{no, titulo, pag}] · leer []
PAGINAS.indice = (P, X) => {
  const e = P._entradas || [];
  const figs = (P._figuras || []).map((f) => '<div style="display:flex;gap:10px;break-inside:avoid"><b style="flex:none;width:64px">' + X.esc(f.no) + '</b><span style="flex:1">' + X.esc(f.titulo) + "</span><span>" + X.esc(f.pag) + "</span></div>").join("");
  // Índice largo (informe.continuar_indice): la lista de figuras y tablas va en hojas propias a dos columnas.
  if (P._indice_cont) {
    const nC = (P._figuras || []).length;
    return '<section class="pagina">' + X.cab("Contenido") + '<h1 class="t1" style="margin-top:28px;font-size:48px">' + X.esc(P.titulo) + (P._hojas_figuras > 1 ? " (" + P._indice_cont + "/" + P._hojas_figuras + ")" : "") + "</h1>" +
      '<div style="display:grid;grid-auto-flow:column;grid-template-rows:repeat(' + Math.ceil(nC / 2) + ',auto);column-gap:28px;row-gap:6px;margin-top:24px;font:400 12px/1.35 \'JetBrains Mono\',monospace">' + figs + "</div>" + X.pie() + "</section>";
  }
  // Con más de seis capítulos, los capítulos van a dos columnas y sin descripción.
  const compacto = e.filter((it) => it.clase === "capitulo").length > 6;
  const fila = (it) => it.clase === "capitulo" && compacto
    ? '<div style="display:grid;grid-template-columns:44px minmax(0,1fr) 32px;gap:10px;align-items:baseline;padding:8px 0;border-bottom:1px solid var(--regla-f)"><span style="font:400 30px/.9 \'Instrument Serif\',Georgia,serif;color:var(--tinta)">' + X.esc(it.numero) + '</span><span style="font:400 19px/1.15 \'Instrument Serif\',Georgia,serif">' + X.md(it.titulo) + '</span><span class="mono" style="text-align:right;font-weight:500">' + X.esc(it.pag) + "</span></div>"
    : it.clase === "capitulo"
    ? '<div style="display:grid;grid-template-columns:72px minmax(0,1fr) 48px;gap:16px;align-items:baseline;padding:11px 0"><span style="font:400 44px/.9 \'Instrument Serif\',Georgia,serif;color:var(--tinta)">' + X.esc(it.numero) + '</span><div style="display:flex;flex-direction:column;gap:6px"><span style="font:400 28px/1.1 \'Instrument Serif\',Georgia,serif">' + X.md(it.titulo) + '</span><span style="font:400 14px/1.45 Archivo,sans-serif">' + X.md(it.desc || "") + '</span></div><span class="mono" style="text-align:right;font-weight:500">' + X.esc(it.pag) + "</span></div>"
    : '<div style="display:flex;justify-content:space-between;align-items:baseline;padding:12px 0"><span style="font:400 26px/1.1 \'Instrument Serif\',Georgia,serif">' + X.md(it.titulo) + '</span><span class="mono" style="font-weight:500">' + X.esc(it.pag) + "</span></div>";
  // Dos entradas simples seguidas (p. ej. Resumen y Cifras clave) comparten fila.
  const filas = [];
  for (let i = 0; i < e.length; i++) {
    if (compacto && e[i].clase === "capitulo") {
      const caps = [];
      while (i < e.length && e[i].clase === "capitulo") caps.push(fila(e[i++]));
      i--;
      filas.push('<div style="display:grid;grid-auto-flow:column;grid-template-rows:repeat(' + Math.ceil(caps.length / 2) + ',auto);column-gap:28px;padding:4px 0">' + caps.join("") + "</div>");
    } else if (e[i].clase !== "capitulo" && e[i + 1] && e[i + 1].clase !== "capitulo") {
      filas.push('<div class="rejilla2" style="padding:0">' + fila(e[i]) + fila(e[i + 1]) + "</div>");
      i++;
    } else filas.push(fila(e[i]));
  }
  const anexos = (P._anexos || []).map((a) => '<div style="display:flex;flex-direction:column;gap:4px;padding-top:8px;border-top:1px solid var(--regla-f)"><span style="font-weight:700">' + X.esc(a.pag) + "</span><span>" + X.esc(a.titulo) + "</span></div>").join("");
  // Con más de 10 figuras y tablas, la lista va a dos columnas (si no, con 5 capítulos solo caben 11).
  // Con más de 14 figuras y tablas, la caja «Cómo leer» pasa arriba a lo ancho y la lista va a todo el ancho en
  // dos columnas (a una columna caben ~12 con tres capítulos; la caja a lo ancho cuesta ~80 px, así que solo compensa desde 15).
  const nF = (P._figuras || []).length, fuera = !!P._hojas_figuras, largo = nF > 14 || fuera;
  const leerCaja = (estilo) => (P.leer ? '<div style="' + estilo + 'padding:18px 20px;background:var(--suave);display:flex;' + (largo ? 'gap:24px;align-items:flex-start' : 'flex-direction:column;gap:10px') + '"><span class="k acento"' + (largo ? ' style="flex:none;width:104px;padding-top:3px"' : '') + '>Cómo leer</span>' +
    (largo ? '<div style="display:flex;flex-direction:column;gap:6px">' : '') + P.leer.map((s) => '<span style="font:400 13px/1.5 Archivo,sans-serif">' + X.md(s) + "</span>").join("") + (largo ? "</div>" : "") + "</div>" : "");
  const listaFigs = fuera
    ? '<span style="margin-top:12px;font:400 15px/1.45 Archivo,sans-serif">La lista de figuras y tablas sigue en la página ' + X.esc(P._figuras_en) + ".</span>"
    : largo
    ? '<div style="display:grid;grid-auto-flow:column;grid-template-rows:repeat(' + Math.ceil(nF / 2) + ',auto);column-gap:28px;row-gap:4px;margin-top:12px;font:400 12px/1.35 \'JetBrains Mono\',monospace">' + figs + "</div>"
    : '<div style="display:flex;flex-direction:column;gap:4px;margin-top:12px;font:400 12px/1.35 \'JetBrains Mono\',monospace">' + figs + "</div>";
  return '<section class="pagina">' + X.cab("Contenido") + '<h1 class="t1" style="margin-top:28px;font-size:64px">' + X.esc(P.titulo || "Contenido") + "</h1>" +
    '<div class="lista-reglas" style="margin-top:28px">' + filas.join("") + "</div>" +
    (anexos ? '<div style="display:grid;grid-template-columns:repeat(' + Math.min(5, P._anexos.length) + ',minmax(0,1fr));gap:16px;margin-top:16px;font:400 12px/1.4 \'JetBrains Mono\',monospace">' + anexos + "</div>" : "") +
    (largo ? leerCaja("margin-top:24px;") : "") +
    '<div style="display:flex;gap:32px;margin-top:' + (largo ? 24 : 32) + 'px"><div style="flex:1;display:flex;flex-direction:column"><span class="k acento">Figuras y tablas</span>' + listaFigs + "</div>" +
    (largo ? "" : leerCaja("flex:none;width:232px;align-self:flex-start;")) +
    "</div>" + X.pie() + "</section>";
};

// resumen · tesis, cifras [{kicker, valor, texto, fuente, id}], no_afirma []
PAGINAS.resumen = (P, X) => {
  const cif = P.cifras.map((c) => '<div class="celda"><span class="k">' + X.esc(c.kicker) + '</span><span class="cifra-g">' + X.esc(c.valor) + '</span><span style="font:400 15px/1.45 Archivo,sans-serif">' + X.md(c.texto) + '</span><span class="mono gris">Fuente: ' + X.esc(c.fuente) + "</span></div>").join("");
  return '<section class="pagina">' + X.cab("Resumen") + '<h1 class="t1" style="margin-top:36px">' + X.esc(P.titulo || "Resumen") + "</h1>" +
    '<div style="display:flex;gap:24px;margin-top:28px"><span class="k acento" style="flex:none;width:128px;padding-top:6px">Tesis</span><p style="margin:0;flex:1;font:400 19px/1.55 Archivo,sans-serif;text-wrap:pretty">' + X.md(P.tesis) + "</p></div>" +
    '<div class="rejilla2" style="margin-top:32px;row-gap:28px">' + cif + "</div>" +
    (P.no_afirma ? X.bloque({ b: "caja", etiqueta: "No afirma", items: P.no_afirma }).replace('class="caja"', 'class="caja" style="margin-top:32px"') : "") +
    X.pie() + "</section>";
};

// tablero · titulo, subtitulo, cifras [{kicker, valor, contexto, grafico, fuente, id}]
PAGINAS.tablero = (P, X) => {
  const t = P.cifras.map((c) => '<div class="celda" style="padding-top:12px;gap:8px"><span class="k">' + X.esc(c.kicker) + '</span>' +
    '<div style="display:flex;align-items:baseline;gap:10px"><span style="font:400 48px/.9 \'Instrument Serif\',Georgia,serif;color:var(--tinta)">' + X.esc(c.valor) + '</span><span style="font:400 14px/1.3 Archivo,sans-serif">' + X.md(c.contexto || "") + "</span></div>" +
    '<div style="margin-top:6px">' + I.grafico(c.grafico, "papel").replace('class="grafico"', 'class="grafico" style="margin-top:0"') + "</div>" +
    '<span class="mono gris">Fuente: ' + X.esc(c.fuente) + "</span></div>").join("");
  return '<section class="pagina">' + X.cab(P.seccion || "Cifras clave") +
    '<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-top:36px"><h2 class="t2" style="margin:0">' + X.esc(P.titulo || "Cifras clave") + '</h2><span style="max-width:280px;padding-bottom:6px;font:400 14px/1.45 Archivo,sans-serif">' + X.md(P.subtitulo || "") + "</span></div>" +
    '<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:36px 24px;margin-top:32px">' + t + "</div>" + X.pie() + "</section>";
};

// conclusiones · hallazgos [{titulo, texto, ref}], cierre, no_afirma [], limites []
PAGINAS.conclusiones = (P, X) => {
  const h = P.hallazgos.map((x, i) => '<li style="display:grid;grid-template-columns:56px minmax(0,1fr) 96px;gap:16px;align-items:baseline;padding:14px 0"><span style="font:400 36px/.9 \'Instrument Serif\',Georgia,serif;color:var(--tinta)">' + (i + 1) + '</span><div style="display:flex;flex-direction:column;gap:4px"><span style="font:700 16px/1.35 Archivo,sans-serif">' + X.md(x.titulo) + '</span><span style="font:400 15px/1.5 Archivo,sans-serif">' + X.md(x.texto) + '</span></div><span class="mono" style="text-align:right">' + X.esc(x.ref || "") + "</span></li>").join("");
  const col = (titulo, items) => '<div style="display:flex;flex-direction:column;gap:12px"><span class="k acento" style="padding-bottom:10px;border-bottom:1.5px solid var(--tp)">' + X.esc(titulo) + "</span>" + items.map((s) => '<span style="font:400 13px/1.5 Archivo,sans-serif">' + X.md(s) + "</span>").join("") + "</div>";
  return '<section class="pagina">' + X.cab(P.titulo || "Conclusiones") + '<h2 class="t2">' + X.esc(P.titulo || "Conclusiones") + "</h2>" +
    '<ol class="lista-reglas" style="margin:24px 0 0;padding:0;list-style:none">' + h + "</ol>" +
    (P.cierre ? '<p style="margin:28px 0 0;max-width:600px;font:400 italic 28px/1.2 \'Instrument Serif\',Georgia,serif;text-wrap:balance">' + X.md(P.cierre) + "</p>" : "") +
    '<div class="rejilla2" style="margin-top:32px">' + col("Este informe no afirma", P.no_afirma || []) + col("Límites de los datos", P.limites || []) + "</div>" + X.pie() + "</section>";
};
