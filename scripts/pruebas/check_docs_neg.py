#!/usr/bin/env python3
"""Negativos de scripts/check_docs.py: cada regla D0–D7 muerde sobre una raíz mínima fabricada en un temporal.

Uso: python3 scripts/pruebas/check_docs_neg.py   (exit 0 ok · 1 falla)
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check_docs as C  # noqa: E402


def escribir(raiz, ruta, texto):
    p = os.path.join(raiz, ruta)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(texto)


def raiz_sana(base):
    """Una raíz mínima que pasa D0–D3 y D5–D7 (D4, las anclas, se prueba aparte sobre la raíz real)."""
    r = tempfile.mkdtemp(dir=base)
    escribir(r, "CLAUDE.md", "# Prueba\n\nLee `referencias/flujo-x.md` y «Reglas» en `referencias/flujo-x.md`. Corre `scripts/uno.py`.\n")
    escribir(r, "referencias/flujo-x.md", "# X\n\n## Reglas\n\n`V99` y `cosa.json` viven aquí.\n")
    escribir(r, "referencias/mapa.md", "`/hola` · `rol-a` · `flujo.js` · `uno.py`\n")
    escribir(r, "referencias/roles/rol-a.md", "# rol\n\nModos en `referencias/roles/rol-a/`: `modo.md`.\n")
    escribir(r, "referencias/roles/rol-a/modo.md", "# modo\n")
    escribir(r, ".claude/commands/hola.md", "hola\n")
    escribir(r, ".claude/agents/rol-a.md", "rol\n")
    escribir(r, ".claude/workflows/flujo.js", "const x = guia('rol-a', 'modo')\n")
    escribir(r, "scripts/uno.py", "")
    escribir(r, C.CONGELADOS, "# congelados\nV99\ncosa.json\n")
    escribir(r, C.RETIRADOS, "# retirados\n")
    return r


def fallas(r, sin_d4=True):
    D = C.docs(r)
    f = C.d0(r, D)[0] + C.d1(D) + C.d2(r, D) + C.d3(r, D) + C.d5(r) + C.d6(D) + C.d7(r, D)
    return f + ([] if sin_d4 else C.d4(r))


def main():
    base = tempfile.mkdtemp(prefix="check_docs_")
    try:
        r = raiz_sana(base)
        assert fallas(r) == [], fallas(r)
        casos = [
            ("D0", lambda r: escribir(r, "referencias/flujo-x.md", "# X\n\n## Reglas\n\nsolo `cosa.json`.\n")),      # V99 se perdió
            ("D1", lambda r: escribir(r, "CLAUDE.md", "palabra " * (C.PALABRAS_MAX + 1))),
            ("D2", lambda r: escribir(r, "CLAUDE.md", "Lee `referencias/flujo-que-no-existe.md`.\n")),
            ("D3", lambda r: escribir(r, "CLAUDE.md", "Mira «Sección fantasma» en `referencias/flujo-x.md`.\n")),
            ("D5", lambda r: escribir(r, "scripts/dos.py", "")),                                                      # script que el mapa no lista
            ("D6", lambda r: escribir(r, "referencias/flujo-x.md", "# X\n\n## Reglas\n\n`V99` `cosa.json`. Corre /noticias cada día.\n")),
            ("D7", lambda r: escribir(r, "referencias/roles/rol-a/otro.md", "# otro\n")),                             # modo sin citar en el núcleo
            ("D7", lambda r: escribir(r, ".claude/workflows/flujo.js", "const x = guia('rol-a', 'fantasma')\n")),     # guia() a un archivo que no existe
        ]
        for codigo, romper in casos:
            r = raiz_sana(base)
            romper(r)
            f = fallas(r)
            assert any(x.startswith(codigo + " ") for x in f), (codigo, f)
        # un flujo retirado se puede nombrar si la línea dice que se retiró
        r = raiz_sana(base)
        escribir(r, "referencias/flujo-x.md", "# X\n\n## Reglas\n\n`V99` `cosa.json`. /noticias se retiró el 2026-11-14.\n")
        assert fallas(r) == [], fallas(r)
        # un identificador retirado con su motivo no cuenta; sin motivo, sí
        r = raiz_sana(base)
        escribir(r, "referencias/flujo-x.md", "# X\n\n## Reglas\n\nsolo `cosa.json`.\n")
        escribir(r, C.RETIRADOS, "V99\tera de un flujo retirado\n")
        assert fallas(r) == [], fallas(r)
        escribir(r, C.RETIRADOS, "V99\n")
        assert any("sin motivo" in x for x in fallas(r)), fallas(r)
        # D4 sobre la raíz real: todas las anclas están donde les toca
        assert C.d4(C.RAIZ) == [], C.d4(C.RAIZ)
        print("[check_docs · negativos] ok (%d casos)" % (len(casos) + 4))
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
