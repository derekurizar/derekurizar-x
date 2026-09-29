#!/usr/bin/env python3
"""Peso de un texto según las reglas de X (twitter-text), sin dependencias.

Reglas (simplificación fiel de twitter-text v3):
  - El texto se normaliza a NFC.
  - Cada URL pesa 23 (t.co), sea https://…, www.… o un dominio pelado
    conocido (mem.gob.gt, banguat.gob.gt, eia.gov…).
  - Los puntos de código en 0–4351, 8192–8205, 8208–8223 y 8242–8247 pesan 1
    (latín, tildes, ñ, signos, guiones largos «—», comillas tipográficas…).
  - Todo lo demás pesa 2 («…», «→», CJK, emoji).
  - Un emoji compuesto (base + FE0F / ZWJ + siguiente, tono de piel 1F3FB–1F3FF,
    keycap 20E3, par de indicadores regionales 🇬🇹) cuenta como UNO y pesa 2.

Uso:
  python3 scripts/contar_x.py "texto"           # imprime el peso
  echo "texto" | python3 scripts/contar_x.py    # idem desde stdin
  python3 scripts/contar_x.py --vectores        # valida scripts/pruebas/contar_x.json
Salida: 0 ok · 1 algún vector falla · 2 uso incorrecto

La misma lógica vive en scripts/contar_x.js (pesoX); ambos deben coincidir en
todos los vectores de scripts/pruebas/contar_x.json.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORES = os.path.join(RAIZ, "scripts", "pruebas", "contar_x.json")

PESO_URL = 23
TLDS = "com|gt|org|net|io|edu|gov|mx|sv|hn|es|info|co"
# (?<!\w) equivale a \b aquí (la URL siempre arranca con carácter de palabra)
# y se traduce sin ambigüedad a JS: (?<![\p{L}\p{N}\p{M}_]).
RE_URL = re.compile(
    r"https?://\S+|www\.\S+|(?<!\w)[a-z0-9-]+(\.[a-z0-9-]+)*\.(%s)(/\S*)?" % TLDS, re.I)
RANGOS_1 = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))

VS16, ZWJ, KEYCAP = 0xFE0F, 0x200D, 0x20E3


def _es_tono(cp):
    return 0x1F3FB <= cp <= 0x1F3FF


def _es_regional(cp):
    return 0x1F1E6 <= cp <= 0x1F1FF


def _peso_cp(cp):
    for a, b in RANGOS_1:
        if a <= cp <= b:
            return 1
    return 2


def _peso_texto_plano(texto):
    """Peso de un tramo sin URLs: agrupa emoji compuestos y suma por punto de código."""
    cps = [ord(c) for c in texto]
    i, n, total = 0, len(cps), 0
    while i < n:
        j = i + 1
        if _es_regional(cps[i]) and j < n and _es_regional(cps[j]):
            j += 1  # bandera: par de indicadores regionales
        while j < n:
            if cps[j] in (VS16, KEYCAP) or _es_tono(cps[j]):
                j += 1
            elif cps[j] == ZWJ and j + 1 < n:
                j += 2  # ZWJ + siguiente elemento de la secuencia
            else:
                break
        total += 2 if j - i > 1 else _peso_cp(cps[i])
        i = j
    return total


def peso_x(texto):
    """Peso del texto según X. Devuelve un entero (el límite es 280)."""
    texto = unicodedata.normalize("NFC", texto or "")
    total, pos = 0, 0
    for m in RE_URL.finditer(texto):
        total += _peso_texto_plano(texto[pos:m.start()]) + PESO_URL
        pos = m.end()
    return total + _peso_texto_plano(texto[pos:])


def correr_vectores(ruta):
    with open(ruta, encoding="utf-8") as fh:
        vectores = json.load(fh)
    fallos = 0
    for v in vectores:
        got = peso_x(v["texto"])
        ok = got == v["peso"]
        fallos += not ok
        print("%s %3d (esperado %3d)  %s" % ("OK   " if ok else "FALLO", got, v["peso"], json.dumps(v["texto"], ensure_ascii=False)[:70]))
    print("[contar_x] %d vectores · %d fallo(s)" % (len(vectores), fallos))
    return 1 if fallos else 0


def main():
    p = argparse.ArgumentParser(description="Peso de un texto según X (280 = límite)")
    p.add_argument("texto", nargs="?", help="texto a pesar (si falta, se lee stdin)")
    p.add_argument("--vectores", nargs="?", const=VECTORES, metavar="RUTA", help="valida los vectores de prueba (default scripts/pruebas/contar_x.json)")
    a = p.parse_args()
    if a.vectores:
        return correr_vectores(a.vectores)
    texto = a.texto if a.texto is not None else sys.stdin.read()
    if a.texto is None and texto.endswith("\n"):
        texto = texto[:-1]  # echo añade un salto final que no forma parte del tuit
    print(peso_x(texto))
    return 0


if __name__ == "__main__":
    sys.exit(main())
