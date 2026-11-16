// Objeto «cliente» (ficha: cliente.json): una persona de ciudad (1.75 m) con un VASO DE CAFÉ para llevar en la mano
// derecha, ARTICULADA. Muñeco sin rostro, genérico (nunca el parecido de alguien): chaqueta con cuello (toma el color de la
// instancia: `tinte`), la camisa clara que asoma al frente, pantalón, zapatos y el pelo como un casquete. El vaso: claro,
// cónico, con funda de cartón a media altura y tapa con su domo; sin logo. Low-poly con primitivas de three.js, en METROS
// (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo `usa`n (actor, flujo)
// con ctx.flota. Sin colores escritos: todo sale de ctx.tonos, ctx.COL y ctx.lin.
// ARTICULADO: `pierna_d`, `pierna_i` (cadera), `brazo_i` (hombro) caminan como `persona` (con la velocidad que pasa el actor:
// de pie no se mueven); el brazo derecho es una cadena: `brazo_d` (hombro) → `antebrazo_d` (codo, padre brazo_d) →
// `mano_d` (muñeca, padre antebrazo_d; la mano y el vaso). Lleva el vaso derecho a la altura de la cintura y, cada 4–6 s
// (desfasado por instancia con ctx.hash(i)), lo sube a la boca en 0.7 s, sorbe 0.9 s y lo baja en 0.8 s; la `cabeza`
// (cuello) se echa un poco atrás al sorber. Sorbe también de pie. Pose = función pura de t.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const CADERA = 0.88, HOMBRO = 1.42, CUELLO = 1.47, PZ = 0.095, HZ = 0.25, PIERNA = 0.28, BRAZO = 0.23;
  const CODO = HOMBRO - 0.29, MUNECA = HOMBRO - 0.55;
  // el vaso en el marco de la mano: centro, eje a lo largo de +x (queda derecho cuando la mano gira +90° desde colgar)
  const VY = MUNECA - 0.07, VZ = HZ - 0.055, VL = 0.19;
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  // dos poses del brazo derecho (radianes; resueltas para que la tapa llegue a la boca): llevar y sorber
  const LLEVA = { brazo: [0, 0, 0.1], ante: [0, 0, 1.1], mano: [0, 0, Math.PI / 2 - 1.2] };
  const SORBE = { brazo: [0.2, 0, 0.7], ante: [0, 0.8, 2.3], mano: [0, 0, -1.0] };
  const mez = (a, b, r) => a.map((v, k) => v + (b[k] - v) * r);
  MAQ.OBJETOS.cliente = {
    medidas: { largo_m: 0.6, ancho_m: 0.6, alto_m: 1.75 },
    grupos: {
      pierna_d: { pivote: [0, CADERA, PZ] },
      pierna_i: { pivote: [0, CADERA, -PZ] },
      brazo_i: { pivote: [0, HOMBRO, -HZ] },
      brazo_d: { pivote: [0, HOMBRO, HZ] },
      antebrazo_d: { pivote: [0, CODO, HZ], padre: "brazo_d" },
      mano_d: { pivote: [0, MUNECA, HZ], padre: "antebrazo_d" },
      cabeza: { pivote: [0, CUELLO, 0] },
    },
    // la chaqueta por instancia: tonos de ropa de ciudad (marino, camello, gris, oliva, vino); nunca el acento
    variantes(ctx) {
      const { tonos, COL, lin, ES } = ctx;
      if (ES.dia) return [lin(COL.mar).lerp(tonos.linea, 0.6), lin(COL.tierra_alta).lerp(tonos.linea, 0.15),
        tonos.linea.clone().lerp(lin(COL.costa), 0.38), lin(COL.tierra_baja).lerp(tonos.linea, 0.35), tonos.techo.clone().lerp(tonos.linea, 0.45)];
      return tonos.vehiculos;
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), noche = ES.modo === 1;
      const piel = ES.dia ? lin(COL.tierra_media).lerp(tonos.secundario, 0.28) : tonos.secundario.clone().lerp(tonos.techo, 0.4);
      const pantalon = ES.dia ? tonos.linea.clone().lerp(lin(COL.mar), 0.3) : tonos.linea.clone().lerp(tonos.muro, 0.5);
      const zapato = tonos.linea.clone().lerp(tonos.muro, noche ? 0.3 : 0.08);
      const pelo = tonos.linea.clone().lerp(tonos.muro, noche ? 0.4 : 0.12);
      const camisa = ES.dia ? tonos.secundario.clone().lerp(lin(COL.costa), 0.5) : tonos.secundario.clone().lerp(tonos.muro, 0.3);
      const cierre = tonos.linea.clone().lerp(tonos.muro, 0.3);
      // el vaso: claro (loza de papel), la funda de cartón y la tapa apenas más gris
      const vaso = ES.dia ? tonos.secundario.clone().lerp(lin(COL.costa), 0.2)
        : noche ? tonos.secundario.clone().lerp(tonos.techo, 0.2) : tonos.secundario.clone().lerp(tonos.muro, 0.15);
      const funda = ES.dia ? lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.25)
        : noche ? lin(COL.luces).lerp(tonos.techo, 0.5).multiplyScalar(0.8) : tonos.arena.clone().lerp(tonos.linea, 0.2);
      const tapa = vaso.clone().multiplyScalar(0.84);
      const eje = (g) => g.rotateZ(-Math.PI / 2);                     // de y a +x: el fondo atrás, la tapa adelante
      const P = [
        // CHAQUETA (rígida): el cuerpo hasta medio muslo, los hombros y el cuello alto (tinte)
        { geo: B(T, 0.3, HOMBRO - CADERA + 0.16, 0.42, 0, CADERA - 0.14, 0), color: blanco, tinte: true },
        { geo: B(T, 0.24, 0.07, 0.48, 0, HOMBRO - 0.05, 0), color: blanco, tinte: true },
        { geo: new T.CylinderGeometry(0.085, 0.1, 0.07, 10).translate(0, HOMBRO + 0.03, 0), color: blanco, tinte: true },
        // la camisa que asoma al frente (la chaqueta abierta arriba) y el cierre que baja
        { geo: B(T, 0.02, 0.22, 0.1, 0.15, HOMBRO - 0.22, 0), color: camisa },
        { geo: B(T, 0.015, HOMBRO - CADERA - 0.06, 0.018, 0.152, CADERA - 0.14, 0), color: cierre },
      ];
      // CABEZA: cuello, cabeza sin rostro y el pelo (un casquete atrás y arriba); coronilla a 1.75 m
      P.push(
        { geo: new T.CylinderGeometry(0.05, 0.055, 0.09, 8).translate(0, CUELLO + 0.02, 0), color: piel, grupo: "cabeza" },
        { geo: new T.SphereGeometry(0.12, 12, 9).scale(1, 1.06, 0.95).translate(0, 1.61, 0), color: piel, grupo: "cabeza" },
        { geo: new T.SphereGeometry(0.128, 12, 9, 0, 2 * Math.PI, 0, 0.5 * Math.PI).scale(1, 0.95, 0.97).translate(-0.012, 1.632, 0), color: pelo, grupo: "cabeza" },
      );
      // PIERNAS: pantalón y zapato, colgando desde la cadera
      for (const [g, z] of [["pierna_d", PZ], ["pierna_i", -PZ]]) P.push(
        { geo: B(T, 0.15, CADERA - 0.06, 0.14, 0, 0.06, z), color: pantalon, grupo: g },
        { geo: B(T, 0.26, 0.07, 0.13, 0.045, 0, z), color: zapato, grupo: g },
      );
      // BRAZO IZQUIERDO: manga (tinte) y la mano
      P.push(
        { geo: B(T, 0.11, 0.56, 0.11, 0, HOMBRO - 0.56, -HZ), color: blanco, tinte: true, grupo: "brazo_i" },
        { geo: B(T, 0.085, 0.09, 0.07, 0.005, HOMBRO - 0.65, -HZ), color: piel, grupo: "brazo_i" },
      );
      // BRAZO DERECHO: manga hasta el codo, antebrazo con su puño, y la mano con el vaso
      P.push(
        { geo: B(T, 0.11, HOMBRO - CODO + 0.02, 0.11, 0, CODO - 0.02, HZ), color: blanco, tinte: true, grupo: "brazo_d" },
        { geo: B(T, 0.1, CODO - MUNECA + 0.01, 0.1, 0, MUNECA, HZ), color: blanco, tinte: true, grupo: "antebrazo_d" },
        { geo: B(T, 0.08, 0.1, 0.06, 0, MUNECA - 0.1, HZ + 0.005), color: piel, grupo: "mano_d" },
        // el vaso (cónico, más ancho arriba), la funda de cartón y la tapa con su domo
        { geo: eje(new T.CylinderGeometry(0.05, 0.04, VL, 14)).translate(0, VY, VZ), color: vaso, grupo: "mano_d" },
        { geo: eje(new T.CylinderGeometry(0.0505, 0.0465, 0.08, 14)).translate(0.01, VY, VZ), color: funda, grupo: "mano_d" },
        { geo: eje(new T.CylinderGeometry(0.054, 0.054, 0.02, 14)).translate(VL / 2 + 0.002, VY, VZ), color: tapa, grupo: "mano_d" },
        { geo: eje(new T.CylinderGeometry(0.034, 0.048, 0.018, 14)).translate(VL / 2 + 0.02, VY, VZ), color: vaso, grupo: "mano_d" },
      );
      return P;
    },
    // la pose en t (función pura): el paso como `persona` (escalado por la velocidad) y el sorbo cada 4–6 s
    pose(t, i, ctx, est) {
      const h = ctx.hash;
      const vel = est && est.vel !== null && est.vel !== undefined ? est.vel : null, f = vel === null ? 1 : Math.min(1, vel / 0.5);
      const paso = 0.9 + 0.2 * h(i, 81), s = f * Math.sin(2 * Math.PI * (t / (2 * paso) + h(i, 82)));
      const a = PIERNA * (0.9 + 0.2 * h(i, 83)) * s, b = BRAZO * (0.9 + 0.2 * h(i, 84)) * s;
      // el sorbo: periodo 4–6 s con su fase; sube 0.7 s, sorbe 0.9 s, baja 0.8 s
      const per = 4 + 2 * h(i, 91), q = ((((t / per) + h(i, 92)) % 1) + 1) % 1 * per;
      const r = q < 0.7 ? s3(q / 0.7) : q < 1.6 ? 1 : q < 2.4 ? 1 - s3((q - 1.6) / 0.8) : 0;
      const vaiven = 0.05 * s * (1 - r);                                  // el brazo del vaso apenas acompaña el paso
      const br = mez(LLEVA.brazo, SORBE.brazo, r);
      return {
        pierna_d: [0, 0, a],
        pierna_i: [0, 0, -a],
        brazo_i: [0.04, 0, b],
        brazo_d: [br[0], br[1], br[2] - vaiven],
        antebrazo_d: mez(LLEVA.ante, SORBE.ante, r),
        mano_d: mez(LLEVA.mano, SORBE.mano, r),
        cabeza: [0, 0, 0.16 * r],
      };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
