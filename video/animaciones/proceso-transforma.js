// Animación «proceso-transforma» de la escena explica (mecanismo cadena): un material pasa por 2–6 etapas y cambia de
// forma en cada una. Las etapas son estaciones redondas en un riel vertical; en la primera el material es una gota que
// ondula (líquido) y en cada etapa siguiente se parte en más trozos y más finos (escamas, granos, polvo). Cuando la voz
// dice un paso, su estación se dibuja, el material aparece dentro y es lo único en acento; por el conducto que llega a
// ella bajan granos que se achican en el camino (lo de arriba se vuelve lo de abajo). Lo ya dicho queda en crema
// atenuada; lo que falta, solo el contorno tenue. Todo es función de t (seek puro, sin azar ni reloj).
ANIM.registrar('proceso-transforma', {
  meta: {
    descripcion: 'proceso por etapas: un material baja por estaciones y cambia de forma en cada una, de una gota líquida a escamas y a polvo fino',
    mecanismo: 'cadena',
    temas: ['proceso', 'fabricación', 'transformación', 'industria', 'invento', 'producto'],
    pasos: [2, 6],
    ejemplo: { titulo: '¿Cómo se vuelve polvo?', pasos: ['Esencia de café', 'Cilindros calientes', 'Secado al vacío', 'Escamas molidas'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, F = ctx.F45;
    const gap = F ? 56 : 72;
    const D = Math.min(F ? 150 : 172, (ctx.alto - (n - 1) * gap) / n);
    const y0 = Math.max(0, (ctx.alto - (n * D + (n - 1) * gap)) / 2);
    const cx = D / 2 + 14, R = D / 2 - 6;
    const NS = 'http://www.w3.org/2000/svg';
    this.V = V; this.R = R;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', ctx.ancho); svg.setAttribute('height', ctx.alto);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    lienzo.appendChild(svg);
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); return e; };

    this.est = P.pasos.map((txt, i) => {
      const cy = y0 + i * (D + gap) + D / 2;
      const s = n > 1 ? i / (n - 1) : 1;          // 0 = líquido … 1 = polvo
      const g = mk('g', {});
      const aro = mk('circle', { cx, cy, r: R, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6 });
      g.appendChild(aro);
      const L = 2 * Math.PI * R;
      aro.style.strokeDasharray = L.toFixed(1);
      const mat = mk('g', {});
      g.appendChild(mat);
      let gota = null, granos = [];
      if (s === 0) {
        gota = mk('path', { fill: 'var(--ink)' });
        mat.appendChild(gota);
      } else {
        const m = Math.round(3 + 42 * s * s), Ri = R * 0.72;
        const pr = Math.max(5, (Ri / Math.sqrt(m)) * 0.78);
        for (let j = 0; j < m; j++) {
          const rad = Ri * Math.sqrt((j + 0.5) / m), ang = j * 2.39996;
          const rx = pr * (1 + 0.7 * (1 - s)), ry = pr * (1 - 0.35 * (1 - s));
          const e = mk('ellipse', { rx: rx.toFixed(1), ry: ry.toFixed(1), fill: 'var(--ink)' });
          mat.appendChild(e);
          granos.push({ e, x: cx + rad * Math.cos(ang), y: cy + rad * Math.sin(ang), rot: (j * 47) % 180, f: (j * 37) % 11 });
        }
      }
      svg.appendChild(g);
      // rótulo del paso a la derecha de la estación
      const el = document.createElement('div');
      const left = D + 54;
      el.style.cssText = `position:absolute;left:${left}px;width:${ctx.ancho - left}px;top:${cy}px;transform:translateY(-50%);` +
        `font:800 ${F ? 40 : 46}px/1.1 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);`;
      el.textContent = txt;
      lienzo.appendChild(el);
      return { g, aro, L, mat, gota, granos, el, cx, cy, s };
    });

    // conductos entre estaciones, con su punta y granos que bajan achicándose
    this.tubos = this.est.slice(1).map((b, k) => {
      const a = this.est[k];
      const ya = a.cy + R + 10, yb = b.cy - R - 12;
      const linea = mk('path', { d: `M${cx} ${ya} L${cx} ${yb - 4} M${cx - 14} ${yb - 18} L${cx} ${yb - 2} L${cx + 14} ${yb - 18}`,
        fill: 'none', stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
      svg.appendChild(linea);
      const L = linea.getTotalLength();
      linea.style.strokeDasharray = L.toFixed(1);
      const gr = [0, 1].map(() => { const c = mk('circle', { cx: cx + 22, fill: 'var(--ink)' }); svg.appendChild(c); return c; });
      return { linea, L, ya, yb, gr, sa: a.s, sb: b.s };
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, R = this.R;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    const fantasma = 0.28 * eo((t - T.ini) / 0.5);
    this.est.forEach((e, i) => {
      const s0 = ps[i].start, entra = eo((t - s0) / 0.5);
      const act = i === activo, dicho = t >= s0;
      const col = act && entra > 0.4 ? 'var(--acento)' : 'var(--ink)';
      // el aro: contorno tenue antes; se dibuja al decirlo
      e.aro.style.strokeDashoffset = (e.L * (1 - (dicho ? entra : 1))).toFixed(1);
      e.aro.style.opacity = dicho ? (i < activo ? 0.5 : 1).toFixed(3) : fantasma.toFixed(3);
      if (!dicho) e.aro.style.strokeDashoffset = '0';
      e.aro.setAttribute('stroke', col);
      const respira = act ? 1 + 0.02 * Math.sin(2 * Math.PI * (t - s0) / 1.7) : 1;
      e.g.setAttribute('transform', `translate(${e.cx} ${e.cy}) scale(${respira.toFixed(4)}) translate(${-e.cx} ${-e.cy})`);
      // el material: aparece al decirlo, en acento si es el activo
      const k = dicho ? 0.2 + 0.8 * entra : 0;
      e.mat.style.display = dicho ? '' : 'none';
      e.mat.style.opacity = (i < activo ? 0.5 : 1).toFixed(3);
      e.mat.setAttribute('transform', `translate(${e.cx} ${e.cy}) scale(${k.toFixed(4)}) translate(${-e.cx} ${-e.cy})`);
      if (dicho) {
        if (e.gota) {
          // gota que ondula: radio modulado por dos senos lentos
          const R0 = R * 0.62, pts = [];
          for (let a = 0; a < 48; a++) {
            const th = (a / 48) * 2 * Math.PI;
            const r = R0 * (1 + 0.07 * Math.sin(3 * th + 1.8 * t) + 0.04 * Math.sin(5 * th - 1.3 * t));
            pts.push(`${(e.cx + r * Math.cos(th)).toFixed(1)} ${(e.cy + r * Math.sin(th)).toFixed(1)}`);
          }
          e.gota.setAttribute('d', 'M' + pts.join(' L') + ' Z');
          e.gota.setAttribute('fill', col);
        }
        e.granos.forEach((q, j) => {
          const dx = 3 * Math.sin(1.3 * t + q.f), dy = 3 * Math.cos(1.1 * t + j * 0.7);
          const rot = q.rot + 12 * Math.sin(0.9 * t + q.f);
          q.e.setAttribute('transform', `translate(${(q.x + dx).toFixed(1)} ${(q.y + dy).toFixed(1)}) rotate(${rot.toFixed(1)})`);
          q.e.setAttribute('fill', col);
        });
      }
      e.el.style.opacity = (dicho ? entra * (i < activo ? 0.5 : 1) : 0).toFixed(3);
      e.el.style.transform = `translateY(-50%) translateX(${((1 - entra) * 30).toFixed(1)}px)`;
    });
    this.tubos.forEach((f, k) => {
      const s = ps[k + 1].start, d = clamp((t - (s - 0.4)) / 0.35);
      f.linea.style.strokeDashoffset = (f.L * (1 - d)).toFixed(1);
      f.linea.style.opacity = Math.max(fantasma, d * 0.8).toFixed(3);
      f.gr.forEach((c, j) => {
        c.style.display = d >= 1 ? '' : 'none';
        if (d < 1) return;
        const u = ((((t - s) * 0.7 + j * 0.5) % 1) + 1) % 1;
        const sm = f.sa + (f.sb - f.sa) * u;
        c.setAttribute('cy', (f.ya + (f.yb - 20 - f.ya) * u).toFixed(1));
        c.setAttribute('r', (11 - 5 * sm).toFixed(1));
        c.style.opacity = (Math.sin(Math.PI * u) * 0.85).toFixed(3);
      });
    });
  },
});
