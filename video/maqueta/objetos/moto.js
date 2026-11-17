// Objeto «moto» (ficha: moto.json): una moto con su piloto, de 2.1 m. Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.moto = {
    medidas: { largo_m: 2.1, ancho_m: 0.8, alto_m: 1.6 },
    cabecea: true,                       // sobre el relieve de una pieza se inclina con la pendiente (motor.js: flota)
    faros: [[1.05, 0.95, 0]], pilotos: [[-1.05, 0.85, 0]],
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL } = ctx, blanco = new T.Color(1, 1, 1), oscuro = tonos.linea.clone().lerp(tonos.muro, 0.4);
      return [
        { geo: B(T, 1.7, 0.45, 0.36, 0, 0.35, 0), color: blanco, tinte: true },
        { geo: new T.CylinderGeometry(0.32, 0.32, 0.12, 8).rotateX(Math.PI / 2).translate(0.75, 0.32, 0), color: oscuro },
        { geo: new T.CylinderGeometry(0.32, 0.32, 0.12, 8).rotateX(Math.PI / 2).translate(-0.75, 0.32, 0), color: oscuro },
        { geo: B(T, 0.45, 0.65, 0.42, -0.15, 0.8, 0), color: oscuro },
        { geo: new T.SphereGeometry(0.15, 8, 6).translate(-0.05, 1.6, 0), color: blanco, tinte: true },
        { geo: B(T, 0.08, 0.14, 0.18, 0.9, 0.85, 0), color: lin(COL.luces), luz: 1 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
