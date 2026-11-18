// Objeto «volteo» (ficha: volteo.json): un camión de volteo genérico de dos ejes atrás (8.6 × 2.5 m, 3.3 m al visor) con la
// palangana (tolva) abierta llena de basura mezclada: bolsas de varios tonos, botellas tiradas y restos orgánicos sobre un
// relleno oscuro que asoma sobre las barandas. Sin logo, sin marca, sin rótulo: la cabina toma el color de la instancia
// (`tinte`, una de `variantes`; el protagonista, en el acento) y la palangana el segundo (`tinte2`: tonos de metal gastado).
// En METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro). Lo dibujan actor y flujo con ctx.flota.
// ARTICULADO (grupos): `cabina` (cabina, cofre, parrilla, espejos: se mece en la suspensión al rodar) · `tolva` (la palangana,
// pivote en la bisagra trasera: gira hasta 48° para volcar) → `compuerta` (la puerta trasera, colgada de su canto alto: queda
// vertical al subir la tolva) y `carga` (la basura de adentro: baja al vaciarse) · `piston0`…`piston3` (el cilindro telescópico
// de cuatro etapas entre el chasis y el frente de la tolva: apunta y se estira con ella) · `cae0`…`cae5` (bolsas y botellas que
// caen por detrás mientras vuelca) · `monton` (lo que se junta en el suelo detrás) · `humo0`…`humo4` (el escape: bocanadas).
// POSES (`est.pose`): `rodar` (por defecto: tolva abajo; se mece si avanza), `volcar` (una vez: sube la tolva desde t = 0.5 s,
// la basura cae y queda arriba), `volcando` (ciclo de 14 s contado desde t = 0: sube a 1–5 s, vacía, baja a 10–13 s; el montón
// crece ciclo a ciclo), `volcada` (ya arriba y vaciada, con el montón detrás). Todo es función pura de t (y de la velocidad que da quien lo lleva). Sin colores escritos.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  const fr = (x) => ((x % 1) + 1) % 1;
  const TAU = 2 * Math.PI;
  // la bisagra de la tolva, el pie del pistón y su enganche en el frente de la tolva (en reposo, justo encima del pie)
  const HX = -4.05, HY = 1.15, PX = 1.17, PY = 0.8, ETAPA = 1.45, NP = 4, AY = PY + ETAPA, TMAX = 48 * Math.PI / 180;
  const NC = 6, NH = 5, PH = 2.6;                          // grupos de basura que cae, bocanadas del escape y su ciclo
  const XE = 1.6, YE = 3.5, ZE = 0.98;                     // la boca del escape
  const RUEDA = (T, x, z, ancho) => new T.CylinderGeometry(0.52, 0.52, ancho, 16).rotateX(Math.PI / 2).translate(x, 0.52, z);
  const RIN = (T, x, z) => new T.CylinderGeometry(0.25, 0.25, 0.04, 12).rotateX(Math.PI / 2).translate(x, 0.52, z);
  // una bolsa de basura: esfera aplastada, con su nudo (un cono chico) si toca
  const BOLSA = (T, r, x, y, z, a, b) => new T.SphereGeometry(r, 9, 6).scale(1 + 0.25 * a, 0.62 + 0.2 * b, 1 - 0.15 * a).rotateY(a * 3).translate(x, y + r * 0.55, z);
  const NUDO = (T, r, x, y, z) => new T.ConeGeometry(r * 0.28, r * 0.5, 6).translate(x, y + r * 1.1 + r * 0.2, z);
  // una botella tendida: cuerpo y cuello, girada en el plano del suelo
  const BOTELLA = (T, x, y, z, giro, tumbo) => [
    new T.CylinderGeometry(0.055, 0.055, 0.24, 8).rotateZ(Math.PI / 2 + tumbo).rotateY(giro).translate(x, y + 0.06, z),
    new T.CylinderGeometry(0.022, 0.04, 0.09, 8).translate(0, 0.16, 0).rotateZ(Math.PI / 2 + tumbo).rotateY(giro).translate(x, y + 0.06, z),
  ];
  // el ángulo de la tolva (0–1), lo que cae (0–1), el montón del suelo (0–1) y la carga que queda (0–1) según la pose, en t
  function volcado(t, nom) {
    if (nom === "volcada") return { a: 1, f: 0, m: 1, c: 0.4 };
    if (nom === "volcando") {                       // ciclo de 14 s desde t = 0: espera, sube (1–5 s), vacía, baja (10–13 s)
      const n = Math.floor(t / 14), d = t - 14 * n;
      const a = d < 10 ? s3((d - 1) / 4) : 1 - s3((d - 10) / 3);
      const f = d < 3.6 ? 0 : d < 4.2 ? (d - 3.6) / 0.6 : d < 9.4 ? 1 : d < 10 ? 10 - d : 0;
      const p = s3((d - 3.6) / 6);                   // lo vaciado en este ciclo; el montón crece ciclo a ciclo (lleno al segundo)
      const m = Math.min(1, (n + p) / 2);
      const c = d < 10 ? 1 - 0.55 * p : 0.45 + 0.55 * s3((d - 10) / 4);
      return { a, f, m, c };
    }
    if (nom !== "volcar") return { a: 0, f: 0, m: 0, c: 1 };
    const d = t - 0.5;                               // una vez, desde t = 0.5 s, y queda arriba
    const a = s3(d / 4), m = s3((d - 3.1) / 6);
    const f = d < 3.1 ? 0 : d < 3.7 ? (d - 3.1) / 0.6 : d < 8.5 ? 1 : d < 9.5 ? 9.5 - d : 0;
    return { a, f, m, c: 1 - 0.6 * m };
  }
  const grupos = {
    cabina: { pivote: [2.4, 1.05, 0] },
    tolva: { pivote: [HX, HY, 0] },
    compuerta: { pivote: [-4.16, 2.52, 0], padre: "tolva" },
    carga: { pivote: [-1.6, 1.3, 0], padre: "tolva" },
    monton: { pivote: [-6.2, 0, 0] },
  };
  for (let k = 0; k < NP; k++) grupos["piston" + k] = k ? { pivote: [PX, PY, 0], padre: "piston" + (k - 1) } : { pivote: [PX, PY, 0] };
  for (let k = 0; k < NC; k++) grupos["cae" + k] = { pivote: [-5.0, 1.45, -0.8 + 0.32 * k] };
  for (let k = 0; k < NH; k++) grupos["humo" + k] = { pivote: [XE, YE, ZE] };

  MAQ.OBJETOS.volteo = {
    medidas: { largo_m: 8.6, ancho_m: 2.5, alto_m: 3.3 },
    cabecea: true,                       // sobre el relieve de una pieza se inclina con la pendiente (motor.js: flota)
    poses: ["rodar", "volcar", "volcando", "volcada"],
    faros: [[4.24, 1.2, -0.82], [4.24, 1.2, 0.82]], pilotos: [[-4.27, 0.82, -1.0], [-4.27, 0.82, 1.0]],
    grupos,
    variantes: (ctx) => ctx.tonos.vehiculos,
    // la palangana: metal pintado y gastado (nunca el acento), del estilo
    variantes2(ctx) {
      const { tonos, ES } = ctx, noche = ES.modo === 1;
      const base = noche ? tonos.muro.clone().lerp(tonos.techo, 0.3) : tonos.muro.clone().lerp(tonos.linea, 0.3);
      return [base, base.clone().lerp(tonos.arena, 0.35), base.clone().lerp(tonos.secundario, 0.3), base.clone().multiplyScalar(0.8), base.clone().lerp(tonos.mal, 0.2)];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, blanco = new T.Color(1, 1, 1);
      const noche = ES.modo === 1;
      const vidrio = tonos.linea.clone().lerp(tonos.techo, 0.25), llanta = tonos.linea.clone().multiplyScalar(0.85);
      const metal = tonos.linea.clone().lerp(tonos.techo, 0.55), chasis = tonos.linea.clone().lerp(tonos.muro, 0.35);
      const rin = tonos.techo.clone().lerp(tonos.arena, 0.3), cromo = tonos.techo.clone().lerp(lin(COL.luces), 0.15);
      const luzC = lin(COL.luces);
      const P = [];
      const pon = (geo, color, extra) => P.push(Object.assign({ geo, color }, extra || {}));
      // ── CHASIS (fijo): largueros, travesaños, subchasis bajo la tolva, bisagras, defensa trasera y loderas
      for (const z of [-0.45, 0.45]) pon(B(T, 8.3, 0.25, 0.12, 0, 0.75, z), chasis);
      for (const x of [-3.9, -2.4, -0.9, 0.6, 2.2, 3.7]) pon(B(T, 0.12, 0.16, 0.9, x, 0.8, 0), chasis);
      for (const z of [-0.45, 0.45]) pon(B(T, 4.9, 0.08, 0.16, -1.6, 0.98, z), chasis);
      for (const z of [-0.45, 0.45]) pon(new T.CylinderGeometry(0.09, 0.09, 0.22, 12).rotateX(Math.PI / 2).translate(HX, HY, z), metal);
      pon(B(T, 0.2, 0.2, 2.3, -4.15, 0.6, 0), chasis);
      for (const z of [-0.95, 0.95]) pon(B(T, 0.04, 0.68, 0.5, -3.75, 0.14, z), llanta);
      // ── RUEDAS: delantera sencilla y doble eje trasero con llantas dobles; rines y masas
      for (const z of [-1.05, 1.05]) { pon(RUEDA(T, 3.25, z, 0.32), llanta); pon(RIN(T, 3.25, z + Math.sign(z) * 0.16), rin); }
      for (const x of [-1.75, -3.05]) for (const z of [-1.07, -0.74, 0.74, 1.07]) pon(RUEDA(T, x, z, 0.3), llanta);
      for (const x of [-1.75, -3.05]) for (const z of [-1.07, 1.07]) pon(RIN(T, x, z + Math.sign(z) * 0.15), rin);
      for (const x of [-1.75, -3.05]) pon(new T.CylinderGeometry(0.08, 0.08, 1.6, 8).rotateX(Math.PI / 2).translate(x, 0.52, 0), chasis);
      // tanque de combustible, caja de baterías y estribos (fijos al chasis)
      pon(new T.CylinderGeometry(0.28, 0.28, 0.85, 14).rotateZ(Math.PI / 2).translate(2.2, 0.82, -0.88), cromo);
      pon(B(T, 0.6, 0.45, 0.42, 2.25, 0.6, 0.86), chasis);
      // ── LA CABINA (grupo, se mece): cabina, cofre, parrilla, defensa, guardafangos, vidrios, espejos, luces de techo
      const cab = { grupo: "cabina" };
      pon(B(T, 1.25, 2.0, 2.3, 2.38, 1.05, 0), blanco, { ...cab, tinte: true });
      pon(B(T, 1.4, 0.07, 2.36, 2.38, 3.05, 0), blanco, { ...cab, tinte: true });
      pon(B(T, 1.2, 1.05, 1.95, 3.6, 1.05, 0), blanco, { ...cab, tinte: true });
      pon(B(T, 1.1, 0.12, 1.75, 3.6, 2.1, 0), blanco, { ...cab, tinte: true });
      pon(B(T, 0.06, 0.95, 1.35, 4.22, 1.12, 0), chasis, cab);
      for (let k = 0; k < 5; k++) pon(B(T, 0.04, 0.05, 1.3, 4.26, 1.22 + k * 0.17, 0), metal, cab);
      pon(B(T, 0.22, 0.3, 2.42, 4.3, 0.74, 0), cromo, cab);
      for (const z of [-1.08, 1.08]) {
        pon(B(T, 1.25, 0.08, 0.36, 3.3, 1.12, z), blanco, { ...cab, tinte: true });
        pon(B(T, 0.4, 0.08, 0.36, 3.95, 1.0, z).rotateZ(0), blanco, { ...cab, tinte: true });
        pon(B(T, 0.75, 0.6, 0.03, 2.5, 2.25, z * 1.07), vidrio, { ...cab, luz: noche ? 0.25 : 0 });
        pon(B(T, 0.04, 0.22, 0.08, 2.15, 1.75, z * 1.075), metal, cab);                  // la manija
        pon(B(T, 0.5, 0.06, 0.4, 2.35, 0.62, z), metal, cab);                             // el estribo
        pon(B(T, 0.04, 0.04, 0.32, 3.02, 2.55, z * 1.13), metal, cab);                    // el brazo del espejo
        pon(B(T, 0.06, 0.42, 0.14, 3.02, 2.35, z * 1.27), chasis, cab);                   // el espejo
      }
      pon(B(T, 0.04, 0.62, 2.0, 3.02, 2.25, 0), vidrio, { ...cab, luz: noche ? 0.25 : 0 });
      pon(B(T, 0.06, 0.1, 2.32, 3.02, 2.92, 0), chasis, cab);
      for (const z of [-0.5, -0.25, 0, 0.25, 0.5]) pon(B(T, 0.08, 0.06, 0.1, 3.0, 3.12, z), luzC, { ...cab, luz: 0.8 });
      for (const z of [-0.82, 0.82]) pon(B(T, 0.05, 0.2, 0.36, 4.21, 1.1, z), luzC, { ...cab, luz: 1 });
      // el escape vertical detrás de la cabina, con su protector y su boca
      pon(new T.CylinderGeometry(0.075, 0.075, 2.5, 12).translate(XE, 1.0 + 1.25, ZE), metal);
      pon(new T.CylinderGeometry(0.11, 0.11, 0.8, 12).translate(XE, 2.2, ZE), cromo);
      pon(new T.CylinderGeometry(0.085, 0.075, 0.12, 12).translate(XE, YE - 0.04, ZE), chasis);
      // ── LA TOLVA (grupo): piso, costados con costillas y larguero, frente alto con visor sobre la cabina, enganche del pistón
      const tv = { grupo: "tolva", tinte2: true };
      pon(B(T, 5.08, 0.15, 2.42, -1.57, 1.15, 0), blanco, tv);
      for (const z of [-0.45, 0.45]) pon(B(T, 4.95, 0.1, 0.16, -1.6, 1.05, z), chasis, { grupo: "tolva" });
      for (const s of [-1, 1]) {
        pon(B(T, 5.08, 1.15, 0.07, -1.57, 1.3, s * 1.175), blanco, tv);
        pon(B(T, 5.16, 0.1, 0.15, -1.57, 2.45, s * 1.19), blanco, tv);
        pon(B(T, 5.08, 0.08, 0.06, -1.57, 1.85, s * 1.235), blanco, tv);
        pon(B(T, 5.08, 0.12, 0.06, -1.57, 1.18, s * 1.235), blanco, tv);
        for (let k = 0; k < 6; k++) pon(B(T, 0.08, 1.27, 0.06, -3.75 + k * 0.88, 1.2, s * 1.235), blanco, tv);
      }
      pon(B(T, 0.1, 1.95, 2.42, 0.92, 1.3, 0), blanco, tv);
      for (const z of [-0.8, 0, 0.8]) pon(B(T, 0.06, 1.95, 0.08, 0.99, 1.3, z), blanco, tv);
      pon(B(T, 1.2, 0.07, 2.42, 1.5, 3.2, 0), blanco, tv);                                   // el visor que cubre la cabina
      for (const z of [-1.1, 1.1]) pon(B(T, 1.2, 0.05, 0.06, 1.5, 3.15, z), blanco, tv);
      pon(B(T, 0.32, 0.18, 0.5, PX, AY - 0.1, 0), chasis, { grupo: "tolva" });             // el enganche del pistón
      // la compuerta trasera (grupo, cuelga de su canto alto) con sus dos refuerzos
      const cp = { grupo: "compuerta", tinte2: true };
      pon(B(T, 0.08, 1.3, 2.42, -4.15, 1.22, 0), blanco, cp);
      for (const y of [1.55, 2.05]) pon(B(T, 0.05, 0.08, 2.42, -4.21, y, 0), blanco, cp);
      for (const z of [-1.15, 1.15]) pon(B(T, 0.12, 0.12, 0.08, -4.15, 2.45, z), metal, cp);
      // ── LA CARGA (grupo): relleno oscuro de basura mezclada que asoma sobre las barandas, con bolsas, botellas y restos
      const sucio = noche ? tonos.linea.clone().lerp(tonos.muro, 0.45) : tonos.linea.clone().lerp(tonos.arena, 0.25);
      const bolsas = [
        tonos.linea.clone().multiplyScalar(0.7),                                   // negra
        tonos.linea.clone().lerp(tonos.muro, 0.3),                                 // negra gastada
        tonos.secundario.clone().lerp(tonos.techo, 0.2),                           // de color
        tonos.agua.clone().lerp(tonos.techo, 0.45),                                // celeste
        tonos.techo.clone().lerp(tonos.arena, 0.2),                                // blanca
        tonos.verde.clone().lerp(tonos.linea, 0.25),                               // verde
      ];
      const organico = [tonos.verde.clone().lerp(tonos.arena, 0.35), tonos.arena.clone().lerp(tonos.mal, 0.25), tonos.muro.clone().lerp(tonos.arena, 0.4)];
      const botella = tonos.agua.clone().lerp(tonos.techo, noche ? 0.3 : 0.6);
      const cg = { grupo: "carga" };
      pon(B(T, 4.85, 0.95, 2.28, -1.6, 1.3, 0), sucio, cg);
      // el lomo: dos cajas giradas que suben al centro (no una caja lisa)
      pon(new T.BoxGeometry(4.4, 0.4, 1.9).rotateX(0.05).translate(-1.65, 2.35, 0), sucio, cg);
      let n = 0;
      for (let i = 0; i < 8; i++) for (let j = 0; j < 4; j++) {
        const a = hash(n, 21), b = hash(n, 22), d = hash(n, 23), r = 0.2 + 0.12 * hash(n, 24);
        const x = -3.85 + i * 0.64 + (a - 0.5) * 0.25, z = -0.85 + j * 0.57 + (b - 0.5) * 0.2;
        const lomo = 0.28 * (1 - Math.abs(z) / 1.2) * (1 - Math.pow(Math.abs(x + 1.55) / 2.6, 2));
        const y = 2.22 + lomo + (d - 0.5) * 0.08;
        if (hash(n, 25) < 0.78) {
          const c = bolsas[Math.floor(hash(n, 26) * bolsas.length)];
          pon(BOLSA(T, r, x, y, z, a - 0.5, b), c, cg);
          if (hash(n, 27) < 0.45) pon(NUDO(T, r, x, y, z), c, cg);
        } else {
          pon(new T.DodecahedronGeometry(r * 0.75, 0).scale(1.2, 0.55, 1).rotateY(a * 3).translate(x, y + 0.1, z), organico[Math.floor(hash(n, 28) * 3)], cg);
        }
        n++;
      }
      for (let k = 0; k < 14; k++) {
        const x = -3.8 + 4.5 * hash(k, 31), z = -1.0 + 2.0 * hash(k, 32);
        const lomo = 0.28 * (1 - Math.abs(z) / 1.2) * (1 - Math.pow(Math.abs(x + 1.55) / 2.6, 2));
        for (const g of BOTELLA(T, x, 2.3 + lomo + 0.1 * hash(k, 33), z, hash(k, 34) * TAU, (hash(k, 35) - 0.5) * 0.6)) pon(g, botella, { ...cg, luz: noche ? 0.12 : 0 });
      }
      // ── EL PISTÓN telescópico (cuatro etapas, cada una más delgada, apiladas sobre el pie)
      for (let k = 0; k < NP; k++) {
        const r = 0.17 - 0.03 * k;
        pon(new T.CylinderGeometry(r, r, ETAPA, 14).translate(PX, PY + ETAPA / 2, 0), k ? cromo : chasis, { grupo: "piston" + k });
        pon(new T.CylinderGeometry(r + 0.02, r + 0.02, 0.08, 14).translate(PX, PY + ETAPA - 0.04, 0), chasis, { grupo: "piston" + k });
      }
      pon(B(T, 0.4, 0.14, 0.5, PX, PY - 0.08, 0), chasis);                              // el pie del pistón
      // ── LO QUE CAE (grupos cae0…cae5): una bolsa y a veces una botella, en el labio de la tolva; la pose las deja caer
      for (let k = 0; k < NC; k++) {
        const g = { grupo: "cae" + k }, z = -0.8 + 0.32 * k, r = 0.18 + 0.08 * hash(k, 41);
        pon(BOLSA(T, r, -5.0, 1.45 - r * 0.55, z, hash(k, 42) - 0.5, hash(k, 43)), bolsas[k % bolsas.length], g);
        if (hash(k, 44) < 0.6) for (const geo of BOTELLA(T, -5.0 + 0.25, 1.4, z + 0.15, hash(k, 45) * TAU, 0.3)) pon(geo, botella, g);
      }
      // ── EL MONTÓN del suelo detrás (grupo): un lomo de relleno con bolsas y botellas encima; la pose lo hace crecer
      const mg = { grupo: "monton" };
      pon(new T.SphereGeometry(1.0, 14, 7, 0, TAU, 0, Math.PI / 2).scale(1.5, 0.55, 1.35).translate(-6.2, 0, 0), sucio, mg);
      for (let k = 0; k < 16; k++) {
        const ang = hash(k, 51) * TAU, rr = 1.25 * Math.sqrt(hash(k, 52)), x = -6.2 + Math.cos(ang) * rr * 1.3, z = Math.sin(ang) * rr * 1.1;
        const y = 0.55 * Math.max(0, 1 - (rr / 1.4) * (rr / 1.4)) - 0.05, r = 0.16 + 0.1 * hash(k, 53);
        pon(BOLSA(T, r, x, y, z, hash(k, 54) - 0.5, hash(k, 55)), hash(k, 56) < 0.8 ? bolsas[k % bolsas.length] : organico[k % 3], mg);
      }
      for (let k = 0; k < 8; k++) for (const geo of BOTELLA(T, -6.2 + 2.6 * (hash(k, 61) - 0.5), 0.05 + 0.25 * hash(k, 62), 2.2 * (hash(k, 63) - 0.5), hash(k, 64) * TAU, 0.2)) pon(geo, botella, mg);
      // ── EL HUMO del escape (grupos humo0…humo4): bocanadas que suben, se abren y se apagan
      const humo = noche ? tonos.muro.clone().lerp(tonos.techo, 0.35) : tonos.techo.clone().lerp(tonos.linea, 0.3);
      for (let k = 0; k < NH; k++) pon(new T.IcosahedronGeometry(0.16, 1).translate(XE, YE + 0.08, ZE), humo, { grupo: "humo" + k });
      return P;
    },
    // la pose en t (pura): el mecido al rodar, el volcado (tolva, compuerta, pistón, carga, lo que cae, el montón) y el humo
    pose(t, i, ctx, est) {
      const E = est || {}, h = ctx.hash, vel = E.vel === undefined || E.vel === null ? 0 : Math.abs(E.vel);
      const nom = E.pose && typeof E.pose === "object" ? (E.pose.nombre || E.pose.pose) : E.pose;
      const V = volcado(t, nom), th = TMAX * V.a;
      const kv = ctx.suave(0.3, 4, vel);                         // cuánto rueda (m/s): la cabina se mece y el humo se tiende
      const w = TAU * t / (0.9 + 0.3 * h(i, 71)) + h(i, 72) * TAU;
      const R = {
        cabina: [0.006 * Math.sin(w * 0.7) * kv, 0, 0.004 * Math.sin(w) * kv, 0, 0.018 * Math.sin(w * 1.3) * kv, 0],
        tolva: [0, 0, th, 0, 0.006 * Math.sin(w * 1.1 + 1) * kv * (1 - V.a), 0],
        compuerta: [0, 0, -th * 0.62],
        carga: [0, 0, 0, 0, 0, 0, Math.max(0.001, V.c)],
        monton: [0, 0, 0, 0, 0, 0, Math.max(0, V.m)],
      };
      // el pistón: del pie al enganche (que gira con la tolva), cada etapa sale un tercio de lo que falta
      const ax = PX - HX, ay = AY - HY, c = Math.cos(th), s = Math.sin(th);
      const qx = HX + ax * c - ay * s, qy = HY + ax * s + ay * c, dx = qx - PX, dy = qy - PY;
      const L = Math.hypot(dx, dy), sale = Math.max(0, L - ETAPA) / (NP - 1);
      R.piston0 = [0, 0, Math.atan2(-dx, dy)];
      for (let k = 1; k < NP; k++) R["piston" + k] = [0, 0, 0, 0, sale, 0];
      // lo que cae: del labio (que baja con la tolva) al suelo detrás, rodando; cada grupo con su desfase
      const lx = HX + (-0.05) * c - 0.3 * s, ly = HY + (-0.05) * s + 0.3 * c;   // el labio trasero, en t
      for (let k = 0; k < NC; k++) {
        const u = fr(t / (0.75 + 0.2 * h(k, 81)) + h(k, 82));
        const vive = V.f > 0 ? V.f : 0;
        R["cae" + k] = [0, 0, 4 * u, (lx - (-5.0)) - 0.25 - 0.9 * u, (ly - 1.45) - (ly - 0.15) * u * u, 0.15 * (h(k, 83) - 0.5) * u, vive > 0 ? (u < 0.9 ? 1 : (1 - u) * 10) * vive : 0];
      }
      // el humo: sube, se abre y se apaga; al rodar se tiende hacia atrás
      for (let k = 0; k < NH; k++) {
        const u = fr(t / PH + k / NH + h(i, 91));
        R["humo" + k] = [0, 0, 0, -(0.25 + 2.2 * kv) * u, (1.4 - 0.8 * kv) * u, 0.2 * Math.sin(TAU * (u + k * 0.37)), (0.5 + 1.6 * u) * (u < 0.75 ? 1 : (1 - u) / 0.25) * (0.75 + 0.25 * V.a)];
      }
      return R;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
