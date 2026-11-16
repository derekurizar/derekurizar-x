// Pieza «trazo» (ficha: trazo.json): una línea brillante sobre un camino (la de Google Maps sobre una calle), con su
// núcleo y un halo (de noche suma luz). Generaliza «ruta» para ciudad y esquema: aquí la línea se DIBUJA con el tiempo (el
// evento «trazar» deja en ctx.cuadro.trazado[id] hasta qué s se ve; un trazo con algún trazar no se ve antes del primero) y
// se PINTA por tramos (cada «pintar» deja en ctx.cuadro.pintura[id] su tramo [de, frente] y su color; el último manda). Los
// colores bien · medio · mal son del estilo (ctx.tonos); el acento, solo si el trazo es el protagonista. Todo de t: seek puro.
(function (MAQ) {
  const NP = 8;   // tramos pintados que se ven a la vez (los últimos)
  const FRAG = `uniform vec3 cBase; uniform vec4 uP[${NP}]; uniform vec3 uC[${NP}]; uniform float uDib, uAlfa, uHalo, uBorde; varying float vLado, vS;
    void main(){ if (vS > uDib) discard;
      vec3 c = cBase;
      for (int i = 0; i < ${NP}; i++) { if (uP[i].z > 0.5) { float lo = min(uP[i].x, uP[i].y), hi = max(uP[i].x, uP[i].y);
        c = mix(c, uC[i], smoothstep(lo - uBorde, lo + uBorde * 0.3, vS) * (1.0 - smoothstep(hi - uBorde * 0.3, hi + uBorde, vS))); } }
      float e = 1.0 - abs(vLado), a = uHalo > 0.5 ? pow(e, 2.4) * uAlfa : smoothstep(0.0, 0.45, e) * uAlfa;
      a *= 1.0 - 0.5 * smoothstep(uDib - uBorde, uDib, vS);
      c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));
      gl_FragColor = vec4(c, a); }`;
  MAQ.PIEZAS.trazo = {
    orden: 12,
    armar(ctx, piezas) {
      const { THREE, ES, tonos, lin, COL } = ctx;
      const colorDe = (n) => ({ bien: tonos.bien, medio: tonos.medio, mal: tonos.mal, acento: tonos.acento, texto: lin(COL.secundario) }[n] || tonos.bien);
      return piezas.map((p) => {
        const geo = ctx.geoCinta(ctx.pegar(p.puntos, ctx.metros(6), ctx.metros(1.4)));
        const mats = [];
        for (const halo of p.brillo ? [true, false] : [false]) {
          const mat = new THREE.ShaderMaterial({
            uniforms: { ...ctx.uComun(), uAncho: { value: 1 }, cBase: { value: colorDe(p.color).clone() }, uDib: { value: 1e9 },
              uAlfa: { value: halo ? (ES.aditivo ? 0.55 : 0.28) : 1 }, uHalo: { value: halo ? 1 : 0 }, uBorde: { value: ctx.metros(3) },
              uP: { value: Array.from({ length: NP }, () => new THREE.Vector4()) }, uC: { value: Array.from({ length: NP }, () => new THREE.Color()) } },
            vertexShader: ctx.VERT_CINTA, fragmentShader: FRAG, transparent: true, depthWrite: false,
            blending: halo && ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending });
          const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = halo ? 7 : 8; ctx.scene.add(m);
          mats.push({ mat, base: halo ? p.ancho * 4.5 : p.ancho });
        }
        const conTrazar = ctx.M.eventos.some((e) => e.tipo === "trazar" && e.trazo === p.id);
        return { p, mats, conTrazar, colorDe };
      });
    },
    en(t, lista, ctx) {
      const esc = ctx.clamp(1 + 30 / ctx.cuadro.dist_km, 1, 1.8);
      for (const s of lista) {
        const T = (ctx.cuadro.trazado || {})[s.p.id], dib = T === undefined ? (s.conTrazar ? -1 : 1e9) : T;
        const P = ((ctx.cuadro.pintura || {})[s.p.id] || []).slice(-NP), b = ctx.cuadro.brillo[s.p.id];
        for (const { mat, base } of s.mats) {
          const U = mat.uniforms;
          U.uDib.value = dib; U.uAncho.value = base * esc * (b ? 1 + 0.25 * (b - 1) : 1);
          for (let i = 0; i < NP; i++) {
            if (i < P.length) { U.uP.value[i].set(P[i].de, P[i].frente, 1, 0); U.uC.value[i].copy(s.colorDe(P[i].color)); }
            else U.uP.value[i].set(0, 0, 0, 0);
          }
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
