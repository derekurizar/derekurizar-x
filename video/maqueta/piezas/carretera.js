// Pieza «carretera» (ficha: carretera.json): una vía de N carriles sobre su eje (el de la receta de un esquema o una
// arteria de un set de ciudad; la resuelve scripts/maqueta_tipos/carretera.py): la banda de asfalto con sus acotamientos,
// la línea central doble (o la mediana), las orillas y las rayas entre carriles, en líneas de ancho en píxeles que se ven a
// cualquier distancia. Sus caminos («<id>», «<id>.carril-k») ya vienen en ctx.caminos. «resaltar» la pieza aviva sus
// líneas; con `elemento`, la vía entera se enciende en el acento.
(function (MAQ) {
  function correr(pts, d) {            // la polilínea corrida d unidades a su izquierda (como desplazar() en esquema.py)
    return pts.map((p, i) => { const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      return [p[0] - (b[1] - a[1]) / L * d, p[1] + (b[0] - a[0]) / L * d]; });
  }
  MAQ.PIEZAS.carretera = {
    orden: 7,
    armar(ctx, piezas) {
      const { malla, tonos, COL, CFG, ES } = ctx;
      const raya = ES.modo === 4 ? COL.linea : COL.costa, central = ES.modo === 4 ? COL.linea : COL.luces;
      return piezas.map((p) => {
        const n2 = p.carriles / 2, w = p.ancho_carril, med = p.mediana, ancho = p.carriles * w + med + 2.4;
        const acc = malla.nueva();
        malla.banda(acc, p.eje, ancho, 0.6, 15, tonos.asfalto);
        if (med > 1.2) malla.banda(acc, p.eje, med - 0.6, 0.75, 15, tonos.verde.clone().lerp(tonos.asfalto, 0.4));
        const mat = malla.material({ desfase: 2 });
        malla.poner(acc, mat, 2);
        const A = CFG.ruta.ancho, L = [];
        const linea = (pts, color, ancho_px, alfa, extra) => { const c = ctx.cinta(ctx.pegar(pts, 8, 1.1), color, ancho_px, alfa, 6, extra); L.push(c); return c; };
        // la central: doble si no hay mediana; si la hay, sus dos orillas
        for (const s of [1, -1]) linea(correr(p.eje, s * Math.max(0.25, med / 2)), central, A * 0.75, 0.95);
        for (const s of [1, -1]) {
          linea(correr(p.eje, s * (med / 2 + n2 * w)), raya, A * 0.7, 0.85);                         // las orillas
          for (let k = 1; k < n2; k++) linea(correr(p.eje, s * (med / 2 + k * w)), raya, A * 0.55, 0.7, { raya: 12 });   // entre carriles
        }
        ctx.linea(p.id, L[0]);
        let enc = null;
        if (ctx.M.eventos.some((e) => e.pieza === p.id && e.indice !== undefined)) {
          const a = malla.nueva(); malla.banda(a, p.eje, ancho + 2, 1.3, 15, tonos.acento);
          enc = malla.material({ alfa: 0, desfase: 3 }); malla.poner(a, enc, 5);
        }
        return { id: p.id, mat, enc };
      });
    },
    en(t, lista, ctx) {
      for (const s of lista) {
        const b = ctx.cuadro.brillo[s.id];
        s.mat.uniforms.uBrillo.value = b ? 1 + 0.3 * (b - 1) : 1;
        if (s.enc) s.enc.uniforms.uAlfa.value = Math.min(0.85, ((ctx.cuadro.elementos[s.id] || [])[0] || { k: 0 }).k * 0.85);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
