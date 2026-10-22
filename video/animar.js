// Animación de tarjetas para /video: estado = f(t), sin transiciones CSS.
// Se inyecta al final de una copia de tuit_N.html. Lee el estado final del DOM ya renderizado y, en p = 1,
// restaura exactamente los atributos/textos originales (las cifras nunca se redondean distinto).
// T = { tit, ini, nota, valores: { "8402.4": [desde, hasta], ... }, linea_fin }  (segundos de la escena)
// Plantillas con animador propio: antes-despues, cifra, barras-v, linea, barras-h, waffle, dona, pesas, mapa,
// pendiente, divergente, apilada, embudo, bullet, agrupadas, treemap, area-apilada, calor, cascada, combinado,
// dispersion, hemiciclo, linea-tiempo, multiples, pictograma, piramide. Cualquier otra (o una tarjeta sin
// plantilla): el gráfico se revela con un barrido en T.ini.
// window.__caja(clave) → [x, y, w, h] en px de la tarjeta del elemento que muestra ese valor (para el foco de
// escena.html), o null si la plantilla no lo sabe; nunca lanza.
(() => {
  const clamp = (x) => Math.max(0, Math.min(1, x));
  const eo = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const prog = (t, a, b) => (t >= b ? 1 : eo((t - a) / Math.max(0.001, b - a)));
  const aparecer = (el, p, dy = 24) => { if (!el) return; el.style.opacity = p; el.style.transform = `translateY(${(1 - p) * dy}px)`; };
  const clave = (v) => String(Number(v));
  // «estres-barras-v» (templates/.pruebas) anima como «barras-v»
  const plantilla = ((document.documentElement.innerHTML.match(/plantilla: ([\w-]+) ·/) || [])[1] || "").replace(/^estres-/, "");
  let E = null;  // estado final leído una sola vez

  // ventana de animación de un valor: la de la voz si se menciona; si no, al arrancar el gráfico
  const ventana = (T, v, i) => T.valores[clave(v)] || [T.ini + 0.25 * i, T.ini + 1.2 + 0.25 * i];
  // como ventana(), pero prueba varias claves (valor crudo de DATA y el número que se ve en la tarjeta)
  const ventanaDe = (T, vs, i) => { for (const v of vs) if (v != null && T.valores[clave(v)]) return T.valores[clave(v)]; return ventana(T, NaN, i); };

  // Pulso de los años que dice la voz (T.anios = { "1997": [desde, hasta] }, solo años que la tarjeta tiene en su
  // eje): el rótulo del eje pasa a negrita y las demás columnas bajan de opacidad mientras dura; en p = 1 no queda
  // ningún estilo. Sin zoom: el foco es solo para las cifras.
  // rótulos del eje x, uno por etiqueta y en su orden (null si no se encuentra), con su atributo style original:
  // el pulso se aplica reescribiendo el atributo entero (tocar style.fontWeight desarma el shorthand «font» y al
  // borrarlo el peso no vuelve al original: V7 lo detectaría)
  const ejesX = (etiquetas) => {
    const ts = [...document.querySelectorAll("#grafico svg text")].filter((t) => !t.classList.contains("t-val") && !t.classList.contains("t-eje"));
    return (etiquetas || []).map((lab) => { const t = ts.find((x) => x.textContent === String(lab)); return t ? { t, estilo: t.getAttribute("style") || "" } : null; });
  };
  // índice de la etiqueta que corresponde a un año dicho («1997» casa con «1997» y con «1997-98»)
  const indiceAnio = (etiquetas, anio) => (etiquetas || []).findIndex((l) => new RegExp("^" + anio + "(?!\\d)").test(String(l)));
  // peso del pulso en t: entra en 0.35 s desde que la voz empieza el año y sale 0.6 s después de terminarlo
  const pesoPulso = (t, a, b) => prog(t, a - 0.1, a + 0.25) * (1 - prog(t, b + 0.2, b + 0.6));
  // aplica el pulso: columna(i, peso de la columna i, peso total) para lo que cada plantilla quiera atenuar
  const pulsarEje = (t, T, etiquetas, columna) => {
    const pulsos = Object.entries(T.anios || {}).map(([anio, [a, b]]) => ({ i: indiceAnio(etiquetas, anio), w: pesoPulso(t, a, b) })).filter((p) => p.i >= 0);
    const wTot = Math.max(0, ...pulsos.map((p) => p.w));
    (E.ejes || []).forEach((lab, i) => {
      const wi = Math.max(0, ...pulsos.filter((p) => p.i === i).map((p) => p.w));
      if (lab) lab.t.setAttribute("style", wTot > 0 ? `${lab.estilo};${wi > 0.5 ? "font-weight:800;" : ""}opacity:${(1 - 0.4 * (wTot - wi)).toFixed(3)}` : lab.estilo);
      if (columna) columna(i, wi, wTot);
    });
  };

  // Número dentro de un texto ya formateado («US$5.90», «1,596.2 kg», «−12%»): se cuenta con el mismo
  // formato (decimales, miles, prefijo y sufijo) y en p = 1 se devuelve el texto original intacto.
  const RE_NUM = /([-−]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?/;
  function numTexto(s) {
    const m = (s || "").match(RE_NUM);
    if (!m) return null;
    const dec = m[3] ? m[3].length : 0, miles = m[2].includes(",");
    const v = parseFloat(m[2].replace(/,/g, "") + (m[3] ? "." + m[3] : "")) * (m[1] ? -1 : 1);
    const pre = s.slice(0, m.index), post = s.slice(m.index + m[0].length);
    const fmt = (x) => {
      let c = Math.abs(x).toFixed(dec);
      if (miles) { const [e, d] = c.split("."); c = e.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (d ? "." + d : ""); }
      return pre + (x < 0 ? m[1] || "-" : "") + c + post;
    };
    return { v, fmt };
  }
  const contar = (el, txt, p) => { const n = numTexto(txt); el.textContent = p >= 1 || !n ? txt : n.fmt(n.v * p); };
  // opacidad animada que respeta el atributo `opacity` del elemento (p. ej. .85) y en p = 1 no deja estilo
  const opacar = (el, p) => { if (!el) return; const base = el.hasAttribute("opacity") ? +el.getAttribute("opacity") : 1; el.style.opacity = p >= 1 ? "" : (base * p).toFixed(3); };
  const attr = (el, k) => +el.getAttribute(k);
  const cerca = (a, b, tol = 1.5) => Math.abs(a - b) <= tol;

  function leer() {
    const q = (s) => document.querySelector(s), qa = (s) => [...document.querySelectorAll(s)];
    E = { svg: q("#grafico svg") };
    if (plantilla === "antes-despues") {
      E.cols = ["antes", "despues"].map((k) => {
        const c = q(".ad-col." + k);
        return { k, c, num: c.querySelector(".num"), txt: c.querySelector(".num").textContent,
                 barra: c.querySelector(".barra"), ancho: parseFloat(c.querySelector(".barra").style.width) };
      });
      E.flecha = q(".ad-flecha"); E.pildora = q(".ad-pildora");
    } else if (plantilla === "cifra") {
      E.num = q(".cifra-num"); E.txt = E.num.textContent; E.ctx = q(".cifra-ctx"); E.cap = q(".cifra-txt");
      E.num.style.fontSize = getComputedStyle(E.num).fontSize;  // fija el tamaño final mientras cuenta
    } else if (plantilla === "barras-v") {
      E.barras = qa("#grafico svg rect").map((r) => ({ r, y: r.getAttribute("y"), h: r.getAttribute("height") }));
      E.vals = qa("#grafico svg text.t-val").map((t) => ({ t, y: t.getAttribute("y"), txt: t.textContent }));
      E.ejes = ejesX(DATA.etiquetas);
    } else if (plantilla === "linea") {
      E.lineas = qa("#grafico svg path").filter((p) => p.getAttribute("fill") === "none")
        .map((p) => ({ p, L: p.getTotalLength() }));
      E.puntos = qa("#grafico svg circle");
      E.ejes = ejesX(DATA.etiquetasX);
    } else if (plantilla === "barras-h") {
      // un rect y un t-val por item, en el orden dibujado (desc o «dado», como la plantilla)
      const D = DATA, items = D.orden === "dado" ? D.items.slice() : D.items.slice().sort((a, b) => b.valor - a.valor);
      const vals = qa("#grafico svg text.t-val");
      E.barras = qa("#grafico svg rect").map((r, i) => ({ r, w: r.getAttribute("width"), v: (items[i] || {}).valor,
        t: vals[i], txt: vals[i] ? vals[i].textContent : "" }));
    } else if (plantilla === "waffle") {
      E.on = qa(".wf-celdas span.on");
      E.num = q(".wf-texto .num"); E.txt = E.num ? E.num.textContent : "";
      E.resto = qa(".wf-texto .t, .wf-ley");
    } else if (plantilla === "dona") {
      E.aro = q(".dona-aro"); E.bg = E.aro.style.background;
      E.v = q(".dona-centro .v"); E.vtxt = E.v.textContent; E.t = q(".dona-centro .t");
      E.items = qa(".dona-item").map((it) => ({ it, p: it.querySelector(".p").textContent }));
    } else if (plantilla === "pesas") {
      const D = DATA, items = D.orden === "desc" ? D.items.slice().sort((x, y) => y.b - x.b) : D.items.slice();
      const conect = qa("#grafico svg line").filter((l) => l.getAttribute("stroke-linecap") === "round");
      const circ = qa("#grafico svg circle");
      const labs = qa("#grafico svg text").filter((t) => /700 22px 'JetBrains Mono'/.test(t.getAttribute("style") || ""));
      E.items = items.map((it, i) => ({ a: it.a, b: it.b, l: conect[i], x2: conect[i].getAttribute("x2"),
        ca: circ[2 * i], cb: circ[2 * i + 1], cx: circ[2 * i + 1].getAttribute("cx"),
        la: labs[2 * i], lat: labs[2 * i].textContent, lb: labs[2 * i + 1], lbt: labs[2 * i + 1].textContent }));
      nombrarFilas(labs);
    } else if (plantilla === "pendiente") {
      // la plantilla dibuja el item destacado al final: mismo orden aquí
      const D = DATA, n = D.items.length, hi = ((D.destacar || 0) % n + n) % n;
      const orden = D.items.map((_, i) => i).sort((a, b) => (a === hi) - (b === hi));
      const lineas = qa("#grafico svg line").filter((l) => l.getAttribute("stroke-linecap") === "round");
      const circ = qa("#grafico svg circle");
      const labs = qa("#grafico svg text").filter((t) => /700 26px 'JetBrains Mono'/.test(t.getAttribute("style") || ""));
      E.items = orden.map((k, j) => ({ a: D.items[k].a, b: D.items[k].b, l: lineas[j],
        x1: +lineas[j].getAttribute("x1"), y1: +lineas[j].getAttribute("y1"),
        x2: lineas[j].getAttribute("x2"), y2: lineas[j].getAttribute("y2"),
        ca: circ[2 * j], cb: circ[2 * j + 1], la: labs[2 * j], lat: labs[2 * j].textContent, lb: labs[2 * j + 1], lbt: labs[2 * j + 1].textContent }));
      nombrarFilas(labs);
    } else if (plantilla === "divergente") {
      // un rect por item (desde el eje x0 hacia su valor) y, por item, dos textos: nombre y valor
      const D = DATA, items = D.orden === "dado" ? D.items.slice() : D.items.slice().sort((a, b) => b.valor - a.valor);
      const rects = qa("#grafico svg rect").filter((r) => !r.closest("pattern")), ts = qa("#grafico svg text");
      E.items = items.map((it, i) => ({ v: it.valor, r: rects[i], xs: rects[i] && rects[i].getAttribute("x"), ws: rects[i] && rects[i].getAttribute("width"),
        nombre: ts[2 * i] || null, t: ts[2 * i + 1] || null, txt: ts[2 * i + 1] ? ts[2 * i + 1].textContent : "" })).filter((it) => it.r);
      const eje = qa("#grafico svg line").find((l) => l.getAttribute("x1") === l.getAttribute("x2"));
      E.x0 = eje ? +eje.getAttribute("x1") : Math.max(...E.items.map((it) => +it.xs));
    } else if (plantilla === "apilada") {
      // filas de segmentos (rects con la misma y, en orden de dibujo); totales t-val; rótulos centrados en su segmento
      const filas = new Map();
      qa("#grafico svg rect").forEach((r) => { const y = r.getAttribute("y"); if (!filas.has(y)) filas.set(y, []); filas.get(y).push({ r, ws: r.getAttribute("width") }); });
      E.filas = [...filas.values()];
      const ts = qa("#grafico svg text");
      E.totales = ts.filter((t) => t.classList.contains("t-val")).map((t) => ({ t, txt: t.textContent }));
      E.rotulos = ts.filter((t) => t.getAttribute("text-anchor") === "middle").map((t) => {
        const x = +t.getAttribute("x"), y = +t.getAttribute("y");
        let fila = -1, j = -1;
        E.filas.forEach((segs, r) => segs.forEach((sg, jj) => { const rx = +sg.r.getAttribute("x"), ry = +sg.r.getAttribute("y");
          if (x >= rx && x <= rx + +sg.ws && y >= ry && y <= ry + +sg.r.getAttribute("height")) { fila = r; j = jj; } }));
        return { t, fila, j };
      }).filter((ro) => ro.fila >= 0);
    } else if (plantilla === "embudo") {
      const rects = qa("#grafico svg rect"), ts = qa("#grafico svg text"), vals = ts.filter((t) => t.classList.contains("t-val"));
      E.items = rects.map((r, i) => { const y = +r.getAttribute("y"), h = +r.getAttribute("height");
        return { r, ws: r.getAttribute("width"), v: ((DATA.etapas || [])[i] || {}).valor, t: vals[i] || null, txt: vals[i] ? vals[i].textContent : "",
          nombre: ts.find((x) => !x.classList.contains("t-val") && +x.getAttribute("x") === 0 && Math.abs(+x.getAttribute("y") - (y - 14)) < 1.5) || null,
          pct: ts.find((x) => !x.classList.contains("t-val") && +x.getAttribute("x") !== 0 && Math.abs(+x.getAttribute("y") - (y + h / 2 + 7)) < 1.5) || null }; });
    } else if (plantilla === "bullet") {
      // por item, en orden de dibujo: pista (todo el ancho), barra, [exceso rayado], marcador de la meta (6 px)
      const rects = qa("#grafico svg rect").filter((r) => !r.closest("pattern")), vals = qa("#grafico svg text.t-val");
      E.items = [];
      for (let i = 0, k = 0; k + 2 < rects.length + 1 && rects[k + 1]; i++) {
        const pista = rects[k++], barra = rects[k++];
        const exceso = rects[k] && (rects[k].getAttribute("fill") || "").startsWith("url(") ? rects[k++] : null;
        const marca = rects[k++] || null;
        E.items.push({ v: ((DATA.items || [])[i] || {}).valor, pista, barra, ws: barra.getAttribute("width"), exceso, wes: exceso && exceso.getAttribute("width"),
          marca, t: vals[i] || null, txt: vals[i] ? vals[i].textContent : "" });
      }
    } else if (plantilla === "agrupadas") {
      const D = DATA, m = D.series.length, ts = qa("#grafico svg text");
      const labs = ts.filter((t) => !t.classList.contains("t-eje") && +t.getAttribute("x") > 0);
      E.barras = qa("#grafico svg rect").map((r, k) => { const y = +r.getAttribute("y"), h = +r.getAttribute("height"), i = Math.floor(k / m), j = k % m;
        const t = labs.find((l) => Math.abs(+l.getAttribute("y") - (y + h / 2 + 7)) < 1.5) || null;
        return { r, ws: r.getAttribute("width"), i, v: (D.series[j].valores || [])[i], t, txt: t ? t.textContent : "" }; });
      E.etiquetas = ts.filter((t) => !t.classList.contains("t-eje") && +t.getAttribute("x") === 0);
      E.ref = qa("#grafico svg line").find((l) => l.getAttribute("stroke-dasharray")) || null;
      E.refT = E.ref ? ts.find((t) => t.classList.contains("t-eje") && +t.getAttribute("y") === 16) || null : null;
    } else if (plantilla === "treemap") {
      const ts = qa("#grafico svg text");
      E.teselas = qa("#grafico svg rect").map((r, k) => { const x = +r.getAttribute("x"), y = +r.getAttribute("y"), w = +r.getAttribute("width"), h = +r.getAttribute("height");
        const textos = ts.filter((t) => { const tx = +t.getAttribute("x"), ty = +t.getAttribute("y"); return tx >= x && tx <= x + w && ty >= y && ty <= y + h; });
        return { r, k, cx: x + w / 2, cy: y + h / 2, textos: textos.map((t) => ({ t, txt: t.textContent })) }; });
    } else if (plantilla === "area-apilada") {
      // bandas (path con relleno, de abajo arriba, una por parte), bordes (fill none), rótulos de fin (2 tspan)
      const paths = qa("#grafico svg path");
      E.bandas = paths.filter((p) => p.getAttribute("fill") !== "none");
      E.bordes = paths.filter((p) => p.getAttribute("fill") === "none");
      E.y1 = Math.max(...E.bandas.flatMap((p) => (p.getAttribute("d").match(/[\d.]+/g) || []).filter((_, i) => i % 2 === 1).map(Number)));
      const ts = qa("#grafico svg text");
      E.fines = ts.filter((t) => t.querySelectorAll("tspan").length === 2).map((t) => ({ t, ts: t.querySelectorAll("tspan")[1], txt: t.querySelectorAll("tspan")[1].textContent }));
      E.inicios = ts.filter((t) => t.getAttribute("text-anchor") === "end" && !t.classList.contains("t-eje") && !t.querySelector("tspan"));
      E.guias = qa("#grafico svg line").filter((l) => l.getAttribute("stroke-dasharray"));
    } else if (plantilla === "calor") {
      // celdas (rect rx=3 antes del contorno), su texto centrado, nombres de fila (anchor end), cabecera (y=20)
      const rects = qa("#grafico svg rect"), ts = qa("#grafico svg text");
      const k0 = rects.findIndex((r) => r.getAttribute("fill") === "none");
      const celdas = (k0 < 0 ? rects : rects.slice(0, k0)).filter((r) => r.getAttribute("rx") === "3");
      const filas = new Map();
      celdas.forEach((r) => { const y = attr(r, "y"); if (!filas.has(y)) filas.set(y, []); filas.get(y).push(r); });
      E.filas = [...filas.entries()].sort((a, b) => a[0] - b[0]).map(([y, cs]) => ({ y, celdas: cs.map((r) => {
        const x = attr(r, "x"), w = attr(r, "width"), h = attr(r, "height");
        const t = ts.find((x_) => x_.getAttribute("text-anchor") === "middle" && attr(x_, "x") > x && attr(x_, "x") < x + w && attr(x_, "y") > y && attr(x_, "y") < y + h) || null;
        return { r, t, txt: t ? t.textContent : "" }; }),
        nombre: ts.find((t) => t.getAttribute("text-anchor") === "end" && attr(t, "y") > y && attr(t, "y") < y + attr(cs[0], "height")) || null }));
      E.cabecera = ts.filter((t) => attr(t, "y") === 20);
      E.resto = [...(k0 < 0 ? [] : rects.slice(k0)), ...ts.filter((t) => attr(t, "y") > Math.max(...[...filas.keys()]) + 40)];
    } else if (plantilla === "cascada") {
      // filas: rect + nombre (x=0) + rótulo (anchor start/end) + conector vertical dasharray; el eje es la primera line
      const rects = qa("#grafico svg rect"), ts = qa("#grafico svg text"), lines = qa("#grafico svg line");
      const eje = lines.find((l) => !l.getAttribute("stroke-dasharray")), conect = lines.filter((l) => l.getAttribute("stroke-dasharray"));
      E.x0 = eje ? attr(eje, "x1") : 0;
      E.items = rects.map((r, k) => { const y = attr(r, "y"), h = attr(r, "height"), cy = y + h / 2, x = attr(r, "x"), w = attr(r, "width");
        const desde = k === 0 || !conect[k - 1] ? E.x0 : attr(conect[k - 1], "x1");
        const t = ts.find((x_) => attr(x_, "x") !== 0 && cerca(attr(x_, "y"), cy + 8, 3)) || null;
        return { r, xs: r.getAttribute("x"), ws: r.getAttribute("width"), x, w, derecha: cerca(desde, x, 2) || k === rects.length - 1 && cerca(E.x0, x, 2),
          nombre: ts.find((x_) => attr(x_, "x") === 0 && cerca(attr(x_, "y"), cy + 8, 3)) || null, t, txt: t ? t.textContent : "", c: conect[k] || null }; });
    } else if (plantilla === "combinado") {
      // barras (rect fuera de la leyenda), línea (path fill none), puntos (circle), rótulos por columna
      const rects = qa("#grafico svg rect").filter((r) => attr(r, "y") > 30), ts = qa("#grafico svg text");
      E.barras = rects.map((r) => { const x = attr(r, "x"), w = attr(r, "width"), cx = x + w / 2;
        const t = ts.find((x_) => !x_.classList.contains("t-eje") && cerca(attr(x_, "x"), cx, 2) && /18px/.test(x_.getAttribute("style") || "")) || null;
        return { r, ys: r.getAttribute("y"), hs: r.getAttribute("height"), cx, t, txt: t ? t.textContent : "" }; });
      E.linea = qa("#grafico svg path").find((p) => p.getAttribute("fill") === "none") || null;
      E.L = E.linea ? E.linea.getTotalLength() : 0;
      E.puntos = qa("#grafico svg circle");
      E.rotLinea = ts.filter((t) => /paint-order/.test(t.getAttribute("style") || "")).map((t) => ({ t, txt: t.textContent }));
    } else if (plantilla === "dispersion") {
      E.puntos = qa("#grafico svg circle").map((c) => ({ c, rs: c.getAttribute("r") }));
      E.guias = [...qa("#grafico svg line").filter((l) => l.getAttribute("stroke-dasharray")), ...qa("#grafico svg text.t-eje").filter((t) => !/^[\d.,−-]+%?$/.test(t.textContent))];
      E.nombres = qa("#grafico svg text").filter((t) => !t.classList.contains("t-eje") && /paint-order/.test(t.getAttribute("style") || ""));
    } else if (plantilla === "hemiciclo") {
      const circ = qa("#grafico svg circle"), ts = qa("#grafico svg text"), total = DATA.total || 0;
      E.curules = circ.slice(0, total);
      const muestras = circ.slice(total);
      E.bloques = muestras.map((m, j) => { const cy = attr(m, "cy");
        const fila = ts.filter((t) => !t.classList.contains("t-val") && cerca(attr(t, "y"), cy, 14));
        const v = fila.find((t) => t.getAttribute("text-anchor") === "end") || null;
        return { m, nombre: fila.find((t) => t !== v) || null, v, txt: v ? v.textContent : "", n: ((DATA.bloques || [])[j] || {}).curules }; });
      E.mayoria = [...qa("#grafico svg line"), ...ts.filter((t) => !t.classList.contains("t-val") && !E.bloques.some((b) => b.nombre === t || b.v === t))];
      E.total = q("#grafico svg text.t-val");
    } else if (plantilla === "linea-tiempo") {
      E.espina = qa("#grafico svg line").find((l) => !l.getAttribute("stroke-dasharray")) || null;
      E.y2 = E.espina ? E.espina.getAttribute("y2") : null;
      const circ = qa("#grafico svg circle"), ts = qa("#grafico svg text"), rects = qa("#grafico svg rect");
      const xs = E.espina ? attr(E.espina, "x1") : 0;
      const puntos = circ.filter((c) => cerca(attr(c, "cx"), xs, 2));
      E.eventos = puntos.map((c) => { const cy = attr(c, "cy");
        const textos = ts.filter((t) => Math.abs(attr(t, "y") - cy) <= 40);
        const valor = textos.filter((t) => attr(t, "x") > xs).sort((a, b) => attr(b, "x") - attr(a, "x"))[0] || null;
        const rect = rects.find((r) => attr(r, "y") <= cy && attr(r, "y") + attr(r, "height") >= cy) || null;
        const forma = circ.find((x_) => x_ !== c && Math.abs(attr(x_, "cy") - cy) <= 20) || null;
        return { c, rs: c.getAttribute("r"), cy, textos: textos.filter((t) => t !== valor), valor, txt: valor ? valor.textContent : "",
          rect, ws: rect && rect.getAttribute("width"), forma, frs: forma && forma.getAttribute("r") }; }).sort((a, b) => a.cy - b.cy);
      E.yTop = E.eventos.length ? E.eventos[0].cy : 0; E.yBot = E.eventos.length ? E.eventos[E.eventos.length - 1].cy : 1;
    } else if (plantilla === "multiples") {
      const fondos = qa("#grafico svg rect"), ts = qa("#grafico svg text"), paths = qa("#grafico svg path"), circ = qa("#grafico svg circle"), lines = qa("#grafico svg line");
      const dentro = (el, f) => { const x = attr(el, el.tagName === "circle" ? "cx" : "x"), y = attr(el, el.tagName === "circle" ? "cy" : "y");
        return x >= attr(f, "x") - 1 && x <= attr(f, "x") + attr(f, "width") + 1 && y >= attr(f, "y") - 1 && y <= attr(f, "y") + attr(f, "height") + 1; };
      E.paneles = fondos.map((f) => { const x = attr(f, "x"), y = attr(f, "y"), w = attr(f, "width");
        const cabecera = ts.filter((t) => cerca(attr(t, "y"), y + 24, 2) && attr(t, "x") >= x && attr(t, "x") <= x + w);
        const v = cabecera.find((t) => t.getAttribute("text-anchor") === "end") || null;
        const path = paths.find((p) => { const m = (p.getAttribute("d") || "").match(/M\s*([\d.]+)[ ,]([\d.]+)/); return m && +m[1] >= x - 1 && +m[1] <= x + w + 1 && +m[2] >= y && +m[2] <= y + attr(f, "height"); }) || null;
        return { f, nombre: cabecera.find((t) => t !== v) || null, v, txt: v ? v.textContent : "", path, L: path ? path.getTotalLength() : 0,
          circ: circ.find((c) => dentro(c, f)) || null, otros: [...lines.filter((l) => dentro(l, f) || (attr(l, "x1") >= x && attr(l, "x1") <= x + w && attr(l, "y1") >= y)), ...ts.filter((t) => t.classList.contains("t-eje") && dentro(t, f))] }; });
    } else if (plantilla === "pictograma") {
      E.celdas = qa(".pg-celdas > span");
      E.on = E.celdas.filter((c) => c.classList.contains("on"));
      E.num = q(".pg-texto .num"); E.txt = E.num ? E.num.textContent : "";
      E.resto = qa(".pg-texto .t, .pg-ley");
    } else if (plantilla === "piramide") {
      // por grupo (de arriba abajo): rótulo central, rect izquierdo (crece hacia la izquierda), rect derecho, valores
      const rects = qa("#grafico svg rect"), ts = qa("#grafico svg text");
      E.grupos = [];
      for (let k = 0; k + 1 < rects.length; k += 2) {
        const li = rects[k], de = rects[k + 1], y = attr(li, "y"), h = attr(li, "height"), cy = y + h / 2;
        const fila = ts.filter((t) => cerca(attr(t, "y"), cy + 7, 3) || cerca(attr(t, "y"), cy + 8, 3));
        const vi = fila.find((t) => t.getAttribute("text-anchor") === "end") || null, vd = fila.find((t) => t.getAttribute("text-anchor") === "start") || null;
        E.grupos.push({ li, lis: li.getAttribute("x"), liw: li.getAttribute("width"), de, dew: de.getAttribute("width"),
          nombre: fila.find((t) => t.getAttribute("text-anchor") === "middle") || null,
          vi, vix: vi && vi.getAttribute("x"), vit: vi ? vi.textContent : "", vd, vdx: vd && vd.getAttribute("x"), vdt: vd ? vd.textContent : "" });
      }
    } else if (plantilla === "mapa") {
      const g = E.svg.querySelector(":scope > g");
      E.deptos = [...g.querySelectorAll("path")].filter((p) => p.getAttribute("fill") !== "none");
      E.contorno = [...g.querySelectorAll("path")].filter((p) => p.getAttribute("fill") === "none");
      // columna derecha (leyenda, extremos): todo lo que no es el grupo del mapa ni <defs>
      E.col = [...E.svg.children].filter((el) => el !== g && el.tagName !== "defs");
      E.textos = E.col.filter((el) => el.tagName === "text").map((t) => ({ t, txt: t.textContent }));
      // la fila del destacado en la columna: su casilla (borde a1 de 4 px) y los textos a su altura
      const casilla = E.col.find((el) => el.tagName === "rect" && +el.getAttribute("stroke-width") === 4);
      const cy = casilla ? +casilla.getAttribute("y") + +casilla.getAttribute("height") / 2 : null;
      E.dest = casilla ? { rect: casilla, textos: E.textos.filter((x) => Math.abs(+x.t.getAttribute("y") - cy) <= 20).map((x) => x.t) } : null;
    }
  }

  // pesas y pendiente: el texto del nombre de cada fila (a la altura del punto a, a su izquierda), para que el foco
  // encuadre nombre + punto + valor y no solo el número
  function nombrarFilas(labs) {
    const nombres = [...document.querySelectorAll("#grafico svg text")].filter((t) => !labs.includes(t) && !t.classList.contains("t-eje"));
    E.items.forEach((it) => {
      const cy = +it.ca.getAttribute("cy"), cx = Math.min(+it.ca.getAttribute("cx"), +it.cb.getAttribute("cx"));
      it.nombre = nombres.find((t) => Math.abs(+t.getAttribute("y") - cy) <= 16 && +t.getAttribute("x") < cx) || null;
    });
  }

  window.__seek = (t, T) => {
    if (!E) leer();
    const q = (s) => document.querySelector(s);
    aparecer(q("#kicker"), prog(t, T.tit, T.tit + 0.5));
    aparecer(q("#titular"), prog(t, T.tit + 0.1, T.tit + 0.9), 40);
    aparecer(q("#leyenda"), prog(t, T.ini - 0.4, T.ini + 0.2), 10);
    aparecer(q("#nota"), prog(t, T.nota, T.nota + 0.6), 10);
    const D = DATA;

    if (plantilla === "antes-despues") {
      E.cols.forEach((col, i) => {
        const v = D[col.k].valor, [a, b] = ventana(T, v, i), p = prog(t, a, b);
        aparecer(col.c, prog(t, a - 0.4, a), 16);
        col.num.textContent = p >= 1 ? col.txt : H.num(v * p, D.formato);
        col.barra.style.width = (col.ancho * p) + "%";
      });
      const fin = Math.max(...E.cols.map((c, i) => ventana(T, D[c.k].valor, i)[1]));
      aparecer(E.flecha, prog(t, ventana(T, D.despues.valor, 1)[0] - 0.4, ventana(T, D.despues.valor, 1)[0]), 0);
      aparecer(E.pildora, prog(t, fin, fin + 0.5), 12);
    } else if (plantilla === "cifra") {
      const v = D.cifra.valor, [a, b] = ventana(T, v, 0), p = prog(t, a, b);
      aparecer(E.ctx, prog(t, T.ini - 0.4, T.ini + 0.2));
      aparecer(E.num, prog(t, a - 0.3, a), 30);
      E.num.textContent = p >= 1 ? E.txt : H.num(v * p, D.formato);
      aparecer(E.cap, prog(t, b, b + 0.5));
    } else if (plantilla === "barras-v") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      E.barras.forEach((bar, i) => {
        const v = D.valores[i], [a, b] = ventana(T, v, i), p = prog(t, a, b);
        const y0 = parseFloat(bar.y), h0 = parseFloat(bar.h), base = y0 + h0;
        bar.r.setAttribute("height", p >= 1 ? bar.h : h0 * p);
        bar.r.setAttribute("y", p >= 1 ? bar.y : base - h0 * p);
        const lab = E.vals[i];
        if (lab) {
          lab.t.setAttribute("y", p >= 1 ? lab.y : parseFloat(lab.y) + h0 * (1 - p));
          lab.t.textContent = p >= 1 ? lab.txt : H.num(v * p, D.formato);
          lab.t.style.opacity = prog(t, a, a + 0.2);
        }
      });
      pulsarEje(t, T, D.etiquetas, (i, wi, wTot) => { const bar = E.barras[i]; if (bar) bar.r.style.opacity = wTot > 0 ? 1 - 0.3 * (wTot - wi) : ""; });
    } else if (plantilla === "linea") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      const a = T.ini, b = T.linea_fin || T.ini + 4, p = prog(t, a, b);
      E.lineas.forEach((l) => {
        l.p.style.strokeDasharray = p >= 1 ? "" : l.L;
        l.p.style.strokeDashoffset = p >= 1 ? "" : l.L * (1 - p);
      });
      E.puntos.forEach((c) => (c.style.opacity = prog(t, b - 0.2, b + 0.3)));
      pulsarEje(t, T, D.etiquetasX, null);
    } else if (plantilla === "barras-h") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      E.barras.forEach((bar, i) => {
        const n = numTexto(bar.txt), [a, b] = ventanaDe(T, [bar.v, n && n.v], i), p = prog(t, a, b);
        bar.r.setAttribute("width", p >= 1 ? bar.w : parseFloat(bar.w) * p);
        if (bar.t) { contar(bar.t, bar.txt, p); bar.t.style.opacity = prog(t, a, a + 0.2); }
      });
    } else if (plantilla === "waffle") {
      const n = numTexto(E.txt), [a, b] = ventanaDe(T, [D.cifra && D.cifra.valor, D.porcentaje, n && n.v], 0), p = prog(t, a, b);
      const k = Math.round(E.on.length * p);
      E.on.forEach((s, i) => s.classList.toggle("on", p >= 1 || i < k));
      if (E.num) { aparecer(E.num, prog(t, a - 0.3, a), 20); contar(E.num, E.txt, p); }
      E.resto.forEach((el) => aparecer(el, prog(t, b, b + 0.5), 12));
    } else if (plantilla === "dona") {
      const n = numTexto(E.vtxt);
      const claves = [n && n.v, ...E.items.map((x) => (numTexto(x.p) || {}).v), ...D.partes.map((x) => x.valor)];
      const [a, b] = ventanaDe(T, claves, 0), p = prog(t, a, b);
      // barrido: las paradas del conic-gradient escaladas por p; el resto del aro queda vacío
      E.aro.style.background = p >= 1 ? E.bg : E.bg.replace(/(\d+(?:\.\d+)?)%/g, (_, x) => (parseFloat(x) * p).toFixed(3) + "%")
        .replace(/\)\s*$/, ", transparent " + (100 * p).toFixed(3) + "% 100%)");
      aparecer(E.v, prog(t, a - 0.3, a), 20); contar(E.v, E.vtxt, p);
      aparecer(E.t, prog(t, a, a + 0.5), 10);
      E.items.forEach((x, i) => aparecer(x.it, prog(t, b + 0.15 * i, b + 0.5 + 0.15 * i), 12));
    } else if (plantilla === "pesas") {
      E.items.forEach((it, i) => {
        // primero aparece el punto a con su valor; luego el punto b sale de a, viaja estirando la barra y cuenta
        const [aa, ab] = ventana(T, it.a, 2 * i), [ba, bb] = ventana(T, it.b, 2 * i + 1);
        const b0 = Math.max(ba, ab), pb = prog(t, b0, Math.max(bb, b0 + 0.3));
        const xa = parseFloat(it.ca.getAttribute("cx")), xb = parseFloat(it.cx), pa = prog(t, aa - 0.3, aa);
        it.ca.style.opacity = pa; aparecer(it.la, pa, 0);
        it.cb.setAttribute("cx", pb >= 1 ? it.cx : xa + (xb - xa) * pb);
        it.l.setAttribute("x2", pb >= 1 ? it.x2 : xa + (xb - xa) * pb);
        it.cb.style.opacity = it.l.style.opacity = prog(t, b0 - 0.2, b0);
        aparecer(it.lb, prog(t, b0, b0 + 0.3), 0); contar(it.lb, it.lbt, pb);
      });
    } else if (plantilla === "pendiente") {
      E.items.forEach((it, i) => {
        const [aa] = ventana(T, it.a, i), [ba, bb] = ventana(T, it.b, i), pb = prog(t, ba, bb);
        const pa = prog(t, aa - 0.3, aa);
        it.ca.style.opacity = pa; aparecer(it.la, pa, 0);
        it.l.style.opacity = pa;
        it.l.setAttribute("x2", pb >= 1 ? it.x2 : it.x1 + (parseFloat(it.x2) - it.x1) * pb);
        it.l.setAttribute("y2", pb >= 1 ? it.y2 : it.y1 + (parseFloat(it.y2) - it.y1) * pb);
        // el valor b aparece cuando la línea va a medio camino y termina de contar al llegar
        const mitad = ba + (bb - ba) / 2;
        it.cb.style.opacity = prog(t, bb - 0.2, bb + 0.2);
        aparecer(it.lb, prog(t, mitad, mitad + 0.3), 0); contar(it.lb, it.lbt, pb);
      });
    } else if (plantilla === "divergente") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      E.items.forEach((it, i) => {
        const [a, b] = ventana(T, it.v, i), p = prog(t, a, b), x = +it.xs, w = +it.ws, neg = x + w <= E.x0 + 0.5 && x < E.x0 - 0.5;
        it.r.setAttribute("width", p >= 1 ? it.ws : Math.max(0.01, w * p));   // crece desde el eje, a un lado o al otro
        it.r.setAttribute("x", p >= 1 ? it.xs : neg ? x + w * (1 - p) : x);
        if (it.nombre) aparecer(it.nombre, prog(t, a - 0.3, a), 0);
        if (it.t) { contar(it.t, it.txt, p); it.t.style.opacity = prog(t, a, a + 0.2); }
      });
    } else if (plantilla === "apilada") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // cada fila entra en su ventana (la del total si la voz lo dice); dentro, los segmentos de izquierda a derecha
      const ventanas = E.filas.map((segs, r) => { const tot = E.totales[r], n = tot ? numTexto(tot.txt) : null; return ventanaDe(T, [n && n.v], r); });
      E.filas.forEach((segs, r) => {
        const [a, b] = ventanas[r], n = segs.length;
        segs.forEach((sg, j) => { const p = prog(t, a + (b - a) * j / n, a + (b - a) * (j + 1) / n); sg.r.setAttribute("width", p >= 1 ? sg.ws : Math.max(0.01, +sg.ws * p)); });
        const tot = E.totales[r];
        if (tot) { contar(tot.t, tot.txt, prog(t, a, b)); tot.t.style.opacity = prog(t, b - 0.3, b); }
      });
      E.rotulos.forEach((ro) => { const [a, b] = ventanas[ro.fila], n = E.filas[ro.fila].length, fin = a + (b - a) * (ro.j + 1) / n;
        ro.t.style.opacity = prog(t, fin - 0.1, fin + 0.2); });
    } else if (plantilla === "embudo") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      E.items.forEach((it, i) => {
        const [a, b] = ventana(T, it.v, i), p = prog(t, a, b);
        it.r.setAttribute("width", p >= 1 ? it.ws : Math.max(0.01, +it.ws * p));
        if (it.nombre) aparecer(it.nombre, prog(t, a - 0.3, a), 0);
        if (it.t) { contar(it.t, it.txt, p); it.t.style.opacity = prog(t, a, a + 0.2); }
        if (it.pct) it.pct.style.opacity = prog(t, b - 0.1, b + 0.25);
      });
    } else if (plantilla === "bullet") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      E.items.forEach((it, i) => {
        const [a, b] = ventana(T, it.v, i), p = prog(t, a, b);
        it.pista.style.opacity = prog(t, a - 0.4, a - 0.1);
        it.barra.setAttribute("width", p >= 1 ? it.ws : Math.max(0.01, +it.ws * p));
        if (it.exceso) { const q = prog(t, b, b + 0.35); it.exceso.setAttribute("width", q >= 1 ? it.wes : Math.max(0.01, +it.wes * q)); }
        if (it.marca) it.marca.style.opacity = prog(t, b - 0.2, b + 0.2);
        if (it.t) { contar(it.t, it.txt, p); it.t.style.opacity = prog(t, a, a + 0.2); }
      });
    } else if (plantilla === "agrupadas") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      E.barras.forEach((bar) => {
        const [a, b] = ventana(T, bar.v, bar.i), p = prog(t, a, b);
        bar.r.setAttribute("width", p >= 1 ? bar.ws : Math.max(0.01, +bar.ws * p));
        if (bar.t) { contar(bar.t, bar.txt, p); bar.t.style.opacity = prog(t, a, a + 0.2); }
      });
      E.etiquetas.forEach((e, i) => aparecer(e, prog(t, T.ini - 0.4 + 0.25 * i, T.ini + 0.25 * i), 0));
      const fin = T.linea_fin || T.ini + 3;
      if (E.ref) E.ref.style.opacity = prog(t, fin, fin + 0.5);
      if (E.refT) E.refT.style.opacity = prog(t, fin, fin + 0.5);
    } else if (plantilla === "treemap") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // las teselas entran de mayor a menor (orden de dibujo), creciendo desde su centro; los textos cuando acaba la suya
      E.teselas.forEach((te) => {
        const a = T.ini + 0.07 * te.k, b = a + 0.35, p = prog(t, a, b);
        te.r.style.opacity = p;
        if (p >= 1) te.r.removeAttribute("transform");
        else te.r.setAttribute("transform", `translate(${te.cx} ${te.cy}) scale(${(0.85 + 0.15 * p).toFixed(4)}) translate(${-te.cx} ${-te.cy})`);
        te.textos.forEach((x) => {
          const n = numTexto(x.txt), w = n && T.valores[clave(n.v)];
          x.t.style.opacity = w ? prog(t, w[0] - 0.2, w[0]) : prog(t, b - 0.1, b + 0.25);
          if (w) contar(x.t, x.txt, prog(t, w[0], w[1]));
        });
      });
    } else if (plantilla === "area-apilada") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // las bandas suben desde la base en el tramo de la escena; los rótulos de fin cuentan cuando la voz los dice
      const a = T.ini, b = T.linea_fin || T.ini + 2.5, p = prog(t, a, b);
      E.bandas.forEach((pa) => { if (p >= 1) pa.removeAttribute("transform"); else pa.setAttribute("transform", `translate(0 ${E.y1}) scale(1 ${p.toFixed(4)}) translate(0 ${-E.y1})`); });
      E.bordes.forEach((pa) => opacar(pa, prog(t, b - 0.3, b + 0.2)));
      E.guias.forEach((l) => opacar(l, prog(t, a, a + 0.4)));
      E.inicios.forEach((x) => opacar(x, prog(t, a - 0.2, a + 0.3)));
      E.fines.forEach((f, i) => { const n = numTexto(f.txt), w = n && T.valores[clave(n.v)]; const [fa, fb] = w || [b - 0.2 + 0.08 * i, b + 0.3 + 0.08 * i];
        opacar(f.t, prog(t, fa - 0.2, fa + 0.2)); contar(f.ts, f.txt, prog(t, fa, fb)); });
    } else if (plantilla === "calor") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // las celdas entran fila a fila, de izquierda a derecha; el contorno y la leyenda al final
      const nf = E.filas.length, paso = Math.min(0.2, 1.6 / Math.max(1, nf));
      E.cabecera.forEach((x) => opacar(x, prog(t, T.ini - 0.2, T.ini + 0.3)));
      E.filas.forEach((f, i) => { const a = T.ini + paso * i;
        opacar(f.nombre, prog(t, a - 0.1, a + 0.3));
        f.celdas.forEach((c, j) => { const ca = a + 0.05 * j, p = prog(t, ca, ca + 0.3); opacar(c.r, p);
          if (c.t) { const n = numTexto(c.txt), w = n && T.valores[clave(n.v)]; opacar(c.t, p); if (w) contar(c.t, c.txt, prog(t, w[0], w[1])); } }); });
      const fin = T.ini + paso * nf + 0.3;
      E.resto.forEach((el) => opacar(el, prog(t, fin, fin + 0.5)));
    } else if (plantilla === "cascada") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // cada fila crece desde donde acabó la anterior (o desde el eje), su rótulo cuenta, el conector aparece al acabar
      E.items.forEach((it, i) => {
        const n = numTexto(it.txt), [a, b] = ventanaDe(T, [n && Math.abs(n.v)], i), p = prog(t, a, b);
        it.r.setAttribute("width", p >= 1 ? it.ws : Math.max(0.01, it.w * p));
        it.r.setAttribute("x", p >= 1 ? it.xs : it.derecha ? it.x : it.x + it.w * (1 - p));
        opacar(it.nombre, prog(t, a - 0.3, a));
        if (it.t) { contar(it.t, it.txt, p); opacar(it.t, prog(t, a, a + 0.25)); }
        if (it.c) opacar(it.c, prog(t, b - 0.1, b + 0.3));
      });
    } else if (plantilla === "combinado") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // las barras crecen desde la base; después la línea se dibuja de izquierda a derecha y sus puntos aparecen
      E.barras.forEach((bar, i) => {
        const n = numTexto(bar.txt), [a, b] = ventanaDe(T, [n && n.v], i), p = prog(t, a, b), y0 = +bar.ys, h0 = +bar.hs;
        bar.r.setAttribute("height", p >= 1 ? bar.hs : Math.max(0.01, h0 * p));
        bar.r.setAttribute("y", p >= 1 ? bar.ys : y0 + h0 * (1 - p));
        if (bar.t) { contar(bar.t, bar.txt, p); opacar(bar.t, prog(t, a, a + 0.25)); }
      });
      const fb = Math.max(T.ini + 0.8, ...E.barras.map((bar, i) => { const n = numTexto(bar.txt); return ventanaDe(T, [n && n.v], i)[1]; }));
      const la = fb, lb = Math.max(la + 0.8, T.linea_fin || la + 1.5), pl = prog(t, la, lb);
      if (E.linea) { E.linea.style.strokeDasharray = pl >= 1 ? "" : E.L; E.linea.style.strokeDashoffset = pl >= 1 ? "" : E.L * (1 - pl); opacar(E.linea, prog(t, la - 0.1, la + 0.1)); }
      E.puntos.forEach((c, i) => opacar(c, prog(t, la + (lb - la) * (i / Math.max(1, E.puntos.length - 1)) - 0.05, la + (lb - la) * (i / Math.max(1, E.puntos.length - 1)) + 0.2)));
      E.rotLinea.forEach((x, i) => { const n = numTexto(x.txt), w = n && T.valores[clave(n.v)]; const a = w ? w[0] : la + (lb - la) * (i / Math.max(1, E.rotLinea.length - 1));
        opacar(x.t, prog(t, a, a + 0.3)); if (w) contar(x.t, x.txt, prog(t, w[0], w[1])); });
    } else if (plantilla === "dispersion") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // los puntos brotan escalonados; las guías y los nombres después; el destacado (el último) al final
      const n = E.puntos.length, paso = Math.min(0.05, 1.2 / Math.max(1, n));
      E.puntos.forEach((pt, i) => { const p = prog(t, T.ini + paso * i, T.ini + paso * i + 0.3); pt.c.setAttribute("r", p >= 1 ? pt.rs : Math.max(0.01, +pt.rs * p)); });
      const fin = T.ini + paso * n + 0.2;
      E.guias.forEach((g) => opacar(g, prog(t, fin, fin + 0.5)));
      E.nombres.forEach((x, i) => opacar(x, prog(t, fin + 0.1 * i, fin + 0.1 * i + 0.3)));
    } else if (plantilla === "hemiciclo") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // las curules se encienden en orden (barrido del arco); cada bloque muestra su fila al completar sus curules
      const a = T.ini, b = T.linea_fin || T.ini + 2.5, n = E.curules.length;
      E.curules.forEach((c, i) => opacar(c, prog(t, a + (b - a) * i / Math.max(1, n), a + (b - a) * i / Math.max(1, n) + 0.15)));
      opacar(E.total, prog(t, a - 0.2, a + 0.3));
      let acum = 0;
      E.bloques.forEach((bl, j) => { const cur = bl.n != null ? bl.n : Math.round(n / Math.max(1, E.bloques.length)); const t0 = a + (b - a) * acum / Math.max(1, n), t1 = a + (b - a) * (acum + cur) / Math.max(1, n); acum += cur;
        const nv = numTexto(bl.txt), w = nv && T.valores[clave(nv.v)];
        opacar(bl.m, prog(t, t0, t0 + 0.3)); opacar(bl.nombre, prog(t, t0, t0 + 0.3));
        if (bl.v) { opacar(bl.v, prog(t, t0, t0 + 0.3)); contar(bl.v, bl.txt, w ? prog(t, w[0], w[1]) : prog(t, t0, t1)); } });
      E.mayoria.forEach((el) => opacar(el, prog(t, b, b + 0.5)));
    } else if (plantilla === "linea-tiempo") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // la espina baja y cada evento aparece cuando la espina lo alcanza; su barra crece y su valor cuenta
      const a = T.ini, b = T.linea_fin || T.ini + 3, p = prog(t, a, b);
      if (E.espina) E.espina.setAttribute("y2", p >= 1 ? E.y2 : E.yTop + (+E.y2 - E.yTop) * p);
      E.eventos.forEach((ev) => { const ta = a + (b - a) * (ev.cy - E.yTop) / Math.max(1, E.yBot - E.yTop), pe = prog(t, ta, ta + 0.4);
        ev.c.setAttribute("r", pe >= 1 ? ev.rs : Math.max(0.01, +ev.rs * pe));
        ev.textos.forEach((x) => opacar(x, pe));
        const n = numTexto(ev.txt), w = n && T.valores[clave(n.v)], [va, vb] = w || [ta + 0.1, ta + 0.7], pv = prog(t, va, vb);
        if (ev.rect) ev.rect.setAttribute("width", pv >= 1 ? ev.ws : Math.max(0.01, +ev.ws * pv));
        if (ev.forma) ev.forma.setAttribute("r", pv >= 1 ? ev.frs : Math.max(0.01, +ev.frs * pv));
        if (ev.valor) { opacar(ev.valor, prog(t, va, va + 0.25)); contar(ev.valor, ev.txt, pv); } });
    } else if (plantilla === "multiples") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // panel a panel: fondo y cabecera, la línea se dibuja, el punto final aparece y el último valor cuenta
      const paso = Math.min(0.45, 2.4 / Math.max(1, E.paneles.length));
      E.paneles.forEach((pn, i) => { const a = T.ini + paso * i, pf = prog(t, a, a + 0.3);
        opacar(pn.f, pf); opacar(pn.nombre, pf); pn.otros.forEach((el) => opacar(el, pf));
        const n = numTexto(pn.txt), w = n && T.valores[clave(n.v)], [la, lb] = [a + 0.15, w ? Math.max(w[1], a + 0.6) : a + 0.7], pl = prog(t, la, lb);
        if (pn.path) { pn.path.style.strokeDasharray = pl >= 1 ? "" : pn.L; pn.path.style.strokeDashoffset = pl >= 1 ? "" : pn.L * (1 - pl); }
        opacar(pn.circ, prog(t, lb - 0.1, lb + 0.2));
        if (pn.v) { opacar(pn.v, prog(t, la, la + 0.25)); contar(pn.v, pn.txt, pl); } });
    } else if (plantilla === "pictograma") {
      // como waffle: las formas se encienden en orden mientras la cifra cuenta; texto y leyenda al final
      const n = numTexto(E.txt), [a, b] = ventanaDe(T, [D.destacado, n && n.v], 0), p = prog(t, a, b);
      const k = Math.round(E.on.length * p);
      E.on.forEach((c, i) => c.classList.toggle("on", p >= 1 || i < k));
      if (E.num) { aparecer(E.num, prog(t, a - 0.3, a), 20); contar(E.num, E.txt, p); }
      E.resto.forEach((el) => aparecer(el, prog(t, b, b + 0.5), 12));
    } else if (plantilla === "piramide") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // las barras crecen desde el eje central hacia fuera; los valores viajan con el borde y cuentan
      E.grupos.forEach((g, i) => {
        const ni = numTexto(g.vit), nd = numTexto(g.vdt), [a, b] = ventanaDe(T, [ni && ni.v, nd && nd.v], i), p = prog(t, a, b);
        const liw = +g.liw, lix = +g.lis, dew = +g.dew;
        g.li.setAttribute("width", p >= 1 ? g.liw : Math.max(0.01, liw * p)); g.li.setAttribute("x", p >= 1 ? g.lis : lix + liw * (1 - p));
        g.de.setAttribute("width", p >= 1 ? g.dew : Math.max(0.01, dew * p));
        opacar(g.nombre, prog(t, a - 0.3, a));
        if (g.vi) { g.vi.setAttribute("x", p >= 1 ? g.vix : +g.vix + liw * (1 - p)); contar(g.vi, g.vit, p); opacar(g.vi, prog(t, a, a + 0.25)); }
        if (g.vd) { g.vd.setAttribute("x", p >= 1 ? g.vdx : +g.vdx - dew * (1 - p)); contar(g.vd, g.vdt, p); opacar(g.vd, prog(t, a, a + 0.25)); }
      });
    } else if (plantilla === "mapa") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      // los departamentos aparecen uno tras otro (orden de la geometría) en 1.5 s
      const n = E.deptos.length;
      E.deptos.forEach((d, k) => (d.style.opacity = prog(t, T.ini + (1.5 * k) / n, T.ini + 0.4 + (1.5 * k) / n)));
      E.contorno.forEach((c) => (c.style.opacity = prog(t, T.ini + 1.6, T.ini + 2.0)));
      E.col.forEach((el) => { if (el.tagName !== "text") el.style.opacity = prog(t, T.ini + 1.2, T.ini + 1.7); });
      E.textos.forEach((x) => {
        const n = numTexto(x.txt), w = n && T.valores[clave(n.v)];
        const [a, b] = w || [T.ini + 1.2, T.ini + 1.7], p = prog(t, a, b);
        x.t.style.opacity = prog(t, Math.min(a, T.ini + 1.2), Math.min(a, T.ini + 1.2) + 0.5);
        if (w) contar(x.t, x.txt, p);
      });
    } else {
      // genérico: el gráfico se revela de izquierda a derecha al arrancar (en p = 1 no queda clip-path)
      const g = q("#grafico"), p = prog(t, T.ini - 0.5, T.ini + 0.1);
      if (g) { g.style.clipPath = p >= 1 ? "" : `inset(0 ${((1 - p) * 100).toFixed(2)}% 0 0)`; aparecer(g, Math.min(1, p * 2), 16); }
    }
  };

  // elementos de la tarjeta que muestran el valor con clave k (misma clave que T.valores). La voz redondea
  // («mil quinientos noventa y seis» por 1,596.2): coincide si el valor, redondeado a los decimales de k, es k
  const coincide = (v, k) => { if (v == null || Number.isNaN(Number(v))) return false;
    if (clave(v) === k) return true;
    const kv = Number(k), dec = (k.split(".")[1] || "").length;
    return !Number.isNaN(kv) && Math.abs(kv) >= 1 && Math.abs(Number(v) - kv) <= 0.5 * Math.pow(10, -dec) + 1e-9; };
  function elementos(k) {
    const D = DATA, ck = (v) => coincide(v, k);
    const num = (el) => { const n = el && numTexto(el.textContent); return !!n && coincide(n.v, k); };
    const q = (s) => document.querySelector(s), qa = (s) => [...document.querySelectorAll(s)];
    if (plantilla === "antes-despues") return E.cols.filter((c) => ck(D[c.k].valor) || num(c.num)).map((c) => c.num);
    if (plantilla === "cifra") return ck(D.cifra.valor) || num(E.num) ? [E.num] : [];
    if (plantilla === "barras-v") return E.barras.flatMap((bar, i) => (ck(D.valores[i]) || (E.vals[i] && num(E.vals[i].t))) ? [bar.r, E.vals[i] && E.vals[i].t] : []);
    if (plantilla === "barras-h") return E.barras.flatMap((bar) => (ck(bar.v) || num(bar.t)) ? [bar.r, bar.t] : []);
    if (plantilla === "waffle") return E.num && (ck(D.cifra && D.cifra.valor) || ck(D.porcentaje) || num(E.num)) ? [E.num] : [];
    if (plantilla === "dona") {
      if (num(E.v)) return [E.v];
      const it = E.items.find((x, i) => num(x.it.querySelector(".p")) || ck((D.partes[i] || {}).valor));
      return it ? [it.it] : [];
    }
    if (plantilla === "pesas" || plantilla === "pendiente") {
      return E.items.flatMap((it) => (ck(it.b) || num(it.lb)) ? [it.nombre, it.cb, it.lb] : (ck(it.a) || num(it.la)) ? [it.nombre, it.ca, it.la] : []);
    }
    if (plantilla === "divergente" || plantilla === "embudo") return E.items.flatMap((it) => (ck(it.v) || num(it.t)) ? [it.r, it.t] : []);
    if (plantilla === "bullet") return E.items.flatMap((it) => (ck(it.v) || num(it.t)) ? [it.barra, it.t] : []);
    if (plantilla === "agrupadas") return E.barras.flatMap((b) => (ck(b.v) || num(b.t)) ? [b.r, b.t] : []);
    if (plantilla === "apilada") {
      const tot = E.totales.find((x) => num(x.t));
      if (tot) return [tot.t];
      const ro = E.rotulos.find((x) => num(x.t));
      return ro ? [ro.t] : [];
    }
    if (plantilla === "treemap") {
      const parte = (D.partes || []).find((p) => ck(p.valor));
      const te = E.teselas.find((te) => te.textos.some((x) => num(x.t) || (parte && (x.txt === parte.nombre || parte.nombre.startsWith(x.txt + " ")))));
      return te ? [te.r, ...te.textos.map((x) => x.t)] : [];
    }
    if (plantilla === "area-apilada") { const f = E.fines.find((x) => { const n = numTexto(x.txt); return !!n && coincide(n.v, k); }); return f ? [f.t] : []; }
    if (plantilla === "calor") { for (const f of E.filas) { const c = f.celdas.find((c_) => c_.t && num(c_.t)); if (c) return [c.r, c.t]; } return []; }
    if (plantilla === "cascada") return E.items.flatMap((it) => (it.t && num(it.t)) ? [it.nombre, it.r, it.t] : []);
    if (plantilla === "combinado") {
      const bar = E.barras.find((b) => b.t && num(b.t)); if (bar) return [bar.r, bar.t];
      const ro = E.rotLinea.find((x) => num(x.t)); return ro ? [ro.t] : [];
    }
    if (plantilla === "hemiciclo") return E.bloques.flatMap((bl) => (bl.v && num(bl.v)) ? [bl.m, bl.nombre, bl.v] : []);
    if (plantilla === "linea-tiempo") return E.eventos.flatMap((ev) => (ev.valor && num(ev.valor)) ? [ev.c, ...ev.textos, ev.valor] : []);
    if (plantilla === "multiples") return E.paneles.flatMap((pn) => (pn.v && num(pn.v)) ? [pn.nombre, pn.v, pn.circ] : []);
    if (plantilla === "pictograma") return E.num && (ck(D.destacado) || num(E.num)) ? [E.num] : [];
    if (plantilla === "piramide") return E.grupos.flatMap((g) => ((g.vi && num(g.vi)) || (g.vd && num(g.vd))) ? [g.nombre, g.li, g.de, g.vi, g.vd] : []);
    if (plantilla === "mapa") {
      const hit = E.textos.find((x) => num(x.t));
      if (!hit) return [];
      // el destacado: su contorno en el mapa + su fila de la columna (departamento y rótulo a la vez; si el
      // departamento queda lejos de la columna la unión pasa de 0.7×1080 y escena.html deja solo los textos)
      if (E.dest && E.dest.textos.includes(hit.t)) return [...E.contorno, E.dest.rect, ...E.dest.textos];
      // otra fila de la columna (Mayor / Menor): sus textos y su casilla, a la misma altura
      const y = +hit.t.getAttribute("y");
      return E.col.filter((el) => (el.tagName === "text" && Math.abs(+el.getAttribute("y") - y) <= 14) ||
        (el.tagName === "rect" && Math.abs(+el.getAttribute("y") + +el.getAttribute("height") / 2 + 8 - y) <= 14));
    }
    if (plantilla === "linea") {
      const t = qa("#grafico svg text.t-val").find((x) => num(x));
      if (!t) return [];
      const r = t.getBoundingClientRect(), cy = r.top + r.height / 2;
      const c = E.puntos.slice().sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return Math.abs(ra.top + ra.height / 2 - cy) - Math.abs(rb.top + rb.height / 2 - cy); })[0];
      return c ? [t, c] : [t];
    }
    // genérico: hojas de #grafico (sin ejes) cuyo número coincide; la unión solo si cabe en 300 px
    const g = q("#grafico");
    if (!g) return [];
    const hojas = [...g.querySelectorAll("text, span, div, tspan")].filter((el) => !el.children.length && !el.classList.contains("t-eje") && num(el));
    if (!hojas.length) return [];
    const rs = hojas.map((el) => el.getBoundingClientRect());
    const w = Math.max(...rs.map((r) => r.right)) - Math.min(...rs.map((r) => r.left));
    const h = Math.max(...rs.map((r) => r.bottom)) - Math.min(...rs.map((r) => r.top));
    return hojas.length === 1 || (w <= 300 && h <= 300) ? hojas : [];
  }

  // caja de un elemento: en HTML, la de su texto (un div de ancho completo no cuenta); en SVG, la del elemento
  const rectDe = (el) => {
    if (el.ownerSVGElement) return el.getBoundingClientRect();
    const r = document.createRange(); r.selectNodeContents(el);
    const b = r.getBoundingClientRect();
    return b.width > 0 && b.height > 0 ? b : el.getBoundingClientRect();
  };
  const union = (els) => {
    const rs = els.map(rectDe).filter((r) => r.width > 0 && r.height > 0);
    if (!rs.length) return null;
    const x0 = Math.min(...rs.map((r) => r.left)), y0 = Math.min(...rs.map((r) => r.top));
    const x1 = Math.max(...rs.map((r) => r.right)), y1 = Math.max(...rs.map((r) => r.bottom));
    return [Math.round(x0 * 10) / 10, Math.round(y0 * 10) / 10, Math.round((x1 - x0) * 10) / 10, Math.round((y1 - y0) * 10) / 10];
  };
  window.__caja = (k) => {
    try {
      if (!E) leer();
      const els = elementos(String(k)).filter(Boolean);
      if (!els.length) return null;
      let c = union(els);
      // si la unión (p. ej. barra + rótulo) es demasiado grande para un foco, se queda solo con los textos
      if (c && (c[2] > 0.7 * 1080 || c[3] > 0.7 * 1080)) {
        const textos = els.filter((el) => el.tagName === "text" || el.tagName === "tspan" || (!el.ownerSVGElement && !el.children.length));
        if (textos.length && textos.length < els.length) c = union(textos) || c;
      }
      return c;
    } catch (e) {
      return null;
    }
  };
})();
