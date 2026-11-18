// Evento «terremoto» (ficha: terremoto.json; reglas: scripts/maqueta_tipos/terremoto.py): la sacudida sobre un escenario
// con edificios, sin epicentro ni onda y sin mover la cámara.
// - TIEMBLA: el mundo entero se desplaza unos centímetros a 2–7 Hz (la cámara queda quieta: se mueve el suelo) y lo que
//   está en pie se mece más arriba que abajo. `previo`: un temblor corto y débil, una pausa, y luego el fuerte.
// - SE ROMPE POR PARTES: dentro de `radio_m` del centro, lo que está en pie (los vértices de las mallas de las piezas que
//   pasan de 0.7 m sobre el suelo) se reparte en celdas de 8 m; cada celda, por la semilla y `danos`, queda en pie, pierde
//   el techo y se inclina, o se cae: su parte alta baja a una línea de ruina quebrada y se vuelca hacia un lado. Las celdas
//   altas (torres, cúpulas) caen con más frecuencia; las de `lugares` caen siempre. Un edificio grande cae por pedazos.
// - LO QUE CAE: bloques, tejas y cascajo salen de la parte alta de cada celda caída, caen con gravedad y quedan en el suelo
//   sobre un montón de escombro que crece. Todo se queda en ruina hasta el final.
// - EL POLVO (`polvo`): bocanadas que suben de cada celda caída y del suelo, se abren con el viento, tapan el daño y se
//   adelgazan hasta una bruma que queda.
// - LA GENTE (`personas`): en pie o paseando en el borde del espacio abierto (`refugio`), corre hacia su centro al empezar
//   lo fuerte y se queda ahí mirando afuera.
// - PUBLICA ctx.cuadro.sismo[pieza] = {k, dx, dz, avance, danos, cx, cy, radio, caen}: una pieza que quiera romperse a su
//   manera (en su `en`, que corre después de los eventos) lo lee.
// Seek puro: cada cuadro escribe valores absolutos desde la copia que se toma al armar (nada se acumula); el azar es ctx.hash.
(function (MAQ) {
  const TAU = 2 * Math.PI, CELDA = 8, SOBRE = 0.7;
  const SRGB = "c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c));";
  const MAX_TROZOS = 1400, MAX_POLVO = 1400;

  // las mallas de lo que está en pie (de cualquier pieza): ni el cielo, ni las cintas, ni lo instanciado (gente, vehículos),
  // ni semillas en una caja diminuta (la lluvia), ni lo transparente que no brilla
  function candidatas(ctx) {
    const { THREE, scene } = ctx, out = [], I = new THREE.Matrix4();
    scene.updateMatrixWorld(true);
    scene.traverse((o) => {
      if (!(o.isMesh || o.isPoints || o.isLineSegments) || o.isInstancedMesh || o.userData.cielo || o.userData.terremoto) return;
      const m = o.material, g = o.geometry;
      if (!g || !g.attributes || !g.attributes.position || g.attributes.position.isInterleavedBufferAttribute) return;
      if (Array.isArray(m) || (m && m.uniforms && (m.uniforms.uAncho || m.uniforms.uS))) return;
      if (o.isPoints && !(m && m.blending === THREE.AdditiveBlending)) return;
      if (!o.matrixWorld.equals(I)) return;
      if (!g.boundingBox) g.computeBoundingBox();
      const b = g.boundingBox, dg = b.max.clone().sub(b.min).length();
      if (!(dg > 2)) return;
      out.push(o);
    });
    return out;
  }

  function copiaColor(C, idx) {
    const r = new Float32Array(idx.length * 3);
    for (let q = 0; q < idx.length; q++) { const j = idx[q]; r[q * 3] = C.array[j * 3]; r[q * 3 + 1] = C.array[j * 3 + 1]; r[q * 3 + 2] = C.array[j * 3 + 2]; }
    return r;
  }

  MAQ.EVENTOS.terremoto = {
    orden: 64,
    armar(ctx, lista) {
      const { THREE, scene, hash, tonos, lin, COL, ES, CFG, clamp } = ctx;
      const U = 1 / (ctx.unidad_m || 1), G = CELDA * U, noche = !!ES.noche;
      const alt = (x, y) => ctx.altura(x, y);
      const mallas = candidatas(ctx);
      const base = scene.position.clone();

      // ---------- los vértices de lo que está en pie, por evento (cada uno su centro y su radio) ----------
      const evs = lista.map((e, ne) => {
        const R2 = e.radio * e.radio, celdas = new Map(), grupos = [];
        for (const o of mallas) {
          const P = o.geometry.attributes.position, A = P.array, n = P.count;
          const idx = [], hv = [], gy = [], cel = [];
          for (let j = 0; j < n; j++) {
            const x = A[j * 3], yy = A[j * 3 + 1], y = -A[j * 3 + 2];
            const dx = x - e.cx, dy = y - e.cy;
            if (dx * dx + dy * dy > R2) continue;
            const g = alt(x, y), h = yy - g;
            if (!(h > SOBRE * U) || h > 400 * U) continue;
            const kx = Math.floor(x / G), ky = Math.floor(y / G), key = kx + "," + ky;
            let c = celdas.get(key);
            if (!c) { c = { i: celdas.size, kx, ky, hmax: 0, sx: 0, sy: 0, n: 0, g: 0, x0: x, x1: x, y0: y, y1: y }; celdas.set(key, c); }
            c.hmax = Math.max(c.hmax, h); c.sx += x; c.sy += y; c.n++; c.g += g;
            c.x0 = Math.min(c.x0, x); c.x1 = Math.max(c.x1, x); c.y0 = Math.min(c.y0, y); c.y1 = Math.max(c.y1, y);
            idx.push(j); hv.push(h); gy.push(g); cel.push(c.i);
          }
          if (!idx.length) continue;
          const C = o.geometry.attributes.color;
          grupos.push({ o, P, C: o.isMesh && C && C.itemSize === 3 ? C : null, idx: Int32Array.from(idx), hv: Float32Array.from(hv), gy: Float32Array.from(gy),
            cel: Int32Array.from(cel), ox: Float32Array.from(idx.map((j) => P.array[j * 3])), oy: Float32Array.from(idx.map((j) => P.array[j * 3 + 1])),
            oz: Float32Array.from(idx.map((j) => P.array[j * 3 + 2])), oc: C && C.itemSize === 3 && o.isMesh ? copiaColor(C, idx) : null });
        }
        // la huella de lo alto de cada celda (los vértices sobre el 60 % de su altura): un techo es ancho; un poste o una farola no
        const lista_c = [...celdas.values()].sort((p, q) => p.i - q.i);
        for (const c of lista_c) { c.tx0 = Infinity; c.tx1 = -Infinity; c.ty0 = Infinity; c.ty1 = -Infinity; }
        for (const gr of grupos) for (let q = 0; q < gr.idx.length; q++) {
          const c = lista_c[gr.cel[q]];
          if (gr.hv[q] < 0.6 * c.hmax) continue;
          const x = gr.ox[q], y = -gr.oz[q];
          c.tx0 = Math.min(c.tx0, x); c.tx1 = Math.max(c.tx1, x); c.ty0 = Math.min(c.ty0, y); c.ty1 = Math.max(c.ty1, y);
        }
        // el destino de cada celda: 0 en pie · 1 pierde el techo y se inclina · 2 se cae
        const D = Math.max(2, e.dur), s0 = e.previo ? 0.34 * D : 0, Df = D - s0;
        const CL = [...celdas.values()].sort((a, b) => a.i - b.i).map((c) => {
          const cx = c.sx / c.n, cy = c.sy / c.n, g = c.g / c.n, s = e.semilla * 31 + ne * 7;
          const h1 = hash(c.kx * 7919 + c.ky * 104729, 11 + s), h2 = hash(c.kx * 7919 + c.ky * 104729, 12 + s), h3 = hash(c.kx * 7919 + c.ky * 104729, 13 + s);
          const alta = clamp((c.hmax / U - 9) / 12, 0, 1);
          let forz = false;
          for (const q of e.caen || []) if (Math.hypot(q[0] - cx, q[1] - cy) < 1.6 * G) forz = true;
          const pc = clamp(e.danos * 0.62 + 0.22 * alta * e.danos, 0, 0.97), pt = clamp(e.danos * 1.15, 0, 1);
          // un poste, una farola o una banca no son un edificio: solo se mecen
          const obra = c.hmax >= 2.6 * U && Math.max(c.tx1 - c.tx0, c.ty1 - c.ty0) >= 3 * U;
          const fin = !obra ? 0 : forz ? 2 : h1 < pc ? 2 : h1 < pt ? 1 : 0;
          const tf = s0 + (forz ? 0.05 + 0.2 * h2 : 0.08 + 0.55 * h2) * Df, dc = (0.9 + 0.9 * h3) * Math.max(0.6, Math.min(1.4, Df / 6));
          const an = TAU * hash(c.kx * 7919 + c.ky * 104729, 14 + s);
          return { ...c, cx, cy, g, fin, tf, dc, dirx: Math.cos(an), diry: Math.sin(an), inc: (0.03 + 0.05 * h3) * (h2 < 0.5 ? 1 : -1) };
        });
        // el temblor: tres senos por eje, fase por semilla
        const ondas = [0, 1, 2].map((k) => ({ f: [2.3, 3.9, 6.7][k] * (0.9 + 0.2 * hash(k, 40 + e.semilla)), px: TAU * hash(k, 41 + e.semilla), pz: TAU * hash(k, 42 + e.semilla), w: [0.55, 0.32, 0.18][k] }));
        return { e, grupos, CL, D, s0, Df, ondas };
      });

      // ---------- material de lo que cae (instanciado, con la luz del estilo) ----------
      const az = (CFG.luz && CFG.luz.azimut || 135) * Math.PI / 180, el = (CFG.luz && CFG.luz.elevacion || 45) * Math.PI / 180;
      const uLuz = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)).normalize();
      const matT = new THREE.ShaderMaterial({ uniforms: { ...ctx.uComun(), uLuz: { value: uLuz }, uModo: { value: ES.modo || 0 } },
        vertexShader: `attribute vec3 color; uniform vec3 uLuz; uniform float uModo; varying vec3 vCol, vPos;
          void main(){ mat4 im = mat4(1.0);
          #ifdef USE_INSTANCING
            im = instanceMatrix;
          #endif
            vec4 w = modelMatrix * im * vec4(position, 1.0); vec3 n = normalize(mat3(modelMatrix * im) * normal); float lam = max(0.0, dot(n, uLuz));
            float s = (uModo > 1.5 && uModo < 2.5) ? (lam < 0.22 ? 0.62 : (lam < 0.62 ? 0.82 : 1.0)) : 0.5 + 0.62 * lam;
            vec3 c = color;
          #ifdef USE_INSTANCING_COLOR
            c *= instanceColor;
          #endif
            vCol = c * s; vPos = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
        fragmentShader: ctx.GLSL_COMUN + "varying vec3 vCol, vPos; void main(){ gl_FragColor = vec4(salida(niebla(vCol, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
      const blanca = (geo) => { const g = geo.toNonIndexed(); g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(g.attributes.position.count * 3).fill(1), 3)); return g; };
      const cMuro = tonos.muro.clone(), cTecho = tonos.techo.clone(), cSuelo = (tonos.suelo || tonos.muro).clone();
      const cPolvoT = cMuro.clone().lerp(cSuelo, 0.35);

      // ---------- los trozos (bloques y tejas) y el cascajo, y los montones ----------
      const trozos = [];
      for (const V of evs) for (const c of V.CL) {
        if (c.fin !== 2) continue;
        const k = Math.round(clamp(5 + 9 * c.hmax / (14 * U), 5, 16));
        for (let j = 0; j < k && trozos.length < MAX_TROZOS; j++) {
          const s = c.i * 37 + j * 3 + V.e.semilla * 101, h = (q) => hash(s, 60 + q);
          const teja = h(0) < 0.3, roca = !teja && h(1) < 0.45;
          const sx = (teja ? 0.7 + 0.6 * h(2) : 0.45 + 0.9 * h(2)) * U, sy = (teja ? 0.12 + 0.06 * h(3) : 0.3 + 0.5 * h(3)) * U, sz = (teja ? 0.5 + 0.4 * h(4) : 0.35 + 0.6 * h(4)) * U;
          const x0 = c.cx + (h(5) - 0.5) * G * 0.85, y0 = c.cy + (h(6) - 0.5) * G * 0.85, z0 = c.g + c.hmax * (0.45 + 0.55 * h(7));
          const vo = (0.6 + 2.6 * h(8)) * U, an = Math.atan2(c.diry, c.dirx) + (h(9) - 0.5) * 2.2;
          const vx = Math.cos(an) * vo, vy = Math.sin(an) * vo, vz0 = (h(10) * 1.6) * U, gr = 9.8 * U;
          const ts = V.e.t + c.tf + c.dc * (0.05 + 0.6 * h(11));
          // dónde cae: sobre el suelo y sobre el montón de su celda
          const Rm = G * 0.75, Hm = clamp(0.24 * c.hmax, 0.8 * U, 5 * U);
          let tl = (vz0 + Math.sqrt(vz0 * vz0 + 2 * gr * Math.max(0.1 * U, z0 - c.g))) / gr;
          let xl = x0 + vx * tl, yl = y0 + vy * tl;
          const dm = Math.hypot(xl - c.cx, yl - c.cy), zl = alt(xl, yl) + (dm < Rm ? Hm * (1 - dm / Rm) * 0.85 : 0) + sy * 0.5 + 0.15 * U * h(12);
          tl = (vz0 + Math.sqrt(vz0 * vz0 + 2 * gr * Math.max(0.05 * U, z0 - zl))) / gr; xl = x0 + vx * tl; yl = y0 + vy * tl;
          const col = (teja ? cTecho.clone() : cMuro.clone()).multiplyScalar(0.72 + 0.4 * h(13)).lerp(cPolvoT, 0.15 + 0.25 * h(14));
          trozos.push({ roca, x0, y0, z0, vx, vy, vz0, gr, ts, tl, zl, sx, sy, sz, col,
            ax: new THREE.Vector3(h(15) - 0.5, h(16) - 0.5, h(17) - 0.5).normalize(), w: (3 + 7 * h(18)) * (h(19) < 0.5 ? 1 : -1),
            yaw: TAU * h(20), tilt: (h(21) - 0.5) * (teja ? 0.5 : 0.35) });
        }
      }
      const nB = Math.max(1, trozos.filter((q) => !q.roca).length), nR = Math.max(1, trozos.filter((q) => q.roca).length);
      const mkIM = (geo, n, orden) => { const m = new THREE.InstancedMesh(blanca(geo), matT, n); m.frustumCulled = false; m.renderOrder = orden; m.userData.terremoto = true; scene.add(m); return m; };
      const imB = mkIM(new THREE.BoxGeometry(1, 1, 1), nB, 3), imR = mkIM(new THREE.IcosahedronGeometry(0.6, 0), nR, 3);
      const cero = new THREE.Matrix4().makeScale(0, 0, 0);
      let iB = 0, iR = 0;
      for (const q of trozos) { q.im = q.roca ? imR : imB; q.k = q.roca ? iR++ : iB++; q.im.setColorAt(q.k, q.col); }
      for (const m of [imB, imR]) { for (let i = 0; i < m.count; i++) m.setMatrixAt(i, cero); if (m.instanceColor) m.instanceColor.needsUpdate = true; }

      const montones = [];
      for (const V of evs) for (const c of V.CL) if (c.fin === 2) {
        const h = (q) => hash(c.i * 13 + V.e.semilla * 7, 90 + q);
        montones.push({ V, c, R: G * (0.6 + 0.25 * h(0)), H: clamp(0.24 * c.hmax, 0.8 * U, 5 * U), yaw: TAU * h(1), col: cMuro.clone().multiplyScalar(0.62 + 0.18 * h(2)).lerp(cPolvoT, 0.35) });
      }
      const imM = mkIM(new THREE.IcosahedronGeometry(1, 1), Math.max(1, montones.length), 2);
      montones.forEach((m, i) => imM.setColorAt(i, m.col));
      for (let i = 0; i < imM.count; i++) imM.setMatrixAt(i, cero);
      if (imM.instanceColor) imM.instanceColor.needsUpdate = true;

      // ---------- el polvo: bocanadas por celda caída y del suelo (posición y tamaño en el shader, de uTs) ----------
      let polvo = null;
      const puf = [];
      for (const V of evs) {
        if (!V.e.polvo) continue;
        for (const c of V.CL) {
          if (c.fin === 0) continue;
          const k = c.fin === 2 ? 15 : 4;
          for (let j = 0; j < k && puf.length < MAX_POLVO; j++) {
            const h = (q) => hash(c.i * 17 + j * 5 + V.e.semilla * 13, 120 + q), an = TAU * h(0);
            puf.push([c.cx + (h(1) - 0.5) * G * 0.7, c.g, c.cy + (h(2) - 0.5) * G * 0.7, V.e.t + c.tf + c.dc * (0.15 + 0.5 * h(3)) + 0.1 * j,
              c.hmax * (c.fin === 2 ? 1 : 0.5), h(4), h(5), Math.cos(an), Math.sin(an)]);
          }
        }
        for (let j = 0; j < 28 && puf.length < MAX_POLVO; j++) {     // el polvo que levanta el suelo al sacudirse
          const h = (q) => hash(j * 23 + V.e.semilla * 3, 150 + q), r = V.e.radio * Math.sqrt(h(0)) * 0.9, an = TAU * h(1);
          const x = V.e.cx + Math.cos(an) * r, y = V.e.cy + Math.sin(an) * r;
          puf.push([x, alt(x, y), y, V.e.t + V.s0 + 0.35 * V.Df * h(2), 7 * U, 0.6 + 0.4 * h(3), h(4), Math.cos(an), Math.sin(an)]);
        }
      }
      const uTs = { value: 0 }, uPx = { value: 1 };
      if (puf.length) {
        const g = new THREE.BufferGeometry(), P = new Float32Array(puf.length * 3), A = new Float32Array(puf.length * 4), Dd = new Float32Array(puf.length * 2);
        puf.forEach((q, i) => { P.set([q[0], q[1], -q[2]], i * 3); A.set([q[3], q[4], q[5], q[6]], i * 4); Dd.set([q[7], -q[8]], i * 2); });
        g.setAttribute("position", new THREE.BufferAttribute(P, 3)); g.setAttribute("aP", new THREE.BufferAttribute(A, 4)); g.setAttribute("aD", new THREE.BufferAttribute(Dd, 2));
        const vi = TAU * hash(lista.length, 170);
        const cP = cPolvoT.clone().lerp(cSuelo, 0.25).multiplyScalar(noche ? 0.42 : 1.08), cP2 = cP.clone().multiplyScalar(noche ? 0.75 : 0.82);
        polvo = new THREE.ShaderMaterial({ uniforms: { uTs, uPx, uU: { value: U }, uV: { value: new THREE.Vector2(Math.cos(vi), -Math.sin(vi)) }, cA: { value: cP }, cB: { value: cP2 }, uK: { value: noche ? 0.7 : 0.95 } },
          transparent: true, depthWrite: false, depthTest: true,
          vertexShader: `uniform float uTs, uPx, uU; uniform vec2 uV; attribute vec4 aP; attribute vec2 aD; varying float vA, vS;
            void main(){ float a = uTs - aP.x; vS = aP.z;
              if (a < 0.0) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); gl_PointSize = 0.0; vA = 0.0; return; }
              float hm = aP.y, e1 = 1.0 - exp(-a / 1.6), e2 = 1.0 - exp(-a / 1.3);
              float sube = e1 * hm * (0.55 + 0.6 * aP.z) + a * 0.3 * uU + hm * 0.2 * aP.w;
              float abre = e2 * (3.0 + 7.0 * aP.w) * uU;
              vec3 p = position + vec3(aD.x * abre + uV.x * a * 0.55 * uU, sube, aD.y * abre + uV.y * a * 0.55 * uU);
              vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv;
              float tam = (4.0 + 15.0 * (1.0 - exp(-a / 1.9))) * uU * (0.65 + 0.6 * aP.z) * sqrt(clamp(hm / (12.0 * uU), 0.4, 2.2));
              gl_PointSize = clamp(tam * uPx / max(1e-3, -mv.z), 1.0, 480.0);
              vA = smoothstep(0.0, 0.3, a) * (0.72 * exp(-a / 4.2) + 0.13 * exp(-a / 18.0)); }`,
          fragmentShader: `uniform vec3 cA, cB; uniform float uK; varying float vA, vS;
            void main(){ vec2 d = gl_PointCoord - 0.5; float r = length(d) * 2.0; if (r > 1.0) discard;
              float a = uK * vA * exp(-r * r * 2.6) * (0.85 + 0.15 * sin(vS * 40.0 + d.x * 9.0 + d.y * 7.0)); if (a < 0.004) discard;
              vec3 c = mix(cB, cA, clamp(0.5 - d.y * 1.2, 0.0, 1.0)); ${SRGB} gl_FragColor = vec4(c, a); }` });
        const m = new THREE.Points(g, polvo); m.frustumCulled = false; m.renderOrder = 9; m.userData.terremoto = true; scene.add(m);
      }

      // ---------- la gente: en el borde del espacio abierto; corre a su centro con lo fuerte ----------
      const gente = [];
      for (const V of evs) {
        const n = Math.max(0, Math.min(40, V.e.personas | 0));
        for (let i = 0; i < n; i++) {
          const h = (q) => hash(i * 29 + V.e.semilla * 11, 200 + q);
          const r0 = V.e.rr * (0.74 + 0.24 * h(0)), th0 = TAU * (i + 0.6 * h(1)) / n;
          const pasea = h(2) < 0.35, vp = pasea ? (0.45 + 0.35 * h(3)) * U * (h(4) < 0.5 ? 1 : -1) : 0;
          const tc = V.e.t + V.s0 + 0.45 + 1.5 * h(5), vc = (2.6 + 1.4 * h(6)) * U, r1 = V.e.rr * (0.08 + 0.32 * h(7)), dth = (h(8) - 0.5) * 0.5;
          gente.push({ V, r0, th0, pasea, vp, tc, vc, r1, dth, mira: TAU * h(9) });
        }
      }
      const flP = gente.length ? ctx.flota("persona", gente.length, { tamano: 1, orden: 6, semilla: 17 }) : null;
      const uPxV = () => ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      return { scene, evs, base, trozos, imB, imR, imM, montones, polvo, uTs, uPx, gente, flP, uPxV, cPolvo: cPolvoT, activos: [], cero, sucio: new Set() };
    },

    inicio(t, st) {
      if (!st) return;
      st.scene.position.copy(st.base);
      st.activos.length = 0;
    },

    aplicar(t, e, ctx, st) {
      if (!st) return;
      const V = st.evs.find((v) => v.e === e) || st.evs.find((v) => v.e.t === e.t && v.e.cx === e.cx && v.e.cy === e.cy);
      if (!V || t < e.t) return;
      const { suave, clamp } = ctx, tr = t - e.t, D = V.D, s0 = V.s0, U = 1 / (ctx.unidad_m || 1);
      // la envolvente: (previo) un temblor débil y corto · lo fuerte: sube, se sostiene y se apaga al final de `dur`
      let env = 0;
      if (e.previo) env = 0.3 * suave(0, 0.03 * D, tr) * (1 - suave(0.1 * D, 0.17 * D, tr));
      env = Math.max(env, suave(s0, s0 + Math.max(0.35, 0.08 * V.Df), tr) * (1 - suave(s0 + 0.62 * V.Df, D, tr)));
      env *= clamp(e.intensidad, 0, 1);
      const dist = (ctx.cuadro && ctx.cuadro.dist) || 300 * U, amp = env * clamp(0.0042 * dist, 0.06 * U, 5 * U);
      let sx = 0, sz = 0, sy = 0;
      for (const o of V.ondas) { sx += o.w * Math.sin(TAU * o.f * tr + o.px); sz += o.w * Math.sin(TAU * o.f * 1.07 * tr + o.pz); sy += o.w * Math.sin(TAU * o.f * 1.3 * tr + o.px + o.pz); }
      const dx = amp * sx, dz = amp * sz;
      ctx.scene.position.x += dx; ctx.scene.position.z += dz; ctx.scene.position.y += 0.25 * amp * sy;
      st.activos.push({ V, tr, env, dx, dz });
      ctx.cuadro.sismo = ctx.cuadro.sismo || {};
      ctx.cuadro.sismo[e.pieza] = { k: env, dx, dz: -dz, avance: clamp(tr / D, 0, 1), danos: e.danos, cx: e.cx, cy: e.cy, radio: e.radio, caen: e.caen || [] };
    },

    en(t, st, ctx) {
      if (!st) return;
      const { clamp } = ctx, U = 1 / (ctx.unidad_m || 1), M4 = st.M4 || (st.M4 = new ctx.THREE.Matrix4()), Q = st.Q || (st.Q = new ctx.THREE.Quaternion()),
        Q2 = st.Q2 || (st.Q2 = new ctx.THREE.Quaternion()), P = st.P || (st.P = new ctx.THREE.Vector3()), S = st.S || (st.S = new ctx.THREE.Vector3()),
        Yv = st.Yv || (st.Yv = new ctx.THREE.Vector3(0, 1, 0)), Xv = st.Xv || (st.Xv = new ctx.THREE.Vector3(1, 0, 0));
      // ---------- lo que está en pie: valores absolutos desde la copia (si nada pasa, la copia tal cual) ----------
      for (const V of st.evs) {
        const A = st.activos.find((a) => a.V === V), tr = A ? A.tr : -1;
        const sway = A ? A.env : 0, swx = A ? A.dx : 0, swz = A ? A.dz : 0;
        for (const g of V.grupos) {
          if (!A && !st.sucio.has(g)) continue;
          const PA = g.P.array, CA = g.C ? g.C.array : null;
          for (let q = 0; q < g.idx.length; q++) {
            const j = g.idx[q];
            let x = g.ox[q], y = g.oy[q], z = g.oz[q];
            if (A) {
              const c = V.CL[g.cel[q]], h = g.hv[q], hm = Math.max(c.hmax, 1e-3);
              // se mece: más arriba que abajo, contra el suelo que se mueve
              const f = Math.pow(h / hm, 1.4) * Math.min(1, h / (14 * U)) * 0.9;
              if (sway > 0) { x -= swx * f; z -= swz * f; }
              let e = 0;
              if (c.fin && tr > c.tf) { const u = clamp((tr - c.tf) / c.dc, 0, 1); e = u * u * (3 - 2 * u); }
              if (e > 0) {
                const qx = Math.round(g.ox[q] / (0.25 * U)), qz = Math.round(g.oz[q] / (0.25 * U)), hq = ctx.hash(qx * 7919 + qz * 104729, 31);
                if (c.fin === 2) {
                  const rh = hm * (0.1 + 0.34 * hq), sob = Math.max(0, h - rh);
                  y -= e * sob * (0.82 + 0.18 * hq);
                  const vu = e * sob * (0.32 + 0.25 * hq);
                  x += c.dirx * vu; z -= c.diry * vu;
                } else {
                  const cr = 0.66 * hm, sob = Math.max(0, h - cr);
                  y -= e * sob * (0.55 + 0.35 * hq);
                  x += c.dirx * c.inc * h * e; z -= c.diry * c.inc * h * e;
                }
                if (CA) {
                  const k = (c.fin === 2 ? 0.5 : 0.22) * e, cp = st.cPolvo;
                  CA[j * 3] = g.oc[q * 3] + (cp.r - g.oc[q * 3]) * k; CA[j * 3 + 1] = g.oc[q * 3 + 1] + (cp.g - g.oc[q * 3 + 1]) * k; CA[j * 3 + 2] = g.oc[q * 3 + 2] + (cp.b - g.oc[q * 3 + 2]) * k;
                }
              } else if (CA) { CA[j * 3] = g.oc[q * 3]; CA[j * 3 + 1] = g.oc[q * 3 + 1]; CA[j * 3 + 2] = g.oc[q * 3 + 2]; }
            } else if (CA) { CA[j * 3] = g.oc[q * 3]; CA[j * 3 + 1] = g.oc[q * 3 + 1]; CA[j * 3 + 2] = g.oc[q * 3 + 2]; }
            PA[j * 3] = x; PA[j * 3 + 1] = y; PA[j * 3 + 2] = z;
          }
          g.P.needsUpdate = true; if (g.C) g.C.needsUpdate = true;
          if (A) st.sucio.add(g); else st.sucio.delete(g);
        }
      }
      // ---------- los trozos: caen con gravedad y se quedan ----------
      for (const q of st.trozos) {
        const a = t - q.ts;
        if (a < 0) { q.im.setMatrixAt(q.k, st.cero); continue; }
        const tau = Math.min(a, q.tl), cae = a < q.tl;
        P.set(q.x0 + q.vx * tau, cae ? q.z0 + q.vz0 * tau - 0.5 * q.gr * tau * tau : q.zl, -(q.y0 + q.vy * tau));
        Q.setFromAxisAngle(Yv, q.yaw); Q2.setFromAxisAngle(Xv, q.tilt); Q.multiply(Q2);
        if (cae) { Q2.setFromAxisAngle(q.ax, q.w * tau); Q.multiply(Q2); }
        S.set(q.sx, q.sy, q.sz);
        M4.compose(P, Q, S); q.im.setMatrixAt(q.k, M4);
      }
      st.imB.instanceMatrix.needsUpdate = true; st.imR.instanceMatrix.needsUpdate = true;
      // ---------- los montones de escombro: crecen con la caída ----------
      st.montones.forEach((m, i) => {
        const tr = t - m.V.e.t - m.c.tf;
        const u = clamp((tr - 0.2 * m.c.dc) / (m.c.dc * 1.3), 0, 1), e = u * u * (3 - 2 * u);
        if (e <= 0) { st.imM.setMatrixAt(i, st.cero); return; }
        P.set(m.c.cx, m.c.g - 0.12 * m.H, -m.c.cy); Q.setFromAxisAngle(Yv, m.yaw); S.set(m.R * (0.6 + 0.4 * e), m.H * e, m.R * (0.6 + 0.4 * e) * 0.85);
        M4.compose(P, Q, S); st.imM.setMatrixAt(i, M4);
      });
      st.imM.instanceMatrix.needsUpdate = true;
      // ---------- el polvo ----------
      if (st.polvo) { st.uTs.value = t; st.uPx.value = st.uPxV(); }
      // ---------- la gente ----------
      if (st.flP) {
        st.gente.forEach((p, i) => {
          const e = p.V.e, rx = e.rx, ry = e.ry;
          const thA = (tt) => p.th0 + (p.pasea ? p.vp * tt / p.r0 : 0);
          let x, y, dx, dy, vel;
          if (t < p.tc) {
            const th = thA(t); x = rx + Math.cos(th) * p.r0; y = ry + Math.sin(th) * p.r0;
            if (p.pasea) { const sg = Math.sign(p.vp); dx = -Math.sin(th) * sg; dy = Math.cos(th) * sg; vel = Math.abs(p.vp) / U; }
            else { dx = Math.cos(p.mira); dy = Math.sin(p.mira); vel = 0; }
          } else {
            const th = thA(p.tc), x0 = rx + Math.cos(th) * p.r0, y0 = ry + Math.sin(th) * p.r0, th1 = th + p.dth;
            const x1 = rx + Math.cos(th1) * p.r1, y1 = ry + Math.sin(th1) * p.r1, L = Math.hypot(x1 - x0, y1 - y0) || 1e-6, T = L / p.vc;
            const u = Math.min(1, (t - p.tc) / T);
            x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * u;
            if (u < 1) { dx = (x1 - x0) / L; dy = (y1 - y0) / L; vel = p.vc / U; }
            else { dx = -(x1 - x0) / L; dy = -(y1 - y0) / L; vel = 0; }
          }
          st.flP.poner(i, x, y, dx, dy, 1, 0, vel);
        });
        st.flP.listo();
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
