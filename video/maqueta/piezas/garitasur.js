// Pieza «garitasur» (ficha: garitasur.json; reglas: scripts/maqueta_tipos/garitasur.py): la entrada de una ciudad de fines del
// siglo XIX por su garita, genérica y en METROS × `tamano`, centrada en `lugar` (la puerta) y orientada por `rumbo` (u: hacia
// la ciudad; v: a su izquierda).
// - El POTRERO de fondo (pasto con su ruido de tono, matas y árboles) y el CAMINO REAL de tierra con sus dos roderas y el lomo
//   de pasto entre ellas, de u −300 a u +140; afuera, a 110 m de la puerta, se le juntan dos RAMALES (tres caminos que
//   convergen, sin rótulos).
// - La PUERTA de madera: dos postes sobre su base de piedra, el dintel y dos hojas de tablas con sus travesaños, su tranca en
//   Z y sus bisagras; sin muro ni cerca a los lados. De día abierta; de noche cerrada, con su farol encendido.
// - La TRANCA 8 m antes de la puerta: la vara con su contrapeso sobre un poste horquillado y su apoyo del otro lado. De día
//   sube, pasa la carreta o la recua del frente y baja (ciclo de `tranca_s`); de noche, abajo.
// - Una RAMADA genérica junto a la tranca (postes, techo de teja a un agua, banca, mesa y farol).
// - La FILA: carretas de dos ruedas con carga, tiradas por una pareja de animales de tiro genéricos, y recuas de mulas con
//   aparejo y bultos. Posición = función de t: la del frente pasa y sigue al paso hacia la ciudad (patas que caminan según lo
//   andado, ruedas que giran), la fila avanza una plaza y otra entra por la cola. Arrieros a su lado (objeto persona).
// - Adentro a la izquierda, el CANTÓN trazado sobre el potrero: estacas, cordeles y la línea de cal de 9 manzanas; con
//   `canton` > 0, calles pisadas y casas genéricas de un piso con techo de teja en esa fracción de los solares (ilustrativo).
//   El trazo va grueso (faja rastrillada de 3 m, línea de cal de 1.1 m, estacas con punta encalada) para leerse a 150 m; con
//   `vecinos`, gente que rastrilla la faja, acarrea sacos de cal y ata el cordel a una estaca (de día).
// - Adentro a la derecha, una SIEMBRA en surcos y el ganado que pasta. Con `tren`, la vía y una estación de madera.
// - De noche (ES.noche): puerta cerrada, nadie pasa, los arrieros sentados junto a una fogata, faroles, ventanas encendidas.
// Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto, marcas ni números.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  const s3 = (x) => { const v = Math.max(0, Math.min(1, x)); return v * v * (3 - 2 * v); };
  MAQ.PIEZAS.garitasur = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1;
      // ---- los tonos (todos del estilo)
      const cTierra = tonos.calle.clone().lerp(tonos.arena, 0.45);
      const cRodera = cTierra.clone().multiplyScalar(0.72);
      const cPasto = tonos.campo.clone(), cPasto2 = tonos.campo2.clone();
      const cMata = tonos.verde.clone().lerp(tonos.campo2, 0.3).multiplyScalar(oscuro ? 1.3 : 0.82);
      const cHoja = tonos.verde.clone().lerp(lin(COL.tierra_media), 0.2).multiplyScalar(oscuro ? 1.35 : 0.72);
      const cMadera = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.55).multiplyScalar(oscuro ? 0.75 : 0.95);
      const cMaderaO = cMadera.clone().multiplyScalar(0.66);
      const cTronco = cMadera.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.8);
      const cTeja = tonos.techo.clone();
      const cAdobe = tonos.muro.clone();
      const cZocalo = tonos.muro.clone().lerp(tonos.arena, 0.5).multiplyScalar(0.82);
      const cPiedra = tonos.arena.clone().lerp(tonos.asfalto, 0.45);
      const cCal = tonos.muro.clone().lerp(tonos.linea, 0.3).multiplyScalar(oscuro ? 1.0 : 1.08);
      const cTrazo = tonos.muro.clone().lerp(tonos.linea, 0.55).multiplyScalar(oscuro ? 1.25 : 1.22);   // la cal del trazo, lo más claro del suelo
      const cRastro = lin(COL.tierra_media).lerp(tonos.calle, 0.35).multiplyScalar(oscuro ? 0.85 : 0.62);   // la tierra rastrillada, oscura
      const cHierro = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.9 : 0.45);
      const cSurco = cTierra.clone().lerp(lin(COL.tierra_media), 0.3).multiplyScalar(0.78);
      const cHueco = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.6 : 0.32);
      const cLuz = lin(COL.luces);
      const cVent = noche ? cLuz.clone().lerp(lin(COL.luz), 0.3) : cHueco.clone().lerp(cMadera, 0.35);
      const cFuego = tonos.medio.clone().lerp(cLuz, 0.5);
      const PELO = [lin(COL.tierra_media).multiplyScalar(0.6), lin(COL.tierra_alta).multiplyScalar(0.5),
        tonos.asfalto.clone().lerp(lin(COL.tierra_media), 0.4).multiplyScalar(0.72), tonos.arena.clone().multiplyScalar(0.82)];
      const CARGA = [tonos.arena.clone().lerp(tonos.muro, 0.5), tonos.muro.clone().lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(0.9),
        cMadera.clone().lerp(tonos.arena, 0.5), tonos.secundario.clone().lerp(tonos.muro, 0.55).multiplyScalar(0.85)];
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;

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

      // ================= lo que se mueve, en METROS locales (x adelante, y arriba, z a la derecha): las geometrías, una vez
      const geos = {};
      const geo = (clave, hacer) => { if (!geos[clave]) { const acc = malla.nueva(); hacer(acc); geos[clave] = malla.geometria(acc); } return geos[clave]; };
      // un animal de tiro o de carga genérico (cuerpo con cuello, cabeza, orejas y cola; las patas van aparte). Origen: el centro
      // del cuerpo en el suelo; la cabeza llega a x ≈ +1.2. `pasta`: la cabeza abajo, al pasto
      const cuerpo = (acc, col, pasta, orejas) => {
        const cO = col.clone().multiplyScalar(0.72), cC = col.clone().lerp(cHueco, 0.5);
        tubo(acc, [-0.62, 1.12, 0], [0.5, 1.16, 0], 0.31, 12, col, col);
        gema(acc, [-0.64, 1.1, 0], 0.26, 0.29, 0.29, 0, col); gema(acc, [0.52, 1.14, 0], 0.27, 0.3, 0.28, 0, col);
        const cu = pasta ? [[0.62, 1.2], [0.98, 0.72]] : [[0.58, 1.22], [0.92, 1.62]];
        tubo(acc, [cu[0][0], cu[0][1], 0], [cu[1][0], cu[1][1], 0], 0.14, 10, col, col);
        bx(acc, XL, cu[0][0] - 0.02, cu[1][0] - 0.05, Math.min(cu[0][1], cu[1][1]) + 0.08, Math.max(cu[0][1], cu[1][1]) + 0.1, -0.03, 0.03, cO);   // la crin
        const cb = pasta ? [[0.98, 0.74], [1.12, 0.32]] : [[0.92, 1.64], [1.18, 1.32]];
        tubo(acc, [cb[0][0], cb[0][1], 0], [cb[1][0], cb[1][1], 0], 0.11, 10, col, cC);
        if (orejas) for (const z of [-0.06, 0.06]) tubo(acc, [cb[0][0] - 0.02, cb[0][1] + 0.06, z], [cb[0][0] - 0.08, cb[0][1] + (pasta ? -0.1 : 0.32), z * 1.8], 0.03, 5, cO, null);
        tubo(acc, [-0.86, 1.18, 0], [-0.98, 0.62, 0], 0.045, 6, cO, cO);
      };
      const pata = (acc, col) => {   // de la cadera (y 0) al casco (y −1.0)
        const cC = col.clone().lerp(cHueco, 0.6);
        bx(acc, XL, -0.07, 0.07, -0.55, 0.05, -0.06, 0.06, col);
        bx(acc, XL, -0.05, 0.05, -0.93, -0.55, -0.045, 0.045, col.clone().multiplyScalar(0.85));
        bx(acc, XL, -0.065, 0.065, -1.0, -0.92, -0.06, 0.06, cC);
      };
      // la carga de una mula: aparejo, dos bultos a los costados y uno encima, con su soga
      const aparejo = (acc, k) => {
        const c1 = CARGA[k % CARGA.length], c2 = CARGA[(k + 1) % CARGA.length], cS = cCal.clone().multiplyScalar(0.8);
        bx(acc, XL, -0.5, 0.42, 1.38, 1.48, -0.36, 0.36, cMaderaO);
        for (const z of [-1, 1]) {
          bx(acc, XL, -0.42, 0.36, 0.78, 1.42, z > 0 ? 0.32 : -0.6, z > 0 ? 0.6 : -0.32, c1.clone().multiplyScalar(0.92 + 0.08 * z));
          for (const x of [-0.2, 0.15]) bx(acc, XL, x - 0.02, x + 0.02, 0.76, 1.44, z > 0 ? 0.6 : -0.62, z > 0 ? 0.62 : -0.6, cS);
        }
        bx(acc, XL, -0.36, 0.3, 1.48, 1.78, -0.28, 0.28, c2);
        bx(acc, XL, -0.04, 0.0, 1.47, 1.8, -0.62, 0.62, cS);
      };
      const collera = (acc) => {   // el collerón de tiro (genérico)
        tubo(acc, [0.62, 1.05, -0.2], [0.66, 1.42, -0.18], 0.06, 6, cMaderaO, null); tubo(acc, [0.62, 1.05, 0.2], [0.66, 1.42, 0.18], 0.06, 6, cMaderaO, null);
        tubo(acc, [0.62, 1.05, -0.2], [0.62, 1.05, 0.2], 0.06, 6, cMaderaO, null);
      };
      // la carreta: plataforma, barandas, lanza hasta el balancín de la pareja, eje; la carga en sacos y fardos. Origen: la
      // punta de la lanza (x 0); la plataforma va de x −1.45 a −4.65
      const carreta = (acc, k) => {
        const cM = cMadera.clone().multiplyScalar(0.9 + 0.12 * ((k * 37) % 7) / 7);
        bx(acc, XL, -4.65, -1.45, 0.92, 1.04, -0.85, 0.85, cM, { fondo: true });
        for (let x = -4.5; x < -1.5; x += 0.42) bx(acc, XL, x, x + 0.05, 1.04, 1.045, -0.85, 0.85, cM.clone().multiplyScalar(0.8));
        for (const z of [-1, 1]) {
          bx(acc, XL, -4.65, -1.45, 1.42, 1.5, z > 0 ? 0.8 : -0.85, z > 0 ? 0.85 : -0.8, cM);
          for (let x = -4.55; x <= -1.5; x += 0.64) bx(acc, XL, x, x + 0.08, 1.04, 1.5, z > 0 ? 0.79 : -0.86, z > 0 ? 0.86 : -0.79, cMaderaO);
        }
        bx(acc, XL, -4.65, -4.57, 1.04, 1.5, -0.85, 0.85, cMaderaO); bx(acc, XL, -1.53, -1.45, 1.04, 1.5, -0.85, 0.85, cMaderaO);
        tubo(acc, [-0.15, 1.02, 0], [-2.6, 0.95, 0], 0.07, 8, cMaderaO, cMaderaO);                 // la lanza
        tubo(acc, [-0.35, 1.02, -0.85], [-0.35, 1.02, 0.85], 0.06, 8, cMaderaO, cMaderaO);          // el balancín
        tubo(acc, [-3.05, 0.78, -1.08], [-3.05, 0.78, 1.08], 0.07, 10, cHierro, cHierro);           // el eje
        bx(acc, XL, -3.4, -2.7, 0.8, 0.92, -0.7, 0.7, cMaderaO);
        for (let i = 0; i < 7; i++) {                                                                // la carga
          const x = -4.25 + (i % 4) * 0.72, z = i < 4 ? -0.36 : 0.36, h = 0.34 + 0.08 * ((k * 13 + i * 7) % 5) / 5;
          const c = CARGA[(k + i) % CARGA.length].clone().multiplyScalar(0.9 + 0.1 * ((i * 3) % 4) / 4);
          gema(acc, [x, 1.05 + h * 0.9, z], 0.36, h, 0.32, 0.15 * i, c);
        }
        bx(acc, XL, -4.4, -2.0, 1.55, 1.82, -0.55, 0.55, CARGA[(k + 2) % CARGA.length].clone().multiplyScalar(0.95));
      };
      const rueda = (acc) => {   // radio 0.78, en el plano x-y (eje z)
        const R = 0.78, n = 16;
        for (let i = 0; i < n; i++) {
          const a0 = TAU * i / n, a1 = TAU * (i + 1) / n;
          bx(acc, (x, y, z) => { const a = a0 + (a1 - a0) * (x + 0.5); return [Math.cos(a) * (R - 0.09 + y), Math.sin(a) * (R - 0.09 + y), z]; }, -0.5, 0.5, 0, 0.09, -0.06, 0.06, cMaderaO);
        }
        tubo(acc, [0, 0, -0.12], [0, 0, 0.12], 0.13, 12, cMaderaO, cMadera);
        for (let i = 0; i < 8; i++) { const a = TAU * i / 8; tubo(acc, [Math.cos(a) * 0.12, Math.sin(a) * 0.12, 0], [Math.cos(a) * 0.7, Math.sin(a) * 0.7, 0], 0.035, 5, cMadera, null); }
      };
      const matMov = malla.material(), mats = [matMov];
      const malla0 = (g, x, y, z) => { const m = new THREE.Mesh(g, matMov); m.frustumCulled = false; m.renderOrder = 4; m.position.set(x || 0, y || 0, z || 0); return m; };
      // un animal armado: grupo con su cuerpo y 4 patas (para mover las patas según lo andado)
      const animal = (k, pasta, carga, tiro) => {
        const ic = k % PELO.length, col = PELO[ic];
        const g = new THREE.Group();
        g.add(malla0(geo("cuerpo" + ic + (pasta ? "p" : ""), (acc) => cuerpo(acc, col, pasta, true))));
        if (carga) g.add(malla0(geo("carga" + (k % CARGA.length), (acc) => aparejo(acc, k))));
        if (tiro) g.add(malla0(geo("collera", collera)));
        const patas = [[0.48, -0.17, 0], [0.48, 0.17, Math.PI], [-0.56, -0.17, Math.PI], [-0.56, 0.17, 0]].map(([x, z, f]) => {
          const m = malla0(geo("pata" + ic, (acc) => pata(acc, col)), x, 1.02, z); m.userData.f = f; g.add(m); return m; });
        return { g, patas };
      };
      const andar = (A, d, amp) => { for (const m of A.patas) m.rotation.z = amp * Math.sin(TAU * d / 1.7 + m.userData.f); };

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, ctx.altura(x, y) + h * M, -y]; };
        const XW = (x, y, z) => E(x, z, y);                                   // caja del mundo: x = u, y = h, z = v
        const cw = (acc, u0, u1, v0, v1, h0, h1, col, op) => bx(acc, XW, u0, u1, h0, h1, v0, v1, col, op);
        const twu = (acc, u0, v0, h0, u1, v1, h1, rr, seg, col, tapa) => tubo(acc, E(u0, v0, h0), E(u1, v1, h1), rr * M, seg, col, tapa);
        const gmu = (acc, u, v, h, rx, ry, rz, rot, col) => gema(acc, E(u, v, h), rx * M, ry * M, rz * M, rot, col);
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const losa = (acc, u0, u1, v0, v1, h, cel, colf) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cel)), nv = Math.max(1, Math.round((v1 - v0) / cel)), l = sombra(0, 1, 0);
          for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
            const a = u0 + (u1 - u0) * i / nu, b = u0 + (u1 - u0) * (i + 1) / nu, e = v0 + (v1 - v0) * j / nv, f = v0 + (v1 - v0) * (j + 1) / nv;
            const q = acc.pos.length / 3;
            for (const [uu, vv] of [[a, e], [b, e], [b, f], [a, f]]) { const P = E(uu, vv, h), c = colf(uu, vv); acc.pos.push(P[0], P[1], P[2]); acc.col.push(c.r * l, c.g * l, c.b * l); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        // una franja sobre una polilínea [[u, v], …]: ancho, corrida `off` a su izquierda
        const franja = (acc, pts, ancho, off, h, colf) => {
          const l = sombra(0, 1, 0), N = pts.map((P, i) => {
            const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], du = b[0] - a[0], dv = b[1] - a[1], L = Math.hypot(du, dv) || 1;
            return [-dv / L, du / L]; });
          for (let i = 0; i < pts.length - 1; i++) {
            const q = acc.pos.length / 3;
            for (const [j, s] of [[i, 1], [i + 1, 1], [i + 1, -1], [i, -1]]) {
              const w = off + s * ancho / 2, uu = pts[j][0] + N[j][0] * w, vv = pts[j][1] + N[j][1] * w, P = E(uu, vv, h), c = colf(uu, vv);
              acc.pos.push(P[0], P[1], P[2]); acc.col.push(c.r * l, c.g * l, c.b * l);
            }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };
        const nueva = () => malla.nueva();
        const poner = (acc, op) => { const m = new THREE.Mesh(malla.geometria(acc), malla.material(op || {})); m.frustumCulled = false; m.renderOrder = 3; scene.add(m); mats.push(m.material); return m; };

        // ================= el suelo: potrero, caminos, siembra, cantón
        const U0 = -300, U1 = 140, V1 = 150;
        const piso = nueva(), camino = nueva(), marcas = nueva(), solido = nueva(), veg = nueva(), vid = nueva();
        const tonoPasto = (u, v) => cPasto.clone().lerp(cPasto2, clamp(ruido(u, v, 38, 3) * 1.2 - 0.1, 0, 1)).multiplyScalar(0.92 + 0.1 * ruido(u, v, 7, 4));
        // adentro del cantón el pasto va parejo (sin las manchas grandes del potrero) para que el trazo se lea de lejos
        const enCanton = (u, v) => u > 10 && u < 136 && v > 14 && v < 142;
        const pastoParejo = (u, v) => cPasto.clone().lerp(cPasto2, 0.3 + 0.15 * ruido(u, v, 38, 3)).multiplyScalar(0.95 + 0.04 * ruido(u, v, 7, 4));
        losa(piso, U0, U1, -V1, V1, 0.03, 10, (u, v) => (enCanton(u, v) ? pastoParejo(u, v) : tonoPasto(u, v)));
        const tonoTierra = (u, v) => cTierra.clone().multiplyScalar(0.92 + 0.12 * ruido(u, v, 6, 5));
        const real = []; for (let u = U0; u <= U1; u += 4) real.push([u, 0]);
        const vRamal = (u) => 170 * Math.pow(Math.max(0, 1 - (u - U0) / 190), 1.4);
        const ramal = (s) => { const P = []; for (let k = 0; k <= 30; k++) { const u = U0 + 190 * k / 30; P.push([u, s * vRamal(u)]); } return P; };
        const caminos = [real, ramal(1), ramal(-1)];
        caminos.forEach((P, i) => {
          franja(camino, P, i ? 6.5 : 8, 0, 0.07, tonoTierra);
          franja(marcas, P, i ? 0.5 : 0.7, 0, 0.085, (u, v) => cTierra.clone().lerp(cPasto, 0.45));
          for (const o of [-0.85, 0.85]) franja(marcas, P, 0.42, o, 0.09, () => cRodera);
        });
        const libre = (u, v, m) => {
          if (u < U0 + 2 || u > U1 - 2 || Math.abs(v) > V1 - 2) return false;
          if (Math.abs(v) < 6 + m) return false;
          if (u < -100 && Math.abs(Math.abs(v) - vRamal(u)) < (5 + m) * 1.7) return false;
          if (u > 10 && u < 136 && v > 14 && v < 142) return false;                  // el cantón
          if (u > 14 && u < 86 && v < -18 && v > -66) return false;                  // la siembra
          if (u > -22 && u < 10 && v > -18 && v < 14) return false;                  // la garita y la ramada
          if (Math.hypot(u + 36, v - 10) < 6 + m) return false;                      // la fogata
          if (p.tren && v < -80 && v > -106) return false;
          return true;
        };
        // la siembra: surcos y matas
        for (let v = -62; v <= -22; v += 1.4) {
          franja(marcas, [[18, v], [82, v]], 0.45, 0, 0.06, () => cSurco);
          for (let u = 19; u < 82; u += 1.9) { const k = Math.round(u * 7 + v * 13); gmu(veg, u + (hz(k, 21) - 0.5) * 0.4, v, 0.45, 0.3, 0.5 + 0.25 * hz(k, 22), 0.3, hz(k, 23) * 3, cMata.clone().multiplyScalar(0.85 + 0.25 * hz(k, 24))); }
        }
        // matas de pasto y árboles
        for (let i = 0, n = 0; i < 2600 && n < 800; i++) {
          const u = U0 + (U1 - U0) * hz(i, 31), v = -V1 + 2 * V1 * hz(i, 32);
          if (!libre(u, v, 0)) continue; n++;
          gmu(veg, u, v, 0.12, 0.35 + 0.3 * hz(i, 33), 0.25 + 0.2 * hz(i, 34), 0.35 + 0.3 * hz(i, 35), hz(i, 36) * 3, cMata.clone().multiplyScalar(0.8 + 0.3 * hz(i, 37)));
        }
        const arboles = [];
        for (let i = 0; i < 900 && arboles.length < 46; i++) {
          const u = U0 + (U1 - U0) * hz(i, 41), v = -V1 + 2 * V1 * hz(i, 42);
          if (!libre(u, v, 5) || arboles.some(([a, b]) => Math.hypot(a - u, b - v) < 14)) continue;
          arboles.push([u, v]);
          const h = 3.4 + 2.6 * hz(i, 43), R = 2.4 + 1.6 * hz(i, 44), cH = cHoja.clone().multiplyScalar(0.85 + 0.3 * hz(i, 45));
          twu(solido, u, v, 0, u, v, h + 0.6, 0.22 + 0.08 * hz(i, 46), 10, cTronco, null);
          gmu(veg, u, v, h + R * 0.55, R, R * 0.75, R, hz(i, 47) * 3, cH);
          for (let j = 0; j < 3; j++) { const a = TAU * (j / 3 + hz(i, 48)); gmu(veg, u + Math.cos(a) * R * 0.6, v + Math.sin(a) * R * 0.6, h + R * 0.25, R * 0.7, R * 0.55, R * 0.7, a, cH.clone().multiplyScalar(0.88 + 0.1 * j)); }
        }

        // ================= el cantón: 9 manzanas trazadas (cal, estacas, cordeles); casas genéricas en la fracción `canton`
        const BU = [18, 58, 98], BVs = [24, 64, 104], BL = 30, CANT = clamp(p.canton || 0, 0, 1);
        if (CANT > 0) {
          const cCalle = cPasto.clone().lerp(cTierra, 0.35 + 0.55 * CANT);
          for (const u of [8, 48, 88, 128]) losa(marcas, u + 0.5, u + 9.5, 14, 142, 0.05, 4, () => cCalle);
          for (const v of [14, 54, 94, 134]) losa(marcas, 8, 138, v + 0.5, v + 9.5, 0.055, 4, () => cCalle);
        }
        let nLote = 0;
        for (const u0 of BU) for (const v0 of BVs) {
          const u1 = u0 + BL, v1 = v0 + BL;
          for (const [a, b, c, d] of [[u0, v0, u1, v0], [u1, v0, u1, v1], [u1, v1, u0, v1], [u0, v1, u0, v0]]) {
            // la faja rastrillada (tierra a la vista, 3 m) y encima la línea de cal (1.1 m): oscuro y claro, se lee a 150 m
            const du = Math.sign(c - a), dv = Math.sign(d - b);
            franja(marcas, [[a - du * 1.5, b - dv * 1.5], [c + du * 1.5, d + dv * 1.5]], 3.0, 0, 0.085, (uu, vv) => cRastro.clone().multiplyScalar(0.92 + 0.12 * ruido(uu, vv, 3, 6)));
            franja(marcas, [[a - du * 0.55, b - dv * 0.55], [c + du * 0.55, d + dv * 0.55]], 1.1, 0, 0.11, (uu, vv) => cTrazo.clone().multiplyScalar(0.95 + 0.08 * ruido(uu, vv, 2, 7)));
            const L = Math.hypot(c - a, d - b), n = Math.round(L / 5);
            for (let k = 0; k < n; k++) {
              const q = k / n, uu = a + (c - a) * q, vv = b + (d - b) * q, alta = k === 0, w = alta ? 0.16 : 0.1, hE = alta ? 1.7 : 1.05;
              cw(solido, uu - w, uu + w, vv - w, vv + w, 0, hE, alta ? cMadera : cMadera.clone().multiplyScalar(1.1));
              cw(solido, uu - w - 0.01, uu + w + 0.01, vv - w - 0.01, vv + w + 0.01, hE - 0.28, hE + 0.01, cTrazo);   // la punta encalada
            }
            // el cordel, tendido a media estaca (grueso: una cuerda torcida de 8 cm que se ve como línea clara)
            twu(solido, a, b, 0.72, c, d, 0.72, 0.045, 5, cTrazo, null);
          }
          // un montón de cal en la esquina de la manzana
          if (hz(nLote, 58) < 0.7) gmu(solido, u0 - 3.2, v0 - 3.2, 0.12, 1.1, 0.45, 0.9, hz(nLote, 59) * 3, cTrazo.clone().multiplyScalar(0.94));
          // los solares (2 × 2 por manzana)
          for (const [i, j] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
            const lote = nLote++;
            if (!(hz(lote, 51) < CANT)) continue;
            const su = i ? 1 : -1, uf = i ? u1 : u0, vc = v0 + BL * (j ? 0.75 : 0.25) + (hz(lote, 52) - 0.5) * 1.2;
            const fondo = 6.5 + 1.5 * hz(lote, 53), med = 6 + 0.6 * hz(lote, 54), ub = uf - su * fondo, va = vc - med, vb = vc + med;
            const uA = Math.min(uf, ub), uB = Math.max(uf, ub), H = 3.2 + 0.4 * hz(lote, 55), cA = cAdobe.clone().multiplyScalar(0.92 + 0.12 * hz(lote, 56));
            cw(solido, uA, uB, va, vb, 0, 0.55, cZocalo, { tope: cZocalo });
            cw(solido, uA + 0.02, uB - 0.02, va + 0.02, vb - 0.02, 0.55, H, cA, { sinTope: true });
            const ur = (uf + ub) / 2, uE = uf + su * 0.7, uE2 = ub - su * 0.7, HR = H + 1.7;
            for (const [ue, ref] of [[uE, su], [uE2, -su]]) {
              cara(solido, [E(ue, va - 0.5, H - 0.15), E(ue, vb + 0.5, H - 0.15), E(ur, vb + 0.5, HR), E(ur, va - 0.5, HR)], cTeja.clone().multiplyScalar(0.95 + 0.08 * hz(lote, 57)), [ref * ux, 1, -ref * uy]);
              for (let k = 1; k < 7; k++) { const q = k / 7, uq = ue + (ur - ue) * q, hq = H - 0.15 + (HR - H + 0.15) * q + 0.03;
                cara(marcas, [E(uq, va - 0.5, hq), E(uq, vb + 0.5, hq), E(uq + (ur - ue) * 0.025, vb + 0.5, hq + 0.02), E(uq + (ur - ue) * 0.025, va - 0.5, hq + 0.02)], cTeja.clone().multiplyScalar(0.72), [0, 1, 0]); }
            }
            for (const vv of [va, vb]) cara(solido, [E(uf, vv, H), E(ub, vv, H), E(ur, vv, HR - 0.1), E(ur, vv, HR - 0.1)], cA.clone().multiplyScalar(0.94), vv === va ? [uy, 0, ux] : [-uy, 0, -ux]);
            // la fachada: puerta y dos ventanas (con su marco); de noche, encendidas
            const uF2 = uf + su * 0.03, refF = [su * ux, 0, -su * uy];
            cara(solido, [E(uF2, vc - 0.7, 0.05), E(uF2, vc + 0.7, 0.05), E(uF2, vc + 0.7, 2.3), E(uF2, vc - 0.7, 2.3)], cMaderaO, refF);
            for (const dv of [-3.6, 3.6]) {
              cara(solido, [E(uF2, vc + dv - 0.75, 1.05), E(uF2, vc + dv + 0.75, 1.05), E(uF2, vc + dv + 0.75, 2.35), E(uF2, vc + dv - 0.75, 2.35)], cMaderaO, refF);
              cara(vid, [E(uF2 + su * 0.02, vc + dv - 0.55, 1.2), E(uF2 + su * 0.02, vc + dv + 0.55, 1.2), E(uF2 + su * 0.02, vc + dv + 0.55, 2.2), E(uF2 + su * 0.02, vc + dv - 0.55, 2.2)], cVent, refF);
            }
          }
        }

        // ================= los vecinos del cantón (`vecinos`): rastrillan la faja, acarrean cal, tienden el cordel a una estaca
        const NVe = clamp(p.vecinos | 0, 0, 9), VEC = [];
        const MZ = [[0, 0], [1, 0], [0, 1], [1, 1], [2, 0], [0, 2], [2, 1], [1, 2], [2, 2]];
        for (let i = 0; i < NVe; i++) {
          const [bi, bj] = MZ[i], u0 = BU[bi], v0 = BVs[bj], rol = i % 3;
          if (rol === 0) VEC.push({ rol, u: u0 + 15, v: v0 + 2.2, A: 9, w: 0.06 + 0.02 * hz(i, 71), f: hz(i, 72) * TAU });
          else if (rol === 1) {
            const uu = u0 + 4.5, vv = v0 + 5.5;
            VEC.push({ rol, u: uu, v: vv });
            // la tarima con los sacos de cal que toma (≈ 0.7 m), adelante de él (+u)
            cw(solido, uu + 0.55, uu + 1.75, vv - 0.7, vv + 0.7, 0, 0.16, cMaderaO);
            for (let k = 0; k < 4; k++) cw(solido, uu + 0.6 + 0.55 * (k % 2), uu + 1.12 + 0.55 * (k % 2), vv - 0.62 + 0.62 * (k >> 1), vv - 0.04 + 0.62 * (k >> 1), 0.16, 0.42, cTrazo.clone().multiplyScalar(0.9 + 0.08 * hz(i * 4 + k, 73)));
            for (let k = 0; k < 2; k++) cw(solido, uu + 0.7 + 0.5 * k, uu + 1.18 + 0.5 * k, vv - 0.3, vv + 0.28, 0.42, 0.68, cTrazo.clone().multiplyScalar(0.92));
          } else VEC.push({ rol, u: u0 + BL - 0.75, v: v0 + 10 + 10 * hz(i, 74) });
        }

        // ================= la puerta: postes con su base de piedra, dintel, hojas de tablas (abiertas de día, cerradas de noche)
        const PV = 4.95;
        for (const s of [-1, 1]) {
          cw(solido, -0.55, 0.55, s * PV - 0.55, s * PV + 0.55, 0, 0.55, cPiedra, { tope: cPiedra.clone().multiplyScalar(1.08) });
          cw(solido, -0.21, 0.21, s * PV - 0.21, s * PV + 0.21, 0.5, 4.75, cMadera);
          cw(solido, -0.27, 0.27, s * PV - 0.27, s * PV + 0.27, 4.6, 4.8, cMaderaO);
          for (let i = 0; i < 4; i++) gmu(solido, -0.6 + 1.2 * hz(i + s * 5, 61), s * (PV + 0.7 + 0.5 * hz(i + s * 5, 62)), 0.15, 0.32, 0.22, 0.3, i, cPiedra.clone().multiplyScalar(0.85 + 0.2 * hz(i, 63)));
        }
        cw(solido, -0.24, 0.24, -PV - 0.6, PV + 0.6, 4.3, 4.68, cMadera);
        cw(solido, -0.32, 0.32, -PV - 0.75, PV + 0.75, 4.68, 4.82, cMaderaO);
        const hoja = (acc) => {   // a lo largo de +z, de 0 a 4.7; 3.6 de alto; grosor en x
          for (let z = 0.04; z < 4.66; z += 0.33) bx(acc, XL, -0.05, 0.05, 0.12, 3.5 - 0.05 * ((z * 7) % 2), z, Math.min(4.7, z + 0.31), cMadera.clone().multiplyScalar(0.9 + 0.12 * ((z * 11) % 3) / 3));
          for (const y of [0.45, 1.85, 3.15]) bx(acc, XL, 0.05, 0.12, y, y + 0.22, 0.1, 4.6, cMaderaO);
          const d0 = [0.085, 0.67, 0.25], d1 = [0.085, 1.85, 4.4], dl = [0.085, 2.07, 0.25], dm = [0.085, 3.15, 4.4];
          cara(acc, [[0.13, d0[1], d0[2]], [0.13, d0[1] + 0.2, d0[2]], [0.13, d1[1], d1[2] - 0.25], [0.13, d1[1], d1[2]]], cMaderaO, [1, 0, 0]);
          cara(acc, [[0.13, dl[1], dl[2]], [0.13, dl[1] + 0.2, dl[2]], [0.13, dm[1], dm[2] - 0.25], [0.13, dm[1], dm[2]]], cMaderaO, [1, 0, 0]);
          for (const y of [0.55, 1.95, 3.25]) bx(acc, XL, -0.07, 0.14, y - 0.06, y + 0.06, 0.0, 0.7, cHierro);
        };
        const gHoja = geo("hoja", hoja), ab = noche ? 0 : 0.92 * Math.PI / 2;
        for (const s of [1, -1]) {
          const m = malla0(gHoja), P = E(0, s * (PV - 0.25), 0);
          m.position.set(P[0], P[1], P[2]); m.scale.setScalar(M); m.rotation.y = s > 0 ? r + ab : r + Math.PI - ab; scene.add(m);
        }

        // ================= la tranca: poste horquillado, vara con contrapeso, apoyo del otro lado
        const TU = -8, TVp = -6.2, TVa = 5.6;
        cw(solido, TU - 0.16, TU + 0.16, TVp - 0.16, TVp + 0.16, 0, 1.0, cMadera);
        for (const du of [-0.14, 0.14]) cw(solido, TU + du - 0.05, TU + du + 0.05, TVp - 0.12, TVp + 0.12, 0.95, 1.3, cMaderaO);
        cw(solido, TU - 0.12, TU + 0.12, TVa - 0.12, TVa + 0.12, 0, 0.98, cMadera);
        for (const dv of [-0.12, 0.12]) cw(solido, TU - 0.04, TU + 0.04, TVa + dv - 0.04, TVa + dv + 0.04, 0.9, 1.25, cMaderaO);
        const gTranca = geo("tranca", (acc) => {
          tubo(acc, [0, 0, 1.4], [0, 0, -12.0], 0.1, 12, cMadera, cMaderaO);
          gema(acc, [0, -0.05, 1.45], 0.38, 0.32, 0.42, 0.3, cPiedra);
          for (const z of [1.1, 1.8]) tubo(acc, [0, 0.0, z], [0, 0.0, z + 0.06], 0.4, 8, cHierro, null);
        });
        const mTranca = malla0(gTranca); { const P = E(TU, TVp, 1.18); mTranca.position.set(P[0], P[1], P[2]); }
        mTranca.scale.setScalar(M); mTranca.rotation.order = "YXZ"; mTranca.rotation.y = r; scene.add(mTranca);

        // ================= la ramada: postes, techo de teja a un agua, banca, mesa y farol
        const RU0 = -13, RU1 = -4.5, RV0 = -15.5, RV1 = -9.5;
        for (const [u, v, h] of [[RU0, RV0, 2.35], [RU1, RV0, 2.35], [RU0, RV1, 2.85], [RU1, RV1, 2.85], [(RU0 + RU1) / 2, RV1, 2.85]]) twu(solido, u, v, 0, u, v, h + 0.05, 0.11, 8, cMadera, cMaderaO);
        cw(solido, RU0 - 0.1, RU1 + 0.1, RV1 - 0.1, RV1 + 0.1, 2.72, 2.88, cMaderaO);
        cw(solido, RU0 - 0.1, RU1 + 0.1, RV0 - 0.1, RV0 + 0.1, 2.22, 2.38, cMaderaO);
        { const A = [RU0 - 0.7, RV0 - 0.8, 2.25], B = [RU1 + 0.7, RV1 + 0.9, 2.98];
          cara(solido, [E(A[0], A[1], A[2]), E(B[0], A[1], A[2]), E(B[0], B[1], B[2]), E(A[0], B[1], B[2])], cTeja, [0, 1, 0]);
          for (let k = 1; k < 9; k++) { const q = k / 9, v = A[1] + (B[1] - A[1]) * q, h = A[2] + (B[2] - A[2]) * q + 0.03;
            cara(marcas, [E(A[0], v, h), E(B[0], v, h), E(B[0], v + 0.14, h + 0.02), E(A[0], v + 0.14, h + 0.02)], cTeja.clone().multiplyScalar(0.72), [0, 1, 0]); }
          cara(solido, [E(A[0], A[1], A[2] - 0.12), E(B[0], A[1], A[2] - 0.12), E(B[0], A[1], A[2]), E(A[0], A[1], A[2])], cTeja.clone().multiplyScalar(0.7), [uy, 0, ux]); }
        cw(solido, RU0 + 0.6, RU1 - 0.6, -14.9, -14.4, 0.42, 0.5, cMadera);
        for (const u of [RU0 + 0.9, RU1 - 0.9]) cw(solido, u - 0.06, u + 0.06, -14.8, -14.5, 0, 0.42, cMaderaO);
        cw(solido, -9.2, -7.6, -13.4, -12.4, 0.74, 0.82, cMadera);
        for (const [u, v] of [[-9.1, -13.3], [-7.7, -13.3], [-9.1, -12.5], [-7.7, -12.5]]) cw(solido, u - 0.04, u + 0.04, v - 0.04, v + 0.04, 0, 0.74, cMaderaO);
        cw(solido, -8.6, -8.3, -13.0, -12.7, 0.82, 1.18, cHierro);
        cw(solido, -8.57, -8.33, -12.97, -12.73, 0.86, 1.12, noche ? cLuz : cHueco.clone().lerp(cCal, 0.4));
        // el farol de la puerta (en el poste izquierdo, del lado de afuera)
        cw(solido, -0.62, -0.22, PV - 0.04, PV + 0.04, 3.48, 3.54, cHierro);
        cw(solido, -0.78, -0.52, PV - 0.13, PV + 0.13, 3.0, 3.42, cHierro);
        cw(solido, -0.76, -0.54, PV - 0.11, PV + 0.11, 3.05, 3.37, noche ? cLuz : cHueco.clone().lerp(cCal, 0.4));

        // ================= la fogata de los arrieros (de día, las cenizas)
        const FU = -36, FV = 10;
        for (let i = 0; i < 9; i++) { const a = TAU * i / 9; gmu(solido, FU + Math.cos(a) * 0.75, FV + Math.sin(a) * 0.75, 0.1, 0.2, 0.15, 0.2, a, cPiedra.clone().multiplyScalar(0.8 + 0.25 * hz(i, 71))); }
        for (let i = 0; i < 3; i++) { const a = TAU * i / 3 + 0.4; twu(solido, FU + Math.cos(a) * 0.55, FV + Math.sin(a) * 0.55, 0.12, FU - Math.cos(a) * 0.15, FV - Math.sin(a) * 0.15, 0.3, 0.07, 6, cTronco, cMaderaO); }
        cara(marcas, [E(FU - 0.6, FV - 0.6, 0.1), E(FU + 0.6, FV - 0.6, 0.1), E(FU + 0.6, FV + 0.6, 0.1), E(FU - 0.6, FV + 0.6, 0.1)], cHueco, [0, 1, 0]);
        let mFuego = null;
        if (noche) {
          const g = geo("fuego", (acc) => { gema(acc, [0, 0.42, 0], 0.32, 0.5, 0.32, 0, cFuego); gema(acc, [0.12, 0.3, 0.1], 0.2, 0.32, 0.2, 0.7, cLuz); gema(acc, [-0.12, 0.28, -0.08], 0.18, 0.28, 0.18, 1.3, cLuz); });
          mFuego = new THREE.Mesh(g, malla.material({ aditivo: true })); mFuego.frustumCulled = false; mFuego.renderOrder = 6;
          const P = E(FU, FV, 0.1); mFuego.position.set(P[0], P[1], P[2]); mFuego.scale.setScalar(M); scene.add(mFuego);
        }

        // ================= con tren: balasto, durmientes, rieles, andén y estación de madera
        const LUCES = [[-8.45, -12.85, 1.0, 0, 0.9], [-0.65, PV, 3.2, 0, 1.0], [FU, FV, 0.7, 1, 1.0]];   // u, v, h, clase, alfa
        if (p.tren) {
          const RV = -100, via = []; for (let u = U0; u <= U1; u += 5) via.push([u, RV]);
          franja(camino, via, 3.2, 0, 0.1, () => cPiedra);
          for (let u = U0 + 0.5; u < U1; u += 1.0) cw(solido, u - 0.12, u + 0.12, RV - 1.2, RV + 1.2, 0.1, 0.24, cMaderaO);
          for (const o of [-0.72, 0.72]) cw(solido, U0, U1, RV + o - 0.04, RV + o + 0.04, 0.24, 0.38, cHierro);
          cw(solido, 36, 68, -97.6, -93.2, 0, 0.95, cPiedra, { tope: cPiedra.clone().multiplyScalar(1.1) });
          const EU0 = 44, EU1 = 60, EV0 = -91.5, EV1 = -84.5;
          cw(solido, EU0, EU1, EV0, EV1, 0, 0.6, cZocalo, { tope: cZocalo });
          cw(solido, EU0 + 0.05, EU1 - 0.05, EV0 + 0.05, EV1 - 0.05, 0.6, 4.4, cMadera.clone().lerp(cCal, 0.35), { sinTope: true });
          for (let u = EU0 + 0.5; u < EU1; u += 0.5) cara(marcas, [E(u, EV0 - 0.01, 0.6), E(u + 0.05, EV0 - 0.01, 0.6), E(u + 0.05, EV0 - 0.01, 4.4), E(u, EV0 - 0.01, 4.4)], cMaderaO, [uy, 0, ux]);
          const er = (EV0 + EV1) / 2;
          for (const [va, ref] of [[EV0 - 3.0, -1], [EV1 + 0.7, 1]]) cara(solido, [E(EU0 - 0.7, va, ref < 0 ? 3.6 : 4.2), E(EU1 + 0.7, va, ref < 0 ? 3.6 : 4.2), E(EU1 + 0.7, er, 6.0), E(EU0 - 0.7, er, 6.0)], cTeja, [0, 1, 0]);
          for (const uu of [EU0 - 0.4, EU0 + 4, EU0 + 8, EU0 + 12, EU1 + 0.4]) twu(solido, uu, EV0 - 2.7, 0.95, uu, EV0 - 2.7, 3.65, 0.09, 8, cMaderaO, null);
          for (const uu of [EU0, EU1]) cara(solido, [E(uu, EV0, 4.4), E(uu, EV1, 4.4), E(uu, er, 5.9), E(uu, er, 5.9)], cMadera, [uu === EU0 ? -ux : ux, 0, uu === EU0 ? uy : -uy]);
          for (let k = 0; k < 4; k++) { const uc = EU0 + 2.2 + k * 3.9, d = k === 1;
            cara(d ? solido : vid, [E(uc - (d ? 0.65 : 0.55), EV0 - 0.03, d ? 0.62 : 1.5), E(uc + (d ? 0.65 : 0.55), EV0 - 0.03, d ? 0.62 : 1.5), E(uc + (d ? 0.65 : 0.55), EV0 - 0.03, d ? 2.9 : 2.8), E(uc - (d ? 0.65 : 0.55), EV0 - 0.03, d ? 2.9 : 2.8)], d ? cMaderaO : cVent, [uy, 0, ux]); }
          twu(solido, 41, -95.4, 0.95, 41, -95.4, 4.6, 0.07, 8, cHierro, cHierro);
          cw(solido, 40.85, 41.15, -95.55, -95.25, 4.3, 4.75, cHierro);
          LUCES.push([41, -95.4, 4.5, 0, 0.9]);
        }

        // ================= las mallas fijas
        poner(piso, { desfase: 1 });
        poner(camino, { desfase: 2 });
        poner(marcas, { desfase: 4 });
        poner(solido, { desfase: 1 });
        poner(veg);
        const mVid = poner(vid, { desfase: 3 }); mats.splice(mats.indexOf(mVid.material), 1);
        const BV = noche ? 1.7 : 1.0;
        // de noche: charcos de luz bajo los faroles y la fogata
        if (noche) {
          const ch = nueva();
          for (const [u, v, , cl] of LUCES) {
            const R = cl === 1 ? 7 : 5.5, n = 20, q = ch.pos.length / 3, nuc = cLuz.clone().multiplyScalar(cl === 1 ? 0.24 : 0.15);
            const C = E(u, v, 0.12); ch.pos.push(C[0], C[1], C[2]); ch.col.push(nuc.r, nuc.g, nuc.b);
            for (let i = 0; i < n; i++) { const a = TAU * i / n, P = E(u + R * Math.cos(a), v + R * Math.sin(a), 0.12); ch.pos.push(P[0], P[1], P[2]); ch.col.push(0, 0, 0); }
            for (let i = 0; i < n; i++) ch.idx.push(q, q + 1 + i, q + 1 + ((i + 1) % n));
          }
          const mC = new THREE.Mesh(malla.geometria(ch), malla.material({ aditivo: true, desfase: 5 })); mC.frustumCulled = false; mC.renderOrder = 5; scene.add(mC);
        }
        // las luces (puntos que brillan: faroles, fogata, estación)
        const NL = LUCES.length, gP = new THREE.BufferGeometry(), posP = new Float32Array(NL * 3), aP = new Float32Array(NL * 2);
        LUCES.forEach(([u, v, h, cl, a], i) => { posP.set(E(u, v, h), i * 3); aP[i * 2] = noche ? a : 0; aP[i * 2 + 1] = cl; });
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 2));
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: cLuz }, cB: { value: cFuego } },
          transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "attribute vec2 aK; uniform float uPx, uTam; varying vec2 vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " float m = aK.y < 0.5 ? 1.6 : 2.6; gl_PointSize = aK.x > 0.0 ? clamp(m * uTam * uPx / max(1e-3, -mv.z), 2.0, 64.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA, cB; varying vec2 vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = vK.y < 0.5 ? cA : cB; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK.x * (exp(-r * r * 6.0) + 0.6 * exp(-r * r * 40.0)); gl_FragColor = vec4(s * a, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);

        // ================= la fila: carretas y recuas que esperan, pasan la tranca y siguen hacia la ciudad
        const NC = clamp(p.carretas | 0, 0, 6), NMu = clamp(p.mulas | 0, 0, 8), NR = Math.ceil(NMu / 2);
        const seq = [];
        for (let c = 0, q = 0, mu = NMu; c < NC || q < NR;) {
          const tocaC = c < NC && (q >= NR || c * NR <= q * NC);
          if (tocaC) { seq.push({ tipo: "carreta", L: 5.9 }); c++; }
          else { const n = Math.min(2, mu); mu -= n; seq.push({ tipo: "recua", n, L: n === 2 ? 5.5 : 2.3 }); q++; }
        }
        const NU = seq.length, GAP = 2.5, UF = -10.5, P = clamp(p.tranca_s || 8, 5, 20), T1 = 1.5, UF0 = 80, UF1 = 110;
        const pre = [0]; seq.forEach((x, k) => pre.push(pre[k] + x.L + GAP));
        const LMAX = NU ? Math.max(...seq.map((x) => x.L)) : 0;
        const VEL = Math.max(1.6, 1.3 * (LMAX + GAP) / (0.83 * P - 0.75));
        const KP = NU ? Math.ceil((UF1 - UF) / (VEL * P)) + 1 : 0, S = NU ? NU * Math.ceil((NU + KP + 2) / NU) : 0;
        const md = (i) => ((i % NU) + NU) % NU, Cf = (i) => Math.floor(i / NU) * pre[NU] + pre[md(i)];
        // dónde va la cabeza de la unidad i en t, y su escala (0 = no se ve): función pura de t
        const pos = (i, t) => {
          if (noche) return i < 0 || i >= NU ? [0, 0] : [UF - (Cf(i) - Cf(0)), 1];
          const m = Math.floor(t / P), f = t / P - m;
          if (i > m) {
            if (i > m + NU) return [0, 0];
            const qa = s3((f - 0.35) / 0.6), off = Cf(i) - Cf(m) - qa * (seq[md(m)].L + GAP);
            return [UF - off, i === m + NU ? qa : 1];
          }
          const tau = t - (i + 0.12) * P;
          if (tau <= 0) return [UF, 1];
          const s = UF + (tau < T1 ? VEL * tau * tau / (2 * T1) : VEL * (tau - T1 / 2));
          return s >= UF1 ? [s, 0] : [s, 1 - s3((s - UF0) / (UF1 - UF0))];
        };
        const slots = [];
        for (let sl = 0; sl < S; sl++) {
          const U = seq[sl % NU], g = new THREE.Group(), an = [], ruedas = [], k0 = Math.floor(hz(sl, 81) * 1000);
          g.rotation.order = "YXZ"; scene.add(g);
          if (U.tipo === "carreta") {
            g.add(malla0(geo("carreta" + (k0 % 3), (acc) => carreta(acc, k0 % 3))));
            for (const z of [-1, 1]) { const w = malla0(geo("rueda", rueda), -3.05, 0.78, z * 1.02); g.add(w); ruedas.push(w); }
            for (const z of [-0.5, 0.5]) { const A = animal(k0 + (z > 0 ? 1 : 0), false, false, true); A.g.position.set(-1.2 + 0.4, 0, z); g.add(A.g); an.push(A); }
          } else {
            for (let j = 0; j < U.n; j++) { const A = animal(k0 + j * 3, false, true, false); A.g.position.set(-1.2 - j * 3.2, 0, 0); g.add(A.g); an.push(A); }
            if (U.n === 2) g.add(malla0(geo("soga", (acc) => tubo(acc, [-2.4, 1.0, 0.04], [-3.5, 1.5, 0.0], 0.02, 4, cCal, null))));
          }
          slots.push({ g, an, ruedas, L: U.L, carreta: U.tipo === "carreta" });
        }
        // la gente: guardas (sin uniforme) y arrieros (los de cada unidad; de noche, sentados junto a la fogata)
        const camisas = [tonos.secundario.clone().multiplyScalar(0.8), tonos.muro.clone().multiplyScalar(0.95), tonos.arena.clone(), tonos.techo.clone().multiplyScalar(0.9), lin(COL.costa).multiplyScalar(0.85)];
        const NG = clamp(p.guardas | 0, 0, 3), NA = clamp(p.arrieros | 0, 0, 8);
        const posesG = noche ? ["de_pie", "sentado", "caminar"] : ["atender", "de_pie", "caminar"];
        const flG = NG ? ctx.flota("persona", NG, { tamano: K * 1.25, lev: 0, orden: 6, semilla: p.semilla % 991, color: (i) => camisas[(i + 3) % camisas.length], pose: (i) => posesG[i] }) : null;
        const ARR = [];   // [slot, lado]
        if (NU) for (let sl = 0; sl < S; sl++) { const k = sl % NU; if (k < NA) ARR.push([sl, 1]); if (k + NU < NA) ARR.push([sl, -1]); }
        const NFA = Math.max(NA, ARR.length);
        const flA = NA ? ctx.flota("persona", NFA, { tamano: K * 1.25, lev: 0, orden: 6, semilla: (p.semilla + 17) % 991, color: (i) => camisas[i % camisas.length],
          pose: (i) => (noche ? "sentado" : null) }) : null;
        const posesV = [{ nombre: "rastrillar" }, { nombre: "descargar", alto: 0.68, alcance: 0.6 }, { nombre: "clasificar", mesa: 0.72 }];
        const flV = NVe ? ctx.flota("persona", NVe, { tamano: K * 1.25, lev: 0, orden: 6, semilla: (p.semilla + 41) % 991, color: (i) => camisas[(i + 1) % camisas.length],
          pose: (i) => posesV[VEC[i].rol] }) : null;
        // el ganado que pasta en el potrero
        const reses = [0, 1, 2].map((j) => { const A = animal(j + 7, true, false, false); A.g.rotation.order = "YXZ"; A.g.scale.setScalar(M * 1.08); scene.add(A.g); return { A, R: 9 + 5 * hz(j, 91), f: hz(j, 92) * TAU, cu: 84 + 18 * (j - 1), cv: -108 + 10 * hz(j, 93) }; });

        return { id: p.id, M, r, ux, uy, W, E, noche, mats, vidrios: [mVid.material], BV, mTranca, slots, pos, NU, S, P, KP, VEL, flG, flA, ARR, NA,
          reses, mFuego, gP, aP, matP, NL, FU, FV, andar, flV, VEC };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.4 * kb;
        for (const m of s.vidrios) m.uniforms.uBrillo.value = s.BV * (1 + 0.2 * kb);
        const { r, ux, uy, W, E, M, noche } = s;
        const Ga = (u, v) => { const [x, y] = W(u, v); return ctx.altura(x, y); };
        // ---- la tranca: sube al empezar el ciclo, baja cuando ya pasó la del frente (de noche, abajo)
        const m = noche ? 0 : Math.floor(t / s.P), f = noche ? 0 : t / s.P - m;
        const up = noche || !s.NU ? 0 : s3((f - 0.02) / 0.1) * (1 - s3((f - 0.86) / 0.1));
        s.mTranca.rotation.x = up * 1.3;
        // ---- las unidades de la fila
        for (const q of s.slots) q.g.visible = false;
        const vista = {};   // slot → [s, k, vel]
        if (s.NU) {
          const i0 = noche ? 0 : m - s.KP, i1 = noche ? s.NU - 1 : m + s.NU;
          for (let i = i0; i <= i1; i++) {
            const [su, k] = s.pos(i, t);
            if (k <= 0) continue;
            const sl = ((i % s.S) + s.S) % s.S, q = s.slots[sl], vel = noche ? 0 : (su - s.pos(i, t - 0.1)[0]) / 0.1;
            const hH = Ga(su, 0), hT = Ga(su - q.L, 0), P = E(su, 0, 0);
            q.g.visible = true; q.g.position.set(P[0], hH, P[2]);
            q.g.rotation.y = r; q.g.rotation.z = Math.atan2(hH - hT, q.L * M); q.g.scale.setScalar(M * k);
            for (const A of q.an) s.andar(A, su, 0.42);
            for (const w of q.ruedas) w.rotation.z = -su / 0.78;
            vista[sl] = [su, k, vel, q];
          }
        }
        // ---- los arrieros: junto a su unidad (de noche, alrededor de la fogata)
        if (s.flA) {
          for (let i = 0; i < s.flA.n; i++) s.flA.poner(i, 0, 0, 1, 0, 0);
          if (noche) {
            for (let i = 0; i < s.NA; i++) {
              const a = TAU * (i + 0.3) / s.NA, [x, y] = W(s.FU + Math.cos(a) * 2.1, s.FV + Math.sin(a) * 2.1), [fx, fy] = W(s.FU, s.FV), l = Math.hypot(fx - x, fy - y) || 1;
              s.flA.poner(i, x, y, (fx - x) / l, (fy - y) / l, 1, 0, 0);
            }
          } else if (!s.NU) {
            for (let i = 0; i < s.NA; i++) { const [x, y] = W(-14 - i * 2.2, 5.2); s.flA.poner(i, x, y, ux, uy, 1, 0, 0); }
          } else {
            s.ARR.forEach(([sl, lado], i) => {
              const v = vista[sl]; if (!v) return;
              const [su, k, vel, q] = v, [x, y] = W(su - (q.carreta ? 1.9 : 1.3) - (lado < 0 ? 1.4 : 0), lado * 1.75);
              s.flA.poner(i, x, y, ux, uy, k, 0, vel);
            });
          }
          s.flA.listo();
        }
        // ---- los guardas
        if (s.flG) {
          const cara = (x, y, tu, tv) => { const [a, b] = W(tu, tv), l = Math.hypot(a - x, b - y) || 1; return [(a - x) / l, (b - y) / l]; };
          for (let i = 0; i < s.flG.n; i++) {
            let u, v, d, vel = 0;
            if (i === 2) {
              const L = 18, per = 2 * L / 1.0, q = (((t / per + 0.15) % 1) + 1) % 1, ida = q < 0.5;
              u = ida ? 4 + L * q * 2 : 4 + L - L * (q - 0.5) * 2; v = -7.2; vel = 1.0;
              d = ida ? [ux, uy] : [-ux, -uy];
            } else if (i === 0) {
              if (noche) { u = 1.4; v = -3.2; } else { u = -9.6; v = -7.3; }
              const [x, y] = W(u, v); d = noche ? cara(x, y, 1.4, 4) : cara(x, y, -16, 0);
            } else {
              if (noche) { u = -8.2; v = -14.0; } else { u = -6.6; v = -11.4; }
              const [x, y] = W(u, v); d = cara(x, y, u, 0);
            }
            const [x, y] = W(u, v);
            s.flG.poner(i, x, y, d[0], d[1], 1, 0, vel);
          }
          s.flG.listo();
        }
        // ---- los vecinos del cantón (de día; de noche ya no hay nadie trabajando)
        if (s.flV) {
          s.VEC.forEach((Q, i) => {
            if (noche) { s.flV.poner(i, 0, 0, 1, 0, 0); return; }
            if (Q.rol === 0) {   // rastrilla la faja, despacio de ida y vuelta a lo largo de la línea
              const a = Q.f + Q.w * t, u = Q.u + Q.A * Math.sin(a), du = Math.cos(a) >= 0 ? 1 : -1, vel = Math.abs(Q.A * Q.w * Math.cos(a)) * M;
              const [x, y] = W(u, Q.v); s.flV.poner(i, x, y, du * ux, du * uy, 1, 0, vel);
            } else if (Q.rol === 1) { const [x, y] = W(Q.u, Q.v); s.flV.poner(i, x, y, ux, uy, 1, 0, 0); }
            else { const [x, y] = W(Q.u, Q.v); s.flV.poner(i, x, y, ux, uy, 1, 0, 0); }
          });
          s.flV.listo();
        }
        // ---- el ganado: pasta mientras camina despacio en una vuelta
        for (const R of s.reses) {
          const w = 0.035, a = R.f + w * t, u = R.cu + R.R * Math.cos(a), v = R.cv + R.R * Math.sin(a);
          const P = E(u, v, 0); R.A.g.position.set(P[0], P[1], P[2]);
          const du = -Math.sin(a), dv = Math.cos(a); R.A.g.rotation.y = Math.atan2(du * uy + dv * ux, du * ux - dv * uy);
          s.andar(R.A, R.R * w * t, 0.25);
        }
        // ---- la fogata y los faroles titilan
        if (s.mFuego) { const k = 1 + 0.16 * Math.sin(t * 11.3) + 0.1 * Math.sin(t * 17.9 + 1.3); s.mFuego.scale.set(M, M * k, M); }
        if (noche) for (let i = 0; i < s.NL; i++) s.aP[i * 2] = (s.aP[i * 2 + 1] > 0.5 ? 0.85 : 0.8) * (1 + 0.12 * Math.sin(t * (i ? 13.1 : 7.3) + i * 2.1));
        s.gP.attributes.aK.needsUpdate = true;
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
