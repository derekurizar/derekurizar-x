// Pieza «tostaduria» (ficha: tostaduria.json; reglas: scripts/maqueta_tipos/tostaduria.py): el interior de una tostaduría
// de café, genérica, centrada en `lugar` y orientada por `rumbo` (u: hacia el frente abierto; v: a su izquierda). Es una
// MAQUETA DE CORTE: sin techo, con la pared del fondo (u−) y la de la izquierda (v+) enteras, de ladrillo, con sus ventanales
// (los del fondo, altos; los de la izquierda, en lo alto de la pared) que dejan entrar haces de luz al piso; la del frente y
// la de la derecha cortadas a media rodilla para mirar adentro (cámara en azimut ≈ rumbo + 45, elevación 15–35°).
// Adentro, sobre el piso de cemento pulido con sus juntas: las ESTIBAS de sacos de café verde de yute (lisos, sin texto ni
// sellos) en tarimas de madera, en la esquina del fondo; una báscula de piso con un saco abierto (el grano verde a la vista);
// una o dos `tostadora` (objeto del catálogo, ctx.flota; cada una con su desfase); detrás de la primera, una plataforma de
// metal con su escalera desde la que una `persona` carga un saco en la TOLVA; la mesa de catación redonda con sus tazas; y
// los estantes con bolsas de café tostado (lisas, sin marcas) contra la pared izquierda.
// Lo que se mueve (función pura de t, nada se acumula): los tambores, brazos y humo de las tostadoras (su pose); el saco que
// aparece en manos de quien carga, sube, se inclina sobre la tolva, se vacía (se aplana) con un chorro de grano verde que cae,
// y desaparece, en un ciclo de 7 s; el nivel de grano en la tolva que sube mientras cae el chorro y baja mientras el tambor lo
// traga; el polvo que flota en los haces de luz, una nube de polvo en la boca de la tolva al vaciar y el vapor de las tazas.
// `personas` (objeto persona con su pose): 1 = quien carga (`cargar`, sus brazos suben con el saco); 2 = y quien revisa la
// bandeja de enfriamiento (`atender`); 3 = y quien cata en la mesa (`sorber`). Sin colores
// escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto. «resaltar» la pieza aviva los sacos, el grano y las tostadoras.
(function (MAQ) {
  MAQ.PIEZAS.tostaduria = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo)
      const cPiso = tonos.pavimento.clone().lerp(lin(COL.mar), dia ? 0.1 : 0.04).multiplyScalar(dia ? 0.86 : noche ? 1.2 : 0.9);
      const cJunta = cPiso.clone().multiplyScalar(0.72);
      const cLadr = tonos.techo.clone().lerp(tonos.mal, dia ? 0.12 : 0.05).multiplyScalar(noche ? 1.25 : 0.92);
      const cMortero = tonos.muro.clone().multiplyScalar(noche ? 1.0 : 0.86);
      const cCorte = tonos.pavimento.clone().multiplyScalar(noche ? 1.3 : 0.95);
      const cMetal = tonos.asfalto.clone().lerp(tonos.pavimento, 0.45);
      const cOscuro = tonos.linea.clone().lerp(tonos.asfalto, 0.4);
      const cMadera = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.55).multiplyScalar(noche ? 0.7 : 0.95);
      const cYute = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.3).multiplyScalar(noche ? 0.62 : 0.98);
      const cVerde = tonos.verde.clone().lerp(lin(COL.tierra_alta), 0.5).lerp(lin(COL.costa), 0.12).multiplyScalar(noche ? 0.7 : 0.95);
      const cTostado = lin(COL.tierra_media).multiplyScalar(0.32).lerp(tonos.mal, 0.05);
      const cLuz = lin(COL.luz), cVidrio = lin(COL.luz).lerp(tonos.agua, 0.3).lerp(lin(COL.costa), 0.2);
      const cTaza = tonos.secundario.clone().lerp(lin(COL.costa), 0.3).multiplyScalar(noche ? 0.85 : 1);
      const cMesa = lin(COL.tierra_media).lerp(tonos.linea, 0.35).multiplyScalar(noche ? 0.9 : 1.05);
      const bolsas = [lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.45), tonos.linea.clone().lerp(tonos.asfalto, 0.25).multiplyScalar(noche ? 2.2 : 1.1),
        lin(COL.costa).multiplyScalar(0.86), lin(COL.tierra_media).multiplyScalar(0.75)];
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      // la almohada del saco: una esfera baja de caras que se vuelve caja redondeada y se adelgaza en los bordes
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
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // ---- caras con la luz horneada (4 puntos de escena; ref = hacia dónde es «afuera»)
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
            cara(acc, V, k === 0 && op.tope ? op.tope : col, m, 1);
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
        // un cilindro vertical en (u, v) de h0 a h1, radio rr (metros), con su tapa
        const cil = (acc, u, v, h0, h1, rr, seg, col, tapa) => {
          const C = E(u, v, (h0 + h1) / 2);
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg;
            const P = [E(u + rr * Math.cos(a0), v + rr * Math.sin(a0), h0), E(u + rr * Math.cos(a1), v + rr * Math.sin(a1), h0),
              E(u + rr * Math.cos(a1), v + rr * Math.sin(a1), h1), E(u + rr * Math.cos(a0), v + rr * Math.sin(a0), h1)];
            cara(acc, P, col, [0, 1, 2].map((j) => (P[0][j] + P[1][j]) / 2 - C[j]));
            if (tapa) { const T0 = E(u, v, h1); cara(acc, [P[3], P[2], T0, T0], tapa, [0, 1, 0]); }
          }
        };
        const barra = (acc, A, B, rr, col) => {
          const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
          let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
          for (let i = 0; i < 4; i++) {
            const t0 = TAU * i / 4, t1 = TAU * (i + 1) / 4, o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * rr);
            const va = o(t0), vb = o(t1), nm = o((t0 + t1) / 2);
            cara(acc, [[A[0] + va[0], A[1] + va[1], A[2] + va[2]], [A[0] + vb[0], A[1] + vb[1], A[2] + vb[2]],
              [B[0] + vb[0], B[1] + vb[1], B[2] + vb[2]], [B[0] + va[0], B[1] + va[1], B[2] + va[2]]], col, nm);
          }
        };
        const sinTraslado = (acc, mat, orden) => { const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };

        // ================= el galpón: piso, paredes de ladrillo con ventanales, paredes cortadas
        const U0 = -9, U1 = 9, V0 = -6, V1 = 6, H0 = 0.1, HW = 4.8, EP = 0.3, HC = 0.55;
        const piso = malla.nueva(), solido = malla.nueva(), ladr = malla.nueva(), vidrio = malla.nueva(), juntas = malla.nueva();
        losa(piso, U0 - EP, U1 + EP, V0 - EP, V1 + EP, H0, 0.75, 0.75, (u, v, k) =>
          c.copy(cPiso).multiplyScalar(0.9 + 0.12 * ruido(u, v, 5.5, 11) + 0.05 * ruido(u, v, 1.4, 12) + 0.02 * hz(k, 13)).clone());
        cj(solido, U0 - EP, U1 + EP, V0 - EP, V1 + EP, 0, H0, cCorte, { sinTope: true });
        // las juntas del pulido, cada 3 m
        for (let u = U0 + 3; u < U1; u += 3) losa(juntas, u - 0.025, u + 0.025, V0, V1, H0 + 0.004, 0.05, 12, () => cJunta);
        for (let v = V0 + 3; v < V1; v += 3) losa(juntas, U0, U1, v - 0.025, v + 0.025, H0 + 0.004, 18, 0.05, () => cJunta);
        // una pared a lo largo de un eje: L(s, h, d) → punto (s: a lo largo, d: espesor hacia adentro); vanos [s0, s1, h0, h1]
        const pared = (L, s0, s1, vanos, adentro) => {
          // el muro macizo por tramos alrededor de los vanos (cajas en (s, d, h))
          const T = (s, d, h) => L(s, h, d);
          const cortes = [s0].concat(...vanos.map((w) => [w[0], w[1]])).concat([s1]);
          for (let i = 0; i + 1 < cortes.length; i += 2) caja(solido, T, cortes[i], cortes[i + 1], 0, EP, H0, HW, cMortero, { tope: cCorte });
          for (const w of vanos) {
            caja(solido, T, w[0], w[1], 0, EP, H0, w[2], cMortero, { tope: cCorte });
            caja(solido, T, w[0], w[1], 0, EP, w[3], HW, cMortero, { tope: cCorte });
            // el vidrio (al medio del espesor) y su marco: dos parteluces y un travesaño
            const P = [L(w[0], w[2], EP / 2), L(w[1], w[2], EP / 2), L(w[1], w[3], EP / 2), L(w[0], w[3], EP / 2)];
            const q = vidrio.pos.length / 3;
            P.forEach((x, j) => { vidrio.pos.push(...x); const cc = cVidrio.clone().multiplyScalar(j < 2 ? 0.92 : 1.05); vidrio.col.push(cc.r, cc.g, cc.b); });
            vidrio.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
            const n = Math.max(2, Math.round((w[1] - w[0]) / 0.75));
            for (let k = 1; k < n; k++) { const s = w[0] + (w[1] - w[0]) * k / n; caja(solido, T, s - 0.035, s + 0.035, EP / 2 - 0.05, EP / 2 + 0.05, w[2], w[3], cOscuro); }
            for (const h of [w[2] + (w[3] - w[2]) * 0.5]) caja(solido, T, w[0], w[1], EP / 2 - 0.05, EP / 2 + 0.05, h - 0.035, h + 0.035, cOscuro);
            caja(solido, T, w[0] - 0.06, w[1] + 0.06, -0.02, EP + 0.1, w[2] - 0.08, w[2], cCorte);   // el alféizar
          }
          // el ladrillo de la cara de adentro: hiladas de 0.16 m, sogas de 0.40 m a matajunta, un poco salidas del mortero
          const HL = 0.16, LL = 0.4, JN = 0.024, sale = adentro * 0.014;
          let fila = 0;
          for (let h = H0 + 0.02; h + HL <= HW + 0.001; h += HL, fila++) {
            const off = (fila % 2) * LL / 2;
            for (let s = s0 - off; s < s1; s += LL) {
              const a = Math.max(s0, s + JN / 2), b = Math.min(s1, s + LL - JN / 2), hb = h + JN / 2, ht = h + HL - JN / 2;
              if (b - a < 0.08) continue;
              if (vanos.some((w) => b > w[0] - 0.01 && a < w[1] + 0.01 && ht > w[2] - 0.01 && hb < w[3] + 0.01)) continue;
              const k = fila * 997 + Math.round(s * 10), tono = cLadr.clone().multiplyScalar(0.8 + 0.26 * hz(k, 21) + 0.08 * ruido(s, h, 1.8, 22));
              const dd = adentro > 0 ? EP + sale : -sale;
              cara(ladr, [L(a, hb, dd), L(b, hb, dd), L(b, ht, dd), L(a, ht, dd)], tono, L.normal);
            }
          }
        };
        // los ejes de las paredes: el fondo (u = U0, a lo largo de v) y la izquierda (v = V1, a lo largo de u)
        const fondo = (s, h, d) => E(U0 - EP + d, s, h); fondo.normal = [ux, 0, -uy];
        const izq = (s, h, d) => E(s, V1 + EP - d, h); izq.normal = [uy, 0, ux];
        const VF = [[-4.75, -2.85, 1.7, 4.05], [-1.55, 0.35, 1.7, 4.05], [1.65, 3.55, 1.7, 4.05]];
        const VI = [[-7.2, -4.6, 2.75, 4.15], [-3.3, -0.7, 2.75, 4.15], [0.6, 3.2, 2.75, 4.15], [4.5, 7.1, 2.75, 4.15]];
        pared(fondo, V0 - EP, V1 + EP, VF, 1);
        pared(izq, U0, U1 + EP, VI, 1);
        // las paredes cortadas (frente y derecha), a media rodilla: el corte en el tono del corte; el ladrillo en su cara
        cj(solido, U1, U1 + EP, V0 - EP, V1, H0, HC, cMortero, { tope: cCorte });
        cj(solido, U0, U1, V0 - EP, V0, H0, HC, cMortero, { tope: cCorte });
        for (let fila = 0, h = H0 + 0.02; h + 0.16 <= HC; h += 0.16, fila++) {
          const off = (fila % 2) * 0.2;
          for (let s = V0 - EP - off; s < V1; s += 0.4) {
            const a = Math.max(V0 - EP, s + 0.012), b = Math.min(V1, s + 0.388); if (b - a < 0.08) continue;
            const tono = cLadr.clone().multiplyScalar(0.8 + 0.26 * hz(fila * 991 + Math.round(s * 10), 23));
            cara(ladr, [E(U1 + EP + 0.012, a, h + 0.012), E(U1 + EP + 0.012, b, h + 0.012), E(U1 + EP + 0.012, b, h + 0.148), E(U1 + EP + 0.012, a, h + 0.148)], tono, [ux, 0, -uy]);
          }
          for (let s = U0 - off; s < U1 + EP; s += 0.4) {
            const a = Math.max(U0, s + 0.012), b = Math.min(U1 + EP, s + 0.388); if (b - a < 0.08) continue;
            const tono = cLadr.clone().multiplyScalar(0.8 + 0.26 * hz(fila * 983 + Math.round(s * 10), 24));
            cara(ladr, [E(a, V0 - EP - 0.012, h + 0.012), E(b, V0 - EP - 0.012, h + 0.012), E(b, V0 - EP - 0.012, h + 0.148), E(a, V0 - EP - 0.012, h + 0.148)], tono, [uy, 0, ux]);
          }
        }

        // ================= la luz que entra por los ventanales del fondo: manchas en el piso y haces muy tenues
        const DV = -0.28;                     // el rayo baja 0.72 m por metro hacia el frente y se corre a la derecha
        const luzA = malla.nueva(), haz = malla.nueva();
        const pie = (v, h) => [U0 + (h - H0) / 0.72, v + DV * (h - H0) / 0.72];    // dónde cae en el piso el rayo de (U0, v, h)
        const haces = [];
        for (const w of VF) {
          const [a, b, s, tt] = w;
          // la mancha: el cuadro del vano proyectado, con un borde suave (anillo exterior a negro: se suma)
          const P = [pie(a, s), pie(b, s), pie(b, tt), pie(a, tt)], cx = (P[0][0] + P[2][0]) / 2, cy = (P[0][1] + P[2][1]) / 2;
          const nucleo = cLuz.clone().multiplyScalar(dia ? 0.05 : noche ? 0.035 : 0.04), q = luzA.pos.length / 3;
          for (const [pu, pv] of P) { luzA.pos.push(...E(cx + (pu - cx) * 0.86, cy + (pv - cy) * 0.86, H0 + 0.01)); luzA.col.push(nucleo.r, nucleo.g, nucleo.b); }
          for (const [pu, pv] of P) { luzA.pos.push(...E(cx + (pu - cx) * 1.08, cy + (pv - cy) * 1.08, H0 + 0.01)); luzA.col.push(0, 0, 0); }
          luzA.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; luzA.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
          // el haz: cuatro lados del prisma del vano a la mancha (más claro en la ventana, nada en el piso)
          const Wv = [E(U0, a, s), E(U0, b, s), E(U0, b, tt), E(U0, a, tt)], Fv = P.map(([pu, pv]) => E(pu, pv, H0 + 0.02));
          const ch = cLuz.clone().multiplyScalar(dia ? 0.007 : 0.01);
          for (let i = 0; i < 4; i++) {
            const j = (i + 1) % 4, qq = haz.pos.length / 3;
            for (const [X, cc] of [[Wv[i], ch], [Wv[j], ch], [Fv[j], null], [Fv[i], null]]) { haz.pos.push(...X); if (cc) haz.col.push(cc.r, cc.g, cc.b); else haz.col.push(0, 0, 0); }
            haz.idx.push(qq, qq + 1, qq + 2, qq, qq + 2, qq + 3);
          }
          haces.push({ a, b, s, tt });
        }

        // ================= las estibas: tarimas de madera con sacos de yute lisos (café verde), trabados por camada
        const sacos = malla.nueva();
        const tarima = (uc, vc) => {
          for (const dv of [-0.42, 0, 0.42]) cj(solido, uc - 0.6, uc + 0.6, vc + dv - 0.05, vc + dv + 0.05, H0, H0 + 0.1, cMadera.clone().multiplyScalar(0.8));
          for (let i = 0; i < 6; i++) { const u = uc - 0.6 + 0.1 + i * 0.2; cj(solido, u - 0.08, u + 0.08, vc - 0.5, vc + 0.5, H0 + 0.1, H0 + 0.14, cMadera.clone().multiplyScalar(0.9 + 0.15 * hz(i + uc * 13 + vc * 7, 31))); }
        };
        const saco = (acc, P, largo, rot, k, col) => gema(acc, almohada, P, largo, 0.13, 0.29, rot, col.clone().multiplyScalar(0.88 + 0.16 * hz(k, 33)), 0.28);
        const estiba = (uc, vc, camadas, n) => {
          tarima(uc, vc);
          for (let l = 0; l < camadas; l++) {
            const h = H0 + 0.14 + 0.115 + l * 0.215;
            const ult = l === camadas - 1, falta = ult ? Math.floor(hz(n, 34) * 3) : -1;   // en la de arriba, a veces falta uno
            if (l % 2 === 0) { for (let j = 0; j < 2; j++) if (j !== falta) saco(sacos, E(uc + (hz(n * 31 + l * 7 + j, 35) - 0.5) * 0.06, vc - 0.25 + 0.5 * j, h), 0.5, -r, n * 41 + l * 5 + j, cYute); }
            else { for (let j = 0; j < 2; j++) if (j !== falta) saco(sacos, E(uc - 0.3 + 0.6 * j, vc + (hz(n * 37 + l * 3 + j, 36) - 0.5) * 0.06, h), 0.48, -r + Math.PI / 2, n * 43 + l * 7 + j, cYute); }
          }
        };
        let n = 0;
        for (const uc of [-8.2, -6.85]) for (const vc of [4.85, 3.7, 2.55]) estiba(uc, vc, 4 + Math.floor(hz(n, 32) * 3) - (uc > -7 && vc < 3 ? 1 : 0), n++);
        // una estiba a medias junto a la plataforma (de la que se toman los sacos)
        estiba(-5.3, 3.0, 2, n++);

        // ================= la báscula de piso con un saco abierto: el café verde a la vista
        const BU = -7.45, BV = 0.55;
        cj(solido, BU - 0.55, BU + 0.55, BV - 0.55, BV + 0.55, H0, H0 + 0.09, cMetal, { tope: cMetal.clone().multiplyScalar(1.12) });
        barra(solido, E(BU - 0.62, BV - 0.5, H0), E(BU - 0.62, BV - 0.5, H0 + 1.15), 0.035 * M, cOscuro);
        cj(solido, BU - 0.7, BU - 0.55, BV - 0.72, BV - 0.28, H0 + 1.1, H0 + 1.38, cMetal);
        const pantalla = malla.nueva();
        { const Q = [E(BU - 0.545, BV - 0.66, H0 + 1.16), E(BU - 0.545, BV - 0.34, H0 + 1.16), E(BU - 0.545, BV - 0.34, H0 + 1.3), E(BU - 0.545, BV - 0.66, H0 + 1.3)];
          const qq = pantalla.pos.length / 3, cc = tonos.bien.clone().lerp(cLuz, 0.4).multiplyScalar(0.8);
          Q.forEach((X) => { pantalla.pos.push(...X); pantalla.col.push(cc.r, cc.g, cc.b); }); pantalla.idx.push(qq, qq + 1, qq + 2, qq, qq + 2, qq + 3); }
        // el saco de pie, abierto: el cuerpo de yute, la boca doblada y el grano verde arriba
        cil(sacos, BU, BV, H0 + 0.09, H0 + 0.5, 0.31, 12, cYute.clone().multiplyScalar(1.02), null);
        cil(sacos, BU, BV, H0 + 0.5, H0 + 0.76, 0.29, 12, cYute.clone().multiplyScalar(0.96), null);
        cil(sacos, BU, BV, H0 + 0.74, H0 + 0.84, 0.33, 12, cYute.clone().multiplyScalar(0.82), cYute.clone().multiplyScalar(0.78));   // la boca doblada
        const grano = malla.nueva();
        for (let i = 0; i < 46; i++) {
          const a = hz(i, 37) * TAU, rr = 0.27 * Math.sqrt(hz(i, 38));
          gema(grano, oct, E(BU + rr * Math.cos(a), BV + rr * Math.sin(a), H0 + 0.82 + 0.04 * (1 - rr / 0.27)), 0.05, 0.035, 0.04, hz(i, 39) * 3, cVerde.clone().multiplyScalar(0.85 + 0.25 * hz(i, 40)), 0.4);
        }
        cil(grano, BU, BV, H0 + 0.8, H0 + 0.845, 0.3, 12, cVerde.clone().multiplyScalar(0.8), cVerde.clone().multiplyScalar(0.8));

        // ================= las tostadoras (objeto del catálogo), mirando al frente; la primera con su plataforma de carga
        const NT = clamp(p.tostadoras | 0, 1, 2), TT = 1.0;
        const TOS = [[-1.6, 1.0], [-1.6, -2.7]].slice(0, NT);
        const flT = ctx.flota("tostadora", NT, { tamano: K * TT, lev: H0 * K, orden: 6, semilla: (p.semilla * 13 + np * 7) % 997,
          color: (i, vars) => vars[(i + Math.floor(hz(0, 41) * vars.length)) % vars.length] });
        const [UT, VT] = TOS[0], UTOL = UT - 1.15 * TT, HTOL = H0 + 3.0 * TT;     // la boca de la tolva de la primera
        // la plataforma: piso de lámina, cuatro patas, baranda atrás y a la izquierda, escalera bajando hacia la derecha (v−)
        const HPL = 1.45, PU0 = -4.65, PU1 = UT - 1.55 * TT, PV0 = VT - 0.75, PV1 = VT + 0.75;
        cj(solido, PU0, PU1, PV0, PV1, H0 + HPL - 0.08, H0 + HPL, cMetal, { tope: cMetal.clone().multiplyScalar(1.15) });
        for (const [uu, vv] of [[PU0 + 0.06, PV0 + 0.06], [PU0 + 0.06, PV1 - 0.06], [PU1 - 0.06, PV0 + 0.06], [PU1 - 0.06, PV1 - 0.06]])
          barra(solido, E(uu, vv, H0), E(uu, vv, H0 + HPL - 0.08), 0.045 * M, cOscuro);
        for (const [A, B] of [[[PU0 + 0.04, PV0 + 0.04], [PU0 + 0.04, PV1 - 0.04]], [[PU0 + 0.04, PV1 - 0.04], [PU1 - 0.04, PV1 - 0.04]]]) {
          for (const hh of [0.55, 1.05]) barra(solido, E(A[0], A[1], H0 + HPL + hh), E(B[0], B[1], H0 + HPL + hh), 0.025 * M, cOscuro);
          barra(solido, E(A[0], A[1], H0 + HPL), E(A[0], A[1], H0 + HPL + 1.05), 0.025 * M, cOscuro);
          barra(solido, E(B[0], B[1], H0 + HPL), E(B[0], B[1], H0 + HPL + 1.05), 0.025 * M, cOscuro);
        }
        const NE = 6, EU0 = PU0 + 0.15, EU1 = PU0 + 0.85;
        for (let k = 0; k < NE; k++) {
          const hh = H0 + HPL * (NE - k) / (NE + 1) - 0.05, v0 = PV0 - (k + 1) * 0.27;
          cj(solido, EU0, EU1, v0, v0 + 0.27, hh, hh + 0.05, cMetal.clone().multiplyScalar(1.08));
        }
        for (const uu of [EU0, EU1]) {
          barra(solido, E(uu, PV0, H0 + HPL), E(uu, PV0 - (NE + 1) * 0.27, H0), 0.03 * M, cOscuro);
          barra(solido, E(uu, PV0, H0 + HPL + 1.0), E(uu, PV0 - (NE + 1) * 0.27, H0 + 0.95), 0.022 * M, cOscuro);
        }

        // ================= la mesa de catación: redonda, con su giratorio, las tazas en el borde y dos frascos de grano
        const MU = 3.4, MV = -3.0, MR = 0.9, MH = H0 + 0.92;
        const mesa = malla.nueva();
        cil(mesa, MU, MV, H0, H0 + 0.04, 0.42, 14, cOscuro, cOscuro);
        cil(mesa, MU, MV, H0 + 0.04, MH - 0.06, 0.09, 8, cOscuro, null);
        cil(mesa, MU, MV, MH - 0.06, MH, MR, 24, cMesa.clone().multiplyScalar(0.8), cMesa);
        cil(mesa, MU, MV, MH, MH + 0.07, 0.42, 18, cMesa.clone().multiplyScalar(0.75), cMesa.clone().multiplyScalar(1.1));
        const NTZ = 10, tazas = [];
        for (let i = 0; i < NTZ; i++) {
          const a = TAU * i / NTZ + 0.2, tu = MU + 0.7 * Math.cos(a), tv = MV + 0.7 * Math.sin(a);
          cil(mesa, tu, tv, MH, MH + 0.1, 0.075, 10, cTaza, null);
          cil(mesa, tu, tv, MH + 0.07, MH + 0.09, 0.064, 10, cTaza.clone().multiplyScalar(0.85), cTostado.clone().lerp(lin(COL.tierra_media), 0.25));
          tazas.push([tu, tv, MH + 0.1]);
        }
        for (const [a, col] of [[0.6, cVerde], [2.6, cTostado.clone().multiplyScalar(1.4)]]) {
          const fu = MU + 0.22 * Math.cos(a), fv = MV + 0.22 * Math.sin(a);
          cil(mesa, fu, fv, MH + 0.07, MH + 0.25, 0.08, 10, col, col.clone().multiplyScalar(1.1));
          cil(mesa, fu, fv, MH + 0.25, MH + 0.29, 0.065, 10, cOscuro, cOscuro);
        }

        // ================= los estantes con bolsas de café tostado (lisas) contra la pared izquierda
        const est = malla.nueva(), EV0 = V1 - 0.6, EV1 = V1 - 0.08;
        for (const [a, b] of [[-1.2, 1.4], [1.7, 4.3], [6.0, 8.6]]) {
          for (const uu of [a + 0.03, b - 0.03]) for (const vv of [EV0 + 0.03, EV1 - 0.03]) barra(est, E(uu, vv, H0), E(uu, vv, H0 + 2.25), 0.03 * M, cOscuro);
          [0.12, 0.66, 1.2, 1.74, 2.22].forEach((hh, k) => {
            cj(est, a, b, EV0, EV1, H0 + hh, H0 + hh + 0.04, cMetal.clone().multiplyScalar(1.05));
            if (k === 4) return;
            const fam = bolsas[Math.floor(hz(Math.round(a * 10) + k * 7, 51) * bolsas.length)], hueco = hz(Math.round(a * 10) + k, 52);
            for (let s = a + 0.12, j = 0; s < b - 0.12; s += 0.19, j++) {
              if (hueco > 0.55 && s > a + (b - a) * hueco) break;    // algunas repisas a medio llenar
              const tono = fam.clone().multiplyScalar(0.88 + 0.18 * hz(j + k * 31 + Math.round(a * 10), 53)), bh = 0.3 + 0.03 * hz(j, 54);
              cj(est, s - 0.075, s + 0.075, EV0 + 0.12, EV0 + 0.26, H0 + hh + 0.04, H0 + hh + 0.04 + bh, tono, { tope: tono.clone().multiplyScalar(0.85) });
              cj(est, s - 0.07, s + 0.07, EV0 + 0.14, EV0 + 0.24, H0 + hh + 0.04 + bh, H0 + hh + 0.08 + bh, tono.clone().multiplyScalar(0.8));   // el doblez de arriba
            }
          });
        }

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
        sombraRect(-8.8, -6.25, 2.05, 5.35, 0.5); sombraRect(-5.9, -4.7, 2.5, 3.5, 0.4);
        sombraRect(BU - 0.55, BU + 0.55, BV - 0.55, BV + 0.55, 0.3);
        sombraRect(PU0, PU1, PV0, PV1, 0.5);
        sombraRect(MU - 0.6, MU + 0.6, MV - 0.6, MV + 0.6, 0.6);
        for (const [a, b] of [[-1.2, 1.4], [1.7, 4.3], [6.0, 8.6]]) sombraRect(a, b, EV0, EV1, 0.3);
        sombraRect(U0, U1, V1 - 0.02, V1, 0.7); sombraRect(U0, U0 + 0.02, V0, V1, 0.7);
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
        sinTraslado(juntas, malla.material({ desfase: 3 }), 3);
        sinTraslado(solido, malla.material({ desfase: 1 }), 3);
        sinTraslado(ladr, malla.material({ desfase: 2 }), 3);
        sinTraslado(vidrio, malla.material(), 3).material.uniforms.uBrillo.value = noche ? 1.6 : 1.25;
        sinTraslado(pantalla, malla.material(), 5).material.uniforms.uBrillo.value = 1.3;
        sinTraslado(luzA, malla.material({ aditivo: true, desfase: 4 }), 4);
        sinTraslado(haz, malla.material({ aditivo: true }), 8);
        const matSacos = malla.material(); sinTraslado(sacos, matSacos, 5);
        const matGrano = malla.material(); sinTraslado(grano, matGrano, 5);
        sinTraslado(mesa, malla.material(), 5);
        sinTraslado(est, malla.material(), 5);

        // ================= el saco que se vacía en la tolva (una malla que se coloca por t) y el chorro de grano verde
        const sacoM = malla.nueva(); gema(sacoM, almohada, [0, 0, 0], 0.46, 0.14, 0.29, 0, cYute, 0.35);
        const matSaco = malla.material(), gSaco = new THREE.Group(), mSaco = new THREE.Mesh(malla.geometria(sacoM), matSaco);
        mSaco.frustumCulled = false; mSaco.renderOrder = 6; gSaco.add(mSaco); gSaco.rotation.y = r; scene.add(gSaco);
        const chorroA = malla.nueva(); cil(chorroA, 0, 0, 0, 1, 0.055, 8, cVerde, null);
        // el chorro es un cilindro unitario armado en E(0, 0, ·): se recentra en el origen para escalarlo
        const gChA = malla.geometria(chorroA); { const o = E(0, 0, 0); gChA.translate(-o[0], -o[1], -o[2]); gChA.scale(1 / M, 1 / M, 1 / M); }
        const matChorro = malla.material(), mChorro = new THREE.Mesh(gChA, matChorro); mChorro.frustumCulled = false; mChorro.renderOrder = 6; scene.add(mChorro);
        const gotaM = malla.nueva(); gema(gotaM, oct, [0, 0, 0], 0.045, 0.03, 0.035, 0, cVerde, 0.4);
        const gGota = malla.geometria(gotaM), gotas = [], NG = 14;
        for (let j = 0; j < NG; j++) { const m = new THREE.Mesh(gGota, matChorro); m.frustumCulled = false; m.renderOrder = 6; scene.add(m); gotas.push({ m, f0: j / NG + 0.02 * hz(j, 61), dv: (hz(j, 62) - 0.5) * 0.09, rot: hz(j, 63) * TAU }); }
        // el grano en la tolva: un cuadro (la tolva es una pirámide de lados alineados) que sube y baja con su nivel
        const nivelM = malla.nueva(); { const l = sombra(0, 1, 0), q = 0; for (const [a, b] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { nivelM.pos.push(a, 0, b); const cc = cVerde.clone().multiplyScalar(0.9); nivelM.col.push(cc.r * l, cc.g * l, cc.b * l); } nivelM.idx.push(q, q + 1, q + 2, q, q + 2, q + 3); }
        const mNivel = new THREE.Mesh(malla.geometria(nivelM), matGrano); mNivel.frustumCulled = false; mNivel.renderOrder = 6; mNivel.rotation.y = r; scene.add(mNivel);
        const PS = 7.0, F0 = hz(1, 64), TILT = 0.95, LH = 0.46;
        const s3 = (x) => { const v = clamp(x, 0, 1); return v * v * (3 - 2 * v); };
        const Pt = [UTOL - Math.cos(TILT) * LH * 0.9, VT, HTOL + 0.12 + Math.sin(TILT) * LH * 0.9 + 0.1];
        const Pc = [PU1 - 0.2, VT, H0 + HPL + 1.32];
        const carga = (t) => {      // fase del ciclo de carga: posición, inclinación, aplastado, escala y el chorro
          const f = (((t / PS + F0) % 1) + 1) % 1;
          let u, h, tilt = 0, aplasta = 1, k = 1, chorro = 0;
          if (f < 0.1) { k = s3(f / 0.1); u = Pc[0]; h = Pc[2]; }
          else if (f < 0.3) { const q = s3((f - 0.1) / 0.2); u = Pc[0] + (Pt[0] - Pc[0]) * q; h = Pc[2] + (Pt[2] - Pc[2]) * q + 0.15 * Math.sin(Math.PI * q); tilt = TILT * q; }
          else if (f < 0.76) { const q = (f - 0.3) / 0.46; u = Pt[0]; h = Pt[2] - 0.05 * q; tilt = TILT + 0.3 * q; aplasta = 1 - 0.72 * s3(q * 1.1); chorro = s3(q / 0.08) * (1 - s3((q - 0.9) / 0.1)); }
          else if (f < 0.9) { const q = s3((f - 0.76) / 0.14); u = Pt[0] + (Pc[0] - Pt[0]) * q; h = Pt[2] - 0.05 + (Pc[2] - Pt[2] + 0.05) * q; tilt = (TILT + 0.3) * (1 - q); aplasta = 0.28; k = 1 - s3((f - 0.83) / 0.07); }
          else { k = 0; u = Pc[0]; h = Pc[2]; }
          // el nivel de la tolva: sube mientras cae el chorro, baja el resto del ciclo (el tambor lo traga)
          const llena = f < 0.3 ? 0.35 * (1 - (f + 0.1) / 0.4) + 0.05 : f < 0.76 ? 0.05 + 0.85 * s3((f - 0.3) / 0.46) : 0.9 - 0.75 * ((f - 0.76) / 0.34);
          return { f, u, h, tilt, aplasta, k, chorro, llena };
        };

        // ================= el polvo en los haces, la nube de la tolva y el vapor de las tazas: puntos que se calculan de t
        const NPOL = 70, NNUBE = 16, NVAP = NTZ * 2, NPT = NPOL + NNUBE + NVAP;
        const gP = new THREE.BufferGeometry(), posP = new Float32Array(NPT * 3), aP = new Float32Array(NPT * 2);
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 2));
        const cPolvo = cLuz.clone().lerp(lin(COL.costa), 0.3), cVapor = lin(COL.costa).lerp(tonos.secundario, 0.4);
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: cPolvo }, cB: { value: cVapor }, cC: { value: cVerde.clone().lerp(lin(COL.tierra_alta), 0.5) } },
          transparent: true, depthWrite: false,
          vertexShader: "attribute vec2 aK; uniform float uPx, uTam; varying vec2 vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " float m = aK.y < 0.5 ? 0.035 : (aK.y < 1.5 ? 0.12 : 0.09); gl_PointSize = aK.x > 0.0 ? clamp(m * uTam * uPx / max(1e-3, -mv.z), 1.5, 26.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA, cB, cC; varying vec2 vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = vK.y < 0.5 ? cA : (vK.y < 1.5 ? cB : cC); vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK.x * (vK.y < 0.5 ? exp(-r * r * 3.0) : (1.0 - smoothstep(0.2, 1.0, r)) * 0.55); gl_FragColor = vec4(s, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);
        const polvo = (t) => {
          let j = 0;
          for (let i = 0; i < NPOL; i++, j++) {            // dentro de un haz: deriva lenta y un parpadeo (sale de la luz)
            const H = haces[i % haces.length], lam = hz(i, 71), vv = H.a + (H.b - H.a) * hz(i, 72), hh = H.s + (H.tt - H.s) * hz(i, 73);
            const [pu, pv] = pie(vv, hh), ph = TAU * hz(i, 74), per = 9 + 6 * hz(i, 75);
            const u = U0 + (pu - U0) * lam + 0.25 * Math.sin(TAU * t / per + ph), v = vv + (pv - vv) * lam + 0.2 * Math.cos(TAU * t / (per * 1.3) + ph);
            const h = hh + (H0 - hh) * lam + 0.18 * Math.sin(TAU * t / (per * 0.8) + ph * 2);
            const P = E(u, v, h); posP.set(P, j * 3); aP[j * 2] = 0.65 * (0.5 + 0.5 * Math.sin(TAU * t / (3 + 2 * hz(i, 76)) + ph)); aP[j * 2 + 1] = 0;
          }
          const C = carga(t);
          for (let i = 0; i < NNUBE; i++, j++) {           // la nube de polvo del grano en la boca de la tolva, mientras cae
            const q = (((t / 1.6 + i / NNUBE) % 1) + 1) % 1, a = TAU * hz(i, 77);
            const P = E(UTOL + (0.15 + 0.5 * q) * Math.cos(a), VT + (0.15 + 0.5 * q) * Math.sin(a), HTOL + 0.05 + 0.6 * q);
            posP.set(P, j * 3); aP[j * 2] = C.chorro * Math.sin(Math.PI * q) * 0.75; aP[j * 2 + 1] = 2;
          }
          for (let i = 0; i < NVAP; i++, j++) {            // el vapor de las tazas: sube, crece y se apaga
            const tz = tazas[i % NTZ], q = (((t / 2.8 + hz(i, 78) + (i >= NTZ ? 0.5 : 0)) % 1) + 1) % 1;
            const P = E(tz[0] + 0.04 * Math.sin(TAU * (q + hz(i, 79))), tz[1] + 0.04 * Math.cos(TAU * q * 1.3), tz[2] + 0.04 + 0.42 * q);
            posP.set(P, j * 3); aP[j * 2] = Math.sin(Math.PI * q) * 0.8; aP[j * 2 + 1] = 1;
          }
          gP.attributes.position.needsUpdate = true; gP.attributes.aK.needsUpdate = true;
        };

        // ================= la gente: quien carga (en la plataforma), quien revisa la bandeja y quien cata
        const NP = clamp(p.personas | 0, 0, 3), PG = 1.1;
        const camisas = dia ? [lin(COL.mar).multiplyScalar(0.72), tonos.mal.clone(), tonos.bien.clone()]
          : noche ? [lin(COL.costa), tonos.mal.clone(), tonos.secundario.clone().multiplyScalar(0.85)]
          : [lin(COL.mar), tonos.mal.clone(), tonos.bien.clone()];
        const flC = NP >= 1 ? ctx.flota("persona", 1, { tamano: K * PG, lev: (H0 + HPL) * K, orden: 6, semilla: p.semilla % 991, color: () => camisas[0],
          pose: { nombre: "cargar", periodo: PS, fase: F0, saco: false } }) : null;   // la pose cargar con el ciclo del saco de aquí (el saco lo dibuja la pieza)
        const flG = NP >= 2 ? ctx.flota("persona", NP - 1, { tamano: K * PG, lev: H0 * K, orden: 6, semilla: (p.semilla * 5 + 3) % 991, color: (i) => camisas[1 + i],
          pose: (i) => (i === 0 ? "atender" : "sorber") }) : null;   // quien revisa la bandeja atiende; quien cata sorbe
        const BAND = [UT + 0.85 * TT, VT];
        const gente = [[UT + 0.75 * TT, VT + 1.25, 0, -1, 0.15], [MU - 1.25, MV - 0.45, 1, 0.35, 0.1]];
        return { id: p.id, K, flT, flC, flG, TOS, ux, uy, W, E, gente, NP, BAND, PU1, VT, H0, HPL,
          gSaco, mSaco, mChorro, gotas, mNivel, carga, polvo, matSacos, matGrano, matSaco, matChorro, UTOL, HTOL, TT, M, LH, matP, mats: [matSacos, matGrano, matSaco, matChorro] };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) m.uniforms.uBrillo.value = 1 + 0.45 * k;
        s.flT.mesh.material.uniforms.uBrillo.value = 1 + 0.3 * k;
        // las tostadoras (su pose gira el tambor, el brazo y el humo)
        s.TOS.forEach(([u, v], i) => { const [x, y] = s.W(u, v); s.flT.poner(i, x, y, s.ux, s.uy, 1, 0); });
        s.flT.listo();
        // el saco y el chorro: solo si hay quien carga
        const C = s.carga(t), vis = s.NP >= 1;
        const P = s.E(C.u, s.VT, C.h);
        s.gSaco.position.set(P[0], P[1], P[2]);
        s.mSaco.rotation.z = -C.tilt;
        const kk = vis ? C.k : 0;
        s.mSaco.scale.set(kk * (0.82 + 0.18 * C.aplasta), kk * C.aplasta, kk * (0.9 + 0.1 * C.aplasta));
        // la boca del saco (la punta de adelante) y la caída hasta el grano de la tolva
        const lh = s.LH * (0.82 + 0.18 * C.aplasta), nu = C.u + Math.cos(C.tilt) * lh, nh = C.h - Math.sin(C.tilt) * lh;
        const hNivel = s.H0 + (2.45 + 0.5 * C.llena) * s.TT, ch = vis ? C.chorro : 0;
        const A = s.E(nu, s.VT, nh), Bp = s.E(nu, s.VT, hNivel);
        s.mChorro.position.set(Bp[0], Bp[1], Bp[2]);
        s.mChorro.scale.set(s.M * ch, Math.max(1e-4, A[1] - Bp[1]) * (ch > 0 ? 1 : 0), s.M * ch);
        s.gotas.forEach((g, j) => {
          const q = (((t / 0.55 + g.f0) % 1) + 1) % 1, G = s.E(nu + 0.05 * q, s.VT + g.dv, nh + (hNivel - nh) * q);
          g.m.position.set(G[0], G[1], G[2]); g.m.rotation.set(0, g.rot + t * 5, 0.5); g.m.scale.setScalar(ch > 0.2 ? 1 : 0);
        });
        const N = s.E(s.UTOL, s.VT, hNivel), lado = (0.12 + (hNivel - s.H0 - 2.4 * s.TT) / (0.6 * s.TT) * 0.38) * 0.707 * 0.93 * s.TT * s.M;
        s.mNivel.position.set(N[0], N[1], N[2]); s.mNivel.scale.set(lado, 1, lado);
        // la gente: quien carga sube el saco a la tolva (pose cargar, en fase con el saco); quien revisa la bandeja atiende, quien cata sorbe
        if (s.flC) { const [x, y] = s.W(s.PU1 - 0.62, s.VT + 0.12); s.flC.poner(0, x, y, s.ux, s.uy, 1, 0, 0); s.flC.listo(); }
        if (s.flG) {
          for (let i = 0; i < s.NP - 1; i++) {
            const [u, v] = s.gente[i], [x, y] = s.W(u, v);
            const [tx, ty] = i === 0 ? s.W(s.BAND[0], s.BAND[1]) : s.W(u + 1, v + 0.2);
            const dx = tx - x, dy = ty - y, l = Math.hypot(dx, dy) || 1;
            s.flG.poner(i, x, y, dx / l, dy / l, 1, 0, 0);
          }
          s.flG.listo();
        }
        // el tamaño de los puntos: px por unidad a 1 unidad
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.polvo(t);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
