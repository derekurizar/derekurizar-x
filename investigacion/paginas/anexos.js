// Páginas de cierre: método y fuentes, glosario y la hoja de tarjetas del hilo.

// metodo · pasos [{titulo, texto}] (por defecto los tres del flujo; [] los omite), fuentes: false omite la lista, _cifras [{concepto, valor, veredicto, aparece}]
// (informe.py las arma desde datos.json por id), nota, _fuentes [texto] (meta.fuentes numeradas)
PAGINAS.metodo = (P, X) => {
  const pasos = (P.pasos || [
    { titulo: "Evidencia", texto: "Cada cifra llega con la URL de la fuente primaria, la cita textual y una copia local del archivo." },
    { titulo: "Segunda fuente", texto: "Un verificador parte de esa evidencia y busca una segunda fuente para cada cifra." },
    { titulo: "Veredicto", texto: "Solo entran las cifras verificadas o ajustadas; manda el valor final." },
  ]).map((p, i) => '<div class="celda" style="padding-top:12px;gap:8px"><span style="font:400 32px/1 \'Instrument Serif\',Georgia,serif;color:var(--tinta)">' + String(i + 1).padStart(2, "0") + '</span><span style="font:700 14px/1.2 Archivo,sans-serif">' + X.esc(p.titulo) + '</span><span style="font:400 14px/1.45 Archivo,sans-serif">' + X.md(p.texto) + "</span></div>").join("");
  const filas = (P._cifras || []).map((c) => ({ c: [c.concepto, c.valor, { chip: c.veredicto }, c.aparece] }));
  const tabla = '<table class="t" style="margin-top:12px;font-size:13px"><thead><tr><th>Cifra</th><th class="num">Valor</th><th>Veredicto</th><th class="num">Aparece en</th></tr></thead><tbody>' +
    filas.map((f) => "<tr><td>" + X.esc(f.c[0]) + '</td><td class="num" style="font-weight:700">' + X.esc(f.c[1]) + '</td><td><span class="chip' + (f.c[2].chip === "ajustada" ? " borde" : "") + '">' + X.esc(f.c[2].chip) + '</span></td><td class="num" style="font-size:12px">' + X.esc(f.c[3]) + "</td></tr>").join("") + "</tbody></table>";
  const fuentes = (P._fuentes || []).map((f, i) => '<li style="display:flex;gap:14px"><span style="flex:none;width:20px;font:700 12px/1.6 \'JetBrains Mono\',monospace;color:var(--tinta)">' + (i + 1) + "</span><span>" + X.md(f) + "</span></li>").join("");
  return '<section class="pagina">' + X.cab(P.seccion || "Anexo") + '<h2 class="t2">' + X.esc(P.titulo || "Método y fuentes") + "</h2>" +
    '<div class="rejilla3" style="margin-top:28px">' + pasos + "</div>" +
    '<div style="display:flex;align-items:center;gap:10px;margin-top:20px;font:500 12px/1 \'JetBrains Mono\',monospace"><span class="chip">verificada</span><span class="chip borde">ajustada</span><span class="chip tachado">no confirmada</span><span class="gris">· nunca aparece en el informe</span></div>' +
    '<span class="k acento" style="margin-top:32px">Cifras usadas</span>' + tabla +
    (P.nota ? '<span class="mono gris" style="margin-top:8px">' + X.md(P.nota) + "</span>" : "") +
    (P.fuentes === false ? "" : '<span class="k acento" style="margin-top:28px">Fuentes</span><ol style="margin:12px 0 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:8px;font:400 13px/1.45 Archivo,sans-serif">' + fuentes + "</ol>") +
    X.pie() + "</section>";
};

// glosario · terminos [{t, d}] (columna izquierda y, si sobran, arriba de la derecha), siglas [{s, d}]
PAGINAS.glosario = (P, X) => {
  const corte = P.corte || Math.ceil(P.terminos.length * 0.7);
  const term = (lst) => lst.map((x, i) => '<div style="display:flex;flex-direction:column;gap:4px;padding:12px 0;border-top:' + (i === 0 ? "1.5px solid var(--tp)" : "1px solid var(--regla)") + '"><span style="font:400 22px/1.1 \'Instrument Serif\',Georgia,serif;color:var(--tinta)">' + X.esc(x.t) + '</span><span style="font:400 13px/1.5 Archivo,sans-serif">' + X.md(x.d) + "</span></div>").join("");
  const siglas = (P.siglas || []).map((x) => '<b style="padding:9px 0;border-bottom:1px solid var(--regla);font:700 12px/1.6 \'JetBrains Mono\',monospace">' + X.esc(x.s) + '</b><span style="padding:9px 0;border-bottom:1px solid var(--regla)">' + X.esc(x.d) + "</span>").join("");
  return '<section class="pagina">' + X.cab(P.seccion || "Anexo") + '<h2 class="t2">' + X.esc(P.titulo || "Glosario") + "</h2>" +
    '<div class="rejilla2" style="margin-top:28px;align-items:start"><div style="display:flex;flex-direction:column;border-bottom:1.5px solid var(--tp)">' + term(P.terminos.slice(0, corte)) + "</div>" +
    '<div style="display:flex;flex-direction:column">' + term(P.terminos.slice(corte)) +
    (siglas ? '<span class="k acento" style="margin-top:20px;padding-bottom:10px;border-bottom:1.5px solid var(--tp)">Siglas</span><div style="display:grid;grid-template-columns:72px minmax(0,1fr);gap:0 12px;font:400 13px/1.45 Archivo,sans-serif">' + siglas + "</div>" : "") +
    "</div></div>" + X.pie() + "</section>";
};

// tarjetas · titulo, lead, items [{_src, n, beat, titulo, alt}], tuit {gancho, texto, publicado}
PAGINAS.tarjetas = (P, X) => {
  const it = P.items.map((t) => '<figure style="display:flex;flex-direction:column;gap:8px"><img src="' + X.esc(t._src) + '" alt="' + X.esc(t.alt || t.titulo) + '" style="display:block;width:156px;height:156px;object-fit:cover"><figcaption style="display:flex;flex-direction:column;gap:3px"><span class="mono-b" style="line-height:1;color:var(--tinta)">' + X.esc(t.n + " · " + t.beat) + '</span><span style="font:400 13px/1.35 Archivo,sans-serif">' + X.esc(t.titulo) + "</span></figcaption></figure>").join("");
  const T = P.tuit;
  return '<section class="pagina">' + X.cab(P.seccion || "Anexo") + '<h2 class="t2">' + X.esc(P.titulo) + "</h2>" + (P.lead ? '<p class="p">' + X.md(P.lead) + "</p>" : "") +
    '<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px 16px;margin-top:28px">' + it + "</div>" +
    (T ? '<div class="caja" style="margin-top:36px"><span class="k acento">Tuit 1</span><div class="items" style="gap:10px"><span style="font:400 italic 22px/1.25 \'Instrument Serif\',Georgia,serif">' + X.md(T.gancho) + "</span><span style=\"font:400 14px/1.5 Archivo,sans-serif\">" + X.md(T.texto) + '</span><span class="mono" style="color:rgba(12,21,32,.72)">' + X.esc(T.publicado) + "</span></div></div>" : "") +
    X.pie() + "</section>";
};
