// Animación «cronologia» (semilla de la biblioteca, sembrada con /historia): una línea de tiempo vertical con 2–6
// eventos. Cada paso es «fecha · qué pasó» («1952 · Abre el primer horno»): la fecha va grande a la izquierda del texto y
// el punto del riel se enciende cuando la voz dice ese paso; el riel se llena del evento anterior al siguiente mientras
// la voz avanza y el punto activo late. Al entrar la escena se ven tenues todos los eventos (el espectador ve cuánto
// falta). Estilo Noche: la fecha va en Archivo condensado 900 en mayúsculas y el evento en Archivo 800; lo único en
// acento es el evento activo (su fecha, su punto y la marca del riel), lo ya dicho queda en crema atenuada.
// Todo es función de t (seek puro, sin azar ni reloj).
//
// Contrato (referencias/roles/video-animador.md): ANIM.registrar(id, { meta, pintar(lienzo, P, ctx), seek(t, T) })
//   P   = { titulo, pasos: [texto] }                         (del guion; «fecha · evento» o solo el evento)
//   ctx = { colores, F45, ancho, alto, V }
//   T   = { ini, pasos: [{ texto, start }], fin, dur }       (video.py tiempos)
ANIM.registrar('cronologia', {
  meta: {
    descripcion: 'línea de tiempo vertical: cada evento «fecha · qué pasó» se enciende en el riel cuando la voz lo dice',
    mecanismo: 'cronologia',
    temas: ['historia', 'cronología', 'línea de tiempo', 'caso', 'fechas', 'etapas'],
    pasos: [2, 6],
    ejemplo: { titulo: '¿Cómo pasó?', pasos: ['1952 · Abre el horno', '1976 · El terremoto', '1990 · 25 sucursales', '2010 · Cierra la última'] },
  },
  pintar(lienzo, P, ctx) {
    const { V } = ctx, n = P.pasos.length;
    this.V = V;
    const x = ctx.F45 ? 40 : 46, margen = ctx.F45 ? 40 : 60;
    const paso = (ctx.alto - 2 * margen) / Math.max(1, n - 1);
    this.ys = P.pasos.map((_, i) => (n === 1 ? ctx.alto / 2 : margen + i * paso));
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', ctx.ancho); svg.setAttribute('height', ctx.alto);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const linea = (y1, y2, color, ancho) => {
      const l = document.createElementNS(NS, 'line');
      l.setAttribute('x1', x); l.setAttribute('x2', x); l.setAttribute('y1', y1); l.setAttribute('y2', y2);
      l.setAttribute('stroke', color); l.setAttribute('stroke-width', ancho); l.setAttribute('stroke-linecap', 'round');
      svg.appendChild(l);
      return l;
    };
    linea(this.ys[0], this.ys[n - 1], 'color-mix(in srgb, var(--ink) 22%, transparent)', 6);
    this.lleno = linea(this.ys[0], this.ys[0], 'var(--ink)', 6);
    this.marca = document.createElementNS(NS, 'circle');
    this.marca.setAttribute('r', 9); this.marca.setAttribute('cx', x); this.marca.setAttribute('fill', 'var(--acento)');
    this.puntos = this.ys.map((y) => {
      const c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', ctx.F45 ? 16 : 18);
      c.setAttribute('stroke-width', 5);
      svg.appendChild(c);
      return c;
    });
    svg.appendChild(this.marca);
    lienzo.appendChild(svg);
    const fs = ctx.F45 ? 42 : 50, fsF = ctx.F45 ? 76 : 92;
    this.filas = P.pasos.map((txt, i) => {
      const m = String(txt).match(/^\s*([^·:]{1,14}?)\s*[·:]\s*(.+)$/);
      const el = document.createElement('div');
      el.style.cssText = `position:absolute;left:${x + 52}px;right:0;top:${this.ys[i]}px;transform-origin:0 50%;` +
        'display:flex;align-items:baseline;gap:22px;white-space:nowrap;overflow:hidden';
      const fecha = document.createElement('span');
      // el shorthand font resetea font-stretch: el ancho condensado va después
      fecha.style.cssText = `font:900 ${fsF}px/1 Archivo,sans-serif;font-stretch:62.5%;text-transform:uppercase;` +
        'letter-spacing:-.01em;color:var(--ink)';
      fecha.textContent = m ? m[1] : '';
      const texto = document.createElement('span');
      texto.style.cssText = `font:800 ${fs}px/1.1 Archivo,sans-serif;letter-spacing:-.01em;color:var(--ink);white-space:normal`;
      texto.textContent = m ? m[2] : txt;
      el.appendChild(fecha); el.appendChild(texto);
      lienzo.appendChild(el);
      el.style.marginTop = -(el.offsetHeight / 2) + 'px';
      el._fecha = fecha;
      return el;
    });
  },
  seek(t, T) {
    const { clamp, eo } = this.V, ps = T.pasos, n = ps.length;
    let activo = -1;
    ps.forEach((p, i) => { if (t >= p.start) activo = i; });
    // el riel se llena del evento activo hacia el siguiente mientras pasa el tiempo entre los dos
    let y = this.ys[0];
    if (activo >= 0) {
      const sig = activo + 1 < n ? ps[activo + 1].start : T.fin;
      const a = this.ys[activo], b = activo + 1 < n ? this.ys[activo + 1] : this.ys[activo];
      y = a + (b - a) * 0.6 * clamp((t - ps[activo].start) / Math.max(0.5, sig - ps[activo].start));
    }
    this.lleno.setAttribute('y2', y.toFixed(1));
    this.marca.setAttribute('cy', y.toFixed(1));
    this.marca.style.opacity = activo >= 0 ? 1 : 0;
    this.puntos.forEach((c, i) => {
      const on = i <= activo, late = i === activo ? Math.sin(Math.PI * clamp((t - ps[i].start) / 0.5)) : 0;
      const color = i === activo ? 'var(--acento)' : 'var(--ink)';
      c.setAttribute('fill', on ? color : 'var(--bg)');
      c.setAttribute('stroke', on ? color : 'color-mix(in srgb, var(--ink) 35%, transparent)');
      c.setAttribute('r', ((this.puntos.length > 4 ? 16 : 18) * (1 + 0.35 * late)).toFixed(2));
    });
    // lo que falta, tenue; lo ya dicho, al 50 %; la fecha del activo en acento
    this.filas.forEach((el, i) => {
      const entra = eo((t - ps[i].start) / 0.45), fantasma = 0.28 * eo((t - T.ini) / 0.5);
      el.style.opacity = Math.max(fantasma, entra * (i < activo ? 0.5 : 1)).toFixed(3);
      el.style.transform = `translateX(${((1 - entra) * -30).toFixed(1)}px)`;
      el._fecha.style.color = i === activo ? 'var(--acento)' : 'var(--ink)';
    });
  },
});
