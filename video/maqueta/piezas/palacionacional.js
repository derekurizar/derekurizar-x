// Pieza «palacionacional» (ficha: palacionacional.json; reglas: scripts/maqueta_tipos/palacionacional.py): el Palacio
// Nacional de la Cultura SIMPLIFICADO como un volumen de 127 × 70 × 30 m, centrado en `lugar` (el centro de su planta) y
// orientado por `rumbo` (u: de la planta hacia la fachada que da a la plaza; v: a su izquierda, a lo largo de esa fachada).
// Solo lo que la referencia visual verificó: un edificio VERDE (el tono es del estilo, no un dato), de 30 m, tres pisos
// sobre el suelo y la terraza (sin torre ni reloj), con fachadas trabajadas y detalle decorativo genérico; junto a una plaza.
// Lo demás es genérico: el volumen se arma con un cuerpo central y cuatro pabellones de esquina apenas salientes (1.5 m),
// zócalo, pilastras, cordones entre pisos, ventanas en arco abajo, con balcón en el primer piso y con marco en el segundo,
// un friso de rombos y dentículos bajo la cornisa, balaustrada en la terraza y áticos en los pabellones. No se dibujan
// patios (su número y su forma no están verificados): la terraza va cerrada. Sin texto, sin escudos, sin banderas.
// CRISTAL (`cristal`, 0–1; `cristal_desde` y `cristal_dur` lo animan): las caras se vuelven translúcidas y quedan las
// aristas de la caja (127 × 70 × 30) con un halo de contraste (la de arriba, a 30 m, la más gruesa), un volumen liso
// translúcido del mismo tamaño y las líneas de los pisos, para medir lo que se pone adentro; `aristas` (0–1) dice cuánto
// pesan. «resaltar» la pieza la tiñe y enciende sus aristas en el acento. `gente_tamano` (1–2) agranda a la gente.
// EL ENTORNO (`entorno`): la acera alrededor; al frente, una calle de adoquín, la acera de enfrente y una franja de plaza
// con bancas, farolas y árboles (mobiliario genérico, sin ventas ni palomas); a los lados y atrás, calles de asfalto.
// CON VIDA (puro de t): gente que camina por la acera de enfrente (y alguna de pie en la plaza). De noche (ctx.ES.noche):
// ventanas encendidas al azar fijo y farolas con su charco de luz. Sin colores escritos.
(function (MAQ) {
  const DU = 35, DV = 63.5, H0 = 0.15, HZ = 1.4, F1 = 10, F2 = 18.5, HC = 26.6, HR = 27.4, HP = 29.0, HA = 29.6, HT = 30;
  const RE = 1.5, PAB = 12, CEN = 15;
  const AC = 6, CA = 10, AE = 6, PZ = 30, AR = 4, CR = 10, VX = 80;
  const UA = DU + AC, UC = UA + CA, UE = UC + AE, UP = UE + PZ;
  const suave = (x) => x * x * (3 - 2 * x);
  MAQ.PIEZAS.palacionacional = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, dia = !!ES.dia, TAU = 2 * Math.PI;
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo; el verde del palacio sale del tono «bien» con el muro: «color verde», sin tono exacto)
      const cVerde = tonos.bien.clone().lerp(tonos.muro, 0.4).multiplyScalar(dia ? 0.95 : 1.1);
      const cMold = cVerde.clone().lerp(lin(COL.costa), 0.32).multiplyScalar(1.06);
      const cPil = cVerde.clone().lerp(cMold, 0.45);
      const cZoc = cVerde.clone().multiplyScalar(0.6);
      const cVent = cVerde.clone().multiplyScalar(0.22).lerp(tonos.asfalto, 0.25);
      const cTecho = tonos.pavimento.clone().lerp(tonos.techo, 0.18).lerp(lin(COL.costa), 0.12);
      const cLoseta = tonos.pavimento.clone().lerp(tonos.muro, 0.35).multiplyScalar(dia ? 0.95 : 1.05);
      const cBord = tonos.pavimento.clone().lerp(lin(COL.costa), 0.3).multiplyScalar(dia ? 1.0 : 1.15);
      const cAsf = tonos.asfalto.clone().multiplyScalar(dia ? 1.0 : 1.1);
      const cAdoq = tonos.pavimento.clone().lerp(lin(COL.tierra_media), 0.25).multiplyScalar(dia ? 0.92 : 1.0);
      const cPlaza = tonos.pavimento.clone().lerp(lin(COL.costa), 0.18).multiplyScalar(dia ? 1.0 : 1.08);
      const cPintura = lin(COL.costa).lerp(tonos.pavimento, 0.25).multiplyScalar(dia ? 0.95 : 0.8);
      const cNegro = tonos.linea.clone().lerp(tonos.asfalto, 0.25).multiplyScalar(0.8);
      const cMadera = lin(COL.tierra_media).lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(0.8);
      const cTierra = lin(COL.tierra_media).multiplyScalar(0.5);
      const cArbol = tonos.verde.clone().lerp(tonos.bien, 0.35).multiplyScalar(dia ? 0.8 : 0.95);
      const cLuz = lin(COL.luces || COL.luz), cAc = lin(COL.acento);

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
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
        const cono = (acc, u, v, h0, h1, r0, r1, seg, col, tapa) => {
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
            const P = [E(u + r0 * Math.cos(a0), v + r0 * Math.sin(a0), h0), E(u + r0 * Math.cos(a1), v + r0 * Math.sin(a1), h0),
              E(u + r1 * Math.cos(a1), v + r1 * Math.sin(a1), h1), E(u + r1 * Math.cos(a0), v + r1 * Math.sin(a0), h1)];
            const O = E(u + Math.cos(am), v + Math.sin(am), (h0 + h1) / 2), C0 = E(u, v, (h0 + h1) / 2);
            cara(acc, P, col, [O[0] - C0[0], (r0 - r1) * M * 0.5, O[2] - C0[2]]);
            if (tapa) { const T0 = E(u, v, h1); cara(acc, [P[3], P[2], T0, T0], tapa, [0, 1, 0]); }
          }
        };
        const cil = (acc, u, v, h0, h1, rr, seg, col, tapa) => cono(acc, u, v, h0, h1, rr, rr, seg, col, tapa);
        const ico = new THREE.IcosahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
        const bola = (acc, u, v, h, ru, rh, col, k) => {
          const P0 = E(u, v, h);
          for (let i = 0; i < ico.length; i += 9) {
            const vs = [];
            for (let j = 0; j < 9; j += 3) {
              const w = 1 + 0.14 * (hz(k * 131 + ((i + j) % 97), 5) - 0.5);
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

        // ---- las paredes: eje 'u' (el plano u = w) o 'v' (v = w), sg = hacia afuera. s: a lo largo; d: hacia afuera; h: alto
        const UV = (P, s, d) => (P.ax === "u" ? [P.w + P.sg * d, s] : [s, P.w + P.sg * d]);
        const EW = (P, s, d, h) => { const [u, v] = UV(P, s, d); return E(u, v, h); };
        const aEsc = (u, v) => [u * ux - v * uy, 0, -(u * uy + v * ux)];
        const nW = (P) => (P.ax === "u" ? aEsc(P.sg, 0) : aEsc(0, P.sg));
        const tW = (P) => (P.ax === "u" ? aEsc(0, 1) : aEsc(1, 0));
        const cjW = (acc, P, s0, s1, d0, d1, h0, h1, col, op) => {
          const [a0, b0] = UV(P, s0, d0), [a1, b1] = UV(P, s1, d1);
          cj(acc, Math.min(a0, a1), Math.max(a0, a1), Math.min(b0, b1), Math.max(b0, b1), h0, h1, col, op);
        };
        const quadW = (acc, P, s0, s1, d, h0, h1, col) => cara(acc, [EW(P, s0, d, h0), EW(P, s1, d, h0), EW(P, s1, d, h1), EW(P, s0, d, h1)], col, nW(P));
        // un arco de medio punto: la rosca (de r0 a r1, al frente en d1), el intradós (de d0 a d1) y, si va, el vano (abanico en d0)
        const arco = (acc, P, sc, hs, r0, r1, d0, d1, col, colVano) => {
          const n = 10, N = nW(P), T = tW(P);
          const pt = (rr, a, d) => EW(P, sc + rr * Math.cos(a), d, hs + rr * Math.sin(a));
          for (let i = 0; i < n; i++) {
            const a0 = Math.PI * i / n, a1 = Math.PI * (i + 1) / n, am = (a0 + a1) / 2;
            cara(acc, [pt(r0, a0, d1), pt(r1, a0, d1), pt(r1, a1, d1), pt(r0, a1, d1)], col, N);
            cara(acc, [pt(r0, a0, d0), pt(r0, a1, d0), pt(r0, a1, d1), pt(r0, a0, d1)], col.clone().multiplyScalar(0.8),
              [-T[0] * Math.cos(am), -Math.sin(am), -T[2] * Math.cos(am)]);
            if (colVano) { const C0 = EW(P, sc, d0, hs); cara(acc, [pt(r0, a0, d0), pt(r0, a1, d0), C0, C0], colVano, N); }
          }
        };

        const suelo = malla.nueva(), pal = malla.nueva(), focP = malla.nueva(), mueble = malla.nueva(), focE = malla.nueva(), luzA = malla.nueva();
        const iluminadas = [];   // ventanas que se encienden de noche: [P, s0, s1, h0, h1]
        let kv = 0;
        const enciende = (P, s0, s1, h0, h1) => {
          kv++;
          if (noche && hz(kv, 41) > 0.52) {
            const f = 0.32 + 0.4 * hz(kv, 42);
            quadW(focP, P, s0, s1, 0.07, h0, h1, cLuz.clone().multiplyScalar(f));
            iluminadas.push(1);
          }
        };

        // ================= las ventanas (tres pisos) y las pilastras
        const ventana = (P, sc, piso) => {
          if (piso === 0) {                                                       // planta baja: en arco
            const w = 1.0, h0 = 2.7, hs = 6.9;
            quadW(pal, P, sc - w, sc + w, 0.04, h0, hs, cVent);
            arco(pal, P, sc, hs, w, w + 0.38, 0.04, 0.24, cMold, cVent);
            cjW(pal, P, sc - w - 0.32, sc - w, 0, 0.24, h0 - 0.05, hs, cMold);
            cjW(pal, P, sc + w, sc + w + 0.32, 0, 0.24, h0 - 0.05, hs, cMold);
            cjW(pal, P, sc - w - 0.5, sc + w + 0.5, 0, 0.42, h0 - 0.32, h0, cMold, { base: true });
            cjW(pal, P, sc - 0.05, sc + 0.05, 0.04, 0.11, h0, hs + w, cMold.clone().multiplyScalar(0.85));
            cjW(pal, P, sc - w, sc + w, 0.04, 0.11, hs - 0.06, hs + 0.06, cMold.clone().multiplyScalar(0.85));
            cjW(pal, P, sc - 0.24, sc + 0.24, 0, 0.36, hs + w - 0.05, hs + w + 0.55, cMold.clone().multiplyScalar(1.08));   // la clave
            enciende(P, sc - w + 0.1, sc + w - 0.1, h0 + 0.1, hs);
          } else if (piso === 1) {                                                // primer piso: balcón y frontón recto
            const w = 0.95, h0 = F1 + 1.75, h1 = F1 + 6.2;
            quadW(pal, P, sc - w, sc + w, 0.04, h0, h1, cVent);
            cjW(pal, P, sc - w - 0.28, sc - w, 0, 0.22, h0, h1, cMold); cjW(pal, P, sc + w, sc + w + 0.28, 0, 0.22, h0, h1, cMold);
            cjW(pal, P, sc - w - 0.28, sc + w + 0.28, 0, 0.22, h1, h1 + 0.28, cMold);
            cjW(pal, P, sc - w - 0.55, sc + w + 0.55, 0, 0.5, h1 + 0.45, h1 + 0.78, cMold.clone().multiplyScalar(1.05), { base: true });
            cjW(pal, P, sc - 0.05, sc + 0.05, 0.04, 0.1, h0, h1, cMold.clone().multiplyScalar(0.85));
            cjW(pal, P, sc - 1.6, sc + 1.6, 0, 0.95, h0 - 0.24, h0, cMold, { base: true });      // la losa del balcón
            cjW(pal, P, sc - 1.25, sc + 1.25, 0, 0.5, h0 - 0.62, h0 - 0.24, cMold.clone().multiplyScalar(0.9));   // la ménsula
            cjW(pal, P, sc - 1.55, sc + 1.55, 0.82, 0.9, h0 + 0.9, h0 + 1.0, cNegro);            // el pasamanos
            for (let s = sc - 1.5; s <= sc + 1.51; s += 0.38) cjW(pal, P, s - 0.025, s + 0.025, 0.83, 0.88, h0, h0 + 0.9, cNegro);
            enciende(P, sc - w + 0.1, sc + w - 0.1, h0 + 0.1, h1 - 0.1);
          } else {                                                                // segundo piso: marco y repisa
            const w = 0.85, h0 = F2 + 1.5, h1 = F2 + 5.3;
            quadW(pal, P, sc - w, sc + w, 0.04, h0, h1, cVent);
            cjW(pal, P, sc - w - 0.25, sc - w, 0, 0.2, h0, h1, cMold); cjW(pal, P, sc + w, sc + w + 0.25, 0, 0.2, h0, h1, cMold);
            cjW(pal, P, sc - w - 0.25, sc + w + 0.25, 0, 0.26, h1, h1 + 0.35, cMold);
            cjW(pal, P, sc - w - 0.4, sc + w + 0.4, 0, 0.38, h0 - 0.25, h0, cMold, { base: true });
            cjW(pal, P, sc - 0.05, sc + 0.05, 0.04, 0.1, h0, h1, cMold.clone().multiplyScalar(0.85));
            enciende(P, sc - w + 0.1, sc + w - 0.1, h0 + 0.1, h1 - 0.1);
          }
        };
        const pilastra = (P, s, alto = HC) => {
          cjW(pal, P, s - 0.42, s + 0.42, 0, 0.3, HZ, alto, cPil);
          cjW(pal, P, s - 0.55, s + 0.55, 0, 0.42, HZ, HZ + 0.6, cMold);
          cjW(pal, P, s - 0.58, s + 0.58, 0, 0.46, alto - 0.65, alto - 0.3, cMold, { base: true });
        };
        // las fajas de una pared: zócalo, cordones, friso de rombos, dentículos, cornisa
        const fajas = (P, s0, s1, e0, e1) => {
          const a = s0 - e0, b = s1 + e1;
          cjW(pal, P, s0 - e0 * 0.45, s1 + e1 * 0.45, 0, 0.45, H0, HZ, cZoc, { tope: cZoc.clone().multiplyScalar(1.2) });
          cjW(pal, P, s0 - e0 * 0.42, s1 + e1 * 0.42, 0, 0.42, F1 - 0.15, F1 + 0.45, cMold, { base: true });
          cjW(pal, P, s0 - e0 * 0.32, s1 + e1 * 0.32, 0, 0.32, F2 - 0.1, F2 + 0.3, cMold, { base: true });
          for (let s = s0 + 0.45; s < s1 - 0.3; s += 0.9) {                     // el friso de rombos (decorado genérico)
            const m = HC - 1.0, hw = 0.36;
            cara(pal, [EW(P, s - hw, 0.02, m), EW(P, s, 0.02, m - hw), EW(P, s + hw, 0.02, m), EW(P, s, 0.02, m + hw)], cMold.clone().multiplyScalar(0.9), nW(P));
          }
          cjW(pal, P, s0, s1, 0, 0.05, HC - 1.5, HC - 1.42, cMold);
          for (let s = s0 + 0.3; s < s1 - 0.2; s += 0.8) cjW(pal, P, s - 0.17, s + 0.17, 0, 0.28, HC - 0.42, HC, cMold.clone().multiplyScalar(0.95));
          cjW(pal, P, s0 - e0 * 0.6, s1 + e1 * 0.6, 0, 0.6, HC, HC + 0.35, cMold, { base: true });
          cjW(pal, P, a, b, 0, 1.1, HC + 0.35, HR, cMold.clone().multiplyScalar(1.05), { base: true, tope: cMold.clone().multiplyScalar(1.1) });
        };
        // la balaustrada de la terraza (sobre la pared, hacia adentro)
        const balaustrada = (P, s0, s1) => {
          cjW(pal, P, s0, s1, -0.45, 0, HR, HR + 0.25, cMold);
          cjW(pal, P, s0, s1, -0.45, 0, HP - 0.18, HP, cMold, { tope: cMold.clone().multiplyScalar(1.12) });
          for (let s = s0 + 0.35; s < s1 - 0.2; s += 0.62) cjW(pal, P, s - 0.08, s + 0.08, -0.32, -0.12, HR + 0.25, HP - 0.18, cMold.clone().multiplyScalar(0.92));
        };
        // el ático (pretil macizo) de un pabellón o del cuerpo central
        const atico = (P, s0, s1, alto) => {
          cjW(pal, P, s0, s1, -0.7, 0, HR, alto - 0.3, cVerde, { tope: cMold });
          cjW(pal, P, s0 - 0.2, s1 + 0.2, -0.7, 0.3, alto - 0.3, alto, cMold, { base: true, tope: cMold.clone().multiplyScalar(1.1) });
          cara(pal, [EW(P, s0 + 0.6, 0.02, HR + 0.4), EW(P, s1 - 0.6, 0.02, HR + 0.4), EW(P, s1 - 0.6, 0.02, alto - 0.6), EW(P, s0 + 0.6, 0.02, alto - 0.6)],
            cVerde.clone().multiplyScalar(0.85), nW(P));
        };
        // una fachada: n vanos entre pilastras
        const fachada = (P, s0, s1, tipo) => {
          const n = Math.max(1, Math.round((s1 - s0) / (tipo === "cen" || tipo === "cenb" ? 6 : 4.6))), paso = (s1 - s0) / n;
          fajas(P, s0, s1, 1, 1);
          for (let k = 0; k <= n; k++) pilastra(P, s0 + k * paso);
          for (let k = 0; k < n; k++) {
            const sc = s0 + (k + 0.5) * paso;
            const portal = tipo === "cen" && k >= 1 && k <= n - 2;
            if (portal) {                                                       // el portal: tres arcos altos con columnas pareadas
              const w = 1.7, hs = 6.6;
              quadW(pal, P, sc - w, sc + w, 0.04, H0, hs, cVent.clone().multiplyScalar(0.6));
              arco(pal, P, sc, hs, w, w + 0.45, 0.04, 0.3, cMold, cVent.clone().multiplyScalar(0.6));
              for (const sg of [-1, 1]) for (const o of [0.25, 0.95]) {
                const [cu, cv] = UV(P, sc + sg * (w + o + 0.1), 0.75);
                cil(pal, cu, cv, HZ, hs + 1.2, 0.36, 14, cPil.clone().multiplyScalar(1.06), null);
                cjW(pal, P, sc + sg * (w + o + 0.1) - 0.5, sc + sg * (w + o + 0.1) + 0.5, 0.25, 1.25, hs + 1.2, hs + 1.6, cMold);
                cjW(pal, P, sc + sg * (w + o + 0.1) - 0.5, sc + sg * (w + o + 0.1) + 0.5, 0.25, 1.25, H0, HZ, cZoc);
              }
              enciende(P, sc - w + 0.2, sc + w - 0.2, H0 + 0.3, hs - 0.2);
            } else ventana(P, sc, 0);
            ventana(P, sc, 1); ventana(P, sc, 2);
          }
          if (tipo === "cen") {                                                  // las gradas del portal y su entablamento
            for (let g = 0; g < 3; g++) cjW(pal, P, s0 + paso - 0.6 + g * 0.3, s1 - paso + 0.6 - g * 0.3, 0, 2.0 - g * 0.55, H0, H0 + 0.17 * (g + 1), cZoc.clone().multiplyScalar(1.3 + 0.08 * g), { tope: cMold.clone().multiplyScalar(0.95 - 0.04 * g) });
            cjW(pal, P, s0 + paso - 0.6, s1 - paso + 0.6, 0, 1.3, 8.2, 9.0, cMold, { base: true });
          }
        };
        // las vueltas cortas (el escalón de 1.5 m entre un cuerpo y la pared metida): solo fajas
        const vuelta = (P, s0, s1) => { fajas(P, s0, s1, 1, 1); };

        // ================= los cuerpos macizos
        cj(pal, -DU + RE, DU - RE, -DV + RE, DV - RE, H0, HR, cVerde, { tope: cTecho });
        const PABS = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
        for (const [cu, cv] of PABS) {
          const u0 = cu > 0 ? DU - PAB : -DU, v0 = cv > 0 ? DV - PAB : -DV;
          cj(pal, u0, u0 + PAB, v0, v0 + PAB, H0, HR, cVerde, { tope: cTecho });
        }
        for (const cu of [1, -1]) cj(pal, cu > 0 ? DU - 6 : -DU, cu > 0 ? DU : -DU + 6, -CEN, CEN, H0, HR, cVerde, { tope: cTecho });
        // la terraza: juntas de la losa
        losa(pal, -DU + RE + 0.6, DU - RE - 0.6, -DV + RE + 0.6, DV - RE - 0.6, HR + 0.02, 5.5, 5.5,
          (u, v, k) => c.copy(cTecho).multiplyScalar(0.9 + 0.12 * hz(k, 7)).clone());

        // ================= las fachadas: al frente (+u), atrás (−u) y a los lados (±v)
        for (const cu of [1, -1]) {
          const Pc = { ax: "u", w: cu * DU, sg: cu }, Pm = { ax: "u", w: cu * (DU - RE), sg: cu };
          fachada(Pc, -DV, -DV + PAB, "pab"); fachada(Pc, DV - PAB, DV, "pab");
          fachada(Pm, -DV + PAB, -CEN, "main"); fachada(Pm, CEN, DV - PAB, "main");
          fachada(Pc, -CEN, CEN, cu > 0 ? "cen" : "cenb");
          balaustrada(Pm, -DV + PAB, -CEN); balaustrada(Pm, CEN, DV - PAB);
          atico(Pc, -DV, -DV + PAB, HA); atico(Pc, DV - PAB, DV, HA);
          atico(Pc, -CEN, CEN, HP + 0.3); atico(Pc, -6, 6, HT);
          // las vueltas del cuerpo central
          for (const cv of [1, -1]) {
            const Pr = { ax: "v", w: cv * CEN, sg: cv }, a = cu > 0 ? DU - RE : -DU, b = cu > 0 ? DU : -DU + RE;
            vuelta(Pr, a, b);
          }
        }
        for (const cv of [1, -1]) {
          const Pc = { ax: "v", w: cv * DV, sg: cv }, Pm = { ax: "v", w: cv * (DV - RE), sg: cv };
          fachada(Pc, -DU, -DU + PAB, "pab"); fachada(Pc, DU - PAB, DU, "pab");
          fachada(Pm, -DU + PAB, DU - PAB, "main");
          balaustrada(Pm, -DU + PAB, DU - PAB);
          atico(Pc, -DU, -DU + PAB, HA); atico(Pc, DU - PAB, DU, HA);
        }
        // las vueltas de los pabellones y los pretiles de su lado de adentro
        for (const [cu, cv] of PABS) {
          const u0 = cu > 0 ? DU - PAB : -DU, v0 = cv > 0 ? DV - PAB : -DV;
          vuelta({ ax: "v", w: cv > 0 ? DV - PAB : -DV + PAB, sg: -cv }, cu > 0 ? DU - RE : -DU, cu > 0 ? DU : -DU + RE);
          vuelta({ ax: "u", w: cu > 0 ? DU - PAB : -DU + PAB, sg: -cu }, cv > 0 ? DV - RE : -DV, cv > 0 ? DV : -DV + RE);
          atico({ ax: "v", w: cv > 0 ? DV - PAB : -DV + PAB, sg: -cv }, u0, u0 + PAB, HA);
          atico({ ax: "u", w: cu > 0 ? DU - PAB : -DU + PAB, sg: -cu }, v0, v0 + PAB, HA);
        }
        for (const cu of [1, -1]) {      // el pretil de atrás del ático central
          const P = { ax: "u", w: cu > 0 ? DU - 6 : -DU + 6, sg: -cu };
          cjW(pal, P, -CEN, CEN, -0.5, 0, HR, HP + 0.3, cVerde, { tope: cMold });
        }

        // ================= el suelo: el piso del palacio (se ve con el cristal), la acera y, con entorno, calles y plaza
        losa(suelo, -DU, DU, -DV, DV, H0, 4, 4, (u, v, k, i, j) => c.copy(cLoseta).lerp(cVerde, 0.08).multiplyScalar(0.88 + 0.08 * ((i + j) % 2)).clone());
        const loset = (u0, u1, v0, v1, cel = 1.2) => losa(suelo, u0, u1, v0, v1, H0, cel, cel,
          (u, v, k, i, j) => c.copy(cLoseta).multiplyScalar(0.9 + 0.1 * hz(i * 211 + j, 8) + ((i + j) % 2 ? 0.03 : -0.02)).clone());
        const ent = !!p.entorno;
        const U0 = -DU - AR, V0 = DV + AR;
        loset(DU, UA, -V0, V0); loset(U0, -DU, -V0, V0);
        loset(-DU, DU, DV, V0); loset(-DU, DU, -V0, -DV);
        // los bordillos de la acera
        cj(mueble, UA - 0.22, UA, -V0, V0, 0, H0 + 0.01, cBord, { tope: cBord.clone().multiplyScalar(1.08) });
        cj(mueble, U0, U0 + 0.22, -V0, V0, 0, H0 + 0.01, cBord, { tope: cBord.clone().multiplyScalar(1.08) });
        for (const cv of [1, -1]) cj(mueble, U0, UA, cv > 0 ? V0 - 0.22 : -V0, cv > 0 ? V0 : -V0 + 0.22, 0, H0 + 0.01, cBord, { tope: cBord.clone().multiplyScalar(1.08) });
        const farolas = [], bancas = [], arboles = [];
        if (ent) {
          // la calle del frente, de adoquín (sin rayas)
          losa(suelo, UA, UC, -VX, VX, 0.03, 1.0, 2.0, (u, v, k, i, j) => c.copy(cAdoq).multiplyScalar(0.86 + 0.16 * hz(i * 37 + j * 101, 9)).clone());
          // las calles de los lados y de atrás, de asfalto, con su línea
          const asf = (u0, u1, v0, v1) => losa(suelo, u0, u1, v0, v1, 0.02, 2, 2, (u, v, k) => c.copy(cAsf).multiplyScalar(0.92 + 0.12 * hz(k, 10)).clone());
          asf(U0 - CR, U0, -VX, VX);
          for (const cv of [1, -1]) asf(U0, UA, cv > 0 ? V0 : -V0 - CR, cv > 0 ? V0 + CR : -V0);
          for (let v = -VX + 2; v < VX - 3; v += 6) losa(suelo, U0 - CR / 2 - 0.08, U0 - CR / 2 + 0.08, v, v + 3, 0.03, 0.16, 3, () => cPintura);
          for (const cv of [1, -1]) for (let u = U0 + 2; u < UA - 3; u += 6) losa(suelo, u, u + 3, cv * (V0 + CR / 2) - 0.08, cv * (V0 + CR / 2) + 0.08, 0.03, 3, 0.16, () => cPintura);
          // la acera de enfrente y su bordillo
          loset(UC, UE, -VX, VX);
          cj(mueble, UC, UC + 0.22, -VX, VX, 0, H0 + 0.01, cBord, { tope: cBord.clone().multiplyScalar(1.08) });
          // la plaza: losas grandes en dos tonos
          losa(suelo, UE, UP, -VX, VX, H0, 3, 3, (u, v, k, i, j) => c.copy(cPlaza).multiplyScalar((i + j) % 2 ? 0.94 : 1.02).multiplyScalar(0.96 + 0.06 * hz(k, 11)).clone());
          losa(suelo, UE, UE + 0.5, -VX, VX, H0 + 0.004, 0.5, 4, () => cPlaza.clone().multiplyScalar(0.8));
          // farolas en el bordillo de enfrente y del lado del palacio; bancas mirando al palacio; árboles en su alcorque
          for (let v = -72, k = 0; v <= 72; v += 16, k++) { farolas.push([UC + 0.7, v, -1]); if (k % 2 === 0) farolas.push([UA - 0.7, v + 8, 1]); }
          for (let v = -64; v <= 64; v += 16) bancas.push([UE + 1.4, v + 8]);
          for (let v = -70, k = 0; v <= 70; v += 20, k++) arboles.push([UE + 10 + 2 * hz(k, 12), v + 3 * (hz(k, 13) - 0.5), k]);
        }
        const farola = ([u, v, sgn]) => {
          cono(mueble, u, v, H0, H0 + 0.6, 0.16, 0.11, 12, cNegro, null);
          cil(mueble, u, v, H0 + 0.6, H0 + 4.6, 0.07, 10, cNegro, null);
          cj(mueble, u - 0.05, u + 0.05, v - 0.05, v + 0.05, H0 + 4.6, H0 + 4.75, cNegro);
          cono(mueble, u, v, H0 + 4.75, H0 + 5.35, 0.2, 0.26, 12, noche ? cLuz.clone().multiplyScalar(0.9) : cNegro.clone().lerp(lin(COL.costa), 0.4), null);
          cono(mueble, u, v, H0 + 5.35, H0 + 5.6, 0.3, 0.05, 12, cNegro, cNegro);
          cil(focE, u, v, H0 + 4.8, H0 + 5.3, 0.15, 12, noche ? cLuz : cNegro.clone().lerp(lin(COL.costa), 0.5), null);
        };
        const banca = ([u, v], k) => {
          const col = cMadera.clone().multiplyScalar(0.9 + 0.15 * hz(k, 14));
          for (let j = 0; j < 4; j++) cj(mueble, u - 0.25 + j * 0.13, u - 0.25 + j * 0.13 + 0.1, v - 0.95, v + 0.95, H0 + 0.42, H0 + 0.46, col);
          for (let j = 0; j < 3; j++) cj(mueble, u + 0.28, u + 0.33, v - 0.95, v + 0.95, H0 + 0.55 + j * 0.14, H0 + 0.65 + j * 0.14, col);
          for (const vv of [-0.8, 0.8]) { cj(mueble, u - 0.28, u + 0.3, vv + v - 0.04, vv + v + 0.04, H0, H0 + 0.42, cNegro); cj(mueble, u + 0.28, u + 0.35, vv + v - 0.04, vv + v + 0.04, H0 + 0.42, H0 + 0.95, cNegro); }
        };
        const arbol = ([u, v, k]) => {
          cj(mueble, u - 0.8, u + 0.8, v - 0.8, v + 0.8, H0 - 0.02, H0 + 0.08, cBord, { tope: cBord.clone().multiplyScalar(0.95) });
          cj(mueble, u - 0.68, u + 0.68, v - 0.68, v + 0.68, H0 + 0.08, H0 + 0.09, cTierra);
          cono(mueble, u, v, H0, 3.4, 0.2, 0.13, 10, lin(COL.tierra_media).multiplyScalar(0.55), null);
          for (let j = 0; j < 5; j++) bola(mueble, u + 1.1 * Math.cos(j * 1.3 + k), v + 1.1 * Math.sin(j * 1.3 + k), 4.6 + 0.8 * hz(k * 7 + j, 15), 1.7 + 0.4 * hz(k * 7 + j, 16), 1.3 + 0.3 * hz(k * 7 + j, 17), cArbol.clone().multiplyScalar(0.8 + 0.3 * hz(k * 7 + j, 18)), 500 + k * 7 + j);
        };
        farolas.forEach(farola); bancas.forEach(banca); arboles.forEach(arbol);
        for (let j = 0; j < bancas.length; j += 2) { const [u, v] = bancas[j]; cono(mueble, u, v + 1.6, H0, H0 + 0.95, 0.24, 0.27, 14, cNegro.clone().lerp(cVerde, 0.3), cNegro); }

        // ================= la luz de noche: charcos bajo las farolas
        // un charco redondo: el centro encendido y dos anillos que se apagan hacia la orilla
        const charco = (u, v, rr, col, h = H0 + 0.008) => {
          const n = 20, q = luzA.pos.length / 3, A = [[0, 1], [0.45, 0.55], [1, 0]];
          luzA.pos.push(...E(u, v, h)); luzA.col.push(col.r, col.g, col.b);
          for (const [f, a] of A.slice(1)) for (let i = 0; i < n; i++) { const t0 = TAU * i / n; luzA.pos.push(...E(u + rr * f * Math.cos(t0), v + rr * f * Math.sin(t0), h)); luzA.col.push(col.r * a, col.g * a, col.b * a); }
          for (let i = 0; i < n; i++) { const j = (i + 1) % n; luzA.idx.push(q, q + 1 + i, q + 1 + j);
            luzA.idx.push(q + 1 + i, q + 1 + n + i, q + 1 + n + j, q + 1 + i, q + 1 + n + j, q + 1 + j); }
        };
        if (noche) for (const [u, v] of farolas) charco(u, v, 6, cLuz.clone().multiplyScalar(0.13));

        // ================= la sombra de contacto (la del palacio se va con el cristal)
        const KS = ctx.CFG.sombra_contacto || (dia ? 0.4 : 0.22);
        const sombras = (rects) => {
          const so = { pos: [], a: [], idx: [] };
          for (const [u0, u1, v0, v1, pad] of rects) {
            const anillo = (d, al) => [[u0 - d, v0 - d], [u1 + d, v0 - d], [u1 + d, v1 + d], [u0 - d, v1 + d]].map(([u, v]) => ({ P: E(u, v, H0 + 0.012), a: al }));
            const I = anillo(0, 1), O = anillo(pad, 0), q = so.pos.length / 3;
            for (const x of I.concat(O)) { so.pos.push(...x.P); so.a.push(x.a); }
            so.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
            for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; so.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
          }
          const g = new THREE.BufferGeometry();
          g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(so.pos), 3));
          g.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(so.a), 1));
          g.setIndex(so.idx);
          const mat = new THREE.ShaderMaterial({ uniforms: { uK: { value: KS * 0.7 } }, transparent: true, depthWrite: false,
            polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
            vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: "uniform float uK; varying float vA; void main(){ float a = uK * vA * vA; gl_FragColor = vec4(0.0, 0.0, 0.0, a); }" });
          const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = 4; scene.add(m);
          return mat;
        };
        const matSomP = sombras([[DU - 0.1, DU + 0.6, -DV, DV, 1.6], [-DU - 0.6, -DU + 0.1, -DV, DV, 1.6], [-DU, DU, DV - 0.1, DV + 0.6, 1.6], [-DU, DU, -DV - 0.6, -DV + 0.1, 1.6]]);
        sombras(bancas.map(([u, v]) => [u - 0.3, u + 0.35, v - 0.95, v + 0.95, 0.4]).concat(arboles.map(([u, v]) => [u - 0.3, u + 0.3, v - 0.3, v + 0.3, 1.8])));

        // ================= las mallas
        const sinTraslado = (acc, mat, orden) => { const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        const matSuelo = malla.material({ desfase: 2 }), matPal = malla.material({ desfase: 1 }), matMue = malla.material();
        malla.poner(suelo, matSuelo, 2);
        sinTraslado(pal, matPal, 3);
        sinTraslado(mueble, matMue, 5);
        const matFocP = malla.material({ desfase: 3 }); if (focP.pos.length) sinTraslado(focP, matFocP, 4); matFocP.uniforms.uBrillo.value = noche ? 1.7 : 1.0;
        const matFocE = malla.material(); if (focE.pos.length) sinTraslado(focE, matFocE, 5); matFocE.uniforms.uBrillo.value = noche ? 1.8 : 1.0;
        if (luzA.pos.length) sinTraslado(luzA, malla.material({ aditivo: true, desfase: 4 }), 4);
        for (const m of [matPal, matFocP]) { m.uniforms.cTinte.value.copy(cAc); }

        // ================= el CRISTAL: la caja de 127 × 70 × 30 sigue a la vista cuando las caras se van (2026-11-17)
        // Con `cristal` las caras del palacio casi desaparecen; lo que queda para medir es la CAJA: (1) un volumen liso y
        // translúcido del mismo tamaño (techo un poco más denso que los muros: el «lleno hasta aquí»), (2) sus aristas con
        // un halo de contraste debajo (se leen sobre un suelo claro y sobre uno oscuro) y la de arriba, a 30 m, la más gruesa,
        // y (3) las líneas de los pisos más tenues. `aristas` (0–1) dice cuánto pesan las tres cosas.
        const AR0 = clamp(p.aristas === undefined ? 1 : +p.aristas, 0, 1);
        const luma = (x) => 0.2126 * x.r + 0.7152 * x.g + 0.0722 * x.b;
        const pisoClaro = luma(cLoseta) > 0.22;
        const cTinta = pisoClaro ? cVerde.clone().multiplyScalar(0.32).lerp(tonos.linea, 0.35) : cMold.clone().lerp(lin(COL.costa), 0.6).multiplyScalar(1.35);
        const cHalo = pisoClaro ? lin(COL.costa).lerp(tonos.pavimento, 0.15).multiplyScalar(1.1) : cVerde.clone().multiplyScalar(0.18).lerp(tonos.asfalto, 0.5);
        const vol = malla.nueva();
        const ladoV = (u0, v0, u1, v1, nrm, f) => cara(vol, [E(u0, v0, H0 + 0.06), E(u1, v1, H0 + 0.06), E(u1, v1, HT), E(u0, v0, HT)], cVerde.clone().multiplyScalar(f), nrm);
        ladoV(DU, -DV, DU, DV, aEsc(1, 0), 1.05); ladoV(-DU, -DV, -DU, DV, aEsc(-1, 0), 0.95);
        ladoV(-DU, DV, DU, DV, aEsc(0, 1), 1.0); ladoV(-DU, -DV, DU, -DV, aEsc(0, -1), 1.0);
        cara(vol, [E(-DU, -DV, HT), E(DU, -DV, HT), E(DU, DV, HT), E(-DU, DV, HT)], cVerde.clone().lerp(lin(COL.costa), 0.25).multiplyScalar(1.15), [0, 1, 0]);
        const matVol = malla.material({ alfa: 0, desfase: 0 });
        matVol.transparent = true; matVol.depthWrite = false; matVol.side = THREE.DoubleSide;
        const mVol = sinTraslado(vol, matVol, 8); mVol.visible = false;
        matVol.uniforms.cTinte.value.copy(cAc);

        const V3 = (u, v, h) => new THREE.Vector3(...E(u, v, h));
        const poli = (cad) => { const out = []; let s = 0; cad.forEach((x, i) => { if (i) s += cad[i - 1].distanceTo(x); out.push({ v: x, s, salto: i === cad.length - 1 }); }); return out; };
        const anillo = (h) => poli([V3(-DU, -DV, h), V3(DU, -DV, h), V3(DU, DV, h), V3(-DU, DV, h), V3(-DU, -DV, h)]);
        const cEdge = cTinta;
        const arriba = anillo(HT + 0.05);
        const caja = [].concat(anillo(H0 + 0.08), ...[[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => poli([V3(a * DU, b * DV, H0 + 0.08), V3(a * DU, b * DV, HT)])));
        const pisos = [].concat(anillo(F1), anillo(F2), anillo(HR));
        const gA = 0.7 + 0.6 * AR0;       // el grueso de las aristas
        const aristas = [
          { c: ctx.cinta(arriba, cHalo, 8.5 * gA, 0, 8), alfa: 0.7, tipo: "halo" },
          { c: ctx.cinta(caja, cHalo, 6.0 * gA, 0, 8), alfa: 0.6, tipo: "halo" },
          { c: ctx.cinta(arriba, cEdge, 4.6 * gA, 0, 9), alfa: 1, tipo: "caja" },
          { c: ctx.cinta(caja, cEdge, 3.0 * gA, 0, 9), alfa: 1, tipo: "caja" },
          { c: ctx.cinta(pisos, cEdge, 1.6 * gA, 0, 9), alfa: 0.5, tipo: "piso" },
        ];

        // ================= la gente: caminan por la acera de enfrente (sin entorno, por la acera del frente); alguna de pie
        const NPER = clamp(p.personas | 0, 0, 12), NCAM = NPER - Math.floor(NPER / 4);
        const camisas = [tonos.mal.clone().multiplyScalar(0.9), lin(COL.mar).multiplyScalar(0.8), tonos.bien.clone().multiplyScalar(0.8),
          lin(COL.costa).multiplyScalar(0.85), tonos.medio.clone().multiplyScalar(0.9), lin(COL.tierra_media).multiplyScalar(0.85), tonos.secundario.clone()]
          // que se distingan a tamaño de teléfono: sobre losetas claras, camisas oscuras y saturadas; sobre oscuras, claras
          .map((x) => (pisoClaro ? x.multiplyScalar(0.55) : x.lerp(lin(COL.costa), 0.25).multiplyScalar(1.3)));
        const KG = K * clamp(+p.gente_tamano || 1, 1, 2);
        const gente = [];
        for (let i = 0; i < NPER; i++) {
          if (i < NCAM) {
            const uL = ent ? UC + 1.2 + (UE - UC - 2.2) * hz(i, 20) : DU + 1.5 + (UA - DU - 2.8) * hz(i, 20);
            gente.push({ cam: true, u: uL, dir: hz(i, 21) > 0.5 ? 1 : -1, vel: 1.05 + 0.4 * hz(i, 22), v0: hz(i, 23) * 2 * (VX - 6) });
          } else {
            const k = i - NCAM, u = ent ? UE + 4 + 14 * hz(i, 24) : UA - 1.6, v = -50 + 100 * hz(i, 25);
            gente.push({ cam: false, u, v, a: TAU * hz(i, 26) + k });
          }
        }
        const flP = NPER ? ctx.flota("persona", NPER, { tamano: KG, lev: H0 * K, orden: 6, semilla: (p.semilla * 11 + np * 5) % 991,
          color: (i) => camisas[(i + Math.floor(hz(1, 27) * camisas.length)) % camisas.length],
          pose: (i) => (gente[i].cam ? "caminar" : "de_pie") }) : null;

        return { id: p.id, W, ux, uy, M, gente, flP, matsPal: [matPal, matFocP], matSomP, KS, aristas, cEdge, cAc, matVol, mVol, AR0,
          mats: [matMue, matSuelo], cristal: clamp(+p.cristal || 0, 0, 1), desde: +p.cristal_desde || 0, dur: Math.max(0.05, +p.cristal_dur || 1.2), largo: 2 * (VX - 6) };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? clamp((b - 1) / 0.9, 0, 1) : 0;
        // el cristal: 0 = macizo; sube de `desde` a `desde + dur` (si `desde` es 0, ya está)
        const q = s.cristal * (s.desde <= 0 ? 1 : suave(clamp((t - s.desde) / s.dur, 0, 1)));
        const transp = q > 0.002, alfa = 1 - 0.965 * q;
        for (const m of s.matsPal) {
          m.transparent = transp; m.depthWrite = !transp; m.uniforms.uAlfa.value = alfa;
          m.uniforms.uTinte.value = 0.42 * k;
        }
        s.matsPal[0].uniforms.uBrillo.value = 1 + 0.2 * k;
        s.matSomP.uniforms.uK.value = s.KS * 0.7 * (1 - q);
        // el volumen liso: aparece con el cristal (techo y muros translúcidos), nunca tapa lo que se pone adentro
        s.mVol.visible = transp && s.AR0 > 0;
        s.matVol.uniforms.uAlfa.value = q * (0.05 + 0.1 * s.AR0);
        s.matVol.uniforms.uTinte.value = 0.42 * k;
        for (const m of s.mats) m.uniforms.uBrillo.value = 1;
        const fa = 0.35 + 0.65 * s.AR0;
        for (const A of s.aristas) {
          const a = A.tipo === "piso" ? q : Math.max(q, 0.85 * k);
          A.c.mat.uniforms.uAlfa.value = Math.min(1, a * A.alfa * fa);
          if (A.tipo !== "halo") A.c.mat.uniforms.cColor.value.copy(s.cEdge).lerp(s.cAc, k);
        }
        // la gente: la posición a lo largo de la acera es función de t
        if (s.flP) {
          s.gente.forEach((g, i) => {
            if (g.cam) {
              const L = s.largo, sv = ((((g.v0 + g.dir * g.vel * t) % L) + L) % L), v = -L / 2 + sv;
              const kk = clamp(sv / 3, 0, 1) * clamp((L - sv) / 3, 0, 1);
              const [x, y] = s.W(g.u, v);
              s.flP.poner(i, x, y, -s.uy * g.dir, s.ux * g.dir, kk, 0, g.vel);
            } else {
              const [x, y] = s.W(g.u, g.v), du = Math.cos(g.a), dv = Math.sin(g.a);
              s.flP.poner(i, x, y, du * s.ux - dv * s.uy, du * s.uy + dv * s.ux, 1, 0, 0);
            }
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
