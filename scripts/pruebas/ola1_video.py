#!/usr/bin/env python3
"""Pruebas de la ola 1 de mejoras de video (2026-11-14), sin render, sin red y sin créditos:
  1. el gancho y la escena 2 medidos sobre la voz REAL (V9 y P5 en `tiempos`): aviso y falla con palabras fabricadas;
  2. una sola `elegir_musica` que cuenta todos los registros (un «¿Sabías que…?» y una parte de serie cambian la pista);
  3. la rotación mira todo el feed (R9, F7, P3): una parte de serie reciente bloquea su forma de promesa en /video;
  4. quién eligió el gancho y el cierre, en el guion y en el registro (memoria.py --dry-run);
  5. una escena `toma` sigue fallando con TM0 y el código de las tomas y de los sub-planos ya no está;
  6. `podar_intermedios.py` en modo lista (y el borrado, solo sobre el árbol fabricado).
Todo lo que escribe va a un directorio temporal: memoria/ y sesiones/ del repositorio no se tocan. Exit 0 ok · 1 falla."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402
import historia as HI  # noqa: E402
import explica as EX  # noqa: E402
import sabias as SB  # noqa: E402
import congreso as CG  # noqa: E402
import serie as SE  # noqa: E402
import memoria as ME  # noqa: E402

F = []
TMP = tempfile.mkdtemp(prefix="ola1_video_")


def ok(cond, que):
    if not cond:
        F.append(que)


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def correr(*args):
    """Un script del repositorio en un proceso aparte → (código, salida)."""
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", args[0])] + [str(x) for x in args[1:]], cwd=RAIZ,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


# ---------- 1. la voz real del gancho y de la escena 2 ----------
def escena(n, tipo, segundos, texto="uno dos tres cuatro cinco seis siete ocho."):
    """Una escena de escenas.json con palabras fabricadas que terminan a los `segundos` (fin_voz = la última palabra)."""
    ws = texto.split()
    paso = segundos / len(ws)
    pal = [{"text": w, "start": round(i * paso, 3), "end": round((i + 1) * paso, 3)} for i, w in enumerate(ws)]
    return {"n": n, "tipo": tipo, "palabras": pal, "fin_voz": pal[-1]["end"], "dur": round(segundos + 0.7, 3)}


def real(gancho, e2, tipo2="foto"):
    return VD.revisar_voz_real([escena(1, "gancho", gancho), escena(2, tipo2, e2), escena(3, "foto", 9.0), escena(4, "cierre", 8.0)],
                               {"escenas": [{"n": 1, "voz": "x" * 80}, {"n": 2, "voz": "x" * 170}]}, "sesiones/x")


ok(real(5.9, 11.0) == ([], []), "voz real: un gancho de 5.9 s y una escena 2 de 11 s no deben avisar ni fallar: %s" % (real(5.9, 11.0),))
f, av = real(6.2, 11.0)
ok(not f and len(av) == 1 and av[0].startswith("V9 gancho: la voz real dura 6.20 s") and "--solo 1" in av[0] and "5.2 s" in av[0],
   "voz real: un gancho de 6.2 s debe AVISAR con su duración, el estimado y la retoma: %s %s" % (f, av))
f, av = real(6.5, 11.0)
ok(not f and len(av) == 1, "voz real: 6.5 s justos es aviso, no falla: %s %s" % (f, av))
f, av = real(6.72, 11.0)
ok(len(f) == 1 and not av and f[0].startswith("V9 gancho: la voz real dura 6.72 s (máximo 6.5 s") and "--solo 1" in f[0],
   "voz real: un gancho de 6.72 s debe FALLAR y proponer la retoma de solo esa escena: %s %s" % (f, av))
f, av = real(5.0, 12.4)
ok(not f and len(av) == 1 and av[0].startswith("P5 la escena 2 dura 12.40 s de voz real") and "--solo 2" in av[0],
   "voz real: una escena 2 de 12.4 s debe AVISAR (P5): %s %s" % (f, av))
f, av = real(5.0, 13.3)
ok(len(f) == 1 and f[0].startswith("P5 la escena 2 dura 13.30 s de voz real (máximo 13 s"), "voz real: una escena 2 de 13.3 s debe FALLAR (P5): %s" % f)
f, av = real(7.0, 14.0)
ok(len(f) == 2, "voz real: gancho y escena 2 largos son dos fallas: %s" % f)
# un video de gancho + escena + cierre: la escena 2 cuenta; de gancho + cierre, no (la escena 2 es el cierre)
ok(VD.revisar_voz_real([escena(1, "gancho", 5.0), escena(2, "cierre", 14.0)]) == ([], []), "voz real: el cierre no es la escena 2 de P5")
ok(VD.revisar_voz_real([escena(1, "foto", 9.0), escena(2, "foto", 9.0), escena(3, "cierre", 9.0)]) == ([], []),
   "voz real: una escena 1 que no es gancho (piezas sueltas) no se mide")
# /sabias y /congreso no llevan promesa: P5 no se mide (el mismo filtro que ya usan sobre el gate del guion); el gancho sí
for mod in (SB, CG):
    ok(mod.de_video_que_no_aplica("P5 la escena 2 dura 13.30 s de voz real") and not mod.de_video_que_no_aplica("V9 gancho: la voz real dura 6.72 s"),
       "voz real: el filtro de %s debe quitar P5 y dejar el gancho" % mod.__name__)
VD.NO_APLICA_REAL.append(SB.de_video_que_no_aplica)
f, av = real(6.72, 13.3, "tarjeta")
ok(len(f) == 1 and f[0].startswith("V9 gancho"), "voz real: con el filtro de /sabias queda solo la falla del gancho: %s" % f)
VD.NO_APLICA_REAL.pop()
r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'scripts'); import sabias as S, video as V; S.aplicar_extension(); "
                    "print(len(V.NO_APLICA_REAL), V.GANCHO_ORACION_S, max(V.GANCHO_REAL_S[1], V.GANCHO_ORACION_S))"], cwd=RAIZ, capture_output=True, text=True)
ok(r.stdout.split() == ["1", "6.5", "6.5"], "voz real: /sabias debe enchufar su filtro y conservar su tope de 6.5 s: %s %s" % (r.stdout, r.stderr[-300:]))

# ---------- 2. una sola elegir_musica, sobre todos los registros ----------
for mod in (HI, EX, SB, CG):
    ok(not hasattr(mod, "elegir_musica"), "música: %s todavía tiene su copia de elegir_musica" % mod.__name__)
MEM = os.path.join(TMP, "memoria")
os.makedirs(MEM)
MEMORIA_REAL, VD.MEMORIA_DIR = VD.MEMORIA_DIR, MEM
cat = leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
paleta = next(p["paleta"] for p in cat if p.get("paleta") and sum(1 for q in cat if q.get("paleta") == p["paleta"]) >= 2)
a, b = sorted(p["id"] for p in cat if p.get("paleta") == paleta)[:2]
ok(VD.elegir_musica(paleta)["id"] == a, "música: sin registros, la primera pista de la paleta")
escribir(os.path.join(MEM, "sabias.json"), {"sabias": [{"id": "sabias-x", "slug": "x", "fecha": "2026-11-01", "musica": a, "frases": {}}]})
ok(VD.elegir_musica(paleta)["id"] == b, "música: un «¿Sabías que…?» (otro flujo) que usó %s debe mandar a /video a %s (llegó %s)" % (a, b, VD.elegir_musica(paleta)["id"]))
ok(VD.elegir_musica(paleta, a)["id"] == a, "música: la pista forzada manda")
escribir(os.path.join(MEM, "series.json"), {"series": [{"id": "2026-11-05-s", "slug": "s", "fecha": "2026-11-05", "motor": "historia", "musica": None,
         "partes": [{"n": 1, "estado": "entregada", "ruta": "series/s/parte-1", "musica": b, "frases": {}},
                    {"n": 2, "estado": "lista", "ruta": None, "musica": a}]}]})
ok(VD.elegir_musica(paleta)["id"] == a, "música: la parte entregada de una serie cuenta con su pista (%s más reciente → toca %s)" % (b, a))
ok(VD.usos_musica() == {a: "2026-11-01", b: "2026-11-05"}, "música: usos %s" % VD.usos_musica())
ok(VD.usos_musica("x") == {b: "2026-11-05"}, "música: excluir_slug deja fuera la pieza que se está rehaciendo: %s" % VD.usos_musica("x"))
tema = next((t for p in cat for t in (p.get("temas") or []) if p["id"] in (a, b)), None)
if tema:
    del_tema = sorted(p["id"] for p in cat if tema in (p.get("temas") or []))
    ok(VD.elegir_musica_tema(tema)["id"] == next((x for x in del_tema if x not in (a, b)), a),
       "música por tema: la pista del tema usada hace más tiempo (llegó %s)" % VD.elegir_musica_tema(tema)["id"])
try:
    VD.elegir_musica("no-existe")
    ok(False, "música: una paleta sin pistas debe dar ValueError")
except ValueError:
    pass

# ---------- 3. la rotación mira todo el feed ----------
G = leer(os.path.join(RAIZ, "sesiones", "_fixture_video", "guion.json"))
forma = G["promesa"]["forma"]
otra = next(x for x in VD.PROMESA_FORMAS if x != forma)
for n in os.listdir(MEM):
    os.remove(os.path.join(MEM, n))
ok(VD.promesas_recientes("v") == [] and VD.ganchos_recientes("v") == {"familias": [], "visuales": []}
   and VD.cierres_recientes("v") == {"tipos": [], "formas": [], "mecanismos": []}, "rotación: sin registros no bloquea nada")
ok(not [x for x in VD.validar_promesa(G, {"slug": "v"}, []) if x.startswith("P3")], "P3: sin registros, la promesa del fixture pasa")
# solo un video viejo de /video: como antes de la ola 1, nada lo bloquea
escribir(os.path.join(MEM, "videos.json"), {"videos": [{"id": "2026-10-20-a", "slug": "a", "fecha": "2026-10-20", "musica": a,
         "frases": {"promesa": "x", "promesa_forma": otra, "familia": "tu", "visual": "llenado", "cierre_tipo": "remate",
                    "cierre_forma": "pendiente", "cierre_mecanismo": None}}]})
ok(not [x for x in VD.validar_promesa(G, {"slug": "v"}, []) if x.startswith("P3")], "P3: otra forma no bloquea")
# … y una parte de serie reciente con la misma forma: P3 la bloquea en /video
serie = {"id": "2026-11-12-s", "slug": "s", "fecha": "2026-11-12", "motor": "historia", "musica": b, "partes": [
    {"n": 1, "estado": "entregada", "ruta": "series/s/parte-1", "musica": b,
     "frases": {"promesa": "y", "promesa_forma": forma, "familia": "misterio", "visual": "foto", "cierre_tipo": "pregunta", "cierre_forma": "puente"}},
    {"n": 2, "estado": "lista", "frases": {"promesa_forma": "reloj", "familia": "lugar"}}]}
escribir(os.path.join(MEM, "series.json"), {"series": [serie]})
ok(VD.promesas_recientes("v") == [otra, forma], "P3: las formas del feed deben traer la de la parte de serie: %s" % VD.promesas_recientes("v"))
p3 = [x for x in VD.validar_promesa(G, {"slug": "v"}, []) if x.startswith("P3")]
ok(len(p3) == 1 and "«%s»" % forma in p3[0], "P3: una parte de serie reciente con la forma «%s» debe bloquearla en /video: %s" % (forma, p3))
ok(not [x for x in VD.validar_promesa(G, {"slug": "v", "fixture": True}, []) if x.startswith("P3")], "P3: una maqueta no rota contra lo producido")
ok(not [x for x in VD.validar_promesa(G, {"slug": "v", "promesas_recientes": []}, []) if x.startswith("P3")], "P3: la rotación guardada en video.json manda")
# R9: la familia de la parte de serie y la del video viejo bloquean (últimas 2 piezas); el visual de una historia o de una
# parte de serie (siempre la foto) no bloquea el de la pieza siguiente; una parte sin entregar no cuenta
gr = VD.ganchos_recientes("v")
ok(gr == {"familias": ["tu", "misterio"], "visuales": []}, "R9: ganchos recientes del feed: %s" % gr)
ok(VD.ganchos_recientes("v", 1, 0)["familias"] == ["misterio"], "R9: la ventana de cada flujo (1 familia, sin visual)")
cr = VD.cierres_recientes("v")
ok(cr == {"tipos": ["pregunta"], "formas": ["pendiente", "puente"], "mecanismos": []}, "F7: cierres recientes del feed: %s" % cr)
# F7: tras una parte que cerró con pregunta·puente, la parte siguiente puede cerrar con pregunta·puente (es obligatorio);
# otro video no puede cerrar con una pregunta ni repetir «pendiente»
hilo, tarj = {"tema": "Hacinamiento en las cárceles", "tesis": "Las cárceles tienen 3.42 presos por espacio"}, [{"titular": "Pavón: 4,464 presos"}]
st_parte = {"cierres_recientes": cr, "serie": {"parte": 2, "de": 3}}
fp = VD.reglas_cierre({"tipo": "pregunta", "forma": "puente", "final": "¿Quién dejó crecer las cárceles?", "texto": "x"}, st_parte, hilo, tarj, [])
ok(not [x for x in fp if x.startswith("F7")], "F7: el puente de una parte de serie no rota: %s" % fp)
fv = VD.reglas_cierre({"tipo": "pregunta", "forma": "porque", "final": "¿Por qué siguen llenas las cárceles?", "texto": "x"}, {"cierres_recientes": cr}, hilo, tarj, [])
ok(any(x.startswith("F7 el video anterior cerró con una pregunta") for x in fv), "F7: una pregunta no sigue a otra, aunque la anterior sea de otro flujo: %s" % fv)
fv = VD.reglas_cierre({"tipo": "remate", "forma": "pendiente", "final": "Las cárceles siguen llenas de presos.", "texto": "x"}, {"cierres_recientes": cr}, hilo, tarj, [])
ok(any(x.startswith("F7 la forma «pendiente»") for x in fv), "F7: la forma del video viejo sigue bloqueada: %s" % fv)
# registros que no guardan el dato se saltan sin fallar: un video 3D (sin `frases`), una pieza sin nada, un registro vacío
escribir(os.path.join(MEM, "videos3d.json"), {"videos3d": [{"id": "video3d-t", "slug": "t", "fecha": "2026-11-14", "musica": a,
         "gancho": {"id": "g1", "familia": "ruptura"}, "cierre": {"tipo": "remate", "forma": "consecuencia", "consecuencia": {"mecanismo": "espera"}}}]})
escribir(os.path.join(MEM, "congreso.json"), {"congreso": [{"id": "congreso-c", "slug": "c", "fecha": "2026-11-13"}]})
escribir(os.path.join(MEM, "explicaciones.json"), {"explicaciones": []})
ok([x["slug"] for x in VD.piezas_feed()] == ["a", "s-parte-1", "c", "t"], "feed: orden por fecha y solo las partes entregadas: %s" % [x["slug"] for x in VD.piezas_feed()])
ok(VD.ganchos_recientes("v")["familias"] == ["ruptura"], "R9: un registro sin familia ocupa su lugar y no bloquea: %s" % VD.ganchos_recientes("v"))
ok(VD.cierres_recientes("v") == {"tipos": ["remate"], "formas": ["consecuencia"], "mecanismos": ["espera"]}, "F7 con un video 3D: %s" % VD.cierres_recientes("v"))
ok(VD.promesas_recientes("v") == [otra, forma], "P3: las piezas sin promesa no ocupan la ventana: %s" % VD.promesas_recientes("v"))
ok([x["slug"] for x in VD.piezas_feed("t")] == ["a", "s-parte-1", "c"] and [x["slug"] for x in VD.piezas_feed(excluir_serie="s")] == ["a", "c", "t"],
   "feed: excluir la pieza propia y una serie entera")
# cada flujo lee el mismo feed: /historia (familias, sin visual), /explica (familia y visual), /congreso, /sabias (F7)
ok(HI.recientes("v")[0] == {"familias": ["ruptura"], "visuales": []} and HI.recientes("v")[1]["mecanismos"] == ["espera"], "historia.recientes: %s" % (HI.recientes("v"),))
ok(EX.recientes("v")[1]["formas"] == ["consecuencia"], "explica.recientes: %s" % (EX.recientes("v"),))
ok(CG.recientes("v")[1][1]["tipos"] == ["remate"], "congreso.recientes: %s" % (CG.recientes("v"),))
# una parte de serie se arma con la rotación de ESE momento: el feed sin su serie + sus partes anteriores (del TRABAJO)
S = {"slug": "s", "fecha": "2026-11-12", "motor": "historia", "partes": [{"n": 1, "trabajo": os.path.relpath(os.path.join(TMP, "p1"), RAIZ)},
                                                                         {"n": 2, "trabajo": os.path.relpath(os.path.join(TMP, "p2"), RAIZ)}, {"n": 3}]}
escribir(os.path.join(TMP, "p1", "guion.json"), {"escenas": [{"tipo": "gancho", "familia": "misterio", "visual": "foto"}],
                                               "promesa": {"texto": "a", "forma": "apuesta"}, "cierre": {"tipo": "pregunta", "forma": "puente"}})
escribir(os.path.join(TMP, "p2", "guion.json"), {"escenas": [{"tipo": "gancho", "familia": "contraste", "visual": "foto"}], "gancho": {"id": "g2", "elegido_por": "usuario"},
                                               "promesa": {"texto": "b", "forma": "apuesta"}, "cierre": {"tipo": "pregunta", "forma": "puente"}})
rot = SE.rotacion_parte(S, 3, "s-parte-3")
ok(rot["promesas_recientes"] == ["apuesta", "apuesta"], "serie: la parte 3 debe ver la forma de promesa de las partes 1 y 2: %s" % rot)
ok(rot["ganchos_recientes"]["familias"] == ["misterio", "contraste"] and rot["cierres_recientes"]["tipos"] == ["pregunta"], "serie: rotación de la parte 3: %s" % rot)
ok(SE.rotacion_parte(S, 1, "s-parte-1")["promesas_recientes"] == [otra], "serie: la parte 1 ve el feed sin su propia serie: %s" % SE.rotacion_parte(S, 1, "s-parte-1"))
VD.MEMORIA_DIR = MEMORIA_REAL
ok(all(x in VD.PROMESA_FORMAS + ("anuncio",) for x in VD.promesas_recientes("__ninguno__", 50)), "P3: formas desconocidas en los registros reales")
ok(isinstance(VD.piezas_feed(), list) and all(set(x["frases"]) == set(VD.CAMPOS_ROTACION) for x in VD.piezas_feed()), "feed: los registros reales no se leen")

# ---------- 4 y 5. la maqueta de /historia: quién eligió, y la escena toma ----------
T = os.path.join(TMP, "historia")
rc, out = correr("historia.py", "preparar", "La Espiga (maqueta)", "--slug", "la-espiga-maqueta", "--trabajo", T, "--fixture")
rc = rc or correr("historia.py", "consolidar", T)[0]
ok(rc == 0, "la maqueta de /historia no se arma: %s" % out[-400:])
if rc == 0:
    ok(not os.path.isdir(os.path.join(T, "tomas")) and not os.path.isdir(os.path.join(T, "videos")), "tomas: la maqueta ya no arma videos ni tomas")
    ok("tomas" not in leer(os.path.join(T, "historia.json")), "tomas: historia.json ya no lleva «tomas»")
    # con `auto` (ganchos --usar a secas): queda el ganador del crítico
    rc, out = correr("historia.py", "ganchos", T, "--usar")
    g = leer(os.path.join(T, "guion.json"))
    rec = leer(os.path.join(T, "seleccion.json"))["ganador"]
    ok(rc == 0 and g.get("gancho") == {"id": rec, "elegido_por": "critico", "recomendado": rec}, "elección: --usar a secas = critico: %s %s" % (g.get("gancho"), out[-300:]))
    ok(correr("historia.py", "guion", T, "--check")[0] == 0, "elección: el guion con guion.gancho debe seguir pasando el gate")
    # 5. una escena `toma` sigue fallando con TM0 (y el gate no escribe locucion.json)
    T2 = os.path.join(TMP, "historia_toma")
    shutil.copytree(T, T2)
    g2 = leer(os.path.join(T2, "guion.json"))
    g2["escenas"][3].update(tipo="toma", toma="ori-v01-t02")
    escribir(os.path.join(T2, "guion.json"), g2)
    if os.path.exists(os.path.join(T2, "locucion.json")):
        os.remove(os.path.join(T2, "locucion.json"))
    rc, out = correr("historia.py", "guion", T2, "--check")
    ok(rc != 0 and "FALLA TM0 escena 4: las tomas de video ya no van" in out and not os.path.exists(os.path.join(T2, "locucion.json")),
       "TM0: una escena toma debe fallar con TM0: rc=%s %s" % (rc, out[-400:]))
    # el usuario elige otro: --elegir y luego --usar
    T3 = os.path.join(TMP, "historia_elige")
    shutil.copytree(T, T3)
    otro = next(c["id"] for c in leer(os.path.join(T3, "ganchos.json"))["candidatos"] if c["id"] != rec)
    rc = correr("historia.py", "ganchos", T3, "--elegir", otro)[0] or correr("historia.py", "ganchos", T3, "--usar")[0]
    g3 = leer(os.path.join(T3, "guion.json"))
    ok(rc == 0 and g3.get("gancho") == {"id": otro, "elegido_por": "usuario", "recomendado": rec}, "elección: --elegir + --usar = usuario, con el recomendado del crítico: %s" % g3.get("gancho"))
    ok(leer(os.path.join(T3, "ganchos.json")).get("elegido_por") == "usuario", "elección: ganchos.json guarda quién eligió")
    correr("historia.py", "ganchos", T3, "--usar", rec, "--por", "propio")
    ok(leer(os.path.join(T3, "guion.json"))["gancho"]["elegido_por"] == "propio", "elección: --por fija quién eligió")
    # el cierre: el usuario se queda con una opción (o corre con auto: --por critico)
    c1 = dict({k: g["cierre"][k] for k in ("texto", "final", "tipo", "forma", "consecuencia") if k in g["cierre"]}, id="c1")
    escribir(os.path.join(T, "cierres.json"), {"candidatos": [c1]})
    rc, out = correr("historia.py", "cierres", T, "--usar", "c1")
    g = leer(os.path.join(T, "guion.json"))
    ok(rc == 0 and {k: g["cierre"].get(k) for k in VD.CAMPOS_ELECCION} == {"id": "c1", "elegido_por": "usuario", "recomendado": "c1"},
       "elección: cierres --usar = usuario: rc=%s %s %s" % (rc, g["cierre"], out[-300:]))
    ok(VD.eleccion_cierre(T) == {"id": "c1", "elegido_por": "usuario", "recomendado": "c1"} and VD.eleccion_gancho(T)["elegido_por"] == "critico", "elección: lo que lee entregar")
    rc, out = correr("historia.py", "cierres", T, "--usar", "c1", "--por", "critico")
    ok(rc == 0 and leer(os.path.join(T, "guion.json"))["cierre"]["elegido_por"] == "critico", "elección: cierres --usar --por critico (auto): %s" % out[-300:])
    # si un retoque reescribe el guion sin esos campos, la elección sale de ganchos.json y cierres.json
    g = leer(os.path.join(T, "guion.json"))
    g.pop("gancho")
    for k in VD.CAMPOS_ELECCION:
        g["cierre"].pop(k, None)
    ok(VD.eleccion_gancho(T, g) == {"id": rec, "elegido_por": "critico", "recomendado": rec} and VD.eleccion_cierre(T, g).get("elegido_por") == "critico",
       "elección: respaldo en ganchos.json y cierres.json: %s %s" % (VD.eleccion_gancho(T, g), VD.eleccion_cierre(T, g)))
    g["cierre"]["final"] = "Otra frase final que nadie eligió."
    ok(VD.eleccion_cierre(T, g) == {}, "elección: un cierre reescrito ya no es el que se eligió")
    # el guion de ENTREGA y el registro (--dry-run: no se escribe nada)
    ent = VD.con_eleccion({"id": "2026-01-01-la-espiga-maqueta", "tipo": "historia", "slug": "la-espiga-maqueta", "tema": "x", "fecha": "2026-01-01",
                           "paleta": "maiz", "musica": a, "duracion_s": 150.0, "escenas": [], "promesa": g3.get("promesa"),
                           "gancho": {"familia": "resultado", "visual": "foto"}, "cierre": dict(c1)}, T3)
    ok(ent["gancho"] == {"familia": "resultado", "visual": "foto", "id": rec, "elegido_por": "propio", "recomendado": rec}, "elección: guion de entrega: %s" % ent["gancho"])
    ent["gancho"].update(id=otro, elegido_por="usuario")
    ent["cierre"].update(id="c1", elegido_por="usuario", recomendado="c1")
    D = os.path.join(TMP, "historias", "2026-01-01-la-espiga-maqueta")
    escribir(os.path.join(D, "guion.json"), ent)
    antes = open(os.path.join(RAIZ, "memoria", "historias.json"), encoding="utf-8").read()
    rc, out = correr("memoria.py", "--historia", D, "--dry-run")
    ok(rc == 0 and "elección: gancho %s por usuario (recomendado: %s) · cierre c1 por usuario (recomendado: c1)" % (otro, rec) in out and "[dry-run]" in out,
       "elección: memoria.py --historia --dry-run debe decir quién eligió: rc=%s %s" % (rc, out[-400:]))
    ok(open(os.path.join(RAIZ, "memoria", "historias.json"), encoding="utf-8").read() == antes, "elección: --dry-run escribió en memoria/historias.json")
fr = ME.frases_video({"gancho": {"familia": "tu", "id": "g2", "elegido_por": "usuario", "recomendado": "g1"}, "escenas": [],
                      "cierre": {"tipo": "remate", "forma": "consecuencia", "final": "x", "id": "cu", "elegido_por": "propio"}})
ok((fr.get("gancho_elegido_por"), fr.get("gancho_recomendado"), fr.get("gancho_id"), fr.get("cierre_elegido_por"), fr.get("cierre_id")) ==
   ("usuario", "g1", "g2", "propio", "cu") and "cierre_recomendado" not in fr, "elección: frases del registro: %s" % fr)
viejo = ME.frases_video({"gancho": {"familia": "tu"}, "cierre": {"tipo": "remate", "forma": "consecuencia", "final": "x"}, "escenas": []})
ok(not [k for k in viejo if "elegido" in k or "recomendado" in k] and ME.linea_eleccion(viejo) == "elección: gancho sin registro · cierre sin registro",
   "elección: un guion viejo no gana claves nuevas: %s" % viejo)
# el registro de /serie guarda por parte entregada su música y sus frases (rotación del feed y elección)
ME_RAIZ, ME.RAIZ = ME.RAIZ, TMP
escribir(os.path.join(TMP, "series", "s", "parte-1", "guion.json"), {"musica": b, "gancho": {"familia": "misterio", "visual": "foto", "id": "g1", "elegido_por": "usuario", "recomendado": "g3"},
                                                              "promesa": {"texto": "t", "forma": "reloj"}, "cierre": {"tipo": "pregunta", "forma": "puente", "final": "¿Y?"}, "escenas": []})
escribir(os.path.join(TMP, "series", "s", "serie.json"), {"slug": "s", "fecha": "2026-11-12", "motor": "historia", "partes": [
    {"n": 1, "titulo": "Uno", "estado": "entregada", "ruta": "series/s/parte-1", "duracion_s": 90}, {"n": 2, "titulo": "Dos", "estado": "lista"}]})
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = ME.registrar_serie("series/s", dry_run=True)
ok(rc == 0 and "parte 1 · música %s · gancho misterio (eligió: usuario) · promesa reloj" % b in buf.getvalue() and "[dry-run]" in buf.getvalue(),
   "serie: el registro de la parte debe llevar música, promesa y elección: %s" % buf.getvalue())
p1, p2 = ME.parte_serie({"n": 1, "estado": "entregada", "ruta": "series/s/parte-1"}), ME.parte_serie({"n": 2, "estado": "lista"})
ok(p1["musica"] == b and p1["frases"]["promesa_forma"] == "reloj" and p1["frases"].get("gancho_recomendado") == "g3" and "frases" not in p2, "serie: parte_serie %s %s" % (p1, p2))
ME.RAIZ = ME_RAIZ

# ---------- 5. lo que se borró ya no está ----------
for nombre in ("cmd_video", "cmd_toma", "cmd_tomas_contacto", "bajar_video", "t_toma", "tomas_h", "transcribir", "videos_de_html",
               "transicion_con_direccion", "segundos_toma", "oyente_toma", "tomas_fixture"):
    ok(not hasattr(HI, nombre), "código muerto: historia.%s sigue ahí" % nombre)
for nombre in ("SEGUNDOS_EXTRA", "EXTRA_OYENTE", "segundos_extra", "CAMARA_QUIETA", "saltos_escena", "PLANO_S", "SALTOS_EXENTOS"):
    ok(not hasattr(VD, nombre), "código muerto: video.%s sigue ahí" % nombre)
ok(HI.revisar_tomas({"escenas": [{"tipo": "foto"}, {"tipo": "toma"}]}) == [
   "TM0 escena 2: las tomas de video ya no van en /historia ni /serie: una cita (la frase literal, leída por la voz) o una foto o documento con la misma voz"],
   "TM0: revisar_tomas")
for sub in ("video", "toma", "tomas-contacto"):
    ok(correr("historia.py", sub, "x")[0] == 2, "código muerto: historia.py %s sigue siendo un subcomando" % sub)
# cámara quieta: un plano y, a lo más, un corte a la cara de la persona que la voz nombra (lo que hacía la rama viva)
pl, fs = VD.planos_foto([{"x": .1, "y": .2, "w": .1, "h": .1}, {"x": .7, "y": .2, "w": .1, "h": .1}], 18.0, cortes=[3.4, 7.2, 10.9, 14.6], evitar=[7.0])
ok(len(pl) == 1 and pl[0]["z"] == "amplio" and len(fs) == 2, "cámara quieta: un solo plano: %s" % pl)
pl, fs = VD.planos_foto(None, 12.0, personas=[(5.0, 1), (8.0, 0)])
ok(len(pl) == 2 and pl[1].get("persona") and pl[1]["t"] == 5.0 and fs == VD.TERCIOS, "cámara quieta: un corte a la persona: %s" % pl)

# ---------- 6. podar_intermedios.py: modo lista (y el borrado, solo en el árbol fabricado) ----------
R = os.path.join(TMP, "raiz")


def archivo(ruta, n=2048, relleno=b"x"):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(relleno * n)


def trabajo(nombre, estado, video=b"v"):
    d = os.path.join(R, "sesiones", nombre)
    escribir(os.path.join(d, "video.json"), estado)
    for x in ("guion.json", "plano.json", "escenas.json", "locucion.json"):
        escribir(os.path.join(d, x), {})
    archivo(os.path.join(d, "salida", "video.mp4"), 4096, video)
    for x, n in (("audio/voz_1.mp3", 3000), ("fotos/a.jpg", 3000), ("segs/voz.wav", 50000), ("segs_4x5/video_solo.mp4", 40000),
                 ("clips/e1.mp4", 30000), ("clips_4x5/e1.mp4", 20000), ("clips_tablero/e3.mp4", 7000), ("clips_maqueta/m1.mp4", 9000),
                 ("revision/c_001.png", 6000), ("revision/c_4x5_001.png", 6000), ("revision/contacto.png", 5000), ("revision/zona.json", 10),
                 ("hf/9x16/render/video.mp4", 60000), ("hf/9x16/.hyperframes/cache.bin", 8000), ("hf/9x16/assets/a.jpg", 4000),
                 ("hf/9x16/mesas.json", 10), ("hf/9x16/index.html", 100), ("hf/piloto/assets/a.jpg", 4000), ("hf/piloto/index.html", 100),
                 ("variante_b/segs/voz.wav", 11000), ("variante_b/audio/voz_1.mp3", 3000)):
        archivo(os.path.join(d, x), n)
    return d


def entrega(ruta, video=b"v"):
    escribir(os.path.join(R, ruta, "guion.json"), {})
    archivo(os.path.join(R, ruta, "video.mp4"), 4096, video)


t_ok = trabajo("historia-lista", {"tipo": "historia", "slug": "lista"})
entrega("historias/2026-01-01-lista")
t_sin = trabajo("historia-sin-registro", {"tipo": "historia", "slug": "sin-registro"})
t_inc = trabajo("historia-incompleta", {"tipo": "historia", "slug": "incompleta"})
entrega("historias/2026-01-01-incompleta")
t_reg = trabajo("historia-regrabada", {"tipo": "historia", "slug": "regrabada"}, video=b"w")   # se volvió a grabar tras entregar
entrega("historias/2026-01-01-regrabada")
t_p1 = trabajo("serie-s/parte-1", {"tipo": "historia", "slug": "s-parte-1", "serie": {"slug": "s", "parte": 1}})
t_copia = trabajo("serie-s-v0/parte-1", {"tipo": "historia", "slug": "s-parte-1", "serie": {"slug": "s", "parte": 1}})   # una versión vieja
entrega("series/2026-01-02-s/parte-1")
escribir(os.path.join(R, "series", "2026-01-02-s", "serie.json"), {"slug": "s", "partes": [
    {"n": 1, "estado": "entregada", "ruta": "series/2026-01-02-s/parte-1", "trabajo": "sesiones/serie-s/parte-1"}]})
trabajo("serie-s", {"tipo": "historia", "slug": "s", "serie": {"slug": None, "parte": None}})   # la base de la serie
t_fix = trabajo("_fixture_x", {"tipo": "historia", "slug": "lista"})                               # una maqueta: ni se mira
escribir(os.path.join(R, "memoria", "historias.json"), {"historias": [
    {"slug": "lista", "ruta": "historias/2026-01-01-lista", "estado": "listo"},
    {"slug": "incompleta", "ruta": "historias/2026-01-01-incompleta", "estado": "incompleto"},
    {"slug": "regrabada", "ruta": "historias/2026-01-01-regrabada", "estado": "publicado"}]})
escribir(os.path.join(R, "memoria", "series.json"), {"series": [{"slug": "s", "carpeta": "series/2026-01-02-s"}]})


def arbol(d):
    return sorted(os.path.relpath(os.path.join(b, n), d) for b, _, ns in os.walk(d) for n in ns)


antes = {d: arbol(d) for d in (t_ok, t_sin, t_inc, t_reg, t_p1, t_copia, t_fix)}
rc, out = correr("podar_intermedios.py", "--raiz", R)
ok(rc == 0, "podar: modo lista rc=%s %s" % (rc, out[-400:]))
ok({d: arbol(d) for d in antes} == antes, "podar: el modo lista borró algo")
ok("sesiones/historia-lista  →  historias/2026-01-01-lista (memoria/historias.json)" in out and
   "sesiones/serie-s/parte-1  →  series/2026-01-02-s/parte-1 (memoria/series.json)" in out, "podar: debe listar la historia y la parte entregadas:\n%s" % out)
bloque = out.split("sesiones/historia-lista  →", 1)[-1].split("\nsesiones/", 1)[0].split("\nNo se tocan", 1)[0]
for x in ("segs/", "segs_4x5/", "clips/", "clips_4x5/", "clips_tablero/", "revision/c_001.png", "revision/c_4x5_001.png", "hf/9x16/render/",
          "hf/9x16/.hyperframes/", "hf/9x16/assets/", "variante_b/segs/"):
    ok(("    %s " % x) in bloque, "podar: falta «%s» en la lista:\n%s" % (x, bloque))
for x in ("audio", "fotos", "clips_maqueta", "contacto.png", "zona.json", "salida", "guion.json", "plano.json", "hf/piloto", "index.html", "mesas.json"):
    ok(x not in bloque, "podar: «%s» no se puede borrar y sale en la lista:\n%s" % (x, bloque))
for nombre, motivo in (("historia-sin-registro", "sin registro en memoria/historias.json"), ("historia-incompleta", "registrado como «incompleto»"),
                       ("historia-regrabada", "no es el video entregado"), ("serie-s-v0/parte-1", "no desde aquí"), ("serie-s —", "es la base de una serie")):
    ok(any(nombre in l and motivo in l for l in out.splitlines()), "podar: «%s» debe quedar sin tocar por «%s»:\n%s" % (nombre, motivo, out))
ok("_fixture_x" not in out, "podar: una carpeta que empieza con «_» no se mira")
ok("nada se borró: make podar-intermedios CONFIRMAR=1" in out and "2 trabajo(s) entregado(s)" in out, "podar: el pie debe decir el total y cómo borrar:\n%s" % out[-300:])
ok(correr("podar_intermedios.py", "--raiz", R, "--solo", "sesiones/historia-sin-registro")[1].count("→") == 0, "podar: --solo limita a un trabajo")
ok(correr("podar_intermedios.py", "--raiz", R, "--solo", "/tmp")[0] == 2, "podar: --solo fuera de sesiones/ es un error de uso")
ok(correr("podar_intermedios.py", "--raiz", os.path.join(TMP, "no-existe"))[0] == 2, "podar: una raíz sin sesiones/ es un error de uso")
ok(correr("podar_intermedios.py", "--help")[0] == 0, "podar: --help")
# el borrado, SOLO sobre el árbol fabricado: se van los intermedios de los dos trabajos entregados y nada más
rc, out = correr("podar_intermedios.py", "--raiz", R, "--borrar")
ok(rc == 0 and "liberados" in out, "podar: --borrar rc=%s %s" % (rc, out[-300:]))
queda = arbol(t_ok)
ok(queda == sorted(["video.json", "guion.json", "plano.json", "escenas.json", "locucion.json", "salida/video.mp4", "audio/voz_1.mp3", "fotos/a.jpg",
                    "clips_maqueta/m1.mp4", "revision/contacto.png", "revision/zona.json", "hf/9x16/mesas.json", "hf/9x16/index.html",
                    "hf/piloto/assets/a.jpg", "hf/piloto/index.html", "variante_b/audio/voz_1.mp3"]), "podar: tras borrar queda %s" % queda)
ok({d: arbol(d) for d in (t_sin, t_inc, t_reg, t_copia, t_fix)} == {d: antes[d] for d in (t_sin, t_inc, t_reg, t_copia, t_fix)},
   "podar: --borrar tocó un trabajo que no estaba entregado")
ok(correr("podar_intermedios.py", "--raiz", R)[1].count("→") == 0, "podar: la segunda pasada no encuentra nada")

shutil.rmtree(TMP, ignore_errors=True)
for x in F:
    print("FALLA", x)
print("ola 1 de video: %s" % ("ok" if not F else "%d falla(s)" % len(F)))
sys.exit(1 if F else 0)
