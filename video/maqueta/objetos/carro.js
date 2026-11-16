// Objeto «carro» (ficha: carro.json): un carro (sedán) de 4.5 × 1.8 m, con faros y pilotos. Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.carro = {
    medidas: { largo_m: 4.5, ancho_m: 1.8, alto_m: 1.5 },
    faros: [[2.3, 0.62, -0.6], [2.3, 0.62, 0.6]], pilotos: [[-2.3, 0.72, -0.62], [-2.3, 0.72, 0.62]],
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL } = ctx, blanco = new T.Color(1, 1, 1), vidrio = tonos.linea.clone().lerp(tonos.techo, 0.25), rueda = tonos.linea.clone();
      return [
        { geo: B(T, 4.5, 0.72, 1.8, 0, 0.3, 0), color: blanco, tinte: true },
        { geo: B(T, 2.3, 0.5, 1.6, -0.3, 1.02, 0), color: vidrio },
        { geo: B(T, 2.0, 0.06, 1.5, -0.35, 1.52, 0), color: blanco, tinte: true },
        { geo: B(T, 0.08, 0.16, 0.34, 2.23, 0.56, -0.6), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.08, 0.16, 0.34, 2.23, 0.56, 0.6), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.06, 0.14, 0.34, -2.24, 0.66, -0.6), color: tonos.mal, luz: 0.6 },
        { geo: B(T, 0.06, 0.14, 0.34, -2.24, 0.66, 0.6), color: tonos.mal, luz: 0.6 },
        ...[[1.4, 0.86], [1.4, -0.86], [-1.4, 0.86], [-1.4, -0.86]].map(([x, z]) => ({ geo: new T.CylinderGeometry(0.33, 0.33, 0.24, 8).rotateX(Math.PI / 2).translate(x, 0.33, z), color: rueda })),
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
