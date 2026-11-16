// Objeto «persona» (ficha: persona.json): UNA persona (1.75 m) con POSES CON NOMBRE y sus accesorios. Muñeco sin rostro,
// genérico; low-poly con primitivas de three.js, en METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al
// centro). Lo dibujan las piezas que lo `usa`n (actor, flujo, beneficio, tostaduria) con ctx.flota: las partes con `tinte`
// (camisa y mangas) toman el color de la instancia. Sin colores escritos: todo sale de ctx.tonos, ctx.COL y ctx.lin.
// ESQUELETO (grupos anidados con `padre`): `cuerpo` (raíz: baja al sentarse) → `torso` (cadera; se inclina) → `cabeza`
// (cuello) → `sombrero`; `torso` → `brazo_d|i` (hombro) → `antebrazo_d|i` (codo; la mano y el vaso); `cuerpo` → `pierna_d|i`
// (cadera) → `espinilla_d|i` (rodilla). Los brazos se colocan con una IK de dos huesos hacia un punto (la rama, el rastrillo,
// el saco, la boca), así la mano llega a donde tiene que estar.
// ACCESORIOS (grupos que solo salen en su pose: escala 0 en las demás): sombrero de ala (cosechar, rastrillar), costal al
// costado (cosechar), rastrillo (rastrillar), saco (cargar), vaso para llevar (sorber), delantal (atender), banco (sentado).
// POSES (`est.pose`: el nombre que pidió quien la puso; o un objeto {nombre, periodo, fase, saco, banco} con el que una pieza
// sincroniza el ciclo con lo suyo y apaga un accesorio que dibuja ella): de_pie (respira, mira alrededor), caminar (paso de
// 0.9–1.1 s con rodillas y codos, escalado por `vel`), cosechar (el brazo sube a la rama y baja al costal), rastrillar (torso
// inclinado, el rastrillo va y viene; si avanza, pasos cortos), cargar (sube el saco del pecho a una tolva alta, lo inclina,
// lo baja: fases 0.1 · 0.3 · 0.76 · 0.9 de su ciclo, ~6 s), sorber (lleva el vaso a la cintura y lo sube a la boca cada
// 4–6 s; camina si avanza), sentado (cadera abajo, rodillas a 90°, manos en los muslos), atender (detrás de un mostrador: las
// manos al frente se mueven poco). Sin pose pedida: `caminar` si vel > 0.3 m/s (o si nadie da la velocidad), `de_pie` si no.
// Todo es función pura de t, desfasada por instancia con ctx.hash(i).
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const CADERA = 0.88, RODILLA = 0.47, HOMBRO = 1.4, CUELLO = 1.45, CODO = 1.11, MUNECA = 0.85;
  const PZ = 0.095, HZ = 0.255, L1 = HOMBRO - CODO, L2 = CODO - MUNECA + 0.05, LT = HOMBRO - CADERA;
  const PIERNA = 0.28, BRAZO = 0.23, TAU = 2 * Math.PI;
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  const fr = (x) => ((x % 1) + 1) % 1;
  const ACC = ["sombrero", "costal", "rastrillo", "saco", "vaso", "delantal", "banco"];
  const POSES = ["de_pie", "caminar", "cosechar", "rastrillar", "cargar", "sorber", "sentado", "atender"];
  // IK de dos huesos en el plano del brazo: la mano hacia (tx, ty) del cuerpo; el torso inclinado th (rz) y el cuerpo corrido
  // dy. Devuelve [rz del brazo relativo al torso, rz del codo] (0 = colgando; + = hacia adelante)
  const ik = (tx, ty, th, dy) => {
    const sx = -LT * Math.sin(th), sy = CADERA + dy + LT * Math.cos(th);
    const vx = tx - sx, vy = ty - sy, d = Math.max(0.06, Math.min(L1 + L2 - 0.005, Math.hypot(vx, vy)));
    const fT = Math.atan2(vx, -vy);
    const a = Math.acos(Math.max(-1, Math.min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))));
    const b = Math.acos(Math.max(-1, Math.min(1, (L2 * L2 + d * d - L1 * L1) / (2 * L2 * d))));
    return [fT - a - th, a + b];
  };
  MAQ.OBJETOS.persona = {
    medidas: { largo_m: 0.5, ancho_m: 0.5, alto_m: 1.75 },
    poses: POSES,
    grupos: {
      cuerpo: { pivote: [0, 0, 0] },
      torso: { pivote: [0, CADERA, 0], padre: "cuerpo" },
      cabeza: { pivote: [0, CUELLO, 0], padre: "torso" },
      sombrero: { pivote: [0, 1.68, 0], padre: "cabeza" },
      brazo_d: { pivote: [0, HOMBRO, HZ], padre: "torso" },
      brazo_i: { pivote: [0, HOMBRO, -HZ], padre: "torso" },
      antebrazo_d: { pivote: [0, CODO, HZ], padre: "brazo_d" },
      antebrazo_i: { pivote: [0, CODO, -HZ], padre: "brazo_i" },
      pierna_d: { pivote: [0, CADERA, PZ], padre: "cuerpo" },
      pierna_i: { pivote: [0, CADERA, -PZ], padre: "cuerpo" },
      espinilla_d: { pivote: [0, RODILLA, PZ], padre: "pierna_d" },
      espinilla_i: { pivote: [0, RODILLA, -PZ], padre: "pierna_i" },
      costal: { pivote: [0.07, 0.96, 0.33], padre: "torso" },
      delantal: { pivote: [0.15, CADERA, 0], padre: "torso" },
      vaso: { pivote: [0, MUNECA - 0.06, HZ], padre: "antebrazo_d" },
      saco: { pivote: [0.38, 1.2, 0], padre: "cuerpo" },
      rastrillo: { pivote: [0.5, 1.0, 0.05], padre: "cuerpo" },
      banco: { pivote: [0, 0, 0] },
    },
    variantes: (ctx) => ctx.tonos.vehiculos,
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), dia = !!(ES && ES.dia), noche = ES && ES.modo === 1;
      const oscuro = tonos.linea.clone().lerp(tonos.muro, 0.5);
      const piel = dia && lin && COL ? lin(COL.tierra_media).lerp(tonos.secundario, 0.28) : tonos.secundario.clone().lerp(tonos.techo, 0.4);
      const zapato = oscuro.clone().multiplyScalar(0.7);
      const pelo = tonos.linea.clone().lerp(tonos.muro, noche ? 0.4 : 0.12);
      const L = (k) => (lin && COL && COL[k] ? lin(COL[k]) : tonos.techo.clone());
      const paja = noche ? L("luces").lerp(tonos.techo, 0.3) : ES && ES.modo === 4 ? tonos.techo.clone() : L("luces").lerp(tonos.arena, 0.55);
      const yute = noche ? L("luces").lerp(tonos.techo, 0.5).multiplyScalar(0.8)
        : ES && ES.modo === 4 ? tonos.techo.clone().lerp(tonos.linea, 0.18) : tonos.arena.clone().lerp(tonos.linea, 0.12);
      const madera = tonos.techo.clone().lerp(tonos.linea, 0.45).multiplyScalar(dia ? 0.8 : 1.2);
      const fierro = tonos.linea.clone().lerp(tonos.asfalto || tonos.muro, 0.4);
      const vaso = dia ? tonos.secundario.clone().lerp(L("costa"), 0.2) : tonos.secundario.clone().lerp(tonos.muro, 0.15);
      const funda = dia ? L("tierra_alta").lerp(L("tierra_media"), 0.25) : tonos.arena.clone().lerp(tonos.linea, 0.2);
      const delantal = dia ? L("costa").lerp(tonos.secundario, 0.4) : tonos.secundario.clone().lerp(tonos.muro, 0.35);
      const eje = (g) => g.rotateZ(-Math.PI / 2);                     // de y a +x (el vaso: queda derecho con el antebrazo al frente)
      const P = [
        // CUERPO (raíz): la cadera, que tapa el arranque de las piernas
        { geo: B(T, 0.26, 0.14, 0.36, 0, CADERA - 0.1, 0), color: oscuro, grupo: "cuerpo" },
        // TORSO: camisa con su tinte y los hombros
        { geo: B(T, 0.28, LT + 0.02, 0.4, 0, CADERA, 0), color: blanco, tinte: true, grupo: "torso" },
        { geo: B(T, 0.22, 0.07, 0.46, 0, HOMBRO - 0.04, 0), color: blanco, tinte: true, grupo: "torso" },
        // CABEZA: cuello, cabeza sin rostro (coronilla a 1.73 m) y el pelo como un casquete
        { geo: new T.CylinderGeometry(0.05, 0.055, 0.1, 8).translate(0, HOMBRO + 0.07, 0), color: piel, grupo: "cabeza" },
        { geo: new T.SphereGeometry(0.13, 10, 8).translate(0, 1.6, 0), color: piel, grupo: "cabeza" },
        { geo: new T.SphereGeometry(0.136, 10, 8, 0, TAU, 0, 0.5 * Math.PI).scale(1, 0.92, 0.98).translate(-0.012, 1.615, 0), color: pelo, grupo: "cabeza" },
        // SOMBRERO de ala ancha (paja): ala, copa y cinta
        { geo: new T.CylinderGeometry(0.29, 0.29, 0.025, 16).translate(0, 1.67, 0), color: paja, grupo: "sombrero" },
        { geo: new T.CylinderGeometry(0.115, 0.135, 0.12, 12).translate(0, 1.74, 0), color: paja, grupo: "sombrero" },
        { geo: new T.CylinderGeometry(0.137, 0.137, 0.03, 12).translate(0, 1.695, 0), color: paja.clone().multiplyScalar(0.55), grupo: "sombrero" },
        // COSTAL al costado derecho, con la boca abierta y la correa que cruza el pecho hasta el hombro izquierdo
        { geo: B(T, 0.26, 0.36, 0.2, 0.07, 0.6, 0.33), color: yute, grupo: "costal" },
        { geo: B(T, 0.28, 0.04, 0.22, 0.07, 0.96, 0.33), color: yute.clone().multiplyScalar(1.15), grupo: "costal" },
        // DELANTAL al frente, del pecho a la rodilla
        { geo: B(T, 0.02, 0.78, 0.34, 0.15, 0.48, 0), color: delantal, grupo: "delantal" },
        { geo: B(T, 0.015, 0.03, 0.42, 0.152, CADERA - 0.02, 0), color: delantal.clone().multiplyScalar(0.75), grupo: "delantal" },
        // SACO de yute (lleno, con el amarre atrás): centrado en el pivote, a lo largo de x
        { geo: B(T, 0.5, 0.3, 0.34, 0.38, 1.05, 0), color: yute, grupo: "saco" },
        { geo: B(T, 0.08, 0.16, 0.2, 0.38 - 0.27, 1.12, 0), color: yute.clone().multiplyScalar(0.8), grupo: "saco" },
        // VASO para llevar en la mano derecha (eje a lo largo de +x: derecho con el antebrazo al frente), funda y tapa
        { geo: eje(new T.CylinderGeometry(0.05, 0.04, 0.19, 12)).translate(0.03, MUNECA - 0.06, HZ - 0.05), color: vaso, grupo: "vaso" },
        { geo: eje(new T.CylinderGeometry(0.0505, 0.0465, 0.08, 12)).translate(0.04, MUNECA - 0.06, HZ - 0.05), color: funda, grupo: "vaso" },
        { geo: eje(new T.CylinderGeometry(0.054, 0.054, 0.02, 12)).translate(0.127, MUNECA - 0.06, HZ - 0.05), color: vaso.clone().multiplyScalar(0.84), grupo: "vaso" },
        // BANCO (para sentarse donde no hay silla): asiento y cuatro patas
        { geo: B(T, 0.42, 0.05, 0.42, 0.08, 0.34, 0), color: madera, grupo: "banco" },
      ];
      // la correa del costal: del costal (derecha, abajo) al hombro izquierdo, por delante del pecho
      { const a = [0.15, 0.98, 0.3], b = [0.15, HOMBRO + 0.02, -0.18], dy = b[1] - a[1], dz = b[2] - a[2], l = Math.hypot(dy, dz);
        P.push({ geo: new T.BoxGeometry(0.02, l, 0.05).rotateX(Math.atan2(dz, dy)).translate(a[0], (a[1] + b[1]) / 2, (a[2] + b[2]) / 2),
                 color: yute.clone().multiplyScalar(0.7), grupo: "costal" }); }
      for (const [x, z] of [[-0.1, -0.18], [-0.1, 0.18], [0.26, -0.18], [0.26, 0.18]]) P.push({ geo: B(T, 0.04, 0.34, 0.04, x, 0, z), color: madera.clone().multiplyScalar(0.8), grupo: "banco" });
      // RASTRILLO: el palo de las manos (0.45, 1.02) al suelo (1.55, 0.1), el travesaño y los dientes
      { const ax = 0.42, ay = 1.04, bx = 1.55, by = 0.1, l = Math.hypot(bx - ax, by - ay);
        P.push({ geo: new T.BoxGeometry(l, 0.04, 0.04).rotateZ(Math.atan2(by - ay, bx - ax)).translate((ax + bx) / 2, (ay + by) / 2, 0.05), color: madera, grupo: "rastrillo" });
        P.push({ geo: B(T, 0.08, 0.06, 0.8, bx, 0.06, 0.05), color: fierro, grupo: "rastrillo" });
        for (let k = 0; k < 9; k++) P.push({ geo: B(T, 0.05, 0.07, 0.025, bx + 0.02, 0, 0.05 - 0.37 + 0.74 * k / 8), color: fierro, grupo: "rastrillo" }); }
      // PIERNAS: muslo (pantalón) y espinilla con su zapato
      for (const [s, z] of [["d", PZ], ["i", -PZ]]) P.push(
        { geo: B(T, 0.16, CADERA - RODILLA + 0.03, 0.15, 0, RODILLA - 0.02, z), color: oscuro, grupo: "pierna_" + s },
        { geo: B(T, 0.145, RODILLA - 0.04, 0.135, 0, 0.05, z), color: oscuro, grupo: "espinilla_" + s },
        { geo: B(T, 0.25, 0.07, 0.13, 0.045, 0, z), color: zapato, grupo: "espinilla_" + s },
      );
      // BRAZOS: manga (tinte) hasta el codo; antebrazo y mano (piel)
      for (const [s, z] of [["d", HZ], ["i", -HZ]]) P.push(
        { geo: B(T, 0.11, L1 + 0.03, 0.11, 0, CODO - 0.02, z), color: blanco, tinte: true, grupo: "brazo_" + s },
        { geo: B(T, 0.085, CODO - MUNECA + 0.02, 0.085, 0, MUNECA, z), color: piel, grupo: "antebrazo_" + s },
        { geo: B(T, 0.09, 0.09, 0.075, 0.005, MUNECA - 0.09, z), color: piel, grupo: "antebrazo_" + s },
      );
      return P;
    },
    // la pose en t (función pura). est = {vel (m/s o null), pose (nombre u objeto {nombre, periodo, fase, saco, banco})}
    pose(t, i, ctx, est) {
      const h = ctx.hash, E = est || {};
      const O = E.pose && typeof E.pose === "object" ? E.pose : { nombre: E.pose || null };
      const vel = E.vel !== null && E.vel !== undefined ? E.vel : null;
      let nom = O.nombre || O.pose || null;
      if (!nom || POSES.indexOf(nom) < 0) nom = vel === null || vel > 0.3 ? "caminar" : "de_pie";
      const G = {};
      for (const g of Object.keys(MAQ.OBJETOS.persona.grupos)) G[g] = [0, 0, 0, 0, 0, 0, ACC.indexOf(g) >= 0 ? 0 : 1];
      const pon = (g, r) => { for (let k = 0; k < r.length; k++) G[g][k] = r[k]; };
      const ve = (g) => { G[g][6] = 1; };
      const brazo = (s, tx, ty, th, dy, rx = 0) => { const [a, e] = ik(tx, ty, th, dy); pon("brazo_" + s, [rx, 0, a]); pon("antebrazo_" + s, [0, 0, e]); };
      // el paso (lo comparten caminar, rastrillar y sorber): f = cuánto camina (por la velocidad)
      const paso = (f, amp = 1) => {
        const per = 0.9 + 0.2 * h(i, 81), w = TAU * (t / (2 * per) + h(i, 82)), s = f * Math.sin(w), c = Math.cos(w);
        const a = PIERNA * (0.9 + 0.2 * h(i, 83)) * s * amp;
        pon("pierna_d", [0, 0, a]); pon("pierna_i", [0, 0, -a]);
        pon("espinilla_d", [0, 0, -f * amp * (0.08 + 0.5 * Math.max(0, c))]); pon("espinilla_i", [0, 0, -f * amp * (0.08 + 0.5 * Math.max(0, -c))]);
        return s;
      };
      const fv = (v0) => (vel === null ? 1 : Math.min(1, Math.max(0, vel) / v0));
      const respira = Math.sin(TAU * (t / (3.4 + 0.8 * h(i, 85)) + h(i, 86)));
      const mira = Math.sin(TAU * (t / (7 + 3 * h(i, 87)) + h(i, 88)));

      if (nom === "de_pie") {
        pon("torso", [0, 0, 0.012 * respira]);
        pon("cabeza", [0, 0.2 * mira, -0.04]);
        pon("brazo_d", [-0.06, 0, 0.03 + 0.015 * respira]); pon("brazo_i", [0.06, 0, 0.03 + 0.015 * respira]);
        pon("antebrazo_d", [0, 0, 0.1]); pon("antebrazo_i", [0, 0, 0.1]);
        pon("pierna_d", [-0.03, 0, 0]); pon("pierna_i", [0.03, 0, 0]);
      } else if (nom === "caminar") {
        const f = fv(0.5), s = paso(f), b = BRAZO * (0.9 + 0.2 * h(i, 84)) * s;
        pon("torso", [0, 0, -0.04 * f]);
        pon("brazo_d", [-0.04, 0, -b]); pon("brazo_i", [0.04, 0, b]);
        pon("antebrazo_d", [0, 0, 0.15 + 0.2 * f * Math.max(0, -s)]); pon("antebrazo_i", [0, 0, 0.15 + 0.2 * f * Math.max(0, s)]);
      } else if (nom === "cosechar") {
        ve("sombrero"); ve("costal");
        const per = 1.8 + 0.6 * h(i, 71), u = fr(t / per + h(i, 72));
        const r = u < 0.34 ? s3(u / 0.34) : u < 0.52 ? 1 : u < 0.84 ? 1 - s3((u - 0.52) / 0.32) : 0;
        const tiron = u > 0.38 && u < 0.5 ? Math.sin(Math.PI * (u - 0.38) / 0.12) : 0;
        const suelta = u > 0.84 ? Math.sin(Math.PI * (u - 0.84) / 0.16) : 0;
        const alto = 1.5 + 0.28 * h(i, 73), th = -0.07 - 0.17 * r - 0.04 * tiron;
        pon("torso", [0, 0, th]);
        brazo("d", 0.12 + 0.4 * r, 0.95 + (alto - 0.95) * r - 0.07 * tiron + 0.05 * suelta, th, 0, -0.18 * (1 - r));
        brazo("i", 0.44 + 0.03 * Math.sin(TAU * u), 1.42 + 0.05 * Math.sin(TAU * u) - 0.03 * tiron, th, 0, 0.05);
        pon("cabeza", [0, -0.28 * (1 - r), 0.42 * r - 0.38 * (1 - r)]);
        pon("pierna_d", [-0.04, 0, 0.06]); pon("pierna_i", [0.04, 0, -0.04]);
        pon("espinilla_d", [0, 0, -0.1]); pon("espinilla_i", [0, 0, -0.06]);
      } else if (nom === "rastrillar") {
        ve("sombrero"); ve("rastrillo");
        const per = 1.2 + 0.3 * h(i, 55), va = Math.sin(TAU * (t / per + h(i, 56))), d = 0.24 * va;
        const th = -0.3 - 0.1 * va;
        pon("torso", [0, 0, th]);
        pon("rastrillo", [0, 0, 0, d, 0.02 * Math.max(0, -va), 0]);
        brazo("d", 0.6 + d, 0.88 - 0.05 * va, th, 0, 0.3);
        brazo("i", 0.42 + d, 1.03 - 0.04 * va, th, 0, -0.45);
        pon("cabeza", [0, 0, -0.22]);
        const f = vel === null ? 0 : Math.min(1, Math.max(0, vel) / 0.6);
        paso(f, 0.6);
        G.pierna_i[2] += 0.16; G.pierna_d[2] -= 0.06; G.espinilla_i[2] -= 0.12; G.espinilla_d[2] -= 0.08;
      } else if (nom === "cargar") {
        const per = O.periodo || 5.6 + 0.8 * h(i, 61), f = fr(t / per + (O.fase !== undefined ? O.fase : h(i, 62)));
        const solo = O.saco !== false;                 // sin saco propio: lo dibuja la pieza (y aparece y se va)
        if (solo) ve("saco");
        let q, tilt, baja = 0;
        if (f < 0.1) { q = 0; tilt = 0; }
        else if (f < 0.3) { q = s3((f - 0.1) / 0.2); tilt = 0.95 * q; }
        else if (f < 0.76) { const w = (f - 0.3) / 0.46; q = 1; tilt = 0.95 + 0.3 * w; baja = 0.045 * w; }
        else if (f < 0.9) { const w = s3((f - 0.76) / 0.14); q = 1 - w; tilt = 1.25 * (1 - w); baja = 0.045 * (1 - w); }
        else { q = 0; tilt = 0; }
        // cuánto sostiene: con saco propio, siempre; sin él, se prende al aparecer el saco y se suelta al irse
        const e = solo ? 1 : f < 0.1 ? s3(f / 0.1) : f < 0.83 ? 1 : f < 0.9 ? 1 - s3((f - 0.83) / 0.07) : 0;
        const cx = 0.38 + 0.33 * q, cy = 1.2 + 0.715 * q + 0.136 * Math.sin(Math.PI * q) - baja;
        G.saco = [0, 0, -tilt, cx - 0.38, cy - 1.2, 0, solo ? 1 : 0];
        const th = 0.06 * q - 0.08 * (1 - q) * e;
        pon("torso", [0, 0, th]);
        const ct = Math.cos(tilt), st = Math.sin(tilt);
        const rd = [cx - 0.16 * ct, cy + 0.16 * st - 0.13], ri = [cx + 0.08 * ct, cy - 0.08 * st - 0.15];
        const reposo = [0.03, 0.78];
        brazo("d", reposo[0] + (rd[0] - reposo[0]) * e, reposo[1] + (rd[1] - reposo[1]) * e, th, 0, 0.12 * e - 0.05);
        brazo("i", reposo[0] + (ri[0] - reposo[0]) * e, reposo[1] + (ri[1] - reposo[1]) * e, th, 0, -0.12 * e + 0.05);
        pon("cabeza", [0, 0, 0.3 * q * e - 0.1 * (1 - q) * e]);
        pon("pierna_i", [0, 0, 0.14]); pon("pierna_d", [0, 0, -0.08]); pon("espinilla_i", [0, 0, -0.1]); pon("espinilla_d", [0, 0, -0.04]);
      } else if (nom === "sorber") {
        ve("vaso");
        const f = vel === null ? 0 : Math.min(1, Math.max(0, vel) / 0.5), s = paso(f), b = BRAZO * s;
        const per = 4 + 2 * h(i, 91), qq = fr(t / per + h(i, 92)) * per;
        const r = qq < 0.7 ? s3(qq / 0.7) : qq < 1.6 ? 1 : qq < 2.4 ? 1 - s3((qq - 1.6) / 0.8) : 0;
        pon("torso", [0, 0, 0.015 * respira]);
        brazo("d", 0.27 + (0.15 - 0.27) * r, 1.0 + (1.47 - 1.0) * r, 0, 0, -0.02 + 0.3 * r);
        G.antebrazo_d[0] = -0.55 * r;
        pon("brazo_i", [0.05, 0, 0.03 + b]); pon("antebrazo_i", [0, 0, 0.12]);
        pon("cabeza", [0, 0.15 * mira * (1 - r), 0.17 * r - 0.03]);
      } else if (nom === "sentado") {
        const banco = O.banco !== false;
        if (banco) ve("banco");
        const dy = 0.47 - CADERA, th = -0.05 + 0.01 * respira;
        pon("cuerpo", [0, 0, 0, 0, dy, 0]);
        pon("torso", [0, 0, th]);
        pon("pierna_d", [-0.04, 0, Math.PI / 2]); pon("pierna_i", [0.04, 0, Math.PI / 2]);
        pon("espinilla_d", [0, 0, -Math.PI / 2 + 0.06]); pon("espinilla_i", [0, 0, -Math.PI / 2 - 0.04]);
        brazo("d", 0.3, 0.6, th, dy, -0.05); brazo("i", 0.26, 0.6, th, dy, 0.05);
        pon("cabeza", [0, 0.25 * mira, -0.05]);
      } else if (nom === "atender") {
        ve("delantal");
        const per = 2.6 + 0.9 * h(i, 95), w = TAU * (t / per + h(i, 96)), th = -0.07;
        pon("torso", [0, 0, th + 0.01 * respira]);
        brazo("d", 0.4 + 0.06 * Math.sin(w), 1.0 + 0.03 * Math.sin(2 * w), th, 0, 0.1);
        brazo("i", 0.36 + 0.025 * Math.sin(0.5 * w + 1), 0.98, th, 0, -0.1);
        pon("cabeza", [0, 0.12 * mira, -0.16 + 0.05 * Math.sin(0.5 * w)]);
      }
      return G;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
