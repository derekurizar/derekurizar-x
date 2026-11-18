// Pieza «coberturaceldas» (ficha: coberturaceldas.json; reglas: scripts/maqueta_tipos/coberturaceldas.py): una serie anual
// de cobertura por celdas dentro del contorno de un área. El contorno va como línea fina sobre el relieve; dentro, una celda
// plana pegada al suelo que se ve por cada celda del archivo, que brilla en el tono (acento o verde) según su cobertura del
// año base. El año corre de `anio` a `anio_fin` entre `corre_desde` y `corre_hasta` (en escalones de un año): al llegar el
// año de una pérdida, esa parte de la celda se apaga hasta un tono oscuro tenue, con un destello breve.
// «resaltar» por su id: las celdas brillan más y el contorno se engruesa. Sin texto: el año va en la capa 2D.
// Seek puro: el año, lo apagado y el destello salen de t (cada cuadro se recalcula entero, nada se acumula).
(function (MAQ) {
  const FRAG = `uniform vec3 cTono, cOsc, cNada, cLuz; uniform float uBr, uAlfa;
    varying vec3 vPos; varying vec3 vEst; varying vec2 vUV; varying float vVar;
    void main(){
      float q = max(abs(vUV.x), abs(vUV.y));
      float v = vEst.x, w = vEst.y, d = vEst.z;               // bosque que queda · lo perdido · destello
      vec3 c = cTono * v * (0.88 + 0.24 * vVar) * uBr + cOsc * w + cNada * max(0.0, 1.0 - v - w);
      c /= max(1e-3, v * (0.88 + 0.24 * vVar) * uBr + w + max(0.0, 1.0 - v - w)) ;
      c = mix(c, cTono * 1.15, 0.25 * smoothstep(0.55, 0.95, v) * (1.0 - q));   // un núcleo más vivo en las celdas llenas
      c *= 1.0 - 0.38 * smoothstep(0.8, 0.97, q);                              // el marco de cada celda
      c = mix(c, cLuz, clamp(d, 0.0, 1.0) * 0.7);
      float a = uAlfa * (0.3 + 0.62 * clamp(v * uBr, 0.0, 1.2) + 0.45 * w) + 0.4 * d;
      if (a < 0.003) discard;
      gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), clamp(a, 0.0, 1.0));
    }`;
  const VERT = `attribute vec3 aEst; attribute vec2 aUV; attribute float aVar;
    varying vec3 vPos; varying vec3 vEst; varying vec2 vUV; varying float vVar;
    void main(){ vEst = aEst; vUV = aUV; vVar = aVar; vPos = (modelMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

  // el año (continuo) en t, y el segundo en que llegó el año entero Y
  function anioEn(p, t) {
    if (p.anio_fin == null) return p.anio;
    const u = Math.min(1, Math.max(0, (t - p.corre_desde) / (p.corre_hasta - p.corre_desde)));
    return p.anio + (p.anio_fin - p.anio) * u;
  }
  const llegada = (p, Y) => p.anio_fin == null ? -1e9 : p.corre_desde + (Y - p.anio) / (p.anio_fin - p.anio) * (p.corre_hasta - p.corre_desde);

  MAQ.PIEZAS.coberturaceldas = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, CFG, COL, ES, lin, clamp, scene } = ctx;
      const S = ctx.sueloVisto, claro = ES.modo === 1 || ES.modo === 4;
      const lev = ES.cubos ? 0.32 : 0.09;
      return piezas.map((p, ip) => {
        const [hx, hy] = p.medio, gap = 0.9;                 // la celda ocupa el 90 %: entre celda y celda se ve el suelo
        const n = clamp(Math.ceil(Math.max(hx, hy) * 2 / 1.2), 1, 4), nv = (n + 1) * (n + 1);
        const N = p.celdas.length;
        const pos = new Float32Array(N * nv * 3), uv = new Float32Array(N * nv * 2), est = new Float32Array(N * nv * 3), va = new Float32Array(N * nv);
        const idx = [];
        p.celdas.forEach((c, i) => {
          const o = i * nv, vr = ctx.hash(i, 7 + ip);
          for (let b = 0; b <= n; b++) for (let a = 0; a <= n; a++) {
            const k = o + b * (n + 1) + a, u = -1 + 2 * a / n, v = -1 + 2 * b / n;
            const x = c[0] + u * hx * gap, y = c[1] + v * hy * gap;
            pos[3 * k] = x; pos[3 * k + 1] = S(x, y) + lev; pos[3 * k + 2] = -y;
            uv[2 * k] = u; uv[2 * k + 1] = v; va[k] = vr; est[3 * k] = c[2];
          }
          for (let b = 0; b < n; b++) for (let a = 0; a < n; a++) {
            const k = o + b * (n + 1) + a;
            idx.push(k, k + 1, k + n + 1, k + 1, k + n + 2, k + n + 1);
          }
        });
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
        g.setAttribute("aUV", new THREE.BufferAttribute(uv, 2));
        g.setAttribute("aVar", new THREE.BufferAttribute(va, 1));
        const aEst = new THREE.BufferAttribute(est, 3); aEst.setUsage(THREE.DynamicDrawUsage); g.setAttribute("aEst", aEst);
        g.setIndex(N * nv > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
        const tono = p.protagonista || p.tono !== "verde" ? lin(COL.acento) : ctx.tonos.bien.clone();
        const suelo = claro ? lin(COL.exterior) : lin(COL.tierra_baja);
        const osc = suelo.clone().multiplyScalar(0.35).lerp(tono, p.apagado);   // lo perdido: oscuro tenue con un dejo del tono
        const nada = suelo.clone().multiplyScalar(0.5);
        const mat = new THREE.ShaderMaterial({
          uniforms: { ...ctx.uComun(), cTono: { value: tono }, cOsc: { value: osc }, cNada: { value: nada },
            cLuz: { value: lin(COL.luz || COL.secundario) }, uBr: { value: 1 }, uAlfa: { value: ES.aditivo ? 0.95 : 0.9 } },
          vertexShader: VERT, fragmentShader: ctx.GLSL_COMUN + FRAG, transparent: true, depthWrite: false,
          polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4,
          blending: THREE.NormalBlending });
        const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = 2; scene.add(m);
        // el contorno: una cinta fina pegada al suelo que se ve (resaltar la aviva y la engruesa)
        const pts = ctx.pegar(p.contorno, 0.4, lev);
        for (const q of pts) q.v.y = S(q.v.x, -q.v.z) + lev + 0.06;
        const anchoF = (CFG.frontera && CFG.frontera.ancho) || 1.6, base = anchoF * 0.55 * p.grosor;
        const cn = ctx.cinta(pts, claro ? lin(COL.costa).lerp(lin(COL.luz || COL.costa), 0.3) : lin(COL.linea), base, 1, 3);
        ctx.linea(p.id, cn);
        // para cada celda, lo perdido acumulado año por año (índice k → fracción)
        const K = p.anios.length;
        const cel = p.celdas.map((c) => { const fr = new Float32Array(K); for (const [k, f] of c[3]) fr[k] = f; return { f0: c[2], fr }; });
        return { p, mat, aEst, cel, nv, cn, base, K };
      });
    },
    en(t, lista, ctx) {
      const { clamp, suave } = ctx;
      for (const o of lista) {
        const p = o.p, b = ctx.cuadro.brillo[p.id] || 1;
        o.mat.uniforms.uBr.value = 1 + 0.55 * (b - 1);
        o.cn.base = o.base * (1 + 1.1 * (b - 1));
        const y = anioEn(p, t), Y = Math.floor(y + 1e-6);
        const paso = p.anio_fin == null ? 1 : (p.corre_hasta - p.corre_desde) / (p.anio_fin - p.anio);
        const fade = clamp(paso * 0.6, 0.12, 0.45), tau = clamp(paso * 0.35, 0.05, 0.28);
        // por año k: cuánto pesa ya (0 → 1 al llegar) y su destello
        const peso = new Float32Array(o.K), dest = new Float32Array(o.K);
        for (let k = 0; k < o.K; k++) {
          const A = p.anios[k];
          if (A > Y) continue;
          const tl = llegada(p, A), dt = t - tl;
          if (A <= p.anio || dt >= fade + 1.2) { peso[k] = 1; continue; }   // ya estaba perdido al empezar, o hace rato
          peso[k] = suave(0, fade, dt);
          dest[k] = p.destello ? Math.exp(-dt / tau) * suave(-0.01, 0.04, dt) : 0;
        }
        const E = o.aEst.array, nv = o.nv;
        for (let i = 0; i < o.cel.length; i++) {
          const c = o.cel[i]; let w = 0, d = 0;
          for (let k = 0; k < o.K; k++) { const f = c.fr[k]; if (f && peso[k]) { w += f * peso[k]; d = Math.max(d, dest[k] * clamp(f * 10, 0.15, 1)); } }
          const v = Math.max(0, c.f0 - w), j0 = i * nv * 3;
          for (let j = 0; j < nv; j++) { E[j0 + 3 * j] = v; E[j0 + 3 * j + 1] = w; E[j0 + 3 * j + 2] = d; }
        }
        o.aEst.needsUpdate = true;
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
