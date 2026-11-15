// Objeto «torre» (ficha: torre.json): una torre de telecomunicaciones de 30 m, con su baliza encendida. Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.torre = {
    medidas: { largo_m: 2.4, ancho_m: 2.4, alto_m: 30.0 },
    variantes: (ctx) => [ctx.tonos.secundario.clone().multiplyScalar(0.75)],
    partes(ctx) {
      const { THREE: T, tonos } = ctx, blanco = new T.Color(1, 1, 1);
      return [
        { geo: new T.CylinderGeometry(0.25, 1.2, 28, 4).rotateY(Math.PI / 4).translate(0, 14, 0), color: blanco, tinte: true },
        { geo: B(T, 0.25, 1.6, 0.8, 0.45, 25.5, 0), color: blanco, tinte: true },
        { geo: B(T, 0.25, 1.6, 0.8, -0.45, 25.5, 0), color: blanco, tinte: true },
        { geo: new T.CylinderGeometry(0.05, 0.05, 2.5, 4).translate(0, 29.2, 0), color: blanco, tinte: true },
        { geo: new T.SphereGeometry(0.22, 8, 6).translate(0, 30.5, 0), color: tonos.mal, luz: 1 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
