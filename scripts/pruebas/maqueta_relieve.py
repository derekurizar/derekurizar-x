#!/usr/bin/env python3
"""El relieve de pieza, los lugares que publica una pieza, el flujo que se ve y el rótulo que no tapa (m250, m253, m270,
m273, m275, m277; 2026-11-16), sin render ni red (≈ 3 s):

  campos    perfil, plano y malla de maqueta_tipos/_relieve.py: lo que valen dentro y fuera; manda el más alto
  camino    un caminomontana publica su calzada: S.suelo sube a lo largo del eje (5 m al pie, 5 + pendiente_m arriba) y
            fuera del camino sigue en 0; un actor en «<id>.carril-1» y la cámara que lo sigue van a esa altura
  cafetal   publica su ladera: 0 fuera del polígono, ≈ pendiente_m en su borde alto; la caja con que se mide la escena
            (M3D15) sigue naciendo en el suelo del mundo
  lugares   `_lugares`: «curva» y «<id>.curva» existen como lugares del mundo; uno del mismo id en mundo.lugares manda
  flujo     solo viajan los vehículos que alguna vez están en su carril: `n: 0` se ve en t = 0
  M3D20     una marca cuya tarjeta cae sobre el actor junto a su ancla avisa (no falla); con más `alto`, ya no
  modulo    la maqueta mínima de maqueta_modulo.py se arma sobre una base donde el ejemplo se resuelve (piezas/carretera)
Exit 0 ok · 1 falla. Uso: python3 scripts/pruebas/maqueta_relieve.py"""
import copy
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402
import maqueta_escena as ESC  # noqa: E402
import maqueta_modulo as MM  # noqa: E402
from maqueta_tipos import _relieve as RL  # noqa: E402

F = []


def ok(cond, que):
    if not cond:
        F.append(que)


# ---------- campos ----------
pf = RL.perfil([[0, 0, 0], [100, 0, 10]], 4)
ok(abs(RL.campo_en(pf, 50, 2) - 5) < 1e-6 and RL.campo_en(pf, 50, 5) is None and RL.campo_en(pf, 200, 0) is None, "perfil: 5 a media línea, nada a más de su ancho")
pl = RL.plano([0, 0, 10, 0, 10, 10, 0, 10], 2)
ok(RL.campo_en(pl, 5, 5) == 2 and RL.campo_en(pl, 11, 5) is None, "plano: su altura dentro, nada fuera")
ml = RL.malla([0, 0, 10, 10], 3, 3, lambda x, y: x + y)
ok(abs(RL.campo_en(ml, 2.5, 7.5) - 10) < 1e-6 and RL.campo_en(ml, -1, 0) is None, "malla: bilineal dentro de su caja")
ok(RL.en([pl, RL.plano([0, 0, 10, 0, 10, 10, 0, 10], 7)], 5, 5) == 7 and RL.en([pl], 50, 50) == 0, "relieve: manda el campo más alto; 0 donde no hay")
try:
    RL.revisar([{"tipo": "rampa"}], "prueba", M3.Falla)
    ok(False, "un campo de tipo desconocido debía fallar")
except M3.Falla:
    pass

# ---------- una maqueta con camino de montaña, cafetal, un actor y un flujo ----------
BASE = M3.cargar_json(os.path.join(M3.MOTOR, "fixture", "esquema_carretera.json"))


def maqueta(piezas, camara=None, marcas=(), lugares=None):
    m = copy.deepcopy(BASE)
    m["estilo"], m["duracion_s"] = "dia", 12.0
    m["mundo"] = {"escala": "esquema", "receta": "campo", "semilla": 4, "tamano_m": 1200, "lugares": lugares or {}, "piezas": piezas}
    m["protagonista"] = piezas[0]["id"]
    m["camara"] = camara or [{"t": 0.0, "mira": [0, 0], "dist_m": 200, "azimut": 0, "elevacion": 30}]
    m["eventos"], m["marcas"] = [{"t": 0.0, "dur": 2.0, "tipo": "resaltar", "pieza": piezas[0]["id"]}], list(marcas)
    C = m["capa"]
    C["titulares"], C["cifras"], C["palabras"] = [{"t": 0.0, "hasta": 3.0, "kicker": "Prueba", "texto": "Relieve"}], [], []
    C["progreso"], C["seguir"] = {"actos": [0.0]}, {"t": 4.0, "dur": 2.0}
    C["cierre"]["t"] = 10.0
    return m


CAMINO = {"id": "camino", "tipo": "caminomontana", "lugar": [0, 0], "rumbo": 0, "curvas": 2, "pendiente_m": 30, "vehiculos": 0, "camion": False, "semilla": 2}
CAMION = {"id": "camion", "tipo": "actor", "objeto": "camionsacos", "camino": "camino.carril-1", "claves": [{"t": 0, "s": "30%", "vel_kmh": 30}]}
BAJAN = {"id": "bajan", "tipo": "flujo", "carriles": ["camino.carril-2"], "tipos": {"carro": 2, "moto": 1}, "densidad": 20, "vel_kmh": 38, "semilla": 3}
CAFETAL = {"id": "cafetal", "tipo": "cafetal", "puntos": [[-200, -330], [-110, -330], [-110, -250], [-200, -250]], "hileras": 10, "pendiente_m": 14, "rumbo": 90, "personas": 2, "semilla": 3}
QUIETA = {"id": "quieta", "tipo": "actor", "objeto": "persona", "lugar": [-140, -290], "rumbo": 200, "pose": "cosechar", "tamano": 1.3}

m = maqueta([CAMINO, CAMION, BAJAN, CAFETAL, QUIETA],
            camara=[{"t": 0.0, "mira": {"actor": "camion"}, "dist_m": 40, "azimut": 250, "elevacion": 14, "mira_lev_m": 1.5},
                    {"t": 12.0, "mira": {"actor": "camion"}, "dist_m": 34, "azimut": 280, "elevacion": 12, "mira_lev_m": 1.5}])
R = M3.resolver(m, "9:16", [])
S, cam = R["_set"], R["mundo"]["caminos"]["camino"]
ok(len(R["mundo"]["alturas"]) == 2 and all(p.get("relieve") for p in R["piezas"] if p["tipo"] in ("caminomontana", "cafetal")), "el camino y el cafetal publican su relieve (mundo.alturas)")
ok(not any(k.startswith("_") for p in R["piezas"] for k in p), "`_caminos`, `_alturas` y `_lugares` no viajan al motor con la pieza")
a, b = S.suelo(cam[0][0], cam[0][1]), S.suelo(cam[-1][0], cam[-1][1])
ok(abs(a - 5.06) < 0.05 and abs(b - 35.06) < 0.05, "camino: 5 m al pie y 35 m arriba (hay %.2f y %.2f)" % (a, b))
ok(S.suelo(0, 400) == 0 and S.suelo_base(cam[0][0], cam[0][1]) == 0, "fuera del camino el suelo sigue en 0; suelo_base no lleva relieve")
x, y = R["_moviles"]["camion"].en(3.0, 0)[:2]
alt = M3.camara_en(R["camara"], 3.0)["alt"]
ok(S.suelo(x, y) > 10 and abs(alt - (S.suelo(x, y) + 1.5)) < 0.6, "la cámara que sigue al camión mira a la altura del camino (%.1f frente a %.1f)" % (alt, S.suelo(x, y) + 1.5))
ok(abs(S.suelo(-150, -251) - 14) < 1.2 and 0 < S.suelo(-150, -329) < 1.0 and S.suelo(-150, -340) == 0 and S.suelo(-100, -290) == 0,
   "cafetal: ≈ pendiente_m en su borde alto, casi 0 en el bajo y 0 fuera (%.2f, %.2f)" % (S.suelo(-150, -251), S.suelo(-150, -329)))
caf = next(c for c in ESC.cosas(M3, R, 0.0) if c["clave"] == "cafetal")
ok(caf["base"] is True, "la pieza con relieve propio se mide desde el suelo del mundo (cosa.base)")

# ---------- lugares publicados ----------
L = R["mundo"]["lugares"]
ok("curva" in L and "camino.curva" in L and L["curva"] == L["camino.curva"], "`_lugares`: «curva» y «camino.curva» son lugares del mundo")
R2 = M3.resolver(maqueta([CAMINO], lugares={"curva": {"x": 50, "y": -60, "nombre": "Otra curva"}}), "9:16", [])
L2 = R2["mundo"]["lugares"]
ok(L2["curva"]["x"] == 50 and L2["camino.curva"]["x"] != 50, "un lugar del mismo id en mundo.lugares manda; el de la pieza queda con su prefijo")

# ---------- el flujo que se ve ----------
M = R["_moviles"]["bajan"]
ok(len(M) > 0 and M.en(0.0, 0)[5], "flujo: `n: 0` está en su carril en t = 0")
largo = R["mundo"]["caminos"]["camino.carril-2"][-1][2]
ok(all(M.s_en(0.0, n)[0] <= largo + 1e-6 and M.s_en(12.0, n)[0] >= -1e-6 for n in range(len(M))), "flujo: ningún vehículo viaja si nunca entra a su carril")

# ---------- M3D20: el rótulo que tapa ----------
ver = [{"t": 0.0, "mira": [-140, -290], "dist_m": 70, "azimut": 20, "elevacion": 20}, {"t": 12.0, "mira": [-140, -290], "dist_m": 60, "azimut": 30, "elevacion": 20}]
mt = maqueta([CAFETAL, QUIETA], camara=ver, marcas=[{"t": 3.2, "hasta": 6.0, "lugar": [-140, -290], "texto": "Cosecha", "alto": 0}])
fa, av = M3.revisar_m(mt, ["9:16"])
ok(any(x.startswith("M3D20 ") and "quieta" in x for x in av), "M3D20: la marca sobre la persona debía avisar: %s" % [x[:60] for x in av])
ok(not any(x.startswith("M3D20") for x in fa), "M3D20 es un aviso, no una falla")
mt["marcas"][0]["alto"] = 220
ok(not any(x.startswith("M3D20 ") for x in M3.revisar_m(mt, ["9:16"])[1]), "M3D20: con la tarjeta arriba (`alto` 220) ya no avisa")

# ---------- la maqueta mínima del banco de pruebas ----------
V = M3.vocabulario()
mm = MM.maqueta_minima("pieza", "carretera", V["carretera"])
try:
    M3.resolver(mm[0], "9:16", [])
    ok("esquema" in mm[3], "maqueta mínima de carretera: debía armarse sobre un esquema (%s)" % mm[3])
except Exception as e:
    ok(False, "maqueta mínima de piezas/carretera no se resuelve: %s" % str(e)[:120])

for x in F:
    print("FALLA", x)
print("maqueta_relieve: %s" % ("OK" if not F else "%d falla(s)" % len(F)))
sys.exit(1 if F else 0)
