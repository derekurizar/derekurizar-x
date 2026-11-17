// Objeto «camion» (ficha: camion.json): un camión de carga de 10 × 2.5 m (cabina y caja). Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.camion = {
    medidas: { largo_m: 10.0, ancho_m: 2.5, alto_m: 3.6 },
    cabecea: true,                       // sobre el relieve de una pieza se inclina con la pendiente (motor.js: flota)
    faros: [[5.05, 0.8, -0.95], [5.05, 0.8, 0.95]], pilotos: [[-5.05, 0.9, -1.05], [-5.05, 0.9, 1.05]],
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL } = ctx, blanco = new T.Color(1, 1, 1), caja = tonos.muro.clone().lerp(tonos.secundario, 0.35), vidrio = tonos.linea.clone().lerp(tonos.techo, 0.25);
      return [
        { geo: B(T, 2.3, 2.3, 2.4, 3.85, 0.45, 0), color: blanco, tinte: true },
        { geo: B(T, 0.06, 0.8, 2.1, 5.0, 1.75, 0), color: vidrio },
        { geo: B(T, 7.3, 3.1, 2.5, -1.15, 0.5, 0), color: caja },
        { geo: B(T, 0.08, 0.22, 0.4, 5.02, 0.7, -0.95), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.08, 0.22, 0.4, 5.02, 0.7, 0.95), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.06, 0.3, 0.3, -4.82, 0.8, -1.05), color: tonos.mal, luz: 0.6 },
        { geo: B(T, 0.06, 0.3, 0.3, -4.82, 0.8, 1.05), color: tonos.mal, luz: 0.6 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
