// Pieza «actor» (ficha: actor.json): UN objeto del catálogo (video/maqueta/objetos/) que sigue un camino con nombre,
// orientado en la dirección de marcha. Su trayectoria (T, S) ya viene calculada por scripts/maqueta_tipos/actor.py (claves y
// eventos `mover`); aquí solo se evalúa en t, suavizada (ctx.tray: seek puro). Se registra como móvil (ctx.moviles[id]):
// la cámara lo sigue con `mira: {actor: id}` y las anotaciones se pegan a él. El protagonista va en el acento; los demás, en
// una de las variantes del objeto. Los pilotos se avivan al frenar. «aparecer» / «desaparecer» lo hacen crecer o encogerse
// (ctx.cuadro.vis[id]).
(function (MAQ) {
  MAQ.PIEZAS.actor = {
    orden: 20,
    armar(ctx, piezas) {
      return piezas.map((p) => {
        const r = ctx.tray.nueva(p.T, p.S);
        const fl = ctx.flota(p.objeto, 1, { tamano: p.tamano, lev: p.lev, orden: 4,
          color: (i, vs) => (p.protagonista ? ctx.tonos.acento : vs[p.variante % vs.length]) });
        const movil = (t) => { const [s, v] = ctx.tray.suave(r, p.h, t), q = ctx.enCamino(p.camino, s);
          return { x: q.x, y: q.y, dx: q.dx, dy: q.dy, v, vis: true }; };
        ctx.moviles[p.id] = movil;
        return { p, r, fl, movil };
      });
    },
    en(t, lista, ctx) {
      const a3 = ctx.metros(3);
      for (const a of lista) {
        const q = a.movil(t), V = (ctx.cuadro.vis || {})[a.p.id], k = V === undefined ? 1 : V;
        const v0 = ctx.tray.suave(a.r, a.p.h, t - 0.15)[1], v1 = ctx.tray.suave(a.r, a.p.h, t + 0.15)[1];
        a.fl.poner(0, q.x, q.y, q.dx, q.dy, k, ctx.clamp((v0 - v1) / 0.3 / a3));
        a.fl.listo();
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
