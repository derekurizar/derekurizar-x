// Pieza «aldeabarranca» (ficha: aldeabarranca.json; reglas: scripts/maqueta_tipos/aldeabarranca.py): una aldea rural
// pequeña en la falda baja de un volcán genérico, con una barranca ancha de piedra y arena gris a un lado y una carretera
// asfaltada que la cruza por un puente de concreto y pasa junto a la aldea. Sin lugar real: el trazo es ilustrativo.
// Centrada en `lugar` (la aldea) y orientada por `rumbo` (u: hacia el volcán; v: a su izquierda, el lado de la barranca).
// Todo en METROS × `tamano`.
// - EL TERRENO (la misma cuenta que aldeabarranca.py → Geo): meseta que baja a cero por fuera del recuadro, el CONO con su
//   cráter y costillas (ceniza y roca arriba, zacatal, bosque, potrero abajo), una LOMA al sur con CAFETALES en hileras y
//   árboles de sombra, y la BARRANCA: fondo plano de arena gris con piedras y bloques, paredes de roca con vetas, árboles
//   en la orilla. Una lámina cuyas columnas siguen el eje de la barranca (densas en ella, ralas en la meseta).
// - LA CARRETERA: asfalto de dos carriles con raya central discontinua y orillas a ras, hombros de grava, y el PUENTE
//   (losa, barandas de concreto con postes, pilas dobles sobre el fondo, estribos). Postes de luz junto a la aldea.
// - LA ALDEA: calles de tierra, LOTES con patio (cerca de postes y alambre o muro bajo de block), casas sencillas y mezcladas
//   (champas de lámina sobre postes, block, ladrillo) con techo de lámina acanalada (alguna oxidada), puerta y ventana;
//   patios con árbol, leña y tendedero; la ESCUELA de ladrillo con su corredor y su cancha, el SALÓN comunal de block y
//   la CISTERNA de concreto.
// - CON VIDA (seek puro): vecinos que caminan por las calles y otros que platican de pie, vehículos que van y vienen por
//   la carretera (por el puente), humo de fogón; de noche (ES.noche) ventanas, postes y faros encendidos.
// La pieza PUBLICA su relieve, sus lugares y los caminos «<id>.cauce» y «<id>.carretera» (aldeabarranca.py). Sin colores
// escritos (ctx.tonos, ctx.COL); sin texto ni marcas.
(function (MAQ) {
  const US = 820, VS = -40, HS = 480, RB = 640, RC = 0.075, Z0 = 22, UA = -600, UB = 1500, VA = -640, VB = 680, FD = 200;
  const UR = 170, UTOP = 740, TAU = 2 * Math.PI;
  const VEH = ["carro", "camion", "bus", "carro"];
  const lisoF = (a, b, x) => { const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const fase = (s) => ((s * 0.6180339887) % 1) * TAU;
  // la cuenta del terreno (espejo de aldeabarranca.py → Geo)
  const geo = (W, ph) => {
    const VB0 = 95 + W / 2;
    const plain = (u) => Z0 + 8 * lisoF(-200, 500, u);
    const cone = (u, v) => {
      const du = u - US, dv = v - VS, r = Math.hypot(du, dv), x = r / RB;
      if (x >= 1) return 0;
      const th = Math.atan2(dv, -du);
      let h = HS * Math.pow(1 - x, 1.45);
      h *= 1 + 0.05 * Math.sin(9 * th + ph) * 4 * x * (1 - x);
      h += 5 * Math.exp(-Math.pow((x - RC) / 0.025, 2));
      if (x < RC) h -= 38 * (1 - (x / RC) * (x / RC));
      return h;
    };
    const loma = (u, v) => 26 * Math.exp(-Math.pow((v + 330) / 120, 2)) * (0.75 + 0.25 * Math.sin(u / 170 + ph)) * (1 - lisoF(500, 900, u));
    const base = (u, v) => plain(u) + cone(u, v) + loma(u, v);
    const fade = (u, v) => lisoF(UA - FD, UA, u) * lisoF(UB + FD, UB, u) * lisoF(VA - FD, VA, v) * lisoF(VB + FD, VB, v);
    const va = (u) => VB0 + 30 * Math.sin(u / 210 + ph) - 150 * lisoF(350, UTOP, u);
    const hw = (u) => W / 2 * (0.18 + 0.82 * (1 - lisoF(150, UTOP, u))) * (1 + 0.12 * Math.sin(u / 90 + 2 * ph));
    const floor = (u) => { const b = base(u, va(u)), flp = 3 + 6 * lisoF(-600, 500, u);
      return b - Math.min(32, Math.max(0, b - flp)) * (1 - lisoF(UTOP - 160, UTOP, u)); };
    const mOf = (u, v) => (u > UTOP ? 99 : Math.abs(v - va(u)) / Math.max(1e-6, hw(u)));
    const carved = (u, v) => { const b = base(u, v); if (u > UTOP) return b; const pr = 1 - lisoF(0.7, 1.12, mOf(u, v)); return b + (floor(u) - b) * pr; };
    const alto = (u, v) => fade(u, v) * carved(u, v);
    const vis = (u, v) => Math.max(0, alto(u, v) - 0.6);
    const ur = (v) => UR + 18 * Math.sin(v / 260 + ph * 0.7);
    let vb = va(UR); for (let i = 0; i < 30; i++) vb = va(ur(vb));
    const hb = hw(ur(vb)), v0 = vb - hb * 1.25 - 6, v1 = vb + hb * 1.25 + 6;
    const ha = vis(ur(v0), v0) + 0.12, hbb = vis(ur(v1), v1) + 0.12;
    const hroad = (v) => (v >= v0 && v <= v1 ? ha + (hbb - ha) * (v - v0) / (v1 - v0) : vis(ur(v), v) + 0.12);
    return { VB0, base, fade, va, hw, floor, mOf, alto, vis, ur, vb, v0, v1, hroad, cone, loma };
  };

  MAQ.PIEZAS.aldeabarranca = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      const liso = lisoF;
      const neg = (d) => [-d[0], -d[1], -d[2]], UP = [0, 1, 0];
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      // ---- los tonos (todos del estilo)
      const cPasto = tonos.campo.clone(), cPasto2 = tonos.campo2.clone();
      const cBosque = tonos.verde.clone().lerp(tonos.campo2, 0.45).multiplyScalar(oscuro ? 0.95 : 0.8);
      const cTierra = lin(COL.tierra_media).lerp(tonos.arena, 0.35).multiplyScalar(oscuro ? 0.95 : 0.85);
      const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.45);
      const cGris = tonos.asfalto.clone().lerp(tonos.muro, 0.4).lerp(tonos.arena, 0.22).multiplyScalar(oscuro ? 1.1 : 0.82);
      const cGris2 = cGris.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.9);
      const cPared = cRoca.clone().lerp(lin(COL.tierra_media), 0.3).multiplyScalar(oscuro ? 0.85 : 0.62);
      const cVeta = lin(COL.tierra_alta).lerp(cGris, 0.5).multiplyScalar(oscuro ? 0.95 : 0.85);
      const cCeniza = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.55).multiplyScalar(oscuro ? 1.05 : 0.78);
      const cZacate = cPasto.clone().lerp(lin(COL.tierra_alta), 0.4).multiplyScalar(0.95);
      const cPino = tonos.verde.clone().lerp(tonos.campo2, 0.3).multiplyScalar(dia ? 0.6 : oscuro ? 1.0 : 0.75);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.5 : dia ? 0.85 : 0.95);
      const cCafe = tonos.bien.clone().lerp(tonos.verde, 0.55).multiplyScalar(oscuro ? 0.75 : dia ? 0.48 : 0.6);
      const cCafeSuelo = cTierra.clone().lerp(tonos.campo2, 0.35).multiplyScalar(0.78);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cAsf = tonos.asfalto.clone().lerp(tonos.pavimento, oscuro ? 0.22 : 0.1);
      const cRayaC = lin(ES.modo === 4 ? COL.linea : COL.luces), cRayaB = lin(ES.modo === 4 ? COL.linea : COL.costa);
      const cGrava = tonos.arena.clone().lerp(tonos.asfalto, 0.4);
      const cConc = tonos.pavimento.clone().lerp(tonos.muro, 0.35).multiplyScalar(oscuro ? 1.1 : 1.0);
      const cBlock = tonos.pavimento.clone().lerp(tonos.muro, 0.55).multiplyScalar(oscuro ? 1.05 : 0.95);
      const cLadrillo = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.55).multiplyScalar(oscuro ? 0.95 : 0.88);
      const cLamina = tonos.pavimento.clone().lerp(tonos.muro, 0.25).lerp(lin(COL.costa), 0.12).multiplyScalar(oscuro ? 1.15 : 1.02);
      const cOxido = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.6).lerp(tonos.medio, 0.15).multiplyScalar(oscuro ? 0.9 : 0.8);
      const cMortero = cBlock.clone().multiplyScalar(0.72);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.22);
      const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
      const cCalle = tonos.calle.clone().lerp(cTierra, 0.5);
      const cPatio = tonos.calle.clone().lerp(cTierra, 0.7).multiplyScalar(0.92);
      const cCancha = tonos.pavimento.clone().lerp(cConc, 0.5).multiplyScalar(oscuro ? 1.05 : 0.96);
      const cLuz = lin(COL.luces), cHumo = tonos.muro.clone().lerp(lin(COL.costa), 0.5);
      const cRopa = [tonos.medio.clone(), tonos.bien.clone().lerp(tonos.muro, 0.3), lin(COL.costa).lerp(tonos.muro, 0.3), tonos.secundario.clone().lerp(tonos.muro, 0.3)];

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
      const cono = (acc, P, r, h, seg, col) => {
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
        const K = p.tamano, M = metros(1) * K, ph = fase(p.semilla), G = geo(clamp(p.ancho_barranca_m, 20, 200), ph);
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const W2 = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W2(u, v); return [x, ctx.suelo(x, y) + h * M, -y]; };
        const Eg = (u, v, lev) => E(u, v, G.vis(u, v) + lev);           // sobre el terreno de la pieza
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const mats = [];
        const poner = (acc, op, orden) => { const mat = malla.material(op || {}); mats.push(mat); malla.poner(acc, mat, orden); return mat; };
        const nueva = () => malla.nueva();
        const AX = { u: -20, v: -20 };                                   // el centro de la aldea
        const rimS = (u) => G.va(u) - G.hw(u) * 1.12;                    // la orilla sur de la barranca (la de la aldea)
        const enCafe = [];                                                // parcelas de café (rectángulos locales)

        // ================= el terreno: filas en u, columnas que siguen el eje de la barranca
        const cols = [];
        for (let j = 0; j <= 24; j++) cols.push(["o", j / 24]);                       // sur, ralo
        for (let j = 1; j < 24; j++) cols.push(["i", -1.5 + 3 * j / 24]);              // la barranca, densa
        for (let j = 0; j <= 22; j++) cols.push(["n", j / 22]);                       // norte, ralo
        const Pt = [], Ct = [], VMIN = VA - FD - 40, VMAX = VB + FD + 40;
        for (let u = UA - FD - 30; u <= UB + FD + 30; u += 12) {
          const va = G.va(u), hw = G.hw(u), fila = [], filc = [];
          for (const [z, f] of cols) {
            let v;
            if (z === "o") v = VMIN + (va - 1.5 * hw - 0.01 - VMIN) * f;
            else if (z === "i") v = va + f * hw;
            else v = va + 1.5 * hw + 0.01 + (VMAX - va - 1.5 * hw) * f;
            const m = G.mOf(u, v), h = G.alto(u, v), fl = G.floor(u) * G.fade(u, v);
            fila.push(E(u, v, h - 0.6 + (m < 0.7 ? 0.35 * (ruido(u, v, 9, 3) - 0.5) : 0)));
            const n1 = ruido(u, v, 70, 11), n2 = ruido(u, v, 14, 12);
            const du = u - US, dv = v - VS, x = Math.hypot(du, dv) / RB;
            let c;
            if (x < 0.13) c = cCeniza.clone().lerp(cRoca, 0.35 * n2);
            else if (x < 0.3) c = cZacate.clone().lerp(cCeniza, 1 - liso(0.12, 0.24, x)).lerp(cRoca, 0.25 * n2 * (1 - liso(0.2, 0.3, x)));
            else if (x < 0.7) c = cBosque.clone().lerp(cZacate, 1 - liso(0.28, 0.36, x)).lerp(cPasto2, 0.3 * n1).lerp(cPasto, liso(0.62, 0.7, x));
            else c = cPasto.clone().lerp(cPasto2, 0.5 * n1).lerp(cTierra, 0.14 * n2);
            if (G.loma(u, v) > 8 && x >= 0.7) c.lerp(cCafeSuelo, 0.35 * liso(8, 18, G.loma(u, v)));
            const dA = Math.hypot(u - AX.u, v - AX.v);
            if (dA < 210) c.lerp(cTierra, 0.35 * (1 - liso(120, 210, dA)) * (0.6 + 0.4 * n2));
            // la barranca: fondo de arena gris con regueros; paredes de roca con vetas
            if (u <= UTOP && m < 1.2) {
              const prof = 1 - liso(0.7, 1.12, m);
              const fondo = cGris.clone().lerp(cGris2, 0.55 * ruido(u * 0.4, v, 6, 13)).lerp(cRoca, 0.2 * n2);
              const pared = cPared.clone().lerp(cVeta, 0.5 + 0.5 * Math.sin((h - fl) * 1.3 + n2 * 2)).multiplyScalar(0.85 + 0.2 * n2);
              const cb = m < 0.72 ? fondo : pared;
              c = c.lerp(cb, Math.max(prof > 0.02 ? 1 : 0, liso(1.2, 1.1, m) * 0.6));
            }
            filc.push(c.multiplyScalar(0.93 + 0.1 * n2));
          }
          Pt.push(fila); Ct.push(filc);
        }
        const tierra = nueva(); lamina(tierra, Pt, Ct);

        // ================= piedras y bloques en el fondo de la barranca, roca en las paredes
        const solido = nueva(), veg = nueva();
        for (let k = 0; k < 360; k++) {
          const u = UA - 120 + (UTOP - 60 - UA + 120) * hz(k, 20), m = (hz(k, 21) - 0.5) * 1.5, v = G.va(u) + m * G.hw(u);
          const rr = (k % 9 === 0 ? 2.2 + 2.4 * hz(k, 22) : 0.5 + 1.1 * hz(k, 22));
          gema(solido, Eg(u, v, rr * 0.18), rr * 1.25 * M, rr * 0.62 * M, rr * M, TAU * hz(k, 23), (k % 4 ? cRoca : cGris2).clone().multiplyScalar(0.72 + 0.4 * hz(k, 24)));
        }
        for (let k = 0; k < 140; k++) {
          const u = UA - 60 + (UTOP - 80 - UA) * hz(k, 25), sg = hz(k, 26) < 0.5 ? 1 : -1, m = 0.8 + 0.25 * hz(k, 27), v = G.va(u) + sg * m * G.hw(u);
          const rr = 1.2 + 2.0 * hz(k, 28);
          gema(solido, Eg(u, v, 0), rr * 1.4 * M, rr * 0.9 * M, rr * M, TAU * hz(k, 29), cPared.clone().multiplyScalar(0.7 + 0.35 * hz(k, 30)));
        }

        // ================= árboles
        const pino = (P, al, k) => {
          tubo(veg, [P[0], P[1] - 0.4 * M, P[2]], [P[0], P[1] + al * 0.35 * M, P[2]], 0.035 * al * M, 4, cTronco);
          for (let j = 0; j < 2; j++) cono(veg, [P[0], P[1] + al * (0.25 + 0.3 * j) * M, P[2]], al * (0.3 - 0.09 * j) * M, al * (0.5 - 0.08 * j) * M, 6,
            cPino.clone().multiplyScalar(0.88 + 0.2 * hz(k, 40 + j)));
        };
        const frondoso = (P, al, k) => {
          tubo(veg, [P[0], P[1] - 0.4 * M, P[2]], [P[0], P[1] + al * 0.6 * M, P[2]], 0.04 * al * M, 5, cTronco);
          for (let j = 0; j < 3; j++) { const a = TAU * hz(k, 50 + j), rr = j ? al * 0.2 : 0;
            gema(veg, [P[0] + Math.cos(a) * rr * M, P[1] + al * (0.74 - 0.08 * j) * M, P[2] + Math.sin(a) * rr * M], al * 0.32 * M, al * 0.24 * M, al * 0.3 * M, a,
              cCopa.clone().multiplyScalar(0.82 + 0.28 * hz(k, 53 + j))); }
        };
        const sombraCafe = (P, al, k) => {                          // árbol de sombra del cafetal: tronco alto, copa ancha y rala
          tubo(veg, [P[0], P[1] - 0.3 * M, P[2]], [P[0], P[1] + al * 0.7 * M, P[2]], 0.03 * al * M, 5, cTronco);
          for (let j = 0; j < 3; j++) { const a = TAU * (j / 3 + hz(k, 60));
            gema(veg, [P[0] + Math.cos(a) * al * 0.22 * M, P[1] + al * 0.82 * M, P[2] + Math.sin(a) * al * 0.22 * M], al * 0.3 * M, al * 0.12 * M, al * 0.26 * M, a,
              cCopa.clone().lerp(cPasto2, 0.2).multiplyScalar(0.86 + 0.24 * hz(k, 61 + j))); }
        };
        // el bosque de la falda media del cono
        let nArb = 0;
        for (let k = 0; k < 3000 && nArb < 420; k++) {
          const x = 0.3 + 0.42 * Math.sqrt(hz(k, 70)), th = -Math.PI + TAU * hz(k, 71);
          const u = US - x * RB * Math.cos(th), v = VS + x * RB * Math.sin(th);
          if (G.mOf(u, v) < 1.4 || ruido(u, v, 60, 72) < 0.35 || hz(k, 73) > 0.8) continue;
          const al = 12 + 9 * hz(k, 74), P = Eg(u, v, 0);
          if (x < 0.5 || hz(k, 75) < 0.3) pino(P, al, k); else frondoso(P, al * 0.9, k);
          nArb++;
        }
        // árboles en la orilla de la barranca y sueltos por la meseta (no en la aldea, ni en la carretera)
        for (let k = 0; k < 220; k++) {
          const u = UA + (UTOP - 200 - UA) * hz(k, 80), sg = hz(k, 81) < 0.55 ? 1 : -1, v = G.va(u) + sg * G.hw(u) * (1.25 + 0.5 * hz(k, 82));
          if (Math.abs(u - G.ur(v)) < 14 || Math.hypot(u - AX.u, v - AX.v) < 175) continue;
          frondoso(Eg(u, v, 0), 8 + 7 * hz(k, 83), k + 500);
        }
        for (let k = 0; k < 160; k++) {
          const u = UA + (550 - UA) * hz(k, 84), v = VA + (VB - VA) * hz(k, 85);
          if (G.mOf(u, v) < 1.5 || Math.abs(u - G.ur(v)) < 16 || Math.hypot(u - AX.u, v - AX.v) < 200 || ruido(u, v, 90, 86) < 0.5) continue;
          frondoso(Eg(u, v, 0), 7 + 8 * hz(k, 87), k + 900);
        }

        // ================= el café: parcelas en hileras sobre la loma del sur, con árboles de sombra
        for (const [cu, cv, lu, lv, kk] of [[-300, -330, 150, 80, 1], [-110, -370, 120, 70, 2], [-90, -270, 110, 50, 3], [60, -330, 90, 90, 4]]) {
          enCafe.push([cu - lu / 2, cu + lu / 2, cv - lv / 2, cv + lv / 2]);
          for (let rv = cv - lv / 2; rv <= cv + lv / 2; rv += 3.6) {
            for (let ru = cu - lu / 2; ru <= cu + lu / 2; ru += 3.1) {
              const k = Math.round(ru * 7 + rv * 131 + kk * 7777);
              if (hz(k, 90) < 0.06) continue;
              const u = ru + 0.5 * (hz(k, 91) - 0.5), v = rv + 0.4 * (hz(k, 92) - 0.5), hb = 1.3 + 0.5 * hz(k, 93);
              gema(veg, Eg(u, v, hb * 0.5), 1.0 * M, hb * 0.55 * M, 0.95 * M, TAU * hz(k, 94), cCafe.clone().multiplyScalar(0.82 + 0.3 * hz(k, 95)));
            }
          }
          for (let k = 0; k < Math.round(lu * lv / 520); k++) {
            const u = cu + lu * (hz(k + kk * 100, 96) - 0.5), v = cv + lv * (hz(k + kk * 100, 97) - 0.5);
            sombraCafe(Eg(u, v, 0), 11 + 6 * hz(k + kk * 100, 98), k + kk * 100);
          }
        }

        // ================= la carretera y el puente
        const suelos = nueva(), asf = nueva(), rayas = nueva(), muros = nueva(), techos = nueva(), huecos = nueva(), focos = nueva();
        const brillos = [], humos = [];
        const RP = [];
        for (let v = VA - FD - 120; v <= VB + FD + 120; v += 6) RP.push(v);
        for (const vq of [G.v0, G.v1]) { const j = RP.findIndex((x) => Math.abs(x - vq) < 2); if (j >= 0) RP.splice(j, 1); RP.push(vq); }
        RP.sort((a, b) => a - b);
        const dirRoad = (v) => { const d = G.ur(v + 1) - G.ur(v - 1); const L = Math.hypot(d, 2); return [d / L, 2 / L]; };   // (du, dv) normalizado
        const tiraRoad = (acc, t0, t1, col, lev, raya) => {
          for (let i = 0; i + 1 < RP.length; i++) {
            const va_ = RP[i], vb_ = RP[i + 1];
            if (raya && Math.floor((va_ + 2000) / 6) % 2) continue;
            const [ta, tb] = [va_, vb_].map((v) => { const [du, dv] = dirRoad(v), nu = dv, nv = -du; return [G.ur(v), v, nu, nv, G.hroad(v)]; });
            const P = (q, t) => E(q[0] + q[2] * t, q[1] + q[3] * t, q[4] + lev);
            cara(acc, [P(ta, t0), P(ta, t1), P(tb, t1), P(tb, t0)], col, null);
          }
        };
        tiraRoad(suelos, -5.2, 5.2, cGrava, -0.02);
        tiraRoad(asf, -3.6, 3.6, cAsf, 0.04);
        tiraRoad(rayas, -0.08, 0.08, cRayaC, 0.07, true);
        tiraRoad(rayas, 3.15, 3.3, cRayaB, 0.07); tiraRoad(rayas, -3.3, -3.15, cRayaB, 0.07);
        {
          // el puente: losa, barandas, pilas y estribos (el marco: s a lo largo de la carretera en el cruce)
          const vb = G.vb, [du, dv] = dirRoad(vb), uc = G.ur(vb);
          const Fb = (s, t, y) => { const u = uc + du * s + dv * t, v = vb + dv * s - du * t; return E(u, v, y); };
          const refW = (a, b) => [a * ux - b * uy, 0, -(a * uy + b * ux)], tW = refW(dv, -du), sW = refW(du, dv), ntW = neg(tW);
          const sA = G.v0 - vb, sB = G.v1 - vb, hS = (s) => G.hroad(vb + s);
          const N = Math.max(8, Math.round((sB - sA) / 3));
          for (let i = 0; i < N; i++) {
            const s0 = sA + (sB - sA) * i / N, s1 = sA + (sB - sA) * (i + 1) / N, y0 = hS(s0), y1 = hS(s1);
            cara(muros, [Fb(s0, -5.4, y0 - 1.1), Fb(s1, -5.4, y1 - 1.1), Fb(s1, -5.4, y1), Fb(s0, -5.4, y0)], cConc.clone().multiplyScalar(0.86), ntW);
            cara(muros, [Fb(s0, 5.4, y0 - 1.1), Fb(s1, 5.4, y1 - 1.1), Fb(s1, 5.4, y1), Fb(s0, 5.4, y0)], cConc.clone().multiplyScalar(0.86), tW);
            cara(muros, [Fb(s0, -5.4, y0 - 1.1), Fb(s1, -5.4, y1 - 1.1), Fb(s1, 5.4, y1 - 1.1), Fb(s0, 5.4, y0 - 1.1)], cConc.clone().multiplyScalar(0.5), [0, -1, 0]);
            for (const sg of [1, -1]) {                                       // el bordillo y la baranda
              const t0 = sg * 4.4, t1 = sg * 5.4;
              cara(muros, [Fb(s0, t0, y0 + 0.35), Fb(s1, t0, y1 + 0.35), Fb(s1, t1, y1 + 0.35), Fb(s0, t1, y0 + 0.35)], cConc, null);
              cara(muros, [Fb(s0, t0, y0), Fb(s1, t0, y1), Fb(s1, t0, y1 + 0.35), Fb(s0, t0, y0 + 0.35)], cConc.clone().multiplyScalar(0.9), sg > 0 ? ntW : tW);
              cara(muros, [Fb(s0, sg * 4.85, y0 + 1.05), Fb(s1, sg * 4.85, y1 + 1.05), Fb(s1, sg * 5.15, y1 + 1.05), Fb(s0, sg * 5.15, y0 + 1.05)], cConc.clone().multiplyScalar(1.05), null);
              cara(muros, [Fb(s0, sg * 4.85, y0 + 0.85), Fb(s1, sg * 4.85, y1 + 0.85), Fb(s1, sg * 4.85, y1 + 1.05), Fb(s0, sg * 4.85, y0 + 1.05)], cConc.clone().multiplyScalar(0.8), sg > 0 ? ntW : tW);
              const sp = s0, yp = y0;
              tubo(muros, Fb(sp, sg * 5.0, yp + 0.3), Fb(sp, sg * 5.0, yp + 1.0), 0.13 * M, 4, cConc.clone().multiplyScalar(0.92));
            }
          }
          // las pilas: dos columnas con su cabezal, del fondo a la losa
          const span = sB - sA, npil = Math.max(1, Math.round(span / 26) - 1);
          for (let k = 1; k <= npil; k++) {
            const s = sA + span * k / (npil + 1), yTop = hS(s) - 1.1;
            for (const tc of [-2.8, 2.8]) {
              const u = uc + du * s + dv * tc, v = vb + dv * s - du * tc, yb = G.vis(u, v) - 0.4;
              if (yTop - yb > 0.8) tubo(muros, E(u, v, yb), E(u, v, yTop - 0.9), 0.75 * M, 14, cConc.clone().multiplyScalar(0.84 + 0.06 * (k % 2)));
            }
            const yC = yTop - 0.9;
            for (const [a, b] of [[[-0.9, -4.2], [0.9, -4.2]], [[0.9, 4.2], [-0.9, 4.2]]]) {
              cara(muros, [Fb(s + a[0], a[1], yC), Fb(s + b[0], b[1], yC), Fb(s + b[0], b[1], yTop), Fb(s + a[0], a[1], yTop)], cConc.clone().multiplyScalar(0.78), a[1] < 0 ? ntW : tW);
            }
            for (const ss of [-0.9, 0.9]) cara(muros, [Fb(s + ss, -4.2, yC), Fb(s + ss, 4.2, yC), Fb(s + ss, 4.2, yTop), Fb(s + ss, -4.2, yTop)], cConc.clone().multiplyScalar(0.72), ss > 0 ? sW : neg(sW));
          }
          // los estribos
          for (const [s, sg] of [[sA, 1], [sB, -1]]) {
            const y = hS(s), uu = uc + du * s, vv = vb + dv * s, yb = G.vis(uu + du * sg * 6, vv + dv * sg * 6) - 1;
            cara(muros, [Fb(s + sg * 0.2, -5.6, Math.min(yb, y - 4)), Fb(s + sg * 0.2, 5.6, Math.min(yb, y - 4)), Fb(s + sg * 0.2, 5.6, y - 0.1), Fb(s + sg * 0.2, -5.6, y - 0.1)], cConc.clone().multiplyScalar(0.7), sg > 0 ? sW : neg(sW));
          }
        }
        // postes de luz a lo largo de la carretera, junto a la aldea
        for (let v = -170; v <= 70; v += 40) {
          const [du, dv] = dirRoad(v), u = G.ur(v) - dv * 6.2, vv = v + du * 6.2, y = G.hroad(v);
          const B = E(u, vv, y - 0.3), T = E(u, vv, y + 7.5), A = E(u + dv * 1.8, vv - du * 1.8, y + 7.6);
          tubo(solido, B, T, 0.11 * M, 6, cConc.clone().multiplyScalar(0.8));
          tubo(solido, T, A, 0.06 * M, 4, cConc.clone().multiplyScalar(0.7));
          const L = E(u + dv * 1.9, vv - du * 1.9, y + 7.45);
          gema(noche ? focos : solido, L, 0.35 * M, 0.14 * M, 0.25 * M, 0, noche ? cLuz : cConc);
          if (noche) brillos.push([L[0], L[1] - 0.3 * M, L[2], 1.6]);
        }

        // ================= la aldea
        // el marco de un edificio: s a lo largo de `ang` (radianes en el plano local), t a su izquierda; y sobre el suelo del centro
        const marco = (cu, cv, ang) => {
          const a = ang + r, ax = Math.cos(a), ay = Math.sin(a), [cx, cy] = W2(cu, cv), y0 = ctx.suelo(cx, cy) + G.vis(cu, cv) * M;
          const F = (s, t, y) => [cx + (ax * s - ay * t) * M, y0 + y * M, -(cy + (ay * s + ax * t) * M)];
          const L2 = (s, t) => [cu + Math.cos(ang) * s - Math.sin(ang) * t, cv + Math.sin(ang) * s + Math.cos(ang) * t];
          return { F, L2, S: [ax, 0, -ay], T: [-ay, 0, -ax] };
        };
        const caja = (acc, B, s0, s1, t0, t1, y0, y1, col, sinTapa) => {
          const F = B.F;
          if (!sinTapa) cara(acc, [F(s0, t0, y1), F(s1, t0, y1), F(s1, t1, y1), F(s0, t1, y1)], col, UP);
          cara(acc, [F(s1, t0, y0), F(s1, t1, y0), F(s1, t1, y1), F(s1, t0, y1)], col, B.S);
          cara(acc, [F(s0, t0, y0), F(s0, t1, y0), F(s0, t1, y1), F(s0, t0, y1)], col, neg(B.S));
          cara(acc, [F(s0, t1, y0), F(s1, t1, y0), F(s1, t1, y1), F(s0, t1, y1)], col, B.T);
          cara(acc, [F(s0, t0, y0), F(s1, t0, y0), F(s1, t0, y1), F(s0, t0, y1)], col, neg(B.T));
        };
        const vano = (B, tf, lado, s0, s1, y0, y1, prendido, reja) => {
          const F = B.F, t = tf + lado * 0.04, ref = lado > 0 ? B.T : neg(B.T);
          cara(prendido ? focos : huecos, [F(s0, t, y0), F(s1, t, y0), F(s1, t, y1), F(s0, t, y1)], prendido ? cLuz : cHueco, ref);
          cara(muros, [F(s0 - 0.08, t, y0 - 0.08), F(s1 + 0.08, t, y0 - 0.08), F(s1 + 0.08, t, y0), F(s0 - 0.08, t, y0)], cConc, ref);   // el alféizar
          if (reja) for (let q = 1; q < 4; q++) { const ss = s0 + (s1 - s0) * q / 4; cara(muros, [F(ss - 0.03, t + lado * 0.02, y0), F(ss + 0.03, t + lado * 0.02, y0), F(ss + 0.03, t + lado * 0.02, y1), F(ss - 0.03, t + lado * 0.02, y1)], cMadera, ref); }
          if (prendido) brillos.push([...F((s0 + s1) / 2, tf + lado * 0.5, (y0 + y1) / 2), 1]);
        };
        // techo de lámina acanalada a un agua: baja de t1 (yA) a t0 (yB), con alero; franjas de tono alterno
        const lamTecho = (B, s0, s1, t0, t1, yA, yB, col) => {
          const F = B.F, n = Math.max(4, Math.min(16, Math.round((s1 - s0) / 0.55))), th = 0.06;
          for (let i = 0; i < n; i++) {
            const a = s0 + (s1 - s0) * i / n, b = s0 + (s1 - s0) * (i + 1) / n, cc = col.clone().multiplyScalar(i % 2 ? 0.86 : 1.02);
            cara(techos, [F(a, t0, yB + th), F(b, t0, yB + th), F(b, t1, yA + th), F(a, t1, yA + th)], cc, null);
          }
          cara(techos, [F(s0, t0, yB), F(s1, t0, yB), F(s1, t1, yA), F(s0, t1, yA)], col.clone().multiplyScalar(0.42), [0, -1, 0]);
          cara(techos, [F(s0, t0, yB), F(s1, t0, yB), F(s1, t0, yB + th), F(s0, t0, yB + th)], col.clone().multiplyScalar(0.7), neg(B.T));
          cara(techos, [F(s0, t1, yA), F(s1, t1, yA), F(s1, t1, yA + th), F(s0, t1, yA + th)], col.clone().multiplyScalar(0.7), B.T);
        };
        // techo de lámina a dos aguas (cumbrera a lo largo de s)
        const lamDos = (B, L, Wd, hw, ov, col) => {
          const rise = Wd * 0.32, yR = hw + rise;
          lamTecho(B, -L - ov, L + ov, Wd + ov, 0, yR, hw - ov * 0.32, col);
          lamTecho(B, -L - ov, L + ov, -Wd - ov, 0, yR, hw - ov * 0.32, col.clone().multiplyScalar(0.94));
          for (const ss of [L, -L]) cara(muros, [B.F(ss, -Wd, hw), B.F(ss, Wd, hw), B.F(ss, 0, yR), B.F(ss, 0, yR)], cBlock.clone().multiplyScalar(0.9), ss > 0 ? B.S : neg(B.S));
          tiras(B, L + ov, yR + 0.07, col);
          return yR;
        };
        const tiras = (B, L, y, col) => caja(techos, B, -L, L, -0.12, 0.12, y - 0.02, y + 0.1, col.clone().multiplyScalar(0.8));
        // muros de block con las juntas (líneas de mortero) en el frente y los costados
        const juntas = (B, L, Wd, H) => {
          for (let y = 0.6; y < H - 0.1; y += 0.4) for (const sg of [1, -1]) {
            cara(muros, [B.F(-L, sg * (Wd + 0.015), y), B.F(L, sg * (Wd + 0.015), y), B.F(L, sg * (Wd + 0.015), y + 0.035), B.F(-L, sg * (Wd + 0.015), y + 0.035)], cMortero, sg > 0 ? B.T : neg(B.T));
          }
        };
        const parche = (pts, col, lev) => {                             // un parche de suelo sobre el terreno de la pieza
          const P = [], C = [];
          const n = 4, [a, b, c, d] = pts;
          for (let i = 0; i <= n; i++) {
            const f = [], fc = [];
            for (let j = 0; j <= n; j++) {
              const s = i / n, t = j / n;
              const u = (a[0] * (1 - s) + b[0] * s) * (1 - t) + (d[0] * (1 - s) + c[0] * s) * t, v = (a[1] * (1 - s) + b[1] * s) * (1 - t) + (d[1] * (1 - s) + c[1] * s) * t;
              f.push(Eg(u, v, lev)); fc.push(col);
            }
            P.push(f); C.push(fc);
          }
          lamina(suelos, P, C);
        };
        const franja = (pts, w, col, lev, k) => {
          const P = [], C = [];
          for (let i = 0; i < pts.length; i++) {
            const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
            const nu = -(b[1] - a[1]) / L, nv = (b[0] - a[0]) / L, f = [], fc = [];
            for (const d of [-1, -0.5, 0, 0.5, 1]) {
              const ww = w * (1 + 0.15 * (hz(k * 53 + i, 100) - 0.5)), u = pts[i][0] + nu * d * ww, v = pts[i][1] + nv * d * ww;
              f.push(Eg(u, v, lev)); fc.push(col.clone().multiplyScalar((0.88 + 0.16 * ruido(u, v, 7, 101)) * (Math.abs(d) === 1 ? 0.92 : 1)));
            }
            P.push(f); C.push(fc);
          }
          lamina(suelos, P, C);
        };
        const dSeg = (pu, pv, a, b) => { const du = b[0] - a[0], dv = b[1] - a[1], h = clamp(((pu - a[0]) * du + (pv - a[1]) * dv) / ((du * du + dv * dv) || 1), 0, 1);
          return Math.hypot(pu - a[0] - du * h, pv - a[1] - dv * h); };
        const dPol = (pu, pv, pts) => { let m = Infinity; for (let i = 0; i + 1 < pts.length; i++) m = Math.min(m, dSeg(pu, pv, pts[i], pts[i + 1])); return m; };

        // ---- las calles de tierra (trazo genérico: una calle que sale de la carretera y tres que la cruzan)
        const linea = (a, b, w, ic) => {
          const L = Math.hypot(b[0] - a[0], b[1] - a[1]), du = (b[0] - a[0]) / L, dv = (b[1] - a[1]) / L, n = Math.ceil(L / 5), pts = [];
          for (let i = 0; i <= n; i++) { const s = L * i / n, o = 2.2 * Math.sin(s / 37 + ic * 2.1 + ph) * liso(0, 12, s) * liso(0, 12, L - s); pts.push([a[0] + du * s - dv * o, a[1] + dv * s + du * o]); }
          return { pts, w };
        };
        const calles = [
          linea([G.ur(-12) - 4, -12], [-200, -8], 6, 0),
          linea([110, -100], [-185, -96], 4.5, 1),
          linea([72, -165], [72, rimS(72) - 18], 4.5, 2),
          linea([-38, -170], [-38, rimS(-38) - 18], 4.5, 3),
          linea([-142, -160], [-142, rimS(-142) - 18], 4, 4),
        ];
        calles.forEach((c, i) => franja(c.pts, c.w / 2, cCalle, 0.05, i));
        // ---- la escuela de ladrillo (corredor y cancha), el salón comunal de block y la cisterna
        const RES = [[-6, 60, -92, -22], [-108, -72, 6, 50], [-72, -50, 22, 40]];   // [u0, u1, v0, v1] reservados
        {
          const B = marco(26, -34, 0), L = 13, Wd = 3.8, H = 3.2;
          parche([[-6, -88], [58, -88], [58, -24], [-6, -24]].map(([u, v]) => [u, v]), cPatio, 0.06);
          caja(muros, B, -L - 0.15, L + 0.15, -Wd - 0.15, Wd + 0.15, -0.3, 0.45, cConc.clone().multiplyScalar(0.85));
          caja(muros, B, -L, L, -Wd, Wd, 0.45, H, cLadrillo, true);
          for (let y = 0.75; y < H; y += 0.5) for (const sg of [1, -1]) cara(muros, [B.F(-L, sg * (Wd + 0.015), y), B.F(L, sg * (Wd + 0.015), y), B.F(L, sg * (Wd + 0.015), y + 0.04), B.F(-L, sg * (Wd + 0.015), y + 0.04)], cLadrillo.clone().multiplyScalar(0.75), sg > 0 ? B.T : neg(B.T));
          for (const ss of [-L, L]) cara(muros, [B.F(ss, -Wd, H), B.F(ss, Wd, H), B.F(ss, Wd, H + 0.84), B.F(ss, -Wd, H + 0.1)], cLadrillo, ss > 0 ? B.S : neg(B.S));
          cara(muros, [B.F(-L, Wd, H), B.F(L, Wd, H), B.F(L, Wd, H + 0.84), B.F(-L, Wd, H + 0.84)], cLadrillo, B.T);
          cara(muros, [B.F(-L, -Wd, H), B.F(L, -Wd, H), B.F(L, -Wd, H + 0.1), B.F(-L, -Wd, H + 0.1)], cLadrillo, neg(B.T));
          // tres aulas: puerta y dos ventanas cada una, al corredor (t = -Wd: hacia la cancha)
          for (let a = 0; a < 3; a++) {
            const sc = -L + (2 * L) * (a + 0.5) / 3, on = noche && hz(a, 110) < 0.5;
            vano(B, -Wd, -1, sc - 3.2, sc - 2.3, 0.45, 2.4, false);
            vano(B, -Wd, -1, sc - 1.4, sc + 0.6, 1.3, 2.5, on, true);
            vano(B, -Wd, -1, sc + 1.4, sc + 3.2, 1.3, 2.5, on, true);
            vano(B, Wd, 1, sc - 1.2, sc + 1.2, 1.5, 2.5, false, true);
          }
          // corredor con columnas y el techo de lámina que lo cubre
          caja(muros, B, -L - 0.2, L + 0.2, -Wd - 2.6, -Wd, -0.3, 0.35, cConc.clone().multiplyScalar(0.95));
          for (let q = 0; q <= 6; q++) { const ss = -L + 2 * L * q / 6; caja(muros, B, ss - 0.15, ss + 0.15, -Wd - 2.45, -Wd - 2.15, 0.35, H - 0.1, cConc); }
          lamTecho(B, -L - 0.6, L + 0.6, -Wd - 2.9, Wd + 0.6, H + 0.9, H - 0.15, cLamina);
          // la cancha de concreto con sus líneas (sin texto)
          const C = marco(26, -66, 0);
          const cP = (s, t) => C.L2(s, t);
          parche([cP(-15, -9), cP(15, -9), cP(15, 9), cP(-15, 9)], cCancha, 0.1);
          for (const [a, b, c, d] of [[-15, 15, 8.8, 9], [-15, 15, -9, -8.8], [-15, -14.8, -9, 9], [14.8, 15, -9, 9], [-0.1, 0.1, -9, 9]]) parche([cP(a, c), cP(b, c), cP(b, d), cP(a, d)], cRayaB.clone().multiplyScalar(0.8), 0.14);
          for (const ss of [-14.2, 14.2]) { tubo(solido, C.F(ss, 0, 0), C.F(ss, 0, 3.0), 0.06 * M, 6, cConc); caja(solido, C, ss - 0.05, ss + 0.05, -0.9, 0.9, 2.9, 3.9, cConc.clone().multiplyScalar(1.05)); }
        }
        {
          const B = marco(-90, 26, Math.PI / 2), L = 8, Wd = 5, H = 4.2;
          parche([[-108, 6], [-72, 6], [-72, 50], [-108, 50]], cPatio, 0.06);
          caja(muros, B, -L - 0.15, L + 0.15, -Wd - 0.15, Wd + 0.15, -0.3, 0.5, cConc.clone().multiplyScalar(0.8));
          caja(muros, B, -L, L, -Wd, Wd, 0.5, H, cBlock, true);
          juntas(B, L, Wd, H);
          lamDos(B, L, Wd, H, 0.6, cLamina.clone().multiplyScalar(0.96));
          const on = noche;
          caja(huecos, B, -L - 0.05, -L + 0.02, -1.4, 1.4, 0.5, 3.1, cHueco);
          for (const sc of [-5, -1.5, 2, 5.4]) for (const sg of [1, -1]) vano(B, sg * Wd, sg, sc - 0.8, sc + 0.8, 1.6, 2.8, on && hz(Math.round(sc * 3) + sg, 111) < 0.6, true);
          if (on) brillos.push([...B.F(-L - 1.2, 0, 2.6), 1.4]);
        }
        {
          const [x, y] = W2(-61, 31), P = [x, ctx.suelo(x, y) + G.vis(-61, 31) * M, -y], R = 3.6 * M;
          const P1 = [P[0], P[1] - 0.3 * M, P[2]], P2 = [P[0], P[1] + 2.2 * M, P[2]];
          tubo(muros, P1, P2, R, 20, cConc.clone().multiplyScalar(0.92));
          cono(techos, P2, R * 1.04, 0.5 * M, 20, cConc.clone().multiplyScalar(1.05));
          tubo(solido, [P2[0], P2[1] + 0.45 * M, P2[2]], [P2[0], P2[1] + 0.75 * M, P2[2]], 0.55 * M, 10, cConc.clone().multiplyScalar(0.7));
          const B = marco(-61, 31, 0);
          for (const tc of [-0.25, 0.25]) caja(solido, B, 3.55, 3.65, tc - 0.03, tc + 0.03, 0, 2.4, cMadera);
          for (let q = 0; q < 5; q++) caja(solido, B, 3.55, 3.68, -0.25, 0.25, 0.3 + q * 0.45, 0.35 + q * 0.45, cMadera);
          tubo(solido, B.F(-3.4, 0, 0.4), B.F(-9, 0, 0.12), 0.08 * M, 6, cConc.clone().multiplyScalar(0.6));   // el tubo
        }

        // ---- los lotes con su casa: candidatas a lo largo de las calles (y algunas sueltas); se aceptan sin encimarse
        const cand = [];
        calles.forEach((c, ic) => {
          for (let i = 1; i < c.pts.length - 1; i++) {
            const a = c.pts[i - 1], b = c.pts[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, du = (b[0] - a[0]) / L, dv = (b[1] - a[1]) / L;
            for (const lado of [1, -1]) {
              const k = ic * 1000 + i * 2 + (lado > 0 ? 0 : 1);
              if (hz(k, 120) < 0.3) continue;
              const ret = c.w / 2 + 3.6 + 3 * hz(k, 121), cu = c.pts[i][0] - dv * lado * ret, cv = c.pts[i][1] + du * lado * ret;
              cand.push({ cu, cv, ang: Math.atan2(dv, du) + (lado > 0 ? Math.PI : 0) + 0.12 * (hz(k, 122) - 0.5), k, d: Math.hypot(cu - AX.u, cv - AX.v) + 60 * hz(k, 123) });
            }
          }
        });
        for (let k = 0; k < 40; k++) {
          const rr = 120 + 90 * Math.sqrt(hz(k, 124)), a = TAU * hz(k, 125);
          cand.push({ cu: AX.u + rr * Math.cos(a), cv: AX.v + rr * Math.sin(a), ang: TAU * hz(k, 126), k: 9000 + k, d: rr + 80 * hz(k, 127) });
        }
        cand.sort((a, b) => a.d - b.d);
        const puestas = [], N_CASAS = clamp(p.casas | 0, 0, 80);
        for (const c of cand) {
          if (puestas.length >= N_CASAS) break;
          const k = c.k, kind = hz(k, 130) < 0.34 ? 0 : hz(k, 130) < 0.72 ? 1 : 2;     // 0 champa · 1 block · 2 ladrillo
          const L = kind === 0 ? 1.7 + 0.8 * hz(k, 131) : 2.6 + 1.4 * hz(k, 131), Wd = kind === 0 ? 1.6 + 0.5 * hz(k, 132) : 2.2 + 0.8 * hz(k, 132);
          const D = 8 + 9 * hz(k, 133);
          const ca = Math.cos(c.ang), sa = Math.sin(c.ang), tc = -(Wd + D) / 2;
          const ou = c.cu - sa * tc, ov = c.cv + ca * tc, rad = Math.hypot(L + 2.5, (Wd * 2 + D) / 2) + 0.8;
          if (ov + rad > rimS(ou) - 6 || Math.abs(ou - G.ur(ov)) < rad + 10) continue;
          if (RES.some(([u0, u1, v0, v1]) => ou > u0 - rad && ou < u1 + rad && ov > v0 - rad && ov < v1 + rad)) continue;
          if (enCafe.some(([u0, u1, v0, v1]) => ou > u0 - rad && ou < u1 + rad && ov > v0 - rad && ov < v1 + rad)) continue;
          if (calles.some((q) => dPol(ou, ov, q.pts) < q.w / 2 + rad * 0.82)) continue;
          if (calles.some((q) => dPol(c.cu, c.cv, q.pts) < q.w / 2 + Wd + 0.4)) continue;
          if (puestas.some((q) => Math.hypot(q.ou - ou, q.ov - ov) < q.rad + rad)) continue;
          puestas.push({ ...c, ou, ov, rad, L, Wd, D, kind });
        }
        for (const c of puestas) {
          const k = c.k, B = marco(c.cu, c.cv, c.ang), F = B.F, L = c.L, Wd = c.Wd, kind = c.kind;
          const Hw = kind === 0 ? 2.3 + 0.3 * hz(k, 140) : 2.6 + 0.4 * hz(k, 140);
          const lot = [[-L - 2.5, Wd + 0.6], [L + 2.5, Wd + 0.6], [L + 2.5, -Wd - c.D], [-L - 2.5, -Wd - c.D]];
          const lotL = lot.map(([s, t]) => B.L2(s, t));
          parche([lotL[0], lotL[1], lotL[2], lotL[3]], cPatio.clone().multiplyScalar(0.92 + 0.12 * hz(k, 141)), 0.04);
          // la casa
          const cm = (kind === 0 ? cLamina.clone().multiplyScalar(0.9) : kind === 1 ? cBlock : cLadrillo).clone().multiplyScalar(0.92 + 0.14 * hz(k, 142));
          const oxid = hz(k, 143) < 0.35, cT = (oxid ? cOxido : cLamina).clone().multiplyScalar(0.9 + 0.15 * hz(k, 144));
          if (kind === 0) {
            // champa: postes de madera, paredes de lámina acanalada (franjas verticales), techo de lámina a un agua
            for (const [s, t] of [[-L, -Wd], [L, -Wd], [L, Wd], [-L, Wd]]) caja(solido, B, s - 0.07, s + 0.07, t - 0.07, t + 0.07, -0.2, Hw + 0.3, cMadera);
            for (const [ax, sg] of [["t", 1], ["t", -1], ["s", 1], ["s", -1]]) {
              const n = Math.round((ax === "t" ? 2 * L : 2 * Wd) / 0.45);
              for (let q = 0; q < n; q++) {
                const a = -1 + 2 * q / n, b = -1 + 2 * (q + 1) / n, cc = cm.clone().multiplyScalar(q % 2 ? 0.84 : 1);
                const yT = ax === "t" ? (sg > 0 ? Hw + 0.3 : Hw - 0.3) : Hw - 0.3 + 0.6 * (b + 1) / 2;
                if (ax === "t") cara(muros, [F(a * L, sg * Wd, 0), F(b * L, sg * Wd, 0), F(b * L, sg * Wd, yT), F(a * L, sg * Wd, yT)], cc, sg > 0 ? B.T : neg(B.T));
                else cara(muros, [F(sg * L, a * Wd, 0), F(sg * L, b * Wd, 0), F(sg * L, b * Wd, yT), F(sg * L, a * Wd, yT)], cc, sg > 0 ? B.S : neg(B.S));
              }
            }
            vano(B, Wd, 1, -0.4, 0.4, 0.05, 1.9, noche && hz(k, 145) < 0.35);
            lamTecho(B, -L - 0.4, L + 0.4, -Wd - 0.5, Wd + 0.5, Hw + 0.45, Hw - 0.35, cT);
            if (hz(k, 146) < 0.55) humos.push({ P: F(-L * 0.5, -Wd - 0.3, Hw), f: hz(k, 147) });
          } else {
            caja(muros, B, -L - 0.1, L + 0.1, -Wd - 0.1, Wd + 0.1, -0.3, 0.35, cConc.clone().multiplyScalar(0.8));
            caja(muros, B, -L, L, -Wd, Wd, 0.35, Hw, cm, true);
            if (kind === 1) juntas(B, L, Wd, Hw);
            else for (let y = 0.6; y < Hw; y += 0.45) for (const sg of [1, -1]) cara(muros, [F(-L, sg * (Wd + 0.015), y), F(L, sg * (Wd + 0.015), y), F(L, sg * (Wd + 0.015), y + 0.035), F(-L, sg * (Wd + 0.015), y + 0.035)], cm.clone().multiplyScalar(0.74), sg > 0 ? B.T : neg(B.T));
            // remate de los costados bajo el techo inclinado
            for (const ss of [-L, L]) cara(muros, [F(ss, -Wd, Hw), F(ss, Wd, Hw), F(ss, Wd, Hw + 0.5), F(ss, -Wd, Hw)], cm, ss > 0 ? B.S : neg(B.S));
            cara(muros, [F(-L, Wd, Hw), F(L, Wd, Hw), F(L, Wd, Hw + 0.5), F(-L, Wd, Hw + 0.5)], cm, B.T);
            const sD = (hz(k, 148) - 0.5) * (L - 1.0), on = noche && hz(k, 149) < 0.65;
            vano(B, Wd, 1, sD - 0.45, sD + 0.45, 0.35, 2.05, false);
            const sV = sD > 0 ? sD - 1.5 : sD + 1.5;
            if (Math.abs(sV) < L - 0.5) vano(B, Wd, 1, sV - 0.5, sV + 0.5, 1.1, 1.9, on, true);
            vano(B, -Wd, -1, -0.35, 0.35, 1.2, 1.8, false);
            lamTecho(B, -L - 0.45, L + 0.45, -Wd - 0.6, Wd + 0.55, Hw + 0.6, Hw, cT);
            if (hz(k, 150) < 0.25) humos.push({ P: F(L * 0.4, -Wd - 0.2, Hw + 0.2), f: hz(k, 151) });
          }
          // la cerca del lote: postes y alambre, o muro bajo de block
          const muroBajo = hz(k, 152) < 0.35;
          for (let e = 0; e < 4; e++) {
            const [s0, t0] = lot[e], [s1, t1] = lot[(e + 1) % 4];
            if (e === 0) continue;                                           // el frente queda abierto a la calle
            const Le = Math.hypot(s1 - s0, t1 - t0), nrm = [(t1 - t0) / Le, -(s1 - s0) / Le], ref = [B.S[0] * nrm[0] + B.T[0] * nrm[1], 0, B.S[2] * nrm[0] + B.T[2] * nrm[1]];
            if (muroBajo) {
              cara(muros, [F(s0, t0, -0.1), F(s1, t1, -0.1), F(s1, t1, 1.0), F(s0, t0, 1.0)], cBlock.clone().multiplyScalar(0.92), ref);
              cara(muros, [F(s0, t0, 1.0), F(s1, t1, 1.0), F(s1 + nrm[0] * 0.15, t1 + nrm[1] * 0.15, 1.0), F(s0 + nrm[0] * 0.15, t0 + nrm[1] * 0.15, 1.0)], cConc, null);
            } else {
              const n = Math.max(1, Math.round(Le / 2.6));
              for (let q = 0; q <= n; q++) { const s = s0 + (s1 - s0) * q / n, t = t0 + (t1 - t0) * q / n; caja(solido, B, s - 0.05, s + 0.05, t - 0.05, t + 0.05, -0.1, 1.25 + 0.15 * hz(k + q, 153), cMadera); }
              for (const y of [0.55, 1.05]) cara(solido, [F(s0, t0, y), F(s1, t1, y), F(s1, t1, y + 0.03), F(s0, t0, y + 0.03)], cConc.clone().multiplyScalar(0.55), ref);
            }
          }
          // el patio: árbol (o banano), leña, tendedero
          const tB = -Wd - c.D + 2.2;
          if (hz(k, 154) < 0.6) frondoso(F(L * 0.8 * (hz(k, 155) - 0.5) * 2, tB + 0.5, 0), 5 + 4 * hz(k, 156), k + 3000);
          if (hz(k, 157) < 0.5) for (let q = 0; q < 4; q++) caja(solido, B, -L - 1.6 + q * 0.18, -L - 1.45 + q * 0.18, -Wd - 1.2, -Wd - 2.6, 0, 0.5 + 0.08 * (q % 2), cMadera.clone().multiplyScalar(0.9 + 0.2 * hz(k + q, 158)));
          if (hz(k, 159) < 0.5) {
            const t = -Wd - c.D * 0.55, s0 = -L, s1 = L;
            for (const s of [s0, s1]) caja(solido, B, s - 0.04, s + 0.04, t - 0.04, t + 0.04, 0, 1.9, cMadera);
            cara(solido, [F(s0, t, 1.8), F(s1, t, 1.8), F(s1, t, 1.83), F(s0, t, 1.83)], cConc.clone().multiplyScalar(0.5), B.T);
            const nr = 2 + Math.floor(3 * hz(k, 160));
            for (let q = 0; q < nr; q++) { const s = s0 + (s1 - s0) * (q + 0.5) / nr, w = 0.32 + 0.12 * hz(k + q, 161);
              cara(solido, [F(s - w, t, 1.15), F(s + w, t, 1.15), F(s + w, t, 1.8), F(s - w, t, 1.8)], cRopa[(k + q) % cRopa.length].clone().multiplyScalar(0.75), B.T); }
          }
        }

        // ================= las mallas fijas
        poner(tierra, { desfase: 0 }, 2);
        poner(suelos, { desfase: 3 }, 2);
        poner(asf, { desfase: 4 }, 3);
        poner(rayas, { desfase: 6 }, 3);
        poner(muros, {}, 3);
        poner(techos, {}, 3);
        poner(solido, { desfase: 1 }, 3);
        poner(veg, {}, 3);
        poner(huecos, { desfase: 2 }, 3);
        const matFoc = malla.material({ desfase: 3 }); malla.poner(focos, matFoc, 4); matFoc.uniforms.uBrillo.value = noche ? 1.7 : 1;

        // ================= lo que se mueve: brillos, humo (shaders con uT)
        const uPx = { value: 1 }, uT = { value: 0 };
        if (brillos.length) {
          const g = new THREE.BufferGeometry(), pos = new Float32Array(brillos.length * 3), fa = new Float32Array(brillos.length * 2);
          brillos.forEach((b, i) => { pos.set(b.slice(0, 3), i * 3); fa[i * 2] = hz(i, 170); fa[i * 2 + 1] = b[3] || 1; });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 2));
          const matB = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uTam: { value: 3.4 * M }, cA: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "uniform float uPx, uTam, uT; attribute vec2 aF; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(aF.y * uTam * uPx / max(1e-3, -mv.z), 1.5, 30.0); vA = 0.85 + 0.1 * sin(uT * 6.1 + aF.x * 40.0) * step(aF.y, 1.2); }",
            fragmentShader: sRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.5 * vA * exp(-r * r * 4.5); gl_FragColor = vec4(srgb(cA) * a, a); }" });
          const m = new THREE.Points(g, matB); m.frustumCulled = false; m.renderOrder = 9; scene.add(m);
        }
        if (humos.length) {
          const NPh = 7, g = new THREE.BufferGeometry(), pos = new Float32Array(humos.length * NPh * 3), fa = new Float32Array(humos.length * NPh * 2);
          humos.forEach((h, i) => { for (let j = 0; j < NPh; j++) { pos.set(h.P, (i * NPh + j) * 3); fa[(i * NPh + j) * 2] = h.f; fa[(i * NPh + j) * 2 + 1] = j / NPh; } });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 2));
          const vi = [Math.cos(r + 2.2), -Math.sin(r + 2.2)];
          const matH = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, uV: { value: new THREE.Vector2(vi[0], vi[1]) }, cA: { value: cHumo.clone() }, uK: { value: noche ? 0.16 : 0.45 } },
            transparent: true, depthWrite: false,
            vertexShader: "uniform float uPx, uT, uM; uniform vec2 uV; attribute vec2 aF; varying float vA; void main(){ float a = fract(uT / 8.0 + aF.x + aF.y); vec3 p = position + vec3(uV.x * a * a * 8.0, a * 10.0, uV.y * a * a * 8.0) * uM; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp((1.0 + 3.2 * a) * uM * uPx / max(1e-3, -mv.z), 1.0, 60.0); vA = (1.0 - a) * smoothstep(0.0, 0.15, a); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.6); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, matH); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }

        // ================= los vecinos: caminan por las calles, otros platican de pie (en pareja)
        const NP = clamp(p.personas | 0, 0, 12), npv = noche ? Math.ceil(NP / 2) : NP;
        const rutas = calles.map((c) => { const S = [0]; for (let i = 1; i < c.pts.length; i++) S.push(S[i - 1] + Math.hypot(c.pts[i][0] - c.pts[i - 1][0], c.pts[i][1] - c.pts[i - 1][1])); return { pts: c.pts, S, L: S[S.length - 1] }; });
        const charlas = [[-60, -11], [40, -12], [-30, -97], [-62, 23.5]];
        const gente = [];
        for (let i = 0; i < npv; i++) {
          if (i % 4 >= 2) {
            const ch = charlas[Math.floor(i / 4) % charlas.length], par = i % 2 ? 1 : -1;
            gente.push({ quieto: true, qu: ch[0] + par * 0.55, qv: ch[1] + 0.2 * par, du: -par, dv: 0.15 * (hz(i, 180) - 0.5) });
          } else {
            const ru = rutas[i % rutas.length];
            gente.push({ ru, s0: hz(i, 181), v: 1.0 + 0.35 * hz(i, 182), sg: hz(i, 183) < 0.5 ? 1 : -1, lado: (hz(i, 184) - 0.5) * 2.4 });
          }
        }
        const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: K, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991,
          pose: (i) => (gente[i] && gente[i].quieto ? "de_pie" : "caminar") }) : null;

        // ================= los vehículos de la carretera (van y vienen; por el puente)
        const NV = clamp(p.vehiculos | 0, 0, 4), RL = [], RV = RP.filter((v) => v >= -320 && v <= G.v1 + 160);
        { let s = 0; RL.push(0); for (let i = 1; i < RV.length; i++) { s += Math.hypot(G.ur(RV[i]) - G.ur(RV[i - 1]), RV[i] - RV[i - 1]); RL.push(s); } }
        const LT = RL[RL.length - 1], LC = LT + 60;
        const veh = [];
        for (let i = 0; i < NV; i++) {
          const fl = ctx.flota(VEH[i], 1, { tamano: K, orden: 5, luces: true, semilla: (p.semilla + i * 7) % 991,
            color: (j, vs) => vs[(i * 3 + p.semilla) % vs.length] });
          veh.push({ fl, s0: LC * ((i * 0.29 + 0.22 + 0.06 * hz(i, 190)) % 1), v: (i === 1 || i === 2 ? 9 : 12), sg: i % 2 ? -1 : 1 });
        }
        return { id: p.id, M, ux, uy, W2, mats, uPx, uT, gente, flP, veh, RV, RL, LT, LC, G };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.35 * kb;
        s.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.uT.value = t;
        const dW = (du, dv) => [du * s.ux - dv * s.uy, du * s.uy + dv * s.ux];
        if (s.flP) {
          s.gente.forEach((g, i) => {
            if (g.quieto) { const [x, y] = s.W2(g.qu, g.qv), [dx, dy] = dW(g.du, g.dv); s.flP.poner(i, x, y, dx, dy, 1, 0, 0); return; }
            const ru = g.ru, L = ru.L || 1;
            const q0 = g.s0 * L + g.v * t * g.sg, m = ((q0 % (2 * L)) + 2 * L) % (2 * L), q = m > L ? 2 * L - m : m, sg = g.sg * (m > L ? -1 : 1);
            let k = 1; while (k < ru.S.length - 1 && ru.S[k] < q) k++;
            const a = ru.pts[k - 1], bb = ru.pts[k], f = (q - ru.S[k - 1]) / Math.max(1e-6, ru.S[k] - ru.S[k - 1]);
            const Lk = Math.hypot(bb[0] - a[0], bb[1] - a[1]) || 1, tu = (bb[0] - a[0]) / Lk, tv = (bb[1] - a[1]) / Lk;
            const u = a[0] + (bb[0] - a[0]) * f - tv * g.lado * sg, v = a[1] + (bb[1] - a[1]) * f + tu * g.lado * sg;
            const [x, y] = s.W2(u, v), [dx, dy] = dW(tu * sg, tv * sg);
            s.flP.poner(i, x, y, dx, dy, 1, 0, g.v * s.M / ctx.metros(1));
          });
          s.flP.listo();
        }
        for (const c of s.veh) {
          const q = ((((c.s0 + c.v * t) % s.LC) + s.LC) % s.LC) - 30, sv = c.sg > 0 ? q : s.LT - q;
          const k = clamp(Math.min(q + 4, s.LT + 4 - q) / 8, 0, 1);
          let i = 1; while (i < s.RL.length - 1 && s.RL[i] < sv) i++;
          const f = clamp((sv - s.RL[i - 1]) / Math.max(1e-6, s.RL[i] - s.RL[i - 1]), 0, 1), vv = s.RV[i - 1] + (s.RV[i] - s.RV[i - 1]) * f;
          const d = s.G.ur(vv + 1) - s.G.ur(vv - 1), Ld = Math.hypot(d, 2), tu = d / Ld * c.sg, tv = 2 / Ld * c.sg;
          const u = s.G.ur(vv) + tv * 1.75, v = vv - tu * 1.75;                 // el carril de la derecha
          const [x, y] = s.W2(u, v), [dx, dy] = dW(tu, tv);
          c.fl.poner(0, x, y, dx, dy, k, 0, c.v * s.M / ctx.metros(1));
          c.fl.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
