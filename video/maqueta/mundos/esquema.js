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
            // el suelo con textura: manchas grandes y grano fino fijos en el mundo (no es un color plano)
            float tx = (ruido2(vPos.xz * 0.045) - 0.5) * 0.16 + (ruido2(vPos.xz * 0.35 + 7.0) - 0.5) * 0.09 + (ruido(vPos.xz * 2.2) - 0.5) * 0.035;
            vec3 col = mix(cExterior, vCol * (1.0 + tx), smoothstep(-0.6 * uBorde, uBorde, bd));
            gl_FragColor = vec4(salida(niebla(col, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }` });
      const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; scene.add(m);
      // EL HORIZONTE (mundo.horizonte: colinas | montanas | ciudad | mar | llano): relieve y siluetas SOLO más allá del
      // mundo (da profundidad y no mueve nada de lo que está puesto). Determinista por la semilla; se funde con la bruma.
      const MU = ctx.M.mundo, T = x1 - x0, hz = MU.horizonte || { ciudad: "ciudad", plaza: "ciudad", costa: "colinas", campo: "colinas", carretera: "colinas" }[MU.receta] || "colinas";
      if (hz !== "llano" && hz !== "mar") {
        const h = (i, k) => ctx.hash(i + (MU.semilla || 1) * 131, k), ach = malla.nueva(), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
        const verde = tonos.verde.clone().lerp(lin(COL.fondo2), 0.25), lejos = tonos.verde.clone().lerp(lin(COL.fondo2), 0.6), muro = tonos.muro.clone().lerp(lin(COL.fondo2), 0.35);
        // una caja con sus cuatro muros y su techo, sombreada con la luz del estilo
        const caja = (acc, ax, ay, bx, by, al, col) => {
          const cara = (pts, n) => { const k = ctx.sombra(n[0], n[1], n[2]), b = acc.pos.length / 3;
            for (const q of pts) { acc.pos.push(q[0], q[2], -q[1]); acc.col.push(col.r * k, col.g * k, col.b * k); }
            acc.idx.push(b, b + 1, b + 2, b, b + 2, b + 3); };
          cara([[ax, ay, 0], [bx, ay, 0], [bx, ay, al], [ax, ay, al]], [0, 0, 1]); cara([[bx, by, 0], [ax, by, 0], [ax, by, al], [bx, by, al]], [0, 0, -1]);
          cara([[bx, ay, 0], [bx, by, 0], [bx, by, al], [bx, ay, al]], [1, 0, 0]); cara([[ax, by, 0], [ax, ay, 0], [ax, ay, al], [ax, by, al]], [-1, 0, 0]);
          cara([[ax, ay, al], [bx, ay, al], [bx, by, al], [ax, by, al]], [0, 1, 0]); };
        if (hz === "ciudad") {            // un anillo de bloques (el resto de la ciudad): cajas con su techo, más altas a lo lejos
          const N = 150;
          for (let i = 0; i < N; i++) {
            const a = h(i, 1) * Math.PI * 2, r = T * (0.72 + 0.75 * h(i, 2)), w = T * (0.018 + 0.03 * h(i, 3)), d = T * (0.018 + 0.03 * h(i, 4)), al = (10 + 55 * h(i, 5) * h(i, 6)) * (0.6 + r / T * 0.5);
            const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r;
            caja(ach, px - w, py - d, px + w, py + d, ctx.metros(al), muro.clone().lerp(lejos, 0.3 + 0.5 * h(i, 7)));
          }
        } else {                           // colinas o montañas: dos o tres cordones de cerros alrededor (conos anchos de pocas caras)
          const alto = hz === "montanas" ? 0.34 : 0.13, cordones = hz === "montanas" ? 3 : 2;
          for (let c = 0; c < cordones; c++) {
            const N = 16 + 6 * c, R0 = T * (0.95 + 0.55 * c), col = verde.clone().lerp(lejos, 0.35 + 0.3 * c);
            for (let i = 0; i < N; i++) {
              const a = (i + h(i, 11 + c)) / N * Math.PI * 2, r = R0 * (0.92 + 0.2 * h(i, 21 + c)), rad = T * (0.2 + 0.2 * h(i, 31 + c)) * (1 + 0.3 * c), al = T * alto * (0.5 + 0.8 * h(i, 41 + c)) * (1 + 0.5 * c);
              const px = cx + Math.cos(a) * r, py = cy + Math.sin(a) * r, L = 9, base = ach.pos.length / 3;
              ach.pos.push(px, ctx.metros(1) * al, -py); ach.col.push(col.r * 1.08, col.g * 1.08, col.b * 1.08);
              for (let j = 0; j < L; j++) { const b = j / L * Math.PI * 2, rr = rad * (0.8 + 0.4 * h(i * 17 + j, 51 + c)), k = ctx.sombra(Math.cos(b) * 0.7, 0.7, -Math.sin(b) * 0.7);
                ach.pos.push(px + Math.cos(b) * rr, 0, -(py + Math.sin(b) * rr)); ach.col.push(col.r * k, col.g * k, col.b * k); }
              for (let j = 0; j < L; j++) ach.idx.push(base, base + 1 + j, base + 1 + (j + 1) % L);
            }
          }
        }
        if (ach.pos.length) malla.poner(ach, malla.material(), 0);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
