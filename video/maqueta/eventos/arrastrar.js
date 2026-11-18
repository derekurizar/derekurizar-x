// Evento «arrastrar» (ficha: arrastrar.json; reglas: scripts/maqueta_tipos/arrastrar.py): una crecida. Por el cauce de un
// río (de la fuente a la boca) primero baja el agua turbia, la corriente se acelera (estelas claras que corren cada vez más
// rápido) y la basura que había en las orillas se suelta: cientos de pedazos (bolsas, botellas, restos: piezas chicas,
// alargadas, giradas por semilla, en el acento con tonos mezclados) bajan por el cauce y, en la boca, salen sobre el lago y se
// abren en abanico hasta donde las reglas dejaron a cada una (dentro del agua). Con `barda`, una hilera de boyas en arco las
// detiene. Al terminar, la mancha queda flotando (se mece apenas) o, con queda=false, se desvanece.
// Seek puro: todo sale de t − e.t con una velocidad que crece suave (su integral es cerrada) y ctx.hash para el azar.
(function (MAQ) {
  const SRGB = "c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c));";
  const LEV_RIO = 0.32, LEV_LAGO = 0.24;   // sobre la superficie que se ve: la cinta del río va a 0.2, el lago a 0.07–0.12
  const ESTELAS = 34, COLA = 4;             // estelas de la corriente × puntos de cola

  // ∫₀^τ smoothstep(0, a, x) dx: lo que avanza algo cuya velocidad sube suave de 0 a 1 en `a` segundos
  function G(tau, a) {
    if (tau <= 0) return 0;
    if (tau >= a) return a * 0.5 + (tau - a);
    const u = tau / a;
    return a * (u * u * u - 0.5 * u * u * u * u);
  }

  function claveDe(e) { return [e.t, e.boca[0], e.boca[1], e.largo_km].map((v) => Number(v).toFixed(3)).join("|"); }

  function armarUno(ctx, e) {
    const { THREE, lin, COL, ES, hash, scene } = ctx, S = ctx.superficieVista(ctx.altura);
    // el cauce: x, y, la altura que se ve y la distancia acumulada
    const c = e.cauce, nC = c.length / 2, CX = new Float32Array(nC), CY = new Float32Array(nC), CH = new Float32Array(nC), CS = new Float32Array(nC);
    for (let i = 0; i < nC; i++) {
      CX[i] = c[2 * i]; CY[i] = c[2 * i + 1]; CH[i] = S(CX[i], CY[i]);
      CS[i] = i ? CS[i - 1] + Math.hypot(CX[i] - CX[i - 1], CY[i] - CY[i - 1]) : 0;
    }
    const L = CS[nC - 1] || 1;
    const bx = e.boca[0], by = e.boca[1], hB = S(bx, by);
    const NM = e.mancha.length / 2, NB = (e.barda || []).length / 2;
    const TH = new Float32Array(NM);
    for (let i = 0; i < NM; i++) TH[i] = S(e.mancha[2 * i], e.mancha[2 * i + 1]);
    const BH = new Float32Array(NB);
    for (let i = 0; i < NB; i++) BH[i] = S(e.barda[2 * i], e.barda[2 * i + 1]);
    // las capas, en orden de dibujo (sin depthWrite: lo primero queda debajo): velo turbio, estelas, boyas, basura
    const KV = Math.min(140, Math.max(8, Math.round(L / 0.35))), KF = Math.min(160, Math.ceil(NM / 6));
    const o = { velo: 0, fan: KV, est: KV + KF, boya: KV + KF + ESTELAS * COLA, pza: KV + KF + ESTELAS * COLA + NB };
    const NP = o.pza + NM;
    const g = new THREE.BufferGeometry(), F = (k) => new THREE.BufferAttribute(new Float32Array(NP * k), k);
    g.setAttribute("position", F(3));
    for (const a of ["aTam", "aAlfa", "aTono", "aForma", "aRot", "aAsp"]) g.setAttribute(a, F(1));
    const A = g.attributes;
    // lo fijo de cada punto: forma (0 basura · 1 velo · 2 estela · 3 boya), tamaño (km), tono, giro y alargamiento
    for (let i = 0; i < NP; i++) {
      const forma = i >= o.pza ? 0 : i >= o.boya ? 3 : i >= o.est ? 2 : 1;
      A.aForma.setX(i, forma);
      A.aTono.setX(i, hash(i, 11));
      A.aRot.setX(i, 6.2832 * hash(i, 12));
      A.aAsp.setX(i, 1 + 1.6 * hash(i, 13));
      A.aTam.setX(i, forma === 0 ? 0.05 + 0.06 * hash(i, 14) : forma === 1 ? 0.42 + 0.3 * hash(i, 15) : forma === 2 ? 0.055 : 0.045);
    }
    const noche = !!ES.noche;
    const cAc = lin(COL.acento), cCrema = lin(COL.luces);
    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uPx: { value: 1 }, cAc: { value: cAc }, cCrema: { value: cCrema },
        cTierra: { value: lin(COL.tierra_media).lerp(lin(COL.acento), 0.35) },
        cTurbia: { value: lin(COL.tierra_media).lerp(lin(COL.acento), 0.3).lerp(lin(COL.mar), 0.25) },
        cEstela: { value: lin(COL.costa).lerp(lin(COL.luces), 0.5) },
        cBorde: { value: lin(COL.linea) }, uNoche: { value: noche ? 1 : 0 } },
      transparent: true, depthWrite: false, depthTest: true, blending: THREE.NormalBlending,
      vertexShader: `attribute float aTam, aAlfa, aTono, aForma, aRot, aAsp; uniform float uPx;
        varying float vAlfa, vTono, vForma, vRot, vAsp;
        void main(){ vAlfa = aAlfa; vTono = aTono; vForma = aForma; vRot = aRot; vAsp = aAsp;
          vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;
          float px = aTam * uPx / max(0.001, -mv.z);
          float lo = aForma < 0.5 ? 2.6 : aForma < 1.5 ? 5.0 : aForma < 2.5 ? 2.2 : 2.4;
          float hi = aForma < 0.5 ? 15.0 : aForma < 1.5 ? 140.0 : aForma < 2.5 ? 9.0 : 9.0;
          gl_PointSize = aAlfa > 0.003 ? clamp(px, lo, hi) : 0.0; }`,
      fragmentShader: `uniform vec3 cAc, cCrema, cTierra, cTurbia, cEstela, cBorde; uniform float uNoche;
        varying float vAlfa, vTono, vForma, vRot, vAsp;
        void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0; vec3 c; float a;
          if (vForma < 0.5) {                       // un pedazo de basura: un rectángulo redondeado, girado y alargado
            float cs = cos(vRot), sn = sin(vRot); vec2 q = vec2(cs * d.x - sn * d.y, sn * d.x + cs * d.y);
            vec2 h = vec2(0.42, 0.42 / vAsp); vec2 k = abs(q) - h + 0.06;
            float sd = length(max(k, 0.0)) + min(max(k.x, k.y), 0.0) - 0.06;
            a = 1.0 - smoothstep(-0.03, 0.03, sd); if (a < 0.01) discard;
            c = vTono < 0.58 ? cAc : vTono < 0.82 ? mix(cAc, cCrema, 0.5) : cTierra;
            c = mix(c, cBorde, smoothstep(-0.11, -0.02, sd) * (uNoche > 0.5 ? 0.25 : 0.45));   // el borde que lo despega del agua
          } else if (vForma < 1.5) {                // el velo turbio: una mancha blanda
            if (r > 1.0) discard; a = (exp(-r * r * 3.4) - 0.033) * 0.9; c = cTurbia;
          } else if (vForma < 2.5) {                // la estela de la corriente
            if (r > 1.0) discard; a = exp(-r * r * 5.0) * (1.0 - smoothstep(0.85, 1.0, r)); c = cEstela;
          } else {                                  // una boya de la barda: un punto claro con borde
            if (r > 1.0) discard; a = 1.0 - smoothstep(0.78, 1.0, r); c = mix(cCrema, cBorde, smoothstep(0.45, 0.8, r) * 0.6);
          }
          a *= vAlfa; if (a < 0.004) discard;
          ${SRGB} gl_FragColor = vec4(c, clamp(a, 0.0, 1.0)); }` });
    const pts = new THREE.Points(g, mat); pts.frustumCulled = false; pts.renderOrder = 9; pts.visible = false; scene.add(pts);
    return { pts, mat, A, o, NP, NM, NB, KV, KF, CX, CY, CH, CS, L, bx, by, hB, TH, BH, clave: claveDe(e) };
  }

  // en el cauce, a la distancia s (km): x, y, altura y la normal (para correrse a una orilla)
  function enCauce(U, s) {
    const n = U.CS.length; s = Math.max(0, Math.min(U.L, s));
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (U.CS[m] <= s) lo = m; else hi = m; }
    const d = U.CS[hi] - U.CS[lo] || 1, u = (s - U.CS[lo]) / d;
    const dx = U.CX[hi] - U.CX[lo], dy = U.CY[hi] - U.CY[lo], ln = Math.hypot(dx, dy) || 1;
    return { x: U.CX[lo] + dx * u, y: U.CY[lo] + dy * u, h: U.CH[lo] + (U.CH[hi] - U.CH[lo]) * u, nx: -dy / ln, ny: dx / ln };
  }

  MAQ.EVENTOS.arrastrar = {
    orden: 40,
    armar(ctx, lista) {
      return { lista, uno: lista.map((e) => armarUno(ctx, e)) };
    },
    inicio(t, st) { if (st) for (const U of st.uno) U.pts.visible = false; },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      let k = st.lista.indexOf(e); if (k < 0) { const c = claveDe(e); k = st.uno.findIndex((u) => u.clave === c); }
      const U = st.uno[k]; if (!U) return;
      const { suave, clamp, hash } = ctx, D = Math.max(0.6, e.dur), tr = t - e.t, I = clamp(e.intensidad == null ? 0.7 : e.intensidad);
      const fin = e.queda !== false ? 1 : 1 - suave(D, D + 0.8, tr);
      if (fin <= 0) return;
      U.pts.visible = true;
      U.mat.uniforms.uPx.value = ctx.cuadro ? ctx.cuadro.pxKm : 1;
      const A = U.A, o = U.o, L = U.L, a = 0.25 * D;
      const k0 = L / G(0.62 * D, a);              // km/s del cauce a toda velocidad: la primera llega a la boca en 0.62·D
      const Gt = G(tr, a), Gmax = G(0.7 * D, a);
      const on = suave(0.02 * D, 0.2 * D, tr);
      // 1) el velo turbio del cauce: el frente de la crecida baja (llega a la boca en 0.45·D) y luego aclara un poco
      const sF = L * Gt / G(0.45 * D, a), aclara = 1 - 0.45 * suave(D, D + 1.5, tr);
      for (let j = 0; j < U.KV; j++) {
        const s = L * (j + 0.5) / U.KV, p = enCauce(U, s), lado = (hash(j, 21) - 0.5) * 0.16;
        A.position.setXYZ(o.velo + j, p.x + p.nx * lado, p.h + LEV_RIO - 0.04, -(p.y + p.ny * lado));
        A.aAlfa.setX(o.velo + j, (0.16 + 0.22 * I) * clamp((sF - s) / 1.2) * aclara * fin);
      }
      // 2) el velo del abanico: sale de la boca con la basura y queda debajo de la mancha
      const Gb = Math.max(0, Gt - G(0.42 * D, a)) * k0;
      for (let j = 0; j < U.KF; j++) {
        const m = Math.min(U.NM - 1, Math.floor(j * U.NM / U.KF)), tx = e.mancha[2 * m], ty = e.mancha[2 * m + 1];
        const dist = Math.max(0.2, Math.hypot(tx - U.bx, ty - U.by)), f = 1 - Math.exp(-Gb * 0.3 / dist);
        A.position.setXYZ(o.fan + j, U.bx + (tx - U.bx) * f, U.hB + (U.TH[m] - U.hB) * f + LEV_LAGO - 0.05, -(U.by + (ty - U.by) * f));
        A.aAlfa.setX(o.fan + j, (0.14 + 0.2 * I) * suave(0, 0.25, f) * (1 - 0.3 * suave(D, D + 1.5, tr)) * fin);
      }
      // 3) las estelas: la corriente se acelera (su avance es la integral de una velocidad que sube suave)
      const vEst = k0 * (0.75 + 0.5 * I), apaga = 1 - suave(D, D + 1.2, tr);
      for (let j = 0; j < ESTELAS; j++) {
        const s0 = L * hash(j, 31), lado = (hash(j, 32) - 0.5) * 0.09;
        const sh = ((s0 + vEst * Gt + 0.35 * tr) % L + L) % L;
        const borde = Math.pow(Math.sin(Math.PI * clamp(sh / L)), 0.4);
        const rapido = suave(0, a, tr);
        for (let q = 0; q < COLA; q++) {
          const p = enCauce(U, sh - q * (0.08 + 0.22 * rapido)), i = o.est + j * COLA + q;
          A.position.setXYZ(i, p.x + p.nx * lado, p.h + LEV_RIO + 0.02, -(p.y + p.ny * lado));
          A.aAlfa.setX(i, (0.5 + 0.35 * I) * on * apaga * borde * (1 - q / COLA) * (0.35 + 0.65 * rapido) * fin);
        }
      }
      // 4) la barda: las boyas aparecen al empezar y se mecen apenas
      for (let j = 0; j < U.NB; j++) {
        const x = e.barda[2 * j], y = e.barda[2 * j + 1];
        A.position.setXYZ(o.boya + j, x, U.BH[j] + LEV_LAGO + 0.03 * Math.sin(t * 1.7 + 6.283 * hash(j, 41)), -y);
        A.aAlfa.setX(o.boya + j, 0.95 * suave(0, 0.15 * D, tr) * fin);
      }
      // 5) la basura: aparece en su orilla, la corriente la suelta, baja por el cauce y en la boca se abre en abanico
      for (let i = 0; i < U.NM; i++) {
        const h1 = hash(i, 51), h2 = hash(i, 52), h3 = hash(i, 53), h4 = hash(i, 54);
        const s0 = L * 0.92 * Math.pow(h1, 0.75);
        const gmax = Math.max(0, Gmax - (L - s0) / k0), gi = 0.92 * h2 * gmax;
        const nace = suave(0.04 * D + 0.18 * D * h3, 0.1 * D + 0.18 * D * h3, tr);
        const s = s0 + k0 * Math.max(0, Gt - gi);
        let x, y, h;
        if (s <= L) {
          const p = enCauce(U, s), lado = (h4 - 0.5) * 0.11;
          x = p.x + p.nx * lado; y = p.y + p.ny * lado; h = p.h + LEV_RIO + 0.03;
        } else {
          const tx = e.mancha[2 * i], ty = e.mancha[2 * i + 1], dx = tx - U.bx, dy = ty - U.by;
          const dist = Math.max(0.15, Math.hypot(dx, dy)), f = 1 - Math.exp(-(s - L) * 0.3 / dist);
          const curva = Math.sin(Math.PI * f) * 0.14 * dist * (h4 - 0.5) * 2, nx = -dy / dist, ny = dx / dist;
          const meca = suave(0.6, 1, f) * 0.025;                       // flota: se mece apenas, sin irse
          x = U.bx + dx * f + nx * curva + meca * Math.sin(t * 0.7 + 6.283 * h2);
          y = U.by + dy * f + ny * curva + meca * Math.cos(t * 0.55 + 6.283 * h3);
          h = U.hB + (U.TH[i] - U.hB) * f + (s - L < 0.4 ? LEV_RIO : LEV_LAGO) + 0.01 * Math.sin(t * 1.3 + 6.283 * h1);
        }
        A.position.setXYZ(o.pza + i, x, h, -y);
        A.aAlfa.setX(o.pza + i, (0.75 + 0.25 * hash(i, 55)) * nace * fin);
        A.aRot.setX(o.pza + i, 6.2832 * hash(i, 12) + 0.25 * Math.sin(t * 0.8 + 6.283 * h3));
      }
      for (const n of ["position", "aAlfa", "aRot"]) A[n].needsUpdate = true;
      // la pieza del río (el afluente) se aviva mientras baja la crecida
      if (e.pieza && ctx.cuadro) {
        const b = 1 + 0.35 * on * (1 - 0.6 * suave(D, D + 1.5, tr)) * fin;
        ctx.cuadro.brillo[e.pieza] = Math.max(ctx.cuadro.brillo[e.pieza] || 0, b);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
