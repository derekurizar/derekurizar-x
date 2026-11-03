// Módulo común de las páginas de escena de /video (video/*.html), objeto global V: parámetros de la URL (?n=, ?f=45,
// ?portada=1), curvas, carga de escenas.json, DATA de una tarjeta, golpe de arriba, barra de progreso, subtítulos y el
// rótulo de acto de /historia (S.R: pintarActo, seekActo, desfase) y el chip o sello (S.chip, S.ejemplo: V.chip).
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
  // palabras vacías: un trozo de subtítulo no termina en ellas y no cuentan al comparar con la pantalla
  const VACIAS = new Set(['a', 'al', 'con', 'de', 'del', 'e', 'el', 'en', 'es', 'la', 'las', 'lo', 'los', 'o', 'para', 'por', 'que', 'se', 'su', 'sus', 'u', 'un', 'una', 'y']);
  // subtítulos en trozos de ≤ 26 caracteres (caben en la columna segura); corta también tras puntuación fuerte, y si el
  // corte por largo deja al final una palabra vacía («el», «de», «y»), esa pasa al trozo siguiente
  const trocear = (ps) => { const out = []; let cur = [];
    for (const p of ps) { const largo = cur.map((x) => x.text).join(' ').length + p.text.length + 1;
      if (cur.length && largo > 26) {
        const lleva = cur.length > 1 && VACIAS.has(normal(cur[cur.length - 1].text)) ? [cur.pop()] : [];
        out.push(cur); cur = lleva; }
      cur.push(p); if (/[.?:;…]$/.test(p.text)) { out.push(cur); cur = []; } }
    if (cur.length) out.push(cur); return out; };

  // CHIP o sello en pantalla («Ejemplo», «MITO», «Parte 2 de 4», «#3 · Economía»): chip({texto, tono, desde, pos, id})
  // · tono: «ink» (crema con borde tenue, el de «Ejemplo»), «acento» (el acento del tema) o «tenue» (apagado)
  // · pos: «arriba» (a la derecha, sobre la columna de iconos: x ≤ 1023, y ≥ 232) o «abajo» (a la izquierda, sobre los
  //   subtítulos: termina antes de --fin); varios chips en la misma posición se apilan
  // · desde: segundo de la escena en que entra (fundido de 0.25 s; antes no se ve ni lo mide V13); 0 = desde el cuadro 0
  // Va en un contenedor .vchips (sin fondo) y cada chip lleva borde: V13 (medirZona) lo mide como cualquier caja. Solo
  // colores por variables. Lo pinta V.cargar desde S.chip (y S.ejemplo); las páginas no hacen nada: lo mueve
  // V.seekProgreso, que todas llaman en su seek. → el elemento.
  const CHIPS = [];
  const TONOS = ['ink', 'acento', 'tenue'];
  function chip(o = {}) {
    if (o.id && document.getElementById(o.id)) return document.getElementById(o.id);
    const pos = o.pos === 'abajo' ? 'abajo' : 'arriba';
    let caja = document.querySelector('.vchips.' + pos);
    if (!caja) { caja = document.createElement('div'); caja.className = 'vchips ' + pos; document.body.appendChild(caja); }
    const el = document.createElement('div');
    if (o.id) el.id = o.id;
    el.className = 'vchip ' + (TONOS.includes(o.tono) ? o.tono : 'ink');
    el.textContent = String(o.texto ?? '');
    caja.appendChild(el);
    const desde = Math.max(0, Number(o.desde) || 0);
    CHIPS.push({ el, desde });
    if (desde > 0) el.style.opacity = '0';
    return el;
  }
  const seekChips = (t) => { for (const c of CHIPS) if (c.desde > 0) c.el.style.opacity = eo((t - c.desde) / 0.25).toFixed(3); };

  // escenas.json → { todo, S, trozos }: la paleta como variables CSS (--bg, --ink, --resalte-bg…) y la escena ?n=N
  // (o la que elija `buscar`)
  async function cargar(buscar) {
    const todo = await (await fetch('escenas.json')).json();
    for (const [k, v] of Object.entries(todo.colores)) document.documentElement.style.setProperty('--' + k.replace('_', '-'), v);
    const S = todo.escenas.find(buscar || ((e) => e.n === n));
    // Noche: el acto 2 de /historia (el nudo) baja el fondo a fondo_acto2; la escena lo hereda entera (cuerpo y velos)
    if (S && S.acto === 2 && todo.colores.fondo_acto2) document.documentElement.style.setProperty('--bg', todo.colores.fondo_acto2);
    // /explica: una escena con números de ejemplo (ilustrativos, calculados por scripts/explica.py) lleva el chip «Ejemplo»
    // fijo arriba a la derecha, fuera de la columna del golpe y dentro de la zona segura (S.ejemplo → chip)
    if (S && S.ejemplo) chip({ texto: 'Ejemplo', tono: 'ink', id: 'ejemplo' });
    // cualquier escena: el chip o sello que pongan los scripts en escenas.json (S.chip = {texto, tono, desde, pos})
    if (S && S.chip && S.chip.texto) chip(S.chip);
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
  // la palabra del titular que va en el acento (una sola): la primera con cifra («220», «6», «Q126»); si no hay cifra, la
  // primera palabra de cantidad («menos», «más», «casi»…); si no hay ninguna, nada. → índice o -1. Un titular solo de
  // cifras y signos («26 → 46.1») va entero en el acento (todos: true)
  const CANTIDAD = new Set(['mas', 'menos', 'mayor', 'menor', 'doble', 'triple', 'mitad', 'casi', 'solo', 'ningun', 'ninguna',
    'ninguno', 'nadie', 'todos', 'todas', 'cero', 'record', 'maximo', 'minimo', 'nunca', 'siempre']);
  const acentoDe = (palabras) => {
    const ws = palabras.map((w) => String(w));
    if (!ws.some((w) => /\p{L}/u.test(w))) return { k: -1, todos: true };
    const k = ws.findIndex((w) => /\d/.test(w));
    return { k: k >= 0 ? k : ws.findIndex((w) => CANTIDAD.has(normal(w))), todos: false };
  };
  const pintarGolpe = (S) => {
    const a = acentoDe(S.arriba.map((w) => w.text));
    document.getElementById('golpe').innerHTML = S.arriba.map((w, i) => `<span${a.todos || i === a.k ? ' class="acento"' : ''}>${esc(w.text)}</span>`).join('');
  };
  const ajustarGolpe = (S, limite) => {
    const g = document.getElementById('golpe'), arriba = document.getElementById('arriba');
    for (let fs = 96; S.arriba.length && fs > 60 && arriba.offsetTop + arriba.offsetHeight > limite - 16; fs -= 6) g.style.fontSize = fs + 'px';
  };
  const seekGolpe = (t, S) => {
    const pg = eo((t - (S.arriba.length ? S.arriba[0].start : 0) + 0.15) / 0.4);
    document.getElementById('golpe').style.transform = `translateX(${(1 - pg) * -60}px)`;
    [...document.querySelectorAll('#golpe span')].forEach((s, i) => {
      const p = eo((t - S.arriba[i].start + 0.15) / 0.3); s.style.opacity = p; s.style.transform = `translateY(${(1 - p) * 16}px)`; });
  };

  // barra de progreso: un tramo por grupo, de largo proporcional a su duración. /historia agrupa por acto (S.acto),
  // /noticias por noticia (S.N.indice) y /video va por escena. Una escena sin grupo toma el de la anterior (el cierre) o,
  // al principio, el de la siguiente (el gancho). Los grupos anteriores llenos, el actual avanza con el tiempo.
  let GRUPOS = null;
  const grupos = (todo) => {
    const es = todo.escenas, ks = es.map((e) => (e.acto != null ? 'a' + e.acto : e.N && e.N.indice != null ? 'n' + e.N.indice : null));
    if (!ks.some((x) => x !== null)) return es.map((e) => ({ ns: [e.n], durs: [e.dur || 1] }));
    for (let i = 0; i < ks.length; i++) if (ks[i] === null) ks[i] = i > 0 ? ks[i - 1] : ks.find((x) => x !== null);
    const out = [];
    ks.forEach((k, i) => { if (!out.length || out[out.length - 1].k !== k) out.push({ k, ns: [], durs: [] });
      out[out.length - 1].ns.push(es[i].n); out[out.length - 1].durs.push(es[i].dur || 1); });
    return out;
  };
  const pintarProgreso = (todo) => {
    GRUPOS = grupos(todo);
    document.getElementById('progreso').innerHTML = GRUPOS.map((g) => `<i style="flex:${g.durs.reduce((a, b) => a + b, 0).toFixed(2)}"><b></b></i>`).join('');
  };
  const seekProgreso = (t, k, dur) => {
    seekChips(t);   // los chips (V.chip) entran a su segundo: todas las páginas llaman seekProgreso en su seek
    const gi = GRUPOS.findIndex((g) => g.ns.includes(k)), g = GRUPOS[gi] || { ns: [k], durs: [dur] };
    const j = g.ns.indexOf(k), antes = g.durs.slice(0, j).reduce((a, b) => a + b, 0), total = g.durs.reduce((a, b) => a + b, 0);
    const avance = clamp((antes + Math.max(0, Math.min(t, dur)) * (g.durs[j] || dur) / Math.max(0.001, dur)) / Math.max(0.001, total));
    [...document.querySelectorAll('#progreso b')].forEach((b, i) => { b.style.width = (i < gi ? 100 : i === gi ? 100 * avance : 0) + '%'; });
  };

  // subtítulos: el trozo que suena (se oculta tras la voz, o cuando `ocultar(trozo, t)` lo pide); la palabra que se
  // dice resaltada, las ya dichas normales, las que vienen apagadas. Con S.sigue (la escena siguiente continúa la
  // misma secuencia de voz, /historia) el último trozo se queda hasta el final del clip: subtítulos continuos
  // una sola palabra resaltada a la vez: la última que empezó (la cola de 0.08 s de la anterior no la duplica)
  const palabras = (ps, t) => {
    let k = -1; ps.forEach((p, i) => { if (t >= p.start && t < p.end + 0.08) k = i; });
    return ps.map((p, i) => `<span class="${i === k ? 'ahora' : t >= p.start ? '' : 'no'}${p.num ? ' cifra' : ''}">${esc(p.text)}</span>`).join(' ');
  };
  // sin subtítulo doble: si ≥ 60 % de las palabras con contenido del trozo ya se leen en pantalla (texto visible fuera de
  // #subs y #progreso: la cita, el golpe, el titular, la frase final), el trozo no se muestra
  const enPantalla = () => {
    const s = new Set(), w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let nd = w.nextNode(); nd; nd = w.nextNode()) {
      const el = nd.parentElement;
      if (!el || el.closest('#subs, #progreso, script, style') || !el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) continue;
      for (const x of nd.textContent.split(/\s+/)) { const k = normal(x); if (k) s.add(k); }
    }
    return s;
  };
  const doble = (ps) => {
    const ks = ps.map((p) => normal(p.text)).filter((k) => k && !VACIAS.has(k));
    if (ks.length < 2) return false;
    const vis = enPantalla();
    return ks.filter((k) => vis.has(k)).length / ks.length >= 0.6;
  };
  const finSubs = (S) => S.fin_voz + (S.sigue ? 1e9 : 0.4);
  const subtitulos = (t, S, trozos, o = {}) => {
    const k = trozos.findIndex((c, j) => t >= c[0].start - 0.05 && t < ((trozos[j + 1] || [{ start: 1e9 }])[0].start - 0.05));
    const tr = trozos[k];
    const oculto = !tr || t > finSubs(S) || (o.ocultar && o.ocultar(tr, t)) || doble(tr);
    document.getElementById('subs').innerHTML = oculto ? '' : palabras(tr, t);
  };
  // variante del cierre: una ventana de 5 palabras alrededor de la que suena
  const subtitulosVentana = (t, S) => {
    const ini = S.palabras.findIndex((p) => t < p.end + 0.08);
    const k = ini < 0 ? S.palabras.length - 1 : ini;
    const ventana = S.palabras.slice(Math.max(0, k - 2), k + 3);
    document.getElementById('subs').innerHTML = t > finSubs(S) || doble(ventana) ? '' : palabras(ventana, t);
  };

  // RÓTULO DE ACTO (S.R, lo escribe scripts/historia.py en la primera escena de cada acto): un velo a sangre sobre la
  // escena (data-fuera-de-zona: V13 no lo mide) y una columna con el año grande (cuenta de `desde` a `hasta` entre
  // cuenta[0] y cuenta[1] si los dos son años de 4 cifras; si no, `hasta` tal cual), el título palabra a palabra en
  // sus `start`, el lugar y el riel (un punto por acto; el del acto se enciende al terminar la cuenta). El número de
  // acto NO se escribe: «Acto 2 de 3» es vocabulario del guion, no del espectador; numero/total solo mueven el riel.
  // Está desde el cuadro 0 y se desvanece 0.4 s antes de S.R.fin; los subtítulos siguen debajo (#subs va después en el
  // DOM). Las páginas lo pintan en __listo (pintarActo, tras sus propias medidas) y lo mueven en seek (seekActo);
  // desfase(S) es cuánto retrasan sus entradas fijas (chip, foto, caja) para que ocurran después del rótulo: las que
  // dependen de tiempos de la voz ya llegan desplazadas de python. Sin S.R las tres no hacen nada.
  const desfase = (S) => (S && S.R ? S.R.fin - 0.3 : 0);
  const esAnio4 = (x) => /^\d{4}$/.test(String(x ?? ''));
  async function pintarActo(S) {
    if (!S || !S.R || document.getElementById('acto')) return;
    const R = S.R, subs = document.getElementById('subs'), total = Math.max(1, R.total | 0);
    const el = document.createElement('div'); el.id = 'acto';
    el.innerHTML = '<div class="velo" data-fuera-de-zona></div><div class="col">' +
      `<div class="anio">${esc(R.hasta)}</div>` +
      `<div class="titulo">${(R.titulo || []).map((w) => `<span>${esc(w.text)}</span>`).join('')}</div>` +
      `<div class="lugar">${esc(R.lugar || '')}</div>` +
      '<div class="riel"><div class="linea"></div><div class="lleno"></div>' +
      Array.from({ length: total }, (_, k) => `<div class="punto" style="left:${total > 1 ? (100 * k / (total - 1)).toFixed(2) : 0}%"></div>`).join('') +
      '</div></div>';
    (subs ? subs.parentNode : document.body).insertBefore(el, subs);
    // las fuentes del rótulo pueden no estar cargadas aún (la página quizá no las usa): se piden antes de medir
    await Promise.all(['extra-condensed 900 230px Archivo', "600 24px 'JetBrains Mono'", '800 66px Archivo'].map((f) => document.fonts.load(f)));
    await document.fonts.ready;
    // el año grande: desde 230 px (180 en 4:5) hacia abajo hasta que quepa en la columna («Los sesenta» cabe)
    const a = el.querySelector('.anio'), col = el.querySelector('.col').clientWidth;
    for (let fs = F45 ? 180 : 230; fs > 90 && a.scrollWidth > col; fs -= 10) a.style.fontSize = fs + 'px';
  }
  const seekActo = (t, S) => {
    const el = document.getElementById('acto');
    if (!S || !S.R || !el) return;
    const R = S.R, [c0, c1] = R.cuenta || [0, 0], titulo = R.titulo || [];
    const op = eo((t + 0.1) / 0.3) * (1 - eo((t - (R.fin - 0.4)) / 0.4));
    el.style.opacity = op.toFixed(3); el.style.visibility = op > 0.001 ? '' : 'hidden';
    // el año cuenta desde el del acto anterior hasta el suyo (si los dos son años); entra creciendo y late al llegar
    const p = prog(t, c0, c1), a = el.querySelector('.anio');
    a.textContent = esAnio4(R.desde) && esAnio4(R.hasta) ? String(Math.round(+R.desde + (+R.hasta - +R.desde) * p)) : String(R.hasta);
    const ap = eo((t - c0 + 0.2) / 0.35);
    a.style.opacity = ap.toFixed(3);
    a.style.transform = `scale(${((0.92 + 0.08 * ap) * (1 + 0.04 * Math.sin(Math.PI * clamp((t - c1) / 0.5)))).toFixed(4)})`;
    [...el.querySelectorAll('.titulo span')].forEach((s, i) => {
      const w = eo((t - titulo[i].start + 0.15) / 0.3); s.style.opacity = w.toFixed(3); s.style.transform = `translateY(${((1 - w) * 26).toFixed(1)}px)`; });
    const lg = eo((t - (titulo.length ? titulo[titulo.length - 1].start : c1) - 0.2) / 0.4);
    el.querySelector('.lugar').style.opacity = (0.7 * lg).toFixed(3);
    // el riel: los actos anteriores llenos, el actual se enciende al terminar la cuenta
    const total = Math.max(1, R.total | 0), k = R.numero - 1, frac = total > 1 ? 1 / (total - 1) : 0;
    el.querySelector('.riel .lleno').style.width = (total > 1 ? 100 * frac * (Math.max(0, k - 1) + (k > 0 ? p : 0)) : 0).toFixed(2) + '%';
    [...el.querySelectorAll('.riel .punto')].forEach((d, i) => {
      d.classList.toggle('ya', i < k); d.classList.toggle('hoy', i === k && t >= c1);
      d.style.transform = i === k ? `scale(${(1 + 0.35 * Math.sin(Math.PI * clamp((t - c1) / 0.5))).toFixed(3)})` : '';
    });
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
  // data-fuera-de-zona (fondos a sangre, el velo del rótulo de acto; su columna de texto sí se mide) y la tarjeta
  // durante un foco (#ventana[data-foco]: solo la caja enfocada;
  // «mov» = la cámara pasa de un foco a otro). También falla el texto recortado (m013): un texto HTML o un <text> SVG
  // cuya caja se sale de la del ancestro más cercano con overflow hidden/clip (o del lienzo de su <svg>) queda dentro de
  // la zona, pero cortado. Devuelve [{que, caja: [x0, y0, x1, y1], regla}].
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
    // texto recortado: el ancestro más cercano que recorta (overflow distinto de visible en algún eje; el <svg> recorta su
    // lienzo por defecto) y cuánto se sale el texto de él en ese eje → la regla o null. html y body no cuentan: lo que
    // sale de la página ya lo marca la zona
    const cortado = (el, win, b) => {
      for (let x = el; x && x.nodeType === 1; x = x.parentElement) {
        const tag = x.tagName.toLowerCase();
        if (tag === 'body' || tag === 'html') return null;
        const c = win.getComputedStyle(x), cx = c.overflowX !== 'visible', cy = c.overflowY !== 'visible';
        if (!cx && !cy) continue;
        const a = x.getBoundingClientRect();
        if (a.width < 1 || a.height < 1) return null;
        const sale = Math.max(cx ? Math.max(a.left - b[0], b[2] - a.right) : 0, cy ? Math.max(a.top - b[1], b[3] - a.bottom) : 0);
        return sale > TOL + 1 ? 'texto recortado por <' + tag + (x.id ? '#' + x.id : '') + '> (overflow ' + (cx ? c.overflowX : c.overflowY)
          + '; sale ' + Math.round(sale) + ' px)' : null;
      }
      return null;
    };
    // la caja de TINTA de un texto (no la de su fuente: la cifra pegada al borde de su <svg> deja fuera el hueco del
    // descendente sin cortar nada): las cajas de línea del rango ajustadas con measureText (canvas) en la fuente, el
    // espaciado y la caja del texto; arriba la primera línea, abajo la última y a los lados solo si es una y de ancho
    // normal (el canvas no casa bien la cara condensada de Archivo: sus métricas verticales son las mismas, las de ancho
    // no, y a los lados queda la caja de avance)
    const CTX = document.createElement('canvas').getContext('2d');
    const tinta = (nodo, win, rg, b) => {
      const el = nodo.parentElement, svg = el instanceof win.SVGGraphicsElement && typeof el.getBBox === 'function';
      // un texto SVG: su caja en unidades del usuario (getBBox) llevada a la pantalla con getScreenCTM (los rectángulos de
      // un rango dentro de un SVG no son fiables en Chromium: salen corridos cuando un ancestro HTML tiene transform)
      const ls = svg ? [] : [...rg.getClientRects()].filter((q) => q.width > 0 && q.height > 0);
      if (!svg && !ls.length) return b;
      const c = win.getComputedStyle(el);
      CTX.font = [c.fontStyle, c.fontWeight, c.fontSize, c.fontFamily].join(' ');
      CTX.letterSpacing = c.letterSpacing === 'normal' ? '0px' : c.letterSpacing;
      let txt = nodo.textContent.trim();
      if (c.textTransform === 'uppercase') txt = txt.toUpperCase(); else if (c.textTransform === 'lowercase') txt = txt.toLowerCase();
      const m = CTX.measureText(txt), alto = m.fontBoundingBoxAscent + m.fontBoundingBoxDescent, lados = parseFloat(c.fontStretch) === 100;
      if (!(alto > 0)) return b;
      if (svg) {
        const bx = el.getBBox(), M = el.getScreenCTM();
        if (!M || !(bx.height > 0)) return b;
        const k = bx.height / alto;
        const u = [bx.x - m.actualBoundingBoxLeft * k, bx.y + (m.fontBoundingBoxAscent - m.actualBoundingBoxAscent) * k,
          bx.x + m.actualBoundingBoxRight * k, bx.y + (m.fontBoundingBoxAscent + m.actualBoundingBoxDescent) * k];
        if (!lados || txt.length !== el.textContent.trim().length || el.querySelector('tspan')) { u[0] = bx.x; u[2] = bx.x + bx.width; }
        const P = [[u[0], u[1]], [u[2], u[1]], [u[0], u[3]], [u[2], u[3]]].map(([x, y]) => [M.a * x + M.c * y + M.e, M.b * x + M.d * y + M.f]);
        return [Math.min(...P.map((q) => q[0])), Math.min(...P.map((q) => q[1])), Math.max(...P.map((q) => q[0])), Math.max(...P.map((q) => q[1]))];
      }
      const k = ls[0].height / alto, u = ls[ls.length - 1];
      const r = [b[0], ls[0].top + (m.fontBoundingBoxAscent - m.actualBoundingBoxAscent) * k, b[2],
        u.top + (m.fontBoundingBoxAscent + m.actualBoundingBoxDescent) * k];
      if (ls.length === 1 && lados) { r[0] = ls[0].left - m.actualBoundingBoxLeft * k; r[2] = ls[0].left + m.actualBoundingBoxRight * k; }
      return r;
    };
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
          const bb = [b.left, b.top, b.right, b.bottom];
          let r = recorte(nodo, win, bb);   // el texto se recorta desde su propio padre
          if (r && (r = corta(r))) {
            revisar(nodo.textContent.trim(), r);
            // el SVG cuenta entero (abajo), salvo su texto: un <text> que se sale del lienzo o del recorte queda cortado
            if ((b.right - b.left) * (b.bottom - b.top) >= 6 && !nodo.parentElement.closest('[data-foco]:not([data-foco=""])')) {
              const ti = tinta(nodo, win, rg, bb), corte = cortado(nodo.parentElement, win, ti);
              if (corte) fallas.push({ que: nodo.textContent.trim().slice(0, 40), caja: map(ti).map((v) => Math.round(v)), regla: corte });
            }
          }
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

  return { n, F45, portada, clamp, eo, prog, esc, normal, trocear, cargar, tarjeta, chip, seekChips, acentoDe, pintarGolpe, ajustarGolpe, seekGolpe,
    pintarProgreso, seekProgreso, subtitulos, subtitulosVentana, desfase, pintarActo, seekActo, zona, medirZona };
})();
