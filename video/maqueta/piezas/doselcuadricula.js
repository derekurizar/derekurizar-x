// Pieza «doselcuadricula» (ficha: doselcuadricula.json; reglas: scripts/maqueta_tipos/doselcuadricula.py): un parche de
// selva tropical de tierras bajas visto de cerca y desde arriba, con la cuadrícula de cuadros que mide un satélite encima.
// Lo que se ve: el piso del sotobosque (verde oscuro con hojarasca) y sus arbustos; el dosel de copas en grumos de varios
// verdes (cada árbol con su tronco, su tamaño y su tono por semilla) que se mecen con el viento (en el vertex shader, puro
// de uT); algunos emergentes que sobresalen con copas más anchas y claras; una orla de selva de casi un cuadro alrededor de
// la cuadrícula, de borde irregular. Encima de las copas, la cuadrícula: líneas finas (cinta con su propio shader) que se
// trazan una tras otra desde `cuadricula_desde`; «resaltar» la pieza las aviva y «resaltar» con `elemento` enciende el
// borde de UN cuadro en el acento. Cada cuadro de `cuadros` cambia en su segundo:
//   tala     los árboles se tumban uno a uno y desaparecen; queda la tierra limpia con tocones (sin máquina ni persona)
//   fuego    llamas y humo genéricos; las copas se encogen y se carbonizan; queda la cicatriz oscura con troncos quemados
//   quemado  la cicatriz ya hecha
//   viento   los árboles caen volcados hacia un mismo lado y se quedan en el suelo
//   rebrote  plantas jóvenes que empiezan a crecer (sin pérdida antes, el cuadro arranca talado)
//   bosque   solo el tinte
// y se tiñe (un velo a la altura de la cuadrícula): bosque en `bien`, pérdida en `mal`, rebrote en `medio`, nunca el acento.
// De noche (ES.noche) el fuego alumbra (brasa y halo aditivo) y la cuadrícula se lee clara sobre la selva oscura. Todo se
// arma una vez; cada cuadro solo fija escalas, giros, tintes y alfas en función de t. Seek puro.
(function (MAQ) {
  const PERDIDA = { tala: 2.4, fuego: 2.8, quemado: 0.6, viento: 1.8 };      // cuánto tarda cada pérdida en verse completa (s)
  MAQ.PIEZAS.doselcuadricula = {
    orden: 6,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp, uComun, GLSL_COMUN, VERT_CINTA, geoCinta } = ctx;
      const noche = !!ES.noche, dia = !!ES.dia, TAU = 2 * Math.PI;
      const liso = (a, b, x) => { const u = clamp((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u); };
      // el material de la vegetación: color por vértice (luz horneada) que se mece con el viento según aMece (0 en la base)
      const matVeg = (mece) => new THREE.ShaderMaterial({
        uniforms: { ...uComun(), uBrillo: { value: 1 }, uTinte: { value: 0 }, cTinte: { value: new THREE.Color() }, uMece: { value: mece } },
        side: THREE.DoubleSide,
        vertexShader: "attribute vec3 color; attribute float aMece; uniform float uT, uMece; varying vec3 vCol, vPos;" +
          "void main(){ vCol = color; vec4 w = modelMatrix * vec4(position, 1.0); float f = aMece * uMece;" +
          " w.x += f * (sin(uT * 0.85 + w.x * 0.09 + w.z * 0.05) + 0.45 * sin(uT * 2.3 + w.z * 0.23));" +
          " w.z += f * 0.6 * sin(uT * 1.15 + w.x * 0.07 + 1.3); vPos = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }",
        fragmentShader: GLSL_COMUN + "uniform float uBrillo, uTinte; uniform vec3 cTinte; varying vec3 vCol, vPos;" +
          "void main(){ vec3 c = mix(vCol, cTinte, uTinte) * uBrillo; gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
      const nuevo = () => ({ pos: [], col: [], mec: [], idx: [] });
      const geo = (a) => {
        const g = new THREE.BufferGeometry();
        g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(a.pos), 3));
        g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(a.col), 3));
        g.setAttribute("aMece", new THREE.BufferAttribute(new Float32Array(a.mec), 1));
        g.setIndex(a.pos.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(a.idx), 1) : new THREE.BufferAttribute(new Uint16Array(a.idx), 1));
        return g;
      };
      const poner = (a, mat, orden, padre) => {
        const m = new THREE.Mesh(geo(a), mat); m.frustumCulled = false; m.renderOrder = orden; (padre || scene).add(m); return m;
      };
      // ---- sólidos de caras planas (icosaedro con los vértices movidos por semilla; cada cara con su luz y su tono)
      const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
      const vIco = [], uni = [];
      for (let i = 0; i < ico.length; i += 3) {
        let u = uni.findIndex((q) => Math.abs(q[0] - ico[i]) + Math.abs(q[1] - ico[i + 1]) + Math.abs(q[2] - ico[i + 2]) < 1e-4);
        if (u < 0) { u = uni.length; uni.push([ico[i], ico[i + 1], ico[i + 2]]); } vIco.push(u);
      }
      const c = new THREE.Color();
      const grumo = (a, cx, cy, cz, sx, sy, sz, rot, col, sem, m0, m1, aclara) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), v = [];
        for (let i = 0, k = 0; i < ico.length; i += 3, k++) {
          const f = 0.82 + 0.36 * hash(sem, 200 + vIco[k]), x = ico[i] * sx * f, y = ico[i + 1] * sy * f, z = ico[i + 2] * sz * f;
          v.push(cx + x * cr - z * sr, cy + y, cz + x * sr + z * cr, ico[i + 1]);
        }
        for (let i = 0, k = 0; i < v.length; i += 12, k++) {
          const e1 = [v[i + 4] - v[i], v[i + 5] - v[i + 1], v[i + 6] - v[i + 2]], e2 = [v[i + 8] - v[i], v[i + 9] - v[i + 1], v[i + 10] - v[i + 2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          const sb = sombra(nx, ny, nz) * (0.82 + 0.36 * hash(sem, 300 + k)) * (1 + (aclara || 0) * Math.max(0, ny));
          c.copy(col).multiplyScalar(sb);
          const q = a.pos.length / 3;
          for (let j = 0; j < 12; j += 4) {
            a.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); a.col.push(c.r, c.g, c.b);
            a.mec.push(m0 + (m1 - m0) * (v[i + j + 3] * 0.5 + 0.5));
          }
          a.idx.push(q, q + 1, q + 2);
        }
      };
      const tronco = (a, x0, y0, z0, x1, y1, z1, r0, r1, col, lados, m1) => {
        const d = [x1 - x0, y1 - y0, z1 - z0], l = Math.hypot(...d) || 1, ax = [d[0] / l, d[1] / l, d[2] / l];
        let p1 = Math.abs(ax[1]) < 0.9 ? [ax[2], 0, -ax[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
        const p2 = [ax[1] * p1[2] - ax[2] * p1[1], ax[2] * p1[0] - ax[0] * p1[2], ax[0] * p1[1] - ax[1] * p1[0]];
        for (let i = 0; i < lados; i++) {
          const t0 = TAU * i / lados, t1 = TAU * (i + 1) / lados, tm = (t0 + t1) / 2;
          const o = (t, r) => [(Math.cos(t) * p1[0] + Math.sin(t) * p2[0]) * r, (Math.cos(t) * p1[1] + Math.sin(t) * p2[1]) * r, (Math.cos(t) * p1[2] + Math.sin(t) * p2[2]) * r];
          const nm = o(tm, 1), q = a.pos.length / 3; c.copy(col).multiplyScalar(sombra(nm[0], nm[1], nm[2]));
          const va = o(t0, r0), vb = o(t1, r0), vc = o(t1, r1), vd = o(t0, r1);
          for (const [P, V, m] of [[[x0, y0, z0], va, 0], [[x0, y0, z0], vb, 0], [[x1, y1, z1], vc, m1], [[x1, y1, z1], vd, m1]]) {
            a.pos.push(P[0] + V[0], P[1] + V[1], P[2] + V[2]); a.col.push(c.r, c.g, c.b); a.mec.push(m);
          }
          a.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        }
      };
      // ---- colores (de ctx.tonos y ctx.COL): verdes del dosel, el sotobosque, la hojarasca, la tierra, la ceniza
      const verdes = [
        tonos.verde.clone().multiplyScalar(noche ? 1.25 : 0.82),
        tonos.verde.clone().lerp(tonos.bien, 0.35).multiplyScalar(noche ? 1.05 : 0.7),
        tonos.campo2.clone().lerp(tonos.verde, 0.6).multiplyScalar(noche ? 1.3 : 0.86),
        tonos.verde.clone().lerp(tonos.linea, 0.22).multiplyScalar(noche ? 1.4 : 0.9),
        tonos.verde.clone().lerp(tonos.medio, 0.18).multiplyScalar(noche ? 1.1 : 0.9),
      ];
      const cEmerg = tonos.verde.clone().lerp(tonos.medio, 0.1).lerp(tonos.bien, 0.12).multiplyScalar(noche ? 1.3 : 0.92);
      const cSoto = tonos.verde.clone().lerp(tonos.linea, 0.45).multiplyScalar(noche ? 1.0 : 0.62);
      const cHojarasca = lin(COL.tierra_media).lerp(tonos.linea, 0.45).multiplyScalar(noche ? 0.6 : 0.75);
      const cArbusto = tonos.verde.clone().lerp(tonos.linea, 0.3).multiplyScalar(noche ? 1.05 : 0.6);
      const cTronco = tonos.linea.clone().lerp(lin(COL.tierra_media), noche ? 0.55 : 0.45);
      const cTierra = noche ? lin(COL.tierra_media).lerp(tonos.suelo, 0.5) : lin(COL.tierra_media).lerp(tonos.calle, 0.25);
      const cBrote = tonos.bien.clone().lerp(tonos.verde, 0.35).multiplyScalar(noche ? 1.15 : 1.0);
      const cLlama = lin(COL.luces), cLlama2 = tonos.mal.clone().lerp(lin(COL.luces), 0.25);
      const cHumo = lin(COL.costa).lerp(tonos.linea, noche ? 0.35 : 0.3);
      const cRed = lin(COL.secundario), cAcento = lin(COL.acento);
      const cTinte = { bosque: tonos.bien.clone(), perdida: tonos.mal.clone(), rebrote: tonos.medio.clone() };
      const sRGB = "c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c));";

      return piezas.map((p, np) => {
        const n = p.n, K = p.celda, M1 = metros(1), half = n * K / 2, orla = 0.8 * K, E = half + orla;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const W = (u, v) => [p.x + u * ux - v * uy, p.y + u * uy + v * ux];                 // (u, v) locales → (x, y) de la escena
        const base0 = ctx.suelo(p.x, p.y), suelo = (x, y) => ctx.suelo(x, y);
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        const celda = (u, v) => {                                           // el cuadro (índice) de (u, v), o −1 en la orla
          const cc = Math.floor(u / K + n / 2), ff = Math.floor(n / 2 - v / K);
          return cc >= 0 && cc < n && ff >= 0 && ff < n ? ff * n + cc : -1;
        };
        const dentro = (u, v) => Math.max(Math.abs(u), Math.abs(v)) < half + orla * (0.45 + 0.55 * ruido(u + 3 * v, v - 2 * u, metros(14), 5));
        const centroCelda = (i) => [((i % n) + 0.5 - n / 2) * K, (n / 2 - Math.floor(i / n) - 0.5) * K];

        // ---- la historia de cada cuadro: su pérdida (tipo y segundo), su rebrote y su tinte (una secuencia de colores)
        const est = [];
        for (let i = 0; i < n * n; i++) est.push({ perdida: null, tp: 0, rebrote: null, tintes: [] });
        for (const [i, e, t] of p.cambios) {
          const s = est[i];
          if (e === "bosque") s.tintes.push({ col: "bosque", t: t > 0 ? t : -1 });
          else if (e === "rebrote") {
            if (!s.perdida) { s.perdida = "tala"; s.tp = -1000; s.tintes.push({ col: "perdida", t: -1 }); }
            if (s.rebrote === null) s.rebrote = t > 0 ? t : -1000;
            s.tintes.push({ col: "rebrote", t: t > 0 ? t + 1.0 : -1 });
          } else if (!s.perdida) {
            s.perdida = e; s.tp = t > 0 ? t : -1000;
            s.tintes.push({ col: "perdida", t: t > 0 ? t + PERDIDA[e] : -1 });
          }
        }
        const anim = (i) => !!est[i].perdida;                              // cuadros cuyos árboles se arman uno a uno

        // ---- el piso: una cuadrícula de caras (sotobosque y hojarasca), por cuadro si el cuadro cambia; y los arbustos
        const pisoFijo = nuevo(), arbFijo = nuevo(), pisos = {}, arbs = {};
        const pisoDe = (i) => (i >= 0 && anim(i) ? (pisos[i] = pisos[i] || nuevo()) : pisoFijo);
        const arbDe = (i) => (i >= 0 && anim(i) ? (arbs[i] = arbs[i] || nuevo()) : arbFijo);
        const g = Math.max(metros(3), 2 * E / 64), NG = Math.ceil(2 * E / g), LEV = metros(0.06);
        for (let a = 0; a < NG; a++) for (let b = 0; b < NG; b++) {
          const u0 = -E + a * g, v0 = -E + b * g, um = u0 + g / 2, vm = v0 + g / 2;
          if (!dentro(um, vm)) continue;
          const i = celda(um, vm), A = pisoDe(i);
          const n1 = ruido(um, vm, metros(9), 11), n2 = ruido(um, vm, metros(3), 12);
          c.copy(cSoto).lerp(cHojarasca, 0.55 * liso(0.55, 0.9, n1)).multiplyScalar(0.85 + 0.25 * n2 + 0.1 * hz(a * 977 + b, 13));
          const q = A.pos.length / 3;
          for (const [du, dv] of [[0, 0], [g, 0], [g, g], [0, g]]) {
            const [x, y] = W(u0 + du, v0 + dv); A.pos.push(x, suelo(x, y) + LEV, -y); A.col.push(c.r, c.g, c.b); A.mec.push(0);
          }
          A.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        }
        {   // los arbustos del sotobosque: grumos bajos y oscuros, más en los claros
          const pa = metros(6.5), na = Math.ceil(2 * E / pa);
          for (let a = 0; a < na; a++) for (let b = 0; b < na; b++) {
            const q = a * 1013 + b, u = -E + (a + hz(q, 20)) * pa, v = -E + (b + hz(q, 21)) * pa;
            if (!dentro(u, v) || hz(q, 22) > 0.7) continue;
            const [x, y] = W(u, v), R = metros(1.1 + 1.1 * hz(q, 23)), Hh = metros(0.9 + 1.0 * hz(q, 24));
            grumo(arbDe(celda(u, v)), x, suelo(x, y) + Hh * 0.55, -y, R, Hh * 0.65, R * (0.8 + 0.4 * hz(q, 25)), hz(q, 26) * TAU,
              cArbusto.clone().multiplyScalar(0.8 + 0.4 * hz(q, 27)), sem + q * 7 + 1, 0, 0.25);
          }
        }
        const matPisoFijo = malla.material(), matArbFijo = matVeg(metros(0.12));
        poner(pisoFijo, matPisoFijo, 2); poner(arbFijo, matArbFijo, 3);

        // ---- los árboles: una cuadrícula con azar fijo (≤ ~900), cada uno con tronco y copa en grumos
        const HB = metros(21), sp = Math.max(metros(6.2), 2 * E / 30), nt = Math.ceil(2 * E / sp), arboles = [];
        for (let a = 0; a < nt; a++) for (let b = 0; b < nt; b++) {
          const q = a * 2003 + b, u = -E + (a + 0.15 + 0.7 * hz(q, 30)) * sp, v = -E + (b + 0.15 + 0.7 * hz(q, 31)) * sp;
          if (!dentro(u, v) || hz(q, 32) > p.densidad) continue;
          const em = hz(q, 33) < p.emergentes, H = HB * (em ? 1.28 + 0.18 * hz(q, 34) : 0.8 + 0.2 * hz(q, 34));
          const R = sp * (em ? 0.82 + 0.18 * hz(q, 35) : 0.62 + 0.2 * hz(q, 35));
          const [x, y] = W(u, v);
          arboles.push({ q, u, v, x, y, h: suelo(x, y), H, R, em, i: celda(u, v), col: em ? cEmerg.clone().multiplyScalar(0.92 + 0.16 * hz(q, 36)) : verdes[Math.floor(hz(q, 37) * verdes.length) % verdes.length].clone().multiplyScalar(0.88 + 0.24 * hz(q, 38)) });
        }
        // la copa (en coordenadas locales: centro de la copa en el origen) y el tronco (base en el origen)
        const copa = (A, t, ox, oy, oz) => {
          const Ry = t.R * (t.em ? 0.42 : 0.52), nG = t.em ? 4 : 2, sm = sem + t.q * 13;
          grumo(A, ox, oy, oz, t.R, Ry, t.R * (0.85 + 0.3 * hz(t.q, 40)), hz(t.q, 41) * TAU, t.col, sm, 0.55, 1, dia ? 0.12 : 0.05);
          for (let k = 0; k < nG; k++) {
            const az = hz(t.q, 42 + k) * TAU, d = t.R * (0.5 + 0.15 * hz(t.q, 46 + k)), rr = t.R * (0.5 + 0.18 * hz(t.q, 50 + k));
            grumo(A, ox + Math.cos(az) * d, oy - Ry * (0.15 + 0.3 * hz(t.q, 54 + k)), oz + Math.sin(az) * d, rr, Ry * 0.75, rr,
              hz(t.q, 58 + k) * TAU, t.col.clone().multiplyScalar(0.9 + 0.2 * hz(t.q, 62 + k)), sm + k + 1, 0.45, 0.95, dia ? 0.1 : 0.04);
          }
        };
        const alturaCopa = (t) => t.H - t.R * (t.em ? 0.42 : 0.52) * 0.8;
        const radioTronco = (t) => metros(t.em ? 0.75 : 0.35 + 0.15 * hz(t.q, 64));
        const copasFijas = nuevo(), cuadros = {};
        for (const t of arboles) {
          const yc = alturaCopa(t);
          if (t.i < 0 || !anim(t.i)) {
            tronco(copasFijas, t.x, t.h, -t.y, t.x, t.h + yc, -t.y, radioTronco(t), radioTronco(t) * 0.6, cTronco, 6, 0.4);
            copa(copasFijas, t, t.x, t.h + yc, -t.y);
            continue;
          }
          // un cuadro que cambia: cada árbol en su grupo (base en el suelo) para tumbarlo, encogerlo o carbonizarlo
          const S = cuadros[t.i] = cuadros[t.i] || { arboles: [], matCopa: matVeg(metros(0.32)), matTronco: matVeg(0) };
          const grp = new THREE.Group(); grp.position.set(t.x, t.h, -t.y); scene.add(grp);
          const at = nuevo(), ac = nuevo();
          tronco(at, 0, 0, 0, 0, yc, 0, radioTronco(t), radioTronco(t) * 0.6, cTronco, 8, 0.4);
          copa(ac, t, 0, 0, 0);
          poner(at, S.matTronco, 3, grp);
          const mc = poner(ac, S.matCopa, 3, grp); mc.position.set(0, yc, 0);
          S.arboles.push({ t, grp, mc, yc });
        }
        const matCopasFijas = matVeg(metros(0.32));
        poner(copasFijas, matCopasFijas, 3);

        // ---- lo que necesita cada cuadro que cambia: su piso propio, tocones, brotes, llamas y humo
        const CAMB = [];
        for (let i = 0; i < n * n; i++) {
          if (!anim(i)) continue;
          const s = est[i], S = cuadros[i] || { arboles: [], matCopa: matVeg(metros(0.32)), matTronco: matVeg(0) };
          const [uc, vc] = centroCelda(i), [cx, cy] = W(uc, vc), dirV = hz(i, 70) * TAU;     // hacia dónde cae (viento)
          const matPiso = malla.material(), matArb = matVeg(metros(0.12));
          if (pisos[i]) poner(pisos[i], matPiso, 2);
          const mArb = arbs[i] ? poner(arbs[i], matArb, 3) : null;
          const ent = { i, s, S, cx, cy, matPiso, matArb, mArb, dirV, tocones: null, brotes: [], llamas: [], humo: [] };
          // el orden en que se va cada árbol, y hacia dónde cae
          S.arboles.forEach((a, k) => {
            a.d = s.perdida === "viento" ? 1.1 * hz(a.t.q, 80) : 1.8 * hz(a.t.q, 81);
            a.cae = s.perdida === "viento" ? hz(a.t.q, 82) < 0.86 : true;
            const az = s.perdida === "viento" ? dirV + (hz(a.t.q, 83) - 0.5) * 0.7 : hz(a.t.q, 84) * TAU;
            const dx = Math.cos(az), dz = -Math.sin(az);
            a.eje = new THREE.Vector3(dz, 0, -dx).normalize();
          });
          if (s.perdida === "tala") {                                        // los tocones y unos troncos cortados en la tierra
            const A = nuevo();
            for (const a of S.arboles) {
              const rt = radioTronco(a.t) * 1.05, hh = metros(0.5 + 0.4 * hz(a.t.q, 86));
              tronco(A, a.t.x, a.t.h - metros(0.1), -a.t.y, a.t.x, a.t.h + hh, -a.t.y, rt, rt, cTronco.clone().lerp(lin(COL.costa), 0.25), 8, 0);
              c.copy(lin(COL.costa)).lerp(cTierra, 0.35);                 // la cara del corte, clara
              const q = A.pos.length / 3;
              for (let k = 0; k < 8; k++) { const an = TAU * k / 8; A.pos.push(a.t.x + Math.cos(an) * rt, a.t.h + hh + metros(0.01), -a.t.y + Math.sin(an) * rt); A.col.push(c.r, c.g, c.b); A.mec.push(0); }
              for (let k = 1; k < 7; k++) A.idx.push(q, q + k, q + k + 1);
            }
            ent.tocones = poner(A, matVeg(0), 3);
          }
          if (s.rebrote !== null) {                                          // los brotes: plantas jóvenes, de a una
            const pb = Math.max(metros(2.6), K / 9), nb = Math.floor(K / pb);
            for (let a = 0; a < nb; a++) for (let b = 0; b < nb; b++) {
              const q = i * 4099 + a * 31 + b;
              if (hz(q, 90) > 0.8) continue;
              const u = uc - K / 2 + (a + 0.2 + 0.6 * hz(q, 91)) * pb, v = vc - K / 2 + (b + 0.2 + 0.6 * hz(q, 92)) * pb, [x, y] = W(u, v);
              const A = nuevo(), hh = metros(1.6 + 2.2 * hz(q, 93)), rr = metros(0.7 + 0.7 * hz(q, 94));
              tronco(A, 0, 0, 0, 0, hh * 0.7, 0, metros(0.06), metros(0.04), cTronco, 5, 0.3);
              grumo(A, 0, hh * 0.72, 0, rr, rr * 0.8, rr, hz(q, 95) * TAU, cBrote.clone().multiplyScalar(0.85 + 0.3 * hz(q, 96)), sem + q, 0.3, 0.9, 0.3);
              grumo(A, rr * 0.4, hh * 0.45, -rr * 0.3, rr * 0.6, rr * 0.5, rr * 0.6, hz(q, 97) * TAU, cBrote.clone().multiplyScalar(0.8), sem + q + 3, 0.2, 0.6, 0.3);
              const m = poner(A, matVeg(metros(0.08)), 3); m.position.set(x, suelo(x, y), -y);
              ent.brotes.push({ m, d: 0.1 + 1.8 * hz(q, 98) });
            }
          }
          if (s.perdida === "fuego") {                                       // llamas: conos de dos colores que laten
            for (let k = 0; k < 14; k++) {
              const q = i * 6007 + k, u = uc + (hz(q, 100) - 0.5) * K * 0.85, v = vc + (hz(q, 101) - 0.5) * K * 0.85, [x, y] = W(u, v);
              const A = nuevo(), rad = metros(1.6 + 1.6 * hz(q, 102));
              for (let j = 0; j < 9; j++) {
                const a0 = TAU * j / 9, a1 = TAU * (j + 1) / 9, qq = A.pos.length / 3;
                A.pos.push(Math.cos(a0) * rad, 0, Math.sin(a0) * rad, Math.cos(a1) * rad, 0, Math.sin(a1) * rad, 0, 1, 0);
                A.col.push(cLlama2.r, cLlama2.g, cLlama2.b, cLlama2.r, cLlama2.g, cLlama2.b, cLlama.r, cLlama.g, cLlama.b); A.mec.push(0, 0, 0);
                A.idx.push(qq, qq + 1, qq + 2);
              }
              const mat = malla.material(); mat.uniforms.uBrillo.value = noche ? 1.6 : 1.35;
              const m = poner(A, mat, 5); m.position.set(x, suelo(x, y), -y);
              ent.llamas.push({ m, x, y, alto: metros(5 + 9 * hz(q, 103)), f: 6 + 5 * hz(q, 104), ph: hz(q, 105) * TAU, d: 0.6 * hz(q, 106) });
            }
            for (let k = 0; k < 20; k++) {
              const q = i * 7001 + k;
              ent.humo.push({ u: uc + (hz(q, 110) - 0.5) * K * 0.8, v: vc + (hz(q, 111) - 0.5) * K * 0.8, ph: hz(q, 112), per: 3.2 + 1.6 * hz(q, 113) });
            }
          }
          CAMB.push(ent);
        }
        // ---- el humo y el halo del fuego: puntos con su tamaño y su alfa (un atributo por punto)
        const nH = CAMB.reduce((s, e) => s + e.humo.length, 0), nL = CAMB.reduce((s, e) => s + (e.llamas.length ? 1 : 0), 0);
        const puntos = (N, color, aditivo, orden) => {
          const gh = new THREE.BufferGeometry();
          gh.setAttribute("position", new THREE.BufferAttribute(new Float32Array(Math.max(1, N) * 3), 3));
          gh.setAttribute("aTam", new THREE.BufferAttribute(new Float32Array(Math.max(1, N)), 1));
          gh.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(Math.max(1, N)), 1));
          const mh = new THREE.ShaderMaterial({ uniforms: { cA: { value: color }, uPx: { value: ctx.H * 0.5 } },
            transparent: true, depthWrite: false, blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
            vertexShader: "attribute float aTam, aA; uniform float uPx; varying float vA; void main(){ vA = aA; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aA > 0.0 ? clamp(aTam * uPx * projectionMatrix[1][1] / max(-mv.z, 0.001), 1.0, 380.0) : 0.0; }",
            fragmentShader: "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vA * (" +
              (aditivo ? "exp(-r * r * 4.0)" : "smoothstep(1.0, 0.35, r) * 0.9") + "); if (a < 0.003) discard; vec3 c = cA; " + sRGB + " gl_FragColor = vec4(c, a); }" });
          const pt = new THREE.Points(gh, mh); pt.frustumCulled = false; pt.renderOrder = orden; scene.add(pt); return pt;
        };
        const humo = nH ? puntos(nH, cHumo, false, 7) : null, halo = nL ? puntos(nL, cLlama2.clone().lerp(cLlama, 0.5), true, 8) : null;

        // ---- la cuadrícula y los tintes, a la altura de las copas
        const HG = base0 + HB * 1.0 + metros(1.2);
        const matRed = (color) => new THREE.ShaderMaterial({
          uniforms: { ...uComun(), uAncho: { value: 1.4 }, cColor: { value: color }, uAlfa: { value: 0 }, uHasta: { value: 0 }, uK: { value: 1 } },
          vertexShader: VERT_CINTA, transparent: true, depthWrite: false,
          fragmentShader: "uniform vec3 cColor; uniform float uAlfa, uHasta, uK; varying float vLado, vS; void main(){ if (vS > uHasta) discard;" +
            " float a = uAlfa * smoothstep(0.0, 0.5, 1.0 - abs(vLado)); if (a < 0.003) discard; vec3 c = cColor * uK; " + sRGB + " gl_FragColor = vec4(c, a); }" });
        let red = null, SMAX = 1;
        if (p.cuadricula) {
          const pts = [], OFF = 0.1;
          for (let j = 0; j <= n; j++) {                       // las líneas a lo largo de u (filas) y de v (columnas), alternadas
            for (const dir of [0, 1]) {
              const k = j * 2 + dir, o = -half + j * K;
              const A = dir ? W(o, half) : W(-half, half - j * K), B = dir ? W(o, -half) : W(half, half - j * K);
              const NSEG = 6;
              for (let s2 = 0; s2 <= NSEG; s2++) {
                const f = s2 / NSEG, x = A[0] + (B[0] - A[0]) * f, y = A[1] + (B[1] - A[1]) * f;
                pts.push({ v: new THREE.Vector3(x, HG, -y), s: k * OFF + f, salto: s2 === NSEG });
              }
            }
          }
          SMAX = (2 * n + 1) * OFF + 1;
          const mat = matRed(cRed);
          const m = new THREE.Mesh(geoCinta(pts), mat); m.frustumCulled = false; m.renderOrder = 9; scene.add(m);
          ctx.registrarCinta(mat, 1.4);
          red = mat;
        }
        // los bordes de los cuadros resaltados (en el acento): hasta 4 a la vez, cada uno se pone en su cuadro
        const marcos = [];
        for (let k = 0; k < 4; k++) {
          const pts = [], hk = K / 2 - metros(0.4);
          [[-hk, -hk], [hk, -hk], [hk, hk], [-hk, hk], [-hk, -hk]].forEach(([u, v], j) => {
            const x = u * ux - v * uy, y = u * uy + v * ux; pts.push({ v: new THREE.Vector3(x, metros(0.3), -y), s: 0, salto: j === 4 });
          });
          const mat = matRed(cAcento); mat.uniforms.uHasta.value = 10;
          const m = new THREE.Mesh(geoCinta(pts), mat); m.frustumCulled = false; m.renderOrder = 10; m.visible = false; scene.add(m);
          ctx.registrarCinta(mat, 3.2);
          marcos.push({ m, mat });
        }
        const velos = [];
        for (let i = 0; i < n * n; i++) {
          if (!est[i].tintes.length) continue;
          const [uc, vc] = centroCelda(i), A = malla.nueva(), hk = K / 2 - metros(0.25);
          for (const [du, dv] of [[-hk, -hk], [hk, -hk], [hk, hk], [-hk, hk]]) {
            const [x, y] = W(uc + du, vc + dv); A.pos.push(x, HG - metros(0.2), -y); A.col.push(1, 1, 1);
          }
          A.idx.push(0, 1, 2, 0, 2, 3);
          const mat = malla.material({ alfa: 0.5 }); mat.uniforms.uTinte.value = 1;
          const m = malla.poner(A, mat, 8);
          velos.push({ i, m, mat, tintes: est[i].tintes.slice().sort((a, b) => a.t - b.t) });
        }
        return { id: p.id, p, CAMB, humo, halo, red, SMAX, marcos, velos, W, centroCelda, HB, K, HG };
      });
    },
    en(t, lista, ctx) {
      const { clamp, suave, tonos, ES } = ctx, noche = !!ES.noche;
      const liso = (a, b, x) => { const u = clamp((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u); };
      for (const P of lista) {
        const p = P.p, br = ctx.cuadro.brillo[P.id], kb = br ? clamp((br - 1) / 0.9, 0, 1.2) : 0;
        let iH = 0, iL = 0;
        const AH = P.humo && P.humo.geometry.attributes, AL = P.halo && P.halo.geometry.attributes;
        for (const e of P.CAMB) {
          const s = e.s, L = t - s.tp, tipo = s.perdida;
          // el piso: tierra (tala), ceniza (fuego), igual (viento)
          const kp = tipo === "tala" ? liso(0.3, PERDIDA.tala, L) : tipo === "fuego" ? liso(0.6, 3.2, L) : tipo === "quemado" ? liso(0, 0.6, L) : 0;
          if (tipo === "tala") e.matPiso.uniforms.cTinte.value.copy(ctx.lin(ctx.COL.tierra_media)).lerp(tonos.calle, noche ? 0 : 0.25).multiplyScalar(noche ? 0.55 : 0.92);
          else e.matPiso.uniforms.cTinte.value.copy(tonos.linea).lerp(ctx.lin(ctx.COL.tierra_media), 0.15).multiplyScalar(noche ? 1.6 : 1);
          e.matPiso.uniforms.uTinte.value = kp * (tipo === "tala" ? 0.85 : 0.8);
          if (e.mArb) {                                                  // los arbustos: se van (tala) o se queman
            const ka = tipo === "tala" ? 1 - liso(0.2, 1.4, L) : 1;
            e.mArb.visible = ka > 0.01; e.mArb.scale.set(1, Math.max(0.01, ka), 1);
            e.matArb.uniforms.cTinte.value.copy(tonos.linea);
            e.matArb.uniforms.uTinte.value = tipo === "fuego" ? 0.85 * liso(0.4, 2.6, L) : tipo === "quemado" ? 0.85 * liso(0, 0.6, L) : 0;
          }
          // los árboles
          const S = e.S, kc = tipo === "fuego" ? liso(0.4, 3.0, L) : tipo === "quemado" ? liso(0, 0.6, L) : 0;
          S.matCopa.uniforms.cTinte.value.copy(tonos.linea).lerp(ctx.lin(ctx.COL.tierra_media), 0.12);
          S.matCopa.uniforms.uTinte.value = 0.88 * kc;
          S.matTronco.uniforms.cTinte.value.copy(tonos.linea);
          S.matTronco.uniforms.uTinte.value = 0.75 * kc;
          for (const a of S.arboles) {
            a.grp.visible = true; a.grp.quaternion.identity(); a.grp.scale.set(1, 1, 1); a.mc.scale.set(1, 1, 1); a.mc.visible = true;
            if (tipo === "tala") {
              const u = clamp((L - a.d) / 0.55, 0, 1), th = u * u * (Math.PI / 2 - 0.08), sale = liso(0.55, 0.95, (L - a.d) / 1.0);
              a.grp.quaternion.setFromAxisAngle(a.eje, th);
              const k = 1 - sale; a.grp.visible = k > 0.01; a.grp.scale.setScalar(Math.max(0.01, k));
            } else if (tipo === "viento" && a.cae) {
              const u = clamp((L - a.d) / 0.7, 0, 1), th = u * u * (Math.PI / 2 - 0.12) + Math.sin(Math.min(1, Math.max(0, (L - a.d - 0.7) / 0.35)) * Math.PI) * 0.05;
              a.grp.quaternion.setFromAxisAngle(a.eje, th);
            } else if (tipo === "fuego" || tipo === "quemado") {
              const kk = tipo === "quemado" ? liso(0, 0.6, L) : liso(0.8 + 0.4 * a.d, 3.6 + 0.4 * a.d, L);
              const f = 1 - 0.78 * kk; a.mc.scale.set(f, f * 0.8 + 0.2 * (1 - kk), f); a.mc.visible = f > 0.05;
            }
          }
          if (e.tocones) e.tocones.visible = tipo === "tala" && L > 0;
          for (const b of e.brotes) {                                    // los brotes crecen de a uno, desde su segundo
            const k = s.rebrote === null ? 0 : liso(b.d, b.d + 1.8, t - s.rebrote);
            b.m.visible = k > 0.01; b.m.scale.setScalar(Math.max(0.01, k));
          }
          // las llamas, el halo y el humo del fuego
          if (e.llamas.length) {
            const env = liso(0, 0.9, L) * (1 - liso(3.4, 5.0, L));
            let sumx = 0, sumy = 0;
            for (const l of e.llamas) {
              const k = env * liso(l.d, l.d + 0.5, L), fl = 0.78 + 0.14 * Math.sin(t * l.f + l.ph) + 0.08 * Math.sin(t * l.f * 2.3 + l.ph * 2);
              l.m.visible = k > 0.01; l.m.scale.set(Math.max(0.01, k) * (0.9 + 0.1 * fl), Math.max(0.01, k * fl) * l.alto, Math.max(0.01, k) * (0.9 + 0.1 * fl));
              l.m.rotation.y = 0.4 * Math.sin(t * 1.3 + l.ph); sumx += l.x; sumy += l.y;
            }
            if (AL) {
              const cx = sumx / e.llamas.length, cy = sumy / e.llamas.length;
              AL.position.setXYZ(iL, cx, ctx.suelo(cx, cy) + P.HB * 0.45, -cy);
              AL.aTam.setX(iL, P.K * (noche ? 1.3 : 1.2)); AL.aA.setX(iL, env * (noche ? 0.38 : 0.35) * (0.85 + 0.15 * Math.sin(t * 7.3 + e.i))); iL++;
            }
            const kh = liso(0.2, 1.2, L) * (1 - liso(4.6, 8.5, L));
            for (const h of e.humo) {
              const a = ((t - s.tp) / h.per + h.ph) % 1, age = a < 0 ? a + 1 : a;
              const deriva = ctx.metros(4 + 26 * age), [x, y] = P.W(h.u + Math.cos(e.dirV) * deriva, h.v + Math.sin(e.dirV) * deriva);
              AH.position.setXYZ(iH, x, ctx.suelo(x, y) + P.HB * (0.7 + 1.4 * age), -y);
              AH.aTam.setX(iH, ctx.metros(5 + 13 * age)); AH.aA.setX(iH, L > 0 ? kh * 0.55 * Math.sin(Math.PI * Math.min(1, age * 1.15)) : 0); iH++;
            }
          }
        }
        if (AH) { AH.position.needsUpdate = AH.aTam.needsUpdate = AH.aA.needsUpdate = true; }
        if (AL) { AL.position.needsUpdate = AL.aTam.needsUpdate = AL.aA.needsUpdate = true; }
        // la cuadrícula: se traza desde `cuadricula_desde`; resaltar la pieza la aviva
        if (P.red) {
          const u = clamp((t - p.cuadricula_desde) / 1.6, 0, 1);
          P.red.uniforms.uHasta.value = u > 0 ? u * P.SMAX : -1;
          P.red.uniforms.uAlfa.value = (noche ? 0.85 : 0.78) + 0.2 * kb;
          P.red.uniforms.uK.value = 1 + 0.35 * kb;
        }
        // los tintes de cada cuadro
        for (const v of P.velos) {
          let alfa = 0; const col = v.mat.uniforms.cTinte.value; let primero = true;
          for (const ti of v.tintes) {
            const k = ti.t < 0 ? 1 : liso(ti.t, ti.t + 0.6, t); if (k <= 0) break;
            const cc = ti.col === "bosque" ? tonos.bien : ti.col === "perdida" ? tonos.mal : tonos.medio;
            if (primero) { col.copy(cc); alfa = k; primero = false; } else { col.lerp(cc, k); alfa = 1; }
          }
          v.m.visible = alfa > 0.01 && p.tinte > 0;
          v.mat.uniforms.uAlfa.value = p.tinte * alfa * (1 + 0.4 * kb);
        }
        // el borde de los cuadros resaltados con `elemento`
        const el = ctx.cuadro.elementos[P.id] || [];
        P.marcos.forEach((m, k) => {
          const q = el[k];
          if (!q || !(q.k > 0)) { m.m.visible = false; return; }
          const [uc, vc] = P.centroCelda(q.i), [x, y] = P.W(uc, vc);
          m.m.visible = true; m.m.position.set(x, P.HG, -y);
          m.mat.uniforms.uAlfa.value = Math.min(1, q.k * 1.1);
          m.mat.uniforms.uK.value = 1 + 0.25 * Math.sin(t * 5.0);
        });
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
