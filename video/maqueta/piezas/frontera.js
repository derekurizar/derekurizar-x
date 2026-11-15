// Pieza «frontera» (ficha: frontera.json): el contorno del país, los anillos del set, como cinta pegada al relieve.
// La protagonista va en el acento y más gruesa; «resaltar» la sube por su id (ctx.linea).
(function (MAQ) {
  MAQ.PIEZAS.frontera = {
    orden: 10,
    armar(ctx, piezas) {
      const { CFG, COL, pegar, cinta } = ctx;
      for (const p of piezas) {
        for (const an of p.anillos) { const cad = an.map(([x, y]) => [x, y]); cad.push(cad[0]);
          if (CFG.frontera.borde) cinta(pegar(cad, 1.5, 0.35), COL.linea, CFG.frontera.ancho + CFG.frontera.borde, 1, 2);
          ctx.linea(p.id, p.protagonista ? cinta(pegar(cad, 1.5, 0.35), COL.acento, CFG.frontera.ancho * 1.7, 1, 3)
            : cinta(pegar(cad, 1.5, 0.35), COL.frontera, CFG.frontera.ancho, CFG.frontera.alfa, 3)); }
      }
      return null;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
