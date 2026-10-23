// Módulo común de las páginas de escena de /video (video/*.html), objeto global V: parámetros de la URL (?n=, ?f=45,
// ?portada=1), curvas, carga de escenas.json, DATA de una tarjeta, golpe de arriba, barra de progreso y subtítulos.
// Cada página lo carga antes de su script y usa V.*; lo propio de la escena (cifra, mapa, filas…) sigue en la página.
// Todo es función de t (seek), sin relojes: los clips salen idénticos en serie y en paralelo. Lo sirve
// scripts/video_grabar.js; la hoja común es video/comun.css.
const V = (() => {
  const q = new URLSearchParams(location.search);
  const n = Number(q.get('n')), F45 = q.get('f') === '45', portada = q.get('portada') === '1';
  if (F45) document.documentElement.classList.add('f45');
  if (portada) document.documentElement.classList.add('portada');

  const clamp = (x) => Math.max(0, Math.min(1, x));
  const eo = (x) => 1 - Math.pow(1 - clamp(x), 3);                                  // ease-out cúbica
  const prog = (t, a, b) => (t >= b ? 1 : eo((t - a) / Math.max(0.001, b - a)));    // avance de a a b, con curva
  const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
  // palabra comparable: minúsculas, sin tildes ni puntuación
  const normal = (w) => (w || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
  // subtítulos en trozos de ≤ 26 caracteres (caben en la columna segura); corta también tras puntuación fuerte
  const trocear = (ps) => { const out = []; let cur = [];
    for (const p of ps) { const largo = cur.map((x) => x.text).join(' ').length + p.text.length + 1;
      if (cur.length && largo > 26) { out.push(cur); cur = []; }
      cur.push(p); if (/[.?:;…]$/.test(p.text)) { out.push(cur); cur = []; } }
    if (cur.length) out.push(cur); return out; };

  // escenas.json → { todo, S, trozos }: la paleta como variables CSS (--bg, --ink, --resalte-bg…) y la escena ?n=N
  // (o la que elija `buscar`)
  async function cargar(buscar) {
    const todo = await (await fetch('escenas.json')).json();
    for (const [k, v] of Object.entries(todo.colores)) document.documentElement.style.setProperty('--' + k.replace('_', '-'), v);
    const S = todo.escenas.find(buscar || ((e) => e.n === n));
    return { todo, S, trozos: trocear(S.palabras) };
  }
  // el objeto DATA de tarjeta_N.html (el tuit_N.html del hilo)
  async function tarjeta(tuit) {
    const html = await (await fetch('tarjeta_' + tuit + '.html')).text();
    const m = html.match(/const DATA = (\{[\s\S]*?\n\});/);
    if (!m) throw new Error('tarjeta_' + tuit + '.html no tiene un bloque const DATA = {…};');
    return new Function('return ' + m[1])();
  }

  // golpe de arriba (S.arriba, palabras con start): se pinta, se achica hasta que golpe + barra terminen antes de
  // `limite` (y de página) y entra deslizándose desde la izquierda, cada palabra subiendo
  const pintarGolpe = (S) => { document.getElementById('golpe').innerHTML = S.arriba.map((w) => `<span>${esc(w.text)}</span>`).join(''); };
  const ajustarGolpe = (S, limite) => {
    const g = document.getElementById('golpe'), arriba = document.getElementById('arriba');
    for (let fs = 72; S.arriba.length && fs > 48 && arriba.offsetTop + arriba.offsetHeight > limite - 16; fs -= 4) g.style.fontSize = fs + 'px';
  };
  const seekGolpe = (t, S) => {
    const pg = eo((t - (S.arriba.length ? S.arriba[0].start : 0) + 0.15) / 0.4);
    document.getElementById('golpe').style.transform = `translateX(${(1 - pg) * -60}px)`;
    [...document.querySelectorAll('#golpe span')].forEach((s, i) => {
      const p = eo((t - S.arriba[i].start + 0.15) / 0.3); s.style.opacity = p; s.style.transform = `translateY(${(1 - p) * 16}px)`; });
  };

  // barra de progreso: escenas anteriores llenas, la actual (k) avanza con el tiempo, las siguientes vacías
  const pintarProgreso = (todo) => { document.getElementById('progreso').innerHTML = todo.escenas.map(() => '<i><b></b></i>').join(''); };
  const seekProgreso = (t, k, dur) => {
    [...document.querySelectorAll('#progreso b')].forEach((b, i) => { b.style.width = (i + 1 < k ? 100 : i + 1 === k ? 100 * clamp(t / dur) : 0) + '%'; });
  };

  // subtítulos: el trozo que suena (se oculta tras la voz, o cuando `ocultar(trozo, t)` lo pide); la palabra que se
  // dice resaltada, las ya dichas normales, las que vienen apagadas
  const palabras = (ps, t) => ps.map((p) => `<span class="${t >= p.start && t < p.end + 0.08 ? 'ahora' : t >= p.end ? '' : 'no'}${p.num ? ' cifra' : ''}">${esc(p.text)}</span>`).join(' ');
  const subtitulos = (t, S, trozos, o = {}) => {
    const k = trozos.findIndex((c, j) => t >= c[0].start - 0.05 && t < ((trozos[j + 1] || [{ start: 1e9 }])[0].start - 0.05));
    const tr = trozos[k];
    const oculto = !tr || t > S.fin_voz + 0.4 || (o.ocultar && o.ocultar(tr, t));
    document.getElementById('subs').innerHTML = oculto ? '' : palabras(tr, t);
  };
  // variante del cierre: una ventana de 5 palabras alrededor de la que suena
  const subtitulosVentana = (t, S) => {
    const ini = S.palabras.findIndex((p) => t < p.end + 0.08);
    const k = ini < 0 ? S.palabras.length - 1 : ini;
    const ventana = S.palabras.slice(Math.max(0, k - 2), k + 3);
    document.getElementById('subs').innerHTML = t > S.fin_voz + 0.4 ? '' : palabras(ventana, t);
  };

  // ZONA SEGURA (variables de comun.css): x en [corte, ancho − corte]; desde iconosY, x ≤ iconosX; y en [sup, fin], con
  // fin = top de #subs − 30 si la página tiene subtítulos. Las páginas que dimensionan en JS la leen con V.zona().
  const zona = () => {
    const cs = getComputedStyle(document.documentElement), px = (k) => parseFloat(cs.getPropertyValue(k)) || 0;
    const ancho = document.body.clientWidth, alto = document.body.clientHeight, subs = document.getElementById('subs');
    const fin = window.__zonaFin || (subs ? Math.min(alto, subs.offsetTop - 30) : px('--fin'));   // __zonaFin: prueba del gate
    return { ancho, alto, izq: px('--izq'), der: ancho - px('--der'), corte: px('--corte'), sup: px('--sup'), fin,
      iconosX: px('--iconos-x'), iconosY: px('--iconos-y') };
  };
  // gate V13: lo visible (texto, SVG, imágenes y cajas con fondo o borde; también dentro de la tarjeta del iframe,
  // con su transform) fuera de la zona. Cuenta lo que se ve al menos a media opacidad (lo que entra o sale
  // deslizándose, más tenue, es movimiento). Fuera de la medición: subtítulos, barra de progreso, lo marcado con
  // data-fuera-de-zona (fondos a sangre) y la tarjeta durante un foco (#ventana[data-foco]: solo la caja enfocada;
  // «mov» = la cámara pasa de un foco a otro). Devuelve [{que, caja: [x0, y0, x1, y1], regla}].
  const medirZona = () => {
    const Z = zona(), fallas = [], TOL = 2;
    const fuera = (el) => el.closest && el.closest('#subs, #progreso, [data-fuera-de-zona]');
    const visible = (el, win) => { let op = 1; for (let x = el; x && x.nodeType === 1; x = x.parentElement) {
      const c = win.getComputedStyle(x); if (c.display === 'none' || c.visibility === 'hidden') return false; op *= parseFloat(c.opacity); }
      return op >= 0.5; };
    const recorte = (el, win, r) => { for (let x = el.parentElement; x && r; x = x.parentElement) {
      const c = win.getComputedStyle(x); if (c.overflow === 'visible' && c.overflowX === 'visible' && c.overflowY === 'visible') continue;
      const b = x.getBoundingClientRect(); r = [Math.max(r[0], b.left), Math.max(r[1], b.top), Math.min(r[2], b.right), Math.min(r[3], b.bottom)];
      if (r[0] >= r[2] || r[1] >= r[3]) return null; }
      return r; };
    const conFondo = (c) => { const m = c.backgroundColor.match(/[\d.]+/g); return (m && (m.length < 4 || +m[3] > 0.05) && c.backgroundColor !== 'transparent')
      || parseFloat(c.borderTopWidth) + parseFloat(c.borderBottomWidth) + parseFloat(c.borderLeftWidth) + parseFloat(c.borderRightWidth) > 0; };
    const revisar = (que, r) => {
      const [x0, y0, x1, y1] = r;
      if ((x1 - x0) * (y1 - y0) < 6) return;
      const reglas = [];
      if (x0 < Z.corte - TOL || x1 > Z.ancho - Z.corte + TOL) reglas.push('sale del recorte lateral (' + Z.corte + ' px por lado)');
      if (y0 < Z.sup - TOL) reglas.push('entra en la barra de arriba (y < ' + Z.sup + ')');
      if (y1 > Z.fin + TOL) reglas.push('baja de y ' + Z.fin + ' (subtítulos y texto de la app)');
      if (y1 > Z.iconosY + TOL && x1 > Z.iconosX + TOL) reglas.push('entra en la columna de iconos (x > ' + Z.iconosX + ' desde y ' + Z.iconosY + ')');
      if (reglas.length) fallas.push({ que: que.slice(0, 40), caja: r.map((v) => Math.round(v)), regla: reglas.join('; ') });
    };
    // recorre un documento; `map` lleva las cajas del iframe a coordenadas de la página (translate + escala) y `clip`
    // es el recorte del iframe en la página
    const recorrer = (doc, win, map, clip) => {
      const corta = (r) => { r = map(r); if (!clip) return r; const q = [Math.max(r[0], clip[0]), Math.max(r[1], clip[1]), Math.min(r[2], clip[2]), Math.min(r[3], clip[3])];
        return q[0] < q[2] && q[1] < q[3] ? q : null; };
      const w = doc.createTreeWalker(doc.body, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
      for (let nodo = w.currentNode; nodo; nodo = w.nextNode()) {
        if (nodo.nodeType === 3) {
          if (!nodo.textContent.trim() || fuera(nodo.parentElement) || !visible(nodo.parentElement, win)) continue;
          const rg = doc.createRange(); rg.selectNodeContents(nodo); const b = rg.getBoundingClientRect();
          let r = recorte(nodo, win, [b.left, b.top, b.right, b.bottom]);   // el texto se recorta desde su propio padre
          if (r && (r = corta(r))) revisar(nodo.textContent.trim(), r);
          continue;
        }
        const el = nodo, tag = el.tagName.toLowerCase();
        if (fuera(el)) continue;
        if (el.dataset && el.dataset.foco) { if (el.dataset.foco !== 'mov') revisar('foco de la tarjeta', JSON.parse(el.dataset.foco)); continue; }
        if (el.closest && el.closest('[data-foco]:not([data-foco=""])')) continue;   // durante un foco, lo demás sale de cuadro a propósito
        if (tag === 'iframe') {
          const d = el.contentDocument; if (!d || !d.body || !visible(el, win)) continue;
          const b = el.getBoundingClientRect(), k = b.width / (el.clientWidth || 1);
          const sub = (r) => map([b.left + r[0] * k, b.top + r[1] * k, b.left + r[2] * k, b.top + r[3] * k]);
          const cl = recorte(el, win, [b.left, b.top, b.right, b.bottom]);
          if (cl) recorrer(d, el.contentWindow, sub, map(cl));
          continue;
        }
        if (['script', 'style', 'defs', 'clippath', 'lineargradient', 'mask'].includes(tag)) continue;
        if (el.parentElement && el.parentElement.closest('svg')) continue;   // el SVG cuenta entero
        const hoja = tag === 'svg' || tag === 'img' || tag === 'canvas' || (!el.firstElementChild && conFondo(win.getComputedStyle(el)));
        if (!hoja || !visible(el, win)) continue;
        const b = el.getBoundingClientRect();
        let r = recorte(el, win, [b.left, b.top, b.right, b.bottom]);
        if (r && (r = corta(r))) revisar(tag === 'svg' ? 'svg' + (el.id ? '#' + el.id : '') : '<' + tag + (el.id ? '#' + el.id : '') + '>', r);
      }
    };
    recorrer(document, window, (r) => r, null);
    return fallas;
  };

  return { n, F45, portada, clamp, eo, prog, esc, normal, trocear, cargar, tarjeta, pintarGolpe, ajustarGolpe, seekGolpe,
    pintarProgreso, seekProgreso, subtitulos, subtitulosVentana, zona, medirZona };
})();
