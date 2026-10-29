// Animación «embudo-filtro» (semilla de la biblioteca): un embudo vertical de 2–6 bandas apiladas, cada una más
// angosta que la anterior. Un flujo continuo de partículas cae desde arriba. Mientras una etapa no se enciende, las
// partículas se acumulan tenues en ella; cuando la voz dice el paso i, su banda se enciende y desde ese momento la etapa
// descarta una parte (salen por los lados y se desvanecen) y deja bajar al resto. Por la boca salen pocas, en acento.
// Estilo Noche: partículas y contornos en crema; en acento solo la etapa que suena (trazo y velo) y las pocas que
// salen por la boca; las etapas ya dichas quedan en crema atenuada. Todo es función de t: cada partícula k nace en un instante fijo y su recorrido (dónde espera, si se descarta) sale de
// un hash fijo de k y de la etapa, nunca de la ejecución.
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
// ayudantes (se copian en this al pintar)
const EMBUDO_AUX = {
  // medio ancho del perfil del embudo en la altura y
  hw(y) {
    const { yTop, yBot, wTop, wBot } = this;
    if (y <= yTop) return wTop / 2;
    if (y >= yBot) return wBot / 2;
    return (wTop + (wBot - wTop) * (y - yTop) / (yBot - yTop)) / 2;
  },

  // hash fijo en [0, 1)
  h(k, j) {
    let x = Math.imul((k + 7919) ^ Math.imul(j + 1, 0x9e3779b1), 0x85ebca6b);
    x ^= x >>> 13; x = Math.imul(x, 0xc2b2ae35); x ^= x >>> 16;
    return (x >>> 0) / 4294967296;
  },

  // estado de la partícula k en t: {x, y, o, r, acento} o null
  particula(k, t, T) {
    const { clamp, eo } = this.V, n = this.n, ps = T.pasos;
    const s = this.s0 + k * this.dt;
    if (t < s) return null;
    const u = (this.h(k, 99) * 2 - 1) * 0.8;
    const xEn = (y) => this.cx + u * this.hw(y);
    let y = 2, tau = s;
    const nace = eo((t - s) / 0.3);
    for (let j = 0; j < n; j++) {
      const b = this.bandas[j];
      const yd = b.y0 + this.bh * (0.3 + 0.6 * this.h(k, j + 10));
      const td = tau + (yd - y) / this.v;
      const st = ps[j] ? ps[j].start : T.fin;
      if (t < td) {
        const yy = y + (t - tau) * this.v;
        return { x: xEn(yy), y: yy, o: 0.85 * nace, r: 7 };
      }
      const espera = st > td;
      const suelta = espera ? st + 0.9 * this.h(k, j + 30) : td;
      if (t < suelta) {
        const q = eo((t - td) / 0.4), fase = k * 1.7 + j;
        return {
          x: xEn(yd) + 3 * Math.sin(2.3 * t + fase), y: yd + 2.5 * Math.cos(1.9 * t + fase * 0.7),
          o: (0.85 - 0.5 * q) * nace, r: 7,
        };
      }
      if (this.h(k, j + 50) < this.tasa) {
        // descartada: sale por el lado más cercano y se desvanece
        const p = clamp((t - suelta) / 0.9);
        if (p >= 1) return null;
        const x0 = xEn(yd), lado = u >= 0 ? 1 : -1;
        const borde = this.hw(yd) - Math.abs(x0 - this.cx);
        const extra = lado < 0 ? Math.min(70, this.cx - this.hw(yd) - 12) : 16;
        const vuelve = espera ? 0.4 : 0.85; // la que esperaba sale desde su opacidad tenue
        return {
          x: x0 + lado * (borde + extra) * eo(p / 0.85), y: yd + 46 * p * p,
          o: vuelve * (1 - p) * nace, r: 7 * (1 - 0.3 * p),
        };
      }
      y = yd; tau = suelta;
    }
    // sobreviviente: baja por el cuello y sale por la boca en acento
    const yy = y + (t - tau) * this.v * 0.45;
    const fondo = this.H - 14;
    if (yy > fondo) return null;
    const q = eo((t - tau) / 0.35);
    const o = 1 - clamp((yy - (fondo - 70)) / 70);
    return { x: xEn(Math.min(yy, this.yBoca)), y: yy, o, r: 7 + 5 * q, acento: true };
  },
};

ANIM.registrar('embudo-filtro', {
  meta: {
    descripcion: 'embudo de etapas: entran muchas partículas arriba, cada etapa descarta una parte y abajo quedan pocas',
    mecanismo: 'embudo',
    temas: ['filtro', 'etapas', 'confirmación', 'casos', 'proceso', 'descarte', 'embudo'],
    pasos: [2, 6],
    ejemplo: {
      titulo: 'Cómo se confirma una muerte',
      pasos: ['Se notifica la sospecha', 'Se investiga el caso', 'Una mesa técnica revisa', 'Se confirma o se descarta'],
    },
  },

  pintar(lienzo, P, ctx) {
    Object.assign(this, EMBUDO_AUX);
    const { V, F45 } = ctx, W = ctx.ancho, H = ctx.alto, n = Math.max(1, P.pasos.length);
    this.V = V; this.n = n; this.W = W; this.H = H;
    // geometría del embudo: perfil continuo de ancho, cortado en n bandas con un hueco entre ellas
    const margenIzq = F45 ? 30 : 24;
    const wTop = W * (F45 ? 0.5 : 0.54), wBot = wTop * 0.2;
    const yTop = F45 ? 40 : 46, cuello = F45 ? 30 : 36, abajo = F45 ? 100 : 130;
    const yBot = H - abajo - cuello, hueco = n > 4 ? 8 : 12;
    const bh = (yBot - yTop - hueco * (n - 1)) / n;
    const cx = margenIzq + wTop / 2;
    Object.assign(this, { wTop, wBot, yTop, yBot, cuello, bh, cx, hueco });
    this.bandas = [];
    for (let i = 0; i < n; i++) {
      const y0 = yTop + i * (bh + hueco);
      this.bandas.push({ y0, y1: y0 + bh });
    }
    this.yBoca = yBot + cuello;

    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:hidden';
    const el = (tag, at) => {
      const e = document.createElementNS(NS, tag);
      for (const k in at) e.setAttribute(k, at[k]);
      return e;
    };
    const gB = el('g', {}), gP = el('g', {});
    svg.appendChild(gB); svg.appendChild(gP);
    // bandas (trapecios) y cuello de la boca
    this.polis = this.bandas.map((b) => {
      const a = this.hw(b.y0), c = this.hw(b.y1);
      const pts = [[cx - a, b.y0], [cx + a, b.y0], [cx + c, b.y1], [cx - c, b.y1]].map((p) => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
      const p = el('polygon', { points: pts, 'stroke-width': 5, 'stroke-linejoin': 'round' });
      gB.appendChild(p);
      return p;
    });
    const hb = wBot / 2;
    this.cuelloEl = el('path', {
      d: `M${(cx - hb).toFixed(1)},${yBot + 6} L${(cx - hb).toFixed(1)},${this.yBoca} M${(cx + hb).toFixed(1)},${yBot + 6} L${(cx + hb).toFixed(1)},${this.yBoca}`,
      stroke: 'color-mix(in srgb, var(--ink) 30%, transparent)', 'stroke-width': 5, 'stroke-linecap': 'round', fill: 'none',
    });
    gB.appendChild(this.cuelloEl);
    // reserva de partículas (cada partícula k usa el círculo k % M)
    this.M = 800;
    this.circ = [];
    for (let i = 0; i < this.M; i++) {
      const c = el('circle', { r: 7, cx: -50, cy: -50 });
      c.style.display = 'none';
      gP.appendChild(c);
      this.circ.push(c);
    }
    lienzo.appendChild(svg);

    // textos de los pasos, a la derecha de su banda
    const base = F45 ? (n > 4 ? 36 : 40) : (n > 4 ? 38 : 44);
    this.textos = P.pasos.map((txt, i) => {
      const b = this.bandas[i], izq = cx + this.hw(b.y0) + 26;
      const d = document.createElement('div');
      d.style.cssText = `position:absolute;left:${izq.toFixed(1)}px;width:${(W - izq - 6).toFixed(1)}px;top:${((b.y0 + b.y1) / 2).toFixed(1)}px;` +
        `font:800 ${base}px/1.08 Archivo,sans-serif;color:var(--ink);letter-spacing:-.01em;opacity:0`;
      d.textContent = txt;
      lienzo.appendChild(d);
      let fs = base;
      while (d.offsetHeight > bh + hueco && fs > 36) { fs -= 2; d.style.fontSize = fs + 'px'; }
      d.style.marginTop = -(d.offsetHeight / 2) + 'px';
      return d;
    });
    // cuánto descarta cada etapa: al final queda ~1 de cada 7
    this.tasa = 1 - Math.pow(0.14, 1 / n);
    this.v = F45 ? 250 : 280;       // caída, px/s
    this.dt = 0.035;                // una partícula nueva cada dt
  },

  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n;
    this.s0 = T.ini - 0.6;
    // bandas: contorno tenue desde la entrada; se encienden cuando la voz dice su paso
    const entra = eo((t - T.ini) / 0.5);
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.polis.forEach((pg, i) => {
      const st = ps[i] ? ps[i].start : T.fin, on = eo((t - st) / 0.5);
      const late = i === activo ? Math.sin(Math.PI * clamp((t - st) / 0.6)) : 0;
      const resp = i === activo ? 0.5 + 0.5 * Math.sin(2.2 * (t - st)) : 0;
      // la etapa que suena: velo y trazo en acento; las ya dichas: velo crema leve y trazo crema atenuado
      const es = i === activo;
      const relleno = Math.round(on * (es ? 24 + 6 * resp : 8));
      pg.setAttribute('fill', relleno > 0 ? `color-mix(in srgb, var(${es ? '--acento' : '--ink'}) ${relleno}%, transparent)` : 'transparent');
      const trazo = Math.round(14 + 16 * entra + 60 * on * (es ? 1 : 0.4));
      pg.setAttribute('stroke', es && on > 0.01
        ? `color-mix(in srgb, var(--acento) ${Math.round(100 * on)}%, color-mix(in srgb, var(--ink) ${trazo}%, transparent))`
        : `color-mix(in srgb, var(--ink) ${trazo}%, transparent)`);
      pg.setAttribute('stroke-width', (5 + 2 * late + (i === activo ? 1.2 * resp : 0)).toFixed(2));
    });
    this.cuelloEl.style.opacity = entra.toFixed(3);
    this.textos.forEach((d, i) => {
      const st = ps[i] ? ps[i].start : T.fin, e = eo((t - st) / 0.45);
      d.style.opacity = (e * (i < activo ? 0.5 : 1)).toFixed(3);
      d.style.transform = `translateX(${((1 - e) * 24).toFixed(1)}px)`;
    });
    // partículas
    const kmax = Math.floor((t - this.s0) / this.dt);
    const usados = new Array(this.M).fill(false);
    for (let k = Math.max(0, kmax - this.M + 1); k <= kmax; k++) {
      const e = this.particula(k, t, T), c = this.circ[k % this.M];
      if (!e || e.o <= 0.01) continue;
      usados[k % this.M] = true;
      c.style.display = '';
      c.setAttribute('cx', e.x.toFixed(1)); c.setAttribute('cy', e.y.toFixed(1));
      c.setAttribute('r', e.r.toFixed(2));
      c.setAttribute('fill', e.acento ? 'var(--acento)' : 'var(--ink)');
      c.setAttribute('opacity', e.o.toFixed(3));
    }
    usados.forEach((u, i) => { if (!u) this.circ[i].style.display = 'none'; });
  },
});
