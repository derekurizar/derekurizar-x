// Evento «poblar» (ficha: poblar.json; reglas: scripts/maqueta_tipos/poblar.py): la orilla de una `orillalago` se llena
// de casas de verano y hoteles, lote a lote, de la fracción `de` a la `a` de los lotes de una franja paralela al agua.
// Ilustrativo: no cuenta edificios. Cada lote BROTA en su turno: primero se despeja el solar (el césped y el andén se
// abren desde el centro con un poco de polvo), luego sube la casa o el hotel desde el suelo, rebota apenas y se asienta
// con su sombra de contacto; al final sale alguien a caminar frente al lote. Genéricos y bajos: casa de una planta con
// corredor, tapia baja y árboles; hotel de dos plantas con balcón corrido, terraza y sombrillas. `epoca` antes: techos
// de teja a dos aguas o a cuatro; hoy: losas planas con pretil, vidrio y algún techo de teja. De noche se encienden las
// ventanas y la lámpara del corredor. Seek puro: cada lote tiene su segundo de brote (de los eventos, al armar) y todo
// lo que se ve sale de t. Las casas y hoteles no descargan nada ni tienen muelle propio: no se dibuja ningún tubo.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
  const crecida = (dur) => Math.min(1.6, Math.max(0.5, 0.45 * dur));   // lo que tarda un lote en brotar (s)

  MAQ.EVENTOS.poblar = {
    orden: 44,
    armar(ctx, lista) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1;
      const alt = (x, y) => (ctx.altura ? ctx.altura(x, y) : ctx.suelo(x, y));
      const oct = new THREE.OctahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
      // ---- los tonos (todos del estilo)
      const cMuro = tonos.muro.clone().lerp(tonos.arena, 0.12);
      const cMuroHoy = tonos.muro.clone().lerp(lin(COL.costa), 0.22);
      const cTeja = tonos.mal.clone().lerp(lin(COL.tierra_media), 0.5).multiplyScalar(oscuro ? 0.9 : 0.85);
      const cLosa = tonos.pavimento.clone().lerp(tonos.muro, 0.4);
      const cZocalo = tonos.muro.clone().lerp(tonos.asfalto, 0.45).multiplyScalar(0.85);
      const cHueco = tonos.suelo.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.22);
      const cVidrio = tonos.agua.clone().lerp(cHueco, 0.45);
      const cMadera = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.55) : tonos.linea.clone().lerp(tonos.techo, 0.45);
      const cCesped = tonos.verde.clone().lerp(tonos.campo, 0.5).multiplyScalar(oscuro ? 1.15 : 1.0);
      const cAnden = tonos.pavimento.clone().lerp(tonos.arena, 0.5);
      const cCopa = tonos.verde.clone().lerp(tonos.campo2, 0.12).multiplyScalar(oscuro ? 1.5 : 0.9);
      const cTronco = oscuro ? tonos.linea.clone().lerp(tonos.muro, 0.6) : tonos.linea.clone().lerp(tonos.techo, 0.4);
      const cTela = tonos.secundario ? tonos.secundario.clone().lerp(tonos.muro, 0.35) : tonos.arena.clone();
      const cLuz = lin(COL.luces), cPolvo = tonos.arena.clone().lerp(tonos.muro, 0.3), cSombra = tonos.asfalto.clone().multiplyScalar(0.12);

      // ---- caras con la luz horneada (4 puntos; ref = hacia dónde es «afuera»; sin ref, hacia arriba)
      const cara = (acc, P, col, ref) => {
        const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
        let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
        const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
        if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx, ny, nz), q = acc.pos.length / 3;
        for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
        acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
      };
      const tubo = (acc, A, B, r, seg, col) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2));
        }
      };
      const cono = (acc, P, r, h, seg, col) => {
        const T = [P[0], P[1] + h, P[2]];
        for (let i = 0; i < seg; i++) {
          const a0 = TAU * i / seg, a1 = TAU * (i + 1) / seg, am = (a0 + a1) / 2;
          cara(acc, [[P[0] + r * Math.cos(a0), P[1], P[2] + r * Math.sin(a0)], [P[0] + r * Math.cos(a1), P[1], P[2] + r * Math.sin(a1)], T, T], col, [Math.cos(am), r / h, Math.sin(am)]);
        }
      };
      const gema = (acc, P, rx, ry, rz, rot, col) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), c = new THREE.Color();
        for (let i = 0; i < oct.length; i += 9) {
          const v = [];
          for (let j = 0; j < 9; j += 3) { const x = oct[i + j] * rx, y = oct[i + j + 1] * ry, z = oct[i + j + 2] * rz; v.push([P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr]); }
          const e1 = [v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]], e2 = [v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; c.copy(col).multiplyScalar(sombra(nx / n, Math.abs(ny / n), nz / n));
          const q = acc.pos.length / 3;
          for (const w of v) { acc.pos.push(w[0], w[1], w[2]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2);
        }
      };

      // ---- los lotes de cada orilla (los eventos de una misma pieza comparten los del primero) y su segundo de brote
      const porPieza = new Map();
      for (const e of [...lista].sort((a, b) => a.t - b.t)) {
        if (!porPieza.has(e.pieza)) porPieza.set(e.pieza, { e0: e, evs: [] });
        porPieza.get(e.pieza).evs.push(e);
      }
      const orillas = [];
      const matCuerpo = malla.material({ desfase: 1 }), matSuelo = malla.material({ desfase: 3 }), matFoc = malla.material({ desfase: 2 });
      matFoc.uniforms.uBrillo.value = noche ? 1.7 : 1;
      const matSom = new THREE.ShaderMaterial({ uniforms: { cS: { value: cSombra }, uA: { value: ES.dia ? 0.42 : 0.5 } }, transparent: true, depthWrite: false,
        polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4,
        vertexShader: "attribute float aR; varying float vR; void main(){ vR = aR; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        fragmentShader: SRGB + "uniform vec3 cS; uniform float uA; varying float vR; void main(){ float a = uA * (1.0 - smoothstep(0.35, 1.0, vR)); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cS), a); }" });
      const uT = { value: 0 }, uPx = { value: 1 };
      const polvo = [], lamparas = [];

      for (const [pid, { e0, evs }] of porPieza) {
        const M = e0.k, n = [e0.nx, e0.ny], tg = [-e0.ny, e0.nx], N = e0.n;
        const sem = e0.semilla * 7919, hz = (i, k) => hash(i + sem, k);
        const dirS = [tg[0], 0, -tg[1]], dirD = [n[0], 0, -n[1]], UP = [0, 1, 0], neg = (d) => [-d[0], -d[1], -d[2]];
        // el brote de cada lote (rango → t0): lo que ya estaba (rango < de del primero) desde siempre
        const t0 = new Array(N).fill(Infinity);
        evs.forEach((e, ie) => {
          const n0 = Math.round(e.de * N), n1 = Math.round(e.a * N), G = crecida(e.dur);
          if (ie === 0) for (let r = 0; r < n0; r++) t0[r] = -1e9;
          else for (let r = 0; r < n0; r++) if (t0[r] === Infinity) t0[r] = e.t;
          for (let r = n0; r < n1; r++) if (t0[r] === Infinity) t0[r] = e.t + Math.max(0, e.dur - G) * (n1 - n0 > 1 ? (r - n0) / (n1 - n0 - 1) : 0);
        });
        const G = crecida(e0.dur);
        const hoy = e0.epoca !== "antes";
        const lotes = e0.lotes.map((L) => {
          const k = L.k, w = L.w / M, d = L.d / M, hb = alt(L.x, L.y);
          // punto local (s a lo largo, q hacia tierra, h arriba; metros) → relativo a la base, en three
          const F = (s, q, h) => [(tg[0] * s + n[0] * q) * M, h * M, -(tg[1] * s + n[1] * q) * M];
          const Wd = (s, q) => [L.x + (tg[0] * s + n[0] * q) * M, L.y + (tg[1] * s + n[1] * q) * M];
          const sueloRel = (s, q, lev) => { const [x, y] = Wd(s, q); return [(tg[0] * s + n[0] * q) * M, alt(x, y) - hb + lev * M, -(tg[1] * s + n[1] * q) * M]; };
          const cuerpo = malla.nueva(), suelo = malla.nueva(), focos = malla.nueva();
          const caja = (acc, s0, s1, q0, q1, h0, h1, col, sinTapa) => {
            if (!sinTapa) cara(acc, [F(s0, q0, h1), F(s1, q0, h1), F(s1, q1, h1), F(s0, q1, h1)], col, UP);
            cara(acc, [F(s1, q0, h0), F(s1, q1, h0), F(s1, q1, h1), F(s1, q0, h1)], col, dirS);
            cara(acc, [F(s0, q0, h0), F(s0, q1, h0), F(s0, q1, h1), F(s0, q0, h1)], col, neg(dirS));
            cara(acc, [F(s0, q1, h0), F(s1, q1, h0), F(s1, q1, h1), F(s0, q1, h1)], col, dirD);
            cara(acc, [F(s0, q0, h0), F(s1, q0, h0), F(s1, q0, h1), F(s0, q0, h1)], col, neg(dirD));
          };
          // un vano sobre la cara q = qf (lado −1: el frente, hacia el agua) o sobre s = sf (eje "s")
          const vano = (qf, lado, s0, s1, h0, h1, prendido, vidrio) => {
            const q = qf + lado * 0.05, ref = lado > 0 ? dirD : neg(dirD);
            cara(prendido ? focos : cuerpo, [F(s0, q, h0), F(s1, q, h0), F(s1, q, h1), F(s0, q, h1)], prendido ? cLuz.clone().multiplyScalar(0.75 + 0.25 * hz(k * 13 + Math.round(s0 * 7), 70)) : (vidrio ? cVidrio : cHueco), ref);
            const qm = qf + lado * 0.09;                                          // el marco (dintel y repisa)
            caja(cuerpo, s0 - 0.12, s1 + 0.12, Math.min(qf, qm), Math.max(qf, qm), h1, h1 + 0.12, cZocalo.clone().lerp(cMuro, 0.5));
            if (h0 > 0.5) caja(cuerpo, s0 - 0.1, s1 + 0.1, Math.min(qf, qf + lado * 0.16), Math.max(qf, qf + lado * 0.16), h0 - 0.1, h0, cZocalo.clone().lerp(cMuro, 0.4));
          };
          const techo2 = (s0, s1, q0, q1, hw, ov, col, colMuro) => {        // a dos aguas, cumbrera a lo largo de s
            const qm = (q0 + q1) / 2, hr = hw + 0.45 * (q1 - q0) / 2 + 0.6;
            for (const [qa, qb] of [[q0 - ov, qm], [q1 + ov, qm]]) {
              const caida = (qa - qm) / ((q1 - q0) / 2), ha = hr - (hr - hw) * Math.abs(caida);
              cara(cuerpo, [F(s0 - ov, qa, ha), F(s1 + ov, qa, ha), F(s1 + ov, qb, hr), F(s0 - ov, qb, hr)], col, null);
              cara(cuerpo, [F(s0 - ov, qa, ha - 0.16), F(s1 + ov, qa, ha - 0.16), F(s1 + ov, qa, ha), F(s0 - ov, qa, ha)], col.clone().multiplyScalar(0.7), qa < qm ? neg(dirD) : dirD);
              for (let j = 1; j < 6; j++) {                                      // las hiladas de teja
                const f = j / 6, qq = qa + (qb - qa) * f, hh = ha + (hr - ha) * f + 0.03;
                cara(cuerpo, [F(s0 - ov, qq, hh), F(s1 + ov, qq, hh), F(s1 + ov, qq + (qb - qa) * 0.025, hh + 0.05), F(s0 - ov, qq + (qb - qa) * 0.025, hh + 0.05)], col.clone().multiplyScalar(0.8), null);
              }
            }
            for (const ss of [s0, s1]) cara(cuerpo, [F(ss, q0, hw), F(ss, q1, hw), F(ss, qm, hr - 0.05), F(ss, qm, hr - 0.05)], colMuro, ss === s0 ? neg(dirS) : dirS);
            caja(cuerpo, s0 - ov, s1 + ov, qm - 0.12, qm + 0.12, hr - 0.05, hr + 0.12, col.clone().multiplyScalar(0.75));
            return hr;
          };
          const techo4 = (s0, s1, q0, q1, hw, ov, col) => {                  // a cuatro aguas
            const qm = (q0 + q1) / 2, hr = hw + 0.4 * (q1 - q0) / 2 + 0.5, a = (q1 - q0) / 2 + ov;
            const S0 = s0 - ov, S1 = s1 + ov, Q0 = q0 - ov, Q1 = q1 + ov, r0 = Math.min(S0 + a, (S0 + S1) / 2), r1 = Math.max(S1 - a, (S0 + S1) / 2);
            const he = hw - 0.12;
            cara(cuerpo, [F(S0, Q0, he), F(S1, Q0, he), F(r1, qm, hr), F(r0, qm, hr)], col, null);
            cara(cuerpo, [F(S1, Q1, he), F(S0, Q1, he), F(r0, qm, hr), F(r1, qm, hr)], col, null);
            cara(cuerpo, [F(S0, Q1, he), F(S0, Q0, he), F(r0, qm, hr), F(r0, qm, hr)], col.clone().multiplyScalar(0.94), null);
            cara(cuerpo, [F(S1, Q0, he), F(S1, Q1, he), F(r1, qm, hr), F(r1, qm, hr)], col.clone().multiplyScalar(0.94), null);
            for (const [qa, rf] of [[Q0, neg(dirD)], [Q1, dirD]]) cara(cuerpo, [F(S0, qa, he - 0.15), F(S1, qa, he - 0.15), F(S1, qa, he), F(S0, qa, he)], col.clone().multiplyScalar(0.7), rf);
            return hr;
          };
          const losa = (s0, s1, q0, q1, hw, col) => {                          // losa plana con su pretil
            caja(cuerpo, s0 - 0.3, s1 + 0.3, q0 - 0.3, q1 + 0.3, hw, hw + 0.25, col);
            const p = 0.18, hp = hw + 0.25 + 0.55;
            caja(cuerpo, s0 - 0.3, s1 + 0.3, q0 - 0.3, q0 - 0.3 + p, hw + 0.25, hp, col.clone().multiplyScalar(0.95));
            caja(cuerpo, s0 - 0.3, s1 + 0.3, q1 + 0.3 - p, q1 + 0.3, hw + 0.25, hp, col.clone().multiplyScalar(0.95));
            caja(cuerpo, s0 - 0.3, s0 - 0.3 + p, q0 - 0.3, q1 + 0.3, hw + 0.25, hp, col.clone().multiplyScalar(0.95));
            caja(cuerpo, s1 + 0.3 - p, s1 + 0.3, q0 - 0.3, q1 + 0.3, hw + 0.25, hp, col.clone().multiplyScalar(0.95));
            return hp;
          };
          const arbol = (s, q, al, kk) => {
            const P = sueloRel(s, q, -0.2);
            tubo(cuerpo, P, [P[0], P[1] + al * 0.55 * M, P[2]], 0.05 * al * M, 6, cTronco);
            for (let j = 0; j < 3; j++) { const a = TAU * hz(kk, 30 + j), rr = j ? al * 0.16 : 0;
              gema(cuerpo, [P[0] + Math.cos(a) * rr * M, P[1] + al * (0.74 - 0.07 * j) * M, P[2] + Math.sin(a) * rr * M], al * 0.3 * M, al * 0.22 * M, al * 0.28 * M, a,
                cCopa.clone().multiplyScalar(0.85 + 0.25 * hz(kk, 33 + j))); }
          };
          // ---- el solar: césped, el andén al agua, la tapia baja a los lados y atrás (el frente al agua, abierto)
          const ws = w / 2 - 0.6, dq = d / 2;
          const NS = 5;
          const grid = (s0, s1, q0, q1, lev, col, acc) => {
            for (let i = 0; i < NS; i++) for (let j = 0; j < NS; j++) {
              const a0 = s0 + (s1 - s0) * i / NS, a1 = s0 + (s1 - s0) * (i + 1) / NS, b0 = q0 + (q1 - q0) * j / NS, b1 = q0 + (q1 - q0) * (j + 1) / NS;
              cara(acc, [sueloRel(a0, b0, lev), sueloRel(a1, b0, lev), sueloRel(a1, b1, lev), sueloRel(a0, b1, lev)], col.clone().multiplyScalar(0.95 + 0.08 * hz(k * 50 + i * 7 + j, 40)), null);
            }
          };
          grid(-ws, ws, -dq, dq, 0.08, cCesped.clone().multiplyScalar(0.92 + 0.12 * hz(k, 1)), suelo);
          const hotel = !!L.hotel, var_ = hz(k, 2);
          const muroC = (hoy && hz(k, 3) < 0.55 ? cMuroHoy : cMuro).clone().multiplyScalar(0.92 + 0.14 * hz(k, 4));
          // el edificio: huella (s: largo, q: fondo) y su posición en el solar (hacia atrás, el frente mira al agua)
          const Lh = hotel ? Math.min(ws - 1.2, 7 + 1.5 * var_) : Math.min(ws - 2.0, 4 + 1.6 * var_);
          const Wh = hotel ? 4.2 + 0.6 * hz(k, 5) : 3.2 + 0.8 * hz(k, 5);
          const qc = Math.min(dq - Wh - 1.6, 1.5 + 2.5 * hz(k, 6)), sc = (hz(k, 7) - 0.5) * Math.max(0, ws - Lh - 1.5);
          const s0 = sc - Lh, s1 = sc + Lh, q0 = qc - Wh, q1 = qc + Wh;
          // andén del frente al agua y la terraza
          const qT = q0 - (hotel ? 4.2 : 3.0);
          grid(s0 + 0.6, s1 - 0.6, qT, q0, 0.12, cLosa, suelo);
          for (let j = 0; j < 4; j++) { const qa = -dq + (qT + dq) * j / 4, qb = -dq + (qT + dq) * (j + 1) / 4;
            cara(suelo, [sueloRel(sc - 0.8, qa, 0.13), sueloRel(sc + 0.8, qa, 0.13), sueloRel(sc + 0.8, qb, 0.13), sueloRel(sc - 0.8, qb, 0.13)], cAnden, null); }
          // la tapia: a los lados y atrás, con remate y pilares; hacia el camino, el portón
          const hT = 1.1 + 0.3 * hz(k, 8), cT = muroC.clone().multiplyScalar(0.88);
          const tapia = (sa, sb, qa, qb) => {
            const nseg = Math.max(1, Math.round(Math.hypot(sb - sa, qb - qa) / 3));
            for (let j = 0; j < nseg; j++) {
              const f0 = j / nseg, f1 = (j + 1) / nseg, A = [sa + (sb - sa) * f0, qa + (qb - qa) * f0], B = [sa + (sb - sa) * f1, qa + (qb - qa) * f1];
              const [x0, y0] = Wd(A[0], A[1]), [x1, y1] = Wd(B[0], B[1]), h0 = (alt(x0, y0) - hb) / M, h1 = (alt(x1, y1) - hb) / M, hh = Math.min(h0, h1);
              caja(cuerpo, Math.min(A[0], B[0]) - 0.12, Math.max(A[0], B[0]) + 0.12, Math.min(A[1], B[1]) - 0.12, Math.max(A[1], B[1]) + 0.12, hh - 0.4, hh + hT, cT);
              caja(cuerpo, Math.min(A[0], B[0]) - 0.18, Math.max(A[0], B[0]) + 0.18, Math.min(A[1], B[1]) - 0.18, Math.max(A[1], B[1]) + 0.18, hh + hT, hh + hT + 0.1, cZocalo);
              if (j % 2 === 0) caja(cuerpo, A[0] - 0.22, A[0] + 0.22, A[1] - 0.22, A[1] + 0.22, hh - 0.4, hh + hT + 0.3, cT.clone().multiplyScalar(0.92));
            }
          };
          tapia(-ws, -ws, -dq + 2, dq); tapia(ws, ws, -dq + 2, dq);
          tapia(-ws, sc - 1.6, dq, dq); tapia(sc + 1.6, ws, dq, dq);
          for (const ss of [sc - 1.6, sc + 1.6]) caja(cuerpo, ss - 0.28, ss + 0.28, dq - 0.28, dq + 0.28, -0.4, hT + 0.55, cZocalo);
          // ---- el cuerpo
          const luzDe = (j) => noche && hz(k * 31 + j, 60) < 0.72;
          let hTop;
          if (!hotel) {
            const Hw = 3.0 + 0.3 * hz(k, 9);
            caja(cuerpo, s0 - 0.12, s1 + 0.12, q0 - 0.12, q1 + 0.12, -0.6, 0.45, cZocalo);
            caja(cuerpo, s0, s1, q0, q1, 0.45, Hw, muroC, true);
            const teja = !hoy || hz(k, 10) < 0.4;
            hTop = teja ? (hz(k, 11) < 0.5 ? techo2(s0, s1, q0, q1, Hw, 0.7, cTeja.clone().multiplyScalar(0.9 + 0.15 * hz(k, 12)), muroC) : techo4(s0, s1, q0, q1, Hw, 0.7, cTeja.clone().multiplyScalar(0.9 + 0.15 * hz(k, 12))))
              : losa(s0, s1, q0, q1, Hw, cLosa.clone().lerp(muroC, 0.4));
            // frente: puerta al centro y ventanas a los lados; atrás y a los lados, ventanas chicas
            vano(q0, -1, sc - 0.55, sc + 0.55, 0.45, 2.35, noche && hz(k, 13) < 0.35, false);
            const nv = Math.max(1, Math.floor((Lh - 1.2) / 1.9));
            for (let j = 1; j <= nv; j++) for (const sg of [-1, 1]) {
              const sv = sc + sg * (0.6 + 1.9 * j - 0.7);
              if (Math.abs(sv - sc) + 0.6 > Lh - 0.3) continue;
              vano(q0, -1, sv - 0.55, sv + 0.55, 1.05, 2.25, luzDe(j * 2 + (sg > 0 ? 1 : 0)), hoy);
            }
            vano(q1, 1, sc - 0.4, sc + 0.4, 1.3, 2.1, luzDe(9), false);
            // corredor: losa, horcones y alero hacia el agua
            const qE = q0 - 2.4, yE = Hw - 0.35;
            caja(cuerpo, s0, s1, qE, q0, 0.0, 0.3, cLosa.clone().multiplyScalar(0.95));
            for (const ss of [s0 + 0.25, sc - Lh / 2, sc + Lh / 2, s1 - 0.25]) tubo(cuerpo, F(ss, qE + 0.25, 0.3), F(ss, qE + 0.25, yE), 0.09 * M, 8, cMadera);
            caja(cuerpo, s0 - 0.2, s1 + 0.2, qE - 0.3, q0, yE, yE + 0.18, (hoy ? cLosa : cTeja).clone().multiplyScalar(0.92));
            if (!hoy) caja(cuerpo, s0 + 0.2, s1 - 0.2, qE + 0.1, qE + 0.35, yE - 0.3, yE, cMadera);   // la viga
            if (noche) lamparas.push({ P: F(sc, qE + 0.6, yE - 0.4), pid, r: L.rango, base: [L.x, L.y, hb] });
            if (hz(k, 14) < 0.5) tubo(cuerpo, F(s1 - 0.8, q1 - 0.8, Hw - 0.3), F(s1 - 0.8, q1 - 0.8, hTop + 0.6), 0.22 * M, 10, cZocalo);   // la chimenea
          } else {
            const H1 = 3.1, H2 = 6.2;
            caja(cuerpo, s0 - 0.15, s1 + 0.15, q0 - 0.15, q1 + 0.15, -0.6, 0.5, cZocalo);
            caja(cuerpo, s0, s1, q0, q1, 0.5, H2, muroC, true);
            caja(cuerpo, s0 - 0.1, s1 + 0.1, q0 - 0.1, q1 + 0.1, H1 - 0.1, H1 + 0.15, cZocalo.clone().lerp(muroC, 0.5));   // la cornisa entre plantas
            const teja = !hoy || hz(k, 10) < 0.3;
            hTop = teja ? techo4(s0, s1, q0, q1, H2, 0.9, cTeja.clone().multiplyScalar(0.9 + 0.15 * hz(k, 12))) : losa(s0, s1, q0, q1, H2, cLosa.clone().lerp(muroC, 0.3));
            // el balcón corrido de la segunda planta, con su baranda
            const qB = q0 - 1.5;
            caja(cuerpo, s0 + 0.3, s1 - 0.3, qB, q0, H1 + 0.15, H1 + 0.35, cLosa);
            caja(cuerpo, s0 + 0.3, s1 - 0.3, qB, qB + 0.08, H1 + 1.25, H1 + 1.35, hoy ? cZocalo : cMadera);
            const nb = Math.max(4, Math.round((s1 - s0) / 1.1));
            for (let j = 0; j <= nb; j++) { const ss = s0 + 0.35 + (s1 - s0 - 0.7) * j / nb; caja(cuerpo, ss - 0.04, ss + 0.04, qB, qB + 0.08, H1 + 0.35, H1 + 1.25, hoy ? cZocalo : cMadera); }
            for (const ss of [s0 + 0.4, (s0 + s1) / 2, s1 - 0.4]) tubo(cuerpo, F(ss, qB + 0.2, 0.3), F(ss, qB + 0.2, H1 + 0.15), 0.12 * M, 10, hoy ? cZocalo : cMadera);
            // las ventanas: un ritmo por planta en el frente y atrás; la puerta al centro abajo
            const nv = Math.max(3, Math.floor((s1 - s0) / 2.4));
            for (let p = 0; p < 2; p++) for (let j = 0; j < nv; j++) {
              const sv = s0 + (s1 - s0) * (j + 0.5) / nv, h0 = p ? H1 + 0.35 : 0.5, h1 = p ? H1 + 2.4 : 2.6, puerta = !p && Math.abs(sv - (s0 + s1) / 2) < (s1 - s0) / nv * 0.5;
              vano(q0, -1, sv - (p ? 0.65 : 0.6), sv + (p ? 0.65 : 0.6), puerta ? 0.5 : (p ? h0 : 1.0), puerta ? 2.5 : h1, luzDe(p * 20 + j), hoy && !puerta);
              vano(q1, 1, sv - 0.45, sv + 0.45, h0 + 0.6, h1 - 0.2, luzDe(p * 20 + j + 50), false);
            }
            // la terraza del frente con sombrillas y mesas
            const ns = Math.max(1, Math.min(3, Math.floor((s1 - s0) / 5)));
            for (let j = 0; j < ns; j++) {
              const ss = s0 + (s1 - s0) * (j + 0.5) / ns, qq = (qT + q0) / 2 - 0.3, B = F(ss, qq, 0.12);
              tubo(cuerpo, B, F(ss, qq, 2.3), 0.04 * M, 6, cMadera);
              cono(cuerpo, F(ss, qq, 2.0), 1.4 * M, 0.55 * M, 12, cTela.clone().multiplyScalar(0.92 + 0.15 * hz(k * 7 + j, 80)));
              tubo(cuerpo, F(ss, qq, 0.12), F(ss, qq, 0.8), 0.45 * M, 12, cMadera.clone().multiplyScalar(1.1));
            }
            if (noche) lamparas.push({ P: F((s0 + s1) / 2, q0 - 1.2, H1 - 0.4), pid, r: L.rango, base: [L.x, L.y, hb] });
          }
          // los árboles del jardín (atrás y a los lados del edificio)
          const nArb = hotel ? 2 : 1 + (hz(k, 15) < 0.6 ? 1 : 0);
          for (let j = 0; j < nArb; j++) {
            const lado = (j % 2 ? 1 : -1) * (hz(k, 16) < 0.5 ? 1 : -1), sA = clamp(sc + lado * (Lh + 2.2 + 1.2 * hz(k, 17 + j)), -ws + 1.3, ws - 1.3);
            const qA = clamp(qc + (hz(k, 19 + j) - 0.3) * Wh * 2, -dq + 4, dq - 1.5);
            if (Math.abs(sA - sc) < Lh + 1.2) continue;
            arbol(sA, qA, 6 + 3 * hz(k, 21 + j), k * 11 + j);
          }
          // ---- la sombra de contacto (un disco suave bajo el edificio)
          const gS = new THREE.BufferGeometry(), segS = 24, posS = [0, 0.05 * M, 0], aR = [0], idS = [];
          const ra = Lh + 1.6, rb = Wh + 1.8, sh = 0.3;
          for (let i = 0; i <= segS; i++) { const a = TAU * i / segS, p = F(sc + Math.cos(a) * ra + sh, qc + Math.sin(a) * rb + sh, 0.06); posS.push(p[0], p[1], p[2]); aR.push(1); if (i) idS.push(0, i, i + 1); }
          const cS = F(sc + sh, qc + sh, 0.06); posS[0] = cS[0]; posS[1] = cS[1]; posS[2] = cS[2];
          gS.setAttribute("position", new THREE.BufferAttribute(new Float32Array(posS), 3)); gS.setAttribute("aR", new THREE.BufferAttribute(new Float32Array(aR), 1)); gS.setIndex(idS);
          // ---- las mallas del lote, con su origen en la base (para crecer desde el suelo)
          const base = new THREE.Vector3(L.x, hb, -L.y);
          const poner = (acc, mat, orden) => { if (!acc.idx.length) return null; const m = malla.poner(acc, mat, orden); m.position.copy(base); m.visible = false; return m; };
          const mS = new THREE.Mesh(gS, matSom); mS.position.copy(base); mS.renderOrder = 2; mS.frustumCulled = false; mS.visible = false; scene.add(mS);
          // el polvo: puntos que salen del pie del edificio cuando brota
          const tb = t0[L.rango];
          if (Number.isFinite(tb) && tb > -1e8) for (let j = 0; j < 14; j++) {
            const a = TAU * j / 14 + hz(k * 3 + j, 90), p = F(sc + Math.cos(a) * (Lh + 0.5), qc + Math.sin(a) * (Wh + 0.5), 0.3);
            polvo.push({ P: [p[0] + base.x, p[1] + base.y, p[2] + base.z], d: [Math.cos(a), Math.sin(a)], t0: tb, f: hz(k * 5 + j, 91) });
          }
          return { L, tb, sc, qc, Lh, Wh, qT, dq, ws, F, Wd, hotel, sale: hz(k, 99) < (hotel ? 0.9 : 0.55),
            suelo: poner(suelo, matSuelo, 2), cuerpo: poner(cuerpo, matCuerpo, 3), focos: poner(focos, matFoc, 4), sombra: mS };
        });
        orillas.push({ pid, G, lotes, M, hz });
      }
      // ---- el polvo y las lámparas (shaders con uT: seek puro)
      const puntos = (lst, vs, fs, uni, orden) => {
        if (!lst.length) return null;
        const g = new THREE.BufferGeometry(), pos = new Float32Array(lst.length * 3), a1 = new Float32Array(lst.length * 4);
        lst.forEach((p, i) => { pos.set(p.P, i * 3); a1.set([p.t0, p.f, p.d ? p.d[0] : 0, p.d ? p.d[1] : 0], i * 4); });
        g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aD", new THREE.BufferAttribute(a1, 4));
        const mat = new THREE.ShaderMaterial({ uniforms: { uT, uPx, ...uni }, transparent: true, depthWrite: false, vertexShader: vs, fragmentShader: fs,
          blending: orden === 9 ? THREE.AdditiveBlending : THREE.NormalBlending });
        const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m;
      };
      const M0 = orillas.length ? orillas[0].M : 1, G0 = orillas.length ? orillas[0].G : 1;
      // el polvo: cada partícula se abre y sube en 1.8 s desde el brote de su lote (dirección local en three: tg/n ya horneados en P)
      puntos(polvo, "uniform float uT, uPx, uM, uG; attribute vec4 aD; varying float vA; void main(){ float a = (uT - aD.x - 0.15 * uG) / 1.8; vec3 p = position; " +
        "float v = clamp(a, 0.0, 1.0); p.y += (0.4 + 2.6 * v) * uM * (0.7 + 0.6 * aD.y); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; " +
        "gl_PointSize = (a > 0.0 && a < 1.0) ? clamp((1.6 + 4.0 * v) * uM * uPx / max(1e-3, -mv.z), 1.0, 70.0) : 0.0; vA = (a > 0.0 && a < 1.0) ? (1.0 - v) * smoothstep(0.0, 0.12, v) : 0.0; }",
        SRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = uK * vA * exp(-r * r * 2.4); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }",
        { uM: { value: M0 }, uG: { value: G0 }, cA: { value: cPolvo }, uK: { value: noche ? 0.25 : 0.55 } }, 8);
      // las lámparas del corredor y del balcón: se encienden cuando el lote termina de brotar
      const tLamp = lamparas.map((l) => { const o = orillas.find((q) => q.pid === l.pid), lo = o && o.lotes.find((q) => q.L.rango === l.r); return lo ? lo.tb + (o.G || 1) : Infinity; });
      puntos(lamparas.map((l, i) => ({ P: [l.P[0] + l.base[0], l.P[1] + l.base[2], l.P[2] - l.base[1]], t0: tLamp[i], f: hash(i, 7) })),
        "uniform float uT, uPx, uM; attribute vec4 aD; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; " +
        "float on = aD.x < -1e8 ? 1.0 : smoothstep(aD.x - 0.2, aD.x + 0.3, uT); gl_PointSize = on > 0.0 ? clamp(4.0 * uM * uPx / max(1e-3, -mv.z), 2.0, 30.0) : 0.0; vA = on * (0.85 + 0.15 * sin(uT * 5.1 + aD.y * 40.0)); }",
        SRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = 0.6 * vA * exp(-r * r * 4.0); gl_FragColor = vec4(srgb(cA) * a, a); }",
        { uM: { value: M0 }, cA: { value: cLuz.clone() } }, 9);
      // ---- la gente que sale a caminar frente a cada lote ya poblado
      const caminan = [];
      for (const o of orillas) for (const lo of o.lotes) if (lo.sale && (!noche || o.hz(lo.L.k, 98) < 0.5)) caminan.push({ o, lo });
      const flP = caminan.length ? ctx.flota("persona", caminan.length, { tamano: orillas[0].M * (ctx.unidad_m || 1), orden: 6, semilla: (lista[0].semilla * 13) % 991 }) : null;
      return { orillas, matCuerpo, uT, uPx, flP, caminan };
    },
    inicio(t, st) {
      if (!st) return;
      st.uT.value = t;
    },
    aplicar(t, e, ctx, st) {
      // el brote de cada lote ya está fijado al armar (de todos los poblar de su orilla): aquí solo se aviva al resaltar
      if (!st) return;
      const b = ctx.cuadro && ctx.cuadro.brillo ? ctx.cuadro.brillo[e.pieza] : 0;
      st.matCuerpo.uniforms.uBrillo.value = 1 + (b ? 0.3 * ctx.clamp((b - 1) / 0.9, 0, 1.2) : 0);
    },
    en(t, st, ctx) {
      if (!st) return;
      const { clamp, suave } = ctx;
      st.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      const rebote = (x) => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };   // sube, pasa un poco y se asienta
      for (const o of st.orillas) for (const lo of o.lotes) {
        const g = lo.tb < -1e8 ? 1 : clamp((t - lo.tb) / o.G, 0, 1), vivo = lo.tb < -1e8 || t >= lo.tb;
        const kp = suave(0, 0.3, g), kc = clamp(rebote(clamp((g - 0.18) / 0.67, 0, 1)), 0, 1.08), kh = 0.9 + 0.1 * suave(0.2, 0.85, g);
        if (lo.suelo) { lo.suelo.visible = vivo && kp > 0.001; lo.suelo.scale.set(Math.max(1e-3, kp), 1, Math.max(1e-3, kp)); }
        for (const m of [lo.cuerpo, lo.focos]) if (m) { m.visible = vivo && kc > 0.001; m.scale.set(kh, Math.max(1e-3, kc), kh); }
        lo.sombra.visible = vivo && kc > 0.02; lo.sombra.scale.setScalar(Math.max(1e-3, Math.min(1, kc)));
      }
      if (st.flP) {
        st.caminan.forEach(({ o, lo }, i) => {
          const tl = lo.tb < -1e8 ? 99 : t - lo.tb - o.G, k = clamp(tl / 0.5, 0, 1);
          if (k <= 0) { st.flP.poner(i, 0, 0, 1, 0, 0, 0, 0); return; }
          const span = Math.max(2, lo.Lh + 1.5), v = 0.9 + 0.3 * o.hz(lo.L.k, 95), ph = o.hz(lo.L.k, 96) * 2 * span;
          const m = ((v * t + ph) % (2 * span) + 2 * span) % (2 * span), sg = m > span ? -1 : 1, s = lo.sc - span / 2 + (m > span ? 2 * span - m : m);
          const q = lo.qT - 1.2 - 1.5 * o.hz(lo.L.k, 97);
          const [x, y] = lo.Wd(s, q), [x2, y2] = lo.Wd(s + sg, q);
          st.flP.poner(i, x, y, x2 - x, y2 - y, k, 0, v);
        });
        st.flP.listo();
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
