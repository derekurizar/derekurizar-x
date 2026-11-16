// Evento «pintar» (ficha: pintar.json): un tramo del trazo cambia de `color`; el color avanza como un frente de `de` a
// `a` en `dur` segundos y se queda. Añade a ctx.cuadro.pintura[trazo] {de, frente, color}; el último pintado manda.
(function (MAQ) {
  MAQ.EVENTOS.pintar = {
    orden: 24,
    inicio(t, st, ctx) { ctx.cuadro.pintura = ctx.cuadro.pintura || {}; },
    aplicar(t, e, ctx) {
      if (t < e.t) return;
      const u = ctx.clamp((t - e.t) / Math.max(1e-3, e.dur)), k = 1 - Math.pow(1 - u, 2);
      const P = ctx.cuadro.pintura = ctx.cuadro.pintura || {};
      (P[e.trazo] = P[e.trazo] || []).push({ de: e.de, frente: e.de + (e.a - e.de) * k, color: e.color });
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
