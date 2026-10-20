// Animación de tarjetas para /video: estado = f(t), sin transiciones CSS.
// Se inyecta al final de una copia de tuit_N.html. Lee el estado final del DOM ya renderizado y, en p = 1,
// restaura exactamente los atributos/textos originales (las cifras nunca se redondean distinto).
// T = { tit, ini, nota, valores: { "8402.4": [desde, hasta], ... }, linea_fin }  (segundos de la escena)
// Plantillas con animador propio: antes-despues, cifra, barras-v, linea, barras-h, waffle, dona, pesas,
// mapa, pendiente. Cualquier otra (o una tarjeta sin plantilla): el gráfico se revela con un barrido en T.ini.
// window.__caja(clave) → [x, y, w, h] en px de la tarjeta del elemento que muestra ese valor (para el foco de
// escena.html), o null si la plantilla no lo sabe; nunca lanza.
(() => {
  const clamp = (x) => Math.max(0, Math.min(1, x));
  const eo = (x) => 1 - Math.pow(1 - clamp(x), 3);
  const prog = (t, a, b) => (t >= b ? 1 : eo((t - a) / Math.max(0.001, b - a)));
  const aparecer = (el, p, dy = 24) => { if (!el) return; el.style.opacity = p; el.style.transform = `translateY(${(1 - p) * dy}px)`; };
  const clave = (v) => String(Number(v));
  const plantilla = (document.documentElement.innerHTML.match(/plantilla: ([\w-]+) ·/) || [])[1];
  let E = null;  // estado final leído una sola vez

  // ventana de animación de un valor: la de la voz si se menciona; si no, al arrancar el gráfico
  const ventana = (T, v, i) => T.valores[clave(v)] || [T.ini + 0.25 * i, T.ini + 1.2 + 0.25 * i];
  // como ventana(), pero prueba varias claves (valor crudo de DATA y el número que se ve en la tarjeta)
  const ventanaDe = (T, vs, i) => { for (const v of vs) if (v != null && T.valores[clave(v)]) return T.valores[clave(v)]; return ventana(T, NaN, i); };

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
    } else if (plantilla === "linea") {
      E.lineas = qa("#grafico svg path").filter((p) => p.getAttribute("fill") === "none")
        .map((p) => ({ p, L: p.getTotalLength() }));
      E.puntos = qa("#grafico svg circle");
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
    } else if (plantilla === "mapa") {
      const g = E.svg.querySelector(":scope > g");
      E.deptos = [...g.querySelectorAll("path")].filter((p) => p.getAttribute("fill") !== "none");
      E.contorno = [...g.querySelectorAll("path")].filter((p) => p.getAttribute("fill") === "none");
      // columna derecha (leyenda, extremos): todo lo que no es el grupo del mapa ni <defs>
      E.col = [...E.svg.children].filter((el) => el !== g && el.tagName !== "defs");
      E.textos = E.col.filter((el) => el.tagName === "text").map((t) => ({ t, txt: t.textContent }));
    }
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
    } else if (plantilla === "linea") {
      aparecer(E.svg, prog(t, T.ini - 0.5, T.ini), 0);
      const a = T.ini, b = T.linea_fin || T.ini + 4, p = prog(t, a, b);
      E.lineas.forEach((l) => {
        l.p.style.strokeDasharray = p >= 1 ? "" : l.L;
        l.p.style.strokeDashoffset = p >= 1 ? "" : l.L * (1 - p);
      });
      E.puntos.forEach((c) => (c.style.opacity = prog(t, b - 0.2, b + 0.3)));
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
      return E.items.flatMap((it) => (ck(it.b) || num(it.lb)) ? [it.cb, it.lb] : (ck(it.a) || num(it.la)) ? [it.ca, it.la] : []);
    }
    if (plantilla === "mapa") return E.textos.some((x) => num(x.t)) ? E.col : [];  // la columna derecha entera
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
