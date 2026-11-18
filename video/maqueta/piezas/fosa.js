// Pieza «fosa» (ficha: fosa.json; reglas: scripts/maqueta_tipos/fosa.py): la fosa oceánica mar adentro, en esquema.
// Un valle ancho y oscuro sobre el fondo del mar (el mar hondo del estilo), con una línea rayada encima (o continua si
// `esquematica` es false); la protagonista en el acento y con un halo. «resaltar» la aviva por su id (ctx.linea).
// Con `flechas`: carriles de galones que avanzan hacia la fosa, la cruzan y se hunden bajo la costa (se apagan y bajan
// bajo el relieve). Seek puro: la fase de los galones es función de t.
(function (MAQ) {
  const PERIODO_KM = 22, VEL = 0.45;       // galones: separación (km) y periodos por segundo (ilustrativo, no una velocidad)
  MAQ.PIEZAS.fosa = {
    orden: 12,
    armar(ctx, piezas) {
      const { THREE, CFG, COL, lin, pegar, cinta, geoCinta, V3, uComun, VERT_CINTA, scene, EXAG } = ctx;
      const lista = [];
      for (const p of piezas) {
        const pts = pegar(p.cadena, 2.0, 0.25), prota = !!p.protagonista;
        const o = { p, halo: null, flechas: [] };
        cinta(pts, COL.mar_hondo, 18, 0.7, 3);                                   // el valle submarino
        cinta(pts, COL.linea, 7, 0.22, 4);                                       // sus bordes, apenas
        if (prota) o.halo = cinta(pts, COL.acento, 12, 0.22, 5, { oculta: false });
        const nucleo = cinta(pts, prota ? COL.acento : COL.secundario, prota ? 3.4 : 2.6, prota ? 1 : 0.85, 6,
          p.esquematica ? { raya: (CFG.ruta && CFG.ruta.raya_km) || 6 } : {});
        ctx.linea(p.id, nucleo);
        // flechas de convergencia: una cinta por carril, que baja bajo el relieve pasado el cruce (s > 0)
        const hunde = 0.035 * (EXAG || 5);
        for (const car of p.carriles || []) {
          const pc = [];
          for (let i = 0; i < car.length; i++) {
            const a = car[i], b = car[i + 1];
            const k = b ? Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 2)) : 1;
            for (let j = 0; j < (b ? k : 1); j++) {
              const u = j / k, x = b ? a[0] + (b[0] - a[0]) * u : a[0], y = b ? a[1] + (b[1] - a[1]) * u : a[1];
              const s = b ? a[2] + (b[2] - a[2]) * u : a[2];
              pc.push({ v: V3(x, y, 0.35 - hunde * Math.max(0, s)), s, salto: !b });
            }
          }
          const mat = new THREE.ShaderMaterial({
            uniforms: { ...uComun(), uAncho: { value: CFG.falla.flechas_px * 0.6 }, cColor: { value: lin(COL.flechas) },
              uFase: { value: 0 }, uPeriodo: { value: PERIODO_KM }, uFin: { value: p.adentro_km }, uAlfa: { value: 0.85 } },
            vertexShader: VERT_CINTA, transparent: true, depthWrite: false, depthTest: true,
            fragmentShader: `uniform vec3 cColor; uniform float uFase, uPeriodo, uFin, uAlfa; varying float vLado, vS;
              void main() {
                float q = abs(vLado); if (q > 1.0 || uAlfa <= 0.0) discard;
                float m = vS / uPeriodo - uFase;
                float galon = 1.0 - smoothstep(0.22, 0.30, fract(m + q * 0.45));
                float ini = smoothstep(-150.0, -110.0, vS);
                float fin = 1.0 - smoothstep(-0.15 * uFin, uFin, vS);
                float a = galon * ini * fin * uAlfa * (1.0 - smoothstep(0.75, 1.0, q));
                if (a < 0.003) discard;
                vec3 c = cColor; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a);
              }` });
          const m = new THREE.Mesh(geoCinta(pc), mat); m.frustumCulled = false; m.renderOrder = 7; scene.add(m);
          o.flechas.push({ mat, base: CFG.falla.flechas_px * 0.6 });
        }
        lista.push(o);
      }
      return { lista };
    },
    en(t, { lista }, ctx) {
      const { brillo, k } = ctx.cuadro;
      for (const o of lista) {
        const b = brillo[o.p.id] || 1;
        if (o.halo) o.halo.mat.uniforms.uAlfa.value = Math.min(1, 0.22 * (1 + 2.2 * (b - 1)));
        for (const f of o.flechas) {
          f.mat.uniforms.uAncho.value = f.base * k;
          f.mat.uniforms.uFase.value = t * VEL;
          f.mat.uniforms.uAlfa.value = Math.min(1, 0.85 * (1 + 0.4 * (b - 1)));
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
