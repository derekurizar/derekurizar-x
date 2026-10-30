// Animación «dos-fracciones» (mecanismo «proporcion»): dos divisiones lado a lado con el mismo medidor. Izquierda:
// muchos puntos arriba sobre una franja muy larga de figuras; derecha: menos puntos sobre una franja corta. Cuando
// los medidores suben, el de la izquierda apenas sube (su denominador es enorme) y el de la derecha sube más y queda
// por encima: cada punto de la derecha «pesa más» (se hincha). Una línea punteada lleva el nivel de la izquierda al
// medidor de la derecha para que se vea que lo pasa. Con 2–6 pasos se reparten las fases: puntos → franjas → medidor
// izquierdo → medidor derecho → comparación. Sin cifras propias. seek puro.
// Estilo Noche: todo en crema; el acento es UNA cosa a la vez: los puntos mientras la voz los nombra y, al final, el
// medidor de la derecha (la idea de la escena).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }
ANIM.registrar('dos-fracciones', {
  meta: {
    descripcion: 'dos fracciones lado a lado: más casos sobre una base mucho mayor dan una tasa menor; menos casos sobre una base chica la superan',
    mecanismo: 'proporcion',
    temas: ['tasa', 'proporción', 'denominador', 'per cápita', 'ranking', 'comparación', 'población', 'nacimientos'],
    pasos: [2, 6],
    ejemplo: {
      titulo: 'Por qué cambia el orden',
      pasos: ['Arriba, los casos', 'Abajo, la población', 'Cada caso pesa más'],
    },
  },

  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, A = ctx.ancho, H = ctx.alto;
    this.V = V; this.n = n;
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', A); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    lienzo.appendChild(svg);
    const el = (tag, at, padre) => {
      const e = document.createElementNS(NS, tag);
      Object.keys(at).forEach((k) => e.setAttribute(k, at[k]));
      (padre || svg).appendChild(e);
      return e;
    };

    // --- datos de la forma (fijos, sin cifras visibles)
    const COLS = 4;
    const LADOS = [
      { num: 8, den: 36 }, // izquierda: muchos casos, base muy larga
      { num: 4, den: 8 },  // derecha: menos casos, base corta
    ];
    this.ESCALA = 0.6; // tope del medidor (proporción)
    this.COLS = COLS;

    // --- geometría
    const fsL = ctx.F45 ? 38 : 40, filaH = ctx.F45 ? 52 : 58;
    const rotH = n * filaH, sep = ctx.F45 ? 22 : 34;
    const gut = ctx.F45 ? 64 : 40, mw = ctx.F45 ? 70 : 62, mg = 16;
    const colW = (A - gut) / 2, fw = colW - mw - mg;
    this.mw = mw;
    const dispH = H - rotH - sep;
    const RN = 0.82, RD = 0.92, BAR = 0.35;
    const filasN = 2, filasD = 9;
    const unid = filasN * RN + 2 * BAR + filasD * RD + 0.1;
    const c = Math.min(fw / COLS, dispH / unid);
    this.c = c;
    const hT = unid * c, y0 = Math.max(0, (dispH - hT) / 2);
    const yBar = y0 + filasN * RN * c + BAR * c;
    const yBot = yBar + BAR * c + filasD * RD * c;
    this.yBar = yBar;

    this.lados = LADOS.map((L, s) => {
      const xs = s * (colW + gut);
      const x0 = xs + (fw - COLS * c) / 2;
      const lado = { prop: L.num / L.den, puntos: [], figs: [] };
      // numerador: puntos (filas pegadas a la raya)
      for (let i = 0; i < L.num; i++) {
        const fila = Math.floor(i / COLS), k = i % COLS;
        const enFila = Math.min(COLS, L.num - fila * COLS);
        const xa = x0 + ((COLS - enFila) / 2 + k + 0.5) * c;
        const ya = yBar - BAR * c - (fila + 0.5) * RN * c;
        const d = el('circle', { cx: 0, cy: 0, r: (0.27 * c).toFixed(1), fill: 'var(--ink)' });
        lado.puntos.push({ e: d, x: xa, y: ya, i });
      }
      // raya
      lado.bar = { x1: x0 + 0.1 * c, x2: x0 + (COLS - 0.1) * c };
      lado.raya = el('line', { y1: yBar.toFixed(1), y2: yBar.toFixed(1), stroke: 'var(--ink)',
        'stroke-width': Math.max(9, 0.16 * c).toFixed(1), 'stroke-linecap': 'round' });
      // denominador: figuras (cabeza + cuerpo), fila por fila hacia abajo
      for (let i = 0; i < L.den; i++) {
        const fila = Math.floor(i / COLS), k = i % COLS;
        const g = el('g', {});
        el('circle', { cx: 0, cy: (-0.25 * c).toFixed(1), r: (0.18 * c).toFixed(1), fill: 'var(--ink)' }, g);
        el('rect', { x: (-0.27 * c).toFixed(1), y: (-0.04 * c).toFixed(1), width: (0.54 * c).toFixed(1),
          height: (0.42 * c).toFixed(1), rx: (0.2 * c).toFixed(1), fill: 'var(--ink)' }, g);
        lado.figs.push({ g, x: x0 + (k + 0.5) * c, y: yBar + BAR * c + (fila + 0.55) * RD * c, fila, i });
      }
      // medidor (misma escala en los dos lados)
      const mx = xs + fw + mg;
      lado.med = { x: mx, top: y0, bot: yBot, h: yBot - y0 };
      el('rect', { x: mx, y: y0.toFixed(1), width: mw, height: (yBot - y0).toFixed(1), rx: 14,
        fill: 'color-mix(in srgb, var(--ink) 6%, transparent)',
        stroke: 'color-mix(in srgb, var(--ink) 42%, transparent)', 'stroke-width': 5 });
      lado.lleno = el('rect', { x: mx + 7, width: mw - 14, rx: 8,
        fill: s === 0 ? 'color-mix(in srgb, var(--ink) 62%, transparent)' : 'var(--acento)' });
      return lado;
    });

    // línea punteada: el nivel de la izquierda llevado hasta el medidor de la derecha
    const Li = this.lados[0], Ri = this.lados[1];
    this.yNivelL = Li.med.bot - 7 - (Li.med.h - 14) * (Li.prop / this.ESCALA);
    this.guia = el('line', { x1: (Li.med.x + mw + 6).toFixed(1), x2: (Ri.med.x + mw + 12).toFixed(1),
      y1: this.yNivelL.toFixed(1), y2: this.yNivelL.toFixed(1),
      stroke: 'color-mix(in srgb, var(--ink) 70%, transparent)', 'stroke-width': 5, 'stroke-dasharray': '10 9',
      'stroke-linecap': 'round' });

    // --- rótulos de los pasos (abajo)
    const yR = H - rotH;
    this.rotulos = P.pasos.map((txt, i) => {
      const fila = document.createElement('div');
      fila.style.cssText = `position:absolute;left:0;right:0;top:${(yR + i * filaH).toFixed(1)}px;height:${filaH}px;` +
        'display:flex;align-items:center;gap:20px';
      const marca = document.createElement('div');
      marca.style.cssText = 'width:10px;height:38px;border-radius:5px;flex:none';
      const tx = document.createElement('div');
      tx.style.cssText = `font:800 ${fsL}px/1.05 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);white-space:nowrap;` +
        'overflow:hidden;text-overflow:ellipsis;min-width:0;transform-origin:0 50%';
      tx.textContent = txt;
      fila.appendChild(marca); fila.appendChild(tx);
      lienzo.appendChild(fila);
      return { fila, marca, tx };
    });
  },

  seek(t, T) {
    const { clamp, eo } = this.V, c = this.c, ps = T.pasos, n = ps.length;
    const st = (i) => ps[Math.min(i, n - 1)].start;
    const du = (i) => (i + 1 < n ? ps[i + 1].start : T.fin) - st(i);
    const en = (i, fr) => st(i) + Math.min(2.4, Math.max(0, fr * du(i)));
    let F;
    if (n === 2) F = { pts: st(0), dL: en(0, 0.45), dR: en(0, 0.45), mL: st(1), mR: st(1) + 0.7 };
    else if (n === 3) F = { pts: st(0), dL: st(1), dR: st(1) + 0.5, mL: st(2), mR: st(2) + 0.7 };
    else if (n === 4) F = { pts: st(0), dL: st(1), dR: st(1) + 0.5, mL: st(2), mR: st(3) };
    else F = { pts: st(0), dL: st(1), dR: st(2), mL: st(3), mR: st(4) };
    F.cmp = n === 6 ? Math.max(st(5), F.mR + 1.2) : F.mR + 1.5;
    const insinua = 0.14 * eo((t - T.ini) / 0.5);
    const acPts = 1 - eo((t - F.dL) / 0.6); // los puntos llevan el acento mientras la voz los nombra
    const colPts = `color-mix(in srgb, var(--acento) ${Math.round(100 * acPts)}%, var(--ink))`;

    this.lados.forEach((L, s) => {
      const tD = s === 0 ? F.dL : F.dR, tM = s === 0 ? F.mL : F.mR;
      // puntos: entran escalonados, respiran; los de la derecha se hinchan cuando sube su medidor
      const pesa = s === 1 ? eo((t - F.mR) / 0.6) : 0;
      L.puntos.forEach((p) => {
        const entra = eo((t - F.pts - s * 0.35 - (p.i / L.puntos.length) * 0.6) / 0.4);
        const resp = 1 + 0.05 * Math.sin(t * 2.2 + p.i * 0.9 + s);
        const esc = (0.7 + 0.3 * entra) * resp * (1 + 0.38 * pesa);
        p.e.setAttribute('transform', `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) scale(${esc.toFixed(4)})`);
        p.e.setAttribute('fill', colPts);
        p.e.style.opacity = Math.max(insinua, entra).toFixed(3);
      });
      // raya
      const r = Math.max(0.12, eo((t - F.pts - 0.3) / 0.5)), mid = (L.bar.x1 + L.bar.x2) / 2,
        half = (L.bar.x2 - L.bar.x1) / 2;
      L.raya.setAttribute('x1', (mid - half * r).toFixed(1));
      L.raya.setAttribute('x2', (mid + half * r).toFixed(1));
      L.raya.style.opacity = Math.max(insinua * 1.5, eo((t - F.pts - 0.3) / 0.5)).toFixed(3);
      // figuras: la franja se desenrolla hacia abajo, fila por fila
      const atenua = 0.42 * eo((t - F.mL) / 0.6);
      L.figs.forEach((f) => {
        const entra = eo((t - tD - f.fila * 0.2 - (f.i % 4) * 0.04) / 0.4);
        const resp = 1 + 0.03 * Math.sin(t * 1.7 + f.i * 0.61);
        const esc = (0.8 + 0.2 * entra) * resp;
        const dy = (1 - entra) * -0.3 * c;
        f.g.setAttribute('transform', `translate(${f.x.toFixed(1)} ${(f.y + dy).toFixed(1)}) scale(${esc.toFixed(4)})`);
        f.g.style.opacity = Math.max(insinua * 0.8, entra * (1 - atenua)).toFixed(3);
      });
      // medidor
      const m = L.med, sube = eo((t - tM) / 1.5);
      let nivel = (L.prop / this.ESCALA) * sube;
      nivel += 0.006 * Math.sin(t * 2.4 + s * 1.3) * sube; // superficie viva
      const y = m.bot - 7 - (m.h - 14) * clamp(nivel);
      L.lleno.setAttribute('y', y.toFixed(1));
      L.lleno.setAttribute('height', Math.max(0, m.bot - 7 - y).toFixed(1));
      L.lleno.style.opacity = sube > 0.001 ? '1' : '0';
    });

    // guía punteada: aparece cuando ya subieron los dos y late despacio
    const g = eo((t - F.cmp) / 0.5);
    this.guia.style.opacity = (g * (0.75 + 0.25 * Math.sin((t - F.cmp) * 2.6))).toFixed(3);
    const Li = this.lados[0], Ri = this.lados[1];
    const xa = Li.med.x + this.mw + 6, xb = Ri.med.x + this.mw + 12;
    this.guia.setAttribute('x2', (xa + (xb - xa) * g).toFixed(1));

    // rótulos
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    this.rotulos.forEach((ro, i) => {
      const entra = eo((t - ps[i].start) / 0.45), fant = 0.28 * eo((t - T.ini) / 0.5);
      const on = i === activo;
      ro.fila.style.opacity = Math.max(fant, entra * (on ? 1 : 0.5)).toFixed(3);
      ro.tx.style.fontWeight = on ? '800' : '600';
      ro.tx.style.transform = `translateX(${((1 - entra) * -24).toFixed(1)}px)`;
      ro.marca.style.background = on ? 'var(--ink)' : 'color-mix(in srgb, var(--ink) 35%, transparent)';
    });
  },
});
