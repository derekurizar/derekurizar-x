// Animación «concentracion-caja» (mecanismo proporcion): riesgo de concentración. Arriba un montón de monedas (lo que
// había: `rotulos.base`). Paso 1: casi todas ruedan a UNA sola caja (`rotulos.limite`, en acento) y unas pocas quedan
// sueltas a un lado. Paso 2: la caja se marca como la parte que pesa (relleno tenue de acento). Paso 3: la caja se
// agrieta y toda su parte se apaga de golpe; las sueltas siguen encendidas. Sirve para depósitos en un solo banco,
// exportaciones a un solo comprador, agua de una sola fuente: cualquier «todo en un solo lugar». Cámara quieta (A1),
// nada antes de la voz (A2); seek puro.
ANIM.registrar('concentracion-caja', {
  meta: {
    descripcion: 'riesgo de concentración: casi todas las monedas ruedan a una sola caja; la caja se agrieta y su parte se apaga, las sueltas quedan',
    mecanismo: 'proporcion',
    temas: ['concentración', 'riesgo', 'banco', 'quiebra', 'depósitos', 'offshore', 'un solo lugar', 'diversificar', 'dependencia'],
    pasos: [2, 3],
    ejemplo: { titulo: 'Riesgo de concentración', pasos: ['Un solo lugar', 'Riesgo de concentración', 'Si cae, cae todo'],
      rotulos: { base: 'Los ahorros', limite: 'Un banco' } },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, NS = 'http://www.w3.org/2000/svg', F45 = ctx.F45;
    this.V = V;
    this.n = P.pasos.length;
    const rot = P.rotulos || {};
    const tenue = (p) => `color-mix(in srgb, var(--ink) ${p}%, transparent)`;
    const r = F45 ? 20 : 22, d = 2 * r;
    // zonas: rótulo base + montón arriba, caja al centro, textos abajo
    const F = F45 ? 38 : 40, lineH = Math.round(F * 1.15);
    const textosH = this.n * lineH + 10;
    const yLabel = 0, pileTop = 52, filas = 6;
    const paso = d * 0.87;
    const pileBot = pileTop + r + (filas - 1) * paso;
    const bTop = pileBot + r + (F45 ? 46 : 70), bBot = H - textosH - (F45 ? 24 : 40);
    const bX = 60, bW = Math.min(470, W - 300), bH = bBot - bTop;
    const cx = W / 2;
    this.g = { bX, bW, bTop, bBot };
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const el = (tag, at, padre) => {
      const e = document.createElementNS(NS, tag);
      for (const k in at) e.setAttribute(k, at[k]);
      (padre || svg).appendChild(e); return e;
    };
    // la caja: relleno (tinte de acento en el paso 2), contorno en acento, grieta en el paso 3
    this.cajaFondo = el('rect', { x: bX, y: bTop, width: bW, height: bH, rx: 24,
      fill: 'color-mix(in srgb, var(--acento) 22%, transparent)' });
    this.caja = el('rect', { x: bX, y: bTop, width: bW, height: bH, rx: 24, fill: 'none', stroke: 'var(--acento)', 'stroke-width': 9 });
    // posiciones: montón (21 monedas en triángulo) → 18 en la caja, 3 sueltas a la derecha
    const ini = [];
    for (let k = 0; k < filas; k++) {
      const m = filas - k;
      for (let j = 0; j < m; j++) ini.push([cx + (j - (m - 1) / 2) * d * 1.02, pileBot - k * paso]);
    }
    const sueltas = [2, 9, 16];
    const cols = 6, rows = 3, gx = (bW - 60) / cols, gy = Math.min(d * 1.25, (bH - 110) / rows);
    const gridTop = bTop + 100 + ((bH - 110) - rows * gy) / 2;
    const xSuelta = bX + bW + (W - bX - bW) / 2;
    const ySuelta = (bTop + bBot) / 2;
    let a = 0, b = 0;
    this.monedas = ini.map((p0, i) => {
      let p1, suelta = sueltas.includes(i);
      if (suelta) { p1 = [xSuelta, ySuelta + (b - 1) * d * 1.35]; b++; }
      else { p1 = [bX + 30 + gx * (a % cols + 0.5), gridTop + gy * (Math.floor(a / cols) + 0.5)]; a++; }
      const g = el('g', {});
      el('circle', { cx: 0, cy: 0, r, fill: 'var(--ink)' }, g);
      el('circle', { cx: 0, cy: 0, r: r * 0.58, fill: 'none', stroke: 'var(--bg)', 'stroke-width': 4 }, g);
      return { g, p0, p1, suelta, orden: (i * 7) % 21 };
    });
    // grieta: zigzag de arriba abajo de la caja
    const gxs = [0.52, 0.44, 0.58, 0.41, 0.55, 0.47];
    const pts = gxs.map((f, i) => `${(bX + bW * f).toFixed(1)} ${(bTop + (bH * i) / (gxs.length - 1)).toFixed(1)}`);
    this.grieta = el('path', { d: 'M' + pts.join(' L'), fill: 'none', stroke: 'var(--bg)', 'stroke-width': 16,
      'stroke-linejoin': 'round', 'stroke-linecap': 'round' });
    this.grietaL = 0;
    for (let i = 1; i < gxs.length; i++) {
      const dx = bW * (gxs[i] - gxs[i - 1]), dy = bH / (gxs.length - 1);
      this.grietaL += Math.hypot(dx, dy);
    }
    this.grieta.style.strokeDasharray = this.grietaL.toFixed(1);
    lienzo.appendChild(svg);
    // textos (HTML para las fuentes de la casa)
    const caja = (css, txt) => {
      const e = document.createElement('div');
      e.style.cssText = 'position:absolute;' + css;
      e.textContent = txt;
      lienzo.appendChild(e);
      return e;
    };
    const cond = 'font-weight:900;font-stretch:62.5%;text-transform:uppercase;';
    this.base = caja(`left:0;width:${W}px;top:${yLabel}px;text-align:center;` +
      `font:600 ${F45 ? 30 : 34}px/1 'JetBrains Mono',monospace;color:var(--ink);opacity:.8;letter-spacing:.04em;`,
      rot.base || 'Lo que hay');
    this.nombre = caja(`left:${bX}px;width:${bW}px;top:${bTop + 24}px;text-align:center;` +
      `font:900 ${F45 ? 54 : 60}px/1 Archivo,sans-serif;${cond}color:var(--ink);letter-spacing:.01em;`,
      rot.limite || 'Un lugar');
    const yT = H - textosH + 6;
    this.textos = P.pasos.map((txt, i) => caja(`left:20px;width:${W - 40}px;top:${yT + i * lineH}px;text-align:center;` +
      `font:800 ${F}px/1.1 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);white-space:nowrap;`, txt));
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n;
    const s = (i) => (ps[i] ? ps[i].start : 1e9);
    const p = (i, a, b) => eo(clamp((t - s(i) - a) / (b - a)));
    const op = (e, o) => { e.style.opacity = o.toFixed(3); e.style.visibility = o > 0.001 ? '' : 'hidden'; };
    const iCae = n - 1;              // el último paso: la caja cae
    const iMarca = n >= 3 ? 1 : -1;  // con 3 pasos, el del medio marca la caja
    // paso 1: aparecen el montón y la caja; las monedas ruedan
    const ap = p(0, 0, 0.35);
    op(this.base, 0.8 * ap);
    op(this.caja, p(0, 0.1, 0.45));
    op(this.nombre, p(0, 0.1, 0.45) * (1 - 0.6 * p(iCae, 0.5, 0.8)));
    const marca = iMarca >= 0 ? p(iMarca, 0, 0.5) : 0;
    const cae = p(iCae, 0, 0.5), apaga = p(iCae, 0.45, 0.75);
    op(this.cajaFondo, marca * (1 - apaga));
    this.caja.setAttribute('stroke', apaga > 0.5 ? 'color-mix(in srgb, var(--ink) 30%, transparent)' : 'var(--acento)');
    this.caja.setAttribute('stroke-width', (9 + 5 * marca * (1 - apaga)).toFixed(1));
    this.grieta.style.strokeDashoffset = (this.grietaL * (1 - cae)).toFixed(1);
    op(this.grieta, cae > 0 ? 1 : 0);
    this.monedas.forEach((m) => {
      const k = p(0, 0.35 + m.orden * 0.03, 0.35 + m.orden * 0.03 + 0.5);
      const x = m.p0[0] + (m.p1[0] - m.p0[0]) * k, y = m.p0[1] + (m.p1[1] - m.p0[1]) * k;
      m.g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      op(m.g, ap * (m.suelta ? 1 : 1 - 0.82 * apaga));
    });
    this.textos.forEach((e, i) => {
      const entra = p(i, 0, 0.45), pasa = i < n - 1 ? p(i + 1, 0, 0.35) : 0;
      op(e, entra * (1 - 0.55 * pasa));
      e.style.marginTop = ((1 - entra) * 16).toFixed(1) + 'px';
    });
  },
});
