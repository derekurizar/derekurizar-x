// Evento «deslizar» (ficha: deslizar.json): el corrimiento de una falla, dos carriles de galones (las flechas que arma
// piezas/falla.js) a los dos lados del trazo, en sentidos opuestos, alrededor de s0.
(function (MAQ) {
  MAQ.EVENTOS.deslizar = {
    orden: 61,
    inicio(t, st, ctx) { for (const o of ctx.fallas3d || []) o.flechas.visible = false; },
    aplicar(t, e, ctx) {
      if (!(t >= e.t && t <= e.t + e.dur)) return;
      const o = ctx.fallas3d[ctx.idxFalla(e.pieza)], U = o.flechas.material.uniforms, tr = t - e.t, { suave } = ctx;
      o.flechas.visible = true; U.uCentro.value = e.s0; U.uSentido.value = e.sentido; U.uMedio.value = e.km / 2; U.uPeriodo.value = e.periodo_km;
      U.uFase.value = tr * e.vel / e.periodo_km; U.uAlfa.value = suave(0, 0.35, tr) * suave(e.dur, e.dur - 0.35, tr); U.uAncho.value = ctx.CFG.falla.flechas_px * ctx.cuadro.k;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
