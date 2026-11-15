// Mundo «ciudad» (ficha: ciudad.json): un lugar real de pocos km de un set de escala ciudad (design/sets3d/<set>/), en
// METROS: x = (lon − lon0)·m_lon (este), y = (lat − lat0)·m_lat (norte). El suelo es el relieve a zoom alto (relieve.png,
// el mismo códec que el del país) con su punto más bajo en 0 (base_m) y exagerado `exageracion` veces, teñido con el suelo
// del estilo y la luz de su ficha; su orilla se funde con el plano exterior. Las calles, los edificios, el agua y las zonas
// son PIEZAS (calles, edificios, agua, zona, carretera), no el mundo.
// Publica en ctx: altura(x, y) (m, ya exagerada) y geo(lon, lat) → [x, y] en metros (también como ctx.km).
(function (MAQ) {
  MAQ.MUNDOS.ciudad = {
    async cargar(ctx) {
      const MU = ctx.M.mundo, R = MU.relieve, P = R.proyeccion, EX = MU.exageracion, CJ = R.caja;
      const RW = R.ancho, RH = R.alto;
      const X0 = (CJ.lon_min - P.lon0) * P.m_lon, X1 = (CJ.lon_max - P.lon0) * P.m_lon;
      const Y0 = (CJ.lat_min - P.lat0) * P.m_lat, Y1 = (CJ.lat_max - P.lat0) * P.m_lat;
      const CX = (X1 - X0) / RW, CY = (Y1 - Y0) / RH;            // metros por celda
      const img = new Image(); img.src = "assets/set/" + R.archivo; await img.decode();
      const c = document.createElement("canvas"); c.width = RW; c.height = RH;
      const g = c.getContext("2d", { willReadFrequently: true, colorSpace: "srgb" });
      g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, RW, RH).data, ALT = new Float32Array(RW * RH);
      for (let i = 0; i < RW * RH; i++) ALT[i] = d[4 * i] * 256 + d[4 * i + 1] - R.desfase_m;
      for (const [i, j, v] of R.muestras) if (ALT[j * RW + i] !== v) console.error("relieve: la imagen se leyó con conversión de color (muestra " + i + "," + j + ")");
      const { clamp } = ctx;
      function altura(x, y) {          // la misma cuenta que scripts/maqueta_tipos/ciudad.py → suelo
        const fi = clamp((x - X0) / CX - 0.5, 0, RW - 1.001), fj = clamp((Y1 - y) / CY - 0.5, 0, RH - 1.001);
        const i = Math.floor(fi), j = Math.floor(fj), u = fi - i, v = fj - j, k = j * RW + i;
        const h = (ALT[k] * (1 - u) + ALT[k + 1] * u) * (1 - v) + (ALT[k + RW] * (1 - u) + ALT[k + RW + 1] * u) * v;
        return Math.max(0, h - R.base_m) * EX;
      }
      const geo = (lon, lat) => [(lon - P.lon0) * P.m_lon, (lat - P.lat0) * P.m_lat];
      Object.assign(ctx, { altura, geo, km: geo });
      return { ALT, RW, RH, X0, X1, Y0, Y1, CX, CY, EX, base: R.base_m };
    },
    armar(ctx, st) {
      const { THREE, lin, COL, scene, tonos, sombra, uComun, GLSL_COMUN } = ctx;
      const { ALT, RW, RH, X0, Y1, CX, CY, EX, base } = st;
      const pos = new Float32Array(RW * RH * 3), col = new Float32Array(RW * RH * 3), c = new THREE.Color();
      const h = (i, j) => Math.max(0, ALT[clampI(j, RH) * RW + clampI(i, RW)] - base) * EX;
      function clampI(v, n) { return v < 0 ? 0 : v >= n ? n - 1 : v; }
      for (let j = 0; j < RH; j++) for (let i = 0; i < RW; i++) {
        const k = j * RW + i, x = X0 + (i + 0.5) * CX, y = Y1 - (j + 0.5) * CY;
        pos[3 * k] = x; pos[3 * k + 1] = h(i, j); pos[3 * k + 2] = -y;
        // normal por diferencias finitas (three: y arriba, z = −norte); la luz del suelo, suave
        const dx = (h(i + 1, j) - h(i - 1, j)) / (2 * CX), dn = (h(i, j - 1) - h(i, j + 1)) / (2 * CY), L = Math.hypot(dx, 1, dn);
        const k2 = 0.55 + 0.45 * sombra(-dx / L, 1 / L, dn / L) / 1.12;
        c.copy(tonos.suelo).multiplyScalar(k2);
        col[3 * k] = c.r; col[3 * k + 1] = c.g; col[3 * k + 2] = c.b;
      }
      const idx = new Uint32Array((RW - 1) * (RH - 1) * 6); let q = 0;
      for (let j = 0; j < RH - 1; j++) for (let i = 0; i < RW - 1; i++) { const a = j * RW + i, b = a + 1, c2 = a + RW, d = c2 + 1; idx[q++] = a; idx[q++] = c2; idx[q++] = b; idx[q++] = b; idx[q++] = c2; idx[q++] = d; }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3)); geo.setAttribute("color", new THREE.BufferAttribute(col, 3)); geo.setIndex(new THREE.BufferAttribute(idx, 1));
      const [x0, y0, x1, y1] = ctx.caja;
      const mat = new THREE.ShaderMaterial({ uniforms: { ...uComun(), cExterior: { value: lin(COL.exterior) }, uCaja: { value: new THREE.Vector4(x0, x1, -y1, -y0) }, uBorde: { value: 350 } },
        vertexShader: "attribute vec3 color; varying vec3 vCol, vPos; void main(){ vCol = color; vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        fragmentShader: GLSL_COMUN + `uniform vec3 cExterior; uniform vec4 uCaja; uniform float uBorde; varying vec3 vCol, vPos;
          void main(){ float bd = min(min(vPos.x - uCaja.x, uCaja.y - vPos.x), min(vPos.z - uCaja.z, uCaja.w - vPos.z));
            vec3 col = mix(cExterior, vCol, smoothstep(0.0, uBorde, bd));
            gl_FragColor = vec4(salida(niebla(col, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }` });
      const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; scene.add(m);
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
