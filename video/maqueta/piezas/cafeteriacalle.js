// Pieza «cafeteriacalle» (ficha: cafeteriacalle.json; reglas: scripts/maqueta_tipos/cafeteriacalle.py): una cafetería
// GENÉRICA de mostrador abierta a la calle, sin marca ni texto, con su tramo de calle. Centrada en `lugar` (el pie de la
// fachada, al medio) y orientada por `rumbo` (u: de la fachada hacia la calle; v: a su izquierda, a lo largo de la acera).
// El LOCAL (11 m de frente, una planta de 4.4 m con cornisa y pretil) entre dos VECINOS más altos (sin texto ni rótulos):
// abajo la VIDRIERA (vidrio aditivo: se ve adentro) con sus parteluces y su zócalo, la puerta con su marquesina, la franja
// de fachada lisa (sin letras). ADENTRO, a la vista por el vidrio: la barra con sus listones y la vitrina de panes, la caja;
// detrás, la contrabarra con la MÁQUINA DE ESPRESSO (dos cabezales con su portafiltro y su mango, la bandeja con tazas, la
// lanza de vapor, las tazas arriba), el MOLINO (tolva con grano), la CAJA DE DESECHO y las jarras; el azulejo, las repisas
// (tazas y bolsas lisas) y una pizarra con rayas (no letras); tres lámparas colgantes; y la BARISTA (persona, pose atender).
// AFUERA, en la acera de losetas: tres mesitas redondas pegadas a la fachada, cada una con dos sillas (la silla debajo de quien
// se sienta), los CLIENTES sentados con su taza humeante; una SOMBRILLA sobre la tercera mesa; la JARDINERA con sus matas;
// el PASO LIBRE entre las mesas y el bordillo, por donde salen los PASEANTES con su vaso liso (persona, pose sorber, camina);
// un árbol en su alcorque, un basurero y una farola en el bordillo; la calle con su línea discontinua.
// Lo que se mueve (puro de t): la barista atiende, quien sale camina y sorbe, el vapor de las tazas y la lanza de la máquina.
// De noche (ctx.ES.noche): las lámparas y el vidrio encendidos, la luz que cae en la acera y la farola. Sin colores escritos.
(function (MAQ) {
  MAQ.PIEZAS.cafeteriacalle = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, dia = !!ES.dia, TAU = 2 * Math.PI;
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo)
      const kN = noche ? 1.15 : 1;
      const cLoseta = tonos.pavimento.clone().lerp(tonos.muro, 0.35).multiplyScalar(dia ? 0.95 : 1.05);
      const cBord = tonos.pavimento.clone().lerp(lin(COL.costa), 0.3).multiplyScalar(dia ? 1.0 : 1.15);
      const cAsf = tonos.asfalto.clone().multiplyScalar(dia ? 1.0 : 1.1);
      const cPintura = lin(COL.costa).lerp(tonos.pavimento, 0.25).multiplyScalar(dia ? 0.95 : 0.8);
      const cEstuco = tonos.muro.clone().lerp(lin(COL.costa), 0.35).multiplyScalar(dia ? 0.95 : 1.0);
      const cMarco = tonos.linea.clone().lerp(tonos.asfalto, 0.4);
      const cNegro = tonos.linea.clone().lerp(tonos.asfalto, 0.25).multiplyScalar(0.8);
      const cAcero = tonos.pavimento.clone().lerp(lin(COL.costa), 0.45).multiplyScalar(1.12);
      const cMadera = lin(COL.tierra_media).lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(0.8 * kN);
      const cPisoI = lin(COL.tierra_media).lerp(tonos.muro, 0.45).multiplyScalar(0.95 * kN);
      const cParedI = tonos.muro.clone().lerp(lin(COL.costa), 0.55).multiplyScalar(0.92 * kN);
      const cAzulejo = lin(COL.costa).lerp(tonos.muro, 0.2).multiplyScalar(1.02 * kN);
      const cTope = tonos.pavimento.clone().lerp(lin(COL.costa), 0.55).multiplyScalar(kN);
      const cTaza = tonos.secundario.clone().lerp(lin(COL.costa), 0.6).multiplyScalar(noche ? 0.95 : 1.05);
      const cCafe = lin(COL.tierra_media).multiplyScalar(0.3);
      const cGrano = lin(COL.tierra_media).multiplyScalar(0.42);
      const cVerde = tonos.verde.clone().lerp(tonos.campo, 0.3).multiplyScalar(dia ? 0.85 : 0.9);
      const cTierra = lin(COL.tierra_media).multiplyScalar(0.5);
      const cLuz = lin(COL.luces || COL.luz), cVidrio = lin(COL.luz).lerp(tonos.agua, 0.35).lerp(lin(COL.costa), 0.2);
      const familias = [tonos.mal.clone().multiplyScalar(0.72), lin(COL.mar_hondo || COL.mar).multiplyScalar(0.62),
        lin(COL.tierra_media).multiplyScalar(0.8), tonos.linea.clone().lerp(lin(COL.costa), 0.22)];
      const vecinos = [tonos.techo.clone().lerp(tonos.muro, 0.3), tonos.muro.clone().multiplyScalar(0.86), tonos.techo.clone().lerp(lin(COL.tierra_alta), 0.25),
        tonos.muro.clone().lerp(tonos.pavimento, 0.5)];
      const bolsas = [lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.45), lin(COL.costa).multiplyScalar(0.86), lin(COL.tierra_media).multiplyScalar(0.7)];

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const fam = familias[Math.floor(hz(0, 1) * familias.length)];
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
        // una caja en (u, v, h); op.tope: color de la cara de arriba; op.sinTope; op.sinBase (sin la de abajo)
        const cj = (acc, a0, a1, b0, b1, c0, c1, col, op = {}) => {
          const C = E((a0 + a1) / 2, (b0 + b1) / 2, (c0 + c1) / 2);
          const caras = [
            [[a0, b0, c1], [a1, b0, c1], [a1, b1, c1], [a0, b1, c1]],
            [[a0, b0, c0], [a1, b0, c0], [a1, b0, c1], [a0, b0, c1]],
            [[a0, b1, c0], [a1, b1, c0], [a1, b1, c1], [a0, b1, c1]],
            [[a0, b0, c0], [a0, b1, c0], [a0, b1, c1], [a0, b0, c1]],
            [[a1, b0, c0], [a1, b1, c0], [a1, b1, c1], [a1, b0, c1]],
            [[a0, b0, c0], [a1, b0, c0], [a1, b1, c0], [a0, b1, c0]],
          ];
          caras.forEach((q, k) => {
            if ((k === 0 && op.sinTope) || (k === 5 && !op.base)) return;
            const V = q.map((a) => E(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
            cara(acc, V, k === 0 && op.tope ? op.tope : col, m, 1);
          });
        };
        const losa = (acc, u0, u1, v0, v1, h, cu, cv, col) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0);
          for (let i = 0, k = 0; i < nu; i++) for (let j = 0; j < nv; j++, k++) {
            const a = u0 + (u1 - u0) * i / nu, b = u0 + (u1 - u0) * (i + 1) / nu, e = v0 + (v1 - v0) * j / nv, f = v0 + (v1 - v0) * (j + 1) / nv;
            const cc = col((a + b) / 2, (e + f) / 2, k, i, j), q = acc.pos.length / 3;
            for (const [uu, vv] of [[a, e], [b, e], [b, f], [a, f]]) { const P = E(uu, vv, h); acc.pos.push(P[0], P[1], P[2]); acc.col.push(cc.r * l, cc.g * l, cc.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        // un tronco de cono vertical en (u, v): radio r0 abajo (h0) y r1 arriba (h1), con su tapa
        const cono = (acc, u, v, h0, h1, r0, r1, seg, col, tapa, base) => {
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
            const P = [E(u + r0 * Math.cos(a0), v + r0 * Math.sin(a0), h0), E(u + r0 * Math.cos(a1), v + r0 * Math.sin(a1), h0),
              E(u + r1 * Math.cos(a1), v + r1 * Math.sin(a1), h1), E(u + r1 * Math.cos(a0), v + r1 * Math.sin(a0), h1)];
            const O = E(u + Math.cos(am), v + Math.sin(am), (h0 + h1) / 2), C0 = E(u, v, (h0 + h1) / 2);
            cara(acc, P, col, [O[0] - C0[0], (r0 - r1) * M * 0.5, O[2] - C0[2]]);
            if (tapa) { const T0 = E(u, v, h1); cara(acc, [P[3], P[2], T0, T0], tapa, [0, 1, 0]); }
            if (base) { const T0 = E(u, v, h0); cara(acc, [P[0], P[1], T0, T0], base, [0, -1, 0]); }
          }
        };
        const cil = (acc, u, v, h0, h1, rr, seg, col, tapa) => cono(acc, u, v, h0, h1, rr, rr, seg, col, tapa);
        const barra = (acc, A, B, rr, col, lados = 4) => {
          const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
          let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
          for (let i = 0; i < lados; i++) {
            const t0 = TAU * i / lados, t1 = TAU * (i + 1) / lados, o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * rr);
            const va = o(t0), vb = o(t1), nm = o((t0 + t1) / 2);
            cara(acc, [[A[0] + va[0], A[1] + va[1], A[2] + va[2]], [A[0] + vb[0], A[1] + vb[1], A[2] + vb[2]],
              [B[0] + vb[0], B[1] + vb[1], B[2] + vb[2]], [B[0] + va[0], B[1] + va[1], B[2] + va[2]]], col, nm);
          }
        };
        // una mata o una copa: una esfera de caras, aplastada, con el tono por cara
        const ico = new THREE.IcosahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
        const bola = (acc, u, v, h, ru, rh, col, k) => {
          const P0 = E(u, v, h);
          for (let i = 0; i < ico.length; i += 9) {
            const vs = [];
            for (let j = 0; j < 9; j += 3) {
              const w = 1 + 0.12 * (hz(k * 131 + ((i + j) % 97), 5) - 0.5);
              const [x, y] = W(u + ico[i + j] * ru * w, v - ico[i + j + 2] * ru * w);
              vs.push([x, P0[1] + ico[i + j + 1] * rh * w * M, -y]);
            }
            const e1 = [vs[1][0] - vs[0][0], vs[1][1] - vs[0][1], vs[1][2] - vs[0][2]], e2 = [vs[2][0] - vs[0][0], vs[2][1] - vs[0][1], vs[2][2] - vs[0][2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const cx = (vs[0][0] + vs[1][0] + vs[2][0]) / 3 - P0[0], cy = (vs[0][1] + vs[1][1] + vs[2][1]) / 3 - P0[1], cz = (vs[0][2] + vs[1][2] + vs[2][2]) / 3 - P0[2];
            if (nx * cx + ny * cy + nz * cz < 0) { nx = -nx; ny = -ny; nz = -nz; }
            const n = Math.hypot(nx, ny, nz) || 1, sb = sombra(nx / n, ny / n, nz / n);
            c.copy(col).multiplyScalar(sb * (0.86 + 0.24 * hz(k * 977 + i, 6)));
            const q = acc.pos.length / 3;
            for (const X of vs) { acc.pos.push(X[0], X[1], X[2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };
        const quad = (acc, P, col) => { const q = acc.pos.length / 3; for (const X of P) { acc.pos.push(X[0], X[1], X[2]); acc.col.push(col.r, col.g, col.b); } acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3); };

        const H0 = 0.15, UB = -7.5, VL = 5.5, HW = 4.4, EP = 0.3;
        const suelo = malla.nueva(), solido = malla.nueva(), interior = malla.nueva(), vidrio = malla.nueva(), focos = malla.nueva(), luzA = malla.nueva();

        // ================= el suelo: la acera de losetas, el bordillo, la calle con su línea; el piso del local
        const UA = 5.0, UC = 13.5, VA = 11.5;
        losa(suelo, -0.05, UA - 0.18, -VA, VA, H0, 0.6, 0.6, (u, v, k, i, j) => c.copy(cLoseta).multiplyScalar(0.9 + 0.1 * hz(i * 211 + j, 7) + ((i + j) % 2 ? 0.03 : -0.02)).clone());
        cj(solido, -0.05, UA - 0.18, -VA, VA, 0, H0 - 0.003, cLoseta.clone().multiplyScalar(0.8), { sinTope: true });
        cj(solido, UA - 0.18, UA, -VA, VA, 0, H0 + 0.01, cBord, { tope: cBord.clone().multiplyScalar(1.08) });
        losa(suelo, UA, UC, -VA, VA, 0.02, 1.5, 1.5, (u, v, k) => c.copy(cAsf).multiplyScalar(0.92 + 0.12 * hz(k, 8)).clone());
        losa(suelo, UA, UA + 0.45, -VA, VA, 0.025, 0.45, 2, () => cAsf.clone().multiplyScalar(0.8));      // la cuneta
        for (let v = -VA + 1; v < VA - 2; v += 6) losa(suelo, 9.2, 9.35, v, v + 3, 0.03, 0.15, 3, () => cPintura);   // la línea discontinua
        losa(suelo, UC - 0.4, UC - 0.25, -VA, VA, 0.03, 0.15, 6, () => cPintura.clone().multiplyScalar(0.9));         // la orilla de enfrente
        // el piso del local: duela de madera
        losa(interior, UB + 0.3, -EP, -VL + EP, VL - EP, H0 + 0.004, 0.9, 0.18, (u, v, k, i, j) => c.copy(cPisoI).multiplyScalar(0.86 + 0.2 * hz(i * 37 + j * 101, 9)).clone());

        // ================= los vecinos: dos frentes más altos, con ventanas y una cortina metálica; sin rótulos
        const vecino = (v0, v1, alto, col, tipo) => {
          cj(solido, -8.5, 0, v0, v1, 0, alto, col, { tope: col.clone().multiplyScalar(0.9) });
          cj(solido, -0.02, 0.18, v0, v1, alto - 0.35, alto - 0.18, col.clone().multiplyScalar(1.12));       // la cornisa
          cj(solido, 0, 0.06, v0, v1, H0, 0.55, col.clone().multiplyScalar(0.78));                         // el zócalo
          const pisos = Math.floor((alto - 3.4) / 3.0);
          for (let f = 0; f < pisos; f++) {
            const h0 = 4.2 + f * 3.0, n = Math.max(1, Math.round((v1 - v0) / 2.4));
            for (let k = 0; k < n; k++) {
              const vc = v0 + (v1 - v0) * (k + 0.5) / n;
              cj(solido, 0, 0.05, vc - 0.6, vc + 0.6, h0, h0 + 1.6, cMarco);
              quad(vidrio, [E(0.055, vc - 0.52, h0 + 0.08), E(0.055, vc + 0.52, h0 + 0.08), E(0.055, vc + 0.52, h0 + 1.52), E(0.055, vc - 0.52, h0 + 1.52)],
                (noche && hz(k * 7 + f, 10) > 0.55 ? cLuz.clone().multiplyScalar(0.22) : cVidrio.clone().multiplyScalar(0.12)));
              cj(solido, 0, 0.14, vc - 0.7, vc + 0.7, h0 - 0.08, h0, col.clone().multiplyScalar(1.15));      // el alféizar
            }
          }
          if (tipo === 0) {        // la cortina metálica bajada, de costillas
            const a = v0 + 0.8, b = v1 - 0.8;
            cj(solido, 0, 0.12, a - 0.15, b + 0.15, H0, 3.25, cMarco);
            for (let h = H0 + 0.05; h < 2.9; h += 0.12) cj(solido, 0.12, 0.16, a, b, h, h + 0.08, cAcero.clone().multiplyScalar(0.72 + 0.04 * ((h * 10) % 2)));
            cj(solido, 0.12, 0.3, a - 0.1, b + 0.1, 2.95, 3.3, cMarco.clone().multiplyScalar(1.2));
          } else {                 // una puerta cerrada y una ventana baja
            const vm = (v0 + v1) / 2;
            cj(solido, 0, 0.06, vm - 2.0, vm - 0.9, H0, 2.4, cMadera.clone().multiplyScalar(0.8));
            cj(solido, 0, 0.09, vm - 1.95, vm - 0.95, H0 + 0.1, 2.3, cMadera.clone().multiplyScalar(0.7));
            cj(solido, 0, 0.05, vm + 0.2, vm + 2.3, 1.0, 2.5, cMarco);
            quad(vidrio, [E(0.055, vm + 0.28, 1.08), E(0.055, vm + 2.22, 1.08), E(0.055, vm + 2.22, 2.42), E(0.055, vm + 0.28, 2.42)], cVidrio.clone().multiplyScalar(0.1));
          }
        };
        const altoI = 7.6 + 3.0 * Math.floor(hz(2, 11) * 2), altoD = 7.6 + 3.0 * Math.floor(hz(3, 11) * 2);
        vecino(-VA, -VL, altoD, vecinos[Math.floor(hz(4, 12) * vecinos.length)], 0);
        vecino(VL, VA, altoI, vecinos[Math.floor(hz(5, 12) * vecinos.length)], 1);

        // ================= el local: paredes, techo, la fachada con su vidriera, la puerta y la franja lisa
        cj(solido, UB, -EP, -VL, -VL + EP, H0, HW, cEstuco);
        cj(solido, UB, -EP, VL - EP, VL, H0, HW, cEstuco);
        cj(solido, UB, -EP, -VL, VL, HW, HW + 0.2, cEstuco.clone().multiplyScalar(0.9), { tope: tonos.techo.clone().multiplyScalar(0.95), base: true });
        cj(solido, UB, -EP + 0.05, -VL, VL, HW + 0.2, HW + 0.55, cEstuco, { tope: cEstuco.clone().multiplyScalar(1.05) });      // el pretil
        cj(solido, UB + 0.3, -EP - 0.3, -VL + 0.3, VL - 0.3, HW + 0.2, HW + 0.24, tonos.techo.clone().multiplyScalar(0.8));
        cj(solido, -4.6, -3.4, 1.5, 2.6, HW + 0.24, HW + 1.05, cAcero.clone().multiplyScalar(0.85), { tope: cAcero });              // la unidad de aire
        // el muro del frente (u ∈ [−EP, 0]) por tramos de v: [v0, v1, [h0, h1] macizos]
        const DV0 = -4.75, DV1 = -3.15, LV0 = -3.05, LV1 = -2.35, GV0 = -2.05, GV1 = VL - 0.4, HG0 = 0.6, HG1 = 2.95, HD = 2.45;
        const tramos = [[-VL, DV0, [[H0, HW]]], [DV0, DV1, [[HG1, HW]]], [DV1, LV0, [[H0, HW]]], [LV0, LV1, [[HG1, HW]]], [LV1, GV0, [[H0, HW]]],
          [GV0, GV1, [[HG1, HW]]], [GV1, VL, [[H0, HW]]]];
        for (const [a, b, hs] of tramos) for (const [h0, h1] of hs) cj(solido, -EP, 0, a, b, h0, h1, cEstuco);
        // el zócalo de la vidriera (en el color de la casa) y el de la luz lateral
        cj(solido, -EP + 0.05, 0.04, GV0, GV1, H0, HG0, fam, { tope: cMarco });
        cj(solido, -EP + 0.05, 0.04, LV0, LV1, H0, HG0, fam, { tope: cMarco });
        // la franja lisa (sin letras), la cornisa y el remate
        cj(solido, 0, 0.09, -VL + 0.15, VL - 0.15, 3.2, 3.95, fam.clone().multiplyScalar(0.92), { tope: fam });
        cj(solido, 0.09, 0.11, -VL + 0.2, VL - 0.2, 3.25, 3.28, cMarco.clone().multiplyScalar(1.2));
        cj(solido, 0.09, 0.11, -VL + 0.2, VL - 0.2, 3.87, 3.9, cMarco.clone().multiplyScalar(1.2));
        cj(solido, 0, 0.22, -VL - 0.05, VL + 0.05, 4.15, 4.32, cEstuco.clone().multiplyScalar(1.1), { tope: cEstuco.clone().multiplyScalar(1.15), base: true });
        // el vidrio y sus parteluces
        const vidrioCol = noche ? cLuz.clone().multiplyScalar(0.12) : cVidrio.clone().multiplyScalar(dia ? 0.07 : 0.09);
        const pano = (a, b, h0, h1) => {
          const P = [E(-0.12, a, h0), E(-0.12, b, h0), E(-0.12, b, h1), E(-0.12, a, h1)], q = vidrio.pos.length / 3;
          P.forEach((X, j) => { vidrio.pos.push(...X); const cc = vidrioCol.clone().multiplyScalar(j < 2 ? 0.75 : 1.25); vidrio.col.push(cc.r, cc.g, cc.b); });
          vidrio.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          // un reflejo diagonal tenue
          const m0 = a + (b - a) * (0.15 + 0.3 * hz(Math.round(a * 10), 13)), w = (b - a) * 0.12;
          quad(vidrio, [E(-0.115, m0, h0 + 0.1), E(-0.115, m0 + w, h0 + 0.1), E(-0.115, m0 + w + 0.5, h1 - 0.1), E(-0.115, m0 + 0.5, h1 - 0.1)], vidrioCol.clone().multiplyScalar(0.4));
        };
        const parteluces = (a, b, h0, h1, n) => {
          cj(solido, -0.16, -0.06, a, b, h0 - 0.05, h0, cMarco); cj(solido, -0.16, -0.06, a, b, h1, h1 + 0.06, cMarco);
          for (let k = 0; k <= n; k++) { const s = a + (b - a) * k / n; cj(solido, -0.17, -0.05, s - 0.045, s + 0.045, h0, h1, cMarco); }
        };
        pano(GV0, GV1, HG0, HG1); parteluces(GV0, GV1, HG0, HG1, 3);
        cj(solido, -0.16, -0.06, GV0, GV1, 2.42, 2.47, cMarco);                    // el travesaño de la vidriera
        pano(LV0, LV1, HG0, HG1); parteluces(LV0, LV1, HG0, HG1, 1);
        // la puerta: abierta hacia adentro (la hoja contra el derrame), su marco y el montante de vidrio
        cj(solido, -0.2, 0.02, DV0 - 0.06, DV0, H0, HG1, cMarco); cj(solido, -0.2, 0.02, DV1, DV1 + 0.06, H0, HG1, cMarco);
        cj(solido, -0.2, 0.02, DV0, DV1, HD, HD + 0.06, cMarco);
        pano(DV0, DV1, HD + 0.06, HG1);
        cj(solido, -1.25, -0.25, DV1 - 0.06, DV1 - 0.02, H0 + 0.02, HD - 0.02, cMarco);
        quad(vidrio, [E(-1.15, DV1 - 0.065, H0 + 0.2), E(-0.35, DV1 - 0.065, H0 + 0.2), E(-0.35, DV1 - 0.065, HD - 0.12), E(-1.15, DV1 - 0.065, HD - 0.12)], vidrioCol);
        cj(solido, -EP, 0.05, DV0, DV1, H0, H0 + 0.02, cAcero);                     // el umbral
        // la marquesina sobre la puerta y sus dos tensores
        cj(solido, 0, 0.95, DV0 - 0.2, DV1 + 0.2, 2.78, 2.86, cMarco.clone().multiplyScalar(1.1), { tope: cAcero.clone().multiplyScalar(0.8), base: true });
        for (const vv of [DV0 - 0.1, DV1 + 0.1]) barra(solido, E(0.9, vv, 2.86), E(0, vv, 3.15), 0.012 * M, cMarco);
        // dos apliques a los lados de la puerta (de noche, encendidos)
        for (const vv of [DV0 - 0.35, DV1 + 0.35]) { cj(solido, 0, 0.1, vv - 0.06, vv + 0.06, 2.25, 2.5, cMarco); cj(focos, 0.1, 0.16, vv - 0.04, vv + 0.04, 2.28, 2.47, noche ? cLuz : cTaza.clone().multiplyScalar(0.8)); }

        // ================= adentro: la pared del fondo (con azulejo, repisas y pizarra), la contrabarra y la barra
        const UF = -4.55;     // el tabique del fondo (detrás, la cocina: no se ve)
        cj(interior, UF - 0.15, UF, -VL + EP, VL - EP, H0, HW, cParedI);
        // la puerta de la cocina, oscura
        cj(interior, UF, UF + 0.03, -4.6, -3.5, H0, 2.3, cMarco.clone().multiplyScalar(0.7));
        // el azulejo detrás de la contrabarra: hiladas de 0.15 × 0.3 m a matajunta
        for (let fila = 0, h = 1.02; h + 0.15 <= 1.72; h += 0.15, fila++) {
          for (let s = -3.3 + (fila % 2) * 0.15; s < 4.7; s += 0.3) {
            const a = Math.max(-3.3, s + 0.01), b = Math.min(4.7, s + 0.29); if (b - a < 0.05) continue;
            cara(interior, [E(UF + 0.004, a, h + 0.01), E(UF + 0.004, b, h + 0.01), E(UF + 0.004, b, h + 0.14), E(UF + 0.004, a, h + 0.14)],
              cAzulejo.clone().multiplyScalar(0.92 + 0.12 * hz(fila * 97 + Math.round(s * 10), 14)), [ux, 0, -uy]);
          }
        }
        // las repisas: tazas y bolsas lisas de café (sin marca)
        for (const [h, cosa] of [[1.95, 0], [2.4, 1]]) {
          cj(interior, UF, UF + 0.32, -3.2, 4.6, h, h + 0.04, cMadera.clone().multiplyScalar(1.1));
          for (let s = -3.0, j = 0; s < 4.4; s += cosa ? 0.24 : 0.2, j++) {
            if (hz(j + cosa * 50, 15) > 0.85) continue;
            if (cosa) { const t = bolsas[Math.floor(hz(j, 16) * bolsas.length)].clone().multiplyScalar(0.9 + 0.15 * hz(j, 17)); cj(interior, UF + 0.08, UF + 0.24, s - 0.08, s + 0.08, h + 0.04, h + 0.34, t, { tope: t.clone().multiplyScalar(0.85) }); }
            else cil(interior, UF + 0.16, s, h + 0.04, h + 0.13, 0.05, 10, cTaza.clone().multiplyScalar(0.95 + 0.08 * hz(j, 18)), cTaza.clone().multiplyScalar(0.85));
          }
        }
        // la pizarra (rayas de tiza, sin letras)
        cj(interior, UF, UF + 0.05, -1.5, 1.9, 2.95, 3.9, cMarco.clone().multiplyScalar(1.05));
        cj(interior, UF + 0.05, UF + 0.06, -1.42, 1.82, 3.02, 3.83, cNegro.clone().lerp(tonos.verde, 0.15));
        for (let k = 0; k < 6; k++) {
          const h = 3.68 - k * 0.12, a = -1.25 + (k % 3 === 0 ? 0 : 0.15), b = a + 0.9 + 1.4 * hz(k, 19);
          cj(interior, UF + 0.06, UF + 0.065, a, Math.min(1.65, b), h, h + 0.025, cTaza.clone().multiplyScalar(0.75));
        }
        // la contrabarra
        const UC0 = UF, UC1 = UF + 0.68, HCB = 0.95;
        cj(interior, UC0, UC1, -3.3, 4.7, H0, HCB - 0.05, cMadera.clone().multiplyScalar(0.8));
        for (let s = -3.3; s < 4.7; s += 0.6) cj(interior, UC1 - 0.01, UC1 + 0.01, s + 0.03, s + 0.57, H0 + 0.15, HCB - 0.12, cMadera.clone().multiplyScalar(0.92));
        cj(interior, UC0, UC1 + 0.04, -3.32, 4.72, HCB - 0.05, HCB, cTope, { tope: cTope.clone().multiplyScalar(1.05) });
        // ---- la MÁQUINA DE ESPRESSO, mirando a la calle (dos cabezales)
        const MV0 = 0.0, MV1 = 1.1, MU0 = UC0 + 0.1, MU1 = UC0 + 0.6, HM = HCB;
        cj(interior, MU0, MU1, MV0, MV1, HM, HM + 0.5, cAcero, { tope: cAcero.clone().multiplyScalar(1.08) });
        cj(interior, MU1, MU1 + 0.01, MV0 + 0.05, MV1 - 0.05, HM + 0.3, HM + 0.46, cAcero.clone().multiplyScalar(0.85));      // el panel del frente
        cj(interior, MU0 - 0.01, MU1 + 0.01, MV0 - 0.02, MV0 + 0.04, HM, HM + 0.5, fam.clone().multiplyScalar(0.9));          // los costados
        cj(interior, MU0 - 0.01, MU1 + 0.01, MV1 - 0.04, MV1 + 0.02, HM, HM + 0.5, fam.clone().multiplyScalar(0.9));
        cj(interior, MU1, MU1 + 0.2, MV0 + 0.05, MV1 - 0.05, HM, HM + 0.05, cNegro, { tope: cAcero.clone().multiplyScalar(0.7) });     // la bandeja de goteo
        for (const [i, vv] of [[0, MV0 + 0.3], [1, MV1 - 0.3]]) {
          cil(interior, MU1 + 0.08, vv, HM + 0.27, HM + 0.36, 0.065, 14, cAcero.clone().multiplyScalar(1.1), cAcero);          // el cabezal
          cil(interior, MU1 + 0.08, vv, HM + 0.2, HM + 0.27, 0.055, 14, cNegro, cNegro);                                        // el portafiltro
          barra(interior, E(MU1 + 0.12, vv, HM + 0.235), E(MU1 + 0.32, vv + (i ? 0.05 : -0.05), HM + 0.215), 0.016 * M, cNegro, 6);  // su mango
          cil(interior, MU1 + 0.08, vv, HM + 0.05, HM + 0.12, 0.04, 12, cTaza, cCafe);                                          // la taza debajo
        }
        cil(interior, MU1 + 0.03, MV0 + 0.55, HM + 0.38, HM + 0.42, 0.04, 10, cNegro, cTaza);       // el manómetro
        barra(interior, E(MU1 + 0.02, MV1 - 0.06, HM + 0.36), E(MU1 + 0.16, MV1 + 0.04, HM + 0.1), 0.01 * M, cAcero.clone().multiplyScalar(1.2), 6);   // la lanza de vapor
        cj(interior, MU0 + 0.03, MU1 - 0.03, MV0 + 0.03, MV1 - 0.03, HM + 0.5, HM + 0.53, cAcero.clone().multiplyScalar(0.9));  // el calientatazas
        for (let k = 0; k < 6; k++) cil(interior, MU0 + 0.15 + (k % 2) * 0.2, MV0 + 0.18 + Math.floor(k / 2) * 0.36, HM + 0.53, HM + 0.6, 0.04, 10, cTaza, cTaza.clone().multiplyScalar(0.9));
        // ---- el MOLINO: cuerpo, cuello, tolva con grano y la boca
        const GU = UC0 + 0.32, GVv = 1.55;
        cj(interior, GU - 0.13, GU + 0.13, GVv - 0.12, GVv + 0.12, HM, HM + 0.36, cNegro.clone().multiplyScalar(1.3), { tope: cNegro });
        cil(interior, GU, GVv, HM + 0.36, HM + 0.42, 0.07, 14, cAcero, null);
        cono(interior, GU, GVv, HM + 0.42, HM + 0.7, 0.07, 0.15, 16, cVidrio.clone().lerp(cGrano, 0.55), cGrano);
        cj(interior, GU + 0.13, GU + 0.2, GVv - 0.04, GVv + 0.04, HM + 0.18, HM + 0.26, cAcero);
        cj(interior, GU + 0.13, GU + 0.24, GVv - 0.08, GVv + 0.08, HM, HM + 0.03, cAcero.clone().multiplyScalar(0.8));
        // ---- la CAJA DE DESECHO (con su barra de golpe) y las jarras de leche
        const KVv = -0.45;
        cj(interior, UC0 + 0.25, UC0 + 0.5, KVv - 0.12, KVv + 0.12, HM, HM + 0.15, cNegro.clone().multiplyScalar(1.2), { tope: cNegro.clone().multiplyScalar(0.6) });
        barra(interior, E(UC0 + 0.375, KVv - 0.12, HM + 0.15), E(UC0 + 0.375, KVv + 0.12, HM + 0.15), 0.018 * M, cAcero, 6);
        for (const vv of [2.0, 2.18]) cono(interior, UC0 + 0.4, vv, HM, HM + 0.14, 0.05, 0.06, 12, cAcero.clone().multiplyScalar(1.15), cAcero);
        // ---- la BARRA del frente: listones, tope de piedra, la vitrina de panes y la caja
        const BU0 = -2.35, BU1 = -1.75, BV0 = -1.6, BV1 = 4.7, HB = 1.0;
        cj(interior, BU0, BU1, BV0, BV1, H0, HB - 0.05, cMadera, { tope: cMadera });
        for (let s = BV0 + 0.02; s < BV1 - 0.06; s += 0.14) cj(interior, BU1, BU1 + 0.025, s, s + 0.11, H0 + 0.12, HB - 0.08, cMadera.clone().multiplyScalar(0.92 + 0.16 * hz(Math.round(s * 10), 20)));
        cj(interior, BU1 - 0.02, BU1 + 0.03, BV0, BV1, H0, H0 + 0.12, cNegro);
        cj(interior, BU0 - 0.05, BU1 + 0.1, BV0 - 0.05, BV1 + 0.05, HB - 0.05, HB, cTope, { tope: cTope.clone().multiplyScalar(1.08) });
        // la vitrina de panes
        const PV0 = 3.0, PV1 = 4.5;
        cj(interior, BU0 + 0.05, BU1 - 0.02, PV0, PV1, HB, HB + 0.06, cMarco);
        for (const vv of [PV0, PV1]) cj(interior, BU0 + 0.05, BU1 - 0.02, vv - 0.02, vv + 0.02, HB, HB + 0.42, cMarco);
        cj(interior, BU0 + 0.05, BU1 - 0.02, PV0, PV1, HB + 0.42, HB + 0.45, cMarco);
        quad(vidrio, [E(BU1 - 0.02, PV0, HB + 0.06), E(BU1 - 0.02, PV1, HB + 0.06), E(BU1 - 0.02, PV1, HB + 0.42), E(BU1 - 0.02, PV0, HB + 0.42)], vidrioCol.clone().multiplyScalar(0.9));
        cj(interior, BU0 + 0.08, BU1 - 0.05, PV0 + 0.04, PV1 - 0.04, HB + 0.24, HB + 0.26, cVidrio.clone().multiplyScalar(0.5));
        for (let k = 0; k < 14; k++) {
          const fila = k % 2, vv = PV0 + 0.14 + (Math.floor(k / 2)) * 0.19, hh = HB + (fila ? 0.3 : 0.11);
          bola(interior, (BU0 + BU1) / 2 + 0.03 * (hz(k, 21) - 0.5), vv, hh, 0.07, 0.04, lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.3 + 0.4 * hz(k, 22)).multiplyScalar(kN), 300 + k);
        }
        // la caja (una pantalla sin nada escrito) y una pila de vasos para llevar
        cj(interior, -2.3, -2.0, -1.2, -0.85, HB, HB + 0.08, cNegro);
        barra(interior, E(-2.15, -1.02, HB + 0.08), E(-2.12, -1.02, HB + 0.3), 0.02 * M, cNegro);
        cj(interior, -2.18, -2.13, -1.18, -0.86, HB + 0.25, HB + 0.45, cNegro.clone().multiplyScalar(1.2));
        cj(focos, -2.13, -2.12, -1.15, -0.89, HB + 0.28, HB + 0.42, noche ? cVidrio.clone().multiplyScalar(0.9) : cVidrio.clone().multiplyScalar(0.55));
        for (const [vv, n] of [[-0.45, 7], [-0.3, 5]]) for (let k = 0; k < n; k++) cono(interior, -2.05, vv, HB + k * 0.035, HB + k * 0.035 + 0.12, 0.035, 0.045, 10, cTaza.clone().multiplyScalar(0.96), k === n - 1 ? cTaza.clone().multiplyScalar(0.8) : null);
        // las tres lámparas colgantes sobre la barra
        for (const vv of [-0.2, 1.6, 3.4]) {
          barra(interior, E(-2.05, vv, HW), E(-2.05, vv, 2.62), 0.008 * M, cNegro);
          cono(interior, -2.05, vv, 2.42, 2.62, 0.2, 0.05, 16, cNegro.clone().lerp(fam, 0.3), null, noche ? cLuz.clone().multiplyScalar(0.8) : cNegro);
          cil(focos, -2.05, vv, 2.37, 2.43, 0.05, 10, noche ? cLuz : cTaza.clone().multiplyScalar(0.7), noche ? cLuz : null);
        }

        // ================= afuera: las mesitas, las sillas, la sombrilla, la jardinera, el árbol, el basurero, la farola
        const UT = 1.05, MESAS = [-0.95, 1.55, 4.05], HT = 0.74;
        const asientos = [];   // [u, v, dx, dy] de la persona sentada (el origen 0.08 detrás del centro del asiento)
        const muebles = malla.nueva();
        const silla = (u, v, du, dv, k) => {      // (du, dv): hacia la mesa
          const col = fam.clone().lerp(cNegro, 0.35).multiplyScalar(0.95 + 0.1 * hz(k, 23));
          const pu = -dv, pv = du;               // a lo ancho
          const P = (a, b) => [u + du * a + pu * b, v + dv * a + pv * b];
          const sq = (a0, a1, b0, b1, h0, h1, cc) => { const [x0, y0] = P(a0, b0), [x1, y1] = P(a1, b1); cj(muebles, Math.min(x0, x1), Math.max(x0, x1), Math.min(y0, y1), Math.max(y0, y1), h0, h1, cc); };
          sq(-0.21, 0.21, -0.21, 0.21, H0 + 0.37, H0 + 0.41, col);                                   // el asiento
          for (const [a, b] of [[-0.18, -0.18], [-0.18, 0.18], [0.18, -0.18], [0.18, 0.18]]) {
            const [x, y] = P(a, b); barra(muebles, E(x, y, H0), E(x, y, H0 + 0.37), 0.016 * M, cNegro);
          }
          for (const b of [-0.18, 0.18]) { const [x, y] = P(-0.2, b); barra(muebles, E(x, y, H0 + 0.41), E(x, y, H0 + 0.84), 0.016 * M, cNegro); }
          for (const h of [0.6, 0.76]) sq(-0.22, -0.19, -0.2, 0.2, H0 + h, H0 + h + 0.06, col);       // el respaldo de dos tablillas
        };
        const tazasMesa = [];
        MESAS.forEach((vT, m) => {
          cil(muebles, UT, vT, H0, H0 + 0.03, 0.22, 14, cNegro, cNegro);
          cil(muebles, UT, vT, H0 + 0.03, H0 + HT - 0.03, 0.03, 8, cNegro, null);
          cil(muebles, UT, vT, H0 + HT - 0.03, H0 + HT, 0.34, 20, cAcero.clone().multiplyScalar(0.85), cTope.clone().multiplyScalar(1.05));
          for (const s of [-1, 1]) {
            const sv = vT + s * 0.6;               // el centro del asiento
            silla(UT, sv, 0, -s, m * 2 + (s > 0 ? 1 : 0));
            asientos.push([UT, sv + s * 0.08, 0, -s, m, s]);
          }
        });
        // la sombrilla sobre la tercera mesa: mástil, copa de 16 paños con sus varillas y su faldón
        const SU = UT, SV = MESAS[2], HS0 = 2.15, HS1 = 2.6, RS = 1.3;
        barra(muebles, E(SU, SV, H0 + HT), E(SU, SV, HS1 + 0.12), 0.022 * M, cAcero, 6);
        const lona = fam.clone().lerp(lin(COL.costa), 0.12);
        for (let i = 0; i < 16; i++) {
          const a0 = TAU * i / 16, a1 = TAU * (i + 1) / 16;
          const A = E(SU + RS * Math.cos(a0), SV + RS * Math.sin(a0), HS0), B = E(SU + RS * Math.cos(a1), SV + RS * Math.sin(a1), HS0), T0 = E(SU, SV, HS1);
          cara(muebles, [A, B, T0, T0], lona.clone().multiplyScalar(i % 2 ? 1 : 0.93), [0, 1, 0]);
          const A2 = E(SU + RS * Math.cos(a0), SV + RS * Math.sin(a0), HS0 - 0.16), B2 = E(SU + RS * Math.cos(a1), SV + RS * Math.sin(a1), HS0 - 0.16);
          const am = (a0 + a1) / 2;
          cara(muebles, [A, B, B2, A2], lona.clone().multiplyScalar(0.85), [Math.cos(am) * ux - Math.sin(am) * uy, 0, -(Math.cos(am) * uy + Math.sin(am) * ux)]);
          if (i % 2 === 0) barra(muebles, E(SU, SV, HS1 - 0.35), E(SU + RS * 0.6 * Math.cos(a0), SV + RS * 0.6 * Math.sin(a0), HS0 + 0.12), 0.008 * M, cAcero, 4);
        }
        cil(muebles, SU, SV, HS1, HS1 + 0.1, 0.05, 10, lona.clone().multiplyScalar(0.8), lona);
        // la jardinera pegada a la fachada, con tierra y matas
        const JU0 = 0.12, JU1 = 0.7, JV0 = 5.7, JV1 = 7.6;
        cj(muebles, JU0, JU1, JV0, JV1, H0, H0 + 0.55, cMadera.clone().multiplyScalar(0.85), { tope: cMadera });
        for (let s = JV0 + 0.05; s < JV1 - 0.05; s += 0.16) cj(muebles, JU1, JU1 + 0.02, s, s + 0.12, H0 + 0.04, H0 + 0.5, cMadera.clone().multiplyScalar(0.78 + 0.12 * hz(Math.round(s * 10), 24)));
        cj(muebles, JU0 + 0.04, JU1 - 0.04, JV0 + 0.04, JV1 - 0.04, H0 + 0.48, H0 + 0.52, cTierra);
        for (let k = 0; k < 6; k++) bola(muebles, (JU0 + JU1) / 2 + 0.08 * (hz(k, 25) - 0.5), JV0 + 0.25 + k * 0.29, H0 + 0.72, 0.24 + 0.06 * hz(k, 26), 0.3 + 0.12 * hz(k, 27), cVerde.clone().multiplyScalar(0.85 + 0.25 * hz(k, 28)), 400 + k);
        // un macetero junto a la puerta
        cono(muebles, 0.35, DV0 - 0.5, H0, H0 + 0.5, 0.2, 0.26, 14, cTierra.clone().lerp(tonos.mal, 0.25).multiplyScalar(1.4), cTierra);
        bola(muebles, 0.35, DV0 - 0.5, H0 + 0.85, 0.26, 0.42, cVerde.clone().multiplyScalar(1.05), 420);
        // el árbol en su alcorque, el basurero y la farola, en la franja del bordillo
        const AU = 4.25, AV = -8.2;
        cj(muebles, AU - 0.55, AU + 0.55, AV - 0.55, AV + 0.55, H0 - 0.002, H0 + 0.02, cTierra, { tope: cTierra.clone().multiplyScalar(0.9) });
        cono(muebles, AU, AV, H0, 2.6, 0.13, 0.09, 10, lin(COL.tierra_media).multiplyScalar(0.55), null);
        for (let k = 0; k < 4; k++) bola(muebles, AU + 0.7 * Math.cos(k * 1.9), AV + 0.7 * Math.sin(k * 1.9), 3.3 + 0.4 * hz(k, 29), 1.1 + 0.3 * hz(k, 30), 0.9 + 0.2 * hz(k, 31), cVerde.clone().multiplyScalar(0.8 + 0.25 * hz(k, 32)), 440 + k);
        cono(muebles, 4.4, -5.9, H0, H0 + 0.9, 0.24, 0.27, 14, cNegro.clone().lerp(fam, 0.2), cNegro);
        const FU = 4.55, FV = 8.6;
        cono(muebles, FU, FV, H0, H0 + 0.5, 0.12, 0.08, 10, cNegro, null);
        barra(muebles, E(FU, FV, H0 + 0.5), E(FU, FV, 4.6), 0.045 * M, cNegro, 8);
        barra(muebles, E(FU, FV, 4.55), E(FU - 0.8, FV, 4.75), 0.03 * M, cNegro, 6);
        cono(muebles, FU - 0.85, FV, 4.55, 4.78, 0.24, 0.08, 14, cNegro, null, noche ? cLuz : cNegro);
        cil(focos, FU - 0.85, FV, 4.52, 4.56, 0.12, 12, noche ? cLuz : cTaza.clone().multiplyScalar(0.7), noche ? cLuz : null);

        // ================= las tazas de los clientes (una por quien se sienta: aparecen con él)
        const NC = clamp(p.clientes | 0, 0, 6), ORDEN = [0, 5, 2, 1, 4, 3];   // a quién se sienta primero: mesa 0, 2, 1…
        const ocupados = ORDEN.slice(0, NC).map((k) => asientos[k]);
        for (const [u, v, , dy, m, s] of ocupados) {
          const tv = MESAS[m] + s * 0.17, tu = UT + 0.06 * (hz(m * 2 + s, 33) - 0.5);
          cil(muebles, tu, tv, H0 + HT, H0 + HT + 0.008, 0.075, 14, cTaza.clone().multiplyScalar(0.9), cTaza);                // el plato
          cono(muebles, tu, tv, H0 + HT + 0.008, H0 + HT + 0.09, 0.04, 0.05, 14, cTaza, cCafe);                                 // la taza
          barra(muebles, E(tu + 0.05, tv, H0 + HT + 0.07), E(tu + 0.07, tv, H0 + HT + 0.03), 0.008 * M, cTaza);               // el asa
          tazasMesa.push([tu, tv, H0 + HT + 0.09]);
        }

        // ================= la luz: de noche, la que sale por la vidriera a la acera, la de las lámparas y la farola
        const charco = (u0, u1, v0, v1, col, h = H0 + 0.006) => {
          const cu = (u0 + u1) / 2, cv = (v0 + v1) / 2, q = luzA.pos.length / 3, P = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]];
          for (const [a, b] of P) { luzA.pos.push(...E(cu + (a - cu) * 0.6, cv + (b - cv) * 0.75, h)); luzA.col.push(col.r, col.g, col.b); }
          for (const [a, b] of P) { luzA.pos.push(...E(a, b, h)); luzA.col.push(0, 0, 0); }
          luzA.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; luzA.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
        };
        if (noche) {
          charco(-0.05, 2.6, GV0 - 0.4, GV1 + 0.4, cLuz.clone().multiplyScalar(0.07));
          charco(-0.05, 1.8, DV0 - 0.3, DV1 + 0.3, cLuz.clone().multiplyScalar(0.06));
          charco(FU - 2.6, FU + 0.9, FV - 1.8, FV + 1.8, cLuz.clone().multiplyScalar(0.08));
          charco(-3.2, -0.6, -1.0, 4.4, cLuz.clone().multiplyScalar(0.05), H0 + 0.01);
          charco(-2.4, -1.7, -1.6, 4.7, cLuz.clone().multiplyScalar(0.06), HB + 0.004);
        } else {
          charco(-3.4, -0.4, -2.0, 4.8, cLuz.clone().multiplyScalar(dia ? 0.025 : 0.03), H0 + 0.01);   // la luz del local, tenue
        }

        // ================= la sombra de contacto bajo lo que se asienta
        const KS = ctx.CFG.sombra_contacto || (dia ? 0.4 : 0.22);
        const so = { pos: [], a: [], idx: [] };
        const sombraRect = (u0, u1, v0, v1, pad, h = H0) => {
          const anillo = (d, al) => [[u0 - d, v0 - d], [u1 + d, v0 - d], [u1 + d, v1 + d], [u0 - d, v1 + d]].map(([u, v]) => ({ P: E(u, v, h + 0.012), a: al }));
          const I = anillo(0, 1), O = anillo(pad, 0), q = so.pos.length / 3;
          for (const x of I.concat(O)) { so.pos.push(...x.P); so.a.push(x.a); }
          so.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; so.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
        };
        for (const vT of MESAS) sombraRect(UT - 0.3, UT + 0.3, vT - 0.85, vT + 0.85, 0.35);
        sombraRect(JU0, JU1, JV0, JV1, 0.3); sombraRect(0, 0.05, -VL, VL, 0.6); sombraRect(0, 0.05, -VA, -VL, 0.5); sombraRect(0, 0.05, VL, VA, 0.5);
        sombraRect(BU0, BU1, BV0, BV1, 0.35); sombraRect(UC0, UC1, -3.3, 4.7, 0.35);
        sombraRect(SU - 1.0, SU + 1.0, SV - 1.0, SV + 1.0, 0.6);
        const gS = new THREE.BufferGeometry();
        gS.setAttribute("position", new THREE.BufferAttribute(new Float32Array(so.pos), 3));
        gS.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(so.a), 1));
        gS.setIndex(so.idx);
        const mS = new THREE.Mesh(gS, new THREE.ShaderMaterial({ uniforms: { uK: { value: KS * 0.7 } }, transparent: true, depthWrite: false,
          polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
          vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: "uniform float uK; varying float vA; void main(){ float a = uK * vA * vA; gl_FragColor = vec4(0.0, 0.0, 0.0, a); }" }));
        mS.frustumCulled = false; mS.renderOrder = 4; scene.add(mS);

        // ================= las mallas fijas
        const sinTraslado = (acc, mat, orden) => { const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        const matSuelo = malla.material({ desfase: 2 }), matSol = malla.material({ desfase: 1 }), matInt = malla.material({ desfase: 1 }), matMue = malla.material();
        malla.poner(suelo, matSuelo, 2);
        sinTraslado(solido, matSol, 3);
        sinTraslado(interior, matInt, 3);
        sinTraslado(muebles, matMue, 5);
        const matFoc = malla.material(); sinTraslado(focos, matFoc, 5); matFoc.uniforms.uBrillo.value = noche ? 1.8 : 1.0;
        sinTraslado(luzA, malla.material({ aditivo: true, desfase: 4 }), 4);
        sinTraslado(vidrio, malla.material({ aditivo: true }), 8);

        // ================= el vapor de las tazas y de la lanza de la máquina: puntos que se calculan de t
        const NV = tazasMesa.length * 3, NL = 10, NPT = Math.max(1, NV + NL);
        const gP = new THREE.BufferGeometry(), posP = new Float32Array(NPT * 3), aP = new Float32Array(NPT);
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 1));
        const cVapor = lin(COL.costa).lerp(tonos.secundario, 0.3);
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cB: { value: cVapor } }, transparent: true, depthWrite: false,
          vertexShader: "attribute float aK; uniform float uPx, uTam; varying float vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " gl_PointSize = aK > 0.0 ? clamp(0.1 * uTam * uPx / max(1e-3, -mv.z), 1.5, 22.0) : 0.0; }",
          fragmentShader: "uniform vec3 cB; varying float vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = cB; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK * (1.0 - smoothstep(0.2, 1.0, r)) * 0.55; gl_FragColor = vec4(s, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);
        const LANZA = [MU1 + 0.16, MV1 + 0.04, HM + 0.1], FL = hz(7, 34);
        const vapor = (t) => {
          let j = 0;
          for (let i = 0; i < NV; i++, j++) {
            const tz = tazasMesa[Math.floor(i / 3)], q = (((t / 2.6 + hz(i, 35) + (i % 3) / 3) % 1) + 1) % 1;
            const P = E(tz[0] + 0.03 * Math.sin(TAU * (q + hz(i, 36))), tz[1] + 0.03 * Math.cos(TAU * q * 1.3), tz[2] + 0.02 + 0.32 * q);
            posP.set(P, j * 3); aP[j] = Math.sin(Math.PI * q) * 0.8;
          }
          // la lanza: un soplo de 1.6 s cada 7 s
          const f = (((t / 7 + FL) % 1) + 1) % 1, on = f < 0.23 ? Math.sin(Math.PI * f / 0.23) : 0;
          for (let i = 0; i < NL; i++, j++) {
            const q = (((t / 0.9 + i / NL) % 1) + 1) % 1, a = TAU * hz(i, 37);
            const P = E(LANZA[0] + 0.06 * q * Math.cos(a), LANZA[1] + 0.06 * q * Math.sin(a), LANZA[2] + 0.05 + 0.4 * q);
            posP.set(P, j * 3); aP[j] = on * Math.sin(Math.PI * q) * 0.9;
          }
          gP.attributes.position.needsUpdate = true; gP.attributes.aK.needsUpdate = true;
        };

        // ================= la gente: la barista (atender), los clientes sentados y quienes salen con su vaso (sorber, caminan)
        const NPA = clamp(p.paseantes | 0, 0, 3), NPER = 1 + NC + NPA;
        const camisas = [tonos.mal.clone().multiplyScalar(0.9), lin(COL.mar).multiplyScalar(0.8), tonos.bien.clone().multiplyScalar(0.9),
          lin(COL.costa).multiplyScalar(0.85), tonos.medio.clone().multiplyScalar(0.9), lin(COL.tierra_media).multiplyScalar(0.85), tonos.secundario.clone()];
        const flP = ctx.flota("persona", NPER, { tamano: K, lev: H0 * K, orden: 6, semilla: (p.semilla * 11 + np * 5) % 991,
          color: (i) => (i === 0 ? cNegro.clone().multiplyScalar(1.6) : camisas[(i + Math.floor(hz(1, 38) * camisas.length)) % camisas.length]),
          pose: (i) => (i === 0 ? "atender" : i <= NC ? { nombre: "sentado", banco: false } : "sorber") });
        // el recorrido de quien sale: de adentro, por la puerta, al paso libre y por la acera hasta la orilla
        const VEL = 1.15, caminos = [];
        for (let i = 0; i < NPA; i++) {
          const lado = i % 2 ? -1 : 1, uL = 2.75 + 0.7 * hz(i, 39);
          const pts = [[-1.4, (DV0 + DV1) / 2], [0.3, (DV0 + DV1) / 2], [uL, (DV0 + DV1) / 2 + lado * 0.6], [uL, lado * 11.0]];
          const L = [0]; for (let k = 1; k < pts.length; k++) L.push(L[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
          caminos.push({ pts, L, tot: L[L.length - 1], ciclo: L[L.length - 1] + 7, fase: 0.12 + i / Math.max(1, NPA) });
        }
        const enCam = (C, s) => {
          s = clamp(s, 0, C.tot);
          for (let k = 1; k < C.pts.length; k++) if (s <= C.L[k] || k === C.pts.length - 1) {
            const q = (s - C.L[k - 1]) / ((C.L[k] - C.L[k - 1]) || 1), A = C.pts[k - 1], B = C.pts[k];
            return [A[0] + (B[0] - A[0]) * q, A[1] + (B[1] - A[1]) * q];
          }
          return C.pts[0];
        };
        return { id: p.id, flP, W, E, NC, NPA, ocupados, caminos, enCam, VEL, matP, vapor, ux, uy, M,
          mats: [matSol, matInt, matMue, matSuelo], matFoc, noche };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) m.uniforms.uBrillo.value = 1 + 0.35 * k;
        s.flP.mesh.material.uniforms.uBrillo.value = 1 + 0.25 * k;
        // la barista, detrás de la barra, mirando a la calle
        { const [x, y] = s.W(-2.95, 0.6); s.flP.poner(0, x, y, s.ux, s.uy, 1, 0, 0); }
        // los clientes sentados, mirando a su mesa
        s.ocupados.forEach(([u, v, du, dv], i) => {
          const [x, y] = s.W(u, v), dx = du * s.ux - dv * s.uy, dy = du * s.uy + dv * s.ux;
          s.flP.poner(1 + i, x, y, dx, dy, 1, 0, 0);
        });
        // quienes salen con su vaso: la posición es función de t (y de su fase), el rumbo de la tangente
        s.caminos.forEach((C, i) => {
          const sc = ((((t * s.VEL) / C.ciclo + C.fase) % 1) + 1) % 1 * C.ciclo;
          const vis = sc <= C.tot;
          const [u, v] = s.enCam(C, sc), [u1, v1] = s.enCam(C, sc + 0.35), [u0, v0] = s.enCam(C, sc - 0.35);
          let du = u1 - u0, dv = v1 - v0; const l = Math.hypot(du, dv) || 1; du /= l; dv /= l;
          const kk = vis ? clamp(sc / 0.4, 0, 1) * clamp((C.tot - sc) / 0.8, 0, 1) : 0;
          const [x, y] = s.W(u, v);
          s.flP.poner(1 + s.NC + i, x, y, du * s.ux - dv * s.uy, du * s.uy + dv * s.ux, kk, 0, vis ? s.VEL : 0);
        });
        s.flP.listo();
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.vapor(t);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
