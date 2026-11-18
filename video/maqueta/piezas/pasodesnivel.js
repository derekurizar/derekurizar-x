// Pieza «pasodesnivel» (ficha: pasodesnivel.json; reglas: scripts/maqueta_tipos/pasodesnivel.py): un paso a desnivel sobre
// un cruce real de la traza de OpenStreetMap. Python resuelve el EJE (la vía «desnivel» de la traza o una recta), su perfil
// ILUSTRATIVO (z en m: + puente, − trinchera; los extremos a nivel) y las calles a nivel de alrededor (las que el eje cruza,
// marcadas). Aquí solo se dibuja:
//   sobre · calzada de asfalto con rayas, tablero de concreto sobre pilas con viga cabezal, vigas bajo la losa, juntas entre
//           tramos, rampas macizas que bajan a nivel, pretiles con baranda metálica, postes de luz y postes de señal sin
//           texto; jardineras con arbustos entre las pilas;
//   bajo  · trinchera con muros de concreto y pretiles arriba; la calle que cruza pasa encima en su losa.
// Las calles que cruza siguen a nivel, con su asfalto, rayas y aceras. Genérico y sin afirmar: carriles, anchos, sentidos,
// número de pilas, colores, barandas, postes y letreros (sin texto), el tipo de las rampas. Carros ilustrativos.
// CON VIDA (puro de t): carros que suben, cruzan y bajan sin detenerse; otros corren por la calle que cruza; gente que
// camina por las aceras. De noche: postes de luz con su charco y faros en la calle a nivel.
// «resaltar» la pieza (o uno de sus lugares) enciende el paso entero en el acento.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  MAQ.PIEZAS.pasodesnivel = {
    orden: 9,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, dia = !!ES.dia;
      const alt = (x, y) => ctx.altura(x, y);
      // ---- los tonos (todos del estilo)
      const cAsf = tonos.asfalto.clone().multiplyScalar(dia ? 1.0 : 1.12);
      const cConc = tonos.pavimento.clone().lerp(lin(COL.costa), 0.4).multiplyScalar(dia ? 1.05 : 1.2);
      const cConcC = cConc.clone().lerp(lin(COL.costa), 0.2).multiplyScalar(1.05);
      const cConcO = cConc.clone().multiplyScalar(0.7);
      const cAcera = tonos.pavimento.clone().lerp(lin(COL.costa), 0.25).multiplyScalar(dia ? 1.0 : 1.1);
      const cPasto = tonos.verde.clone().lerp(tonos.bien, 0.25).multiplyScalar(dia ? 0.9 : 1.1);
      const cArbusto = tonos.verde.clone().multiplyScalar(dia ? 0.75 : 0.95);
      const cPintura = lin(COL.costa).lerp(tonos.pavimento, 0.15);
      const cNegro = tonos.linea.clone().lerp(tonos.asfalto, 0.3).multiplyScalar(0.85);
      const cMetal = cNegro.clone().lerp(cConc, 0.45);
      const cSenal = tonos.bien.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(dia ? 0.85 : 1.0);
      const cLuz = lin(COL.luces || COL.luz), cAc = lin(COL.acento);

      return piezas.map((p, np) => {
        const M = metros(1), sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const E = (x, y, z) => [x, z, -y];
        const SOBRE = p.forma === "sobre";
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
          const caras = [[[a0, b0, h1], [a1, b0, h1], [a1, b1, h1], [a0, b1, h1]], [[a0, b0, h0], [a1, b0, h0], [a1, b0, h1], [a0, b0, h1]],
            [[a0, b1, h0], [a1, b1, h0], [a1, b1, h1], [a0, b1, h1]], [[a0, b0, h0], [a0, b1, h0], [a0, b1, h1], [a0, b0, h1]],
            [[a1, b0, h0], [a1, b1, h0], [a1, b1, h1], [a1, b0, h1]]];
          if (op.fondo) caras.push([[a0, b0, h0], [a1, b0, h0], [a1, b1, h0], [a0, b1, h0]]);
          caras.forEach((q, k) => {
            const V = q.map((a) => P(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
            cara(acc, V, k === 0 && op.tope ? op.tope : col, m);
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
              const w = 1 + 0.16 * (hz(k * 131 + ((i + j) % 97), 5) - 0.5);
              vs.push([x + ico[i + j] * ru * w * M, z + Math.max(-0.2, ico[i + j + 1]) * rh * w * M, -(y - ico[i + j + 2] * ru * w * M)]);
            }
            const e1 = [vs[1][0] - vs[0][0], vs[1][1] - vs[0][1], vs[1][2] - vs[0][2]], e2 = [vs[2][0] - vs[0][0], vs[2][1] - vs[0][1], vs[2][2] - vs[0][2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const cx = (vs[0][0] + vs[1][0] + vs[2][0]) / 3 - x, cy = (vs[0][1] + vs[1][1] + vs[2][1]) / 3 - z, cz = (vs[0][2] + vs[1][2] + vs[2][2]) / 3 + y;
            if (nx * cx + ny * cy + nz * cz < 0) { nx = -nx; ny = -ny; nz = -nz; }
            const n = Math.hypot(nx, ny, nz) || 1;
            c.copy(col).multiplyScalar(sombra(nx / n, ny / n, nz / n) * (0.86 + 0.24 * hz(k * 977 + i, 6)));
            const q = acc.pos.length / 3;
            for (const X of vs) { acc.pos.push(X[0], X[1], X[2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };
        // el marco de una polilínea: punto, tangente, normal (izquierda) y suelo; y su largo acumulado
        const marcoDe = (c) => c.map((q, i) => {
          const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
          return { x: q[0], y: q[1], tx: (b[0] - a[0]) / L, ty: (b[1] - a[1]) / L, nx: -(b[1] - a[1]) / L, ny: (b[0] - a[0]) / L, g: alt(q[0], q[1]) };
        });
        const sDe = (c) => { const s = [0]; for (let i = 1; i < c.length; i++) s.push(s[i - 1] + Math.hypot(c[i][0] - c[i - 1][0], c[i][1] - c[i - 1][1])); return s; };
        // una banda de i0 a i1, corrida `d` (izquierda) y de ancho `ww`, a h(i) m sobre el suelo de cada muestra
        const banda = (acc, F, i0, i1, ww, h, tono, d = 0) => {
          const base = acc.pos.length / 3; let n = 0;
          for (let i = i0; i <= i1; i++) {
            const f = F[i], hh = h(i), cc = tono(i);
            for (const s of [1, -1]) { const o = d + ww / 2 * s; acc.pos.push(...E(f.x + f.nx * o * M, f.y + f.ny * o * M, f.g + hh * M)); acc.col.push(cc.r, cc.g, cc.b); }
            if (n) { const q = base + 2 * n; acc.idx.push(q - 2, q - 1, q, q - 1, q + 1, q); }
            n++;
          }
        };
        // una pared a lo largo, corrida `d`, de bot(i) a top(i) m (con la normal hacia `lado`)
        const pared = (acc, F, i0, i1, d, top, bot, col, lado) => {
          for (let i = i0; i < i1; i++) {
            const a = F[i], b = F[i + 1], ha = top(i), hb = top(i + 1), ba = bot(i), bb = bot(i + 1);
            if (Math.abs(ha - ba) < 0.03 && Math.abs(hb - bb) < 0.03) continue;
            const P = (f, h) => E(f.x + f.nx * d * M, f.y + f.ny * d * M, f.g + h * M);
            cara(acc, [P(a, ba), P(b, bb), P(b, hb), P(a, ha)], col, [a.nx * lado, 0, -a.ny * lado]);
          }
        };
        const tramos = (n, f) => {        // los tramos [i0, i1] donde f(i) es cierto
          const out = []; let i0 = -1;
          for (let i = 0; i < n; i++) { if (f(i)) { if (i0 < 0) i0 = i; } else if (i0 >= 0) { out.push([i0, i - 1]); i0 = -1; } }
          if (i0 >= 0) out.push([i0, n - 1]);
          return out.map(([a, b]) => [Math.max(0, a - 1), Math.min(n - 1, b + 1)]);
        };

        const vias = malla.nueva(), estr = malla.nueva(), mueble = malla.nueva(), focos = malla.nueva(), verde = malla.nueva();
        const luzA = malla.nueva(), enc = malla.nueva(), fondo = malla.nueva(), muroA = malla.nueva(), muroB = malla.nueva();
        const A0 = ctx.CFG.ruta.ancho, lamparas = [];
        const pts3 = (F, S, d, h) => F.map((f, i) => ({ v: new THREE.Vector3(f.x + f.nx * d * M, f.g + h(i) * M, -(f.y + f.ny * d * M)), s: S[i], salto: i === F.length - 1 }));

        // ================= las calles a nivel (las de la traza): asfalto, aceras y rayas
        const VI = p.vias.map((v) => ({ ...v, F: marcoDe(v.c), S: sDe(v.c) }));
        VI.forEach((v, k) => {
          const n = v.c.length - 1, w = v.ancho, lv = 0.3 + 0.01 * (k % 4);
          banda(vias, v.F, 0, n, w, () => lv, (i) => cAsf.clone().multiplyScalar(0.95 + 0.07 * hz(k * 300 + i, 1)));
          if (v.clase !== "autopista") for (const s of [1, -1]) banda(vias, v.F, 0, n, 2.2, () => lv + 0.14, (i) => cAcera.clone().multiplyScalar(0.94 + 0.08 * hz(k * 400 + i, 2)), s * (w / 2 + 1.1));
          if (v.cruza || w >= 8) {
            const L = [];
            if (v.cruza) for (const s of [1, -1]) L.push(ctx.cinta(pts3(v.F, v.S, s * (w / 2 - 0.4), () => lv + 0.06), cPintura, A0 * 0.4, 0.75, 6));
            if (w >= 8) L.push(ctx.cinta(pts3(v.F, v.S, 0, () => lv + 0.06), cPintura, A0 * 0.32, 0.6, 6, { raya: 9 }));
          }
        });
        // ¿hay una calle a nivel en (x, y)? (para no plantar una pila en su asfalto)
        const sobreVia = (x, y, m) => VI.some((v) => v.c.some((q) => Math.hypot(q[0] - x, q[1] - y) < v.ancho / 2 + m));

        // ================= el eje: calzada, estructura, mobiliario
        const C = p.eje, F = marcoDe(C), S = sDe(C), Z = p.z, N = C.length, W = p.ancho, LOSA = 1.4, HT = 4.0, lev = 0.36;
        const LT = S[N - 1];
        const tonoAsf = (i) => cAsf.clone().multiplyScalar(0.94 + 0.08 * hz(i, 3));
        // la calzada del eje (en bajo, el fondo de la trinchera va en su propia malla)
        if (SOBRE) banda(vias, F, 0, N - 1, W, (i) => Z[i] + lev, tonoAsf);
        else {
          for (const [a, b] of tramos(N, (i) => Z[i] > -0.3)) banda(vias, F, a, b, W, (i) => Z[i] + lev, tonoAsf);
          for (const [a, b] of tramos(N, (i) => Z[i] <= -0.3)) banda(fondo, F, a, b, W, (i) => Z[i] + lev, tonoAsf);
        }
        // rayas del eje: orillas y raya central discontinua
        const rayasEje = [];
        for (const s of [1, -1]) rayasEje.push(ctx.cinta(pts3(F, S, s * (W / 2 - 0.45), (i) => Z[i] + lev + 0.06), cPintura, A0 * 0.42, 0.8, 6));
        rayasEje.push(ctx.cinta(pts3(F, S, 0, (i) => Z[i] + lev + 0.06), cPintura, A0 * 0.34, 0.7, 6, { raya: 9 }));
        ctx.linea(p.id, rayasEje[0]);

        const pilas = [];
        if (SOBRE) {
          for (const [a, b] of tramos(N, (i) => Z[i] > 0.25)) {
            // los costados: la losa donde va sobre pilas; maciza (rampa) hasta el suelo donde no
            for (const s of [1, -1]) pared(estr, F, a, b, s * W / 2, (i) => Z[i] + lev, (i) => (Z[i] >= HT ? Z[i] + lev - LOSA : 0), cConc, s);
            for (const [a2, b2] of tramos(N, (i) => Z[i] >= HT && i >= a && i <= b)) {
              banda(estr, F, a2, b2, W, (i) => Z[i] + lev - LOSA, () => cConcO);                     // la cara de abajo de la losa
              // las vigas bajo la losa (cuatro, a lo largo)
              for (const v of [-3.3, -1.1, 1.1, 3.3]) {
                const bot = (i) => Z[i] + lev - LOSA - 0.95, top = (i) => Z[i] + lev - LOSA;
                for (const s of [1, -1]) pared(estr, F, a2, b2, v + s * 0.28, top, bot, cConcO.clone().multiplyScalar(1.15), s);
                banda(estr, F, a2, b2, 0.56, bot, () => cConcO.clone().multiplyScalar(0.9), v);
              }
            }
            // pretiles con su baranda metálica
            for (const s of [1, -1]) {
              const d0 = s * W / 2, d1 = s * (W / 2 - 0.3), top = (i) => Z[i] + lev + 1.0, bot = (i) => Z[i] + lev;
              pared(estr, F, a, b, d0, top, bot, cConcC, s);
              pared(estr, F, a, b, d1, top, bot, cConcO.clone().multiplyScalar(1.25), -s);
              banda(estr, F, a, b, 0.3, top, () => cConcC, s * (W / 2 - 0.15));
              pared(estr, F, a, b, s * (W / 2 - 0.15), (i) => Z[i] + lev + 1.42, (i) => Z[i] + lev + 1.32, cMetal, s);
              for (let i = a; i <= b; i += 1) { const f = F[i], d = s * (W / 2 - 0.15);
                cono(estr, f.x + f.nx * d, f.y + f.ny * d, f.g, Z[i] + lev + 1.0, Z[i] + lev + 1.42, 0.05, 0.05, 6, cMetal, null); }
            }
          }
          // las pilas: dos columnas con zapata y su viga cabezal, cada ≈ 26 m bajo el tablero (no sobre una calle)
          let sig = 10;
          for (let i = 0; i < N; i++) {
            if (S[i] < sig || Z[i] < HT) continue;
            const f = F[i], ang = Math.atan2(f.ty, f.tx), top = Z[i] + lev - LOSA - 0.95;
            const cols = [-2.7, 2.7].map((d) => [f.x + f.nx * d, f.y + f.ny * d]);
            if (cols.some(([x, y]) => sobreVia(x, y, 1.2))) { sig = S[i] + 4; continue; }
            sig = S[i] + 26;
            for (const [x, y] of cols) {
              caja(estr, x, y, ang, -1.1, 1.1, -1.1, 1.1, 0, 0.45, cConcO, { z0: f.g });
              cono(estr, x, y, f.g, 0.45, top - 1.1, 0.68, 0.62, 16, cConc, null);
            }
            caja(estr, f.x, f.y, ang, -0.8, 0.8, -W * 0.47, W * 0.47, top - 1.15, top, cConcC.clone().multiplyScalar(0.95), { z0: f.g, fondo: true });
            caja(estr, f.x, f.y, ang, -0.12, 0.12, -W / 2 + 0.35, W / 2 - 0.35, Z[i] + lev, Z[i] + lev + 0.035, cNegro, { z0: f.g });   // la junta
            pilas.push([f.x, f.y, ang, i]);
          }
          // jardineras entre las columnas de cada pila, con arbustos
          pilas.forEach(([x, y, ang], k) => {
            const g = alt(x, y);
            caja(verde, x, y, ang, -5.5, 5.5, -1.3, 1.3, 0, 0.55, cConcC, { z0: g, tope: cPasto });
            for (let j = 0; j < 4; j++) { const u = -4 + j * 2.7 + 0.6 * (hz(k * 7 + j, 8) - 0.5);
              bola(verde, x + Math.cos(ang) * u, y + Math.sin(ang) * u, g + 0.55 * M, 0.75 + 0.3 * hz(k * 7 + j, 9), 0.7 + 0.3 * hz(k * 7 + j, 10), cArbusto.clone().multiplyScalar(0.9 + 0.2 * hz(k * 7 + j, 11)), 700 + k * 7 + j); }
          });
        } else {
          // la trinchera: los muros de concreto (cada lado en su malla: el del lado de la cámara no se ve) y los pretiles
          for (const [a, b] of tramos(N, (i) => Z[i] < -0.25)) {
            pared(muroA, F, a, b, W / 2, () => 0.3, (i) => Z[i] + lev, cConc, -1);
            pared(muroB, F, a, b, -W / 2, () => 0.3, (i) => Z[i] + lev, cConc, 1);
            for (const s of [1, -1]) {
              pared(estr, F, a, b, s * (W / 2 + 0.35), () => 1.3, () => 0.2, cConcC, s);
              pared(estr, F, a, b, s * W / 2, () => 1.3, () => 0.3, cConcO.clone().multiplyScalar(1.2), -s);
              banda(estr, F, a, b, 0.35, () => 1.3, () => cConcC, s * (W / 2 + 0.17));
              pared(estr, F, a, b, s * (W / 2 + 0.17), () => 1.72, () => 1.62, cMetal, s);
            }
          }
          // la losa por donde la calle cruza encima de la trinchera
          for (const [x, y] of p.cruces) {
            let k = 0, dm = 1e9; F.forEach((f, i) => { const d = Math.hypot(f.x - x, f.y - y); if (d < dm) { dm = d; k = i; } });
            const f = F[k], ang = Math.atan2(f.ty, f.tx), z = Z[k];
            caja(estr, x, y, ang, -7, 7, -W / 2 - 0.4, W / 2 + 0.4, Math.min(-0.2, z + lev + 4.8), 0.3, cConcO.clone().multiplyScalar(1.1), { z0: f.g, fondo: true });
          }
        }
        // los postes de luz sobre el eje, cada ≈ 40 m alternando lado
        { let sl = 12, lado = 1;
          for (let i = 0; i < N; i++) {
            if (S[i] < sl || S[i] > LT - 10) continue;
            sl = S[i] + 40; lado = -lado;
            const f = F[i], d = lado * (W / 2 - 0.15), x = f.x + f.nx * d, y = f.y + f.ny * d;
            const z0 = f.g + (SOBRE ? Z[i] + lev + 1.0 : Z[i] + lev) * M, H = 9;
            cono(mueble, x, y, z0, 0, H, 0.12, 0.08, 10, cNegro, null);
            const ax = -f.nx * lado, ay = -f.ny * lado;
            caja(mueble, x + ax * 0.9, y + ay * 0.9, Math.atan2(ay, ax), -0.9, 0.9, -0.06, 0.06, H - 0.1, H + 0.05, cNegro, { z0 });
            caja(focos, x + ax * 1.7, y + ay * 1.7, Math.atan2(ay, ax), -0.35, 0.35, -0.16, 0.16, H - 0.25, H, noche ? cLuz : cNegro.clone().lerp(cConc, 0.5), { z0 });
            lamparas.push([x + ax * 1.7, y + ay * 1.7, f.g + (Z[i] + lev) * M]);
          }
        }
        // los postes de señal (sin texto) al pie de cada rampa, a un lado del eje
        for (const fin of [0, 1]) {
          let i = fin ? N - 1 : 0; const st = fin ? -1 : 1;
          while (i > 0 && i < N - 1 && Math.abs(Z[i]) < 0.6) i += st;
          i = clamp(i - st * 3, 0, N - 1);
          const f = F[i], s = fin ? -1 : 1, d = s * (W / 2 + 2.2), x = f.x + f.nx * d, y = f.y + f.ny * d, g = alt(x, y), ang = Math.atan2(f.ty, f.tx);
          if (sobreVia(x, y, 0.5)) continue;
          for (const v of [-1.3, 1.3]) cono(mueble, x + Math.cos(ang + Math.PI / 2) * v, y + Math.sin(ang + Math.PI / 2) * v, g, 0, 5.2, 0.07, 0.07, 8, cMetal, null);
          caja(mueble, x, y, ang, -0.05, 0.05, -1.6, 1.6, 3.4, 5.3, cSenal, { z0: g });
          caja(mueble, x, y, ang, -0.07, -0.05, -1.45, 1.45, 3.55, 5.15, cSenal.clone().lerp(cPintura, 0.15), { z0: g });
        }
        // el resaltado del paso: una banda en el acento sobre el eje (apagada hasta su resaltar)
        banda(enc, F, 0, N - 1, W + 1.4, (i) => Z[i] + lev + 0.25, () => cAc);

        // de noche, los charcos de luz
        if (noche) {
          const charco = (x, y, z, rr, col) => {
            const n = 16, q = luzA.pos.length / 3;
            luzA.pos.push(...E(x, y, z)); luzA.col.push(col.r, col.g, col.b);
            for (const [f, a] of [[0.5, 0.55], [1, 0]]) for (let i = 0; i < n; i++) { const t0 = TAU * i / n; luzA.pos.push(...E(x + rr * f * Math.cos(t0) * M, y + rr * f * Math.sin(t0) * M, z)); luzA.col.push(col.r * a, col.g * a, col.b * a); }
            for (let i = 0; i < n; i++) { const j = (i + 1) % n; luzA.idx.push(q, q + 1 + i, q + 1 + j, q + 1 + i, q + 1 + n + i, q + 1 + n + j, q + 1 + i, q + 1 + n + j, q + 1 + j); }
          };
          for (const [x, y, z] of lamparas) charco(x, y, z + 0.45 * M, 8, cLuz.clone().multiplyScalar(0.08));
        }

        // ================= las mallas
        const pone = (acc, mat, orden) => { if (!acc.pos.length) return null; const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        const matVias = malla.material({ desfase: 2 }), matEstr = malla.material({ desfase: 1 }), matMue = malla.material(), matFoc = malla.material(), matVerde = malla.material();
        pone(vias, matVias, 3); pone(estr, matEstr, 4); pone(mueble, matMue, 5); pone(focos, matFoc, 5); pone(verde, matVerde, 4);
        // la trinchera se ve por su boca: se dibuja después del suelo del mundo y sin probar su profundidad
        let mA = null, mB = null; const matFondo = malla.material(), matMuro = malla.material();
        for (const mt of [matFondo, matMuro]) mt.depthTest = false;
        pone(fondo, matFondo, 1); mA = pone(muroA, matMuro, 1.5); mB = pone(muroB, matMuro, 1.5);
        matFoc.uniforms.uBrillo.value = noche ? 1.9 : 1.0;
        if (luzA.pos.length) pone(luzA, malla.material({ aditivo: true, desfase: 5 }), 4);
        for (const m of [matVias, matEstr, matFondo, matMuro]) m.uniforms.cTinte.value.copy(cAc);
        const matEnc = malla.material({ alfa: 0, desfase: 6 }); matEnc.depthWrite = false; const mEnc = pone(enc, matEnc, 8);

        // ================= lo que se mueve: carros por el paso y por la calle que cruza; gente en las aceras
        const NC = clamp(p.carros | 0, 0, 20), nEje = Math.ceil(NC / 2), nVia = NC - nEje;
        const carrosEje = [];
        for (let i = 0; i < nEje; i++) carrosEje.push({ s0: hz(i, 20) * LT, v: 11 + 4 * hz(i, 21), dir: i % 2 ? -1 : 1 });
        const ejesVia = VI.map((v, k) => k).filter((k) => VI[k].cruza && VI[k].S[VI[k].S.length - 1] > 60);
        const carrosVia = [];
        if (ejesVia.length) for (let i = 0; i < nVia; i++) { const k = ejesVia[i % ejesVia.length], v = VI[k], L = v.S[v.S.length - 1];
          carrosVia.push({ k, L, s0: hz(i, 22) * L, v: 10 + 5 * hz(i, 23), d: v.ancho >= 8 ? (hz(i, 24) < 0.5 ? -1 : 1) * v.ancho * 0.22 : 0 }); }
        const flE = carrosEje.length ? ctx.flota("carro", carrosEje.length, { luces: false, orden: 6, semilla: (p.semilla * 17 + np) % 991 }) : null;
        const flV = carrosVia.length ? ctx.flota("carro", carrosVia.length, { orden: 6, semilla: (p.semilla * 23 + np + 5) % 991 }) : null;
        // la gente: camina por las aceras de las calles que cruza (no en las autopistas)
        const aceras = VI.map((v, k) => k).filter((k) => VI[k].clase !== "autopista" && VI[k].S[VI[k].S.length - 1] > 40)
          .sort((a, b) => (VI[b].cruza - VI[a].cruza) || (VI[b].S[VI[b].S.length - 1] - VI[a].S[VI[a].S.length - 1]));
        const gente = [];
        if (aceras.length) for (let i = 0; i < clamp(p.personas | 0, 0, 12); i++) { const k = aceras[i % Math.min(3, aceras.length)], v = VI[k], L = v.S[v.S.length - 1];
          gente.push({ k, L, s0: hz(i, 25) * L, v: (hz(i, 26) < 0.5 ? 1 : -1) * (1.1 + 0.4 * hz(i, 27)), d: (hz(i, 28) < 0.5 ? 1 : -1) * (v.ancho / 2 + 1.1) }); }
        const camisas = [tonos.mal.clone(), lin(COL.mar).multiplyScalar(0.9), tonos.bien.clone(), lin(COL.costa), tonos.medio.clone(), tonos.secundario.clone()]
          .map((x) => (dia ? x.multiplyScalar(0.7) : x.lerp(lin(COL.costa), 0.25).multiplyScalar(1.25)));
        const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: 1.4, lev: 0.45, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991,
          color: (i) => camisas[(i + Math.floor(hz(1, 29) * camisas.length)) % camisas.length], pose: () => "caminar" }) : null;

        return { id: p.id, F, S, Z, LT, W, lev, VI, carrosEje, carrosVia, flE, flV, gente, flP, matVias, matEstr, matFondo, matMuro, matEnc, mEnc,
          mA, mB, SOBRE, medio: F[Math.floor(N / 2)], m4: new THREE.Matrix4() };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx, M = ctx.metros(1);
      // el punto a s de un marco (interpolado): x, y, normal, suelo y el índice
      const en = (F, S, u) => {
        let k = 0; while (k < S.length - 2 && S[k + 1] < u) k++;
        const f = clamp((u - S[k]) / Math.max(1e-6, S[k + 1] - S[k]), 0, 1), A = F[k], B = F[k + 1];
        return { k, f, x: A.x + (B.x - A.x) * f, y: A.y + (B.y - A.y) * f, nx: A.nx + (B.nx - A.nx) * f, ny: A.ny + (B.ny - A.ny) * f, g: A.g + (B.g - A.g) * f, dx: B.x - A.x, dy: B.y - A.y };
      };
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kp = b ? clamp((b - 1) / 0.9, 0, 1) : 0;
        let kA = kp;
        for (const e of ctx.cuadro.elementos[s.id] || []) kA = Math.max(kA, clamp(e.k, 0, 1));
        s.matEnc.uniforms.uAlfa.value = 0.36 * kA; if (s.mEnc) s.mEnc.visible = kA > 0.002;
        s.matEstr.uniforms.uTinte.value = 0.35 * kA; s.matEstr.uniforms.uBrillo.value = 1 + 0.2 * kA;
        s.matVias.uniforms.uTinte.value = 0.12 * kA; s.matFondo.uniforms.uTinte.value = 0.3 * kA; s.matMuro.uniforms.uTinte.value = 0.3 * kA;
        // la trinchera: solo el muro del lado contrario a la cámara (el otro se ve por detrás)
        if (s.mA || s.mB) {
          const c = ctx.camera.position, md = s.medio, lado = (c.x - md.x * M) * md.nx + (-c.z - md.y * M) * md.ny;
          if (s.mA) s.mA.visible = lado < 0;
          if (s.mB) s.mB.visible = lado >= 0;
        }
        // los carros del paso: s = s0 + v·t a lo largo del eje (vuelven a empezar), a la altura del perfil en ese punto
        if (s.flE) {
          s.carrosEje.forEach((c, i) => {
            const u0 = (((c.s0 + c.v * t) % s.LT) + s.LT) % s.LT, u = c.dir > 0 ? u0 : s.LT - u0, P = en(s.F, s.S, u);
            const z = s.Z[P.k] + (s.Z[P.k + 1] - s.Z[P.k]) * P.f + s.lev, d = -c.dir * s.W * 0.25;
            const kk = clamp(u0 / 10, 0, 1) * clamp((s.LT - u0) / 10, 0, 1);
            s.flE.poner(i, P.x + P.nx * d, P.y + P.ny * d, P.dx * c.dir, P.dy * c.dir, kk);
            s.flE.mesh.getMatrixAt(i, s.m4); s.m4.elements[13] = P.g + z * M; s.flE.mesh.setMatrixAt(i, s.m4);
          });
          s.flE.listo();
        }
        // los carros de la calle que cruza: a nivel, siguen su vía
        if (s.flV) {
          s.carrosVia.forEach((c, i) => {
            const v = s.VI[c.k], u = (((c.s0 + c.v * t) % c.L) + c.L) % c.L, P = en(v.F, v.S, u);
            const kk = clamp(u / 10, 0, 1) * clamp((c.L - u) / 10, 0, 1);
            s.flV.poner(i, P.x + P.nx * c.d, P.y + P.ny * c.d, P.dx, P.dy, kk);
          });
          s.flV.listo();
        }
        // la gente por las aceras
        if (s.flP) {
          s.gente.forEach((g, i) => {
            const v = s.VI[g.k], u = (((g.s0 + g.v * t) % g.L) + g.L) % g.L, P = en(v.F, v.S, u), sg = g.v > 0 ? 1 : -1;
            const kk = clamp(u / 4, 0, 1) * clamp((g.L - u) / 4, 0, 1);
            s.flP.poner(i, P.x + P.nx * g.d, P.y + P.ny * g.d, P.dx * sg, P.dy * sg, kk, 0, Math.abs(g.v));
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
