// Pieza «lagocorte» (ficha: lagocorte.json; reglas: scripts/maqueta_tipos/lagocorte.py): un lago en corte como
// bloque-diagrama (esquema, no a escala), sin lugar real. Centrado en `lugar` y orientado por `rumbo` (u: de la orilla con
// la desembocadura hacia el lago abierto; v: a su izquierda). Todo en METROS de maqueta × `tamano`; z = altura sobre el
// espejo del agua (negativa hacia abajo). El bloque se apoya en el suelo del mundo.
// - LA TAPA: la orilla de tierra con pasto, árboles y carrizo; un RÍO que entra por la tierra y desemboca en el lago; la
//   BARDA (`barda`): una hilera doble de envases plásticos atados con lazo que cruza la desembocadura, con sus estacas en
//   cada orilla; la BASURA mezclada (bolsas, botellas, latas, duroport, cartón, ramas y hojas: `basura`) atrapada contra
//   la barda, del lado del río, sin llegar al espejo del lago; el espejo del agua, translúcido, con su oleaje.
// - LA CARA DEL CORTE (v = −WV): la tierra en capas, el talud y el fondo con su sedimento; el agua, translúcida, con rayos
//   de luz. Pegados a ella nadan `peces` peces genéricos en un CARDUMEN SUELTO, sin filas, lejos de la barda y de la
//   basura (se cuentan: nadie se toca); cada uno lleva una ventana de corte en el vientre con su tracto digestivo, gris, y
//   en `marcados` de ellos unas fibras de microplástico DENTRO del tracto (no en la carne).
// - CON VIDA (seek puro, todo de t): el cardumen se mece junto y cada pez baten la cola y cabecea; la barda y la basura
//   suben y bajan con el oleaje; el carrizo, las plantas del fondo y las copas se mecen; partículas que flotan en el agua.
// - «resaltar» la pieza: las fibras se encienden en el acento una tras otra (de izquierda a derecha) en lo que dura el
//   resalte y se quedan encendidas; antes no se ven (un pez marcado es igual a uno limpio) y los limpios siguen grises.
// Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin); sin texto ni números.
(function (MAQ) {
  const UL = 26, UR = 30, WV = 11, DB = 30, DW = 24, HT = 1.6, UO = -9, VC = 2, WC = 4.5, DC = 2.2, SUB = 0.2;
  const FU0 = 1.5, FU1 = 28.5, FZ0 = -21.5, FZ1 = -2.5, UCEN = (UR - UL) / 2, TAU = 2 * Math.PI;
  const liso = (a, b, x) => { const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const fase = (s) => ((s * 0.6180339887) % 1) * TAU;
  const h0 = (u, v, ph) => HT - (HT + 0.6) * liso(UO - 2.5, UO, u) - (DW - 0.6) * liso(UO, UO + 12, u)
    + 0.15 * Math.sin(u / 2.3 + ph) * Math.sin(v / 3.1 + ph) * (1 - liso(UO - 3, UO - 1, u))
    + 0.5 * Math.sin(u / 3.1 + ph) * Math.sin(v / 2.7 + 0.7 * ph) * liso(UO + 2, UO + 8, u);
  const canal = (v) => { const d = Math.abs(v - VC); return d < WC ? -DC * (1 - (d / WC) * (d / WC)) : HT * liso(WC, WC + 1.4, d); };
  const alto = (u, v, ph) => Math.min(h0(u, v, ph), canal(v));
  // la barda: de estaca a estaca por la desembocadura, combada hacia el lago (s 0–1 → [u, v])
  const BV = WC + 0.9, barda = (s) => [UO - 3.2 + 4.6 * Math.sin(Math.PI * s), VC - BV + 2 * BV * s];
  const bardaU = (v) => { const s = Math.min(1, Math.max(0, (v - VC + BV) / (2 * BV))); return barda(s)[0]; };
  const sRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

  MAQ.PIEZAS.lagocorte = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp, GLSL_COMUN, uComun } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1;
      const C = (a, b) => lin(COL[a] || COL[b] || COL.secundario);
      const sube = (c, k) => (oscuro ? c.clone().lerp(tonos.muro, 0.2).multiplyScalar(k) : c.clone());
      const ico1 = new THREE.IcosahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
      const ico0 = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const eventos = (ctx.M && ctx.M.eventos) || [];

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K, ph = fase(p.semilla);
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r), cr = Math.cos(r), sr = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const y0 = ctx.suelo(p.x, p.y) - SUB * M;
        const W2 = (u, v) => [p.x + ((u - UCEN) * ux - v * uy) * M, p.y + ((u - UCEN) * uy + v * ux) * M];
        const E = (u, v, z) => { const [x, y] = W2(u, v); return [x, y0 + (DB + z) * M, -y]; };
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz(((a & 4095) * 4099 + (b & 4095)) % 1000003, k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const A = (u, v) => alto(u, v, ph);

        // ---- los tonos (todos del estilo)
        const cAgua = tonos.agua.clone(), cAguaH = C("mar_hondo", "mar").lerp(tonos.agua, 0.35).multiplyScalar(oscuro ? 0.55 : 0.5);
        const cPasto = tonos.campo.clone().lerp(tonos.verde, 0.35), cPasto2 = tonos.campo2.clone().lerp(tonos.verde, 0.2);
        const cTierra = sube(C("tierra_media", "secundario").lerp(tonos.techo, 0.25).multiplyScalar(0.85), 1.25);
        const cArcilla = sube(tonos.techo.clone().lerp(C("tierra_alta", "secundario"), 0.4).multiplyScalar(0.85), 1.25);
        const cArena = sube(tonos.arena.clone().multiplyScalar(0.92), 1.1);
        const cLodo = sube(C("tierra_baja", "secundario").lerp(tonos.asfalto, 0.45).lerp(tonos.verde, 0.12).multiplyScalar(0.8), 1.4);
        const cLimo = sube(C("tierra_baja", "secundario").lerp(tonos.agua, 0.25).multiplyScalar(0.85), 1.3);
        const cRoca = sube(tonos.muro.clone().lerp(tonos.asfalto, 0.45), 1.2);
        const cMadera = sube(tonos.techo.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.8), 1.3);
        const cHoja = tonos.verde.clone().lerp(tonos.campo2, 0.3).multiplyScalar(0.85), cCarrizo = tonos.campo.clone().lerp(tonos.arena, 0.3);
        const cPlanta = tonos.verde.clone().lerp(tonos.agua, 0.3).multiplyScalar(0.7);
        const L = (n) => lin(COL[n] || COL.secundario);
        const cBotella = tonos.agua.clone().lerp(L("luz"), 0.55), cBotellaV = tonos.verde.clone().lerp(L("luz"), 0.45), cBlanco = tonos.arena.clone().lerp(L("luz"), 0.6);
        const cTapa = [tonos.secundario.clone(), tonos.medio.clone(), tonos.bien.clone().multiplyScalar(0.85), L("mar").lerp(tonos.linea, 0.2)];
        const cLazo = sube(tonos.arena.clone().lerp(tonos.techo, 0.5), 1.1);
        const cBolsaN = sube(tonos.asfalto.clone().lerp(tonos.linea, 0.2).multiplyScalar(0.85), 1.7), cBolsaG = sube(tonos.pavimento.clone().lerp(tonos.asfalto, 0.3), 1.4);
        const cBolsaC = sube(tonos.secundario.clone().lerp(tonos.medio, 0.3).multiplyScalar(0.85), 1.1), cBolsaA = sube(L("mar").lerp(tonos.linea, 0.25), 1.2);
        const cLata = tonos.muro.clone().lerp(L("luz"), 0.3), cCarton = sube(tonos.arena.clone().lerp(tonos.techo, 0.45), 1.15);
        const cOrg = sube(tonos.techo.clone().lerp(tonos.campo2, 0.5).multiplyScalar(0.72), 1.5), cMancha = sube(tonos.calle.clone().lerp(tonos.techo, 0.4).multiplyScalar(0.6), 1.5);
        // los peces (genéricos: lomo oscuro, flanco plateado, vientre claro; ningún rasgo de especie)
        const cDorso = sube(tonos.agua.clone().lerp(tonos.asfalto, 0.55).lerp(tonos.verde, 0.12), 1.5);
        const cFlanco = tonos.muro.clone().lerp(L("luz"), 0.4).multiplyScalar(oscuro ? 1.0 : 0.95), cVientre = tonos.arena.clone().lerp(L("luz"), 0.55);
        const cAleta = cDorso.clone().lerp(cFlanco, 0.35), cOjo = tonos.asfalto.clone().multiplyScalar(0.5);
        // la ventana de corte, clara y neutra; el tracto, gris (así quedan los peces limpios: gris, sin acento)
        const cVentana = cVientre.clone().lerp(tonos.muro, 0.22), cTracto = sube(tonos.muro.clone().lerp(tonos.asfalto, 0.55).multiplyScalar(0.8), 1.3);
        const cFibra = tonos.acento.clone();

        // ---- los acumuladores: fijo (malla.material), vivo (se mece con el oleaje o el viento: aF fase, aA amplitudes)
        const nuevaV = () => ({ pos: [], col: [], idx: [], f: [], a: [] });
        const fijo = nuevaV(), vivo = nuevaV(), panel = { pos: [], col: [], idx: [], q: [] }, fondoA = nuevaV();
        const push = (acc, P, c, l, f = 0, ax = 0, ay = 0) => { acc.pos.push(P[0], P[1], P[2]); acc.col.push(c.r * l, c.g * l, c.b * l); if (acc.f) { acc.f.push(f); acc.a.push(ax, ay); } return acc.pos.length / 3 - 1; };
        const normal = (P) => {
          const a = P[0], b = P[1], c = P[2], e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
          const nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0], n = Math.hypot(nx, ny, nz) || 1;
          return [nx / n, ny / n, nz / n];
        };
        // un polígono convexo ya en la escena (abanico), con su luz; `ref` (punto de la escena) = de dónde se aleja la normal
        const poly = (acc, P, col, ref, f = 0, ax = 0, ays = 0) => {
          let n = normal(P);
          if (ref) { let cx = 0, cy = 0, cz = 0; for (const q of P) { cx += q[0]; cy += q[1]; cz += q[2]; }
            const k = P.length; if (n[0] * (cx / k - ref[0]) + n[1] * (cy / k - ref[1]) + n[2] * (cz / k - ref[2]) < 0) n = n.map((x) => -x); }
          else if (n[1] < 0) n = n.map((x) => -x);
          const l = sombra(n[0], n[1], n[2]), q0 = acc.pos.length / 3;
          P.forEach((q, j) => push(acc, q, col, l, f, ax, Array.isArray(ays) ? ays[j] : ays));
          for (let j = 1; j + 1 < P.length; j++) acc.idx.push(q0, q0 + j, q0 + j + 1);
        };
        // de local (u, v, z en metros de maqueta) a la escena
        const El = (q) => E(q[0], q[1], q[2]);
        // un tubo de A a B (local), radios r0 → r1, n lados; tapas opcionales
        const tubo = (acc, Al, Bl, r0, r1, n, col, f = 0, ax = 0, ay0 = 0, ay1 = 0, tapas = false) => {
          const d = [Bl[0] - Al[0], Bl[1] - Al[1], Bl[2] - Al[2]], ln = Math.hypot(...d) || 1, a = d.map((x) => x / ln);
          let p1 = Math.abs(a[2]) < 0.9 ? [-a[1], a[0], 0] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
          const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
          const anillo = (C0, rr) => { const o = []; for (let i = 0; i < n; i++) { const t = TAU * i / n; o.push(El([0, 1, 2].map((j) => C0[j] + (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * rr))); } return o; };
          const RA = anillo(Al, r0), RB = anillo(Bl, r1);
          for (let i = 0; i < n; i++) { const j = (i + 1) % n, eje = El([0, 1, 2].map((k) => (Al[k] + Bl[k]) / 2));
            poly(acc, [RA[i], RA[j], RB[j], RB[i]], col.clone().multiplyScalar(0.94 + 0.08 * ((i * 7) % 3) / 2), eje, f, ax, [ay0, ay0, ay1, ay1]); }
          if (tapas) { poly(acc, RA.slice().reverse(), col, El(Bl), f, ax, ay0); poly(acc, RB, col, El(Al), f, ax, ay1); }
        };
        // un icosaedro aplastado (bolsa, piedra, copa, hoja): centro local, radios (u, v, z), giro en el plano
        const gema = (acc, Cl, ru, rv, rz, giro, col, f = 0, ax = 0, ay = 0, tri = ico1, plana = 0.25) => {
          const c1 = Math.cos(giro), s1 = Math.sin(giro), ref = El(Cl), c = new THREE.Color();
          for (let i = 0; i < tri.length; i += 9) {
            const P = [];
            for (let j = 0; j < 9; j += 3) { const x = tri[i + j] * ru, y = tri[i + j + 1] * rv, z = tri[i + j + 2] * rz;
              P.push(El([Cl[0] + x * c1 - y * s1, Cl[1] + x * s1 + y * c1, Cl[2] + z])); }
            let n = normal(P); const m = [(P[0][0] + P[1][0] + P[2][0]) / 3 - ref[0], (P[0][1] + P[1][1] + P[2][1]) / 3 - ref[1], (P[0][2] + P[1][2] + P[2][2]) / 3 - ref[2]];
            if (n[0] * m[0] + n[1] * m[1] + n[2] * m[2] < 0) n = n.map((x) => -x);
            c.copy(col).multiplyScalar(plana + (1 - plana) * sombra(n[0], n[1], n[2]));
            const q0 = acc.pos.length / 3; for (const q of P) push(acc, q, c, 1, f, ax, ay); acc.idx.push(q0, q0 + 1, q0 + 2);
          }
        };
        // una caja girada (medios lados a, b, c en metros) centrada en Cl local
        const caja = (acc, Cl, a, b, c3, giro, col, f = 0, ax = 0) => {
          const c1 = Math.cos(giro), s1 = Math.sin(giro), V = (x, y, z) => El([Cl[0] + (x * a) * c1 - (y * b) * s1, Cl[1] + (x * a) * s1 + (y * b) * c1, Cl[2] + z * c3]);
          const F = [[[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1]], [[-1, 1, -1], [1, 1, -1], [1, 1, 1], [-1, 1, 1]],
            [[-1, -1, -1], [-1, 1, -1], [-1, 1, 1], [-1, -1, 1]], [[1, -1, -1], [1, 1, -1], [1, 1, 1], [1, -1, 1]]];
          for (const q of F) poly(acc, q.map((e) => V(...e)), col, El(Cl), f, ax, 0);
        };

        // ================= la tapa sólida: tierra con pasto, el talud, el cauce del río y el fondo del lago
        { const du = 0.5, nu = Math.round((UL + UR) / du), nv = Math.round(2 * WV / du), Z = [];
          for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) Z.push(A(-UL + du * i, -WV + du * j));
          const z = (i, j) => Z[i * (nv + 1) + j];
          const colT = (u, v, h) => {
            const n1 = ruido(u, v, 4, 11), n2 = ruido(u, v, 1.3, 12);
            let c;
            if (h > 0.35) c = cPasto.clone().lerp(cPasto2, 0.7 * n1).lerp(cTierra, 0.25 * liso(0.7, 0.95, n2));
            else if (h > -0.4) c = cArena.clone().lerp(cTierra, 0.45).lerp(cLodo, 0.3 * n1);
            else if (h > -3.5) c = cLimo.clone().lerp(cArena, 0.25 * n2);
            else c = cLodo.clone().lerp(cLimo, 0.35 * n1).lerp(cPlanta, 0.15 * liso(0.6, 0.9, n2));
            return c.multiplyScalar(0.9 + 0.14 * n2);
          };
          for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
            const ua = -UL + du * i, va = -WV + du * j, P = [E(ua, va, z(i, j)), E(ua + du, va, z(i + 1, j)), E(ua + du, va + du, z(i + 1, j + 1)), E(ua, va + du, z(i, j + 1))];
            const hm = (z(i, j) + z(i + 1, j) + z(i + 1, j + 1) + z(i, j + 1)) / 4;
            poly(fijo, P, colT(ua + du / 2, va + du / 2, hm), null);
          }
        }
        // ================= las caras del corte: la tierra y el sedimento en capas; el agua (adelante translúcida, atrás de fondo)
        const FR = [0, 0.015, 0.04, 0.08, 0.14, 0.24, 0.38, 0.55, 0.75, 1];
        const capa = (u, v, z, top) => {
          const d = top - z, n = ruido(u * 1.7, z * 1.7, 2.2, 20);
          let c;
          if (top > 0.2 && d < 0.35) c = cPasto2.clone().lerp(cTierra, 0.5);
          else if (top > 0.2 && d < 1.4) c = cTierra.clone();
          else if (top <= 0.2 && d < 0.8) c = cLodo.clone();
          else if (top <= 0.2 && d < 2.2) c = cLimo.clone().lerp(cLodo, 0.3);
          else if (z > -18) c = cArcilla.clone().lerp(cArena, 0.5 + 0.5 * Math.sin(z / 1.6 + 2.2 * n));
          else c = cRoca.clone().lerp(cArcilla, 0.4 * n);
          return c.multiplyScalar(0.88 + 0.16 * ruido(u, z, 0.9, 21));
        };
        const seccion = (muestras, nrm, atras) => {
          const l = sombra(...nrm), cols = muestras.map(([u, v]) => A(u, v));
          for (let i = 0; i + 1 < muestras.length; i++) {
            const [ua, va, sa] = muestras[i], [ub, vb, sb] = muestras[i + 1], ta = cols[i], tb = cols[i + 1];
            for (let k = 0; k + 1 < FR.length; k++) {
              const za0 = ta + (-DB - ta) * FR[k], za1 = ta + (-DB - ta) * FR[k + 1], zb0 = tb + (-DB - tb) * FR[k], zb1 = tb + (-DB - tb) * FR[k + 1];
              const q0 = fijo.pos.length / 3;
              push(fijo, E(ua, va, za0), capa(ua, va, za0, ta), l); push(fijo, E(ub, vb, zb0), capa(ub, vb, zb0, tb), l);
              push(fijo, E(ub, vb, zb1), capa(ub, vb, zb1, tb), l); push(fijo, E(ua, va, za1), capa(ua, va, za1, ta), l);
              fijo.idx.push(q0, q0 + 1, q0 + 2, q0, q0 + 2, q0 + 3);
            }
            // el agua entre el fondo y el espejo
            const wa = Math.min(0, ta), wb = Math.min(0, tb);
            if (wa >= 0 && wb >= 0) continue;
            if (atras) {
              const q0 = fondoA.pos.length / 3, c = (z) => cAguaH.clone().lerp(cAgua, 0.45 * (1 + z / DW) * (1 + z / DW));
              push(fondoA, E(ua, va, 0), c(0), 1); push(fondoA, E(ub, vb, 0), c(0), 1); push(fondoA, E(ub, vb, wb), c(wb), 1); push(fondoA, E(ua, va, wa), c(wa), 1);
              fondoA.idx.push(q0, q0 + 1, q0 + 2, q0, q0 + 2, q0 + 3);
            } else {
              const q0 = panel.pos.length / 3;
              for (const [P, s, z] of [[E(ua, va, 0), sa, 0], [E(ub, vb, 0), sb, 0], [E(ub, vb, wb), sb, wb], [E(ua, va, wa), sa, wa]]) {
                panel.pos.push(...P); panel.col.push(cAgua.r, cAgua.g, cAgua.b); panel.q.push(s, z); }
              panel.idx.push(q0, q0 + 1, q0 + 2, q0, q0 + 2, q0 + 3);
            }
          }
        };
        const muestrasU = (v) => { const o = []; for (let u = -UL; u <= UR + 1e-6; u += 0.4) o.push([u, v, u]); return o; };
        const muestrasV = (u) => { const o = []; for (let v = -WV; v <= WV + 1e-6; v += 0.4) o.push([u, v, v + 40]); return o; };
        const nF = [uy, 0, ux], nB = [-uy, 0, -ux], nI = [-ux, 0, uy], nD = [ux, 0, -uy];
        seccion(muestrasU(-WV), nF, false); seccion(muestrasU(WV), nB, true);
        seccion(muestrasV(-UL), nI, false); seccion(muestrasV(UR), nD, false);

        // ================= el agua: el espejo (translúcido, con oleaje) sobre el lago y el río
        const tapaAgua = { pos: [], col: [], idx: [], q: [] };
        { const du = 1, nu = UL + UR, nv = 2 * WV;
          for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) { const u = -UL + i * du, v = -WV + j * du; tapaAgua.pos.push(...E(u, v, 0)); tapaAgua.col.push(cAgua.r, cAgua.g, cAgua.b); tapaAgua.q.push(u, v); }
          for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
            const u = -UL + i + 0.5, v = -WV + j + 0.5;
            if (Math.min(A(u - 0.5, v - 0.5), A(u + 0.5, v - 0.5), A(u + 0.5, v + 0.5), A(u - 0.5, v + 0.5)) > 0.05) continue;
            const a = i * (nv + 1) + j; tapaAgua.idx.push(a, a + nv + 1, a + 1, a + 1, a + nv + 1, a + nv + 2);
          }
        }

        // ================= la orilla: árboles, piedras, carrizo; el fondo: plantas y piedras
        for (let i = 0, k = 0; i < 40 && k < 6; i++) {
          const u = -UL + 1.8 + 12 * hz(i, 30), v = -WV + 1.5 + (2 * WV - 3) * hz(i, 31);
          if (Math.abs(v - VC) < WC + 2.6 || (u > UO - 9 && Math.abs(v - VC) < WC + 5.5) || A(u, v) < 1.2) continue;
          const h = 3.2 + 1.6 * hz(i, 32), z0 = A(u, v), g = 0.5 + 0.5 * hz(i, 33);
          tubo(fijo, [u, v, z0 - 0.2], [u, v, z0 + h * 0.62], 0.2, 0.13, 8, cMadera);
          const cc = cHoja.clone().lerp(cPasto2, 0.4 * g);
          gema(vivo, [u, v, z0 + h * 0.72], 1.5 + 0.5 * g, 1.4 + 0.4 * g, 1.1, hz(i, 34) * TAU, cc, i * 1.7, 0, 0.06);
          gema(vivo, [u + 0.7, v - 0.4, z0 + h * 0.9], 1.0, 1.0, 0.85, hz(i, 35) * TAU, cc.clone().multiplyScalar(1.08), i * 1.7 + 0.4, 0, 0.08);
          k++;
        }
        for (let i = 0; i < 14; i++) {
          const u = -UL + 1 + (UL + UO - 2) * hz(i, 40), v = -WV + 0.8 + (2 * WV - 1.6) * hz(i, 41), z0 = A(u, v);
          if (z0 < 0.5) continue;
          gema(fijo, [u, v, z0 + 0.1], 0.35 + 0.3 * hz(i, 42), 0.3 + 0.2 * hz(i, 43), 0.22, hz(i, 44) * TAU, cRoca.clone().multiplyScalar(0.9 + 0.2 * hz(i, 45)), 0, 0, 0, ico0);
        }
        // carrizo genérico donde la orilla toca el agua (no en la boca del río: ahí está la barda)
        const carrizo = (u, v, n, s) => {
          const z0 = A(u, v);
          for (let b = 0; b < n; b++) {
            const a = hz(s * 31 + b, 50) * TAU, h = (1.3 + 1.1 * hz(s * 31 + b, 51)), du = 0.35 * Math.cos(a), dv = 0.35 * Math.sin(a), ie = 0.18 * hz(s + b, 52);
            const w = 0.05, B0 = [u + du * 0.3, v + dv * 0.3, z0 - 0.1], T = [u + du + ie, v + dv, z0 + h];
            const P = [El([B0[0] - w * Math.sin(a), B0[1] + w * Math.cos(a), B0[2]]), El([B0[0] + w * Math.sin(a), B0[1] - w * Math.cos(a), B0[2]]), El(T)];
            poly(vivo, P, cCarrizo.clone().multiplyScalar(0.85 + 0.25 * hz(s + b, 53)), null, s * 0.9 + b * 0.3, 0, [0, 0, 0.22]);
          }
        };
        for (let i = 0; i < 26; i++) {
          const v = -WV + 0.6 + (2 * WV - 1.2) * hz(i, 55);
          if (Math.abs(v - VC) < WC + 1.6) continue;
          carrizo(UO - 1.2 - 1.6 * hz(i, 56), v, 5 + Math.floor(4 * hz(i, 57)), i);
        }
        for (let i = 0; i < 16; i++) {
          const lado = i % 2 ? 1 : -1, u = -UL + 1.2 + (UL + UO - 6) * hz(i, 58);
          carrizo(u, VC + lado * (WC + 0.7 + 0.5 * hz(i, 59)), 4 + Math.floor(3 * hz(i, 60)), 40 + i);
        }
        // plantas del fondo (en la mitad de atrás: no tapan a los peces) y piedras
        for (let i = 0; i < 46; i++) {
          const u = UO + 3 + (UR - UO - 4) * hz(i, 62), v = -1.5 + (WV - 0.6 + 1.5) * hz(i, 63), z0 = A(u, v);
          if (z0 > -2) continue;
          const nb = 3 + Math.floor(3 * hz(i, 64));
          for (let b = 0; b < nb; b++) {
            const a = hz(i * 7 + b, 65) * TAU, h = 1.6 + 2.6 * hz(i * 7 + b, 66), w = 0.14, P = [];
            const B0 = [u, v, z0 - 0.05], d = [Math.cos(a) * 0.5, Math.sin(a) * 0.5];
            P.push(El([B0[0] - w * Math.sin(a), B0[1] + w * Math.cos(a), B0[2]]), El([B0[0] + w * Math.sin(a), B0[1] - w * Math.cos(a), B0[2]]),
              El([u + d[0] + 0.06, v + d[1], z0 + h * 0.6]), El([u + d[0] * 1.2, v + d[1] * 1.2, z0 + h]));
            poly(vivo, [P[0], P[1], P[2]], cPlanta.clone().multiplyScalar(0.85 + 0.3 * hz(i + b, 67)), null, i * 1.3 + b, 0, [0, 0, 0.3]);
            poly(vivo, [P[0], P[2], P[3]], cPlanta.clone().multiplyScalar(0.8 + 0.3 * hz(i + b, 68)), null, i * 1.3 + b, 0, [0, 0.3, 0.55]);
          }
        }
        for (let i = 0; i < 40; i++) {
          const u = UO + 1 + (UR - UO - 1.5) * hz(i, 70), v = -WV + 0.6 + (2 * WV - 1.2) * hz(i, 71), z0 = A(u, v);
          if (z0 > -0.5) continue;
          gema(fijo, [u, v, z0], 0.25 + 0.45 * hz(i, 72), 0.22 + 0.3 * hz(i, 73), 0.2, hz(i, 74) * TAU, cRoca.clone().lerp(cLodo, 0.4).multiplyScalar(0.85 + 0.25 * hz(i, 75)), 0, 0, 0, ico0);
        }

        // ================= la barda: dos hileras de envases plásticos tendidos, atados con lazo, de estaca a estaca
        const OLA = 0.07;
        const botella = (acc, Cl, eje, largo, rr, col, tapa, f) => {
          const a = [Math.cos(eje), Math.sin(eje)], P = (s) => [Cl[0] + a[0] * s, Cl[1] + a[1] * s, Cl[2]];
          tubo(acc, P(-largo / 2), P(largo * 0.22), rr, rr, 12, col, f, OLA, 0, 0, false);
          tubo(acc, P(largo * 0.22), P(largo * 0.36), rr, rr * 0.38, 12, col.clone().multiplyScalar(0.95), f, OLA);
          tubo(acc, P(largo * 0.36), P(largo * 0.5), rr * 0.3, rr * 0.3, 8, tapa, f, OLA, 0, 0, true);
          poly(acc, Array.from({ length: 12 }, (_, i) => { const t = TAU * i / 12; return El([P(-largo / 2)[0] - a[1] * rr * Math.cos(t), P(-largo / 2)[1] + a[0] * rr * Math.cos(t), Cl[2] + rr * Math.sin(t)]); }), col, El(Cl), f, OLA);
        };
        if (p.barda) {
          const pasos = 80, lin2 = []; for (let i = 0; i <= pasos; i++) lin2.push(barda(i / pasos));
          let acum = [0]; for (let i = 1; i <= pasos; i++) acum.push(acum[i - 1] + Math.hypot(lin2[i][0] - lin2[i - 1][0], lin2[i][1] - lin2[i - 1][1]));
          const LB = acum[pasos], en = (s) => { let i = 1; while (i < pasos && acum[i] < s) i++; const f = (s - acum[i - 1]) / ((acum[i] - acum[i - 1]) || 1); const a = lin2[i - 1], b = lin2[i];
            return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, Math.atan2(b[1] - a[1], b[0] - a[0])]; };
          const largo = 0.78, rr = 0.15, paso = 0.62, puntos = [];
          for (let s = 0.3, i = 0; s < LB - 0.3; s += paso, i++) {
            const [u, v, eje] = en(s);
            if (A(u, v) > -0.15) continue;
            puntos.push([u, v, s]);
            for (const lado of [-1, 1]) {
              const o = lado * 0.17, uu = u - Math.sin(eje) * o, vv = v + Math.cos(eje) * o, hh = hz(i * 2 + (lado > 0), 80);
              const col = (hh < 0.55 ? cBotella : hh < 0.8 ? cBlanco : cBotellaV).clone().multiplyScalar(0.92 + 0.14 * hz(i, 81));
              botella(vivo, [uu, vv, 0.04 + 0.03 * hz(i, 82)], eje + (hz(i * 2 + lado, 83) - 0.5) * 0.25, largo * (0.9 + 0.2 * hz(i, 84)), rr, col, cTapa[(i + (lado > 0 ? 1 : 0)) % cTapa.length], s * 0.9);
            }
            // amarre de través cada dos
            if (i % 2 === 0) tubo(vivo, [u - Math.sin(eje) * 0.36, v + Math.cos(eje) * 0.36, 0.19], [u + Math.sin(eje) * 0.36, v - Math.cos(eje) * 0.36, 0.19], 0.028, 0.028, 5, cLazo, s * 0.9, OLA);
          }
          // el lazo a lo largo (encima) y hasta las estacas de cada orilla
          for (let j = 0; j + 1 < puntos.length; j++) { const a = puntos[j], b = puntos[j + 1];
            tubo(vivo, [a[0], a[1], 0.2], [b[0], b[1], 0.2], 0.035, 0.035, 5, cLazo, a[2] * 0.9, OLA); }
          for (const [s, q] of [[0, puntos[0]], [1, puntos[puntos.length - 1]]]) {
            if (!q) continue;
            const [ue, ve] = barda(s), ze = A(ue, ve);
            tubo(fijo, [ue, ve, ze - 0.4], [ue, ve, ze + 1.1], 0.09, 0.08, 7, cMadera, 0, 0, 0, 0, true);
            const m = 6; for (let j = 0; j < m; j++) { const f0 = j / m, f1 = (j + 1) / m, za = ze + 0.9 + (0.2 - ze - 0.9) * f0, zb = ze + 0.9 + (0.2 - ze - 0.9) * f1;
              tubo(vivo, [ue + (q[0] - ue) * f0, ve + (q[1] - ve) * f0, za - 0.12 * Math.sin(Math.PI * f0)], [ue + (q[0] - ue) * f1, ve + (q[1] - ve) * f1, zb - 0.12 * Math.sin(Math.PI * f1)], 0.03, 0.03, 5, cLazo, q[2] * 0.9, OLA * f1); }
          }
        }

        // ================= la basura atrapada contra la barda, del lado del río (mezclada: no solo plástico)
        { const NB = Math.round(clamp(p.basura, 0, 1) * 300);
          // la mancha de fondo: una nata oscura e irregular bajo las cosas
          if (NB > 0) {
            const fondoU = 4 + 9 * clamp(p.basura, 0, 1);
            for (let j = 0; j < 20; j++) {
              const va = VC - WC + 0.5 + (2 * WC - 1) * j / 20, vb = VC - WC + 0.5 + (2 * WC - 1) * (j + 1) / 20;
              const ua1 = bardaU(va) - 0.25, ub1 = bardaU(vb) - 0.25, la = fondoU * (0.55 + 0.45 * ruido(va, 0, 2, 90)), lb = fondoU * (0.55 + 0.45 * ruido(vb, 0, 2, 90));
              poly(vivo, [E(ua1 - la, va, 0.03), E(ub1 - lb, vb, 0.03), E(ub1, vb, 0.03), E(ua1, va, 0.03)], cMancha.clone().multiplyScalar(0.9 + 0.2 * ruido(va, 3, 1.5, 91)), null, va * 0.9, OLA * 0.6);
            }
          }
          const TIPOS = [["bolsa", 0.3], ["botella", 0.24], ["lata", 0.07], ["duroport", 0.09], ["carton", 0.07], ["rama", 0.08], ["hojas", 0.15]];
          for (let i = 0; i < NB; i++) {
            const v = VC - WC + 0.7 + (2 * WC - 1.4) * hz(i, 100), lejos = 0.2 + (3 + 10 * clamp(p.basura, 0, 1)) * Math.pow(hz(i, 101), 1.8);
            const u = bardaU(v) - 0.35 - lejos;
            if (A(u, v) > -0.2) continue;
            let x = hz(i, 102), tipo = TIPOS[0][0]; for (const [t, w] of TIPOS) { x -= w; if (x <= 0) { tipo = t; break; } }
            const g = hz(i, 103) * TAU, f = v * 0.9 + 0.3 * hz(i, 104), z = 0.06 + 0.08 * hz(i, 105);
            if (tipo === "bolsa") { const cc = [cBolsaN, cBolsaN, cBolsaG, cBlanco, cBolsaC, cBolsaA][Math.floor(hz(i, 106) * 6)];
              gema(vivo, [u, v, z + 0.1], 0.42 + 0.2 * hz(i, 107), 0.32 + 0.15 * hz(i, 108), 0.24, g, cc.clone().multiplyScalar(0.9 + 0.2 * hz(i, 109)), f, OLA, 0, ico1, 0.3); }
            else if (tipo === "botella") botella(vivo, [u, v, z], g, 0.72 * (0.85 + 0.3 * hz(i, 110)), 0.14, (hz(i, 111) < 0.6 ? cBotella : hz(i, 111) < 0.85 ? cBlanco : cBotellaV).clone(), cTapa[i % cTapa.length], f);
            else if (tipo === "lata") tubo(vivo, [u - 0.18 * Math.cos(g), v - 0.18 * Math.sin(g), z + 0.05], [u + 0.18 * Math.cos(g), v + 0.18 * Math.sin(g), z + 0.05], 0.1, 0.1, 10, cLata.clone().multiplyScalar(0.9 + 0.2 * hz(i, 112)), f, OLA, 0, 0, true);
            else if (tipo === "duroport") caja(vivo, [u, v, z + 0.04], 0.3 + 0.2 * hz(i, 113), 0.22 + 0.12 * hz(i, 114), 0.09, g, cBlanco.clone().multiplyScalar(1.02), f, OLA);
            else if (tipo === "carton") caja(vivo, [u, v, z], 0.4 + 0.2 * hz(i, 115), 0.3 + 0.15 * hz(i, 116), 0.035, g, cCarton.clone().multiplyScalar(0.9 + 0.2 * hz(i, 117)), f, OLA);
            else if (tipo === "rama") { const l = 1.2 + 1.4 * hz(i, 118);
              tubo(vivo, [u - l / 2 * Math.cos(g), v - l / 2 * Math.sin(g), z], [u + l / 2 * Math.cos(g), v + l / 2 * Math.sin(g), z + 0.05], 0.07, 0.04, 6, cMadera, f, OLA);
              tubo(vivo, [u, v, z + 0.02], [u + 0.6 * Math.cos(g + 0.6), v + 0.6 * Math.sin(g + 0.6), z + 0.08], 0.035, 0.02, 5, cMadera, f, OLA); }
            else { const cc = hz(i, 119) < 0.6 ? cOrg : cHoja.clone().lerp(cOrg, 0.4);
              gema(vivo, [u, v, z], 0.36 + 0.2 * hz(i, 120), 0.28 + 0.12 * hz(i, 121), 0.08, g, cc.clone().multiplyScalar(0.9 + 0.2 * hz(i, 122)), f, OLA, 0, ico0, 0.35); }
          }
        }

        // ================= las mallas fijas, vivas, el agua y su fondo
        const uTi = { value: 0 }, mats = [];
        const matFijo = malla.material({}); mats.push(matFijo);
        const mFijo = new THREE.Mesh(malla.geometria(fijo), matFijo); mFijo.frustumCulled = false; mFijo.renderOrder = 3; scene.add(mFijo);
        const mFondoA = new THREE.Mesh(malla.geometria(fondoA), matFijo); mFondoA.frustumCulled = false; mFondoA.renderOrder = 3; scene.add(mFondoA);
        const matVivo = new THREE.ShaderMaterial({ uniforms: { ...uComun(), uBrillo: { value: 1 }, uTi, uM: { value: M } }, side: THREE.DoubleSide,
          vertexShader: "attribute vec3 color; attribute float aF; attribute vec2 aA; uniform float uTi, uM; varying vec3 vCol, vPos;" +
            "void main(){ vCol = color; vec3 p = position; p.y += aA.x * uM * (sin(uTi * 1.45 + aF) * 0.8 + 0.2 * sin(uTi * 2.3 + aF * 1.7));" +
            " p.x += aA.y * uM * sin(uTi * 0.9 + aF); p.z += aA.y * uM * 0.6 * cos(uTi * 0.73 + aF * 1.3);" +
            " vPos = (modelMatrix * vec4(p, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0); }",
          fragmentShader: GLSL_COMUN + "uniform float uBrillo; varying vec3 vCol, vPos; void main(){ gl_FragColor = vec4(salida(niebla(vCol * uBrillo, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
        mats.push(matVivo);
        { const g = malla.geometria(vivo); g.setAttribute("aF", new THREE.BufferAttribute(new Float32Array(vivo.f), 1)); g.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(vivo.a), 2));
          const m = new THREE.Mesh(g, matVivo); m.frustumCulled = false; m.renderOrder = 4; scene.add(m); }
        // el agua: modo 0 = el panel del corte (rayos de luz, más espesa abajo), 1 = el espejo (oleaje y destellos)
        const matAgua = (modo, alfa) => {
          const m = new THREE.ShaderMaterial({ uniforms: { ...uComun(), uBrillo: { value: 1 }, uTi, uModo: { value: modo }, uAlfa: { value: alfa }, uNoche: { value: noche ? 1 : 0 },
            cHondo: { value: cAguaH.clone() }, cClaro: { value: cAgua.clone().lerp(L("luz"), 0.35) }, uDW: { value: DW } },
            transparent: true, depthWrite: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2,
            vertexShader: "attribute vec3 color; attribute vec2 aQ; varying vec3 vCol, vPos; varying vec2 vQ; void main(){ vCol = color; vQ = aQ; vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: GLSL_COMUN + `uniform float uBrillo, uTi, uModo, uAlfa, uNoche, uDW; uniform vec3 cHondo, cClaro; varying vec3 vCol, vPos; varying vec2 vQ;
              void main(){
                vec3 c; float a;
                if (uModo < 0.5) {
                  float d = clamp(-vQ.y / uDW, 0.0, 1.0);
                  c = mix(vCol, cHondo, 0.25 + 0.55 * d);
                  float rayo = pow(max(0.0, sin(vQ.x * 0.42 + vQ.y * 0.16 + uTi * 0.22 + sin(vQ.x * 0.11 + uTi * 0.13) * 2.0)), 8.0) * (1.0 - d) * 0.5;
                  c = mix(c, cClaro, rayo * (0.6 - 0.3 * uNoche));
                  float borde = smoothstep(-0.25, 0.0, vQ.y);
                  c = mix(c, cClaro, borde * 0.6);
                  a = uAlfa * (0.55 + 0.6 * d) + borde * 0.25;
                } else {
                  float o = sin(vQ.x * 1.7 + uTi * 1.1) * sin(vQ.y * 1.3 - uTi * 0.8) + 0.5 * sin((vQ.x + vQ.y) * 3.1 + uTi * 1.9);
                  c = vCol * (0.92 + 0.07 * o);
                  float brillo = pow(max(0.0, o - 0.85), 2.0) * (0.9 - 0.4 * uNoche);
                  c = mix(c, cClaro, clamp(brillo, 0.0, 0.6));
                  a = uAlfa;
                }
                gl_FragColor = vec4(salida(niebla(c * uBrillo, vPos, gl_FragCoord.xy), gl_FragCoord.xy), a); }` });
          mats.push(m); return m;
        };
        const ponerQ = (acc, mat, orden) => { const g = malla.geometria(acc); g.setAttribute("aQ", new THREE.BufferAttribute(new Float32Array(acc.q), 2));
          const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        ponerQ(panel, matAgua(0, oscuro ? 0.3 : 0.26), 9);
        ponerQ(tapaAgua, matAgua(1, oscuro ? 0.62 : 0.55), 10);

        // ================= las partículas que flotan en el agua (puro de t)
        { const NP = 320, pos = [], fa = [];
          for (let i = 0, k = 0; i < 900 && k < NP; i++) {
            const u = UO + 1 + (UR - UO - 1.5) * hz(i, 130), v = -WV + 0.4 + (2 * WV - 0.8) * hz(i, 131), zb = A(u, v), z = zb + (0 - zb) * (0.05 + 0.9 * hz(i, 132));
            if (zb > -1) continue;
            pos.push(...E(u, v, z)); fa.push(hz(i, 133) * TAU, 0.6 + 0.8 * hz(i, 134)); k++;
          }
          const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3)); g.setAttribute("aF", new THREE.BufferAttribute(new Float32Array(fa), 2));
          const mat = new THREE.ShaderMaterial({ uniforms: { uTi, uM: { value: M }, cA: { value: L("luz").lerp(cAgua, 0.3) }, uK: { value: noche ? 0.4 : 0.3 }, uPx: { value: (1.6 + (noche ? 0.4 : 0)) * ctx.W / 1080 } },
            transparent: true, depthWrite: false,
            vertexShader: "attribute vec2 aF; uniform float uTi, uM, uPx; varying float vA; void main(){ vec3 p = position + uM * vec3(0.35 * sin(uTi * 0.21 + aF.x), 0.3 * sin(uTi * 0.17 * aF.y + aF.x * 2.0), 0.3 * cos(uTi * 0.19 + aF.x * 1.3)); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uPx * aF.y * 1.6; vA = 0.6 + 0.4 * sin(uTi * 0.7 + aF.x * 3.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * (1.0 - smoothstep(0.3, 1.0, r)); gl_FragColor = vec4(srgb(cA), a); }" });
          const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
        }

        // ================= los peces (genéricos, agrandados para contarse): una malla de cuerpo y una de cola compartidas
        const luzL = (nx, ny, nz) => { const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n; return sombra(nx * cr + nz * sr, ny, -nx * sr + nz * cr); };
        const hH = (q) => 0.035 * q + 0.004 * (1 - q) + 0.18 * Math.pow(Math.max(0, Math.sin(Math.PI * Math.pow(q, 0.85))), 0.8) * (1 - 0.12 * q);
        const hW = (q) => hH(q) * (0.4 + 0.12 * (1 - q)), yc = (q) => -0.02 * Math.sin(Math.PI * q) + 0.01 * q, xq = (q) => 0.5 - 0.86 * q;
        const qDe = (x) => clamp((0.5 - x) / 0.86, 0, 1);
        const zSup = (x, y) => { const q = qDe(x), h = hH(q), d = (y - yc(q)) / h; return hW(q) * Math.sqrt(Math.max(0, 1 - d * d)); };
        const cuerpo = malla.nueva(), cola = malla.nueva(), SV = 1.15;   // SV: la ventana y el tracto, algo más grandes (se leen a 40 m)
        const pv = (acc, P, c, l) => { acc.pos.push(P[0], P[1], P[2]); acc.col.push(c.r * l, c.g * l, c.b * l); return acc.pos.length / 3 - 1; };
        const triL = (acc, P, c, nz) => { const l = luzL(0, 0.25, nz), q0 = acc.pos.length / 3; for (const q of P) pv(acc, q, c, l); for (let j = 1; j + 1 < P.length; j++) acc.idx.push(q0, q0 + j, q0 + j + 1); };
        { const NQ = 18, NA = 18, qs = []; for (let i = 0; i <= NQ; i++) qs.push(Math.pow(i / NQ, 1.15));
          qs.forEach((q, i) => {
            const x = xq(q), h = hH(q), w = hW(q), dh = (hH(Math.min(1, q + 0.02)) - hH(Math.max(0, q - 0.02))) / 0.04 / 0.86;
            for (let j = 0; j <= NA; j++) {
              const a = -Math.PI / 2 + TAU * j / NA, s = Math.sin(a), y = yc(q) + h * s, z = w * Math.cos(a);
              let c = cFlanco.clone().lerp(cDorso, liso(0.05, 0.7, s)).lerp(cVientre, liso(-0.25, -0.8, s));
              if (q > 0.16 && q < 0.2) c.multiplyScalar(0.82);                                          // el opérculo
              const ny0 = s * w, nz0 = Math.cos(a) * h, nn = Math.hypot(ny0, nz0) || 1;
              pv(cuerpo, [x, y, z], c, luzL(0.6 * dh, ny0 / nn, nz0 / nn));
            }
            if (i) for (let j = 0; j < NA; j++) { const a = (i - 1) * (NA + 1) + j, b = a + NA + 1; cuerpo.idx.push(a, b, a + 1, a + 1, b, b + 1); }
          });
          // las aletas: dorsal con sus espinas, anal, pectorales y pélvicas (de los dos lados)
          const tira = (q0, q1, n, alto, abajo, col) => {
            for (let i = 0; i < n; i++) {
              const qa = q0 + (q1 - q0) * i / n, qb = q0 + (q1 - q0) * (i + 1) / n, ha = alto * Math.pow(Math.sin(Math.PI * (i / n) * 0.92 + 0.08), 0.6) * (i % 2 ? 0.85 : 1), hb = alto * Math.pow(Math.sin(Math.PI * ((i + 1) / n) * 0.92 + 0.08), 0.6) * ((i + 1) % 2 ? 0.85 : 1);
              const ya = yc(qa) + (abajo ? -hH(qa) : hH(qa)) * 0.96, yb = yc(qb) + (abajo ? -hH(qb) : hH(qb)) * 0.96, sg = abajo ? -1 : 1;
              triL(cuerpo, [[xq(qa), ya, 0], [xq(qb), yb, 0], [xq(qb) + 0.01, yb + sg * hb, 0], [xq(qa) + 0.01, ya + sg * ha, 0]], col.clone().multiplyScalar(i % 2 ? 0.9 : 1), 1);
            }
          };
          tira(0.27, 0.8, 12, 0.1, false, cAleta); tira(0.6, 0.84, 6, 0.07, true, cAleta);
          for (const sd of [1, -1]) {
            const q = 0.24, x = xq(q), y = yc(q) - 0.045, z = sd * (zSup(x, y) + 0.004);
            triL(cuerpo, [[x, y, z], [x - 0.13, y - 0.045, z + sd * 0.04], [x - 0.11, y + 0.015, z + sd * 0.05]], cAleta.clone().lerp(cFlanco, 0.3), sd);
            const qp = 0.34, xp = xq(qp), ypp = yc(qp) - hH(qp) * 0.9;
            triL(cuerpo, [[xp, ypp, sd * 0.01], [xp - 0.09, ypp - 0.05, sd * 0.03], [xp - 0.06, ypp - 0.005, sd * 0.02]], cAleta, sd);
            // el ojo (anillo claro y pupila) y la ventana de corte con el tracto digestivo
            const xo = xq(0.1), yo = yc(0.1) + 0.035, zo = (r, dz) => sd * (zSup(xo, yo) + dz);
            const disco = (r, dz, col) => { const P = []; for (let k = 0; k < 12; k++) { const t = TAU * k / 12; P.push([xo + r * Math.cos(t), yo + r * Math.sin(t), zo(r, dz)]); } triL(cuerpo, P, col, sd); };
            disco(0.034, 0.004, cVientre); disco(0.021, 0.007, cOjo);
            const X0 = 0.035, Y0 = yc(0.52) - 0.025, RX = 0.17 * SV, RY = 0.072 * SV, ven = [];
            for (let k = 0; k < 24; k++) { const t = TAU * k / 24, x = X0 + RX * Math.cos(t), y = Y0 + RY * Math.sin(t); ven.push([x, y, sd * (zSup(x, y) + 0.005)]); }
            triL(cuerpo, ven, cVentana, sd);
            for (let k = 0; k < 24; k++) { const a = ven[k], b = ven[(k + 1) % 24], f = 1.1;
              const a2 = [X0 + (a[0] - X0) * f, Y0 + (a[1] - Y0) * f], b2 = [X0 + (b[0] - X0) * f, Y0 + (b[1] - Y0) * f];
              triL(cuerpo, [a, b, [b2[0], b2[1], sd * (zSup(b2[0], b2[1]) + 0.005)], [a2[0], a2[1], sd * (zSup(a2[0], a2[1]) + 0.005)]], cTracto.clone().multiplyScalar(0.8), sd); }
          }
        }
        // el tracto (una banda en S dentro de la ventana) — el mismo camino lo siguen las fibras
        const TR = (() => { let P = [[0.12, 0.012], [0.05, 0.035], [-0.04, 0.022], [-0.085, -0.01], [-0.01, -0.03], [-0.07, -0.048], [-0.125, -0.03]].map(([x, y]) => [0.035 + SV * x, yc(0.52) - 0.025 + SV * y]);
          for (let it = 0; it < 2; it++) { const Q = [P[0]]; for (let i = 0; i + 1 < P.length; i++) { const a = P[i], b = P[i + 1]; Q.push([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]], [0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]]); } Q.push(P[P.length - 1]); P = Q; }
          const ac = [0]; for (let i = 1; i < P.length; i++) ac.push(ac[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
          return { P, ac, L: ac[ac.length - 1], en(s) { s = clamp(s, 0, 1) * this.L; let i = 1; while (i < P.length - 1 && ac[i] < s) i++; const f = (s - ac[i - 1]) / ((ac[i] - ac[i - 1]) || 1), a = P[i - 1], b = P[i];
            const dx = b[0] - a[0], dy = b[1] - a[1], n = Math.hypot(dx, dy) || 1; return [a[0] + dx * f, a[1] + dy * f, -dy / n, dx / n]; } }; })();
        const banda = (acc, s0, s1, ancho, dz, sd, col, ondas = 0, amp = 0, fz = 0) => {
          const n = 22, q0 = acc.pos.length / 3;
          for (let i = 0; i <= n; i++) { const s = s0 + (s1 - s0) * i / n, [x, y, nx, ny] = TR.en(s), o = amp * Math.sin(ondas * TAU * i / n + fz);
            for (const k of [-1, 1]) { const xx = x + nx * (o + k * ancho / 2), yy = y + ny * (o + k * ancho / 2); acc.pos.push(xx, yy, sd * (zSup(xx, yy) + dz)); if (col) { const l = luzL(0, 0.25, sd); acc.col.push(col.r * l, col.g * l, col.b * l); } }
            if (i) { const a = q0 + 2 * (i - 1); acc.idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } }
        };
        for (const sd of [1, -1]) banda(cuerpo, 0, 1, 0.034 * SV, 0.008, sd, cTracto);
        { const P = [[0, 0.035], [-0.24, 0.18], [-0.29, 0.17], [-0.19, 0.0], [-0.29, -0.17], [-0.24, -0.18], [0, -0.035]].map((q) => new THREE.Vector2(q[0], q[1]));
          const l = luzL(0, 0.2, 1), q0 = cola.pos.length / 3;
          P.forEach((v, i) => pv(cola, [v.x, v.y, 0], cAleta.clone().multiplyScalar(i === 0 || i === 6 ? 0.9 : 1.05), l));
          for (const t of THREE.ShapeUtils.triangulateShape(P, [])) cola.idx.push(q0 + t[0], q0 + t[1], q0 + t[2]);
          for (let k = 0; k < 5; k++) { const yy = -0.14 + 0.07 * k; triL(cola, [[-0.01, yy * 0.22, 0.002], [-0.2, yy, 0.002], [-0.2, yy + 0.006, 0.002]], cAleta.clone().multiplyScalar(0.75), 1); }
        }
        const gCuerpo = malla.geometria(cuerpo), gCola = malla.geometria(cola);
        const matPez = malla.material({});   // fuera de `mats`: el resalte no aclara los peces (los limpios se quedan como están)
        // fibras: no se ven hasta que el resalte las enciende, una tras otra (aR = su turno): antes, un pez marcado es igual a uno limpio
        const uN = { value: 0 }, uBF = { value: 1 }, uPx = { value: 1 };
        const matFibra = new THREE.ShaderMaterial({ uniforms: { ...uComun(), uN, uBF, uNoche: { value: noche ? 1 : 0 }, cOn: { value: cFibra.clone() }, cOff: { value: cTracto.clone() } },
          side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4,
          vertexShader: "attribute float aR; uniform float uN; varying float vK; varying vec3 vPos; void main(){ vK = clamp(uN - aR, 0.0, 1.0); vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: GLSL_COMUN + "uniform vec3 cOn, cOff; uniform float uBF, uNoche; varying float vK; varying vec3 vPos; void main(){ if (vK <= 0.002) discard; vec3 c = mix(cOff, cOn * (1.35 + 0.6 * uNoche) * uBF, vK); gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
        const matHalo = new THREE.ShaderMaterial({ uniforms: { uN, uBF, uPx, uTi, cA: { value: cFibra.clone() }, uK: { value: noche ? 0.85 : 0.7 } },
          transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "attribute float aR, aS; uniform float uN, uPx; varying float vK, vR; void main(){ vK = clamp(uN - aR, 0.0, 1.0); vR = aR; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = vK > 0.0 ? clamp(aS * uPx / max(1e-3, -mv.z), 4.0, 90.0) : 0.0; }",
          fragmentShader: sRGB + "uniform vec3 cA; uniform float uK, uTi, uBF; varying float vK, vR; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vK * uK * uBF * (exp(-r * r * 4.0) * 0.8 + exp(-r * r * 30.0) * 0.5) * (0.85 + 0.15 * sin(uTi * 2.2 + vR * 1.7)); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA) * a, a); }" });

        // el cardumen suelto (sin filas): puntos azul-ruido dentro de una mancha ovalada de la zona de los peces, separados
        // con una métrica alargada (un pez es ≈ 2 veces más largo que alto) y relajados unas vueltas; todo en armar, fijo por
        // semilla. Ningún pez cerca de la barda ni de la basura (la zona empieza lejos de la desembocadura).
        const N = clamp(p.peces | 0, 1, 100), NM = clamp(p.marcados | 0, 0, N);
        const uc = (FU0 + FU1) / 2, zc = (FZ0 + FZ1) / 2, SA = (FU1 - FU0) / 2 - 0.6, SB = (FZ1 - FZ0) / 2 - 0.5, EXP = 2.6;
        const dentro = (u, z) => Math.pow(Math.abs(u - uc) / SA, EXP) + Math.pow(Math.abs(z - zc) / SB, EXP);
        const tam = Array.from({ length: N }, (_, i) => 0.84 + 0.32 * hz(i, 153));        // 15.6–24 cm: ≈ 1.5 veces
        const MU = 1.2, MZ = 0.6;                                                            // la caja de un pez (× su largo)
        const met = (i, j, U, Z) => Math.hypot((U[i] - U[j]) / MU, (Z[i] - Z[j]) / MZ) / ((tam[i] + tam[j]) / 2);
        const U = [], Z = [];
        for (let i = 0; i < N; i++) {
          let mejor = null, dm = -1;
          for (let c = 0, ok = 0; c < 240 && ok < 14; c++) {
            const cu = FU0 + (FU1 - FU0) * hz(i * 241 + c, 170), cz = FZ0 + (FZ1 - FZ0) * hz(i * 241 + c, 171);
            if (dentro(cu, cz) > 1) continue; ok++;
            let d = 1e9; U.push(cu); Z.push(cz);
            for (let j = 0; j < i; j++) d = Math.min(d, met(i, j, U, Z));
            U.pop(); Z.pop();
            if (d > dm) { dm = d; mejor = [cu, cz]; }
          }
          if (!mejor) mejor = [uc, zc];
          U.push(mejor[0]); Z.push(mejor[1]);
        }
        const area = 4 * SA * SB * 0.86, Lobj = Math.min(2.2, Math.sqrt(area * 0.52 / (MU * MZ * N)));
        for (let it = 0; it < 48; it++) {                                                   // se separan hasta su caja
          const T = Lobj * 1.14;
          for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
            const d = met(i, j, U, Z); if (d >= T) continue;
            const s = (tam[i] + tam[j]) / 2, du = (U[i] - U[j]) / MU, dz = (Z[i] - Z[j]) / MZ, n = Math.hypot(du, dz) || 1e-3;
            const k = 0.5 * (T - d) * s / n;
            U[i] += du * k * MU * 0.5; U[j] -= du * k * MU * 0.5; Z[i] += dz * k * MZ * 0.5; Z[j] -= dz * k * MZ * 0.5;
          }
          for (let i = 0; i < N; i++) { const e = dentro(U[i], Z[i]); if (e > 1) { const f = Math.pow(1 / e, 1 / EXP); U[i] = uc + (U[i] - uc) * f; Z[i] = zc + (Z[i] - zc) * f; } }
        }
        let dmin = 1e9; for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) dmin = Math.min(dmin, met(i, j, U, Z));
        const Lb = Math.min(Lobj, N > 1 ? dmin / 1.14 : 2.2, 2.2);                           // con margen para el vaivén: nadie se toca
        // el cardumen nada hacia un lado (casi todos), y se encienden de izquierda a derecha (mirando la cara del corte)
        const rumboC = (p.semilla % 2) ? 1 : -1;
        const orden = Array.from({ length: N }, (_, i) => i).sort((a, b) => hz(a, 150) - hz(b, 150));
        const marcados = orden.slice(0, NM).sort((a, b) => (U[a] - 0.25 * Z[a]) - (U[b] - 0.25 * Z[b]));
        const marca = new Array(N).fill(-1); marcados.forEach((i, k) => { marca[i] = k; });
        const peces = [];
        for (let i = 0; i < N; i++) {
          const u = U[i], z = Z[i], Lp = Lb * tam[i], dir = hz(i, 154) < 0.9 ? rumboC : -rumboC;
          const v = -WV + 1.2 + 1.1 * hz(i, 155);
          const g = new THREE.Group(); scene.add(g);
          const mc = new THREE.Mesh(gCuerpo, matPez); mc.frustumCulled = false; mc.renderOrder = 5; g.add(mc);
          const mk = new THREE.Mesh(gCola, matPez); mk.frustumCulled = false; mk.renderOrder = 5; mk.position.set(xq(1) + 0.01, yc(1), 0); g.add(mk);
          if (marca[i] >= 0) {
            const fb = { pos: [], col: [], idx: [] }, nf = 2 + Math.floor(2 * hz(i, 156));
            for (let k = 0; k < nf; k++) { const s0 = 0.04 + 0.5 * hz(i * 5 + k, 157), s1 = Math.min(0.98, s0 + 0.28 + 0.2 * hz(i * 5 + k, 158));
              for (const sd of [1, -1]) banda(fb, s0, s1, 0.03, 0.012, sd, null, 2 + k, 0.012, k * 1.7); }
            const gF = new THREE.BufferGeometry(); gF.setAttribute("position", new THREE.BufferAttribute(new Float32Array(fb.pos), 3));
            gF.setAttribute("aR", new THREE.BufferAttribute(new Float32Array(fb.pos.length / 3).fill(marca[i]), 1)); gF.setIndex(fb.idx);
            const mf = new THREE.Mesh(gF, matFibra); mf.frustumCulled = false; mf.renderOrder = 6; g.add(mf);
            const gH = new THREE.BufferGeometry(); gH.setAttribute("position", new THREE.BufferAttribute(new Float32Array([0.03, yc(0.52) - 0.025, 0.12]), 3));
            gH.setAttribute("aR", new THREE.BufferAttribute(new Float32Array([marca[i]]), 1)); gH.setAttribute("aS", new THREE.BufferAttribute(new Float32Array([0.55 * Lp * M]), 1));
            const mh = new THREE.Points(gH, matHalo); mh.frustumCulled = false; mh.renderOrder = 11; g.add(mh);
          }
          peces.push({ g, cola: mk, u, v, z, Lp, dir, w: 0.3 + 0.25 * hz(i, 160), fc: 1.3 + 1.0 * hz(i, 161), a: hz(i, 162) * TAU, b: hz(i, 163) * TAU, cw: Lb, rh: Lb * 0.5 });
        }
        // los resaltes de esta pieza (las fibras se encienden durante cada uno y se quedan)
        const resaltes = eventos.filter((e) => e && e.tipo === "resaltar" && e.pieza === p.id && e.indice === undefined && e.elemento === undefined);

        // ================= la gente en la orilla, junto a la barda (opcional; de pie, mirando el río)
        const NPe = clamp(p.personas | 0, 0, 4), gente = [];
        const SITIOS = [[UO - 4.4, VC - WC - 2.3, 1], [UO - 6.6, VC - WC - 2.9, 1], [UO - 4.2, VC + WC + 2.3, -1], [UO - 7.2, VC + WC + 3.0, -1]];
        for (let i = 0; i < NPe; i++) { const [u, v, lado] = SITIOS[i]; const [x, y] = W2(u, v), d = [-uy * lado, ux * lado]; gente.push([x, y, d[0], d[1]]); }
        const camisas = [tonos.mal.clone(), tonos.medio.clone(), tonos.bien.clone(), tonos.muro.clone().multiplyScalar(0.9)];
        const flP = NPe ? ctx.flota("persona", NPe, { tamano: K, lev: 0, orden: 6, semilla: p.semilla % 991, color: (i) => camisas[(i + p.semilla) % camisas.length], pose: "de_pie" }) : null;

        return { id: p.id, mats, uTi, uN, uBF, uPx, NM, peces, resaltes, flP, gente, E, M, r };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.22 * kb;
        s.uTi.value = t;
        s.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        // cuántas fibras van encendidas: en cada resalte avanzan de 0 a todas en lo que dura (menos su entrada y salida)
        let n = 0;
        for (const e of s.resaltes) if (t >= e.t) n = Math.max(n, clamp((t - e.t - 0.2) / Math.max(0.5, (e.dur || 2) - 0.7), 0, 1) * s.NM);
        s.uN.value = n; s.uBF.value = 1 + 0.35 * kb;
        // los peces: se sostienen en el agua (vaivén corto), baten la cola y cabecean apenas
        for (const P of s.peces) {
          // el cardumen se mece junto (lento) y cada pez un poco por su lado: nunca tanto como para tocar a otro
          const du = 0.06 * P.cw * Math.sin(t * P.w + P.a) + 0.35 * Math.sin(t * 0.23 + 0.04 * P.z), dz = 0.07 * P.rh * Math.sin(t * P.w * 0.73 + P.b) + 0.25 * Math.sin(t * 0.17 + 0.05 * P.u);
          const pos = s.E(P.u + du, P.v, P.z + dz);
          P.g.position.set(pos[0], pos[1], pos[2]);
          P.g.rotation.set(0, s.r + 0.05 * Math.sin(t * P.fc * 2.1 + P.a), 0.05 * Math.sin(t * P.w * 0.73 + P.b + 1.2));
          const k = P.Lp * s.M; P.g.scale.set(P.dir * k, k, k);
          P.cola.rotation.set(0, 0.42 * Math.sin(t * P.fc * TAU + P.b), 0);
        }
        if (s.flP) { s.gente.forEach(([x, y, dx, dy], i) => s.flP.poner(i, x, y, dx, dy, 1, 0, 0)); s.flP.listo(); }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
