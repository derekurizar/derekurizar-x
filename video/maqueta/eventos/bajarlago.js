// Evento «bajarlago» (ficha: bajarlago.json; reglas: scripts/maqueta_tipos/bajarlago.py): el nivel de una `orillalago`
// baja. La orilla del agua se va mar adentro con su borde irregular y una línea de espuma, y deja al aire el LECHO: lodo
// mojado y oscuro junto al agua que se aclara al secarse, con charcos en las hondonadas que se encogen y piedras que
// asoman. El TULAR del evento (el mismo trecho que el de la pieza: manchas de tul y de enea con su espiga) se mece verde
// mientras está en el agua; el que queda al aire pasa de verde a pardo y se dobla (cada junco a su modo). Ilustrativo:
// no dibuja metros ni cuenta juncos. La pieza va con `tul: 0` (el tular de este evento sustituye al suyo).
// Seek puro: el segundo en que el agua deja al aire cada punto se calcula al armar (de los eventos), y todo lo que se ve
// sale de t. Sin colores escritos (ctx.tonos, ctx.COL, ctx.lin).
(function (MAQ) {
  const HA = 0.08, U_MAX = 44, SECO_M = 24, TU0 = 5, LV = 700;
  const ORILLA = 0.7;   // cuánto detrás del frente cruza el lecho el plano del agua (m)
  const SECADO = 3.2;   // lo que tarda un junco en secarse y doblarse tras quedar al aire (s; ilustrativo)
  const TAU = 2 * Math.PI;

  MAQ.EVENTOS.bajarlago = {
    orden: 46,
    armar(ctx, lista) {
      const { THREE, malla, tonos, sombra, hash, ES, lin, COL, metros, clamp, suave } = ctx;
      const oscuro = ES.modo === 1;
      // ---- los tonos (todos del estilo)
      const cLodo = tonos.arena.clone().lerp(lin(COL.tierra_media), 0.45).multiplyScalar(oscuro ? 0.9 : 0.72);
      const cLodoH = cLodo.clone().lerp(tonos.agua, 0.18).multiplyScalar(0.62);
      const cLodoS = cLodo.clone().lerp(tonos.arena, 0.4).multiplyScalar(1.08);
      const cGrieta = cLodo.clone().multiplyScalar(0.55);
      const cTul = tonos.verde.clone().lerp(tonos.campo2, 0.35), cTulP = tonos.arena.clone().lerp(tonos.verde, 0.35).multiplyScalar(1.05);
      const cPardo = lin(COL.tierra_media).lerp(tonos.arena, 0.35).multiplyScalar(oscuro ? 0.85 : 0.78);
      const cPardoP = tonos.arena.clone().lerp(lin(COL.tierra_alta), 0.3).multiplyScalar(0.95);
      const cEspiga = lin(COL.tierra_alta).lerp(tonos.asfalto, 0.35).multiplyScalar(0.7);
      const cPiedra = tonos.arena.clone().lerp(tonos.asfalto, 0.4).multiplyScalar(0.8);
      const cEspuma = tonos.agua.clone().lerp(tonos.muro, 0.7);
      const OCT = new THREE.OctahedronGeometry(1, 1).toNonIndexed().attributes.position.array;
      const lS = sombra(0, 1, 0);

      const porPieza = new Map();
      for (const e of [...lista].sort((a, b) => a.t - b.t)) {
        if (!porPieza.has(e.pieza)) porPieza.set(e.pieza, []);
        porPieza.get(e.pieza).push(e);
      }
      const orillas = [];
      for (const [pid, evs] of porPieza) {
        const e0 = evs[0], K = e0.tamano || 1, M = metros(1) * K;
        const r = e0.rumbo * Math.PI / 180, ux = Math.cos(r), uy = Math.sin(r);
        const sem = (e0.semilla || 1) * 7919 + 31, hz = (i, k) => hash(i + sem, k);
        const base0 = ctx.suelo ? ctx.suelo(e0.x, e0.y) : ctx.altura(e0.x, e0.y);
        const E = (u, v, h) => [e0.x + (u * ux - v * uy) * M, base0 + h * M, -(e0.y + (u * uy + v * ux) * M)];
        const ruido = (x, y, cel, k) => {
          const fx = x / cel, fy = y / cel, ix = Math.floor(fx), iy = Math.floor(fy), tx = fx - ix, ty = fy - iy;
          const v = (a, b) => hz((a & 4095) * 4099 + (b & 4095), k), sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
          return (v(ix, iy) * (1 - sx) + v(ix + 1, iy) * sx) * (1 - sy) + (v(ix, iy + 1) * (1 - sx) + v(ix + 1, iy + 1) * sx) * sy;
        };
        // ---- el nivel en el tiempo (0 = lleno, 1 = el agua U_MAX m más allá) y el frente a lo largo de la orilla
        const segs = evs.map((e) => ({ t0: e.t, t1: e.t + Math.max(0.05, e.dur || 0), a: e.de, b: e.baja, seca: e.seca }));
        const nivel = (t) => {
          let f = segs[0].a;
          for (const s of segs) { if (t < s.t0) break; f = t >= s.t1 ? s.b : s.a + (s.b - s.a) * suave(s.t0, s.t1, t); }
          return f;
        };
        const U0 = SECO_M * (e0.seco0 || 0);
        const borde = (v) => 0.8 + 0.4 * ruido(3.1, v, 46, 3) + 0.08 * Math.sin(v * 0.21 + 1.3);   // la orilla no es recta
        const frente = (f, v) => Math.max(U0, U_MAX * f * borde(v));
        // el segundo en que el frente deja al aire (u, v): -1e9 si ya lo estaba, Infinity si nunca; y la `seca` de ese evento
        const alAire = (u, v) => {
          const L = (u + ORILLA) / (U_MAX * borde(v));
          if (U0 >= u + ORILLA || segs[0].a >= L) return [-1e9, segs[0].seca];
          for (const s of segs) {
            if (s.b < L) continue;
            let lo = s.t0, hi = s.t1;
            for (let i = 0; i < 26; i++) { const mid = (lo + hi) / 2; if (s.a + (s.b - s.a) * suave(s.t0, s.t1, mid) >= L) hi = mid; else lo = mid; }
            return [hi, s.seca];
          }
          return [Infinity, 0];
        };

        // ================= el lecho: una losa que va bajo el agua y sube al quedar al aire (con charcos y grietas)
        const UG = U_MAX * 1.32 + 2, NU = Math.round(UG / 0.75);
        const VS = [];
        for (let v = -LV; v < -260; v += 10) VS.push(v);
        for (let v = -260; v < 260; v += 2.5) VS.push(v);
        for (let v = 260; v <= LV; v += 10) VS.push(v);
        const NV = VS.length, nL = (NU + 1) * NV;
        const lecho = malla.nueva(), LD = [];
        for (let i = 0; i <= NU; i++) for (let j = 0; j < NV; j++) {
          const u = UG * i / NU, v = VS[j], [te, sc] = alAire(u, v);
          const charco = suave(0.6, 0.82, ruido(u, v, 9, 21)) * clamp(u / 6, 0, 1);
          const grieta = Math.abs(ruido(u, v, 3.2, 22) - 0.5) < 0.035 ? 1 : 0;
          LD.push({ u, v, te, sc, charco, grieta, n: 0.9 + 0.16 * ruido(u, v, 5, 23) });
          lecho.pos.push(0, 0, 0); lecho.col.push(0, 0, 0);
        }
        for (let i = 0; i < NU; i++) for (let j = 0; j < NV - 1; j++) { const a = i * NV + j, b = a + NV; lecho.idx.push(a, b, b + 1, a, b + 1, a + 1); }
        const mLecho = malla.poner(lecho, malla.material({ desfase: 1 }), 2);
        // las piedras del fondo, que asoman al bajar el agua
        const piedras = malla.nueva();
        for (let i = 0; i < 160; i++) {
          const u = 3 + (U_MAX * 1.1) * Math.pow(hz(i, 30), 0.9), v = (hz(i, 31) - 0.5) * 560, rr = 0.2 + 0.45 * hz(i, 32);
          if (Math.abs(v) < 4) continue;
          const P = E(u, v, HA - 0.1), cr = Math.cos(TAU * hz(i, 33)), sr = Math.sin(TAU * hz(i, 33)), c = new THREE.Color();
          for (let q = 0; q < OCT.length; q += 9) {
            const w = [];
            for (let j = 0; j < 9; j += 3) { const x = OCT[q + j] * rr * M, y = OCT[q + j + 1] * rr * 0.5 * M, z = OCT[q + j + 2] * rr * 0.8 * M; w.push([P[0] + x * cr - z * sr, P[1] + y, P[2] + x * sr + z * cr]); }
            const e1 = [w[1][0] - w[0][0], w[1][1] - w[0][1], w[1][2] - w[0][2]], e2 = [w[2][0] - w[0][0], w[2][1] - w[0][1], w[2][2] - w[0][2]];
            let nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2], nz = e1[0] * e2[1] - e1[1] * e2[0];
            const nn = Math.hypot(nx, ny, nz) || 1; c.copy(cPiedra).multiplyScalar((0.8 + 0.3 * hz(i, 34)) * sombra(nx / nn, Math.abs(ny / nn), nz / nn));
            const b = piedras.pos.length / 3;
            for (const p of w) { piedras.pos.push(p[0], p[1], p[2]); piedras.col.push(c.r, c.g, c.b); }
            piedras.idx.push(b, b + 1, b + 2);
          }
        }
        malla.poner(piedras, malla.material({}), 3);
        // la espuma en la orilla del agua (se mueve con el frente)
        const espuma = malla.nueva();
        for (let j = 0; j < NV; j++) { espuma.pos.push(0, 0, 0, 0, 0, 0); espuma.col.push(cEspuma.r, cEspuma.g, cEspuma.b, cEspuma.r * 0.9, cEspuma.g * 0.9, cEspuma.b * 0.9); }
        for (let j = 0; j < NV - 1; j++) { const a = 2 * j; espuma.idx.push(a, a + 2, a + 3, a, a + 3, a + 1); }
        const mEspuma = malla.poner(espuma, malla.material({ alfa: 0.7, desfase: 3 }), 4);

        // ================= el tular: manchas de tul y de enea (el trecho de la pieza: de 5 a 5 + 34·tul m mar adentro)
        const TUL = clamp(e0.tul, 0, 1), TU1 = TU0 + 34 * Math.max(0.25, TUL), B = [];
        if (TUL > 0.01) {
          const NC = Math.round(2200 * TUL);
          for (let i = 0; i < NC && B.length < 9000; i++) {
            const lado = hz(i, 40) < 0.62 ? 1 : -1;
            const v = lado > 0 ? 26 + 190 * hz(i, 41) : -(56 + 150 * hz(i, 41));
            const u = TU0 + (TU1 - TU0) * Math.pow(hz(i, 42), 0.8);
            if (ruido(u, v, 14, 43) < 0.3 + 0.25 * (1 - TUL)) continue;
            const enea = ruido(u, v, 9, 44) > 0.62, alto = (enea ? 1.7 : 2.2) + 1.0 * hz(i, 45), nb = 6 + Math.floor(4 * hz(i, 46));
            for (let b = 0; b < nb; b++) {
              const k = i * 11 + b, a = TAU * hz(k, 47), d = 0.25 * hz(k, 48), uu = u + d * Math.cos(a), vv = v + d * Math.sin(a);
              const [te, sc] = alAire(uu, vv);
              B.push({ u: uu, v: vv, ia: TAU * hz(k, 49), inc: 0.2 * hz(k, 50), hh: alto * (0.7 + 0.35 * hz(k, 51)) + 0.4, w: enea ? 0.11 : 0.08,
                enea: enea && b < 3, tono: 0.8 + 0.25 * hz(k, 52), dob: 0.45 + 0.55 * hz(k, 53), ph: TAU * hz(k, 54), lag: 0.8 * hz(k, 55), te, sc });
            }
          }
        }
        let mTul = null;
        if (B.length) {
          const tul = malla.nueva();
          for (let i = 0; i < B.length; i++) {
            for (let q = 0; q < 10; q++) { tul.pos.push(0, 0, 0); tul.col.push(0, 0, 0); }
            for (const o of [i * 10, i * 10 + 5]) tul.idx.push(o, o + 1, o + 3, o, o + 3, o + 2, o + 2, o + 3, o + 4);
          }
          mTul = malla.poner(tul, malla.material({}), 3);
        }
        orillas.push({ pid, E, M, nivel, frente, LD, NV, NU, mLecho, mEspuma, VS, B, mTul });
      }
      return { orillas, _cTul: cTul, _cTulP: cTulP, _cPardo: cPardo, _cPardoP: cPardoP, _cEsp: cEspiga, _cLodoH: cLodoH, _cLodoS: cLodoS, _cGrieta: cGrieta, _lS: lS };
    },
    aplicar() {
      // el nivel de cada orilla sale de todos sus bajarlago (fijado al armar): se dibuja en `en`
    },
    en(t, st, ctx) {
      if (!st) return;
      const { clamp, suave } = ctx;
      for (const o of st.orillas) {
        const f = o.nivel(t), E = o.E;
        // ---- el lecho: bajo el agua donde todavía la hay; al aire, mojado junto al agua y claro y agrietado al secarse
        const pL = o.mLecho.geometry.attributes.position.array, cL = o.mLecho.geometry.attributes.color.array;
        for (let n = 0; n < o.LD.length; n++) {
          const L = o.LD[n], d = o.frente(f, L.v) - L.u;
          const seco = L.te > t ? 0 : suave(0, 5.5, t - L.te);
          const h = HA - 0.4 + 0.45 * clamp((d + 0.2) / 1.0, 0, 1) - 0.2 * L.charco * (1 - 0.7 * seco);
          const P = E(L.u, L.v, h); pL[n * 3] = P[0]; pL[n * 3 + 1] = P[1]; pL[n * 3 + 2] = P[2];
          const mo = 1 - seco * (0.3 + 0.7 * L.sc), kg = L.grieta ? clamp((seco - 0.4) / 0.6, 0, 1) * 0.7 : 0;
          for (let k = 0; k < 3; k++) {
            const c = k === 0 ? "r" : k === 1 ? "g" : "b", lodo = st._cLodoH[c] * mo + st._cLodoS[c] * (1 - mo);
            cL[n * 3 + k] = (lodo * (1 - kg) + st._cGrieta[c] * kg) * st._lS * L.n;
          }
        }
        o.mLecho.geometry.attributes.position.needsUpdate = true; o.mLecho.geometry.attributes.color.needsUpdate = true;
        // ---- la espuma: una cinta sobre el agua junto al frente, que respira
        const pE = o.mEspuma.geometry.attributes.position.array, U = f > 0 ? 1 : 0;
        o.mEspuma.visible = U > 0 && o.frente(f, 0) > 1.2;
        if (o.mEspuma.visible) for (let j = 0; j < o.NV; j++) {
          const v = o.VS[j], u0 = o.frente(f, v) - ORILLA + 0.05 + 0.12 * Math.sin(t * 1.7 + v * 0.13), a = 0.25 + 0.2 * (0.5 + 0.5 * Math.sin(t * 2.3 + v * 0.31));
          const A = E(u0, v, HA + 0.012), Bb = E(u0 + a, v, HA + 0.012);
          pE.set(A, j * 6); pE.set(Bb, j * 6 + 3);
        }
        o.mEspuma.geometry.attributes.position.needsUpdate = true;
        // ---- el tul: verde y meciéndose en el agua; al aire, pardo y doblado
        if (o.mTul) {
          const pT = o.mTul.geometry.attributes.position.array, cT = o.mTul.geometry.attributes.color.array, l = 0.92;
          const col = (q, c, k) => { cT[q * 3] = c[0] * k; cT[q * 3 + 1] = c[1] * k; cT[q * 3 + 2] = c[2] * k; };
          const put = (q, u, v, h) => { const P = E(u, v, h); pT[q * 3] = P[0]; pT[q * 3 + 1] = P[1]; pT[q * 3 + 2] = P[2]; };
          for (let i = 0; i < o.B.length; i++) {
            const J = o.B[i], te = J.te + J.lag;
            const dry = J.te > t ? 0 : J.te < -1e8 ? J.sc : J.sc * suave(te, te + SECADO, t);
            const dob = dry * J.dob, mece = (1 - dry) * 0.07 * Math.sin(t * 1.25 + J.ph) + (1 - dry) * 0.03 * Math.sin(t * 2.9 + J.ph * 1.7);
            const du = Math.cos(J.ia), dv = Math.sin(J.ia);
            const th1 = Math.atan2(J.inc, J.hh) + 0.3 * dob + 0.5 * mece, th2 = th1 + mece + 1.85 * dob;
            const L1 = J.hh * (0.55 - 0.06 * dry), L2 = J.hh * 0.48 * (1 - 0.12 * dry), h0 = HA - 0.4;
            const mu = J.u + du * L1 * Math.sin(th1), mv = J.v + dv * L1 * Math.sin(th1), mh = h0 + L1 * Math.cos(th1);
            const tu = mu + du * L2 * Math.sin(th2), tv = mv + dv * L2 * Math.sin(th2), th = Math.max(HA + 0.12, mh + L2 * Math.cos(th2));
            // el color: verde → pardo (y la espiga de la enea)
            const cb = [0, 0, 0], ct = [0, 0, 0];
            for (let k = 0; k < 3; k++) {
              const g = k === 0 ? "r" : k === 1 ? "g" : "b";
              cb[k] = (st._cTul[g] * (1 - dry) + st._cPardo[g] * dry) * J.tono;
              ct[k] = J.enea ? st._cEsp[g] * (1 - 0.3 * dry) + st._cPardoP[g] * 0.3 * dry : st._cTulP[g] * (1 - dry) + st._cPardoP[g] * dry;
            }
            const q0 = i * 10;
            for (let f2 = 0; f2 < 2; f2++) {
              const q = q0 + f2 * 5, lu = f2 === 0 ? -dv : du, lv = f2 === 0 ? du : dv, w = J.w, wm = w * 0.7;
              put(q, J.u - lu * w, J.v - lv * w, h0); put(q + 1, J.u + lu * w, J.v + lv * w, h0);
              put(q + 2, mu - lu * wm, mv - lv * wm, mh); put(q + 3, mu + lu * wm, mv + lv * wm, mh);
              put(q + 4, tu, tv, th);
              const k = f2 ? 0.85 * l : l;
              col(q, cb, k); col(q + 1, cb, k); col(q + 2, cb, k * 1.05); col(q + 3, cb, k * 1.05); col(q + 4, ct, k);
            }
          }
          o.mTul.geometry.attributes.position.needsUpdate = true; o.mTul.geometry.attributes.color.needsUpdate = true;
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
