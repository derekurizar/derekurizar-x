// Evento «correranios» (ficha: correranios.json; reglas: scripts/maqueta_tipos/correranios.py): sobre una pieza
// coberturaceldas, el año corre de `de` a `a` durante `dur`: cada año que llega apaga, con su destello, las celdas que
// perdieron cobertura ese año (lo dibuja la pieza: este evento le dice qué año es en cada segundo). Un contador de año
// grande, en la capa 2D (arriba o abajo a la derecha), dice el año; con `queda`, se queda en el último al terminar.
// Se llama varias veces sobre la misma pieza y sigue donde quedó (2001→2002, 2003→2007…): en cada segundo manda el
// último evento que ya empezó; antes del primero, la pieza queda como la dejó su ficha (`anio`).
// Cómo: la pieza coberturaceldas lee en cada cuadro su `anio`, `anio_fin`, `corre_desde` y `corre_hasta`; `inicio`
// devuelve a la pieza sus valores de la ficha y `aplicar` pone los del evento que manda en t (el año «de» llega justo en
// e.t; los demás, en escalones iguales hasta e.t + dur). Seek puro: todo sale de t y del maqueta.json, nada se acumula.
// El contador es un elemento de la capa (no hay texto en el 3D); el año visible es una cifra: `cifra_por_anio` dice con
// qué prefijo se respalda cada año mostrado (C3D5).
(function (MAQ) {
  const CAMPOS = ["anio", "anio_fin", "corre_desde", "corre_hasta"];

  // los parámetros que le toca a la pieza por el evento e (año «de» llega en e.t; «a», en e.t + dur)
  function tramo(e) {
    const n = e.a - e.de, paso = n > 0 ? Math.max(0.05, e.dur) / n : Math.min(1, Math.max(0.3, e.dur));
    return { anio: e.de - 1, anio_fin: e.a, corre_desde: e.t - paso, corre_hasta: e.t + (n > 0 ? Math.max(0.05, e.dur) : 0) };
  }
  // el año (entero) que se ve en t según el evento e (t ≥ e.t)
  function anioDe(e, t) {
    const n = e.a - e.de; if (n <= 0) return e.a;
    const u = Math.min(1, Math.max(0, (t - e.t) / Math.max(0.05, e.dur)));
    return e.de + Math.floor(n * u + 1e-6);
  }

  MAQ.EVENTOS.correranios = {
    orden: 6,   // antes de la pieza (7): su `inicio` corre primero; el `en` de la pieza ya ve el año del evento
    armar(ctx, lista) {
      const piezas = {};
      for (const p of ctx.M.piezas || []) if (p.tipo === "coberturaceldas") piezas[p.id] = p;
      const orig = {};
      for (const id in piezas) { orig[id] = {}; for (const k of CAMPOS) orig[id][k] = piezas[id][k]; }
      // el contador: uno por pieza (los eventos de una pieza comparten el suyo); en la capa 2D, con la tarjeta del reloj
      const capa = document.querySelector("#root .capa") || document.querySelector(".capa") || document.body;
      const Z = ctx.M.zona || {};
      const cont = {};
      for (const e of lista) {
        if (e.contador === false || cont[e.pieza]) continue;
        const el = document.createElement("div");
        el.className = "anot-reloj correranios";
        el.style.cssText = "position:absolute;left:0;top:0;opacity:0;z-index:4;pointer-events:none;text-align:right;" +
          "font-size:" + Math.round((Z.cifra_px || 150) * 0.62) + "px;letter-spacing:.01em;padding:14px 22px 12px;";
        const sm = document.createElement("small"); sm.style.textAlign = "right"; el.appendChild(sm);
        const num = document.createElement("span"); el.appendChild(num);
        capa.appendChild(el);
        cont[e.pieza] = { el, sm, num, w: null, rot: "" };
      }
      return { lista, piezas, orig, cont, manda: {} };
    },
    inicio(t, st) {
      if (!st) return;
      for (const id in st.piezas) { const p = st.piezas[id], o = st.orig[id]; for (const k of CAMPOS) p[k] = o[k]; }
      st.manda = {};
    },
    aplicar(t, e, ctx, st) {
      if (!st || t < e.t - 1e-6) return;
      const p = st.piezas[e.pieza]; if (!p) return;
      const m = st.manda[e.pieza];
      if (m && m.t > e.t) return;                          // manda el último evento que ya empezó
      st.manda[e.pieza] = e;
      Object.assign(p, tramo(e));
    },
    en(t, st, ctx) {
      if (!st) return;
      const Z = ctx.M.zona || {}, { clamp } = ctx;
      for (const id in st.cont) {
        const c = st.cont[id], e = st.manda[id];
        // el contador lo lleva el último evento de esta pieza que ya empezó y quiere contador
        let ev = e && e.contador !== false ? e : null;
        if (!ev) for (const x of st.lista) if (x.pieza === id && x.contador !== false && t >= x.t - 1e-6 && (!ev || x.t > ev.t)) ev = x;
        if (!ev) { c.el.style.opacity = "0"; continue; }
        const fin = ev.queda !== false ? 1 : 1 - clamp((t - (ev.t + ev.dur)) / 0.3);
        // entra con el primer evento con contador de la pieza (en el cuadro cero, ya entero)
        let t0 = ev.t; for (const x of st.lista) if (x.pieza === id && x.contador !== false && x.t < t0) t0 = x.t;
        const ent = t0 <= 0.1 ? 1 : 1 - Math.pow(1 - clamp((t - t0) / 0.35), 3);
        const op = ent * fin;
        if (op <= 0.002) { c.el.style.opacity = "0"; continue; }
        const Y = anioDe(ev, t), rot = ev.rotulo || "";
        if (c.rot !== rot) { c.sm.textContent = rot; c.sm.style.display = rot ? "block" : "none"; c.rot = rot; c.w = null; }
        c.num.textContent = String(Y);
        if (c.w === null) c.w = [c.el.offsetWidth, c.el.offsetHeight];
        // el año que acaba de llegar late un instante (el mismo destello que las celdas)
        const n = ev.a - ev.de, tl = n > 0 ? ev.t + (Y - ev.de) / n * ev.dur : ev.t, late = Math.exp(-Math.max(0, t - tl) / 0.22) * (t >= tl ? 1 : 0);
        const der = Z.der || 876, y = ev.pos === "abajo" ? (Z.fin_marcas || 1282) - c.w[1] - 10 : (Z.tit_y || 256) + (Z.tit_px || 84) * 2 + 70;
        c.el.style.opacity = op.toFixed(3);
        c.el.style.transform = "translate(" + (der - c.w[0]).toFixed(1) + "px," + (y + (1 - ent) * 16).toFixed(1) + "px) scale(" + (1 + 0.06 * late).toFixed(4) + ")";
        c.el.style.transformOrigin = "100% 50%";
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
