// Pieza «cabildoranchos» (ficha: cabildoranchos.json; reglas: scripts/maqueta_tipos/cabildoranchos.py): un llano abierto y
// modesto, sin obras, donde UN rancho de paja hace de casa consistorial. Genérico, sin lugar real. Centrada en `lugar` (la mesa
// bajo el rancho) y orientada por `rumbo` (u: hacia donde queda la ermita sobre su loma; v: a su izquierda). METROS × `tamano`.
// - EL RANCHO DEL CABILDO: abierto, sin paredes: seis horcones con su horqueta, soleras y tirantes, techo de paja a dos aguas
//   en tres hiladas con su fleco en el alero, alfardas a la vista por debajo y la cumbrera. Debajo, sobre el piso apisonado:
//   una mesa de tablas con papeles, tintero y pluma, una vela (encendida de noche), dos bancas, un cofre, y `cabildantes`
//   sentados (persona, pose `sentado`) más el escribano de pie en la cabecera (pose `clasificar`: las manos van y vienen sobre
//   el papel). Mesa, bancas y cofre son ambientación genérica.
// - EL RANCHERÍO: `ranchos` de alojamiento alrededor (paredes de caña, de tabla o de bajareque, techo de paja; `enlucidas` de
//   ellos, enlucidos y con teja), cada uno con su puerta, unos con corredor de horcones, fogón de tres piedras con su comal
//   y su humo, cántaros y leña.
// - EL LLANO: tierra apisonada al centro que se vuelve zacate, matas, árboles sueltos, el camino de llegada con sus rodadas y
//   las veredas a cada rancho; con `iglesia`, una ermita sencilla y pequeña sobre una loma al fondo (genérica: nave enlucida,
//   espadaña, techo de teja) con su vereda: nunca frente al rancho.
// - CON VIDA (seek puro): `llegan` capitulares que caminan sin prisa desde sus ranchos y llegan al rancho del cabildo en
//   `llegada_s`; `vecinos` que van y vienen por las veredas (la mitad con un bulto a la espalda); `mulas` con su carga y su
//   arriero y `carretas` de bueyes con su boyero que entran por el camino y se detienen en `llegada_s` (las patas y las
//   ruedas, función de lo recorrido); humo de los fogones. De noche (ES.noche) se encienden la vela, los fogones, algunas
//   puertas y la de la ermita (puntos de luz genéricos, no un dato).
// La pieza PUBLICA sus lugares (rancho, mesa, iglesia, llegada, ranchos, llano) y el camino «<id>.llegada»
// y el piso del llano (`_alturas`: un plano a 0.12 m, para que la gente y los vehículos de otros lo pisen) (cabildoranchos.py: la misma traza). Sin colores escritos (ctx.tonos, ctx.COL); sin texto ni marcas.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  const BASE = 0.12;                                        // el piso del llano: un plano que la pieza publica (cabildoranchos.py)
  const RC = { L: 4.6, W: 3.1, H: 2.45 };                  // el rancho del cabildo: medio largo (a lo largo de v), medio fondo, alero
  const ERMITA = [58, 20], LOMA_R = 24, LOMA_H = 5.5, LOMA_T = 8;
  const CAMINO = [[-96, -30], [-72, -23], [-50, -14], [-32, -7.5], [-19, -4], [-6, -1.4]];
  const RANCHOS = [[-15, 19], [5, 23], [-23, -21], [13, -20], [25, 6], [-35, 23], [27, -9], [-4, 35]];
  const ENLUCIDAS = [1, 4, 6];
  const ARBOLES = [[-8, 48], [19, 39], [42, -27], [-48, 37], [-12, -39], [36, 37], [-60, 7], [8, -41], [-31, -35]];
  const HUB = [-10, 7.5], JR = [-13, -3.4];
  const SPOTS = [[-4.2, 2.6], [-4.2, -1.8], [-4.8, 0.5]];  // donde se quedan los capitulares que llegan
  const QUIENES = [0, 2, 7];                                // de qué rancho sale cada uno
  const lisa = (a, b, x) => { const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const lomaH = (r) => LOMA_H * (1 - lisa(LOMA_T, LOMA_R, r));
  const polil = (pts) => { const S = [0]; for (let i = 1; i < pts.length; i++) S.push(S[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return { pts, S, L: S[S.length - 1] }; };
  const enPol = (P, s) => {
    s = Math.max(0, Math.min(P.L, s));
    let k = 1; while (k < P.S.length - 1 && P.S[k] < s) k++;
    const a = P.pts[k - 1], b = P.pts[k], l = (P.S[k] - P.S[k - 1]) || 1, f = (s - P.S[k - 1]) / l;
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / l, (b[1] - a[1]) / l];
  };
  const dPol = (u, v, pts) => {
    let d = 1e9;
    for (let i = 0; i + 1 < pts.length; i++) {
      const [a, b] = pts[i], [c, e] = pts[i + 1], du = c - a, dv = e - b, l2 = du * du + dv * dv || 1;
      const f = Math.max(0, Math.min(1, ((u - a) * du + (v - b) * dv) / l2));
      d = Math.min(d, Math.hypot(u - a - du * f, v - b - dv * f));
    }
    return d;
  };
  const remuestra = (pts, paso) => {
    const P = polil(pts), n = Math.max(1, Math.round(P.L / paso)), out = [];
    for (let i = 0; i <= n; i++) { const q = enPol(P, P.L * i / n); out.push([q[0], q[1]]); }
    return out;
  };
  // lo que falta por recorrer a x s de llegar (v m/s; frena suave en τ s) y la velocidad que lleva
  const falta = (x, v, tau) => x <= 0 ? [0, 0] : x < tau ? [v * x * x / (2 * tau), v * x / tau] : [v * (x - tau / 2), v];

  MAQ.PIEZAS.cabildoranchos = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const ico1 = new THREE.IcosahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
      const c = new THREE.Color();
      // ---- los tonos (todos del estilo)
      const cTierra = lin(COL.tierra_media).lerp(tonos.arena, 0.35).multiplyScalar(oscuro ? 0.95 : 0.85);
      const cApis = tonos.calle.clone().lerp(cTierra, 0.6).multiplyScalar(oscuro ? 1.0 : 0.92);
      const cZacate = tonos.campo.clone().lerp(lin(COL.tierra_alta), 0.38).multiplyScalar(oscuro ? 1.0 : 0.95);
      const cMata = tonos.verde.clone().lerp(tonos.campo2, 0.4).lerp(lin(COL.tierra_alta), 0.22).multiplyScalar(oscuro ? 1.1 : 0.78);
      const cCamino = tonos.calle.clone().lerp(cTierra, 0.45), cRodada = cCamino.clone().multiplyScalar(0.72);
      const cPaja = lin(COL.tierra_alta).lerp(tonos.medio, 0.3).multiplyScalar(oscuro ? 0.92 : 0.86);
      const cTeja = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.5).multiplyScalar(oscuro ? 0.9 : 0.85);
      const cCana = lin(COL.tierra_alta).lerp(tonos.arena, 0.4).multiplyScalar(oscuro ? 0.9 : 0.8);
      const cAdobe = tonos.muro.clone().lerp(lin(COL.tierra_media), 0.38).lerp(tonos.arena, 0.15);
      const cBajareque = cAdobe.clone().lerp(cTierra, 0.4).multiplyScalar(0.9);
      const cEnlucido = tonos.muro.clone().lerp(lin(COL.costa), 0.35);
      const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.45), cZocalo = cRoca.clone().multiplyScalar(0.78);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.22);
      const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
      const cTabla = cMadera.clone().lerp(lin(COL.tierra_media), 0.45).multiplyScalar(oscuro ? 1.05 : 1.1);
      const cPapel = lin(COL.costa).lerp(tonos.arena, 0.2);
      const cTinta = tonos.asfalto.clone().multiplyScalar(0.35);
      const cMula = lin(COL.tierra_media).lerp(tonos.linea, 0.55).multiplyScalar(oscuro ? 1.2 : 0.72);
      const cBuey = lin(COL.tierra_alta).lerp(tonos.muro, 0.4).multiplyScalar(oscuro ? 1.0 : 0.9);
      const cCuerno = lin(COL.costa).lerp(tonos.arena, 0.4);
      const cSaco = lin(COL.tierra_alta).lerp(tonos.arena, 0.5).multiplyScalar(0.9);
      const cBarro = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.65);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.5 : dia ? 0.85 : 0.95);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cCeniza = tonos.muro.clone().lerp(tonos.asfalto, 0.3).multiplyScalar(0.8);
      const cLuz = lin(COL.luces), cHumo = tonos.muro.clone().lerp(lin(COL.costa), 0.5);
      const neg = (d) => [-d[0], -d[1], -d[2]], UP = [0, 1, 0];

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
      const disco = (acc, C, r, seg, col, abajo) => {          // un disco horizontal (tapa)
        for (let i = 0; i < seg; i++) {
          const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, P0 = [C[0] + r * Math.cos(a0), C[1], C[2] + r * Math.sin(a0)], P1 = [C[0] + r * Math.cos(a1), C[1], C[2] + r * Math.sin(a1)];
          cara(acc, [C, P0, P1, P1], col, abajo ? [0, -1, 0] : UP);
        }
      };
      const cono = (acc, P, r, h, seg, col) => {
        const T = [P[0], P[1] + h, P[2]];
        for (let i = 0; i < seg; i++) {
          const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
          cara(acc, [[P[0] + r * Math.cos(a0), P[1], P[2] + r * Math.sin(a0)], [P[0] + r * Math.cos(a1), P[1], P[2] + r * Math.sin(a1)], T, T], col, [Math.cos(am), r / Math.max(1e-6, Math.abs(h)), Math.sin(am)]);
        }
      };
      const gema = (acc, tri, P, rx, ry, rz, rot, col, plana = 0) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), cc = new THREE.Color();
        for (let i = 0; i < tri.length; i += 9) {
          const v = [];
          for (let j = 0; j < 9; j += 3) { const x = tri[i + j] * rx, y = tri[i + j + 1] * ry, z = tri[i + j + 2] * rz; v.push([P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr]); }
          const e1 = [v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]], e2 = [v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1;
          cc.copy(col).multiplyScalar(plana + (1 - plana) * sombra(nx / n, Math.abs(ny / n), nz / n));
          const q = acc.pos.length / 3;
          for (const w of v) { acc.pos.push(w[0], w[1], w[2]); acc.col.push(cc.r, cc.g, cc.b); }
          acc.idx.push(q, q + 1, q + 2);
        }
      };
      const sRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const W2 = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const D2 = (du, dv) => [du * ux - dv * uy, du * uy + dv * ux];
        const E = (u, v, h) => { const [x, y] = W2(u, v); return [x, ctx.suelo(x, y) + (h + BASE) * M, -y]; };
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // el marco de un edificio: s a lo largo de `ang` (radianes en el plano local u, v), t a su izquierda
        const marco = (cu, cv, ang, lev = 0) => {
          const a = ang + r, ax = Math.cos(a), ay = Math.sin(a), [cx, cy] = W2(cu, cv), y0 = ctx.suelo(cx, cy) + (lev + BASE) * M;
          const F = (s, t, y) => [cx + (ax * s - ay * t) * M, y0 + y * M, -(cy + (ay * s + ax * t) * M)];
          const P2 = (s, t) => [cx + (ax * s - ay * t) * M, cy + (ay * s + ax * t) * M];
          const D = (ds, dt) => [ax * ds - ay * dt, ay * ds + ax * dt];
          return { F, P2, D, S: [ax, 0, -ay], T: [-ay, 0, -ax] };
        };
        const mats = [];
        const poner = (acc, op, orden) => { if (!acc.idx.length) return null; const mat = malla.material(op || {}); mats.push(mat); malla.poner(acc, mat, orden); return mat; };
        const suelo = malla.nueva(), sendas = malla.nueva(), muros = malla.nueva(), techos = malla.nueva(), solido = malla.nueva();
        const veg = malla.nueva(), huecos = malla.nueva(), focos = malla.nueva(), papeles = malla.nueva();
        const brillos = [], humos = [];
        const nR = clamp(p.ranchos | 0, 1, RANCHOS.length);

        // ================= el llano: una malla de vértices con el tono de cada uno (tierra apisonada al centro, zacate afuera)
        {
          const RS = 90, CS = 3, N = Math.round(2 * RS / CS), lS = sombra(0, 1, 0), q0 = suelo.pos.length / 3;
          for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) {
            const u = -RS + i * CS, v = -RS + j * CS, rr = Math.hypot(u, v), n1 = ruido(u, v, 11, 3), n2 = ruido(u, v, 3.5, 4);
            const z = clamp(lisa(9, 34, rr) * 0.92 + 0.55 * (n1 - 0.5) + 0.15 * (n2 - 0.5), 0, 1);
            c.copy(cApis).lerp(cZacate, z).multiplyScalar(0.9 + 0.16 * n2).lerp(tonos.campo, lisa(64, RS, rr));
            const P = E(u, v, 0.03); suelo.pos.push(...P); suelo.col.push(c.r * lS, c.g * lS, c.b * lS);
          }
          for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
            if (Math.hypot(-RS + (i + 0.5) * CS, -RS + (j + 0.5) * CS) > RS) continue;
            const a = q0 + i * (N + 1) + j, b = a + 1, d = a + N + 1, e = d + 1;
            suelo.idx.push(a, d, b, b, d, e);
          }
        }
        // ---- franjas de suelo a lo largo de una polilínea (camino, veredas)
        const franja = (acc, pts, w, col, lev, k, desv = 0) => {
          const n = pts.length, L = [], R = [];
          for (let i = 0; i < n; i++) {
            const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)], du = b[0] - a[0], dv = b[1] - a[1], l = Math.hypot(du, dv) || 1;
            const nu = -dv / l, nv = du / l, ww = w * (0.9 + 0.2 * hz(k * 131 + i, 31)) / 2;
            L.push([pts[i][0] + nu * (desv + ww), pts[i][1] + nv * (desv + ww)]); R.push([pts[i][0] + nu * (desv - ww), pts[i][1] + nv * (desv - ww)]);
          }
          for (let i = 0; i + 1 < n; i++) {
            const cc = col.clone().multiplyScalar(0.92 + 0.14 * hz(k * 131 + i, 32));
            cara(acc, [E(...L[i], lev), E(...R[i], lev), E(...R[i + 1], lev), E(...L[i + 1], lev)], cc, null);
          }
        };
        const camino = remuestra(CAMINO, 2);
        franja(sendas, camino, 3.6, cCamino, 0.05, 1);
        for (const d of [-0.8, 0.8]) franja(sendas, camino, 0.36, cRodada, 0.065, 2 + (d > 0 ? 1 : 0), d);
        franja(sendas, camino, 0.45, cCamino.clone().lerp(cZacate, 0.55), 0.06, 4);
        // las puertas de los ranchos (el frente mira al rancho del cabildo) y sus veredas
        const ranchos = RANCHOS.slice(0, nR).map(([cu0, cv0], j) => {
          const k = 300 + j * 37, cu = cu0 + (hz(k, 7) - 0.5) * 3, cv = cv0 + (hz(k, 8) - 0.5) * 3;
          const phi = Math.atan2(-cv, -cu), ang = phi - Math.PI / 2 + (hz(k, 5) - 0.5) * 0.5;
          const L = 2.5 + 0.9 * hz(k, 2), Wd = 1.8 + 0.45 * hz(k, 3), hw = 2.15 + 0.3 * hz(k, 4);
          const tipo = ENLUCIDAS.slice(0, clamp(p.enlucidas | 0, 0, 3)).includes(j) ? "enlucida" : hz(k, 1) < 0.45 ? "cana" : hz(k, 1) < 0.8 ? "bajareque" : "tabla";
          const corredor = tipo !== "enlucida" && hz(k, 9) < 0.4, sD = (hz(k, 10) - 0.5) * (L - 1.2);
          const tF = Wd + (corredor ? 3.3 : 2.3), sF = sD + (hz(k, 11) < 0.5 ? -1.6 : 1.6);
          const B = marco(cu, cv, ang), aa = ang, ca = Math.cos(aa), sa = Math.sin(aa);
          const loc = (s, t) => [cu + ca * s - sa * t, cv + sa * s + ca * t];
          return { j, k, cu, cv, ang, L, Wd, hw, tipo, corredor, sD, tF, sF, B, loc, puerta: loc(sD, Wd + 1.6), fogon: loc(sF, tF) };
        });
        const veredas = ranchos.map((q) => {
          const dH = Math.hypot(q.puerta[0] - HUB[0], q.puerta[1] - HUB[1]), dJ = Math.hypot(q.puerta[0] - JR[0], q.puerta[1] - JR[1]);
          const o = dH <= dJ ? HUB : JR, m = [(o[0] + q.puerta[0]) / 2 + (hz(q.k, 12) - 0.5) * 4, (o[1] + q.puerta[1]) / 2 + (hz(q.k, 13) - 0.5) * 4];
          return remuestra([o, m, q.puerta], 1.5);
        });
        veredas.forEach((pts, i) => franja(sendas, pts, 1.15, cCamino.clone().lerp(cApis, 0.3), 0.045, 20 + i));
        franja(sendas, remuestra([JR, [-8, 1.5], HUB], 1.5), 1.3, cCamino.clone().lerp(cApis, 0.3), 0.045, 40);
        const dE = Math.hypot(...ERMITA), eu = ERMITA[0] / dE, ev = ERMITA[1] / dE;
        if (p.iglesia) franja(sendas, remuestra([[RC.W + 2.2, 0.6], [ERMITA[0] - eu * (LOMA_R - 0.5), ERMITA[1] - ev * (LOMA_R - 0.5)]], 1.6), 1.2, cCamino.clone().lerp(cApis, 0.3), 0.045, 41);

        // ================= techos de paja (tres hiladas con su labio, fleco en el alero) y de teja (canales a lo largo)
        const techoPaja = (B, l, w, hw, ov, col, k, abierto) => {
          const F = B.F, pz = 0.68, tp = Math.tan(pz), dth = 0.34 / Math.cos(pz), Ls = l + 0.7, yR = hw + w * tp;
          for (const sg of [1, -1]) {
            const te = sg * (w + ov), ye = hw - ov * tp, fuera = sg > 0 ? B.T : neg(B.T);
            const at = (f, off) => [te * (1 - f), ye + (yR - ye) * f + off];
            [[0, 0.38, 0.55], [0.34, 0.7, 0.8], [0.66, 1.0, 1.0]].forEach(([f0, f1, o], q) => {
              const [t0, y0] = at(f0, dth * o), [t1, y1] = at(f1, dth * o), [tb, yb] = at(f0, dth * (o - 0.55));
              cara(techos, [F(-Ls, t0, y0), F(Ls, t0, y0), F(Ls, t1, y1), F(-Ls, t1, y1)], col.clone().multiplyScalar(0.88 + 0.06 * q + 0.04 * hz(k, 50 + q)), null);
              cara(techos, [F(-Ls, tb, yb), F(Ls, tb, yb), F(Ls, t0, y0), F(-Ls, t0, y0)], col.clone().multiplyScalar(0.6), fuera);
              for (const ss of [Ls, -Ls]) cara(techos, [F(ss, tb, yb), F(ss, t0, y0), F(ss, t1, y1), F(ss, t1, y1 - dth * 0.55)], col.clone().multiplyScalar(0.58), ss > 0 ? B.S : neg(B.S));
            });
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, 0, yR), F(-Ls, 0, yR)], col.clone().multiplyScalar(abierto ? 0.4 : 0.5), [0, -1, 0]);
            const nF = Math.round(2 * Ls / 0.24), [tA, yA] = at(0, dth * 0.05);
            for (let i = 0; i < nF; i++) {
              const s0 = -Ls + 2 * Ls * i / nF, s1 = -Ls + 2 * Ls * (i + 1) / nF, ll = 0.12 + 0.2 * hz(k * 977 + i * 2 + (sg > 0 ? 1 : 0), 51);
              cara(techos, [F(s0, tA, yA), F(s1, tA, yA), F((s0 + s1) / 2, tA + sg * 0.05, yA - ll), F((s0 + s1) / 2, tA + sg * 0.05, yA - ll)],
                col.clone().multiplyScalar(0.66 + 0.16 * hz(k * 977 + i, 52)), fuera);
            }
            if (abierto) for (let s = -Ls + 0.35; s < Ls; s += 0.85) tubo(solido, F(s, te * 0.97, ye - 0.08), F(s, 0, yR - 0.1), 0.05 * M, 5, cMadera);
          }
          tubo(techos, F(-Ls - 0.1, 0, yR + dth * 0.95), F(Ls + 0.1, 0, yR + dth * 0.95), 0.26 * M, 8, col.clone().multiplyScalar(0.76));
          return { yR, tp };
        };
        const techoTeja = (B, l, w, hw, ov, col, k) => {
          const F = B.F, pz = 0.45, tp = Math.tan(pz), dth = 0.14, Ls = l + 0.45, yR = hw + w * tp;
          for (const sg of [1, -1]) {
            const te = sg * (w + ov), ye = hw - ov * tp, fuera = sg > 0 ? B.T : neg(B.T);
            cara(techos, [F(-Ls, te, ye + dth), F(Ls, te, ye + dth), F(Ls, 0, yR + dth), F(-Ls, 0, yR + dth)], col.clone().multiplyScalar(0.93 + 0.06 * hz(k, 55)), null);
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, 0, yR), F(-Ls, 0, yR)], col.clone().multiplyScalar(0.5), [0, -1, 0]);
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, te, ye + dth), F(-Ls, te, ye + dth)], col.clone().multiplyScalar(0.7), fuera);
            for (const ss of [Ls, -Ls]) cara(techos, [F(ss, te, ye), F(ss, 0, yR), F(ss, 0, yR + dth), F(ss, te, ye + dth)], col.clone().multiplyScalar(0.62), ss > 0 ? B.S : neg(B.S));
            for (let s = -Ls + 0.14; s < Ls; s += 0.28)
              tubo(techos, F(s, te, ye + dth + 0.03), F(s, 0, yR + dth + 0.03), 0.055 * M, 4, col.clone().multiplyScalar(0.8 + 0.2 * hz(k * 31 + Math.round(s * 10) + (sg > 0 ? 500 : 0), 56)));
          }
          tubo(techos, F(-Ls, 0, yR + dth + 0.06), F(Ls, 0, yR + dth + 0.06), 0.13 * M, 6, col.clone().multiplyScalar(0.75));
          return { yR, tp };
        };
        // ================= una pared (eje "s": a lo largo de s en t = fijo; eje "t": a lo largo de t en s = fijo), de -0.05 a
        // alto(a), con huecos [a0, a1, y_dintel]: caña (tiras verticales con dos amarres), tabla (hiladas), bajareque o enlucida
        const pared = (B, eje, a0, a1, fijo, lado, alto, tipo, col, k, hs = []) => {
          const ref = eje === "s" ? (lado > 0 ? B.T : neg(B.T)) : (lado > 0 ? B.S : neg(B.S));
          const P = (a, y, d = 0) => eje === "s" ? B.F(a, fijo + lado * d, y) : B.F(fijo + lado * d, a, y);
          const hueco = (m) => hs.find((h) => m > h[0] && m < h[1]);
          if (tipo === "cana") {
            const n = Math.max(2, Math.round((a1 - a0) / 0.11));
            for (let i = 0; i < n; i++) {
              const a = a0 + (a1 - a0) * i / n, b = a0 + (a1 - a0) * (i + 1) / n, h = hueco((a + b) / 2), d = (i % 2) * 0.025;
              const yb = h ? h[2] : -0.05, ya = alto(a), yb2 = alto(b);
              if (yb >= Math.min(ya, yb2) - 0.02) continue;
              cara(muros, [P(a, yb, d), P(b, yb, d), P(b, yb2, d), P(a, ya, d)], col.clone().multiplyScalar(0.8 + 0.22 * hz(k * 977 + i, 81) + (i % 2 ? 0 : 0.06)), ref);
            }
            const cortes = [a0].concat(...hs.map((h) => [h[0], h[1]]), [a1]).sort((x, y) => x - y);
            for (let i = 0; i + 1 < cortes.length; i += 2) for (const yy of [0.85, 1.7]) {
              if (alto(cortes[i]) < yy + 0.1 || alto(cortes[i + 1]) < yy + 0.1) continue;
              cara(solido, [P(cortes[i], yy, 0.06), P(cortes[i + 1], yy, 0.06), P(cortes[i + 1], yy + 0.07, 0.06), P(cortes[i], yy + 0.07, 0.06)], cMadera, ref);
            }
            return;
          }
          const paso = tipo === "tabla" ? 1.6 : 0.7, fila = tipo === "tabla" ? 0.26 : 0.6;
          const br = [a0]; for (let a = a0 + paso; a < a1 - 0.1; a += paso) br.push(a); br.push(a1);
          for (const h of hs) br.push(h[0], h[1]);
          br.sort((x, y) => x - y);
          const top = Math.max(alto(a0), alto(a1), alto((a0 + a1) / 2));
          for (let i = 0; i + 1 < br.length; i++) {
            const a = br[i], b = br[i + 1]; if (b - a < 0.02) continue;
            const h = hueco((a + b) / 2);
            for (let y0 = -0.05, q = 0; y0 < top; y0 += fila, q++) {
              let ya = Math.min(y0 + fila, alto(a)), yb = Math.min(y0 + fila, alto(b)), yy = y0;
              if (h) yy = Math.max(yy, h[2]);
              if (yy >= Math.max(ya, yb) - 0.01) continue;
              ya = Math.max(ya, yy); yb = Math.max(yb, yy);
              const n1 = tipo === "tabla" ? hz(k * 977 + q * 31 + i, 82) : ruido((a + b) * 0.9, y0 * 1.3 + k, 1.4, 83);
              const cc = col.clone().multiplyScalar(tipo === "enlucida" ? 0.95 + 0.07 * n1 : tipo === "tabla" ? 0.8 + 0.28 * n1 : 0.82 + 0.24 * n1);
              cara(muros, [P(a, yy), P(b, yy), P(b, yb), P(a, ya)], cc, ref);
              if (tipo === "tabla" && yy === y0) cara(solido, [P(a, y0, 0.02), P(b, y0, 0.02), P(b, Math.min(y0 + 0.035, yb), 0.02), P(a, Math.min(y0 + 0.035, ya), 0.02)], cc.clone().multiplyScalar(0.55), ref);
            }
          }
        };

        // ================= los ranchos de alojamiento
        for (const q of ranchos) {
          const { B, L, Wd, hw, k, tipo, sD } = q, F = B.F, teja = tipo === "enlucida";
          const col = { cana: cCana, tabla: cTabla, bajareque: cBajareque, enlucida: cEnlucido }[tipo].clone().multiplyScalar(0.92 + 0.12 * hz(k, 14));
          const roof = teja ? techoTeja(B, L, Wd, hw, 0.55, cTeja.clone().multiplyScalar(0.92 + 0.12 * hz(k, 15)), k)
            : techoPaja(B, L, Wd, hw, q.corredor ? 0.3 : 0.75, cPaja.clone().multiplyScalar(0.9 + 0.14 * hz(k, 15)), k, false);
          const gable = (tt) => hw + (Wd - Math.abs(tt)) * roof.tp, recto = () => hw;
          const puerta = [[sD - 0.45, sD + 0.45, 1.85]];
          if (tipo === "bajareque" || teja) {                        // el zócalo
            const z = 0.12;
            cara(solido, [F(-L - z, Wd + z, 0.4), F(L + z, Wd + z, 0.4), F(L + z, -Wd - z, 0.4), F(-L - z, -Wd - z, 0.4)], cZocalo, UP);
            for (const [a, b, n] of [[[-L - z, Wd + z], [L + z, Wd + z], B.T], [[L + z, -Wd - z], [-L - z, -Wd - z], neg(B.T)], [[L + z, Wd + z], [L + z, -Wd - z], B.S], [[-L - z, -Wd - z], [-L - z, Wd + z], neg(B.S)]])
              cara(solido, [F(a[0], a[1], -0.2), F(b[0], b[1], -0.2), F(b[0], b[1], 0.4), F(a[0], a[1], 0.4)], cZocalo.clone().multiplyScalar(0.92), n);
          }
          pared(B, "s", -L, L, Wd, 1, recto, tipo, col, k, puerta);
          pared(B, "s", -L, L, -Wd, -1, recto, tipo, col, k + 1);
          pared(B, "t", -Wd, Wd, L, 1, gable, tipo, col, k + 2);
          pared(B, "t", -Wd, Wd, -L, -1, gable, tipo, col, k + 3);
          if (tipo === "bajareque" || tipo === "cana") for (const [s, t] of [[-L, Wd], [L, Wd], [-L, -Wd], [L, -Wd]])
            tubo(solido, F(s, t, -0.1), F(s, t, hw + 0.1), 0.1 * M, 6, cMadera);
          // la puerta: el hueco oscuro (o la luz del fogón de adentro, de noche) y su marco
          const luzOn = noche && hz(k, 16) < 0.55;
          cara(luzOn ? focos : huecos, [F(sD - 0.45, Wd - 0.1, 0), F(sD + 0.45, Wd - 0.1, 0), F(sD + 0.45, Wd - 0.1, 1.85), F(sD - 0.45, Wd - 0.1, 1.85)], luzOn ? cLuz.clone().multiplyScalar(0.6) : cHueco, B.T);
          if (luzOn) brillos.push(F(sD, Wd + 0.5, 0.9));
          for (const ss of [sD - 0.5, sD + 0.5]) tubo(solido, F(ss, Wd + 0.04, -0.05), F(ss, Wd + 0.04, 1.92), 0.055 * M, 4, cMadera);
          tubo(solido, F(sD - 0.62, Wd + 0.04, 1.9), F(sD + 0.62, Wd + 0.04, 1.9), 0.055 * M, 4, cMadera);
          if (teja) {                                               // la ventana con su postigo
            const sV = sD > 0 ? sD - 1.5 : sD + 1.5;
            if (Math.abs(sV) < L - 0.4) {
              cara(huecos, [F(sV - 0.35, Wd + 0.03, 1.1), F(sV + 0.35, Wd + 0.03, 1.1), F(sV + 0.35, Wd + 0.03, 1.65), F(sV - 0.35, Wd + 0.03, 1.65)], cHueco, B.T);
              cara(solido, [F(sV + 0.35, Wd + 0.04, 1.08), F(sV + 0.8, Wd + 0.3, 1.08), F(sV + 0.8, Wd + 0.3, 1.67), F(sV + 0.35, Wd + 0.04, 1.67)], cTabla, B.T);
            }
          }
          if (q.corredor) {                                         // corredor de horcones con su alero de paja
            const tE = Wd + 2.1, yE = 1.95, dth = 0.3;
            cara(techos, [F(-L - 0.4, Wd, hw - 0.05 + dth), F(L + 0.4, Wd, hw - 0.05 + dth), F(L + 0.4, tE, yE + dth), F(-L - 0.4, tE, yE + dth)], cPaja.clone().multiplyScalar(0.9), null);
            cara(techos, [F(-L - 0.4, Wd, hw - 0.05), F(L + 0.4, Wd, hw - 0.05), F(L + 0.4, tE, yE), F(-L - 0.4, tE, yE)], cPaja.clone().multiplyScalar(0.42), [0, -1, 0]);
            cara(techos, [F(-L - 0.4, tE, yE), F(L + 0.4, tE, yE), F(L + 0.4, tE, yE + dth), F(-L - 0.4, tE, yE + dth)], cPaja.clone().multiplyScalar(0.65), B.T);
            for (const ss of [-L + 0.1, L - 0.1]) tubo(solido, F(ss, tE - 0.2, -0.1), F(ss, tE - 0.2, yE + 0.05), 0.09 * M, 6, cMadera);
            const nF = Math.round((2 * L + 0.8) / 0.24);
            for (let i = 0; i < nF; i++) {
              const s0 = -L - 0.4 + (2 * L + 0.8) * i / nF, s1 = -L - 0.4 + (2 * L + 0.8) * (i + 1) / nF, ll = 0.1 + 0.16 * hz(k * 977 + i, 57);
              cara(techos, [F(s0, tE, yE + 0.04), F(s1, tE, yE + 0.04), F((s0 + s1) / 2, tE + 0.04, yE - ll), F((s0 + s1) / 2, tE + 0.04, yE - ll)], cPaja.clone().multiplyScalar(0.62 + 0.14 * hz(k * 977 + i, 58)), B.T);
            }
          }
          // el fogón de tres piedras con su comal, ceniza y leña; el humo (de día) o la brasa (de noche)
          {
            const [fu, fv] = q.fogon, C = E(fu, fv, 0);
            disco(solido, E(fu, fv, 0.05), 0.65 * M, 12, cCeniza);
            for (let i = 0; i < 3; i++) { const a = TAU * i / 3 + hz(k, 17); gema(solido, ico, E(fu + 0.3 * Math.cos(a), fv + 0.3 * Math.sin(a), 0.12), 0.17 * M, 0.15 * M, 0.15 * M, a, cRoca.clone().multiplyScalar(0.85 + 0.25 * hz(k * 7 + i, 18)), 0.2); }
            disco(solido, E(fu, fv, 0.3), 0.36 * M, 14, cTinta.clone().lerp(cRoca, 0.3));
            disco(solido, E(fu, fv, 0.27), 0.36 * M, 14, cTinta, true);
            for (let i = 0; i < 3; i++) { const a = TAU * i / 3 + 0.6 + hz(k, 19); tubo(solido, E(fu + 0.15 * Math.cos(a), fv + 0.15 * Math.sin(a), 0.1), E(fu + 0.85 * Math.cos(a), fv + 0.85 * Math.sin(a), 0.07), 0.04 * M, 5, cMadera); }
            if (noche) { cono(focos, E(fu, fv, 0.08), 0.16 * M, 0.2 * M, 6, cLuz.clone().multiplyScalar(0.8)); brillos.push(E(fu, fv, 0.35)); brillos.push(E(fu, fv, 0.55)); }
            humos.push({ P: [C[0], C[1] + 0.4 * M, C[2]], f: hz(k, 20) });
          }
          // cántaros junto a la puerta y leña apilada al costado
          for (let i = 0; i < 1 + (hz(k, 21) < 0.5 ? 1 : 0); i++) {
            const [cu2, cv2] = q.loc(sD + (sD > 0 ? -0.9 : 0.9) + 0.45 * i * (sD > 0 ? -1 : 1), Wd + 0.45);
            gema(solido, ico1, E(cu2, cv2, 0.24), 0.2 * M, 0.23 * M, 0.2 * M, 0, cBarro.clone().multiplyScalar(0.9 + 0.2 * hz(k * 3 + i, 22)), 0.15);
            tubo(solido, E(cu2, cv2, 0.42), E(cu2, cv2, 0.55), 0.07 * M, 8, cBarro.clone().multiplyScalar(0.85));
          }
          if (hz(k, 23) < 0.7) for (let i = 0; i < 7; i++) {
            const row = i < 4 ? 0 : 1, col2 = row ? i - 4 : i, ss = L + 0.32 + col2 * 0.17 + row * 0.085, yy = 0.09 + row * 0.15;
            tubo(solido, F(ss, -Wd + 0.3, yy), F(ss, -Wd + 1.7, yy), 0.075 * M, 6, cMadera.clone().multiplyScalar(0.9 + 0.2 * hz(k * 5 + i, 24)));
          }
        }

        // ================= el rancho del cabildo: abierto, sobre horcones, con la mesa, las bancas y el cofre
        const BC = marco(0, 0, Math.PI / 2);            // s a lo largo de v; t hacia −u: el frente abierto mira al camino
        {
          const F = BC.F, L = RC.L, Wd = RC.W, hw = RC.H;
          cara(sendas, [F(-L - 0.5, Wd + 0.6, 0.055), F(L + 0.5, Wd + 0.6, 0.055), F(L + 0.5, -Wd - 0.6, 0.055), F(-L - 0.5, -Wd - 0.6, 0.055)], cApis.clone().multiplyScalar(0.86), null);
          for (const s of [-L + 0.3, 0, L - 0.3]) for (const t of [Wd - 0.25, -Wd + 0.25]) {
            tubo(solido, F(s, t, -0.2), F(s, t, hw - 0.12), 0.12 * M, 10, cMadera.clone().multiplyScalar(0.92 + 0.14 * hz(Math.round(s * 10 + t * 100), 25)));
            for (const d of [-1, 1]) tubo(solido, F(s, t, hw - 0.2), F(s, t + d * 0.16, hw + 0.08), 0.07 * M, 6, cMadera);
          }
          for (const t of [Wd - 0.25, -Wd + 0.25]) tubo(solido, F(-L - 0.3, t, hw), F(L + 0.3, t, hw), 0.1 * M, 8, cMadera.clone().multiplyScalar(0.95));
          for (const s of [-L + 0.3, 0, L - 0.3]) tubo(solido, F(s, Wd + 0.1, hw + 0.12), F(s, -Wd - 0.1, hw + 0.12), 0.07 * M, 6, cMadera.clone().multiplyScalar(0.85));
          techoPaja(BC, L, Wd, hw, 0.85, cPaja.clone().multiplyScalar(1.02), 7, true);
          tubo(solido, F(-L - 0.5, 0, hw + Wd * Math.tan(0.68) - 0.12), F(L + 0.5, 0, hw + Wd * Math.tan(0.68) - 0.12), 0.09 * M, 6, cMadera);
          // la mesa de tablas (0.76 m), con sus patas y travesaño
          const ML = 1.8, MW = 0.45, MH = 0.76;
          for (let i = 0; i < 4; i++) {
            const t0 = -MW + 2 * MW * i / 4, t1 = -MW + 2 * MW * (i + 1) / 4, cc = cTabla.clone().multiplyScalar(0.92 + 0.14 * hz(i, 26));
            cara(solido, [F(-ML, t0 + 0.006, MH), F(ML, t0 + 0.006, MH), F(ML, t1 - 0.006, MH), F(-ML, t1 - 0.006, MH)], cc, UP);
          }
          for (const [a, b, n] of [[[-ML, MW], [ML, MW], BC.T], [[-ML, -MW], [ML, -MW], neg(BC.T)]]) cara(solido, [F(a[0], a[1], MH - 0.06), F(b[0], b[1], MH - 0.06), F(b[0], b[1], MH), F(a[0], a[1], MH)], cTabla.clone().multiplyScalar(0.7), n);
          for (const s of [-ML, ML]) cara(solido, [F(s, -MW, MH - 0.06), F(s, MW, MH - 0.06), F(s, MW, MH), F(s, -MW, MH)], cTabla.clone().multiplyScalar(0.7), s > 0 ? BC.S : neg(BC.S));
          for (const s of [-ML + 0.12, ML - 0.12]) for (const t of [-MW + 0.08, MW - 0.08]) tubo(solido, F(s, t, 0), F(s, t, MH - 0.06), 0.035 * M, 4, cMadera);
          tubo(solido, F(-ML + 0.12, 0, 0.18), F(ML - 0.12, 0, 0.18), 0.03 * M, 4, cMadera);
          // las bancas: una tabla sobre dos caballetes a cada lado
          for (const sg of [1, -1]) {
            const t0 = sg * 0.7, t1 = sg * 1.04, BH = 0.44;
            cara(solido, [F(-1.75, t0, BH), F(1.75, t0, BH), F(1.75, t1, BH), F(-1.75, t1, BH)], cTabla.clone().multiplyScalar(0.95), UP);
            cara(solido, [F(-1.75, t1, BH - 0.05), F(1.75, t1, BH - 0.05), F(1.75, t1, BH), F(-1.75, t1, BH)], cTabla.clone().multiplyScalar(0.7), sg > 0 ? BC.T : neg(BC.T));
            for (const s of [-1.5, 1.5]) for (const d of [-0.12, 0.12]) tubo(solido, F(s, (t0 + t1) / 2 + d, 0), F(s, (t0 + t1) / 2 + d * 0.4, BH - 0.04), 0.03 * M, 4, cMadera);
          }
          // los papeles, el tintero con su pluma y la vela (de noche, encendida)
          const hojas = [[-1.55, -1.05, -0.32, 0.05, 0.04], [-1.45, -1.0, 0.0, 0.34, -0.06], [-0.5, -0.05, -0.38, -0.05, 0.08], [0.5, 0.92, 0.05, 0.36, -0.1], [1.0, 1.42, -0.36, -0.04, 0.05]];
          hojas.forEach(([s0, s1, t0, t1, g], i) => {
            const cs = Math.cos(g), sn = Math.sin(g), sm = (s0 + s1) / 2, tm = (t0 + t1) / 2, R2 = (s, t) => [sm + (s - sm) * cs - (t - tm) * sn, tm + (s - sm) * sn + (t - tm) * cs];
            const Q = [[s0, t0], [s1, t0], [s1, t1], [s0, t1]].map(([s, t]) => { const [a, b] = R2(s, t); return F(a, b, MH + 0.012 + 0.003 * i); });
            cara(papeles, Q, cPapel.clone().multiplyScalar(0.94 + 0.08 * hz(i, 27)), UP);
          });
          for (let i = 0; i < 6; i++) cara(papeles, [F(-1.5, -0.27 + i * 0.05, MH + 0.017), F(-1.12, -0.27 + i * 0.05, MH + 0.017), F(-1.12, -0.255 + i * 0.05, MH + 0.017), F(-1.5, -0.255 + i * 0.05, MH + 0.017)], cTinta.clone().lerp(cPapel, 0.45), UP);
          tubo(solido, F(-1.2, 0.2, MH), F(-1.2, 0.2, MH + 0.07), 0.04 * M, 10, cTinta);
          disco(solido, F(-1.2, 0.2, MH + 0.07), 0.04 * M, 10, cTinta);
          tubo(solido, F(-1.2, 0.2, MH + 0.05), F(-1.08, 0.27, MH + 0.3), 0.006 * M, 4, cPapel);
          gema(solido, oct, F(-1.1, 0.26, MH + 0.25), 0.03 * M, 0.08 * M, 0.012 * M, 0.5, cPapel, 0.3);
          tubo(solido, F(0.2, 0.1, MH), F(0.2, 0.1, MH + 0.015), 0.07 * M, 10, cBarro);
          tubo(solido, F(0.2, 0.1, MH + 0.015), F(0.2, 0.1, MH + 0.2), 0.025 * M, 10, cPapel.clone().multiplyScalar(0.95));
          if (noche) { gema(focos, oct, F(0.2, 0.1, MH + 0.24), 0.018 * M, 0.04 * M, 0.018 * M, 0, cLuz, 0.6); brillos.push(F(0.2, 0.1, MH + 0.26)); }
          // el cofre de madera junto a la cabecera
          const cofre = (s0, s1, t0, t1, h) => {
            cara(solido, [F(s0, t0, h), F(s1, t0, h), F(s1, t1, h), F(s0, t1, h)], cTabla.clone().multiplyScalar(0.85), UP);
            for (const [a, b, n] of [[[s0, t1], [s1, t1], BC.T], [[s1, t0], [s0, t0], neg(BC.T)], [[s1, t1], [s1, t0], BC.S], [[s0, t0], [s0, t1], neg(BC.S)]]) {
              cara(solido, [F(a[0], a[1], 0), F(b[0], b[1], 0), F(b[0], b[1], h), F(a[0], a[1], h)], cTabla.clone().multiplyScalar(0.75), n);
              cara(solido, [F(a[0], a[1], h - 0.12), F(b[0], b[1], h - 0.12), F(b[0], b[1], h - 0.09), F(a[0], a[1], h - 0.09)], cMadera.clone().multiplyScalar(0.6), n);
            }
          };
          cofre(-3.6, -2.9, -1.9, -1.35, 0.5);
          // bultos y petates de los que llegaron, al costado del rancho
          for (let i = 0; i < 5; i++) gema(solido, ico1, E(-1.6 + i * 0.75 + 0.2 * hz(i, 28), -RC.L - 1.6 - 0.4 * hz(i, 29), 0.26), (0.32 + 0.08 * hz(i, 30)) * M, 0.26 * M, 0.24 * M, hz(i, 31) * 3, cSaco.clone().multiplyScalar(0.85 + 0.2 * hz(i, 32)), 0.15);
          tubo(solido, E(1.9, -RC.L - 2.3, 0.18), E(2.0, -RC.L - 0.9, 0.18), 0.17 * M, 10, cCana.clone().multiplyScalar(1.05));
        }

        // ================= la loma y la ermita (genérica: nave enlucida con contrafuertes, espadaña, techo de teja)
        if (p.iglesia) {
          const NRl = 12, NS = 40, q0 = veg.pos.length / 3, eAng = Math.atan2(-ERMITA[1], -ERMITA[0]);
          const Pt = [];
          for (let i = 0; i <= NRl; i++) for (let j = 0; j <= NS; j++) {
            const rr = LOMA_R * i / NRl, a = TAU * j / NS, u = ERMITA[0] + rr * Math.cos(a), v = ERMITA[1] + rr * Math.sin(a);
            const h = lomaH(rr) + 0.02, P = E(u, v, h);
            const da = Math.abs(((a - eAng + Math.PI) % TAU + TAU) % TAU - Math.PI) * rr, vd = da < 0.7 && rr > 5;
            c.copy(cZacate).lerp(cApis, 0.25 * (1 - rr / LOMA_R)).multiplyScalar(0.9 + 0.16 * ruido(u, v, 3, 33));
            if (vd) c.copy(cCamino).lerp(cApis, 0.3);
            Pt.push({ P, c: c.clone(), h, u, v });
          }
          for (let i = 0; i <= NRl; i++) for (let j = 0; j <= NS; j++) {
            const id = i * (NS + 1) + j, q = Pt[id], rr = LOMA_R * i / NRl, dh = (lomaH(rr + 0.5) - lomaH(Math.max(0, rr - 0.5)));
            const a = TAU * j / NS, nx = -dh * Math.cos(a), nz = dh * Math.sin(a), ny = 1, n = Math.hypot(nx, ny, nz);
            // la normal en escena: x = este; z = −norte (las direcciones locales u, v giradas por el rumbo)
            const [wx, wy] = D2(-dh * Math.cos(a), -dh * Math.sin(a)), l = sombra(wx / n, ny / n, -wy / n);
            veg.pos.push(...q.P); veg.col.push(q.c.r * l, q.c.g * l, q.c.b * l);
          }
          for (let i = 0; i < NRl; i++) for (let j = 0; j < NS; j++) {
            const a = q0 + i * (NS + 1) + j, b = a + 1, d = a + NS + 1, e = d + 1;
            veg.idx.push(a, d, b, b, d, e);
          }
          const BE = marco(ERMITA[0], ERMITA[1], eAng, LOMA_H), F = BE.F;
          const S0 = -5.5, S1 = 5.0, Wn = 2.8, Hn = 4.0;
          cara(sendas, [F(S0 - 1.2, Wn + 1.4, 0.04), F(S1 + 3.5, Wn + 1.4, 0.04), F(S1 + 3.5, -Wn - 1.4, 0.04), F(S0 - 1.2, -Wn - 1.4, 0.04)], cApis.clone().multiplyScalar(0.95), null);
          const recto = () => Hn;
          pared(BE, "s", S0, S1, Wn, 1, recto, "enlucida", cEnlucido, 900);
          pared(BE, "s", S0, S1, -Wn, -1, recto, "enlucida", cEnlucido, 901);
          const teja = techoTeja(BE, (S1 - S0) / 2, Wn, Hn, 0.4, cTeja, 902);
          pared(BE, "t", -Wn, Wn, S0, -1, (tt) => Hn + (Wn - Math.abs(tt)) * teja.tp, "enlucida", cEnlucido, 903);
          // la fachada con la espadaña (hacia el llano): muro grueso que sube a un piñón y a la espadaña de un vano
          const FS = S1, FT = 0.45, Wf = Wn + 0.25, yP = Hn + Wf * 0.55, yE = yP + 1.9;
          const perfil = (tt) => { const a = Math.abs(tt); return a < 1.05 ? yE : Hn + (Wf - a) / (Wf - 1.05) * (yP - 0.4 - Hn); };
          pared(BE, "t", -Wf, Wf, FS + FT, 1, perfil, "enlucida", cEnlucido.clone().multiplyScalar(1.03), 904, [[-0.75, 0.75, 2.5], [-1.05, -1.05, -1], [1.05, 1.05, -1]]);
          pared(BE, "t", -Wf, Wf, FS, -1, perfil, "enlucida", cEnlucido.clone().multiplyScalar(0.95), 905, [[-1.05, -1.05, -1], [1.05, 1.05, -1]]);
          for (const sg of [1, -1]) {
            cara(muros, [F(FS, sg * Wf, -0.05), F(FS + FT, sg * Wf, -0.05), F(FS + FT, sg * Wf, Hn), F(FS, sg * Wf, Hn)], cEnlucido, sg > 0 ? BE.T : neg(BE.T));
            const pts = [[Wf, Hn], [1.05, yP - 0.4], [1.05, yE]];
            for (let i = 0; i + 1 < pts.length; i++) cara(muros, [F(FS, sg * pts[i][0], pts[i][1]), F(FS + FT, sg * pts[i][0], pts[i][1]), F(FS + FT, sg * pts[i + 1][0], pts[i + 1][1]), F(FS, sg * pts[i + 1][0], pts[i + 1][1])], cEnlucido.clone().multiplyScalar(1.05), [sg * 0.3 * BE.T[0], 1, sg * 0.3 * BE.T[2]]);
          }
          cara(muros, [F(FS, -1.05, yE), F(FS + FT, -1.05, yE), F(FS + FT, 1.05, yE), F(FS, 1.05, yE)], cEnlucido.clone().multiplyScalar(1.08), UP);
          // el vano de la campana (oscuro por ambas caras) con su campana, y una cruz chica arriba
          for (const [sx, n] of [[FS + FT + 0.02, BE.S], [FS - 0.02, neg(BE.S)]]) cara(huecos, [F(sx, -0.42, yP + 0.1), F(sx, 0.42, yP + 0.1), F(sx, 0.42, yP + 1.3), F(sx, -0.42, yP + 1.3)], cHueco, n);
          cono(solido, F(FS + FT / 2, 0, yP + 0.35), 0.28 * M, 0.55 * M, 12, cTinta.clone().lerp(cBarro, 0.35));
          tubo(solido, F(FS + FT / 2, 0, yE), F(FS + FT / 2, 0, yE + 1.1), 0.05 * M, 4, cMadera);
          tubo(solido, F(FS + FT / 2, -0.3, yE + 0.75), F(FS + FT / 2, 0.3, yE + 0.75), 0.05 * M, 4, cMadera);
          // la puerta (de noche, encendida) y el óculo
          const pr = noche;
          cara(pr ? focos : huecos, [F(FS + FT + 0.02, -0.75, 0), F(FS + FT + 0.02, 0.75, 0), F(FS + FT + 0.02, 0.75, 2.5), F(FS + FT + 0.02, -0.75, 2.5)], pr ? cLuz.clone().multiplyScalar(0.6) : cHueco, BE.S);
          if (pr) brillos.push(F(FS + FT + 0.8, 0, 1.2));
          cara(pr ? focos : huecos, [F(FS + FT + 0.02, -0.3, 3.1), F(FS + FT + 0.02, 0.3, 3.1), F(FS + FT + 0.02, 0.3, 3.7), F(FS + FT + 0.02, -0.3, 3.7)], pr ? cLuz.clone().multiplyScalar(0.5) : cHueco, BE.S);
          tubo(solido, F(FS + FT + 0.06, -0.85, 2.55), F(FS + FT + 0.06, 0.85, 2.55), 0.06 * M, 4, cZocalo);
          // contrafuertes y ventanas altas de la nave
          for (const s of [-3.0, 0.4]) for (const sg of [1, -1]) {
            const t0 = sg * Wn, t1 = sg * (Wn + 0.6);
            cara(muros, [F(s - 0.3, t1, -0.05), F(s + 0.3, t1, -0.05), F(s + 0.3, t1 - sg * 0.35, 3.2), F(s - 0.3, t1 - sg * 0.35, 3.2)], cEnlucido.clone().multiplyScalar(0.96), sg > 0 ? BE.T : neg(BE.T));
            for (const ss of [s - 0.3, s + 0.3]) cara(muros, [F(ss, t0, -0.05), F(ss, t1, -0.05), F(ss, t1 - sg * 0.35, 3.2), F(ss, t0, 3.2)], cEnlucido.clone().multiplyScalar(0.88), ss > s ? BE.S : neg(BE.S));
            cara(huecos, [F(s + 1.5, sg * (Wn + 0.03), 2.6), F(s + 2.0, sg * (Wn + 0.03), 2.6), F(s + 2.0, sg * (Wn + 0.03), 3.3), F(s + 1.5, sg * (Wn + 0.03), 3.3)], pr ? cLuz.clone().multiplyScalar(0.4) : cHueco, sg > 0 ? BE.T : neg(BE.T));
          }
          for (const sg of [1, -1]) cara(solido, [F(S0 - 0.1, sg * (Wn + 0.1), -0.2), F(S1, sg * (Wn + 0.1), -0.2), F(S1, sg * (Wn + 0.1), 0.35), F(S0 - 0.1, sg * (Wn + 0.1), 0.35)], cZocalo, sg > 0 ? BE.T : neg(BE.T));
        }

        // ================= los árboles sueltos y las matas de zacate
        const arbol = (u, v, k) => {
          const h = 4.5 + 3 * hz(k, 34), R = 1.8 + 1.3 * hz(k, 35);
          tubo(veg, E(u, v, -0.2), E(u + 0.3 * (hz(k, 36) - 0.5), v, h * 0.62), 0.16 * M * (h / 6), 6, cTronco);
          for (let i = 0; i < 6; i++) {
            const a = TAU * i / 6 + hz(k, 37) * 3, d = i === 5 ? 0 : R * 0.55;
            gema(veg, ico1, E(u + d * Math.cos(a), v + d * Math.sin(a), h * 0.68 + (i === 5 ? R * 0.45 : 0.25 * R * hz(k * 7 + i, 38))),
              R * (0.62 + 0.2 * hz(k * 7 + i, 39)) * M, R * 0.5 * M, R * (0.6 + 0.2 * hz(k * 7 + i, 40)) * M, a, cCopa.clone().multiplyScalar(0.82 + 0.3 * hz(k * 7 + i, 41)), 0.15);
          }
        };
        ARBOLES.forEach(([u, v], i) => arbol(u + (hz(i, 42) - 0.5) * 4, v + (hz(i, 43) - 0.5) * 4, 600 + i));
        {
          let n = 0;
          for (let i = 0; i < 1400 && n < 560; i++) {
            const rr = 9 + 78 * Math.sqrt(hz(i, 44)), a = TAU * hz(i, 45), u = rr * Math.cos(a), v = rr * Math.sin(a);
            if (ruido(u, v, 11, 3) < 0.35 - 0.15 * lisa(20, 60, rr)) continue;
            if (Math.abs(u) < RC.W + 3 && Math.abs(v) < RC.L + 3.5) continue;
            if (ranchos.some((q) => Math.hypot(u - q.cu, v - q.cv) < Math.max(q.L, q.Wd) + 3.6) || ranchos.some((q) => Math.hypot(u - q.fogon[0], v - q.fogon[1]) < 1.8)) continue;
            if (dPol(u, v, CAMINO) < 2.8 || veredas.some((pts) => dPol(u, v, pts) < 1.2)) continue;
            if (p.iglesia && Math.hypot(u - ERMITA[0], v - ERMITA[1]) < LOMA_R + 1) continue;
            gema(veg, oct, E(u, v, 0.12), (0.3 + 0.25 * hz(i, 46)) * M, (0.3 + 0.3 * hz(i, 47)) * M, (0.3 + 0.2 * hz(i, 48)) * M, hz(i, 49) * 3, cMata.clone().multiplyScalar(0.8 + 0.35 * hz(i, 50)), 0.25);
            n++;
          }
        }

        // ================= las mallas fijas
        poner(suelo, { desfase: 2 }, 2);
        poner(sendas, { desfase: 3 }, 2);
        poner(muros, {}, 3);
        poner(techos, {}, 3);
        poner(solido, { desfase: 1 }, 3);
        poner(veg, {}, 3);
        poner(huecos, { desfase: 2 }, 3);
        poner(papeles, { desfase: 4 }, 4);
        const matFoc = poner(focos, { desfase: 3 }, 4); if (matFoc) matFoc.uniforms.uBrillo.value = noche ? 1.7 : 1;

        // ================= lo que se mueve en shaders: el brillo de las luces (tiembla) y el humo de los fogones
        const uPx = { value: 1 }, uT = { value: 0 };
        if (brillos.length) {
          const g = new THREE.BufferGeometry(), pos = new Float32Array(brillos.length * 3), fa = new Float32Array(brillos.length);
          brillos.forEach((b, i) => { pos.set(b, i * 3); fa[i] = hz(i, 140); });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 1));
          const mB = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uTam: { value: 3.0 * M }, cA: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "uniform float uPx, uTam, uT; attribute float aF; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(uTam * uPx / max(1e-3, -mv.z), 1.5, 34.0); vA = 0.8 + 0.12 * sin(uT * 7.3 + aF * 40.0) + 0.08 * sin(uT * 2.9 + aF * 17.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.5 * vA * exp(-r * r * 4.5); gl_FragColor = vec4(srgb(cA) * a, a); }" });
          const m = new THREE.Points(g, mB); m.frustumCulled = false; m.renderOrder = 9; scene.add(m);
        }
        if (humos.length) {
          const NPh = 8, g = new THREE.BufferGeometry(), pos = new Float32Array(humos.length * NPh * 3), fa = new Float32Array(humos.length * NPh * 2);
          humos.forEach((h, i) => { for (let j = 0; j < NPh; j++) { pos.set(h.P, (i * NPh + j) * 3); fa[(i * NPh + j) * 2] = h.f; fa[(i * NPh + j) * 2 + 1] = j / NPh; } });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 2));
          const vi = D2(Math.cos(2.2), Math.sin(2.2));
          const mH = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, uV: { value: new THREE.Vector2(vi[0], -vi[1]) }, cA: { value: cHumo.clone() }, uK: { value: noche ? 0.14 : 0.42 } },
            transparent: true, depthWrite: false,
            vertexShader: "uniform float uPx, uT, uM; uniform vec2 uV; attribute vec2 aF; varying float vA; void main(){ float a = fract(uT / 7.0 + aF.x + aF.y); vec3 p = position + vec3(uV.x * a * a * 5.0, a * 7.0, uV.y * a * a * 5.0) * uM; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp((0.5 + 2.4 * a) * uM * uPx / max(1e-3, -mv.z), 1.0, 70.0); vA = (1.0 - a) * smoothstep(0.0, 0.12, a); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.6); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, mH); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }

        // ================= los animales: mula con su carga y carreta de bueyes (grupos; patas y ruedas giran con lo recorrido)
        const T = (x, y, z) => [x * M, y * M, z * M];
        const mallaDe = (acc, orden = 5) => { const mat = malla.material(); mats.push(mat); const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; return m; };
        const pata = (largo, rr, col) => { const a = malla.nueva(); tubo(a, T(0, 0.05, 0), T(0, -largo + 0.08, 0), rr * M, 6, col); tubo(a, T(0, -largo + 0.1, 0), T(0, -largo, 0), rr * 1.25 * M, 6, cTinta); return malla.geometria(a); };
        const conPatas = (g, geoP, caderas, matP) => caderas.map(([x, y, z, f]) => { const m = new THREE.Mesh(geoP, matP); m.frustumCulled = false; m.renderOrder = 5; m.position.set(...T(x, y, z)); g.add(m); return { m, f }; });
        const matPatas = malla.material(); mats.push(matPatas);
        const geoPataMula = pata(0.97, 0.055, cMula), geoPataBuey = pata(1.0, 0.085, cBuey);
        const mulaCuerpo = (() => {
          const a = malla.nueva();
          gema(a, ico1, T(0, 1.05, 0), 0.72 * M, 0.3 * M, 0.25 * M, 0, cMula, 0.1);
          tubo(a, T(0.52, 1.12, 0), T(0.86, 1.5, 0), 0.13 * M, 8, cMula);
          gema(a, ico1, T(1.0, 1.42, 0), 0.27 * M, 0.12 * M, 0.11 * M, 0, cMula, 0.1);
          gema(a, ico, T(1.2, 1.34, 0), 0.1 * M, 0.09 * M, 0.09 * M, 0, cMula.clone().multiplyScalar(0.7), 0.1);
          for (const z of [-0.06, 0.06]) cono(a, T(0.9, 1.52, z), 0.045 * M, 0.24 * M, 5, cMula);
          tubo(a, T(-0.7, 1.14, 0), T(-0.84, 0.62, 0), 0.035 * M, 5, cMula.clone().multiplyScalar(0.6));
          tubo(a, T(0.5, 1.3, 0), T(0.82, 1.62, 0), 0.04 * M, 4, cMula.clone().multiplyScalar(0.55));
          // la carga: el aparejo, dos bultos a los costados, un fardo encima y la soga
          cara(a, [T(-0.42, 1.34, -0.32), T(0.4, 1.34, -0.32), T(0.4, 1.34, 0.32), T(-0.42, 1.34, 0.32)], cTabla, UP);
          for (const z of [-0.4, 0.4]) gema(a, ico1, T(0, 1.06, z), 0.36 * M, 0.25 * M, 0.14 * M, 0, cSaco, 0.12);
          gema(a, ico1, T(0, 1.5, 0), 0.32 * M, 0.17 * M, 0.24 * M, 0, cCana.clone().multiplyScalar(1.05), 0.12);
          for (const x of [-0.12, 0.14]) tubo(a, T(x, 0.82, 0.33), T(x, 1.65, 0), 0.02 * M, 4, cMadera);
          for (const x of [-0.12, 0.14]) tubo(a, T(x, 0.82, -0.33), T(x, 1.65, 0), 0.02 * M, 4, cMadera);
          return malla.geometria(a);
        })();
        const carretaCuerpo = (() => {
          const a = malla.nueva();
          for (const z of [-0.58, 0.58]) {                                 // los dos bueyes
            gema(a, ico1, T(0, 1.15, z), 1.0 * M, 0.42 * M, 0.36 * M, 0, cBuey.clone().multiplyScalar(z > 0 ? 1 : 0.9), 0.1);
            tubo(a, T(0.75, 1.32, z), T(1.12, 1.18, z), 0.22 * M, 8, cBuey);
            gema(a, ico1, T(1.3, 1.02, z), 0.3 * M, 0.17 * M, 0.15 * M, 0, cBuey.clone().multiplyScalar(0.85), 0.1);
            for (const d of [-1, 1]) tubo(a, T(1.2, 1.16, z + d * 0.1), T(1.22, 1.44, z + d * 0.3), 0.035 * M, 5, cCuerno);
            tubo(a, T(-0.95, 1.3, z), T(-1.08, 0.6, z), 0.04 * M, 5, cBuey.clone().multiplyScalar(0.6));
          }
          tubo(a, T(1.18, 1.3, -1.05), T(1.18, 1.3, 1.05), 0.07 * M, 6, cMadera);        // el yugo
          tubo(a, T(1.15, 1.22, 0), T(-1.65, 0.95, 0), 0.06 * M, 6, cMadera);           // la lanza
          // la carreta: plataforma de tablas, estacas y baranda, y la carga
          const x0 = -4.45, x1 = -1.6, zw = 0.75, yb = 0.95;
          for (let i = 0; i < 5; i++) { const z0 = -zw + 2 * zw * i / 5, z1 = -zw + 2 * zw * (i + 1) / 5; cara(a, [T(x0, yb + 0.1, z0 + 0.01), T(x1, yb + 0.1, z0 + 0.01), T(x1, yb + 0.1, z1 - 0.01), T(x0, yb + 0.1, z1 - 0.01)], cTabla.clone().multiplyScalar(0.9 + 0.15 * hz(i, 60)), UP); }
          for (const z of [-zw, zw]) cara(a, [T(x0, yb, z), T(x1, yb, z), T(x1, yb + 0.1, z), T(x0, yb + 0.1, z)], cTabla.clone().multiplyScalar(0.7), [0, 0, z > 0 ? 1 : -1]);
          for (const z of [-zw, zw]) {
            for (let x = x0 + 0.1; x <= x1 - 0.05; x += 0.45) tubo(a, T(x, yb + 0.1, z), T(x, yb + 0.72, z), 0.03 * M, 4, cMadera);
            tubo(a, T(x0, yb + 0.72, z), T(x1, yb + 0.72, z), 0.035 * M, 4, cMadera);
          }
          for (const x of [x0, x1]) tubo(a, T(x, yb + 0.6, -zw), T(x, yb + 0.6, zw), 0.035 * M, 4, cMadera);
          tubo(a, T(-3.0, 0.65, -0.95), T(-3.0, 0.65, 0.95), 0.06 * M, 6, cMadera);   // el eje
          for (let i = 0; i < 6; i++) gema(a, ico1, T(x0 + 0.5 + (i % 3) * 0.85, yb + 0.35 + 0.22 * Math.floor(i / 3), (i % 2 ? 0.3 : -0.3) + 0.1 * hz(i, 61)), 0.38 * M, 0.2 * M, 0.26 * M, hz(i, 62), cSaco.clone().multiplyScalar(0.85 + 0.2 * hz(i, 63)), 0.12);
          tubo(a, T(-2.0, yb + 0.35, -0.6), T(-2.0, yb + 0.35, 0.6), 0.16 * M, 10, cCana);
          return malla.geometria(a);
        })();
        const geoRueda = (() => {                                       // rueda maciza de tablas: 18 lados, cubo y dos tablas a la vista
          const a = malla.nueva(), R = 0.65, w = 0.06, n = 18;
          for (let i = 0; i < n; i++) {
            const a0 = TAU * i / n, a1 = TAU * (i + 1) / n, P = (an, z) => T(R * Math.cos(an), R * Math.sin(an), z);
            cara(a, [P(a0, -w), P(a1, -w), P(a1, w), P(a0, w)], cMadera.clone().multiplyScalar(0.8), [Math.cos((a0 + a1) / 2), Math.sin((a0 + a1) / 2), 0]);
            for (const z of [-w, w]) cara(a, [T(0, 0, z), P(a0, z), P(a1, z), P(a1, z)], cTabla.clone().multiplyScalar(0.85 + 0.12 * (Math.floor(i / 3) % 2)), [0, 0, z]);
          }
          for (const z of [-w - 0.005, w + 0.005]) for (const d of [-0.28, 0.28]) cara(a, [T(d - 0.025, -R * 0.92, z), T(d + 0.025, -R * 0.92, z), T(d + 0.025, R * 0.92, z), T(d - 0.025, R * 0.92, z)], cMadera.clone().multiplyScalar(0.55), [0, 0, z]);
          tubo(a, T(0, 0, -0.16), T(0, 0, 0.16), 0.11 * M, 10, cMadera.clone().multiplyScalar(0.6));
          return malla.geometria(a);
        })();
        const matAn = malla.material(); mats.push(matAn);
        const ROAD = polil(CAMINO), VC = 0.95, TAUF = 1.8, TA = Math.max(0, p.llegada_s);
        const convoy = [];
        let cursor = ROAD.L - 11;
        for (let i = 0; i < clamp(p.mulas | 0, 0, 4); i++) {
          const g = new THREE.Group(), mb = new THREE.Mesh(mulaCuerpo, matAn); mb.frustumCulled = false; mb.renderOrder = 5; g.add(mb); scene.add(g);
          const patas = conPatas(g, geoPataMula, [[0.48, 0.97, -0.14, 0], [0.48, 0.97, 0.14, Math.PI], [-0.5, 0.97, -0.14, Math.PI], [-0.5, 0.97, 0.14, 0]], matPatas);
          const stop = cursor - 1.25; convoy.push({ tipo: "mula", g, patas, ruedas: [], stop, paso: 1.3, A: 0.38, fase: hz(i, 64) * TAU }); cursor = stop - 0.9 - 1.6;
        }
        for (let i = 0; i < clamp(p.carretas | 0, 0, 3); i++) {
          const g = new THREE.Group(), mb = new THREE.Mesh(carretaCuerpo, matAn); mb.frustumCulled = false; mb.renderOrder = 5; g.add(mb); scene.add(g);
          const cad = []; for (const z of [-0.58, 0.58]) cad.push([0.65, 1.0, z - 0.2, 0], [0.65, 1.0, z + 0.2, Math.PI], [-0.68, 1.0, z - 0.2, Math.PI], [-0.68, 1.0, z + 0.2, 0]);
          const patas = conPatas(g, geoPataBuey, cad, matPatas);
          const ruedas = [-0.95, 0.95].map((z) => { const m = new THREE.Mesh(geoRueda, matAn); m.frustumCulled = false; m.renderOrder = 5; m.position.set(...T(-3.0, 0.65, z)); g.add(m); return m; });
          const stop = cursor - 1.6; convoy.push({ tipo: "carreta", g, patas, ruedas, stop, paso: 1.7, A: 0.26, fase: hz(i, 65) * TAU }); cursor = stop - 4.5 - 2.0;
        }

        // ================= la gente: cabildantes sentados, el escribano de pie en la cabecera y quienes caminan
        const PG = 1.1;
        const nCab = clamp(p.cabildantes | 0, 2, 8), sentados = [];
        const lado = [Math.ceil(nCab / 2), Math.floor(nCab / 2)];
        [1, -1].forEach((sg, li) => { for (let j = 0; j < lado[li]; j++) sentados.push({ s: (j - (lado[li] - 1) / 2) * 0.82 + (sg > 0 ? 0.1 : -0.1), t: sg * 0.95, sg }); });
        const flSen = ctx.flota("persona", sentados.length, { tamano: K * PG, orden: 6, semilla: (p.semilla * 11 + np * 5) % 997, pose: { nombre: "sentado", banco: false } });
        const flEsc = ctx.flota("persona", 1, { tamano: K * PG, orden: 6, semilla: (p.semilla * 7 + np * 3 + 5) % 997, pose: { nombre: "clasificar", mesa: 0.78 } });
        const andan = [];
        const nLl = clamp(p.llegan | 0, 0, 3);
        for (let i = 0; i < nLl; i++) {
          const q = ranchos[QUIENES[i] % ranchos.length], sp = SPOTS[i], o = q.puerta;
          const m = [(o[0] + sp[0]) / 2 + (hz(i, 66) - 0.5) * 3, (o[1] + sp[1]) / 2 + (hz(i, 67) - 0.5) * 3];
          andan.push({ tipo: "cap", ru: polil([o, m, sp]), tArr: TA + 2.2 * i, v: 0.7 + 0.08 * hz(i, 68), mira: [-sp[0], -sp[1]] });
        }
        const nV = clamp(p.vecinos | 0, 0, 12), nVv = noche ? Math.ceil(nV / 2) : nV;
        for (let i = 0; i < nVv; i++) {
          const j = i % ranchos.length, quieto = i % 4 === 3;
          andan.push({ tipo: "vec", ru: polil(veredas[j]), s0: hz(i, 69), v: 0.9 + 0.35 * hz(i, 70), quieto, bulto: !quieto && i % 2 === 0, j });
        }
        convoy.forEach((it, i) => andan.push({ tipo: "arr", it, lat: it.tipo === "carreta" ? 1.25 : 0.85, ade: it.tipo === "carreta" ? 0.6 : 1.0 }));
        const flAnd = andan.length ? ctx.flota("persona", andan.length, { tamano: K * PG, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991 }) : null;
        const geoBulto = (() => { const a = malla.nueva(); gema(a, ico1, [0, 0, 0], 0.22 * M * PG, 0.28 * M * PG, 0.2 * M * PG, 0, cSaco, 0.15); tubo(a, T(0, 0.2 * PG, 0.12 * PG), T(0.2 * PG, 0.05, 0.12 * PG), 0.015 * M, 4, cMadera); return malla.geometria(a); })();
        andan.forEach((a) => { if (a.bulto) { a.mb = new THREE.Mesh(geoBulto, matAn); a.mb.frustumCulled = false; a.mb.renderOrder = 6; scene.add(a.mb); } });

        return { id: p.id, M, K, PG, W2, D2, BC, mats, uPx, uT, sentados, flSen, flEsc, andan, flAnd, convoy, ROAD, VC, TAUF, TA, ranchos };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo && !(m.uniforms.uBrillo.value > 1.5)) m.uniforms.uBrillo.value = 1 + 0.35 * kb;
        s.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.uT.value = t;
        // el convoy: dónde va cada uno (frena suave y se detiene en llegada_s), sus patas y sus ruedas
        const [dr] = falta(s.TA - t, s.VC, s.TAUF), vel = falta(s.TA - t, s.VC, s.TAUF)[1];
        const posConv = s.convoy.map((it) => {
          const sc = it.stop - dr, [u, v, du, dv] = enPol(s.ROAD, sc), [x, y] = s.W2(u, v), [dx, dy] = s.D2(du, dv);
          it.g.position.set(x, ctx.altura(x, y), -y); it.g.rotation.y = Math.atan2(dy, dx); it.g.visible = sc > 1;
          const mov = vel / s.VC;
          for (const pt of it.patas) pt.m.rotation.z = it.A * mov * Math.sin(TAU * sc / it.paso + pt.f + it.fase);
          for (const rd of it.ruedas) rd.rotation.z = -sc / 0.65;
          return { sc, u, v, du, dv };
        });
        s.sentados.forEach((q, i) => { const [x, y] = s.BC.P2(q.s, q.t), [dx, dy] = s.BC.D(0, -q.sg); s.flSen.poner(i, x, y, dx, dy, 1, 0, 0); });
        s.flSen.listo();
        { const [x, y] = s.BC.P2(-2.22, 0), [dx, dy] = s.BC.D(1, 0); s.flEsc.poner(0, x, y, dx, dy, 1, 0, 0); s.flEsc.listo(); }
        if (!s.flAnd) continue;
        s.andan.forEach((a, i) => {
          let u, v, du, dv, sp = 0;
          if (a.tipo === "cap") {
            const [fr, vv] = falta(a.tArr - t, a.v, 1.2), q = a.ru.L - fr;
            [u, v, du, dv] = enPol(a.ru, q); sp = q > 0 ? vv : 0;
            if (sp < 0.05) { const l = Math.hypot(...a.mira) || 1; du = a.mira[0] / l; dv = a.mira[1] / l; }
          } else if (a.tipo === "vec") {
            const L = a.ru.L || 1;
            if (a.quieto) {
              const f = s.ranchos[a.j].fogon, d0 = s.ranchos[a.j].puerta, l = Math.hypot(f[0] - d0[0], f[1] - d0[1]) || 1;
              u = f[0] + (d0[0] - f[0]) / l * 1.1; v = f[1] + (d0[1] - f[1]) / l * 1.1; du = (f[0] - d0[0]) / l; dv = (f[1] - d0[1]) / l;
            } else {
              const m = ((a.s0 * 2 * L + a.v * t) % (2 * L) + 2 * L) % (2 * L), q = m > L ? 2 * L - m : m, sg = m > L ? -1 : 1;
              [u, v, du, dv] = enPol(a.ru, q); du *= sg; dv *= sg; sp = a.v;
            }
          } else {
            const pc = posConv[s.convoy.indexOf(a.it)], [u0, v0, du0, dv0] = enPol(s.ROAD, pc.sc + a.ade);
            u = u0 - dv0 * a.lat; v = v0 + du0 * a.lat; du = du0; dv = dv0; sp = vel;
          }
          const [x, y] = s.W2(u, v), [dx, dy] = s.D2(du, dv);
          s.flAnd.poner(i, x, y, dx, dy, 1, 0, sp);
          if (a.mb) {
            const bob = 0.03 * Math.abs(Math.sin(t * 5.5 * a.v)), bx = x - dx * 0.24 * s.M * s.PG, by = y - dy * 0.24 * s.M * s.PG;
            a.mb.position.set(bx, ctx.altura(bx, by) + (1.22 + bob) * s.M * s.PG, -by); a.mb.rotation.y = Math.atan2(dy, dx);
          }
        });
        s.flAnd.listo();
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
