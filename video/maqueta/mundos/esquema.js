// Mundo «esquema» (ficha: esquema.json): un lugar GENÉRICO hecho por una receta (ciudad, carretera, campo, costa, plaza),
// determinista por su semilla y sin archivos. La receta la calcula scripts/maqueta_tipos/esquema.py UNA vez (así los gates
// y el motor ven lo mismo) y llega en MAQUETA.mundo: sus suelos (arena, campos, pavimento) los pinta este módulo; sus
// calles, edificios, agua, zonas y la carretera son PIEZAS. En METROS, con el centro del mundo en (0, 0); el suelo es plano
// (altura 0) y su orilla se funde con el plano exterior. No afirma geografía: el pie lleva «Esquema» (M3D12).
// Publica en ctx: altura(x, y) = 0 y geo = null (un esquema no tiene lon/lat). Sus caminos y lugares con nombre (ctx.caminos,
// ctx.lugares) ya vienen resueltos en MAQUETA.mundo.
(function (MAQ) {
  MAQ.MUNDOS.esquema = {
    async cargar(ctx) {
      Object.assign(ctx, { altura: () => 0, geo: null, km: null });
      return {};
    },
    armar(ctx) {
      const { THREE, lin, COL, scene, tonos, malla, uComun, GLSL_COMUN } = ctx;
      const [x0, y0, x1, y1] = ctx.caja, mg = 0.12 * (x1 - x0);
      // el suelo: una placa algo mayor que la caja (su orilla se funde con el plano exterior) y los suelos de la receta encima
      const acc = malla.nueva();
      malla.poligono(acc, [x0 - mg, y0 - mg, x1 + mg, y0 - mg, x1 + mg, y1 + mg, x0 - mg, y1 + mg], 0, tonos.suelo);
      const suelos = ctx.M.mundo.suelos || [];
      suelos.forEach((s, k) => malla.poligono(acc, s.puntos.flat(), 0.04 + 0.002 * k, tonos[s.clase] || tonos.pavimento));
      const mat = new THREE.ShaderMaterial({ uniforms: { ...uComun(), cExterior: { value: lin(COL.exterior) }, uCaja: { value: new THREE.Vector4(x0, x1, -y1, -y0) }, uBorde: { value: 0.1 * (x1 - x0) } },
        side: THREE.DoubleSide,
        vertexShader: "attribute vec3 color; varying vec3 vCol, vPos; void main(){ vCol = color; vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        fragmentShader: GLSL_COMUN + `uniform vec3 cExterior; uniform vec4 uCaja; uniform float uBorde; varying vec3 vCol, vPos;
          void main(){ float bd = min(min(vPos.x - uCaja.x, uCaja.y - vPos.x), min(vPos.z - uCaja.z, uCaja.w - vPos.z));
            vec3 col = mix(cExterior, vCol, smoothstep(-0.6 * uBorde, uBorde, bd));
            gl_FragColor = vec4(salida(niebla(col, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }` });
      const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; scene.add(m);
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
