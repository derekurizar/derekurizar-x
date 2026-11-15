#!/usr/bin/env python3
"""Lo que se mueve en la maqueta 3D (Fases 2 y 3: actor, flujo, frenar/acelerar, trazo, anotaciones), sin render ni red:

  modelo     la posición en t es cerrada: la misma al pedirla directo o tras recorrer otros segundos (y en otro orden);
             la trayectoria suavizada que evalúa motor.js (node, sobre los mismos T y S) es la de Python
  cola       tras `frenar` la cola crece HACIA ATRÁS (el último vehículo lento queda cada vez más atrás) y se suelta tras
             `acelerar`; en ningún carril un vehículo atraviesa al de adelante (hueco entre parachoques ≥ 1.5 m siempre)
  parámetros la densidad por encima del tope falla M3D2 con el tope; carriles, objetos, anclas, el acento en un trazo que no
             es el protagonista y un reloj con hora mal escrita fallan; un actor con dos formas de camino falla
  cámara     `mira: {flujo, …}` sigue al vehículo (el punto que mira en t = dónde está en t, con su desfase); `cenital` = 89°
  anclas     `cuantos` da varios vehículos; una anotación fuera de cuadro falla M3D4
  respaldo   en video3d.py, el número de una etiqueta o una medida sin cifra verificada falla C3D5 y con ella pasa; un reloj
             `ilustrativo` sobre un esquema no pide respaldo (sobre un país sí)
  caso       video/maqueta/fixture/trafico.json pasa M3D en los dos formatos
Exit 0 ok · 1 falla. Uso: python3 scripts/pruebas/maqueta_movimiento.py"""
import copy
import json
import math
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402
from maqueta_tipos import _movimiento as MV  # noqa: E402

F = []
TRAFICO = M3.cargar_json(os.path.join(M3.MOTOR, "fixture", "trafico.json"))


def ok(cond, que):
    if not cond:
        F.append(que)


def fallas_de(base, cambio=None, formatos=("9:16",)):
    m = copy.deepcopy(base)
    if cambio:
        cambio(m)
    return M3.revisar_m(m, list(formatos))[0]


def salta(gate, fallas, texto=""):
    return any(x.startswith(gate + " ") and texto in x for x in fallas)


# ---------- el caso integrador ----------
f = fallas_de(TRAFICO, formatos=("9:16", "4:5"))
ok(not f, "caso trafico.json: debía pasar y falla: %s" % f[:3])
R = M3.resolver(copy.deepcopy(TRAFICO), "9:16", [])
M = R["_moviles"]["este"]

# ---------- modelo: posición cerrada en t ----------
ts = [0.0, 3.3, 6.1, 9.7, 12.4, 15.0, 17.9]
directo = {(t, n): M.en(t, n) for t in ts for n in (0, 40, 85, len(M) - 1)}
for t in reversed(ts):                     # otro camino: al revés y con otros segundos entre medio
    M.en(t + 0.37, 3)
    for n in (len(M) - 1, 85, 40, 0):
        ok(M.en(t, n) == directo[(t, n)], "modelo: la posición del vehículo %d en t = %g cambia según el camino" % (n, t))

# ---------- cola: crece hacia atrás y nadie atraviesa a nadie ----------
info = [p for p in R["piezas"] if p["id"] == "este"][0]
L = {o: M3.ficha(o, "objeto")["medidas"]["largo_m"] for o in info["tipos"]}
por_carril = {}
for n, v in enumerate(info["vehiculos"]):
    por_carril.setdefault(v[0], []).append((n, L[info["tipos"][v[1]]]))
peor = 1e9
for c, lista in por_carril.items():
    for k in range(0, int(R["dur"] * 10) + 1):
        t = k / 10
        s = [(M.s_en(t, n)[0], l) for n, l in lista]
        for (sa, la), (sb, lb) in zip(s, s[1:]):
            peor = min(peor, sa - sb - (la + lb) / 2)
ok(peor >= 1.5, "cola: dos vehículos del mismo carril se acercan a %.2f m entre parachoques (mínimo 1.5): uno atraviesa al otro" % peor)


def ultimo_lento(t, carril=1):
    xs = [M.s_en(t, n)[0] for n, _ in por_carril[carril] if M.s_en(t, n)[1] < 15 / 3.6 and 0 <= M.s_en(t, n)[0] <= info["largos"][carril]]
    return min(xs) if xs else None


colas = [ultimo_lento(t) for t in (7.0, 10.0, 13.0, 16.0)]
ok(all(c is not None for c in colas) and colas[0] > colas[1] > colas[2] > colas[3],
   "cola: tras frenar, el último vehículo lento debía quedar cada vez más atrás: %s" % colas)
sin_frenar = M3.resolver(dict(copy.deepcopy(TRAFICO), eventos=[e for e in TRAFICO["eventos"] if e["tipo"] != "frenar"]), "9:16", [])["_moviles"]["este"]
ok(all(abs(sin_frenar.s_en(t, n)[1] - 80 / 3.6) < 1e-3 for t in (5.0, 12.0) for n in range(0, len(sin_frenar), 7)),
   "cola: sin frenar, todo el flujo va a su velocidad base")
# acelerar suelta la cola
con_acel = copy.deepcopy(TRAFICO)
con_acel["eventos"].append({"t": 9.0, "dur": 1.5, "tipo": "acelerar", "flujo": "este", "en": "frenada", "vel_kmh": 80})
Ma = M3.resolver(con_acel, "9:16", [])["_moviles"]["este"]
lentos = lambda MM, t: sum(1 for n in range(len(MM)) if MM.en(t, n)[5] and MM.en(t, n)[4] < 15 / 3.6)
ok(lentos(Ma, 17.5) < lentos(M, 17.5) / 3, "cola: tras acelerar, la cola se suelta (%d lentos contra %d)" % (lentos(Ma, 17.5), lentos(M, 17.5)))

# ---------- el motor evalúa lo mismo que Python (node sobre motor.js → tray) ----------
if shutil.which("node"):
    js = open(os.path.join(M3.MOTOR, "motor.js"), encoding="utf-8").read()
    a, b = js.index("const tray = {"), js.index("// los móviles:")
    v = info["vehiculos"][85]
    pruebas = [-1.0, 0.0, 4.95, 10.3, 12.71, 17.99, 25.0]
    src = js[a:b] + "\nconst r = tray.nueva(%s, %s); console.log(JSON.stringify(%s.map((t) => tray.suave(r, %s, t))));" % (
        json.dumps(v[3]), json.dumps(v[4]), json.dumps(pruebas), json.dumps(info["h"]))
    p = subprocess.run(["node", "-e", src], capture_output=True, text=True)
    try:
        jsv = json.loads(p.stdout)
        T, S = v[3], v[4]
        Fi = MV.integral(T, S)
        for t, (sj, vj) in zip(pruebas, jsv):
            sp, vp = MV.suave(T, S, Fi, info["h"], t)
            ok(abs(sj - sp) < 1e-6 and abs(vj - vp) < 1e-6, "motor: tray.suave en t = %g da %.6f y Python %.6f" % (t, sj, sp))
    except (ValueError, TypeError):
        F.append("motor: node no evaluó tray (%s)" % (p.stderr.strip()[-200:]))

# ---------- parámetros ----------
def flujo_mas(**k):
    def c(m):
        for p in m["mundo"]["piezas"]:
            if p["id"] == "este":
                p.update(k)
    return c


f = fallas_de(TRAFICO, flujo_mas(densidad=60))
ok(salta("M3D2", f, "tope"), "parámetros: densidad 60 a 80 km/h debía fallar M3D2 con su tope: %s" % f[:2])
f = fallas_de(TRAFICO, flujo_mas(carriles=["carril-9"]))
ok(salta("M3D2", f, "carril-9"), "parámetros: un carril que no existe debía fallar M3D2: %s" % f[:2])
f = fallas_de(TRAFICO, flujo_mas(tipos={"avion": 1}))
ok(salta("M3D2", f, "avion"), "parámetros: un objeto que no está en el catálogo debía fallar M3D2: %s" % f[:2])
f = fallas_de(TRAFICO, flujo_mas(vel_kmh=500))
ok(salta("M3D2", f, "vel_kmh"), "parámetros: vel_kmh fuera de rango debía fallar M3D2: %s" % f[:2])
f = fallas_de(TRAFICO, lambda m: m["mundo"]["piezas"].append({"id": "a", "tipo": "actor", "camino": "carril-1", "lugar": "centro"}))
ok(salta("M3D2", f, "UNA forma"), "parámetros: un actor con camino y lugar debía fallar M3D2: %s" % f[:2])
def acento_ajeno(m):
    m["protagonista"] = "este"
    m["mundo"]["piezas"][-1]["color"] = "acento"


f = fallas_de(TRAFICO, acento_ajeno)
ok(salta("M3D2", f, "acento"), "parámetros: un trazo en el acento que no es el protagonista debía fallar M3D2: %s" % f[:2])
f = fallas_de(TRAFICO, lambda m: m["anotaciones"][0].update(de="8:74:21"))
ok(salta("M3D2", f, "H:MM:SS"), "parámetros: un reloj con una hora mal escrita debía fallar M3D2: %s" % f[:2])
f = fallas_de(TRAFICO, lambda m: m["anotaciones"][1].update(sigue={"flujo": "nadie", "n": 0}))
ok(salta("M3D2", f, "nadie"), "parámetros: un ancla a una pieza que no existe debía fallar M3D2: %s" % f[:2])
f = fallas_de(TRAFICO, lambda m: m["eventos"].append({"t": 2, "dur": 1, "tipo": "frenar", "flujo": "estado", "en": "frenada"}))
ok(salta("M3D2", f, "flujo"), "parámetros: frenar sobre una pieza que no es un flujo debía fallar M3D2: %s" % f[:2])

# ---------- cámara que sigue y cenital ----------
k = [c for c in R["camara"] if c.get("sigue")][1]
sg = k["sigue"]
for t in (11.5, 13.0, 16.0):
    c = M3.camara_en(R["camara"], t)
    x, y = MV.ancla_en(sg, t, R["_moviles"])[:2]
    if k["t"] <= t <= [c2 for c2 in R["camara"] if c2.get("sigue")][-1]["t"]:
        ok(math.hypot(c["x"] - x, c["y"] - y) < 1e-6, "cámara: en t = %g mira (%.2f, %.2f) y el vehículo está en (%.2f, %.2f)" % (t, c["x"], c["y"], x, y))
ok(R["camara"][0]["elevacion"] == 89.0, "cámara: `cenital: true` debía ser elevación 89")
ok("_pos" not in json.dumps({k2: v2 for k2, v2 in R["camara"][3].items() if k2 != "_pos"}) and R["camara"][3].get("sigue"),
   "cámara: la clave que sigue lleva `sigue`")

# ---------- anclas ----------
pulso = [a for a in R["anotaciones"] if a["tipo"] == "pulso"][0]
ok(len(pulso["sobre"]) == 5 and len({a["n"] for a in pulso["sobre"]}) == 5, "anclas: `cuantos: 5` debía dar 5 vehículos distintos")
f = fallas_de(TRAFICO, lambda m: m["anotaciones"][4].update(sigue={"flujo": "este", "cerca": "inicio", "t": 14.0}))
ok(salta("M3D4", f, "etiqueta"), "anclas: una etiqueta sobre un carro que la cámara no encuadra debía fallar M3D4: %s" % f[:2])

# ---------- respaldo de números (video3d.py C3D5) ----------
etq = {"tipo": "etiqueta", "texto": "102 km/h"}
med = {"tipo": "medida", "radio_m": 5}
rel = {"tipo": "reloj", "de": "8:14:21", "a": "8:14:22", "ilustrativo": True}
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402
for o, esc, pide in ((etq, "esquema", ["102"]), (med, "esquema", ["5"]), (rel, "esquema", []), (rel, "ciudad", ["8"])):
    txt = M3.textos_anotacion(o, esc)
    sin = [x for t_ in txt for x in VD.sin_respaldo(t_, [])]
    ok(all(any(p in str(s) for s in sin) for p in pide) and (pide or not sin),
       "respaldo: %s en %s debía pedir respaldo para %s y pide %s" % (o["tipo"], esc, pide, sin))
    if pide:
        con = [x for t_ in txt for x in VD.sin_respaldo(t_, [(float(v_), 1.0) for v_ in ("102", "5", "8", "14", "21", "22")])]
        ok(not con, "respaldo: %s con sus cifras verificadas no debía pedir nada: %s" % (o["tipo"], con))

if F:
    for x in F:
        print("FALLA", x)
    sys.exit(1)
print("maqueta: movimiento OK (modelo cerrado, cola hacia atrás sin atravesarse, motor = Python, parámetros, cámara que sigue, anclas, respaldo, caso tráfico)")
