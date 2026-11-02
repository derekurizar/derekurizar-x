// Animación «plazo-vencido» de la escena explica (mecanismo umbral): arriba, un riel de tiempo con marcas de días y
// un cursor que avanza solo, al ritmo del reloj, hacia una línea límite (la fecha del primer paso); abajo, una bodega
// con cajas en pila. Mientras el cursor no llega, las cajas esperan en crema tenue con su cruz; cuando la voz dice el
// paso del cruce, el cursor pasa la línea y las cajas cambian de estado en una ola de izquierda a derecha: se llenan
// de acento y la cruz gira hasta ser una X. En el último paso se asientan y cae polvo sobre ellas: el tiempo sigue
// (el cursor sigue avanzando, cada vez más lento) y las cajas ya no. Estilo Noche: antes del cruce lo único en acento
// es la fecha límite; desde el cruce, solo las cajas vencidas. seek puro: todo es función de t.
ANIM.registrar('plazo-vencido', {
  meta: {
    descripcion: 'un cursor de tiempo avanza hasta una fecha límite; al cruzarla, las cajas guardadas cambian de estado a vencidas y se quedan',
    mecanismo: 'umbral',
    temas: ['caducidad', 'vencimiento', 'plazo', 'fecha límite', 'bodega', 'inventario', 'medicinas', 'vacunas', 'desperdicio'],
    pasos: [2, 5],
    ejemplo: {
      titulo: '¿Por qué se tiró la medicina?',
      pasos: ['Vence el 15 de marzo', 'Nadie la entregó a tiempo', 'Se quedó en la bodega'],
    },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, W = ctx.ancho, H = ctx.alto, n = P.pasos.length, F45 = ctx.F45;
    this.V = V; this.n = n;
    this.c = n >= 3 ? n - 2 : 1;                       // paso en que el cursor cruza la línea
    // ── fecha límite (paso 0) arriba, centrada sobre la línea y sin salirse del lienzo
    const xd = Math.round(W * 0.64);
    const chip = document.createElement('div');
    let fsChip = F45 ? 50 : 56;
    chip.style.cssText = `position:absolute;top:0;left:0;white-space:nowrap;font:900 ${fsChip}px/1 Archivo,sans-serif;` +
      'font-stretch:62.5%;text-transform:uppercase;letter-spacing:.01em;color:var(--acento);';
    chip.textContent = P.pasos[0];
    lienzo.appendChild(chip);
    let cw = chip.offsetWidth || P.pasos[0].length * fsChip * 0.42;
    while (cw > W - 8 && fsChip > 38) { fsChip -= 2; chip.style.fontSize = fsChip + 'px'; cw = chip.offsetWidth || cw * 0.95; }
    chip.style.left = Math.max(0, Math.min(W - cw, xd - cw / 2)).toFixed(1) + 'px';
    this.chip = chip;
    // ── lista de los demás pasos abajo
    const fs = F45 ? 38 : 44;
    const lista = document.createElement('div');
    lista.style.cssText = 'position:absolute;left:0;right:0;bottom:0;display:flex;flex-direction:column;gap:14px;';
    this.items = P.pasos.slice(1).map((txt) => {
      const el = document.createElement('div');
      el.style.cssText = `position:relative;padding-left:44px;font:800 ${fs}px/1.12 Archivo,sans-serif;letter-spacing:-.01em;` +
        'color:var(--ink);transform-origin:0 50%;';
      el.innerHTML = `<span style="position:absolute;left:0;top:calc(.56em - 11px);width:22px;height:22px;border-radius:4px;background:var(--ink)"></span>`;
      el.appendChild(document.createTextNode(txt));
      lista.appendChild(el);
      return { el };
    });
    lienzo.appendChild(lista);
    const listaH = lista.offsetHeight || (n - 1) * (fs * 1.12 + 14);
    // ── riel de tiempo
    const yr = Math.round(fsChip + 70), xa = 26, xb = W - 26;
    Object.assign(this, { xd, yr, xa, xb, x0: xa + 22, xe: W - 58 });
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';
    const mk = (tag, at, padre) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); (padre || svg).appendChild(e); return e; };
    mk('line', { x1: xa, x2: xb, y1: yr, y2: yr, stroke: 'color-mix(in srgb, var(--ink) 35%, transparent)', 'stroke-width': 6, 'stroke-linecap': 'round' });
    this.recorrido = mk('line', { x1: xa, y1: yr, y2: yr, stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round' });
    this.marcas = [];
    for (let x = xa + 14; x <= xb - 6; x += 30) {
      const largo = this.marcas.length % 7 === 0 ? 22 : 12;
      this.marcas.push({ x, e: mk('line', { x1: x, x2: x, y1: yr + 12, y2: yr + 12 + largo, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linecap': 'round' }) });
    }
    // línea límite (vertical, punteada) con su punta hacia la fecha
    this.limite = mk('line', { x1: xd, x2: xd, y1: fsChip + 14, y2: yr + 52, stroke: 'var(--acento)', 'stroke-width': 7, 'stroke-dasharray': '16 11', 'stroke-linecap': 'round' });
    // cursor: el «hoy» que avanza
    this.cursor = mk('g', {});
    mk('circle', { cx: 0, cy: 0, r: 17, fill: 'var(--ink)' }, this.cursor);
    mk('circle', { cx: 0, cy: 0, r: 7, fill: 'var(--bg)' }, this.cursor);
    // ── bodega
    const top = yr + 70, bottom = Math.max(top + 300, H - listaH - 40);
    const bw = Math.min(W - 40, F45 ? 620 : 700), bx = (W - bw) / 2, techo = Math.min(120, (bottom - top) * 0.26);
    const yw = top + techo;
    mk('path', { d: `M${bx} ${bottom} L${bx} ${yw} L${bx + bw / 2} ${top} L${bx + bw} ${yw} L${bx + bw} ${bottom}`, fill: 'none',
      stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' });
    mk('line', { x1: bx - 18, x2: bx + bw + 18, y1: bottom, y2: bottom, stroke: 'var(--ink)', 'stroke-width': 6, 'stroke-linecap': 'round' });
    Object.assign(this, { bx, bw, yw, bottom });
    // cajas en pila: columnas × filas, de abajo hacia arriba
    const cols = 4, filas = (bottom - yw) > 330 ? 3 : 2, gap = 14, pad = 34;
    const cwid = (bw - 2 * pad - (cols - 1) * gap) / cols;
    const chi = Math.min(110, ((bottom - yw) - 40 - (filas - 1) * gap) / filas);
    this.cajas = [];
    for (let f = 0; f < filas; f++) {
      for (let k = 0; k < cols; k++) {
        const x = bx + pad + k * (cwid + gap), y = bottom - 8 - (f + 1) * chi - f * gap;
        const g = mk('g', {});
        mk('rect', { x, y, width: cwid, height: chi, rx: 12, fill: 'color-mix(in srgb, var(--ink) 16%, transparent)' }, g);
        const lleno = mk('rect', { x, y, width: cwid, height: chi, rx: 12, fill: 'var(--acento)' }, g);
        const borde = mk('rect', { x: x + 2.5, y: y + 2.5, width: cwid - 5, height: chi - 5, rx: 10, fill: 'none', stroke: 'var(--ink)', 'stroke-width': 5 }, g);
        const cx = x + cwid / 2, cy = y + chi / 2, r = Math.min(cwid, chi) * 0.24;
        const cruz = mk('path', { d: `M${cx - r} ${cy} L${cx + r} ${cy} M${cx} ${cy - r} L${cx} ${cy + r}`, stroke: 'var(--ink)', 'stroke-width': 8, 'stroke-linecap': 'round', fill: 'none' }, g);
        this.cajas.push({ g, lleno, borde, cruz, cx, cy, k, f });
      }
    }
    // polvo que cae dentro de la bodega cuando ya nadie mueve las cajas
    this.polvo = Array.from({ length: 9 }, (_, i) => {
      const e = mk('circle', { r: 5 + (i % 3), fill: 'var(--ink)', cx: bx + 50 + (((i * 37) % 11) / 10) * (bw - 100) });
      return { e, per: 3.6 + (i % 4) * 0.7, fase: ((i * 5) % 9) / 9 };
    });
    lienzo.appendChild(svg);
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = this.n, c = this.c;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    const s0 = ps[0].start, sc = ps[c].start, sf = ps[n - 1].start;
    const fantasma = 0.28 * eo(clamp((t - T.ini) / 0.5));
    // cursor: avanza a ritmo constante desde el inicio hasta la línea justo cuando la voz dice el cruce; después sigue,
    // cada vez más lento (el tiempo no se detiene)
    const t0 = Math.min(T.ini, sc - 0.5);
    let x;
    if (t <= sc) x = this.x0 + (this.xd - this.x0) * clamp((t - t0) / Math.max(0.5, sc - t0));
    else x = this.xd + (this.xe - this.xd) * (1 - Math.exp(-(t - sc) / 5));
    this.cursor.setAttribute('transform', `translate(${x.toFixed(1)} ${this.yr})`);
    this.cursor.style.opacity = Math.max(fantasma, eo(clamp((t - T.ini) / 0.4))).toFixed(3);
    this.recorrido.setAttribute('x2', x.toFixed(1));
    this.marcas.forEach(({ x: mx, e }) => { e.style.opacity = (mx <= x ? 0.85 : 0.3).toFixed(2); });
    // fecha límite: en acento hasta el cruce; después queda en crema
    const dicha = eo(clamp((t - s0) / 0.45)), cruzo = t >= sc + 0.2;
    const pulso = 0.85 + 0.15 * Math.sin(2 * Math.PI * t / 1.5);
    this.chip.style.opacity = Math.max(fantasma, dicha * (cruzo ? 0.75 : pulso)).toFixed(3);
    this.chip.style.color = cruzo ? 'var(--ink)' : 'var(--acento)';
    this.chip.style.transform = `translateY(${((1 - dicha) * -14).toFixed(1)}px)`;
    this.limite.setAttribute('stroke', cruzo ? 'var(--ink)' : 'var(--acento)');
    this.limite.style.opacity = Math.max(fantasma, dicha * (cruzo ? 0.6 : 1)).toFixed(3);
    this.limite.style.strokeDashoffset = (-t * 16).toFixed(1);
    // cajas: esperan; al cruce cambian de estado en ola de izquierda a derecha; al final se asientan
    const asienta = n - 1 > c ? eo(clamp((t - sf) / 0.6)) : eo(clamp((t - sc - 1.2) / 0.6));
    this.cajas.forEach((cj) => {
      const tv = sc + 0.09 * cj.k + 0.05 * cj.f, s = eo(clamp((t - tv) / 0.45));
      cj.lleno.style.opacity = s.toFixed(3);
      cj.borde.setAttribute('stroke', s > 0.5 ? 'var(--acento)' : 'var(--ink)');
      cj.borde.style.opacity = (s > 0.5 ? 1 : Math.max(0.3, 0.55 + 0.25 * Math.sin(2 * Math.PI * (t / 2.2 + cj.k * 0.12)))).toFixed(3);
      cj.cruz.setAttribute('stroke', s > 0.5 ? 'var(--tinta-acento, var(--bg))' : 'var(--ink)');
      cj.cruz.setAttribute('transform', `rotate(${(45 * s).toFixed(2)} ${cj.cx} ${cj.cy})`);
      cj.cruz.style.opacity = (s > 0.5 ? 1 : 0.7).toFixed(3);
      cj.g.setAttribute('transform', `translate(0 ${(asienta * 5).toFixed(2)})`);
    });
    // polvo: solo desde que las cajas vencieron
    const yTop = this.yw + 10, yBot = this.bottom - 14;
    this.polvo.forEach(({ e, per, fase }) => {
      if (t < sc + 0.6) { e.style.display = 'none'; return; }
      e.style.display = '';
      const u = ((((t - sc) / per + fase) % 1) + 1) % 1;
      e.setAttribute('cy', (yTop + (yBot - yTop) * u).toFixed(1));
      e.style.opacity = (0.4 * Math.sin(Math.PI * u) * eo(clamp((t - sc - 0.6) / 0.8))).toFixed(3);
    });
    // lista de los pasos 2..n
    this.items.forEach(({ el }, j) => {
      const i = j + 1, s = ps[i].start, entra = eo(clamp((t - s) / 0.45));
      const respira = i === activo ? 1 + 0.012 * Math.sin(2 * Math.PI * (t - s) / 1.6) : 1;
      el.style.opacity = Math.max(fantasma, entra * (i < activo ? 0.5 : 1)).toFixed(3);
      el.style.transform = `translateX(${((1 - entra) * -30).toFixed(1)}px) scale(${respira.toFixed(4)})`;
    });
  },
});
