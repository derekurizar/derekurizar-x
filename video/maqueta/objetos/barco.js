// Objeto «barco» (ficha: barco.json): un buque portacontenedores de 180 × 28 m (casco con proa en punta, puente y chimenea a
// popa, bodegas de contenedores apilados en tres tonos) con su estela. Low-poly con primitivas de three.js, en METROS (x
// adelante, y arriba, z a su derecha; el origen en la línea de flotación, al centro). Lo dibujan las piezas que lo `usa`n
// (actor) con ctx.flota: las pilas de contenedores con `tinte` toman el color de la instancia (una de `variantes`, por la
// `variante` del actor; el protagonista, en el acento) y las demás pilas van en dos tonos fijos. Sin colores escritos: todo
// sale de ctx.tonos y ctx.COL. Sin faros: de noche solo brillan las ventanas del puente.
// ESTELA ARTICULADA (m271): tres grupos (`estela`: la V de dos brazos tras la popa; `lavado`: la espuma del centro;
// `bigotes`: las olas de proa) hechos de franjas cortas que se separan y adelgazan hacia atrás, con agua entre ellas.
// pose(t, i, ctx, est): la escala sale de est.vel (m/s): 0 hasta 0.3 (amarrado, sin estela) y crece suave hasta completa a
// 5 m/s; sin velocidad (null) va completa; la pose `sin_estela` la apaga siempre. Un vaivén lento, puro de t.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  // una planta [[x, z], …] extruida de y0 a y1 (el casco con su proa, la estela)
  const planta = (T, pts, y0, y1) => {
    const s = new T.Shape(); pts.forEach(([x, z], i) => (i ? s.lineTo(x, -z) : s.moveTo(x, -z)));
    return new T.ExtrudeGeometry(s, { depth: y1 - y0, bevelEnabled: false }).rotateX(-Math.PI / 2).translate(0, y0, 0);
  };
  MAQ.OBJETOS.barco = {
    poses: ["sin_estela"],
    grupos: { estela: { pivote: [-90, 0.5, 0] }, lavado: { pivote: [-90, 0.5, 0] }, bigotes: { pivote: [70, 0.5, 0] } },
    medidas: { largo_m: 180.0, ancho_m: 28.0, alto_m: 40.0 },
    variantes(ctx) {
      const t = ctx.tonos;
      return [t.mal.clone().multiplyScalar(0.72), t.medio.clone().multiplyScalar(0.72), t.secundario.clone().multiplyScalar(0.85), t.techo.clone()];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, blanco = new T.Color(1, 1, 1);
      const casco = tonos.linea.clone().lerp(tonos.muro, 0.55), fondo = tonos.mal.clone().lerp(tonos.muro, 0.6), cubierta = tonos.muro.clone();
      const puente = tonos.techo.clone().lerp(tonos.linea, 0.3), vidrio = tonos.linea.clone().lerp(lin(COL.luces), ES.noche ? 0.6 : 0.15);
      const fijoA = tonos.secundario.clone().multiplyScalar(0.85), fijoB = tonos.techo.clone().lerp(tonos.muro, 0.25);
      const P = [];
      // el casco: la banda de flotación y el costado, con la proa en punta y la popa recta
      const forma = (w) => [[-90, -w], [58, -w], [90, 0], [58, w], [-90, w]];
      P.push({ geo: planta(T, forma(14), -0.6, 3), color: fondo });
      P.push({ geo: planta(T, forma(14), 3, 11), color: casco });
      P.push({ geo: planta(T, forma(13.2), 11, 11.4), color: cubierta });
      // el puente a popa: el bloque, la franja de ventanas, las alas y la chimenea
      P.push({ geo: B(T, 14, 24, 24, -76, 11, 0), color: puente });
      P.push({ geo: B(T, 14.3, 1.6, 24.3, -76, 31, 0), color: vidrio, luz: ES.noche ? 0.6 : 0 });
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
      // la estela (grupos articulados): franjas de espuma que se abren tras la popa y se apagan hacia el agua. `rombo`: una
      // franja en [cx, cz], a lo largo de (ux, uz), de largo l y ancho w, delgada (no tapa el agua de alrededor)
      const costa = lin(COL.costa), base = ES.noche ? 0.4 : 0.62, lejos = Math.hypot;   // la espuma: el agua hacia el claro de la costa
      const espuma = (f) => tonos.agua.clone().lerp(costa, base * (1 - 0.55 * f));   // f: 0 junto al casco → 1 al final
      const LUZ = ES.noche ? 0.08 : 0.4;   // lo que emite no se tiñe con la hora: al atardecer queda espuma, no rosa
      const rombo = (cx, cz, ux, uz, l, w, y = 0.5) => {
        const n = lejos(ux, uz) || 1, ax = ux / n * l / 2, az = uz / n * l / 2, px = -uz / n * w / 2, pz = ux / n * w / 2;
        return planta(T, [[cx - ax, cz - az], [cx + px, cz + pz], [cx + ax, cz + az], [cx - px, cz - pz]], y, y + 0.12);
      };
      // la V tras la popa: dos brazos de 7 franjas cada uno, cada vez más abiertas, más cortas y más delgadas
      for (let lado = -1; lado <= 1; lado += 2) {
        for (let k = 0; k < 7; k++) {
          const f = k / 6, cx = -96 - k * 12 + (hash(k, lado + 31) - 0.5) * 2.5, cz = lado * (11 + k * 3.4);
          P.push({ geo: rombo(cx, cz, -12, lado * 3.4, 11 - 5 * f, 4 - 2.6 * f), color: espuma(f), luz: LUZ, grupo: "estela" });
        }
      }
      // el lavado del centro: manchas cortas a través de la popa que se angostan y se separan
      for (let k = 0; k < 6; k++) {
        const f = k / 5, cx = -97 - k * 12, cz = (hash(k, 41) - 0.5) * 5 * f;
        P.push({ geo: rombo(cx, cz, -1, 0.12 * (hash(k, 43) - 0.5), 10 - 4 * f, 15 - 9 * f, 0.52), color: espuma(0.2 + 0.8 * f), luz: LUZ, grupo: "lavado" });
      }
      // los bigotes de proa: tres trazos finos por lado que se abren desde el casco
      for (let lado = -1; lado <= 1; lado += 2) {
        const tramos = [[[83, 3.6], [66, 12.6]], [[63, 14.4], [50, 18.2]], [[47, 19.6], [37, 22.4]]];
        tramos.forEach(([[x0, z0], [x1, z1]], k) => {
          P.push({ geo: rombo((x0 + x1) / 2, lado * (z0 + z1) / 2, x1 - x0, lado * (z1 - z0), lejos(x1 - x0, z1 - z0), 2.4 - 0.6 * k),
            color: espuma(0.15 + 0.35 * k), luz: LUZ, grupo: "bigotes" });
        });
      }
      return P;
    },
    // la estela: cuánto se ve sale de la velocidad (continua) y un vaivén lento sale solo de t
    pose(t, i, ctx, est) {
      const E = est || {}, vel = E.vel === undefined ? null : E.vel;
      const nom = E.pose && typeof E.pose === "object" ? (E.pose.nombre || E.pose.pose) : E.pose;
      // 0 hasta 0.3 m/s (amarrado), completa desde 5 m/s, curva suave en medio; sin velocidad: completa
      const k = nom === "sin_estela" ? 0 : vel === null ? 1 : ctx.suave(0.3, 5, Math.abs(vel));
      const h = ctx.hash(i, 3) * 6.283, w = 6.283 * t / 7.5 + h;
      return {
        estela: [0, 0.018 * Math.sin(w), 0, -1.5 * (1 - Math.cos(w)) * k, 0, 0, k],
        lavado: [0, 0.03 * Math.sin(w * 1.3 + 1), 0, -2.0 * (1 - Math.cos(w * 1.3 + 1)) * k, 0, 0, k],
        bigotes: [0, 0, 0, 0.6 * Math.sin(w * 1.7) * k, 0, 0, k],
      };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
