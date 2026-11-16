// Objeto «tostadora» (ficha: tostadora.json): una tostadora de café de tambor, de las de una tostaduría (≈ 3 m hasta la boca
// de la chimenea). OBJETO ARTICULADO (referencias/diseno/maqueta3d.md, «Objetos articulados»). Quedan quietos: el zócalo, la
// caja de atrás (donde se apoya el tambor), el hogar con su llama bajo el tambor, el soporte del frente, la TOLVA (pirámide
// invertida arriba), la CHIMENEA, el tablero de mando al costado derecho, el canal que baja del tambor y la BANDEJA de
// enfriamiento redonda al frente sobre su pedestal. Se mueven, en funciones puras de t (desfase por instancia con ctx.hash; el
// actor suma a `i` una semilla de su id):
//   · `tambor`: el cilindro horizontal (eje adelante-atrás) con sus costillas oscuras y la tapa del frente con su cruz: gira
//     continuo (≈ 0.45 vueltas/s), así el giro se lee de lado (las costillas pasan) y de frente (la cruz da vueltas);
//   · `brazo`: el brazo que remueve los granos en la bandeja (cuatro radios con sus rastrillos): gira lento (≈ 0.12 vueltas/s);
//   · `granos`: el café TOSTADO (un marrón oscuro del estilo) va con el brazo a la mitad de su paso: la cama se ve removida;
//   · `humo0`…`humo6`: el hilo de humo de la chimenea, una columna de bocanadas que suben, crecen y se apagan (escala 0 abajo
//     y arriba) en un ciclo de 3.6 s, como el vapor de la taza.
// En METROS (x adelante = hacia la bandeja, y arriba, z a su derecha; el origen en el suelo, al centro). Las partes con `tinte`
// (la carcasa) toman el color de la instancia (una de `variantes`; el protagonista, en el acento). Sin colores escritos: todo
// sale de ctx.tonos, ctx.COL y ctx.lin. Sin texto ni logos.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  const TAU = Math.PI * 2;
  // la geometría (metros)
  const XT = -0.5, YT = 1.45, RT = 0.5, LT = 1.3;     // tambor: centro, radio, largo (de x = -1.15 a 0.15)
  const XC = 0.85, YB = 0.6, RB = 0.6;                // bandeja: centro, base y radio
  const YG = 0.745;                                    // la cama de granos (arriba)
  const XH = -1.33, ZH = -0.38, YH = 3.0;             // la boca de la chimenea
  const NH = 7, PH = 3.6;                              // bocanadas de humo y su ciclo
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  const grupos = {
    tambor: { pivote: [XT, YT, 0] },
    brazo: { pivote: [XC, YG, 0] },
    granos: { pivote: [XC, YG, 0] },
  };
  for (let k = 0; k < NH; k++) grupos["humo" + k] = { pivote: [XH, YH + 0.08, ZH] };

  MAQ.OBJETOS.tostadora = {
    medidas: { largo_m: 2.95, ancho_m: 1.6, alto_m: 3.1 },
    grupos,
    // la carcasa: acero, acero claro o la tostadora pintada de rojo de las tostadurías (nunca el acento: ese es del protagonista)
    variantes(ctx) {
      const { tonos, COL, lin, ES } = ctx;
      if (ES.modo === 1 || ES.modo === 4) return [tonos.vehiculos[0].clone(), tonos.vehiculos[1].clone(), tonos.vehiculos[2].clone()];
      return [tonos.linea.clone().lerp(lin(COL.costa), 0.5), tonos.mal.clone().multiplyScalar(0.72), lin(COL.costa).multiplyScalar(0.7)];
    },
    pose(t, i, ctx) {
      const h = ctx.hash(i, 3), a = TAU * (0.45 * t + h), b = TAU * (0.12 * t + ctx.hash(i, 5));
      const P = { tambor: [-a, 0, 0], brazo: [0, b, 0], granos: [0, b * 0.5, 0] };
      for (let k = 0; k < NH; k++) {
        const u = (((t / PH + k / NH + ctx.hash(i, 9)) % 1) + 1) % 1;
        const vive = s3(u / 0.14) * (1 - s3((u - 0.62) / 0.38));
        const dz = 0.08 * Math.sin(TAU * (u * 0.9 + k * 0.37));
        P["humo" + k] = [0, 0, 0, -0.32 * u * u, 1.5 * u, dz, (0.55 + 1.9 * u) * vive];
      }
      return P;
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, g = (v) => new T.Color(v, v, v), noche = ES.modo === 1;
      const P = [];
      const est = (geo, v = 1, grupo) => P.push({ geo, color: g(v), tinte: true, grupo });
      const fijo = (geo, color, grupo, luz) => P.push({ geo, color, grupo, luz: luz || 0 });
      const oscuro = tonos.linea.clone().lerp(tonos.muro, 0.25);
      const acero = lin(COL.costa).lerp(tonos.linea, 0.28);
      const tostado = lin(COL.tierra_media).multiplyScalar(0.3).lerp(tonos.mal, 0.06);   // café tostado: marrón oscuro
      const tostado2 = tostado.clone().multiplyScalar(1.55);
      const humo = noche ? tonos.secundario.clone().lerp(tonos.techo, 0.5) : lin(COL.costa).lerp(tonos.secundario, 0.5);
      // ── el zócalo y la caja de atrás (donde se apoya el tambor; arriba van la tolva y la chimenea)
      fijo(B(T, 1.75, 0.38, 1.25, -0.62, 0, 0), oscuro);
      est(B(T, 0.36, 1.72, 1.22, -1.33, 0.38, 0));
      est(B(T, 0.42, 0.08, 1.3, -1.33, 2.1, 0), 0.8);                    // la cornisa
      // ── el hogar bajo el tambor, con la llama que se ve por su ranura
      est(B(T, 1.2, 0.5, 0.95, -0.55, 0.38, 0), 0.82);
      fijo(B(T, 0.9, 0.07, 0.97, -0.55, 0.55, 0), tonos.medio.clone(), undefined, noche ? 0.9 : 0.45);
      // ── el soporte del frente del tambor (el cojinete)
      est(B(T, 0.2, 0.2, 0.7, 0.05, 0.88, 0), 0.75);
      // ── la tolva: pirámide invertida sobre su cuello, con su borde
      fijo(new T.CylinderGeometry(0.1, 0.1, 0.22, 10).translate(-1.15, 2.29, 0), oscuro);
      est(new T.CylinderGeometry(0.5, 0.12, 0.6, 4, 1).rotateY(Math.PI / 4).translate(-1.15, 2.7, 0), 0.95);
      fijo(new T.CylinderGeometry(0.51, 0.51, 0.04, 4, 1).rotateY(Math.PI / 4).translate(-1.15, 3.0, 0), oscuro);
      // ── la chimenea: el tubo con su abrazadera y el sombrerete
      fijo(new T.CylinderGeometry(0.1, 0.1, YH - 2.18, 12).translate(XH, 2.18 + (YH - 2.18) / 2, ZH), acero);
      fijo(new T.CylinderGeometry(0.125, 0.125, 0.06, 12).translate(XH, 2.6, ZH), oscuro);
      fijo(new T.CylinderGeometry(0.12, 0.12, 0.05, 12).translate(XH, YH - 0.02, ZH), oscuro);
      // ── el tablero de mando al costado derecho, con sus dos luces y un reloj
      est(B(T, 0.38, 1.0, 0.14, -0.85, 0.75, 0.68), 0.88);
      fijo(B(T, 0.3, 0.4, 0.02, -0.85, 1.25, 0.76), oscuro);
      fijo(new T.CylinderGeometry(0.035, 0.035, 0.03, 10).rotateX(Math.PI / 2).translate(-0.93, 1.1, 0.76), tonos.bien.clone(), undefined, 0.6);
      fijo(new T.CylinderGeometry(0.035, 0.035, 0.03, 10).rotateX(Math.PI / 2).translate(-0.77, 1.1, 0.76), tonos.mal.clone(), undefined, 0.6);
      fijo(new T.CylinderGeometry(0.075, 0.075, 0.03, 16).rotateX(Math.PI / 2).translate(-0.85, 1.38, 0.775), acero);
      // ── el canal que baja de la boca del tambor a la bandeja
      fijo(new T.BoxGeometry(0.52, 0.05, 0.3).rotateZ(-0.62).translate(0.36, 1.0, 0), oscuro);
      fijo(new T.BoxGeometry(0.52, 0.1, 0.03).rotateZ(-0.62).translate(0.36, 1.04, 0.15), oscuro);
      fijo(new T.BoxGeometry(0.52, 0.1, 0.03).rotateZ(-0.62).translate(0.36, 1.04, -0.15), oscuro);
      // ── EL TAMBOR (grupo «tambor»): acero claro con ocho costillas oscuras a lo largo, dos aros y la tapa del frente con su cruz
      fijo(new T.CylinderGeometry(RT, RT, LT, 28).rotateZ(Math.PI / 2).translate(XT, YT, 0), acero, "tambor");
      for (let k = 0; k < 8; k++) {
        fijo(new T.BoxGeometry(LT + 0.02, 0.07, 0.1).translate(0, RT + 0.02, 0).rotateX(k * TAU / 8).translate(XT, YT, 0), oscuro, "tambor");
      }
      for (const x of [XT - LT / 2 + 0.12, XT + LT / 2 - 0.12]) {
        fijo(new T.TorusGeometry(RT + 0.03, 0.035, 6, 28).rotateY(Math.PI / 2).translate(x, YT, 0), oscuro, "tambor");
      }
      const xf = XT + LT / 2;
      fijo(new T.CylinderGeometry(RT - 0.02, RT - 0.02, 0.05, 28).rotateZ(Math.PI / 2).translate(xf + 0.02, YT, 0), acero.clone().multiplyScalar(1.08), "tambor");
      fijo(new T.BoxGeometry(0.05, 0.9, 0.11).translate(xf + 0.06, YT, 0), oscuro, "tambor");
      fijo(new T.BoxGeometry(0.05, 0.11, 0.9).translate(xf + 0.06, YT, 0), oscuro, "tambor");
      fijo(new T.CylinderGeometry(0.1, 0.1, 0.08, 14).rotateZ(Math.PI / 2).translate(xf + 0.08, YT, 0), oscuro, "tambor");
      fijo(new T.CylinderGeometry(0.06, 0.06, 0.06, 10).rotateZ(Math.PI / 2).translate(xf + 0.06, YT + 0.32, 0.12), tostado2, "tambor");   // la mirilla (marca fuera del eje)
      // ── LA BANDEJA de enfriamiento: pedestal, plato ancho y bajo con su borde (quietos)
      fijo(new T.CylinderGeometry(0.34, 0.42, YB, 16).translate(XC, YB / 2, 0), oscuro);
      est(new T.CylinderGeometry(RB, RB - 0.04, 0.15, 32).translate(XC, YB + 0.075, 0), 0.95);
      fijo(new T.TorusGeometry(RB, 0.028, 6, 32).rotateX(Math.PI / 2).translate(XC, YB + 0.15, 0), oscuro);
      // ── LOS GRANOS (grupo «granos»): la cama de café tostado y los granos sueltos encima, con un montículo al pie del canal
      fijo(new T.CylinderGeometry(RB - 0.04, RB - 0.04, 0.03, 32).translate(XC, YG - 0.03, 0), tostado, "granos");
      for (let k = 0; k < 90; k++) {
        const r = (RB - 0.08) * Math.sqrt(ctx.hash(k, 11)), a = TAU * ctx.hash(k, 12), s = 0.028 + 0.014 * ctx.hash(k, 13);
        const geo = new T.SphereGeometry(s, 5, 4).scale(1.3, 0.6, 0.9).rotateY(TAU * ctx.hash(k, 14))
          .translate(XC + r * Math.cos(a), YG + s * 0.3, r * Math.sin(a));
        fijo(geo, k % 3 ? tostado : tostado2, "granos");
      }
      fijo(new T.ConeGeometry(0.2, 0.08, 14).translate(XC - 0.36, YG + 0.04, 0), tostado, "granos");
      // ── EL BRAZO (grupo «brazo»): eje al centro con su remate y cuatro radios con rastrillos que se meten en los granos
      fijo(new T.CylinderGeometry(0.04, 0.04, 0.3, 10).translate(XC, YG + 0.15, 0), oscuro, "brazo");
      fijo(new T.CylinderGeometry(0.075, 0.075, 0.07, 12).translate(XC, YG + 0.3, 0), acero, "brazo");
      for (let k = 0; k < 4; k++) {
        const ang = k * TAU / 4;
        fijo(new T.BoxGeometry(RB - 0.1, 0.035, 0.05).translate((RB - 0.1) / 2, YG + 0.11, 0).rotateY(ang).translate(XC, 0, 0), oscuro, "brazo");
        for (const r of [0.18, 0.32, 0.46]) {
          fijo(new T.BoxGeometry(0.04, 0.12, 0.09).translate(r, YG + 0.04, 0).rotateY(ang).translate(XC, 0, 0), oscuro, "brazo");
        }
      }
      // ── EL HUMO (grupos «humo0»…): una bocanada por grupo en la boca de la chimenea; la pose la sube, la crece y la apaga
      for (let k = 0; k < NH; k++) {
        fijo(new T.IcosahedronGeometry(0.11, 1).translate(XH, YH + 0.08, ZH), humo, "humo" + k, noche ? 0.35 : 0.1);
      }
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
