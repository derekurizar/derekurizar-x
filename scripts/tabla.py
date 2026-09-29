#!/usr/bin/env python3
"""Explora un CSV grande sin cargarlo entero: columnas, cabeza, conteo, filtros, agrupación y series.

Pensado para los CSV que deja fetch_tabla.py en sesiones/_descargas/ (xlsx → csv).
Detecta el delimitador, entiende números con coma de miles («25,530.2») y con coma
decimal («25.530,2») y trabaja en streaming (solo --agrupar y --serie acumulan, y
solo sus claves).

Uso:
  python3 scripts/tabla.py datos.csv --columnas                  # nombres y un ejemplo por columna
  python3 scripts/tabla.py datos.csv --cabeza 10                  # primeras N filas
  python3 scripts/tabla.py datos.csv --contar [--filtrar col=val]  # filas (que cumplen)
  python3 scripts/tabla.py datos.csv --filtrar PAIS="EE. UU." --filtrar VIA=AEREO
  python3 scripts/tabla.py datos.csv --agrupar depto --sumar total   # (o --contar)
  python3 scripts/tabla.py datos.csv --serie fecha valor [--agregar sum|mean|last] [--periodo anio|mes|dia]
  python3 scripts/tabla.py datos.csv --describir valor            # n, mín, máx, media, suma
  --encabezado N   fila (1-based) que trae los nombres de columna (default: la primera no vacía)
  --sin-encabezado columnas numeradas c1, c2, …

--filtrar admite col=val (igual, sin tildes ni mayúsculas), col~texto (contiene),
col>n, col<n, col>=n, col<=n. --serie agrupa por periodo detectando YYYY, YYYY-MM o
dd/mm/yyyy y devuelve «periodo,valor» listo para pegar como serie.
Máximo 60 filas en pantalla (avisa si recorta). Salida: 0 ok · 1 error · 2 uso incorrecto.
"""
import argparse
import csv
import io
import os
import re
import sys
import unicodedata

MAX_FILAS = 60
RE_NUM = re.compile(r"^[-+]?\(?\s*[\d.,]+\s*\)?%?$")
RE_FECHA_DMY = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})")
RE_FECHA_YMD = re.compile(r"^(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?")
RE_ANIO = re.compile(r"^\s*(\d{4})\s*$")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
         "jan": 1, "apr": 4, "aug": 8, "dec": 12}


def normalizar(s):
    s = unicodedata.normalize("NFD", str(s or "")).lower().strip()
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def a_numero(s):
    """'25,530.2' → 25530.2 · '25.530,2' → 25530.2 · '(1,200)' → -1200 · '12%' → 12. None si no es número."""
    if s is None:
        return None
    t = str(s).strip().replace(" ", "").replace(" ", "")
    if not t or not RE_NUM.match(t):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()%")
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")  # coma decimal
        else:
            t = t.replace(",", "")  # coma de miles
    elif "," in t:
        partes = t.split(",")
        # 1,234 / 12,345,678 → miles; 12,5 → decimal
        t = t.replace(",", "") if all(len(x) == 3 for x in partes[1:]) else t.replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        if v.is_integer():
            return "{:,}".format(int(v))
        return ("{:,.4f}".format(v)).rstrip("0").rstrip(".")
    return str(v)


def periodo_de(s):
    """Normaliza a YYYY, YYYY-MM o YYYY-MM-DD según lo que traiga la celda."""
    t = str(s or "").strip()
    m = RE_ANIO.match(t)
    if m:
        return m.group(1)
    m = RE_FECHA_DMY.match(t)
    if m:
        d, mo, y = m.groups()
        return "%s-%02d-%02d" % (y, int(mo), int(d))
    m = RE_FECHA_YMD.match(t)
    if m:
        y, mo, d = m.groups()
        return "%s-%02d" % (y, int(mo)) + ("-%02d" % int(d) if d else "")
    m = re.match(r"^([a-záéíóú]{3})[a-záéíóú]*[\s./-]*(\d{4})$", normalizar(t))
    if m and m.group(1) in MESES:
        return "%s-%02d" % (m.group(2), MESES[m.group(1)])
    return t or None


def abrir(ruta):
    raw = open(ruta, "rb").read(65536)
    enc = "utf-8-sig"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        enc = "latin-1"
    muestra = raw.decode(enc, errors="replace")
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t|")
        delim = dialecto.delimiter
    except csv.Error:
        delim = ","
    fh = open(ruta, encoding=enc, newline="")
    return fh, csv.reader(fh, delimiter=delim), delim


def nombres(fila):
    """Nombres de columna limpios y únicos: vacíos → cN, repetidos → nombre_2, nombre_3…"""
    out, vistos = [], {}
    for k, c in enumerate(fila):
        n = re.sub(r"\s+", " ", str(c)).strip() or "c%d" % (k + 1)
        if n in vistos:
            vistos[n] += 1
            n = "%s_%d" % (n, vistos[n])
        else:
            vistos[n] = 1
        out.append(n)
    return out


def filas(ruta, encabezado=None, sin_encabezado=False):
    """Generador de (cabecera, dict fila). Salta filas vacías; la cabecera es la
    primera fila no vacía, la fila --encabezado N, o cN si --sin-encabezado."""
    fh, rd, _ = abrir(ruta)
    with fh:
        cab = None
        for i, fila in enumerate(rd, 1):
            if cab is None:
                if sin_encabezado:
                    cab = nombres([""] * len(fila))
                elif encabezado:
                    if i < encabezado:
                        continue
                    cab = nombres(fila)
                    continue
                else:
                    if not any(c.strip() for c in fila):
                        continue
                    cab = nombres(fila)
                    continue
            if not any(c.strip() for c in fila):
                continue
            if len(fila) > len(cab):
                cab = cab + ["c%d" % (k + 1) for k in range(len(cab), len(fila))]
            yield cab, {cab[k]: (fila[k] if k < len(fila) else "") for k in range(len(cab))}


def resolver_col(cab, nombre):
    """Acepta nombre exacto, sin tildes/mayúsculas, prefijo único o índice 1-based."""
    if nombre in cab:
        return nombre
    n = normalizar(nombre)
    exactas = [c for c in cab if normalizar(c) == n]
    if len(exactas) == 1:
        return exactas[0]
    if nombre.isdigit() and 1 <= int(nombre) <= len(cab):
        return cab[int(nombre) - 1]
    pref = [c for c in cab if normalizar(c).startswith(n)]
    if len(pref) == 1:
        return pref[0]
    raise SystemExit("ERROR: columna %r no existe (hay: %s)" % (nombre, ", ".join(cab)))


def compilar_filtros(exprs):
    ops = []
    for e in exprs or []:
        m = re.match(r"^([^<>=~!]+)(>=|<=|!=|>|<|~|=)(.*)$", e)
        if not m:
            raise SystemExit("ERROR: filtro %r inválido (usa col=val, col~texto, col>n, col<n, col>=n, col<=n, col!=val)" % e)
        ops.append((m.group(1).strip(), m.group(2), m.group(3).strip()))
    return ops


def pasa(fila, cab, filtros):
    for col, op, val in filtros:
        c = resolver_col(cab, col)
        celda = fila.get(c, "")
        if op in ("=", "!="):
            igual = normalizar(celda) == normalizar(val) or (a_numero(celda) is not None and a_numero(val) is not None and a_numero(celda) == a_numero(val))
            if (op == "=") != igual:
                return False
        elif op == "~":
            if normalizar(val) not in normalizar(celda):
                return False
        else:
            x, y = a_numero(celda), a_numero(val)
            if x is None or y is None:
                return False
            if not {">": x > y, "<": x < y, ">=": x >= y, "<=": x <= y}[op]:
                return False
    return True


def imprimir_tabla(cab, filas_out, total=None):
    if not filas_out:
        print("(sin filas)")
        return
    anchos = [min(40, max(len(str(c)), *(len(str(f[i])) for f in filas_out))) for i, c in enumerate(cab)]
    def linea(vals):
        return " | ".join(str(v)[:anchos[i]].ljust(anchos[i]) for i, v in enumerate(vals))
    print(linea(cab))
    print("-+-".join("-" * w for w in anchos))
    for f in filas_out:
        print(linea(f))
    if total is not None and total > len(filas_out):
        print("… recortado: se muestran %d de %d filas" % (len(filas_out), total))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv")
    p.add_argument("--columnas", action="store_true")
    p.add_argument("--cabeza", type=int, metavar="N")
    p.add_argument("--contar", action="store_true")
    p.add_argument("--filtrar", action="append", metavar="COL=VAL")
    p.add_argument("--agrupar", metavar="COL")
    p.add_argument("--sumar", metavar="COL")
    p.add_argument("--serie", nargs=2, metavar=("COL_FECHA", "COL_VALOR"))
    p.add_argument("--agregar", choices=["sum", "mean", "last"], default="sum")
    p.add_argument("--periodo", choices=["anio", "mes", "dia"], default="mes", help="granularidad de --serie (default mes: dd/mm/yyyy → YYYY-MM)")
    p.add_argument("--describir", metavar="COL")
    p.add_argument("--encabezado", type=int, metavar="N", help="fila 1-based con los nombres de columna")
    p.add_argument("--sin-encabezado", action="store_true")
    a = p.parse_args()
    if not os.path.exists(a.csv):
        print("ERROR: no existe %s" % a.csv, file=sys.stderr)
        return 1
    if not (a.columnas or a.cabeza or a.contar or a.filtrar or a.agrupar or a.serie or a.describir):
        a.cabeza = 10
    filtros = compilar_filtros(a.filtrar)
    gen = filas(a.csv, a.encabezado, a.sin_encabezado)

    if a.columnas:
        cab, ejemplo, n = None, {}, 0
        for cab, f in gen:
            n += 1
            for c in cab:
                if f.get(c, "").strip() and c not in ejemplo:
                    ejemplo[c] = f[c]
            if len(ejemplo) == len(cab) and n > 5:
                break
        if cab is None:
            print("ERROR: archivo vacío o sin cabecera", file=sys.stderr)
            return 1
        print("%d columnas (delimitador %r):" % (len(cab), abrir(a.csv)[2]))
        for i, c in enumerate(cab, 1):
            print("  %2d  %-30s ej: %s" % (i, c[:30], ejemplo.get(c, "")[:50]))
        return 0

    if a.serie:
        col_f, col_v = a.serie
        acc = {}
        cab = None
        for cab, f in gen:
            if not pasa(f, cab, filtros):
                continue
            cf, cv = resolver_col(cab, col_f), resolver_col(cab, col_v)
            per = periodo_de(f.get(cf))
            if per and re.match(r"^\d{4}-\d{2}", per):
                per = per[:4] if a.periodo == "anio" else per[:7] if a.periodo == "mes" else per
            v = a_numero(f.get(cv))
            if per is None or v is None:
                continue
            s = acc.setdefault(per, [0.0, 0, None])
            s[0] += v; s[1] += 1; s[2] = v
        if not acc:
            print("ERROR: sin puntos (¿columna de fecha o de valor equivocada?)", file=sys.stderr)
            return 1
        print("periodo,valor")
        for per in sorted(acc):
            s = acc[per]
            val = {"sum": s[0], "mean": s[0] / s[1], "last": s[2]}[a.agregar]
            print("%s,%s" % (per, fmt(val).replace(",", "")))
        print("# %d periodos · agregado=%s" % (len(acc), a.agregar), file=sys.stderr)
        return 0

    if a.agrupar:
        grupos = {}
        cab = None
        for cab, f in gen:
            if not pasa(f, cab, filtros):
                continue
            cg = resolver_col(cab, a.agrupar)
            k = f.get(cg, "").strip()
            g = grupos.setdefault(k, [0, 0.0])
            g[0] += 1
            if a.sumar:
                v = a_numero(f.get(resolver_col(cab, a.sumar)))
                if v is not None:
                    g[1] += v
        if cab is None:
            print("ERROR: archivo vacío", file=sys.stderr)
            return 1
        col2 = ("suma_" + a.sumar) if a.sumar else "n"
        filas_out = sorted(((k, g[1] if a.sumar else g[0]) for k, g in grupos.items()), key=lambda x: -x[1])
        imprimir_tabla([a.agrupar, col2], [(k, fmt(v)) for k, v in filas_out[:MAX_FILAS]], len(filas_out))
        print("# %d grupos" % len(grupos), file=sys.stderr)
        return 0

    if a.describir:
        n, s, mn, mx, vacias = 0, 0.0, None, None, 0
        for cab, f in gen:
            if not pasa(f, cab, filtros):
                continue
            v = a_numero(f.get(resolver_col(cab, a.describir)))
            if v is None:
                vacias += 1
                continue
            n += 1; s += v
            mn = v if mn is None else min(mn, v)
            mx = v if mx is None else max(mx, v)
        if not n:
            print("ERROR: la columna no tiene valores numéricos", file=sys.stderr)
            return 1
        print("n=%d · vacías/no numéricas=%d · mín=%s · máx=%s · media=%s · suma=%s" % (n, vacias, fmt(mn), fmt(mx), fmt(s / n), fmt(s)))
        return 0

    # --cabeza / --filtrar / --contar
    total, out, cab = 0, [], None
    limite = a.cabeza or MAX_FILAS
    for cab, f in gen:
        if not pasa(f, cab, filtros):
            continue
        total += 1
        if len(out) < limite:
            out.append([f.get(c, "") for c in cab])
        elif a.cabeza and not a.contar:
            break
    if a.contar:
        print(total)
        return 0
    if cab is None:
        print("(archivo vacío)")
        return 0
    imprimir_tabla(cab, out, total if not a.cabeza else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
