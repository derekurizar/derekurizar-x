// Evento «endurecer» (ficha: endurecer.json; reglas: scripts/maqueta_tipos/endurecer.py): llueve sobre el depósito que
// dejó un `piroclastico` en una pieza `aldeabarranca` (o `faldavolcan`) y la ceniza suelta se vuelve costra dura.
// Sin texto ni cifras: ilustra un proceso, no afirma un espesor.
// - EL DEPÓSITO: el mismo que dejó el piroclastico (su relleno del cauce y su lóbulo en la aldea, en su estado final y
//   con su mismo azar: las reglas copian lo que resolvió ese evento). Esta capa va encima, pegada (polygonOffset): al
//   empezar es idéntica a la ceniza gris y, con la lluvia, se moja, se oscurece y se parte en placas.
// - LA LLUVIA (`lluvia`): rayas con viento en una caja que va con la cámara y gotas que salpican sobre el depósito;
//   sube al empezar y escampa antes del final.
// - LA COSTRA (`costra`): el gris pasa a un gris oscuro y mate por placas (cada una con su tono); en lo bajo quedan
//   charcos que se secan al escampar.
// - LAS GRIETAS (`grietas`): una red de placas (Voronoi sobre el depósito) cuyas grietas oscuras se abren una tras otra.
// Lo que queda se queda el resto del tramo. Seek puro: todo sale de t (lo fijo se arma en `armar`); el azar es ctx.hash.
(function (MAQ) {
  const PASO = 4, NW = 23, S0 = 40;
  const liso = (a, b, x) => { if (a === b) return x >= b ? 1 : 0; const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const cl01 = (x) => Math.min(1, Math.max(0, x));
  const sq = (v) => v * v;
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

  // ---- las curvas del evento en la fracción x de `dur`
  const curva = (e, x) => ({
    lluvia: e.lluvia * liso(0, 0.12, x) * (1 - liso(0.72, 0.95, x)),
    moja: e.lluvia * liso(0.04, 0.32, x) * (1 - 0.55 * liso(0.8, 1, x)),
    dura: e.costra * liso(0.12, 0.78, x),
    charco: e.lluvia * liso(0.22, 0.5, x) * (1 - 0.75 * liso(0.82, 1, x)),
  });

  // ---- la red de placas: Voronoi de semillas en una rejilla con jitter sobre [a0, a1] × [b0, b1] (en metros locales)
  function voronoi(a0, a1, b0, b1, L, hm, k0) {
    const NA = Math.max(1, Math.ceil((a1 - a0) / L)), NB = Math.max(1, Math.ceil((b1 - b0) / L));
    const sem = (i, j) => (i < 0 || j < 0 || i >= NA || j >= NB) ? null
      : [a0 + (i + 0.15 + 0.7 * hm(i * 7919 + j + k0, 1)) * L, b0 + (j + 0.15 + 0.7 * hm(i * 7919 + j + k0, 2)) * L, i * NB + j];
    const placa = (a, b) => {                       // la semilla más cercana a (a, b): su id
      const i0 = Math.floor((a - a0) / L), j0 = Math.floor((b - b0) / L);
      let m = Infinity, id = -1;
      for (let i = i0 - 2; i <= i0 + 2; i++) for (let j = j0 - 2; j <= j0 + 2; j++) { const s = sem(i, j); if (!s) continue; const d = sq(a - s[0]) + sq(b - s[1]); if (d < m) { m = d; id = s[2]; } }
      return id;
    };
    const aristas = [];
    for (let i = 0; i < NA; i++) for (let j = 0; j < NB; j++) {
      const s = sem(i, j), R = 1.6 * L;
      let pol = [{ x: s[0] - R, y: s[1] - R, l: -1 }, { x: s[0] + R, y: s[1] - R, l: -1 }, { x: s[0] + R, y: s[1] + R, l: -1 }, { x: s[0] - R, y: s[1] + R, l: -1 }];
      for (let di = -2; di <= 2; di++) for (let dj = -2; dj <= 2; dj++) {
        if (!di && !dj) continue;
        const o = sem(i + di, j + dj); if (!o) continue;
        const nx = o[0] - s[0], ny = o[1] - s[1], c = nx * (s[0] + o[0]) / 2 + ny * (s[1] + o[1]) / 2, out = [];
        for (let q = 0; q < pol.length; q++) {
          const P = pol[q], Q = pol[(q + 1) % pol.length], dp = nx * P.x + ny * P.y - c, dq = nx * Q.x + ny * Q.y - c;
          if (dp <= 0) out.push(P);
          if ((dp <= 0) !== (dq <= 0)) {
            const f = dp / (dp - dq), I = { x: P.x + (Q.x - P.x) * f, y: P.y + (Q.y - P.y) * f, l: dp <= 0 ? o[2] : P.l };
            out.push(I);
          }
        }
        pol = out; if (pol.length < 3) break;
      }
      for (let q = 0; q < pol.length; q++) {
        const P = pol[q], Q = pol[(q + 1) % pol.length];
        if (P.l > s[2]) aristas.push([P.x, P.y, Q.x, Q.y, s[2] * 131 + P.l]);
      }
    }
    return { placa, aristas };
  }

  function preparar(ctx, e, ie) {
    const { THREE, malla, tonos, lin, COL, ES, hash, scene, metros, sombra } = ctx;
    const oscuro = ES.modo === 1, noche = !!ES.noche;
    const M = metros(1) * e.tamano, n = Math.max(1, e.pulsos | 0);
    const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
    const W2 = (u, v) => [e.fx + (u * ux - v * uy) * M, e.fy + (u * uy + v * ux) * M];
    const gz = (u, v) => { const [x, y] = W2(u, v); return ctx.altura(x, y); };
    // el azar del piroclastico (el mismo depósito) y el propio (placas, grietas, gotas)
    const hz = (i, k) => hash(i + 6151 * ((e.ie | 0) + 1) + (e.p_semilla | 0) * 97, k);
    const hm = (i, k) => hash(i + 4253 * (ie + 1) + (e.semilla | 0) * 131 + 77, k);
    const ruido = (a, b, cel, k, h = hz) => {
      const fx = a / cel, fy = b / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
      const v = (p, q) => h((p & 4095) * 4099 + (q & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
    };

    // ---- los tonos: los del piroclastico (para empezar idéntico) y los de la costra
    const cDep = tonos.asfalto.clone().lerp(tonos.muro, 0.35).lerp(tonos.arena, 0.1).multiplyScalar(oscuro ? 1.15 : ES.dia ? 0.5 : 0.62);
    const cDep2 = cDep.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.82);
    const cRojo = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.55).lerp(cDep, 0.35).multiplyScalar(oscuro ? 0.95 : 0.8);
    const cDura = cDep2.clone().lerp(tonos.asfalto, 0.45).multiplyScalar(oscuro ? 0.92 : 0.74);
    const cDuraC = cDura.clone().lerp(tonos.muro, 0.22).multiplyScalar(1.12);        // la cara clara de una placa
    const cGrieta = tonos.asfalto.clone().lerp(tonos.linea, 0.15).multiplyScalar(oscuro ? 0.42 : 0.3);
    const cAgua = cDura.clone().lerp(lin(COL.costa), 0.3).multiplyScalar(oscuro ? 0.7 : noche ? 0.5 : 0.6);        // charco: más oscuro que la costra
    const cLluvia = lin(COL.costa).lerp(tonos.muro, 0.25), cGota = lin(COL.costa).lerp(tonos.muro, 0.5).multiplyScalar(oscuro ? 1 : 1.15);

    const vis = (pos, NA, NB) => {                   // la luz de cada vértice de una lámina (sus normales: fijas)
      const L = new Float32Array(NA * NB);
      for (let a = 0; a < NA; a++) for (let b = 0; b < NB; b++) {
        const q = a * NB + b, qa = a * NB + Math.max(0, b - 1), qb = a * NB + Math.min(NB - 1, b + 1), qc = Math.max(0, a - 1) * NB + b, qd = Math.min(NA - 1, a + 1) * NB + b;
        const ax = pos[qb * 3] - pos[qa * 3], ay = pos[qb * 3 + 1] - pos[qa * 3 + 1], az = pos[qb * 3 + 2] - pos[qa * 3 + 2];
        const bx = pos[qd * 3] - pos[qc * 3], by = pos[qd * 3 + 1] - pos[qc * 3 + 1], bz = pos[qd * 3 + 2] - pos[qc * 3 + 2];
        let nx = ay * bz - az * by, ny = az * bx - ax * bz, nz = ax * by - ay * bx;
        const nn = Math.hypot(nx, ny, nz) || 1; nx /= nn; ny /= nn; nz /= nn; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        L[q] = sombra(nx, ny, nz);
      }
      return L;
    };
    const lamina = (NA, NB, pos) => {
      const idx = [];
      for (let j = 0; j + 1 < NA; j++) for (let i = 0; i + 1 < NB; i++) { const a = j * NB + i, b = a + 1, c = a + NB, d = c + 1; idx.push(a, c, b, b, c, d); }
      const g = new THREE.BufferGeometry(), N = NA * NB;
      g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
      g.setIndex(N > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
      const m = new THREE.Mesh(g, malla.material({ desfase: 2 })); m.frustumCulled = false; m.renderOrder = 4; m.visible = false; scene.add(m);
      return m;
    };
    const tono = new THREE.Color();
    const LAM = [];                                  // las láminas: {m, N, base, L, placa, charco}
    const GOTAS = [];                                // dónde salpica la lluvia: [x, y, z]
    const GR = [];                                   // los tramos de grieta: [ax, ay, az, bx, by, bz, x0, ancho]
    const Lp = 9 + 6 * (1 - e.grietas);              // m: el lado de una placa

    // ---- las grietas de una red: tramos cortos que siguen las aristas dentro del depósito, cada uno con su x de salida
    const grietas = (V, sup, ok, k0) => {
      if (!(e.grietas > 0)) return;
      const lleva = 0.3 + 0.7 * e.grietas;
      for (const A of V.aristas) {
        const id = A[4];
        if (hm(id, 3) > lleva) continue;
        const len = Math.hypot(A[2] - A[0], A[3] - A[1]); if (len < 1) continue;
        const m = Math.max(1, Math.ceil(len / 2.6)), pa = -(A[3] - A[1]) / len, pb = (A[2] - A[0]) / len, nodos = [];
        for (let k = 0; k <= m; k++) {
          const f = k / m, w = k === 0 || k === m ? 0 : (hm(id * 31 + k, 4) - 0.5) * 0.9;
          nodos.push([A[0] + (A[2] - A[0]) * f + pa * w, A[1] + (A[3] - A[1]) * f + pb * w]);
        }
        const x0 = 0.34 + 0.4 * hm(id, 5), an = (0.32 + 0.3 * hm(id, 6)) * (0.65 + 0.55 * e.grietas), dir = hm(id, 7) < 0.5;
        for (let k = 0; k < m; k++) {
          const P = nodos[k], Q = nodos[k + 1];
          if (!ok(P[0], P[1]) || !ok(Q[0], Q[1])) continue;
          const sp = sup(P[0], P[1]), sq2 = sup(Q[0], Q[1]), kk = dir ? k : m - 1 - k;
          GR.push([sp[0], sp[1], sp[2] + 0.18 * M, sq2[0], sq2[1], sq2[2] + 0.18 * M, Math.min(0.9, x0 + 0.025 * kk), an * M, k0]);
        }
      }
    };

    // ================= el relleno del cauce (el estado final del piroclastico)
    const C = e.cauce, NC = C.length;
    const enC = (s) => {
      s = Math.min(C[NC - 1][2], Math.max(0, s));
      let i = 1; while (i < NC - 1 && C[i][2] < s) i++;
      const a = C[i - 1], b = C[i], f = (s - a[2]) / ((b[2] - a[2]) || 1e-9), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return { u: a[0] + (b[0] - a[0]) * f, v: a[1] + (b[1] - a[1]) * f, tu: (b[0] - a[0]) / L, tv: (b[1] - a[1]) / L, hw: a[3] + (b[3] - a[3]) * f };
    };
    const sgn = (F) => (e.lado === 0 ? 1 : (F.tu * e.lado >= 0 ? 1 : -1));
    {
      const SF = Math.min(C[NC - 1][2], e.s_fin + 40), NS = Math.max(2, Math.ceil(SF / PASO) + 1), NV = NS * NW;
      const RS = new Float32Array(NS), FL = new Float32Array(NS), HC = new Float32Array(NS), RV = new Float32Array(NS), RO = new Float32Array(NS), BU = new Float32Array(NS), H = new Float32Array(NS);
      for (let j = 0; j < NS; j++) {
        const s = Math.min(SF, j * PASO), F = enC(s), nu = -F.tv, nv = F.tu, sv = sgn(F);
        RS[j] = s; FL[j] = gz(F.u, F.v);
        RV[j] = gz(F.u + nu * sv * 1.35 * F.hw, F.v + nv * sv * 1.35 * F.hw);
        RO[j] = gz(F.u - nu * sv * 1.35 * F.hw, F.v - nv * sv * 1.35 * F.hw);
        HC[j] = Math.max(2 * M, Math.min(RV[j], RO[j]) - FL[j]);
      }
      for (let j = 0; j < NS; j++) {
        const ds = RS[j] - e.s_spill, g = Math.exp(-sq(ds / (ds < 0 ? 70 : 32)));
        const meta = RV[j] + (0.6 + 1.8 * e.desborde) * M;
        BU[j] = e.desborde < 0.15 ? 0 : Math.max(0, meta - (FL[j] + 0.55 * HC[j])) * g;
      }
      // los frentes ya quietos: los primeros a su alcance, el último hasta s_fin
      const Fs = []; for (let i = 0; i < n; i++) Fs.push(i === n - 1 ? e.s_fin : Math.max(S0, e.s_spill * (0.5 + 0.4 * i / Math.max(1, n - 1))));
      for (let j = 0; j < NS; j++) {
        let h = 0;
        for (let i = 0; i < n; i++) {
          const d = Fs[i] - RS[j]; if (d <= 0) continue;
          const fr = n > 1 ? 0.55 / n * (0.6 + 0.8 * i / (n - 1)) : 0.55;
          h += fr * HC[j] * liso(0, 40, d);
          if (i === n - 1) h += BU[j] * liso(0, 30, d);
        }
        H[j] = h;
      }
      const pos = new Float32Array(NV * 3), base = new Float32Array(NV * 3), placa = new Float32Array(NV), charco = new Float32Array(NV);
      let alguno = false, o0 = Infinity, o1 = -Infinity;
      const V = (() => { for (let j = 0; j < NS; j++) { const hw = enC(RS[j]).hw; o0 = Math.min(o0, -1.3 * hw); o1 = Math.max(o1, 1.3 * hw); } return voronoi(0, SF, o0, o1, Lp, hm, 1); })();
      for (let j = 0; j < NS; j++) {
        const F = enC(RS[j]), nu = -F.tv, nv = F.tu, L = FL[j] + H[j];
        for (let i = 0; i < NW; i++) {
          const w = -1.3 + 2.6 * i / (NW - 1), q = j * NW + i, uu = F.u + nu * w * F.hw, vv = F.v + nv * w * F.hw, ow = w * F.hw;
          const [x, y] = W2(uu, vv), aw = Math.abs(w);
          const n1 = ruido(RS[j], ow, 9, 11), n2 = ruido(RS[j], ow, 3.5, 12), cK = n1 * 0.7 + n2 * 0.3;
          let z = L + (cK - 0.5) * 0.5 * M;
          const sv = w * sgn(F);
          if (aw > 1) { const rim = sv > 0 ? RV[j] : RO[j]; z = Math.min(z, rim + 0.8 * M * (1.3 - aw) / 0.3); }
          if (H[j] < 0.15 * M) z = FL[j] - 3 * M; else { alguno = true; z += 0.04 * M; }
          pos[q * 3] = x; pos[q * 3 + 1] = z; pos[q * 3 + 2] = -y;
          tono.copy(cDep).lerp(cRojo, liso(0.62, 0.8, n2) * 0.7).multiplyScalar(0.9 + 0.18 * n1).lerp(cDep2, 0.5);
          base[q * 3] = tono.r; base[q * 3 + 1] = tono.g; base[q * 3 + 2] = tono.b;
          placa[q] = hm(V.placa(RS[j], ow), 9);
          charco[q] = aw < 0.8 ? liso(0.62, 0.78, ruido(RS[j], ow, 16, 13, hm)) : 0;
          if (H[j] >= 0.4 * M && aw < 0.9 && (j * 7 + i) % 5 === 0) GOTAS.push([x, y, z + 0.1 * M]);
        }
      }
      if (alguno) {
        const m = lamina(NS, NW, pos);
        LAM.push({ m, N: NV, base, L: vis(pos, NS, NW), placa, charco });
        // la superficie en (s, o): la misma cuenta que arriba (sin el aplanado de las orillas: las grietas van por dentro)
        const sup = (s, o) => {
          const fj = Math.min(NS - 1, Math.max(0, s / PASO)), j = Math.min(NS - 2, Math.floor(fj)), f = fj - j;
          const F = enC(s), uu = F.u - F.tv * o, vv = F.v + F.tu * o, [x, y] = W2(uu, vv);
          const cK = ruido(s, o, 9, 11) * 0.7 + ruido(s, o, 3.5, 12) * 0.3;
          return [x, y, (FL[j] + H[j]) * (1 - f) + (FL[j + 1] + H[j + 1]) * f + (cK - 0.5) * 0.5 * M];
        };
        const ok = (s, o) => { if (s < 0 || s > SF) return false; const j = Math.round(s / PASO), F = enC(s); return H[Math.min(NS - 1, j)] >= 0.4 * M && Math.abs(o) < 0.9 * F.hw; };
        grietas(V, sup, ok, 0);
      }
    }

    // ================= el lóbulo (el estado final del piroclastico: el frente quieto en r_fin)
    const FU = e.fuente, RF = e.r_fin;
    const dist = (u, v) => { let m = Infinity; for (const f of FU) { const d = Math.hypot(u - f[0], v - f[1]) + f[2]; if (d < m) m = d; } return m; };
    const fuera = (u, v) => {
      let best = Infinity, bi = 0;
      for (let i = 0; i < NC; i += 2) { const d = sq(u - C[i][0]) + sq(v - C[i][1]); if (d < best) { best = d; bi = i; } }
      const F = enC(C[bi][2]), o = ((u - F.u) * -F.tv + (v - F.v) * F.tu) * sgn(F);
      return e.lado === 0 ? Math.abs(o) < F.hw * 0.95 : o < F.hw * 1.05;
    };
    const HD = 2.4 + 0.6 * e.desborde;
    const grueso = (d, k) => {
      if (!(d < RF + 20)) return 0;
      const fin = HD * (0.55 + 0.45 * liso(RF, 0.45 * RF, d)) * liso(RF + 16, RF - 8, d);
      return fin * liso(RF + 10, RF - 14, d) * (0.85 + 0.3 * k);
    };
    if (RF > 0 && FU.length) {
      let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
      for (const f of FU) { u0 = Math.min(u0, f[0]); u1 = Math.max(u1, f[0]); v0 = Math.min(v0, f[1]); v1 = Math.max(v1, f[1]); }
      const R = RF + 40, B = e.caja;
      u0 = Math.max(B[0], u0 - R); u1 = Math.min(B[1], u1 + R); v0 = Math.max(B[2], v0 - R); v1 = Math.min(B[3], v1 + R);
      const st = Math.max(3, Math.sqrt((u1 - u0) * (v1 - v0) / 16000));
      const NA = Math.max(2, Math.ceil((u1 - u0) / st) + 1), NB = Math.max(2, Math.ceil((v1 - v0) / st) + 1), N = NA * NB;
      const pos = new Float32Array(N * 3), base = new Float32Array(N * 3), placa = new Float32Array(N), charco = new Float32Array(N);
      const V = voronoi(u0, u1, v0, v1, Lp, hm, 50000);
      const espesor = (u, v) => {
        if (fuera(u, v)) return 0;
        const n1 = ruido(u, v, 13, 21), n2 = ruido(u, v, 4, 22);
        return grueso(dist(u, v) + 14 * (n1 - 0.5), 0.75 * n1 + 0.25 * n2);
      };
      let alguno = false;
      for (let a = 0; a < NA; a++) for (let b = 0; b < NB; b++) {
        const q = a * NB + b, u = u0 + (u1 - u0) * a / (NA - 1), v = v0 + (v1 - v0) * b / (NB - 1);
        const [x, y] = W2(u, v), G = ctx.altura(x, y);
        const n1 = ruido(u, v, 13, 21), n2 = ruido(u, v, 4, 22);
        const D = fuera(u, v) ? Infinity : dist(u, v) + 14 * (n1 - 0.5), th = grueso(D, 0.75 * n1 + 0.25 * n2);
        const z = th > 0.12 ? G + th * M + 0.04 * M : G - 1.5 * M;
        if (th > 0.12) alguno = true;
        pos[q * 3] = x; pos[q * 3 + 1] = z; pos[q * 3 + 2] = -y;
        tono.copy(cDep).lerp(cRojo, liso(0.64, 0.82, n2) * 0.6).multiplyScalar(0.88 + 0.2 * n1).lerp(cDep2, 0.5);
        base[q * 3] = tono.r; base[q * 3 + 1] = tono.g; base[q * 3 + 2] = tono.b;
        placa[q] = hm(V.placa(u, v), 9);
        charco[q] = th > 1.2 ? liso(0.64, 0.8, ruido(u, v, 20, 14, hm)) : 0;
        if (th > 0.8 && (a * 3 + b * 7) % 9 === 0) GOTAS.push([x, y, z + 0.1 * M]);
      }
      if (alguno) {
        const m = lamina(NA, NB, pos);
        LAM.push({ m, N, base, L: vis(pos, NA, NB), placa, charco });
        const sup = (u, v) => { const [x, y] = W2(u, v); return [x, y, ctx.altura(x, y) + espesor(u, v) * M]; };
        const ok = (u, v) => espesor(u, v) > 0.9;
        grietas(V, sup, ok, 1);
      }
    }

    // ================= las grietas (una malla de cintas; cada tramo se abre desde su punta en su momento)
    let grieta = null;
    if (GR.length) {
      const NG = GR.length, g = new THREE.BufferGeometry(), gp = new Float32Array(NG * 12), gc = new Float32Array(NG * 12), idx = new Uint32Array(NG * 6);
      const lg = sombra(0, 1, 0);
      for (let k = 0; k < NG; k++) {
        const kk = 0.85 + 0.25 * hm(k, 8);
        for (let z = 0; z < 4; z++) { gc[k * 12 + z * 3] = cGrieta.r * lg * kk; gc[k * 12 + z * 3 + 1] = cGrieta.g * lg * kk; gc[k * 12 + z * 3 + 2] = cGrieta.b * lg * kk; }
        idx.set([k * 4, k * 4 + 1, k * 4 + 2, k * 4 + 1, k * 4 + 3, k * 4 + 2], k * 6);
      }
      g.setAttribute("position", new THREE.BufferAttribute(gp, 3)); g.setAttribute("color", new THREE.BufferAttribute(gc, 3)); g.setIndex(new THREE.BufferAttribute(idx, 1));
      const m = new THREE.Mesh(g, malla.material({ desfase: 4 })); m.frustumCulled = false; m.renderOrder = 5; m.visible = false; scene.add(m);
      grieta = { m, gp };
    }

    // ================= la lluvia (rayas con viento en una caja que va con la cámara)
    const uT = { value: 0 }, uPx = { value: 1 };
    const NLl = Math.round(900 + 5600 * cl01(e.lluvia)), gl = new THREE.BufferGeometry(), lp = new Float32Array(NLl * 6), le = new Float32Array(NLl * 2);
    for (let i = 0; i < NLl; i++) { const a = [hm(i, 150), hm(i, 151), hm(i, 152)]; lp.set(a, i * 6); lp.set(a, i * 6 + 3); le[i * 2] = 0; le[i * 2 + 1] = 1; }
    gl.setAttribute("position", new THREE.BufferAttribute(lp, 3)); gl.setAttribute("aE", new THREE.BufferAttribute(le, 1));
    const vi = [Math.cos(r + 2.2), -Math.sin(r + 2.2)];
    const matL = new THREE.ShaderMaterial({ uniforms: { uT, uC: { value: new THREE.Vector3() }, uS: { value: 300 }, uVel: { value: 9 * M }, uV: { value: new THREE.Vector2(vi[0], vi[1]) },
      cA: { value: cLluvia.clone() }, uA: { value: 0 } }, transparent: true, depthWrite: false,
      vertexShader: "uniform float uT, uS, uVel; uniform vec3 uC; uniform vec2 uV; attribute float aE; void main(){ vec3 q = position * uS; vec3 d = vec3(uV.x * 0.4, -1.0, uV.y * 0.4); q += d * uT * uVel; vec3 lo = uC - 0.5 * uS; vec3 w = lo + mod(q - lo, uS); w -= d * aE * uS * 0.018; gl_Position = projectionMatrix * viewMatrix * vec4(w, 1.0); }",
      fragmentShader: SRGB + "uniform vec3 cA; uniform float uA; void main(){ gl_FragColor = vec4(srgb(cA), uA); }" });
    const lluvia = new THREE.LineSegments(gl, matL); lluvia.frustumCulled = false; lluvia.renderOrder = 10; lluvia.visible = false; scene.add(lluvia);

    // ================= las gotas que salpican sobre el depósito (anillos que se abren; fase = función de t)
    let gotas = null;
    if (GOTAS.length) {
      const NGo = GOTAS.length, g = new THREE.BufferGeometry(), p = new Float32Array(NGo * 3), f = new Float32Array(NGo);
      GOTAS.forEach((G, i) => { p[i * 3] = G[0]; p[i * 3 + 1] = G[2]; p[i * 3 + 2] = -G[1]; f[i] = hm(i, 160); });
      g.setAttribute("position", new THREE.BufferAttribute(p, 3)); g.setAttribute("aF", new THREE.BufferAttribute(f, 1));
      const mat = new THREE.ShaderMaterial({ uniforms: { uT, uPx, uM: { value: M }, cA: { value: cGota.clone() }, uA: { value: 0 } }, transparent: true, depthWrite: false,
        vertexShader: "uniform float uT, uPx, uM; attribute float aF; varying float vP; void main(){ float ph = fract(uT * 1.6 + aF * 7.0); vP = ph; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = ph < 0.4 ? clamp((0.4 + 2.6 * ph / 0.4) * uM * uPx / max(1e-3, -mv.z), 1.0, 40.0) : 0.0; }",
        fragmentShader: SRGB + "uniform vec3 cA; uniform float uA; varying float vP; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float k = vP / 0.4; float d = r - 0.75 * k; float a = uA * (1.0 - k) * exp(-d * d * 18.0); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }" });
      const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = 9; m.visible = false; scene.add(m);
      gotas = { m, mat };
    }

    return { e, M, LAM, grieta, GR, lluvia, matL, gotas, uT, uPx, cDura, cDuraC, cAgua };
  }

  function dibujar(t, P, ctx) {
    const { e, M } = P, D = Math.max(0.5, e.dur), x = (t - e.t) / D, K = curva(e, x);
    // ---- el depósito: de la ceniza suelta (idéntica a la del piroclastico) a la costra mojada, por placas, con charcos
    for (const S of P.LAM) {
      const col = S.m.geometry.attributes.color.array;
      for (let q = 0; q < S.N; q++) {
        const pl = S.placa[q], ka = K.dura * (0.75 + 0.25 * pl);
        let rr = S.base[q * 3], gg = S.base[q * 3 + 1], bb = S.base[q * 3 + 2];
        const tr = P.cDura.r + (P.cDuraC.r - P.cDura.r) * pl * 0.55, tg = P.cDura.g + (P.cDuraC.g - P.cDura.g) * pl * 0.55, tb = P.cDura.b + (P.cDuraC.b - P.cDura.b) * pl * 0.55;
        rr += (tr - rr) * ka; gg += (tg - gg) * ka; bb += (tb - bb) * ka;
        const mo = 1 - 0.28 * K.moja; rr *= mo; gg *= mo; bb *= mo;
        const ch = S.charco[q] * K.charco * 0.7;
        rr += (P.cAgua.r - rr) * ch; gg += (P.cAgua.g - gg) * ch; bb += (P.cAgua.b - bb) * ch;
        const l = S.L[q]; col[q * 3] = rr * l; col[q * 3 + 1] = gg * l; col[q * 3 + 2] = bb * l;
      }
      S.m.geometry.attributes.color.needsUpdate = true; S.m.visible = true;
    }
    // ---- las grietas: cada tramo crece de su punta a la otra en 0.06 de dur
    if (P.grieta) {
      const gp = P.grieta.gp; let alguno = false;
      for (let k = 0; k < P.GR.length; k++) {
        const G = P.GR[k], g = cl01((x - G[6]) / 0.06), o = k * 12;
        if (g <= 0) { for (let z = 0; z < 4; z++) { gp[o + z * 3] = G[0]; gp[o + z * 3 + 1] = G[2]; gp[o + z * 3 + 2] = -G[1]; } continue; }
        alguno = true;
        const bx = G[0] + (G[3] - G[0]) * g, by = G[1] + (G[4] - G[1]) * g, bz = G[2] + (G[5] - G[2]) * g;
        const L = Math.hypot(G[3] - G[0], G[4] - G[1]) || 1, w = G[7] * 0.5 * (0.6 + 0.4 * liso(0, 1, g)), px = -(G[4] - G[1]) / L * w, py = (G[3] - G[0]) / L * w;
        const v = [[G[0] + px, G[1] + py, G[2]], [G[0] - px, G[1] - py, G[2]], [bx + px, by + py, bz], [bx - px, by - py, bz]];
        for (let z = 0; z < 4; z++) { gp[o + z * 3] = v[z][0]; gp[o + z * 3 + 1] = v[z][2]; gp[o + z * 3 + 2] = -v[z][1]; }
      }
      P.grieta.m.geometry.attributes.position.needsUpdate = true; P.grieta.m.visible = alguno;
    }
    // ---- la lluvia y las gotas
    P.uT.value = t;
    P.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
    const noche = !!ctx.ES.noche;
    if (K.lluvia > 0.002) {
      const dir = new ctx.THREE.Vector3(); ctx.camera.getWorldDirection(dir);
      const Dc = (ctx.cuadro && ctx.cuadro.dist) || 300 * M, S = ctx.clamp(Dc * 0.9, 30 * M, 900 * M);
      P.matL.uniforms.uS.value = S;
      P.matL.uniforms.uC.value.copy(ctx.camera.position).addScaledVector(dir, Math.min(Dc * 0.55, S * 0.5));
      P.matL.uniforms.uA.value = ((noche ? 0.2 : 0.26) + 0.3 * e.lluvia) * K.lluvia / Math.max(0.05, e.lluvia);
      P.lluvia.visible = true;
      if (P.gotas) { P.gotas.mat.uniforms.uA.value = (noche ? 0.45 : 0.6) * K.lluvia; P.gotas.m.visible = true; }
    }
  }

  const clave = (e) => [e.t, e.pieza, e.lluvia, e.costra, e.grietas].map(String).join("|");

  MAQ.EVENTOS.endurecer = {
    orden: 47,
    armar(ctx, lista) {
      return { lista, P: lista.map((e, i) => preparar(ctx, e, i)) };
    },
    inicio(t, st) {
      if (!st) return;
      for (const P of st.P) {
        for (const S of P.LAM) S.m.visible = false;
        if (P.grieta) P.grieta.m.visible = false;
        P.lluvia.visible = false; if (P.gotas) P.gotas.m.visible = false;
      }
    },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      let i = st.lista.indexOf(e); if (i < 0) { const k = clave(e); i = st.P.findIndex((P) => clave(P.e) === k); }
      if (i >= 0) dibujar(t, st.P[i], ctx);
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
