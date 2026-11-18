// Objeto «lobina» (ficha: lobina.json): una lobina negra genérica (pez alargado y robusto de 0.56 m, el tamaño de una de
// siete libras) que nada a flor de agua entre los tallos del tul y da TIRONES: cada 3–4.5 s acelera de golpe, la cola azota,
// el lomo sale y el agua salpica en anillos. Lo verificado de ella es solo «pez alargado, oscuro y grande»: el resto es
// genérico (oliva, vientre claro y una banda oscura irregular a lo largo del flanco; sin texto, sin marcas).
// En METROS (x adelante = hocico, y arriba, z a su derecha; el origen en la LÍNEA DEL AGUA, al centro del pez). El agua de la
// maqueta es opaca: el pez nada con el lomo y la aleta dorsal rompiendo la superficie (lo que se ve desde la orilla) y en el
// tirón asoma el flanco con su banda. Lo dibujan las piezas que lo `usa`n (actor, flujo) con ctx.flota.
// El cuerpo es una malla propia por secciones elípticas (alto y ancho por perfil, lomo arqueado, pedúnculo angosto, hocico
// romo con la mandíbula de abajo que sobresale), pintada en franjas: lomo oscuro, flanco oliva, la banda (de borde irregular
// por semilla), flanco bajo y vientre claro; el opérculo marcado, el ojo con su anillo, las aletas de membrana (dorsal
// espinosa con su escotadura y la blanda, anal, pélvicas, pectorales y la caudal apenas escotada).
// ARTICULADO (grupos anidados con `padre`): `cuerpo` (la mitad de adelante; pivote al centro: sube, cabecea y se ladea) →
// `cola` (la mitad de atrás con la dorsal blanda y la anal; pivote a media espalda: ondula) → `caudal` (la aleta de la cola:
// azota con más fase). `pec_d`/`pec_i` (pectorales que abanican, padre `cuerpo`). `estela` (no sigue al cuerpo: la V de
// agua y los anillos que deja) y `salpica` (gotas y corona de agua que salen solo en el tirón: escala 0 el resto del tiempo).
// POSES (`est.pose`): `nadar` (por defecto: ondula y da tirones), `quieto` (cernido entre el tul: solo abanica y ondula
// despacio, sin tirones). Sin pose pedida y vel ≤ 0.05 m/s: `quieto`. Todo es función pura de t (fase por instancia con
// ctx.hash). Sin luces: un pez no lleva; de noche se lee por el tono y la espuma. Sin colores escritos.
(function (MAQ) {
  const L = 0.56, HM = 0.085, WM = 0.046, Y0 = -0.045, SJ = 0.46;   // largo, medio alto, medio ancho, línea media, junta cola
  const TAU = 2 * Math.PI;
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  const fr = (x) => ((x % 1) + 1) % 1;
  // el perfil en s ∈ [0, 1] (0 = base de la cola, 1 = hocico)
  const X = (s) => -L / 2 + s * L;
  const alto = (s) => {
    const ped = 0.026 + 0.01 * s3(s / 0.2);                                       // el pedúnculo
    const cuerpo = HM * Math.pow(Math.sin(Math.PI * Math.min(1, Math.pow(s, 0.85) * 0.97 + 0.02)), 0.75);
    const hocico = s > 0.9 ? 1 - 0.55 * s3((s - 0.9) / 0.1) : 1;
    return Math.max(ped, cuerpo) * hocico;
  };
  const ancho = (s) => Math.max(0.012, WM * Math.pow(Math.sin(Math.PI * Math.min(1, s * 0.95 + 0.04)), 0.8)) * (s > 0.92 ? 1 - 0.45 * s3((s - 0.92) / 0.08) : 1);
  const yc = (s) => Y0 + 0.012 * Math.sin(Math.PI * s) - 0.006 * s3((s - 0.85) / 0.15);   // el lomo arqueado, el hocico baja un poco
  const P3 = (s, th, lado) => [X(s), yc(s) + alto(s) * Math.cos(th), lado * ancho(s) * Math.sin(th)];
  // malla de triángulos con la normal hacia `hacia(p)`
  const malla = (T) => {
    const P = [];
    const tri = (a, b, c, h) => {
      const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const d = h((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3);
      if (nx * d[0] + ny * d[1] + nz * d[2] < 0) P.push(...a, ...c, ...b); else P.push(...a, ...b, ...c);
    };
    const quad = (a, b, c, d, h) => { tri(a, b, c, h); tri(a, c, d, h); };
    const geo = () => { const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(P, 3)); g.computeVertexNormals(); return g; };
    return { tri, quad, geo, vacia: () => P.length === 0 };
  };
  const afuera = (x, y, z) => { const s = (x + L / 2) / L; return [s > 0.97 ? 1 : 0.15 * (s - 0.5), y - yc(Math.max(0, Math.min(1, s))), z]; };
  // una franja del cuerpo entre s0..s1 y los ángulos th0(s)..th1(s) (0 = lomo, π = vientre), en los dos lados
  const NA = 4;
  const franja = (T, s0, s1, ns, th0, th1) => {
    const M = malla(T);
    for (const lado of [-1, 1]) for (let i = 0; i < ns; i++) {
      const sa = s0 + (s1 - s0) * i / ns, sb = s0 + (s1 - s0) * (i + 1) / ns;
      for (let k = 0; k < NA; k++) {
        const ta = (s, f) => th0(s) + (th1(s) - th0(s)) * f;
        M.quad(P3(sa, ta(sa, k / NA), lado), P3(sb, ta(sb, k / NA), lado), P3(sb, ta(sb, (k + 1) / NA), lado), P3(sa, ta(sa, (k + 1) / NA), lado), afuera);
      }
    }
    return M.geo();
  };
  // una aleta de membrana en el plano xy (z = z0): base[i] → punta[i], con las dos caras
  const aleta = (T, base, punta, z0 = 0) => {
    const P = [];
    for (let i = 0; i + 1 < base.length; i++) {
      const a = [base[i][0], base[i][1], z0], b = [base[i + 1][0], base[i + 1][1], z0], c = [punta[i + 1][0], punta[i + 1][1], z0], d = [punta[i][0], punta[i][1], z0];
      P.push(...a, ...b, ...c, ...a, ...c, ...d, ...a, ...c, ...b, ...a, ...d, ...c);
    }
    const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(P, 3)); g.computeVertexNormals(); return g;
  };
  // las espinas: varitas finas que tensan la membrana (de la base a la punta)
  const vara = (T, a, b, r) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), l = d.length();
    const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize());
    return new T.CylinderGeometry(r * 0.4, r, l, 5).applyQuaternion(q).translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  const lomo = (s) => yc(s) + alto(s) * 0.97, vientre = (s) => yc(s) - alto(s) * 0.97;
  MAQ.OBJETOS.lobina = {
    medidas: { largo_m: 0.68, ancho_m: 0.12, alto_m: 0.26 },
    poses: ["nadar", "quieto"],
    grupos: {
      cuerpo: { pivote: [0, Y0, 0] },
      cola: { pivote: [X(SJ), Y0, 0], padre: "cuerpo" },
      caudal: { pivote: [X(0.02), Y0, 0], padre: "cola" },
      pec_d: { pivote: [X(0.72), Y0 - 0.02, 0.04], padre: "cuerpo" },
      pec_i: { pivote: [X(0.72), Y0 - 0.02, -0.04], padre: "cuerpo" },
      estela: { pivote: [0, 0, 0] },
      salpica: { pivote: [0.05, 0, 0] },
    },
    // el oliva del lomo y el flanco por instancia (del verde y la tierra del estilo; el protagonista, en el acento)
    variantes(ctx) {
      const t = ctx.tonos, noche = ctx.ES.modo === 1;
      const base = noche ? t.verde.clone().lerp(t.muro, 0.35) : t.verde.clone().lerp(t.linea, 0.32).lerp(t.techo, 0.12);
      return [base, base.clone().lerp(t.arena, 0.18), base.clone().multiplyScalar(0.82), base.clone().lerp(t.muro, 0.22)];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, noche = ES.modo === 1;
      const gris = (v) => new T.Color(v, v, v);
      const vientreC = noche ? tonos.arena.clone().lerp(tonos.muro, 0.45) : tonos.arena.clone().lerp(lin(COL.costa), 0.35);
      const ojoC = tonos.linea.clone().multiplyScalar(0.35), anillo = noche ? tonos.techo.clone().lerp(tonos.muro, 0.3) : lin(COL.luces).lerp(tonos.techo, 0.45);
      const P = [];
      // EL CUERPO en franjas (las de color `tinte` toman el oliva de la instancia): la banda es irregular por semilla
      const borde = (s, k) => 0.11 * Math.sin(s * 37 + 6 * hash(k, 81)) + 0.07 * Math.sin(s * 71 + 6 * hash(k, 82));
      const bA = (s) => 1.2 + borde(s, 1) * (s > 0.1 && s < 0.86 ? 1 : 0.3), bB = (s) => 1.68 + borde(s, 2) * (s > 0.1 && s < 0.86 ? 1 : 0.3);
      for (const [s0, s1, ns, g] of [[SJ - 0.02, 1, 22, "cuerpo"], [0, SJ + 0.02, 14, "cola"]]) {
        P.push(
          { geo: franja(T, s0, s1, ns, () => 0, () => 0.75), color: gris(0.68), tinte: true, grupo: g },
          { geo: franja(T, s0, s1, ns, () => 0.75, bA), color: gris(1), tinte: true, grupo: g },
          { geo: franja(T, s0, s1, ns, bA, bB), color: gris(0.42), tinte: true, grupo: g },
          { geo: franja(T, s0, s1, ns, bB, () => 2.2), color: gris(1.15), tinte: true, grupo: g },
          { geo: franja(T, s0, s1, ns, () => 2.2, () => Math.PI), color: vientreC, grupo: g },
        );
      }
      // el opérculo: una línea oscura y curva detrás del ojo
      for (const lado of [-1, 1]) for (let k = 0; k < 7; k++) {
        const th = 0.55 + (2.3 - 0.55) * k / 6, th2 = 0.55 + (2.3 - 0.55) * (k + 1) / 6, s = 0.765 - 0.02 * Math.sin(Math.PI * k / 6);
        const a = P3(s, th, lado * 1.04), b = P3(0.765 - 0.02 * Math.sin(Math.PI * (k + 1) / 6), th2, lado * 1.04);
        P.push({ geo: vara(T, a, b, 0.0035), color: gris(0.45), tinte: true, grupo: "cuerpo" });
      }
      // la boca grande: la mandíbula de abajo sobresale y la comisura llega bajo el ojo
      { const s = 0.985, y = yc(s) - 0.012;
        P.push({ geo: new T.SphereGeometry(1, 14, 8, 0, TAU, Math.PI / 2, Math.PI / 2).scale(0.05, 0.016, 0.028).translate(X(s) - 0.03, y, 0), color: gris(0.9), tinte: true, grupo: "cuerpo" },
          { geo: new T.SphereGeometry(1, 14, 8, 0, TAU, 0, Math.PI / 2).scale(0.045, 0.012, 0.026).translate(X(s) - 0.035, y + 0.002, 0), color: gris(0.55), tinte: true, grupo: "cuerpo" });
        for (const lado of [-1, 1]) P.push({ geo: vara(T, [X(s) - 0.01, y + 0.002, lado * 0.021], [X(0.87), y - 0.004, lado * (ancho(0.87) * 0.92)], 0.003), color: ojoC, grupo: "cuerpo" }); }
      // el ojo: anillo claro y pupila oscura, a cada lado
      for (const lado of [-1, 1]) { const s = 0.9, th = 1.05, p = P3(s, th, lado);
        P.push({ geo: new T.SphereGeometry(0.0125, 12, 8).translate(p[0], p[1], p[2] - lado * 0.002), color: anillo, grupo: "cuerpo" },
          { geo: new T.SphereGeometry(0.0078, 10, 8).translate(p[0] + 0.001, p[1], p[2] + lado * 0.0055), color: ojoC, grupo: "cuerpo" }); }
      // ALETAS (membrana algo más oscura que el flanco: toman el oliva)
      const membrana = gris(0.62), espina = gris(0.48);
      // la dorsal espinosa: picos que bajan hacia la escotadura
      { const n = 9, base = [], punta = [];
        for (let i = 0; i <= n; i++) { const s = 0.7 - 0.24 * i / n, h = 0.07 * Math.sin(Math.PI * Math.min(1, 0.25 + 0.9 * i / n)) * (i === n ? 0.35 : 1) * (0.9 + 0.12 * hash(i, 83));
          base.push([X(s), lomo(s) - 0.006]); punta.push([X(s) - 0.008, lomo(s) + h]); }
        P.push({ geo: aleta(T, base, punta), color: membrana, tinte: true, grupo: "cuerpo" });
        for (let i = 0; i < n; i++) P.push({ geo: vara(T, [base[i][0], base[i][1], 0], [punta[i][0], punta[i][1] + 0.004, 0], 0.0022), color: espina, tinte: true, grupo: "cuerpo" }); }
      // la dorsal blanda (redondeada, en la cola) y la anal
      { const base = [], punta = [], b2 = [], p2 = [];
        for (let i = 0; i <= 8; i++) { const u = i / 8, s = 0.45 - 0.27 * u, h = 0.062 * Math.pow(Math.sin(Math.PI * (0.12 + 0.88 * u)), 0.7);
          base.push([X(s), lomo(s) - 0.006]); punta.push([X(s) - 0.012, lomo(s) + h]);
          const sa = 0.34 - 0.18 * u, ha = 0.045 * Math.pow(Math.sin(Math.PI * (0.1 + 0.9 * u)), 0.7);
          b2.push([X(sa), vientre(sa) + 0.006]); p2.push([X(sa) - 0.012, vientre(sa) - ha]); }
        P.push({ geo: aleta(T, base, punta), color: membrana, tinte: true, grupo: "cola" }, { geo: aleta(T, b2, p2), color: membrana, tinte: true, grupo: "cola" }); }
      // las pélvicas: un par bajo el pecho
      for (const lado of [-1, 1]) { const s = 0.66, base = [[X(s + 0.03), vientre(s) + 0.004], [X(s - 0.03), vientre(s) + 0.004]], punta = [[X(s + 0.01), vientre(s) - 0.035], [X(s - 0.06), vientre(s) - 0.03]];
        P.push({ geo: aleta(T, base, punta, lado * 0.018), color: membrana.clone().multiplyScalar(1.2), tinte: true, grupo: "cuerpo" }); }
      // las pectorales: un abanico detrás del opérculo, a cada lado (cada una en su grupo)
      for (const [g, lado] of [["pec_d", 1], ["pec_i", -1]]) {
        const x0 = X(0.72), y0 = Y0 - 0.02, z0 = lado * (ancho(0.72) + 0.002), base = [], punta = [];
        for (let i = 0; i <= 4; i++) { const a = -0.25 - 0.7 * i / 4, r = 0.065 * (0.8 + 0.2 * Math.sin(Math.PI * i / 4));
          base.push([x0 + 0.004 * i, y0 + 0.006 - 0.004 * i]); punta.push([x0 - r * Math.cos(a), y0 + r * Math.sin(a)]); }
        const geo = aleta(T, base, punta, z0);
        P.push({ geo: geo.translate(0, 0, 0), color: membrana.clone().multiplyScalar(1.15), tinte: true, grupo: g });
      }
      // la caudal: ancha y apenas escotada, con sus radios
      { const x0 = X(0.015), base = [], punta = [];
        for (let i = 0; i <= 10; i++) { const u = i / 10, y = (u - 0.5) * 0.05, yt = (u - 0.5) * 0.17, esc = 0.022 * (1 - Math.pow(Math.abs(u - 0.5) * 2, 1.4));
          base.push([x0 + 0.004, Y0 + y]); punta.push([x0 - 0.115 + esc - 0.01 * Math.pow(Math.abs(u - 0.5) * 2, 3), Y0 + yt]); }
        P.push({ geo: aleta(T, base, punta), color: membrana, tinte: true, grupo: "caudal" });
        for (let i = 1; i < 10; i += 2) P.push({ geo: vara(T, [base[i][0], base[i][1], 0], [punta[i][0], punta[i][1], 0], 0.0018), color: espina, tinte: true, grupo: "caudal" }); }
      // LA ESTELA: la V de agua que abre el lomo y dos anillos que se quedan atrás (no se tiñen con la hora)
      const costa = lin(COL.costa), LUZ = noche ? 0.12 : 0.3;
      const espuma = (f) => tonos.agua.clone().lerp(costa, (noche ? 0.45 : 0.62) * (1 - 0.55 * f));
      for (const lado of [-1, 1]) for (let k = 0; k < 6; k++) {
        const f = k / 5, cx = 0.12 - 0.11 * k, cz = lado * (0.045 + 0.05 * k);
        P.push({ geo: new T.CylinderGeometry(1, 1, 0.006, 10).scale(0.07 - 0.02 * f, 1, 0.012 - 0.005 * f).rotateY(lado * 0.45).translate(cx, 0.004, cz), color: espuma(f), luz: LUZ, grupo: "estela" });
      }
      for (let k = 0; k < 3; k++) P.push({ geo: new T.TorusGeometry(0.1 + 0.09 * k, 0.005, 4, 24).rotateX(Math.PI / 2).translate(-0.3 - 0.16 * k, 0.005, 0), color: espuma(0.35 + 0.25 * k), luz: LUZ, grupo: "estela" });
      // LA SALPICADURA del tirón: la corona de agua y gotas que saltan a los lados del lomo
      P.push({ geo: new T.CylinderGeometry(0.16, 0.12, 0.05, 20, 1, true).translate(0, 0.025, 0), color: espuma(0.1), luz: LUZ, grupo: "salpica" });
      for (let k = 0; k < 14; k++) {
        const a = TAU * k / 14 + 0.4 * hash(k, 84), r = 0.12 + 0.08 * hash(k, 85), y = 0.05 + 0.1 * hash(k, 86);
        P.push({ geo: new T.SphereGeometry(0.008 + 0.006 * hash(k, 87), 6, 5).translate(r * Math.cos(a), y, r * Math.sin(a)), color: espuma(0), luz: LUZ, grupo: "salpica" });
      }
      for (let k = 0; k < 2; k++) P.push({ geo: new T.TorusGeometry(0.16 + 0.1 * k, 0.007, 4, 28).rotateX(Math.PI / 2).translate(0, 0.006, 0), color: espuma(0.15 * k), luz: LUZ, grupo: "salpica" });
      return P;
    },
    // la pose en t (pura): ondulación de crucero y, cada 3–4.5 s, un tirón (acelera, la cola azota, el lomo sale, salpica)
    pose(t, i, ctx, est) {
      const E = est || {}, h = ctx.hash, vel = E.vel === undefined || E.vel === null ? null : Math.abs(E.vel);
      const nom = E.pose && typeof E.pose === "object" ? (E.pose.nombre || E.pose.pose) : E.pose;
      const quieto = nom === "quieto" || (!nom && vel !== null && vel <= 0.05);
      // el tirón: ciclo por instancia, dura ≈ 0.7 s
      const per = 3.0 + 1.5 * h(i, 91), u = fr(t / per + h(i, 92)), D = 0.7 / per;
      const g = quieto ? 0 : (u < D ? Math.sin(Math.PI * u / D) : 0);                 // 0 → 1 → 0 durante el tirón
      const ga = quieto ? 0 : (u < D ? s3(u / D) : 1) * (1 - s3((u - D) / (0.25)));       // lo que avanzó en el tirón (vuelve despacio)
      // la ondulación: lenta de crucero (≈ 1.6 Hz) más un azote rápido (≈ 6 Hz) que solo vive en el tirón
      const w = TAU * (quieto ? 0.7 : 1.6) * t + TAU * h(i, 93), wz = TAU * 6 * t;
      const amp = quieto ? 0.4 : 1;
      const cuerpoY = 0.05 * Math.sin(w) * amp + 0.06 * g * Math.sin(wz);
      const colaY = 0.32 * Math.sin(w - 1.1) * amp + 0.55 * g * Math.sin(wz - 1.1);
      const caudY = 0.38 * Math.sin(w - 2.0) * amp + 0.6 * g * Math.sin(wz - 2.0);
      const pec = (quieto ? 0.35 : 0.2) * Math.sin(TAU * (quieto ? 1.3 : 0.9) * t + h(i, 94) * TAU) - 0.4 * g;
      // el cuerpo: sube y asoma (dy), avanza (dx), cabecea hacia arriba y se ladea al azotar; arfada suave
      const arfada = 0.006 * Math.sin(TAU * t / 2.3 + h(i, 95) * TAU);
      const dy = 0.055 * g + arfada, dx = 0.22 * ga, cab = 0.12 * g, ladeo = 0.18 * g * Math.sin(wz * 0.5);
      // la estela crece con la marcha (y en el tirón); la salpicadura solo en el tirón
      const k = vel === null ? (quieto ? 0.15 : 0.7) : 0.15 + 0.85 * ctx.suave(0.05, 0.8, vel);
      const sal = g > 0.02 ? 0.4 + 0.8 * g : 0;
      return {
        cuerpo: [ladeo, cuerpoY, cab, dx, dy, 0],
        cola: [0, colaY, 0],
        caudal: [0, caudY, 0],
        pec_d: [pec, 0, 0],
        pec_i: [-pec, 0, 0],
        estela: [0, 0, 0, dx * 0.6, 0, 0, Math.max(0.001, Math.min(1.4, k + 0.6 * g))],
        salpica: [0, 0, 0, dx, 0, 0, Math.max(0, sal)],
      };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
