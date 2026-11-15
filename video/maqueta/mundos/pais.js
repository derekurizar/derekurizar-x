// Mundo «pais» (ficha: pais.json): el relieve nacional de un set de geodatos (design/sets3d/<set>/relieve.png), en km.
// Es el relieve que el núcleo dibujaba antes de la Fase 1, movido tal cual: malla + textura de normales, máscara del país,
// el shader de la superficie (fallas, rupturas, ondas: los canales que llenan piezas/falla.js, eventos/ruptura.js y
// eventos/onda.js) y, en el estilo voxel, las columnas. Unidad de la escena: 1 km (x = este, y = norte).
// Contrato de un mundo: referencias/diseno/maqueta3d.md («Mundos»): cargar(ctx) → estado · armar(ctx, estado) · en(t, estado, ctx);
// publica en ctx: altura(x, y), geo(lon, lat), y lo propio de su superficie.
(function (MAQ) {
  MAQ.MUNDOS.pais = {
    async cargar(ctx) {
      const { THREE, M, EXAG, COL, CFG, ES, lin, clamp, suave, hash, renderer, scene, uComun, GLSL_COMUN } = ctx;
      const R = M.relieve, P = R.proyeccion, NR = 4, NC = 56, NO = 4;
      // ---------- relieve: imagen → alturas ----------
      const RW = R.ancho, RH = R.alto, CAJA = R.caja;
      const X0 = (CAJA.lon_min - P.lon0) * P.km_lon, X1 = (CAJA.lon_max - P.lon0) * P.km_lon;
      const Y0 = (CAJA.lat_min - P.lat0) * P.km_lat, Y1 = (CAJA.lat_max - P.lat0) * P.km_lat;
      const CX = (X1 - X0) / RW, CY = (Y1 - Y0) / RH;                  // km por celda
      let ALT = null;                                                  // metros reales, fila 0 = norte
      async function cargarRelieve() {
        const img = new Image(); img.src = "assets/set/" + R.archivo; await img.decode();
        const c = document.createElement("canvas"); c.width = RW; c.height = RH;
        const g = c.getContext("2d", { willReadFrequently: true, colorSpace: "srgb" });
        g.drawImage(img, 0, 0);
        const d = g.getImageData(0, 0, RW, RH).data;
        ALT = new Float32Array(RW * RH);
        for (let i = 0; i < RW * RH; i++) ALT[i] = d[4 * i] * 256 + d[4 * i + 1] - R.desfase_m;
        for (const [i, j, v] of R.muestras) if (ALT[j * RW + i] !== v) console.error("relieve: la imagen se leyó con conversión de color (muestra " + i + "," + j + ")");
      }
      // altura de la maqueta (km, ya exagerada) en un punto del mundo; el mar queda en 0
      function altura(x, y) {
        const fi = clamp((x - X0) / CX - 0.5, 0, RW - 1.001), fj = clamp((Y1 - y) / CY - 0.5, 0, RH - 1.001);
        const i = Math.floor(fi), j = Math.floor(fj), u = fi - i, v = fj - j, k = j * RW + i;
        const h = (ALT[k] * (1 - u) + ALT[k + 1] * u) * (1 - v) + (ALT[k + RW] * (1 - u) + ALT[k + RW + 1] * u) * v;
        return Math.max(0, h) / 1000 * EXAG;
      }

      const GLSL_RUPTURA = `
        uniform vec4 uRup[${NR}]; uniform vec2 uRupT[${NR}];   // (s0, km hacia −s, km hacia +s, dur) · (segundos desde que empezó, pieza)
        float encendida(float s, float pieza, out float calor) {
          float L = 0.0; calor = 0.0;
          for (int i = 0; i < ${NR}; i++) {
            float tr = uRupT[i].x;
            if (abs(uRupT[i].y - pieza) > 0.25 || tr <= 0.0) continue;
            float d = s - uRup[i].x, ad = abs(d);
            float alc = d < 0.0 ? uRup[i].y : uRup[i].z;
            float frente = alc * min(tr / uRup[i].w, 1.0);          // cada frente avanza a su ritmo; los dos llegan en dur
            float l = alc > 0.0 ? 1.0 - smoothstep(frente - 1.2, frente + 0.4, ad) : 0.0;
            float c = exp(-max(tr - ad / max(alc, 0.001) * uRup[i].w, 0.0) / 1.4);   // recién roto: más caliente
            L = max(L, l); calor = max(calor, l * c);
          }
          return L;
        }`;
      const uRuptura = { uRup: { value: Array.from({ length: NR }, () => new THREE.Vector4()) }, uRupT: { value: Array.from({ length: NR }, () => new THREE.Vector2(0, -1)) } };

      // ---------- el relieve ----------
      let matRelieve = null, cubos = null;
      const uRelieve = {
        ...uComun(), ...uRuptura,
        tNormal: { value: null }, tPais: { value: null }, uModo: { value: ES.modo },
        cMar: { value: lin(COL.mar) }, cMarHondo: { value: lin(COL.mar_hondo) }, cExterior: { value: lin(COL.exterior) }, uMarRel: { value: CFG.mar.relieve }, uMarLuz: { value: CFG.mar.luz }, cBaja: { value: lin(COL.tierra_baja) }, cMedia: { value: lin(COL.tierra_media) }, cAlta: { value: lin(COL.tierra_alta) },
        cLuz: { value: lin(COL.luz) }, cAmb: { value: lin(COL.ambiente) }, cOnda: { value: lin(COL.onda) },
        cPieza: { value: [0, 1, 2, 3].map(() => lin(COL.secundario).multiplyScalar(CFG.falla.secundaria)) },   // piezas/falla.js pone el acento en la suya
        cLinea: { value: lin(COL.linea) }, cCosta: { value: lin(COL.costa) },
        uLuzDir: { value: new THREE.Vector3() }, uLuzK: { value: CFG.luz.fuerza }, uAmbK: { value: CFG.luz.ambiente }, uRel: { value: CFG.luz.relieve },
        uFuera: { value: CFG.fuera }, uCosta: { value: CFG.costa }, uAltMax: { value: R.max_m / 1000 * EXAG }, uExag: { value: EXAG },
        uCaja: { value: new THREE.Vector4(X0, X1, -Y1, -Y0) }, uBorde: { value: CFG.borde_km },
        uCad: { value: Array.from({ length: NC }, () => new THREE.Vector4()) }, uCadN: { value: 0 },
        uBrillo: { value: [1, 1, 1, 1] }, uGlow: { value: CFG.falla.suelo }, uSigma: { value: CFG.falla.suelo_km },
        uOnda: { value: Array.from({ length: NO }, () => new THREE.Vector4(0, 0, 0, 0)) }, uOndaPieza: { value: [-1, -1, -1, -1] },   // en reposo: w = 0 (sin onda)
      };
      { const az = CFG.luz.azimut * Math.PI / 180, el = CFG.luz.elevacion * Math.PI / 180;   // de dónde viene la luz (0 = norte, 90 = este)
        uRelieve.uLuzDir.value.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)); }
      // uCad y cPieza (las fallas), uRup* (las rupturas), uOnda* (las ondas) y uBrillo (resaltar): canales de la SUPERFICIE que
      // llenan los módulos (piezas/falla.js, eventos/ruptura.js, eventos/onda.js); el shader del relieve los dibuja

      const FRAG_RELIEVE = GLSL_COMUN + GLSL_RUPTURA + `
        uniform sampler2D tNormal, tPais; uniform int uModo;
        uniform vec3 cMar, cMarHondo, cExterior, cBaja, cMedia, cAlta, cLuz, cAmb, cOnda, cLinea, cCosta, uLuzDir; uniform vec3 cPieza[4]; uniform float uMarRel, uMarLuz;
        uniform float uLuzK, uAmbK, uRel, uFuera, uCosta, uAltMax, uExag, uBorde, uGlow, uSigma;
        uniform vec4 uCaja; uniform vec4 uCad[${NC}]; uniform int uCadN; uniform float uBrillo[4];
        uniform vec4 uOnda[${NO}]; uniform float uOndaPieza[${NO}];
        varying vec2 vUv; varying vec3 vPos; varying float vAlt;
        void main() {
          vec4 tn = texture2D(tNormal, vUv);
          vec2 nh = tn.xy * 2.0 - 1.0; vec3 n0 = vec3(nh.x, sqrt(max(1.0 - dot(nh, nh), 0.0)), nh.y);   // textura: normal (x, z), fondo del mar, tierra
          float tierra = smoothstep(0.35, 0.65, tn.a);
          vec3 n = normalize(vec3(n0.x * uRel, n0.y, n0.z * uRel));
          // el mar: más claro en lo somero, más oscuro en lo hondo, con el relieve del fondo apenas insinuado
          vec3 nm = normalize(vec3(n0.x * uRel * uMarRel, n0.y, n0.z * uRel * uMarRel));
          float sm = smoothstep(-0.35, 1.0, dot(nm, uLuzDir));
          vec3 mar = mix(cMar, cMarHondo, smoothstep(0.0, 0.62, tn.b)) * mix(1.0, 0.45 + 1.1 * sm * sm, uMarLuz);
          float pais = texture2D(tPais, vUv).r;
          float hN = clamp(vAlt / uAltMax, 0.0, 1.0);
          float metros = vAlt / uExag * 1000.0;
          float lam = max(dot(n, uLuzDir), 0.0);
          vec3 base = mix(cBaja, cMedia, smoothstep(0.0, 0.38, hN)); base = mix(base, cAlta, smoothstep(0.38, 1.0, hN));
          float costa = (1.0 - abs(tn.a * 2.0 - 1.0)) * uCosta;
          vec3 col;
          if (uModo == 1) {                       // noche: luz rasante tenue, mar más oscuro, el país un poco más claro que lo de afuera
            float sl = smoothstep(-0.35, 1.0, dot(n, uLuzDir));
            col = base * (cAmb * uAmbK + cLuz * uLuzK * sl * sl);
            float gris = dot(col, vec3(0.3, 0.5, 0.2));
            col = mix(mix(vec3(gris), col, 0.45) * uFuera, col, pais);
            col = mix(mar, col, tierra);
            col += cCosta * costa * mix(0.4, 1.0, pais);
          } else if (uModo == 2) {                // contorno: tres tonos, bandas de altura y línea de tinta
            float q = lam < 0.22 ? 0.56 : (lam < 0.62 ? 0.8 : 1.0);
            float banda = floor(metros / 600.0);
            vec3 b = mix(cBaja, cMedia, clamp(banda / 3.0, 0.0, 1.0)); b = mix(b, cAlta, clamp((banda - 3.0) / 3.0, 0.0, 1.0));
            col = mix(mix(cMar, cMarHondo, step(0.25, tn.b) * 0.5 + step(0.5, tn.b) * 0.5), b * q, step(0.5, tn.a));
            col = mix(col, mix(col, cMar, 0.35), (1.0 - pais) * uFuera);
            float fb = metros / 600.0; float lc = abs(fract(fb - 0.5) - 0.5) / max(fwidth(fb), 1e-5);
            float tinta = (1.0 - smoothstep(0.7, 1.6, lc)) * tierra * 0.55;
            float fc = abs(tn.a - 0.5) / max(fwidth(tn.a), 1e-5);
            tinta = max(tinta, 1.0 - smoothstep(1.0, 2.2, fc));
            col = mix(col, cLinea, tinta);
          } else if (uModo == 4) {                // plano: caras del color del fondo, curvas de nivel y retícula en línea clara
            col = mix(mix(cMar, cMarHondo, smoothstep(0.0, 0.62, tn.b)), cBaja, tierra);
            { float fd = tn.b * 8.0; float ld = abs(fract(fd - 0.5) - 0.5) / max(fwidth(fd), 1e-5); col = mix(col, cLinea, (1.0 - smoothstep(0.5, 1.5, ld)) * (1.0 - tierra) * 0.12); }
            float fb = metros / 400.0; float lc = abs(fract(fb - 0.5) - 0.5) / max(fwidth(fb), 1e-5);
            float l = (1.0 - smoothstep(0.5, 1.5, lc)) * tierra * step(40.0, metros) * 0.5;
            vec2 gr = vUv * vec2(10.4, 9.6); vec2 fg = abs(fract(gr - 0.5) - 0.5) / max(fwidth(gr), vec2(1e-5));
            l = max(l, (1.0 - smoothstep(0.5, 1.4, min(fg.x, fg.y))) * 0.28);
            float fc = abs(tn.a - 0.5) / max(fwidth(tn.a), 1e-5);
            l = max(l, (1.0 - smoothstep(0.8, 2.0, fc)) * 0.9);
            col = mix(col, cLinea, l * mix(uFuera, 1.0, pais));
          } else {                                // color: tinta hipsométrica con sol
            col = base * (cAmb * uAmbK + cLuz * uLuzK * lam);
            col = mix(mar, col, tierra);
            col += cCosta * costa;
            col = mix(mix(col, cFondo, (1.0 - uFuera) * tierra), col, pais);
          }
          // la falla encendida alumbra el suelo; las ondas son anillos que crecen
          vec2 p = vPos.xz; float glow = 0.0, cal = 0.0; vec3 cg = cPieza[0]; float dP[4]; dP[0] = 1e6; dP[1] = 1e6; dP[2] = 1e6; dP[3] = 1e6;
          for (int i = 0; i < ${NC - 1}; i++) {
            if (i >= uCadN - 1) break;
            vec4 a = uCad[i], b = uCad[i + 1];
            float pa = floor(a.w);
            if (pa != floor(b.w) || fract(a.w) > 0.25) continue;
            vec2 ab = b.xy - a.xy; float h = clamp(dot(p - a.xy, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
            float d = length(p - (a.xy + ab * h));
            int ip = int(pa); if (ip == 0) dP[0] = min(dP[0], d); else if (ip == 1) dP[1] = min(dP[1], d); else if (ip == 2) dP[2] = min(dP[2], d); else dP[3] = min(dP[3], d);
            float ds = max(b.z - a.z, 1e-4), br = ip == 0 ? uBrillo[0] : ip == 1 ? uBrillo[1] : ip == 2 ? uBrillo[2] : uBrillo[3];
            for (int j = 0; j < ${NR}; j++) {
              float tr = uRupT[j].x;
              if (abs(uRupT[j].y - pa) > 0.25 || tr <= 0.0) continue;
              float u = min(tr / uRup[j].w, 1.0), lo = uRup[j].x - uRup[j].y * u, hi = uRup[j].x + uRup[j].z * u;
              if (hi < a.z || lo > b.z) continue;
              float hh = clamp(h, clamp((lo - a.z) / ds, 0.0, 1.0), clamp((hi - a.z) / ds, 0.0, 1.0));
              float dl = length(p - (a.xy + ab * hh)), sl = mix(a.z, b.z, hh) - uRup[j].x;
              float alc = sl < 0.0 ? uRup[j].y : uRup[j].z;
              float g = (exp(-dl / uSigma) * 0.75 + exp(-dl / (uSigma * 0.22)) * 0.6) * br * smoothstep(0.0, 0.25, tr);
              if (g > glow) { glow = g; cg = ip == 0 ? cPieza[0] : ip == 1 ? cPieza[1] : ip == 2 ? cPieza[2] : cPieza[3]; }
              cal = max(cal, exp(-max(tr - abs(sl) / max(alc, 0.001) * uRup[j].w, 0.0) / 1.4) * exp(-dl / uSigma));
            }
          }
          col += cg * glow * uGlow * (1.0 + cal * 0.9);
          for (int i = 0; i < ${NO}; i++) {
            float k = uOnda[i].w; if (k <= 0.0) continue;
            int ip = int(uOndaPieza[i]);
            float d = ip < 0 ? length(p - uOnda[i].xy) : (ip == 0 ? dP[0] : ip == 1 ? dP[1] : ip == 2 ? dP[2] : dP[3]);
            float r = uOnda[i].z, w = 1.3 + r * 0.016;
            float anillo = exp(-((d - r) / w) * ((d - r) / w)) + 0.10 * (1.0 - smoothstep(r - 14.0 * w, r, d)) * step(d, r);
            col = uModo == 1 || uModo == 4 ? col + cOnda * anillo * k * 0.55 : mix(col, cOnda, clamp(anillo * k, 0.0, 0.9));
          }
          // el borde de la maqueta se funde con el fondo
          float bd = min(min(vPos.x - uCaja.x, uCaja.y - vPos.x), min(vPos.z - uCaja.z, uCaja.w - vPos.z));
          col = mix(cExterior, col, smoothstep(0.0, uBorde, bd));   // la orilla de la caja se funde con el plano exterior
          gl_FragColor = vec4(salida(niebla(col, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0);
        }`;

      function armarRelieve() {
        // textura: normal (RGB, con exageración fija 4) y tierra/mar (A), a resolución completa con mipmaps
        const S0 = 4, tex = new Uint8Array(RW * RH * 4);
        for (let j = 0; j < RH; j++) for (let i = 0; i < RW; i++) {
          const h = (ii, jj) => ALT[clamp(jj, 0, RH - 1) * RW + clamp(ii, 0, RW - 1)] / 1000 * S0;
          const dx = (h(i + 1, j) - h(i - 1, j)) / (2 * CX), dz = (h(i, j + 1) - h(i, j - 1)) / (2 * CY);
          const l = Math.hypot(dx, 1, dz), k = (j * RW + i) * 4;
          tex[k] = (-dx / l * 0.5 + 0.5) * 255; tex[k + 1] = (-dz / l * 0.5 + 0.5) * 255; tex[k + 2] = clamp(-ALT[j * RW + i] / 8000) * 255;
          tex[k + 3] = ALT[j * RW + i] > 0 ? 255 : 0;
        }
        const tN = new THREE.DataTexture(tex, RW, RH, THREE.RGBAFormat, THREE.UnsignedByteType);
        tN.colorSpace = THREE.NoColorSpace; tN.generateMipmaps = true; tN.minFilter = THREE.LinearMipmapLinearFilter; tN.magFilter = THREE.LinearFilter;
        tN.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy()); tN.needsUpdate = true;
        uRelieve.tNormal.value = tN; uRelieve.uRel.value = CFG.luz.relieve * EXAG / S0;
        // máscara del país (1 adentro): el contorno relleno en un lienzo 2D
        const c = document.createElement("canvas"); c.width = 2048; c.height = 2048; const g = c.getContext("2d");
        g.fillStyle = "black"; g.fillRect(0, 0, 2048, 2048); g.fillStyle = "white"; g.filter = "blur(1.5px)";
        for (const an of M.frontera) { g.beginPath(); an.forEach(([x, y], k) => { const u = (x - X0) / (X1 - X0) * 2048, v = (Y1 - y) / (Y1 - Y0) * 2048; k ? g.lineTo(u, v) : g.moveTo(u, v); }); g.closePath(); g.fill(); }
        const tP = new THREE.CanvasTexture(c); tP.flipY = false; tP.colorSpace = THREE.NoColorSpace; tP.minFilter = THREE.LinearMipmapLinearFilter; tP.generateMipmaps = true;
        uRelieve.tPais.value = tP;

        if (ES.cubos) return armarCubos(g);
        const PASO = 2, nx = Math.floor((RW - 1) / PASO) + 1, ny = Math.floor((RH - 1) / PASO) + 1;
        const pos = new Float32Array(nx * ny * 3), uv = new Float32Array(nx * ny * 2);
        for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
          const ci = i * PASO, cj = j * PASO, k = j * nx + i;
          const x = X0 + (ci + 0.5) * CX, y = Y1 - (cj + 0.5) * CY;
          pos[3 * k] = x; pos[3 * k + 1] = Math.max(0, ALT[cj * RW + ci]) / 1000 * EXAG; pos[3 * k + 2] = -y;
          uv[2 * k] = (ci + 0.5) / RW; uv[2 * k + 1] = (cj + 0.5) / RH;
        }
        const idx = new Uint32Array((nx - 1) * (ny - 1) * 6); let q = 0;
        for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) { const a = j * nx + i, b = a + 1, c2 = a + nx, d = c2 + 1; idx[q++] = a; idx[q++] = c2; idx[q++] = b; idx[q++] = b; idx[q++] = c2; idx[q++] = d; }
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.BufferAttribute(pos, 3)); geo.setAttribute("uv", new THREE.BufferAttribute(uv, 2)); geo.setIndex(new THREE.BufferAttribute(idx, 1));
        matRelieve = new THREE.ShaderMaterial({ uniforms: uRelieve, 
          vertexShader: "varying vec2 vUv; varying vec3 vPos; varying float vAlt; void main(){ vUv = uv; vPos = position; vAlt = position.y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
          fragmentShader: FRAG_RELIEVE });
        const malla = new THREE.Mesh(geo, matRelieve); malla.frustumCulled = false; scene.add(malla);
      }

      // [estilo:voxel] el relieve en columnas: una por cada bloque de 6×6 celdas, altura en escalones, tono por altura
      function armarCubos(gPais) {
        const B = 6, nx = Math.floor(RW / B), ny = Math.floor(RH / B), paso = 0.3 * EXAG;   // escalón: 300 m reales
        const pais = gPais.getImageData(0, 0, 2048, 2048).data;
        const cBaja = lin(COL.tierra_baja), cMedia = lin(COL.tierra_media), cAlta = lin(COL.tierra_alta), cMar = lin(COL.mar), cHondo = lin(COL.mar_hondo), cF = lin(COL.exterior);
        const lista = [];
        for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
          let s = 0, t = 0, fondo = 0; for (let b = 0; b < B; b++) for (let a = 0; a < B; a++) { const v = ALT[(j * B + b) * RW + i * B + a]; s += Math.max(0, v); fondo += Math.min(0, v); if (v > 0) t++; }
          const m = s / (B * B), x = X0 + (i + 0.5) * B * CX, y = Y1 - (j + 0.5) * B * CY;
          const borde = suave(0, CFG.borde_km, Math.min(x - X0, X1 - x, y - Y0, Y1 - y));
          if (borde <= 0.02) continue;
          const tierra = t > B * B / 2;
          const alto = tierra ? Math.max(1, Math.round(m / 1000 * EXAG / paso)) * paso : paso * 0.35;
          const hN = clamp(m / R.max_m), col = new THREE.Color();
          if (tierra) { col.copy(cBaja).lerp(cMedia, suave(0, 0.38, hN)).lerp(cAlta, suave(0.38, 1, hN)); col.multiplyScalar(0.92 + 0.16 * hash(i, j)); }
          else col.copy(cMar).lerp(cHondo, suave(0, 5000, -fondo / (B * B))).multiplyScalar(0.95 + 0.1 * hash(i, j));
          const dentro = pais[(Math.floor((Y1 - y) / (Y1 - Y0) * 2048) * 2048 + Math.floor((x - X0) / (X1 - X0) * 2048)) * 4] > 127;
          if (!dentro && tierra) col.lerp(cF, 1 - CFG.fuera);
          col.lerp(cF, 1 - borde);
          lista.push({ x, y, alto, col });
        }
        const geo = new THREE.BoxGeometry(B * CX * 0.96, 1, B * CY * 0.96); geo.translate(0, 0.5, 0);
        const mat = new THREE.MeshLambertMaterial();
        cubos = new THREE.InstancedMesh(geo, mat, lista.length); cubos.frustumCulled = false;
        const m4 = new THREE.Matrix4();
        lista.forEach((c, k) => { m4.makeScale(1, c.alto, 1); m4.setPosition(c.x, 0, -c.y); cubos.setMatrixAt(k, m4); cubos.setColorAt(k, c.col); });
        cubos.userData = { lista, base: lista.map((c) => c.col.clone()) };
        scene.add(cubos);
        const az = CFG.luz.azimut * Math.PI / 180, el = CFG.luz.elevacion * Math.PI / 180;
        const sol = new THREE.DirectionalLight(lin(COL.luz), CFG.luz.fuerza * Math.PI); sol.position.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
        scene.add(sol, new THREE.AmbientLight(lin(COL.ambiente), CFG.luz.ambiente * Math.PI));
      }
      // [/estilo:voxel]

      // [estilo:voxel] la falla y las ondas tiñen los cubos (lo que en los demás estilos hace el shader del relieve)
      function cubosEn(t, ondas, rup) {
        if (!rup.length && !ondas.length && !cubos.userData.sucio) return;
        const { lista, base } = cubos.userData, FALLAS = ctx.fallas;
        const ac = lin(COL.acento), se = lin(COL.secundario), on = lin(COL.onda), c = new THREE.Color();
        lista.forEach((q, i) => {
          c.copy(base[i]);
          for (const e of rup) { const f = FALLAS[ctx.idxFalla(e.pieza)]; let g = 0;
            for (let j = 0; j < f.simple.length - 1; j++) { const a = f.simple[j], b = f.simple[j + 1]; if (a[3]) continue;
              const dx = b[0] - a[0], dy = b[1] - a[1], h = clamp(((q.x - a[0]) * dx + (q.y - a[1]) * dy) / Math.max(1e-9, dx * dx + dy * dy));
              const d = Math.hypot(q.x - a[0] - dx * h, q.y - a[1] - dy * h); if (d > 14) continue;
              const s = a[2] + (b[2] - a[2]) * h - e.s0, alc = s < 0 ? e.km_menos : e.km_mas;
              if (Math.abs(s) <= alc * clamp((t - e.t) / e.dur)) g = Math.max(g, Math.exp(-d / 4.5)); }
            if (g > 0) c.lerp(f.protagonista ? ac : se, Math.min(1, g * 1.3)); }
          for (const o of ondas) { const d = o.pieza < 0 ? Math.hypot(q.x - o.x, q.y - o.y) : ctx.distCadena(FALLAS[o.pieza].simple, q.x, q.y), w = 4 + o.r * 0.04;
            c.lerp(on, Math.min(0.8, Math.exp(-Math.pow((d - o.r) / w, 2)) * o.k)); }
          cubos.setColorAt(i, c);
        });
        cubos.instanceColor.needsUpdate = true; cubos.userData.sucio = rup.length > 0 || ondas.length > 0;
      }
      // [/estilo:voxel]

      await cargarRelieve();
      const geo = (lon, lat) => [(lon - P.lon0) * P.km_lon, (lat - P.lat0) * P.km_lat];
      Object.assign(ctx, { altura, geo, km: geo, NR, NC, NO, GLSL_RUPTURA, uRuptura, superficie: uRelieve });
      return { armar: armarRelieve, en: (t) => { if (cubos) cubosEn(t, ctx.cuadro.ondas, ctx.cuadro.rupturas); } };
    },
    armar(ctx, estado) { estado.armar(); },
    en(t, estado) { estado.en(t); },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
