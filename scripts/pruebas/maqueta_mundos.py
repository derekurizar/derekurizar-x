#!/usr/bin/env python3
"""Los mundos de la maqueta 3D (Fase 1: pais · ciudad · esquema), sin render ni red (≈ 2 s):

  escalas   un tipo cuya ficha no incluye la escala del mundo falla M3D2 (falla en un esquema, calles en un país, onda en una
            ciudad); un set de otra escala falla M3D1; el mundo pais resuelve igual que antes (dist = dist_km)
  esquema   cada receta se arma; la misma semilla da exactamente los mismos datos y otra semilla otros; la receta carretera
            publica eje y carril-1…N en el sentido de la marcha; los lugares genéricos (centro, norte, sur, este, oeste)
  M3D12     el caso esquema pasa; sin «Esquema» en el aviso, con un lugar o una marca que se llaman como un lugar real: falla
  cámara    la distancia va en la unidad de la escala (dist_km en pais, dist_m en ciudad y esquema) y en su rango
  ciudad    el set de la capital completo (capas, fuente.json con escala y pie, < 5 MB); el pie sin OpenStreetMap falla M3D7;
            `resaltar` con `elemento` resuelve un índice; la carretera publica sus caminos con nombre
Exit 0 ok · 1 falla. Uso: python3 scripts/pruebas/maqueta_mundos.py"""
import contextlib
import copy
import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402
import build_set3d as B  # noqa: E402
from maqueta_tipos import esquema as ESQ  # noqa: E402

F = []
FIX = os.path.join(M3.MOTOR, "fixture")
PAIS = M3.cargar_json(M3.FIXTURE)
ESQUEMA = M3.cargar_json(os.path.join(FIX, "esquema_carretera.json"))
CIUDAD = M3.cargar_json(os.path.join(FIX, "ciudad_capital.json"))


def ok(cond, que):
    if not cond:
        F.append(que)


def fallas_de(base, cambio=None, formatos=("9:16",)):
    m = copy.deepcopy(base)
    if cambio:
        cambio(m)
    return M3.revisar_m(m, list(formatos))[0]


def salta(gate, fallas):
    return any(x.startswith(gate + " ") for x in fallas)


# ---------- los casos de prueba pasan ----------
for nombre, base in (("pais", PAIS), ("esquema", ESQUEMA), ("ciudad", CIUDAD)):
    f = fallas_de(base, formatos=("9:16", "4:5"))
    ok(not f, "caso %s: debía pasar y falla: %s" % (nombre, f[:3]))

# ---------- escalas ----------
f = fallas_de(ESQUEMA, lambda m: m["mundo"]["piezas"].append({"id": "x", "tipo": "falla", "trazos": ["Motagua Fault"]}))
ok(salta("M3D2", f) and "escala esquema" in " ".join(f), "escalas: una falla en un esquema debía fallar M3D2: %s" % f[:2])
f = fallas_de(PAIS, lambda m: m["mundo"]["piezas"].append({"id": "c", "tipo": "calles"}))
ok(salta("M3D2", f) and "escala pais" in " ".join(f), "escalas: calles en un país debía fallar M3D2: %s" % f[:2])
f = fallas_de(CIUDAD, lambda m: m["eventos"].append({"t": 5.0, "dur": 1.0, "tipo": "onda", "centro": "capital", "radio_km": 2}))
ok(salta("M3D2", f), "escalas: una onda en una ciudad debía fallar M3D2: %s" % f[:2])
f = fallas_de(CIUDAD, lambda m: m["mundo"].update(set="guatemala"))
ok(salta("M3D1", f) and "escala pais" in f[0], "escalas: un mundo ciudad con un set de país debía fallar M3D1: %s" % f[:2])
f = fallas_de(PAIS, lambda m: m["mundo"].update(set="capital"))
ok(salta("M3D1", f), "escalas: un mundo pais con un set de ciudad debía fallar M3D1: %s" % f[:2])
f = fallas_de(PAIS, lambda m: m["mundo"].update(escala="luna"))
ok(salta("M3D2", f), "escalas: una escala que no está en el catálogo debía fallar M3D2: %s" % f[:2])
R = M3.resolver(copy.deepcopy(PAIS), "9:16")
ok(R["mundo"]["escala"] == "pais" and R["mundo"]["unidad_m"] == 1000 and all(k["dist"] == k["dist_km"] for k in R["camara"]),
   "pais: el mundo pais debía resolver con unidad 1000 m y dist = dist_km")
ok("relieve" in R and "frontera" in R, "pais: el resuelto debía conservar relieve y frontera en su primer nivel (motor.js pais y Blender)")
for t, f_ in M3.vocabulario().items():
    ok(set(f_["escalas"]) <= set(M3.ESCALAS) and f_["escalas"], "escalas: la ficha de «%s» no declara escalas válidas" % t)

# ---------- el esquema: determinista y con sus caminos ----------
for receta in ESQ.RECETAS:
    a, b = ESQ.Esquema(receta, 7), ESQ.Esquema(receta, 7)
    ok(json.dumps(a.datos(), sort_keys=True) == json.dumps(b.datos(), sort_keys=True), "esquema %s: la misma semilla no da los mismos datos" % receta)
    ok(all(k in a.lugares for k in ("centro", "norte", "sur", "este", "oeste")), "esquema %s: faltan los lugares genéricos" % receta)
    ok(a.calles and a.caminos, "esquema %s: sin calles o sin caminos con nombre" % receta)
    ok(all(c[0][2] == 0 and all(q[2] >= p[2] for p, q in zip(c, c[1:])) for c in a.caminos.values()), "esquema %s: un camino sin s creciente" % receta)
    m = copy.deepcopy(ESQUEMA)
    m["mundo"].update(receta=receta, piezas=[{"id": "calles", "tipo": "calles"}])
    m["camara"] = [{"t": 0.0, "mira": "centro", "dist_m": 1500, "azimut": 0, "elevacion": 60}, {"t": 11.0, "mira": "centro", "dist_m": 1200, "azimut": 10, "elevacion": 55}]
    m["eventos"], m["marcas"], m["protagonista"] = [{"t": 0.0, "dur": 2.0, "tipo": "resaltar", "lugar": "centro"}], [], "calles"
    f = M3.revisar_m(m, ["9:16"])[0]
    ok(not f, "esquema %s: una maqueta mínima debía pasar: %s" % (receta, f[:2]))
c1, c2 = ESQ.Esquema("ciudad", 7), ESQ.Esquema("ciudad", 8)
ok([e[0] for e in c1.edificios] != [e[0] for e in c2.edificios], "esquema: otra semilla debía dar otras alturas")
car = ESQ.Esquema("carretera", 7, carriles=4)
ok(set(car.caminos) >= {"eje", "carril-1", "carril-2", "carril-3", "carril-4"}, "esquema carretera: faltan eje o carril-k: %s" % sorted(car.caminos)[:8])
ok(car.caminos["carril-1"][-1][0] > car.caminos["carril-1"][0][0] and car.caminos["carril-3"][-1][0] < car.caminos["carril-3"][0][0],
   "esquema carretera: carril-1 va al este y carril-3 al oeste (en el sentido de la marcha)")
ok(car.caminos["carril-1"][0][1] < 0 < car.caminos["carril-3"][0][1], "esquema carretera: se circula por la derecha (carril-1 al sur del eje)")

# ---------- M3D12 ----------
f = fallas_de(ESQUEMA, lambda m: m["capa"].update(aviso="Maqueta"))
ok(salta("M3D12", f), "M3D12: un esquema sin «Esquema» en el aviso debía fallar: %s" % f[:2])
f = fallas_de(ESQUEMA, lambda m: m["capa"].pop("aviso"))
ok(salta("M3D12", f), "M3D12: un esquema sin aviso debía fallar")
f = fallas_de(ESQUEMA, lambda m: m["mundo"]["lugares"].update(mixco={"x": 100, "y": 200, "nombre": "Mixco"}))
ok(salta("M3D12", f), "M3D12: un lugar del esquema llamado como un lugar real debía fallar: %s" % f[:2])
f = fallas_de(ESQUEMA, lambda m: m["marcas"][0].update(texto="Antigua Guatemala"))
ok(salta("M3D12", f), "M3D12: una marca con el nombre de un lugar real sobre un esquema debía fallar: %s" % f[:2])
f = fallas_de(CIUDAD, lambda m: m["marcas"][0].update(texto="Antigua Guatemala"))
ok(not salta("M3D12", f), "M3D12: en una ciudad real los nombres reales valen")
with contextlib.redirect_stdout(io.StringIO()):
    f = fallas_de(ESQUEMA, lambda m: m.pop("capa"), formatos=("950x1040",))
ok(not salta("M3D12", f), "M3D12: en modo pieza sin capa el aviso lo pone el anfitrión: %s" % f[:2])

# ---------- la cámara: unidad y rango por escala ----------
f = fallas_de(CIUDAD, lambda m: m["camara"][0].update(dist_m=20))
ok(salta("M3D3", f) and "dist_m" in " ".join(f), "cámara: dist_m = 20 en una ciudad (tope 40 m) debía fallar M3D3: %s" % f[:2])
f = fallas_de(ESQUEMA, lambda m: m["camara"][0].update(dist_m=8000))
ok(salta("M3D3", f), "cámara: dist_m = 8000 en un esquema (tope 5000 m) debía fallar M3D3")
f = fallas_de(PAIS, lambda m: [k.update(dist_m=k.pop("dist_km") * 1000) for k in m["camara"]])
ok(salta("M3D3", f) and "dist_km" in " ".join(f), "cámara: dist_m en un país debía fallar M3D3 (va en dist_km): %s" % f[:2])
f = fallas_de(CIUDAD, lambda m: [k.update(dist_km=k.pop("dist_m") / 1000) for k in m["camara"]])
ok(salta("M3D3", f) and "dist_m" in " ".join(f), "cámara: dist_km en una ciudad debía fallar M3D3 (va en dist_m): %s" % f[:2])
for esc in M3.ESCALAS:
    cam = M3.ficha(esc, "mundo")["camara"]
    ok(cam["campo"] == ("dist_km" if esc == "pais" else "dist_m"), "cámara: la escala %s debía medir en %s" % (esc, cam["campo"]))

# ---------- la ciudad: el set, el pie, los elementos y los caminos ----------
with contextlib.redirect_stdout(io.StringIO()) as sal:
    rc = B.revisar("capital")
ok(rc == 0, "set capital: build_set3d.py capital --check falla: %s" % sal.getvalue()[-300:])
d = os.path.join(M3.SETS, "capital")
fu = M3.cargar_json(os.path.join(d, "fuente.json"))
ok(fu.get("escala") == "ciudad" and set(fu["capas"]) == {"relieve", "calles", "edificios", "agua", "zonas", "lugares"},
   "set capital: fuente.json sin escala ciudad o sin sus seis capas")
ok("OpenStreetMap" in fu["pie"] and "Mapzen" in fu["pie"], "set capital: el pie no nombra OpenStreetMap y Mapzen")
peso = sum(os.path.getsize(os.path.join(d, x)) for x in os.listdir(d))
ok(peso < 5e6, "set capital: pesa %.1f MB (tope 5)" % (peso / 1e6))
ok(M3.escala_set("capital") == "ciudad" and "capital" in M3.lista_sets("ciudad") and "capital" not in M3.lista_sets("pais"), "set capital: lista_sets no lo da como ciudad")
f = fallas_de(CIUDAD, lambda m: m["capa"].update(pie="Relieve: Mapzen Terrain Tiles"))
ok(salta("M3D7", f) and "OpenStreetMap" in " ".join(f), "ciudad: el pie sin OpenStreetMap debía fallar M3D7: %s" % f[:2])
R = M3.resolver(copy.deepcopy(CIUDAD), "9:16")
ev = [e for e in R["eventos"] if e.get("pieza") == "edificios"][0]
ok(isinstance(ev.get("indice"), int) and ev["indice"] >= 0, "ciudad: resaltar con `elemento` no resolvió el índice del edificio")
nombres = M3.cargar_json(os.path.join(d, "edificios.json"))["nombres"]
pz = [p for p in R["piezas"] if p["id"] == "edificios"][0]
ok(pz["nombres"].get(str(ev["indice"])) == "Dubai Center", "ciudad: el elemento debía ser el Dubai Center (es %r)" % pz["nombres"].get(str(ev["indice"])))
ok({"bolivar", "bolivar.carril-1", "bolivar.carril-4"} <= set(R["mundo"]["caminos"]), "ciudad: la carretera no publicó sus caminos: %s" % sorted(R["mundo"]["caminos"])[:6])
ok(R["mundo"]["escala"] == "ciudad" and R["mundo"]["unidad_m"] == 1 and "relieve" in R["mundo"], "ciudad: el mundo resuelto no trae escala, unidad o relieve")
f = fallas_de(CIUDAD, lambda m: m["eventos"][1].update(pieza="parques"))
ok(salta("M3D2", f), "resaltar: `elemento` con una pieza sin elementos (zona) debía fallar M3D2: %s" % f[:2])
Re = M3.resolver(copy.deepcopy(ESQUEMA), "9:16")
ok({"eje", "carril-1", "autopista", "autopista.carril-2"} <= set(Re["mundo"]["caminos"]) and "centro" in Re["mundo"]["lugares"],
   "esquema: el mundo resuelto debía traer los caminos de la receta y de la carretera, y sus lugares")

for x in F:
    print("FALLA", x)
print("[maqueta · mundos] %s" % ("ok" if not F else "%d fallas" % len(F)))
sys.exit(1 if F else 0)
