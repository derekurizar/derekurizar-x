// Animación «boca-a-boca» (mecanismo onda): algo empieza en un punto y se corre de lugar en lugar hasta llegar a
// quien lo adopta. Abajo, el origen (una burbuja de voz) emite ondas; arriba, una etiqueta con su nombre viejo
// (barras tenues). Al decir el primer paso, la voz se propaga: cada casita se enciende cuando la onda la alcanza
// (por distancia al origen), se dibuja el enlace desde la casita que se lo contó y salta un anillo en acento. Al decir
// el último paso, la onda llega a la etiqueta, que se voltea y queda en acento con el texto de ese paso. Los pasos
// intermedios (si hay) se leen abajo mientras la onda avanza. Seek puro: todo es función de t.
ANIM.registrar('boca-a-boca', {
  meta: {
    descripcion: 'boca a boca: la voz sale de un punto, salta de casa en casa en ondas y, al llegar arriba, la etiqueta cambia',
    mecanismo: 'onda',
    temas: ['boca a boca', 'rumor', 'contagio', 'nombre', 'marca', 'difusión', 'adopción'],
    pasos: [2, 6],
    ejemplo: { titulo: '¿Cómo se volvió costumbre?', pasos: ['Un vecino lo pidió', 'Se corrió de casa en casa', 'La fábrica lo adoptó'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, F = ctx.F45, n = P.pasos.length;
    const NS = 'http://www.w3.org/2000/svg';
    this.V = V; this.n = n;
    // geometría: etiqueta arriba, red en medio, origen y leyenda abajo
    const lw = Math.min(W * 0.88, 680), lh = F ? 128 : 150, ly = F ? 10 : 20;
    const capH = F ? 120 : 150, oy = H - capH - (F ? 70 : 84);
    const top = ly + lh + (F ? 50 : 70), bot = oy - (F ? 70 : 90);
    this.O = { x: W / 2, y: oy };
    this.L = { x: W / 2, y: ly + lh };
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    lienzo.appendChild(svg);
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); return e; };
    // casitas en posiciones fijas (fracciones de la banda de la red)
    const F_POS = [[0.2, 0.92], [0.8, 0.88], [0.5, 0.7], [0.12, 0.58], [0.88, 0.55], [0.34, 0.42], [0.67, 0.36], [0.18, 0.14], [0.84, 0.12], [0.5, 0.06]];
    const nodos = F_POS.map(([fx, fy]) => ({ x: 40 + fx * (W - 80), y: top + fy * (bot - top) }));
    const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    nodos.forEach(nd => { nd.d = dist(nd, this.O); });
    // el padre de cada casita: la más cercana que ya la oyó (más cerca del origen); si no hay, el origen
    nodos.forEach(nd => {
      let p = this.O, best = Infinity;
      nodos.forEach(m => { if (m.d < nd.d && dist(m, nd) < best) { best = dist(m, nd); p = m; } });
      if (dist(this.O, nd) < best) p = this.O;
      nd.padre = p;
    });
    this.Dmax = Math.max(...nodos.map(nd => nd.d));
    const gEnl = mk('g', {}), gAn = mk('g', {}), gNod = mk('g', {});
    svg.appendChild(gEnl); svg.appendChild(gAn); svg.appendChild(gNod);
    const linea = (a, b) => {
      const l = mk('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linecap': 'round' });
      const len = dist(a, b); l.style.strokeDasharray = len; gEnl.appendChild(l); return { el: l, len };
    };
    const s = F ? 1.2 : 1.4;
    this.nodos = nodos.map((nd, i) => {
      const enl = linea(nd.padre, nd);
      const g = mk('g', {});
      // casita: techo y cuerpo, centrada en (0,0)
      const casa = mk('path', { d: 'M-24 -2 L0 -26 L24 -2 M-17 -8 L-17 22 L17 22 L17 -8 Z', fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' });
      g.appendChild(casa); gNod.appendChild(g);
      const anillo = mk('circle', { cx: nd.x, cy: nd.y, r: 20, fill: 'none', stroke: 'var(--acento)', 'stroke-width': 7 });
      gAn.appendChild(anillo);
      return Object.assign(nd, { i, g, casa, enl, anillo, s });
    });
    // enlaces a la etiqueta desde las casitas de arriba
    const altas = nodos.filter(nd => nd.y < top + 0.25 * (bot - top));
    this.aEtiqueta = altas.map(nd => linea(nd, { x: Math.min(Math.max(nd.x, this.L.x - lw / 2 + 60), this.L.x + lw / 2 - 60), y: this.L.y + 6 }));
    // origen: burbuja de voz con tres puntos
    const og = mk('g', {});
    og.appendChild(mk('path', { d: 'M-46 -30 Q-46 -46 -30 -46 L30 -46 Q46 -46 46 -30 L46 10 Q46 26 30 26 L-6 26 L-26 46 L-22 26 L-30 26 Q-46 26 -46 10 Z', fill: 'var(--ink)', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linejoin': 'round' }));
    this.puntos = [-20, 0, 20].map(x => { const c = mk('circle', { cx: x, cy: -10, r: 6, fill: 'var(--bg)' }); og.appendChild(c); return c; });
    svg.appendChild(og); this.og = og;
    this.ondas = [0, 1, 2].map(() => { const c = mk('circle', { cx: this.O.x, cy: this.O.y - 10, r: 50, fill: 'none', stroke: 'var(--acento)', 'stroke-width': 5 }); svg.insertBefore(c, gEnl); return c; });
    // etiqueta de arriba: nombre viejo (barras tenues) → texto del último paso en acento
    const et = document.createElement('div');
    et.style.cssText = `position:absolute;left:${(W - lw) / 2}px;top:${ly}px;width:${lw}px;height:${lh}px;box-sizing:border-box;` +
      `border:5px solid var(--ink);border-radius:${lh / 2}px;display:flex;align-items:center;justify-content:center;` +
      `transform-origin:50% 50%;`;
    const barras = document.createElement('div');
    barras.style.cssText = 'display:flex;flex-direction:column;gap:18px;align-items:center';
    [0.62, 0.4].forEach(f => { const b = document.createElement('div'); b.style.cssText = `width:${lw * f}px;height:22px;border-radius:11px;background:color-mix(in srgb, var(--ink) 45%, transparent)`; barras.appendChild(b); });
    const txt = document.createElement('div');
    txt.style.cssText = `display:none;padding:0 40px;text-align:center;font:800 ${F ? 40 : 44}px/1.08 Archivo,sans-serif;letter-spacing:-.01em;color:var(--tinta-acento, var(--bg))`;
    txt.textContent = P.pasos[n - 1];
    et.appendChild(barras); et.appendChild(txt); lienzo.appendChild(et);
    this.et = { el: et, barras, txt };
    // leyenda de abajo: los pasos previos al último, uno a la vez
    this.leyendas = P.pasos.slice(0, n - 1).map((p, i) => {
      const d = document.createElement('div');
      d.style.cssText = `position:absolute;left:20px;right:20px;top:${H - capH}px;height:${capH}px;display:flex;align-items:center;justify-content:center;` +
        `text-align:center;font:800 ${F ? 42 : 46}px/1.1 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink)`;
      d.innerHTML = `<span style="font:600 36px/1 'JetBrains Mono',monospace;margin-right:22px;opacity:.6">${i + 1}</span>`;
      d.appendChild(document.createTextNode(p));
      lienzo.appendChild(d); return d;
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n;
    const t0 = ps[0].start, tL = ps[n - 1].start;
    const fantasma = 0.28 * eo((t - T.ini) / 0.5);
    const llega = d => t0 + 0.3 + (d / this.Dmax) * Math.max(0.4, tL - t0 - 0.75);
    const fin = t >= tL;
    // origen: respira siempre; los tres puntos laten como quien habla
    const r = 1 + 0.035 * Math.sin(2 * Math.PI * (t - T.ini) / 1.8);
    this.og.setAttribute('transform', `translate(${this.O.x} ${this.O.y}) scale(${r.toFixed(4)})`);
    this.og.style.opacity = Math.max(fantasma * 1.6, t >= t0 ? 1 : 0).toFixed(3);
    this.puntos.forEach((c, k) => { c.setAttribute('cy', (-10 - 5 * Math.max(0, Math.sin(2 * Math.PI * ((t - T.ini) / 1.1 - k / 6)))).toFixed(2)); });
    // ondas del origen (en acento mientras la voz corre; crema tenue cuando la etiqueta ya cambió)
    this.ondas.forEach((c, k) => {
      if (t < t0) { c.style.display = 'none'; return; }
      c.style.display = '';
      const u = ((((t - t0) / 1.6 + k / 3) % 1) + 1) % 1;
      c.setAttribute('r', (50 + u * 230).toFixed(1));
      c.setAttribute('stroke', fin ? 'var(--ink)' : 'var(--acento)');
      c.style.opacity = ((1 - u) * (fin ? 0.3 : 0.7) * eo((t - t0) / 0.4)).toFixed(3);
    });
    // casitas: fantasma → se encienden al llegar la onda (anillo en acento, enlace desde quien se lo contó)
    this.nodos.forEach(nd => {
      const ta = llega(nd.d), tp = nd.padre.d !== undefined ? llega(nd.padre.d) : t0;
      const e = eo((t - ta) / 0.4);
      const resp = e > 0 ? 1 + 0.04 * Math.sin(2 * Math.PI * (t - ta) / 1.7) : 1;
      const pop = 1 + 0.25 * Math.sin(Math.PI * clamp((t - ta) / 0.4));
      nd.g.setAttribute('transform', `translate(${nd.x} ${nd.y}) scale(${(nd.s * resp * pop).toFixed(4)})`);
      nd.g.style.opacity = Math.max(fantasma, e).toFixed(3);
      nd.casa.setAttribute('fill', e > 0.5 ? 'var(--ink)' : 'none');
      const dl = clamp((t - tp) / Math.max(0.2, ta - tp));
      nd.enl.el.style.strokeDashoffset = (nd.enl.len * (1 - dl)).toFixed(1);
      nd.enl.el.style.opacity = (dl > 0 ? 0.45 : fantasma * 0.6).toFixed(3);
      const ua = (t - ta) / 0.8;
      if (ua < 0 || ua > 1) { nd.anillo.style.display = 'none'; return; }
      nd.anillo.style.display = '';
      nd.anillo.setAttribute('r', (32 + 80 * eo(ua)).toFixed(1));
      nd.anillo.style.opacity = (0.9 * (1 - ua)).toFixed(3);
    });
    // enlaces a la etiqueta: se dibujan justo antes del último paso
    this.aEtiqueta.forEach(l => {
      const d = clamp((t - (tL - 0.5)) / 0.45);
      l.el.style.strokeDashoffset = (l.len * (1 - d)).toFixed(1);
      l.el.style.opacity = (d > 0 ? (fin ? 0.45 : 0.6) : fantasma * 0.6).toFixed(3);
    });
    // etiqueta: se voltea al llegar la onda y queda en acento con el último paso; luego respira
    const et = this.et, f = clamp((t - tL) / 0.5);
    const sy = f <= 0 ? 1 : Math.abs(Math.cos(Math.PI * f));
    const resp = fin ? 1 + 0.015 * Math.sin(2 * Math.PI * (t - tL) / 1.6) : 1;
    const cambiada = f >= 0.5;
    et.el.style.opacity = Math.max(fantasma * 2.2, t >= t0 ? 0.85 : 0, cambiada ? 1 : 0).toFixed(3);
    et.el.style.transform = `scale(${resp.toFixed(4)}, ${(Math.max(0.02, sy) * resp).toFixed(4)})`;
    et.el.style.background = cambiada ? 'var(--acento)' : 'transparent';
    et.el.style.borderColor = cambiada ? 'var(--acento)' : 'var(--ink)';
    et.barras.style.display = cambiada ? 'none' : 'flex';
    et.txt.style.display = cambiada ? '' : 'none';
    // leyendas: la del paso activo (antes del último); al final queda la anterior atenuada
    let activo = -1; ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.leyendas.forEach((d, i) => {
      const e = eo((t - ps[i].start) / 0.45), piso = i === n - 2 ? 0.4 : 0;
      const sale = 1 - (1 - piso) * eo((t - ps[i + 1].start) / 0.3);
      const op = e * sale;
      d.style.display = op > 0.001 ? 'flex' : 'none';
      d.style.opacity = op.toFixed(3);
      d.style.transform = `translateY(${((1 - e) * 24).toFixed(1)}px)`;
    });
  },
});
