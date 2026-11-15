// Evento «desaparecer» (ficha: desaparecer.json): un actor o un flujo se encoge hasta cero en `dur` segundos y no
// vuelve (salvo otro «aparecer» después). Escribe ctx.cuadro.vis[pieza], como «aparecer».
(function (MAQ) {
  MAQ.EVENTOS.desaparecer = {
    orden: 23,
    inicio(t, st, ctx) { ctx.cuadro.vis = ctx.cuadro.vis || {}; },
    aplicar(t, e, ctx) {
      const V = ctx.cuadro.vis = ctx.cuadro.vis || {};
      if (t >= e.t) V[e.pieza] = Math.min(V[e.pieza] === undefined ? 1 : V[e.pieza], 1 - ctx.suave(e.t, e.t + Math.max(1e-3, e.dur), t));
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
