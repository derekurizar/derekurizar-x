// Animación «riel-productos» (mecanismo cronologia): un riel horizontal de tiempo donde primero se levanta el origen
// (un edificio: la empresa, el taller, la planta) y después, uno al lado del otro, caen los sacos de lo que fue
// produciendo. Cada estación entra cuando la voz dice su paso (T.pasos[i].start): el riel se alarga hasta ella, el
// objeto se levanta o cae en ≤ 0.6 s y su rótulo aparece debajo; luego todo queda quieto (A1). Un paso «1901 · Cemento»
// pone el año dentro del objeto. Estilo Noche: lo único en acento es la estación activa; lo ya dicho, en crema atenuada.
// Todo es función de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
ANIM.registrar('riel-productos', {
  meta: {
    descripcion: 'riel de tiempo horizontal: se levanta el origen (un edificio) y a su lado caen, uno tras otro, los sacos de lo que produjo',
    mecanismo: 'cronologia',
    temas: ['historia', 'empresa', 'productos', 'origen', 'fábrica', 'línea de tiempo', 'marca'],
    pasos: [2, 4],
    ejemplo: { titulo: 'Del molino a la harina', pasos: ['Molino San Juan', 'Maíz en grano', '1950 · Harina de maíz'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, F = ctx.F45;
    this.V = V;
    const NS = 'http://www.w3.org/2000/svg';
    const m = 30, w = (ctx.ancho - 2 * m) / n;
    const s = Math.min(w * 0.9, F ? 250 : 280);       // ancho del objeto
    const oh = s * 1.3;                                // alto del objeto
    const fs = F ? 44 : 48, lh = fs * 1.12;
    const bloque = oh + 34 + 3 * lh;                    // objeto + riel + hasta 3 líneas de rótulo
    const yR = Math.max(oh + 20, (ctx.alto - bloque) / 2 + oh);
    this.xs = P.pasos.map((_, i) => m + w * (i + 0.5));
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', ctx.ancho); svg.setAttribute('height', ctx.alto);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const el = (tag, attrs, padre) => {
      const e = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
      (padre || svg).appendChild(e);
      return e;
    };
    // el riel: un tramo por estación, de la anterior (o del borde) hasta esta
    this.tramos = this.xs.map((x, i) => {
      const x0 = i === 0 ? x - w * 0.45 : this.xs[i - 1];
      const l = el('line', { x1: x0, y1: yR, x2: x, y2: yR, stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-linecap': 'round' });
      const L = Math.abs(x - x0) || 1;
      l.style.strokeDasharray = L;
      return { l, L };
    });
    this.estaciones = P.pasos.map((txt, i) => {
      const mt = /^\s*(\d{3,4})\s*·\s*(.+)$/.exec(txt);
      const fecha = mt ? mt[1] : '', texto = mt ? mt[2] : txt;
      const cx = this.xs[i], yb = yR - 4;
      const g = el('g', {});
      const formas = [];
      if (i === 0) {
        // el origen: un edificio con techo a dos aguas y chimenea
        const bw = s, bh = oh * 0.58;
        formas.push(el('path', { d: `M${cx + bw * 0.22} ${yb - bh - bw * 0.16} L${cx + bw * 0.22} ${yb - oh} L${cx + bw * 0.36} ${yb - oh} L${cx + bw * 0.36} ${yb - bh - bw * 0.06}`, 'stroke-width': 6, 'stroke-linejoin': 'round' }, g));
        formas.push(el('path', { d: `M${cx - bw / 2} ${yb} L${cx - bw / 2} ${yb - bh} L${cx} ${yb - bh - bw * 0.3} L${cx + bw / 2} ${yb - bh} L${cx + bw / 2} ${yb} Z`, 'stroke-width': 6, 'stroke-linejoin': 'round' }, g));
        const puerta = el('rect', { x: cx - bw * 0.11, y: yb - bh * 0.5, width: bw * 0.22, height: bh * 0.5, 'stroke-width': 5 }, g);
        puerta.dataset.hueco = '1';
        formas.push(puerta);
      } else {
        // un saco: boca más angosta, amarrado arriba
        const sw = s * 0.8, sh = oh * 0.96;
        formas.push(el('path', {
          d: `M${cx - sw * 0.46} ${yb} Q${cx - sw * 0.54} ${yb - sh * 0.45} ${cx - sw * 0.4} ${yb - sh * 0.82} L${cx - sw * 0.5} ${yb - sh} ` +
             `L${cx + sw * 0.5} ${yb - sh} L${cx + sw * 0.4} ${yb - sh * 0.82} Q${cx + sw * 0.54} ${yb - sh * 0.45} ${cx + sw * 0.46} ${yb} Z`,
          'stroke-width': 6, 'stroke-linejoin': 'round',
        }, g));
        const amarre = el('line', { x1: cx - sw * 0.38, y1: yb - sh * 0.8, x2: cx + sw * 0.38, y2: yb - sh * 0.8, 'stroke-width': 6, 'stroke-linecap': 'round' }, g);
        amarre.dataset.linea = '1';
        formas.push(amarre);
      }
      let tf = null;
      if (fecha) {
        tf = el('text', { x: cx, y: yb - oh * (i === 0 ? 0.62 : 0.3), 'text-anchor': 'middle', 'dominant-baseline': 'middle' }, g);
        tf.textContent = fecha;
        tf.style.cssText = `font:900 ${Math.round(s * 0.34)}px Archivo,sans-serif;font-stretch:62.5%;text-transform:uppercase`;
        if (i === 0) tf.setAttribute('y', yb - oh * 0.28);
      }
      const rot = document.createElement('div');
      rot.style.cssText = `position:absolute;left:${cx - w / 2 + 6}px;width:${w - 12}px;top:${yR + 30}px;text-align:center;` +
        `font:800 ${fs}px/1.12 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);overflow-wrap:break-word`;
      rot.textContent = texto;
      return { g, formas, tf, rot, cx, yb };
    });
    lienzo.appendChild(svg);
    this.estaciones.forEach((e) => lienzo.appendChild(e.rot));
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.tramos.forEach((tr, i) => {
      const d = clamp((t - ps[i].start) / 0.4);
      tr.l.style.strokeDashoffset = (tr.L * (1 - d)).toFixed(1);
      tr.l.style.opacity = (d > 0 ? (i === activo ? 1 : 0.55) : 0).toFixed(3);
    });
    this.estaciones.forEach((e, i) => {
      const s = ps[i].start, k = eo((t - s - 0.1) / 0.5);
      const visible = t >= s + 0.1;
      e.g.style.display = visible ? '' : 'none';
      e.rot.style.display = visible ? '' : 'none';
      if (!visible) return;
      const act = i === activo;
      // el origen se levanta desde el riel; los sacos caen desde arriba
      const tr = i === 0
        ? `translate(0 ${(e.yb * (1 - k)).toFixed(2)}) scale(1 ${k.toFixed(4)})`
        : `translate(0 ${(-70 * (1 - k)).toFixed(2)})`;
      e.g.setAttribute('transform', tr);
      e.g.style.opacity = (k * (act ? 1 : 0.55)).toFixed(3);
      e.formas.forEach((f) => {
        const linea = f.dataset && (f.dataset.linea || f.dataset.hueco);
        f.setAttribute('stroke', act ? 'var(--acento)' : 'var(--ink)');
        f.setAttribute('fill', linea ? (f.dataset.hueco ? 'var(--bg)' : 'none')
          : (act ? 'var(--acento)' : 'color-mix(in srgb, var(--ink) 18%, transparent)'));
        if (f.dataset && f.dataset.linea) f.setAttribute('stroke', act ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)');
      });
      if (e.tf) e.tf.setAttribute('fill', act ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)');
      const kr = eo((t - s - 0.3) / 0.45);
      e.rot.style.opacity = (kr * (act ? 1 : 0.5)).toFixed(3);
      e.rot.style.transform = `translateY(${((1 - kr) * 14).toFixed(1)}px)`;
    });
  },
});
