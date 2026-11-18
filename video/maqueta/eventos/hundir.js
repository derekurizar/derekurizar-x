// Evento «hundir» (ficha: hundir.json; reglas: scripts/maqueta_tipos/hundir.py): sobre una pieza `subduccion`, la placa
// oceánica avanza y baja. En la cara del corte (v = −WV, un poco delante), dos hileras de CHEVRONES en el acento corren
// por dentro de la placa desde el canto del mar, pasan la fosa y se doblan con ella hacia el manto. Con `agua`, desde el
// primer tercio, el techo de la placa bajo la fila se entibia (una franja tenue, no se derrite) y suelta GOTAS de agua
// que suben a la cuña de manto y se apagan antes de la continental. La placa misma no cambia de color: sigue apagada.
// La geometría es la de la pieza (copia de techo/pend de subduccion.js: si allá cambia, cambia aquí).
// Seek puro: todo sale de t − e.t (ningún estado entre cuadros); el azar fijo es ctx.hash. Sin colores escritos.
(function (MAQ) {
  const L1 = 600, L2 = 1300, WV = 450, D = 600, W0 = 45, DIP = 55, FW = 110, TC = 150, TP = 90, BEND = 150;
  const UC = (L2 - L1) / 2;
  const techo = (u, ta) => u <= 0 ? W0 + DIP * Math.exp(-(u / FW) * (u / FW)) : W0 + DIP + ta * (u - BEND * (1 - Math.exp(-u / BEND)));
  const pend = (u, ta) => u <= 0 ? -2 * DIP * u / (FW * FW) * Math.exp(-(u / FW) * (u / FW)) : ta * (1 - Math.exp(-u / BEND));
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
  const FILAS = [0.3, 0.7];      // dónde corren las hileras (fracción del grueso de la placa)
  const NCH = 8;                 // chevrones por hilera (ilustrativos)
  const VEL = 38;                // m de maqueta por segundo con vel = 1
  const CL = 30, CW = 22, CT = 12;  // largo, medio ancho y grueso del chevrón (m de maqueta)
  const NG = 64;                 // gotas

  const clave = (e) => e.pieza + "|" + e.t + "|" + e.dur;

  MAQ.EVENTOS.hundir = {
    orden: 46,
    armar(ctx, lista) {
      const { THREE, tonos, lin, COL, ES, hash, scene, metros } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1;
      const C = (a, b) => lin(COL[a] || COL[b] || COL.secundario);
      const cAc = tonos.acento.clone(), cBorde = tonos.linea ? tonos.linea.clone() : C("linea", "texto");
      const cGota = C("costa", "secundario").lerp(tonos.agua, 0.2).lerp(C("luces", "acento"), 0.15);
      const cTibio = tonos.mal.clone().lerp(C("luces", "acento"), 0.35);
      const items = {};
      lista.forEach((e, ie) => {
        const K = e.tamano, M = metros(1) * K, ta = e.ta, UA = e.ua;
        const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const y0 = ctx.suelo(e.fx, e.fy) - 0.8 * M;
        const E = (u, v, z) => { const x = e.fx + ((u - UC) * ux - v * uy) * M, y = e.fy + ((u - UC) * uy + v * ux) * M; return [x, y0 + (D + z) * M, -y]; };
        const hz = (i, k) => hash(i + 911 * (ie + 1) + e.semilla * 37, k);
        // ---- el eje de cada hilera: u, z y lo andado (s) desde el canto del mar hasta que toca el fondo del bloque
        const zf = (u, f) => -(techo(u, ta) + TP * f * Math.hypot(1, pend(u, ta)));
        const U = [], S = [];
        for (let u = -L1 + 24, s = 0, zp = null; u <= L2 - 20; u += 4) {
          const z = zf(u, 0.5);
          if (zp !== null) s += Math.hypot(4, z - zp);
          if (-zf(u, FILAS[FILAS.length - 1]) - CW > D - 12) break;
          U.push(u); S.push(s); zp = z;
        }
        const SPAN = S[S.length - 1];
        const uDe = (s) => {
          if (s <= 0) return U[0];
          let a = 0, b = S.length - 1;
          while (b - a > 1) { const m = (a + b) >> 1; if (S[m] < s) a = m; else b = m; }
          const f = (s - S[a]) / ((S[b] - S[a]) || 1); return U[a] + (U[b] - U[a]) * f;
        };
        const vC = -WV - 2.4;
        // ---- los chevrones: 4 triángulos cada uno (dos brazos), posiciones que pone `aplicar`
        const nch = FILAS.length * NCH, gC = new THREE.BufferGeometry();
        gC.setAttribute("position", new THREE.BufferAttribute(new Float32Array(nch * 12 * 3), 3));
        gC.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(nch * 12), 1));
        gC.setAttribute("aB", new THREE.BufferAttribute(new Float32Array(nch * 12), 1));
        const matC = new THREE.ShaderMaterial({
          uniforms: { cA: { value: cAc.clone() }, cB: { value: cBorde.clone() }, uK: { value: oscuro ? 0.95 : 0.9 } },
          transparent: true, depthWrite: false, side: THREE.DoubleSide,
          vertexShader: "attribute float aA, aB; varying float vA, vB; void main(){ vA = aA; vB = aB; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: SRGB + "uniform vec3 cA, cB; uniform float uK; varying float vA, vB; void main(){ if (vA < 0.01) discard; vec3 c = mix(cA, cB, 0.35 * smoothstep(0.75, 1.0, vB)); gl_FragColor = vec4(srgb(c), vA * uK); }" });
        const mC = new THREE.Mesh(gC, matC); mC.frustumCulled = false; mC.renderOrder = 11; scene.add(mC);
        // ---- el techo tibio bajo la fila: una franja a lo largo del techo de la placa
        const u0 = UA - 260, u1 = UA + 60, nW = 60, pw = [], aw = [], iw = [];
        for (let i = 0; i <= nW; i++) {
          const u = u0 + (u1 - u0) * i / nW, h = techo(u, ta), w = Math.sin(Math.PI * i / nW);
          const k = h > TC + 6 ? w * w : 0;
          pw.push(...E(u, vC + 0.6, -h + 2.5), ...E(u, vC + 0.6, -h - 9)); aw.push(k, 0.25 * k);
          if (i < nW) { const a = 2 * i; iw.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
        }
        const gW = new THREE.BufferGeometry();
        gW.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pw), 3));
        gW.setAttribute("aW", new THREE.BufferAttribute(new Float32Array(aw), 1));
        gW.setIndex(iw);
        const matW = new THREE.ShaderMaterial({
          uniforms: { cA: { value: cTibio.clone() }, uOn: { value: 0 }, uNoche: { value: noche ? 1 : 0 } },
          transparent: true, depthWrite: false, side: THREE.DoubleSide,
          vertexShader: "attribute float aW; varying float vW; void main(){ vW = aW; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: SRGB + "uniform vec3 cA; uniform float uOn, uNoche; varying float vW; void main(){ float a = uOn * vW * (0.55 + 0.3 * uNoche); if (a < 0.01) discard; gl_FragColor = vec4(srgb(cA), a); }" });
        const mW = new THREE.Mesh(gW, matW); mW.frustumCulled = false; mW.renderOrder = 10; scene.add(mW);
        // ---- las gotas: salen del techo de la placa bajo la fila y suben a la cuña (un poco hacia la tierra)
        const gp = [], gf = [], gd = [];
        for (let i = 0, k = 0; i < 600 && k < NG; i++) {
          const u = UA - 270 + 300 * hz(i, 1), h = techo(u, ta);
          if (h < TC + 34) continue;
          const sube = (h - TC - 10) * (0.55 + 0.4 * hz(i, 2)), lado = 8 + 18 * hz(i, 3);
          const P0 = E(u, vC - 0.4, -h + 3), P1 = E(u + lado, vC - 0.4, -h + 3 + sube);
          gp.push(...P0); gd.push(P1[0] - P0[0], P1[1] - P0[1], P1[2] - P0[2]);
          gf.push(hz(i, 4), 2.2 + 1.6 * hz(i, 5), 0.8 + 0.5 * hz(i, 6), 0); k++;
        }
        const gG = new THREE.BufferGeometry();
        gG.setAttribute("position", new THREE.BufferAttribute(new Float32Array(gp), 3));
        gG.setAttribute("aF", new THREE.BufferAttribute(new Float32Array(gf), 4));
        gG.setAttribute("aD", new THREE.BufferAttribute(new Float32Array(gd), 3));
        const matG = new THREE.ShaderMaterial({
          uniforms: { uPx: { value: 1 }, uT: { value: 0 }, uOn: { value: 0 }, uM: { value: M }, uNoche: { value: noche ? 1 : 0 },
            cA: { value: cGota.clone() }, cB: { value: cBorde.clone() } },
          transparent: true, depthWrite: false,
          vertexShader: "uniform float uPx, uT, uM, uOn; attribute vec4 aF; attribute vec3 aD; varying float vA; void main(){ float a = fract(uT / aF.y + aF.x); vec3 p = position + aD * a; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uOn > 0.001 ? clamp(11.0 * aF.z * uM * uPx / max(1e-3, -mv.z), 2.0, 22.0) : 0.0; vA = uOn * smoothstep(0.0, 0.14, a) * (1.0 - smoothstep(0.7, 1.0, a)); }",
          fragmentShader: SRGB + "uniform vec3 cA, cB; uniform float uNoche; varying float vA; void main(){ vec2 d = gl_PointCoord - 0.5; d.y *= 0.85; float r = length(d) * 2.0; if (r > 1.0) discard; float a = vA * (0.85 + 0.15 * uNoche) * (1.0 - smoothstep(0.75, 1.0, r)); if (a < 0.01) discard; vec3 c = mix(cA, cB, 0.55 * smoothstep(0.55, 0.85, r) * (1.0 - uNoche)); c = mix(c, cA * 1.25, 0.4 * (1.0 - smoothstep(0.0, 0.35, length(d + vec2(0.12, 0.12)) * 2.0))); gl_FragColor = vec4(srgb(c), a); }" });
        const mG = new THREE.Points(gG, matG); mG.frustumCulled = false; mG.renderOrder = 12; scene.add(mG);
        items[clave(e)] = { E, ta, vC, zf, uDe, SPAN, gC, matW, matG };
      });
      return { items };
    },
    inicio(t, st) {
      if (!st) return;
      for (const k in st.items) {
        const it = st.items[k];
        it.gC.attributes.aA.array.fill(0); it.gC.attributes.aA.needsUpdate = true;
        it.matW.uniforms.uOn.value = 0; it.matG.uniforms.uOn.value = 0;
      }
    },
    aplicar(t, e, ctx, st) {
      if (!st) return;
      const it = st.items[clave(e)];
      if (!it || t < e.t) return;
      const { suave } = ctx, Dd = Math.max(0.3, e.dur), tr = t - e.t, gancho = e.t <= 0.1;
      const env = (gancho ? 1 : suave(0, 0.5, tr)) * (1 - suave(Dd, Dd + 0.6, tr));
      if (env <= 0) return;
      const vel = e.vel || 1;
      // los chevrones: cada uno en su lugar a lo largo de la placa (función de tr)
      const P = it.gC.attributes.position.array, A = it.gC.attributes.aA.array, B = it.gC.attributes.aB.array;
      let n = 0;
      FILAS.forEach((f, fi) => {
        for (let j = 0; j < NCH; j++, n++) {
          const q = (((j + 0.5 * fi) / NCH + (gancho ? 0.25 : 0) + tr * vel * VEL / it.SPAN) % 1 + 1) % 1;
          const s = q * it.SPAN, u = it.uDe(s), z = it.zf(u, f);
          const ua = it.uDe(s - 6), ub = it.uDe(s + 6), za = it.zf(ua, f), zb = it.zf(ub, f);
          const L = Math.hypot(ub - ua, zb - za) || 1, tu = (ub - ua) / L, tz = (zb - za) / L, nu = -tz, nz = tu;
          const pt = (a, b) => [u + tu * a + nu * b, z + tz * a + nz * b];
          const tip = pt(CL / 2, 0), tipI = pt(CL / 2 - CT, 0);
          const up = pt(-CL / 2, CW), upI = pt(-CL / 2 - CT, CW), dn = pt(-CL / 2, -CW), dnI = pt(-CL / 2 - CT, -CW);
          const tris = [tip, up, upI, tip, upI, tipI, tip, tipI, dnI, tip, dnI, dn];
          const al = env * Math.pow(Math.sin(Math.PI * q), 0.6);
          const bo = [0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1];
          tris.forEach(([uu, zz], k) => { P.set(it.E(uu, it.vC, zz), (n * 12 + k) * 3); A[n * 12 + k] = al; B[n * 12 + k] = bo[k]; });
        }
      });
      it.gC.attributes.position.needsUpdate = true; it.gC.attributes.aA.needsUpdate = true; it.gC.attributes.aB.needsUpdate = true;
      // el agua: desde el primer tercio (o desde el cuadro cero si abre el video)
      const a0 = gancho ? 0 : 0.3 * Dd, on = e.agua === false ? 0 : env * (gancho ? 1 : suave(a0, a0 + 0.8, tr));
      it.matW.uniforms.uOn.value = on;
      it.matG.uniforms.uOn.value = on;
      it.matG.uniforms.uT.value = tr * vel + (gancho ? 1.5 : 0);
      it.matG.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
