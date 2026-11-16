// Anotación «medida» (ficha: medida.json): el tamaño de algo con su rótulo («5 m»). `circulo`: un círculo de `radio_m`
// en el suelo alrededor del ancla (con su radio punteado); `regla`: una regla de `radio_m` desde el ancla hacia adelante (la
// dirección del móvil), con sus topes. Se abre al entrar. El rótulo va junto al borde derecho de la figura, dentro de la
// columna de texto. Capa 2D (capa.js → A); seek puro.
(function (MAQ) {
  MAQ.ANOTACIONES = MAQ.ANOTACIONES || {};
  MAQ.ANOTACIONES.medida = {
    armar(A, lista) {
      return lista.map((o) => ({ o, sombra: A.svg("path", "anot-sombra"), linea: A.svg("path", "anot-linea"), radio: A.svg("path", "anot-fina"),
        centro: A.svg("circle", "anot-relleno"), rot: A.div("anot-rotulo", o.rotulo), w: null }));
    },
    en(t, st, A) {
      const Z = A.Z;
      for (const s of st) {
        const o = s.o, viva = t >= o.t && t < o.hasta, [e, f] = A.vida(t, o.t, o.hasta, 0.5, 0.3), op = viva ? e * f : 0;
        const q = viva ? A.ancla(o.en, t) : null, ok = !!(q && q.vis && q.px !== null);
        let pts = null, ext = null, rad = null;
        if (ok && o.forma === "regla") {
          const L = A.mundo.metros(o.radio_m) * e, x1 = q.x + q.dx * L, y1 = q.y + q.dy * L;
          const p0 = [q.px, q.py], p1 = A.p(x1, y1, A.mundo.altura(x1, y1) + A.mundo.metros(0.3));
          if (p1) {
            const dx = p1[0] - p0[0], dy = p1[1] - p0[1], n = Math.hypot(dx, dy) || 1, nx = -dy / n * 12, ny = dx / n * 12;
            pts = [p0, p1]; ext = [[p0[0] + nx, p0[1] + ny], [p0[0] - nx, p0[1] - ny], [p1[0] + nx, p1[1] + ny], [p1[0] - nx, p1[1] - ny]];
          }
        } else if (ok) {
          pts = A.suelo(q.x, q.y, o.radio_m * (0.2 + 0.8 * e), 64);
          const xr = q.x + A.mundo.metros(o.radio_m * (0.2 + 0.8 * e)), pr = A.p(xr, q.y, A.mundo.altura(xr, q.y) + A.mundo.metros(0.3));
          rad = pr ? [[q.px, q.py], pr] : null;
        }
        const d = pts ? (o.forma === "regla" ? A.d(pts) + (ext ? "M" + A.d([ext[0], ext[1]]).slice(1) + "M" + A.d([ext[2], ext[3]]).slice(1) : "") : A.d(pts)) : "";
        s.linea.setAttribute("d", d); s.sombra.setAttribute("d", d); s.radio.setAttribute("d", rad ? A.d(rad) : "");
        for (const el of [s.linea, s.sombra, s.radio]) el.style.opacity = op.toFixed(3);
        s.centro.setAttribute("r", ok ? "5" : "0");
        if (ok) { s.centro.setAttribute("cx", q.px.toFixed(1)); s.centro.setAttribute("cy", q.py.toFixed(1)); }
        s.centro.style.opacity = op.toFixed(3);
        // el rótulo: a la derecha de la figura (o a la izquierda si no cabe), centrado en su altura
        if (!pts) { s.rot.style.opacity = "0"; continue; }
        if (s.w === null) s.w = [s.rot.offsetWidth, s.rot.offsetHeight];
        let xm = -1e9, ym = 0, xmin = 1e9, y0 = 1e9, y1 = -1e9;
        for (const p of pts) { if (p[0] > xm) { xm = p[0]; ym = p[1]; } xmin = Math.min(xmin, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); }
        if (o.forma !== "regla") ym = (y0 + y1) / 2;
        let x = xm + 18;
        if (x + s.w[0] > Z.der) x = xmin - 18 - s.w[0];
        x = Math.max(Z.izq, Math.min(Z.der - s.w[0], x));
        s.rot.style.opacity = (op * A.clamp((e - 0.5) * 3)).toFixed(3);
        s.rot.style.transform = "translate(" + x.toFixed(1) + "px," + (ym - s.w[1] / 2).toFixed(1) + "px)";
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, ANOTACIONES: {}, MUNDOS: {} });
