// Evento «ruptura» (ficha: ruptura.json): una falla se rompe desde un punto (s0) hacia los dos lados, cada frente a su
// ritmo, y los dos llegan en `dur`. Llena el canal uRup/uRupT (lo dibujan el relieve y las cintas de la falla) y dibuja
// la cabeza de cada frente (un destello). Tope: ctx.NR rupturas (las primeras del maqueta.json; el gate lo exige).
(function (MAQ) {
  MAQ.EVENTOS.ruptura = {
    orden: 30,
    armar(ctx) {
      const { THREE, lin, COL, CFG, ES, NR, scene } = ctx;
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NR * 2 * 3), 3));
      g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(NR * 2), 1)); g.setAttribute("aAc", new THREE.BufferAttribute(new Float32Array(NR * 2), 1));
      const m = new THREE.ShaderMaterial({ uniforms: { cAcento: { value: lin(COL.acento) }, cSec: { value: lin(COL.secundario) }, cCaliente: { value: lin(COL.caliente) }, uTam: { value: CFG.falla.cabeza_px } },
        transparent: true, depthWrite: false, depthTest: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
        vertexShader: "attribute float aK, aAc; uniform float uTam; varying float vK, vAc; void main(){ vK = aK; vAc = aAc; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_PointSize = uTam * (0.6 + 0.4 * aK); }",
        fragmentShader: `uniform vec3 cAcento, cSec, cCaliente; varying float vK, vAc;
          void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; float a = (exp(-r * r * 7.0) * 0.9 + exp(-r * r * 60.0)) * vK * (1.0 - smoothstep(0.85, 1.0, r)); if (a < 0.003) discard;
            vec3 c = mix(mix(cSec, cAcento, vAc), cCaliente, exp(-r * r * 30.0) * 0.8); c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }` });
      const cabezas = new THREE.Points(g, m); cabezas.frustumCulled = false; cabezas.renderOrder = 10; scene.add(cabezas);
      return { cabezas, n: 0 };
    },
    inicio(t, st) { st.cabezas.geometry.attributes.aK.array.fill(0); st.n = 0; },
    aplicar(t, e, ctx, st) {
      if (t > e.t) ctx.cuadro.rupturas.push(e);
      const i = st.n++;
      if (i >= ctx.NR) return;
      const { uRuptura, suave, clamp, V3 } = ctx, A = st.cabezas.geometry.attributes;
      const tr = t - e.t, ip = ctx.idxFalla(e.pieza), u = clamp(tr / e.dur);
      uRuptura.uRup.value[i].set(e.s0, e.km_menos, e.km_mas, e.dur); uRuptura.uRupT.value[i].set(Math.max(0, tr), ip);
      if (tr > 0 && tr < e.dur + 0.5) {
        const f = ctx.fallas[ip], cad = f.cadena, fin = suave(e.dur + 0.5, e.dur - 0.1, tr), ini = suave(0, 0.15, tr);
        [[-1, e.km_menos], [1, e.km_mas]].forEach(([sg, alc], j) => {
          if (alc <= 0) return;
          const s = e.s0 + sg * alc * u, [x, y] = ctx.puntoEnS(cad, s), p = V3(x, y, 0.4);
          A.position.setXYZ(2 * i + j, p.x, p.y, p.z); A.aK.setX(2 * i + j, ini * fin); A.aAc.setX(2 * i + j, f.protagonista ? 1 : 0);
        });
      }
    },
    en(t, st, ctx) {
      for (let i = Math.min(st.n, ctx.NR); i < ctx.NR; i++) ctx.uRuptura.uRupT.value[i].set(0, -1);
      const A = st.cabezas.geometry.attributes;
      A.position.needsUpdate = true; A.aK.needsUpdate = true; A.aAc.needsUpdate = true;
      st.cabezas.material.uniforms.uTam.value = ctx.CFG.falla.cabeza_px * ctx.cuadro.k;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
