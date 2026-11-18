// Evento «descenso» (ficha: descenso.json; reglas: scripts/maqueta_tipos/descenso.py): un flujo piroclástico. Desde el
// cráter (el primer punto del cauce de una barranca) salen PULSOS uno tras otro: cada uno es una lengua de material gris
// (manchas blandas que se apilan) con el borde anaranjado en el frente y en las orillas, y encima una nube de ceniza baja
// que sube y se queda atrás. Cada pulso llega un poco más lejos; el último llega a `hasta` del cauce. Por donde pasó queda
// el depósito gris oscuro con bloques rojizos. Con `desborde`, el último pulso se sale del cauce al final y se abre en
// abanico hacia esos lugares; las luces de `apaga` se apagan cuando el depósito las alcanza. Sin lava ni texto en el 3D.
// De noche, el gris casi no se ve y el borde anaranjado (y unas brasas en el depósito) es lo único encendido.
// Seek puro: todo sale de t − e.t (frentes en forma cerrada) y ctx.hash para el azar. Sin colores escritos.
(function (MAQ) {
  const SRGB = "c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c));";
  const NC = 80, NB = 56, NN = 24;      // por pulso: manchas del cuerpo, puntos del borde, bocanadas de nube
  const NFC = 110, NFB = 60, NFN = 30;  // la oleada del abanico: cuerpo, borde, nube
  const LEV = 0.06;                     // sobre la superficie que se ve

  const eo = (u) => { u = Math.max(0, Math.min(1, u)); return 1 - (1 - u) * (1 - u); };   // sale rápido, frena al final

  function claveDe(e) { return [e.t, e.fin[0], e.fin[1], e.alcance_km, e.pulsos].map((v) => Number(v).toFixed(3)).join("|"); }

  // el reloj de los pulsos (todo en segundos desde e.t): [{t0, Tp, alc}] y la ventana del abanico
  function plan(e, D) {
    const P = Math.max(1, Math.min(6, e.pulsos | 0 || 3)), fan = (e.abanico || []).length > 0;
    const Dp = fan ? 0.78 * D : D, Tp = Math.max(0.5, 0.48 * Dp), A = e.alcance_km;
    const p = [];
    for (let k = 0; k < P; k++) {
      const t0 = P > 1 ? (Dp - Tp) * k / (P - 1) : 0;
      p.push({ t0, Tp, alc: A * (P > 1 ? 0.55 + 0.45 * k / (P - 1) : 1) });
    }
    return { P, p, fan, f0: 0.7 * D, fT: 0.3 * D };
  }

  function armarUno(ctx, e) {
    const { THREE, lin, COL, ES, hash, scene } = ctx, S = ctx.superficieVista(ctx.altura);
    const c = e.cauce, nC = c.length / 2, CX = new Float32Array(nC), CY = new Float32Array(nC), CH = new Float32Array(nC), CS = new Float32Array(nC);
    for (let i = 0; i < nC; i++) {
      CX[i] = c[2 * i]; CY[i] = c[2 * i + 1]; CH[i] = S(CX[i], CY[i]);
      CS[i] = i ? CS[i - 1] + Math.hypot(CX[i] - CX[i - 1], CY[i] - CY[i - 1]) : 0;
    }
    const P = Math.max(1, Math.min(6, e.pulsos | 0 || 3));
    const KD = Math.min(900, Math.max(80, Math.round(e.alcance_km / 0.01)));      // granos del depósito en el cauce
    const NA = (e.abanico || []).length / 2;
    const AH = new Float32Array(NA), AR = new Float32Array(NA);
    for (let i = 0; i < NA; i++) {
      const x = e.abanico[2 * i], y = e.abanico[2 * i + 1];
      AH[i] = S(x, y); AR[i] = Math.hypot(x - e.fin[0], y - e.fin[1]);
    }
    const hF = S(e.fin[0], e.fin[1]);
    const fan = NA > 0;
    // capas, en orden de dibujo (sin depthWrite: lo primero queda debajo)
    const o = {}; let n = 0;
    o.dep = n; n += KD; o.aba = n; n += NA;
    o.cue = n; n += P * NC; o.fcue = n; n += fan ? NFC : 0;
    o.bor = n; n += P * NB; o.fbor = n; n += fan ? NFB : 0;
    o.nub = n; n += P * NN; o.fnub = n; n += fan ? NFN : 0;
    const NP = n;
    const g = new THREE.BufferGeometry(), F = (k) => new THREE.BufferAttribute(new Float32Array(NP * k), k);
    g.setAttribute("position", F(3));
    for (const a of ["aTam", "aAlfa", "aTono", "aForma", "aRot"]) g.setAttribute(a, F(1));
    const A = g.attributes;
    // forma: 0 cuerpo · 1 borde · 2 nube · 3 grano del depósito · 4 bloque
    const forma = (i) => i >= o.nub ? 2 : i >= o.bor ? 1 : i >= o.cue ? 0 : (hash(i, 7) < 0.16 ? 4 : 3);
    for (let i = 0; i < NP; i++) {
      const f = forma(i), h = hash(i, 14);
      A.aForma.setX(i, f); A.aTono.setX(i, hash(i, 11)); A.aRot.setX(i, 6.2832 * hash(i, 12));
      A.aTam.setX(i, f === 0 ? 0.3 + 0.25 * h : f === 1 ? 0.13 + 0.08 * h : f === 2 ? 0.45 + 0.45 * h : f === 3 ? 0.13 + 0.08 * h : 0.1 + 0.08 * h);
    }
    const noche = !!ES.noche;
    const claro = lin(COL.luz), oscuro = lin(COL.linea);
    const gris = (k) => claro.clone().lerp(oscuro, k);
    const cNar = lin(COL.medio || COL.luces).lerp(lin(COL.mal || COL.acento), 0.45);
    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uPx: { value: 1 }, uNoche: { value: noche ? 1 : 0 },
        cCuerpo: { value: gris(0.42) }, cNube: { value: gris(0.24) }, cDep: { value: gris(0.66) },
        cBloque: { value: gris(0.6).lerp(lin(COL.mal || COL.acento), 0.32) }, cNar: { value: cNar },
        cBrasa: { value: cNar.clone().lerp(oscuro, 0.25) } },
      transparent: true, depthWrite: false, depthTest: true, blending: THREE.NormalBlending,
      vertexShader: `attribute float aTam, aAlfa, aTono, aForma, aRot; uniform float uPx;
        varying float vAlfa, vTono, vForma, vRot;
        void main(){ vAlfa = aAlfa; vTono = aTono; vForma = aForma; vRot = aRot;
          vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;
          float px = aTam * uPx / max(0.001, -mv.z);
          float lo = aForma < 0.5 ? 7.0 : aForma < 1.5 ? 4.0 : aForma < 2.5 ? 9.0 : aForma < 3.5 ? 3.6 : 3.2;
          float hi = aForma < 0.5 ? 70.0 : aForma < 1.5 ? 18.0 : aForma < 2.5 ? 150.0 : aForma < 3.5 ? 14.0 : 14.0;
          gl_PointSize = aAlfa > 0.003 ? clamp(px, lo, hi) : 0.0; }`,
      fragmentShader: `uniform vec3 cCuerpo, cNube, cDep, cBloque, cNar, cBrasa; uniform float uNoche;
        varying float vAlfa, vTono, vForma, vRot;
        void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0; vec3 c; float a;
          float oscu = uNoche > 0.5 ? 0.42 : 1.0;
          if (vForma < 0.5) {                       // el cuerpo: una mancha blanda con su sombra abajo
            if (r > 1.0) discard; a = (exp(-r * r * 2.6) - 0.07) * 1.05;
            c = cCuerpo * (0.82 + 0.3 * vTono) * (0.85 + 0.25 * (0.5 - d.y)) * oscu;
          } else if (vForma < 1.5) {                // el borde anaranjado: brilla, de noche más
            if (r > 1.0) discard; a = exp(-r * r * 3.2); c = cNar * (uNoche > 0.5 ? 1.5 : 1.15) * (0.85 + 0.3 * vTono);
          } else if (vForma < 2.5) {                // la nube de ceniza: bocanada blanda, rizada
            float rz = r * (1.0 + 0.12 * sin(atan(d.y, d.x) * 5.0 + vRot));
            if (rz > 1.0) discard; a = (exp(-rz * rz * 2.2) - 0.11) * 0.8;
            c = cNube * (0.88 + 0.22 * vTono) * (0.8 + 0.35 * (0.5 - d.y)) * (uNoche > 0.5 ? 0.35 : 1.0);
          } else if (vForma < 3.5) {                // un grano del depósito
            if (r > 1.0) discard; a = 1.0 - smoothstep(0.55, 1.0, r); c = cDep * (0.8 + 0.35 * vTono) * oscu;
          } else {                                  // un bloque: un cuadro girado, rojizo; de noche, brasa tenue
            float cs = cos(vRot), sn = sin(vRot); vec2 q = vec2(cs * d.x - sn * d.y, sn * d.x + cs * d.y);
            float sd = max(abs(q.x), abs(q.y)) - 0.34; a = 1.0 - smoothstep(-0.03, 0.03, sd); if (a < 0.01) discard;
            c = mix(cBloque * (0.8 + 0.4 * vTono), cDep * 0.6, smoothstep(-0.1, 0.0, sd) * 0.6);
            if (uNoche > 0.5) c = mix(cBloque * 0.35, cBrasa, step(0.55, vTono) * 0.8);
          }
          a *= vAlfa; if (a < 0.004) discard;
          ${SRGB} gl_FragColor = vec4(c, clamp(a, 0.0, 1.0)); }` });
    const pts = new THREE.Points(g, mat); pts.frustumCulled = false; pts.renderOrder = 9; pts.visible = false; scene.add(pts);
    return { pts, mat, A, o, NP, KD, NA, AH, AR, hF, P, CX, CY, CH, CS, L: CS[nC - 1] || 1, clave: claveDe(e) };
  }

  function enCauce(U, s) {
    const n = U.CS.length; s = Math.max(0, Math.min(U.L, s));
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (U.CS[m] <= s) lo = m; else hi = m; }
    const d = U.CS[hi] - U.CS[lo] || 1, u = (s - U.CS[lo]) / d;
    const dx = U.CX[hi] - U.CX[lo], dy = U.CY[hi] - U.CY[lo], ln = Math.hypot(dx, dy) || 1;
    return { x: U.CX[lo] + dx * u, y: U.CY[lo] + dy * u, h: U.CH[lo] + (U.CH[hi] - U.CH[lo]) * u, nx: -dy / ln, ny: dx / ln };
  }

  MAQ.EVENTOS.descenso = {
    orden: 42,
    armar(ctx, lista) { return { lista, uno: lista.map((e) => armarUno(ctx, e)) }; },
    inicio(t, st) { if (st) for (const U of st.uno) U.pts.visible = false; },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      let k = st.lista.indexOf(e); if (k < 0) { const c = claveDe(e); k = st.uno.findIndex((u) => u.clave === c); }
      const U = st.uno[k]; if (!U) return;
      const { suave, clamp, hash } = ctx, D = Math.max(1, e.dur), tr = t - e.t;
      const fin = e.queda !== false ? 1 : 1 - suave(D, D + 1, tr);
      if (fin <= 0) return;
      U.pts.visible = true;
      U.mat.uniforms.uPx.value = ctx.cuadro ? ctx.cuadro.pxKm : 1;
      const A = U.A, o = U.o, PL = plan(e, D), W = Math.max(0.45, e.ancho_km), alc = e.alcance_km;
      // el frente más bajo de todos los pulsos: hasta ahí llega el depósito
      let Fmax = 0;
      for (const p of PL.p) Fmax = Math.max(Fmax, p.alc * eo((tr - p.t0) / p.Tp) * (tr >= p.t0 ? 1 : 0));
      const uF = PL.fan ? (tr - PL.f0) / PL.fT : -1, fR = eo(uF) * e.abanico_km;
      // 1) el depósito del cauce: granos y bloques fijos que aparecen cuando un frente pasa por su sitio
      for (let j = 0; j < U.KD; j++) {
        const i = o.dep + j, s = alc * Math.pow(hash(j, 21), 0.9), p = enCauce(U, s);
        const lado = (hash(j, 22) - 0.5) * W * (0.75 + 0.5 * s / alc);
        A.position.setXYZ(i, p.x + p.nx * lado, p.h + LEV * 1.6 + 0.02 * hash(j, 23), -(p.y + p.ny * lado));
        A.aAlfa.setX(i, 0.9 * suave(0, 0.12, Fmax - s) * fin);
      }
      // 2) el depósito del abanico: cada bloque queda donde lo dejaron las reglas cuando el frente lo alcanza
      for (let j = 0; j < U.NA; j++) {
        const i = o.aba + j;
        A.position.setXYZ(i, e.abanico[2 * j], U.AH[j] + LEV * 1.6, -e.abanico[2 * j + 1]);
        A.aAlfa.setX(i, 0.9 * suave(0, 0.06 * e.abanico_km, fR - U.AR[j]) * fin);
      }
      // 3) cada pulso: cuerpo, borde y nube
      for (let q = 0; q < U.P; q++) {
        const p = PL.p[q], u = (tr - p.t0) / p.Tp, vivo = tr >= p.t0 ? 1 : 0;
        const fr = p.alc * eo(u), lobu = Math.min(2.6, 0.45 * p.alc) * (0.35 + 0.65 * clamp(u));
        const sale = suave(0, 0.08, u) * (1 - suave(1.0, 1.35, u)) * vivo;          // el cuerpo se asienta al parar
        const nubeV = suave(0, 0.1, u) * (1 - suave(1.1, 2.2, u)) * vivo;          // la nube se queda y se deshace
        const sube = Math.max(0, u - 0.6);
        for (let j = 0; j < NC; j++) {
          const i = o.cue + q * NC + j, h = hash(i, 31), s = fr - lobu * Math.pow(h, 1.3);
          const pc = enCauce(U, s), lado = (hash(i, 32) - 0.5) * W * (1.1 - 0.5 * h);
          const lev = LEV + 0.05 + 0.1 * (1 - h) * hash(i, 33) + 0.02 * Math.sin(5 * t + 6.28 * hash(i, 34));
          A.position.setXYZ(i, pc.x + pc.nx * lado, pc.h + lev, -(pc.y + pc.ny * lado));
          A.aAlfa.setX(i, 0.92 * sale * (s > 0 ? 1 : 0) * (0.55 + 0.45 * (1 - h)) * fin);
        }
        for (let j = 0; j < NB; j++) {
          const i = o.bor + q * NB + j, h = hash(i, 41), enFrente = hash(i, 42) < 0.55;
          const s = enFrente ? fr - lobu * 0.12 * h : fr - lobu * h;
          const pc = enCauce(U, s), lado = enFrente ? (hash(i, 43) - 0.5) * W * 1.05 : (hash(i, 43) < 0.5 ? -1 : 1) * W * 0.55;
          const brilla = enFrente ? 1 : 0.65 * (1 - h);
          A.position.setXYZ(i, pc.x + pc.nx * lado, pc.h + LEV + 0.07, -(pc.y + pc.ny * lado));
          A.aAlfa.setX(i, 0.95 * brilla * suave(0, 0.06, u) * (1 - suave(0.95, 1.25, u)) * vivo * (s > 0 ? 1 : 0) * fin);
        }
        for (let j = 0; j < NN; j++) {
          const i = o.nub + q * NN + j, h = hash(i, 51), s = fr - lobu * (0.1 + 1.1 * h);
          const pc = enCauce(U, s), lado = (hash(i, 52) - 0.5) * W * 1.6 + 0.08 * sube * Math.sin(6.28 * hash(i, 53));
          const lev = LEV + 0.18 + 0.32 * hash(i, 54) + 0.25 * h + 0.35 * sube;
          A.position.setXYZ(i, pc.x + pc.nx * lado, pc.h + lev, -(pc.y + pc.ny * lado));
          A.aRot.setX(i, 6.2832 * hash(i, 12) + 0.6 * tr);
          A.aAlfa.setX(i, 0.6 * nubeV * (s > 0 ? 1 : 0) * (1 - 0.4 * h) * fin);
        }
      }
      // 4) la oleada del abanico: sale del fin del cauce hacia los lugares del desborde
      if (PL.fan) {
        const vive = suave(0, 0.06, uF) * (1 - suave(1.0, 1.4, uF)), nubeF = suave(0, 0.08, uF) * (1 - suave(1.1, 2.3, uF));
        const pon = (i, m, r0, lev) => {
          const tx = e.abanico[2 * m], ty = e.abanico[2 * m + 1], R = Math.max(0.05, U.AR[m]), f = Math.min(1, fR * r0 / R);
          A.position.setXYZ(i, e.fin[0] + (tx - e.fin[0]) * f, U.hF + (U.AH[m] - U.hF) * f + lev, -(e.fin[1] + (ty - e.fin[1]) * f));
          return { f, R };
        };
        for (let j = 0; j < NFC; j++) {
          const i = o.fcue + j, m = Math.floor(hash(i, 61) * U.NA), r = pon(i, m, 0.75 + 0.25 * hash(i, 62), LEV + 0.05 + 0.08 * hash(i, 63));
          A.aAlfa.setX(i, 0.75 * vive * fin * (r.f > 0.02 ? 1 : 0));
        }
        for (let j = 0; j < NFB; j++) {
          const i = o.fbor + j, m = Math.floor(hash(i, 64) * U.NA), r = pon(i, m, 1, LEV + 0.07);
          const alFrente = suave(0.6, 0.95, fR / Math.max(0.05, U.AR[m]) ) * (1 - suave(1.2, 1.6, fR / Math.max(0.05, U.AR[m])));
          A.aAlfa.setX(i, 0.95 * Math.max(alFrente, 0.25) * (1 - suave(0.95, 1.25, uF)) * suave(0, 0.05, uF) * fin * (r.f > 0.02 ? 1 : 0));
        }
        for (let j = 0; j < NFN; j++) {
          const i = o.fnub + j, m = Math.floor(hash(i, 66) * U.NA), r = pon(i, m, 0.6 + 0.3 * hash(i, 67), LEV + 0.22 + 0.35 * hash(i, 68) + 0.3 * Math.max(0, uF - 0.6));
          A.aRot.setX(i, 6.2832 * hash(i, 12) + 0.6 * tr);
          A.aAlfa.setX(i, 0.55 * nubeF * fin * (r.f > 0.02 ? 1 : 0));
        }
      }
      for (const nm of ["position", "aAlfa", "aRot"]) A[nm].needsUpdate = true;
      // 5) las luces que quedan cubiertas se apagan cuando el depósito llega a ellas
      if (e.apaga && e.apaga.length && ctx.luces) {
        e.apaga.forEach((a, j) => {
          const id = e.apaga_ids[j], prog = a[2] === 1 ? (fR / Math.max(0.01, e.abanico_km)) : Fmax / Math.max(0.01, alc);
          const off = suave(0, 0.08, prog - a[3]);
          if (off <= 0) return;
          for (const l of ctx.luces) if (l.id === id && Math.abs(l.x - a[0]) < 0.02 && Math.abs(l.y - a[1]) < 0.02) l.v *= 1 - off;
        });
      }
      // la barranca se aviva mientras bajan los pulsos
      if (e.pieza && ctx.cuadro) {
        const b = 1 + 0.3 * suave(0, 0.1 * D, tr) * (1 - 0.7 * suave(D, D + 1.5, tr));
        ctx.cuadro.brillo[e.pieza] = Math.max(ctx.cuadro.brillo[e.pieza] || 0, b);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
