// Pieza «trebol» (ficha: trebol.json; reglas: scripts/maqueta_tipos/trebol.py): el nudo de El Trébol sobre su traza de
// OpenStreetMap (set de ciudad) y con volumen. Python resuelve las vías del nudo (cosidas y recortadas a RADIO m del
// centro), los cruces a desnivel, la altura ILUSTRATIVA de cada muestra (tableros sobre pilas, rampas que bajan al suelo),
// los puentes, las callecitas, las casas y la nave. Aquí solo se dibuja, según la época:
//   callecitas · sin nudo: callecitas genéricas por las calzadas que convergen, casas bajas, una nave industrial genérica
//                (dientes de sierra y chimenea que humea) y gente que camina;
//   obra       · tierra removida a lo largo de las vías, rampas de tierra, pilas a medio hacer con sus varillas, tableros
//                por tramos, cimbras genéricas (postes y largueros de madera) y obreros sin empresa ni rótulo;
//   1959       · tableros nuevos (concreto claro) sin los lazos («construidos después»), pocos carros;
//   hoy        · asfalto con rayas, barandas, postes de luz y carros. Sin rótulos de destino.
// Solo lo verificado: tableros con asfalto sobre el nudo sin nombre por tablero; callecitas y una fábrica genérica antes de
// la obra (no se afirma tierra: tono neutro); obreros genéricos. Genérico y sin afirmar: cuántos tableros, niveles y lazos
// (salen de la traza), cimbras, anchos, carros (ilustrativos), la forma, el tamaño y el lugar de la nave. Sin texto.
// CON VIDA (puro de t): carros que corren por las vías y suben a los tableros, obreros con su pose, la gente que camina,
// el humo de la chimenea. De noche: postes de luz con su charco, ventanas de la nave, focos de obra.
// «resaltar» la pieza enciende el nudo; con «<id>.puentes», los tableros (sin decir cuál es cuál); con «<id>.fabrica», la nave.
// Con un «transformar» sobre ella (ctx.cuadro.epoca[id].hunde), las casas, la nave y la gente de callecitas que caen dentro de
// la obra se hunden en el turno de lo viejo del evento: la voz dice «tres puentes» y no queda una casa encima de un tablero.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  MAQ.PIEZAS.trebol = {
    orden: 9,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, dia = !!ES.dia;
      const alt = (x, y) => ctx.altura(x, y);
      // ---- los tonos (todos del estilo)
      const cAsf = tonos.asfalto.clone().multiplyScalar(dia ? 1.0 : 1.12);
      const cConc = tonos.pavimento.clone().lerp(lin(COL.costa), 0.4).multiplyScalar(dia ? 1.05 : 1.2);
      const cConcN = cConc.clone().lerp(lin(COL.costa), 0.25).multiplyScalar(1.06);            // concreto nuevo (1959)
      const cConcO = cConc.clone().multiplyScalar(0.72);
      const cTierra = lin(COL.tierra_media).lerp(tonos.pavimento, 0.15).multiplyScalar(dia ? 0.95 : 1.1);
      const cTierraO = cTierra.clone().multiplyScalar(0.78);
      const cCalle = tonos.pavimento.clone().lerp(lin(COL.tierra_media), 0.4).multiplyScalar(dia ? 1.0 : 1.1);
      const cPasto = tonos.verde.clone().lerp(tonos.bien, 0.25).multiplyScalar(dia ? 0.9 : 1.1);
      const cPintura = lin(COL.costa).lerp(tonos.pavimento, 0.15);
      const cNegro = tonos.linea.clone().lerp(tonos.asfalto, 0.3).multiplyScalar(0.85);
      const cMadera = lin(COL.tierra_media).lerp(lin(COL.tierra_alta), 0.35).multiplyScalar(0.85);
      const cMuro = tonos.pavimento.clone().lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(dia ? 1.0 : 1.15);
      const cTecho = tonos.pavimento.clone().lerp(lin(COL.costa), 0.15).multiplyScalar(0.9);
      const cVidrio = noche ? lin(COL.luces || COL.luz).multiplyScalar(0.9) : tonos.asfalto.clone().lerp(lin(COL.mar), 0.3).multiplyScalar(0.8);
      const cLadrillo = lin(COL.tierra_media).lerp(tonos.mal, 0.25).multiplyScalar(0.8);
      const cHumo = tonos.pavimento.clone().lerp(lin(COL.costa), 0.6).multiplyScalar(dia ? 1.05 : 0.7);
      const cLuz = lin(COL.luces || COL.luz), cAc = lin(COL.acento);

      return piezas.map((p, np) => {
        const M = metros(1), sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const E = (x, y, z) => [x, z, -y];
        const ep = p.epoca, OBRA = ep === "obra", CALLE = ep === "callecitas", HOY = ep === "hoy", N59 = ep === "1959";
        const cara = (acc, P, col, ref, f = 1) => {
          const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = sombra(nx, ny, nz) * f, q = acc.pos.length / 3;
          for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        // una caja orientada (u a lo largo de `ang`, v a su izquierda), alturas en m sobre z0 (escena)
        const caja = (acc, cx, cy, ang, a0, a1, b0, b1, h0, h1, col, op = {}) => {
          const ca = Math.cos(ang), sa = Math.sin(ang), z0 = op.z0 !== undefined ? op.z0 : alt(cx, cy);
          const P = (u, v, h) => E(cx + (u * ca - v * sa) * M, cy + (u * sa + v * ca) * M, z0 + h * M);
          const C = P((a0 + a1) / 2, (b0 + b1) / 2, (h0 + h1) / 2);
          [[[a0, b0, h1], [a1, b0, h1], [a1, b1, h1], [a0, b1, h1]], [[a0, b0, h0], [a1, b0, h0], [a1, b0, h1], [a0, b0, h1]],
            [[a0, b1, h0], [a1, b1, h0], [a1, b1, h1], [a0, b1, h1]], [[a0, b0, h0], [a0, b1, h0], [a0, b1, h1], [a0, b0, h1]],
            [[a1, b0, h0], [a1, b1, h0], [a1, b1, h1], [a1, b0, h1]]].forEach((q, k) => {
            const V = q.map((a) => P(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
            cara(acc, V, k === 0 && op.tope ? op.tope : (op.lados ? op.lados[k] || col : col), m);
          });
        };
        const cono = (acc, x, y, z0, h0, h1, r0, r1, seg, col, tapa) => {
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
            const Q = (r, a, h) => E(x + r * Math.cos(a) * M, y + r * Math.sin(a) * M, z0 + h * M);
            const P = [Q(r0, a0, h0), Q(r0, a1, h0), Q(r1, a1, h1), Q(r1, a0, h1)];
            cara(acc, P, col, [Math.cos(am), (r0 - r1) * 0.5, -Math.sin(am)]);
            if (tapa) { const T0 = Q(0, 0, h1); cara(acc, [P[3], P[2], T0, T0], tapa, [0, 1, 0]); }
          }
        };
        const ico = new THREE.IcosahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
        const bola = (acc, x, y, z, ru, rh, col, k) => {
          const c = new THREE.Color();
          for (let i = 0; i < ico.length; i += 9) {
            const vs = [];
            for (let j = 0; j < 9; j += 3) {
              const w = 1 + 0.14 * (hz(k * 131 + ((i + j) % 97), 5) - 0.5);
              vs.push([x + ico[i + j] * ru * w * M, z + Math.max(-0.2, ico[i + j + 1]) * rh * w * M, -(y - ico[i + j + 2] * ru * w * M)]);
            }
            const e1 = [vs[1][0] - vs[0][0], vs[1][1] - vs[0][1], vs[1][2] - vs[0][2]], e2 = [vs[2][0] - vs[0][0], vs[2][1] - vs[0][1], vs[2][2] - vs[0][2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const cx = (vs[0][0] + vs[1][0] + vs[2][0]) / 3 - x, cy = (vs[0][1] + vs[1][1] + vs[2][1]) / 3 - z, cz = (vs[0][2] + vs[1][2] + vs[2][2]) / 3 + y;
            if (nx * cx + ny * cy + nz * cz < 0) { nx = -nx; ny = -ny; nz = -nz; }
            const n = Math.hypot(nx, ny, nz) || 1;
            c.copy(col).multiplyScalar(sombra(nx / n, ny / n, nz / n) * (0.88 + 0.22 * hz(k * 977 + i, 6)));
            const q = acc.pos.length / 3;
            for (const X of vs) { acc.pos.push(X[0], X[1], X[2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };

        // ================= las vías: muestras, normales, alturas (m) y ancho
        const V = p.vias, Z = p.z, NV = V.length;
        const ancho = V.map((c, w) => {
          const L = c.reduce((a, q, i) => a + (i ? Math.hypot(q[0] - c[i - 1][0], q[1] - c[i - 1][1]) : 0), 0);
          return p.lazo[w] ? 6.0 : p.clases[w] === "primaria" ? 8.5 : L > 300 ? 10.5 : L > 160 ? 8.0 : 6.8;
        });
        const usar = V.map((c, w) => !(N59 && p.lazo[w]));
        const marco = V.map((c) => c.map((q, i) => {
          const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
          return { x: q[0], y: q[1], tx: (b[0] - a[0]) / L, ty: (b[1] - a[1]) / L, nx: -(b[1] - a[1]) / L, ny: (b[0] - a[0]) / L, g: alt(q[0], q[1]) };
        }));
        const sAc = V.map((c) => { const s = [0]; for (let i = 1; i < c.length; i++) s.push(s[i - 1] + Math.hypot(c[i][0] - c[i - 1][0], c[i][1] - c[i - 1][1])); return s; });
        const HT = 4.2, LOSA = 1.3;
        const vias = malla.nueva(), estr = malla.nueva(), tabl = malla.nueva(), obraA = malla.nueva(), mueble = malla.nueva();
        const focos = malla.nueva(), luzA = malla.nueva(), nave = malla.nueva(), vent = malla.nueva(), enc = malla.nueva();
        // la cinta de una vía con su altura: de i0 a i1, desplazada `d` y de ancho `w`, a `lev` m sobre su altura
        const cintaZ = (acc, w, i0, i1, ww, lev, col, fz, tono) => {
          const F = marco[w], base = acc.pos.length / 3; let n = 0;
          for (let i = i0; i <= i1; i++) {
            const f = F[i], h = (fz ? fz(i) : Z[w][i]) + lev;
            const cc = tono ? tono(i) : col;
            for (const s of [1, -1]) { acc.pos.push(...E(f.x + f.nx * ww / 2 * s * M, f.y + f.ny * ww / 2 * s * M, f.g + h * M)); acc.col.push(cc.r, cc.g, cc.b); }
            if (n) { const q = base + 2 * n; acc.idx.push(q - 2, q - 1, q, q - 1, q + 1, q); }
            n++;
          }
        };
        // los costados de un tramo: del borde (z + top) hasta abajo (bot(i): m sobre el suelo)
        const costados = (acc, w, i0, i1, ww, top, bot, col) => {
          const F = marco[w];
          for (let i = i0; i < i1; i++) for (const s of [1, -1]) {
            const a = F[i], b = F[i + 1], ha = Z[w][i] + top, hb = Z[w][i + 1] + top, ba = bot(i), bb = bot(i + 1);
            if (ha - ba < 0.05 && hb - bb < 0.05) continue;
            const P = (f, h) => E(f.x + f.nx * ww / 2 * s * M, f.y + f.ny * ww / 2 * s * M, f.g + h * M);
            cara(acc, [P(a, ba), P(b, bb), P(b, hb), P(a, ha)], col, [a.nx * s, 0, -a.ny * s]);
          }
        };
        const tramos = (w, f) => {        // los tramos [i0, i1] de una vía donde f(i) es cierto
          const out = []; let i0 = -1;
          for (let i = 0; i < V[w].length; i++) { if (f(i)) { if (i0 < 0) i0 = i; } else if (i0 >= 0) { out.push([i0, i - 1]); i0 = -1; } }
          if (i0 >= 0) out.push([i0, V[w].length - 1]);
          return out.map(([a, b]) => [Math.max(0, a - 1), Math.min(V[w].length - 1, b + 1)]);
        };
        // ¿hay una vía de abajo en (x, y)? (para no plantar una pila en el asfalto de otra)
        const sobreVia = (x, y, w0) => {
          for (let w = 0; w < NV; w++) { if (w === w0 || !usar[w]) continue;
            const c = V[w]; for (let i = 0; i < c.length; i++) if (Z[w][i] < 2 && Math.hypot(c[i][0] - x, c[i][1] - y) < ancho[w] / 2 + 3) return true; }
          return false;
        };
        const esPuente = V.map(() => []);
        for (const [w, i0, i1] of p.puentes) for (let i = i0; i <= i1; i++) esPuente[w][i] = true;

        const pilas = [], lamparas = [], ejesCarro = [];
        // ================= el nudo (obra, 1959, hoy)
        if (!CALLE) {
          for (let w = 0; w < NV; w++) {
            if (!usar[w]) continue;
            const ww = ancho[w], c = V[w], last = c.length - 1;
            if (OBRA) {
              // la tierra removida: una franja ancha al ras, con su tono que varía
              cintaZ(obraA, w, 0, last, ww + 16, 0.16, null, () => 0, (i) => cTierra.clone().multiplyScalar(0.86 + 0.24 * hz(w * 300 + i, 1)));
            }
            const lev = 0.32 + 0.01 * (w % 5);
            // la calzada: asfalto (1959, hoy); en obra, la terracería donde aún no hay tablero
            const pu = p.puentes.find((q) => q[0] === w);
            const enObraSinTablero = (i) => OBRA && !!esPuente[w][i] && i - pu[1] > (pu[2] - pu[1]) * (0.4 + 0.3 * hz(w, 2));
            for (const [a0, b0] of tramos(w, (i) => !enObraSinTablero(i))) cintaZ(vias, w, a0, b0, ww, lev, null, null, (i) => (OBRA ? (esPuente[w][i] ? cConcN : cTierraO.clone().multiplyScalar(1.05 + 0.15 * hz(w * 77 + i, 3)))
              : (N59 ? cAsf.clone().lerp(tonos.pavimento, 0.12) : cAsf).clone().multiplyScalar(0.96 + 0.06 * hz(w * 77 + i, 3))));
            // los costados: rampas macizas (muro hasta el suelo) y tableros (la losa)
            for (const [a, b] of tramos(w, (i) => Z[w][i] > 0.3 && !enObraSinTablero(i))) {
              const colR = OBRA ? cTierraO : N59 ? cConcN : cConc;
              costados(estr, w, a, b, ww, lev, (i) => (Z[w][i] >= HT ? Z[w][i] + lev - LOSA : 0), colR);
              for (const [a2, b2] of tramos(w, (i) => Z[w][i] >= HT && i >= a && i <= b && !enObraSinTablero(i)))
                cintaZ(estr, w, a2, b2, ww, lev - LOSA, cConcO);               // la cara de abajo de la losa
              if (!OBRA) {                                                     // barandas: un pretil a cada lado
                for (const s of [1, -1]) {
                  const F = marco[w];
                  for (let i = a; i < b; i++) {
                    const P = (f, dd, h) => E(f.x + f.nx * (ww / 2 - dd) * s * M, f.y + f.ny * (ww / 2 - dd) * s * M, f.g + h * M);
                    const A = F[i], B = F[i + 1], za = Z[w][i] + lev, zb = Z[w][i + 1] + lev, hp = N59 ? 0.8 : 1.0;
                    cara(estr, [P(A, 0, za), P(B, 0, zb), P(B, 0, zb + hp), P(A, 0, za + hp)], N59 ? cConcN : cConc, [A.nx * s, 0, -A.ny * s]);
                    cara(estr, [P(A, 0.3, za), P(B, 0.3, zb), P(B, 0.3, zb + hp), P(A, 0.3, za + hp)], cConcO.clone().multiplyScalar(1.2), [-A.nx * s, 0, A.ny * s]);
                    cara(estr, [P(A, 0, za + hp), P(B, 0, zb + hp), P(B, 0.3, zb + hp), P(A, 0.3, za + hp)], N59 ? cConcN : cConc, [0, 1, 0]);
                    if (HOY && i % 2 === 0) {                                   // la baranda metálica sobre el pretil
                      cara(estr, [P(A, 0.15, za + hp), P(B, 0.15, zb + hp), P(B, 0.15, zb + hp + 0.35), P(A, 0.15, za + hp + 0.35)], cNegro.clone().lerp(cConc, 0.4), [A.nx * s, 0, -A.ny * s]);
                    }
                  }
                }
              }
            }
            // las pilas bajo los tableros, cada ≈ 22 m, con su viga cabezal
            let sig = 8;
            for (let i = 0; i < c.length; i++) {
              if (sAc[w][i] < sig || Z[w][i] < HT) continue;
              sig = sAc[w][i] + 22;
              const f = marco[w][i];
              if (sobreVia(f.x, f.y, w)) continue;
              const top = Z[w][i] + lev - LOSA, sinT = enObraSinTablero(i);
              const hp = sinT ? top * (0.4 + 0.45 * hz(w * 31 + i, 4)) : top;
              const ang = Math.atan2(f.ty, f.tx), lado = Math.min(ww * 0.3, 2.6);
              for (const s of (ww > 7.5 ? [1, -1] : [0])) {
                const x = f.x + f.nx * lado * s, y = f.y + f.ny * lado * s;
                cono(estr, x, y, f.g, 0, 0.35, 0.95, 0.95, 14, cConcO, null);
                cono(estr, x, y, f.g, 0.35, hp - (sinT ? 0 : 0.9), 0.62, 0.55, 14, OBRA ? cConc.clone().multiplyScalar(0.92) : N59 ? cConcN : cConc, sinT ? cConcO : null);
                if (sinT) for (let k = 0; k < 4; k++) {                       // las varillas que asoman
                  const a = TAU * k / 4 + 0.6, rx = x + Math.cos(a) * 0.32, ry = y + Math.sin(a) * 0.32;
                  cono(estr, rx, ry, f.g, hp, hp + 1.6, 0.04, 0.03, 4, cNegro, null);
                }
              }
              if (!sinT) caja(estr, f.x, f.y, ang, -0.6, 0.6, -ww * 0.42, ww * 0.42, top - 0.95, top, cConcO.clone().multiplyScalar(1.1), { z0: f.g });
              pilas.push([f.x, f.y, ang, w, i, sinT]);
            }
            // la cimbra (obra): postes y largueros de madera bajo el tramo sin tablero (genérica, sin rótulo)
            if (OBRA) for (const [a, b] of tramos(w, enObraSinTablero)) {
              for (let i = a; i <= b; i++) {
                const f = marco[w][i], top = Z[w][i] + lev - 0.2, ang = Math.atan2(f.ty, f.tx);
                for (const v of [-ww * 0.4, 0, ww * 0.4]) {
                  const x = f.x + f.nx * v, y = f.y + f.ny * v;
                  caja(estr, x, y, ang, -0.12, 0.12, -0.12, 0.12, 0, top, cMadera.clone().multiplyScalar(0.9 + 0.2 * hz(i * 7 + v, 5)), { z0: f.g });
                }
                for (let h = 2; h < top; h += 2.4) caja(estr, f.x, f.y, ang, -0.07, 0.07, -ww * 0.44, ww * 0.44, h - 0.1, h + 0.1, cMadera, { z0: f.g });
                if (i < b) caja(estr, f.x, f.y, ang, 0, sAc[w][i + 1] - sAc[w][i], -ww * 0.44, ww * 0.44, top - 0.15, top, cMadera.clone().multiplyScalar(1.1), { z0: f.g });
              }
            }
            // los postes de luz (1959 y hoy), cada ≈ 40 m en un borde
            if (!OBRA && !p.lazo[w]) {
              let sl = 15;
              for (let i = 0; i < c.length; i++) {
                if (sAc[w][i] < sl) continue;
                sl = sAc[w][i] + 62;
                const f = marco[w][i], s = (w % 2 ? 1 : -1), d = ww / 2 - 0.4, x = f.x + f.nx * d * s, y = f.y + f.ny * d * s;
                const z0 = f.g + (Z[w][i] + lev + (Z[w][i] > 0.3 ? 0.5 : 0)) * M, H = N59 ? 8 : 10;
                cono(mueble, x, y, z0, 0, H, 0.11, 0.08, 8, cNegro, null);
                const ax = -f.nx * s, ay = -f.ny * s;                        // el brazo, hacia la vía
                caja(mueble, x + ax * 0.9, y + ay * 0.9, Math.atan2(ay, ax), -0.9, 0.9, -0.06, 0.06, H - 0.1, H + 0.05, cNegro, { z0 });
                caja(focos, x + ax * 1.7, y + ay * 1.7, Math.atan2(ay, ax), -0.35, 0.35, -0.16, 0.16, H - 0.25, H, noche ? cLuz : cNegro.clone().lerp(cConc, 0.5), { z0 });
                lamparas.push([x + ax * 1.7, y + ay * 1.7, f.g + (Z[w][i] + lev) * M]);
              }
            }
            // las rayas (hoy): orillas continuas y, si es ancha, una raya de carril
            if (HOY) {
              const F = marco[w], A0 = ctx.CFG.ruta.ancho, rayas = [];
              const pts = (d, lv) => F.map((f, i) => ({ v: new THREE.Vector3(f.x + f.nx * d * M, f.g + (Z[w][i] + lev + lv) * M, -(f.y + f.ny * d * M)), s: sAc[w][i], salto: i === last }));
              for (const s of [1, -1]) rayas.push(ctx.cinta(pts(s * (ww / 2 - 0.5), 0.06), cPintura, A0 * 0.45, 0.8, 6));
              if (ww >= 8) rayas.push(ctx.cinta(pts(0, 0.06), cPintura, A0 * 0.35, 0.65, 6, { raya: 9 }));
              if (w === 0) ctx.linea(p.id, rayas[0]);
            }
            if (!OBRA && !p.lazo[w] && sAc[w][last] > 70) ejesCarro.push(w);
            // el resaltado del nudo: una banda en el acento sobre cada vía (apagada hasta su resaltar)
            cintaZ(enc, w, 0, last, ww + 1.2, lev + 0.25, cAc);
          }
          // en obra: montículos de tierra y pilas de tablones junto a las pilas
          if (OBRA) pilas.forEach(([x, y, ang, w], k) => {
            if (hz(k, 7) < 0.55) bola(obraA, x + 9 * Math.cos(ang + 1.4), y + 9 * Math.sin(ang + 1.4), alt(x, y), 3 + 2 * hz(k, 8), 1.6 + hz(k, 9), cTierra.clone().multiplyScalar(0.9 + 0.2 * hz(k, 10)), 600 + k);
            else for (let j = 0; j < 4; j++) caja(obraA, x - 7 * Math.cos(ang + 1.4), y - 7 * Math.sin(ang + 1.4), ang + 0.05 * j, -2.2, 2.2, -0.5, 0.5, j * 0.2, j * 0.2 + 0.18, cMadera.clone().multiplyScalar(0.9 + 0.1 * j));
          });
          // de noche, los charcos de luz (1959 y hoy) y focos de obra
          if (noche) {
            const charco = (x, y, z, rr, col) => {
              const n = 16, q = luzA.pos.length / 3;
              luzA.pos.push(...E(x, y, z)); luzA.col.push(col.r, col.g, col.b);
              for (const [f, a] of [[0.5, 0.55], [1, 0]]) for (let i = 0; i < n; i++) { const t0 = TAU * i / n; luzA.pos.push(...E(x + rr * f * Math.cos(t0) * M, y + rr * f * Math.sin(t0) * M, z)); luzA.col.push(col.r * a, col.g * a, col.b * a); }
              for (let i = 0; i < n; i++) { const j = (i + 1) % n; luzA.idx.push(q, q + 1 + i, q + 1 + j, q + 1 + i, q + 1 + n + i, q + 1 + n + j, q + 1 + i, q + 1 + n + j, q + 1 + j); }
            };
            for (const [x, y, z] of lamparas) charco(x, y, z + 0.4 * M, 7, cLuz.clone().multiplyScalar(0.07));
            if (OBRA) pilas.filter((q, k) => k % 3 === 0).forEach(([x, y, ang], k) => {
              const fx = x + 6 * Math.cos(ang - 1.4), fy = y + 6 * Math.sin(ang - 1.4), g = alt(fx, fy);
              cono(mueble, fx, fy, g, 0, 6, 0.08, 0.07, 6, cNegro, null);
              caja(focos, fx, fy, ang, -0.5, 0.5, -0.2, 0.2, 5.8, 6.4, cLuz, { z0: g });
              charco(fx, fy, g + 0.3 * M, 16, cLuz.clone().multiplyScalar(0.2));
            });
          }
        }

        // ================= las callecitas (época callecitas): calles angostas, casas bajas
        if (CALLE) for (const c of p.callecitas) malla.banda(vias, c, 5.5, 0.3, 4, cCalle.clone().multiplyScalar(0.97 + 0.06 * hz(c.length, 11)));
        if (CALLE) for (const c of p.callecitas) for (const s of [1, -1]) {          // orillas de pasto
          const cc = c.map((q, i) => { const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1; return [q[0] - (b[1] - a[1]) / L * 3.6 * s, q[1] + (b[0] - a[0]) / L * 3.6 * s]; });
          malla.banda(obraA, cc, 1.6, 0.26, 4, cPasto);
        }

        // ================= la nave industrial genérica (callecitas y obra): dientes de sierra, ventanas y chimenea
        let humo = [], matNave = null;
        const conNave = p.fabrica && (CALLE || OBRA);
        if (conNave) {
          const [fx, fy, ang] = p.nave, g = Math.min(alt(fx, fy), alt(fx + 20, fy), alt(fx - 20, fy), alt(fx, fy + 20), alt(fx, fy - 20));
          const LL = 28, AA = 12, HH = 7, ca = Math.cos(ang), sa = Math.sin(ang);
          const P = (u, v, h) => E(fx + (u * ca - v * sa) * M, fy + (u * sa + v * ca) * M, g + h * M);
          caja(nave, fx, fy, ang, -LL - 6, LL + 6, -AA - 6, AA + 10, 0, 0.35, cCalle, { z0: g });                         // el patio
          caja(nave, fx, fy, ang, -LL, LL, -AA, AA, 0, 0.8, cLadrillo.clone().multiplyScalar(0.8), { z0: g });           // zócalo
          caja(nave, fx, fy, ang, -LL + 0.15, LL - 0.15, -AA + 0.15, AA - 0.15, 0.8, HH, cMuro, { z0: g });
          caja(nave, fx, fy, ang, -LL - 0.2, LL + 0.2, -AA - 0.2, AA + 0.2, HH, HH + 0.4, cMuro.clone().multiplyScalar(0.85), { z0: g });   // cornisa
          // el techo de dientes de sierra: 6 dientes a lo largo, cada uno con su cara inclinada y su vidriera vertical
          const nd = 6, dd = 2 * LL / nd;
          for (let k = 0; k < nd; k++) {
            const u0 = -LL + k * dd, u1 = u0 + dd, h0 = HH + 0.4, h1 = HH + 3.6;
            cara(nave, [P(u0, -AA, h0), P(u0, AA, h0), P(u1, AA, h1), P(u1, -AA, h1)], cTecho.clone().multiplyScalar(0.92 + 0.12 * hz(k, 12)), [-sa * 0 - ca * 0.4, 1, sa * 0.4]);
            cara(vent, [P(u1, -AA, h0), P(u1, AA, h0), P(u1, AA, h1 - 0.3), P(u1, -AA, h1 - 0.3)], cVidrio, [ca, 0, -sa]);
            cara(nave, [P(u1, -AA, h1 - 0.3), P(u1, AA, h1 - 0.3), P(u1, AA, h1), P(u1, -AA, h1)], cTecho.clone().multiplyScalar(0.7), [ca, 0, -sa]);
            for (const v of [-AA, AA]) cara(nave, [P(u0, v, h0), P(u1, v, h0), P(u1, v, h1), P(u1, v, h1)], cMuro.clone().multiplyScalar(0.9), [-sa * Math.sign(v), 0, -ca * Math.sign(v)]);
          }
          // ventanas en los costados largos y un portón al frente
          for (const v of [-AA - 0.05, AA + 0.05]) for (let u = -LL + 3; u < LL - 2; u += 4.2)
            cara(vent, [P(u, v, 2.4), P(u + 2.4, v, 2.4), P(u + 2.4, v, 5.2), P(u, v, 5.2)], cVidrio, [-sa * Math.sign(v), 0, -ca * Math.sign(v)]);
          cara(nave, [P(LL + 0.05, -3.5, 0.4), P(LL + 0.05, 3.5, 0.4), P(LL + 0.05, 3.5, 5), P(LL + 0.05, -3.5, 5)], cMadera.clone().multiplyScalar(0.8), [ca, 0, -sa]);
          // la chimenea de ladrillo y una caseta de calderas
          const chx = fx + (-LL + 6) * ca - (AA + 5) * sa, chy = fy + (-LL + 6) * sa + (AA + 5) * ca;
          caja(nave, chx, chy, ang, -3, 3, -3.2, 3.2, 0, 4.5, cLadrillo, { z0: g, tope: cTecho });
          cono(nave, chx, chy, g, 4.5, 24, 1.25, 0.85, 14, cLadrillo.clone().multiplyScalar(1.05), null);
          cono(nave, chx, chy, g, 24, 24.8, 1.05, 1.05, 14, cLadrillo.clone().multiplyScalar(0.75), cNegro);
          // cajas y tambos en el patio
          for (let k = 0; k < 6; k++) caja(nave, fx + (LL + 3) * ca - (-AA + 2 + k * 2.2) * sa, fy + (LL + 3) * sa + (-AA + 2 + k * 2.2) * ca, ang + 0.2 * hz(k, 13), -0.8, 0.8, -0.8, 0.8, 0.35, 1.5 + 0.6 * hz(k, 14), cMadera, { z0: g });
          // el humo: 7 bocanadas que suben y se abren (cada una su malla; posición = función de t)
          for (let j = 0; j < 7; j++) {
            const acc = malla.nueva(); bola(acc, 0, 0, 0, 1, 1, cHumo, 900 + j);
            const mt = malla.material({ alfa: 0.5 }); mt.depthWrite = false;
            const m = new THREE.Mesh(malla.geometria(acc), mt); m.frustumCulled = false; m.renderOrder = 7; scene.add(m);
            humo.push({ m, mt, j });
          }
          humo.base = [chx, chy, g + 24.8 * M];
        }

        // ================= las mallas
        const pone = (acc, mat, orden) => { if (!acc.pos.length) return null; const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        const matVias = malla.material({ desfase: 2 }), matEstr = malla.material({ desfase: 1 }), matObra = malla.material({ desfase: 1 }), matMue = malla.material();
        const matFoc = malla.material(), matVent = malla.material();
        matNave = malla.material();
        pone(obraA, matObra, 2); pone(vias, matVias, 3); pone(estr, matEstr, 4); pone(mueble, matMue, 5); pone(focos, matFoc, 5);
        const mNave = [pone(nave, matNave, 4), pone(vent, matVent, 5)].filter(Boolean);
        matFoc.uniforms.uBrillo.value = noche ? 1.9 : 1.0; matVent.uniforms.uBrillo.value = noche ? 1.7 : 1.0;
        if (luzA.pos.length) pone(luzA, malla.material({ aditivo: true, desfase: 5 }), 4);
        for (const m of [matVias, matEstr, matNave, matObra]) m.uniforms.cTinte.value.copy(cAc);
        const matEnc = malla.material({ alfa: 0, desfase: 6 }); matEnc.depthWrite = false; const mEnc = pone(enc, matEnc, 8);
        // los tableros encendidos (elemento «puentes»): una banda en el acento sobre cada tablero y sus orillas
        const puentesOn = malla.nueva(), bordes = [];
        if (!CALLE) for (const [w, i0, i1] of p.puentes) {
          if (!usar[w]) continue;
          const lev = 0.32 + 0.01 * (w % 5) + 0.3, F = marco[w];
          cintaZ(puentesOn, w, i0, i1, ancho[w] + 0.6, lev, cAc);
          for (const s of [1, -1]) bordes.push(ctx.cinta(F.slice(i0, i1 + 1).map((f, k) => ({ v: new THREE.Vector3(f.x + f.nx * (ancho[w] / 2 + 0.4) * s * M, f.g + (Z[w][i0 + k] + lev + 0.8) * M, -(f.y + f.ny * (ancho[w] / 2 + 0.4) * s * M)), s: sAc[w][i0 + k], salto: k === i1 - i0 })), cAc, ctx.CFG.ruta.ancho * 1.4, 0, 9));
        }
        const matPu = malla.material({ alfa: 0, desfase: 7 }); matPu.depthWrite = false; const mPu = pone(puentesOn, matPu, 8);

        // ================= lo que se mueve: carros (1959, hoy), obreros (obra), gente que camina (callecitas)
        const NC = (N59 || HOY) && ejesCarro.length ? clamp(p.carros | 0, 0, 12) : 0;
        ejesCarro.sort((a, b) => (p.puentes.some((q) => q[0] === b) - p.puentes.some((q) => q[0] === a)) || (sAc[b][sAc[b].length - 1] - sAc[a][sAc[a].length - 1]));
        const carros = [];
        for (let i = 0; i < NC; i++) { const w = ejesCarro[i % ejesCarro.length], L = sAc[w][sAc[w].length - 1];
          carros.push({ w, L, s0: hz(i, 20) * L, v: (N59 ? 9 : 11) + 4 * hz(i, 21), d: ancho[w] >= 8 ? (hz(i, 22) < 0.5 ? -1 : 1) * ancho[w] * 0.22 : 0 }); }
        const flC = NC ? ctx.flota("carro", NC, { luces: false, orden: 6, semilla: (p.semilla * 17 + np) % 991 }) : null;
        const gente = [];
        if (OBRA && pilas.length) for (let i = 0; i < clamp(p.obreros | 0, 0, 12); i++) {
          const q = pilas[Math.floor(hz(i, 23) * pilas.length)], ang = q[2] + (hz(i, 24) - 0.5) * 2, r = 3.5 + 4 * hz(i, 25);
          const pose = ["descargar", "rastrillar", "caminar", "de_pie"][i % 4];
          gente.push({ x: q[0] + Math.cos(ang) * r, y: q[1] + Math.sin(ang) * r, a: q[2] + Math.PI / 2 * (hz(i, 26) < 0.5 ? 1 : -1), pose, amp: pose === "caminar" ? 7 : pose === "rastrillar" ? 1.2 : 0, fase: hz(i, 27) * TAU });
        }
        const calleL = p.callecitas.map((c) => c.reduce((a, q, i) => a + (i ? Math.hypot(q[0] - c[i - 1][0], q[1] - c[i - 1][1]) : 0), 0));
        if (CALLE) for (let i = 0; i < clamp(p.obreros | 0, 0, 12); i++) { const k = i % p.callecitas.length;
          gente.push({ calle: k, s0: hz(i, 28) * calleL[k], v: (hz(i, 29) < 0.5 ? 1 : -1) * (1.0 + 0.4 * hz(i, 30)), d: (hz(i, 31) < 0.5 ? -1 : 1) * 2.0 }); }
        const camisas = [tonos.mal.clone(), lin(COL.mar).multiplyScalar(0.9), tonos.bien.clone(), lin(COL.costa), tonos.medio.clone(), lin(COL.tierra_media), tonos.secundario.clone()]
          .map((x) => (dia ? x.multiplyScalar(0.7) : x.lerp(lin(COL.costa), 0.25).multiplyScalar(1.25)));
        const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: 1.6, lev: 0.35, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991,
          color: (i) => camisas[(i + Math.floor(hz(1, 32) * camisas.length)) % camisas.length], pose: (i) => gente[i].pose || "caminar" }) : null;
        // las casas bajas (callecitas): el objeto «casa», quieto
        const flH = CALLE && p.casas.length ? ctx.flota("casa", p.casas.length, { orden: 4, semilla: p.semilla % 991 }) : null;
        const casas = p.casas.map(([x, y, a], i) => ({ x, y, a, k: 0.85 + 0.25 * hz(i, 33) }));
        if (flH) { casas.forEach((c, i) => flH.poner(i, c.x, c.y, Math.cos(c.a), Math.sin(c.a), c.k)); flH.listo(); }

        return { id: p.id, V, Z, marco, sAc, carros, flC, gente, flP, humo, matVias, matEstr, matNave, matObra, matEnc, mEnc, matPu, mPu, bordes,
          calles: p.callecitas, calleL, conNave, lev: (w) => 0.32 + 0.01 * (w % 5), m4: new THREE.Matrix4(), casas, flH, mNave,
          nave: conNave ? [p.nave[0], p.nave[1]] : null };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx, M = ctx.metros(1);
      for (const s of lista) {
        // una obra («transformar») sobre esta pieza: lo de la época vieja dentro de la obra se hunde en el turno de lo viejo
        // del evento (ctx.cuadro.epoca[id].hunde, 0–1); sin obra, nada se hunde
        const EP = ctx.cuadro.epoca && ctx.cuadro.epoca[s.id], hunde = EP && EP.hunde ? EP.hunde : null;
        if (s.flH && hunde) {
          s.casas.forEach((c, i) => {
            const h = hunde(c.x, c.y, i), k = 1 - h;
            s.flH.poner(i, c.x, c.y, Math.cos(c.a), Math.sin(c.a), k > 0.002 ? c.k * (0.75 + 0.25 * k) : 0);
            if (h > 0 && k > 0.002) { s.flH.mesh.getMatrixAt(i, s.m4); s.m4.elements[13] -= h * 6 * M; s.flH.mesh.setMatrixAt(i, s.m4); }
          });
          s.flH.listo();
        }
        let kNave = 1;
        if (s.nave && hunde) {
          const h = hunde(s.nave[0], s.nave[1], 9000);
          kNave = 1 - h;
          for (const m of s.mNave) { m.visible = kNave > 0.002; m.position.y = -h * 26 * M; }
        }
        const b = ctx.cuadro.brillo[s.id], kp = b ? clamp((b - 1) / 0.9, 0, 1) : 0;
        const el = [0, 0, 0];
        for (const e of ctx.cuadro.elementos[s.id] || []) if (e.i >= 0 && e.i < 3) el[e.i] = Math.max(el[e.i], clamp(e.k, 0, 1));
        const kA = Math.max(kp, el[0]);                       // el nudo entero
        s.matEnc.uniforms.uAlfa.value = 0.32 * kA; if (s.mEnc) s.mEnc.visible = kA > 0.002;
        s.matVias.uniforms.uTinte.value = 0.2 * kA; s.matObra.uniforms.uTinte.value = 0.15 * kA;
        const kP = el[1];                                      // los tableros, sin decir cuál es cuál
        s.matPu.uniforms.uAlfa.value = 0.5 * kP; if (s.mPu) s.mPu.visible = kP > 0.002;
        for (const c of s.bordes) c.mat.uniforms.uAlfa.value = kP;
        s.matEstr.uniforms.uTinte.value = 0.35 * kP; s.matEstr.uniforms.uBrillo.value = 1 + 0.25 * kP;
        s.matNave.uniforms.uTinte.value = 0.45 * el[2]; s.matNave.uniforms.uBrillo.value = 1 + 0.3 * el[2];
        // el humo de la chimenea: cada bocanada sube 18 m en 7 s, se abre y se apaga (función de t)
        if (s.humo.length) {
          const [hx, hy, hz0] = s.humo.base;
          for (const h of s.humo) {
            const u = (((t / 7 + h.j / 7) % 1) + 1) % 1, r = 1.4 + 3.2 * u;
            h.m.position.set(hx + 7 * u * u * M, hz0 + (1 + 18 * u) * M, -(hy + 3 * u * M));
            h.m.scale.setScalar(r * M); h.mt.uniforms.uAlfa.value = 0.55 * Math.sin(Math.PI * Math.min(1, u * 1.15)) * (s.conNave ? kNave : 0);
          }
        }
        // los carros: s = s0 + v·t a lo largo de su vía (vuelve a empezar), a la altura de la vía en ese punto
        if (s.flC) {
          s.carros.forEach((c, i) => {
            const u = (((c.s0 + c.v * t) % c.L) + c.L) % c.L, sa = s.sAc[c.w], F = s.marco[c.w], z = s.Z[c.w];
            let k = 0; while (k < sa.length - 2 && sa[k + 1] < u) k++;
            const f = (u - sa[k]) / Math.max(1e-6, sa[k + 1] - sa[k]), A = F[k], B = F[k + 1];
            const x = A.x + (B.x - A.x) * f, y = A.y + (B.y - A.y) * f, nx = A.nx + (B.nx - A.nx) * f, ny = A.ny + (B.ny - A.ny) * f;
            const zz = z[k] + (z[k + 1] - z[k]) * f + s.lev(c.w), kk = clamp(u / 10, 0, 1) * clamp((c.L - u) / 10, 0, 1);
            const px = x + nx * c.d, py = y + ny * c.d;
            s.flC.poner(i, px, py, B.x - A.x, B.y - A.y, kk);
            const gA = A.g + (B.g - A.g) * f;                // la altura de la vía: el suelo de su muestra + su altura (no el suelo bajo el carro)
            s.flC.mesh.getMatrixAt(i, s.m4); s.m4.elements[13] = gA + zz * M; s.flC.mesh.setMatrixAt(i, s.m4);
          });
          s.flC.listo();
        }
        // la gente: obreros en su pose (los que caminan van y vienen) o caminantes por las callecitas
        if (s.flP) {
          s.gente.forEach((g, i) => {
            if (g.calle !== undefined) {
              const c = s.calles[g.calle], L = s.calleL[g.calle], u = (((g.s0 + g.v * t) % L) + L) % L;
              let acc = 0, k = 0;
              while (k < c.length - 2 && acc + Math.hypot(c[k + 1][0] - c[k][0], c[k + 1][1] - c[k][1]) < u) { acc += Math.hypot(c[k + 1][0] - c[k][0], c[k + 1][1] - c[k][1]); k++; }
              const lg = Math.hypot(c[k + 1][0] - c[k][0], c[k + 1][1] - c[k][1]) || 1, f = clamp((u - acc) / lg, 0, 1), dx = (c[k + 1][0] - c[k][0]) / lg, dy = (c[k + 1][1] - c[k][1]) / lg;
              const sg = g.v > 0 ? 1 : -1, px = c[k][0] + (c[k + 1][0] - c[k][0]) * f - dy * g.d, py = c[k][1] + (c[k + 1][1] - c[k][1]) * f + dx * g.d;
              const kk = clamp(u / 4, 0, 1) * clamp((L - u) / 4, 0, 1) * (hunde ? 1 - hunde(px, py, 7000 + i) : 1);   // con la obra, la gente se va
              s.flP.poner(i, px, py, dx * sg, dy * sg, kk, 0, Math.abs(g.v));
            } else {
              const ca = Math.cos(g.a), sa = Math.sin(g.a), ph = t * (g.pose === "caminar" ? 0.18 : 0.5) + g.fase;
              const off = g.amp * Math.sin(ph), vel = g.amp * Math.cos(ph) * (g.pose === "caminar" ? 0.18 : 0.5), sg = vel >= 0 ? 1 : -1;
              s.flP.poner(i, g.x + ca * off, g.y + sa * off, g.pose === "caminar" ? ca * sg : ca, g.pose === "caminar" ? sa * sg : sa, 1, 0, Math.abs(vel));
            }
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
