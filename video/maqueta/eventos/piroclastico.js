// Evento «piroclastico» (ficha: piroclastico.json; reglas: scripts/maqueta_tipos/piroclastico.py): un flujo piroclástico
// DE CERCA sobre una pieza `aldeabarranca` (o `faldavolcan`). Sin texto ni cifras: ilustra, no mide.
// - LOS PULSOS: lenguas de material que bajan por el cauce de la pieza una tras otra (salen rápido y frenan); cada una
//   rellena el fondo con su capa y, encima, una NUBE gris turbulenta (puntos blandos: la base densa y oscura, la cima más
//   clara que sube, se enrosca y se queda atrás). El último llega más lejos: junto al puente (aguas arriba: el puente
//   queda entero a la vista) sube sobre la orilla del lado de la aldea.
// - EL DESBORDE: un lóbulo que avanza por un campo de distancias medido desde esa orilla (`fuente`, cada punto con su
//   castigo: sale del desborde y corre orilla abajo), pasa sobre la carretera y entra a la aldea; deja ceniza gris de
//   ≈ 3 m (hasta el techo: los techos asoman), con bloques que ruedan en el frente (algunos rojizos y unos grandes) y
//   escombros (láminas y vigas) que asoman. La nube del frente sube donde llega y se deshace.
// - DESPUÉS: el depósito se oscurece (ceniza endurecida) y echa humo (`humo`); con `queda` se queda el resto del tramo.
// - LA GENTE (`gente`, `vacia`): vecinos en las calles que, antes de que llegue, caminan de prisa y dejan la calle; nadie
//   queda alcanzado. Sin `vacia`, dos vuelven al final a mirar desde fuera del depósito.
// Seek puro: todo sale de t (ningún estado entre cuadros); el azar es ctx.hash. Sin colores escritos.
(function (MAQ) {
  const TAU = 2 * Math.PI, PASO = 4, NW = 23, S0 = 40;
  const liso = (a, b, x) => { if (a === b) return x >= b ? 1 : 0; const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const cl01 = (x) => Math.min(1, Math.max(0, x));
  const sale = (p) => 1 - (1 - cl01(p)) * (1 - cl01(p));
  const sq = (v) => v * v;

  // ---- los pulsos: dónde va el frente de cada uno (m locales sobre el cauce) en la fracción x de `dur`
  function frentes(e, x) {
    const n = Math.max(1, e.pulsos | 0), XD = e.x_desb, out = [];
    for (let i = 0; i < n; i++) {
      const ult = i === n - 1, x0 = n > 1 ? 0.42 * i / (n - 1) : 0;
      if (x < x0) { out.push(null); continue; }
      if (!ult) {
        const S = e.s_spill * (0.5 + 0.4 * i / Math.max(1, n - 1)), p = (x - x0) / 0.26;
        out.push({ s: S0 + (S - S0) * sale(p), mov: 1 - liso(0.75, 1, p), fin: x0 + 0.26 });
      } else if (x < XD) {
        const p = cl01((x - x0) / Math.max(0.05, XD - x0));
        out.push({ s: S0 + (e.s_spill - S0) * Math.pow(p, 0.85), mov: 1, fin: XD + 0.3 });
      } else {
        const p = (x - XD) / 0.3;
        out.push({ s: e.s_spill + (e.s_fin - e.s_spill) * sale(p), mov: 1 - liso(0.7, 1, p), fin: XD + 0.3 });
      }
    }
    return out;
  }
  const radio = (e, x) => e.r_fin * sale((x - e.x_desb) / (0.95 - e.x_desb));
  const llega = (e, d) => {                      // la fracción x en que el lóbulo alcanza la distancia d
    if (d >= e.r_fin) return 9;
    const q = 1 - Math.sqrt(Math.max(0, 1 - d / e.r_fin));
    return e.x_desb + q * (0.95 - e.x_desb);
  };

  function preparar(ctx, e, ie) {
    const { THREE, malla, tonos, lin, COL, ES, hash, scene, metros } = ctx;
    const oscuro = ES.modo === 1, noche = !!ES.noche;
    const M = metros(1) * e.tamano, n = Math.max(1, e.pulsos | 0);
    const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
    const W2 = (u, v) => [e.fx + (u * ux - v * uy) * M, e.fy + (u * uy + v * ux) * M];
    const gz = (u, v) => { const [x, y] = W2(u, v); return ctx.altura(x, y); };
    const hz = (i, k) => hash(i + 6151 * (ie + 1) + (e.semilla | 0) * 97, k);
    const ruido = (a, b, cel, k) => {
      const fx = a / cel, fy = b / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
      const v = (p, q) => hz((p & 4095) * 4099 + (q & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
    };

    // ---- los tonos (del estilo)
    const cDep = tonos.asfalto.clone().lerp(tonos.muro, 0.35).lerp(tonos.arena, 0.1).multiplyScalar(oscuro ? 1.15 : ES.dia ? 0.5 : 0.62);
    const cDep2 = cDep.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.82);           // ceniza endurecida
    const cFresco = cDep.clone().lerp(tonos.muro, 0.25).multiplyScalar(oscuro ? 1.2 : 1.25);
    const cRojo = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.55).lerp(cDep, 0.35).multiplyScalar(oscuro ? 0.95 : 0.8);
    const cRoca = tonos.muro.clone().lerp(tonos.asfalto, 0.6).multiplyScalar(oscuro ? 1.05 : 0.7);
    const cLam = tonos.pavimento.clone().lerp(tonos.muro, 0.3).lerp(cDep, 0.3);
    const cOxido = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.6).multiplyScalar(0.75);
    const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
    const cNubeB = cDep.clone().lerp(tonos.asfalto, 0.2).multiplyScalar(oscuro ? 0.7 : 1.05);
    const cNubeA = tonos.muro.clone().lerp(tonos.arena, 0.35).lerp(cDep, 0.3).multiplyScalar(oscuro ? 0.62 : noche ? 0.8 : 1.08);

    // ---- el cauce: punto, tangente y medio ancho a la distancia s
    const C = e.cauce, NC = C.length;
    const enC = (s) => {
      s = Math.min(C[NC - 1][2], Math.max(0, s));
      let i = 1; while (i < NC - 1 && C[i][2] < s) i++;
      const a = C[i - 1], b = C[i], f = (s - a[2]) / ((b[2] - a[2]) || 1e-9), L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return { u: a[0] + (b[0] - a[0]) * f, v: a[1] + (b[1] - a[1]) * f, tu: (b[0] - a[0]) / L, tv: (b[1] - a[1]) / L, hw: a[3] + (b[3] - a[3]) * f };
    };
    // el lado de la aldea: la normal izquierda (−tv, tu) si apunta hacia `lado` en v; con lado 0, los dos
    const sgn = (F) => (e.lado === 0 ? 1 : (F.tu * e.lado >= 0 ? 1 : -1));

    // ================= el relleno del cauce (filas a lo largo de s, NW columnas de orilla a orilla)
    const SF = Math.min(C[NC - 1][2], e.s_fin + 40), NS = Math.max(2, Math.ceil(SF / PASO) + 1), NV = NS * NW;
    const cXY = new Float32Array(NV * 2), cW = new Float32Array(NV), cK = new Float32Array(NV), cB = new Float32Array(NV * 3);
    const RS = new Float32Array(NS), FL = new Float32Array(NS), HC = new Float32Array(NS), RV = new Float32Array(NS), RO = new Float32Array(NS), HWs = new Float32Array(NS);
    for (let j = 0; j < NS; j++) {
      const s = Math.min(SF, j * PASO), F = enC(s), nu = -F.tv, nv = F.tu, sv = sgn(F);
      RS[j] = s; HWs[j] = F.hw; FL[j] = gz(F.u, F.v);
      RV[j] = gz(F.u + nu * sv * 1.35 * F.hw, F.v + nv * sv * 1.35 * F.hw);           // la orilla del lado de la aldea
      RO[j] = gz(F.u - nu * sv * 1.35 * F.hw, F.v - nv * sv * 1.35 * F.hw);           // la otra
      HC[j] = Math.max(2 * M, Math.min(RV[j], RO[j]) - FL[j]);
      for (let i = 0; i < NW; i++) {
        const w = -1.3 + 2.6 * i / (NW - 1), q = j * NW + i, uu = F.u + nu * w * F.hw, vv = F.v + nv * w * F.hw;
        const [x, y] = W2(uu, vv); cXY[q * 2] = x; cXY[q * 2 + 1] = y; cW[q] = w * sv;
        const n1 = ruido(s, w * F.hw, 9, 11), n2 = ruido(s, w * F.hw, 3.5, 12);
        cK[q] = n1 * 0.7 + n2 * 0.3;
        const c = cDep.clone().lerp(cRojo, liso(0.62, 0.8, n2) * 0.7).multiplyScalar(0.9 + 0.18 * n1);
        cB[q * 3] = c.r; cB[q * 3 + 1] = c.g; cB[q * 3 + 2] = c.b;
      }
    }
    const malla2 = (NA, NB) => {
      const idx = [];
      for (let j = 0; j + 1 < NA; j++) for (let i = 0; i + 1 < NB; i++) { const a = j * NB + i, b = a + 1, c = a + NB, d = c + 1; idx.push(a, c, b, b, c, d); }
      const g = new THREE.BufferGeometry(), N = NA * NB;
      g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
      g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
      g.setIndex(N > 65535 ? new THREE.BufferAttribute(new Uint32Array(idx), 1) : new THREE.BufferAttribute(new Uint16Array(idx), 1));
      const m = new THREE.Mesh(g, malla.material({})); m.frustumCulled = false; m.renderOrder = 3; m.visible = false; scene.add(m);
      return m;
    };
    const relleno = malla2(NS, NW);
    // el bulto del último pulso: sube sobre la orilla de la aldea en s_spill (aguas arriba del puente)
    const BU = new Float32Array(NS);
    for (let j = 0; j < NS; j++) {
      const ds = RS[j] - e.s_spill, g = Math.exp(-sq(ds / (ds < 0 ? 70 : 32)));
      const meta = RV[j] + (0.6 + 1.8 * e.desborde) * M;
      BU[j] = e.desborde < 0.15 ? 0 : Math.max(0, meta - (FL[j] + 0.55 * HC[j])) * g;
    }

    // ================= el lóbulo (malla en u, v locales sobre la caja que alcanza)
    const FU = e.fuente, RF = e.r_fin;
    const dist = (u, v) => { let m = Infinity; for (const f of FU) { const d = Math.hypot(u - f[0], v - f[1]) + f[2]; if (d < m) m = d; } return m; };
    const fuera = (u, v) => {                      // ¿cae dentro del cauce o al otro lado? (ahí el lóbulo no va)
      let best = Infinity, bi = 0;
      for (let i = 0; i < NC; i += 2) { const d = sq(u - C[i][0]) + sq(v - C[i][1]); if (d < best) { best = d; bi = i; } }
      const F = enC(C[bi][2]), o = ((u - F.u) * -F.tv + (v - F.v) * F.tu) * sgn(F);
      return e.lado === 0 ? Math.abs(o) < F.hw * 0.95 : o < F.hw * 1.05;
    };
    let lob = null;
    if (RF > 0 && FU.length) {
      let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
      for (const f of FU) { u0 = Math.min(u0, f[0]); u1 = Math.max(u1, f[0]); v0 = Math.min(v0, f[1]); v1 = Math.max(v1, f[1]); }
      const R = RF + 40, B = e.caja;
      u0 = Math.max(B[0], u0 - R); u1 = Math.min(B[1], u1 + R); v0 = Math.max(B[2], v0 - R); v1 = Math.min(B[3], v1 + R);
      const st = Math.max(3, Math.sqrt((u1 - u0) * (v1 - v0) / 16000));
      const NA = Math.max(2, Math.ceil((u1 - u0) / st) + 1), NB = Math.max(2, Math.ceil((v1 - v0) / st) + 1), N = NA * NB;
      const XY = new Float32Array(N * 2), UV = new Float32Array(N * 2), G = new Float32Array(N), D = new Float32Array(N), K = new Float32Array(N), BC = new Float32Array(N * 3);
      const dentro = [];
      for (let a = 0; a < NA; a++) for (let b = 0; b < NB; b++) {
        const q = a * NB + b, u = u0 + (u1 - u0) * a / (NA - 1), v = v0 + (v1 - v0) * b / (NB - 1);
        const [x, y] = W2(u, v); XY[q * 2] = x; XY[q * 2 + 1] = y; UV[q * 2] = u; UV[q * 2 + 1] = v; G[q] = ctx.altura(x, y);
        const n1 = ruido(u, v, 13, 21), n2 = ruido(u, v, 4, 22);
        D[q] = fuera(u, v) ? Infinity : dist(u, v) + 14 * (n1 - 0.5);
        K[q] = 0.75 * n1 + 0.25 * n2;
        const c = cDep.clone().lerp(cRojo, liso(0.64, 0.82, n2) * 0.6).multiplyScalar(0.88 + 0.2 * n1);
        BC[q * 3] = c.r; BC[q * 3 + 1] = c.g; BC[q * 3 + 2] = c.b;
        if (D[q] < RF * 0.97) dentro.push(q);
      }
      lob = { m: malla2(NA, NB), NA, NB, N, XY, UV, G, D, K, BC, dentro };
    }
    const HD = (2.4 + 0.6 * e.desborde);            // m: el espesor del lóbulo (hasta el techo de una casa sencilla)
    // el espesor del lóbulo (m) a la distancia d con el frente en R (mov: 1 mientras avanza)
    const grueso = (d, R, mov, k) => {
      if (!(d < RF + 20)) return 0;
      const fin = HD * (0.55 + 0.45 * liso(RF, 0.45 * RF, d)) * liso(RF + 16, RF - 8, d);
      const fr = liso(R + 10, R - 14, d), cab = 0.5 * mov * Math.exp(-sq((R - d - 12) / 12));
      return fin * fr * (1 + cab) * (0.85 + 0.3 * k);
    };

    // ================= bloques y escombros (una malla que se rehace en cada cuadro)
    const tri = (geo) => Array.from(geo.toNonIndexed().attributes.position.array);
    const ICO = tri(new THREE.IcosahedronGeometry(1, 1)), CAJA = tri(new THREE.BoxGeometry(1, 1, 1));
    const cosas = [];
    const NBk = Math.max(0, e.bloques | 0);
    for (let i = 0; i < NBk; i++) {
      const grande = hz(i, 1) < 0.18, rr = grande ? 2.2 + 1.2 * hz(i, 2) : 0.6 + 1.3 * Math.pow(hz(i, 3), 1.4);
      const sx = 1 + 0.35 * (hz(i, 4) - 0.5), sy = 0.7 + 0.25 * hz(i, 5), sz = 1 + 0.35 * (hz(i, 6) - 0.5);
      // la roca: un icosaedro abollado (cada vértice movido por su posición: las caras siguen cerradas)
      const V = ICO.map((x, o) => x * [sx, sy, sz][o % 3] * rr);
      for (let o = 0; o < V.length; o += 3) { const k = 0.82 + 0.3 * hash(Math.round(ICO[o] * 97) * 7 + Math.round(ICO[o + 1] * 89) * 131 + Math.round(ICO[o + 2] * 83) * 1543 + i * 11, 7);
        V[o] *= k; V[o + 1] *= k; V[o + 2] *= k; }
      const col = (hz(i, 8) < 0.35 ? cRojo : cRoca).clone().multiplyScalar(0.85 + 0.3 * hz(i, 9));
      const enLob = lob && lob.dentro.length && i % 3 !== 2;
      const c = { clase: "roca", r: rr, V, col, q0: new THREE.Quaternion().setFromEuler(new THREE.Euler(TAU * hz(i, 10), TAU * hz(i, 11), TAU * hz(i, 12))) };
      if (enLob) {
        const q = lob.dentro[Math.floor(hz(i, 13) * lob.dentro.length)], u = lob.UV[q * 2], v = lob.UV[q * 2 + 1];
        let fb = FU[0], m = Infinity; for (const f of FU) { const d = Math.hypot(u - f[0], v - f[1]) + f[2]; if (d < m) { m = d; fb = f; } }
        Object.assign(c, { lob: true, u, v, d: lob.D[q], bu: fb[0], bv: fb[1], pen: fb[2] });
      } else {
        Object.assign(c, { lob: false, s: (0.3 + 0.68 * hz(i, 14)) * Math.min(e.s_fin, e.s_spill + 60), w: (hz(i, 15) - 0.5) * 1.3, pul: n - 1 - (i % Math.min(2, n)) });
      }
      cosas.push(c);
    }
    if (lob && lob.dentro.length) {
      for (let i = 0; i < 16; i++) {               // láminas de los techos y vigas que asoman del depósito
        const k = 200 + i, q = lob.dentro[Math.floor(hz(k, 1) * lob.dentro.length)], lam = i < 10;
        const sc = lam ? [2.0 + 1.2 * hz(k, 2), 0.06, 0.8 + 0.3 * hz(k, 3)] : [0.16, 0.16, 2.6 + 2 * hz(k, 4)];
        const V = CAJA.map((x, o) => x * sc[o % 3]);
        const col = (lam ? (hz(k, 5) < 0.3 ? cOxido : cLam) : cMadera).clone().multiplyScalar(0.85 + 0.25 * hz(k, 6));
        cosas.push({ clase: "resto", V, col, u: lob.UV[q * 2], v: lob.UV[q * 2 + 1], d: lob.D[q], hund: lam ? 0.1 : 0.05,
          q0: new THREE.Quaternion().setFromEuler(new THREE.Euler(0.25 + 0.6 * (hz(k, 7) - 0.5), TAU * hz(k, 8), 0.5 * (hz(k, 9) - 0.5))) });
      }
    }
    let NT = 0; for (const c of cosas) NT += c.V.length / 9;
    const gd = new THREE.BufferGeometry(), dpos = new Float32Array(Math.max(1, NT) * 9), dcol = new Float32Array(Math.max(1, NT) * 9);
    gd.setAttribute("position", new THREE.BufferAttribute(dpos, 3)); gd.setAttribute("color", new THREE.BufferAttribute(dcol, 3));
    const restos = new THREE.Mesh(gd, malla.material({})); restos.frustumCulled = false; restos.renderOrder = 3; restos.visible = false; scene.add(restos);

    // ================= la nube y el humo (puntos blandos; posiciones de cada cuadro)
    const KN = noche ? 0.7 : 1, PC = 170, LC = lob && lob.dentro.length ? 260 : 0, SM = e.humo ? 220 : 0, NPt = n * PC + LC + SM;
    const gp = new THREE.BufferGeometry(), ppos = new Float32Array(NPt * 3), pA = new Float32Array(NPt * 3);
    gp.setAttribute("position", new THREE.BufferAttribute(ppos, 3)); gp.setAttribute("aP", new THREE.BufferAttribute(pA, 3));
    const uPx = { value: 1 };
    const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
    const matN = new THREE.ShaderMaterial({ uniforms: { uPx, cB: { value: cNubeB }, cA: { value: cNubeA } }, transparent: true, depthWrite: false,
      vertexShader: "uniform float uPx; attribute vec3 aP; varying float vA, vS; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aP.x > 0.002 ? clamp(aP.y * uPx / max(1e-3, -mv.z), 1.5, 420.0) : 0.0; vA = aP.x; vS = aP.z; }",
      fragmentShader: SRGB + "uniform vec3 cB, cA; varying float vA, vS; void main(){ vec2 p = gl_PointCoord - 0.5; float r = length(p) * 2.0; if (r > 1.0) discard; float a = vA * exp(-r * r * 2.4); if (a < 0.004) discard; float l = 0.82 + 0.3 * clamp(0.5 - p.y, 0.0, 1.0); gl_FragColor = vec4(srgb(mix(cB, cA, vS) * l), a); }" });
    const nube = new THREE.Points(gp, matN); nube.frustumCulled = false; nube.renderOrder = 8; nube.visible = false; scene.add(nube);
    const part = [];
    for (let i = 0; i < NPt; i++) part.push([hz(i + 900, 1), hz(i + 900, 2), hz(i + 900, 3), hz(i + 900, 4), hz(i + 900, 5), hz(i + 900, 6)]);
    const lobPick = (i, k) => lob.dentro[Math.floor(hz(i + 1700, k) * lob.dentro.length)];

    return { KN, e, M, W2, gz, n, relleno, lob, restos, nube, ppos, pA, part, lobPick, uPx, cosas, dpos, dcol, grueso, dist, enC, sgn,
      NS, NV, cXY, cW, cK, cB, RS, FL, HC, RV, RO, BU, HWs, PC, LC, SM, cFresco, cDep2,
      tmp: { m: new THREE.Matrix4(), q: new THREE.Quaternion(), v: new THREE.Vector3(), s: new THREE.Vector3(), ax: new THREE.Vector3() } };
  }

  // la cota (unidades) del relleno del cauce en la fila j con los frentes F
  function nivel(P, j, F, e) {
    const s = P.RS[j], n = P.n;
    let h = 0;
    for (let i = 0; i < n; i++) {
      const f = F[i]; if (!f) continue;
      const d = f.s - s; if (d <= 0) continue;
      const fr = n > 1 ? 0.55 / n * (0.6 + 0.8 * i / (n - 1)) : 0.55;
      const a = liso(0, 40, d) * (1 + 0.35 * f.mov * Math.exp(-sq((d - 15) / 14)));
      h += fr * P.HC[j] * a;
      if (i === n - 1) h += P.BU[j] * liso(0, 30, d);
    }
    return h;
  }

  function dibujar(t, P, ctx) {
    const { e, M } = P, { sombra, THREE } = ctx, D = Math.max(0.5, e.dur), tr = t - e.t, x = tr / D;
    const F = frentes(e, x), R = radio(e, x), movL = 1 - liso(0.85, 0.98, x);
    const se = e.queda ? 1 : 1 - liso(D + 0.5, D + 2.5, tr);   // sin `queda`, el depósito se va al terminar
    const viejo = liso(D * 0.95, D * 0.95 + 4, tr);             // la ceniza se oscurece al enfriarse
    const vis = (pos, col, NA, NB) => {                          // normales y luz horneada de una lámina
      for (let a = 0; a < NA; a++) for (let b = 0; b < NB; b++) {
        const q = a * NB + b, qa = a * NB + Math.max(0, b - 1), qb = a * NB + Math.min(NB - 1, b + 1), qc = Math.max(0, a - 1) * NB + b, qd = Math.min(NA - 1, a + 1) * NB + b;
        const ax = pos[qb * 3] - pos[qa * 3], ay = pos[qb * 3 + 1] - pos[qa * 3 + 1], az = pos[qb * 3 + 2] - pos[qa * 3 + 2];
        const bx = pos[qd * 3] - pos[qc * 3], by = pos[qd * 3 + 1] - pos[qc * 3 + 1], bz = pos[qd * 3 + 2] - pos[qc * 3 + 2];
        let nx = ay * bz - az * by, ny = az * bx - ax * bz, nz = ax * by - ay * bx;
        const nn = Math.hypot(nx, ny, nz) || 1; nx /= nn; ny /= nn; nz /= nn; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx, ny, nz); col[q * 3] *= l; col[q * 3 + 1] *= l; col[q * 3 + 2] *= l;
      }
    };
    // ---- el relleno del cauce
    {
      const g = P.relleno.geometry, pos = g.attributes.position.array, col = g.attributes.color.array, { NS, cXY, cW, cK, cB, FL, RV, RO } = P;
      let alguno = false;
      for (let j = 0; j < NS; j++) {
        const h = nivel(P, j, F, e) * se, L = FL[j] + h;
        let fres = 0; for (const f of F) if (f) fres = Math.max(fres, f.mov * Math.exp(-Math.max(0, f.s - P.RS[j]) / 22) * (f.s > P.RS[j] ? 1 : 0));
        for (let i = 0; i < NW; i++) {
          const q = j * NW + i, w = cW[q], aw = Math.abs(w);
          const ola = 0.3 * M * fres * Math.sin(0.4 * P.RS[j] - 6 * tr + 3 * w + 7 * cK[q]);
          let z = L + ola + (cK[q] - 0.5) * 0.5 * M;
          if (aw > 1) { const rim = w > 0 ? RV[j] : RO[j]; z = Math.min(z, rim + 0.8 * M * (1.3 - aw) / 0.3); }
          if (h < 0.15 * M) z = FL[j] - 3 * M; else alguno = true;
          pos[q * 3] = cXY[q * 2]; pos[q * 3 + 1] = z; pos[q * 3 + 2] = -cXY[q * 2 + 1];
          const k = 0.6 * fres;
          let rr = cB[q * 3], gg = cB[q * 3 + 1], bb = cB[q * 3 + 2];
          rr += (P.cDep2.r - rr) * viejo * 0.5; gg += (P.cDep2.g - gg) * viejo * 0.5; bb += (P.cDep2.b - bb) * viejo * 0.5;
          col[q * 3] = rr + (P.cFresco.r - rr) * k; col[q * 3 + 1] = gg + (P.cFresco.g - gg) * k; col[q * 3 + 2] = bb + (P.cFresco.b - bb) * k;
        }
      }
      vis(pos, col, NS, NW);
      g.attributes.position.needsUpdate = true; g.attributes.color.needsUpdate = true; P.relleno.visible = alguno;
    }
    // ---- el lóbulo
    const L = P.lob;
    if (L) {
      const g = L.m.geometry, pos = g.attributes.position.array, col = g.attributes.color.array;
      let alguno = false;
      for (let q = 0; q < L.N; q++) {
        const d = L.D[q], th = R > 0 ? P.grueso(d, R, movL, L.K[q]) * se : 0;
        const ola = th > 0 ? 0.25 * movL * Math.exp(-sq((R - d - 10) / 16)) * Math.sin(0.3 * d - 7 * tr + 6 * L.K[q]) : 0;
        const z = th > 0.12 ? L.G[q] + (th + ola) * M : L.G[q] - 1.5 * M;
        if (th > 0.12) alguno = true;
        pos[q * 3] = L.XY[q * 2]; pos[q * 3 + 1] = z; pos[q * 3 + 2] = -L.XY[q * 2 + 1];
        const k = 0.65 * movL * Math.exp(-sq((R - d - 8) / 18));
        let rr = L.BC[q * 3], gg = L.BC[q * 3 + 1], bb = L.BC[q * 3 + 2];
        rr += (P.cDep2.r - rr) * viejo * 0.5; gg += (P.cDep2.g - gg) * viejo * 0.5; bb += (P.cDep2.b - bb) * viejo * 0.5;
        col[q * 3] = rr + (P.cFresco.r - rr) * k; col[q * 3 + 1] = gg + (P.cFresco.g - gg) * k; col[q * 3 + 2] = bb + (P.cFresco.b - bb) * k;
      }
      vis(pos, col, L.NA, L.NB);
      g.attributes.position.needsUpdate = true; g.attributes.color.needsUpdate = true; L.m.visible = alguno;
    }
    // la superficie del depósito en (u, v) locales (lóbulo) y en (s, w) del cauce
    const sobreLob = (u, v) => { const d = P.dist(u, v); return P.gz(u, v) + P.grueso(d, R, movL, 0.5) * se * M; };
    const sobreCau = (s, w) => {
      const j = Math.min(P.NS - 1, Math.max(0, Math.round(s / PASO))), C = P.enC(s), nu = -C.tv, nv = C.tu;
      const [X, Y] = P.W2(C.u + nu * w * C.hw * P.sgn(C), C.v + nv * w * C.hw * P.sgn(C));
      return { x: X, y: Y, z: P.FL[j] + nivel(P, j, F, e) * se, h: nivel(P, j, F, e), C };
    };
    // ---- bloques y escombros
    {
      const { dpos, dcol, tmp } = P;
      let nt = 0;
      const pegar = (c, X, Y, Z, q) => {
        tmp.s.set(M, M, M); tmp.v.set(X, Z, -Y); tmp.m.compose(tmp.v, q, tmp.s);
        const m = tmp.m.elements, V = c.V;
        for (let o = 0; o < V.length; o += 9) {
          const pt = [];
          for (let z = 0; z < 3; z++) { const a = V[o + z * 3], b = V[o + z * 3 + 1], cc = V[o + z * 3 + 2];
            pt.push([m[0] * a + m[4] * b + m[8] * cc + m[12], m[1] * a + m[5] * b + m[9] * cc + m[13], m[2] * a + m[6] * b + m[10] * cc + m[14]]); }
          const e1 = [pt[1][0] - pt[0][0], pt[1][1] - pt[0][1], pt[1][2] - pt[0][2]], e2 = [pt[2][0] - pt[0][0], pt[2][1] - pt[0][1], pt[2][2] - pt[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const nn = Math.hypot(nx, ny, nz) || 1, l = sombra(nx / nn, ny / nn, nz / nn);
          for (let z = 0; z < 3; z++) { dpos.set(pt[z], nt * 9 + z * 3); dcol[nt * 9 + z * 3] = c.col.r * l; dcol[nt * 9 + z * 3 + 1] = c.col.g * l; dcol[nt * 9 + z * 3 + 2] = c.col.b * l; }
          nt++;
        }
      };
      const rumbo = e.rumbo * Math.PI / 180, ru = Math.cos(rumbo), rv = Math.sin(rumbo);
      const rodar = (du, dv, ang, q0) => {          // gira `ang` alrededor del eje horizontal perpendicular a (du, dv) locales
        const X = du * ru - dv * rv, Y = du * rv + dv * ru, n = Math.hypot(X, Y) || 1;
        tmp.ax.set(-Y / n, 0, -X / n); return tmp.q.setFromAxisAngle(tmp.ax, ang).multiply(q0);
      };
      for (const c of P.cosas) {
        if (c.clase === "roca" && c.lob) {
          if (!(R > c.pen + 2) || se <= 0) continue;
          const f = Math.min(1, (R - c.pen) / Math.max(1, c.d - c.pen)), u = c.bu + (c.u - c.bu) * f, v = c.bv + (c.v - c.bv) * f;
          const camino = Math.hypot(c.u - c.bu, c.v - c.bv) * f, [X, Y] = P.W2(u, v);
          pegar(c, X, Y, sobreLob(u, v) + (0.25 - 0.15 * f) * c.r * M * se, rodar(c.u - c.bu, c.v - c.bv, -camino / c.r, c.q0));
        } else if (c.clase === "roca") {
          const f = F[Math.max(0, Math.min(P.n - 1, c.pul))]; if (!f || se <= 0) continue;
          const s = Math.min(f.s - 6, c.s); if (s < 2) continue;
          const S = sobreCau(s, c.w); if (S.h < 0.3 * M) continue;
          pegar(c, S.x, S.y, S.z + 0.2 * c.r * M, rodar(S.C.tu, S.C.tv, -s / c.r, c.q0));
        } else {
          const lleva = R - c.d; if (lleva <= 0 || se <= 0) continue;
          const sube = liso(0, 10, lleva), [X, Y] = P.W2(c.u, c.v);
          pegar(c, X, Y, sobreLob(c.u, c.v) - (c.hund + 1.2 * (1 - sube)) * M, c.q0);
        }
      }
      P.restos.geometry.setDrawRange(0, nt * 3);
      P.restos.geometry.attributes.position.needsUpdate = true; P.restos.geometry.attributes.color.needsUpdate = true;
      P.restos.visible = nt > 0;
    }
    // ---- la nube de los pulsos, la del frente del lóbulo y el humo del depósito
    {
      const { ppos, pA, part, PC, LC, SM, KN } = P;
      let o = 0, alguno = false;
      const pon = (X, Y, Z, a, tam, sh) => { ppos[o * 3] = X; ppos[o * 3 + 1] = Z; ppos[o * 3 + 2] = -Y; pA[o * 3] = a * KN; pA[o * 3 + 1] = tam * M; pA[o * 3 + 2] = sh; if (a > 0.002) alguno = true; o++; };
      for (let i = 0; i < P.n; i++) {
        const f = F[i], x0 = P.n > 1 ? 0.42 * i / (P.n - 1) : 0;
        for (let k = 0; k < PC; k++) {
          const h = part[i * PC + k];
          if (!f) { pon(0, 0, 0, 0, 0, 0); continue; }
          const tq = Math.max(0, (x - f.fin) * D);                       // segundos desde que el pulso se detuvo
          const fade = 1 - liso(0, 3.2, tq), b = -8 + 120 * Math.pow(h[0], 1.25), s = f.s - b;
          if (s < 1 || fade <= 0) { pon(0, 0, 0, 0, 0, 0); continue; }
          const w = (h[1] - 0.5) * 2.4, sube = Math.pow(cl01(b / 120), 0.8);
          const S = sobreCau(s, w);
          const alto = (2 + 28 * sube * (0.7 + 0.3 * i / P.n) + 7 * h[2]) + 4 * tq * (0.5 + h[3]);
          const gi = tr * (0.8 + 0.6 * h[4]) + TAU * h[5];
          const X = S.x + 4 * M * Math.sin(gi) * (0.3 + sube), Y = S.y + 4 * M * Math.cos(1.3 * gi) * (0.3 + sube);
          const tam = (7 + 18 * sube + 7 * h[3]) * (1 + 0.35 * tq / 3.2);
          const a = (0.62 - 0.32 * sube) * fade * liso(-8, 4, b) * liso(1, 12, s) * (0.7 + 0.3 * h[2]);
          pon(X, Y, S.z + alto * M, a, tam, cl01(0.15 + 0.85 * sube));
        }
      }
      if (LC) {
        for (let k = 0; k < LC; k++) {
          const h = part[P.n * PC + k], q = P.lobPick(k, 1), d = P.lob.D[q];
          const ta = (x - llega(e, d)) * D;                               // segundos desde que el frente llegó aquí
          if (!(ta > -0.3) || ta > 4.2) { pon(0, 0, 0, 0, 0, 0); continue; }
          const p = cl01((ta + 0.3) / 4.5), X = P.lob.XY[q * 2] + 3 * M * Math.sin(TAU * h[0] + 1.5 * tr), Y = P.lob.XY[q * 2 + 1] + 3 * M * Math.cos(TAU * h[1] + 1.2 * tr);
          const z = P.lob.G[q] + (HDm(P) + 3 + 30 * Math.pow(p, 0.7) + 5 * h[2]) * M;
          pon(X, Y, z, 0.55 * Math.pow(Math.sin(Math.PI * p), 0.7) * (0.7 + 0.3 * h[3]), 8 + 16 * p + 5 * h[4], cl01(0.2 + 0.8 * p));
        }
      }
      if (SM) {
        for (let k = 0; k < SM; k++) {
          const h = part[P.n * PC + LC + k], col = Math.floor(k / 4), j = k % 4;
          let X, Y, Z, ta;
          if (P.lob && P.lob.dentro.length && col % 3 !== 0) {
            const q = P.lobPick(col, 3), d = P.lob.D[q];
            ta = (x - llega(e, d)) * D - 1; X = P.lob.XY[q * 2]; Y = P.lob.XY[q * 2 + 1];
            Z = P.lob.G[q] + P.grueso(d, R, movL, P.lob.K[q]) * se * M;
          } else {
            const hs = P.part[col % P.part.length], s = (0.15 + 0.8 * hs[0]) * e.s_fin, S = sobreCau(s, (hs[1] - 0.5) * 1.4);
            let fx = 0; for (const f of F) if (f && f.s > s) fx = 1;
            ta = fx ? tr - 1.5 - 3 * hs[2] : -1; X = S.x; Y = S.y; Z = S.z;
          }
          if (!(ta > 0) || se <= 0) { pon(0, 0, 0, 0, 0, 0); continue; }
          const a = ((t / 8 + h[0] + j / 4) % 1 + 1) % 1, k2 = liso(0, 2, ta) * (1 - 0.5 * liso(0, 25, ta));
          const vi = 0.5 + 0.5 * Math.sin(TAU * h[1]);
          pon(X + vi * a * a * 9 * M, Y + (1 - vi) * a * a * 9 * M, Z + a * 22 * M, 0.26 * k2 * (1 - a) * liso(0, 0.15, a), 3 + 9 * a, 0.75);
        }
      }
      P.nube.geometry.attributes.position.needsUpdate = true; P.nube.geometry.attributes.aP.needsUpdate = true;
      P.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      P.nube.visible = alguno;
    }
  }
  const HDm = (P) => 2.4 + 0.6 * P.e.desborde;

  // ---- la gente que pone el evento: camina por su calle y, antes de que llegue, la deja (seek puro)
  function gente(t, P, ctx) {
    const { e } = P, G = P.g; if (!G) return;
    const r = e.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r), dW = (du, dv) => [du * ux - dv * uy, du * uy + dv * ux];
    e.gente.forEach((g, i) => {
      const ts = e.t + g[4], h = ctx.hash(i + 77, 3), pre = (tt) => { const ph = ((tt * 1.0 / 10 + h) % 1 + 1) % 1, tri = ph < 0.5 ? ph * 2 : 2 - ph * 2; return { o: tri * 10 - 5, sg: ph < 0.5 ? 1 : -1 }; };
      let u, v, du, dv, k = 1, vel;
      if (t < ts) { const p = pre(t); u = g[0] + g[2] * p.o; v = g[1] + g[3] * p.o; du = g[2] * p.sg; dv = g[3] * p.sg; vel = 1.0; }
      else {
        const p = pre(ts), tau = t - ts; u = g[0] + g[2] * (p.o + 3 * tau); v = g[1] + g[3] * (p.o + 3 * tau); du = g[2]; dv = g[3]; vel = 3.0;
        k = 1 - liso(1.2, 2.5, tau);
      }
      const [x, y] = P.W2(u, v), [dx, dy] = dW(du, dv);
      G.poner(i, x, y, dx, dy, Math.max(0, k), 0, k > 0 ? vel : 0);
    });
    e.miran.forEach((g, j) => {
      const k = liso(e.t + e.dur * 0.97, e.t + e.dur * 0.97 + 0.8, t), [x, y] = P.W2(g[0], g[1]), [dx, dy] = dW(g[2], g[3]);
      G.poner(e.gente.length + j, x, y, dx, dy, k, 0, 0);
    });
    G.listo();
  }

  const clave = (e) => [e.t, e.pieza, e.s_spill, e.r_fin, e.pulsos].map(String).join("|");

  MAQ.EVENTOS.piroclastico = {
    orden: 46,
    armar(ctx, lista) {
      const P = lista.map((e, i) => {
        const p = preparar(ctx, e, i), N = e.gente.length + e.miran.length;
        p.g = N ? ctx.flota("persona", N, { tamano: e.tamano, orden: 6, semilla: (e.semilla * 17 + i * 5) % 991 }) : null;
        return p;
      });
      return { lista, P };
    },
    inicio(t, st) {
      if (!st) return;
      for (const P of st.P) { P.relleno.visible = false; if (P.lob) P.lob.m.visible = false; P.restos.visible = false; P.nube.visible = false; }
    },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t) return;
      let i = st.lista.indexOf(e); if (i < 0) { const k = clave(e); i = st.P.findIndex((P) => clave(P.e) === k); }
      if (i >= 0) dibujar(t, st.P[i], ctx);
    },
    en(t, st, ctx) {
      if (!st) return;
      for (const P of st.P) gente(t, P, ctx);
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
