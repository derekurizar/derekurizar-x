// Objeto «bus» (ficha: bus.json): un bus urbano de 12 × 2.5 m, con ventanas que de noche brillan. Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.bus = {
    medidas: { largo_m: 12.0, ancho_m: 2.5, alto_m: 3.2 },
    faros: [[6.05, 0.75, -0.95], [6.05, 0.75, 0.95]], pilotos: [[-6.05, 0.9, -1.0], [-6.05, 0.9, 1.0]],
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), vidrio = tonos.linea.clone().lerp(lin(COL.luces), ES.modo === 1 ? 0.35 : 0.1);
      return [
        { geo: B(T, 12, 2.6, 2.5, 0, 0.35, 0), color: blanco, tinte: true },
        { geo: B(T, 11.0, 0.85, 2.54, 0.3, 1.65, 0), color: vidrio, luz: ES.modo === 1 ? 0.5 : 0 },
        { geo: B(T, 0.06, 1.2, 2.3, 6.0, 1.45, 0), color: vidrio },
        { geo: B(T, 0.08, 0.22, 0.4, 6.0, 0.62, -0.95), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.08, 0.22, 0.4, 6.0, 0.62, 0.95), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.06, 0.3, 0.3, -6.02, 0.8, -1.0), color: tonos.mal, luz: 0.6 },
        { geo: B(T, 0.06, 0.3, 0.3, -6.02, 0.8, 1.0), color: tonos.mal, luz: 0.6 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
