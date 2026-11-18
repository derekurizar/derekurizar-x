// Pieza «lagos» (ficha: lagos.json): los lagos y las lagunas grandes del set (OpenStreetMap), superficies posadas sobre el
// relieve en el color del agua del estilo, con su orilla en línea fina y un brillo que deriva muy despacio (puro de t).
// La pieza protagonista lleva la orilla en el acento; «resaltar» aclara el agua y sube la orilla por su id (ctx.linea).
(function (MAQ) {
  // La altura de lo que se VE. mundos/pais.js arma la malla del relieve con una celda de cada dos (y, en voxel, columnas de
  // 6 × 6 celdas): un cauce angosto cae entre dos vértices y con ctx.altura quedaría debajo de la malla. Aquí se calcula
  // esa misma superficie con ctx.altura en los centros de celda (allí es exacta).
  const suelo = (ctx) => ctx.superficieVista(ctx.altura);   // la malla que se ve (motor.js, m305)
  // un polígono [x0, y0, …] → triángulos de lados ≤ `max` (km), sin costuras: cada lado largo se parte por su punto medio
  // (la regla es del LADO, no del triángulo: los dos triángulos que lo comparten lo parten igual)
  function teselar(THREE, flat, max) {
    const pts = []; for (let i = 0; i + 1 < flat.length; i += 2) pts.push(new THREE.Vector2(flat[i], flat[i + 1]));
    if (pts.length < 3) return [];
    if (THREE.ShapeUtils.isClockWise(pts)) pts.reverse();
    let tris = THREE.ShapeUtils.triangulateShape(pts, []).map((t) => t.map((i) => [pts[i].x, pts[i].y]));
    const largo = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]) > max, medio = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    for (let vuelta = 0; vuelta < 9; vuelta++) {
      const out = []; let partio = false;
      for (const [a, b, c] of tris) {
        const ab = largo(a, b), bc = largo(b, c), ca = largo(c, a), n = ab + bc + ca;
        if (!n) { out.push([a, b, c]); continue; }
        partio = true;
        const mab = ab && medio(a, b), mbc = bc && medio(b, c), mca = ca && medio(c, a);
        if (n === 3) out.push([a, mab, mca], [mab, b, mbc], [mca, mbc, c], [mab, mbc, mca]);
        else if (n === 2) { if (!ab) out.push([a, b, mbc], [a, mbc, mca], [mca, mbc, c]); else if (!bc) out.push([a, mab, mca], [mab, b, c], [mab, c, mca]); else out.push([a, mab, c], [mab, mbc, c], [mab, b, mbc]); }
        else if (ab) out.push([a, mab, c], [mab, b, c]); else if (bc) out.push([a, b, mbc], [a, mbc, c]); else out.push([a, b, mca], [mca, b, c]);
      }
      tris = out; if (!partio) break;
    }
    return tris;
  }
  MAQ.PIEZAS.lagos = {
    orden: 6,
    armar(ctx, piezas) {
      const { THREE, CFG, COL, ES, lin, cinta } = ctx, S = suelo(ctx);
      const claro = ES.modo === 1 || ES.modo === 4;           // noche y plano: la orilla es el hilo claro de la costa
      const agua = lin(ES.modo === 4 ? COL.mar_hondo : COL.mar), reflejo = lin(COL.costa);
      const lev = ES.cubos ? 0.12 : 0.07;
      return piezas.map((p) => {
        const pos = [], idx = [], visto = new Map(), orillas = [];
        const vert = (q) => { const k = q[0] + "," + q[1]; let i = visto.get(k);
          if (i === undefined) { i = pos.length / 3; pos.push(q[0], S(q[0], q[1]) + lev, -q[1]); visto.set(k, i); } return i; };
        for (const an of p.anillos) for (const t of teselar(THREE, an, 0.75)) idx.push(vert(t[0]), vert(t[1]), vert(t[2]));
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
        g.setIndex(pos.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
        const mat = new THREE.ShaderMaterial({
          uniforms: { ...ctx.uComun(), uLagoT: { value: 0 }, uBrillo: { value: 1 }, cAgua: { value: agua }, cReflejo: { value: reflejo }, uReflejo: { value: claro ? 0.2 : 0.3 } },
          side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4,
          vertexShader: "varying vec3 vPos; void main(){ vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: ctx.GLSL_COMUN + `uniform float uLagoT, uBrillo, uReflejo; uniform vec3 cAgua, cReflejo; varying vec3 vPos;
            void main(){   // el brillo: una franja ancha de reflejo cada ≈ 23 km, apenas ondulada, que deriva muy despacio
              float onda = 0.9 * sin(vPos.x * 0.07 - vPos.z * 0.11 + uLagoT * 0.05);
              float r = smoothstep(0.5, 1.0, sin(vPos.x * 0.24 + vPos.z * 0.13 + uLagoT * 0.2 + onda));
              vec3 c = mix(cAgua, cReflejo, r * uReflejo) * uBrillo;
              gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }` });
        const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = 0; ctx.scene.add(m);
        if (p.orilla || p.protagonista) {                     // la orilla: una sola cinta con un salto entre lago y lago
          const cad = []; let s = 0;
          for (const an of p.anillos) { const n = an.length / 2;
            for (let i = 0; i <= n; i++) { const x = an[2 * (i % n)], y = an[2 * (i % n) + 1]; if (i) s += Math.hypot(x - cad[cad.length - 1][0], y - cad[cad.length - 1][1]); cad.push([x, y, s, i === n ? 1 : 0]); }
            s += 1; }
          const pts = ctx.pegar(cad, 0.75, lev);
          for (const q of pts) q.v.y = S(q.v.x, -q.v.z) + lev + 0.05;
          const ancho = CFG.frontera.ancho * (p.protagonista ? 1.1 : claro ? 0.7 : 0.5);
          ctx.linea(p.id, p.protagonista ? cinta(pts, COL.acento, ancho, 1, 1)
            : cinta(pts, claro ? lin(COL.costa) : lin(COL.mar_hondo).lerp(lin(COL.linea), 0.25), ancho, claro ? 0.75 : 0.7, 1));
        }
        return { id: p.id, mat };
      });
    },
    en(t, lista, ctx) {
      for (const e of lista) { const b = ctx.cuadro.brillo[e.id]; e.mat.uniforms.uLagoT.value = t; e.mat.uniforms.uBrillo.value = b ? 1 + 0.35 * (b - 1) : 1; }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
