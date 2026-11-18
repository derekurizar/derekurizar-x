// Evento «transformar» (ficha: transformar.json; reglas: scripts/maqueta_tipos/transformar.py): una pieza con épocas pasa
// de una (`de`) a otra (`a`) mientras dura el evento, como una OBRA que se ve de principio a fin:
//  1. lo VIEJO se desvanece por partes (casas, la fábrica, su chimenea, los árboles, la cerca del potrero): cada parte se
//     hunde en su turno con un poco de polvo, en `orden` centro-afuera o en un azar fijo;
//  2. la TIERRA se mueve: un terreno de obra se abre desde el centro y tapa las callecitas; montículos que se empujan de
//     un lado a otro y volteos genéricos que dan vueltas; obreros genéricos sin empresa ni chaleco con marca;
//  3. las PILAS suben (dos columnas con su viga cabezal y su zapata), del centro de cada puente hacia afuera;
//  4. los TABLEROS se tienden tramo a tramo (asfalto, pretiles, rayas, rampas macizas y postes de luz) sobre tres puentes
//     que pasan por encima de tres calzadas a nivel: un nudo ilustrativo, sin decir cuál puente es cuál ni cuántos carriles;
//  5. las calzadas nuevas se asfaltan, la tierra que queda se vuelve jardín y al final llegan los CARROS de la época nueva.
// Sin texto ni números en el 3D (los años van en la capa). Con una pieza que declara `epocas: true` en su módulo, la pieza
// dibuja sus épocas (lee ctx.cuadro.epoca[pieza]) y aquí solo va la obra (tierra, montículos, volteos, obreros, polvo).
// Publica en `inicio` ctx.cuadro.epoca[pieza] = {de, a, u, viejo, tierra, pilas, tableros, carros (cada una 0–1), x, y, radio_m,
// hunde(x, y, i)}: con él, la pieza hunde lo suyo de la época vieja dentro de la obra al mismo tiempo que lo viejo del evento.
// Seek puro: cada parte tiene su segundo (de la semilla, al armar) y todo lo que se ve sale de t.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
  const ease = (u) => u * u * (3 - 2 * u);
  // las fases, en fracción de la duración del evento
  const F = { viejo: [0.02, 0.24], dv: 0.08, tierra: [0.05, 0.34], mont: [0.1, 0.62], volteos: [0.08, 0.76], obreros: [0.2, 0.86],
    pilas: [0.3, 0.5], dp: 0.07, tableros: [0.48, 0.78], dt: 0.06, calles: [0.74, 0.88], verde: [0.8, 0.95], carros: [0.84, 0.97] };

  MAQ.EVENTOS.transformar = {
    orden: 43,
    armar(ctx, lista) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, M = ctx.metros(1), gnd = (x, y) => ctx.suelo(x, y);
      const C = (k, alt) => lin(COL[k] || COL[alt] || COL.secundario);
      // ---- los tonos (todos del estilo)
      const cConc = tonos.muro.clone().lerp(tonos.pavimento, 0.5), cConcO = cConc.clone().multiplyScalar(0.78);
      const cAsf = tonos.asfalto.clone().lerp(tonos.calle || tonos.asfalto, 0.3), cRaya = (tonos.raya || tonos.arena).clone();
      const cMuro = tonos.muro.clone().lerp(tonos.arena, 0.15), cZoc = tonos.muro.clone().lerp(tonos.asfalto, 0.45).multiplyScalar(0.85);
      const cLam = tonos.techo.clone().lerp(tonos.muro, 0.25), cLamO = cLam.clone().multiplyScalar(0.72);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.25), cVidrio = tonos.agua.clone().lerp(cHueco, 0.5);
      const cLuz = lin(COL.luces), cMetal = tonos.linea.clone().lerp(tonos.muro, 0.5);
      const cCalle0 = tonos.pavimento.clone().lerp(tonos.arena, 0.45), cCampo = tonos.campo.clone().lerp(tonos.verde, 0.25);
      const cCesped = tonos.verde.clone().lerp(tonos.campo, 0.45).multiplyScalar(oscuro ? 1.1 : 1);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.45 : 0.9);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cMadera = cTronco.clone().lerp(tonos.arena, 0.2);
      const TIE = [C("tierra_media").multiplyScalar(0.85), C("tierra_alta", "tierra_media").lerp(C("tierra_media"), 0.5).multiplyScalar(0.8), C("tierra_baja", "tierra_media").lerp(C("tierra_media"), 0.6).multiplyScalar(0.9)];
      const cPolvo = TIE[0].clone().lerp(tonos.arena, 0.5), cHumo = tonos.muro.clone().lerp(tonos.suelo, 0.3);
      const oct = new THREE.OctahedronGeometry(1, 1).toNonIndexed().attributes.position.array;

      // ---- una PARTE: una malla con su origen (x, y escena; h la altura del suelo) y su giro; todo en METROS locales
      // (x adelante, y arriba, z a su derecha); la luz se hornea con la normal ya girada
      const parte = (x, y, rot, h) => ({ acc: malla.nueva(), foc: malla.nueva(), x, y, h: h === undefined ? gnd(x, y) : h, rot, c: Math.cos(rot), s: Math.sin(rot) });
      const aEscena = (p, lx, lz) => [p.x + (lx * p.c + lz * p.s) * M, p.y + (lx * p.s - lz * p.c) * M];
      const sueloL = (p, lx, lz) => { const [x, y] = aEscena(p, lx, lz); return (gnd(x, y) - p.h) / M; };
      const cara = (p, P, col, ref, acc) => {
        const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
        let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
        const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
        if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx * p.c + nz * p.s, ny, -nx * p.s + nz * p.c), a = acc || p.acc, q = a.pos.length / 3;
        for (const v of P) { a.pos.push(v[0] * M, v[1] * M, v[2] * M); a.col.push(col.r * l, col.g * l, col.b * l); }
        a.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
      };
      const UP = [0, 1, 0];
      const caja = (p, x0, x1, y0, y1, z0, z1, col, o = {}) => {
        const a = o.acc;
        if (!o.sinTapa) cara(p, [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]], col, UP, a);
        if (o.base) cara(p, [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]], col, [0, -1, 0], a);
        cara(p, [[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]], col, [1, 0, 0], a);
        cara(p, [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]], col, [-1, 0, 0], a);
        cara(p, [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], col, [0, 0, 1], a);
        cara(p, [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]], col, [0, 0, -1], a);
      };
      const tubo = (p, A, B, r, seg, col, acc) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) { const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(p, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2), acc); }
      };
      const gema = (p, P, rx, ry, rz, rot, col) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), c = new THREE.Color();
        for (let i = 0; i < oct.length; i += 9) {
          const v = [];
          for (let j = 0; j < 9; j += 3) { const x = oct[i + j] * rx, y = oct[i + j + 1] * ry, z = oct[i + j + 2] * rz; v.push([P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr]); }
          const e1 = [v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]], e2 = [v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; c.copy(col).multiplyScalar(sombra(nx / n, Math.abs(ny / n), nz / n));
          const q = p.acc.pos.length / 3;
          for (const w of v) { p.acc.pos.push(w[0] * M, w[1] * M, w[2] * M); p.acc.col.push(c.r, c.g, c.b); }
          p.acc.idx.push(q, q + 1, q + 2);
        }
      };
      const arbol = (p, lx, lz, al, kk, hz) => {
        const y0 = sueloL(p, lx, lz) - 0.2;
        tubo(p, [lx, y0, lz], [lx, y0 + al * 0.55, lz], 0.06 * al, 8, cTronco);
        for (let j = 0; j < 3; j++) { const a = TAU * hz(kk, 30 + j), rr = j ? al * 0.17 : 0;
          gema(p, [lx + Math.cos(a) * rr, y0 + al * (0.74 - 0.07 * j), lz + Math.sin(a) * rr], al * 0.32, al * 0.24, al * 0.3, a, cCopa.clone().multiplyScalar(0.85 + 0.25 * hz(kk, 33 + j))); }
      };
      const mCuerpo = malla.material({ desfase: 1 }), mFoc = malla.material({ desfase: 2 }), mSuelo0 = malla.material({ desfase: 2 });
      const mTierra = malla.material({ desfase: 4 }), mCalle = malla.material({ desfase: 6 }), mRaya = malla.material({ desfase: 8 });
      mFoc.uniforms.uBrillo.value = noche ? 1.7 : 1;
      mTierra.uniforms.cTinte.value.copy(cCesped);
      const poner = (p, mat, orden, acc) => {
        const a = acc || p.acc; if (!a.idx.length) return null;
        const m = malla.poner(a, mat, orden); m.position.set(p.x, p.h, -p.y); m.rotation.y = p.rot; m.visible = false; return m;
      };

      // ---- el carro (objetos/carro.js) como malla propia: así sube por la rampa y se inclina con ella
      const carroGeo = (rot, col) => {
        const O = MAQ.OBJETOS.carro; if (!O) return null;
        const p = parte(0, 0, rot, 0), acc = malla.nueva(), c = new THREE.Color();
        for (const pt of O.partes(ctx)) {
          const a = pt.geo.toNonIndexed().attributes.position.array, base = pt.tinte ? col : pt.color, kL = pt.luz && noche ? 1.7 : 1;
          for (let i = 0; i < a.length; i += 9) {
            const e1 = [a[i + 3] - a[i], a[i + 4] - a[i + 1], a[i + 5] - a[i + 2]], e2 = [a[i + 6] - a[i], a[i + 7] - a[i + 1], a[i + 8] - a[i + 2]];
            const nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0], n = Math.hypot(nx, ny, nz) || 1;
            c.copy(base).multiplyScalar(kL * (pt.luz ? 1 : sombra((nx * p.c + nz * p.s) / n, Math.abs(ny / n), (-nx * p.s + nz * p.c) / n)));
            const q = acc.pos.length / 3;
            for (let j = 0; j < 9; j += 3) { acc.pos.push(a[i + j] * M, a[i + j + 1] * M, a[i + j + 2] * M); acc.col.push(c.r, c.g, c.b); }
            acc.idx.push(q, q + 1, q + 2);
          }
        }
        return malla.geometria(acc);
      };

      const porPieza = new Map();
      for (const e of [...lista].sort((a, b) => a.t - b.t)) if (!e.ignorar && !porPieza.has(e.pieza)) porPieza.set(e.pieza, e);
      const obras = [], polvo = [], lamparas = [], humo = [];
      let nPers = 0;
      const pers = [];          // {obra, tipo: "paseo"|"obrero", ...}
      const volteos = [];

      for (const [pid, e] of porPieza) {
        const R = e.radio_m, H = e.alto_m, ro = e.rumbo * Math.PI / 180, cr = Math.cos(ro), sr = Math.sin(ro);
        const sem = e.semilla * 7919, hz = (i, k) => hash(i + sem, k);
        const Pz = MAQ.PIEZAS[e.pieza_tipo];
        const cuerpo = e.cuerpo === null || e.cuerpo === undefined ? !(Pz && Pz.epocas) : !!e.cuerpo;
        const W = (u, v) => [e.x + (u * cr - v * sr) * M, e.y + (u * sr + v * cr) * M];   // (u a lo largo de rumbo, v a su izquierda) en metros
        const hc = gnd(e.x, e.y), Dr = Math.max(0.5, e.dur);
        // `hundir_desde_s`: lo viejo sigue en pie hasta ese segundo (desde el inicio del evento) y la obra entera (hundirse,
        // la tierra, las pilas, los tableros, los carros) cabe en lo que queda; sin él, como siempre (con su adelanto en t ≤ 0.1)
        const hD = clamp(+e.hundir_desde_s || 0, 0, Math.max(0, Dr - 1.5));
        const D = hD > 0 ? (Dr - hD) / (1 - F.viejo[0]) : Dr;                                 // segundos por unidad de u
        const t00 = hD > 0 ? e.t + hD - F.viejo[0] * D : e.t - (e.t <= 0.1 ? 0.1 * Dr : 0);
        const tU = (u) => t00 + u * D;                                                       // la fracción u → el segundo
        const centroAfuera = e.orden !== "azar";
        // `ultimo`: lo que se hunde al final de lo viejo (la fábrica: 400/401 aquí, 9000 la nave de trebol.js; las casas;
        // la gente 7000+ de la pieza; la cerca 300+; los árboles 600+)
        const ult = new Set(Array.isArray(e.ultimo) ? e.ultimo : e.ultimo ? [e.ultimo] : []);
        const claseDe = (i) => (i === 400 || i === 401 || i === 9000 ? "fabrica" : i < 300 ? "casas" : i < 400 ? "cerca" : i >= 7000 && i < 9000 ? "gente" : "arboles");
        const ajusta = (o, i) => (ult.size ? (ult.has(claseDe(i)) ? 0.86 + 0.14 * o : 0.8 * o) : o);
        const ordDe = (dist, i) => ajusta(clamp(centroAfuera ? dist * 0.9 + 0.1 * hz(i, 7) : hz(i, 8), 0, 1), i);
        const ob = { pid, e, cuerpo, R, H, D, hD, tU, hz, ajusta, viejo: [], pilas: [], tramos: [], mont: [], carros: [], hc };
        const pc = parte(e.x, e.y, 0, hc);   // la parte del centro (suelos), sin giro
        const L = (x, y, lev) => [(x - e.x) / M, (gnd(x, y) - hc) / M + lev, -(y - e.y) / M];
        const quad = (acc, a, b, c, d, lev, col) => { cara(pc, [L(...a, lev), L(...b, lev), L(...c, lev), L(...d, lev)], col, UP, acc); };

        if (cuerpo) {
          // ================= LO VIEJO: callecitas, potrero con su cerca, casas, la fábrica de tejidos genérica y árboles
          const sv = [-0.45 * R, 0.1 * R], su = [-0.4 * R, 0.42 * R], aCalle = 7, rV = 0.94 * R;
          const s0 = { acc: malla.nueva() };
          const banda = (u0, v0, u1, v1, w, lev, col) => {
            const Lg = Math.hypot(u1 - u0, v1 - v0), n = Math.max(1, Math.ceil(Lg / 6)), du = (u1 - u0) / Lg, dv = (v1 - v0) / Lg;
            for (let i = 0; i < n; i++) {
              const a0 = i / n * Lg, a1 = (i + 1) / n * Lg, P = (s, o) => W(u0 + du * s - dv * o, v0 + dv * s + du * o);
              quad(s0.acc, P(a0, -w / 2), P(a1, -w / 2), P(a1, w / 2), P(a0, w / 2), lev, col.clone().multiplyScalar(0.94 + 0.1 * hz(i + Math.round(u0 * 3 + v0 * 7), 3)));
            }
          };
          const corte = (c) => Math.sqrt(Math.max(0, rV * rV - c * c));
          for (const v of sv) banda(-corte(v), v, corte(v), v, aCalle, 0.08, cCalle0);
          for (const u of su) banda(u, -corte(u), u, corte(u), aCalle, 0.08, cCalle0);
          // el potrero (arriba a la izquierda del cruce de calles): pasto en franjas y su cerca de postes
          const pu0 = -0.88 * R, pu1 = su[0] - aCalle, pv0 = sv[1] + aCalle, pv1 = 0.82 * R;
          for (let i = 0; i < 6; i++) { const a = pu0 + (pu1 - pu0) * i / 6, b = pu0 + (pu1 - pu0) * (i + 1) / 6;
            for (let j = 0; j < 6; j++) { const c = pv0 + (pv1 - pv0) * j / 6, d = pv0 + (pv1 - pv0) * (j + 1) / 6;
              if (Math.hypot((a + b) / 2, (c + d) / 2) > rV) continue;
              quad(s0.acc, W(a, c), W(b, c), W(b, d), W(a, d), 0.1, cCampo.clone().multiplyScalar(0.88 + 0.16 * ((i + j) % 2) + 0.06 * hz(i * 7 + j, 4))); } }
          ob.suelo0 = poner(pc, mSuelo0, 2, s0.acc);
          const viejo = (p, dist, i, extra) => { ob.viejo.push({ m: poner(p, mCuerpo, 3), f: poner(p, mFoc, 4, p.foc), ord: ordDe(dist, i), p, ...extra }); };
          // la cerca: postes y dos hilos, una parte por lado
          const lados = [[pu0, pv0, pu1, pv0], [pu1, pv0, pu1, pv1], [pu1, pv1, pu0, pv1], [pu0, pv1, pu0, pv0]];
          lados.forEach(([a, b, c, d], li) => {
            const [x0, y0] = W(a, b), p = parte(x0, y0, Math.atan2(d - b, c - a) + ro), Lg = Math.hypot(c - a, d - b), n = Math.ceil(Lg / 4);
            let ok = 0;
            for (let i = 0; i <= n; i++) { const lx = Lg * i / n, [xx, yy] = W(a + (c - a) * i / n, b + (d - b) * i / n);
              if (Math.hypot((xx - e.x) / M, (yy - e.y) / M) > rV) continue; ok++;
              const y = sueloL(p, lx, 0); caja(p, lx - 0.08, lx + 0.08, y - 0.2, y + 1.3, -0.08, 0.08, cMadera);
              if (i < n) for (const hh of [0.6, 1.1]) caja(p, lx, lx + Lg / n, y + hh, y + hh + 0.04, -0.02, 0.02, cMadera.clone().multiplyScalar(0.8)); }
            if (ok) viejo(p, Math.hypot((a + c) / 2, (b + d) / 2) / R, 300 + li);
          });
          // la fábrica de tejidos genérica: nave de dientes de sierra con ventanales, portón y su chimenea aparte
          const fu = 0.02 * R, fv = -0.18 * R, fL = Math.min(56, 0.62 * (su[1] - su[0]) - 6), fW = Math.min(24, 0.4 * (sv[1] - sv[0])), fH = 6.5;
          {
            const [x, y] = W(fu, fv), p = parte(x, y, ro), b0 = Math.min(sueloL(p, -fL / 2, -fW / 2), sueloL(p, fL / 2, fW / 2), 0);
            caja(p, -fL / 2 - 0.3, fL / 2 + 0.3, b0 - 0.6, 0.6, -fW / 2 - 0.3, fW / 2 + 0.3, cZoc);
            caja(p, -fL / 2, fL / 2, 0.6, fH, -fW / 2, fW / 2, cMuro, { sinTapa: true });
            for (const sg of [-1, 1]) {                          // ventanales corridos en los lados largos, con pilastras
              const z = sg * (fW / 2 + 0.05), nv = Math.floor(fL / 4);
              for (let i = 0; i < nv; i++) { const xa = -fL / 2 + 4 * i + 0.8, xb = xa + 2.4, lit = noche && hz(i + (sg > 0 ? 50 : 0), 11) < 0.75;
                cara(p, [[xa, 2.2, z], [xb, 2.2, z], [xb, 4.8, z], [xa, 4.8, z]], lit ? cLuz.clone().multiplyScalar(0.8 + 0.2 * hz(i, 12)) : cVidrio, [0, 0, sg], lit ? p.foc : null);
                caja(p, xb + 0.3, xb + 1.0, 0.6, fH, sg > 0 ? fW / 2 : -fW / 2 - 0.35, sg > 0 ? fW / 2 + 0.35 : -fW / 2, cMuro.clone().multiplyScalar(0.9)); }
            }
            cara(p, [[fL / 2 + 0.05, 0.6, -2.5], [fL / 2 + 0.05, 0.6, 2.5], [fL / 2 + 0.05, 4.4, 2.5], [fL / 2 + 0.05, 4.4, -2.5]], cHueco, [1, 0, 0]);   // el portón
            caja(p, -fL / 2 - 0.2, fL / 2 + 0.2, fH, fH + 0.4, -fW / 2 - 0.2, fW / 2 + 0.2, cZoc);                                                     // la cornisa
            const nd = Math.max(3, Math.round(fL / 9)), dl = fL / nd, hd = 3.2;
            for (let i = 0; i < nd; i++) {                       // los dientes: faldón de lámina y cara de vidrio vertical
              const xa = -fL / 2 + i * dl, xb = xa + dl, y0 = fH + 0.4, lit = noche && hz(i, 13) < 0.6;
              cara(p, [[xa, y0, -fW / 2], [xb, y0 + hd, -fW / 2], [xb, y0 + hd, fW / 2], [xa, y0, fW / 2]], cLam.clone().multiplyScalar(0.92 + 0.08 * (i % 2)), UP);
              cara(p, [[xb, y0, -fW / 2], [xb, y0, fW / 2], [xb, y0 + hd, fW / 2], [xb, y0 + hd, -fW / 2]], lit ? cLuz.clone().multiplyScalar(0.7) : cVidrio, [1, 0, 0], lit ? p.foc : null);
              for (const z of [-fW / 2, fW / 2]) cara(p, [[xa, y0, z], [xb, y0, z], [xb, y0 + hd, z], [xb, y0 + hd, z]], cMuro.clone().multiplyScalar(0.85), [0, 0, Math.sign(z)]);
              for (let j = 1; j < 4; j++) { const f = j / 4; caja(p, xa + dl * f - 0.05, xa + dl * f + 0.05, y0 + hd * f, y0 + hd * f + 0.08, -fW / 2, fW / 2, cLamO); }
            }
            viejo(p, Math.hypot(fu, fv) / R, 400);
            const cu = fu + fL / 2 - 3, cvv = fv - fW / 2 - 4, [xc, yc] = W(cu, cvv), pch = parte(xc, yc, ro), hCh = 22;
            caja(pch, -2, 2, -0.5, 1.2, -2, 2, cZoc);
            for (let j = 0; j < 6; j++) { const y0 = 1.2 + j * (hCh - 1.2) / 6, y1 = y0 + (hCh - 1.2) / 6, r0 = 1.25 - 0.06 * j, r1 = r0 - 0.06;
              tubo(pch, [0, y0, 0], [0, y1, 0], (r0 + r1) / 2, 16, (j % 2 ? cMuro : cMuro.clone().lerp(tonos.mal, 0.25)).clone().multiplyScalar(0.92)); }
            tubo(pch, [0, hCh, 0], [0, hCh + 0.6, 0], 1.3, 16, cZoc);
            viejo(pch, Math.hypot(cu, cvv) / R, 401, { chimenea: true });
            ob.chim = { P: [xc, gnd(xc, yc) + (hCh + 0.8) * M, -yc], n: ob.viejo.length - 1 };
          }
          // las casas genéricas (lámina o losa; sin adobe ni teja: no está sostenido), a lo largo de las calles
          const fuera = (u, v, a, b) => {
            if (Math.hypot(u, v) > 0.88 * R) return true;
            for (const c of sv) if (Math.abs(v - c) < aCalle / 2 + b + 2) return true;
            for (const c of su) if (Math.abs(u - c) < aCalle / 2 + a + 2) return true;
            if (Math.abs(u - fu) < fL / 2 + a + 5 && Math.abs(v - fv) < fW / 2 + b + 8) return true;
            if (u > pu0 - a - 3 && u < pu1 + a + 3 && v > pv0 - b - 3 && v < pv1 + b + 3) return true;
            return false;
          };
          let nc = 0;
          for (let gu = -0.9 * R; gu <= 0.9 * R; gu += 15) for (let gv = -0.9 * R; gv <= 0.9 * R; gv += 14) {
            const k = nc * 31 + Math.round(gu * 3 + gv * 11 + 5000);
            const a = 3.5 + 2.2 * hz(k, 1), b = 3 + 1.4 * hz(k, 2), u = gu + (hz(k, 3) - 0.5) * 4, v = gv + (hz(k, 4) - 0.5) * 4;
            if (hz(k, 5) < 0.22 || fuera(u, v, a, b) || nc >= 46) continue;
            const [x, y] = W(u, v), p = parte(x, y, ro + (hz(k, 6) < 0.5 ? 0 : Math.PI)), Hh = 3.1 + 0.9 * hz(k, 9), dos = hz(k, 10) < 0.18;
            const b0 = Math.min(sueloL(p, -a, -b), sueloL(p, a, b), sueloL(p, a, -b), sueloL(p, -a, b), 0), Ht = dos ? 2 * Hh : Hh;
            const muro = cMuro.clone().lerp(tonos.arena, 0.3 * hz(k, 11)).multiplyScalar(0.9 + 0.15 * hz(k, 12));
            caja(p, -a - 0.12, a + 0.12, b0 - 0.4, 0.4, -b - 0.12, b + 0.12, cZoc);
            caja(p, -a, a, 0.4, Ht, -b, b, muro, { sinTapa: true });
            if (dos) caja(p, -a - 0.1, a + 0.1, Hh - 0.1, Hh + 0.12, -b - 0.1, b + 0.1, cZoc.clone().lerp(muro, 0.5));
            if (hz(k, 13) < 0.55) {                              // techo de lámina a un agua con su alero
              const t0 = Ht + 0.1, t1 = Ht + 0.9;
              cara(p, [[-a - 0.5, t0, -b - 0.6], [a + 0.5, t0, -b - 0.6], [a + 0.5, t1, b + 0.6], [-a - 0.5, t1, b + 0.6]], cLam.clone().multiplyScalar(0.88 + 0.16 * hz(k, 14)), UP);
              for (const x0 of [-a, a]) cara(p, [[x0, Ht, -b], [x0, Ht, b], [x0, t1 - 0.05, b], [x0, t0, -b]], muro, [Math.sign(x0), 0, 0]);
              cara(p, [[-a, Ht, b], [a, Ht, b], [a, t1 - 0.05, b], [-a, t1 - 0.05, b]], muro, [0, 0, 1]);
              for (let j = 1; j < 5; j++) { const xx = -a - 0.5 + (2 * a + 1) * j / 5; cara(p, [[xx - 0.04, t0 + 0.02, -b - 0.6], [xx + 0.04, t0 + 0.02, -b - 0.6], [xx + 0.04, t1 + 0.02, b + 0.6], [xx - 0.04, t1 + 0.02, b + 0.6]], cLamO, UP); }
            } else {                                             // losa con pretil
              caja(p, -a - 0.2, a + 0.2, Ht, Ht + 0.22, -b - 0.2, b + 0.2, cZoc.clone().lerp(muro, 0.4));
              for (const [x0, x1, z0, z1] of [[-a - 0.2, a + 0.2, -b - 0.2, -b + 0.05], [-a - 0.2, a + 0.2, b - 0.05, b + 0.2], [-a - 0.2, -a + 0.05, -b, b], [a - 0.05, a + 0.2, -b, b]])
                caja(p, x0, x1, Ht + 0.22, Ht + 0.7, z0, z1, muro.clone().multiplyScalar(0.94));
            }
            // el frente (−z): puerta y ventanas con marco; atrás, una ventana
            const zf = -b - 0.04, luz = (j) => noche && hz(k * 7 + j, 15) < 0.65;
            cara(p, [[-0.5, 0.4, zf], [0.5, 0.4, zf], [0.5, 2.4, zf], [-0.5, 2.4, zf]], cMadera, [0, 0, -1]);
            for (const pl of dos ? [0, Hh] : [0]) for (const sg of [-1, 1]) {
              const xa = sg * (a * 0.55) - 0.6, xb = xa + 1.2, lit = luz(sg + (pl ? 5 : 0));
              cara(p, [[xa, pl + 1.1, zf], [xb, pl + 1.1, zf], [xb, pl + 2.3, zf], [xa, pl + 2.3, zf]], lit ? cLuz.clone().multiplyScalar(0.75 + 0.25 * hz(k, 16 + sg)) : cHueco, [0, 0, -1], lit ? p.foc : null);
              caja(p, xa - 0.12, xb + 0.12, pl + 2.3, pl + 2.42, zf - 0.08, zf, cZoc);
            }
            const lit2 = luz(9);
            cara(p, [[-0.6, 1.2, b + 0.04], [0.6, 1.2, b + 0.04], [0.6, 2.2, b + 0.04], [-0.6, 2.2, b + 0.04]], lit2 ? cLuz.clone().multiplyScalar(0.7) : cHueco, [0, 0, 1], lit2 ? p.foc : null);
            viejo(p, Math.hypot(u, v) / R, nc);
            if (hz(k, 17) < 0.45) {                              // un árbol en el patio
              const [xt, yt] = W(u + (hz(k, 18) - 0.5) * 2 * a, v + (b + 3) * (hz(k, 19) < 0.5 ? 1 : -1)), pt = parte(xt, yt, 0);
              arbol(pt, 0, 0, 6 + 3 * hz(k, 20), k, hz); viejo(pt, Math.hypot(u, v) / R, 600 + nc);
            }
            nc++;
          }
          // árboles sueltos en la orilla del potrero
          for (let i = 0; i < 10; i++) {
            const u = pu0 + (pu1 - pu0) * hz(i, 21), v = hz(i, 22) < 0.5 ? pv0 + 2 : pv1 - 2;
            if (Math.hypot(u, v) > 0.92 * R) continue;
            const [x, y] = W(u, v), p = parte(x, y, 0); arbol(p, 0, 0, 7 + 4 * hz(i, 23), 700 + i, hz); viejo(p, Math.hypot(u, v) / R, 700 + i);
          }
          ob.viejo.forEach((v, i) => {
            v.t0 = tU(F.viejo[0] + (F.viejo[1] - F.viejo[0]) * v.ord); v.t1 = v.t0 + F.dv * D;
            for (let j = 0; j < 8; j++) { const a = TAU * j / 8 + hz(i * 3 + j, 90), r = 3 + 3 * hz(i + j, 91), P = [v.p.x + Math.cos(a) * r * M, v.p.h + 0.4 * M, -v.p.y - Math.sin(a) * r * M];
              polvo.push({ P, t0: v.t0, f: hz(i * 9 + j, 92) }); }
          });
          // la gente que pasea por las callecitas (mientras no llega la obra)
          for (let i = 0; i < 8; i++) {
            const hor = i % 2 === 0, c = hor ? sv[i % 4 < 2 ? 0 : 1] : su[i % 4 < 2 ? 0 : 1], lado = (hz(i, 41) < 0.5 ? -1 : 1) * (aCalle / 2 - 1);
            const span = corte(c) * 0.8, ph = hz(i, 42) * 4 * span, vel = 1.1 + 0.3 * hz(i, 43);
            pers.push({ ob, tipo: "paseo", hor, c, lado, span, ph, vel, rad: 0, sale: tU(F.tierra[0] + 0.1 * (F.tierra[1] - F.tierra[0]) + 0.5 * hz(i, 44) * (F.tierra[1] - F.tierra[0])) });
          }

          // ================= LO NUEVO: tres puentes sobre tres calzadas a nivel (ilustrativo, sin nombres)
          const rO = 0.42 * R, Ld = 0.95 * R, Lf = 0.42 * Ld, Lr = (Ld - Lf) / 2, Wd = 15, sh = Lf / 2 + 0.5 * Lr, Ls = 0.14 * R;
          const prof = (s) => { const a = Math.abs(s); return a <= Lf / 2 ? 1 : a >= Ld / 2 ? 0 : ease(1 - (a - Lf / 2) / Lr); };
          ob.decks = [];
          for (let k = 0; k < 3; k++) {
            const al = ro + k * TAU / 3, phi = al + Math.PI / 2, cx = e.x + Math.cos(al) * rO * M, cy = e.y + Math.sin(al) * rO * M;
            const P = (s) => [cx + Math.cos(phi) * s * M, cy + Math.sin(phi) * s * M];
            const g = (s) => gnd(...P(s)), Y = (s) => g(s) + (H * prof(s) + 0.3) * M;
            const dk = { k, al, phi, P, g, Y, prof, Ld, Lf, sh, Ls, Wd };
            ob.decks.push(dk);
            // los tramos: del centro del puente hacia cada punta (elevados hasta sh, macizos hasta Ld/2)
            const nE = Math.max(2, Math.round(sh / 16)), nR = Math.max(2, Math.round((Ld / 2 - sh) / 14));
            const cortes = [...Array.from({ length: nE + 1 }, (_, i) => sh * i / nE), ...Array.from({ length: nR }, (_, i) => sh + (Ld / 2 - sh) * (i + 1) / nR)];
            for (const sg of [1, -1]) for (let i = 0; i + 1 < cortes.length; i++) {
              const sa = sg * cortes[i], sb = sg * cortes[i + 1], elev = i < nE;
              const P0 = P(sa), p = parte(P0[0], P0[1], sg > 0 ? phi : phi + Math.PI), Wm = Wd / 2;
              const yT = (s) => (Y(s) - p.h) / M, yG = (s) => (g(s) - p.h) / M, n = Math.max(2, Math.ceil(Math.abs(sb - sa) / 3.5));
              for (let j = 0; j < n; j++) {
                const a0 = sa + (sb - sa) * j / n, a1 = sa + (sb - sa) * (j + 1) / n, x0 = Math.abs(a0 - sa), x1 = Math.abs(a1 - sa), t0 = yT(a0), t1 = yT(a1);
                cara(p, [[x0, t0, -Wm + 0.4], [x1, t1, -Wm + 0.4], [x1, t1, Wm - 0.4], [x0, t0, Wm - 0.4]], cAsf.clone().multiplyScalar(0.96 + 0.06 * hz(k * 97 + i * 7 + j, 50)), UP);
                for (const z of [-0.3, 0.3]) cara(p, [[x0, t0 + 0.03, z - 0.07], [x1, t1 + 0.03, z - 0.07], [x1, t1 + 0.03, z + 0.07], [x0, t0 + 0.03, z + 0.07]], cRaya, UP);
                for (const z of [-Wm + 1.1, Wm - 1.1]) cara(p, [[x0, t0 + 0.03, z - 0.08], [x1, t1 + 0.03, z - 0.08], [x1, t1 + 0.03, z + 0.08], [x0, t0 + 0.03, z + 0.08]], cRaya.clone().multiplyScalar(0.85), UP);
                for (const z of [-3.6, 3.6]) if ((Math.floor(Math.abs(a0) / 3.5) % 2) === 0) cara(p, [[x0, t0 + 0.03, z - 0.07], [x1, t1 + 0.03, z - 0.07], [x1, t1 + 0.03, z + 0.07], [x0, t0 + 0.03, z + 0.07]], cRaya.clone().multiplyScalar(0.8), UP);
                for (const sz of [-1, 1]) {                       // pretil de concreto y la cara del puente (o el muro de la rampa)
                  const zi = sz * (Wm - 0.4), zo = sz * Wm, b0 = elev ? t0 - 1.2 : yG(a0) - 0.4, b1 = elev ? t1 - 1.2 : yG(a1) - 0.4;
                  cara(p, [[x0, t0, zi], [x1, t1, zi], [x1, t1 + 0.95, zi], [x0, t0 + 0.95, zi]], cConc, [0, 0, -sz]);
                  cara(p, [[x0, t0 + 0.95, zi], [x1, t1 + 0.95, zi], [x1, t1 + 0.95, zo], [x0, t0 + 0.95, zo]], cConc.clone().multiplyScalar(1.05), UP);
                  cara(p, [[x0, b0, zo], [x1, b1, zo], [x1, t1 + 0.95, zo], [x0, t0 + 0.95, zo]], elev ? cConc : cConcO, [0, 0, sz]);
                  if (elev) cara(p, [[x0, t0 - 0.35, zo + sz * 0.02], [x1, t1 - 0.35, zo + sz * 0.02], [x1, t1 - 0.2, zo + sz * 0.02], [x0, t0 - 0.2, zo + sz * 0.02]], cConcO, [0, 0, sz]);   // el goterón
                }
                if (elev) cara(p, [[x0, t0 - 1.2, -Wm], [x1, t1 - 1.2, -Wm], [x1, t1 - 1.2, Wm], [x0, t0 - 1.2, Wm]], cConcO.clone().multiplyScalar(0.8), [0, -1, 0]);
                if (elev) for (const z of [-Wm + 2.2, 0, Wm - 2.2]) cara(p, [[x0, t0 - 1.75, z - 0.4], [x1, t1 - 1.75, z - 0.4], [x1, t1 - 1.2, z - 0.4], [x0, t0 - 1.2, z - 0.4]], cConcO.clone().multiplyScalar(0.75), [0, 0, -1]);   // las vigas
              }
              if (!elev && i === nE) caja(p, -0.2, 0.2, yG(sa) - 0.4, yT(sa) - 1.2, -Wm, Wm, cConcO);       // el estribo
              let lamp = null;
              if (elev && i % 2 === 0) {                           // un poste de luz con su brazo
                const zp = (i % 4 === 0 ? 1 : -1) * (Wm - 0.2), y0 = yT(sa) + 0.95, y1 = y0 + 8.5, za = zp - Math.sign(zp) * 2.2;
                tubo(p, [0.6, y0, zp], [0.6, y1, zp], 0.13, 10, cMetal);
                tubo(p, [0.6, y1, zp], [0.6, y1 + 0.3, za], 0.08, 8, cMetal);
                caja(p, 0.25, 0.95, y1 + 0.05, y1 + 0.4, za - 0.35, za + 0.35, cMetal, noche ? {} : {});
                cara(p, [[0.3, y1 + 0.04, za - 0.3], [0.9, y1 + 0.04, za - 0.3], [0.9, y1 + 0.04, za + 0.3], [0.3, y1 + 0.04, za + 0.3]], noche ? cLuz : cMetal.clone().multiplyScalar(1.3), [0, -1, 0], p.foc);
                lamp = [0.6, y1 - 0.2, za];
              }
              const ord = (Math.abs(sa) / (Ld / 2)) * 0.88 + 0.04 * k + 0.08 * hz(k * 40 + i * 2 + (sg > 0 ? 1 : 0), 51);
              const tr = { m: poner(p, mCuerpo, 3), f: poner(p, mFoc, 4, p.foc), p, ord: centroAfuera ? clamp(ord, 0, 1) : hz(k * 40 + i * 2 + (sg > 0 ? 1 : 0), 52) };
              tr.t0 = tU(F.tableros[0] + (F.tableros[1] - F.tableros[0]) * tr.ord); tr.t1 = tr.t0 + F.dt * D;
              ob.tramos.push(tr);
              if (lamp) { const [lx, , lz] = lamp, [xs, ys] = aEscena(p, lx, lz); lamparas.push({ P: [xs, p.h + lamp[1] * M, -ys], t0: tr.t1, f: hz(k * 13 + i, 53) }); }
              // la pila bajo el comienzo del tramo elevado
              if (elev && (sg > 0 || i > 0)) {
                const Pp = P(sa), pp = parte(Pp[0], Pp[1], phi), yTop = (Y(sa) - pp.h) / M - 1.75, zc = Wm - 3.2;
                caja(pp, -1.7, 1.7, -0.6, 0.3, -Wm + 1.2, Wm - 1.2, cConcO);                                   // la zapata
                for (const z of [-zc, zc]) { tubo(pp, [0, 0.2, z], [0, yTop - 1.1, z], 0.6, 14, cConc); caja(pp, -0.75, 0.75, 0.15, 0.45, z - 0.75, z + 0.75, cConcO); }
                caja(pp, -0.85, 0.85, yTop - 1.1, yTop, -Wm + 0.9, Wm - 0.9, cConc.clone().multiplyScalar(0.95));     // la viga cabezal
                const op = (Math.abs(sa) / sh) * 0.85 + 0.05 * k + 0.1 * hz(k * 40 + i, 54);
                const pl = { m: poner(pp, mCuerpo, 3), p: pp, ord: centroAfuera ? clamp(op, 0, 1) : hz(k * 40 + i, 55) };
                pl.t0 = tU(F.pilas[0] + (F.pilas[1] - F.pilas[0]) * pl.ord); pl.t1 = pl.t0 + F.dp * D;
                ob.pilas.push(pl);
              }
            }
          }
          // ---- las calzadas nuevas a nivel: tres que llegan al cruce por debajo de los puentes, y las que siguen a las rampas
          const qs = [];
          const tira = (A, B, w, rayas) => {
            const Lg = Math.hypot(B[0] - A[0], B[1] - A[1]), n = Math.max(1, Math.ceil(Lg / 5)), du = (B[0] - A[0]) / Lg, dv = (B[1] - A[1]) / Lg;
            for (let i = 0; i < n; i++) {
              const a0 = Lg * i / n, a1 = Lg * (i + 1) / n, Q = (s, o) => [A[0] + (du * s - dv * o) * M, A[1] + (dv * s + du * o) * M];
              const d = Math.hypot((Q((a0 + a1) / 2, 0)[0] - e.x) / M, (Q((a0 + a1) / 2, 0)[1] - e.y) / M);
              qs.push({ d, q: [Q(a0, -w / 2), Q(a1, -w / 2), Q(a1, w / 2), Q(a0, w / 2)], col: cAsf.clone().multiplyScalar(0.95 + 0.07 * hz(i + qs.length, 56)), lev: 0.35, acc: "c" });
              if (rayas && (i % 2 === 0)) qs.push({ d, q: [Q(a0, -0.12), Q(a1, -0.12), Q(a1, 0.12), Q(a0, 0.12)], col: cRaya, lev: 0.38, acc: "r" });
              if (rayas) for (const o of [-w / 2 + 0.9, w / 2 - 0.9]) qs.push({ d, q: [Q(a0, o - 0.08), Q(a1, o - 0.08), Q(a1, o + 0.08), Q(a0, o + 0.08)], col: cRaya.clone().multiplyScalar(0.85), lev: 0.38, acc: "r" });
            }
          };
          for (const dk of ob.decks) {
            tira([e.x, e.y], [e.x + Math.cos(dk.al) * 1.0 * R * M, e.y + Math.sin(dk.al) * 1.0 * R * M], 14, true);
            for (const sg of [1, -1]) tira(dk.P(sg * (dk.Ld / 2 - 0.5)), dk.P(sg * (dk.Ld / 2 + dk.Ls)), Wd - 0.8, true);
          }
          const nd = 28;                                         // la plancha del cruce
          for (let i = 0; i < nd; i++) { const a0 = TAU * i / nd, a1 = TAU * (i + 1) / nd, r = 19;
            qs.push({ d: 0, q: [[e.x, e.y], [e.x + Math.cos(a0) * r * M, e.y + Math.sin(a0) * r * M], [e.x + Math.cos(a1) * r * M, e.y + Math.sin(a1) * r * M], [e.x, e.y]], col: cAsf.clone().multiplyScalar(0.92), lev: 0.33, acc: "c" }); }
          qs.sort((a, b) => a.d - b.d);
          const aC = malla.nueva(), aR = malla.nueva(), cc = [0], cR = [0];
          for (const q of qs) { quad(q.acc === "c" ? aC : aR, ...q.q, q.lev, q.col); cc.push(aC.idx.length); cR.push(aR.idx.length); }
          ob.calles = { c: poner(pc, mCalle, 2, aC), r: poner(pc, mRaya, 3, aR), cc, cR, n: qs.length };
          // ---- los carros de la época nueva: por cada puente, dos carriles en cada sentido; y en las calzadas de abajo
          const vehs = tonos.vehiculos && tonos.vehiculos.length ? tonos.vehiculos : [tonos.secundario];
          const nA = Math.max(0, e.autos);
          let ic = 0;
          for (const dk of ob.decks) for (let j = 0; j < nA; j++) {
            const dir = j % 2 ? -1 : 1, carril = (Math.floor(j / 2) % 2 ? 5.2 : 1.9), off = dir * carril;   // a la derecha de su sentido
            const g = carroGeo(dir > 0 ? dk.phi : dk.phi + Math.PI, vehs[(ic * 3 + e.semilla) % vehs.length]);
            if (!g) break;
            const m = new THREE.Mesh(g, mCuerpo); m.frustumCulled = false; m.renderOrder = 4; m.visible = false; scene.add(m);
            const Ltot = dk.Ld + 2 * dk.Ls;
            ob.carros.push({ m, dk, dir, off, Ltot, ph: hz(ic, 60) * Ltot + j * Ltot / Math.max(1, nA), v: 7 + 3 * hz(ic, 61), t0: tU(F.carros[0] + (F.carros[1] - F.carros[0]) * hz(ic, 62)) });
            ic++;
          }
          for (const dk of ob.decks) for (let j = 0; j < 2; j++) {
            const dir = j ? -1 : 1, ang = dk.al + (dir > 0 ? Math.PI : 0), g = carroGeo(ang, vehs[(ic * 5 + 1) % vehs.length]);
            if (!g) break;
            const m = new THREE.Mesh(g, mCuerpo); m.frustumCulled = false; m.renderOrder = 4; m.visible = false; scene.add(m);
            ob.carros.push({ m, suelo: true, al: dk.al, dir, Ltot: R - 16, ph: hz(ic, 63) * R, v: 6 + 3 * hz(ic, 64), t0: tU(F.carros[0] + (F.carros[1] - F.carros[0]) * hz(ic, 65)) });
            ic++;
          }
        }

        // ================= LA OBRA (siempre): el terreno de tierra, los montículos que se empujan, volteos y obreros
        {
          const NR = 26, NSc = 72, aT = malla.nueva(), cT = [0], Rt = 1.0 * R, ph0 = 6 * hz(0, 71);
          const rad = (i, j) => Rt * (i / NR) * (1 + (i === NR ? 0.06 * (hz(j % NSc, 70) - 0.5) : 0));
          // el suelo removido no es plano: ondula hasta ≈ 0.5 m (se apaga en la orilla), y la luz lo dibuja
          const und = (x, y) => { const u = (x - e.x) / M, v = (y - e.y) / M, r = Math.hypot(u, v) / Rt;
            return (0.16 * (1 + Math.sin(u * 0.13 + ph0) * Math.cos(v * 0.11 - ph0)) + 0.09 * (1 + Math.sin(u * 0.31 - v * 0.27 + 2 * ph0))) * (1 - ctx.suave(0.86, 1.02, r)); };
          const quadU = (acc, Q, base, col, ref) => cara(pc, Q.map(([x, y, lv]) => L(x, y, base + und(x, y) + (lv || 0))), col, ref || UP, acc);
          // ---- lo que se lee de lejos en la tierra: ZANJAS (fondo oscuro, paredes, bordos de tierra sacada a los lados) a lo
          // largo de donde van las pilas, y MONTONES de tierra sacada; cada cosa en el anillo de su distancia (se abre con la tierra)
          const aZ = malla.nueva(), cZ = [0], porAnillo = Array.from({ length: NR }, () => []), anillo = (x, y) => Math.min(NR - 1, Math.floor(Math.hypot(x - e.x, y - e.y) / M / Rt * NR));
          const cFondo = TIE[0].clone().lerp(cHueco, 0.55), cPared = TIE[2].clone().multiplyScalar(0.62), cBordo = TIE[1].clone().multiplyScalar(1.04);
          const ejes = [];
          if (cuerpo && ob.decks && ob.decks.length) for (const dk of ob.decks) ejes.push({ P: dk.P, s0: -0.47 * dk.Ld, s1: 0.47 * dk.Ld, ph: dk.phi });
          else for (let k = 0; k < 3; k++) { const a = ro + k * TAU / 3 + TAU / 6, ca = Math.cos(a), sa = Math.sin(a);
            ejes.push({ P: (s) => [e.x + ca * s * M, e.y + sa * s * M], s0: 0.12 * R, s1: 0.86 * R, ph: a }); }
          ejes.forEach((z, k) => {
            const nx = -Math.sin(z.ph), ny = Math.cos(z.ph), n = Math.max(2, Math.ceil((z.s1 - z.s0) / 6));
            for (let j = 0; j < n; j++) {
              if (hz(k * 50 + j, 74) < 0.12) continue;                     // la zanja no es corrida: tiene cortes donde se pasa
              const sa = z.s0 + (z.s1 - z.s0) * j / n, sb = z.s0 + (z.s1 - z.s0) * (j + 1) / n, A = z.P(sa), B = z.P(sb);
              const Q = (P, o) => [P[0] + nx * o * M, P[1] + ny * o * M];
              const alt = 1.25 + 0.35 * hz(k * 50 + j, 75);
              porAnillo[anillo((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)].push(() => {
                const fo = (P, o) => L(...Q(P, o), 0.24 + und(...Q(P, o)));   // el fondo: apenas sobre la tierra, oscuro; lo hondo lo dicen las paredes
                cara(pc, [fo(A, -1.9), fo(B, -1.9), fo(B, 1.9), fo(A, 1.9)], cFondo, UP, aZ);
                for (const sg of [-1, 1]) {
                  const o0 = sg * 1.9, o1 = sg * 3.1, o2 = sg * 5.6;
                  cara(pc, [fo(A, o0), fo(B, o0), L(...Q(B, o1), 0.18 + und(...Q(B, o1)) + alt), L(...Q(A, o1), 0.18 + und(...Q(A, o1)) + alt)], cPared, null, aZ);
                  cara(pc, [L(...Q(A, o1), 0.18 + und(...Q(A, o1)) + alt), L(...Q(B, o1), 0.18 + und(...Q(B, o1)) + alt), L(...Q(B, o2), 0.18 + und(...Q(B, o2))), L(...Q(A, o2), 0.18 + und(...Q(A, o2)))], cBordo.clone().multiplyScalar(0.94 + 0.1 * hz(j * 2 + (sg > 0 ? 1 : 0), 76)), UP, aZ);
                }
              });
            }
          });
          const pZ = { ...pc, acc: aZ };
          for (let i = 0; i < 16; i++) {                                    // montones de tierra sacada: dos o tres lomos cada uno
            const a = TAU * hz(i, 77), r = (0.18 + 0.68 * hz(i, 78)) * R, x = e.x + Math.cos(a) * r * M, y = e.y + Math.sin(a) * r * M, s = 1 + 0.7 * hz(i, 79);
            const P0 = [(x - e.x) / M, (gnd(x, y) - hc) / M + 0.18 + und(x, y), -(y - e.y) / M], g = TAU * hz(i, 80);
            porAnillo[anillo(x, y)].push(() => {
              gema(pZ, P0, 6.5 * s, 2.6 * s, 5 * s, g, TIE[i % 3].clone().multiplyScalar(0.92 + 0.12 * hz(i, 81)));
              gema(pZ, [P0[0] + 4.5 * s * Math.cos(g), P0[1], P0[2] + 4.5 * s * Math.sin(g)], 4.2 * s, 1.8 * s, 3.6 * s, g + 0.9, TIE[(i + 1) % 3].clone().multiplyScalar(0.9));
              if (hz(i, 82) < 0.5) gema(pZ, [P0[0] - 3.8 * s * Math.sin(g), P0[1], P0[2] + 3.8 * s * Math.cos(g)], 3.4 * s, 1.5 * s, 3 * s, g - 0.7, TIE[(i + 2) % 3].clone().multiplyScalar(0.96));
            });
          }
          for (let i = 0; i < NR; i++) {
            for (let j = 0; j < NSc; j++) {
              const a0 = TAU * j / NSc, a1 = TAU * (j + 1) / NSc, r0 = rad(i, j), r1 = rad(i + 1, j), r1b = rad(i + 1, j + 1);
              const P = (r, a) => [e.x + Math.cos(a) * r * M, e.y + Math.sin(a) * r * M];
              // tierra removida: manchas suaves (dos ondas lentas por radio y ángulo), sin alternar celda a celda (no es un damero)
              const am = (j + 0.5) * TAU / NSc;
              const w1 = 0.5 + 0.5 * Math.sin(am * 3 + i * 0.23 + ph0) * Math.cos(i * 0.17 - am * 2 + ph0);
              const w2 = 0.5 + 0.5 * Math.sin(am * 5 - i * 0.29 + 2 * ph0);
              const col = TIE[0].clone().lerp(TIE[1].clone().lerp(TIE[2], w2), 0.55 * w1).multiplyScalar(0.97 + 0.03 * hz(i * NSc + j, 72));
              quadU(aT, [P(r0, a0), P(r1, a0), P(r1b, a1), P(r0, a1)], 0.18, col);
            }
            cT.push(aT.idx.length);
            for (const f of porAnillo[i]) f();
            cZ.push(aZ.idx.length);
          }
          ob.tierra = { m: poner(pc, mTierra, 2, aT), cortes: cT, NR, z: poner(pc, mCuerpo, 3, aZ), cZ };
          // montículos: nacen, se empujan de A a B y se aplanan
          for (let i = 0; i < 9; i++) {
            const a = TAU * hz(i, 80), r = (0.15 + 0.6 * hz(i, 81)) * R, b = a + (hz(i, 82) - 0.5) * 1.2, r2 = clamp(r + (hz(i, 83) - 0.5) * 0.4 * R, 0.1 * R, 0.8 * R);
            const A = [e.x + Math.cos(a) * r * M, e.y + Math.sin(a) * r * M], B = [e.x + Math.cos(b) * r2 * M, e.y + Math.sin(b) * r2 * M];
            const p = parte(A[0], A[1], 0), s = 0.9 + 0.6 * hz(i, 84);
            gema(p, [0, 0, 0], 7 * s, 2.8 * s, 6 * s, TAU * hz(i, 85), TIE[i % 3].clone().multiplyScalar(0.95));
            gema(p, [3 * s, 0, 2 * s], 4 * s, 1.6 * s, 3.5 * s, TAU * hz(i, 86), TIE[(i + 1) % 3].clone().multiplyScalar(0.9));
            const u0 = F.mont[0] + (F.mont[1] - F.mont[0] - 0.18) * hz(i, 87);
            const mt = { m: poner(p, mCuerpo, 3), A, B, t0: tU(u0), t1: tU(u0 + 0.18 + 0.06 * hz(i, 88)) };
            ob.mont.push(mt);
            for (let j = 0; j < 6; j++) polvo.push({ P: [A[0] + Math.cos(j) * 5 * M, gnd(A[0], A[1]) + 0.5 * M, -A[1] - Math.sin(j) * 5 * M], t0: mt.t0 + 0.5, f: hz(i * 7 + j, 89) });
          }
          for (let i = 0; i < Math.max(0, e.volteos); i++) volteos.push({ ob, r: (0.5 + 0.1 * i) * R, ph: hz(i, 93) * TAU, v: 5.5 + hz(i, 94), sg: i % 2 ? -1 : 1, tA: tU(F.volteos[0]) });
          const sitios = ob.pilas.length ? ob.pilas.map((q) => [q.p.x, q.p.y]) : Array.from({ length: 6 }, (_, i) => [e.x + Math.cos(TAU * i / 6 + ro) * 0.4 * R * M, e.y + Math.sin(TAU * i / 6 + ro) * 0.4 * R * M]);
          for (let i = 0; i < Math.max(0, e.obreros); i++) {
            const s = sitios[Math.floor(hz(i, 95) * sitios.length) % sitios.length], a = TAU * hz(i, 96), r = 7 + 4 * hz(i, 97);
            pers.push({ ob, tipo: "obrero", x: s[0] + Math.cos(a) * r * M, y: s[1] + Math.sin(a) * r * M, a: a + Math.PI / 2, camina: i % 3 === 1, vel: 0.9 + 0.3 * hz(i, 98), ph: hz(i, 99) * 10 });
          }
        }
        obras.push(ob);
      }

      // ---- puntos: polvo, lámparas de los postes, humo de la chimenea (shaders con uT: seek puro)
      const uT = { value: 0 }, uPx = { value: 1 };
      const puntos = (lst, vs, fs, uni, orden, aditivo) => {
        if (!lst.length) return null;
        const g = new THREE.BufferGeometry(), pos = new Float32Array(lst.length * 3), a1 = new Float32Array(lst.length * 2);
        lst.forEach((p, i) => { pos.set(p.P, i * 3); a1.set([p.t0, p.f], i * 2); });
        g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aD", new THREE.BufferAttribute(a1, 2));
        const mat = new THREE.ShaderMaterial({ uniforms: { uT, uPx, ...uni }, transparent: true, depthWrite: false, vertexShader: vs, fragmentShader: fs,
          blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending });
        const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m;
      };
      puntos(polvo, "uniform float uT, uPx, uM; attribute vec2 aD; varying float vA; void main(){ float a = (uT - aD.x) / 2.0; vec3 p = position; " +
        "float v = clamp(a, 0.0, 1.0); p.y += (0.5 + 4.0 * v) * uM * (0.7 + 0.6 * aD.y); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; " +
        "gl_PointSize = (a > 0.0 && a < 1.0) ? clamp((3.0 + 7.0 * v) * uM * uPx / max(1e-3, -mv.z), 1.0, 80.0) : 0.0; vA = (a > 0.0 && a < 1.0) ? (1.0 - v) * smoothstep(0.0, 0.1, v) : 0.0; }",
        SRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.4); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }",
        { uM: { value: M }, cA: { value: cPolvo }, uK: { value: noche ? 0.3 : 0.55 } }, 8, false);
      if (noche) puntos(lamparas, "uniform float uT, uPx, uM; attribute vec2 aD; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; " +
        "float on = smoothstep(aD.x - 0.1, aD.x + 0.4, uT); gl_PointSize = on > 0.0 ? clamp(9.0 * uM * uPx / max(1e-3, -mv.z), 2.0, 34.0) : 0.0; vA = on * (0.9 + 0.1 * sin(uT * 3.1 + aD.y * 40.0)); }",
        SRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.7 * vA * (exp(-r * r * 5.0) + 0.5 * exp(-r * r * 40.0)); gl_FragColor = vec4(srgb(cA) * a, a); }",
        { uM: { value: M }, cA: { value: cLuz.clone() } }, 9, true);
      // el humo de la chimenea: bocanadas que suben y se abren, mientras la chimenea está en pie
      const chims = obras.filter((o) => o.chim);
      for (const o of chims) for (let j = 0; j < 22; j++) humo.push({ P: o.chim.P, t0: j / 22, f: o.hz(j, 101) });
      const mHumo = puntos(humo, "uniform float uT, uPx, uM, uOn; attribute vec2 aD; varying float vA; void main(){ float a = fract(uT * 0.16 + aD.x); vec3 p = position; " +
        "p.y += a * 16.0 * uM; p.x += a * a * 9.0 * uM * (0.6 + 0.6 * aD.y); p.z += (aD.y - 0.5) * a * 6.0 * uM; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; " +
        "gl_PointSize = uOn > 0.0 ? clamp((2.5 + 7.0 * a) * uM * uPx / max(1e-3, -mv.z), 1.0, 70.0) : 0.0; vA = uOn * (1.0 - a) * smoothstep(0.0, 0.12, a); }",
        SRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.2); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }",
        { uM: { value: M }, uOn: { value: 1 }, cA: { value: cHumo }, uK: { value: noche ? 0.25 : 0.45 } }, 8, false);
      // los faros de los carros (de noche)
      const nCar = obras.reduce((s, o) => s + o.carros.length, 0);
      let faros = null;
      if (noche && nCar) {
        const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(nCar * 6), 3)); g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(nCar * 2), 1));
        const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uM: { value: M }, cA: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "uniform float uPx, uM; attribute float aK; varying float vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aK > 0.0 ? clamp(2.6 * uM * uPx / max(1e-3, -mv.z), 2.5, 14.0) : 0.0; }",
          fragmentShader: SRGB + "uniform vec3 cA; varying float vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vK * (exp(-r * r * 8.0) + exp(-r * r * 50.0)); gl_FragColor = vec4(srgb(cA) * a, a); }" });
        const pts = new THREE.Points(g, mat); pts.frustumCulled = false; pts.renderOrder = 9; scene.add(pts);
        faros = { g };
      }
      // la gente: paseantes de lo viejo y obreros (persona, sin rostro), y los volteos genéricos de la obra
      const tamP = M * (ctx.unidad_m || 1) * (lista[0] ? lista[0].gente_tamano || 1.6 : 1.6);
      const flP = pers.length ? ctx.flota("persona", pers.length, { tamano: tamP, orden: 6, semilla: 17, pose: (i) => {
        const q = pers[i]; return q && q.tipo === "obrero" ? (q.camina ? "caminar" : (i % 3 === 0 ? "cargar" : "de_pie")) : "caminar"; } }) : null;
      const tamV = M * (ctx.unidad_m || 1) * (lista[0] ? lista[0].volteos_tamano || 1 : 1);
      const flV = volteos.length && MAQ.OBJETOS.volteo ? ctx.flota("volteo", volteos.length, { tamano: tamV, orden: 5, semilla: 5, pose: "rodar" }) : null;
      return { obras, uT, uPx, mCuerpo, mHumo, faros, flP, pers, flV, volteos };
    },

    inicio(t, st, ctx) {
      if (!st) return;
      st.uT.value = t;
      const E = ctx.cuadro.epoca = ctx.cuadro.epoca || {}, { clamp } = ctx;
      for (const o of st.obras) {
        const u = clamp((t - o.tU(0)) / o.D, 0, 1), f = (a) => clamp((u - a[0]) / (a[1] - a[0]), 0, 1);
        // hunde(x, y, i): cuánto se ha hundido (0–1) lo viejo de la PIEZA en (x, y) escena, en el mismo turno que lo viejo de
        // la obra (centro-afuera o azar); 0 fuera del radio de la obra (+12 m): lo de afuera se queda
        const M = ctx.metros(1), hunde = (x, y, i) => {
          const d = Math.hypot(x - o.e.x, y - o.e.y) / M; if (d > o.R + 12) return 0;
          const ord = o.ajusta(o.e.orden !== "azar" ? clamp((d / o.R) * 0.9 + 0.1 * o.hz(i + 5000, 7), 0, 1) : o.hz(i + 5000, 8), i);
          const a = o.tU(F.viejo[0] + (F.viejo[1] - F.viejo[0]) * ord);
          return ease(clamp((t - a) / Math.max(1e-3, F.dv * o.D), 0, 1));
        };
        E[o.pid] = { de: o.e.de, a: o.e.a, u, viejo: f([F.viejo[0], F.viejo[1] + F.dv]), tierra: f(F.tierra), pilas: f([F.pilas[0], F.pilas[1] + F.dp]),
          tableros: f([F.tableros[0], F.tableros[1] + F.dt]), carros: f(F.carros), x: o.e.x, y: o.e.y, radio_m: o.R, hunde };
      }
    },

    aplicar(t, e, ctx, st) {
      if (!st) return;
      const b = ctx.cuadro && ctx.cuadro.brillo ? ctx.cuadro.brillo[e.pieza] : 0;
      st.mCuerpo.uniforms.uBrillo.value = 1 + (b ? 0.3 * ctx.clamp((b - 1) / 0.9, 0, 1.2) : 0);
    },

    en(t, st, ctx) {
      if (!st) return;
      const { clamp, suave } = ctx, M = ctx.metros(1);
      st.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      const rebote = (x) => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
      let iF = 0, humoOn = 0;
      const FA = st.faros ? st.faros.g.attributes : null;
      for (const o of st.obras) {
        const u = (t - o.tU(0)) / o.D, ent = (a, b) => clamp((u - a) / Math.max(1e-3, b - a), 0, 1);
        // lo viejo: cada parte se hunde en su turno
        for (const v of o.viejo) {
          const k = clamp((t - v.t0) / Math.max(1e-3, v.t1 - v.t0), 0, 1), s = 1 - ease(k), vis = s > 0.002;
          for (const m of [v.m, v.f]) if (m) { m.visible = vis; m.scale.set(1 + 0.06 * k, Math.max(1e-3, s), 1 + 0.06 * k); }
          if (v.chimenea) humoOn = Math.max(humoOn, s);
        }
        if (o.suelo0) o.suelo0.visible = u < F.tierra[1] + 0.02;
        // la tierra: se abre del centro hacia afuera; al final, jardín (o se recoge, si la pieza dibuja sus épocas)
        const kT = ease(ent(F.tierra[0], F.tierra[1])) * (o.cuerpo ? 1 : 1 - ease(ent(F.verde[0], F.verde[1])));
        const nr = Math.round(kT * o.tierra.NR);
        o.tierra.m.visible = nr > 0; o.tierra.m.geometry.setDrawRange(0, o.tierra.cortes[nr]);
        o.tierra.m.material.uniforms.uTinte.value = o.cuerpo ? 0.9 * ease(ent(F.verde[0], F.verde[1])) : 0;
        // zanjas y montones: se abren con la tierra y se aplanan cuando se asfalta y se siembra
        if (o.tierra.z) { const kz = 1 - ease(ent(F.calles[0], F.verde[1]));
          o.tierra.z.visible = nr > 0 && kz > 0.01; o.tierra.z.geometry.setDrawRange(0, o.tierra.cZ[nr]); o.tierra.z.scale.set(1, Math.max(1e-3, kz), 1); }
        // los montículos: crecen, se empujan de A a B y se aplanan
        for (const mt of o.mont) {
          const k = (t - mt.t0) / Math.max(1e-3, mt.t1 - mt.t0), vis = k > 0 && k < 1;
          mt.m.visible = vis; if (!vis) continue;
          const g = suave(0, 0.2, k) * (1 - suave(0.75, 1, k)), w = ease(clamp((k - 0.15) / 0.7, 0, 1));
          const x = mt.A[0] + (mt.B[0] - mt.A[0]) * w, y = mt.A[1] + (mt.B[1] - mt.A[1]) * w;
          mt.m.position.set(x, ctx.suelo(x, y), -y); mt.m.scale.set(0.6 + 0.4 * g, Math.max(1e-3, g), 0.6 + 0.4 * g);
        }
        // las pilas suben; los tableros se tienden tramo a tramo desde el centro de cada puente
        for (const p of o.pilas) {
          const k = clamp((t - p.t0) / Math.max(1e-3, p.t1 - p.t0), 0, 1);
          p.m.visible = k > 0.001; p.m.scale.set(1, Math.max(1e-3, ease(k)), 1);
        }
        for (const r of o.tramos) {
          const k = clamp((t - r.t0) / Math.max(1e-3, r.t1 - r.t0), 0, 1), s = clamp(rebote(k), 0, 1.04);
          for (const m of [r.m, r.f]) if (m) { m.visible = k > 0.001; m.scale.set(Math.max(1e-3, Math.min(1, s)), 1, 1); m.position.y = r.p.h + (1 - ease(k)) * 2.5 * M; }
        }
        // las calzadas nuevas se asfaltan del cruce hacia afuera
        if (o.calles) {
          const n = Math.round(ease(ent(F.calles[0], F.calles[1])) * o.calles.n);
          o.calles.c.visible = n > 0; o.calles.c.geometry.setDrawRange(0, o.calles.cc[n]);
          o.calles.r.visible = n > 0; o.calles.r.geometry.setDrawRange(0, o.calles.cR[n]);
        }
        // los carros: entran en su turno y siguen andando (posición = función de t)
        for (const c of o.carros) {
          const k = clamp((t - c.t0) / 0.6, 0, 1);
          if (k <= 0) { c.m.visible = false; if (FA) { FA.aK.setX(iF * 2, 0); FA.aK.setX(iF * 2 + 1, 0); } iF++; continue; }
          const s = (((c.v * t + c.ph) % c.Ltot) + c.Ltot) % c.Ltot, fin = suave(0, 6, s) * (1 - suave(c.Ltot - 6, c.Ltot, s));
          let x, y, z, head, pitch = 0;
          if (c.suelo) {                                     // por la calzada de abajo: entra al cruce o sale de él
            const r = c.dir > 0 ? o.R - s : 16 + s, lat = c.dir > 0 ? 1.9 : -1.9, ca = Math.cos(c.al), sa = Math.sin(c.al);
            x = o.e.x + (ca * r + sa * lat) * M; y = o.e.y + (sa * r - ca * lat) * M; z = ctx.suelo(x, y) + 0.35 * M;
            head = c.dir > 0 ? c.al + Math.PI : c.al;
          } else {
            const dk = c.dk, sd = c.dir > 0 ? -dk.Ld / 2 - dk.Ls + s : dk.Ld / 2 + dk.Ls - s, P = dk.P(sd);
            const cp = Math.cos(dk.phi), sp = Math.sin(dk.phi), lat = c.off;  // a la derecha de su sentido
            x = P[0] + sp * lat * M; y = P[1] - cp * lat * M;
            const Yd = (q) => (Math.abs(q) <= dk.Ld / 2 ? dk.Y(q) : dk.g(q) + 0.35 * M);
            z = Yd(sd); const dz = (Yd(sd + 1) - Yd(sd - 1)) / (2 * M);
            head = c.dir > 0 ? dk.phi : dk.phi + Math.PI; pitch = Math.atan(dz * c.dir);
          }
          const kk = k * fin;
          c.m.visible = kk > 0.01; c.m.position.set(x, z, -y); c.m.rotation.set(0, head, pitch); c.m.scale.setScalar(Math.max(1e-3, kk));
          if (FA) {
            const cx = Math.cos(head), sx = Math.sin(head);
            for (const j of [0, 1]) { const lz = j ? 0.6 : -0.6, fx = x + (2.35 * cx + lz * sx) * M, fy = y + (2.35 * sx - lz * cx) * M;
              FA.position.setXYZ(iF * 2 + j, fx, z + 0.6 * M, -fy); FA.aK.setX(iF * 2 + j, kk > 0.3 ? 0.8 : 0); }
          }
          iF++;
        }
      }
      if (FA) { FA.position.needsUpdate = true; FA.aK.needsUpdate = true; }
      if (st.mHumo) st.mHumo.material.uniforms.uOn.value = humoOn;
      // la gente
      if (st.flP) {
        st.pers.forEach((q, i) => {
          const o = q.ob, u = (t - o.tU(0)) / o.D;
          if (q.tipo === "paseo") {
            const k = 1 - clamp((t - q.sale) / 0.6, 0, 1);
            if (k <= 0) { st.flP.poner(i, 0, 0, 1, 0, 0, 0, 0); return; }
            const span = q.span, m = (((q.vel * t + q.ph) % (4 * span)) + 4 * span) % (4 * span), ida = m < 2 * span, s = -span + (ida ? m : 4 * span - m);
            const uu = q.hor ? s : q.c + q.lado, vv = q.hor ? q.c + q.lado : s, du = q.hor ? (ida ? 1 : -1) : 0, dv = q.hor ? 0 : (ida ? 1 : -1);
            const cr = Math.cos(o.e.rumbo * Math.PI / 180), sr = Math.sin(o.e.rumbo * Math.PI / 180);
            const x = o.e.x + (uu * cr - vv * sr) * M, y = o.e.y + (uu * sr + vv * cr) * M;
            st.flP.poner(i, x, y, du * cr - dv * sr, du * sr + dv * cr, k, 0, q.vel);
          } else {
            const k = ease(clamp((u - F.obreros[0]) / 0.04, 0, 1)) * (1 - ease(clamp((u - F.obreros[1]) / 0.04, 0, 1)));
            if (k <= 0) { st.flP.poner(i, 0, 0, 1, 0, 0, 0, 0); return; }
            let x = q.x, y = q.y, dx = Math.cos(q.a), dy = Math.sin(q.a);
            if (q.camina) { const w = Math.sin((t + q.ph) * q.vel * 0.35) * 5; x += dx * w * M; y += dy * w * M; const c = Math.cos((t + q.ph) * q.vel * 0.35); if (c < 0) { dx = -dx; dy = -dy; } }
            st.flP.poner(i, x, y, dx, dy, k, 0, q.camina ? q.vel : 0);
          }
        });
        st.flP.listo();
      }
      if (st.flV) {
        st.volteos.forEach((q, i) => {
          const o = q.ob, u = (t - o.tU(0)) / o.D;
          if (o.hD > 0 && t < q.tA) {                        // con `hundir_desde_s`: los volteos LLEGAN desde afuera mientras lo viejo sigue en pie
            const k = o.e.t <= 0.1 ? 1 : ease(clamp((t - o.e.t) / 0.5, 0, 1)), w = ease(clamp((t - o.e.t) / Math.max(0.5, q.tA - o.e.t), 0, 1));
            if (k <= 0) { st.flV.poner(i, 0, 0, 1, 0, 0, 0, 0); return; }
            const r = 1.5 * o.R + (q.r - 1.5 * o.R) * w, ca = Math.cos(q.ph), sa = Math.sin(q.ph);
            st.flV.poner(i, o.e.x + ca * r * M, o.e.y + sa * r * M, -ca, -sa, k, 0, w < 1 ? q.v : 0);
            return;
          }
          const k = o.hD > 0 ? 1 - ease(clamp((u - F.volteos[1]) / 0.05, 0, 1)) : ease(clamp((u - F.volteos[0]) / 0.05, 0, 1)) * (1 - ease(clamp((u - F.volteos[1]) / 0.05, 0, 1)));
          if (k <= 0) { st.flV.poner(i, 0, 0, 1, 0, 0, 0, 0); return; }
          const a = q.ph + q.sg * q.v * (o.hD > 0 ? t - q.tA : t) / q.r, x = o.e.x + Math.cos(a) * q.r * M, y = o.e.y + Math.sin(a) * q.r * M;
          st.flV.poner(i, x, y, -Math.sin(a) * q.sg, Math.cos(a) * q.sg, k, 0, q.v);
        });
        st.flV.listo();
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
