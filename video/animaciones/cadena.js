// Animación «cadena» de la escena explica (semilla de la biblioteca y ejemplo del contrato): causa → efecto en 2–6
// pasos apilados. Al entrar la escena se ven los contornos tenues de todas las cajas; cada caja se llena cuando la voz
// dice su paso (T.pasos[i].start) y la flecha que llega a ella se dibuja justo antes; por las flechas ya dibujadas
// bajan partículas y la caja activa respira. Todo es función de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }                         (del guion)
//   ctx = { colores, F45, ancho, alto, V }                   (V: clamp, eo, prog… de video/comun.js)
//   T   = { ini, pasos: [{ texto, start }], fin, dur }       (video.py tiempos)
ANIM.registrar('cadena', {
  meta: {
    descripcion: 'cadena causa → efecto: cajas apiladas que se llenan al decir cada paso, flechas con partículas',
    temas: ['causas', 'consecuencias', 'proceso'],
    pasos: [2, 6],
    ejemplo: { titulo: '¿Por qué la sequía da hambre?', pasos: ['Llueve menos', 'La milpa se seca', 'Se pierde la cosecha', 'Hay menos comida en casa'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, gap = ctx.F45 ? 54 : 74;
    const alto = Math.min(ctx.F45 ? 128 : 150, (ctx.alto - (n - 1) * gap) / n);
    const y0 = Math.max(0, (ctx.alto - (n * alto + (n - 1) * gap)) / 2);
    this.V = V;
    this.cajas = P.pasos.map((txt, i) => {
      const el = document.createElement('div');
      const y = y0 + i * (alto + gap);
      el.style.cssText = `position:absolute;left:0;right:0;top:${y}px;height:${alto}px;box-sizing:border-box;border:5px solid var(--ink);` +
        `border-radius:26px;display:flex;align-items:center;padding:0 36px;font:700 ${ctx.F45 ? 40 : 46}px/1.1 Archivo,sans-serif;` +
        `color:var(--ink);transform-origin:0 50%;`;
      el.innerHTML = `<span style="font:500 ${ctx.F45 ? 26 : 30}px/1 'JetBrains Mono',monospace;margin-right:26px;opacity:.6">${i + 1}</span>`;
      el.appendChild(document.createTextNode(txt));
      lienzo.appendChild(el);
      return { el, y, alto };
    });
    // flechas y partículas en un SVG encima de las cajas
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', ctx.ancho); svg.setAttribute('height', ctx.alto);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    const x = ctx.ancho / 2;
    this.flechas = this.cajas.slice(1).map((c, k) => {
      const a = this.cajas[k].y + this.cajas[k].alto + 6, b = c.y - 10;
      const linea = document.createElementNS(NS, 'path');
      linea.setAttribute('d', `M${x} ${a} L${x} ${b - 14} M${x - 16} ${b - 26} L${x} ${b - 8} L${x + 16} ${b - 26}`);
      linea.setAttribute('fill', 'none'); linea.setAttribute('stroke', 'var(--ink)'); linea.setAttribute('stroke-width', '6');
      linea.setAttribute('stroke-linecap', 'round'); linea.setAttribute('stroke-linejoin', 'round');
      svg.appendChild(linea);
      const L = linea.getTotalLength();
      linea.style.strokeDasharray = L;
      const puntos = [0, 1, 2].map(() => {
        const p = document.createElementNS(NS, 'circle');
        p.setAttribute('r', '9'); p.setAttribute('cx', x + 36); p.setAttribute('fill', 'var(--ink)');
        svg.appendChild(p);
        return p;
      });
      return { linea, L, a, b, puntos };
    });
    lienzo.appendChild(svg);
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.cajas.forEach((c, i) => {
      const s = ps[i].start, entra = eo((t - s) / 0.45), fantasma = 0.18 * eo((t - T.ini) / 0.5);
      const respira = i === activo ? 1 + 0.015 * Math.sin(2 * Math.PI * (t - s) / 1.6) : 1;
      c.el.style.opacity = Math.max(fantasma, entra * (i < activo ? 0.75 : 1)).toFixed(3);
      c.el.style.transform = `translateX(${((1 - entra) * -36).toFixed(1)}px) scale(${((0.97 + 0.03 * entra) * respira).toFixed(4)})`;
      const lleno = i === activo && entra > 0.5;
      c.el.style.background = lleno ? 'var(--ink)' : 'transparent';
      c.el.style.color = lleno ? 'var(--bg)' : 'var(--ink)';
    });
    this.flechas.forEach((f, k) => {
      const s = ps[k + 1].start, d = clamp((t - (s - 0.4)) / 0.35);
      f.linea.style.strokeDashoffset = (f.L * (1 - d)).toFixed(1);
      f.linea.style.opacity = Math.max(0.18 * eo((t - T.ini) / 0.5), d).toFixed(3);
      // partículas: bajan por la flecha ya dibujada, cada una desfasada un tercio
      f.puntos.forEach((p, q) => {
        const u = ((((t - s) * 0.8 + q / 3) % 1) + 1) % 1;
        p.setAttribute('cy', (f.a + (f.b - f.a) * u).toFixed(1));
        p.style.opacity = d >= 1 ? (Math.sin(Math.PI * u) * 0.9).toFixed(3) : 0;
      });
    });
  },
});
