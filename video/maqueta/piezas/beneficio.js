// Pieza «beneficio» (ficha: beneficio.json; reglas: scripts/maqueta_tipos/beneficio.py): el beneficio húmedo de una finca,
// genérico (cereza → pergamino), centrado en `lugar` y orientado por `rumbo` (u: hacia donde avanza el proceso; v: a lo
// ancho). De atrás hacia adelante: la pila de recibo llena de cereza roja y su canaleta, la despulpadora (cuerpo pintado,
// volante de rayos y la TOLVA arriba, abierta, con cereza adentro) que bota la pulpa a un montón a su costado; las tres pilas
// de fermento de cemento (la primera con la masa de grano en su mucílago, las otras con agua); el canal de correteo, angosto,
// por donde corre el agua con el grano; y el patio de secado de cemento con bordillo y el pergamino tendido en cuatro
// franjas claras con sus surcos. Todo sobre un patio de tierra y una plataforma de cemento, con sombra de contacto (más
// marcada en el estilo `dia`). Medidas en metros reales × `tamano`; la cereza y el rastrillo, agrandados para leerse.
// Lo que se mueve (función pura de t, nada se acumula): la cereza que baja por la canaleta y cae en la tolva (cada una con
// su fase fija por ctx.hash), el volante que gira, el agua (un shader: brillo que viaja con la corriente y granos que flotan
// en el canal; ondas lentas en las pilas) y `personas` (objeto persona en su pose `rastrillar`: sombrero de ala y rastrillo
// que va y viene, el torso inclinado, pasos cortos) que avanzan despacio a lo largo de su franja (agrandadas ×1.45, camisa de
// color y sombra, para leerse a 35–45 m); con 3, la tercera en la pose `cargar` sube sacos junto a la pila de recibo. El pergamino es crema/beige en surcos con relieve, el cemento gris y frío: no se
// confunden ni en `dia` ni en `noche`. «resaltar» la pieza aviva la cereza, el agua y el pergamino. Sin colores escritos.
(function (MAQ) {
  MAQ.PIEZAS.beneficio = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp, GLSL_COMUN, uComun } = ctx;
      const noche = ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo)
      const cTierra = tonos.calle.clone().lerp(tonos.campo2, 0.25);
      // el cemento, gris y frío (en `dia` con un poco del azul del estilo, para que el pergamino crema no se confunda con él)
      const cCem = dia ? tonos.pavimento.clone().lerp(lin(COL.mar), 0.18).multiplyScalar(0.66) : tonos.pavimento.clone().multiplyScalar(noche ? 1.15 : 0.74);
      const cMuro = tonos.muro.clone().lerp(tonos.pavimento, 0.45).multiplyScalar(noche ? 1.3 : 0.95);
      const cBorde = cMuro.clone().multiplyScalar(1.08);
      const cMaq = dia ? lin(COL.mar).lerp(tonos.linea, 0.42) : tonos.techo.clone().lerp(tonos.muro, 0.3);
      const cMetal = tonos.asfalto.clone().lerp(tonos.pavimento, 0.45);
      const cOscuro = tonos.linea.clone().lerp(tonos.asfalto, 0.4);
      const cRoja = tonos.mal.clone();
      const cPulpa = tonos.mal.clone().lerp(tonos.linea, 0.6);
      // el pergamino: crema/beige, más cálido y más oscuro que la luz (en `dia` no se quema; de noche, tibio sobre el cemento azul)
      const cPerg = dia ? lin(COL.tierra_alta).lerp(lin(COL.costa), 0.25).lerp(tonos.medio, 0.18).multiplyScalar(0.97)
        : noche ? lin(COL.luces).lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(0.45)
        : lin(COL.costa).lerp(tonos.arena, 0.4).lerp(tonos.medio, 0.12);
      const cMuci = cPerg.clone().lerp(tonos.medio, 0.18).multiplyScalar(0.92);
      const cAgua = tonos.agua.clone(), cAguaPila = tonos.agua.clone().lerp(tonos.verde, 0.22).multiplyScalar(0.9);
      const cLuz = lin(COL.luz), cMadera = tonos.techo.clone().lerp(tonos.linea, 0.35);
      const KS = ctx.CFG.sombra_contacto || (dia ? 0.4 : 0.22);
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K, OFF = 3.5;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + ((u - OFF) * ux - v * uy) * M, p.y + ((u - OFF) * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const ruido = (x, y, cel, k) => {                 // ruido de valor fijo, 0–1
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // ---- caras con la luz horneada: una cara de 4 puntos de escena; ref = hacia dónde es «afuera»
        const cara = (acc, P, col, ref, f = 1) => {
          const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = sombra(nx, ny, nz) * f, q = acc.pos.length / 3;
          for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        // una caja (a, b, c) → T (en el beneficio: u, v, h); sinTope: solo los costados
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
            cara(acc, V, k === 0 && op.tope ? op.tope : col, m, k ? 1 : (op.luzTope || 1));
          });
        };
        const cj = (acc, u0, u1, v0, v1, h0, h1, col, op) => caja(acc, E, u0, u1, v0, v1, h0, h1, col, op);
        // una losa en celdas (cada una con su tono): col(u, v, i) → Color
        const losa = (acc, u0, u1, v0, v1, h, cu, cv, col) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0);
          for (let i = 0, k = 0; i < nu; i++) for (let j = 0; j < nv; j++, k++) {
            const a = u0 + (u1 - u0) * i / nu, b = u0 + (u1 - u0) * (i + 1) / nu, e = v0 + (v1 - v0) * j / nv, f = v0 + (v1 - v0) * (j + 1) / nv;
            const cc = col((a + b) / 2, (e + f) / 2, k, j), q = acc.pos.length / 3;
            for (const [uu, vv] of [[a, e], [b, e], [b, f], [a, f]]) { const P = E(uu, vv, h); acc.pos.push(P[0], P[1], P[2]); acc.col.push(cc.r * l, cc.g * l, cc.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        // un sólido de caras planas (octaedro o icosaedro) en (u, v, h), radios en metros
        const gema = (acc, tri, P, rx, ry, rz, rot, col, plana = 0) => {
          const cr = Math.cos(rot), sr = Math.sin(rot), v = [];
          for (let i = 0; i < tri.length; i += 3) {
            const x = tri[i] * rx * M, y = tri[i + 1] * ry * M, z = tri[i + 2] * rz * M;
            v.push(P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr);
          }
          for (let i = 0; i < v.length; i += 9) {
            const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const n = Math.hypot(nx, ny, nz) || 1, sb = sombra(nx / n, ny / n, nz / n);
            c.copy(col).multiplyScalar(plana + (1 - plana) * sb);
            const q = acc.pos.length / 3;
            for (let j = 0; j < 9; j += 3) { acc.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };
        // una barra de A a B (puntos de escena), de 4 lados
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

        // ================= el suelo: patio de tierra, plataforma de cemento y patio de secado
        const suelo = malla.nueva(), solido = malla.nueva(), perg = malla.nueva();
        losa(suelo, -28, 35, -13.5, 13.5, 0.04, 1.5, 1.5, (u, v, k) =>
          c.copy(cTierra).multiplyScalar(0.86 + 0.22 * ruido(u, v, 4.5, 11) + 0.06 * hz(k, 12)).clone());
        // la plataforma de cemento (recibo, despulpadora y pilas)
        const H0 = 0.12;
        losa(solido, -27, -1.5, -9.5, 9.5, H0, 1.0, 1.0, (u, v, k) => c.copy(cCem).multiplyScalar(0.93 + 0.1 * ruido(u, v, 3, 21) + 0.04 * hz(k, 22)).clone());
        cj(solido, -27, -1.5, -9.5, 9.5, 0, H0, cCem, { sinTope: true });
        // el patio de secado: losa con bordillo
        const PU0 = 9, PU1 = 34, PV = 11.6;
        losa(solido, PU0, PU1, -PV, PV, H0, 1.0, 1.0, (u, v, k) => c.copy(cCem).multiplyScalar(0.95 + 0.08 * ruido(u, v, 4, 31) + 0.04 * hz(k, 32)).clone());
        cj(solido, PU0, PU1, -PV, PV, 0, H0, cCem, { sinTope: true });
        for (const [a0, a1, b0, b1] of [[PU0, PU1, -PV, -PV + 0.22], [PU0, PU1, PV - 0.22, PV], [PU0, PU0 + 0.22, -PV, PV], [PU1 - 0.22, PU1, -PV, PV]])
          cj(solido, a0, a1, b0, b1, H0, 0.32, cBorde);
        // el pergamino: cuatro franjas de 4.2 m a lo largo del patio, en SURCOS de verdad: crestas a lo largo (u) cada SP m
        // a lo ancho, la cresta clara y el fondo del surco oscuro (color por vértice, luz por cara): se leen a 35–45 m
        const FR = [-8.4, -2.8, 2.8, 8.4], FW = 2.1, FU0 = PU0 + 1.1, FU1 = PU1 - 1.1, HP = 0.17, HS = 0.08, SP = 0.6;
        const rampa = (acc, a, b, v0, v1, h0, h1, c0, c1) => {   // una ladera del surco: de (v0, h0) a (v1, h1), de a a b
          const P = [E(a, v0, h0), E(b, v0, h0), E(b, v1, h1), E(a, v1, h1)], e1 = P[1].map((x, i) => x - P[0][i]), e2 = P[3].map((x, i) => x - P[0][i]);
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = sombra(nx / n, ny / n, nz / n), q = acc.pos.length / 3;
          [c0, c0, c1, c1].forEach((cc, i) => { acc.pos.push(P[i][0], P[i][1], P[i][2]); acc.col.push(cc.r * l, cc.g * l, cc.b * l); });
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        for (const vc of FR) {
          const nv = Math.round(2 * FW / SP), nu = Math.round(FU1 - FU0);
          for (let j = 0; j < nv; j++) {
            const v0 = vc - FW + 2 * FW * j / nv, v1 = vc - FW + 2 * FW * (j + 1) / nv, vm = (v0 + v1) / 2;
            const borde = 1 - 0.1 * clamp(1 - (FW - Math.abs(vm - vc)) / 0.5, 0, 1);
            for (let i = 0; i < nu; i++) {
              const a = FU0 + (FU1 - FU0) * i / nu, b = FU0 + (FU1 - FU0) * (i + 1) / nu, k = (vc + 20) * 1000 + j * 97 + i;
              const tono = cPerg.clone().multiplyScalar(borde * (0.93 + 0.09 * hz(k, 41) + 0.07 * ruido((a + b) / 2, vm, 2.5, 42)));
              const hondo = tono.clone().multiplyScalar(0.7), cresta = tono.clone().multiplyScalar(1.07);
              rampa(perg, a, b, v0, vm, HP, HP + HS, hondo, cresta);
              rampa(perg, a, b, vm, v1, HP + HS, HP, cresta, hondo);
            }
          }
          cj(perg, FU0, FU1, vc - FW, vc + FW, H0, HP, cPerg.clone().multiplyScalar(0.8), { sinTope: true });
        }

        // ================= el recibo, la canaleta y la despulpadora (alineados en v = VD)
        const VD = -4.3;
        // la pila de recibo: un tanque de cemento alto con su boca llena de cereza
        const RU0 = -25.6, RU1 = -22, RV0 = VD - 1.75, RV1 = VD + 1.75, RH = 3.0, e = 0.22;
        cj(solido, RU0, RU1, RV0, RV0 + e, H0, RH, cMuro, { tope: cBorde });
        cj(solido, RU0, RU1, RV1 - e, RV1, H0, RH, cMuro, { tope: cBorde });
        cj(solido, RU0, RU0 + e, RV0 + e, RV1 - e, H0, RH, cMuro, { tope: cBorde });
        cj(solido, RU1 - e, RU1, RV0 + e, RV1 - e, H0, RH, cMuro, { tope: cBorde });
        const fruta = malla.nueva();
        losa(fruta, RU0 + e, RU1 - e, RV0 + e, RV1 - e, RH - 0.12, 0.6, 0.6, () => cRoja.clone().multiplyScalar(0.7));
        for (let i = 0, n = 0; i < 11; i++) for (let j = 0; j < 11; j++, n++) {
          const u = RU0 + e + 0.15 + (RU1 - RU0 - 2 * e - 0.3) * (i + hz(n, 61) * 0.6) / 11, v = RV0 + e + 0.15 + (RV1 - RV0 - 2 * e - 0.3) * (j + hz(n, 62) * 0.6) / 11;
          gema(fruta, oct, E(u, v, RH - 0.08 + 0.06 * hz(n, 63)), 0.15, 0.17, 0.15, hz(n, 64) * 3, cRoja.clone().multiplyScalar(0.85 + 0.25 * hz(n, 65)), 0.45);
        }
        // la canaleta: de la boca del recibo a la tolva, en U, bajando
        const CU0 = -22, CU1 = -18.0, CH0 = 2.85, CH1 = 2.5, CW = 0.34;
        const ch = (u) => CH0 + (CH1 - CH0) * (u - CU0) / (CU1 - CU0);
        {
          const pts = (v, dh) => [E(CU0, v, CH0 + dh), E(CU1, v, CH1 + dh)];
          const [a0, a1] = pts(VD - CW, 0), [b0, b1] = pts(VD + CW, 0), [c0, c1] = pts(VD - CW, 0.22), [d0, d1] = pts(VD + CW, 0.22);
          cara(solido, [a0, a1, b1, b0], cMetal, [0, 1, 0]);
          cara(solido, [a0, a1, c1, c0], cMetal.clone().multiplyScalar(0.9), null);
          cara(solido, [b0, b1, d1, d0], cMetal.clone().multiplyScalar(0.9), null);
          barra(solido, E(CU1 - 0.6, VD, 0.12), E(CU1 - 0.6, VD, CH1 + 0.05), 0.06 * M, cOscuro);   // la pata
          barra(solido, E(CU0 + 1.2, VD, 0.12), E(CU0 + 1.2, VD, ch(CU0 + 1.2)), 0.06 * M, cOscuro);
        }
        // la despulpadora: patas, cuerpo pintado, la tolva abierta arriba (cereza adentro), el volante y la salida a la pila
        const DU0 = -18.5, DU1 = -16.7, DH = 1.45, TH = 2.3;
        cj(solido, DU0 - 0.3, DU1 + 0.3, VD - 1.2, VD + 1.2, H0, 0.3, cOscuro);
        cj(solido, DU0, DU1, VD - 0.9, VD + 0.9, 0.3, DH, cMaq, { tope: cMaq.clone().multiplyScalar(1.08) });
        cj(solido, DU0 + 0.25, DU1 - 0.25, VD - 1.05, VD + 1.05, 0.55, 1.2, cMaq.clone().multiplyScalar(0.8));   // el cilindro
        const tolva = [[-18.1, -17.1, VD - 0.5, VD + 0.5, DH], [-18.95, -16.25, VD - 1.3, VD + 1.3, TH]];
        {
          const [lo, hi] = tolva, P = (q, i) => E(i < 2 ? q[i === 0 ? 0 : 1] : q[i === 2 ? 1 : 0], i === 0 || i === 1 ? q[2] : q[3], q[4]);
          // los cuatro lados inclinados (doble cara); su afuera es hacia afuera del centro de la boca
          const C = E(-17.6, VD, (DH + TH) / 2);
          for (let i = 0; i < 4; i++) {
            const j = (i + 1) % 4, V = [P(lo, i), P(lo, j), P(hi, j), P(hi, i)], m = [0, 1, 2].map((k) => (V[0][k] + V[1][k] + V[2][k] + V[3][k]) / 4 - C[k]);
            cara(solido, V, cMetal.clone().multiplyScalar(1.05), m);
          }
          cj(solido, -19.0, -16.2, VD - 1.35, VD + 1.35, TH - 0.06, TH + 0.04, cMetal, { sinTope: true });   // el borde de la boca
          // la cereza adentro de la tolva, un poco bajo el borde
          const f = 0.72, iu0 = lo[0] + (hi[0] - lo[0]) * f, iu1 = lo[1] + (hi[1] - lo[1]) * f, iv0 = lo[2] + (hi[2] - lo[2]) * f, iv1 = lo[3] + (hi[3] - lo[3]) * f;
          const hf = DH + (TH - DH) * f;
          losa(fruta, iu0, iu1, iv0, iv1, hf, 0.5, 0.5, () => cRoja.clone().multiplyScalar(0.7));
          for (let i = 0, n = 500; i < 7; i++) for (let j = 0; j < 7; j++, n++)
            gema(fruta, oct, E(iu0 + 0.12 + (iu1 - iu0 - 0.24) * (i + 0.5 * hz(n, 66)) / 7, iv0 + 0.12 + (iv1 - iv0 - 0.24) * (j + 0.5 * hz(n, 67)) / 7, hf + 0.05 * hz(n, 68)),
              0.15, 0.17, 0.15, hz(n, 69) * 3, cRoja.clone().multiplyScalar(0.85 + 0.25 * hz(n, 70)), 0.45);
        }
        // la salida de la pulpa al costado y su montón
        barra(solido, E(-17.6, VD - 0.9, 0.95), E(-17.6, VD - 2.3, 0.55), 0.2 * M, cMetal.clone().multiplyScalar(0.85));
        for (let i = 0; i < 9; i++)
          gema(solido, ico, E(-17.6 + (hz(i, 81) - 0.5) * 1.6, VD - 3.0 + (hz(i, 82) - 0.5) * 1.2, H0 + 0.1), 0.55 + 0.35 * hz(i, 83), 0.28 + 0.18 * hz(i, 84), 0.5 + 0.3 * hz(i, 85),
            hz(i, 86) * 3, cPulpa.clone().multiplyScalar(0.85 + 0.3 * hz(i, 87)), 0.2);
        // la salida del grano: una canaleta corta a la primera pila
        {
          const a = E(DU1, VD - 0.28, 1.3), b = E(-14.85, VD - 0.28, 1.16), a2 = E(DU1, VD + 0.28, 1.3), b2 = E(-14.85, VD + 0.28, 1.16);
          cara(solido, [a, b, b2, a2], cMetal, [0, 1, 0]);
          const au = E(DU1, VD - 0.28, 1.46), bu = E(-14.85, VD - 0.28, 1.32), au2 = E(DU1, VD + 0.28, 1.46), bu2 = E(-14.85, VD + 0.28, 1.32);
          cara(solido, [a, b, bu, au], cMetal.clone().multiplyScalar(0.9), null);
          cara(solido, [a2, b2, bu2, au2], cMetal.clone().multiplyScalar(0.9), null);
        }
        // el volante: un aro con cuatro rayos en el costado (gira con t)
        const volante = malla.nueva(), RV = 0.62;
        {
          const T = (a, b, c3) => [a * M, c3 * M, b * M];            // local del volante: a (u), c3 (h), b (a lo ancho)
          const seg = 14;
          for (let i = 0; i < seg; i++) {
            const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg;
            barra(volante, T(Math.cos(t0) * RV, 0, Math.sin(t0) * RV), T(Math.cos(t1) * RV, 0, Math.sin(t1) * RV), 0.05 * M, cOscuro);
          }
          for (let i = 0; i < 4; i++) { const a = TAU * i / 4 + 0.3; barra(volante, T(0, 0, 0), T(Math.cos(a) * RV, 0, Math.sin(a) * RV), 0.035 * M, cOscuro); }
          gema(volante, oct, [0, 0, 0], 0.1, 0.1, 0.1, 0, cMetal, 0.3);
        }
        const gVol = new THREE.Group(), mVol = new THREE.Mesh(malla.geometria(volante), malla.material());
        mVol.frustumCulled = false; mVol.renderOrder = 5; gVol.add(mVol);
        gVol.position.set(...E(-17.6, VD + 1.18, 0.95)); gVol.rotation.y = r; scene.add(gVol);

        // ================= las pilas de fermento: tres tanques de cemento (la primera con la masa de grano, las otras con agua)
        const PU0p = -15, PU1p = -7, PVx = 6.6, ew = 0.25, PH = 1.1;
        const sep = [[-PVx, -PVx + ew], [-2.3, -2.05], [2.05, 2.3], [PVx - ew, PVx]];
        for (const [b0, b1] of sep) cj(solido, PU0p, PU1p, b0, b1, H0, PH, cMuro, { tope: cBorde });
        for (const [a0, a1] of [[PU0p, PU0p + ew], [PU1p - ew, PU1p]]) cj(solido, a0, a1, -PVx + ew, PVx - ew, H0, PH, cMuro, { tope: cBorde });
        losa(fruta, PU0p + ew, PU1p - ew, -PVx + ew, -2.3, 0.9, 0.3, 0.3, (u, v, k) =>
          c.copy(cMuci).multiplyScalar(0.86 + 0.16 * hz(k, 91) + 0.1 * ruido(u, v, 1.2, 92)).clone());

        // ================= el canal de correteo: del frente de la pila del medio al patio, angosto, con el agua corriendo
        const KU0 = PU1p, KU1 = PU0 - 0.05, KW = 0.42, KE = 0.16, KH = 0.6;
        cj(solido, KU0, KU1, -KW - KE, -KW, 0.04, KH, cMuro, { tope: cBorde });
        cj(solido, KU0, KU1, KW, KW + KE, 0.04, KH, cMuro, { tope: cBorde });
        cj(solido, KU0, KU1, -KW, KW, 0.04, 0.2, cMuro);
        // el agua: un shader (aF = metros a lo largo, a lo ancho, velocidad m/s): ondas, un brillo que viaja, granos que flotan
        const ag = { pos: [], f: [], idx: [] };
        const lamina = (u0, u1, v0, v1, h, vel) => {
          const q = ag.pos.length / 3;
          for (const [u, v] of [[u0, v0], [u1, v0], [u1, v1], [u0, v1]]) { const P = E(u, v, h); ag.pos.push(...P); ag.f.push(u - u0, v, vel); }
          ag.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        lamina(KU0 - 0.2, KU1, -KW, KW, KH - 0.14, 1.1);
        const gAg = new THREE.BufferGeometry();
        gAg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(ag.pos), 3));
        gAg.setAttribute("aF", new THREE.BufferAttribute(new Float32Array(ag.f), 3));
        gAg.setIndex(ag.idx);
        const shAgua = (col) => new THREE.ShaderMaterial({
          uniforms: { ...uComun(), uBrillo: { value: 1 }, uLuz: { value: sombra(0, 1, 0) }, cA: { value: col.clone() }, cB: { value: cLuz.clone() }, cG: { value: cPerg.clone() } },
          side: THREE.DoubleSide,
          vertexShader: "attribute vec3 aF; varying vec3 vPos, vF; void main(){ vF = aF; vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: GLSL_COMUN + "uniform float uBrillo, uLuz; uniform vec3 cA, cB, cG; varying vec3 vPos, vF;" +
            "void main(){ float s = vF.x - uT * vF.z, w = vF.y, corre = step(0.5, vF.z);" +
            " float ola = 0.5 + 0.5 * sin(s * 3.1 + w * 4.0) * sin(s * 1.3 - w * 2.6 + 1.7);" +
            " vec3 c = cA * uLuz * (0.84 + 0.26 * ola);" +
            " float fr = fract(s / 1.7 + 0.08 * sin(w * 7.0));" +
            " float rayo = smoothstep(0.5, 0.78, fr) * (1.0 - smoothstep(0.78, 0.97, fr)) * corre;" +
            " c = mix(c, cB, 0.6 * rayo + 0.14 * smoothstep(0.78, 1.0, ola));" +
            " float g = step(0.88, ruido(vec2(s * 3.0, w * 5.0 + 0.5))) * corre;" +
            " c = mix(c, cG * uLuz, 0.9 * g);" +
            " gl_FragColor = vec4(salida(niebla(c * uBrillo, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
        const matCanal = shAgua(cAgua), mCanal = new THREE.Mesh(gAg, matCanal); mCanal.frustumCulled = false; mCanal.renderOrder = 5; scene.add(mCanal);
        // el agua de las dos pilas: ondas lentas (sin corriente)
        const ag2 = ag; ag2.pos = []; ag2.f = []; ag2.idx = [];
        lamina(PU0p + ew, PU1p - ew, -2.05, 2.05, 0.86, 0.12);
        lamina(PU0p + ew, PU1p - ew, 2.3, PVx - ew, 0.86, 0.12);
        const gAp = new THREE.BufferGeometry();
        gAp.setAttribute("position", new THREE.BufferAttribute(new Float32Array(ag2.pos), 3));
        gAp.setAttribute("aF", new THREE.BufferAttribute(new Float32Array(ag2.f), 3));
        gAp.setIndex(ag2.idx);
        const matPila = shAgua(cAguaPila), mPila = new THREE.Mesh(gAp, matPila); mPila.frustumCulled = false; mPila.renderOrder = 5; scene.add(mPila);

        // ================= la sombra de contacto: rectángulos suaves bajo lo que se asienta en la plataforma y el patio
        const so = { pos: [], a: [], idx: [] };
        const sombraRect = (u0, u1, v0, v1, h, pad) => {
          const anillo = (d, a) => [[u0 - d, v0 - d], [u1 + d, v0 - d], [u1 + d, v1 + d], [u0 - d, v1 + d]].map(([u, v]) => ({ P: E(u, v, h), a }));
          const I = anillo(0, 1), O = anillo(pad, 0), q = so.pos.length / 3;
          for (const x of I.concat(O)) { so.pos.push(...x.P); so.a.push(x.a); }
          so.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; so.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
        };
        sombraRect(RU0, RU1, RV0, RV1, H0 + 0.01, 0.9);
        sombraRect(DU0 - 0.3, DU1 + 0.3, VD - 1.2, VD + 1.2, H0 + 0.01, 0.7);
        sombraRect(PU0p, PU1p, -PVx, PVx, H0 + 0.01, 0.8);
        sombraRect(-18.6, -16.6, VD - 3.6, VD - 2.4, H0 + 0.01, 0.7);
        sombraRect(KU0, KU1, -KW - KE, KW + KE, 0.05, 0.4);
        const gS = new THREE.BufferGeometry();
        gS.setAttribute("position", new THREE.BufferAttribute(new Float32Array(so.pos), 3));
        gS.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(so.a), 1));
        gS.setIndex(so.idx);
        const mS = new THREE.Mesh(gS, new THREE.ShaderMaterial({ uniforms: { uK: { value: KS * 0.8 } }, transparent: true, depthWrite: false,
          polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
          vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: "uniform float uK; varying float vA; void main(){ float a = uK * vA * vA; gl_FragColor = vec4(0.0, 0.0, 0.0, a); }" }));
        mS.frustumCulled = false; mS.renderOrder = 4; scene.add(mS);

        // ================= las mallas fijas
        malla.poner(suelo, malla.material({ desfase: 2 }), 2);
        sinTraslado(solido, malla.material({ desfase: 1 }), 3);
        const matPerg = malla.material({ desfase: 2 }); sinTraslado(perg, matPerg, 3);
        const matFruta = malla.material(); sinTraslado(fruta, matFruta, 5);

        // ================= la cereza que baja por la canaleta y cae en la tolva (cada una, una malla que se coloca por t)
        const baya = malla.nueva(); gema(baya, oct, [0, 0, 0], 0.16, 0.19, 0.16, 0, cRoja, 0.5);
        const gB = malla.geometria(baya), matBaya = malla.material(), bayas = [], NB = 22, PER = 2.6;
        for (let j = 0; j < NB; j++) {
          const m = new THREE.Mesh(gB, matBaya); m.frustumCulled = false; m.renderOrder = 6; scene.add(m);
          bayas.push({ m, f0: j / NB + 0.03 * hz(j, 3), dv: (hz(j, 5) - 0.5) * 0.36, rot: hz(j, 6) * TAU });
        }
        const HF = DH + (TH - DH) * 0.72;
        const ponBaya = (b, t) => {
          const f = (((t / PER + b.f0) % 1) + 1) % 1;
          let u, h, k = 1;
          if (f < 0.72) { const q = Math.pow(f / 0.72, 1.35); u = CU0 + 0.2 + (CU1 - CU0 - 0.2) * q; h = ch(u) + 0.17; }
          else { const tau = (f - 0.72) * PER; u = CU1 + 0.55 * tau; h = CH1 + 0.17 + 0.3 * tau - 4.9 * tau * tau; if (h < HF + 0.05) k = 0; }
          const P = E(u, VD + b.dv, h);
          b.m.position.set(P[0], P[1], P[2]); b.m.rotation.set(0, b.rot + t * 4, 0.4); b.m.scale.setScalar(k);
        };

        // ================= quienes rastrillan: persona (catálogo) en su pose `rastrillar` (sombrero de ala y rastrillo en las
        // manos que va y viene; el torso inclinado; pasos cortos al avanzar), agrandada PG para leerse a 35–45 m, con camisa de
        // color que contrasta con el pergamino y una sombra suave (además de la de contacto de la flota). Con 3 personas, la
        // tercera, en la pose `cargar`, sube sacos junto a la pila de recibo (de pie en la plataforma, de cara al muro).
        const gente = [], NP = p.personas, NR = Math.min(NP, 2), PG = 1.45, HG = HP + HS;
        let flCarga = null;
        const camisas = dia ? [tonos.mal.clone(), lin(COL.mar).multiplyScalar(0.72), tonos.bien.clone()]
          : noche ? [lin(COL.costa), tonos.mal.clone(), tonos.secundario.clone().multiplyScalar(0.85)]
          : [tonos.mal.clone(), lin(COL.mar), tonos.bien.clone()];
        const c0 = Math.floor(hz(0, 52) * 3);
        if (NR) {
          const fl = ctx.flota("persona", NR, { tamano: K * PG, lev: HG * K, orden: 6, semilla: (p.semilla * 11 + np * 5) % 997,
            pose: "rastrillar", color: (i) => camisas[(i + c0) % 3] });
          const gSo = new THREE.PlaneGeometry(1, 1); gSo.rotateX(-Math.PI / 2);
          const matSo = new THREE.ShaderMaterial({ uniforms: { uK: { value: KS * 0.55 } }, transparent: true, depthWrite: false,
            polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
            vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: "uniform float uK; varying vec2 vUv; void main(){ float r = length((vUv - 0.5) * 2.0); gl_FragColor = vec4(0.0, 0.0, 0.0, uK * (1.0 - smoothstep(0.3, 1.0, r))); }" });
          const orden = [1, 2, 0, 3];
          for (let i = 0; i < NR; i++) {
            const g = new THREE.Group(), so2 = new THREE.Mesh(gSo, matSo);
            so2.frustumCulled = false; so2.renderOrder = 4; so2.position.set(0.6 * M * PG, 0.02 * M, 0); so2.scale.set(2.6 * M * PG, 1, 1.5 * M * PG); g.add(so2);
            scene.add(g);
            gente.push({ g, vc: FR[orden[i]] + (hz(i, 53) - 0.5) * 0.6, f0: hz(i, 54) });
          }
          gente.fl = fl;
        }
        if (NP >= 3) flCarga = ctx.flota("persona", 1, { tamano: K * PG, lev: H0 * K, orden: 6, semilla: (p.semilla * 7 + np * 3) % 997,
          pose: "cargar", color: () => camisas[(2 + c0) % 3] });
        const LP = FU1 - FU0 - 3.4, VEL = 0.32;
        const ponGente = (t) => {
          gente.forEach((q, i) => {
            const per = 2 * LP / VEL, f = (((t / per + q.f0) % 1) + 1) % 1, g = f < 0.5 ? 2 * f : 2 - 2 * f, dir = f < 0.5 ? 1 : -1;
            const u = FU0 + 1.7 + LP * g, [x, y] = W(u, q.vc), dx = ux * dir, dy = uy * dir;
            gente.fl.poner(i, x, y, dx, dy, 1, 0, VEL);
            q.g.position.set(x, base0 + HG * M, -y); q.g.rotation.y = Math.atan2(dy, dx);
          });
          if (gente.fl) gente.fl.listo();
          if (flCarga) { const [x, y] = W((RU0 + RU1) / 2, RV1 + 1.1); flCarga.poner(0, x, y, uy, -ux, 1, 0, 0); flCarga.listo(); }
        };
        return { id: p.id, matCanal, matPila, matPerg, matFruta, matBaya, mVol, bayas, ponBaya, ponGente, perg: [matPerg] };
      });
    },
    en(t, lista, ctx) {
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? ctx.clamp((b - 1) / 0.9, 0, 1.2) : 0;
        s.matCanal.uniforms.uBrillo.value = 1 + 0.3 * k; s.matPila.uniforms.uBrillo.value = 1 + 0.2 * k;
        s.matPerg.uniforms.uBrillo.value = 1 + 0.25 * k;
        s.matFruta.uniforms.uBrillo.value = 1 + 0.5 * k; s.matBaya.uniforms.uBrillo.value = 1 + 0.6 * k;
        s.mVol.rotation.z = -t * 5.2;
        for (const bb of s.bayas) s.ponBaya(bb, t);
        s.ponGente(t);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
