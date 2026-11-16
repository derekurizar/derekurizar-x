#!/usr/bin/env python3
"""Varios mundos en un video (tramos, scripts/maqueta_tramos.py; usuario 2026-11-15), sin render ni red (≈ 3 s):

  base      video/maqueta/fixture/tramos.json pasa M3D1–M3D13 en 9:16 y 4:5
  M3D13     hueco entre tramos, tramo < 2.5 s, mundo inexistente, transición desconocida, evento fuera de su tramo,
            `mundo` y `mundos` a la vez, un mundo sin usar, la cámara en el primer nivel: fallan
  partir    los tiempos son locales al tramo (con medio fundido de más), la cámara abre en t = 0, el protagonista es el de
            su mundo, la capa del tramo trae solo lo que se cruza con su ventana; las duraciones encadenadas dan el video
  gates     una falla de un tramo dice su tramo; un estilo de Blender con un esquema falla M3D2; el aviso «Esquema» solo
            en las ventanas de los esquemas
  guion     video3d.py: un guion de un mundo da la misma maqueta de siempre (sin tramos); con `mundos`, construir hace un
            tramo por racha de escenas del mismo mundo; C3D12 (escena con un mundo que no existe, un mundo sin usar)
Exit 0 ok · 1 falla. Uso: python3 scripts/pruebas/maqueta_tramos.py"""
import copy
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402
import maqueta_tramos as TR  # noqa: E402
import video3d as V3  # noqa: E402

F = []
BASE = M3.cargar_json(M3.FIXTURE_TRAMOS)


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
ok(not f, "base: tramos.json debía pasar y falla: %s" % f[:3])

# ---------- M3D13 ----------
NEG = [
    ("hueco entre tramos", lambda m: m["tramos"][1].update(desde=5.4)),
    ("tramo < 2.5 s", lambda m: (m["tramos"][1].update(hasta=7.0), m["tramos"][2].update(desde=7.0))),
    ("mundo inexistente", lambda m: m["tramos"][2].update(mundo="luna")),
    ("transición desconocida", lambda m: m["tramos"][1].update(transicion="barrido")),
    ("evento fuera de su tramo", lambda m: m["tramos"][0]["eventos"].append({"t": 4.0, "dur": 2.0, "tipo": "resaltar", "lugar": "pueblo"})),
    ("mundo y mundos a la vez", lambda m: m.update(mundo={"set": "guatemala"})),
    ("un mundo sin usar", lambda m: m["mundos"].update(sobra={"escala": "esquema", "receta": "plaza", "piezas": []})),
    ("cámara en el primer nivel", lambda m: m.update(camara=[{"t": 0, "mira": "guatemala", "dist_km": 500}])),
    ("el último tramo no llega al final", lambda m: m.update(duracion_s=16.0)),
]
for que, cambio in NEG:
    f = fallas_de(cambio)
    ok(salta("M3D13", f), "M3D13 · %s: debía fallar M3D13 y dio %s" % (que, f[:2]))

# ---------- partir ----------
partes = TR.partir(copy.deepcopy(BASE))
ok(len(partes) == 3, "partir: 3 tramos y salen %d" % len(partes))
i0, s0 = partes[0]
i1, s1 = partes[1]
i2, s2 = partes[2]
ok(i0["pre"] == 0 and abs(i0["post"] - 0.3) < 1e-9 and abs(i1["pre"] - 0.3) < 1e-9 and i1["post"] == 0 and i2["pre"] == 0,
   "partir: medio fundido de 0.6 s a cada lado del límite campo→país y nada en el corte país→costa (%s)" % [(x["pre"], x["post"]) for x, _ in partes])
ok(abs(i1["off"] - 4.7) < 1e-9 and s1["camara"][0]["t"] == 0.0, "partir: el tramo 2 empieza a grabarse en 4.7 s y su cámara abre en t = 0")
ok(abs(s1["eventos"][0]["t"] - (5.4 - 4.7)) < 1e-6, "partir: el evento del tramo 2 pasa a su tiempo local (0.7 s): %s" % s1["eventos"][0]["t"])
ok(s0.get("protagonista") == "camion" and s1.get("protagonista") == "ruta" and "protagonista" not in s2,
   "partir: el protagonista es el de cada mundo (%s)" % [s.get("protagonista") for _, s in partes])
ok("protagonista" not in s0["mundo"], "partir: `protagonista` sale del mundo (no es un parámetro del mundo)")
ok([t["texto"] for t in s1["capa"]["titulares"]] == ["La ruta cruza el país"], "partir: la capa del tramo 2 solo trae su titular: %s" % s1["capa"]["titulares"])
tot = sum(x["dur"] for x, _ in partes) - sum(x["fundido"] for x, _ in partes if x["transicion"] in ("fundido", "oscuro"))
ok(abs(tot - BASE["duracion_s"]) < 1e-6, "partir: los tramos encadenados (menos los cruces) dan %.3f s y el video dura %.3f" % (tot, BASE["duracion_s"]))
ok(TR.tramo_en(BASE, 5.0)[0]["n"] == 1 and TR.tramo_en(BASE, 15.0)[0]["n"] == 2, "tramo_en: el segundo 5 es del tramo 2 y el final del último")

# ---------- gates ----------
f = fallas_de(lambda m: m["tramos"][1]["camara"].__setitem__(0, dict(m["tramos"][1]["camara"][0], mira="no-existe")))
ok(salta("M3D2", f) and "[tramo 2" in " ".join(f), "gates: una falla de un tramo dice su tramo: %s" % f[:2])
f = fallas_de(lambda m: m.update(estilo="arquitecto"))
ok(salta("M3D2", f) and "esquema" in " ".join(f), "gates: un estilo de Blender con un esquema debía fallar M3D2: %s" % f[:2])
g = TR.capa_global(copy.deepcopy(BASE))
ok(g["capa"]["aviso_ventanas"] == [[0.0, 5.0], [11.0, 15.0]], "aviso: «Esquema» solo en el campo y la costa: %s" % g["capa"]["aviso_ventanas"])
ok(TR.efectos(BASE) == [[0.0, "pulso"], [5.4, "whoosh"]], "efectos: los sfx de los tramos en tiempo del video: %s" % TR.efectos(BASE))

# ---------- estilo por mundo (2026-11-16) ----------
def _dia(m):
    m["mundos"]["campo"]["estilo"] = "dia"
f = fallas_de(_dia)
ok(not f, "estilo por mundo: el campo en `dia` y el país en noche debía pasar: %s" % f[:2])
ok(TR.partir(dict(copy.deepcopy(BASE), mundos=dict(copy.deepcopy(BASE)["mundos"], campo=dict(BASE["mundos"]["campo"], estilo="dia"))))[0][1]["estilo"] == "dia",
   "estilo por mundo: el tramo del campo se graba en `dia`")
f = fallas_de(lambda m: m["mundos"]["campo"].update(estilo="acuarela"))
ok(salta("M3D13", f), "estilo por mundo: un estilo que no existe debía fallar M3D13: %s" % f[:2])

# ---------- M3D14: lo que la cámara sigue no se traba ----------
def _barco_quieto(m):
    m["mundos"]["campo"]["piezas"][3]["claves"] = [{"t": 0, "s": "30%", "vel_kmh": 50}, {"t": 1.5, "s": "40%", "vel_kmh": 0}]
    m["tramos"][0]["camara"].insert(1, {"t": 0.5, "mira": {"actor": "camion"}, "dist_m": 120, "azimut": 0, "elevacion": 50})
f = fallas_de(_barco_quieto)
ok(salta("M3D14", f), "M3D14: la cámara que sigue a un camión ya detenido debía fallar: %s" % [x[:90] for x in f[:3]])

# ---------- guion (video3d.py) ----------
FIXV = os.path.join(RAIZ, "sesiones", "_fixture_video3d")
if os.path.exists(os.path.join(FIXV, "guion.json")):
    import json
    import shutil
    import tempfile
    T = tempfile.mkdtemp(prefix="v3d-tramos-")
    try:
        os.makedirs(os.path.join(T, "base"))
        os.makedirs(os.path.join(T, "audio"))
        shutil.copyfile(os.path.join(FIXV, "video3d.json"), os.path.join(T, "video3d.json"))
        shutil.copyfile(os.path.join(FIXV, "datos.json"), os.path.join(T, "base", "datos.json"))
        g1 = M3.cargar_json(os.path.join(FIXV, "guion.json"))
        st = V3.estado(T)
        f, _, loc = V3.revisar_guion(g1, st, T)
        m1, _, _ = V3.construir(T, g1, loc, real=False)
        ok("tramos" not in m1 and "mundo" in m1, "guion: un solo mundo da la maqueta de siempre (sin tramos)")
        g2 = copy.deepcopy(g1)
        pais = g2.pop("mundo")
        g2["mundos"] = {"pais": pais, "pueblo": {"escala": "esquema", "receta": "ciudad", "semilla": 3, "tamano_m": 1400, "protagonista": "casas",
                                                  "piezas": [{"id": "calles", "tipo": "calles"}, {"id": "casas", "tipo": "edificios"}],
                                                  # la ficha de la escena (C3D14–C3D15): aquí, un lugar cualquiera (la riqueza la prueba maqueta_escena.py)
                                                  "escena": {"que_pasa": "un pueblo cualquiera", "quien": "nadie", "con_que": "casas y calles", "se_mueve": "la cámara",
                                                             "sostiene": [{"que": "un pueblo genérico", "generico": True}], "ilustrativa": "caso de prueba de los tramos"}}}
        for e in g2["escenas"]:
            e["mundo"] = "pais"
        c = g2["escenas"][-1]
        c.update(mundo="pueblo", transicion="fundido", eventos=[{"tipo": "resaltar", "lugar": "centro", "dur": 2.0}],
                 camara=[{"mira": "centro", "dist_m": 1300, "azimut": 0, "elevacion": 60}, {"al": "fin", "mira": "centro", "dist_m": 900, "azimut": 20, "elevacion": 50}])
        f, _, loc = V3.revisar_guion(g2, st, T)
        ok(not f, "guion: dos mundos debía pasar C3D y falla: %s" % f[:3])
        m2, _, _ = V3.construir(T, g2, loc, real=False)
        ok([t["mundo"] for t in m2.get("tramos") or []] == ["pais", "pueblo"], "guion: construir hace un tramo por racha (%s)" % [t["mundo"] for t in m2.get("tramos") or []])
        ok(m2["capa"].get("aviso", "").startswith("Esquema"), "guion: con un esquema, el aviso «Esquema» sale solo")
        ok(m2.get("video") is True, "guion: la maqueta de un video lleva `video: true` (activa los gates de la escena viva)")
        m2.pop("video")   # aquí se prueba la mecánica de los tramos; la riqueza de la escena (M3D15–M3D19), en maqueta_escena.py
        fm = M3.revisar_m(m2, ["9:16", "4:5"])[0]
        ok(not fm, "guion: la maqueta de dos mundos debía pasar M3D y falla: %s" % fm[:3])
        g3 = copy.deepcopy(g2)
        g3["escenas"][1]["mundo"] = "luna"
        ok(any(x.startswith("C3D12") for x in V3.revisar_guion(g3, st, T)[0]), "C3D12: una escena en un mundo que no existe debía fallar")
        g5 = copy.deepcopy(g2)
        g5["escenas"][1]["mundo"] = "pueblo"; g5["escenas"][2]["mundo"] = "pais"   # país → pueblo → país → pueblo (cierre)
        ok(any(x.startswith("C3D13") for x in V3.revisar_guion(g5, st, T)[0]), "C3D13: volver a un mundo a mitad del video debía fallar")
        # cambio de mundo a mitad de una escena: el cierre empieza en el país y pasa al pueblo en su última frase
        g6 = copy.deepcopy(g2)
        c6 = g6["escenas"][-1]
        frase = c6["texto"].rstrip(".").split()[-1]
        c6["mundo"] = "pais"
        c6["cambios"] = [{"dice": frase, "mundo": "pueblo", "transicion": "corte"}]
        c6["camara"] = [{"mira": "los-amates", "dist_km": 520, "azimut": 0, "elevacion": 62},
                        {"dice": frase, "mira": "centro", "dist_m": 1300, "azimut": 0, "elevacion": 60},
                        {"al": "fin", "mira": "centro", "dist_m": 900, "azimut": 20, "elevacion": 50}]
        c6["eventos"] = [{"tipo": "resaltar", "pieza": "ruptura", "dur": 1.0}, {"dice": frase, "tipo": "resaltar", "lugar": "centro", "dur": 1.0}]
        f6, _, loc6 = V3.revisar_guion(g6, st, T)
        ok(not [x for x in f6 if x.startswith(("C3D12", "C3D13", "C3D3"))], "cambios: un cambio de mundo a mitad de escena debía pasar: %s" % f6[:3])
        m6, _, _ = V3.construir(T, g6, loc6, real=False)
        tr6 = m6.get("tramos") or []
        ok([t["mundo"] for t in tr6] == ["pais", "pueblo"] and tr6[1]["transicion"] == "corte" and tr6[1]["desde"] > max(x["off"] for x in V3.linea_de_tiempo(T, loc6, False)[0]),
           "cambios: el tramo del pueblo empieza en la frase del cambio (%s)" % [(t["mundo"], t["desde"]) for t in tr6])
        g7 = copy.deepcopy(g6)
        g7["escenas"][-1]["cambios"][0]["dice"] = "una frase que no se dice"
        ok(any(x.startswith("C3D12") for x in V3.revisar_guion(g7, st, T)[0]), "cambios: un cambio anclado a una frase que no se dice debía fallar C3D12")
        g8 = copy.deepcopy(g2)
        g8["mundos"]["pueblo"]["hora"] = "noche"
        ok(any(x.startswith("C3D19") for x in V3.revisar_guion(g8, st, T)[0]), "C3D19: una hora distinta del día sin `hora_razon` debía fallar")
        g8["mundos"]["pueblo"]["hora_razon"] = "el pueblo duerme: pasó de madrugada"
        ok(not any(x.startswith("C3D19") for x in V3.revisar_guion(g8, st, T)[0]), "C3D19: con su razón, la hora pasa")
        g4 = copy.deepcopy(g2)
        g4["mundos"]["sobra"] = {"escala": "esquema", "receta": "plaza", "piezas": []}
        ok(any(x.startswith("C3D12") for x in V3.revisar_guion(g4, st, T)[0]), "C3D12: un mundo sin usar debía fallar")
        _ = json
    finally:
        shutil.rmtree(T, ignore_errors=True)

# el cruce de un fundido (m255), el pie con solo lo usado (m256) y el límite del render (m234)
import maqueta_tramos as TRX  # noqa: E402
import maqueta3d as M3X  # noqa: E402
if True:
    try:
        mf = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "video", "maqueta", "fixture", "tramos.json"), encoding="utf-8"))
        pf = TRX.partir(mf)
        lim = pf[1][0]["desde"]
        x = TRX.cruce_en(pf, lim)
        ok(x and x[0] == "fundido" and abs(x[1] - 0.5) < 1e-6 and x[2][0]["n"] == 0 and x[3][0]["n"] == 1, "cruce_en: en el límite de un fundido se ven los dos tramos a la mitad (%s)" % (x and x[:2],))
        ok(TRX.cruce_en(pf, lim + 1.0) is None, "cruce_en: lejos del límite no hay cruce")
        ok(TRX.cruce_en(pf, pf[2][0]["desde"]) is None, "cruce_en: un corte no cruza")
        pie = V3.pie_de_capas("guatemala", {"relieve", "lugares", "rios", "lagos"})
        ok("GEM" not in pie and "Mapzen" in pie and "ríos y lagos: © OpenStreetMap" in pie, "pie_de_capas: solo lo usado y agrupado por fuente (%s)" % pie)
        os.environ["MAQUETA_RENDER_LIMITE_S"] = "2"
        p_, _ = M3X.correr([sys.executable, "-c", "import time; time.sleep(30)"], ".", None, limite=M3X.limite_render(10))
        ok(p_.returncode == 124, "correr con límite: un proceso colgado se detiene con 124 (dio %s)" % p_.returncode)
        os.environ.pop("MAQUETA_RENDER_LIMITE_S", None)
        ok(M3X.limite_render(100) == M3X.RENDER_LIMITE_BASE_S + 100 * M3X.RENDER_LIMITE_POR_S, "limite_render: proporcional a la duración")
    finally:
        os.environ.pop("MAQUETA_RENDER_LIMITE_S", None)

for x in F:
    print("FALLA", x)
print("maqueta_tramos: %s" % ("OK" if not F else "%d falla(s)" % len(F)))
sys.exit(1 if F else 0)
