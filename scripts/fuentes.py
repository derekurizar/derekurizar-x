#!/usr/bin/env python3
"""Busca en memoria/fuentes.json las fuentes (y series) que casan con un tema.

Normaliza tildes y mayúsculas, separa el tema en palabras de ≥ 4 letras y puntúa
las coincidencias en nombre, categoria y nota (fuentes) o en nombre, unidad, nota
y fuente (series). Imprime compacto:

  fuentes:  nombre · url · categoria · rating · nota (≤ 160)
  --series: nombre · fuente · url · formato · unidad · desde · frecuencia · nota

Sin coincidencias imprime las 8 fuentes de mayor rating de la categoría más
cercana y lo dice. Salida: 0 ok · 1 error · 2 uso incorrecto.

Uso: python3 scripts/fuentes.py --tema "remesas familiares" [--categoria economia] [--series] [--max 12]
"""
import argparse
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORIA = os.path.join(RAIZ, "memoria", "fuentes.json")
# Sufijos que se pelan para que «remesas» case con «remesa» y «migrantes» con «migración».
SUFIJOS = ("ciones", "cion", "mente", "es", "s", "a", "o")


def normalizar(s):
    s = unicodedata.normalize("NFD", str(s or "")).lower()
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def raiz(palabra):
    for suf in SUFIJOS:
        if palabra.endswith(suf) and len(palabra) - len(suf) >= 4:
            return palabra[: -len(suf)]
    return palabra


def palabras_clave(tema):
    """Palabras ≥ 4 letras del tema, en su raíz normalizada, sin duplicados."""
    vistas, out = set(), []
    for w in re.findall(r"[a-z0-9]+", normalizar(tema).replace("_", " ")):
        if len(w) < 4:
            continue
        r = raiz(w)
        if r not in vistas:
            vistas.add(r)
            out.append(r)
    return out


def puntuar(claves, campos):
    """campos: lista de (texto, peso). Suma peso por cada clave presente en el texto."""
    total = 0
    for texto, peso in campos:
        t = normalizar(texto)
        for k in claves:
            if k in t:
                total += peso
    return total


def buscar_fuentes(fuentes, claves, categoria=None):
    res = []
    for f in fuentes:
        if categoria and normalizar(f.get("categoria")) != normalizar(categoria):
            continue
        s = puntuar(claves, [(f.get("nombre"), 3), (f.get("categoria"), 2), (f.get("nota"), 1),
                             (" ".join(f.get("temas") or []), 3), (" ".join(f.get("alias") or []), 2)])
        if s:
            res.append((s, f.get("rating", 0), f))
    res.sort(key=lambda x: (-x[0], -x[1]))
    return [f for _, _, f in res]


def buscar_series(series, claves):
    res = []
    for s in series:
        p = puntuar(claves, [(s.get("nombre"), 3), (s.get("unidad"), 1), (s.get("nota"), 1), (s.get("fuente"), 2)])
        if p:
            res.append((p, s))
    res.sort(key=lambda x: -x[0])
    return [s for _, s in res]


def categoria_cercana(fuentes, claves, categoria=None):
    """La categoría pedida si existe; si no, la que más casa con las claves; si no, la más poblada."""
    cats = {}
    for f in fuentes:
        cats.setdefault(f.get("categoria"), []).append(f)
    if categoria:
        for c in cats:
            if normalizar(c) == normalizar(categoria):
                return c
    mejor = max(cats, key=lambda c: (puntuar(claves, [(c, 1)]), len(cats[c])))
    # Sin señal en las claves, la categoría más útil para datos de Guatemala es economía.
    if puntuar(claves, [(mejor, 1)]) == 0 and "economia" in cats:
        return "economia"
    return mejor


def fuentes_de_series(fuentes, series_hits):
    """Fuentes referenciadas por las series que casaron (por nombre o alias)."""
    out = []
    for s in series_hits:
        ref = normalizar(s.get("fuente") or "")
        if not ref:
            continue
        for f in fuentes:
            nombres = [f.get("nombre") or ""] + list(f.get("alias") or [])
            if any(normalizar(n) and (normalizar(n) in ref or ref in normalizar(n)) for n in nombres) and f not in out:
                out.append(f)
    return out


def fmt_fuente(f):
    nota = re.sub(r"\s+", " ", f.get("nota") or "").strip()
    if len(nota) > 160:
        nota = nota[:159] + "…"
    return "%s · %s · %s · %s%s" % (f.get("nombre"), f.get("url"), f.get("categoria"), f.get("rating"), (" · " + nota) if nota else "")


def fmt_serie(s):
    nota = re.sub(r"\s+", " ", s.get("nota") or "").strip()
    return "%s · %s · %s · %s · %s · %s · %s%s" % (
        s.get("nombre"), s.get("fuente"), s.get("url"), s.get("formato"), s.get("unidad"), s.get("desde", "?"), s.get("frecuencia"), (" · " + nota) if nota else "")


def cargar(ruta=MEMORIA):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tema", required=True, help="texto libre; se usan sus palabras de ≥ 4 letras")
    p.add_argument("--categoria", help="restringe a una categoría de memoria/fuentes.json")
    p.add_argument("--series", action="store_true", help="también las series[] que casan")
    p.add_argument("--max", type=int, default=12)
    p.add_argument("--memoria", default=MEMORIA, help=argparse.SUPPRESS)
    a = p.parse_args()
    if not os.path.exists(a.memoria):
        print("ERROR: no existe %s" % a.memoria, file=sys.stderr)
        return 1
    d = cargar(a.memoria)
    claves = palabras_clave(a.tema)
    if not claves:
        print("ERROR: el tema no tiene palabras de ≥ 4 letras", file=sys.stderr)
        return 2
    fuentes = d.get("fuentes", [])
    hits = buscar_fuentes(fuentes, claves, a.categoria)
    series_hits = buscar_series(d.get("series", []), claves)
    if not hits:
        hits = fuentes_de_series(fuentes, series_hits)
    print("tema: %s · claves: %s" % (a.tema, ", ".join(claves)))
    if hits:
        print("fuentes (%d, se muestran %d):" % (len(hits), min(len(hits), a.max)))
        for f in hits[: a.max]:
            print("  " + fmt_fuente(f))
    else:
        cat = categoria_cercana(fuentes, claves, a.categoria)
        top = sorted((f for f in fuentes if f.get("categoria") == cat), key=lambda f: -f.get("rating", 0))[:8]
        print("sin coincidencias para el tema; las 8 de mayor rating en la categoría más cercana «%s»:" % cat)
        for f in top:
            print("  " + fmt_fuente(f))
    if a.series:
        ss = series_hits
        print("series (%d):" % len(ss) if ss else "series: ninguna casa con el tema")
        for s in ss[: a.max]:
            print("  " + fmt_serie(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
