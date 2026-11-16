#!/usr/bin/env python3
"""La escena viva (scripts/maqueta_escena.py; usuario 2026-11-16), sin render ni red (≈ 4 s):

  base      video/maqueta/fixture/escena_viva.json (la finca con su gente y la tostaduría) pasa M3D1–M3D19 en 9:16 y 4:5
  fichas    cada pieza y objeto del catálogo declara nivel, contiene, animado y gente; un escenario dice lo que contiene
  M3D15     la escena vacía (sin su escenario ni su gente) falla «cuadro lleno»
  M3D16     un solo objeto sobre el suelo falla «variedad»
  M3D17     nada se mueve (sin gente, sin eventos, un objeto quieto) falla «vida»
  M3D18     la cámara lejísimos de lo que mira falla «a su distancia»
  M3D19     un actor levantado sin nada debajo falla «nada flota»
  video     sin `video: true` (una pieza, un caso de prueba de un mundo) los gates no corren
  guion     video3d.py: C3D14 (ficha de escena), C3D15 (sostiene con hecho verificado o genérico), C3D17 (gente),
            C3D18 (un objeto, un papel)
Exit 0 ok · 1 falla. Uso: python3 scripts/pruebas/maqueta_escena.py"""
import copy
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402
import maqueta_escena as ESC  # noqa: E402
import video3d as V3  # noqa: E402

F = []
BASE = M3.cargar_json(os.path.join(M3.MOTOR, "fixture", "escena_viva.json"))


def ok(cond, que):
    if not cond:
        F.append(que)


def fallas_de(cambio=None, formatos=("9:16",)):
    m = copy.deepcopy(BASE)
    if cambio:
        cambio(m)
    return M3.revisar_m(m, list(formatos))[0]


def salta(gate, fallas):
    return any(x.startswith(gate + " ") for x in fallas)


# ---------- base ----------
f = fallas_de(formatos=("9:16", "4:5"))
ok(not f, "base: escena_viva.json debía pasar y falla: %s" % f[:3])

# ---------- fichas ----------
for e in M3.vocabulario().values():
    if e["clase"] in ("pieza", "objeto"):
        ok(e.get("nivel") in ("objeto", "escenario", "fondo") and isinstance(e.get("contiene"), list) and isinstance(e.get("gente"), bool)
           and (e.get("animado") is False or isinstance(e.get("animado"), str)), "ficha %s: faltan nivel, contiene, animado o gente" % e["tipo"])
        ok(e.get("nivel") != "escenario" or len(e["contiene"]) >= 3, "ficha %s: un escenario dice ≥ 3 cosas que contiene" % e["tipo"])


# ---------- negativos: la tostaduría sin su escenario ----------
def solo(m, piezas, eventos=()):
    """Deja el mundo de la tostaduría con esas piezas (y esos eventos en su tramo), para vaciar la escena."""
    m["mundos"]["tostaduria"]["piezas"] = piezas
    m["mundos"]["tostaduria"].pop("protagonista", None)
    tr = m["tramos"][1]
    tr["eventos"], tr["marcas"], tr["anotaciones"] = list(eventos), [], []
    tr["camara"] = [{"t": tr["desde"], "mira": [0, 0], "dist_m": 18, "azimut": 30, "elevacion": 25}, {"t": tr["hasta"], "mira": [0, 0], "dist_m": 16, "azimut": 40, "elevacion": 22}]


f = fallas_de(lambda m: solo(m, [{"id": "calles", "tipo": "calles"}]))
ok(salta("M3D15", f) and salta("M3D16", f) and salta("M3D17", f), "vacía: solo calles debía fallar M3D15, M3D16 y M3D17: %s" % [x[:8] for x in f])
f = fallas_de(lambda m: solo(m, [{"id": "t", "tipo": "actor", "objeto": "tostadora", "lugar": [0, 0]}, {"id": "z", "tipo": "actor", "objeto": "taza", "lugar": [4, 2]}]))
ok(salta("M3D16", f), "dos objetos sueltos (la tostadora y la taza) debía fallar M3D16: %s" % [x[:8] for x in f])
f = fallas_de(lambda m: solo(m, [{"id": "c%d" % i, "tipo": "actor", "objeto": "contenedor", "lugar": [i * 7 - 14, 0]} for i in range(5)]))
ok(salta("M3D17", f), "cinco contenedores quietos debía fallar M3D17 (nada se mueve): %s" % [x[:8] for x in f])


def lejos(m):
    for k in m["tramos"][1]["camara"]:
        if "dist_m" in k:
            k["dist_m"] = 900
f = fallas_de(lejos)
ok(salta("M3D18", f) or salta("M3D15", f), "la cámara a 900 m de la tostaduría debía fallar M3D18 (o M3D15): %s" % [x[:8] for x in f])
f = fallas_de(lambda m: m["mundos"]["tostaduria"]["piezas"].append({"id": "flota", "tipo": "actor", "objeto": "contenedor", "lugar": [60, 60], "lev_m": 150}))
ok(salta("M3D19", f), "un contenedor a 150 m del suelo sin apoyo debía fallar M3D19: %s" % [x[:8] for x in f])
f = fallas_de(lambda m: (m.pop("video"), solo(m, [{"id": "calles", "tipo": "calles"}])))
ok(not any(x[:5] in ("M3D15", "M3D16", "M3D17") for x in f), "sin `video: true` los gates de la escena no corren: %s" % [x[:8] for x in f])

# ---------- la hora (mundo.hora sobre un estilo con `horas`) ----------
def _hora(m, h, mundo="finca"):
    m["mundos"][mundo]["hora"] = h
f = fallas_de(lambda m: _hora(m, "noche"))
ok(not f, "hora: la finca de noche debía pasar: %s" % f[:2])
Rn = M3.resolver(M3.TR.partir((lambda m: (_hora(m, "noche"), m)[1])(copy.deepcopy(BASE)))[0][1], "9:16")
ok(Rn["estilo_cfg"].get("noche") is True and Rn["estilo_cfg"].get("hora") == "noche" and Rn["col"]["fondo"] != M3.resolver(M3.TR.partir(copy.deepcopy(BASE))[0][1], "9:16")["col"]["fondo"],
   "hora: de noche el resolver enciende `noche`, pone la hora y cambia el cielo")
Rd = M3.resolver(M3.TR.partir(copy.deepcopy(BASE))[0][1], "9:16")
ok(not Rd["estilo_cfg"].get("noche") and Rd["estilo_cfg"].get("tinte") in (None, [1.0, 1.0, 1.0]), "hora: sin `hora` es de día, sin tinte ni luces")
f = fallas_de(lambda m: _hora(m, "madrugada"))
ok(salta("M3D1", f), "hora: una hora que el estilo no tiene debía fallar M3D1: %s" % [x[:60] for x in f[:2]])
f = fallas_de(lambda m: (m["mundos"]["finca"].update(estilo="contorno"), _hora(m, "noche")))
ok(salta("M3D1", f), "hora: un estilo sin horas con `hora` debía fallar M3D1: %s" % [x[:60] for x in f[:2]])

# ---------- la medida ----------
partes = M3.TR.partir(copy.deepcopy(BASE))
R = M3.resolver(partes[0][1], "9:16")
r = ESC.medir(M3, partes[0][1], R)
ok(r["lleno"] >= 0.9 and r["vida"] >= 0.9 and r["gente_max"] >= 2 and r["variedad"] >= 5, "medida de la finca: llena, viva, con gente y variada: %s" % {k: v for k, v in r.items() if k != "muestras"})

# ---------- guion (video3d.py): la ficha de escena ----------
MUNDOS = {"finca": copy.deepcopy(BASE["mundos"]["finca"])}
g = {"mundos": MUNDOS, "escenas": []}
import shutil  # noqa: E402
import tempfile  # noqa: E402
T = tempfile.mkdtemp(prefix="v3d-escena-")
os.makedirs(os.path.join(T, "base"))
shutil.copyfile(os.path.join(RAIZ, "sesiones", "_fixture_video3d", "datos.json"), os.path.join(T, "base", "datos.json"))
ESCENA = {"que_pasa": "se cosecha el café a mano", "quien": "recolectores", "con_que": "costales", "se_mueve": "los brazos que cosechan",
          "sostiene": [{"que": "una ladera cualquiera", "generico": True}], "ilustrativa": "caso de prueba"}
fz = V3.revisar_escenas(g, MUNDOS, T)[0]
ok(any(x.startswith("C3D14") for x in fz), "C3D14: un mundo de cerca sin ficha `escena` debía fallar: %s" % fz[:2])
MUNDOS["finca"]["escena"] = copy.deepcopy(ESCENA)
fz = V3.revisar_escenas(g, MUNDOS, T)[0]
ok(not fz, "ficha de escena completa debía pasar: %s" % fz[:2])
MUNDOS["finca"]["escena"]["sostiene"] = [{"que": "árboles de sombra", "hecho": "no-existe-h99"}]
ok(any(x.startswith("C3D15") for x in V3.revisar_escenas(g, MUNDOS, T)[0]), "C3D15: un hecho que no existe debía fallar")
MUNDOS["finca"]["escena"] = dict(ESCENA, ilustrativa="")
ok(any(x.startswith("C3D15") for x in V3.revisar_escenas(g, MUNDOS, T)[0]), "C3D15: todo genérico sin `ilustrativa` debía fallar")
MUNDOS["finca"]["escena"] = copy.deepcopy(ESCENA)
sin_gente = copy.deepcopy(MUNDOS)
sin_gente["finca"]["piezas"] = [dict(p, personas=0) if p.get("tipo") == "cafetal" else p for p in sin_gente["finca"]["piezas"] if p.get("tipo") != "actor"]
ok(any(x.startswith("C3D17") for x in V3.revisar_escenas(g, sin_gente, T)[0]), "C3D17: «recolectores» sin gente en la escena debía fallar")
dos = {"a": {"escala": "esquema", "receta": "campo", "escena": dict(ESCENA, quien="nadie"),
             "piezas": [{"id": "c1", "tipo": "actor", "objeto": "casa", "lugar": [0, 0]}, {"id": "c2", "tipo": "actor", "objeto": "casa", "lugar": [50, 0]}]}}
g2 = {"mundos": dos, "escenas": [{"n": 1, "mundo": "a", "marcas": [{"lugar": [0, 0], "texto": "Beneficio húmedo"}, {"lugar": [50, 0], "texto": "Tostador"}]}]}
ok(any(x.startswith("C3D18") for x in V3.revisar_escenas(g2, dos, T)[0]), "C3D18: la misma casa rotulada como dos cosas debía fallar")

shutil.rmtree(T, ignore_errors=True)
for x in F:
    print("FALLA", x)
print("maqueta_escena: %s" % ("OK" if not F else "%d falla(s)" % len(F)))
sys.exit(1 if F else 0)
