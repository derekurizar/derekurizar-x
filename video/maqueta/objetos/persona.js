// Objeto «persona» (ficha: persona.json): una persona de pie (1.75 m), ARTICULADA para caminar. Low-poly con primitivas de
// three.js, en METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan las piezas que lo
// `usa`n (actor, flujo, beneficio) con ctx.flota: las partes con `tinte` (camisa y mangas) toman el color de la instancia (una
// de `variantes`, por semilla). Sin colores escritos: todo sale de ctx.tonos, ctx.COL y ctx.lin.
// ARTICULADO (2026-11-16): grupos `pierna_d`, `pierna_i` (pivote en la cadera) y `brazo_d`, `brazo_i` (pivote en el hombro);
// el torso, la cadera y la cabeza quedan rígidos. `pose(t, i)` es una función pura de t: un paso de 0.9–1.1 s (el ciclo de
// dos pasos dura el doble), desfasado por instancia con ctx.hash(i); cada pierna se balancea ±16° y el brazo contrario ±13°.
// La pose no conoce la velocidad del que la lleva: el balanceo es moderado para que, de pie, se lea como quien cambia el peso
// y no como quien corre (no hay variante quieta: ver `nucleo` del constructor).
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const CADERA = 0.88, HOMBRO = 1.4, PZ = 0.095, HZ = 0.255, PIERNA = 0.28, BRAZO = 0.23;
  MAQ.OBJETOS.persona = {
    medidas: { largo_m: 0.5, ancho_m: 0.5, alto_m: 1.75 },
    grupos: {
      pierna_d: { pivote: [0, CADERA, PZ] },
      pierna_i: { pivote: [0, CADERA, -PZ] },
      brazo_d: { pivote: [0, HOMBRO, HZ] },
      brazo_i: { pivote: [0, HOMBRO, -HZ] },
    },
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1);
      const oscuro = tonos.linea.clone().lerp(tonos.muro, 0.5);
      const piel = ES && ES.dia && lin && COL ? lin(COL.tierra_media).lerp(tonos.secundario, 0.28) : tonos.secundario.clone().lerp(tonos.techo, 0.4);
      const zapato = oscuro.clone().multiplyScalar(0.7);
      const P = [
        // CADERA (rígida): tapa el arranque de las piernas cuando se balancean
        { geo: B(T, 0.26, 0.14, 0.36, 0, CADERA - 0.1, 0), color: oscuro },
        // TORSO (rígido): camisa con su tinte y los hombros
        { geo: B(T, 0.28, HOMBRO - CADERA + 0.02, 0.4, 0, CADERA, 0), color: blanco, tinte: true },
        { geo: B(T, 0.22, 0.07, 0.46, 0, HOMBRO - 0.04, 0), color: blanco, tinte: true },
        // CABEZA (rígida): cuello y cabeza sin rostro (coronilla a 1.73 m)
        { geo: new T.CylinderGeometry(0.05, 0.055, 0.1, 8).translate(0, HOMBRO + 0.07, 0), color: piel },
        { geo: new T.SphereGeometry(0.13, 10, 8).translate(0, 1.6, 0), color: piel },
      ];
      // PIERNAS: pantalón y zapato, colgando desde la cadera
      for (const [g, z] of [["pierna_d", PZ], ["pierna_i", -PZ]]) P.push(
        { geo: B(T, 0.15, CADERA - 0.06, 0.14, 0, 0.06, z), color: oscuro, grupo: g },
        { geo: B(T, 0.25, 0.07, 0.13, 0.045, 0, z), color: zapato, grupo: g },
      );
      // BRAZOS: manga (tinte) y antebrazo con la mano (piel), colgando desde el hombro
      for (const [g, z] of [["brazo_d", HZ], ["brazo_i", -HZ]]) P.push(
        { geo: B(T, 0.1, 0.3, 0.1, 0, HOMBRO - 0.28, z), color: blanco, tinte: true, grupo: g },
        { geo: B(T, 0.08, 0.26, 0.08, 0, HOMBRO - 0.54, z), color: piel, grupo: g },
        { geo: B(T, 0.09, 0.08, 0.07, 0.005, HOMBRO - 0.62, z), color: piel, grupo: g },
      );
      return P;
    },
    // la pose en t (función pura): un paso de 0.9–1.1 s por instancia, con su fase; piernas en contrafase y cada brazo
    // con la pierna contraria (rz > 0 lleva el pie o la mano hacia adelante; rx abre un poco cada brazo hacia afuera)
    pose(t, i, ctx, est) {
      // con la velocidad de quien la lleva (est.vel, m/s; la pasa el actor): de pie no camina, y camina pleno desde ~0.5 m/s;
      // sin ella (una flota que no la pasa), el paso de siempre
      const vel = est && est.vel !== null && est.vel !== undefined ? est.vel : null, f = vel === null ? 1 : Math.min(1, vel / 0.5);
      const h = ctx.hash, paso = 0.9 + 0.2 * h(i, 81), s = f * Math.sin(2 * Math.PI * (t / (2 * paso) + h(i, 82)));
      const a = PIERNA * (0.9 + 0.2 * h(i, 83)) * s, b = BRAZO * (0.9 + 0.2 * h(i, 84)) * s;
      return {
        pierna_d: [0, 0, a],
        pierna_i: [0, 0, -a],
        brazo_d: [-0.04, 0, -b],
        brazo_i: [0.04, 0, b],
      };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
