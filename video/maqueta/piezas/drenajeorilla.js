// Pieza «drenajeorilla» (ficha: drenajeorilla.json; reglas: scripts/maqueta_tipos/drenajeorilla.py): el drenaje de un pueblo
// de orilla, genérico, de cerca. Centrada en `lugar` (la línea del agua frente al pueblo) y orientada por `rumbo` (u: hacia
// el lago; v: a su izquierda). Todo en METROS × `tamano`. Sin lugar real, sin texto, sin marcas, sin personas reales.
// - EL PUEBLO: dos filas de casas genéricas (un piso con techo de dos aguas, o dos pisos con losa y tinaco) a los lados de
//   una calle con su colector y sus tapas de pozo; patios, muros bajos, árboles y faroles.
// - EL DRENAJE (un esquema: tubos a flor de tierra para que se lean): cada casa conectada baja a la calle por su tubo y su
//   caja de registro; las que no tienen conexión (`sin_drenaje`) llevan una fosa en el patio, sin tubo. Las casas con v ≥
//   `corte` (de `a_planta`) van por el colector a la PLANTA; las demás, a 1–3 DESAGÜES que bajan entre las casas del frente y
//   salen crudos a la playa: chorro, hilo de agua por la arena y una MANCHA turbia en el lago que respira (solo de ellos).
// - LA PLANTA DE TRATAMIENTO genérica, cercada: canal de rejas, tanque rectangular con burbujas, dos sedimentadores redondos
//   con su puente que gira, lechos de secado y un edificio bajo; su efluente sale a la orilla menos turbio y sin mancha (no se
//   pinta como agua limpia: muchas plantas no cumplen).
// - CON VIDA (todo función de t): el agua que corre por los tubos (pulsos), los chorros, la mancha y sus anillos, las
//   burbujas, los puentes que giran, destellos del lago, gente. De noche (ES.noche): ventanas, faroles y lámparas.
// Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto. «resaltar» la pieza aviva todo; el drenaje, más.
(function (MAQ) {
  const HL = 0.6, HA = 0.08, U_PLAYA = -12, U_CALLE = -60, AC = 3.2, U_TIERRA = -150, LV = 150, LU = 170;
  const HV0 = -95, HPASO = 15, NH = 10, FILAS = [-40, -82], SAL_V = 83, U_BOCA = -2.5;
  const PL = { u0: -54, u1: -11, v0: 50, v1: 114 };
  const CLAR = [[-20, 72], [-20, 94]], RCL = 5.5;
  const TAU = 2 * Math.PI;
  const piso = (u) => u < U_PLAYA ? HL : u < 0 ? HL + (HA + 0.04 - HL) * (u - U_PLAYA) / -U_PLAYA : HA;
  MAQ.PIEZAS.drenajeorilla = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      // ---- los tonos (todos del estilo)
      const cAgua = tonos.agua.clone(), cAguaH = tonos.agua.clone().multiplyScalar(oscuro ? 0.8 : 0.74).lerp(tonos.linea, 0.06);
      const cAguaB = tonos.agua.clone().lerp(tonos.verde, 0.2).lerp(tonos.arena, 0.12);
      const cArena = tonos.arena.clone(), cArenaM = tonos.arena.clone().lerp(cAgua, 0.25).multiplyScalar(0.82);
      const cPasto = tonos.campo.clone().lerp(tonos.verde, 0.4), cPasto2 = tonos.campo2.clone();
      const cPatio = tonos.calle.clone().lerp(tonos.pavimento, 0.5).multiplyScalar(dia ? 0.95 : 1);
      const cCalle = tonos.calle.clone().multiplyScalar(dia ? 0.9 : 1), cCuneta = tonos.calle.clone().multiplyScalar(0.75);
      const cMuros = [tonos.muro.clone(), tonos.muro.clone().lerp(lin(COL.tierra_alta), 0.25), tonos.muro.clone().lerp(lin(COL.costa), 0.3),
        tonos.muro.clone().lerp(tonos.secundario, 0.18), tonos.muro.clone().lerp(tonos.verde, 0.15)];
      const cZocalo = tonos.muro.clone().lerp(tonos.asfalto, 0.45), cTeja = tonos.techo.clone(), cTeja2 = tonos.techo.clone().multiplyScalar(0.82);
      const cLosaT = tonos.pavimento.clone().lerp(tonos.muro, 0.4).multiplyScalar(0.9);
      const cConcreto = tonos.pavimento.clone().lerp(tonos.muro, 0.35), cConcretoO = cConcreto.clone().multiplyScalar(0.72);
      const cTubo = tonos.asfalto.clone().lerp(tonos.pavimento, 0.55).multiplyScalar(dia ? 1.05 : 1.15), cTuboO = cTubo.clone().multiplyScalar(0.7);
      const cHueco = tonos.linea.clone().lerp(tonos.asfalto, 0.5).multiplyScalar(0.55);
      const cTurbio = lin(COL.tierra_media).lerp(tonos.arena, 0.3).lerp(cAgua, 0.22).multiplyScalar(oscuro ? 1.25 : 0.92);
      const cClara = cAgua.clone().lerp(lin(COL.costa), 0.3).lerp(cTurbio, 0.18);
      const cLodo = tonos.arena.clone().lerp(lin(COL.tierra_media), 0.55).multiplyScalar(oscuro ? 0.9 : 0.6);
      const cMojado = cArena.clone().lerp(cTurbio, 0.55).multiplyScalar(0.8);
      const cTronco = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.4).multiplyScalar(0.7);
      const cHoja = tonos.verde.clone().multiplyScalar(0.8), cHoja2 = tonos.verde.clone().lerp(lin(COL.tierra_media), 0.25).multiplyScalar(0.85);
      const cMetal = tonos.linea.clone().lerp(tonos.pavimento, 0.35), cBaranda = tonos.secundario.clone().lerp(tonos.linea, 0.3);
      const cVidrio = noche ? lin(COL.luces).lerp(lin(COL.costa), 0.25) : tonos.agua.clone().lerp(tonos.linea, 0.3).multiplyScalar(0.6);
      const cVidrioA = tonos.agua.clone().lerp(tonos.linea, 0.4).multiplyScalar(0.5);
      const cPuerta = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.35).multiplyScalar(0.75);
      const cEspuma = tonos.agua.clone().lerp(lin(COL.costa), 0.8), cBrillo = tonos.agua.clone().lerp(lin(COL.costa), 0.7);
      const cLuz = lin(COL.luces);
      const OCT = [new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array, new THREE.OctahedronGeometry(1, 1).toNonIndexed().attributes.position.array];

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
      const bx = (acc, X, x0, x1, y0, y1, z0, z1, col, op = {}) => {
        const C = X((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
        const F = [[[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]], [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]],
          [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]],
          [[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]], [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]]];
        F.forEach((q, k) => {
          if ((k === 0 && op.sinTope) || (k === 5 && !op.fondo)) return;
          const V = q.map((a) => X(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
          cara(acc, V, k === 0 && op.tope ? op.tope : (op.lados && k > 0 ? op.lados : col), m);
        });
      };
      const tubo = (acc, A, B, r, seg, col, tapa) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2));
          if (tapa) { cara(acc, [S(B, va), S(B, vb), B, B], tapa, a); cara(acc, [S(A, va), S(A, vb), A, A], tapa, a.map((x) => -x)); }
        }
      };
      const gema = (acc, P, rx, ry, rz, rot, col, fino) => {
        const oct = OCT[fino ? 1 : 0], cr = Math.cos(rot), sr = Math.sin(rot), c = new THREE.Color();
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

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.suelo ? ctx.suelo(p.x, p.y) : ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const XW = (x, y, z) => E(x, z, y);
        const cw = (acc, u0, u1, v0, v1, h0, h1, col, op) => bx(acc, XW, u0, u1, h0, h1, v0, v1, col, op);
        const twu = (acc, u0, v0, h0, u1, v1, h1, rr, seg, col, tapa) => tubo(acc, E(u0, v0, h0), E(u1, v1, h1), rr * M, seg, col, tapa);
        const quad = (acc, P4, col, ref) => cara(acc, P4.map(([u, v, h]) => E(u, v, h)), col, ref || [0, 1, 0]);
        const haciaU = (s) => [s * ux, 0.1, -s * uy], haciaV = (s) => [-s * uy, 0.1, -s * ux];
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const losa = (acc, u0, u1, v0, v1, cu, cv, hf, colf) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0), q0 = acc.pos.length / 3;
          for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) {
            const uu = u0 + (u1 - u0) * i / nu, vv = v0 + (v1 - v0) * j / nv, P = E(uu, vv, hf(uu, vv)), c = colf(uu, vv);
            acc.pos.push(P[0], P[1], P[2]); acc.col.push(c.r * l, c.g * l, c.b * l);
          }
          for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) { const a = q0 + i * (nv + 1) + j, b = a + nv + 1; acc.idx.push(a, b, b + 1, a, b + 1, a + 1); }
        };
        // un disco (u, v) a la altura h; anillos de color de adentro (c0) hacia afuera (c1)
        const disco = (acc, u, v, h, R, n, col) => { const C = E(u, v, h);
          for (let i = 0; i < n; i++) { const a0 = TAU * i / n, a1 = TAU * (i + 1) / n; cara(acc, [C, E(u + R * Math.cos(a0), v + R * Math.sin(a0), h), E(u + R * Math.cos(a1), v + R * Math.sin(a1), h), C], col, [0, 1, 0]); } };
        const cilU = (acc, u, v, h0, h1, R, n, col, tapa) => {
          for (let i = 0; i < n; i++) { const a0 = TAU * i / n, a1 = TAU * (i + 1) / n;
            cara(acc, [E(u + R * Math.cos(a0), v + R * Math.sin(a0), h0), E(u + R * Math.cos(a1), v + R * Math.sin(a1), h0), E(u + R * Math.cos(a1), v + R * Math.sin(a1), h1), E(u + R * Math.cos(a0), v + R * Math.sin(a0), h1)], col,
              [Math.cos((a0 + a1) / 2) * ux - Math.sin((a0 + a1) / 2) * uy, 0, -(Math.cos((a0 + a1) / 2) * uy + Math.sin((a0 + a1) / 2) * ux)]); }
          if (tapa) disco(acc, u, v, h1, R, n, tapa);
        };
        const nueva = () => malla.nueva();
        const mats = [], mDren = [];
        const poner = (acc, op, orden, lista) => { if (!acc.idx.length) return null; const m = new THREE.Mesh(malla.geometria(acc), malla.material(op || {})); m.frustumCulled = false; m.renderOrder = orden || 3; scene.add(m); (lista || mats).push(m.material); return m; };
        const geoLocal = (acc, P) => { const g = malla.geometria(acc); g.translate(-P[0], -P[1], -P[2]); return g; };
        const suelo = nueva(), agua = nueva(), solido = nueva(), techos = nueva(), vid = nueva(), plantas = nueva(), dren = nueva(), marcas = nueva();
        const luces = [];
        const A_PL = clamp(p.a_planta, 0, 1), SIN = clamp(p.sin_drenaje, 0, 1), VC = p.corte, DES = p.desagues || [];

        // ================= el lago, la playa en rampa y la tierra
        losa(agua, 0, LU, -LV, LV, 10, 10, () => HA, (u, v) => {
          const f = clamp(u / 120, 0, 1), n = ruido(u, v, 60, 3);
          return cAguaB.clone().lerp(cAgua, clamp(f * 2.4, 0, 1)).lerp(cAguaH, clamp(f - 0.35, 0, 1)).multiplyScalar(0.95 + 0.08 * n);
        });
        losa(suelo, U_PLAYA, 0, -LV, LV, 3, 6, (u) => piso(u), (u, v) => cArena.clone().lerp(cArenaM, clamp((u + 4) / 4, 0, 1)).multiplyScalar(0.92 + 0.1 * ruido(u, v, 7, 5)));
        losa(suelo, U_TIERRA, U_PLAYA, -LV, LV, 6, 6, () => HL, (u, v) => cPasto.clone().lerp(cPasto2, ruido(u, v, 30, 7)).multiplyScalar(0.92 + 0.12 * ruido(u, v, 7, 8)));
        // el faldón de tierra en los bordes (la maqueta sobre el suelo del mundo)
        const cFaldon = lin(COL.tierra_media).lerp(tonos.arena, 0.3).multiplyScalar(0.7);
        quad(solido, [[U_TIERRA, -LV, 0], [U_TIERRA, LV, 0], [U_TIERRA, LV, HL], [U_TIERRA, -LV, HL]], cFaldon, haciaU(-1));
        for (const s of [-1, 1]) quad(solido, [[U_TIERRA, s * LV, 0], [U_PLAYA, s * LV, 0], [U_PLAYA, s * LV, HL], [U_TIERRA, s * LV, HL]], cFaldon, haciaV(s));
        // piedras sueltas en la orilla
        for (let i = 0; i < 70; i++) {
          const v = -LV * 0.9 + LV * 1.8 * hz(i, 11), u = -3 + 3.5 * hz(i, 12), rr = 0.25 + 0.45 * hz(i, 14);
          if (DES.some((g) => Math.abs(v - g) < 3) || Math.abs(v - SAL_V) < 3) continue;
          gema(solido, E(u, v, piso(u) + 0.06), rr * M, rr * 0.55 * M, rr * 0.8 * M, hz(i, 15) * TAU, cArenaM.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.8 + 0.3 * hz(i, 16)));
        }

        // ================= la calle (con cunetas) y las tapas de pozo del colector
        losa(suelo, U_CALLE - AC, U_CALLE + AC, -LV, LV, AC, 8, () => HL + 0.05, (u, v) => cCalle.clone().multiplyScalar(0.92 + 0.1 * ruido(u, v, 6, 9)));
        for (const s of [-1, 1]) losa(suelo, U_CALLE + s * AC - (s < 0 ? 0.5 : 0), U_CALLE + s * AC + (s > 0 ? 0.5 : 0), -LV, LV, 0.5, 10, () => HL + 0.03, () => cCuneta);

        // ================= las casas: dos filas a los lados de la calle; el frente mira a la calle
        const casas = [];
        for (let f = 0; f < 2; f++) for (let j = 0; j < NH; j++) casas.push({ f, j, uc: FILAS[f], v: HV0 + HPASO * j, s: f === 0 ? -1 : 1 });
        // cuáles no tienen conexión: las primeras por un orden fijo (round(sin_drenaje · N))
        const orden = casas.map((c, i) => [hz(i, 40), i]).sort((a, b) => a[0] - b[0]);
        const nSin = Math.round(SIN * casas.length);
        orden.forEach(([, i], k) => { casas[i].sin = k < nSin; });
        casas.forEach((C, i) => {
          const { uc, v, s } = C, w = 7 + 2 * hz(i, 41), d = 6 + 1.6 * hz(i, 42), dos = hz(i, 43) < 0.25, h = dos ? 5.6 : 2.7 + 0.5 * hz(i, 44);
          const cm = cMuros[Math.floor(hz(i, 45) * cMuros.length)].clone().multiplyScalar(0.94 + 0.1 * hz(i, 46));
          const uf = uc + s * d / 2, ut = uc - s * d / 2;     // la fachada (hacia la calle) y la pared de atrás
          C.w = w; C.d = d; C.uf = uf;
          // el patio: tierra apisonada; el muro bajo de la calle con su portón
          losa(suelo, uc - 6.5, uc + 6.5, v - 6.6, v + 6.6, 13, 13, () => HL + 0.02, (uu, vv) => cPatio.clone().multiplyScalar(0.9 + 0.12 * ruido(uu, vv, 4, 47 + i)));
          const um = uc + s * 6.4;
          cw(solido, Math.min(um, um - s * 0.2), Math.max(um, um - s * 0.2), v - 6.6, v - 1.4, HL, HL + 1.1, cm.clone().multiplyScalar(0.92), { tope: cZocalo });
          cw(solido, Math.min(um, um - s * 0.2), Math.max(um, um - s * 0.2), v + 1.4, v + 6.6, HL, HL + 1.1, cm.clone().multiplyScalar(0.92), { tope: cZocalo });
          for (const e of [-1, 1]) cw(solido, Math.min(um, um - s * 0.25) - 0.05, Math.max(um, um - s * 0.25) + 0.05, v + e * 1.4 - 0.2, v + e * 1.4 + 0.2, HL, HL + 1.5, cZocalo);
          // el cuerpo con su zócalo
          cw(solido, Math.min(uf, ut), Math.max(uf, ut), v - w / 2, v + w / 2, HL, HL + h, cm, { sinTope: dos ? false : true, tope: cLosaT });
          cw(solido, Math.min(uf, ut) - 0.04, Math.max(uf, ut) + 0.04, v - w / 2 - 0.04, v + w / 2 + 0.04, HL, HL + 0.45, cZocalo, { sinTope: true });
          if (dos) {
            cw(solido, Math.min(uf, ut) - 0.15, Math.max(uf, ut) + 0.15, v - w / 2 - 0.15, v + w / 2 + 0.15, HL + h, HL + h + 0.15, cLosaT);          // la losa
            cw(solido, Math.min(uf, ut) - 0.15, Math.max(uf, ut) + 0.15, v - w / 2 - 0.15, v + w / 2 + 0.15, HL + 2.8, HL + 2.95, cLosaT);         // el entrepiso
            cilU(techos, ut + s * 1.2, v + w / 2 - 1.2, HL + h + 0.15, HL + h + 1.3, 0.55, 14, cHueco.clone().lerp(tonos.secundario, 0.3), cHueco);  // el tinaco
            for (let k = 0; k < 6; k++) cw(solido, uf - s * 0.02 - 0.03, uf - s * 0.02 + 0.03, v - w / 2 + k * w / 5 - 0.03, v - w / 2 + k * w / 5 + 0.03, HL + h + 0.15, HL + h + 1.0, cMetal);  // varillas
          } else {
            // el techo de dos aguas (cumbrera a lo largo de v), con alero
            const al = 0.45, hc = HL + h + 1.3 + 0.3 * hz(i, 48), u0 = Math.min(uf, ut) - al, u1 = Math.max(uf, ut) + al, um2 = (u0 + u1) / 2, he = HL + h - 0.12;
            const tj = (hz(i, 49) < 0.5 ? cTeja : cTeja2).clone().multiplyScalar(0.94 + 0.1 * hz(i, 50));
            quad(techos, [[u0, v - w / 2 - al, he], [um2, v - w / 2 - al, hc], [um2, v + w / 2 + al, hc], [u0, v + w / 2 + al, he]], tj, haciaU(-1).map((x, k) => k === 1 ? 0.8 : x));
            quad(techos, [[u1, v - w / 2 - al, he], [um2, v - w / 2 - al, hc], [um2, v + w / 2 + al, hc], [u1, v + w / 2 + al, he]], tj.clone().multiplyScalar(0.92), haciaU(1).map((x, k) => k === 1 ? 0.8 : x));
            // las tejas: canales a lo largo de la pendiente
            for (let vv = v - w / 2 - al + 0.35; vv < v + w / 2 + al; vv += 0.7) for (const [ua, ub] of [[u0, um2], [u1, um2]])
              quad(techos, [[ua, vv - 0.04, he + 0.03], [ub, vv - 0.04, hc + 0.03], [ub, vv + 0.04, hc + 0.03], [ua, vv + 0.04, he + 0.03]], tj.clone().multiplyScalar(0.72), [0, 1, 0]);
            for (const e of [-1, 1]) quad(solido, [[Math.min(uf, ut), v + e * w / 2, HL + h], [Math.max(uf, ut), v + e * w / 2, HL + h], [um2, v + e * w / 2, hc - 0.1], [um2, v + e * w / 2, hc - 0.1]], cm, haciaV(e));
            cw(techos, um2 - 0.12, um2 + 0.12, v - w / 2 - al, v + w / 2 + al, hc - 0.02, hc + 0.12, tj.clone().multiplyScalar(0.8));
          }
          // la puerta y las ventanas de la fachada (y una a cada lado); de noche, la mayoría encendidas
          const fu = uf + s * 0.03, pv = v + (hz(i, 51) - 0.5) * (w - 3);
          quad(solido, [[fu, pv - 0.5, HL + 0.05], [fu, pv + 0.5, HL + 0.05], [fu, pv + 0.5, HL + 2.1], [fu, pv - 0.5, HL + 2.1]], cPuerta, haciaU(s));
          const pisos = dos ? [HL + 1.0, HL + 3.8] : [HL + 1.0];
          pisos.forEach((h0, kp) => {
            for (const vv of [v - w / 2 + 1.3, v + w / 2 - 1.3]) {
              if (kp === 0 && Math.abs(vv - pv) < 1.2) continue;
              const enc = noche && hz(i * 7 + kp * 3 + (vv > v ? 1 : 0), 52) < 0.75;
              cw(solido, Math.min(fu, fu + s * 0.08), Math.max(fu, fu + s * 0.08), vv - 0.7, vv + 0.7, h0 - 0.08, h0 + 1.22, cZocalo);   // el marco
              quad(enc ? vid : solido, [[fu + s * 0.1, vv - 0.6, h0], [fu + s * 0.1, vv + 0.6, h0], [fu + s * 0.1, vv + 0.6, h0 + 1.1], [fu + s * 0.1, vv - 0.6, h0 + 1.1]], enc ? cVidrio : cVidrioA, haciaU(s));
              quad(solido, [[fu + s * 0.12, vv - 0.03, h0], [fu + s * 0.12, vv + 0.03, h0], [fu + s * 0.12, vv + 0.03, h0 + 1.1], [fu + s * 0.12, vv - 0.03, h0 + 1.1]], cMetal, haciaU(s));   // la reja
            }
          });
          for (const e of [-1, 1]) {
            const enc = noche && hz(i * 5 + e + 2, 53) < 0.6;
            quad(enc ? vid : solido, [[uc - 0.6, v + e * (w / 2 + 0.03), HL + 1.0], [uc + 0.6, v + e * (w / 2 + 0.03), HL + 1.0], [uc + 0.6, v + e * (w / 2 + 0.03), HL + 2.0], [uc - 0.6, v + e * (w / 2 + 0.03), HL + 2.0]], enc ? cVidrio : cVidrioA, haciaV(e));
          }
          // sin conexión: la fosa en el patio de atrás (tapa de concreto y su respiradero), sin tubo
          if (C.sin) {
            const uz = ut - s * 2.6, vz = v + (hz(i, 54) - 0.5) * 3;
            cw(solido, uz - 0.7, uz + 0.7, vz - 0.7, vz + 0.7, HL, HL + 0.14, cConcreto, { tope: cConcretoO });
            twu(solido, uz + 0.5, vz + 0.5, HL + 0.14, uz + 0.5, vz + 0.5, HL + 1.1, 0.05, 8, cTubo, cHueco);
            C.fosa = [uz, vz];
          }
          // un árbol en algunos patios de atrás
          if (hz(i, 55) < 0.55) {
            const ua = ut - s * (3.6 + hz(i, 56)), va = v + (hz(i, 57) - 0.5) * 8, ht = 2.4 + 1.6 * hz(i, 58), rc = 1.8 + 1.2 * hz(i, 59);
            twu(plantas, ua, va, HL, ua, va, HL + ht, 0.18, 8, cTronco, null);
            gema(plantas, E(ua, va, HL + ht + rc * 0.5), rc * M, rc * 0.8 * M, rc * M, hz(i, 60) * TAU, (hz(i, 61) < 0.5 ? cHoja : cHoja2).clone().multiplyScalar(0.9 + 0.2 * hz(i, 62)), true);
          }
        });
        // árboles sueltos detrás del pueblo y entre la planta y el pueblo
        for (let i = 0; i < 26; i++) {
          const u = i < 18 ? -100 - 45 * hz(i, 63) : -20 - 25 * hz(i, 64), v = i < 18 ? -140 + 280 * hz(i, 65) : 47.2 + 2.2 * hz(i, 66);
          const ht = 3 + 3 * hz(i, 67), rc = 2.2 + 1.6 * hz(i, 68);
          twu(plantas, u, v, HL, u, v, HL + ht, 0.22, 8, cTronco, null);
          gema(plantas, E(u, v, HL + ht + rc * 0.5), rc * M, rc * 0.85 * M, rc * M, hz(i, 69) * TAU, (hz(i, 70) < 0.5 ? cHoja : cHoja2).clone().multiplyScalar(0.85 + 0.25 * hz(i, 71)), true);
        }
        // los faroles de la calle
        for (let v = -135; v <= 135; v += 30) {
          const uf = U_CALLE + AC + 0.7;
          twu(solido, uf, v, HL, uf, v, HL + 6, 0.08, 10, cMetal, cHueco);
          twu(solido, uf, v, HL + 6, uf - 1.2, v, HL + 6.1, 0.05, 6, cMetal, null);
          cw(solido, uf - 1.45, uf - 1.0, v - 0.2, v + 0.2, HL + 5.85, HL + 6.1, cHueco);
          luces.push([uf - 1.2, v, HL + 5.8, 0.85]);
        }

        // ================= EL DRENAJE: los tubos (a flor de tierra), con sus uniones, y el agua que corre por ellos (pulsos)
        // camino: [[u, v, h], …] (h = el eje del tubo); rr = radio (m; 0 = un hilo de agua sobre el suelo); tipo: crudo · clara
        const DASH = [];       // {i0 (vértice), s, tipo, vel}
        const dash = nueva();
        const camino = (pts, rr, tipo, vel = 1.2, s0 = 0) => {
          let s = s0;
          for (let k = 0; k + 1 < pts.length; k++) {
            const [ua, va, ha] = pts[k], [ub, vb, hb] = pts[k + 1], L = Math.hypot(ub - ua, vb - va, hb - ha);
            if (rr > 0) {
              twu(dren, ua, va, ha, ub, vb, hb, rr, 12, cTubo, null);
              if (k > 0) twu(dren, ua - (ub - ua) / L * 0.12, va - (vb - va) / L * 0.12, ha, ua + (ub - ua) / L * 0.12, va + (vb - va) / L * 0.12, ha, rr * 1.18, 12, cTuboO, cTuboO);
            }
            const du = (ub - ua) / (L || 1), dv = (vb - va) / (L || 1), wn = rr > 0 ? rr * 0.75 : 0.45, n = Math.max(1, Math.floor(L / 1.1));
            for (let q = 0; q < n; q++) {
              const f0 = (q + 0.1) / n, f1 = (q + 0.9) / n, z = rr > 0 ? rr + 0.03 : 0.025;
              const P = (f) => [ua + (ub - ua) * f, va + (vb - va) * f, ha + (hb - ha) * f + z];
              const A = P(f0), B = P(f1), i0 = dash.pos.length / 3;
              for (const [a, e] of [[A, -1], [B, -1], [B, 1], [A, 1]]) { const Q = E(a[0] - dv * e * wn, a[1] + du * e * wn, a[2]); dash.pos.push(Q[0], Q[1], Q[2]); dash.col.push(0, 0, 0); }
              dash.idx.push(i0, i0 + 1, i0 + 2, i0, i0 + 2, i0 + 3);
              DASH.push({ i0, s: s + L * (q + 0.5) / n, tipo, vel, sup: rr > 0 });
            }
            s += L;
          }
          return s;
        };
        const ejeH = (u, rr) => piso(u) + rr * 0.45;
        const R_LAT = 0.3, R_COL = 0.5, R_BAJ = 0.6;
        // las acometidas: de la fachada a la calle, con su caja de registro en la banqueta
        casas.forEach((C, i) => {
          if (C.sin) return;
          const tipo = C.v >= VC ? "planta" : "crudo", vv = C.v + 1.6, ue = U_CALLE + C.s * -0.5;
          const ub = C.s < 0 ? U_CALLE + AC + 0.9 : U_CALLE - AC - 0.9;
          cw(solido, ub - 0.4, ub + 0.4, vv - 0.4, vv + 0.4, HL, HL + 0.32, cConcreto, { tope: cConcretoO });
          camino([[C.uf, vv, ejeH(C.uf, R_LAT)], [ub, vv, ejeH(ub, R_LAT)], [ue, vv, ejeH(ue, R_LAT)]], R_LAT, tipo, 0.9, hz(i, 72) * 10);
        });
        // los colectores por la calle: el crudo (a los desagües) y el de la planta (al canal de rejas)
        const vDir = casas.filter((c) => !c.sin && c.v < VC).map((c) => c.v + 1.6), vPla = casas.filter((c) => !c.sin && c.v >= VC).map((c) => c.v + 1.6);
        const tapas = [];
        if (DES.length) {
          const v0 = Math.min(DES[0], ...vDir) - 1, v1 = Math.max(DES[DES.length - 1], ...vDir) + 0.6;
          camino([[U_CALLE, v1, ejeH(U_CALLE, R_COL)], [U_CALLE, v0, ejeH(U_CALLE, R_COL)]], R_COL, "crudo", 1.1);
          for (let v = v0 + 6; v < v1; v += 20) tapas.push(v);
          twu(dren, U_CALLE, v0, ejeH(U_CALLE, R_COL), U_CALLE, v0 - 0.05, ejeH(U_CALLE, R_COL), R_COL * 1.05, 12, cTuboO, cTuboO);   // el tapón
        }
        if (vPla.length && A_PL > 0) {
          const v0 = Math.min(...vPla) - 0.6, hp = ejeH(U_CALLE, R_COL);
          camino([[U_CALLE, v0, hp], [U_CALLE, 74, hp], [-50.2, 74, ejeH(-50, R_COL)]], R_COL, "planta", 1.1);
          for (let v = v0 + 6; v < 74; v += 20) tapas.push(v);
          twu(dren, U_CALLE, v0, hp, U_CALLE, v0 - 0.05, hp, R_COL * 1.05, 12, cTuboO, cTuboO);
        }
        tapas.forEach((v) => { disco(marcas, U_CALLE + 1.4, v, HL + 0.07, 0.45, 14, cHueco); disco(marcas, U_CALLE + 1.4, v, HL + 0.075, 0.32, 14, cMetal); });
        // las bajadas de los desagües crudos: de la calle, entre las casas del frente, a la playa
        const bocas = [];
        const bajada = (v, tipo, uIni, hIni) => {
          const pts = [[uIni, v, hIni]];
          for (const u of [-30, -16, U_PLAYA, -7]) if (u > uIni + 0.5) pts.push([u, v, ejeH(u, R_BAJ)]);
          const hb = piso(U_BOCA) + R_BAJ + 0.12;
          pts.push([U_BOCA, v, hb]);
          const s = camino(pts, R_BAJ, tipo, 1.3);
          // el cabezal de concreto que sostiene la boca y la boca oscura
          cw(solido, U_BOCA - 0.9, U_BOCA - 0.3, v - 1.5, v + 1.5, piso(U_BOCA) - 0.1, hb + R_BAJ + 0.25, cConcreto, { tope: cConcretoO });
          quad(solido, [[U_BOCA + 0.01, v - R_BAJ * 0.8, hb - R_BAJ * 0.8], [U_BOCA + 0.01, v + R_BAJ * 0.8, hb - R_BAJ * 0.8], [U_BOCA + 0.01, v + R_BAJ * 0.8, hb + R_BAJ * 0.8], [U_BOCA + 0.01, v - R_BAJ * 0.8, hb + R_BAJ * 0.8]], cHueco, haciaU(1));
          // el hilo de agua por la arena: la arena mojada y el agua que corre al lago
          losa(marcas, U_BOCA - 0.2, 1.2, v - 1.0, v + 1.0, 0.6, 0.5, (u) => piso(u) + 0.02, (u, vv) => (tipo === "clara" ? cArenaM : cMojado).clone().multiplyScalar(0.9 + 0.15 * ruido(u, vv, 1.2, 73)));
          camino([[U_BOCA - 0.2, v, piso(U_BOCA) + 0.03], [1.0, v, HA + 0.02]], 0, tipo, 1.6, s);
          bocas.push({ u: U_BOCA, v, h: hb, tipo });
        };
        DES.forEach((g) => bajada(g, "crudo", U_CALLE, ejeH(U_CALLE, R_COL)));
        // tubos que unen el colector crudo con cada bajada (ya empiezan en la calle) y la salida de la planta
        bajada(SAL_V, "clara", PL.u1 - 3.5, ejeH(PL.u1, R_BAJ));

        // ================= LA PLANTA DE TRATAMIENTO (genérica): cerca, canal de rejas, tanque, sedimentadores, lechos, edificio
        const planta = nueva();
        losa(suelo, PL.u0, PL.u1, PL.v0, PL.v1, 4, 4, () => HL + 0.03, (u, v) => cPatio.clone().lerp(cConcreto, 0.3).multiplyScalar(0.9 + 0.1 * ruido(u, v, 5, 74)));
        // la cerca: postes cada 3 m y tres hilos; el portón hacia la calle
        { const lados = [[PL.u0, PL.v0, PL.u1, PL.v0], [PL.u1, PL.v0, PL.u1, PL.v1], [PL.u1, PL.v1, PL.u0, PL.v1], [PL.u0, PL.v1, PL.u0, PL.v0]];
          lados.forEach(([ua, va, ub, vb], k) => {
            const L = Math.hypot(ub - ua, vb - va), n = Math.round(L / 3);
            for (let q = 0; q <= n; q++) { const u = ua + (ub - ua) * q / n, v = va + (vb - va) * q / n;
              if (k === 3 && v > 84 && v < 92) continue;
              cw(planta, u - 0.06, u + 0.06, v - 0.06, v + 0.06, HL, HL + 2.0, cMetal); }
            for (const h of [0.5, 1.2, 1.9]) {
              if (k === 3) { twu(planta, ua, va, HL + h, ua, 92, HL + h, 0.02, 4, cMetal, null); twu(planta, ua, 84, HL + h, ub, vb, HL + h, 0.02, 4, cMetal, null); }
              else twu(planta, ua, va, HL + h, ub, vb, HL + h, 0.02, 4, cMetal, null);
            }
          });
          // el portón abierto y el camino de entrada desde la calle
          cw(planta, PL.u0 - 0.06, PL.u0 + 0.06, 84, 84.15, HL, HL + 2.2, cMetal); cw(planta, PL.u0 - 0.06, PL.u0 + 0.06, 91.85, 92, HL, HL + 2.2, cMetal);
          losa(suelo, U_CALLE + AC, PL.u0, 84.5, 91.5, 2, 3.5, () => HL + 0.04, (u, v) => cCalle.clone().multiplyScalar(0.95 + 0.08 * ruido(u, v, 3, 75)));
        }
        // el canal de rejas: paredes, agua turbia y la reja de barras
        { const u0 = -50, u1 = -40, v0 = 72, v1 = 76, hw = HL + 1.0;
          for (const [a0, a1, b0, b1] of [[u0, u1, v0 - 0.25, v0], [u0, u1, v1, v1 + 0.25], [u0 - 0.25, u0, v0 - 0.25, v1 + 0.25]]) cw(planta, a0, a1, b0, b1, HL, hw, cConcreto, { tope: cConcretoO });
          losa(agua, u0, u1, v0, v1, 2, 2, () => hw - 0.25, () => cTurbio);
          for (let v = v0 + 0.3; v < v1; v += 0.35) twu(planta, -45, v, hw - 0.6, -44.4, v, hw + 0.25, 0.03, 4, cMetal, null);
          cw(planta, -45.4, -44.2, v0 - 0.3, v1 + 0.3, hw + 0.25, hw + 0.35, cBaranda);
        }
        // el tanque rectangular (aireación): muros, agua, pasarela con baranda y las burbujas
        const TQ = { u0: -38, u1: -27, v0: 66, v1: 96 }, hT = HL + 2.2;
        { const e = 0.3;
          cw(planta, TQ.u0 - e, TQ.u1 + e, TQ.v0 - e, TQ.v0, HL, hT, cConcreto, { tope: cConcretoO }); cw(planta, TQ.u0 - e, TQ.u1 + e, TQ.v1, TQ.v1 + e, HL, hT, cConcreto, { tope: cConcretoO });
          cw(planta, TQ.u0 - e, TQ.u0, TQ.v0, TQ.v1, HL, hT, cConcreto, { tope: cConcretoO }); cw(planta, TQ.u1, TQ.u1 + e, TQ.v0, TQ.v1, HL, hT, cConcreto, { tope: cConcretoO });
          losa(agua, TQ.u0, TQ.u1, TQ.v0, TQ.v1, 1, 2, () => hT - 0.3, (u, v) => cTurbio.clone().lerp(cClara, 0.25).multiplyScalar(0.9 + 0.12 * ruido(u, v, 2.5, 76)));
          // la pasarela a lo largo del tanque, con sus barandas
          const um = (TQ.u0 + TQ.u1) / 2;
          cw(planta, um - 0.6, um + 0.6, TQ.v0 - 0.3, TQ.v1 + 0.3, hT + 0.05, hT + 0.18, cMetal);
          for (const sg of [-1, 1]) { twu(planta, um + sg * 0.6, TQ.v0, hT + 1.1, um + sg * 0.6, TQ.v1, hT + 1.1, 0.04, 6, cBaranda, null);
            for (let v = TQ.v0; v <= TQ.v1; v += 2.5) twu(planta, um + sg * 0.6, v, hT + 0.18, um + sg * 0.6, v, hT + 1.1, 0.03, 4, cBaranda, null); }
          // los tubos del canal al tanque y del tanque a cada sedimentador
          twu(planta, -40, 74, HL + 0.75, TQ.u0 - 0.3, 74, HL + 0.75, 0.25, 12, cTubo, null);
          for (const [cu, cv] of CLAR) twu(planta, TQ.u1 + 0.3, cv, HL + 1.4, cu - RCL, cv, HL + 1.4, 0.25, 12, cTubo, null);
        }
        const burb = [];      // [u, v, fase, periodo]
        for (let i = 0; i < 90; i++) burb.push([TQ.u0 + 0.6 + (TQ.u1 - TQ.u0 - 1.2) * hz(i, 77), TQ.v0 + 0.6 + (TQ.v1 - TQ.v0 - 1.2) * hz(i, 78), hz(i, 79), 1.2 + 1.4 * hz(i, 80)]);
        // los sedimentadores: muro redondo, agua, vertedero y la columna del centro; el puente gira (malla aparte)
        const puentes = [];
        CLAR.forEach(([cu, cv], k) => {
          const hc = HL + 2.0;
          cilU(planta, cu, cv, HL, hc, RCL + 0.3, 28, cConcreto, null);
          cilU(planta, cu, cv, hc - 0.6, hc, RCL, 28, cConcretoO, null);
          { const n = 28; for (let i = 0; i < n; i++) { const a0 = TAU * i / n, a1 = TAU * (i + 1) / n;
            quad(planta, [[cu + RCL * Math.cos(a0), cv + RCL * Math.sin(a0), hc], [cu + (RCL + 0.3) * Math.cos(a0), cv + (RCL + 0.3) * Math.sin(a0), hc], [cu + (RCL + 0.3) * Math.cos(a1), cv + (RCL + 0.3) * Math.sin(a1), hc], [cu + RCL * Math.cos(a1), cv + RCL * Math.sin(a1), hc]], cConcretoO); } }
          // el agua: más clara hacia el borde (lo que se asienta queda abajo)
          { const n = 28;
            for (let i = 0; i < n; i++) { const a0 = TAU * i / n, a1 = TAU * (i + 1) / n;
              for (let rg = 0; rg < 3; rg++) { const r0 = RCL * rg / 3, r1 = RCL * (rg + 1) / 3, c = cTurbio.clone().lerp(cClara, 0.3 + 0.25 * rg);
                quad(agua, [[cu + r0 * Math.cos(a0), cv + r0 * Math.sin(a0), hc - 0.25], [cu + r1 * Math.cos(a0), cv + r1 * Math.sin(a0), hc - 0.25], [cu + r1 * Math.cos(a1), cv + r1 * Math.sin(a1), hc - 0.25], [cu + r0 * Math.cos(a1), cv + r0 * Math.sin(a1), hc - 0.25]], c); } }
          }
          // la canaleta del vertedero (un anillo de lámina por dentro del muro)
          cilU(planta, cu, cv, hc - 0.45, hc - 0.1, RCL - 0.35, 28, cMetal, null);
          cilU(planta, cu, cv, hc - 0.4, hc + 0.9, 0.45, 14, cConcreto, cConcretoO);
          // el puente que gira: en ejes locales (x a lo largo del radio), con su baranda y el motor del centro
          const a = nueva();
          bx(a, (x, y, z) => [x, y, z], 0, RCL + 0.35, 0, 0.18, -0.45, 0.45, cMetal);
          for (const sg of [-1, 1]) { tubo(a, [0, 0.18, sg * 0.45], [RCL + 0.35, 0.18, sg * 0.45], 0.03, 4, cBaranda, null); tubo(a, [0, 1.0, sg * 0.45], [RCL + 0.35, 1.0, sg * 0.45], 0.035, 6, cBaranda, null);
            for (let x = 0.4; x < RCL + 0.4; x += 1.4) tubo(a, [x, 0.18, sg * 0.45], [x, 1.0, sg * 0.45], 0.03, 4, cBaranda, null); }
          bx(a, (x, y, z) => [x, y, z], -0.55, 0.55, 0.18, 0.85, -0.55, 0.55, tonos.secundario.clone().lerp(cMetal, 0.4));
          tubo(a, [RCL - 0.2, 0.0, 0], [RCL - 0.2, -1.6, 0], 0.06, 6, cMetal, null);     // la rastra que baja al agua
          bx(a, (x, y, z) => [x, y, z], 0.4, RCL - 0.2, -1.65, -1.55, -0.05, 0.05, cMetal);
          const g = malla.geometria(a); g.scale(M, M, M);
          const m = new THREE.Mesh(g, malla.material({})); m.frustumCulled = false; m.renderOrder = 4; scene.add(m); mats.push(m.material);
          const P = E(cu, cv, hc + 0.9); m.position.set(P[0], P[1], P[2]);
          puentes.push({ m, per: 46 + 8 * k, ph: hz(k, 81) });
          // la salida del sedimentador al tubo del efluente
          twu(planta, cu + RCL + 0.3, cv, HL + 0.9, PL.u1 - 3.5, cv, HL + 0.9, 0.25, 12, cTubo, null);
        });
        twu(planta, PL.u1 - 3.5, CLAR[0][1], HL + 0.9, PL.u1 - 3.5, CLAR[1][1], HL + 0.9, 0.3, 12, cTubo, null);
        twu(planta, PL.u1 - 3.5, SAL_V, HL + 0.9, PL.u1 - 3.5, SAL_V, ejeH(PL.u1, R_BAJ), 0.3, 12, cTubo, null);
        // los lechos de secado: tres celdas con lodo agrietado
        { const u0 = -52, u1 = -42;
          for (let k = 0; k < 3; k++) { const v0 = 54 + k * 4.6, v1 = v0 + 4.2;
            losa(planta, u0, u1, v0, v1, 0.8, 0.7, () => HL + 0.25, (u, v) => cLodo.clone().multiplyScalar(ruido(u, v, 0.6, 82 + k) < 0.25 ? 0.6 : 0.95 + 0.1 * ruido(u, v, 2, 85)));
            for (const [a0, a1, b0, b1] of [[u0 - 0.2, u1 + 0.2, v0 - 0.2, v0], [u0 - 0.2, u1 + 0.2, v1, v1 + 0.2]]) cw(planta, a0, a1, b0, b1, HL, HL + 0.5, cConcreto, { tope: cConcretoO });
          }
          cw(planta, u0 - 0.2, u0, 53.8, 67.8, HL, HL + 0.5, cConcreto, { tope: cConcretoO }); cw(planta, u1, u1 + 0.2, 53.8, 67.8, HL, HL + 0.5, cConcreto, { tope: cConcretoO });
        }
        // el edificio bajo (control): losa con pretil, puerta, ventanas, una unidad en el techo y la lámpara de la puerta
        { const u0 = -52, u1 = -44, v0 = 98, v1 = 110, hb = HL + 3.4;
          cw(planta, u0, u1, v0, v1, HL, hb, cMuros[2].clone().lerp(cConcreto, 0.4), { tope: cLosaT });
          cw(planta, u0 - 0.05, u1 + 0.05, v0 - 0.05, v1 + 0.05, HL, HL + 0.5, cZocalo, { sinTope: true });
          for (const [a0, a1, b0, b1] of [[u0, u1, v0, v0 + 0.2], [u0, u1, v1 - 0.2, v1], [u0, u0 + 0.2, v0, v1], [u1 - 0.2, u1, v0, v1]]) cw(planta, a0, a1, b0, b1, hb, hb + 0.45, cConcreto, { tope: cConcretoO });
          cw(planta, -49.5, -47.5, 102, 104.5, hb, hb + 0.9, cMetal);
          quad(solido, [[u0 - 0.03, 103.4, HL + 0.05], [u0 - 0.03, 104.6, HL + 0.05], [u0 - 0.03, 104.6, HL + 2.2], [u0 - 0.03, 103.4, HL + 2.2]], cPuerta, haciaU(-1));
          for (const vv of [100, 107.5]) quad(noche ? vid : solido, [[u0 - 0.03, vv - 0.9, HL + 1.1], [u0 - 0.03, vv + 0.9, HL + 1.1], [u0 - 0.03, vv + 0.9, HL + 2.3], [u0 - 0.03, vv - 0.9, HL + 2.3]], noche ? cVidrio : cVidrioA, haciaU(-1));
          for (const uu of [-50, -46]) quad(noche ? vid : solido, [[uu - 0.9, v0 - 0.03, HL + 1.1], [uu + 0.9, v0 - 0.03, HL + 1.1], [uu + 0.9, v0 - 0.03, HL + 2.3], [uu - 0.9, v0 - 0.03, HL + 2.3]], noche ? cVidrio : cVidrioA, haciaV(-1));
          luces.push([u0 - 0.4, 104, HL + 2.6, 0.6]);
        }
        // las lámparas de la planta
        for (const [u, v] of [[-41, 64], [-13, 60], [-41, 97], [-14, 108]]) { twu(planta, u, v, HL, u, v, HL + 5, 0.07, 10, cMetal, cHueco); luces.push([u, v, HL + 5.1, 0.8]); }

        // ================= las mallas fijas
        poner(agua, { desfase: 1 }, 1);
        poner(suelo, { desfase: 2 }, 2);
        poner(marcas, { desfase: 3 }, 3);
        poner(solido, { desfase: 1 }, 3);
        poner(techos, {}, 3);
        poner(plantas, {}, 3);
        poner(planta, {}, 3);
        poner(dren, {}, 4, mDren);
        const mVid = poner(vid, { desfase: 3 }, 4, []);
        // el agua que corre: los guiones encima de los tubos (sus colores se calculan con t)
        const gDash = malla.geometria(dash), matDash = malla.material({ desfase: 4 });
        const mDash = new THREE.Mesh(gDash, matDash); mDash.frustumCulled = false; mDash.renderOrder = 5; scene.add(mDash); mDren.push(matDash);
        const colDash = gDash.attributes.color.array;
        const lTop = sombra(0, 1, 0), cFondoTubo = cTubo.clone().multiplyScalar(lTop), cFondoSup = cMojado.clone().multiplyScalar(lTop);
        const cFlujo = { crudo: cTurbio.clone().multiplyScalar(lTop * (oscuro ? 1.2 : 1)), planta: cTurbio.clone().multiplyScalar(lTop * (oscuro ? 1.2 : 1)), clara: cClara.clone().multiplyScalar(lTop * 1.05) };

        // ================= la mancha turbia frente a cada desagüe crudo (respira) y los anillos que salen de la boca
        const manchas = [], anillos = [];
        DES.forEach((g, k) => {
          const R = 15 + 4 * hz(k, 90), cu = R * 0.55 + 1.5, cv = g + 3 * (hz(k, 91) - 0.5), a = nueva(), n = 40, NR = 6;
          const borde = (th) => R * (0.78 + 0.3 * ruido(Math.cos(th) * 3 + k * 7, Math.sin(th) * 3, 1.3, 92)) * (Math.cos(th) < 0 ? 0.5 + 0.5 * (1 + Math.cos(th)) : 1);
          const C = E(cu, cv, HA + 0.012);
          for (let rg = 0; rg < NR; rg++) for (let i = 0; i < n; i++) {
            const a0 = TAU * i / n, a1 = TAU * (i + 1) / n, f0 = rg / NR, f1 = (rg + 1) / NR;
            const ca = cTurbio.clone().lerp(cAguaB, Math.pow(f0, 1.6)), cb = cTurbio.clone().lerp(cAguaB, Math.pow(f1, 1.6));
            const P = (f, th) => E(cu + f * borde(th) * Math.cos(th) * 0.8, cv + f * borde(th) * Math.sin(th) * 1.25, HA + 0.012), q = a.pos.length / 3, l = sombra(0, 1, 0);
            for (const [Q, c] of [[P(f0, a0), ca], [P(f1, a0), cb], [P(f1, a1), cb], [P(f0, a1), ca]]) { a.pos.push(Q[0], Q[1], Q[2]); a.col.push(c.r * l, c.g * l, c.b * l); }
            a.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
          const m = new THREE.Mesh(geoLocal(a, C), malla.material({ desfase: 2 })); m.frustumCulled = false; m.renderOrder = 2; scene.add(m); mDren.push(m.material);
          m.position.set(C[0], C[1], C[2]);
          manchas.push({ m, ph: hz(k, 93) * TAU });
          for (let j = 0; j < 2; j++) {
            const b = nueva(), nn = 28;
            for (let i = 0; i < nn; i++) { const a0 = TAU * i / nn, a1 = TAU * (i + 1) / nn; cara(b, [[0.86 * Math.cos(a0), 0, 0.86 * Math.sin(a0)], [Math.cos(a0), 0, Math.sin(a0)], [Math.cos(a1), 0, Math.sin(a1)], [0.86 * Math.cos(a1), 0, 0.86 * Math.sin(a1)]], cTurbio.clone().multiplyScalar(0.8), [0, 1, 0]); }
            const mm = new THREE.Mesh(malla.geometria(b), malla.material({ alfa: 0.6, desfase: 4 })); mm.frustumCulled = false; mm.renderOrder = 3; scene.add(mm);
            anillos.push({ m: mm, P: E(1.2, g, HA + 0.02), ph: j * 0.5 + hz(k, 94) });
          }
        });
        // ================= los chorros de las bocas: gotas que caen de la boca a la arena
        const gGota = (col) => { const a = nueva(); gema(a, [0, 0, 0], 0.11, 0.16, 0.11, 0, col, false); return malla.geometria(a); };
        const gotas = [], gT = gGota(cTurbio.clone().multiplyScalar(1.1)), gC = gGota(cClara);
        const matG = malla.material({}); mDren.push(matG);
        const plantaFluye = vPla.length > 0 && A_PL > 0;
        bocas.forEach((B, k) => {
          if (B.tipo === "clara" && !plantaFluye) return;
          for (let j = 0; j < 10; j++) { const m = new THREE.Mesh(B.tipo === "clara" ? gC : gT, matG); m.frustumCulled = false; m.renderOrder = 5; m.scale.setScalar(M); scene.add(m);
            gotas.push({ m, B, f0: j / 10 + 0.05 * hz(j + k * 13, 95), dv: (hz(j + k * 13, 96) - 0.5) * 0.5 }); }
        });

        // ================= los destellos del lago (titilan: función de t)
        const ND = 160, gD = new THREE.BufferGeometry(), posD = new Float32Array(ND * 4 * 3), colD = new Float32Array(ND * 4 * 3), idxD = [], DESL = [];
        for (let i = 0; i < ND; i++) {
          const u = 30 + (LU - 35) * Math.pow(hz(i, 150), 1.2), v = (hz(i, 151) - 0.5) * 2 * (LV - 5), L = 1.2 + 2.2 * hz(i, 152);
          const P = [E(u - 0.08, v - L / 2, HA + 0.02), E(u + 0.08, v - L / 2, HA + 0.02), E(u + 0.08, v + L / 2, HA + 0.02), E(u - 0.08, v + L / 2, HA + 0.02)];
          P.forEach((q, j) => posD.set(q, (i * 4 + j) * 3));
          idxD.push(i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3);
          DESL.push([TAU * hz(i, 153), 0.6 + 1.2 * hz(i, 154)]);
        }
        gD.setAttribute("position", new THREE.BufferAttribute(posD, 3)); gD.setAttribute("color", new THREE.BufferAttribute(colD, 3)); gD.setIndex(idxD);
        const mD = new THREE.Mesh(gD, malla.material({ aditivo: true, desfase: 3 })); mD.frustumCulled = false; mD.renderOrder = 5; scene.add(mD);
        // las burbujas del tanque (puntitos claros que suben y se apagan)
        const gB = (() => { const a = nueva(); gema(a, [0, 0, 0], 0.16, 0.08, 0.16, 0, cEspuma, false); return malla.geometria(a); })();
        const burbM = burb.map(() => { const m = new THREE.Mesh(gB, matG); m.frustumCulled = false; m.renderOrder = 5; m.scale.setScalar(M); scene.add(m); return m; });

        // ================= la gente: quien opera la planta, quien camina por la calle, quien mira el agua en la orilla
        const NP = clamp(p.personas | 0, 0, 4);
        const camisas = [tonos.secundario.clone(), tonos.mal.clone(), tonos.bien.clone(), lin(COL.costa).multiplyScalar(0.85), tonos.medio.clone()];
        const d0 = DES.length ? DES[0] : SAL_V;
        const GENTE = [["fijo", -25.2, 84, 1, 0, "de_pie"], ["calle", 0.15, 1.0, 1], ["fijo", -6, d0 - 7, 1, 0.3, "de_pie"], ["calle", 0.62, 0.9, -1]].slice(0, NP);
        const flP = NP ? ctx.flota("persona", NP, { tamano: K * 1.25, lev: 0, orden: 6, semilla: p.semilla % 991, color: (i) => camisas[(i + p.semilla) % camisas.length],
          pose: (i) => GENTE[i][0] === "calle" ? "caminar" : GENTE[i][5] }) : null;

        // ================= las luces de noche (faroles y lámparas): puntos que brillan, y sus charcos de luz
        const NL = luces.length, gP = new THREE.BufferGeometry(), posP = new Float32Array(NL * 3), aP = new Float32Array(NL * 2);
        luces.forEach(([u, v, h, a], j) => { posP.set(E(u, v, h), j * 3); aP[j * 2] = noche ? a : 0; aP[j * 2 + 1] = 2.2; });
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 2));
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: cLuz } },
          transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "attribute vec2 aK; uniform float uPx, uTam; varying vec2 vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " gl_PointSize = aK.x > 0.0 ? clamp(aK.y * uTam * uPx / max(1e-3, -mv.z), 2.0, 48.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA; varying vec2 vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = cA; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK.x * (exp(-r * r * 6.0) + 0.6 * exp(-r * r * 40.0)); gl_FragColor = vec4(s * a, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);
        if (noche) { const ch = nueva();
          luces.forEach(([u, v, h]) => { const q = ch.pos.length / 3, R = Math.min(8, h * 1.3), n = 18, c0 = cLuz.clone().multiplyScalar(0.13), hh = HL + 0.09;
            const C = E(u, v, hh); ch.pos.push(C[0], C[1], C[2]); ch.col.push(c0.r, c0.g, c0.b);
            for (let i = 0; i < n; i++) { const P = E(u + R * Math.cos(TAU * i / n), v + R * Math.sin(TAU * i / n), hh); ch.pos.push(P[0], P[1], P[2]); ch.col.push(0, 0, 0); }
            for (let i = 0; i < n; i++) ch.idx.push(q, q + 1 + i, q + 1 + ((i + 1) % n)); });
          const mC = new THREE.Mesh(malla.geometria(ch), malla.material({ aditivo: true, desfase: 5 })); mC.frustumCulled = false; mC.renderOrder = 5; scene.add(mC); }

        return { id: p.id, K, M, r, ux, uy, E, W, mats, mDren, vidrio: mVid ? mVid.material : null, BV: noche ? 1.7 : 1.0, DASH, colDash, gDash, cFondoTubo, cFondoSup, cFlujo,
          plantaFluye, manchas, anillos, gotas, puentes, burb, burbM, hT, DESL, colD, gD, ND, flP, GENTE, gP, matP, noche, hz };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.3 * kb;
        for (const m of s.mDren) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.6 * kb;
        if (s.vidrio) s.vidrio.uniforms.uBrillo.value = s.BV * (1 + 0.2 * kb);
        const { E } = s;
        // ---- el agua que corre por los tubos: un pulso que avanza (color = función de t y de dónde está el guion)
        for (const D of s.DASH) {
          const fl = D.tipo !== "crudo" && !s.plantaFluye ? 0 : 1;
          const f = (((D.s / 7 - t * D.vel / 7) % 1) + 1) % 1, a = fl * (0.25 + 0.75 * Math.pow(0.5 + 0.5 * Math.cos(TAU * f), 3));
          const c0 = D.sup ? s.cFondoTubo : s.cFondoSup, c1 = s.cFlujo[D.tipo];
          const rr = c0.r + (c1.r - c0.r) * a, gg = c0.g + (c1.g - c0.g) * a, bb = c0.b + (c1.b - c0.b) * a;
          for (let j = 0; j < 4; j++) { const o = (D.i0 + j) * 3; s.colDash[o] = rr; s.colDash[o + 1] = gg; s.colDash[o + 2] = bb; }
        }
        s.gDash.attributes.color.needsUpdate = true;
        // ---- la mancha respira y los anillos salen de la boca (ciclo de 5 s)
        for (const Mn of s.manchas) Mn.m.scale.setScalar(0.94 + 0.06 * Math.sin(t * 0.45 + Mn.ph));
        for (const A of s.anillos) {
          const f = (((t / 5 + A.ph) % 1) + 1) % 1, R = (1.5 + 13 * f) * s.M;
          A.m.position.set(A.P[0], A.P[1], A.P[2]); A.m.scale.set(R, 1, R * 1.3); A.m.rotation.set(0, s.r, 0);
          A.m.material.uniforms.uAlfa.value = 0.55 * (1 - f) * Math.min(1, f * 6);
        }
        // ---- las gotas de los chorros: de la boca a la arena (caída con gravedad), en bucle
        for (const G of s.gotas) {
          const q = (((t * 1.6 + G.f0) % 1) + 1) % 1, B = G.B;
          const P = E(B.u + 0.15 + 0.9 * q, B.v + G.dv, B.h - 0.1 - (B.h - piso(B.u + 1.0)) * q * q);
          G.m.position.set(P[0], P[1], P[2]); G.m.scale.setScalar(s.M * (1 - 0.4 * q));
        }
        // ---- los puentes de los sedimentadores giran despacio
        for (const Pn of s.puentes) Pn.m.rotation.set(0, TAU * (t / Pn.per + Pn.ph), 0);
        // ---- las burbujas: suben un poco, crecen y se apagan
        s.burb.forEach(([u, v, ph, per], i) => {
          const q = (((t / per + ph) % 1) + 1) % 1, P = E(u, v, s.hT - 0.28 + 0.12 * q);
          s.burbM[i].position.set(P[0], P[1], P[2]); s.burbM[i].scale.setScalar(s.M * Math.max(1e-4, Math.sin(Math.PI * q)) * 1.1);
        });
        // ---- los destellos del lago
        for (let i = 0; i < s.ND; i++) {
          const [ph, w] = s.DESL[i], a = Math.pow(Math.max(0, Math.sin(t * w + ph)), 6) * (s.noche ? 0.12 : 0.3);
          for (let j = 0; j < 4; j++) s.colD.set([0.9 * a, 0.95 * a, a], (i * 4 + j) * 3);
        }
        s.gD.attributes.color.needsUpdate = true;
        // ---- la gente
        if (s.flP) {
          const dirW = (du, dv) => [du * s.ux - dv * s.uy, du * s.uy + dv * s.ux];
          s.GENTE.forEach((g, i) => {
            if (g[0] === "calle") {
              const T = 260 / g[2], f = (((t / T + g[1]) % 1) + 1) % 1, v = g[3] * (-130 + 260 * f), u = U_CALLE + g[3] * (AC - 0.9);
              const [x, y] = s.W(u, v), [dx, dy] = dirW(0, g[3]); s.flP.poner(i, x, y, dx, dy, 1, 0, g[2]);
            } else { const [x, y] = s.W(g[1], g[2]), [dx, dy] = dirW(g[3], g[4]); s.flP.poner(i, x, y, dx, dy, 1, 0, 0); }
          });
          s.flP.listo();
        }
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
