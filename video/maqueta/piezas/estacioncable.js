// Pieza «estacioncable» (ficha: estacioncable.json; reglas: scripts/maqueta_tipos/estacioncable.py): una estación genérica de
// teleférico urbano, centrada en `lugar` y orientada por `rumbo` (u: hacia donde sale el cable; v: a su izquierda). Todo en
// METROS × `tamano`. Nada afirma una línea real: ni su trazo, ni su color, ni su marca.
// - `obra`: el predio con VALLAS de lámina y su portón; la EXCAVACIÓN de la cimentación (fondo, tablestacas y barandal), seis
//   ZAPATAS con sus varillas de arranque, dos columnas (una encofrada) y una viga a medio hacer sobre puntales; la BASE DEL
//   MÁSTIL con sus pernos; montículos de tierra, una EXCAVADORA que gira entre la fosa y el montículo, un volteo estacionado,
//   pilas de varillas y de tablas, la CASETA de obra y REFLECTORES en postes. 0–2 GRÚAS TORRE de celosía: la pluma gira, el
//   carro corre y el gancho baja por un atado de varillas y lo deja en la fosa (ciclo de 26 s). Obreros sin rostro.
// - `lista`: la plaza adoquinada con jardineras, árboles, bancas y faroles; la ESTACIÓN ELEVADA (losa a 7 m sobre columnas
//   redondas, barandal de vidrio, cuarto de máquinas, techo en arco con costillas y tragaluz), la RUEDA horizontal que gira
//   bajo el techo, el riel de la estación y las CABINAS que entran despacio, dan la vuelta y salen por el cable (dos mástiles
//   tubulares con cruceta; el cable se pierde a 240 m: trazo ilustrativo); vestíbulo de vidrio, escalera y elevador; pasajeros.
// - De noche (ES.noche): la obra queda quieta (grúa y excavadora paradas, dos obreros de pie) con reflectores y su charco de
//   luz, la caseta encendida y la luz roja de la grúa; la estación con el vestíbulo, las cabinas, los faroles y el techo
//   encendidos y la luz roja de los mástiles. Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto, marcas ni números.
(function (MAQ) {
  MAQ.PIEZAS.estacioncable = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      // ---- los tonos (todos del estilo)
      const cConc = tonos.pavimento.clone().lerp(tonos.muro, 0.2).multiplyScalar(dia ? 0.98 : oscuro ? 1.15 : 0.95);
      const cConcO = cConc.clone().multiplyScalar(0.78);
      const cTierra = tonos.arena.clone().lerp(lin(COL.tierra_media), 0.45).multiplyScalar(oscuro ? 0.9 : 0.86);
      const cFosa = cTierra.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.72);
      const cGrava = tonos.pavimento.clone().lerp(tonos.arena, 0.4).multiplyScalar(0.9);
      const cOsc = tonos.asfalto.clone().lerp(tonos.linea, 0.1).multiplyScalar(oscuro ? 1.0 : 0.5);
      const cMetal = tonos.asfalto.clone().lerp(tonos.pavimento, 0.45);
      const cAcero = tonos.linea.clone().lerp(tonos.muro, 0.55).multiplyScalar(oscuro ? 1.0 : 0.85);
      const cVarilla = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.45).multiplyScalar(0.8);
      const cGrua = tonos.medio.clone().lerp(tonos.muro, 0.3);
      const cGruaO = cGrua.clone().multiplyScalar(0.62);
      const cValla = tonos.muro.clone().lerp(tonos.secundario, 0.22).multiplyScalar(oscuro ? 0.95 : 1.0);
      const cRaya = tonos.medio.clone().lerp(tonos.muro, 0.15);
      const cMadera = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.55).multiplyScalar(oscuro ? 0.75 : 1.0);
      const cTecho = tonos.muro.clone().lerp(tonos.linea, 0.25).multiplyScalar(oscuro ? 1.05 : 1.04);
      const cMuro = tonos.muro.clone().multiplyScalar(oscuro ? 1.0 : 0.97);
      const cAdoq = tonos.pavimento.clone().lerp(tonos.arena, 0.25);
      const cVerde = tonos.bien.clone().lerp(lin(COL.tierra_media), 0.35).multiplyScalar(0.75);
      const cVidrio = noche ? lin(COL.luces).lerp(lin(COL.luz), 0.3) : tonos.agua.clone().lerp(tonos.linea, 0.3).multiplyScalar(0.72);
      const cVidrioT = tonos.agua.clone().lerp(tonos.muro, 0.45).multiplyScalar(0.85);
      const cLlanta = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.75 : 0.35);
      const cLuz = lin(COL.luces);
      const CABS = [tonos.secundario.clone(), tonos.medio.clone().lerp(tonos.muro, 0.15), tonos.bien.clone().multiplyScalar(0.85), lin(COL.costa).multiplyScalar(0.9)];
      const oct = new THREE.OctahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
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
      const tubo = (acc, A, B, r, seg, col, tapa, r2) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const rb = r2 === undefined ? r : r2;
        const o = (t, rr) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * rr), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg;
          cara(acc, [S(A, o(t0, r)), S(A, o(t1, r)), S(B, o(t1, rb)), S(B, o(t0, rb))], col, o((t0 + t1) / 2, 1));
          if (tapa) { cara(acc, [S(B, o(t0, rb)), S(B, o(t1, rb)), B, B], tapa, a); cara(acc, [S(A, o(t0, r)), S(A, o(t1, r)), A, A], tapa, a.map((x) => -x)); }
        }
      };
      const gema = (acc, P, rx, ry, rz, rot, col) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), c = new THREE.Color();
        for (let i = 0; i < oct.length; i += 9) {
          const v = [];
          for (let j = 0; j < 9; j += 3) { const x = oct[i + j] * rx, y = Math.max(0, oct[i + j + 1]) * ry, z = oct[i + j + 2] * rz; v.push([P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr]); }
          const e1 = [v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]], e2 = [v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; c.copy(col).multiplyScalar(sombra(nx / n, Math.abs(ny / n), nz / n));
          const q = acc.pos.length / 3;
          for (const w of v) { acc.pos.push(w[0], w[1], w[2]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2);
        }
      };
      const XL = (x, y, z) => [x, y, z];

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K, obra = p.estado !== "lista";
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const hSuelo = (u, v) => { const [x, y] = W(u, v); return (ctx.altura(x, y) - base0) / M; };
        const XW = (x, y, z) => E(x, z, y);
        const cw = (acc, u0, u1, v0, v1, h0, h1, col, op) => bx(acc, XW, u0, u1, h0, h1, v0, v1, col, op);
        const twu = (acc, u0, v0, h0, u1, v1, h1, rr, seg, col, tapa, r2) => tubo(acc, E(u0, v0, h0), E(u1, v1, h1), rr * M, seg, col, tapa, r2 === undefined ? undefined : r2 * M);
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const losa = (acc, u0, u1, v0, v1, h, cu, cv, colf) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0);
          for (let i = 0, k = 0; i < nu; i++) for (let j = 0; j < nv; j++, k++) {
            const a = u0 + (u1 - u0) * i / nu, b = u0 + (u1 - u0) * (i + 1) / nu, e = v0 + (v1 - v0) * j / nv, f = v0 + (v1 - v0) * (j + 1) / nv;
            const cc = colf((a + b) / 2, (e + f) / 2, k), q = acc.pos.length / 3;
            for (const [uu, vv] of [[a, e], [b, e], [b, f], [a, f]]) { const P = E(uu, vv, h); acc.pos.push(P[0], P[1], P[2]); acc.col.push(cc.r * l, cc.g * l, cc.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        // un muro delgado de (u0, v0) a (u1, v1), de h0 a h1, grueso th
        const muro = (acc, u0, v0, u1, v1, h0, h1, th, col, tope) => {
          const L = Math.hypot(u1 - u0, v1 - v0) || 1, du = (u1 - u0) / L, dv = (v1 - v0) / L, nu = -dv * th / 2, nv = du * th / 2;
          const c = [[u0 + nu, v0 + nv], [u1 + nu, v1 + nv], [u1 - nu, v1 - nv], [u0 - nu, v0 - nv]], C = E((u0 + u1) / 2, (v0 + v1) / 2, (h0 + h1) / 2);
          for (let i = 0; i < 4; i++) {
            const a = c[i], b = c[(i + 1) % 4], V = [E(a[0], a[1], h0), E(b[0], b[1], h0), E(b[0], b[1], h1), E(a[0], a[1], h1)];
            cara(acc, V, col, [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]));
          }
          cara(acc, c.map((a) => E(a[0], a[1], h1)), tope || col, [0, 1, 0]);
        };
        const nueva = (orden) => { const acc = malla.nueva(); acc._o = orden; return acc; };
        const fijas = [];
        const poner = (acc, op) => { const m = new THREE.Mesh(malla.geometria(acc), malla.material(op || {})); m.frustumCulled = false; m.renderOrder = acc._o || 3; scene.add(m); fijas.push(m.material); return m; };
        const matMov = malla.material(), matMovV = malla.material(); fijas.push(matMov);
        const mk = (geo, mat, par) => { const m = new THREE.Mesh(geo, mat || matMov); m.frustumCulled = false; m.renderOrder = 4; (par || scene).add(m); return m; };
        const piso = nueva(2), solido = nueva(3), rayas = nueva(3), vid = nueva(4);
        const LUCES = [];                                   // [P, a, k]: k 0 = reflector/farol, 1 = luz chica, 2 = roja
        const charcos = [];                                 // [u, v, h, R]
        const NOB = clamp(p.obreros | 0, 0, 8);
        const camisas = [tonos.mal.clone(), tonos.medio.clone(), tonos.bien.clone(), lin(COL.costa).multiplyScalar(0.85), tonos.secundario.clone()];
        const SU = 42, SV = 30;
        const out = { id: p.id, K, M, r, ux, uy, E, W, obra, noche, s3 };

        if (obra) {
          // ================= el predio: tierra apisonada con su ruido de tono y el camino de grava del portón a la fosa
          const tonoT = (u, v, k) => cTierra.clone().multiplyScalar(0.86 + 0.16 * ruido(u, v, 14, 11) + 0.06 * ruido(u, v, 3, 12) + 0.03 * hz(k, 13));
          losa(piso, -SU, SU, -SV, SV, 0.04, 3, 3, tonoT);
          cw(solido, -SU, SU, -SV, SV, -1.6, 0.04, cTierra.clone().multiplyScalar(0.8), { sinTope: true });
          losa(piso, -SU, -16, -3.2, 3.2, 0.07, 2, 2, (u, v, k) => cGrava.clone().multiplyScalar(0.9 + 0.12 * hz(k, 14)));
          // ---- las vallas de lámina: paneles de 2.5 m con postes, zócalo y una franja; portón abierto en u = −SU
          const tramo = (u0, v0, u1, v1, k0) => {
            const L = Math.hypot(u1 - u0, v1 - v0), n = Math.max(1, Math.round(L / 2.5));
            for (let i = 0; i < n; i++) {
              const a = i / n, b = (i + 1) / n, ua = u0 + (u1 - u0) * a, va = v0 + (v1 - v0) * a, ub = u0 + (u1 - u0) * b, vb = v0 + (v1 - v0) * b;
              muro(solido, ua, va, ub, vb, 0.05, 2.4, 0.06, cValla.clone().multiplyScalar(0.93 + 0.1 * hz(i, k0)));
              muro(rayas, ua, va, ub, vb, 0.05, 0.35, 0.1, cConcO);
              muro(rayas, ua, va, ub, vb, 1.9, 2.1, 0.08, cRaya);
              twu(solido, ua, va, 0, ua, va, 2.55, 0.05, 6, cMetal, null);
            }
          };
          tramo(-SU, -SV, SU, -SV, 21); tramo(SU, -SV, SU, SV, 22); tramo(SU, SV, -SU, SV, 23);
          tramo(-SU, SV, -SU, 4, 24); tramo(-SU, -4, -SU, -SV, 25);
          muro(solido, -SU, 4, -SU + 3.2, 6.6, 0.05, 2.4, 0.06, cValla.clone().multiplyScalar(0.9));       // las hojas del portón, abiertas
          muro(solido, -SU, -4, -SU + 3.2, -6.6, 0.05, 2.4, 0.06, cValla.clone().multiplyScalar(0.9));

          // ================= la excavación: fondo, tablestacas, barandal
          const PX0 = -17, PX1 = 21, PY = 12.5;
          losa(piso, PX0, PX1, -PY, PY, 0.09, 2, 2, (u, v, k) => cFosa.clone().multiplyScalar(0.85 + 0.2 * ruido(u, v, 6, 15) + 0.04 * hz(k, 16)));
          const borde = [[PX0, -PY], [PX1, -PY], [PX1, PY], [PX0, PY]];
          for (let i = 0; i < 4; i++) {
            const [a, b] = [borde[i], borde[(i + 1) % 4]], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.round(L / 0.6);
            muro(solido, a[0], a[1], b[0], b[1], -0.4, 0.75, 0.25, cMetal.clone().multiplyScalar(0.9), cMetal);
            for (let k = 0; k < n; k++) { const q = (k + 0.5) / n, uu = a[0] + (b[0] - a[0]) * q, vv = a[1] + (b[1] - a[1]) * q;
              if (k % 2) muro(rayas, uu - (b[0] - a[0]) * 0.12 / L, vv - (b[1] - a[1]) * 0.12 / L, uu + (b[0] - a[0]) * 0.12 / L, vv + (b[1] - a[1]) * 0.12 / L, 0.0, 0.76, 0.33, cMetal.clone().multiplyScalar(0.7)); }
            const nb = Math.round(L / 3);
            for (let k = 0; k <= nb; k++) { const q = k / nb, uu = a[0] + (b[0] - a[0]) * q, vv = a[1] + (b[1] - a[1]) * q; twu(solido, uu, vv, 0.75, uu, vv, 1.85, 0.04, 5, cMetal, null); }
            for (const hh of [1.3, 1.82]) twu(rayas, a[0], a[1], hh, b[0], b[1], hh, 0.045, 5, hh > 1.5 ? cRaya : cValla, null);
          }
          // la rampa de bajada (tierra) del lado del portón
          cara(piso, [E(PX0 - 6, -3, 0.06), E(PX0, -3, 0.1), E(PX0, 3, 0.1), E(PX0 - 6, 3, 0.06)], cGrava.clone().multiplyScalar(0.85), [0, 1, 0]);

          // ================= las zapatas, las varillas de arranque, las columnas y la viga a medio hacer
          const CU = [-11, 0, 11], CV = [-7, 7];
          const varillas = (u, v, h0, h1, s) => { for (const du of [-1, 1]) for (const dv of [-1, 1]) for (const e of [0, 1]) {
            const uu = u + du * s * (e ? 0.45 : 1), vv = v + dv * s * (e ? 1 : 0.45); twu(solido, uu, vv, h0, uu, vv, h1, 0.035, 4, cVarilla, null); } };
          CU.forEach((u, a) => CV.forEach((v, b) => {
            const i = a * 2 + b;
            cw(solido, u - 1.8, u + 1.8, v - 1.8, v + 1.8, 0.09, 0.95, cConc, { tope: cConc.clone().multiplyScalar(1.06) });
            for (let k = -1; k <= 1; k++) { muro(rayas, u - 1.8, v + k * 1.2, u + 1.8, v + k * 1.2, 0.95, 1.0, 0.05, cVarilla); muro(rayas, u + k * 1.2, v - 1.8, u + k * 1.2, v + 1.8, 0.95, 1.0, 0.05, cVarilla); }
            if (a === 1) {                                   // las dos columnas del eje del medio: una encofrada, otra desnuda
              if (b === 0) {
                cw(solido, u - 0.62, u + 0.62, v - 0.62, v + 0.62, 0.95, 6.3, cMadera, { tope: cMadera.clone().multiplyScalar(0.8) });
                for (let h = 1.4; h < 6.2; h += 0.9) cw(rayas, u - 0.68, u + 0.68, v - 0.68, v + 0.68, h, h + 0.12, cMadera.clone().multiplyScalar(0.7));
                for (const [du, dv] of [[3.2, 0], [-3.2, 0], [0, 3.2], [0, -3.2]]) twu(solido, u + du, v + dv, 0.09, u + du * 0.2, v + dv * 0.2, 4.6, 0.06, 5, cMetal, null);
              } else cw(solido, u - 0.5, u + 0.5, v - 0.5, v + 0.5, 0.95, 6.3, cConc, { tope: cConcO });
              varillas(u, v, 6.0, 7.6, 0.38);
            } else {
              const hc = 1.3 + 1.6 * hz(i, 31);
              cw(solido, u - 0.5, u + 0.5, v - 0.5, v + 0.5, 0.95, hc, cConc.clone().multiplyScalar(0.95), { tope: cConcO });
              varillas(u, v, hc - 0.2, hc + 1.7, 0.38);
            }
          }));
          // la viga entre las dos columnas del medio: fondo de tablas sobre puntales, varillas a la vista
          cw(solido, -0.55, 0.55, -6.4, 6.4, 6.0, 6.25, cMadera, { fondo: true });
          for (const s of [-1, 1]) cw(solido, s > 0 ? 0.5 : -0.62, s > 0 ? 0.62 : -0.5, -6.4, 6.4, 6.25, 7.1, cMadera.clone().multiplyScalar(0.88));
          for (let v = -5.6; v <= 5.7; v += 1.6) for (const du of [-0.3, 0.3]) twu(solido, du, v, 0.09, du, v, 6.0, 0.05, 5, cMetal, null);
          for (const dz of [-0.25, 0.25]) for (const hh of [6.4, 6.95]) twu(solido, dz, -6.6, hh, dz, 6.6, hh, 0.03, 4, cVarilla, null);
          // atados de varillas quietos en la fosa (donde las grúas dejan su carga)
          const ATADO = (acc, X, col) => { for (let k = 0; k < 10; k++) { const z = -0.32 + (k % 5) * 0.16, y = 0.06 + Math.floor(k / 5) * 0.12; tubo(acc, X(-3, y, z), X(3, y, z), 0.05, 4, col, null); }
            for (const x of [-1.8, 1.8]) bx(acc, X, x - 0.06, x + 0.06, 0, 0.3, -0.42, 0.42, cOsc); };
          const GPOS = [[-27, -16], [30, -14]], DROPS = [[-7, 1.5], [8, -3.5]].map(([du, dv], i) => [du, dv, Math.atan2(dv - GPOS[i][1], du - GPOS[i][0]) + 0.4]);
          for (const [du, dv, a] of DROPS.slice(0, clamp(p.gruas | 0, 0, 2))) ATADO(solido, (x, y, z) => E(du + x * Math.cos(a) - z * Math.sin(a), dv + x * Math.sin(a) + z * Math.cos(a), 0.09 + y), cVarilla);

          // ================= la base del mástil: zapata cuadrada con sus cuatro grupos de pernos y la zanja alrededor
          const MU = 31, MV = 3;
          losa(piso, MU - 5, MU + 5, MV - 5, MV + 5, 0.06, 2, 2, () => cFosa.clone().multiplyScalar(0.95));
          cw(solido, MU - 3.6, MU + 3.6, MV - 3.6, MV + 3.6, 0.06, 0.8, cConc, { tope: cConc.clone().multiplyScalar(1.08) });
          cw(solido, MU - 1.6, MU + 1.6, MV - 1.6, MV + 1.6, 0.8, 1.3, cConc.clone().multiplyScalar(0.95), { tope: cConcO });
          for (const du of [-1, 1]) for (const dv of [-1, 1]) for (const a of [0, 1]) for (const b of [0, 1])
            twu(solido, MU + du * (0.9 + a * 0.35), MV + dv * (0.9 + b * 0.35), 1.3, MU + du * (0.9 + a * 0.35), MV + dv * (0.9 + b * 0.35), 1.75, 0.05, 6, cAcero, cOsc);
          for (const [a, b, c, d] of [[MU - 4.4, MV - 4.4, MU + 4.4, MV - 4.4], [MU + 4.4, MV - 4.4, MU + 4.4, MV + 4.4], [MU + 4.4, MV + 4.4, MU - 4.4, MV + 4.4], [MU - 4.4, MV + 4.4, MU - 4.4, MV - 4.4]]) {
            const n = 5; for (let k = 0; k <= n; k++) { const uu = a + (c - a) * k / n, vv = b + (d - b) * k / n; twu(solido, uu, vv, 0, uu, vv, 1.1, 0.04, 5, cRaya, null); }
            twu(rayas, a, b, 1.0, c, d, 1.0, 0.035, 4, cRaya, null);
          }

          // ================= montículos de tierra, pilas de varillas y tablas, tarimas de block
          const MONT = [[29, 22, 5.2, 2.8], [35, 15, 3.6, 2.0], [24, 26, 3.0, 1.6], [-30, 18.5, 2.6, 1.3]];
          MONT.forEach(([u, v, rr, hh], i) => { for (let k = 0; k < 5; k++) {
            const a = TAU * k / 5 + hz(i, 41) * 3, d = k ? rr * 0.45 : 0, s = k ? 0.65 : 1;
            gema(solido, E(u + d * Math.cos(a), v + d * Math.sin(a), 0.04), rr * s * M, hh * s * (0.85 + 0.3 * hz(i * 7 + k, 42)) * M, rr * s * 0.9 * M, hz(i * 7 + k, 43) * TAU, cTierra.clone().multiplyScalar(0.8 + 0.18 * hz(i * 7 + k, 44))); } });
          const PILAS = [[-31, -24.5, 0], [37, -24.5, 0]];
          for (const [u, v] of PILAS) {
            for (const du of [-3, 0, 3]) cw(solido, u + du - 0.15, u + du + 0.15, v - 1.2, v + 1.2, 0.04, 0.25, cMadera);
            for (let k = 0; k < 24; k++) { const vv = v - 1.0 + (k % 8) * 0.28, hh = 0.32 + Math.floor(k / 8) * 0.11; twu(solido, u - 4.5, vv, hh, u + 4.5, vv, hh, 0.05, 4, cVarilla.clone().multiplyScalar(0.9 + 0.15 * hz(k, 45)), null); }
          }
          for (let i = 0; i < 4; i++) { const u = -21 + i * 2.4, v = -25;
            cw(solido, u - 1.0, u + 1.0, v - 1.4, v + 1.4, 0.04, 0.18, cMadera);
            cw(solido, u - 0.95, u + 0.95, v - 1.3, v + 1.3, 0.18, 0.5 + 0.7 * hz(i, 46), cMadera.clone().multiplyScalar(1.15 + 0.1 * hz(i, 47))); }
          for (let i = 0; i < 3; i++) { const u = -7 + i * 2.2, v = -25.5;
            cw(solido, u - 0.9, u + 0.9, v - 0.9, v + 0.9, 0.04, 0.16, cMadera);
            for (let k = 0; k < 4; k++) cw(solido, u - 0.85, u + 0.85, v - 0.85, v + 0.85, 0.16 + k * 0.2, 0.34 + k * 0.2, cConc.clone().multiplyScalar(0.9 + 0.08 * (k % 2))); }

          // ================= la caseta de obra (contenedor oficina) con ventanas, puerta y escalón
          const KU0 = -40, KU1 = -34, KV0 = 15, KV1 = 27;
          for (const u of [KU0 + 0.6, KU1 - 0.6]) for (const v of [KV0 + 0.6, (KV0 + KV1) / 2, KV1 - 0.6]) cw(solido, u - 0.3, u + 0.3, v - 0.3, v + 0.3, 0.04, 0.45, cConc);
          cw(solido, KU0, KU1, KV0, KV1, 0.45, 3.1, cMuro, { fondo: true });
          cw(solido, KU0 - 0.2, KU1 + 0.2, KV0 - 0.2, KV1 + 0.2, 3.1, 3.3, cMuro.clone().multiplyScalar(0.85));
          for (let v = KV0 + 0.3; v < KV1; v += 0.5) cara(rayas, [E(KU1 + 0.02, v - 0.05, 0.6), E(KU1 + 0.02, v + 0.05, 0.6), E(KU1 + 0.02, v + 0.05, 3.0), E(KU1 + 0.02, v - 0.05, 3.0)], cMuro.clone().multiplyScalar(0.85), [ux, 0, -uy]);
          for (const v of [KV0 + 2.0, KV0 + 5.0, KV1 - 2.0]) {
            cara(vid, [E(KU1 + 0.04, v - 0.9, 1.5), E(KU1 + 0.04, v + 0.9, 1.5), E(KU1 + 0.04, v + 0.9, 2.5), E(KU1 + 0.04, v - 0.9, 2.5)], cVidrio, [ux, 0, -uy]);
            cw(solido, KU1, KU1 + 0.1, v - 1.0, v + 1.0, 1.42, 1.5, cOsc);
          }
          cara(solido, [E(KU1 + 0.05, 20.8, 0.5), E(KU1 + 0.05, 21.8, 0.5), E(KU1 + 0.05, 21.8, 2.6), E(KU1 + 0.05, 20.8, 2.6)], cOsc, [ux, 0, -uy]);
          cw(solido, KU1, KU1 + 1.1, 20.4, 22.2, 0.04, 0.25, cConc);
          // el tinaco y la unidad de aire sobre la caseta
          twu(solido, KU0 + 1.5, KV1 - 1.5, 3.3, KU0 + 1.5, KV1 - 1.5, 4.5, 0.6, 14, cOsc, cOsc);
          cw(solido, KU0 + 2.2, KU0 + 3.2, KV0 + 1, KV0 + 2, 3.3, 3.9, cMetal);
          LUCES.push([E(KU1 + 0.4, 21.3, 2.9), 0.6, 1]);

          // ================= la excavadora: oruga fija; la casa, la pluma, el brazo y el cucharón giran
          const XU = 25.5, XV = 15.5, XPH = Math.atan2(PY - 4 - XV, PX1 - 2 - XU);
          { const X = (x, y, z) => { const c = Math.cos(XPH), s = Math.sin(XPH); return E(XU + x * c + z * s, XV + x * s - z * c, y); };
            for (const zz of [-1.45, 1.45]) {
              bx(solido, X, -2.3, 2.3, 0.04, 0.85, zz - 0.35, zz + 0.35, cLlanta, { tope: cOsc });
              for (let x = -2.1; x <= 2.1; x += 0.35) bx(rayas, X, x - 0.06, x + 0.06, 0.82, 0.9, zz - 0.36, zz + 0.36, cOsc);
            }
            bx(solido, X, -1.2, 1.2, 0.5, 1.05, -1.1, 1.1, cOsc); }
          const ex = malla.nueva(), exV = malla.nueva();
          { const X = XL, cE = cGrua.clone().lerp(tonos.mal, 0.15);
            tubo(ex, [0, 0, 0], [0, 0.2, 0], 1.05, 16, cOsc, cOsc);
            bx(ex, X, -2.4, 0.4, 0.2, 1.5, -1.25, 1.25, cE, { tope: cE.clone().multiplyScalar(1.08) });
            bx(ex, X, -2.75, -2.2, 0.2, 1.4, -1.2, 1.2, cOsc.clone().lerp(cE, 0.4));
            for (let x = -2.1; x < -0.6; x += 0.3) bx(ex, X, x, x + 0.12, 0.7, 1.3, 1.26, 1.28, cOsc);
            bx(ex, X, -0.2, 1.3, 0.2, 2.55, 0.25, 1.25, cE.clone().multiplyScalar(0.92), { tope: cE });
            cara(exV, [[1.32, 1.0, 0.35], [1.32, 1.0, 1.15], [1.32, 2.4, 1.15], [1.32, 2.4, 0.35]], cVidrio, [1, 0, 0]);
            cara(exV, [[-0.1, 1.1, 1.27], [1.2, 1.1, 1.27], [1.2, 2.4, 1.27], [-0.1, 2.4, 1.27]], cVidrio, [0, 0, 1]);
            const sq = (A, B, w, col) => tubo(ex, A, B, w, 4, col, col);
            sq([0.4, 1.0, -0.35], [3.6, 4.0, -0.35], 0.32, cE); sq([3.6, 4.0, -0.35], [5.6, 4.3, -0.35], 0.28, cE);
            sq([5.6, 4.3, -0.35], [6.6, 1.6, -0.35], 0.22, cE);
            tubo(ex, [1.0, 1.0, -0.35], [3.0, 3.0, -0.35], 0.1, 8, cAcero, null);
            bx(ex, X, 6.2, 7.2, 0.8, 1.7, -0.85, 0.15, cOsc);
            for (let z = -0.75; z <= 0.1; z += 0.21) tubo(ex, [7.15, 0.85, z], [7.45, 0.6, z], 0.05, 4, cAcero, null);
          }
          const gEx = new THREE.Group(); scene.add(gEx); gEx.scale.setScalar(M);
          mk(malla.geometria(ex), matMov, gEx); mk(malla.geometria(exV), matMovV, gEx);
          const carga = malla.nueva(); gema(carga, [6.7, 1.55, -0.35], 0.55, 0.35, 0.5, 0.3, cTierra.clone().multiplyScalar(0.85));
          const mCarga = mk(malla.geometria(carga), matMov, gEx);
          { const P = E(XU, XV, 1.05); gEx.position.set(P[0], P[1], P[2]); }
          out.ex = { g: gEx, carga: mCarga, a: XPH, b: Math.atan2(22 - XV, 29 - XU) - 0.1 };

          // ================= las grúas torre: mástil de celosía fijo; la parte que gira (pluma, contrapluma, cabina) por grúa
          const HM = 34, GRUAS = GPOS.map(([gu, gv], i) => [gu, gv, Math.atan2(PILAS[i][1] - gv, PILAS[i][0] - gu), DROPS[i]]);
          const NG = clamp(p.gruas | 0, 0, 2), LG = GRUAS.slice(0, NG);
          for (const [gu, gv] of LG) {
            cw(solido, gu - 3, gu + 3, gv - 3, gv + 3, 0.04, 1.0, cConc, { tope: cConc.clone().multiplyScalar(1.05) });
            for (const du of [-1.9, 1.9]) cw(solido, gu + du - 0.9, gu + du + 0.9, gv - 2.6, gv + 2.6, 1.0, 2.0, cConcO, { tope: cConc });
            const ch = [[-0.85, -0.85], [0.85, -0.85], [0.85, 0.85], [-0.85, 0.85]];
            for (const [a, b] of ch) twu(solido, gu + a, gv + b, 1.0, gu + a, gv + b, HM, 0.1, 6, cGrua, null);
            for (let h = 1.0; h < HM - 0.5; h += 1.7) for (let k = 0; k < 4; k++) {
              const [a, b] = ch[k], [c, d] = ch[(k + 1) % 4];
              twu(solido, gu + a, gv + b, h, gu + c, gv + d, h, 0.05, 4, cGrua, null);
              twu(solido, gu + a, gv + b, h, gu + c, gv + d, h + 1.7, 0.04, 4, cGruaO, null);
            }
          }
          const sup = malla.nueva(), supV = malla.nueva();
          { const X = XL;
            tubo(sup, [0, 0, 0], [0, 0.8, 0], 1.3, 16, cGruaO, cGrua);
            for (const [a, b] of [[-0.8, -0.8], [0.8, -0.8], [0.8, 0.8], [-0.8, 0.8]]) tubo(sup, [a, 0.8, b], [0, 7.2, 0], 0.09, 6, cGrua, null);
            for (const h of [3, 5.2]) { const s = 0.8 * (1 - (h - 0.8) / 6.4); for (const [a, b, c, d] of [[-s, -s, s, -s], [s, -s, s, s], [s, s, -s, s], [-s, s, -s, -s]]) tubo(sup, [a, h, b], [c, h, d], 0.04, 4, cGrua, null); }
            bx(sup, X, 0.9, 2.7, -0.1, 2.4, 1.0, 2.7, cGrua.clone().multiplyScalar(1.05), { tope: cGruaO, fondo: true });
            cara(supV, [[2.72, 0.6, 1.1], [2.72, 0.6, 2.6], [2.72, 2.2, 2.6], [2.72, 2.2, 1.1]], cVidrio, [1, 0, 0]);
            cara(supV, [[1.0, 0.6, 2.72], [2.6, 0.6, 2.72], [2.6, 2.2, 2.72], [1.0, 2.2, 2.72]], cVidrio, [0, 0, 1]);
            const JL = 38, ch = (x) => [[x, 0.8, -0.75], [x, 0.8, 0.75], [x, 2.4, 0]];
            for (let k = 0; k < 3; k++) tubo(sup, ch(0)[k], ch(JL)[k], 0.08, 5, cGrua, null);
            for (let x = 0; x < JL; x += 2) { const A = ch(x), B = ch(x + 2);
              tubo(sup, A[0], A[1], 0.04, 4, cGrua, null); tubo(sup, A[0], B[2], 0.035, 4, cGruaO, null); tubo(sup, A[1], B[2], 0.035, 4, cGruaO, null); }
            bx(sup, X, JL - 0.4, JL + 0.3, 0.6, 2.4, -0.8, 0.8, cGruaO);
            for (const z of [-0.8, 0.8]) bx(sup, X, -13, 0, 0.55, 1.0, z - 0.15, z + 0.15, cGrua);
            for (let x = -12.5; x < 0; x += 1.2) bx(sup, X, x, x + 0.5, 1.0, 1.06, -0.8, 0.8, cMetal);
            bx(sup, X, -13.2, -10.6, -1.6, 1.6, -1.2, 1.2, cConc, { fondo: true, tope: cConc.clone().multiplyScalar(1.05) });
            for (let y = -1.2; y < 1.6; y += 0.7) bx(sup, X, -13.25, -10.55, y, y + 0.05, -1.25, 1.25, cConcO);
            bx(sup, X, -8.8, -6.6, 1.0, 2.0, -0.7, 0.7, cOsc, { tope: cMetal });
            for (const z of [-0.5, 0.5]) { tubo(sup, [0, 7.2, z * 0.2], [24, 2.4, 0], 0.04, 4, cOsc, null); tubo(sup, [0, 7.2, z * 0.2], [-12, 1.0, z * 1.4], 0.04, 4, cOsc, null); }
          }
          const geoSup = malla.geometria(sup), geoSupV = malla.geometria(supV);
          const car = malla.nueva(); bx(car, XL, -0.8, 0.8, -0.45, 0, -0.85, 0.85, cGruaO); for (const s of [-0.7, 0.7]) tubo(car, [-0.5, -0.1, s], [0.5, -0.1, s], 0.15, 8, cOsc, cOsc);
          const cab = malla.nueva(); for (const z of [-0.15, 0.15]) bx(cab, XL, -0.03, 0.03, 0, 1, z - 0.03, z + 0.03, cOsc);
          const gan = malla.nueva(); bx(gan, XL, -0.35, 0.35, 0, 0.7, -0.25, 0.25, cGrua.clone().lerp(tonos.mal, 0.4)); tubo(gan, [0, 0, 0], [0, -0.35, 0], 0.08, 6, cAcero, cAcero);
          const at = malla.nueva(); ATADO(at, (x, y, z) => [x, y - 0.75, z], cVarilla); for (const x of [-1.8, 1.8]) tubo(at, [0, -0.35, 0], [x, -0.65, 0], 0.025, 4, cOsc, null);
          const gCar = malla.geometria(car), gCab = malla.geometria(cab), gGan = malla.geometria(gan), gAt = malla.geometria(at);
          out.gruas = LG.map(([gu, gv, a0, dr], i) => {
            const g = new THREE.Group(); mk(geoSup, matMov, g); mk(geoSupV, matMovV, g);
            const P = E(gu, gv, HM); g.position.set(P[0], P[1], P[2]); g.scale.setScalar(M); scene.add(g);
            const sc = (m) => { m.scale.setScalar(M); return m; };
            const pick = Math.hypot(PILAS[i][0] - gu, PILAS[i][1] - gv), drop = Math.hypot(dr[0] - gu, dr[1] - gv), a1 = Math.atan2(dr[1] - gv, dr[0] - gu);
            let da = a1 - a0; while (da > Math.PI) da -= TAU; while (da < -Math.PI) da += TAU;
            LUCES.push([E(gu, gv, HM + 7.5), 0.9, 2]);
            return { gu, gv, g, car: sc(mk(gCar)), cab: sc(mk(gCab)), gan: sc(mk(gGan)), at: sc(mk(gAt)), a0, da, pick, drop, ph: i * 0.47 + hz(i, 51) * 0.1, HM };
          });

          // ================= los reflectores: postes en las esquinas, dos cabezas cada uno
          for (const [u, v] of [[-38, -26], [38, -26], [38, 26], [-30, 26]]) {
            twu(solido, u, v, 0.04, u, v, 0.5, 0.35, 10, cConc, cConc);
            twu(solido, u, v, 0.5, u, v, 9.5, 0.1, 8, cMetal, cMetal);
            const du = -Math.sign(u) * 0.5, dv = -Math.sign(v) * 0.5;
            twu(solido, u - dv, v + du, 9.3, u + dv, v - du, 9.3, 0.06, 5, cMetal, null);
            for (const s of [-1, 1]) { const uu = u - dv * s * 1.4 + du * 0.6, vv = v + du * s * 1.4 + dv * 0.6;
              cw(solido, uu - 0.35, uu + 0.35, vv - 0.35, vv + 0.35, 9.0, 9.6, cOsc); LUCES.push([E(uu + du * 0.4, vv + dv * 0.4, 9.2), 0.95, 0]); }
            charcos.push([u * 0.82, v * 0.8, 0.12, 15]);
          }

          // ================= el volteo estacionado junto al camino y los obreros
          out.flV = ctx.flota("volteo", 1, { tamano: K, lev: 0.05 * K, orden: 5, semilla: (p.semilla * 5 + 2) % 97, luces: false });
          out.volteo = [-27, 7.5, 0];
          const OB = [[null, null, "caminar"], [-2.4, -5.2, "atender", 0, -7], [9.3, 5.6, "cargar", 11, 7], [-9.5, 8.6, "de_pie", 0, 0],
            [8.6, -8.9, "atender", 11, -7], [-13.6, -3.2, "atender", -11, -7], [21.8, 9.6, "de_pie", XU, XV], [null, null, "caminar2"]].slice(0, NOB);
          out.OB = OB;
          out.flP = NOB ? ctx.flota("persona", NOB, { tamano: K * 1.3, lev: 0.1 * K, orden: 6, semilla: p.semilla % 991,
            color: (i) => camisas[i % camisas.length], pose: (i) => noche ? "de_pie" : (OB[i][2].startsWith("caminar") ? "caminar" : OB[i][2]) }) : null;
        } else {
          // ================= LISTA. La plaza: adoquín con su tono, bordillo, jardineras y bancas
          const tonoA = (u, v, k) => cAdoq.clone().multiplyScalar(0.9 + 0.08 * ((Math.round(u / 2.5) + Math.round(v / 2.5)) % 2 === 0 ? 1 : 0) + 0.06 * ruido(u, v, 12, 61) + 0.03 * hz(k, 62));
          losa(piso, -SU, SU, -SV, SV, 0.06, 2.5, 2.5, tonoA);
          cw(solido, -SU, SU, -SV, SV, -1.6, 0.06, cConcO, { sinTope: true });
          for (const [a, b, c, d] of [[-SU, -SV, SU, -SV], [SU, -SV, SU, SV], [SU, SV, -SU, SV], [-SU, SV, -SU, -SV]]) muro(solido, a, b, c, d, 0.0, 0.2, 0.35, cConc);
          // las sendas hacia el acceso (franjas de otro tono)
          losa(rayas, -SU, -14, -2.6, 2.6, 0.075, 2, 2, (u, v, k) => cConc.clone().multiplyScalar(0.98 + 0.05 * hz(k, 63)));
          for (const s of [-1, 1]) for (let u = -SU; u < -14; u += 1.2) cara(rayas, [E(u, s * 2.6 - 0.1, 0.08), E(u + 0.6, s * 2.6 - 0.1, 0.08), E(u + 0.6, s * 2.6 + 0.1, 0.08), E(u, s * 2.6 + 0.1, 0.08)], cConcO, [0, 1, 0]);
          const JARD = [[-30, -17, 9, 2.2], [-30, 17, 9, 2.2], [32, -21, 10, 2.2], [32, 21, 10, 2.2], [-24, -26, 12, 1.6], [-24, 26, 12, 1.6]];
          JARD.forEach(([u, v, l, a], i) => {
            cw(solido, u - l / 2, u + l / 2, v - a / 2, v + a / 2, 0.06, 0.6, cConc, { tope: cConc.clone().multiplyScalar(1.05) });
            losa(piso, u - l / 2 + 0.2, u + l / 2 - 0.2, v - a / 2 + 0.2, v + a / 2 - 0.2, 0.62, 1.2, 1.2, () => cTierra.clone().multiplyScalar(0.8));
            for (let k = 0; k < Math.round(l / 1.4); k++) gema(solido, E(u - l / 2 + 0.8 + k * 1.4, v + (hz(i * 9 + k, 64) - 0.5) * 0.4, 0.6), 0.75 * M, (0.6 + 0.4 * hz(i * 9 + k, 65)) * M, 0.65 * M, hz(k, 66) * TAU, cVerde.clone().multiplyScalar(0.85 + 0.25 * hz(i * 9 + k, 67)));
          });
          for (const [u, v] of [[-22, -9], [-22, 9], [-36, -9], [-36, 9]]) {
            for (const du of [-0.8, 0.8]) cw(solido, u + du - 0.1, u + du + 0.1, v - 0.25, v + 0.25, 0.06, 0.45, cMetal);
            cw(solido, u - 1.0, u + 1.0, v - 0.28, v + 0.28, 0.45, 0.55, cMadera);
            cw(solido, u - 1.0, u + 1.0, v + (v > 0 ? 0.2 : -0.28), v + (v > 0 ? 0.28 : -0.2), 0.55, 1.0, cMadera.clone().multiplyScalar(0.9));
          }
          out.arboles = [[-35, -22], [-35, 22], [-20, -22], [-20, 22], [36, -12], [36, 12], [26, -26], [26, 26]];
          out.flA = ctx.flota("arbol", out.arboles.length, { tamano: K * 1.1, lev: 0.06 * K, orden: 5, semilla: (p.semilla * 3 + 1) % 97 });

          // ================= la estación: columnas redondas con capitel, losa con su viga de borde, barandal de vidrio
          const D0 = 7.0, D1 = 7.9, U0 = -20, U1 = 24, VV = 10.5;
          for (const u of [-17, -6, 5, 16]) for (const v of [-7.5, 7.5]) {
            twu(solido, u, v, 0.05, u, v, 0.4, 0.85, 16, cConcO, cConc);
            twu(solido, u, v, 0.4, u, v, D0 - 0.6, 0.55, 16, cConc, null);
            twu(solido, u, v, D0 - 0.6, u, v, D0, 0.55, 16, cConc, null, 0.95);
          }
          cw(solido, U0, U1, -VV, VV, D0, D1, cConc, { fondo: true, tope: cConc.clone().multiplyScalar(1.05) });
          for (const v of [-VV, VV]) cw(rayas, U0 - 0.05, U1 + 0.05, v - 0.06, v + 0.06, D0 + 0.3, D0 + 0.45, cConcO);
          losa(piso, U0 + 0.3, U1 - 0.3, -VV + 0.3, VV - 0.3, D1 + 0.01, 1.5, 1.5, (u, v, k) => cConc.clone().lerp(cAdoq, 0.4).multiplyScalar(0.94 + 0.08 * hz(k, 68)));
          // franjas del andén (bordes de embarque)
          for (const s of [-1, 1]) for (const v of [s * 3.6, s * 7.4]) muro(rayas, -6, v, U1 - 1, v, D1, D1 + 0.03, 0.25, cRaya);
          const bar = (u0, v0, u1, v1) => {
            const L = Math.hypot(u1 - u0, v1 - v0), n = Math.max(1, Math.round(L / 1.6));
            for (let i = 0; i <= n; i++) { const uu = u0 + (u1 - u0) * i / n, vv = v0 + (v1 - v0) * i / n; twu(solido, uu, vv, D1, uu, vv, D1 + 1.1, 0.04, 5, cAcero, null); }
            twu(solido, u0, v0, D1 + 1.1, u1, v1, D1 + 1.1, 0.05, 6, cAcero, null);
            cara(vid, [E(u0, v0, D1 + 0.1), E(u1, v1, D1 + 0.1), E(u1, v1, D1 + 1.05), E(u0, v0, D1 + 1.05)], cVidrioT, null);
          };
          bar(-13, -VV + 0.1, 4, -VV + 0.1); bar(10, -VV + 0.1, U1 - 0.2, -VV + 0.1); bar(-13, VV - 0.1, U1 - 0.2, VV - 0.1);
          // el cuarto de máquinas al fondo, con su banda de ventanas
          cw(solido, U0, -15, -VV, VV, D1, 12.6, cMuro, { tope: cMuro.clone().multiplyScalar(0.9) });
          for (let v = -VV + 0.5; v < VV; v += 0.6) cara(rayas, [E(U0 - 0.03, v - 0.06, D1 + 0.2), E(U0 - 0.03, v + 0.06, D1 + 0.2), E(U0 - 0.03, v + 0.06, 12.4), E(U0 - 0.03, v - 0.06, 12.4)], cMuro.clone().multiplyScalar(0.86), [-ux, 0, uy]);
          for (const s of [-1, 1]) cara(vid, [E(U0 + 0.5, s * (VV + 0.03), 10.0), E(-15.5, s * (VV + 0.03), 10.0), E(-15.5, s * (VV + 0.03), 11.6), E(U0 + 0.5, s * (VV + 0.03), 11.6)], cVidrio, null);
          // el techo en arco con costillas, canalón y una franja de tragaluz; columnas del techo sobre la losa
          const TU0 = -21, TU1 = 27, TV = 11.8, hArco = (v) => 14 + 2.4 * (1 - (v / TV) * (v / TV));
          const NA = 12;
          for (let j = 0; j < NA; j++) {
            const v0 = -TV + 2 * TV * j / NA, v1 = -TV + 2 * TV * (j + 1) / NA, centro = Math.abs((v0 + v1) / 2) < 2.2;
            for (let u = TU0; u < TU1 - 0.01; u += 4) {
              const P = [E(u, v0, hArco(v0)), E(u + 4, v0, hArco(v0)), E(u + 4, v1, hArco(v1)), E(u, v1, hArco(v1))];
              cara(centro ? vid : solido, P, centro ? cVidrioT : cTecho.clone().multiplyScalar(0.96 + 0.06 * hz(j, 69)), [0, 1, 0]);
              cara(solido, P.map((q) => [q[0], q[1] - 0.25 * M, q[2]]), cTecho.clone().multiplyScalar(0.62), [0, -1, 0]);
            }
          }
          for (let u = TU0; u <= TU1 + 0.01; u += 4) for (let j = 0; j < NA; j++) {
            const v0 = -TV + 2 * TV * j / NA, v1 = -TV + 2 * TV * (j + 1) / NA;
            twu(solido, u, v0, hArco(v0) - 0.3, u, v1, hArco(v1) - 0.3, 0.14, 4, cAcero, null);
          }
          for (const s of [-1, 1]) {
            twu(solido, TU0, s * TV, 13.85, TU1, s * TV, 13.85, 0.22, 8, cAcero, cAcero);
            for (let u = -19; u <= 23; u += 7) { twu(solido, u, s * (VV - 0.35), D1, u, s * (VV - 0.35), 13.0, 0.22, 10, cAcero, null); twu(solido, u, s * (VV - 0.35), 13.0, u, s * (TV - 0.1), 13.9, 0.14, 6, cAcero, null); }
          }
          // el riel de la estación (en lazo) colgado del techo
          const HCS = 11.3, RW = 5.5, CW = -9;
          const lazo = [];
          for (let u = U1; u >= CW; u -= 3) lazo.push([u, RW]);
          for (let k = 1; k < 16; k++) { const a = Math.PI / 2 + Math.PI * k / 16; lazo.push([CW + RW * Math.cos(a), RW * Math.sin(a)]); }
          for (let u = CW; u <= U1; u += 3) lazo.push([u, -RW]);
          for (let i = 0; i + 1 < lazo.length; i++) { const [a, b] = [lazo[i], lazo[i + 1]]; twu(solido, a[0], a[1], HCS + 0.35, b[0], b[1], HCS + 0.35, 0.16, 4, cMetal, null); }
          for (let i = 0; i < lazo.length; i += 3) { const [u, v] = lazo[i]; twu(solido, u, v, HCS + 0.4, u, v, hArco(v) - 0.3, 0.06, 5, cAcero, null); }
          // la rueda: eje y motor fijos; el aro con sus rayos gira
          twu(solido, CW, 0, HCS + 0.5, CW, 0, hArco(0) - 0.3, 0.32, 12, cAcero, cAcero);
          for (const s of [-1, 1]) { twu(solido, U1, s * RW, HCS, U1 - 6, s * RW, HCS + 0.9, 0.13, 4, cOsc, null); twu(solido, U1 - 6, s * RW, HCS + 0.9, CW, s * RW, HCS + 0.9, 0.13, 4, cOsc, null); }
          cw(solido, CW - 1.4, CW + 1.4, -1.0, 1.0, 13.0, 14.6, cOsc, { tope: cMetal, fondo: true });
          const ru = malla.nueva();
          for (let k = 0; k < 32; k++) { const a = TAU * k / 32, b = TAU * (k + 1) / 32; tubo(ru, [RW * Math.cos(a), 0, RW * Math.sin(a)], [RW * Math.cos(b), 0, RW * Math.sin(b)], 0.26, 8, cGrua, null); }
          for (let k = 0; k < 32; k++) { const a = TAU * k / 32, b = TAU * (k + 1) / 32; tubo(ru, [(RW - 0.3) * Math.cos(a), -0.18, (RW - 0.3) * Math.sin(a)], [(RW - 0.3) * Math.cos(b), -0.18, (RW - 0.3) * Math.sin(b)], 0.08, 4, cOsc, null); }
          for (let k = 0; k < 8; k++) { const a = TAU * k / 8; tubo(ru, [0, 0, 0], [(RW - 0.2) * Math.cos(a), 0, (RW - 0.2) * Math.sin(a)], 0.1, 6, cGruaO, null); tubo(ru, [0, 0.4, 0], [(RW - 0.2) * Math.cos(a), 0, (RW - 0.2) * Math.sin(a)], 0.05, 4, cGruaO, null); }
          tubo(ru, [0, -0.3, 0], [0, 0.5, 0], 0.7, 16, cOsc, cMetal);
          const mRueda = mk(malla.geometria(ru)); mRueda.scale.setScalar(M);
          { const P = E(CW, 0, HCS + 0.9); mRueda.position.set(P[0], P[1], P[2]); }
          out.rueda = { m: mRueda, RW };
          // el vestíbulo de vidrio en la planta baja (marcos, losa, puertas)
          const VU0 = -14, VU1 = 2, VW = 5;
          cw(solido, VU0, VU1, -VW, VW, 0.06, 0.2, cConc);
          cw(solido, VU0 - 0.3, VU1 + 0.3, -VW - 0.3, VW + 0.3, 4.2, 4.6, cConc, { fondo: true, tope: cConcO });
          for (const [a, b, c, d] of [[VU0, -VW, VU1, -VW], [VU1, -VW, VU1, VW], [VU1, VW, VU0, VW], [VU0, VW, VU0, -VW]]) {
            cara(vid, [E(a, b, 0.2), E(c, d, 0.2), E(c, d, 4.2), E(a, b, 4.2)], cVidrio, null);
            const L = Math.hypot(c - a, d - b), n = Math.round(L / 2);
            for (let i = 0; i <= n; i++) { const uu = a + (c - a) * i / n, vv = b + (d - b) * i / n; twu(rayas, uu, vv, 0.2, uu, vv, 4.2, 0.06, 4, cOsc, null); }
            twu(rayas, a, b, 2.4, c, d, 2.4, 0.05, 4, cOsc, null);
          }
          cara(solido, [E(VU0 - 0.03, -1.6, 0.2), E(VU0 - 0.03, 1.6, 0.2), E(VU0 - 0.03, 1.6, 2.6), E(VU0 - 0.03, -1.6, 2.6)], cOsc.clone().multiplyScalar(0.8), [-ux, 0, uy]);
          cw(solido, VU0 - 2.5, VU0, -2.6, 2.6, 3.0, 3.25, cConc, { fondo: true });
          // los torniquetes y el mostrador adentro
          for (let k = 0; k < 4; k++) cw(solido, -8 - 0.15, -8 + 0.15, -3 + k * 2, -3 + k * 2 + 0.9, 0.2, 1.1, cAcero);
          cw(solido, -3, -1, -4.5, -1.5, 0.2, 1.2, cMadera);
          // la escalera al andén (al costado, v−) con sus barandales
          const EV0 = -10.9, EV1 = -13.2, EU0 = 25, EU1 = 7;
          const NS = 26;
          for (let k = 0; k < NS; k++) { const u = EU0 + (EU1 - EU0) * k / NS, h = D1 * (k + 1) / NS;
            cw(solido, Math.min(u, u + (EU1 - EU0) / NS), Math.max(u, u + (EU1 - EU0) / NS), EV1, EV0, h - 0.3, h, cConc.clone().multiplyScalar(0.95 + 0.06 * (k % 2))); }
          for (const v of [EV0, EV1]) {
            cara(solido, [E(EU0, v, 0), E(EU1, v, D1), E(EU1, v, D1 - 0.6), E(EU0 - 0.6, v, 0)], cConcO, null);
            twu(solido, EU0, v, 1.0, EU1, v, D1 + 1.0, 0.05, 6, cAcero, null);
            for (let k = 0; k <= 6; k++) { const q = k / 6; twu(solido, EU0 + (EU1 - EU0) * q, v, D1 * q, EU0 + (EU1 - EU0) * q, v, D1 * q + 1.0, 0.035, 4, cAcero, null); }
          }
          for (const u of [16, 7.3]) twu(solido, u, (EV0 + EV1) / 2, 0.05, u, (EV0 + EV1) / 2, D1 * (EU0 - u) / (EU0 - EU1) - 0.3, 0.2, 8, cConcO, null);
          // el elevador: cubo de vidrio con su marco
          const LU0 = -4, LU1 = -0.8, LV0 = 10.7, LV1 = 13.4, LH = D1 + 2.8;
          for (const [a, b] of [[LU0, LV0], [LU1, LV0], [LU1, LV1], [LU0, LV1]]) twu(solido, a, b, 0.06, a, b, LH, 0.08, 4, cAcero, null);
          for (const [a, b, c, d] of [[LU0, LV1, LU1, LV1], [LU1, LV0, LU1, LV1], [LU0, LV0, LU0, LV1]]) cara(vid, [E(a, b, 0.1), E(c, d, 0.1), E(c, d, LH), E(a, b, LH)], cVidrioT, null);
          cw(solido, LU0 - 0.1, LU1 + 0.1, LV0 - 0.1, LV1 + 0.1, LH, LH + 0.3, cMuro);
          for (let h = 3; h < LH; h += 3) twu(rayas, LU0, LV1, h, LU1, LV1, h, 0.05, 4, cAcero, null);

          // ================= el cable y sus mástiles: el trazo es ilustrativo (sale hacia `rumbo` y se pierde a 240 m)
          const LEND = 240, TOR = [[70, 26], [150, 33], [230, 38]];
          const SOP = [[U1, HCS]].concat(TOR).concat([[LEND, 38.6]]);
          const hLinea = (u) => {
            if (u <= U1) return HCS;
            for (let i = 0; i + 1 < SOP.length; i++) {
              const [a, ha] = SOP[i], [b, hb] = SOP[i + 1];
              if (u <= b) { const q = (u - a) / (b - a); return ha + (hb - ha) * q - 0.022 * (b - a) * 4 * q * (1 - q); }
            }
            return SOP[SOP.length - 1][1];
          };
          for (const s of [-1, 1]) for (let u = U1; u < LEND; u += 2) twu(solido, u, s * RW, hLinea(u), u + 2, s * RW, hLinea(u + 2), 0.13, 4, cOsc, null);
          for (const [tu, th] of TOR) {
            const hg = hSuelo(tu, 0);
            cw(solido, tu - 2.4, tu + 2.4, -2.4, 2.4, hg - 0.5, hg + 0.5, cConc, { tope: cConc.clone().multiplyScalar(1.05) });
            twu(solido, tu, 0, hg + 0.5, tu, 0, th - 1.3, 1.05, 16, cAcero, null, 0.6);
            cw(solido, tu - 0.6, tu + 0.6, -RW - 1.6, RW + 1.6, th - 1.6, th - 0.9, cAcero.clone().multiplyScalar(0.9), { fondo: true });
            for (const s of [-1, 1]) {
              cw(solido, tu - 2.4, tu + 2.4, s * RW - 0.25, s * RW + 0.25, th - 0.9, th - 0.45, cOsc, { fondo: true });
              for (const du of [-1.6, -0.55, 0.55, 1.6]) twu(solido, tu + du, s * RW - 0.2, th - 0.2, tu + du, s * RW + 0.2, th - 0.2, 0.22, 10, cMetal, cOsc);
            }
            for (let h = hg + 2; h < th - 2; h += 0.6) cw(rayas, tu - 0.75 - 0.1, tu - 0.75, -0.25, 0.25, h, h + 0.05, cOsc);
            LUCES.push([E(tu, 0, th - 0.4), 0.8, 2]);
          }
          out.hLinea = hLinea;
          // las cabinas: un lazo con tramos lentos en la estación (las cabinas se juntan adentro)
          const SEG = [];
          const seg = (len, f, fn) => SEG.push({ len, f, fn });
          seg(LEND - U1, 1, (q) => { const u = LEND - q * (LEND - U1); return [u, RW, hLinea(u), Math.PI]; });
          seg(8, 0.5, (q) => [U1 - 8 * q, RW, HCS, Math.PI]);
          seg(U1 - 8 - CW, 0.22, (q) => [U1 - 8 - (U1 - 8 - CW) * q, RW, HCS, Math.PI]);
          seg(Math.PI * RW, 0.22, (q) => { const a = Math.PI / 2 + Math.PI * q; return [CW + RW * Math.cos(a), RW * Math.sin(a), HCS, a + Math.PI / 2]; });
          seg(U1 - 8 - CW, 0.22, (q) => [CW + (U1 - 8 - CW) * q, -RW, HCS, 0]);
          seg(8, 0.5, (q) => [U1 - 8 + 8 * q, -RW, HCS, 0]);
          seg(LEND - U1, 1, (q) => { const u = U1 + q * (LEND - U1); return [u, -RW, hLinea(u), 0]; });
          let VL = 0; for (const s of SEG) { s.v0 = VL; VL += s.len / s.f; }
          const NCAB = Math.max(6, Math.round(VL / 38));
          const cb = malla.nueva(), cbV = malla.nueva(), cCab = CABS[Math.floor(hz(3, 71) * CABS.length)];
          { const X = XL, y0 = -3.3, y1 = -1.25;
            bx(cb, X, -1.15, 1.15, y0, y0 + 0.55, -1.0, 1.0, cCab.clone().multiplyScalar(0.8), { fondo: true });
            bx(cb, X, -1.2, 1.2, y0 + 0.55, y0 + 0.75, -1.05, 1.05, cCab);
            for (const [a, b] of [[-1.15, -1.0], [1.15, -1.0], [1.15, 1.0], [-1.15, 1.0]]) bx(cb, X, a - 0.08, a + 0.08, y0 + 0.75, y1 - 0.25, b - 0.08, b + 0.08, cCab);
            for (const x of [0]) bx(cb, X, x - 0.05, x + 0.05, y0 + 0.75, y1 - 0.25, -1.03, 1.03, cCab);
            bx(cb, X, -1.2, 1.2, y1 - 0.25, y1, -1.05, 1.05, cCab, { tope: cCab.clone().multiplyScalar(1.1) });
            bx(cb, X, -0.7, 0.7, y1, y1 + 0.12, -0.6, 0.6, cMetal);
            for (const [x, z, n] of [[1.13, 0, [1, 0, 0]], [-1.13, 0, [-1, 0, 0]]]) cara(cbV, [[x, y0 + 0.78, -0.95], [x, y0 + 0.78, 0.95], [x, y1 - 0.28, 0.95], [x, y1 - 0.28, -0.95]], cVidrio, n);
            for (const z of [-0.98, 0.98]) cara(cbV, [[-1.1, y0 + 0.78, z], [1.1, y0 + 0.78, z], [1.1, y1 - 0.28, z], [-1.1, y1 - 0.28, z]], cVidrio, [0, 0, Math.sign(z)]);
            tubo(cb, [0, y1 + 0.1, 0], [0, -0.45, 0], 0.07, 6, cAcero, null);
            tubo(cb, [0, -0.45, 0], [0, -0.1, -0.25], 0.06, 6, cAcero, null);
            bx(cb, X, -0.35, 0.35, -0.2, 0.15, -0.35, 0.05, cOsc);
          }
          const gCb = malla.geometria(cb), gCbV = malla.geometria(cbV);
          out.cabinas = [];
          for (let i = 0; i < NCAB; i++) { const g = new THREE.Group(); mk(gCb, matMov, g); mk(gCbV, matMovV, g); g.scale.setScalar(M); scene.add(g); out.cabinas.push(g); }
          Object.assign(out, { SEG, VL, NCAB, LEND });
          // los faroles de la plaza y las luces bajo el techo
          for (const [u, v] of [[-40, -12], [-40, 12], [-28, -28], [-28, 28], [10, -28], [10, 28], [38, -28], [38, 28]]) {
            twu(solido, u, v, 0.06, u, v, 0.5, 0.22, 10, cConcO, cConcO);
            twu(solido, u, v, 0.5, u, v, 5.5, 0.08, 8, cMetal, null);
            const du = -Math.sign(u) * 0.8 * (Math.abs(v) < 20 ? 1 : 0), dv = -Math.sign(v) * 0.8;
            twu(solido, u, v, 5.4, u + du, v + dv, 5.6, 0.04, 4, cMetal, null);
            cw(solido, u + du - 0.3, u + du + 0.3, v + dv - 0.2, v + dv + 0.2, 5.45, 5.7, cOsc);
            LUCES.push([E(u + du, v + dv, 5.35), 0.75, 0]); charcos.push([u + du, v + dv, 0.1, 8]);
          }
          for (let u = -12; u <= 22; u += 8.5) for (const s of [-1, 1]) LUCES.push([E(u, s * 8.5, 13.3), 0.55, 1]);
          for (const [u, v] of [[-12, 0], [-6, 0], [0, 0]]) LUCES.push([E(u, v, 4.0), 0.5, 1]);
          charcos.push([-6, 0, 0.1, 13]);
          // los pasajeros: caminan hacia el acceso o esperan
          const PA = [[-SU + 1, -24, "caminar"], [-SU + 1, 22, "caminar"], [-18.5, -3.2, "de_pie"], [-SU + 1, 1, "caminar"], [-19, 4.2, "de_pie"],
            [-6, 11.5, "de_pie"], [-SU + 3, -28, "caminar"], [-31, 9.6, "de_pie"]].slice(0, NOB);
          out.PA = PA;
          out.flP = NOB ? ctx.flota("persona", NOB, { tamano: K * 1.3, lev: 0.08 * K, orden: 6, semilla: p.semilla % 991,
            color: (i) => camisas[(i + 1) % camisas.length], pose: (i) => PA[i][2] }) : null;
        }

        // ================= los charcos de luz (de noche) y los puntos de luz
        const charco = malla.nueva();
        if (noche) for (const [u, v, h, R] of charcos) {
          const n = 22, q = charco.pos.length / 3, nucleo = cLuz.clone().multiplyScalar(0.18);
          const C = E(u, v, h); charco.pos.push(C[0], C[1], C[2]); charco.col.push(nucleo.r, nucleo.g, nucleo.b);
          for (let i = 0; i < n; i++) { const a = TAU * i / n, P = E(u + R * Math.cos(a), v + R * Math.sin(a), h); charco.pos.push(P[0], P[1], P[2]); charco.col.push(0, 0, 0); }
          for (let i = 0; i < n; i++) charco.idx.push(q, q + 1 + i, q + 1 + ((i + 1) % n));
        }
        const NL = Math.max(1, LUCES.length);
        const gP = new THREE.BufferGeometry(), posP = new Float32Array(NL * 3), aP = new Float32Array(NL * 2);
        LUCES.forEach(([P, a, k], j) => { posP.set(P, j * 3); aP[j * 2] = noche ? a : (k === 2 ? a * 0.5 : 0); aP[j * 2 + 1] = k; });
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 2));
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: cLuz }, cB: { value: tonos.mal.clone() } },
          transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "attribute vec2 aK; uniform float uPx, uTam; varying vec2 vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " float m = aK.y < 0.5 ? 2.8 : (aK.y < 1.5 ? 1.4 : 0.9); gl_PointSize = aK.x > 0.0 ? clamp(m * uTam * uPx / max(1e-3, -mv.z), 2.0, 64.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA, cB; varying vec2 vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = vK.y < 1.5 ? cA : cB; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK.x * (exp(-r * r * 6.0) + 0.6 * exp(-r * r * 40.0)); gl_FragColor = vec4(s * a, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);

        // ================= las mallas fijas
        malla.poner(piso, malla.material({ desfase: 2 }), 2);
        poner(rayas, { desfase: 4 });
        poner(solido, { desfase: 1 });
        const mVid = poner(vid, { desfase: 3 });
        if (noche && charco.pos.length) { const mC = new THREE.Mesh(malla.geometria(charco), malla.material({ aditivo: true, desfase: 5 })); mC.frustumCulled = false; mC.renderOrder = 5; scene.add(mC); }
        fijas.splice(fijas.indexOf(mVid.material), 1);
        return Object.assign(out, { mats: fijas, vidrios: [mVid.material, matMovV], BV: noche ? 1.7 : 1.0, matP });
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      const PI = Math.PI, TAU = 2 * PI;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.4 * kb;
        for (const m of s.vidrios) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = s.BV * (1 + 0.2 * kb);
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        const { E, W, r, s3, noche } = s;
        if (s.obra) {
          // ---- la excavadora: de día gira de la fosa al montículo y vuelve (ciclo de 16 s); de noche, quieta hacia la fosa
          { const f = noche ? 0 : (((t / 16) % 1) + 1) % 1;
            let da = s.ex.b - s.ex.a; while (da > PI) da -= TAU; while (da < -PI) da += TAU;
            const q = f < 0.3 ? 0 : f < 0.5 ? s3((f - 0.3) / 0.2) : f < 0.7 ? 1 : f < 0.9 ? 1 - s3((f - 0.7) / 0.2) : 0;
            s.ex.g.rotation.set(0, r + s.ex.a + da * q, 0);
            s.ex.carga.scale.setScalar(!noche && f > 0.22 && f < 0.6 ? 1 : 1e-4); }
          // ---- las grúas: baja el gancho a la pila, sube el atado, gira, corre el carro, lo baja a la fosa, lo deja y vuelve
          for (const g of s.gruas) {
            const f = noche ? 0.95 : (((t / 26 + g.ph) % 1) + 1) % 1, HUP = g.HM - 5;
            let a = 0, x = g.pick, h = HUP, lleva = 0;
            if (f < 0.12) h = HUP + (0.62 - HUP) * s3(f / 0.12);
            else if (f < 0.18) h = 0.62;
            else if (f < 0.32) { h = 0.62 + (HUP - 0.62) * s3((f - 0.18) / 0.14); lleva = 1; }
            else if (f < 0.55) { const q = s3((f - 0.32) / 0.23); a = q; x = g.pick + (g.drop - g.pick) * q; lleva = 1; }
            else if (f < 0.66) { a = 1; x = g.drop; h = HUP + (0.09 - HUP) * s3((f - 0.55) / 0.11); lleva = 1; }
            else if (f < 0.72) { a = 1; x = g.drop; h = 0.09; lleva = f < 0.69 ? 1 : 0; }
            else if (f < 0.82) { a = 1; x = g.drop; h = 0.09 + (HUP - 0.09) * s3((f - 0.72) / 0.1); }
            else { const q = s3((f - 0.82) / 0.18); a = 1 - q; x = g.drop + (g.pick - g.drop) * q; }
            const phi = g.a0 + g.da * a;
            g.g.rotation.set(0, r + phi, 0);
            const cu = g.gu + x * Math.cos(phi), cv = g.gv + x * Math.sin(phi);
            const Pc = E(cu, cv, g.HM + 0.8); g.car.position.set(Pc[0], Pc[1], Pc[2]); g.car.rotation.set(0, r + phi, 0);
            const top = g.HM + 0.35, hg = h + 0.75 + 0.7, L = Math.max(0.1, top - hg);
            const Pk = E(cu, cv, hg); g.cab.position.set(Pk[0], Pk[1], Pk[2]); g.cab.scale.set(s.M, s.M * L, s.M); g.cab.rotation.set(0, r + phi, 0);
            const Pg = E(cu, cv, h + 0.75); g.gan.position.set(Pg[0], Pg[1], Pg[2]); g.gan.rotation.set(0, r + phi, 0);
            g.at.position.set(Pg[0], Pg[1], Pg[2]); g.at.rotation.set(0, r + phi + 0.4, 0); g.at.scale.setScalar(lleva ? s.M : 1e-4);
          }
          // ---- el volteo y la gente
          { const [u, v, ph] = s.volteo, [x, y] = W(u, v); s.flV.poner(0, x, y, Math.cos(r + ph), Math.sin(r + ph), 1, 0, 0); s.flV.listo(); }
          if (s.flP) {
            s.OB.forEach((o, i) => {
              let u, v, dx, dy, vel = 0, k = 1;
              if (noche) {
                if (i > 1) k = 0;
                u = -36 + i * 1.6; v = 12 - i * 0.8; dx = 1; dy = -0.3;
              } else if (o[2].startsWith("caminar")) {
                const [A, B] = o[2] === "caminar" ? [[-33, 20.5], [-17.5, 3.5]] : [[-37.5, -10], [-37.5, 12]];
                const L = Math.hypot(B[0] - A[0], B[1] - A[1]), per = 2 * L / 1.1 + 4, q = (((t / per + (i ? 0.55 : 0.1)) % 1) + 1) % 1;
                const pausa = 2 / per, ida = q < 0.5;
                const qq = clamp(((ida ? q : q - 0.5) - pausa / 2) / (0.5 - pausa), 0, 1);
                u = ida ? A[0] + (B[0] - A[0]) * qq : B[0] + (A[0] - B[0]) * qq; v = ida ? A[1] + (B[1] - A[1]) * qq : B[1] + (A[1] - B[1]) * qq;
                dx = (ida ? 1 : -1) * (B[0] - A[0]) / L; dy = (ida ? 1 : -1) * (B[1] - A[1]) / L; vel = qq > 0 && qq < 1 ? 1.1 : 0;
              } else { u = o[0]; v = o[1]; const L = Math.hypot(o[3] - u, o[4] - v) || 1; dx = (o[3] - u) / L; dy = (o[4] - v) / L; }
              const [x, y] = W(u, v), ddx = dx * s.ux - dy * s.uy, ddy = dx * s.uy + dy * s.ux;
              s.flP.poner(i, x, y, ddx, ddy, k, 0, vel);
            });
            s.flP.listo();
          }
        } else {
          // ---- la rueda gira a la velocidad del cable (5 m/s en el aro) y las cabinas recorren el lazo
          s.rueda.m.rotation.set(0, t * 5 / s.rueda.RW, 0);
          const V = 5, D = s.VL / s.NCAB;
          s.cabinas.forEach((g, i) => {
            const sv = ((((t * V + i * D) % s.VL) + s.VL) % s.VL);
            let sg = s.SEG[0]; for (const x of s.SEG) if (sv >= x.v0) sg = x;
            const q = clamp((sv - sg.v0) * sg.f / sg.len, 0, 1), [u, v, h, ph] = sg.fn(q);
            const P = E(u, v, h); g.position.set(P[0], P[1], P[2]);
            g.rotation.set(0.025 * Math.sin(t * 1.3 + i * 1.7), r + ph, 0.02 * Math.sin(t * 0.9 + i));
            const k = clamp((s.LEND - u) / 8, 0, 1); g.scale.setScalar(s.M * Math.max(1e-4, k));
          });
          if (s.flA) { s.arboles.forEach(([u, v], i) => { const [x, y] = W(u, v); s.flA.poner(i, x, y, 1, 0, 1, 0, 0); }); s.flA.listo(); }
          if (s.flP) {
            s.PA.forEach((o, i) => {
              let u = o[0], v = o[1], dx = 1, dy = 0, vel = 0, k = 1;
              if (o[2] === "caminar") {
                const B = [-15.5, clamp(o[1] * 0.08, -1.5, 1.5)], A = [o[0], o[1]], L = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1;
                const per = L / 1.2 + 3, q = (((t / per + i * 0.31) % 1) + 1) % 1, qq = clamp(q * per / (L / 1.2), 0, 1);
                u = A[0] + (B[0] - A[0]) * qq; v = A[1] + (B[1] - A[1]) * qq; dx = (B[0] - A[0]) / L; dy = (B[1] - A[1]) / L; vel = qq < 1 ? 1.2 : 0; k = clamp((1 - qq) * 40, 0, 1);
              } else { const L = Math.hypot(-14 - u, -v) || 1; dx = (-14 - u) / L; dy = -v / L; }
              const [x, y] = W(u, v), ddx = dx * s.ux - dy * s.uy, ddy = dx * s.uy + dy * s.ux;
              s.flP.poner(i, x, y, ddx, ddy, k, 0, vel);
            });
            s.flP.listo();
          }
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
