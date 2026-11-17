// Objeto «camionsacos» (ficha: camionsacos.json): un camión de plataforma de 9 × 2.5 m con barandas bajas y su carga de sacos
// de yute apilados en tres camas (18 + 16 + 12, en pirámide), para que la carga se lea cuando la cámara lo sigue de cerca
// (40–80 m). Low-poly con primitivas de three.js, en METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al
// centro). Lo dibujan las piezas que lo `usa`n (actor, flujo) con ctx.flota: la cabina toma el color de la instancia
// (`variantes`, o el acento si es el protagonista); los sacos van en tonos de yute que salen del estilo; `luz` = faros y
// pilotos. El acomodo de los sacos es fijo (ctx.hash), no cambia entre cuadros. Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const RUEDA = (T, x, z) => new T.CylinderGeometry(0.5, 0.5, 0.34, 10).rotateX(Math.PI / 2).translate(x, 0.5, z);
  // un saco tendido a lo ancho de la plataforma: una cápsula aplastada (0.62 de ancho, 1.06 de largo, 0.36 de grueso)
  const SACO = (T, x, y, z, giro) => new T.CapsuleGeometry(0.31, 0.44, 2, 8).rotateX(Math.PI / 2).scale(1, 0.58, 1)
    .rotateY(giro).translate(x, y + 0.18, z);
  MAQ.OBJETOS.camionsacos = {
    medidas: { largo_m: 9.0, ancho_m: 2.5, alto_m: 2.9 },
    cabecea: true,                       // sobre el relieve de una pieza se inclina con la pendiente (motor.js: flota)
    faros: [[4.45, 0.85, -0.95], [4.45, 0.85, 0.95]], pilotos: [[-4.3, 0.95, -1.05], [-4.3, 0.95, 1.05]],
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, blanco = new T.Color(1, 1, 1);
      const noche = ES.modo === 1, plano = ES.modo === 4;
      const vidrio = tonos.linea.clone().lerp(tonos.techo, 0.25), llanta = tonos.linea.clone();
      // la madera de la plataforma y las barandas: un tono del muro hacia la tierra
      const madera = noche ? tonos.muro.clone().lerp(tonos.techo, 0.35) : plano ? tonos.muro.clone() : tonos.muro.clone().lerp(tonos.arena, 0.55).multiplyScalar(0.8);
      const chasis = tonos.linea.clone().lerp(tonos.muro, 0.4);
      // el yute: de noche, la luz cálida apagada hacia el techo; de día, la arena del estilo; tres tonos para que se lea cada saco
      const yute = noche ? lin(COL.luces).clone().lerp(tonos.techo, 0.5).multiplyScalar(0.8)
        : plano ? tonos.techo.clone().lerp(tonos.linea, 0.18) : tonos.arena.clone().lerp(tonos.linea, 0.12);
      const sacos = [yute, yute.clone().multiplyScalar(0.84), yute.clone().lerp(tonos.secundario, 0.18)];
      const P = [
        // ruedas (eje delantero y doble eje trasero) y chasis
        ...[3.1, -2.3, -3.35].flatMap((x) => [{ geo: RUEDA(T, x, -1.06), color: llanta }, { geo: RUEDA(T, x, 1.06), color: llanta }]),
        { geo: B(T, 8.4, 0.32, 1.3, -0.05, 0.55, 0), color: chasis },
        // la cabina (toma el color de la instancia), su parabrisas y sus ventanas
        { geo: B(T, 1.95, 1.95, 2.4, 3.45, 0.62, 0), color: blanco, tinte: true },
        { geo: B(T, 0.06, 0.72, 2.1, 4.44, 1.62, 0), color: vidrio },
        { geo: B(T, 0.85, 0.6, 2.44, 3.65, 1.68, 0), color: vidrio },
        // faros y pilotos
        { geo: B(T, 0.08, 0.22, 0.4, 4.43, 0.75, -0.95), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.08, 0.22, 0.4, 4.43, 0.75, 0.95), color: lin(COL.luces), luz: 1 },
        { geo: B(T, 0.06, 0.3, 0.3, -4.27, 0.85, -1.05), color: tonos.mal, luz: 0.6 },
        { geo: B(T, 0.06, 0.3, 0.3, -4.27, 0.85, 1.05), color: tonos.mal, luz: 0.6 },
        // la plataforma y la cabecera (la tabla alta detrás de la cabina)
        { geo: B(T, 6.55, 0.18, 2.5, -1.0, 0.9, 0), color: madera },
        { geo: B(T, 0.12, 1.45, 2.5, 2.2, 1.08, 0), color: madera },
      ];
      // las barandas: postes cada ~1.3 m y dos largueros por lado, y la compuerta de atrás; bajas, para que se vea la carga
      for (const z of [-1.21, 1.21]) {
        for (let i = 0; i < 6; i++) P.push({ geo: B(T, 0.1, 0.66, 0.1, -4.2 + i * 1.27, 1.08, z), color: madera });
        for (const y of [1.3, 1.62]) P.push({ geo: B(T, 6.45, 0.1, 0.08, -1.0, y, z), color: madera });
      }
      for (const y of [1.3, 1.62]) P.push({ geo: B(T, 0.08, 0.1, 2.5, -4.22, y, 0), color: madera });
      // los sacos: tres camas en pirámide (9, 8 y 6 a lo largo, dos a lo ancho), cada cama corrida medio saco sobre la de abajo
      const camas = [[9, -3.8, 1.08], [8, -3.46, 1.42], [6, -3.12, 1.76]];
      let n = 0;
      camas.forEach(([cuantos, x0, y], c) => {
        for (let i = 0; i < cuantos; i++) for (const z of [-0.55, 0.55]) {
          const a = hash(n, 11), b = hash(n, 12), d = hash(n, 13);
          P.push({ geo: SACO(T, x0 + i * 0.68 + (a - 0.5) * 0.08, y, z + (b - 0.5) * 0.08, (d - 0.5) * 0.22),
                   color: sacos[(c + Math.floor(hash(n, 14) * 3)) % 3] });
          n++;
        }
      });
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
