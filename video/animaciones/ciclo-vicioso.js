// Animación «ciclo-vicioso» (semilla de la biblioteca, mecanismo «ciclo»): 3–6 nodos repartidos en un anillo
// (una elipse que llena el lienzo), cada uno con el texto de su paso. Al entrar la escena se ven tenues todos los
// nodos y las pistas punteadas entre ellos, que fluyen despacio en el sentido del ciclo. Cuando la voz dice el paso i,
// su nodo se enciende y la flecha que llega a él se dibuja. Al encenderse el último se dibuja, en acento, la flecha de
// regreso al primero (la que cierra el ciclo) y desde ahí un pulso da vueltas al anillo; cada vuelta completa refuerza
// el anillo (trazo más grueso, más acento, halo más visible), con tope a las tres vueltas. Los nodos se iluminan cuando
// el pulso pasa por ellos. Estilo Noche: el nodo del paso que suena se llena de acento con el texto en --tinta-acento
// (en el lazo, el que toca el pulso se marca con borde y texto en acento); los demás, contorno y texto crema (lo ya
// dicho al 50 %).
// Todo es función de t (seek puro: las vueltas se calculan desde t, sin estado).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
ANIM.registrar('ciclo-vicioso', {
  meta: {
    descripcion: 'ciclo que se retroalimenta: nodos en anillo que se encienden al decirlos y un pulso que da la vuelta y lo refuerza',
    mecanismo: 'ciclo',
    temas: ['pobreza', 'ciclo', 'círculo vicioso', 'retroalimentación', 'se repite', 'trampa'],
    pasos: [3, 6],
    ejemplo: { titulo: 'Por qué cuesta salir', pasos: ['Poco ingreso', 'Se deja la escuela', 'Trabajo informal', 'Hijos con poco ingreso'] },
  },

  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, W = ctx.ancho, H = ctx.alto;
    const NS = 'http://www.w3.org/2000/svg';
    this.V = V; this.n = n;
    const m = 18, ESC = 1.06;                       // margen al borde y escala máxima de un nodo
    this.cx = W / 2; this.cy = H / 2;
    this.ang = P.pasos.map((_, i) => -Math.PI / 2 + (2 * Math.PI * i) / n);

    // nodos: cajas redondeadas con el texto del paso
    let fs = ctx.F45 ? 44 : 48, pw = Math.min(360, Math.round(W * 0.45));
    this.nodos = P.pasos.map((txt) => {
      const el = document.createElement('div');
      el.textContent = txt;
      lienzo.appendChild(el);
      return el;
    });
    const estilo = () => this.nodos.forEach((el) => {
      el.style.cssText = `position:absolute;left:0;top:0;width:${pw}px;box-sizing:border-box;padding:16px 20px;` +
        `border-radius:26px;border:5px solid transparent;text-align:center;overflow-wrap:break-word;` +
        `font:800 ${fs}px/1.12 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);transform-origin:50% 50%`;
    });
    const medir = () => {
      estilo();
      const hs = this.nodos.map((el) => el.offsetHeight), hmax = Math.max(...hs);
      const rx = W / 2 - m - (pw / 2) * ESC, ry = H / 2 - m - (hmax / 2) * ESC;
      const cajas = this.ang.map((a, i) => {
        const x = this.cx + rx * Math.cos(a), y = this.cy + ry * Math.sin(a);
        return { x, y, w: pw, h: hs[i] };
      });
      let choca = false;
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        const a = cajas[i], b = cajas[j];
        if (Math.abs(a.x - b.x) < (a.w + b.w) / 2 * ESC + 14 && Math.abs(a.y - b.y) < (a.h + b.h) / 2 * ESC + 14) choca = true;
      }
      return { rx, ry, cajas, choca };
    };
    let g = medir();
    for (let k = 0; g.choca && k < 40; k++) {
      if (pw > 220) pw -= 12; else if (fs > 36) fs -= 2; else break;
      g = medir();
    }
    this.rx = g.rx; this.ry = g.ry; this.cajas = g.cajas;
    this.nodos.forEach((el, i) => {
      const c = g.cajas[i];
      el.style.left = (c.x - c.w / 2).toFixed(1) + 'px';
      el.style.top = (c.y - c.h / 2).toFixed(1) + 'px';
    });

    // punto de la elipse y salida de cada caja (por pasos fijos: determinista)
    const pt = (a) => [this.cx + this.rx * Math.cos(a), this.cy + this.ry * Math.sin(a)];
    this.pt = pt;
    const dentro = (p, c) => Math.abs(p[0] - c.x) < c.w / 2 * ESC + 16 && Math.abs(p[1] - c.y) < c.h / 2 * ESC + 16;
    const salida = (i, dir) => {
      let d = 0;
      while (d < Math.PI / n && dentro(pt(this.ang[i] + dir * d), this.cajas[i])) d += 0.004;
      return d;
    };

    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    lienzo.insertBefore(svg, lienzo.firstChild);
    const nuevo = (tag, at) => {
      const e = document.createElementNS(NS, tag);
      Object.keys(at || {}).forEach((k) => e.setAttribute(k, at[k]));
      svg.appendChild(e);
      return e;
    };

    // halo del anillo (crece con las vueltas)
    this.halo = nuevo('ellipse', { cx: this.cx, cy: this.cy, rx: this.rx, ry: this.ry, fill: 'none' });
    this.halo.style.stroke = 'var(--acento)';

    // flecha j llega al nodo j; la 0 es la de cierre (del último al primero)
    this.flechas = this.ang.map((_, j) => {
      const de = (j - 1 + n) % n;
      const a0 = this.ang[de] + salida(de, 1);
      let a1 = this.ang[j] - salida(j, -1);
      if (a1 <= a0) a1 += 2 * Math.PI;
      const N = 56, pts = [];
      for (let k = 0; k <= N; k++) pts.push(pt(a0 + ((a1 - a0) * k) / N));
      let largo = 0;
      for (let k = 1; k < pts.length; k++) largo += Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]);
      const d = 'M' + pts.map((p) => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' L');
      const pista = nuevo('path', { d, fill: 'none', 'stroke-linecap': 'round' });
      pista.style.stroke = 'color-mix(in srgb, var(--ink) 30%, transparent)';
      pista.style.strokeWidth = '6';
      pista.style.strokeDasharray = '2 18';
      const linea = nuevo('path', { d, fill: 'none', 'stroke-linecap': 'round' });
      linea.style.strokeDasharray = largo.toFixed(1);
      // punta: un triángulo orientado con la tangente del final
      const pa = pts[N - 4], pb = pts[N];
      const rot = (Math.atan2(pb[1] - pa[1], pb[0] - pa[0]) * 180) / Math.PI;
      const punta = nuevo('path', { d: 'M 6 0 L -16 -14 L -10 0 L -16 14 Z' });
      punta.dataset.x = pb[0].toFixed(1); punta.dataset.y = pb[1].toFixed(1); punta.dataset.r = rot.toFixed(1);
      return { pista, linea, punta, largo, a0, a1, cierre: j === 0 };
    });

    // pulso con estela
    this.estela = [0, 1, 2, 3, 4, 5].map((k) => {
      const c = nuevo('circle', { r: Math.max(6, 18 - 2 * k) });
      c.style.fill = 'var(--acento)';
      if (k === 0) { c.style.stroke = 'var(--bg)'; c.style.strokeWidth = '5'; }
      return c;
    });
  },

  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n;
    const fant = eo((t - T.ini) / 0.6);
    const s = (i) => ps[Math.min(i, ps.length - 1)].start;

    // vueltas del pulso: arranca cuando se cierra el ciclo
    // el pulso sale del último nodo y él mismo dibuja la flecha de cierre; luego sigue dando vueltas
    const tLazo = s(n - 1) + 0.4, periodo = 2.4;
    const u = (t - tLazo) / periodo;
    let ref = 0;                                    // refuerzo 0..1, sube al completar cada vuelta
    if (u >= 1) {
      const k = Math.floor(u);
      ref = Math.min(3, k - 1 + eo((u - k) / 0.3)) / 3;
    }
    const enLazo = u >= 0;
    const angPulso = this.ang[n - 1] + 2 * Math.PI * Math.max(0, u);

    // halo
    this.halo.style.opacity = (enLazo ? (0.06 + 0.16 * ref) * eo(u / 0.3) : 0).toFixed(3);
    this.halo.style.strokeWidth = (26 + 18 * ref).toFixed(1);

    // flechas
    const ancho = 8 * (1 + 0.6 * ref);
    this.flechas.forEach((f, j) => {
      const p = f.cierre ? (u <= 0 ? 0 : clamp((angPulso - f.a0) / (f.a1 - f.a0))) : eo((t - s(j)) / 0.55);
      f.pista.style.opacity = (fant * (1 - p)).toFixed(3);
      f.pista.style.strokeDashoffset = (-t * 22).toFixed(1);
      const color = f.cierre ? 'var(--acento)'
        : `color-mix(in srgb, var(--acento) ${(70 * ref).toFixed(1)}%, var(--ink))`;
      f.linea.style.stroke = color;
      f.linea.style.strokeWidth = (f.cierre ? ancho * 1.5 : ancho).toFixed(2);
      f.linea.style.strokeDashoffset = (f.largo * (1 - p)).toFixed(1);
      f.linea.style.opacity = p > 0 ? 1 : 0;
      f.punta.style.fill = color;
      f.punta.style.opacity = clamp((p - 0.85) / 0.15).toFixed(3);
      const e = ((f.cierre ? 1.25 : 0.9) + 0.2 * ref).toFixed(3);
      f.punta.setAttribute('transform', `translate(${f.punta.dataset.x} ${f.punta.dataset.y}) rotate(${f.punta.dataset.r}) scale(${e})`);
    });

    // pulso
    this.estela.forEach((c, k) => {
      const [x, y] = this.pt(angPulso - 0.07 * k);
      c.setAttribute('cx', x.toFixed(1)); c.setAttribute('cy', y.toFixed(1));
      c.style.opacity = (enLazo ? eo(u / 0.15) * (1 - k / 6) * (0.8 + 0.2 * ref) : 0).toFixed(3);
    });

    // nodos
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.nodos.forEach((el, i) => {
      const on = eo((t - s(i)) / 0.45);
      let d = (angPulso - this.ang[i]) % (2 * Math.PI);
      if (d < 0) d += 2 * Math.PI;
      if (d > Math.PI) d -= 2 * Math.PI;
      const cerca = enLazo ? Math.max(0, 1 - Math.abs(d) / 0.45) * eo(u / 0.15) : 0;
      const respira = enLazo
        ? 0.012 * Math.sin(2 * Math.PI * (t / 2.6 + i / n))
        : (i === activo ? 0.022 * Math.sin(2 * Math.PI * (t - s(i)) / 2.4) * on : 0);
      const esc = 0.95 + 0.05 * on + respira + 0.035 * cerca;
      el.style.transform = `scale(${esc.toFixed(4)})`;
      // relleno de acento (0–1) solo para el paso que suena; el último lo conserva un momento ya en el lazo y se apaga
      // rápido (sin medios tonos largos). En el lazo, el nodo que toca el pulso se marca con borde y texto en acento.
      const lleno = enLazo ? (i === n - 1 ? 1 - eo((u - 0.35) / 0.12) : 0) : (i === activo ? on : 0);
      const marca = Math.max(lleno, cerca);
      el.style.opacity = (enLazo ? 0.55 + 0.45 * marca : Math.max(0.35 * fant, on * (i < activo ? 0.5 : 1))).toFixed(3);
      el.style.background = `color-mix(in srgb, var(--acento) ${(100 * lleno).toFixed(1)}%, var(--bg))`;
      el.style.color = lleno > 0.5 ? 'var(--tinta-acento, var(--bg))'
        : `color-mix(in srgb, var(--acento) ${(100 * cerca).toFixed(1)}%, var(--ink))`;
      const tenue = enLazo ? 45 + 30 * ref : 30 + 45 * on;
      el.style.borderColor = `color-mix(in srgb, var(--acento) ${(100 * marca).toFixed(1)}%, ` +
        `color-mix(in srgb, var(--ink) ${tenue.toFixed(1)}%, transparent))`;
    });
  },
});
