// Pieza «rios» (ficha: rios.json): los ríos principales del set (OpenStreetMap), cintas pegadas al relieve en el color del
// agua del estilo, más finas que la frontera y por orden (1 = los grandes, más anchos). La pieza protagonista va en el
// acento; «resaltar» la sube por su id (ctx.linea la cinta principal; las demás siguen el mismo brillo en `en`).
(function (MAQ) {
  // La altura de lo que se VE. mundos/pais.js arma la malla del relieve con una celda de cada dos (y, en voxel, columnas de
  // 6 × 6 celdas): un cauce angosto cae entre dos vértices y con ctx.altura quedaría debajo de la malla. Aquí se calcula
  // esa misma superficie con ctx.altura en los centros de celda (allí es exacta).
  function suelo(ctx) {
    const R = ctx.M.relieve, P = R.proyeccion, C = R.caja, { clamp, EXAG } = ctx;
    const X0 = (C.lon_min - P.lon0) * P.km_lon, X1 = (C.lon_max - P.lon0) * P.km_lon, Y0 = (C.lat_min - P.lat0) * P.km_lat, Y1 = (C.lat_max - P.lat0) * P.km_lat;
    const CX = (X1 - X0) / R.ancho, CY = (Y1 - Y0) / R.alto;
    const celda = (ci, cj) => ctx.altura(X0 + (ci + 0.5) * CX, Y1 - (cj + 0.5) * CY);
    if (ctx.ES.cubos) {   // voxel: el tope de la columna (la media del bloque en escalones de 300 m)
      const B = 6, paso = 0.3 * EXAG, memo = new Map(), nbx = Math.floor(R.ancho / B), nby = Math.floor(R.alto / B);
      return (x, y) => {
        const bi = clamp(Math.floor((x - X0) / CX / B), 0, nbx - 1), bj = clamp(Math.floor((Y1 - y) / CY / B), 0, nby - 1), k = bj * nbx + bi;
        if (!memo.has(k)) { let s = 0, n = 0;
          for (let b = 0; b < B; b++) for (let a = 0; a < B; a++) { const h = celda(bi * B + a, bj * B + b); s += h; if (h > 0) n++; }
          memo.set(k, n > B * B / 2 ? Math.max(1, Math.round(s / (B * B) / paso)) * paso : paso * 0.35); }
        return memo.get(k);
      };
    }
    const PASO = 2, nx = Math.floor((R.ancho - 1) / PASO) + 1, ny = Math.floor((R.alto - 1) / PASO) + 1;
    return (x, y) => {   // el triángulo de la malla que pisa (x, y): a–b arriba, c–d abajo, diagonal b–c
      const fi = clamp(((x - X0) / CX - 0.5) / PASO, 0, nx - 1.0001), fj = clamp(((Y1 - y) / CY - 0.5) / PASO, 0, ny - 1.0001);
      const i = Math.floor(fi), j = Math.floor(fj), u = fi - i, v = fj - j;
      const a = celda(i * PASO, j * PASO), b = celda((i + 1) * PASO, j * PASO), c = celda(i * PASO, (j + 1) * PASO), d = celda((i + 1) * PASO, (j + 1) * PASO);
      return u + v <= 1 ? a + (b - a) * u + (c - a) * v : d + (c - d) * (1 - u) + (b - d) * (1 - v);
    };
  }
  // líneas [[clase, x0, y0, x1, y1, …], …] de una clase → UNA cadena con saltos, densificada (ctx.pegar) y posada en lo que se ve
  function cadena(ctx, S, lineas, clase, paso, lev) {
    const cad = []; let s = 0;
    for (const ln of lineas) { if (ln[0] !== clase) continue;
      for (let i = 1; i + 1 < ln.length; i += 2) { if (i > 1) s += Math.hypot(ln[i] - ln[i - 2], ln[i + 1] - ln[i - 1]); cad.push([ln[i], ln[i + 1], s, i + 3 < ln.length ? 0 : 1]); }
      s += 1; }
    if (cad.length < 2) return null;
    const pts = ctx.pegar(cad, paso, lev);
    for (const q of pts) q.v.y = S(q.v.x, -q.v.z) + lev;
    return pts;
  }
  MAQ.PIEZAS.rios = {
    orden: 7,
    armar(ctx, piezas) {
      const { CFG, COL, ES, lin, cinta } = ctx, S = suelo(ctx);
      // noche y plano: el agua es tan oscura como el suelo → un hilo claro, el de la costa; en los demás, el azul del mar
      const claro = ES.modo === 1 || ES.modo === 4;
      const agua = claro ? lin(COL.costa) : lin(COL.mar).lerp(lin(COL.mar_hondo), 0.85);
      const ANCHO = [0, 0.9, 0.65, 0.48], ALFA = claro ? [0, 0.6, 0.45, 0.32] : [0, 0.95, 0.85, 0.72];
      const lev = ES.cubos ? 0.3 : 0.2;
      return piezas.map((p) => {
        const cintas = [];
        for (const o of [3, 2, 1]) {
          const pts = cadena(ctx, S, p.lineas, o, 1.2, lev);
          if (pts) cintas.push(cinta(pts, p.protagonista ? COL.acento : agua, CFG.frontera.ancho * ANCHO[o] * p.grosor * (p.protagonista ? 1.4 : 1), p.protagonista ? 1 : ALFA[o], 1));
        }
        ctx.linea(p.id, cintas.pop());          // la de los ríos más grandes que haya: la que «resaltar» sube
        return { id: p.id, cintas };
      });
    },
    en(t, lista, ctx) {
      for (const e of lista) { const b = ctx.cuadro.brillo[e.id];
        for (const c of e.cintas) c.mat.uniforms.uAlfa.value = Math.min(1, c.alfa * (b || 1) * (b ? 1.3 : 1)); }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
