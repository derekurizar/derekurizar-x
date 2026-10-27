// Animación «arco-viaje» de la escena explica (mecanismo onda): una ruta curva que sube de un origen a un destino.
// El primer paso enciende el origen y de él salen ondas; los pasos intermedios dibujan la ruta tramo a tramo y por
// ella viajan figuras de personas; al llegar al destino (penúltimo paso) se junta un grupo de figuras; el último paso
// manda por la misma ruta lo que las sigue (cajas de color) y cada llegada hace latir el destino. Sirve para
// migración, rutas de un producto, difusión de una costumbre o cualquier «algo sigue a la gente».
// Todo es función de t (seek puro, sin azar ni reloj).
ANIM.registrar('arco-viaje', {
  meta: {
    descripcion: 'ruta en arco: el origen emite ondas, figuras viajan al destino y se juntan, y luego algo las sigue por la misma ruta',
    mecanismo: 'onda',
    temas: ['migracion', 'ruta', 'viaje', 'expansion', 'difusion', 'producto', 'diaspora'],
    pasos: [2, 6],
    ejemplo: { titulo: 'La comida sigue a la gente', pasos: ['Falta trabajo en casa', 'Muchos se van', 'Llegan a otra ciudad', 'Su comida los sigue'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length;
    const NS = 'http://www.w3.org/2000/svg';
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); return e; };
    this.V = V; this.n = n;
    // K = pasos que son tramos de la ruta (todos menos el último, que es «lo que sigue»)
    const K = Math.max(1, n - 1); this.K = K;
    const O = [0.18 * W, 0.90 * H], C = [0.60 * W, 0.50 * H], D = [0.18 * W, 0.11 * H];
    const svg = mk('svg', { width: W, height: H });
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    const d = `M${O[0]} ${O[1]} Q${C[0]} ${C[1]} ${D[0]} ${D[1]}`;
    this.fantasma = mk('path', { d, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linecap': 'round', 'stroke-dasharray': '6 20' });
    this.ruta = mk('path', { d, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-linecap': 'round' });
    svg.appendChild(this.fantasma); svg.appendChild(this.ruta);
    lienzo.appendChild(svg);
    const L = this.ruta.getTotalLength(); this.L = L;
    this.ruta.style.strokeDasharray = `${L} ${L}`;
    const pt = f => { const p = this.ruta.getPointAtLength(V.clamp(f) * L); return [p.x, p.y]; };
    this.pt = pt;
    this.O = O; this.D = D;
    const Rmax = 0.065 * H; this.Rmax = Rmax;
    // ondas del origen y latido del destino
    this.ondas = [0, 1, 2].map(() => { const c = mk('circle', { cx: O[0], cy: O[1], r: 20, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5 }); svg.appendChild(c); return c; });
    this.latido = mk('circle', { cx: D[0], cy: D[1], r: 20, fill: 'none', stroke: 'var(--acento)', 'stroke-width': 6 });
    svg.appendChild(this.latido);
    // nodos: uno por tramo; si solo hay un tramo, el destino va sin rótulo y se enciende con el último paso
    const fr = i => (K >= 2 ? i / (K - 1) : 0);
    this.nodos = [];
    for (let i = 0; i < K; i++) this.nodos.push({ f: fr(i), paso: i });
    if (K < 2) this.nodos.push({ f: 1, paso: n - 1, mudo: true });
    this.nodos.forEach(nd => {
      const [x, y] = pt(nd.f);
      nd.x = x; nd.y = y;
      nd.el = mk('circle', { cx: x, cy: y, r: 17, fill: 'var(--bg)', stroke: 'var(--ink)', 'stroke-width': 6 });
      svg.appendChild(nd.el);
    });
    // figuras de personas
    const figura = (color, esc) => {
      const g = mk('g', {});
      g.appendChild(mk('circle', { cx: 0, cy: -31 * esc, r: 9 * esc, fill: color }));
      g.appendChild(mk('path', { d: `M${-12 * esc} 0 L${-12 * esc} ${-13 * esc} Q${-12 * esc} ${-22 * esc} 0 ${-22 * esc} Q${12 * esc} ${-22 * esc} ${12 * esc} ${-13 * esc} L${12 * esc} 0 Z`, fill: color }));
      svg.appendChild(g); return g;
    };
    this.viajeros = [0, 1, 2, 3, 4].map(() => figura('var(--ink)', 1.35));
    // grupo en el destino (a su izquierda, en rejilla 2 × 3)
    const colX = [D[0] - 124, D[0] - 82, D[0] - 40].map(x => Math.max(16, x));
    this.grupo = [0, 1, 2, 3, 4, 5].map(j => {
      const g = figura('var(--ink)', 1.15);
      g.bx = colX[j % 3]; g.by = D[1] + 2 + Math.floor(j / 3) * 58 - 14;
      return g;
    });
    // cajas que siguen
    this.cajas = [0, 1, 2, 3].map(() => {
      const g = mk('g', {});
      g.appendChild(mk('rect', { x: -20, y: -16, width: 40, height: 32, rx: 5, fill: 'var(--acento)' }));
      g.appendChild(mk('path', { d: 'M-20 -5 L20 -5', stroke: 'var(--bg)', 'stroke-width': 5 }));
      svg.appendChild(g); return g;
    });
    // rótulos (los pasos)
    const fs = ctx.F45 ? 38 : 42;
    const rotulo = (x, y, html, sep = 56) => {
      const el = document.createElement('div');
      const left = x + sep;
      el.style.cssText = `position:absolute;left:${left}px;top:${y}px;max-width:${W - left - 10}px;transform:translateY(-50%);` +
        `font:700 ${fs}px/1.12 Archivo,sans-serif;color:var(--ink);display:flex;align-items:center;`;
      el.innerHTML = html;
      lienzo.appendChild(el); return el;
    };
    this.nodos.forEach(nd => { if (!nd.mudo) nd.rot = rotulo(nd.x, nd.y, `<span>${V.esc(P.pasos[nd.paso])}</span>`, nd.f === 0 ? Math.max(56, 28 + Rmax) : 56); });
    // rótulo del último paso: junto a la ruta, entre los dos primeros nodos (o a media ruta)
    let fy = 0.5;
    if (K >= 2) {
      const yObj = (this.nodos[0].y + this.nodos[1].y) / 2;
      let mejor = 1e9;
      for (let s = 0; s <= 200; s++) { const f = s / 200 * this.nodos[1].f, p = pt(f); if (Math.abs(p[1] - yObj) < mejor) { mejor = Math.abs(p[1] - yObj); fy = f; } }
    }
    const [sx, sy] = pt(fy);
    this.sigue = rotulo(sx, sy, `<span style="flex:none;width:34px;height:26px;border-radius:5px;background:var(--acento);margin-right:16px"></span><span>${V.esc(P.pasos[n - 1])}</span>`);
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n, K = this.K, L = this.L;
    const s = i => ps[Math.min(i, ps.length - 1)].start;
    const frac = x => ((x % 1) + 1) % 1;
    const base = eo((t - T.ini) / 0.5);
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    // ruta fantasma que fluye (nunca quieta) y ruta dibujada hasta el frente
    this.fantasma.style.opacity = (0.22 * base).toFixed(3);
    this.fantasma.style.strokeDashoffset = (-(t * 28) % 26).toFixed(1);
    let frente = 0;
    if (K >= 2) {
      for (let i = 1; i < K; i++) {
        const dd = eo(clamp((t - (s(i) - 0.25)) / 0.6));
        if (dd > 0) frente = this.nodos[i - 1].f + (this.nodos[i].f - this.nodos[i - 1].f) * dd;
      }
    } else frente = eo(clamp((t - (s(n - 1) - 0.25)) / 0.6));
    this.ruta.style.strokeDashoffset = (L * (1 - frente)).toFixed(1);
    this.ruta.style.opacity = frente > 0 ? 1 : 0;
    const pon = (g, x, y, op, esc = 1) => { g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${esc.toFixed(3)})`); g.style.opacity = op.toFixed(3); };
    // ondas del origen desde el primer paso
    this.ondas.forEach((c, r) => {
      const ph = (t - s(0)) / 1.8 - r / 3;
      if (ph < 0) { c.style.opacity = 0; return; }
      const u = frac(ph);
      c.setAttribute('r', (20 + u * this.Rmax).toFixed(1));
      c.style.opacity = ((1 - u) * 0.75).toFixed(3);
    });
    // nodos
    this.nodos.forEach(nd => {
      const e = eo((t - s(nd.paso)) / 0.45);
      const resp = nd.paso === activo ? 1 + 0.12 * Math.sin(2 * Math.PI * (t - s(nd.paso)) / 1.6) : 1;
      nd.el.style.opacity = Math.max(0.25 * base, e).toFixed(3);
      nd.el.setAttribute('r', ((14 + 5 * e) * resp).toFixed(1));
      nd.el.setAttribute('fill', e > 0.5 ? 'var(--ink)' : 'var(--bg)');
      if (nd.rot) {
        nd.rot.style.opacity = (e * (nd.paso < activo ? 0.72 : 1)).toFixed(3);
        nd.rot.style.transform = `translateY(-50%) translateX(${((1 - e) * 28).toFixed(1)}px)`;
      }
    });
    // viajeros: salen con el segundo paso y recorren la ruta hasta el frente
    const sF = K >= 2 ? s(1) - 0.25 : Infinity, PF = 3.4;
    this.viajeros.forEach((g, k) => {
      const ph = (t - sF) / PF - k / this.viajeros.length;
      if (!(ph >= 0)) { g.style.opacity = 0; return; }
      const u = frac(ph), [x, y] = this.pt(u * frente);
      const op = Math.min(1, u / 0.08, (1 - u) / 0.12) * 0.95;
      pon(g, x, y + 26, Math.max(0, op));
    });
    // grupo en el destino al llegar
    const sD = K >= 2 ? s(K - 1) + 0.3 : Infinity;
    this.grupo.forEach((g, j) => {
      const e = eo((t - sD - j * 0.35) / 0.4);
      const bob = 2.5 * Math.sin(2 * Math.PI * (t / 2.2 + j * 0.17));
      pon(g, g.bx, g.by + 30 + bob + (1 - e) * 14, e);
    });
    // cajas: con el último paso recorren toda la ruta
    const sB = s(n - 1) - 0.1, PB = 2.8, B = this.cajas.length;
    this.cajas.forEach((g, k) => {
      const ph = (t - sB) / PB - k / B;
      if (!(ph >= 0)) { g.style.opacity = 0; return; }
      const u = frac(ph), [x, y] = this.pt(u * frente);
      const op = Math.min(1, u / 0.08, (1 - u) / 0.1);
      pon(g, x, y, Math.max(0, op), 1.3);
    });
    // latido del destino con cada caja que llega
    const phL = (t - (sB + PB)) / (PB / B);
    if (phL >= 0) {
      const u = frac(phL);
      this.latido.setAttribute('r', (20 + u * 0.75 * this.Rmax).toFixed(1));
      this.latido.style.opacity = ((1 - u) * 0.85).toFixed(3);
    } else this.latido.style.opacity = 0;
    // rótulo del último paso
    const eS = eo((t - s(n - 1)) / 0.45);
    this.sigue.style.opacity = eS.toFixed(3);
    this.sigue.style.transform = `translateY(-50%) translateX(${((1 - eS) * 28).toFixed(1)}px)`;
  },
});
