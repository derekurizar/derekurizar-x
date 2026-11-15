// Objeto «arbol» (ficha: arbol.json): un árbol de 7 m (tronco y copa). Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.arbol = {
    medidas: { largo_m: 4.4, ancho_m: 4.4, alto_m: 7.0 },
    variantes(ctx) { const v = ctx.tonos.verde, s = ctx.ES.modo === 1 ? 2.2 : 1; return [v.clone().multiplyScalar(s), v.clone().multiplyScalar(s * 0.85).lerp(ctx.tonos.techo, 0.15), v.clone().multiplyScalar(s * 1.15)]; },
    partes(ctx) {
      const { THREE: T, tonos } = ctx, blanco = new T.Color(1, 1, 1), tronco = tonos.linea.clone().lerp(tonos.muro, 0.6);
      return [
        { geo: new T.CylinderGeometry(0.22, 0.3, 2.4, 6).translate(0, 1.2, 0), color: tronco },
        { geo: new T.IcosahedronGeometry(2.2, 0).translate(0, 4.4, 0), color: blanco, tinte: true },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
