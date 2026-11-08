// Animación «presion-limite» de la escena explica (mecanismo umbral): un medidor vertical. Abajo, si la escena lo nombra
// (P.rotulos.base: «La plaza»), la presión que ya había; cada paso que dice la voz apila un tramo nuevo con su nombre al
// lado y el nivel sube hacia la línea de arriba, que dice qué pasa si se cruza (P.rotulos.limite: «Renuncia»). Al final
// queda cerca de la línea, sin cruzarla; una flecha fija marca lo que falta.
// Cámara quieta (2026-11-07): se mueve SOLO lo que entra cuando la voz lo dice; entre pasos, nada se mueve (A1). Ningún
// paso se ve antes de que la voz lo diga (A2). Sin marcas de escala: la presión no se mide con números.
// En una escena que `continua` la anterior (P.previos), los primeros pasos ya están dibujados desde el cuadro 0.
// Estilo Noche: columna, base y tramos viejos en crema; lo único en acento es el tramo del paso que suena.
ANIM.registrar('presion-limite', {
  meta: {
    descripcion: 'medidor: la presión que ya había y un tramo por paso que lo acerca a la línea del desenlace, sin cruzarla',
    mecanismo: 'umbral',
    temas: ['presión', 'límite', 'renuncia', 'crisis', 'acumulación', 'umbral', 'tensión', 'protesta', 'medidor'],
    pasos: [2, 5],
    ejemplo: {
      titulo: '¿Por qué renunció el ministro?',
      pasos: ['Las protestas', 'La prensa', 'Los diputados', 'Su propio partido'],
    },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length, fs = ctx.F45 ? 36 : 40;
    const R = P.rotulos || {}, previos = Math.min(n, P.previos || 0);
    Object.assign(this, { V, n, previos });
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    const mk = (tag, at, padre) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); (padre || svg).appendChild(e); return e; };
    // columna (deja arriba sitio para el rótulo de la línea)
    const cw = Math.min(150, W * 0.19), cx = Math.max(40, W * 0.08), top = 76, bottom = H - 20, ch = bottom - top;
    const ins = 10, ix = cx + ins, iw = cw - 2 * ins, iy = top + ins, ih = ch - 2 * ins;
    const LINE = 0.95, L0 = R.base ? 0.4 : 0, Lf = 0.86;
    this.niveles = [L0];
    const tot = Math.max(n, P.total || n);   // con una escena que la continúa, deja sitio a sus pasos (sin saltos en el corte)
    for (let i = 1; i <= n; i++) this.niveles.push(L0 + (Lf - L0) * i / tot);
    const yDe = (f) => iy + ih * (1 - f);
    Object.assign(this, { cx, cw, ix, iw, iy, ih, yDe, LINE, L0 });
    const defs = mk('defs', {});
    const clip = mk('clipPath', { id: 'pl-clip' }, defs);
    mk('rect', { x: ix, y: iy, width: iw, height: ih, rx: 22 }, clip);
    const g = mk('g', { 'clip-path': 'url(#pl-clip)' });
    this.fondo = iy + ih + 4;
    this.base = mk('rect', { x: ix, width: iw, fill: 'color-mix(in srgb, var(--ink) 34%, transparent)' }, g);
    this.tramos = P.pasos.map(() => mk('rect', { x: ix, width: iw, fill: 'var(--ink)' }, g));
    this.separ = P.pasos.map(() => mk('line', { x1: ix, x2: ix + iw, stroke: 'var(--bg)', 'stroke-width': 6 }, g));
    mk('rect', { x: cx, y: top, width: cw, height: ch, rx: 32, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 });
    // la línea del desenlace, fija
    const yl = yDe(LINE);
    this.yl = yl;
    this.linea = mk('line', { x1: cx - 30, x2: W - 10, y1: yl, y2: yl, stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-dasharray': '24 14', 'stroke-linecap': 'round' });
    this.rot = document.createElement('div');
    this.rot.style.cssText = `position:absolute;right:10px;top:${yl - 62}px;font:600 ${ctx.F45 ? 32 : 36}px 'JetBrains Mono',monospace;` +
      'letter-spacing:.06em;text-transform:uppercase;color:var(--ink);white-space:nowrap';
    this.rot.textContent = R.limite || 'Límite';
    this.flecha = mk('path', { fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', opacity: 0.6 });
    lienzo.appendChild(svg);
    lienzo.appendChild(this.rot);
    // textos: la base y un texto por paso, a la altura de su tramo (sin encimarse: se apilan de abajo hacia arriba)
    const tx = cx + cw + 40, tw = W - tx - 8;
    const texto = (txt, tenue) => {
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:${tx - 54}px;width:${tw + 54}px;padding-left:54px;box-sizing:border-box;` +
        `font:800 ${fs}px/1.08 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);` + (tenue ? 'opacity:.62;' : '');
      el.innerHTML = '<span style="position:absolute;left:0;top:50%;width:34px;height:7px;margin-top:-3.5px;border-radius:4px;background:currentColor"></span>';
      el.appendChild(document.createTextNode(txt));
      lienzo.appendChild(el);
      return el;
    };
    this.baseTxt = R.base ? texto(R.base, true) : null;
    this.items = P.pasos.map((txt) => texto(txt, false));
    const todos = (this.baseTxt ? [{ el: this.baseTxt, ym: (yDe(0) + yDe(L0)) / 2 }] : [])
      .concat(this.items.map((el, i) => ({ el, ym: (yDe(this.niveles[i]) + yDe(this.niveles[i + 1])) / 2 })));
    let techo = H - 4;
    todos.forEach((x) => {
      const h = x.el.offsetHeight || fs * 1.1;
      const y = Math.max(yl + 24, Math.min(techo - h, x.ym - h / 2));
      x.el.style.top = y.toFixed(1) + 'px';
      techo = y - 10;
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, yDe = this.yDe, previos = this.previos;
    // un paso nunca entra antes que la base (el rótulo de acto puede correr el inicio del lienzo)
    const listo = (i) => i < previos ? 1 : eo(clamp((t - Math.max(ps[i].start, T.ini + 0.6)) / 0.7));
    let activo = -1;
    ps.forEach((p, i) => { if (i < previos || t >= p.start) activo = i; });
    // base: sube al abrir la escena (en una continuación ya está)
    const sube = previos ? 1 : eo(clamp((t - T.ini) / 0.6));
    const yb = yDe(this.L0 * sube);
    this.base.setAttribute('y', yb.toFixed(1)); this.base.setAttribute('height', Math.max(0, this.fondo - yb).toFixed(1));
    if (this.baseTxt) this.baseTxt.style.opacity = (0.62 * sube).toFixed(3);
    let L = this.L0 * sube;
    this.tramos.forEach((r, i) => {
      const u = listo(i), a = this.niveles[i], b = this.niveles[i + 1];
      const hi = a + (b - a) * u, ya = yDe(a), yh = yDe(hi);
      r.setAttribute('y', yh.toFixed(1)); r.setAttribute('height', Math.max(0, ya - yh).toFixed(1));
      r.setAttribute('fill', i === activo ? 'var(--acento)' : 'var(--ink)');
      r.style.opacity = i === activo ? '1' : '0.62';
      const s = this.separ[i];
      s.setAttribute('y1', ya); s.setAttribute('y2', ya); s.style.opacity = u > 0.05 ? '1' : '0';
      if (u > 0) L = hi;
    });
    // la línea y su rótulo aparecen con el lienzo y se quedan quietos
    const op = (previos ? 1 : eo(clamp((t - T.ini) / 0.5))).toFixed(3);
    this.linea.style.opacity = op; this.rot.style.opacity = op;
    // flecha fija de lo que falta (cambia solo cuando sube el nivel)
    const xa = this.cx + this.cw + 18, a = this.yl + 8, b = yDe(L) - 8;
    if (b - a > 22) {
      const pt = Math.min(12, (b - a) / 3);
      this.flecha.setAttribute('d', `M${xa} ${a} L${xa} ${b} M${xa - pt} ${a + pt} L${xa} ${a} L${xa + pt} ${a + pt} M${xa - pt} ${b - pt} L${xa} ${b} L${xa + pt} ${b - pt}`);
    } else this.flecha.setAttribute('d', '');
    this.flecha.style.opacity = (0.6 * sube).toFixed(3);
    // cada texto entra cuando la voz dice su paso; antes no está (ni fantasma)
    this.items.forEach((el, i) => {
      const entra = listo(i);
      el.style.opacity = (entra * (i < activo ? 0.55 : 1)).toFixed(3);
      el.style.transform = `translateX(${((1 - entra) * -24).toFixed(1)}px)`;
    });
  },
});
