// Animación «tanque-balance» (semilla de la biblioteca, mecanismo balance): un tanque con un tubo de entrada arriba a
// la izquierda y uno de salida abajo a la derecha. Por los tubos corre un flujo de partículas continuo y la superficie
// del líquido ondula. Fases repartidas entre los pasos, cada una cuando la voz la dice:
//   entrada  (paso 0)        se abre la entrada, cae el chorro y el nivel sube un poco
//   salida   (paso 1)        el tubo de salida se ensancha y lleva más partículas que la entrada
//   baja     (paso 2 si n≥4) el nivel baja de forma continua mientras la voz sigue
//   final    (último paso)   el tanque queda bajo, la marca del nivel de antes tenue arriba, el líquido en acento
// Con 2–3 pasos las fases se juntan (la bajada empieza con la salida). Los pasos se leen abajo como lista, el activo
// destacado. Todo es función de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
ANIM.registrar('tanque-balance', {
  meta: {
    descripcion: 'tanque con entrada y salida: cuando sale más de lo que entra el nivel baja (o sube si es al revés)',
    mecanismo: 'balance',
    temas: ['agua', 'lago', 'nivel', 'presupuesto', 'deuda', 'reservas', 'balance', 'entradas y salidas'],
    pasos: [2, 6],
    ejemplo: { titulo: '¿Por qué baja el lago?', pasos: ['Entra el agua de lluvia', 'Sale más de la que entra', 'El nivel baja', 'El lago se encoge'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length;
    this.V = V;
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tag, attrs, padre) => {
      const e = document.createElementNS(NS, tag);
      Object.keys(attrs).forEach((k) => e.setAttribute(k, attrs[k]));
      padre.appendChild(e);
      return e;
    };
    const TINTE = 'color-mix(in srgb, var(--a1) 35%, var(--bg))';

    // --- lista de pasos (abajo): se mide primero para saber cuánto alto le queda al tanque ---
    const lista = document.createElement('div');
    lista.style.cssText = 'position:absolute;left:0;right:0;bottom:0;display:flex;flex-direction:column;gap:12px';
    lienzo.appendChild(lista);
    this.filas = P.pasos.map((txt) => {
      const fila = document.createElement('div');
      fila.style.cssText = 'display:flex;align-items:center;gap:20px;transform-origin:0 50%';
      const punto = document.createElement('i');
      punto.style.cssText = 'flex:none;width:18px;height:18px;border-radius:50%;border:5px solid var(--ink);box-sizing:content-box';
      const texto = document.createElement('span');
      texto.style.cssText = 'font-family:Archivo,sans-serif;font-weight:700;line-height:1.12;color:var(--ink)';
      texto.textContent = txt;
      fila.appendChild(punto); fila.appendChild(texto);
      lista.appendChild(fila);
      return { fila, punto, texto };
    });
    let fs = ctx.F45 ? 42 : 46;
    const tope = H * (ctx.F45 ? 0.42 : 0.40);
    const ajustar = () => this.filas.forEach((f) => { f.texto.style.fontSize = fs + 'px'; });
    ajustar();
    while (lista.offsetHeight > tope && fs > 36) { fs -= 2; ajustar(); }
    const Ht = H - lista.offsetHeight - (ctx.F45 ? 26 : 34);

    // --- geometría del tanque ---
    const svg = el('svg', { width: W, height: Ht }, lienzo);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:hidden';
    const muro = 7;
    const yIn = 34, wIn = 28;
    const tankW = Math.min(W * (ctx.F45 ? 0.46 : 0.5), Ht * 0.95);
    const tankL = Math.round((W - tankW) / 2 - 8), tankR = Math.round(tankL + tankW);
    const tankTop = yIn + 74, tankBot = Ht - 10;
    const iL = tankL + muro / 2, iR = tankR - muro / 2, iB = tankBot - muro / 2;
    const Hin = iB - tankTop;
    const xm = Math.round(tankL + tankW * 0.26), yM = yIn + 46;
    const wN = 22, wW = Math.round(Math.min(58, Hin * 0.13));
    const yOut = Math.round(iB - wW / 2 - 12);
    Object.assign(this, { W, Ht, yIn, xm, yM, iL, iR, iB, Hin, tankR, wN, wW, yOut });

    // líquido: dos capas (a1 y acento) que se funden al final
    this.liq = el('path', { fill: 'var(--a1)' }, svg);
    this.liqF = el('path', { fill: 'var(--acento)', opacity: 0 }, svg);
    // marca del nivel de antes (tenue, punteada)
    this.marca = el('line', { x1: iL + 4, x2: iR - 4, y1: 0, y2: 0, stroke: 'var(--ink)', 'stroke-width': 5,
      'stroke-dasharray': '16 12', opacity: 0 }, svg);
    // tanque abierto arriba (U de trazo grueso)
    el('path', { d: `M${tankL} ${tankTop - 18} L${tankL} ${tankBot} L${tankR} ${tankBot} L${tankR} ${tankTop - 18}`,
      fill: 'none', stroke: 'var(--ink)', 'stroke-width': muro, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);

    // chorro de entrada (banda translúcida del tubo a la superficie)
    this.chorro = el('rect', { x: xm - 10, width: 20, y: yM, height: 10, fill: TINTE, opacity: 0 }, svg);
    // tubo de entrada: codo desde la izquierda que baja sobre el tanque
    const codo = `M0 ${yIn} L${xm} ${yIn} L${xm} ${yM}`;
    el('path', { d: codo, fill: 'none', stroke: 'var(--ink)', 'stroke-width': wIn + 12, 'stroke-linejoin': 'miter' }, svg);
    this.tuboIn = el('path', { d: codo, fill: 'none', stroke: 'var(--bg)', 'stroke-width': wIn, 'stroke-linejoin': 'miter' }, svg);
    // tubo de salida: horizontal desde la pared derecha hasta el borde
    const recto = `M${tankR - muro} ${yOut} L${W} ${yOut}`;
    this.tuboOutA = el('path', { d: recto, fill: 'none', stroke: 'var(--ink)', 'stroke-width': wN + 12 }, svg);
    this.tuboOutB = el('path', { d: recto, fill: 'none', stroke: TINTE, 'stroke-width': wN }, svg);

    // partículas
    this.pIn = Array.from({ length: 12 }, () => el('circle', { r: 7, fill: 'var(--a2)', opacity: 0 }, svg));
    this.pOut = [-1, 0, 1].map(() => Array.from({ length: 6 }, () => el('circle', { r: 8, fill: 'var(--a2)', opacity: 0 }, svg)));

    // rótulos cortos junto a los tubos
    const rotulo = (txt, css) => {
      const d = document.createElement('div');
      d.style.cssText = "position:absolute;font:500 36px/1 'JetBrains Mono',monospace;color:var(--ink);white-space:nowrap;opacity:0;" + css;
      d.textContent = txt;
      lienzo.appendChild(d);
      return d;
    };
    this.rIn = rotulo('entra', `left:6px;top:${yIn + 32}px`);
    this.rOut = rotulo('sale', `left:${tankR + 22}px;top:${yOut - wW / 2 - 56}px`);
    this.rAntes = rotulo('antes', `right:${W - tankL + 16}px;top:0px`);
    this.rAntes.style.color = 'color-mix(in srgb, var(--ink) 70%, transparent)';
  },

  // nivel (fracción de la altura interior) en el segundo t
  nivel(t, T) {
    const { clamp } = this.V, ps = T.pasos, n = ps.length;
    const io = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };
    const tA = ps[0].start, tB = ps[this.f.b].start, tC = ps[this.f.c].start, tD = ps[this.f.d].start;
    const L0 = 0.5, L1 = 0.66, Lb = this.f.c > this.f.b ? 0.63 : L1, Lm = 0.33, Lf = 0.26;
    const fin = Math.max(T.fin, tD + 0.5);
    if (t < tA) return L0;
    if (t < tB) return L0 + (L1 - L0) * io((t - tA) / Math.max(0.6, tB - tA));
    if (t < tC) return L1 + (Lb - L1) * clamp((t - tB) / Math.max(0.6, tC - tB));
    if (this.f.d > this.f.c) {
      if (t < tD) return Lb + (Lm - Lb) * clamp((t - tC) / Math.max(0.6, tD - tC));
      return Lm + (Lf - Lm) * this.V.eo((t - tD) / Math.max(0.8, fin - tD));
    }
    return Lb + (Lf - Lb) * io((t - tC) / Math.max(1, fin - tC));
  },

  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = ps.length;
    const frac = (x) => x - Math.floor(x);
    // reparto de fases: entrada = 0, salida = 1, baja = 2 (si n ≥ 4) o 1, final = último
    this.f = { b: Math.min(1, n - 1), c: n >= 4 ? 2 : Math.min(1, n - 1), d: n - 1 };
    const tA = ps[0].start, tB = ps[this.f.b].start, tD = ps[this.f.d].start;
    const abre = eo((t - tA) / 0.6), ancho = n > 1 ? eo((t - tB) / 0.6) : 0, final = eo((t - tD) / 0.8);
    const { W, xm, yM, yIn, iL, iR, iB, Hin, tankR, wN, wW, yOut } = this;

    // superficie ondulada
    const L = this.nivel(t, T), ySup = iB - L * Hin;
    const ola = (x) => ySup + 5 * Math.sin(x / 26 + t * 2.4) + 2.5 * Math.sin(x / 11 - t * 1.7);
    let d = `M${iL.toFixed(1)} ${ola(iL).toFixed(1)}`;
    for (let x = iL + 16; x < iR; x += 16) d += ` L${x.toFixed(1)} ${ola(x).toFixed(1)}`;
    d += ` L${iR.toFixed(1)} ${ola(iR).toFixed(1)} L${iR.toFixed(1)} ${iB.toFixed(1)} L${iL.toFixed(1)} ${iB.toFixed(1)} Z`;
    this.liq.setAttribute('d', d);
    this.liqF.setAttribute('d', d);
    this.liq.setAttribute('opacity', (1 - final).toFixed(3));
    this.liqF.setAttribute('opacity', final.toFixed(3));

    // marca del nivel de antes
    const yMarca = iB - 0.66 * Hin;
    this.marca.setAttribute('y1', yMarca.toFixed(1)); this.marca.setAttribute('y2', yMarca.toFixed(1));
    this.marca.setAttribute('opacity', (0.4 * final).toFixed(3));
    this.rAntes.style.top = (yMarca - 18).toFixed(1) + 'px';
    this.rAntes.style.opacity = final.toFixed(3);

    // entrada: tubo lleno, chorro y partículas
    this.tuboIn.setAttribute('stroke', abre > 0.01 ? 'color-mix(in srgb, var(--a1) 35%, var(--bg))' : 'var(--bg)');
    const yS = ola(xm);
    this.chorro.setAttribute('height', Math.max(0, yS - yM).toFixed(1));
    this.chorro.setAttribute('opacity', (0.9 * abre).toFixed(3));
    const N = this.pIn.length;
    this.pIn.forEach((c, i) => {
      const s = frac(t * 0.42 + i / N);
      let x, y;
      if (s < 0.55) { x = 8 + (xm - 8) * (s / 0.55); y = yIn; }
      else if (s < 0.62) { x = xm; y = yIn + (yM - yIn) * ((s - 0.55) / 0.07); }
      else { x = xm + ((i * 37) % 7) - 3; y = yM + (yS - 8 - yM) * ((s - 0.62) / 0.38); }
      c.setAttribute('cx', x.toFixed(1)); c.setAttribute('cy', y.toFixed(1));
      c.setAttribute('opacity', (abre * Math.min(1, s / 0.05, (1 - s) / 0.05)).toFixed(3));
    });
    this.rIn.style.opacity = abre.toFixed(3);

    // salida: el tubo se ensancha y corre más rápido con más filas de partículas
    const w = wN + (wW - wN) * ancho;
    this.tuboOutA.setAttribute('stroke-width', (w + 12).toFixed(1));
    this.tuboOutB.setAttribute('stroke-width', w.toFixed(1));
    const fase = 0.32 * (t - tA) + 0.38 * Math.max(0, t - tB - 0.3);
    const x0 = tankR - 44, x1 = W - 10;
    this.pOut.forEach((fila, r) => {
      const off = (r - 1) * Math.max(0, w / 2 - 11);
      const vis = r === 1 ? abre : ancho;
      fila.forEach((c, i) => {
        const s = frac(fase + i / fila.length + r * 0.31);
        c.setAttribute('cx', (x0 + (x1 - x0) * s).toFixed(1));
        c.setAttribute('cy', (yOut + off).toFixed(1));
        c.setAttribute('opacity', (vis * Math.min(1, s / 0.08, (1 - s) / 0.08)).toFixed(3));
      });
    });
    this.rOut.style.opacity = ancho.toFixed(3);

    // lista de pasos: tenue antes de su turno, destacado el activo, atenuado lo ya dicho
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.filas.forEach((f, i) => {
      const entra = eo((t - ps[i].start) / 0.45), fantasma = 0.22 * eo((t - T.ini) / 0.5);
      const op = Math.max(fantasma, entra * (i < activo ? 0.5 : 1));
      f.fila.style.opacity = op.toFixed(3);
      const late = i === activo ? 0.03 * Math.sin(t * 3) : 0;
      f.fila.style.transform = `translateX(${((1 - entra) * -24).toFixed(1)}px) scale(${(1 + late).toFixed(4)})`;
      f.punto.style.background = i === activo ? 'var(--acento)' : (i < activo ? 'var(--ink)' : 'transparent');
      f.punto.style.borderColor = i === activo ? 'var(--acento)' : 'var(--ink)';
    });
  },
});
