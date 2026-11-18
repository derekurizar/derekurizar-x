// Objeto «cayuco» (ficha: cayuco.json): una canoa excavada en un tronco (5.2 × 0.8 m, borda a 0.34 m del agua) con UN remero
// sin rostro sentado a popa que rema con una pala por estribor. Genérico: madera del tronco (toma el color de la instancia:
// `tinte`, una de `variantes`; el protagonista, en el acento), camisa (`tinte2`), sombrero de paja; sin redes ni nada de
// pesca (en Panajachel el cayuco era transporte). En METROS (x adelante = proa, y arriba, z a su derecha = estribor; el
// origen en la línea de flotación, al centro). Lo dibujan las piezas que lo `usa`n (actor, flujo) con ctx.flota.
// El casco es una malla propia: secciones en U que se afinan a proa y popa, el arrufo que sube en las puntas, el hueco
// excavado (piso, paredes) y la borda; un tajamar tallado a proa y una tablita de asiento a popa.
// ARTICULADO (grupos anidados con `padre`): `casco` (todo lo que flota: se mece en balance, cabeceo y arfada) → `remero`
// (torso, cabeza y sombrero; pivote en la cadera: se inclina al meter la pala y se endereza al jalar) → `remo` (brazos,
// manos y la pala; pivote entre los hombros: barre de proa a popa bajo el agua y vuelve por el aire); `casco` → `tul`
// (manojos de tul atados, tendidos a lo largo frente al remero: solo con la pose `tul` o `tul_quieto`). `estela` (no sigue
// al casco: queda en el agua): dos brazos de espuma tras la popa y el remolino de la pala, que crecen con la velocidad.
// POSES (`est.pose`): `remar` (por defecto si avanza o si nadie da la velocidad), `tul` (rema cargado de manojos de tul),
// `quieto` (sostiene la pala, sin bogar), `tul_quieto`. Sin pose pedida y vel ≤ 0.3 m/s: `quieto`. El ciclo de la palada
// (1.5–1.9 s, desfasado por instancia con ctx.hash) se escala con la velocidad. Todo es función pura de t.
// Sin luces: un cayuco no lleva; de noche la borda y la espuma se leen por su tono. Sin colores escritos.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const L = 5.2, W = 0.8, BORDA = 0.34, QUILLA = -0.13, GRUESO = 0.05, PISO = -0.06;
  const XR = -1.55, YH = 0.06, HS = YH + 0.55, HZ = 0.2;      // el remero: cadera, hombros
  const TAU = 2 * Math.PI;
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  const fr = (x) => ((x % 1) + 1) % 1;
  // la planta y el perfil del casco en s ∈ [−1, 1] (−1 popa, 1 proa)
  const media = (s) => (W / 2) * Math.pow(Math.max(0, 1 - Math.pow(Math.abs(s), 2.6)), 0.55);
  const tope = (s) => BORDA + 0.07 * s * s * (s > 0 ? 1.3 : 1);
  const fondo = (s) => QUILLA + (BORDA - 0.04 - QUILLA) * Math.pow(Math.abs(s), 5);
  // una malla de triángulos con la normal hacia `hacia(p)` (se voltea si queda al revés)
  const malla = (T) => {
    const P = [];
    const tri = (a, b, c, h) => {
      const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const mx = (a[0] + b[0] + c[0]) / 3, my = (a[1] + b[1] + c[1]) / 3, mz = (a[2] + b[2] + c[2]) / 3, d = h(mx, my, mz);
      if (nx * d[0] + ny * d[1] + nz * d[2] < 0) P.push(...a, ...c, ...b); else P.push(...a, ...b, ...c);
    };
    const quad = (a, b, c, d, h) => { tri(a, b, c, h); tri(a, c, d, h); };
    const geo = () => { const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(P, 3)); return g; };
    return { tri, quad, geo };
  };
  const NS = 30, NM = 14;
  // la sección en U del casco en s: k = 0…NM de babor a estribor; `dentro` = el hueco excavado (más angosto, el piso arriba)
  const seccion = (s, dentro) => {
    const x = s * L / 2, w = media(s), y1 = tope(s), y0 = fondo(s), out = [];
    const wi = Math.max(0, w - GRUESO), yi = Math.min(y1 - 0.01, Math.max(PISO, y0 + 0.07));
    for (let k = 0; k <= NM; k++) {
      const a = -Math.PI / 2 + Math.PI * k / NM, c = Math.pow(Math.cos(a), 0.7);
      out.push(dentro ? (wi > 0.03 ? [x, y1 - (y1 - yi) * c, wi * Math.sin(a)] : [x, y1, 0]) : [x, y1 - (y1 - y0) * c, w * Math.sin(a)]);
    }
    return out;
  };
  const casco = (T) => {
    const M = malla(T), afuera = (x, y, z) => [0, y - (BORDA + 0.2), z], adentro = (x, y, z) => [0, BORDA + 0.3 - y, -z];
    const S = []; for (let i = 0; i <= NS; i++) S.push(-1 + 2 * i / NS);
    for (let i = 0; i < NS; i++) {
      const a = seccion(S[i], false), b = seccion(S[i + 1], false);
      for (let k = 0; k < NM; k++) M.quad(a[k], b[k], b[k + 1], a[k + 1], afuera);
    }
    const ext = M.geo();
    const N = malla(T);
    for (let i = 0; i < NS; i++) {
      const a = seccion(S[i], true), b = seccion(S[i + 1], true);
      for (let k = 0; k < NM; k++) N.quad(a[k], b[k], b[k + 1], a[k + 1], adentro);
    }
    const int = N.geo();
    // la borda: la franja de arriba entre la cara de afuera y la de adentro, a babor y estribor
    const R = malla(T), arriba = () => [0, 1, 0];
    for (let i = 0; i < NS; i++) {
      for (const k of [0, NM]) {
        const a0 = seccion(S[i], false)[k], b0 = seccion(S[i + 1], false)[k], a1 = seccion(S[i], true)[k], b1 = seccion(S[i + 1], true)[k];
        R.quad(a0, b0, b1, a1, arriba);
      }
    }
    return [ext, int, R.geo()];
  };
  // un cilindro de a a b (metros, ejes del objeto)
  const vara = (T, a, b, r0, r1, seg) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), l = d.length();
    const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize());
    return new T.CylinderGeometry(r1, r0, l, seg).applyQuaternion(q).translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  // la pala: la mano de arriba frente al pecho, la de abajo sobre la borda de estribor, la hoja en el agua (de 0 a −0.37 m)
  const MANO_A = [XR + 0.22, HS + 0.22, 0.2], MANO_B = [XR + 0.3, HS - 0.2, 0.38];
  const DIR = (() => { const d = [MANO_B[0] - MANO_A[0], MANO_B[1] - MANO_A[1], MANO_B[2] - MANO_A[2]], n = Math.hypot(...d); return d.map((v) => v / n); })();
  const PUNTO = (l) => [MANO_B[0] + DIR[0] * l, MANO_B[1] + DIR[1] * l, MANO_B[2] + DIR[2] * l];
  MAQ.OBJETOS.cayuco = {
    medidas: { largo_m: L, ancho_m: W, alto_m: 1.25 },
    poses: ["remar", "tul", "quieto", "tul_quieto"],
    grupos: {
      casco: { pivote: [0, 0, 0] },
      remero: { pivote: [XR, YH, 0], padre: "casco" },
      remo: { pivote: [XR, HS, 0], padre: "remero" },
      tul: { pivote: [0.3, BORDA, 0], padre: "casco" },
      estela: { pivote: [-L / 2, 0, 0] },
    },
    // la madera del tronco por instancia (de tonos del estilo): más clara, más oscura, rojiza, gris de lago
    variantes(ctx) {
      const t = ctx.tonos, noche = ctx.ES.modo === 1;
      const base = noche ? t.techo.clone().lerp(t.muro, 0.35) : t.techo.clone().lerp(t.linea, 0.25);
      return [base, base.clone().lerp(t.arena, 0.3), base.clone().multiplyScalar(0.78), base.clone().lerp(t.mal, 0.18), base.clone().lerp(t.muro, 0.3)];
    },
    // la camisa del remero: tonos de tela (nunca el acento)
    variantes2(ctx) {
      const { tonos, COL, lin, ES } = ctx;
      if (ES.dia) return [tonos.secundario.clone().lerp(tonos.arena, 0.3), lin(COL.fondo).multiplyScalar(0.75), tonos.medio.clone().lerp(tonos.secundario, 0.4), lin(COL.tierra_alta).multiplyScalar(0.9)];
      return [tonos.secundario.clone().lerp(tonos.muro, 0.3), tonos.muro.clone(), tonos.arena.clone().lerp(tonos.muro, 0.5)];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, blanco = new T.Color(1, 1, 1), noche = ES.modo === 1;
      const gris = (v) => new T.Color(v, v, v);
      const piel = ES.dia ? lin(COL.tierra_media).lerp(tonos.secundario, 0.28) : tonos.secundario.clone().lerp(tonos.techo, 0.4);
      const pantalon = ES.dia ? lin(COL.mar).lerp(tonos.linea, 0.55) : tonos.linea.clone().lerp(tonos.muro, 0.5);
      const paja = noche ? lin(COL.luces).lerp(tonos.techo, 0.3) : ES.modo === 4 ? tonos.techo.clone() : lin(COL.luces).lerp(tonos.arena, 0.55);
      const palo = noche ? tonos.techo.clone().lerp(tonos.muro, 0.5) : tonos.arena.clone().lerp(tonos.techo, 0.55);
      // el tul seco al sol (pajizo) y el que aún verdea: dos tonos para que se lea cada manojo
      const tulA = tonos.verde.clone().lerp(tonos.arena, noche ? 0.3 : 0.55), tulB = tonos.verde.clone().lerp(tonos.techo, 0.25);
      const amarre = tulA.clone().multiplyScalar(0.55);
      const [ext, int, borda] = casco(T);
      const P = [
        // el casco (toma la madera de la instancia): afuera un poco más oscuro, el hueco en sombra, la borda clara
        { geo: ext, color: gris(0.86), tinte: true, grupo: "casco" },
        { geo: int, color: gris(0.58), tinte: true, grupo: "casco" },
        { geo: borda, color: gris(1.12), tinte: true, grupo: "casco" },
        // el tajamar tallado de proa (un taco que sobresale de la punta) y el taco de popa
        { geo: B(T, 0.3, 0.07, 0.07, L / 2 - 0.05, tope(1) - 0.05, 0), color: gris(0.95), tinte: true, grupo: "casco" },
        { geo: B(T, 0.18, 0.06, 0.07, -L / 2 + 0.03, tope(-1) - 0.05, 0), color: gris(0.95), tinte: true, grupo: "casco" },
        // la tablita del asiento a popa, de borda a borda por dentro
        { geo: B(T, 0.32, 0.04, 2 * (media(XR / (L / 2)) - GRUESO) + 0.02, XR, YH - 0.04, 0), color: palo, grupo: "casco" },
      ];
      // el agua que entra al piso: un charco plano al fondo del hueco (se lee como interior mojado)
      P.push({ geo: B(T, 1.6, 0.01, 0.28, 0.6, PISO + 0.01, 0), color: tonos.agua.clone().lerp(tonos.linea, 0.35), grupo: "casco" });
      // las piernas del remero (no se inclinan con el torso): muslos al frente, espinillas, pies en el piso
      for (const z of [-0.1, 0.1]) P.push(
        { geo: B(T, 0.46, 0.14, 0.15, XR + 0.2, YH, z), color: pantalon, grupo: "casco" },
        { geo: B(T, 0.13, YH + 0.16 - PISO, 0.13, XR + 0.45, PISO, z), color: pantalon, grupo: "casco" },
        { geo: B(T, 0.22, 0.07, 0.11, XR + 0.53, PISO, z), color: pantalon.clone().multiplyScalar(0.7), grupo: "casco" },
      );
      // REMERO: cadera, torso (camisa: tinte2), hombros, cuello, cabeza sin rostro y sombrero de ala
      P.push(
        { geo: B(T, 0.24, 0.12, 0.36, XR, YH, 0), color: pantalon, grupo: "remero" },
        { geo: B(T, 0.24, HS - YH - 0.06, 0.38, XR, YH + 0.08, 0), color: blanco, tinte2: true, grupo: "remero" },
        { geo: B(T, 0.2, 0.08, 0.48, XR, HS - 0.06, 0), color: blanco, tinte2: true, grupo: "remero" },
        { geo: new T.CylinderGeometry(0.05, 0.055, 0.08, 10).translate(XR, HS + 0.06, 0), color: piel, grupo: "remero" },
        { geo: new T.SphereGeometry(0.105, 14, 10).scale(1, 1.08, 0.95).translate(XR, HS + 0.19, 0), color: piel, grupo: "remero" },
        { geo: new T.CylinderGeometry(0.27, 0.27, 0.022, 18).translate(XR, HS + 0.255, 0), color: paja, grupo: "remero" },
        { geo: new T.CylinderGeometry(0.11, 0.13, 0.12, 14).translate(XR, HS + 0.32, 0), color: paja, grupo: "remero" },
        { geo: new T.CylinderGeometry(0.132, 0.132, 0.028, 14).translate(XR, HS + 0.28, 0), color: paja.clone().multiplyScalar(0.55), grupo: "remero" },
      );
      // REMO: los brazos del hombro a cada mano (manga y antebrazo), las manos y la pala de un palo con su hoja
      const hombroI = [XR, HS - 0.02, -HZ], hombroD = [XR, HS - 0.02, HZ];
      for (const [h, m] of [[hombroI, MANO_A], [hombroD, MANO_B]]) {
        const c = [(h[0] + m[0]) / 2, (h[1] + m[1]) / 2, (h[2] + m[2]) / 2];
        P.push({ geo: vara(T, h, c, 0.055, 0.05, 8), color: blanco, tinte2: true, grupo: "remo" },
          { geo: vara(T, c, m, 0.045, 0.04, 8), color: piel, grupo: "remo" },
          { geo: new T.SphereGeometry(0.05, 8, 6).translate(...m), color: piel, grupo: "remo" });
      }
      const puno = [MANO_A[0] - DIR[0] * 0.12, MANO_A[1] - DIR[1] * 0.12, MANO_A[2] - DIR[2] * 0.12];
      P.push({ geo: vara(T, puno, PUNTO(0.46), 0.022, 0.022, 10), color: palo, grupo: "remo" },
        { geo: B(T, 0.04, 0.035, 0.13, 0, -0.017, 0).translate(...puno), color: palo, grupo: "remo" });
      // la hoja: ancha a lo largo de z (empuja el agua hacia popa), afinada en la punta
      { const a = PUNTO(0.44), b = PUNTO(0.9), q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), new T.Vector3(...DIR));
        const hoja = new T.CylinderGeometry(0.085, 0.07, 0.48, 12).scale(1, 1, 0.22).rotateY(Math.PI / 2);
        P.push({ geo: hoja.applyQuaternion(q).translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), color: palo.clone().multiplyScalar(0.92), grupo: "remo" }); }
      // TUL: manojos atados tendidos a lo largo, en dos camas, frente al remero; las puntas se abren en abanico
      for (let k = 0; k < 9; k++) {
        const cama = k < 5 ? 0 : 1, j = cama ? k - 5 : k, n = cama ? 4 : 5;
        const largo = 1.6 + 0.3 * hash(k, 52), x0 = -0.72 + 0.2 * hash(k, 53);
        const sm = (x0 + largo / 2) / (L / 2), wi = media(sm) - GRUESO - 0.09;
        const z = (j - (n - 1) / 2) * (2 * wi / Math.max(1, n - 1)) * (cama ? 0.8 : 1);
        const y = PISO + 0.1 + cama * 0.17 + (cama ? 0 : 0.04 * Math.abs(z) / 0.3), r = 0.085 + 0.02 * hash(k, 54);
        const col = hash(k, 55) < 0.6 ? tulA : tulB, gx = (hash(k, 56) - 0.5) * 0.1;
        P.push({ geo: new T.CylinderGeometry(r, r, largo, 12).rotateZ(Math.PI / 2).rotateY(gx).translate(x0 + largo / 2, y + r, z), color: col, grupo: "tul" });
        // las puntas: un abanico de junco que se abre hacia proa
        P.push({ geo: new T.ConeGeometry(r * 1.6, 0.42, 10, 1, true).rotateZ(Math.PI / 2).rotateY(gx).translate(x0 + largo + 0.18, y + r, z), color: col.clone().multiplyScalar(1.08), grupo: "tul" });
        // dos amarres por manojo
        for (const f of [0.28, 0.72]) P.push({ geo: new T.CylinderGeometry(r * 1.06, r * 1.06, 0.05, 12).rotateZ(Math.PI / 2).rotateY(gx).translate(x0 + largo * f, y + r, z), color: amarre, grupo: "tul" });
      }
      // ESTELA: franjas de espuma en V tras la popa y el remolino junto a la pala (no se tiñen con la hora)
      const costa = lin(COL.costa), LUZ = noche ? 0.1 : 0.35;
      const espuma = (f) => tonos.agua.clone().lerp(costa, (noche ? 0.45 : 0.6) * (1 - 0.6 * f));
      for (const lado of [-1, 1]) for (let k = 0; k < 5; k++) {
        const f = k / 4, cx = -L / 2 - 0.4 - k * 0.75, cz = lado * (0.22 + k * 0.28);
        P.push({ geo: new T.CylinderGeometry(1, 1, 0.02, 10).scale(0.42 - 0.12 * f, 1, 0.07 - 0.03 * f).rotateY(lado * 0.33).translate(cx, 0.02, cz), color: espuma(f), luz: LUZ, grupo: "estela" });
      }
      for (let k = 0; k < 3; k++) P.push({ geo: new T.TorusGeometry(0.16 + 0.13 * k, 0.018, 4, 18).rotateX(Math.PI / 2).translate(XR - 0.1 - 0.35 * k, 0.025, 0.72 + 0.05 * k), color: espuma(0.3 + 0.3 * k), luz: LUZ, grupo: "estela" });
      return P;
    },
    // la pose en t (pura): el mecido del casco, la palada (inclinación del torso y barrido de la pala) y la carga de tul
    pose(t, i, ctx, est) {
      const E = est || {}, h = ctx.hash, vel = E.vel === undefined || E.vel === null ? null : Math.abs(E.vel);
      const nom = E.pose && typeof E.pose === "object" ? (E.pose.nombre || E.pose.pose) : E.pose;
      const quieto = nom === "quieto" || nom === "tul_quieto" || (!nom && vel !== null && vel <= 0.3);
      const tul = nom === "tul" || nom === "tul_quieto";
      // cuánto rema: 0 quieto, completo desde 0.8 m/s (o sin velocidad dada)
      const a = quieto ? 0 : vel === null ? 1 : Math.max(0.35, ctx.suave(0.2, 0.8, vel));
      const per = 1.5 + 0.4 * h(i, 61), u = fr(t / per + h(i, 62));
      // la palada: entra a proa (0), jala hacia popa bajo el agua (0–0.5), sale (0.5–0.6), vuelve por el aire (0.6–0.92: la pala se abre hacia afuera y sube), entra
      const barre = u < 0.5 ? 1 - 2 * s3(u / 0.5) : u < 0.6 ? -1 : u < 0.92 ? -1 + 2 * s3((u - 0.6) / 0.32) : 1;
      const alza = u < 0.5 ? 0 : u < 0.6 ? s3((u - 0.5) / 0.1) : u < 0.86 ? 1 : 1 - s3((u - 0.86) / 0.14);
      const rz = (0.08 + 0.5 * barre) * a, rx = -0.32 * alza * a, dy = 0.05 * alza * a;
      const lean = (-0.12 - 0.14 * Math.max(0, barre) + 0.04 * alza) * a - 0.05 * (1 - a);
      const gira = -0.12 * barre * a;     // el torso gira un poco hacia la pala al meterla
      // el mecido: balance lento (y un tirón hacia la pala al jalar), cabeceo y arfada; fase por instancia
      const f = h(i, 63) * TAU, w = TAU * t / (3.2 + 0.8 * h(i, 64)) + f;
      const tiron = u < 0.5 ? Math.sin(Math.PI * u / 0.5) : 0;
      const roll = 0.035 * Math.sin(w) + 0.025 * tiron * a, pitch = 0.012 * Math.sin(w * 0.73 + 1.3) + 0.006 * tiron * a;
      const heave = 0.02 * Math.sin(w * 1.21 + 0.4);
      const k = vel === null ? (quieto ? 0 : 1) : ctx.suave(0.2, 1.5, vel);
      return {
        casco: [roll, 0, pitch, 0, heave, 0],
        remero: [0, gira, lean],
        remo: [rx, 0, rz, 0, dy, 0],
        tul: [0, 0, 0, 0, 0, 0, tul ? 1 : 0],
        estela: [0, 0, 0, 0, 0, 0, Math.max(0.001, k * (0.85 + 0.15 * Math.sin(w * 1.7)))],
      };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
