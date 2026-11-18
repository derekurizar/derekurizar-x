// Objeto «poc» (ficha: poc.json): un zambullidor pequeño y robusto que nada bajo en el agua (el poc de Atitlán; genérico:
// cuerpo redondo pardo grisáceo oscuro, alas pequeñas plegadas, cuello corto, cabeza redonda y un pico grueso y pálido con
// una marca negra que lo rodea). Un macho medía 525 mm: el cuerpo mide ≈ 0.52 m de la cola a la punta del pico. En METROS
// (x adelante = el pico, y arriba, z a su derecha; el origen en la línea de flotación, al centro). Lo dibujan las piezas
// que lo `usa`n (actor, flujo) con ctx.flota; con `tamano` 3–4 se lee junto al tul de una orilla.
// ARTICULADO: `ave` (todo lo que flota: se mece y se zambulle de cabeza) → `cabeza` (cuello, cabeza y pico; pivote en la
// base del cuello: cabecea con cada patada y mira a los lados); `anillo` (no sigue al ave: queda en el agua) los anillos
// que abre al hundirse y al salir; `estela` la V de ondas que deja al nadar, que crece con la velocidad.
// POSES: `nadar` (por defecto: nada 5–8 s y se zambulle; bajo el agua ≈ 3 s, abreviado para que se lea en un plano),
// `bucear` (el ritmo que vio la referencia: nada ≈ 8 s y se queda ≈ 20 s bajo el agua), `flotar` (descansa al abrigo del
// tul, el cuello recogido, sin zambullirse). Todo es función pura de t (fase por instancia con ctx.hash). No vuela: no
// hay pose de vuelo. Sin luces: de noche se lee por el pico claro y los anillos. Sin colores escritos.
(function (MAQ) {
  const TAU = 2 * Math.PI;
  const s3 = (u) => { const v = Math.max(0, Math.min(1, u)); return v * v * (3 - 2 * v); };
  const fr = (x) => ((x % 1) + 1) % 1;
  // el cuello y la cabeza: base del cuello, centro de la cabeza, el pico
  const NX = 0.11, NY = 0.09, HX = 0.152, HY = 0.172, RH = 0.048;
  // un elipsoide (radios en x, y, z) centrado en c
  const ovo = (T, c, rx, ry, rz, seg) => new T.SphereGeometry(1, seg || 20, Math.max(10, (seg || 20) * 0.6 | 0)).scale(rx, ry, rz).translate(c[0], c[1], c[2]);
  // un cilindro de a a b
  const vara = (T, a, b, r0, r1, seg) => {
    const d = new T.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), l = d.length();
    const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize());
    return new T.CylinderGeometry(r1, r0, l, seg).applyQuaternion(q).translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2);
  };
  // el ritmo de cada pose: segundos en la superficie (mín, rango) y bajo el agua
  const RITMO = { nadar: [5, 3, 3.0], bucear: [8, 2, 20] };
  const BAJA = 0.7, SUBE = 0.6;      // lo que tarda en hundirse de cabeza y en salir
  MAQ.OBJETOS.poc = {
    medidas: { largo_m: 0.52, ancho_m: 0.22, alto_m: 0.3 },
    poses: ["nadar", "bucear", "flotar"],
    grupos: {
      ave: { pivote: [0.02, 0, 0] },
      cabeza: { pivote: [NX, NY, 0], padre: "ave" },
      anillo: { pivote: [0, 0, 0] },
      estela: { pivote: [-0.2, 0, 0] },
    },
    // el plumaje por instancia: pardo grisáceo oscuro (más pardo, más gris, más oscuro); el protagonista, en el acento
    variantes(ctx) {
      const t = ctx.tonos, noche = ctx.ES.modo === 1;
      const base = t.asfalto.clone().lerp(t.techo, 0.22).lerp(t.linea, 0.1).multiplyScalar(noche ? 1.15 : 0.62);
      return [base, base.clone().lerp(t.muro, 0.12), base.clone().multiplyScalar(0.85), base.clone().lerp(t.techo, 0.14)];
    },
    partes(ctx) {
      const { THREE: T, tonos, lin, COL, ES } = ctx, blanco = new T.Color(1, 1, 1), noche = ES.modo === 1;
      const gris = (v) => new T.Color(v, v, v);
      // el pico claro (pálido, casi blanco) y su marca negra; el ojo oscuro
      const pico = tonos.muro.clone().lerp(lin(COL.costa), 0.35).lerp(blanco, noche ? 0.1 : 0.3);
      const negro = tonos.asfalto.clone().multiplyScalar(noche ? 0.5 : 0.25);
      const P = [
        // CUERPO: el ovoide que flota bajo (la mitad bajo el agua), el lomo más oscuro, el pecho un poco más claro
        { geo: ovo(T, [0, 0.04, 0], 0.21, 0.095, 0.105, 28), color: gris(1), tinte: true, grupo: "ave" },
        { geo: ovo(T, [-0.02, 0.09, 0], 0.17, 0.05, 0.085, 24), color: gris(0.78), tinte: true, grupo: "ave" },
        { geo: ovo(T, [0.11, 0.06, 0], 0.085, 0.07, 0.085, 20), color: gris(1.18), tinte: true, grupo: "ave" },
        // la cola: un copete corto y esponjado, alzado atrás
        { geo: ovo(T, [-0.2, 0.08, 0], 0.055, 0.045, 0.06, 16), color: gris(1.25), tinte: true, grupo: "ave" },
        // las alas pequeñas plegadas a los costados, con su borde
        ...[-1, 1].flatMap((z) => [
          { geo: ovo(T, [-0.04, 0.08, z * 0.085], 0.11, 0.035, 0.03, 18).rotateY(z * 0.08), color: gris(0.7), tinte: true, grupo: "ave" },
          { geo: ovo(T, [-0.09, 0.075, z * 0.09], 0.05, 0.022, 0.02, 12), color: gris(0.55), tinte: true, grupo: "ave" },
        ]),
        // CABEZA: el cuello corto y grueso, la cabeza redonda con la coronilla más oscura, el ojo y el pico
        { geo: vara(T, [NX - 0.01, NY - 0.01, 0], [HX - 0.01, HY - 0.025, 0], 0.046, 0.036, 16), color: gris(1.05), tinte: true, grupo: "cabeza" },
        { geo: ovo(T, [HX, HY, 0], RH, RH * 0.95, RH * 0.9, 20), color: gris(1), tinte: true, grupo: "cabeza" },
        { geo: ovo(T, [HX - 0.008, HY + 0.022, 0], RH * 0.85, RH * 0.5, RH * 0.75, 16), color: gris(0.72), tinte: true, grupo: "cabeza" },
        ...[-1, 1].map((z) => ({ geo: ovo(T, [HX + 0.024, HY + 0.01, z * 0.036], 0.011, 0.011, 0.008, 10), color: negro, grupo: "cabeza" })),
        // el pico: grueso, corto y romo (alto de base), con la marca negra que lo rodea a media longitud
        { geo: new T.ConeGeometry(0.024, 0.065, 14).scale(1, 1, 0.8).rotateZ(-Math.PI / 2).translate(HX + RH + 0.026, HY - 0.008, 0), color: pico, grupo: "cabeza" },
        { geo: new T.CylinderGeometry(0.0175, 0.0185, 0.008, 14).scale(1, 1, 0.82).rotateZ(-Math.PI / 2).translate(HX + RH + 0.03, HY - 0.008, 0), color: negro, grupo: "cabeza" },
      ];
      // ANILLOS: tres aros concéntricos de onda (al hundirse y al salir); ESTELA: la V de ondas tras la cola
      const costa = lin(COL.costa), LUZ = noche ? 0.25 : 0.3;
      const onda = (f) => tonos.agua.clone().lerp(costa, (noche ? 0.55 : 0.65) * (1 - 0.5 * f));
      for (let k = 0; k < 3; k++) P.push({ geo: new T.TorusGeometry(0.16 + 0.14 * k, 0.012 - 0.002 * k, 4, 32).rotateX(Math.PI / 2).translate(0, 0.012, 0), color: onda(k / 2), luz: LUZ, grupo: "anillo" });
      for (const lado of [-1, 1]) for (let k = 0; k < 4; k++) {
        const f = k / 3;
        P.push({ geo: new T.CylinderGeometry(1, 1, 0.01, 12).scale(0.1 - 0.02 * f, 1, 0.016 - 0.005 * f).rotateY(lado * 0.42).translate(-0.24 - k * 0.15, 0.01, lado * (0.06 + k * 0.07)), color: onda(f), luz: LUZ, grupo: "estela" });
      }
      return P;
    },
    // la pose en t (pura): el ciclo nada → se hunde → bajo el agua → sale; el cabeceo de cada patada y la mirada
    pose(t, i, ctx, est) {
      const E = est || {}, h = ctx.hash, vel = E.vel === undefined || E.vel === null ? null : Math.abs(E.vel);
      const nom0 = E.pose && typeof E.pose === "object" ? (E.pose.nombre || E.pose.pose) : E.pose;
      const nom = nom0 === "bucear" || nom0 === "flotar" ? nom0 : "nadar";
      const f0 = h(i, 71) * TAU, w = TAU * t / (2.6 + 0.6 * h(i, 72)) + f0;
      // la mirada lenta a los lados y el mecido
      const mira = 0.45 * Math.sin(TAU * t / (7 + 2 * h(i, 73)) + f0) * Math.max(0, Math.sin(TAU * t / (11 + 3 * h(i, 74)) + 2 * f0));
      const roll = 0.03 * Math.sin(w), heave = 0.01 * Math.sin(w * 1.3 + 0.7);
      if (nom === "flotar") {
        // descansa: el cuello recogido hacia atrás, apenas se mece
        return { ave: [roll * 0.6, 0, 0.03, 0, heave * 0.6, 0, 1], cabeza: [0, mira * 0.6, 0.32, -0.025, -0.045, 0], anillo: [0, 0, 0, 0, 0, 0, 0], estela: [0, 0, 0, 0, 0, 0, 0] };
      }
      const [s0, sr, abajo] = RITMO[nom];
      // el ciclo de esta instancia (la superficie varía 5–8 s por ciclo; fijo por instancia para que sea puro)
      const sup = s0 + sr * h(i, 75), C = sup + BAJA + abajo + SUBE, q = fr(t / C + h(i, 76)) * C;
      // la patada: el cuello avanza y vuelve (ciclo 0.9–1.1 s) mientras nada
      const pat = Math.sin(TAU * t / (0.9 + 0.2 * h(i, 77)) + f0);
      const mueve = vel === null ? 1 : ctx.suave(0.05, 0.5, vel);
      let ave = [roll, 0, 0, 0, heave, 0, 1], cab = [0, mira, 0.06 * pat * mueve, 0.012 * pat * mueve, 0, 0], ani = [0, 0, 0, 0, 0, 0, 0];
      let est2 = Math.max(0.001, (vel === null ? 0.7 : ctx.suave(0.05, 0.6, vel)) * (0.85 + 0.15 * Math.sin(w * 1.7)));
      if (q < sup) {
        // en la superficie; el último medio segundo se encoge y se adelanta (el salto antes de hundirse)
        const pre = s3((q - (sup - 0.45)) / 0.45);
        ave = [roll, 0, 0.12 * pre, 0, heave - 0.02 * pre, 0, 1];
        cab = [0, mira * (1 - pre), 0.06 * pat * mueve * (1 - pre) - 0.25 * pre, 0.012 * pat * mueve, 0, 0];
        // el anillo de la salida anterior aún se abre los primeros 1.6 s
        if (q < 1.6) ani = [0, 0, 0, 0, 0, 0, 0.6 + 1.6 * s3(q / 1.6), 1 - q / 1.6];
      } else if (q < sup + BAJA) {
        // se hunde de cabeza: un brinco corto hacia adelante, el pico al agua, la cola al final
        const d = (q - sup) / BAJA, hop = 0.05 * Math.sin(Math.PI * Math.min(1, d / 0.35));
        const k = 1 - s3((d - 0.55) / 0.45);
        ave = [0, 0, -1.1 * s3(d), 0.12 * s3(d), hop - 0.32 * s3((d - 0.15) / 0.85), 0, Math.max(0.001, k)];
        cab = [0, 0, -0.35 * s3(d / 0.4), 0, 0, 0];
        ani = [0, 0, 0, 0.1, 0, 0, 0.3 + 0.9 * s3(d), 1];
        est2 = 0.001;
      } else if (q < sup + BAJA + abajo) {
        // bajo el agua: no se ve; el anillo de la zambullida termina de abrirse y se apaga
        const u = q - sup - BAJA;
        ave = [0, 0, 0, 0, -0.4, 0, 0];
        ani = u < 1.6 ? [0, 0, 0, 0.1, 0, 0, 1.2 + 1.2 * s3(u / 1.6), 1 - u / 1.6] : [0, 0, 0, 0, 0, 0, 0];
        est2 = 0.001;
      } else {
        // sale: emerge de abajo con el pico arriba y se asienta con una sacudida
        const d = (q - sup - BAJA - abajo) / SUBE, k = s3(d / 0.5);
        ave = [0.06 * Math.sin(TAU * 2 * d) * (1 - d), 0, 0.35 * (1 - s3(d)), 0, -0.22 * (1 - s3(d)) + 0.02 * Math.sin(Math.PI * d), 0, Math.max(0.001, k)];
        cab = [0, 0.2 * Math.sin(TAU * 1.5 * d) * (1 - d), 0.15 * (1 - d), 0, 0, 0];
        ani = [0, 0, 0, 0, 0, 0, 0.3 + 0.4 * d, 1];
        est2 = 0.001;
      }
      return { ave, cabeza: cab, anillo: ani, estela: [0, 0, 0, 0, 0, 0, est2] };
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
