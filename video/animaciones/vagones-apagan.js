// Animación «vagones-apagan» (mecanismo cronologia, sembrada con /historia): el final de un servicio contado por
// fechas. Arriba, una línea de tiempo corta: cada paso «fecha · qué pasó» entra cuando la voz lo dice. Abajo, un tren
// (locomotora y vagones con sus ventanas encendidas, rotulado con P.rotulos.base, «El tren» por defecto) sobre su riel:
// con cada fecha se apaga un tramo del tren, de la cola hacia la locomotora; con el último paso queda todo apagado.
// Antes de la voz solo se ve el tren encendido (lo que ya había), nunca el texto de un paso (A2); entre pasos todo
// queda quieto (A1). Estilo Noche: lo único en acento es la fecha del paso que la voz dice. seek puro, sin azar ni reloj.
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
ANIM.registrar('vagones-apagan', {
  meta: {
    descripcion: 'final por fechas: cada evento entra en la línea de tiempo y apaga un tramo del tren, de la cola a la locomotora',
    mecanismo: 'cronologia',
    temas: ['historia', 'tren', 'ferrocarril', 'cierre', 'cronología', 'servicio que se apaga', 'transporte'],
    pasos: [2, 5],
    ejemplo: { titulo: 'El último tren', pasos: ['Marzo 1996 · Cierra la línea', '1996 · Sin pasajeros'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, W = ctx.ancho, H = ctx.alto;
    this.V = V;
    const NS = 'http://www.w3.org/2000/svg';
    const mx = ctx.F45 ? 90 : 60;
    // tren abajo
    const unidades = 5, gap = 16, uw = Math.min(140, (W - 2 * mx - gap * (unidades - 1)) / unidades), uh = uw * 0.72;
    const anchoTren = unidades * uw + (unidades - 1) * gap, x0 = (W - anchoTren) / 2;
    const yRiel = H - (ctx.F45 ? 110 : 130), yTop = yRiel - 18 - uh;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const el = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); svg.appendChild(e); return e; };
    el('line', { x1: x0 - 20, x2: x0 + anchoTren + 20, y1: yRiel, y2: yRiel, stroke: 'color-mix(in srgb, var(--ink) 45%, transparent)', 'stroke-width': 6, 'stroke-linecap': 'round' });
    this.unidades = [];
    for (let u = 0; u < unidades; u++) {
      const x = x0 + u * (uw + gap), loco = u === 0;
      const cuerpo = el('rect', { x, y: yTop, width: uw, height: uh, rx: loco ? 22 : 10, 'stroke-width': 6, fill: 'var(--bg)' });
      const vent = [];
      if (loco) {
        vent.push(el('rect', { x: x + uw * 0.18, y: yTop + uh * 0.18, width: uw * 0.4, height: uh * 0.36, rx: 6 }));
      } else {
        for (let w = 0; w < 2; w++) vent.push(el('rect', { x: x + uw * (0.14 + w * 0.39), y: yTop + uh * 0.2, width: uw * 0.33, height: uh * 0.34, rx: 5 }));
      }
      const ruedas = [0.27, 0.73].map((f) => el('circle', { cx: x + uw * f, cy: yRiel - 9, r: 11, 'stroke-width': 5, fill: 'var(--bg)' }));
      if (u > 0) el('line', { x1: x - gap, x2: x, y1: yTop + uh * 0.75, y2: yTop + uh * 0.75, stroke: 'color-mix(in srgb, var(--ink) 45%, transparent)', 'stroke-width': 5 });
      this.unidades.push({ cuerpo, vent, ruedas });
    }
    lienzo.appendChild(svg);
    const rot = document.createElement('div');
    rot.style.cssText = `position:absolute;left:0;right:0;top:${yRiel + 22}px;text-align:center;` +
      "font:600 34px/1 'JetBrains Mono',monospace;letter-spacing:.06em;text-transform:uppercase;" +
      'color:color-mix(in srgb, var(--ink) 70%, transparent)';
    rot.textContent = (P.rotulos && P.rotulos.base) || 'El tren';
    lienzo.appendChild(rot);
    // cuántas unidades quedan apagadas tras cada paso (de la cola a la locomotora)
    this.apagadas = P.pasos.map((_, i) => Math.round(unidades * (i + 1) / n));
    this.nU = unidades;
    // línea de tiempo arriba
    const zona = yTop - 70, fila = Math.min(190, zona / n), k = Math.min(1, fila / 170);
    const fsF = Math.round((ctx.F45 ? 80 : 88) * k), fs = Math.round((ctx.F45 ? 46 : 50) * k);
    const xr = mx + 10, y0 = 30;
    this.filas = P.pasos.map((txt, i) => {
      const m = String(txt).match(/^\s*([^·:]{1,16}?)\s*[·:]\s*(.+)$/);
      const d = document.createElement('div');
      d.style.cssText = `position:absolute;left:${xr + 56}px;right:${mx}px;top:${y0 + i * fila}px`;
      const f = document.createElement('div');
      f.style.cssText = `font:900 ${fsF}px/1 Archivo,sans-serif;font-stretch:62.5%;text-transform:uppercase;letter-spacing:-.01em;color:var(--ink)`;
      f.textContent = m ? m[1] : '';
      const tx = document.createElement('div');
      tx.style.cssText = `font:800 ${fs}px/1.1 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);margin-top:6px`;
      tx.textContent = m ? m[2] : txt;
      d.appendChild(f); d.appendChild(tx);
      lienzo.appendChild(d);
      const pt = document.createElement('div');
      pt.style.cssText = `position:absolute;left:${xr - 16}px;top:${y0 + i * fila + fsF / 2 - 16}px;width:32px;height:32px;border-radius:50%;box-sizing:border-box;border:5px solid var(--ink)`;
      lienzo.appendChild(pt);
      d._f = f; d._pt = pt;
      return d;
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.filas.forEach((d, i) => {
      const e = eo(clamp((t - ps[i].start) / 0.45));
      const op = e * (i < activo ? 0.5 : 1);
      d.style.opacity = op.toFixed(3);
      d.style.transform = `translateY(${((1 - e) * 24).toFixed(1)}px)`;
      d._f.style.color = i === activo ? 'var(--acento)' : 'var(--ink)';
      d._pt.style.opacity = op.toFixed(3);
      d._pt.style.background = i === activo ? 'var(--acento)' : 'var(--ink)';
      d._pt.style.borderColor = i === activo ? 'var(--acento)' : 'var(--ink)';
    });
    // luz de cada unidad: 1 encendida, 0 apagada; se apaga en cascada de la cola a la locomotora al entrar su paso
    for (let u = 0; u < this.nU; u++) {
      const desdeCola = this.nU - 1 - u;
      let luz = 1;
      for (let i = 0; i < ps.length; i++) {
        const antes = i > 0 ? this.apagadas[i - 1] : 0;
        if (desdeCola >= antes && desdeCola < this.apagadas[i]) {
          const orden = desdeCola - antes;
          luz = 1 - eo(clamp((t - ps[i].start - 0.3 - orden * 0.25) / 0.5));
        }
      }
      const U = this.unidades[u];
      const borde = `color-mix(in srgb, var(--ink) ${Math.round(28 + 72 * luz)}%, transparent)`;
      U.cuerpo.setAttribute('stroke', borde);
      U.vent.forEach((v) => {
        v.setAttribute('fill', `color-mix(in srgb, var(--ink) ${Math.round(8 + 87 * luz)}%, transparent)`);
      });
      U.ruedas.forEach((r) => r.setAttribute('stroke', borde));
    }
  },
});
