#!/usr/bin/env python3
"""Pruebas de scripts/producir.py con un ejecutor inyectado (no corre ningún paso de verdad).

Cubre: la cadena de cada clase (mesa, propio, 3d, largo y largo --render), el script de cada flujo, la pausa con
código 3 cuando falta el plano, la reanudación (se salta lo hecho; rehace desde donde cambió la voz, el guion o el
plano), --desde / --hasta / --todo / --sin-escucha / --borrador, y que una falla se detiene y deja reanudar ahí.

Uso: python3 scripts/pruebas/producir.py   (exit 0 ok · 1 falla)
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import producir as P  # noqa: E402


def trabajo(base, nombre, video=None, youtube=None, plano=False, voces=("voz_1.mp3",), nuevas=False):
    t = os.path.join(base, nombre)
    os.makedirs(os.path.join(t, "nuevas", "audio") if nuevas else os.path.join(t, "audio"))
    if video is not None:
        json.dump(video, open(os.path.join(t, "video.json"), "w"))
        json.dump({"escenas": []}, open(os.path.join(t, "guion.json"), "w"))
        json.dump({"escenas": []}, open(os.path.join(t, "locucion.json"), "w"))
    if youtube is not None:
        json.dump(youtube, open(os.path.join(t, "youtube.json"), "w"))
        json.dump({"capitulos": []}, open(os.path.join(t, "montaje.json"), "w"))
    for v in voces:
        open(os.path.join(t, "nuevas", "audio", v) if nuevas else os.path.join(t, "audio", v), "wb").write(b"voz-uno")
    if plano:
        json.dump({"mesas": []}, open(os.path.join(t, "plano.json"), "w"))
    return t


class Ejecutor:
    """Apunta cada paso que se le pide; falla los que estén en `fallan`."""

    def __init__(self, fallan=()):
        self.vistos, self.fallan = [], set(fallan)

    def __call__(self, cmd):
        self.vistos.append(cmd)
        return 1 if cmd[1] in self.fallan else 0

    def pasos(self):
        return [c[1] + ("-4x5" if "4:5" in c else "") for c in self.vistos]


def correr(t, *banderas, fallan=()):
    e, dicho = Ejecutor(fallan), []
    rc = P.correr(t, P.argumentos([t] + list(banderas)), ejecutar=e, decir=dicho.append)
    return rc, e, "\n".join(dicho)


MESA = ["tiempos", "escuchar", "plano", "grabar", "montar", "revisar", "grabar-4x5", "montar-4x5", "revisar-4x5"]


def main():
    base = tempfile.mkdtemp(prefix="producir_", dir=os.path.join(P.RAIZ, "sesiones")) if os.path.isdir(os.path.join(P.RAIZ, "sesiones")) else tempfile.mkdtemp()
    try:
        # ── cadenas y script por flujo ──
        t = trabajo(base, "historia", {"tipo": "historia", "realizacion": "mesa"}, plano=True)
        rc, e, _ = correr(t)
        assert rc == 0 and e.pasos() == MESA, e.pasos()
        assert all(c[0] == "historia.py" for c in e.vistos), e.vistos[0]
        assert e.vistos[2][1:] == ["plano", P.rel(t), "--check", "--hoja"], e.vistos[2]
        for tipo, script in (("explica", "explica.py"), ("sabias", "sabias.py"), ("congreso", "congreso.py"), ("video", "video.py"), (None, "video.py")):
            assert P.script_de("mesa", {"tipo": tipo}) == script, (tipo, script)
        t2 = trabajo(base, "viejo", {"tipo": "video", "realizacion": "propio"})
        rc, e, _ = correr(t2)
        assert rc == 0 and e.pasos() == [x for x in MESA if x != "plano"], e.pasos()
        t3 = trabajo(base, "tresd", {"tipo": "video3d"})
        os.rename(os.path.join(t3, "video.json"), os.path.join(t3, "video3d.json"))   # /video-3d guarda su estado en video3d.json
        rc, e, _ = correr(t3)
        assert rc == 0 and e.pasos() == ["tiempos", "escuchar", "render", "montar"] and e.vistos[0][0] == "video3d.py", e.vistos
        rc, e, _ = correr(t3, "--todo", "--sin-escucha")
        assert e.pasos() == ["tiempos", "render", "montar"], e.pasos()

        # ── nada que hacer la segunda vez; --todo lo rehace ──
        rc, e, dicho = correr(t)
        assert rc == 0 and e.pasos() == [] and "nada que hacer" in dicho, dicho
        rc, e, _ = correr(t, "--todo")
        assert e.pasos() == MESA

        # ── pausa (código 3) cuando falta el plano; reanuda ahí ──
        t4 = trabajo(base, "sin-plano", {"tipo": "explica", "realizacion": "mesa"})
        rc, e, dicho = correr(t4)
        assert rc == P.PAUSA == 3 and e.pasos() == ["tiempos", "escuchar"] and "Workflow" in dicho and '"plano"' in dicho, (rc, e.pasos(), dicho)
        json.dump({"mesas": []}, open(os.path.join(t4, "plano.json"), "w"))
        rc, e, dicho = correr(t4)
        assert rc == 0 and e.pasos() == MESA[2:] and "reanuda en «plano»" in dicho, (e.pasos(), dicho)
        # una maqueta (fixture) o --borrador no se detienen: el script usa el borrador
        t5 = trabajo(base, "maqueta", {"tipo": "historia", "realizacion": "mesa", "fixture": True})
        rc, e, _ = correr(t5)
        assert rc == 0 and e.pasos() == MESA
        t6 = trabajo(base, "sin-voz", {"tipo": "historia", "realizacion": "mesa"})
        rc, e, _ = correr(t6, "--borrador")
        assert rc == 0 and e.pasos() == MESA and "--borrador" in e.vistos[2], e.vistos[2]

        # ── una falla se detiene y deja reanudar en ese paso ──
        t7 = trabajo(base, "falla", {"tipo": "historia", "realizacion": "mesa"}, plano=True)
        rc, e, dicho = correr(t7, fallan=("montar",))
        assert rc == 1 and e.pasos() == MESA[:5] and "«montar»" in dicho, (rc, e.pasos())
        rc, e, _ = correr(t7)
        assert rc == 0 and e.pasos() == MESA[4:], e.pasos()

        # ── si cambia el plano, rehace desde `plano`; si cambia la voz, desde `tiempos` ──
        json.dump({"mesas": [1]}, open(os.path.join(t7, "plano.json"), "w"))
        rc, e, _ = correr(t7)
        assert e.pasos() == MESA[2:], e.pasos()
        open(os.path.join(t7, "audio", "voz_1.mp3"), "wb").write(b"voz-dos")
        rc, e, _ = correr(t7)
        assert e.pasos() == MESA, e.pasos()
        json.dump({"escenas": [1]}, open(os.path.join(t7, "guion.json"), "w"))
        rc, e, _ = correr(t7)
        assert e.pasos() == MESA, e.pasos()

        # ── --desde y --hasta ──
        rc, e, dicho = correr(t7, "--todo", "--hasta", "plano")
        assert rc == 0 and e.pasos() == MESA[:3] and "falta grabar" in dicho, (e.pasos(), dicho)
        rc, e, _ = correr(t7, "--desde", "montar", "--hasta", "revisar")
        assert e.pasos() == ["montar", "revisar"], e.pasos()
        rc, e, _ = correr(t7, "--desde", "render")
        assert rc == 2 and e.pasos() == []
        rc, e, dicho = correr(t7, "--pasos")
        assert rc == 0 and e.pasos() == [] and "tiempos → escuchar → plano" in dicho

        # ── el largo: dos mitades, y la pausa por el plano de los capítulos ──
        t8 = trabajo(base, "largo", youtube={"serie": "x"}, nuevas=True)
        rc, e, dicho = correr(t8)
        assert rc == 3 and e.pasos() == ["armar"] and '"youtube"' in dicho and "desde" in dicho, (rc, e.pasos(), dicho)
        json.dump({"mesas": []}, open(os.path.join(t8, "plano_1.json"), "w"))   # los planos por capítulo: `youtube.py plano` los une
        rc, e, dicho = correr(t8)
        assert rc == 0 and e.pasos() == ["plano", "grabar", "proyecto", "revisar"] and "--render" in dicho, (e.pasos(), dicho)
        assert all(c[0] == "youtube.py" for c in e.vistos)
        rc, e, _ = correr(t8, "--render")
        assert rc == 0 and e.pasos() == ["audio", "render", "montar"], e.pasos()

        # ── sin video.json ni youtube.json no es un TRABAJO ──
        os.makedirs(os.path.join(base, "nada"))
        rc, e, _ = correr(os.path.join(base, "nada"))
        assert rc == 2
        print("[producir] ok")
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
