#!/usr/bin/env python3
"""Registra un hilo terminado en memoria/ (lo usa el productor al cerrar) y consulta series.

--registrar <sesion> --ruta <ruta relativa> [--estado listo|incompleto] [--hook <hook_tipo>] [--dry-run]
  Lee <sesion>/guion.json (slug, fecha, paleta, hook_tipo, sintesis.tesis, tuits),
  encuadre.json (tema), <ruta>/datos.json y <sesion>/hallazgos_*.json.
  Añade o actualiza en memoria/hilos.json → hilos[]
    {id: "<fecha>-<slug>", fecha, slug, tema, tesis, paleta, n_tuits, ruta, estado, hook_tipo, modo}
  (hook_tipo: el nombre del gancho de guion.json; --hook lo sobrescribe y debe ser uno
  de los ocho nombres de ensamblar.HOOKS; modo: guion.modo, hilo | explica | perfil). En memoria/fuentes.json:
  · series[]  ← cifras de datos.json con tipo "serie" y n_puntos ≥ 5 (dedup por url +
    nombre): nombre=concepto, fuente, url, formato (por la extensión de la url; "html" si
    no se sabe), unidad, desde, hasta, frecuencia inferida, nota.
  · fuentes[] ← fuentes con nivel "primaria" de hallazgos_*.json que no existan aún
    (dedup por dominio y por nombre/alias): categoria "auto", rating 8, temas del eje y
    del tema, nota "hallada en <id>: <url>".
  · ideas     ← si encuadre.json trae idea_id, el registro lo guarda y la idea de
    ideas/banco.json pasa a «hecha» (estado listo) o «en_curso» (incompleto) vía
    scripts/ideas.py. En sesiones smoke/fixture la idea no se toca.
  · nota      ← cada vacío de hallazgos_*.json que mencione el alias de una fuente
    conocida se anexa a su nota como "· [<fecha>] <vacío>" (sin duplicar).
  Rechaza rutas absolutas (exit 2). --dry-run imprime sin escribir.

  Modo DATO (guion.tipo == "dato", lo produce /dato): el registro va a memoria/datos.json → datos[]
    {id: "<fecha>-<slug>", fecha, slug, tema, pista, dato, cifra_id, valor_final, unidad, fuente,
     plantilla, paleta, hook_tipo, modo (dato | vs | mapa | antes), ruta, estado}
    (dato = titular en una línea; cifra_id = la cifra de la tarjeta; fuente = la del pie), leídos de
    <ruta>/dato.json y <ruta>/datos.json. Series y fuentes van a memoria/fuentes.json igual que en un
    hilo. El banco de ideas NO se toca (/dato no usa ideas).

  Modo INVESTIGACIÓN (guion.modo == "investigacion", lo produce /investigacion): el hilo se registra igual en
    memoria/hilos.json (modo investigacion, ruta investigacion/<fecha>-<slug>/hilo) y, con --informe <dir>, el
    informe va a memoria/informes.json → informes[]
    {id: "<fecha>-<slug>", fecha, slug, tema, tesis, paleta, numero, n_paginas, n_figuras, ruta_informe,
     ruta_hilo, hilo_id, estado, modo (investigacion | desde)}
    (numero = informe.json meta.numero; fecha y slug, del nombre de la carpeta <fecha>-<slug>; hilo_id, el id del
    hilo en hilos.json). --solo-informe registra solo el informe sobre un hilo YA registrado (flujo desde:<slug>):
    el hilo no se toca ni se funden series. Un numero ya usado por otro informe es error.

--video <hilos/<fecha>-<slug>/video> [--estado listo|incompleto] [--dry-run]
  Registra el video de /video (lee el guion.json de entrega que escribe scripts/video.py entregar) en
  memoria/videos.json → videos[] {id, fecha, slug, hilo_id, tema, paleta, duracion, duracion_s, n_escenas,
  musica, creditos_voz, ruta_video, ruta_hilo, estado, frases {promesa, gancho, aperturas[], pregunta}}; un id
  repetido se actualiza (conserva su fecha). video.py lo lee para rotar
  la música de cada paleta.

--series "tema"   mismo filtro que scripts/fuentes.py --series
--informes ["tema"] lista los informes registrados (del más reciente al más antiguo; con tema, filtrados) y
                  termina con «siguiente N.º NN» (lo usa /investigacion para numerar)
--datos ["tema"]  lista los datos registrados en memoria/datos.json, del más reciente al más antiguo
                  (con tema, filtrados por palabras clave); lo consulta el investigador de /dato para
                  no repetir un dato y para hook_evitar (el hook_tipo del primero de la lista).

Salida: 0 ok · 1 error · 2 uso incorrecto
"""
import argparse
import glob
import json
import os
import re
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import fuentes as _fuentes  # noqa: E402
import ideas as _ideas  # noqa: E402  (único escritor de ideas/banco.json)
from ensamblar import HOOKS  # noqa: E402  (los ocho nombres de gancho: una sola lista)

HILOS = os.path.join(RAIZ, "memoria", "hilos.json")
DATOS = os.path.join(RAIZ, "memoria", "datos.json")
INFORMES = os.path.join(RAIZ, "memoria", "informes.json")
VACIO_INFORMES = {
    "version": 1,
    "_comentario": "Registro de informes de investigación (PDF) producidos por /investigacion. Lo escribe SOLO scripts/memoria.py (--registrar … --informe) desde el productor; `python3 scripts/memoria.py --informes` lista y da el siguiente N.º. estado: borrador | listo | publicado | incompleto · modo: investigacion (flujo completo) | desde (informe sobre un hilo previo).",
    "informes": [],
}
VIDEOS = os.path.join(RAIZ, "memoria", "videos.json")
VACIO_VIDEOS = {
    "version": 1,
    "_comentario": "Registro de videos verticales producidos por /video a partir de un hilo entregado. Lo escribe SOLO scripts/memoria.py --video <hilos/<fecha>-<slug>/video>; scripts/video.py lo lee para rotar la música de cada paleta. estado: listo | publicado | incompleto · duracion: corto | medio | largo.",
    "videos": [],
}
FUENTES = os.path.join(RAIZ, "memoria", "fuentes.json")
VACIO_DATOS = {
    "version": 1,
    "_comentario": "Registro de datos sueltos (una tarjeta) producidos por /dato. Lo escribe SOLO scripts/memoria.py desde el productor; el investigador consulta con `python3 scripts/memoria.py --datos \"tema\"` para no repetir un dato ni el último gancho. estado: borrador | listo | publicado | incompleto.",
    "datos": [],
}
MESES = "ene|feb|mar|abr|may|jun|jul|ago|sep|set|oct|nov|dic|jan|apr|aug|dec"
RE_MES = re.compile(r"^(\d{4}-\d{2}(-\d{2})?|(%s)[a-z]*\.?[\s/-]*\d{2,4}|\d{1,2}/\d{4}|(%s)[a-z]*)$" % (MESES, MESES), re.I)
RE_ANIO = re.compile(r"^\d{4}$")
RE_TRIM = re.compile(r"^(\d{4}[-\s]?[TQ][1-4]|[TQ][1-4][-\s]?\d{4}|[1-4]T[-\s]?\d{4})$", re.I)


def leer(ruta, obligatorio=True):
    if not os.path.exists(ruta):
        if obligatorio:
            raise SystemExit("ERROR: falta %s" % os.path.relpath(ruta, RAIZ))
        return None
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def punto_p(pt):
    """Etiqueta temporal de un punto de serie: el contrato es {p, v}, pero se tolera {periodo|anio|fecha, valor}."""
    for k in ("p", "periodo", "anio", "fecha"):
        if pt.get(k) is not None:
            return pt[k]
    return None


def frecuencia_de(serie):
    ps = [str(punto_p(p) or "").strip() for p in serie]
    if not ps:
        return "otra"
    if all(RE_ANIO.match(p) for p in ps):
        return "anual"
    if all(RE_TRIM.match(p) for p in ps):
        return "trimestral"
    if all(RE_MES.match(p) for p in ps):
        return "mensual"
    return "otra"


def formato_de(url):
    ext = os.path.splitext((url or "").split("?")[0].split("#")[0])[1].lower().lstrip(".")
    if ext in ("xlsx", "xls", "csv", "pdf", "json"):
        return ext
    if "format=json" in (url or "").lower() or "/api/" in (url or "").lower():
        return "api"
    return "html"


def series_de(datos, hilo_id, origen="hilo"):
    out = []
    for c in datos.get("cifras", []):
        if c.get("tipo") != "serie":
            continue
        serie = c.get("serie") or []
        n = c.get("n_puntos") or len(serie)
        if n < 5 or not serie:
            continue
        out.append({
            "nombre": c.get("concepto"), "fuente": c.get("fuente"), "url": c.get("url") or "",
            "formato": formato_de(c.get("url")), "unidad": c.get("unidad") or "",
            "desde": str(punto_p(serie[0])), "hasta": str(punto_p(serie[-1])),
            "frecuencia": frecuencia_de(serie), "nota": "registrada desde %s %s" % (origen, hilo_id),
        })
    return out


def dominio_de(url):
    u = re.sub(r"^https?://", "", str(url or "").strip(), flags=re.I)
    u = u.split("/")[0].split("?")[0].lower()
    return u[4:] if u.startswith("www.") else u


def hallazgos_de(sesion):
    """(fuentes primarias, vacíos) de todos los <sesion>/hallazgos_*.json."""
    primarias, vacios = [], []
    for ruta in sorted(glob.glob(os.path.join(sesion, "hallazgos_*.json"))):
        try:
            h = leer(ruta)
        except (SystemExit, ValueError):
            continue
        eje = h.get("eje") or re.sub(r"^hallazgos_|\.json$", "", os.path.basename(ruta))
        for f in h.get("fuentes") or []:
            if str(f.get("nivel") or "").strip().lower() == "primaria" and f.get("url") and f.get("nombre"):
                primarias.append({"nombre": str(f["nombre"]).strip(), "url": str(f["url"]).strip(), "eje": eje})
        vacios += [v.strip() for v in (h.get("vacios") or []) if isinstance(v, str) and v.strip()]
    return primarias, vacios


def fusionar_fuentes(mf, primarias, vacios, tema, hid, fecha):
    """Añade fuentes primarias nuevas y anexa a la nota de una fuente conocida los vacíos que la mencionan."""
    fuentes = mf.setdefault("fuentes", [])
    por_dominio = {dominio_de(f.get("url")): f for f in fuentes if dominio_de(f.get("url"))}
    por_nombre = {}
    for f in fuentes:
        for n in [f.get("nombre")] + list(f.get("alias") or []):
            n = _fuentes.normalizar(n)
            # varias fuentes comparten alias (INSIVUMEH, INE…): gana la de mayor rating y, en empate, la primera del catálogo
            if n and (n not in por_nombre or (f.get("rating") or 0) > (por_nombre[n].get("rating") or 0)):
                por_nombre[n] = f
    temas_hilo = [w for w in re.findall(r"[a-z0-9]+", _fuentes.normalizar(tema)) if len(w) >= 4 and not w.isdigit()]
    nuevas = []
    for p in primarias:
        dom = dominio_de(p["url"])
        if not dom or dom in por_dominio or _fuentes.normalizar(p["nombre"]) in por_nombre:
            continue
        f = {"nombre": p["nombre"], "url": dom, "categoria": "auto", "rating": 8, "alias": [],
             "temas": sorted(set([p["eje"]] + temas_hilo)), "nota": "hallada en %s: %s" % (hid, p["url"])}
        fuentes.append(f); nuevas.append(f)
        por_dominio[dom] = f; por_nombre[_fuentes.normalizar(p["nombre"])] = f
    notas, por_fuente = [], {}
    for v in vacios:
        t = _fuentes.normalizar(v)
        # el alias más largo que aparezca como palabra entera (evita que «INE» pesque dentro de otra palabra)
        hits = [(n, f) for n, f in por_nombre.items() if len(n) >= 3 and re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(n), t)]
        if not hits:
            continue
        n, f = max(hits, key=lambda x: len(x[0]))
        cuerpo = re.sub(r"\s+", " ", v)[:200]
        nota = (f.get("nota") or "").strip()
        if cuerpo in nota or por_fuente.get(f["nombre"], 0) >= 3:  # ya anexado, o ya van 3 notas de esta corrida
            continue
        f["nota"] = (nota + " · " if nota else "") + "[%s] %s" % (fecha, cuerpo)
        por_fuente[f["nombre"]] = por_fuente.get(f["nombre"], 0) + 1
        notas.append((f["nombre"], cuerpo))
    return nuevas, notas


def registro_dato(a, ruta_abs, guion, encuadre, datos, hid, fecha, slug, hook):
    """Registro para memoria/datos.json a partir de <ruta>/dato.json y <ruta>/datos.json (None si algo falta)."""
    n = len(guion.get("tuits", []))
    if n != 1:
        print("ERROR: un dato tiene exactamente 1 tuit (el guion trae %d)" % n, file=sys.stderr)
        return None
    dj = leer(os.path.join(ruta_abs, "dato.json"))
    tu = dj.get("tuit") or {}
    cid = dj.get("cifra_id") or (tu.get("cifra_ids") or [None])[0]  # la cifra héroe (ensamblar la resuelve)
    cf = next((c for c in datos.get("cifras", []) if c.get("id") == cid), None)
    if not cid or cf is None:
        print("ERROR: dato.json no trae cifra_ids o la cifra %r no está en datos.json" % cid, file=sys.stderr)
        return None
    visual = guion["tuits"][0].get("visual") or {}
    return {
        "id": hid, "fecha": fecha, "slug": slug,
        "tema": encuadre.get("tema") or guion.get("tema") or dj.get("tema") or slug,
        "pista": encuadre.get("pista") or dj.get("pista") or None,
        "dato": dj.get("dato") or " ".join(l.strip() for l in (visual.get("titular") or [])),
        "cifra_id": cid, "valor_final": cf.get("valor"), "unidad": cf.get("unidad") or "",
        "fuente": tu.get("fuente") or cf.get("fuente") or "",
        "plantilla": tu.get("plantilla") or visual.get("plantilla_final") or visual.get("plantilla"),
        "paleta": guion.get("paleta"), "hook_tipo": hook,
        "modo": guion.get("modo") or encuadre.get("modo") or dj.get("modo") or "dato",
        "ruta": os.path.normpath(a.ruta), "estado": a.estado,
    }


def registro_informe(a, guion, hid_hilo, slug, tema, tesis):
    """Registro para memoria/informes.json a partir de <informe>/informe.json (None si algo falta)."""
    import informe as _informe  # noqa: E402  (figuras_de_pagina; se importa aquí para no cargar Playwright/tokens en cada uso)
    d = os.path.join(RAIZ, a.informe)
    ruta = os.path.join(d, "informe.json")
    if not os.path.exists(ruta):
        print("ERROR: --informe %s no tiene informe.json" % a.informe, file=sys.stderr)
        return None
    R = leer(ruta)
    meta = R.get("meta") or {}
    numero = str(meta.get("numero") or "").strip()
    if not numero:
        m = re.search(r"N\.º\s*(\d+)", "%s %s" % (meta.get("numero_largo") or "", meta.get("pie") or ""))
        numero = m.group(1) if m else ""
    if not re.fullmatch(r"\d{2,}", numero):
        print("ERROR: informe.json sin meta.numero (dos dígitos) ni «N.º NN» en numero_largo/pie", file=sys.stderr)
        return None
    nombre = os.path.basename(os.path.normpath(a.informe))
    m = re.match(r"(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)$", nombre)
    fecha_inf, slug_inf = (m.group(1), m.group(2)) if m else (guion.get("fecha") or "", slug)
    paginas = list(R.get("paginas") or [])
    _informe.continuar_indice(paginas)  # hojas «Figuras y tablas» que informe.py inserta tras el índice
    n_fig = sum(1 for P in paginas for k, _ in _informe.figuras_de_pagina(P) if k == "figura")
    if not os.path.exists(os.path.join(d, "salida", "informe.pdf")):
        print("AVISO: %s/salida/informe.pdf no existe todavía (corre scripts/informe.py %s --check)" % (a.informe, a.informe), file=sys.stderr)
    return {
        "id": "%s-%s" % (fecha_inf, slug_inf), "fecha": fecha_inf, "slug": slug_inf, "tema": tema, "tesis": tesis,
        "paleta": meta.get("paleta") or guion.get("paleta"), "numero": numero, "n_paginas": len(paginas), "n_figuras": n_fig,
        "ruta_informe": os.path.normpath(a.informe), "ruta_hilo": os.path.normpath(a.ruta), "hilo_id": hid_hilo,
        "estado": a.estado, "modo": "desde" if a.solo_informe else "investigacion",
    }


def registrar(a):
    if os.path.isabs(a.ruta) or (a.informe and os.path.isabs(a.informe)):
        print("ERROR: --ruta debe ser relativa a la raíz del repo (p. ej. hilos/2026-09-28-remesas o datos/2026-09-28-remesas)", file=sys.stderr)
        return 2
    sesion = os.path.abspath(a.registrar)
    ruta_abs = os.path.join(RAIZ, a.ruta)
    guion = leer(os.path.join(sesion, "guion.json"))
    encuadre = leer(os.path.join(sesion, "encuadre.json"), obligatorio=False) or {}
    datos = leer(os.path.join(ruta_abs, "datos.json"))
    slug = guion.get("slug") or encuadre.get("slug") or os.path.basename(os.path.normpath(sesion))
    fecha = guion.get("fecha") or encuadre.get("fecha") or ""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        print("ERROR: fecha %r del guion no es YYYY-MM-DD" % fecha, file=sys.stderr)
        return 1
    hook = a.hook or guion.get("hook_tipo")
    if hook and hook not in HOOKS:
        print("ERROR: hook_tipo %r del guion no está en %s" % (hook, ", ".join(HOOKS)), file=sys.stderr)
        return 1
    hid = "%s-%s" % (fecha, slug)
    modo_dato = (guion.get("tipo") or encuadre.get("tipo")) == "dato"
    smoke = bool(guion.get("smoke") or encuadre.get("smoke") or encuadre.get("fixture"))
    idea_id = encuadre.get("idea_id")
    if modo_dato:
        reg = registro_dato(a, ruta_abs, guion, encuadre, datos, hid, fecha, slug, hook)
        if reg is None:
            return 1
        archivo, clave, etiqueta = DATOS, "datos", "dato"
        mh = leer(archivo, obligatorio=False) or json.loads(json.dumps(VACIO_DATOS))
    else:
        reg = {
            "id": hid, "fecha": fecha, "slug": slug,
            "tema": encuadre.get("tema") or guion.get("tema") or datos.get("tema") or slug,
            "tesis": (guion.get("sintesis") or {}).get("tesis") or guion.get("tesis") or "",
            "paleta": guion.get("paleta"), "n_tuits": len(guion.get("tuits", [])),
            "ruta": os.path.normpath(a.ruta), "estado": a.estado, "hook_tipo": hook,
            "modo": guion.get("modo") or encuadre.get("modo") or "hilo",
        }
        if idea_id:
            reg["idea_id"] = idea_id
        if isinstance(guion.get("perfil"), dict) and guion["perfil"].get("sujeto"):
            reg["sujeto"] = guion["perfil"]["sujeto"]
        archivo, clave, etiqueta = HILOS, "hilos", "hilo"
        mh = leer(archivo)
    if smoke:
        print("AVISO: la sesión es smoke; en smoke el productor NO escribe memoria/ (usa --dry-run o confirma que quieres registrarla).", file=sys.stderr)

    # Informe (modo investigacion): memoria/informes.json; con --solo-informe el hilo debe estar ya registrado.
    reg_inf, mi = None, None
    if a.informe:
        if modo_dato:
            print("ERROR: --informe solo aplica a un hilo (modo investigacion), no a un dato", file=sys.stderr)
            return 2
        hid_hilo = hid
        if a.solo_informe:
            prev = next((h for h in (leer(HILOS).get("hilos") or []) if os.path.normpath(str(h.get("ruta") or "")) == os.path.normpath(a.ruta)), None)
            if not prev:
                print("ERROR: --solo-informe exige que el hilo %s ya esté en memoria/hilos.json" % a.ruta, file=sys.stderr)
                return 1
            hid_hilo = prev["id"]
        reg_inf = registro_informe(a, guion, hid_hilo, slug, reg["tema"], reg["tesis"])
        if reg_inf is None:
            return 1
        mi = leer(INFORMES, obligatorio=False) or json.loads(json.dumps(VACIO_INFORMES))
        choque = next((x for x in mi.get("informes", []) if str(x.get("numero")) == reg_inf["numero"] and x.get("id") != reg_inf["id"]), None)
        if choque:
            print("ERROR: el N.º %s ya es del informe %s; corre `memoria.py --informes` para ver el siguiente número" % (reg_inf["numero"], choque["id"]), file=sys.stderr)
            return 1

    items = mh.setdefault(clave, [])
    idx = next((i for i, h in enumerate(items) if h.get("id") == hid), None)
    accion = "actualizado" if idx is not None else "añadido"
    if a.solo_informe:
        accion = "ya registrado (--solo-informe no lo toca)"
    elif idx is not None:
        items[idx].update(reg)
    else:
        items.append(reg)

    mf = leer(FUENTES)
    series = mf.setdefault("series", [])
    # Dedup por url + nombre normalizado: un mismo xlsx (Banguat) trae varias series distintas.
    clave_serie = lambda s: (str(s.get("url") or "").strip().lower(), _fuentes.normalizar(s.get("nombre")))
    vistas = {clave_serie(s) for s in series}
    nuevas, repetidas = [], []
    for s in ([] if a.solo_informe else series_de(datos, hid, etiqueta)):
        if clave_serie(s) in vistas:
            repetidas.append(s["nombre"])
            continue
        vistas.add(clave_serie(s))
        series.append(s); nuevas.append(s)
    primarias, vacios = hallazgos_de(sesion) if not a.solo_informe else ([], [])
    fuentes_nuevas, notas = fusionar_fuentes(mf, primarias, vacios, reg["tema"], hid, fecha)
    if reg_inf:
        inf_items = mi.setdefault("informes", [])
        j = next((i for i, x in enumerate(inf_items) if x.get("id") == reg_inf["id"]), None)
        if j is not None:
            inf_items[j].update(reg_inf)
        else:
            inf_items.append(reg_inf)
        print("%sinforme %s → memoria/informes.json (%s, N.º %s, %d páginas, %d figuras, paleta %s, estado %s, modo %s, hilo %s)" % (
            "[dry-run] " if a.dry_run else "", reg_inf["id"], "actualizado" if j is not None else "añadido", reg_inf["numero"], reg_inf["n_paginas"],
            reg_inf["n_figuras"], reg_inf["paleta"], reg_inf["estado"], reg_inf["modo"], reg_inf["hilo_id"]))

    if modo_dato:
        print("%sdato %s → memoria/datos.json (%s, cifra %s = %s %s · %s, plantilla %s, paleta %s, estado %s%s%s)" % (
            "[dry-run] " if a.dry_run else "", hid, accion, reg["cifra_id"], reg["valor_final"], reg["unidad"], (reg["fuente"] or "")[:40],
            reg["plantilla"], reg["paleta"], reg["estado"], (", hook " + hook) if hook else "", (", modo " + reg["modo"]) if reg["modo"] != "dato" else ""))
        print("  tema: %s" % reg["tema"])
        if reg.get("pista"):
            print("  pista: %s" % reg["pista"])
        print("  dato: %s" % reg["dato"])
    else:
        print("%s hilo %s → memoria/hilos.json (%s, %d tuits, paleta %s, estado %s%s%s)" % (
            "[dry-run] " if a.dry_run else "", hid, accion, reg["n_tuits"], reg["paleta"], reg["estado"], (", hook " + hook) if hook else "", (", modo " + reg["modo"]) if reg["modo"] != "hilo" else ""))
        print("  tema: %s" % reg["tema"])
        print("  tesis: %s" % reg["tesis"][:160])
    for s in nuevas:
        print("  + serie: %s · %s · %s · %s · %s–%s · %s" % (s["nombre"], s["fuente"][:40], s["formato"], s["unidad"], s["desde"], s["hasta"], s["frecuencia"]))
    for n in repetidas:
        print("  = serie ya registrada (misma url y nombre): %s" % n)
    if not nuevas and not repetidas:
        print("  (sin series de ≥ 5 puntos en datos.json)")
    for f in fuentes_nuevas:
        print("  + fuente: %s · %s · temas %s" % (f["nombre"], f["url"], ", ".join(f["temas"])))
    for nombre, cuerpo in notas:
        print("  ~ nota en %s: %s" % (nombre, cuerpo[:120]))
    if primarias and not fuentes_nuevas:
        print("  (las %d fuentes primarias de los hallazgos ya estaban en memoria/fuentes.json)" % len(primarias))
    if idea_id and modo_dato:
        print("  (idea %s ignorada: /dato no usa el banco de ideas)" % idea_id)
    elif idea_id and smoke:
        print("  (idea %s: sesión smoke/fixture, el banco de ideas no se toca)" % idea_id)
    marcar_idea = bool(idea_id) and not smoke and not modo_dato and not a.solo_informe
    if a.dry_run:
        if marcar_idea:
            print("  idea %s → %s (hilo %s)" % (idea_id, "hecha" if a.estado == "listo" else "en_curso", hid))
        print("[dry-run] no se escribió nada")
        return 0
    if not a.solo_informe:
        escribir(archivo, mh)
    escribir(FUENTES, mf)
    if reg_inf:
        escribir(INFORMES, mi)
        print("escrito memoria/informes.json (%d informes)" % len(mi["informes"]))
    print("escrito memoria/%s.json (%d %s) y memoria/fuentes.json (%d series, %d nuevas; %d fuentes nuevas, %d notas)" % (
        clave, len(items), clave, len(series), len(nuevas), len(fuentes_nuevas), len(notas)))
    if marcar_idea:
        msg, rc = _ideas.marcar_idea(idea_id, "hecha" if a.estado == "listo" else "en_curso", hid, fecha)
        print(("AVISO: " if rc else "  ") + msg, file=sys.stderr if rc else sys.stdout)
    return 0


def listar_datos(tema, maximo):
    """--datos [TEMA]: una línea por dato registrado, del más reciente al más antiguo (con tema, filtrados por palabras clave)."""
    items = list((leer(DATOS, obligatorio=False) or VACIO_DATOS).get("datos", []))
    # Del más reciente al más antiguo: por fecha y, a igual fecha, el registrado más tarde primero (el último del archivo).
    items = [d for _, d in sorted(enumerate(items), key=lambda x: (str(x[1].get("fecha") or ""), x[0]), reverse=True)]
    claves = _fuentes.palabras_clave(tema) if tema else []
    if claves:
        pts = [(_fuentes.puntuar(claves, [(d.get("tema"), 3), (d.get("dato"), 3), (d.get("slug"), 2), (d.get("pista"), 1), (d.get("fuente"), 1), (d.get("modo"), 1)]), d) for d in items]
        items = [d for p, d in sorted(pts, key=lambda x: -x[0]) if p]  # estable: a igual puntaje, el más reciente primero
    print("datos registrados: %d%s" % (len(items), (" · tema: %s · claves: %s" % (tema, ", ".join(claves))) if claves else ""))
    for d in items[:maximo]:
        print("  %s · %s%s · %s %s · %s · hook %s · %s · %s" % (
            d.get("id"), ("[%s] " % d["modo"]) if d.get("modo") and d["modo"] != "dato" else "", d.get("dato"), d.get("valor_final"), d.get("unidad") or "", (d.get("fuente") or "")[:40],
            d.get("hook_tipo") or "—", d.get("estado"), d.get("ruta")))
    if not items:
        print("  (ninguno)")
    return 0


def listar_informes(tema, maximo):
    """--informes [TEMA]: una línea por informe (el más reciente primero) y el siguiente número disponible."""
    items = list((leer(INFORMES, obligatorio=False) or VACIO_INFORMES).get("informes", []))
    todos = items
    items = [d for _, d in sorted(enumerate(items), key=lambda x: (str(x[1].get("fecha") or ""), x[0]), reverse=True)]
    claves = _fuentes.palabras_clave(tema) if tema else []
    if claves:
        pts = [(_fuentes.puntuar(claves, [(d.get("tema"), 3), (d.get("tesis"), 2), (d.get("slug"), 2)]), d) for d in items]
        items = [d for p, d in sorted(pts, key=lambda x: -x[0]) if p]
    print("informes registrados: %d%s" % (len(items), (" · tema: %s · claves: %s" % (tema, ", ".join(claves))) if claves else ""))
    for d in items[:maximo]:
        print("  %s · N.º %s · %s · %s págs · %s · %s (hilo: %s)" % (
            d.get("id"), d.get("numero"), (d.get("tema") or "")[:60], d.get("n_paginas"), d.get("estado"), d.get("ruta_informe"), d.get("ruta_hilo")))
    if not items:
        print("  (ninguno)")
    usados = [int(d["numero"]) for d in todos if str(d.get("numero") or "").isdigit()]
    print("siguiente N.º %02d" % ((max(usados) + 1) if usados else 1))
    return 0


def frases_video(g):
    """Frases de la voz que el guionista tiende a repetir entre videos: la promesa, la primera oración del gancho, cómo
    abre cada escena desde la 3 y la pregunta del cierre. video.py preparar las pone en el digesto («Frases ya usadas»)."""
    def primera(t):
        return re.split(r"(?<=[.?!])\s+", (t or "").strip())[0] if t else ""
    esc = g.get("escenas") or []
    voz = [e.get("voz") or e.get("texto") or "" for e in esc]
    return {
        "promesa": (g.get("promesa") or {}).get("texto", ""),
        "gancho": primera(voz[0]) if voz else "",
        "aperturas": [" ".join(v.split()[:4]) for v in voz[2:] if v.strip()],
        "pregunta": (g.get("cierre") or {}).get("pregunta", ""),
    }


def registrar_video(d, estado, dry_run=False):
    """--video DIR: registra en memoria/videos.json el video entregado en DIR (hilos/<fecha>-<slug>/video, con guion.json)."""
    ruta = os.path.normpath(d)
    g = leer(os.path.join(RAIZ, ruta, "guion.json"), obligatorio=False)
    if not g or not g.get("id"):
        print("ERROR: %s no tiene guion.json de entrega (scripts/video.py entregar)" % ruta, file=sys.stderr)
        return 1
    hilo = leer(os.path.join(RAIZ, g["hilo"], "hilo.json"), obligatorio=False) or {}
    reg = {
        "id": g["id"], "fecha": time.strftime("%Y-%m-%d"), "slug": g["slug"], "hilo_id": "%s-%s" % (hilo.get("fecha"), g["slug"]),
        "tema": hilo.get("tema", ""), "paleta": g["paleta"], "duracion": g["duracion"], "duracion_s": g["duracion_s"],
        "n_escenas": g["n_escenas"], "musica": g["musica"], "creditos_voz": g.get("creditos_voz"),
        "ruta_video": ruta, "ruta_hilo": g["hilo"], "estado": estado, "frases": frases_video(g),
    }
    mv = leer(VIDEOS, obligatorio=False) or json.loads(json.dumps(VACIO_VIDEOS))
    previos = [i for i, v in enumerate(mv["videos"]) if v.get("id") == reg["id"]]
    if previos:  # volver a registrar conserva la fecha original (y el estado «publicado» si ya lo tenía)
        viejo = mv["videos"][previos[0]]
        reg["fecha"] = viejo.get("fecha", reg["fecha"])
        if viejo.get("estado") == "publicado" and estado == "listo":
            reg["estado"] = "publicado"
        mv["videos"][previos[0]] = reg
    else:
        mv["videos"].append(reg)
    print("video %s · %s %.0f s · %d escenas · música %s · %s" % (reg["id"], reg["duracion"], reg["duracion_s"],
                                                              reg["n_escenas"], reg["musica"], reg["estado"]))
    if dry_run:
        print("[dry-run] no se escribió nada")
        return 0
    escribir(VIDEOS, mv)
    print("escrito memoria/videos.json (%d videos)" % len(mv["videos"]))
    return 0


def conciliar_modos(dry_run=False):
    """Registros viejos sin «modo»: lo toma del hilo.json / dato.json de su entrega (o el del tipo)."""
    n = 0
    for archivo, clave, entrega, defecto in ((HILOS, "hilos", "hilo.json", "hilo"), (DATOS, "datos", "dato.json", "dato")):
        d = leer(archivo, obligatorio=False)
        if not d:
            continue
        cambia = False
        for r in d.get(clave, []):
            if r.get("modo"):
                continue
            j = leer(os.path.join(RAIZ, str(r.get("ruta", "")), entrega), obligatorio=False) or {}
            r["modo"] = j.get("modo") or defecto
            cambia, n = True, n + 1
            print("%s%s → modo %s" % ("[dry-run] " if dry_run else "", r.get("id"), r["modo"]))
        if cambia and not dry_run:
            escribir(archivo, d)
    print("[memoria] %d registro(s) con modo completado" % n)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--registrar", metavar="SESION", help="carpeta sesiones/<slug> (hilo o dato según guion.tipo)")
    g.add_argument("--series", metavar="TEMA", help="busca series conocidas para un tema")
    g.add_argument("--datos", nargs="?", const="", metavar="TEMA", help="lista los datos registrados en memoria/datos.json (/dato), del más reciente al más antiguo; con TEMA filtra por palabras clave")
    g.add_argument("--conciliar-modos", action="store_true", help="completa «modo» en los registros de hilos.json y datos.json que no lo tienen, desde el hilo.json / dato.json de su entrega")
    g.add_argument("--informes", nargs="?", const="", metavar="TEMA", help="lista los informes de memoria/informes.json (/investigacion) y el siguiente N.º; con TEMA filtra")
    g.add_argument("--video", metavar="DIR", help="registra el video de /video entregado en DIR (hilos/<fecha>-<slug>/video) en memoria/videos.json")
    p.add_argument("--ruta", help="carpeta de entrega, relativa a la raíz (hilos/<fecha>-<slug>, datos/<fecha>-<slug> o investigacion/<fecha>-<slug>/hilo)")
    p.add_argument("--informe", metavar="DIR", help="con --registrar: carpeta del informe (investigacion/<fecha>-<slug>, con informe.json) → memoria/informes.json")
    p.add_argument("--solo-informe", action="store_true", help="con --informe: registra solo el informe; el hilo ya está en hilos.json (flujo desde:<slug>)")
    p.add_argument("--estado", choices=["listo", "incompleto"], default="listo")
    p.add_argument("--hook", choices=HOOKS, metavar="<hook_tipo>", help="nombre del gancho (por defecto, guion.hook_tipo): " + "|".join(HOOKS))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=12)
    a = p.parse_args()
    if a.conciliar_modos:
        return conciliar_modos(a.dry_run)
    if a.video:
        return registrar_video(a.video, a.estado, a.dry_run)
    if a.datos is not None:
        return listar_datos(a.datos, a.max)
    if a.informes is not None:
        return listar_informes(a.informes, a.max)
    if a.solo_informe and not a.informe:
        p.error("--solo-informe exige --informe <dir>")
    if a.series:
        claves = _fuentes.palabras_clave(a.series)
        if not claves:
            print("ERROR: el tema no tiene palabras de ≥ 4 letras", file=sys.stderr)
            return 2
        ss = _fuentes.buscar_series(leer(FUENTES).get("series", []), claves)
        print("tema: %s · claves: %s · series: %d" % (a.series, ", ".join(claves), len(ss)))
        for s in ss[: a.max]:
            print("  " + _fuentes.fmt_serie(s))
        return 0
    if not a.ruta:
        p.error("--registrar requiere --ruta <carpeta de entrega relativa>")
    return registrar(a)


if __name__ == "__main__":
    sys.exit(main())
