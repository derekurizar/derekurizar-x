// Evento «onda» (ficha: onda.json): un anillo que crece desde un lugar o desde toda una falla (la sacudida que se
// propaga). Va a ctx.cuadro.ondas (las leen las luces y el voxel) y al canal uOnda del relieve (hasta ctx.NO a la vez).
(function (MAQ) {
  MAQ.EVENTOS.onda = {
    orden: 60,
    aplicar(t, e, ctx) {
      if (!(t >= e.t && t <= e.t + e.dur)) return;
      const u = (t - e.t) / e.dur;
      ctx.cuadro.ondas.push({ x: e.x, y: e.y, pieza: e.pieza ? ctx.idxFalla(e.pieza) : -1, r: e.radio_km * (1 - Math.pow(1 - u, 1.6)),
        k: Math.pow(1 - u, 0.8) * ctx.suave(0, 0.06, u) * ctx.CFG.onda });
    },
    en(t, st, ctx) {
      const S = ctx.superficie, ondas = ctx.cuadro.ondas;
      for (let i = 0; i < ctx.NO; i++) { const o = ondas[i];
        if (o) { S.uOnda.value[i].set(o.x, -o.y, o.r, o.k); S.uOndaPieza.value[i] = o.pieza; } else S.uOnda.value[i].set(0, 0, 0, 0); }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
