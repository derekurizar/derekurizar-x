// Animación «paso-reten» (mecanismo cadena): un bulto llega a un retén (garita con barrera). El primer paso es una
// señal que el bulto lleva (un punto que emite ondas); los pasos del medio son paquetes que cruzan del bulto a la
// garita; el último paso encoge la etiqueta del bulto, la barrera se levanta y el bulto pasa al otro lado.
// Sirve para cualquier «pagar para pasar»: soborno en aduana, peaje, trámite que se salta. Debajo, los pasos en lista
// (el que la voz dice, en acento). Todo es función de t (seek puro). Cámara quieta (2026-11-07): solo se mueve lo que
// entra con su paso; entre pasos todo queda quieto (A1) y nada se ve antes de que la voz lo diga (A2).
ANIM.registrar('paso-reten', {
  meta: {
    descripcion: 'un bulto llega a un retén: lleva una señal, pasa un paquete a la garita, su etiqueta se encoge y la barrera lo deja pasar',
    mecanismo: 'cadena',
    temas: ['aduana', 'soborno', 'corrupción', 'contrabando', 'peaje', 'trámite', 'retén'],
    pasos: [2, 5],
    ejemplo: { titulo: '¿Cómo cobraba la red?', pasos: ['Un número: La Línea', 'El soborno', 'Impuestos rebajados'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length, NS = 'http://www.w3.org/2000/svg';
    this.V = V; this.n = n;
    const sceneH = Math.round(H * 0.58), gy = Math.round(sceneH * 0.88);
    const cw = Math.round(W * 0.32), ch = Math.round(cw * 0.6), cx0 = 24;
    const gateX = Math.round(W * 0.6), bw = 76, boothH = Math.round(ch * 1.75);
    this.g = { W, sceneH, gy, cw, ch, cx0, gateX, bw, boothH, cxF: W - cw - 24 };
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', sceneH);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const el = (tag, at, padre) => {
      const e = document.createElementNS(NS, tag);
      for (const k in at) e.setAttribute(k, at[k]);
      (padre || svg).appendChild(e); return e;
    };
    const tenue = 'color-mix(in srgb, var(--ink) 45%, transparent)';
    // suelo: línea con marcas (fijas)
    el('line', { x1: 0, y1: gy, x2: W, y2: gy, stroke: tenue, 'stroke-width': 5, 'stroke-linecap': 'round' });
    this.marcas = el('line', { x1: 0, y1: gy + 22, x2: W, y2: gy + 22, stroke: tenue, 'stroke-width': 5, 'stroke-dasharray': '18 42' });
    // garita
    const bx = gateX - bw / 2, by = gy - boothH;
    el('rect', { x: bx, y: by, width: bw, height: boothH, rx: 10, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 });
    el('rect', { x: bx + 14, y: by + 22, width: bw - 28, height: 46, rx: 6, fill: 'none', stroke: tenue, 'stroke-width': 5 });
    // barrera (gira sobre su bisagra en el lado izquierdo de la garita)
    const armY = gy - Math.round(ch * 0.5), armL = Math.round(bx - (cx0 + cw) - 30);
    this.brazo = el('g', {});
    el('line', { x1: bx, y1: armY, x2: bx - armL, y2: armY, stroke: 'var(--ink)', 'stroke-width': 12, 'stroke-linecap': 'round' }, this.brazo);
    for (let k = 1; k < 4; k++) {
      const x = bx - armL * k / 4;
      el('line', { x1: x, y1: armY - 6, x2: x - 16, y2: armY + 6, stroke: 'var(--bg)', 'stroke-width': 5 }, this.brazo);
    }
    this.bisagra = { x: bx, y: armY };
    el('circle', { cx: bx, cy: armY, r: 10, fill: 'var(--ink)' });
    // paquetes (uno por paso del medio): de la puerta del bulto al techo de la garita
    this.paquetes = [];
    for (let k = 0; k < Math.max(0, n - 2); k++) {
      const p = el('g', {});
      el('rect', { x: -32, y: -21, width: 64, height: 42, rx: 6, fill: 'none', 'stroke-width': 6 }, p);
      el('path', { d: 'M-30 -18 L0 4 L30 -18', fill: 'none', 'stroke-width': 5, 'stroke-linejoin': 'round' }, p);
      this.paquetes.push({ g: p, piezas: p.childNodes, destY: by - 30 - k * 50 });
    }
    // el bulto (contenedor) con su etiqueta y su señal
    this.bulto = el('g', {});
    el('rect', { x: 0, y: -ch, width: cw, height: ch, rx: 10, fill: 'var(--bg)', stroke: 'var(--ink)', 'stroke-width': 6 }, this.bulto);
    for (let k = 1; k < 6; k++) {
      el('line', { x1: cw * k / 6, y1: -ch + 62, x2: cw * k / 6, y2: -14, stroke: tenue, 'stroke-width': 5 }, this.bulto);
    }
    this.etqW = cw - 40;
    this.etiqueta = el('rect', { x: 20, y: -ch + 16, width: this.etqW, height: 30, rx: 6 }, this.bulto);
    this.senal = el('g', {}, this.bulto);
    this.ondas = [0, 1].map(() => el('circle', { cx: cw / 2, cy: -ch - 72, r: 36, fill: 'none', 'stroke-width': 5 }, this.senal));
    this.punto = el('circle', { cx: cw / 2, cy: -ch - 72, r: 32 }, this.senal);
    lienzo.appendChild(svg);
    // lista de pasos debajo de la escena
    const F = ctx.F45 ? 38 : 42, fila = Math.min(110, (H - sceneH - 16) / n);
    this.filas = P.pasos.map((txt, i) => {
      const d = document.createElement('div');
      d.style.cssText = `position:absolute;left:0;right:0;top:${(sceneH + 16 + i * fila).toFixed(0)}px;height:${fila.toFixed(0)}px;` +
        `display:flex;align-items:center;font:800 ${F}px/1.1 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);`;
      d.innerHTML = `<span style="font:600 36px/1 'JetBrains Mono',monospace;margin-right:24px;opacity:.6">${i + 1}</span>`;
      d.appendChild(document.createTextNode(txt));
      lienzo.appendChild(d);
      return d;
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n, g = this.g;
    const tenue = 'color-mix(in srgb, var(--ink) 45%, transparent)';
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    const ini = eo((t - T.ini) / 0.5);
    // último paso: etiqueta que se encoge, barrera que sube, bulto que pasa
    const sU = ps[n - 1].start;
    const encoge = eo(clamp((t - sU) / 0.6)), sube = eo(clamp((t - sU - 0.5) / 0.5)), pasa = eo(clamp((t - sU - 0.8) / 0.75));   // todo termina en 1.6 s (A1)
    const x = g.cx0 + (g.cxF - g.cx0) * pasa, bob = 0;
    this.bulto.setAttribute('transform', `translate(${x.toFixed(1)} ${(g.gy - 3 + bob).toFixed(1)})`);
    this.bulto.style.opacity = ini.toFixed(3);
    this.brazo.setAttribute('transform', `rotate(${(sube * 78).toFixed(2)} ${this.bisagra.x} ${this.bisagra.y})`);
    this.etiqueta.setAttribute('width', (this.etqW * (1 - 0.72 * encoge)).toFixed(1));
    const etqActiva = activo === n - 1;
    this.etiqueta.setAttribute('fill', etqActiva ? 'var(--acento)' : tenue);
    // señal: entra con el primer paso y emite ondas
    const s0 = ps[0].start, e0 = eo(clamp((t - s0) / 0.45)), a0 = activo === 0;
    this.senal.style.opacity = e0.toFixed(3);
    const col0 = a0 ? 'var(--acento)' : (t >= s0 ? tenue : 'none');
    this.punto.setAttribute('fill', col0);
    this.punto.setAttribute('stroke', 'var(--ink)'); this.punto.setAttribute('stroke-width', t >= s0 ? 0 : 5);
    this.punto.setAttribute('r', '32');
    this.ondas.forEach((o, k) => {
      const u = clamp((t - s0 - k * 0.3) / 1.2);   // la señal emite dos ondas al decirse y se calla
      o.style.display = t >= s0 && u < 1 ? '' : 'none';
      o.setAttribute('r', (36 + 70 * u).toFixed(1));
      o.setAttribute('stroke', a0 ? 'var(--acento)' : tenue);
      o.style.opacity = ((1 - u) * (a0 ? 0.9 : 0.5) * e0).toFixed(3);
    });
    // paquetes del medio: vuelan del bulto al techo de la garita en arco
    this.paquetes.forEach((p, k) => {
      const s = ps[k + 1].start, u = eo(clamp((t - s) / 1.2)), act = activo === k + 1;
      const x0 = g.cx0 + g.cw - 40, y0 = g.gy - g.ch * 0.5, x1 = g.gateX, y1 = p.destY;
      const px = x0 + (x1 - x0) * u, py = y0 + (y1 - y0) * u - Math.sin(Math.PI * u) * 90;
      const resp = 1;
      p.g.setAttribute('transform', `translate(${px.toFixed(1)} ${py.toFixed(1)}) scale(${resp.toFixed(4)})`);
      p.g.style.display = t >= s ? '' : 'none';
      p.g.style.opacity = clamp((t - s) / 0.3).toFixed(3);
      const c = act ? 'var(--acento)' : 'var(--ink)';
      p.piezas[0].setAttribute('stroke', c); p.piezas[1].setAttribute('stroke', c);
    });
    // lista
    this.filas.forEach((d, i) => {
      const e = eo(clamp((t - ps[i].start) / 0.45));
      d.style.opacity = (e * (i < activo ? 0.5 : 1)).toFixed(3);
      d.style.transform = `translateX(${((1 - e) * -30).toFixed(1)}px)`;
      d.style.color = i === activo && e > 0.5 ? 'var(--acento)' : 'var(--ink)';
    });
  },
});
