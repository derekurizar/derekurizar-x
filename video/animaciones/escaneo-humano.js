// Animación «escaneo-humano» de la escena explica (mecanismo cadena): lo que la máquina no puede leer va a una
// persona y vuelve resuelto. A la izquierda, una página escaneada (renglones como barras) con una palabra borrosa en
// su hueco; un escáner baja por la página y se traba en ella; la palabra sale volando, se tuerce y queda en una casilla
// (el captcha, con su raya ondulada); abajo, un teclado: sus teclas se hunden y la palabra se escribe letra a letra en
// el campo; por último la palabra limpia vuelve a su hueco, los renglones se vuelven sólidos (la página queda digital)
// y suben píxeles de la página. Abajo, los pasos con su número: el que la voz dice en crema llena, los dichos atenuados.
// La palabra es la más larga del primer paso. Una sola cosa en acento: el hueco, luego la palabra torcida, luego lo
// tecleado y al final la palabra en su lugar. Las cuatro estaciones se reparten entre los pasos (3–5). Todo es
// función de t (seek puro, sin azar ni reloj).
ANIM.registrar('escaneo-humano', {
  meta: {
    descripcion: 'lo que la máquina no lee va a una persona: una palabra borrosa sale de la página, se teclea y vuelve; la página queda digital',
    mecanismo: 'cadena',
    temas: ['digitalizar', 'escáner', 'captcha', 'trabajo humano', 'libros', 'tecnología', 'invento', 'colaboración'],
    pasos: [3, 5],
    ejemplo: { titulo: '¿Cómo ayudaba cada captcha?', pasos: ['Palabra de un libro viejo', 'La máquina no la lee', 'Una persona la escribe', 'La página queda digital'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, F = ctx.F45, W = ctx.ancho, H = ctx.alto;
    const NS = 'http://www.w3.org/2000/svg';
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); return e; };
    const tenue = (p) => `color-mix(in srgb, var(--ink) ${p}%, transparent)`;
    this.V = V; this.tenue = tenue;

    // la palabra: la más larga del primer paso
    const palabras = (P.pasos[0] || '').split(/\s+/).map((w) => w.replace(/[^\p{L}\p{N}]/gu, '')).filter(Boolean);
    let pal = palabras[0] || 'PALABRA';
    palabras.forEach((w) => { if (w.length > pal.length) pal = w; });
    pal = pal.toUpperCase();
    const len = Math.max(3, pal.length);

    // reparto: estación (página, captcha, teclado) arriba; pasos abajo
    const lineH = F ? 58 : 68, capH = n * lineH, capY0 = H - capH;
    const SH = capY0 - (F ? 26 : 38);
    const px = 8, pw = Math.round(W * (F ? 0.42 : 0.44));
    const ph = Math.min(SH - 16, Math.round(pw * 1.38));
    const py = Math.max(8, (SH - ph) / 2);
    const rx = Math.round(W * 0.56), rw = W - rx - 14;
    const cY = py + ph * 0.05, cH = ph * 0.30;
    const iY = cY + cH + ph * 0.10, iH = ph * 0.16;
    const kY = iY + iH + ph * 0.07;
    const g = { px, pw, py, ph, rx, rw, cY, cH, iY, iH, kY };
    this.g = g;

    const svg = mk('svg', { width: W, height: H });
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    lienzo.appendChild(svg);

    // página con la esquina doblada
    const dob = 38;
    this.hoja = mk('path', { d: `M${px} ${py} L${px + pw - dob} ${py} L${px + pw} ${py + dob} L${px + pw} ${py + ph} L${px} ${py + ph} Z`,
      fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linejoin': 'round' });
    svg.appendChild(this.hoja);
    this.pliegue = mk('path', { d: `M${px + pw - dob} ${py} L${px + pw - dob} ${py + dob} L${px + pw} ${py + dob}`,
      fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linejoin': 'round' });
    svg.appendChild(this.pliegue);

    // renglones: 4 arriba, el de la palabra, 4 abajo
    const ix = px + 28, iw = pw - 56, top = py + 50, bot = py + ph - 34;
    const filaP = 78, rowH = (bot - top - filaP) / 8;
    this.barras = [];
    const barra = (x, y, w) => { const r = mk('rect', { x, y: y - 6, width: Math.max(10, w), height: 12, rx: 6 }); svg.appendChild(r); this.barras.push({ r, y }); };
    for (let i = 0; i < 4; i++) barra(ix, top + rowH * (i + 0.5), iw * (0.62 + ((i * 37) % 11) / 11 * 0.36));
    const sy = top + 4 * rowH + filaP / 2;               // centro del renglón de la palabra
    const sx = ix + iw * 0.14, sw = iw * 0.66, sh = 64;
    barra(ix, sy, iw * 0.10);
    barra(sx + sw + 10, sy, ix + iw - (sx + sw + 10));
    for (let i = 0; i < 4; i++) barra(ix, top + 4 * rowH + filaP + rowH * (i + 0.5), iw * (0.58 + (((i + 5) * 37) % 11) / 11 * 0.4));
    this.barras.sort((a, b) => a.y - b.y);
    this.hueco = mk('rect', { x: sx, y: sy - sh / 2, width: sw, height: sh, rx: 12, fill: 'none', 'stroke-width': 5, 'stroke-dasharray': '14 10' });
    svg.appendChild(this.hueco);
    Object.assign(g, { sx, sw, sy, sh, ix, iw });

    // escáner: una línea con su haz
    this.haz = mk('rect', { x: px + 6, width: pw - 12, height: 46, fill: tenue(16) });
    this.scan = mk('rect', { x: px + 6, width: pw - 12, height: 7, rx: 3, fill: 'var(--ink)' });
    svg.appendChild(this.haz); svg.appendChild(this.scan);

    // captcha: casilla con la raya ondulada
    this.caja = mk('rect', { x: rx, y: cY, width: rw, height: cH, rx: 18, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 });
    svg.appendChild(this.caja);
    let d = '';
    for (let k = 0; k <= 24; k++) { const x = rx + 22 + (rw - 44) * k / 24, y = cY + cH * 0.56 + Math.sin(k * 0.9) * cH * 0.12; d += (k ? ' L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1); }
    this.onda = mk('path', { d, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-dasharray': '22 12' });
    svg.appendChild(this.onda);

    // campo donde se escribe
    this.campo = mk('rect', { x: rx, y: iY, width: rw, height: iH, rx: 14, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5 });
    svg.appendChild(this.campo);

    // teclado: 3 filas (10, 9, 7)
    const gap = 6, kw = (rw - 9 * gap) / 10, kh = Math.max(18, Math.min(36, (py + ph - kY - 2 * gap) / 3));
    this.teclas = [];
    [10, 9, 7].forEach((m, f) => {
      const x0 = rx + (rw - (m * kw + (m - 1) * gap)) / 2;
      for (let j = 0; j < m; j++) {
        const r = mk('rect', { x: x0 + j * (kw + gap), y: kY + f * (kh + gap), width: kw, height: kh, rx: 6, 'stroke-width': 4 });
        svg.appendChild(r); this.teclas.push(r);
      }
    });

    // rastros: página → captcha, captcha → campo, campo → página
    const traza = (dd) => { const p = mk('path', { d: dd, fill: 'none', stroke: tenue(40), 'stroke-width': 5, 'stroke-linecap': 'round' }); svg.appendChild(p); const L = p.getTotalLength(); p.style.strokeDasharray = L.toFixed(1); return { p, L }; };
    const ccx = rx + rw / 2;
    this.trA = traza(`M${px + pw + 8} ${sy - 18} C${px + pw + 50} ${sy - 80}, ${rx - 50} ${cY + cH / 2}, ${rx - 10} ${cY + cH / 2}`);
    this.trB = traza(`M${ccx} ${cY + cH + 8} L${ccx} ${iY - 8}`);
    this.trC = traza(`M${rx - 10} ${iY + iH / 2} C${rx - 50} ${iY + iH / 2}, ${px + pw + 50} ${sy + 60}, ${px + pw + 8} ${sy + 18}`);

    // píxeles que suben de la página digital
    this.pix = Array.from({ length: 9 }, (_, i) => { const r = mk('rect', { width: 11, height: 11, fill: 'var(--ink)' }); r.style.display = 'none'; svg.appendChild(r); return { r, x: px + 22 + ((i * 53) % (pw - 50)), f: ((i * 37) % 11) / 11 }; });

    // la palabra en tres estados (texto: Archivo condensado 900)
    const fs = Math.min(46, sw / (len * 0.5));
    const fsC = Math.min(F ? 60 : 64, (rw - 40) / (len * 0.5));
    const fsI = Math.min(46, iH * 0.62, (rw - 40) / (len * 0.5));
    Object.assign(g, { fs, fsC, fsI });
    const palabra = (size, conLetras) => {
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:0;top:0;white-space:nowrap;font:900 ${size}px/1 Archivo,sans-serif;` +
        `font-stretch:62.5%;text-transform:uppercase;letter-spacing:.02em;color:var(--ink);transform-origin:50% 50%;`;
      const letras = [...pal].map((c) => { const s = document.createElement('span'); s.textContent = c; s.style.display = 'inline-block'; el.appendChild(s); return s; });
      lienzo.appendChild(el);
      return { el, letras };
    };
    this.wPag = palabra(fs);      // borrosa en la página
    this.wVuela = palabra(fs);    // la que sale y se tuerce en el captcha
    this.wTec = palabra(fsI);     // la que se teclea
    this.cursor = document.createElement('span');
    this.cursor.style.cssText = `display:inline-block;width:6px;height:${(fsI * 0.9).toFixed(0)}px;margin-left:6px;vertical-align:-4%;background:var(--ink);`;
    this.wTec.el.appendChild(this.cursor);
    this.wVuelve = palabra(fs);   // la limpia que vuelve
    this.pal = pal;

    // los pasos, abajo
    this.caps = P.pasos.map((txt, i) => {
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:0;width:${W - 10}px;top:${capY0 + i * lineH}px;height:${lineH}px;display:flex;align-items:center;` +
        `white-space:nowrap;overflow:hidden;font:800 ${F ? 38 : 42}px/1.05 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);`;
      el.innerHTML = `<span style="font:600 36px/1 'JetBrains Mono',monospace;margin-right:22px;opacity:.6">${i + 1}</span>`;
      el.appendChild(document.createTextNode(txt));
      lienzo.appendChild(el);
      return el;
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, g = this.g, ps = T.pasos, n = ps.length, tenue = this.tenue;
    const st = ps.map((p) => p.start);
    // cuatro estaciones repartidas entre los pasos
    const fase = (k) => { const f = k * (n - 1) / 3, i0 = Math.min(n - 2, Math.floor(f)), r = f - i0; return st[i0] + r * (st[i0 + 1] - st[i0]); };
    const s0 = fase(0), s1 = fase(1), s2 = fase(2), s3 = fase(3);
    const fin = Math.max(T.fin || s3 + 3, s3 + 2);
    const ghost = 0.28 * eo((t - T.ini) / 0.5);
    const op = (e, v) => { e.style.opacity = clamp(v).toFixed(3); };
    const ent = (s) => eo((t - s) / 0.45);

    // tiempos dentro de cada tramo (se acomodan si la voz va rápida)
    const g1 = Math.max(0.6, s2 - s1), g2 = Math.max(0.6, s3 - s2);
    const scanFin = s1 + Math.min(0.7, 0.35 * g1);
    const vA0 = s1 + Math.min(0.85, 0.45 * g1), vA1 = vA0 + Math.min(0.6, 0.4 * g1);
    const dt = Math.min(0.16, (0.75 * g2) / this.pal.length), tec0 = s2 + Math.min(0.3, 0.15 * g2);
    const vB0 = s3, vB1 = s3 + 0.6, dig0 = s3 + 0.55, dig1 = s3 + 1.35;

    // página
    const pagE = Math.max(ghost, ent(s0));
    op(this.hoja, pagE); op(this.pliegue, pagE);
    const digital = this.barras.length;
    this.barras.forEach((b, i) => {
      const u = clamp((t - dig0 - (i / digital) * (dig1 - dig0) * 0.7) / 0.3);
      b.r.setAttribute('fill', u >= 1 ? 'var(--ink)' : tenue(Math.round(38 + 62 * u)));
      op(b.r, pagE);
    });
    const respira = t >= vB1 ? 1 + 0.012 * Math.sin(2 * Math.PI * (t - vB1) / 1.8) : 1;
    const cxP = g.px + g.pw / 2, cyP = g.py + g.ph / 2;
    const tp = `translate(${cxP} ${cyP}) scale(${respira.toFixed(4)}) translate(${-cxP} ${-cyP})`;
    this.hoja.setAttribute('transform', tp); this.pliegue.setAttribute('transform', tp);

    // el hueco: acento mientras la palabra borrosa espera; luego vacío tenue; se borra al volver la palabra
    const enHueco = t < vA0;
    this.hueco.setAttribute('stroke', enHueco && t >= s0 ? 'var(--acento)' : 'var(--ink)');
    this.hueco.style.strokeDashoffset = (-(t - T.ini) * 30).toFixed(1);
    op(this.hueco, t >= vB1 ? 0 : enHueco ? Math.max(ghost, ent(s0)) : 0.45);

    // palabra borrosa en la página
    const pos = (w, x, y, extra) => { w.el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -50%) ${extra || ''}`; };
    const hx = g.sx + g.sw / 2, hy = g.sy;
    pos(this.wPag, hx, hy);
    this.wPag.el.style.filter = 'blur(3px)';
    this.wPag.el.style.display = t < vA0 ? '' : 'none';
    op(this.wPag.el, Math.max(ghost, ent(s0)) * 0.9);

    // escáner: baja hasta la palabra, se traba ahí y se apaga cuando la palabra se va
    const scOn = t >= s1 - 0.05 && t < vA1 + 0.4;
    this.scan.style.display = this.haz.style.display = scOn ? '' : 'none';
    if (scOn) {
      const u = eo(clamp((t - s1) / (scanFin - s1)));
      let y = g.py + 24 + (hy - g.py - 24) * u;
      if (t > scanFin) y += 8 * Math.sin(2 * Math.PI * (t - scanFin) / 0.5);
      const a = clamp((t - s1) / 0.2) * (1 - clamp((t - vA1) / 0.4));
      this.scan.setAttribute('y', (y - 3.5).toFixed(1)); this.haz.setAttribute('y', (y - 46).toFixed(1));
      op(this.scan, a); op(this.haz, a);
    }

    // captcha y su palabra torcida
    op(this.caja, Math.max(ghost, ent(s1)));
    op(this.onda, t >= vA1 ? 0.7 * ent(vA1) : 0);
    this.onda.style.strokeDashoffset = (-(t - T.ini) * 24).toFixed(1);
    const ccx = g.rx + g.rw / 2, ccy = g.cY + g.cH * 0.48;
    const uA = clamp((t - vA0) / (vA1 - vA0)), eA = eo(uA);
    this.wVuela.el.style.display = t >= vA0 ? '' : 'none';
    if (t >= vA0) {
      const x = hx + (ccx - hx) * eA, y = hy + (ccy - hy) * eA - 70 * Math.sin(Math.PI * uA);
      const sc = 1 + (g.fsC / g.fs - 1) * eA;
      pos(this.wVuela, x, y, `scale(${sc.toFixed(4)})`);
      this.wVuela.el.style.filter = `blur(${(3 * (1 - eA)).toFixed(2)}px)`;
      this.wVuela.letras.forEach((s, i) => {
        const rot = (((i * 37) % 11) - 5) * 3.2 + 2 * Math.sin(t * 2.1 + i);
        const dy = (((i * 53) % 9) - 4) * 2.4;
        s.style.transform = `translateY(${(dy * eA).toFixed(1)}px) rotate(${(rot * eA).toFixed(2)}deg)`;
      });
      this.wVuela.el.style.color = t < s2 ? 'var(--acento)' : 'var(--ink)';
      op(this.wVuela.el, t < s3 ? 1 : 1 - 0.5 * ent(s3));
    }

    // campo y teclado: las teclas se hunden y la palabra se escribe letra a letra
    const kE = Math.max(ghost, ent(s2));
    op(this.campo, kE);
    const k = Math.floor((t - tec0) / dt), escritas = t < tec0 ? 0 : Math.min(this.pal.length, k + 1);
    const nT = this.teclas.length;
    this.teclas.forEach((r, j) => {
      let pulsa = false;
      if (t >= tec0 && k < this.pal.length) pulsa = ((this.pal.charCodeAt(k) * 7 + k * 3) % nT) === j && ((t - tec0) % dt) < dt * 0.7;
      r.setAttribute('fill', pulsa ? 'var(--ink)' : 'none');
      r.setAttribute('stroke', 'var(--ink)');
      r.setAttribute('transform', pulsa ? 'translate(0 3)' : '');
      op(r, Math.max(ghost, ent(s2) * (t < s3 ? 0.8 : 0.45)));
    });
    const tecOn = t >= s2 && t < vB0;
    this.wTec.el.style.display = tecOn ? '' : 'none';
    if (tecOn) {
      pos(this.wTec, ccx, g.iY + g.iH / 2);
      this.wTec.letras.forEach((s, i) => { s.style.display = i < escritas ? 'inline-block' : 'none'; });
      this.wTec.el.style.color = 'var(--acento)';
      op(this.wTec.el, ent(s2));
      this.cursor.style.opacity = (0.55 + 0.45 * Math.cos(2 * Math.PI * (t - s2) / 1.1)).toFixed(3);
    }
    op(this.campo, t >= s3 ? kE * (1 - 0.5 * ent(s3)) : kE);

    // rastros del viaje
    const traz = (tr, a, b) => { const d = clamp((t - a) / (b - a)); tr.p.style.strokeDashoffset = (tr.L * (1 - d)).toFixed(1); op(tr.p, d > 0 ? 1 : 0); };
    traz(this.trA, vA0, vA1); traz(this.trB, s2 - 0.1, s2 + 0.35); traz(this.trC, vB0, vB1);

    // la palabra limpia vuelve a su hueco
    this.wVuelve.el.style.display = t >= vB0 ? '' : 'none';
    if (t >= vB0) {
      const uB = clamp((t - vB0) / (vB1 - vB0)), eB = eo(uB);
      const x0 = ccx, y0 = g.iY + g.iH / 2;
      const x = x0 + (hx - x0) * eB, y = y0 + (hy - y0) * eB + 60 * Math.sin(Math.PI * uB);
      const sc = (g.fsI / g.fs) + (1 - g.fsI / g.fs) * eB;
      pos(this.wVuelve, x, y, `scale(${(sc * respira).toFixed(4)})`);
      this.wVuelve.el.style.color = 'var(--acento)';
      op(this.wVuelve.el, 1);
    }

    // píxeles que suben de la página ya digital
    const pOn = t >= dig1;
    this.pix.forEach((p, i) => {
      p.r.style.display = pOn ? '' : 'none';
      if (!pOn) return;
      const u = (((t - dig1) * 0.35 + p.f) % 1 + 1) % 1;
      p.r.setAttribute('x', p.x.toFixed(1));
      p.r.setAttribute('y', (g.py + g.ph - 40 - u * (g.ph - 80)).toFixed(1));
      op(p.r, 0.6 * Math.sin(Math.PI * u) * clamp((t - dig1) / 0.4));
    });

    // los pasos, abajo
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.caps.forEach((el, i) => {
      const e = ent(st[i]);
      el.style.opacity = (e * (i === activo ? 1 : 0.45)).toFixed(3);
      el.style.transform = `translateX(${((1 - e) * -30).toFixed(1)}px)`;
    });
    void fin;
  },
});
