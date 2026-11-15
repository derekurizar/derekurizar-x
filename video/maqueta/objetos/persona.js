// Objeto «persona» (ficha: persona.json): una persona de pie (1.75 m). Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.persona = {
    medidas: { largo_m: 0.5, ancho_m: 0.5, alto_m: 1.75 },
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos } = ctx, blanco = new T.Color(1, 1, 1), oscuro = tonos.linea.clone().lerp(tonos.muro, 0.5), piel = tonos.secundario.clone().lerp(tonos.techo, 0.4);
      return [
        { geo: B(T, 0.26, 0.85, 0.36, 0, 0, 0), color: oscuro },
        { geo: B(T, 0.3, 0.62, 0.5, 0, 0.85, 0), color: blanco, tinte: true },
        { geo: new T.SphereGeometry(0.13, 8, 6).translate(0, 1.6, 0), color: piel },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
