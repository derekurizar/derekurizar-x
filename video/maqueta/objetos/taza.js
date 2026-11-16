// Objeto «taza» (ficha: taza.json): una taza de café con su plato y un hilo de vapor, a escala de maqueta (0.55 m de alto
// con el vapor; con `tamano` 8 mide ≈ 4.4 m y se lee junto a una persona en una plaza). Low-poly con primitivas de three.js,
// en METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n
// (actor) con ctx.flota: la loza toma el color de la instancia (`variantes`); la superficie del café va en el acento. El
// vapor es geometría quieta (dos hilos en S): los objetos no reciben `t`. Sin colores escritos: todo sale de ctx.tonos.
(function (MAQ) {
  const hilo = (T, pts, r) => new T.TubeGeometry(new T.CatmullRomCurve3(pts.map((p) => new T.Vector3(p[0], p[1], p[2]))), 24, r, 6, false);
  MAQ.OBJETOS.taza = {
    medidas: { largo_m: 0.44, ancho_m: 0.44, alto_m: 0.55 },
    variantes: (ctx) => [ctx.tonos.techo.clone().lerp(ctx.tonos.secundario, 0.25)],
    partes(ctx) {
      const { THREE: T, tonos, ES } = ctx, blanco = new T.Color(1, 1, 1), noche = ES.modo === 1 || ES.modo === 4;
      const sombra = tonos.linea.clone().lerp(tonos.muro, 0.55);
      const vapor = noche ? tonos.secundario.clone().lerp(tonos.techo, 0.5) : tonos.linea.clone().lerp(tonos.muro, 0.35);
      return [
        // el plato: un disco ancho y bajo con su borde
        { geo: new T.CylinderGeometry(0.22, 0.17, 0.022, 28).translate(0, 0.011, 0), color: blanco, tinte: true },
        { geo: new T.TorusGeometry(0.21, 0.008, 5, 28).rotateX(Math.PI / 2).translate(0, 0.024, 0), color: sombra },
        // la taza: un vaso que se abre hacia arriba, con su labio
        { geo: new T.CylinderGeometry(0.125, 0.09, 0.2, 24).translate(0, 0.122, 0), color: blanco, tinte: true },
        { geo: new T.TorusGeometry(0.122, 0.009, 5, 24).rotateX(Math.PI / 2).translate(0, 0.222, 0), color: blanco, tinte: true },
        // el asa, del lado derecho
        { geo: new T.TorusGeometry(0.055, 0.014, 6, 14).rotateY(Math.PI / 2).translate(0, 0.13, 0.135), color: blanco, tinte: true },
        // la superficie del café: lo protagonista, en el acento
        { geo: new T.CylinderGeometry(0.112, 0.112, 0.006, 24).translate(0, 0.218, 0), color: tonos.acento.clone(), luz: noche ? 0.45 : 0.15 },
        // el vapor: dos hilos en S que suben desde el café y se adelgazan
        { geo: hilo(T, [[0.02, 0.23, -0.02], [0.05, 0.3, -0.03], [-0.02, 0.38, -0.01], [0.03, 0.46, 0.01], [0.0, 0.55, 0.0]], 0.014), color: vapor, luz: noche ? 0.4 : 0 },
        { geo: hilo(T, [[-0.03, 0.23, 0.03], [-0.06, 0.29, 0.02], [0.0, 0.35, 0.04], [-0.04, 0.42, 0.03], [-0.01, 0.48, 0.05]], 0.01), color: vapor, luz: noche ? 0.3 : 0 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
