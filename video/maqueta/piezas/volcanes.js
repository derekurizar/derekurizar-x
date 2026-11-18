// Pieza «volcanes» (ficha: volcanes.json; reglas: scripts/maqueta_tipos/volcanes.py): los conos de unos volcanes nombrados,
// nítidos sobre el relieve del país, que a 60–120 km los deja romos y bajos. Cada cumbre es un cono cóncavo con su cráter y
// barrancas radiales; el protagonista, en el acento; los demás («atenuado»), con la cima y el cráter en el acento a media intensidad. Dos conos que se tocan son un
// macizo: una sola malla por macizo cuya altura es el máximo de los conos y del suelo VISIBLE del relieve (la misma
// superficie que arma mundos/pais.js), así el pie se funde con la ladera sin flotar ni hundirse. Sin humo ni lava.
// «resaltar» aviva toda la pieza por su id (ctx.cuadro.brillo) o una cumbre con `elemento` (ctx.cuadro.elementos).
// `forma: "cono"` quita las barrancas (un cono liso, sin abanico de rayos); `reposo` es la intensidad de la cima naranja
// antes de encenderse, y `encendido` («queda»/«solo») la sube al acento pleno cuando un evento cumbres nombra esa cumbre
// (con «solo», la anterior vuelve a `reposo` cuando prende la siguiente). Todo sale de t y de los eventos: seek puro.
(function (MAQ) {
  const CRATER = 0.06, HONDO = 0.05, POT = 1.6, BARRANCAS = 0.06;   // las mismas constantes que volcanes.py
  // la altura del cono c = [x, y, R, top, base, fase] en (x, y), o null fuera de su radio (= volcanes.py → forma)
  function forma(c, x, y, crater, liso) {
    const [cx, cy, R, top, base, fase] = c, dx = x - cx, dy = y - cy, u = Math.hypot(dx, dy) / R;
    if (u >= 1) return null;
    const alto = top - base, uc = crater ? CRATER : 0;
    if (u <= uc) { const q = u / uc; return top - HONDO * alto * (1 - q * q); }
    const v = (u - uc) / (1 - uc), n = 9 + (fase % 4);
    if (liso) return base + alto * Math.pow(1 - v, POT);
    return base + alto * Math.pow(1 - v, POT) - BARRANCAS * alto * 4 * v * (1 - v) * Math.pow(0.5 + 0.5 * Math.sin(n * Math.atan2(dy, dx) + fase * 2.4), 3);
  }
  // el suelo que se VE (la malla de mundos/pais.js toma una celda de cada dos; en voxel, columnas de 6 × 6): sobre el suelo
  // del mundo SIN el relieve de pieza (ctx.suelo), para no contar el cono dos veces
  const sueloVisible = (ctx) => ctx.sueloVisto;   // el suelo que se ve sin el relieve de pieza (motor.js, m305)
  // los grupos de conos que se tocan (= volcanes.py → macizos)
  function macizos(cs) {
    const padre = cs.map((_, i) => i), raiz = (i) => { while (padre[i] !== i) i = padre[i] = padre[padre[i]]; return i; };
    for (let i = 0; i < cs.length; i++) for (let j = i + 1; j < cs.length; j++)
      if (Math.hypot(cs[i][0] - cs[j][0], cs[i][1] - cs[j][1]) < cs[i][2] + cs[j][2]) padre[raiz(i)] = raiz(j);
    const g = new Map(); cs.forEach((_, i) => { const r = raiz(i); if (!g.has(r)) g.set(r, []); g.get(r).push(i); });
    return [...g.values()];
  }
  MAQ.PIEZAS.volcanes = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, COL, ES, lin, scene } = ctx, S = sueloVisible(ctx);
      const lev = ES.cubos ? 0.1 : 0.03, escalon = ES.cubos ? 0.3 * ctx.EXAG : 0;
      const claro = lin(COL.secundario), acento = lin(COL.acento);
      // el pie se funde hacia el tono de las tierras altas del relieve; el cráter, en la sombra
      const pie = lin(COL.tierra_media || COL.secundario), hondo = claro.clone().multiplyScalar(0.4);
      const tierra = lin(COL.tierra_alta || COL.secundario);
      // fuera de acento («atenuado», por defecto si no es protagonista): el cuerpo en el acento oscurecido (≈ 30 %) y
      // la cima con su cráter en el MISMO naranja a media intensidad (nunca blanco: un cono claro se lee como humo o nube);
      // la capa de la cima es ancha (hasta ~26 % del radio) para que un cono de 5 km se lea a 150–280 km
      const medio = acento.clone().multiplyScalar(0.5), cuerpoAt = acento.clone().multiplyScalar(0.3).lerp(pie.clone().multiplyScalar(0.6), 0.25);
      return piezas.map((p) => {
        const cs = p.cumbres, crater = p.crater !== false, mallas = [], liso = p.forma === "cono";
        const at = (p.tono || (p.protagonista ? "acento" : "atenuado")) === "atenuado";
        // la cima naranja (dinámica: su nivel va en uNivel): siempre en «atenuado»; en «acento», si se pide `reposo`
        const cima = at || p.reposo != null, rep = ctx.clamp(p.reposo != null ? +p.reposo : 0.5, 0, 1);
        const cuerpoAc = acento.clone().multiplyScalar(0.34).lerp(pie.clone().multiplyScalar(0.6), 0.25);   // apenas más vivo que el atenuado: la cima manda
        const color = at ? cuerpoAt : (cima ? cuerpoAc : acento), fondo = cima ? cuerpoAt : hondo;
        for (const grupo of macizos(cs)) {
          const G = grupo.map((i) => cs[i]);
          const x0 = Math.min(...G.map((c) => c[0] - c[2])), y0 = Math.min(...G.map((c) => c[1] - c[2]));
          const x1 = Math.max(...G.map((c) => c[0] + c[2])), y1 = Math.max(...G.map((c) => c[1] + c[2]));
          const paso = Math.min(...G.map((c) => c[2])) / 46, nx = Math.ceil((x1 - x0) / paso) + 1, ny = Math.ceil((y1 - y0) / paso) + 1;
          // las alturas de la cuadrícula: el máximo de los conos (y cuál manda) y del suelo visible
          const H = new Float32Array(nx * ny), Q = new Int16Array(nx * ny), U = new Float32Array(nx * ny), D = new Uint8Array(nx * ny), E = new Float32Array(nx * ny);
          for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
            const x = x0 + i * paso, y = y0 + j * paso, k = j * nx + i, s = S(x, y);
            let h = -1e9, q = -1, u = 9;
            G.forEach((c, gi) => { const v = forma(c, x, y, crater, liso); if (v !== null && v > h) { h = v; q = grupo[gi]; } u = Math.min(u, Math.hypot(x - c[0], y - c[1]) / c[2]); });
            if (escalon && h > -1e8) h = Math.round(h / escalon * 3) * escalon / 3;   // voxel: el cono en terrazas
            H[k] = Math.max(s + lev, h); Q[k] = q < 0 ? grupo[0] : q; U[k] = u; E[k] = h - s;   // E: lo que el cono sobresale del suelo
            const c = cs[Q[k]]; D[k] = crater && Math.hypot(x - c[0], y - c[1]) / c[2] < CRATER * 0.92 ? 1 : 0;
          }
          const pos = [], col = [], cum = [], sh = [], cap = [], ff = [], idx = [], mapa = new Int32Array(nx * ny).fill(-1);
          const vert = (i, j) => { const k = j * nx + i; if (mapa[k] >= 0) return mapa[k];
            const il = Math.max(0, i - 1), ir = Math.min(nx - 1, i + 1), jl = Math.max(0, j - 1), jr = Math.min(ny - 1, j + 1);
            const gx = (H[j * nx + ir] - H[j * nx + il]) / ((ir - il) * paso), gy = (H[jr * nx + i] - H[jl * nx + i]) / ((jr - jl) * paso);
            const L = Math.hypot(gx, 1, gy), lam = (ctx.sombra(-gx / L, 1 / L, gy / L) - 0.5) / 0.62;
            const f = Math.min(1.25, Math.max(0.24, 0.3 + 0.95 * lam));   // más contraste que el relieve: el cono se lee como volumen
            const cc = cs[Q[k]], w = ctx.suave(0, 0.14 * (cc[3] - cc[4]), E[k]), c = (D[k] ? fondo : color).clone();
            if (!D[k]) c.lerp(pie, 1 - w);                               // el pie se funde con la ladera donde el cono apenas sobresale
            // la cima (y el cráter) en el naranja del acento a su nivel: el shader la mezcla con uNivel de su cumbre
            const wc = cima ? (D[k] ? 1 : 0.85 * (1 - ctx.suave(0.1, 0.26, U[k]))) : 0;
            mapa[k] = pos.length / 3; pos.push(x0 + i * paso, H[k], -(y0 + j * paso));
            col.push(c.r * f, c.g * f, c.b * f); cum.push(Q[k]); sh.push(f * (D[k] ? 0.42 : 1)); cap.push(wc); ff.push(f);
            return mapa[k]; };
          for (let j = 0; j + 1 < ny; j++) for (let i = 0; i + 1 < nx; i++) {
            const k = j * nx + i;
            if (Math.max(E[k], E[k + 1], E[k + nx], E[k + nx + 1]) <= 0) continue;   // el cono no sobresale: queda el relieve
            const a = vert(i, j), b = vert(i + 1, j), c = vert(i, j + 1), d = vert(i + 1, j + 1);
            idx.push(a, c, b, b, c, d);
          }
          if (!idx.length) continue;
          const g = new THREE.BufferGeometry();
          g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
          g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(col), 3));
          g.setAttribute("aCum", new THREE.BufferAttribute(new Float32Array(cum), 1));
          g.setAttribute("aSh", new THREE.BufferAttribute(new Float32Array(sh), 1));
          g.setAttribute("aCap", new THREE.BufferAttribute(new Float32Array(cap), 1));
          g.setAttribute("aF", new THREE.BufferAttribute(new Float32Array(ff), 1));
          g.setIndex(pos.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
          const mat = new THREE.ShaderMaterial({
            uniforms: { ...ctx.uComun(), uBrillo: { value: 1 }, uCumbre: { value: new Float32Array(16) }, uNivel: { value: new Float32Array(16).fill(rep) }, cAcento: { value: acento } },
            side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2,
            vertexShader: "attribute vec3 color; attribute float aCum, aSh, aCap, aF; varying vec3 vCol, vPos; varying float vCum, vSh, vCap, vF;" +
              "void main(){ vCol = color; vCum = aCum; vSh = aSh; vCap = aCap; vF = aF; vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: ctx.GLSL_COMUN + `uniform float uBrillo; uniform float uCumbre[16], uNivel[16]; uniform vec3 cAcento; varying vec3 vCol, vPos; varying float vCum, vSh, vCap, vF;
              void main(){   // una cumbre resaltada toma el acento con su misma luz; la cima, el naranja a su nivel
                float k = 0.0, nv = 0.0; for (int i = 0; i < 16; i++) { float s = 1.0 - step(0.5, abs(vCum - float(i))); k = max(k, uCumbre[i] * s); nv = max(nv, uNivel[i] * s); }
                vec3 c = mix(vCol, cAcento * nv * vF, vCap);
                c = mix(c, cAcento * vSh, k * 0.85) * uBrillo;
                gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }` });
          const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = 1; scene.add(m); mallas.push(mat);
        }
        // los encendidos de sus cumbres: cada evento cumbres sobre esta pieza, con los mismos tiempos que cumbres.js
        const prenden = [];
        for (const e of (p.encendido === "queda" || p.encendido === "solo") ? (ctx.M.eventos || []) : []) {
          if (e.tipo !== "cumbres" || e.pieza !== p.id || !e.cumbres || !e.cumbres.length) continue;
          const D = Math.max(0.3, e.dur || 0), n = e.cumbres.length, w = ctx.clamp(0.9 * D / n, 0.12, 0.55);
          e.cumbres.forEach((c, k) => prenden.push({ i: c[0], t0: e.t + (n > 1 ? 0.78 * D * k / (n - 1) : 0), w,
            fin: e.queda === false ? e.t + D : null }));
        }
        prenden.sort((a, b) => a.t0 - b.t0);
        return { id: p.id, mallas, rep, cima, solo: p.encendido === "solo", prenden };
      });
    },
    en(t, lista, ctx) {
      for (const e of lista) {
        const b = ctx.cuadro.brillo[e.id], el = (ctx.cuadro.elementos || {})[e.id] || [];
        for (const mat of e.mallas) {
          mat.uniforms.uBrillo.value = b ? 1 + 0.3 * (b - 1) : 1;
          const R = mat.uniforms.uCumbre.value; R.fill(0);
          for (const o of el) if (o.i >= 0 && o.i < 16) R[o.i] = Math.max(R[o.i], o.k);
        }
        if (!e.cima) continue;
        // el nivel de cada cima: reposo; al acento pleno cuando su cumbres la prende (con «solo», hasta que prende la
        // siguiente); un «resaltar» de toda la pieza las aviva todas a la vez
        const N = new Float32Array(16).fill(e.rep), P = e.prenden, { suave, clamp } = ctx;
        for (let j = 0; j < P.length; j++) {
          const a = P[j]; if (t < a.t0 || a.i < 0 || a.i >= 16) continue;
          let on = suave(a.t0, a.t0 + a.w, t);
          if (a.fin !== null) on *= 1 - suave(a.fin, a.fin + 0.6, t);
          if (e.solo && j + 1 < P.length) on *= 1 - suave(P[j + 1].t0, P[j + 1].t0 + P[j + 1].w, t);
          N[a.i] = Math.max(N[a.i], e.rep + (1 - e.rep) * on);
        }
        if (b) { const v = e.rep + (1 - e.rep) * clamp((b - 1) / 0.7, 0, 1); for (let i = 0; i < 16; i++) N[i] = Math.max(N[i], v); }
        for (const mat of e.mallas) mat.uniforms.uNivel.value.set(N);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
