// Pieza «cafetal» (ficha: cafetal.json; reglas: scripts/maqueta_tipos/cafetal.py): una ladera de cafetal en terrazas. El
// polígono sube hacia `rumbo` (0 = este, 90 = norte) hasta `pendiente_m` en `hileras` escalones: cada uno, un banco plano
// y su talud; la ladera cierra con muros a los lados y atrás, hasta el suelo. En cada banco, una hilera de cafetos
// (arbustos de ~2 m: cuatro copas de hoja verde oscuro en cono, distintas por semilla) con racimos de cereza pegados a
// las ramas: las maduras (`maduras`) en el rojo del estilo (tonos.mal, nunca el acento), las verdes en un verde claro. Todo se arma una vez (una malla con la luz del estilo horneada, como los edificios); cada cuadro solo lee
// ctx.cuadro.brillo[id]: «resaltar» la pieza aviva las cerezas maduras sin cambiarles el color (más brillo y un halo rojo que se ve también de
// lejos). `personas` > 0 deja recolectores del catálogo (objeto persona) de pie entre las hileras. Seek puro.
(function (MAQ) {
  MAQ.PIEZAS.cafetal = {
    orden: 6,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = ES.modo === 1;
      return piezas.map((p, np) => {
        const pol = []; for (let i = 0; i + 1 < p.poligono.length; i += 2) pol.push([p.poligono[i], p.poligono[i + 1]]);
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r), vx = -uy, vy = ux;     // u: sube · v: a lo ancho
        const S = pol.map((q) => q[0] * ux + q[1] * uy), Wv = pol.map((q) => q[0] * vx + q[1] * vy);
        const s0 = Math.min(...S), s1 = Math.max(...S), L = s1 - s0, N = p.hileras, P = metros(p.pendiente_m);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const xy = (s, w) => [s * ux + w * vx, s * uy + w * vy];
        // el ancho del polígono a la altura s (lo más afuera, si el polígono no es convexo)
        const ancho = (s) => {
          const ss = clamp(s, s0 + 1e-3 * L, s1 - 1e-3 * L); let a = Infinity, b = -Infinity;
          for (let i = 0; i < pol.length; i++) {
            const j = (i + 1) % pol.length, sa = S[i], sb = S[j];
            if ((sa - ss) * (sb - ss) > 0 || sa === sb) continue;
            const w = Wv[i] + (Wv[j] - Wv[i]) * (ss - sa) / (sb - sa); a = Math.min(a, w); b = Math.max(b, w);
          }
          return a <= b ? [a, b] : [0, 0];
        };
        const alt = (k) => P * k / N;                                 // la altura del banco k
        const base0 = ctx.altura(...xy(s0 + L / 2, 0));
        // colores (todos de ctx.tonos): el banco, el talud y los muros; la hoja oscura; la cereza verde
        const cBanco = tonos.campo2.clone().lerp(tonos.campo, 0.3), cTalud = tonos.campo.clone().lerp(tonos.suelo, 0.65);
        const cMuro = tonos.campo.clone().lerp(tonos.suelo, 0.55);
        // la hoja: verde oscuro del estilo (su «bien» hundido en el campo); la cereza madura en su «mal» (rojo en todos los
        // estilos de three) y la verde en el verde claro, un poco hacia el «medio»
        const cHoja = tonos.bien.clone().lerp(tonos.campo, noche ? 0.66 : 0.55).multiplyScalar(noche ? 0.6 : 0.62);
        const cRoja = tonos.mal.clone().multiplyScalar(noche ? 1.0 : 0.92), cVerde = tonos.bien.clone().lerp(tonos.medio, 0.35).multiplyScalar(noche ? 0.62 : 0.85);
        const c = new THREE.Color();
        // ---- la ladera: bancos, taludes y muros, cada cara con su luz
        const acc = malla.nueva();
        const cara = (vs, col) => {                                  // vs: 4 vértices [x, y, z_escena] en orden; normal por producto
          const [a, b, , d] = vs, e1 = [b[0] - a[0], b[2] - a[2], -(b[1] - a[1])], e2 = [d[0] - a[0], d[2] - a[2], -(d[1] - a[1])];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n; if (ny < -0.05) { nx = -nx; ny = -ny; nz = -nz; }
          c.copy(col).multiplyScalar(sombra(nx, Math.abs(ny), nz));
          const q = acc.pos.length / 3;
          for (const v of vs) { acc.pos.push(v[0], base0 + v[2], -v[1]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        const muroLado = (sa, sb, ha, hb, lado, col) => {           // muro vertical en un costado, de la altura al suelo
          const wa = ancho(sa)[lado], wb = ancho(sb)[lado], A = xy(sa, wa), B = xy(sb, wb);
          const vs = [[A[0], A[1], 0], [B[0], B[1], 0], [B[0], B[1], hb], [A[0], A[1], ha]];
          const dx = B[0] - A[0], dy = B[1] - A[1], l = Math.hypot(dx, dy) || 1, sg = lado ? -1 : 1;   // normal hacia afuera
          c.copy(col).multiplyScalar(sombra(sg * dy / l, 0, sg * dx / l));
          const q = acc.pos.length / 3;
          for (const v of vs) { acc.pos.push(v[0], base0 + v[2], -v[1]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        };
        const aristas = [], FB = 0.74;                               // FB: la parte del escalón que es banco
        const banda = (sa, sb, ha, hb, col) => {
          const [a0, b0] = ancho(sa), [a1, b1] = ancho(sb), A = xy(sa, a0), B = xy(sa, b0), C = xy(sb, b1), D = xy(sb, a1);
          cara([[A[0], A[1], ha], [B[0], B[1], ha], [C[0], C[1], hb], [D[0], D[1], hb]], col);
          muroLado(sa, sb, ha, hb, 0, cMuro); muroLado(sa, sb, ha, hb, 1, cMuro);
        };
        for (let k = 0; k < N; k++) {
          const sa = s0 + L * k / N, sm = s0 + L * (k + FB) / N, sb = s0 + L * (k + 1) / N, h = alt(k) + metros(0.25);
          banda(sa, sm, h, h, cBanco);
          if (k < N - 1 || P > 0) banda(sm, sb, h, alt(k + 1) + metros(0.25), cTalud);
          for (const s of [sm]) {
            const [a, b] = ancho(s), A = xy(s, a), B = xy(s, b); aristas.push(A[0], base0 + h, -A[1], B[0], base0 + h, -B[1]);
          }
        }
        { // atrás: el muro del borde alto, hasta el suelo
          const [a, b] = ancho(s1), A = xy(s1, a), B = xy(s1, b), h = P + metros(0.25);
          const q = acc.pos.length / 3; c.copy(cMuro).multiplyScalar(sombra(ux, 0, -uy));
          for (const v of [[A[0], A[1], 0], [B[0], B[1], 0], [B[0], B[1], h], [A[0], A[1], h]]) { acc.pos.push(v[0], base0 + v[2], -v[1]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
        }
        const matSuelo = malla.material(); malla.poner(acc, matSuelo, 2);
        if (aristas.length) {
          const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(aristas), 3));
          const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: lin(COL.linea), transparent: true, opacity: ES.modo === 4 ? 0.8 : ES.modo === 2 ? 0.55 : 0.28 }));
          l.frustumCulled = false; l.renderOrder = 3; scene.add(l);
        }
        // ---- los cafetos y sus cerezas. Un cafeto: cuatro copas de hoja apiladas en cono (icosaedros con los vértices
        // movidos por semilla, cada cara con su tono), de la falda ancha a la punta; las cerezas, en racimos de 3–4 pegados
        // al borde de las copas de abajo (donde están las ramas). Maduras en el rojo del estilo (tonos.mal), verdes en el
        // verde claro; el acento queda fuera de la fruta (una cereza en el acento ámbar se lee como luz de ciudad).
        const ico = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
        const oct = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
        const vIco = [], uni = [];                                     // a qué vértice único (12) pertenece cada vértice del icosaedro
        for (let i = 0; i < ico.length; i += 3) {
          let u = uni.findIndex((q) => Math.abs(q[0] - ico[i]) + Math.abs(q[1] - ico[i + 1]) + Math.abs(q[2] - ico[i + 2]) < 1e-4);
          if (u < 0) { u = uni.length; uni.push([ico[i], ico[i + 1], ico[i + 2]]); } vIco.push(u);
        }
        const hojas = malla.nueva(), rojas = malla.nueva(), verdes = malla.nueva(), halo = [];
        // cada triángulo con su luz (normal de cara); jit(u) mueve el vértice único u (la copa irregular); tri(k) varía el tono
        // de la cara k; plana > 0 aclara la sombra (la fruta se lee aun en la cara oscura)
        const solido = (dst, tri, cx, cy, cz, sx, sy, sz, rot, col, jit, ton, plana) => {
          const cr = Math.cos(rot), sr = Math.sin(rot), v = [];
          for (let i = 0, k = 0; i < tri.length; i += 3, k++) {
            const f = jit ? jit(vIco[k]) : 1, x = tri[i] * sx * f, y = tri[i + 1] * sy * f, z = tri[i + 2] * sz * f;
            v.push(cx + x * cr - z * sr, cy + y, cz + x * sr + z * cr);
          }
          for (let i = 0, k = 0; i < v.length; i += 9, k++) {
            const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const n = Math.hypot(nx, ny, nz) || 1, sb = sombra(nx / n, ny / n, nz / n);
            c.copy(col).multiplyScalar((plana ? plana + (1 - plana) * sb : sb) * (ton ? ton(k) : 1));
            const q = dst.pos.length / 3;
            for (let j = 0; j < 9; j += 3) { dst.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); dst.col.push(c.r, c.g, c.b); }
            dst.idx.push(q, q + 1, q + 2);
          }
        };
        // las copas: [altura del centro, radio a lo ancho, radio alto] (× ry, × rx): ~2 m de alto, ~1.9 m de falda
        const COPAS = [[0.42, 1.0, 0.42], [0.9, 0.8, 0.38], [1.35, 0.58, 0.33], [1.74, 0.34, 0.26]];
        const paso = 2.6, rx = metros(0.95), ry = metros(1.0), rc = metros(0.12);
        let total = 0; for (let k = 0; k < N; k++) { const [a, b] = ancho(s0 + L * (k + 0.38) / N); total += Math.max(0, b - a) / paso; }
        const dil = Math.max(1, total / 3000);                       // tope: ~3000 cafetos (se espacian más en un cafetal enorme)
        let n = 0, nr = 0;
        for (let k = 0; k < N; k++) {
          const s = s0 + L * (k + 0.36) / N, [a, b] = ancho(s), h = alt(k) + metros(0.25), m = Math.floor((b - a - 2) / (paso * dil));
          for (let j = 0; j <= m; j++, n++) {
            const w = a + 1 + (b - a - 2) * (m ? j / m : 0.5) + (hz(n, 1) - 0.5) * 0.6, ds = (hz(n, 2) - 0.5) * 0.5;
            const [x, y] = xy(s + ds, w), e = 0.82 + 0.36 * hz(n, 3), ew = e * (0.88 + 0.24 * hz(n, 6)), rot = hz(n, 4) * 6.283;
            const y0 = base0 + h, tono = cHoja.clone().multiplyScalar(0.86 + 0.28 * hz(n, 5));
            const cop = COPAS.map((C, b) => {                          // cada copa, un poco corrida y girada (el cafeto no es simétrico)
              const ox = (hz(n, 60 + b) - 0.5) * 0.22 * rx * ew, oz = (hz(n, 64 + b) - 0.5) * 0.22 * rx * ew;
              return { cx: x + ox, cy: y0 + C[0] * ry * e, cz: -y + oz, R: C[1] * rx * ew, Ry: C[2] * ry * e, rot: rot + b * 0.9 };
            });
            cop.forEach((q, b) => solido(hojas, ico, q.cx, q.cy, q.cz, q.R, q.Ry, q.R, q.rot, tono,
              (u) => 0.84 + 0.32 * hz(n * 4 + b, 200 + u), (f) => 0.8 + 0.4 * hz(n * 4 + b, 300 + f), 0));
            for (let r = 0; r < 6; r++) {                            // racimos: en el borde de las tres copas de abajo, sobre la rama
              const q = cop[r % 3], az = rot + r * 1.047 + hz(n, 10 + r) * 0.7, el = -0.35 + 0.5 * hz(n, 20 + r);
              const ca = Math.cos(az), sa = Math.sin(az), ce = Math.cos(el);
              const bx = q.cx + ca * ce * q.R * 0.92, by = q.cy + Math.sin(el) * q.Ry * 0.92, bz = q.cz + sa * ce * q.R * 0.92;
              const tx = -sa, tz = ca, nC = 3 + (hz(n, 40 + r) < 0.5 ? 1 : 0);   // a lo largo de la rama (tangente)
              let maduro = 0;
              for (let i = 0; i < nC; i++) {
                const d = (i - (nC - 1) / 2) * rc * 1.6, dy = (hz(n, 70 + r * 4 + i) - 0.5) * rc * 1.2;
                const px = bx + tx * d + ca * rc * 0.5, py = by + dy, pz = bz + tz * d + sa * rc * 0.5;
                const madura = hz(n, 30 + r * 4 + i) < p.maduras; if (madura) maduro++;
                solido(madura ? rojas : verdes, oct, px, py, pz, rc, rc * 1.15, rc, az + i, madura ? cRoja : cVerde, null, null, 0.45);
              }
              if (maduro) { halo.push(bx + ca * rc, by, bz + sa * rc); nr++; }
            }
          }
        }
        const sinTraslado = (accm, mat, orden) => {                  // las mallas de los cafetos ya vienen en coordenadas de escena
          const m = new THREE.Mesh(malla.geometria(accm), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m;
        };
        const matHoja = malla.material(), matRoja = malla.material(), matVerde = malla.material();
        sinTraslado(hojas, matHoja, 3); sinTraslado(verdes, matVerde, 3); sinTraslado(rojas, matRoja, 4);
        // el halo de las maduras: un punto por racimo, en su mismo rojo (de lejos la cereza es más chica que un píxel); se
        // enciende al resaltar: aviva la fruta sin cambiarle el color
        const gh = new THREE.BufferGeometry(); gh.setAttribute("position", new THREE.BufferAttribute(new Float32Array(halo.length ? halo : [0, 0, 0]), 3));
        const mh = new THREE.ShaderMaterial({ uniforms: { cA: { value: cRoja.clone() }, uK: { value: 0 }, uTam: { value: ctx.H * 0.5 * metros(0.9) } },
          transparent: true, depthWrite: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
          vertexShader: "uniform float uTam, uK; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uK > 0.0 ? clamp(uTam * projectionMatrix[1][1] / max(-mv.z, 0.001), 2.5, 22.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA; uniform float uK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = (exp(-r * r * 5.0) * 0.5 + exp(-r * r * 40.0) * 0.5) * uK; if (a < 0.003) discard; vec3 c = cA; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }" });
        const ph = new THREE.Points(gh, mh); ph.frustumCulled = false; ph.renderOrder = 8; ph.visible = nr > 0; scene.add(ph);
        // ---- recolectores: de pie en el banco, entre su hilera y el talud, mirando a lo largo de la hilera
        const gente = [];
        for (let i = 0; i < p.personas; i++) {
          const k = Math.min(N - 1, Math.floor((i + 0.5) * N / p.personas)), s = s0 + L * (k + 0.6) / N, [a, b] = ancho(s);
          const w = a + (b - a) * (0.2 + 0.6 * hz(i, 50)), [x, y] = xy(s, w), sg = hz(i, 51) < 0.5 ? 1 : -1;
          const fl = ctx.flota("persona", 1, { lev: p.pendiente_m * k / N + 0.25, orden: 4,
            color: (_, vs) => vs[Math.floor(hz(i, 52) * vs.length) % vs.length] });
          gente.push({ fl, x, y, dx: vx * sg, dy: vy * sg });
        }
        return { id: p.id, matRoja, mh, gente };
      });
    },
    en(t, lista, ctx) {
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], k = b ? ctx.clamp((b - 1) / 0.9, 0, 1.2) : 0;
        s.matRoja.uniforms.uBrillo.value = 1 + 0.7 * k;
        s.mh.uniforms.uK.value = k;
        for (const g of s.gente) { g.fl.poner(0, g.x, g.y, g.dx, g.dy, 1, 0); g.fl.listo(); }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
