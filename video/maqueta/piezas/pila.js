// Pieza «pila» (ficha: pila.json; reglas: scripts/maqueta_tipos/pila.py): «¿cuánto es eso?»: un volumen puesto sobre un
// lugar conocido. Una pila de basura mezclada (o de tierra, o de agua) con la planta de un rectángulo (`largo_m` × `ancho_m`
// girado por `rumbo`) o de un polígono (`puntos`) y un alto final `alto_m`, en metros reales. Arranca en la fracción
// `inicio` del alto (0 = el lugar vacío) y sube con el evento `crecer` (que escribe la fracción de este cuadro).
// Cómo se ve: los LADOS en capas (una capa ≈ 1 m: tonos que se alternan, la panza de las bolsas a media capa, la junta
// hundida entre capas con una hilera de bolsas y botellas asomadas; el talud entra un poco hacia arriba), la SUPERFICIE de
// arriba irregular (montículos de ruido fijo que se aplanan contra el borde, manchas de bolsas negras, de color, papel y
// orgánico) sembrada de bolsas, botellas tendidas, cartones y restos; un faldón de cosas rodadas al pie y la sombra de
// contacto. Sin marcas, sin logos, sin texto. Las cosas van a su tamaño real hasta ≈ 110 m de lado y crecen con la pila
// (para leerse cuando la pila es de cientos de metros).
// Cómo crece (seek puro): un solo número por cuadro, f (0–1). Los lados están armados a su alto final y un shader los corta
// en la altura de f (nada se rehace); la superficie de arriba es un grupo que sube a esa altura y se encoge con el talud.
// `inicio` deja f en reposo antes de los eventos; `crecer` la fija en su `aplicar`; `en` la dibuja.
// Con vida: unas bolsas sueltas arriba se mecen e inflan con el viento y las botellas destellan (de noche, con la luz de la
// ciudad). `acento`: un filo en el acento rodea el borde de arriba (la pila protagonista). «resaltar» la aviva.
//
// Lo que publica para el evento `crecer` (MAQ.PILA.pilas[id]): {f0, f, alto_m, M (unidades por metro), ko (escala de
// las cosas), fijar(f), cima(f) → altura de escena del borde de arriba, muestras (n), punto(i, f) → [x, y, z] de escena del
// i-ésimo punto de la superficie con la pila en f, tonos (Colors de sus cosas), dibujar(acc, i, P, k) → la i-ésima cosa
// (bolsa, botella, orgánico, cartón según su hash) en un acumulador de ctx.malla, centrada en P (escena) y a escala k}.
(function (MAQ) {
  const PILA = MAQ.PILA = MAQ.PILA || {};
  PILA.pilas = PILA.pilas || {};

  MAQ.PIEZAS.pila = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp, GLSL_COMUN, uComun } = ctx;
      const noche = !!ES.noche, modoN = ES.modo === 1, dia = !!ES.dia, TAU = 2 * Math.PI;
      const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const ico1 = new THREE.IcosahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
      const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const KS = ctx.CFG.sombra_contacto || (dia ? 0.4 : 0.24);
      const sube = (c, k) => (modoN ? c.clone().lerp(tonos.muro, 0.25).multiplyScalar(k) : c.clone());

      // ---- los tonos de cada material (todos del estilo; de noche, levantados para leerse sobre el suelo oscuro)
      const L = (n) => lin(COL[n]);
      const PAL = {
        basura: () => {
          const masa = sube(tonos.calle.clone().lerp(tonos.techo, 0.35).multiplyScalar(0.78), 1.5);
          const negra = sube(tonos.asfalto.clone().lerp(tonos.linea, 0.2).multiplyScalar(0.85), 1.7);
          const gris = sube(tonos.pavimento.clone().lerp(tonos.asfalto, 0.3), 1.4);
          const blanca = tonos.arena.clone().lerp(L("luz"), 0.45).multiplyScalar(modoN ? 0.8 : 1);
          const azul = sube(L("mar").lerp(tonos.linea, 0.25), 1.2);
          const colorB = sube(tonos.secundario.clone().lerp(tonos.medio, 0.3).multiplyScalar(0.85), 1.1);
          const verdeB = sube(tonos.bien.clone().multiplyScalar(0.72), 1.2);
          const botella = tonos.agua.clone().lerp(L("luz"), 0.5);
          const botellaV = tonos.verde.clone().lerp(L("luz"), 0.4);
          const organico = sube(tonos.techo.clone().lerp(tonos.campo2, 0.5).multiplyScalar(0.72), 1.5);
          const hoja = sube(tonos.verde.clone().lerp(tonos.bien, 0.3).multiplyScalar(0.75), 1.4);
          const cascara = sube(tonos.medio.clone().lerp(tonos.techo, 0.35).multiplyScalar(0.9), 1.1);
          const carton = sube(tonos.arena.clone().lerp(tonos.techo, 0.45), 1.15);
          const blancaV = blanca.clone().lerp(tonos.arena, 0.3);
          const negraB = sube(tonos.asfalto.clone().lerp(tonos.linea, 0.1).multiplyScalar(0.7), 1.2);   // la bolsa negra, que se lea negra también de noche
          return {
            capas: [masa, negra.clone().lerp(masa, 0.35), organico.clone().lerp(masa, 0.4), masa.clone().lerp(negra, 0.5)],
            manchas: [[masa, 3], [negra, 3.5], [blanca, 1.1], [organico, 2], [hoja, 0.6], [carton, 0.8], [gris, 0.4]],
            // arriba: bultos (montones de bolsas aplastadas, cartón y orgánico) con su pliegue oscuro entre uno y otro, y
            // encima las cosas sueltas: sobre todo bolsas negras y blancas, botellas y cartón (cajas y láminas)
            bultos: [[masa, 1.8], [negraB, 2.4], [organico, 2.2], [carton.clone().multiplyScalar(0.85), 1.2], [blancaV, 1.0], [hoja, 0.1]],
            cosas: [["bolsa", negraB, 6], ["bolsa", blanca, 4.2], ["bolsa", gris, 0.6], ["bolsa", azul, 0.4], ["bolsa", colorB, 0.6],
              ["bolsa", verdeB, 0.12], ["botella", botella, 2.4], ["botella", botellaV, 0.9], ["organico", organico, 1.4],
              ["organico", hoja, 0.35], ["organico", cascara, 0.6], ["carton", carton, 2.0]],
            amp: 1.6, densidad: 3.2, k: 1.15, brillos: true, sueltas: [blanca, negraB, colorB, blanca],
          };
        },
        tierra: () => {
          const t1 = sube(tonos.techo.clone().lerp(tonos.campo2, 0.55).multiplyScalar(0.85), 1.45);
          const t2 = sube(tonos.calle.clone().lerp(tonos.techo, 0.6).multiplyScalar(0.8), 1.45);
          const t3 = sube(tonos.arena.clone().lerp(tonos.techo, 0.5).multiplyScalar(0.9), 1.3);
          const piedra = sube(tonos.pavimento.clone().lerp(tonos.muro, 0.4), 1.3);
          return { capas: [t1, t2, t3, t2.clone().lerp(t1, 0.5)], manchas: [[t1, 3], [t2, 2], [t3, 1.5]],
            cosas: [["organico", t2, 3], ["organico", t3, 2], ["organico", piedra, 1.5]], amp: 0.75, densidad: 0.35, brillos: false, sueltas: [] };
        },
        agua: () => {
          const a1 = sube(tonos.agua.clone(), 1.25), a2 = sube(tonos.agua.clone().lerp(tonos.linea, 0.18), 1.25);
          const a3 = tonos.agua.clone().lerp(L("luz"), 0.25);
          return { capas: [a1, a2, a1.clone().lerp(a3, 0.3), a2], manchas: [[a1, 3], [a3, 1], [a2, 2]], cosas: [], amp: 0.12, densidad: 0, brillos: true, sueltas: [] };
        },
      };

      // ---- material de los lados: el de superficie, cortado en la altura de la pila (uTope, en y de escena)
      const matLados = () => new THREE.ShaderMaterial({
        uniforms: { ...uComun(), uBrillo: { value: 1 }, uTope: { value: -1e9 } }, side: THREE.DoubleSide,
        vertexShader: "attribute vec3 color; attribute float aH; varying vec3 vCol, vPos; varying float vH; void main(){ vCol = color; vH = aH; vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        fragmentShader: GLSL_COMUN + "uniform float uBrillo, uTope; varying vec3 vCol, vPos; varying float vH;" +
          "void main(){ if (vH > uTope) discard; gl_FragColor = vec4(salida(niebla(vCol * uBrillo, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });

      return piezas.map((p, np) => {
        const P0 = PAL[p.material] ? PAL[p.material]() : PAL.basura();
        const M = metros(1), H = p.alto_m, r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const cr = Math.cos(r), sr = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const ruido = (x, y, cel, k) => {                 // ruido de valor fijo, 0–1
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz(((a & 4095) * 4099 + (b & 4095)) % 1000003, k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const elegir = (lista, x, col) => {               // lista [[…, peso]] → un elemento por x (0–1)
          let tot = 0; for (const e of lista) tot += e[e.length - 1];
          let a = x * tot; for (const e of lista) { a -= e[e.length - 1]; if (a <= 0) return e; }
          return lista[lista.length - 1];
        };

        // ---- la planta en metros locales (u: a lo largo del rumbo, v: a lo ancho), en sentido antihorario
        let pol;
        if (p.puntos) {
          pol = [];
          for (let i = 0; i + 1 < p.puntos.length; i += 2) {
            const du = (p.puntos[i] - p.x) / M, dv = (p.puntos[i + 1] - p.y) / M;
            pol.push([du * ux + dv * uy, -du * uy + dv * ux]);
          }
        } else {
          const a = p.largo_m / 2, b = p.ancho_m / 2;
          pol = [[-a, -b], [a, -b], [a, b], [-a, b]];
        }
        let area = 0, per = 0;
        for (let i = 0; i < pol.length; i++) { const A = pol[i], B = pol[(i + 1) % pol.length]; area += A[0] * B[1] - B[0] * A[1]; per += Math.hypot(B[0] - A[0], B[1] - A[1]); }
        if (area < 0) { pol.reverse(); area = -area; }
        area /= 2;
        let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
        for (const [u, v] of pol) { u0 = Math.min(u0, u); u1 = Math.max(u1, u); v0 = Math.min(v0, v); v1 = Math.max(v1, v); }
        const uc = (u0 + u1) / 2, vc = (v0 + v1) / 2, Lb = Math.max(0.5, u1 - u0), Ab = Math.max(0.5, v1 - v0);
        const dentro = (u, v) => { let c = false;
          for (let i = 0, j = pol.length - 1; i < pol.length; j = i++) { const [ax, ay] = pol[i], [bx, by] = pol[j];
            if ((ay > v) !== (by > v) && u < (bx - ax) * (v - ay) / ((by - ay) || 1e-9) + ax) c = !c; }
          return c; };
        const alBorde = (u, v) => { let d = Infinity;
          for (let i = 0; i < pol.length; i++) { const [ax, ay] = pol[i], [bx, by] = pol[(i + 1) % pol.length];
            const ex = bx - ax, ey = by - ay, l2 = ex * ex + ey * ey || 1e-9, s = clamp(((u - ax) * ex + (v - ay) * ey) / l2, 0, 1);
            d = Math.min(d, Math.hypot(u - ax - s * ex, v - ay - s * ey)); }
          return d; };

        // ---- medidas: capas, talud, escala de las cosas, rugosidad
        const ko = clamp(Math.sqrt(area) / 110, 1, 6);
        const N = Math.max(2, Math.min(16, Math.round(H / 1.0))), hL = H / N;
        const inR = 2 * area / Math.max(per, 1e-6);                       // ≈ el radio de lo que cabe adentro
        const D = Math.min(0.3 * H, 0.15 * inR);                          // cuánto entra el talud hasta arriba
        const J = clamp(0.1 * hL + 0.05, 0.04, 0.5 * ko);                 // lo dentado del borde
        const BUL = clamp(0.1 * hL + 0.05, 0.04, 0.6 * ko);               // la panza de cada capa
        const AMP = clamp(0.12 * H, 0.04, 0.8 * ko) * P0.amp;             // el alto de los montículos de arriba
        const inset = (hv) => D * clamp(hv / H, 0, 1);

        // ---- de local a escena; la pila sigue al suelo: cada punto se mide desde el suelo que tiene debajo (en una plaza en
        // pendiente, los 5 m son 5 m en todo el borde, no desde el punto más bajo)
        const cx = p.x, cy = p.y;
        const SX = (u, v) => [cx + (u * ux - v * uy) * M, cy + (u * uy + v * ux) * M];
        const G = (u, v) => { const [x, y] = SX(u, v); return ctx.altura(x, y); };
        const B = G(uc, vc);
        const E = (u, v, h) => { const [x, y] = SX(u, v); return [x, ctx.altura(x, y) + h * M, -y]; };
        const Lc = (u, v, h) => [(u - uc) * M, G(u, v) + h * M, -(v - vc) * M];   // local del grupo de arriba (y: suelo + h)
        const luzR = (nx, ny, nz) => sombra(nx * cr + nz * sr, ny, -nx * sr + nz * cr);

        // ---- primitivas con la luz horneada (acc.rot: el acumulador vive en el grupo girado)
        const nueva = (rot) => Object.assign(malla.nueva(), { rot: !!rot });
        const luz = (acc, nx, ny, nz) => (acc.rot ? luzR(nx, ny, nz) : sombra(nx, ny, nz));
        const cara = (acc, P, col, ref) => {
          const [A, Bq, , Dq] = P, e1 = [Bq[0] - A[0], Bq[1] - A[1], Bq[2] - A[2]], e2 = [Dq[0] - A[0], Dq[1] - A[1], Dq[2] - A[2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          const l = luz(acc, nx, ny, nz), q = acc.pos.length / 3;
          for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        const gema = (acc, tri, P, rx, ry, rz, rot, col, plana = 0.25, inc = 0) => {
          const c1 = Math.cos(rot), s1 = Math.sin(rot), ci = Math.cos(inc), si = Math.sin(inc), v = [];
          for (let i = 0; i < tri.length; i += 3) {
            let x = tri[i] * rx * M, y = tri[i + 1] * ry * M, z = tri[i + 2] * rz * M;
            const y2 = y * ci - x * si, x2 = x * ci + y * si; x = x2; y = y2;          // un poco tumbada
            v.push(P[0] + x * c1 - z * s1, P[1] + y, P[2] + x * s1 + z * c1);
          }
          const c = new THREE.Color();
          for (let i = 0; i < v.length; i += 9) {
            const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const n = Math.hypot(nx, ny, nz) || 1;
            c.copy(col).multiplyScalar(plana + (1 - plana) * luz(acc, nx / n, ny / n, nz / n));
            const q = acc.pos.length / 3;
            for (let j = 0; j < 9; j += 3) { acc.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        };
        // un prisma de `lados` de A a B (puntos ya en la escena o en el grupo), radio en metros
        const barra = (acc, A, Bq, rr, col, lados = 6) => {
          const d = [Bq[0] - A[0], Bq[1] - A[1], Bq[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
          let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]], R = rr * M;
          for (let i = 0; i < lados; i++) {
            const t0 = TAU * i / lados, t1 = TAU * (i + 1) / lados, o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * R);
            const va = o(t0), vb = o(t1), nm = o((t0 + t1) / 2);
            cara(acc, [[A[0] + va[0], A[1] + va[1], A[2] + va[2]], [A[0] + vb[0], A[1] + vb[1], A[2] + vb[2]],
              [Bq[0] + vb[0], Bq[1] + vb[1], Bq[2] + vb[2]], [Bq[0] + va[0], Bq[1] + va[1], Bq[2] + va[2]]], col, nm);
          }
        };
        // una caja girada (medios lados a, b, c en metros) centrada en P
        const cajaR = (acc, P, a, b, c3, rot, col, inc = 0) => {
          const c1 = Math.cos(rot), s1 = Math.sin(rot), ci = Math.cos(inc), si = Math.sin(inc);
          const V = (x, y, z) => { x *= a * M; y *= c3 * M; z *= b * M; const y2 = y * ci - x * si, x2 = x * ci + y * si;
            return [P[0] + x2 * c1 - z * s1, P[1] + y2, P[2] + x2 * s1 + z * c1]; };
          const C = P, Q = [[[-1, 1, -1], [1, 1, -1], [1, 1, 1], [-1, 1, 1]], [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1]],
            [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], [[-1, -1, -1], [-1, -1, 1], [-1, 1, 1], [-1, 1, -1]], [[1, -1, -1], [1, -1, 1], [1, 1, 1], [1, 1, -1]]];
          for (const q of Q) { const W = q.map((e) => V(...e)), m = [0, 1, 2].map((j) => (W[0][j] + W[1][j] + W[2][j] + W[3][j]) / 4 - C[j]); cara(acc, W, col, m); }
        };
        // una cosa de la pila: bolsa (con su nudo), botella tendida (con cuello), orgánico o cartón; s = escala, P en el acc
        const cosa = (acc, i, P, s, cual) => {
          const [forma, col0] = cual || elegir(P0.cosas, hz(i, 301));
          const col = col0.clone().multiplyScalar(0.84 + 0.3 * hz(i, 302)), rot = hz(i, 303) * TAU, inc = (hz(i, 304) - 0.5) * 0.8;
          if (forma === "bolsa") {
            const rx = (0.38 + 0.2 * hz(i, 305)) * s, ry = (0.24 + 0.12 * hz(i, 306)) * s, rz = (0.32 + 0.16 * hz(i, 307)) * s;
            gema(acc, ico, [P[0], P[1] + ry * 0.55 * M, P[2]], rx, ry, rz, rot, col, 0.3, inc * 0.4);
            gema(acc, oct, [P[0], P[1] + ry * 1.45 * M, P[2]], 0.09 * s, 0.11 * s, 0.09 * s, rot, col.clone().multiplyScalar(0.85), 0.3);
          } else if (forma === "botella") {
            const lg = (0.3 + 0.08 * hz(i, 308)) * 1.6 * s, rr = 0.045 * 1.6 * s, dx = Math.cos(rot), dz = Math.sin(rot), y = P[1] + rr * M;
            const A = [P[0] - dx * lg / 2 * M, y, P[2] - dz * lg / 2 * M], Bq = [P[0] + dx * lg * 0.3 * M, y, P[2] + dz * lg * 0.3 * M];
            const Cq = [P[0] + dx * lg / 2 * M, y, P[2] + dz * lg / 2 * M];
            barra(acc, A, Bq, rr, col, 6); barra(acc, Bq, Cq, rr * 0.45, col.clone().multiplyScalar(0.9), 5);
          } else if (forma === "carton") {
            if (hz(i, 313) < 0.45) {                                     // una caja aplastada a medias, ladeada
              const a = (0.26 + 0.1 * hz(i, 309)) * s, b = (0.2 + 0.08 * hz(i, 310)) * s, c3 = (0.12 + 0.1 * hz(i, 314)) * s;
              cajaR(acc, [P[0], P[1] + c3 * 0.8 * M, P[2]], a, b, c3, rot, col, inc * 0.7);
              cajaR(acc, [P[0], P[1] + (c3 * 1.8 + 0.01 * s) * M, P[2]], a * 0.98, b * 0.6, 0.012 * s, rot, col.clone().multiplyScalar(0.8), inc * 0.7 + 0.5);
            } else cajaR(acc, [P[0], P[1] + 0.05 * s * M, P[2]], (0.36 + 0.14 * hz(i, 309)) * s, (0.25 + 0.1 * hz(i, 310)) * s, 0.05 * s, rot, col, inc * 0.9);
          } else {
            const rr = (0.16 + 0.14 * hz(i, 311)) * s;
            gema(acc, hz(i, 312) < 0.5 ? oct : ico, [P[0], P[1] + rr * 0.5 * M, P[2]], rr * 1.2, rr * 0.7, rr, rot, col, 0.3, inc);
          }
        };

        // ================= los LADOS en capas (escena; se cortan en la altura de f)
        // el perímetro densificado: cada vértice con su normal hacia afuera (inglete acotado)
        const seg = Math.max(1.2, per / 150), V = [];
        for (let i = 0; i < pol.length; i++) {
          const A = pol[i], Bq = pol[(i + 1) % pol.length], l = Math.hypot(Bq[0] - A[0], Bq[1] - A[1]), k = Math.max(1, Math.ceil(l / seg));
          for (let j = 0; j < k; j++) V.push({ u: A[0] + (Bq[0] - A[0]) * j / k, v: A[1] + (Bq[1] - A[1]) * j / k, esquina: j === 0 });
        }
        const NV = V.length;
        const nEdge = (a, b) => { const ex = b.u - a.u, ey = b.v - a.v, l = Math.hypot(ex, ey) || 1; return [ey / l, -ex / l]; };
        for (let i = 0; i < NV; i++) {
          const a = V[(i - 1 + NV) % NV], b = V[i], c = V[(i + 1) % NV], n1 = nEdge(a, b), n2 = nEdge(b, c);
          let nx = n1[0] + n2[0], ny = n1[1] + n2[1]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
          const m = 1 / Math.max(0.5, nx * n1[0] + ny * n1[1]);
          V[i].nx = nx * m; V[i].ny = ny * m;
        }
        // las filas: 0 enterrada; impares a media capa (la panza); pares la junta (hundida)
        const filas = [];
        for (let j = 0; j <= 2 * N; j++) filas.push(j === 0 ? -0.35 : j * hL / 2);
        const offs = (i, j) => {                                         // cuánto entra el borde en el vértice i, fila j (m)
          const h = filas[j]; let d = inset(Math.max(0, h));
          if (j % 2 === 1) d -= BUL * (0.6 + 0.8 * hz(i * 7 + j, 21));
          else if (j > 0 && j < 2 * N) d += 0.05 * hL + 0.03;
          return d + (hz(i * 131 + j, 17) - 0.5) * 2 * J;
        };
        const PW = (i, j) => { const q = V[i % NV], d = offs(i % NV, j); return E(q.u - q.nx * d, q.v - q.ny * d, filas[j]); };
        const lados = nueva(false);
        for (let j = 0; j < 2 * N; j++) {
          const capa = Math.floor(j / 2), base = P0.capas[capa % P0.capas.length];
          for (let i = 0; i < NV; i++) {
            const q = V[i], k = i * 53 + j * 977, mm = hz(k, 31) < 0.3 ? elegir(P0.manchas, hz(k, 32))[0] : base;
            const col = mm.clone().multiplyScalar((j % 2 ? 1.0 : 0.82) * (0.84 + 0.28 * hz(k, 33)));
            const ref = [q.nx * ux - q.ny * uy, 0, -(q.nx * uy + q.ny * ux)];
            cara(lados, [PW(i, j), PW(i + 1, j), PW(i + 1, j + 1), PW(i, j + 1)], col, ref);
          }
        }
        // en cada junta, una hilera de cosas asomadas (y, a media capa, alguna suelta): marcan las capas
        const NJ = Math.max(1, N - 1), porJunta = Math.max(6, Math.min(Math.floor(per / (1.5 * ko)), Math.floor(720 / NJ)));
        for (let j = 2; j < 2 * N; j += 2) for (let n = 0; n < porJunta; n++) {
          const k = j * 7001 + n, s = per * (n + 0.8 * hz(k, 41)) / porJunta;
          let acum = 0, i = 0;
          while (i < NV - 1) { const l = Math.hypot(V[(i + 1) % NV].u - V[i].u, V[(i + 1) % NV].v - V[i].v); if (acum + l >= s) break; acum += l; i++; }
          const a = V[i], b = V[(i + 1) % NV], lseg = Math.hypot(b.u - a.u, b.v - a.v) || 1, w = clamp((s - acum) / lseg, 0, 1);
          const nx = a.nx + (b.nx - a.nx) * w, ny = a.ny + (b.ny - a.ny) * w;
          const d = inset(filas[j]) - 0.12 * ko, h = filas[j] - 0.25 * ko + 0.3 * hz(k, 42) * hL;
          cosa(lados, k, E(a.u + (b.u - a.u) * w - nx * d, a.v + (b.v - a.v) * w - ny * d, h), ko * (0.85 + 0.4 * hz(k, 43)));
        }
        const matL = matLados();
        const gL = malla.geometria(lados), aH = new Float32Array(lados.pos.length / 3);
        for (let i = 0; i < aH.length; i++) { const x = lados.pos[3 * i], y = -lados.pos[3 * i + 2]; aH[i] = (lados.pos[3 * i + 1] - ctx.altura(x, y)) / M; }
        gL.setAttribute("aH", new THREE.BufferAttribute(aH, 1));
        const mLados = new THREE.Mesh(gL, matL); mLados.frustumCulled = false; mLados.renderOrder = 4; scene.add(mLados);

        // ================= el faldón: cosas rodadas al pie, sobre el suelo (aparecen con la primera capa)
        const falda = nueva(false), NF = Math.min(220, Math.floor(per / (1.8 * ko)));
        if (P0.cosas.length) for (let n = 0; n < NF; n++) {
          const i = Math.floor(hz(n, 51) * NV), q = V[i], b = V[(i + 1) % NV], w = hz(n, 52);
          const u = q.u + (b.u - q.u) * w, v = q.v + (b.v - q.v) * w, d = (0.15 + 2.2 * Math.pow(hz(n, 53), 1.6)) * ko;
          const [x, y] = SX(u + q.nx * d, v + q.ny * d);
          cosa(falda, 9000 + n, [x, ctx.altura(x, y) + 0.02 * M, -y], ko * (0.7 + 0.4 * hz(n, 54)));
        }
        const matF = malla.material({ desfase: 1 });
        const mFalda = new THREE.Mesh(malla.geometria(falda), matF); mFalda.frustumCulled = false; mFalda.renderOrder = 5; scene.add(mFalda);

        // ================= la sombra de contacto: un anillo suave alrededor del pie
        const so = { pos: [], a: [], idx: [] }, PAD = Math.max(1.5, 0.06 * Math.sqrt(area)) * ko;
        for (let i = 0; i < NV; i++) {
          const q = V[i];
          for (const [d, a] of [[-0.4, 1], [PAD, 0]]) { const [x, y] = SX(q.u + q.nx * d, q.v + q.ny * d); so.pos.push(x, ctx.altura(x, y) + 0.04 * M, -y); so.a.push(a); }
        }
        for (let i = 0; i < NV; i++) { const a = 2 * i, b = 2 * ((i + 1) % NV); so.idx.push(a, a + 1, b + 1, a, b + 1, b); }
        const gS = new THREE.BufferGeometry();
        gS.setAttribute("position", new THREE.BufferAttribute(new Float32Array(so.pos), 3));
        gS.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(so.a), 1));
        gS.setIndex(so.idx);
        const matS = new THREE.ShaderMaterial({ uniforms: { uK: { value: 0 } }, transparent: true, depthWrite: false, side: THREE.DoubleSide,
          polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
          vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: "uniform float uK; varying float vA; void main(){ gl_FragColor = vec4(0.0, 0.0, 0.0, uK * vA * vA); }" });
        const mS = new THREE.Mesh(gS, matS); mS.frustumCulled = false; mS.renderOrder = 3; scene.add(mS);

        // ================= ARRIBA: un grupo (girado por rumbo) que sube con f y se encoge con el talud
        const grupo = new THREE.Group(); grupo.rotation.y = r; scene.add(grupo);
        { const [x, y] = SX(uc, vc); grupo.position.set(x, 0, -y); }
        const arriba = nueva(true);
        // los montículos: ruido de dos escalas que se apaga contra el borde (z ≥ 0, en metros)
        const cs = Math.max(0.45, Math.max(Lb, Ab) / 60), cayo = 1.5 * ko + 2 * cs;
        const zA = (u, v) => {
          const e = clamp(alBorde(u, v) / cayo, 0, 1), ee = e * e * (3 - 2 * e);
          const n = 0.65 * ruido(u, v, 4.5 * ko, 61) + 0.35 * ruido(u, v, 1.6 * ko, 62);
          return AMP * ee * (0.25 + 0.75 * n);
        };
        // los BULTOS (solo basura): una rejilla temblada de montones (≈ 2.4 m) que se abultan con su propio alto; entre uno y
        // otro, el pliegue (F2 − F1 chico) queda hundido y oscuro: de lejos se lee como cosas apiladas, no como baldosas
        const CB = 2.4 * ko, HB = P0.bultos ? clamp(0.12 * H + 0.15, 0.25, 0.9 * ko) : 0;
        const bulto = (u, v) => {
          if (!P0.bultos) return { z: 0, c: 1, id: 0 };
          const a0 = Math.floor(u / CB), b0 = Math.floor(v / CB);
          let F1 = 1e9, F2 = 1e9, id = 0, R = 1;
          for (let da = -1; da <= 1; da++) for (let db = -1; db <= 1; db++) {
            const a = a0 + da, b = b0 + db, k = ((a & 2047) * 2053 + (b & 2047)) % 999983;
            const px = (a + 0.12 + 0.76 * hz(k, 121)) * CB, py = (b + 0.12 + 0.76 * hz(k, 122)) * CB;
            const sx = 0.8 + 0.45 * hz(k, 124), d = Math.hypot((u - px) / sx, v - py);
            if (d < F1) { F2 = F1; F1 = d; id = k; R = sx; } else if (d < F2) F2 = d;
          }
          const c = clamp((F2 - F1) / (0.32 * CB), 0, 1), dome = clamp(1 - Math.pow(F1 / (0.85 * CB), 2), 0, 1);
          const e = clamp(alBorde(u, v) / cayo, 0, 1);
          return { z: HB * (0.45 + 0.75 * hz(id, 123)) * Math.sqrt(dome) * (0.35 + 0.65 * c) * (0.3 + 0.7 * e) * R, c, id };
        };
        const zT = (u, v) => zA(u, v) + bulto(u, v).z;
        const AMPT = AMP + HB * 1.3;
        // la tapa plana (bajo los montículos) y la falda corta que esconde el canto
        { const pts = pol.map(([u, v]) => new THREE.Vector2(u, v)), q0 = arriba.pos.length / 3, cm = P0.capas[(N - 1) % P0.capas.length].clone().multiplyScalar(0.92), l = luzR(0, 1, 0);
          // solo en un polígono (en un rectángulo la malla lo cubre todo): tapa las celdas cortadas por el borde. Va por debajo
          // de todo el desnivel del suelo bajo la planta: sus triángulos grandes no siguen al suelo y no deben asomar
          if (p.puntos) {
            let g0 = Infinity, g1 = -Infinity;
            for (let i = 0; i <= 12; i++) for (let j = 0; j <= 12; j++) { const u = u0 + Lb * i / 12, v = v0 + Ab * j / 12; if (dentro(u, v)) { const g = G(u, v); g0 = Math.min(g0, g); g1 = Math.max(g1, g); } }
            const hb = -0.03 - (isFinite(g1) ? (g1 - g0) / M : 0);
            for (const [u, v] of pol) { const P = Lc(u, v, hb); arriba.pos.push(...P); arriba.col.push(cm.r * l, cm.g * l, cm.b * l); }
            for (const t of THREE.ShapeUtils.triangulateShape(pts, [])) arriba.idx.push(q0 + t[0], q0 + t[1], q0 + t[2]);
          }
          const hf = Math.min(0.45 * hL + 0.1, 0.6 * ko);
          for (let i = 0; i < NV; i++) {
            const a = V[i], b = V[(i + 1) % NV], k = 70000 + i, cc = P0.capas[(N - 1) % P0.capas.length].clone().multiplyScalar(0.8 + 0.25 * hz(k, 71));
            const ja = (hz(k, 72) - 0.5) * J, jb = (hz(70000 + (i + 1) % NV, 72) - 0.5) * J;
            cara(arriba, [Lc(a.u + a.nx * ja, a.v + a.ny * ja, 0.02), Lc(b.u + b.nx * jb, b.v + b.ny * jb, 0.02), Lc(b.u, b.v, -hf * (0.7 + 0.3 * hz(k, 73))), Lc(a.u, a.v, -hf)], cc, [a.nx, 0, -a.ny]);
          }
        }
        // la malla de montículos, por celdas enteras adentro; cada celda con su mancha
        if (P0.bultos) {
          // basura: una rejilla fina con vértices compartidos; el color y la luz van por vértice (sin bordes de celda), el color
          // del bulto con su pliegue oscuro y la luz de la normal real (el relieve se lee también con la cámara baja)
          const cb = Math.max(0.55, Math.max(Lb, Ab) / 170), mu = Math.min(170, Math.ceil(Lb / cb)), mv = Math.min(170, Math.ceil(Ab / cb));
          const du = Lb / mu, dv = Ab / mv, q0 = arriba.pos.length / 3, ok = [], Z = [], BI = [];
          for (let i = 0; i <= mu; i++) for (let j = 0; j <= mv; j++) {
            const u = u0 + du * i, v = v0 + dv * j, dn = dentro(u, v), b = bulto(u, v);
            ok.push(dn); BI.push(b); Z.push(zA(u, v) + b.z);
          }
          const W = (i, j) => Z[clamp(i, 0, mu) * (mv + 1) + clamp(j, 0, mv)];
          const cc = new THREE.Color();
          for (let i = 0; i <= mu; i++) for (let j = 0; j <= mv; j++) {
            const n = i * (mv + 1) + j, u = u0 + du * i, v = v0 + dv * j, b = BI[n];
            const gx = (W(i + 1, j) - W(i - 1, j)) / (2 * du), gy = (W(i, j + 1) - W(i, j - 1)) / (2 * dv);
            const ln = Math.hypot(gx, 1, gy), l = luzR(-gx / ln, 1 / ln, gy / ln);
            cc.copy(elegir(P0.bultos, hz(b.id, 125))[0]).multiplyScalar((0.8 + 0.32 * hz(b.id, 126)) * (0.5 + 0.5 * b.c) * (0.92 + 0.16 * ruido(u, v, 0.9 * ko, 127)));
            const P = Lc(u, v, 0.01 + Z[n]);
            arriba.pos.push(P[0], P[1], P[2]); arriba.col.push(cc.r * l, cc.g * l, cc.b * l);
          }
          for (let i = 0; i < mu; i++) for (let j = 0; j < mv; j++) {
            const a = i * (mv + 1) + j, b = a + mv + 1;
            if (!(ok[a] && ok[a + 1] && ok[b] && ok[b + 1])) continue;
            arriba.idx.push(q0 + a, q0 + b, q0 + b + 1, q0 + a, q0 + b + 1, q0 + a + 1);
          }
        }
        const nu = P0.bultos ? 0 : Math.min(80, Math.ceil(Lb / cs)), nv = Math.min(80, Math.ceil(Ab / cs));
        const zG = [];
        for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) { const u = u0 + Lb * i / nu, v = v0 + Ab * j / nv; zG.push(dentro(u, v) ? zA(u, v) : null); }
        const Zg = (i, j) => zG[i * (nv + 1) + j];
        for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
          const z00 = Zg(i, j), z10 = Zg(i + 1, j), z11 = Zg(i + 1, j + 1), z01 = Zg(i, j + 1);
          if (z00 === null || z10 === null || z11 === null || z01 === null) continue;
          const ua = u0 + Lb * i / nu, ub = u0 + Lb * (i + 1) / nu, va = v0 + Ab * j / nv, vb = v0 + Ab * (j + 1) / nv, k = i * 811 + j;
          const mm = elegir(P0.manchas, clamp(ruido((ua + ub) / 2, (va + vb) / 2, 2.2 * ko, 63) * 0.7 + 0.3 * hz(k, 64), 0, 0.999))[0];
          const col = mm.clone().multiplyScalar(0.86 + 0.22 * hz(k, 65));
          cara(arriba, [Lc(ua, va, 0.01 + z00), Lc(ub, va, 0.01 + z10), Lc(ub, vb, 0.01 + z11), Lc(ua, vb, 0.01 + z01)], col, null);
        }
        // las cosas sembradas arriba (y unas muestras de la superficie para el evento crecer)
        const muestra = (n, k0) => {                                     // un punto adentro, lejos del canto (o null)
          for (let tr = 0; tr < 8; tr++) {
            const u = u0 + Lb * hz(n * 13 + tr, k0), v = v0 + Ab * hz(n * 13 + tr, k0 + 1);
            if (dentro(u, v) && alBorde(u, v) > 0.35 * ko) return [u, v];
          }
          return null;
        };
        const NO = Math.round(clamp(area / (4.5 * ko * ko), 40, 760) * P0.densidad), brillos = [];  // basura: hasta ≈ 2,400
        for (let n = 0; n < NO; n++) {
          const q = muestra(n, 81); if (!q) continue;
          const cual = elegir(P0.cosas, hz(n, 301));
          cosa(arriba, n, Lc(q[0], q[1], zT(q[0], q[1]) - 0.04 * ko), ko * (P0.k || 1) * (0.85 + 0.35 * hz(n, 82)), cual);
          if (P0.brillos && cual[0] === "botella") brillos.push([q[0], q[1], zT(q[0], q[1]) + 0.12 * ko, hz(n, 83)]);
        }
        if (P0.brillos && !P0.cosas.length) for (let n = 0; n < 40; n++) { const q = muestra(n, 85); if (q) brillos.push([q[0], q[1], zA(q[0], q[1]) + 0.02, hz(n, 86)]); }
        const matA = malla.material({ desfase: 1 });
        const mArriba = new THREE.Mesh(malla.geometria(arriba), matA); mArriba.frustumCulled = false; mArriba.renderOrder = 5; grupo.add(mArriba);

        // el filo en el acento (la pila protagonista): una cinta de canto alrededor del borde de arriba
        let matFilo = null;
        if (p.acento) {
          const filo = nueva(true), ac = tonos.acento.clone(), wf = Math.max(0.22, 0.004 * Math.sqrt(area)) * ko, hf = 0.35 * ko;
          for (let i = 0; i < NV; i++) {
            const a = V[i], b = V[(i + 1) % NV], o = 0.06;
            cara(filo, [Lc(a.u + a.nx * o, a.v + a.ny * o, 0.04 + AMP * 0.1), Lc(b.u + b.nx * o, b.v + b.ny * o, 0.04 + AMP * 0.1),
              Lc(b.u + b.nx * o, b.v + b.ny * o, -hf), Lc(a.u + a.nx * o, a.v + a.ny * o, -hf)], ac, [a.nx, 0, -a.ny]);
            cara(filo, [Lc(a.u + a.nx * o, a.v + a.ny * o, 0.04 + AMP * 0.1), Lc(b.u + b.nx * o, b.v + b.ny * o, 0.04 + AMP * 0.1),
              Lc(b.u - b.nx * wf, b.v - b.ny * wf, 0.04 + AMP * 0.1), Lc(a.u - a.nx * wf, a.v - a.ny * wf, 0.04 + AMP * 0.1)], ac, [0, 1, 0]);
          }
          matFilo = malla.material({ desfase: 2 });
          const mF = new THREE.Mesh(malla.geometria(filo), matFilo); mF.frustumCulled = false; mF.renderOrder = 6; grupo.add(mF);
        }

        // las bolsas sueltas que se mecen y se inflan con el viento (pivote en su base; cada una con su fase)
        const sueltas = [];
        if (P0.sueltas.length) {
          const NS = 4 + Math.floor(hz(0, 91) * 4);
          for (let n = 0; n < NS; n++) {
            const q = muestra(n, 93); if (!q) continue;
            const b = nueva(true), col = P0.sueltas[n % P0.sueltas.length].clone().multiplyScalar(0.95 + 0.15 * hz(n, 94)), s = ko * (1.0 + 0.3 * hz(n, 95));
            gema(b, ico1, [0, 0.3 * s * M, 0], 0.42 * s, 0.3 * s, 0.36 * s, hz(n, 96) * TAU, col, 0.3);
            barra(b, [0, 0.52 * s * M, 0], [0.1 * s * M, 0.78 * s * M, 0.05 * s * M], 0.035 * s, col.clone().multiplyScalar(0.9), 4);
            barra(b, [0, 0.52 * s * M, 0], [-0.1 * s * M, 0.76 * s * M, -0.04 * s * M], 0.035 * s, col.clone().multiplyScalar(0.9), 4);
            const m = new THREE.Mesh(malla.geometria(b), matA); m.frustumCulled = false; m.renderOrder = 5;
            m.position.set(...Lc(q[0], q[1], zT(q[0], q[1]) - 0.03 * ko)); grupo.add(m);
            sueltas.push({ m, f1: 1.4 + 0.9 * hz(n, 97), f2: 0.9 + 0.7 * hz(n, 98), ph: hz(n, 99) * TAU });
          }
        }

        // los destellos: puntos de pocos píxeles sobre las botellas (o el agua), que titilan con su fase (uTiempo = t)
        let matB = null;
        if (brillos.length) {
          const gB = new THREE.BufferGeometry(), pos = [], fa = [];
          for (const [u, v, z, f] of brillos.slice(0, 160)) { pos.push(...Lc(u, v, z)); fa.push(f * 37.0); }
          gB.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
          gB.setAttribute("aFase", new THREE.BufferAttribute(new Float32Array(fa), 1));
          matB = new THREE.ShaderMaterial({
            uniforms: { uTiempo: { value: 0 }, uPx: { value: (noche ? 5.5 : 4.0) * ctx.W / 1080 }, uFuerza: { value: noche ? 1.0 : 0.55 },
              cLuzB: { value: noche ? L("luces").lerp(L("luz"), 0.4) : L("luz") }, uVis: { value: 0 } },
            transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "attribute float aFase; uniform float uTiempo, uPx; varying float vB; void main(){ float w = 0.7 + 0.5 * fract(aFase * 0.137);" +
              " float s = sin(uTiempo * w * 2.4 + aFase); vB = pow(max(0.0, s), 10.0); vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uPx * (0.6 + 0.8 * vB); }",
            fragmentShader: "uniform float uFuerza, uVis; uniform vec3 cLuzB; varying float vB; void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0;" +
              " float a = (1.0 - smoothstep(0.0, 1.0, r)) * vB * uFuerza * uVis; vec3 c = cLuzB; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c * a, a); }" });
          const pB = new THREE.Points(gB, matB); pB.frustumCulled = false; pB.renderOrder = 7; grupo.add(pB);
        }

        // ---- el registro que lee el evento crecer (lo de este cuadro: f; lo fijo: lo demás)
        const NM = 64, MU_ = [];
        for (let n = 0; n < NM; n++) { const q = muestra(n, 111); if (q) MU_.push(q); }
        const forma = (f) => {                                          // la altura (m), el encogido y el aplastado con f
          const hv = f * H, dc = inset(hv) - BUL - J;
          return { hv, su: clamp((Lb - 2 * dc) / Lb, 0.05, 1.5), sv: clamp((Ab - 2 * dc) / Ab, 0.05, 1.5), sy: clamp(hv / (2 * AMPT + 1e-6), 0, 1) };
        };
        const rec = {
          id: p.id, f0: p.inicio, f: p.inicio, alto_m: H, M, ko, muestras: MU_.length, tonos: P0.cosas.map((c) => c[1].clone()),
          fijar(f) { rec.f = clamp(+f || 0, 0, 1); },
          cima(f) { return B + clamp(f, 0, 1) * H * M; },
          punto(i, f) {
            const q = MU_[((i % MU_.length) + MU_.length) % MU_.length] || [uc, vc], F = forma(clamp(f, 0, 1));
            const u = uc + (q[0] - uc) * F.su, v = vc + (q[1] - vc) * F.sv;
            return E(u, v, F.hv + zT(q[0], q[1]) * F.sy);
          },
          dibujar(acc, i, P, k = 1) { const r0 = acc.rot; acc.rot = false; cosa(acc, i, P, ko * k); acc.rot = r0; },
        };
        PILA.pilas[p.id] = rec;

        const mats = [matL, matF, matA].concat(matFilo ? [matFilo] : []);
        const poner = (t, f, brillo) => {
          const F = forma(f), vis = f > 1e-4, k = brillo ? clamp((brillo - 1) / 0.9, 0, 1.2) : 0;
          matL.uniforms.uTope.value = vis ? F.hv : -1e9;
          mLados.visible = vis; grupo.visible = vis; mFalda.visible = f > 0.02 || F.hv > 0.3;
          grupo.position.y = (F.hv - AMPT * (1 - F.sy)) * M; grupo.scale.set(F.su, 1, F.sv);
          matS.uniforms.uK.value = KS * 0.75 * clamp(f * 6, 0, 1);
          for (const m of mats) m.uniforms.uBrillo.value = 1 + 0.35 * k;
          if (matFilo) matFilo.uniforms.uBrillo.value = (noche ? 1.25 : 1.05) + 0.4 * k;
          if (matB) { matB.uniforms.uVis.value = vis ? 1 : 0; matB.uniforms.uTiempo.value = t; }
          for (const s of sueltas) {
            const a = t * s.f1 + s.ph, b = t * s.f2 + 1.3 * s.ph;
            s.m.rotation.set(0.22 * Math.sin(a), 0.15 * Math.sin(0.5 * b), 0.18 * Math.sin(b));
            const inf = 1 + 0.16 * (0.5 + 0.5 * Math.sin(1.7 * a));
            s.m.scale.set(1 / Math.sqrt(inf), inf, 1 / Math.sqrt(inf));
          }
        };
        return { id: p.id, rec, poner };
      });
    },
    inicio(t, lista) { for (const s of lista) s.rec.f = s.rec.f0; },
    en(t, lista, ctx) { for (const s of lista) s.poner(t, s.rec.f, ctx.cuadro.brillo[s.id]); },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
