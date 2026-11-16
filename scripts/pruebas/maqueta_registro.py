#!/usr/bin/env python3
"""El vocabulario de la maqueta 3D como catálogo de módulos (sin render ni red; ≈ 1 s): el catálogo
(design/sets3d/vocabulario.json) se genera igual dos veces y está al día con las fichas; cada módulo de
video/maqueta/<clase>/ tiene su ficha y cada ficha su módulo (un módulo suelto, una ficha suelta, un color escrito a mano
o un módulo que no se registra fallan al registrar); el validador genérico rechaza un parámetro fuera de rango, uno
requerido que falta, un valor fuera de su lista y un tipo que no está en el catálogo (y avisa lo que la ficha no
declara); un estilo de Blender con un tipo que solo dibuja three.js falla M3D2; el proyecto copia solo los módulos que
la maqueta usa y los carga antes del núcleo; el núcleo no nombra ningún tipo. Exit 0 ok · 1 falla.

Uso: python3 scripts/pruebas/maqueta_registro.py"""
import copy
import json
import os
import re
import shutil
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402

F = []
TMP = tempfile.mkdtemp(prefix="maqueta_registro_")
BASE = M3.cargar_json(M3.FIXTURE)


def ok(cond, que):
    if not cond:
        F.append(que)


def fallas_de(cambio, formatos=("9:16",)):
    m = copy.deepcopy(BASE)
    cambio(m)
    return M3.revisar_m(m, list(formatos))


# ---------- 1. el catálogo: determinista, al día, completo ----------
c1, f1 = M3.generar_catalogo()
c2, f2 = M3.generar_catalogo()
ok(not f1, "catálogo: las fichas de hoy no pasan: %s" % f1[:3])
ok(M3.texto_catalogo(c1) == M3.texto_catalogo(c2), "catálogo: dos generaciones seguidas no dan el mismo texto")
ok(os.path.isfile(M3.VOCABULARIO) and M3.texto_catalogo(c1) == M3.cargar_texto(M3.VOCABULARIO),
   "catálogo: design/sets3d/vocabulario.json no está al día (python3 scripts/maqueta3d.py catalogo --registrar)")
tipos = {e["tipo"]: e for e in c1["entradas"]}
for clase, carpeta in M3.CLASES.items():
    d = os.path.join(M3.MOTOR, carpeta)
    for n in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if n.endswith(".js"):
            ok(n[:-3] in tipos and tipos[n[:-3]]["clase"] == clase, "catálogo: el módulo %s/%s no está en el catálogo" % (carpeta, n))
ok(set(M3.tipos("pieza")) >= {"falla", "luces", "frontera", "ruta"} and
   set(M3.tipos("evento")) >= {"ruptura", "onda", "deslizar", "encender", "apagar", "parpadear", "resaltar"},
   "catálogo: faltan tipos de hoy (piezas %s, eventos %s)" % (M3.tipos("pieza"), M3.tipos("evento")))

# un módulo sin ficha, una ficha sin módulo, un módulo con un color escrito o que no se registra: fallan al registrar
falso = os.path.join(TMP, "maqueta")
shutil.copytree(M3.MOTOR, falso, ignore=shutil.ignore_patterns("fixture", "*.html", "*.css"))
motor_real = M3.MOTOR
try:
    M3.MOTOR = falso
    with open(os.path.join(falso, "piezas", "suelto.js"), "w") as fh:
        fh.write("(function (MAQ) { MAQ.PIEZAS.suelto = {}; })(window.MAQ);\n")
    shutil.copyfile(os.path.join(falso, "eventos", "onda.json"), os.path.join(falso, "eventos", "huerfana.json"))
    with open(os.path.join(falso, "eventos", "onda.js"), "a") as fh:
        fh.write("// el color: \nconst X = '#ff0000';\n")
    with open(os.path.join(falso, "eventos", "apagar.js"), "w") as fh:
        fh.write("// no se registra\n")
    _, fx = M3.generar_catalogo()
    txt = "\n".join(fx)
    ok("suelto.js no tiene ficha" in txt, "registrar: un módulo sin ficha no falla: %s" % fx)
    ok("huerfana.json no tiene módulo" in txt, "registrar: una ficha sin módulo no falla")
    ok(re.search(r"onda\.js: un color escrito", txt), "registrar: un color escrito a mano en un módulo no falla")
    ok(re.search(r"apagar\.js: el módulo no se registra", txt), "registrar: un módulo que no se registra no falla")
    fi = M3.cargar_json(os.path.join(falso, "piezas", "ruta.json"))
    fi["ejemplo"]["lugares"] = ["guatemala"]
    _, fy = [None, M3.revisar_ficha(fi, "pieza", "ruta", os.path.join(falso, "piezas", "ruta.js"))]
    ok(any("ejemplo" in x for x in fy), "registrar: una ficha cuyo ejemplo no pasa su propia ficha no falla: %s" % fy)
finally:
    M3.MOTOR = motor_real

# ---------- 2. el validador genérico (M3D2) ----------
f, _ = fallas_de(lambda m: m["eventos"][2].update(radio_km=99999))
ok(any(x.startswith("M3D2 ") and "radio_km" in x and "va de" in x for x in f), "validador: un parámetro fuera de rango no falla: %s" % f[:2])
f, _ = fallas_de(lambda m: m["eventos"][0].pop("desde"))
ok(any(x.startswith("M3D2 ") and "falta `desde`" in x for x in f), "validador: un parámetro requerido que falta no falla: %s" % f[:2])
f, _ = fallas_de(lambda m: m["eventos"][1].update(sentido="arriba"))
ok(any(x.startswith("M3D2 ") and "sentido" in x and "izquierdo" in x for x in f), "validador: un valor fuera de su lista no falla: %s" % f[:2])
f, _ = fallas_de(lambda m: m["eventos"][0].update(pieza="frontera"))
ok(any(x.startswith("M3D2 ") and "no es una pieza de tipo falla" in x for x in f), "validador: una pieza del tipo equivocado no falla: %s" % f[:2])
f, _ = fallas_de(lambda m: m["eventos"].append({"t": 2.0, "dur": 1.0, "tipo": "tornado"}))
ok(any(x.startswith("M3D2 ") and "no está en el catálogo" in x and "constructor" in x for x in f), "validador: un tipo de evento desconocido no falla: %s" % f[:2])
f, _ = fallas_de(lambda m: m["mundo"]["piezas"].append({"id": "x", "tipo": "volcan"}))
ok(any(x.startswith("M3D2 ") and "no está en el catálogo" in x for x in f), "validador: un tipo de pieza desconocido no falla: %s" % f[:2])
f, av = fallas_de(lambda m: m["eventos"][2].update(color="rojo"))
ok(not f and any("`color`" in a for a in av), "validador: un parámetro que la ficha no declara debe avisar (no fallar): %s · %s" % (f[:2], av))

# ---------- 3. Blender: un tipo que solo dibuja three.js ----------
v_real = dict(M3.vocabulario())
try:
    M3._VOCAB["v"] = dict(v_real, onda=dict(v_real["onda"], motores=["three"]))
    f, _ = fallas_de(lambda m: m.update(estilo="arquitecto"))
    ok(any(x.startswith("M3D2 ") and "no dibuja «onda»" in x and "three.js" in x for x in f), "blender: un tipo solo de three.js con un estilo de Blender no falla: %s" % f[:2])
    f, _ = fallas_de(lambda m: m.update(estilo="noche"))
    ok(not f, "blender: el mismo guion con un estilo de three.js debía pasar: %s" % f[:2])
finally:
    M3._VOCAB["v"] = v_real

# ---------- 4. el proyecto: solo los módulos que usa (su mundo, sus piezas y eventos), antes del núcleo ----------
m = copy.deepcopy(BASE)
d = os.path.join(TMP, "proyecto")
os.makedirs(d)
R = M3.escribir_proyecto(m, "9:16", d)
usados = sorted(os.path.relpath(os.path.join(r, n), os.path.join(d, "assets", "modulos")) for r, _, ns in os.walk(os.path.join(d, "assets", "modulos")) for n in ns)
esperado = sorted(M3.vocabulario()[t]["modulo"] for t in {p["tipo"] for p in R["piezas"]} | {e["tipo"] for e in R["eventos"]} | {R["mundo"]["escala"]})
ok(usados == esperado, "proyecto: copia %s y la maqueta usa %s" % (usados, esperado))
html = M3.cargar_texto(os.path.join(d, "index.html"))
pos = [html.find('src="assets/modulos/%s"' % x) for x in esperado]
ok(all(p > 0 for p in pos) and max(pos) < html.find('src="assets/motor.js"'), "proyecto: los módulos no se cargan antes de motor.js")

# ---------- 5. el núcleo no nombra ningún tipo ----------
nucleo = M3.cargar_texto(os.path.join(M3.MOTOR, "motor.js"))
nombrados = [t for t in M3.vocabulario() if re.search(r"tipo\s*===?\s*[\"']%s[\"']" % t, nucleo)]
ok(not nombrados, "núcleo: motor.js nombra tipos del vocabulario (%s): van en su módulo" % nombrados)
src = M3.cargar_texto(os.path.join(RAIZ, "scripts", "maqueta3d.py"))
ok(not re.search(r"tipo\"?\]?\s*==\s*[\"'](ruptura|onda|deslizar|resaltar|encender|apagar|parpadear)[\"']", src),
   "núcleo: maqueta3d.py vuelve a nombrar un tipo de evento: sus reglas van en scripts/maqueta_tipos/<tipo>.py")

# ---------- 6. lo que lee la orquestación ----------
L = M3.lineas_catalogo("realizador")
ok(any("`ruptura`" in x and "\"dice\"" in x for x in L), "catálogo legible: el del realizador debe traer los eventos con `dice`")
ok(len("\n".join(M3.lineas_catalogo("critico", escala="pais")).splitlines()) <= 40, "catálogo legible: el del crítico debe caber en una página")

shutil.rmtree(TMP, ignore_errors=True)
for x in F:
    print("FALLA", x)
print("[maqueta · registro del vocabulario] %s" % ("ok" if not F else "%d fallas" % len(F)))
sys.exit(1 if F else 0)
