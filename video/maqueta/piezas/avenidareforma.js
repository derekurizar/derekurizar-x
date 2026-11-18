// Pieza «avenidareforma» (ficha: avenidareforma.json; reglas: scripts/maqueta_tipos/avenidareforma.py): la Avenida La
// Reforma de hoy sobre su trazo de OpenStreetMap (set de ciudad), en todo su largo dentro de la caja. Lo resuelve Python y
// llega ya colocado: las cuatro vías (principal al norte y al sur, los dos auxiliares), las secciones del arriate cada 8 m
// (bordes en x de cada franja), los cruces, la plaza del Obelisco y todo lo que se planta (árboles, bancas, farolas,
// monumentos, el depósito de agua). Aquí solo se dibuja.
// Solo lo verificado: vía principal en dos sentidos y carriles auxiliares a los lados; arriate con pasto, caminos, bancas,
// monumentos a lo largo y un depósito de agua; árboles de muchas especies sin una dominante, los cipreses los más grandes;
// algunas jacarandas (lila solo si `jacaranda_flor`: marzo y abril); semáforos (ubicación genérica: en los cruces); el
// Obelisco (forma genérica) con escudo arriba, la llama en un pebetero de cobre y cuatro pérgolas, sobre su plaza.
// Genérico y sin afirmar: carriles (ilustrativos: 3 por sentido), anchos, monumentos (pedestales y figuras sin rostro),
// el depósito (un tanque redondo), la forma del obelisco. Sin texto, sin marcas.
// CON VIDA (puro de t): gente que camina y corre por el camino del arriate (y alguna sentada en las bancas), los semáforos
// que cambian (la avenida y la calle que cruza, en fases opuestas), la llama que tiembla. De noche: farolas con su charco de
// luz, la llama que alumbra y los semáforos encendidos. «resaltar» la pieza (o con `elemento` en «<id>.norte/sur») enciende
// la avenida entera en el acento como una sola calle; con «<id>.jacarandas» las jacarandas se encienden en lila; con
// «<id>.obelisco», el Obelisco; con «<id>.semaforos», los semáforos; con «<id>.arriate», el camellón.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  function correr(pts, d) {            // la polilínea corrida d unidades a su izquierda
    return pts.map((p, i) => { const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return [p[0] - (b[1] - a[1]) / L * d, p[1] + (b[0] - a[0]) / L * d]; });
  }
  MAQ.PIEZAS.avenidareforma = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, dia = !!ES.dia;
      const suelo = (x, y) => (ctx.suelo || ctx.altura)(x, y), alt = (x, y) => ctx.altura(x, y);
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo)
      const cAsf = tonos.asfalto.clone().multiplyScalar(dia ? 1.0 : 1.12);
      const cAsfAux = cAsf.clone().lerp(tonos.pavimento, 0.12);
      const cPasto = tonos.verde.clone().lerp(tonos.bien, dia ? 0.22 : 0.3).multiplyScalar(dia ? 0.95 : 1.15);
      const cCamino = tonos.pavimento.clone().lerp(lin(COL.tierra_media), 0.18).multiplyScalar(dia ? 1.0 : 1.12);
      const cAcera = tonos.pavimento.clone().multiplyScalar(dia ? 0.95 : 1.05);
      const cBord = tonos.pavimento.clone().lerp(lin(COL.costa), 0.35).multiplyScalar(dia ? 1.05 : 1.2);
      const cPintura = lin(COL.costa).lerp(tonos.pavimento, 0.2).multiplyScalar(dia ? 1.0 : 0.9);
      const cNegro = tonos.linea.clone().lerp(tonos.asfalto, 0.3).multiplyScalar(0.85);
      const cTronco = lin(COL.tierra_media).multiplyScalar(0.5);
      const cFronda = tonos.verde.clone().lerp(tonos.bien, 0.35).multiplyScalar(dia ? 0.8 : 1.0);
      const cCipres = tonos.verde.clone().lerp(tonos.bien, 0.15).multiplyScalar(dia ? 0.55 : 0.75);
      const cManz = tonos.verde.clone().lerp(tonos.bien, 0.5).multiplyScalar(dia ? 0.85 : 1.05);
      const cLila = tonos.mal.clone().lerp(lin(COL.costa), 0.72).lerp(lin(COL.mar), 0.1).lerp(tonos.secundario, 0.1).multiplyScalar(dia ? 1.0 : 1.15);
      const cJacVerde = cFronda.clone().lerp(lin(COL.costa), 0.12);
      const cPiedra = tonos.pavimento.clone().lerp(lin(COL.costa), 0.45).multiplyScalar(dia ? 1.08 : 1.25);
      const cPiedraO = cPiedra.clone().multiplyScalar(0.8);
      const cCobre = lin(COL.tierra_media).lerp(tonos.mal, 0.35).multiplyScalar(0.85);
      const cMadera = lin(COL.tierra_media).lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(0.8);
      const cAguaD = (tonos.agua || lin(COL.mar)).clone();
      const cLuz = lin(COL.luces || COL.luz), cAc = lin(COL.acento);

      return piezas.map((p, np) => {
        const M = metros(1), sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const E = (x, y, z) => [x, z, -y];
        // ---- caras con la luz horneada (4 puntos de escena; ref = hacia afuera)
        const cara = (acc, P, col, ref, f = 1) => {
          const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = sombra(nx, ny, nz) * f, q = acc.pos.length / 3;
          for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        // una caja orientada: u a lo largo de `ang`, v a su izquierda; alturas sobre z0 (la base)
        const caja = (acc, cx, cy, ang, a0, a1, b0, b1, h0, h1, col, op = {}) => {
          const ca = Math.cos(ang), sa = Math.sin(ang), z0 = op.z0 !== undefined ? op.z0 : alt(cx, cy);
          const P = (u, v, h) => E(cx + (u * ca - v * sa) * M, cy + (u * sa + v * ca) * M, z0 + h * M);
          const C = P((a0 + a1) / 2, (b0 + b1) / 2, (h0 + h1) / 2);
          const caras = [[[a0, b0, h1], [a1, b0, h1], [a1, b1, h1], [a0, b1, h1]], [[a0, b0, h0], [a1, b0, h0], [a1, b0, h1], [a0, b0, h1]],
            [[a0, b1, h0], [a1, b1, h0], [a1, b1, h1], [a0, b1, h1]], [[a0, b0, h0], [a0, b1, h0], [a0, b1, h1], [a0, b0, h1]],
            [[a1, b0, h0], [a1, b1, h0], [a1, b1, h1], [a1, b0, h1]]];
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
        const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
        const bola = (acc, x, y, z, ru, rh, col, k) => {
          for (let i = 0; i < ico.length; i += 9) {
            const vs = [];
            for (let j = 0; j < 9; j += 3) {
              const w = 1 + 0.16 * (hz(k * 131 + ((i + j) % 97), 5) - 0.5);
              vs.push([x + ico[i + j] * ru * w * M, z + ico[i + j + 1] * rh * w * M, -(y - ico[i + j + 2] * ru * w * M)]);
            }
            const e1 = [vs[1][0] - vs[0][0], vs[1][1] - vs[0][1], vs[1][2] - vs[0][2]], e2 = [vs[2][0] - vs[0][0], vs[2][1] - vs[0][1], vs[2][2] - vs[0][2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const cx = (vs[0][0] + vs[1][0] + vs[2][0]) / 3 - x, cy = (vs[0][1] + vs[1][1] + vs[2][1]) / 3 - z, cz = (vs[0][2] + vs[1][2] + vs[2][2]) / 3 + y;
            if (nx * cx + ny * cy + nz * cz < 0) { nx = -nx; ny = -ny; nz = -nz; }
            const n = Math.hypot(nx, ny, nz) || 1, sb = sombra(nx / n, ny / n, nz / n);
            c.copy(col).multiplyScalar(sb * (0.86 + 0.24 * hz(k * 977 + i, 6)));
            const q = acc.pos.length / 3;
            for (const X of vs) { acc.pos.push(X[0], X[1], X[2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };
        // un disco plano (12–24 lados) a una altura fija
        const disco = (acc, x, y, z, r, seg, col, r0 = 0) => {
          const l = sombra(0, 1, 0);
          for (let i = 0; i < seg; i++) {
            const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, q = acc.pos.length / 3;
            for (const [rr, a] of [[r0, a0], [r, a0], [r, a1], [r0, a1]]) { acc.pos.push(...E(x + rr * Math.cos(a) * M, y + rr * Math.sin(a) * M, z)); acc.col.push(col.r * l, col.g * l, col.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };

        // ================= el eje y sus secciones (sec[i] = [y, e1, e2, e3, e4, e5, e6]; e3–e4 el arriate)
        const sec = p.sec, eje = p.eje, sAc = [0];
        for (let i = 1; i < eje.length; i++) sAc.push(sAc[i - 1] + Math.hypot(eje[i][0] - eje[i - 1][0], eje[i][1] - eje[i - 1][1]));
        const L = sAc[sAc.length - 1];
        const en = (s) => {                 // el punto del eje a s (x, y, dx, dy) y la sección interpolada
          s = clamp(s, 0, L);
          let k = Math.min(eje.length - 2, Math.max(0, Math.floor(s / L * (eje.length - 1))));
          while (k < eje.length - 2 && sAc[k + 1] < s) k++;
          while (k > 0 && sAc[k] > s) k--;
          const a = eje[k], b = eje[k + 1], d = sAc[k + 1] - sAc[k] || 1, u = (s - sAc[k]) / d;
          const q = sec[k].map((v, j) => (v === null || sec[k + 1][j] === null ? null : v + (sec[k + 1][j] - v) * u));
          return { x: a[0] + (b[0] - a[0]) * u, y: a[1] + (b[1] - a[1]) * u, dx: (b[0] - a[0]) / d, dy: (b[1] - a[1]) / d, q };
        };
        const cruces = p.cruces, enCruce = (s, h) => cruces.some((cr) => Math.abs(cr[0] - s) < h);
        const HV = 0.45, HA = 0.43, HR = 0.75, HAR = 0.68, HCM = 0.71, HPL = 0.72;   // alturas (m) sobre el suelo

        const vias = malla.nueva(), arr = malla.nueva(), mueble = malla.nueva(), arbo = malla.nueva(), jac = malla.nueva(), jacH = malla.nueva();
        const obe = malla.nueva(), semP = malla.nueva(), focos = malla.nueva(), luzA = malla.nueva();
        const lamp = [0, 1, 2, 3, 4, 5].map(() => malla.nueva());      // rojo, ámbar, verde de la avenida (0–2) y de la calle (3–5)
        // ================= las vías: asfalto con bordes, carriles y aceras
        const V = p.vias, hv = p.ancho_via / 2, ha = p.ancho_aux / 2;
        for (const k of ["norte", "sur"]) malla.banda(vias, V[k], p.ancho_via, HV, 10, cAsf);
        for (const k of ["aux_norte", "aux_sur"]) if (V[k]) {
          malla.banda(vias, V[k], p.ancho_aux, HA, 10, cAsfAux);
          const fuera = k === "aux_norte" ? -1 : 1;     // la acera, del lado de afuera (aux al norte: a su derecha)
          malla.banda(vias, correr(V[k], fuera * (ha + 1.9)), 3.6, HA + 0.2, 10, cAcera);
        }
        for (const c0 of p.via_plaza) malla.banda(vias, c0, 9, HV, 8, cAsf);
        for (const cr of cruces) {
          const dx = Math.cos(cr[3]), dy = Math.sin(cr[3]);
          malla.banda(vias, [[cr[1] - dx * 36, cr[2] - dy * 36], [cr[1] + dx * 36, cr[2] + dy * 36]], 18, HV - 0.02, 6, cAsf.clone().multiplyScalar(0.96));
        }
        const A = ctx.CFG.ruta.ancho, rayas = [];
        const linea = (pts, color, ancho_px, alfa, extra) => { const cn = ctx.cinta(ctx.pegar(pts, 8, HR), color, ancho_px, alfa, 6, extra); rayas.push(cn); return cn; };
        for (const k of ["norte", "sur"]) {
          for (const s of [1, -1]) linea(correr(V[k], s * (hv - 0.35)), cPintura, A * 0.6, 0.85);
          for (const s of [1, -1]) linea(correr(V[k], s * p.carril * 0.5), cPintura, A * 0.45, 0.7, { raya: 10 });
        }
        for (const k of ["aux_norte", "aux_sur"]) if (V[k]) linea(V[k], cPintura, A * 0.4, 0.55, { raya: 10 });
        ctx.linea(p.id, rayas[0]);

        // ================= el arriate y los separadores: franjas entre secciones, abiertas en los cruces
        const tira = (acc, i, j0, j1, d0, d1, lev, col, minw = 0.8) => {
          const a = sec[i], b = sec[i + 1];
          if (a[j0] === null || a[j1] === null || b[j0] === null || b[j1] === null) return false;
          const xa0 = a[j0] + d0, xa1 = a[j1] + d1, xb0 = b[j0] + d0, xb1 = b[j1] + d1;
          if (xa1 - xa0 < minw || xb1 - xb0 < minw) return false;
          const q = acc.pos.length / 3, l = sombra(0, 1, 0);
          for (const [x, y] of [[xa0, a[0]], [xa1, a[0]], [xb1, b[0]], [xb0, b[0]]]) { acc.pos.push(...E(x, y, suelo(x, y) + lev)); acc.col.push(col.r * l, col.g * l, col.b * l); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          return true;
        };
        const canto = (acc, i, j, d, h0, h1, col, sg) => {        // la cara vertical de un bordillo
          const a = sec[i], b = sec[i + 1];
          if (a[j] === null || b[j] === null) return;
          const xa = a[j] + d, xb = b[j] + d;
          cara(acc, [E(xa, a[0], suelo(xa, a[0]) + h0), E(xb, b[0], suelo(xb, b[0]) + h0), E(xb, b[0], suelo(xb, b[0]) + h1), E(xa, a[0], suelo(xa, a[0]) + h1)], col, [sg, 0, 0]);
        };
        for (let i = 0; i + 1 < sec.length; i++) {
          const sm = (sAc[i] + sAc[i + 1]) / 2;
          if (enCruce(sm, 10)) continue;
          const g = cPasto.clone().multiplyScalar(0.9 + 0.16 * hz(i, 30));
          if (tira(arr, i, 3, 4, 0.3, -0.3, HAR, g)) {
            tira(mueble, i, 3, 3, 0, 0.3, HAR + 0.04, cBord, 0.1); tira(mueble, i, 4, 4, -0.3, 0, HAR + 0.04, cBord, 0.1);
            canto(mueble, i, 3, 0, HV, HAR + 0.04, cBord.clone().multiplyScalar(0.85), -1); canto(mueble, i, 4, 0, HV, HAR + 0.04, cBord.clone().multiplyScalar(0.85), 1);
            // el camino del arriate (al centro) donde el arriate es ancho
            const a = sec[i], b = sec[i + 1];
            if (a[4] - a[3] > 5 && b[4] - b[3] > 5) {
              const m0 = (a[3] + a[4]) / 2, m1 = (b[3] + b[4]) / 2, q = mueble.pos.length / 3, l = sombra(0, 1, 0);
              const cc = cCamino.clone().multiplyScalar(0.94 + 0.1 * hz(i, 31));
              for (const [x, y] of [[m0 - 1.25, a[0]], [m0 + 1.25, a[0]], [m1 + 1.25, b[0]], [m1 - 1.25, b[0]]]) { mueble.pos.push(...E(x, y, suelo(x, y) + HCM)); mueble.col.push(cc.r * l, cc.g * l, cc.b * l); }
              mueble.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
            }
          }
          tira(arr, i, 1, 2, 0.1, -0.1, HAR - 0.05, g.clone().multiplyScalar(0.95));
          tira(arr, i, 5, 6, 0.1, -0.1, HAR - 0.05, g.clone().multiplyScalar(0.95));
        }

        // ================= los cruces: pasos de cebra y semáforos
        const semaforos = [];
        for (const [k, cr] of cruces.entries()) {
          const P = en(cr[0]), tx = P.dx, ty = P.dy, nx = ty, ny = -tx;     // n: hacia el este (d > 0)
          const q = P.q, w0 = (q[1] !== null ? q[1] - p.ancho_aux : q[2]) - P.x, w1 = (q[6] !== null ? q[6] + p.ancho_aux : q[5]) - P.x;
          for (const sg of [-1, 1]) {                       // la cebra: franjas paralelas a la avenida, a 7 m del cruce
            for (let d = w0 + 0.5; d < w1 - 0.5; d += 1.1) {
              const ox = P.x + nx * d + tx * sg * 8.5, oy = P.y + ny * d + ty * sg * 8.5;
              const ar = suelo(ox, oy) + HV + 0.05;
              const Q = (u, v) => E(ox + tx * u + nx * v, oy + ty * u + ny * v, ar);
              cara(vias, [Q(-1.5, -0.27), Q(1.5, -0.27), Q(1.5, 0.27), Q(-1.5, 0.27)], cPintura.clone().multiplyScalar(0.95), [0, 1, 0]);
            }
          }
          if (!p.semaforos) continue;
          // dos postes en las puntas del arriate (para la avenida) y dos en las orillas de afuera (para la calle)
          const ang = Math.atan2(ty, tx);
          const postes = [[0, -11, 0], [0, 11, 0], [w0 - 1.2, -11, 1], [w1 + 1.2, 11, 1]];
          for (const [d, u, grupo] of postes) {
            const x = P.x + nx * d + tx * u, y = P.y + ny * d + ty * u, z0 = alt(x, y) + HAR * M;
            cono(semP, x, y, z0, 0, 0.35, 0.2, 0.16, 8, cNegro, null);
            cono(semP, x, y, z0, 0.35, 5.0, 0.09, 0.08, 8, cNegro, null);
            const dir = grupo === 0 ? ang + (u < 0 ? Math.PI : 0) : ang + Math.PI / 2 * (d < 0 ? 1 : -1);
            const ca = Math.cos(dir), sa = Math.sin(dir);
            const hx = x + ca * 0.28, hy = y + sa * 0.28;      // la cabeza: caja negra con visera y tres focos de cada lado
            caja(semP, hx, hy, dir, -0.2, 0.2, -0.22, 0.22, 3.5, 4.75, cNegro, { z0 });
            caja(semP, hx, hy, dir, -0.24, 0.24, -0.3, 0.3, 3.45, 3.5, cNegro, { z0 });
            for (let j = 0; j < 3; j++) {
              const h = 4.5 - j * 0.38, g = grupo === 0 ? j : 3 + j;
              for (const sg of [1, -1]) caja(lamp[g], hx + ca * sg * 0.21, hy + sa * sg * 0.21, dir, -0.03, 0.03, -0.12, 0.12, h - 0.12, h + 0.12, (j === 0 ? tonos.mal : j === 1 ? tonos.medio : tonos.bien), { z0 });
            }
            semaforos.push([x, y]);
          }
        }

        // ================= los árboles: frondosos, cipreses (los más grandes), jacarandas y manzanotes
        const arbol = ([x, y, esp, t], k) => {
          const z0 = alt(x, y) + (HAR - 0.05) * M;
          if (esp === 1) {                                  // ciprés: alto y cónico
            const H = 13 * t;
            cono(arbo, x, y, z0, 0, 1.2, 0.3, 0.25, 6, cTronco, null);
            cono(arbo, x, y, z0, 1.0, H * 0.62, 2.4 * t, 1.5 * t, 8, cCipres.clone().multiplyScalar(0.9 + 0.2 * hz(k, 40)), null);
            cono(arbo, x, y, z0, H * 0.6, H, 1.55 * t, 0.05, 8, cCipres.clone().multiplyScalar(0.95 + 0.2 * hz(k, 41)), null);
          } else if (esp === 3) {                           // manzanote: arbusto bajo
            for (let j = 0; j < 2; j++) bola(arbo, x + 0.8 * (j - 0.5), y + 0.4 * (hz(k, 42) - 0.5), z0 + 1.0 * M, 1.3 * t, 1.0 * t, cManz.clone().multiplyScalar(0.85 + 0.25 * hz(k * 3 + j, 43)), 900 + k * 3 + j);
          } else {
            const H = (esp === 2 ? 4.2 : 4.8) * t;
            cono(arbo, x, y, z0, 0, H, 0.26 * t, 0.15 * t, 6, cTronco.clone().multiplyScalar(0.9 + 0.2 * hz(k, 44)), null);
            const nb = 2;
            for (let j = 0; j < nb; j++) {
              const a = j * 2.6 + k, rr = 1.2 * t;
              if (esp === 2) {                              // jacaranda: copa ancha y aplanada
                const col = (p.jacaranda_flor ? cLila : cJacVerde).clone().multiplyScalar(0.88 + 0.24 * hz(k * 7 + j, 45));
                bola(jac, x + rr * Math.cos(a), y + rr * Math.sin(a), z0 + (H + 0.8 * hz(k * 7 + j, 46)) * M, 3.0 * t, 1.7 * t, col, 500 + k * 7 + j);
                bola(jacH, x + rr * Math.cos(a), y + rr * Math.sin(a), z0 + (H + 0.8 * hz(k * 7 + j, 46)) * M, 3.5 * t, 2.1 * t, cLila, 500 + k * 7 + j);
              } else {
                bola(arbo, x + rr * Math.cos(a), y + rr * Math.sin(a), z0 + (H + 1.0 * hz(k * 7 + j, 47)) * M, 2.6 * t, 2.2 * t,
                  cFronda.clone().lerp(lin(COL.tierra_media), 0.18 * hz(k, 48)).multiplyScalar(0.8 + 0.3 * hz(k * 7 + j, 49)), 700 + k * 7 + j);
              }
            }
          }
        };
        p.arbolado.forEach(arbol);

        // ================= bancas, farolas, monumentos y el depósito de agua (en el camino del arriate)
        const lado = (s, d) => { const P = en(s); return [P.x - P.dy * d, P.y + P.dx * d, Math.atan2(P.dy, P.dx)]; };
        const bancas = [];
        for (const [s, sg] of p.bancas) {
          const [x, y, ang] = lado(s, sg * 2.1), z0 = alt(x, y) + HCM * M, v = -sg;   // de frente al camino
          const col = cMadera.clone().multiplyScalar(0.9 + 0.2 * hz(s | 0, 50));
          caja(mueble, x, y, ang, -0.9, 0.9, -0.25 * v, 0.2 * v, 0.42, 0.47, col, { z0 });
          caja(mueble, x, y, ang, -0.9, 0.9, -0.3 * v, -0.24 * v, 0.55, 0.9, col, { z0 });
          for (const u of [-0.75, 0.75]) caja(mueble, x, y, ang, u - 0.04, u + 0.04, -0.28 * v, 0.18 * v, 0, 0.42, cNegro, { z0 });
          bancas.push([x, y, ang + (v > 0 ? Math.PI / 2 : -Math.PI / 2)]);
        }
        const farolas = [];
        p.farolas.forEach((s, k) => {
          const [x, y] = lado(s, (k % 2 ? 1 : -1) * 1.65), z0 = alt(x, y) + HCM * M;
          cono(mueble, x, y, z0, 0, 0.5, 0.14, 0.1, 8, cNegro, null);
          cono(mueble, x, y, z0, 0.5, 4.2, 0.06, 0.06, 6, cNegro, null);
          cono(focos, x, y, z0, 4.2, 4.65, 0.17, 0.24, 10, noche ? cLuz.clone().multiplyScalar(0.95) : cNegro.clone().lerp(lin(COL.costa), 0.45), null);
          cono(mueble, x, y, z0, 4.65, 4.85, 0.28, 0.04, 10, cNegro, cNegro);
          farolas.push([x, y, z0]);
        });
        const charco = (x, y, z, rr, col) => {
          const n = 16, q = luzA.pos.length / 3, AA = [[0.5, 0.55], [1, 0]];
          luzA.pos.push(...E(x, y, z)); luzA.col.push(col.r, col.g, col.b);
          for (const [f, a] of AA) for (let i = 0; i < n; i++) { const t0 = TAU * i / n; luzA.pos.push(...E(x + rr * f * Math.cos(t0) * M, y + rr * f * Math.sin(t0) * M, z)); luzA.col.push(col.r * a, col.g * a, col.b * a); }
          for (let i = 0; i < n; i++) { const j = (i + 1) % n; luzA.idx.push(q, q + 1 + i, q + 1 + j, q + 1 + i, q + 1 + n + i, q + 1 + n + j, q + 1 + i, q + 1 + n + j, q + 1 + j); }
        };
        if (noche) for (const [x, y, z0] of farolas) charco(x, y, z0 + 0.02 * M, 7, cLuz.clone().multiplyScalar(0.14));
        // los monumentos: una glorieta de piedra en el camino con un pedestal y una figura genérica (sin rostro)
        for (const [s, tipo] of p.monumentos) {
          const P = en(s), x = P.x, y = P.y, ang = Math.atan2(P.dy, P.dx), z0 = alt(x, y) + HCM * M;
          disco(mueble, x, y, z0 + 0.01 * M, 5.2, 20, cCamino.clone().multiplyScalar(1.05));
          disco(mueble, x, y, z0 + 0.02 * M, 5.2, 20, cBord, 4.8);
          caja(mueble, x, y, ang, -1.6, 1.6, -1.6, 1.6, 0, 0.35, cPiedraO, { z0, tope: cPiedra });
          caja(mueble, x, y, ang, -1.1, 1.1, -1.1, 1.1, 0.35, 2.6, cPiedra, { z0 });
          caja(mueble, x, y, ang, -1.3, 1.3, -1.3, 1.3, 2.6, 2.85, cPiedraO, { z0, tope: cPiedra });
          if (tipo === 0) {                                  // una columna con su capitel
            cono(mueble, x, y, z0, 2.85, 6.8, 0.42, 0.36, 14, cPiedra, null);
            caja(mueble, x, y, ang, -0.6, 0.6, -0.6, 0.6, 6.8, 7.2, cPiedra, { z0 });
          } else if (tipo === 1) {                           // una figura de pie, sin rostro ni pose afirmada
            cono(mueble, x, y, z0, 2.85, 4.1, 0.45, 0.32, 12, cPiedra, null);
            cono(mueble, x, y, z0, 4.1, 4.9, 0.32, 0.38, 12, cPiedra, null);
            bola(mueble, x, y, z0 + 5.25 * M, 0.3, 0.34, cPiedra, 3000 + (s | 0));
          } else {                                           // un busto sobre su fuste
            cono(mueble, x, y, z0, 2.85, 4.3, 0.3, 0.3, 12, cPiedra, null);
            caja(mueble, x, y, ang, -0.45, 0.45, -0.3, 0.3, 4.3, 4.8, cPiedra, { z0 });
            bola(mueble, x, y, z0 + 5.1 * M, 0.26, 0.32, cPiedra, 3100 + (s | 0));
          }
          for (let j = 0; j < 4; j++) { const a = ang + Math.PI / 4 + j * Math.PI / 2;   // cuatro arbustos alrededor
            bola(arbo, x + Math.cos(a) * 3.4, y + Math.sin(a) * 3.4, z0 + 0.5 * M, 0.9, 0.6, cManz.clone().multiplyScalar(0.85 + 0.2 * hz(j + (s | 0), 51)), 3200 + j + (s | 0)); }
        }
        {                                                    // el depósito de agua: un tanque redondo genérico
          const P = en(p.deposito), x = P.x, y = P.y, z0 = alt(x, y) + HCM * M;
          disco(mueble, x, y, z0 + 0.01 * M, 6.5, 20, cCamino.clone().multiplyScalar(1.02));
          cono(mueble, x, y, z0, 0, 0.5, 5.0, 5.0, 20, cPiedraO, null);
          cono(mueble, x, y, z0, 0.5, 2.9, 4.6, 4.6, 20, cPiedra.clone().multiplyScalar(0.95), null);
          cono(mueble, x, y, z0, 2.9, 3.2, 4.85, 4.85, 20, cPiedraO, null);
          disco(mueble, x, y, z0 + 3.2 * M, 4.85, 20, cPiedraO, 4.3);
          disco(mueble, x, y, z0 + 2.7 * M, 4.3, 20, cAguaD);
        }

        // ================= la plaza del Obelisco: losas en anillos, plataforma, obelisco, pebetero y cuatro pérgolas
        let llama = null, obeLuz = null;
        if (p.obelisco) {
          const [ox, oy, rp] = p.plaza, z0 = alt(ox, oy) + HPL * M;
          for (let k = 0, r = rp; r > 0.5; k++, r -= 4) disco(obe, ox, oy, z0 + 0.002 * k * M, r, 36, (k % 2 ? cAcera : cCamino).clone().multiplyScalar(dia ? 1 : 1.05), Math.max(0, r - 4));
          disco(obe, ox, oy, z0 + 0.01 * M, rp, 36, cBord, rp - 0.5);
          // jardineras en anillo entre las losas
          disco(obe, ox, oy, z0 + 0.03 * M, rp * 0.78, 36, cPasto.clone().multiplyScalar(0.95), rp * 0.66);
          // la plataforma con dos gradas
          cono(obe, ox, oy, z0, 0, 0.3, 9.5, 9.5, 24, cPiedraO, cPiedra);
          cono(obe, ox, oy, z0, 0.3, 0.6, 8.2, 8.2, 24, cPiedraO, cPiedra);
          // el obelisco (forma genérica): basa, fuste que se afina y piramidión
          const ang = 0, zb = z0 + 0.6 * M;
          caja(obe, ox, oy, ang, -2.4, 2.4, -2.4, 2.4, 0, 0.8, cPiedraO, { z0: zb, tope: cPiedra });
          caja(obe, ox, oy, ang, -1.9, 1.9, -1.9, 1.9, 0.8, 3.4, cPiedra, { z0: zb });
          caja(obe, ox, oy, ang, -2.1, 2.1, -2.1, 2.1, 3.4, 3.7, cPiedraO, { z0: zb, tope: cPiedra });
          const H0 = 3.7, H1 = 20.5, r0 = 1.25, r1 = 0.82;
          const fuste = (h, r) => [[-r, -r], [r, -r], [r, r], [-r, r]].map(([u, v]) => [ox + u * M, oy + v * M, zb + h * M]);
          const B = fuste(H0, r0), T = fuste(H1, r1);
          for (let j = 0; j < 4; j++) { const j2 = (j + 1) % 4, mx = (B[j][0] + B[j2][0]) / 2 - ox, my = (B[j][1] + B[j2][1]) / 2 - oy;
            cara(obe, [E(...B[j]), E(...B[j2]), E(...T[j2]), E(...T[j])], cPiedra.clone().multiplyScalar(1.04), [mx, 0, -my]); }
          const cima = [ox, oy, zb + (H1 + 1.7) * M];
          for (let j = 0; j < 4; j++) { const j2 = (j + 1) % 4, mx = (T[j][0] + T[j2][0]) / 2 - ox, my = (T[j][1] + T[j2][1]) / 2 - oy;
            cara(obe, [E(...T[j]), E(...T[j2]), E(...cima), E(...cima)], cPiedra.clone().multiplyScalar(1.1), [mx, 0.6, -my]); }
          // el escudo arriba: una placa de bronce en cada cara (sin dibujo ni texto)
          for (let j = 0; j < 4; j++) {
            const a = j * Math.PI / 2, h = H1 - 3.2, rr = r0 + (r1 - r0) * (h - H0) / (H1 - H0) + 0.04;
            const cx0 = ox + Math.cos(a) * rr * M, cy0 = oy + Math.sin(a) * rr * M, tx = -Math.sin(a), ty = Math.cos(a);
            const Q = (u, w) => E(cx0 + tx * u * M, cy0 + ty * u * M, zb + w * M);
            cara(obe, [Q(-0.5, h - 0.6), Q(0.5, h - 0.6), Q(0.5, h + 0.45), Q(-0.5, h + 0.45)], cCobre.clone().lerp(tonos.medio, 0.3), [Math.cos(a), 0, -Math.sin(a)]);
            cara(obe, [Q(-0.5, h - 0.6), Q(0.5, h - 0.6), Q(0, h - 1.0), Q(0, h - 1.0)], cCobre.clone().lerp(tonos.medio, 0.3), [Math.cos(a), 0, -Math.sin(a)]);
          }
          // el pebetero de cobre con la llama, al frente (hacia la avenida)
          const [ex, ey] = eje[0], dd = Math.hypot(ex - ox, ey - oy) || 1, px = ox + (ex - ox) / dd * 6.6, py = oy + (ey - oy) / dd * 6.6;
          const zp = alt(px, py) + (HPL + 0.6) * M;
          cono(obe, px, py, zp, 0, 0.25, 0.75, 0.7, 14, cPiedraO, cPiedra);
          cono(obe, px, py, zp, 0.25, 1.1, 0.16, 0.12, 12, cCobre, null);
          cono(obe, px, py, zp, 1.1, 1.65, 0.18, 0.85, 16, cCobre.clone().multiplyScalar(1.1), null);
          disco(obe, px, py, zp + 1.6 * M, 0.82, 16, cCobre.clone().multiplyScalar(0.55));
          const fl = malla.nueva();
          for (const [r, h, k] of [[0.55, 1.3, 1.0], [0.36, 1.9, 1.25], [0.2, 2.4, 1.5]]) {
            for (let i = 0; i < 9; i++) {
              const a0 = TAU * i / 9, a1 = TAU * (i + 1) / 9, q = fl.pos.length / 3, col = cLuz.clone().lerp(tonos.medio, 0.35 / k).multiplyScalar(k);
              for (const [x, y, z] of [[r * Math.cos(a0), r * Math.sin(a0), 0], [r * Math.cos(a1), r * Math.sin(a1), 0], [0, 0, h]]) { fl.pos.push(x * M, z * M, -y * M); fl.col.push(col.r, col.g, col.b); }
              fl.idx.push(q, q + 1, q + 2);
            }
          }
          const mFl = malla.material({ desfase: 0 }); mFl.uniforms.uBrillo.value = noche ? 1.9 : 1.35;
          const mL = new THREE.Mesh(malla.geometria(fl), mFl); mL.frustumCulled = false; mL.renderOrder = 6; mL.position.set(px, zp + 1.6 * M, -py); scene.add(mL);
          llama = { mesh: mL, k: hz(3, 60) * 10 };
          if (noche) { const lz = malla.nueva(); const cl = cLuz.clone().lerp(tonos.medio, 0.3).multiplyScalar(0.22);
            const q = lz.pos.length / 3, n = 18; lz.pos.push(...E(px, py, zp - 0.55 * M)); lz.col.push(cl.r, cl.g, cl.b);
            for (let i = 0; i < n; i++) { const t0 = TAU * i / n; lz.pos.push(...E(px + 9 * Math.cos(t0) * M, py + 9 * Math.sin(t0) * M, zp - 0.55 * M)); lz.col.push(0, 0, 0); }
            for (let i = 0; i < n; i++) lz.idx.push(q, q + 1 + i, q + 1 + (i + 1) % n);
            const mz = malla.material({ aditivo: true, desfase: 4 }); const m = new THREE.Mesh(malla.geometria(lz), mz); m.frustumCulled = false; m.renderOrder = 4; scene.add(m);
            obeLuz = mz; }
          // las cuatro pérgolas, en las diagonales
          for (let j = 0; j < 4; j++) {
            const a = Math.PI / 4 + j * Math.PI / 2, rr = rp * 0.55, gx = ox + Math.cos(a) * rr * M, gy = oy + Math.sin(a) * rr * M, gz = alt(gx, gy) + HPL * M;
            const ang = a + Math.PI / 2;                     // a lo largo del anillo
            for (const u of [-3, -1, 1, 3]) for (const v of [-1.3, 1.3]) caja(obe, gx, gy, ang, u - 0.13, u + 0.13, v - 0.13, v + 0.13, 0, 2.9, cPiedra, { z0: gz });
            for (const v of [-1.3, 1.3]) caja(obe, gx, gy, ang, -3.6, 3.6, v - 0.12, v + 0.12, 2.9, 3.15, cMadera, { z0: gz });
            for (let u = -3.3; u <= 3.31; u += 0.6) caja(obe, gx, gy, ang, u - 0.06, u + 0.06, -1.8, 1.8, 3.15, 3.3, cMadera.clone().multiplyScalar(1.08), { z0: gz });
            for (const v of [-2.1, 2.1]) caja(obe, gx, gy, ang, -2.2, 2.2, v - 0.25, v + 0.25, 0.42, 0.47, cMadera, { z0: gz });   // bancas bajo la pérgola
          }
          // árboles alrededor de la plaza
          for (let j = 0; j < 8; j++) { const a = j * Math.PI / 4 + 0.2, rr = rp * 0.72;
            arbol([ox + Math.cos(a) * rr, oy + Math.sin(a) * rr, j === 5 ? 2 : 0, 0.85], 4000 + j); }
        }

        // ================= las mallas
        const pone = (acc, mat, orden) => { if (!acc.pos.length) return null; const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        const matVias = malla.material({ desfase: 2 }), matArr = malla.material({ desfase: 3 }), matMue = malla.material({ desfase: 4 });
        const matArb = malla.material(), matJac = malla.material(), matObe = malla.material({ desfase: 3 }), matSem = malla.material(), matFoc = malla.material();
        pone(vias, matVias, 2); pone(arr, matArr, 3); pone(mueble, matMue, 4); pone(arbo, matArb, 5); pone(jac, matJac, 5); pone(obe, matObe, 5); pone(semP, matSem, 5);
        pone(focos, matFoc, 5); matFoc.uniforms.uBrillo.value = noche ? 1.8 : 1.0;
        if (luzA.pos.length) pone(luzA, malla.material({ aditivo: true, desfase: 5 }), 4);
        const matJacH = malla.material({ alfa: 0, desfase: 0 }); matJacH.depthWrite = false; const mJacH = pone(jacH, matJacH, 7);
        const matLamp = lamp.map((acc) => { const m = malla.material(); pone(acc, m, 6); return m; });
        for (const m of [matObe, matSem, matArr, matVias]) m.uniforms.cTinte.value.copy(cAc);
        // la avenida entera en el acento: una banda sobre las dos vías y el arriate (apagada hasta su resaltar)
        const enc = malla.nueva();
        for (const k of ["norte", "sur"]) malla.banda(enc, V[k], p.ancho_via + 1, HAR + 0.2, 10, cAc);
        for (let i = 0; i + 1 < sec.length; i++) tira(enc, i, 3, 4, 0, 0, HAR + 0.22, cAc);
        const matEnc = malla.material({ alfa: 0, desfase: 6 }); const mEnc = pone(enc, matEnc, 8); matEnc.depthWrite = false;
        const bordes = [];
        for (const [k, sg] of [["norte", -1], ["sur", 1]]) bordes.push(ctx.cinta(ctx.pegar(correr(V[k], sg * (hv + 0.2)), 8, HR + 0.3), cAc, A * 1.6, 0, 9));

        // ================= la gente: caminan y corren por el camino del arriate; alguna sentada en las bancas
        const NP = clamp(p.personas | 0, 0, 40), NS = Math.min(bancas.length, Math.floor(NP / 5)), NC = NP - NS;
        const pisoClaro = 0.2126 * cCamino.r + 0.7152 * cCamino.g + 0.0722 * cCamino.b > 0.22;
        const camisas = [tonos.mal.clone(), lin(COL.mar).multiplyScalar(0.9), tonos.bien.clone(), lin(COL.costa), tonos.medio.clone(), lin(COL.tierra_media), tonos.secundario.clone()]
          .map((x) => (pisoClaro ? x.multiplyScalar(0.55) : x.lerp(lin(COL.costa), 0.25).multiplyScalar(1.3)));
        const gente = [];
        for (let i = 0; i < NC; i++) {
          const corre = hz(i, 70) < 0.3;
          gente.push({ cam: true, dir: hz(i, 71) > 0.5 ? 1 : -1, vel: corre ? 2.4 + 0.6 * hz(i, 72) : 1.0 + 0.4 * hz(i, 72), s0: hz(i, 73) * L, d: (hz(i, 74) - 0.5) * 1.6 });
        }
        for (let i = 0; i < NS; i++) { const b = bancas[Math.floor(i * bancas.length / Math.max(1, NS))]; gente.push({ cam: false, b }); }
        // el tramo donde hay camino (el arriate de más de 5 m): ahí camina la gente
        let iA = sec.findIndex((q) => q[4] - q[3] > 5), iB = sec.length - 1 - [...sec].reverse().findIndex((q) => q[4] - q[3] > 5);
        if (iA < 0) { iA = 0; iB = sec.length - 1; }
        const sA = sAc[iA] + 4, sB = sAc[iB] - 4;
        for (const g of gente) if (g.cam) g.s0 = sA + (g.s0 / L) * (sB - sA);
        const KG = clamp(+p.gente_tamano || 1, 1, 2);
        const flP = NP ? ctx.flota("persona", NP, { tamano: KG, lev: HCM, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991,
          color: (i) => camisas[(i + Math.floor(hz(1, 75) * camisas.length)) % camisas.length],
          pose: (i) => (gente[i].cam ? "caminar" : { nombre: "sentado", banco: false }) }) : null;

        return { id: p.id, L, sA, sB, en, gente, flP, llama, obeLuz, matEnc, mEnc, bordes, matJac, matJacH, mJacH, matObe, matSem, matLamp, matArr, matVias,
          noche, flor: !!p.jacaranda_flor, fase: hz(9, 76) * 14 };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kp = b ? clamp((b - 1) / 0.9, 0, 1) : 0;
        const el = [0, 0, 0, 0, 0];
        for (const e of ctx.cuadro.elementos[s.id] || []) if (e.i >= 0 && e.i < 5) el[e.i] = Math.max(el[e.i], clamp(e.k, 0, 1));
        // la avenida entera (resaltar la pieza o con elemento en la avenida)
        const kA = Math.max(kp, el[0]);
        s.matEnc.uniforms.uAlfa.value = 0.42 * kA; s.mEnc.visible = kA > 0.002;
        for (const c of s.bordes) c.mat.uniforms.uAlfa.value = kA;
        s.matVias.uniforms.uTinte.value = 0.25 * kA;
        // las jacarandas: se encienden en lila
        const kJ = Math.max(el[1], 0.6 * kp);
        s.matJac.uniforms.uBrillo.value = 1 + 1.3 * kJ;
        s.matJacH.uniforms.uAlfa.value = 0.7 * kJ; if (s.mJacH) s.mJacH.visible = kJ > 0.002;
        // el obelisco, los semáforos y el arriate
        s.matObe.uniforms.uTinte.value = 0.45 * el[2]; s.matObe.uniforms.uBrillo.value = 1 + 0.35 * el[2];
        s.matSem.uniforms.uTinte.value = 0.6 * el[3];
        s.matArr.uniforms.uTinte.value = 0.4 * el[4]; s.matArr.uniforms.uBrillo.value = 1 + 0.25 * el[4];
        // los semáforos: la avenida en verde 7 s, ámbar 2, rojo 5; la calle al revés (ciclo de 14 s, puro de t)
        const f = (((t + s.fase) % 14) + 14) % 14;
        const av = f < 7 ? 2 : f < 9 ? 1 : 0, ca = f >= 9.5 && f < 12.5 ? 2 : f >= 12.5 && f < 13.6 ? 1 : 0;
        const on = s.noche ? 2.3 : 1.6, off = 0.22, kS = 1 + 0.5 * el[3];
        s.matLamp.forEach((m, j) => { m.uniforms.uBrillo.value = (j < 3 ? (j === av ? on : off) : (j - 3 === ca ? on : off)) * kS; });
        // la llama: tiembla (escala y giro, función de t)
        if (s.llama) {
          const k = s.llama.k, sy = 1 + 0.14 * Math.sin(t * 9.1 + k) + 0.08 * Math.sin(t * 15.7 + 2 * k), sx = 1 + 0.07 * Math.sin(t * 11.3 + 3 * k);
          s.llama.mesh.scale.set(sx, sy, sx); s.llama.mesh.rotation.y = 0.4 * Math.sin(t * 2.3 + k);
          if (s.obeLuz) s.obeLuz.uniforms.uBrillo.value = 0.85 + 0.15 * Math.sin(t * 9.1 + k);
        }
        // la gente: la posición a lo largo del camino es función de t
        if (s.flP) {
          s.gente.forEach((g, i) => {
            if (g.cam) {
              const LL = s.sB - s.sA, u = ((((g.s0 - s.sA + g.dir * g.vel * t) % LL) + LL) % LL), sv = s.sA + u, P = s.en(sv);
              const kk = clamp(u / 6, 0, 1) * clamp((LL - u) / 6, 0, 1);
              s.flP.poner(i, P.x - P.dy * g.d, P.y + P.dx * g.d, P.dx * g.dir, P.dy * g.dir, kk, 0, g.vel);
            } else {
              const [x, y, a] = g.b;
              s.flP.poner(i, x, y, Math.cos(a), Math.sin(a), 1, 0, 0);
            }
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
