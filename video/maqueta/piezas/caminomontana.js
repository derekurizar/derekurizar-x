// Pieza «caminomontana» (ficha: caminomontana.json; reglas: scripts/maqueta_tipos/caminomontana.py): un camino de montaña
// genérico, sin lugar real. Centrado en `lugar` y orientado por `rumbo` (u: hacia donde sube; v: a su izquierda). Todo en
// METROS × `tamano`.
// - El EJE va de u = −170 a +170 con `curvas` medias ondas de un seno (radio ≥ 50 m) y sube `pendiente_m` de punta a punta
//   (desde 5 m sobre el suelo). Los caminos «<id>.carril-1» (subida) y «<id>.carril-2» (bajada) los publica el .py.
// - El TERRENO es un campo de alturas propio: a la izquierda de quien sube, la cuneta de concreto, el TALUD cortado (2:1,
//   6–9.5 m, con vetas de tierra y rocas incrustadas) y el monte que sigue subiendo; a la derecha, la berma de grava con el
//   GUARDAVÍA (lámina sobre postes) y la ladera que cae hasta el suelo del mundo. Cerca del camino lo dibuja una banda
//   barrida a lo largo del eje (fina, exacta); lejos, una cuadrícula de 3 m (rebajada bajo la banda para no asomarse).
// - El ASFALTO con su tono por tramos, la línea central doble y las orillas pintadas A RAS (pegadas al asfalto).
// - La vegetación de sierra: pinos en grupos, matorral sobre la berma y el borde del corte, y arriba un CAFETAL en hileras
//   bajo árboles de sombra (copas anchas y planas) con matas de banano. Al fondo, la sierra en tres filas redondeadas (sin
//   conos volcánicos).
// - Los VEHÍCULOS propios: el camión de sacos (objeto camionsacos, en el acento; `camion: false` lo quita) y `vehiculos` más
//   (carro, moto, carro, camión…), cada uno una flota de uno metida en un grupo que lo sube a la altura del camino y lo
//   inclina con la pendiente. Posición = función de t (seek puro). Además la pieza PUBLICA su relieve (caminomontana.py →
//   `_alturas`): un actor o un flujo del núcleo en «<id>.carril-1» / «<id>.carril-2» sube e inclina igual (motor.js: flota).
// - De noche (ES.noche): faros y pilotos de los vehículos (los pone la flota) y captafaros en el guardavía.
// Sin colores escritos (ctx.tonos, ctx.COL); sin texto, km ni señales.
(function (MAQ) {
  const OTROS = ["carro", "moto", "carro", "camion", "carro", "moto"];   // el mismo orden de caminomontana.py
  MAQ.PIEZAS.caminomontana = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      // ---- los tonos (todos del estilo)
      const cAsf = tonos.asfalto.clone().lerp(tonos.pavimento, oscuro ? 0.22 : 0.1);
      const cRayaC = lin(ES.modo === 4 ? COL.linea : COL.luces), cRayaB = lin(ES.modo === 4 ? COL.linea : COL.costa);
      const cConc = tonos.pavimento.clone().lerp(tonos.muro, 0.25);
      const cGrava = tonos.arena.clone().lerp(tonos.asfalto, 0.4);
      const cTierra = lin(COL.tierra_media).lerp(tonos.arena, 0.35).multiplyScalar(oscuro ? 0.95 : 0.85);
      const cVeta = lin(COL.tierra_alta).lerp(tonos.arena, 0.25).multiplyScalar(oscuro ? 0.85 : 0.72);
      const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.45);
      const cPasto = tonos.campo.clone(), cPasto2 = tonos.campo2.clone();
      const cBosque = tonos.verde.clone().lerp(tonos.campo2, 0.45).multiplyScalar(0.85);
      const cSuelo = tonos.calle.clone().lerp(tonos.campo2, 0.45).multiplyScalar(oscuro ? 0.9 : 0.78);
      const cPino = tonos.verde.clone().lerp(tonos.campo2, 0.3).multiplyScalar(dia ? 0.6 : oscuro ? 1.0 : 0.75);
      const cPino2 = cPino.clone().lerp(tonos.bien, 0.12).multiplyScalar(1.15);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cHoja = dia ? tonos.bien.clone().lerp(tonos.campo, 0.45).multiplyScalar(0.5)
        : tonos.bien.clone().lerp(tonos.campo, oscuro ? 0.66 : 0.55).multiplyScalar(oscuro ? 0.6 : 0.62);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.7 : dia ? 0.95 : 1);
      const cBanano = tonos.bien.clone().lerp(tonos.campo, 0.4).multiplyScalar(oscuro ? 0.8 : 0.9);
      const cMata = tonos.campo2.clone().lerp(tonos.verde, 0.5).multiplyScalar(oscuro ? 1.2 : 0.8);
      const cMetal = tonos.pavimento.clone().lerp(tonos.muro, 0.6).multiplyScalar(oscuro ? 1.2 : 1.05);
      const cPoste = cMetal.clone().multiplyScalar(0.62);
      const cCorte = lin(COL.tierra_media).lerp(tonos.asfalto, 0.45).multiplyScalar(0.8);
      const cSierra = [0, 1, 2].map((j) => lin(COL.tierra_alta).lerp(tonos.verde, 0.55 - 0.1 * j).lerp(tonos.agua, 0.18 + 0.2 * j)
        .multiplyScalar((oscuro ? 1.1 : 0.85) * (1 + 0.1 * j)));
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const liso = (a, b, x) => { const v = clamp((x - a) / (b - a), 0, 1); return v * v * (3 - 2 * v); };
      const smin = (a, b, k) => { const h = clamp(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h); };

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
      const tubo = (acc, A, B, r, seg, col, tapa) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2));
          if (tapa) cara(acc, [S(B, va), S(B, vb), B, B], tapa, a);
        }
      };
      // un cono (copa de pino): base en P (radio r) y punta h más arriba, con su luz por cara
      const cono = (acc, P, r, h, seg, col) => {
        const T = [P[0], P[1] + h, P[2]];
        for (let i = 0; i < seg; i++) {
          const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
          const A = [P[0] + r * Math.cos(a0), P[1], P[2] + r * Math.sin(a0)], B = [P[0] + r * Math.cos(a1), P[1], P[2] + r * Math.sin(a1)];
          cara(acc, [A, B, T, T], col, [Math.cos(am), r / h, Math.sin(am)]);
          cara(acc, [A, B, P, P], col.clone().multiplyScalar(0.55), [0, -1, 0]);
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
      // una lámina (filas × columnas de puntos de la escena) con normales suaves y la luz horneada por vértice
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

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.suelo(p.x, p.y);                                   // el suelo del mundo (sin el relieve que esta pieza publica)
        const W2 = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W2(u, v); return [x, base0 + h * M, -y]; };
        const piso = (u, v) => (ctx.suelo(...W2(u, v)) - base0) / M;
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };

        // ================= el eje (el mismo de caminomontana.py) y su largo
        const U = 170, NCV = clamp(p.curvas | 0, 1, 3), kk = Math.PI * NCV / (2 * U), A = Math.min(28, 1 / (50 * kk * kk));
        const vc = (u) => A * Math.sin(kk * (u + U)), vcp = (u) => A * kk * Math.cos(kk * (u + U));
        const NT = 2 * U, SS = new Float64Array(NT + 1);
        for (let i = 1; i <= NT; i++) SS[i] = SS[i - 1] + Math.hypot(1, vc(-U + i) - vc(-U + i - 1));
        const LT = SS[NT];
        const sDe = (u) => { const f = clamp(u + U, 0, NT), i = Math.min(NT - 1, Math.floor(f)); return SS[i] + (SS[i + 1] - SS[i]) * (f - i); };
        const uDe = (s) => { const ss = clamp(s, 0, LT); let i = clamp(Math.floor(ss / LT * NT), 0, NT - 1);
          while (i > 0 && SS[i] > ss) i--; while (i < NT - 1 && SS[i + 1] < ss) i++;
          return -U + i + (ss - SS[i]) / Math.max(1e-6, SS[i + 1] - SS[i]); };
        const PL = p.pendiente_m / K, H0 = 5, GR = PL / LT;                 // en metros locales
        const hr = (s) => H0 + PL * clamp(s, 0, LT) / LT;
        // un punto a d del eje (d > 0: lado del monte) en el s del eje → [u, v]
        const enS = (s, d) => { const u = uDe(s), th = Math.atan(vcp(u)); return [u - d * Math.sin(th), vc(u) + d * Math.cos(th), th]; };

        // ================= el perfil de la ladera (relativo al camino) y el campo de alturas
        const W = 3.7, C1 = W + 0.25, C2 = W + 0.75, C3 = W + 1.25, BER = W + 1.4;
        const Hc = (u) => 6 + 3.5 * ruido(u, 7, 26, 21);
        const perfil = (u, d) => {
          if (d >= 0) {
            if (d <= W) return 0;
            if (d <= C1) return 0.06;
            if (d <= C2) return 0.06 - 0.5 * (d - C1) / 0.5;
            if (d <= C3) return -0.44 + 0.5 * (d - C2) / 0.5;
            const hc = Hc(u), dl = C3 + hc / 2, g1 = 0.4 + 0.25 * ruido(u, d, 40, 22);
            const corte = 0.06 + 2 * (d - C3) + 0.35 * (ruido(u, d, 1.7, 23) - 0.5) * liso(C3, C3 + 1, d);
            const nat = hc + g1 * (d - dl) + 10 * (ruido(u, d, 36, 24) - 0.5) * liso(dl, dl + 18, d);
            return smin(corte, nat, 1.3);
          }
          const e = -d;
          if (e <= W) return 0;
          if (e <= BER) return -0.03;
          const g2 = 0.75 + 0.2 * ruido(u, e, 30, 25);
          return smin(-0.03, -0.03 - g2 * (e - BER) + 5 * (ruido(u, e, 30, 26) - 0.5) * liso(BER, BER + 14, e), 0.6);
        };
        const dDe = (u, v) => (v - vc(u)) / Math.sqrt(1 + vcp(u) * vcp(u));
        const campo = (u, v) => { const d = dDe(u, v), h = hr(sDe(u)) + perfil(u, d), f = piso(u, v) - 0.25;
          return { h: h > f + 1.2 ? h : -smin(-h, -f, 1.2), d }; };
        const bajar = (u, d) => { const dl = C3 + Hc(u) / 2;
          return d >= 0 ? 1.5 * (1 - liso(dl + 1, dl + 4, d)) : 1.5 * (1 - liso(BER + 1.6, BER + 4.6, -d)); };
        const dLabio = (u) => C3 + Hc(u) / 2;

        const nueva = () => malla.nueva();
        const mats = [];
        const poner = (acc, op, orden) => { const mat = malla.material(op || {}); mats.push(mat); malla.poner(acc, mat, orden); return mat; };

        // ================= la cuadrícula (lejos del camino) con sus faldones
        const VD = 150, VU = 120, PASO = 3;
        const NU = Math.round(2 * U / PASO), NV = Math.round((VD + VU) / PASO);
        const tonoSuelo = (u, v, d, h, rel) => {
          const n1 = ruido(u, v, 22, 31), n2 = ruido(u, v, 6, 32);
          let c;
          if (d >= 0) {
            const dl = dLabio(u);
            if (d < dl + 1) c = cTierra.clone().lerp(cVeta, 0.5 + 0.5 * Math.sin(h * 1.7 + n2 * 3));
            else c = cPasto.clone().lerp(cBosque, clamp(n1 * 1.4 - 0.2, 0, 1)).lerp(cPasto2, 0.25 * n2);
          } else {
            const e = -d;
            if (e < BER + 0.2) c = cGrava.clone();
            else c = cTierra.clone().lerp(cPasto, liso(BER + 1, BER + 9, e)).lerp(cBosque, 0.6 * clamp(n1 * 1.5 - 0.4, 0, 1) * liso(BER + 6, BER + 20, e));
          }
          if (rel < 0.3) c.lerp(cPasto, 0.6);                                    // el fondo del valle
          return c.multiplyScalar(0.9 + 0.12 * n2);
        };
        const suelo = nueva(), Pg = [], Cg = [];
        for (let j = 0; j <= NV; j++) {
          const v = -VD + j * PASO, fila = [], filc = [];
          for (let i = 0; i <= NU; i++) {
            const u = -U + i * PASO, q = campo(u, v), h = q.h - bajar(u, q.d);
            fila.push(E(u, v, h)); filc.push(tonoSuelo(u, v, q.d, q.h, q.h - piso(u, v)));
          }
          Pg.push(fila); Cg.push(filc);
        }
        lamina(suelo, Pg, Cg);
        // los faldones: de la orilla de la cuadrícula al suelo del mundo
        const falda = nueva();
        const borde = (pts) => { for (let i = 0; i + 1 < pts.length; i++) { const [a, b] = [pts[i], pts[i + 1]];
          const fa = piso(a[0], a[1]) - 0.6, fb = piso(b[0], b[1]) - 0.6, ha = a[2], hb = b[2];
          if (ha - fa < 0.2 && hb - fb < 0.2) continue;
          cara(falda, [E(a[0], a[1], fa), E(b[0], b[1], fb), E(b[0], b[1], hb), E(a[0], a[1], ha)], cCorte, null); } };
        for (const [i0, j0, di, dj, n] of [[0, 0, 1, 0, NU], [0, NV, 1, 0, NU], [0, 0, 0, 1, NV], [NU, 0, 0, 1, NV]]) {
          const pts = []; for (let k = 0; k <= n; k++) { const i = i0 + di * k, j = j0 + dj * k, u = -U + i * PASO, v = -VD + j * PASO; pts.push([u, v, campo(u, v).h - bajar(u, campo(u, v).d)]); }
          borde(pts);
        }

        // ================= la banda barrida junto al camino: berma, ladera baja, cuneta, talud y su labio
        const banda = nueva(), asf = nueva(), rayas = nueva();
        const DS = 2, NR = Math.ceil(LT / DS);
        const Pb = [], Cb = [], Pa = [], Ca = [];
        for (let i = 0; i <= NR; i++) {
          const s = Math.min(LT, i * DS), u = uDe(s), hc = Hc(u), dl = C3 + hc / 2, hs = hr(s);
          const D = [-(BER + 7), -(BER + 5.5), -(BER + 4), -(BER + 2.8), -(BER + 1.8), -(BER + 0.9), -BER, -W, W, C1, C2, C3];
          for (let k = 1; k <= 9; k++) D.push(C3 + (dl + 6 - C3) * k / 9);
          const fila = [], filc = [];
          for (const d of D) {
            const [uu, vv] = enS(s, d), q = campo(uu, vv), h = Math.abs(d) <= W ? hs + 0.03 : q.h;
            fila.push(E(uu, vv, h));
            let c;
            if (d < -BER) c = cTierra.clone().lerp(cPasto, liso(BER + 1, BER + 9, -d)).multiplyScalar(0.92 + 0.1 * ruido(uu, vv, 5, 33));
            else if (d <= -W) c = cGrava.clone().multiplyScalar(0.95 + 0.1 * ruido(uu, vv, 3, 34));
            else if (d <= W) c = cAsf;
            else if (d <= C3 + 0.01) c = cConc.clone();
            else if (d < dl - 0.2) c = cTierra.clone().lerp(cVeta, 0.5 + 0.5 * Math.sin((h - hs) * 1.9 + 2.5 * ruido(uu, vv, 4, 35))).lerp(cRoca, 0.3 * ruido(uu, vv, 2.5, 36));
            else c = cTierra.clone().lerp(cPasto, liso(dl - 0.2, dl + 3, d)).lerp(cBosque, 0.3 * ruido(uu, vv, 12, 37));
            filc.push(c);
          }
          Pb.push(fila); Cb.push(filc);
          // el asfalto (su propia lámina, por encima de la banda) con su tono por tramos
          const ta = cAsf.clone().multiplyScalar(0.9 + 0.14 * ruido(s, 0, 14, 38) + 0.05 * hz(i, 39));
          const fa = [], fc = [];
          for (const d of [-W, -W / 2, 0, W / 2, W]) { const [uu, vv] = enS(s, d); fa.push(E(uu, vv, hs + 0.05)); fc.push(ta); }
          Pa.push(fa); Ca.push(fc);
        }
        lamina(banda, Pb, Cb);
        lamina(asf, Pa, Ca);
        // las rayas, a ras del asfalto: la central doble (continua: curvas sin rebase) y las dos orillas
        const tira = (acc, d0, d1, col, h) => {
          for (let i = 0; i < NR; i++) {
            const s0 = i * DS, s1 = Math.min(LT, (i + 1) * DS), a0 = enS(s0, d0), a1 = enS(s1, d0), b0 = enS(s0, d1), b1 = enS(s1, d1);
            cara(acc, [E(a0[0], a0[1], hr(s0) + h), E(a1[0], a1[1], hr(s1) + h), E(b1[0], b1[1], hr(s1) + h), E(b0[0], b0[1], hr(s0) + h)], col, [0, 1, 0]);
          }
        };
        tira(rayas, 0.08, 0.2, cRayaC, 0.065); tira(rayas, -0.2, -0.08, cRayaC, 0.065);
        tira(rayas, W - 0.5, W - 0.35, cRayaB, 0.065); tira(rayas, -(W - 0.35), -(W - 0.5), cRayaB, 0.065);

        // ================= el guardavía: postes cada 4 m sobre la berma y la lámina en dos ondas
        const solido = nueva(), veg = nueva();
        const captas = [];
        if (p.guardavia) {
          const dP = -(W + 0.85);
          for (let s = 2, k = 0; s < LT - 1; s += 4, k++) {
            const [uu, vv] = enS(s, dP), h = hr(s);
            tubo(solido, E(uu, vv, h - 0.3), E(uu, vv, h + 0.78), 0.075 * M, 4, cPoste, cPoste);
            if (k % 3 === 0) captas.push(E(...enS(s, dP + 0.12).slice(0, 2), h + 0.66));
          }
          for (const [d, h0, h1, kc] of [[-(W + 0.72), 0.5, 0.64, 1.0], [-(W + 0.68), 0.64, 0.7, 1.12], [-(W + 0.72), 0.7, 0.82, 0.95]]) {
            for (let s = 1; s < LT - 1.5; s += 2) {
              const s1 = Math.min(LT - 1, s + 2), a = enS(s, d), b = enS(s1, d);
              cara(solido, [E(a[0], a[1], hr(s) + h0), E(b[0], b[1], hr(s1) + h0), E(b[0], b[1], hr(s1) + h1), E(a[0], a[1], hr(s) + h1)],
                cMetal.clone().multiplyScalar(kc), null);
            }
          }
        }

        // ================= la vegetación: pinos, matorral, rocas del talud y el cafetal de arriba
        const pino = (u, v, h, alto, k) => {
          const P = E(u, v, h), T = 4 + (k % 2), rb = alto * (0.28 + 0.06 * hz(k, 41));
          tubo(veg, [P[0], P[1] - 0.3 * M, P[2]], [P[0], P[1] + alto * 0.45 * M, P[2]], 0.12 * alto / 10 * M, 6, cTronco, null);
          for (let j = 0; j < T; j++) {
            const y0 = alto * (0.22 + 0.62 * j / T), rr = rb * (1 - 0.68 * j / T), hh = alto * (0.42 - 0.04 * j);
            cono(veg, [P[0], P[1] + y0 * M, P[2]], rr * M, hh * M, 9, (j % 2 ? cPino2 : cPino).clone().multiplyScalar(0.92 + 0.14 * hz(k, 42 + j)));
          }
        };
        const mata = (u, v, h, s, k) => {
          const P = E(u, v, h);
          for (let j = 0; j < 3; j++) {
            const a = TAU * hz(k, 50 + j), rr = s * 0.55;
            gema(veg, [P[0] + Math.cos(a) * rr * M, P[1] + s * (0.45 + 0.2 * hz(k, 53 + j)) * M, P[2] + Math.sin(a) * rr * M],
              s * 0.75 * M, s * 0.6 * M, s * 0.7 * M, a, cMata.clone().multiplyScalar(0.85 + 0.3 * hz(k, 56 + j)));
          }
        };
        const zonaCafe = (u, d) => { const dl = dLabio(u); return u > -U * 0.75 && u < U * 0.15 && d > dl + 8 && d < dl + 40; };
        // pinos: en grupos (ruido) en el monte y en la ladera baja, nunca sobre el camino ni en el cafetal
        let npin = 0;
        for (let k = 0; k < 900 && npin < 150; k++) {
          const u = -U + 4 + (2 * U - 8) * hz(k, 60), v = -VD + 4 + (VD + VU - 8) * hz(k, 61), q = campo(u, v), d = q.d;
          const ok = d > dLabio(u) + 2.5 ? !zonaCafe(u, d) : d < -(BER + 4);
          if (!ok || ruido(u, v, 34, 62) < 0.42 || q.h - piso(u, v) < 0.5 && hz(k, 63) < 0.7) continue;
          pino(u, v, q.h, 8 + 8 * hz(k, 64), k); npin++;
        }
        // matorral: sobre la berma (detrás del guardavía), al pie de la ladera baja y en el labio del corte
        for (let k = 0; k < 260; k++) {
          const s = LT * hz(k, 70), lado = hz(k, 71) < 0.5;
          const d = lado ? -(BER + 0.6 + 6 * hz(k, 72)) : dLabio(uDe(s)) + 0.4 + 4 * hz(k, 72);
          const [uu, vv] = enS(s, d); mata(uu, vv, campo(uu, vv).h, 0.6 + 0.9 * hz(k, 73), k);
        }
        for (let k = 0; k < 160; k++) {
          const u = -U + 2 * U * hz(k, 74), v = -VD + (VD + VU) * hz(k, 75), q = campo(u, v);
          if ((q.d > -(BER + 3) && q.d < dLabio(u) + 1) || zonaCafe(u, q.d)) continue;
          mata(u, v, q.h, 0.8 + 1.1 * hz(k, 76), k + 300);
        }
        // rocas incrustadas en el talud
        for (let k = 0; k < 130; k++) {
          const s = LT * hz(k, 80), u0 = uDe(s), dl = dLabio(u0), d = C3 + 0.4 + (dl - C3 - 0.6) * hz(k, 81), [uu, vv] = enS(s, d), h = campo(uu, vv).h;
          const rr = 0.35 + 0.7 * hz(k, 82);
          gema(solido, E(uu, vv, h + rr * 0.1), rr * 1.2 * M, rr * 0.8 * M, rr * M, TAU * hz(k, 83), cRoca.clone().multiplyScalar(0.8 + 0.35 * hz(k, 84)));
        }
        // el cafetal: hileras a lo largo del monte, cafetos bajo árboles de sombra (copas planas) y matas de banano
        for (let fila = 0, k = 0; fila < 12; fila++) {
          for (let u = -U * 0.75 + 2; u < U * 0.15 - 2; u += 2.1, k++) {
            const dl = dLabio(u), d = dl + 9 + fila * 2.6 + 0.4 * Math.sin(u * 0.08 + fila), v = vc(u) + d * Math.sqrt(1 + vcp(u) * vcp(u));
            if (hz(k, 90) < 0.08) continue;
            const h = campo(u, v).h, P = E(u, v, h), a = 0.9 + 0.35 * hz(k, 91), c = cHoja.clone().multiplyScalar(0.85 + 0.3 * hz(k, 92));
            gema(veg, [P[0], P[1] + a * 0.75 * M, P[2]], 0.75 * a * M, 0.8 * a * M, 0.75 * a * M, TAU * hz(k, 93), c);
            gema(veg, [P[0], P[1] + a * 1.45 * M, P[2]], 0.45 * a * M, 0.45 * a * M, 0.45 * a * M, TAU * hz(k, 94), c.clone().multiplyScalar(1.1));
          }
        }
        for (let k = 0; k < 26; k++) {
          const u = -U * 0.75 + 6 + (U * 0.9 - 12) * hz(k, 100), dl = dLabio(u), d = dl + 10 + 28 * hz(k, 101), v = vc(u) + d * Math.sqrt(1 + vcp(u) * vcp(u));
          const h = campo(u, v).h, P = E(u, v, h);
          if (k % 3 === 2) {                              // banano: el tallo y sus hojas largas
            const al = 3 + 1.2 * hz(k, 102), T = [P[0], P[1] + al * M, P[2]];
            tubo(veg, [P[0], P[1] - 0.2 * M, P[2]], T, 0.16 * M, 7, cBanano.clone().multiplyScalar(0.8), null);
            for (let j = 0; j < 6; j++) { const an = TAU * j / 6 + hz(k, 103), L = 1.5;
              gema(veg, [T[0] + Math.cos(an) * L * 0.8 * M, T[1] - 0.25 * M, T[2] + Math.sin(an) * L * 0.8 * M], L * M, 0.1 * M, 0.32 * M, -an, cBanano.clone().multiplyScalar(0.9 + 0.2 * hz(k, 104 + j))); }
          } else {                                        // árbol de sombra: tronco delgado y copa ancha y plana en grumos
            const al = 8 + 5 * hz(k, 110), T = [P[0], P[1] + al * M, P[2]];
            tubo(veg, [P[0], P[1] - 0.3 * M, P[2]], T, 0.2 * M, 7, cTronco, null);
            for (let j = 0; j < 4; j++) { const an = TAU * (j / 4 + hz(k, 111)), rr = j ? 2.4 : 0;
              gema(veg, [T[0] + Math.cos(an) * rr * M, T[1] + (j ? -0.4 : 0.3) * M, T[2] + Math.sin(an) * rr * M], 3.4 * M, 1.1 * M, 3.0 * M, an,
                cCopa.clone().multiplyScalar(0.88 + 0.22 * hz(k, 112 + j))); }
          }
        }

        // ================= la sierra al fondo: tres filas redondeadas detrás del monte (sin conos)
        const sierra = nueva();
        [[360, 150, 0.9], [560, 230, 0.75], [820, 300, 0.6]].forEach(([vR, alto, kc], j) => {
          const filas = [], colores = [];
          for (const [dv, fh] of [[-110, 0], [-45, 0.55], [0, 1]]) {
            const f = [], c = [];
            for (let u = -1000; u <= 1000; u += 25) {
              const cima = alto * (0.55 + 0.3 * ruido(u, j * 97, 260, 120 + j) + 0.15 * ruido(u, j * 31, 90, 124 + j));
              const vv = vR + dv + 20 * (ruido(u, j, 150, 128) - 0.5), fl = piso(u, vv) - 2;
              f.push(E(u, vv, fl + (cima - fl) * fh)); c.push(cSierra[j].clone().multiplyScalar(kc * (0.92 + 0.12 * fh)));
            }
            filas.push(f); colores.push(c);
          }
          lamina(sierra, filas, colores);
        });

        // ================= las mallas fijas
        poner(sierra, {}, 1);
        poner(suelo, { desfase: 0 }, 2);
        poner(falda, { desfase: 0 }, 2);
        poner(banda, { desfase: 2 }, 2);
        poner(asf, { desfase: 3 }, 3);
        poner(rayas, { desfase: 5 }, 3);
        poner(solido, { desfase: 1 }, 3);
        poner(veg, {}, 3);

        // los captafaros del guardavía (de noche)
        let gP = null, matP = null;
        if (noche && captas.length) {
          gP = new THREE.BufferGeometry(); const pos = new Float32Array(captas.length * 3); captas.forEach((c, i) => pos.set(c, i * 3));
          gP.setAttribute("position", new THREE.BufferAttribute(pos, 3));
          matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: lin(COL.luces) } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "uniform float uPx, uTam; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(0.5 * uTam * uPx / max(1e-3, -mv.z), 1.5, 9.0); }",
            fragmentShader: "uniform vec3 cA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; vec3 c = cA; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); float a = 0.55 * exp(-r * r * 5.0); gl_FragColor = vec4(s * a, a); }" });
          const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);
        }

        // ================= los vehículos: cada uno una flota de uno dentro de un grupo que lo sube al camino y lo inclina
        const NV2 = clamp(p.vehiculos | 0, 0, 6);
        const lista = (p.camion === false ? [] : [{ tipo: "camionsacos", carril: 1, prot: true }]).concat(OTROS.slice(0, NV2).map((t, i) => ({ tipo: t, carril: i % 2 === 0 ? 2 : 1 })));
        const LC = LT + 40, VEL = { 1: 7.5, 2: 11 };
        const s0P = clamp(p.camion_s, 0, 1) * LT;
        const enCarril = lista.map((x) => x.carril);
        const n1 = enCarril.filter((c) => c === 1).length, n2 = enCarril.filter((c) => c === 2).length;
        let i1 = 0, i2 = 0;
        const veh = lista.map((x, i) => {
          const antes = new Set(scene.children);
          const fl = ctx.flota(x.tipo, 1, { tamano: K, orden: 5, luces: true, cabeceo: false, semilla: (p.semilla + i * 7) % 991,
            color: (j, vs) => (x.prot ? tonos.acento : vs[(i + p.semilla) % vs.length]) });
          const g = new THREE.Group(); g.matrixAutoUpdate = false; scene.add(g);
          for (const o of scene.children.filter((o) => !antes.has(o) && o !== g)) { scene.remove(o); g.add(o); }
          let s0;
          if (x.carril === 1) { s0 = x.prot ? s0P : s0P - LC * (++i1) / n1 + 6 * (hz(i, 130) - 0.5); }
          else { s0 = LC * (i2++) / Math.max(1, n2) + 0.4 * LC / Math.max(1, n2) * hz(i, 131); }
          return { fl, g, s0, carril: x.carril, v: VEL[x.carril] };
        });
        return { id: p.id, M, ux, uy, W2, E, base0, enS, hr, LT, LC, GR, veh, mats, matP };
      });
    },
    en(t, lista, ctx) {
      const { THREE, clamp } = ctx;
      const mA = new THREE.Matrix4(), mB = new THREE.Matrix4(), mR = new THREE.Matrix4(), ax = new THREE.Vector3();
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.4 * kb;
        if (s.matP) s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        for (const c of s.veh) {
          // dónde va (seek puro): s a lo largo del eje, de −20 a LT + 20 (fuera de la orilla, encogido)
          const q = ((((c.s0 + c.v * t) % s.LC) + s.LC) % s.LC) - 20, sv = c.carril === 1 ? q : s.LT - q;
          const k = clamp(Math.min(q + 4, s.LT + 4 - q) / 8, 0, 1);
          const d = c.carril === 1 ? -1.65 : 1.65, [u, v, th] = s.enS(sv, d), sg = c.carril === 1 ? 1 : -1;
          const du = Math.cos(th) * sg, dv = Math.sin(th) * sg;
          const dx = du * s.ux - dv * s.uy, dy = du * s.uy + dv * s.ux;
          const [x, y] = s.W2(u, v), a = ctx.altura(x, y), H = s.base0 + (s.hr(sv) + 0.06) * s.M;
          c.fl.poner(0, x, y, dx, dy, k, 0, c.v * s.M / ctx.metros(1));
          c.fl.listo();
          ax.set(dy, 0, dx).normalize();
          mA.makeTranslation(x, H, -y); mR.makeRotationAxis(ax, Math.atan(s.GR) * sg); mB.makeTranslation(-x, -a, y);
          c.g.matrix.copy(mA).multiply(mR).multiply(mB); c.g.matrixWorldNeedsUpdate = true;
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
