// Pieza «falla» (ficha: falla.json): la traza de una falla. Dormida es una línea fina; al romperse (evento «ruptura»)
// el tramo roto lleva halo + núcleo en el acento y alumbra el suelo (canal uCad/cPieza/uBrillo del shader del relieve).
// Las flechas del corrimiento (evento «deslizar») viven aquí, ocultas hasta que un deslizar las enciende.
// Expone ctx.fallas (las piezas, con .cadena y .simple), ctx.idxFalla(id) y ctx.fallas3d (lo dibujado).
(function (MAQ) {
  MAQ.PIEZAS.falla = {
    orden: 20,
    armar(ctx, FALLAS) {
      const { THREE, lin, COL, CFG, ES, NC, scene, uComun, uRuptura, VERT_CINTA, GLSL_RUPTURA, pegar, geoCinta } = ctx, S = ctx.superficie;
      ctx.fallas = FALLAS;
      ctx.idxFalla = (id) => FALLAS.findIndex((p) => p.id === id);
      S.cPieza.value = [0, 1, 2, 3].map((i) => (FALLAS[i] && FALLAS[i].protagonista ? lin(COL.acento) : lin(COL.secundario).multiplyScalar(CFG.falla.secundaria)));
      // cadenas simplificadas de todas las fallas en un solo arreglo (x, z, s, pieza [+0.5 si después hay un salto])
      { let n = 0;
        FALLAS.forEach((f, ip) => { for (const p of f.simple) { if (n >= NC) break; S.uCad.value[n++].set(p[0], -p[1], p[2], ip + (p[3] ? 0.5 : 0)); } });
        S.uCadN.value = n; }
      const fallas3d = ctx.fallas3d = [];
      FALLAS.forEach((f, ip) => {
        const pts = pegar(f.cadena, 1.0, 0.3), geo = geoCinta(pts);
        const capa = (n, ancho, orden, aditivo, oculta) => {
          const mat = new THREE.ShaderMaterial({
            uniforms: { ...uComun(), ...uRuptura, uAncho: { value: ancho }, uCapa: { value: n }, uPieza: { value: ip }, uBrillo: { value: 1 },
              cAcento: { value: lin(f.protagonista ? COL.acento : COL.secundario) }, cCaliente: { value: lin(COL.caliente) }, cDormida: { value: lin(COL.falla_dormida) }, cBorde: { value: lin(COL.linea) },
              uDormida: { value: CFG.falla.dormida }, uHalo: { value: CFG.falla.halo * (f.protagonista ? 1 : CFG.falla.secundaria) } },
            vertexShader: VERT_CINTA, transparent: true, depthWrite: false, depthTest: oculta,
            blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
            fragmentShader: GLSL_RUPTURA + `uniform int uCapa; uniform float uPieza, uBrillo, uDormida, uHalo; uniform vec3 cAcento, cCaliente, cDormida, cBorde;
              varying float vLado, vS;
              vec3 srgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); }
              void main() {
                float cal; float L = encendida(vS, uPieza, cal); float p = 1.0 - abs(vLado); vec3 c; float a;
                if (uCapa == 0) { a = clamp(uDormida * (1.0 + 1.6 * (uBrillo - 1.0)), 0.0, 1.0) * (1.0 - L) * smoothstep(0.0, 0.5, p); c = cDormida; }
                else if (uCapa == 1) { a = L * pow(p, 2.6) * uHalo * (1.0 + cal * 0.9) * uBrillo; c = cAcento; }
                else if (uCapa == 3) { a = L * smoothstep(0.0, 0.25, p); c = cBorde; }
                else { a = L * smoothstep(0.0, 0.4, p); c = mix(cAcento, cCaliente, clamp(0.04 + 0.6 * cal * cal + 0.25 * (uBrillo - 1.0), 0.0, 0.85)); }
                if (a < 0.003) discard;
                gl_FragColor = vec4(srgb(c), a);
              }` });
          const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m);
          return { mat, base: ancho };
        };
        const o = { f, ip, capas: [capa(0, CFG.falla.dormida_px, 5, false, true)] };
        if (CFG.falla.halo > 0) o.capas.push(capa(1, CFG.falla.halo_px, 6, ES.aditivo, false));
        if (CFG.falla.borde_px) o.capas.push(capa(3, CFG.falla.nucleo_px + CFG.falla.borde_px, 7, false, false));
        o.capas.push(capa(2, CFG.falla.nucleo_px, 8, false, false));
        // flechas del corrimiento (evento «deslizar»): dos carriles de galones, uno a cada lado, en sentidos opuestos
        const mf = new THREE.ShaderMaterial({
          uniforms: { ...uComun(), uAncho: { value: CFG.falla.flechas_px }, cColor: { value: lin(COL.flechas) }, uSentido: { value: 1 },
            uCentro: { value: 0 }, uMedio: { value: 30 }, uPeriodo: { value: 7 }, uFase: { value: 0 }, uAlfa: { value: 0 } },
          vertexShader: VERT_CINTA, transparent: true, depthWrite: false, depthTest: false,
          fragmentShader: `uniform vec3 cColor; uniform float uSentido, uCentro, uMedio, uPeriodo, uFase, uAlfa; varying float vLado, vS;
            void main() {
              float q = (abs(vLado) - 0.6) / 0.34; if (abs(q) > 1.0 || uAlfa <= 0.0) discard;
              float dir = -sign(vLado) * uSentido;                       // corrimiento izquierdo: el lado a la izquierda del trazo va hacia −s (el norte, al oeste)
              float m = dir * (vS - uCentro) / uPeriodo - uFase;
              float galon = 1.0 - smoothstep(0.27, 0.34, fract(m + abs(q) * 0.6));
              float env = 1.0 - smoothstep(uMedio * 0.72, uMedio, abs(vS - uCentro));
              float a = galon * env * uAlfa * (1.0 - smoothstep(0.8, 1.0, abs(q)));
              if (a < 0.003) discard;
              vec3 c = cColor; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a);
            }` });
        const flechas = new THREE.Mesh(geo, mf); flechas.frustumCulled = false; flechas.renderOrder = 9; flechas.visible = false; scene.add(flechas);
        o.flechas = flechas;
        fallas3d.push(o);
      });
      return { fallas3d };
    },
    // resaltar una falla (ctx.cuadro.brillo, que pone el evento «resaltar») la ensancha y la aviva; las líneas engordan al acercarse
    en(t, { fallas3d }, ctx) {
      const { brillo, k } = ctx.cuadro, S = ctx.superficie;
      fallas3d.forEach((o) => { const b = brillo[o.f.id] || 1; S.uBrillo.value[o.ip] = b;
        o.capas.forEach((cp, i) => { cp.mat.uniforms.uAncho.value = cp.base * k * (i === 0 ? 1 + 1.8 * (b - 1) : 1); cp.mat.uniforms.uBrillo.value = b; }); });
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
