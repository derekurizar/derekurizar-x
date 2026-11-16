// Pieza «flujo» (ficha: flujo.json): el tráfico. Cada vehículo trae resuelto su carril, su tipo (un objeto del catálogo),
// su variante de color y su trayectoria (T, S), que calcula scripts/maqueta_tipos/_movimiento.py con el modelo de Newell
// (la cola que forma un `frenar` crece hacia atrás sola y nadie atraviesa al de adelante). Aquí solo se evalúa en t,
// suavizada (ctx.tray: seek puro), y se dibuja con una flota por tipo (una malla instanciada). Un vehículo se ve mientras
// está sobre su carril (0 ≤ s ≤ largo). Los pilotos se avivan al frenar y en la cola. Es un móvil (ctx.moviles[id](t, n)):
// la cámara puede seguir a uno (`mira: {flujo: id, n}`) y las anotaciones pegarse a ellos.
(function (MAQ) {
  MAQ.PIEZAS.flujo = {
    orden: 21,
    armar(ctx, piezas) {
      return piezas.map((p) => {
        const V = p.vehiculos.map(([c, o, va, T, S]) => ({ c, o, va, r: ctx.tray.nueva(T, S), slot: 0 }));
        const flotas = p.tipos.map((tipo, o) => {
          const suyos = V.filter((v) => v.o === o);
          suyos.forEach((v, j) => { v.slot = j; });
          return ctx.flota(tipo, suyos.length, { tamano: p.tamano, luces: p.luces, color: (j, vs) => vs[suyos[j] ? suyos[j].va % vs.length : 0] });
        });
        const movil = (t, n) => { const v = V[n], [s, vel] = ctx.tray.suave(v.r, p.h, t), q = ctx.enCamino(p.carriles[v.c], s);
          return { x: q.x, y: q.y, dx: q.dx, dy: q.dy, v: vel, vis: s >= -1e-6 && s <= p.largos[v.c] + 1e-6 }; };
        ctx.moviles[p.id] = movil;
        return { p, V, flotas, movil };
      });
    },
    en(t, lista, ctx) {
      const a3 = ctx.metros(3), lento = ctx.metros(1.2);
      for (const f of lista) {
        const vis = (ctx.cuadro.vis || {})[f.p.id], k = vis === undefined ? 1 : vis;
        f.V.forEach((v, n) => {
          const q = f.movil(t, n);
          if (!q.vis || k <= 0) { f.flotas[v.o].poner(v.slot, q.x, q.y, q.dx, q.dy, 0, 0); return; }
          const v0 = ctx.tray.suave(v.r, f.p.h, t - 0.15)[1], v1 = ctx.tray.suave(v.r, f.p.h, t + 0.15)[1];
          const freno = Math.max(ctx.clamp((v0 - v1) / 0.3 / a3), q.v < lento ? 0.75 : 0);
          f.flotas[v.o].poner(v.slot, q.x, q.y, q.dx, q.dy, k, freno);
        });
        for (const fl of f.flotas) fl.listo();
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
