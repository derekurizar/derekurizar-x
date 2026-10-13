// mapa · los 22 departamentos (GEOMETRIA la inyecta scripts/informe.py desde design/mapa_geometria.svg).
//   marcados [GTxx…] en el acento, el resto en tinta suave; marcadores [{id, n, dx, dy}] numerados en
//   el centroide del departamento (dx/dy corrigen en px si dos quedan juntos).
G.mapa = (el, S, { ancho, col }) => {
  H.assert(typeof GEOMETRIA === "object", "mapa: falta GEOMETRIA (informe.py la inyecta)");
  const [vx, vy, vw, vh] = GEOMETRIA.viewBox.split(/\s+/).map(Number);
  const W = Math.min(ancho, S.ancho || ancho), Hh = Math.round((W * vh) / vw), k = W / vw;  // S.ancho acota el mapa (un mapa a 672 px mide 705 de alto)
  const svg = GX.lienzo(el, W, Hh, S.aria);
  const g = H.svgEl("g", { transform: "scale(" + k + ") translate(" + -vx + " " + -vy + ")" }, svg);
  const marcados = new Set(S.marcados || []);
  const cajas = {};
  for (const [id, dep] of Object.entries(GEOMETRIA.deptos)) {
    const p = H.svgEl("path", { d: dep.d, fill: marcados.has(id) ? col.dest : col.suave, stroke: col.sobre, "stroke-width": 2.2, "stroke-linejoin": "round" }, g);
    cajas[id] = p;
  }
  for (const m of S.marcadores || []) {
    H.assert(cajas[m.id], "mapa: marcador en un departamento desconocido " + m.id);
    // Centroide de área (informe.py) o, si falta, el centro de la caja.
    const b = cajas[m.id].getBBox(), c = (GEOMETRIA.centros || {})[m.id] || [b.x + b.width / 2, b.y + b.height / 2];
    const cx = (c[0] - vx) * k + (m.dx || 0), cy = (c[1] - vy) * k + (m.dy || 0);
    const txt = String(m.n), w = txt.length > 1 ? Math.max(22, H.medir(txt, GX.MONO_B) + 14) : 22;
    GX.rect(svg, cx - w / 2, cy - 11, w, 22, col.texto, { rx: 11 });
    GX.t(svg, cx, cy + 4.5, txt, GX.MONO_B, col.sobre, { "text-anchor": "middle" });
  }
};
