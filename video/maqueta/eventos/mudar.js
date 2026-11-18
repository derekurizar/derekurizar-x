// Evento «mudar» (ficha: mudar.json): lo que se muda de un lugar a otro (una sede, una capital, una institución). Un arco
// de luz en el acento sale de `desde`, sube sobre el relieve (nunca lo toca ni sigue valles: no es un camino) y cae en
// `hacia`, donde se enciende un núcleo con anillos (como «resaltar» un lugar); en `desde` queda una brasa tenue. Con
// `pieza` (una pieza luces) también aviva la luz de `hacia` y deja tenue la de `desde`. Se encadena: el `desde` de un salto
// puede ser el `hacia` del anterior (el núcleo se vuelve brasa cuando sale el siguiente; manda el último en el maqueta.json).
// Seek puro: todo sale de t − e.t; la geometría de cada arco se arma una vez.
(function (MAQ) {
  const N = 96;   // muestras del arco
  const SRGB = "c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c));";
  const ANCHO = 10;   // px del arco (medio ancho) a cualquier distancia: el núcleo lo engorda al acercarse; a 100 km 7 px no se leía (m304)

  function claveDe(e) { return [e.t, e.x0, e.y0, e.x1, e.y1].map((v) => Number(v).toFixed(3)).join("|"); }

  // el arco: base = recta entre los dos extremos (sobre su suelo) + una parábola de alto H que nunca baja del relieve
  function arco(ctx, e) {
    const { THREE } = ctx, alt = (x, y) => ctx.altura(x, y);
    const h0 = alt(e.x0, e.y0) + 0.3, h1 = alt(e.x1, e.y1) + 0.3, M = 1000 / (ctx.unidad_m || 1000);
    let H = Math.max(0.5, (e.altura_km || 12) * M);
    for (let i = 1; i < N; i++) {   // el relieve debajo del arco: si un cerro lo tocaría, el arco sube
      const u = i / N, x = e.x0 + (e.x1 - e.x0) * u, y = e.y0 + (e.y1 - e.y0) * u, p = 4 * u * (1 - u);
      if (p < 0.12) continue;
      const falta = alt(x, y) + 1.2 * M - (h0 + (h1 - h0) * u);
      if (falta > 0) H = Math.max(H, falta / p);
    }
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const u = i / N, x = e.x0 + (e.x1 - e.x0) * u, y = e.y0 + (e.y1 - e.y0) * u;
      pts.push({ v: new THREE.Vector3(x, h0 + (h1 - h0) * u + H * 4 * u * (1 - u), -y), s: u, salto: false });
    }
    return pts;
  }

  MAQ.EVENTOS.mudar = {
    orden: 42,
    armar(ctx, lista) {
      const { THREE, lin, COL, CFG, ES, scene } = ctx;
      const cAc = lin(COL.acento), cNuc = ES.aditivo ? lin(COL.luces).lerp(lin(COL.acento), 0.35) : lin(COL.acento);
      const arcos = lista.map((e) => {
        const pts = arco(ctx, e);
        const mat = new THREE.ShaderMaterial({
          uniforms: { ...ctx.uComun(), uAncho: { value: ANCHO }, cAc: { value: cAc }, cNuc: { value: cNuc }, uIni: { value: 0 }, uFin: { value: 0 }, uAlfa: { value: 0 } },
          vertexShader: ctx.VERT_CINTA, transparent: true, depthWrite: false, depthTest: true,
          blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
          fragmentShader: `uniform vec3 cAc, cNuc; uniform float uIni, uFin, uAlfa; varying float vLado, vS;
            void main(){ if (vS < uIni || vS > uFin) discard;
              float l = abs(vLado), cola = smoothstep(uIni, mix(uIni, uFin, 0.75) + 1e-4, vS);
              float perfil = exp(-l * l * 9.0) + 0.35 * exp(-l * l * 2.4);
              float a = uAlfa * perfil * (0.25 + 0.75 * cola * cola) * (1.0 - smoothstep(0.86, 1.0, l)); if (a < 0.004) discard;
              vec3 c = mix(cAc, cNuc, exp(-l * l * 40.0) * cola); ${SRGB} gl_FragColor = vec4(c, clamp(a, 0.0, 1.0)); }` });
        const m = new THREE.Mesh(ctx.geoCinta(pts), mat); m.frustumCulled = false; m.renderOrder = 10; m.visible = false; scene.add(m);
        if (ctx.registrarCinta) ctx.registrarCinta(mat, ANCHO);   // el núcleo le ajusta el ancho a la distancia (m305)
        return { m, mat, pts, clave: claveDe(e) };
      });
      // los puntos: núcleos, brasas, anillos y la cabeza de cada arco (hasta 3 por evento)
      const NP = Math.max(3, lista.length * 3);
      const g = new THREE.BufferGeometry(), F = (k) => new THREE.BufferAttribute(new Float32Array(NP * k), k);
      g.setAttribute("position", F(3)); for (const a of ["aNuc", "aBrasa", "aAn", "aFase", "aTam"]) g.setAttribute(a, F(1));
      const mp = new THREE.ShaderMaterial({
        uniforms: { cAc: { value: cAc }, cNuc: { value: cNuc }, cBrasa: { value: lin(COL.acento).lerp(lin(COL.luces), 0.25) }, cBorde: { value: lin(COL.linea) },
          uTam: { value: CFG.resalte_px || 320 }, uAditivo: { value: ES.aditivo ? 1 : 0 } },
        transparent: true, depthWrite: false, depthTest: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
        vertexShader: `attribute float aNuc, aBrasa, aAn, aFase, aTam; uniform float uTam; varying float vNuc, vBrasa, vAn, vFase;
          void main(){ vNuc = aNuc; vBrasa = aBrasa; vAn = aAn; vFase = aFase; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            gl_PointSize = (aNuc + aBrasa + aAn) > 0.001 ? uTam * aTam : 0.0; }`,
        fragmentShader: `uniform vec3 cAc, cNuc, cBrasa, cBorde; uniform float uAditivo; varying float vNuc, vBrasa, vAn, vFase;
          float anillo(float r, float ph) { float rr = 0.16 + 0.78 * ph, q = (r - rr) / 0.028; return exp(-q * q) * pow(1.0 - ph, 1.4); }
          void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;
            float nuc = (exp(-r * r * 300.0) * 1.25 + exp(-r * r * 42.0) * 0.7 + exp(-r * r * 9.0) * 0.2) * vNuc;
            float br = (exp(-r * r * 160.0) * 0.85 + exp(-r * r * 26.0) * 0.3) * vBrasa;
            float an = (anillo(r, fract(vFase)) + anillo(r, fract(vFase + 0.5))) * vAn;
            float w = nuc / max(nuc + br, 1e-4);
            vec3 c = uAditivo > 0.5 ? mix(mix(cBrasa, cAc, w), cNuc, clamp(nuc - 0.6, 0.0, 1.0)) : mix(cBorde, mix(cBrasa, cAc, w), clamp((nuc + br) * 1.6, 0.0, 1.0));
            float a = clamp(nuc + br + an * 0.9, 0.0, 1.0) * (1.0 - smoothstep(0.92, 1.0, r)); if (a < 0.003) discard;
            ${SRGB} gl_FragColor = vec4(c, a); }` });
      const puntos = new THREE.Points(g, mp); puntos.frustumCulled = false; puntos.renderOrder = 12; scene.add(puntos);
      return { lista, arcos, puntos, NP, marcas: new Map(), cabezas: [] };
    },
    inicio(t, st) {
      if (!st) return;
      for (const a of st.arcos) a.m.visible = false;
      st.marcas = new Map(); st.cabezas = [];
    },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      const { suave, clamp } = ctx, D = Math.max(0.3, e.dur), tr = t - e.t, queda = e.queda !== false;
      const fin = queda ? 1 : 1 - suave(D, D + 0.6, tr);
      if (fin <= 0) return;
      let ia = st.lista.indexOf(e); if (ia < 0) { const k = claveDe(e); ia = st.arcos.findIndex((a) => a.clave === k); }
      const A = st.arcos[ia];
      const tSale = 0.08 * D, tLlega = 0.8 * D, x = clamp((tr - tSale) / (tLlega - tSale)), s = 0.5 - 0.5 * Math.cos(Math.PI * x);
      // el arco: la cola sigue a la cabeza y, al caer, se recoge en `hacia`
      if (A && tr > tSale && tr < tLlega + 0.3 * D) {
        const rec = clamp((tr - tLlega) / (0.26 * D));
        A.m.visible = true;
        A.mat.uniforms.uFin.value = s;
        A.mat.uniforms.uIni.value = tr < tLlega ? Math.max(0, s - 0.62) : 0.38 + 0.62 * rec;
        A.mat.uniforms.uAlfa.value = 0.95 * suave(tSale, tSale + 0.12 * D, tr) * (1 - 0.6 * rec);
        if (!ctx.registrarCinta) A.mat.uniforms.uAncho.value = ANCHO * clamp(1 + 30 / Math.max(1, ctx.cuadro.dist_km || 100), 1, 1.8);
        if (tr < tLlega + 0.04 * D) {
          const i = Math.min(A.pts.length - 1, Math.round(s * (A.pts.length - 1))), p = A.pts[i].v;
          st.cabezas.push({ p, nuc: 1.15 * suave(tSale, tSale + 0.06 * D, tr) });
        }
      }
      // `desde`: el núcleo se va con el arco y queda una brasa que respira
      const brasa = 0.6 * suave(0.12 * D, 0.55 * D, tr) * (0.84 + 0.16 * Math.sin(t * 2.6 + 6.283 * ctx.hash(ia, 7)));
      st.marcas.set(e.x0.toFixed(3) + "," + e.y0.toFixed(3), { x: e.x0, y: e.y0, nuc: (1 - suave(0.04 * D, 0.5 * D, tr)) * fin, brasa: brasa * fin, an: 0, fase: 0, tam: 0.62 });
      // `hacia`: se enciende al caer (un destello) y queda encendido; los anillos se abren y se apagan
      const llega = suave(tLlega - 0.03 * D, tLlega + 0.1 * D, tr), tl = Math.max(0, tr - tLlega);
      if (llega > 0) {
        const nuc = llega * (1 + 0.55 * Math.exp(-tl * 4)) * (0.93 + 0.07 * Math.cos(tl / 2.4 * 6.283));
        const an = llega * (1 - suave(1.4, 2.6, tl));
        st.marcas.set(e.x1.toFixed(3) + "," + e.y1.toFixed(3), { x: e.x1, y: e.y1, nuc: nuc * fin, brasa: 0, an: an * fin, fase: tl / 1.3, tam: 0.82 });
      }
      // las luces de la pieza: `hacia` se aviva, `desde` queda tenue
      if (e.pieza && ctx.luces) for (const l of ctx.luces) {
        if (l.pieza_id && l.pieza_id !== e.pieza) continue;   // solo las luces de esa pieza (m305)
        if (e.desde_id && l.id === e.desde_id) { const k = suave(0.05 * D, 0.5 * D, tr) * fin; l.v = l.v + (0.3 - l.v) * k; }
        if (e.hacia_id && l.id === e.hacia_id) { const k = llega * fin; l.v = l.v * (1 - k) + (1.5 + 0.8 * Math.exp(-tl * 4)) * k; }
      }
    },
    en(t, st, ctx) {
      if (!st) return;
      const G = st.puntos.geometry.attributes;
      for (const k of ["aNuc", "aBrasa", "aAn"]) G[k].array.fill(0);
      let n = 0;
      const pon = (p, nuc, br, an, fase, tam) => {
        if (n >= st.NP) return;
        G.position.setXYZ(n, p.x, p.y, p.z); G.aNuc.setX(n, nuc); G.aBrasa.setX(n, br); G.aAn.setX(n, an); G.aFase.setX(n, fase); G.aTam.setX(n, tam); n++;
      };
      for (const m of st.marcas.values()) pon(ctx.V3(m.x, m.y, 0.6), m.nuc, m.brasa, m.an, m.fase, m.tam);
      for (const c of st.cabezas) pon(c.p, c.nuc, 0, 0, 0, 0.34);
      for (const k of ["position", "aNuc", "aBrasa", "aAn", "aFase", "aTam"]) G[k].needsUpdate = true;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
