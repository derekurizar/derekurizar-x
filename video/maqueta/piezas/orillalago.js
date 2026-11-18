// Pieza «orillalago» (ficha: orillalago.json; reglas: scripts/maqueta_tipos/orillalago.py): la orilla de un lago de montaña
// genérico, de cerca. Centrada en `lugar` (la línea del agua con el lago lleno) y orientada por `rumbo` (u: hacia el lago;
// v: a su izquierda). Todo en METROS × `tamano`. Sin lugar real, sin texto, sin marcas, sin personas reales.
// - EL LAGO: agua quieta con su tono más hondo mar adentro, destellos que titilan (seek puro) y, con `seco`, el agua retirada
//   que deja un lecho de lodo y el tul en seco. La PLAYA angosta con la tierra en su borde.
// - EL TULAR: manchas de tul (juncos altos) y de enea (con su espiga) en el agua baja, `tul` 0–1; manojos de tul cortado
//   secándose en la playa; con `aves`, zambullidores oscuros que nadan, se sumergen ≈ 20 s y salen en otro lado.
// - EL MUELLE público de madera sobre pilotes (tablones, largueros, bitas, escalera a la playa), con sus lanchas amarradas.
// - LOS LOTES en ranuras fijas: HOTELES bajos genéricos (cuerpo largo con corredor de columnas hacia el lago) y CASAS DE
//   CAMPO con jardín (césped, seto, árboles, sendero a la playa), `construcciones` 0–1 llena las ranuras. `epoca` hoy:
//   más lotes ocupados, hoteles de tres pisos, muros, faroles.
// - EL CAMINO detrás (tierra con huellas o asfalto con su raya), con el acceso al muelle; por él pasan un camión-bus, un carro,
//   un camión y gente a pie, algunos con su carga a la espalda sujeta por la frente (mecapal).
// - LOS HUERTOS (surcos) y EL PUEBLITO: casas de adobe encalado con teja y reja junto al camino; ranchos de caña y adobe con
//   techo de paja entre cafetales más atrás; humo de fogón. Los VOLCANES al fondo, tierra adentro.
// - CON VIDA (todo función de t): lanchas que cruzan con su estela, cayucos con su remero de pie, gente que camina, vende en el
//   muelle o corta tul, vehículos por el camino, destellos, humo, aves. De noche (ES.noche): ventanas, faroles y luces de las
//   lanchas. Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin).
(function (MAQ) {
  const HL = 0.6, HA = 0.08, H_MUELLE = 1.3, SECO_M = 24, U_PLAYA = -10, U_CAMINO = -95, MU0 = -6, MU1 = 48, MV = 1.6, LV = 700;
  const TAU = 2 * Math.PI;
  // las ranuras de los lotes (centro en v) y en qué orden se llenan; tipo h = hotel, c = casa de campo
  const LOTES = { antes: [[70, "h"], [-70, "h"], [34, "c"], [-34, "c"], [110, "c"], [-110, "c"], [150, "c"], [-150, "c"], [190, "c"], [-190, "c"]],
    hoy: [[70, "h"], [-70, "h"], [150, "h"], [34, "c"], [-34, "c"], [110, "c"], [-110, "c"], [-150, "c"], [190, "c"], [-190, "c"]] };
  MAQ.PIEZAS.orillalago = {
    orden: 7,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL, metros, clamp } = ctx;
      const noche = !!ES.noche, oscuro = ES.modo === 1, dia = !!ES.dia;
      // ---- los tonos (todos del estilo)
      const cAgua = tonos.agua.clone(), cAguaH = tonos.agua.clone().multiplyScalar(oscuro ? 0.8 : 0.72).lerp(tonos.linea, 0.06);
      const cAguaB = tonos.agua.clone().lerp(tonos.verde, 0.22).lerp(tonos.arena, 0.12);
      const cArena = tonos.arena.clone(), cArenaM = tonos.arena.clone().lerp(cAgua, 0.25).multiplyScalar(0.82);
      const cLodo = tonos.arena.clone().lerp(lin(COL.tierra_media), 0.45).multiplyScalar(oscuro ? 0.9 : 0.72);
      const cPasto = tonos.campo.clone().lerp(tonos.verde, 0.4), cPasto2 = tonos.campo2.clone();
      const cCesped = tonos.verde.clone().lerp(tonos.campo, 0.3).multiplyScalar(dia ? 1.12 : 1.05);
      const cSeto = tonos.verde.clone().multiplyScalar(0.62), cHoja = tonos.verde.clone().multiplyScalar(0.78), cHoja2 = tonos.verde.clone().lerp(lin(COL.tierra_media), 0.25).multiplyScalar(0.85);
      const cTronco = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.4).multiplyScalar(0.7);
      const cTul = tonos.verde.clone().lerp(tonos.campo2, 0.35), cTulP = tonos.arena.clone().lerp(tonos.verde, 0.35).multiplyScalar(1.05);
      const cTulSeco = tonos.arena.clone().lerp(lin(COL.tierra_alta), 0.3);
      const cEspiga = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.35).multiplyScalar(0.7);
      const cMadera = lin(COL.tierra_alta).lerp(lin(COL.tierra_media), 0.55).multiplyScalar(oscuro ? 0.75 : 0.92);
      const cMaderaO = cMadera.clone().multiplyScalar(0.66), cMaderaC = cMadera.clone().lerp(tonos.arena, 0.35);
      const cMuro = tonos.muro.clone(), cZocalo = tonos.muro.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.85);
      const cEncal = tonos.muro.clone().lerp(lin(COL.costa), 0.15).multiplyScalar(dia ? 1.04 : 1.0);
      const cAdobe = lin(COL.tierra_media).lerp(tonos.arena, 0.45).multiplyScalar(oscuro ? 0.85 : 0.95);
      const cCana = tonos.arena.clone().lerp(lin(COL.tierra_alta), 0.45).multiplyScalar(0.92);
      const cTeja = tonos.techo.clone(), cTejaO = tonos.techo.clone().multiplyScalar(0.8);
      const cTechoG = tonos.techo.clone().lerp(tonos.asfalto, 0.45).lerp(tonos.muro, 0.15);
      const cPaja = tonos.arena.clone().lerp(lin(COL.tierra_alta), 0.5).multiplyScalar(0.88), cPajaO = cPaja.clone().multiplyScalar(0.72);
      const cHueco = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.55 : 0.32);
      const cVidrio = noche ? lin(COL.luces).lerp(lin(COL.luz || COL.luces), 0.3) : tonos.agua.clone().lerp(tonos.linea, 0.3).multiplyScalar(0.62);
      const cReja = tonos.asfalto.clone().multiplyScalar(oscuro ? 0.8 : 0.4);
      const cCamino = tonos.calle.clone().lerp(tonos.arena, 0.3), cHuella = cCamino.clone().multiplyScalar(0.84);
      const cAsfalto = tonos.asfalto.clone(), cRaya = tonos.raya.clone().lerp(tonos.muro, 0.2);
      const cSurco = lin(COL.tierra_media).lerp(tonos.arena, 0.2).multiplyScalar(oscuro ? 0.8 : 0.75), cMata = tonos.verde.clone().lerp(tonos.bien, 0.15);
      const cCafe = tonos.verde.clone().multiplyScalar(0.55).lerp(tonos.asfalto, 0.1);
      const cVolc = lin(COL.tierra_media).lerp(tonos.secundario, 0.15).multiplyScalar(oscuro ? 0.8 : 0.88), cVolcV = tonos.verde.clone().multiplyScalar(0.7);
      const cCasco = tonos.muro.clone().lerp(lin(COL.costa), 0.25), cCascoO = tonos.secundario.clone().lerp(tonos.muro, 0.35).multiplyScalar(0.8);
      const cCayuco = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.25).multiplyScalar(0.62);
      const cAve = tonos.asfalto.clone().lerp(tonos.linea, 0.1).multiplyScalar(oscuro ? 0.9 : 0.45), cPico = tonos.muro.clone().lerp(lin(COL.costa), 0.4);
      const cHumo = tonos.muro.clone().lerp(tonos.secundario, 0.15), cLuz = lin(COL.luces), cBrillo = tonos.agua.clone().lerp(lin(COL.costa), 0.7);
      const cCarga = lin(COL.tierra_alta).lerp(tonos.arena, 0.35).multiplyScalar(0.8);
      const OCT = [new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array, new THREE.OctahedronGeometry(1, 1).toNonIndexed().attributes.position.array];

      // ---- caras con la luz horneada (4 puntos; ref = hacia dónde es «afuera»)
      const cara = (acc, P, col, ref) => {
        const [A, B, , D] = P, e1 = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], e2 = [D[0] - A[0], D[1] - A[1], D[2] - A[2]];
        let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
        const n = Math.hypot(nx, ny, nz) || 1; nx /= n; ny /= n; nz /= n;
        if (ref ? nx * ref[0] + ny * ref[1] + nz * ref[2] < 0 : ny < 0) { nx = -nx; ny = -ny; nz = -nz; }
        const l = sombra(nx, ny, nz), q = acc.pos.length / 3;
        for (const v of P) { acc.pos.push(v[0], v[1], v[2]); acc.col.push(col.r * l, col.g * l, col.b * l); }
        acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
      };
      const bx = (acc, X, x0, x1, y0, y1, z0, z1, col, op = {}) => {
        const C = X((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
        const F = [[[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]], [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]],
          [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]],
          [[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]], [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]]];
        F.forEach((q, k) => {
          if ((k === 0 && op.sinTope) || (k === 5 && !op.fondo)) return;
          const V = q.map((a) => X(a[0], a[1], a[2])), m = [0, 1, 2].map((j) => (V[0][j] + V[1][j] + V[2][j] + V[3][j]) / 4 - C[j]);
          cara(acc, V, k === 0 && op.tope ? op.tope : (op.lados && k > 0 ? op.lados : col), m);
        });
      };
      const tubo = (acc, A, B, r, seg, col, tapa) => {
        const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], l = Math.hypot(...d) || 1, a = d.map((x) => x / l);
        let p1 = Math.abs(a[1]) < 0.9 ? [a[2], 0, -a[0]] : [1, 0, 0]; const pl = Math.hypot(...p1) || 1; p1 = p1.map((x) => x / pl);
        const p2 = [a[1] * p1[2] - a[2] * p1[1], a[2] * p1[0] - a[0] * p1[2], a[0] * p1[1] - a[1] * p1[0]];
        const o = (t) => [0, 1, 2].map((j) => (Math.cos(t) * p1[j] + Math.sin(t) * p2[j]) * r), S = (P, v) => [P[0] + v[0], P[1] + v[1], P[2] + v[2]];
        for (let i = 0; i < seg; i++) {
          const t0 = TAU * i / seg, t1 = TAU * (i + 1) / seg, va = o(t0), vb = o(t1);
          cara(acc, [S(A, va), S(A, vb), S(B, vb), S(B, va)], col, o((t0 + t1) / 2));
          if (tapa) { cara(acc, [S(B, va), S(B, vb), B, B], tapa, a); }
        }
      };
      const gema = (acc, P, rx, ry, rz, rot, col, fino) => {
        const oct = OCT[fino ? 1 : 0], cr = Math.cos(rot), sr = Math.sin(rot), c = new THREE.Color();
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
      const XL = (x, y, z) => [x, y, z];

      return piezas.map((p, np) => {
        const K = p.tamano, M = metros(1) * K;
        const r = p.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = p.semilla * 7919 + np * 104729, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.suelo ? ctx.suelo(p.x, p.y) : ctx.altura(p.x, p.y);
        const W = (u, v) => [p.x + (u * ux - v * uy) * M, p.y + (u * uy + v * ux) * M];
        const E = (u, v, h) => { const [x, y] = W(u, v); return [x, base0 + h * M, -y]; };
        const XW = (x, y, z) => E(x, z, y);
        const cw = (acc, u0, u1, v0, v1, h0, h1, col, op) => bx(acc, XW, u0, u1, h0, h1, v0, v1, col, op);
        const twu = (acc, u0, v0, h0, u1, v1, h1, rr, seg, col, tapa) => tubo(acc, E(u0, v0, h0), E(u1, v1, h1), rr * M, seg, col, tapa);
        const quad = (acc, P4, col, ref) => cara(acc, P4.map(([u, v, h]) => E(u, v, h)), col, ref || [0, 1, 0]);
        const haciaU = (s) => [s * ux, 0.15, -s * uy], haciaV = (s) => [-s * uy, 0.15, -s * ux];
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // una losa en cuadrícula (u, v) a la altura h(u, v), con el color de cada celda
        const losa = (acc, u0, u1, v0, v1, cu, cv, hf, colf) => {
          const nu = Math.max(1, Math.round((u1 - u0) / cu)), nv = Math.max(1, Math.round((v1 - v0) / cv)), l = sombra(0, 1, 0), q0 = acc.pos.length / 3;
          for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) {
            const uu = u0 + (u1 - u0) * i / nu, vv = v0 + (v1 - v0) * j / nv, P = E(uu, vv, hf(uu, vv)), c = colf(uu, vv);
            acc.pos.push(P[0], P[1], P[2]); acc.col.push(c.r * l, c.g * l, c.b * l);
          }
          for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) { const a = q0 + i * (nv + 1) + j, b = a + nv + 1; acc.idx.push(a, b, b + 1, a, b + 1, a + 1); }
        };
        const nueva = () => malla.nueva();
        const mats = [];
        const poner = (acc, op, orden) => { if (!acc.idx.length) return null; const m = new THREE.Mesh(malla.geometria(acc), malla.material(op || {})); m.frustumCulled = false; m.renderOrder = orden || 3; scene.add(m); mats.push(m.material); return m; };
        const ep = p.epoca === "hoy" ? "hoy" : "antes", HOY = ep === "hoy";
        const useco = SECO_M * clamp(p.seco, 0, 1), TUL = clamp(p.tul, 0, 1);
        const suelo = nueva(), agua = nueva(), solido = nueva(), techos = nueva(), vid = nueva(), plantas = nueva(), tul = nueva();

        // ================= el lago: agua con su tono por hondura (más claro y verdoso en el agua baja) y la playa
        const uA0 = useco;
        losa(agua, uA0, 760, -LV, LV, 20, 20, () => HA, (u, v) => {
          const f = clamp((u - uA0) / 160, 0, 1), n = ruido(u, v, 90, 3);
          return cAguaB.clone().lerp(cAgua, clamp(f * 2.2, 0, 1)).lerp(cAguaH, clamp(f - 0.3, 0, 1) * 0.9).multiplyScalar(0.95 + 0.08 * n);
        });
        // la playa en rampa (de la tierra al agua) y, con seco, el lecho de lodo que quedó al aire
        losa(suelo, U_PLAYA, 0, -LV, LV, 2.5, 6, (u) => HL + (HA + 0.04 - HL) * (u - U_PLAYA) / (-U_PLAYA), (u, v) =>
          cArena.clone().lerp(cArenaM, clamp((u + 3) / 3, 0, 1)).multiplyScalar(0.92 + 0.1 * ruido(u, v, 7, 5)));
        if (useco > 0.5) losa(suelo, 0, uA0 + 0.5, -LV, LV, Math.max(1, useco / 6), 6, (u) => HA + 0.04 - 0.035 * u / (uA0 + 0.5), (u, v) =>
          cLodo.clone().lerp(cArenaM, clamp(1 - u / (uA0 + 0.5), 0, 1) * 0.45).multiplyScalar(0.9 + 0.14 * ruido(u, v, 5, 6)));
        // la tierra (pasto con manchas) y el talud de la playa
        losa(suelo, -380, U_PLAYA, -LV, LV, 14, 14, () => HL, (u, v) => cPasto.clone().lerp(cPasto2, ruido(u, v, 40, 7)).multiplyScalar(0.92 + 0.12 * ruido(u, v, 9, 8)));
        // piedras sueltas en la orilla
        for (let i = 0; i < 90; i++) {
          const v = -LV * 0.45 + LV * 0.9 * hz(i, 11), u = -2.5 + 3 * hz(i, 12) + useco * hz(i, 13), rr = 0.25 + 0.5 * hz(i, 14);
          if (Math.abs(v) < 6) continue;
          gema(solido, E(u, v, HA + 0.08), rr * M, rr * 0.55 * M, rr * 0.8 * M, hz(i, 15) * TAU, cArenaM.clone().lerp(tonos.asfalto, 0.35).multiplyScalar(0.8 + 0.3 * hz(i, 16)));
        }

        // ================= el camino (tierra con huellas o asfalto con su raya) y el acceso al muelle
        const UC = U_CAMINO, AC = 3.6;
        if (p.camino === "asfalto") {
          losa(suelo, UC - AC, UC + AC, -LV, LV, AC, 8, () => HL + 0.05, () => cAsfalto);
          for (let v = -LV; v < LV; v += 8) quad(suelo, [[UC - 0.07, v, HL + 0.07], [UC + 0.07, v, HL + 0.07], [UC + 0.07, v + 4, HL + 0.07], [UC - 0.07, v + 4, HL + 0.07]], cRaya);
          for (const s of [-1, 1]) quad(suelo, [[UC + s * (AC - 0.25), -LV, HL + 0.07], [UC + s * (AC - 0.15), -LV, HL + 0.07], [UC + s * (AC - 0.15), LV, HL + 0.07], [UC + s * (AC - 0.25), LV, HL + 0.07]], cRaya);
          for (const s of [-1, 1]) losa(suelo, UC + s * AC - (s < 0 ? 1.2 : 0), UC + s * AC + (s > 0 ? 1.2 : 0), -LV, LV, 1.2, 10, () => HL + 0.03, (u, v) => cCamino.clone().multiplyScalar(0.92 + 0.1 * ruido(u, v, 6, 9)));
        } else {
          losa(suelo, UC - AC - 0.8, UC + AC + 0.8, -LV, LV, 1.2, 8, () => HL + 0.04, (u, v) => {
            const d = Math.abs(Math.abs(u - UC) - 1.0);
            return (d < 0.4 ? cHuella : cCamino).clone().multiplyScalar(0.9 + 0.12 * ruido(u, v, 5, 10));
          });
        }
        // el acceso público al muelle: de tierra, del camino a la playa
        losa(suelo, UC + AC, U_PLAYA + 0.5, -2.2, 2.2, 3, 1.1, () => HL + 0.035, (u, v) => cCamino.clone().multiplyScalar(0.93 + 0.1 * ruido(u, v, 4, 17)));

        // ================= el muelle de madera: pilotes, largueros, tablones, bitas y escalera a la playa
        { const HM = H_MUELLE;
          for (let u = MU0 + 2; u <= MU1; u += 3) for (const s of [-1, 1]) twu(solido, u, s * (MV - 0.15), -0.4, u, s * (MV - 0.15), HM + (u >= MU1 - 1 || (u - MU0) % 12 < 1 ? 0.7 : -0.05), 0.13, 12, cMaderaO, cMadera);
          for (const s of [-1, 1]) cw(solido, MU0, MU1 + 0.2, s > 0 ? MV - 0.32 : -MV, s > 0 ? MV : -MV + 0.32, HM - 0.35, HM - 0.06, cMaderaO);
          for (let u = MU0 + 2; u <= MU1; u += 3) cw(solido, u - 0.1, u + 0.1, -MV - 0.05, MV + 0.05, HM - 0.32, HM - 0.12, cMaderaO);
          for (let u = MU0, i = 0; u < MU1 + 0.2; u += 0.3, i++) cw(solido, u, u + 0.27, -MV - 0.08, MV + 0.08, HM - 0.06, HM, cMadera.clone().multiplyScalar(0.86 + 0.2 * hz(i, 20)));
          // bitas en la punta y la escalera a la playa
          for (const s of [-1, 1]) twu(solido, MU1 - 1.2, s * (MV - 0.4), HM, MU1 - 1.2, s * (MV - 0.4), HM + 0.45, 0.13, 12, cMaderaO, cMaderaO);
          for (let k = 0; k < 4; k++) cw(solido, MU0 - 0.6 - k * 0.5, MU0 - 0.1 - k * 0.5, -1.1, 1.1, 0, HM - 0.3 * (k + 1), tonos.arena.clone().lerp(cMadera, 0.8));
        }

        // ================= el tular: manchas de tul y enea en el agua baja (fijo en u; con seco, parte queda al aire)
        const TU0 = 5, TU1 = 5 + 34 * Math.max(0.25, TUL);
        const enAgua = (u) => u > uA0;
        const manchas = [];
        if (TUL > 0.01) {
          const NC = Math.round(2200 * TUL);
          for (let i = 0; i < NC; i++) {
            const lado = hz(i, 30) < 0.62 ? 1 : -1;
            const v = lado > 0 ? 26 + 190 * hz(i, 31) : -(56 + 150 * hz(i, 31));
            const u = TU0 + (TU1 - TU0) * Math.pow(hz(i, 32), 0.8);
            const n = ruido(u, v, 14, 33);
            if (n < 0.3 + 0.25 * (1 - TUL)) continue;
            const seco = !enAgua(u), enea = ruido(u, v, 9, 34) > 0.62, h0 = seco ? HA + 0.04 : HA;
            const alto = (enea ? 1.7 : 2.2) + 1.0 * hz(i, 35);
            const nb = 7 + Math.floor(5 * hz(i, 36));
            for (let b = 0; b < nb; b++) {
              const a = TAU * hz(i * 9 + b, 37), d = 0.25 * hz(i * 9 + b, 38), uu = u + d * Math.cos(a), vv = v + d * Math.sin(a);
              const inc = 0.35 * hz(i * 9 + b, 39), ia = TAU * hz(i * 9 + b, 40), hh = alto * (0.7 + 0.35 * hz(i * 9 + b, 41));
              const w = enea ? 0.11 : 0.08, tu = uu + inc * Math.cos(ia), tv = vv + inc * Math.sin(ia);
              const cb = (seco ? cTulSeco : cTul).clone().multiplyScalar(0.8 + 0.25 * hz(i * 9 + b, 42)), ct = seco ? cTulSeco.clone().multiplyScalar(1.1) : cTulP;
              const P = [E(uu - w * Math.sin(ia), vv + w * Math.cos(ia), h0), E(uu + w * Math.sin(ia), vv - w * Math.cos(ia), h0), E(tu, tv, h0 + hh), E(tu, tv, h0 + hh)];
              const q = tul.pos.length / 3, l = 0.92;
              for (let k = 0; k < 4; k++) { const c = k < 2 ? cb : ct; tul.pos.push(P[k][0], P[k][1], P[k][2]); tul.col.push(c.r * l, c.g * l, c.b * l); }
              tul.idx.push(q, q + 1, q + 2);
              // y su cara cruzada (que se lea de cualquier lado)
              const P2 = [E(uu - w * Math.cos(ia), vv - w * Math.sin(ia), h0), E(uu + w * Math.cos(ia), vv + w * Math.sin(ia), h0), E(tu, tv, h0 + hh)];
              const q2 = tul.pos.length / 3;
              for (let k = 0; k < 3; k++) { const c = k < 2 ? cb.clone().multiplyScalar(0.85) : ct; tul.pos.push(P2[k][0], P2[k][1], P2[k][2]); tul.col.push(c.r * l, c.g * l, c.b * l); }
              tul.idx.push(q2, q2 + 1, q2 + 2);
              if (enea && b < 2) twu(tul, uu + (tu - uu) * 0.78, vv + (tv - vv) * 0.78, h0 + hh * 0.78, uu + (tu - uu) * 0.92, vv + (tv - vv) * 0.92, h0 + hh * 0.92, 0.05, 6, cEspiga, cEspiga);
            }
            if (manchas.length < 40 && hz(i, 43) < 0.08) manchas.push([u, v]);
          }
          // manojos de tul cortado secándose en la playa (de pie, en cono)
          const NM = Math.round(3 + 6 * TUL);
          for (let i = 0; i < NM; i++) {
            const v = 30 + 150 * hz(i, 44), u = -6 + 4 * hz(i, 45), h0 = HL + (HA + 0.04 - HL) * (u - U_PLAYA) / (-U_PLAYA);
            for (let b = 0; b < 14; b++) {
              const a = TAU * b / 14 + hz(i, 46), rb = 0.35, P0 = E(u + rb * Math.cos(a), v + rb * Math.sin(a), h0), Pt = E(u, v, h0 + 1.5 + 0.2 * hz(i * 14 + b, 47));
              cara(plantas, [P0, E(u + rb * Math.cos(a + 0.4), v + rb * Math.sin(a + 0.4), h0), Pt, Pt], cTulSeco.clone().multiplyScalar(0.85 + 0.3 * hz(i * 14 + b, 48)), [Math.cos(a), 0.2, -Math.sin(a)]);
            }
          }
        }

        // ================= una casa: muros con zócalo, puertas, ventanas (con reja o con luz), corredor y techo
        // (u0..u1 hacia el lago, v0..v1 a lo largo; la fachada principal mira a +u si `frente` 1, a −u si −1)
        const ventana = (uF, v, h, ancho, alto, frente, reja, k) => {
          const d = frente * 0.04;
          quad(vid, [[uF + d, v - ancho / 2, h], [uF + d, v + ancho / 2, h], [uF + d, v + ancho / 2, h + alto], [uF + d, v - ancho / 2, h + alto]], cVidrio.clone().multiplyScalar(noche ? (hz(k, 60) < 0.7 ? 1 : 0.25) : 1), haciaU(frente));
          cw(solido, uF + (frente > 0 ? 0 : -0.12), uF + (frente > 0 ? 0.12 : 0), v - ancho / 2 - 0.1, v + ancho / 2 + 0.1, h - 0.12, h, cZocalo);   // el alféizar
          if (reja) for (let j = 1; j < 5; j++) { const vv = v - ancho / 2 + ancho * j / 5; cw(solido, uF + d - 0.03, uF + d + 0.05, vv - 0.025, vv + 0.025, h, h + alto, cReja); }
        };
        const ventanaLado = (u, vF, h, ancho, alto, lado, k) => {
          const d = lado * 0.04;
          quad(vid, [[u - ancho / 2, vF + d, h], [u + ancho / 2, vF + d, h], [u + ancho / 2, vF + d, h + alto], [u - ancho / 2, vF + d, h + alto]], cVidrio.clone().multiplyScalar(noche ? (hz(k, 61) < 0.6 ? 1 : 0.25) : 1), haciaV(lado));
        };
        const techo4 = (acc, u0, u1, v0, v1, h0, alto, vuelo, col, colO) => {
          const a0 = u0 - vuelo, a1 = u1 + vuelo, b0 = v0 - vuelo, b1 = v1 + vuelo, lu = a1 - a0, lv = b1 - b0;
          const e = Math.min(lu, lv) / 2, hc = h0 + alto;
          let R0, R1;
          if (lv >= lu) { R0 = [(a0 + a1) / 2, b0 + e]; R1 = [(a0 + a1) / 2, b1 - e]; } else { R0 = [a0 + e, (b0 + b1) / 2]; R1 = [a1 - e, (b0 + b1) / 2]; }
          const P = (u, v, h) => E(u, v, h), C = E((a0 + a1) / 2, (b0 + b1) / 2, h0 - 2);
          const caraT = (A, B, Cc, D, c) => { const m = [0, 1, 2].map((j) => (A[j] + B[j] + Cc[j] + D[j]) / 4 - C[j]); cara(acc, [A, B, Cc, D], c, m); };
          if (lv >= lu) {
            caraT(P(a1, b0, h0), P(a1, b1, h0), P(R1[0], R1[1], hc), P(R0[0], R0[1], hc), col);
            caraT(P(a0, b1, h0), P(a0, b0, h0), P(R0[0], R0[1], hc), P(R1[0], R1[1], hc), col);
            caraT(P(a0, b0, h0), P(a1, b0, h0), P(R0[0], R0[1], hc), P(R0[0], R0[1], hc), colO);
            caraT(P(a1, b1, h0), P(a0, b1, h0), P(R1[0], R1[1], hc), P(R1[0], R1[1], hc), colO);
          } else {
            caraT(P(a0, b1, h0), P(a1, b1, h0), P(R1[0], R1[1], hc), P(R0[0], R0[1], hc), col);
            caraT(P(a1, b0, h0), P(a0, b0, h0), P(R0[0], R0[1], hc), P(R1[0], R1[1], hc), col);
            caraT(P(a0, b0, h0), P(a0, b1, h0), P(R0[0], R0[1], hc), P(R0[0], R0[1], hc), colO);
            caraT(P(a1, b1, h0), P(a1, b0, h0), P(R1[0], R1[1], hc), P(R1[0], R1[1], hc), colO);
          }
          // el canto del alero
          for (const [A, B] of [[[a0, b0], [a1, b0]], [[a1, b0], [a1, b1]], [[a1, b1], [a0, b1]], [[a0, b1], [a0, b0]]])
            cara(acc, [P(A[0], A[1], h0), P(B[0], B[1], h0), P(B[0], B[1], h0 - 0.14), P(A[0], A[1], h0 - 0.14)], colO.clone().multiplyScalar(0.8), [(A[0] + B[0]) / 2 - (a0 + a1) / 2 > 0 ? ux : -ux, 0, 0]);
          // las hileras de teja (o los surcos de la paja): líneas a lo largo de la pendiente en las dos caras largas
          return { a0, a1, b0, b1, hc, R0, R1 };
        };
        const surcosTecho = (T, h0, col, paso) => {
          const { a0, a1, b0, b1, hc, R0, R1 } = T;
          if (b1 - b0 >= a1 - a0) {
            for (let v = b0 + paso; v < b1 - 0.01; v += paso) for (const [ae, ar] of [[a1, R0[0]], [a0, R0[0]]]) {
              const vr = clamp(v, R0[1], R1[1]), f = 0.012;
              quad(techos, [[ae, v - 0.05, h0 + f], [ae, v + 0.05, h0 + f], [ar, vr + 0.05, hc + f], [ar, vr - 0.05, hc + f]], col);
            }
          } else {
            for (let u = a0 + paso; u < a1 - 0.01; u += paso) for (const [be, br] of [[b1, R0[1]], [b0, R0[1]]]) {
              const ur = clamp(u, R0[0], R1[0]), f = 0.012;
              quad(techos, [[u - 0.05, be, h0 + f], [u + 0.05, be, h0 + f], [ur + 0.05, br, hc + f], [ur - 0.05, br, hc + f]], col);
            }
          }
        };
        // un cuerpo de casa: pisos, muros, zócalo, cornisa entre pisos, puertas y ventanas en las cuatro caras
        const cuerpo = (u0, u1, v0, v1, h0, pisos, hp, colM, op, k) => {
          const H = h0 + pisos * hp;
          cw(solido, u0, u1, v0, v1, h0, H, colM, { sinTope: true });
          cw(solido, u0 - 0.06, u1 + 0.06, v0 - 0.06, v1 + 0.06, h0, h0 + 0.45, cZocalo, { sinTope: true });
          for (let f = 1; f < pisos; f++) cw(solido, u0 - 0.1, u1 + 0.1, v0 - 0.1, v1 + 0.1, h0 + f * hp - 0.12, h0 + f * hp + 0.06, colM.clone().multiplyScalar(0.86));
          cw(solido, u0 - 0.12, u1 + 0.12, v0 - 0.12, v1 + 0.12, H - 0.18, H, colM.clone().multiplyScalar(0.84));
          for (let f = 0; f < pisos; f++) {
            const hv = h0 + f * hp + 1.0, hw = Math.min(1.4, hp - 1.5);
            for (const fr of [1, -1]) {
              const uF = fr > 0 ? u1 : u0, paso = op.paso || 3.2, n = Math.max(1, Math.floor((v1 - v0 - 1) / paso));
              for (let j = 0; j < n; j++) {
                const v = v0 + (v1 - v0) * (j + 0.5) / n;
                if (f === 0 && j === Math.floor(n / 2) && (fr > 0 || op.puertaAtras)) {
                  quad(vid, [[uF + fr * 0.04, v - 0.6, h0 + 0.02], [uF + fr * 0.04, v + 0.6, h0 + 0.02], [uF + fr * 0.04, v + 0.6, h0 + 2.3], [uF + fr * 0.04, v - 0.6, h0 + 2.3]], noche ? cVidrio.clone().multiplyScalar(0.7) : cHueco, haciaU(fr));
                  cw(solido, uF - 0.08, uF + 0.08, v - 0.72, v + 0.72, h0 + 2.3, h0 + 2.45, cMaderaO);
                } else ventana(uF, v, hv, op.vancho || 1.0, hw, fr, op.reja, k * 31 + f * 7 + j + (fr > 0 ? 0 : 500));
              }
            }
            for (const lado of [1, -1]) {
              const n = Math.max(0, Math.floor((u1 - u0 - 2) / 4));
              for (let j = 0; j < n; j++) ventanaLado(u0 + (u1 - u0) * (j + 0.5) / n, lado > 0 ? v1 : v0, hv, 0.9, hw, lado, k * 37 + f * 5 + j + (lado > 0 ? 900 : 0));
            }
          }
          return H;
        };
        const arbol = (u, v, h0, alto, k, colH) => {
          twu(plantas, u, v, h0, u, v, h0 + alto * 0.45, 0.09 * alto * 0.4 + 0.08, 8, cTronco, null);
          const nc = 2 + Math.floor(2 * hz(k, 70));
          for (let c = 0; c < nc; c++) {
            const a = TAU * hz(k * 5 + c, 71), d = alto * 0.12 * hz(k * 5 + c, 72), rr = alto * (0.26 + 0.1 * hz(k * 5 + c, 73));
            gema(plantas, E(u + d * Math.cos(a), v + d * Math.sin(a), h0 + alto * (0.58 + 0.16 * hz(k * 5 + c, 74))), rr * M, rr * 0.78 * M, rr * M, hz(k * 5 + c, 75) * TAU,
              (colH || cHoja).clone().multiplyScalar(0.82 + 0.3 * hz(k * 5 + c, 76)), true);
          }
        };

        // ================= los lotes: hoteles bajos y casas de campo con jardín (ranuras fijas; `construcciones` las llena)
        const luces = [];   // [u, v, h, a]: puntos de luz de noche
        const NL = Math.round(clamp(p.construcciones, 0, 1) * LOTES[ep].length);
        const LU0 = -14, LU1 = -80;
        const ocupados = LOTES[ep].slice(0, NL);
        let hotel1 = null;
        // `dispersion`: las casas de campo dejan de ir en fila (corridas, de tamaños y giros distintos, sin lindero continuo,
        // algún lote vacío); los hoteles se quedan en su ranura
        const D = clamp(+p.dispersion || 0, 0, 1);
        ocupados.forEach(([vc0, tipo], i) => {
          const k = 100 + i * 13, vs = 17, esC = tipo === "c", vc = vc0 + (esC ? D * (hz(k, 127) - 0.5) * 14 : 0);
          if (esC && hz(k, 125) < D * 0.22) { for (let j = 0; j < 3; j++) arbol(-24 - 40 * hz(k + j, 97), vc + (hz(k + j, 98) - 0.5) * 26, HL, 6 + 5 * hz(k + j, 99), k * 11 + j); return; }
          const conLindero = !esC || hz(k, 126) >= D * 0.75, uL = LU1 + (esC ? D * hz(k, 128) * 22 : 0);
          // el césped del lote y su lindero (seto antes; muro hoy) con su portón al camino
          losa(suelo, uL + 0.5, LU0 - 0.5, vc - vs * (1 - 0.3 * D * hz(k, 129)), vc + vs * (1 - 0.3 * D * hz(k, 130)), 3, 3, () => HL + 0.02, (u, v) => cCesped.clone().multiplyScalar(0.9 + 0.12 * ruido(u, v, 6, k)));
          if (conLindero) for (const s of [-1, 1]) {
            if (HOY) cw(solido, LU1, LU0 - 3, vc + s * vs - 0.15, vc + s * vs + 0.15, HL, HL + 1.6, cMuro.clone().multiplyScalar(0.95), { tope: cZocalo });
            else for (let u = LU1 + 0.6; u < LU0 - 3; u += 1.4) gema(plantas, E(u, vc + s * vs, HL + 0.55), 0.85 * M, 0.7 * M, 0.6 * M, hz(k + u | 0, 77), cSeto.clone().multiplyScalar(0.85 + 0.25 * hz(k * 3 + (u | 0), 78)));
          }
          if (!conLindero) { /* sin lindero: el jardín se abre al pasto */ } else if (HOY) { cw(solido, LU1 - 0.3, LU1 + 0.3, vc - vs, vc - 3, HL, HL + 1.8, cMuro, { tope: cZocalo }); cw(solido, LU1 - 0.3, LU1 + 0.3, vc + 3, vc + vs, HL, HL + 1.8, cMuro, { tope: cZocalo }); }
          else for (let v = vc - vs + 0.8; v < vc + vs; v += 1.4) if (Math.abs(v - vc) > 2.5) gema(plantas, E(LU1 + 0.4, v, HL + 0.55), 0.6 * M, 0.7 * M, 0.85 * M, 0, cSeto.clone().multiplyScalar(0.85 + 0.25 * hz(k * 7 + (v | 0), 79)));
          // el sendero del portón a la casa y de la casa a la playa
          for (let u = uL + 1; u < U_PLAYA; u += 1.6) { const vv = vc + 0.6 * Math.sin(u * 0.15 + k); quad(suelo, [[u, vv - 0.45, HL + 0.04], [u + 1.1, vv - 0.45, HL + 0.04], [u + 1.1, vv + 0.45, HL + 0.04], [u, vv + 0.45, HL + 0.04]], cArena.clone().multiplyScalar(0.92 + 0.12 * hz(k + (u | 0), 80))); }
          if (tipo === "h") {
            // hotel: cuerpo largo a lo largo de la orilla, un ala atrás, corredor de columnas hacia el lago
            const pisos = HOY ? 3 : (i === 0 ? 2 : 1), hp = 3.2, cu0 = -52, cu1 = -40, cv0 = vc - 13, cv1 = vc + 13;
            const colM = cMuro.clone().multiplyScalar(0.94 + 0.08 * hz(k, 81));
            const H = cuerpo(cu0, cu1, cv0, cv1, HL, pisos, hp, colM, { paso: 3.0, reja: false, puertaAtras: true }, k);
            const T = techo4(techos, cu0, cu1, cv0, cv1, H, 2.4, 0.7, cTechoG.clone().multiplyScalar(0.95 + 0.1 * hz(k, 82)), cTechoG.clone().multiplyScalar(0.8)); surcosTecho(T, H, cTechoG.clone().multiplyScalar(0.78), 0.55);
            // el ala de atrás (un piso)
            const H2 = cuerpo(-70, cu0, vc + 3, vc + 11, HL, 1, hp, colM, { paso: 3.2 }, k + 3);
            const T2 = techo4(techos, -70, cu0 - 0.6, vc + 3, vc + 11, H2, 1.8, 0.6, cTechoG, cTechoG.clone().multiplyScalar(0.8)); surcosTecho(T2, H2, cTechoG.clone().multiplyScalar(0.78), 0.55);
            // el corredor: losa, columnas con basa y capitel, viga y su techo de un agua
            const cu2 = cu1 + 3.2;
            cw(solido, cu1, cu2, cv0, cv1, HL, HL + 0.32, cZocalo, { tope: cArena.clone().lerp(cMuro, 0.5) });
            for (let v = cv0 + 0.3; v <= cv1 - 0.2; v += (cv1 - cv0 - 0.5) / 8) {
              twu(solido, cu2 - 0.3, v, HL + 0.32, cu2 - 0.3, v, HL + hp - 0.15, 0.14, 12, cMuro.clone().multiplyScalar(1.03), null);
              cw(solido, cu2 - 0.52, cu2 - 0.08, v - 0.22, v + 0.22, HL + 0.32, HL + 0.55, cZocalo);
            }
            cw(solido, cu1, cu2, cv0 - 0.2, cv1 + 0.2, HL + hp - 0.22, HL + hp, cMaderaO);
            quad(techos, [[cu1, cv0 - 0.4, HL + hp + 0.75], [cu1, cv1 + 0.4, HL + hp + 0.75], [cu2 + 0.6, cv1 + 0.4, HL + hp - 0.05], [cu2 + 0.6, cv0 - 0.4, HL + hp - 0.05]], cTechoG.clone().multiplyScalar(0.9));
            // barandal del corredor entre columnas (antes de madera)
            cw(solido, cu2 - 0.36, cu2 - 0.24, cv0, cv1, HL + 1.0, HL + 1.08, cMaderaO);
            // mesas y sillas en el corredor; una terraza con bancas frente al lago
            for (let j = 0; j < 3; j++) { const v = cv0 + 4 + j * 9; twu(solido, cu1 + 1.6, v, HL + 0.32, cu1 + 1.6, v, HL + 1.05, 0.05, 8, cMaderaO, null); twu(solido, cu1 + 1.6, v, HL + 1.05, cu1 + 1.6, v, HL + 1.09, 0.45, 14, cMadera, cMadera); }
            for (let j = 0; j < 2; j++) cw(solido, -24, -22.8, vc - 8 + j * 16, vc - 5 + j * 16, HL, HL + 0.45, cMadera, { tope: cMaderaC });
            for (let j = 0; j < 5; j++) arbol(-30 + 12 * hz(k + j, 83), vc + (hz(k + j, 84) - 0.5) * 28, HL, 6 + 4 * hz(k + j, 85), k * 9 + j);
            luces.push([cu2 - 0.2, vc - 6, HL + hp - 0.3, 0.6], [cu2 - 0.2, vc + 6, HL + hp - 0.3, 0.6]);
            if (!hotel1) hotel1 = [cu2 + 1.2, vc];
          } else {
            // casa de campo: cuerpo de un piso con corredor al lago, jardín con arriates y árboles
            const giro = D > 0.3 && hz(k, 124) < 0.5 * D;
            const lu = (giro ? 12 : 9) * (1 + D * (hz(k, 121) - 0.5) * 0.5), lv = (giro ? 8 : 14 + 2 * hz(k, 87)) * (1 + D * (hz(k, 122) - 0.5) * 0.6);
            const cu0 = -48 + 4 * hz(k, 86) + D * (hz(k, 120) - 0.5) * 26 - (lu - 9) / 2, cu1 = cu0 + lu, cv0 = vc - lv / 2, cv1 = vc + lv / 2, hp = 3.0, pisos = HOY && hz(k, 88) < 0.5 ? 2 : 1;
            const colM = (hz(k, 89) < 0.5 ? cMuro : cEncal).clone().multiplyScalar(0.93 + 0.1 * hz(k, 90));
            const H = cuerpo(cu0, cu1, cv0, cv1, HL, pisos, hp, colM, { paso: 3.4 }, k);
            const cT = cTechoG.clone().lerp(hz(k, 131) < 0.5 ? cTejaO : cMuro, D * 0.45 * hz(k, 132)).multiplyScalar(0.9 + 0.15 * hz(k, 91));
            const T = techo4(techos, cu0, cu1, cv0, cv1, H, 2.0 * (1 + D * (hz(k, 133) - 0.5) * 0.6), 0.6, cT, cT.clone().multiplyScalar(0.82)); surcosTecho(T, H, cT.clone().multiplyScalar(0.8), 0.55);
            cw(solido, cu1, cu1 + 2.6, cv0, cv1, HL, HL + 0.25, cZocalo, { tope: cArena.clone().lerp(cMuro, 0.5) });
            for (const v of [cv0 + 0.25, (cv0 + cv1) / 2, cv1 - 0.25]) twu(solido, cu1 + 2.35, v, HL + 0.25, cu1 + 2.35, v, HL + 2.7, 0.11, 12, cMaderaO, null);
            quad(techos, [[cu1, cv0 - 0.3, HL + 3.3], [cu1, cv1 + 0.3, HL + 3.3], [cu1 + 3.0, cv1 + 0.3, HL + 2.65], [cu1 + 3.0, cv0 - 0.3, HL + 2.65]], cTechoG.clone().multiplyScalar(0.88));
            // arriates con flores (puntos de color) junto al corredor
            for (let j = 0; j < 14; j++) { const v = cv0 + (cv1 - cv0) * j / 13, u = cu1 + 3.3;
              gema(plantas, E(u, v, HL + 0.25), 0.45 * M, 0.35 * M, 0.45 * M, j, cSeto.clone().multiplyScalar(1.05));
              if (hz(k + j, 92) < 0.6) gema(plantas, E(u + 0.1, v, HL + 0.62), 0.14 * M, 0.12 * M, 0.14 * M, 0, [tonos.mal, tonos.medio, tonos.muro][j % 3].clone().multiplyScalar(0.95)); }
            for (let j = 0; j < 4; j++) {
              const au = -26 + 10 * hz(k + j, 93); let av = vc + (hz(k + j, 94) - 0.5) * 26;
              if (au > cu0 - 2 && au < cu1 + 4.5 && Math.abs(av - vc) < lv / 2 + 2.5) av = vc + Math.sign(av - vc || 1) * (lv / 2 + 3 + 2 * hz(k + j, 134));
              arbol(au, av, HL, 5 + 4 * hz(k + j, 95), k * 7 + j, hz(k + j, 96) < 0.5 ? cHoja : cHoja2);
            }
            luces.push([cu1 + 2.3, vc, HL + 2.5, 0.45]);
          }
        });
        // donde no hay lote: pasto con árboles sueltos
        LOTES[ep].slice(NL).forEach(([vc], i) => { for (let j = 0; j < 3; j++) arbol(-30 - 40 * hz(300 + i * 5 + j, 97), vc + (hz(300 + i * 5 + j, 98) - 0.5) * 30, HL, 6 + 5 * hz(300 + i * 5 + j, 99), 300 + i * 5 + j); });
        // árboles de orilla a lo largo de la playa (sauces y otros, genéricos)
        for (let i = 0; i < 26; i++) { const v = -200 + 400 * (i + hz(i, 101) * 0.6) / 26; if (Math.abs(v) < 8) continue; arbol(-11.5 - 1.5 * hz(i, 102), v, HL, 7 + 5 * hz(i, 103), 600 + i, hz(i, 104) < 0.5 ? cHoja2 : cHoja); }

        // ================= los huertos (surcos) detrás del camino
        { const H0 = HL + 0.03, uA = UC - AC - 6, uB = uA - 32;
          for (let pq = 0; pq < 5; pq++) {
            const v0 = -205 + pq * 28, v1 = v0 + 25, rumboSurco = pq % 2;
            losa(suelo, uB, uA, v0, v1, 4, 4, () => H0, () => cSurco.clone().multiplyScalar(0.9 + 0.12 * hz(pq, 110)));
            if (rumboSurco) for (let u = uB + 0.9; u < uA - 0.5; u += 1.1) quad(plantas, [[u - 0.22, v0 + 0.6, H0 + 0.22], [u + 0.22, v0 + 0.6, H0 + 0.22], [u + 0.22, v1 - 0.6, H0 + 0.22], [u - 0.22, v1 - 0.6, H0 + 0.22]], cMata.clone().multiplyScalar(0.8 + 0.25 * hz(pq * 50 + (u | 0), 111)));
            else for (let v = v0 + 0.9; v < v1 - 0.5; v += 1.1) quad(plantas, [[uB + 0.6, v - 0.22, H0 + 0.22], [uA - 0.6, v - 0.22, H0 + 0.22], [uA - 0.6, v + 0.22, H0 + 0.22], [uB + 0.6, v + 0.22, H0 + 0.22]], cMata.clone().multiplyScalar(0.8 + 0.25 * hz(pq * 50 + (v | 0), 112)));
            // el bordo del huerto y una cerca de palos
            for (let v = v0; v <= v1; v += 2.5) twu(solido, uA + 0.4, v, H0, uA + 0.4, v, H0 + 1.1, 0.05, 6, cMaderaO, null);
          }
        }

        // ================= el pueblito: casas ladinas junto al camino (adobe encalado, teja, reja) y ranchos de paja entre cafetales
        const humos = [];
        { const H0 = HL;
          // con `dispersion` dejan de ir en fila: menos casas, retiradas del camino a distintas distancias, de tamaños, giros y
          // techos distintos (ninguna se encima a otra)
          const puestas = [];
          for (let i = 0; i < 9; i++) {
            if (D > 0 && hz(i, 150) < D * 0.4) continue;
            const giro = D > 0.3 && hz(i, 151) < 0.5 * D, fondo = (8 + 2 * hz(i, 121)) * (1 + D * (hz(i, 152) - 0.5) * 0.5);
            const v = -30 + i * 15 + 3 * hz(i, 120) + D * (hz(i, 153) - 0.5) * 6, u1 = UC - AC - 2.5 - D * 26 * hz(i, 154), w0 = (6 + 4 * hz(i, 122)) * (1 - 0.3 * D * hz(i, 155));
            const u0 = u1 - (giro ? w0 + 2 : fondo), w = giro ? Math.min(fondo, 9) : w0;
            if (puestas.some(([a0, a1, b0, b1]) => u0 < a1 + 1.5 && u1 > a0 - 1.5 && v - w / 2 < b1 + 1.5 && v + w / 2 > b0 - 1.5)) continue;
            puestas.push([u0, u1, v - w / 2, v + w / 2]);
            const colM = (D > 0 && hz(i, 156) < 0.4 * D ? cAdobe : cEncal).clone().multiplyScalar(0.92 + 0.1 * hz(i, 123));
            const H = cuerpo(u0, u1, v - w / 2, v + w / 2, H0, 1, 3.2 - 0.4 * D * hz(i, 157), colM, { paso: 2.8, reja: true, vancho: 0.9 }, 700 + i);
            const cT = cTeja.clone().lerp(cTechoG, D * 0.55 * hz(i, 158)).multiplyScalar(0.9 + 0.15 * hz(i, 124) - 0.12 * D * hz(i, 159));
            const T = techo4(techos, u0, u1, v - w / 2, v + w / 2, H, 1.8 * (1 + D * (hz(i, 160) - 0.5) * 0.5), 0.7, cT, cT.clone().multiplyScalar(0.8)); surcosTecho(T, H, cT.clone().multiplyScalar(0.78), 0.32);
            if (hz(i, 125) < 0.5) { cw(solido, u0 - 10, u0, v - w / 2, v - w / 2 + 0.4, H0, H0 + 2.0, cAdobe, { tope: cTejaO }); }
          }
          // el adoquín frente a las casas del centro
          losa(suelo, UC - AC - 2.5, UC - AC, D > 0.4 ? -16 : -36, D > 0.4 ? 46 : 106, 0.6, 0.6, () => HL + 0.045, (u, v) => cZocalo.clone().lerp(cArena, 0.3).multiplyScalar(0.85 + 0.25 * hz(((u * 7) | 0) * 131 + ((v * 7) | 0), 126)));
          // ranchos de caña y adobe con techo de paja, entre cafetales, lejos del camino
          for (let i = 0; i < 14; i++) {
            const u = -150 - 80 * hz(i, 130), v = -40 + 230 * hz(i, 131), lu = 4.5 + 1.5 * hz(i, 132), lv = 5.5 + 2 * hz(i, 133), cana = hz(i, 134) < 0.5;
            const u0 = u - lu / 2, u1 = u + lu / 2, v0 = v - lv / 2, v1 = v + lv / 2, hm = 2.3;
            cw(solido, u0, u1, v0, v1, H0, H0 + hm, cana ? cCana : cAdobe, { sinTope: true });
            if (cana) for (let vv = v0 + 0.15; vv < v1; vv += 0.22) for (const uF of [u0 - 0.02, u1 + 0.02]) quad(solido, [[uF, vv - 0.04, H0 + 0.1], [uF, vv + 0.04, H0 + 0.1], [uF, vv + 0.04, H0 + hm], [uF, vv - 0.04, H0 + hm]], cCana.clone().multiplyScalar(0.8), haciaU(uF > u ? 1 : -1));
            quad(vid, [[u1 + 0.05, v - 0.5, H0 + 0.02], [u1 + 0.05, v + 0.5, H0 + 0.02], [u1 + 0.05, v + 0.5, H0 + 1.9], [u1 + 0.05, v - 0.5, H0 + 1.9]], noche ? cVidrio.clone().multiplyScalar(0.55) : cHueco, haciaU(1));
            const T = techo4(techos, u0, u1, v0, v1, H0 + hm, 2.6, 0.8, cPaja.clone().multiplyScalar(0.9 + 0.15 * hz(i, 135)), cPajaO); surcosTecho(T, H0 + hm, cPajaO, 0.4);
            if (i % 3 === 0) humos.push([u, v, H0 + hm + 2.7, i]);
            // los cafetos alrededor (hileras) y un árbol de sombra
            for (let j = 0; j < 22; j++) { const a = TAU * hz(i * 40 + j, 136), d = 6 + 9 * hz(i * 40 + j, 137);
              gema(plantas, E(u + d * Math.cos(a), v + d * Math.sin(a), H0 + 0.75), 0.75 * M, 0.85 * M, 0.75 * M, a, cCafe.clone().multiplyScalar(0.8 + 0.3 * hz(i * 40 + j, 138))); }
            arbol(u + 8 * (hz(i, 139) - 0.5), v + 9, H0, 9 + 4 * hz(i, 140), 800 + i, cHoja2);
          }
          // cafetal continuo al fondo
          for (let j = 0; j < 520; j++) { const u = -235 - 120 * hz(j, 141), v = -260 + 520 * hz(j, 142);
            gema(plantas, E(u, v, H0 + 0.75), 0.8 * M, 0.85 * M, 0.8 * M, j, cCafe.clone().multiplyScalar(0.8 + 0.3 * hz(j, 143))); }
          for (let j = 0; j < 40; j++) arbol(-240 - 120 * hz(j, 144), -260 + 520 * hz(j, 145), H0, 10 + 6 * hz(j, 146), 900 + j, cHoja2);
        }

        // ================= los volcanes al fondo, tierra adentro (conos genéricos; maqueta, no a escala)
        { const VS = [[-1500, -520, 560, 900], [-1700, 300, 480, 800], [-1450, 1000, 520, 820]];
          const vol = nueva(), NR = 56, NA = 14;
          VS.forEach(([cu, cv, hh, rb], kv) => {
            const q0 = vol.pos.length / 3;
            for (let a = 0; a <= NA; a++) for (let s = 0; s < NR; s++) {
              const x = a / NA, th = TAU * s / NR, rad = rb * (0.05 + 0.95 * x) * (1 + 0.05 * Math.sin(5 * th + kv)), hgt = hh * Math.pow(1 - x, 1.35) * (1 + 0.04 * Math.sin(9 * th + kv * 2) * x);
              const P = E(cu + rad * Math.cos(th), cv + rad * Math.sin(th), hgt);
              const wx = Math.cos(th) * ux - Math.sin(th) * uy, wy = Math.cos(th) * uy + Math.sin(th) * ux, l = sombra(0.55 * wx, 0.8, -0.55 * wy), c = cVolc.clone().lerp(cVolcV, clamp((x - 0.35) * 1.6, 0, 0.85));
              vol.pos.push(P[0], P[1], P[2]); vol.col.push(c.r * l, c.g * l, c.b * l);
            }
            for (let a = 0; a < NA; a++) for (let s = 0; s < NR; s++) { const i0 = q0 + a * NR + s, i1 = q0 + a * NR + (s + 1) % NR; vol.idx.push(i0, i0 + NR, i1 + NR, i0, i1 + NR, i1); }
          });
          poner(vol, {}, 1);
        }

        // ================= las mallas fijas
        poner(agua, { desfase: 1 }, 1);
        poner(suelo, { desfase: 2 }, 2);
        poner(solido, { desfase: 1 }, 3);
        poner(techos, {}, 3);
        poner(plantas, {}, 3);
        poner(tul, {}, 3);
        const mVid = poner(vid, { desfase: 3 }, 4);
        const vidrios = mVid ? [mVid.material] : [];
        if (mVid) mats.splice(mats.indexOf(mVid.material), 1);

        // ================= los destellos del agua (titilan: función de t) y las ondas
        const ND = 220, gD = new THREE.BufferGeometry(), posD = new Float32Array(ND * 4 * 3), colD = new Float32Array(ND * 4 * 3), idxD = [];
        const DES = [];
        for (let i = 0; i < ND; i++) {
          const u = uA0 + 4 + 300 * Math.pow(hz(i, 150), 1.4), v = (hz(i, 151) - 0.5) * 420, L = 1.2 + 2.5 * hz(i, 152);
          const P = [E(u - 0.08, v - L / 2, HA + 0.02), E(u + 0.08, v - L / 2, HA + 0.02), E(u + 0.08, v + L / 2, HA + 0.02), E(u - 0.08, v + L / 2, HA + 0.02)];
          P.forEach((q, j) => posD.set(q, (i * 4 + j) * 3));
          idxD.push(i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3);
          DES.push([2 * Math.PI * hz(i, 153), 0.6 + 1.2 * hz(i, 154)]);
        }
        gD.setAttribute("position", new THREE.BufferAttribute(posD, 3)); gD.setAttribute("color", new THREE.BufferAttribute(colD, 3)); gD.setIndex(idxD);
        const matD = malla.material({ aditivo: true, desfase: 3 });
        const mD = new THREE.Mesh(gD, matD); mD.frustumCulled = false; mD.renderOrder = 5; scene.add(mD);

        // ================= las embarcaciones: lanchas (casco, toldo, motor) y cayucos (tronco excavado), en ejes locales
        const geoLancha = (() => { const a = nueva(), L = 7.5, B = 1.1;
          // casco: costados que se cierran en la proa, borda y fondo
          for (const s of [-1, 1]) {
            cara(a, [[-L / 2, 0.05, s * B * 0.85], [L * 0.2, 0.05, s * B * 0.8], [L * 0.2, 0.75, s * B], [-L / 2, 0.7, s * B * 0.95]], cCasco, [0, 0, s]);
            cara(a, [[L * 0.2, 0.05, s * B * 0.8], [L / 2, 0.45, 0], [L / 2, 0.95, 0], [L * 0.2, 0.75, s * B]], cCasco, [s * 0.3, 0, s]);
            cara(a, [[-L / 2, 0.7, s * B * 0.95], [L * 0.2, 0.75, s * B], [L * 0.2, 0.62, s * B * 0.98], [-L / 2, 0.58, s * B * 0.93]], cCascoO, [0, 0, s]);
          }
          cara(a, [[-L / 2, 0.05, -B * 0.85], [-L / 2, 0.05, B * 0.85], [-L / 2, 0.7, B * 0.95], [-L / 2, 0.7, -B * 0.95]], cCascoO, [-1, 0, 0]);
          bx(a, XL, -L / 2 + 0.2, L * 0.2, 0.3, 0.42, -B * 0.85, B * 0.85, cMaderaC);
          // bancos, toldo sobre horcones y motor fuera de borda
          for (const x of [-2.2, -0.8, 0.6]) bx(a, XL, x - 0.15, x + 0.15, 0.42, 0.6, -B * 0.85, B * 0.85, cMadera);
          for (const x of [-2.6, 0.9]) for (const s of [-1, 1]) tubo(a, [x, 0.6, s * B * 0.85], [x, 2.0, s * B * 0.85], 0.04, 6, cMaderaO, null);
          bx(a, XL, -2.9, 1.2, 2.0, 2.08, -B * 1.0, B * 1.0, cCascoO.clone().multiplyScalar(1.1));
          bx(a, XL, -L / 2 - 0.45, -L / 2 + 0.05, 0.5, 1.15, -0.2, 0.2, cHueco); tubo(a, [-L / 2 - 0.25, 0.5, 0], [-L / 2 - 0.25, -0.35, 0], 0.07, 8, cHueco, null);
          return malla.geometria(a); })();
        const geoCayuco = (() => { const a = nueva(), L = 5.2, B = 0.42, n = 12;
          for (let i = 0; i < n; i++) {
            const x0 = -L / 2 + L * i / n, x1 = -L / 2 + L * (i + 1) / n, w0 = B * Math.sqrt(Math.max(0.02, 1 - Math.pow(2 * x0 / L, 2))), w1 = B * Math.sqrt(Math.max(0.02, 1 - Math.pow(2 * x1 / L, 2)));
            for (const s of [-1, 1]) {
              cara(a, [[x0, 0.02, s * w0 * 0.7], [x1, 0.02, s * w1 * 0.7], [x1, 0.42, s * w1], [x0, 0.42, s * w0]], cCayuco.clone().multiplyScalar(0.92 + 0.08 * (i % 2)), [0, -0.2, s]);
              cara(a, [[x0, 0.42, s * w0], [x1, 0.42, s * w1], [x1, 0.42, s * w1 * 0.72], [x0, 0.42, s * w0 * 0.72]], cCayuco.clone().multiplyScalar(1.25), [0, 1, 0]);
            }
            cara(a, [[x0, 0.12, -w0 * 0.72], [x1, 0.12, -w1 * 0.72], [x1, 0.12, w1 * 0.72], [x0, 0.12, w0 * 0.72]], cCayuco.clone().multiplyScalar(0.6), [0, 1, 0]);
          }
          return malla.geometria(a); })();
        const geoRemo = (() => { const a = nueva(); tubo(a, [0, 0, 0], [0, 2.1, 0], 0.03, 6, cMaderaC, null); bx(a, XL, -0.09, 0.09, -0.5, 0.05, -0.02, 0.02, cMaderaC); return malla.geometria(a); })();
        const geoEstela = (() => { const a = nueva(), l = 1;
          for (const s of [-1, 1]) { const q = a.pos.length / 3;
            for (const [x, z, c] of [[0, s * 0.6, 0.55], [-14, s * 5.5, 0], [-14, s * 4.2, 0], [0, s * 0.25, 0.4]]) { a.pos.push(x, 0.03, z); a.col.push(cBrillo.r * c * l, cBrillo.g * c * l, cBrillo.b * c * l); }
            a.idx.push(q, q + 1, q + 2, q, q + 2, q + 3); }
          { const q = a.pos.length / 3; for (const [x, z, c] of [[0, -0.5, 0.5], [-9, -0.9, 0], [-9, 0.9, 0], [0, 0.5, 0.5]]) { a.pos.push(x, 0.03, z); a.col.push(cBrillo.r * c, cBrillo.g * c, cBrillo.b * c); } a.idx.push(q, q + 1, q + 2, q, q + 2, q + 3); }
          return malla.geometria(a); })();
        const geoAnillo = (() => { const a = nueva(), n = 24;
          for (let i = 0; i < n; i++) { const a0 = TAU * i / n, a1 = TAU * (i + 1) / n, q = a.pos.length / 3, c = cBrillo.clone().multiplyScalar(0.5);
            for (const [rr, t0] of [[0.82, a0], [1, a0], [1, a1], [0.82, a1]]) { a.pos.push(rr * Math.cos(t0), 0.03, rr * Math.sin(t0)); a.col.push(c.r, c.g, c.b); }
            a.idx.push(q, q + 1, q + 2, q, q + 2, q + 3); }
          return malla.geometria(a); })();
        const matB = malla.material({}), matE = malla.material({ aditivo: true, desfase: 4 });
        mats.push(matB);
        const mk = (geo, mat, ord) => { const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = ord || 4; m.scale.setScalar(M); scene.add(m); return m; };
        const NLA = clamp(p.lanchas | 0, 0, 4), NCA = clamp(p.cayucos | 0, 0, 4);
        // lanchas: la mitad (redondeada abajo) amarradas al muelle, las demás cruzan el lago
        const lanchas = [];
        for (let i = 0; i < NLA; i++) {
          const amarrada = i < Math.floor(NLA / 2) || (NLA === 1 && false);
          lanchas.push({ m: mk(geoLancha, matB), e: amarrada ? null : mk(geoEstela, matE, 5), amarrada, lado: i % 2 ? 1 : -1, uc: 70 + 90 * hz(i, 160), dir: hz(i, 161) < 0.5 ? 1 : -1, vel: 5 + 2 * hz(i, 162), ph: hz(i, 163), k: i });
        }
        const cayucos = [];
        for (let i = 0; i < NCA; i++) cayucos.push({ m: mk(geoCayuco, matB), remo: mk(geoRemo, matB), e: mk(geoEstela, matE, 5), uc: uA0 + 26 + 50 * hz(i, 170), dir: hz(i, 171) < 0.5 ? 1 : -1, vel: 0.9 + 0.4 * hz(i, 172), ph: hz(i, 173), k: i });
        // ================= las aves del tular (zambullidores): cuerpo, cuello, cabeza y pico claro
        const NAV = clamp(p.aves | 0, 0, 6), aves = [];
        if (NAV) {
          const a = nueva();
          gema(a, [0, 0.12, 0], 0.27, 0.13, 0.15, 0, cAve); gema(a, [-0.22, 0.17, 0], 0.1, 0.07, 0.1, 0, cAve.clone().multiplyScalar(0.9));
          tubo(a, [0.15, 0.15, 0], [0.24, 0.36, 0], 0.045, 8, cAve, null); gema(a, [0.26, 0.38, 0], 0.07, 0.06, 0.06, 0, cAve);
          tubo(a, [0.31, 0.38, 0], [0.39, 0.36, 0], 0.022, 6, cPico, cPico); tubo(a, [0.345, 0.372, 0], [0.355, 0.37, 0], 0.025, 6, cAve, null);
          const gAve = malla.geometria(a);
          for (let i = 0; i < NAV; i++) {
            const c = manchas.length ? manchas[Math.floor(hz(i, 180) * manchas.length)] : [TU1 + 2, 60 + 30 * i];
            aves.push({ m: mk(gAve, matB), o: mk(geoAnillo, matE, 5), u: Math.max(c[0], uA0) + 3 + 3 * hz(i, 181), v: c[1], ph: hz(i, 182) * 30, k: i });
          }
        }

        // ================= el humo de los fogones (bolitas que suben y se deshacen)
        const gH = (() => { const a = nueva(); gema(a, [0, 0, 0], 1, 1, 1, 0, cHumo); return malla.geometria(a); })();
        const matH = malla.material({ alfa: 0.5 }); mats.push(matH);
        const humo = []; humos.forEach((h, j) => { for (let b = 0; b < 6; b++) humo.push({ m: mk(gH, matH, 6), h, b, j }); });

        // ================= la gente: vendedoras en el muelle, gente en la playa y en el corredor, quien corta tul en el agua,
        // y gente a pie por el camino; los cargadores llevan su carga a la espalda con el mecapal (adjuntos del objeto)
        const NP = clamp(p.personas | 0, 0, 10);
        const camisas = [tonos.mal.clone(), tonos.medio.clone(), tonos.bien.clone(), lin(COL.costa).multiplyScalar(0.85), tonos.muro.clone().multiplyScalar(0.9)];
        const PUESTOS = [["vende", MU1 - 4, 0.6, "de_pie"], ["camina", 0, 0, "caminar"], ["carga", 0, 0, "caminar"], ["playa", -3, -22, "de_pie"],
          ["corredor", hotel1 ? hotel1[0] - 2.6 : -30, hotel1 ? hotel1[1] - 3 : 66, "de_pie"], ["tul", TU0 + 2, 64, "de_pie"], ["carga", 0, 0, "caminar"],
          ["vende", -2, 6, "de_pie"], ["camina", 0, 0, "caminar"], ["playa", -4, 16, "de_pie"]].slice(0, NP);
        // `cargadores` y `vendedoras` (si vienen) mandan sobre los de `personas`: los cargadores van en grupo por el camino,
        // espaciados, cerca del acceso al muelle; las vendedoras, en la playa con su mercancía en el suelo o caminando con ella
        const NCG = p.cargadores >= 0 ? clamp(p.cargadores | 0, 0, 6) : -1, NVD = p.vendedoras >= 0 ? clamp(p.vendedoras | 0, 0, 6) : -1;
        const G = p.gente_escala > 0 ? clamp(+p.gente_escala, 1, 2.2) : 1.25;
        let PS = PUESTOS;
        if (NCG >= 0) PS = PS.filter((q) => q[0] !== "carga").concat(Array.from({ length: NCG }, () => ["carga", 0, 0, "caminar"]));
        if (NVD >= 0) PS = PS.filter((q) => q[0] !== "vende");
        const genP = PS.filter((q) => q[0] !== "carga"), carP = PS.filter((q) => q[0] === "carga"), grupoC = NCG >= 0;
        // las vendedoras: [u, v, anda] (anda = camina por la playa con su carga)
        const SV = [[-3.6, -32, 0], [-2.4, 7, 0], [-5.5, -10, 1], [-3.8, -50, 0], [-4.2, -88, 0], [-5.5, 15, 1]].slice(0, Math.max(0, NVD));
        const hPlaya = (u) => u >= U_PLAYA ? HL + (HA + 0.04 - HL) * (u - U_PLAYA) / (-U_PLAYA) : HL;
        let flVd = null;
        if (SV.length) {
          const cTela = tonos.medio.clone().lerp(tonos.muro, 0.35).multiplyScalar(0.8), cTela2 = tonos.mal.clone().lerp(tonos.muro, 0.3).multiplyScalar(0.75);
          const cCebolla = tonos.muro.clone().lerp(tonos.mal, 0.25), cFruta = tonos.medio.clone(), cFruta2 = tonos.mal.clone().multiplyScalar(0.9);
          // la mercancía en el suelo: un petate con montones (cebolla, ajo, fruta, verdura; genéricos) junto a la que vende
          SV.forEach(([u, v, anda], j) => {
            if (anda) return;
            const a0 = u + 0.7, a1 = u + 2.3, b0 = v - 0.9, b1 = v + 0.9;
            quad(suelo, [[a0, b0, hPlaya(a0) + 0.03], [a1, b0, hPlaya(a1) + 0.03], [a1, b1, hPlaya(a1) + 0.03], [a0, b1, hPlaya(a0) + 0.03]], cTulSeco.clone().multiplyScalar(0.9 + 0.1 * hz(j, 200)));
            for (let q = 0; q < 4; q++) {
              const pu = a0 + 0.45 + 0.75 * (q % 2), pv = b0 + 0.5 + 0.8 * (q >> 1), col = [cCebolla, cFruta, cMata, cFruta2][(q + j) % 4], h0 = hPlaya(pu) + 0.04;
              for (let b = 0; b < 7; b++) {
                const a = TAU * b / 6 + hz(j * 9 + q, 201), d = b === 6 ? 0 : 0.17, rr = 0.09 + 0.03 * hz(j * 50 + q * 7 + b, 202);
                gema(plantas, E(pu + d * Math.cos(a), pv + d * Math.sin(a), h0 + rr + (b === 6 ? 0.12 : 0)), rr * M, rr * 0.9 * M, rr * M, a, col.clone().multiplyScalar(0.85 + 0.25 * hz(j * 50 + q * 7 + b, 203)), true);
              }
            }
          });
          // lo que llevan: un bulto de tela al frente, abrazado, con fruta y verdura asomando (en ejes del objeto, atado al torso)
          const tela = new THREE.BoxGeometry(0.34, 0.3, 0.5); tela.translate(0.3, 1.02, 0);
          const nudo = new THREE.BoxGeometry(0.36, 0.05, 0.52); nudo.translate(0.3, 1.18, 0);
          const fr1 = new THREE.IcosahedronGeometry(0.075, 1); fr1.translate(0.3, 1.24, -0.12);
          const fr2 = new THREE.IcosahedronGeometry(0.08, 1); fr2.translate(0.26, 1.25, 0.1);
          const fr3 = new THREE.IcosahedronGeometry(0.07, 1); fr3.translate(0.36, 1.23, 0.0);
          const faldas = [cTela, cTela2];
          flVd = ctx.flota("persona", SV.length, { tamano: K * G, lev: 0, orden: 6, semilla: (p.semilla + 11) % 991, color: (i) => faldas[i % 2], pose: (i) => SV[i][2] ? "caminar" : "de_pie",
            adjuntos: [{ geo: tela, color: cTela2, grupo: "torso" }, { geo: nudo, color: cTela, grupo: "torso" }, { geo: fr1, color: cCebolla, grupo: "torso" }, { geo: fr2, color: cFruta, grupo: "torso" }, { geo: fr3, color: cFruta2, grupo: "torso" }] });
        }
        const flP = genP.length ? ctx.flota("persona", genP.length, { tamano: K * G, lev: 0, orden: 6, semilla: p.semilla % 991, color: (i) => camisas[(i + p.semilla) % camisas.length], pose: (i) => genP[i][3] }) : null;
        const remP = NCA ? ctx.flota("persona", NCA, { tamano: K * G, lev: 0.12, orden: 6, semilla: (p.semilla + 5) % 991, color: (i) => camisas[(i + 2) % camisas.length], pose: "de_pie" }) : null;
        let flC = null;
        if (carP.length) {
          // la carga: un bulto envuelto con sus amarras y la banda del mecapal hasta la frente (en ejes del objeto, atado al torso)
          const bulto = new THREE.BoxGeometry(0.36, 0.55, 0.46); bulto.translate(-0.33, 1.18, 0);
          const amarra = new THREE.BoxGeometry(0.38, 0.04, 0.48); amarra.translate(-0.33, 1.05, 0);
          const amarra2 = new THREE.BoxGeometry(0.38, 0.04, 0.48); amarra2.translate(-0.33, 1.3, 0);
          const banda = new THREE.BoxGeometry(0.03, 0.52, 0.32); banda.rotateZ(0.55); banda.translate(-0.1, 1.5, 0);
          flC = ctx.flota("persona", carP.length, { tamano: K * G, lev: 0, orden: 6, semilla: (p.semilla + 3) % 991, color: (i) => camisas[(i + 1) % camisas.length], pose: "caminar",
            adjuntos: [{ geo: bulto, color: cCarga, grupo: "torso" }, { geo: amarra, color: cMaderaO, grupo: "torso" }, { geo: amarra2, color: cMaderaO, grupo: "torso" }, { geo: banda, color: cMaderaO, grupo: "torso" }] });
        }
        // ================= los vehículos por el camino: camión-bus, carro y camión (más carros hoy), posición = función de t
        const VEH = [["bus", 7.5], ["carro", 10], ["camion", 7]].concat(HOY ? [["carro", 11], ["carro", 9.5], ["carro", 12]] : []);
        const flV = {};
        for (const tipo of ["bus", "carro", "camion"]) { const n = VEH.filter((x) => x[0] === tipo).length; flV[tipo] = ctx.flota(tipo, n, { tamano: K, lev: 0.05, orden: 6, semilla: (p.semilla + tipo.length) % 97 }); }

        // ================= las luces de noche: ventanas encendidas ya van en `vid`; faroles (hoy), farol del muelle, lanchas
        if (HOY) { for (let v = -180; v <= 180; v += 45) luces.push([UC + AC + 0.8, v, HL + 6.5, 0.9]); }
        luces.push([MU1 - 0.6, MV - 0.2, H_MUELLE + 2.6, 0.8]);
        twu(solido, MU1 - 0.6, MV - 0.2, H_MUELLE, MU1 - 0.6, MV - 0.2, H_MUELLE + 2.5, 0.06, 8, cMaderaO, null);
        if (HOY) for (let v = -180; v <= 180; v += 45) { twu(solido, UC + AC + 0.8, v, HL, UC + AC + 0.8, v, HL + 6.6, 0.08, 10, cHueco, cHueco); }
        const NLF = luces.length, NLT = NLF + NLA + NCA;
        const gP = new THREE.BufferGeometry(), posP = new Float32Array(NLT * 3), aP = new Float32Array(NLT * 2);
        gP.setAttribute("position", new THREE.BufferAttribute(posP, 3)); gP.setAttribute("aK", new THREE.BufferAttribute(aP, 2));
        const matP = new THREE.ShaderMaterial({ uniforms: { uPx: { value: 1 }, uTam: { value: M }, cA: { value: cLuz } },
          transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
          vertexShader: "attribute vec2 aK; uniform float uPx, uTam; varying vec2 vK; void main(){ vK = aK; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;" +
            " gl_PointSize = aK.x > 0.0 ? clamp(aK.y * uTam * uPx / max(1e-3, -mv.z), 2.0, 48.0) : 0.0; }",
          fragmentShader: "uniform vec3 cA; varying vec2 vK; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;" +
            " vec3 c = cA; vec3 s = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));" +
            " float a = vK.x * (exp(-r * r * 6.0) + 0.6 * exp(-r * r * 40.0)); gl_FragColor = vec4(s * a, a); }" });
        const mP = new THREE.Points(gP, matP); mP.frustumCulled = false; mP.renderOrder = 9; scene.add(mP);
        luces.forEach(([u, v, h, a], j) => { posP.set(E(u, v, h), j * 3); aP[j * 2] = noche ? a : 0; aP[j * 2 + 1] = 2.2; });
        // charcos de luz bajo los faroles (de noche)
        if (noche) { const ch = nueva();
          luces.forEach(([u, v, h]) => { const q = ch.pos.length / 3, R = Math.min(9, h * 1.4), n = 18, c0 = cLuz.clone().multiplyScalar(0.12), hh = h > H_MUELLE + 2 ? H_MUELLE + 0.03 : HL + 0.08;
            const C = E(u, v, hh); ch.pos.push(C[0], C[1], C[2]); ch.col.push(c0.r, c0.g, c0.b);
            for (let i = 0; i < n; i++) { const P = E(u + R * Math.cos(TAU * i / n), v + R * Math.sin(TAU * i / n), hh); ch.pos.push(P[0], P[1], P[2]); ch.col.push(0, 0, 0); }
            for (let i = 0; i < n; i++) ch.idx.push(q, q + 1 + i, q + 1 + ((i + 1) % n)); });
          const mC = new THREE.Mesh(malla.geometria(ch), malla.material({ aditivo: true, desfase: 5 })); mC.frustumCulled = false; mC.renderOrder = 5; scene.add(mC); }

        return { id: p.id, K, M, r, ux, uy, E, W, uA0, lanchas, cayucos, aves, humo, flP, remP, flC, flV, VEH, genP, carP, grupoC, SV, flVd, posD, colD, gD, DES, ND,
          posP, aP, gP, matP, NLF, noche, mats, vidrios, BV: noche ? 1.6 : 1.0, hz };
      });
    },
    en(t, lista, ctx) {
      const { clamp } = ctx;
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id], kb = b ? clamp((b - 1) / 0.9, 0, 1.2) : 0;
        for (const m of s.mats) if (m.uniforms && m.uniforms.uBrillo) m.uniforms.uBrillo.value = 1 + 0.35 * kb;
        for (const m of s.vidrios) m.uniforms.uBrillo.value = s.BV * (1 + 0.2 * kb);
        const { E, W, r, ux, uy } = s;
        const dirW = (du, dv) => [du * ux - dv * uy, du * uy + dv * ux];
        // ---- los destellos: cada uno titila con su fase (sin acumular)
        for (let i = 0; i < s.ND; i++) {
          const [ph, w] = s.DES[i], a = Math.pow(Math.max(0, Math.sin(t * w + ph)), 6) * (s.noche ? 0.12 : 0.32);
          for (let j = 0; j < 4; j++) s.colD.set([0.9 * a, 0.95 * a, a], (i * 4 + j) * 3);
        }
        s.gD.attributes.color.needsUpdate = true;
        let jl = s.NLF;
        const luz = (P, a) => { s.posP.set(P, jl * 3); s.aP[jl * 2] = s.noche ? a : 0; s.aP[jl * 2 + 1] = 1.4; jl++; };
        // ---- las lanchas: amarradas al muelle (se mecen) o cruzando el lago a lo largo de la orilla (envuelve en ±700 m)
        for (const L of s.lanchas) {
          let u, v, ang, rol = 0;
          if (L.amarrada) {
            u = MU1 - 6 - L.k * 3.2; v = L.lado * (MV + 1.4); ang = 0; rol = 0.03 * Math.sin(t * 1.3 + L.k);
          } else {
            const T = 1400 / L.vel, f = (((t / T + L.ph) % 1) + 1) % 1;
            u = L.uc; v = L.dir * (-700 + 1400 * f); ang = L.dir > 0 ? Math.PI / 2 : -Math.PI / 2;
          }
          const P = E(u, v, HA + 0.02 * Math.sin(t * 1.7 + L.k)); L.m.position.set(P[0], P[1], P[2]); L.m.rotation.set(rol, r + ang, 0, "YXZ");
          if (L.e) { const Q = E(u, v, HA); L.e.position.set(Q[0], Q[1], Q[2]); L.e.rotation.set(0, r + ang, 0); }
          luz(E(u, v, HA + 2.3), 0.7);
        }
        // ---- los cayucos: cruzan despacio, el remero de pie y su remo que entra y sale del agua
        s.cayucos.forEach((C, i) => {
          const T = 1000 / C.vel, f = (((t / T + C.ph) % 1) + 1) % 1, v = C.dir * (-500 + 1000 * f), u = C.uc, ang = C.dir > 0 ? Math.PI / 2 : -Math.PI / 2;
          const P = E(u, v, HA - 0.06 + 0.02 * Math.sin(t * 1.1 + i)); C.m.position.set(P[0], P[1], P[2]); C.m.rotation.set(0, r + ang, 0);
          C.e.position.set(P[0], E(u, v, HA)[1], P[2]); C.e.rotation.set(0, r + ang, 0); C.e.scale.set(s.M * 0.35, s.M, s.M * 0.35);
          const [dx, dy] = dirW(0, C.dir);     // el remero, a popa
          const [wx, wy] = W(u, v - C.dir * 1.6);
          s.remP.poner(i, wx, wy, dx, dy, 1, 0, 0);
          const ph = (t * 0.9 + i) % 1, sw = Math.sin(TAU * ph), lado = (Math.floor(t * 0.9 + i) % 2) ? 1 : -1;
          const [pu, pv] = [u + lado * 0.55, v - C.dir * 1.3];
          const Pr = E(pu, pv, HA + 0.1 + 0.25 * Math.max(0, sw)); C.remo.position.set(Pr[0], Pr[1], Pr[2]);
          C.remo.rotation.set(0, r + ang, 0.5 * Math.cos(TAU * ph), "YXZ");
          luz(E(u, v, HA + 1.2), 0.35);
        });
        // ---- las aves: nadan junto al tul, se zambullen ≈ 20 s y salen más allá (ciclo de 30 s)
        for (const A of s.aves) {
          const T = 30, q = ((t + A.ph) % T + T) % T, n = Math.floor((t + A.ph) / T), du = 2.5 * s.hz(A.k * 97 + n, 190), dv = 6 * (s.hz(A.k * 97 + n, 191) - 0.5);
          const nada = q < 10, u = A.u + du + (nada ? 0.15 * q : 1.5), v = A.v + dv;
          const k = nada ? 1 - clamp((q - 9.4) / 0.6, 0, 1) : (q > 29.4 ? clamp((q - 29.4) / 0.6, 0, 1) : 0);
          const P = E(u, v, HA - 0.05); A.m.position.set(P[0], P[1] - (1 - k) * 0.3 * s.M, P[2]); A.m.rotation.set(0, r + 0.4 + 0.3 * Math.sin(n), 0); A.m.scale.setScalar(s.M * Math.max(1e-4, k) * 1.0);
          const ro = nada ? clamp((q - 9.3) / 1.5, 0, 1) : 0, ka = ro > 0 && ro < 1 ? 1 - ro : 0;
          A.o.position.set(P[0], E(u, v, HA)[1], P[2]); A.o.scale.set(s.M * (0.3 + 1.6 * ro), s.M, s.M * (0.3 + 1.6 * ro)); A.o.visible = ka > 0;
        }
        // ---- el humo: bolitas que suben, crecen y se apagan (ciclo de 6 s, desfasadas)
        for (const H of s.humo) {
          const f = (((t / 6 + H.b / 6 + H.j * 0.13) % 1) + 1) % 1, [u, v, h] = H.h;
          const P = E(u + 2.5 * f + 0.3 * Math.sin(f * 7), v + 1.2 * f, h + 7 * f); H.m.position.set(P[0], P[1], P[2]);
          H.m.scale.setScalar(s.M * (0.35 + 1.1 * f) * Math.sin(Math.PI * Math.min(1, f * 1.2)) + 1e-4);
        }
        // ---- la gente
        const camino = (q, i, vel, dirSign) => {      // por el camino: posición = función de t, envuelve en ±300 m
          const T = 600 / vel, f = (((t / T + q) % 1) + 1) % 1, v = dirSign * (-300 + 600 * f);
          return [U_CAMINO + 3.6 + 1.0 + 0.6 * (i % 2), v];
        };
        if (s.flP) {
          s.genP.forEach((g, i) => {
            if (g[0] === "camina") { const d = i % 2 ? 1 : -1, [u, v] = camino(0.2 + 0.37 * i, i, 1.1, d), [x, y] = W(u, v), [dx, dy] = dirW(0, d); s.flP.poner(i, x, y, dx, dy, 1, 0, 1.1); }
            else {
              const [x, y] = W(g[1], g[2]), mira = g[0] === "corredor" || g[0] === "playa" ? [1, 0.2] : g[0] === "tul" ? [0, 1] : [-1, 0.3], [dx, dy] = dirW(mira[0], mira[1]);
              s.flP.poner(i, x, y, dx, dy, 1, 0, 0);
            }
          });
          s.flP.listo();
        }
        if (s.flC && !s.grupoC) { s.carP.forEach((g, i) => { const d = i % 2 ? -1 : 1, [u, v] = camino(0.55 + 0.29 * i, i + 1, 1.0, d), [x, y] = W(u - 2.2, v), [dx, dy] = dirW(0, d); s.flC.poner(i, x, y, dx, dy, 1, 0, 1.0); }); s.flC.listo(); }
        else if (s.flC) {
          // en grupo: los pares hacia +v y los nones hacia −v, espaciados 16–21 m, cerca del acceso al muelle al empezar (envuelve en ±150 m)
          s.carP.forEach((g, i) => {
            const d = i % 2 ? -1 : 1, n = i >> 1, vel = 0.95 + 0.1 * s.hz(i, 210), T = 300 / vel;
            const v0 = d > 0 ? -5 - 16 * n - 3 * s.hz(i, 211) : 7 + 18 * n + 3 * s.hz(i, 211);
            const f = (((t / T + (d > 0 ? v0 + 150 : 150 - v0) / 300) % 1) + 1) % 1, v = d > 0 ? -150 + 300 * f : 150 - 300 * f;
            const u = U_CAMINO + 3.6 - 1.2 + 0.7 * (i % 2), [x, y] = W(u, v), [dx, dy] = dirW(0, d);
            s.flC.poner(i, x, y, dx, dy, 1, 0, vel);
          });
          s.flC.listo();
        }
        if (s.flVd) {
          s.SV.forEach(([u0, v0, anda], i) => {
            if (anda) {   // camina por la playa entre v = −100 y 25 (envuelve), con su carga al frente
              const d = i % 2 ? 1 : -1, T = 125 / 0.9, f = (((t / T + (d > 0 ? v0 + 100 : 25 - v0) / 125) % 1) + 1) % 1, v = d > 0 ? -100 + 125 * f : 25 - 125 * f;
              const [x, y] = W(u0, v), [dx, dy] = dirW(0, d); s.flVd.poner(i, x, y, dx, dy, 1, 0, 0.9);
            } else { const [x, y] = W(u0, v0), [dx, dy] = dirW(1, i % 2 ? 0.35 : -0.35); s.flVd.poner(i, x, y, dx, dy, 1, 0, 0); }
          });
          s.flVd.listo();
        }
        if (s.remP) s.remP.listo();
        // ---- los vehículos: cada tipo por su carril, envuelven en ±420 m
        const cnt = { bus: 0, carro: 0, camion: 0 };
        s.VEH.forEach(([tipo, vel], i) => {
          const d = i % 2 ? -1 : 1, T = 840 / vel, f = (((t / T + 0.17 * i + 0.05) % 1) + 1) % 1, v = d * (-420 + 840 * f), u = U_CAMINO - d * 1.75;
          const [x, y] = W(u, v), [dx, dy] = dirW(0, d);
          s.flV[tipo].poner(cnt[tipo]++, x, y, dx, dy, 1, 0, vel);
        });
        for (const tipo in s.flV) s.flV[tipo].listo();
        s.gP.attributes.position.needsUpdate = true; s.gP.attributes.aK.needsUpdate = true;
        s.matP.uniforms.uPx.value = ctx.H / (2 * Math.tan(ctx.camera.fov * Math.PI / 360));
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
