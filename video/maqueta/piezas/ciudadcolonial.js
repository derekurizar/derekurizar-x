// Pieza «ciudadcolonial» (ficha: ciudadcolonial.json; reglas: scripts/maqueta_tipos/ciudadcolonial.py): una ciudad colonial
// GENÉRICA en damero alrededor de su plaza mayor, sin lugar real. Centrada en `lugar` (la fuente de la plaza) y orientada por
// `rumbo` (u: hacia el volcán del fondo; v: a su izquierda); calles a escuadra con u y v. Todo en METROS × `tamano`.
// - LA PLAZA (una manzana de 64 m sin construir, empedrada): la FUENTE al centro (pila ochavada, taza, remate y el agua que
//   cae), PUESTOS de mercado (mesas con mercancía, canastos y toldos de lona) y una carreta con sacos.
// - LOS LADOS DE LA PLAZA (solo el orden relativo, sin brújula): la CATEDRAL de tres naves (fachada con pilastras, dos torres
//   bajas, bóveda, cupulitas en las naves laterales y cúpula con tambor en el crucero) con la galería del arzobispado al lado;
//   enfrente, CASAS CON BALCONES sobre un portal de comercio; a los otros dos lados, el PALACIO y el CABILDO, con dos pisos de
//   arquería de piedra. Todos con portal y tiendas al fondo.
// - LAS MANZANAS (`manzanas`, de la plaza hacia afuera): casas de un piso de muros gruesos (zócalo, cornisa, portón con marco de
//   piedra, ventanas con reja, algunas voladizas), techo de teja a dos aguas o azotea con pretil y gárgolas; detrás, un patio
//   y a veces otra crujía; huertos con árboles al centro. Algunas manzanas tienen una IGLESIA de muros gruesos con
//   contrafuertes, atrio con tapia y cruz, espadaña o torre. Calles empedradas con su canal al centro.
// - EL VOLCÁN DE FONDO (`volcan_fondo`): un cono genérico, piramidal, con barrancas, a 1.75 km por `rumbo`.
// - CON VIDA (seek puro): gente que camina por la plaza, los portales y las calles; vendedores que atienden; un cargador que
//   baja sacos de la carreta; un carretón de mano que da la vuelta a la plaza con sus ruedas girando; el agua de la fuente;
//   humo de cocinas. De noche (ES.noche), puertas de tienda, ventanas, faroles de los puestos y la puerta de los templos
//   encendidos (puntos de luz genéricos, no un dato).
// La pieza PUBLICA sus lugares (plaza, fuente, mercado, catedral, palacio, cabildo, portal, volcan) y el camino «<id>.ronda»
// (ciudadcolonial.py). Sin colores escritos (ctx.tonos, ctx.COL); sin texto ni marcas.
(function (MAQ) {
  const BLK = 64, CALLE = 9, PASO = BLK + CALLE, H2 = BLK / 2, DF = 8, TAU = 2 * Math.PI, PI = Math.PI;
  const VU = 1750, VH = 560, VR = 950;                  // el volcán de fondo: cumbre a VU por u, alto y radio de base (maqueta)
  const RONDA = H2 + CALLE / 2 - 2.1, RR = 3.0;         // el carril de la ronda (la carreta) y el radio de sus esquinas
  // las manzanas, de la plaza hacia afuera: las cuatro que dan a la plaza primero (la misma cuenta en ciudadcolonial.py no hace falta)
  const celdas = (n, hz) => {
    const c = [];
    for (let i = -3; i <= 3; i++) for (let j = -3; j <= 3; j++) if (i || j) c.push({ i, j, d: Math.hypot(i, j) * PASO + 18 * hz(i * 31 + j + 500, 1) });
    c.sort((a, b) => a.d - b.d);
    return c.slice(0, n);
  };
  // un rectángulo de esquinas redondeadas alrededor de la plaza (u, v), en sentido antihorario: la ronda
  const ronda = (a, rc) => {
    const pts = [], q = [[a, -a], [a, a], [-a, a], [-a, -a]];
    for (let k = 0; k < 4; k++) {
      const [cu, cv] = q[k], a0 = -PI / 2 + k * PI / 2;
      const ccu = cu - Math.sign(cu) * rc, ccv = cv - Math.sign(cv) * rc;
      for (let j = 0; j <= 6; j++) { const a1 = a0 + (PI / 2) * j / 6; pts.push([ccu + rc * Math.cos(a1), ccv + rc * Math.sin(a1)]); }
    }
    pts.push(pts[0]);
    return pts;
  };
  const conS = (pts) => { const S = [0]; for (let i = 1; i < pts.length; i++) S.push(S[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return { pts, S, L: S[S.length - 1] }; };
  const enRuta = (ru, q) => {
    let k = 1; while (k < ru.S.length - 1 && ru.S[k] < q) k++;
    const a = ru.pts[k - 1], b = ru.pts[k], f = (q - ru.S[k - 1]) / Math.max(1e-6, ru.S[k] - ru.S[k - 1]), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / L, (b[1] - a[1]) / L];
  };

  MAQ.PIEZAS.ciudadcolonial = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      const liso = (a, b, x) => { const v = clamp((x - a) / (b - a), 0, 1); return v * v * (3 - 2 * v); };
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      // ---- los tonos (todos del estilo; acabados y colores genéricos)
      const cCal = tonos.muro.clone();
      const MUROS = [cCal.clone(), cCal.clone().lerp(lin(COL.tierra_alta), 0.35), cCal.clone().lerp(tonos.medio, 0.26),
        cCal.clone().lerp(tonos.mal, 0.15), cCal.clone().lerp(lin(COL.tierra_media), 0.3)];
      const cPiedra = tonos.muro.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(oscuro ? 1.0 : 0.95);
      const cPiedraL = cPiedra.clone().lerp(tonos.muro, 0.45);
      const cTeja = tonos.techo.clone().lerp(tonos.mal, dia ? 0.12 : 0.05);
      const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
      const cHierro = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.3) : tonos.asfalto.clone().lerp(tonos.linea, 0.6).multiplyScalar(0.55);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.22);
      const cEmp = tonos.calle.clone().lerp(cPiedra, 0.45), cCanal = cEmp.clone().multiplyScalar(0.72);
      const cPlaza = tonos.pavimento.clone().lerp(cPiedra, 0.25), cAcera = cPiedra.clone().lerp(tonos.pavimento, 0.3);
      const cHuerto = tonos.verde.clone().lerp(tonos.campo2, 0.4), cPatio = tonos.pavimento.clone().lerp(cPiedraL, 0.3);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.5 : dia ? 0.85 : 0.95);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cAgua = tonos.agua.clone(), cChorro = lin(COL.costa).lerp(tonos.agua, 0.3);
      const LONAS = [tonos.medio, tonos.bien, tonos.mal, lin(COL.costa), lin(COL.tierra_alta)].map((c) => c.clone().lerp(tonos.muro, 0.35));
      const FRUTA = [tonos.mal, tonos.medio, tonos.bien, lin(COL.tierra_alta)].map((c) => c.clone().multiplyScalar(0.9));
      const cSaco = lin(COL.tierra_alta).lerp(tonos.arena, 0.4).multiplyScalar(0.85), cCesto = lin(COL.tierra_alta).lerp(cMadera, 0.4);
      const cLuz = lin(COL.luces), cHumo = tonos.muro.clone().lerp(lin(COL.costa), 0.5);
      const cPasto = tonos.campo.clone(), cPasto2 = tonos.campo2.clone();
      const cBosque = tonos.verde.clone().lerp(tonos.campo2, 0.45).multiplyScalar(oscuro ? 0.95 : 0.8);
      const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.45);
      const cCeniza = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.55).multiplyScalar(oscuro ? 1.05 : 0.78);
      const cZacate = cPasto.clone().lerp(lin(COL.tierra_alta), 0.4);
      const ROPA = [tonos.mal.clone(), tonos.medio.clone(), tonos.bien.clone(), lin(COL.costa).multiplyScalar(0.85), lin(COL.tierra_alta).multiplyScalar(0.8)];

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
        const K = p.tamano, M = metros(1) * K, r = p.rumbo * PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const W2 = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W2(u, v); return [x, ctx.suelo(x, y) + h * M, -y]; };
        const mats = [];
        const poner = (acc, op, orden) => { const mat = malla.material(op || {}); mats.push(mat); malla.poner(acc, mat, orden); return mat; };
        const nueva = () => malla.nueva();
        const suelos = nueva(), muros = nueva(), techos = nueva(), solido = nueva(), veg = nueva(), huecos = nueva(), focos = nueva(), aguas = nueva();
        const brillos = [], humos = [];
        const neg = (d) => [-d[0], -d[1], -d[2]], UP = [0, 1, 0], DOWN = [0, -1, 0];
        // el marco de un edificio: s a lo largo de `ang` (radianes en el plano local), t a su izquierda; el piso, el más bajo
        // del suelo bajo su huella (ext = [medio largo, fondo]) para que nada flote
        const marco = (cu, cv, ang, ext) => {
          const a = ang + r, ax = Math.cos(a), ay = Math.sin(a), ca = Math.cos(ang), sa = Math.sin(ang), [cx, cy] = W2(cu, cv);
          let y0 = ctx.suelo(cx, cy);
          if (ext) for (const [ss, tt] of [[-ext[0], 0], [ext[0], 0], [-ext[0], -ext[1]], [ext[0], -ext[1]], [0, -ext[1]]]) {
            y0 = Math.min(y0, ctx.suelo(cx + (ax * ss - ay * tt) * M, cy + (ay * ss + ax * tt) * M));
          }
          const F = (s, t, y) => [cx + (ax * s - ay * t) * M, y0 + y * M, -(cy + (ay * s + ax * t) * M)];
          const lu = (s, t) => [cu + ca * s - sa * t, cv + sa * s + ca * t];
          return { F, lu, S: [ax, 0, -ay], T: [-ay, 0, -ax], ang, cu, cv };
        };
        const sub = (B, ds, dt) => ({ ...B, F: (s, t, y) => B.F(s + ds, t + dt, y), lu: (s, t) => B.lu(s + ds, t + dt) });
        // el mismo marco girado 90°: sus caras de t constante son las de s constante del original (s' = t, t' = −s)
        const girar = (B) => ({ ...B, F: (s, t, y) => B.F(-t, s, y), lu: (s, t) => B.lu(-t, s), S: B.T, T: [-B.S[0], -B.S[1], -B.S[2]] });
        const caja = (acc, B, s0, s1, t0, t1, y0, y1, col, sinTapa) => {
          const F = B.F;
          if (!sinTapa) cara(acc, [F(s0, t0, y1), F(s1, t0, y1), F(s1, t1, y1), F(s0, t1, y1)], col, UP);
          cara(acc, [F(s1, t0, y0), F(s1, t1, y0), F(s1, t1, y1), F(s1, t0, y1)], col, B.S);
          cara(acc, [F(s0, t0, y0), F(s0, t1, y0), F(s0, t1, y1), F(s0, t0, y1)], col, neg(B.S));
          cara(acc, [F(s0, t1, y0), F(s1, t1, y0), F(s1, t1, y1), F(s0, t1, y1)], col, B.T);
          cara(acc, [F(s0, t0, y0), F(s1, t0, y0), F(s1, t0, y1), F(s0, t0, y1)], col, neg(B.T));
        };
        // un vano (puerta, ventana) sobre la cara t = tf (lado = +1: la que mira a +T)
        const vano = (B, tf, lado, s0, s1, y0, y1, prendido, kLuz) => {
          const F = B.F, t = tf + lado * 0.04, ref = lado > 0 ? B.T : neg(B.T);
          cara(prendido ? focos : huecos, [F(s0, t, y0), F(s1, t, y0), F(s1, t, y1), F(s0, t, y1)], prendido ? cLuz.clone().multiplyScalar(kLuz || 1) : cHueco, ref);
          if (prendido) brillos.push(F((s0 + s1) / 2, tf + lado * 0.5, (y0 + y1) / 2));
        };
        // una barra delgada (reja, baranda) como una cara que mira a `ref`
        const barra = (acc, P0, P1, P2, P3, col, ref) => cara(acc, [P0, P1, P2, P3], col, ref);
        // un sólido de revolución alrededor de (s, t) con su perfil [[r, y], …] (la normal sale a la derecha del perfil)
        const torno = (acc, B, s, t, perfil, seg, col, fase) => {
          const F = B.F, a0f = fase || 0;
          for (let i = 0; i < seg; i++) {
            const a0 = a0f + TAU * i / seg, a1 = a0f + TAU * (i + 1) / seg, am = (a0 + a1) / 2;
            for (let k = 0; k + 1 < perfil.length; k++) {
              const [r0, y0] = perfil[k], [r1, y1] = perfil[k + 1], nr = y1 - y0, ny = -(r1 - r0);
              const P = (rr, yy, a) => F(s + rr * Math.cos(a), t + rr * Math.sin(a), yy);
              const ref = [Math.cos(am) * nr * B.S[0] + Math.sin(am) * nr * B.T[0], ny, Math.cos(am) * nr * B.S[2] + Math.sin(am) * nr * B.T[2]];
              cara(acc, [P(r0, y0, a0), P(r0, y0, a1), P(r1, y1, a1), P(r1, y1, a0)], col, ref);
            }
          }
        };
        const cupula = (acc, B, s, t, y0, R, H, seg, col) => {
          const pf = []; for (let j = 0; j <= 6; j++) { const f = (PI / 2) * j / 6; pf.push([Math.max(0.04, R * Math.cos(f)), y0 + H * Math.sin(f)]); }
          torno(acc, B, s, t, pf, seg, col);
        };
        const linterna = (B, s, t, y0, R) => {
          torno(muros, B, s, t, [[R, y0], [R, y0 + 1.5 * R]], 12, cCal.clone().multiplyScalar(1.02));
          for (let i = 0; i < 4; i++) { const a = TAU * i / 4 + PI / 4, P = (yy, da) => B.F(s + (R + 0.02) * Math.cos(a + da), t + (R + 0.02) * Math.sin(a + da), yy);
            cara(huecos, [P(y0 + 0.35 * R, -0.3), P(y0 + 0.35 * R, 0.3), P(y0 + 1.2 * R, 0.3), P(y0 + 1.2 * R, -0.3)], cHueco,
              [Math.cos(a) * B.S[0] + Math.sin(a) * B.T[0], 0, Math.cos(a) * B.S[2] + Math.sin(a) * B.T[2]]); }
          cupula(techos, B, s, t, y0 + 1.5 * R, R * 1.1, R * 0.9, 12, cCal.clone().multiplyScalar(0.95));
          tubo(solido, B.F(s, t, y0 + 2.3 * R), B.F(s, t, y0 + 3.3 * R), 0.07 * M, 4, cHierro);
        };
        // un techo de teja a dos aguas con la cumbrera a lo largo de s (centrado en el marco), sobre muros de ancho 2·w y alto hw
        const techo = (B, l, w, hw, ovF, ovB, col, colMuro, ovS) => {
          const F = B.F, p_ = 0.45, tp = Math.tan(p_), th = 0.2, Ls = l + (ovS == null ? 0.3 : ovS);
          const rise = w * tp, yR = hw + rise, dth = th / Math.cos(p_);
          for (const sg of [1, -1]) {
            const ov = sg > 0 ? ovF : ovB, te = sg * (w + ov), ye = hw - ov * tp;
            const cTop = col.clone().multiplyScalar(sg > 0 ? 1.0 : 0.95), cBajo = col.clone().multiplyScalar(0.45);
            const tm = te * 0.86, ym = ye + (yR - ye) * 0.14;           // la hilera del alero, más curtida
            cara(techos, [F(-Ls, te, ye + dth), F(Ls, te, ye + dth), F(Ls, tm, ym + dth), F(-Ls, tm, ym + dth)], cTop.clone().multiplyScalar(0.84), null);
            cara(techos, [F(-Ls, tm, ym + dth), F(Ls, tm, ym + dth), F(Ls, 0, yR + dth), F(-Ls, 0, yR + dth)], cTop, null);
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, 0, yR), F(-Ls, 0, yR)], cBajo, DOWN);
            cara(techos, [F(-Ls, te, ye), F(Ls, te, ye), F(Ls, te, ye + dth), F(-Ls, te, ye + dth)], col.clone().multiplyScalar(0.7), sg > 0 ? B.T : neg(B.T));
            for (const ss of [Ls, -Ls]) cara(techos, [F(ss, te, ye), F(ss, 0, yR), F(ss, 0, yR + dth), F(ss, te, ye + dth)], col.clone().multiplyScalar(0.62), ss > 0 ? B.S : neg(B.S));
          }
          for (const ss of [l, -l]) cara(muros, [F(ss, -w, hw), F(ss, w, hw), F(ss, 0, yR), F(ss, 0, yR)], colMuro, ss > 0 ? B.S : neg(B.S));
          tubo(techos, F(-Ls, 0, yR + dth), F(Ls, 0, yR + dth), 0.16 * M, 6, col.clone().multiplyScalar(0.78));
          return yR + dth;
        };
        // una bóveda de cañón a lo largo de t (de t0 a t1), de medio ancho w y flecha f, sobre muros de alto y
        const boveda = (B, s0c, w, t0, t1, y, f, col) => {
          const F = B.F, N = 12;
          for (let i = 0; i < N; i++) {
            const a0 = PI * i / N, a1 = PI * (i + 1) / N, am = (a0 + a1) / 2;
            const P = (a, t) => F(s0c + w * Math.cos(a), t, y + f * Math.sin(a));
            const ref = [Math.cos(am) * B.S[0], Math.sin(am), Math.cos(am) * B.S[2]];
            cara(techos, [P(a0, t0), P(a1, t0), P(a1, t1), P(a0, t1)], col.clone().multiplyScalar(0.97 + 0.03 * (i % 2)), ref);
          }
          for (const tt of [t0, t1]) for (let i = 0; i < N; i++) {          // los tímpanos de los extremos
            const a0 = PI * i / N, a1 = PI * (i + 1) / N, P = (a) => F(s0c + w * Math.cos(a), tt, y + f * Math.sin(a));
            cara(muros, [P(a0), P(a1), F(s0c, tt, y), F(s0c, tt, y)], col.clone().multiplyScalar(0.9), tt === t1 ? B.T : neg(B.T));
          }
        };
        // un parche de suelo (rectángulo del marco o polígono local) posado sobre el suelo del mundo
        const parche = (pts, col, lev) => malla.poligono(suelos, pts.flatMap(([u, v]) => W2(u, v)), lev * M, col);
        const parcheB = (B, s0, s1, t0, t1, col, lev) => parche([B.lu(s0, t0), B.lu(s1, t0), B.lu(s1, t1), B.lu(s0, t1)], col, lev);
        // losas: un rectángulo (u, v) en piezas con su tono cada una (el empedrado)
        const losas = (u0, v0, u1, v1, lu_, lv_, col, var_, lev, k) => {
          const nu = Math.max(1, Math.round((u1 - u0) / lu_)), nv = Math.max(1, Math.round((v1 - v0) / lv_));
          for (let a = 0; a < nu; a++) for (let b = 0; b < nv; b++) {
            const ua = u0 + (u1 - u0) * a / nu, ub = u0 + (u1 - u0) * (a + 1) / nu, va = v0 + (v1 - v0) * b / nv, vb = v0 + (v1 - v0) * (b + 1) / nv;
            const c = col.clone().multiplyScalar(1 - var_ / 2 + var_ * hz(k * 7919 + a * 131 + b, 70));
            cara(suelos, [E(ua, va, lev), E(ub, va, lev), E(ub, vb, lev), E(ua, vb, lev)], c, null);
          }
        };
        const rectB = (B, s0, s1, t0, t1) => { const a = B.lu(s0, t0), b = B.lu(s1, t1); return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])]; };
        const cruza = (A, B, m) => { const g = m || 0; return A[0] < B[2] - g && B[0] < A[2] - g && A[1] < B[3] - g && B[1] < A[3] - g; };
        const frondoso = (P, alto_, k) => {
          tubo(veg, [P[0], P[1] - 0.3 * M, P[2]], [P[0], P[1] + alto_ * 0.6 * M, P[2]], 0.045 * alto_ * M, 6, cTronco);
          for (let j = 0; j < 3; j++) { const a = TAU * hz(k, 30 + j), rr = j ? alto_ * 0.2 : 0;
            gema(veg, [P[0] + Math.cos(a) * rr * M, P[1] + alto_ * (0.74 - 0.08 * j) * M, P[2] + Math.sin(a) * rr * M], alto_ * 0.32 * M, alto_ * 0.24 * M, alto_ * 0.3 * M, a,
              cCopa.clone().multiplyScalar(0.85 + 0.25 * hz(k, 32 + j))); }
        };

        // ================= la arquería: pilares con basa y capitel, arcos de medio punto con su rosca, enjutas y cornisa
        const arcada = (B, s0, s1, nb, ya, yb, TH, pw, col, colB, antepecho) => {
          const F = B.F, L = s1 - s0, ow = (L - (nb + 1) * pw) / nb, ra = ow / 2, ys = Math.min(ya + (yb - ya) * 0.55, yb - ra - 0.6), NA = 12;
          for (let k = 1; k < nb; k++) {
            const sk = s0 + pw / 2 + k * (ow + pw);
            caja(muros, B, sk - pw / 2, sk + pw / 2, -TH, 0, ya, yb, col, true);
            caja(solido, B, sk - pw / 2 - 0.12, sk + pw / 2 + 0.12, -TH - 0.12, 0.12, ya, ya + 0.4, colB);
            caja(solido, B, sk - pw / 2 - 0.1, sk + pw / 2 + 0.1, -TH - 0.1, 0.1, ys - 0.3, ys, colB);
          }
          const centros = [];
          for (let k = 0; k < nb; k++) {
            const sc = s0 + pw + ow / 2 + k * (ow + pw);
            centros.push(sc);
            for (let i = 0; i < NA; i++) {
              const a0 = PI * i / NA, a1 = PI * (i + 1) / NA, am = (a0 + a1) / 2;
              const p0 = [sc + ra * Math.cos(a0), ys + ra * Math.sin(a0)], p1 = [sc + ra * Math.cos(a1), ys + ra * Math.sin(a1)];
              cara(muros, [F(p0[0], 0, p0[1]), F(p1[0], 0, p1[1]), F(p1[0], 0, yb), F(p0[0], 0, yb)], col, B.T);
              cara(muros, [F(p0[0], -TH, p0[1]), F(p1[0], -TH, p1[1]), F(p1[0], -TH, yb), F(p0[0], -TH, yb)], col.clone().multiplyScalar(0.85), neg(B.T));
              const ref = [-Math.cos(am) * B.S[0], -Math.sin(am), -Math.cos(am) * B.S[2]];
              cara(muros, [F(p0[0], 0, p0[1]), F(p1[0], 0, p1[1]), F(p1[0], -TH, p1[1]), F(p0[0], -TH, p0[1])], col.clone().multiplyScalar(0.75), ref);
              // la rosca: una banda de piedra alrededor del arco, un poco adelante
              const q0 = [sc + (ra + 0.32) * Math.cos(a0), ys + (ra + 0.32) * Math.sin(a0)], q1 = [sc + (ra + 0.32) * Math.cos(a1), ys + (ra + 0.32) * Math.sin(a1)];
              cara(solido, [F(p0[0], 0.05, p0[1]), F(p1[0], 0.05, p1[1]), F(q1[0], 0.05, q1[1]), F(q0[0], 0.05, q0[1])], colB, B.T);
            }
            if (antepecho) {
              caja(muros, B, sc - ra, sc + ra, -TH * 0.7, -0.1, ya, ya + 1.0, col.clone().multiplyScalar(0.95));
              caja(solido, B, sc - ra - 0.05, sc + ra + 0.05, -TH * 0.7 - 0.08, -0.02, ya + 1.0, ya + 1.12, colB);
            }
          }
          return centros;
        };
        // un edificio con portal: arquería al frente (t = 0) y el cuerpo detrás; pisos: [{h, arcos, antepecho, balcones}]
        const edificio = (Bs, s0, s1, D, nb, pisos, cm, k, op) => {
          op = op || {};
          const l = (s1 - s0) / 2, [cu, cv] = Bs.lu((s0 + s1) / 2, 0), B = marco(cu, cv, Bs.ang, [l, D]), F = B.F;
          const PD = 4.6, TH = 0.85, pw = op.pw || 1.25, Ht = pisos.reduce((a, q) => a + q.h, 0);
          caja(muros, B, -l, l, -D, -PD, -0.4, Ht, cm, true);
          for (const sg of [-1, 1]) caja(muros, B, sg > 0 ? l - pw : -l, sg > 0 ? l : -l + pw, -PD, 0, -0.4, Ht, cm.clone().lerp(cPiedra, 0.35), true);
          caja(solido, B, -l - 0.1, l + 0.1, -D - 0.1, 0.15, -0.4, 0.3, cPiedra.clone().multiplyScalar(0.9));        // el basamento
          parcheB(B, -l + pw, l - pw, -PD, -0.05, cPiedraL.clone().multiplyScalar(0.95), 0.34);
          let y = 0;
          pisos.forEach((q, ip) => {
            const ya = y, yb = y + q.h;
            let centros;
            if (q.arcos) centros = arcada(B, -l, l, nb, ya, yb, TH, pw, cPiedra, cPiedraL, q.antepecho);
            else {
              const paso = (2 * l - 2 * pw) / nb; centros = [];
              for (let b = 0; b < nb; b++) {
                const sa = -l + pw + b * paso, sc = sa + paso / 2, cB = op.colores ? op.colores[b] : cm;
                centros.push(sc);
                caja(muros, B, sa, sa + paso, -TH, 0, ya, yb, cB, true);
                if (q.balcones) {                                                     // balcón de madera sobre el portal
                  const hp = Math.min(2.7, q.h - 1.0), lit = noche && hz(k * 50 + b, 3) < 0.5;
                  vano(B, 0, 1, sc - 0.6, sc + 0.6, ya + 0.2, ya + hp, lit, 0.8);
                  caja(solido, B, sc - 1.15, sc + 1.15, 0, 0.8, ya + 0.02, ya + 0.2, cMadera);
                  for (let j = 0; j <= 8; j++) { const x = sc - 1.1 + 2.2 * j / 8;
                    barra(solido, F(x - 0.035, 0.76, ya + 0.2), F(x + 0.035, 0.76, ya + 0.2), F(x + 0.035, 0.76, ya + 1.15), F(x - 0.035, 0.76, ya + 1.15), cMadera, B.T); }
                  for (const sg of [-1, 1]) for (const tt of [0.25, 0.5]) barra(solido, F(sc + sg * 1.12, tt - 0.035, ya + 0.2), F(sc + sg * 1.12, tt + 0.035, ya + 0.2),
                    F(sc + sg * 1.12, tt + 0.035, ya + 1.15), F(sc + sg * 1.12, tt - 0.035, ya + 1.15), cMadera, sg > 0 ? B.S : neg(B.S));
                  caja(solido, B, sc - 1.15, sc + 1.15, 0.0, 0.82, ya + 1.15, ya + 1.25, cMadera);
                  caja(solido, B, sc - 1.0, sc + 1.0, 0, 0.5, ya + hp + 0.25, ya + hp + 0.4, cPiedraL);       // el guardapolvo
                } else {
                  vano(B, 0, 1, sc - 0.6, sc + 0.6, ya + 1.0, ya + q.h - 1.2, noche && hz(k * 50 + b, 4) < 0.45, 0.8);
                }
              }
            }
            caja(muros, B, -l - 0.15, l + 0.15, -TH - 0.15, 0.24, yb - 0.42, yb, cPiedraL);                // la cornisa del piso
            cara(muros, [F(-l + pw, -TH, yb - 0.42), F(l - pw, -TH, yb - 0.42), F(l - pw, -PD, yb - 0.42), F(-l + pw, -PD, yb - 0.42)], cm.clone().multiplyScalar(0.5), DOWN);
            if (ip > 0 && q.arcos) cara(muros, [F(-l + pw, -TH, ya + 0.01), F(l - pw, -TH, ya + 0.01), F(l - pw, -PD, ya + 0.01), F(-l + pw, -PD, ya + 0.01)], cPiedraL.clone().multiplyScalar(0.92), UP);
            if (q.arcos) {                                                            // el muro del fondo del portal: puertas de tienda
              for (const [b, sc] of centros.entries()) {
                const hD = Math.min(3.3, q.h - 1.3), lit = noche && hz(k * 50 + b, ip ? 5 : 6) < (ip ? 0.45 : 0.78);
                vano(B, -PD, 1, sc - 0.85, sc + 0.85, ya + 0.36, ya + hD, lit, 0.95);
                caja(solido, B, sc - 1.05, sc + 1.05, -PD, -PD + 0.14, ya + hD, ya + hD + 0.3, cPiedraL);
                if (op.comercio && ip === 0 && hz(k * 50 + b, 7) < 0.55) {            // mercancía en el portal: sacos, canastos, un cajón
                  const sx = sc + (hz(k * 50 + b, 8) < 0.5 ? -1.6 : 1.6);
                  for (let j = 0; j < 3; j++) gema(solido, F(sx + (j - 1) * 0.55, -PD + 0.7, 0.62 + (j === 1 ? 0.25 : 0)), 0.32 * M, 0.3 * M, 0.26 * M, j, cSaco.clone().multiplyScalar(0.9 + 0.12 * j));
                  torno(solido, B, sc + (sx > sc ? -1.7 : 1.7), -PD + 1.6, [[0.42, 0.34], [0.5, 0.82], [0.44, 0.82]], 10, cCesto);
                  torno(solido, B, sc + (sx > sc ? -1.7 : 1.7), -PD + 1.6, [[0.44, 0.8], [0.05, 0.86]], 10, FRUTA[b % 4]);
                }
              }
            }
            y = yb;
          });
          caja(muros, B, -l - 0.1, l + 0.1, -D - 0.1, -PD, Ht - 0.4, Ht, cPiedraL, true);
          techo(sub(B, 0, -D / 2), l, D / 2, Ht, 0.8, 0.5, cTeja, cm, 0.3);
          return B;
        };

        // ================= la casa de un piso (crujía de la calle): muros gruesos, zócalo, cornisa, portón, ventanas con reja
        const casa = (Bs, s0, s1, k, prof) => {
          const l = (s1 - s0) / 2 - 0.02, [cu, cv] = Bs.lu((s0 + s1) / 2, 0), B = marco(cu, cv, Bs.ang, [l, prof]), F = B.F;
          const Hw = 4.0 + 1.4 * hz(k, 1), azo = hz(k, 2) < 0.18;
          const cm = MUROS[Math.floor(hz(k, 3) * MUROS.length)].clone().multiplyScalar(0.92 + 0.12 * hz(k, 4));
          const cz = cm.clone().lerp(cPiedra, 0.55).multiplyScalar(0.8);
          caja(muros, B, -l, l, -prof, 0, -0.4, Hw, cm, !azo);
          const sD = (hz(k, 5) - 0.5) * Math.max(0, 2 * l - 5), hD = Math.min(3.1, Hw - 0.9);
          // zócalo a los lados del portón y la cornisa
          if (sD - 1.4 > -l) caja(muros, B, -l, sD - 1.4, 0, 0.1, -0.4, 0.95, cz);
          if (sD + 1.4 < l) caja(muros, B, sD + 1.4, l, 0, 0.1, -0.4, 0.95, cz);
          caja(muros, B, -l, l, -0.1, 0.3, Hw - 0.34, Hw, cz.clone().lerp(cm, 0.5));
          // el portón con su marco de piedra (de noche, a veces abierto con luz)
          caja(solido, B, sD - 1.4, sD - 1.04, 0, 0.17, -0.2, hD + 0.1, cPiedraL);
          caja(solido, B, sD + 1.04, sD + 1.4, 0, 0.17, -0.2, hD + 0.1, cPiedraL);
          caja(solido, B, sD - 1.5, sD + 1.5, 0, 0.2, hD + 0.1, hD + 0.45, cPiedraL);
          if (noche && hz(k, 6) < 0.22) vano(B, 0, 1, sD - 1.04, sD + 1.04, 0, hD + 0.1, true, 0.75);
          else {
            cara(solido, [F(sD - 1.04, 0.03, 0), F(sD + 1.04, 0.03, 0), F(sD + 1.04, 0.03, hD + 0.1), F(sD - 1.04, 0.03, hD + 0.1)], cMadera.clone().multiplyScalar(0.9), B.T);
            cara(huecos, [F(sD - 0.03, 0.06, 0), F(sD + 0.03, 0.06, 0), F(sD + 0.03, 0.06, hD + 0.1), F(sD - 0.03, 0.06, hD + 0.1)], cHueco, B.T);
          }
          // las ventanas: con reja al ras o voladiza, repisa y guardapolvo
          const ws = [];
          if (sD - 1.5 - (-l) > 3.2) ws.push((-l + sD - 1.5) / 2);
          if (l - (sD + 1.5) > 3.2) ws.push((sD + 1.5 + l) / 2);
          ws.forEach((sw, w) => {
            const kw = k * 3 + w, bal = hz(kw, 7) < 0.3, y0 = 1.15, y1 = Math.min(3.05, Hw - 0.85), tb = bal ? 0.45 : 0.1;
            vano(B, 0, 1, sw - 0.62, sw + 0.62, y0, y1, noche && hz(kw, 8) < 0.5, 0.85);
            caja(solido, B, sw - 0.82, sw + 0.82, 0, 0.24 + (bal ? 0.3 : 0), y0 - 0.16, y0, cPiedraL);
            for (let b = 0; b <= 4; b++) { const x = sw - 0.6 + 1.2 * b / 4;
              barra(solido, F(x - 0.03, tb, y0), F(x + 0.03, tb, y0), F(x + 0.03, tb, y1 + 0.1), F(x - 0.03, tb, y1 + 0.1), cHierro, B.T); }
            for (const yy of [y0 + 0.12, (y0 + y1) / 2, y1 + 0.06]) barra(solido, F(sw - 0.66, tb + 0.01, yy - 0.03), F(sw + 0.66, tb + 0.01, yy - 0.03), F(sw + 0.66, tb + 0.01, yy + 0.03), F(sw - 0.66, tb + 0.01, yy + 0.03), cHierro, B.T);
            if (bal) {
              for (const sg of [-1, 1]) for (const tt of [0.15, 0.3]) barra(solido, F(sw + sg * 0.66, tt - 0.03, y0), F(sw + sg * 0.66, tt + 0.03, y0), F(sw + sg * 0.66, tt + 0.03, y1 + 0.1), F(sw + sg * 0.66, tt - 0.03, y1 + 0.1), cHierro, sg > 0 ? B.S : neg(B.S));
              caja(solido, B, sw - 0.78, sw + 0.78, 0, tb + 0.12, y1 + 0.1, y1 + 0.24, cHierro);
            } else caja(solido, B, sw - 0.85, sw + 0.85, 0, 0.15, y1 + 0.18, y1 + 0.34, cPiedraL);
          });
          if (azo) {                                                                     // azotea con pretil y gárgolas
            caja(muros, B, -l, l, -0.32, 0.02, Hw, Hw + 0.7, cm);
            caja(muros, B, -l, l, -prof, -prof + 0.32, Hw, Hw + 0.7, cm);
            for (const sg of [-1, 1]) caja(muros, B, sg > 0 ? l - 0.32 : -l, sg > 0 ? l : -l + 0.32, -prof, 0, Hw, Hw + 0.7, cm);
            caja(solido, B, -l, l, -0.4, 0.12, Hw + 0.7, Hw + 0.82, cz);
            for (const sg of [-0.6, 0.6]) caja(solido, B, sg * l - 0.12, sg * l + 0.12, 0, 0.75, Hw + 0.05, Hw + 0.3, cPiedra);
          } else techo(sub(B, 0, -prof / 2), l, prof / 2, Hw, 0.75, 0.4, cTeja.clone().multiplyScalar(0.9 + 0.16 * hz(k, 9)), cm, 0.04);
          return { B, Hw, cm, l };
        };
        // la crujía de atrás, al otro lado del patio (mira al patio: +T), con su chimenea de cocina a veces
        const crujia = (h, tF, prof, k) => {
          const { cm } = h, l = h.l - 0.6, [cu, cv] = h.B.lu(0, tF), B = marco(cu, cv, h.B.ang, [l, prof]), F = B.F, Hw = 3.6 + 0.8 * hz(k, 40);
          caja(muros, B, -l, l, -prof, 0, -0.4, Hw, cm.clone().multiplyScalar(0.96), true);
          caja(muros, B, -l, l, -0.1, 0.12, -0.4, 0.8, cm.clone().lerp(cPiedra, 0.55).multiplyScalar(0.8));
          const sD = (hz(k, 41) - 0.5) * Math.max(0, 2 * l - 4);
          vano(B, 0, 1, sD - 0.6, sD + 0.6, 0, 2.4, noche && hz(k, 42) < 0.35, 0.7);
          if (Math.abs(sD) + 2.6 < l) vano(B, 0, 1, sD + (sD > 0 ? -2.2 : 1.4), sD + (sD > 0 ? -1.4 : 2.2), 1.1, 2.3, false);
          const yR = techo(sub(B, 0, -prof / 2), l, prof / 2, Hw, 0.9, 0.4, cTeja.clone().multiplyScalar(0.88 + 0.16 * hz(k, 43)), cm, 0.2);
          if (hz(k, 44) < 0.4) {
            const sc = (hz(k, 45) - 0.5) * l;
            caja(muros, B, sc - 0.45, sc + 0.45, -prof / 2 - 0.45, -prof / 2 + 0.45, Hw, yR + 0.9, cm.clone().multiplyScalar(0.85));
            humos.push({ P: F(sc, -prof / 2, yR + 1.0), f: hz(k, 46) });
          }
          return B;
        };

        // ================= las manzanas
        const cells = celdas(clamp(p.manzanas | 0, 4, 25), hz);
        // los edificios de la plaza y las iglesias reservan su huella (u, v)
        const reservas = [[41, -H2, 41 + 18.5, H2], [-41 - 16.5, -H2, -41, H2], [-H2, -41 - 16.5, H2, -41], [-3, 41, H2, 41 + BLK], [-H2, 41, -3, 41 + 14.5]];
        const nIgl = cells.length >= 7 ? Math.min(3, 1 + Math.floor((cells.length - 7) / 7)) : 0;
        const igl = cells.slice(4).map((c, i) => ({ c, o: hz(i, 600) })).sort((a, b) => a.o - b.o).slice(0, nIgl).map((x) => x.c);
        const iglesias = igl.map((c, n) => {
          const phi = Math.abs(c.i) >= Math.abs(c.j) ? (c.i > 0 ? PI : 0) : (c.j > 0 ? -PI / 2 : PI / 2), bu = c.i * PASO, bv = c.j * PASO;
          const Bs = marco(bu + Math.cos(phi) * H2, bv + Math.sin(phi) * H2, phi - PI / 2), so = (hz(n, 610) - 0.5) * 16;
          const Bi = sub(Bs, so, 0);
          reservas.push(rectB(Bi, -12.5, 12.5, -52, 0));
          return { Bi, k: 7000 + n };
        });
        // las calles empedradas (con su canal al centro) alrededor de cada manzana y de la plaza; cada tramo una vez
        const hechos = new Set();
        const tramo = (key, u0, v0, u1, v1, largoU) => {
          if (hechos.has(key)) return; hechos.add(key);
          const kk = hechos.size;
          if (largoU) { const vm = (v0 + v1) / 2;
            losas(u0, v0, u1, vm - 0.6, 3.2, 1.95, cEmp, 0.16, 0.06, kk); losas(u0, vm + 0.6, u1, v1, 3.2, 1.95, cEmp, 0.16, 0.06, kk + 300);
            losas(u0, vm - 0.6, u1, vm + 0.6, 2.4, 1.2, cCanal, 0.1, 0.03, kk + 600);
          } else { const um = (u0 + u1) / 2;
            losas(u0, v0, um - 0.6, v1, 1.95, 3.2, cEmp, 0.16, 0.06, kk); losas(um + 0.6, v0, u1, v1, 1.95, 3.2, cEmp, 0.16, 0.06, kk + 300);
            losas(um - 0.6, v0, um + 0.6, v1, 1.2, 2.4, cCanal, 0.1, 0.03, kk + 600);
          }
        };
        for (const c of [{ i: 0, j: 0 }].concat(cells)) {
          const bu = c.i * PASO, bv = c.j * PASO;
          tramo("h" + c.i + "," + c.j, bu - H2, bv - H2 - CALLE, bu + H2, bv - H2, true);
          tramo("h" + c.i + "," + (c.j + 1), bu - H2, bv + H2, bu + H2, bv + H2 + CALLE, true);
          tramo("v" + c.i + "," + c.j, bu - H2 - CALLE, bv - H2, bu - H2, bv + H2, false);
          tramo("v" + (c.i + 1) + "," + c.j, bu + H2, bv - H2, bu + H2 + CALLE, bv + H2, false);
          for (const [a, b] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
            const key = "x" + (c.i + a) + "," + (c.j + b); if (hechos.has(key)) continue; hechos.add(key);
            const uc = bu - H2 - CALLE / 2 + a * PASO, vc = bv - H2 - CALLE / 2 + b * PASO;
            losas(uc - CALLE / 2, vc - CALLE / 2, uc + CALLE / 2, vc + CALLE / 2, 2.25, 2.25, cEmp, 0.16, 0.06, hechos.size + 900);
          }
        }
        cells.forEach((c, ic) => {
          const bu = c.i * PASO, bv = c.j * PASO, kb = (c.i + 5) * 17 + (c.j + 5);
          // el suelo de la manzana, el bordillo y el huerto del centro con sus árboles
          parche([[bu - H2, bv - H2], [bu + H2, bv - H2], [bu + H2, bv + H2], [bu - H2, bv + H2]], cAcera, 0.22);
          const Bb = marco(bu, bv, 0, [H2, 0]);
          for (const [s0, s1, t0, t1] of [[-H2, H2, -H2, -H2 + 0.35], [-H2, H2, H2 - 0.35, H2], [-H2, -H2 + 0.35, -H2, H2], [H2 - 0.35, H2, -H2, H2]])
            caja(solido, Bb, s0, s1, t0, t1, -0.1, 0.26, cPiedra.clone().multiplyScalar(0.85));
          const enRes = (R) => reservas.some((q) => cruza(q, R, 0.3));
          const bloque = [bu - H2, bv - H2, bu + H2, bv + H2], resB = reservas.filter((q) => cruza(q, bloque));
          if (!resB.length) parche([[bu - H2 + DF, bv - H2 + DF], [bu + H2 - DF, bv - H2 + DF], [bu + H2 - DF, bv + H2 - DF], [bu - H2 + DF, bv + H2 - DF]], cHuerto, 0.24);
          const ocupado = [], estas = [];
          for (let d = 0; d < 4; d++) {
            const phi = d * PI / 2, Bs = marco(bu + Math.cos(phi) * H2, bv + Math.sin(phi) * H2, phi - PI / 2);
            const sA = d % 2 ? -H2 + DF : -H2, sB = -sA;
            let s = sA, n = 0;
            while (s < sB - 0.5) {
              const k = kb * 1000 + d * 100 + n;
              let L = 9 + 8 * hz(k, 20); if (sB - s - L < 7) L = sB - s;
              const R = rectB(Bs, s, s + L, -DF, 0);
              if (!enRes(R)) { const h = casa(Bs, s, s + L, k, DF); ocupado.push(R); estas.push({ ...h, k }); }
              s += L; n++;
            }
          }
          for (const h of estas) {
            if (h.l < 4 || hz(h.k, 30) > 0.55) continue;
            const P = 6 + 4 * hz(h.k, 31), pr = 5 + 2 * hz(h.k, 32), tF = -DF - P;
            const R = rectB(h.B, -h.l + 0.6, h.l - 0.6, tF - pr, tF);
            if (enRes(R) || ocupado.some((q) => cruza(q, R, 0.4))) continue;
            crujia(h, tF, pr, h.k + 5);
            ocupado.push(R);
            parcheB(h.B, -h.l + 0.4, h.l - 0.4, tF, -DF, cPatio.clone().multiplyScalar(0.94 + 0.1 * hz(h.k, 33)), 0.28);
            const z = hz(h.k, 34);
            if (z < 0.45) frondoso(h.B.F((hz(h.k, 35) - 0.5) * h.l, tF + P * 0.5, 0.28), 5 + 3 * hz(h.k, 36), h.k + 77);
            else if (z < 0.75) {                                                       // la pila del patio
              const sc = (hz(h.k, 37) - 0.5) * h.l, tc = tF + P * 0.5;
              torno(solido, h.B, sc, tc, [[1.0, 0.2], [1.0, 0.8], [0.8, 0.8], [0.8, 0.6]], 12, cPiedraL);
              torno(aguas, h.B, sc, tc, [[0.8, 0.62], [0.04, 0.62]], 12, cAgua);
            }
          }
          if (!resB.length) for (let q = 0; q < 3; q++) {                                // los árboles del huerto
            const k = kb * 31 + q, uu = bu + (hz(k, 50) - 0.5) * 16, vv = bv + (hz(k, 51) - 0.5) * 16;
            if (hz(k, 52) < 0.75) frondoso(E(uu, vv, 0.24), 6 + 4 * hz(k, 53), k + 3000);
          }
        });

        // ================= la plaza: empedrada, con su bordillo, la fuente al centro y el mercado
        losas(-H2, -H2, H2, H2, 4, 4, cPlaza, 0.12, 0.12, 4242);
        const Bp = marco(0, 0, 0, [H2, 0]);
        for (const [s0, s1, t0, t1] of [[-H2, H2, -H2, -H2 + 0.45], [-H2, H2, H2 - 0.45, H2], [-H2, -H2 + 0.45, -H2, H2], [H2 - 0.45, H2, -H2, H2]])
          caja(solido, Bp, s0, s1, t0, t1, -0.1, 0.26, cPiedra.clone().multiplyScalar(0.85));
        // la fuente: pila ochavada, pedestal, taza, remate y el agua
        {
          const B = marco(0, 0, 0, [6, 6]), cF = cPiedraL.clone().multiplyScalar(1.02);
          torno(solido, B, 0, 0, [[6.2, 0.0], [6.2, 0.22], [5.7, 0.22]], 8, cPiedra, PI / 8);                // la grada
          torno(solido, B, 0, 0, [[5.5, 0.1], [5.5, 0.92], [5.0, 0.92], [5.0, 0.55]], 8, cF, PI / 8);         // la pila
          torno(aguas, B, 0, 0, [[5.0, 0.68], [0.6, 0.68]], 8, cAgua, PI / 8);
          torno(solido, B, 0, 0, [[0.9, 0.5], [0.62, 1.0], [0.45, 1.55], [0.38, 1.6]], 16, cF);
          torno(solido, B, 0, 0, [[0.35, 1.5], [2.3, 2.0], [2.4, 2.25], [2.1, 2.22], [0.4, 1.9]], 20, cF);
          torno(aguas, B, 0, 0, [[2.1, 2.16], [0.4, 2.16]], 20, cAgua);
          torno(solido, B, 0, 0, [[0.32, 2.1], [0.26, 2.9], [0.55, 3.05], [0.5, 3.25], [0.05, 3.7]], 16, cF);
        }
        // los puestos: mesa con mercancía, canastos, toldo de lona a dos aguas sobre cuatro horcones
        const puestos = [];
        for (const v of [-21, 21]) for (const u of [-24, -17, -10, 10, 17, 24]) puestos.push([u, v, v > 0 ? -PI / 2 : PI / 2]);
        for (const v of [-8, 0, 8]) puestos.push([-23, v, 0]);
        const vendedores = [];
        puestos.forEach(([u, v, phi], i) => {
          const B = marco(u, v, phi - PI / 2, [1.6, 1.6]), F = B.F, k = 800 + i, cl = LONAS[Math.floor(hz(k, 1) * LONAS.length)].clone().multiplyScalar(0.9 + 0.14 * hz(k, 2));
          caja(solido, B, -1.3, 1.3, -0.7, 0.7, 0.74, 0.84, cMadera);
          for (const [a, b] of [[-1.2, -0.6], [1.2, -0.6], [-1.2, 0.6], [1.2, 0.6]]) tubo(solido, F(a, b, 0.1), F(a, b, 0.76), 0.045 * M, 6, cMadera);
          for (const [a, b] of [[-1.45, -1.35], [1.45, -1.35], [-1.45, 1.35], [1.45, 1.35]]) tubo(solido, F(a, b, 0.1), F(a, b, b > 0 ? 2.05 : 2.3), 0.05 * M, 6, cMadera);
          // el toldo (un agua hacia el frente, con la orilla que cae)
          cara(techos, [F(-1.65, 1.55, 2.0), F(1.65, 1.55, 2.0), F(1.65, -1.55, 2.4), F(-1.65, -1.55, 2.4)], cl, null);
          cara(techos, [F(-1.65, 1.55, 2.0), F(1.65, 1.55, 2.0), F(1.65, -1.55, 2.4), F(-1.65, -1.55, 2.4)].map((P) => [P[0], P[1] - 0.02 * M, P[2]]), cl.clone().multiplyScalar(0.5), DOWN);
          cara(techos, [F(-1.65, 1.55, 2.0), F(1.65, 1.55, 2.0), F(1.65, 1.6, 1.7), F(-1.65, 1.6, 1.7)], cl.clone().multiplyScalar(0.85), B.T);
          // la mercancía: montones de fruta y verdura, canastos en el suelo
          for (let j = 0; j < 7; j++) {
            const sx = -1.05 + 2.1 * j / 6, cf = FRUTA[Math.floor(hz(k * 9 + j, 3) * FRUTA.length)];
            gema(solido, F(sx, 0.15 * (hz(k * 9 + j, 4) - 0.5), 0.92), 0.2 * M, 0.13 * M, 0.2 * M, j, cf.clone().multiplyScalar(0.85 + 0.25 * hz(k * 9 + j, 5)));
          }
          for (const [a, b] of [[-1.9, 0.9], [1.9, 0.5]]) if (hz(k, 6 + a) < 0.75) {
            torno(solido, B, a, b, [[0.34, 0.1], [0.42, 0.5], [0.36, 0.5]], 10, cCesto);
            torno(solido, B, a, b, [[0.38, 0.48], [0.04, 0.58]], 10, FRUTA[(i + (a > 0 ? 1 : 2)) % 4]);
          }
          if (noche && hz(k, 9) < 0.65) {                                               // el farol del puesto
            gema(focos, F(0, 0.4, 2.05), 0.12 * M, 0.16 * M, 0.12 * M, 0, cLuz);
            brillos.push(F(0, 0.4, 1.95));
          }
          vendedores.push({ B, k });
        });
        // la carreta con sacos (quieta, al borde de la plaza) y el carretón de mano que da la vuelta (armados en metros locales)
        const carretaGeo = (sacos) => {
          const acc = nueva(), I = { F: (s, t, y) => [s, y, t], S: [1, 0, 0], T: [0, 0, 1] };
          caja(acc, I, -1.5, 1.5, -0.78, 0.78, 0.98, 1.12, cMadera);
          for (let j = 0; j < 5; j++) cara(acc, [[-1.5, 1.125, -0.75 + j * 0.32], [1.5, 1.125, -0.75 + j * 0.32], [1.5, 1.125, -0.73 + j * 0.32], [-1.5, 1.125, -0.73 + j * 0.32]], cHueco, UP);
          for (const z of [-0.78, 0.78]) {
            for (const x of [-1.4, -0.45, 0.45, 1.4]) caja(acc, I, x - 0.05, x + 0.05, z - 0.05, z + 0.05, 1.1, 1.75, cMadera);
            caja(acc, I, -1.5, 1.5, z - 0.05, z + 0.05, 1.62, 1.72, cMadera);
          }
          for (const z of [-0.45, 0.45]) tubo(acc, [1.5, 1.05, z], [3.3, 0.62, z * 0.4], 0.055, 6, cMadera);
          tubo(acc, [0, 0.75, -0.92], [0, 0.75, 0.92], 0.06, 8, cMadera);
          if (sacos) for (let j = 0; j < 6; j++) { const x = -1.0 + 0.95 * (j % 3), z = j < 3 ? -0.36 : 0.36;
            gema(acc, [x, 1.38 + (j === 4 ? 0.3 : 0), z], 0.42, 0.3, 0.34, j * 0.7, cSaco.clone().multiplyScalar(0.88 + 0.06 * (j % 3))); }
          return acc;
        };
        const ruedaGeo = () => {
          const acc = nueva(), R = 0.75, N = 16;
          for (let i = 0; i < N; i++) {                                               // el aro (ejes: rueda en el plano x-y, eje z)
            const a0 = TAU * i / N, a1 = TAU * (i + 1) / N, am = (a0 + a1) / 2, P = (rr, a, z) => [rr * Math.cos(a), rr * Math.sin(a), z];
            for (const [rA, rB, zA, zB, ref] of [[R, R, -0.07, 0.07, [Math.cos(am), Math.sin(am), 0]], [R - 0.12, R - 0.12, 0.07, -0.07, [-Math.cos(am), -Math.sin(am), 0]],
              [R, R - 0.12, 0.07, 0.07, [0, 0, 1]], [R - 0.12, R, -0.07, -0.07, [0, 0, -1]]])
              cara(acc, [P(rA, a0, zA), P(rA, a1, zA), P(rB, a1, zB), P(rB, a0, zB)], cMadera, ref);
          }
          for (let i = 0; i < 8; i++) { const a = TAU * i / 8; tubo(acc, [0, 0, 0], [(R - 0.1) * Math.cos(a), (R - 0.1) * Math.sin(a), 0], 0.035, 4, cMadera); }
          tubo(acc, [0, 0, -0.12], [0, 0, 0.12], 0.13, 10, cMadera.clone().multiplyScalar(0.8));
          return acc;
        };
        const matMov = malla.material({}); mats.push(matMov);
        const hacerCarreta = (sacos, esc) => {
          const g = new THREE.Group(), m = new THREE.Mesh(malla.geometria(carretaGeo(sacos)), matMov); m.frustumCulled = false; m.renderOrder = 4; g.add(m);
          const ruedas = [-0.86, 0.86].map((z) => { const w = new THREE.Mesh(malla.geometria(ruedaGeo()), matMov); w.frustumCulled = false; w.renderOrder = 4; w.position.set(0, 0.75, z); g.add(w); return w; });
          g.scale.setScalar(M * esc); scene.add(g); return { g, ruedas };
        };
        const carreta = hacerCarreta(true, 1);
        { const P = E(-30.2, 11, 0.12); carreta.g.position.set(P[0], P[1], P[2]); carreta.g.rotation.set(0, r + PI / 2, -0.16); }

        // ================= la catedral (tres naves, torres bajas, bóveda, cupulitas y cúpula del crucero) y la galería del arzobispado
        const Bcs = marco(15, 41, PI);
        {
          const B = marco(15, 41, PI, [17, 62]), F = B.F, cm = cCal.clone().multiplyScalar(1.02), cF = cm.clone().lerp(cPiedraL, 0.25);
          const T0 = -60, T1 = -5.5, Hc = 13, Hl = 9;
          parcheB(B, -17, 17, -5.5, 0, cPatio, 0.3);
          caja(solido, B, -12, 12, -1.4, 0, -0.2, 0.3, cPiedraL); caja(solido, B, -11, 11, -2.6, -1.4, -0.2, 0.6, cPiedraL);
          caja(muros, B, -5.6, 5.6, T0, T1, -0.4, Hc, cm, true);
          boveda(B, 0, 5.6, T0, T1, Hc, 3.2, cCal.clone().multiplyScalar(1.05));
          for (const sg of [-1, 1]) {
            caja(muros, B, sg > 0 ? 5.6 : -12, sg > 0 ? 12 : -5.6, T0, T1, -0.4, Hl, cm);
            caja(solido, B, sg > 0 ? 5.5 : -12.2, sg > 0 ? 12.2 : -5.5, T0 - 0.2, T1, Hl - 0.3, Hl + 0.15, cPiedraL);
            for (const tc of [-11, -19, -27, -47, -55]) {
              caja(muros, B, sg * 8.8 - 1.9, sg * 8.8 + 1.9, tc - 1.9, tc + 1.9, Hl, Hl + 0.6, cm);
              cupula(techos, B, sg * 8.8, tc, Hl + 0.6, 1.9, 1.5, 14, cCal.clone().multiplyScalar(1.0));
              tubo(solido, F(sg * 8.8, tc, Hl + 2.0), F(sg * 8.8, tc, Hl + 2.6), 0.22 * M, 8, cCal);
            }
            for (let tc = -9; tc > T0; tc -= 8) {                                      // contrafuertes con su remate en talud
              caja(muros, B, sg > 0 ? 12 : -13.5, sg > 0 ? 13.5 : -12, tc - 0.8, tc + 0.8, -0.3, Hl - 1.2, cm.clone().multiplyScalar(0.94));
              const so = sg * 13.5, si = sg * 12;
              cara(muros, [F(so, tc - 0.8, Hl - 1.2), F(so, tc + 0.8, Hl - 1.2), F(si, tc + 0.8, Hl - 0.2), F(si, tc - 0.8, Hl - 0.2)], cm.clone().multiplyScalar(0.85), null);
              if (tc - 4 > T0) vano(girar(B), -sg * 12, -sg, tc - 4.6, tc - 3.4, 4.2, 6.8, noche && hz(Math.round(tc) * 3 + sg, 620) < 0.3, 0.5);
            }
          }
          // el crucero: base, tambor con ventanas, cúpula y linterna
          caja(muros, B, -5.8, 5.8, -43.8, -32.2, Hc - 0.2, Hc + 1.4, cm);
          torno(muros, B, 0, -38, [[5.0, Hc + 1.4], [5.0, Hc + 4.4]], 16, cm.clone().multiplyScalar(0.98));
          for (let i = 0; i < 8; i++) { const a = TAU * i / 8 + PI / 8, P = (rr, yy, da) => F(rr * Math.cos(a + da), -38 + rr * Math.sin(a + da), yy);
            cara(huecos, [P(5.04, Hc + 2.0, -0.12), P(5.04, Hc + 2.0, 0.12), P(5.04, Hc + 3.8, 0.12), P(5.04, Hc + 3.8, -0.12)], cHueco, [Math.cos(a) * B.S[0] + Math.sin(a) * B.T[0], 0, Math.cos(a) * B.S[2] + Math.sin(a) * B.T[2]]); }
          torno(solido, B, 0, -38, [[5.3, Hc + 4.4], [5.3, Hc + 4.75], [5.0, Hc + 4.75]], 16, cPiedraL);
          cupula(techos, B, 0, -38, Hc + 4.75, 5.0, 4.4, 20, cCal.clone().multiplyScalar(1.04));
          linterna(B, 0, -38, Hc + 9.1, 0.9);
          // la fachada: frontispicio en tres cuerpos con pilastras y cornisas, puerta en arco, ventana del coro, nichos
          caja(muros, B, -11.6, 11.6, T1 - 0.2, -4.0, -0.4, 15.5, cF);
          caja(muros, B, -7.2, 7.2, T1 - 0.2, -4.0, 15.5, 18.8, cF);
          caja(muros, B, -3.2, 3.2, T1 - 0.2, -4.0, 18.8, 20.6, cF);
          for (const [yy, a] of [[6.6, 11.9], [11.6, 11.9], [15.5, 11.9], [18.8, 7.5]]) caja(solido, B, -a, a, T1 - 0.3, -3.65, yy - 0.4, yy, cPiedraL);
          for (const sx of [-9.4, -3.6, 3.6, 9.4]) for (const [ya, yb] of [[0.3, 6.2], [6.6, 11.2], [11.6, 15.1]]) caja(solido, B, sx - 0.45, sx + 0.45, -4.0, -3.72, ya, yb, cPiedraL);
          for (const sx of [-5.2, 5.2]) caja(solido, B, sx - 0.4, sx + 0.4, -4.0, -3.72, 15.5, 18.4, cPiedraL);
          const pr = noche;
          { const tP = -3.96, ref = B.T, cP = pr ? cLuz.clone().multiplyScalar(0.8) : cHueco, acc = pr ? focos : huecos;
            cara(acc, [F(-1.7, tP, 0.3), F(1.7, tP, 0.3), F(1.7, tP, 4.3), F(-1.7, tP, 4.3)], cP, ref);
            for (let i = 0; i < 10; i++) { const a0 = PI * i / 10, a1 = PI * (i + 1) / 10;
              cara(acc, [F(1.7 * Math.cos(a0), tP, 4.3 + 1.7 * Math.sin(a0)), F(1.7 * Math.cos(a1), tP, 4.3 + 1.7 * Math.sin(a1)), F(0, tP, 4.3), F(0, tP, 4.3)], cP, ref); }
            if (pr) { brillos.push(F(0, -2.6, 2.6)); brillos.push(F(0, -2.2, 4.6)); }
            vano(B, -4.0, 1, -1.1, 1.1, 8.0, 10.3, pr, 0.6);
            for (const sx of [-6.5, 6.5]) for (const [ya, yb] of [[2.2, 4.8], [8.0, 10.2]]) vano(B, -4.0, 1, sx - 0.55, sx + 0.55, ya, yb, false);
            vano(B, -4.0, 1, -0.6, 0.6, 16.3, 17.9, false);
          }
          // las dos torres bajas: cuerpo, campanario con sus vanos en arco y cupulino con linterna
          for (const sg of [-1, 1]) {
            const sc = sg * 14.3, tc = -6.8;
            caja(muros, B, sc - 2.7, sc + 2.7, tc - 2.7, tc + 2.7, -0.4, 16.4, cF);
            caja(solido, B, sc - 2.95, sc + 2.95, tc - 2.95, tc + 2.95, 16.0, 16.6, cPiedraL);
            caja(muros, B, sc - 2.3, sc + 2.3, tc - 2.3, tc + 2.3, 16.6, 21.2, cF);
            caja(solido, B, sc - 2.55, sc + 2.55, tc - 2.55, tc + 2.55, 21.2, 21.7, cPiedraL);
            for (const lado of [1, -1]) for (const Bt of [sub(B, sc, tc), girar(sub(B, sc, tc))]) vano(Bt, lado * 2.3, lado, -0.85, 0.85, 17.4, 20.0, false);
            for (const sx of [sc - 1.9, sc + 1.9]) caja(solido, B, sx - 0.35, sx + 0.35, -4.0, -3.72, 0.3, 15.8, cPiedraL);
            cupula(techos, B, sc, tc, 21.7, 2.2, 2.0, 16, cCal.clone().multiplyScalar(1.03));
            linterna(B, sc, tc, 23.6, 0.45);
          }
          // la galería del arzobispado, al lado, con dos pisos de arquería
          edificio(Bcs, 17.6, 47, 14, 6, [{ h: 5.8, arcos: true }, { h: 4.6, arcos: true, antepecho: true }], cCal.clone().lerp(MUROS[1], 0.4), 9100, { pw: 1.15 });
        }
        // el palacio y el cabildo (dos pisos de arquería de piedra), y enfrente de la catedral las casas con balcones sobre su portal
        edificio(marco(41, 0, PI / 2), -H2, H2, 18, 13, [{ h: 6.4, arcos: true }, { h: 5.2, arcos: true, antepecho: true }], cCal.clone(), 9200, { comercio: true });
        edificio(marco(-41, 0, -PI / 2), -H2, H2, 16, 11, [{ h: 6.2, arcos: true }, { h: 5.0, arcos: true, antepecho: true }], cCal.clone().lerp(MUROS[2], 0.5), 9300, { comercio: true, pw: 1.4 });
        const colCasas = []; { let c = 0; for (let b = 0; b < 12; b++) { if (b && hz(b, 630) < 0.45) c++; colCasas.push(MUROS[(c + 1) % MUROS.length].clone().multiplyScalar(0.94 + 0.1 * hz(c, 631))); } }
        edificio(marco(0, -41, 0), -H2, H2, 16, 12, [{ h: 5.2, arcos: true }, { h: 4.4, arcos: false, balcones: true }], MUROS[4].clone(), 9400, { comercio: true, colores: colCasas });

        // ================= las otras iglesias: muros gruesos, contrafuertes, atrio con tapia y cruz, espadaña o torre
        for (const { Bi, k } of iglesias) {
          const [cu, cv] = Bi.lu(0, 0), B = marco(cu, cv, Bi.ang, [12, 50]), F = B.F;
          const L0 = -48, L1 = -11, Wn = 5.6, Hn = 10 + 2 * hz(k, 1), bov = hz(k, 2) < 0.55;
          const cm = MUROS[Math.floor(hz(k, 3) * MUROS.length)].clone(), cF = cm.clone().multiplyScalar(1.04);
          parcheB(B, -11, 11, -11, 0, cPatio, 0.3);
          caja(muros, B, -11.5, -2.3, -0.5, 0, -0.3, 1.3, cm); caja(muros, B, 2.3, 11.5, -0.5, 0, -0.3, 1.3, cm);
          for (const sg of [-1, 1]) {
            caja(muros, B, sg > 0 ? 11 : -11.5, sg > 0 ? 11.5 : -11, -11, 0, -0.3, 1.3, cm);
            caja(solido, B, sg * 2.6 - 0.35, sg * 2.6 + 0.35, -0.6, 0.1, -0.3, 2.6, cPiedraL);
          }
          caja(solido, B, -0.9, 0.9, -5.9, -4.1, -0.2, 0.8, cPiedraL);                    // la cruz del atrio en su peana
          caja(solido, B, -0.13, 0.13, -5.13, -4.87, 0.8, 3.8, cPiedraL); caja(solido, B, -0.75, 0.75, -5.13, -4.87, 2.9, 3.15, cPiedraL);
          caja(muros, B, -Wn, Wn, L0, L1, -0.4, Hn, cm, true);
          for (let tc = L1 - 5; tc > L0 + 1; tc -= 7) for (const sg of [-1, 1]) {
            caja(muros, B, sg > 0 ? Wn : -Wn - 1.4, sg > 0 ? Wn + 1.4 : -Wn, tc - 0.75, tc + 0.75, -0.3, Hn - 1.8, cm.clone().multiplyScalar(0.93));
            cara(muros, [F(sg * (Wn + 1.4), tc - 0.75, Hn - 1.8), F(sg * (Wn + 1.4), tc + 0.75, Hn - 1.8), F(sg * Wn, tc + 0.75, Hn - 0.6), F(sg * Wn, tc - 0.75, Hn - 0.6)], cm.clone().multiplyScalar(0.85), null);
            if (tc - 3.5 > L0) vano(girar(B), -sg * Wn, -sg, tc - 4.0, tc - 3.0, Hn - 4.2, Hn - 2.0, false);
          }
          if (bov) {
            caja(solido, B, -Wn - 0.2, Wn + 0.2, L0 - 0.2, L1, Hn - 0.3, Hn + 0.1, cPiedraL);
            boveda(B, 0, Wn, L0, L1 - 1, Hn + 0.1, 2.6, cCal.clone().multiplyScalar(1.04));
            const tc = L0 + 8;
            caja(muros, B, -Wn - 0.1, Wn + 0.1, tc - 5.2, tc + 5.2, Hn, Hn + 2.8, cm);
            torno(muros, B, 0, tc, [[4.0, Hn + 2.8], [4.0, Hn + 4.6]], 16, cm.clone().multiplyScalar(0.97));
            cupula(techos, B, 0, tc, Hn + 4.6, 4.1, 3.4, 18, cCal.clone().multiplyScalar(1.03));
            linterna(B, 0, tc, Hn + 8.0, 0.7);
          } else techo(sub(B, 0, (L0 + L1) / 2), (L1 - L0) / 2, Wn, Hn, 0.6, 0.6, cTeja, cm, 0.2);
          caja(muros, B, -Wn - 1.7, Wn + 1.7, L1 - 1.3, L1, -0.4, Hn + 1.6, cF);
          caja(muros, B, -4.0, 4.0, L1 - 1.3, L1, Hn + 1.6, Hn + 4.2, cF);
          caja(muros, B, -1.8, 1.8, L1 - 1.3, L1, Hn + 4.2, Hn + 5.5, cF);
          for (const [yy, a] of [[5.9, Wn + 1.95], [Hn + 1.6, Wn + 1.95], [Hn + 4.2, 4.3]]) caja(solido, B, -a, a, L1 - 1.4, L1 + 0.26, yy - 0.38, yy, cPiedraL);
          for (const sx of [-5.9, -2.7, 2.7, 5.9]) for (const [ya, yb] of [[0.3, 5.5], [5.9, Hn + 1.2]]) caja(solido, B, sx - 0.38, sx + 0.38, L1, L1 + 0.24, ya, yb, cPiedraL);
          { const tP = L1 + 0.04, cP = noche ? cLuz.clone().multiplyScalar(0.75) : cHueco, acc = noche ? focos : huecos;
            cara(acc, [F(-1.4, tP, 0.3), F(1.4, tP, 0.3), F(1.4, tP, 3.5), F(-1.4, tP, 3.5)], cP, B.T);
            for (let i = 0; i < 10; i++) { const a0 = PI * i / 10, a1 = PI * (i + 1) / 10;
              cara(acc, [F(1.4 * Math.cos(a0), tP, 3.5 + 1.4 * Math.sin(a0)), F(1.4 * Math.cos(a1), tP, 3.5 + 1.4 * Math.sin(a1)), F(0, tP, 3.5), F(0, tP, 3.5)], cP, B.T); }
            if (noche) brillos.push(F(0, L1 + 1.2, 2.2));
            vano(B, L1, 1, -0.75, 0.75, 7.0, 8.8, false);
            for (const sx of [-4.3, 4.3]) vano(B, L1, 1, sx - 0.45, sx + 0.45, 2.0, 4.2, false);
          }
          if (hz(k, 4) < 0.5) {                                                         // espadaña con tres vanos
            caja(muros, B, -2.8, 2.8, L1 - 1.0, L1 - 0.3, Hn + 5.5, Hn + 9.4, cF);
            caja(solido, B, -3.0, 3.0, L1 - 1.1, L1 - 0.2, Hn + 9.4, Hn + 9.7, cPiedraL);
            for (const [sx, y0] of [[-1.5, Hn + 6.0], [1.5, Hn + 6.0], [0, Hn + 7.9]]) for (const lado of [1, -1]) {
              vano(B, lado > 0 ? L1 - 0.3 : L1 - 1.0, lado, sx - 0.5, sx + 0.5, y0, y0 + 1.3, false);
            }
          } else {                                                                      // torre baja a un lado
            const sc = Wn + 4.2, tc = L1 - 2.6;
            caja(muros, B, sc - 2.5, sc + 2.5, tc - 2.5, tc + 2.5, -0.4, Hn + 3.0, cF);
            caja(solido, B, sc - 2.75, sc + 2.75, tc - 2.75, tc + 2.75, Hn + 2.7, Hn + 3.2, cPiedraL);
            caja(muros, B, sc - 2.1, sc + 2.1, tc - 2.1, tc + 2.1, Hn + 3.2, Hn + 7.2, cF);
            for (const lado of [1, -1]) for (const Bt of [sub(B, sc, tc), girar(sub(B, sc, tc))]) vano(Bt, lado * 2.1, lado, -0.75, 0.75, Hn + 3.9, Hn + 6.3, false);
            caja(solido, B, sc - 2.35, sc + 2.35, tc - 2.35, tc + 2.35, Hn + 7.2, Hn + 7.6, cPiedraL);
            cupula(techos, B, sc, tc, Hn + 7.6, 2.0, 1.8, 16, cCal.clone().multiplyScalar(1.03));
            linterna(B, sc, tc, Hn + 9.3, 0.4);
          }
        }

        // ================= el volcán de fondo: cono genérico, piramidal, con barrancas (maqueta, no a escala)
        if (p.volcan_fondo) {
          const NR = 40, NS = 128, Pv = [], Cv = [], ph = (p.semilla * 0.618) % 1 * TAU;
          const ruido = (a, b) => 0.5 + 0.25 * Math.sin(a * 0.031 + b * 0.017 + ph) + 0.25 * Math.sin(a * 0.013 - b * 0.029 + 2 * ph);
          for (let i = 0; i <= NR; i++) {
            const x = 0.006 + 0.994 * i / NR, fila = [], filc = [];
            for (let j = 0; j <= NS; j++) {
              const th = TAU * (j % NS) / NS, u = VU + x * VR * Math.cos(th), v = x * VR * Math.sin(th);
              let h = VH * Math.pow(1 - x, 1.12);
              const rib = Math.pow(0.5 + 0.5 * Math.sin(13 * th + ph), 3);
              h -= 0.07 * VH * 4 * x * (1 - x) * rib;
              if (x < 0.05) h -= 26 * (1 - (x / 0.05) * (x / 0.05));
              fila.push(E(u, v, h - 0.8));
              const n = ruido(u, v);
              let c;
              if (x < 0.16) c = cCeniza.clone().lerp(cRoca, 0.4 * n);
              else if (x < 0.34) c = cZacate.clone().lerp(cCeniza, 1 - liso(0.14, 0.3, x));
              else if (x < 0.78) c = cBosque.clone().lerp(cZacate, 1 - liso(0.32, 0.42, x)).lerp(cPasto2, 0.3 * n).lerp(cPasto, liso(0.7, 0.8, x));
              else c = cPasto.clone().lerp(cPasto2, 0.5 * n);
              c.multiplyScalar(0.9 + 0.12 * n - 0.12 * rib * (x > 0.15 && x < 0.9 ? 1 : 0));
              filc.push(c);
            }
            Pv.push(fila); Cv.push(filc);
          }
          const tierra = nueva(); lamina(tierra, Pv, Cv); poner(tierra, { desfase: 0 }, 2);
        }

        // ================= las mallas fijas
        poner(suelos, { desfase: 3 }, 2);
        poner(muros, {}, 3);
        poner(techos, {}, 3);
        poner(solido, { desfase: 1 }, 3);
        poner(veg, {}, 3);
        poner(huecos, { desfase: 2 }, 3);
        poner(aguas, { desfase: 4 }, 3);
        const matFoc = malla.material({ desfase: 3 }); malla.poner(focos, matFoc, 4); matFoc.uniforms.uBrillo.value = noche ? 1.7 : 1;

        // ================= lo que se mueve por shader: brillos de las luces, humo de las cocinas, el agua de la fuente
        const uPx = { value: 1 }, uT = { value: 0 };
        if (brillos.length) {
          const g = new THREE.BufferGeometry(), pos = new Float32Array(brillos.length * 3), fa = new Float32Array(brillos.length);
          brillos.forEach((b, i) => { pos.set(b, i * 3); fa[i] = hz(i, 140); });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 1));
          const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uTam: { value: 3.4 * M }, cA: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "uniform float uPx, uTam, uT; attribute float aF; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(uTam * uPx / max(1e-3, -mv.z), 1.5, 26.0); vA = 0.82 + 0.1 * sin(uT * 6.1 + aF * 40.0) + 0.08 * sin(uT * 2.3 + aF * 17.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.5 * vA * exp(-r * r * 4.5); gl_FragColor = vec4(srgb(cA) * a, a); }" });
          const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 9; scene.add(m);
        }
        if (humos.length) {
          const NP = 7, g = new THREE.BufferGeometry(), pos = new Float32Array(humos.length * NP * 3), fa = new Float32Array(humos.length * NP * 2);
          humos.forEach((h, i) => { for (let j = 0; j < NP; j++) { pos.set(h.P, (i * NP + j) * 3); fa[(i * NP + j) * 2] = h.f; fa[(i * NP + j) * 2 + 1] = j / NP; } });
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 2));
          const vi = [Math.cos(r + 2.2), -Math.sin(r + 2.2)];
          const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, uV: { value: new THREE.Vector2(vi[0], vi[1]) }, cA: { value: cHumo.clone() }, uK: { value: noche ? 0.14 : 0.42 } },
            transparent: true, depthWrite: false,
            vertexShader: "uniform float uPx, uT, uM; uniform vec2 uV; attribute vec2 aF; varying float vA; void main(){ float a = fract(uT / 8.0 + aF.x + aF.y); vec3 p = position + vec3(uV.x * a * a * 7.0, a * 10.0, uV.y * a * a * 7.0) * uM; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp((0.9 + 3.0 * a) * uM * uPx / max(1e-3, -mv.z), 1.0, 60.0); vA = (1.0 - a) * smoothstep(0.0, 0.15, a); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.6); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }
        {                                                                                 // el agua: chorros del remate a la taza y de la taza a la pila
          const NC = 24, NG = 7, N = NC * NG, g = new THREE.BufferGeometry(), pos = new Float32Array(N * 3), fa = new Float32Array(N * 4);
          const C0 = E(0, 0, 0);
          for (let c = 0; c < NC; c++) for (let j = 0; j < NG; j++) {
            const i = c * NG + j, alto = c < 8, an = TAU * (c % (alto ? 8 : 16)) / (alto ? 8 : 16) + (alto ? 0.2 : 0);
            pos.set(C0, i * 3);
            fa.set([an, alto ? 1 : 0, j / NG, hz(i, 160)], i * 4);
          }
          g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aF", new THREE.BufferAttribute(fa, 4));
          const ex = W2(1, 0), ez = W2(0, 1), O = W2(0, 0);
          const eu = new THREE.Vector3((ex[0] - O[0]) / M, 0, -(ex[1] - O[1]) / M), ev = new THREE.Vector3((ez[0] - O[0]) / M, 0, -(ez[1] - O[1]) / M);
          const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, uU: { value: eu }, uV: { value: ev }, cA: { value: cChorro.clone() }, uK: { value: noche ? 0.4 : 0.75 } },
            transparent: true, depthWrite: false,
            vertexShader: "uniform float uPx, uT, uM; uniform vec3 uU, uV; attribute vec4 aF; varying float vA; void main(){ float per = aF.y > 0.5 ? 1.1 : 0.9; float a = fract(uT / per + aF.z + aF.w * 0.13); vec2 d = vec2(cos(aF.x), sin(aF.x)); float r, h; if (aF.y > 0.5) { r = 0.2 + 1.5 * a; h = 3.62 + 0.5 * 4.0 * a * (1.0 - a) - 1.45 * a * a; } else { r = 2.42 + 0.55 * a; h = 2.24 - 1.56 * a * a; } vec3 p = position + (uU * d.x * r + uV * d.y * r) * uM + vec3(0.0, h * uM, 0.0); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(0.16 * uM * uPx / max(1e-3, -mv.z), 1.0, 14.0); vA = smoothstep(0.0, 0.08, a) * (1.0 - smoothstep(0.85, 1.0, a)); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * (1.0 - r * r); gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }

        // ================= la gente: vendedores, el cargador de la carreta, quien jala el carretón, dos que platican y los que caminan
        const NPER = clamp(p.personas | 0, 0, 30), npv = noche ? Math.ceil(NPER / 2) : NPER;
        const a2 = 26.5, ln = H2 + CALLE / 2 + 2.2;
        const RUTAS = [
          { pts: [[-a2, -a2], [a2, -a2], [a2, a2], [-a2, a2], [-a2, -a2]], loop: true },
          { pts: [[-a2, a2], [a2, a2], [a2, -a2], [-a2, -a2], [-a2, a2]], loop: true },
          { pts: [[-19, -12], [27, -12]], loop: false },
          { pts: [[27, 12], [-19, 12]], loop: false },
          { pts: [[7, -30], [7, 30]], loop: false },
          { pts: [[41 + 2.4, -29], [41 + 2.4, 29]], loop: false },                   // bajo el portal del palacio
          { pts: [[-29, -41 - 2.4], [29, -41 - 2.4]], loop: false },                 // bajo el portal de las casas
          { pts: [[ln, -100], [ln, 100]], loop: false },
          { pts: [[-100, ln], [100, ln]], loop: false },
          { pts: [[-ln, 100], [-ln, -100]], loop: false },
          { pts: [[100, -ln], [-100, -ln]], loop: false },
          { pts: [[-41 - 2.4, 29], [-41 - 2.4, -29]], loop: false },                 // bajo el portal del cabildo
        ].map((ru) => ({ ...conS(ru.pts), loop: ru.loop }));
        const rondaR = conS(ronda(RONDA, RR));
        const gente = [];
        if (npv > 0) {
          const nv = Math.min(puestos.length, Math.max(1, Math.round(npv * 0.3)));
          const orden = puestos.map((_, i) => i).sort((a, b) => hz(a, 170) - hz(b, 170)).slice(0, nv);
          for (const i of orden) { const { B } = vendedores[i]; const [u, v] = B.lu(0, -1.25), [fu, fv] = B.lu(0, 1);
            gente.push({ q: "fijo", u, v, du: fu - u, dv: fv - v, pose: "atender" }); }
          let resto = npv - nv;
          if (resto > 0) { gente.push({ q: "fijo", u: -30.2 + 0.8 + 0.78, v: 11, du: -1, dv: 0, pose: { nombre: "descargar", alto: 1.2, alcance: 0.78, trecho: 0.9 } }); resto--; }
          if (resto > 0 && npv >= 6) { gente.push({ q: "tira", s0: rondaR.L * hz(3, 171), v: 1.05, pose: "caminar" }); resto--; }
          if (resto >= 2 && npv >= 10) {
            gente.push({ q: "fijo", u: -9.2, v: -6.4, du: 1, dv: 0.25, pose: "de_pie" }); gente.push({ q: "fijo", u: -7.9, v: -6.1, du: -1, dv: -0.25, pose: "de_pie" }); resto -= 2;
          }
          for (let i = 0; i < resto; i++) gente.push({ q: "ruta", ru: RUTAS[i % RUTAS.length], s0: hz(i, 172), v: 0.95 + 0.45 * hz(i, 173), sg: hz(i, 174) < 0.5 ? 1 : -1, pose: "caminar" });
        }
        const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: K, orden: 6, semilla: (p.semilla * 13 + np * 7) % 991,
          color: (i) => ROPA[(i * 3 + p.semilla) % ROPA.length], pose: (i) => gente[i].pose }) : null;
        const tira = gente.some((g) => g.q === "tira") ? hacerCarreta(false, 0.78) : null;
        return { id: p.id, M, r, ux, uy, W2, E, mats, uPx, uT, gente, flP, tira, rondaR };
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
            if (g.q === "fijo") {
              const [x, y] = s.W2(g.u, g.v), [dx, dy] = dW(g.du, g.dv), l = Math.hypot(dx, dy) || 1;
              s.flP.poner(i, x, y, dx / l, dy / l, 1, 0, 0);
              return;
            }
            if (g.q === "tira") {                                                     // jala el carretón por la ronda
              const R = s.rondaR, q = (((g.s0 + g.v * t) % R.L) + R.L) % R.L, [u, v, du, dv] = enRuta(R, q), [x, y] = s.W2(u, v), [dx, dy] = dW(du, dv);
              s.flP.poner(i, x, y, dx, dy, 1, 0, g.v * s.M / ctx.metros(1));
              const qc = q - 2.9 < 0 ? q - 2.9 + R.L : q - 2.9, qa = qc + 1.0 > R.L ? qc + 1.0 - R.L : qc + 1.0, qb = qc - 1.0 < 0 ? qc - 1.0 + R.L : qc - 1.0;
              const [cu, cv] = enRuta(R, qc), [au, av] = enRuta(R, qa), [bu, bv] = enRuta(R, qb), P = s.E(cu, cv, 0.06);
              s.tira.g.position.set(P[0], P[1], P[2]); s.tira.g.rotation.set(0, s.r + Math.atan2(av - bv, au - bu), 0);
              for (const w of s.tira.ruedas) w.rotation.z = -(g.s0 + g.v * t) / (0.75 * 0.78);
              return;
            }
            const ru = g.ru, L = ru.L || 1;
            let q = g.s0 * L + g.v * t * g.sg, sg = g.sg;
            if (ru.loop) q = ((q % L) + L) % L;
            else { const m = ((q % (2 * L)) + 2 * L) % (2 * L); q = m > L ? 2 * L - m : m; sg = g.sg * (m > L ? -1 : 1); }
            const [u, v, du, dv] = enRuta(ru, q), [x, y] = s.W2(u, v), [dx, dy] = dW(du * sg, dv * sg);
            s.flP.poner(i, x, y, dx, dy, 1, 0, g.v * s.M / ctx.metros(1));
          });
          s.flP.listo();
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
