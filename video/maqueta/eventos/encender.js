// Evento «encender» (ficha: encender.json): las luces de unos lugares (o «todos») se encienden de a poco, cada una con
// su retraso fijo (hash por índice) dentro de `dur`.
(function (MAQ) {
  MAQ.EVENTOS.encender = {
    orden: 70,
    aplicar(t, e, ctx) {
      const { suave, hash } = ctx;
      ctx.luces.forEach((l, i) => {
        if (!(e.lugares === "todos" || (e.lugares && e.lugares.includes(l.id)))) return;
        l.v = l.v + (1 - l.v) * suave(0, 1, (t - e.t - hash(i, 3) * e.dur * 0.7) / Math.max(0.05, e.dur * 0.3));
      });
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
