// Evento «cumbres» (ficha: cumbres.json; reglas: scripts/maqueta_tipos/cumbres.py): sobre una pieza volcanes, los cráteres
// se encienden uno tras otro (en el orden de la lista, o de oeste a este, o de este a oeste) y quedan encendidos. Cada boca
// es un punto de luz sobre la cumbre (su `top`, el mismo de volcanes.py): un núcleo en la boca, un halo ancho que baña la
// cima, un aro fino que la ciñe y, al encenderse, un destello y un anillo que se abre una vez. En el acento si la pieza es
// la protagonista; en crema (la luz del estilo) si no. Sin humo ni lava: solo luz. Seek puro: todo sale de t − e.t.
(function (MAQ) {
  const SRGB = "c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c));";
  const LEV = 0.08;   // la luz flota apenas sobre la boca (unidades de la escena)

  MAQ.EVENTOS.cumbres = {
    orden: 44,
    armar(ctx, lista) {
      const { THREE, lin, COL, CFG, ES, scene } = ctx;
      const NP = Math.max(1, lista.reduce((s, e) => s + (e.cumbres || []).length, 0));
      const g = new THREE.BufferGeometry(), F = (k) => new THREE.BufferAttribute(new Float32Array(NP * k), k);
      g.setAttribute("position", F(3));
      for (const a of ["aNuc", "aHalo", "aAn", "aFase", "aTam", "aProta"]) g.setAttribute(a, F(1));
      const mat = new THREE.ShaderMaterial({
        uniforms: { cAc: { value: lin(COL.acento) }, cCrema: { value: lin(COL.luces) }, cBorde: { value: lin(COL.linea) },
          uTam: { value: CFG.resalte_px || 320 }, uAditivo: { value: ES.aditivo ? 1 : 0 } },
        transparent: true, depthWrite: false, depthTest: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
        vertexShader: `attribute float aNuc, aHalo, aAn, aFase, aTam, aProta; uniform float uTam; varying float vNuc, vHalo, vAn, vFase, vProta;
          void main(){ vNuc = aNuc; vHalo = aHalo; vAn = aAn; vFase = aFase; vProta = aProta;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            gl_PointSize = (aNuc + aHalo + aAn) > 0.001 ? uTam * aTam : 0.0; }`,
        fragmentShader: `uniform vec3 cAc, cCrema, cBorde; uniform float uAditivo; varying float vNuc, vHalo, vAn, vFase, vProta;
          void main(){ vec2 d = gl_PointCoord - 0.5; d.y *= 1.35;            // un poco achatado: la boca se ve desde arriba en escorzo
            float r = length(d) * 2.0; if (r > 1.0) discard;
            float nuc = (exp(-r * r * 420.0) * 1.3 + exp(-r * r * 90.0) * 0.75) * vNuc;
            float halo = (exp(-r * r * 14.0) * 0.42 + exp(-r * r * 4.0) * 0.14) * vHalo;
            float q = (r - 0.2) / 0.022, aro = exp(-q * q) * 0.55 * vHalo;     // el aro fino que ciñe la boca
            float ph = fract(vFase), rr = 0.2 + 0.74 * ph, q2 = (r - rr) / 0.03;
            float an = exp(-q2 * q2) * pow(1.0 - ph, 1.5) * vAn;               // el anillo del encendido, una vez
            vec3 base = mix(cCrema, cAc, vProta), cal = mix(base, cCrema, 0.55);
            vec3 c = mix(base, cal, clamp(nuc - 0.5, 0.0, 1.0));
            if (uAditivo < 0.5) c = mix(cBorde, c, clamp((nuc + halo + aro + an) * 1.8, 0.0, 1.0));
            float a = clamp(nuc + halo + aro + an * 0.9, 0.0, 1.0) * (1.0 - smoothstep(0.9, 1.0, r)); if (a < 0.003) discard;
            ${SRGB} gl_FragColor = vec4(c, a); }` });
      const puntos = new THREE.Points(g, mat); puntos.frustumCulled = false; puntos.renderOrder = 12; scene.add(puntos);
      return { lista, puntos, NP, luces: [] };
    },
    inicio(t, st) { if (st) st.luces = []; },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t || !e.cumbres || !e.cumbres.length) return;
      const { suave, clamp } = ctx, D = Math.max(0.3, e.dur), tr = t - e.t, n = e.cumbres.length;
      const fin = e.queda !== false ? 1 : 1 - suave(D, D + 0.6, tr);
      if (fin <= 0) return;
      const w = clamp(0.9 * D / n, 0.12, 0.55);                   // lo que tarda en prender cada boca
      e.cumbres.forEach((c, k) => {
        const s = n > 1 ? 0.78 * D * k / (n - 1) : 0, ign = suave(s, s + w, tr);
        if (ign <= 0) return;
        const tl = Math.max(0, tr - s - w), flash = 1 + 0.7 * Math.exp(-tl * 3.5);
        const resp = 0.9 + 0.1 * Math.sin(t * 2.2 + 6.283 * ctx.hash(c[0], 3));   // la boca respira, sin humo
        st.luces.push({ x: c[1], y: c[2], top: c[3], nuc: ign * flash * resp * fin, halo: ign * (0.85 + 0.15 * resp) * fin,
          an: ign * (1 - suave(0.7, 1.0, (tr - s) / 1.3)) * fin, fase: Math.min(0.999, (tr - s) / 1.3), prota: e.prota ? 1 : 0 });
      });
    },
    en(t, st, ctx) {
      if (!st) return;
      const G = st.puntos.geometry.attributes;
      for (const k of ["aNuc", "aHalo", "aAn"]) G[k].array.fill(0);
      const zoom = ctx.clamp(110 / Math.max(1, ctx.cuadro.dist_km || 110), 0.6, 1.3);
      let i = 0;
      for (const l of st.luces) {
        if (i >= st.NP) break;
        G.position.setXYZ(i, l.x, l.top + LEV, -l.y);
        G.aNuc.setX(i, l.nuc); G.aHalo.setX(i, l.halo); G.aAn.setX(i, l.an); G.aFase.setX(i, l.fase);
        G.aTam.setX(i, 0.55 * zoom); G.aProta.setX(i, l.prota); i++;
      }
      for (const k of ["position", "aNuc", "aHalo", "aAn", "aFase", "aTam", "aProta"]) G[k].needsUpdate = true;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
