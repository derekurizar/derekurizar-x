// Objeto «bodega» (ficha: bodega.json): el BENEFICIO SECO, una galera industrial de 18 × 30 m con techo de lámina a dos aguas
// sobre cerchas de hierro, ABIERTA al frente (x adelante = la entrada), con los muros de los costados y del fondo de lámina
// acanalada sobre un zócalo bajo (sin ventanas: no es una casa). Adentro, la línea de la trilla, de la izquierda (z+) a la
// derecha (z−) vista desde la entrada: el elevador (tubo vertical) que sube el pergamino a la TOLVA de la trilladora; la
// trilladora (cuerpo pintado, el color de la instancia; el protagonista, en el acento) con su volante y su motor; la zaranda
// que clasifica; una BANDA inclinada que saca el café oro (grano verde) hasta la ensacadora, con un saco en la boca. Junto a la
// entrada, las estibas de sacos de yute sobre tarimas.
// ARTICULADO (referencias/diseno/maqueta3d.md, «Objetos articulados»): `polea` (el volante de la trilladora) y `polea2` (la del
// motor) giran; `zaranda` vibra de lado a lado; `banda` (las tablillas y el grano sobre la banda) avanza hacia la ensacadora.
// `pose(t, i)` es función pura de t con el desfase de la instancia (ctx.hash(i)). Lo demás es rígido.
// En METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro de la planta). Para que un camión llegue a su
// puerta: el camión a ≈ 13 m adelante de la bodega, mirando hacia afuera (su rumbo = el de la bodega).
// Sin colores escritos: todo sale de ctx.tonos y ctx.COL. Sin texto ni logos.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  // una barra de sección g × w entre dos puntos (cerchas, nervios de la lámina, la banda inclinada)
  const barra = (T, a, b, g, w) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), n = d.length();
    return new T.BoxGeometry(n, g, w === undefined ? g : w).applyQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(1, 0, 0), d.normalize()))
      .translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  // una tolva: tronco de pirámide cuadrada (lado arriba la, abajo lb), de y0 a y1
  const TOLVA = (T, la, lb, x, y0, y1, z) => new T.CylinderGeometry(la / Math.SQRT2, lb / Math.SQRT2, y1 - y0, 4, 1)
    .rotateY(Math.PI / 4).translate(x, (y0 + y1) / 2, z);
  // un saco tendido (0.62 × 1.06 × 0.36), largo a lo largo de z (giro 0) o de x (giro π/2)
  const SACO = (T, x, y, z, giro) => new T.CapsuleGeometry(0.31, 0.44, 2, 6).rotateX(Math.PI / 2).scale(1, 0.58, 1)
    .rotateY(giro).translate(x, y + 0.18, z);
  // la nave
  const XA = 8, ZA = 14, YE = 7.0, YR = 9.6, VOL = 1.0;     // media profundidad, medio ancho, alero, cumbrera, vuelo del techo
  const PEND = (YR - YE) / XA;
  const yTecho = (x) => YR - PEND * Math.abs(x);            // la cara de abajo del techo en x
  // la línea de la trilla
  const CX = -0.8, CZ = 7.0;                                // la trilladora
  const PZ = [CX + 1.35, 2.0, CZ], RP = 0.65;                   // el volante (eje a lo largo de x, de cara a la entrada)
  const PM = [CX + 1.35, 0.55, CZ], RM = 0.22;                  // la polea del motor
  const ZZ = 4.3;                                           // la zaranda
  const BZ0 = 3.4, BZ1 = -4.6, BY0 = 0.75, BY1 = 1.9;       // la banda: de la zaranda (abajo) a la ensacadora (arriba)
  const BL = Math.hypot(BZ1 - BZ0, BY1 - BY0), BU = [(BZ1 - BZ0) / BL, (BY1 - BY0) / BL];   // largo y dirección (z, y)
  const PASO = 0.6, VB = 0.9;                               // la banda: separación de las tablillas, m/s
  const NB = Math.floor((BL - PASO - 0.3) / PASO);
  const bpt = (s, h) => [CX, BY0 + BU[1] * s + h, BZ0 + BU[0] * s];   // un punto sobre la banda a s metros, h arriba (x, y, z)

  MAQ.OBJETOS.bodega = {
    medidas: { largo_m: 18.0, ancho_m: 30.0, alto_m: 9.8 },
    grupos: {
      polea: { pivote: PZ.slice() },
      polea2: { pivote: PM.slice() },
      zaranda: { pivote: [CX, 1.3, ZZ] },
      banda: { pivote: [CX, BY0, BZ0] },
    },
    variantes(ctx) {
      const t = ctx.tonos;
      return [t.medio.clone().multiplyScalar(0.92), t.mal.clone().multiplyScalar(0.82), t.bien.clone().multiplyScalar(0.72)];
    },
    pose(t, i, ctx) {
      const h = ctx.hash(i, 3), w = 2 * Math.PI * 1.4 * t + h * 6.283;
      const s = ((((t + h * 5) * VB) % PASO) + PASO) % PASO;   // lo que avanzó la banda dentro de un paso
      return {
        polea: [w, 0, 0],
        polea2: [w * RP / RM, 0, 0],
        zaranda: [0, 0, 0, 0, 0.015 * Math.sin(2 * Math.PI * 8 * t + h * 9), 0.11 * Math.sin(2 * Math.PI * 4 * t + h * 7)],
        banda: [0, 0, 0, 0, BU[1] * s, BU[0] * s],
      };
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES, hash } = ctx, g = (v) => new T.Color(v, v, v), noche = ES.modo === 1, plano = ES.modo === 4;
      const P = [], put = (geo, color, grupo, luz) => P.push({ geo, color, grupo, luz: luz || 0 });
      const maq = (geo, v = 1, grupo) => P.push({ geo, color: g(v), tinte: true, grupo });
      // tonos: la lámina galvanizada (clara, un poco fría), el hierro (oscuro), el zócalo y el piso de concreto, el yute, el café oro
      const frio = COL.ambiente ? lin(COL.ambiente) : tonos.secundario.clone();
      const lamina = plano ? tonos.techo.clone() : tonos.muro.clone().lerp(tonos.linea, noche ? 0.1 : 0.22).lerp(frio, 0.25);
      const techo = plano ? tonos.techo.clone() : lamina.clone().lerp(frio, 0.2).multiplyScalar(noche ? 1.15 : 1.05);
      const nervio = lamina.clone().multiplyScalar(0.82), traslucida = techo.clone().lerp(tonos.secundario, 0.45);
      const hierro = tonos.linea.clone().lerp(tonos.muro, 0.28), hierro2 = tonos.linea.clone().lerp(tonos.muro, 0.12);
      const zocalo = tonos.muro.clone().lerp(tonos.arena, 0.35).multiplyScalar(0.9), piso = tonos.pavimento.clone().multiplyScalar(0.92);
      const madera = tonos.muro.clone().lerp(tonos.arena, 0.55).multiplyScalar(0.72);
      const yute = noche ? lin(COL.luces).clone().lerp(tonos.techo, 0.5).multiplyScalar(0.8)
        : plano ? tonos.techo.clone().lerp(tonos.linea, 0.18) : tonos.arena.clone().lerp(tonos.linea, 0.12);
      const sacos = [yute, yute.clone().multiplyScalar(0.85), yute.clone().lerp(tonos.secundario, 0.15)];
      const oro = tonos.bien.clone().lerp(tonos.arena, 0.55), cinta = tonos.linea.clone().lerp(tonos.muro, 0.08);
      const claro = tonos.secundario.clone().lerp(tonos.muro, 0.3);

      // ── el piso de concreto (apenas sobre el terreno)
      put(B(T, 2 * XA + 1.2, 0.2, 2 * ZA + 1.2, 0, -0.12, 0), piso);
      // ── las columnas de hierro (frente abierto y fondo), con su placa de base
      for (const x of [-XA, XA]) for (let z = -ZA; z <= ZA; z += 7) {
        put(B(T, 0.32, YE, 0.28, x, 0, z), hierro);
        put(B(T, 0.6, 0.06, 0.6, x, 0.08, z), hierro2);
      }
      // ── las cerchas (una por columna): cuerda baja, cuerdas altas bajo el techo, montantes y diagonales
      const yc = (x) => yTecho(x) - 0.18;
      for (let z = -ZA; z <= ZA; z += 7) {
        put(barra(T, [-XA, YE, z], [XA, YE, z], 0.2, 0.16), hierro);
        for (const s of [-1, 1]) {
          put(barra(T, [s * (XA + VOL), yc(XA + VOL), z], [0, yc(0), z], 0.22, 0.16), hierro);
          const xs = [0, XA / 3, 2 * XA / 3, XA].map((v) => s * v);
          for (let k = 1; k < 3; k++) put(barra(T, [xs[k], YE, z], [xs[k], yc(xs[k]), z], 0.1), hierro);
          for (let k = 1; k < 4; k++) put(barra(T, [xs[k], YE, z], [xs[k - 1], yc(xs[k - 1]), z], 0.1), hierro);
        }
        put(barra(T, [0, YE, z], [0, yc(0), z], 0.12), hierro);
      }
      put(B(T, 0.24, 0.3, 2 * ZA, XA, YE - 0.3, 0), hierro);               // la viga del frente abierto
      // ── las costaneras (a lo largo, bajo la lámina)
      for (const s of [-1, 1]) for (const x of [1, 3, 5, 7, XA + VOL - 0.2]) put(B(T, 0.14, 0.14, 2 * ZA + 1.4, s * x, yTecho(x) - 0.16, 0), hierro2);
      // ── el techo a dos aguas: la lámina, sus nervios, dos franjas de lámina traslúcida por agua y la cumbrera
      for (const s of [-1, 1]) {
        const a = [s * (XA + VOL), yTecho(XA + VOL) + 0.03], b = [0, YR + 0.03];
        put(barra(T, [a[0], a[1], 0], [b[0], b[1], 0], 0.06, 2 * ZA + 1.6), techo);
        for (let z = -ZA - 0.6; z <= ZA + 0.61; z += 0.75) put(barra(T, [a[0], a[1] + 0.06, z], [b[0], b[1] + 0.06, z], 0.07), nervio);
        for (const z of [-7, 7]) put(barra(T, [s * (XA - 0.5), yTecho(XA - 0.5) + 0.1, z], [s * 1.0, yTecho(1.0) + 0.1, z], 0.03, 1.4), traslucida);
      }
      put(B(T, 0.9, 0.14, 2 * ZA + 1.6, 0, YR, 0), nervio);
      // ── los muros: zócalo bajo y lámina acanalada en los costados (con su hastial) y en el fondo; el frente queda abierto
      const ZOC = 1.0;
      put(B(T, 0.25, ZOC, 2 * ZA, -XA, 0, 0), zocalo);
      put(B(T, 0.08, YE - ZOC, 2 * ZA, -XA - 0.05, ZOC, 0), lamina);
      for (let z = -ZA + 0.4; z < ZA; z += 0.8) put(B(T, 0.06, YE - ZOC, 0.07, -XA - 0.12, ZOC, z), nervio);
      const hastial = new T.Shape();
      hastial.moveTo(-XA, ZOC); hastial.lineTo(XA, ZOC); hastial.lineTo(XA, YE); hastial.lineTo(0, YR); hastial.lineTo(-XA, YE); hastial.lineTo(-XA, ZOC);
      for (const s of [-1, 1]) {
        put(B(T, 2 * XA, ZOC, 0.25, 0, 0, s * ZA), zocalo);
        put(new T.ExtrudeGeometry(hastial, { depth: 0.08, bevelEnabled: false }).translate(0, 0, s * (ZA + 0.05) - 0.04), lamina);
        for (let x = -XA + 0.4; x < XA; x += 0.8) put(B(T, 0.07, yTecho(x) - ZOC - 0.05, 0.06, x, ZOC, s * (ZA + 0.12)), nervio);
      }
      // de noche, las lámparas bajo la cumbrera
      if (noche) for (const z of [-10.5, -3.5, 3.5, 10.5]) put(B(T, 0.5, 0.15, 0.5, 0, YR - 0.6, z), lin(COL.luces), undefined, 1);

      // ── el ELEVADOR: la fosa donde se vacía el pergamino, el tubo vertical, su cabeza y el ducto a la tolva
      put(B(T, 1.2, 0.5, 1.2, CX - 2, 0, CZ + 2.4), hierro2);
      maq(B(T, 0.5, 5.6, 0.5, CX - 2, 0.5, CZ + 2.4), 0.85);
      maq(B(T, 0.85, 0.7, 0.75, CX - 2, 6.0, CZ + 2.4), 0.95);
      put(barra(T, [CX - 2, 6.2, CZ + 2.1], [CX, 4.25, CZ + 0.5], 0.26), hierro);
      // ── la TRILLADORA: patas, cuerpo (el color de la instancia), tapa, la tolva arriba y el ducto de salida
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) put(B(T, 0.16, 1.2, 0.16, CX + sx * 1.0, 0, CZ + sz * 0.75), hierro);
      maq(B(T, 2.4, 1.6, 1.8, CX, 1.2, CZ));
      put(B(T, 2.5, 0.12, 1.9, CX, 2.8, CZ), hierro2);
      maq(TOLVA(T, 2.0, 0.6, CX, 2.92, 4.3, CZ), 0.88);
      put(B(T, 2.05, 0.1, 2.05, CX, 4.28, CZ), hierro2);
      maq(B(T, 0.5, 0.5, 0.4, CX, 1.25, CZ - 1.1), 0.8);                    // la boca hacia la zaranda
      // el motor (en el piso, frente al volante), las fajas y las dos poleas que giran (rayos claros para que se lea el giro)
      put(B(T, 0.75, 0.6, 0.7, CX + 1.85, 0.12, CZ), hierro2);
      put(B(T, 0.9, 0.12, 0.9, CX + 1.85, 0, CZ), hierro);
      for (const s of [-1, 1]) put(barra(T, [PM[0], PM[1], PM[2] + s * RM], [PZ[0], PZ[1], PZ[2] + s * RP], 0.07), cinta);
      const polea = (c, r, grupo, n) => {
        put(new T.CylinderGeometry(r, r, 0.14, 20).rotateZ(Math.PI / 2).translate(c[0], c[1], c[2]), hierro, grupo);
        for (let k = 0; k < n; k++) {
          const a = k * Math.PI / n;
          put(B(T, 0.05, 0.1, 2 * r * 0.92, 0, -0.05, 0).rotateX(a).translate(c[0] + 0.08, c[1], c[2]), claro, grupo);
        }
        put(B(T, 0.06, 0.18, 0.18, 0, -0.09, 0).translate(c[0] + 0.09, c[1] + r * 0.72, c[2]), tonos.mal, grupo);   // una marca
      };
      polea(PZ, RP, "polea", 3);
      polea(PM, RM, "polea2", 1);
      // ── la ZARANDA: el bastidor sobre resortes (quieto) y la bandeja con el grano (vibra)
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
        put(B(T, 0.12, 1.0, 0.12, CX + sx * 0.85, 0, ZZ + sz * 0.7), hierro);
        put(new T.CylinderGeometry(0.1, 0.1, 0.25, 8).translate(CX + sx * 0.85, 1.12, ZZ + sz * 0.7), hierro2);
      }
      maq(B(T, 2.0, 0.08, 1.6, CX, 1.25, ZZ), 0.9, "zaranda");
      for (const sx of [-1, 1]) maq(B(T, 0.08, 0.28, 1.6, CX + sx * 0.96, 1.25, ZZ), 0.8, "zaranda");
      for (const sz of [-1, 1]) maq(B(T, 2.0, 0.28, 0.08, CX, 1.25, ZZ + sz * 0.76), 0.8, "zaranda");
      put(B(T, 1.8, 0.07, 1.4, CX, 1.33, ZZ), oro, "zaranda");
      // ── la BANDA inclinada: largueros, la cinta, rodillos, patas; las tablillas y el grano (grupo «banda») avanzan
      const ini = bpt(0, 0), fin = bpt(BL, 0);
      for (const sx of [-1, 1]) put(barra(T, [CX + sx * 0.46, ini[1] - 0.05, ini[2]], [CX + sx * 0.46, fin[1] - 0.05, fin[2]], 0.2, 0.08), hierro);
      put(barra(T, [CX, ini[1] + 0.02, ini[2]], [CX, fin[1] + 0.02, fin[2]], 0.05, 0.84), cinta);
      for (const p of [ini, fin]) put(new T.CylinderGeometry(0.13, 0.13, 0.96, 10).rotateZ(Math.PI / 2).translate(CX, p[1] - 0.02, p[2]), hierro2);
      for (let s = 0.4; s < BL; s += 2.0) {
        const p = bpt(s, 0);
        for (const sx of [-1, 1]) put(B(T, 0.08, p[1] - 0.15, 0.08, CX + sx * 0.46, 0, p[2]), hierro);
      }
      for (let k = 0; k < NB; k++) {
        const s0 = 0.15 + k * PASO, p = bpt(s0, 0.05);
        put(barra(T, [CX - 0.4, p[1], p[2]], [CX + 0.4, p[1], p[2]], 0.05, 0.05), hierro2, "banda");
        for (let j = 0; j < 3; j++) {
          const q = bpt(s0 + 0.15 + j * 0.13, 0.06);
          put(new T.SphereGeometry(0.11, 6, 4).scale(1.5, 0.55, 1).translate(CX + (hash(k * 3 + j, 21) - 0.5) * 0.45, q[1], q[2]), oro, "banda");
        }
      }
      // ── la ENSACADORA al final de la banda: su tolva sobre patas y el saco que se llena
      const ZE = BZ1 - 0.45;
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) put(B(T, 0.08, 1.7, 0.08, CX + sx * 0.45, 0, ZE + sz * 0.45), hierro);
      maq(TOLVA(T, 1.0, 0.35, CX, 1.15, 1.75, ZE), 0.85);
      put(new T.CapsuleGeometry(0.32, 0.42, 2, 8).translate(CX, 0.53, ZE), yute);
      // ── las ESTIBAS junto a la entrada: sacos cruzados por cama sobre tarimas de madera
      const estiba = (x0, z0, camas) => {
        put(B(T, 2.3, 0.14, 3.3, x0, 0, z0), madera);
        for (let c = 0; c < camas; c++) {
          const y = 0.14 + c * 0.34, a = c % 2 === 0;
          const nx = a ? 3 : 2, nz = a ? 3 : 5, px = a ? 0.68 : 1.08, pz = a ? 1.08 : 0.66;
          for (let ix = 0; ix < nx; ix++) for (let iz = 0; iz < nz; iz++) {
            const n = (x0 * 31 + z0 * 7 + c * 13 + ix * 5 + iz) | 0;
            P.push({ geo: SACO(T, x0 + (ix - (nx - 1) / 2) * px + (hash(n, 11) - 0.5) * 0.07, y,
              z0 + (iz - (nz - 1) / 2) * pz + (hash(n, 12) - 0.5) * 0.07, (a ? 0 : Math.PI / 2) + (hash(n, 13) - 0.5) * 0.18),
              color: sacos[(c + Math.floor(hash(n, 14) * 3)) % 3] });
          }
        }
      };
      estiba(4.6, -8.3, 6);
      estiba(4.6, -11.9, 5);
      estiba(1.6, -11.9, 3);
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
