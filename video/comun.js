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

  return { n, F45, portada, clamp, eo, prog, esc, normal, trocear, cargar, tarjeta, pintarGolpe, ajustarGolpe, seekGolpe,
    pintarProgreso, seekProgreso, subtitulos, subtitulosVentana };
})();
