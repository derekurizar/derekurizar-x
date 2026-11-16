#!/usr/bin/env python3
"""producir.py — la cadena de producción de un video que ya tiene voz, de punta a punta y reanudable.

Antes cada comando tecleaba 6–9 pasos por pieza (y /youtube-long, 9); `producir` existía solo en /historia. Ahora es
uno para todos: cada script lo reenvía aquí (`<flujo>.py producir <TRABAJO>`).

  python3 scripts/<flujo>.py producir <TRABAJO> [--desde PASO] [--hasta PASO] [--todo] [--sin-escucha]
                                                [--borrador] [--solo N] [--render] [--pasos]

Cadenas (según el TRABAJO: `video.json → tipo` y `realizacion`, o `youtube.json`):
  mesa      tiempos → escuchar → plano → grabar → montar → revisar → grabar-4x5 → montar-4x5 → revisar-4x5
  propio    lo mismo sin `plano` (el motor propio: trabajos viejos)
  3d        tiempos → escuchar → render → montar                                  (/video-3d)
  largo     armar → plano → grabar → proyecto → revisar                            (/youtube-long)
            y con --render: audio → render → montar   (entre los dos se miran las hojas)

El paso «Plano» lo escribe un Workflow (el realizador), no un script: si el trabajo va en mesa y todavía no tiene
`plano.json`, `producir` **se detiene con código 3**; la sesión lanza el Workflow `plano` (en el largo, `youtube` con
`desde: "plano"`) y repite `producir`, que reanuda ahí. Con `--borrador` (maquetas y `sin-voz`) usa el borrador del
plano y no se detiene.

Reanudación: `<TRABAJO>/producir.json` guarda por paso si terminó bien y la huella de lo que usó (voz, guion, plano).
Al repetir, se salta lo que ya está hecho y sigue igual; si cambió la voz, el guion o el plano, rehace desde el primer
paso que dependía de eso. `--todo` rehace todo; `--desde` y `--hasta` acotan; `--pasos` solo lista la cadena.

Códigos: 0 hecho · 1 un paso falló (dice cuál) · 2 uso incorrecto · 3 pausa: falta el plano.
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(RAIZ, "scripts")
PAUSA = 3
SCRIPT_DE = {"historia": "historia.py", "explica": "explica.py", "sabias": "sabias.py", "congreso": "congreso.py", "video3d": "video3d.py"}
ESTADO = "producir.json"


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def rel(p):
    return os.path.relpath(os.path.abspath(p), RAIZ)


def clase_de(trabajo):
    """(clase, estado): «largo» si es un TRABAJO de /youtube-long; si no, «3d», «mesa» o «propio» según su video.json."""
    if os.path.exists(os.path.join(trabajo, "youtube.json")):
        return "largo", leer(os.path.join(trabajo, "youtube.json"))
    if os.path.exists(os.path.join(trabajo, "video3d.json")):   # /video-3d guarda su estado aparte
        return "3d", dict(leer(os.path.join(trabajo, "video3d.json")), tipo="video3d")
    vj = os.path.join(trabajo, "video.json")
    if not os.path.exists(vj):
        return None, {}
    st = leer(vj)
    if st.get("tipo") == "video3d":
        return "3d", st
    return ("mesa" if st.get("realizacion") == "mesa" else "propio"), st


def script_de(clase, st):
    """El script del flujo: sus `tiempos` son propios; lo demás lo reenvía a video.py."""
    if clase == "largo":
        return "youtube.py"
    return SCRIPT_DE.get(st.get("tipo"), "video.py")


def paso(pid, script, args, depende, etiqueta=None):
    return {"id": pid, "cmd": [script] + list(args), "depende": tuple(depende), "etiqueta": etiqueta or pid}


def cadena(clase, st, trabajo, a):
    """Los pasos, en orden: [{id, cmd: [script, subcomando, …], depende: (voz|guion|plano, …)}]."""
    T, s = rel(trabajo), script_de(clase, st)
    if clase == "largo":
        if a.render:
            return [paso("audio", s, ["audio", T], ("guion", "plano")), paso("render", s, ["render", T], ("guion", "plano")),
                    paso("montar", s, ["montar", T], ("guion", "plano"))]
        return [paso("armar", s, ["armar", T], ("voz", "guion")),
                paso("plano", s, ["plano", T, "--check", "--hoja"] + (["--borrador"] if a.borrador else []), ("voz", "guion", "plano")),
                paso("grabar", s, ["grabar", T], ("voz", "guion", "plano")), paso("proyecto", s, ["proyecto", T], ("voz", "guion", "plano")),
                paso("revisar", s, ["revisar", T], ("voz", "guion", "plano"))]
    c = [paso("tiempos", s, ["tiempos", T], ("voz", "guion"))]
    if not a.sin_escucha:
        c.append(paso("escuchar", s, ["escuchar", T], ("voz", "guion")))
    if clase == "3d":
        return c + [paso("render", s, ["render", T], ("voz", "guion")), paso("montar", s, ["montar", T], ("voz", "guion"))]
    dep = ("voz", "guion", "plano") if clase == "mesa" else ("voz", "guion")
    if clase == "mesa":
        c.append(paso("plano", s, ["plano", T, "--check", "--hoja"] + (["--borrador"] if a.borrador else []), dep))
    solo = ["--solo", str(a.solo)] if a.solo else []
    for sufijo, fmt in (("", []), ("-4x5", ["--formato", "4:5"])):
        c += [paso("grabar" + sufijo, s, ["grabar", T] + fmt + solo, dep), paso("montar" + sufijo, s, ["montar", T] + fmt, dep),
              paso("revisar" + sufijo, s, ["revisar", T] + fmt, dep)]
    return c


def _sha(rutas):
    h = hashlib.sha1()
    for r in rutas:
        if os.path.isfile(r):
            h.update(os.path.basename(r).encode())
            with open(r, "rb") as f:
                for bloque in iter(lambda: f.read(1 << 20), b""):
                    h.update(bloque)
    return h.hexdigest()[:16]


def huellas(clase, trabajo):
    """Lo que cada paso usa: si cambia, lo hecho con la versión anterior ya no vale."""
    j = lambda *x: os.path.join(trabajo, *x)   # noqa: E731
    audio = j("nuevas", "audio") if clase == "largo" else j("audio")
    voces = sorted(os.path.join(audio, f) for f in (os.listdir(audio) if os.path.isdir(audio) else []) if f.endswith(".mp3"))
    guion = [j("montaje.json")] if clase == "largo" else [j("guion.json"), j("locucion.json")]
    return {"voz": _sha(voces), "guion": _sha(guion), "plano": _sha([j("plano.json")])}


def falta_plano(clase, st, trabajo, a):
    """¿Hay que parar a que el realizador escriba el plano? Solo en mesa o en el largo, sin plano.json, y no en una
    maqueta ni con --borrador (ahí el script usa el borrador)."""
    if clase not in ("mesa", "largo") or a.borrador or st.get("fixture"):
        return False
    if os.path.exists(os.path.join(trabajo, "plano.json")):
        return False
    # el largo trae un plano por capítulo (plano_<N>.json), que `youtube.py plano` une en plano.json
    return not (clase == "largo" and any(f.startswith("plano_") and f.endswith(".json") for f in os.listdir(trabajo)))


def desde_donde(pasos, estado, H, a):
    """Índice del primer paso que hay que correr: el de --desde; con --todo, el primero; si no, el primero que no
    terminó bien o cuya huella guardada ya no es la de ahora."""
    ids = [p["id"] for p in pasos]
    if a.desde:
        return ids.index(a.desde)
    if a.todo:
        return 0
    hechos = estado.get("pasos") or {}
    for k, p in enumerate(pasos):
        e = hechos.get(p["id"]) or {}
        if not e.get("ok") or any((e.get("huellas") or {}).get(d) != H[d] for d in p["depende"]):
            return k
    return len(pasos)


def ejecutar(cmd):
    """Un paso en su propio proceso. → código de salida."""
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, cmd[0])] + cmd[1:], cwd=RAIZ).returncode


def guardar(trabajo, estado):
    with open(os.path.join(trabajo, ESTADO), "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1)


def _decir(m):
    print(m, flush=True)   # en orden con la salida de cada paso, también redirigido


def correr(trabajo, a, ejecutar=ejecutar, decir=_decir):
    trabajo = os.path.abspath(trabajo)
    clase, st = clase_de(trabajo)
    if not clase:
        decir("ERROR: %s no tiene video.json, video3d.json ni youtube.json: no es un TRABAJO de video" % rel(trabajo))
        return 2
    pasos = cadena(clase, st, trabajo, a)
    ids = [p["id"] for p in pasos]
    for bandera, valor in (("--desde", a.desde), ("--hasta", a.hasta)):
        if valor and valor not in ids:
            decir("ERROR: %s %s no es un paso de esta cadena (%s)" % (bandera, valor, " → ".join(ids)))
            return 2
    if a.pasos:
        decir("%s · %s: %s" % (rel(trabajo), clase, " → ".join(ids)))
        return 0
    ep = os.path.join(trabajo, ESTADO)
    estado = leer(ep) if os.path.exists(ep) else {}
    if estado.get("clase") != clase or estado.get("render") != bool(a.render):
        estado = {"clase": clase, "render": bool(a.render), "pasos": {}}
    k0 = desde_donde(pasos, estado, huellas(clase, trabajo), a)
    fin = ids.index(a.hasta) if a.hasta else len(pasos) - 1
    if k0 > fin:
        decir("producir: nada que hacer en %s (%s ya está hecho con esta voz, este guion y este plano; --todo lo rehace)"
              % (rel(trabajo), " → ".join(ids[:fin + 1])))
        return 0
    if k0:
        decir("producir: ya hecho %s · reanuda en «%s»" % (" → ".join(ids[:k0]), ids[k0]))
    for k in range(k0, fin + 1):
        p = pasos[k]
        if p["id"] == "plano" and falta_plano(clase, st, trabajo, a):
            guardar(trabajo, estado)
            wf = ('Workflow({ name: "youtube", args: { trabajo: "%s", desde: "plano", capitulos: N } })' if clase == "largo"
                  else 'Workflow({ name: "plano", args: { trabajo: "%s" } })') % rel(trabajo)
            decir("PAUSA (código 3): falta el paso «Plano». Lanza %s y repite `producir`: reanuda aquí. "
                  "(En una maqueta o con sin-voz: --borrador.)" % wf)
            return PAUSA
        decir("── %d/%d · %s" % (k + 1, len(pasos), " ".join(p["cmd"][1:2] + p["cmd"][3:])))
        rc = ejecutar(p["cmd"])
        H = huellas(clase, trabajo)   # después de correr: `tiempos` y `armar` no cambian la voz ni el guion, pero el plano puede nacer en su paso
        estado["pasos"][p["id"]] = {"ok": rc == 0, "codigo": rc, "huellas": {d: H[d] for d in p["depende"]},
                                    "cuando": datetime.datetime.now().isoformat(timespec="seconds")}
        for q in pasos[k + 1:]:   # lo que viene después se hizo con lo de antes: ya no vale
            estado["pasos"].pop(q["id"], None)
        guardar(trabajo, estado)
        if rc:
            decir("FALLA  producir se detuvo en «%s» (exit %d): corrige y repite `producir` (reanuda en ese paso)" % (p["id"], rc))
            return 1
    if fin < len(pasos) - 1:
        decir("producir: hecho hasta «%s»; falta %s" % (ids[fin], " → ".join(ids[fin + 1:])))
    elif clase == "largo" and not a.render:
        decir("producir: armado y revisado; mira las hojas y sigue con `producir --render` (audio → render → montar)")
    else:
        decir("producido: %s/salida · falta entregar" % rel(trabajo))
    return 0


def argumentos(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trabajo")
    ap.add_argument("--desde", help="empieza en este paso (aunque los anteriores no consten)")
    ap.add_argument("--hasta", help="se detiene tras este paso")
    ap.add_argument("--todo", action="store_true", help="rehace toda la cadena")
    ap.add_argument("--sin-escucha", dest="sin_escucha", action="store_true", help="salta `escuchar` (V11)")
    ap.add_argument("--borrador", action="store_true", help="usa el borrador del plano (maquetas y sin-voz): no se detiene a esperar al realizador")
    ap.add_argument("--solo", help="pasa --solo N a `grabar`")
    ap.add_argument("--render", action="store_true", help="/youtube-long: la segunda mitad (audio → render → montar)")
    ap.add_argument("--pasos", action="store_true", help="lista la cadena de este TRABAJO y sale")
    return ap.parse_args(argv)


def main(argv=None):
    a = argumentos(argv)
    if not os.path.isdir(a.trabajo):
        print("ERROR: no existe %s" % a.trabajo, file=sys.stderr)
        return 2
    return correr(a.trabajo, a)


if __name__ == "__main__":
    sys.exit(main())
