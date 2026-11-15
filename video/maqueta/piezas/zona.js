// Pieza «zona» (ficha: zona.json): un área teñida sobre el suelo (un barrio, los parques, la plaza, el área de lo que
// pasó): el relleno en su tono con su opacidad y, si `borde`, el contorno en línea (una cinta de ancho en píxeles, que
// «resaltar» la pieza aviva por su id, como la ruta y la frontera).
(function (MAQ) {
  MAQ.PIEZAS.zona = {
    orden: 5,
    armar(ctx, piezas) {
      const { malla, tonos, lin, COL, CFG } = ctx;
      const tono = { acento: tonos.acento, secundario: tonos.secundario, verde: tonos.verde, agua: tonos.agua };
      const linea = { acento: COL.acento, secundario: COL.secundario, verde: COL.tierra_baja, agua: COL.mar };
      return piezas.map((p) => {
        const acc = malla.nueva();
        for (const q of p.poligonos) malla.poligono(acc, q, 0.5, tono[p.tono]);
        const mat = malla.material({ alfa: p.opacidad, desfase: 3 });
        malla.poner(acc, mat, 4);
        if (p.borde) for (const q of p.poligonos) {
          const pts = []; for (let i = 0; i + 1 < q.length; i += 2) pts.push([q[i], q[i + 1]]);
          pts.push(pts[0]);
          ctx.linea(p.id, ctx.cinta(ctx.pegar(pts, 12, 1.0), linea[p.tono], CFG.ruta.ancho * 1.2, 0.95, 5));
        }
        return { id: p.id, mat, alfa: p.opacidad };
      });
    },
    en(t, lista, ctx) { for (const s of lista) s.mat.uniforms.uAlfa.value = Math.min(1, s.alfa * (ctx.cuadro.brillo[s.id] ? 1 + 0.6 * (ctx.cuadro.brillo[s.id] - 1) : 1)); },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
