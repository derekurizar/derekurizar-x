// Páginas a sangre de color (la tarjeta hecha página): portada, aperturas de capítulo y contraportada.

// portada · kicker_izq, kicker_der, titulo, lead, cifra {valor, etiqueta, texto}; _capitulos y fuentes
PAGINAS.portada = (P, X) => {
  const caps = (P._capitulos || []).map((c) => '<div style="flex:1;border-top:1.5px solid var(--rule);padding-top:12px"><span style="opacity:.75">' + X.esc(c.numero) + "</span><br>" + X.esc(c.titulo) + "</div>").join("");
  return '<section class="pagina color">' +
    '<div class="corrido sobre-color"><span class="k acento">' + X.esc(P.kicker_izq) + '</span><span class="k">' + X.esc(P.kicker_der || "") + "</span></div>" +
    '<h1 class="t-portada">' + X.md(P.titulo) + "</h1>" +
    (P.lead ? '<p class="lead">' + X.md(P.lead) + "</p>" : "") +
    (P.cifra ? '<div style="margin-top:auto;display:flex;align-items:flex-end;gap:32px"><div class="cifra-heroe">' + X.esc(P.cifra.valor) + '</div>' +
      '<div style="display:flex;flex-direction:column;gap:10px;padding-bottom:14px;max-width:260px"><span class="k">' + X.esc(P.cifra.etiqueta) + '</span><span style="font:400 16px/1.4 Archivo,sans-serif">' + X.md(P.cifra.texto || "") + "</span></div></div>" : '<div style="margin-top:auto"></div>') +
    (caps ? '<div style="display:flex;gap:24px;margin-top:44px;font:500 12px/1.4 \'JetBrains Mono\',monospace">' + caps + "</div>" : "") +
    '<div class="pie-pag sobre-color" style="margin-top:40px"><span class="mono">Fuentes: ' + X.esc(P.fuentes) + "</span>" + X.marca() + "</div></section>";
};

// capitulo · variante "banda" (banda de color + cuerpo), "dividida" (columna de color + contenido)
// o "destacado" (página entera de color con un antes → después).
PAGINAS.capitulo = (P, X) => {
  const v = P.variante || "banda";
  if (v === "banda") {
    return '<section class="pagina sin-margen"><div class="banda sobre-color" style="height:' + (P.alto_banda || 492) + 'px;box-sizing:border-box;padding:56px 72px 48px;display:flex;flex-direction:column">' +
      '<div style="display:flex;justify-content:space-between"><span class="k acento">' + X.esc(P.kicker) + '</span><span class="k">' + X.esc(X.M.corto) + "</span></div>" +
      '<div style="margin-top:auto;display:flex;align-items:flex-end;justify-content:space-between;gap:24px"><div style="display:flex;flex-direction:column;gap:22px;max-width:470px">' +
      '<h2 style="margin:0;font:400 80px/.94 \'Instrument Serif\',Georgia,serif;letter-spacing:-.015em;text-wrap:balance">' + X.md(P.titulo) + "</h2>" +
      (P.lead ? '<p style="margin:0;font:400 17px/1.5 Archivo,sans-serif;text-wrap:pretty">' + X.md(P.lead) + "</p>" : "") + "</div>" +
      '<span style="font:400 220px/.78 \'Instrument Serif\',Georgia,serif;letter-spacing:-.03em;color:var(--a1)">' + X.esc(P.numero) + "</span></div></div>" +
      '<div style="flex:1;box-sizing:border-box;padding:30px 72px 48px;display:flex;flex-direction:column">' + X.bloques(P.bloques) + X.pie() + "</div></section>";
  }
  if (v === "dividida") {
    const secs = (P.secciones || []).map((s) => '<div style="display:flex;justify-content:space-between;gap:16px;padding:12px 0;font:400 15px/1.4 Archivo,sans-serif"><span>' + X.md(s.texto) + '</span><span class="mono" style="font-weight:500">' + X.esc(s.pag) + "</span></div>").join("");
    return '<section class="pagina sin-margen" style="flex-direction:row">' +
      '<div class="banda sobre-color" style="flex:none;width:320px;box-sizing:border-box;padding:56px 40px 48px 72px;display:flex;flex-direction:column">' +
      '<span class="k acento">' + X.esc(P.kicker) + '</span><span class="k" style="margin-top:8px">' + X.esc(P.kicker2 || "") + "</span>" +
      '<span style="margin-top:auto;font:400 184px/.76 \'Instrument Serif\',Georgia,serif;letter-spacing:-.04em;color:var(--a1)">' + X.esc(P.numero) + "</span>" +
      '<div style="margin-top:40px;padding-top:16px;border-top:1.5px solid var(--rule)">' + X.marca() + "</div></div>" +
      '<div style="flex:1;min-width:0;box-sizing:border-box;padding:56px 72px 48px 48px;display:flex;flex-direction:column">' +
      '<span class="k acento" style="padding-bottom:14px;border-bottom:1px solid var(--regla)">' + X.esc(X.M.corrido) + "</span>" +
      '<h2 style="margin:120px 0 0;font:400 68px/.94 \'Instrument Serif\',Georgia,serif;letter-spacing:-.015em;text-wrap:balance">' + X.md(P.titulo) + "</h2>" +
      (P.lead ? '<p style="margin:24px 0 0;font:400 17px/1.55 Archivo,sans-serif;text-wrap:pretty">' + X.md(P.lead) + "</p>" : "") +
      (secs ? '<div style="margin-top:48px"><span class="k acento" style="display:block;padding-bottom:10px">En este capítulo</span><div class="lista-reglas">' + secs + "</div></div>" : "") +
      '<div class="pie-pag"><span class="mono">' + X.esc(X.M.pie) + '</span><span class="mono" style="font-weight:500">' + X.esc(P._n_texto) + "</span></div></div></section>";
  }
  if (v === "destacado") {
    const D = P.dato;
    const flecha = '<svg viewBox="0 0 72 40" width="72" height="40" aria-hidden="true" style="display:block;margin-bottom:92px"><line x1="0" y1="20" x2="64" y2="20" stroke="currentColor" stroke-width="3"></line><polyline points="50,6 66,20 50,34" fill="none" stroke="currentColor" stroke-width="3"></polyline></svg>';
    return '<section class="pagina color">' +
      '<div class="corrido sobre-color"><span class="k acento">' + X.esc(P.kicker) + '</span><span class="k">' + X.esc(X.M.corto) + "</span></div>" +
      '<h2 style="margin:56px 0 0;font:400 88px/.92 \'Instrument Serif\',Georgia,serif;letter-spacing:-.02em;text-wrap:balance">' + X.md(P.titulo) + "</h2>" +
      (P.lead ? '<p class="lead" style="max-width:520px">' + X.md(P.lead) + "</p>" : "") +
      '<div style="margin-top:auto;display:flex;flex-direction:column;gap:18px"><span class="k">' + X.esc(D.kicker) + '</span><div style="display:flex;align-items:flex-end;gap:28px">' +
      '<div style="display:flex;flex-direction:column;gap:14px"><span style="font:400 200px/.8 \'Instrument Serif\',Georgia,serif;letter-spacing:-.03em;opacity:.6">' + X.esc(D.antes.valor) + '</span><span class="mono" style="font-weight:500">' + X.esc(D.antes.etiqueta) + "</span></div>" + flecha +
      '<div style="display:flex;flex-direction:column;gap:14px"><span style="font:400 200px/.8 \'Instrument Serif\',Georgia,serif;letter-spacing:-.03em;color:var(--a1)">' + X.esc(D.despues.valor) + '</span><span class="mono-b">' + X.esc(D.despues.etiqueta) + "</span></div></div></div>" +
      '<div style="margin-top:48px">' + X.pie("Fuente: " + P.fuente, { color: true }) + "</div></section>";
  }
  throw new Error("capitulo: variante desconocida " + v);
};

// contraportada · lema y ficha [[clave, valor], …] (la paleta se rellena sola).
PAGINAS.contraportada = (P, X) => {
  const ficha = (P.ficha || []).map(([k, v]) => '<div style="display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-top:1.5px solid var(--rule)"><span style="opacity:.8">' + X.esc(k) + "</span><span>" + X.esc(v) + "</span></div>").join("");
  return '<section class="pagina color">' +
    '<div class="corrido sobre-color"><span class="k acento">' + X.esc(X.M.numero_largo) + '</span><span class="k">' + X.esc(X.M.fecha) + "</span></div>" +
    '<p style="margin:64px 0 0;max-width:560px;font:400 64px/.98 \'Instrument Serif\',Georgia,serif;letter-spacing:-.015em;text-wrap:balance">' + X.md(P.lema) + "</p>" +
    '<div style="margin-top:auto;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 32px;font:400 12px/1.4 \'JetBrains Mono\',monospace;border-bottom:1.5px solid var(--rule)">' + ficha + "</div>" +
    '<div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:56px"><div style="display:flex;align-items:center;gap:16px"><div class="x" style="width:56px;height:56px;border-radius:12px;font-size:30px;background:var(--ink);color:var(--x-fg)">X</div><span style="font:600 32px/1 Archivo,sans-serif">' + X.esc(X.M.handle) + "</span></div>" +
    '<span class="mono" style="text-align:right">Tipografía: Instrument Serif,<br>Archivo y JetBrains Mono</span></div></section>';
};
