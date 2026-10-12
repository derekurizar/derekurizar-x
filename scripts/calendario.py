#!/usr/bin/env python3
"""Calendario editorial (ideas/calendario.json): fechas con dato para /fecha. Es el ÚNICO escritor del calendario.

Cada entrada: {id, fecha, tipo, titulo, pista, formato, modo, fuentes_sugeridas[], anio_origen, nota,
estado, ultimo_uso, pieza}.
  fecha: "MM-DD" (anual: efeméride o día internacional) · "DD" (mensual: publicación de una fuente)
         · "YYYY-MM-DD" (puntual: elecciones, plazo) · o una lista de esas formas (pliegos trimestrales)
  tipo: efemeride | dia_internacional | publicacion | evento · formato: dato | hilo
  modo: null | dato | vs | mapa | antes (formato dato) · null | hilo | explica | perfil (formato hilo)
  anio_origen: año del hecho (efemérides) para decir «hace N años» · estado: pendiente | hecha | descartada
  Una entrada anual o mensual vuelve a salir en --proximas cuando pasó su ciclo (ultimo_uso de otro
  año o mes); una puntual hecha no vuelve; una descartada no sale nunca.

--proximas [DIAS]         entradas cuya próxima ocurrencia cae en los próximos DIAS días (30)
--dia <YYYY-MM-DD|MM-DD>  entradas que caen ese día
--ver <id>                una entrada (JSON compacto)
--buscar "texto"          entradas cuyo título o pista casan con el texto (palabras clave)
--importar <dir>          añade las entradas de <dir>/calendario_*.json (las escribe el explorador de
                          /fecha buscar): valida y descarta repetidas (mismo id, o misma fecha con
                          ≥ 60 % de palabras clave compartidas)
--marcar <id> --estado E [--pieza <ruta>]   cambia el estado (hecha anota ultimo_uso y pieza)

Opciones: --fecha YYYY-MM-DD (hoy por defecto) · --dry-run · --calendario <ruta> (para pruebas).
Salida: 0 ok · 1 error · 2 uso incorrecto
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import fuentes as _fuentes  # noqa: E402
from ensamblar import MODOS  # noqa: E402  (modos válidos por tipo de pieza)

CALENDARIO = os.path.join(RAIZ, "ideas", "calendario.json")
TIPOS = ["efemeride", "dia_internacional", "publicacion", "evento"]
FORMATOS_PIEZA = ["dato", "hilo"]
ESTADOS = ["pendiente", "hecha", "descartada"]
UMBRAL = 0.6
COMENTARIO = ("Calendario editorial para /fecha: efemérides, días internacionales y publicaciones de fuentes "
              "con un dato de Guatemala detrás. Lo escribe SOLO scripts/calendario.py (importar, marcar). "
              "fecha: MM-DD anual · DD mensual · YYYY-MM-DD puntual (o lista). estado: pendiente | hecha | descartada.")


class ErrorUso(Exception):
    pass


def hoy():
    return datetime.date.today().isoformat()


def leer(ruta, defecto=None):
    if not os.path.exists(ruta):
        if defecto is not None:
            return defecto
        raise SystemExit("ERROR: falta %s" % os.path.relpath(ruta, RAIZ))
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def cargar(ruta=CALENDARIO):
    c = leer(ruta, {"version": 1, "_comentario": COMENTARIO, "entradas": []})
    c.setdefault("entradas", [])
    return c


def slug_de(texto):
    s = re.sub(r"[^a-z0-9]+", "-", _fuentes.normalizar(texto)).strip("-")
    return s[:60].rstrip("-")


def claves(*textos):
    return {k for k in _fuentes.palabras_clave(" ".join(str(t or "") for t in textos)) if not k.isdigit()}


def solapa(a, b):
    if not a or not b:
        return 0.0
    comun = len(a & b)
    return 0.0 if comun < 2 else comun / float(min(len(a), len(b)))


# ── fechas ────────────────────────────────────────────────────────────────
def parsear_spec(f):
    """'MM-DD' → ('anual', mm, dd) · 'DD' → ('mensual', dd) · 'YYYY-MM-DD' → ('puntual', date). None si no vale."""
    f = str(f or "").strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", f):
            return ("puntual", datetime.date.fromisoformat(f))
        if re.fullmatch(r"\d{2}-\d{2}", f):
            mm, dd = int(f[:2]), int(f[3:])
            datetime.date(2024, mm, dd)  # 2024 es bisiesto: admite 02-29
            return ("anual", mm, dd)
        if re.fullmatch(r"\d{2}", f) and 1 <= int(f) <= 31:
            return ("mensual", int(f))
    except ValueError:
        return None
    return None


def specs_de(e):
    fs = e.get("fecha")
    return [s for s in (fs if isinstance(fs, list) else [fs]) if s is not None]


def fecha_segura(anio, mes, dia):
    while dia > 28:
        try:
            return datetime.date(anio, mes, dia)
        except ValueError:
            dia -= 1
    return datetime.date(anio, mes, dia)


def proxima(spec, desde):
    """Primera ocurrencia de la spec en o después de `desde` (None si no hay)."""
    p = parsear_spec(spec)
    if not p:
        return None
    if p[0] == "puntual":
        return p[1] if p[1] >= desde else None
    if p[0] == "anual":
        d = fecha_segura(desde.year, p[1], p[2])
        return d if d >= desde else fecha_segura(desde.year + 1, p[1], p[2])
    d = fecha_segura(desde.year, desde.month, p[1])
    if d >= desde:
        return d
    anio, mes = (desde.year + 1, 1) if desde.month == 12 else (desde.year, desde.month + 1)
    return fecha_segura(anio, mes, p[1])


def cae(spec, dia):
    """True si la spec ocurre en la fecha `dia` (date)."""
    p = parsear_spec(spec)
    if not p:
        return False
    if p[0] == "puntual":
        return p[1] == dia
    if p[0] == "anual":
        return fecha_segura(dia.year, p[1], p[2]) == dia
    return fecha_segura(dia.year, dia.month, p[1]) == dia


def vigente(e, spec, ocurrencia):
    """¿La entrada debe salir para esa ocurrencia? pendiente sí; hecha solo si pasó su ciclo; descartada nunca."""
    estado = e.get("estado", "pendiente")
    if estado == "descartada":
        return False
    if estado != "hecha" or not e.get("ultimo_uso"):
        return True
    p = parsear_spec(spec)
    try:
        u = datetime.date.fromisoformat(str(e["ultimo_uso"]))
    except ValueError:
        return True
    if p[0] == "puntual":
        return False
    if p[0] == "anual":
        return u.year != ocurrencia.year
    return (u.year, u.month) != (ocurrencia.year, ocurrencia.month)


def anios_desde(e, ocurrencia):
    a = e.get("anio_origen")
    return (ocurrencia.year - int(a)) if isinstance(a, int) and a > 0 else None


# ── validación ────────────────────────────────────────────────────────────
def validar_entrada(e):
    F = []
    if not re.fullmatch(r"[a-z0-9-]+", str(e.get("id") or "")):
        F.append("id %r no es un slug" % e.get("id"))
    specs = specs_de(e)
    if not specs:
        F.append("sin fecha")
    for s in specs:
        if not parsear_spec(s):
            F.append("fecha %r no es MM-DD, DD ni YYYY-MM-DD" % s)
    if e.get("tipo") not in TIPOS:
        F.append("tipo %r no está en %s" % (e.get("tipo"), "|".join(TIPOS)))
    for campo in ("titulo", "pista"):
        if not str(e.get(campo) or "").strip():
            F.append("sin %s" % campo)
    fmt = e.get("formato")
    if fmt not in FORMATOS_PIEZA:
        F.append("formato %r no está en %s" % (fmt, "|".join(FORMATOS_PIEZA)))
    elif e.get("modo") is not None and e["modo"] not in MODOS[fmt]:
        F.append("modo %r no vale para formato %s (%s)" % (e["modo"], fmt, "|".join(MODOS[fmt])))
    if e.get("estado", "pendiente") not in ESTADOS:
        F.append("estado %r no está en %s" % (e.get("estado"), "|".join(ESTADOS)))
    if e.get("anio_origen") is not None and not (isinstance(e["anio_origen"], int) and 1500 < e["anio_origen"] < 2200):
        F.append("anio_origen %r no es un año" % e.get("anio_origen"))
    if e.get("fuentes_sugeridas") is not None and not (isinstance(e["fuentes_sugeridas"], list) and all(isinstance(x, str) for x in e["fuentes_sugeridas"])):
        F.append("fuentes_sugeridas debe ser una lista de textos")
    if e.get("ultimo_uso") is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e["ultimo_uso"])):
        F.append("ultimo_uso %r no es YYYY-MM-DD" % e.get("ultimo_uso"))
    return F


def compacta(e):
    return {k: e.get(k) for k in ("id", "fecha", "tipo", "titulo", "pista", "formato", "modo", "fuentes_sugeridas", "anio_origen", "nota", "estado", "ultimo_uso", "pieza")}


def linea(e, ocurrencia, desde):
    n = (ocurrencia - desde).days
    cuando = "hoy" if n == 0 else ("mañana" if n == 1 else "en %d días" % n)
    hace = anios_desde(e, ocurrencia)
    etiqueta = e.get("formato", "?") + (("/" + e["modo"]) if e.get("modo") else "")
    extra = (" · hace %d años" % hace) if hace is not None else ""
    estado = e.get("estado", "pendiente") + ((" " + e["ultimo_uso"]) if e.get("estado") == "hecha" and e.get("ultimo_uso") else "")
    nota = (" · " + e["nota"]) if e.get("nota") else ""
    return "  %s (%s) · %s · %s · %s · %s · [%s]%s%s" % (ocurrencia.isoformat(), cuando, e.get("id"), e.get("titulo"), etiqueta, e.get("tipo"), estado, extra, nota)


# ── comandos ──────────────────────────────────────────────────────────────
def cmd_proximas(a):
    desde = datetime.date.fromisoformat(a.fecha or hoy())
    hasta = desde + datetime.timedelta(days=a.proximas if a.proximas is not None else 30)
    filas = []
    for e in cargar(a.calendario)["entradas"]:
        for s in specs_de(e):
            o = proxima(s, desde)
            if o and o <= hasta and vigente(e, s, o):
                filas.append((o, e))
    filas.sort(key=lambda x: (x[0], x[1].get("id", "")))
    print("calendario: %d entrada(s) entre %s y %s" % (len(filas), desde.isoformat(), hasta.isoformat()))
    for o, e in filas:
        print(linea(e, o, desde))
    if not filas:
        print("  (ninguna; prueba /fecha buscar <mes> para proponer entradas)")
    return 0


def cmd_dia(a):
    desde = datetime.date.fromisoformat(a.fecha or hoy())
    arg = str(a.dia).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
        dia = datetime.date.fromisoformat(arg)
    elif re.fullmatch(r"\d{2}-\d{2}", arg):
        dia = proxima(arg, desde)
    else:
        raise ErrorUso("--dia espera YYYY-MM-DD o MM-DD")
    filas = [(dia, e) for e in cargar(a.calendario)["entradas"] if any(cae(s, dia) for s in specs_de(e)) and e.get("estado") != "descartada"]
    print("calendario: %d entrada(s) el %s" % (len(filas), dia.isoformat()))
    for o, e in filas:
        print(linea(e, o, desde))
    return 0 if filas else 1


def cmd_ver(a):
    e = next((x for x in cargar(a.calendario)["entradas"] if x.get("id") == a.ver), None)
    if not e:
        print("ERROR: no hay entrada %r" % a.ver, file=sys.stderr)
        return 1
    print(json.dumps(compacta(e), ensure_ascii=False, indent=1))
    return 0


def cmd_buscar(a):
    k = claves(a.buscar)
    if not k:
        print("ERROR: el texto no tiene palabras de ≥ 4 letras", file=sys.stderr)
        return 2
    res = []
    for e in cargar(a.calendario)["entradas"]:
        if e.get("estado") == "descartada":
            continue
        # Fracción de las palabras del texto que aparecen en la entrada (una palabra basta: «/fecha migrante»).
        comun = len(k & claves(e.get("titulo"), e.get("pista")))
        s = comun / float(len(k)) if comun else 0.0
        if s > 0:
            res.append((s, e))
    res.sort(key=lambda x: -x[0])
    print("texto: %s · entradas que casan: %d" % (a.buscar, len(res)))
    for s, e in res[:8]:
        print("  %s %.2f · %s · %s · [%s] %s" % ("FUERTE" if s >= UMBRAL else "débil ", s, e["id"], e.get("fecha"), e.get("estado"), e.get("titulo")))
    return 0


def cmd_importar(a):
    archivos = sorted(glob.glob(os.path.join(a.importar, "calendario_*.json")))
    if not archivos:
        print("ERROR: no hay calendario_*.json en %s" % a.importar, file=sys.stderr)
        return 1
    cal = cargar(a.calendario)
    fecha = a.fecha or hoy()
    ids = {e.get("id") for e in cal["entradas"]}
    existentes = [(e.get("id"), tuple(sorted(str(s) for s in specs_de(e))), claves(e.get("titulo"), e.get("pista"))) for e in cal["entradas"]]
    nuevas, n_rep, n_inv = [], 0, 0
    for ruta in archivos:
        try:
            d = leer(ruta)
        except ValueError as exc:
            print("✗ %s no es JSON válido: %s" % (os.path.basename(ruta), exc)); n_inv += 1
            continue
        for e in (d.get("entradas") if isinstance(d, dict) else d) or []:
            e = dict(e)
            e["id"] = slug_de(e.get("id") or e.get("titulo") or "")
            e.setdefault("estado", "pendiente")
            problemas = validar_entrada(e)
            if problemas:
                print("✗ inválida %s (%s): %s" % (e["id"] or "?", os.path.basename(ruta), "; ".join(problemas))); n_inv += 1
                continue
            if e["id"] in ids:
                print("= repetida %s (mismo id)" % e["id"]); n_rep += 1
                continue
            spec = tuple(sorted(str(s) for s in specs_de(e)))
            k = claves(e.get("titulo"), e.get("pista"))
            parecida = next((eid for eid, es, ek in existentes if es == spec and solapa(k, ek) >= UMBRAL), None)
            if parecida:
                print("= repetida %s (≈ %s, misma fecha)" % (e["id"], parecida)); n_rep += 1
                continue
            entrada = {"id": e["id"], "fecha": e.get("fecha"), "tipo": e["tipo"], "titulo": e["titulo"].strip(), "pista": e["pista"].strip(),
                       "formato": e["formato"], "modo": e.get("modo"), "fuentes_sugeridas": e.get("fuentes_sugeridas") or [],
                       "anio_origen": e.get("anio_origen"), "nota": (e.get("nota") or "").strip(),
                       "estado": "pendiente", "ultimo_uso": None, "pieza": None, "creada": fecha}
            cal["entradas"].append(entrada); nuevas.append(entrada)
            ids.add(entrada["id"]); existentes.append((entrada["id"], spec, k))
            print("+ %s · %s · %s · %s" % (entrada["id"], entrada["fecha"], entrada["formato"] + (("/" + entrada["modo"]) if entrada["modo"] else ""), entrada["titulo"]))
    print("%s%d nuevas · %d repetidas · %d inválidas · calendario con %d entradas" % (
        "[dry-run] " if a.dry_run else "", len(nuevas), n_rep, n_inv, len(cal["entradas"])))
    if not a.dry_run and nuevas:
        escribir(a.calendario, cal)
    return 0


def marcar(entrada_id, estado, pieza=None, fecha=None, ruta=CALENDARIO, dry_run=False):
    """Cambia el estado de una entrada. Devuelve (mensaje, código)."""
    if estado not in ESTADOS:
        raise ErrorUso("estado %r no está en %s" % (estado, "|".join(ESTADOS)))
    cal = cargar(ruta)
    e = next((x for x in cal["entradas"] if x.get("id") == entrada_id), None)
    if not e:
        return "ERROR: no hay entrada %r en %s" % (entrada_id, os.path.relpath(ruta, RAIZ)), 1
    antes = e.get("estado")
    e["estado"] = estado
    if estado == "hecha":
        e["ultimo_uso"] = fecha or hoy()
        if pieza:
            e["pieza"] = pieza
    msg = "%sentrada %s: %s → %s%s" % ("[dry-run] " if dry_run else "", entrada_id, antes, estado, (" (pieza %s)" % pieza) if pieza else "")
    if not dry_run:
        escribir(ruta, cal)
    return msg, 0


def cmd_marcar(a):
    if not a.estado:
        raise ErrorUso("--marcar requiere --estado")
    msg, rc = marcar(a.marcar, a.estado, a.pieza, a.fecha, a.calendario, a.dry_run)
    print(msg, file=sys.stderr if rc else sys.stdout)
    return rc


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--proximas", nargs="?", const=30, type=int, metavar="DIAS")
    g.add_argument("--dia", metavar="FECHA")
    g.add_argument("--ver", metavar="ID")
    g.add_argument("--buscar", metavar="TEXTO")
    g.add_argument("--importar", metavar="DIR")
    g.add_argument("--marcar", metavar="ID")
    p.add_argument("--estado", choices=ESTADOS)
    p.add_argument("--pieza", metavar="RUTA", help="carpeta de entrega relativa (para --marcar hecha)")
    p.add_argument("--fecha", metavar="YYYY-MM-DD", help="«hoy» para los cálculos (por defecto la fecha actual)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--calendario", default=CALENDARIO, metavar="RUTA", help="ruta del calendario (para pruebas)")
    a = p.parse_args()
    if a.fecha and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.fecha):
        p.error("--fecha debe ser YYYY-MM-DD")
    try:
        if a.proximas is not None:
            return cmd_proximas(a)
        if a.dia:
            return cmd_dia(a)
        if a.ver:
            return cmd_ver(a)
        if a.buscar:
            return cmd_buscar(a)
        if a.importar:
            return cmd_importar(a)
        return cmd_marcar(a)
    except ErrorUso as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
