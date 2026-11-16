// Evento «aparecer» (ficha: aparecer.json): un actor o un flujo crece desde cero en `dur` segundos. Deja en
// ctx.cuadro.vis[pieza] su escala (0–1), que leen actor y flujo; antes de su primer aparecer (si nada anterior lo fijó) la
// pieza no se ve. Los eventos van en el orden del maqueta.json (por t): el último que ya empezó manda.
(function (MAQ) {
  MAQ.EVENTOS.aparecer = {
    orden: 23,
    inicio(t, st, ctx) { ctx.cuadro.vis = ctx.cuadro.vis || {}; },
    aplicar(t, e, ctx) {
      const V = ctx.cuadro.vis = ctx.cuadro.vis || {};
      if (t >= e.t) { const u = ctx.clamp((t - e.t) / Math.max(1e-3, e.dur)); V[e.pieza] = 1 - Math.pow(1 - u, 3) * (1 - 1.4 * u * (1 - u)); }
      else if (V[e.pieza] === undefined) V[e.pieza] = 0;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
