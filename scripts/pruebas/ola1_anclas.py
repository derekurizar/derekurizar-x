#!/usr/bin/env python3
"""Ola 1 · punto 12: un `dice` resuelve igual en la mesa, en /video-3d y en los tableros (una sola conversión: VD.dicho).

Antes «1995» resolvía en /video-3d (que pasaba los números a palabras) y fallaba en la mesa (que no).
Uso: python3 scripts/pruebas/ola1_anclas.py   (exit 0 ok · 1 falla)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import mesa as M      # noqa: E402
import video as VD    # noqa: E402
import video3d as V3  # noqa: E402

VOZ = "En mil novecientos noventa y cinco el banco abrió con el doce por ciento de los ahorros".split()
S = {"palabras": [{"text": w, "start": round(i * .3, 3), "end": round(i * .3 + .25, 3)} for i, w in enumerate(VOZ)]}


def main():
    assert VD.dicho("1995") == "mil novecientos noventa y cinco", VD.dicho("1995")
    assert VD.dicho("el banco") == "el banco"
    # la mesa: el año en dígitos, una frase literal y una que la voz no dice
    assert M.buscar(S, "1995", 0) == (1, 1, 5), M.buscar(S, "1995", 0)
    assert M.buscar(S, "en 1995", 0) == (0, 0, 5), M.buscar(S, "en 1995", 0)
    assert M.buscar(S, "el banco", 0) == (6, 6, 7), M.buscar(S, "el banco", 0)
    assert M.buscar(S, "mil novecientos noventa y cinco", 0) == (1, 1, 5)
    assert M.buscar(S, "2001", 0) is None and M.buscar(S, "", 0) is None
    assert M.buscar(S, "1995", 2) is None   # `desde` se respeta también con la forma en palabras
    # /video-3d y los tableros: lo mismo
    assert V3.buscar(S["palabras"], "1995") == (1, 5), V3.buscar(S["palabras"], "1995")
    assert V3.buscar(S["palabras"], "el banco") == (6, 7)
    assert VD.indice_frase(S["palabras"], "1995 el banco") == 1
    # los tres coinciden en dónde empieza
    for frase in ("1995", "el banco", "doce por ciento", "12 por ciento"):
        m, v = M.buscar(S, frase, 0), V3.buscar(S["palabras"], frase)
        assert (m is None) == (v is None) and (m is None or m[1] == v[0]), (frase, m, v)
    print("[ola 1 · anclas] ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
