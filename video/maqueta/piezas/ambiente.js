// Pieza «ambiente» (ficha: ambiente.json; reglas: scripts/maqueta_tipos/ambiente.py): viste un mundo de cerca (esquema o
// ciudad) con lo que hay en un lugar así. DÓNDE va cada cosa lo decide el resolver en Python (una vez, por semilla, sin
// pisar calles, caminos, ríos, edificios, el mar ni `evitar`): aquí solo se dibuja. Todo se hornea al armar en mallas de
// caras planas con la luz del estilo (como edificios y cafetal); lo que se mece (copas, palmas, pasto, flores) va en una
// malla aparte cuyos vértices se recalculan de t en cada cuadro (base + vaivén: seek puro). De noche (ctx.ES.noche) las
// farolas, los postes, las ventanas de los ranchos y los semáforos se encienden: bombillo, halo cálido que respira y un
// charco de luz en el suelo (materiales propios que no se tiñen con la hora). Los semáforos ciclan verde → ámbar → rojo
// (función de t). La fuente: el agua de la pila brilla y se mueve y el chorro cae en gotas (posición = función de t).
// Sin texto, sin colores escritos: todo sale de ctx.tonos, ctx.COL y ctx.lin.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  MAQ.PIEZAS.ambiente = {
    orden: 9,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!(ES.noche || ctx.noche), dia = !!ES.dia, M1 = metros(1);
      const c = new THREE.Color();
      // ---- plantillas de triángulos (no indexadas)
      const tri = (g) => g.toNonIndexed().attributes.position.array;
      const ICO = tri(new THREE.IcosahedronGeometry(1, 0)), OCT = tri(new THREE.OctahedronGeometry(1, 0));
      const CONO = tri(new THREE.ConeGeometry(1, 1, 7, 1).translate(0, 0.5, 0)), CONO3 = tri(new THREE.ConeGeometry(1, 1, 3, 1).translate(0, 0.5, 0));
      const CIL = tri(new THREE.CylinderGeometry(1, 1, 1, 7, 1).translate(0, 0.5, 0)), CAJA = tri(new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0));
      const CIL12 = tri(new THREE.CylinderGeometry(1, 1, 1, 14, 1).translate(0, 0.5, 0));
      // ---- colores (de los tonos del estilo)
      const V = (k) => tonos.verde.clone().multiplyScalar(k);
      const kv = noche ? 1.9 : dia ? 0.62 : 0.78;
      const cCopa = [V(kv), V(kv * 0.86).lerp(tonos.techo, 0.12), V(kv * 1.12).lerp(tonos.bien, 0.12)];
      const cPino = V(kv * 0.62).lerp(tonos.linea, 0.12), cArbusto = V(kv * 0.9).lerp(tonos.bien, 0.1);
      const cMatorral = V(kv).lerp(tonos.campo2, 0.45).lerp(tonos.medio, 0.08), cPasto = tonos.campo2.clone().lerp(tonos.medio, 0.22).multiplyScalar(noche ? 1.4 : 1.05);
      const cTronco = tonos.linea.clone().lerp(tonos.muro, 0.55).lerp(tonos.techo, 0.2);
      const cPiedra = tonos.muro.clone().lerp(tonos.linea, noche ? 0.2 : 0.42), cRoca = tonos.muro.clone().lerp(tonos.linea, noche ? 0.3 : 0.55);
      const cMetal = tonos.linea.clone().lerp(tonos.muro, noche ? 0.55 : 0.32), cConcreto = tonos.muro.clone().lerp(tonos.linea, 0.18);
      const cMadera = tonos.techo.clone().lerp(tonos.linea, 0.35).lerp(tonos.muro, 0.3), cAdobe = tonos.muro.clone().lerp(tonos.techo, 0.35), cPaja = tonos.campo2.clone().lerp(tonos.medio, 0.35).lerp(tonos.techo, 0.2);
      const cFlores = [tonos.mal.clone(), tonos.medio.clone(), tonos.muro.clone().lerp(tonos.secundario, 0.2)];
      const cPozo = tonos.calle.clone().multiplyScalar(0.55), cAgua = tonos.agua.clone().lerp(tonos.muro, noche ? 0.15 : 0.25);
      const cBote = [tonos.secundario.clone().multiplyScalar(0.85), tonos.mal.clone().lerp(tonos.muro, 0.35), tonos.agua.clone().lerp(tonos.muro, 0.3), tonos.medio.clone().lerp(tonos.muro, 0.3)];
      const cLuz = lin(COL.luces), cApagada = tonos.muro.clone().lerp(tonos.linea, 0.15).multiplyScalar(0.95), cSombra = tonos.linea.clone().multiplyScalar(0.35);
      const cBien = tonos.bien.clone(), cMedio = tonos.medio.clone(), cMal = tonos.mal.clone();

      // ---- una forma sólida: plantilla escalada, (op.jit) movida por vértice, girada en y y puesta en (X, Y) del mundo
      // sobre la altura h0; cada cara con su luz. op.mece = {base, alto, amp, fase}: va a la malla que se mece.
      let fija, mece, luces, sombras, halos, charcos, semaforos;
      const forma = (dst, T, X, Y, h0, sx, sy, sz, rot, col, op = {}) => {
        const cr = Math.cos(rot), sr = Math.sin(rot), ox = op.ox || 0, oy = op.oy || 0, oz = op.oz || 0, v = [];
        const inc = op.inc || 0;                                      // inclinación a lo largo de x local (palmeras)
        for (let i = 0; i < T.length; i += 3) {
          const j = op.jit ? op.jit(i / 3) : 1;
          let x = T[i] * sx * j + ox, y = T[i + 1] * sy * j + oy, z = T[i + 2] * sz * j + oz;
          if (inc) x += inc * y;
          v.push(X + (x * cr + z * sr) * M1, h0 + y * M1, -Y + (-x * sr + z * cr) * M1);
        }
        for (let i = 0, k = 0; i < v.length; i += 9, k++) {
          const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
          if (op.arriba && ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          c.copy(col).multiplyScalar((op.plana ? op.plana + (1 - op.plana) * sombra(nx, ny, nz) : sombra(nx, ny, nz)) * (op.ton ? op.ton(k) : 1));
          const q = dst.pos.length / 3;
          for (let j = 0; j < 9; j += 3) {
            dst.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); dst.col.push(c.r, c.g, c.b);
            if (dst.w) { const m = op.mece; dst.w.push(m ? clamp((v[i + j + 1] - m.base) / m.alto, 0, 1.3) * m.amp : 0); dst.f.push(m ? m.fase : 0); }
          }
          dst.idx.push(q, q + 1, q + 2);
        }
      };
      const disco = (dst, X, Y, h, r, col, n = 10) => {               // un disco plano (sombra de contacto, pozo, agua)
        const q = dst.pos.length / 3; dst.pos.push(X, h, -Y); dst.col.push(col.r, col.g, col.b);
        for (let i = 0; i <= n; i++) { const a = i / n * TAU; dst.pos.push(X + Math.cos(a) * r, h, -Y - Math.sin(a) * r); dst.col.push(col.r, col.g, col.b); }
        for (let i = 0; i < n; i++) dst.idx.push(q, q + 1 + i, q + 2 + i);
      };
      // un tronco o un cable rígido de A a B (metros locales ya puestos: three), cónico
      const vara = (dst, A, B, r0, r1, col, lados = 5) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1); p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        for (let i = 0; i < lados; i++) {
          const t0 = TAU * i / lados, t1 = TAU * (i + 1) / lados, tm = (t0 + t1) / 2;
          const o = (t, r) => [0, 1, 2].map((k) => (Math.cos(t) * p1[k] + Math.sin(t) * p2[k]) * r);
          const nm = o(tm, 1), q = dst.pos.length / 3; c.copy(col).multiplyScalar(sombra(nm[0], nm[1], nm[2]));
          for (const [P0, W] of [[A, o(t0, r0)], [A, o(t1, r0)], [B, o(t1, r1)], [B, o(t0, r1)]]) {
            dst.pos.push(P0[0] + W[0], P0[1] + W[1], P0[2] + W[2]); dst.col.push(c.r, c.g, c.b);
            if (dst.w) { dst.w.push(0); dst.f.push(0); }
          }
          dst.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        }
      };
      return piezas.map((p, np) => {
        fija = { pos: [], col: [], idx: [] }; mece = { pos: [], col: [], idx: [], w: [], f: [] }; luces = { pos: [], col: [], idx: [] };
        sombras = { pos: [], col: [], idx: [] };
        halos = []; charcos = [];                                     // de noche: [x, y(arriba), z, tamaño_m, fase]
        semaforos = [];                                               // {fl: [verde, ámbar, rojo] en three, fase}
        const sem = (p.semilla || 1) * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const I = p.items || {};
        const cada = (clase, fn) => { const a = I[clase] || []; for (let i = 0, n = 0; i + 3 < a.length; i += 4, n++) fn(a[i], a[i + 1], a[i + 2], a[i + 3], n); };
        const H0 = (x, y) => ctx.suelo(x, y);     // el suelo del mundo: el ambiente no se sube al relieve de otra pieza
        // ---------------- vegetación
        const copa = (x, y, r, e, n, k0) => {
          const h = H0(x, y), alto = 2.4 * e, R = 2.1 * e, col = cCopa[Math.floor(hz(n, k0) * 3) % 3], f = hz(n, k0 + 1) * TAU;
          forma(fija, CIL, x, y, h, 0.2 * e, alto + 0.6, 0.2 * e, 0, cTronco);
          const m = { base: h + alto * 0.8 * M1, alto: 3 * e * M1, amp: 0.07 * e * M1, fase: f };
          forma(mece, ICO, x, y, h, R, R * 0.85, R, r, col, { oy: alto + R * 0.8, jit: (u) => 0.85 + 0.3 * hz(n * 13 + u, k0 + 2), ton: (q) => 0.86 + 0.28 * hz(n * 29 + q, k0 + 3), mece: m });
          for (let b = 0; b < 2; b++) {
            const a = hz(n, k0 + 4 + b) * TAU, d = R * 0.6;
            forma(mece, ICO, x, y, h, R * 0.62, R * 0.55, R * 0.62, r + b, col.clone().multiplyScalar(0.92 + 0.16 * b),
              { ox: Math.cos(a) * d, oz: Math.sin(a) * d, oy: alto + R * (0.55 + 0.5 * b), jit: (u) => 0.85 + 0.3 * hz(n * 17 + u + b, k0 + 5), mece: m });
          }
          disco(sombras, x, y, h + 0.06 * M1, R * 1.05 * M1, cSombra);
        };
        cada("copa", (x, y, r, e, n) => copa(x, y, r, e, n, 10));
        cada("alcorque", (x, y, r, e, n) => {
          copa(x, y, r, e * 0.72, n, 40);
          const h = H0(x, y);
          forma(fija, CAJA, x, y, h, 1.3, 0.07, 1.3, Math.round(r / (TAU / 4)) * TAU / 4, cPozo, { plana: 0.6 });
        });
        cada("pino", (x, y, r, e, n) => {
          const h = H0(x, y), m = { base: h + 2 * M1, alto: 7 * e * M1, amp: 0.06 * e * M1, fase: hz(n, 61) * TAU };
          forma(fija, CIL, x, y, h, 0.16 * e, 1.6 * e, 0.16 * e, 0, cTronco);
          const capas = 3 + (hz(n, 62) < 0.5 ? 1 : 0);
          for (let k = 0; k < capas; k++) {
            const u = k / capas, R = (1.6 - 1.1 * u) * e;
            forma(mece, CONO, x, y, h, R, 3.0 * e, R, r + k, cPino.clone().multiplyScalar(0.9 + 0.2 * hz(n, 63 + k)), { oy: (1.2 + 1.7 * k) * e, mece: m, ton: (q) => 0.9 + 0.2 * hz(n * 7 + q, 70) });
          }
          disco(sombras, x, y, h + 0.06 * M1, 1.5 * e * M1, cSombra);
        });
        const mata = (x, y, r, e, n, col, R0, cuantas, k0) => {
          const h = H0(x, y), m = { base: h, alto: 2 * M1, amp: 0.05 * M1, fase: hz(n, k0) * TAU };
          for (let b = 0; b < cuantas; b++) {
            const a = hz(n, k0 + 1 + b) * TAU, d = R0 * e * 0.55 * (b ? 1 : 0), R = R0 * e * (0.7 + 0.35 * hz(n, k0 + 9 + b));
            forma(mece, ICO, x, y, h, R, R * 0.75, R, r + b, col.clone().multiplyScalar(0.88 + 0.24 * hz(n, k0 + 17 + b)),
              { ox: Math.cos(a) * d, oz: Math.sin(a) * d, oy: R * 0.55, jit: (u) => 0.8 + 0.4 * hz(n * 11 + u + b, k0 + 25), mece: m });
          }
          disco(sombras, x, y, h + 0.05 * M1, R0 * e * 1.2 * M1, cSombra, 8);
        };
        cada("arbusto", (x, y, r, e, n) => mata(x, y, r, e, n, cArbusto, 1.0, 3, 100));
        cada("matorral", (x, y, r, e, n) => mata(x, y, r, e, n, cMatorral, 0.5, 4, 140));
        cada("piedra", (x, y, r, e, n) => {
          const h = H0(x, y); forma(fija, OCT, x, y, h, 0.6 * e, 0.38 * e, 0.45 * e, r, cPiedra, { oy: 0.05, jit: (u) => 0.75 + 0.5 * hz(n * 7 + u, 180) });
          if (hz(n, 181) < 0.5) forma(fija, OCT, x, y, h, 0.32 * e, 0.22 * e, 0.28 * e, r + 1, cPiedra.clone().multiplyScalar(0.92), { ox: 0.7 * e, jit: (u) => 0.75 + 0.5 * hz(n * 5 + u, 182) });
        });
        cada("roca", (x, y, r, e, n) => {
          const h = H0(x, y), k = 2 + (hz(n, 190) < 0.5 ? 1 : 0);
          for (let b = 0; b < k; b++) forma(fija, OCT, x, y, h, (1.1 - 0.3 * b) * e, (0.7 - 0.15 * b) * e, (0.9 - 0.25 * b) * e, r + b * 1.7, cRoca.clone().multiplyScalar(0.9 + 0.2 * hz(n, 191 + b)),
            { ox: b * 0.8 * e, oz: (b - 1) * 0.5 * e, oy: -0.1, jit: (u) => 0.7 + 0.6 * hz(n * 9 + u + b, 195) });
        });
        cada("flores", (x, y, r, e, n) => {
          const h = H0(x, y), m = { base: h, alto: 0.8 * M1, amp: 0.06 * M1, fase: hz(n, 200) * TAU }, cf = cFlores[Math.floor(hz(n, 201) * 3) % 3];
          for (let b = 0; b < 14; b++) {
            const a = hz(n, 210 + b) * TAU, d = 2.2 * e * Math.sqrt(hz(n, 230 + b)), ax = Math.cos(a) * d, az = Math.sin(a) * d, hh = 0.35 + 0.3 * hz(n, 250 + b);
            forma(mece, CONO3, x, y, h, 0.12, hh, 0.12, b, cPasto, { ox: ax, oz: az, mece: m });
            forma(mece, OCT, x, y, h, 0.13, 0.11, 0.13, b, b % 4 ? cf : cFlores[(Math.floor(hz(n, 201) * 3) + 1) % 3], { ox: ax, oz: az, oy: hh, plana: 0.55, mece: m });
          }
        });
        cada("pasto", (x, y, r, e, n) => {
          const h = H0(x, y), m = { base: h, alto: 1.1 * M1, amp: 0.09 * M1, fase: hz(n, 260) * TAU };
          for (let b = 0; b < 16; b++) {
            const a = hz(n, 270 + b) * TAU, d = 2.3 * e * Math.sqrt(hz(n, 290 + b));
            forma(mece, CONO3, x, y, h, 0.14, 0.75 + 0.5 * hz(n, 310 + b), 0.14, b, cPasto.clone().multiplyScalar(0.85 + 0.3 * hz(n, 330 + b)), { ox: Math.cos(a) * d, oz: Math.sin(a) * d, mece: m });
          }
        });
        cada("palmera", (x, y, r, e, n) => {
          const h = H0(x, y), alto = (7 + 2.5 * hz(n, 350)) * e, inc = 0.12 + 0.12 * hz(n, 351), S = 6;
          const pt = (u) => { const yy = alto * u; return [x + Math.cos(r) * inc * yy * yy / alto * M1, h + yy * M1, -y - Math.sin(r) * inc * yy * yy / alto * M1]; };
          for (let k = 0; k < S; k++) vara(fija, pt(k / S), pt((k + 1) / S), (0.24 - 0.08 * k / S) * e * M1, (0.24 - 0.08 * (k + 1) / S) * e * M1, cTronco.clone().lerp(tonos.muro, 0.25).multiplyScalar(k % 2 ? 0.92 : 1.04), 6);
          const top = pt(1), m = { base: top[1] - 1.2 * M1, alto: 2.5 * M1, amp: 0.14 * M1, fase: hz(n, 352) * TAU };
          const cH = V(kv * 1.05).lerp(tonos.bien, 0.15), F = 8;
          for (let k = 0; k < F; k++) {                                 // las palmas: hojas largas que caen, cada una dos caras
            const a = k / F * TAU + hz(n, 360 + k) * 0.5, L = (3.2 + 0.8 * hz(n, 370 + k)) * e * M1, ca = Math.cos(a), sa = Math.sin(a), w = 0.55 * e * M1;
            const mid = [top[0] + ca * L * 0.55, top[1] + 0.5 * M1, top[2] - sa * L * 0.55], tip = [top[0] + ca * L, top[1] - (1.4 + 0.8 * hz(n, 380 + k)) * e * M1, top[2] - sa * L];
            const px = -sa * w, pz = -ca * w;
            const q = mece.pos.length / 3, col = cH.clone().multiplyScalar(0.85 + 0.3 * hz(n, 390 + k));
            const P = [top, [mid[0] + px, mid[1], mid[2] + pz], tip, [mid[0] - px, mid[1], mid[2] - pz]];
            const k1 = sombra(0, 1, 0) * 0.95, k2 = sombra(ca * 0.5, 0.8, -sa * 0.5);
            P.forEach((v, j) => { mece.pos.push(...v); const kk = j % 2 ? k2 : k1; mece.col.push(col.r * kk, col.g * kk, col.b * kk);
              mece.w.push(clamp((v[1] - m.base) / m.alto, 0, 1.3) * m.amp * (j === 2 ? 1.6 : 1)); mece.f.push(m.fase + k * 0.3); });
            mece.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
          forma(fija, ICO, top[0], -top[2], top[1] - 0.2 * M1, 0.45 * e, 0.4 * e, 0.45 * e, 0, cTronco.clone().lerp(tonos.medio, 0.2));
          disco(sombras, x + Math.cos(r) * inc * alto * M1, y + Math.sin(r) * inc * alto * M1, h + 0.06 * M1, 2.6 * e * M1, cSombra);
        });
        // ---------------- construcciones y mobiliario
        cada("rancho", (x, y, r, e, n) => {
          const h = H0(x, y), L = 6 * e, W = 4.4 * e, A = 2.4 * e;
          forma(fija, CAJA, x, y, h, L, A, W, r, cAdobe.clone().multiplyScalar(0.92 + 0.16 * hz(n, 400)));
          // techo de paja a dos aguas: dos planos inclinados (cajas delgadas giradas sobre x local)
          const cr = Math.cos(r), sr = Math.sin(r);
          for (const s of [1, -1]) {
            const T = [], ang = 0.55 * s;
            for (let i = 0; i < CAJA.length; i += 3) {
              const bx = CAJA[i] * (L + 1.2), by = CAJA[i + 1] * 0.25, bz = CAJA[i + 2] * (W * 0.62);
              const zz = bz * Math.cos(ang) - by * Math.sin(ang), yy = bz * Math.sin(ang) + by * Math.cos(ang);
              T.push(bx, yy, zz + s * W * 0.27);
            }
            forma(fija, T, x, y, h, 1, 1, 1, r, cPaja, { oy: A + 0.75 * e, ton: (q) => 0.9 + 0.2 * hz(n * 3 + q, 410) });
          }
          // la puerta y una ventana (encendida de noche)
          const vx = x + cr * (L / 2 + 0.03) * M1, vy = y + sr * (L / 2 + 0.03) * M1;
          forma(fija, CAJA, vx, vy, h, 0.06, 1.8 * e, 0.9 * e, r, tonos.linea.clone().multiplyScalar(0.7), { oz: -0.9 * e });
          forma(noche ? luces : fija, CAJA, vx, vy, h, 0.06, 0.7 * e, 0.8 * e, r, noche ? cLuz : tonos.linea.clone().lerp(tonos.agua, 0.3), { oz: 1.1 * e, oy: 1.0 * e });
          if (noche) halos.push([vx + 0.3 * cr * M1, h + 1.35 * e * M1, -(vy + 0.3 * sr * M1), 2.2, hz(n, 411) * TAU]);
          disco(sombras, x, y, h + 0.05 * M1, 4.2 * e * M1, cSombra, 12);
        });
        const foco = (X, Y, Z, tam, fase, charco) => {                 // una luz encendida: halo y, si va alta, el charco en el suelo
          halos.push([X, Y, Z, tam, fase]); if (charco) charcos.push([X, H0(X, -Z) + 0.08 * M1, Z, charco, fase]);
        };
        cada("farola", (x, y, r, e, n) => {
          const h = H0(x, y), cr = Math.cos(r), sr = Math.sin(r), A = 4.4;
          forma(fija, CIL, x, y, h, 0.16, 0.5, 0.16, 0, cMetal);
          forma(fija, CIL, x, y, h, 0.075, A, 0.075, 0, cMetal);
          forma(fija, CAJA, x, y, h, 0.9, 0.07, 0.07, r, cMetal, { ox: 0.4, oy: A - 0.1 });
          forma(noche ? luces : fija, CAJA, x, y, h, 0.5, 0.16, 0.3, r, noche ? cLuz : cApagada, { ox: 0.8, oy: A - 0.25 });
          if (noche) foco(x + cr * 0.8 * M1, h + (A - 0.3) * M1, -(y + sr * 0.8 * M1), 4.5, hz(n, 420) * TAU, 6.5);
        });
        cada("poste", (x, y, r, e, n) => {
          const h = H0(x, y), cr = Math.cos(r), sr = Math.sin(r), A = 8;
          forma(fija, CIL, x, y, h, 0.14, A, 0.14, 0, cConcreto, { ton: (q) => 0.95 + 0.1 * (q % 2) });
          forma(fija, CAJA, x, y, h, 0.12, 0.12, 1.8, r, cMadera, { oy: A - 0.45 });
          forma(fija, CAJA, x, y, h, 1.5, 0.07, 0.07, r, cMetal, { ox: 0.75, oy: A - 1.5 });
          forma(noche ? luces : fija, CAJA, x, y, h, 0.45, 0.14, 0.26, r, noche ? cLuz : cApagada, { ox: 1.45, oy: A - 1.65 });
          if (hz(n, 430) < 0.3) forma(fija, CIL, x, y, h, 0.35, 0.8, 0.35, 0, cConcreto.clone().multiplyScalar(0.85), { oz: -0.45, oy: A - 2.6 });   // un transformador
          if (noche) foco(x + cr * 1.45 * M1, h + (A - 1.75) * M1, -(y + sr * 1.45 * M1), 4.0, hz(n, 431) * TAU, 7);
        });
        cada("postec", (x, y, r, e, n) => forma(fija, CIL, x, y, H0(x, y), 0.07, 1.3 + 0.12 * hz(n, 440), 0.07, 0, cTronco.clone().multiplyScalar(0.9 + 0.2 * hz(n, 441))));
        cada("banca", (x, y, r, e, n) => {
          const h = H0(x, y);
          forma(fija, CAJA, x, y, h, 1.7, 0.08, 0.5, r, cMadera, { oy: 0.42 });
          forma(fija, CAJA, x, y, h, 1.7, 0.42, 0.07, r, cMadera, { oy: 0.55, oz: 0.24 });
          for (const s of [-0.7, 0.7]) forma(fija, CAJA, x, y, h, 0.08, 0.45, 0.5, r, cMetal, { ox: s });
        });
        cada("basurero", (x, y, r, e, n) => { const h = H0(x, y); forma(fija, CIL, x, y, h, 0.25, 0.85, 0.25, 0, cMetal.clone().lerp(tonos.verde, 0.3)); forma(fija, CIL, x, y, h, 0.28, 0.08, 0.28, 0, cMetal, { oy: 0.85 }); });
        cada("bolardo", (x, y, r, e, n) => { const h = H0(x, y); forma(fija, CIL, x, y, h, 0.17, 0.55, 0.17, 0, cMetal); forma(fija, ICO, x, y, h, 0.21, 0.14, 0.21, 0, cMetal, { oy: 0.58 }); });
        cada("semaforo", (x, y, r, e, n) => {
          const h = H0(x, y), cr = Math.cos(r), sr = Math.sin(r), A = 5.2, L = 3.2;
          forma(fija, CIL, x, y, h, 0.1, A + 0.2, 0.1, 0, cMetal);
          forma(fija, CAJA, x, y, h, L, 0.1, 0.1, r, cMetal, { ox: L / 2, oy: A });
          forma(fija, CAJA, x, y, h, 0.32, 1.05, 0.38, r, tonos.linea.clone().multiplyScalar(0.8), { ox: L - 0.1, oy: A - 1.1 });
          const fl = [];
          [cBien, cMedio, cMal].forEach((col, k) => {
            const oy = A - 0.95 + (2 - k) * 0.33;
            forma(fija, CAJA, x, y, h, 0.05, 0.22, 0.22, r, col.clone().multiplyScalar(0.35), { ox: L - 0.1, oy, oz: -0.2 });
            // el foco mira hacia −z local (a la calle que cruza)
            fl.push([x + (cr * (L - 0.1) + (-0.25) * sr) * M1, h + (oy + 0.11) * M1, -(y + (sr * (L - 0.1) - (-0.25) * cr) * M1)]);
          });
          semaforos.push({ fl, fase: hz(n, 450) * 16 });
        });
        cada("parada", (x, y, r, e, n) => {
          const h = H0(x, y);
          forma(fija, CAJA, x, y, h, 3.8, 0.1, 1.7, r, cMetal.clone().lerp(tonos.muro, 0.3), { oy: 2.5 });
          for (const s of [-1.75, 1.75]) forma(fija, CAJA, x, y, h, 0.08, 2.5, 0.08, r, cMetal, { ox: s, oz: 0.75 });
          forma(fija, CAJA, x, y, h, 3.5, 1.9, 0.05, r, tonos.agua.clone().lerp(tonos.muro, 0.55), { oy: 0.4, oz: 0.8, plana: 0.4 });
          forma(fija, CAJA, x, y, h, 2.6, 0.07, 0.42, r, cMadera, { oy: 0.45, oz: 0.5 });
          if (noche) foco(x, h + 2.3 * M1, -y, 3.0, hz(n, 460) * TAU, 4);
        });
        cada("bote", (x, y, r, e, n) => {
          const h = H0(x, y), col = cBote[Math.floor(hz(n, 470) * cBote.length) % cBote.length];
          // el casco: proa en +x local, popa recta; caras a mano (dos lados, fondo y popa)
          const P = { pr: [2.3, 0.75, 0], ps: [-1.9, 0.62, 0.78], pb: [-1.9, 0.62, -0.78], ks: [-1.7, 0.08, 0.3], kb: [-1.7, 0.08, -0.3], kp: [1.9, 0.18, 0], ms: [0.4, 0.72, 0.85], mb: [0.4, 0.72, -0.85], fs: [0.4, 0.05, 0.38], fb: [0.4, 0.05, -0.38] };
          const T = [], t3 = (a, b, d) => T.push(...P[a], ...P[b], ...P[d]);
          t3("pr", "ms", "kp"); t3("ms", "fs", "kp"); t3("ms", "ps", "fs"); t3("ps", "ks", "fs");
          t3("pr", "kp", "mb"); t3("mb", "kp", "fb"); t3("mb", "fb", "pb"); t3("pb", "fb", "kb");
          t3("kp", "fs", "fb"); t3("fs", "ks", "kb"); t3("fs", "kb", "fb"); t3("ps", "pb", "ks"); t3("pb", "kb", "ks");
          forma(fija, T, x, y, h, e, e, e, r, col, { oy: 0.05 });
          forma(fija, CAJA, x, y, h, 3.4 * e, 0.04, 1.3 * e, r, tonos.linea.clone().lerp(tonos.muro, 0.35), { ox: -0.1, oy: 0.55 * e, plana: 0.5 });
          forma(fija, CAJA, x, y, h, 0.25 * e, 0.06, 1.5 * e, r, cMadera, { ox: 0.1 * e, oy: 0.6 * e });
          disco(sombras, x, y, h + 0.05 * M1, 2.2 * e * M1, cSombra, 10);
        });
        cada("jardinera", (x, y, r, e, n) => {
          const h = H0(x, y);
          forma(fija, CAJA, x, y, h, 3.4, 0.6, 1.5, r, cConcreto.clone().lerp(tonos.muro, 0.4));
          forma(fija, CAJA, x, y, h, 3.1, 0.04, 1.2, r, cPozo.clone().lerp(tonos.campo2, 0.4), { oy: 0.6 });
          const m = { base: h + 0.6 * M1, alto: 1.2 * M1, amp: 0.04 * M1, fase: hz(n, 480) * TAU };
          for (let b = 0; b < 3; b++) forma(mece, ICO, x, y, h, 0.55, 0.45, 0.55, r + b, cArbusto.clone().multiplyScalar(0.9 + 0.2 * hz(n, 481 + b)), { ox: (b - 1) * 1.0, oy: 0.95, mece: m, jit: (u) => 0.8 + 0.4 * hz(n * 5 + u + b, 485) });
        });
        // ---------------- la fuente
        let fuente = null;
        if (p.fuente) {
          const [fx, fy, rf] = p.fuente, h = H0(fx, fy);
          forma(fija, CIL12, fx, fy, h, rf, 0.55, rf, 0, cConcreto.clone().lerp(tonos.muro, 0.5));
          forma(fija, CIL12, fx, fy, h, rf + 0.35, 0.12, rf + 0.35, 0, cConcreto, { });
          forma(fija, CIL, fx, fy, h, 0.35, 1.5, 0.35, 0, cConcreto.clone().lerp(tonos.muro, 0.5));
          forma(fija, CIL12, fx, fy, h, 1.0, 0.18, 1.0, 0, cConcreto.clone().lerp(tonos.muro, 0.5), { oy: 1.4 });
          const agua = malla.nueva(); disco(agua, fx, fy, h + 0.5 * M1, (rf - 0.25) * M1, cAgua, 24); disco(agua, fx, fy, h + 1.6 * M1, 0.85 * M1, cAgua, 12);
          const matAgua = malla.material({ desfase: 1 }); malla.poner(agua, matAgua, 3);
          // el anillo que se abre en el agua (escala de t)
          const ani = malla.nueva(), N = 28, r0 = 1, r1 = 1.12;
          for (let i = 0; i < N; i++) {
            const a0 = i / N * TAU, a1 = (i + 1) / N * TAU, q = ani.pos.length / 3, cc = cAgua.clone().lerp(tonos.muro, 0.6);
            for (const [a, rr] of [[a0, r0], [a1, r0], [a1, r1], [a0, r1]]) { ani.pos.push(Math.cos(a) * rr, 0, -Math.sin(a) * rr); ani.col.push(cc.r, cc.g, cc.b); }
            ani.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
          }
          const matAni = malla.material({ alfa: 0.6, desfase: 2 }), anillos = [0, 1].map(() => { const m = malla.poner(ani, matAni, 4); m.position.set(fx, h + 0.52 * M1, -fy); return m; });
          fuente = { fx, fy, h, rf, matAgua, matAni, anillos };
        }
        // ---------------- las líneas: cables (catenaria entre postes) y alambre de las cercas
        const lin3 = [];
        const tendido = (runs, alturas, pandeo, sep) => {
          for (const run of runs || []) {
            for (let i = 0; i + 3 < run.length; i += 2) {
              const ax = run[i], ay = run[i + 1], bx = run[i + 2], by = run[i + 3], L = Math.hypot(bx - ax, by - ay) || 1;
              if (L > 60 * M1) continue;
              const nx = -(by - ay) / L, ny = (bx - ax) / L;
              for (const [hh, o] of alturas) {
                const ha = H0(ax, ay) + hh * M1, hb = H0(bx, by) + hh * M1, K = 8;
                let pv = null;
                for (let k = 0; k <= K; k++) {
                  const u = k / K, px = ax + (bx - ax) * u + nx * o * sep * M1, py = ay + (by - ay) * u + ny * o * sep * M1;
                  const pt = [px, ha + (hb - ha) * u - pandeo * L * 4 * u * (1 - u), -py];
                  if (pv) lin3.push(...pv, ...pt); pv = pt;
                }
              }
            }
          }
        };
        tendido(p.lineas && p.lineas.cable, [[7.55, 0.8], [7.55, -0.8], [7.0, 0]], 0.022, 1);
        const lin3c = lin3.length; tendido(p.lineas && p.lineas.cerca, [[0.45, 0], [0.8, 0], [1.15, 0]], 0.004, 0);
        const lineas = (arr, col, alfa) => {
          if (!arr.length) return;
          const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(arr), 3));
          const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: alfa })); l.frustumCulled = false; l.renderOrder = 5; scene.add(l);
        };
        lineas(lin3.slice(0, lin3c), tonos.linea.clone().multiplyScalar(noche ? 2.2 : 0.8), noche ? 0.55 : 0.75);
        lineas(lin3.slice(lin3c), tonos.linea.clone().lerp(tonos.muro, noche ? 0.35 : 0.35), noche ? 0.3 : 0.6);

        // ---------------- las mallas
        const ponerAcc = (acc, mat, orden) => { if (!acc.pos.length) return null; const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; };
        if (sombras.pos.length) ponerAcc(sombras, malla.material({ alfa: dia ? 0.32 : 0.22, desfase: 2 }), 2);
        const matFija = malla.material(); ponerAcc(fija, matFija, 3);
        const mm = ponerAcc(mece, malla.material(), 3);
        const base = mm ? Float32Array.from(mm.geometry.attributes.position.array) : null, W = Float32Array.from(mece.w), F = Float32Array.from(mece.f);
        // lo que emite (no se tiñe con la hora): color de vértice tal cual, a sRGB
        const GAMMA = "vec3 g(vec3 c){ return mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
        if (luces.pos.length) {
          const mat = new THREE.ShaderMaterial({ vertexShader: "attribute vec3 color; varying vec3 vC; void main(){ vC = color; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: GAMMA + "varying vec3 vC; void main(){ gl_FragColor = vec4(g(min(vC * 1.25, vec3(1.0))), 1.0); }" });
          ponerAcc(luces, mat, 3);
        }
        // halos (puntos que respiran) y charcos de luz en el suelo
        const puntos = (lista, fragA, aditivo, orden) => {
          const n = lista.length, P = new Float32Array(3 * Math.max(1, n)), T = new Float32Array(Math.max(1, n)), Fa = new Float32Array(Math.max(1, n)), C = new Float32Array(3 * Math.max(1, n));
          lista.forEach((h, i) => { P.set([h[0], h[1], h[2]], 3 * i); T[i] = h[3]; Fa[i] = h[4]; const cc = h[5] || cLuz; C.set([cc.r, cc.g, cc.b], 3 * i); });
          const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(P, 3)); g.setAttribute("aTam", new THREE.BufferAttribute(T, 1));
          g.setAttribute("aFase", new THREE.BufferAttribute(Fa, 1)); g.setAttribute("aCol", new THREE.BufferAttribute(C, 3));
          const mat = new THREE.ShaderMaterial({ uniforms: { uT: { value: 0 }, uK: { value: n ? 1 : 0 }, uEsc: { value: ctx.H * 0.5 * M1 }, uPul: { value: 0.05 } },
            transparent: true, depthWrite: false, blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
            vertexShader: "attribute float aTam, aFase; attribute vec3 aCol; uniform float uT, uEsc, uPul; varying vec3 vC; void main(){ vC = aCol; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
              " gl_PointSize = aTam <= 0.0 ? 0.0 : clamp(aTam * uEsc * (1.0 + uPul * sin(uT * 1.7 + aFase)) * projectionMatrix[1][1] / max(-mv.z, 0.001), 1.5, 140.0); }",
            fragmentShader: GAMMA + "uniform float uK; varying vec3 vC; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; " + fragA + " if (a < 0.003) discard; gl_FragColor = vec4(g(vC), a); }" });
          const pts = new THREE.Points(g, mat); pts.frustumCulled = false; pts.renderOrder = orden; pts.visible = n > 0; scene.add(pts);
          return { g, mat, P, C, T };
        };
        const H = noche ? puntos(halos, "float a = (exp(-r * r * 6.0) * 0.4 + exp(-r * r * 40.0) * 0.6) * uK;", true, 8) : null;
        let ch = null;
        if (noche && charcos.length) {                                // el charco: un disco tenue en el suelo bajo cada luz
          const acc = { pos: [], col: [], idx: [] }, A = [];
          for (const q of charcos) {
            const b = acc.pos.length / 3, R = q[3] * M1;
            acc.pos.push(q[0], q[1], q[2]); acc.col.push(1, 0, 0); A.push(0);
            for (let i = 0; i <= 14; i++) { const a = i / 14 * TAU; acc.pos.push(q[0] + Math.cos(a) * R, q[1], q[2] + Math.sin(a) * R); acc.col.push(0, 0, 0); A.push(1); }
            for (let i = 0; i < 14; i++) acc.idx.push(b, b + 1 + i, b + 2 + i);
          }
          const g = malla.geometria(acc); g.setAttribute("aR", new THREE.BufferAttribute(new Float32Array(A), 1));
          const mat = new THREE.ShaderMaterial({ uniforms: { cL: { value: cLuz.clone() } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
            polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -6,
            vertexShader: "attribute float aR; varying float vR; void main(){ vR = aR; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: GAMMA + "uniform vec3 cL; varying float vR; void main(){ float a = (1.0 - smoothstep(0.0, 1.0, vR)) * 0.32; gl_FragColor = vec4(g(cL), a); }" });
          ch = new THREE.Mesh(g, mat); ch.frustumCulled = false; ch.renderOrder = 2; scene.add(ch);
        }
        // semáforos: el foco encendido de cada uno (se mueve de un foco al otro con t)
        const SF = semaforos.length ? puntos(semaforos.map((s) => [...s.fl[0], noche ? 1.4 : 0.7, 0, cBien]), "float a = (exp(-r * r * 5.0) * 0.45 + exp(-r * r * 30.0) * 0.55) * uK;", true, 8) : null;
        if (SF) SF.mat.uniforms.uPul.value = 0;
        // gotas de la fuente
        let GT = null;
        if (fuente) {
          const N = 70, l = []; for (let i = 0; i < N; i++) l.push([fuente.fx, fuente.h, -fuente.fy, 0.16, 0, cAgua.clone().lerp(tonos.muro, 0.55)]);
          GT = puntos(l, "float a = (1.0 - smoothstep(0.45, 1.0, r)) * 0.9 * uK;", false, 7); GT.mat.uniforms.uPul.value = 0; GT.N = N;
        }
        return { id: p.id, mm, base, W, F, H, SF, semaforos, GT, fuente, matFija, cBien, cMedio, cMal };
      });
    },
    en(t, lista, ctx) {
      const M1 = ctx.metros(1);
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id]; s.matFija.uniforms.uBrillo.value = b ? 1 + 0.2 * (b - 1) : 1;
        // el vaivén: base + w·(sen lento + un soplo); x y z con desfase (la copa describe una elipse chica)
        if (s.mm) {
          const P = s.mm.geometry.attributes.position.array, B = s.base, W = s.W, F = s.F;
          for (let i = 0, v = 0; v < W.length; v++, i += 3) {
            const w = W[v];
            if (w === 0) continue;
            const f = F[v], o = Math.sin(1.05 * t + f) + 0.45 * Math.sin(2.3 * t + 1.7 * f) * (0.5 + 0.5 * Math.sin(0.31 * t + f));
            P[i] = B[i] + w * o; P[i + 2] = B[i + 2] + w * 0.55 * Math.sin(0.83 * t + 2.1 * f);
          }
          s.mm.geometry.attributes.position.needsUpdate = true;
        }
        if (s.H) s.H.mat.uniforms.uT.value = t;
        if (s.SF) {                                                   // ciclo de 16 s: verde 7 · ámbar 2.5 · rojo 6.5
          const P = s.SF.P, C = s.SF.C;
          s.semaforos.forEach((q, i) => {
            const u = ((t + q.fase) % 16 + 16) % 16, k = u < 7 ? 0 : u < 9.5 ? 1 : 2, col = [s.cBien, s.cMedio, s.cMal][k];
            P.set(q.fl[k], 3 * i); C.set([col.r, col.g, col.b], 3 * i);
          });
          s.SF.g.attributes.position.needsUpdate = true; s.SF.g.attributes.aCol.needsUpdate = true;
        }
        if (s.fuente) {
          const F = s.fuente;
          F.matAgua.uniforms.uBrillo.value = 1 + 0.1 * Math.sin(2.2 * t) + 0.05 * Math.sin(5.1 * t + 1);
          F.anillos.forEach((m, k) => { const u = ((t / 2.4 + k * 0.5) % 1 + 1) % 1, r = (0.9 + (F.rf - 1.3) * u) * M1; m.scale.set(r, 1, r); m.visible = u < 0.95; });
          F.matAni.uniforms.uAlfa.value = 0.45;
          const P = s.GT.P, N = s.GT.N, T0 = 1.3;                    // cada gota: sale de la taza de arriba y cae a la pila
          for (let j = 0; j < N; j++) {
            const u = ((t / T0 + j / N) % 1 + 1) % 1, a = j * 2.39996, vr = (0.9 + 0.5 * ctx.hash(j, 5)) * (F.rf - 1.0) / T0 * 0.8, tt = u * T0;
            const r = 0.6 + vr * tt, y = 1.75 + 1.4 * tt - 0.5 * 9.8 * 0.5 * tt * tt;
            P.set([F.fx + Math.cos(a) * r * M1, F.h + Math.max(0.5, y) * M1, -F.fy - Math.sin(a) * r * M1], 3 * j);
          }
          s.GT.g.attributes.position.needsUpdate = true;
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
