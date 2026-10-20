#!/usr/bin/env python3
"""Cifras escritas con dígitos → texto hablado en español (Guatemala) para la locución de /video.

- miles con coma y decimal con punto («8,402.4» → «ocho mil cuatrocientos dos punto cuatro»)
- «%» → «por ciento»; «1 de enero» → «primero de enero»; años como número; «2016–2026» → «… a …»
- concordancia: «26,955 personas» → «veintiséis mil novecientas cincuenta y cinco personas»,
  «21 denuncias» → «veintiuna denuncias»; con el sustantivo elidido se marca {22,981:f} o {504:m}
- dinero: «Q75 mil millones» → «setenta y cinco mil millones de quetzales», «Q1.51» → «un quetzal
  con cincuenta y un centavos», «US$1,200 millones» → «mil doscientos millones de dólares»
- unidades abreviadas detrás de la cifra: kg, km, km², kWh, ha, pp

Cada conversión se comprueba de vuelta (palabras → número); si no coincide, ValueError. Una cifra cuyo
género cambia la lectura y no tiene sustantivo ni marca queda en AVISOS (el gate V3 la rechaza).

Uso: numeros_es.py --prueba | numeros_es.py "texto con 8,402.4 kg"   (exit 0 ok · 1 fallo · 2 uso)
"""
import argparse
import re
import sys

UNIDADES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
            "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
            "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis",
            "veintisiete", "veintiocho", "veintinueve"]
DECENAS = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa"}
CENTENAS = {100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos", 500: "quinientos",
            600: "seiscientos", 700: "setecientos", 800: "ochocientos", 900: "novecientos"}
MESES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre"
FEMENINOS = {"personas", "persona", "denuncias", "denuncia", "víctimas", "víctima", "alertas", "alerta", "capturas",
             "captura", "toneladas", "tonelada", "muertes", "muerte", "mujeres", "mujer", "niñas", "niña", "horas",
             "hora", "semanas", "semana", "veces", "vez", "gráficas", "gráfica", "sentencias", "sentencia",
             "necropsias", "necropsia", "extorsiones", "extorsión", "armas", "arma", "cárceles", "cárcel", "pandillas"}
UNIDADES_ABREV = {"kg": "kilogramos", "km²": "kilómetros cuadrados", "km": "kilómetros", "kWh": "kilovatios hora",
                  "ha": "hectáreas", "pp": "puntos porcentuales"}


def _menor_cien(n, genero, apocope):
    if n < 30:
        if n == 1:
            return "un" if apocope and genero != "f" else ("una" if genero == "f" else "uno")
        if n == 21:
            return "veintiún" if apocope and genero != "f" else ("veintiuna" if genero == "f" else "veintiuno")
        return UNIDADES[n]
    d, u = divmod(n, 10)
    base = DECENAS[d * 10]
    return base if u == 0 else base + " y " + _menor_cien(u, genero, apocope)


def _menor_mil(n, genero, apocope):
    if n == 100:
        return "cien"
    c, r = divmod(n, 100)
    partes = []
    if c:
        cen = CENTENAS[c * 100]
        if genero == "f" and c > 1:
            cen = cen[:-2] + "as"
        partes.append(cen)
    if r:
        partes.append(_menor_cien(r, genero, apocope))
    return " ".join(partes)


def entero_a_palabras(n, genero="m", apocope=False):
    """apocope=True cuando sigue un sustantivo: «un caso», «veintiún policías»."""
    if n == 0:
        return "cero"
    if n >= 10 ** 9:
        raise ValueError("número demasiado grande: %d" % n)
    millones, resto = divmod(n, 10 ** 6)
    miles, unidades = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append("un millón" if millones == 1 else _menor_mil(millones, "m", True) + " millones")
    if miles:
        # «mil», «veintiún mil», «doscientas mil personas»: las centenas concuerdan; el 1 final se apocopa
        partes.append("mil" if miles == 1 else _menor_mil(miles, genero, True) + " mil")
    if unidades:
        partes.append(_menor_mil(unidades, genero, apocope))
    return " ".join(partes)


def decimal_a_palabras(entero, decimales, genero="m", apocope=False):
    txt = entero_a_palabras(entero, genero, apocope and not decimales)
    if decimales:
        if decimales.startswith("0"):
            txt += " punto " + " ".join(UNIDADES[int(c)] for c in decimales)
        else:
            txt += " punto " + entero_a_palabras(int(decimales))
    return txt


# ---------- palabras → número (para la comprobación de ida y vuelta) ----------
_VAL = {w: i for i, w in enumerate(UNIDADES)}
_VAL.update({"un": 1, "una": 1, "veintiún": 21, "veintiuna": 21, "cien": 100})
_VAL.update({v: k for k, v in DECENAS.items()})
for k, v in CENTENAS.items():
    _VAL[v] = k
    _VAL[v[:-2] + "as"] = k


def palabras_a_numero(frase):
    toks = [t for t in frase.lower().split() if t != "y"]
    if "punto" in toks:
        i = toks.index("punto")
        ent, dec = toks[:i], toks[i + 1:]
    else:
        ent, dec = toks, []
    total, grupo = 0, 0
    for t in ent:
        if t == "mil":
            total += (grupo or 1) * 1000
            grupo = 0
        elif t in ("millón", "millones"):
            total += (grupo or 1) * 10 ** 6
            grupo = 0
        else:
            grupo += _VAL[t]
    total += grupo
    if not dec:
        return str(total)
    if dec[0] == "cero":
        return "%d.%s" % (total, "".join(str(_VAL[t]) for t in dec))
    return "%d.%s" % (total, palabras_a_numero(" ".join(dec)))


# ---------- texto ----------
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
RE_TOKEN = re.compile(
    r"\{(?P<marca>\d{1,3}(?:,\d{3})*(?:\.\d+)?):(?P<g>[mf])\}"
    r"|(?<![\w.,$])(?P<mon>Q|US\$)?(?P<num>" + NUM + r")(?![\d])(?P<pct>\s*%)?")
RE_SIGUE = re.compile(r"\s+([\wáéíóúñü²]+)")
RE_RANGO = re.compile(r"\s*[–-]\s*(" + NUM + r")(?![\d])")
RE_ESCALA = re.compile(r"\s+(mil millones|millones|millón)\b")
RE_UNIDAD = re.compile(r"\s*(%s)(?![\w²])" % "|".join(re.escape(u) for u in sorted(UNIDADES_ABREV, key=len, reverse=True)))
NO_SUSTANTIVO = {"de", "a", "y", "en", "frente", "por", "con", "o", "al", "del", "mil", "millones", "millón"}
AVISOS = []  # cifras cuyo género cambia la lectura y no tienen sustantivo ni marca


def _numero(bruto, genero, apocope):
    """«8,402.4» → palabras, con comprobación de ida y vuelta."""
    entero_txt, _, dec = bruto.replace(",", "").partition(".")
    dicho = decimal_a_palabras(int(entero_txt), dec, genero, apocope)
    esperado = str(int(entero_txt)) + ("." + dec if dec else "")
    vuelta = palabras_a_numero(dicho)
    if vuelta != esperado:
        raise ValueError("ida y vuelta falló: %s → «%s» → %s" % (bruto, dicho, vuelta))
    return dicho


def _dinero(bruto, moneda, escala):
    nombre, singular = ("quetzales", "quetzal") if moneda == "Q" else ("dólares", "dólar")
    entero_txt, _, dec = bruto.replace(",", "").partition(".")
    if escala:  # «Q75 mil millones» → «setenta y cinco mil millones de quetzales»
        return "%s %s de %s" % (_numero(bruto, "m", True), escala, nombre)
    if len(dec) == 2:  # «Q1.51» → «un quetzal con cincuenta y un centavos»
        ent = int(entero_txt)
        base = "%s %s" % (_numero(entero_txt, "m", True), singular if ent == 1 else nombre)
        return base if dec == "00" else base + " con %s centavos" % _numero(str(int(dec)), "m", True)
    return "%s %s" % (_numero(bruto, "m", True), singular if bruto == "1" else nombre)


# abreviaturas sueltas (sin cifra delante): «por kWh» → «por kilovatio hora»
ABREV_SUELTAS = {"kWh": ("kilovatio hora", "kilovatios hora")}
RE_SUELTA = re.compile(r"(?<![\w])(%s)(?![\w])" % "|".join(ABREV_SUELTAS))


def _texto(t):
    """Segmentos de texto sin cifras; las abreviaturas sueltas son segmentos propios (p ≠ v)."""
    out, pos = [], 0
    for m in RE_SUELTA.finditer(t):
        if m.start() > pos:
            out.append({"p": t[pos:m.start()], "v": t[pos:m.start()], "num": False})
        sing, plur = ABREV_SUELTAS[m.group(1)]
        out.append({"p": m.group(1), "v": sing if re.search(r"\bpor\s*$", t[:m.start()]) else plur, "num": False})
        pos = m.end()
    if pos < len(t):
        out.append({"p": t[pos:], "v": t[pos:], "num": False})
    return out


def segmentos(texto):
    """Parte el texto en [{p: pantalla, v: voz, num: bool}]. Un segmento numérico abarca la cifra con su
    moneda, escala, rango, «%» y unidad («Q75 mil millones», «2016–2026», «8,402.4 kg»), para que la
    alineación por palabra lo trate como una sola unidad en pantalla (igual que cualquier segmento con p ≠ v)."""
    segs, pos = [], 0
    for m in RE_TOKEN.finditer(texto):
        if m.start() < pos:
            continue
        if m.start() > pos:
            segs += _texto(texto[pos:m.start()])
        bruto = m.group("marca") or m.group("num")
        genero_forzado, moneda, es_pct = m.group("g"), m.group("mon"), bool(m.group("pct"))
        fin = m.end()
        resto = texto[fin:]
        entero_txt, _, dec = bruto.replace(",", "").partition(".")
        entero = int(entero_txt)
        es_fecha = re.match(r"\s+de\s+(%s)\b" % MESES, resto, re.I) is not None and not dec and not moneda
        rango = None if es_pct or moneda else RE_RANGO.match(resto)
        if moneda:
            esc = RE_ESCALA.match(resto)
            dicho = _dinero(bruto, moneda, esc.group(1) if esc else None)
            fin += esc.end() if esc else 0
        elif es_fecha and entero == 1:
            dicho = "primero"
        else:
            sig = RE_SIGUE.match(resto[rango.end():] if rango else resto)
            siguiente = sig.group(1).lower() if sig else ""
            genero = genero_forzado or ("f" if siguiente in FEMENINOS else "m")
            sustantivo = bool(siguiente) and not es_pct and not es_fecha and siguiente not in NO_SUSTANTIVO
            dicho = _numero(bruto, genero, sustantivo and not rango)
            anio = 1900 <= entero <= 2100 and not dec
            if not genero_forzado and not sustantivo and not es_pct and not anio \
                    and decimal_a_palabras(entero, dec, "f") != decimal_a_palabras(entero, dec, "m"):
                AVISOS.append("género ambiguo: «%s» sin sustantivo detrás; márcalo {%s:f} o {%s:m}" % (bruto, bruto, bruto))
            if rango:  # «2016–2026» → «dos mil dieciséis a dos mil veintiséis» («entre … y …»)
                une = " y " if re.search(r"\bentre\s*$", texto[:m.start()], re.I) else " a "
                dicho += une + _numero(rango.group(1), genero, sustantivo)
                fin += rango.end()
        if es_pct:
            dicho += " por ciento"
        uni = RE_UNIDAD.match(texto[fin:])
        if uni:
            dicho += " " + UNIDADES_ABREV[uni.group(1)]
            fin += uni.end()
        p = texto[m.start():fin]
        if m.group("marca"):
            p = bruto + texto[m.end():fin]
        segs.append({"p": p, "v": dicho, "num": True})
        pos = fin
    if pos < len(texto):
        segs += _texto(texto[pos:])
    return segs


def convertir(texto):
    """Devuelve (texto_pantalla, texto_voz, conversiones [(pantalla, dicho)])."""
    segs = segmentos(texto)
    return ("".join(s["p"] for s in segs), "".join(s["v"] for s in segs),
            [(s["p"], s["v"]) for s in segs if s["num"]])


CASOS = [
    ("8,402.4 kilogramos", "ocho mil cuatrocientos dos punto cuatro kilogramos"),
    ("8,402.4 kg de cocaína", "ocho mil cuatrocientos dos punto cuatro kilogramos de cocaína"),
    ("1,596.2.", "mil quinientos noventa y seis punto dos."),
    ("el 66.7% de", "el sesenta y seis punto siete por ciento de"),
    ("26,955 personas", "veintiséis mil novecientas cincuenta y cinco personas"),
    ("{22,981:f} en 2025", "veintidós mil novecientas ochenta y una en dos mil veinticinco"),
    ("del 1 de enero al 12 de julio", "del primero de enero al doce de julio"),
    ("al 28 de julio", "al veintiocho de julio"),
    ("21 denuncias", "veintiuna denuncias"),
    ("21 casos", "veintiún casos"),
    ("201 personas", "doscientas una personas"),
    ("100 mil habitantes", "cien mil habitantes"),
    ("2.05 puntos", "dos punto cero cinco puntos"),
    ("el 4% terminó", "el cuatro por ciento terminó"),
    ("de {504:m} a {378:m}.", "de quinientos cuatro a trescientos setenta y ocho."),
    ("20 policías", "veinte policías"),
    ("1,000,000", "un millón"),
    ("Q75 mil millones en nueve meses", "setenta y cinco mil millones de quetzales en nueve meses"),
    ("Q1.51 por kWh", "un quetzal con cincuenta y un centavos por kilovatio hora"),
    ("Q2.12 en Occidente", "dos quetzales con doce centavos en Occidente"),
    ("US$1,200 millones", "mil doscientos millones de dólares"),
    ("entre 2016–2026", "entre dos mil dieciséis y dos mil veintiséis"),
    ("de 2016–2026", "de dos mil dieciséis a dos mil veintiséis"),
    ("3.3 millones de estudiantes", "tres punto tres millones de estudiantes"),
    ("subió 5.2 pp en un año", "subió cinco punto dos puntos porcentuales en un año"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("texto", nargs="?")
    ap.add_argument("--prueba", action="store_true", help="corre los casos de prueba")
    a = ap.parse_args()
    if a.prueba:
        mal = 0
        for entrada, esperado in CASOS:
            try:
                _, voz, _ = convertir(entrada)
            except ValueError as e:
                voz = "ERROR " + str(e)
            ok = voz == esperado
            mal += not ok
            print(("ok   " if ok else "FALLA"), entrada, "→", voz, "" if ok else "(esperado: %s)" % esperado)
        print("%d/%d casos ok" % (len(CASOS) - mal, len(CASOS)))
        return 1 if mal else 0
    if not a.texto:
        ap.print_usage()
        return 2
    AVISOS.clear()
    pantalla, voz, conv = convertir(a.texto)
    print("PANTALLA:", pantalla)
    print("VOZ:     ", voz)
    for b, d in conv:
        print("  %s → %s" % (b, d))
    for x in AVISOS:
        print("AVISO:", x)
    return 1 if AVISOS else 0


if __name__ == "__main__":
    sys.exit(main())
