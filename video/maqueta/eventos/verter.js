// Evento «verter» (ficha: verter.json; reglas: scripts/maqueta_tipos/verter.py): sobre una pieza `drenajeorilla`, el agua
// residual corre por los tubos en PULSOS (bolos de agua turbia que avanzan sobre cada tubo): de cada casa conectada, por su
// acometida y el colector de la calle, a los DESAGÜES crudos —bajan entre las casas, caen a la playa y abren en el lago una
// MANCHA turbia que crece hasta `mancha` y SE QUEDA cuando el evento termina— o a la PLANTA (entran al canal de rejas), cuya
// salida suelta pulsos menos turbios, sin mancha (no se pinta como agua limpia). Los pulsos dejan de salir de las casas al
// terminar el evento y el agua que ya iba en los tubos termina su recorrido. Ilustrativo: ni la mancha ni los pulsos miden.
// La geometría es la de la pieza (copia de casas, acometidas, colectores y bajadas de drenajeorilla.js: si allá cambia,
// cambia aquí). Seek puro: todo sale de t (ningún estado entre cuadros); el azar fijo es ctx.hash. Sin colores escritos.
(function (MAQ) {
  const HL = 0.6, HA = 0.08, U_PLAYA = -12, U_CALLE = -60, AC = 3.2, HV0 = -95, HPASO = 15, NH = 10, FILAS = [-40, -82];
  const SAL_V = 83, U_BOCA = -2.5, PL_U1 = -11, R_LAT = 0.3, R_COL = 0.5, R_BAJ = 0.6;
  const R_MIN = 12, R_MAX = 60;          // radio de la mancha (m × tamano) con mancha 0 y 1 (el mismo de verter.py)
  const VEL = 26;                        // m por segundo con vel = 1 (didáctico: no es la velocidad del agua)
  const PER = 1.5;                       // cada cuánto sale un pulso de cada casa (s, con vel = 1)
  const LS = 6.5;                        // largo de un pulso (m)
  const NSEG = 6, NA = 7;                // un pulso: medio tubo de NSEG tramos y NA puntos en su arco
  const PRE = 4.5;                       // con el evento en t ≤ 0.1 (gancho): cuánto lleva corriendo en el cuadro cero
  const RETRASO = 1.2;                   // lo que tarda el agua que entra a la planta en salir por su efluente (s; ilustrativo)
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
  const NOISE = "float h2(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }" +
    "float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h2(i), h2(i + vec2(1.0, 0.0)), f.x), mix(h2(i + vec2(0.0, 1.0)), h2(i + vec2(1.0, 1.0)), f.x), f.y); }" +
    "float fbm(vec2 p){ return 0.5 * vn(p) + 0.25 * vn(p * 2.03 + 3.1) + 0.125 * vn(p * 4.1 + 7.7); }";
  const piso = (u) => u < U_PLAYA ? HL : u < 0 ? HL + (HA + 0.04 - HL) * (u - U_PLAYA) / -U_PLAYA : HA;
  const ejeH = (u, rr) => piso(u) + rr * 0.45;
  const clave = (e) => e.pieza + "|" + e.t + "|" + e.dur;

  // las rutas del agua (u, v, h del eje, radio) de la pieza: las mismas casas y tubos que drenajeorilla.js
  function rutas(e, hz) {
    const casas = [];
    for (let f = 0; f < 2; f++) for (let j = 0; j < NH; j++) casas.push({ uc: FILAS[f], v: HV0 + HPASO * j, s: f === 0 ? -1 : 1 });
    const orden = casas.map((c, i) => [hz(i, 40), i]).sort((a, b) => a[0] - b[0]);
    const nSin = Math.round(Math.max(0, Math.min(1, e.sin_drenaje)) * casas.length);
    orden.forEach(([, i], k) => { casas[i].sin = k < nSin; });
    casas.forEach((C, i) => { const d = 6 + 1.6 * hz(i, 42); C.uf = C.uc + C.s * d / 2; });
    const VC = e.corte, DES = e.desagues || [], A_PL = Math.max(0, Math.min(1, e.a_planta));
    const vPla = casas.filter((c) => !c.sin && c.v >= VC);
    const plantaFluye = vPla.length > 0 && A_PL > 0;
    const hb = piso(U_BOCA) + R_BAJ + 0.12, hC = ejeH(U_CALLE, R_COL);
    const bajada = (g, uIni, hIni) => {
      const pts = [[uIni, g, hIni, R_BAJ]];
      for (const u of [-30, -16, U_PLAYA, -7]) if (u > uIni + 0.5) pts.push([u, g, ejeH(u, R_BAJ), R_BAJ]);
      pts.push([U_BOCA, g, hb, R_BAJ]);
      const nb = pts.length - 1;   // la boca
      pts.push([U_BOCA + 0.7, g, piso(U_BOCA + 0.7) + 0.05, 0.32], [1.4, g, HA + 0.03, 0.34]);
      return [pts, nb];
    };
    const R = [];
    casas.forEach((C, i) => {
      if (C.sin) return;
      const vv = C.v + 1.6, ub = C.s < 0 ? U_CALLE + AC + 0.9 : U_CALLE - AC - 0.9, ue = U_CALLE + C.s * -0.5;
      const aco = [[C.uf, vv, ejeH(C.uf, R_LAT), R_LAT], [ub, vv, ejeH(ub, R_LAT), R_LAT], [ue, vv, ejeH(ue, R_LAT), R_LAT]];
      if (C.v >= VC) {
        if (!plantaFluye) return;
        R.push({ pts: aco.concat([[U_CALLE, vv, hC, R_COL], [U_CALLE, 74, hC, R_COL], [-50.2, 74, ejeH(-50, R_COL), R_COL], [-44, 74, HL + 0.78, 0.45]]),
          tipo: 0, fin: "planta", ph: hz(i, 300), per: 0.75 + 0.5 * hz(i, 301) });
      } else if (DES.length) {
        const abajo = DES.filter((g) => g <= vv);
        const g = abajo.length ? Math.max(...abajo) : DES.reduce((a, b) => Math.abs(b - vv) < Math.abs(a - vv) ? b : a);
        const [baj, nb] = bajada(g, U_CALLE, hC);
        R.push({ pts: aco.concat([[U_CALLE, vv, hC, R_COL]]).concat(baj), nb: aco.length + 1 + nb, tipo: 0, fin: "lago", g,
          ph: hz(i, 300), per: 0.75 + 0.5 * hz(i, 301) });
      }
    });
    const salida = plantaFluye ? bajada(SAL_V, PL_U1 - 3.5, ejeH(PL_U1, R_BAJ))[0] : null;
    return { R, salida, plantaFluye };
  }

  // una polilínea con su largo acumulado → dónde está lo andado s (u, v, h, radio) y su dirección
  function cadenaDe(pts) {
    const S = [0];
    for (let k = 1; k < pts.length; k++) { const a = pts[k - 1], b = pts[k]; S.push(S[k - 1] + Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2])); }
    const L = S[S.length - 1];
    const en = (s) => {
      s = Math.max(0, Math.min(L, s));
      let k = 1; while (k < S.length - 1 && S[k] < s) k++;
      const a = pts[k - 1], b = pts[k], f = (s - S[k - 1]) / ((S[k] - S[k - 1]) || 1);
      const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], n = Math.hypot(d[0], d[1], d[2]) || 1;
      return { p: [a[0] + d[0] * f, a[1] + d[1] * f, a[2] + d[2] * f, a[3] + (b[3] - a[3]) * f], d: [d[0] / n, d[1] / n, d[2] / n] };
    };
    return { S, L, en };
  }

  MAQ.EVENTOS.verter = {
    orden: 47,
    armar(ctx, lista) {
      const { THREE, tonos, lin, COL, ES, hash, scene, metros, sombra } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1;
      const lS = sombra ? sombra(0, 1, 0) : 1;
      const cAgua = tonos.agua.clone();
      const cTurbio = lin(COL.tierra_media).lerp(tonos.arena, 0.3).lerp(cAgua, 0.22).multiplyScalar(oscuro ? 1.25 : 0.92);
      const kN = noche ? 0.5 : 1;
      const cPulso = cTurbio.clone().multiplyScalar(oscuro ? 1.15 : 0.66);
      const cClaro = cAgua.clone().lerp(lin(COL.costa), 0.3).lerp(cTurbio, 0.18).multiplyScalar(oscuro ? 1.2 : 1.08);
      const cCore = cTurbio.clone().multiplyScalar(0.8 * lS * kN), cBorde = cTurbio.clone().lerp(cAgua, 0.42).multiplyScalar(lS * kN);
      const cFrente = tonos.arena.clone().lerp(tonos.acento, 0.25).multiplyScalar(lS * (noche ? 0.6 : 1));
      const items = {};
      lista.forEach((e, ie) => {
        const K = e.tamano || 1, M = metros(1) * K;
        const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = (e.semilla || 1) * 7919 + (e.np || 0) * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.suelo ? ctx.suelo(e.x, e.y) : ctx.altura(e.x, e.y);
        const E = (u, v, h) => [e.x + (u * ux - v * uy) * M, base0 + h * M, -(e.y + (u * uy + v * ux) * M)];
        const vel = e.vel || 1, V = VEL * vel, gancho = e.t <= 0.1;
        const t0 = e.t - (gancho ? PRE : 0), tE = e.t + Math.max(0.3, e.dur || 0);
        const { R, salida, plantaFluye } = rutas(e, hz);
        // ---- cada ruta: su cadena, su periodo, su fase y cuántos pulsos caben a la vez en ella (ranuras)
        const rutasE = R.map((q) => {
          const c = cadenaDe(q.pts), P = PER * q.per / vel;
          return { c, P, te0: t0 + q.ph * P, tE, K: Math.ceil((c.L + LS) / V / P) + 1, tipo: 0, nb: q.nb, g: q.g, fin: q.fin };
        });
        // la planta: el agua que entra sale por el efluente RETRASO s después (pulsos más seguidos, menos turbios)
        let llegaPlanta = Infinity;
        rutasE.forEach((q) => { if (q.fin === "planta") llegaPlanta = Math.min(llegaPlanta, q.te0 + q.c.L / V); });
        if (salida && plantaFluye && isFinite(llegaPlanta)) {
          const c = cadenaDe(salida), P = 0.55 / vel, te0 = llegaPlanta + RETRASO;
          rutasE.push({ c, P, te0, tE: tE + RETRASO + (llegaPlanta - t0), K: Math.ceil((c.L + LS) / V / P) + 1, tipo: 1, fin: "salida" });
        }
        // ---- cuándo llega el primer pulso crudo a cada desagüe (de ahí crece su mancha)
        const llega = new Map();
        rutasE.forEach((q) => {
          if (q.fin !== "lago") return;
          const s = q.c.S[q.nb], ta = q.te0 + s / V;
          llega.set(q.g, Math.min(llega.has(q.g) ? llega.get(q.g) : Infinity, ta));
        });
        // ================= los pulsos: medio tubo (NSEG × NA) por ranura, encima del tubo; y un punto de halo en su cabeza
        const NS = rutasE.reduce((a, q) => a + q.K, 0), NV = (NSEG + 1) * NA;
        const pos = new Float32Array(NS * NV * 3), aA = new Float32Array(NS * NV), aK = new Float32Array(NS * NV), aS = new Float32Array(NS * NV);
        const idx = [];
        for (let n = 0; n < NS; n++) for (let a = 0; a <= NSEG; a++) for (let b = 0; b < NA; b++) {
          const i = n * NV + a * NA + b, th = Math.PI * b / (NA - 1);
          aS[i] = 0.62 + 0.45 * Math.sin(th);
          if (a < NSEG && b < NA - 1) idx.push(i, i + NA, i + 1, i + 1, i + NA, i + NA + 1);
        }
        const gP = new THREE.BufferGeometry();
        gP.setAttribute("position", new THREE.BufferAttribute(pos, 3));
        gP.setAttribute("aA", new THREE.BufferAttribute(aA, 1));
        gP.setAttribute("aK", new THREE.BufferAttribute(aK, 1));
        gP.setAttribute("aS", new THREE.BufferAttribute(aS, 1));
        gP.setIndex(idx);
        const matP = new THREE.ShaderMaterial({
          uniforms: { cR: { value: cPulso.clone() }, cC: { value: cClaro.clone() }, uNoche: { value: noche ? 1 : 0 } },
          transparent: true, depthWrite: false, side: THREE.DoubleSide,
          vertexShader: "attribute float aA, aK, aS; varying float vA, vK, vS; void main(){ vA = aA; vK = aK; vS = aS; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: SRGB + "uniform vec3 cR, cC; uniform float uNoche; varying float vA, vK, vS; void main(){ if (vA < 0.01) discard; vec3 c = mix(cR, cC, vK) * vS * (1.0 + 0.25 * uNoche); gl_FragColor = vec4(srgb(c), vA); }" });
        const mP = new THREE.Mesh(gP, matP); mP.frustumCulled = false; mP.renderOrder = 6; scene.add(mP);
        const hPos = new Float32Array(NS * 3), hA = new Float32Array(NS), hK = new Float32Array(NS);
        const gH = new THREE.BufferGeometry();
        gH.setAttribute("position", new THREE.BufferAttribute(hPos, 3));
        gH.setAttribute("aA", new THREE.BufferAttribute(hA, 1));
        gH.setAttribute("aK", new THREE.BufferAttribute(hK, 1));
        const matH = new THREE.ShaderMaterial({
          uniforms: { cR: { value: cPulso.clone() }, cC: { value: cClaro.clone() }, uPx: { value: 1 }, uM: { value: M }, uNoche: { value: noche ? 1 : 0 } },
          transparent: true, depthWrite: false,
          vertexShader: "uniform float uPx, uM; attribute float aA, aK; varying float vA, vK; void main(){ vA = aA; vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aA > 0.01 ? clamp(3.4 * uM * uPx / max(1e-3, -mv.z), 4.0, 14.0) : 0.0; }",
          fragmentShader: SRGB + "uniform vec3 cR, cC; uniform float uNoche; varying float vA, vK; void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0; if (r > 1.0) discard; float a = vA * (0.8 + 0.2 * uNoche) * (1.0 - smoothstep(0.55, 1.0, r)); if (a < 0.01) discard; vec3 c = mix(cR, cC, vK) * (1.05 + 0.3 * uNoche - 0.25 * r); gl_FragColor = vec4(srgb(c), a); }" });
        const mH = new THREE.Points(gH, matH); mH.frustumCulled = false; mH.renderOrder = 7; scene.add(mH);
        // ================= la mancha de cada desagüe crudo: un plano sobre el lago con su borde vivo (shader, función de t)
        const Rmax = R_MIN + (R_MAX - R_MIN) * (e.mancha == null ? 0.6 : e.mancha);
        const manchas = [];
        [...llega.keys()].sort((a, b) => a - b).forEach((g, k) => {
          const u0 = 1 + 0.5 * Rmax - 1.35 * (0.62 * Rmax + 0.5), u1 = 1 + 0.5 * Rmax + 1.35 * (0.62 * Rmax + 0.5), w = 1.35 * (1.05 * Rmax + 0.5);
          const h = HA + 0.04, P = [];
          for (const [u, v] of [[u0, -w], [u1, -w], [u1, w], [u0, w]]) P.push(...E(u, g + v, h));
          const g2 = new THREE.BufferGeometry();
          g2.setAttribute("position", new THREE.BufferAttribute(new Float32Array(P), 3));
          g2.setAttribute("aP", new THREE.BufferAttribute(new Float32Array([u0, -w, u1, -w, u1, w, u0, w]), 2));
          g2.setIndex([0, 1, 2, 0, 2, 3]);
          const mat = new THREE.ShaderMaterial({
            uniforms: { cT: { value: cCore.clone() }, cE: { value: cBorde.clone() }, cF: { value: cFrente.clone() }, uR: { value: 0 }, uA: { value: 0 },
              uFr: { value: 0 }, uSeg: { value: 0 }, uSem: { value: 13.7 * k + 3.1 * (e.semilla || 1) } },
            transparent: true, depthWrite: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -8,
            vertexShader: "attribute vec2 aP; varying vec2 vP; void main(){ vP = aP; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: SRGB + NOISE + "uniform vec3 cT, cE, cF; uniform float uR, uA, uFr, uSeg, uSem; varying vec2 vP; void main(){" +
              " if (uR < 0.2) discard;" +
              " vec2 q = vec2((vP.x - 0.5 * uR - 1.0) / (0.62 * uR + 0.5), vP.y / (1.05 * uR + 0.5));" +
              " vec2 o = vec2(uSem, -uSem * 0.7);" +
              " float n = fbm(vP * 0.085 + o + vec2(0.0, uSeg * 0.05)), n2 = fbm(vP * 0.32 - o - vec2(uSeg * 0.09, 0.0));" +
              " float d = length(q) + 0.42 * (n - 0.5) + 0.12 * (n2 - 0.5);" +
              " float a = 1.0 - smoothstep(0.8, 1.0, d); if (a < 0.01) discard;" +
              " vec3 c = mix(cT, cE, smoothstep(0.15, 0.95, d)) * (0.86 + 0.28 * n2);" +
              " float rim = uFr * smoothstep(0.8, 0.92, d) * (1.0 - smoothstep(0.92, 1.0, d)); c = mix(c, cF, 0.55 * rim);" +
              " vec2 b = vP - vec2(1.5, 0.0); float core = exp(-dot(b, b) / (9.0 + 0.05 * uR * uR)); c = mix(c, cT * 0.8, 0.45 * core);" +
              " gl_FragColor = vec4(srgb(c), uA * a * (0.6 + 0.3 * (1.0 - smoothstep(0.0, 0.9, d)) + 0.25 * rim)); }" });
          const m = new THREE.Mesh(g2, mat); m.frustumCulled = false; m.renderOrder = 4; scene.add(m);
          const ta = llega.get(g), tg = Math.max(ta + 1.5, tE);
          manchas.push({ mat, ta, tg });
        });
        items[clave(e)] = { E, rutasE, V, NS, NV, pos, aA, aK, gP, hPos, hA, hK, gH, matH, manchas, Rmax: Rmax };
      });
      return { items };
    },
    inicio(t, st) {
      if (!st) return;
      for (const k in st.items) {
        const it = st.items[k];
        it.aA.fill(0); it.gP.attributes.aA.needsUpdate = true;
        it.hA.fill(0); it.gH.attributes.aA.needsUpdate = true;
        for (const m of it.manchas) { m.mat.uniforms.uA.value = 0; m.mat.uniforms.uR.value = 0; }
      }
    },
    aplicar(t, e, ctx, st) {
      if (!st) return;
      const it = st.items[clave(e)];
      if (!it) return;
      const { E, V } = it;
      // ---- los pulsos: cada ranura de cada ruta lleva el pulso n ≡ ranura (mod K) más reciente que ya salió
      let n0 = 0;
      for (const q of it.rutasE) {
        const tTop = Math.min(t, q.tE), nMax = Math.floor((tTop - q.te0) / q.P);
        for (let j = 0; j < q.K; j++) {
          const sl = n0 + j;
          let n = nMax - ((((nMax - j) % q.K) + q.K) % q.K);
          if (n < 0 || nMax < 0) continue;
          const te = q.te0 + n * q.P, s1 = (t - te) * V;
          if (te > t || s1 - LS > q.c.L) continue;
          const sh = Math.min(s1, q.c.L), sa = Math.max(0, s1 - LS);
          if (sh - sa < 0.3) continue;
          // medio tubo de NSEG tramos, de la cola (sa) a la cabeza (sh)
          for (let a = 0; a <= NSEG; a++) {
            const f = a / NSEG, s = sa + (sh - sa) * f, { p, d } = q.c.en(s);
            const sx = -d[1], sy = d[0], ln = Math.hypot(sx, sy) || 1, ax = sx / ln, ay = sy / ln;   // de lado (en u, v)
            const rr = p[3] * 1.7 + 0.22, al = Math.pow(Math.sin(Math.PI * Math.min(1, Math.max(0, (s - (s1 - LS)) / LS))), 0.5);
            for (let b = 0; b < NA; b++) {
              const th = Math.PI * b / (NA - 1), cs = Math.cos(th), sn = Math.sin(th);
              const P = E(p[0] + rr * cs * ax, p[1] + rr * cs * ay, p[2] + rr * sn * 0.9);
              const i = (sl * it.NV + a * NA + b);
              it.pos[i * 3] = P[0]; it.pos[i * 3 + 1] = P[1]; it.pos[i * 3 + 2] = P[2];
              it.aA[i] = 0.92 * al; it.aK[i] = q.tipo;
            }
          }
          const H = q.c.en(Math.max(0, sh - 0.6)).p, PH = E(H[0], H[1], H[2] + H[3] * 1.2 + 0.1);
          it.hPos[sl * 3] = PH[0]; it.hPos[sl * 3 + 1] = PH[1]; it.hPos[sl * 3 + 2] = PH[2];
          it.hA[sl] = 0.9; it.hK[sl] = q.tipo;
        }
        n0 += q.K;
      }
      it.gP.attributes.position.needsUpdate = true; it.gP.attributes.aA.needsUpdate = true; it.gP.attributes.aK.needsUpdate = true;
      it.gH.attributes.position.needsUpdate = true; it.gH.attributes.aA.needsUpdate = true; it.gH.attributes.aK.needsUpdate = true;
      it.matH.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      // ---- la mancha: crece desde que llega el primer pulso crudo hasta el final del evento, y se queda
      for (const m of it.manchas) {
        if (t < m.ta) continue;
        const x = Math.min(1, (t - m.ta) / (m.tg - m.ta)), g = 1 - (1 - x) * (1 - x);
        const u = m.mat.uniforms;
        u.uR.value = it.Rmax * Math.max(0.04, g); u.uA.value = Math.min(1, (t - m.ta) / 0.4);
        u.uFr.value = x < 1 ? 1 : Math.max(0, 1 - (t - m.tg) / 1.5);
        u.uSeg.value = t;
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
