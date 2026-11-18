// Evento «florecer» (ficha: florecer.json; reglas: scripts/maqueta_tipos/florecer.py): sobre un lago de una pieza `lagos`
// aparecen manchas verde vivo (un florecimiento de cianobacteria): nacen en unos focos y se extienden en VETAS estiradas
// por el viento, con un núcleo más denso y hebras finas que derivan despacio sobre el agua. `cobertura` es la fracción
// del lago que queda verde al terminar (ilustrativa: no se rotula). Al terminar, la mancha queda.
// Cómo: una malla en rejilla sobre el lago (posada en la misma superficie que el agua, un poco encima); cada vértice
// lleva su turno (0–1: 1 = el primero en ponerse verde, por cercanía a un foco y por veta) y su distancia a la orilla.
// El shader enciende lo que tiene turno por encima del umbral, que baja con t: seek puro (el umbral sale de t).
// Sin colores escritos: el verde es tonos.bien del estilo (o tonos.secundario), mezclado con el agua.
(function (MAQ) {
  function ruidoDe(hash, k) {      // ruido de valor suave en el plano (km), fijo por k
    return (x, y) => {
      const ix = Math.floor(x), iy = Math.floor(y), tx = x - ix, ty = y - iy;
      const v = (a, b) => hash((a & 4095) * 4099 + (b & 4095), k);
      const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
    };
  }

  function dentro(x, y, an) {
    const n = an.length / 2; let c = false;
    for (let i = 0, j = n - 1; i < n; j = i++) {
      const xi = an[2 * i], yi = an[2 * i + 1], xj = an[2 * j], yj = an[2 * j + 1];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / ((yj - yi) || 1e-12) + xi) c = !c;
    }
    return c;
  }
  function distAnillo(x, y, an) {
    const n = an.length / 2; let best = Infinity;
    for (let i = 0; i < n; i++) {
      const ax = an[2 * i], ay = an[2 * i + 1], bx = an[2 * ((i + 1) % n)], by = an[2 * ((i + 1) % n) + 1];
      const dx = bx - ax, dy = by - ay, u = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / ((dx * dx + dy * dy) || 1e-12)));
      const d = Math.hypot(x - ax - u * dx, y - ay - u * dy); if (d < best) best = d;
    }
    return best;
  }

  function armarUno(ctx, e) {
    const { THREE, ES, hash, lin, COL, tonos } = ctx, S = ctx.superficieVista(ctx.altura);
    const lev = (ES.cubos ? 0.12 : 0.07) + 0.04;
    const [x0, y0, x1, y1] = e.caja, lado = Math.max(x1 - x0, y1 - y0);
    const paso = Math.max(0.06, lado / 110), mar = paso * 1.5;
    const NX = Math.ceil((x1 - x0 + 2 * mar) / paso) + 1, NY = Math.ceil((y1 - y0 + 2 * mar) / paso) + 1;
    const N = NX * NY, sem = (e.semilla || 1) * 7919 + 17;
    const hz = (i, k) => hash(i + sem, k);
    const r1 = ruidoDe(hz, 61), r2 = ruidoDe(hz, 62), r3 = ruidoDe(hz, 63), r4 = ruidoDe(hz, 64);
    const ca = Math.cos(e.viento), sa = Math.sin(e.viento), esc = Math.max(0.35, lado * 0.11);
    const focos = []; for (let i = 0; i + 1 < e.focos.length; i += 2) focos.push([e.focos[i], e.focos[i + 1]]);
    const pos = new Float32Array(N * 3), aQ = new Float32Array(N), aD = new Float32Array(N), aV = new Float32Array(N);
    const score = new Float32Array(N), cuenta = [];
    for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
      const n = j * NX + i, x = x0 - mar + i * paso, y = y0 - mar + j * paso;
      let ins = false, d = Infinity;
      for (const an of e.anillos) { if (dentro(x, y, an)) ins = true; d = Math.min(d, distAnillo(x, y, an)); }
      const sd = (ins ? d : -d) / paso;
      aD[n] = Math.max(-4, Math.min(4, sd));
      pos[n * 3] = x; pos[n * 3 + 1] = S(x, y) + lev; pos[n * 3 + 2] = -y;
      // la veta: ruido «de cresta» estirado a lo largo del viento, con el dominio torcido por otro ruido
      const al = (x * ca + y * sa) / esc, at = (-x * sa + y * ca) / esc;
      const wx = al * 0.38 + 1.2 * (r1(al * 0.6, at * 0.6) - 0.5), wy = at * 1.25 + 1.2 * (r2(al * 0.6 + 7, at * 0.6) - 0.5);
      const cresta = 1 - Math.abs(2 * r3(wx, wy) - 1), cresta2 = 1 - Math.abs(2 * r3(wx * 2.1 + 3, wy * 2.1) - 1);
      const vena = Math.pow(0.7 * cresta + 0.3 * cresta2, 1.7);
      let dmin = Infinity; for (const f of focos) dmin = Math.min(dmin, Math.hypot(x - f[0], y - f[1]));
      const foco = Math.exp(-dmin / (0.26 * lado));
      score[n] = 0.48 * foco + 0.4 * vena + 0.12 * r4(x / (esc * 0.5), y / (esc * 0.5));
      aV[n] = vena;
      if (sd > -1.2) cuenta.push(n);
    }
    // el turno: el orden de cada vértice del lago (1 = el primero en ponerse verde): así `cobertura` es la fracción del lago
    cuenta.sort((a, b) => score[b] - score[a]);
    const nIn = cuenta.length || 1;
    for (let k = 0; k < cuenta.length; k++) aQ[cuenta[k]] = 1 - k / nIn;
    const idx = [];
    for (let j = 0; j < NY - 1; j++) for (let i = 0; i < NX - 1; i++) {
      const a = j * NX + i, b = a + 1, c = a + NX, d = c + 1;
      if (Math.max(aD[a], aD[b], aD[c], aD[d]) <= -1) continue;
      idx.push(a, c, b, b, c, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("aQ", new THREE.BufferAttribute(aQ, 1));
    g.setAttribute("aD", new THREE.BufferAttribute(aD, 1));
    g.setAttribute("aV", new THREE.BufferAttribute(aV, 1));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(idx), 1));
    const verde = (tonos.bien || tonos.secundario || lin(COL.costa)).clone();
    const agua = lin(ES.modo === 4 ? COL.mar_hondo : COL.mar);
    const noche = !!ES.noche;
    const cHondo = verde.clone().lerp(agua, 0.45).multiplyScalar(noche ? 0.75 : 0.85);
    const cVivo = verde.clone().multiplyScalar(noche ? 1.0 : 1.12);
    const cHebra = verde.clone().lerp(lin(COL.luces), 0.35);
    const mat = new THREE.ShaderMaterial({
      uniforms: { ...ctx.uComun(), uUmbral: { value: 2 }, uFlorT: { value: 0 }, uViento: { value: new THREE.Vector2(ca, sa) },
        uEsc: { value: esc }, uPaso: { value: paso }, cHondo: { value: cHondo }, cVivo: { value: cVivo }, cHebra: { value: cHebra } },
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8,
      vertexShader: `attribute float aQ, aD, aV; varying float vQ, vD, vV; varying vec3 vPos;
        void main(){ vQ = aQ; vD = aD; vV = aV; vPos = (modelMatrix * vec4(position, 1.0)).xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: ctx.GLSL_COMUN + `uniform float uUmbral, uFlorT, uEsc, uPaso; uniform vec2 uViento; uniform vec3 cHondo, cVivo, cHebra;
        varying float vQ, vD, vV; varying vec3 vPos;
        float hh(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
          return mix(mix(hh(i), hh(i + vec2(1.0, 0.0)), f.x), mix(hh(i + vec2(0.0, 1.0)), hh(i + vec2(1.0, 1.0)), f.x), f.y); }
        void main(){
          vec2 p = vec2(vPos.x, -vPos.z);
          float al = dot(p, uViento), at = dot(p, vec2(-uViento.y, uViento.x));
          vec2 q = vec2(al / (uEsc * 0.55) - uFlorT * 0.025, at / (uEsc * 0.12));      // hebras finas, deriva lenta a favor del viento
          float h1 = 1.0 - abs(2.0 * vn(q + vec2(0.0, 0.6 * vn(q * 0.5))) - 1.0);
          float h2 = vn(p / (uEsc * 0.07) + vec2(uFlorT * 0.03, 0.0));
          float turno = vQ + 0.07 * (h1 - 0.5) + 0.03 * (h2 - 0.5);
          float a = smoothstep(uUmbral, uUmbral + 0.03, turno) * smoothstep(-0.2, 0.9, vD);
          if (a < 0.004) discard;
          float nucleo = smoothstep(uUmbral + 0.02, uUmbral + 0.3, turno);
          vec3 c = mix(cHondo, cVivo, clamp(nucleo * (0.55 + 0.45 * vV), 0.0, 1.0));
          c = mix(c, cHebra, 0.32 * smoothstep(0.72, 0.98, h1) * (0.4 + 0.6 * nucleo));
          a *= 0.5 + 0.42 * nucleo + 0.08 * h2;
          gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), clamp(a, 0.0, 1.0)); }` });
    const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = 3; m.visible = false; ctx.scene.add(m);
    return { m, mat, cob: e.cobertura == null ? 0.6 : e.cobertura };
  }

  MAQ.EVENTOS.florecer = {
    orden: 42,
    armar(ctx, lista) { return { lista, uno: lista.map((e) => armarUno(ctx, e)) }; },
    inicio(t, st) { if (st) for (const U of st.uno) U.m.visible = false; },
    aplicar(t, e, ctx, st) {
      if (!st) return;
      const k = st.lista.indexOf(e), U = st.uno[k];
      if (!U || t < e.t) return;
      const D = Math.max(0.4, e.dur || 0), tr = t - e.t;
      // crece rápido al principio (los focos se ven ya) y se asienta: el umbral baja de «nada» a 1 − cobertura
      const p = ctx.suave(0, 1, Math.min(1, tr / D)), f = 1 - Math.pow(1 - p, 1.6);
      U.mat.uniforms.uUmbral.value = 1.06 - (1.06 - (1 - U.cob)) * f;
      U.mat.uniforms.uFlorT.value = t;
      U.m.visible = true;
      if (e.pieza && ctx.cuadro) {     // el lago se aviva apenas mientras florece
        const b = 1 + 0.15 * Math.sin(Math.PI * Math.min(1, tr / D));
        ctx.cuadro.brillo[e.pieza] = Math.max(ctx.cuadro.brillo[e.pieza] || 0, b);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
