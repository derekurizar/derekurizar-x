// Pieza «calles» (ficha: calles.json): la red de calles por clase, en metros (de un set de ciudad o de la receta de un
// esquema; las resuelve scripts/maqueta_tipos/calles.py): bandas de su ancho real posadas sobre el suelo, las mayores más
// claras. «resaltar» la sube entera (por su id) o, con `elemento`, enciende UNA calle en el acento (ctx.cuadro.elementos).
(function (MAQ) {
  const MAYORES = { autopista: 1, primaria: 0.75, secundaria: 0.45, terciaria: 0.25 };
  MAQ.PIEZAS.calles = {
    orden: 6,
    armar(ctx, piezas) {
      const { malla, tonos } = ctx;
      return piezas.map((p) => {
        const acc = malla.nueva(), tono = p.clases.map((cl) => tonos.calle.clone().lerp(tonos.calle_mayor, MAYORES[cl] || 0));
        const pares = (q) => { const o = []; for (let i = 1; i + 1 < q.length; i += 2) o.push([q[i], q[i + 1]]); return o; };
        for (const q of p.calles) malla.banda(acc, pares(q), p.anchos[q[0]], 0.3 + 0.02 * (p.clases.length - q[0]), 24, tono[q[0]]);
        const mat = malla.material({ desfase: 1 }), mesh = malla.poner(acc, mat, 1);
        // las calles que un «resaltar» con `elemento` enciende: una banda propia en el acento, apagada hasta su evento
        const extra = {};
        for (const e of ctx.M.eventos) if (e.pieza === p.id && e.indice !== undefined && !extra[e.indice]) {
          const a = malla.nueva(), q = p.calles[e.indice];
          malla.banda(a, pares(q), p.anchos[q[0]] * 1.7, 0.9, 12, tonos.acento);
          const m = malla.material({ alfa: 0, desfase: 2 }); extra[e.indice] = { mat: m, mesh: malla.poner(a, m, 3) };
        }
        return { id: p.id, mat, extra };
      });
    },
    en(t, lista, ctx) {
      for (const s of lista) {
        s.mat.uniforms.uBrillo.value = ctx.cuadro.brillo[s.id] ? 1 + 0.35 * (ctx.cuadro.brillo[s.id] - 1) : 1;
        for (const i in s.extra) s.extra[i].mat.uniforms.uAlfa.value = 0;
        for (const el of ctx.cuadro.elementos[s.id] || []) if (s.extra[el.i]) s.extra[el.i].mat.uniforms.uAlfa.value = Math.min(1, el.k);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
