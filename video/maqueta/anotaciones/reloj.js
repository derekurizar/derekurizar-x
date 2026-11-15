// Anotación «reloj» (ficha: reloj.json): una hora que corre de `de` a `a` entre `corre` [t0, t1] (antes, quieta en `de`;
// después, en `a`), en una tarjeta con su rótulo: arriba a la derecha bajo el titular, abajo a la derecha sobre la banda,
// o encima de un ancla (`en`). Los segundos saltan como en un reloj; con `decimas`, también las décimas. Capa 2D (capa.js →
// A); seek puro.
(function (MAQ) {
  MAQ.ANOTACIONES = MAQ.ANOTACIONES || {};
  const dos = (n) => (n < 10 ? "0" : "") + n;
  function texto(o, v) {
    const d = o.decimas ? Math.floor(v * 10 + 1e-6) / 10 : Math.floor(v + 1e-6);
    const h = Math.floor(d / 3600), m = Math.floor((d % 3600) / 60), s = Math.floor(d % 60), dec = Math.round((d - Math.floor(d)) * 10) % 10;
    return h + ":" + dos(m) + (o.segundos || o.decimas ? ":" + dos(s) : "") + (o.decimas ? "." + dec : "");
  }
  MAQ.ANOTACIONES.reloj = {
    armar(A, lista) {
      return lista.map((o) => {
        const el = A.div("anot-reloj");
        if (o.rotulo) { const sm = document.createElement("small"); sm.textContent = o.rotulo; el.appendChild(sm); }
        const hora = document.createElement("span"); el.appendChild(hora);
        return { o, el, hora, w: null };
      });
    },
    en(t, st, A) {
      const Z = A.Z;
      for (const s of st) {
        const o = s.o, viva = t >= o.t && t < o.hasta, [e, f] = A.vida(t, o.t, o.hasta, 0.3, 0.25);
        if (!viva) { s.el.style.opacity = "0"; continue; }
        const u = A.clamp((t - o.corre[0]) / (o.corre[1] - o.corre[0]));
        s.hora.textContent = texto(o, o.de_s + (o.a_s - o.de_s) * u);
        if (s.w === null) s.w = [s.el.offsetWidth, s.el.offsetHeight];
        let x, y;
        if (o.en) {
          const q = A.ancla(o.en, t);
          if (!q.vis || q.px === null) { s.el.style.opacity = "0"; continue; }
          x = Math.max(Z.izq, Math.min(Z.der - s.w[0], q.px - s.w[0] / 2)); y = q.py - 40 - s.w[1];
        } else if (o.pos === "abajo") { x = Z.der - s.w[0]; y = Z.fin_marcas - s.w[1] - 10; }
        else { x = Z.der - s.w[0]; y = Z.tit_y + Z.tit_px * 2 + 70; }
        s.el.style.opacity = (e * f).toFixed(3);
        s.el.style.transform = "translate(" + x.toFixed(1) + "px," + (y + (1 - e) * 16).toFixed(1) + "px)";
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, ANOTACIONES: {}, MUNDOS: {} });
