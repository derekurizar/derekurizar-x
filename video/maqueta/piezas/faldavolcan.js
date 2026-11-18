// Pieza «faldavolcan» (ficha: faldavolcan.json; reglas: scripts/maqueta_tipos/faldavolcan.py): la falda de un volcán
// genérico con un pueblo al pie, sin lugar real. Centrada en `lugar` (la plaza) y orientada por `rumbo` (u: hacia el
// volcán; v: a su izquierda). Todo en METROS × `tamano`.
// - EL VOLCÁN (la misma cuenta que faldavolcan.py → `alto`): cono cóncavo con la cumbre a 760 m del pueblo, 480 m de alto
//   (maqueta, no a escala), cráter poco hondo con su labio, costillas y nueve BARRANCOS radiales (el 0 es el cauce que
//   baja al pueblo). Una malla radial con la luz horneada por vértice; los tonos van por franja: roca y escoria arriba,
//   zacatal, BOSQUE (pinos arriba, latifoliadas abajo), y abajo las MILPAS en parcelas con sus surcos (verdes, secas o
//   aradas) y los árboles de los linderos. El fondo de los barrancos, más oscuro y húmedo.
// - EL PUEBLO al pie: la PLAZA de tierra con un árbol grande, la IGLESIA genérica (nave de adobe con contrafuertes,
//   fachada con espadaña, techo de paja o de teja), calles de tierra con `traza` (0 = caminos que serpentean; 1 = damero),
//   y `casas` de adobe o de bajareque con techo de paja (de teja, solo la parte `teja`), zócalo, puerta, ventana, algunas
//   con corredor; solares con cerca de caña, troje y árbol. Del cauce, al llano, un lecho de piedra hasta la plaza.
// - CON VIDA (seek puro): gente que camina por la plaza y la calle (persona), humo de fogón que sale por los techos de
//   paja, y de noche (ES.noche) las ventanas y la puerta de la iglesia encendidas, con su luz que tiembla (`ventanas`).
//   `lluvia` > 0: lluvia en rayas con viento, en una caja que va con la cámara (posición = función de t y de la cámara).
// La pieza PUBLICA su relieve, sus lugares (cumbre, ladera-alta, barranco, pueblo, plaza, iglesia) y el camino
// «<id>.cauce» (faldavolcan.py). Sin colores escritos (ctx.tonos, ctx.COL); sin texto ni marcas.
(function (MAQ) {
  const US = 760, HS = 480, RB = 640, RC = 0.075, PLAZA = 46, TAU = 2 * Math.PI;
  const IG_U = PLAZA / 2 + 6 + 13;
  const BARR = [[0.08, 30, 1.0], [-0.58, 20, 0.85], [0.66, 22, 0.9], [-1.18, 18, 0.8], [1.28, 19, 0.85],
    [-1.92, 16, 0.8], [2.02, 17, 0.8], [2.72, 15, 0.75], [-2.62, 16, 0.75]];
  const fase = (s) => ((s * 0.6180339887) % 1) * TAU;
  const ejeB = (k, x, ph) => BARR[k][0] + 0.045 * Math.sin(x * 9 + k * 1.7 + ph);
  const hondo = (k, x) => { const f = Math.min(1, Math.max(0, (x - 0.1) / 0.86)); return BARR[k][1] * Math.pow(Math.sin(Math.PI * f), 0.8); };
  const anchoB = (k, x) => (9 + 24 * x) * BARR[k][2];
  // → [h (m sobre el suelo del mundo), g (0–1: cuánto fondo de barranco), x (r / RB), th (0 = hacia el pueblo)]
  const alto = (u, v, ph) => {
    const du = u - US, r = Math.hypot(du, v), x = r / RB, th = Math.atan2(v, -du);
    if (x >= 1) return [0, 0, x, th];
    let h = HS * Math.pow(1 - x, 1.45);
    h *= 1 + 0.035 * Math.sin(7 * th + ph) * 4 * x * (1 - x);
    h += 5 * Math.exp(-Math.pow((x - RC) / 0.025, 2));
    if (x < RC) h -= 38 * (1 - (x / RC) * (x / RC));
    let g = 0;
    for (let k = 0; k < BARR.length; k++) {
      const d = hondo(k, x); if (d <= 0) continue;
      let dt = th - ejeB(k, x, ph) + Math.PI; dt = ((dt % TAU) + TAU) % TAU - Math.PI;
      const m = dt * r / anchoB(k, x);
      if (Math.abs(m) < 3.5) { const e = Math.exp(-m * m); h -= d * e; g = Math.max(g, e * Math.min(1, d / 8)); }
    }
    return [h, g, x, th];
  };
  // m305: la cuenta de la falda, publicada para los eventos que se posan sobre ella (alud): una sola copia en JS
  MAQ.FALDA = { alto, fase, US, HS, RB, RC };

  MAQ.PIEZAS.faldavolcan = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      const liso = (a, b, x) => { const v = clamp((x - a) / (b - a), 0, 1); return v * v * (3 - 2 * v); };
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      // ---- los tonos (todos del estilo)
      const cPasto = tonos.campo.clone(), cPasto2 = tonos.campo2.clone();
      const cBosque = tonos.verde.clone().lerp(tonos.campo2, 0.45).multiplyScalar(oscuro ? 0.95 : 0.8);
      const cTierra = lin(COL.tierra_media).lerp(tonos.arena, 0.35).multiplyScalar(oscuro ? 0.95 : 0.85);
      const cHumeda = cTierra.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.72);
      const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.45);
      const cCeniza = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.55).multiplyScalar(oscuro ? 1.05 : 0.78);
      const cZacate = cPasto.clone().lerp(lin(COL.tierra_alta), 0.4).multiplyScalar(oscuro ? 1.0 : 0.95);
      const cPino = tonos.verde.clone().lerp(tonos.campo2, 0.3).multiplyScalar(dia ? 0.6 : oscuro ? 1.0 : 0.75);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.5 : dia ? 0.85 : 0.95);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cMilpa = tonos.bien.clone().lerp(tonos.campo, 0.5).multiplyScalar(oscuro ? 0.75 : 0.72);
      const cSeca = lin(COL.tierra_alta).lerp(tonos.medio, 0.3).multiplyScalar(oscuro ? 0.85 : 0.88);
      const cArado = cTierra.clone().multiplyScalar(0.72);
      const cAdobe = tonos.muro.clone().lerp(lin(COL.tierra_media), 0.38).lerp(tonos.arena, 0.15);
      const cBajareque = cAdobe.clone().lerp(cTierra, 0.4).multiplyScalar(0.9);
      const cZocalo = cRoca.clone().multiplyScalar(0.78);
      const cPaja = lin(COL.tierra_alta).lerp(tonos.medio, 0.3).multiplyScalar(oscuro ? 0.92 : 0.86);
      const cTeja = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.5).multiplyScalar(oscuro ? 0.9 : 0.85);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.22);
      const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
      const cCana = lin(COL.tierra_alta).lerp(tonos.arena, 0.4).multiplyScalar(oscuro ? 0.9 : 0.8);
      const cCalle = tonos.calle.clone().lerp(cTierra, 0.45);
      const cPlaza = tonos.calle.clone().lerp(cTierra, 0.55).multiplyScalar(oscuro ? 1.0 : 0.86);
      const cSolar = tonos.calle.clone().lerp(cTierra, 0.65).multiplyScalar(0.95);
      const cLecho = cHumeda.clone().lerp(cRoca, 0.3).multiplyScalar(oscuro ? 1.1 : 0.95);
      const cLuz = lin(COL.luces), cHumo = tonos.muro.clone().lerp(lin(COL.costa), 0.5), cLluvia = lin(COL.costa);

      // ---- caras con la luz horneada (4 puntos; ref = hacia dónde es «afuera»; sin ref, hacia arriba)
      const cara = (acc, P, col, ref) => {
        const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
        let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
        const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
        if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx, ny, nz), q = acc.pos.length / 3;
        for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
        acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
      };
      const tubo = (acc, A, B, r, seg, col) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2));
        }
      };
      const cono = (acc, P, r, h, seg, col) => {          // solo el costado (la base no se ve)
        const T = [P[0], P[1] + h, P[2]];
        for (let i = 0; i < seg; i++) {
          const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
          cara(acc, [[P[0] + r * Math.cos(a0), P[1], P[2] + r * Math.sin(a0)], [P[0] + r * Math.cos(a1), P[1], P[2] + r * Math.sin(a1)], T, T],
            col, [Math.cos(am), r / h, Math.sin(am)]);
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
      const sRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K, ph = fase(p.semilla), TZ = clamp(p.traza, 0, 1);
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const moja = 1 - 0.12 * clamp(p.lluvia, 0, 1);
        const W2 = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W2(u, v); return [x, ctx.suelo(x, y) + h * M, -y]; };
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const polar = (x, th) => [US - x * RB * Math.cos(th), x * RB * Math.sin(th)];
        const mats = [];
        const poner = (acc, op, orden) => { const mat = malla.material(op || {}); mats.push(mat); malla.poner(acc, mat, orden); return mat; };
        const nueva = () => malla.nueva();

        // ================= las milpas: parcelas por franjas de la falda baja (x) y por tramos de arco
        const BANDAS = [0.66, 0.715, 0.77, 0.825, 0.88, 0.935, 0.975], ARCO = 44;
        const parcelas = [];
        for (let b = 0; b + 1 < BANDAS.length; b++) {
          const xm = (BANDAS[b] + BANDAS[b + 1]) / 2, dth = ARCO / (xm * RB), n = Math.floor(1.75 / dth);
          for (let q = -n; q < n; q++) {
            const k = b * 97 + q + 400, t0 = q * dth, t1 = t0 + dth, [, g] = alto(...polar(xm, t0 + dth / 2), ph);
            if (hz(k, 1) < 0.22 || g > 0.12) continue;
            const ins = 2.5 + 2.5 * hz(k, 2), kind = hz(k, 3);
            parcelas.push({ x0: BANDAS[b] + ins / RB, x1: BANDAS[b + 1] - ins / RB, t0: t0 + ins / (xm * RB), t1: t1 - ins / (xm * RB),
              tipo: kind < 0.55 ? 0 : kind < 0.82 ? 1 : 2, k });
          }
        }
        const enMilpa = (x, th) => parcelas.some((m) => x > m.x0 - 0.004 && x < m.x1 + 0.004 && th > m.t0 - 0.004 && th < m.t1 + 0.004);

        // ================= el volcán: malla radial (anillos × sectores) con la luz y el tono horneados
        const NR = 66, NS = 240, Pv = [], Cv = [];
        for (let i = 0; i <= NR; i++) {
          const x = 0.004 + (1 - 0.004) * i / NR, fila = [], filc = [];
          for (let j = 0; j <= NS; j++) {
            const th = -Math.PI + TAU * (j % NS) / NS, [u, v] = polar(x, th), [h, g] = alto(u, v, ph);
            fila.push(E(u, v, h - 0.6));
            const n1 = ruido(u, v, 70, 11), n2 = ruido(u, v, 14, 12);
            let c;
            if (x < 0.13) c = cCeniza.clone().lerp(cRoca, 0.35 * n2);
            else if (x < 0.3) c = cZacate.clone().lerp(cCeniza, 1 - liso(0.12, 0.24, x)).lerp(cRoca, 0.25 * n2 * (1 - liso(0.2, 0.3, x)));
            else if (x < 0.66) c = cBosque.clone().lerp(cZacate, 1 - liso(0.28, 0.36, x)).lerp(cPasto2, 0.3 * n1).lerp(cPasto, liso(0.6, 0.68, x));
            else c = cPasto.clone().lerp(cPasto2, 0.45 * n1).lerp(cTierra, 0.12 * n2);
            if (g > 0) c.lerp(cHumeda, 0.6 * g);
            c.multiplyScalar((0.92 + 0.12 * n2) * (x < 0.66 ? moja : 1));
            filc.push(c);
          }
          Pv.push(fila); Cv.push(filc);
        }
        const tierra = nueva(); lamina(tierra, Pv, Cv);

        // los surcos de las milpas: franjas a lo largo del contorno, sobre el terreno
        const milpa = nueva();
        for (const m of parcelas) {
          const col = [cMilpa, cSeca, cArado][m.tipo].clone().multiplyScalar(0.9 + 0.15 * hz(m.k, 4));
          const fondo = (m.tipo === 2 ? cArado.clone().multiplyScalar(0.85) : cTierra.clone().multiplyScalar(0.8)).multiplyScalar(moja);
          const NA = 4, prof = (m.x1 - m.x0) * RB, nS = Math.max(4, Math.round(prof / 2.1));
          // el suelo de la parcela y encima los surcos (más angostos: se ve la tierra entre ellos)
          for (const [w, cc, lev] of [[1, fondo, 0.22], [0.48, col, 0.42]]) {
            for (let s = 0; s < nS; s++) {
              const xa = m.x0 + (m.x1 - m.x0) * s / nS, xb = xa + (m.x1 - m.x0) / nS * w;
              const fila = [], filc = [];
              for (const xx of [xa, xb]) {
                const f = [], fc = [];
                for (let a = 0; a <= NA; a++) { const th = m.t0 + (m.t1 - m.t0) * a / NA, [u, v] = polar(xx, th); f.push(E(u, v, alto(u, v, ph)[0] - 0.6 + lev)); fc.push(cc); }
                fila.push(f); filc.push(fc);
              }
              lamina(milpa, fila, filc);
            }
          }
        }

        // ================= los árboles: bosque en la falda media, linderos abajo; rocas y escoria arriba
        const veg = nueva(), solido = nueva();
        const pino = (P, alto_, k) => {
          tubo(veg, [P[0], P[1] - 0.4 * M, P[2]], [P[0], P[1] + alto_ * 0.35 * M, P[2]], 0.035 * alto_ * M, 4, cTronco);
          for (let j = 0; j < 2; j++) cono(veg, [P[0], P[1] + alto_ * (0.25 + 0.3 * j) * M, P[2]], alto_ * (0.3 - 0.09 * j) * M, alto_ * (0.5 - 0.08 * j) * M, 6,
            cPino.clone().multiplyScalar(0.88 + 0.2 * hz(k, 20 + j)));
        };
        const frondoso = (P, alto_, k) => {
          tubo(veg, [P[0], P[1] - 0.4 * M, P[2]], [P[0], P[1] + alto_ * 0.6 * M, P[2]], 0.04 * alto_ * M, 4, cTronco);
          for (let j = 0; j < 2; j++) { const a = TAU * hz(k, 30 + j), rr = j ? alto_ * 0.18 : 0;
            gema(veg, [P[0] + Math.cos(a) * rr * M, P[1] + alto_ * (0.72 - 0.08 * j) * M, P[2] + Math.sin(a) * rr * M], alto_ * 0.32 * M, alto_ * 0.24 * M, alto_ * 0.3 * M, a,
              cCopa.clone().multiplyScalar(0.85 + 0.25 * hz(k, 32 + j))); }
        };
        let nArb = 0;
        for (let k = 0; k < 4200 && nArb < 640; k++) {
          const x = Math.sqrt(0.28 * 0.28 + (0.99 * 0.99 - 0.28 * 0.28) * hz(k, 40)), th = -Math.PI + TAU * hz(k, 41), [u, v] = polar(x, th);
          const atras = Math.abs(th) > 1.9 ? 0.45 : 1, n = ruido(u, v, 60, 42);
          const ok = x < 0.66 ? n > 0.33 && hz(k, 43) < 0.75 * atras : n > 0.6 && hz(k, 43) < 0.55 * atras && !enMilpa(x, th);
          if (!ok) continue;
          const [h] = alto(u, v, ph), P = E(u, v, h - 0.6), al = 12 + 10 * hz(k, 44);
          if (x < 0.46 || (x < 0.6 && hz(k, 45) < 0.35)) pino(P, al, k); else frondoso(P, al * 0.9, k);
          nArb++;
        }
        for (let k = 0; k < 60; k++) {
          const x = 0.08 + 0.14 * hz(k, 50), th = -Math.PI + TAU * hz(k, 51), [u, v] = polar(x, th), [h] = alto(u, v, ph), rr = 2 + 4 * hz(k, 52);
          gema(solido, E(u, v, h - 0.6 + rr * 0.15), rr * 1.3 * M, rr * 0.7 * M, rr * M, TAU * hz(k, 53), cRoca.clone().multiplyScalar(0.75 + 0.35 * hz(k, 54)));
        }

        // ================= el pueblo: calles, plaza, iglesia, casas, solares
        const suelos = nueva(), muros = nueva(), techos = nueva(), huecos = nueva(), focos = nueva();
        const brillos = [], humos = [];
        // el marco de un edificio: s a lo largo de `ang` (radianes en el plano local), t a su izquierda
        const marco = (cu, cv, ang) => {
          const a = ang + r, ax = Math.cos(a), ay = Math.sin(a), [cx, cy] = W2(cu, cv), y0 = ctx.suelo(cx, cy);
          const F = (s, t, y) => [cx + (ax * s - ay * t) * M, y0 + y * M, -(cy + (ay * s + ax * t) * M)];
          return { F, S: [ax, 0, -ay], T: [-ay, 0, -ax] };
        };
        const neg = (d) => [-d[0], -d[1], -d[2]], UP = [0, 1, 0];
        const caja = (acc, B, s0, s1, t0, t1, y0, y1, col, sinTapa) => {
          const F = B.F;
          if (!sinTapa) cara(acc, [F(s0, t0, y1), F(s1, t0, y1), F(s1, t1, y1), F(s0, t1, y1)], col, UP);
          cara(acc, [F(s1, t0, y0), F(s1, t1, y0), F(s1, t1, y1), F(s1, t0, y1)], col, B.S);
          cara(acc, [F(s0, t0, y0), F(s0, t1, y0), F(s0, t1, y1), F(s0, t0, y1)], col, neg(B.S));
          cara(acc, [F(s0, t1, y0), F(s1, t1, y0), F(s1, t1, y1), F(s0, t1, y1)], col, B.T);
          cara(acc, [F(s0, t0, y0), F(s1, t0, y0), F(s1, t0, y1), F(s0, t0, y1)], col, neg(B.T));
        };
        // un vano (puerta, ventana) sobre la cara t = tf (lado = +1: la del frente)
        const vano = (B, tf, lado, s0, s1, y0, y1, prendido) => {
          const F = B.F, t = tf + lado * 0.04, ref = lado > 0 ? B.T : neg(B.T);
          cara(prendido ? focos : huecos, [F(s0, t, y0), F(s1, t, y0), F(s1, t, y1), F(s0, t, y1)], prendido ? cLuz : cHueco, ref);
          if (prendido) brillos.push(F((s0 + s1) / 2, tf + lado * 0.5, (y0 + y1) / 2));
        };
        // un techo a dos aguas con la cumbrera a lo largo de s, sobre muros de ancho 2·w y alto hw
        const techo = (B, l, w, hw, paja, ovF, col, colMuro) => {
          const F = B.F, p_ = paja ? 0.74 : 0.43, tp = Math.tan(p_), th = paja ? 0.42 : 0.16, ovs = paja ? 0.65 : 0.45, Ls = l + ovs;
          const rise = w * tp, yR = hw + rise, dth = th / Math.cos(p_);
          for (const sg of [1, -1]) {
            const ov = sg > 0 ? ovF : (paja ? 0.8 : 0.5), te = sg * (w + ov), ye = hw - ov * tp;
            const cTop = col.clone().multiplyScalar(0.95 + 0.08 * (sg > 0 ? 1 : 0)), cBajo = col.clone().multiplyScalar(0.5);
            // la vertiente en dos tiras: abajo, más curtida (el alero)
            const tm = te * 0.72, ym = ye + (yR - ye) * 0.28;
            cara(techos, [F(-Ls, te, ye + dth), F(Ls, te, ye + dth), F(Ls, tm, ym + dth), F(-Ls, tm, ym + dth)], cTop.clone().multiplyScalar(paja ? 0.86 : 0.92), null);
            cara(techos, [F(-Ls, tm, ym + dth), F(Ls, tm, ym + dth), F(Ls, 0, yR + dth), F(-Ls, 0, yR + dth)], cTop, null);
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, 0, yR), F(-Ls, 0, yR)], cBajo, [0, -1, 0]);
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, te, ye + dth), F(-Ls, te, ye + dth)], col.clone().multiplyScalar(0.7), sg > 0 ? B.T : neg(B.T));
            for (const ss of [Ls, -Ls]) cara(techos, [F(ss, te, ye), F(ss, 0, yR), F(ss, 0, yR + dth), F(ss, te, ye + dth)], col.clone().multiplyScalar(0.62), ss > 0 ? B.S : neg(B.S));
          }
          for (const ss of [l, -l]) cara(muros, [F(ss, -w, hw), F(ss, w, hw), F(ss, 0, yR), F(ss, 0, yR)], colMuro, ss > 0 ? B.S : neg(B.S));
          if (paja) tubo(techos, F(-Ls, 0, yR + dth * 0.8), F(Ls, 0, yR + dth * 0.8), 0.24 * M, 6, col.clone().multiplyScalar(0.8));
          else tubo(techos, F(-Ls, 0, yR + dth), F(Ls, 0, yR + dth), 0.13 * M, 6, col.clone().multiplyScalar(0.75));
          return yR + dth;
        };
        const cerca = (B, pts, hf, k) => {
          const F = B.F;
          for (let i = 0; i + 1 < pts.length; i++) {
            const [s0, t0] = pts[i], [s1, t1] = pts[i + 1], L = Math.hypot(s1 - s0, t1 - t0), n = Math.max(1, Math.round(L / 0.42));
            const nrm = [(t1 - t0) / L, -(s1 - s0) / L], ref = [B.S[0] * nrm[0] + B.T[0] * nrm[1], 0, B.S[2] * nrm[0] + B.T[2] * nrm[1]];
            for (let j = 0; j < n; j++) {
              const a = j / n, b = (j + 1) / n, sa = s0 + (s1 - s0) * a, ta = t0 + (t1 - t0) * a, sb = s0 + (s1 - s0) * b, tb = t0 + (t1 - t0) * b;
              const hh = hf * (0.86 + 0.24 * hz(k * 131 + i * 17 + j, 60));
              cara(solido, [F(sa, ta, -0.1), F(sb, tb, -0.1), F(sb, tb, hh), F(sa, ta, hh)], cCana.clone().multiplyScalar(j % 2 ? 0.78 : 0.96), ref);
            }
            cara(solido, [F(s0, t0, hf * 0.55), F(s1, t1, hf * 0.55), F(s1, t1, hf * 0.62), F(s0, t0, hf * 0.62)], cMadera, ref);
          }
        };
        // un parche de suelo (polígono local) posado sobre el suelo del mundo
        const parche = (pts, col, lev) => malla.poligono(suelos, pts.flatMap(([u, v]) => W2(u, v)), lev * M, col);
        // una franja de suelo a lo largo de una polilínea local (calles, el lecho del cauce)
        const franja = (acc, pts, w, col, lev, k) => {
          const P = [], C = [];
          for (let i = 0; i < pts.length; i++) {
            const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
            const nu = -(b[1] - a[1]) / L, nv = (b[0] - a[0]) / L, f = [], fc = [];
            for (const d of [-1, -0.5, 0, 0.5, 1]) {
              const ww = w * (1 + 0.15 * (hz(k * 53 + i, 70) - 0.5)), [x, y] = W2(pts[i][0] + nu * d * ww, pts[i][1] + nv * d * ww);
              f.push([x, ctx.suelo(x, y) + lev * M, -y]); fc.push(col.clone().multiplyScalar((0.9 + 0.14 * ruido(pts[i][0], d * 3, 9, 71)) * (Math.abs(d) === 1 ? 0.93 : 1)));
            }
            P.push(f); C.push(fc);
          }
          lamina(acc, P, C);
        };
        const dSeg = (pu, pv, a, b) => { const du = b[0] - a[0], dv = b[1] - a[1], h = clamp(((pu - a[0]) * du + (pv - a[1]) * dv) / ((du * du + dv * dv) || 1), 0, 1);
          return Math.hypot(pu - a[0] - du * h, pv - a[1] - dv * h); };
        const dPol = (pu, pv, pts) => { let m = Infinity; for (let i = 0; i + 1 < pts.length; i++) m = Math.min(m, dSeg(pu, pv, pts[i], pts[i + 1])); return m; };

        // ---- las calles (traza: 0 = caminos que serpentean, 1 = damero)
        const BASE = [[[-PLAZA / 2, 0], [-178, 0], 6], [[0, PLAZA / 2], [0, 152], 5], [[0, -PLAZA / 2], [0, -152], 5],
          [[-86, -138], [-86, 138], 4.5], [[-162, 80], [24, 80], 4.5], [[-162, -80], [24, -80], 4.5], [[PLAZA / 2, -PLAZA / 2 + 4], [116, -74], 3.5]];
        const calles = BASE.map(([a, b, w], ic) => {
          const L = Math.hypot(b[0] - a[0], b[1] - a[1]), du = (b[0] - a[0]) / L, dv = (b[1] - a[1]) / L, n = Math.ceil(L / 4), pts = [];
          const desde = Math.abs(a[0]) <= PLAZA / 2 + 0.1 && Math.abs(a[1]) <= PLAZA / 2 + 0.1;
          for (let i = 0; i <= n; i++) {
            const s = L * i / n, env = desde ? liso(0, 22, s) : liso(0, 10, s) * liso(0, 10, L - s);
            const o = (1 - TZ) * env * (6 * Math.sin(s / 31 + ic * 2.1 + ph) + 2.4 * Math.sin(s / 11 + ic * 1.3));
            pts.push([a[0] + du * s - dv * o, a[1] + dv * s + du * o]);
          }
          return { pts, w, du, dv };
        });
        for (const [i, c] of calles.entries()) franja(suelos, c.pts, c.w / 2, cCalle.clone().multiplyScalar(moja * moja), 0.05, i);
        // la plaza (con su atrio frente a la iglesia)
        parche([[-PLAZA / 2, -PLAZA / 2], [PLAZA / 2, -PLAZA / 2], [PLAZA / 2, PLAZA / 2], [-PLAZA / 2, PLAZA / 2]], cPlaza.clone().multiplyScalar(moja), 0.07);
        parche([[PLAZA / 2, -9], [PLAZA / 2 + 6.4, -9], [PLAZA / 2 + 6.4, 9], [PLAZA / 2, 9]], cPlaza.clone().multiplyScalar(0.93 * moja), 0.075);
        // el lecho del cauce al llano (piedra y arena), del pie hasta la plaza
        const thPie = ejeB(0, 1, ph), pie = polar(1, thPie), fin = [PLAZA * 0.5 + 2, PLAZA * 0.3];
        const lecho = [];
        for (let i = 0; i <= 14; i++) { const f = i / 14; lecho.push([pie[0] + (fin[0] - pie[0]) * f, pie[1] + (fin[1] - pie[1]) * f + 4 * Math.sin(Math.PI * f)]); }
        franja(suelos, lecho, 3.2, cLecho.clone().multiplyScalar(moja), 0.06, 99);
        for (let k = 0; k < 40; k++) {
          const i = Math.floor(hz(k, 80) * lecho.length), [u, v] = lecho[i], rr = 0.3 + 0.6 * hz(k, 81);
          gema(solido, E(u + 5 * (hz(k, 82) - 0.5), v + 5 * (hz(k, 83) - 0.5), 0.05), rr * M, rr * 0.5 * M, rr * 0.8 * M, TAU * hz(k, 84), cRoca.clone().multiplyScalar(0.8 + 0.3 * hz(k, 85)));
        }

        // ---- la iglesia (genérica): nave de adobe con contrafuertes, fachada con espadaña hacia la plaza
        {
          const B = marco(IG_U, 0, 0), F = B.F, L = 13, Wn = 5, Hn = 7.2, tejaI = p.teja >= 0.5;
          caja(muros, B, -L - 0.2, L + 0.2, -Wn - 0.2, Wn + 0.2, -0.4, 0.6, cZocalo);
          caja(muros, B, -L, L, -Wn, Wn, 0.6, Hn, cAdobe, true);
          for (const sc of [-8.5, -2.8, 2.8, 8.5]) for (const sg of [1, -1]) {
            caja(muros, B, sc - 0.65, sc + 0.65, sg > 0 ? Wn : -Wn - 1.0, sg > 0 ? Wn + 1.0 : -Wn, -0.3, 5.6, cAdobe.clone().multiplyScalar(0.93));
            cara(muros, [F(sc - 0.65, sg * (Wn + 1.0), 5.6), F(sc + 0.65, sg * (Wn + 1.0), 5.6), F(sc + 0.65, sg * Wn, 6.6), F(sc - 0.65, sg * Wn, 6.6)], cAdobe.clone().multiplyScalar(0.85), null);
          }
          const yR = techo(B, L, Wn, Hn, !tejaI, tejaI ? 0.5 : 0.8, tejaI ? cTeja : cPaja, cAdobe);
          // la fachada: hastial que sobresale del techo y la espadaña con dos vanos
          caja(muros, B, -L - 0.9, -L + 0.1, -Wn - 0.7, Wn + 0.7, -0.3, Hn, cAdobe.clone().multiplyScalar(1.04));
          caja(muros, B, -L - 0.9, -L + 0.1, -Wn + 0.6, Wn - 0.6, Hn, yR - 0.4, cAdobe.clone().multiplyScalar(1.04));
          caja(muros, B, -L - 0.85, -L + 0.05, -2.3, 2.3, yR - 0.4, yR + 3.6, cAdobe.clone().multiplyScalar(1.07));
          caja(muros, B, -L - 1.0, -L + 0.2, -2.5, 2.5, yR + 3.6, yR + 3.9, cZocalo);
          for (const tc of [-1.05, 1.05]) for (const sF of [-L - 0.9, -L + 0.1]) {
            const t0 = tc - 0.45, t1 = tc + 0.45, sx = sF + (sF < -L ? -0.04 : 0.04), ref = sF < -L ? neg(B.S) : B.S;
            cara(huecos, [F(sx, t0, yR + 0.9), F(sx, t1, yR + 0.9), F(sx, t1, yR + 2.8), F(sx, t0, yR + 2.8)], cHueco, ref);
          }
          caja(solido, B, -L - 0.5, -L - 0.3, -0.09, 0.09, yR + 3.9, yR + 5.6, cMadera);
          caja(solido, B, -L - 0.5, -L - 0.3, -0.55, 0.55, yR + 4.8, yR + 5.0, cMadera);
          // la puerta y el óculo (de noche, encendidos), y las ventanas altas de la nave
          const pr = noche && p.ventanas;
          const sP = -L - 0.94, refP = neg(B.S);
          cara(pr ? focos : huecos, [F(sP, -1.3, 0.6), F(sP, 1.3, 0.6), F(sP, 1.3, 4.3), F(sP, -1.3, 4.3)], pr ? cLuz.clone().multiplyScalar(0.8) : cHueco, refP);
          cara(pr ? focos : huecos, [F(sP, -0.5, 5.2), F(sP, 0.5, 5.2), F(sP, 0.5, 6.1), F(sP, -0.5, 6.1)], pr ? cLuz.clone().multiplyScalar(0.7) : cHueco, refP);
          if (pr) { brillos.push(F(-L - 1.6, 0, 2.4)); brillos.push(F(-L - 1.4, 0, 5.6)); }
          for (const sc of [-5.6, 0, 5.6]) for (const sg of [1, -1]) vano(B, sg * Wn, sg, sc - 0.4, sc + 0.4, 4.6, 5.7, pr && hz(Math.round(sc) + sg, 90) < 0.7);
        }

        // ---- el árbol grande de la plaza
        { const [x, y] = W2(-PLAZA / 2 + 6, PLAZA / 2 - 6), P = [x, ctx.suelo(x, y), -y], al = 13;
          tubo(veg, [P[0], P[1] - 0.3 * M, P[2]], [P[0], P[1] + al * 0.55 * M, P[2]], 0.55 * M, 8, cTronco);
          for (let j = 0; j < 5; j++) { const a = TAU * j / 5 + 0.4, rr = j ? 3.6 : 0;
            gema(veg, [P[0] + Math.cos(a) * rr * M, P[1] + (al * 0.72 + (j ? -0.6 : 0.8)) * M, P[2] + Math.sin(a) * rr * M], 4.6 * M, 2.4 * M, 4.2 * M, a, cCopa.clone().multiplyScalar(0.88 + 0.2 * hz(j, 95))); } }

        // ---- las casas: candidatas a lo largo de las calles (y sueltas, si la traza es floja); se aceptan sin encimarse
        const cand = [];
        calles.forEach((c, ic) => {
          for (let i = 1; i < c.pts.length - 1; i++) {
            if (hz(ic * 1000 + i, 100) > 0.42 + 0.18 * TZ) continue;
            const [a, b] = [c.pts[i - 1], c.pts[i + 1]], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, du = (b[0] - a[0]) / L, dv = (b[1] - a[1]) / L;
            for (const lado of [1, -1]) {
              const k = ic * 1000 + i * 2 + (lado > 0 ? 0 : 1);
              if (hz(k, 101) < 0.35) continue;
              const ret = c.w / 2 + 3.2 + (1 - TZ) * 7 * hz(k, 102), cu = c.pts[i][0] - dv * lado * ret, cv = c.pts[i][1] + du * lado * ret;
              cand.push({ cu, cv, ang: Math.atan2(dv, du) + (lado > 0 ? Math.PI : 0) + (1 - TZ) * 0.5 * (hz(k, 103) - 0.5), k,
                d: Math.hypot(cu, cv) + 70 * hz(k, 104) });
            }
          }
        });
        for (let k = 0; k < Math.round(40 * (1 - TZ)); k++) {
          const rr = 60 + 115 * Math.sqrt(hz(k, 105)), a = TAU * hz(k, 106), cu = rr * Math.cos(a) - 20, cv = rr * Math.sin(a);
          cand.push({ cu, cv, ang: TAU * hz(k, 107), k: 9000 + k, d: rr + 90 * hz(k, 108) });
        }
        cand.sort((a, b) => a.d - b.d);
        const puestas = [];
        const N_CASAS = clamp(p.casas | 0, 0, 80);
        for (const c of cand) {
          if (puestas.length >= N_CASAS) break;
          const k = c.k, bajareque = hz(k, 110) < 0.45, L = bajareque ? 2.6 + 1.2 * hz(k, 111) : 3.0 + 2.0 * hz(k, 111), Wd = 2.2 + 0.8 * hz(k, 112);
          const D = 6 + 7 * hz(k, 113), solar = hz(k, 114) < 0.62;
          // el centro de lo que ocupa (casa + solar detrás) y su radio
          const ca = Math.cos(c.ang), sa = Math.sin(c.ang), tc = solar ? -(Wd + D) / 2 : 0;
          const ou = c.cu - sa * tc, ov = c.cv + ca * tc, rad = Math.hypot(L + 1.2, solar ? (Wd * 2 + D) / 2 : Wd) + 1.5;
          if (Math.abs(ou) < PLAZA / 2 + rad && Math.abs(ov) < PLAZA / 2 + rad) continue;
          if (ou > PLAZA / 2 - rad && ou < IG_U + 16 + rad && Math.abs(ov) < 9 + rad) continue;
          if (ou + rad > 108 || Math.hypot(ou, ov) > 210) continue;
          if (dPol(c.cu, c.cv, lecho) < 5 + Math.max(L, Wd)) continue;
          if (calles.some((q) => dPol(c.cu, c.cv, q.pts) < q.w / 2 + Wd + 0.6)) continue;
          if (puestas.some((q) => Math.hypot(q.ou - ou, q.ov - ov) < q.rad + rad)) continue;
          puestas.push({ ...c, ou, ov, rad, L, Wd, D, solar, bajareque });
        }
        for (const c of puestas) {
          const k = c.k, B = marco(c.cu, c.cv, c.ang), F = B.F, L = c.L, Wd = c.Wd;
          const Hw = (c.bajareque ? 2.4 : 2.7) + 0.4 * hz(k, 120), paja = hz(k, 121) >= p.teja, corredor = !c.bajareque && hz(k, 122) < 0.4;
          const cm = (c.bajareque ? cBajareque : cAdobe).clone().multiplyScalar(0.9 + 0.16 * hz(k, 123));
          if (c.solar) parche([[-L - 1.2, Wd + 1.2], [L + 1.2, Wd + 1.2], [L + 1.2, -Wd - c.D], [-L - 1.2, -Wd - c.D]].map(([s, t]) => {
            const a = c.ang, ax = Math.cos(a), ay = Math.sin(a); return [c.cu + ax * s - ay * t, c.cv + ay * s + ax * t]; }), cSolar.clone().multiplyScalar(moja), 0.035);
          caja(muros, B, -L - 0.12, L + 0.12, -Wd - 0.12, Wd + 0.12, -0.3, 0.4, cZocalo);
          caja(muros, B, -L, L, -Wd, Wd, 0.4, Hw, cm, true);
          if (c.bajareque) for (const yy of [1.2, 2.0]) for (const sg of [1, -1])          // las tiras de los horcones y varas
            cara(muros, [F(-L, sg * (Wd + 0.02), yy), F(L, sg * (Wd + 0.02), yy), F(L, sg * (Wd + 0.02), yy + 0.1), F(-L, sg * (Wd + 0.02), yy + 0.1)], cMadera, sg > 0 ? B.T : neg(B.T));
          const yR = techo(B, L, Wd, Hw, paja, corredor ? 0.25 : (paja ? 0.8 : 0.5), (paja ? cPaja : cTeja).clone().multiplyScalar(0.92 + 0.14 * hz(k, 124)), cm);
          // puerta y ventana en el frente (t = +Wd); otra ventana atrás
          const sD = (hz(k, 125) - 0.5) * (L - 1.0), luzOn = noche && p.ventanas && hz(k, 126) < 0.7;
          vano(B, Wd, 1, sD - 0.48, sD + 0.48, 0.4, 2.0, false);
          const sV = sD > 0 ? sD - 1.6 : sD + 1.6;
          if (Math.abs(sV) < L - 0.5) vano(B, Wd, 1, sV - 0.35, sV + 0.35, 1.2, 1.75, luzOn);
          if (luzOn && hz(k, 127) < 0.5) { cara(focos, [F(sD - 0.48, Wd + 0.05, 0.4), F(sD + 0.48, Wd + 0.05, 0.4), F(sD + 0.48, Wd + 0.05, 2.0), F(sD - 0.48, Wd + 0.05, 2.0)], cLuz.clone().multiplyScalar(0.55), B.T); brillos.push(F(sD, Wd + 0.7, 1.1)); }
          vano(B, -Wd, -1, -0.3, 0.3, 1.25, 1.7, false);
          if (corredor) {                                                              // corredor de horcones con su alero
            const tE = Wd + 2.0, yE = 2.15, dth = 0.3;
            cara(techos, [F(-L - 0.3, Wd, Hw - 0.05 + dth), F(L + 0.3, Wd, Hw - 0.05 + dth), F(L + 0.3, tE, yE + dth), F(-L - 0.3, tE, yE + dth)], (paja ? cPaja : cTeja).clone().multiplyScalar(0.9), null);
            cara(techos, [F(-L - 0.3, Wd, Hw - 0.05), F(L + 0.3, Wd, Hw - 0.05), F(L + 0.3, tE, yE), F(-L - 0.3, tE, yE)], (paja ? cPaja : cTeja).clone().multiplyScalar(0.45), [0, -1, 0]);
            cara(techos, [F(-L - 0.3, tE, yE), F(L + 0.3, tE, yE), F(L + 0.3, tE, yE + dth), F(-L - 0.3, tE, yE + dth)], (paja ? cPaja : cTeja).clone().multiplyScalar(0.7), B.T);
            for (const ss of [-L + 0.2, 0, L - 0.2]) tubo(solido, F(ss, tE - 0.2, -0.1), F(ss, tE - 0.2, yE + 0.05), 0.09 * M, 6, cMadera);
            parche([[-L - 0.3, Wd], [L + 0.3, Wd], [L + 0.3, tE], [-L - 0.3, tE]].map(([s, t]) => {
              const ax = Math.cos(c.ang), ay = Math.sin(c.ang); return [c.cu + ax * s - ay * t, c.cv + ay * s + ax * t]; }), cZocalo.clone().multiplyScalar(1.1), 0.12);
          }
          if (c.solar) {
            const t0 = -Wd - 0.2, t1 = -Wd - c.D, s0 = -L - 1.0, s1 = L + 1.0;
            if (hz(k, 130) < 0.8) cerca(B, [[s0, t0], [s0, t1], [s1, t1], [s1, t0]], 1.2 + 0.5 * hz(k, 131), k);
            if (hz(k, 132) < 0.35) {                                                   // troje: redonda, con su techo de paja
              const P = F(s0 + 1.6, t1 + 1.6, 0.3), rr = 0.9 * M;
              tubo(muros, P, F(s0 + 1.6, t1 + 1.6, 2.0), rr, 12, cCana.clone().multiplyScalar(0.9));
              cono(techos, F(s0 + 1.6, t1 + 1.6, 1.9), rr * 1.45, 1.5 * M, 12, cPaja.clone().multiplyScalar(0.92));
              for (const [a, b] of [[0.6, 0.6], [-0.6, 0.6], [0.6, -0.6], [-0.6, -0.6]]) tubo(solido, F(s0 + 1.6 + a, t1 + 1.6 + b, -0.1), F(s0 + 1.6 + a, t1 + 1.6 + b, 0.35), 0.07 * M, 4, cMadera);
            }
            if (hz(k, 133) < 0.45) frondoso(F(s1 - 1.5, t1 + 2 + 2 * hz(k, 134), 0), 6 + 3 * hz(k, 135), k + 7000);
          }
          if (paja && hz(k, 136) < 0.45) humos.push({ P: F((hz(k, 137) - 0.5) * L, 0, yR + 0.2), f: hz(k, 138) });
        }

        // ================= las mallas fijas
        poner(tierra, { desfase: 0 }, 2);
        poner(milpa, { desfase: 2 }, 2);
        poner(suelos, { desfase: 3 }, 2);
        poner(muros, {}, 3);
        poner(techos, {}, 3);
        poner(solido, { desfase: 1 }, 3);
        poner(veg, {}, 3);
        poner(huecos, { desfase: 2 }, 3);
        const matFoc = malla.material({ desfase: 3 }); malla.poner(focos, matFoc, 4); matFoc.uniforms.uBrillo.value = noche ? 1.7 : 1;

        // ================= lo que se mueve: brillos de las ventanas, humo y lluvia (shaders con uT)
        const uPx = { value: 1 }, uT = { value: 0 };
        let matB = null;
        if (brillos.length) {
          const g = new THREE.BufferGeometry(), pos = new Float32Array(brillos.length * 3), fa = new Float32Array(brillos.length);
          brillos.forEach((b, i) => { pos.set(b, i * 3); fa[i] = hz(i, 140); });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 1));
          matB = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uTam: { value: 3.6 * M }, cA: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "uniform float uPx, uTam, uT; attribute float aF; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(uTam * uPx / max(1e-3, -mv.z), 1.5, 26.0); vA = 0.8 + 0.12 * sin(uT * 7.3 + aF * 40.0) + 0.08 * sin(uT * 2.9 + aF * 17.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.5 * vA * exp(-r * r * 4.5); gl_FragColor = vec4(srgb(cA) * a, a); }" });
          const m = new THREE.Points(g, matB); m.frustumCulled = false; m.renderOrder = 9; scene.add(m);
        }
        let matH = null;
        if (humos.length) {
          const NP = 7, g = new THREE.BufferGeometry(), pos = new Float32Array(humos.length * NP * 3), fa = new Float32Array(humos.length * NP * 2);
          humos.forEach((h, i) => { for (let j = 0; j < NP; j++) { pos.set(h.P, (i * NP + j) * 3); fa[(i * NP + j) * 2] = h.f; fa[(i * NP + j) * 2 + 1] = j / NP; } });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 2));
          const vi = [Math.cos(r + 2.2), -Math.sin(r + 2.2)];
          matH = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, uV: { value: new THREE.Vector2(vi[0], vi[1]) }, cA: { value: cHumo.clone() }, uK: { value: noche ? 0.16 : 0.5 } },
            transparent: true, depthWrite: false,
            vertexShader: "uniform float uPx, uT, uM; uniform vec2 uV; attribute vec2 aF; varying float vA; void main(){ float a = fract(uT / 8.0 + aF.x + aF.y); vec3 p = position + vec3(uV.x * a * a * 9.0, a * 12.0, uV.y * a * a * 9.0) * uM; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp((1.0 + 3.6 * a) * uM * uPx / max(1e-3, -mv.z), 1.0, 60.0); vA = (1.0 - a) * smoothstep(0.0, 0.15, a); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.6); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, matH); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }
        let lluvia = null;
        const LL = clamp(p.lluvia, 0, 1);
        if (LL > 0) {
          const N = Math.round(500 + 5500 * LL), g = new THREE.BufferGeometry(), pos = new Float32Array(N * 6), ex = new Float32Array(N * 2);
          for (let i = 0; i < N; i++) { const a = [hz(i, 150), hz(i, 151), hz(i, 152)]; pos.set(a, i * 6); pos.set(a, i * 6 + 3); ex[i * 2] = 0; ex[i * 2 + 1] = 1; }
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aE", new THREE.BufferAttribute(ex, 1));
          const vi = [Math.cos(r + 2.2), -Math.sin(r + 2.2)];
          const mat = new THREE.ShaderMaterial({ uniforms: { uT, uC: { value: new THREE.Vector3() }, uS: { value: 300 }, uVel: { value: 8 * M }, uV: { value: new THREE.Vector2(vi[0], vi[1]) },
            cA: { value: cLluvia.clone() }, uA: { value: (noche ? 0.18 : 0.24) + 0.32 * LL } }, transparent: true, depthWrite: false,
            vertexShader: "uniform float uT, uS, uVel; uniform vec3 uC; uniform vec2 uV; attribute float aE; void main(){ vec3 q = position * uS; vec3 d = vec3(uV.x * 0.45, -1.0, uV.y * 0.45); q += d * uT * uVel; vec3 lo = uC - 0.5 * uS; vec3 w = lo + mod(q - lo, uS); w -= d * aE * uS * 0.016; gl_Position = projectionMatrix * viewMatrix * vec4(w, 1.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uA; void main(){ gl_FragColor = vec4(srgb(cA), uA); }" });
          const m = new THREE.LineSegments(g, mat); m.frustumCulled = false; m.renderOrder = 10; scene.add(m);
          lluvia = mat;
        }

        // ================= la gente: por la plaza (en ronda y cruzándola), por la calle y frente a la iglesia
        const NP = clamp(p.personas | 0, 0, 12), npv = noche ? Math.ceil(NP / 2) : NP;
        const a2 = PLAZA / 2 - 3;
        const RUTAS = [
          { pts: [[-a2, -a2], [a2, -a2], [a2, a2], [-a2, a2], [-a2, -a2]], loop: true },
          { pts: [[-a2, a2], [a2, a2], [a2, -a2], [-a2, -a2], [-a2, a2]], loop: true },
          { pts: calles[0].pts.slice(0, 22), loop: false },
          { pts: [[-a2, -a2 + 4], [a2 - 4, a2]], loop: false },
          { pts: [[-PLAZA / 2 + 2, 2], [PLAZA / 2 + 4, 1]], loop: false },
          { pts: calles[1].pts.slice(0, 16), loop: false },
          { pts: calles[2].pts.slice(0, 16), loop: false },
        ].map((ru) => { const S = [0]; for (let i = 1; i < ru.pts.length; i++) S.push(S[i - 1] + Math.hypot(ru.pts[i][0] - ru.pts[i - 1][0], ru.pts[i][1] - ru.pts[i - 1][1])); return { ...ru, S, L: S[S.length - 1] }; });
        const gente = [];
        for (let i = 0; i < npv; i++) {
          const quieto = i % 5 === 4;
          gente.push({ ru: RUTAS[i % RUTAS.length], s0: hz(i, 160), v: quieto ? 0 : 1.0 + 0.4 * hz(i, 161), sg: hz(i, 162) < 0.5 ? 1 : -1, quieto,
            qu: PLAZA / 2 + 2 + 2 * hz(i, 163), qv: (hz(i, 164) - 0.5) * 8 });
        }
        const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: K, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991 }) : null;
        return { id: p.id, M, ux, uy, W2, mats, matFoc, matB, matH, lluvia, uPx, uT, gente, flP, noche };
      });
    },
    en(t, lista, ctx) {
      const { THREE, clamp } = ctx;
      const dir = new THREE.Vector3();
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.35 * kb;
        s.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.uT.value = t;
        if (s.lluvia) {
          const D = (ctx.cuadro && ctx.cuadro.dist) || 300 * s.M;
          ctx.camera.getWorldDirection(dir);
          const S = clamp(D * 0.9, 30 * s.M, 900 * s.M);
          s.lluvia.uniforms.uS.value = S;
          s.lluvia.uniforms.uC.value.copy(ctx.camera.position).addScaledVector(dir, Math.min(D * 0.55, S * 0.5));
        }
        if (s.flP) {
          s.gente.forEach((g, i) => {
            const toW = (u, v) => s.W2(u, v), dW = (du, dv) => [du * s.ux - dv * s.uy, du * s.uy + dv * s.ux];
            if (g.quieto) {
              const [x, y] = toW(g.qu, g.qv), [dx, dy] = dW(-1, 0);
              s.flP.poner(i, x, y, dx, dy, 1, 0, 0);
              return;
            }
            const ru = g.ru, L = ru.L || 1;
            let q = g.s0 * L + g.v * t * g.sg, sg = g.sg;
            if (ru.loop) q = ((q % L) + L) % L;
            else { const m = ((q % (2 * L)) + 2 * L) % (2 * L); q = m > L ? 2 * L - m : m; sg = g.sg * (m > L ? -1 : 1); }
            let k = 1; while (k < ru.S.length - 1 && ru.S[k] < q) k++;
            const a = ru.pts[k - 1], bb = ru.pts[k], f = (q - ru.S[k - 1]) / Math.max(1e-6, ru.S[k] - ru.S[k - 1]);
            const u = a[0] + (bb[0] - a[0]) * f, v = a[1] + (bb[1] - a[1]) * f, Lk = Math.hypot(bb[0] - a[0], bb[1] - a[1]) || 1;
            const ru_ = (bb[0] - a[0]) / Lk * sg, rv = (bb[1] - a[1]) / Lk * sg, [x, y] = toW(u, v), [dx, dy] = dW(ru_, rv);
            s.flP.poner(i, x, y, dx, dy, 1, 0, g.v * s.M / ctx.metros(1));
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
