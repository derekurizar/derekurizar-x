// Capa 2D de la maqueta 3D: titulares, cifras, marcas pegadas al 3D, subtítulos palabra por palabra, barra de
// progreso por actos, «Sígueme» a mitad, y el cierre con «Sígueme en». Los elementos con tiempo están escritos en el
// HTML (clips de HyperFrames, por scripts/maqueta3d.py); aquí solo se mueve lo de adentro, como función pura de t.
// La llama el motor en cada cuadro: window.__capa(t, proyectar), con proyectar(x, y, z) → [px, py] | null.
(function () {
  const M = window.MAQUETA, Z = M.zona, C = M.capa;
  const $ = (id) => document.getElementById(id);
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const eo = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const vida = (t, a, b, ent = 0.4, sal = 0.3) => [eo((t - a) / ent), clamp((b - t) / sal)];
  window.__capaFuentes = ['900 80px Archivo', '800 60px Archivo', '700 34px Archivo', '600 22px "JetBrains Mono"'];

  // subtítulos: trozos de ≤ 26 caracteres (como video/comun.js); corta tras puntuación fuerte y no deja una palabra vacía al final
  const normal = (w) => (w || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
  const VACIAS = new Set(['a', 'al', 'con', 'de', 'del', 'e', 'el', 'en', 'es', 'la', 'las', 'lo', 'los', 'o', 'para', 'por', 'que', 'se', 'su', 'sus', 'u', 'un', 'una', 'y']);
  const trocear = (ps) => { const out = []; let cur = [];
    for (const p of ps) { const largo = cur.map((x) => x.text).join(' ').length + p.text.length + 1;
      if (cur.length && largo > 26) { const lleva = cur.length > 1 && VACIAS.has(normal(cur[cur.length - 1].text)) ? [cur.pop()] : []; out.push(cur); cur = lleva; }
      cur.push(p); if (/[.?:;…]$/.test(p.text)) { out.push(cur); cur = []; } }
    if (cur.length) out.push(cur); return out; };
  const subs = $('subs'), TROZOS = [];
  if (subs) for (const tr of trocear((C.palabras || []).filter((p) => p.start < C.subs_hasta))) {
    const d = document.createElement('div');
    const sp = tr.map((p) => { const s = document.createElement('span'); s.textContent = p.text; d.appendChild(s); d.appendChild(document.createTextNode(' ')); return s; });
    subs.appendChild(d); TROZOS.push({ d, sp, ps: tr, a: tr[0].start, b: tr[tr.length - 1].end });
  }
  // progreso
  const ACTOS = (C.progreso && C.progreso.actos) || [0], BARRAS = [...document.querySelectorAll('#progreso i b')];
  // titulares, cifras y marcas
  const TIT = (C.titulares || []).map((o, i) => ({ o, el: document.querySelector('#tit-' + i + ' .titulo') }));
  const CIF = (C.cifras || []).map((o, i) => ({ o, el: document.querySelector('#cifra-' + i + ' .cifra') }));
  const MAR = (M.marcas || []).map((o, i) => { const el = document.querySelector('#marca-' + i + ' .pin'); return { o, el, card: el.querySelector('.card') }; });
  const seg = document.querySelector('#seguir .vseguir'), segBt = seg && seg.querySelector('.bt'), segCam = seg && seg.querySelector('.cam');
  const velo = document.querySelector('#velo .velo'), cie = $('cierre');
  const FRASE = cie ? [...cie.querySelectorAll('.frase span')] : [], sigue = cie && cie.querySelector('.sigue'), cieBt = cie && cie.querySelector('.bt');
  let medidas = null;
  const medir = () => { medidas = { tit: TIT.map((x) => x.el.offsetTop + x.el.offsetHeight), card: MAR.map((x) => [x.card.offsetWidth, x.card.offsetHeight]) }; };

  window.__capa = function (t, proyectar) {
    if (!medidas) medir();
    // barra de progreso
    BARRAS.forEach((b, i) => { const a = ACTOS[i], z = i + 1 < ACTOS.length ? ACTOS[i + 1] : M.dur; b.style.width = (clamp((t - a) / Math.max(0.01, z - a)) * 100).toFixed(2) + '%'; });
    // titulares: suben 26 px y aparecen; salen desvaneciéndose
    let bandaTit = Z.banda_sin;
    TIT.forEach(({ o, el }, i) => { let [e, s] = vida(t, o.t, o.hasta); if (o.t <= 0.1) e = 1;   // el cuadro 0 es la portada: ese titular ya está completo
      el.style.opacity = (e * s).toFixed(3); el.style.transform = 'translateY(' + ((1 - e) * 26).toFixed(2) + 'px)';
      if (t >= o.t && t < o.hasta) bandaTit = Math.max(bandaTit, medidas.tit[i] + 14); });
    // cifras: el valor crece un poco al entrar
    CIF.forEach(({ o, el }) => { const [e, s] = vida(t, o.t, o.hasta, 0.35, 0.25);
      el.style.opacity = (e * s).toFixed(3); el.style.transform = 'scale(' + (0.9 + 0.1 * e).toFixed(4) + ')'; });
    // marcas: el punto sigue su ancla; la tarjeta no se sale de los márgenes y se desvanece antes de pisar el titular o el pie
    MAR.forEach(({ o, el, card }, i) => {
      const p = t >= o.t && t < o.hasta ? proyectar(o.x, o.y, o.z) : null;
      if (!p || p[0] < Z.corte || p[0] > Z.W - Z.corte || p[1] < 0 || p[1] > Z.H) { el.style.opacity = '0'; return; }
      const [e, s] = vida(t, o.t, o.hasta, 0.35, 0.25), [cw, ch] = medidas.card[i], alto = o.alto;
      const tope = p[1] - alto - ch;
      el.style.opacity = (e * s * clamp((tope - bandaTit) / 40 + 1) * clamp((Z.fin_marcas - p[1]) / 60 + 1)).toFixed(3);
      el.style.transform = 'translate(' + p[0].toFixed(2) + 'px,' + p[1].toFixed(2) + 'px) scale(' + (0.6 + 0.4 * e).toFixed(4) + ')';
      const izq = Z.izq - 25, der = (p[1] - alto > Z.iconos_y ? Z.iconos_x - 10 : Z.W - Z.corte - 3);
      let dx = 0; if (p[0] - cw / 2 < izq) dx = izq - (p[0] - cw / 2); if (p[0] + cw / 2 > der) dx = der - (p[0] + cw / 2);
      card.style.transform = 'translateX(calc(-50% + ' + dx.toFixed(2) + 'px))';
    });
    // subtítulos: el trozo que suena (queda 0.5 s tras su última palabra)
    let act = null;
    for (const tr of TROZOS) { if (tr.a <= t + 0.02) act = tr; else break; }
    if (act && (t > act.b + 0.5 || t >= C.subs_hasta)) act = null;
    for (const tr of TROZOS) {
      const si = tr === act; if (tr.si !== si) { tr.d.className = si ? 'si' : ''; tr.si = si; }
      if (si) { let k = -1; tr.ps.forEach((p, i) => { if (p.start <= t + 0.02) k = i; });
        tr.sp.forEach((s, i) => { const c = i > k ? 'no' : i === k ? 'ahora' : ''; if (s.className !== c) s.className = c; }); }
    }
    // «Sígueme» a mitad: entra, se toca («Siguiendo») y se va
    if (seg) { const o = C.seguir, [e, s] = vida(t, o.t, o.t + o.dur, 0.3, 0.3), u = (t - o.t) / o.dur;
      seg.style.opacity = (e * s).toFixed(3); seg.style.transform = 'translateY(' + ((1 - e) * -16).toFixed(2) + 'px) scale(' + (1 + 0.05 * Math.max(0, 1 - Math.abs(u - 0.45) / 0.06)).toFixed(4) + ')';
      const hecho = u >= 0.45; if (segBt.classList.contains('hecho') !== hecho) segBt.classList.toggle('hecho', hecho);
      const cam = u > 0.5 && u < 0.8 ? Math.sin((u - 0.5) / 0.3 * Math.PI * 4) * 14 * (1 - (u - 0.5) / 0.3) : 0; segCam.style.transform = 'rotate(' + cam.toFixed(2) + 'deg)'; }
    // cierre: velo, la frase palabra a palabra y «Sígueme en»
    if (cie) { const o = C.cierre;
      velo.style.opacity = (clamp((t - o.t) / 0.6) * Z.velo).toFixed(3);
      FRASE.forEach((s, i) => { const ya = t >= o.palabras[i].start; if (s.classList.contains('ya') !== ya) s.classList.toggle('ya', ya); });
      const e = eo((t - o.t_redes) / 0.45);
      sigue.style.opacity = e.toFixed(3); sigue.style.transform = 'translateY(' + ((1 - e) * 22).toFixed(2) + 'px)';
      const hecho = t >= o.t_redes + 1.0; if (cieBt.classList.contains('hecho') !== hecho) cieBt.classList.toggle('hecho', hecho); }
  };
})();
