// Evento «magma» (ficha: magma.json; reglas: scripts/maqueta_tipos/magma.py): sobre una pieza `subduccion` (esquema, no a
// escala), la secuencia didáctica del magma. Usa la MISMA cuenta del corte que subduccion.js (techo, tierra, perfil, el
// bloque y su lugar en el suelo): si allá cambia, cambia aquí.
// - EL MANTO (fase 1): unas gotas de agua salen del techo de la placa y la cuña de manto de ENCIMA se enciende, en la cara
//   del corte, sobre placa-100 (la placa no se enciende: no se derrite).
// - LA GOTA (fase 2): una gota de magma sale del manto encendido, sube a la bolsa al pie de la continental y por el conducto
//   del cono partido; deja tras de sí un hilo encendido que queda tibio.
// - EL CRÁTER (fase 3): el cráter del cono del frente se enciende en el acento (cuenco brillante y su halo).
// - LA FILA (con `fila`): los cráteres del resto se encienden uno tras otro, paralelos a la fosa (`orden`), y quedan
//   encendidos. Después del evento todo lo encendido sigue encendido (late apenas).
// Seek puro: todo sale de t − e.t; el azar es ctx.hash. Sin colores escritos (ctx.tonos, ctx.COL). Sin texto ni números.
(function (MAQ) {
  const L1 = 600, WV = 450, D = 600, W0 = 45, DIP = 55, FW = 110, UCOSTA = 170, TC = 150, BEND = 150, RC = 0.1;
  const L2 = 1300, UC = (L2 - L1) / 2, TAU = 2 * Math.PI;
  const liso = (a, b, x) => { if (b <= a) return x >= b ? 1 : 0; const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const techo = (u, ta) => u <= 0 ? W0 + DIP * Math.exp(-(u / FW) * (u / FW)) : W0 + DIP + ta * (u - BEND * (1 - Math.exp(-u / BEND)));
  const fase = (s) => ((s * 0.6180339887) % 1) * TAU;
  const tierra = (u, v, ph) => u < UCOSTA ? 0 : 22 * liso(UCOSTA, UCOSTA + 260, u) + 6 * Math.sin(u / 95 + ph) * Math.sin(v / 140 + 1.3 * ph) * liso(UCOSTA + 40, UCOSTA + 240, u);
  const perfil = (x) => x >= 1 ? 0 : x < RC ? Math.pow(1 - RC, 1.55) - 0.12 * (1 - (x / RC) * (x / RC)) : Math.pow(1 - x, 1.55);
  // las fases (las MISMAS que magma.py): [fin del manto, inicio y fin del ascenso, inicio y fin del cráter del frente]
  const FASES = { false: [0.25, 0.2, 0.85, 0.82, 1.0], true: [0.15, 0.12, 0.5, 0.48, 0.58] };
  const sRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

  function preparar(ctx, e, ie) {
    const { THREE, tonos, lin, COL, ES, hash, scene, metros } = ctx;
    const noche = !!ES.noche;
    const C = (a, b) => lin(COL[a] || COL[b] || COL.secundario);
    const K = e.tamano, M = metros(1) * K, ph = fase(e.semilla), ta = e.ta, UA = e.u_arco;
    const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
    const hz = (i, k) => hash(i + 5113 * (ie + 1) + e.semilla * 173, k);
    const y0 = ctx.suelo(e.x, e.y) - 0.8 * M;
    const E = (u, v, z) => { const x = e.x + ((u - UC) * ux - v * uy) * M, y = e.y + ((u - UC) * uy + v * ux) * M; return [x, y0 + (D + z) * M, -y]; };
    // ---- los tonos (del estilo)
    const cMagma = tonos.mal.clone().lerp(C("luces", "acento"), 0.22), cLuz = C("luces", "acento");
    const cAcento = tonos.acento.clone(), cGota = C("costa", "secundario").lerp(tonos.agua, 0.2);
    const cHondo = cMagma.clone().multiplyScalar(0.62);
    const conos = e.conos, c0 = conos[0], NC = conos.length;
    const UM = UA - 25, ZM = -(techo(UA - 25, ta) - 42);
    let uw = 0; { let a = 0, b = 3000; for (let i = 0; i < 50; i++) { const m = (a + b) / 2; if (techo(m, ta) < TC) a = m; else b = m; } uw = a; }
    const altoC = (c, u, v) => { const x = Math.hypot(u - c[0], v - c[1]) / c[2]; return tierra(u, v, ph) + c[3] * perfil(x); };
    const uPx = { value: 1 }, uT = { value: 0 }, objs = [];
    const material = (vs, fs, uni, aditivo, lado) => new THREE.ShaderMaterial({ uniforms: { uPx, uT, uM: { value: M }, uNoche: { value: noche ? 1 : 0 }, ...uni },
      transparent: true, depthWrite: false, side: lado ? THREE.DoubleSide : THREE.FrontSide,
      blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending, vertexShader: vs, fragmentShader: sRGB + fs });
    const geo = (pos, attrs, idx) => {
      const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(pos instanceof Float32Array ? pos : new Float32Array(pos), 3));
      for (const [n, a, d] of attrs) g.setAttribute(n, new THREE.BufferAttribute(a instanceof Float32Array ? a : new Float32Array(a), d));
      if (idx) g.setIndex(new THREE.BufferAttribute(new Uint32Array(idx), 1));
      return g;
    };
    const poner = (o, orden) => { o.frustumCulled = false; o.renderOrder = orden; o.visible = false; scene.add(o); objs.push(o); return o; };

    // ================= 1. el manto de encima (la cuña sobre la placa, en la cara del corte) que se enciende
    const uMan = { value: 0 };
    { const ua = Math.max(uw, UM - 260), ub = Math.min(L2, UM + 260), nu = 52, nz = 10, pos = [], wgt = [], idx = [];
      for (let i = 0; i <= nu; i++) {
        const u = ua + (ub - ua) * i / nu, zt = -TC - 0.5, zb = -techo(u, ta) + 2.5;
        for (let k = 0; k <= nz; k++) {
          const z = zt + (Math.min(zt, zb) - zt) * k / nz, dm = Math.hypot((u - UM) / 130, (z - ZM) / 62);
          pos.push(...E(u, -WV - 1.0, z)); wgt.push(Math.exp(-dm * dm * 1.5), u, z);
        }
      }
      for (let i = 0; i < nu; i++) for (let k = 0; k < nz; k++) { const a = i * (nz + 1) + k, b = a + 1, c = a + nz + 1, d = c + 1; idx.push(a, c, b, b, c, d); }
      poner(new THREE.Mesh(geo(pos, [["aW", wgt, 3]], idx), material(
        "attribute vec3 aW; varying vec3 vW; void main(){ vW = aW; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        "uniform vec3 cA, cB; uniform float uK, uT, uNoche; varying vec3 vW; void main(){ float w = vW.x * (0.86 + 0.14 * sin(uT * 1.7 + vW.y * 0.035 + vW.z * 0.05)); float a = uK * w; if (a < 0.01) discard; vec3 c = mix(cA, cB, 0.55 * w * w); gl_FragColor = vec4(srgb(c * (1.0 + 0.35 * uNoche)), min(1.0, a * (0.95 + 0.05 * uNoche))); }",
        { uK: uMan, cA: { value: cMagma.clone() }, cB: { value: cLuz.clone() } }, false, true)), 11);
    }
    // las gotas de agua que salen de la placa hacia la cuña (fase 1)
    const uAgua = { value: 0 };
    { const pos = [], aF = [];
      for (let i = 0, n = 0; i < 300 && n < 22; i++) {
        const u = UM - 150 + 260 * hz(i, 1); if (techo(u, ta) < TC + 20) continue;
        pos.push(...E(u, -WV - 1.6, -techo(u, ta) + 2)); aF.push(hz(i, 2), (24 + 30 * hz(i, 3)) * M, 1.8 + 1.2 * hz(i, 4), 0); n++;
      }
      poner(new THREE.Points(geo(pos, [["aF", aF, 4]]), material(
        "uniform float uPx, uT, uM; attribute vec4 aF; varying float vA; void main(){ float a = fract(uT / aF.z + aF.x); vec3 p = position + vec3(0.0, a * aF.y, 0.0); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(8.0 * uM * uPx / max(1e-3, -mv.z), 1.5, 14.0); vA = smoothstep(0.0, 0.15, a) * (1.0 - smoothstep(0.6, 1.0, a)); }",
        "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * (1.0 - smoothstep(0.5, 1.0, r)); if (a < 0.01) discard; gl_FragColor = vec4(srgb(cA * (1.1 - 0.3 * r)), a); }",
        { uK: uAgua, cA: { value: cGota.clone() } }, false)), 12);
    }

    // ================= 2. el camino de la gota: del manto a la bolsa y por el conducto hasta el cráter
    const zb = -TC + 4, zt = altoC(c0, c0[0], -WV) - 1.5, ruta = [];
    for (let i = 0; i <= 14; i++) { const f = i / 14, fe = f * f * (3 - 2 * f); ruta.push([UM + (c0[0] - UM) * fe + 14 * Math.sin(f * Math.PI) * Math.sin(ph), ZM + (zb - ZM) * f]); }
    for (let i = 1; i <= 30; i++) { const f = i / 30; ruta.push([c0[0] + 3 * Math.sin(f * 5 + ph), zb + (zt - zb) * f]); }
    const SA = [0]; for (let i = 1; i < ruta.length; i++) SA.push(SA[i - 1] + Math.hypot(ruta[i][0] - ruta[i - 1][0], ruta[i][1] - ruta[i - 1][1]));
    const LT = SA[SA.length - 1], sBolsa = SA[14] / LT;
    const enRuta = (q) => { const s = Math.min(1, Math.max(0, q)) * LT; let i = 1; while (i < SA.length - 1 && SA[i] < s) i++;
      const f = (s - SA[i - 1]) / ((SA[i] - SA[i - 1]) || 1); return [ruta[i - 1][0] + (ruta[i][0] - ruta[i - 1][0]) * f, ruta[i - 1][1] + (ruta[i][1] - ruta[i - 1][1]) * f]; };
    // el hilo encendido (una cinta en la cara del corte; se ve hasta donde llegó la gota)
    const uHead = { value: 0 }, uHilo = { value: 0 };
    { const pos = [], at = [], idx = [], n = ruta.length;
      for (let i = 0; i < n; i++) {
        const a = ruta[Math.max(0, i - 1)], b = ruta[Math.min(n - 1, i + 1)], du = b[0] - a[0], dz = b[1] - a[1], L = Math.hypot(du, dz) || 1;
        const q = SA[i] / LT, w = q < sBolsa ? 7 - 2 * q / sBolsa : 3.2 + 2.6 * (1 - (q - sBolsa) / (1 - sBolsa));
        for (const s of [-1, 1]) { pos.push(...E(ruta[i][0] - dz / L * w * s, -WV - 2.0, ruta[i][1] + du / L * w * s)); at.push(q, s); }
      }
      for (let i = 0; i + 1 < n; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
      poner(new THREE.Mesh(geo(pos, [["aT", at, 2]], idx), material(
        "attribute vec2 aT; varying vec2 vT; void main(){ vT = aT; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        "uniform vec3 cA, cB, cC; uniform float uHead, uK, uT, uNoche; varying vec2 vT; void main(){ float d = uHead - vT.x; if (d < 0.0) discard; float cab = exp(-d * d * 900.0); float borde = 1.0 - smoothstep(0.55, 1.0, abs(vT.y)); float tib = uK * (0.62 + 0.1 * sin(uT * 2.2 - vT.x * 40.0)); float a = max(cab, tib) * (0.35 + 0.65 * borde); if (a < 0.01) discard; vec3 c = mix(mix(cC, cA, tib), cB, cab * 0.8); gl_FragColor = vec4(srgb(c * (1.0 + 0.3 * uNoche)), min(1.0, a)); }",
        { uHead, uK: uHilo, cA: { value: cMagma.clone() }, cB: { value: cLuz.clone() }, cC: { value: cHondo.clone() } }, false, true)), 12);
    }
    // la gota: la cabeza y su cola (puntos; su lugar lo pone dibujar, de t)
    const NG = 7, gpos = new Float32Array(NG * 3), gat = new Float32Array(NG * 2);
    const gota = poner(new THREE.Points(geo(gpos, [["aG", gat, 2]]), material(
      "uniform float uPx, uM; attribute vec2 aG; varying float vA, vK; void main(){ vA = aG.y; vK = aG.x; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp((26.0 - 14.0 * aG.x) * uM * uPx / max(1e-3, -mv.z), 3.0, 60.0); }",
      "uniform vec3 cA, cB; uniform float uNoche; varying float vA, vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vA * exp(-r * r * 2.4); if (a < 0.01) discard; gl_FragColor = vec4(srgb(mix(cA, cB, (1.0 - r) * (1.0 - vK) * 0.85) * (1.05 + 0.3 * uNoche)), min(1.0, a * 1.3)); }",
      { cA: { value: cMagma.clone() }, cB: { value: cLuz.clone() } }, false)), 14);

    // ================= 3. los cráteres: un cuenco que se enciende (el del frente, partido y en el acento) y su halo
    const cpos = [], ccol = [], cat = [], cidx = [], hpos = [], hat = [], NA = 7, NS = 28;
    conos.forEach((c, i) => {
      const t0 = i === 0 ? 0 : -Math.PI, t1 = Math.PI, base = cpos.length / 3, col = i === 0 ? cAcento.clone().lerp(cLuz, 0.25) : cMagma.clone();
      for (let a = 0; a <= NA; a++) {
        const x = 0.002 + 0.3 * a / NA;
        for (let s = 0; s <= NS; s++) {
          const th = t0 + (t1 - t0) * s / NS, u = c[0] + x * c[2] * Math.cos(th), v = Math.max(-WV - 0.4, c[1] + x * c[2] * Math.sin(th));
          cpos.push(...E(u, v, altoC(c, u, v) + 0.7)); ccol.push(col.r, col.g, col.b);
          cat.push(x < RC ? 1 - 0.25 * x / RC : 0.75 * Math.pow(1 - (x - RC) / (0.3 - RC), 2), 0);
        }
      }
      for (let a = 0; a < NA; a++) for (let s = 0; s < NS; s++) { const p = base + a * (NS + 1) + s, q = p + NS + 1; cidx.push(p, q, p + 1, p + 1, q, q + 1); }
      const top = altoC(c, c[0], Math.max(-WV, c[1]));
      hpos.push(...E(c[0], Math.max(-WV + 4, c[1]), top + 0.22 * c[3])); hat.push(c[2] * (i === 0 ? 1.15 : 0.85), 0, i === 0 ? 1 : 0);
    });
    const cK = new Float32Array(cat), crat = poner(new THREE.Mesh(geo(cpos, [["color", ccol, 3], ["aK", cK, 2]], cidx), material(
      "attribute vec3 color; attribute vec2 aK; varying vec3 vC; varying vec2 vK; void main(){ vC = color; vK = aK; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      "uniform vec3 cB; uniform float uNoche; varying vec3 vC; varying vec2 vK; void main(){ float a = vK.x * vK.y; if (a < 0.01) discard; vec3 c = mix(vC, cB, 0.35 * vK.x * vK.y); gl_FragColor = vec4(srgb(c * (1.0 + 0.35 * uNoche)), min(1.0, a * 1.15)); }",
      { cB: { value: cLuz.clone() } }, false, true)), 13);
    const hK = new Float32Array(hat), halo = poner(new THREE.Points(geo(hpos, [["aH", hK, 3]]), material(
      "uniform float uPx, uM; attribute vec3 aH; varying float vA, vF; void main(){ vA = aH.y; vF = aH.z; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(2.0 * aH.x * uM * uPx / max(1e-3, -mv.z), 2.0, 260.0); }",
      "uniform vec3 cA, cB, cC; uniform float uNoche; varying float vA, vF; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vA * exp(-r * r * 3.2) * (0.45 + 0.1 * uNoche); if (a < 0.01) discard; vec3 c = mix(mix(cA, cC, vF), cB, 0.3 * (1.0 - r)); gl_FragColor = vec4(srgb(c), a); }",
      { cA: { value: cMagma.clone() }, cB: { value: cLuz.clone() }, cC: { value: cAcento.clone() } }, false)), 15);

    // el orden en que se encienden los cráteres de la fila (el del frente, siempre primero)
    const rest = []; for (let i = 1; i < NC; i++) rest.push(i);
    const seq = e.orden === "fondo-frente" ? rest.reverse() : rest;
    return { e, objs, uPx, uT, uMan, uAgua, uHead, uHilo, gota, gpos, gat, enRuta, E, crat, cK, NA, NS, halo, hK, seq, NC };
  }

  function dibujar(t, P, ctx) {
    const { e } = P, tr = t - e.t, D = Math.max(0.3, e.dur), x = tr / D;
    const [a1, b0, b1, c0, c1] = FASES[e.fila ? "true" : "false"];
    P.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360)); P.uT.value = tr;
    for (const o of P.objs) o.visible = true;
    // el manto: se enciende en la fase 1 y queda encendido
    P.uMan.value = liso(0, a1, x) * (1 + 0.15 * Math.exp(-Math.pow((x - a1) / 0.08, 2)));
    P.uAgua.value = liso(0, 0.04, x) * (1 - liso(b1 * 0.7, b1, x));
    // la gota: de la cuña al cráter (más lenta en el manto, más rápida en el conducto)
    const g = liso(b0, b1, x), q = g < 0.5 ? 0.9 * g * g * 2 : 1 - (1 - g) * (1 - g) * 2 * 1.1, head = Math.min(1, Math.max(0, x < b0 ? 0 : q));
    P.uHead.value = head <= 0 ? -1 : head;
    P.uHilo.value = liso(b0, b0 + 0.1, x) * (0.75 - 0.25 * liso(c0, c1, x));
    const vis = x > b0 && x < b1 + 0.03 ? 1 - liso(b1 - 0.01, b1 + 0.03, x) : 0;
    for (let i = 0; i < 7; i++) {
      const [u, z] = P.enRuta(head - i * 0.012), w = P.E(u, -WV - 2.6, z);
      P.gpos.set(w, i * 3); P.gat[i * 2] = i / 6; P.gat[i * 2 + 1] = vis * (1 - i / 8);
    }
    P.gota.geometry.attributes.position.needsUpdate = true; P.gota.geometry.attributes.aG.needsUpdate = true;
    P.gota.visible = vis > 0.01;
    // los cráteres: el del frente cuando llega la gota; con fila, los demás uno tras otro; todos quedan encendidos
    const k = new Float32Array(P.NC);
    const flare = (y) => liso(0, 1, y) * (1 + 0.35 * Math.exp(-Math.pow((y - 1.1) / 0.5, 2)));
    k[0] = flare((x - c0) / Math.max(0.02, c1 - c0));
    if (e.fila && P.seq.length) {
      const w = (1 - c1) / P.seq.length;
      P.seq.forEach((ic, j) => { k[ic] = flare((x - (c1 + j * w)) / (1.6 * w)); });
    }
    for (let i = 0; i < P.NC; i++) k[i] *= 0.92 + 0.08 * Math.sin(tr * 2.3 + i * 1.7);
    const per = (P.NA + 1) * (P.NS + 1);
    for (let i = 0; i < P.NC; i++) { for (let j = 0; j < per; j++) P.cK[(i * per + j) * 2 + 1] = k[i]; P.hK[i * 3 + 1] = k[i]; }
    P.crat.geometry.attributes.aK.needsUpdate = true; P.halo.geometry.attributes.aH.needsUpdate = true;
  }
  const clave = (e) => [e.t, e.pieza, e.dur, e.fila, e.orden].map(String).join("|");

  MAQ.EVENTOS.magma = {
    orden: 46,
    armar(ctx, lista) { return { lista, P: lista.map((e, i) => preparar(ctx, e, i)) }; },
    inicio(t, st) { if (!st) return; for (const P of st.P) for (const o of P.objs) o.visible = false; },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      let i = st.lista.indexOf(e); if (i < 0) { const k = clave(e); i = st.P.findIndex((P) => clave(P.e) === k); }
      if (i >= 0) dibujar(t, st.P[i], ctx);
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
