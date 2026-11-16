// Objeto «pin» (ficha: pin.json): un pin de mapa (una gota invertida de 2.4 m) que marca un punto. Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.pin = {
    medidas: { largo_m: 1.0, ancho_m: 1.0, alto_m: 2.4 },
    variantes: (ctx) => [ctx.tonos.secundario.clone()],
    partes(ctx) {
      const { THREE: T, tonos } = ctx, blanco = new T.Color(1, 1, 1), ojo = tonos.linea.clone().lerp(tonos.muro, 0.4);
      return [
        { geo: new T.SphereGeometry(0.5, 14, 10).translate(0, 1.9, 0), color: blanco, tinte: true },
        { geo: new T.ConeGeometry(0.42, 1.55, 14).rotateX(Math.PI).translate(0, 0.78, 0), color: blanco, tinte: true },
        { geo: new T.SphereGeometry(0.2, 10, 8).translate(0, 1.9, 0.38), color: ojo },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
