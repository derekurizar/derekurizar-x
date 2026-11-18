// Evento «alud» (ficha: alud.json; reglas: scripts/maqueta_tipos/alud.py): un flujo de escombros sobre una pieza
// `faldavolcan`. La parte alta de la ladera se desprende y un frente de lodo pardo, con piedras, árboles arrancados,
// techos de paja, vigas y trozos de adobe, baja por el cauce ensanchándose y se abre en un lóbulo sobre el pueblo. Lo que
// toca queda debajo: el lodo sube alrededor de las casas hasta taparlas (y tapa con ellas la luz de sus ventanas); lo
// cubierto queda cubierto. Sin erupción, sin lava, sin lago.
// - EL LODO: una malla en coordenadas del flujo (s: metros locales desde el desprendimiento; w: −1…1 de orilla a orilla),
//   posada sobre el relieve EXACTO de la pieza (la cuenta `alto` que publica faldavolcan.js en MAQ.FALDA; faldavolcan.py la repite). El frente va
//   en s = frente(x) (la misma cuenta que alud.py), con la cabeza abultada y las orillas atrasadas; en la ladera, tras el
//   frente, el lodo baja a menos de la mitad (escurre) y en lo alto queda la cicatriz de tierra fresca; en el llano se queda.
//   Rellena el fondo del barranco (superficie plana) y donde las orillas suben sigue el terreno.
// - LO QUE ARRASTRA: piedras que ruedan en la cabeza, `arboles` que caen hacia abajo y se van flotando y, en el pueblo,
//   techos de paja, vigas y adobes que salen del lodo y se van con él; al parar, todo queda medio enterrado.
// Seek puro: todo sale de t − e.t (ningún estado entre cuadros); el azar es ctx.hash. Sin colores escritos.
(function (MAQ) {
  // ---- la falda: la cuenta que publica piezas/faldavolcan.js (MAQ.FALDA, m305); el alud siempre va sobre una faldavolcan
  const TAU = 2 * Math.PI;
  const fase = (s) => MAQ.FALDA.fase(s);
  const alto = (u, v, ph) => MAQ.FALDA.alto(u, v, ph)[0];
  // ---- el flujo (las mismas constantes que alud.py)
  const S0 = 26, RAMPA = 14, CONVEXO = 0.55, PASO = 2.5, NW = 45;
  const frente = (x, st) => { x = Math.min(1, Math.max(0, x)); return S0 + (st - S0) * (0.5 - 0.5 * Math.cos(Math.PI * Math.pow(x, 0.8))); };
  const liso = (a, b, x) => { if (b <= a) return x >= b ? 1 : 0; const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const sq = (v) => v * v;

  function preparar(ctx, e, ie) {
    const { THREE, malla, tonos, lin, COL, ES, hash, scene, metros } = ctx;
    const oscuro = ES.modo === 1, noche = !!ES.noche;
    const M = metros(1) * e.tamano, ph = fase(e.semilla);
    const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
    const W2 = (u, v) => [e.fx + (u * ux - v * uy) * M, e.fy + (u * uy + v * ux) * M];
    const suelo = (u, v) => { const [x, y] = W2(u, v); return ctx.suelo(x, y) + Math.max(0, alto(u, v, ph) - 0.6) * M; };
    const hz = (i, k) => hash(i + 7703 * (ie + 1) + e.semilla * 131, k);
    const C = e.camino, SP = e.s_pie, SH = e.s_hacia, SF = e.s_fin, ST = e.s_tope;
    // el eje: punto y tangente suavizada (la ventana crece con el ancho: el lóbulo no se dobla sobre sí mismo)
    const eje = (s) => {
      s = Math.min(SF, Math.max(0, s));
      let i = 1; while (i < C.length - 1 && C[i][2] < s) i++;
      const a = C[i - 1], b = C[i], f = (s - a[2]) / ((b[2] - a[2]) || 1e-9);
      return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
    };
    const hw = (s) => {
      const h0 = e.hw0;
      if (s <= SP) return h0 * (0.35 + 0.3 * s / Math.max(1, SP));
      if (s <= SH) { const a = h0 * 0.65; return a + (e.lobulo - a) * liso(SP, SP + 0.75 * (SH - SP), s); }
      const q = (s - SH) / e.lr; return e.lobulo * Math.sqrt(Math.max(0, 1 - q * q));
    };
    const marco = (s) => {
      const h = Math.min(90, Math.max(6, 0.9 * hw(s))), A = eje(s - h), B = eje(s + h), P = eje(s);
      const L = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1, tu = (B[0] - A[0]) / L, tv = (B[1] - A[1]) / L;
      return { P, tu, tv, nu: -tv, nv: tu };
    };
    const esp = (s) => 4.0 + 1.5 * liso(SP - 20, SP + 30, s);           // espesor (m) en la ladera y en el llano
    // cuánto lodo hay a `d` m detrás del frente en s (0 = nada; > 1 = la cabeza abultada)
    const A = (d, s) => {
      if (d <= 0) return 0;
      let a = liso(0, RAMPA, d) * (1 + 0.45 * Math.exp(-sq((d - 0.9 * RAMPA) / (0.9 * RAMPA))));
      if (s < SP) a *= 1 - 0.55 * liso(60, 240, d) * (1 - liso(SP - 40, SP, s));
      a *= 1 - 0.8 * liso(40, 130, d) * (1 - liso(22, 44, s));            // la cicatriz: arriba no se queda nada
      return a;
    };
    const lateral = (w) => Math.pow(Math.max(0, 1 - w * w), 0.55);
    // el espesor (m locales) en (s, w) con el frente en sf
    const grueso = (s, w, hws, sf, tr, ola, k) => {
      const d = sf - (s + CONVEXO * hws * w * w), a = A(d, s), f = lateral(w);
      return { th: (esp(s) * k * f * a + ola * a * f * Math.exp(-Math.max(0, d) / 70)) - 3.0 * (1 - Math.min(1, a)) - 0.25, a, d };
    };

    // ---- los tonos (del estilo; los de la falda donde aplica)
    const cTierra = lin(COL.tierra_media).lerp(tonos.arena, 0.35);
    const cLodo = lin(COL.tierra_media).lerp(tonos.asfalto, 0.42).multiplyScalar(oscuro ? 1.25 : noche ? 1.1 : 0.9);
    const cLodo2 = cLodo.clone().lerp(tonos.muro, 0.25).multiplyScalar(0.82);
    const cEspuma = cTierra.clone().lerp(tonos.arena, 0.45).multiplyScalar(oscuro ? 1.25 : 1.05);
    if (noche) cEspuma.lerp(lin(COL.acento), 0.22);
    const cFresca = lin(COL.tierra_alta).lerp(cTierra, 0.45).multiplyScalar(oscuro ? 1.1 : 0.95);
    const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.45);
    const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.5 : 0.9);
    const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
    const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
    const cPaja = lin(COL.tierra_alta).lerp(tonos.medio, 0.3).multiplyScalar(oscuro ? 0.92 : 0.86);
    const cAdobe = tonos.muro.clone().lerp(lin(COL.tierra_media), 0.38).lerp(tonos.arena, 0.15);

    // ---- la malla del lodo (filas a lo largo de s, NW columnas de orilla a orilla)
    const NS = Math.max(2, Math.ceil(SF / PASO) + 1), NV = NS * NW;
    const XY = new Float32Array(NV * 2), G = new Float32Array(NV), S = new Float32Array(NS), HW = new Float32Array(NS);
    const GC = new Float32Array(NS), K = new Float32Array(NV), base = new Float32Array(NV * 3), FR = new Float32Array(NV);
    const ruido = (a, b, cel, k) => {
      const fx = a / cel, fy = b / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
      const v = (p, q) => hz((p & 4095) * 4099 + (q & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
    };
    for (let j = 0; j < NS; j++) {
      const s = Math.min(SF, j * PASO), F = marco(s), h = hw(s);
      S[j] = s; HW[j] = h; GC[j] = suelo(F.P[0], F.P[1]);
      for (let i = 0; i < NW; i++) {
        const w = -1 + 2 * i / (NW - 1), u = F.P[0] + F.nu * w * h, v = F.P[1] + F.nv * w * h, q = j * NW + i;
        const [x, y] = W2(u, v); XY[q * 2] = x; XY[q * 2 + 1] = y; G[q] = suelo(u, v);
        const n1 = ruido(s, w * h, 11, 31), n2 = ruido(s, w * h, 4, 32);
        K[q] = 0.82 + 0.3 * n1 + 0.12 * n2;
        const c = cLodo.clone().lerp(cLodo2, Math.min(1, Math.max(0, 1.2 * n1 - 0.1))).multiplyScalar(0.92 + 0.16 * n2);
        const fr = 1 - liso(18, 40, s); FR[q] = fr;
        base[q * 3] = c.r; base[q * 3 + 1] = c.g; base[q * 3 + 2] = c.b;
      }
    }
    const idx = [];
    for (let j = 0; j + 1 < NS; j++) for (let i = 0; i + 1 < NW; i++) {
      const a = j * NW + i, b = a + 1, c = a + NW, d = c + 1; idx.push(a, c, b, b, c, d);
    }
    const g = new THREE.BufferGeometry(), pos = new Float32Array(NV * 3), col = new Float32Array(NV * 3);
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    g.setIndex(NV > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
    const mat = malla.material({});
    const lodo = new THREE.Mesh(g, mat); lodo.frustumCulled = false; lodo.renderOrder = 3; lodo.visible = false; scene.add(lodo);

    // ---- lo que arrastra: plantillas (metros, y arriba) y sus partes
    const tri = (geo) => Array.from(geo.toNonIndexed().attributes.position.array);
    const T = { roca: tri(new THREE.IcosahedronGeometry(1, 0)), copa: tri(new THREE.IcosahedronGeometry(1, 1)),
      tronco: tri(new THREE.CylinderGeometry(1, 1, 1, 10, 1, true)), raiz: tri(new THREE.OctahedronGeometry(1, 0)),
      techo: tri(new THREE.ConeGeometry(1, 1, 4, 1, false)), caja: tri(new THREE.BoxGeometry(1, 1, 1)) };
    const parte = (tpl, sc, of, c, rot) => {
      const m = new THREE.Matrix4().compose(new THREE.Vector3(...of), new THREE.Quaternion().setFromEuler(new THREE.Euler(...(rot || [0, 0, 0]))), new THREE.Vector3(...sc));
      return { v: T[tpl], m, c };
    };
    const cosas = [];
    const tono = (c, k, i) => c.clone().multiplyScalar(0.85 + 0.3 * hz(i, k));
    const qIni = (i, k) => new THREE.Quaternion().setFromEuler(new THREE.Euler(TAU * hz(i, k), TAU * hz(i, k + 1), TAU * hz(i, k + 2)));
    const NR = Math.round(22 + 14 * Math.min(1, e.hw0 / 60));
    for (let i = 0; i < NR; i++) {                                         // piedras: salen del desprendimiento
      const rr = 0.7 + 1.9 * Math.pow(hz(i, 1), 1.6), enLadera = hz(i, 6) < 0.25;
      cosas.push({ clase: "roca", r: rr, w: (hz(i, 2) - 0.5) * 1.5, dl: 2 + 24 * hz(i, 3), sp: 30 * hz(i, 4),
        rest: enLadera ? SP * (0.35 + 0.6 * hz(i, 5)) : SP + (SF - 12 - SP) * (0.12 + 0.86 * hz(i, 5)), q0: qIni(i, 7),
        partes: [parte("roca", [rr, rr * (0.6 + 0.3 * hz(i, 10)), rr * (0.75 + 0.3 * hz(i, 11))], [0, 0, 0], tono(cRoca, 12, i))] });
    }
    for (let i = 0; i < (e.arboles | 0); i++) {                            // árboles: en la falda, caen y se van
      const L = 9 + 6 * hz(i, 21), rc = 2.0 + 1.3 * hz(i, 22), k = 100 + i;
      cosas.push({ clase: "arbol", L, w: (hz(k, 23) - 0.5) * 1.7, dl: 3 + 30 * hz(k, 24), sp: SP * (0.3 + 0.62 * hz(k, 25)),
        rest: SP + (SF - 15 - SP) * (0.1 + 0.85 * hz(k, 26)), giro: (hz(k, 27) - 0.5) * 0.02, yaw: TAU * hz(k, 28),
        partes: [parte("tronco", [0.28, L * 0.62, 0.28], [0, L * 0.31, 0], tono(cTronco, 29, k)),
          parte("copa", [rc, rc * 1.25, rc], [0, L * 0.62 + rc * 0.9, 0], tono(cCopa, 30, k)),
          parte("copa", [rc * 0.7, rc * 0.8, rc * 0.7], [rc * 0.5, L * 0.5, 0.3], tono(cCopa, 31, k).multiplyScalar(0.9)),
          parte("raiz", [0.9, 0.5, 0.9], [0, 0.1, 0], tono(cTronco, 32, k).lerp(cTierra, 0.5))] });
    }
    const zonaP = (i, k) => SP + 20 + Math.max(10, SH + 0.4 * e.lr - SP - 20) * hz(i, k);
    for (let i = 0; i < 8; i++) {                                         // techos de paja que se lleva
      const k = 300 + i, a = 1.9 + 0.8 * hz(k, 41), sp = zonaP(k, 42);
      cosas.push({ clase: "suelto", w: (hz(k, 43) - 0.5) * 1.3, dl: 2 + 18 * hz(k, 44), sp, rest: Math.min(SF - 8, sp + 20 + 70 * hz(k, 45)),
        alto: 0.9, q0: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.25 + 0.5 * hz(k, 46), TAU * hz(k, 47), 0.2 * hz(k, 48))), giro: (hz(k, 49) - 0.5) * 0.03,
        partes: [parte("techo", [a * 1.35, 1.7, a], [0, 0.85, 0], tono(cPaja, 50, k), [0, Math.PI / 4, 0])] });
    }
    for (let i = 0; i < 12; i++) {                                        // vigas y horcones
      const k = 400 + i, Lv = 3.5 + 3 * hz(k, 51), sp = zonaP(k, 52);
      cosas.push({ clase: "suelto", w: (hz(k, 53) - 0.5) * 1.4, dl: 1 + 22 * hz(k, 54), sp, rest: Math.min(SF - 8, sp + 15 + 75 * hz(k, 55)),
        alto: 0.2, q0: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.15 * hz(k, 56), TAU * hz(k, 57), 0.2 * (hz(k, 58) - 0.5))), giro: (hz(k, 59) - 0.5) * 0.05,
        partes: [parte("caja", [0.24, 0.24, Lv], [0, 0, 0], tono(cMadera, 60, k))] });
    }
    for (let i = 0; i < 10; i++) {                                        // trozos de pared de adobe: ruedan
      const k = 500 + i, sx = 0.9 + 0.8 * hz(k, 61), sy = 0.6 + 0.4 * hz(k, 62), sz = 0.7 + 0.5 * hz(k, 63), sp = zonaP(k, 64);
      cosas.push({ clase: "roca", r: (sx + sy + sz) / 5, w: (hz(k, 65) - 0.5) * 1.4, dl: 2 + 16 * hz(k, 66), sp, rest: Math.min(SF - 8, sp + 10 + 50 * hz(k, 67)),
        q0: qIni(k, 68), pueblo: true, partes: [parte("caja", [sx, sy, sz], [0, 0, 0], tono(cAdobe, 70, k))] });
    }
    let NT = 0; for (const c of cosas) for (const p of c.partes) NT += p.v.length / 9;
    const gd = new THREE.BufferGeometry(), dpos = new Float32Array(NT * 9), dcol = new Float32Array(NT * 9);
    gd.setAttribute("position", new THREE.BufferAttribute(dpos, 3)); gd.setAttribute("color", new THREE.BufferAttribute(dcol, 3));
    const restos = new THREE.Mesh(gd, malla.material({})); restos.frustumCulled = false; restos.renderOrder = 3; restos.visible = false; scene.add(restos);

    return { e, lodo, restos, pos, col, dpos, dcol, NS, NV, XY, G, S, HW, GC, K, base, FR, cosas, M, W2, suelo, marco, hw, grueso, A, esp, ph,
      cEspuma, cFresca, tmp: { m: new THREE.Matrix4(), q: new THREE.Quaternion(), q2: new THREE.Quaternion(), v: new THREE.Vector3(), ax: new THREE.Vector3(), s: new THREE.Vector3() } };
  }

  // la superficie del lodo (unidades de la escena) en (s, w) con el frente en sf; y el suelo bajo ella
  function superficie(P, s, w, sf, tr, x) {
    const F = P.marco(s), h = P.hw(s), u = F.P[0] + F.nu * w * h, v = F.P[1] + F.nv * w * h;
    const g = P.suelo(u, v), R = P.grueso(s, w, h, sf, tr, 0, 1);
    const [X, Y] = P.W2(u, v);
    return { x: X, y: Y, g, z: g + Math.max(0, R.th) * P.M, F, a: R.a };
  }

  function dibujar(t, P, ctx) {
    const { e } = P, { sombra } = ctx, D = Math.max(0.3, e.dur), tr = t - e.t, x = Math.min(1, Math.max(0, tr / D));
    const sf = frente(x, e.s_tope), flujo = 1 - liso(0.82, 1.0, x), M = P.M;
    // ---- el lodo
    const { pos, col, XY, G, S, HW, GC, K, base, FR, NS } = P;
    const AA = new Float32Array(NS * NW), DD = new Float32Array(NS * NW);
    for (let j = 0; j < NS; j++) {
      const s = S[j], h = HW[j], aC = P.A(sf - s, s), nivel = GC[j] + (P.esp(s) * aC * 0.95 - 0.25) * M;
      for (let i = 0; i < NW; i++) {
        const q = j * NW + i, w = -1 + 2 * i / (NW - 1);
        const ola = 0.32 * flujo * Math.sin(0.33 * s - 5.5 * tr + 2.6 * w + 6 * K[q]);
        const R = P.grueso(s, w, h, sf, tr, ola, K[q]);
        let z = G[q] + R.th * M;
        if (aC > 0) { const lw = 1 - w * w * w * w, fondo = G[q] - M; z = Math.max(z, fondo + (nivel - fondo) * lw); }
        pos[q * 3] = XY[q * 2]; pos[q * 3 + 1] = z; pos[q * 3 + 2] = -XY[q * 2 + 1];
        AA[q] = R.a; DD[q] = R.d;
      }
    }
    for (let j = 0; j < NS; j++) for (let i = 0; i < NW; i++) {
      const q = j * NW + i, qa = j * NW + Math.max(0, i - 1), qb = j * NW + Math.min(NW - 1, i + 1);
      const qc = Math.max(0, j - 1) * NW + i, qd = Math.min(NS - 1, j + 1) * NW + i;
      const ax = pos[qb * 3] - pos[qa * 3], ay = pos[qb * 3 + 1] - pos[qa * 3 + 1], az = pos[qb * 3 + 2] - pos[qa * 3 + 2];
      const bx = pos[qd * 3] - pos[qc * 3], by = pos[qd * 3 + 1] - pos[qc * 3 + 1], bz = pos[qd * 3 + 2] - pos[qc * 3 + 2];
      let nx = ay * bz - az * by, ny = az * bx - ax * bz, nz = ax * by - ay * bx;
      const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
      const l = sombra(nx, ny, nz), d = DD[q];
      const esp = 0.55 * Math.exp(-sq((d - 0.45 * RAMPA) / RAMPA)) * (0.7 + 0.3 * flujo);    // la cabeza revuelta, más clara
      const cic = FR[q] * liso(30, 90, d);                                                     // la cicatriz de tierra fresca
      let r = base[q * 3], g = base[q * 3 + 1], b = base[q * 3 + 2];
      r += (P.cEspuma.r - r) * esp; g += (P.cEspuma.g - g) * esp; b += (P.cEspuma.b - b) * esp;
      r += (P.cFresca.r - r) * cic; g += (P.cFresca.g - g) * cic; b += (P.cFresca.b - b) * cic;
      col[q * 3] = r * l; col[q * 3 + 1] = g * l; col[q * 3 + 2] = b * l;
    }
    P.lodo.geometry.attributes.position.needsUpdate = true; P.lodo.geometry.attributes.color.needsUpdate = true;
    P.lodo.visible = true;
    // ---- lo que arrastra
    const { dpos, dcol, tmp } = P, THREE = ctx.THREE;
    let n = 0;
    const pegar = (c, X, Y, Z, q, k) => {
      tmp.s.set(M * k, M * k, M * k); tmp.v.set(X, Z, -Y); tmp.m.compose(tmp.v, q, tmp.s);
      for (const p of c.partes) {
        const m = tmp.m.clone().multiply(p.m).elements, V = p.v;
        for (let o = 0; o < V.length; o += 9) {
          const pt = [];
          for (let z = 0; z < 3; z++) { const a = V[o + z * 3], b = V[o + z * 3 + 1], cc = V[o + z * 3 + 2];
            pt.push([m[0] * a + m[4] * b + m[8] * cc + m[12], m[1] * a + m[5] * b + m[9] * cc + m[13], m[2] * a + m[6] * b + m[10] * cc + m[14]]); }
          const e1 = [pt[1][0] - pt[0][0], pt[1][1] - pt[0][1], pt[1][2] - pt[0][2]], e2 = [pt[2][0] - pt[0][0], pt[2][1] - pt[0][1], pt[2][2] - pt[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const nn = Math.hypot(nx, ny, nz) || 1, l = sombra(nx / nn, ny / nn, nz / nn);
          for (let z = 0; z < 3; z++) { dpos.set(pt[z], n * 9 + z * 3); dcol[n * 9 + z * 3] = p.c.r * l; dcol[n * 9 + z * 3 + 1] = p.c.g * l; dcol[n * 9 + z * 3 + 2] = p.c.b * l; }
          n++;
        }
      }
    };
    const ejeMundo = (F) => {                       // la normal del flujo en el mundo (horizontal, ejes de three)
      const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r), X = F.nu * ux - F.nv * uy, Y = F.nu * uy + F.nv * ux;
      return new THREE.Vector3(X, 0, -Y).normalize();
    };
    for (const c of P.cosas) {
      const lleva = sf - c.dl - c.sp;
      if (c.clase === "arbol") {
        const s = lleva <= 0 ? c.sp : Math.min(c.sp + lleva, c.rest), cae = liso(0, 18, lleva), queda = liso(0, 25, sf - c.dl - c.rest);
        const Sp = superficie(P, s, c.w, sf, tr, x), F = Sp.F, ax = ejeMundo(F);
        tmp.q.setFromAxisAngle(ax, -(Math.PI / 2 - 0.12) * cae);
        tmp.q2.setFromAxisAngle(tmp.v.set(0, 1, 0), c.giro * Math.max(0, Math.min(lleva, c.rest - c.sp)));
        const q = tmp.q2.clone().multiply(tmp.q).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), c.yaw));
        const z = Sp.g + ((Sp.z - Sp.g) - (0.2 + 0.5 * queda) * M) * cae;
        pegar(c, Sp.x, Sp.y, z, q, 1);
        continue;
      }
      if (lleva <= 0) continue;
      const s = Math.min(c.sp + lleva, c.rest), parado = liso(0, 20, sf - c.dl - c.rest), Sp = superficie(P, s, c.w * 0.85, sf, tr, x);
      if (Sp.a <= 0.05) continue;
      if (c.clase === "roca") {
        const ax = ejeMundo(Sp.F); tmp.q.setFromAxisAngle(ax, -(s - c.sp) / c.r).multiply(c.q0);
        const sube = c.pueblo ? liso(0, 6, lleva) : 1;
        pegar(c, Sp.x, Sp.y, Sp.z + (c.r * (0.25 - 0.45 * parado) - c.r * 1.6 * (1 - sube)) * M, tmp.q, 1);
      } else {
        const sube = liso(0, 7, lleva);
        tmp.q.setFromAxisAngle(tmp.v.set(0, 1, 0), c.giro * (s - c.sp)).multiply(c.q0);
        pegar(c, Sp.x, Sp.y, Sp.z + (-(0.3 + 0.4 * parado) * c.alto - 1.8 * (1 - sube)) * M, tmp.q, 1);
      }
    }
    P.restos.geometry.setDrawRange(0, n * 3);
    P.restos.geometry.attributes.position.needsUpdate = true; P.restos.geometry.attributes.color.needsUpdate = true;
    P.restos.visible = n > 0;
  }
  const clave = (e) => [e.t, e.pieza, e.s_fin, e.hw0, e.lobulo].map(String).join("|");

  MAQ.EVENTOS.alud = {
    orden: 44,
    armar(ctx, lista) {
      return { lista, P: lista.map((e, i) => preparar(ctx, e, i)) };
    },
    inicio(t, st) {
      if (!st) return;
      for (const P of st.P) { P.lodo.visible = false; P.restos.visible = false; }
    },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      let i = st.lista.indexOf(e); if (i < 0) { const k = clave(e); i = st.P.findIndex((P) => clave(P.e) === k); }
      if (i >= 0) dibujar(t, st.P[i], ctx);
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
