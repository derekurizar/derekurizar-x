// Animación «margen-banco» (mecanismo balance): cómo gana un intermediario con lo que pasa por él. Arriba quien
// deposita, al centro el tanque del banco, abajo quien pide prestado. Paso 1: los depósitos bajan al tanque y lo
// llenan. Paso 2: el tanque los presta hacia abajo y se vacía. Paso 3: del préstamo sube un chorro GRUESO de interés
// que llena una capa nueva; hacia quien deposita sale uno DELGADO que le quita un poco. Paso 4: lo que queda de esa
// capa (la diferencia entre los dos chorros) se enciende en acento: la ganancia. Sirve para banco, cooperativa,
// prestamista, cualquier margen entre lo que se cobra y lo que se paga. Cámara quieta (A1), nada antes de la voz (A2);
// todo es función de t (seek puro).
ANIM.registrar('margen-banco', {
  meta: {
    descripcion: 'margen de un banco: los depósitos llenan el tanque, salen prestados, vuelve un chorro grueso de interés y sale uno delgado; queda la ganancia',
    mecanismo: 'balance',
    temas: ['banco', 'intereses', 'préstamos', 'ahorro', 'depósitos', 'ganancia', 'margen', 'cooperativa', 'crédito'],
    pasos: [4, 4],
    ejemplo: { titulo: '¿Cómo gana un banco?', pasos: ['Tus depósitos', 'Los presta', 'Más interés', 'La diferencia'],
      rotulos: { limite: 'Su ganancia' } },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, NS = 'http://www.w3.org/2000/svg', F45 = ctx.F45;
    this.V = V;
    const rot = P.rotulos || {};
    const cx = W / 2, xL = cx - 70, xR = cx + 70;
    const nodoH = F45 ? 76 : 88;
    const tTop = Math.round(H * 0.34), tBot = Math.round(H * 0.66), tW = 300, tX = cx - tW / 2;
    const inH = tBot - tTop - 16;   // alto interior del tanque
    this.g = { tTop, tBot, inH, tX, tW };
    const tenue = (p) => `color-mix(in srgb, var(--ink) ${p}%, transparent)`;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const el = (tag, at, padre) => {
      const e = document.createElementNS(NS, tag);
      for (const k in at) e.setAttribute(k, at[k]);
      (padre || svg).appendChild(e); return e;
    };
    // tanque: relleno (base = lo depositado, capa = el interés) dentro de un recorte, contorno encima
    const clip = el('clipPath', { id: 'mb-clip' });
    el('rect', { x: tX + 8, y: tTop + 8, width: tW - 16, height: inH, rx: 18 }, clip);
    const relleno = el('g', { 'clip-path': 'url(#mb-clip)' });
    this.base = el('rect', { x: tX + 8, width: tW - 16, y: tBot - 8, height: 0, fill: tenue(32) }, relleno);
    this.capa = el('rect', { x: tX + 8, width: tW - 16, y: tBot - 8, height: 0, fill: tenue(58) }, relleno);
    el('rect', { x: tX, y: tTop, width: tW, height: tBot - tTop, rx: 26, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 7 });
    // tubos: [x, y desde, y hasta, grosor]; se dibujan en el sentido del dinero, con su punta al final
    const tubo = (x, a, b, w) => {
      const dir = Math.sign(b - a), pl = Math.max(30, w * 1.5), bEnd = b - dir * pl;
      const linea = el('path', { d: `M${x} ${a} L${x} ${bEnd}`, fill: 'none', stroke: 'var(--ink)', 'stroke-width': w });
      const hw = Math.max(26, w * 1.25);
      const punta = el('path', { d: `M${x - hw} ${bEnd} L${x + hw} ${bEnd} L${x} ${b} Z`, fill: 'var(--ink)' });
      const L = Math.abs(bEnd - a);
      linea.style.strokeDasharray = L;
      return { linea, punta, L };
    };
    const yTu = nodoH + 10, yQuien = H - nodoH - 10;
    this.tubos = {
      deposito: tubo(xL, yTu, tTop - 8, 18),
      presta: tubo(xL, tBot + 8, yQuien, 18),
      grueso: tubo(xR, yQuien, tBot + 8, 34),
      delgado: tubo(xR, tTop - 8, yTu, 7),
    };
    lienzo.appendChild(svg);
    // textos (HTML para las fuentes de la casa)
    const caja = (css, txt, cls) => {
      const d = document.createElement('div');
      d.style.cssText = 'position:absolute;' + css;
      d.textContent = txt;
      lienzo.appendChild(d);
      return d;
    };
    const cond = 'font-weight:900;font-stretch:62.5%;text-transform:uppercase;';
    const nodo = (y, txt) => caja(`left:${cx - 170}px;width:340px;top:${y}px;height:${nodoH}px;box-sizing:border-box;` +
      `border:6px solid var(--ink);border-radius:${nodoH / 2}px;display:flex;align-items:center;justify-content:center;` +
      `font:900 ${F45 ? 46 : 52}px/1 Archivo,sans-serif;${cond}color:var(--ink);letter-spacing:.01em;`, txt);
    this.tu = nodo(0, rot.arriba || 'Tú');
    this.quien = nodo(H - nodoH, rot.abajo || 'Quien pide');
    this.banco = caja(`left:${tX}px;width:${tW}px;top:${tTop + 26}px;text-align:center;` +
      `font:600 ${F45 ? 30 : 32}px/1 'JetBrains Mono',monospace;color:var(--ink);opacity:.75;letter-spacing:.08em;`, rot.centro || 'BANCO');
    const F = F45 ? 38 : 40;
    const paso = `font:800 ${F}px/1.08 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);`;
    const izq = (y, txt) => caja(`right:${W - xL + 30}px;width:${xL - 40}px;top:${y}px;transform:translateY(-50%);text-align:right;${paso}`, txt);
    const der = (y, txt) => caja(`left:${xR + 32}px;width:${W - xR - 40}px;top:${y}px;transform:translateY(-50%);text-align:left;${paso}`, txt);
    const midArriba = (yTu + tTop) / 2, midAbajo = (tBot + yQuien) / 2;
    this.textos = [
      izq(midArriba, P.pasos[0]),
      izq(midAbajo, P.pasos[1]),
      der(midAbajo, P.pasos[2]),
    ];
    this.tuInteres = caja(`left:${xR + 32}px;width:${W - xR - 40}px;top:${midArriba}px;transform:translateY(-50%);` +
      `font:600 ${F45 ? 32 : 34}px/1.1 'JetBrains Mono',monospace;color:var(--ink);opacity:.8;`, rot.base_interes || 'Tu interés');
    // la diferencia: a la izquierda del tanque el paso, a la derecha el rótulo (los dos en acento: son la misma cosa)
    this.niveles = { lleno: 0.7, resto: 0.15, sube: 0.42, queda: 0.32 };
    const yCapa = tBot - 8 - inH * (this.niveles.resto + this.niveles.queda / 2);
    this.textos.push(caja(`right:${W - tX + 26}px;width:${tX - 30}px;top:${yCapa}px;transform:translateY(-50%);text-align:right;` +
      `${paso}color:var(--acento);`, P.pasos[3]));
    this.ganancia = caja(`left:${tX + tW + 26}px;width:${W - tX - tW - 30}px;top:${yCapa}px;transform:translateY(-50%);` +
      `font:900 ${F45 ? 46 : 50}px/0.95 Archivo,sans-serif;${cond}color:var(--acento);`, rot.limite || 'Su ganancia');
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, g = this.g, nv = this.niveles;
    const s = (i) => (ps[i] ? ps[i].start : 1e9);
    const p = (i, a, b) => eo(clamp((t - s(i) - a) / (b - a)));
    const op = (e, o) => { e.style.opacity = o.toFixed(3); e.style.visibility = o > 0.001 ? '' : 'hidden'; };
    // nodos
    op(this.tu, p(0, 0, 0.4)); op(this.quien, p(1, 0, 0.4));
    // tubos
    const dibuja = (tb, d) => {
      tb.linea.style.strokeDashoffset = (tb.L * (1 - d)).toFixed(1);
      op(tb.linea, d > 0 ? 1 : 0);
      op(tb.punta, clamp((d - 0.85) / 0.15));
    };
    dibuja(this.tubos.deposito, p(0, 0.1, 0.7));
    dibuja(this.tubos.presta, p(1, 0.1, 0.7));
    dibuja(this.tubos.grueso, p(2, 0, 0.6));
    dibuja(this.tubos.delgado, p(2, 0.7, 1.2));
    // niveles del tanque
    const base = nv.lleno * p(0, 0.5, 1.4) - (nv.lleno - nv.resto) * p(1, 0.4, 1.3);
    const capa = nv.sube * p(2, 0.4, 1.0) - (nv.sube - nv.queda) * p(2, 1.0, 1.5);
    const hb = g.inH * base, hc = g.inH * capa, fondo = g.tBot - 8;
    this.base.setAttribute('y', (fondo - hb).toFixed(1)); this.base.setAttribute('height', hb.toFixed(1));
    this.capa.setAttribute('y', (fondo - hb - hc).toFixed(1)); this.capa.setAttribute('height', hc.toFixed(1));
    const enc = p(3, 0, 0.5);
    this.capa.setAttribute('fill', enc > 0.5 ? 'var(--acento)' : 'color-mix(in srgb, var(--ink) 58%, transparent)');
    // textos: el que la voz dice, lleno; los ya dichos, atenuados
    this.textos.forEach((e, i) => {
      const entra = p(i, 0, 0.45), pasa = i < 3 ? p(i + 1, 0, 0.35) : 0;
      op(e, entra * (1 - 0.5 * pasa));
      e.style.marginTop = ((1 - entra) * 18).toFixed(1) + 'px';
    });
    op(this.tuInteres, 0.8 * p(2, 0.8, 1.2) * (1 - 0.4 * p(3, 0, 0.35)));
    op(this.ganancia, p(3, 0.1, 0.6));
    this.ganancia.style.marginTop = ((1 - p(3, 0.1, 0.6)) * 18).toFixed(1) + 'px';
  },
});
