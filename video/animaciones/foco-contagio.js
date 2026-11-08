// Animación «foco-contagio» (mecanismo onda): algo empieza en un punto y se propaga. El primer paso es el foco, un
// círculo grande que late en el centro y emite ondas; cada paso siguiente es un nodo alrededor que se enciende justo
// cuando un frente de onda salido del foco lo alcanza (T.pasos[i].start), queda unido al foco por un trazo y empieza
// a emitir sus propias ondas pequeñas. Sirve para un caso que destapa otros, un brote que se contagia, una noticia
// que se riega. Estilo Noche: lo único en acento es el paso que la voz dice. seek puro: todo es función de t.
ANIM.registrar('foco-contagio', {
  meta: {
    descripcion: 'onda desde un foco: el centro late y sus ondas encienden, una tras otra, los nodos de alrededor',
    mecanismo: 'onda',
    temas: ['contagio', 'propagacion', 'casos derivados', 'brote', 'efecto domino', 'investigacion'],
    pasos: [2, 6],
    ejemplo: { titulo: '¿Cómo se contagia un brote?', pasos: ['Un enfermo', 'Toda su familia', 'La escuela del barrio'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length, k = n - 1;
    const NS = 'http://www.w3.org/2000/svg';
    this.V = V;
    const ro = Math.min(124, H * 0.14, W * 0.16);
    const cx = W / 2, cy = k <= 2 ? H * 0.27 : H * 0.36;
    this.cx = cx; this.cy = cy; this.ro = ro;
    // posiciones de los nodos: con 1–2, abajo en abanico; con 3+, alrededor del foco
    const rn = k <= 2 ? 58 : (k <= 3 ? 50 : 42);
    this.rn = rn;
    const pos = [];
    for (let j = 0; j < k; j++) {
      let a;
      if (k === 1) a = Math.PI / 2;
      else if (k <= 3) a = Math.PI * (0.76 - 0.52 * j / (k - 1));
      else a = -Math.PI * 0.82 + (2 * Math.PI * (j + 0.5)) / k;
      const rx = W * (k <= 3 ? 0.33 : 0.35), ry = H * (k <= 2 ? 0.44 : 0.36);
      pos.push({ x: cx + rx * Math.cos(a), y: cy + ry * Math.sin(a) });
    }
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:hidden;pointer-events:none';
    lienzo.appendChild(svg);
    const circ = (r, attrs) => {
      const c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', attrs.x); c.setAttribute('cy', attrs.y); c.setAttribute('r', r);
      c.setAttribute('fill', attrs.fill || 'none');
      if (attrs.stroke) { c.setAttribute('stroke', attrs.stroke); c.setAttribute('stroke-width', attrs.sw || 6); }
      svg.appendChild(c); return c;
    };
    // ondas de fondo del foco (tres a la vez, desfasadas)
    this.rmax = Math.hypot(W / 2, H / 2) * 0.95;
    this.ondas = [0, 1, 2].map(() => circ(ro, { x: cx, y: cy, stroke: 'var(--ink)', sw: 5 }));
    // trazos foco → nodo y frente de onda que lleva a cada nodo
    this.nodos = pos.map((p) => {
      const d = Math.hypot(p.x - cx, p.y - cy), ux = (p.x - cx) / d, uy = (p.y - cy) / d;
      const linea = document.createElementNS(NS, 'line');
      linea.setAttribute('x1', cx + ux * ro); linea.setAttribute('y1', cy + uy * ro);
      linea.setAttribute('x2', p.x - ux * rn); linea.setAttribute('y2', p.y - uy * rn);
      linea.setAttribute('stroke', 'var(--ink)'); linea.setAttribute('stroke-width', 6); linea.setAttribute('stroke-linecap', 'round');
      svg.appendChild(linea);
      const L = d - ro - rn;
      linea.style.strokeDasharray = L;
      const frente = circ(ro, { x: cx, y: cy, stroke: 'var(--ink)', sw: 7 });
      const eco = circ(rn, { x: p.x, y: p.y, stroke: 'var(--ink)', sw: 5 });
      const nodo = circ(rn, { x: p.x, y: p.y, stroke: 'var(--ink)', sw: 6 });
      return { p, d, linea, L, frente, eco, nodo };
    });
    // el foco encima de sus ondas
    this.foco = circ(ro, { x: cx, y: cy, stroke: 'var(--ink)', sw: 7 });
    // rótulos (HTML): el del foco dentro del círculo, los de los nodos debajo de cada uno
    const rot = (txt, x, y, w, fs, ancla) => {
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:${(x - w / 2).toFixed(1)}px;top:${y.toFixed(1)}px;width:${w.toFixed(1)}px;` +
        `text-align:center;font:900 ${fs}px/0.98 Archivo,sans-serif;font-stretch:62.5%;text-transform:uppercase;` +
        `letter-spacing:.005em;color:var(--ink);${ancla ? 'transform:translateY(-50%);' : ''}`;
      el.textContent = txt;
      lienzo.appendChild(el); return el;
    };
    this.focoRot = rot(P.pasos[0], cx, cy, ro * 1.75, ctx.F45 ? 46 : 52, true);
    const wl = Math.min(340, (W - 124) / Math.min(k, 3));
    const fs = k <= 3 ? (ctx.F45 ? 42 : 46) : 38;
    this.nodos.forEach((nd, j) => {
      const x = Math.min(W - wl / 2 - 62, Math.max(wl / 2 + 62, nd.p.x));
      nd.rot = rot(P.pasos[j + 1], x, nd.p.y + rn + 16, wl, fs, false);
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, s0 = ps[0].start;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    const fant = 0;   // nada antes de que la voz lo diga (A2); entre pasos, quieto (A1; cámara quieta 2026-11-07)
    // foco
    const e0 = eo(clamp((t - s0) / 0.45));
    const late = 1;
    const focoAct = activo === 0 && e0 > 0.5;
    this.foco.setAttribute('r', (this.ro * (0.9 + 0.1 * e0) * late).toFixed(2));
    this.foco.style.opacity = Math.max(fant, e0).toFixed(3);
    this.foco.setAttribute('fill', focoAct ? 'var(--acento)' : (e0 > 0.5 ? 'color-mix(in srgb, var(--ink) 16%, transparent)' : 'none'));
    this.foco.setAttribute('stroke', focoAct ? 'var(--acento)' : 'var(--ink)');
    this.focoRot.style.opacity = Math.max(fant, e0).toFixed(3);
    this.focoRot.style.color = focoAct ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)';
    // ondas de fondo: nacen en el borde del foco y se apagan al crecer (ciclo de 2.4 s, tres desfasadas)
    this.ondas.forEach((c, j) => {
      if (t < s0) { c.style.display = 'none'; return; }
      c.style.display = '';
      const u = clamp((t - s0 - j * 0.35) / 1.2);   // tres ondas al encenderse el foco, y se calla
      c.setAttribute('r', (this.ro + u * (this.rmax - this.ro)).toFixed(2));
      c.style.opacity = (0.32 * (1 - u) * e0).toFixed(3);
    });
    // nodos: el frente sale del foco al decirse el paso y llega justo cuando la voz dice el paso
    this.nodos.forEach((nd, j) => {
      const s = ps[j + 1].start, viaje = 0.12, a = s - viaje;   // el frente sale justo antes (entre pasos, quieto: A1)
      const u = clamp((t - a) / viaje);
      if (t < a || t > s + 0.35) nd.frente.style.display = 'none';
      else {
        nd.frente.style.display = '';
        const r = this.ro + eo(u) * (nd.d - this.ro) + (t > s ? (t - s) * 120 : 0);
        nd.frente.setAttribute('r', r.toFixed(2));
        nd.frente.style.opacity = (t > s ? 0.85 * (1 - (t - s) / 0.35) : 0.85).toFixed(3);
      }
      nd.linea.style.strokeDashoffset = (nd.L * (1 - eo(u))).toFixed(1);
      nd.linea.style.opacity = Math.max(fant * 0.6, 0.55 * u).toFixed(3);
      const en = eo(clamp((t - s) / 0.45));
      const act = activo === j + 1 && en > 0.5;
      const resp = 1;
      nd.nodo.setAttribute('r', (this.rn * (0.8 + 0.2 * en) * resp).toFixed(2));
      nd.nodo.style.opacity = Math.max(fant, en).toFixed(3);
      nd.nodo.setAttribute('fill', act ? 'var(--acento)' : (en > 0.5 ? 'var(--a2)' : 'none'));
      nd.nodo.setAttribute('stroke', act ? 'var(--acento)' : 'var(--ink)');
      nd.rot.style.opacity = Math.max(fant, en * (activo === j + 1 ? 1 : 0.6)).toFixed(3);
      nd.rot.style.transform = `translateY(${((1 - en) * 14).toFixed(1)}px)`;
      // eco del nodo encendido: su propia onda pequeña (contagia)
      if (t < s) { nd.eco.style.display = 'none'; return; }
      nd.eco.style.display = '';
      const v = clamp((t - s) / 1.2);   // un eco al encenderse
      nd.eco.setAttribute('r', (this.rn + v * 90).toFixed(2));
      nd.eco.style.opacity = (0.4 * (1 - v) * en).toFixed(3);
    });
  },
});
