// Pieza «afluente» (ficha: afluente.json; reglas: scripts/maqueta_tipos/afluente.py): un río que el set no trae, desde
// una traza dada de la FUENTE a la BOCA (s crece río abajo), pegado a la superficie que se ve. Más grueso que los ríos del
// país y más ancho hacia la boca, con una orilla oscura, un halo y RAYAS DE CORRIENTE (galones que bajan hacia la boca).
// Con un «resaltar» de su id: no se ve antes del primero, se DIBUJA de la fuente a la boca (con una punta que brilla) y
// queda en el acento; sin resaltar, se ve entero en el agua del estilo (o en el acento si es la protagonista).
// Seek puro: lo dibujado, la fase de las rayas y el brillo salen de t y de los eventos del maqueta.json.
(function (MAQ) {
  const VEL = 0.55;          // periodos de raya por segundo (ilustrativo: no es la velocidad del agua)
  const FRAG = `uniform vec3 cAgua, cRaya, cOrilla; uniform float uAlfa, uDib, uL, uFase, uPer, uRayas, uHalo, uCabeza, uBorde, uNoche;
    varying float vLado, vS;
    void main(){
      if (vS > uDib || uAlfa <= 0.0) discard;
      float u = clamp(vS / max(uL, 1e-3), 0.0, 1.0);
      float w = 0.5 + 0.5 * smoothstep(0.0, 1.0, u);             // nace angosto y se ensancha hacia la boca
      float q = abs(vLado) / w; if (q > 1.0) discard;
      vec3 c = cAgua; float a;
      float cab = uCabeza * exp(-pow((uDib - vS) / uBorde, 2.0)); // la punta que avanza mientras se dibuja
      if (uHalo > 0.5) {
        a = pow(1.0 - q, 2.2) * uAlfa * (1.0 + 1.5 * cab);
      } else {
        a = smoothstep(0.0, 0.3, 1.0 - q) * uAlfa;
        c = mix(c, cOrilla, smoothstep(0.62, 0.92, q) * (0.55 - 0.3 * uNoche));
        if (uRayas > 0.5) {                                       // galones que apuntan río abajo
          float m = fract(vS / uPer - uFase + q * 0.42);
          float r = smoothstep(0.0, 0.08, m) * (1.0 - smoothstep(0.18, 0.28, m)) * (1.0 - smoothstep(0.5, 0.7, q));
          r *= smoothstep(0.0, 0.6 * uPer, vS) * (1.0 - smoothstep(uDib - 0.8 * uPer, uDib, vS));
          c = mix(c, cRaya, r * 0.6);
        }
        c = mix(c, cRaya, clamp(cab, 0.0, 1.0) * 0.85);
      }
      if (a < 0.003) discard;
      c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));
      gl_FragColor = vec4(c, a);
    }`;
  MAQ.PIEZAS.afluente = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, CFG, COL, ES, lin, clamp, scene } = ctx;
      const S = ctx.superficieVista(ctx.altura);
      const claro = ES.modo === 1 || ES.modo === 4;            // noche y plano: el agua es tan oscura como el suelo
      const agua = claro ? lin(COL.costa) : lin(COL.mar).lerp(lin(COL.mar_hondo), 0.6);
      const acento = lin(COL.acento), luz = lin(COL.luz), orilla = lin(COL.linea);
      const noche = ES.noche ? 1 : 0, lev = ES.cubos ? 0.3 : 0.2;
      const anchoF = (CFG.frontera && CFG.frontera.ancho) || 1.6;
      return piezas.map((p, i) => {
        const L = p.largo_km, paso = clamp(L / 160, 0.08, 0.6);
        const pts = ctx.pegar(p.cadena, paso, lev);
        for (const q of pts) q.v.y = S(q.v.x, -q.v.z) + lev;
        const geo = ctx.geoCinta(pts);
        const per = clamp(L / 8, 1, 5) * (0.92 + 0.16 * ctx.hash(i, 3));
        const resaltes = ctx.M.eventos.filter((e) => e.tipo === "resaltar" && e.pieza === p.id && e.indice === undefined)
          .sort((a, b) => a.t - b.t);
        const capas = [];
        for (const halo of [true, false]) {
          const base = anchoF * p.grosor * (halo ? 3.6 : 1.6);
          const mat = new THREE.ShaderMaterial({
            uniforms: { ...ctx.uComun(), uAncho: { value: base }, cAgua: { value: agua.clone() }, cRaya: { value: luz.clone() },
              cOrilla: { value: orilla.clone() }, uAlfa: { value: 1 }, uDib: { value: 1e9 }, uL: { value: L }, uFase: { value: 0 },
              uPer: { value: per }, uRayas: { value: p.corriente && !halo ? 1 : 0 }, uHalo: { value: halo ? 1 : 0 },
              uCabeza: { value: 0 }, uBorde: { value: Math.max(0.35, L * 0.035) }, uNoche: { value: noche } },
            vertexShader: ctx.VERT_CINTA, fragmentShader: FRAG, transparent: true, depthWrite: false,
            blending: halo && ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending });
          const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = halo ? 8 : 9; scene.add(m);
          ctx.registrarCinta(mat, base, 1);
          capas.push({ mat, halo });
        }
        return { p, L, capas, resaltes, agua, acento, luz, prota: !!p.protagonista };
      });
    },
    en(t, lista, ctx) {
      const { suave, clamp, ES } = ctx;
      for (const o of lista) {
        const e0 = o.resaltes[0], b = ctx.cuadro.brillo[o.p.id] || 1;
        let dib = 1e9, cab = 0, enAcento = o.prota;
        if (e0) {
          const D = clamp(e0.dur * 0.7, 0.8, 2.6), r = suave(e0.t, e0.t + D, t);
          dib = t < e0.t ? -1 : (r >= 1 ? 1e9 : o.L * r);
          cab = t >= e0.t && r < 1 ? 1 - 0.6 * r * r * r * r : 0;
          enAcento = enAcento || t >= e0.t;
        }
        const fase = t * VEL;
        for (const { mat, halo } of o.capas) {
          const U = mat.uniforms;
          U.uDib.value = dib; U.uCabeza.value = cab; U.uFase.value = fase;
          U.cAgua.value.copy(enAcento ? o.acento : o.agua);
          U.cRaya.value.copy(o.luz);
          U.uAlfa.value = halo
            ? clamp((enAcento ? (ES.aditivo ? 0.4 : 0.22) : (ES.aditivo ? 0.2 : 0.1)) * (1 + 1.6 * (b - 1)), 0, 0.85)
            : clamp((enAcento ? 1 : 0.92) * (b > 1 ? 1 + 0.3 * (b - 1) : 1), 0, 1);
        }
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
