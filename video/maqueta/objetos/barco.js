// Objeto «barco» (ficha: barco.json): un buque portacontenedores de 180 × 28 m (casco con proa en punta, puente y chimenea a
// popa, bodegas de contenedores apilados en tres tonos) con una estela corta tras la popa. Low-poly con primitivas de three.js,
// en METROS (x adelante, y arriba, z a su derecha; el origen en la línea de flotación, al centro). Lo dibujan las piezas que lo
// `usa`n (actor) con ctx.flota: las pilas de contenedores con `tinte` toman el color de la instancia (una de `variantes`, por la
// `variante` del actor; el protagonista, en el acento) y las demás pilas van en dos tonos fijos. Sin colores escritos: todo sale
// de ctx.tonos y ctx.COL. Sin faros: de noche solo brillan las ventanas del puente.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  // una planta [[x, z], …] extruida de y0 a y1 (el casco con su proa, la estela)
  const planta = (T, pts, y0, y1) => {
    const s = new T.Shape(); pts.forEach(([x, z], i) => (i ? s.lineTo(x, -z) : s.moveTo(x, -z)));
    return new T.ExtrudeGeometry(s, { depth: y1 - y0, bevelEnabled: false }).rotateX(-Math.PI / 2).translate(0, y0, 0);
  };
  MAQ.OBJETOS.barco = {
    medidas: { largo_m: 180.0, ancho_m: 28.0, alto_m: 40.0 },
    variantes(ctx) {
      const t = ctx.tonos;
      return [t.mal.clone().multiplyScalar(0.72), t.medio.clone().multiplyScalar(0.72), t.secundario.clone().multiplyScalar(0.85), t.techo.clone()];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, blanco = new T.Color(1, 1, 1);
      const casco = tonos.linea.clone().lerp(tonos.muro, 0.55), fondo = tonos.mal.clone().lerp(tonos.muro, 0.6), cubierta = tonos.muro.clone();
      const puente = tonos.techo.clone().lerp(tonos.linea, 0.3), vidrio = tonos.linea.clone().lerp(lin(COL.luces), ES.modo === 1 ? 0.6 : 0.15);
      const fijoA = tonos.secundario.clone().multiplyScalar(0.85), fijoB = tonos.techo.clone().lerp(tonos.muro, 0.25);
      const espuma = tonos.agua.clone().lerp(tonos.techo, ES.modo === 1 ? 0.3 : 0.55);
      const P = [];
      // el casco: la banda de flotación y el costado, con la proa en punta y la popa recta
      const forma = (w) => [[-90, -w], [58, -w], [90, 0], [58, w], [-90, w]];
      P.push({ geo: planta(T, forma(14), -0.6, 3), color: fondo });
      P.push({ geo: planta(T, forma(14), 3, 11), color: casco });
      P.push({ geo: planta(T, forma(13.2), 11, 11.4), color: cubierta });
      // el puente a popa: el bloque, la franja de ventanas, las alas y la chimenea
      P.push({ geo: B(T, 14, 24, 24, -76, 11, 0), color: puente });
      P.push({ geo: B(T, 14.3, 1.6, 24.3, -76, 31, 0), color: vidrio, luz: ES.modo === 1 ? 0.6 : 0 });
      P.push({ geo: B(T, 6, 2.2, 32, -71, 33, 0), color: puente });
      P.push({ geo: B(T, 6, 9, 7, -86, 11, 0), color: casco });
      P.push({ geo: B(T, 5, 14, 5, -86, 20, 0), color: cubierta });
      // los contenedores: bahías de 12 m de proa a popa, dos pilas por bahía (babor y estribor) de 2 a 5 alturas
      for (let b = 0; b < 11; b++) {
        const x = -60 + b * 13.2, w = x > 52 ? 9 : 11.6;
        for (let lado = -1; lado <= 1; lado += 2) {
          const g = Math.floor(hash(b, lado + 7) * 3), alto = 2.6 * (2 + Math.floor(hash(b, lado + 11) * 4));
          P.push({ geo: B(T, 12, alto, w, x, 11.4, lado * (w / 2 + 0.5)), color: g === 0 ? blanco : g === 1 ? fijoA : fijoB, tinte: g === 0 });
        }
      }
      // la estela: una cuña de espuma tras la popa y dos bigotes a los lados de la proa
      P.push({ geo: planta(T, [[-90, -11], [-90, 11], [-165, 24], [-165, -24]], 0.5, 0.7), color: espuma, luz: 0.15 });
      P.push({ geo: planta(T, [[84, 2], [62, 16], [40, 19], [62, 14.5]], 0.5, 0.7), color: espuma, luz: 0.15 });
      P.push({ geo: planta(T, [[84, -2], [62, -16], [40, -19], [62, -14.5]], 0.5, 0.7), color: espuma, luz: 0.15 });
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
