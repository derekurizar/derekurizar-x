// Animación «faltante-seguro» (mecanismo balance): lo que se debe contra lo que alcanza a pagar lo que hay. Los bienes
// caen a una caja; al venderse, su dinero baja y llena casi toda la barra de lo que se debe (con sus personas encima);
// queda un hueco; un fondo de respaldo, llenado por cuotas de varios, abre su llave y lo completa; un camino punteado
// de regreso del resto al fondo queda esperando. Cada parte entra cuando la voz dice su paso y luego queda quieta.
// Estilo Noche: el fondo de respaldo es lo único en acento desde que entra (antes, el hueco).
ANIM.registrar('faltante-seguro', {
  meta: {
    descripcion: 'liquidación con respaldo: los bienes pagan casi toda la deuda y un fondo llenado por cuotas cubre el hueco y espera recuperarlo',
    mecanismo: 'balance',
    temas: ['quiebra', 'banco', 'seguro de depósitos', 'fideicomiso', 'liquidación', 'deuda', 'respaldo'],
    pasos: [4, 5],
    ejemplo: {
      titulo: 'Quién cobra en un banco caído',
      pasos: ['Bienes al fideicomiso', 'Se venden para pagar', 'Si no alcanza', 'El FOPA pone lo que falta', 'Espera recuperarlo'],
    },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, F = ctx.F45;
    const NS = 'http://www.w3.org/2000/svg';
    const sy = H / 900;
    const Y = (v) => v * sy;
    this.V = V;
    this.n = P.pasos.length;
    const R = P.rotulos || {};
    const mk = (tag, attrs, padre) => {
      const e = document.createElementNS(NS, tag);
      for (const k in attrs) e.setAttribute(k, attrs[k]);
      (padre || svg).appendChild(e);
      return e;
    };
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    lienzo.appendChild(svg);
    const txt = (x, y, s, cls, anchor, padre) => {
      const e = mk('text', { x, y, 'text-anchor': anchor || 'middle' }, padre);
      e.textContent = s;
      e.style.cssText = cls;
      return e;
    };
    const mono = `font:600 ${F ? 30 : 32}px 'JetBrains Mono',monospace;fill:var(--ink);opacity:.75`;

    // pie: el paso que la voz dice (solo el activo)
    const pie = document.createElement('div');
    pie.style.cssText = `position:absolute;left:0;right:0;top:0;height:${Y(70)}px;display:flex;align-items:center;justify-content:center;` +
      `font:800 ${F ? 40 : 46}px/1.05 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);text-align:center`;
    lienzo.appendChild(pie);
    this.pie = pie;
    this.textos = P.pasos;

    // ── caja de los bienes (paso 0)
    const bx = W * 0.04, bw = W * 0.38, by = Y(230), bh = Y(200);
    this.gCaja = mk('g', {});
    mk('rect', { x: bx, y: by, width: bw, height: bh, rx: 22, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 }, this.gCaja);
    const palabra = /fideicomiso/i.test(P.pasos[0]) ? 'FIDEICOMISO' : '';
    if (palabra) txt(bx + bw / 2, by + Y(48), palabra, mono, 'middle', this.gCaja);
    this.gBase = mk('g', {});
    txt(bx + bw / 2, Y(112), R.base || 'Los bienes', mono, 'middle', this.gBase);
    const lado = Math.min(bw * 0.3, Y(62));
    this.bienes = [0, 1, 2, 3].map((i) => {
      const c = i % 2, f = Math.floor(i / 2);
      const x0 = bx + bw / 2 - lado * 2.2 + i * lado * 1.1;
      const y0 = Y(135);
      const x1 = bx + bw / 2 - lado * 1.08 + c * lado * 1.16;
      const y1 = by + Y(70) + f * (lado * 1.08);
      const r = mk('rect', { width: lado, height: lado, rx: 8, fill: 'var(--ink)' });
      return { r, x0, y0, x1, y1 };
    });

    // ── fila de los que esperan cobrar y su barra (paso 1)
    const fx = W * 0.04, fw = W * 0.92, fy = Y(745), fh = Y(78);
    this.gFila = mk('g', {});
    txt(fx, fy + fh + Y(44), R.limite || 'Lo que se debe', mono, 'start', this.gFila);
    const np = 7;
    for (let i = 0; i < np; i++) {
      const cx = fx + fw * (i + 0.5) / np, cab = Y(17);
      mk('circle', { cx, cy: Y(630), r: cab, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5 }, this.gFila);
      mk('path', { d: `M${cx - Y(30)} ${Y(712)} Q${cx - Y(30)} ${Y(658)} ${cx} ${Y(658)} Q${cx + Y(30)} ${Y(658)} ${cx + Y(30)} ${Y(712)} Z`,
        fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linejoin': 'round' }, this.gFila);
    }
    mk('rect', { x: fx, y: fy, width: fw, height: fh, rx: 16, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 }, this.gFila);
    const parte = 0.74;
    this.barra = { x: fx + 6, y: fy + 6, w: fw - 12, h: fh - 12, parte };
    this.llenoBienes = mk('rect', { x: fx + 6, y: fy + 6, width: 0, height: fh - 12, rx: 10, fill: 'color-mix(in srgb, var(--ink) 55%, transparent)' });
    // chorro de la venta: de la caja a la barra
    const sx = fx + fw * 2 / 7;
    this.chorro1 = mk('path', { d: `M${sx} ${by + bh + 6} L${sx} ${fy - Y(4)}`, fill: 'none', stroke: 'color-mix(in srgb, var(--ink) 55%, transparent)',
      'stroke-width': 14, 'stroke-linecap': 'round' });
    this.L1 = this.chorro1.getTotalLength();
    this.chorro1.style.strokeDasharray = this.L1;

    // ── el hueco (paso 2)
    const hx = fx + 6 + (fw - 12) * parte, hw = (fw - 12) * (1 - parte);
    this.hueco = mk('rect', { x: hx + 3, y: fy + 9, width: hw - 6, height: fh - 18, rx: 8, fill: 'none', stroke: 'var(--acento)',
      'stroke-width': 6, 'stroke-dasharray': '16 10' });
    this.huecoLleno = mk('rect', { x: hx, y: fy + 6, width: hw, height: 0, rx: 10, fill: 'var(--acento)' });
    this.hx = hx; this.hw = hw; this.fy = fy; this.fh = fh;

    // ── el fondo de respaldo (paso 3): tanque con cuotas que caen de arriba y una llave abajo
    const tx = W * 0.58, tw = W * 0.36, ty = Y(240), th = Y(220);
    this.t = { x: tx, y: ty, w: tw, h: th };
    this.gTanque = mk('g', {});
    txt(tx + tw / 2, Y(112), 'Cuotas', mono, 'middle', this.gTanque);
    for (let i = 0; i < 3; i++) {
      const cx = tx + tw * (0.2 + i * 0.3), b = Y(135), a = Y(34);
      mk('path', { d: `M${cx - a} ${b + a * 0.55} L${cx} ${b} L${cx + a} ${b + a * 0.55} Z M${cx - a * 0.8} ${b + a * 0.7} L${cx - a * 0.8} ${b + a * 1.5} ` +
        `M${cx} ${b + a * 0.7} L${cx} ${b + a * 1.5} M${cx + a * 0.8} ${b + a * 0.7} L${cx + a * 0.8} ${b + a * 1.5} M${cx - a} ${b + a * 1.6} L${cx + a} ${b + a * 1.6}`,
        fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, this.gTanque);
    }
    const clipId = 'fs-clip-' + (F ? 'a' : 'b');
    const defs = mk('defs', {}, this.gTanque);
    const cp = mk('clipPath', { id: clipId }, defs);
    mk('rect', { x: tx, y: ty, width: tw, height: th, rx: 22 }, cp);
    this.liquido = mk('rect', { x: tx, y: ty + th, width: tw, height: 0, fill: 'var(--acento)', 'clip-path': `url(#${clipId})` }, this.gTanque);
    mk('rect', { x: tx, y: ty, width: tw, height: th, rx: 22, fill: 'none', stroke: 'var(--acento)', 'stroke-width': 7 }, this.gTanque);
    const nombre = (P.acento || (P.pasos[3] || '').match(/\b[A-ZÁÉÍÓÚÑ]{3,}\b/) || [''])[0] || P.acento || '';
    this.nombre = txt(tx + tw / 2, ty + th / 2 + Y(26), String(nombre).toUpperCase(), '', 'middle', this.gTanque);
    this.nombre.style.cssText = `font:900 ${F ? 66 : 76}px Archivo,sans-serif;font-stretch:62.5%;text-transform:uppercase;fill:var(--ink)`;
    this.g0 = Y(200);
    this.gotas = [0, 1, 2].map((i) => mk('circle', { cx: tx + tw * (0.2 + i * 0.3), cy: Y(230), r: Y(11), fill: 'var(--acento)' }));
    // llave y chorro del fondo al hueco
    const vx = hx + hw / 2;
    mk('path', { d: `M${vx - Y(22)} ${ty + th + Y(4)} L${vx + Y(22)} ${ty + th + Y(4)}`, stroke: 'var(--acento)', 'stroke-width': 10, 'stroke-linecap': 'round' }, this.gTanque);
    this.chorro2 = mk('path', { d: `M${vx} ${ty + th + Y(10)} L${vx} ${fy - Y(4)}`, fill: 'none', stroke: 'var(--acento)', 'stroke-width': 14, 'stroke-linecap': 'round' });
    this.L2 = this.chorro2.getTotalLength();
    this.chorro2.style.strokeDasharray = this.L2;

    // ── camino de regreso, punteado (paso 4): de la caja de bienes al fondo
    const p0 = [bx + bw + Y(10), by + bh * 0.35], p2 = [tx - Y(16), ty + th * 0.35];
    const ctrl = [(p0[0] + p2[0]) / 2, by - Y(40)];
    const guia = mk('path', { d: `M${p0[0]} ${p0[1]} Q${ctrl[0]} ${ctrl[1]} ${p2[0]} ${p2[1]}`, fill: 'none', stroke: 'none' });
    const Lg = guia.getTotalLength(), nd = 9;
    this.puntos = [];
    for (let i = 0; i < nd; i++) {
      const p = guia.getPointAtLength(Lg * i / (nd - 1) * 0.92);
      this.puntos.push(mk('circle', { cx: p.x.toFixed(1), cy: p.y.toFixed(1), r: Y(7), fill: 'var(--ink)' }));
    }
    const pf = guia.getPointAtLength(Lg), pa = guia.getPointAtLength(Lg - 1);
    const ang = Math.atan2(pf.y - pa.y, pf.x - pa.x), k = Y(22);
    const ax = (d) => pf.x - k * Math.cos(ang + d), ay = (d) => pf.y - k * Math.sin(ang + d);
    this.punta = mk('path', { d: `M${ax(0.6)} ${ay(0.6)} L${pf.x} ${pf.y} L${ax(-0.6)} ${ay(-0.6)}`, fill: 'none', stroke: 'var(--ink)',
      'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = ps.length;
    const s = (i) => (i < n ? ps[i].start : Infinity);
    const op = (e, v) => { e.style.opacity = v.toFixed(3); };
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });

    // pie con el paso activo
    if (activo < 0) { this.pie.textContent = ''; this.pie.style.opacity = '0'; }
    else { this.pie.textContent = this.textos[activo]; op(this.pie, eo((t - s(activo)) / 0.4)); }

    // paso 0: la caja y los bienes que caen dentro
    const a0 = eo((t - s(0)) / 0.35);
    op(this.gCaja, a0); op(this.gBase, a0);
    const vendido = eo((t - s(1)) / 1.0);
    this.bienes.forEach((b, i) => {
      const u = eo((t - s(0) - 0.35 - i * 0.12) / 0.6);
      const x = b.x0 + (b.x1 - b.x0) * u, y = b.y0 + (b.y1 - b.y0) * u;
      b.r.setAttribute('x', x.toFixed(1)); b.r.setAttribute('y', y.toFixed(1));
      op(b.r, a0 * (1 - 0.7 * vendido));
    });

    // paso 1: la fila aparece, la venta baja y llena casi toda la barra
    const a1 = eo((t - s(1)) / 0.35);
    op(this.gFila, a1);
    const d1 = clamp((t - s(1)) / 0.4);
    this.chorro1.style.strokeDashoffset = (this.L1 * (1 - d1)).toFixed(1);
    op(this.chorro1, d1 > 0 ? 1 : 0);
    const f1 = eo((t - s(1) - 0.3) / 1.1);
    this.llenoBienes.setAttribute('width', (this.barra.w * this.barra.parte * f1).toFixed(1));

    // paso 2: el hueco que queda
    const a2 = eo((t - s(2)) / 0.4);
    const a3 = eo((t - s(3)) / 0.35);
    op(this.hueco, a2);
    this.hueco.setAttribute('stroke', t >= s(3) ? 'var(--ink)' : 'var(--acento)');

    // paso 3: el fondo entra, recibe las cuotas, abre la llave y llena el hueco
    op(this.gTanque, a3);
    const t3 = t - s(3);
    this.gotas.forEach((g, i) => {
      const u = clamp((t3 - 0.15 - i * 0.1) / 0.45);
      g.setAttribute('cy', (this.g0 + (this.t.y + 30 - this.g0) * u).toFixed(1));
      op(g, u > 0 && u < 1 ? Math.sin(Math.PI * u) : 0);
    });
    const sube = eo((t3 - 0.2) / 0.6), baja = eo((t3 - 0.9) / 0.6);
    const nivel = t >= s(3) ? 0.45 + 0.4 * sube - 0.3 * baja : 0;
    const hl = this.t.h * nivel;
    this.liquido.setAttribute('y', (this.t.y + this.t.h - hl).toFixed(1));
    this.liquido.setAttribute('height', hl.toFixed(1));
    this.nombre.style.fill = nivel > 0.5 ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)';
    const d2 = clamp((t3 - 0.8) / 0.3);
    this.chorro2.style.strokeDashoffset = (this.L2 * (1 - d2)).toFixed(1);
    op(this.chorro2, d2 > 0 ? 1 : 0);
    const f2 = eo((t3 - 0.9) / 0.6);
    const hh = (this.fh - 12) * f2;
    this.huecoLleno.setAttribute('y', (this.fy + 6 + (this.fh - 12) - hh).toFixed(1));
    this.huecoLleno.setAttribute('height', hh.toFixed(1));

    // paso 4: el camino punteado de regreso al fondo
    const t4 = t - s(4), m = this.puntos.length;
    this.puntos.forEach((c, i) => op(c, clamp((t4 - i * 0.08) / 0.2)));
    op(this.punta, clamp((t4 - m * 0.08) / 0.25));
  },
});
