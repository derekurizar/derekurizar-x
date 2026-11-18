// Objeto «carruaje» (ficha: carruaje.json): un carruaje de caballos genérico de fines del siglo XIX (una calesa de cuatro
// ruedas con la capota plegable alzada atrás), tirado por uno o dos caballos que trotan, con un cochero sin rostro en el
// pescante. En METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro): ≈ 7.2 m de la rueda trasera
// al hocico, 2 m de ancho. Genérico y sin afirmar el tipo exacto: caja de madera lacada (toma el color de la instancia:
// `tinte`, una de `variantes`; el protagonista, en el acento), pelaje de los caballos (`tinte2`, de `variantes2`), arreos
// de cuero, faroles a los lados del pescante que de noche se encienden (`luz`). Lo dibujan las piezas que lo `usa`n
// (actor, flujo) con ctx.flota.
// ARTICULADO (grupos con `padre`): `ruedaD` y `ruedaT` (los ejes: giran según la marcha), `caja` (la caja sobre sus
// ballestas: se mece) → `cochero` (rebota con el trote); por caballo (`a` y `b`): `cuerpo_*` (sube y baja con el trote) →
// `cabeza_*` (cabecea), `mdi_*`, `mdd_*`, `mti_*`, `mtd_*` (las cuatro patas: delantera/trasera, izquierda/derecha; pivote
// en la cruz o la cadera). Con un solo caballo (≈ 30 % de las semillas) el caballo `a` va al centro y el `b` no se ve.
// POSES (`est.pose`): `trote` (diagonales a la vez; por defecto si avanza a ≥ 2.2 m/s o si nadie da la velocidad), `paso`
// (cuatro tiempos; < 2.2 m/s) y `quieto` (≤ 0.3 m/s). Todo es función pura de t (y de la velocidad de quien lo lleva).
// Sin colores escritos: todo sale de ctx.tonos y ctx.COL.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const TAU = 2 * Math.PI;
  const fr = (x) => ((x % 1) + 1) % 1;
  // un cilindro de a a b (metros, ejes del objeto)
  const vara = (T, a, b, r0, r1, seg) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), l = d.length();
    const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize());
    return new T.CylinderGeometry(r1, r0, l, seg).applyQuaternion(q).translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  // medidas
  const RT = 0.72, XT = -2.9, ZT = 0.8;          // rueda trasera
  const RD = 0.5, XD = -0.9, ZD = 0.7;           // rueda delantera (bajo el pescante)
  const ZH = 0.62;                               // cada caballo del tronco, a ±ZH del timón
  const HX = 2.0, HY = 1.32;                     // centro del cuerpo del caballo
  const XM = 2.55, XC = 1.45, YP = 1.2, ZP = 0.17;   // patas: delanteras en XM, traseras en XC, pivote a YP
  const SEAT = 1.75, XS = -0.95;                 // el asiento del cochero
  const MANO = [-0.52, 2.02, 0.15];
  const PATAS = [["mdi", XM, -1], ["mdd", XM, 1], ["mti", XC, -1], ["mtd", XC, 1]];
  const grupos = {
    ruedaT: { pivote: [XT, RT, 0] },
    ruedaD: { pivote: [XD, RD, 0] },
    caja: { pivote: [-2.2, 0.9, 0] },
    cochero: { pivote: [XS, SEAT, 0], padre: "caja" },
  };
  for (const [c, zc] of [["a", -ZH], ["b", ZH]]) {
    grupos["cuerpo_" + c] = { pivote: [HX, HY, zc] };
    grupos["cabeza_" + c] = { pivote: [2.65, 1.55, zc], padre: "cuerpo_" + c };
    for (const [p, x, l] of PATAS) grupos[p + "_" + c] = { pivote: [x, YP, zc + l * ZP], padre: "cuerpo_" + c };
  }

  MAQ.OBJETOS.carruaje = {
    medidas: { largo_m: 7.2, ancho_m: 2.0, alto_m: 2.8 },
    cabecea: true,
    poses: ["trote", "paso", "quieto"],
    grupos,
    // la laca de la caja por instancia: negro, vino, verde botella, café y azul de tinta (de los tonos del estilo)
    variantes(ctx) {
      const t = ctx.tonos, noche = ctx.ES.noche;
      const base = noche ? t.muro.clone().lerp(t.techo, 0.25) : t.linea.clone().lerp(t.muro, 0.3);
      return [base, base.clone().lerp(t.mal, 0.4), base.clone().lerp(t.verde, 0.4), base.clone().lerp(t.techo, 0.45), base.clone().lerp(t.secundario, 0.35)];
    },
    // el pelaje de los caballos: castaño, alazán, tordo, negro y bayo
    variantes2(ctx) {
      const { tonos: t, lin, COL, ES } = ctx, k = ES.noche ? 1.25 : 1;
      return [
        t.techo.clone().lerp(t.mal, 0.2).multiplyScalar(0.72 * k),
        t.techo.clone().lerp(t.arena, 0.3).multiplyScalar(0.9 * k),
        t.arena.clone().lerp(t.muro, 0.45),
        t.linea.clone().lerp(t.muro, 0.25).multiplyScalar(k),
        lin(COL.tierra_media).lerp(t.arena, 0.4),
      ];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), noche = ES.noche;
      const gris = (v) => new T.Color(v, v, v);
      const madera = noche ? tonos.techo.clone().lerp(tonos.muro, 0.4) : tonos.arena.clone().lerp(tonos.techo, 0.6);
      const hierro = tonos.linea.clone().lerp(tonos.muro, 0.35), llanta = tonos.linea.clone();
      const cuero = noche ? tonos.techo.clone().lerp(tonos.linea, 0.3) : tonos.techo.clone().lerp(tonos.linea, 0.55);
      const tapiz = tonos.mal.clone().lerp(tonos.linea, noche ? 0.3 : 0.5);
      const capota = tonos.linea.clone().lerp(tonos.muro, noche ? 0.55 : 0.18);
      const crin = tonos.linea.clone().lerp(tonos.muro, noche ? 0.4 : 0.1), casco = tonos.linea.clone();
      const levita = tonos.linea.clone().lerp(tonos.secundario, noche ? 0.45 : 0.2), pantalon = levita.clone().multiplyScalar(0.85);
      const piel = ES.dia ? lin(COL.tierra_media).lerp(tonos.secundario, 0.28) : tonos.secundario.clone().lerp(tonos.techo, 0.4);
      const farol = lin(COL.luces);
      const P = [];
      // RUEDAS: llanta de hierro, pina de madera, doce rayos y el cubo, a cada lado del eje
      const rueda = (g, x, r, z) => {
        P.push({ geo: new T.TorusGeometry(r - 0.03, 0.035, 8, 32).translate(x, r, z), color: llanta, grupo: g },
          { geo: new T.TorusGeometry(r - 0.075, 0.03, 6, 32).scale(1, 1, 1.5).translate(x, r, z), color: madera, grupo: g },
          { geo: new T.CylinderGeometry(0.085, 0.1, 0.2, 14).rotateX(Math.PI / 2).translate(x, r, z), color: madera.clone().multiplyScalar(0.8), grupo: g },
          { geo: new T.CylinderGeometry(0.05, 0.05, 0.24, 12).rotateX(Math.PI / 2).translate(x, r, z), color: hierro, grupo: g });
        for (let k = 0; k < 12; k++) {
          const a = TAU * k / 12, l = r - 0.17;
          P.push({ geo: new T.BoxGeometry(l, 0.035, 0.03).translate(0.09 + l / 2, 0, 0).rotateZ(a).translate(x, r, z), color: madera, grupo: g });
        }
      };
      for (const z of [-ZT, ZT]) rueda("ruedaT", XT, RT, z);
      for (const z of [-ZD, ZD]) rueda("ruedaD", XD, RD, z);
      // EL TREN (no se mece): ejes, la viga, las ballestas elípticas, el timón y la volea
      P.push({ geo: new T.CylinderGeometry(0.04, 0.04, 2 * ZT, 12).rotateX(Math.PI / 2).translate(XT, RT, 0), color: hierro },
        { geo: new T.CylinderGeometry(0.04, 0.04, 2 * ZD, 12).rotateX(Math.PI / 2).translate(XD, RD, 0), color: hierro },
        { geo: vara(T, [XT, RT + 0.02, 0], [XD, RD + 0.05, 0], 0.05, 0.05, 10), color: madera.clone().multiplyScalar(0.75) },
        { geo: vara(T, [XD + 0.3, RD, 0], [3.25, 1.02, 0], 0.045, 0.035, 10), color: madera.clone().multiplyScalar(0.85) },
        { geo: vara(T, [0.05, 0.62, -1.0], [0.05, 0.62, 1.0], 0.035, 0.035, 10), color: madera.clone().multiplyScalar(0.85) });
      for (const [x, y] of [[XT, RT + 0.08], [XD, RD + 0.1]]) for (const z of [-0.5, 0.5])
        P.push({ geo: new T.TorusGeometry(0.28, 0.03, 6, 16).scale(1, 0.32, 1).translate(x, y + 0.08, z), color: hierro });
      // los estribos, a cada lado frente a la caja
      for (const z of [-0.7, 0.7]) P.push({ geo: B(T, 0.22, 0.03, 0.16, -1.35, 0.55, z), color: hierro },
        { geo: vara(T, [-1.35, 0.56, z], [-1.4, 0.95, z * 0.93], 0.015, 0.015, 8), color: hierro });

      // LA CAJA (se mece sobre las ballestas): tina abierta con zócalo, molduras, puertas, asientos tapizados y la capota alzada
      const CX0 = -3.35, CX1 = -1.3, CL = CX1 - CX0, CM = (CX0 + CX1) / 2, CW = 1.3, Y0 = 0.92, CH = 0.6;
      P.push(
        { geo: B(T, CL - 0.5, 0.18, CW - 0.2, CM + 0.05, Y0 - 0.16, 0), color: gris(0.7), tinte: true, grupo: "caja" },     // el vientre
        { geo: B(T, CL, 0.07, CW, CM, Y0, 0), color: gris(0.8), tinte: true, grupo: "caja" },                                // el piso
        { geo: B(T, CL, CH, 0.05, CM, Y0, -CW / 2), color: blanco, tinte: true, grupo: "caja" },
        { geo: B(T, CL, CH, 0.05, CM, Y0, CW / 2), color: blanco, tinte: true, grupo: "caja" },
        { geo: B(T, 0.05, CH + 0.1, CW, CX0, Y0, 0), color: blanco, tinte: true, grupo: "caja" },
        { geo: B(T, 0.05, CH - 0.15, CW, CX1, Y0, 0), color: blanco, tinte: true, grupo: "caja" },
      );
      // molduras (el borde de arriba y el zócalo) en un tono más claro de la laca, y las puertas con su marco
      for (const z of [-CW / 2, CW / 2]) {
        P.push({ geo: B(T, CL + 0.04, 0.05, 0.08, CM, Y0 + CH - 0.02, z), color: gris(1.25), tinte: true, grupo: "caja" },
          { geo: B(T, CL + 0.02, 0.06, 0.07, CM, Y0 + 0.02, z), color: gris(1.2), tinte: true, grupo: "caja" });
        const zs = z + Math.sign(z) * 0.03;
        for (const [dx, dy, l, h] of [[0, 0.1, 0.62, 0.035], [0, CH - 0.12, 0.62, 0.035], [-0.29, 0.1, 0.035, CH - 0.2], [0.29, 0.1, 0.035, CH - 0.2]])
          P.push({ geo: B(T, l, h, 0.02, -2.2 + dx, Y0 + dy, zs), color: gris(1.35), tinte: true, grupo: "caja" });
        P.push({ geo: B(T, 0.05, 0.03, 0.03, -2.42, Y0 + 0.32, zs + Math.sign(z) * 0.02), color: farol.clone().lerp(tonos.arena, 0.5), grupo: "caja" });
      }
      // los asientos: el de atrás con respaldo alto y el de enfrente, tapizados
      P.push({ geo: B(T, 0.55, 0.32, CW - 0.12, CX0 + 0.33, Y0 + 0.07, 0), color: tapiz, grupo: "caja" },
        { geo: B(T, 0.14, 0.5, CW - 0.12, CX0 + 0.1, Y0 + 0.35, 0), color: tapiz.clone().multiplyScalar(0.85), grupo: "caja" },
        { geo: B(T, 0.45, 0.28, CW - 0.12, CX1 - 0.28, Y0 + 0.07, 0), color: tapiz, grupo: "caja" },
        { geo: B(T, 0.09, 0.28, CW - 0.12, CX1 - 0.07, Y0 + 0.3, 0), color: tapiz.clone().multiplyScalar(0.85), grupo: "caja" });
      // la capota plegable, alzada atrás: un cuarto de cilindro de lona con sus costados y cuatro arcos de hierro
      { const R = 0.82, xc = CX0 + 0.65, yc = Y0 + CH, w = CW + 0.04;
        P.push({ geo: new T.CylinderGeometry(R, R, w, 20, 1, true, Math.PI, Math.PI / 2).rotateX(Math.PI / 2).translate(xc, yc, 0), color: capota, grupo: "caja" });
        P.push({ geo: new T.CircleGeometry(R, 16, Math.PI / 2, Math.PI / 2).translate(xc, yc, w / 2), color: capota.clone().multiplyScalar(0.85), grupo: "caja" });
        P.push({ geo: new T.CircleGeometry(R, 16, 0, Math.PI / 2).rotateY(Math.PI).translate(xc, yc, -w / 2), color: capota.clone().multiplyScalar(0.85), grupo: "caja" });
        for (let k = 0; k < 4; k++) { const a = Math.PI / 2 + (Math.PI / 2) * (k + 0.5) / 4;
          P.push({ geo: new T.CylinderGeometry(0.018, 0.018, w + 0.04, 8).rotateX(Math.PI / 2).translate(xc + R * Math.cos(a), yc + R * Math.sin(a), 0), color: hierro, grupo: "caja" }); }
        for (const z of [-w / 2 - 0.01, w / 2 + 0.01]) P.push({ geo: new T.TorusGeometry(R, 0.02, 5, 14, Math.PI / 2).rotateZ(Math.PI / 2).translate(xc, yc, z), color: hierro, grupo: "caja" },
          { geo: vara(T, [xc - 0.05, yc + 0.02, z], [xc + 0.45, yc - 0.05, z], 0.015, 0.015, 8), color: hierro, grupo: "caja" }); }
      // EL PESCANTE: la caja alta del cochero, su cojín, el respaldo bajo, el pescante de pies y el tablero curvo
      P.push({ geo: B(T, 0.6, 0.62, 1.1, XS, 1.02, 0), color: gris(0.9), tinte: true, grupo: "caja" },
        { geo: B(T, 0.64, 0.05, 1.16, XS, 1.62, 0), color: gris(1.25), tinte: true, grupo: "caja" },
        { geo: B(T, 0.5, 0.09, 0.95, XS + 0.02, 1.66, 0), color: tapiz, grupo: "caja" },
        { geo: B(T, 0.06, 0.22, 1.0, XS - 0.27, 1.66, 0), color: gris(0.9), tinte: true, grupo: "caja" },
        { geo: B(T, 0.42, 0.04, 0.9, -0.4, 1.12, 0), color: madera.clone().multiplyScalar(0.8), grupo: "caja" },
        { geo: vara(T, [-0.66, 1.02, 0], [-0.4, 1.12, 0], 0.03, 0.03, 8), color: hierro, grupo: "caja" },
        { geo: B(T, 0.035, 0.46, 0.92, 0, 0, 0).rotateZ(-0.35).translate(-0.12, 1.1, 0), color: cuero, grupo: "caja" });
      // los faroles, uno a cada lado del pescante: brazo, cuerpo, vidrio con luz y remate
      for (const z of [-0.6, 0.6]) {
        P.push({ geo: vara(T, [XS + 0.25, 1.35, z * 0.9], [XS + 0.3, 1.55, z], 0.015, 0.015, 8), color: hierro, grupo: "caja" },
          { geo: B(T, 0.13, 0.04, 0.13, XS + 0.3, 1.55, z), color: hierro, grupo: "caja" },
          { geo: B(T, 0.11, 0.17, 0.11, XS + 0.3, 1.59, z), color: farol, luz: noche ? 1 : 0.12, grupo: "caja" },
          { geo: new T.ConeGeometry(0.09, 0.1, 12).translate(XS + 0.3, 1.81, z), color: hierro, grupo: "caja" });
      }
      // EL COCHERO, sin rostro: levita, piernas al pescante de pies, sombrero de copa, brazos al frente con las riendas y la fusta
      P.push(
        { geo: B(T, 0.3, 0.14, 0.42, XS, SEAT - 0.02, 0), color: pantalon, grupo: "cochero" },
        { geo: B(T, 0.28, 0.58, 0.42, XS - 0.02, SEAT + 0.08, 0), color: levita, grupo: "cochero" },
        { geo: B(T, 0.3, 0.28, 0.46, XS - 0.03, SEAT - 0.05, 0), color: levita.clone().multiplyScalar(0.9), grupo: "cochero" },
        { geo: B(T, 0.22, 0.09, 0.5, XS - 0.02, SEAT + 0.6, 0), color: levita, grupo: "cochero" },
        { geo: new T.CylinderGeometry(0.05, 0.055, 0.08, 12).translate(XS - 0.02, SEAT + 0.68, 0), color: piel, grupo: "cochero" },
        { geo: new T.SphereGeometry(0.105, 16, 12).scale(1, 1.1, 0.95).translate(XS - 0.02, SEAT + 0.83, 0), color: piel, grupo: "cochero" },
        { geo: new T.CylinderGeometry(0.17, 0.17, 0.02, 18).translate(XS - 0.02, SEAT + 0.91, 0), color: crin, grupo: "cochero" },
        { geo: new T.CylinderGeometry(0.105, 0.1, 0.24, 16).translate(XS - 0.02, SEAT + 1.03, 0), color: crin, grupo: "cochero" },
        { geo: new T.CylinderGeometry(0.106, 0.106, 0.04, 16).translate(XS - 0.02, SEAT + 0.94, 0), color: tapiz, grupo: "cochero" },
      );
      for (const z of [-0.11, 0.11]) P.push(
        { geo: vara(T, [XS, SEAT + 0.05, z], [-0.58, SEAT + 0.08, z], 0.07, 0.065, 10), color: pantalon, grupo: "cochero" },
        { geo: vara(T, [-0.58, SEAT + 0.08, z], [-0.45, 1.16, z], 0.06, 0.05, 10), color: pantalon, grupo: "cochero" },
        { geo: B(T, 0.22, 0.07, 0.11, -0.4, 1.14, z), color: casco, grupo: "cochero" });
      for (const z of [-0.2, 0.2]) {
        const h = [XS - 0.02, SEAT + 0.58, z], c = [XS + 0.12, SEAT + 0.3, z * 1.05], m = [MANO[0], MANO[1], Math.sign(z) * MANO[2]];
        P.push({ geo: vara(T, h, c, 0.06, 0.055, 10), color: levita, grupo: "cochero" },
          { geo: vara(T, c, m, 0.05, 0.045, 10), color: levita, grupo: "cochero" },
          { geo: new T.SphereGeometry(0.045, 10, 8).translate(...m), color: piel, grupo: "cochero" });
      }
      P.push({ geo: vara(T, [MANO[0], MANO[1], MANO[2]], [MANO[0] + 0.55, MANO[1] + 1.05, MANO[2] + 0.12], 0.012, 0.006, 8), color: madera.clone().multiplyScalar(0.6), grupo: "cochero" });

      // LOS CABALLOS (`a` a babor, `b` a estribor): cuerpo, grupa y pecho, cuello, cabeza, orejas, crin, cola, collera,
      // sufra, riendas y tirantes; cuatro patas con antebrazo, caña, menudillo y casco
      for (const [c, zc] of [["a", -ZH], ["b", ZH]]) {
        const g = "cuerpo_" + c, gc = "cabeza_" + c;
        P.push(
          { geo: new T.CapsuleGeometry(0.34, 1.0, 6, 16).rotateZ(Math.PI / 2).scale(1, 1, 0.82).translate(HX, HY, zc), color: blanco, tinte2: true, grupo: g },
          { geo: new T.SphereGeometry(0.37, 16, 12).scale(1, 1, 0.85).translate(1.45, HY + 0.05, zc), color: blanco, tinte2: true, grupo: g },
          { geo: new T.SphereGeometry(0.34, 16, 12).scale(1, 1.05, 0.8).translate(2.5, HY + 0.02, zc), color: blanco, tinte2: true, grupo: g },
          { geo: vara(T, [1.12, HY + 0.2, zc], [0.95, 0.7, zc], 0.09, 0.05, 10), color: crin, grupo: g },
          { geo: new T.TorusGeometry(0.33, 0.06, 8, 18).scale(1, 1.0, 0.8).rotateY(Math.PI / 2).translate(2.1, HY, zc), color: cuero, grupo: g },
          { geo: B(T, 0.3, 0.05, 0.5, 2.1, HY + 0.32, zc), color: cuero, grupo: g },
          // las riendas, de la boca a las manos del cochero, y los tirantes de la collera a la volea
          { geo: vara(T, [3.25, 1.88, zc], [MANO[0], MANO[1], Math.sign(zc) * MANO[2]], 0.012, 0.012, 6), color: cuero, grupo: g },
          { geo: vara(T, [2.6, HY - 0.02, zc - 0.3], [0.05, 0.64, zc - 0.3], 0.018, 0.018, 6), color: cuero, grupo: g },
          { geo: vara(T, [2.6, HY - 0.02, zc + 0.3], [0.05, 0.64, zc + 0.3], 0.018, 0.018, 6), color: cuero, grupo: g },
        );
        P.push(
          { geo: vara(T, [2.55, 1.42, zc], [3.0, 1.98, zc], 0.22, 0.14, 14), color: blanco, tinte2: true, grupo: gc },
          { geo: B(T, 0.6, 0.06, 0.06, 0, 0, 0).rotateZ(0.9).translate(2.78, 1.66, zc), color: crin, grupo: gc },
          { geo: vara(T, [2.97, 2.02, zc], [3.36, 1.7, zc], 0.12, 0.085, 14), color: blanco, tinte2: true, grupo: gc },
          { geo: new T.SphereGeometry(0.095, 12, 10).scale(1.1, 1, 0.9).translate(3.39, 1.67, zc), color: crin.clone().lerp(tonos.techo, 0.3), grupo: gc },
          { geo: new T.TorusGeometry(0.29, 0.06, 8, 16).scale(1, 1.15, 0.9).rotateY(Math.PI / 2).rotateZ(-0.75).translate(2.68, 1.55, zc), color: cuero, grupo: gc },
          { geo: new T.TorusGeometry(0.1, 0.015, 5, 14).rotateY(Math.PI / 2).rotateZ(-0.9).translate(3.15, 1.86, zc), color: cuero, grupo: gc },
        );
        for (const s of [-1, 1]) P.push(
          { geo: new T.ConeGeometry(0.035, 0.13, 8).translate(2.97, 2.13, zc + s * 0.06), color: blanco, tinte2: true, grupo: gc },
          { geo: B(T, 0.08, 0.07, 0.01, 3.13, 1.85, zc + s * 0.1), color: cuero, grupo: gc });
        for (const [p, x, l] of PATAS) {
          const gp = p + "_" + c, z = zc + l * ZP, del = x === XM, dx = del ? 0 : -0.05;
          P.push(
            { geo: vara(T, [x, YP + 0.05, z], [x + dx, 0.62, z], del ? 0.1 : 0.13, 0.065, 12), color: blanco, tinte2: true, grupo: gp },
            { geo: vara(T, [x + dx, 0.62, z], [x + dx * 0.4, 0.17, z], 0.05, 0.045, 10), color: blanco, tinte2: true, grupo: gp },
            { geo: new T.SphereGeometry(0.06, 10, 8).translate(x + dx * 0.4, 0.17, z), color: blanco, tinte2: true, grupo: gp },
            { geo: new T.CylinderGeometry(0.06, 0.075, 0.12, 12).translate(x + dx * 0.4 + 0.02, 0.06, z), color: casco, grupo: gp });
        }
      }
      return P;
    },
    // la pose en t (pura): la marcha de los caballos, las ruedas que giran según la velocidad, la caja y el cochero que se mecen
    pose(t, i, ctx, est) {
      const E = est || {}, h = ctx.hash, vel = E.vel === undefined || E.vel === null ? null : Math.abs(E.vel);
      const nom = E.pose && typeof E.pose === "object" ? (E.pose.nombre || E.pose.pose) : E.pose;
      const quieto = nom === "quieto" || (!nom && vel !== null && vel <= 0.3);
      const v = quieto ? 0 : vel === null ? 3.5 : vel;
      const paso = !quieto && (nom === "paso" || (!nom && v < 2.2));
      const trote = !quieto && !paso;
      const uno = h(i, 71) < 0.3;
      // el ciclo de la marcha: trote ≈ 2.8 m por zancada; paso, 1.1 s
      const per = trote ? Math.max(0.5, Math.min(0.9, 2.8 / Math.max(0.1, v))) : 1.1;
      const u0 = fr(t / per + h(i, 72));
      const A = trote ? 0.42 : paso ? 0.24 : 0;
      const F = {};
      // fases por pata: trote en diagonales (mdi+mtd, mdd+mti); paso en cuatro tiempos
      const fase = trote ? { mdi: 0, mtd: 0, mdd: 0.5, mti: 0.5 } : { mti: 0, mdi: 0.25, mtd: 0.5, mdd: 0.75 };
      for (const [c, zc] of [["a", -ZH], ["b", ZH]]) {
        const d = c === "b" ? 0.03 : 0;                 // el segundo caballo, apenas desfasado
        const u = fr(u0 + d), bob = trote ? 0.04 * Math.cos(2 * TAU * u) : paso ? 0.012 * Math.cos(2 * TAU * u) : 0;
        const respira = quieto ? 0.008 * Math.sin(TAU * t / (3 + h(i, 73))) : 0;
        const dz = uno ? (c === "a" ? ZH : 0) : 0, k = uno && c === "b" ? 0 : 1;
        F["cuerpo_" + c] = [0, 0, (trote ? 0.02 : 0.008) * Math.sin(TAU * u), 0, bob + respira, dz, k];
        // la cabeza cabecea con la marcha; quieto, baja de vez en cuando
        const baja = quieto ? 0.15 * Math.max(0, Math.sin(TAU * (t / (7 + 2 * h(i, 74 + (c === "b" ? 1 : 0))) + h(i, 76)))) : 0;
        F["cabeza_" + c] = [0, 0, (trote ? -0.06 : -0.04) * Math.cos(2 * TAU * u) * (A > 0 ? 1 : 0) - baja, 0, 0, 0];
        for (const [p] of PATAS) {
          const w = TAU * fr(u + fase[p]), sw = A * Math.sin(w), alza = A > 0 ? Math.max(0, Math.cos(w)) * (trote ? 0.12 : 0.06) : 0;
          F[p + "_" + c] = [0, 0, sw, 0, alza, 0];
        }
      }
      // las ruedas: ángulo = recorrido / radio (hacia adelante, giro negativo en z)
      F.ruedaT = [0, 0, -(v * t) / RT - TAU * h(i, 77), 0, 0, 0];
      F.ruedaD = [0, 0, -(v * t) / RD - TAU * h(i, 78), 0, 0, 0];
      // la caja se mece sobre las ballestas y el cochero rebota con el trote
      const wc = TAU * t / (1.3 + 0.3 * h(i, 79)) + TAU * h(i, 80), m = trote ? 1 : paso ? 0.5 : 0.15;
      F.caja = [0.012 * m * Math.sin(wc), 0, 0.008 * m * Math.sin(2 * TAU * u0), 0, 0.012 * m * Math.abs(Math.sin(2 * TAU * u0)), 0];
      F.cochero = [0, 0, 0, 0, 0.018 * m * Math.abs(Math.sin(2 * TAU * u0 + 0.6)), 0];
      return F;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
