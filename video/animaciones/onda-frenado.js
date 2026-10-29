// Animación «onda-frenado» (semilla de la biblioteca, mecanismo «onda»): una fila de carros vistos de lado avanza
// de izquierda a derecha por un carril. Primero la fila se densifica (entran más carros por la izquierda), luego la
// separación entre ellos se acorta, luego el carro de adelante (el de la derecha) frena: su luz trasera se enciende
// en el acento y la onda de frenado viaja HACIA ATRÁS de carro en carro, más rápido de lo que avanzan los carros; al
// final la fila queda casi quieta, apretada y toda en rojo: la cola. Con 2–6 pasos las fases se reparten entre los
// pasos (el primero siempre densifica, el último siempre deja la cola formada). Los pasos van como rótulos debajo
// del carril: el activo pleno, los anteriores atenuados. Estilo Noche: carros, carril y rótulos en crema; lo único en
// acento es el frenazo (luces, carrocería frenada, la onda y la llave de la cola). Todo es función de t (seek puro, sin
// azar ni reloj): la distancia recorrida (rayas del carril y giro de las ruedas) se integra con paso fijo desde t = 0.
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const N = 7;                       // carros (la cola sigue más allá del borde izquierdo)
  const FB = 2, OLA = 1.6, DB = 0.4; // fase en que frena el de adelante, lo que tarda la onda en llegar atrás, frenada
  // fases: 0–1 densifica · 1–2 menos espacio · 2–4 frenazo y onda hacia atrás · 4–5 la cola
  const RANGOS = {
    2: [[0, 2], [2, 5]],
    3: [[0, 2], [2, 4], [4, 5]],
    4: [[0, 1], [1, 2], [2, 4], [4, 5]],
    5: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]],
    6: [[0, 1], [1, 2], [2, 3], [3, 3.5], [3.5, 4], [4, 5]],
  };
  const el = (tag, attrs, padre) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(e);
    return e;
  };
  const lerp = (a, b, p) => a + (b - a) * p;
  const suave = (p) => p * p * (3 - 2 * p);

  ANIM.registrar('onda-frenado', {
    meta: {
      descripcion: 'onda de frenado: una fila de carros se aprieta y la luz del frenazo viaja hacia atrás hasta formar la cola',
      mecanismo: 'onda',
      temas: ['tránsito', 'tráfico', 'cola', 'contagio', 'propagación', 'onda'],
      pasos: [2, 6],
      ejemplo: {
        titulo: 'Cómo nace una cola',
        pasos: ['Más carros por kilómetro', 'Menos espacio entre ellos', 'Un frenazo se contagia', 'Se forma la cola'],
      },
    },

    pintar(lienzo, P, ctx) {
      const { V } = ctx, n = P.pasos.length;
      this.V = V;
      this.rangos = RANGOS[Math.min(6, Math.max(2, n))];
      const ancho = ctx.ancho, alto = ctx.alto;
      const m = ctx.F45 ? 30 : 24, W = ancho - 2 * m;
      const L = W / 5.8;
      this.L = L; this.m = m;
      this.xF = ancho - m - L;              // trasera del carro de adelante (fija: la cámara lo sigue)
      this.g = [2.0 * L, 0.85 * L, 0.42 * L, 0.14 * L, 0.06 * L]; // separaciones: inicio, densa, corta, frenada, cola

      // rótulos de los pasos (se miden primero para repartir el alto)
      const caja = document.createElement('div');
      caja.style.cssText = 'position:absolute;left:0;top:0;width:100%';
      lienzo.appendChild(caja);
      const medir = (fs) => {
        caja.innerHTML = '';
        this.filas = P.pasos.map((txt) => {
          const f = document.createElement('div');
          f.style.cssText = `position:relative;padding-left:30px;margin-bottom:${Math.round(fs * 0.32)}px;` +
            `font:800 ${fs}px/1.12 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);transform-origin:0 50%`;
          const barra = document.createElement('div');
          barra.style.cssText = `position:absolute;left:0;top:${Math.round(fs * 0.1)}px;width:9px;height:${Math.round(fs * 0.95)}px;` +
            'border-radius:5px;background:var(--ink)';   // el acento es del frenazo
          const tx = document.createElement('span');
          tx.textContent = txt;
          f.appendChild(barra); f.appendChild(tx);
          f._barra = barra;
          caja.appendChild(f);
          return f;
        });
        return caja.offsetHeight;
      };
      let fs = ctx.F45 ? 46 : 52, Hl = medir(fs);
      while (Hl > alto * 0.48 && fs > 44) { fs -= 2; Hl = medir(fs); }
      this.fs = fs;

      const Hc = 0.74 * L + 70 + 110;       // carril: onda arriba, carros, rayas y llave de la cola abajo
      const esp = Math.max(0, alto - Hc - Hl);
      const top0 = esp * 0.4;
      const yG = top0 + 0.74 * L + 70;
      this.yG = yG;
      caja.style.top = (top0 + Hc + esp * 0.25).toFixed(1) + 'px';

      const svg = el('svg', { width: ancho, height: Math.ceil(yG + 110) });
      svg.style.cssText = 'position:absolute;left:0;top:0;overflow:hidden';
      lienzo.insertBefore(svg, caja);

      // franja de la onda (detrás de los carros) y su frente con flechas hacia atrás
      this.franja = el('rect', { y: (yG - 0.88 * L).toFixed(1), height: (1.0 * L).toFixed(1), rx: (0.2 * L).toFixed(1),
        fill: 'color-mix(in srgb, var(--acento) 16%, transparent)' }, svg);
      this.estela = el('line', { y1: (yG - 0.74 * L - 34).toFixed(1), y2: (yG - 0.74 * L - 34).toFixed(1),
        stroke: 'color-mix(in srgb, var(--acento) 45%, transparent)', 'stroke-width': 5, 'stroke-linecap': 'round' }, svg);
      this.flechas = el('g', {}, svg);
      const fy = 0, fh = 18;
      [0, 26].forEach((dx) => el('path', { d: `M${dx + 16},${fy - fh} L${dx},${fy} L${dx + 16},${fy + fh}`, fill: 'none',
        stroke: 'var(--acento)', 'stroke-width': 7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, this.flechas));

      // carril: suelo y rayas que corren
      el('line', { x1: m, x2: ancho - m, y1: yG + 3, y2: yG + 3, stroke: 'color-mix(in srgb, var(--ink) 30%, transparent)',
        'stroke-width': 6, 'stroke-linecap': 'round' }, svg);
      this.periodo = 0.9 * L;
      this.rayas = el('line', { x1: m, x2: ancho - m, y1: yG + 34, y2: yG + 34,
        stroke: 'color-mix(in srgb, var(--ink) 38%, transparent)', 'stroke-width': 6,
        'stroke-dasharray': `${(0.45 * L).toFixed(1)} ${(0.45 * L).toFixed(1)}` }, svg);

      // llave de la cola
      this.llave = el('path', { fill: 'none', stroke: 'var(--acento)', 'stroke-width': 6, 'stroke-linecap': 'round',
        'stroke-linejoin': 'round', pathLength: 1 }, svg);
      this.yLl = yG + 78;

      // marcas de separación entre carros
      this.marcas = [];
      for (let k = 1; k < N; k++) {
        this.marcas.push(el('path', { fill: 'none', stroke: 'var(--a3)', 'stroke-width': 5, 'stroke-linecap': 'round' }, svg));
      }

      // carros (k = 0 es el de adelante, a la derecha)
      const u = (v) => (v * L).toFixed(1);
      // alto de la carrocería estirado (carro grande y legible); lo de abajo (ruedas) no se estira
      const uy = (v) => ((v >= -0.14 ? v : -0.14 + (v + 0.14) * 1.3) * L).toFixed(1);
      const cuerpo = `M${u(0.05)},${uy(-0.14)} L${u(0.95)},${uy(-0.14)} Q${u(1)},${uy(-0.14)} ${u(1)},${uy(-0.2)} ` +
        `L${u(1)},${uy(-0.3)} Q${u(1)},${uy(-0.36)} ${u(0.93)},${uy(-0.37)} L${u(0.76)},${uy(-0.39)} L${u(0.64)},${uy(-0.55)} ` +
        `Q${u(0.61)},${uy(-0.58)} ${u(0.56)},${uy(-0.58)} L${u(0.31)},${uy(-0.58)} Q${u(0.26)},${uy(-0.58)} ${u(0.23)},${uy(-0.55)} ` +
        `L${u(0.12)},${uy(-0.4)} L${u(0.05)},${uy(-0.39)} Q0,${uy(-0.38)} 0,${uy(-0.32)} L0,${uy(-0.2)} Q0,${uy(-0.14)} ${u(0.05)},${uy(-0.14)} Z`;
      const ventanas = [
        `M${u(0.2)},${uy(-0.42)} L${u(0.29)},${uy(-0.52)} L${u(0.42)},${uy(-0.52)} L${u(0.42)},${uy(-0.42)} Z`,
        `M${u(0.47)},${uy(-0.42)} L${u(0.47)},${uy(-0.52)} L${u(0.58)},${uy(-0.52)} L${u(0.67)},${uy(-0.42)} Z`,
      ];
      const r = 0.13 * L;
      this.r = r;
      this.carros = [];
      for (let k = 0; k < N; k++) {
        const g = el('g', {}, svg);
        const halo = el('circle', { cx: 0, cy: uy(-0.29), r: u(0.26), fill: 'var(--acento)', opacity: 0 }, g);
        const body = el('path', { d: cuerpo, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linejoin': 'round' }, g);
        ventanas.forEach((d) => el('path', { d, fill: 'color-mix(in srgb, var(--ink) 28%, transparent)' }, g));
        const luz = el('rect', { x: u(-0.02), y: uy(-0.35), width: u(0.08), height: u(0.13), rx: 3 }, g);
        el('rect', { x: u(0.95), y: uy(-0.33), width: u(0.06), height: u(0.08), rx: 3, fill: 'var(--bg)' }, g);
        const ruedas = [0.23, 0.77].map((cx) => {
          const w = el('g', {}, g);
          el('circle', { cx: 0, cy: 0, r: r.toFixed(1), fill: 'var(--ink)' }, w);
          el('circle', { cx: 0, cy: 0, r: (r * 0.5).toFixed(1), fill: 'var(--bg)' }, w);
          el('line', { x1: (-r * 0.5).toFixed(1), x2: (r * 0.5).toFixed(1), y1: 0, y2: 0, stroke: 'var(--ink)', 'stroke-width': 5 }, w);
          return { w, cx: cx * L };
        });
        this.carros.push({ g, halo, body, luz, ruedas });
      }
    },

    // fase continua 0–5 en el segundo t (cada paso mueve su tramo cuando la voz lo dice)
    fase(t, T) {
      const ps = T.pasos, R = this.rangos;
      let f = 0;
      for (let i = 0; i < ps.length && i < R.length; i++) {
        const s = ps[i].start;
        if (t < s) break;
        const e = i + 1 < ps.length ? ps[i + 1].start : Math.max(T.fin, s + 1);
        const [a, b] = R[i];
        const dd = Math.min(Math.max(0.5, (e - s) * 0.85), 0.9 + 1.1 * (b - a));
        f = a + (b - a) * suave(this.V.clamp((t - s) / dd));
      }
      return f;
    },
    frena(k, f) { return this.V.clamp((f - (FB + OLA * k / (N - 1))) / DB); },
    velocidad(k, f) { return 1 - 0.92 * this.frena(k, f); },

    seek(t, T) {
      const { clamp, eo } = this.V, L = this.L, m = this.m;
      const f = this.fase(t, T);

      // distancia recorrida por cada carro: integral con paso fijo desde 0 (puro y continuo)
      const h = 1 / 30, d = new Array(N).fill(0);
      let tau = 0;
      while (tau < t) {
        const paso = Math.min(h, t - tau), fm = this.fase(tau + paso / 2, T);
        for (let k = 0; k < N; k++) d[k] += this.velocidad(k, fm) * paso;
        tau += paso;
      }
      const pxs = 2.4 * L; // píxeles por segundo a velocidad libre

      // separaciones y posiciones (la cámara sigue al carro de adelante)
      const [g0, g1, g2, gq, g3] = this.g;
      let base = f < 1 ? lerp(g0, g1, suave(clamp(f))) : lerp(g1, g2, suave(clamp(f - 1)));
      const xs = [this.xF];
      for (let k = 1; k < N; k++) {
        const ini = FB + OLA * (k - 1) / (N - 1), fin = FB + OLA * k / (N - 1) + DB;
        let gap = lerp(base, gq, suave(clamp((f - ini) / (fin - ini))));
        gap = lerp(gap, g3, suave(clamp(f - 4)));
        xs.push(xs[k - 1] - L - gap);
      }

      // carros
      const pulso = 0.85 + 0.15 * Math.sin(t * 2.4);
      this.carros.forEach((c, k) => {
        const x = xs[k], b = this.frena(k, f), v = this.velocidad(k, f);
        const vis = clamp((x - m) / (0.9 * L));
        c.g.style.visibility = vis > 0 ? 'visible' : 'hidden';
        c.g.style.opacity = vis.toFixed(3);
        const bob = Math.sin(t * 7.5 + k * 1.9) * 1.6 * v;
        c.g.setAttribute('transform', `translate(${Math.max(m, x).toFixed(1)},${(this.yG + bob).toFixed(2)})`);
        // libre: carrocería clara del fondo; frenado: se tiñe del acento
        c.body.setAttribute('fill', `color-mix(in srgb, var(--acento) ${Math.round(55 * b)}%, color-mix(in srgb, var(--ink) 10%, var(--bg)))`);
        const brillo = b * (k === 0 || f > 4 ? pulso : 1);
        c.luz.setAttribute('fill', b > 0.02 ? `color-mix(in srgb, var(--acento) ${Math.round(30 + 70 * brillo)}%, var(--bg))`
          : 'color-mix(in srgb, var(--acento) 25%, var(--bg))');
        c.halo.setAttribute('opacity', (0.38 * brillo * eo(b)).toFixed(3));
        const ang = ((d[k] * pxs) / this.r) * 57.2958 + k * 37;
        c.ruedas.forEach((rd, j) => rd.w.setAttribute('transform',
          `translate(${rd.cx.toFixed(1)},${(-this.r).toFixed(1)}) rotate(${((ang + j * 50) % 360).toFixed(1)})`));
      });

      // rayas del carril (corren con el carro de adelante)
      this.rayas.setAttribute('stroke-dashoffset', ((d[0] * pxs) % this.periodo).toFixed(1));

      // frente de la onda: viaja de adelante hacia atrás
      const kf = clamp((f - FB) / OLA) * (N - 1), k0 = Math.floor(kf), k1 = Math.min(N - 1, k0 + 1);
      const xw = Math.max(m, lerp(xs[k0], xs[k1], kf - k0) - 0.12 * L);
      const xFin = this.xF + 1.04 * L;
      const onOla = clamp((f - FB) / 0.15);
      this.franja.setAttribute('x', xw.toFixed(1));
      this.franja.setAttribute('width', Math.max(0, xFin - xw).toFixed(1));
      this.franja.setAttribute('opacity', (onOla * (0.8 + 0.2 * Math.sin(t * 2))).toFixed(3));
      const fl = onOla * (1 - clamp((f - (FB + OLA)) / 0.35));
      const yA = this.yG - 0.74 * L - 34, osc = 6 * Math.sin(t * 6);
      this.flechas.setAttribute('transform', `translate(${(xw - 10 + osc).toFixed(1)},${yA.toFixed(1)})`);
      this.flechas.setAttribute('opacity', fl.toFixed(3));
      this.estela.setAttribute('x1', (xw + 60).toFixed(1));
      this.estela.setAttribute('x2', (xFin - 0.2 * L).toFixed(1));
      this.estela.setAttribute('opacity', (fl * clamp((xFin - xw - 0.4 * L) / L)).toFixed(3));

      // marcas de separación (cuando la voz habla del espacio)
      const onM = clamp((f - 0.85) / 0.25) * (1 - clamp((f - 2.3) / 0.4));
      this.marcas.forEach((p, i) => {
        const k = i + 1, a = xs[k] + L + 8, b = xs[k - 1] - 8, y = this.yG - 0.24 * L;
        if (b - a < 12 || xs[k] < m) { p.setAttribute('opacity', 0); return; }
        p.setAttribute('d', `M${a.toFixed(1)},${(y - 12).toFixed(1)} L${a.toFixed(1)},${(y + 12).toFixed(1)} M${a.toFixed(1)},${y.toFixed(1)} ` +
          `L${b.toFixed(1)},${y.toFixed(1)} M${b.toFixed(1)},${(y - 12).toFixed(1)} L${b.toFixed(1)},${(y + 12).toFixed(1)}`);
        p.setAttribute('opacity', (onM * clamp((xs[k] - m) / (0.6 * L))).toFixed(3));
      });

      // llave de la cola: abarca la fila apretada
      const pc = eo(clamp((f - 4) / 0.8));
      const x1 = Math.max(m, xs[N - 1]), x2 = xFin - 0.04 * L, yl = this.yLl;
      this.llave.setAttribute('d', `M${x1.toFixed(1)},${(yl - 16).toFixed(1)} L${x1.toFixed(1)},${yl.toFixed(1)} ` +
        `L${x2.toFixed(1)},${yl.toFixed(1)} L${x2.toFixed(1)},${(yl - 16).toFixed(1)}`);
      this.llave.setAttribute('stroke-dasharray', `${pc.toFixed(3)} 1`);
      this.llave.setAttribute('opacity', pc > 0 ? 1 : 0);

      // rótulos: el activo pleno, los anteriores atenuados, los que vienen apenas insinuados
      const ps = T.pasos;
      let activo = -1;
      ps.forEach((p, i) => { if (t >= p.start) activo = i; });
      const chico = Math.max(38 / this.fs, 0.8);
      this.filas.forEach((fila, i) => {
        if (i >= ps.length) { fila.style.opacity = 0; return; }
        const entra = eo((t - ps[i].start) / 0.45), fantasma = 0.28 * eo((t - T.ini) / 0.5);
        const es = i === activo ? 1 : 0;
        const op = i <= activo ? (es ? lerp(0.45, 1, entra) : 0.45) : fantasma;
        fila.style.opacity = Math.max(fantasma, op).toFixed(3);
        const esc = i === activo ? lerp(chico, 1, entra) : chico;
        fila.style.transform = `translateX(${(i === activo ? (1 - entra) * -24 : 0).toFixed(1)}px) scale(${esc.toFixed(3)})`;
        fila._barra.style.opacity = (es * entra).toFixed(3);
      });
    },
  });
})();
