// Pieza «bulevar1890» (ficha: bulevar1890.json; reglas: scripts/maqueta_tipos/bulevar1890.py): el Bulevar 30 de Junio de la
// década de 1890 sobre el trazo REAL de la Avenida Reforma (OpenStreetMap, set capital) entre `desde` y `hacia`, sin la
// ciudad moderna. Todo en METROS; el eje y los anchos llegan resueltos.
// - EL CORTE (de un lado al otro): acera de tierra apisonada · jardín con su seto y su fila de árboles · calzada de
//   carruajes (abombada, con bordillo de piedra) · JARDÍN CENTRAL con su sendero, las ESTATUAS blancas en pedestal y las
//   FUENTES genéricas · calzada · jardín · acera. En los jardines laterales, dos ESTANQUES ovalados sin forma precisa.
// - EL PALACIO al extremo sur, mirando al paseo: volumen genérico de estilo renacimiento italiano (planta baja almohadillada,
//   piso noble con ventanas de frontón, cuerpo central con arcada y frontón, pabellones de esquina, cornisa y balaustrada,
//   techo bajo), sobre su zócalo y su escalinata; delante, la explanada y el MONUMENTO ECUESTRE genérico.
// - EL CAMPO: parcelas de cultivo y potrero a los dos lados, árboles sueltos y QUINTAS dispersas (casa de teja con corredor,
//   tapia, huerto y su galera), todas genéricas.
// - CON VIDA (seek puro): carruajes de un caballo que van y vienen por las calzadas (las patas al trote, las ruedas que
//   giran), paseantes que caminan por las aceras y el sendero del jardín, GRUPOS de 2 a 4 que pasean juntos o conversan
//   de pie en las aceras frente al jardín central (`grupos`; `escala_gente` agranda a toda la gente), el agua de las fuentes. De noche: ventanas del
//   palacio y de las quintas, los faroles de los carruajes (puntos de luz genéricos, no un dato).
// - RESALTAR con `elemento`: 0 el palacio y el monumento, 1 los jardines, 2 las estatuas EN ORDEN de desde a hacia a lo
//   largo del resaltado, 3 el inicio del paseo, 100 + j una estatua. El terremoto rompe el palacio por partes (es una malla
//   en pie, propia); los árboles y la gente son instancias y no se rompen.
// Sin colores escritos (ctx.tonos, ctx.COL); sin texto ni marcas.
(function (MAQ) {
  const TAU = 2 * Math.PI, PI = Math.PI;
  const F_CENTRAL = 4.5 / 22, F_CALZ = 7 / 22, F_JARDIN = 7 / 22, F_ACERA = 3.5 / 22;
  const B1 = F_CENTRAL, B2 = F_CENTRAL + F_CALZ, B3 = B2 + F_JARDIN, B4 = 1;
  const VCARRO = 3.4, VPIE = 1.25;      // m/s (ilustrativo)
  const CAD_PERS = 0.88;                // la cadera del objeto persona (m): donde empieza el saco de los grupos

  MAQ.PIEZAS.bulevar1890 = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      // ---- los tonos (del estilo; acabados genéricos)
      const cPiedra = tonos.muro.clone().lerp(tonos.asfalto, 0.38);
      const cPiedraL = cPiedra.clone().lerp(tonos.muro, 0.55);
      const cMarmol = tonos.muro.clone().lerp(lin(COL.luz), 0.55).multiplyScalar(oscuro ? 1.08 : 1.04);
      const cMarmolS = cMarmol.clone().multiplyScalar(0.88);
      const cEstuco = tonos.muro.clone().lerp(lin(COL.tierra_alta), 0.18).multiplyScalar(1.02);
      const cAlmo = cEstuco.clone().lerp(cPiedra, 0.45);
      const cTeja = tonos.techo.clone().lerp(tonos.mal, dia ? 0.14 : 0.06);
      const cTierra = lin(COL.tierra_alta).lerp(tonos.arena, 0.55).multiplyScalar(oscuro ? 0.95 : 0.9);
      const cCalz = cTierra.clone().lerp(tonos.calle, 0.35).multiplyScalar(0.92), cCalzC = cCalz.clone().multiplyScalar(1.05);
      const cAcera = tonos.arena.clone().lerp(tonos.pavimento, 0.35);
      const cSendero = cAcera.clone().lerp(cTierra, 0.25).multiplyScalar(1.03);
      const cPasto = tonos.campo.clone().lerp(tonos.verde, 0.4).multiplyScalar(dia ? 1.0 : 1.05), cPasto2 = cPasto.clone().lerp(tonos.campo2, 0.35);
      const cSeto = tonos.verde.clone().lerp(tonos.campo2, 0.25).multiplyScalar(oscuro ? 1.25 : 0.78);
      const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
      const cLaca = tonos.linea.clone().lerp(tonos.muro, oscuro ? 0.42 : 0.2);
      const cHierro = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.3) : tonos.asfalto.clone().lerp(tonos.linea, 0.6).multiplyScalar(0.6);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.22);
      const cBronce = tonos.linea.clone().lerp(tonos.techo, 0.5).lerp(tonos.medio, 0.12).multiplyScalar(oscuro ? 1.6 : 0.9);
      const cAgua = tonos.agua.clone(), cChorro = lin(COL.costa).lerp(tonos.agua, 0.3);
      const cLuz = lin(COL.luces);
      const PARCELAS = [tonos.campo.clone(), tonos.campo2.clone(), cTierra.clone().multiplyScalar(0.92), tonos.campo.clone().lerp(lin(COL.tierra_alta), 0.3),
        tonos.verde.clone().lerp(tonos.campo2, 0.5)];
      const CABALLOS = [tonos.techo.clone().multiplyScalar(0.62), tonos.linea.clone().lerp(tonos.muro, 0.3), tonos.muro.clone().multiplyScalar(0.82),
        lin(COL.tierra_alta).lerp(tonos.techo, 0.6).multiplyScalar(0.7)];
      const ROPA = [tonos.mal.clone(), tonos.medio.clone(), tonos.bien.clone(), lin(COL.costa).multiplyScalar(0.85), tonos.linea.clone().lerp(tonos.muro, 0.4),
        tonos.muro.clone().multiplyScalar(0.95)];
      const UP = [0, 1, 0], neg = (d) => [-d[0], -d[1], -d[2]];

      // ---- caras con la luz horneada (4 puntos; ref = hacia dónde es «afuera»)
      const cara = (acc, P, col, ref) => {
        const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
        let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
        const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
        if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx, ny, nz), q = acc.pos.length / 3;
        for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
        acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
      };
      const tri = (acc, P, col, ref) => cara(acc, [P[0], P[1], P[2], P[2]], col, ref);
      const tubo = (acc, A, B, r, seg, col, r2) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t, rr) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * rr), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        const rb = r2 === undefined ? r : r2;
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg;
          cara(acc, [S(A, o(t0, r)), S(A, o(t1, r)), S(B, o(t1, rb)), S(B, o(t0, rb))], col, o((t0 + t1) / 2, 1));
        }
      };
      const gema = (acc, P, rx, ry, rz, rot, col) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), c = new THREE.Color();
        for (let i = 0; i < oct.length; i += 9) {
          const v = [];
          for (let j = 0; j < 9; j += 3) { const x = oct[i + j] * rx, y = oct[i + j + 1] * ry, z = oct[i + j + 2] * rz; v.push([P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr]); }
          const e1 = [v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]], e2 = [v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; c.copy(col).multiplyScalar(sombra(nx / n, Math.abs(ny / n), nz / n));
          const q = acc.pos.length / 3;
          for (const w of v) { acc.pos.push(w[0], w[1], w[2]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2);
        }
      };
      // un elipsoide liso (lat × lon) en metros locales, ejes a lo largo de x, y, z
      const ovoide = (acc, C, rx, ry, rz, col, nl, nm) => {
        nl = nl || 8; nm = nm || 12;
        for (let i = 0; i < nl; i++) for (let j = 0; j < nm; j++) {
          const P = (a, b) => { const la = -PI / 2 + PI * a / nl, lo = TAU * b / nm; return [C[0] + rx * Math.cos(la) * Math.cos(lo), C[1] + ry * Math.sin(la), C[2] + rz * Math.cos(la) * Math.sin(lo)]; };
          const la = -PI / 2 + PI * (i + 0.5) / nl, lo = TAU * (j + 0.5) / nm;
          cara(acc, [P(i, j), P(i, j + 1), P(i + 1, j + 1), P(i + 1, j)], col, [Math.cos(la) * Math.cos(lo), Math.sin(la), Math.cos(la) * Math.sin(lo)]);
        }
      };
      const lamina = (acc, P, C) => {
        const R = P.length, Cn = P[0].length, q0 = acc.pos.length / 3;
        for (let i = 0; i < R; i++) for (let j = 0; j < Cn; j++) {
          const a = P[Math.max(0, i - 1)][j], b = P[Math.min(R - 1, i + 1)][j], c = P[i][Math.max(0, j - 1)], d = P[i][Math.min(Cn - 1, j + 1)];
          const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [d[0] - c[0], d[1] - c[1], d[2] - c[2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = sombra(nx / n, ny / n, nz / n), col = C[i][j];
          acc.pos.push(...P[i][j]); acc.col.push(col.r * l, col.g * l, col.b * l);
        }
        for (let i = 0; i + 1 < R; i++) for (let j = 0; j + 1 < Cn; j++) {
          const a = q0 + i * Cn + j, b = a + 1, c = a + Cn, d = c + 1;
          acc.idx.push(a, c, b, b, c, d);
        }
      };
      const sRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

      return piezas.map((p, np) => {
        const M = metros(1), sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const mats = [], poner = (acc, op, orden) => { const mat = malla.material(op || {}); mats.push(mat); const m = malla.poner(acc, mat, orden); return { mat, m }; };
        const nueva = () => malla.nueva();
        const suelo = (x, y) => ctx.suelo(x, y);
        // ---- el eje con su largo acumulado, su normal izquierda y su medio ancho
        const EJ = p.eje, NE = EJ.length, SS = [0], NX = [], NY = [], HH = p.anchos.map((w) => w / 2);
        for (let i = 1; i < NE; i++) SS.push(SS[i - 1] + Math.hypot(EJ[i][0] - EJ[i - 1][0], EJ[i][1] - EJ[i - 1][1]));
        for (let i = 0; i < NE; i++) {
          const a = EJ[Math.max(0, i - 1)], b = EJ[Math.min(NE - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
          NX.push(-(b[1] - a[1]) / L); NY.push((b[0] - a[0]) / L);
        }
        const LT = SS[NE - 1];
        // (x, y, dx, dy, h) en la posición s del eje (h: el medio ancho)
        const enS = (s) => {
          s = clamp(s, 0, LT); let k = 1; while (k < NE - 1 && SS[k] < s) k++;
          const a = EJ[k - 1], b = EJ[k], f = (s - SS[k - 1]) / Math.max(1e-6, SS[k] - SS[k - 1]), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
          return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / L, (b[1] - a[1]) / L, HH[k - 1] + (HH[k] - HH[k - 1]) * f];
        };
        const P3 = (x, y, h) => [x, suelo(x, y) + h * M, -y];
        // un punto del corte: fracción f del medio ancho (+ izquierda), en el vértice i
        const enCorte = (i, f, lev, dv) => { const x = EJ[i][0] + NX[i] * (f * HH[i] + (dv || 0) * M), y = EJ[i][1] + NY[i] * (f * HH[i] + (dv || 0) * M); return P3(x, y, lev); };

        // ================= EL PASEO: las franjas del corte (una lámina por material)
        const pis = nueva(), jard = nueva(), bord = nueva(), inicio = nueva();
        const franja = (acc, cols, colFn) => {          // cols: [[f, lev, dv]…] de izquierda a derecha en el corte
          const P = [], C = [];
          for (let i = 0; i < NE; i++) { P.push(cols.map(([f, lev, dv]) => enCorte(i, f, lev, dv))); C.push(cols.map((c, j) => colFn(i, j))); }
          lamina(acc, P, C);
        };
        const tono = (c, i, k) => c.clone().multiplyScalar(0.95 + 0.08 * hz(Math.floor(SS[i] / (6 * M)) + k * 977, 3));
        for (const sg of [1, -1]) {
          const o = (f) => sg * f;
          // la calzada abombada (de B1 a B2): centro más alto
          franja(pis, [[o(B1), 0.16, sg * 0.35], [o((B1 + B2) / 2), 0.3], [o(B2), 0.16, -sg * 0.35]], (i, j) => tono(j === 1 ? cCalzC : cCalz, i, sg));
          // la acera (B3 a B4)
          franja(pis, [[o(B3), 0.3, sg * 0.25], [o(B4), 0.3]], (i) => tono(cAcera, i, 3 + sg));
          // el jardín lateral (B2 a B3) y el central (0 a B1, con el sendero al medio)
          franja(jard, [[o(B2), 0.3, sg * 0.3], [o(B3), 0.3, -sg * 0.3]], (i, j) => tono(j ? cPasto : cPasto2, i, 7 + sg));
          franja(jard, [[o(0), 0.33, sg * 1.1], [o(B1), 0.33, -sg * 0.32]], (i, j) => tono(j ? cPasto2 : cPasto, i, 11 + sg));
        }
        franja(pis, [[0, 0.36, 1.1], [0, 0.36, -1.1]], (i) => tono(cSendero, i, 21));
        // los bordillos de piedra (entre jardín y calzada) y el seto bajo (entre jardín lateral y acera), con sus claros
        const cordon = (acc, f, dv, ancho, alto, lev, col, claro) => {
          for (let i = 0; i + 1 < NE; i++) {
            if (claro && hz(Math.floor(SS[i] / (claro * M)), 31 + Math.round(f * 50)) < 0.18) continue;
            const A0 = enCorte(i, f, lev, dv - ancho / 2), A1 = enCorte(i, f, lev, dv + ancho / 2), B0 = enCorte(i + 1, f, lev, dv - ancho / 2), B1_ = enCorte(i + 1, f, lev, dv + ancho / 2);
            const up = (P) => [P[0], P[1] + alto * M, P[2]];
            cara(acc, [up(A0), up(B0), up(B1_), up(A1)], col, UP);
            const nl = [NX[i], 0, -NY[i]];
            cara(acc, [A1, B1_, up(B1_), up(A1)], col.clone().multiplyScalar(0.96), nl);
            cara(acc, [A0, B0, up(B0), up(A0)], col.clone().multiplyScalar(0.96), neg(nl));
          }
        };
        for (const sg of [1, -1]) {
          cordon(bord, sg * B1, -sg * 0.15, 0.3, 0.22, 0.14, cPiedraL);
          cordon(bord, sg * B2, sg * 0.15, 0.3, 0.22, 0.14, cPiedraL);
          cordon(jard, sg * B3, -sg * 0.55, 0.7, 0.75, 0.28, cSeto, 26);
        }
        // el inicio (para resaltar): una franja a lo ancho de los primeros 40 m
        {
          const P = [], C = [], n = SS.findIndex((s) => s > 40 * M);
          for (let i = 0; i <= Math.max(1, n); i++) { P.push([-1, -0.5, 0, 0.5, 1].map((f) => enCorte(i, f, 0.42))); C.push([0, 1, 2, 3, 4].map(() => tonos.acento.clone())); }
          lamina(inicio, P, C);
        }

        // ================= EL CAMPO: parcelas a los dos lados (y más allá de las puntas), sobre el suelo
        const campo = nueva();
        {
          const EXT = 150 * M, ANCHOC = 240 * M, paso = 3;
          const filas = [];                                                  // [x, y, nx, ny, h, s]
          for (let s = -EXT; s < 0; s += 24 * M) { const [x, y, dx, dy, h] = enS(0); filas.push([x + dx * s, y + dy * s, -dy, dx, h, s, true]); }
          for (let i = 0; i < NE; i += paso) filas.push([EJ[i][0], EJ[i][1], NX[i], NY[i], HH[i], SS[i], false]);
          filas.push([EJ[NE - 1][0], EJ[NE - 1][1], NX[NE - 1], NY[NE - 1], HH[NE - 1], LT, false]);
          for (let s = LT + 24 * M; s <= LT + EXT; s += 24 * M) { const [x, y, dx, dy, h] = enS(LT); filas.push([x + dx * (s - LT), y + dy * (s - LT), -dy, dx, h, s, true]); }
          for (const sg of [1, -1]) {
            const P = [], C = [];
            for (const [x, y, nx, ny, h, s, fuera] of filas) {
              const fila = [], fc = [];
              for (let j = 0; j <= 12; j++) {
                const v = sg * ((fuera ? 0 : h) + ANCHOC * j / 12), px = x + nx * v, py = y + ny * v;
                fila.push(P3(px, py, 0.55));
                const cel = Math.floor(s / (95 * M)) * 31 + Math.floor((v * sg) / (70 * M)) * 7 + (sg > 0 ? 0 : 500);
                const k = Math.floor(hz(cel, 41) * PARCELAS.length);
                fc.push(PARCELAS[k].clone().multiplyScalar(0.92 + 0.12 * hz(cel, 42)));
              }
              P.push(fila); C.push(fc);
            }
            lamina(campo, P, C);
          }
        }
        poner(campo, { desfase: 2 }, 1);

        // ================= los marcos locales de un edificio (s a lo largo de (fx, fy) rotado −90°, t hacia (fx, fy))
        const marco = (cx, cy, fx, fy, ext) => {
          const sx = fy, sy = -fx;
          let y0 = suelo(cx, cy);
          if (ext) for (const [ss, tt] of [[-ext[0], -ext[1]], [ext[0], -ext[1]], [-ext[0], ext[1]], [ext[0], ext[1]], [0, 0]]) y0 = Math.min(y0, suelo(cx + (sx * ss + fx * tt) * M, cy + (sy * ss + fy * tt) * M));
          const F = (s, t, y) => [cx + (sx * s + fx * t) * M, y0 + y * M, -(cy + (sy * s + fy * t) * M)];
          return { F, S: [sx, 0, -sy], T: [fx, 0, -fy] };
        };
        const caja = (acc, B, s0, s1, t0, t1, y0, y1, col, sinTapa) => {
          const F = B.F;
          if (!sinTapa) cara(acc, [F(s0, t0, y1), F(s1, t0, y1), F(s1, t1, y1), F(s0, t1, y1)], col, UP);
          cara(acc, [F(s1, t0, y0), F(s1, t1, y0), F(s1, t1, y1), F(s1, t0, y1)], col, B.S);
          cara(acc, [F(s0, t0, y0), F(s0, t1, y0), F(s0, t1, y1), F(s0, t0, y1)], col, neg(B.S));
          cara(acc, [F(s0, t1, y0), F(s1, t1, y0), F(s1, t1, y1), F(s0, t1, y1)], col, B.T);
          cara(acc, [F(s0, t0, y0), F(s1, t0, y0), F(s1, t0, y1), F(s0, t0, y1)], col, neg(B.T));
        };
        const torno = (acc, B, s, t, perfil, seg, col) => {
          const F = B.F;
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
            for (let k = 0; k + 1 < perfil.length; k++) {
              const [r0, y0] = perfil[k], [r1, y1] = perfil[k + 1], nr = y1 - y0, ny = -(r1 - r0);
              const P = (rr, yy, a) => F(s + rr * Math.cos(a), t + rr * Math.sin(a), yy);
              const ref = [Math.cos(am) * nr * B.S[0] + Math.sin(am) * nr * B.T[0], ny, Math.cos(am) * nr * B.S[2] + Math.sin(am) * nr * B.T[2]];
              cara(acc, [P(r0, y0, a0), P(r0, y0, a1), P(r1, y1, a1), P(r1, y1, a0)], col, ref);
            }
          }
        };
        const brillos = [];
        // un vano sobre la cara t = tf (lado +1: mira a +T); arco: medio punto encima
        const vano = (accH, accL, B, tf, lado, s0, s1, y0, y1, prendido, arco) => {
          const F = B.F, t = tf + lado * 0.05, ref = lado > 0 ? B.T : neg(B.T), acc = prendido ? accL : accH, col = prendido ? cLuz.clone().multiplyScalar(0.9) : cHueco;
          cara(acc, [F(s0, t, y0), F(s1, t, y0), F(s1, t, y1), F(s0, t, y1)], col, ref);
          if (arco) { const r = (s1 - s0) / 2, sc = (s0 + s1) / 2; for (let k = 0; k < 6; k++) { const a0 = PI * k / 6, a1 = PI * (k + 1) / 6;
            tri(acc, [F(sc, t, y1), F(sc + r * Math.cos(a0), t, y1 + r * Math.sin(a0)), F(sc + r * Math.cos(a1), t, y1 + r * Math.sin(a1))], col, ref); } }
          if (prendido) brillos.push(F((s0 + s1) / 2, tf + lado * 0.6, (y0 + y1) / 2));
        };
        // lo mismo en las caras de s constante (los costados)
        const girar = (B) => ({ F: (s, t, y) => B.F(-t, s, y), S: B.T, T: neg(B.S) });

        // ================= LAS ESTATUAS (una malla cada una, para encenderlas en orden)
        const estatuas = [];
        p.estatuas.forEach((q, j) => {
          const acc = nueva(), B = marco(q[0], q[1], q[2], q[3], [0.9, 0.9]), F = B.F;
          caja(acc, B, -0.95, 0.95, -0.95, 0.95, -0.4, 0.38, cMarmolS);
          caja(acc, B, -0.8, 0.8, -0.8, 0.8, 0.38, 0.62, cMarmol);
          caja(acc, B, -0.58, 0.58, -0.58, 0.58, 0.62, 2.05, cMarmol);
          caja(acc, B, -0.74, 0.74, -0.74, 0.74, 2.05, 2.27, cMarmol);
          caja(acc, B, -0.62, 0.62, -0.62, 0.62, 2.27, 2.37, cMarmolS);
          const v = Math.floor(hz(j, 51) * 3), H0 = 2.37, alto = 1.95 + 0.15 * hz(j, 52);
          // la figura genérica: túnica, torso, cabeza y brazos; la pose varía (no se afirma ninguna)
          torno(acc, B, 0, 0, [[0.36, H0], [0.33, H0 + 0.12], [0.24, H0 + 0.5 * alto], [0.2, H0 + 0.62 * alto], [0.25, H0 + 0.78 * alto], [0.12, H0 + 0.84 * alto]], 12, cMarmol);
          ovoide(acc, F(0, 0.02, H0 + 0.91 * alto), 0.11 * M, 0.13 * M, 0.11 * M, cMarmol, 6, 10);
          const hom = (sg) => F(sg * 0.24, 0, H0 + 0.79 * alto);
          const manoA = v === 0 ? F(0.32, 0.25, H0 + 1.08 * alto) : v === 1 ? F(0.4, 0.38, H0 + 0.72 * alto) : F(0.18, 0.32, H0 + 0.6 * alto);
          const manoB = v === 2 ? F(-0.16, 0.3, H0 + 0.62 * alto) : F(-0.3, 0.05, H0 + 0.45 * alto);
          tubo(acc, hom(1), manoA, 0.07 * M, 6, cMarmol, 0.055 * M);
          tubo(acc, hom(-1), manoB, 0.07 * M, 6, cMarmol, 0.055 * M);
          if (v === 1) tubo(acc, F(0.4, 0.38, H0 + 0.72 * alto - 0.9), F(0.4, 0.38, H0 + 0.72 * alto + 0.5), 0.03 * M, 5, cMarmolS);   // un báculo genérico
          const { mat } = poner(acc, {}, 3);
          estatuas.push(mat);
        });

        // ================= LAS FUENTES (genéricas: pila redonda, pedestal, taza, remate) y LOS ESTANQUES
        const fuentes = nueva(), agua = nueva(), chorros = [];
        p.fuentes.forEach((q, j) => {
          const B = marco(q[0], q[1], q[2], q[3], [3.4, 3.4]), F = B.F;
          torno(fuentes, B, 0, 0, [[3.5, 0.2], [3.5, 0.62], [3.15, 0.66], [3.1, 0.4]], 24, cPiedraL);
          caja(fuentes, B, -3.7, 3.7, -3.7, 3.7, 0.0, 0.22, cPiedra);
          torno(agua, B, 0, 0, [[3.12, 0.48], [0.4, 0.48]], 24, cAgua);
          torno(fuentes, B, 0, 0, [[0.55, 0.48], [0.42, 0.9], [0.3, 1.45], [0.38, 1.55]], 12, cPiedraL);
          torno(fuentes, B, 0, 0, [[0.38, 1.5], [1.15, 1.62], [1.2, 1.78], [1.05, 1.76]], 16, cPiedraL);
          torno(agua, B, 0, 0, [[1.06, 1.72], [0.2, 1.72]], 16, cAgua);
          torno(fuentes, B, 0, 0, [[0.22, 1.72], [0.16, 2.3], [0.3, 2.45], [0.06, 2.75]], 10, cPiedraL);
          if (j === 1) {                                                     // en la del medio, una figura genérica de remate
            torno(fuentes, B, 0, 0, [[0.2, 2.6], [0.17, 3.2], [0.2, 3.45], [0.08, 3.55]], 10, cMarmol);
            ovoide(fuentes, F(0, 0, 3.66), 0.09 * M, 0.11 * M, 0.09 * M, cMarmol, 5, 8);
            tubo(fuentes, F(0.12, 0, 3.4), F(0.32, 0.1, 3.95), 0.045 * M, 5, cMarmol);
            tubo(fuentes, F(0.32, 0.1, 3.4), F(0.32, 0.1, 4.3), 0.025 * M, 4, cMarmolS);
          }
          chorros.push({ C: F(0, 0, 0), alto: j === 1 ? 3.6 : 2.7 });
        });
        p.estanques.forEach((q) => {
          const B = marco(q[0], q[1], -q[3], q[2], [8, 3]), N = 28, RA = 7.6, RB = 2.5;   // largo a lo largo del paseo
          for (let i = 0; i < N; i++) {
            const a0 = TAU * i / N, a1 = TAU * (i + 1) / N, P = (k, a, y) => B.F(RA * k * Math.cos(a), RB * k * Math.sin(a), y);
            cara(fuentes, [P(1, a0, 0.6), P(1, a1, 0.6), P(1.1, a1, 0.6), P(1.1, a0, 0.6)], cPiedraL, UP);
            cara(fuentes, [P(1.1, a0, 0.15), P(1.1, a1, 0.15), P(1.1, a1, 0.6), P(1.1, a0, 0.6)], cPiedra, [Math.cos((a0 + a1) / 2) * B.S[0] + Math.sin((a0 + a1) / 2) * B.T[0], 0, Math.cos((a0 + a1) / 2) * B.S[2] + Math.sin((a0 + a1) / 2) * B.T[2]]);
            tri(agua, [B.F(0, 0, 0.46), P(1, a0, 0.46), P(1, a1, 0.46)], cAgua.clone().multiplyScalar(0.96 + 0.06 * Math.cos(a0 * 2)), UP);
          }
        });

        // ================= EL PALACIO, la explanada y el monumento ecuestre (genéricos)
        const pal = nueva(), palL = nueva();
        const caballoGeo = (acc, O, k, col, conJinete, colJ) => {         // un caballo en metros locales (x adelante), para el monumento
          const P = (x, y, z) => [O[0] + x * k, O[1] + y * k, O[2] + z * k];
          ovoide(acc, P(0, 1.38, 0), 0.95 * k, 0.4 * k, 0.33 * k, col, 7, 12);
          tubo(acc, P(0.7, 1.55, 0), P(1.15, 2.15, 0), 0.22 * k, 8, col, 0.15 * k);
          tubo(acc, P(1.12, 2.22, 0), P(1.62, 1.9, 0), 0.14 * k, 8, col, 0.09 * k);
          for (const [x, z, ang] of [[0.62, 0.17, -0.5], [0.62, -0.17, 0.1], [-0.6, 0.17, 0.2], [-0.6, -0.17, -0.15]]) {
            const A = P(x, 1.2, z), B2_ = P(x + Math.sin(ang) * 0.55, 0.65, z), C = P(x + Math.sin(ang) * 0.3, 0.02, z);
            tubo(acc, A, B2_, 0.1 * k, 6, col, 0.07 * k); tubo(acc, B2_, C, 0.065 * k, 6, col, 0.055 * k);
          }
          tubo(acc, P(-0.92, 1.5, 0), P(-1.18, 0.75, 0), 0.07 * k, 5, col, 0.03 * k);
          if (conJinete) {
            tubo(acc, P(0.05, 1.7, 0), P(0.0, 2.45, 0), 0.2 * k, 8, colJ, 0.17 * k);
            ovoide(acc, P(0.02, 2.62, 0), 0.12 * k, 0.14 * k, 0.12 * k, colJ, 5, 8);
            for (const z of [0.3, -0.3]) tubo(acc, P(0.05, 1.75, z * 0.6), P(0.2, 1.05, z), 0.07 * k, 5, colJ);
            tubo(acc, P(0.02, 2.32, 0.2), P(0.55, 2.35, 0.32), 0.05 * k, 5, colJ);
            tubo(acc, P(0.02, 2.32, -0.2), P(0.45, 2.0, -0.25), 0.05 * k, 5, colJ);
          }
        };
        let palMats = [];
        if (p.palacio) {
          const q = p.palacio, B = marco(q[0], q[1], q[2], q[3], [27, 15]), F = B.F;
          const W = 25, D = 13, H1 = 6, H2 = 13, HC = 16.5;
          caja(pal, B, -W - 1.2, W + 1.2, -D - 1.2, D + 1.2, -3, 0.8, cPiedra);                         // zócalo
          for (let k = 0; k < 4; k++) caja(pal, B, -7 + k * 0.4, 7 - k * 0.4, D + 1.2 + (3 - k) * 0.55, D + 1.2 + (4 - k) * 0.55, -1, 0.8 - (3 - k) * 0.2, cPiedraL);   // escalinata
          caja(pal, B, -W, W, -D, D, 0.8, H1, cAlmo, true);                                           // planta baja almohadillada
          for (let y = 1.55; y < H1; y += 0.75) caja(pal, B, -W - 0.06, W + 0.06, -D - 0.06, D + 0.06, y, y + 0.09, cAlmo.clone().multiplyScalar(0.84), true);
          caja(pal, B, -W - 0.25, W + 0.25, -D - 0.25, D + 0.25, H1, H1 + 0.45, cPiedraL);              // imposta
          caja(pal, B, -W, W, -D, D, H1 + 0.45, H2, cEstuco, true);                                    // piso noble
          caja(pal, B, -W - 0.7, W + 0.7, -D - 0.7, D + 0.7, H2, H2 + 0.9, cPiedraL);                  // cornisa
          caja(pal, B, -W - 0.35, W + 0.35, -D - 0.35, D + 0.35, H2 + 0.9, H2 + 1.1, cPiedraL);
          for (let s = -W + 0.6; s <= W - 0.6; s += 0.8) for (const t of [D + 0.1, -D - 0.1]) caja(pal, B, s - 0.12, s + 0.12, t - 0.12, t + 0.12, H2 + 1.1, H2 + 1.85, cMarmolS);   // balaustres
          for (const t of [D, -D]) caja(pal, B, -W - 0.2, W + 0.2, t - 0.25, t + 0.25, H2 + 1.85, H2 + 2.05, cPiedraL);
          // el techo bajo de teja, detrás de la balaustrada
          { const y0 = H2 + 1.0, y1 = H2 + 4.0, a = W - 1.5, b = D - 1.5, c = 7;
            cara(pal, [F(-a, b, y0), F(a, b, y0), F(c, 0, y1), F(-c, 0, y1)], cTeja, B.T); cara(pal, [F(-a, -b, y0), F(a, -b, y0), F(c, 0, y1), F(-c, 0, y1)], cTeja.clone().multiplyScalar(0.92), neg(B.T));
            tri(pal, [F(a, b, y0), F(a, -b, y0), F(c, 0, y1)], cTeja.clone().multiplyScalar(0.96), B.S); tri(pal, [F(-a, b, y0), F(-a, -b, y0), F(-c, 0, y1)], cTeja.clone().multiplyScalar(0.96), neg(B.S)); }
          // pabellones de esquina (un poco salidos y más altos) y el cuerpo central con su frontón
          for (const sg of [-1, 1]) {
            const s0 = sg > 0 ? W - 6 : -W, s1 = sg > 0 ? W : -W + 6;
            caja(pal, B, s0, s1, D - 0.2, D + 1.0, 0.8, H2, cEstuco.clone().multiplyScalar(0.98));
            caja(pal, B, s0 - 0.4, s1 + 0.4, -D - 0.4, D + 1.4, H2, H2 + 2.6, cEstuco.clone().multiplyScalar(0.97));
            caja(pal, B, s0 - 0.7, s1 + 0.7, -D - 0.7, D + 1.7, H2 + 2.6, H2 + 3.1, cPiedraL);
            for (const s of [s0 + 0.2, s1 - 0.6]) caja(pal, B, s, s + 0.4, D + 1.0, D + 1.25, 0.8, H2, cPiedraL);   // esquinas
          }
          caja(pal, B, -8, 8, D, D + 2.6, 0.8, HC, cEstuco.clone().multiplyScalar(1.02));
          caja(pal, B, -8.5, 8.5, D - 0.5, D + 3.1, HC, HC + 0.7, cPiedraL);
          { const y0 = HC + 0.7, y1 = HC + 3.4, tF = D + 3.1;
            cara(pal, [F(-8.5, tF, y0), F(8.5, tF, y0), F(0, tF, y1), F(0, tF, y1)], cEstuco, B.T);
            cara(pal, [F(-8.5, tF, y0), F(0, tF, y1), F(0, D - 0.5, y1), F(-8.5, D - 0.5, y0)], cTeja, neg(B.S));
            cara(pal, [F(8.5, tF, y0), F(0, tF, y1), F(0, D - 0.5, y1), F(8.5, D - 0.5, y0)], cTeja.clone().multiplyScalar(0.94), B.S);
            tubo(pal, F(-8.6, tF + 0.1, y0), F(0, tF + 0.1, y1 + 0.1), 0.16 * M, 4, cPiedraL); tubo(pal, F(8.6, tF + 0.1, y0), F(0, tF + 0.1, y1 + 0.1), 0.16 * M, 4, cPiedraL); }
          for (const s of [-7.4, -2.6, 2.6, 7.4]) { tubo(pal, F(s, D + 2.75, H1 + 0.5), F(s, D + 2.75, HC - 0.1), 0.32 * M, 12, cMarmolS, 0.28 * M);   // pilastras/columnas del piso noble
            caja(pal, B, s - 0.45, s + 0.45, D + 2.4, D + 3.1, HC - 0.4, HC, cPiedraL); }
          // la arcada de la planta baja del cuerpo central y la puerta
          for (let k = -2; k <= 2; k++) { const sc = k * 3.0; vano(pal, palL, B, D + 2.6, 1, sc - 1.0, sc + 1.0, 0.8, 4.0, noche && k === 0, true);
            caja(pal, B, sc + 1.0, sc + 2.0, D + 2.5, D + 2.85, 0.8, 5.2, cAlmo.clone().multiplyScalar(0.95)); }
          // las ventanas: planta baja con arco, piso noble con frontón o cornisa; en las cuatro caras
          const ventanas = (BB, tf, ancho, sinCentro) => {
            for (let s = -ancho + 2.2; s <= ancho - 2.2; s += 3.6) {
              if (sinCentro && Math.abs(s) < 8.6) continue;
              const pr = (y) => noche && hz(Math.round(s * 10) + Math.round(tf * 7) + y, 61) < 0.42;
              vano(pal, palL, BB, tf, 1, s - 0.7, s + 0.7, 2.0, 4.3, pr(1), true);
              vano(pal, palL, BB, tf, 1, s - 0.75, s + 0.75, H1 + 1.6, H1 + 4.6, pr(2), false);
              caja(pal, BB, s - 1.05, s + 1.05, tf, tf + 0.35, H1 + 4.7, H1 + 5.0, cPiedraL);
              if (Math.round((s + ancho) / 3.6) % 2) { const t1 = tf + 0.3; cara(pal, [BB.F(s - 1.1, t1, H1 + 5.0), BB.F(s + 1.1, t1, H1 + 5.0), BB.F(s, t1, H1 + 5.7), BB.F(s, t1, H1 + 5.7)], cPiedraL, BB.T); }
              caja(pal, BB, s - 0.95, s + 0.95, tf, tf + 0.25, H1 + 1.35, H1 + 1.6, cPiedraL);
            }
          };
          ventanas(B, D + 0.0, W - 6.5, true);
          ventanas({ F: (s, t, y) => B.F(-s, -t, y), S: neg(B.S), T: neg(B.T) }, D, W - 1, false);
          ventanas(girar(B), W, D - 1, false);
          ventanas({ F: (s, t, y) => B.F(t, -s, y), S: neg(B.T), T: B.S }, W, D - 1, false);
          // la explanada al frente y el monumento ecuestre
          const Ep = marco(p.plaza[0], p.plaza[1], q[2], q[3], [26, 18]);
          { const ex = nueva(), Ff = Ep.F, n = 8;
            const PP = [], CC = [];
            for (let i = 0; i <= n; i++) { const fila = [], fc = []; for (let j = 0; j <= n; j++) { const s = -30 + 60 * j / n, t = -18 + 36 * i / n, [x, , zz] = Ff(s, t, 0); fila.push(P3(x, -zz, 0.7)); fc.push(cAcera.clone().multiplyScalar(0.97 + 0.05 * hz(i * 11 + j, 71))); } PP.push(fila); CC.push(fc); }
            lamina(ex, PP, CC); poner(ex, { desfase: 3 }, 2); }
          const mo = p.monumento, Bm = marco(mo[0], mo[1], mo[2], mo[3], [3, 1.8]);
          caja(pal, Bm, -3.2, 3.2, -2.0, 2.0, -0.5, 0.6, cMarmolS); caja(pal, Bm, -2.6, 2.6, -1.45, 1.45, 0.6, 3.6, cMarmol); caja(pal, Bm, -2.9, 2.9, -1.7, 1.7, 3.6, 3.95, cMarmolS);
          { const O = Bm.F(0, 0, 3.95); const g = nueva(); caballoGeo(g, [0, 0, 0], 1.55, cBronce, true, cBronce);
            // a su marco: x local del caballo → la dirección del monumento (mira al paseo)
            const ax = Bm.T, az = Bm.S;
            for (let i = 0; i < g.pos.length; i += 3) { const x = g.pos[i], y = g.pos[i + 1], z = g.pos[i + 2]; g.pos[i] = O[0] + (ax[0] * x + az[0] * z) * M; g.pos[i + 1] = O[1] + y * M; g.pos[i + 2] = O[2] + (ax[2] * x + az[2] * z) * M; }
            for (const k of ["pos", "col"]) for (const v of g[k]) pal[k].push(v);
            const b0 = pal.pos.length / 3 - g.pos.length / 3; for (const ix of g.idx) pal.idx.push(ix + b0); }
          palMats.push(poner(pal, {}, 3).mat);
          const mL = poner(palL, { desfase: 1 }, 4).mat; mL.uniforms.uBrillo.value = noche ? 1.7 : 1; palMats.push(mL);
        }

        // ================= LAS QUINTAS (genéricas): casa de teja con corredor, tapia, huerto, galera
        const qu = nueva(), quL = nueva(), arbolesQ = [];
        p.quintas.forEach((q, j) => {
          const v = q[4], B = marco(q[0], q[1], q[2], q[3], [22, 18]), F = B.F;
          const W = 8 + 2 * v, D = 5 + v, H = v === 2 ? 7.2 : 4.0;
          // la tapia con su portón
          const TW = 22, TD = 18;
          for (const [s0, s1, t0, t1] of [[-TW, TW, -TD, -TD + 0.4], [-TW, -TW + 0.4, -TD, TD], [TW - 0.4, TW, -TD, TD], [-TW, -2.2, TD - 0.4, TD], [2.2, TW, TD - 0.4, TD]]) {
            caja(qu, B, s0, s1, t0, t1, -0.6, 2.1, cEstuco.clone().multiplyScalar(0.93)); caja(qu, B, s0 - 0.08, s1 + 0.08, t0 - 0.08, t1 + 0.08, 2.1, 2.3, cTeja); }
          for (const sg of [-1, 1]) caja(qu, B, sg * 2.2 - 0.35, sg * 2.2 + 0.35, TD - 0.55, TD + 0.15, -0.6, 2.9, cPiedraL);
          caja(qu, B, -2.2, 2.2, TD - 0.1, TD + 0.05, 0.1, 2.2, cMadera);
          // el patio y el huerto
          { const P = [], C = []; for (let i = 0; i <= 4; i++) { const fila = [], fc = []; for (let k = 0; k <= 4; k++) { const [x, , z] = F(-TW + 2 * TW * k / 4, -TD + 2 * TD * i / 4, 0); fila.push(P3(x, -z, 0.7)); fc.push((i < 2 ? cPasto2 : cTierra).clone().multiplyScalar(0.95 + 0.06 * hz(j * 25 + i * 5 + k, 81))); } P.push(fila); C.push(fc); } lamina(qu, P, C); }
          // la casa: zócalo, muros, ventanas y puerta, el corredor con sus horcones y el techo de teja a cuatro aguas
          caja(qu, B, -W - 0.2, W + 0.2, -D - 0.2, D + 0.2, -0.6, 0.85, cPiedra);
          caja(qu, B, -W, W, -D, D, 0.85, H, cEstuco, true);
          for (let s = -W + 1.6; s <= W - 1.6; s += 3.2) {
            const pr = noche && hz(j * 41 + Math.round(s), 82) < 0.55;
            vano(qu, quL, B, D, 1, s - 0.55, s + 0.55, Math.abs(s) < 1.7 ? 0.45 : 1.3, Math.abs(s) < 1.7 ? 2.7 : 2.6, pr, false);
            if (v === 2) vano(qu, quL, B, D, 1, s - 0.5, s + 0.5, 4.4, 6.0, pr && hz(j, 83) < 0.6, false);
          }
          caja(qu, B, -W - 0.1, W + 0.1, D, D + 2.8, 0.2, 0.85, cPiedraL);
          for (let s = -W + 0.3; s <= W; s += (2 * W - 0.6) / 4) tubo(qu, F(s, D + 2.55, 0.45), F(s, D + 2.55, Math.min(H, 4.0) - 0.15), 0.12 * M, 8, cMadera);
          { const y0 = Math.min(H, 4.0) - 0.1, y1 = y0 + 0.55;
            cara(qu, [F(-W - 0.3, D + 3.0, y0), F(W + 0.3, D + 3.0, y0), F(W + 0.3, D, y1), F(-W - 0.3, D, y1)], cTeja.clone().multiplyScalar(0.95), B.T); }
          { const y0 = H, y1 = H + 2.4 + 0.2 * v, a = W + 0.7, b = D + 0.7, c = Math.max(0.5, W - D);
            cara(qu, [F(-a, b, y0), F(a, b, y0), F(c, 0, y1), F(-c, 0, y1)], cTeja, B.T); cara(qu, [F(-a, -b, y0), F(a, -b, y0), F(c, 0, y1), F(-c, 0, y1)], cTeja.clone().multiplyScalar(0.9), neg(B.T));
            tri(qu, [F(a, b, y0), F(a, -b, y0), F(c, 0, y1)], cTeja.clone().multiplyScalar(0.95), B.S); tri(qu, [F(-a, b, y0), F(-a, -b, y0), F(-c, 0, y1)], cTeja.clone().multiplyScalar(0.97), neg(B.S)); }
          tubo(qu, F(W - 2, -1, H + 0.5), F(W - 2, -1, H + 3.2), 0.3 * M, 8, cEstuco.clone().multiplyScalar(0.9));            // chimenea
          // la galera del fondo
          caja(qu, B, -TW + 2, -TW + 9, -TD + 1.5, -TD + 6, -0.3, 2.6, cEstuco.clone().multiplyScalar(0.9));
          cara(qu, [B.F(-TW + 1.6, -TD + 6.4, 2.6), B.F(-TW + 9.4, -TD + 6.4, 2.6), B.F(-TW + 9.4, -TD + 1.1, 3.6), B.F(-TW + 1.6, -TD + 1.1, 3.6)], cTeja, B.T);
          // árboles del huerto y de la entrada
          for (let k = 0; k < 7; k++) { const [x, , z] = F(-TW + 4 + (2 * TW - 8) * hz(j * 13 + k, 84), -TD + 3 + 9 * hz(j * 17 + k, 85), 0); arbolesQ.push([x, -z, 0.8 + 0.4 * hz(j * 7 + k, 86)]); }
          for (const sg of [-1, 1]) { const [x, , z] = F(sg * 6, TD + 4, 0); arbolesQ.push([x, -z, 1.1]); }
        });
        poner(qu, {}, 3);
        const mQL = poner(quL, { desfase: 1 }, 4).mat; mQL.uniforms.uBrillo.value = noche ? 1.7 : 1;

        // ================= las mallas fijas del paseo
        const pisM = poner(pis, { desfase: 3 }, 2).mat;
        const jardM = poner(jard, { desfase: 3 }, 2).mat;
        const bordM = poner(bord, { desfase: 1 }, 3).mat;
        const fuenM = poner(fuentes, {}, 3).mat;
        const aguaM = poner(agua, { desfase: 4 }, 3).mat;
        const iniR = poner(inicio, { alfa: 0.5, desfase: 6 }, 5); iniR.mat.uniforms.uAlfa.value = 0; iniR.m.visible = false;
        const jardines = [jardM, bordM, fuenM];

        // ================= LOS ÁRBOLES (instancias: no se rompen con el terremoto): fila en cada jardín lateral, el campo y las quintas
        const arb = [];
        for (const sg of [1, -1]) for (let s = 6 * M; s < LT - 4 * M; s += 14 * M) {
          const [x, y, , , h] = enS(s), i = Math.min(NE - 1, Math.round(s / (LT || 1) * (NE - 1)));
          const v = sg * h * (B2 + F_JARDIN * 0.5);
          if (p.estanques.some((q) => Math.hypot(q[0] - (x + NX[i] * v), q[1] - (y + NY[i] * v)) < 10 * M)) continue;
          arb.push([x + NX[i] * v, y + NY[i] * v, 0.85 + 0.3 * hz(Math.round(s) * 3 + sg, 91)]);
        }
        for (let k = 0; k < 46; k++) {                                         // árboles sueltos en el campo
          const s = -100 * M + (LT + 200 * M) * hz(k, 92), sg = hz(k, 93) < 0.5 ? 1 : -1, [x, y, dx, dy, h] = enS(s), ext = s < 0 ? s : s > LT ? s - LT : 0;
          const v = sg * (h + (20 + 200 * hz(k, 94)) * M);
          if (p.palacio && Math.hypot(x + dx * ext - dy * v - p.palacio[0], y + dy * ext + dx * v - p.palacio[1]) < 45 * M) continue;
          arb.push([x + dx * ext - dy * v, y + dy * ext + dx * v, 0.8 + 0.6 * hz(k, 95)]);
        }
        for (const a of arbolesQ) arb.push(a);
        const flA = arb.length ? ctx.flota("arbol", arb.length, { tamano: 1.05, orden: 4, lev: 0.45, semilla: 5 }) : null;
        if (flA) { arb.forEach((a, i) => { const g = TAU * hz(i, 96); flA.poner(i, a[0], a[1], Math.cos(g), Math.sin(g), a[2], 0); }); flA.listo(); }

        // ================= EL AGUA DE LAS FUENTES (puntos por shader: chorro del remate a la taza y de la taza a la pila)
        const uPx = { value: 1 }, uT = { value: 0 };
        if (chorros.length) {
          const NC = 22, NG = 6, N = chorros.length * NC * NG, g = new THREE.BufferGeometry(), pos = new Float32Array(N * 3), fa = new Float32Array(N * 4);
          let i = 0;
          chorros.forEach((ch, f) => { for (let c = 0; c < NC; c++) for (let j = 0; j < NG; j++, i++) {
            const alto = c < 8, an = TAU * (c % (alto ? 8 : 14)) / (alto ? 8 : 14) + (alto ? 0.2 : 0);
            pos.set(ch.C, i * 3); fa.set([an, alto ? ch.alto : 0, j / NG, hz(i, 97)], i * 4); } });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 4));
          const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, cA: { value: cChorro.clone() }, uK: { value: noche ? 0.45 : 0.8 } },
            transparent: true, depthWrite: false,
            vertexShader: "uniform float uPx, uT, uM; attribute vec4 aF; varying float vA; void main(){ float alto = aF.y; float per = alto > 0.5 ? 1.1 : 0.85; float a = fract(uT / per + aF.z + aF.w * 0.13); vec2 d = vec2(cos(aF.x), sin(aF.x)); float r, h; if (alto > 0.5) { r = 0.15 + 0.85 * a; h = alto + 1.6 * a * (1.0 - a) - (alto - 1.75) * a * a; } else { r = 1.2 + 0.5 * a; h = 1.75 - 1.25 * a * a; } vec3 p = position + vec3(d.x * r, h, d.y * r) * uM; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(0.16 * uM * uPx / max(1e-3, -mv.z), 1.0, 14.0); vA = smoothstep(0.0, 0.08, a) * (1.0 - smoothstep(0.85, 1.0, a)); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * (1.0 - r * r); gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }

        // ================= LOS CARRUAJES (un caballo; armados en metros locales: x adelante, y arriba, z a la derecha)
        const matMov = malla.material({}); mats.push(matMov);
        const matFarol = malla.material({}); matFarol.uniforms.uBrillo.value = noche ? 1.8 : 1; mats.push(matFarol);
        const I = { F: (s, t, y) => [s, y, t], S: [1, 0, 0], T: [0, 0, 1] };
        const ruedaGeo = (R) => {
          const acc = nueva(), N = 16, a2 = 0.1;
          for (let i = 0; i < N; i++) {
            const a0 = TAU * i / N, a1 = TAU * (i + 1) / N, am = (a0 + a1) / 2, P = (rr, a, z) => [rr * Math.cos(a), rr * Math.sin(a), z];
            for (const [rA, rB, zA, zB, ref] of [[R, R, -0.05, 0.05, [Math.cos(am), Math.sin(am), 0]], [R - a2, R - a2, 0.05, -0.05, [-Math.cos(am), -Math.sin(am), 0]],
              [R, R - a2, 0.05, 0.05, [0, 0, 1]], [R - a2, R, -0.05, -0.05, [0, 0, -1]]])
              cara(acc, [P(rA, a0, zA), P(rA, a1, zA), P(rB, a1, zB), P(rB, a0, zB)], cLaca, ref);
          }
          for (let i = 0; i < 10; i++) { const a = TAU * i / 10; tubo(acc, [0, 0, 0], [(R - 0.08) * Math.cos(a), (R - 0.08) * Math.sin(a), 0], 0.022, 4, cMadera); }
          tubo(acc, [0, 0, -0.1], [0, 0, 0.1], 0.09, 8, cHierro);
          return acc;
        };
        const coche = () => {
          const acc = nueva();
          caja(acc, I, -1.45, 0.85, -0.72, 0.72, 0.85, 1.95, cLaca);                                   // la caja
          caja(acc, I, -1.55, 0.95, -0.78, 0.78, 1.95, 2.08, cLaca.clone().multiplyScalar(0.85));      // el techo
          for (const z of [0.73, -0.73]) { cara(acc, [[-1.2, 1.35, z], [-0.25, 1.35, z], [-0.25, 1.85, z], [-1.2, 1.85, z]], cHueco, [0, 0, Math.sign(z)]);
            cara(acc, [[0.0, 1.35, z], [0.65, 1.35, z], [0.65, 1.85, z], [0.0, 1.85, z]], cHueco, [0, 0, Math.sign(z)]); }
          caja(acc, I, 0.85, 1.55, -0.6, 0.6, 1.2, 1.32, cLaca);                                       // el pescante
          caja(acc, I, 1.4, 1.75, -0.55, 0.55, 0.75, 0.82, cLaca);                                     // el estribo
          for (const z of [0.82, -0.82]) caja(acc, I, -1.3, 1.6, z - 0.03, z + 0.03, 0.62, 0.68, cHierro);   // largueros
          for (const z of [0.45, -0.45]) tubo(acc, [1.5, 0.9, z], [4.05, 1.1, z * 0.75], 0.04, 5, cMadera);  // varas
          // el cochero (genérico): torso, cabeza y sombrero
          tubo(acc, [1.05, 1.32, 0], [1.05, 1.95, 0], 0.2, 8, cLaca.clone().lerp(tonos.muro, 0.25), 0.17);
          ovoide(acc, [1.05, 2.08, 0], 0.11, 0.12, 0.11, tonos.muro.clone().lerp(tonos.techo, 0.45), 5, 8);
          tubo(acc, [1.05, 2.17, 0], [1.05, 2.42, 0], 0.11, 10, cLaca.clone().multiplyScalar(0.7));
          cara(acc, [[0.85, 2.18, -0.2], [1.25, 2.18, -0.2], [1.25, 2.18, 0.2], [0.85, 2.18, 0.2]], cLaca.clone().multiplyScalar(0.7), UP);
          for (const z of [0.4, -0.4]) tubo(acc, [1.05, 1.75, z * 0.5], [1.4, 1.45, z * 0.4], 0.05, 5, cLaca);
          return acc;
        };
        const farol = () => { const acc = nueva(); for (const z of [0.8, -0.8]) caja(acc, I, 0.8, 0.98, z - 0.08, z + 0.08, 1.75, 2.0, cLuz.clone().multiplyScalar(noche ? 1 : 0.6)); return acc; };
        const caballo = (col) => {
          const acc = nueva(), O = 3.1;
          ovoide(acc, [O, 1.38, 0], 0.95, 0.38, 0.32, col, 7, 12);
          tubo(acc, [O + 0.72, 1.52, 0], [O + 1.12, 2.08, 0], 0.21, 8, col, 0.14);
          tubo(acc, [O + 1.1, 2.15, 0], [O + 1.58, 1.82, 0], 0.13, 8, col, 0.09);
          for (const z of [0.06, -0.06]) tubo(acc, [O + 1.02, 2.2, z], [O + 0.98, 2.4, z * 2], 0.04, 4, col, 0.01);
          tubo(acc, [O + 0.78, 1.95, 0], [O + 1.02, 2.28, 0], 0.08, 4, col.clone().multiplyScalar(0.55));   // la crin
          tubo(acc, [O - 0.92, 1.5, 0], [O - 1.15, 0.8, 0], 0.07, 5, col.clone().multiplyScalar(0.6), 0.03);
          tubo(acc, [O + 0.1, 1.05, -0.36], [O + 0.1, 1.75, -0.36], 0.03, 4, cLaca); tubo(acc, [O + 0.1, 1.05, 0.36], [O + 0.1, 1.75, 0.36], 0.03, 4, cLaca);   // el arnés
          return acc;
        };
        const pataGeo = (col) => { const acc = nueva(); tubo(acc, [0, 0, 0], [0, -0.55, 0], 0.09, 6, col, 0.065); tubo(acc, [0, -0.55, 0], [0, -1.1, 0], 0.06, 6, col, 0.05);
          tubo(acc, [0, -1.1, 0], [0, -1.18, 0], 0.07, 6, col.clone().multiplyScalar(0.4)); return acc; };
        const mesh = (acc, mat, orden) => { const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden || 4; return m; };
        // los carriles de los carruajes (corridos del eje) y las sendas de la gente, con su largo acumulado
        const sendero = (f, dv, rev) => {
          const pts = []; for (let i = 0; i < NE; i++) pts.push([EJ[i][0] + NX[i] * (f * HH[i] + dv * M), EJ[i][1] + NY[i] * (f * HH[i] + dv * M)]);
          if (rev) pts.reverse();
          const S = [0]; for (let i = 1; i < pts.length; i++) S.push(S[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
          return { pts, S, L: S[S.length - 1] };
        };
        const enRuta = (ru, q) => {
          let k = 1; while (k < ru.S.length - 1 && ru.S[k] < q) k++;
          const a = ru.pts[k - 1], b = ru.pts[k], f = (q - ru.S[k - 1]) / Math.max(1e-6, ru.S[k] - ru.S[k - 1]), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
          return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / L, (b[1] - a[1]) / L];
        };
        const cMed = (B1 + B2) / 2;
        const carriles = [sendero(-cMed, -0.9, false), sendero(cMed, 0.9, true)];
        const coches = [];
        for (let c = 0; c < p.carruajes; c++) {
          const g = new THREE.Group(), col = CABALLOS[(c + p.semilla) % CABALLOS.length];
          g.add(mesh(coche(), matMov)); g.add(mesh(farol(), matFarol)); g.add(mesh(caballo(col), matMov));
          const ruedas = [[-0.95, 0.62, 0.86], [-0.95, 0.62, -0.86], [0.5, 0.45, 0.84], [0.5, 0.45, -0.84]].map(([x, R, z]) => { const w = mesh(ruedaGeo(R), matMov); w.position.set(x, R, z); w.userData.R = R; g.add(w); return w; });
          const patas = [[3.72, 0.17, 0], [3.72, -0.17, PI], [2.48, 0.17, PI], [2.48, -0.17, 0]].map(([x, z, f]) => { const l = mesh(pataGeo(col), matMov); l.position.set(x, 1.18, z); l.userData.f = f; g.add(l); return l; });
          g.scale.setScalar(M); scene.add(g);
          coches.push({ g, ruedas, patas, ru: carriles[c % 2], s0: hz(c, 101), v: VCARRO * (0.85 + 0.3 * hz(c, 102)) });
        }

        // ================= LOS PASEANTES (genéricos): aceras, ida y vuelta, y el sendero del jardín central
        const sendas = [sendero(B3 + F_ACERA * 0.35, 0, false), sendero(-(B3 + F_ACERA * 0.35), 0, true), sendero(B3 + F_ACERA * 0.7, 0, true),
          sendero(-(B3 + F_ACERA * 0.7), 0, false), sendero(0, 0.5, false), sendero(0, -0.5, true)];
        const gente = [];
        for (let i = 0; i < p.paseantes; i++) {
          const ru = sendas[i % sendas.length], cerca = hz(i, 111) < 0.6;
          gente.push({ ru, s0: (cerca ? 0.3 + 0.4 * hz(i, 112) : hz(i, 112)) * ru.L, v: VPIE * (0.8 + 0.35 * hz(i, 113)) });
        }
        const EG = clamp(p.escala_gente || 1, 1, 2);
        const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: EG, orden: 6, lev: 0.32, semilla: (p.semilla * 13 + np * 7) % 991,
          color: (i) => ROPA[(i * 3 + p.semilla) % ROPA.length], pose: () => "caminar" }) : null;

        // ================= LOS GRUPOS DE PASEANTES (genéricos): de 2 a 4 juntos por las dos aceras, cerca de la mitad del tramo
        // (frente al jardín central, cada ≈ 40 m alrededor de la fuente del medio). Unos pasean a paso lento, ida y vuelta en un
        // trecho de 14–26 m; otros conversan de pie en corro. Ropa
        // genérica de época (no se afirma): todos con sombrero; las de falda larga, con un sombrero más chico.
        const grupos = [], miembros = [[], []];          // miembros[0]: con saco y sombrero de copa; [1]: falda larga
        const NG = p.grupos || 0, porLado = Math.ceil(NG / 2), fAce = B3 + F_ACERA * 0.5;
        for (let g = 0; g < NG; g++) {
          const lado = g % 2 === 0 ? 1 : -1, k = g >> 1;
          const ru = sendero(lado * fAce, 0, lado < 0);
          // a lo largo de cada acera, cada ≈ 40 m alrededor de la fuente del medio (la mitad del tramo), para que entren en
          // un encuadre de 45–60 m sobre el jardín central
          const c = 0.5 + ((k - (porLado - 1) / 2) * 40 + 8 * (hz(g, 131) - 0.5) + (lado > 0 ? 0 : 12)) * M / Math.max(1e-6, ru.L);
          const n = 2 + Math.floor(hz(g, 132) * 2.999), anda = hz(g, 133) < 0.6;
          const G = { ru, c: c * ru.L, anda, A: (7 + 6 * hz(g, 134)) * M, v: 0.75 + 0.2 * hz(g, 135), f0: hz(g, 136), m: [] };
          for (let j = 0; j < n; j++) {
            const dama = hz(g * 7 + j, 137) < 0.5 ? 1 : 0;
            // en fila de dos (de frente) o en corro (de pie), en metros y por el tamaño de la gente
            const off = anda ? [-(j >> 1) * 1.05 * EG, ((j % 2) - 0.5) * (n - (j >> 1) * 2 === 1 ? 0 : 0.66) * EG]
              : [Math.cos(TAU * j / n + hz(g, 138)) * 0.55 * EG, Math.sin(TAU * j / n + hz(g, 138)) * 0.55 * EG];
            G.m.push({ dama, idx: miembros[dama].length, off });
            miembros[dama].push({ anda, v: anda ? G.v : 0 });
          }
          grupos.push(G);
        }
        const cSaco = tonos.linea.clone().lerp(tonos.muro, oscuro ? 0.38 : 0.12), cSombrero = cSaco.clone().multiplyScalar(0.8);
        const cFalda = [tonos.muro.clone().lerp(tonos.medio, 0.3), lin(COL.costa).lerp(tonos.muro, 0.4), tonos.mal.clone().lerp(tonos.muro, 0.45)];
        const ala = (r, y) => new THREE.CylinderGeometry(r, r, 0.018, 16).translate(0, y, 0);
        const copa = (r0, r1, h, y) => new THREE.CylinderGeometry(r0, r1, h, 14).translate(0, y + h / 2, 0);
        const flG = [null, null];
        if (miembros[0].length) {
          // saco largo hasta medio muslo (sobre el torso) y sombrero de copa baja
          const saco = new THREE.CylinderGeometry(0.2, 0.23, 0.5, 12).translate(0, CAD_PERS + 0.08, 0);
          flG[0] = ctx.flota("persona", miembros[0].length, { tamano: EG, orden: 6, lev: 0.32, semilla: (p.semilla * 17 + np * 3 + 5) % 991,
            color: () => cSaco, pose: (i) => (miembros[0][i].anda ? "caminar" : "de_pie"),
            adjuntos: [{ geo: saco, color: cSaco, grupo: "torso" }, { geo: ala(0.16, 1.7), color: cSombrero, grupo: "cabeza" },
              { geo: copa(0.1, 0.105, 0.15, 1.7), color: cSombrero, grupo: "cabeza" }] });
        }
        if (miembros[1].length) {
          // falda larga de campana hasta el tobillo y sombrero chico de ala
          const falda = new THREE.CylinderGeometry(0.16, 0.36, 0.84, 16).translate(0, 0.07 + 0.42, 0);
          const ruedo = new THREE.CylinderGeometry(0.37, 0.37, 0.05, 16).translate(0, 0.095, 0);
          flG[1] = ctx.flota("persona", miembros[1].length, { tamano: EG, orden: 6, lev: 0.32, semilla: (p.semilla * 19 + np * 5 + 9) % 991,
            color: (i) => cFalda[(i + p.semilla) % cFalda.length], pose: (i) => (miembros[1][i].anda ? "caminar" : "de_pie"),
            adjuntos: [{ geo: falda, color: cFalda[0], grupo: "cuerpo" }, { geo: ruedo, color: cFalda[0].clone().multiplyScalar(0.85), grupo: "cuerpo" },
              { geo: ala(0.14, 1.71), color: cFalda[2], grupo: "cabeza" }, { geo: copa(0.08, 0.09, 0.07, 1.71), color: cFalda[2], grupo: "cabeza" }] });
        }

        // ================= los brillos de las ventanas encendidas (de noche)
        if (brillos.length) {
          const g = new THREE.BufferGeometry(), pos = new Float32Array(brillos.length * 3), fa = new Float32Array(brillos.length);
          brillos.forEach((b, i) => { pos.set(b, i * 3); fa[i] = hz(i, 120); });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 1));
          const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uTam: { value: 3.6 * M }, cA: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "uniform float uPx, uTam, uT; attribute float aF; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(uTam * uPx / max(1e-3, -mv.z), 1.5, 26.0); vA = 0.85 + 0.1 * sin(uT * 5.3 + aF * 40.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.5 * vA * exp(-r * r * 4.5); gl_FragColor = vec4(srgb(cA) * a, a); }" });
          const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 9; scene.add(m);
        }

        // los resaltados de las estatuas en orden (índice 2): sus tiempos, del maqueta resuelto
        const ordenes = ((ctx.M && ctx.M.eventos) || []).filter((e) => e.tipo === "resaltar" && e.pieza === p.id && e.indice === 2).map((e) => [e.t, e.dur]);
        return { id: p.id, M, mats, uPx, uT, estatuas, palMats, jardines, iniR, coches, gente, flP, grupos, flG, miembros, ordenes, LT };
      });
    },
    en(t, lista, ctx) {
      const { clamp, tonos } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo && m.uniforms.uBrillo.value <= 1.36) m.uniforms.uBrillo.value = 1 + 0.35 * kb;
        s.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.uT.value = t;
        // ---- los elementos resaltados (todo desde cero en cada cuadro)
        const kE = new Array(s.estatuas.length).fill(0);
        let kP = 0, kJ = 0, kI = 0;
        for (const el of ctx.cuadro.elementos[s.id] || []) {
          const k = Math.min(1, el.k);
          if (el.i === 0) kP = Math.max(kP, k);
          else if (el.i === 1) kJ = Math.max(kJ, k);
          else if (el.i === 3) kI = Math.max(kI, k);
          else if (el.i >= 100 && el.i - 100 < kE.length) kE[el.i - 100] = Math.max(kE[el.i - 100], k);
          else if (el.i === 2) {
            const ev = s.ordenes.find(([t0, d]) => t >= t0 && t <= t0 + d), N = kE.length;
            const u = ev ? clamp((t - ev[0]) / Math.max(0.3, ev[1] * 0.75), 0, 1) * N : N;
            for (let j = 0; j < N; j++) kE[j] = Math.max(kE[j], k * clamp((u - j) * 1.5, 0, 1));
          }
        }
        const tinta = (m, k, br) => { m.uniforms.cTinte.value.copy(tonos.acento); m.uniforms.uTinte.value = 0.62 * k; if (br) m.uniforms.uBrillo.value = Math.max(m.uniforms.uBrillo.value, 1 + 0.3 * k); };
        s.estatuas.forEach((m, j) => tinta(m, kE[j], true));
        for (const m of s.palMats) tinta(m, kP, false);
        for (const m of s.jardines) tinta(m, kJ, false);
        s.iniR.mat.uniforms.uAlfa.value = 0.5 * kI; s.iniR.m.visible = kI > 0.001;
        // ---- los carruajes: van y vienen por su calzada (posición = función de t), entran y salen por las puntas
        for (const c of s.coches) {
          const ru = c.ru, LL = ru.L + 30 * s.M, q = (((c.s0 * LL + c.v * s.M * t) % LL) + LL) % LL - 15 * s.M;
          const vis = clamp(Math.min(q, ru.L - q) / (6 * s.M), 0, 1);
          if (vis <= 0) { c.g.visible = false; continue; }
          c.g.visible = true;
          const [x, y, dx, dy] = enRuta(ru, clamp(q, 0, ru.L));
          c.g.position.set(x, ctx.altura(x, y) + 0.22 * s.M, -y);
          c.g.rotation.set(0, Math.atan2(dy, dx), 0);
          c.g.scale.setScalar(s.M * vis);
          const d = c.s0 * 37 + c.v * t;
          for (const w of c.ruedas) w.rotation.z = -d / w.userData.R;
          const fase = d / 1.15 * Math.PI;
          for (const l of c.patas) l.rotation.z = 0.42 * Math.sin(fase + l.userData.f);
        }
        // ---- los paseantes: ida y vuelta por su senda
        if (s.flP) {
          s.gente.forEach((g, i) => {
            const L = g.ru.L || 1, q0 = g.s0 + g.v * s.M * t, m = ((q0 % (2 * L)) + 2 * L) % (2 * L), q = m > L ? 2 * L - m : m, sg = m > L ? -1 : 1;
            const [x, y, dx, dy] = enRuta(g.ru, q);
            s.flP.poner(i, x, y, dx * sg, dy * sg, 1, 0, g.v);
          });
          s.flP.listo();
        }
        // ---- los grupos: pasean juntos ida y vuelta por su trecho de acera (onda triangular de t) o conversan de pie
        if (s.grupos.length) {
          for (const G of s.grupos) {
            let q = G.c, sg = 1;
            if (G.anda) {
              const P = 4 * G.A / (G.v * s.M), u = (((t / P + G.f0) % 1) + 1) % 1;
              q = G.c + G.A * (u < 0.5 ? 4 * u - 1 : 3 - 4 * u); sg = u < 0.5 ? 1 : -1;
            }
            const [x, y, dx, dy] = enRuta(G.ru, clamp(q, 0, G.ru.L)), fx = dx * sg, fy = dy * sg;
            for (const mb of G.m) {
              const [a, b] = mb.off, px = x + (fx * a - fy * b) * s.M, py = y + (fy * a + fx * b) * s.M;
              const fl = s.flG[mb.dama];
              if (G.anda) fl.poner(mb.idx, px, py, fx, fy, 1, 0, G.v);
              else { const ox = x - px, oy = y - py, L = Math.hypot(ox, oy) || 1; fl.poner(mb.idx, px, py, ox / L, oy / L, 1, 0, 0); }
            }
          }
          for (const fl of s.flG) if (fl) fl.listo();
        }
      }
    },
  };
  // la posición sobre una senda (misma cuenta que en armar; fuera del cierre para `en`)
  function enRuta(ru, q) {
    let k = 1; while (k < ru.S.length - 1 && ru.S[k] < q) k++;
    const a = ru.pts[k - 1], b = ru.pts[k], f = (q - ru.S[k - 1]) / Math.max(1e-6, ru.S[k] - ru.S[k - 1]), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / L, (b[1] - a[1]) / L];
  }
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
