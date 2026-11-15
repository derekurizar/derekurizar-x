// Pieza «agua» (ficha: agua.json): lagos, estanques y el mar (polígonos posados sobre el suelo) y los ríos (bandas de
// ≈ 9 m), en el tono de agua del estilo. «resaltar» la pieza la aclara.
(function (MAQ) {
  MAQ.PIEZAS.agua = {
    orden: 4,
    armar(ctx, piezas) {
      const { malla, tonos } = ctx;
      return piezas.map((p) => {
        const acc = malla.nueva(), orilla = tonos.agua.clone().lerp(tonos.borde, 0.18);
        for (const q of p.poligonos) malla.poligono(acc, q, 0.2, tonos.agua);
        for (const q of p.rios) { const pts = []; for (let i = 0; i + 1 < q.length; i += 2) pts.push([q[i], q[i + 1]]); malla.banda(acc, pts, 9, 0.25, 20, orilla); }
        const mat = malla.material({ desfase: 1 });
        malla.poner(acc, mat, 1);
        return { id: p.id, mat };
      });
    },
    en(t, lista, ctx) { for (const s of lista) s.mat.uniforms.uBrillo.value = ctx.cuadro.brillo[s.id] ? 1 + 0.3 * (ctx.cuadro.brillo[s.id] - 1) : 1; },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
