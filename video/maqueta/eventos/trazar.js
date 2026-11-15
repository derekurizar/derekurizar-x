// Evento «trazar» (ficha: trazar.json): el trazo se dibuja de `de` a `a` (unidades desde su inicio) en `dur` segundos, con
// un arranque y una llegada suaves. Deja en ctx.cuadro.trazado[trazo] hasta dónde se ve; lo lee la pieza trazo.
(function (MAQ) {
  MAQ.EVENTOS.trazar = {
    orden: 24,
    inicio(t, st, ctx) { ctx.cuadro.trazado = ctx.cuadro.trazado || {}; },
    aplicar(t, e, ctx) {
      if (t < e.t) return;
      const u = ctx.clamp((t - e.t) / Math.max(1e-3, e.dur)), k = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      (ctx.cuadro.trazado = ctx.cuadro.trazado || {})[e.trazo] = e.de + (e.a - e.de) * k;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
