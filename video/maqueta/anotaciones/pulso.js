// Anotación «pulso» (ficha: pulso.json): anillos que se abren en el suelo alrededor de cada ancla (un actor, vehículos de
// un flujo, un lugar), con un punto en el centro: «este manda su señal». Capa 2D (capa.js → A): cada anillo es el círculo
// de radio r en metros proyectado desde el 3D, así se ve en perspectiva y sigue al móvil. Seek puro: la fase sale de t.
(function (MAQ) {
  MAQ.ANOTACIONES = MAQ.ANOTACIONES || {};
  MAQ.ANOTACIONES.pulso = {
    armar(A, lista) {
      return lista.map((o) => ({
        o,
        anillos: o.sobre.map(() => Array.from({ length: o.anillos }, () => A.svg("path", "anot-linea"))),
        puntos: o.sobre.map(() => A.svg("circle", "anot-relleno")),
      }));
    },
    en(t, st, A) {
      for (const s of st) {
        const o = s.o, viva = t >= o.t && t < o.hasta, [e, f] = A.vida(t, o.t, o.hasta, 0.3, 0.3), op = viva ? e * f : 0;
        o.sobre.forEach((an, j) => {
          const q = viva ? A.ancla(an, t) : null, ok = !!(q && q.vis && q.px !== null), dot = s.puntos[j];
          dot.setAttribute("r", ok ? "6" : "0");
          if (ok) { dot.setAttribute("cx", q.px.toFixed(1)); dot.setAttribute("cy", q.py.toFixed(1)); }
          dot.style.opacity = op.toFixed(3);
          s.anillos[j].forEach((path, k) => {
            const ph = ok ? (((t - o.t) / o.periodo_s + k / o.anillos) % 1 + 1) % 1 : 0;
            const pts = ok ? A.suelo(q.x, q.y, o.radio_m * (0.12 + 0.88 * ph), 40) : null;
            path.setAttribute("d", A.d(pts));
            path.style.opacity = (op * Math.pow(1 - ph, 1.3) * Math.min(1, ph * 8)).toFixed(3);
          });
        });
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, ANOTACIONES: {}, MUNDOS: {} });
