// Objeto «cosechador» (ficha: cosechador.json): una persona que cosecha café en la ladera, articulada (1.65 m hasta la
// coronilla, 1.74 m con el sombrero). Muñeco sin rostro, genérico: sombrero de ala ancha de paja, camisa (toma el color de
// la instancia: `tinte`), pantalón, botas y un costal de yute colgado AL COSTADO derecho de una correa que cruza el pecho
// hasta el hombro izquierdo. Low-poly con primitivas de three.js, en METROS (x adelante, y arriba, z a su derecha; el origen
// en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor, flujo) con ctx.flota.
// ARTICULADO: grupos `torso` (camisa, correa y costal; pivote en la cadera), `cabeza` (cuello, cabeza y sombrero; pivote en
// el cuello), `brazo_d` y `brazo_i` (pivote en cada hombro). `pose(t, i)` es una función pura de t: un ciclo de 1.8–2.4 s
// desfasado por instancia con ctx.hash(i): el brazo derecho sube a la rama de enfrente (a la altura del pecho y la cabeza),
// arranca con un tirón corto y baja al costal; el izquierdo sostiene la rama y apenas se mueve; el torso se inclina hacia
// adelante al alcanzar y la cabeza sigue a la mano (arriba en la rama, abajo y a la derecha en el costal). Los grupos no se
// anidan en el núcleo: el desplazamiento de hombros y cuello que causa la inclinación del torso se calcula aquí y viaja en
// [dx, dy, dz]. Sin colores escritos: todo sale de ctx.tonos, ctx.COL y ctx.lin.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const CADERA = 0.86, HOMBRO = 1.37, CUELLO = 1.43, HZ = 0.235, LBRAZO = 0.6;
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  MAQ.OBJETOS.cosechador = {
    medidas: { largo_m: 0.6, ancho_m: 0.7, alto_m: 1.74 },
    grupos: {
      torso: { pivote: [0, CADERA, 0] },
      cabeza: { pivote: [0, CUELLO, 0] },
      brazo_d: { pivote: [0, HOMBRO, HZ] },
      brazo_i: { pivote: [0, HOMBRO, -HZ] },
    },
    // la camisa por instancia: tonos de tela que se leen sobre el verde del cafetal (nunca el acento: ese es del protagonista)
    variantes(ctx) {
      const { tonos, COL, lin, ES } = ctx;
      if (ES.dia) return [tonos.secundario.clone().lerp(tonos.arena, 0.25), lin(COL.fondo).multiplyScalar(0.7),
        tonos.techo.clone(), lin(COL.tierra_alta).multiplyScalar(0.9), tonos.medio.clone().lerp(tonos.secundario, 0.35)];
      return tonos.vehiculos;
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), noche = ES.modo === 1;
      // piel, tela del pantalón, botas, yute y paja: todo del estilo
      const piel = ES.dia ? lin(COL.tierra_media).lerp(tonos.secundario, 0.28) : tonos.secundario.clone().lerp(tonos.techo, 0.4);
      const pantalon = ES.dia ? lin(COL.mar).lerp(tonos.linea, 0.55) : tonos.linea.clone().lerp(tonos.muro, 0.5);
      const bota = noche ? tonos.linea.clone().lerp(tonos.muro, 0.3) : tonos.linea.clone().lerp(tonos.muro, 0.12);
      const yute = noche ? lin(COL.luces).lerp(tonos.techo, 0.5).multiplyScalar(0.8)
        : ES.modo === 4 ? tonos.techo.clone().lerp(tonos.linea, 0.18) : tonos.arena.clone().lerp(tonos.linea, 0.12);
      const paja = noche ? lin(COL.luces).lerp(tonos.techo, 0.3)
        : ES.modo === 4 ? tonos.techo.clone() : lin(COL.luces).lerp(tonos.arena, 0.55);
      const cinta = paja.clone().multiplyScalar(0.55);
      const P = [
        // botas y piernas (rígidas: está de pie en el banco)
        { geo: B(T, 0.3, 0.14, 0.13, 0.04, 0, -0.1), color: bota },
        { geo: B(T, 0.3, 0.14, 0.13, 0.04, 0, 0.1), color: bota },
        { geo: B(T, 0.16, 0.74, 0.15, 0, 0.12, -0.1), color: pantalon },
        { geo: B(T, 0.16, 0.74, 0.15, 0, 0.12, 0.1), color: pantalon },
        // TORSO: la cadera (pantalón), la camisa (tinte), los hombros y el costal con su correa
        { geo: B(T, 0.24, 0.12, 0.38, 0, CADERA - 0.06, 0), color: pantalon, grupo: "torso" },
        { geo: B(T, 0.25, HOMBRO - CADERA + 0.04, 0.4, 0, CADERA + 0.02, 0), color: blanco, tinte: true, grupo: "torso" },
        { geo: B(T, 0.2, 0.08, 0.5, 0, HOMBRO - 0.05, 0), color: blanco, tinte: true, grupo: "torso" },
        // el costal: colgado al costado derecho, un poco adelante (ahí cae la mano), con su boca abierta (un borde más claro)
        { geo: B(T, 0.26, 0.36, 0.2, 0.07, 0.6, 0.33), color: yute, grupo: "torso" },
        { geo: B(T, 0.28, 0.04, 0.22, 0.07, 0.96, 0.33), color: yute.clone().multiplyScalar(1.15), grupo: "torso" },
      ];
      // la correa: del costal (derecha, abajo) al hombro izquierdo, cruzando el pecho por delante
      { const a = [0.135, 0.98, 0.3], b = [0.135, HOMBRO + 0.02, -0.18], dy = b[1] - a[1], dz = b[2] - a[2], L = Math.hypot(dy, dz);
        P.push({ geo: new T.BoxGeometry(0.02, L, 0.05).rotateX(Math.atan2(dz, dy)).translate(a[0], (a[1] + b[1]) / 2, (a[2] + b[2]) / 2),
                 color: yute.clone().multiplyScalar(0.7), grupo: "torso" }); }
      // CABEZA: cuello, cabeza (sin rostro), sombrero de ala ancha (ala, copa y cinta)
      P.push(
        { geo: new T.CylinderGeometry(0.05, 0.055, 0.08, 8).translate(0, CUELLO + 0.02, 0), color: piel, grupo: "cabeza" },
        { geo: new T.SphereGeometry(0.11, 10, 8).scale(1, 1.08, 0.95).translate(0, 1.535, 0), color: piel, grupo: "cabeza" },
        { geo: new T.CylinderGeometry(0.29, 0.29, 0.025, 16).translate(0, 1.6, 0), color: paja, grupo: "cabeza" },
        { geo: new T.CylinderGeometry(0.115, 0.135, 0.13, 12).translate(0, 1.675, 0), color: paja, grupo: "cabeza" },
        { geo: new T.CylinderGeometry(0.137, 0.137, 0.03, 12).translate(0, 1.626, 0), color: cinta, grupo: "cabeza" },
      );
      // BRAZOS: manga (tinte) y antebrazo con la mano (piel), colgando desde el hombro
      for (const [g, z] of [["brazo_d", HZ + 0.02], ["brazo_i", -HZ - 0.02]]) P.push(
        { geo: B(T, 0.11, 0.3, 0.11, 0, HOMBRO - 0.3, z), color: blanco, tinte: true, grupo: g },
        { geo: B(T, 0.085, LBRAZO - 0.3, 0.085, 0, HOMBRO - LBRAZO, z), color: piel, grupo: g },
        { geo: B(T, 0.1, 0.1, 0.07, 0.01, HOMBRO - LBRAZO - 0.08, z), color: piel, grupo: g },
      );
      return P;
    },
    // la pose en t (función pura): ciclo de 1.8–2.4 s por instancia, con su fase
    pose(t, i, ctx) {
      const h = ctx.hash, per = 1.8 + 0.6 * h(i, 71), u = (((t / per + h(i, 72)) % 1) + 1) % 1;
      // alcance 0–1: sube (0–0.34), en la rama (0.34–0.52), baja al costal (0.52–0.84), en el costal (0.84–1)
      const r = u < 0.34 ? s3(u / 0.34) : u < 0.52 ? 1 : u < 0.84 ? 1 - s3((u - 0.52) / 0.32) : 0;
      const tiron = u > 0.38 && u < 0.5 ? Math.sin(Math.PI * (u - 0.38) / 0.12) : 0;        // arranca: un tirón corto hacia abajo
      const suelta = u > 0.84 ? Math.sin(Math.PI * (u - 0.84) / 0.16) : 0;                  // suelta el grano en el costal
      const alto = 1.62 + 0.3 * h(i, 73);                                                    // la rama: entre el pecho y la cabeza
      const th = -0.07 - 0.17 * r - 0.04 * tiron;                                            // el torso, hacia adelante al alcanzar
      // dónde quedan hombros y cuello cuando el torso gira alrededor de la cadera (el núcleo no anida grupos)
      const sn = Math.sin(th), cs = Math.cos(th), mueve = (L) => [-L * sn, L * (cs - 1), 0];
      const [hx, hy] = mueve(HOMBRO - CADERA), [cx, cy] = mueve(CUELLO - CADERA);
      const brazoD = 0.32 + (alto - 0.32) * r - 0.22 * tiron + 0.08 * suelta;
      const brazoI = 1.2 + 0.08 * Math.sin(2 * Math.PI * u) + 0.05 * tiron;                 // sostiene la rama
      const mira = th + 0.08 + 0.42 * r - 0.38 * (1 - r);                                    // la cabeza sigue a la mano
      return {
        torso: [0, 0, th],
        cabeza: [0, -0.28 * (1 - r) - 0.06 * r, mira, cx, cy, 0],
        brazo_d: [-0.12 + 0.06 * r, 0, th + brazoD, hx, hy, 0],
        brazo_i: [0.1, 0, th + brazoI, hx, hy, 0],
      };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
