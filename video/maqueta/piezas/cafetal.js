// Pieza «cafetal» (ficha: cafetal.json; reglas: scripts/maqueta_tipos/cafetal.py): una ladera sembrada de café. El
// polígono sube hacia `rumbo` (0 = este, 90 = norte) hasta `pendiente_m` en un talud suave y continuo: cada una de las
// `hileras` es una franja casi plana donde va la hilera de cafetos y una subida suave hasta la siguiente (sin muros de
// terraza). Las hileras siguen la curva de la ladera (una curva suave a lo ancho, fija por semilla). El suelo es tierra
// con pasto y hojarasca (variación por cara, de los tonos del estilo), con un caminito de tierra entre dos hileras; los
// bordes bajan al suelo del mundo en un terraplén redondeado. Cafetos (arbustos de ~2 m: cuatro copas de hoja verde oscuro
// en cono, con brillo de sol en las caras que miran al sol, distintas por semilla) con racimos de cereza en el borde de
// las ramas: las maduras (`maduras`) en el rojo del estilo (tonos.mal, nunca el acento), las verdes en un verde claro.
// `sombra` > 0 siembra árboles de sombra (troncos delgados de 8–14 m y copas anchas y planas en grumos, que dejan ver los
// cafetos debajo), en las calles entre hileras, en densidad según `sombra` (≈ la parte del suelo que cubren sus copas);
// su sombra cae en el suelo como una mancha suave bajo cada copa (más marcada en el estilo `dia`) y oscurece un poco los
// cafetos que cubre. Todo se arma una vez (mallas con la luz del estilo horneada, como los edificios); cada cuadro solo
// lee ctx.cuadro.brillo[id]: «resaltar» la pieza aviva las cerezas maduras sin cambiarles el color (más brillo y un halo
// rojo que se ve también de lejos). `personas` > 0 deja recolectores del catálogo (objeto cosechador, articulado: cosechan) de pie en las calles
// entre hileras. Seek puro.
(function (MAQ) {
  MAQ.PIEZAS.cafetal = {
    orden: 6,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, CFG, metros, clamp } = ctx;
      const noche = ES.modo === 1, dia = !!ES.dia, enLinea = ES.modo === 2 || ES.modo === 4, TAU = 2 * Math.PI;
      // la luz del estilo (la misma de ctx.sombra): para el brillo de sol en las hojas y hacia dónde cae la sombra de las copas
      const az = ((CFG.luz && CFG.luz.azimut) || 300) * Math.PI / 180, el = ((CFG.luz && CFG.luz.elevacion) || 50) * Math.PI / 180;
      const LX = Math.sin(az) * Math.cos(el), LY = Math.sin(el), LZ = -Math.cos(az) * Math.cos(el);
      const lam = (nx, ny, nz) => Math.max(0, nx * LX + ny * LY + nz * LZ);
      const cLuz = lin(COL.luz);
      const liso = (a, b, x) => { const u = clamp((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u); };
      return piezas.map((p, np) => {
        const pol = []; for (let i = 0; i + 1 < p.poligono.length; i += 2) pol.push([p.poligono[i], p.poligono[i + 1]]);
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r), vx = -uy, vy = ux;     // u: sube · v: a lo ancho
        const S = pol.map((q) => q[0] * ux + q[1] * uy), Wv = pol.map((q) => q[0] * vx + q[1] * vy);
        const s0 = Math.min(...S), s1 = Math.max(...S), L = s1 - s0, N = p.hileras, P = metros(p.pendiente_m), M1 = metros(1);
        const w0 = Math.min(...Wv), w1 = Math.max(...Wv), WS = w1 - w0, RS = L / N;          // RS: de una hilera a la otra
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const xy = (s, w) => [s * ux + w * vx, s * uy + w * vy];
        const sw = (x, y) => [x * ux + y * uy, x * vx + y * vy];
        // el ancho del polígono a la altura s (lo más afuera, si el polígono no es convexo)
        const ancho = (s) => {
          const ss = clamp(s, s0 + 1e-3 * L, s1 - 1e-3 * L); let a = Infinity, b = -Infinity;
          for (let i = 0; i < pol.length; i++) {
            const j = (i + 1) % pol.length, sa = S[i], sb = S[j];
            if ((sa - ss) * (sb - ss) > 0 || sa === sb) continue;
            const w = Wv[i] + (Wv[j] - Wv[i]) * (ss - sa) / (sb - sa); a = Math.min(a, w); b = Math.max(b, w);
          }
          return a <= b ? [a, b] : [0, 0];
        };
        // ---- el perfil de la ladera: talud suave. En cada hilera, g(x) sube de 0 a 1 con la parte más plana donde van los
        // cafetos (x ≈ C0) y la más empinada en la calle de en medio (1.6 × la pendiente media: nunca un muro). Al comienzo
        // de la hilera k la altura es pendiente_m · k / hileras (el contrato de lev_m de un actor de pie ahí).
        const BETA = 0.6, C0 = 0.12, g0 = Math.sin(-TAU * C0), XP = 0.14, XC = 0.62;          // XP: cafetos · XC: la calle
        const g = (x) => x - BETA * (Math.sin(TAU * (x - C0)) - g0) / TAU;
        const prof = (s) => { const u = clamp((s - s0) / L * N, 0, N), k = Math.min(N - 1, Math.floor(u)); return P / N * (k + g(u - k)); };
        const AMP = 0.16 * RS, fase = hz(0, 90) * TAU, lam0 = 1.7 * Math.max(WS, M1);
        const curva = (w) => AMP * Math.sin(TAU * (w - w0) / lam0 + fase);             // las hileras siguen la ladera
        const LEV = metros(0.15), alto = (s, w) => LEV + prof(s - curva(w));
        const base0 = ctx.altura(...xy(s0 + L / 2, (w0 + w1) / 2));
        // ---- ruido de valor fijo (para el suelo): bilineal sobre una cuadrícula de `cel` metros, de 0 a 1
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k);
          const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // ---- colores (todos de ctx.tonos y ctx.COL): tierra, pasto, hojarasca, el caminito; la hoja oscura; las cerezas
        const cPasto = tonos.campo.clone(), cTierra = noche ? tonos.campo2.clone().lerp(tonos.calle, 0.2) : tonos.calle.clone().lerp(tonos.campo2, 0.35).multiplyScalar(0.8);
        const cHojarasca = cTierra.clone().lerp(tonos.techo, 0.3).multiplyScalar(noche ? 0.9 : 0.72);
        const cCamino = noche ? tonos.calle.clone().lerp(cTierra, 0.6) : tonos.calle.clone().multiplyScalar(1.08);
        const cHoja = dia ? tonos.bien.clone().lerp(tonos.campo, 0.45).multiplyScalar(0.5)
          : tonos.bien.clone().lerp(tonos.campo, noche ? 0.66 : 0.55).multiplyScalar(noche ? 0.6 : 0.62);
        const cRoja = tonos.mal.clone().multiplyScalar(noche ? 1.0 : dia ? 1.0 : 0.92);
        const cVerde = tonos.bien.clone().lerp(tonos.medio, dia ? 0.42 : 0.35).multiplyScalar(noche ? 0.62 : dia ? 0.95 : 0.85);
        const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(noche ? 1.7 : dia ? 0.95 : 1);
        const cTronco = noche ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
        const c = new THREE.Color(), c2 = new THREE.Color();

        // ---- los árboles de sombra (si `sombra` > 0): dónde van. Su número: la parte del suelo que cubren sus copas ≈ sombra.
        // Cada uno en la calle entre dos hileras (el tronco nunca dentro de un cafeto), en una cuadrícula con azar fijo.
        let area2 = 0; for (let i = 0; i < pol.length; i++) { const a = pol[i], b = pol[(i + 1) % pol.length]; area2 += a[0] * b[1] - b[0] * a[1]; }
        const area = Math.abs(area2) / 2, ccw = area2 > 0, somb = clamp(p.sombra || 0, 0, 1);
        const arboles = [];
        if (somb > 0) {
          const Rm = metros(4.4), n = Math.min(400, Math.max(1, Math.round(somb * area / (Math.PI * Rm * Rm * 0.9))));
          const cel = Math.sqrt(area / n), ns = Math.max(1, Math.round(L / cel)), nw = Math.max(1, Math.round(WS / cel));
          let q = 0;
          for (let i = 0; i < ns; i++) for (let j = 0; j < nw; j++, q++) {
            const sC = s0 + L * (i + 0.15 + 0.7 * hz(q, 500)) / ns, w = w0 + WS * (j + 0.1 + 0.8 * hz(q, 501)) / nw;
            const k = clamp(Math.round((sC - curva(w) - s0) / RS - XC), 0, N - 1);       // la calle más cercana
            const s = s0 + RS * (k + XC) + curva(w) + (hz(q, 502) - 0.5) * 0.12 * RS, [a, b] = ancho(s);
            if (w < a + metros(1.5) || w > b - metros(1.5) || s > s1 - metros(1)) continue;
            if (arboles.some((t) => Math.hypot(t.s - s, t.w - w) < cel * 0.55)) continue;
            const H = metros(8 + 6 * hz(q, 503)), R = Rm * (0.85 + 0.35 * hz(q, 504));
            const [x, y] = xy(s, w), h = alto(s, w);
            // la mancha: bajo la copa, corrida un poco hacia donde no da el sol (un tercio de lo que caería de verdad)
            const corre = 0.33 * H * Math.cos(el) / Math.max(0.2, Math.sin(el));
            arboles.push({ s, w, x, y, h, H, R, q, sx: x - Math.sin(az) * corre, sy: y - Math.cos(az) * corre });
          }
        }
        // ---- los cafetos: dónde va cada uno (cada hilera sigue su curva; tope ~3000: más espaciados en uno enorme)
        const paso = metros(2.6);
        let total = 0; for (let k = 0; k < N; k++) { const [a, b] = ancho(s0 + RS * (k + XP)); total += Math.max(0, b - a) / paso; }
        const dil = Math.max(1, total / 3000), cafetos = [];
        for (let k = 0, n = 0; k < N; k++) {
          const sk = s0 + RS * (k + XP), [a, b] = ancho(sk), m = Math.floor((b - a - 2 * M1) / (paso * dil));
          for (let j = 0; j <= m; j++, n++) {
            const w = a + M1 + (b - a - 2 * M1) * (m ? j / m : 0.5) + (hz(n, 1) - 0.5) * 0.6 * M1;
            const s = sk + curva(w) + (hz(n, 2) - 0.5) * 0.3 * M1, [aa, bb] = ancho(s);
            if (w < aa + 0.6 * M1 || w > bb - 0.6 * M1 || s > s1 - 0.6 * M1 || s < s0 + 0.4 * M1) continue;
            const [x, y] = xy(s, w); cafetos.push({ n, k, s, w, x, y, h: alto(s, w) });
          }
        }
        // ---- la sombra en el suelo: manchas suaves (cubetas de 8 m para buscar rápido). arbol: la copa, moteada; cafeto:
        // la sombra de contacto bajo cada arbusto
        const FA = dia ? 0.6 : noche ? 0.26 : 0.34, FC = dia ? 0.36 : noche ? 0.18 : 0.22, CB = metros(8);
        const cub = new Map(), meter = (o, rad) => {
          for (let i = Math.floor((o.sx - rad) / CB); i <= Math.floor((o.sx + rad) / CB); i++)
            for (let j = Math.floor((o.sy - rad) / CB); j <= Math.floor((o.sy + rad) / CB); j++) {
              const key = i * 100003 + j; if (!cub.has(key)) cub.set(key, []); cub.get(key).push(o);
            }
        };
        for (const t of arboles) meter({ sx: t.sx, sy: t.sy, rad: t.R * 1.15, ri: t.R * 0.5, f: FA, arb: true }, t.R * 1.15);
        for (const t of cafetos) meter({ sx: t.x, sy: t.y, rad: metros(1.45), ri: metros(0.5), f: FC }, metros(1.45));
        const oscuro = (x, y, solo_arboles) => {               // factor de luz (1 = a pleno sol) en (x, y)
          const lst = cub.get(Math.floor(x / CB) * 100003 + Math.floor(y / CB)); if (!lst) return 1;
          let k = 1;
          for (const o of lst) {
            if (solo_arboles && !o.arb) continue;
            const d = Math.hypot(x - o.sx, y - o.sy); if (d >= o.rad) continue;
            let f = 1 - liso(o.ri, o.rad, d);
            if (o.arb) f *= 0.72 + 0.28 * ruido(x, y, metros(1.6), 77);              // la sombra de una copa es moteada
            k *= 1 - o.f * f;
          }
          return Math.max(0.35, k);
        };

        // ---- el suelo de la ladera: una cuadrícula que sigue el polígono, cada cara con su tono (tierra, pasto, hojarasca,
        // el caminito) y su luz; la sombra se hornea por vértice
        const acc = malla.nueva();
        const cel = Math.max(metros(1), Math.sqrt(area / 9000)), NS = Math.max(4, Math.ceil(L / cel)), NW = Math.max(4, Math.ceil(WS / cel));
        const kc = Math.max(0, Math.min(N - 2, Math.floor(N / 2) - (hz(0, 91) < 0.5 ? 1 : 0)));    // el caminito: tras la hilera kc
        const caminoS = (w) => s0 + RS * (kc + XC) + curva(w) + 0.18 * RS * Math.sin(w / metros(9) + fase);
        const tonoSuelo = (x, y, s, w, i, borde) => {
          const n1 = ruido(x, y, metros(7), 11), n2 = ruido(x, y, metros(2.4), 12), n3 = ruido(x, y, metros(1.1), 13);
          const fr = ((s - curva(w) - s0) / RS) % 1, calle = liso(0.35, 0.55, fr) * (1 - liso(0.85, 1.0, fr));
          // el pasto: más en los bordes y en manchas de la calle; bajo los cafetos, tierra y hojarasca
          const pasto = clamp(0.05 + 0.45 * liso(0.55, 0.85, n1) + 0.2 * calle * n3 + 0.6 * borde, 0, 1);
          c.copy(cTierra).lerp(cPasto, pasto);
          const hoj = liso(0.5, 0.85, n2) * (0.55 + 0.45 * (1 - calle)) * (1 - 0.6 * borde);
          c.lerp(cHojarasca, 0.85 * hoj);
          const dc = Math.abs(s - caminoS(w)), cam = (1 - liso(metros(0.45), metros(0.8), dc)) * (1 - borde);
          c.lerp(cCamino, 0.9 * cam);
          return c.multiplyScalar(0.9 + 0.2 * hz(i, 400) + (n3 - 0.5) * 0.12);
        };
        const pon = (vs, col, nrm) => {                  // una cara de 4 vértices [x, y, h]; la sombra de las copas por vértice
          const lz = sombra(nrm[0], nrm[1], nrm[2]), q = acc.pos.length / 3;
          for (const v of vs) { const o = oscuro(v[0], v[1]) * lz; acc.pos.push(v[0], base0 + v[2], -v[1]); acc.col.push(col.r * o, col.g * o, col.b * o); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        const normal = (A, B, D) => {                     // normal en three (y arriba) de la cara A-B-…-D, hacia arriba
          const e1 = [B[0] - A[0], B[2] - A[2], -(B[1] - A[1])], e2 = [D[0] - A[0], D[2] - A[2], -(D[1] - A[1])];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; } return [nx, ny, nz];
        };
        const vert = (s, t) => { const [a, b] = ancho(s), w = a + (b - a) * t, [x, y] = xy(s, w); return [x, y, alto(s, w), s, w]; };
        for (let i = 0, f = 0; i < NS; i++) {
          const sa = s0 + L * i / NS, sb = s0 + L * (i + 1) / NS;
          for (let j = 0; j < NW; j++, f++) {
            const ta = j / NW, tb = (j + 1) / NW, A = vert(sa, ta), B = vert(sa, tb), C = vert(sb, tb), D = vert(sb, ta);
            if (Math.abs(B[4] - A[4]) + Math.abs(C[4] - D[4]) < 1e-6) continue;             // el polígono se cierra en punta
            const sm = (sa + sb) / 2, wm = (A[4] + B[4] + C[4] + D[4]) / 4, [xm, ym] = xy(sm, wm);
            const borde = Math.max(1 - liso(0, 0.05, Math.min(ta, 1 - tb)), 1 - liso(0, 1.2 * RS, Math.min(sm - s0, s1 - sm))) * 0.6;
            pon([A, B, C, D], tonoSuelo(xm, ym, sm, wm, f, borde).clone(), normal(A, B, D));
          }
        }
        // ---- el terraplén: del borde del polígono baja redondeado al suelo del mundo, hacia afuera (sin muros)
        {
          const per = [], paso_b = Math.max(metros(1.2), cel);
          const nEd = (i) => { const a = pol[i], b = pol[(i + 1) % pol.length], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
            return ccw ? [dy / l, -dx / l] : [-dy / l, dx / l]; };
          for (let i = 0; i < pol.length; i++) {
            const a = pol[i], b = pol[(i + 1) % pol.length], ne = nEd(i), np = nEd((i + pol.length - 1) % pol.length);
            let bx = ne[0] + np[0], by = ne[1] + np[1]; const bl = Math.hypot(bx, by) || 1; bx /= bl; by /= bl;
            const mit = 1 / Math.max(0.5, bx * ne[0] + by * ne[1]);
            const k = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / paso_b));
            for (let j = 0; j < k; j++) {
              const x = a[0] + (b[0] - a[0]) * j / k, y = a[1] + (b[1] - a[1]) * j / k;
              per.push(j ? [x, y, ne[0], ne[1], 1] : [x, y, bx, by, mit]);
            }
          }
          per.push(per[0]);
          const punto = (q) => {                          // arriba (en la ladera), el hombro y el pie en el suelo del mundo
            const [s, w] = sw(q[0], q[1]), h = alto(clamp(s, s0, s1), w), run = (h * 1.35 + metros(0.6)) * q[4];
            const xo = q[0] + q[2] * run, yo = q[1] + q[3] * run, xh = q[0] + q[2] * run * 0.42, yh = q[1] + q[3] * run * 0.42;
            return [[q[0], q[1], h], [xh, yh, h * 0.66], [xo, yo, ctx.altura(xo, yo) - base0 - metros(0.05)]];
          };
          let prev = punto(per[0]);
          for (let i = 1; i < per.length; i++) {
            const cur = punto(per[i]);
            for (let b = 0; b < 2; b++) {
              const A = prev[b], B = cur[b], C = cur[b + 1], D = prev[b + 1];
              if (Math.abs(A[2]) + Math.abs(B[2]) < metros(0.05)) continue;              // el borde bajo, a ras del suelo
              const xm = (A[0] + C[0]) / 2, ym = (A[1] + C[1]) / 2, [sm, wm] = sw(xm, ym);
              pon([A, B, C, D], tonoSuelo(xm, ym, sm, wm, 90000 + i * 2 + b, 0.9 + 0.1 * b).clone(), normal(A, B, D));
            }
            prev = cur;
          }
        }
        const matSuelo = malla.material(); malla.poner(acc, matSuelo, 2);
        // en los estilos de línea (contorno, plano): cada hilera, una línea que sigue su curva
        if (enLinea) {
          const ar = [];
          for (let k = 0; k < N; k++) {
            const sk = s0 + RS * (k + XP), [a, b] = ancho(sk); let pv = null;
            for (let j = 0; j <= 16; j++) {
              const w = a + (b - a) * j / 16, s = sk + curva(w), [x, y] = xy(s, w), pt = [x, base0 + alto(s, w), -y];
              if (pv) ar.push(...pv, ...pt); pv = pt;
            }
          }
          if (ar.length) {
            const gl = new THREE.BufferGeometry(); gl.setAttribute("position", new THREE.BufferAttribute(new Float32Array(ar), 3));
            const l = new THREE.LineSegments(gl, new THREE.LineBasicMaterial({ color: lin(COL.linea), transparent: true, opacity: ES.modo === 4 ? 0.8 : 0.55 }));
            l.frustumCulled = false; l.renderOrder = 3; scene.add(l);
          }
        }

        // ---- sólidos de caras planas: cada triángulo con su luz (normal de cara). op: jit(u) mueve el vértice único u (la
        // copa irregular), ton(k) varía el tono de la cara k, plana > 0 aclara la sombra (la fruta se lee aun en la cara
        // oscura), sol > 0: brillo de sol en las caras que miran al sol (la hoja encerada), luz: factor de sombra encima
        const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
        const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
        const vIco = [], uni = [];                                     // a qué vértice único (12) pertenece cada vértice del icosaedro
        for (let i = 0; i < ico.length; i += 3) {
          let u = uni.findIndex((q) => Math.abs(q[0] - ico[i]) + Math.abs(q[1] - ico[i + 1]) + Math.abs(q[2] - ico[i + 2]) < 1e-4);
          if (u < 0) { u = uni.length; uni.push([ico[i], ico[i + 1], ico[i + 2]]); } vIco.push(u);
        }
        const solido = (dst, tri, cx, cy, cz, sx, sy, sz, rot, col, op = {}) => {
          const cr = Math.cos(rot), sr = Math.sin(rot), v = [];
          for (let i = 0, k = 0; i < tri.length; i += 3, k++) {
            const f = op.jit ? op.jit(vIco[k]) : 1, x = tri[i] * sx * f, y = tri[i + 1] * sy * f, z = tri[i + 2] * sz * f;
            v.push(cx + x * cr - z * sr, cy + y, cz + x * sr + z * cr);
          }
          for (let i = 0, k = 0; i < v.length; i += 9, k++) {
            const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
            const sb = sombra(nx, ny, nz), pl = op.plana || 0;
            c.copy(col).multiplyScalar((pl ? pl + (1 - pl) * sb : sb) * (op.ton ? op.ton(k) : 1) * (op.luz || 1));
            if (op.sol) { const b = liso(0.55, 0.95, lam(nx, ny, nz)) * op.sol * (op.luz || 1); if (b > 0) c.lerp(c2.copy(cLuz).multiplyScalar(0.85), b); }
            const q = dst.pos.length / 3;
            for (let j = 0; j < 9; j += 3) { dst.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); dst.col.push(c.r, c.g, c.b); }
            dst.idx.push(q, q + 1, q + 2);
          }
        };
        const prisma = (dst, A, B, r0, r1, col, lados) => {           // un tronco o una rama: de A a B (three), cónico
          const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = [d[0] / l, d[1] / l, d[2] / l];
          let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
          for (let i = 0; i < lados; i++) {
            const t0 = TAU * i / lados, t1 = TAU * (i + 1) / lados, tm = (t0 + t1) / 2;
            const o = (t, r) => [Math.cos(t) * p1[0] * r + Math.sin(t) * p2[0] * r, Math.cos(t) * p1[1] * r + Math.sin(t) * p2[1] * r, Math.cos(t) * p1[2] * r + Math.sin(t) * p2[2] * r];
            const nm = o(tm, 1), q = dst.pos.length / 3, sb = sombra(nm[0], nm[1], nm[2]);
            c.copy(col).multiplyScalar(sb);
            const va = o(t0, r0), vb = o(t1, r0), vc = o(t1, r1), vd = o(t0, r1);
            for (const [P0, V] of [[A, va], [A, vb], [B, vc], [B, vd]]) { dst.pos.push(P0[0] + V[0], P0[1] + V[1], P0[2] + V[2]); dst.col.push(c.r, c.g, c.b); }
            dst.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
        };

        // ---- los cafetos y sus cerezas. Un cafeto: cuatro copas de hoja apiladas en cono (icosaedros con los vértices
        // movidos por semilla, cada cara con su tono), de la falda ancha a la punta; las cerezas, en racimos de 3–4 pegados
        // por fuera del borde de las copas de abajo (donde están las ramas), para que se lean de 15 a 40 m. Maduras en el
        // rojo del estilo (tonos.mal), verdes en el verde claro; el acento queda fuera de la fruta.
        const hojas = malla.nueva(), rojas = malla.nueva(), verdes = malla.nueva(), halo = [];
        const COPAS = [[0.42, 1.0, 0.42], [0.9, 0.8, 0.38], [1.35, 0.58, 0.33], [1.74, 0.34, 0.26]];
        const rx = metros(0.95), ry = metros(1.0), rc = metros(dia ? 0.13 : 0.12), NR = dia && cafetos.length <= 1500 ? 8 : 6;
        let nr = 0;
        for (const cf of cafetos) {
          const n = cf.n, x = cf.x, y = cf.y, e = 0.82 + 0.36 * hz(n, 3), ew = e * (0.88 + 0.24 * hz(n, 6)), rot = hz(n, 4) * 6.283;
          const y0 = base0 + cf.h, sol = oscuro(x, y, true), tono = cHoja.clone().multiplyScalar(0.86 + 0.28 * hz(n, 5));
          const cop = COPAS.map((C, b) => {                            // cada copa, un poco corrida y girada (el cafeto no es simétrico)
            const ox = (hz(n, 60 + b) - 0.5) * 0.22 * rx * ew, oz = (hz(n, 64 + b) - 0.5) * 0.22 * rx * ew;
            return { cx: x + ox, cy: y0 + C[0] * ry * e, cz: -y + oz, R: C[1] * rx * ew, Ry: C[2] * ry * e, rot: rot + b * 0.9 };
          });
          cop.forEach((q, b) => solido(hojas, ico, q.cx, q.cy, q.cz, q.R, q.Ry, q.R, q.rot, tono, {
            jit: (u) => 0.84 + 0.32 * hz(n * 4 + b, 200 + u), ton: (f) => 0.8 + 0.4 * hz(n * 4 + b, 300 + f),
            sol: dia ? 0.3 + 0.25 * hz(n * 4 + b, 310) : noche ? 0 : 0.12, luz: sol }));
          for (let r = 0; r < NR; r++) {                               // racimos: en el borde de las tres copas de abajo, sobre la rama
            const q = cop[r % 3], azr = rot + r * TAU / NR + hz(n, 10 + r) * 0.6, elr = -0.35 + 0.5 * hz(n, 20 + r);
            const ca = Math.cos(azr), sa = Math.sin(azr), ce = Math.cos(elr), fuera = 1.0;
            const bx = q.cx + ca * ce * q.R * fuera, by = q.cy + Math.sin(elr) * q.Ry * 0.92, bz = q.cz + sa * ce * q.R * fuera;
            const tx = -sa, tz = ca, nC = 3 + (hz(n, 40 + r) < 0.5 ? 1 : 0);   // a lo largo de la rama (tangente)
            let maduro = 0;
            for (let i = 0; i < nC; i++) {
              const d = (i - (nC - 1) / 2) * rc * 1.6, dy = (hz(n, 70 + r * 4 + i) - 0.5) * rc * 1.2;
              const px = bx + tx * d + ca * rc * 0.9, py = by + dy, pz = bz + tz * d + sa * rc * 0.9;
              const madura = hz(n, 30 + r * 4 + i) < p.maduras; if (madura) maduro++;
              solido(madura ? rojas : verdes, oct, px, py, pz, rc, rc * 1.15, rc, azr + i, madura ? cRoja : cVerde,
                { plana: dia ? 0.6 : 0.45, luz: 0.5 + 0.5 * sol, sol: dia ? 0.25 : 0 });
            }
            if (maduro) { halo.push(bx + ca * rc * 2, by, bz + sa * rc * 2); nr++; }
          }
        }
        // ---- los árboles de sombra: tronco delgado y alto (un poco ladeado, con dos o tres ramas que se abren) y la copa
        // ancha y plana en grumos, con huecos que dejan ver los cafetos de abajo
        const arb = malla.nueva(), copas = malla.nueva();
        for (const t of arboles) {
          const q = t.q, gx = t.x, gz = -t.y, y0 = base0 + t.h, H = t.H, lx = (hz(q, 510) - 0.5) * 0.08 * H, lz = (hz(q, 511) - 0.5) * 0.08 * H;
          const tope = [gx + lx, y0 + H * 0.86, gz + lz], rt = metros(0.13 + 0.07 * hz(q, 512));
          prisma(arb, [gx, y0 - metros(0.2), gz], tope, rt, rt * 0.55, cTronco, 6);
          const nRam = 2 + (hz(q, 513) < 0.5 ? 1 : 0), cielo = y0 + H, gr = [];
          for (let b = 0; b < nRam; b++) {                             // las ramas: de 2/3 del tronco hacia afuera y arriba
            const a = hz(q, 520 + b) * 0.8 + b * TAU / nRam, rr = t.R * (0.45 + 0.2 * hz(q, 524 + b));
            const B0 = [gx + lx * 0.7, y0 + H * 0.68, gz + lz * 0.7], B1 = [gx + lx + Math.cos(a) * rr, cielo - metros(0.6), gz + lz + Math.sin(a) * rr];
            prisma(arb, B0, B1, rt * 0.55, rt * 0.3, cTronco, 5); gr.push(B1);
          }
          gr.push([gx + lx, cielo, gz + lz]);
          const tono = cCopa.clone().multiplyScalar(0.88 + 0.24 * hz(q, 530));
          // la copa: un grumo plano sobre cada rama y uno al centro, y dos sueltos en el borde (copa ancha, ~2 R de lado)
          for (let b = 0; b < gr.length + 2; b++) {
            const G = b < gr.length ? gr[b] : (() => { const a = hz(q, 540 + b) * TAU, rr = t.R * 0.62; return [gx + lx + Math.cos(a) * rr, cielo - metros(0.3), gz + lz + Math.sin(a) * rr]; })();
            const R = t.R * (b === gr.length - 1 ? 0.62 : 0.5) * (0.85 + 0.3 * hz(q, 550 + b)), Ry = metros(1.0 + 0.6 * hz(q, 560 + b));
            solido(copas, ico, G[0], G[1] + Ry * 0.3, G[2], R, Ry, R * (0.85 + 0.3 * hz(q, 570 + b)), hz(q, 580 + b) * TAU, tono, {
              jit: (u) => 0.8 + 0.4 * hz(q * 8 + b, 600 + u), ton: (f) => 0.84 + 0.32 * hz(q * 8 + b, 700 + f), sol: dia ? 0.22 : 0 });
          }
        }
        const sinTraslado = (accm, mat, orden) => {                    // las mallas ya vienen en coordenadas de escena
          const m = new THREE.Mesh(malla.geometria(accm), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m;
        };
        const matHoja = malla.material(), matRoja = malla.material(), matVerde = malla.material();
        sinTraslado(hojas, matHoja, 3); sinTraslado(verdes, matVerde, 3); sinTraslado(rojas, matRoja, 4);
        if (arboles.length) { sinTraslado(arb, malla.material(), 3); sinTraslado(copas, malla.material(), 3); }
        // el halo de las maduras: un punto por racimo, en su mismo rojo (de lejos la cereza es más chica que un píxel); se
        // enciende al resaltar: aviva la fruta sin cambiarle el color
        const gh = new THREE.BufferGeometry(); gh.setAttribute("position", new THREE.BufferAttribute(new Float32Array(halo.length ? halo : [0, 0, 0]), 3));
        const mh = new THREE.ShaderMaterial({ uniforms: { cA: { value: cRoja.clone() }, uK: { value: 0 }, uTam: { value: ctx.H * 0.5 * metros(0.9) } },
          transparent: true, depthWrite: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
          vertexShader: "uniform float uTam, uK; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uK > 0.0 ? clamp(uTam * projectionMatrix[1][1] / max(-mv.z, 0.001), 2.5, 22.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA; uniform float uK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = (exp(-r * r * 5.0) * 0.5 + exp(-r * r * 40.0) * 0.5) * uK; if (a < 0.003) discard; vec3 c = cA; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }" });
        const ph = new THREE.Points(gh, mh); ph.frustumCulled = false; ph.renderOrder = 8; ph.visible = nr > 0; scene.add(ph);
        // ---- recolectores: de pie en la calle entre su hilera y la siguiente, mirando a lo largo de la hilera
        const gente = [];
        for (let i = 0; i < p.personas; i++) {
          const k = Math.min(N - 1, Math.floor((i + 0.5) * N / p.personas)), sk = s0 + RS * (k + 0.5), [a, b] = ancho(sk);
          const w = a + (b - a) * (0.2 + 0.6 * hz(i, 50)), s = Math.min(s1 - M1, sk + curva(w)), [x, y] = xy(s, w), sg = hz(i, 51) < 0.5 ? 1 : -1;
          const fl = ctx.flota("cosechador", 1, { lev: (base0 + alto(s, w) - ctx.altura(x, y)) / M1, orden: 4, semilla: 101 * i + 13,
            color: (_, vs) => vs[Math.floor(hz(i, 52) * vs.length) % vs.length] });
          gente.push({ fl, x, y, dx: vx * sg, dy: vy * sg });
        }
        return { id: p.id, matRoja, mh, gente };
      });
    },
    en(t, lista, ctx) {
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? ctx.clamp((b - 1) / 0.9, 0, 1.2) : 0;
        s.matRoja.uniforms.uBrillo.value = 1 + 0.7 * k;
        s.mh.uniforms.uK.value = k;
        for (const g of s.gente) { g.fl.poner(0, g.x, g.y, g.dx, g.dy, 1, 0); g.fl.listo(); }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
