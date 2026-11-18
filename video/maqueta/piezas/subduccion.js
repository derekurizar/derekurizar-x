// Pieza «subduccion» (ficha: subduccion.json; reglas: scripts/maqueta_tipos/subduccion.py): un bloque-diagrama genérico de
// la Tierra cortada (esquema, no a escala), sin lugar real. Centrado en `lugar` y orientado por `rumbo` (u: del mar a la
// tierra, el sentido en que entra la placa; v: a lo largo de la fosa). Todo en METROS de maqueta × `tamano`; z = altura
// sobre el mar del bloque (negativa hacia abajo). El bloque se apoya en el suelo del mundo: la tapa queda D más arriba.
// - LA TAPA: el mar (translúcido, con el fondo y la FOSA que se ven debajo), la costa con su playa y la tierra con lomas;
//   sobre ella la FILA de conos empinados (estratovolcanes genéricos) paralela a la fosa, el primero partido por el corte.
// - LA CARA DEL CORTE (v = −WV): el agua, la PLACA OCEÁNICA (fría, apagada, con su costra de basalto) que entra por la fosa y
//   baja con `angulo_grados` bajo la CONTINENTAL, la CUÑA DE MANTO encima y el manto debajo; bajo el cono partido, el
//   conducto con su bolsa al pie de la continental. Las otras caras repiten las capas.
// - CON VIDA (seek puro, todo de t en el shader): la placa avanza (bandas que corren hacia la fosa y bajan con ella), flechas
//   sobre el mar hacia la tierra (`flechas`), gotas de agua que salen de la placa, el manto de encima que se enciende y el
//   magma que sube en gotas y pulsa por el conducto (`magma`). De noche lo que da luz propia brilla más.
// - «resaltar»: la pieza entera (brillo) o, con `elemento`, cada lugar: fosa, placa-oceanica, placa-continental, manto,
//   placa-100, cono, fila (ctx.cuadro.elementos[id] = [{i, k}], i en ese orden).
// Sin colores escritos (ctx.tonos, ctx.COL); sin texto ni números.
(function (MAQ) {
  const L1 = 600, L2 = 1300, WV = 450, D = 600, W0 = 45, DIP = 55, FW = 110, UCOSTA = 170, TC = 150, TP = 90, BEND = 150, RC = 0.1;
  const UC = (L2 - L1) / 2, TAU = 2 * Math.PI;
  const liso = (a, b, x) => { const v = Math.min(1, Math.max(0, (x - a) / (b - a))); return v * v * (3 - 2 * v); };
  const techo = (u, ta) => u <= 0 ? W0 + DIP * Math.exp(-(u / FW) * (u / FW)) : W0 + DIP + ta * (u - BEND * (1 - Math.exp(-u / BEND)));
  const pend = (u, ta) => u <= 0 ? -2 * DIP * u / (FW * FW) * Math.exp(-(u / FW) * (u / FW)) : ta * (1 - Math.exp(-u / BEND));
  const fase = (s) => ((s * 0.6180339887) % 1) * TAU;
  const tierra = (u, v, ph) => u < UCOSTA ? 0 : 22 * liso(UCOSTA, UCOSTA + 260, u) + 6 * Math.sin(u / 95 + ph) * Math.sin(v / 140 + 1.3 * ph) * liso(UCOSTA + 40, UCOSTA + 240, u);
  const piso = (u, v, ta, ph) => u <= 0 ? -techo(u, ta) : u < UCOSTA ? -(W0 + DIP) * (1 - liso(0, UCOSTA, u)) : tierra(u, v, ph);
  const perfil = (x) => x >= 1 ? 0 : x < RC ? Math.pow(1 - RC, 1.55) - 0.12 * (1 - (x / RC) * (x / RC)) : Math.pow(1 - x, 1.55);
  const SIN_FLUJO = -99999;

  const VERT = "attribute vec3 color; attribute vec3 aQ; attribute float aR, aL; varying vec3 vCol, vPos, vQ; varying float vR, vL;" +
    "void main(){ vCol = color; vQ = aQ; vR = aR; vL = aL; vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }";
  const FRAG = `uniform float uBrillo, uAlfa, uNoche, uMagma, uUArc, uUM, uZM, uVel; uniform float uE[8]; uniform vec3 cAcento, cMagma, cLuz;
    varying vec3 vCol, vPos, vQ; varying float vR, vL;
    float es(float r) { return 1.0 - step(0.5, abs(vR - r)); }
    void main(){
      vec3 c = vCol;
      float agua = es(0.0), oce = es(1.0), con = es(2.0), man = es(3.0), cun = es(4.0), c0 = es(5.0), cs = es(6.0), cond = es(7.0);
      // la placa avanza: bandas que corren hacia la fosa y bajan con ella (vQ.z = lo andado a lo largo de la placa)
      float m = fract((vQ.z - uT * uVel) / 46.0), conFlujo = step(-90000.0, vQ.z);
      c *= 1.0 - oce * conFlujo * 0.1 * smoothstep(0.0, 0.05, m) * smoothstep(0.42, 0.36, m);
      // el agua brilla apenas
      c *= 1.0 + agua * 0.05 * sin(vQ.x * 0.045 + uT * 0.9 + sin(vQ.z * 0.02 + uT * 0.5) * 2.0);
      // el manto de encima se enciende sobre la placa bajo la fila
      float dm = length(vec2((vQ.x - uUM) / 130.0, (vQ.y - uZM) / 62.0));
      float g = uMagma * cun * exp(-dm * dm * 1.5) * (0.84 + 0.16 * sin(uT * 1.6 + vQ.x * 0.03));
      c = mix(c, cMagma * (0.6 + 0.4 * vL), g * 0.75);
      float k = uE[0] * max(oce, con) * (1.0 - smoothstep(55.0, 90.0, abs(vQ.x)));
      k = max(k, uE[1] * oce);
      k = max(k, uE[2] * con);
      k = max(k, uE[3] * max(man, cun));
      k = max(k, uE[4] * oce * (1.0 - smoothstep(50.0, 85.0, abs(vQ.x - uUArc))));
      k = max(k, uE[5] * max(c0, cond));
      k = max(k, uE[6] * max(c0, cs));
      k = max(k, uE[7] * oce);
      c = mix(c, cAcento * (0.5 + 0.5 * vL), k * 0.8) * uBrillo;
      vec3 col = niebla(c, vPos, gl_FragCoord.xy);
      // lo que da luz propia (el magma del conducto, la cuña encendida): no se apaga con la hora
      float pulso = 0.5 + 0.5 * sin(vQ.y * 0.07 - uT * 2.6);
      vec3 em = cond * cMagma * (0.35 + uMagma * 0.35 * pulso) * (0.7 + 0.8 * uNoche) + g * cLuz * (0.18 + 0.3 * uNoche);
      col += em * (1.0 - smoothstep(uNiebla.x, uNiebla.y, distance(vPos, cameraPosition)));
      gl_FragColor = vec4(salida(col, gl_FragCoord.xy), uAlfa); }`;
  const sRGB = "vec3 srgb(vec3 c){ return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c)); }";

  MAQ.PIEZAS.subduccion = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1;
      const C = (a, b) => lin(COL[a] || COL[b] || COL.secundario);
      // ---- los tonos (todos del estilo)
      const cMar = tonos.agua.clone(), cMarH = C("mar_hondo", "mar").lerp(tonos.agua, 0.3).multiplyScalar(0.8);
      const cOce = C("mar_hondo", "mar").lerp(tonos.linea, 0.4).lerp(tonos.muro, 0.18).multiplyScalar(oscuro ? 1.25 : 0.95);
      const cBasalto = cOce.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.72);
      const cFondo = cOce.clone().lerp(C("costa", "secundario"), 0.22);
      const cCont = C("tierra_media", "secundario").lerp(C("tierra_alta", "secundario"), 0.4).multiplyScalar(oscuro ? 1.0 : 0.92);
      const cCont2 = C("tierra_media", "secundario").lerp(tonos.muro, 0.2).multiplyScalar(0.78);
      return piezas.map((p, np) => {
      // el manto: `manto_brillo` 1 = el rojo de antes; más bajo, más apagado y más gris (el magma queda como lo más vivo)
      const mb = clamp(p.manto_brillo == null ? 0.4 : p.manto_brillo, 0, 1), gris = tonos.asfalto.clone().lerp(tonos.muro, 0.3);
      const cManto = tonos.mal.clone().lerp(C("tierra_media", "secundario"), 0.55).lerp(gris, 0.55 * (1 - mb)).multiplyScalar((oscuro ? 0.85 : 0.72) * (0.62 + 0.38 * mb));
      const cMantoH = tonos.mal.clone().lerp(C("tierra_baja", "secundario"), 0.45).lerp(gris, 0.5 * (1 - mb)).multiplyScalar((oscuro ? 0.55 : 0.5) * (0.7 + 0.3 * mb));
      const cCuna = cManto.clone().lerp(tonos.mal, 0.2).multiplyScalar(1.1);
      const cMagma = tonos.mal.clone().lerp(C("luces", "acento"), 0.22), cLuz = C("luces", "acento");
      const cCeniza = C("tierra_alta", "secundario").lerp(tonos.asfalto, 0.5).multiplyScalar(oscuro ? 1.1 : 0.85);
      const cCrater = cCeniza.clone().multiplyScalar(0.55), cLava = tonos.muro.clone().lerp(tonos.asfalto, 0.6).multiplyScalar(0.75);
      const cRoca = C("tierra_alta", "secundario").lerp(tonos.muro, 0.3).multiplyScalar(oscuro ? 1.0 : 0.85);
      const cVerde = tonos.verde.clone().lerp(tonos.campo2, 0.3), cCampo = tonos.campo.clone(), cCampo2 = tonos.campo2.clone();
      const cArena = tonos.arena.clone(), cSuelo = C("tierra_media", "secundario").lerp(tonos.campo, 0.4).multiplyScalar(0.8);
      const cGota = C("costa", "secundario").lerp(tonos.agua, 0.2), cFlecha = tonos.secundario.clone();
        const K = p.tamano, M = metros(1) * K, ph = fase(p.semilla), ta = p.ta, UA = p.u_arco;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const y0 = ctx.suelo(p.x, p.y) - 0.8 * M;
        const W2 = (u, v) => [p.x + ((u - UC) * ux - v * uy) * M, p.y + ((u - UC) * uy + v * ux) * M];
        const E = (u, v, z) => { const [x, y] = W2(u, v); return [x, y0 + (D + z) * M, -y]; };
        const Uw = [ux, 0, -uy], Vw = [-uy, 0, -ux];
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // lo andado a lo largo del techo de la placa (para las bandas que corren)
        const sTab = [0]; for (let i = 1; i <= 400; i++) { const u = (i - 0.5) * 4; sTab.push(sTab[i - 1] + 4 * Math.hypot(1, pend(u, ta))); }
        const sArc = (u) => { if (u <= 0) return u; const f = Math.min(400, u / 4), i = Math.floor(f); return i >= 400 ? sTab[400] : sTab[i] + (sTab[i + 1] - sTab[i]) * (f - i); };
        // la cuña: desde dónde el techo de la placa pasa bajo la continental
        let uw = 0; { let a = 0, b = 3000; for (let i = 0; i < 50; i++) { const m = (a + b) / 2; if (techo(m, ta) < TC) a = m; else b = m; } uw = a; }
        const c0 = p.conos[0], UM = UA - 25, ZM = -(techo(UA - 25, ta) - 42);

        // ---- los acumuladores (posición, color, región, luz horneada, [u, z, s] local)
        const nueva = () => ({ pos: [], col: [], reg: [], luz: [], q: [], idx: [] });
        const solido = nueva(), agua = nueva();
        const vert = (acc, P, col, l, reg, q) => { acc.pos.push(P[0], P[1], P[2]); acc.col.push(col.r * l, col.g * l, col.b * l); acc.reg.push(reg); acc.luz.push(l); acc.q.push(q[0], q[1], q[2]); return acc.pos.length / 3 - 1; };
        // una rejilla de puntos ya en el mundo (filas × columnas) con su color, región y [u, z, s]: la luz sale de la normal
        const lamina = (acc, P, Cc, reg, Q, nFija) => {
          const R = P.length, Cn = P[0].length, q0 = acc.pos.length / 3;
          for (let i = 0; i < R; i++) for (let j = 0; j < Cn; j++) {
            let l;
            if (nFija) l = sombra(nFija[0], nFija[1], nFija[2]);
            else {
              const a = P[Math.max(0, i - 1)][j], b = P[Math.min(R - 1, i + 1)][j], c = P[i][Math.max(0, j - 1)], d = P[i][Math.min(Cn - 1, j + 1)];
              const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [d[0] - c[0], d[1] - c[1], d[2] - c[2]];
              let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
              const n = Math.hypot(nx, ny, nz) || 1; if (ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
              l = sombra(nx / n, ny / n, nz / n);
            }
            vert(acc, P[i][j], Cc[i][j], l, Array.isArray(reg) ? reg[i][j] : reg, Q[i][j]);
          }
          for (let i = 0; i + 1 < R; i++) for (let j = 0; j + 1 < Cn; j++) {
            const a = q0 + i * Cn + j, b = a + 1, c = a + Cn, d = c + 1;
            acc.idx.push(a, c, b, b, c, d);
          }
        };

        // ================= las capas del corte (bandas entre dos curvas de u)
        // cada capa: [u0, u1, techo(u, v), piso(u, v), región, color(u, z, f, v), acc, s(u)?]
        const capas = [
          [-L1, UCOSTA, () => 0, (u, v) => Math.min(-0.5, piso(u, v, ta, ph)), 0, (u, z) => cMar.clone().lerp(cMarH, clamp(-z / 110, 0, 1)), agua, null],
          [-L1, L2, (u) => -techo(u, ta), (u) => -(techo(u, ta) + TP * Math.hypot(1, pend(u, ta))), 1,
            (u, z, f) => (f < 0.24 ? cBasalto : cOce).clone().multiplyScalar(0.92 + 0.14 * ruido(u, z, 26, 3) - (f > 0.24 ? 0.12 * f : 0)), solido, sArc],
          [0, L2, (u, v) => piso(u, v, ta, ph), (u) => -Math.min(techo(u, ta), TC), 2,
            (u, z, f, v) => { const top = piso(u, v, ta, ph), d = top - z;
              let c = cCont.clone().lerp(cCont2, 0.5 + 0.5 * Math.sin(z / 13 + 2.4 * ruido(u, z, 60, 4)));
              if (u > UCOSTA && d < 7) c = cSuelo.clone();
              return c.multiplyScalar(0.92 + 0.12 * ruido(u, z, 18, 5)); }, solido, null],
          [uw, L2, () => -TC, (u) => -techo(u, ta), 4, (u, z) => cCuna.clone().multiplyScalar(0.9 + 0.14 * ruido(u, z, 34, 6)), solido, null],
          [-L1, L2, (u) => -(techo(u, ta) + TP * Math.hypot(1, pend(u, ta))), () => -D, 3,
            (u, z) => cManto.clone().lerp(cMantoH, clamp(-z / D, 0, 1)).multiplyScalar(0.9 + 0.14 * ruido(u, z, 40, 7)), solido, null],
        ];
        const FILAS = [3, 5, 5, 4, 7];
        // la cara a v fijo (el corte y la de atrás)
        const cara = (v, n) => {
          capas.forEach(([a, b, top, bot, reg, colf, acc, sf], ic) => {
            const du = 8, nc = Math.ceil((b - a) / du), P = [], Cc = [], Q = [], nr = FILAS[ic];
            for (let k = 0; k <= nr; k++) { P.push([]); Cc.push([]); Q.push([]); }
            for (let i = 0; i <= nc; i++) {
              const u = a + (b - a) * i / nc;
              let zt = Math.max(-D, top(u, v)), zb = Math.max(-D, Math.min(zt, bot(u, v)));
              for (let k = 0; k <= nr; k++) {
                const f = k / nr, z = zt + (zb - zt) * f;
                P[k].push(E(u, v, z)); Cc[k].push(colf(u, z, f, v)); Q[k].push([u, z, sf ? sf(u) : u]);
              }
            }
            lamina(acc, P, Cc, reg, Q, n);
          });
        };
        const nF = [uy, 0, ux], nB = [-uy, 0, -ux];
        cara(-WV, nF); cara(WV, nB);
        // las caras de los cantos (u fijo): las mismas capas a lo ancho
        const canto = (u, n) => {
          capas.forEach(([a, b, top, bot, reg, colf, acc], ic) => {
            if (u < a || u > b) return;
            const nv = 30, P = [], Cc = [], Q = [], nr = FILAS[ic];
            for (let k = 0; k <= nr; k++) { P.push([]); Cc.push([]); Q.push([]); }
            for (let j = 0; j <= nv; j++) {
              const v = -WV + 2 * WV * j / nv, zt = Math.max(-D, top(u, v)), zb = Math.max(-D, Math.min(zt, bot(u, v)));
              for (let k = 0; k <= nr; k++) { const f = k / nr, z = zt + (zb - zt) * f; P[k].push(E(u, v, z)); Cc[k].push(colf(u, z, f, v)); Q[k].push([u, z, SIN_FLUJO]); }
            }
            lamina(acc, P, Cc, reg, Q, n);
          });
        };
        canto(-L1, Uw.map((x) => -x)); canto(L2, Uw);

        // ================= la tapa: el fondo del mar (oceánica hasta la fosa; continental hasta la costa) y la tierra
        const tapa = (a, b, du, reg, colf, zf) => {
          const nc = Math.ceil((b - a) / du), nv = 46, P = [], Cc = [], Q = [];
          for (let j = 0; j <= nv; j++) {
            const v = -WV + 2 * WV * j / nv, f = [], fc = [], fq = [];
            for (let i = 0; i <= nc; i++) { const u = a + (b - a) * i / nc, z = zf(u, v); f.push(E(u, v, z)); fc.push(colf(u, v, z)); fq.push([u, z, reg === 1 ? sArc(u) : u]); }
            P.push(f); Cc.push(fc); Q.push(fq);
          }
          lamina(solido, P, Cc, reg, Q);
        };
        tapa(-L1, 0, 8, 1, (u, v) => cFondo.clone().lerp(cBasalto, 0.55 * Math.exp(-(u / 50) * (u / 50))).multiplyScalar(0.9 + 0.14 * ruido(u, v, 30, 8)),
          (u, v) => piso(u, v, ta, ph) + 1.2 * (ruido(u, v, 22, 9) - 0.5));
        tapa(0, UCOSTA, 6, 2, (u, v) => cCont2.clone().lerp(cFondo, 0.3).lerp(cArena, liso(UCOSTA - 40, UCOSTA, u) * 0.6).multiplyScalar(0.92 + 0.12 * ruido(u, v, 24, 10)),
          (u, v) => piso(u, v, ta, ph));
        tapa(UCOSTA, L2, 10, 2, (u, v, z) => {
          const n1 = ruido(u, v, 120, 11), n2 = ruido(u, v, 30, 12);
          let c = cCampo.clone().lerp(cCampo2, 0.6 * n1).lerp(cVerde, 0.45 * liso(0.55, 0.8, n2));
          c.lerp(cArena, 1 - liso(UCOSTA + 8, UCOSTA + 30, u));
          return c.multiplyScalar(0.9 + 0.12 * n2 + 0.004 * z);
        }, (u, v) => tierra(u, v, ph));

        // el agua: su tapa (translúcida: deja ver el fondo y la fosa)
        { const P = [], Cc = [], Q = [];
          for (let j = 0; j <= 10; j++) { const v = -WV + 2 * WV * j / 10, f = [], fc = [], fq = [];
            for (let i = 0; i <= 40; i++) { const u = -L1 + (UCOSTA + L1) * i / 40; f.push(E(u, v, 0)); fc.push(cMar.clone().multiplyScalar(0.95 + 0.08 * ruido(u, v, 90, 13))); fq.push([u, 0, v]); }
            P.push(f); Cc.push(fc); Q.push(fq); }
          lamina(agua, P, Cc, 0, Q, [0, 1, 0]); }

        // ================= la fila de conos (el primero, partido por el corte)
        const altoCono = (c, u, v, i) => {
          const du = u - c[0], dv = v - c[1], x = Math.hypot(du, dv) / c[2], th = Math.atan2(dv, du);
          const rib = 1 + 0.07 * Math.sin((9 + (i % 3)) * th + ph + i * 1.9) * 4 * x * (1 - x);
          return [tierra(u, v, ph) + c[3] * perfil(x) * (x < 1 ? rib : 1), x, rib];
        };
        p.conos.forEach((c, i) => {
          const NR = 18, NS = i === 0 ? 30 : 56, t0 = i === 0 ? 0 : -Math.PI, t1 = Math.PI, P = [], Cc = [], Q = [];
          const reg = i === 0 ? 5 : 6;
          for (let a = 0; a <= NR; a++) {
            const x = 0.004 + (1.0 - 0.004) * Math.pow(a / NR, 1.15), f = [], fc = [], fq = [];
            for (let s = 0; s <= NS; s++) {
              const th = t0 + (t1 - t0) * s / NS, u = c[0] + x * c[2] * Math.cos(th), v = Math.max(-WV, c[1] + x * c[2] * Math.sin(th));
              const [h, , rib] = altoCono(c, u, v, i);
              f.push(E(u, v, h + 0.3));
              const n = ruido(u * 3, v * 3, 20, 14 + i);
              let cc;
              if (x < RC) cc = cCrater.clone();
              else if (x < 0.32) cc = cCeniza.clone().lerp(cRoca, 0.3 * n);
              else if (x < 0.62) cc = cCeniza.clone().lerp(cRoca, 0.5).lerp(cVerde, liso(0.4, 0.62, x) * 0.6);
              else cc = cVerde.clone().lerp(cCampo2, 0.4 * n).lerp(cCampo, liso(0.85, 1, x));
              cc.multiplyScalar((0.9 + 0.14 * n) * (rib < 1 ? 0.88 : 1));
              fc.push(cc); fq.push([u, h, u]);
            }
            P.push(f); Cc.push(fc); Q.push(fq);
          }
          lamina(solido, P, Cc, reg, Q);
        });
        // el cono partido: sus capas (ceniza y lava alternadas, paralelas a la ladera) en la cara del corte
        { const c = c0, nc = 44, nr = 8, P = [], Cc = [], Q = [];
          for (let k = 0; k <= nr; k++) { P.push([]); Cc.push([]); Q.push([]); }
          for (let i = 0; i <= nc; i++) {
            const u = c[0] - c[2] + 2 * c[2] * i / nc, [h] = altoCono(c, u, -WV, 0), zb = tierra(u, -WV, ph);
            for (let k = 0; k <= nr; k++) {
              const f = k / nr, z = h + (zb - h) * f, cc = (k % 2 ? cLava : cCeniza).clone().multiplyScalar(0.88 + 0.16 * ruido(u, z, 14, 20));
              P[k].push(E(u, -WV, z)); Cc[k].push(cc); Q[k].push([u, z, u]);
            }
          }
          lamina(solido, P, Cc, 5, Q, nF); }
        // el conducto (de la bolsa al pie de la continental hasta el cráter) y su bolsa, un poco delante del corte
        { const vC = -WV - 0.35, zb = -TC + 4, zt = altoCono(c0, c0[0], -WV, 0)[0] - 2, nr = 16, P = [], Cc = [], Q = [];
          for (let k = 0; k <= nr; k++) {
            const f = k / nr, z = zb + (zt - zb) * f, w = 3.5 + 4.5 * (1 - f) + 1.2 * Math.sin(f * 9 + ph), fila = [], fc = [], fq = [];
            for (const s of [-1, 0, 1]) { const u = c0[0] + s * w + 3 * Math.sin(f * 5 + ph); fila.push(E(u, vC, z)); fc.push(cMagma.clone().multiplyScalar(s ? 0.7 : 0.95)); fq.push([u, z, u]); }
            P.push(fila); Cc.push(fc); Q.push(fq);
          }
          lamina(solido, P, Cc, 7, Q, nF);
          const cen = vert(solido, E(c0[0], -WV - 0.3, zb + 2), cMagma, sombra(...nF), 7, [c0[0], zb, 0]), n = 28, q = [];
          for (let j = 0; j < n; j++) { const a = TAU * j / n, u = c0[0] + 44 * Math.cos(a) * (1 + 0.12 * Math.sin(3 * a + ph)), z = zb + 2 + 17 * Math.sin(a);
            q.push(vert(solido, E(u, -WV - 0.3, z), cMagma.clone().multiplyScalar(0.72), sombra(...nF), 7, [u, z, 0])); }
          for (let j = 0; j < n; j++) solido.idx.push(cen, q[j], q[(j + 1) % n]); }

        // ================= el fondo liso (`fondo: "liso"`): un disco oscuro y parejo alrededor del bloque, apenas sobre el suelo
        // del mundo, que tapa los suelos de la receta y se funde con la bruma en el horizonte (sin losas ni parcelas)
        let disco = null;
        if (p.fondo === "liso") {
          const R = 30000, NA = 96, cx = p.x, cy = p.y, yD = ctx.suelo(p.x, p.y) + 0.25 * M, pos = [cx, yD, -cy], idx = [];
          for (let j = 0; j <= NA; j++) { const a = TAU * j / NA; pos.push(cx + R * Math.cos(a), yD, -(cy + R * Math.sin(a))); }
          for (let j = 1; j <= NA; j++) idx.push(0, j, j + 1);
          const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3)); g.setIndex(idx);
          const cD = lin(COL.fondo).lerp(lin(COL.fondo2 || COL.fondo), 0.5).lerp(cMantoH, 0.06).multiplyScalar(oscuro ? 1.25 : 0.55);
          const mat = new THREE.ShaderMaterial({ uniforms: { ...ctx.uComun(), cD: { value: cD }, cC: { value: new THREE.Vector2(cx, -cy) }, uR: { value: 1100 * M } },
            side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2,
            vertexShader: "varying vec3 vPos; void main(){ vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: ctx.GLSL_COMUN + "uniform vec3 cD; uniform vec2 cC; uniform float uR; varying vec3 vPos; void main(){ float d = length(vPos.xz - cC) / uR; vec3 c = cD * (1.08 - 0.1 * smoothstep(0.4, 2.2, d)); gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
          disco = new THREE.Mesh(g, mat); disco.frustumCulled = false; disco.renderOrder = 1; scene.add(disco);
        }

        // ================= las mallas
        const mats = [];
        const material = (alfa, desfase) => {
          const m = new THREE.ShaderMaterial({
            uniforms: { ...ctx.uComun(), uBrillo: { value: 1 }, uAlfa: { value: alfa }, uNoche: { value: noche ? 1 : 0 }, uMagma: { value: p.magma ? 1 : 0 },
              uUArc: { value: UA }, uUM: { value: UM }, uZM: { value: ZM }, uVel: { value: 7 }, uE: { value: new Float32Array(8) },
              cAcento: { value: tonos.acento.clone() }, cMagma: { value: cMagma.clone() }, cLuz: { value: cLuz.clone() } },
            transparent: alfa < 1, depthWrite: alfa >= 1, side: THREE.DoubleSide,
            polygonOffset: desfase !== 0, polygonOffsetFactor: -desfase, polygonOffsetUnits: -desfase * 2,
            vertexShader: VERT, fragmentShader: ctx.GLSL_COMUN + FRAG });
          mats.push(m); return m;
        };
        const poner = (acc, mat, orden) => {
          const g = new THREE.BufferGeometry();
          g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(acc.pos), 3));
          g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(acc.col), 3));
          g.setAttribute("aR", new THREE.BufferAttribute(new Float32Array(acc.reg), 1));
          g.setAttribute("aL", new THREE.BufferAttribute(new Float32Array(acc.luz), 1));
          g.setAttribute("aQ", new THREE.BufferAttribute(new Float32Array(acc.q), 3));
          g.setIndex(acc.pos.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(acc.idx), 1) : new THREE.BufferAttribute(new Uint16Array(acc.idx), 1));
          const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m;
        };
        poner(solido, material(1, 1), 3);
        poner(agua, material(oscuro ? 0.62 : 0.55, 2), 7);

        // ================= lo que se mueve en puntos: las gotas de agua que salen de la placa y el magma que sube
        const uPx = { value: 1 }, uT = { value: 0 }, puntos = [];
        if (p.magma) {
          const NG = 46, gp = [], ga = [];
          for (let i = 0, k = 0; i < 400 && k < NG; i++) {
            const u = UA - 240 + 270 * hz(i, 30);
            if (techo(u, ta) < TC + 25) continue;
            const P = E(u, -WV - 1.2, -techo(u, ta) + 3);
            gp.push(...P); ga.push(hz(i, 31), (30 + 40 * hz(i, 32)) * M, 2.6 + 1.6 * hz(i, 33), 0); k++;
          }
          const NB = 16, bp = [], ba = [], bd = [];
          for (let i = 0; i < NB; i++) {
            const P0 = E(UM + (hz(i, 40) - 0.5) * 70, -WV - 1.4, ZM + (hz(i, 41) - 0.5) * 26), P1 = E(c0[0] + (hz(i, 42) - 0.5) * 30, -WV - 1.4, -TC + 2);
            bp.push(...P0); bd.push(P1[0] - P0[0], P1[1] - P0[1], P1[2] - P0[2]); ba.push(hz(i, 43), 4.5 + 2.5 * hz(i, 44), (5 + 3 * hz(i, 45)) * M, 0);
          }
          const mk = (pos, attrs, vs, fs, aditivo, orden) => {
            const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
            for (const [n, a, d] of attrs) g.setAttribute(n, new THREE.BufferAttribute(new Float32Array(a), d));
            const mat = new THREE.ShaderMaterial({ uniforms: { uPx, uT, uNoche: { value: noche ? 1 : 0 }, cA: { value: (aditivo ? cMagma : cGota).clone() }, cB: { value: cLuz.clone() }, uM: { value: M } },
              transparent: true, depthWrite: false, blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending, vertexShader: vs, fragmentShader: sRGB + fs });
            const m = new THREE.Points(g, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); puntos.push(mat);
          };
          // gotas: suben un trecho desde el techo de la placa y se apagan
          mk(gp, [["aF", ga, 4]],
            "uniform float uPx, uT, uM; attribute vec4 aF; varying float vA; void main(){ float a = fract(uT / aF.z + aF.x); vec3 p = position + vec3(0.0, a * aF.y, 0.0); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(7.0 * uM * uPx / max(1e-3, -mv.z), 1.5, 14.0); vA = smoothstep(0.0, 0.15, a) * (1.0 - smoothstep(0.65, 1.0, a)); }",
            "uniform vec3 cA; uniform float uNoche; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vA * (0.75 + 0.2 * uNoche) * (1.0 - smoothstep(0.55, 1.0, r)); if (a < 0.01) discard; gl_FragColor = vec4(srgb(cA * (1.1 - 0.35 * r)), a); }", false, 9);
          // magma: gotas que suben del manto encendido a la bolsa, bajo el cono
          mk(bp, [["aF", ba, 4], ["aD", bd, 3]],
            "uniform float uPx, uT, uM; attribute vec4 aF; attribute vec3 aD; varying float vA; void main(){ float a = fract(uT / aF.y + aF.x); vec3 p = position + aD * a + vec3(sin(a * 7.0 + aF.x * 20.0) * 6.0 * uM, 0.0, 0.0); vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(aF.z * 2.2 * uPx / max(1e-3, -mv.z), 2.0, 30.0); vA = smoothstep(0.0, 0.2, a) * (1.0 - smoothstep(0.75, 1.0, a)); }",
            "uniform vec3 cA, cB; uniform float uNoche; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = vA * (0.7 + 0.4 * uNoche) * exp(-r * r * 2.2); if (a < 0.01) discard; gl_FragColor = vec4(srgb(mix(cA, cB, 0.35 * (1.0 - r))) * a, a); }", true, 10);
        }

        // ================= las flechas sobre el mar, hacia la tierra (la placa que entra): su forma la pone `en`
        let flechas = null;
        if (p.flechas) {
          const FL = [], NFil = 3, NPor = 3;
          for (let a = 0; a < NFil; a++) for (let b = 0; b < NPor; b++) FL.push({ v: -WV * 0.62 + a * WV * 0.62, f0: (b + 0.35 * hz(a * 7 + b, 50)) / NPor });
          const g = new THREE.BufferGeometry();
          g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(FL.length * 9 * 3), 3));
          g.setAttribute("aA", new THREE.BufferAttribute(new Float32Array(FL.length * 9), 1));
          const mat = new THREE.ShaderMaterial({ uniforms: { cA: { value: cFlecha.clone() }, uK: { value: oscuro ? 0.75 : 0.85 } }, transparent: true, depthWrite: false, side: THREE.DoubleSide,
            vertexShader: "attribute float aA; varying float vA; void main(){ vA = aA; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
            fragmentShader: sRGB + "uniform vec3 cA; uniform float uK; varying float vA; void main(){ if (vA < 0.01) discard; gl_FragColor = vec4(srgb(cA), vA * uK); }" });
          const m = new THREE.Mesh(g, mat); m.frustumCulled = false; m.renderOrder = 8; scene.add(m);
          flechas = { FL, g };
        }
        return { id: p.id, mats, puntos, uPx, uT, flechas, E };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], el = (ctx.cuadro.elementos || {})[s.id] || [];
        for (const m of s.mats) {
          m.uniforms.uBrillo.value = b ? 1 + 0.3 * clamp(b - 1, 0, 1.2) : 1;
          const E = m.uniforms.uE.value; E.fill(0);
          for (const o of el) if (o.i >= 0 && o.i < 8) E[o.i] = Math.max(E[o.i], o.k);
        }
        s.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
        s.uT.value = t;
        if (s.flechas) {
          const { FL, g } = s.flechas, P = g.attributes.position.array, A = g.attributes.aA.array, U0 = -L1 + 50, SPAN = L1 - 120, VEL = 14;
          FL.forEach((f, i) => {
            const q = ((f.f0 + t * VEL / SPAN) % 1 + 1) % 1, u = U0 + q * SPAN, a = Math.pow(Math.sin(Math.PI * q), 0.8), z = 1.2;
            // asta (dos triángulos) y punta (uno), planas sobre el agua, apuntando a +u
            const pts = [[u - 46, f.v - 7], [u, f.v - 7], [u, f.v + 7], [u - 46, f.v - 7], [u, f.v + 7], [u - 46, f.v + 7], [u, f.v - 22], [u + 34, f.v], [u, f.v + 22]];
            pts.forEach(([uu, vv], j) => { const w = s.E(uu, vv, z); P.set(w, (i * 9 + j) * 3); A[i * 9 + j] = a; });
          });
          g.attributes.position.needsUpdate = true; g.attributes.aA.needsUpdate = true;
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
