// Evento «resaltar» (ficha: resaltar.json): llama la atención sobre una PIEZA (sube su brillo con un pulso:
// ctx.cuadro.brillo[id], que leen la falla y las líneas) o sobre un LUGAR (un punto con anillos que se abren, y si el
// lugar es una luz, la aviva). Hasta 6 lugares resaltados a la vez.
(function (MAQ) {
  const NRES = 6;
  MAQ.EVENTOS.resaltar = {
    orden: 40,
    armar(ctx) {
      const { THREE, lin, COL, CFG, ES, scene } = ctx;
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NRES * 3), 3));
      g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(NRES), 1)); g.setAttribute("aFase", new THREE.BufferAttribute(new Float32Array(NRES), 1));
      const m = new THREE.ShaderMaterial({ uniforms: { cSec: { value: lin(COL.secundario) }, cLuz: { value: lin(COL.luces) }, cBorde: { value: lin(COL.linea) }, uTam: { value: CFG.resalte_px }, uAditivo: { value: ES.aditivo ? 1 : 0 } },
        transparent: true, depthWrite: false, depthTest: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
        vertexShader: "attribute float aK, aFase; uniform float uTam; varying float vK, vFase; void main(){ vK = aK; vFase = aFase; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_PointSize = aK > 0.0 ? uTam : 0.0; }",
        fragmentShader: `uniform vec3 cSec, cLuz, cBorde; uniform float uAditivo; varying float vK, vFase;
          float anillo(float r, float ph) { float rr = 0.14 + 0.8 * ph, q = (r - rr) / 0.03; return exp(-q * q) * pow(1.0 - ph, 1.3); }
          void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;
            float nucleo = exp(-r * r * 260.0) * 1.2 + exp(-r * r * 38.0) * 0.75 + exp(-r * r * 9.0) * 0.22;
            float an = anillo(r, fract(vFase)) + anillo(r, fract(vFase + 0.5));
            vec3 c = uAditivo > 0.5 ? cSec : mix(cBorde, cLuz, clamp(nucleo, 0.0, 1.0));
            float a = clamp((nucleo + an * 0.95) * vK, 0.0, 1.0) * (1.0 - smoothstep(0.92, 1.0, r)); if (a < 0.003) discard;
            c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }` });
      const resaltes = new THREE.Points(g, m); resaltes.frustumCulled = false; resaltes.renderOrder = 11; scene.add(resaltes);
      return { resaltes, n: 0 };
    },
    inicio(t, st) { st.resaltes.geometry.attributes.aK.array.fill(0); st.n = 0; },
    aplicar(t, e, ctx, st) {
      if (!(t >= e.t && t <= e.t + e.dur)) return;
      const tr = t - e.t, { suave } = ctx;
      if (e.pieza) ctx.cuadro.brillo[e.pieza] = 1 + 0.9 * suave(0, 0.3, tr) * suave(e.dur, e.dur - 0.4, tr) * (0.8 + 0.2 * Math.cos(tr / 1.2 * Math.PI * 2));
      if (e.pieza === undefined && st.n < NRES) {
        const A = st.resaltes.geometry.attributes, p = ctx.V3(e.x, e.y, 0.5);
        A.position.setXYZ(st.n, p.x, p.y, p.z); A.aFase.setX(st.n, tr / 1.25); A.aK.setX(st.n, suave(0, 0.25, tr) * suave(e.dur, e.dur - 0.4, tr)); st.n++;
      }
      if (e.lugar) for (const l of ctx.luces) if (l.id === e.lugar) l.v = Math.max(l.v, 1) + 1.2;
    },
    en(t, st) { const A = st.resaltes.geometry.attributes; A.position.needsUpdate = A.aK.needsUpdate = A.aFase.needsUpdate = true; },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
