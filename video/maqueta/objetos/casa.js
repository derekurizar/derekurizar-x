// Objeto «casa» (ficha: casa.json): una casa de un nivel con techo de dos aguas (8 × 7 m). Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor,
// flujo) con ctx.flota: las partes con `tinte` toman el color de la instancia (una de `variantes`, por semilla); `luz` = parte
// que brilla sola (faros, ventanas de noche). Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  MAQ.OBJETOS.casa = {
    medidas: { largo_m: 8.0, ancho_m: 7.0, alto_m: 5.4 },
    variantes(ctx) { const t = ctx.tonos; return [t.muro.clone().lerp(t.secundario, 0.3), t.techo.clone(), t.muro.clone().lerp(t.techo, 0.6), t.secundario.clone().multiplyScalar(0.7)]; },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), teja = tonos.linea.clone().lerp(tonos.acento, 0).lerp(tonos.techo, 0.45);
      const s = new T.Shape(); s.moveTo(-3.8, 0); s.lineTo(3.8, 0); s.lineTo(0, 2.4); s.lineTo(-3.8, 0);
      const techo = new T.ExtrudeGeometry(s, { depth: 8.6, bevelEnabled: false }).translate(0, 0, -4.3).rotateY(Math.PI / 2).translate(0, 3.0, 0);
      return [
        { geo: B(T, 8, 3, 7, 0, 0, 0), color: blanco, tinte: true },
        { geo: techo, color: teja },
        { geo: B(T, 0.06, 1.0, 1.0, 4.0, 1.2, -1.8), color: lin(COL.luces).multiplyScalar(ES.noche ? 1 : 0.4), luz: ES.noche ? 1 : 0 },
        { geo: B(T, 0.06, 1.0, 1.0, 4.0, 1.2, 1.8), color: lin(COL.luces).multiplyScalar(ES.noche ? 1 : 0.4), luz: ES.noche ? 1 : 0 },
      ];
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
