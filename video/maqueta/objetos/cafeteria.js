// Objeto «cafeteria» (ficha: cafeteria.json): el FRENTE de una cafetería GENÉRICA de una calle de ciudad en Estados Unidos
// (≈ 12 m de frente × 9 m de alto; nunca una marca: sin logo, sin texto, sin verde de marca). Un edificio de dos pisos de
// ladrillo con su cornisa clara; abajo la VITRINA grande con su luz cálida y, dentro, el mostrador con la máquina de espresso,
// el molino, la vitrina de panes, los vasos y las repisas, la pizarra del fondo (rayas, no letras) y tres lámparas colgantes;
// la puerta con su vidrio iluminado y dos apliques; sobre la vitrina, el LETRERO (una placa lisa con una taza en relieve) y el
// TOLDO de lona a rayas con su faldón festoneado. En la acera: dos mesitas con sus sillas, una tercera bajo una SOMBRILLA, la
// pizarra de menú de caballete (rayas de tiza, sin texto) y los maceteros. Arriba, tres ventanas al frente y dos al costado
// derecho (la esquina), y una unidad de aire en la azotea.
// ARTICULADO (referencias/diseno/maqueta3d.md, «Objetos articulados»): `faldon` (el borde del toldo) y `sombrilla` ondean muy
// poco; `lampara0`…`lampara2` (las colgantes de la vitrina) parpadean apenas. `pose(t, i)` es función pura de t con el desfase
// de la instancia (ctx.hash(i)). Lo demás es rígido.
// Las partes con `tinte` (las rayas del toldo, la sombrilla, el letrero, el zócalo de la vitrina y la puerta) toman el color de
// la instancia (una de `variantes`; el protagonista, en el acento). En METROS (x adelante = hacia la calle, y arriba, z a su
// derecha; el origen en el suelo, al centro de la planta con la terraza). Sin colores escritos: todo sale de ctx.tonos, ctx.COL
// y ctx.lin. Sin texto ni logos.
(function (MAQ) {
  const TAU = Math.PI * 2;
  // caja por rangos (x0..x1, y0..y1, z0..z1)
  const R = (T, x0, x1, y0, y1, z0, z1) => new T.BoxGeometry(x1 - x0, y1 - y0, z1 - z0).translate((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  // una barra de sección g × w entre dos puntos
  const barra = (T, a, b, g, w) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), n = d.length();
    return new T.BoxGeometry(n, g, w === undefined ? g : w).applyQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(1, 0, 0), d.normalize()))
      .translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  const cil = (T, r0, r1, h, x, y, z, n) => new T.CylinderGeometry(r0, r1, h, n || 12).translate(x, y + h / 2, z);   // base en y
  // la planta: el edificio de XB a XF (8 m de fondo) y la terraza hasta XE; de -ZL a ZL de frente
  const XF = 1.95, XB = XF - 8.0, XE = XF + 4.1, ZL = 6.0, MU = 0.3;
  const H1 = 4.3, HC = 8.55, HT = 9.05;                  // el entrepiso, la cornisa y el remate del muro
  const ZV0 = -5.0, ZV1 = 1.2, YV0 = 0.6, YV1 = 3.2;      // la vitrina
  const ZD0 = 2.0, ZD1 = 3.4, YD = 2.7;                   // la puerta
  const XI = XF - 3.4;                                    // el fondo del local (lo que se ve por la vitrina)
  const XC = XI + 1.15;                                   // el centro del mostrador
  // el toldo: del muro (YT0) a su borde (XT1, YT1); el faldón cuelga del borde
  const YT0 = 3.55, XT1 = XF + 1.9, YT1 = 2.85, FAL = 0.3, ZT0 = ZV0 - 0.3, ZT1 = ZD1 + 0.3;
  const LAMPS = [-3.9, -2.2, -0.5].map((z) => [XC + 0.15, 2.5, z]);
  // la sombrilla, sobre la mesa de la esquina
  const SOM = [XF + 2.1, 0, 5.0], YS = 2.35;
  const grupos = {
    faldon: { pivote: [XT1, YT1, 0] },
    sombrilla: { pivote: [SOM[0], YS, SOM[2]] },
  };
  LAMPS.forEach((p, k) => { grupos["lampara" + k] = { pivote: p.slice() }; });

  MAQ.OBJETOS.cafeteria = {
    medidas: { largo_m: 12.1, ancho_m: 13.0, alto_m: 9.7 },
    grupos,
    // el toldo, la sombrilla, el letrero y la carpintería: vino, azul marino, café, carbón o mostaza (nunca verde de marca)
    variantes(ctx) {
      const { tonos, COL, lin, ES } = ctx;
      if (ES.modo === 1 || ES.modo === 4) return tonos.vehiculos.map((c) => c.clone());
      return [tonos.mal.clone().multiplyScalar(0.72), lin(COL.mar_hondo || COL.mar).multiplyScalar(0.62),
        lin(COL.tierra_media).multiplyScalar(0.8), tonos.linea.clone().lerp(lin(COL.costa), 0.22), tonos.medio.clone().multiplyScalar(0.82)];
    },
    pose(t, i, ctx) {
      const h = ctx.hash(i, 3), h2 = ctx.hash(i, 7);
      const P = {
        faldon: [0, 0, 0.045 * Math.sin(TAU * (0.55 * t + h)) + 0.018 * Math.sin(TAU * (1.35 * t + h2))],
        sombrilla: [0.012 * Math.sin(TAU * (0.42 * t + h2)), 0, 0.01 * Math.sin(TAU * (0.6 * t + h))],
      };
      for (let k = 0; k < LAMPS.length; k++) {
        // un parpadeo breve de vez en cuando (pulso agudo de un seno lento) sobre un temblor mínimo
        const u = Math.sin(TAU * (0.21 * t + ctx.hash(i * 7 + k, 11)));
        const pico = Math.pow(Math.max(0, u), 40);
        const s = 1 - 0.035 * (0.5 + 0.5 * Math.sin(TAU * (2.3 * t + k * 0.31))) - 0.3 * pico;
        P["lampara" + k] = [0, 0, 0, 0, 0, 0, s];
      }
      return P;
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, g = (v) => new T.Color(v, v, v), noche = ES.modo === 1;
      const P = [];
      const put = (geo, color, grupo, luz) => P.push({ geo, color, grupo, luz: luz || 0 });
      const tin = (geo, v = 1, grupo) => P.push({ geo, color: g(v), tinte: true, grupo });
      // los tonos (todos del estilo)
      const crema = lin(COL.costa);
      const ladrillo = tonos.techo.clone().lerp(tonos.muro, 0.12).multiplyScalar(0.92);
      const junta = ladrillo.clone().lerp(tonos.muro, 0.35).multiplyScalar(0.86);
      const claro = tonos.muro.clone().lerp(crema, 0.6);
      const oscuro = tonos.linea.clone().lerp(tonos.muro, 0.14);
      const vidrio = tonos.agua.clone().lerp(tonos.linea, 0.55);
      const calido = lin(COL.luces).lerp(tonos.medio, 0.38);
      const madera = tonos.arena.clone().lerp(tonos.linea, 0.42);
      const acero = crema.clone().lerp(tonos.linea, 0.32);
      const planta = tonos.verde.clone().multiplyScalar(0.9);
      const piso = tonos.pavimento.clone();
      const pan = lin(COL.tierra_media).lerp(tonos.medio, 0.3);

      // ── la ACERA: losa al frente y a lo largo del costado de la esquina, y el bordillo
      put(R(T, XF, XE, -0.02, 0.1, -ZL - 0.4, ZL + 1.0), piso);
      put(R(T, XB, XF, -0.02, 0.1, ZL, ZL + 1.0), piso);
      put(R(T, XE - 0.15, XE, -0.02, 0.13, -ZL - 0.4, ZL + 1.0), piso.clone().multiplyScalar(0.88));

      // ── el EDIFICIO: costados, fondo, muro alto del frente, azotea
      put(R(T, XB, XF, 0, HT, -ZL, -ZL + MU), ladrillo);
      put(R(T, XB, XF, 0, HT, ZL - MU, ZL), ladrillo);
      put(R(T, XB, XB + MU, 0, HT, -ZL, ZL), ladrillo);
      put(R(T, XF - MU, XF, H1, HT, -ZL, ZL), ladrillo);
      put(R(T, XB + MU, XF - MU, HT - 0.45, HT - 0.3, -ZL + MU, ZL - MU), tonos.asfalto);
      // la planta baja del frente: pilares y tramos alrededor de la vitrina y de la puerta
      put(R(T, XF - MU, XF, 0, H1, -ZL, ZV0), ladrillo);
      put(R(T, XF - MU, XF, YV1, H1, ZV0, ZV1), ladrillo);
      put(R(T, XF - MU, XF, 0, H1, ZV1, ZD0), ladrillo);
      put(R(T, XF - MU, XF, YD, H1, ZD0, ZD1), ladrillo);
      put(R(T, XF - MU, XF, 0, H1, ZD1, ZL), ladrillo);
      // las juntas del ladrillo (hiladas): muro alto, pilares y el costado de la esquina
      for (let y = 0.42; y < HC; y += 0.42) {
        if (y > H1 + 0.45) put(R(T, XF, XF + 0.012, y, y + 0.035, -ZL, ZL), junta);
        else if (y < H1 - 0.05) {
          put(R(T, XF, XF + 0.012, y, y + 0.035, -ZL, ZV0), junta);
          put(R(T, XF, XF + 0.012, y, y + 0.035, ZD1 + 0.08, ZL), junta);
          if (y > YD + 0.1 || y < 0) put(R(T, XF, XF + 0.012, y, y + 0.035, ZV1, ZD1), junta);
          else put(R(T, XF, XF + 0.012, y, y + 0.035, ZV1, ZD0 - 0.08), junta);
        }
        put(R(T, XB, XF, y, y + 0.035, ZL, ZL + 0.012), junta);
        put(R(T, XB, XF, y, y + 0.035, -ZL - 0.012, -ZL), junta);
      }
      // la cornisa clara (frente y costados) y la faja del entrepiso
      put(R(T, XF, XF + 0.38, HC, HC + 0.32, -ZL - 0.2, ZL + 0.2), claro);
      put(R(T, XB, XF, HC, HC + 0.32, ZL, ZL + 0.2), claro);
      put(R(T, XB, XF, HC, HC + 0.32, -ZL - 0.2, -ZL), claro);
      put(R(T, XF, XF + 0.5, HC + 0.32, HC + 0.42, -ZL - 0.25, ZL + 0.25), claro.clone().multiplyScalar(0.92));
      put(R(T, XF, XF + 0.14, H1 + 0.25, H1 + 0.45, -ZL, ZL), claro);
      // la unidad de aire en la azotea
      put(R(T, XB + 1.5, XB + 3.0, HT - 0.3, HT + 0.55, -3.2, -1.6), acero);
      put(R(T, XB + 1.6, XB + 2.9, HT + 0.55, HT + 0.6, -3.1, -1.7), oscuro);

      // ── las VENTANAS del piso alto: tres al frente (una con luz) y dos al costado de la esquina
      const ventana = (z, luz) => {
        const z0 = z - 0.7, z1 = z + 0.7, y0 = H1 + 1.05, y1 = y0 + 1.9;
        put(R(T, XF, XF + 0.025, y0, y1, z0, z1), luz ? calido.clone().multiplyScalar(0.75) : vidrio, undefined, luz ? 0.45 : 0);
        put(R(T, XF, XF + 0.2, y0 - 0.12, y0, z0 - 0.12, z1 + 0.12), claro);
        put(R(T, XF, XF + 0.1, y1, y1 + 0.22, z0 - 0.15, z1 + 0.15), claro);
        for (const zz of [z0, z, z1]) put(R(T, XF, XF + 0.06, y0, y1, zz - 0.04, zz + 0.04), claro);
        put(R(T, XF, XF + 0.06, (y0 + y1) / 2 - 0.035, (y0 + y1) / 2 + 0.035, z0, z1), claro);
      };
      ventana(-3.7, false); ventana(0, true); ventana(3.7, false);
      for (const x of [XF - 2.2, XF - 5.6]) {
        const y0 = H1 + 1.05, y1 = y0 + 1.9;
        put(R(T, x - 0.65, x + 0.65, y0, y1, ZL, ZL + 0.025), vidrio);
        put(R(T, x - 0.77, x + 0.77, y0 - 0.12, y0, ZL, ZL + 0.2), claro);
        put(R(T, x - 0.8, x + 0.8, y1, y1 + 0.22, ZL, ZL + 0.1), claro);
        for (const xx of [x - 0.65, x, x + 0.65]) put(R(T, xx - 0.04, xx + 0.04, y0, y1, ZL, ZL + 0.06), claro);
      }
      // una ventana baja al costado (oscura: el depósito)
      put(R(T, XF - 5.4, XF - 3.6, 1.0, 2.8, ZL, ZL + 0.025), vidrio);
      put(R(T, XF - 5.5, XF - 3.5, 0.88, 1.0, ZL, ZL + 0.18), claro);

      // ── la VITRINA: zócalo (tinte), repisa, marco, parteluces y travesaño
      tin(R(T, XF - MU, XF + 0.04, 0, YV0, ZV0, ZV1), 0.55);
      put(R(T, XF - 0.35, XF + 0.12, YV0 - 0.05, YV0 + 0.04, ZV0 - 0.05, ZV1 + 0.05), claro);
      put(R(T, XF - 0.12, XF + 0.02, YV1 - 0.1, YV1, ZV0, ZV1), oscuro);
      for (let k = 0; k <= 3; k++) {
        const z = ZV0 + (ZV1 - ZV0) * k / 3;
        put(R(T, XF - 0.14, XF + 0.02, YV0, YV1, z - 0.05, z + 0.05), oscuro);
      }
      put(R(T, XF - 0.14, XF + 0.02, 2.55, 2.61, ZV0, ZV1), oscuro);

      // ── el LOCAL (lo que se adivina por la vitrina): piso, fondo y techo con luz cálida
      put(R(T, XI, XF - MU, 0.0, 0.06, -ZL + MU, ZD1 + 0.3), madera.clone().lerp(calido, 0.3));
      put(R(T, XI - 0.1, XI, 0, YV1 + 0.25, -ZL + MU, ZD1 + 0.3), calido, undefined, 0.55);
      put(R(T, XI, XF - MU, YV1 + 0.05, YV1 + 0.25, -ZL + MU, ZD1 + 0.3), calido.clone().multiplyScalar(0.62), undefined, 0.3);
      put(R(T, XI, XF - MU, 0, YV1 + 0.1, -ZL + MU, -ZL + MU + 0.04), calido.clone().multiplyScalar(0.85), undefined, 0.35);
      put(R(T, XI, XF - MU, 0, YV1 + 0.1, ZD1 + 0.26, ZD1 + 0.3), calido.clone().multiplyScalar(0.85), undefined, 0.35);
      // las repisas del fondo con frascos y tazas
      for (const y of [1.65, 2.15]) {
        put(R(T, XI, XI + 0.3, y, y + 0.04, -4.6, 0.2), madera);
        for (let k = 0; k < 11; k++) {
          const z = -4.4 + k * 0.42, c = [crema, madera.clone().lerp(crema, 0.4), acero][Math.floor(hash(k + (y > 2 ? 20 : 0), 5) * 3)];
          put(cil(T, 0.07, 0.07, 0.14 + 0.1 * hash(k, 6), XI + 0.15, y + 0.04, z, 8), c);
        }
      }
      // la pizarra del fondo: un panel oscuro con rayas claras (no letras)
      put(R(T, XI, XI + 0.04, 2.45, 3.1, -3.6, -0.9), oscuro);
      for (let k = 0; k < 4; k++) {
        const y = 2.62 + k * 0.12, w = 0.6 + 0.9 * hash(k, 8);
        put(R(T, XI + 0.04, XI + 0.05, y, y + 0.025, -3.4, -3.4 + w), claro);
        put(R(T, XI + 0.04, XI + 0.05, y, y + 0.025, -2.1, -2.1 + 0.4 + 0.6 * hash(k, 9)), claro);
      }
      // el MOSTRADOR: cuerpo de madera y cubierta clara
      put(R(T, XC - 0.35, XC + 0.35, 0, 1.0, -4.7, 0.3), madera);
      put(R(T, XC - 0.4, XC + 0.42, 1.0, 1.06, -4.75, 0.35), claro);
      // la máquina de espresso: cuerpo de acero, bandeja, dos grupos, lanza de vapor y tazas encima
      put(R(T, XC - 0.3, XC + 0.12, 1.06, 1.52, -2.85, -1.95), acero);
      put(R(T, XC - 0.3, XC + 0.14, 1.52, 1.57, -2.88, -1.92), oscuro);
      put(R(T, XC + 0.12, XC + 0.3, 1.06, 1.1, -2.8, -2.0), oscuro);
      for (const z of [-2.62, -2.18]) {
        put(cil(T, 0.05, 0.05, 0.08, XC + 0.2, 1.27, z, 8), oscuro);
        put(barra(T, [XC + 0.2, 1.31, z], [XC + 0.34, 1.33, z + 0.12], 0.025), oscuro);
      }
      put(barra(T, [XC + 0.12, 1.45, -1.98], [XC + 0.24, 1.15, -1.98], 0.02), acero);
      for (let k = 0; k < 4; k++) put(cil(T, 0.045, 0.035, 0.07, XC - 0.15 + (k % 2) * 0.16, 1.57, -2.7 + k * 0.2, 8), crema);
      put(R(T, XC + 0.02, XC + 0.06, 1.38, 1.42, -2.5, -2.3), calido, undefined, 1);
      // el molino
      put(R(T, XC - 0.2, XC + 0.05, 1.06, 1.4, -1.65, -1.4), oscuro);
      put(new T.CylinderGeometry(0.12, 0.05, 0.25, 10).translate(XC - 0.08, 1.52, -1.52), acero);
      // los vasos: tazas en la cubierta y pilas de vasos para llevar
      for (let k = 0; k < 4; k++) put(cil(T, 0.055, 0.045, 0.09, XC + 0.25, 1.06, -0.9 + k * 0.17, 8), crema);
      for (let k = 0; k < 3; k++) put(cil(T, 0.055, 0.042, 0.32 + 0.06 * k, XC - 0.1, 1.06, -0.15 + k * 0.14, 8), crema.clone().multiplyScalar(0.94));
      // la vitrina de panes en el mostrador: caja clara iluminada con panes adentro
      put(R(T, XC - 0.25, XC + 0.32, 1.06, 1.44, -4.5, -3.3), calido.clone().lerp(crema, 0.5), undefined, 0.3);
      for (let k = 0; k < 6; k++) put(new T.SphereGeometry(0.075, 8, 5).scale(1.4, 0.7, 1).translate(XC + 0.33, 1.14 + (k % 2) * 0.14, -4.35 + Math.floor(k / 2) * 0.38), pan);
      // quien atiende: una silueta sin rostro detrás del mostrador
      put(new T.CapsuleGeometry(0.2, 0.75, 3, 8).translate(XI + 0.55, 1.0, -3.0), oscuro.clone().lerp(calido, 0.15));
      put(new T.SphereGeometry(0.14, 10, 8).translate(XI + 0.55, 1.68, -3.0), madera.clone().lerp(crema, 0.3));
      put(R(T, XI + 0.66, XI + 0.76, 0.75, 1.3, -3.2, -2.8), crema);   // el delantal
      // las tres lámparas colgantes: cordón (fijo) y bombilla (parpadea)
      LAMPS.forEach((p, k) => {
        put(R(T, p[0] - 0.012, p[0] + 0.012, p[1] + 0.1, YV1 + 0.05, p[2] - 0.012, p[2] + 0.012), oscuro);
        put(new T.CylinderGeometry(0.05, 0.16, 0.13, 12).translate(p[0], p[1] + 0.08, p[2]), oscuro, "lampara" + k);
        put(new T.SphereGeometry(0.1, 10, 6).translate(p[0], p[1], p[2]), lin(COL.luces), "lampara" + k, 1);
      });

      // ── la PUERTA: marco y hoja (tinte), vidrio con la luz de adentro, jaladera, escalón y dos apliques
      tin(R(T, XF - 0.3, XF + 0.04, 0, YD, ZD0 - 0.1, ZD0), 0.5);
      tin(R(T, XF - 0.3, XF + 0.04, 0, YD, ZD1, ZD1 + 0.1), 0.5);
      tin(R(T, XF - 0.3, XF + 0.04, YD - 0.1, YD, ZD0, ZD1), 0.5);
      tin(R(T, XF - 0.24, XF - 0.17, 0, YD - 0.1, ZD0, ZD1), 0.45);
      put(R(T, XF - 0.17, XF - 0.15, 0.95, YD - 0.35, ZD0 + 0.17, ZD1 - 0.17), calido, undefined, 0.6);
      put(R(T, XF - 0.15, XF - 0.06, 1.0, 1.35, ZD0 + 0.12, ZD0 + 0.16), acero);
      put(R(T, XF, XF + 0.42, 0.08, 0.16, ZD0 - 0.15, ZD1 + 0.15), piso.clone().multiplyScalar(0.92));
      for (const z of [ZD0 - 0.38, ZD1 + 0.38]) {
        put(R(T, XF, XF + 0.08, 2.15, 2.35, z - 0.07, z + 0.07), oscuro);
        put(R(T, XF + 0.08, XF + 0.16, 2.17, 2.33, z - 0.05, z + 0.05), calido, undefined, noche ? 1 : 0.8);
      }

      // ── el LETRERO: placa lisa (tinte oscuro) con una taza en relieve (taza, asa, plato y dos hilos de vapor)
      tin(R(T, XF, XF + 0.1, YT0 + 0.15, H1 + 0.2, ZV0, ZD1), 0.42);
      put(R(T, XF + 0.1, XF + 0.12, YT0 + 0.2, YT0 + 0.24, ZV0 + 0.1, ZD1 - 0.1), claro);
      put(R(T, XF + 0.1, XF + 0.12, H1 + 0.11, H1 + 0.15, ZV0 + 0.1, ZD1 - 0.1), claro);
      const zt = (ZV0 + ZD1) / 2, yt = YT0 + 0.32;
      put(new T.CylinderGeometry(0.2, 0.15, 0.32, 16, 1, false, 0, Math.PI).translate(XF + 0.1, yt + 0.16, zt), crema);
      put(new T.TorusGeometry(0.1, 0.03, 6, 14, Math.PI * 1.2).rotateZ(-Math.PI * 0.6).rotateY(-Math.PI / 2).translate(XF + 0.11, yt + 0.18, zt + 0.21), crema);
      put(R(T, XF + 0.1, XF + 0.16, yt - 0.04, yt, zt - 0.3, zt + 0.3), crema);
      for (const dz of [-0.07, 0.07]) {
        put(barra(T, [XF + 0.13, yt + 0.38, zt + dz], [XF + 0.13, yt + 0.5, zt + dz + 0.04], 0.03), crema);
        put(barra(T, [XF + 0.13, yt + 0.5, zt + dz + 0.04], [XF + 0.13, yt + 0.6, zt + dz - 0.02], 0.03), crema);
      }
      // el disco de bandera en la esquina (liso, con su ménsula)
      put(barra(T, [XF, H1 + 0.9, ZL - 0.5], [XF + 0.9, H1 + 0.9, ZL - 0.5], 0.05), oscuro);
      tin(new T.CylinderGeometry(0.42, 0.42, 0.08, 20).rotateX(Math.PI / 2).translate(XF + 0.6, H1 + 0.42, ZL - 0.5), 0.5);
      put(new T.CylinderGeometry(0.3, 0.3, 0.1, 20).rotateX(Math.PI / 2).translate(XF + 0.6, H1 + 0.42, ZL - 0.5), crema);

      // ── el TOLDO: rayas (tinte y crema), brazos, costados y el faldón festoneado (ondea)
      const NR = Math.round((ZT1 - ZT0) / 0.5), WR = (ZT1 - ZT0) / NR;
      for (let k = 0; k < NR; k++) {
        const z = ZT0 + (k + 0.5) * WR, raya = (geo, grupo) => (k % 2 === 0 ? tin(geo, 1, grupo) : put(geo, crema, grupo));
        raya(barra(T, [XF, YT0, z], [XT1, YT1, z], 0.05, WR + 0.002));
        raya(R(T, XT1 - 0.025, XT1 + 0.025, YT1 - FAL, YT1, z - WR / 2, z + WR / 2), "faldon");
        raya(new T.CylinderGeometry(WR / 2, WR / 2, 0.05, 10, 1, false, 0, Math.PI).rotateZ(-Math.PI / 2).translate(XT1, YT1 - FAL, z), "faldon");
      }
      const lado = new T.Shape();
      lado.moveTo(XF, YT0); lado.lineTo(XT1, YT1); lado.lineTo(XT1, YT1 - 0.05); lado.lineTo(XF, YT0 - 0.75); lado.lineTo(XF, YT0);
      for (const z of [ZT0, ZT1]) tin(new T.ExtrudeGeometry(lado, { depth: 0.04, bevelEnabled: false }).translate(0, 0, z - 0.02), 0.85);
      for (const z of [ZT0 + 0.4, (ZT0 + ZT1) / 2, ZT1 - 0.4]) put(barra(T, [XF, YT0 - 0.7, z], [XT1 - 0.05, YT1 - 0.02, z], 0.04), oscuro);

      // ── la TERRAZA: tres mesitas redondas con sus sillas
      const silla = (x, z, s) => {        // s = +1: el respaldo hacia z+, −1 hacia z−
        put(R(T, x - 0.21, x + 0.21, 0.44, 0.48, z - 0.21, z + 0.21), madera);
        put(R(T, x - 0.2, x + 0.2, 0.48, 0.92, z + s * 0.19, z + s * 0.23), madera);
        for (const dx of [-0.17, 0.17]) for (const dz of [-0.17, 0.17]) put(R(T, x + dx - 0.02, x + dx + 0.02, 0.1, 0.44, z + dz - 0.02, z + dz + 0.02), oscuro);
      };
      const mesa = (x, z) => {
        put(cil(T, 0.22, 0.24, 0.03, x, 0.1, z, 14), oscuro);
        put(cil(T, 0.03, 0.03, 0.62, x, 0.12, z, 8), oscuro);
        put(cil(T, 0.36, 0.36, 0.04, x, 0.74, z, 18), claro);
        put(cil(T, 0.05, 0.04, 0.08, x + 0.1, 0.78, z - 0.08, 8), crema);
        silla(x, z - 0.62, -1);
        silla(x, z + 0.62, 1);
      };
      mesa(XF + 2.35, -4.2);
      mesa(XF + 2.35, -1.5);
      mesa(SOM[0], SOM[2]);
      // la sombrilla sobre la mesa de la esquina: asta fija, copa de ocho gajos (tinte y crema) que ondea
      put(cil(T, 0.025, 0.025, YS - 0.78, SOM[0], 0.78, SOM[2], 6), oscuro);
      for (let k = 0; k < 8; k++) {
        const gajo = new T.ConeGeometry(1.15, 0.42, 1, 1, true, k * TAU / 8, TAU / 8).translate(SOM[0], YS + 0.21, SOM[2]);
        if (k % 2 === 0) tin(gajo, 1, "sombrilla"); else put(gajo, crema, "sombrilla");
      }
      put(new T.ConeGeometry(1.13, 0.4, 8, 1, false).translate(SOM[0], YS + 0.19, SOM[2]), crema.clone().multiplyScalar(0.8), "sombrilla");
      put(cil(T, 0.04, 0.02, 0.14, SOM[0], YS + 0.4, SOM[2], 6), oscuro, "sombrilla");

      // ── la PIZARRA de caballete (dos tableros inclinados; rayas de tiza, sin texto)
      const PZ = [XF + 2.3, 0.1, 0.9];
      for (const s of [1, -1]) {
        const tablero = [];
        tablero.push([new T.BoxGeometry(0.04, 0.95, 0.62).translate(0, 0.475, 0), madera]);
        tablero.push([new T.BoxGeometry(0.012, 0.7, 0.5).translate(s * 0.026, 0.48, 0), oscuro]);
        for (let k = 0; k < 4; k++) {
          const w = 0.18 + 0.24 * hash(k + (s > 0 ? 0 : 9), 4);
          tablero.push([new T.BoxGeometry(0.008, 0.03, w).translate(s * 0.034, 0.72 - k * 0.12, -0.18 + w / 2), claro]);
        }
        for (const [geo, c] of tablero) put(geo.rotateZ(s * 0.25).translate(PZ[0] + s * 0.24, PZ[1], PZ[2]), c);
      }

      // ── los MACETEROS: a los lados de la puerta y en las puntas de la vitrina (caja y follaje)
      for (const [x, z, a] of [[XF + 0.38, ZD0 - 0.62, 0.55], [XF + 0.38, ZD1 + 0.75, 0.55], [XF + 0.38, ZV0 - 0.55, 0.5], [XF + 0.38, ZL + 0.45, 0.45]]) {
        put(R(T, x - a / 2, x + a / 2, 0.1, 0.1 + a, z - a / 2, z + a / 2), oscuro.clone().lerp(claro, 0.25));
        for (let k = 0; k < 4; k++) {
          const n = (x * 13 + z * 7 + k) | 0;
          put(new T.IcosahedronGeometry(0.2 + 0.08 * hash(n, 1), 0).translate(x + (hash(n, 2) - 0.5) * 0.25, 0.1 + a + 0.15 + 0.2 * hash(n, 3), z + (hash(n, 4) - 0.5) * 0.25), planta.clone().multiplyScalar(0.85 + 0.25 * hash(n, 5)));
        }
      }
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
