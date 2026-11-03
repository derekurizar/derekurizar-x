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
             "necropsias", "necropsia", "extorsiones", "extorsión", "armas", "arma", "cárceles", "cárcel", "pandillas",
             # /noticias: sustantivos que salen a diario en las noticias
             "familias", "familia", "viviendas", "vivienda", "casas", "casa", "escuelas", "escuela", "comunidades",
             "comunidad", "aldeas", "aldea", "empresas", "empresa", "plazas", "plaza", "hectáreas", "hectárea",
             "carreteras", "carretera", "unidades", "unidad", "órdenes", "vacunas", "vacuna", "dosis", "camas", "cama",
             "consultas", "consulta", "solicitudes", "solicitud", "licencias", "licencia", "fincas", "finca", "libras",
             "libra", "elecciones", "mesas", "mesa", "municipalidades", "municipalidad", "zonas", "zona", "rutas", "ruta",
             "detenciones", "detención", "operaciones", "quejas", "queja", "jornadas", "madres", "madre", "pruebas",
             "prueba", "plantas", "planta", "obras", "obra", "becas", "beca", "multas", "multa",
             "motos", "moto", "motocicletas", "motocicleta"}
# Género del sustantivo que sigue a la cifra (m046): manda FEMENINOS (lista de arriba), luego MASCULINOS; si no
# está en ninguna, la regla general: -a/-as femenino (salvo palabras con mayúscula: nombres propios o inicio de
# oración), -ción/-sión/-dad/-tad/-tud/-umbre femenino, y lo demás masculino.
MASCULINOS = {"día", "días", "mapa", "mapas", "problema", "problemas", "programa", "programas", "sistema", "sistemas",
              "tema", "temas", "idioma", "idiomas", "clima", "climas", "planeta", "planetas", "poema", "poemas",
              "esquema", "esquemas", "dilema", "dilemas", "drama", "dramas", "diploma", "diplomas", "síntoma", "síntomas",
              "trauma", "traumas", "fantasma", "fantasmas", "aroma", "aromas", "lema", "lemas", "enigma", "enigmas",
              "diagrama", "diagramas", "telegrama", "telegramas", "crucigrama", "crucigramas", "cometa", "cometas",
              "tranvía", "tranvías", "sofá", "sofás", "policía", "policías", "atleta", "atletas", "colega", "colegas",
              "homicida", "homicidas", "pediatra", "pediatras", "psiquiatra", "psiquiatras", "astronauta", "astronautas",
              "pirata", "piratas", "guía", "guías", "km", "kg", "pp", "ha",
              "aviones", "avión", "camiones", "camión", "embriones", "embrión",
              # palabras de función que acaban en -a (no son sustantivos; antes ya iban en masculino)
              "para", "hasta", "contra", "hacia", "nunca", "ya", "ahora", "cada", "entonces", "fuera", "afuera",
              "arriba", "abajo", "encima", "apenas", "mientras", "otra", "otras", "esta", "estas", "esa", "esas",
              "era", "eran", "estaba", "estaban", "toda", "todas"}
FEMENINOS_EXTRA = {"mano", "manos", "foto", "fotos", "fotografías", "radio", "radios", "flor", "flores", "crisis",
                   "tesis", "hipótesis", "ley", "leyes", "noche", "noches", "tarde", "tardes", "calle", "calles",
                   "clase", "clases", "parte", "partes", "fuente", "fuentes", "imagen", "imágenes", "razón", "razones",
                   "red", "redes", "sede", "sedes", "llave", "llaves", "nave", "naves", "muerte", "orden", "sangre"}
SUFIJOS_FEMENINOS = ("ción", "ciones", "sión", "siones", "xión", "xiones", "dad", "dades", "tad", "tades", "tud", "tudes",
                     "umbre", "umbres")
UNIDADES_ABREV = {"kg": "kilogramos", "km²": "kilómetros cuadrados", "km": "kilómetros", "kWh": "kilovatios hora",
                  "ha": "hectáreas", "pp": "puntos porcentuales"}


def genero_de(palabra):
    """'f' o 'm' según el sustantivo que sigue a la cifra (FEMENINOS manda; luego MASCULINOS; luego la regla)."""
    w = palabra.lower()
    if not w:
        return "m"
    if w in FEMENINOS or w in FEMENINOS_EXTRA:
        return "f"
    if w in MASCULINOS:
        return "m"
    if palabra[0].isupper():  # nombre propio o inicio de oración: no se adivina
        return "m"
    if w.endswith(("a", "as")) or w.endswith(SUFIJOS_FEMENINOS):
        return "f"
    return "m"


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
    # con decimales la parte entera va en masculino: «1.5 veces» → «uno punto cinco veces» (m017)
    txt = entero_a_palabras(entero, "m" if decimales else genero, apocope and not decimales)
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
RE_MONEDA_TRAS = re.compile(r"\s+(dólares|dólar|quetzales|quetzal)\b")   # «1.15 dólares»: la moneda escrita después
RE_UNIDAD = re.compile(r"\s*(%s)(?![\w²])" % "|".join(re.escape(u) for u in sorted(UNIDADES_ABREV, key=len, reverse=True)))
NO_SUSTANTIVO = {"de", "a", "y", "en", "frente", "por", "con", "o", "al", "del", "mil", "millones", "millón"}
AVISOS = []  # cifras cuyo género cambia la lectura y no tienen sustantivo ni marca
NOTAS = []   # cambios de la voz que no bloquean el gate (letra suelta dicha por su nombre)
RE_ANTES_ANIO = re.compile(r"\b(en|de|del|desde|hasta)\s+$", re.I)


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
        ent, cts = int(entero_txt), int(dec)
        centavos = "%s %s" % (_numero(str(cts), "m", True), "centavo" if cts == 1 else "centavos")
        if ent == 0:  # «US$0.50» → «cincuenta centavos»
            return centavos
        base = "%s %s" % (_numero(entero_txt, "m", True), singular if ent == 1 else nombre)
        return base if cts == 0 else base + " con " + centavos
    return "%s %s" % (_numero(bruto, "m", True), singular if bruto == "1" else nombre)


# abreviaturas sueltas (sin cifra delante): «por kWh» → «por kilovatio hora»
ABREV_SUELTAS = {"kWh": ("kilovatio hora", "kilovatios hora")}
# letra mayúscula suelta tras una palabra con mayúscula: «Sputnik V» → «Sputnik uve», «Plan B» → «Plan be» (m027)
NOMBRES_LETRA = {"B": "be", "C": "ce", "D": "de", "F": "efe", "G": "ge", "H": "hache", "J": "jota", "K": "ka",
                 "L": "ele", "M": "eme", "N": "ene", "Ñ": "eñe", "P": "pe", "Q": "cu", "R": "erre", "S": "ese",
                 "T": "te", "V": "uve", "W": "uve doble", "X": "equis", "Z": "zeta"}
# (las vocales y la Y quedan fuera: se leen como suenan o son la conjunción de una oración)
# tras estos nombres la letra es un número romano de rey, papa o siglo: «Carlos V», «León X»
REGIOS = {"carlos", "felipe", "fernando", "juan", "pablo", "pío", "pio", "benedicto", "león", "leon", "luis", "enrique",
          "isabel", "alfonso", "jorge", "eduardo", "gregorio", "clemente", "inocencio", "urbano", "bonifacio",
          "alejandro", "sixto", "pedro", "jaime", "sancho", "ramiro", "enrique", "guillermo", "federico", "napoleón",
          "siglo", "siglos", "capítulo", "tomo", "fase"}
RE_SUELTA = re.compile(r"(?<![\w])(%s)(?![\w])|(?<=\w )([%s])(?![\w'’-]|\.\w)" % (
    "|".join(ABREV_SUELTAS), "".join(NOMBRES_LETRA)))
RE_PREVIA = re.compile(r"([A-ZÁÉÍÓÚÑ][\wáéíóúñü]*) $")


def _letra_suelta(t, m):
    """(palabra previa, nombre en español de la letra) si la letra sigue a una palabra con mayúscula y no es un
    número romano tras un nombre regio; si no, None."""
    previa = RE_PREVIA.search(t[:m.start()])
    if not previa:
        return None
    letra = m.group(2)
    if letra in "IVXLCDM" and previa.group(1).lower() in REGIOS:
        return None
    return previa.group(1), NOMBRES_LETRA[letra]


def _texto(t):
    """Segmentos de texto sin cifras; las abreviaturas sueltas son segmentos propios (p ≠ v)."""
    out, pos = [], 0
    for m in RE_SUELTA.finditer(t):
        if m.group(2):
            letra = _letra_suelta(t, m)
            if letra is None:
                continue
        if m.start() > pos:
            out.append({"p": t[pos:m.start()], "v": t[pos:m.start()], "num": False})
        if m.group(2):
            previa, dicho = letra
            out.append({"p": m.group(2), "v": dicho, "num": False})
            NOTAS.append("letra suelta: «%s %s» se dice «%s %s»" % (previa, m.group(2), previa, dicho))
        else:
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
        tras = RE_MONEDA_TRAS.match(resto) if len(dec) == 2 and not (moneda or es_pct or rango) else None
        if tras:  # «1.15 dólares» se dice como «US$1.15»: «un dólar con quince centavos»
            dicho = _dinero(bruto, "Q" if tras.group(1).startswith("quetzal") else "US$", None)
            fin += tras.end()
        elif moneda:
            esc = RE_ESCALA.match(resto)
            dicho = _dinero(bruto, moneda, esc.group(1) if esc else None)
            fin += esc.end() if esc else 0
        elif es_fecha and entero == 1:
            dicho = "primero"
        else:
            sig = RE_SIGUE.match(resto[rango.end():] if rango else resto)
            siguiente_orig = sig.group(1) if sig else ""
            siguiente = siguiente_orig.lower()
            # un año (4 cifras sin coma) nunca se apocopa: «en 2021 subió» → «dos mil veintiuno subió»; tras
            # «en/de/del/desde/hasta» también los anteriores a 1900: «en 1821 llegaron» → «… veintiuno …» (m021)
            es_anio = "," not in bruto and not dec and (
                1900 <= entero <= 2100
                or (len(entero_txt) == 4 and 1000 <= entero < 1900 and siguiente not in FEMENINOS
                    and RE_ANTES_ANIO.search(texto[:m.start()]) is not None))
            genero = genero_forzado or ("m" if es_anio else genero_de(siguiente_orig))
            sustantivo = bool(siguiente) and not es_pct and not es_fecha and not es_anio and siguiente not in NO_SUSTANTIVO
            dicho = _numero(bruto, genero, sustantivo and not rango)
            anio = es_anio or (1900 <= entero <= 2100 and not dec)
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
    ("En 2021 subió", "En dos mil veintiuno subió"),
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
    ("costaba 1.15 dólares en 1979", "costaba un dólar con quince centavos en mil novecientos setenta y nueve"),
    ("3.75 quetzales", "tres quetzales con setenta y cinco centavos"),
    ("US$0.50 por litro", "cincuenta centavos por litro"),
    ("Q0.01", "un centavo"),
    ("2.5 millones de dólares", "dos punto cinco millones de dólares"),
    ("entre 2016–2026", "entre dos mil dieciséis y dos mil veintiséis"),
    ("de 2016–2026", "de dos mil dieciséis a dos mil veintiséis"),
    ("3.3 millones de estudiantes", "tres punto tres millones de estudiantes"),
    ("subió 5.2 pp en un año", "subió cinco punto dos puntos porcentuales en un año"),
    # m017: con decimales, la parte entera en masculino
    ("1.5 veces más", "uno punto cinco veces más"),
    ("21.3 toneladas", "veintiuno punto tres toneladas"),
    # m021: año tras «en/de/del» sin apócope
    ("aceptó que en 2021 llegaran", "aceptó que en dos mil veintiuno llegaran"),
    ("en 1821 llegaron", "en mil ochocientos veintiuno llegaron"),
    ("del 2031 al 2041", "del dos mil treinta y uno al dos mil cuarenta y uno"),
    ("en 2021 Guatemala", "en dos mil veintiuno Guatemala"),
    # m046: género por regla (-a/-as femenino) con excepciones
    ("379,021 motos", "trescientas setenta y nueve mil veintiuna motos"),
    ("21 bicicletas", "veintiuna bicicletas"),
    ("21 días", "veintiún días"),
    ("201 programas", "doscientos un programas"),
    ("21 manos", "veintiuna manos"),
    ("21 instituciones", "veintiuna instituciones"),
    ("21 policías", "veintiún policías"),
    ("21 camiones", "veintiún camiones"),
    # m027: letra mayúscula suelta tras nombre propio
    ("la vacuna Sputnik V llegó", "la vacuna Sputnik uve llegó"),
    ("el Plan B.", "el Plan be."),
    ("Carlos V reinó", "Carlos V reinó"),
    ("Pollo Campero S.A.", "Pollo Campero S.A."),
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
    NOTAS.clear()
    pantalla, voz, conv = convertir(a.texto)
    print("PANTALLA:", pantalla)
    print("VOZ:     ", voz)
    for b, d in conv:
        print("  %s → %s" % (b, d))
    for x in AVISOS:
        print("AVISO:", x)
    for x in NOTAS:
        print("NOTA: ", x)
    return 1 if AVISOS else 0


if __name__ == "__main__":
    sys.exit(main())
