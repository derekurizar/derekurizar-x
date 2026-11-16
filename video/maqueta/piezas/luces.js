// Pieza «luces» (ficha: luces.json): un punto de luz por lugar (los pueblos). Su intensidad la mueven los eventos
// encender, apagar, parpadear y resaltar (un lugar), en el orden del maqueta.json, sobre ctx.luces[i].v; la onda las
// aviva al pasar. Todas las piezas «luces» van en un solo dibujo (los puntos se cuentan juntos: hash por índice).
(function (MAQ) {
  MAQ.PIEZAS.luces = {
    orden: 50,
    armar(ctx, LUCES) {
      const { THREE, lin, COL, CFG, ES, V3, scene } = ctx;
      const LZ = ctx.luces = [];   // {x, y, peso, pieza, id, on, ac, v}
      LUCES.forEach((p, ip) => p.puntos.forEach((q) => LZ.push({ x: q[0], y: q[1], peso: q[2], id: q[3], pieza: ip, on: p.encendidas !== false, ac: p.protagonista ? 1 : 0 })));
      if (!LZ.length) return null;
      const pos = new Float32Array(LZ.length * 3), peso = new Float32Array(LZ.length), acs = new Float32Array(LZ.length);
      LZ.forEach((l, i) => { const v = V3(l.x, l.y, 0.35); pos.set([v.x, v.y, v.z], 3 * i); peso[i] = l.peso; acs[i] = l.ac; });
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aPeso", new THREE.BufferAttribute(peso, 1));
      g.setAttribute("aInt", new THREE.BufferAttribute(new Float32Array(LZ.length), 1)); g.setAttribute("aAc", new THREE.BufferAttribute(acs, 1));
      const m = new THREE.ShaderMaterial({
        uniforms: { cLuz: { value: lin(COL.luces) }, cAcento: { value: lin(COL.acento) }, cBorde: { value: lin(COL.linea) }, uEsc: { value: 1 }, uKm: { value: CFG.luces.km }, uMin: { value: CFG.luces.min_px }, uMax: { value: CFG.luces.max_px },
          uAditivo: { value: ES.aditivo ? 1 : 0 }, uFuerza: { value: CFG.luces.fuerza } },
        transparent: true, depthWrite: false, depthTest: true, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
        vertexShader: `attribute float aPeso, aInt, aAc; uniform float uEsc, uKm, uMin, uMax; varying float vInt, vAc;
          void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; vInt = aInt; vAc = aAc;
            gl_PointSize = aInt <= 0.001 ? 0.0 : clamp(uKm * (0.45 + 0.75 * aPeso) * uEsc / max(-mv.z, 1.0), uMin, uMax) * (1.0 + 0.18 * max(aInt - 1.0, 0.0)); }`,
        fragmentShader: `uniform vec3 cLuz, cAcento, cBorde; uniform float uAditivo, uFuerza; varying float vInt, vAc;
          vec3 srgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); }
          void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;
            if (uAditivo > 0.5) { float a = (exp(-r * r * 4.0) * 0.5 + exp(-r * r * 34.0) * 1.0) * min(vInt, 2.6) * uFuerza * (1.0 - smoothstep(0.8, 1.0, r)); gl_FragColor = vec4(srgb(mix(cLuz, cAcento, vAc)), a); }
            else { float a = (1.0 - smoothstep(0.42, 0.5, r)) * min(vInt, 1.0); vec3 c = mix(mix(cLuz, cAcento, vAc), cBorde, smoothstep(0.26, 0.32, r)); if (a < 0.01) discard; gl_FragColor = vec4(srgb(c), a); } }` });
      const luces = new THREE.Points(g, m); luces.frustumCulled = false; luces.renderOrder = 4; scene.add(luces);
      return { luces };
    },
    inicio(t, estado, ctx) { for (const l of ctx.luces) l.v = l.on ? 1 : 0; },
    en(t, estado, ctx) {
      if (!estado) return;
      const { luces } = estado, A = luces.geometry.attributes.aInt, FALLAS = ctx.fallas;
      ctx.luces.forEach((l, i) => {
        let v = l.v;
        for (const o of ctx.cuadro.ondas) { const d = o.pieza < 0 ? Math.hypot(l.x - o.x, l.y - o.y) : ctx.distCadena(FALLAS[o.pieza].cadena, l.x, l.y), w = 5 + o.r * 0.05;
          v *= 1 + 1.5 * Math.exp(-Math.pow((d - o.r) / w, 2)) * Math.min(1, o.k * 2); }
        A.array[i] = v;
      });
      A.needsUpdate = true; luces.material.uniforms.uEsc.value = ctx.cuadro.pxKm;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
