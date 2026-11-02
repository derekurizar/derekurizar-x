// Animación «oleadas-cauce» (mecanismo «onda»): un cerro visto de frente con un cauce que baja por su cara hasta el
// pie, donde hay casas. Primero se acumula una masa en la ladera (en acento, respira); luego se suelta en oleadas que
// bajan una tras otra; sin cauce se abren y se apagan pronto. Cuando el cauce se encaja (sus bordes pasan de tenues a
// firmes), las oleadas se angostan, se alargan y llegan más lejos; con la última fase aparecen granos finos bajo el
// frente, el flujo pasa la marca donde antes se detenía y se desborda al pie sobre las casas. Con 2–6 pasos las fases
// se reparten entre los pasos (el primero siempre acumula, el último siempre llega al pie). Los pasos van como rótulos
// debajo del dibujo: el activo pleno, los anteriores atenuados. Estilo Noche: cerro, cauce, casas y rótulos en crema;
// lo único en acento es lo que se mueve cuesta abajo (la masa al inicio, después las oleadas y el desborde). Todo es
// función de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const VW = 1000, VH = 780;             // dibujo virtual (viewBox)
  const NP = 3, PD = 1.9;                // oleadas a la vez y lo que tarda cada una en bajar
  // fases: 0–1 acumula · 1–2 oleadas · 2–3 cauce que encaja · 3–4 resbala, pasa la marca y desborda
  const RANGOS = {
    2: [[0, 2], [2, 4]],
    3: [[0, 1], [1, 2], [2, 4]],
    4: [[0, 1], [1, 2], [2, 3], [3, 4]],
    5: [[0, 1], [1, 2], [2, 3], [3, 3.5], [3.5, 4]],
    6: [[0, 1], [1, 1.5], [1.5, 2], [2, 3], [3, 3.5], [3.5, 4]],
  };
  const el = (tag, attrs, padre) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (padre) padre.appendChild(e);
    return e;
  };
  const lerp = (a, b, p) => a + (b - a) * p;
  const cl = (x) => Math.max(0, Math.min(1, x));
  const suave = (p) => { p = cl(p); return p * p * (3 - 2 * p); };
  const tenue = (pct) => `color-mix(in srgb, var(--ink) ${pct}%, transparent)`;

  ANIM.registrar('oleadas-cauce', {
    meta: {
      descripcion: 'oleadas por un cauce: una masa en la ladera baja en pulsos, el cauce la encaja y llega más lejos hasta desbordarse al pie',
      mecanismo: 'onda',
      temas: ['volcán', 'lahar', 'flujo piroclástico', 'deslave', 'crecida', 'barranca', 'río', 'inundación', 'avalancha'],
      pasos: [2, 6],
      ejemplo: {
        titulo: '¿Por qué llegó tan lejos?',
        pasos: ['Material en la ladera', 'Baja en oleadas', 'Encajonado en el cauce', 'Ceniza fina: resbala'],
      },
    },

    pintar(lienzo, P, ctx) {
      const { V } = ctx, n = P.pasos.length;
      this.V = V;
      this.rangos = RANGOS[Math.min(6, Math.max(2, n))];
      const ancho = ctx.ancho, alto = ctx.alto;

      // rótulos de los pasos, abajo (se miden primero para repartir el alto)
      const caja = document.createElement('div');
      caja.style.cssText = 'position:absolute;left:0;width:100%';
      lienzo.appendChild(caja);
      const medir = (fs) => {
        caja.innerHTML = '';
        this.filas = P.pasos.map((txt, i) => {
          const f = document.createElement('div');
          f.style.cssText = `display:flex;align-items:baseline;margin-bottom:${Math.round(fs * 0.3)}px;` +
            `font:800 ${fs}px/1.12 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);transform-origin:0 50%`;
          const num = document.createElement('span');
          num.style.cssText = `font:600 36px/1 'JetBrains Mono',monospace;margin-right:22px;opacity:.6;flex:none`;
          num.textContent = i + 1;
          const tx = document.createElement('span');
          tx.textContent = txt;
          f.appendChild(num); f.appendChild(tx);
          caja.appendChild(f);
          return f;
        });
        return caja.offsetHeight;
      };
      let fs = ctx.F45 ? 44 : 50, Hl = medir(fs);
      while (Hl > alto * (ctx.F45 ? 0.42 : 0.38) && fs > 38) { fs -= 2; Hl = medir(fs); }
      const Hd = Math.max(200, alto - Hl - 24);
      caja.style.top = (alto - Hl).toFixed(1) + 'px';

      const svg = el('svg', { width: ancho, height: Hd.toFixed(0), viewBox: `0 0 ${VW} ${VH}`, preserveAspectRatio: 'xMidYMid meet' });
      svg.style.cssText = 'position:absolute;left:0;top:0;overflow:hidden';
      lienzo.insertBefore(svg, caja);
      const esc = Math.min(ancho / VW, Hd / VH);
      const sw = (px) => (px / esc).toFixed(1);   // grosor en px reales → unidades del dibujo
      this.sw = sw;

      // lo fijo: suelo, cerro, columna de humo
      this.fijo = el('g', {}, svg);
      el('line', { x1: 0, x2: VW, y1: 700, y2: 700, stroke: tenue(40), 'stroke-width': sw(6), 'stroke-linecap': 'round' }, this.fijo);
      el('path', { d: 'M30,700 C250,560 380,250 430,92 L455,104 480,112 505,104 530,92 C580,250 730,560 970,700',
        fill: tenue(6), stroke: tenue(55), 'stroke-width': sw(6), 'stroke-linejoin': 'round' }, this.fijo);
      this.humo = [0, 1, 2].map(() => el('circle', { cx: 480, cy: 90, r: 20, fill: tenue(30) }, svg));

      // cauce: línea central muestreada; bordes y lecho a partir de sus normales
      const guia = el('path', { d: 'M600,236 C655,330 560,400 612,490 S725,610 704,700', fill: 'none' }, svg);
      const L = guia.getTotalLength(), M = 160;
      this.L = L;
      this.mu = [];
      for (let k = 0; k <= M; k++) {
        const s = (k / M) * L, a = guia.getPointAtLength(Math.max(0, s - 2)), b = guia.getPointAtLength(Math.min(L, s + 2));
        const p = guia.getPointAtLength(s), ang = Math.atan2(b.y - a.y, b.x - a.x);
        this.mu.push({ x: p.x, y: p.y, ang, nx: -Math.sin(ang), ny: Math.cos(ang), w: lerp(30, 22, k / M) });
      }
      guia.remove();
      const borde = (sg) => this.mu.map((m, k) => `${k ? 'L' : 'M'}${(m.x + sg * m.nx * m.w).toFixed(1)},${(m.y + sg * m.ny * m.w).toFixed(1)}`).join(' ');
      const izq = borde(1), der = borde(-1);
      const lecho = izq + ' ' + this.mu.slice().reverse().map((m) => `L${(m.x - m.nx * m.w).toFixed(1)},${(m.y - m.ny * m.w).toFixed(1)}`).join(' ') + ' Z';
      this.lecho = el('path', { d: lecho, fill: tenue(14) }, svg);
      this.bordes = [izq, der].map((d) => el('path', { d, fill: 'none', stroke: 'var(--ink)', 'stroke-width': sw(6),
        'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, svg));

      // marca donde se detenía antes (aparece en la última fase)
      const mk = this.mu[Math.round(0.72 * M)];
      this.marca = el('line', { x1: (mk.x + mk.nx * 46).toFixed(1), y1: (mk.y + mk.ny * 46).toFixed(1),
        x2: (mk.x - mk.nx * 46).toFixed(1), y2: (mk.y - mk.ny * 46).toFixed(1), stroke: tenue(55), 'stroke-width': sw(5),
        'stroke-dasharray': `${sw(9)} ${sw(9)}`, 'stroke-linecap': 'round' }, svg);

      // desborde al pie (detrás de las casas)
      const fin = this.mu[M];
      this.pie = { x: fin.x, y: fin.y };
      this.lobulo = el('ellipse', { cx: fin.x.toFixed(1), cy: (fin.y - 4).toFixed(1), rx: 1, ry: 1, fill: 'var(--acento)' }, svg);

      // masa acumulada en la cabecera del cauce
      const c0 = this.mu[0];
      this.masa = el('ellipse', { cx: (c0.x - 18).toFixed(1), cy: (c0.y - 16).toFixed(1), rx: 70, ry: 38,
        transform: `rotate(28 ${(c0.x - 18).toFixed(1)} ${(c0.y - 16).toFixed(1)})` }, svg);

      // oleadas: cabeza + dos tramos de cola, y granos finos
      this.olas = [];
      for (let k = 0; k < NP; k++) {
        const g = el('g', {}, svg);
        const partes = [0.45, 0.7, 1].map((op) => el('ellipse', { rx: 1, ry: 1, fill: 'var(--acento)', opacity: op }, g));
        const granos = [0, 1, 2, 3, 4].map(() => el('circle', { r: sw(5), fill: 'var(--ink)' }, g));
        this.olas.push({ g, partes, granos });
      }

      // casas al pie, a los dos lados de la salida del cauce
      const casa = (cx) => {
        const w = 58, h = 40, y = 700;
        el('path', { d: `M${cx - w / 2},${y} L${cx - w / 2},${y - h} L${cx},${y - h - 30} L${cx + w / 2},${y - h} L${cx + w / 2},${y} Z`,
          fill: 'none', stroke: 'var(--ink)', 'stroke-width': sw(6), 'stroke-linejoin': 'round' }, svg);
      };
      [fin.x - 120, fin.x + 110].forEach(casa);
    },

    fase(t, T) {
      const ps = T.pasos;
      let i = -1;
      ps.forEach((p, k) => { if (t >= p.start) i = k; });
      if (i < 0) return 0;
      const [a, b] = this.rangos[i];
      const s = ps[i].start, e = i + 1 < ps.length ? ps[i + 1].start : Math.max(T.fin, s + 2.5);
      const d = Math.max(0.6, Math.min(2.2, (e - s) * 0.8));
      return a + (b - a) * suave((t - s) / d);
    },

    punto(sn) {
      const M = this.mu.length - 1, x = cl(sn) * M, k = Math.min(M - 1, Math.floor(x)), f = x - k;
      const a = this.mu[k], b = this.mu[k + 1];
      return { x: lerp(a.x, b.x, f), y: lerp(a.y, b.y, f), ang: lerp(a.ang, b.ang, f), nx: lerp(a.nx, b.nx, f),
        ny: lerp(a.ny, b.ny, f), w: lerp(a.w, b.w, f) };
    },

    seek(t, T) {
      const { eo } = this.V, ps = T.pasos;
      const phi = this.fase(t, T);
      const vis = eo((t - T.ini) / 0.5);
      this.fijo.style.opacity = vis.toFixed(3);

      // humo: tres bocanadas que suben del cráter en ciclo
      this.humo.forEach((h, k) => {
        const u = ((((t - T.ini) / 3.2 + k / 3) % 1) + 1) % 1;
        h.setAttribute('cy', (96 - 78 * u).toFixed(1));
        h.setAttribute('cx', (480 + 14 * Math.sin(2 * Math.PI * u + k)).toFixed(1));
        h.setAttribute('r', (16 + 20 * u).toFixed(1));
        h.style.opacity = (vis * Math.sin(Math.PI * u) * 0.9).toFixed(3);
      });

      // cauce: tenue hasta que encaja (fase 1.8–2.3)
      const enc = suave((phi - 1.8) / 0.5);
      const bo = vis * lerp(0.26, 1, enc);
      this.bordes.forEach((b) => { b.style.opacity = bo.toFixed(3); });
      this.lecho.style.opacity = (vis * lerp(0.4, 1, enc)).toFixed(3);

      // masa: crece en la fase 0–1 (en acento, respira); luego queda atenuada y se achica
      const crece = suave(phi), resp = 1 + 0.04 * Math.sin(2 * Math.PI * (t - T.ini) / 1.7);
      const sale = suave(phi - 1);
      const sm = (0.35 + 0.65 * crece) * (1 - 0.35 * sale) * resp;
      this.masa.setAttribute('rx', (70 * sm).toFixed(1));
      this.masa.setAttribute('ry', (38 * sm).toFixed(1));
      this.masa.style.fill = phi < 1.05 ? 'var(--acento)' : tenue(45);
      this.masa.style.opacity = Math.max(0.3 * vis, crece).toFixed(3);
      if (phi <= 0) { this.masa.style.fill = 'transparent'; this.masa.style.stroke = tenue(45); this.masa.style.strokeWidth = this.sw(5); }
      else { this.masa.style.stroke = 'none'; }

      // alcance de las oleadas: corto sin cauce, mayor encajonadas, todo el cauce al resbalar
      const res = suave(phi - 3);
      const alc = phi < 2 ? 0.42 : phi < 3 ? lerp(0.42, 0.74, suave(phi - 2)) : lerp(0.74, 1, res);
      const emite = cl((phi - 1) / 0.3);
      this.olas.forEach((o, k) => {
        const u = ((((t - T.ini) / PD + k / NP) % 1) + 1) % 1;
        const on = emite > 0;
        o.g.style.display = on ? '' : 'none';
        if (!on) return;
        const sn = u * alc;
        const finU = phi >= 3 ? 0.04 : 0.25;     // sin resbalar se apaga antes de terminar
        o.g.style.opacity = (emite * cl(u / 0.08) * cl((1 - u) / finU)).toFixed(3);
        // ancho: abierta sin cauce, angosta encajonada, se abre al desbordar en el pie
        const desb = res * suave((sn - 0.9) / 0.1);
        o.partes.forEach((e, j) => {
          const q = this.punto(sn - (2 - j) * 0.035 * Math.max(alc, 0.5));
          const ry = lerp(52, q.w * 0.82, enc) * (0.7 + 0.15 * j) * (1 + 1.6 * desb);
          const rx = lerp(34, 50, enc) * (0.75 + 0.12 * j);
          e.setAttribute('cx', q.x.toFixed(1)); e.setAttribute('cy', q.y.toFixed(1));
          e.setAttribute('rx', rx.toFixed(1)); e.setAttribute('ry', ry.toFixed(1));
          e.setAttribute('transform', `rotate(${(q.ang * 180 / Math.PI).toFixed(1)} ${q.x.toFixed(1)} ${q.y.toFixed(1)})`);
        });
        // granos finos bajo el frente (fase 3 en adelante)
        const go = cl((phi - 3) / 0.35);
        o.granos.forEach((gr, j) => {
          gr.style.display = go > 0 ? '' : 'none';
          if (go <= 0) return;
          const q = this.punto(sn - 0.012 * j);
          const lat = (((j * 37) % 5) - 2) / 2 * q.w * 0.55;
          gr.setAttribute('cx', (q.x + q.nx * lat).toFixed(1));
          gr.setAttribute('cy', (q.y + q.ny * lat).toFixed(1));
          gr.style.opacity = go.toFixed(3);
        });
      });

      // marca de dónde se detenía antes
      this.marca.style.opacity = (vis * cl((phi - 2.9) / 0.3)).toFixed(3);

      // desborde al pie: un lóbulo que se extiende sobre las casas
      const lob = eo(cl((phi - 3.4) / 0.6));
      this.lobulo.style.display = lob > 0 ? '' : 'none';
      if (lob > 0) {
        const ola = 1 + 0.04 * Math.sin(2 * Math.PI * (t - T.ini) / 2.1);
        this.lobulo.setAttribute('rx', (190 * lob * ola).toFixed(1));
        this.lobulo.setAttribute('ry', (26 * lob).toFixed(1));
        this.lobulo.style.opacity = (0.85 * lob).toFixed(3);
      }

      // rótulos: el activo pleno, los anteriores atenuados, los que faltan no se ven
      let activo = -1;
      ps.forEach((p, i) => { if (t >= p.start) activo = i; });
      this.filas.forEach((f, i) => {
        const entra = eo((t - ps[i].start) / 0.45);
        f.style.opacity = (entra * (i < activo ? 0.45 : 1)).toFixed(3);
        f.style.transform = `translateX(${((1 - entra) * -30).toFixed(1)}px)`;
      });
    },
  });
})();
