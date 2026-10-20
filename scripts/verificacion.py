#!/usr/bin/env python3
"""Verificación mecánica de una sesión: lo que un script comprueba mejor que un agente.

Corre después de la fase de Verificación (hallazgos_<eje>.json + verificacion_<eje>.json) y antes del guion.
No busca en la web: coteja lo que ya está en disco.

  V-A  la cita (o el archivo local, o la nota del verificador) contiene el número: valor_final de la cifra,
       con tolerancia de redondeo y de escala (mil, millones; Q18,097,759,240 = 18,097.76 millones; «16 mil
       537 millones»), o sale de dos números de la cita con una operación simple. Un derivado declara
       `calculo` (en la cifra o en el veredicto: «(188442390/226077000-1)*100»); el script lo evalúa.
       Falla en una cifra puntual; aviso en serie/desglose (la cita suele nombrar un solo punto).
  V-B  una cifra ajustada (valor_final ≠ valor) no conserva el valor viejo en serie[] ni en partes[]
       salvo que el veredicto traiga serie_final / partes_final.
  V-C  independencia declarada en cada verificada|ajustada (alta|baja); «alta» con url_2 del mismo dominio que
       la url de la cifra o de su evidencia es falla.
  V-D  dato viejo: anio más de --max-anios (3) antes de la fecha de la sesión (aviso).
  V-E  completitud: cada cifra de hallazgos tiene veredicto; cada veredicto, su cifra; el archivo_local existe (aviso).

Uso:
  python3 scripts/verificacion.py sesiones/<slug> [--eje PREFIJO] [--json] [--max-anios N] [--estricto]
--estricto convierte los avisos V-A de serie/desglose en fallas.
Salida: 0 sin fallas · 1 hay fallas · 2 uso incorrecto
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re
import sys
from urllib.parse import urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_ARCHIVO = 8_000_000  # bytes leídos de un archivo local

RE_NUM = re.compile(r"(?<!\d)(?<!\d[.,])(\d{1,3}(?:[ ,.  ]\d{3})+(?:[.,]\d+)?(?!\d)|\d+(?:[.,]\d+)?)(\s*(?:mil\s+millones|millardos?|millones?|mill\.?|mil\b|M\b|MM\b|k\b))?", re.I)
ESCALA = {"mil": 1e3, "k": 1e3, "millon": 1e6, "millones": 1e6, "mill": 1e6, "mill.": 1e6, "m": 1e6, "mm": 1e6,
          "mil millones": 1e9, "millardo": 1e9, "millardos": 1e9}
RE_MIL_COMPUESTO = re.compile(r"(\d{1,3})\s+mil\s+(\d{3})(?!\d)", re.I)  # «299 mil 256» → 299256
RE_MIL_SOLO = re.compile(r"(?<![\d\s])(\s*)\bmil\s+(\d{1,3})(?=[.,]\d|\D|$)", re.I)  # «mil 734» → 1734 · «mil 4.37» → 1004.37
PALABRAS = {"uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
            "diez": 10, "once": 11, "doce": 12, "quince": 15, "veinte": 20, "treinta": 30, "cien": 100}
RE_PALABRA = re.compile(r"\b(" + "|".join(PALABRAS) + r")\b", re.I)
RE_HABLADO = re.compile(r"(?<![\d.,])(?:\bun|\d{1,3}(?:[.,]\d+)?)\s+(?:mill[oó]n(?:es)?|mil)\b(?:\s+(?:\d{1,3}(?:[.,]\d+)?|mill[oó]n(?:es)?|mil)\b)*", re.I)
SUF_PUBLICO = ("gob.gt", "org.gt", "com.gt", "edu.gt", "net.gt", "gob.mx", "org.mx", "com.mx", "co.uk", "gov.uk")


def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def interpretar(tok):
    """Valores posibles de un número escrito (coma/punto como miles o decimales). Devuelve [(valor, decimales)]."""
    t = tok.replace(" ", " ").replace(" ", " ")
    out = []
    m = re.fullmatch(r"(\d{1,3}(?:([ ,.])\d{3})+)(?:([.,])(\d+))?", t)
    if m:
        sep_mil, sep_dec, dec = m.group(2), m.group(3), m.group(4) or ""
        if not sep_dec or sep_dec != sep_mil:
            entero = re.sub(r"[ ,.]", "", m.group(1))
            out.append((float(entero + ("." + dec if dec else "")), len(dec)))
    if re.fullmatch(r"\d+(?:[.,]\d+)?", t):
        ent, _, dec = t.replace(",", ".").partition(".")
        out.append((float(t.replace(",", ".")), len(dec)))
        if dec and len(dec) == 3:  # «1,234» o «1.234» como miles
            out.append((float(ent + dec), 0))
    return out


def hablado(frase):
    """«16 mil 537 millones 678 mil» → (16537678000, tolerancia). Números escritos a la manera de la prensa."""
    total, grupo, tol = 0.0, 0.0, 0.5
    for tok in frase.lower().split():
        if tok.startswith("mill"):
            total += (grupo or 1) * 1e6
            tol, grupo = tol * 1e6 if grupo else tol, 0.0
        elif tok == "mil":
            grupo = (grupo or 1) * 1000
            tol *= 1000
        else:
            n = 1.0 if tok == "un" else float(tok.replace(",", "."))
            d = len(tok.replace(",", ".").partition(".")[2])
            grupo += n
            tol = 0.5 * 10 ** (-d)
    return total + grupo, tol


def numeros(texto):
    """[(valor, tolerancia)] de todos los números de un texto (con sus escalas)."""
    hab = [hablado(m.group(0)) for m in RE_HABLADO.finditer(texto or "")]
    texto = RE_MIL_COMPUESTO.sub(lambda m: m.group(1) + m.group(2), texto or "")
    texto = RE_MIL_SOLO.sub(lambda m: m.group(1) + str(1000 + int(m.group(2)))[:1] + m.group(2).zfill(3), texto)
    out = hab
    for m in RE_NUM.finditer(texto):
        esc = 1.0
        if m.group(2):
            esc = ESCALA.get(re.sub(r"\s+", " ", m.group(2).strip().lower()), 1.0)
        for v, d in interpretar(m.group(1)):
            out.append((v * esc, 0.5 * 10 ** (-d) * esc))
    for pieza in re.split(r"[,;\s|]+", texto):  # celdas de CSV «482.0,1279.0,53373.0»
        if re.fullmatch(r"-?\d+(?:\.\d+)?", pieza):
            d = len(pieza.partition(".")[2])
            out.append((abs(float(pieza)), 0.5 * 10 ** (-d)))
    for m in RE_PALABRA.finditer(texto):
        out.append((float(PALABRAS[m.group(1).lower()]), 0.0))
    return out


def decimales(v):
    s = repr(float(v))
    if "e" in s:
        return 6
    d = s.partition(".")[2].rstrip("0")
    return len(d)


def coincide(v, encontrados, escalas=(1, 1e3, 1e6, 1e9, 1e-3, 1e-6)):
    """True si v y un número del texto son el mismo redondeado a la precisión del menos preciso de los dos."""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return True
    v = abs(v)
    tol_v = 0.5 * 10 ** (-decimales(v))
    for t, tol in encontrados:
        for e in escalas:
            if abs(v * e - t) <= max(tol, tol_v * e) * 1.0001 + 1e-9:
                return True
    return False


def evaluar(expr):
    """Valor de una operación aritmética escrita por el investigador («(188442390/226077000-1)*100»). None si no es aritmética."""
    import ast
    import operator as op
    ops = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.USub: op.neg, ast.UAdd: op.pos}
    t = str(expr or "").replace("×", "*").replace("÷", "/").replace("−", "-").replace("–", "-")
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)
    if not t.strip() or re.search(r"[^\d\s.+\-*/()]", t):
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.operand))
        raise ValueError
    try:
        return ev(ast.parse(t, mode="eval"))
    except (ValueError, SyntaxError, ZeroDivisionError, TypeError):
        return None


def derivable(v, encontrados, max_n=24):
    """True si v sale de dos números de la cita con una operación simple (a/b, a/b×100, Δ%, a−b, a+b, a×b/100)."""
    if not isinstance(v, (int, float)) or isinstance(v, bool) or (abs(v) < 10 and decimales(v) == 0):
        return False
    ns = [t for t, _ in encontrados if t][:max_n]
    tol = 0.5 * 10 ** (-decimales(v)) * 1.0001 + 1e-9
    for a in ns:
        for b in ns:
            if a is b:
                continue
            for r in (a / b, a / b * 100, (a / b - 1) * 100, a - b, a + b, a * b / 100, a * b):
                if abs(abs(r) - abs(v)) <= tol:
                    return True
    return False


RE_FECHA = re.compile(r"\b\d{1,2}(?:\s+de)?\s+(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\w*|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b(?:SE|semana)\s*\d+", re.I)


def factor_unidad(unidad):
    """Escala que declara la unidad de una cifra: «millones de quetzales» → 1e6, «miles» → 1e3."""
    u = str(unidad or "").lower()
    if re.search(r"mil(es de)? millones|millardo", u):
        return 1e9
    if re.search(r"mill[oó]n", u):
        return 1e6
    if re.search(r"\bmiles\b", u):
        return 1e3
    return 1.0


def sueltos(texto, valores, derivables=(), max_entero=12):
    """Números de un texto que no son ninguno de `valores` (redondeados a como se escribieron), ni salen de dos
    `derivables` (los valores titulares, ≤ 60) con una operación simple, ni son año, fecha o entero ≤ max_entero.
    Con escala en el texto («Q64,642.5 millones») vale la cifra en su unidad (`valores` admite (número, factor):
    1e6 para «millones de quetzales»; factor None = número sin unidad conocida, p. ej. un derivado del pie «16,411.9
    M»: vale también tal como se escribió). Para G10
    (tuits) e I7 (informe)."""
    texto = RE_FECHA.sub(" ", texto or "")
    vals = []
    for v in valores:
        x, f = v if isinstance(v, tuple) else (v, 1.0)
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            vals.append((float(x), f))
    der = [(float(v), 0.0) for v in list(derivables)[:60] if isinstance(v, (int, float)) and not isinstance(v, bool) and v]
    tokens = []  # (texto, [(valor, tol)], escala escrita)
    for m in RE_HABLADO.finditer(texto):
        partes = m.group(0).split()
        simple = len(partes) == 2 and re.fullmatch(r"\d+(?:[.,]\d+)?", partes[0])
        v, tol = hablado(m.group(0))
        tokens.append((m.group(0), [(v, tol)], v / float(partes[0].replace(",", ".")) if simple and float(partes[0].replace(",", ".")) else 0.0))
    for m in RE_NUM.finditer(RE_HABLADO.sub(" ", texto)):
        esc = ESCALA.get(re.sub(r"\s+", " ", (m.group(2) or "").strip().lower()), 1.0)
        tokens.append((m.group(0).strip(), [(v * esc, 0.5 * 10 ** (-d) * esc) for v, d in interpretar(m.group(1))], esc))
    out = []
    for tok, interp, esc in tokens:
        if not interp:
            continue
        v0 = interp[0][0]
        if v0.is_integer() and (1900 <= v0 <= 2100 or v0 <= max_entero):
            continue
        ok = False
        for t, tol in interp:
            for x, f in vals:
                if coincide(x, [(t, tol)], escalas=(f or 1.0,)) or (esc not in (0.0, 1.0) and f is None and coincide(x, [(t / esc, tol / esc)], escalas=(1,))):
                    ok = True
                    break
            if ok:
                break
        if ok or (der and any(derivable(t, der, max_n=60) for t, _ in interp if t >= 10 or not t.is_integer())):
            continue
        out.append(tok)
    return out


def leer_texto(ruta):
    p = ruta if os.path.isabs(ruta) else os.path.join(RAIZ, ruta)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "rb") as fh:
            return fh.read(MAX_ARCHIVO).decode("utf-8", "ignore")
    except OSError:
        return None


def dominio(url):
    h = (urlparse(url or "").hostname or "").lower()
    if h.startswith("www."):
        h = h[4:]
    partes = h.split(".")
    n = 3 if any(h.endswith(s) for s in SUF_PUBLICO) else 2
    return ".".join(partes[-n:]) if h else ""


def evidencias(c):
    ev = c.get("evidencia")
    return ev if isinstance(ev, list) else ([ev] if isinstance(ev, dict) else [])


def revisar(sesion, eje=None, max_anios=3, estricto=False):
    F, A = [], []
    hoy = None
    enc = os.path.join(sesion, "encuadre.json")
    if os.path.exists(enc):
        try:
            hoy = int(str(leer(enc).get("fecha") or "")[:4])
        except ValueError:
            hoy = None
    hoy = hoy or _dt.date.today().year
    cifras, origen, ver = {}, {}, {}
    for r in sorted(glob.glob(os.path.join(sesion, "hallazgos_*.json"))):
        e = os.path.basename(r)[10:-5]
        for c in leer(r).get("cifras", []):
            cifras[c["id"]] = c
            origen[c["id"]] = e
    for r in sorted(glob.glob(os.path.join(sesion, "verificacion_*.json"))):
        v = leer(r)
        for it in v.get("items") or v.get("cifras") or []:
            if "id" in it and "veredicto" in it:
                ver[it["id"]] = it

    def en_eje(cid):
        return not eje or cid.startswith(eje + "-") or origen.get(cid) == eje

    def falla(cid, regla, msg):
        F.append({"id": cid, "eje": origen.get(cid), "regla": regla, "detalle": msg})

    def aviso(cid, regla, msg):
        A.append({"id": cid, "eje": origen.get(cid), "regla": regla, "detalle": msg})

    for cid, c in cifras.items():
        if not en_eje(cid):
            continue
        it = ver.get(cid)
        if not it:
            falla(cid, "V-E", "la cifra no tiene veredicto en ningún verificacion_*.json")
            continue
        vd = it.get("veredicto")
        if vd == "no_confirmada":
            continue
        valor = c.get("valor")
        vf = it.get("valor_final", valor)
        # V-A
        textos = [e.get("cita") or "" for e in evidencias(c)]
        nums = []
        for t in textos:
            nums += numeros(t)
        notas = numeros(" ".join(str(x or "") for x in (c.get("nota"), it.get("nota"), it.get("fuente_2"))))
        ok = coincide(vf, nums) or derivable(vf, nums + notas)
        calc = it.get("calculo") or c.get("calculo")
        if calc:
            r = evaluar(calc)
            if r is None:
                falla(cid, "V-A", "calculo ilegible (solo números y + − × ÷ ( )): %r" % calc)
            elif not coincide(vf, [(r, 0.5 * 10 ** (-decimales(vf)))], escalas=(1,)):
                falla(cid, "V-A", "calculo %s da %s, no %s" % (calc, round(r, 6), vf))
            else:
                ok = True
        if not ok:
            for e in evidencias(c):
                if e.get("archivo_local"):
                    tx = leer_texto(e["archivo_local"])
                    if tx and coincide(vf, numeros(tx), escalas=(1, 1e3, 1e6)):
                        ok, donde = True, "archivo"
                        break
        if not ok and (vd == "ajustada" or vf != valor):
            ok = coincide(vf, numeros(it.get("nota") or "") + numeros(it.get("fuente_2") or ""))
            donde = "nota del verificador"
        if not ok:
            msg = "valor_final %s no aparece en la cita ni en el archivo local, ni sale de una operación de sus números; si es derivado, declara calculo (p. ej. «15454/36»)%s" % (vf, " (la cita dice: «%s»)" % textos[0][:120] if textos and textos[0] else " (sin cita)")
            if c.get("tipo") in ("serie", "desglose") and not estricto:
                aviso(cid, "V-A", msg)
            else:
                falla(cid, "V-A", msg)
        # V-B
        if vd == "ajustada" and isinstance(valor, (int, float)) and isinstance(vf, (int, float)) and abs(vf - valor) > 1e-9:
            if not it.get("serie_final") and any(isinstance(p.get("v"), (int, float)) and abs(p["v"] - valor) < 1e-9 for p in c.get("serie") or []):
                falla(cid, "V-B", "ajustada a %s pero la serie conserva el valor viejo %s: añade serie_final al veredicto" % (vf, valor))
            if not it.get("partes_final") and any(isinstance(p.get("valor"), (int, float)) and abs(p["valor"] - valor) < 1e-9 for p in c.get("partes") or []):
                falla(cid, "V-B", "ajustada a %s pero partes[] conserva el valor viejo %s: añade partes_final al veredicto" % (vf, valor))
        # V-C
        ind = it.get("independencia")
        if ind not in ("alta", "baja"):
            falla(cid, "V-C", "independencia ausente o inválida (%r): alta|baja" % ind)
        elif ind == "alta":
            d2 = dominio(it.get("url_2"))
            d1 = {dominio(c.get("url"))} | {dominio(e.get("url")) for e in evidencias(c)}
            if d2 and d2 in d1:
                falla(cid, "V-C", "independencia «alta» con url_2 del mismo dominio que la primaria (%s)" % d2)
        # V-D
        try:
            anio = int(str(c.get("anio") or "")[:4])
        except ValueError:
            anio = None
        if anio and hoy - anio > max_anios:
            aviso(cid, "V-D", "dato de %d, %d años antes de la sesión (%d)" % (anio, hoy - anio, hoy))
        # V-E archivos
        for e in evidencias(c):
            al = e.get("archivo_local")
            if al and leer_texto(al) is None and not os.path.isdir(os.path.join(RAIZ, al)):
                aviso(cid, "V-E", "archivo_local no existe: %s" % al)
    for cid in ver:
        if cid not in cifras and en_eje(cid) and re.match(r"^[a-z]{3}-c\d+$", cid):
            aviso(cid, "V-E", "veredicto sin cifra en hallazgos_*.json")
    return F, A


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sesion")
    ap.add_argument("--eje", help="solo las cifras de ese prefijo o eje")
    ap.add_argument("--json", action="store_true", help="salida JSON {fallas, avisos}")
    ap.add_argument("--max-anios", type=int, default=3)
    ap.add_argument("--estricto", action="store_true", help="V-A de serie/desglose también falla")
    a = ap.parse_args()
    if not os.path.isdir(a.sesion):
        print("ERROR: no existe %s" % a.sesion, file=sys.stderr)
        return 2
    try:
        F, A = revisar(a.sesion, a.eje, a.max_anios, a.estricto)
    except (OSError, ValueError, KeyError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"fallas": F, "avisos": A}, ensure_ascii=False, indent=1))
    else:
        for x in F:
            print("FALLA %s %s: %s" % (x["regla"], x["id"], x["detalle"]))
        for x in A:
            print("AVISO %s %s: %s" % (x["regla"], x["id"], x["detalle"]))
        print("[verificacion] %d falla(s) · %d aviso(s)" % (len(F), len(A)))
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
