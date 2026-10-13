// mapa · los 22 departamentos (GEOMETRIA la inyecta scripts/informe.py desde design/mapa_geometria.svg).
//   Coroplético (contrato de templates/graficos/mapa.html): valores {GTxx|nombre: v} (≥ 12 con valor; el resto
//   va rayado «sin dato»), cortes [2–5 límites] o clases 3–6 con metodo "cuantiles"|"iguales" y redondear
//   (H.cortes y H.claseDe, los mismos de la tarjeta), destacar (id o nombre: contorno en el acento con halo),
//   rotular "extremos"|"ninguno", formato. Colores de clase de GX.rampa; leyenda (de menor a mayor) y las líneas
//   MAYOR / MENOR en una franja bajo el mapa, dentro del mismo svg (70 px si caben en una fila cada una).
//   Sin `valores`: marcados [GTxx…] en el acento y el resto en tinta suave (p. ej. «contiene un área en alerta»).
//   Siempre: marcadores [{id, n, dx, dy}] numerados en el centroide (dx/dy corrigen en px si dos quedan juntos),
//   ancho (acota el mapa: un mapa a 672 px mide 705 de alto; la franja usa todo el ancho de la columna) y
//   alto como tope (reduce el mapa hasta 150 px; si aun así no cabe, la figura crece: doc).
const GXM = (() => {
  // Unidades inseparables { muestra, borde, partes: [{ s, font, fill, ls, gap }] } repartidas en filas de 16 px
  // que caben en maxW, separadas `sep` px. Devuelve [[{ u, x, w }…]…] sin dibujar (sirve para medir).
  const anchoDe = (u) => (u.muestra != null ? 28 : 0) + u.partes.reduce((s, p) => s + H.medir(p.s, p.font) + (p.ls || 0) * p.s.length + (p.gap || 0), 0);
  const filas = (unidades, maxW, sep) => {
    const out = [];
    let fila = [], x = 0;
    for (const u of unidades) {
      const w = anchoDe(u);
      if (fila.length && x + w > maxW) { out.push(fila); fila = []; x = 0; }
      fila.push({ u, x, w });
      x += w + sep;
    }
    if (fila.length) out.push(fila);
    return out;
  };
  const dibujar = (svg, filasArr, y) => {
    for (const fila of filasArr) {
      for (const { u, x } of fila) {
        let xx = x;
        if (u.muestra != null) { GX.rect(svg, xx, y + 3, 22, 10, u.muestra, u.borde ? { stroke: u.borde, "stroke-width": 2 } : null); xx += 28; }
        for (const p of u.partes) {
          GX.t(svg, xx, y + 13, p.s, p.font, p.fill, p.ls ? { style: "font:" + p.font + ";letter-spacing:" + p.ls + "px" } : null);
          xx += H.medir(p.s, p.font) + (p.ls || 0) * p.s.length + (p.gap || 0);
        }
      }
      y += 16;
    }
    return y;
  };
  return { filas, dibujar };
})();

G.mapa = (el, S, { ancho, alto, col }) => {
  H.assert(typeof GEOMETRIA === "object", "mapa: falta GEOMETRIA (informe.py la inyecta)");
  const [vx, vy, vw, vh] = GEOMETRIA.viewBox.split(/\s+/).map(Number), razon = vh / vw;
  const ids = Object.keys(H.NOMBRES), coro = S.valores != null, acento = col.tinta || col.dest;
  const f = (v) => GX.fmt(v, S.formato), M = GX.MONO, MB = GX.MONO_B;

  // ---- Coroplético: valores → clases (H.cortes, compartido con la tarjeta), destacado y extremos ----
  const val = {};
  let con = [], sin = [], cortes = [], colores = [], hi = null, leyenda = [], lineas = [], sinDatoU = null;
  if (coro) {
    H.assert(typeof S.valores === "object" && !Array.isArray(S.valores), "valores debe ser un objeto { GT01: 12.3, … }");
    for (const [k, v] of Object.entries(S.valores)) {
      if (v === null || v === undefined) continue;
      const id = H.idDepto(k);
      H.assert(typeof v === "number" && isFinite(v), "valores: «" + k + "» no es numérico");
      H.assert(!(id in val), "valores: «" + k + "» está repetido");
      val[id] = v;
    }
    con = ids.filter((id) => id in val);
    sin = ids.filter((id) => !(id in val));
    H.assert(con.length >= 12, "mapa necesita al menos 12 departamentos con valor (hay " + con.length + ")");
    hi = S.destacar ? H.idDepto(S.destacar) : null;
    if (hi) H.assert(hi in val, "destacar: «" + S.destacar + "» no tiene valor");
    const rotular = S.rotular === "ninguno" ? "ninguno" : "extremos";
    const vals = con.map((id) => val[id]).sort((a, b) => a - b), min = vals[0], max = vals[vals.length - 1];
    cortes = H.cortes(vals, { cortes: S.cortes, clases: S.clases, metodo: S.metodo, redondear: S.redondear });
    const nc = cortes.length + 1;
    colores = GX.rampa(nc, col);
    for (let i = 0; i < nc; i++) {
      const lo = i === 0 ? min : cortes[i - 1], hiV = i === nc - 1 ? max : cortes[i];
      leyenda.push({ muestra: colores[i], partes: [{ s: f(lo) + " – " + f(hiV), font: M, fill: col.texto }] });
    }
    if (sin.length) leyenda.push(sinDatoU = { muestra: "none", partes: [{ s: "Sin dato", font: M, fill: col.texto }] });
    const orden = con.slice().sort((a, b) => val[b] - val[a] || a.localeCompare(b));
    const mayor = orden.slice(0, 3), menor = orden.slice(-3).reverse();
    const nombreValor = (id, sep) => ({ partes: [
      { s: H.NOMBRES[id], font: M, fill: id === hi ? acento : col.texto, gap: 5 },
      { s: f(val[id]), font: MB, fill: id === hi ? acento : col.texto, gap: sep ? 5 : 0 }].concat(sep ? [{ s: "·", font: M, fill: col.texto }] : []) });
    if (hi && !(rotular === "extremos" && (mayor.includes(hi) || menor.includes(hi))))
      lineas.push([Object.assign({ muestra: colores[H.claseDe(val[hi], cortes)], borde: col.dest }, nombreValor(hi, false))]);
    if (rotular === "extremos") {
      const lista = (t, arr) => [{ partes: [{ s: t, font: M, fill: col.texto, ls: 1.2, gap: 2 }] }].concat(arr.map((id, i) => nombreValor(id, i < arr.length - 1)));
      lineas.push(lista("MAYOR", mayor), lista("MENOR", menor));
    }
  }

  // ---- Medidas: la franja ocupa todo el ancho de la columna; el mapa, W (S.ancho) acotado por `alto` ----
  const franja = { alto: 0, ley: [], lineas: [] };
  if (coro) {
    franja.ley = GXM.filas(leyenda, ancho, 14);
    franja.lineas = lineas.map((l) => GXM.filas(l, ancho, 8));
    franja.alto = 10 + franja.ley.length * 16 + (lineas.length ? 8 + franja.lineas.reduce((s, r) => s + r.length, 0) * 16 : 0) + 4;
  }
  let W = Math.min(ancho, S.ancho || ancho);
  if (alto) W = Math.max(Math.min(W, 150), Math.min(W, Math.floor((alto - franja.alto) / razon)));
  const mapaH = Math.round(W * razon), Hh = mapaH + franja.alto, k = W / vw;
  const svg = GX.lienzo(el, ancho, Hh, S.aria);
  if (sinDatoU) sinDatoU.muestra = GX.sinDato(svg, col);

  // ---- Mapa: relleno por clase (o marcados), borde entre departamentos en el color del fondo ----
  const g = H.svgEl("g", { transform: "scale(" + k + ") translate(" + -vx + " " + -vy + ")" }, svg);
  const marcados = new Set(coro ? [] : S.marcados || []), cajas = {};
  for (const id of ids) {
    const geo = GEOMETRIA.deptos[id];
    H.assert(geo && geo.d, "GEOMETRIA sin " + id + ": corre python3 scripts/build_mapa.py");
    const fill = coro ? (id in val ? colores[H.claseDe(val[id], cortes)] : sinDatoU.muestra) : marcados.has(id) ? col.dest : col.suave;
    cajas[id] = H.svgEl("path", { d: geo.d, fill, stroke: col.sobre, "stroke-width": 1.5, "stroke-linejoin": "round", "vector-effect": "non-scaling-stroke" }, g);
  }
  if (hi) for (const [stroke, w] of [[col.sobre, 6], [col.dest, 2.5]])  // halo del fondo (separa de los vecinos) + acento encima
    H.svgEl("path", { d: GEOMETRIA.deptos[hi].d, fill: "none", stroke, "stroke-width": w, "stroke-linejoin": "round", "vector-effect": "non-scaling-stroke" }, g);

  // ---- Franja: leyenda de clases (+ sin dato), destacado si no sale en los extremos, MAYOR / MENOR ----
  if (coro) {
    let y = GXM.dibujar(svg, franja.ley, mapaH + 10);
    if (franja.lineas.length) { y += 8; for (const fl of franja.lineas) y = GXM.dibujar(svg, fl, y); }
    if (sin.length) GX.anotar(el, sin.length === 1 ? "1 departamento sin dato" : sin.length + " departamentos sin dato");
  }

  // ---- Marcadores numerados, encima de todo ----
  for (const m of S.marcadores || []) {
    H.assert(cajas[m.id], "mapa: marcador en un departamento desconocido " + m.id);
    // Centroide de área (informe.py) o, si falta, el centro de la caja.
    const b = cajas[m.id].getBBox(), c = (GEOMETRIA.centros || {})[m.id] || [b.x + b.width / 2, b.y + b.height / 2];
    const cx = (c[0] - vx) * k + (m.dx || 0), cy = (c[1] - vy) * k + (m.dy || 0);
    const txt = String(m.n), w = txt.length > 1 ? Math.max(22, H.medir(txt, MB) + 14) : 22;
    GX.rect(svg, cx - w / 2, cy - 11, w, 22, col.texto, { rx: 11 });
    GX.t(svg, cx, cy + 4.5, txt, MB, col.sobre, { "text-anchor": "middle" });
  }
};
