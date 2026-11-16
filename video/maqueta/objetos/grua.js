// Objeto «grua» (ficha: grua.json): una grúa de muelle tipo pórtico (ship-to-shore) de ≈ 52 m que carga un contenedor de 20
// pies al barco. OBJETO ARTICULADO (referencias/diseno/maqueta3d.md, «Objetos articulados»): el pórtico (cuatro patas con sus
// carros de vía, vigas y diagonales), la pluma de dos vigas que vuela hacia el mar (x adelante = el mar), el castillete con sus
// tirantes y la casa de máquinas atrás quedan quietos; se mueven el CARRO por la pluma (dx), el SPREADER con su cabezal (dx, dy),
// los CABLES (siete tramos telescópicos que se reparten la bajada: nunca se ve un hueco ni un cable que sobre) y la CARGA.
// Ciclo de 9.6 s, función pura de t (desfase por instancia con ctx.hash): el spreader toma el contenedor en el muelle, entre las
// patas → sube → el carro corre por la pluma hasta el alcance (32 m adelante del origen) → baja a la cubierta y el contenedor
// entra en la bodega (queda dentro del casco del barco) → el spreader sube vacío, vuelve y baja por el siguiente.
// En METROS (x adelante, y arriba, z a su derecha; el origen en el suelo, al centro de la base del pórtico). Para que la carga
// entre en un barco, el barco va atracado con su eje a ≈ 32 m adelante de la grúa (rumbo de la grúa = hacia el mar).
// Las partes de la estructura llevan `tinte` (el color de la instancia: una de `variantes`; el protagonista, en el acento); la
// carga va en un tono fijo distinto. Sin colores escritos: todo sale de ctx.tonos y ctx.COL. Sin texto ni logos.
(function (MAQ) {
  const B = (T, l, h, w, x, y, z) => new T.BoxGeometry(l, h, w).translate(x, y + h / 2, z);   // caja con la base en y
  // una barra de sección g entre dos puntos (diagonales, tirantes)
  const barra = (T, a, b, g) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), n = d.length();
    return new T.BoxGeometry(n, g, g).applyQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(1, 0, 0), d.normalize()))
      .translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  // la geometría (metros)
  const XL = -11, XW = 9, ZP = 8.5;                 // patas: lado tierra, lado mar; media separación entre las dos vías
  const YV = 38, YP = 40.8, ZV = 3.6;               // pluma: de y = 38 a 40.8, dos vigas en z = ±3.6
  const XB0 = -30, XB1 = 52;                         // pluma: de la casa de máquinas a la punta sobre el mar
  const YT = 36.2;                                   // fondo del carro: de aquí cuelgan los cables
  const XQ = -1, XS = 32;                            // el carro: sobre el muelle (entre las patas) y en el alcance
  const CH = 4.39;                                   // del gancho (arriba del cabezal) al fondo del contenedor
  const D_MIN = YT - (26 + CH);                      // arriba: el contenedor a 26 m del suelo (libra la pila del barco)
  const D_Q = YT - (0 + CH);                         // en el muelle: el contenedor en el suelo
  const D_B = YT - (8 + CH);                         // en el barco: el contenedor dentro de la bodega (cubierta a 11.4 m)
  const NC = 7, LC = D_Q / NC;                       // tramos de cable (los de abajo bajan más)
  const PER = 9.6;
  const S = (a, b, u) => { const x = Math.min(1, Math.max(0, (u - a) / (b - a))); return x * x * (3 - 2 * x); };
  // el estado del ciclo en t: x del carro, largo del cable, dónde está la carga (dx, dy desde su reposo)
  function ciclo(t, i, ctx) {
    const u = (((t + ctx.hash(i, 7) * PER) % PER) + PER) % PER / PER;
    let x, d, cx, cd;
    if (u < 0.06) { x = XQ; d = D_Q; }                                         // toma el contenedor
    else if (u < 0.26) { x = XQ; d = D_Q + (D_MIN - D_Q) * S(0.06, 0.26, u); } // sube
    else if (u < 0.48) { x = XQ + (XS - XQ) * S(0.26, 0.48, u); d = D_MIN; }  // corre hacia el mar
    else if (u < 0.69) { x = XS; d = D_MIN + (D_B - D_MIN) * S(0.48, 0.64, u); } // baja a la bodega y suelta
    else if (u < 0.78) { x = XS; d = D_B + (D_MIN - D_B) * S(0.69, 0.78, u); } // sube vacío
    else if (u < 0.90) { x = XS + (XQ - XS) * S(0.78, 0.90, u); d = D_MIN; }  // vuelve
    else { x = XQ; d = D_MIN + (D_Q - D_MIN) * S(0.90, 1.0, u); }             // baja por el siguiente
    if (u < 0.69) { cx = x; cd = d; }                 // la carga va colgada
    else if (u < 0.78) { cx = XS; cd = D_B; }         // queda en la bodega (dentro del casco)
    else { cx = XQ; cd = D_Q; }                       // el siguiente, ya en el muelle
    return { x, d, cx, cd };
  }
  const grupos = { carro: { pivote: [0, 0, 0] }, gancho: { pivote: [0, 0, 0] }, carga: { pivote: [0, 0, 0] } };
  for (let k = 0; k < NC; k++) grupos["cable" + k] = { pivote: [0, 0, 0] };

  MAQ.OBJETOS.grua = {
    // largo y ancho: la base del pórtico (la sombra de contacto y el espacio en el muelle); la pluma vuela 43 m sobre el mar
    medidas: { largo_m: 22.0, ancho_m: 19.0, alto_m: 52.0 },
    grupos,
    variantes(ctx) {
      const t = ctx.tonos;
      return [t.medio.clone().multiplyScalar(0.95), t.mal.clone().multiplyScalar(0.85), ctx.lin(ctx.COL.costa).multiplyScalar(0.95)];
    },
    pose(t, i, ctx) {
      const c = ciclo(t, i, ctx), P = { carro: [0, 0, 0, c.x - XQ, 0, 0], gancho: [0, 0, 0, c.x - XQ, D_MIN - c.d, 0],
        carga: [0, 0, 0, c.cx - XQ, D_MIN - c.cd, 0] };
      for (let k = 0; k < NC; k++) P["cable" + k] = [0, 0, 0, c.x - XQ, -(c.d - D_MIN) * (k + 0.5) / NC, 0];
      return P;
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, g = (v) => new T.Color(v, v, v), noche = ES.modo === 1;
      const P = [], est = (geo, v = 1) => P.push({ geo, color: g(v), tinte: true });
      const fijo = (geo, color, grupo, luz) => P.push({ geo, color, grupo, luz: luz || 0 });
      const oscuro = tonos.linea.clone().lerp(tonos.muro, 0.25), casa = tonos.muro.clone().lerp(lin(COL.costa), 0.4);
      const vidrio = tonos.linea.clone().lerp(lin(COL.luces), noche ? 0.7 : 0.2), foco = lin(COL.luces);
      // ── el pórtico: cuatro patas sobre sus carros de vía, las vigas a lo largo de cada vía, los cabezales y diagonales
      for (const x of [XL, XW]) for (const z of [-ZP, ZP]) {
        est(B(T, 1.8, YV - 1.2, 1.8, x, 1.2, z));
        fijo(B(T, 5.0, 1.2, 1.4, x, 0, z), oscuro);                       // el carro de vía (bogie)
      }
      for (const z of [-ZP, ZP]) {
        est(B(T, XW - XL + 1.8, 1.8, 1.5, (XL + XW) / 2, 12.5, z), 0.92);  // viga del portal (la carga pasa por dentro)
        est(barra(T, [XL, 14.3, z], [XW, YV - 1, z], 0.9), 0.85);          // diagonal
        est(B(T, XW - XL + 1.8, 1.4, 1.5, (XL + XW) / 2, YV - 1.6, z), 0.92);
      }
      for (const x of [XL, XW]) est(B(T, 1.8, 2.0, 2 * ZP + 1.8, x, YV - 0.4, 0), 0.92);   // cabezales bajo la pluma
      // ── la pluma: dos vigas de la casa de máquinas a la punta, con traviesas arriba y el riel del carro
      for (const z of [-ZV, ZV]) {
        est(B(T, XB1 - XB0, YP - YV, 1.3, (XB0 + XB1) / 2, YV, z));
        fijo(B(T, XB1 - XB0, 0.25, 0.5, (XB0 + XB1) / 2, YV - 0.25, z * 0.88), oscuro);   // el riel
      }
      for (let x = XB0 + 4; x < XB1; x += 8) est(B(T, 0.6, 0.6, 2 * ZV + 1.3, x, YP - 0.6, 0), 0.8);
      // ── el castillete sobre las patas del mar, con los tirantes a la punta y atrás
      const YA = 52, XA = XW - 2;
      for (const z of [-ZV, ZV]) {
        est(barra(T, [XW, YP, z], [XA, YA, z * 0.7], 1.3));
        est(barra(T, [XL + 2, YP, z], [XA, YA, z * 0.7], 1.1), 0.9);
        est(barra(T, [XA, YA, z * 0.7], [XB1 - 1, YP, z], 0.55), 0.85);    // tirante a la punta
        est(barra(T, [XA, YA, z * 0.7], [XS - 6, YP, z], 0.5), 0.85);      // tirante intermedio
        est(barra(T, [XA, YA, z * 0.7], [XB0 + 2, YP + 4, z], 0.55), 0.85); // tirante atrás
      }
      est(B(T, 1.4, 1.2, 2 * ZV * 0.7 + 1.3, XA, YA - 1.2, 0), 0.9);
      // ── la casa de máquinas atrás (clara), con su franja de ventanas
      fijo(B(T, 10, 4.6, 9, XB0 + 5, YP, 0), casa);
      fijo(B(T, 10.1, 0.9, 9.1, XB0 + 5, YP + 2.6, 0), vidrio, undefined, noche ? 0.6 : 0);
      // ── balizas (de noche brillan): la punta de la pluma y lo alto del castillete
      fijo(new T.SphereGeometry(0.6, 8, 6).translate(XB1 - 0.5, YP + 0.7, 0), tonos.mal, undefined, noche ? 1 : 0.2);
      fijo(new T.SphereGeometry(0.6, 8, 6).translate(XA, YA + 0.5, 0), tonos.mal, undefined, noche ? 1 : 0.2);
      if (noche) for (let x = XB0 + 10; x < XB1; x += 14) fijo(B(T, 1.2, 0.3, 1.2, x, YV - 0.55, 0), foco, undefined, 1);   // reflectores bajo la pluma
      // ── el CARRO (grupo «carro»): la caja entre las vigas, sus ruedas y la cabina del operador colgada al costado
      est(B(T, 5.4, YV + 1.6 - YT, 2 * ZV - 1.3, XQ, YT, 0), 0.75); P[P.length - 1].grupo = "carro";
      fijo(B(T, 5.8, 0.6, 2 * ZV * 0.88 + 0.6, XQ, YV - 0.2, 0), oscuro, "carro");
      fijo(B(T, 0.5, 0.5, ZV + 2.2 - ZV + 2.4, XQ + 1.4, YT + 0.2, ZV + 0.3), oscuro, "carro");
      fijo(B(T, 2.6, 2.4, 2.2, XQ + 1.4, YT - 1.6, ZV + 2.2), casa, "carro");
      fijo(B(T, 2.65, 0.9, 2.25, XQ + 1.4, YT - 0.4, ZV + 2.2), vidrio, "carro", noche ? 0.7 : 0);
      // ── los CABLES: siete tramos telescópicos de cuatro líneas, del carro al cabezal
      for (let k = 0; k < NC; k++) {
        const yc = YT - D_MIN * (k + 0.5) / NC;
        for (const x of [-1.5, 1.5]) for (const z of [-0.6, 0.6]) fijo(B(T, 0.26, LC, 0.26, XQ + x, yc - LC / 2, z), oscuro, "cable" + k);
      }
      // ── el SPREADER (grupo «gancho»): el cabezal donde llegan los cables y el bastidor que abraza el contenedor
      const YH = YT - D_MIN;                                       // arriba del cabezal en reposo (la grúa con la carga arriba)
      fijo(B(T, 3.6, 1.0, 1.8, XQ, YH - 1.0, 0), oscuro, "gancho");
      const spr = tonos.medio.clone().lerp(tonos.linea, 0.35);
      fijo(B(T, 6.2, 0.8, 0.7, XQ, YH - 1.8, 0), spr, "gancho");
      for (const s of [-1, 1]) {
        fijo(B(T, 0.6, 0.8, 2.5, XQ + s * 2.85, YH - 1.8, 0), spr, "gancho");
        fijo(B(T, 6.2, 0.35, 0.3, XQ, YH - 1.45, s * 1.1), spr, "gancho");
      }
      // ── la CARGA (grupo «carga»): un contenedor de 20 pies (6.06 × 2.44 × 2.59 m), con acanalado y puertas, en un tono fijo
      const YC = YH - CH, cc = tonos.mal.clone().multiplyScalar(0.8), cm = cc.clone().multiplyScalar(0.7), cr = cc.clone().multiplyScalar(1.1);
      fijo(B(T, 5.9, 2.4, 2.36, XQ, YC + 0.1, 0), cc, "carga");
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) fijo(B(T, 0.16, 2.59, 0.16, XQ + sx * 2.95, YC, sz * 1.14), cm, "carga");
      for (const sz of [-1, 1]) for (const y of [0, 2.43]) fijo(B(T, 6.06, 0.16, 0.14, XQ, YC + y, sz * 1.15), cm, "carga");
      for (let k = 0; k < 10; k++) for (const sz of [-1, 1]) fijo(B(T, 0.18, 2.25, 0.06, XQ - 2.6 + k * 0.58, YC + 0.17, sz * 1.2), cr, "carga");
      for (const z of [-0.85, -0.3, 0.3, 0.85]) fijo(B(T, 0.08, 2.3, 0.05, XQ - 3.07, YC + 0.15, z), cm, "carga");
      return P;
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
