// Objeto «telefono» (ficha: telefono.json): un teléfono móvil de pie (16 cm; con `tamano` se agranda para que se lea). Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.telefono = {
    medidas: { largo_m: 0.01, ancho_m: 0.075, alto_m: 0.16 },
    variantes: (ctx) => [ctx.tonos.linea.clone().lerp(ctx.tonos.muro, 0.3)],
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), pantalla = ES.noche ? lin(COL.luz) : tonos.techo.clone();
      return [
        { geo: B(T, 0.009, 0.16, 0.075, 0, 0, 0), color: blanco, tinte: true },
        { geo: B(T, 0.002, 0.14, 0.066, 0.0052, 0.01, 0), color: pantalla, luz: ES.noche ? 1 : 0.3 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
