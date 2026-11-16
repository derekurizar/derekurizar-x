// Anotación «etiqueta» (ficha: etiqueta.json): un rótulo corto en una píldora que SIGUE a su ancla (un actor, un vehículo
// de un flujo, un lugar), encima de él y unido por un trazo: «102 km/h», «Tu carro». No se sale de la columna de texto. Capa
// 2D (capa.js → A); seek puro.
(function (MAQ) {
  MAQ.ANOTACIONES = MAQ.ANOTACIONES || {};
  MAQ.ANOTACIONES.etiqueta = {
    armar(A, lista) {
      return lista.map((o) => {
        const el = A.div("anot-etq", o.texto);
        if (o.sub) { const sm = document.createElement("small"); sm.textContent = o.sub; el.appendChild(sm); }
        return { o, el, tallo: A.svg("path", "anot-linea"), w: null };
      });
    },
    en(t, st, A) {
      const Z = A.Z, ALTO = 46;
      for (const s of st) {
        const o = s.o, viva = t >= o.t && t < o.hasta, [e, f] = A.vida(t, o.t, o.hasta, 0.3, 0.25);
        const q = viva ? A.ancla(o.sigue, t) : null, ok = !!(q && q.vis && q.px !== null);
        if (!ok) { s.el.style.opacity = "0"; s.tallo.setAttribute("d", ""); continue; }
        if (s.w === null) s.w = [s.el.offsetWidth, s.el.offsetHeight];
        const [w, h] = s.w, top = q.py - ALTO - h;
        const x = Math.max(Z.izq - 20, Math.min(Z.W - Z.corte - w, q.px - w / 2));
        const op = e * f * A.clamp((top - Z.sup) / 40 + 1);
        s.el.style.opacity = op.toFixed(3);
        s.el.style.transform = "translate(" + x.toFixed(1) + "px," + (top + (1 - e) * 14).toFixed(1) + "px)";
        s.tallo.setAttribute("d", A.d([[q.px, q.py - 6], [q.px, q.py - ALTO]]));
        s.tallo.style.opacity = op.toFixed(3);
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, ANOTACIONES: {}, MUNDOS: {} });
