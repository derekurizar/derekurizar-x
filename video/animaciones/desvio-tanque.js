// Animación «desvio-tanque» (mecanismo balance): el dinero entra a un tanque a la vista y termina en otro a la sombra.
// Dos tanques lado a lado: el de la izquierda (P.rotulos.base, «El banco») bajo el cono de luz de una lámpara
// (P.rotulos.limite, «Vista de la SIB»); el de la derecha, fuera de la luz, lleva el nombre del destino (P.rotulos.destino,
// o P.acento, o la última palabra del paso 2). Paso 1: una moneda con un papel cae a la boca del tanque a la vista.
// Paso 2: un tubo se dibuja de esa boca al otro tanque, la moneda viaja por él y el tanque a la sombra se llena; el de la
// vista sigue vacío. Paso 3 (opcional): un papel sale de vuelta y queda tachado. Arriba, los pasos como texto, cada uno
// cuando la voz lo dice. seek puro (sin azar ni reloj); quieta entre pasos.
ANIM.registrar('desvio-tanque', {
  meta: {
    descripcion: 'desvío: el dinero entra al tanque a la vista pero un tubo lo lleva al tanque a la sombra, que se llena; el visible queda vacío',
    mecanismo: 'balance',
    temas: ['desvío', 'fraude', 'banco', 'dinero', 'fuera de balance', 'supervisión', 'captación'],
    pasos: [2, 3],
    ejemplo: {
      titulo: 'El dinero cambia de tanque',
      pasos: ['Firma un pagaré', 'A nombre de Organizadora', 'Un certificado sin validez'],
    },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length, F = ctx.F45, W = ctx.ancho, H = ctx.alto;
    const R = P.rotulos || {};
    const ultima = (s) => String(s || '').trim().split(/\s+/).pop() || '';
    const destino = R.destino || P.acento || ultima(P.pasos[1]);
    this.V = V; this.n = n;
    const NS = 'http://www.w3.org/2000/svg';
    const mk = (tag, at) => { const e = document.createElementNS(NS, tag); for (const k in at) e.setAttribute(k, at[k]); return e; };

    // ---- pasos como texto, arriba
    const fs = F ? 40 : 44, fila = fs + (F ? 16 : 22);
    this.textos = P.pasos.map((txt, i) => {
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:0;right:0;top:${i * fila}px;height:${fila}px;display:flex;align-items:center;` +
        `font:800 ${fs}px/1.05 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);white-space:nowrap;opacity:0;`;
      el.innerHTML = `<span style="font:600 34px/1 'JetBrains Mono',monospace;margin-right:22px;opacity:.6">${i + 1}</span>`;
      el.appendChild(document.createTextNode(txt));
      lienzo.appendChild(el);
      return el;
    });

    // ---- escena
    const top = n * fila + (F ? 24 : 40);
    const labH = F ? 56 : 66;
    const bot = H - labH;
    const tw = Math.min(F ? 300 : 290, W * 0.36);
    const lx = W * 0.25, rx = W * 0.75;          // centros de los tanques
    const tankTop = top + (bot - top) * (F ? 0.42 : 0.36), tankBot = bot - 6;
    const lampY = top + (F ? 76 : 86);
    const bocaY = tankTop - (F ? 34 : 44);
    const svg = mk('svg', { width: W, height: H });
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none';

    // cono de luz y lámpara (estaban desde el principio: llevan su nombre)
    svg.appendChild(mk('path', {
      d: `M${lx - 16} ${lampY} L${lx - tw / 2 - 18} ${tankBot} L${lx + tw / 2 + 18} ${tankBot} L${lx + 16} ${lampY} Z`,
      fill: 'color-mix(in srgb, var(--ink) 11%, transparent)',
    }));
    svg.appendChild(mk('path', {
      d: `M${lx - 44} ${lampY} A44 30 0 0 1 ${lx + 44} ${lampY} Z`, fill: 'var(--ink)',
    }));

    // tanques
    const tanque = (cx) => {
      const x0 = cx - tw / 2, x1 = cx + tw / 2;
      return mk('path', {
        d: `M${x0} ${tankTop} L${x0} ${tankBot - 22} Q${x0} ${tankBot} ${x0 + 22} ${tankBot} L${x1 - 22} ${tankBot} Q${x1} ${tankBot} ${x1} ${tankBot - 22} L${x1} ${tankTop}`,
        fill: 'none', stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-linejoin': 'round', 'stroke-linecap': 'round',
      });
    };
    // relleno del tanque a la sombra (se eleva en el paso 2)
    const inner = tw - 22;
    this.relleno = mk('rect', { x: rx - inner / 2, width: inner, y: tankBot - 4, height: 0, rx: 14, fill: 'var(--acento)' });
    this.fondoT = tankBot - 4; this.altoMax = (tankBot - tankTop) * 0.68;
    svg.appendChild(this.relleno);
    svg.appendChild(tanque(lx));
    svg.appendChild(tanque(rx));
    // boca (ventanilla) sobre el tanque a la vista
    svg.appendChild(mk('path', {
      d: `M${lx - 60} ${bocaY - 18} L${lx - 22} ${bocaY + 14} L${lx + 22} ${bocaY + 14} L${lx + 60} ${bocaY - 18}`,
      fill: 'none', stroke: 'var(--ink)', 'stroke-width': 7, 'stroke-linejoin': 'round', 'stroke-linecap': 'round',
    }));

    // tubo del desvío: de la boca, por encima, al tanque a la sombra
    const ty = bocaY + 14;
    this.tubo = mk('path', {
      d: `M${lx + 22} ${ty} L${rx - 40} ${ty} Q${rx} ${ty} ${rx} ${ty + 40} L${rx} ${tankTop + 30}`,
      fill: 'none', stroke: 'var(--ink)', 'stroke-width': 14, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    });
    svg.appendChild(this.tubo);
    this.tuboL = this.tubo.getTotalLength();
    this.tubo.style.strokeDasharray = this.tuboL;

    // papel (pagaré) y moneda
    const papel = (w, h) => {
      const g = mk('g', {});
      g.appendChild(mk('rect', { x: -w / 2, y: -h / 2, width: w, height: h, rx: 6, fill: 'var(--bg)', stroke: 'var(--ink)', 'stroke-width': 5 }));
      for (let k = 0; k < 3; k++) {
        const yy = -h / 2 + h * (0.3 + k * 0.2);
        g.appendChild(mk('line', { x1: -w / 2 + 12, x2: w / 2 - (k === 2 ? 30 : 12), y1: yy, y2: yy, stroke: 'var(--ink)', 'stroke-width': 5, 'stroke-linecap': 'round' }));
      }
      return g;
    };
    const pw = F ? 70 : 76, ph = F ? 90 : 98;
    this.pagare = papel(pw, ph);
    svg.appendChild(this.pagare);
    this.moneda = mk('circle', { r: F ? 24 : 28, fill: 'var(--acento)' });
    svg.appendChild(this.moneda);

    // certificado que vuelve y su tacha
    this.cert = papel(pw + 14, ph + 6);
    const cw = (pw + 14) / 2 + 12, ch = (ph + 6) / 2 + 12;
    this.tachas = [[-cw, -ch, cw, ch], [cw, -ch, -cw, ch]].map(([x1, y1, x2, y2]) => {
      const l = mk('line', { x1, y1, x2, y2, stroke: 'var(--acento)', 'stroke-width': 9, 'stroke-linecap': 'round' });
      this.cert.appendChild(l);
      return l;
    });
    this.tachaL = 2 * Math.hypot(cw, ch);
    this.tachas.forEach((l) => { l.style.strokeDasharray = `${this.tachaL}`; });
    svg.appendChild(this.cert);

    lienzo.appendChild(svg);

    // rótulos (≤ 3 palabras)
    const rot = (txt, x, y, w) => {
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:${x - w / 2}px;width:${w}px;top:${y}px;text-align:center;white-space:nowrap;` +
        `font:600 36px/1 'JetBrains Mono',monospace;color:var(--ink);`;
      el.textContent = txt;
      lienzo.appendChild(el);
      return el;
    };
    const anchoRot = Math.min(W / 2 - 8, 380);
    rot(R.limite || 'A la vista', lx, top, anchoRot);
    this.rotBase = rot(R.base || 'El origen', lx, bot + 14, anchoRot);
    this.rotDest = document.createElement('div');
    this.rotDest.style.cssText = `position:absolute;left:${rx - anchoRot / 2}px;width:${anchoRot}px;top:${bot + 8}px;text-align:center;white-space:nowrap;` +
      `font:900 ${F ? 46 : 50}px/1 Archivo,sans-serif;color:var(--ink);opacity:.55;`;
    this.rotDest.style.fontStretch = '62.5%'; this.rotDest.style.textTransform = 'uppercase';
    this.rotDest.textContent = destino;
    lienzo.appendChild(this.rotDest);

    // posiciones clave
    this.p = { lx, rx, bocaY, ty, origenX: lx - tw / 2 + 10, origenY: lampY + 10, certX: W * 0.5, certY: lampY + 10 };
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, p = this.p;
    let activo = -1;
    ps.forEach((q, i) => { if (t >= q.start) activo = i; });
    // textos
    this.textos.forEach((el, i) => {
      const e = eo(clamp((t - ps[i].start) / 0.4));
      el.style.opacity = (e * (i < activo ? 0.45 : 1)).toFixed(3);
      el.style.transform = `translateY(${((1 - e) * 14).toFixed(1)}px)`;
    });
    // paso 1: moneda y pagaré caen a la boca
    const s0 = ps[0].start, a = eo(clamp((t - s0) / 0.8));
    const vis0 = t >= s0;
    const mx0 = p.lx, my0 = p.bocaY - 6;
    const cx = p.origenX + (mx0 - p.origenX) * a, cy = p.origenY + (my0 - p.origenY) * a;
    // paso 2: tubo + viaje + llenado
    const s1 = ps[1] ? ps[1].start : Infinity;
    const dTubo = clamp((t - s1) / 0.5);
    this.tubo.style.strokeDashoffset = (this.tuboL * (1 - dTubo)).toFixed(1);
    this.tubo.style.opacity = dTubo > 0 ? '1' : '0';
    const viaje = eo(clamp((t - s1 - 0.4) / 0.7));
    let mx = cx, my = cy;
    if (t >= s1 + 0.4) {
      const pt = this.tubo.getPointAtLength(this.tuboL * viaje);
      mx = pt.x; my = pt.y;
    }
    const llena = eo(clamp((t - s1 - 1.0) / 0.55));
    this.moneda.style.display = vis0 && llena < 1 ? '' : 'none';
    this.moneda.setAttribute('cx', mx.toFixed(1));
    this.moneda.setAttribute('cy', my.toFixed(1));
    this.moneda.style.opacity = (Math.min(a * 1.5, 1) * (1 - llena)).toFixed(3);
    // el pagaré se queda junto a la boca, del lado de la luz
    this.pagare.style.display = vis0 ? '' : 'none';
    const px = p.origenX + 20 + (p.lx - 110 - p.origenX - 20) * a, py = p.origenY + 30 + (p.bocaY - 70 - p.origenY - 30) * a;
    this.pagare.setAttribute('transform', `translate(${px.toFixed(1)} ${py.toFixed(1)}) rotate(${(-8 * a).toFixed(2)})`);
    this.pagare.style.opacity = Math.min(a * 1.5, 1).toFixed(3);
    const h = this.altoMax * llena;
    this.relleno.setAttribute('y', (this.fondoT - h).toFixed(1));
    this.relleno.setAttribute('height', h.toFixed(1));
    // paso 3: certificado que vuelve y queda tachado
    const s2 = ps[2] ? ps[2].start : Infinity;
    const c = eo(clamp((t - s2) / 0.6)), x = eo(clamp((t - s2 - 0.6) / 0.45));
    this.cert.style.display = t >= s2 ? '' : 'none';
    const qx = p.lx + (p.certX - p.lx) * c, qy = p.bocaY + (p.certY - p.bocaY) * c;
    this.cert.setAttribute('transform', `translate(${qx.toFixed(1)} ${qy.toFixed(1)}) rotate(${(6 * c).toFixed(2)})`);
    this.cert.style.opacity = c.toFixed(3);
    this.tachas.forEach((l, k) => {
      const xk = clamp(x * 2 - k);
      l.style.strokeDashoffset = (this.tachaL * (1 - xk)).toFixed(1);
      l.style.display = xk > 0 ? '' : 'none';
    });
    // acento: una cosa a la vez (moneda + tanque a la sombra en el paso 2; la tacha en el 3)
    const enTres = t >= s2 + 0.6;
    this.relleno.setAttribute('fill', enTres ? 'color-mix(in srgb, var(--ink) 40%, transparent)' : 'var(--acento)');
    this.rotDest.style.color = activo === 1 && llena > 0 ? 'var(--acento)' : 'var(--ink)';
    this.rotDest.style.opacity = activo >= 1 && llena > 0 ? '1' : '0.55';
  },
});
