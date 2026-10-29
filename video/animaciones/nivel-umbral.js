// Animación «nivel-umbral» de la escena explica (mecanismo umbral): un recipiente con una línea límite punteada.
// El nivel empieza sobre la línea, cae por debajo con el primer paso (cambia a gris), la distancia que falta se marca
// con una flecha doble que respira; en el paso de cruce entran granos desde arriba, el nivel sube, cruza la línea y
// cambia de color; el último paso marca que quedó cerca de donde estaba al principio. Los pasos se leen en una lista
// debajo del recipiente. Siempre se mueve la superficie (ola) y suben burbujas. seek puro: todo es función de t.
// Estilo Noche: recipiente, línea y granos en crema; bajo la línea el líquido es crema tenue y lo único en acento es el
// líquido cuando vuelve a cruzarla (el cambio de estado).
ANIM.registrar('nivel-umbral', {
  meta: {
    descripcion: 'un nivel cae bajo una línea límite y luego la vuelve a cruzar: al cruzarla cambia de estado y de color',
    mecanismo: 'umbral',
    temas: ['límite', 'umbral', 'déficit', 'necesidad', 'nutrición', 'mínimo', 'recuperación', 'nivel'],
    pasos: [2, 6],
    ejemplo: {
      titulo: '¿Por qué se seca el pozo?',
      pasos: ['Baja el agua del pozo', 'Ya no alcanza la bomba', 'Llegan las lluvias', 'El pozo vuelve a dar agua'],
    },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length, fs = ctx.F45 ? 36 : 40;
    this.V = V; this.n = n;
    this.c = n >= 3 ? n - 2 : 1;                       // paso en que el nivel cruza la línea
    // lista de pasos abajo
    const lista = document.createElement('div');
    lista.style.cssText = 'position:absolute;left:0;right:0;bottom:0;display:flex;flex-direction:column;gap:12px;';
    this.items = P.pasos.map((txt, i) => {
      const el = document.createElement('div');
      el.style.cssText = `position:relative;padding-left:72px;font:800 ${fs}px/1.12 Archivo,sans-serif;letter-spacing:-.01em;` +
        'color:var(--ink);transform-origin:0 50%;';
      el.innerHTML = `<span style="position:absolute;left:0;top:calc(.56em - 26px);width:52px;height:52px;border-radius:50%;box-sizing:border-box;` +
        `border:5px solid var(--ink);display:flex;align-items:center;justify-content:center;font:600 36px/1 'JetBrains Mono',monospace">${i + 1}</span>`;
      el.appendChild(document.createTextNode(txt));
      lista.appendChild(el);
      return { el, dot: el.firstChild };
    });
    lienzo.appendChild(lista);
    const listaH = lista.offsetHeight || n * (fs * 1.12 + 12);
    // recipiente
    const top = 78, bottom = Math.max(top + 260, H - listaH - 46), th = bottom - top;
    const tw = Math.min(460, W * 0.58), tx = Math.max(24, (W - tw) / 2 - 40);
    const ins = 11, ix = tx + ins, iw = tw - 2 * ins, iy = top + ins, ih = th - 2 * ins;
    Object.assign(this, { top, bottom, tx, tw, ix, iw, iy, ih, LINE: 0.6, L0: 0.82, Lb: 0.3, La: 0.78 });
    this.yDe = (f) => iy + ih * (1 - f);
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); svg.appendChild(e); return e; };
    const defs = mk('defs', {});
    const clip = document.createElementNS(NS, 'clipPath'); clip.setAttribute('id', 'nu-clip');
    const cr = document.createElementNS(NS, 'rect');
    [['x', ix], ['y', iy], ['width', iw], ['height', ih], ['rx', 28]].forEach(([k, v]) => cr.setAttribute(k, v));
    clip.appendChild(cr); defs.appendChild(clip);
    const g = mk('g', { 'clip-path': 'url(#nu-clip)' });
    const liq = (fill) => { const p = document.createElementNS(NS, 'path'); p.setAttribute('fill', fill); g.appendChild(p); return p; };
    this.bajo = liq('color-mix(in srgb, var(--ink) 30%, transparent)');
    this.alto = liq('var(--acento)');
    this.burbujas = [0, 1, 2, 3, 4, 5].map((i) => {
      const b = document.createElementNS(NS, 'circle');
      b.setAttribute('r', 7 + (i % 3) * 2); b.setAttribute('cx', ix + 40 + ((i * 97) % Math.max(1, iw - 80)));
      b.setAttribute('fill', 'var(--bg)'); g.appendChild(b);
      return { b, per: 2.2 + (i % 3) * 0.55, fase: i / 6 };
    });
    // marca tenue del nivel inicial (adonde vuelve)
    this.marca = mk('line', { x1: ix + 18, x2: ix + iw - 18, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-dasharray': '10 12', 'stroke-linecap': 'round' });
    // flecha doble de lo que falta
    this.flecha = mk('path', { fill: 'none', stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
    // contorno del recipiente
    mk('rect', { x: tx, y: top, width: tw, height: th, rx: 38, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 });
    // línea límite y su rótulo
    this.yLinea = this.yDe(this.LINE);
    this.linea = mk('line', { x1: tx - 26, x2: tx + tw + 26, y1: this.yLinea, y2: this.yLinea, stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-dasharray': '24 14', 'stroke-linecap': 'round' });
    // tramo de la línea sobre el líquido (claro, para que se vea cuando el nivel la cruza)
    const g2 = mk('g', { 'clip-path': 'url(#nu-clip)' });
    this.lineaIn = document.createElementNS(NS, 'line');
    [['x1', tx - 26], ['x2', tx + tw + 26], ['y1', this.yLinea], ['y2', this.yLinea], ['stroke', 'var(--bg)'], ['stroke-width', 7], ['stroke-dasharray', '24 14'], ['stroke-linecap', 'round']].forEach(([k, v]) => this.lineaIn.setAttribute(k, v));
    g2.appendChild(this.lineaIn);
    const rot = mk('text', { x: tx + tw + 34, y: this.yLinea + 12, fill: 'var(--ink)' });
    rot.style.font = "600 36px 'JetBrains Mono',monospace"; rot.textContent = 'LÍMITE';
    this.rot = rot;
    // granos que entran desde arriba en el paso de cruce
    this.granos = Array.from({ length: 16 }, (_, i) => {
      const e = document.createElementNS(NS, 'circle');
      // granos en crema y crema atenuada (el acento queda para el líquido que cruza)
      e.setAttribute('r', 8 + (i % 3) * 3); e.setAttribute('fill', ['var(--ink)', 'var(--a2)'][i % 2]);
      e.setAttribute('cx', ix + 50 + (((i * 37) % 11) / 10) * (iw - 100));
      svg.appendChild(e);
      return { e, d: ((i * 7) % 16) / 16 * 1.3 };
    });
    lienzo.appendChild(svg);
    // el rótulo no puede salirse del lienzo
    const rw = rot.getComputedTextLength ? rot.getComputedTextLength() : 130;
    if (tx + tw + 34 + rw > W - 4) { rot.setAttribute('x', tx + tw - rw - 16); rot.setAttribute('y', this.yLinea - 18); }
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n, c = this.c;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    const s0 = ps[0].start, sc = ps[c].start, sf = ps[n - 1].start;
    const baja = eo(clamp((t - s0) / 1.3)), sube = eo(clamp((t - sc) / 1.8));
    const L = this.L0 + (this.Lb - this.L0) * baja + (this.La - this.Lb) * sube;
    const y = this.yDe(L), ix = this.ix, iw = this.iw, fondo = this.iy + this.ih + 4;
    // superficie con ola continua
    let d = `M${ix - 2} ${fondo}`;
    for (let k = 0; k <= 16; k++) {
      const x = ix + (iw * k) / 16;
      d += ` L${x.toFixed(1)} ${(y + 7 * Math.sin(x / 55 + t * 2.3)).toFixed(1)}`;
    }
    d += ` L${ix + iw + 2} ${fondo} Z`;
    this.bajo.setAttribute('d', d); this.alto.setAttribute('d', d);
    const arriba = clamp((L - this.LINE) / 0.06 + 0.5);
    this.alto.style.opacity = arriba.toFixed(3);
    // burbujas: suben del fondo a la superficie, siempre
    this.burbujas.forEach(({ b, per, fase }) => {
      const u = ((((t / per) + fase) % 1) + 1) % 1;
      b.setAttribute('cy', (fondo - 20 - (fondo - 20 - (y + 16)) * u).toFixed(1));
      b.style.opacity = (0.55 * Math.sin(Math.PI * u)).toFixed(3);
    });
    // marca del nivel inicial: aparece cuando el nivel se va y se afirma en el último paso
    const ym = this.yDe(this.L0);
    this.marca.setAttribute('y1', ym); this.marca.setAttribute('y2', ym);
    const fin = n > c + 1 ? eo(clamp((t - sf) / 0.5)) : sube;
    this.marca.style.opacity = (0.3 * baja + 0.6 * fin * (0.85 + 0.15 * Math.sin(2 * Math.PI * t / 1.6))).toFixed(3);
    // flecha doble: la distancia que falta hasta la línea
    const yl = this.yLinea, gap = y - yl, xa = ix + iw / 2;
    const vis = clamp((t - (s0 + 0.9)) / 0.5) * (1 - clamp((L - (this.LINE - 0.04)) / 0.03));
    const fuerte = c > 1 ? 0.55 + 0.45 * eo(clamp((t - ps[1].start) / 0.4)) : 1;
    if (gap > 40) {
      const a = yl + 14, b = y - 18;
      this.flecha.setAttribute('d', `M${xa} ${a} L${xa} ${b} M${xa - 18} ${a + 20} L${xa} ${a} L${xa + 18} ${a + 20} M${xa - 18} ${b - 20} L${xa} ${b} L${xa + 18} ${b - 20}`);
    } else this.flecha.setAttribute('d', '');
    this.flecha.style.opacity = (vis * fuerte * (0.8 + 0.2 * Math.sin(2 * Math.PI * t / 1.4))).toFixed(3);
    // línea límite: se marca más cuando el nivel la cruza de nuevo
    this.linea.style.strokeDashoffset = (-t * 18).toFixed(1);
    this.linea.style.opacity = (0.35 + 0.65 * eo(clamp((t - T.ini) / 0.5))).toFixed(3);
    this.rot.style.opacity = this.linea.style.opacity;
    this.lineaIn.style.strokeDashoffset = this.linea.style.strokeDashoffset;
    this.lineaIn.style.opacity = (0.9 * arriba).toFixed(3);
    // granos: caen sobre la superficie durante el cruce
    const top = this.top - 62;
    this.granos.forEach(({ e, d: dl }) => {
      const u = (t - (sc - 0.15) - dl) / 0.75;
      if (u < 0 || u > 1) { e.style.opacity = 0; return; }
      e.setAttribute('cy', (top + (y - top) * u * u).toFixed(1));
      e.style.opacity = (u > 0.85 ? (1 - u) / 0.15 : 1).toFixed(3);
    });
    // lista de pasos
    this.items.forEach(({ el, dot }, i) => {
      const s = ps[i].start, entra = eo(clamp((t - s) / 0.45)), fantasma = 0.28 * eo(clamp((t - T.ini) / 0.5));
      const respira = i === activo ? 1 + 0.012 * Math.sin(2 * Math.PI * (t - s) / 1.6) : 1;
      el.style.opacity = Math.max(fantasma, entra * (i < activo ? 0.5 : 1)).toFixed(3);
      el.style.transform = `translateX(${((1 - entra) * -30).toFixed(1)}px) scale(${respira.toFixed(4)})`;
      const lleno = i === activo && entra > 0.5;
      dot.style.background = lleno ? 'var(--ink)' : 'transparent';
      dot.style.color = lleno ? 'var(--bg)' : 'var(--ink)';
    });
  },
});
