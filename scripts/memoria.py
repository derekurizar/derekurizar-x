#!/usr/bin/env python3
"""Registra un hilo terminado en memoria/ (lo usa el productor al cerrar) y consulta series.

--registrar <sesion> --ruta <ruta relativa> [--estado listo|incompleto] [--hook <hook_tipo>] [--dry-run]
  Lee <sesion>/guion.json (slug, fecha, paleta, hook_tipo, sintesis.tesis, tuits),
  encuadre.json (tema), <ruta>/datos.json y <sesion>/hallazgos_*.json.
  Añade o actualiza en memoria/hilos.json → hilos[]
    {id: "<fecha>-<slug>", fecha, slug, tema, tesis, paleta, n_tuits, ruta, estado, hook_tipo}
  (hook_tipo: el nombre del gancho de guion.json; --hook lo sobrescribe y debe ser uno
  de los ocho nombres de ensamblar.HOOKS). En memoria/fuentes.json:
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

--series "tema"   mismo filtro que scripts/fuentes.py --series

Salida: 0 ok · 1 error · 2 uso incorrecto
"""
import argparse
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import fuentes as _fuentes  # noqa: E402
import ideas as _ideas  # noqa: E402  (único escritor de ideas/banco.json)
from ensamblar import HOOKS  # noqa: E402  (los ocho nombres de gancho: una sola lista)

HILOS = os.path.join(RAIZ, "memoria", "hilos.json")
FUENTES = os.path.join(RAIZ, "memoria", "fuentes.json")
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


def frecuencia_de(serie):
    ps = [str(p.get("p", "")).strip() for p in serie]
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


def series_de(datos, hilo_id):
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
            "desde": str(serie[0].get("p")), "hasta": str(serie[-1].get("p")),
            "frecuencia": frecuencia_de(serie), "nota": "registrada desde hilo %s" % hilo_id,
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


def registrar(a):
    if os.path.isabs(a.ruta):
        print("ERROR: --ruta debe ser relativa a la raíz del repo (p. ej. hilos/2026-09-28-remesas)", file=sys.stderr)
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
    hilo = {
        "id": hid, "fecha": fecha, "slug": slug,
        "tema": encuadre.get("tema") or guion.get("tema") or datos.get("tema") or slug,
        "tesis": (guion.get("sintesis") or {}).get("tesis") or guion.get("tesis") or "",
        "paleta": guion.get("paleta"), "n_tuits": len(guion.get("tuits", [])),
        "ruta": os.path.normpath(a.ruta), "estado": a.estado, "hook_tipo": hook,
    }
    smoke = bool(guion.get("smoke") or encuadre.get("smoke") or encuadre.get("fixture"))
    idea_id = encuadre.get("idea_id")
    if idea_id:
        hilo["idea_id"] = idea_id
    if smoke:
        print("AVISO: la sesión es smoke; en smoke el productor NO escribe memoria/ (usa --dry-run o confirma que quieres registrarla).", file=sys.stderr)

    mh = leer(HILOS)
    hilos = mh.setdefault("hilos", [])
    idx = next((i for i, h in enumerate(hilos) if h.get("id") == hid), None)
    accion = "actualizado" if idx is not None else "añadido"
    if idx is not None:
        hilos[idx].update(hilo)
    else:
        hilos.append(hilo)

    mf = leer(FUENTES)
    series = mf.setdefault("series", [])
    # Dedup por url + nombre normalizado: un mismo xlsx (Banguat) trae varias series distintas.
    clave = lambda s: (str(s.get("url") or "").strip().lower(), _fuentes.normalizar(s.get("nombre")))
    vistas = {clave(s) for s in series}
    nuevas, repetidas = [], []
    for s in series_de(datos, hid):
        if clave(s) in vistas:
            repetidas.append(s["nombre"])
            continue
        vistas.add(clave(s))
        series.append(s); nuevas.append(s)
    primarias, vacios = hallazgos_de(sesion)
    fuentes_nuevas, notas = fusionar_fuentes(mf, primarias, vacios, hilo["tema"], hid, fecha)

    print("%s hilo %s → memoria/hilos.json (%s, %d tuits, paleta %s, estado %s%s)" % (
        "[dry-run] " if a.dry_run else "", hid, accion, hilo["n_tuits"], hilo["paleta"], hilo["estado"], (", hook " + hook) if hook else ""))
    print("  tema: %s" % hilo["tema"])
    print("  tesis: %s" % hilo["tesis"][:160])
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
    if idea_id and smoke:
        print("  (idea %s: sesión smoke/fixture, el banco de ideas no se toca)" % idea_id)
    if a.dry_run:
        if idea_id and not smoke:
            print("  idea %s → %s (hilo %s)" % (idea_id, "hecha" if a.estado == "listo" else "en_curso", hid))
        print("[dry-run] no se escribió nada")
        return 0
    escribir(HILOS, mh)
    escribir(FUENTES, mf)
    print("escrito memoria/hilos.json (%d hilos) y memoria/fuentes.json (%d series, %d nuevas; %d fuentes nuevas, %d notas)" % (
        len(hilos), len(series), len(nuevas), len(fuentes_nuevas), len(notas)))
    if idea_id and not smoke:
        msg, rc = _ideas.marcar_idea(idea_id, "hecha" if a.estado == "listo" else "en_curso", hid, fecha)
        print(("AVISO: " if rc else "  ") + msg, file=sys.stderr if rc else sys.stdout)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--registrar", metavar="SESION", help="carpeta sesiones/<slug>")
    g.add_argument("--series", metavar="TEMA", help="busca series conocidas para un tema")
    p.add_argument("--ruta", help="carpeta de entrega, relativa a la raíz (hilos/<fecha>-<slug>)")
    p.add_argument("--estado", choices=["listo", "incompleto"], default="listo")
    p.add_argument("--hook", choices=HOOKS, metavar="<hook_tipo>", help="nombre del gancho (por defecto, guion.hook_tipo): " + "|".join(HOOKS))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int, default=12)
    a = p.parse_args()
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
