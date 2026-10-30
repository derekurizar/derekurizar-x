// Animación «bola-nieve» (semilla de la biblioteca, mecanismo exponencial): crecer sobre lo acumulado. Doce columnas,
// una por periodo, apiladas en tres capas: el capital (igual en todas, crema tenue), el interés que da el capital (crece
// en línea recta, crema) y el interés sobre lo ya ganado (en ACENTO: al principio una raya y al final casi toda la
// columna). Una bola recorre las puntas de las columnas mientras crecen. Fases repartidas entre los pasos, cada una
// cuando la voz la dice:
//   base      (paso 0)            entran las columnas solo con el capital: todas iguales
//   lineal    (paso 1)            sube la capa del interés del capital, la misma en cada periodo (escalera recta)
//   compuesto (paso 2 si n ≥ 3)   sube la capa en acento, de izquierda a derecha: cada columna gana sobre la anterior
//   manda     (último paso)       el capital y la escalera recta bajan a media luz; la capa en acento late en la última
// Con 2 pasos: base + lineal juntos en el primero y compuesto + manda en el segundo. Los pasos se leen abajo como lista,
// el activo destacado. La forma es paramétrica (no dibuja las cifras del video: esas van en los pasos). Todo es función
// de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
ANIM.registrar('bola-nieve', {
  meta: {
    descripcion: 'columnas por periodo en tres capas: capital igual, interés en línea recta y el interés sobre lo ganado que engorda hasta mandar',
    mecanismo: 'exponencial',
    temas: ['interés compuesto', 'ahorro', 'deuda', 'crecimiento', 'exponencial', 'acumulación', 'bola de nieve', 'inflación'],
    pasos: [2, 6],
    ejemplo: { titulo: 'Cómo crece solo', pasos: ['El capital no cambia', 'El interés se suma', 'Lo sumado también gana', 'Al final manda el interés'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto;
    this.V = V;
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tag, attrs, padre) => {
      const e = document.createElementNS(NS, tag);
      Object.keys(attrs).forEach((k) => e.setAttribute(k, attrs[k]));
      padre.appendChild(e);
      return e;
    };
    // --- lista de pasos (abajo): se mide primero para saber cuánto alto le queda al gráfico ---
    const lista = document.createElement('div');
    lista.style.cssText = 'position:absolute;left:0;right:0;bottom:0;display:flex;flex-direction:column;gap:12px';
    lienzo.appendChild(lista);
    this.filas = P.pasos.map((txt) => {
      const fila = document.createElement('div');
      fila.style.cssText = 'display:flex;align-items:center;gap:20px;transform-origin:0 50%';
      const punto = document.createElement('i');
      punto.style.cssText = 'flex:none;width:18px;height:18px;border-radius:50%;border:5px solid var(--ink);box-sizing:content-box';
      const texto = document.createElement('span');
      texto.style.cssText = 'font-family:Archivo,sans-serif;font-weight:800;line-height:1.12;letter-spacing:-.01em;color:var(--ink)';
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
    const Hg = H - lista.offsetHeight - (ctx.F45 ? 30 : 40);

    // --- geometría: NC columnas; total(k) = (1 + r)^k, lineal(k) = 1 + r·k, capital = 1 ---
    const NC = 12, r = 0.2, gap = Math.round(W * 0.018);
    const ancho = (W - gap * (NC - 1)) / NC;
    const total = (k) => Math.pow(1 + r, k), lineal = (k) => 1 + r * k;
    // dos escalas: mientras solo hay capital y escalera recta, las columnas llenan el alto; cuando entra la capa en acento
    // la «cámara» se aleja hasta que cabe la última columna (el crecimiento empuja el marco)
    const arriba = 36, base = Hg - 6, escalaLin = 0.82 * (base - arriba) / lineal(NC - 1), escala = (base - arriba) / total(NC - 1);
    Object.assign(this, { NC, r, gap, ancho, total, lineal, base, escala, escalaLin, Hg });
    const svg = el('svg', { width: W, height: Hg }, lienzo);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    // eje
    el('line', { x1: 0, x2: W, y1: base + 3, y2: base + 3, stroke: 'color-mix(in srgb, var(--ink) 35%, transparent)', 'stroke-width': 4 }, svg);
    this.cols = Array.from({ length: NC }, (_, k) => {
      const x = k * (ancho + gap);
      const cap = el('rect', { x, width: ancho, y: base, height: 0, rx: 3, fill: 'color-mix(in srgb, var(--ink) 30%, transparent)' }, svg);
      const lin = el('rect', { x, width: ancho, y: base, height: 0, fill: 'var(--ink)' }, svg);
      const com = el('rect', { x, width: ancho, y: base, height: 0, rx: 3, fill: 'var(--acento)' }, svg);
      return { x, cap, lin, com };
    });
    // la bola que recorre las puntas
    this.bola = el('circle', { r: Math.max(10, ancho * 0.28), fill: 'var(--ink)', opacity: 0 }, svg);
    this.bola.style.display = 'none';
  },

  // fases: índices de paso de cada fase según cuántos pasos hay
  fases(n) {
    if (n <= 2) return { base: 0, lineal: 0, compuesto: n - 1, manda: n - 1 };
    if (n === 3) return { base: 0, lineal: 1, compuesto: 2, manda: 2 };
    return { base: 0, lineal: 1, compuesto: 2, manda: n - 1 };
  },

  seek(t, T) {
    const { eo } = this.V, ps = T.pasos, n = ps.length, F = this.fases(n);
    const tB = ps[F.base].start, tL = ps[F.lineal].start + (F.lineal === F.base ? 0.7 : 0), tC = ps[F.compuesto].start,
      tM = ps[F.manda].start + (F.manda === F.compuesto ? 1.6 : 0);
    const { NC, ancho, total, lineal, base } = this;
    // la capa compuesta crece de izquierda a derecha: cada columna empieza un poco después que la anterior
    const durC = Math.max(1.8, Math.min(4.5, tM - tC));
    const zoom = eo((t - tC) / durC), escala = this.escalaLin + (this.escala - this.escalaLin) * zoom;
    let punta = null;
    this.cols.forEach((c, k) => {
      const eb = eo((t - tB - 0.06 * k) / 0.5), el_ = eo((t - tL - 0.08 * k) / 0.6);
      const ec = eo((t - tC - (durC * 0.75) * k / (NC - 1)) / (durC * 0.4));
      const hCap = escala * eb, hLin = escala * (lineal(k) - 1) * el_;
      const hCom = escala * Math.max(0, total(k) - lineal(k)) * ec;
      c.cap.setAttribute('y', (base - hCap).toFixed(1)); c.cap.setAttribute('height', hCap.toFixed(1));
      c.lin.setAttribute('y', (base - hCap - hLin).toFixed(1)); c.lin.setAttribute('height', hLin.toFixed(1));
      c.com.setAttribute('y', (base - hCap - hLin - hCom).toFixed(1)); c.com.setAttribute('height', hCom.toFixed(1));
      // «manda»: el capital y la escalera recta a media luz; la última columna late
      const m = eo((t - tM) / 0.6);
      c.cap.setAttribute('opacity', (1 - 0.5 * m).toFixed(3));
      c.lin.setAttribute('opacity', (0.85 - 0.45 * m).toFixed(3));
      const late = k === NC - 1 ? 1 + 0.035 * m * Math.sin((t - tM) * 3.2) : 1;
      c.com.setAttribute('transform', late !== 1 ? `translate(${(c.x + ancho / 2).toFixed(1)} ${base}) scale(${late.toFixed(4)}) translate(${(-c.x - ancho / 2).toFixed(1)} ${-base})` : '');
      if (ec > 0.02 || el_ > 0.02) punta = { x: c.x + ancho / 2, y: base - hCap - hLin - hCom };
    });
    // la bola: aparece con la escalera y rueda hacia la última punta que ya creció, rebotando suave
    if (punta) {
      this.bola.style.display = '';
      const rb = parseFloat(this.bola.getAttribute('r'));
      this.bola.setAttribute('cx', punta.x.toFixed(1));
      this.bola.setAttribute('cy', (punta.y - rb - 6 - 5 * Math.abs(Math.sin(t * 4))).toFixed(1));
      this.bola.setAttribute('opacity', (0.9 * eo((t - tL) / 0.4)).toFixed(3));
    } else this.bola.style.display = 'none';

    // lista de pasos: tenue antes de su turno, destacado el activo, atenuado lo ya dicho
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.filas.forEach((f, i) => {
      const entra = eo((t - ps[i].start) / 0.45), fantasma = 0.28 * eo((t - T.ini) / 0.5);
      const op = Math.max(fantasma, entra * (i < activo ? 0.5 : 1));
      f.fila.style.opacity = op.toFixed(3);
      const latido = i === activo ? 0.03 * Math.sin(t * 3) : 0;
      f.fila.style.transform = `translateX(${((1 - entra) * -24).toFixed(1)}px) scale(${(1 + latido).toFixed(4)})`;
      f.punto.style.background = i === activo ? 'var(--ink)' : (i < activo ? 'color-mix(in srgb, var(--ink) 45%, transparent)' : 'transparent');
      f.punto.style.borderColor = 'var(--ink)';
    });
  },
});
