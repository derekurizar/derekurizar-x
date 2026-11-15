#!/usr/bin/env python3
"""Pruebas de la medición de series, largos y cortes nuevos (ola 1, punto 9; sin red ni Chrome): cada parte de serie y
cada largo de YouTube son piezas vinculables (dos partes del mismo día no se confunden), /video-3d se alinea con sus
tiempos (m194), `rendimiento --por duracion|promesa|plataforma` y las vistas por día de vida. Todo sobre una raíz
temporal: no lee ni escribe memoria/. Exit 0 ok · 1 falla."""
import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import metricas as MT  # noqa: E402

F = []
TMP = tempfile.mkdtemp(prefix="ola1_metricas_")
MT.RAIZ = TMP
MT.METRICAS = os.path.join(TMP, "memoria", "metricas.json")


def ok(cond, que):
    if not cond:
        F.append(que)


def poner(ruta, datos):
    MT.escribir(os.path.join(TMP, ruta), datos)


def callado(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        r = fn(*args)
    return r, buf.getvalue()


def guion(familia, promesa, cierre, durs):
    return {"gancho": {"familia": familia, "visual": "foto"}, "promesa": {"forma": promesa, "en": 2}, "cierre": {"forma": cierre},
            "escenas": [{"n": k, "tipo": "gancho" if k == 1 else "cierre" if k == len(durs) else "foto", "dur": d,
                         "voz": "La voz de la escena %d." % k, "pantalla": "Pantalla %d" % k} for k, d in enumerate(durs, 1)]}


# ---------- los registros de ejemplo: una serie de 3 partes (2 entregadas, casi igual de largas), otra de 2, un largo ----------
poner("memoria/series.json", {"series": [
    {"id": "2026-11-06-la-prueba", "slug": "la-prueba", "tema": "la prueba del banco", "motor": "historia", "fecha": "2026-11-06",
     "carpeta": "series/2026-11-06-la-prueba", "n_partes": 3, "estado": "en curso", "partes": [
         {"n": 1, "titulo": "El comienzo", "estado": "entregada", "ruta": "series/2026-11-06-la-prueba/parte-1", "duracion_s": 147.9},
         {"n": 2, "titulo": "La caída", "estado": "entregada", "ruta": "series/2026-11-06-la-prueba/parte-2", "duracion_s": 148.3},
         {"n": 3, "titulo": "El juicio", "estado": "guion"}]},
    {"id": "2026-11-07-otra-serie", "slug": "otra-serie", "tema": "otra serie del lago", "motor": "historia", "fecha": "2026-11-07",
     "carpeta": "series/2026-11-07-otra-serie", "n_partes": 2, "estado": "completa", "partes": [
         {"n": 1, "titulo": "El agua", "estado": "entregada", "ruta": "series/2026-11-07-otra-serie/parte-1", "duracion_s": 100.0},
         {"n": 2, "titulo": "El químico", "estado": "entregada", "ruta": "series/2026-11-07-otra-serie/parte-2", "duracion_s": 130.0}]}]})
poner("series/2026-11-06-la-prueba/serie.json", {"slug": "la-prueba", "partes": [{"n": 1, "trabajo": "sesiones/serie-la-prueba/parte-1"},
                                                                                {"n": 2, "trabajo": "sesiones/serie-la-prueba/parte-2"}]})
poner("series/2026-11-06-la-prueba/parte-1/guion.json", guion("personaje", "pregunta", "puente", [6, 12, 40, 50, 39.9]))
poner("series/2026-11-06-la-prueba/parte-2/guion.json", guion("contraste", "secreto", "puente", [6, 12, 40, 50, 40.3]))
poner("series/2026-11-07-otra-serie/parte-1/guion.json", guion("lugar", "reloj", "puente", [6, 44, 50]))
poner("series/2026-11-07-otra-serie/parte-2/guion.json", guion("misterio", "reloj", "legado", [6, 60, 64]))
# la parte 2 tiene su TRABAJO: sus escenas.json (tiempos medidos) mandan sobre el guion entregado
poner("sesiones/serie-la-prueba/parte-2/escenas.json", {"escenas": [{"n": 1, "tipo": "gancho", "dur": 5.0}, {"n": 2, "tipo": "foto", "dur": 143.3}]})
poner("memoria/youtube.json", {"videos": [
    {"id": "youtube-la-prueba", "slug": "la-prueba", "tema": "la prueba del banco", "carpeta": "series/2026-11-06-la-prueba/youtube",
     "fecha": "2026-11-09", "duracion_s": 745.3, "titulo": "La prueba del banco: la historia completa",
     "capitulos": [{"numero": 1, "titulo": "El comienzo", "parte": 1, "t": 0.0}, {"numero": 2, "titulo": "La caída", "parte": 2, "t": 141.2},
                   {"numero": 3, "titulo": "El juicio", "parte": 3, "t": 300.0}]}]})
poner("series/2026-11-06-la-prueba/youtube/guion.json", {"promesa": {"forma": "contradiccion"}})
poner("memoria/historias.json", {"historias": [
    {"id": "2026-11-08-el-volcan", "slug": "el-volcan", "tema": "El volcán que despertó", "fecha": "2026-11-08", "ruta": "historias/2026-11-08-el-volcan",
     "duracion_s": 150.0, "frases": {"familia": "misterio", "visual": "foto", "cierre_forma": "legado", "promesa_forma": "presagio"}}]})
poner("memoria/sabias.json", {"sabias": [
    {"id": "2026-11-09-motos", "slug": "motos", "tema": "motos nuevas", "fecha": "2026-11-09", "ruta": "datos/2026-11-09-motos/video",
     "duracion_s": 27.0, "frases": {"visual": "cifra", "cierre_forma": "consecuencia"}}]})
# /video-3d: guion (texto por escena) + maqueta (palabras con su segundo, cámara, eventos)
TEXTOS = ["Una falla se rompió.", "Empezó aquí, cerca del lago.", "La falla sigue ahí."]
palabras, t = [], 0.0
for txt in TEXTOS:
    for w in txt.split():
        palabras.append({"text": w, "start": round(t, 2), "end": round(t + 0.4, 2)})
        t += 0.5
    t += 1.0
V3 = "videos3d/2026-11-10-falla"
poner("memoria/videos3d.json", {"videos3d": [
    {"id": "video3d-falla", "slug": "falla", "tema": "La falla que se rompió", "fecha": "2026-11-10", "ruta": V3, "duracion_s": 9.0,
     "gancho": {"familia": "ruptura", "texto": "Una falla se rompió."}, "cierre": {"forma": "consecuencia"}}]})
poner(V3 + "/guion.json", {"promesa": {"forma": "presagio", "en": 2}, "escenas": [
    {"n": 1, "tipo": "gancho", "texto": TEXTOS[0], "titular": {"kicker": "1976", "texto": "La madrugada de la falla"}},
    {"n": 2, "tipo": "toma", "texto": TEXTOS[1], "cifras": [{"valor": "7.5", "rotulo": "de magnitud"}]},
    {"n": 3, "tipo": "cierre", "texto": TEXTOS[2], "final": "La falla sigue ahí."}]})
poner(V3 + "/maqueta.json", {"duracion_s": 9.0, "camara": [{"t": 0.0}, {"t": 2.0}, {"t": 3.2}, {"t": 6.4}],
                             "eventos": [{"t": 0.0, "tipo": "ruptura", "dur": 2.0}, {"t": 3.5, "tipo": "resaltar", "dur": 1.0}],
                             "capa": {"palabras": palabras}})

# ---------- las piezas ----------
ps = {(p["flujo"], p["id"]): p for p in MT.piezas()}
ok(set(ps) == {("serie", "la-prueba-parte-1"), ("serie", "la-prueba-parte-2"), ("serie", "otra-serie-parte-1"), ("serie", "otra-serie-parte-2"),
               ("youtube", "youtube-la-prueba"), ("historia", "2026-11-08-el-volcan"), ("sabias", "2026-11-09-motos"), ("video3d", "video3d-falla")},
   "piezas: cada parte ENTREGADA y cada largo son una pieza (la parte 3, sin entregar, no): %s" % sorted(ps))
p1 = ps[("serie", "la-prueba-parte-1")]
ok(p1["parte"] == 1 and p1["de"] == 3 and p1["fecha"] == "2026-11-06" and p1["duracion_s"] == 147.9 and p1["ruta"].endswith("parte-1"),
   "piezas: la parte no trae su número, su fecha, su duración o su ruta: %s" % {k: p1.get(k) for k in ("parte", "de", "fecha", "duracion_s", "ruta")})
ok(p1["frases"].get("familia") == "personaje" and p1["frases"].get("promesa_forma") == "pregunta" and p1["frases"].get("cierre_forma") == "puente",
   "piezas: las categorías de la parte salen de su guion entregado: %s" % p1["frases"])
ok(ps[("video3d", "video3d-falla")]["frases"].get("familia") == "ruptura", "piezas: /video-3d sin la familia de su gancho")
ok(MT.pieza_por("la-prueba-parte-2")["flujo"] == "serie" and MT.pieza_por("youtube:youtube-la-prueba")["duracion_s"] == 745.3
   and MT.pieza_por("serie:otra-serie-parte-1"), "pieza_por no encuentra una parte o un largo")

# el número de parte de un título
for titulo, de, n in (("La Línea · Parte 3: quién era quién", None, 3), ("la prueba parte dos", None, 2), ("La cuarta parte del caso", None, 4),
                      ("Serie · Parte 2 de 5", None, 2), ("La prueba 2/3 la caída", 3, 2), ("La prueba 2/3 la caída", None, None),
                      ("1 de 3 niños no come", 3, 1), ("1 de 3 niños no come", None, None), ("6 de cada 10 muertos", 3, None),
                      ("El volcán que despertó", None, None), ("Pt. 5 del terremoto", None, 5), ("3/11/2026 en Guatemala", 3, None)):
    ok(MT.parte_del_titulo(titulo, de) == n, "parte_del_titulo(%r, de=%r) = %r (se esperaba %r)" % (titulo, de, MT.parte_del_titulo(titulo, de), n))

# ---------- importar y vincular ----------
CURVA = [1.0, 0.8, 0.7, 0.6, 0.55, 0.5, 0.48, 0.45, 0.42, 0.4]


def pub(post_id, titulo, fecha_pub, dur, views, **kw):
    return dict({"post_id": post_id, "titulo": titulo, "fecha_pub": fecha_pub, "duracion_s": dur, "views": views}, **kw)


poner("capturas/tiktok.json", {"plataforma": "tiktok", "fecha": "2026-11-14", "publicaciones": [
    # dos partes de la misma serie, el mismo día y casi igual de largas: solo «Parte N» las distingue
    pub("t1", "La prueba del banco · Parte 1: El comienzo #guatemala", "2026-11-10T09:00", 148, 1000, avg_s=40, curva=CURVA, shares=10, follows=3),
    pub("t2", "La prueba del banco · Parte 2: La caída #guatemala", "2026-11-10T19:30", 148, 600, avg_s=30, curva=CURVA, shares=2),
    # dos publicaciones de 130 s sin «Parte N»: las dos casarían con la parte 2 de la otra serie
    pub("t3", "Otra serie del lago", "2026-11-11T09:00", 130, 300, curva=CURVA),
    pub("t4", "Otra serie del lago, de nuevo", "2026-11-12T09:00", 131, 200, curva=CURVA),
    pub("t5", "El volcán que despertó", "2026-11-08T09:00", 150, 4000, avg_s=60, curva=CURVA),
    pub("t6", "La falla que se rompió en Guatemala", "2026-11-14T08:00", 9, 500, avg_s=5, curva=CURVA),
    pub("t7", "Motos nuevas en Guatemala", "2026-11-13T19:30", 27, 90, avg_s=9, curva=CURVA)]})
poner("capturas/instagram.json", {"plataforma": "instagram", "fecha": "2026-11-14", "publicaciones": [
    # título a mano sin número: empata entre la parte 1 y la 2 (duran casi lo mismo) → pendiente, nunca una al azar
    pub("i1", "La prueba del banco que nadie esperaba", "2026-11-10T09:05", 148, 2000),
    pub("i2", "La prueba 2/3 del banco", "2026-11-10T19:35", 148, 900)]})
poner("capturas/youtube.json", {"plataforma": "youtube", "fecha": "2026-11-14", "publicaciones": [
    pub("y1", "La prueba del banco: la historia completa", "2026-11-12T12:00", 745, 5000, avg_s=200, viewed_pct=0.6),
    pub("y2", "La prueba del banco, parte dos #Shorts", "2026-11-11T12:00", 148.3, 80, viewed_pct=0.5),
    # un corto sin número de parte nunca es el largo, aunque se llame igual
    pub("y3", "La prueba del banco: la historia completa", "2026-11-12T13:00", 59, 70)]})
a = argparse.Namespace(capturas=[os.path.join(TMP, "capturas", x + ".json") for x in ("tiktok", "instagram", "youtube")], dry_run=False)
rc, _ = callado(MT.cmd_importar, a)
ok(rc == 0 and len(MT.cargar()["publicaciones"]) == 12, "importar: no entraron las 12 publicaciones")
rc, salida = callado(MT.cmd_vincular, argparse.Namespace(fijar=None, ajena=None, dry_run=False))
M = MT.cargar()
V = {x["id"]: (x["vinculo"], (x.get("pieza") or {}).get("flujo"), (x.get("pieza") or {}).get("id")) for x in M["publicaciones"]}
for pid, esperado in (("tiktok-t1", ("auto", "serie", "la-prueba-parte-1")), ("tiktok-t2", ("auto", "serie", "la-prueba-parte-2")),
                      ("tiktok-t5", ("auto", "historia", "2026-11-08-el-volcan")), ("tiktok-t6", ("auto", "video3d", "video3d-falla")),
                      ("tiktok-t7", ("auto", "sabias", "2026-11-09-motos")),
                      ("instagram-i1", ("pendiente", None, None)), ("instagram-i2", ("auto", "serie", "la-prueba-parte-2")),
                      ("youtube-y1", ("auto", "youtube", "youtube-la-prueba")), ("youtube-y2", ("auto", "serie", "la-prueba-parte-2")),
                      ("tiktok-t3", ("pendiente", None, None)), ("tiktok-t4", ("pendiente", None, None))):
    ok(V[pid] == esperado, "vincular %s: %s (se esperaba %s)" % (pid, V[pid], esperado))
ok(V["youtube-y3"][1] != "youtube", "vincular: un corto de 59 s quedó ligado al largo de 745 s: %s" % (V["youtube-y3"],))
i1 = next(x for x in M["publicaciones"] if x["id"] == "instagram-i1")
ok(any("la-prueba-parte-1" in c for c in i1.get("candidatos") or []) and any("la-prueba-parte-2" in c for c in i1.get("candidatos") or []),
   "vincular: la pendiente sin «Parte N» no lista las dos partes como candidatas: %s" % i1.get("candidatos"))
t3 = next(x for x in M["publicaciones"] if x["id"] == "tiktok-t3")
ok("otra-serie-parte-2" in " ".join(t3.get("candidatos") or []), "vincular: dos publicaciones sin número para la misma parte deben quedar pendientes con esa parte de candidata")
ok(MT.revisar(M) == [], "M17 rechaza vínculos a partes de serie o a un largo: %s" % MT.revisar(M))
# a mano también: una pendiente se fija a su parte
rc, _ = callado(MT.cmd_vincular, argparse.Namespace(fijar=["instagram-i1", "serie:la-prueba-parte-1"], ajena=None, dry_run=False))
M = MT.cargar()
ok(rc == 0 and next(x for x in M["publicaciones"] if x["id"] == "instagram-i1")["pieza"]["id"] == "la-prueba-parte-1", "vincular --fijar a una parte de serie")
# el puntaje: otra parte queda descartada; una pieza suelta pierde ante «Parte N»
ok(MT.puntaje({"titulo": "La prueba del banco · Parte 2", "fecha_pub": "2026-11-10", "duracion_s": 148}, p1) == -1, "puntaje: «Parte 2» no descarta la parte 1")
sin_n = {"titulo": "El volcán que despertó", "fecha_pub": "2026-11-08", "duracion_s": 150}
ok(MT.puntaje(dict(sin_n, titulo="El volcán que despertó · Parte 2"), ps[("historia", "2026-11-08-el-volcan")])
   == MT.puntaje(sin_n, ps[("historia", "2026-11-08-el-volcan")]) - 2.0, "puntaje: «Parte N» no resta a una pieza que no es de serie")
ok(MT.puntaje({"titulo": "La prueba del banco parte 1", "fecha_pub": "2026-12-15", "duracion_s": 148}, p1) > 0
   and MT.puntaje({"titulo": "La prueba del banco parte 1", "fecha_pub": "2027-01-15", "duracion_s": 148}, p1) == -1,
   "puntaje: la ventana de una parte de serie es de %d días" % MT.VENTANA_SERIE[1])

# ---------- vistas por día de vida ----------
porid = {x["id"]: x for x in M["publicaciones"]}
ok(MT.dias_de_vida(porid["tiktok-t1"]) == 4 and MT.vistas_dia(porid["tiktok-t1"]) == 250.0, "vistas/día: 1,000 vistas en 4 días son 250")
ok(MT.dias_de_vida(porid["tiktok-t6"]) == 1 and MT.vistas_dia(porid["tiktok-t6"]) == 500.0, "vistas/día: publicada el día de la captura, mínimo 1 día")
ok(MT.vistas_dia({"snapshots": [{"fecha": "2026-11-14", "views": 10}]}) is None and MT.vistas_dia({}) is None, "vistas/día: sin fecha de publicación no hay dato")

# ---------- rendimiento: duracion, promesa, plataforma, parte ----------
for d, tramo in ((20, "< 35 s"), (34.9, "< 35 s"), (35, "35–70 s"), (69.9, "35–70 s"), (70, "70–120 s"), (120, "70–120 s"), (120.1, "> 120 s"),
                 (745, "> 120 s"), (None, None), (0, None)):
    ok(MT.tramo_duracion(d) == tramo, "tramo_duracion(%r) = %r (se esperaba %r)" % (d, MT.tramo_duracion(d), tramo))
R = MT.rendimiento("duracion", M)
ok(set(R) == {"< 35 s", "> 120 s"} and R["< 35 s"]["n"] == 2 and R["> 120 s"]["n"] == 4, "rendimiento --por duracion: %s" % {k: v["n"] for k, v in R.items()})
ok(R["< 35 s"]["views_dia"] == 295.0 and R["< 35 s"]["views"] == 295.0 and R["> 120 s"]["views_dia"] == 250.0 and R["> 120 s"]["views"] == 1000.0,
   "rendimiento --por duracion: vistas y vistas/día medianas: %s" % {k: (v["views"], v["views_dia"]) for k, v in R.items()})
R = MT.rendimiento("promesa", M)
ok(set(R) == {"pregunta", "secreto", "presagio", "contradiccion"} and R["presagio"]["n"] == 2,
   "rendimiento --por promesa (la forma del registro o del guion entregado): %s" % {k: v["n"] for k, v in R.items()})
R = MT.rendimiento("flujo", M)
ok(R["serie"]["n"] == 2 and R["youtube"]["n"] == 1 and R["video3d"]["n"] == 1, "rendimiento --por flujo no cuenta las partes ni el largo")
R = MT.rendimiento_plataforma(M)
ok(set(R) == {"tiktok", "instagram", "youtube"} and R["tiktok"]["n"] == 5 and R["youtube"]["n"] == 2 and R["instagram"]["n"] == 2,
   "rendimiento --por plataforma: %s" % {k: v["n"] for k, v in R.items()})
ok(R["tiktok"]["views"] == 600.0 and R["tiktok"]["views_dia"] == 250.0 and R["tiktok"]["hold3"] == 0.6 and R["youtube"]["hold3"] is None,
   "rendimiento --por plataforma: medianas: %s" % R["tiktok"])
for por, pistas in (("duracion", ("vistas/día", "edad", "< 35 s", "> 120 s")), ("plataforma", ("vistas/día", "avg/dur", "tiktok")),
                    ("parte", ("la-prueba", "P1 1000 [250/día]", "→ P2 600 [150/día] (60%)", "por día")), ("promesa", ("pregunta", "vistas/día"))):
    rc, salida = callado(MT.cmd_rendimiento, argparse.Namespace(por=por, md=False))
    ok(rc == 0 and all(x in salida for x in pistas), "rendimiento --por %s no imprime %s:\n%s" % (por, pistas, salida))
rc, salida = callado(MT.cmd_rendimiento, argparse.Namespace(por="duracion", md=False))
ok(salida.index("< 35 s") < salida.index("> 120 s") and salida.splitlines()[0].startswith("Columnas"), "rendimiento --por duracion: los tramos van en orden y con su leyenda")
lin = MT.lineas_rendimiento(("flujo",))
ok("por día de vida" in lin[0] and "/día)" in lin[0], "el «Rendimiento real» de los digestos no trae las vistas por día: %s" % lin[0][:200])

# ---------- alinear: /video-3d (m194), una parte de serie y un largo ----------
p3 = MT.pieza_por("video3d:video3d-falla")
esc, fuente, _ = MT.escenas_de(p3)
ok([(e["n"], e["tipo"], e["t0"], e["t1"]) for e in esc] == [(1, "gancho", 0.0, 3.0), (2, "toma", 3.0, 6.5), (3, "cierre", 6.5, 9.0)]
   and "capa.palabras" in fuente, "alinear 3D por las palabras de la maqueta: %s · %s" % ([(e["t0"], e["t1"]) for e in esc], fuente))
ok(esc[0]["pantalla"] == "La madrugada de la falla" and esc[1]["pantalla"] == "7.5 de magnitud" and esc[0]["en_3d"] == "ruptura · 2 claves de cámara"
   and esc[1]["en_3d"] == "resaltar · 2 claves de cámara" and esc[2]["en_3d"] == "0 claves de cámara" and esc[2]["voz"] == TEXTOS[2], "alinear 3D: pantalla, eventos y cámara por escena: %s" % esc)
poner(V3 + "/tiempos.json", {"real": True, "total_s": 9.0, "escenas": [{"n": 1, "off": 0.0, "dur": 2.8}, {"n": 2, "off": 2.8, "dur": 3.5}, {"n": 3, "off": 6.3, "dur": 2.7}]})
esc, fuente, _ = MT.escenas_de(p3)
ok([(e["t0"], e["t1"]) for e in esc] == [(0.0, 2.8), (2.8, 6.3), (6.3, 9.0)] and fuente.endswith("tiempos.json"), "alinear 3D: tiempos.json de la entrega manda: %s" % fuente)
poner(V3 + "/tiempos.json", {"real": False, "total_s": 9.0, "escenas": [{"n": 1, "off": 0.0, "dur": 1.0}, {"n": 2, "off": 1.0, "dur": 1.0}, {"n": 3, "off": 2.0, "dur": 7.0}]})
ok("capa.palabras" in MT.escenas_de(p3)[1], "alinear 3D: unos tiempos estimados no cuentan")
os.remove(os.path.join(TMP, V3, "tiempos.json"))
poner("sesiones/video3d-falla/tiempos.json", {"real": True, "total_s": 12.0, "escenas": [{"n": 1, "off": 0.0, "dur": 4.0}, {"n": 2, "off": 4.0, "dur": 4.0}, {"n": 3, "off": 8.0, "dur": 4.0}]})
ok("capa.palabras" in MT.escenas_de(p3)[1], "alinear 3D: el tiempos.json de un TRABAJO que ya no dura lo que la entrega no cuenta")
maq = json.load(open(os.path.join(TMP, V3, "maqueta.json"), encoding="utf-8"))
poner(V3 + "/maqueta.json", dict(maq, capa={"palabras": maq["capa"]["palabras"][:-1]}))
esc, fuente, _ = MT.escenas_de(p3)
ok("estimado" in fuente and len(esc) == 3 and esc[0]["t0"] == 0.0 and esc[-1]["t1"] == 9.0, "alinear 3D: sin palabras que casen, reparto estimado: %s" % fuente)
poner(V3 + "/maqueta.json", maq)
filas, _, _ = MT.alinear(p3, CURVA)
ok(len(filas) == 3 and filas[0]["r0"] == 1.0 and filas[1]["r0"] == 0.6 and filas[2]["perdida"] > 0, "alinear 3D con la curva: %s" % [(f["r0"], f["r1"]) for f in filas])
rc, salida = callado(MT.cmd_alinear, argparse.Namespace(pieza="falla", plataforma="tiktok", json=False))
ok(rc == 0 and "video3d:video3d-falla" in salida and "[ruptura · 2 claves de cámara]" in salida, "alinear falla (3D) por la línea de comandos:\n%s" % salida)
esc, fuente, _ = MT.escenas_de(MT.pieza_por("la-prueba-parte-1"))
ok(len(esc) == 5 and esc[0]["t1"] == 6.0 and fuente.endswith("parte-1/guion.json"), "alinear una parte: del guion entregado: %s" % fuente)
esc, fuente, _ = MT.escenas_de(MT.pieza_por("la-prueba-parte-2"))
ok(len(esc) == 2 and esc[1]["t0"] == 4.7 and esc[1]["t1"] == 148.0 and fuente == "sesiones/serie-la-prueba/parte-2/escenas.json", "alinear una parte: el escenas.json de su TRABAJO manda: %s" % fuente)
esc, fuente, _ = MT.escenas_de(MT.pieza_por("youtube:youtube-la-prueba"))
ok([(e["tipo"], e["t0"], e["t1"]) for e in esc] == [("capitulo", 0.0, 141.2), ("capitulo", 141.2, 300.0), ("capitulo", 300.0, 745.3)]
   and esc[1]["pantalla"] == "La caída", "alinear un largo: por capítulos: %s" % esc)

# ---------- el diagnóstico corre con las piezas nuevas y dice las vistas por día donde compara vistas ----------
H, base = MT.diagnosticar(M)
ok(base["piezas"] == 6, "diagnóstico: %d piezas vinculadas (se esperaban 6)" % base["piezas"])
an11 = next((h for h in H if h["codigo"] == "AN11"), None)
ok(an11 and "serie hold3" in an11["evidencia"] and "/día)" in an11["evidencia"], "AN11 no trae las partes de serie o las vistas por día: %s" % (an11 or {}).get("evidencia"))

shutil.rmtree(TMP, ignore_errors=True)
for x in F:
    print("FALLA", x)
print("[ola 1 · métricas] %s" % ("ok" if not F else "%d fallas" % len(F)))
sys.exit(1 if F else 0)
