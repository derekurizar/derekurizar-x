// Animación «cadena» de la escena explica (semilla de la biblioteca y ejemplo del contrato): causa → efecto en 2–6
// pasos apilados. Al entrar la escena se ven los contornos tenues de todas las cajas; cada caja se llena cuando la voz
// dice su paso (T.pasos[i].start) y la flecha que llega a ella se dibuja justo antes; por el asta de cada flecha ya
// dibujada baja una gota que se apaga en la punta, y la caja activa respira. Estilo Noche: la caja activa es lo único en acento (texto en
// --tinta-acento encima), las ya dichas quedan en crema atenuada. Todo es función de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }                         (del guion)
//   ctx = { colores, F45, ancho, alto, V }                   (V: clamp, eo, prog… de video/comun.js)
//   T   = { ini, pasos: [{ texto, start }], fin, dur }       (video.py tiempos)
ANIM.registrar('cadena', {
  meta: {
    descripcion: 'cadena causa → efecto: cajas apiladas que se llenan al decir cada paso, flechas con partículas',
    mecanismo: 'cadena',
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
        `border-radius:26px;display:flex;align-items:center;padding:0 36px;font:800 ${ctx.F45 ? 40 : 46}px/1.1 Archivo,sans-serif;` +
        `letter-spacing:-.01em;color:var(--ink);transform-origin:0 50%;`;
      el.innerHTML = `<span style="font:600 36px/1 'JetBrains Mono',monospace;margin-right:26px;opacity:.6">${i + 1}</span>`;
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
      // una sola gota centrada en el asta (cx = x, un poco más ancha que el trazo de 6 px): baja de la caja de arriba
      // y se apaga al entrar en la punta. Antes eran tres puntos a 36 px de la flecha: una columna que leía como glifo roto
      const gota = document.createElementNS(NS, 'circle');
      gota.setAttribute('r', ctx.F45 ? '6' : '7'); gota.setAttribute('cx', x); gota.setAttribute('fill', 'var(--ink)');
      svg.appendChild(gota);
      return { linea, L, a, b, gota };
    });
    lienzo.appendChild(svg);
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.cajas.forEach((c, i) => {
      const s = ps[i].start, entra = eo((t - s) / 0.45);
      const respira = i === activo ? 1 + 0.015 * Math.sin(2 * Math.PI * (t - s) / 1.6) : 1;
      // lo que falta, tenue; lo ya dicho, al 50 % (crema atenuada); la activa, llena en acento
      const fantasma = 0.28 * eo((t - T.ini) / 0.5);
      c.el.style.opacity = Math.max(fantasma, entra * (i < activo ? 0.5 : 1)).toFixed(3);
      c.el.style.transform = `translateX(${((1 - entra) * -36).toFixed(1)}px) scale(${((0.97 + 0.03 * entra) * respira).toFixed(4)})`;
      const lleno = i === activo && entra > 0.5;
      c.el.style.background = lleno ? 'var(--acento)' : 'transparent';
      c.el.style.borderColor = lleno ? 'var(--acento)' : 'var(--ink)';
      c.el.style.color = lleno ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)';
    });
    this.flechas.forEach((f, k) => {
      const s = ps[k + 1].start, d = clamp((t - (s - 0.4)) / 0.35);
      f.linea.style.strokeDashoffset = (f.L * (1 - d)).toFixed(1);
      f.linea.style.opacity = Math.max(0.28 * eo((t - T.ini) / 0.5), d).toFixed(3);
      // la gota baja por el asta de la flecha ya dibujada (de a al arranque de la punta, b − 14) en ciclos de 1.25 s y
      // nace y se apaga con sin(πu): sin saltos al volver arriba. Antes de la flecha no existe (display:none: una gota
      // invisible que se mueve igual invalida su rectángulo y deja ruido de rasterizado)
      const u = ((((t - s) * 0.8) % 1) + 1) % 1;
      f.gota.style.display = d >= 1 ? '' : 'none';
      if (d < 1) return;
      f.gota.setAttribute('cy', (f.a + (f.b - 14 - f.a) * u).toFixed(1));
      f.gota.style.opacity = (Math.sin(Math.PI * u) * 0.9).toFixed(3);
    });
  },
});
