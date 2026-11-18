// Evento «crecer» (ficha: crecer.json; reglas: scripts/maqueta_tipos/crecer.py): una PILA de basura mezclada sube de una
// fracción de su alto (`de`) a otra (`a`) mientras dura el evento, capa por capa. Se puede llamar varias veces sobre la
// misma pieza: crece con la voz, se detiene y sigue (los `crecer` de una pieza comparten la pila; manda el último que empezó).
// Quieta antes del primero y después de cada uno (A1–A2): nada se mueve fuera de [t, t + dur] salvo en un gancho (t ≤ 0.1).
// La pila (u: a lo largo de `rumbo`; v: a su izquierda), en metros:
//  · el CUERPO: capas apiladas de `dz` m, cada una una banda abombada sobre un rectángulo redondeado con talud (bultos que
//    asoman por el borde, cada capa de su mezcla: orgánico, bolsas claras, bolsas oscuras, envases); la capa de arriba se
//    llena de 0 a dz sin saltos y un núcleo cierra las rendijas;
//  · la CIMA: una superficie con bultos (ruido fijo por semilla) y una alfombra de bolsas, envases, láminas y restos que
//    sube con ella (se va cubriendo de objetos al empezar), y restos sueltos al pie que salen mientras crece la primera capa;
//  · lo que CAE (`caida`): racimos de bolsas y envases que bajan desde encima de la pila, giran, se asientan con un rebote
//    corto y levantan una nube de polvo; quedan en la cima hasta que la capa siguiente los tapa.
// Con una pieza `pila` (MAQ.PILA.pilas[id], de piezas/pila.js) el cuerpo es el de la pila: aquí se le fija la fracción en
// `aplicar` (rec.fijar) y lo que cae se asienta en puntos de su cima (rec.punto) con sus mismas cosas (rec.dibujar).
// Publica también ctx.cuadro.nivel[pieza] (0–1) en `inicio`: otra pieza que dibuje su propia pila lo lee en su `en` y
// declara `crece: true` en su módulo para que aquí solo caiga lo que llega. Sin texto, sin colores escritos.
// Seek puro: el nivel, las capas y cada objeto que cae salen de t (ctx.hash para el azar fijo); nada se acumula entre cuadros.
(function (MAQ) {
  const TAU = 2 * Math.PI, KK = 0.32, PUNTOS = 6;
  const SRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";
  const ease = (u) => 0.45 * u + 0.55 * u * u * (3 - 2 * u);

  // un rectángulo redondeado de semiejes (a, b) y radio rc: el punto y la normal a la fracción s del perímetro
  function rrect(s, a, b, rc, out) {
    const lx = 2 * (a - rc), ly = 2 * (b - rc), q = Math.PI * rc / 2, P = 2 * lx + 2 * ly + 4 * q;
    let d = (((s % 1) + 1) % 1) * P;
    const arco = (g0, cx, cy, t) => { const g = g0 + t / Math.max(rc, 1e-6); out[0] = cx + rc * Math.cos(g); out[1] = cy + rc * Math.sin(g); out[2] = Math.cos(g); out[3] = Math.sin(g); };
    if (d <= ly) { out[0] = a; out[1] = -(b - rc) + d; out[2] = 1; out[3] = 0; return out; } d -= ly;
    if (d <= q) { arco(0, a - rc, b - rc, d); return out; } d -= q;
    if (d <= lx) { out[0] = a - rc - d; out[1] = b; out[2] = 0; out[3] = 1; return out; } d -= lx;
    if (d <= q) { arco(Math.PI / 2, -(a - rc), b - rc, d); return out; } d -= q;
    if (d <= ly) { out[0] = -a; out[1] = b - rc - d; out[2] = -1; out[3] = 0; return out; } d -= ly;
    if (d <= q) { arco(Math.PI, -(a - rc), -(b - rc), d); return out; } d -= q;
    if (d <= lx) { out[0] = -(a - rc) + d; out[1] = -b; out[2] = 0; out[3] = -1; return out; } d -= lx;
    arco(1.5 * Math.PI, a - rc, -(b - rc), Math.min(d, q)); return out;
  }

  MAQ.EVENTOS.crecer = {
    orden: 45,
    armar(ctx, lista) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const oscuro = ES.modo === 1, M = metros(1);
      const C = (k, alt) => lin(COL[k] || COL[alt] || COL.secundario);
      const kN = oscuro ? 1.25 : 1;
      // la mezcla (todo del estilo): orgánico, bolsas claras, bolsas oscuras, envases
      const PAL = [
        [C("tierra_media").multiplyScalar(0.6 * kN), C("tierra_media").lerp(tonos.verde, 0.4).multiplyScalar(0.66 * kN), C("tierra_alta").lerp(C("tierra_media"), 0.5).multiplyScalar(0.55 * kN)],
        [C("costa").lerp(tonos.secundario, 0.12).multiplyScalar(0.92), tonos.secundario.clone().lerp(C("costa"), 0.55), C("costa").lerp(C("tierra_alta"), 0.25).multiplyScalar(0.85)],
        [tonos.linea.clone().lerp(tonos.asfalto, 0.55).multiplyScalar(oscuro ? 0.6 : 0.42), tonos.asfalto.clone().lerp(C("tierra_baja"), 0.3).multiplyScalar(oscuro ? 0.85 : 0.6)],
        [tonos.agua.clone().lerp(C("costa"), 0.45), tonos.verde.clone().lerp(C("costa"), 0.45), C("costa").lerp(tonos.agua, 0.25), tonos.mal.clone().lerp(C("costa"), 0.55)],
      ];
      const PESO = [0.4, 0.28, 0.2, 0.12];
      const elige = (x, y) => { let k = 0, acc = PESO[0]; while (x > acc && k < 3) acc += PESO[++k]; const L = PAL[k]; return L[Math.floor(y * L.length) % L.length]; };
      const cPolvo = C("tierra_media").lerp(C("costa"), 0.45);
      const c = new THREE.Color();
      // plantillas de los objetos (triángulos sueltos, en metros, centradas en su base)
      const plant = (g) => g.toNonIndexed().attributes.position.array;
      const T_BOLSA = (() => { const a = plant(new THREE.SphereGeometry(0.5, 8, 5)), o = new Float32Array(a.length);
        for (let i = 0; i < a.length; i += 3) { const y = a[i + 1]; o[i] = a[i] * (1 + 0.18 * Math.sin(5 * a[i + 2])); o[i + 1] = (y < 0 ? y * 0.25 : y) + 0.13; o[i + 2] = a[i + 2]; } return o; })();
      const T_NUDO = plant(new THREE.ConeGeometry(0.09, 0.22, 6).translate(0, 0.72, 0));
      const T_BOTELLA = (() => { const g = new THREE.CylinderGeometry(0.5, 0.5, 1, 12); g.rotateZ(Math.PI / 2); g.translate(0, 0.5, 0); return plant(g); })();
      const T_RESTO = plant(new THREE.IcosahedronGeometry(0.5, 0).translate(0, 0.32, 0));
      const T_LAMINA = new Float32Array([-0.5, 0.06, -0.4, 0.5, 0.12, -0.35, 0.45, 0.02, 0.4, -0.5, 0.06, -0.4, 0.45, 0.02, 0.4, -0.45, 0.16, 0.35]);

      // un objeto suelto: plantilla × escala, girado (rumbo r, inclinación tx/tz), en el punto P (escena), con la luz horneada
      const pegar = (acc, tri, P, sx, sy, sz, r, col, tx = 0, tz = 0) => {
        const cr = Math.cos(r), sr = Math.sin(r), cx = Math.cos(tx), sx_ = Math.sin(tx), cz = Math.cos(tz), sz_ = Math.sin(tz), v = [];
        for (let i = 0; i < tri.length; i += 3) {
          let x = tri[i] * sx, y = tri[i + 1] * sy, z = tri[i + 2] * sz;
          let y1 = y * cx - z * sx_, z1 = y * sx_ + z * cx; y = y1; z = z1;
          let x1 = x * cz - y * sz_; y1 = x * sz_ + y * cz; x = x1; y = y1;
          v.push(P[0] + (x * cr - z * sr) * M, P[1] + y * M, P[2] + (x * sr + z * cr) * M);
        }
        for (let i = 0; i < v.length; i += 9) {
          const e1 = [v[i + 3] - v[i], v[i + 4] - v[i + 1], v[i + 5] - v[i + 2]], e2 = [v[i + 6] - v[i], v[i + 7] - v[i + 1], v[i + 8] - v[i + 2]];
          let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
          const n = Math.hypot(nx, ny, nz) || 1; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
          c.copy(col).multiplyScalar(sombra(nx / n, ny / n, nz / n));
          const q = acc.pos.length / 3;
          for (let j = 0; j < 9; j += 3) { acc.pos.push(v[i + j], v[i + j + 1], v[i + j + 2]); acc.col.push(c.r, c.g, c.b); }
          acc.idx.push(q, q + 1, q + 2);
        }
      };
      // un objeto de la basura (bolsa con su nudo, envase, lámina o resto orgánico), de tamaño base sK m
      const objeto = (acc, P, sK, hz, i, rumbo) => {
        const k = hz(i, 11), g = 0.7 + 0.6 * hz(i, 12), r = rumbo + TAU * hz(i, 13), tx = (hz(i, 14) - 0.5) * 0.5, tz = (hz(i, 15) - 0.5) * 0.5;
        if (k < 0.42) {          // bolsa (clara u oscura) con su nudo
          const col = elige(0.4 + 0.48 * hz(i, 16), hz(i, 17)), s = sK * g;
          pegar(acc, T_BOLSA, P, s * (1 + 0.3 * hz(i, 18)), s * 0.8, s * 0.85, r, col, tx, tz);
          pegar(acc, T_NUDO, P, s, s * 0.8, s, r, col.clone().multiplyScalar(0.85), tx, tz);
        } else if (k < 0.62) {   // envase acostado (botella, garrafa)
          const col = PAL[3][Math.floor(hz(i, 16) * PAL[3].length) % PAL[3].length], s = sK * g * 0.55;
          pegar(acc, T_BOTELLA, P, s * 1.0, s * 0.42, s * 0.42, r, col, 0, tz * 0.3);
        } else if (k < 0.8) {    // lámina de plástico doblada
          const col = elige(0.4 + 0.6 * hz(i, 16), hz(i, 17)), s = sK * g * 1.25;
          pegar(acc, T_LAMINA, P, s, s, s, r, col, tx, tz);
        } else {                 // resto orgánico
          const col = PAL[0][Math.floor(hz(i, 16) * 3) % 3], s = sK * g * 0.9;
          pegar(acc, T_RESTO, P, s * 1.1, s * 0.6, s, r, col, tx, tz);
        }
      };

      const grupos = {};
      lista.forEach((e) => { (grupos[e.pieza] = grupos[e.pieza] || []).push(e); });
      const pilas = Object.keys(grupos).map((pid, np) => {
        const evs = grupos[pid].slice().sort((a, b) => a.t - b.t), e0 = evs[0];
        const A = e0.ancho_m, F = e0.fondo_m, H = e0.alto_m;
        const ro = e0.rumbo * Math.PI / 180, ux = Math.cos(ro), uy = Math.sin(ro);
        const sem = (e0.semilla || 1) * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const W = (u, v) => [e0.x + (u * ux - v * uy) * M, e0.y + (u * uy + v * ux) * M];
        let b0 = Infinity;
        for (let i = -2; i <= 2; i++) for (let j = -2; j <= 2; j++) { const [x, y] = W(i * A / 4, j * F / 4); b0 = Math.min(b0, ctx.suelo(x, y)); }
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, b0 + h * M, -y]; };
        const N3 = (nu, nv, ny) => [nu * ux - nv * uy, ny, -(nu * uy + nv * ux)];
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // el nivel (fracción del alto) en t: función pura de todos los crecer de esta pila
        const nivelEn = (t) => {
          let L = evs[0].de;
          for (const e of evs) {
            if (t < e.t && !(e.t <= 0.1)) continue;
            const u = clamp((t - e.t) / Math.max(1e-3, e.dur) + (e.t <= 0.1 ? 0.1 : 0), 0, 1);
            L = e.de + (e.a - e.de) * ease(u);
          }
          return clamp(L, 0, 1);
        };
        const activo = (t) => {
          let v = 0;
          for (const e of evs) { const tr = t - e.t, D = Math.max(0.3, e.dur); if (tr < -1e-6 && !(e.t <= 0.1)) continue;
            v = Math.max(v, (e.t <= 0.1 ? 1 : ctx.suave(0, 0.4, tr)) * (1 - ctx.suave(D, D + 0.8, tr))); }
          return v;
        };
        const Hmax = H * Math.max(...evs.map((e) => Math.max(e.a, e.de)));
        const dz = clamp(Hmax / 9, 0.45, 3), NL = Math.max(1, Math.ceil(Hmax / dz - 1e-6));
        const bmax = clamp(dz * 0.85, 0.3, 1.8);
        // el perímetro en 4 lados (de la mitad de una esquina a la siguiente): NV puntos a la derecha, NU arriba, NV a la
        // izquierda y NU abajo; la cima es una rejilla (NU × NV, parche de Coons) cuyo borde son esos mismos puntos
        const NU = Math.max(6, Math.round(48 * A / (A + F))), NV = 48 - NU, NS = 2 * (NU + NV);
        const perim = (j, a, b, rc, o) => {
          const lx = 2 * (a - rc), ly = 2 * (b - rc), q = Math.PI * rc / 2, P = 2 * lx + 2 * ly + 4 * q;
          const cc = [-q / 2, ly + q / 2, ly + lx + 1.5 * q, 2 * ly + lx + 2.5 * q, P - q / 2], jj = ((j % NS) + NS) % NS;
          const [k, f] = jj < NV ? [0, jj / NV] : jj < NV + NU ? [1, (jj - NV) / NU] : jj < 2 * NV + NU ? [2, (jj - NV - NU) / NV] : [3, (jj - 2 * NV - NU) / NU];
          return rrect((cc[k] + (cc[k + 1] - cc[k]) * f) / P, a, b, rc, o);
        };
        const bj = (i, jj) => i === NU ? jj : jj === NV ? NV + (NU - i) : i === 0 ? NV + NU + (NV - jj) : (2 * NV + NU + i) % NS;
        // un punto de la rejilla de la cima a partir del borde (edge[j] = [u, v])
        const coons = (edge, i, jj) => {
          const x = i / NU, y = jj / NV, Bo = edge[bj(i, 0)], To = edge[bj(i, NV)], Le = edge[bj(0, jj)], Ri = edge[bj(NU, jj)];
          const P00 = edge[bj(0, 0)], P10 = edge[bj(NU, 0)], P01 = edge[bj(0, NV)], P11 = edge[bj(NU, NV)];
          const r = [0, 0];
          for (let d = 0; d < 2; d++) r[d] = (1 - y) * Bo[d] + y * To[d] + (1 - x) * Le[d] + x * Ri[d]
            - ((1 - x) * (1 - y) * P00[d] + x * (1 - y) * P10[d] + (1 - x) * y * P01[d] + x * y * P11[d]);
          return r;
        };
        const edge = Array.from({ length: NS }, () => [0, 0]);
        const semi = (z) => { const a = Math.max(A / 2 - KK * z, A * 0.14), b = Math.max(F / 2 - KK * z, F * 0.14); return [a, b, Math.min(a, b) * 0.32]; };
        const sK = clamp(Math.min(A, F) / 70, 0.8, 1.6);
        const lumpA = clamp(dz * 0.9, 0.35, 1.4);
        const lump = (u, v) => lumpA * (ruido(u, v, 4.5 * sK, 31) * 0.75 + ruido(u, v, 1.9 * sK, 32) * 0.4 - 0.45);
        // el borde de cada capa: bultos suaves a lo largo del perímetro (B[i + 1][j]; B[0] = el suelo, sin bultos)
        const B = [new Float32Array(NS)];
        for (let i = 0; i < NL; i++) {
          const b = new Float32Array(NS);
          for (let j = 0; j < NS; j++) { const f = j / 5 + 17.3 * i, f0 = Math.floor(f), w = f - f0, ws = w * w * (3 - 2 * w);
            const n = hz(f0 * 31 + i, 41) * (1 - ws) + hz((f0 + 1) * 31 + i, 41) * ws;
            b[j] = bmax * (0.15 + 0.85 * n * n); }
          B.push(b);
        }
        const out = [0, 0, 0, 0];
        // una pieza `pila` (MAQ.PILA.pilas[id]) dibuja su cuerpo: aquí se le fija la fracción y cae lo que llega sobre su cima
        const rec = (MAQ.PILA && MAQ.PILA.pilas && MAQ.PILA.pilas[pid]) || null;
        const cuerpo = !rec && e0.cuerpo !== false && !(MAQ.PIEZAS[e0.pieza_tipo] && MAQ.PIEZAS[e0.pieza_tipo].crece);
        const mats = [];
        let capas = null, nucleo = null, cima = null, alfombra = null, pie = null;
        if (cuerpo) {
          // ---- las capas: 3 anillos por capa (abajo, panza, arriba), NS puntos por anillo; colores horneados
          const acc = malla.nueva(), giro = [-0.45, 0.05, 0.6];
          for (let i = 0; i < NL; i++) {
            const base = hz(i, 51), alt = hz(i, 52);
            for (let rI = 0; rI < 3; rI++) for (let j = 0; j < NS; j++) {
              perim(j, A / 2, F / 2, Math.min(A, F) * 0.16, out);
              const nh = Math.cos(giro[rI] * 1.2), n = N3(out[2] * nh, out[3] * nh, Math.sin(giro[rI] * 1.2));
              const m = ruido(j, i * 7, 4, 53);
              const col = m < 0.55 ? elige(base, alt) : elige(hz(i * NS + j, 54), hz(i * NS + j, 55));
              c.copy(col).multiplyScalar(sombra(n[0], n[1], n[2]) * (0.88 + 0.2 * hz(i * NS + j, 56)) * (rI === 0 ? 0.82 : 1));
              acc.pos.push(0, 0, 0); acc.col.push(c.r, c.g, c.b);
            }
            const o = i * 3 * NS;
            for (let rI = 0; rI < 2; rI++) for (let j = 0; j < NS; j++) {
              const a0 = o + rI * NS + j, a1 = o + rI * NS + (j + 1) % NS, b0_ = a0 + NS, b1 = a1 + NS;
              acc.idx.push(a0, a1, b1, a0, b1, b0_);
            }
          }
          const mC = malla.poner(acc, malla.material(), 6);
          capas = { m: mC, P: mC.geometry.attributes.position };
          mats.push(mC.material);
          // ---- el núcleo (cierra rendijas entre capas)
          const an = malla.nueva(), cN = PAL[0][0].clone().multiplyScalar(0.8);
          for (let rI = 0; rI < 2; rI++) for (let j = 0; j < NS; j++) { an.pos.push(0, 0, 0); an.col.push(cN.r, cN.g, cN.b); }
          for (let j = 0; j < NS; j++) { const a0 = j, a1 = (j + 1) % NS; an.idx.push(a0, a1, a1 + NS, a0, a1 + NS, a0 + NS); }
          const mN = malla.poner(an, malla.material(), 5);
          nucleo = { m: mN, P: mN.geometry.attributes.position };
          mats.push(mN.material);
          // ---- la cima: una rejilla NU × NV con bultos; colores y luz horneados a media altura
          const ac = malla.nueva(), hRef = Hmax * 0.5, [sa, sb, src] = semi(hRef), RU = [];
          for (let j = 0; j < NS; j++) { perim(j, sa, sb, src, out); edge[j][0] = out[0]; edge[j][1] = out[1]; }
          for (let jj = 0; jj <= NV; jj++) for (let i = 0; i <= NU; i++) {
            const [u, v] = coons(edge, i, jj), w = ctx.suave(0, 0.14, Math.min(i / NU, 1 - i / NU, jj / NV, 1 - jj / NV)), d = 0.6;
            const gu = (lump(u + d, v) - lump(u - d, v)) / (2 * d) * w, gv = (lump(u, v + d) - lump(u, v - d)) / (2 * d) * w;
            const n = N3(-gu, -gv, 1), nl = Math.hypot(...n), g = jj * (NU + 1) + i;
            const col = elige(ruido(u, v, 3.2 * sK, 57), ruido(u, v, 2.1 * sK, 58));
            c.copy(col).multiplyScalar(sombra(n[0] / nl, n[1] / nl, n[2] / nl) * (0.94 + 0.1 * hz(g, 59)));
            ac.pos.push(0, 0, 0); ac.col.push(c.r, c.g, c.b);
            RU.push(w);
          }
          for (let jj = 0; jj < NV; jj++) for (let i = 0; i < NU; i++) {
            const a0 = jj * (NU + 1) + i, a1 = a0 + 1, b0_ = a0 + NU + 1, b1 = b0_ + 1;
            ac.idx.push(a0, a1, b1, a0, b1, b0_);
          }
          const mT = malla.poner(ac, malla.material(), 6);
          cima = { m: mT, P: mT.geometry.attributes.position, RU };
          mats.push(mT.material);
          // ---- la alfombra de la cima: objetos a h = 0 (la malla sube con la pila), en orden de aparición
          const [ta, tb] = semi(Hmax), nA = Math.round(clamp(ta * tb * 4 / (9 * sK * sK), 90, 380));
          const aa = malla.nueva(), cortes = [0];
          for (let i = 0; i < nA; i++) {
            const u = (2 * hz(i, 61) - 1) * ta * 0.74, v = (2 * hz(i, 62) - 1) * tb * 0.74;
            objeto(aa, E(u, v, lump(u, v) - 0.12 * sK), sK, hz, i + 1000, ro);
            cortes.push(aa.idx.length);
          }
          const mA = malla.poner(aa, malla.material(), 7);
          alfombra = { m: mA, cortes, n: nA, lleno: Math.min(1.6 * sK, Hmax * 0.35) };
          mats.push(mA.material);
          // ---- los restos al pie: salen mientras crece la primera capa
          const ap = malla.nueva(), cp = [0], nP = Math.round(clamp((A + F) * 0.9 / sK, 40, 160));
          for (let i = 0; i < nP; i++) {
            perim(Math.floor(hz(i, 71) * NS), A / 2, F / 2, Math.min(A, F) * 0.16, out);
            const d = (0.3 + 3.2 * Math.pow(hz(i, 72), 1.6)) * sK, u = out[0] + out[2] * d, v = out[1] + out[3] * d;
            const [x, y] = W(u, v), P = [x, ctx.suelo(x, y), -y];
            objeto(ap, P, sK * 0.85, hz, i + 5000, ro);
            cp.push(ap.idx.length);
          }
          const mP = malla.poner(ap, malla.material(), 6);
          pie = { m: mP, cortes: cp, n: nP };
          mats.push(mP.material);
        }

        // ---- lo que cae: racimos de 3–5 objetos (6 variantes), uno por malla
        const variantes = [];
        for (let k = 0; k < 6; k++) {
          const av = malla.nueva(), nO = 3 + Math.floor(hz(k, 81) * 3);
          for (let i = 0; i < nO; i++) {
            const g = (TAU * i) / nO + hz(k * 7 + i, 82), rr = (i ? 0.75 : 0) * sK * (0.6 + 0.5 * hz(k * 7 + i, 83));
            const Pc = [Math.cos(g) * rr * M, (i ? 0.15 * sK * hz(k * 7 + i, 84) : 0) * M, Math.sin(g) * rr * M];
            if (rec) rec.dibujar(av, 9000 + k * 13 + i, Pc, 1.6); else objeto(av, Pc, sK * 1.5, hz, 9000 + k * 13 + i, 0);
          }
          variantes.push(malla.geometria(av));
        }
        const matCae = malla.material(); matCae.uniforms.cTinte.value.copy(tonos.acento); mats.push(matCae);
        const caen = [];
        evs.forEach((e, ie) => {
          if (e.caida === false || e.a <= e.de) return;
          const D = Math.max(0.3, e.dur), gancho = e.t <= 0.1;
          const n = Math.round(clamp(D * 9 * Math.sqrt(clamp(A * F / 3000, 0.5, 3)), 8, 72));
          const ts0 = e.t + (gancho ? -0.9 : 0), ts1 = Math.max(ts0 + 0.2, e.t + D - 1.05);
          for (let j = 0; j < n; j++) {
            const q = j * 977 + ie * 53, ts = ts0 + (ts1 - ts0) * (j + hz(q, 91)) / n, tf = 0.8 + 0.3 * hz(q, 92), tl = ts + tf;
            const hl = nivelEn(tl) * H, [la, lb] = semi(hl);
            const u = (2 * hz(q, 93) - 1) * la * 0.8, v = (2 * hz(q, 94) - 1) * lb * 0.8;
            const Pl = rec ? rec.punto(Math.floor(hz(q, 93) * 4096), nivelEn(tl)) : E(u, v, hl + (cuerpo ? lump(u, v) : 0));
            const du = (hz(q, 97) - 0.5) * 3, dv = (hz(q, 98) - 0.5) * 3;
            const caidaM = clamp(Math.min(A, F) * 0.16, 7, 26) * (0.8 + 0.4 * hz(q, 95));
            const m = new THREE.Mesh(variantes[Math.floor(hz(q, 96) * 6) % 6], matCae);
            m.frustumCulled = false; m.renderOrder = 8; m.visible = false; scene.add(m);
            caen.push({ m, ts, tf, tl, Pl, L0: nivelEn(tl), dX: (du * ux - dv * uy) * M, dZ: -(du * uy + dv * ux) * M,
              caidaM, r0: TAU * hz(q, 99), giro: (hz(q, 100) - 0.5) * 7, ladeo: (hz(q, 101) - 0.5) * 1.2 });
          }
        });
        // ---- el polvo al asentarse: PUNTOS por objeto que caen
        const NPt = Math.max(1, caen.length * PUNTOS), gD = new THREE.BufferGeometry();
        gD.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NPt * 3), 3));
        gD.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(NPt), 1));
        const matD = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: 1.8 * sK * M }, cA: { value: cPolvo } }, transparent: true, depthWrite: false,
          vertexShader: "uniform float uPx, uTam; attribute float aA; varying float vA; void main(){ vA = aA; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aA > 0.003 ? clamp(uTam * uPx / max(1e-3, -mv.z) * (1.6 - aA), 2.0, 40.0) : 0.0; }",
          fragmentShader: SRGB + "uniform vec3 cA; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vA * 0.5 * (1.0 - smoothstep(0.3, 1.0, r)); if (a < 0.004) discard; gl_FragColor = vec4(srgb(cA), a); }" });
        const mD = new THREE.Points(gD, matD); mD.frustumCulled = false; mD.renderOrder = 9; scene.add(mD);

        return { pid, rec, evs, A, F, H, NL, dz, B, NS, NU, NV, perim, coons, edge, E, W, semi, lump, nivelEn, activo, capas, nucleo, cima, alfombra, pie, caen, gD, matD, mats, matCae, sK, hz, b0 };
      });
      return { pilas };
    },

    inicio(t, st, ctx) {
      if (!st) return;
      const N = ctx.cuadro.nivel = ctx.cuadro.nivel || {};
      for (const p of st.pilas) N[p.pid] = p.nivelEn(t);
    },

    aplicar(t, e, ctx, st) {
      // el nivel lo dejó `inicio` (función de todos los crecer de la pieza); aquí solo se confirma
      const N = ctx.cuadro.nivel = ctx.cuadro.nivel || {};
      if (N[e.pieza] === undefined) N[e.pieza] = e.de;
      // la pila de la pieza: se le fija la fracción de este cuadro desde el primer crecer (antes, la deja en su `inicio`)
      const p = st && st.pilas.find((x) => x.pid === e.pieza);
      if (p && p.rec && (t >= p.evs[0].t || p.evs[0].t <= 0.1)) p.rec.fijar(p.nivelEn(t));
    },

    en(t, st, ctx) {
      if (!st) return;
      const { clamp } = ctx, Ms = ctx.metros(1), out = [0, 0, 0, 0];
      for (const p of st.pilas) {
        const L = p.nivelEn(t), h = L * p.H, env = p.activo(t);
        const b = ctx.cuadro.brillo && ctx.cuadro.brillo[p.pid], k = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of p.mats) m.uniforms.uBrillo.value = 1 + 0.4 * k;
        if (p.capas) {
          const NS = p.NS, P = p.capas.P.array, NS3 = NS * 3, O = p.E(0, 0, 0);
          const iTop = Math.min(p.NL - 1, Math.floor(h / p.dz)), f = h <= 0 ? 0 : clamp((h - iTop * p.dz) / p.dz, 0, 1);
          const fac = [0.55, 1, 0.4], zr = [0, 0.55, 1];
          for (let i = 0; i < p.NL; i++) {
            const o = i * NS3 * 3;
            if (h <= 1e-4 || i > iTop) { for (let q = 0; q < NS3; q++) P.set(O, o + q * 3); continue; }
            const g = i < iTop ? 1 : f, z0 = i * p.dz, z1 = z0 + g * p.dz, Bp = p.B[i], Bi = p.B[i + 1];
            for (let rI = 0; rI < 3; rI++) {
              const z = z0 + (z1 - z0) * zr[rI], [sa, sb, src] = p.semi(z);
              for (let j = 0; j < NS; j++) {
                p.perim(j, sa, sb, src, out);
                const bb = Bp[j] * 0.4 * (1 - g) + Bi[j] * fac[rI] * g;
                P.set(p.E(out[0] + out[2] * bb, out[1] + out[3] * bb, z), o + (rI * NS + j) * 3);
              }
            }
          }
          p.capas.P.needsUpdate = true;
          // núcleo
          const PN = p.nucleo.P.array;
          for (let rI = 0; rI < 2; rI++) {
            const z = rI ? h : 0, [sa, sb, src] = p.semi(z);
            for (let j = 0; j < NS; j++) {
              p.perim(j, sa, sb, src, out);
              PN.set(h > 1e-4 ? p.E(out[0] - out[2] * 0.15, out[1] - out[3] * 0.15, z * 0.995) : O, (rI * NS + j) * 3);
            }
          }
          p.nucleo.P.needsUpdate = true;
          // la cima: el borde con los bultos de la capa de arriba; adentro, los bultos fijos
          const PT = p.cima.P.array, RU = p.cima.RU, [sa, sb, src] = p.semi(h), Bp = p.B[iTop], Bi = p.B[iTop + 1];
          const crece = clamp(h / Math.max(0.2, p.dz), 0, 1);
          for (let j = 0; j < NS; j++) {
            p.perim(j, sa, sb, src, out);
            const bb = Bp[j] * 0.4 * (1 - f) + Bi[j] * 0.4 * f;
            p.edge[j][0] = out[0] + out[2] * bb; p.edge[j][1] = out[1] + out[3] * bb;
          }
          for (let jj = 0; jj <= p.NV; jj++) for (let i = 0; i <= p.NU; i++) {
            const g = jj * (p.NU + 1) + i, [u, v] = p.coons(p.edge, i, jj);
            PT.set(h > 1e-4 ? p.E(u, v, h + p.lump(u, v) * RU[g] * crece) : O, g * 3);
          }
          p.cima.P.needsUpdate = true;
          // la alfombra sube con la cima y se va llenando al empezar; los restos del pie salen con la primera capa
          const A = p.alfombra, nA = h > 0.05 ? Math.floor(A.n * clamp(h / A.lleno, 0, 1)) : 0;
          A.m.position.y = h * Ms; A.m.geometry.setDrawRange(0, A.cortes[nA]); A.m.visible = nA > 0;
          const Pp = p.pie, nP = Math.floor(Pp.n * clamp(h / Math.max(0.3, p.dz), 0, 1));
          Pp.m.geometry.setDrawRange(0, Pp.cortes[nP]); Pp.m.visible = nP > 0;
        }
        // lo que cae
        p.matCae.uniforms.uTinte.value = 0.06 * env;
        const PD = p.gD.attributes.position.array, AD = p.gD.attributes.aA.array;
        AD.fill(0);
        p.caen.forEach((o, i) => {
          const m = o.m;
          const tapado = (L - o.L0) * p.H > 0.55 * p.sK;
          if (t < o.ts || tapado) { m.visible = false; return; }
          m.visible = true;
          let P, sy = 1, rot, lad;
          if (t < o.tl) {
            const q = (t - o.ts) / o.tf;
            P = [o.Pl[0] + o.dX * (1 - q), o.Pl[1] + o.caidaM * (1 - q * q) * Ms, o.Pl[2] + o.dZ * (1 - q)];
            rot = o.r0 + o.giro * q; lad = o.ladeo * (1 - q);
          } else {
            const s = t - o.tl; P = o.Pl;
            sy = 1 - 0.28 * Math.exp(-s * 9) * Math.sin(Math.min(Math.PI, s * 14)); rot = o.r0 + o.giro; lad = 0;
            if (s < 0.75) {
              const a = 1 - s / 0.75;
              for (let k = 0; k < PUNTOS; k++) {
                const g = TAU * (k / PUNTOS + p.hz(i * PUNTOS + k, 111) * 0.2), rr = (0.5 + 2.2 * Math.sqrt(s / 0.75)) * p.sK * (0.7 + 0.5 * p.hz(i * PUNTOS + k, 112));
                const Q = [o.Pl[0] + Math.cos(g) * rr * Ms, o.Pl[1] + (0.2 + 0.9 * p.sK * Math.sqrt(s / 0.75)) * Ms, o.Pl[2] + Math.sin(g) * rr * Ms];
                PD.set(Q, (i * PUNTOS + k) * 3); AD[i * PUNTOS + k] = a * a;
              }
            }
          }
          const ent = clamp((t - o.ts) / 0.12, 0, 1);
          m.position.set(P[0], P[1], P[2]); m.rotation.set(lad, rot, lad * 0.6); m.scale.set(ent * (2 - sy), ent * sy, ent * (2 - sy));
        });
        p.gD.attributes.position.needsUpdate = true; p.gD.attributes.aA.needsUpdate = true;
        p.matD.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
