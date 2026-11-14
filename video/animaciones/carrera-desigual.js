// Animación «carrera-desigual» de la escena explica (mecanismo proporcion): dos columnas parten del mismo nivel (lo que
// había al empezar, P.rotulos.base: «Hace 20 años») y crecen cada una a su ritmo cuando la voz dice su paso. La altura
// final sale del porcentaje que traiga el paso (crecimiento compuesto durante los años del rótulo base; sin %, un
// crecimiento genérico), así que la rápida se dispara y la lenta apenas se mueve. Al entrar la segunda, una llave marca
// la brecha entre las dos: lo de arriba sobre lo de abajo se agranda. Pasos 3+ (si los hay) se ignoran en el dibujo
// salvo como texto de la segunda columna: la animación es de DOS ritmos (pasos [2, 2]).
// Cámara quieta: se mueve solo lo que entra con la voz (≤ 1.4 s) y luego todo queda quieto (A1); nada antes de su
// paso (A2). Estilo Noche: la columna del paso que suena es lo único en acento; la otra, en crema.
ANIM.registrar('carrera-desigual', {
  meta: {
    descripcion: 'dos columnas que parten iguales y crecen a ritmos distintos: una se dispara, la otra apenas sube y la brecha se abre',
    mecanismo: 'proporcion',
    temas: ['crecimiento', 'brecha', 'ritmo', 'tráfico', 'vehículos', 'calles', 'población', 'oferta', 'demanda', 'carrera'],
    pasos: [2, 2],
    ejemplo: { titulo: 'Carros contra calle', pasos: ['Vehículos: 9.6 % al año', 'Red vial: 1.4 % al año'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, F45 = ctx.F45, fs = F45 ? 36 : 40;
    const R = P.rotulos || {};
    const baseTxt = R.base || 'Al inicio';
    const anios = (() => { const m = String(R.base || '').match(/(\d+)/); const a = m ? +m[1] : 10; return a > 0 && a <= 60 ? a : 10; })();
    const factor = (txt, def) => {
      const m = String(txt || '').match(/(\d+(?:[.,]\d+)?)\s*%/);
      if (!m) return def;
      const r = parseFloat(m[1].replace(',', '.')) / 100;
      return Math.pow(1 + r, anios);
    };
    const f = [factor(P.pasos[0], 4), factor(P.pasos[1], 1.3)].map((x) => Math.max(1.06, Math.min(12, x)));
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); svg.appendChild(e); return e; };
    // geometría: suelo arriba de los textos de los pasos; techo con sitio para la llave
    const piso = H - (F45 ? 136 : 160), techo = 20, alto = piso - techo;
    const fmax = Math.max(f[0], f[1]);
    const h0 = Math.max(F45 ? 60 : 70, alto / fmax);
    const escala = (alto - h0) / Math.max(0.0001, fmax - 1);
    const hDe = (k) => h0 + (k - 1) * escala;
    const bw = Math.min(200, W * 0.24);
    const cxs = [W * 0.40, W * 0.80];
    Object.assign(this, { V, piso, h0, hDe, f, bw, cxs });
    // suelo
    mk('line', { x1: 0, x2: W, y1: piso + 3, y2: piso + 3, stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round' });
    // base (lo que ya había): bloque tenue en cada columna + línea punteada con su nombre
    this.bases = cxs.map((cx) => mk('rect', { x: cx - bw / 2, width: bw, rx: 10, fill: 'color-mix(in srgb, var(--ink) 38%, transparent)' }));
    const yb = piso - h0;
    this.lbase = mk('line', { x1: 0, x2: W, y1: yb, y2: yb, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-dasharray': '18 12', opacity: 0.6 });
    // crecimiento de cada columna
    this.crece = cxs.map((cx) => mk('rect', { x: cx - bw / 2, width: bw, rx: 10, fill: 'var(--ink)' }));
    // llave de la brecha (entra con el segundo paso)
    this.guia = mk('line', { x1: cxs[0] + bw / 2 + 8, x2: cxs[1] + bw / 2, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-dasharray': '14 10', 'stroke-linecap': 'round' });
    this.llave = mk('path', { fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
    lienzo.appendChild(svg);
    const div = (css, txt) => { const el = document.createElement('div'); el.style.cssText = 'position:absolute;' + css; el.textContent = txt; lienzo.appendChild(el); return el; };
    this.baseEl = div(`left:0;width:${(cxs[0] - bw / 2 - 14).toFixed(0)}px;bottom:${(H - yb + 10).toFixed(0)}px;` +
      `font:600 ${F45 ? 26 : 28}px/1.1 'JetBrains Mono',monospace;letter-spacing:.04em;text-transform:uppercase;color:var(--ink);opacity:0`, baseTxt);
    this.brechaEl = div(`left:${(cxs[0] + bw / 2 + 18).toFixed(0)}px;width:${(cxs[1] - bw / 2 - cxs[0] - bw / 2 - 26).toFixed(0)}px;` +
      `font:600 ${F45 ? 26 : 28}px/1.1 'JetBrains Mono',monospace;letter-spacing:.04em;text-transform:uppercase;color:var(--ink);text-align:center;opacity:0`, 'Brecha');
    // textos de los pasos, centrados bajo su columna
    const tw = Math.min(W * 0.39, 310);
    this.items = [P.pasos[0], P.pasos.slice(1).join(' · ')].map((txt, i) => {
      const left = Math.max(0, Math.min(W - tw, cxs[i] - tw / 2));
      return div(`left:${left.toFixed(0)}px;width:${tw.toFixed(0)}px;top:${(piso + 18).toFixed(0)}px;text-align:center;` +
        `font:800 ${fs}px/1.08 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);opacity:0`, txt);
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, piso = this.piso, h0 = this.h0;
    const abre = eo(clamp((t - T.ini) / 0.5));
    const yb = piso - h0 * abre;
    this.bases.forEach((r) => { r.setAttribute('y', yb.toFixed(1)); r.setAttribute('height', (h0 * abre).toFixed(1)); });
    this.lbase.style.opacity = (0.6 * abre).toFixed(3);
    this.baseEl.style.opacity = (0.75 * abre).toFixed(3);
    let activo = -1;
    [0, 1].forEach((i) => { if (ps[i] && t >= ps[i].start) activo = i; });
    const tops = [];
    [0, 1].forEach((i) => {
      const s = ps[i] ? Math.max(ps[i].start, T.ini + 0.5) : 1e9;
      const u = eo(clamp((t - s) / 1.2));
      const h = (this.hDe(this.f[i]) - h0) * u;
      const r = this.crece[i];
      const y = piso - h0 - h;
      r.setAttribute('y', y.toFixed(1)); r.setAttribute('height', Math.max(0, h + 10).toFixed(1));
      r.style.display = u > 0 ? '' : 'none';
      r.setAttribute('fill', i === activo ? 'var(--acento)' : 'var(--ink)');
      r.style.opacity = i === activo ? '1' : '0.7';
      tops.push(y);
      const tx = eo(clamp((t - s) / 0.45));
      const el = this.items[i];
      el.style.opacity = (tx * (i === activo ? 1 : 0.6)).toFixed(3);
      el.style.transform = `translateY(${((1 - tx) * 18).toFixed(1)}px)`;
    });
    // la brecha: entra tras la segunda columna
    const s2 = ps[1] ? Math.max(ps[1].start, T.ini + 0.5) : 1e9;
    const b = eo(clamp((t - s2 - 0.7) / 0.6));
    const ya = tops[0], yz = tops[1];
    this.guia.setAttribute('y1', ya.toFixed(1)); this.guia.setAttribute('y2', ya.toFixed(1));
    this.guia.style.opacity = (0.6 * b).toFixed(3);
    const x = this.cxs[1], p = 14;
    if (yz - ya > 40) {
      this.llave.setAttribute('d', `M${x} ${ya + 6} L${x} ${yz - 10} M${x - p} ${ya + 6 + p} L${x} ${ya + 6} L${x + p} ${ya + 6 + p} M${x - p} ${yz - 10 - p} L${x} ${yz - 10} L${x + p} ${yz - 10 - p}`);
    } else this.llave.setAttribute('d', '');
    this.llave.style.opacity = b.toFixed(3);
    this.brechaEl.style.top = ((ya + yz) / 2 - 16).toFixed(1) + 'px';
    this.brechaEl.style.opacity = b.toFixed(3);
  },
});
