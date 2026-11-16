// Pieza «beneficioseco» (ficha: beneficioseco.json; reglas: scripts/maqueta_tipos/beneficioseco.py): el beneficio seco por
// dentro, genérico (pergamino → café oro), centrado en `lugar` y orientado por `rumbo` (u: hacia el frente abierto; v: a su
// izquierda). Es una MAQUETA DE CORTE: la galera de estructura metálica con sus cerchas y un faldón de lámina arriba al fondo;
// la pared del fondo (u−) y la de la izquierda (v+) enteras (zócalo de bloque y lámina acanalada), la del frente y la de la
// derecha cortadas a media rodilla. El proceso corre de v− a v+ (de derecha a izquierda vista desde el frente):
//   RECIBO      el camión de plataforma (objeto camionsacos) estacionado afuera, de costado, con quien descarga costales;
//               la báscula industrial de plataforma con costales de pergamino y su indicador; la tolva de recibo con su
//               rejilla, donde alguien vacía un costal (chorro de pergamino) y una estiba de costales de pergamino.
//   LIMPIEZA    la prelimpiadora: cuerpo de lámina sobre patas, tolva de alimentación, la caja de zarandas que vibra.
//   TRILLA      la trilladora: el cuerpo cilíndrico horizontal sobre su bastidor, la tolva arriba, el motor con su polea y la
//               banda que giran, la canaleta por la que sale el café oro a un montón, y el ducto de la cascarilla al fondo.
//   CLASIFIC.   las zarandas vibratorias de tres pisos (tres bocas que sueltan grano a tres cajones) y el cilindro rotativo
//               de cribas sobre sus rodillos, perforado, con el grano que cae por debajo.
//   REVISIÓN    la mesa larga con el grano oro extendido, dos guacales, y quien lo revisa a mano.
//   EMPAQUE     la boca de llenado con el saco abierto sobre su báscula (el grano cae y el saco se llena), una fila de sacos
//               cosidos de pie (la costura arriba) y las estibas de sacos de yute en tarimas. Sacos lisos: sin texto.
// Lo que se mueve (función pura de t, nada se acumula): las poleas y la banda, el cilindro de cribas, la vibración de la
// prelimpiadora y de las zarandas, los chorros de grano (cada grano con su fase fija) y la gente con su pose. De noche
// (ctx.ES.noche) se encienden las lámparas colgadas de las cerchas, sus manchas en el piso y el indicador de la báscula.
// Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto. «resaltar» la pieza aviva las máquinas, el grano y los sacos.
(function (MAQ) {
  MAQ.PIEZAS.beneficioseco = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche || ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo)
      const cPiso = tonos.pavimento.clone().lerp(lin(COL.mar), dia ? 0.1 : 0.04).multiplyScalar(dia ? 0.84 : noche ? 1.15 : 0.88);
      const cJunta = cPiso.clone().multiplyScalar(0.72);
      const cPatio = tonos.pavimento.clone().lerp(tonos.calle, 0.35).multiplyScalar(dia ? 0.78 : noche ? 1.05 : 0.8);
      const cBloque = tonos.muro.clone().lerp(tonos.pavimento, 0.35).multiplyScalar(noche ? 1.2 : 0.95);
      const cCorte = tonos.pavimento.clone().multiplyScalar(noche ? 1.3 : 0.95);
      const cLamina = tonos.techo.clone().lerp(tonos.pavimento, 0.55).lerp(lin(COL.mar), dia ? 0.12 : 0.04).multiplyScalar(noche ? 1.15 : 0.98);
      const cAcero = tonos.linea.clone().lerp(tonos.asfalto, 0.25).lerp(tonos.pavimento, 0.25);
      const cMetal = tonos.asfalto.clone().lerp(tonos.pavimento, 0.45);
      const cOscuro = tonos.linea.clone().lerp(tonos.asfalto, 0.4);
      const cMaqA = dia ? lin(COL.mar).lerp(tonos.linea, 0.42) : tonos.techo.clone().lerp(tonos.muro, 0.3).multiplyScalar(noche ? 1.2 : 1);
      const cMaqB = tonos.bien.clone().lerp(tonos.linea, 0.5).multiplyScalar(noche ? 1.3 : 0.95);
      const cMadera = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.55).multiplyScalar(noche ? 0.7 : 0.95);
      const cYute = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.3).multiplyScalar(noche ? 0.62 : 0.98);
      const cYuteP = cYute.clone().lerp(tonos.arena || lin(COL.costa), 0.35).multiplyScalar(0.92);   // los costales de pergamino
      const cPerg = (tonos.arena ? tonos.arena.clone() : lin(COL.costa)).lerp(lin(COL.costa), 0.3).multiplyScalar(noche ? 0.7 : 1.0);
      const cOro = tonos.verde.clone().lerp(lin(COL.tierra_alta), 0.5).lerp(lin(COL.costa), 0.28).multiplyScalar(noche ? 0.72 : 0.98);
      const cCasc = cPerg.clone().lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(1.05);
      const cLuz = lin(COL.luz), cHilo = cOscuro.clone().lerp(cYute, 0.3);
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const almohada = (() => {
        const a = new THREE.SphereGeometry(1, 10, 6).toNonIndexed().attributes.position.array, o = new Float32Array(a.length);
        const pw = (x, e) => Math.sign(x) * Math.pow(Math.abs(x), e);
        for (let i = 0; i < a.length; i += 3) {
          const x = pw(a[i], 0.42), z = pw(a[i + 2], 0.42), m = Math.max(Math.abs(x), Math.abs(z));
          o[i] = x; o[i + 2] = z; o[i + 1] = pw(a[i + 1], 0.75) * (1 - 0.5 * m * m * m);
        }
        return o;
      })();

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const DU = [ux, 0, -uy], DV = [-uy, 0, -ux];          // los ejes u y v en la escena (unitarios)
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // ---- primitivas con la luz horneada
        const cara = (acc, P, col, ref, f = 1) => {
          const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = sombra(nx, ny, nz) * f, q = acc.pos.length / 3;
          for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        const caja = (acc, T, a0, a1, b0, b1, c0, c1, col, op = {}) => {
          const C = T((a0 + a1) / 2, (b0 + b1) / 2, (c0 + c1) / 2);
          const caras = [
            [[a0, b0, c1], [a1, b0, c1], [a1, b1, c1], [a0, b1, c1]],
            [[a0, b0, c0], [a1, b0, c0], [a1, b0, c1], [a0, b0, c1]],
            [[a0, b1, c0], [a1, b1, c0], [a1, b1, c1], [a0, b1, c1]],
            [[a0, b0, c0], [a0, b1, c0], [a0, b1, c1], [a0, b0, c1]],
            [[a1, b0, c0], [a1, b1, c0], [a1, b1, c1], [a1, b0, c1]],
          ];
          caras.forEach((q, k) => {
            if (k === 0 && op.sinTope) return;
            const V = q.map((a) => T(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
            cara(acc, V, k === 0 && op.tope ? op.tope : col, m, k === 0 ? 1 : (k % 2 ? 0.97 : 1.02));
          });
        };
        const cj = (acc, u0, u1, v0, v1, h0, h1, col, op) => caja(acc, E, u0, u1, v0, v1, h0, h1, col, op);
        const losa = (acc, u0, u1, v0, v1, h, cu, cv, col) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0);
          for (let i = 0, k = 0; i < nu; i++) for (let j = 0; j < nv; j++, k++) {
            const a = u0 + (u1 - u0) * i / nu, b = u0 + (u1 - u0) * (i + 1) / nu, e = v0 + (v1 - v0) * j / nv, f = v0 + (v1 - v0) * (j + 1) / nv;
            const cc = col((a + b) / 2, (e + f) / 2, k), q = acc.pos.length / 3;
            for (const [uu, vv] of [[a, e], [b, e], [b, f], [a, f]]) { const P = E(uu, vv, h); acc.pos.push(P[0], P[1], P[2]); acc.col.push(cc.r * l, cc.g * l, cc.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        const gema = (acc, tri, P, rx, ry, rz, rot, col, plana = 0) => {
          const cr = Math.cos(rot), sr = Math.sin(rot), v = [];
          for (let i = 0; i < tri.length; i += 3) {
            const x = tri[i] * rx * M, y = tri[i + 1] * ry * M, z = tri[i + 2] * rz * M;
            v.push(P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr);
          }
          for (let i = 0; i < v.length; i += 9) {
            const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const n = Math.hypot(nx, ny, nz) || 1, sb = sombra(nx / n, Math.abs(ny / n), nz / n);
            c.copy(col).multiplyScalar(plana + (1 - plana) * sb);
            const q = acc.pos.length / 3;
            for (let j = 0; j < 9; j += 3) { acc.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };
        // un cilindro vertical en (u, v) de h0 a h1, radio rr (m), con su tapa; r1 = otro radio arriba (cono truncado)
        const cil = (acc, u, v, h0, h1, rr, seg, col, tapa, r1) => {
          const C = E(u, v, (h0 + h1) / 2), ra = rr, rb = r1 === undefined ? rr : r1;
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg;
            const P = [E(u + ra * Math.cos(a0), v + ra * Math.sin(a0), h0), E(u + ra * Math.cos(a1), v + ra * Math.sin(a1), h0),
              E(u + rb * Math.cos(a1), v + rb * Math.sin(a1), h1), E(u + rb * Math.cos(a0), v + rb * Math.sin(a0), h1)];
            cara(acc, P, col, [0, 1, 2].map((j) => (P[0][j] + P[1][j]) / 2 - C[j]));
            if (tapa) { const T0 = E(u, v, h1); cara(acc, [P[3], P[2], T0, T0], tapa, [0, 1, 0]); }
          }
        };
        // un cilindro de eje cualquiera: A y B puntos de escena, radio en metros; tapas opcionales
        const tubo = (acc, A, B, rr, seg, col, tapas) => {
          const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
          let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]], R = rr * M;
          const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * R);
          for (let i = 0; i < seg; i++) {
            const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1), nm = o((t0 + t1) / 2);
            const P = [[A[0] + va[0], A[1] + va[1], A[2] + va[2]], [A[0] + vb[0], A[1] + vb[1], A[2] + vb[2]],
              [B[0] + vb[0], B[1] + vb[1], B[2] + vb[2]], [B[0] + va[0], B[1] + va[1], B[2] + va[2]]];
            cara(acc, P, typeof col === "function" ? col(i) : col, nm);
            if (tapas) {
              cara(acc, [P[0], P[1], A, A], tapas, a.map((x) => -x));
              cara(acc, [P[3], P[2], B, B], tapas, a);
            }
          }
        };
        const barra = (acc, A, B, rr, col) => tubo(acc, A, B, rr / M, 4, col);
        const geoLocal = (acc, P) => { const g = malla.geometria(acc); g.translate(-P[0], -P[1], -P[2]); return g; };
        const enEscena = (geo, mat, orden) => { const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };

        // ================= la galera: piso, patio de maniobras, muros, columnas, cerchas y el faldón de lámina
        const U0 = -7, U1 = 7, V0 = -12, V1 = 12, H0 = 0.12, HZ = 1.4, HW = 5.6, EP = 0.22, HC = 0.6, HCU = 7.0;
        const piso = malla.nueva(), solido = malla.nueva(), lam = malla.nueva(), juntas = malla.nueva(), patio = malla.nueva();
        losa(piso, U0 - EP, U1 + EP, V0 - EP, V1 + EP, H0, 1.0, 1.0, (u, v, k) =>
          c.copy(cPiso).multiplyScalar(0.9 + 0.12 * ruido(u, v, 6, 11) + 0.05 * ruido(u, v, 1.5, 12) + 0.02 * hz(k, 13)).clone());
        cj(solido, U0 - EP, U1 + EP, V0 - EP, V1 + EP, 0, H0, cCorte, { sinTope: true });
        for (let u = U0 + 3.5; u < U1; u += 3.5) losa(juntas, u - 0.025, u + 0.025, V0, V1, H0 + 0.004, 0.05, 24, () => cJunta);
        for (let v = V0 + 4; v < V1; v += 4) losa(juntas, U0, U1, v - 0.025, v + 0.025, H0 + 0.004, 14, 0.05, () => cJunta);
        // el patio de maniobras a la derecha (donde se estaciona el camión), un poco más bajo y más oscuro
        losa(patio, U0 - 1, U1 + 2, V0 - 7.5, V0 - EP, 0.04, 1.5, 1.5, (u, v, k) =>
          c.copy(cPatio).multiplyScalar(0.88 + 0.16 * ruido(u, v, 4, 14) + 0.03 * hz(k, 15)).clone());
        cj(solido, U0 - 1, U1 + 2, V0 - 7.5, V0 - EP, 0, 0.04, cPatio.clone().multiplyScalar(0.8), { sinTope: true });
        // un muro a lo largo de un eje: T(s, d, h) → punto (s: a lo largo, d: espesor). Zócalo de bloque con sus juntas y la
        // lámina acanalada arriba (franjas que alternan tono: la canal y la cresta), con su remate.
        const muro = (T, s0, s1, nrm, hTop) => {
          caja(solido, T, s0, s1, 0, EP, H0, Math.min(HZ, hTop), cBloque, { tope: cCorte });
          // las juntas del bloque (40 × 20) en la cara de adentro
          for (let h = H0 + 0.2, f = 0; h < Math.min(HZ, hTop) - 0.05; h += 0.2, f++) cara(juntas, [T(s0, EP + 0.006, h - 0.012), T(s1, EP + 0.006, h - 0.012), T(s1, EP + 0.006, h + 0.012), T(s0, EP + 0.006, h + 0.012)], cJunta, nrm);
          for (let f = 0, h = H0; h < Math.min(HZ, hTop) - 0.1; h += 0.2, f++) for (let s = s0 + (f % 2) * 0.2 + 0.4; s < s1 - 0.05; s += 0.4)
            cara(juntas, [T(s - 0.01, EP + 0.006, h), T(s + 0.01, EP + 0.006, h), T(s + 0.01, EP + 0.006, Math.min(h + 0.2, HZ)), T(s - 0.01, EP + 0.006, Math.min(h + 0.2, HZ))], cJunta, nrm);
          if (hTop <= HZ) return;
          const PASO = 0.19;
          for (let s = s0, k = 0; s < s1 - 0.01; s += PASO, k++) {
            const b = Math.min(s1, s + PASO), cresta = k % 2 === 0, d = cresta ? EP * 0.5 + 0.03 : EP * 0.5;
            const tono = cLamina.clone().multiplyScalar((cresta ? 1.06 : 0.84) * (0.95 + 0.08 * ruido(s, 0, 3, 16)));
            cara(lam, [T(s, d, HZ), T(b, d, HZ), T(b, d, hTop), T(s, d, hTop)], tono, nrm);
            cara(lam, [T(s, d - 0.06, HZ), T(b, d - 0.06, HZ), T(b, d - 0.06, hTop), T(s, d - 0.06, hTop)], tono.clone().multiplyScalar(0.8), nrm.map((x) => -x));
          }
          caja(solido, T, s0, s1, EP * 0.5 - 0.06, EP * 0.5 + 0.08, hTop - 0.08, hTop, cAcero);            // el remate
          caja(solido, T, s0, s1, EP * 0.5 - 0.02, EP * 0.5 + 0.12, HZ - 0.02, HZ + 0.06, cAcero);      // el tapajuntas
        };
        const Tf = (s, d, h) => E(U0 - EP + d, s, h), Ti = (s, d, h) => E(s, V1 + EP - d, h);
        muro(Tf, V0 - EP, V1 + EP, DU, HW);
        muro(Ti, U0, U1 + EP, DV.map((x) => -x), HW);
        // las cortadas: frente (u = U1) y derecha (v = V0), a media rodilla, con el vano de entrada en la derecha
        cj(solido, U1, U1 + EP, V0 - EP, V1, H0, HC, cBloque, { tope: cCorte });
        cj(solido, U0, -2.2, V0 - EP, V0, H0, HC, cBloque, { tope: cCorte });
        cj(solido, 3.8, U1, V0 - EP, V0, H0, HC, cBloque, { tope: cCorte });
        // las columnas (perfil de acero) cada 4 m, al fondo y al frente, y las cerchas de dos aguas con sus diagonales
        const COLV = []; for (let v = V0; v <= V1 + 0.01; v += 4) COLV.push(v);
        const cumbre = (u) => HW + 0.25 + (HCU - HW - 0.25) * (1 - Math.abs(u) / (U1 - U0) * 2);
        for (const v of COLV) {
          for (const u of [U0 + 0.1, U1 - 0.1]) { cj(solido, u - 0.1, u + 0.1, v - 0.08, v + 0.08, H0, HW + 0.25, cAcero); cj(solido, u - 0.2, u + 0.2, v - 0.2, v + 0.2, H0, H0 + 0.03, cOscuro); }
          const A = (u, h) => E(u, v, h);
          barra(solido, A(U0, HW + 0.25), A(0, HCU), 0.055 * M, cAcero); barra(solido, A(0, HCU), A(U1, HW + 0.25), 0.055 * M, cAcero);
          barra(solido, A(U0, HW + 0.25), A(U1, HW + 0.25), 0.045 * M, cAcero);
          for (let k = 1; k < 8; k++) {
            const u = U0 + (U1 - U0) * k / 8, un = U0 + (U1 - U0) * (k + (k < 4 ? 1 : -1)) / 8;
            barra(solido, A(u, HW + 0.25), A(u, cumbre(u)), 0.025 * M, cAcero);
            if (k !== 4) barra(solido, A(u, HW + 0.25), A(un, cumbre(un)), 0.022 * M, cAcero);
          }
        }
        // las costaneras a lo largo de v, sobre los cordones de arriba
        for (const u of [U0 + 0.3, -4.5, -2.5, -0.6, 0.6, 2.5, 4.5, U1 - 0.3]) cj(solido, u - 0.05, u + 0.05, V0, V1, cumbre(u) + 0.06, cumbre(u) + 0.16, cAcero.clone().multiplyScalar(1.1));
        // el faldón de lámina del fondo (la maqueta de corte deja ver adentro): de U0 a −3.6, en franjas acanaladas
        { const uA = U0 - 0.4, uB = -3.6;
          for (let v = V0 - 0.3, k = 0; v < V1 + 0.3; v += 0.19, k++) {
            const b = Math.min(V1 + 0.3, v + 0.19), sube = k % 2 ? 0 : 0.035, tono = cLamina.clone().multiplyScalar(k % 2 ? 0.86 : 1.08);
            cara(lam, [E(uA, v, cumbre(U0) + 0.18 + sube - 0.08), E(uA, b, cumbre(U0) + 0.18 + sube - 0.08), E(uB, b, cumbre(uB) + 0.18 + sube), E(uB, v, cumbre(uB) + 0.18 + sube)], tono, [0, 1, 0]);
          }
          cj(solido, uB - 0.05, uB + 0.05, V0 - 0.3, V1 + 0.3, cumbre(uB) + 0.12, cumbre(uB) + 0.26, cAcero); }

        // ================= las lámparas colgadas (de noche encienden su foco y su mancha en el piso)
        const lampara = malla.nueva(), foco = malla.nueva(), manchas = malla.nueva();
        const LAMPS = []; for (const v of [-8, -2, 4, 10]) for (const u of [-2.5, 2.5]) LAMPS.push([u, v]);
        for (const [u, v] of LAMPS) {
          barra(solido, E(u, v, HW + 0.25), E(u, v, 4.6), 0.012 * M, cOscuro);
          cil(lampara, u, v, 4.3, 4.6, 0.38, 14, cMaqA.clone().multiplyScalar(0.8), cMaqA.clone().multiplyScalar(0.7), 0.1);
          cil(foco, u, v, 4.28, 4.3, 0.34, 14, cLuz.clone().multiplyScalar(noche ? 1 : 0.35), cLuz.clone().multiplyScalar(noche ? 1 : 0.35), 0.34);
          if (noche) {
            const q = manchas.pos.length / 3, nc = cLuz.clone().multiplyScalar(0.22), R = 3.4, S = 20;
            const Cc = E(u, v, H0 + 0.015); manchas.pos.push(...Cc); manchas.col.push(nc.r, nc.g, nc.b);
            for (let i = 0; i <= S; i++) { const a = TAU * i / S; manchas.pos.push(...E(u + R * Math.cos(a), v + R * Math.sin(a), H0 + 0.015)); manchas.col.push(0, 0, 0); }
            for (let i = 0; i < S; i++) manchas.idx.push(q, q + 1 + i, q + 2 + i);
          }
        }

        // ================= sacos y estibas
        const sacos = malla.nueva(), grano = malla.nueva();
        const saco = (acc, P, largo, rot, k, col) => gema(acc, almohada, P, largo, 0.13, 0.29, rot, col.clone().multiplyScalar(0.88 + 0.16 * hz(k, 33)), 0.28);
        const tarima = (uc, vc) => {
          for (const dv of [-0.42, 0, 0.42]) cj(solido, uc - 0.6, uc + 0.6, vc + dv - 0.05, vc + dv + 0.05, H0, H0 + 0.1, cMadera.clone().multiplyScalar(0.8));
          for (let i = 0; i < 6; i++) { const u = uc - 0.5 + i * 0.2; cj(solido, u - 0.08, u + 0.08, vc - 0.5, vc + 0.5, H0 + 0.1, H0 + 0.14, cMadera.clone().multiplyScalar(0.9 + 0.15 * hz(i + uc * 13 + vc * 7, 31))); }
        };
        const estiba = (uc, vc, camadas, n, col) => {
          tarima(uc, vc);
          for (let l = 0; l < camadas; l++) {
            const h = H0 + 0.14 + 0.115 + l * 0.215, ult = l === camadas - 1, falta = ult ? Math.floor(hz(n, 34) * 3) : -1;
            if (l % 2 === 0) { for (let j = 0; j < 2; j++) if (j !== falta) saco(sacos, E(uc + (hz(n * 31 + l * 7 + j, 35) - 0.5) * 0.06, vc - 0.25 + 0.5 * j, h), 0.5, -r, n * 41 + l * 5 + j, col); }
            else { for (let j = 0; j < 2; j++) if (j !== falta) saco(sacos, E(uc - 0.3 + 0.6 * j, vc + (hz(n * 37 + l * 3 + j, 36) - 0.5) * 0.06, h), 0.48, -r + Math.PI / 2, n * 43 + l * 7 + j, col); }
          }
        };
        // un saco de pie, cosido arriba: el cuerpo, el hombro, las orejas y la costura (un cordón oscuro)
        const sacoPie = (u, v, k, abierto) => {
          const tono = cYute.clone().multiplyScalar(0.92 + 0.14 * hz(k, 37)), hb = H0 + (abierto ? 0.16 : 0);
          cil(sacos, u, v, hb, hb + 0.62, 0.3, 14, tono, null, 0.31);
          cil(sacos, u, v, hb + 0.62, hb + 0.8, 0.31, 14, tono.clone().multiplyScalar(0.94), abierto ? null : tono.clone().multiplyScalar(0.9), abierto ? 0.3 : 0.16);
          if (abierto) return;
          const a = hz(k, 38) * Math.PI, du = Math.cos(a) * 0.24, dv = Math.sin(a) * 0.24;
          cj(sacos, u - 0.04, u + 0.04, v - 0.04, v + 0.04, hb + 0.78, hb + 0.86, tono);
          barra(sacos, E(u - du, v - dv, hb + 0.83), E(u + du, v + dv, hb + 0.83), 0.035 * M, tono.clone().multiplyScalar(0.85));   // la boca cosida
          barra(sacos, E(u - du * 0.95, v - dv * 0.95, hb + 0.87), E(u + du * 0.95, v + dv * 0.95, hb + 0.87), 0.012 * M, cHilo);    // la costura
          for (const s of [-1, 1]) gema(sacos, oct, E(u + s * du * 1.12, v + s * dv * 1.12, hb + 0.84), 0.06, 0.05, 0.05, a, tono.clone().multiplyScalar(0.8), 0.3);   // las orejas
        };
        // la estiba de pergamino al recibo y las de café oro en el empaque (sacos de yute lisos)
        estiba(5.4, -10.6, 4, 1, cYuteP); estiba(5.4, -9.3, 3, 2, cYuteP);
        let ne = 10;
        for (const uc of [-6.0, -4.75]) for (const vc of [10.9, 9.7, 8.5]) estiba(uc, vc, 4 + Math.floor(hz(ne, 32) * 3) - (uc > -5 && vc < 9 ? 2 : 0), ne++, cYute);
        // el pergamino que espera turno en el frente: estibas de costales y una carretilla con dos costales
        estiba(4.6, -4.6, 3, 3, cYuteP); estiba(4.6, -3.3, 2, 4, cYuteP); estiba(5.9, -4.0, 4, 5, cYuteP);
        { const KU = 4.4, KV = 0.2;
          for (const s of [-1, 1]) { tubo(solido, E(KU - 0.1, KV + s * 0.22, H0 + 0.15), E(KU + 0.1, KV + s * 0.22, H0 + 0.15), 0.15, 12, cOscuro, cMetal);
            barra(solido, E(KU, KV + s * 0.2, H0 + 0.15), E(KU - 0.55, KV + s * 0.2, H0 + 1.25), 0.025 * M, cMaqA); }
          cj(solido, KU + 0.02, KU + 0.2, KV - 0.25, KV + 0.25, H0, H0 + 0.04, cMetal);
          barra(solido, E(KU - 0.55, KV - 0.2, H0 + 1.25), E(KU - 0.55, KV + 0.2, H0 + 1.25), 0.025 * M, cMaqA);
          saco(sacos, E(KU - 0.1, KV, H0 + 0.35), 0.4, -r + Math.PI / 2, 90, cYuteP); saco(sacos, E(KU - 0.2, KV, H0 + 0.58), 0.4, -r + Math.PI / 2, 91, cYuteP); }
        for (let k = 0; k < 5; k++) sacoPie(-3.0 + k * 0.68, 11.3 + (hz(k, 39) - 0.5) * 0.08, 50 + k, false);

        // ================= RECIBO: la báscula industrial con costales y su indicador; la tolva de recibo con su rejilla
        const BU = 2.6, BV = -9.6;
        const maq = malla.nueva(), pantalla = malla.nueva();
        cj(solido, BU - 1.2, BU + 1.2, BV - 1.2, BV + 1.2, H0, H0 + 0.12, cMetal, { tope: cMetal.clone().multiplyScalar(1.15) });
        for (let k = -2; k <= 2; k++) cj(juntas, BU - 1.15, BU + 1.15, BV + k * 0.45 - 0.015, BV + k * 0.45 + 0.015, H0 + 0.124, H0 + 0.13, cOscuro);   // el estriado
        cj(solido, BU - 1.28, BU - 1.2, BV - 1.28, BV + 1.28, H0, H0 + 0.1, cOscuro); cj(solido, BU + 1.2, BU + 1.28, BV - 1.28, BV + 1.28, H0, H0 + 0.1, cOscuro);
        barra(solido, E(BU - 1.55, BV + 1.25, H0), E(BU - 1.55, BV + 1.25, H0 + 1.3), 0.045 * M, cOscuro);
        cj(maq, BU - 1.7, BU - 1.4, BV + 1.0, BV + 1.5, H0 + 1.25, H0 + 1.6, cMaqB);
        { const Q = [E(BU - 1.395, BV + 1.07, H0 + 1.33), E(BU - 1.395, BV + 1.43, H0 + 1.33), E(BU - 1.395, BV + 1.43, H0 + 1.5), E(BU - 1.395, BV + 1.07, H0 + 1.5)];
          const q = pantalla.pos.length / 3, cc = tonos.bien.clone().lerp(cLuz, 0.4).multiplyScalar(noche ? 1 : 0.7);
          Q.forEach((X) => { pantalla.pos.push(...X); pantalla.col.push(cc.r, cc.g, cc.b); }); pantalla.idx.push(q, q + 1, q + 2, q, q + 2, q + 3); }
        for (let l = 0; l < 3; l++) for (let j = 0; j < 2; j++) if (!(l === 2 && j === 1))
          saco(sacos, E(BU + (l % 2 ? -0.32 + 0.64 * j : 0), BV + (l % 2 ? 0 : -0.27 + 0.54 * j), H0 + 0.12 + 0.115 + l * 0.215), 0.5, -r + (l % 2 ? Math.PI / 2 : 0), 70 + l * 3 + j, cYuteP);
        // la tolva: pirámide invertida de lámina sobre cuatro patas, con su rejilla arriba y el pergamino adentro
        const TU = -0.6, TV = -9.4, TH = 1.45, TA = 0.85, TB = 0.22, TH0 = 0.55;
        for (let i = 0; i < 4; i++) {
          const q = [[-1, -1], [1, -1], [1, 1], [-1, 1]], a = q[i], b = q[(i + 1) % 4];
          const P = [E(TU + a[0] * TB, TV + a[1] * TB, TH0), E(TU + b[0] * TB, TV + b[1] * TB, TH0), E(TU + b[0] * TA, TV + b[1] * TA, TH), E(TU + a[0] * TA, TV + a[1] * TA, TH)];
          const m = E(TU + (a[0] + b[0]) * 0.5, TV + (a[1] + b[1]) * 0.5, TH0), C0 = E(TU, TV, TH0);
          cara(maq, P, cMaqA.clone().multiplyScalar(0.95 + 0.05 * i), [m[0] - C0[0], 0.2, m[2] - C0[2]]);
          barra(solido, E(TU + a[0] * TA, TV + a[1] * TA, H0), E(TU + a[0] * TA, TV + a[1] * TA, TH), 0.04 * M, cOscuro);
          barra(solido, E(TU + a[0] * TA, TV + a[1] * TA, TH), E(TU + b[0] * TA, TV + b[1] * TA, TH), 0.04 * M, cAcero);
        }
        cil(grano, TU, TV, TH - 0.12, TH - 0.1, 0.62, 4, cPerg.clone().multiplyScalar(0.92), cPerg.clone().multiplyScalar(0.92));
        for (let k = -3; k <= 3; k++) barra(solido, E(TU + k * 0.23, TV - TA, TH + 0.02), E(TU + k * 0.23, TV + TA, TH + 0.02), 0.015 * M, cOscuro);   // la rejilla
        // una canaleta inclinada en U; de la tolva a la prelimpiadora sube un sinfín (el tubo)
        const canal = (A, B, ancho, col) => {
          const [ua, va, ha] = A, [ub, vb, hb] = B, l = Math.hypot(ub - ua, vb - va) || 1, nu = -(vb - va) / l * ancho / 2, nv = (ub - ua) / l * ancho / 2;
          cara(maq, [E(ua - nu, va - nv, ha), E(ua + nu, va + nv, ha), E(ub + nu, vb + nv, hb), E(ub - nu, vb - nv, hb)], col, [0, 1, 0]);
          for (const s of [-1, 1]) cara(maq, [E(ua + s * nu, va + s * nv, ha), E(ub + s * nu, vb + s * nv, hb), E(ub + s * nu, vb + s * nv, hb + 0.18), E(ua + s * nu, va + s * nv, ha + 0.18)], col.clone().multiplyScalar(0.9), [s * nu, 0, s * nv]);
        };
        tubo(maq, E(TU, TV + 0.2, TH0 - 0.1), E(-1.6, -6.4, 2.55), 0.16, 12, cMaqB.clone().multiplyScalar(0.9), cOscuro);

        // ================= LIMPIEZA: la prelimpiadora (el cuerpo quieto; la caja de cribas vibra)
        const LU = -2.2, LV = -5.2;
        for (const [a, b] of [[-0.9, -0.6], [0.9, -0.6], [-0.9, 0.6], [0.9, 0.6]]) barra(solido, E(LU + a, LV + b, H0), E(LU + a, LV + b, H0 + 1.1), 0.05 * M, cOscuro);
        cj(maq, LU - 1.0, LU + 1.0, LV - 0.7, LV + 0.7, H0 + 1.0, H0 + 1.15, cOscuro);
        cj(maq, LU - 1.05, LU + 0.4, LV - 0.72, LV + 0.72, H0 + 1.95, H0 + 2.55, cMaqA, { tope: cMaqA.clone().multiplyScalar(1.1) });   // la cabeza con el aspirador
        tubo(maq, E(LU - 0.6, LV, H0 + 2.55), E(LU - 0.6, LV, HW - 0.4), 0.15, 12, cMetal, null);    // el ducto del polvo, hacia arriba
        tubo(maq, E(LU - 0.6, LV, HW - 0.4), E(U0 + 0.2, LV, HW - 0.4), 0.15, 12, cMetal, null);
        cil(maq, -1.6, -6.4, 2.45, 2.6, 0.25, 12, cMetal, cOscuro);
        canal([-1.6, -6.2, 2.5], [LU - 0.3, LV - 0.4, H0 + 2.55], 0.3, cMetal);
        const vib1 = malla.nueva(), PV1c = E(LU, LV, H0 + 1.5);
        caja(vib1, E, LU - 1.0, LU + 1.0, LV - 0.68, LV + 0.68, H0 + 1.18, H0 + 1.9, cMaqA.clone().multiplyScalar(0.92), { tope: cMaqA });
        for (let k = 0; k < 6; k++) { const u = LU - 0.85 + k * 0.34; cj(vib1, u - 0.03, u + 0.03, LV - 0.7, LV + 0.7, H0 + 1.2, H0 + 1.88, cMaqA.clone().multiplyScalar(0.78)); }   // las costillas
        cj(vib1, LU + 1.0, LU + 1.35, LV - 0.25, LV + 0.25, H0 + 1.2, H0 + 1.32, cMetal);                // la boca de salida
        // la canaleta de la prelimpiadora a la tolva de la trilla
        canal([LU + 1.25, LV + 0.2, H0 + 1.25], [-1.9, -1.55, H0 + 2.95], 0.3, cMetal);

        // ================= TRILLA: bastidor, cuerpo cilíndrico, tolva, motor con polea y banda, salida del oro y cascarilla
        const RU = -2.2, RV = -0.6, RH = H0 + 1.75, RR = 0.62, RL = 1.2;     // el cuerpo: eje a lo largo de v
        for (const [a, b] of [[-0.7, -1.1], [0.7, -1.1], [-0.7, 1.1], [0.7, 1.1]]) cj(solido, RU + a - 0.08, RU + a + 0.08, RV + b - 0.08, RV + b + 0.08, H0, RH - 0.4, cOscuro);
        cj(solido, RU - 0.8, RU + 0.8, RV - 1.2, RV + 1.2, RH - 0.5, RH - 0.38, cMaqB.clone().multiplyScalar(0.8));
        tubo(maq, E(RU, RV - RL, RH), E(RU, RV + RL, RH), RR, 20, (i) => cMaqB.clone().multiplyScalar(0.92 + 0.12 * Math.cos(TAU * i / 20)), cMaqB.clone().multiplyScalar(0.8));
        for (const s of [-0.7, 0, 0.7]) tubo(maq, E(RU, RV + s - 0.05, RH), E(RU, RV + s + 0.05, RH), RR + 0.04, 20, cOscuro, null);   // los aros
        // la tolva de la trilla
        for (let i = 0; i < 4; i++) {
          const q = [[-1, -1], [1, -1], [1, 1], [-1, 1]], a = q[i], b = q[(i + 1) % 4], TA2 = 0.55, TB2 = 0.18, h0 = RH + RR - 0.05, h1 = RH + RR + 0.75, vc = RV - 0.6;
          const P = [E(RU + a[0] * TB2, vc + a[1] * TB2, h0), E(RU + b[0] * TB2, vc + b[1] * TB2, h0), E(RU + b[0] * TA2, vc + b[1] * TA2, h1), E(RU + a[0] * TA2, vc + a[1] * TA2, h1)];
          const m = E(RU + (a[0] + b[0]) * 0.5, vc + (a[1] + b[1]) * 0.5, h0), C0 = E(RU, vc, h0);
          cara(maq, P, cMaqA.clone().multiplyScalar(0.95 + 0.05 * i), [m[0] - C0[0], 0.2, m[2] - C0[2]]);
        }
        cil(grano, RU, RV - 0.6, RH + RR + 0.6, RH + RR + 0.62, 0.45, 4, cPerg.clone().multiplyScalar(0.92), cPerg.clone().multiplyScalar(0.92));
        // la canaleta de salida del oro (hacia el frente) y el montón de café oro en el piso
        canal([RU + 0.4, RV + 0.6, RH - 0.25], [RU + 1.45, RV + 0.9, H0 + 0.75], 0.28, cMetal);
        const MOU = RU + 1.95, MOV = RV + 1.0;
        for (let i = 0; i < 160; i++) {
          const a = hz(i, 81) * TAU, rr = 0.75 * Math.sqrt(hz(i, 82)), hh = H0 + 0.42 * (1 - rr / 0.75) + 0.02;
          gema(grano, oct, E(MOU + rr * Math.cos(a), MOV + rr * Math.sin(a), hh), 0.07, 0.045, 0.055, hz(i, 83) * 3, cOro.clone().multiplyScalar(0.82 + 0.3 * hz(i, 84)), 0.35);
        }
        cil(grano, MOU, MOV, H0, H0 + 0.42, 0.72, 16, cOro.clone().multiplyScalar(0.85), cOro.clone().multiplyScalar(0.9), 0.04);
        // la cascarilla: un ducto que sube hacia el fondo y un montón claro en el rincón
        tubo(maq, E(RU - RR + 0.05, RV, RH + 0.2), E(U0 + 0.6, RV, RH + 1.4), 0.13, 12, cMetal, null);
        tubo(maq, E(U0 + 0.6, RV, RH + 1.4), E(U0 + 0.6, RV + 1.4, H0 + 0.9), 0.13, 12, cMetal, null);
        cil(grano, U0 + 0.9, RV + 1.6, H0, H0 + 0.5, 0.9, 16, cCasc.clone().multiplyScalar(0.85), cCasc, 0.15);
        // el motor (al costado, v−) con su polea, y la polea del cuerpo: giran; la banda las une
        const MU_ = RU, MV_ = RV - RL - 0.9;
        cj(solido, MU_ - 0.45, MU_ + 0.45, MV_ - 0.35, MV_ + 0.35, H0, H0 + 0.25, cOscuro);
        tubo(maq, E(MU_, MV_ - 0.3, H0 + 0.62), E(MU_, MV_ + 0.25, H0 + 0.62), 0.3, 14, cMaqB, cMaqB.clone().multiplyScalar(0.8));
        for (let k = 0; k < 6; k++) { const v = MV_ - 0.25 + k * 0.09; tubo(maq, E(MU_, v - 0.015, H0 + 0.62), E(MU_, v + 0.015, H0 + 0.62), 0.33, 14, cMaqB.clone().multiplyScalar(0.8), null); }  // las aletas
        const polea = (u, v, h, R) => {
          const acc = malla.nueva(), P = E(u, v, h);
          tubo(acc, E(u, v - 0.06, h), E(u, v + 0.06, h), R, 18, cOscuro, cAcero.clone().multiplyScalar(1.3));
          for (let k = 0; k < 4; k++) { const a = TAU * k / 4; barra(acc, E(u, v + 0.075, h), E(u + R * 0.9 * Math.cos(a), v + 0.075, h + R * 0.9 * Math.sin(a)), 0.035 * M, cLuz.clone().lerp(cMetal, 0.5)); }
          return { m: enEscena(geoLocal(acc, P), malla.material(), 5), P };
        };
        const PL1 = polea(MU_, MV_ + 0.42, H0 + 0.62, 0.2), PL2 = polea(RU, RV - RL - 0.12, RH, 0.48);
        { const bandA = (s) => [MU_ + s * 0.2, MV_ + 0.42, H0 + 0.62], bandB = (s) => [RU + s * 0.48, RV - RL - 0.12, RH];
          for (const s of [-1, 1]) { const A = bandA(s), B = bandB(s); barra(maq, E(A[0], A[1], A[2]), E(B[0], B[1], B[2]), 0.03 * M, cOscuro); } }

        // ================= CLASIFICACIÓN: las zarandas vibratorias (tres pisos, tres bocas) y el cilindro de cribas
        const ZU = -2.3, ZV = 4.0;
        for (const [a, b] of [[-0.75, -1.2], [0.75, -1.2], [-0.75, 1.2], [0.75, 1.2]]) {
          const hh = H0 + 0.95 + (b > 0 ? -0.25 : 0.25);
          barra(solido, E(ZU + a, ZV + b, H0), E(ZU + a, ZV + b, hh - 0.2), 0.05 * M, cOscuro);
          tubo(solido, E(ZU + a, ZV + b, hh - 0.2), E(ZU + a, ZV + b, hh), 0.07, 8, cMaqB, null);   // el resorte
        }
        canal([-1.6, 0.4, H0 + 0.75], [ZU, ZV - 1.2, H0 + 1.95], 0.3, cMetal);
        const vib2 = malla.nueva(), PV2c = E(ZU, ZV, H0 + 1.3);
        const ZT = (s, d, h) => E(ZU + d, ZV + s, h - s * 0.2);      // inclinada: baja hacia v+
        caja(vib2, ZT, -1.3, 1.3, -0.8, -0.72, H0 + 0.95, H0 + 1.75, cMaqA);
        caja(vib2, ZT, -1.3, 1.3, 0.72, 0.8, H0 + 0.95, H0 + 1.75, cMaqA);
        caja(vib2, ZT, -1.38, -1.3, -0.8, 0.8, H0 + 0.95, H0 + 1.75, cMaqA.clone().multiplyScalar(0.9));
        [0, 1, 2].forEach((k) => {
          const h = H0 + 1.0 + k * 0.25, col = cMetal.clone().multiplyScalar(1.1 - k * 0.1);
          caja(vib2, ZT, -1.3, 1.3, -0.72, 0.72, h, h + 0.03, col);
          for (let j = 0; j < 9; j++) { const s = -1.2 + j * 0.3; caja(vib2, ZT, s - 0.01, s + 0.01, -0.72, 0.72, h + 0.03, h + 0.045, cOscuro); }   // la malla
          for (let i = 0; i < 26; i++) gema(vib2, oct, ZT(-1.2 + 2.3 * hz(i + k * 40, 85), -0.6 + 1.2 * hz(i + k * 40, 86), h + 0.07), 0.05, 0.03, 0.04, hz(i, 87) * 3, cOro.clone().multiplyScalar(0.85 + 0.25 * hz(i + k, 88)), 0.35);
          caja(vib2, ZT, 1.3, 1.6, -0.5 + k * 0.4, -0.25 + k * 0.4, h - 0.08, h + 0.03, cMetal);   // la boca de cada piso
        });
        const CAJ = [0, 1, 2].map((k) => [ZU - 0.37 + k * 0.4, ZV + 1.95]);
        for (const [u, v] of CAJ) { cj(maq, u - 0.18, u + 0.18, v - 0.22, v + 0.22, H0, H0 + 0.5, cMadera, { tope: cOro.clone().multiplyScalar(0.9) }); }
        // el cilindro de cribas: sobre un bastidor con rodillos, eje a lo largo de v e inclinado; gira
        const CU = 2.0, CV = 3.6, CH = H0 + 1.35, CR = 0.62, CL = 1.7, CI = 0.18;
        for (const s of [-1, 1]) {
          const hh = CH - CR - 0.05 - s * CI;
          for (const a of [-0.45, 0.45]) { barra(solido, E(CU + a, CV + s * CL * 0.7, H0), E(CU + a, CV + s * CL * 0.7, hh), 0.05 * M, cOscuro);
            tubo(solido, E(CU + a, CV + s * CL * 0.7 - 0.08, hh), E(CU + a, CV + s * CL * 0.7 + 0.08, hh), 0.1, 10, cAcero, cOscuro); }
          cj(solido, CU - 0.55, CU + 0.55, CV + s * CL * 0.7 - 0.06, CV + s * CL * 0.7 + 0.06, hh - 0.25, hh - 0.18, cOscuro);
        }
        const cribas = malla.nueva(), PC = E(CU, CV, CH);
        const A1 = E(CU, CV - CL, CH + CI), B1 = E(CU, CV + CL, CH - CI);
        tubo(cribas, A1, B1, CR, 24, (i) => cMetal.clone().multiplyScalar(i % 2 ? 0.9 : 1.08));
        for (const f of [0, 0.33, 0.66, 1]) { const P = [0, 1, 2].map((j) => A1[j] + (B1[j] - A1[j]) * f), D = [0, 1, 2].map((j) => (B1[j] - A1[j]) * 0.025); tubo(cribas, [P[0] - D[0], P[1] - D[1], P[2] - D[2]], [P[0] + D[0], P[1] + D[1], P[2] + D[2]], CR + 0.05, 24, cMaqA, cOscuro); }
        // las perforaciones: puntos oscuros en la camisa (quads salidos un pelo, en anillos)
        { const ax = [B1[0] - A1[0], B1[1] - A1[1], B1[2] - A1[2]], la = Math.hypot(...ax), a = ax.map((x) => x / la);
          let p1 = [a[2], 0, -a[0]]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
          for (let f = 0.05; f < 0.97; f += 0.075) for (let k = 0; k < 18; k++) {
            if (Math.abs(f - 0.33) < 0.04 || Math.abs(f - 0.66) < 0.04) continue;
            const t0 = TAU * (k + (Math.round(f * 40) % 2) * 0.5) / 18, w = 0.05 * M, R = (CR + 0.006) * M;
            const n = [0, 1, 2].map((j) => Math.cos(t0) * p1[j] + Math.sin(t0) * p2[j]), tg = [0, 1, 2].map((j) => -Math.sin(t0) * p1[j] + Math.cos(t0) * p2[j]);
            const C0 = [0, 1, 2].map((j) => A1[j] + ax[j] * f + n[j] * R);
            const P = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([s, q]) => [0, 1, 2].map((j) => C0[j] + a[j] * s * w + tg[j] * q * w));
            cara(cribas, P, cOscuro.clone().multiplyScalar(0.7), n, 1);
          } }
        const mCribas = enEscena(geoLocal(cribas, PC), malla.material(), 5);
        const ejeC = new THREE.Vector3(B1[0] - A1[0], B1[1] - A1[1], B1[2] - A1[2]).normalize();
        // la tolva bajo el cilindro, con el grano clasificado
        cj(maq, CU - 0.6, CU + 0.6, CV - 1.2, CV + 1.2, H0, H0 + 0.55, cMaqB.clone().multiplyScalar(0.85), { tope: cOro.clone().multiplyScalar(0.88) });

        // ================= REVISIÓN: la mesa larga con el grano oro extendido y dos guacales
        const XU = 2.7, XV = 8.2, XH = H0 + 0.88, XL = 1.6, XA = 0.5;
        for (const [a, b] of [[-0.42, -1.5], [0.42, -1.5], [-0.42, 1.5], [0.42, 1.5]]) barra(solido, E(XU + a, XV + b, H0), E(XU + a, XV + b, XH - 0.05), 0.035 * M, cOscuro);
        cj(maq, XU - XA, XU + XA, XV - XL, XV + XL, XH - 0.05, XH, cMadera.clone().multiplyScalar(1.05), { tope: cMadera.clone().multiplyScalar(1.15) });
        for (const s of [-1, 1]) cj(maq, XU - XA, XU + XA, XV + s * XL - 0.03, XV + s * XL + 0.03, XH, XH + 0.07, cMadera);
        cj(maq, XU + XA - 0.03, XU + XA + 0.03, XV - XL, XV + XL, XH, XH + 0.07, cMadera); cj(maq, XU - XA - 0.03, XU - XA + 0.03, XV - XL, XV + XL, XH, XH + 0.07, cMadera);
        for (let i = 0; i < 240; i++) {
          const u = XU - XA + 0.08 + (2 * XA - 0.16) * hz(i, 91), v = XV - XL + 0.1 + (2 * XL - 0.2) * hz(i, 92);
          gema(grano, oct, E(u, v, XH + 0.025), 0.045, 0.025, 0.035, hz(i, 93) * 3, cOro.clone().multiplyScalar(0.8 + 0.35 * hz(i, 94)), 0.35);
        }
        for (const v of [XV - 1.05, XV + 1.15]) { cil(maq, XU + 0.05, v, XH, XH + 0.18, 0.2, 14, cMaqA, null, 0.24); cil(grano, XU + 0.05, v, XH + 0.14, XH + 0.15, 0.21, 14, cOro, cOro); }

        // ================= EMPAQUE: la boca de llenado sobre el saco abierto en su báscula
        const FU = -1.5, FV = 9.6;
        cj(solido, FU - 0.45, FU + 0.45, FV - 0.45, FV + 0.45, H0, H0 + 0.16, cMetal, { tope: cMetal.clone().multiplyScalar(1.12) });
        barra(solido, E(FU - 0.75, FV - 0.35, H0), E(FU - 0.75, FV - 0.35, H0 + 2.6), 0.05 * M, cOscuro);
        cj(maq, FU - 0.95, FU - 0.55, FV - 0.6, FV - 0.1, H0 + 2.3, H0 + 3.0, cMaqA);
        for (let i = 0; i < 4; i++) {
          const q = [[-1, -1], [1, -1], [1, 1], [-1, 1]], a = q[i], b = q[(i + 1) % 4], h0 = H0 + 1.55, h1 = H0 + 2.35;
          const P = [E(FU + a[0] * 0.12, FV + a[1] * 0.12, h0), E(FU + b[0] * 0.12, FV + b[1] * 0.12, h0), E(FU + b[0] * 0.55, FV + b[1] * 0.55, h1), E(FU + a[0] * 0.55, FV + a[1] * 0.55, h1)];
          const m = E(FU + (a[0] + b[0]) * 0.5, FV + (a[1] + b[1]) * 0.5, h0), C0 = E(FU, FV, h0);
          cara(maq, P, cMaqA.clone().multiplyScalar(0.95 + 0.05 * i), [m[0] - C0[0], 0.2, m[2] - C0[2]]);
        }
        cj(maq, FU - 0.55, FU + 0.55, FV - 0.55, FV + 0.55, H0 + 2.35, H0 + 2.45, cOscuro);
        tubo(maq, E(FU, FV, H0 + 1.55), E(FU, FV, H0 + 1.3), 0.1, 12, cMetal, null);
        canal([CU, CV + CL + 0.3, H0 + 0.55], [FU + 0.4, FV - 0.5, H0 + 2.45], 0.28, cMetal);   // el transportador que sube al empaque
        sacoPie(FU, FV, 60, true);
        const nivelM = malla.nueva(); cil(nivelM, 0, 0, 0, 0.02, 0.29, 14, cOro, cOro);
        const g0 = E(0, 0, 0), gNivel = malla.geometria(nivelM); gNivel.translate(-g0[0], -g0[1], -g0[2]);
        const matGrano = malla.material(), mNivel = enEscena(gNivel, matGrano, 6);

        // ================= la sombra de contacto: rectángulos suaves bajo lo que se asienta en el piso
        const KS = ctx.CFG.sombra_contacto || (dia ? 0.4 : 0.22);
        const so = { pos: [], a: [], idx: [] };
        const sombraRect = (u0, u1, v0, v1, pad) => {
          const anillo = (d, al) => [[u0 - d, v0 - d], [u1 + d, v0 - d], [u1 + d, v1 + d], [u0 - d, v1 + d]].map(([u, v]) => ({ P: E(u, v, H0 + 0.012), a: al }));
          const I = anillo(0, 1), O = anillo(pad, 0), q = so.pos.length / 3;
          for (const x of I.concat(O)) { so.pos.push(...x.P); so.a.push(x.a); }
          so.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; so.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
        };
        sombraRect(4.8, 6.0, -11.2, -8.7, 0.4); sombraRect(4.0, 6.5, -5.1, -2.8, 0.4); sombraRect(-6.6, -4.15, 7.9, 11.5, 0.5);
        sombraRect(BU - 1.2, BU + 1.2, BV - 1.2, BV + 1.2, 0.3); sombraRect(TU - TA, TU + TA, TV - TA, TV + TA, 0.5);
        sombraRect(LU - 1.0, LU + 1.0, LV - 0.7, LV + 0.7, 0.6); sombraRect(RU - 0.8, RU + 0.8, RV - 1.2, RV + 1.2, 0.6);
        sombraRect(ZU - 0.8, ZU + 0.8, ZV - 1.3, ZV + 1.3, 0.6); sombraRect(CU - 0.6, CU + 0.6, CV - 1.6, CV + 1.6, 0.6);
        sombraRect(XU - XA, XU + XA, XV - XL, XV + XL, 0.5); sombraRect(-3.3, 0, 11.0, 11.6, 0.3);
        sombraRect(U0, U1, V1 - 0.02, V1, 0.8); sombraRect(U0, U0 + 0.02, V0, V1, 0.8);
        const gS = new THREE.BufferGeometry();
        gS.setAttribute("position", new THREE.BufferAttribute(new Float32Array(so.pos), 3));
        gS.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(so.a), 1));
        gS.setIndex(so.idx);
        const mS = new THREE.Mesh(gS, new THREE.ShaderMaterial({ uniforms: { uK: { value: KS * 0.75 } }, transparent: true, depthWrite: false,
          polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
          vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: "uniform float uK; varying float vA; void main(){ float a = uK * vA * vA; gl_FragColor = vec4(0.0, 0.0, 0.0, a); }" }));
        mS.frustumCulled = false; mS.renderOrder = 4; scene.add(mS);

        // ================= las mallas fijas
        malla.poner(piso, malla.material({ desfase: 2 }), 2);
        malla.poner(patio, malla.material({ desfase: 1 }), 2);
        malla.poner(juntas, malla.material({ desfase: 3 }), 3);
        malla.poner(solido, malla.material({ desfase: 1 }), 3);
        malla.poner(lam, malla.material(), 3);
        const matMaq = malla.material(); malla.poner(maq, matMaq, 5);
        malla.poner(lampara, malla.material(), 5);
        malla.poner(foco, malla.material(), 5).material.uniforms.uBrillo.value = noche ? 1.8 : 1;
        malla.poner(pantalla, malla.material(), 5).material.uniforms.uBrillo.value = noche ? 1.5 : 1.1;
        if (noche) malla.poner(manchas, malla.material({ aditivo: true, desfase: 4 }), 4);
        const matSacos = malla.material(); malla.poner(sacos, matSacos, 5);
        malla.poner(grano, matGrano, 5);
        const matVib = malla.material();
        const mVib1 = enEscena(geoLocal(vib1, PV1c), matVib, 5), mVib2 = enEscena(geoLocal(vib2, PV2c), matVib, 5);
        const matCribas = mCribas.material, matPoleas = [PL1.m.material, PL2.m.material];

        // ================= los chorros de grano: granos que caen de A a B, cada uno con su fase (función de t)
        const mkGota = (col) => { const a = malla.nueva(); gema(a, oct, [0, 0, 0], 0.05, 0.035, 0.04, 0, col, 0.4); return malla.geometria(a); };
        const gOro = mkGota(cOro), gPerg = mkGota(cPerg);
        const chorros = [];
        const chorro = (A, B, n, per, geo, fase, cuando) => {
          const g = [];
          for (let j = 0; j < n; j++) { const m = enEscena(geo, matGrano, 6); g.push({ m, f0: j / n + 0.3 * hz(j + chorros.length * 31, 61) / n, du: (hz(j, 62 + chorros.length) - 0.5) * 0.1, dv: (hz(j, 63 + chorros.length) - 0.5) * 0.1, rot: hz(j, 64) * TAU }); }
          chorros.push({ A, B, per, g, fase, cuando });
        };
        // la trilla suelta el oro al montón; las tres bocas de las zarandas a sus cajones; el cilindro gotea a su tolva; el llenado
        chorro([RU + 1.5, RV + 0.92, H0 + 0.72], [MOU, MOV, H0 + 0.45], 12, 0.5, gOro, 0);
        [0, 1, 2].forEach((k) => { const h = H0 + 1.0 + k * 0.25 - 1.45 * 0.2 - 0.05; chorro([ZU - 0.37 + k * 0.4, ZV + 1.5, h], [CAJ[k][0], CAJ[k][1], H0 + 0.5], 6, 0.45, gOro, k * 0.17); });
        for (const f of [-0.6, 0, 0.6]) chorro([CU, CV + f * CL, CH - CR - 0.05], [CU, CV + f * CL, H0 + 0.56], 4, 0.6, gOro, f);
        chorro([FU, FV, H0 + 1.3], [FU, FV, H0 + 0.5], 12, 0.45, gOro, 0.2);

        // ================= la gente: quien descarga del camión, quien revisa en la mesa, quien vacía en la tolva, otra en la mesa
        const NP = clamp(p.personas | 0, 0, 4), PG = 1.1;
        const camisas = dia ? [lin(COL.mar).multiplyScalar(0.72), tonos.mal.clone(), tonos.bien.clone(), tonos.secundario.clone()]
          : noche ? [lin(COL.costa), tonos.mal.clone(), tonos.secundario.clone().multiplyScalar(0.85), tonos.bien.clone()]
          : [lin(COL.mar), tonos.mal.clone(), tonos.bien.clone(), tonos.secundario.clone()];
        const c0 = Math.floor(hz(2, 65) * 4);
        const PS = 6.4, F1 = hz(3, 66), F3 = hz(4, 67);
        // [u, v, hacia u, hacia v, pose]
        const SLOTS = [[0.4, -13.0, 0, -1, { nombre: "cargar", periodo: PS, fase: F1 }],
          [XU - XA - 0.45, XV - 0.4, 1, 0, "atender"],
          [TU, TV - TA - 0.25, 0, 1, { nombre: "cargar", periodo: PS * 0.92, fase: F3 }],
          [XU - XA - 0.45, XV + 0.7, 1, 0.1, "atender"]].slice(0, NP);
        const flP = NP ? ctx.flota("persona", NP, { tamano: K * PG, lev: H0 * K, orden: 6, semilla: (p.semilla * 11 + np * 5) % 997,
          color: (i) => camisas[(i + c0) % 4], pose: (i) => SLOTS[i][4] }) : null;
        // el chorro de pergamino de quien vacía en la tolva: solo en la fase en que inclina el costal
        if (NP >= 3) chorro([TU, TV - 0.35, TH + 0.25], [TU, TV - 0.1, TH - 0.1], 10, 0.4, gPerg, 0, (t) => { const f = (((t / (PS * 0.92) + F3) % 1) + 1) % 1; return f > 0.34 && f < 0.74; });
        // el camión, de costado, junto a la entrada (afuera, en el patio de maniobras)
        const flCam = ctx.flota("camionsacos", 1, { tamano: K, orden: 6, semilla: p.semilla % 97 });
        const CAM = W(0.4, -15.2);

        return { id: p.id, K, M, E, W, ux, uy, DU, DV, flP, SLOTS, flCam, CAM, chorros, mVib1, mVib2, PV1c, PV2c, mCribas, PC, ejeC,
          PL1, PL2, mNivel, FU, FV, H0, hz, mats: [matMaq, matSacos, matGrano, matVib, matCribas, ...matPoleas] };
      });
    },
    en(t, lista, ctx) {
      const { clamp, THREE } = ctx, TAU = 2 * Math.PI;
      const q = new THREE.Quaternion(), ejeV = new THREE.Vector3();
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) m.uniforms.uBrillo.value = 1 + 0.45 * k;
        s.flCam.mesh.material.uniforms.uBrillo.value = 1 + 0.3 * k;
        // el camión quieto, de costado, con la cabina hacia el frente
        s.flCam.poner(0, s.CAM[0], s.CAM[1], s.ux, s.uy, 1, 0, 0); s.flCam.listo();
        // la vibración: la prelimpiadora (a lo largo de u) y las zarandas (a lo largo de su pendiente), puras de t
        const a1 = 0.035 * s.M * Math.sin(TAU * 4.2 * t), a2 = 0.045 * s.M * Math.sin(TAU * 3.6 * t + 1.1);
        s.mVib1.position.set(s.PV1c[0] + s.DU[0] * a1, s.PV1c[1] + 0.3 * Math.abs(a1), s.PV1c[2] + s.DU[2] * a1);
        s.mVib2.position.set(s.PV2c[0] + s.DV[0] * a2, s.PV2c[1] + 0.4 * a2, s.PV2c[2] + s.DV[2] * a2);
        // el cilindro de cribas gira despacio; las poleas, rápido (la chica, más)
        s.mCribas.position.set(s.PC[0], s.PC[1], s.PC[2]); s.mCribas.quaternion.setFromAxisAngle(s.ejeC, TAU * t / 5.5);
        ejeV.set(s.DV[0], s.DV[1], s.DV[2]);
        s.PL1.m.position.set(...s.PL1.P); s.PL1.m.quaternion.copy(q.setFromAxisAngle(ejeV, -TAU * t * 1.6));
        s.PL2.m.position.set(...s.PL2.P); s.PL2.m.quaternion.copy(q.setFromAxisAngle(ejeV, -TAU * t * 1.6 * 0.2 / 0.48));
        // el saco que se llena: el nivel sube en 9 s y vuelve a empezar (otro saco)
        const fl = ((t / 9) % 1 + 1) % 1, Pn = s.E(s.FU, s.FV, s.H0 + 0.2 + 0.55 * fl);
        s.mNivel.position.set(Pn[0], Pn[1], Pn[2]); s.mNivel.scale.setScalar(1);
        for (const ch of s.chorros) {
          const on = ch.cuando ? ch.cuando(t) : true;
          ch.g.forEach((g) => {
            const qq = (((t / ch.per + g.f0 + ch.fase) % 1) + 1) % 1, e = qq * qq;
            const P = s.E(ch.A[0] + (ch.B[0] - ch.A[0]) * qq + g.du, ch.A[1] + (ch.B[1] - ch.A[1]) * qq + g.dv, ch.A[2] + (ch.B[2] - ch.A[2]) * e);
            g.m.position.set(P[0], P[1], P[2]); g.m.rotation.set(0, g.rot + t * 5, 0.5); g.m.scale.setScalar(on ? 1 : 0);
          });
        }
        // la gente
        if (s.flP) {
          s.SLOTS.forEach((sl, i) => {
            const [x, y] = s.W(sl[0], sl[1]), dx = sl[2] * s.ux - sl[3] * s.uy, dy = sl[2] * s.uy + sl[3] * s.ux, l = Math.hypot(dx, dy) || 1;
            s.flP.poner(i, x, y, dx / l, dy / l, 1, 0, 0);
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
