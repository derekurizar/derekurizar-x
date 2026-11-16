// Objeto «contenedor» (ficha: contenedor.json): un contenedor marítimo de 20 pies (6.06 × 2.44 × 2.59 m) con el acanalado
// de los costados y del frente, el marco de esquineros y largueros, y las dos puertas al fondo con sus barras de cierre.
// Low-poly con primitivas de three.js, en METROS (x adelante: el frente ciego; las puertas en −x; y arriba; z a su derecha;
// el origen en el suelo, al centro). Todo va con `tinte`: el color de la instancia (una de `variantes`, por la `variante` del
// actor; el protagonista, en el acento) multiplicado por un gris que separa el panel, la costilla, el marco y la puerta.
// Sin logos ni texto. Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const L = 6.06, A = 2.44, H = 2.59, hl = L / 2, ha = A / 2;
  MAQ.OBJETOS.contenedor = {
    medidas: { largo_m: L, ancho_m: A, alto_m: H },
    variantes(ctx) {
      const t = ctx.tonos, C = (k) => ctx.lin(ctx.COL[k]);
      return [t.mal.clone().multiplyScalar(0.8), t.secundario.clone().multiplyScalar(0.85), t.medio.clone().multiplyScalar(0.85),
        t.linea.clone().lerp(C("costa"), 0.45), t.bien.clone().multiplyScalar(0.75), C("costa").multiplyScalar(0.92)];
    },
    partes(ctx) {
      const { THREE: T } = ctx, g = (v) => new T.Color(v, v, v);
      const panel = g(0.9), costilla = g(1.0), marco = g(0.62), puerta = g(0.82), barra = g(0.5);
      const P = [], add = (geo, c) => P.push({ geo, color: c, tinte: true });
      // la caja: el panel un poco hundido para que el acanalado y el marco sobresalgan
      add(B(T, L - 0.16, H - 0.2, A - 0.08, 0, 0.1, 0), panel);
      // el marco: cuatro esquineros, los largueros de arriba y de abajo, y los cabezales de cada extremo
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) add(B(T, 0.16, H, 0.16, sx * (hl - 0.08), 0, sz * (ha - 0.08)), marco);
      for (const sz of [-1, 1]) for (const y of [0, H - 0.16]) add(B(T, L, 0.16, 0.14, 0, y, sz * (ha - 0.07)), marco);
      for (const sx of [-1, 1]) for (const y of [0, H - 0.16]) add(B(T, 0.14, 0.16, A, sx * (hl - 0.07), y, 0), marco);
      // el acanalado: costillas verticales en los dos costados (cada 0.28 m) y en el frente ciego
      const nc = Math.floor((L - 0.4) / 0.28);
      for (let k = 0; k <= nc; k++) {
        const x = -hl + 0.2 + k * ((L - 0.4) / nc);
        if (k % 2) continue;                                   // costilla y valle alternados
        for (const sz of [-1, 1]) add(B(T, 0.14, H - 0.34, 0.06, x, 0.17, sz * (ha - 0.01)), costilla);
      }
      for (let k = 0; k < 4; k++) add(B(T, 0.06, H - 0.34, 0.16, hl - 0.01, 0.17, -0.75 + k * 0.5), costilla);
      // el techo, apenas abombado
      add(B(T, L - 0.3, 0.05, A - 0.3, 0, H - 0.1, 0), costilla);
      // las puertas al fondo (−x): dos hojas, la junta entre ellas, cuatro barras de cierre con sus manijas
      for (const sz of [-1, 1]) add(B(T, 0.05, H - 0.34, ha - 0.2, -hl - 0.005, 0.17, sz * (ha / 2 + 0.03)), puerta);
      add(B(T, 0.07, H - 0.34, 0.04, -hl - 0.02, 0.17, 0), barra);
      for (const z of [-0.85, -0.3, 0.3, 0.85]) {
        add(B(T, 0.08, H - 0.3, 0.05, -hl - 0.04, 0.15, z), barra);
        add(B(T, 0.1, 0.06, 0.18, -hl - 0.05, 1.05, z + 0.08), barra);
      }
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
