#!/usr/bin/env python3
"""Pruebas de /video-3d a la par de los demás flujos (ola 1, punto 11; sin render ni créditos): los 22 negativos del
motor (maqueta3d.negativos: cada gate M3D muerde), el caption obligatorio (V5), la estimación con video.segundos_voz, el
.srt de video.texto_srt, `escuchar` reenviado a video.py, el 4:5 y la portada exigidos al entregar, la rotación de la
familia del gancho y «Rendimiento real» en el digesto. Exit 0 ok · 1 falla."""
import argparse
import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402
import video as VD  # noqa: E402
import video3d as V3  # noqa: E402

F = []
FIX = os.path.join(RAIZ, "sesiones", "_fixture_video3d")
TMP = tempfile.mkdtemp(prefix="ola1_video3d_")


def ok(cond, que):
    if not cond:
        F.append(que)


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def callado(fn, *args):
    """(resultado, lo que imprimió): las pruebas no ensucian la salida de make test."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        r = fn(*args)
    return r, buf.getvalue()


def trabajo(nombre, guion=None, **st):
    """Un TRABAJO como el que arma `make video3d-fixture` (guion, estado y cifras del fixture), en una carpeta temporal."""
    t = os.path.join(TMP, nombre)
    os.makedirs(os.path.join(t, "base"))
    os.makedirs(os.path.join(t, "audio"))
    V3.escribir(os.path.join(t, "guion.json"), guion if guion is not None else leer(os.path.join(FIX, "guion.json")))
    V3.escribir(os.path.join(t, "video3d.json"), dict(leer(os.path.join(FIX, "video3d.json")), **st))
    shutil.copyfile(os.path.join(FIX, "datos.json"), os.path.join(t, "base", "datos.json"))
    return t


G = leer(os.path.join(FIX, "guion.json"))
ST = leer(os.path.join(FIX, "video3d.json"))

# ---------- 1. los negativos del motor: cada cambio al fixture hace saltar SU gate M3D (sin render, ≈ 1 s) ----------
mal, salida = callado(M3.negativos)
ok(mal == 0, "M3D: %d negativo(s) o positivo(s) del motor no dieron lo esperado:\n%s" % (mal, salida))
ok("%d de %d muerden" % (len(M3.NEGATIVOS), len(M3.NEGATIVOS)) in salida and len(M3.NEGATIVOS) >= 22,
   "M3D: no corrieron los %d negativos del motor: %s" % (len(M3.NEGATIVOS), salida.strip()[:200]))

# ---------- 2. el caption es obligatorio y pasa V5 ----------
T0 = trabajo("base")
fallas, avisos, loc = V3.revisar_guion(G, ST, T0)
ok(not fallas and isinstance(loc, dict), "el guion del fixture debe pasar C3D + V2–V5: %s" % fallas)
sin = {k: v for k, v in G.items() if k != "caption"}
f = V3.revisar_guion(sin, ST, T0)[0]
ok(sorted(x for x in f if x.startswith("V5 falta caption.")) == sorted("V5 falta caption.%s" % k for k, _ in VD.PLATAFORMAS),
   "V5: sin caption deben faltar los %d de las plataformas: %s" % (len(VD.PLATAFORMAS), f))


def con_caption(**cambios):
    return V3.revisar_caption(dict(G, caption=dict(G["caption"], **cambios)))


ok(V3.revisar_caption(G) == [], "V5: rechaza el caption del fixture: %s" % V3.revisar_caption(G))
ok(any("caption.instagram" in x for x in con_caption(instagram="  ")), "V5: acepta un caption vacío")
ok(any("#Shorts" in x for x in con_caption(shorts="Terremoto de 1976 en Guatemala\nMagnitud 7.5")), "V5: acepta un Short sin #Shorts")
ok(any("título de YouTube" in x for x in con_caption(shorts="T" * (VD.SHORTS_TITULO + 1) + "\n#Shorts")), "V5: acepta un título de Short largo")
ok(any("cifra en palabras" in x for x in con_caption(tiktok="El terremoto costó mil seiscientos millones de quetzales en Guatemala")),
   "V5: acepta una cifra en palabras en el caption")
ok(any("anuncia el video" in x for x in con_caption(facebook="Al final verás por qué la falla sigue ahí.")), "V5: acepta un caption que anuncia el video")
ok(any("en suma" in x for x in con_caption(tiktok="En suma, la falla sigue ahí. #Guatemala")), "V5: acepta «en suma» en el caption")
# por la línea de comandos: guion --check sale 1 sin caption y nombra V5
T1 = trabajo("sin_caption", sin)
r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video3d.py"), "guion", T1, "--check"], capture_output=True, text=True)
ok(r.returncode == 1 and "FALLA V5 falta caption.tiktok" in r.stdout and not os.path.exists(os.path.join(T1, "locucion.json")),
   "guion --check sin caption debe salir 1 con V5 y sin escribir locucion.json (salió %d): %s" % (r.returncode, r.stdout[-300:]))
# los candidatos a gancho son una sola escena: a ellos no se les pide caption
T2 = trabajo("ganchos")
e1 = G["escenas"][0]
V3.escribir(os.path.join(T2, "ganchos.json"), dict({k: G[k] for k in ("estilo", "idea_visual", "protagonista", "mundo", "pie")},
            candidatos=[{"id": "g%d" % k, "familia": fam, "escena": copy.deepcopy(e1)} for k, fam in enumerate(("ruptura", "caida", "revelacion", "escala"), 1)]))
ns = argparse.Namespace(trabajo=T2, check=True, cuadros=False, clips=False, usar=None, por="usuario", formato="9:16")
rc, salida = callado(V3.cmd_ganchos, ns)
ok(rc == 0 and "V5" not in salida, "ganchos --check no debe pedir caption a un candidato: %s" % salida[-300:])

# ---------- 3. la estimación: video.segundos_voz, sin cambiar lo que ya estaba en palabras ----------
for x in loc["escenas"]:
    ok(x["estimado_s"] == round(VD.segundos_voz(x["voz"]) + x["cola"], 2), "estimación: E%d no usa video.segundos_voz" % x["n"])
    ok(x["estimado_s"] == round(len(x["voz"]) / VD.CPS + x["cola"], 2), "estimación: E%d cambió con la voz ya en palabras" % x["n"])
ok(abs(loc["estimado_s"] - ST["duracion_s"]) <= ST["duracion_s"] * V3.TOL, "estimación: el fixture ya no cae en su objetivo (%s s)" % loc["estimado_s"])
ok(VD.segundos_voz("Fue de magnitud 7.5 en 1976.") > len("Fue de magnitud 7.5 en 1976.") / VD.CPS + 1.0,
   "estimación: video.segundos_voz no pasa las cifras a palabras")

# ---------- 4. el .srt es el de los demás flujos (video.texto_srt): por oración, ≤ 2 líneas de 42, sin solapes ----------
maqueta, tiempos, _ = V3.construir(T0, G, loc, real=False)
escenas, offs = V3.escenas_srt(maqueta, tiempos)
ok([e["n"] for e in escenas] == [e["n"] for e in tiempos["escenas"]] and offs == [e["off"] for e in tiempos["escenas"]],
   "srt: las escenas y sus desfases no son los de tiempos.json")
ok(sum(len(e["palabras"]) for e in escenas) == len(maqueta["capa"]["palabras"]) and all(e["palabras"] for e in escenas),
   "srt: se perdieron palabras al repartirlas por escena")
ok(all(-1e-6 <= w["start"] <= e_t["dur"] for e, e_t in zip(escenas, tiempos["escenas"]) for w in e["palabras"]),
   "srt: una palabra quedó fuera de su escena")
ok(escenas[1]["palabras"][0]["text"].lower().startswith("el") and escenas[-1]["palabras"][-1]["text"].endswith("pueblos."),
   "srt: las palabras no cayeron en su escena: %s" % [e["palabras"][0]["text"] for e in escenas])
# el corte va a 4 decimales y las palabras a 3: la primera palabra de una escena puede quedar medio milisegundo «antes»
e_b, _ = V3.escenas_srt({"capa": {"palabras": [{"text": "Uno.", "start": 0.0, "end": 0.4}, {"text": "Dos.", "start": 5.333, "end": 5.7}]}},
                        {"escenas": [{"n": 1, "off": 0.0, "dur": 5.3333}, {"n": 2, "off": 5.3333, "dur": 2.0}]})
ok([[w["text"] for w in e["palabras"]] for e in e_b] == [["Uno."], ["Dos."]] and e_b[1]["palabras"][0]["start"] == 0.0,
   "srt: la primera palabra de una escena cayó en la anterior por el redondeo: %s" % e_b)
B = VD.bloques_srt(escenas, offs)
ok(B and VD.revisar_srt(B) == [], "srt: solapes o líneas largas: %s" % VD.revisar_srt(B))
ok(all(len(l) <= VD.SRT_ANCHO for b in B for l in b["texto"].split("\n")) and all(b["texto"].count("\n") < VD.SRT_LINEAS for b in B),
   "srt: una línea pasa de %d caracteres o un subtítulo de %d líneas" % (VD.SRT_ANCHO, VD.SRT_LINEAS))
txt, _ = callado(VD.texto_srt, escenas, offs)
ok(txt.startswith("1\n00:00:00,") and " --> " in txt and "A las 3 de la madrugada" in txt.replace("\n", " "), "srt: el texto no tiene la forma de un .srt")
ok(not hasattr(V3, "bloques_srt") and not hasattr(V3, "ts"), "srt: video3d.py conserva su .srt propio")
ok(V3.efectos_de(T0, maqueta) == [(e["t"], e["sfx"]) for e in maqueta["eventos"] if e.get("sfx")] and len(V3.efectos_de(T0, maqueta)) == 2,
   "mezcla: los efectos no salen de los eventos de la maqueta")

# ---------- 5. escuchar (V11) se reenvía a video.py ----------
ok("escuchar" in V3.REENVIO, "escuchar no está en REENVIO")
V3.escribir(os.path.join(T0, "locucion.json"), loc)
r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video3d.py"), "escuchar", T0, "--modelo", os.path.join(TMP, "no-existe.bin")],
                   capture_output=True, text=True)
ok(r.returncode == 0 and "AVISO V11" in r.stdout, "escuchar no llegó a video.py (salió %d): %s %s" % (r.returncode, r.stdout[-200:], r.stderr[-200:]))

# ---------- 6. entregar: sin el 4:5, sin portada o sin caption es una falla ----------
T3 = trabajo("entrega")
sal = os.path.join(T3, "salida")
os.makedirs(sal)
V3.escribir(os.path.join(T3, "tiempos.json"), dict(tiempos, real=True))
V3.escribir(os.path.join(T3, "maqueta.json"), maqueta)
VD.ff("-f", "lavfi", "-i", "color=c=black:s=108x192:r=10:d=1", "-an", "-pix_fmt", "yuv420p", os.path.join(sal, "video.mp4"))
open(os.path.join(sal, "subtitulos.srt"), "w", encoding="utf-8").write(txt)
open(os.path.join(sal, "portada.png"), "wb").write(b"\x89PNG\r\n\x1a\n")
DEST = os.path.join(TMP, "entregado", "2026-11-14-fixture")


def entregar(**kw):
    return callado(V3.cmd_entregar, argparse.Namespace(trabajo=T3, salida=DEST, sin_4x5=kw.get("sin_4x5", False)))


rc, salida = entregar()
ok(rc == 1 and "video_4x5.mp4" in salida and not os.path.exists(DEST), "entregar sin el 4:5 debe fallar sin escribir nada: %s" % salida[-300:])
os.remove(os.path.join(sal, "portada.png"))
rc, salida = entregar(sin_4x5=True)
ok(rc == 1 and "portada.png" in salida, "entregar sin portada debe fallar: %s" % salida[-300:])
open(os.path.join(sal, "portada.png"), "wb").write(b"\x89PNG\r\n\x1a\n")
V3.escribir(os.path.join(T3, "guion.json"), sin)
rc, salida = entregar(sin_4x5=True)
ok(rc == 1 and "V5 falta caption" in salida, "entregar sin caption debe fallar: %s" % salida[-300:])
V3.escribir(os.path.join(T3, "guion.json"), G)
rc, salida = entregar(sin_4x5=True)
ok(rc == 0 and all(os.path.exists(os.path.join(DEST, x)) for x in ("video.mp4", "portada.png", "caption.md", "subtitulos.srt", "tiempos.json",
                                                                 "maqueta.json", "guion.json", "fuentes.md")),
   "entregar --sin-4x5 con todo lo demás debe entregar (salió %s): %s · %s" % (rc, salida[-300:], os.listdir(DEST) if os.path.isdir(DEST) else "—"))
if os.path.isdir(DEST):
    cap = open(os.path.join(DEST, "caption.md"), encoding="utf-8").read()
    ok(all("## " + nombre in cap for _, nombre in VD.PLATAFORMAS) and "#Shorts" in cap, "caption.md sin una sección por plataforma")
    ok(leer(os.path.join(DEST, "tiempos.json"))["real"] is True, "la entrega no lleva los tiempos reales (metricas.py alinear los lee)")
shutil.copyfile(os.path.join(sal, "video.mp4"), os.path.join(sal, "video_4x5.mp4"))
rc, salida = entregar()
ok(rc == 0 and os.path.exists(os.path.join(DEST, "video_4x5.mp4")), "entregar con 9:16 y 4:5 debe pasar: %s" % salida[-300:])

# ---------- 7. rotación: la familia del gancho de los últimos 2 videos 3D ----------
reg_real = V3.REGISTRO
V3.REGISTRO = os.path.join(TMP, "videos3d.json")
V3.escribir(V3.REGISTRO, {"videos3d": [{"slug": "a", "fecha": "2026-11-01", "gancho": {"familia": "caida", "texto": "Uno."}},
                                       {"slug": "b", "fecha": "2026-11-02", "gancho": {"familia": "escala", "texto": "Dos."}},
                                       {"slug": "c", "fecha": "2026-11-03", "gancho": {"familia": "ruptura", "texto": "Tres."}}]})
real = dict(ST, fixture=False, slug="nuevo")
ok(V3.familias_recientes(real) == ["escala", "ruptura"], "rotación: las bloqueadas son las de los últimos %d: %s" % (V3.ROTACION_GANCHOS, V3.familias_recientes(real)))
ok(V3.familias_recientes(dict(real, slug="c")) == ["caida", "escala"], "rotación: el propio video no cuenta")
ok(V3.familias_recientes(ST) == [], "rotación: una maqueta de prueba no rota")
_, av, _ = V3.revisar_guion(G, real, T0)   # el fixture eligió «ruptura»
ok(any(x.startswith("G3D2") for x in av), "rotación: guion --check no avisa de la familia repetida: %s" % av)
_, av, _ = V3.revisar_guion(dict(G, gancho=dict(G["gancho"], familia="revelacion")), real, T0)
ok(not any(x.startswith("G3D2") for x in av), "rotación: avisa de una familia que no está bloqueada")
T4 = trabajo("rotacion", fixture=False, slug="nuevo")
shutil.copyfile(os.path.join(T2, "ganchos.json"), os.path.join(T4, "ganchos.json"))
rc, salida = callado(V3.cmd_ganchos, argparse.Namespace(trabajo=T4, check=True, cuadros=False, clips=False, usar=None, por="usuario", formato="9:16"))
ok(rc == 0 and "AVISO G3D2 g1" in salida and "AVISO G3D2 g4" in salida and "G3D2 g2" not in salida,
   "rotación: ganchos --check debe avisar de g1 (ruptura) y g4 (escala): %s" % salida[-400:])
rc, salida = callado(V3.cmd_ganchos, argparse.Namespace(trabajo=T4, check=False, cuadros=False, clips=False, usar="g1", por="usuario", formato="9:16"))
ok(rc == 0 and "AVISO G3D2" in salida and leer(os.path.join(T4, "guion.json"))["gancho"]["familia"] == "ruptura",
   "rotación: ganchos --usar debe avisar si el elegido repite la familia: %s" % salida[-300:])

# ---------- 8. el digesto: rotación y «Rendimiento real» ----------
rc, salida = callado(V3.cmd_digesto, argparse.Namespace(trabajo=T4))
ok(rc == 0 and "## Rendimiento real" in salida and "## Rotación del gancho" in salida, "digesto: faltan «Rendimiento real» o la rotación")
ok("`escala`, `ruptura`" in salida and salida.count("(NO REPETIR)") == 2, "digesto: no marca las familias bloqueadas: %s" % salida[-900:-500])
ok("`caption` (obligatorio, V5)" in salida, "digesto: no dice que el caption es obligatorio")
ok("- Por " in salida or "métricas" in salida, "digesto: «Rendimiento real» salió vacío")
V3.REGISTRO = reg_real

shutil.rmtree(TMP, ignore_errors=True)
for x in F:
    print("FALLA", x)
print("[ola 1 · /video-3d] %s" % ("ok" if not F else "%d fallas" % len(F)))
sys.exit(1 if F else 0)
