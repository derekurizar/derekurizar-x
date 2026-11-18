// Evento «cerrarcalle» (ficha: cerrarcalle.json; reglas: scripts/maqueta_tipos/cerrarcalle.py): el domingo de paseo sobre
// una `avenidareforma`. En un tramo de la vía principal (entre dos cruces, lo resuelve el .py) pasa, en este orden:
//   1. las VALLAS: una fila atravesada en cada calzada en los extremos del tramo y a los dos lados de cada cruce de adentro
//      (la calle que cruza sigue abierta); cada valla sube del asfalto, rebota apenas y se queda, una fila tras otra;
//   2. el FLUJO de carros sale (escribe ctx.cuadro.vis[flujo], como «desaparecer»);
//   3. la GENTE entra, uno a uno, y llena las dos calzadas en los dos sentidos: caminan, trotan y pedalean.
// Genérico e ilustrativo: la fuente no dice qué puntos se cierran ni con qué vallas; nada de marcas ni de texto. Las
// vallas son de tubo con un panel a franjas (muro y «mal» del estilo), de 2 m × 1 m; las bicicletas, de cuadro tubular con
// ruedas de 16 segmentos y las bielas que giran; el ciclista va sentado (la pose `sentado` sin banco de la persona).
// De noche: una lámpara ámbar intermitente sobre una de cada dos vallas y el faro de cada bicicleta.
// Seek puro: cada valla y cada persona tienen su segundo de entrada (de la semilla) y su posición es función de t.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
  const ASF = 0.45;                         // la altura del asfalto de la avenidareforma sobre el suelo (m)
  const SILLIN = 0.88, CADERA_SENTADO = 0.47, BB = [0, 0.3, 0], R_RUEDA = 0.34, EJE_R = 0.52;

  MAQ.EVENTOS.cerrarcalle = {
    orden: 46,
    armar(ctx, lista) {
      const { THREE, tonos, sombra, hash, ES, scene, lin, COL, clamp, GLSL_COMUN, uComun } = ctx;
      const noche = !!ES.noche;
      // ---- caras con la luz horneada, en metros locales (x adelante, y arriba, z a la derecha)
      const cara = (acc, P, col, ref, tinte) => {
        const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
        let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
        const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
        if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx, ny, nz), q = acc.pos.length / 3;
        for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); acc.tin.push(tinte ? 1 : 0); }
        acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
      };
      const caja = (acc, x0, x1, y0, y1, z0, z1, col, tinte) => {
        const P = (x, y, z) => [x, y, z];
        cara(acc, [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], col, [0, 1, 0], tinte);
        cara(acc, [P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)], col.clone().multiplyScalar(0.6), [0, -1, 0], tinte);
        cara(acc, [P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], col, [1, 0, 0], tinte);
        cara(acc, [P(x0, y0, z0), P(x0, y1, z0), P(x0, y1, z1), P(x0, y0, z1)], col, [-1, 0, 0], tinte);
        cara(acc, [P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], col, [0, 0, 1], tinte);
        cara(acc, [P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0)], col, [0, 0, -1], tinte);
      };
      const tubo = (acc, A, B, r, seg, col, tinte) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2), tinte);
        }
      };
      const nueva = () => ({ pos: [], col: [], idx: [], tin: [] });
      const geo = (acc) => {
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(acc.pos), 3));
        g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(acc.col), 3));
        g.setAttribute("aTinte", new THREE.BufferAttribute(new Float32Array(acc.tin), 1));
        g.setIndex(new THREE.BufferAttribute(new Uint32Array(acc.idx), 1));
        return g;
      };
      // material instanciado: el color horneado × el color de la instancia donde `aTinte` (el cuadro de la bici)
      const material = () => new THREE.ShaderMaterial({ uniforms: { ...uComun(), uBrillo: { value: 1 } }, side: THREE.DoubleSide,
        vertexShader: "attribute vec3 color; attribute float aTinte; varying vec3 vCol, vPos; void main(){ vec3 c = color;\n#ifdef USE_INSTANCING_COLOR\n c = mix(c, c * instanceColor, aTinte);\n#endif\n vCol = c; mat4 im = mat4(1.0);\n#ifdef USE_INSTANCING\n im = instanceMatrix;\n#endif\n vec4 w = modelMatrix * im * vec4(position, 1.0); vPos = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }",
        fragmentShader: GLSL_COMUN + "uniform float uBrillo; varying vec3 vCol, vPos; void main(){ vec3 c = vCol * uBrillo; gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
      const instancias = (acc, n, orden) => { const m = new THREE.InstancedMesh(geo(acc), material(), Math.max(1, n)); m.frustumCulled = false; m.renderOrder = orden;
        const cero = new THREE.Matrix4().makeScale(0, 0, 0); for (let i = 0; i < m.count; i++) m.setMatrixAt(i, cero); scene.add(m); return m; };

      // ---- los tonos (todos del estilo)
      const cBlanco = tonos.muro.clone().lerp(tonos.arena, 0.1).multiplyScalar(noche ? 1.05 : 1.0);
      const cFranja = tonos.mal.clone().lerp(tonos.muro, 0.08);
      const cMetal = tonos.pavimento.clone().lerp(tonos.muro, 0.35);
      const cPie = tonos.asfalto.clone().lerp(tonos.pavimento, 0.35);
      const cLlanta = tonos.asfalto.clone().multiplyScalar(0.45);
      const cRin = tonos.pavimento.clone().lerp(tonos.muro, 0.5);
      const cCuadro = tonos.muro.clone();
      const cLampara = tonos.medio.clone().lerp(lin(COL.luces), 0.3);

      // ---- LA VALLA (2.0 m × 1.0 m): pies en V, dos largueros, panel de franjas, lámpara arriba
      const va = nueva();
      for (const sx of [-0.92, 0.92]) {
        caja(va, sx - 0.05, sx + 0.05, 0, 0.04, -0.32, 0.32, cPie);                 // la zapata
        tubo(va, [sx, 0.03, -0.28], [sx, 1.0, 0], 0.025, 6, cMetal);                 // el pie en V
        tubo(va, [sx, 0.03, 0.28], [sx, 1.0, 0], 0.025, 6, cMetal);
      }
      tubo(va, [-0.97, 1.0, 0], [0.97, 1.0, 0], 0.03, 8, cMetal);                    // larguero de arriba
      tubo(va, [-0.97, 0.42, 0], [0.97, 0.42, 0], 0.025, 8, cMetal);                 // larguero de abajo
      const NF = 7;
      for (let j = 0; j < NF; j++) {                                                  // el panel a franjas (al bies)
        const x0 = -0.9 + 1.8 * j / NF, x1 = -0.9 + 1.8 * (j + 1) / NF, c = j % 2 ? cFranja : cBlanco;
        for (const z of [-0.018, 0.018]) cara(va, [[x0, 0.5, z], [x1, 0.5, z], [x1 + 0.06, 0.92, z], [x0 + 0.06, 0.92, z]], c, [0, 0, Math.sign(z)]);
      }
      caja(va, -0.92, 0.92, 0.47, 0.5, -0.025, 0.025, cBlanco.clone().multiplyScalar(0.85));
      caja(va, -0.9, 0.92, 0.92, 0.95, -0.025, 0.025, cBlanco.clone().multiplyScalar(0.85));
      caja(va, 0.78, 0.92, 1.03, 1.13, -0.05, 0.05, cLampara);                        // la lámpara (de día, apagada)

      // ---- LA BICICLETA (metros; el origen en el eje del pedalier, en el suelo)
      const bi = nueva(), bie = nueva();
      const ruedas = [[-EJE_R, R_RUEDA], [EJE_R, R_RUEDA]];
      for (const [cx, cy] of ruedas) {
        const SEG = 16;
        for (let j = 0; j < SEG; j++) {
          const a0 = TAU * j / SEG, a1 = TAU * (j + 1) / SEG;
          tubo(bi, [cx + Math.cos(a0) * R_RUEDA, cy + Math.sin(a0) * R_RUEDA, 0], [cx + Math.cos(a1) * R_RUEDA, cy + Math.sin(a1) * R_RUEDA, 0], 0.032, 5, cLlanta);
          tubo(bi, [cx + Math.cos(a0) * 0.29, cy + Math.sin(a0) * 0.29, 0], [cx + Math.cos(a1) * 0.29, cy + Math.sin(a1) * 0.29, 0], 0.012, 4, cRin);
        }
        for (let j = 0; j < 4; j++) { const a = TAU * j / 8 + 0.3; tubo(bi, [cx - Math.cos(a) * 0.29, cy - Math.sin(a) * 0.29, 0], [cx + Math.cos(a) * 0.29, cy + Math.sin(a) * 0.29, 0], 0.005, 3, cRin); }
        tubo(bi, [cx, cy, -0.05], [cx, cy, 0.05], 0.03, 8, cRin);
      }
      const P = { bb: [0, BB[1], 0], tras: [-EJE_R, R_RUEDA, 0], sil: [-0.16, 0.82, 0], cab: [0.38, 0.84, 0], del: [EJE_R, R_RUEDA, 0] };
      const T = (a, b, r) => tubo(bi, a, b, r, 6, cCuadro, true);
      T(P.tras, P.bb, 0.018); T(P.bb, P.sil, 0.022); T(P.sil, [0.36, 0.8, 0], 0.02); T(P.bb, [0.36, 0.76, 0], 0.024);     // vainas, sillín, barra, diagonal
      for (const z of [-0.05, 0.05]) { T([P.tras[0], P.tras[1], z], [P.sil[0] + 0.02, P.sil[1] - 0.04, 0], 0.012); T([P.del[0], P.del[1], z], [0.37, 0.8, 0], 0.016); }
      tubo(bi, [0.37, 0.8, 0], [0.4, 1.0, 0], 0.016, 6, cMetal);                    // la potencia
      tubo(bi, [0.4, 1.0, -0.26], [0.4, 1.0, 0.26], 0.014, 6, cMetal);               // el manubrio
      for (const z of [-0.26, 0.26]) tubo(bi, [0.4, 1.0, z], [0.4, 1.0, z + Math.sign(z) * 0.07], 0.022, 6, cLlanta);
      tubo(bi, P.sil, [-0.17, SILLIN, 0], 0.012, 5, cMetal);                         // tija y sillín
      caja(bi, -0.3, -0.06, SILLIN, SILLIN + 0.05, -0.07, 0.07, cLlanta);
      caja(bi, 0.42, 0.47, 0.9, 0.96, -0.03, 0.03, cMetal);                          // el faro
      // las bielas y los pedales (giran alrededor del pedalier: otra malla)
      tubo(bie, [0, 0, 0.07], [0, 0.17, 0.07], 0.012, 5, cMetal); tubo(bie, [0, 0, -0.07], [0, -0.17, -0.07], 0.012, 5, cMetal);
      caja(bie, -0.05, 0.05, 0.16, 0.18, 0.07, 0.17, cLlanta); caja(bie, -0.05, 0.05, -0.18, -0.16, -0.17, -0.07, cLlanta);
      tubo(bie, [0, 0, -0.08], [0, 0, 0.08], 0.05, 10, cMetal);

      const mats = new Set();
      const est = lista.map((e) => {
        const sem = (e.semilla || 1) * 7919, hz = (i, k) => hash(i + sem, k);
        const KG = clamp(+e.gente_tamano || 1, 1, 2), k = e.k || 1;
        const { eje, sec, cs } = e;
        const en = (s) => {               // el eje a s: punto, dirección y la sección (las x de las dos calzadas)
          let i = 0; while (i < cs.length - 2 && cs[i + 1] < s) i++;
          const d = (cs[i + 1] - cs[i]) || 1, u = clamp((s - cs[i]) / d, 0, 1), a = sec[i], b = sec[i + 1];
          const L = (j) => a[j] + (b[j] - a[j]) * u;
          return { y: L(0), e2: L(2), e3: L(3), e4: L(4), e5: L(5), dx: (eje[i + 1][0] - eje[i][0]) / d, dy: (eje[i + 1][1] - eje[i][1]) / d };
        };
        // ---- las vallas: cada fila atraviesa una calzada (oeste e2–e3, este e4–e5) sobre la sección de su s
        const vallas = [], lamp = [];
        const D = e.dur, T0 = e.t, filas = e.barreras.length * 2;
        e.barreras.forEach((s, ib) => {
          const q = en(s);
          for (const [lado, a, b] of [[0, q.e2, q.e3], [1, q.e4, q.e5]]) {
            const w = Math.abs(b - a) - 0.4 * k, n = Math.max(1, Math.round(w / (2.05 * KG * k)));
            const fila = ib * 2 + lado, tf = T0 + 0.28 * D * (filas > 1 ? fila / (filas - 1) : 0);
            for (let j = 0; j < n; j++) {
              const x = Math.min(a, b) + 0.2 * k + w * (j + 0.5) / n, kk = vallas.length;
              vallas.push({ x, y: q.y + (hz(kk, 3) - 0.5) * 0.25 * k, a: (hz(kk, 4) - 0.5) * 0.05, t0: tf + 0.06 * j });
              if (j % 2 === 0) lamp.push(kk);
            }
          }
        });
        // ---- la gente y las bicicletas: calzada, carril lateral, sentido, velocidad, fase y segundo de entrada
        const S0 = e.s0 + 3 * k, S1 = e.s1 - 3 * k, SPAN = Math.max(10 * k, S1 - S0);
        const NPe = Math.max(0, e.personas | 0), NB = Math.max(0, e.bicicletas | 0);
        const gente = [];
        for (let i = 0; i < NPe; i++) {
          const r = hz(i, 10), modo = r < 0.62 ? 0 : 1;                               // 0 camina · 1 trota
          gente.push({ lado: hz(i, 11) < 0.5 ? 0 : 1, f: 0.1 + 0.8 * hz(i, 12), dir: hz(i, 13) < 0.5 ? 1 : -1,
            vel: modo ? 2.4 + 0.8 * hz(i, 14) : 1.0 + 0.45 * hz(i, 14), s0: hz(i, 15) * SPAN, te: T0 + D * (0.36 + 0.56 * hz(i, 16)) });
        }
        const bicis = [];
        for (let i = 0; i < NB; i++) {
          bicis.push({ lado: hz(i, 21) < 0.5 ? 0 : 1, f: 0.12 + 0.76 * hz(i, 22), dir: hz(i, 23) < 0.5 ? 1 : -1,
            vel: 3.6 + 1.6 * hz(i, 24), s0: hz(i, 25) * SPAN, te: T0 + D * (0.4 + 0.5 * hz(i, 26)) });
        }
        const flP = NPe ? ctx.flota("persona", NPe, { tamano: KG, lev: ASF, orden: 6, semilla: (e.semilla * 17) % 991, pose: () => "caminar" }) : null;
        const flC = NB ? ctx.flota("persona", NB, { tamano: KG, lev: ASF + (SILLIN - CADERA_SENTADO) * KG, orden: 6, semilla: (e.semilla * 29 + 5) % 991,
          pose: () => ({ nombre: "sentado", banco: false }) }) : null;
        const mV = vallas.length ? instancias(va, vallas.length, 5) : null;
        const mB = NB ? instancias(bi, NB, 5) : null, mBie = NB ? instancias(bie, NB, 5) : null;
        const tintes = [tonos.bien, tonos.medio, tonos.mal, tonos.secundario || tonos.muro, tonos.muro].filter(Boolean);
        if (mB) { for (let i = 0; i < NB; i++) mB.setColorAt(i, tintes[Math.floor(hz(i, 27) * tintes.length) % tintes.length]); mB.instanceColor.needsUpdate = true; }
        for (const m of [mV, mB, mBie]) if (m) mats.add(m.material);
        // de noche: la lámpara intermitente de las vallas y el faro de cada bici (puntos aditivos)
        let luz = null;
        if (noche && (lamp.length || NB)) {
          const N = lamp.length + NB, g = new THREE.BufferGeometry();
          g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
          g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(N), 1));
          g.setAttribute("aC", new THREE.BufferAttribute(new Float32Array(N), 1));
          const pm = new THREE.ShaderMaterial({ uniforms: { cA: { value: cLampara.clone() }, cB: { value: lin(COL.luces) }, uTam: { value: 0.7 * KG * k }, uPx: { value: 1 } },
            transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            vertexShader: "attribute float aK, aC; uniform float uTam, uPx; varying float vK, vC; void main(){ vK = aK; vC = aC; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aK > 0.0 ? clamp(uTam * uPx / max(1e-3, -mv.z) * 3.0, 3.0, 18.0) : 0.0; }",
            fragmentShader: SRGB + "uniform vec3 cA, cB; varying float vK, vC; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = (exp(-r * r * 8.0) + exp(-r * r * 50.0)) * vK; vec3 c = srgb(mix(cA, cB, vC)); gl_FragColor = vec4(c * a, a); }" });
          const pts = new THREE.Points(g, pm); pts.frustumCulled = false; pts.renderOrder = 9; scene.add(pts);
          luz = { pts, pm };
        }
        return { e, en, vallas, lamp, gente, bicis, flP, flC, mV, mB, mBie, luz, KG, k, S0, SPAN, hz };
      });
      return { est, mats: [...mats], m4: new THREE.Matrix4(), m5: new THREE.Matrix4(), q: new THREE.Quaternion(), p: new THREE.Vector3(),
        sc: new THREE.Vector3(), Y: new THREE.Vector3(0, 1, 0), Z: new THREE.Vector3(0, 0, 1), cero: new THREE.Matrix4().makeScale(0, 0, 0) };
    },
    inicio(t, st, ctx) { ctx.cuadro.vis = ctx.cuadro.vis || {}; },
    aplicar(t, e, ctx) {
      // el flujo de la vía sale (se encoge) entre el 15 % y el 45 % del evento y no vuelve
      if (!e.flujo) return;
      const V = ctx.cuadro.vis = ctx.cuadro.vis || {};
      if (t >= e.t) V[e.flujo] = Math.min(V[e.flujo] === undefined ? 1 : V[e.flujo], 1 - ctx.suave(e.t + 0.15 * e.dur, e.t + 0.45 * e.dur, t));
    },
    en(t, st, ctx) {
      if (!st) return;
      const { clamp, suave } = ctx;
      const { m4, m5, q, p, sc, Y, Z, cero } = st;
      const um = 1 / (ctx.unidad_m || 1);
      const alt = (x, y) => (ctx.altura ? ctx.altura(x, y) : ctx.suelo(x, y));
      const rebote = (x) => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
      const uPx = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      for (const s of st.est) {
        const { KG, k } = s, kM = KG * k;
        // ---- las vallas suben, rebotan y se quedan
        if (s.mV) {
          s.vallas.forEach((v, i) => {
            const g = clamp((t - v.t0) / 0.45, 0, 1);
            if (g <= 0) { s.mV.setMatrixAt(i, cero); return; }
            const h = clamp(rebote(g), 0, 1.1);
            p.set(v.x, alt(v.x, v.y) + ASF * um, -v.y); q.setFromAxisAngle(Y, v.a); sc.set(kM, kM * Math.max(1e-3, h), kM);
            s.mV.setMatrixAt(i, m4.compose(p, q, sc));
          });
          s.mV.instanceMatrix.needsUpdate = true;
        }
        // ---- dónde va cada quien en t (a lo largo del tramo, en su calzada, con su sentido; se desvanece en los extremos)
        const donde = (g) => {
          const u = (((g.s0 + g.dir * g.vel * t * um) % s.SPAN) + s.SPAN) % s.SPAN, sv = s.S0 + u, Q = s.en(sv);
          const a = g.lado ? Q.e4 : Q.e2, b = g.lado ? Q.e5 : Q.e3;
          const borde = clamp(u / (5 * k), 0, 1) * clamp((s.SPAN - u) / (5 * k), 0, 1);
          const kIn = suave(g.te, g.te + 0.55, t);
          return { x: a + (b - a) * g.f, y: Q.y, dx: Q.dx * g.dir, dy: Q.dy * g.dir, kk: borde * kIn };
        };
        if (s.flP) {
          s.gente.forEach((g, i) => { const W = donde(g); s.flP.poner(i, W.x, W.y, W.dx, W.dy, W.kk, 0, W.kk > 0 ? g.vel : 0); });
          s.flP.listo();
        }
        const faros = new Array(s.bicis.length).fill(null);
        if (s.flC) {
          s.bicis.forEach((g, i) => {
            const W = donde(g);
            if (W.kk <= 0) { s.flC.poner(i, 0, 0, 1, 0, 0, 0, 0); s.mB.setMatrixAt(i, cero); s.mBie.setMatrixAt(i, cero); return; }
            const ang = Math.atan2(W.dy, W.dx), dn = Math.hypot(W.dx, W.dy) || 1, fx = W.dx / dn, fy = W.dy / dn;
            s.flC.poner(i, W.x - fx * 0.17 * kM, W.y - fy * 0.17 * kM, W.dx, W.dy, W.kk, 0, 0);
            p.set(W.x, alt(W.x, W.y) + ASF * um, -W.y); q.setFromAxisAngle(Y, ang); sc.setScalar(kM * W.kk);
            m4.compose(p, q, sc); s.mB.setMatrixAt(i, m4);
            const giro = -(g.vel / (R_RUEDA * 2.6)) * t - TAU * s.hz(i, 28);           // las bielas: una vuelta por cada 2.6 de la rueda
            m5.makeTranslation(BB[0], BB[1], BB[2]).multiply(new ctx.THREE.Matrix4().makeRotationAxis(Z, giro));
            s.mBie.setMatrixAt(i, m4.clone().multiply(m5));
            faros[i] = [W.x + fx * 0.45 * kM, alt(W.x, W.y) + (ASF + 0.93 * KG) * um, W.y + fy * 0.45 * kM, W.kk];
          });
          s.flC.listo();
          s.mB.instanceMatrix.needsUpdate = true; s.mBie.instanceMatrix.needsUpdate = true;
        }
        // ---- de noche: lámparas que parpadean (encendidas cuando la valla ya subió) y los faros
        if (s.luz) {
          const A = s.luz.pts.geometry.attributes;
          s.lamp.forEach((iv, j) => {
            const v = s.vallas[iv], on = t >= v.t0 + 0.45 ? (((t * 1.25 + s.hz(iv, 30)) % 1) < 0.55 ? 1 : 0.15) : 0;
            const c = Math.cos(v.a), sn = Math.sin(v.a), lx = 0.85 * kM;
            A.position.setXYZ(j, v.x + c * lx, alt(v.x, v.y) + (ASF + 1.1 * KG) * um, -(v.y + sn * lx)); A.aK.setX(j, on); A.aC.setX(j, 0);
          });
          for (let j = 0; j < s.bicis.length; j++) {
            const f = faros[j], n = s.lamp.length + j;
            if (f) { A.position.setXYZ(n, f[0], f[1], -f[2]); A.aK.setX(n, 0.8 * f[3]); A.aC.setX(n, 1); }
            else A.aK.setX(n, 0);
          }
          A.position.needsUpdate = true; A.aK.needsUpdate = true; A.aC.needsUpdate = true;
          s.luz.pm.uniforms.uPx.value = uPx;
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
