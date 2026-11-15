// Pieza «ruta» (ficha: ruta.json): una línea discontinua por lugares (una carretera, un recorrido), pegada al relieve.
// La protagonista va en el acento y más gruesa; «resaltar» la sube por su id (ctx.linea).
(function (MAQ) {
  MAQ.PIEZAS.ruta = {
    orden: 11,
    armar(ctx, piezas) {
      const { CFG, COL, pegar, cinta } = ctx;
      for (const p of piezas) {
        ctx.linea(p.id, cinta(pegar(p.puntos, 1.5, 0.4), p.protagonista ? COL.acento : COL.ruta, CFG.ruta.ancho * (p.protagonista ? 1.5 : 1),
          p.protagonista ? 1 : CFG.ruta.alfa, 4, { raya: CFG.ruta.raya_km }));
      }
      return null;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
