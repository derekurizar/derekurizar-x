// Evento «parpadear» (ficha: parpadear.json): las luces de unos lugares (o «todos») titilan durante `dur` (14 cambios
// por segundo, fijos por índice y cuadro), con una envolvente que sube y baja: el temblor que corta la luz.
(function (MAQ) {
  MAQ.EVENTOS.parpadear = {
    orden: 72,
    aplicar(t, e, ctx) {
      if (!(t >= e.t && t <= e.t + e.dur)) return;
      const u = (t - e.t) / e.dur, env = Math.sin(Math.PI * u), { hash } = ctx;
      ctx.luces.forEach((l, i) => {
        if (!(e.lugares === "todos" || (e.lugares && e.lugares.includes(l.id)))) return;
        l.v = l.v * (1 - env) + l.v * env * (hash(i, Math.floor(t * 14)) < 0.45 ? 0.12 : 1.25);
      });
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
