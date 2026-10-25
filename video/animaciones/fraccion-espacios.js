// Animación «fraccion-espacios» (semilla de la biblioteca, mecanismo «proporcion»): una fracción grande. Arriba, el
// numerador: una cuadrícula apretada de figuras que respiran; una raya gruesa; abajo, el denominador: una fila de
// casillas vacías, muchas menos que las figuras. A la derecha, un medidor vertical con una marca tenue de «lleno».
// Fases, cada una cuando la voz dice su paso: (1) se arma la división y el medidor sube muy por encima de la marca;
// (2) las casillas quedan fijas: un marco con candado las encierra, intentan crecer y se frenan; (3) unas pocas figuras
// salen del numerador; (4) el medidor baja apenas y sigue muy por encima de la marca. Con 2–6 pasos se reparten esas
// fases (el primero arma la división, el último muestra el medidor casi igual). Sin cifras propias. seek puro.
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
ANIM.registrar('fraccion-espacios', {
  meta: {
    descripcion: 'una fracción: las figuras de arriba sobre los espacios de abajo; si el denominador no crece, quitar unas pocas casi no baja el medidor',
    mecanismo: 'proporcion',
    temas: ['ocupación', 'hacinamiento', 'tasa', 'proporción', 'denominador', 'cárceles', 'cupo'],
    pasos: [2, 6],
    ejemplo: {
      titulo: 'Por qué la ocupación no cede',
      pasos: ['Presos entre espacios', 'Los espacios no crecen', 'Salgan algunos presos', 'La ocupación apenas baja'],
    },
  },

  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, A = ctx.ancho, H = ctx.alto;
    this.V = V; this.n = n;
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tag, at, padre) => {
      const e = document.createElementNS(NS, tag);
      Object.keys(at).forEach((k) => e.setAttribute(k, at[k]));
      (padre || svg).appendChild(e);
      return e;
    };
    const COLS = 8, FILAS = 4, CAS = 6;
    this.SALEN = [7, 15, 6]; // índices de las figuras que salen (esquina superior derecha), en orden
    // --- geometría
    const fsL = ctx.F45 ? 38 : 40, filaH = ctx.F45 ? 52 : 58;
    const rotH = n * filaH, sep = ctx.F45 ? 22 : 34;
    const colW = 130, gapM = ctx.F45 ? 44 : 34;
    const fracW = A - colW - gapM, dispH = H - rotH - sep;
    const c = Math.min(fracW / COLS, dispH / 7.05);
    const rh = Math.min(1.25 * c, (dispH - 2.15 * c) / FILAS); // alto de fila del numerador
    this.c = c;
    const x0 = (fracW - COLS * c) / 2, y0 = Math.max(0, (dispH - (FILAS * rh + 2.05 * c)) / 2);
    const yNum = y0 + 0.45 * c;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', A); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    lienzo.appendChild(svg);

    // --- numerador: figuras (cabeza + cuerpo)
    this.figs = [];
    for (let f = 0; f < FILAS; f++) {
      for (let k = 0; k < COLS; k++) {
        const g = el('g', {});
        el('circle', { cx: 0, cy: (-0.22 * c).toFixed(1), r: (0.17 * c).toFixed(1), fill: 'var(--ink)' }, g);
        el('rect', { x: (-0.25 * c).toFixed(1), y: (-0.02 * c).toFixed(1), width: (0.5 * c).toFixed(1),
          height: (0.38 * c).toFixed(1), rx: (0.19 * c).toFixed(1), fill: 'var(--ink)' }, g);
        this.figs.push({ g, x: x0 + (k + 0.5) * c, y: yNum + (f + 0.55) * rh, i: f * COLS + k });
      }
    }

    // --- raya de fracción
    const yBar = yNum + FILAS * rh + 0.25 * c;
    this.bar = { x1: x0 + 0.15 * c, x2: x0 + (COLS - 0.15) * c, y: yBar };
    this.raya = el('line', { x1: this.bar.x1, x2: this.bar.x2, y1: yBar, y2: yBar, stroke: 'var(--ink)',
      'stroke-width': Math.max(10, 0.13 * c).toFixed(1), 'stroke-linecap': 'round' });

    // --- denominador: casillas vacías + marco con candado + casilla fantasma
    const b = 0.8 * c, yCas = yBar + 0.45 * c;
    const bx = x0 + (COLS * c - (CAS * c + 0.9 * c)) / 2;
    this.cas = { bx, y: yCas, b, n: CAS };
    this.casillas = [];
    for (let i = 0; i < CAS; i++) {
      this.casillas.push(el('rect', { x: (bx + i * c + 0.1 * c).toFixed(1), y: yCas.toFixed(1), width: b.toFixed(1),
        height: b.toFixed(1), rx: (0.1 * c).toFixed(1), fill: 'none',
        stroke: 'color-mix(in srgb, var(--ink) 75%, transparent)', 'stroke-width': 5 }));
    }
    this.fantasma = el('rect', { y: yCas.toFixed(1), height: b.toFixed(1), rx: (0.1 * c).toFixed(1), fill: 'none',
      stroke: 'color-mix(in srgb, var(--ink) 55%, transparent)', 'stroke-width': 5, 'stroke-dasharray': '10 8' });
    this.marco = el('rect', { x: (bx - 0.04 * c).toFixed(1), y: (yCas - 0.14 * c).toFixed(1),
      height: (b + 0.28 * c).toFixed(1), rx: (0.16 * c).toFixed(1), fill: 'none', stroke: 'var(--a1)',
      'stroke-width': 7 });
    this.marcoY = yCas + b / 2;
    // candado
    this.candado = el('g', {});
    const cw = 0.5 * c, ch = 0.4 * c;
    el('path', { d: `M ${(-0.15 * c).toFixed(1)} ${(-ch / 2 + 2).toFixed(1)} v ${(-0.1 * c).toFixed(1)} ` +
      `a ${(0.15 * c).toFixed(1)} ${(0.15 * c).toFixed(1)} 0 0 1 ${(0.3 * c).toFixed(1)} 0 v ${(0.1 * c).toFixed(1)}`,
      fill: 'none', stroke: 'var(--a1)', 'stroke-width': 6, 'stroke-linecap': 'round' }, this.candado);
    el('rect', { x: (-cw / 2).toFixed(1), y: (-ch / 2).toFixed(1), width: cw.toFixed(1), height: ch.toFixed(1),
      rx: (0.07 * c).toFixed(1), fill: 'var(--a1)' }, this.candado);
    el('circle', { cx: 0, cy: 0, r: (0.05 * c).toFixed(1), fill: 'var(--bg)' }, this.candado);

    // --- medidor vertical
    const mw = 110, mx = fracW + gapM + (colW - mw) / 2;
    const mTop = yNum - 0.1 * c, mBot = yCas + b;
    const mH = mBot - mTop;
    this.med = { x: mx, w: mw, top: mTop, bot: mBot, h: mH, marca: mBot - 0.3 * mH };
    el('rect', { x: mx, y: mTop.toFixed(1), width: mw, height: mH.toFixed(1), rx: 14,
      fill: 'color-mix(in srgb, var(--ink) 6%, transparent)',
      stroke: 'color-mix(in srgb, var(--ink) 40%, transparent)', 'stroke-width': 5 });
    this.bajo = el('rect', { x: mx + 7, width: mw - 14, rx: 8, fill: 'color-mix(in srgb, var(--ink) 62%, transparent)' });
    this.sobre = el('rect', { x: mx + 7, width: mw - 14, rx: 8, fill: 'var(--acento)' });
    this.previo = el('line', { x1: mx - 12, x2: mx + mw + 12, stroke: 'color-mix(in srgb, var(--ink) 55%, transparent)',
      'stroke-width': 5, 'stroke-dasharray': '8 7' });
    this.marcaL = el('line', { x1: mx - 16, x2: mx + mw + 16, y1: this.med.marca.toFixed(1), y2: this.med.marca.toFixed(1),
      stroke: 'color-mix(in srgb, var(--ink) 70%, transparent)', 'stroke-width': 6, 'stroke-linecap': 'round' });
    this.lleno = document.createElement('div');
    this.lleno.textContent = 'lleno';
    this.lleno.style.cssText = `position:absolute;left:${mx}px;width:${mw}px;top:${(this.med.marca + 8).toFixed(1)}px;` +
      "text-align:center;font:600 36px/1 Archivo,sans-serif;letter-spacing:-.01em";
    lienzo.appendChild(this.lleno);

    // --- rótulos de los pasos (abajo)
    const yR = H - rotH;
    this.rotulos = P.pasos.map((txt, i) => {
      const fila = document.createElement('div');
      fila.style.cssText = `position:absolute;left:0;right:0;top:${(yR + i * filaH).toFixed(1)}px;height:${filaH}px;` +
        'display:flex;align-items:center;gap:20px';
      const marca = document.createElement('div');
      marca.style.cssText = 'width:10px;height:38px;border-radius:5px;flex:none';
      const tx = document.createElement('div');
      tx.style.cssText = `font:600 ${fsL}px/1.05 Archivo,sans-serif;color:var(--ink);white-space:nowrap;` +
        'overflow:hidden;text-overflow:ellipsis;min-width:0;transform-origin:0 50%';
      tx.textContent = txt;
      fila.appendChild(marca); fila.appendChild(tx);
      lienzo.appendChild(fila);
      return { fila, marca, tx };
    });
  },

  seek(t, T) {
    const { clamp, eo } = this.V, c = this.c, ps = T.pasos;
    // momentos de cada fase según el número de pasos
    const F = (() => {
      const ps = T.pasos, n = ps.length;
      const st = (i) => ps[Math.min(i, n - 1)].start;
      const du = (i) => (i + 1 < n ? ps[i + 1].start : T.fin) - st(i);
      const en = (i, fr) => st(i) + Math.min(2.4, Math.max(0, fr * du(i)));
      const f = { armar: st(0) };
      if (n === 2) Object.assign(f, { sube: en(0, 0.12), fijar: en(0, 0.5), salA: en(1, 0), salB: null, medir: en(1, 0.5) });
      else if (n === 3) Object.assign(f, { sube: en(0, 0.15), fijar: en(1, 0), salA: en(2, 0), salB: null, medir: en(2, 0.5) });
      else if (n === 4) Object.assign(f, { sube: en(0, 0.15), fijar: en(1, 0), salA: en(2, 0), salB: null, medir: en(3, 0) });
      else if (n === 5) Object.assign(f, { sube: en(0, 0.15), fijar: en(1, 0), salA: en(2, 0), salB: en(3, 0), medir: en(4, 0) });
      else Object.assign(f, { sube: en(1, 0), fijar: en(2, 0), salA: en(3, 0), salB: en(4, 0), medir: en(5, 0) });
      return f;
    })();
    const insinua = 0.14 * eo((t - T.ini) / 0.5);

    // numerador: entran escalonadas, respiran; las de SALEN se van hacia afuera
    const salida = (i) => {
      const k = this.SALEN.indexOf(i);
      if (k < 0) return 0;
      const t0 = F.salB === null ? F.salA + k * 0.25 : (k < 2 ? F.salA + k * 0.25 : F.salB);
      return eo((t - t0) / 0.9);
    };
    this.figs.forEach((fg) => {
      const entra = eo((t - F.armar - (fg.i / this.figs.length) * 0.9) / 0.4);
      const resp = 1 + 0.035 * Math.sin(t * 2.1 + fg.i * 0.73);
      const s = salida(fg.i);
      const dx = s * 0.55 * c, dy = -s * 0.35 * c;
      const esc = (0.85 + 0.15 * entra) * resp * (1 - 0.35 * s);
      fg.g.setAttribute('transform', `translate(${(fg.x + dx).toFixed(1)} ${(fg.y + dy).toFixed(1)}) scale(${esc.toFixed(4)})`);
      fg.g.style.opacity = (Math.max(insinua, entra) * (1 - s)).toFixed(3);
    });

    // raya
    const r = eo((t - F.armar - 0.3) / 0.5), mid = (this.bar.x1 + this.bar.x2) / 2, half = (this.bar.x2 - this.bar.x1) / 2;
    const rr = Math.max(0.12, r);
    this.raya.setAttribute('x1', (mid - half * rr).toFixed(1));
    this.raya.setAttribute('x2', (mid + half * rr).toFixed(1));
    this.raya.style.opacity = Math.max(insinua * 1.5, r).toFixed(3);

    // casillas
    const ec = eo((t - F.armar - 0.5) / 0.5);
    this.casillas.forEach((q) => { q.style.opacity = Math.max(insinua * 1.5, ec).toFixed(3); });

    // marco + candado: aparece, intenta crecer y se frena
    const fm = eo((t - F.fijar) / 0.5);
    const bump = Math.sin(Math.PI * clamp((t - F.fijar - 0.6) / 1.4));
    const tiembla = Math.sin(Math.PI * clamp((t - F.fijar - 1.3) / 0.7)) * Math.sin((t - F.fijar) * 28);
    const ext = 0.45 * c * Math.max(0, bump);
    const ancho = this.cas.n * c + 0.08 * c + ext;
    this.marco.setAttribute('width', ancho.toFixed(1));
    this.marco.style.opacity = fm.toFixed(3);
    const xc = this.cas.bx - 0.04 * c + ancho + 0.38 * c;
    const sC = 0.6 + 0.4 * fm;
    this.candado.setAttribute('transform', `translate(${xc.toFixed(1)} ${this.marcoY.toFixed(1)}) ` +
      `rotate(${(tiembla * 9).toFixed(2)}) scale(${sC.toFixed(3)})`);
    this.candado.style.opacity = fm.toFixed(3);
    const xf = this.cas.bx + this.cas.n * c + 0.1 * c;
    this.fantasma.setAttribute('x', xf.toFixed(1));
    this.fantasma.setAttribute('width', Math.max(0.1, ext - 0.08 * c).toFixed(1));
    this.fantasma.style.opacity = (0.8 * Math.max(0, bump)).toFixed(3);

    // medidor
    const ALTO = 0.92, total = this.figs.length, salen = this.SALEN.length;
    const fin = ALTO * (total - salen) / total;
    const sube = eo((t - F.sube - 0.3) / 1.3), baja = eo((t - F.medir - 0.2) / 1.2);
    let nivel = ALTO * sube - (ALTO - fin) * baja;
    nivel += 0.006 * Math.sin(t * 2.4) * sube; // superficie viva
    const m = this.med, y = m.bot - 7 - (m.h - 14) * clamp(nivel);
    const yM = m.marca;
    const yBajo = Math.max(y, yM);
    this.bajo.setAttribute('y', yBajo.toFixed(1));
    this.bajo.setAttribute('height', Math.max(0, m.bot - 7 - yBajo).toFixed(1));
    this.sobre.setAttribute('y', y.toFixed(1));
    this.sobre.setAttribute('height', Math.max(0, yM - y).toFixed(1));
    this.sobre.style.opacity = y < yM ? 1 : 0;
    // la marca del nivel anterior queda tenue al bajar: se ve lo poco que bajó
    const yPrev = m.bot - 7 - (m.h - 14) * ALTO;
    this.previo.setAttribute('y1', yPrev.toFixed(1)); this.previo.setAttribute('y2', yPrev.toFixed(1));
    this.previo.style.opacity = (eo((t - F.medir) / 0.4)).toFixed(3);
    // la marca de lleno late cuando el medidor ya quedó casi igual
    const late = 0.5 + 0.5 * Math.sin((t - F.medir) * 3);
    this.marcaL.setAttribute('stroke-width', (6 + (t > F.medir + 1.4 ? 2 * late : 0)).toFixed(2));
    const cubierto = y < yM + 50;
    this.lleno.style.color = cubierto ? 'var(--bg)' : 'color-mix(in srgb, var(--ink) 60%, transparent)';
    this.lleno.style.opacity = Math.max(0.35, eo((t - T.ini) / 0.5)).toFixed(3);

    // rótulos
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.rotulos.forEach((ro, i) => {
      const entra = eo((t - ps[i].start) / 0.45), fant = 0.22 * eo((t - T.ini) / 0.5);
      const on = i === activo;
      ro.fila.style.opacity = Math.max(fant, entra * (on ? 1 : 0.5)).toFixed(3);
      ro.tx.style.fontWeight = on ? '700' : '500';
      ro.tx.style.transform = `translateX(${((1 - entra) * -24).toFixed(1)}px)`;
      ro.marca.style.background = on ? 'var(--acento)' : 'color-mix(in srgb, var(--ink) 35%, transparent)';
    });
  },
});
