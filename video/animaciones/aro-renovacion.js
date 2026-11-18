// Animación «aro-renovacion» (mecanismo ciclo): un aro de 3–5 estaciones. Cuando la voz dice el paso i, el tramo del
// aro que llega a su estación se dibuja (con su punta de flecha) y la estación se enciende con su texto dentro del aro.
// Con el último paso, el tramo que cierra vuelve a la primera estación, aparece la marca del límite
// (P.rotulos.limite, p. ej. «Vence al año») en el punto de cierre y la primera estación se vuelve a encender: el aro
// empieza otra vez. Estilo Noche: lo único en acento es la estación que la voz dice; lo ya dicho queda en crema
// atenuada. seek puro (todo es función de t); quieto entre pasos (A1) y nada antes de la voz (A2).
ANIM.registrar('aro-renovacion', {
  meta: {
    descripcion: 'aro que se cierra: cada paso dibuja su tramo del círculo hasta su estación; el último vuelve al primero y el ciclo reinicia',
    mecanismo: 'ciclo',
    temas: ['renovacion', 'licencia', 'concesion', 'permiso', 'tramite anual', 'ciclo', 'repetir'],
    pasos: [3, 5],
    ejemplo: {
      titulo: 'Una licencia que vence',
      pasos: ['Propiedad del Estado', 'La concesión', 'Renovarla cada año', 'Volver a pedirla'],
    },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, NS = 'http://www.w3.org/2000/svg';
    this.V = V;
    const W = ctx.ancho, H = ctx.alto, cx = W / 2, cy = H / 2 + 20;
    const R = Math.min(W / 2 - 70, H / 2 - 120);
    const rn = 26;
    const ang = (i) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
    const pt = (a, r) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); Object.entries(at).forEach(([k, v]) => e.setAttribute(k, v)); return e; };

    const svg = mk('svg', { width: W, height: H });
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    lienzo.appendChild(svg);

    // pista tenue del aro (aparece con el primer paso)
    this.pista = mk('circle', { cx, cy, r: R, fill: 'none', stroke: 'color-mix(in srgb, var(--ink) 26%, transparent)', 'stroke-width': 6 });
    svg.appendChild(this.pista);

    // tramos: el tramo k va de la estación k-1 a la k (k = 1..n-1); el tramo n cierra de la última a la primera
    const d = (rn + 10) / R;
    this.tramos = [];
    for (let k = 1; k <= n; k++) {
      const a1 = ang(k - 1) + d, a2 = ang(k) - d - 0.02;
      const [x1, y1] = pt(a1, R), [x2, y2] = pt(a2, R);
      const arco = mk('path', { d: `M${x1.toFixed(1)} ${y1.toFixed(1)} A${R} ${R} 0 0 1 ${x2.toFixed(1)} ${y2.toFixed(1)}`,
        fill: 'none', stroke: 'var(--ink)', 'stroke-width': 8, 'stroke-linecap': 'round' });
      svg.appendChild(arco);
      const L = R * (a2 - a1);
      arco.style.strokeDasharray = `${L.toFixed(1)} ${(L + 10).toFixed(1)}`;
      // punta de flecha tangente (sentido horario) en el extremo
      const tx = -Math.sin(a2), ty = Math.cos(a2), nx = Math.cos(a2), ny = Math.sin(a2);
      const tip = [x2 + tx * 6, y2 + ty * 6];
      const b = [x2 - tx * 18, y2 - ty * 18];
      const punta = mk('polygon', { points: `${tip[0].toFixed(1)},${tip[1].toFixed(1)} ${(b[0] + nx * 14).toFixed(1)},${(b[1] + ny * 14).toFixed(1)} ${(b[0] - nx * 14).toFixed(1)},${(b[1] - ny * 14).toFixed(1)}`, fill: 'var(--ink)' });
      svg.appendChild(punta);
      this.tramos.push({ arco, punta, L });
    }

    // estaciones (nodo con número) y su texto dentro del aro
    this.estaciones = P.pasos.map((txt, i) => {
      const a = ang(i), [x, y] = pt(a, R);
      const nodo = mk('circle', { cx: x, cy: y, r: rn, fill: 'var(--bg)', stroke: 'var(--ink)', 'stroke-width': 6 });
      svg.appendChild(nodo);
      const num = mk('text', { x, y: y + 11, 'text-anchor': 'middle', fill: 'var(--ink)' });
      num.style.font = "600 30px 'JetBrains Mono', monospace";
      num.textContent = String(i + 1);
      svg.appendChild(num);
      const ux = Math.cos(a), uy = Math.sin(a);
      const [lx, ly] = pt(a, R - rn - 22);
      const el = document.createElement('div');
      const w = n >= 5 ? 250 : 280;
      el.style.cssText = `position:absolute;left:${lx.toFixed(1)}px;top:${ly.toFixed(1)}px;width:${w}px;` +
        `transform:translate(${(-50 - 50 * ux).toFixed(1)}%, ${(-50 - 50 * uy).toFixed(1)}%);` +
        `font:800 ${n >= 5 ? 42 : 48}px/1.08 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);` +
        `text-align:${Math.abs(ux) < 0.3 ? 'center' : ux > 0 ? 'right' : 'left'};`;
      el.textContent = txt;
      lienzo.appendChild(el);
      return { nodo, num, el };
    });

    // marca del límite en el punto de cierre (arriba de la primera estación)
    this.limite = null;
    const lim = P.rotulos && P.rotulos.limite;
    if (lim) {
      const [x0, y0] = pt(ang(0), R);
      const marca = mk('line', { x1: x0, y1: y0 - rn - 8, x2: x0, y2: y0 - rn - 40, stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round' });
      svg.appendChild(marca);
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:${x0}px;top:${(y0 - rn - 50).toFixed(1)}px;transform:translate(-50%,-100%);` +
        "white-space:nowrap;font:600 32px/1 'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.04em;color:var(--ink);";
      el.textContent = lim;
      lienzo.appendChild(el);
      this.limite = { marca, el };
    }
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = ps.length;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    const s0 = ps[0].start, sN = ps[n - 1].start;
    this.pista.style.opacity = eo(clamp((t - s0) / 0.5)).toFixed(3);

    // tramos: el k-ésimo (llega a la estación k) se dibuja al decir el paso k; el de cierre, después del último
    this.tramos.forEach((tr, j) => {
      const k = j + 1;
      const ini = k < n ? ps[k].start : sN + 0.7;
      const u = eo(clamp((t - ini) / 0.7));
      tr.arco.style.strokeDashoffset = (tr.L * (1 - u)).toFixed(1);
      tr.arco.style.opacity = u > 0 ? '1' : '0';
      tr.punta.style.opacity = clamp((t - ini - 0.55) / 0.15).toFixed(3);
      const viejo = k < n ? k < activo : false;
      tr.arco.style.stroke = viejo ? 'color-mix(in srgb, var(--ink) 50%, transparent)' : 'var(--ink)';
      tr.punta.style.fill = viejo ? 'color-mix(in srgb, var(--ink) 50%, transparent)' : 'var(--ink)';
    });

    // cierre: tras el último paso la primera estación vuelve a encenderse (el aro empieza otra vez)
    const reinicio = clamp((t - (sN + 1.3)) / 0.3);
    this.estaciones.forEach((e, i) => {
      const s = ps[i].start + (i === 0 ? 0 : 0.45);
      const u = eo(clamp((t - s) / 0.4));
      const txt = eo(clamp((t - ps[i].start - (i === 0 ? 0 : 0.3)) / 0.45));
      const esActivo = i === 0 && reinicio > 0.5 ? true : (i === activo && !(i === n - 1 && reinicio > 0.5));
      e.nodo.style.opacity = u.toFixed(3);
      e.num.style.opacity = u.toFixed(3);
      e.nodo.setAttribute('fill', esActivo ? 'var(--acento)' : 'var(--bg)');
      e.nodo.setAttribute('stroke', esActivo ? 'var(--acento)' : 'var(--ink)');
      e.num.setAttribute('fill', esActivo ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)');
      e.el.style.opacity = (txt * (esActivo ? 1 : i <= activo ? 0.5 : 1)).toFixed(3);
      e.el.style.color = esActivo ? 'var(--acento)' : 'var(--ink)';
      e.el.style.marginTop = ((1 - txt) * 14).toFixed(1) + 'px';
    });

    if (this.limite) {
      const u = eo(clamp((t - (sN + 1.1)) / 0.45));
      this.limite.marca.style.opacity = u.toFixed(3);
      this.limite.el.style.opacity = u.toFixed(3);
    }
  },
});
