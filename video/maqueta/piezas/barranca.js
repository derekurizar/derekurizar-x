// Pieza «barranca» (ficha: barranca.json; reglas: scripts/maqueta_tipos/barranca.py): el cauce de una barranca hundido
// en el relieve, de la CUMBRE hacia ABAJO (s crece cuesta abajo). Una malla propia a lo largo de la traza, en km reales:
// un LECHO claro de arena y piedra volcánica (con puntos de roca y vetas de arena que bajan despacio), dos PAREDES que
// suben del lecho a un labio (la profundidad, exagerada como el relieve) sombreadas con la luz del estilo, y dos HOMBROS
// que bajan del labio y se funden con la ladera. El lecho queda sobre el suelo que se ve (nada lo tapa); el labio sube
// sobre él, así el surco se lee de lado y desde arriba. Más angosta y menos honda junto a la cumbre.
// Con un «resaltar» de su id: no se ve antes del primero, se DIBUJA de la cumbre hacia abajo (con una punta que brilla) y
// queda en el acento; sin resaltar, se ve entera en los tonos de la tierra (o en el acento si es la protagonista).
// Seek puro: lo dibujado, la fase de las vetas y el brillo salen de t y de los eventos del maqueta.json.
(function (MAQ) {
  const VEL = 0.18;                                       // periodos de veta por segundo (ilustrativo: la arena no corre)
  // la sección transversal: u (−1 y 1 = el labio), la altura relativa sobre el lecho (0–1) y la zona (0 lecho, 1 pared, 2 hombro)
  const SECCION = [
    [-1.9, 0.0, 2], [-1.45, 0.55, 2], [-1.12, 0.94, 2], [-1.0, 1.0, 1], [-0.86, 0.72, 1], [-0.68, 0.32, 1], [-0.52, 0.06, 0],
    [-0.26, 0.0, 0], [0.0, 0.0, 0], [0.26, 0.0, 0], [0.52, 0.06, 0], [0.68, 0.32, 1], [0.86, 0.72, 1], [1.0, 1.0, 1],
    [1.12, 0.94, 2], [1.45, 0.55, 2], [1.9, 0.0, 2]];
  const VERT = `attribute float aS, aF, aA; attribute vec3 aCol; varying float vS, vF, vA; varying vec3 vCol, vPos;
    void main(){ vS = aS; vF = aF; vA = aA; vCol = aCol; vPos = (modelMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
  const FRAG = `uniform float uDib, uAlfa, uAcento, uCabeza, uBorde, uFase, uPer, uNoche, uBrillo; uniform vec3 cAcento, cRoca, cLuz;
    varying float vS, vF, vA; varying vec3 vCol, vPos;
    void main(){
      if (vS > uDib || uAlfa <= 0.0) discard;
      vec3 c = vCol;
      float roca = step(0.86, ruido(vPos.xz * 55.0)) * vF;                       // piedra volcánica suelta en el lecho
      float grano = ruido2(vPos.xz * 18.0);
      c *= 0.9 + 0.2 * grano;
      c = mix(c, cRoca, roca * 0.75);
      float m = fract(vS / uPer - uFase + 0.15 * sin(vPos.x * 3.0));             // vetas de arena, apenas, cuesta abajo
      c = mix(c, cLuz, vF * 0.12 * smoothstep(0.0, 0.12, m) * (1.0 - smoothstep(0.2, 0.42, m)));
      c = mix(c, cAcento, uAcento * (0.72 * vF + 0.22 * (1.0 - vF)));
      float cab = uCabeza * exp(-pow((uDib - vS) / uBorde, 2.0));
      c = mix(c, cLuz, clamp(cab, 0.0, 1.0) * 0.7 * vF);
      c *= uBrillo;
      vec3 o = niebla(c, vPos, gl_FragCoord.xy);
      o += cAcento * uAcento * vF * 0.22 * uNoche;                                // de noche el lecho resaltado se lee
      float a = vA * uAlfa;
      if (a < 0.003) discard;
      gl_FragColor = vec4(salida(o, gl_FragCoord.xy), a);
    }`;
  const FRAG_HALO = `uniform vec3 cAcento; uniform float uAlfa, uDib, uCabeza, uBorde; varying float vLado, vS;
    void main(){
      if (vS > uDib || uAlfa <= 0.0) discard;
      float q = abs(vLado); if (q > 1.0) discard;
      float cab = uCabeza * exp(-pow((uDib - vS) / uBorde, 2.0));
      float a = pow(1.0 - q, 2.0) * uAlfa * (1.0 + 2.0 * cab);
      if (a < 0.003) discard;
      vec3 c = cAcento; c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));
      gl_FragColor = vec4(c, clamp(a, 0.0, 1.0));
    }`;

  // la cadena [[x, y, s, salto]] densificada cada ≤ paso km: [[x, y, s]]
  function densa(cad, paso) {
    const out = [];
    for (let i = 0; i < cad.length - 1; i++) {
      const a = cad[i], b = cad[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), k = Math.max(1, Math.ceil(L / paso));
      for (let j = 0; j < k; j++) { const u = j / k; out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]); }
    }
    const z = cad[cad.length - 1]; out.push([z[0], z[1], z[2]]);
    return out;
  }

  MAQ.PIEZAS.barranca = {
    orden: 9,
    armar(ctx, piezas) {
      const { THREE, CFG, COL, ES, lin, clamp, scene, suave } = ctx;
      const S = ctx.superficieVista(ctx.altura);
      const EX = ctx.EXAG || 5;
      const lecho = lin(COL.costa).lerp(lin(COL.luz), 0.18);
      const pared = lin(COL.tierra_media).lerp(lin(COL.tierra_alta), 0.35);
      const hombro = lin(COL.tierra_media);
      const roca = lin(COL.tierra_alta).lerp(lin(COL.fondo), 0.55);
      const acento = lin(COL.acento), luz = lin(COL.luz);
      const noche = ES.noche ? 1 : 0, lev = ES.cubos ? 0.06 : 0.035;
      const anchoF = (CFG.frontera && CFG.frontera.ancho) || 1.6;
      return piezas.map((p, i) => {
        const L = p.largo_km, hw = Math.max(0.02, p.ancho_km / 2), H = (p.profundidad_m / 1000) * EX;
        const paso = clamp(L / 260, 0.025, 0.25);
        const D = densa(p.cadena, paso), n = D.length, nc = SECCION.length;
        const pos = [], col = [], aS = [], aF = [], aA = [], idx = [];
        for (let k = 0; k < n; k++) {
          const a = D[Math.max(0, k - 1)], b = D[Math.min(n - 1, k + 1)], ll = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
          const tx = (b[0] - a[0]) / ll, ty = (b[1] - a[1]) / ll, nx = -ty, ny = tx;
          const [x, y, s] = D[k];
          const r = s / Math.max(L, 1e-6);
          const ancho = hw * (0.5 + 0.5 * suave(0, 0.35, r)) * (0.94 + 0.12 * ctx.hash(i, Math.floor(s / 0.4)));   // nace angosta
          const hondo = H * (0.35 + 0.65 * suave(0, 0.3, r)) * (1 - 0.3 * suave(0.85, 1, r));                     // y se abre al pie
          const fin = Math.min(suave(0, 0.03, r) * 0.7 + 0.3, 1);
          for (let j = 0; j < nc; j++) {
            const [u, h, zona] = SECCION[j];
            const px = x + nx * u * ancho, py = y + ny * u * ancho;
            pos.push(px, S(px, py) + lev + h * hondo, -py);
            // la normal de la sección: la pendiente entre las columnas vecinas, en la dirección transversal
            const j0 = Math.max(0, j - 1), j1 = Math.min(nc - 1, j + 1);
            const du = (SECCION[j1][0] - SECCION[j0][0]) * ancho, dh = (SECCION[j1][1] - SECCION[j0][1]) * hondo;
            const g = dh / (du || 1e-6);                                       // sube hacia +u
            let vx = -g * nx, vy = 1, vz = g * ny;                             // three: (x, y arriba, −y)
            const m = Math.hypot(vx, vy, vz); vx /= m; vy /= m; vz /= m;
            const sh = ctx.sombra(vx, vy, vz) / ctx.sombra(0, 1, 0);
            const base = zona === 0 ? lecho : zona === 1 ? pared : hombro;
            const tono = 0.92 + 0.16 * ctx.hash(i * 31 + j, k);
            col.push(base.r * sh * tono, base.g * sh * tono, base.b * sh * tono);
            aS.push(s);
            aF.push(zona === 0 ? 1 : zona === 1 ? 0.25 * (1 - h) : 0);
            aA.push((zona === 2 ? clamp(Math.abs(u) > 1.6 ? 0 : (1.9 - Math.abs(u)) / 0.8, 0, 1) * 0.85 : 1) * fin);
          }
          if (k) for (let j = 0; j < nc - 1; j++) {
            const q = k * nc + j, w = (k - 1) * nc + j;
            idx.push(w, w + 1, q, w + 1, q + 1, q);
          }
        }
        const geo = new THREE.BufferGeometry(), F = (arr, kk) => new THREE.BufferAttribute(new Float32Array(arr), kk);
        geo.setAttribute("position", F(pos, 3)); geo.setAttribute("aCol", F(col, 3));
        geo.setAttribute("aS", F(aS, 1)); geo.setAttribute("aF", F(aF, 1)); geo.setAttribute("aA", F(aA, 1));
        geo.setIndex(pos.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
        const per = clamp(L / 14, 0.25, 1.2) * (0.92 + 0.16 * ctx.hash(i, 7));
        const borde = Math.max(0.2, L * 0.03);
        const mat = new THREE.ShaderMaterial({
          uniforms: { ...ctx.uComun(), uDib: { value: 1e9 }, uAlfa: { value: 1 }, uAcento: { value: 0 }, uCabeza: { value: 0 },
            uBorde: { value: borde }, uFase: { value: 0 }, uPer: { value: per }, uNoche: { value: noche }, uBrillo: { value: 1 },
            cAcento: { value: acento.clone() }, cRoca: { value: roca }, cLuz: { value: luz.clone() } },
          vertexShader: VERT, fragmentShader: ctx.GLSL_COMUN + FRAG, transparent: true, depthWrite: true,
          side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });
        const malla = new THREE.Mesh(geo, mat); malla.frustumCulled = false; malla.renderOrder = 6; scene.add(malla);
        // el halo del acento: una cinta sobre el lecho (ancho en px, el núcleo lo ajusta a la distancia)
        const ph = D.map((q, k) => ({ v: ctx.V3(q[0], q[1], 0), s: q[2], salto: k === n - 1 }));
        for (const q of ph) q.v.y = S(q.v.x, -q.v.z) + lev + 0.02;
        const baseHalo = anchoF * 3.2;
        const halo = new THREE.ShaderMaterial({
          uniforms: { ...ctx.uComun(), uAncho: { value: baseHalo }, cAcento: { value: acento.clone() }, uAlfa: { value: 0 },
            uDib: { value: 1e9 }, uCabeza: { value: 0 }, uBorde: { value: borde } },
          vertexShader: ctx.VERT_CINTA, fragmentShader: FRAG_HALO, transparent: true, depthWrite: false,
          blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending });
        const mh = new THREE.Mesh(ctx.geoCinta(ph), halo); mh.frustumCulled = false; mh.renderOrder = 5; scene.add(mh);
        ctx.registrarCinta(halo, baseHalo, 1);
        const resaltes = ctx.M.eventos.filter((e) => e.tipo === "resaltar" && e.pieza === p.id && e.indice === undefined)
          .sort((a, b) => a.t - b.t);
        return { p, L, mat, halo, resaltes, prota: !!p.protagonista };
      });
    },
    en(t, lista, ctx) {
      const { suave, clamp, ES } = ctx;
      for (const o of lista) {
        const e0 = o.resaltes[0], b = ctx.cuadro.brillo[o.p.id] || 1;
        let dib = 1e9, cab = 0, enAcento = o.prota ? 1 : 0;
        if (e0) {
          const D = clamp(e0.dur * 0.7, 0.8, 2.6), r = suave(e0.t, e0.t + D, t);
          dib = t < e0.t ? -1 : (r >= 1 ? 1e9 : o.L * r);
          cab = t >= e0.t && r < 1 ? 1 - 0.6 * r * r * r * r : 0;
          if (t >= e0.t) enAcento = 1;
        }
        const U = o.mat.uniforms, V = o.halo.uniforms;
        U.uDib.value = dib; U.uCabeza.value = cab; U.uFase.value = t * VEL; U.uAcento.value = enAcento;
        U.uBrillo.value = b > 1 ? 1 + 0.2 * (b - 1) : 1;
        V.uDib.value = dib; V.uCabeza.value = cab;
        V.uAlfa.value = enAcento ? clamp((ES.aditivo ? 0.32 : 0.16) * (1 + 1.6 * (b - 1)), 0, 0.8) : 0;
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
