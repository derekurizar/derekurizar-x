// Pieza «muelle» (ficha: muelle.json; reglas: scripts/maqueta_tipos/muelle.py): un muelle de carga genérico en la costa,
// centrado en `lugar` (la orilla) y orientado por `rumbo` (u: hacia el mar; v: a su izquierda). Todo en METROS × `tamano`.
// - La PLATAFORMA del patio (u −32…72, v −72…72) de concreto con sus juntas, rayas de carril y el contorno de los bloques, su
//   borde de piedra (escollera) hacia el mar y un talud hacia tierra.
// - El MUELLE de concreto (u 72…200, v −15…15) sobre pilotes, con su viga de borde, defensas y bitas en los DOS costados
//   (atraques a ambos lados): a la derecha un portacontenedores (objeto barco) amarrado con sus cabos; con `barcos` 2, a la
//   izquierda una barcaza de carga general (cajas y fardos con lona).
// - 1–2 GRÚAS MÓVILES de puerto (no pórtico): chasis sobre ruedas con estabilizadores, tornamesa, casa de máquinas con su
//   contrapeso, torre con cabina y pluma de celosía inclinada. Cada una gira (seek puro, ciclo de 20 s): toma un contenedor
//   del borde del muelle, lo sube, gira la pluma sobre el agua, lo baja al barco y vuelve; el siguiente aparece en el borde
//   mientras la pluma está sobre el barco.
// - El PATIO: dos bloques de contenedores de 20 pies apilados de 1 a 3 alturas (lisos, sin marca), el de la derecha con una
//   sección de REFRIGERADOS (claros, con su equipo de frío al frente) y su estructura de pasillos; un APILADOR (reach stacker)
//   que sube un contenedor a la tercera altura y luego lo vuelve a tomar (ciclo de 24 s, ida y vuelta: nada aparece).
// - CAMIONES con contenedor (cabezal + chasis + caja) que dan la vuelta del patio a la punta del muelle y regresan (posición =
//   función de t sobre el circuito) y otros en FILA en la calle de acceso, ante la PUERTA techada (marquesina, caseta y
//   plumas que suben y bajan). Una BODEGA de carga general de lámina con portones (uno abierto) y tarimas afuera.
// - La gente (objeto persona): estibadores que reciben la carga junto a la grúa (`atender`), un supervisor (`de_pie`) y
//   alguien que camina por el muelle.
// - De noche (ES.noche): postes de luz genéricos con su charco de luz, cabinas, ventanas de la bodega y de la caseta, faros y
//   pilotos de los camiones. Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto, marcas ni números.
(function (MAQ) {
  MAQ.PIEZAS.muelle = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      // ---- los tonos (todos del estilo)
      const cConc = tonos.pavimento.clone().lerp(tonos.muro, 0.15).multiplyScalar(dia ? 0.95 : oscuro ? 1.15 : 0.95);
      const cJunta = cConc.clone().multiplyScalar(0.78);
      const cCorte = tonos.pavimento.clone().lerp(tonos.asfalto, 0.3).multiplyScalar(oscuro ? 1.2 : 0.78);
      const cBorde = tonos.muro.clone().multiplyScalar(oscuro ? 1.15 : 1.02);
      const cPilote = tonos.pavimento.clone().lerp(tonos.asfalto, 0.45).multiplyScalar(0.8);
      const cRoca = tonos.arena.clone().lerp(tonos.asfalto, 0.45);
      const cTierra = tonos.arena.clone().lerp(lin(COL.tierra_media), 0.35).multiplyScalar(0.85);
      const cOsc = tonos.asfalto.clone().lerp(tonos.linea, 0.1).multiplyScalar(oscuro ? 1.0 : 0.5);
      const cMetal = tonos.asfalto.clone().lerp(tonos.pavimento, 0.45);
      const cRaya = tonos.medio.clone().lerp(tonos.muro, 0.2);
      const cRayaB = tonos.muro.clone().lerp(lin(COL.costa), 0.3).multiplyScalar(1.05);
      const cGrua = tonos.medio.clone().lerp(tonos.muro, 0.35);
      const cGruaO = cGrua.clone().multiplyScalar(0.62);
      const cMaq = tonos.bien.clone().lerp(tonos.muro, 0.45).multiplyScalar(0.9);
      const cLamina = tonos.muro.clone().lerp(tonos.secundario, 0.18);
      const cTecho = tonos.techo.clone().lerp(tonos.muro, 0.35);
      const cVidrio = noche ? lin(COL.luces).lerp(lin(COL.luz), 0.3) : tonos.agua.clone().lerp(tonos.linea, 0.3).multiplyScalar(0.7);
      const cHueco = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.6 : 0.35);
      const cMadera = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.55).multiplyScalar(oscuro ? 0.7 : 0.95);
      const cLona = tonos.secundario.clone().lerp(tonos.muro, 0.4).multiplyScalar(0.85);
      const cLlanta = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.75 : 0.35);
      const cCasco = tonos.linea.clone().lerp(tonos.muro, 0.5).multiplyScalar(0.8);
      const cLuz = lin(COL.luces);
      const CONT = [tonos.mal.clone().multiplyScalar(0.8), tonos.secundario.clone().multiplyScalar(0.85), tonos.medio.clone().multiplyScalar(0.85),
        tonos.linea.clone().lerp(lin(COL.costa), 0.45), tonos.bien.clone().multiplyScalar(0.75), lin(COL.costa).multiplyScalar(0.92)];
      const cReefer = tonos.muro.clone().lerp(lin(COL.costa), 0.35).multiplyScalar(oscuro ? 1.0 : 1.08);
      const VEH = tonos.vehiculos;
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const s3 = (x) => { const v = clamp(x, 0, 1); return v * v * (3 - 2 * v); };

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
      // una caja en los ejes de X(x, y, z) (y arriba)
      const bx = (acc, X, x0, x1, y0, y1, z0, z1, col, op = {}) => {
        const C = X((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
        const F = [[[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]], [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]],
          [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]],
          [[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]], [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]]];
        F.forEach((q, k) => {
          if ((k === 0 && op.sinTope) || (k === 5 && !op.fondo)) return;
          const V = q.map((a) => X(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
          cara(acc, V, k === 0 && op.tope ? op.tope : col, m);
        });
      };
      // un tubo de A a B (puntos de la malla), radio r (unidades de la malla), con tapas opcionales
      const tubo = (acc, A, B, r, seg, col, tapa) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2));
          if (tapa) { cara(acc, [S(B, va), S(B, vb), B, B], tapa, a); cara(acc, [S(A, va), S(A, vb), A, A], tapa, a.map((x) => -x)); }
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
      const XL = (x, y, z) => [x, y, z];
      // ---- un contenedor de 20 pies en los ejes de X (x a lo largo, y arriba, z a lo ancho; base en y = 0): panel, esquineros,
      // largueros, acanalado en los costados, puertas con sus barras al fondo (−x) y, si es refrigerado, su equipo de frío (+x)
      const CL = 6.06, CW = 2.44, CH = 2.59;
      const contenedor = (acc, X, col, reefer) => {
        const hl = CL / 2, ha = CW / 2, cP = col.clone().multiplyScalar(0.84), cR = col.clone().multiplyScalar(1.02), cM = col.clone().multiplyScalar(0.58);
        bx(acc, X, -hl + 0.06, hl - 0.06, 0.1, CH - 0.08, -ha + 0.05, ha - 0.05, cP, { tope: col.clone().multiplyScalar(0.95) });
        for (const sx of [-1, 1]) for (const sz of [-1, 1])
          bx(acc, X, sx > 0 ? hl - 0.16 : -hl, sx > 0 ? hl : -hl + 0.16, 0, CH, sz > 0 ? ha - 0.16 : -ha, sz > 0 ? ha : -ha + 0.16, cM);
        for (const sz of [-1, 1]) for (const y of [0, CH - 0.15]) bx(acc, X, -hl, hl, y, y + 0.15, sz > 0 ? ha - 0.12 : -ha, sz > 0 ? ha : -ha + 0.12, cM);
        const O = X(0, 0, 0);
        for (const sz of [-1, 1]) {
          const P1 = X(0, 0, sz), ref = [P1[0] - O[0], P1[1] - O[1], P1[2] - O[2]], z = sz * (ha - 0.02);
          for (let x = -hl + 0.42; x < hl - 0.3; x += 0.48) cara(acc, [X(x - 0.11, 0.2, z), X(x + 0.11, 0.2, z), X(x + 0.11, CH - 0.2, z), X(x - 0.11, CH - 0.2, z)], cR, ref);
        }
        const Pm = X(-1, 0, 0), refD = [Pm[0] - O[0], Pm[1] - O[1], Pm[2] - O[2]], xd = -hl - 0.012;
        for (const z of [-0.78, -0.3, 0.3, 0.78]) cara(acc, [X(xd, 0.18, z - 0.035), X(xd, 0.18, z + 0.035), X(xd, CH - 0.18, z + 0.035), X(xd, CH - 0.18, z - 0.035)], cM, refD);
        cara(acc, [X(xd, 0.18, -0.02), X(xd, 0.18, 0.02), X(xd, CH - 0.18, 0.02), X(xd, CH - 0.18, -0.02)], cM.clone().multiplyScalar(0.7), refD);
        if (reefer) {
          bx(acc, X, hl - 0.14, hl + 0.03, 0.32, CH - 0.32, -ha + 0.22, ha - 0.22, cOsc.clone().lerp(col, 0.3));
          const Pp = X(1, 0, 0), refF = [Pp[0] - O[0], Pp[1] - O[1], Pp[2] - O[2]], xf = hl + 0.04;
          for (let y = 0.55; y < CH - 0.5; y += 0.32) cara(acc, [X(xf, y, -ha + 0.32), X(xf, y, ha - 0.32), X(xf, y + 0.12, ha - 0.32), X(xf, y + 0.12, -ha + 0.32)], cM, refF);
          tubo(acc, X(xf, 1.85, 0.45), X(xf + 0.02, 1.85, 0.45), 0.36, 12, cM.clone().multiplyScalar(0.8), cOsc);   // el ventilador
        }
      };

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const XW = (x, y, z) => E(x, z, y);                                   // caja del mundo: x = u, y = h, z = v
        const cw = (acc, u0, u1, v0, v1, h0, h1, col, op) => bx(acc, XW, u0, u1, h0, h1, v0, v1, col, op);
        const twu = (acc, u0, v0, h0, u1, v1, h1, rr, seg, col, tapa) => tubo(acc, E(u0, v0, h0), E(u1, v1, h1), rr * M, seg, col, tapa);
        const losa = (acc, u0, u1, v0, v1, h, cu, cv, colf) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0);
          for (let i = 0, k = 0; i < nu; i++) for (let j = 0; j < nv; j++, k++) {
            const a = u0 + (u1 - u0) * i / nu, b = u0 + (u1 - u0) * (i + 1) / nu, e = v0 + (v1 - v0) * j / nv, f = v0 + (v1 - v0) * (j + 1) / nv;
            const cc = colf((a + b) / 2, (e + f) / 2, k), q = acc.pos.length / 3;
            for (const [uu, vv] of [[a, e], [b, e], [b, f], [a, f]]) { const P = E(uu, vv, h); acc.pos.push(P[0], P[1], P[2]); acc.col.push(cc.r * l, cc.g * l, cc.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        const raya = (acc, u0, v0, u1, v1, h, ancho, col, guion) => {     // una raya pintada (continua o a guiones)
          const L = Math.hypot(u1 - u0, v1 - v0) || 1, du = (u1 - u0) / L, dv = (v1 - v0) / L, nu = -dv * ancho / 2, nv = du * ancho / 2;
          const paso = guion ? guion * 2 : L;
          for (let s = 0; s < L - 0.01; s += paso) {
            const e = Math.min(L, s + (guion || L)), a = [u0 + du * s, v0 + dv * s], b = [u0 + du * e, v0 + dv * e];
            cara(acc, [E(a[0] + nu, a[1] + nv, h), E(b[0] + nu, b[1] + nv, h), E(b[0] - nu, b[1] - nv, h), E(a[0] - nu, a[1] - nv, h)], col, [0, 1, 0]);
          }
        };
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const nueva = (orden, op) => { const acc = malla.nueva(); acc._o = orden; acc._op = op || {}; return acc; };
        const fijas = [];
        const poner = (acc, op) => { const m = new THREE.Mesh(malla.geometria(acc), malla.material(op || {})); m.frustumCulled = false; m.renderOrder = acc._o || 3; scene.add(m); fijas.push(m.material); return m; };

        // ================= medidas del lugar
        const HD = 2.4, PU0 = -32, PU1 = 72, PV = 72, MU1 = 200, MV = 15;
        const NG = clamp(p.gruas | 0, 1, 2), NB = clamp(p.barcos | 0, 0, 2), NPER = clamp(p.personas | 0, 0, 4), NCAM = clamp(p.camiones | 0, 0, 6);
        const GU = NG === 2 ? [118, 165] : [132], GV = -9.5, GR = 17;
        const piso = nueva(2), solido = nueva(3), rayas = nueva(3), vid = nueva(4), conts = nueva(4), rocas = nueva(3);

        // ================= la plataforma y el muelle: losas, cantos, escollera, talud, pilotes, defensas y bitas
        const tonoLosa = (u, v, k) => cConc.clone().multiplyScalar(0.9 + 0.1 * ruido(u, v, 22, 11) + 0.05 * ruido(u, v, 4, 12) + 0.025 * hz(k, 13));
        losa(piso, PU0, PU1, -PV, PV, HD, 6, 6, tonoLosa);
        losa(piso, PU1, MU1, -MV, MV, HD, 6, 6, tonoLosa);
        cw(solido, PU0, PU1, -PV, PV, -1.6, HD, cCorte, { sinTope: true });
        cw(solido, PU1, MU1, -MV, MV, HD - 0.7, HD, cCorte, { sinTope: true });
        for (let u = PU0 + 6; u < PU1; u += 6) raya(rayas, u, -PV, u, PV, HD + 0.01, 0.06, cJunta);
        for (let v = -PV + 6; v < PV; v += 6) raya(rayas, PU0, v, PU1, v, HD + 0.01, 0.06, cJunta);
        for (let u = PU1 + 6; u < MU1; u += 6) raya(rayas, u, -MV, u, MV, HD + 0.01, 0.06, cJunta);
        // la viga de borde del muelle (dos costados y la punta) y el canto de la plataforma hacia el mar
        for (const s of [-1, 1]) cw(solido, PU1, MU1, s > 0 ? MV - 0.5 : -MV, s > 0 ? MV : -MV + 0.5, HD, HD + 0.3, cBorde);
        cw(solido, MU1 - 0.5, MU1, -MV, MV, HD, HD + 0.3, cBorde);
        for (const [a, b] of [[-PV, -MV], [MV, PV]]) cw(solido, PU1 - 0.5, PU1, a, b, HD, HD + 0.3, cBorde);
        // pilotes bajo el muelle
        for (let u = PU1 + 4; u < MU1; u += 8) for (const v of [-13.5, -4.5, 4.5, 13.5]) twu(solido, u, v, -1.5, u, v, HD - 0.7, 0.42, 10, cPilote, null);
        // defensas (cilindros de hule) y bitas en los dos costados
        for (let u = PU1 + 6; u < MU1 - 2; u += 12) for (const s of [-1, 1]) {
          twu(solido, u, s * (MV + 0.45), 0.3, u, s * (MV + 0.45), HD + 0.1, 0.45, 12, cLlanta, cLlanta);
          const vb = s * (MV - 1.1);
          twu(solido, u + 6, vb, HD, u + 6, vb, HD + 0.55, 0.28, 12, cOsc, cOsc);
          twu(solido, u + 6, vb, HD + 0.55, u + 6, vb, HD + 0.68, 0.4, 12, cOsc, cOsc);
        }
        // la escollera: piedras al pie de la plataforma, donde da al mar
        const piedras = (u0, v0, u1, v1, n, k0) => {
          for (let i = 0; i < n; i++) {
            const q = (i + hz(i, k0) * 0.6) / n, uu = u0 + (u1 - u0) * q, vv = v0 + (v1 - v0) * q, sale = 1.2 + 2.2 * hz(i, k0 + 1);
            const L = Math.hypot(u1 - u0, v1 - v0) || 1, nu = (v1 - v0) / L, nv = -(u1 - u0) / L;
            const rr = 0.8 + 0.9 * hz(i, k0 + 2);
            gema(rocas, E(uu + nu * sale, vv + nv * sale, 0.2 + 1.4 * (1 - sale / 3.6)), rr * M, rr * 0.7 * M, rr * 0.9 * M, hz(i, k0 + 3) * TAU,
              cRoca.clone().multiplyScalar(0.78 + 0.32 * hz(i, k0 + 4)));
          }
        };
        piedras(PU1, -PV, PU1, -MV, 34, 31); piedras(PU1, MV, PU1, PV, 34, 41);
        piedras(0, -PV, PU1, -PV, 46, 51); piedras(PU1, PV, 0, PV, 46, 61);
        // el talud hacia tierra
        { const P = [E(PU0, -PV, HD), E(PU0, PV, HD), E(PU0 - 7, PV, 0), E(PU0 - 7, -PV, 0)]; cara(solido, P, cTierra, [-ux, 0.5, uy]); }
        // la calle de acceso: de la plataforma a tierra por el costado derecho (v−), con su rampa
        const RU0 = -29, RU1 = -13, RV0 = -84, RV1 = -142;
        const hCalle = (v) => (v <= RV0 ? 0 : v >= -PV ? HD : HD * (v - RV0) / (-PV - RV0));
        { const q = piso.pos.length / 3, l = sombra(0, 1, 0), ca = tonos.asfalto.clone().lerp(cConc, 0.35);
          for (const [uu, vv] of [[RU0, -PV], [RU1, -PV], [RU1, RV0], [RU0, RV0], [RU0, RV0], [RU1, RV0], [RU1, RV1], [RU0, RV1]]) {
            const P = E(uu, vv, hCalle(vv) + 0.02); piso.pos.push(P[0], P[1], P[2]); piso.col.push(ca.r * l, ca.g * l, ca.b * l); }
          piso.idx.push(q, q + 1, q + 2, q, q + 2, q + 3, q + 4, q + 5, q + 6, q + 4, q + 6, q + 7); }
        for (const uu of [RU0 - 0.3, RU1]) cara(solido, [E(uu, -PV, HD), E(uu + 0.3, -PV, HD), E(uu + 0.3, RV0, 0), E(uu, RV0, 0)], cCorte, null);
        raya(rayas, -21, RV1, -21, RV0, 0.05, 0.18, cRayaB, 3);
        for (const uu of [RU0 + 0.5, RU1 - 0.5]) raya(rayas, uu, RV1, uu, RV0, 0.05, 0.15, cRayaB);

        // ================= las rayas: el circuito de los camiones (doble sentido), el pasillo de la grúa y los bloques
        const UA = -6, UB = 178, VR = -1, VLF = 9, RC = 5, VC = 4;
        raya(rayas, UA, VC, UB, VC, HD + 0.02, 0.18, cRaya, 3);
        for (const v of [-3, 11]) raya(rayas, UA, v, UB + 6, v, HD + 0.02, 0.15, cRayaB);
        raya(rayas, PU1, -4.4, MU1 - 1, -4.4, HD + 0.02, 0.25, cRaya);
        raya(rayas, -21, -50, -21, -8, HD + 0.02, 0.18, cRaya, 3);
        // ================= los bloques de contenedores: filas a lo largo de u, bahías a lo largo de v (el largo va en v)
        const FILAS = [0, 1, 2, 3, 4, 5].map((i) => 11.4 + 2.75 * i).concat([0, 1, 2, 3, 4, 5].map((i) => 34 + 2.75 * i));
        const BAHA = [0, 1, 2, 3, 4, 5].map((j) => 22 + 6.56 * j);
        const BAHR = [-22, -30.26, -36.82, -45.08];                         // la sección refrigerada: pasillos entre pares
        const APU = 11.4, APV = BAHA[2];                                    // la pila del apilador (fila 1, bahía 3): dos alturas
        const ponerCont = (acc, u, v, hb, col, reefer, alV, frente) => {
          const X = alV ? (x, y, z) => E(u - z, v + x * frente, hb + y) : (x, y, z) => E(u + x * frente, v + z, hb + y);
          contenedor(acc, X, col, reefer);
        };
        let nc = 0;
        const bloque = (bahias, filas, reef, k0) => {
          filas.forEach((u, i) => bahias.forEach((v, j) => {
            const k = k0 + i * 31 + j * 7, rf = reef;
            let n = hz(k, 81) < 0.07 ? 0 : 1 + Math.floor(hz(k, 82) * 3);
            if (Math.abs(u - APU) < 0.1 && Math.abs(v - APV) < 0.1) n = 2;
            if (rf && n === 0) n = 1;
            const frente = rf ? (j % 2 === 0 ? -1 : 1) : (hz(k, 85) < 0.5 ? 1 : -1);
            for (let l = 0; l < n; l++) {
              const col = rf ? cReefer.clone().multiplyScalar(0.92 + 0.12 * hz(k + l, 83)) : CONT[Math.floor(hz(k + l * 13, 84) * CONT.length)].clone().multiplyScalar(0.9 + 0.16 * hz(k + l, 86));
              ponerCont(conts, u + (hz(k + l, 87) - 0.5) * 0.12, v + (hz(k + l, 88) - 0.5) * 0.2, HD + l * CH, col, rf, true, frente);
              nc++;
            }
          }));
          // el contorno pintado del bloque
          const u0 = filas[0] - 1.6, u1 = filas[filas.length - 1] + 1.6, v0 = Math.min(...bahias) - 3.4, v1 = Math.max(...bahias) + 3.4;
          for (const [a, b, c, d] of [[u0, v0, u1, v0], [u1, v0, u1, v1], [u1, v1, u0, v1], [u0, v1, u0, v0]]) raya(rayas, a, b, c, d, HD + 0.02, 0.14, cRayaB);
        };
        bloque(BAHA, FILAS, false, 100);
        bloque(BAHA.map((v) => -v), FILAS.slice(0, 6), false, 900);
        bloque(BAHR, FILAS.slice(6), true, 1700);
        // la estructura de los refrigerados: columnas en los pasillos entre pares de bahías, pasarelas a 2 alturas y barandas
        for (const vg of [(BAHR[0] + BAHR[1]) / 2, (BAHR[2] + BAHR[3]) / 2]) {
          const u0 = FILAS[6] - 1.5, u1 = FILAS[11] + 1.5;
          for (let u = u0; u <= u1 + 0.01; u += (u1 - u0) / 3) for (const dv of [-0.9, 0.9]) twu(solido, u, vg + dv, HD, u, vg + dv, HD + 7.8, 0.1, 6, cMetal, null);
          for (const hh of [2.6, 5.2]) {
            cw(solido, u0, u1, vg - 0.95, vg + 0.95, HD + hh - 0.08, HD + hh, cMetal.clone().multiplyScalar(1.15));
            for (const dv of [-0.9, 0.9]) twu(solido, u0, vg + dv, HD + hh + 1.0, u1, vg + dv, HD + hh + 1.0, 0.05, 4, cMetal, null);
          }
          for (let k = 0; k < 8; k++) cw(solido, u0 - 1.6, u0 - 0.2, vg - 0.6, vg + 0.6, HD + k * 0.65, HD + k * 0.65 + 0.08, cMetal);   // la escalera
        }

        // ================= la bodega de carga general (lámina, cumbrera a lo largo de v, portones al frente +u)
        const BU0 = -31, BU1 = -11, BV0 = 24, BV1 = 64, BH = 8, BC = 10.6;
        cw(solido, BU0, BU1, BV0, BV1, HD, HD + BH, cLamina, { sinTope: true });
        { const Pa = [E(BU0 - 0.6, BV0 - 0.4, HD + BH), E(BU0 - 0.6, BV1 + 0.4, HD + BH), E((BU0 + BU1) / 2, BV1 + 0.4, HD + BC), E((BU0 + BU1) / 2, BV0 - 0.4, HD + BC)];
          const Pb = [E(BU1 + 0.6, BV0 - 0.4, HD + BH), E(BU1 + 0.6, BV1 + 0.4, HD + BH), E((BU0 + BU1) / 2, BV1 + 0.4, HD + BC), E((BU0 + BU1) / 2, BV0 - 0.4, HD + BC)];
          cara(solido, Pa, cTecho, [-ux, 1, uy]); cara(solido, Pb, cTecho, [ux, 1, -uy]);
          for (const vv of [BV0, BV1]) cara(solido, [E(BU0, vv, HD + BH), E(BU1, vv, HD + BH), E((BU0 + BU1) / 2, vv, HD + BC), E((BU0 + BU1) / 2, vv, HD + BC)], cLamina, null);
          // costuras de la lámina del techo y tragaluces
          for (let v = BV0 + 1; v < BV1; v += 1.2) for (const s of [-1, 1]) {
            const uM = (BU0 + BU1) / 2, uE = s > 0 ? BU1 + 0.6 : BU0 - 0.6, al = 0.02;
            const P = [E(uE, v - 0.05, HD + BH + al), E(uE, v + 0.05, HD + BH + al), E(uM, v + 0.05, HD + BC + al), E(uM, v - 0.05, HD + BC + al)];
            cara(rayas, P, cTecho.clone().multiplyScalar(1.15), [0, 1, 0]);
          }
          for (const vv of [32, 44, 56]) for (const s of [-1, 1]) {
            const uM = (BU0 + BU1) / 2, f0 = 0.3, f1 = 0.7, uA = uM + s * (BU1 - BU0) / 2 * f0, uB = uM + s * (BU1 - BU0) / 2 * f1;
            const hA = HD + BC - (BC - BH) * f0 + 0.05, hB = HD + BC - (BC - BH) * f1 + 0.05;
            cara(vid, [E(uA, vv - 1.5, hA), E(uA, vv + 1.5, hA), E(uB, vv + 1.5, hB), E(uB, vv - 1.5, hB)], cVidrio.clone().multiplyScalar(0.8), [0, 1, 0]);
          }
          cw(solido, (BU0 + BU1) / 2 - 0.4, (BU0 + BU1) / 2 + 0.4, BV0 - 0.4, BV1 + 0.4, HD + BC - 0.1, HD + BC + 0.15, cTecho.clone().multiplyScalar(0.8)); }
        // el acanalado de las paredes (+u, v−, v+) y los portones
        const PORT = [32, 44, 56];
        for (let v = BV0 + 0.4; v < BV1 - 0.2; v += 0.6) {
          if (PORT.some((pv) => Math.abs(v - pv) < 2.4)) { cara(rayas, [E(BU1 + 0.03, v - 0.08, HD + 5.4), E(BU1 + 0.03, v + 0.08, HD + 5.4), E(BU1 + 0.03, v + 0.08, HD + BH - 0.2), E(BU1 + 0.03, v - 0.08, HD + BH - 0.2)], cLamina.clone().multiplyScalar(1.12), [ux, 0, -uy]); continue; }
          cara(rayas, [E(BU1 + 0.03, v - 0.08, HD + 0.2), E(BU1 + 0.03, v + 0.08, HD + 0.2), E(BU1 + 0.03, v + 0.08, HD + BH - 0.2), E(BU1 + 0.03, v - 0.08, HD + BH - 0.2)], cLamina.clone().multiplyScalar(1.12), [ux, 0, -uy]);
        }
        for (const vv of [BV0 - 0.03, BV1 + 0.03]) for (let u = BU0 + 0.4; u < BU1 - 0.2; u += 0.6)
          cara(rayas, [E(u - 0.08, vv, HD + 0.2), E(u + 0.08, vv, HD + 0.2), E(u + 0.08, vv, HD + BH - 0.2), E(u - 0.08, vv, HD + BH - 0.2)], cLamina.clone().multiplyScalar(1.12), null);
        PORT.forEach((pv, k) => {
          const abierto = k === 1, uF = BU1 + 0.04;
          if (abierto) {
            cara(solido, [E(uF, pv - 2.3, HD), E(uF, pv + 2.3, HD), E(uF, pv + 2.3, HD + 5.2), E(uF, pv - 2.3, HD + 5.2)], cHueco, [ux, 0, -uy]);
            for (let i = 0; i < 4; i++) {   // tarimas con cajas, a la vista adentro
              const vv = pv - 1.4 + (i % 2) * 2.8, uu = BU1 - 1.2 - Math.floor(i / 2) * 2.0;
              cw(solido, uu - 0.6, uu + 0.6, vv - 0.6, vv + 0.6, HD, HD + 0.15, cMadera);
              cw(solido, uu - 0.55, uu + 0.55, vv - 0.55, vv + 0.55, HD + 0.15, HD + 1.1 + 0.4 * hz(i, 91), cLona.clone().lerp(cMadera, 0.5));
            }
          } else {
            cara(solido, [E(uF, pv - 2.3, HD), E(uF, pv + 2.3, HD), E(uF, pv + 2.3, HD + 5.2), E(uF, pv - 2.3, HD + 5.2)], cLamina.clone().multiplyScalar(0.8), [ux, 0, -uy]);
            for (let h = 0.4; h < 5.2; h += 0.4) cara(rayas, [E(uF + 0.02, pv - 2.25, HD + h), E(uF + 0.02, pv + 2.25, HD + h), E(uF + 0.02, pv + 2.25, HD + h + 0.06), E(uF + 0.02, pv - 2.25, HD + h + 0.06)], cLamina.clone().multiplyScalar(0.62), [ux, 0, -uy]);
          }
          cw(solido, BU1, BU1 + 0.25, pv - 2.6, pv - 2.3, HD, HD + 5.5, cOsc); cw(solido, BU1, BU1 + 0.25, pv + 2.3, pv + 2.6, HD, HD + 5.5, cOsc);
          cw(solido, BU1, BU1 + 0.25, pv - 2.6, pv + 2.6, HD + 5.2, HD + 5.5, cOsc);
          for (const dv of [-2.0, 2.0]) cw(solido, BU1, BU1 + 0.35, pv + dv - 0.25, pv + dv + 0.25, HD + 0.3, HD + 0.9, cLlanta);   // topes
        });
        cw(solido, BU1, BU1 + 3.2, BV0 + 2, BV1 - 2, HD + 6.0, HD + 6.25, cTecho.clone().multiplyScalar(0.9));   // la marquesina
        for (let v = BV0 + 4; v < BV1 - 2; v += 3.6) cara(vid, [E(BU1 + 0.05, v - 1.4, HD + 6.6), E(BU1 + 0.05, v + 1.4, HD + 6.6), E(BU1 + 0.05, v + 1.4, HD + 7.5), E(BU1 + 0.05, v - 1.4, HD + 7.5)], cVidrio, [ux, 0, -uy]);
        // tarimas de carga general afuera de la bodega (fardos y cajas, sin marca)
        for (let i = 0; i < 6; i++) {
          const uu = -8.2 + (i % 2) * 2.0, vv = 50 + Math.floor(i / 2) * 2.4, hh = 0.9 + 0.7 * hz(i, 92);
          cw(solido, uu - 0.6, uu + 0.6, vv - 0.6, vv + 0.6, HD, HD + 0.14, cMadera);
          cw(solido, uu - 0.55, uu + 0.55, vv - 0.55, vv + 0.55, HD + 0.14, HD + 0.14 + hh, (i % 3 ? cLona : cMadera.clone().multiplyScalar(1.1)).clone().multiplyScalar(0.9 + 0.15 * hz(i, 93)));
        }

        // ================= la puerta techada: marquesina en columnas, caseta y dos plumas (entrada y salida)
        const GV0 = -64, GV1 = -50;
        for (const uu of [-30, -21, -12]) for (const vv of [GV0 + 0.5, GV1 - 0.5]) cw(solido, uu - 0.3, uu + 0.3, vv - 0.3, vv + 0.3, HD, HD + 6.2, cMetal);
        cw(solido, -31, -11, GV0, GV1, HD + 6.2, HD + 6.9, cTecho.clone().lerp(cBorde, 0.4), { fondo: true });
        cw(solido, -31.1, -10.9, GV0 - 0.1, GV1 + 0.1, HD + 6.9, HD + 7.0, cBorde);
        cw(solido, -22.2, -19.8, -59.5, -54.5, HD, HD + 0.3, cBorde);
        cw(solido, -22, -20, -59, -55, HD + 0.3, HD + 2.9, cBorde.clone().multiplyScalar(0.92), { tope: cTecho });
        for (const uu of [-22.02, -19.98]) cara(vid, [E(uu, -58.5, HD + 1.4), E(uu, -55.5, HD + 1.4), E(uu, -55.5, HD + 2.5), E(uu, -58.5, HD + 2.5)], cVidrio, [uu < -21 ? -ux : ux, 0, uu < -21 ? uy : -uy]);
        for (const uu of [-25, -17]) for (const v of [GV0, GV1]) raya(rayas, uu - 2.2, v, uu + 2.2, v, HD + 0.02, 0.3, cRayaB);
        const plumas = [[-17 - 2.3, -49.5], [-25 + 2.3, -63.8]];
        for (const [uu, vv] of plumas) cw(solido, uu - 0.25, uu + 0.25, vv - 0.25, vv + 0.25, HD, HD + 1.1, cRaya);
        const plumaM = malla.nueva(); bx(plumaM, XL, 0, 3.9, -0.07, 0.07, -0.07, 0.07, cRayaB, {}); for (let x = 0.4; x < 3.8; x += 0.8) bx(plumaM, XL, x, x + 0.4, -0.075, 0.075, -0.075, 0.075, tonos.mal, {});
        const gPluma = malla.geometria(plumaM), matMov = malla.material(); fijas.push(matMov);
        const mPlumas = plumas.map(([uu, vv], i) => { const m = new THREE.Mesh(gPluma, matMov); m.frustumCulled = false; m.renderOrder = 4; const P = E(uu, vv, HD + 1.05); m.position.set(P[0], P[1], P[2]); m.scale.setScalar(M); scene.add(m); return { m, s: i ? -1 : 1 }; });

        // ================= las grúas móviles: chasis (fijo) y la superestructura que gira (malla propia por grúa)
        for (const gu of GU) {
          cw(solido, gu - 7.2, gu + 7.2, GV - 3.3, GV + 3.3, HD + 0.9, HD + 2.6, cGruaO, { tope: cGrua.clone().multiplyScalar(0.85) });
          for (let k = 0; k < 6; k++) for (const s of [-1, 1]) {   // las ruedas (ejes a lo ancho)
            const uu = gu - 6 + k * 2.4;
            twu(solido, uu, GV + s * 2.4, HD + 0.6, uu, GV + s * 3.4, HD + 0.6, 0.6, 12, cLlanta, cOsc);
          }
          for (const su of [-1, 1]) for (const sv of [-1, 1]) {   // los estabilizadores con su zapata
            const ua = gu + su * 5.6, va = GV + sv * 2.6, ub = gu + su * 7.6, vb = GV + sv * 4.6;
            twu(solido, ua, va, HD + 1.9, ub, vb, HD + 1.9, 0.38, 6, cGruaO, null);
            twu(solido, ub, vb, HD + 1.9, ub, vb, HD + 0.25, 0.22, 8, cMetal, null);
            cw(solido, ub - 0.8, ub + 0.8, vb - 0.8, vb + 0.8, HD, HD + 0.25, cOsc);
          }
          for (let k = 0; k < 5; k++) cw(solido, gu + 7.2, gu + 8.2, GV - 0.6 - 0.02, GV + 0.6, HD + k * 0.5, HD + k * 0.5 + 0.07, cMetal);   // la escalerilla
        }
        const superG = () => {
          const a = malla.nueva(), vg = malla.nueva(), X = XL;
          tubo(a, [0, 2.6, 0], [0, 3.5, 0], 3.1, 18, cGruaO, cGrua);
          bx(a, X, -8.2, 0.4, 3.5, 8.6, -2.7, 2.7, cGrua, { tope: cGrua.clone().multiplyScalar(1.1) });
          bx(a, X, -9.6, -8.2, 3.5, 7.6, -2.5, 2.5, cGruaO);
          for (let x = -7.4; x < -1.2; x += 0.75) for (const sz of [-1, 1]) cara(a, [[x, 5.0, sz * 2.72], [x + 0.4, 5.0, sz * 2.72], [x + 0.4, 7.6, sz * 2.72], [x, 7.6, sz * 2.72]], cGruaO, [0, 0, sz]);
          for (const sz of [-1, 1]) { tubo(a, [-8, 9.6, sz * 2.6], [0.2, 9.6, sz * 2.6], 0.05, 4, cMetal, null); for (let x = -8; x <= 0.2; x += 2.05) tubo(a, [x, 8.6, sz * 2.6], [x, 9.6, sz * 2.6], 0.05, 4, cMetal, null); }
          bx(a, X, -0.6, 1.6, 3.5, 22.6, -1.1, 1.1, cGrua);
          for (const [x, z] of [[-0.6, -1.1], [-0.6, 1.1], [1.6, -1.1], [1.6, 1.1]]) bx(a, X, x - 0.08, x + 0.08, 3.5, 22.6, z - 0.08, z + 0.08, cGruaO);
          for (let y = 5; y < 20; y += 1.6) bx(a, X, -0.75, -0.6, y, y + 0.06, -0.4, 0.4, cMetal);   // la escalera de la torre
          bx(a, X, 1.4, 3.9, 19.8, 22.6, -1.35, 1.35, cGrua.clone().multiplyScalar(1.08), { tope: cGruaO });
          cara(vg, [[3.92, 20.6, -1.2], [3.92, 20.6, 1.2], [3.92, 22.2, 1.2], [3.92, 22.2, -1.2]], cVidrio, [1, 0, 0]);
          for (const sz of [-1, 1]) cara(vg, [[2.0, 20.6, sz * 1.37], [3.7, 20.6, sz * 1.37], [3.7, 22.2, sz * 1.37], [2.0, 22.2, sz * 1.37]], cVidrio, [0, 0, sz]);
          // la pluma de celosía: de P0 a P1 (punta a GR m del centro y 30 m sobre la cubierta)
          const P0 = [2.0, 7.4], P1 = [GR, 30], L = Math.hypot(P1[0] - P0[0], P1[1] - P0[1]), d = [(P1[0] - P0[0]) / L, (P1[1] - P0[1]) / L], n = [-d[1], d[0]];
          const pt = (s, e, z) => [P0[0] + d[0] * s * L + n[0] * e, P0[1] + d[1] * s * L + n[1] * e, z];
          const ch = (s) => [[-0.75, -0.8], [-0.75, 0.8], [0.75, -0.8], [0.75, 0.8]].map(([e, z]) => pt(s, e * (1 - 0.45 * s), z * (1 - 0.35 * s)));
          for (let k = 0; k < 4; k++) tubo(a, ch(0)[k], ch(1)[k], 0.14, 6, cGrua, null);
          const NS = 14;
          for (let i = 0; i < NS; i++) {
            const A = ch(i / NS), B = ch((i + 1) / NS);
            for (const [p0, p1] of [[0, 1], [2, 3], [0, 2], [1, 3]]) tubo(a, A[p0], B[p1], 0.06, 4, cGrua, null);
            tubo(a, B[0], B[1], 0.05, 4, cGrua, null); tubo(a, B[2], B[3], 0.05, 4, cGrua, null);
          }
          bx(a, X, P1[0] - 0.5, P1[0] + 0.9, P1[1] - 1.0, P1[1] + 0.5, -0.7, 0.7, cGruaO);
          tubo(a, [P1[0] + 0.3, P1[1] - 0.2, -0.75], [P1[0] + 0.3, P1[1] - 0.2, 0.75], 0.75, 14, cMetal, cOsc);   // la roldana
          // cilindros de izaje y tirantes
          for (const sz of [-0.9, 0.9]) {
            const Bc = pt(0.3, -0.75, sz); tubo(a, [1.2, 4.2, sz], Bc, 0.32, 10, cMetal, null);
            const Bt = pt(0.62, 0.7, sz * 0.6); tubo(a, [0.5, 22.6, sz * 0.8], Bt, 0.06, 4, cOsc, null);
          }
          return [a, vg];
        };
        const [gSup, gSupV] = superG();
        const geoSup = malla.geometria(gSup), geoSupV = malla.geometria(gSupV), matSup = malla.material(), matSupV = malla.material(); fijas.push(matSup);
        // el spreader y la carga que cuelga (el contenedor con su largo a lo largo de u), y los cables
        const spr = malla.nueva(); bx(spr, XL, -3.1, 3.1, 0, 0.35, -1.25, 1.25, cGruaO); bx(spr, XL, -0.9, 0.9, 0.35, 0.95, -0.6, 0.6, cGrua);
        const geoSpr = malla.geometria(spr);
        const cab = malla.nueva(); for (const z of [-0.5, 0.5]) bx(cab, XL, -0.05, 0.05, 0, 1, z - 0.05, z + 0.05, cOsc);
        const geoCab = malla.geometria(cab);
        const gruas = GU.map((gu, i) => {
          const g = new THREE.Group(); g.add(new THREE.Mesh(geoSup, matSup)); g.add(new THREE.Mesh(geoSupV, matSupV));
          const P = E(gu, GV, HD); g.position.set(P[0], P[1], P[2]); g.scale.setScalar(M); scene.add(g);
          g.children.forEach((m) => { m.frustumCulled = false; m.renderOrder = 4; });
          const colC = CONT[(i * 2 + Math.floor(hz(i, 95) * CONT.length)) % CONT.length];
          const cc = malla.nueva(); contenedor(cc, XL, colC, false);
          const geoC = malla.geometria(cc);
          const mk = (geo) => { const m = new THREE.Mesh(geo, matMov); m.frustumCulled = false; m.renderOrder = 4; m.rotation.y = r; m.scale.setScalar(M); scene.add(m); return m; };
          return { gu, g, spr: mk(geoSpr), carga: mk(geoC), slot: mk(geoC), cab: mk(geoCab), ph: hz(i, 96) * 0.5 + i * 0.5 };
        });
        // buffer de contenedores quietos junto a cada grúa
        GU.forEach((gu, i) => { for (let l = 0; l < 2; l++) ponerCont(conts, gu - GR - 7.2, GV, HD + l * CH, CONT[(i + l * 3 + 1) % CONT.length], false, false, 1); });

        // ================= los barcos: el portacontenedores (objeto barco) a la derecha; con 2, la barcaza a la izquierda
        const BCU = 136, BK = 0.72, BCV = -(MV + 1.2 + 14 * BK);
        const flB = NB >= 1 ? ctx.flota("barco", 1, { tamano: K * BK, lev: 0, orden: 5, semilla: (p.semilla * 3 + 1) % 97, color: (i, vars) => vars[Math.floor(hz(2, 97) * vars.length)], luces: false }) : null;
        if (NB >= 1) for (const [ub, us] of [[BCU - 62, BCU - 50], [BCU + 60, BCU + 48], [BCU - 20, BCU - 8], [BCU + 22, BCU + 10]])
          twu(solido, ub, -MV + 1.1, HD + 0.6, us, BCV + 14 * BK - 0.6, 7.6, 0.07, 4, cOsc, null);
        if (NB >= 2) {
          const ZU0 = 92, ZU1 = 158, ZV0 = MV + 1.3, ZV1 = MV + 14.3;
          cw(solido, ZU0 + 3, ZU1 - 3, ZV0, ZV1, -0.4, 1.9, cCasco, { tope: cCasco.clone().multiplyScalar(1.15) });
          for (const [ua, ub] of [[ZU0, ZU0 + 3], [ZU1 - 3, ZU1]]) {
            const fr = ua === ZU0, uF = fr ? ZU0 : ZU1, uI = fr ? ZU0 + 3 : ZU1 - 3;
            cara(solido, [E(uI, ZV0, -0.4), E(uI, ZV1, -0.4), E(uF, ZV1, 1.9), E(uF, ZV0, 1.9)], cCasco.clone().multiplyScalar(0.85), [fr ? -ux : ux, -0.5, fr ? uy : -uy]);
            cara(solido, [E(uI, ZV0, 1.9), E(uI, ZV1, 1.9), E(uF, ZV1, 1.9), E(uF, ZV0, 1.9)], cCasco.clone().multiplyScalar(1.15), [0, 1, 0]);
            for (const vv of [ZV0, ZV1]) cara(solido, [E(uI, vv, -0.4), E(uI, vv, 1.9), E(uF, vv, 1.9), E(uF, vv, 1.9)], cCasco, null);
          }
          cw(solido, ZU0 + 2, ZU1 - 2, ZV0, ZV0 + 0.3, 1.9, 2.6, cCasco.clone().multiplyScalar(0.9)); cw(solido, ZU0 + 2, ZU1 - 2, ZV1 - 0.3, ZV1, 1.9, 2.6, cCasco.clone().multiplyScalar(0.9));
          for (let i = 0; i < 14; i++) {
            const uu = ZU0 + 8 + (i % 7) * 7.2, vv = ZV0 + 3.6 + Math.floor(i / 7) * 5.6, hh = 1.4 + 1.2 * hz(i, 98), lw = 2.4 + 1.2 * hz(i, 99);
            cw(solido, uu - lw, uu + lw, vv - 2.0, vv + 2.0, 1.9, 2.1, cMadera);
            cw(solido, uu - lw + 0.1, uu + lw - 0.1, vv - 1.9, vv + 1.9, 2.1, 2.1 + hh, (i % 3 === 0 ? cMadera.clone().multiplyScalar(1.12) : cLona).clone().multiplyScalar(0.9 + 0.18 * hz(i, 100)));
          }
          for (const [ub, us] of [[ZU0 + 4, ZU0 + 1], [ZU1 - 4, ZU1 - 1]]) twu(solido, ub, MV - 1.1, HD + 0.6, us, ZV0 + 0.3, 2.4, 0.07, 4, cOsc, null);
        }

        // ================= el apilador (reach stacker): cuerpo, cabina, ruedas; la pluma, el cilindro y el spreader se mueven
        const SX = 4.6;                                                    // del centro del apilador al centro del contenedor
        const apil = malla.nueva(), apilV = malla.nueva();
        { const X = XL, cA = cGrua.clone().lerp(tonos.mal, 0.25);
          bx(apil, X, -4.2, 2.8, 0.75, 1.95, -1.9, 1.9, cA, { tope: cA.clone().multiplyScalar(1.1) });
          bx(apil, X, -4.7, -3.6, 0.6, 2.8, -1.85, 1.85, cGruaO);
          bx(apil, X, -3.6, -1.0, 1.95, 2.7, -1.4, 1.4, cA.clone().multiplyScalar(0.9));
          bx(apil, X, -0.6, 1.3, 1.95, 4.0, 0.3, 1.9, cA.clone().multiplyScalar(0.8), { tope: cA });
          cara(apilV, [[1.32, 2.4, 0.4], [1.32, 2.4, 1.8], [1.32, 3.8, 1.8], [1.32, 3.8, 0.4]], cVidrio, [1, 0, 0]);
          cara(apilV, [[-0.4, 2.4, 1.92], [1.1, 2.4, 1.92], [1.1, 3.8, 1.92], [-0.4, 3.8, 1.92]], cVidrio, [0, 0, 1]);
          for (const s of [-1, 1]) {
            tubo(apil, [1.8, 0.95, s * 1.2], [1.8, 0.95, s * 2.1], 0.95, 14, cLlanta, cOsc);
            tubo(apil, [-3.0, 0.75, s * 1.35], [-3.0, 0.75, s * 2.0], 0.75, 14, cLlanta, cOsc);
          }
          bx(apil, X, 2.8, 3.05, 0.5, 0.9, -1.7, 1.7, cOsc); }
        const geoApil = malla.geometria(apil), geoApilV = malla.geometria(apilV);
        const pl = malla.nueva(); bx(pl, XL, 0, 1, -0.45, 0.45, -0.42, 0.42, cGrua.clone().lerp(tonos.mal, 0.25).multiplyScalar(0.85)); bx(pl, XL, 0.55, 1.0, -0.36, 0.36, -0.34, 0.34, cGruaO);
        const cil = malla.nueva(); bx(cil, XL, 0, 1, -0.15, 0.15, -0.15, 0.15, cMetal);
        const sprA = malla.nueva(); bx(sprA, XL, -1.1, 1.1, 0, 0.32, -3.0, 3.0, cGruaO); bx(sprA, XL, -0.5, 0.5, 0.32, 0.8, -0.5, 0.5, cGrua);
        const colA = CONT[Math.floor(hz(5, 101) * CONT.length)];
        const cA2 = malla.nueva(); contenedor(cA2, (x, y, z) => [z, y, x], colA, false);
        const gA = new THREE.Group(); scene.add(gA); gA.scale.setScalar(M);
        const mk2 = (geo, mat, par) => { const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = 4; (par || gA).add(m); return m; };
        mk2(geoApil, matMov); mk2(geoApilV, matSupV);
        const mBoom = mk2(malla.geometria(pl), matMov), mCil = mk2(malla.geometria(cil), matMov), mSprA = mk2(malla.geometria(sprA), matMov), mCargaA = mk2(malla.geometria(cA2), matMov);
        const cA3 = malla.nueva(); contenedor(cA3, (x, y, z) => E(APU - z, APV + x, HD + 2 * CH + y), colA, false);
        const mPila = new THREE.Mesh(malla.geometria(cA3), matMov); mPila.frustumCulled = false; mPila.renderOrder = 4; scene.add(mPila);
        // las claves del ciclo (24 s): [t, u del apilador, altura del fondo del contenedor sobre la cubierta, va enganchado]
        const KA = [[0, -6, 0.9, 1], [1, -6, 0.9, 1], [3.5, -6, 5.6, 1], [7, APU - SX, 5.6, 1], [8.5, APU - SX, 2 * CH, 1], [9, APU - SX, 2 * CH, 0],
          [10.5, APU - SX - 2.2, 5.9, 0], [12.5, APU - SX - 2.2, 5.9, 0], [14, APU - SX, 2 * CH, 0], [14.5, APU - SX, 2 * CH, 1], [16, APU - SX, 5.6, 1],
          [19.5, -6, 5.6, 1], [22, -6, 0.9, 1], [24, -6, 0.9, 1]];
        const PA = 24, FA = hz(6, 102) * PA;
        const apilador = (t) => {
          const tt = (((t + FA) % PA) + PA) % PA;
          let k = 0; while (k < KA.length - 2 && KA[k + 1][0] <= tt) k++;
          const a = KA[k], b = KA[k + 1], q = s3((tt - a[0]) / Math.max(1e-6, b[0] - a[0]));
          return { u: a[1] + (b[1] - a[1]) * q, hb: a[2] + (b[2] - a[2]) * q, eng: tt >= 9 && tt < 14.5 ? 0 : 1, v: (b[1] - a[1]) / Math.max(1e-6, b[0] - a[0]) };
        };

        // ================= los camiones: cabezal (malla por color) y chasis con su contenedor (malla por camión)
        const cabezal = (colC) => {
          const a = malla.nueva(), v = malla.nueva(), X = XL;
          bx(a, X, -3.1, 3.0, 0.75, 1.05, -0.5, 0.5, cOsc);
          bx(a, X, 0.9, 3.05, 1.05, 3.55, -1.22, 1.22, colC, { tope: colC.clone().multiplyScalar(1.1) });
          bx(a, X, 0.9, 2.5, 3.55, 3.95, -1.1, 1.1, colC.clone().multiplyScalar(0.9));
          bx(a, X, 3.05, 3.12, 1.1, 2.1, -0.85, 0.85, cOsc);
          bx(a, X, 2.95, 3.22, 0.5, 0.85, -1.25, 1.25, cMetal);
          cara(v, [[3.07, 2.35, -1.05], [3.07, 2.35, 1.05], [3.07, 3.3, 1.05], [3.07, 3.3, -1.05]], cVidrio, [1, 0, 0]);
          for (const s of [-1, 1]) cara(v, [[2.0, 2.35, s * 1.23], [2.9, 2.35, s * 1.23], [2.9, 3.3, s * 1.23], [2.0, 3.3, s * 1.23]], cVidrio, [0, 0, s]);
          for (const s of [-1, 1]) {
            tubo(a, [-0.3, 0.85, s * 1.0], [0.8, 0.85, s * 1.0], 0.3, 10, cMetal, cMetal);
            bx(a, X, 3.12, 3.2, 0.8, 1.0, s * 0.95 - 0.18, s * 0.95 + 0.18, cLuz);
            for (const x of [2.2, -1.4, -2.6]) tubo(a, [x, 0.52, s * 0.72], [x, 0.52, s * 1.22], 0.52, 12, cLlanta, cOsc);
            bx(a, X, -3.1, -0.9, 1.05, 1.15, s * 0.7, s * 1.3, cOsc);
          }
          tubo(a, [0.75, 1.0, 1.15], [0.75, 4.3, 1.15], 0.09, 8, cMetal, cOsc);
          bx(a, X, -2.6, -1.0, 1.05, 1.2, -0.9, 0.9, cOsc);
          return [malla.geometria(a), malla.geometria(v)];
        };
        const CABS = VEH.map((c) => cabezal(c.clone()));
        const chasis = (col) => {
          const a = malla.nueva(), X = XL;
          for (const s of [-1, 1]) bx(a, X, -3.95, 3.9, 1.0, 1.32, s * 0.45 - 0.08, s * 0.45 + 0.08, cOsc);
          for (const x of [-3.7, -1.2, 1.2, 3.6]) bx(a, X, x - 0.1, x + 0.1, 1.15, 1.35, -1.2, 1.2, cOsc);
          bx(a, X, -4.0, -3.85, 0.55, 0.95, -1.25, 1.25, cOsc);
          for (const s of [-1, 1]) {
            bx(a, X, -4.03, -3.98, 0.65, 0.85, s * 0.95 - 0.15, s * 0.95 + 0.15, tonos.mal);
            for (const x of [-2.4, -3.5]) tubo(a, [x, 0.52, s * 0.72], [x, 0.52, s * 1.22], 0.52, 12, cLlanta, cOsc);
            tubo(a, [2.0, 0.15, s * 0.8], [2.0, 1.0, s * 0.8], 0.07, 6, cMetal, null);
          }
          contenedor(a, (x, y, z) => [x - 0.4, y + 1.35, z], col, false);
          return malla.geometria(a);
        };
        const NM = Math.ceil(NCAM / 2), NQ = NCAM - NM;
        const SL = UB - UA, CC = Math.PI * RC, LT = 2 * SL + 2 * CC;
        const camino = (s) => {
          s = ((s % LT) + LT) % LT;
          if (s < SL) return [UA + s, VR, 0];
          s -= SL;
          if (s < CC) { const a = -Math.PI / 2 + s / RC; return [UB + RC * Math.cos(a), VC + RC * Math.sin(a), a + Math.PI / 2]; }
          s -= CC;
          if (s < SL) return [UB - s, VLF, Math.PI];
          s -= SL;
          const a = Math.PI / 2 + s / RC; return [UA + RC * Math.cos(a), VC + RC * Math.sin(a), a + Math.PI / 2];
        };
        const camiones = [];
        for (let i = 0; i < NCAM; i++) {
          const [gC, gV] = CABS[(i + Math.floor(hz(7, 103) * CABS.length)) % CABS.length];
          const col = CONT[(i * 2 + 1 + Math.floor(hz(i, 104) * 3)) % CONT.length];
          const mC = new THREE.Group(); mC.add(new THREE.Mesh(gC, matMov)); mC.add(new THREE.Mesh(gV, matSupV));
          const mT = new THREE.Mesh(chasis(col), matMov);
          for (const m of [mC.children[0], mC.children[1], mT]) { m.frustumCulled = false; m.renderOrder = 4; }
          mC.scale.setScalar(M); mT.scale.setScalar(M); scene.add(mC); scene.add(mT);
          camiones.push({ mC, mT, mov: i < NM, s0: (i / Math.max(1, NM)) * LT + hz(i, 105) * 12, vq: -90 - (i - NM) * 18.5 });
        }
        const VCAM = 3.6;

        // ================= los postes de luz (genéricos), sus charcos de luz de noche y las luces (puntos que brillan)
        const POSTES = [[60, VC], [95, VC], [135, VC], [175, VC], [30, VC], [-2, VC], [64, 64], [64, -64], [0, 66], [-6, -40], [-34, -96]];
        for (const [pu, pv] of POSTES) {
          const h0 = pv < -PV ? hCalle(pv) : HD;
          twu(solido, pu, pv, h0, pu, pv, h0 + 0.5, 0.45, 10, cBorde, cBorde);
          twu(solido, pu, pv, h0 + 0.5, pu, pv, h0 + 14, 0.16, 10, cMetal, cMetal);
          for (const s of [-1, 1]) { twu(solido, pu, pv, h0 + 13.6, pu + s * 1.4, pv, h0 + 14.1, 0.07, 4, cMetal, null); cw(solido, pu + s * 1.4 - 0.45, pu + s * 1.4 + 0.45, pv - 0.25, pv + 0.25, h0 + 13.85, h0 + 14.2, cMetal); }
        }
        const charco = malla.nueva();
        if (noche) for (const [pu, pv] of POSTES) {
          const h0 = (pv < -PV ? hCalle(pv) : HD) + 0.04, R = 13, n = 20, q = charco.pos.length / 3, nucleo = cLuz.clone().multiplyScalar(0.16);
          const C = E(pu, pv, h0); charco.pos.push(C[0], C[1], C[2]); charco.col.push(nucleo.r, nucleo.g, nucleo.b);
          for (let i = 0; i < n; i++) { const a = TAU * i / n, P = E(pu + R * Math.cos(a), pv + R * Math.sin(a), h0); charco.pos.push(P[0], P[1], P[2]); charco.col.push(0, 0, 0); }
          for (let i = 0; i < n; i++) charco.idx.push(q, q + 1 + i, q + 1 + ((i + 1) % n));
        }
        // las luces: postes (2 por poste), cabinas de grúa, faros y pilotos de camiones, faros del apilador
        const NLP = POSTES.length * 2, NLG = GU.length, NLC = NCAM * 4, NLA = 2, NLT = NLP + NLG + NLC + NLA;
        const gP = new THREE.BufferGeometry(), posP = new Float32Array(NLT * 3), aP = new Float32Array(NLT * 2);
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 2));
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: cLuz }, cB: { value: tonos.mal.clone() } },
          transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "attribute vec2 aK; uniform float uPx, uTam; varying vec2 vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " float m = aK.y < 0.5 ? 2.6 : (aK.y < 1.5 ? 1.3 : 0.7); gl_PointSize = aK.x > 0.0 ? clamp(m * uTam * uPx / max(1e-3, -mv.z), 2.0, 64.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA, cB; varying vec2 vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = vK.y < 1.5 ? cA : cB; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK.x * (exp(-r * r * 6.0) + 0.6 * exp(-r * r * 40.0)); gl_FragColor = vec4(s * a, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);
        POSTES.forEach(([pu, pv], i) => { const h0 = pv < -PV ? hCalle(pv) : HD; for (const s of [-1, 1]) { const P = E(pu + s * 1.4, pv, h0 + 13.75), j = i * 2 + (s > 0 ? 1 : 0); posP.set(P, j * 3); aP[j * 2] = noche ? 0.9 : 0; aP[j * 2 + 1] = 0; } });

        // ================= la sombra de contacto: rectángulos suaves bajo lo que se asienta
        const KS = ctx.CFG.sombra_contacto || (dia ? 0.4 : 0.22);
        const so = { pos: [], a: [], idx: [] };
        const sombraRect = (u0, u1, v0, v1, pad, h) => {
          const anillo = (d, al) => [[u0 - d, v0 - d], [u1 + d, v0 - d], [u1 + d, v1 + d], [u0 - d, v1 + d]].map(([u, v]) => ({ P: E(u, v, h + 0.03), a: al }));
          const I = anillo(0, 1), O = anillo(pad, 0), q = so.pos.length / 3;
          for (const x of I.concat(O)) { so.pos.push(...x.P); so.a.push(x.a); }
          so.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; so.idx.push(q + i, q + 4 + i, q + 4 + j, q + i, q + 4 + j, q + j); }
        };
        sombraRect(FILAS[0] - 1.3, FILAS[5] + 1.3, 18.9, BAHA[5] + 3.1, 1.2, HD); sombraRect(FILAS[6] - 1.3, FILAS[11] + 1.3, 18.9, BAHA[5] + 3.1, 1.2, HD);
        sombraRect(FILAS[0] - 1.3, FILAS[5] + 1.3, -BAHA[5] - 3.1, -18.9, 1.2, HD); sombraRect(FILAS[6] - 1.3, FILAS[11] + 1.3, BAHR[3] - 3.1, -18.9, 1.2, HD);
        sombraRect(BU0, BU1, BV0, BV1, 1.6, HD);
        for (const gu of GU) sombraRect(gu - 7.4, gu + 7.4, GV - 3.5, GV + 3.5, 1.4, HD);
        if (so.pos.length) {
          const gS = new THREE.BufferGeometry();
          gS.setAttribute("position", new THREE.BufferAttribute(new Float32Array(so.pos), 3));
          gS.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(so.a), 1));
          gS.setIndex(so.idx);
          const mS = new THREE.Mesh(gS, new THREE.ShaderMaterial({ uniforms: { uK: { value: KS * 0.7 } }, transparent: true, depthWrite: false,
            polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
            vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: "uniform float uK; varying float vA; void main(){ float a = uK * vA * vA; gl_FragColor = vec4(0.0, 0.0, 0.0, a); }" }));
          mS.frustumCulled = false; mS.renderOrder = 4; scene.add(mS);
        }

        // ================= las mallas fijas
        malla.poner(piso, malla.material({ desfase: 2 }), 2);
        poner(rayas, { desfase: 4 });
        poner(solido, { desfase: 1 });
        poner(rocas);
        poner(conts);
        const mVid = poner(vid, { desfase: 3 });
        if (noche) { const mC = new THREE.Mesh(malla.geometria(charco), malla.material({ aditivo: true, desfase: 5 })); mC.frustumCulled = false; mC.renderOrder = 5; scene.add(mC); }
        fijas.splice(fijas.indexOf(mVid.material), 1);
        const vidrios = [mVid.material, matSupV], BV = noche ? 1.7 : 1.0;

        // ================= la gente: estibadores junto a la grúa, el supervisor y quien camina por el muelle
        const camisas = [tonos.mal.clone(), tonos.medio.clone(), tonos.bien.clone(), lin(COL.costa).multiplyScalar(0.85)];
        const G0 = GU[0] - GR;
        const GENTE = [[G0 + 3.4, GV + 3.0, "atender"], [G0 - 3.6, GV + 3.0, "atender"], [G0 - 9.5, GV + 5.3, "de_pie"], [null, null, "caminar"]].slice(0, NPER);
        const flP = NPER ? ctx.flota("persona", NPER, { tamano: K * 1.35, lev: HD * K, orden: 6, semilla: p.semilla % 991, color: (i) => camisas[i % camisas.length],
          pose: (i) => GENTE[i][2] }) : null;

        return { id: p.id, K, M, r, ux, uy, E, W, HD, GV, GR, gruas, flB, BCU, BCV, flP, GENTE, G0, camiones, camino, VCAM, NM, apilador, gA, mBoom, mCil, mSprA, mCargaA, mPila, SX,
          mPlumas, posP, aP, gP, matP, NLP, NLG, noche, CH, s3, hCalle, mats: fijas.concat([matSup]), vidrios, BV, PU1 };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      const PI = Math.PI;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.4 * kb;
        for (const m of s.vidrios) m.uniforms.uBrillo.value = s.BV * (1 + 0.2 * kb);
        const { E, HD, GV, GR, CH, s3, r } = s;
        // dónde queda (u, v) de un punto local (x adelante, z a la derecha) de algo en (u0, v0) que mira a phi
        const loc = (u0, v0, phi, x, z) => [u0 + x * Math.cos(phi) + z * Math.sin(phi), v0 + x * Math.sin(phi) - z * Math.cos(phi)];
        let jl = s.NLP;
        const luz = (P, a, k) => { s.posP.set(P, jl * 3); s.aP[jl * 2] = s.noche ? a : 0; s.aP[jl * 2 + 1] = k; jl++; };
        // ---- las grúas: gira la pluma entre el borde del muelle (phi = π) y el barco (phi = 3π/2); el gancho sube y baja
        for (const g of s.gruas) {
          const f = (((t / 20 + g.ph) % 1) + 1) % 1, HUP = 19, HB = 6.0;
          let phi = PI, hb = HUP, carga = 0, kc = 1, slot = 1;
          if (f < 0.10) { hb = HUP + (HD - HUP) * s3(f / 0.10); }
          else if (f < 0.14) { hb = HD; }
          else if (f < 0.28) { hb = HD + (HUP - HD) * s3((f - 0.14) / 0.14); carga = 1; }
          else if (f < 0.50) { phi = PI + PI / 2 * s3((f - 0.28) / 0.22); carga = 1; }
          else if (f < 0.62) { phi = 1.5 * PI; hb = HUP + (HB - HUP) * s3((f - 0.50) / 0.12); carga = 1; kc = 1 - s3((f - 0.585) / 0.035); }
          else if (f < 0.66) { phi = 1.5 * PI; hb = HB; }
          else if (f < 0.74) { phi = 1.5 * PI; hb = HB + (HUP - HB) * s3((f - 0.66) / 0.08); }
          else if (f < 0.94) { phi = 1.5 * PI - PI / 2 * s3((f - 0.74) / 0.20); }
          if (f >= 0.14 && f < 0.80) slot = 0; else if (f >= 0.80 && f < 0.86) slot = s3((f - 0.80) / 0.06);
          g.g.rotation.y = r + phi;
          const [hu, hv] = [g.gu + GR * Math.cos(phi), GV + GR * Math.sin(phi)];
          const Ps = E(hu, hv, hb + CH); g.spr.position.set(Ps[0], Ps[1], Ps[2]);
          const top = HD + 30 - 1.2, cab = Math.max(0.1, top - (hb + CH + 0.95));
          const Pc = E(hu, hv, hb + CH + 0.95); g.cab.position.set(Pc[0], Pc[1], Pc[2]); g.cab.scale.set(s.M, s.M * cab, s.M);
          const Pg = E(hu, hv, hb); g.carga.position.set(Pg[0], Pg[1], Pg[2]); g.carga.scale.setScalar(s.M * (carga ? kc : 0) + 1e-6);
          const Pl = E(g.gu - GR, GV, HD); g.slot.position.set(Pl[0], Pl[1], Pl[2]); g.slot.scale.set(s.M * Math.max(1e-4, slot), s.M * Math.max(1e-4, slot), s.M * Math.max(1e-4, slot));
          const [cu, cv] = loc(g.gu, GV, phi, 3.9, 0); luz(E(cu, cv, HD + 21.4), 0.55, 1);
        }
        // ---- el barco amarrado
        if (s.flB) { const [x, y] = s.W(s.BCU, s.BCV); s.flB.poner(0, x, y, s.ux, s.uy, 1, 0); s.flB.listo(); }
        // ---- los camiones: los del circuito avanzan (posición = función de t); los de la fila esperan en la calle de acceso
        for (const c of s.camiones) {
          let cu, cv, ch, h, tu, tv, th, ht;
          if (c.mov) {
            const sp = c.s0 + s.VCAM * t, A = s.camino(sp), K1 = s.camino(sp - 1.8), K2 = s.camino(sp - 8.6);
            [cu, cv, ch] = A; th = Math.atan2(K1[1] - K2[1], K1[0] - K2[0]); tu = K1[0] - 3.2 * Math.cos(th); tv = K1[1] - 3.2 * Math.sin(th); h = HD; ht = HD;
          } else {
            cu = -17; cv = c.vq; ch = PI / 2; th = PI / 2; tu = -17; tv = c.vq - 5.0; h = s.hCalle(cv); ht = s.hCalle(tv);
          }
          const P = E(cu, cv, h), Q = E(tu, tv, ht);
          c.mC.position.set(P[0], P[1], P[2]); c.mC.rotation.set(0, r + ch, 0);
          c.mT.position.set(Q[0], Q[1], Q[2]); c.mT.rotation.set(0, r + th, Math.atan2(h - ht, 5.0) * (c.mov ? 0 : 1));
          for (const z of [-0.95, 0.95]) { const [a, b] = loc(cu, cv, ch, 3.2, z); luz(E(a, b, h + 0.9), 0.9, 1); }
          for (const z of [-0.95, 0.95]) { const [a, b] = loc(tu, tv, th, -4.05, z); luz(E(a, b, ht + 0.75), 0.8, 2); }
        }
        // ---- el apilador: avanza, sube el contenedor a la tercera altura, lo deja, se aparta, vuelve por él y retrocede
        { const A = s.apilador(t);
          const P = E(A.u, 22 + 6.56 * 2, HD); s.gA.position.set(P[0], P[1], P[2]); s.gA.rotation.y = r;
          const ytip = A.hb + CH + 0.85, piv = [-3.0, 3.2], dx = s.SX - piv[0], dy = ytip - piv[1], L = Math.hypot(dx, dy);
          s.mBoom.position.set(piv[0], piv[1], 0); s.mBoom.rotation.set(0, 0, Math.atan2(dy, dx)); s.mBoom.scale.set(L, 1, 1);
          const cb = [piv[0] + dx * 0.42, piv[1] + dy * 0.42 - 0.4], ca = [0.6, 1.95], cl = Math.hypot(cb[0] - ca[0], cb[1] - ca[1]);
          s.mCil.position.set(ca[0], ca[1], 0); s.mCil.rotation.set(0, 0, Math.atan2(cb[1] - ca[1], cb[0] - ca[0])); s.mCil.scale.set(cl, 1, 1);
          s.mSprA.position.set(s.SX, A.hb + CH, 0);
          s.mCargaA.position.set(s.SX, A.hb, 0); s.mCargaA.scale.setScalar(A.eng ? 1 : 1e-4);
          s.mPila.scale.setScalar(A.eng ? 1e-4 : 1);
          for (const z of [-1.5, 1.5]) { const [a, b] = loc(A.u, 22 + 6.56 * 2, 0, 3.0, z); luz(E(a, b, HD + 1.6), 0.7, 1); }
        }
        // ---- las plumas de la puerta: suben y bajan por turnos
        s.mPlumas.forEach((q, i) => { const f = (((t / 9 + i * 0.45) % 1) + 1) % 1, up = s3((f - 0.25) / 0.08) * (1 - s3((f - 0.62) / 0.08));
          q.m.rotation.set(0, r + (q.s > 0 ? 0 : PI), up * 1.35); });
        // ---- la gente
        if (s.flP) {
          s.GENTE.forEach((g, i) => {
            if (g[2] === "caminar") {
              const u0 = s.PU1 + 4, u1 = s.G0 - 12, L = Math.max(4, u1 - u0), per = 2 * L / 1.1, q = (((t / per + 0.3) % 1) + 1) % 1, ida = q < 0.5;
              const u = ida ? u0 + L * q * 2 : u1 - L * (q - 0.5) * 2, [x, y] = s.W(u, GV + 5.1);
              s.flP.poner(i, x, y, ida ? s.ux : -s.ux, ida ? s.uy : -s.uy, 1, 0, 1.1);
            } else {
              const [x, y] = s.W(g[0], g[1]), [tx, ty] = s.W(s.G0, GV), dx = tx - x, dy = ty - y, l = Math.hypot(dx, dy) || 1;
              s.flP.poner(i, x, y, dx / l, dy / l, 1, 0, 0);
            }
          });
          s.flP.listo();
        }
        s.gP.attributes.position.needsUpdate = true; s.gP.attributes.aK.needsUpdate = true;
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
