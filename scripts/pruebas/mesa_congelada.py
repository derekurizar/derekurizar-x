#!/usr/bin/env python3
"""Los gates de la mesa de archivo sobre un plano CONGELADO: sin render, sin red y sin generar ningún trabajo (corre en RAPIDO).

El fixture (sesiones/_fixture_mesa_congelada/, ≈ 130 KB) trae lo mínimo que `video_hf` y `youtube_hf` leen para armar su
contexto y correr los gates sobre los datos:

  vertical/   la parte 1 de la maqueta de /serie (`make serie-fixture`): escenas.json, guion.json, encuadre.json,
              historia.json, video.json, base/{datos,hilo}.json, fotos/*.json (con un JPG de 1 px: el gate solo mira que
              exista) y tres planos: plano.borrador.json (el del trabajo, tal cual: lo compara --deriva), plano.json (el
              borrador CURADO A MANO hasta 0 fallas y 0 avisos) y plano_maqueta.json (DERIVADO: el curado con la mesa de e5
              cambiada por la de la maqueta 3D de sesiones/_fixture_serie/parte-1/mesa_maqueta.json, como `plano --con`)
  largo/      el trabajo de `make youtube-fixture` (16:9, dos capítulos): escenas.json, indice.json, youtube.json,
              base/historia.json, fotos/, plano.borrador.json y plano.json (curado a mano hasta 0 fallas y 0 avisos)

Los borradores de los trabajos NO pasan los gates (en una maqueta solo avisan): por eso los planos de las pruebas están
curados, y una mutación se mide contra un plano limpio.

Cada prueba carga el fixture en memoria (sobre una copia temporal: el gate de la maqueta escribe su maqueta.json), comprueba
que el plano sin mutar pasa con 0 fallas y aplica UNA mutación a una copia del plano o de las escenas: la mutación tiene que
AÑADIR al menos una falla de su código que el plano sin mutar no tenía (se comparan las fallas de antes y de después; no se
busca el código en la salida, que era el fallo de `yp_neg` en test.sh). Si no la añade, la prueba falla y dice cuál.
Además: `fixture` (completo, chico, sin apuntar a un trabajo generado) y `MV9-pila` (MV9 no es un gate: cuántas piezas deja
`componer` al frente, y que la guía diga lo mismo). Exit 0 ok · 1 falla · 2 uso.

Uso:
  python3 scripts/pruebas/mesa_congelada.py [prueba …]     corre todas, o solo las que se nombran (o un prefijo: «MV4»)
  python3 scripts/pruebas/mesa_congelada.py --lista        los nombres de las pruebas, con lo que muta cada una
  python3 scripts/pruebas/mesa_congelada.py --deriva       compara el fixture con los trabajos recién generados (si existen)
  python3 scripts/pruebas/mesa_congelada.py --congelar     regenera el fixture desde esos trabajos (no toca los planos curados)
  python3 scripts/pruebas/mesa_congelada.py -v [prueba …]  enseña qué fallas añadió cada mutación (+ = la esperada)
"""
import argparse
import base64
import contextlib
import copy
import glob
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

FIX_REL = "sesiones/_fixture_mesa_congelada"
FIX = os.path.join(RAIZ, FIX_REL)
# de dónde sale cada mitad del fixture (los trabajos que arman `make serie-fixture` y `make youtube-fixture`)
ORIGEN_V = "sesiones/_fixture_serie/trabajo/parte-1"
ORIGEN_SERIE = "sesiones/_fixture_serie/trabajo"
ORIGEN_L = "sesiones/_fixture_youtube/trabajo"
ORIGEN_MAQUETA = "sesiones/_fixture_serie/parte-1/mesa_maqueta.json"   # versionado: la mesa con maqueta 3D de `make video-fixture-maqueta`
# un JPG de 1 px: la ficha de una foto pide que su archivo exista (YT16/MV4); las medidas salen de `tamano`, no de la imagen
JPG_1PX = base64.b64decode(
    "/9j/4AAQSkZJRgABAgAAAQABAAD//gAPTGF2YzYzLjEuMTAyAP/bAEMACD4+ST5JVVVVVVVVZF1kaGhoZGRkZGhoaHBwcIODg3BwcGhocHB8fIODj5OPh4eDh5OTm5uburqystnZ4P/////EAEoAAQAAAAAA"
    "AAAAAAAAAAAAAAABAQAAAAAAAAAAAAAAAAAAAAAQAQAAAAAAAAAAAAAAAAAAAAARAQAAAAAAAAAAAAAAAAAAAAD/wAARCAABAAEDASIAAhEAAxEA/9oADAMBAAIRAxEAPwAAD//Z")
VOLATIL = ("fecha",)   # lo que cambia con el día en que se generó el trabajo y ningún gate lee


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(p, obj, legible=False):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        if legible:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
        else:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write("\n")


# ---------- el fixture: qué se copia y cómo (lo usan --congelar y --deriva) ----------
def sin_volatil(d):
    return {k: v for k, v in d.items() if k not in VOLATIL} if isinstance(d, dict) else d


def video_json_v(d):
    """video.json del vertical: su `hilo` (el respaldo de las cifras) apunta a la base congelada."""
    return dict(sin_volatil(d), hilo=FIX_REL + "/vertical/base")


def youtube_json(d):
    """youtube.json del largo: la cronología (base) y las partes (elenco, fotos, cifras) apuntan al fixture congelado."""
    d = dict(sin_volatil(d), base=FIX_REL + "/largo/base")
    d["partes"] = [dict(p, trabajo=FIX_REL + "/vertical") for p in d.get("partes") or []]
    return d


def escenas_largo(d):
    """escenas.json del 16:9 sin lo que le añaden los pasos posteriores al plano (`youtube.py miniatura` y `teaser`): ningún gate
    lo lee, y así --deriva vale igual tras `make youtube-fixture` entero que tras sus pasos hasta `plano --check`."""
    return {k: v for k, v in d.items() if k not in ("miniatura", "teaser")}


def igual(d):
    return d


def piezas_del_fixture(fichas="fixture"):
    """[(ruta en el fixture, ruta de origen relativa a la raíz, transformación)] de todo lo que se copia de los trabajos.
    Las fichas de fotos se listan del fixture (las pruebas: nunca miran un trabajo generado), del «origen» (--congelar) o de
    «ambos» (--deriva: una foto de más o de menos en el trabajo también es deriva)."""
    out = [("vertical/escenas.json", ORIGEN_V + "/escenas.json", igual),
           ("vertical/plano.borrador.json", ORIGEN_V + "/plano.borrador.json", igual),
           ("vertical/guion.json", ORIGEN_V + "/guion.json", igual),
           ("vertical/encuadre.json", ORIGEN_V + "/encuadre.json", igual),
           ("vertical/historia.json", ORIGEN_V + "/historia.json", igual),
           ("vertical/video.json", ORIGEN_V + "/video.json", video_json_v),
           ("vertical/base/datos.json", ORIGEN_V + "/base/datos.json", sin_volatil),
           ("vertical/base/hilo.json", ORIGEN_V + "/base/hilo.json", sin_volatil),
           ("largo/escenas.json", ORIGEN_L + "/escenas.json", escenas_largo),
           ("largo/plano.borrador.json", ORIGEN_L + "/plano.borrador.json", igual),
           ("largo/indice.json", ORIGEN_L + "/indice.json", igual),
           ("largo/youtube.json", ORIGEN_L + "/youtube.json", youtube_json),
           ("largo/base/historia.json", ORIGEN_SERIE + "/historia.json", igual)]
    for mitad, origen in (("vertical", ORIGEN_V), ("largo", ORIGEN_L)):
        donde = ([os.path.join(RAIZ, origen)] if fichas in ("origen", "ambos") else []) + ([os.path.join(FIX, mitad)] if fichas in ("fixture", "ambos") else [])
        for n in sorted({os.path.basename(f) for d in donde for f in glob.glob(os.path.join(d, "fotos", "*.json"))}):
            out.append(("%s/fotos/%s" % (mitad, n), "%s/fotos/%s" % (origen, n), igual))
    return out


CURADOS = ("vertical/plano.json", "largo/plano.json")   # escritos a mano: --congelar no los toca
DERIVADOS = ("vertical/plano_maqueta.json",)            # plano.json + la mesa con maqueta de ORIGEN_MAQUETA: --congelar lo rehace siempre


def con_maqueta(P, nuevas, orden):
    """Lo que hace `video_hf.py plano --con`: las mesas de `nuevas` reemplazan a las del plano que cubren sus escenas."""
    claves = {c for m in nuevas for c in m.get("escenas") or []}
    mesas = [m for m in P.get("mesas") or [] if not claves & set(m.get("escenas") or [])] + nuevas
    mesas.sort(key=lambda m: min([orden.get(c, 10 ** 6) for c in m.get("escenas") or []] or [10 ** 6]))
    return dict(P, mesas=mesas)


def plano_maqueta():
    """vertical/plano_maqueta.json como debe ser: el plano curado con la mesa de e5 cambiada por la de la maqueta 3D (o None si falta algo)."""
    fp, fe, fm = os.path.join(FIX, "vertical/plano.json"), os.path.join(FIX, "vertical/escenas.json"), os.path.join(RAIZ, ORIGEN_MAQUETA)
    if not all(os.path.exists(x) for x in (fp, fe, fm)):
        return None
    orden = {"e%d" % S["n"]: i for i, S in enumerate(leer(fe)["escenas"])}
    P = con_maqueta(leer(fp), leer(fm)["mesas"], orden)
    P["_comentario"] = ("DERIVADO (lo rehace `mesa_congelada.py --congelar`; no se edita): vertical/plano.json con la mesa de e5 cambiada por la mesa con maqueta 3D de "
                        "%s, como hace `video_hf.py plano --con`. Pasa MV1–MV19 con 0 fallas." % ORIGEN_MAQUETA)
    return P


def derivado_al_dia():
    """¿vertical/plano_maqueta.json es lo que sale hoy de plano.json y de la mesa con maqueta versionada? (None = no se puede saber)"""
    P, f = plano_maqueta(), os.path.join(FIX, DERIVADOS[0])
    return None if P is None or not os.path.exists(f) else leer(f) == P


def cmd_congelar():
    faltan = [o for _, o, _ in piezas_del_fixture("origen") if not os.path.exists(os.path.join(RAIZ, o))]
    if faltan:
        print("no se puede congelar: faltan %d archivos de los trabajos (corre `make serie-fixture` y `make youtube-fixture`):" % len(faltan), file=sys.stderr)
        for o in faltan[:8]:
            print("  " + o, file=sys.stderr)
        P = plano_maqueta()   # lo único que no sale de un trabajo generado
        if P:
            escribir(os.path.join(FIX, DERIVADOS[0]), P, legible=True)
            print("solo se rehízo %s (sale de plano.json y de %s, que están versionados)" % (DERIVADOS[0], ORIGEN_MAQUETA), file=sys.stderr)
        return 1
    for mitad in ("vertical", "largo"):   # las fichas de fotos que ya no están en el origen se van
        shutil.rmtree(os.path.join(FIX, mitad, "fotos"), ignore_errors=True)
    n = 0
    for dst, org, tr in piezas_del_fixture("origen"):
        d = tr(leer(os.path.join(RAIZ, org)))
        escribir(os.path.join(FIX, dst), d, legible="plano" in dst)
        n += 1
        if "/fotos/" in dst and d.get("archivo"):
            with open(os.path.join(FIX, dst.split("/")[0], d["archivo"]), "wb") as fh:
                fh.write(JPG_1PX)
    nuevos = []
    for c in CURADOS:   # un plano curado que falta nace del borrador (y habrá que curarlo: las pruebas dirán qué le falla)
        p = os.path.join(FIX, c)
        if not os.path.exists(p):
            shutil.copy(os.path.join(FIX, os.path.dirname(c), "plano.borrador.json"), p)
            nuevos.append(c)
    escribir(os.path.join(FIX, DERIVADOS[0]), plano_maqueta(), legible=True)
    peso = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(FIX) for f in fs)
    print("congelado: %d archivos de los trabajos → %s (%.0f KB en total)" % (n, FIX_REL, peso / 1024.0))
    print("planos curados %s: %s" % ("NUEVOS desde el borrador (cúralos a mano hasta 0 fallas)" if nuevos else "sin tocar", ", ".join(nuevos or CURADOS)))
    print("derivado, rehecho: %s (plano.json + %s)" % (DERIVADOS[0], ORIGEN_MAQUETA))
    print("ahora: python3 scripts/pruebas/mesa_congelada.py   (si las escenas cambiaron, los planos curados pueden necesitar ajuste)")
    return 0


def cmd_deriva():
    """El fixture congelado frente a los trabajos recién generados. Sale 1 si las escenas o el borrador del plano difieren
    (lo que los gates leen de verdad); lo demás que difiera se avisa. Sin trabajos: lo dice y sale 0."""
    hay = {o: os.path.isdir(os.path.join(RAIZ, o)) for o in (ORIGEN_V, ORIGEN_L)}
    for o, esta in hay.items():
        if not esta:
            print("deriva: no existe %s (se genera con `make %s`): nada que comparar ahí" % (o, "serie-fixture" if o == ORIGEN_V else "youtube-fixture"))
    if not any(hay.values()):
        print("deriva: sin trabajos generados; el fixture congelado no se comparó (exit 0)")
        return 0
    graves, leves, n = [], [], 0
    for dst, org, tr in piezas_del_fixture("ambos"):
        if not hay.get(ORIGEN_V if org.startswith(ORIGEN_SERIE) else ORIGEN_L):
            continue
        fo, fd = os.path.join(RAIZ, org), os.path.join(FIX, dst)
        n += 1
        if not os.path.exists(fo) or not os.path.exists(fd):
            leves.append("%s: falta %s" % (dst, "en el trabajo (%s)" % org if not os.path.exists(fo) else "en el fixture"))
            continue
        a, b = tr(leer(fo)), leer(fd)
        if a == b:
            continue
        que = "%s ≠ %s%s" % (dst, org, detalle(a, b))
        (graves if dst.endswith(("escenas.json", "plano.borrador.json")) else leves).append(que)
    n += 1   # el plano con maqueta, frente a lo que sale hoy de plano.json y de la mesa con maqueta versionada
    if derivado_al_dia() is False:
        graves.append("%s ≠ vertical/plano.json + %s" % (DERIVADOS[0], ORIGEN_MAQUETA))
    for x in leves:
        print("AVISO deriva:", x)
    for x in graves:
        print("DERIVA", x)
    if graves:
        print("deriva: las escenas o el borrador del plano cambiaron (%d de %d archivos). Recongela con "
              "`python3 scripts/pruebas/mesa_congelada.py --congelar` y vuelve a correr las pruebas (los planos curados pueden pedir ajuste)" % (len(graves), n))
        return 1
    print("deriva: %d archivos comparados con los trabajos; escenas y borradores idénticos%s" % (n, " (%d avisos)" % len(leves) if leves else ""))
    return 0


def detalle(a, b, ruta=""):
    """La primera diferencia entre dos JSON, para decir dónde derivó."""
    if type(a) is not type(b):
        return " (en %s: %s → %s)" % (ruta or "la raíz", type(b).__name__, type(a).__name__)
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                return detalle(a.get(k), b.get(k), "%s.%s" % (ruta, k) if ruta else k) if k in a and k in b else " (en %s: la clave `%s` %s)" % (
                    ruta or "la raíz", k, "es nueva" if k in a else "ya no está")
    if isinstance(a, list):
        if len(a) != len(b):
            return " (en %s: %d → %d elementos)" % (ruta or "la raíz", len(b), len(a))
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return detalle(x, y, "%s[%d]" % (ruta, i))
    return " (en %s: %r → %r)" % (ruta or "la raíz", b if not isinstance(b, (dict, list)) else "…", a if not isinstance(a, (dict, list)) else "…")




# ---------- el banco de pruebas: el fixture en memoria ----------
F = []            # las fallas de esta corrida
VERBOSO = False
_TMP = []         # la copia temporal del fixture (el gate de la maqueta escribe TRABAJO/maquetas/<mesa>/maqueta.json)
_BANCOS = {}


def ok(cond, que):
    if not cond:
        F.append(que)
    return bool(cond)


def modulos():
    """Los módulos de la mesa, importados al correr (no para --lista, --congelar ni --deriva)."""
    import video as VD
    import mesa as MS
    import video_hf as VH
    import youtube as YT
    import youtube_hf as YH
    return VD, MS, VH, YT, YH


@contextlib.contextmanager
def escenas_en_memoria(mod, E):
    """`mod.leer` devuelve E (una copia) cuando le piden escenas.json: el contexto se arma con las escenas mutadas sin tocar el disco."""
    real = mod.leer

    def leer_(p):
        return copy.deepcopy(E) if os.path.basename(p) == "escenas.json" else real(p)
    mod.leer = leer_
    try:
        yield
    finally:
        mod.leer = real


@contextlib.contextmanager
def callado():
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        yield err


class Banco:
    """Una mitad del fixture con uno de sus planos: `correr(P, E)` arma el contexto en memoria y pasa los gates."""
    PLANOS = {"V": ("vertical", "plano.json"), "Q": ("vertical", "plano_maqueta.json"), "L": ("largo", "plano.json")}

    def __init__(self, familia):
        if not _TMP:
            _TMP.append(tempfile.mkdtemp(prefix="mesa_congelada_"))
            shutil.copytree(FIX, os.path.join(_TMP[0], "f"))
        self.familia = familia
        mitad, plano = self.PLANOS[familia]
        self.trabajo = os.path.join(_TMP[0], "f", mitad)
        self.P = leer(os.path.join(self.trabajo, plano))
        self.E = leer(os.path.join(self.trabajo, "escenas.json"))
        self.plano = "%s/%s" % (mitad, plano)
        self.base = self.correr(self.P, self.E)

    def correr(self, P, E):
        """→ {fallas, avisos, mesas, ctx}. P y E no se tocan (los gates trabajan sobre copias)."""
        VD, MS, VH, YT, YH = modulos()
        P, E = copy.deepcopy(P), copy.deepcopy(E)
        with callado():
            if self.familia == "L":
                with escenas_en_memoria(YH, E):
                    ctx = YH.contexto(self.trabajo)
                mesas, f0 = YH.resolver(ctx, P)
                f, av, med = YH.revisar(ctx, P, mesas, f0)
            else:
                with escenas_en_memoria(VH, E):
                    ctx = VH.contexto_v(self.trabajo)
                mesas, f0 = VH.resolver_v(ctx, P)
                f, av, med = VH.revisar_v(ctx, P, mesas, f0)
        return {"fallas": f, "avisos": av, "mesas": mesas, "ctx": ctx, "medidas": med}


def banco(familia):
    if familia not in _BANCOS:
        _BANCOS[familia] = Banco(familia)
    return _BANCOS[familia]


def espacio(B, P, E):
    """Los nombres que ve una mutación: P (el plano), E (escenas.json), M (la mesa de trabajo), Q (su maqueta) y ayudantes.
    M es la de los negativos de test.sh: en el vertical, la primera mesa cuyas piezas llevan todas `dice` (la mesa 1 abre con
    las del cuadro 0); en el 16:9, la primera con piezas; con maqueta, la mesa de la maqueta."""
    VD, MS, VH, YT, YH = modulos()
    if B.familia == "L":
        YT.claves_visuales(E["escenas"])
    else:
        for S in E["escenas"]:
            S["clave"] = "e%d" % S["n"]

    def mesa(clave):
        return next(m for m in P["mesas"] if clave in (m.get("escenas") or []))

    def golpe(clave, tipo, n=0):
        m = mesa(clave)
        return [g for g in m["golpes"] if g.get("tipo") == tipo and (g.get("escena") or m["escenas"][0]) == clave][n]

    def escena(clave):
        return next(S for S in E["escenas"] if S["clave"] == clave)

    def cambia(clave, tipos, a):
        """Las piezas de esos tipos de la mesa de `clave` (o de todas con clave None) pasan a ser `a` (conservan dice y escena)."""
        for m in (P["mesas"] if clave is None else [mesa(clave)]):
            m["golpes"] = [dict(a, **{k: g[k] for k in ("dice", "escena") if g.get(k)}) if (tipos is None or g.get("tipo") in tipos) else g for g in m["golpes"]]

    def palabras(n):
        return " ".join(["zzz"] * n)

    if B.familia == "Q":
        M = next(m for m in P["mesas"] if m.get("maqueta"))
    elif B.familia == "L":
        M = next(m for m in P["mesas"] if m["golpes"])
    else:
        M = next(m for m in P["mesas"] if m["golpes"] and all(g.get("dice") for g in m["golpes"]))
    return {"P": P, "E": E, "M": M, "Q": M.get("maqueta"), "mesa": mesa, "golpe": golpe, "escena": escena, "cambia": cambia, "palabras": palabras,
            "copia": copy.deepcopy}


# ---------- las mutaciones: (nombre, familia, código, qué prueba, python que muta, [dónde, contiene]) ----------
# familia: V = vertical/plano.json · Q = vertical/plano_maqueta.json · L = largo/plano.json (16:9)
# Las marcadas «test.sh» son, tal cual, las de mv_neg, yp_neg y mq_neg de scripts/test.sh.
_FOTO_SIN_FICHA = 'M["golpes"].append(dict(tipo="foto", escena=M["golpes"][-1].get("escena", M["escenas"][0]), dice=M["golpes"][-1]["dice"], foto="zzz-f99", pie="Nada"))'
_RED = ('d = M["golpes"][-1]["dice"]; M["golpes"].append(dict(tipo="red", escena=M["golpes"][-1].get("escena", M["escenas"][0]), dice=d, '
        'nodos=[dict(id="a", nombre="Marta Pérez", nivel=0, dice=d), dict(id="b", nombre="Zzz", nivel=1, dice=d)], aristas=[dict(de="a", a="%s", atribuida=True, dice=d)]%s))')
_MAQ_GANCHO = 'P["mesas"] = [m for m in P["mesas"] if m["escenas"] != ["e1"]]; M["escenas"] = ["e1"]; M["golpes"] = []; Q.update(camara=Q["camara"][:1], eventos=[], marcas=[])'
_UNA_POR_MESA = 'for m in P["mesas"]: m["golpes"] = m["golpes"][:1]'
_TODO_TERMINO = 'cambia(None, None, dict(tipo="termino", texto="Zzz"))'
_SIN_ARCHIVO = 'cambia(None, ("foto", "lugar"), dict(tipo="termino", texto="Zzz"))'

MUTACIONES = [
    # --- vertical: los de mv_neg (test.sh) ---
    ("MV2-mesa-sin-piezas", "V", "MV2", "test.sh · una mesa sin piezas", 'M["golpes"] = []'),
    ("MV4-foto-sin-ficha", "V", "MV4", "test.sh · una foto sin ficha", _FOTO_SIN_FICHA),
    ("MV7-saltos-de-camara", "V", "MV7", "test.sh · una escena con saltos de cámara", 'E["escenas"][1]["saltos"] = [2.0]'),
    ("MV8-ficha-de-40-palabras", "V", "MV8", "test.sh · una ficha con 40 palabras que la voz no dice no da tiempo de leerse",
     'M["golpes"].insert(0, dict(tipo="institucion", escena=M["golpes"][0].get("escena", M["escenas"][0]), dice=M["golpes"][0]["dice"], nombre="Zzz", kicker="Qué es", '
     'rol=" ".join("palabra%d" % i for i in range(40))))'),
    ("MV11-no-cabe-ni-a-escala", "V", "MV11", "test.sh · una pieza que no cabe ni a escala (cita de 160 palabras)",
     'M["golpes"].insert(0, dict(tipo="cita", escena=M["golpes"][0].get("escena", M["escenas"][0]), dice=M["golpes"][0]["dice"], autor="Zzz", '
     'texto=" ".join("palabra%d" % i for i in range(160))))'),
    ("MV12-alegato-sin-segun", "V", "MV12", "test.sh · una jerarquía con un hilo de alegato sin «Según…»", _RED % ("b", "")),
    ("MV4-barra-sola", "V", "MV4", "test.sh · una barra sola (sin con qué compararse)",
     'M["golpes"].append(dict(tipo="barra", escena=M["golpes"][-1].get("escena", M["escenas"][0]), dice=M["golpes"][-1]["dice"], barras=[dict(etiqueta="Zzz", valor=1)]))'),
    ("MV4-barra-900-mide-10", "V", "MV4", "test.sh · una barra que dice 900 y mide 10",
     'M["golpes"].append(dict(tipo="barra", escena=M["golpes"][-1].get("escena", M["escenas"][0]), dice=M["golpes"][-1]["dice"], '
     'barras=[dict(etiqueta="A", valor=10, texto="900"), dict(etiqueta="B", valor=20)]))', "fallas", "el largo no corresponde"),
    # --- vertical: nuevos ---
    ("MV1-anio-sin-pieza", "V", "MV1", "el año que la voz dice (1952) se queda sin la pieza que lo muestra", 'mesa("e2")["golpes"].remove(golpe("e2", "fecha"))'),
    ("MV2-escena-sin-mesa", "V", "MV2", "una escena que ninguna mesa cubre", 'P["mesas"].remove(mesa("e4"))', "fallas", "ninguna mesa del plano la cubre"),
    ("MV2-hueco", "V", "MV2", "más de 4 s sin que entre nada (se quita la pieza del medio)", 'mesa("e7")["golpes"].remove(golpe("e7", "foto"))', "fallas", "sin que entre nada"),
    ("MV2-golpe-sin-dice", "V", "MV2", "una pieza sin `dice` fuera del cuadro 0", 'golpe("e2", "fecha").pop("dice")', "fallas", "falta `dice`"),
    ("MV2-dice-que-no-se-dice", "V", "MV2", "un `dice` que la voz de la escena no dice", 'golpe("e2", "termino")["dice"] = "zzz qqq"', "fallas", "no dice"),
    ("MV3-foto-dos-veces", "V", "MV3", "la misma foto en dos mesas (en vertical, una sola vez)", 'golpe("e7", "foto")["foto"] = golpe("e4", "foto")["foto"]'),
    ("MV4-documento-sin-pagina", "V", "MV4", "un documento cuya página no está en paginas.json (antes el gate reventaba con KeyError)",
     'M["golpes"].append(dict(tipo="documento", escena=M["golpes"][-1].get("escena", M["escenas"][0]), dice=M["golpes"][-1]["dice"], pagina="zzz-p1", titulo="Zzz"))'),
    ("MV4-pie-de-10-palabras", "V", "MV4", "una foto con un pie de 10 palabras", 'golpe("e2", "foto")["pie"] = palabras(10)', "fallas", "`pie` de 1 a 9 palabras"),
    ("MV4-retrato-sin-nombre", "V", "MV4", "un retrato en una escena donde la voz no nombra a nadie", 'golpe("e2", "foto")["foto"] = "ori-f03"', "fallas", "es un retrato"),
    ("MV4-persona-fuera-del-elenco", "V", "MV4", "una persona que no es del elenco y que la voz no nombra", 'golpe("e3", "persona")["persona"] = "Zutano Zzz"', "fallas", "no es del elenco"),
    ("MV4-institucion-sin-rol", "V", "MV4", "una institución sin kicker ni rol", 'M["golpes"].append(dict(tipo="institucion", dice=M["golpes"][-1]["dice"], nombre="Zzz"))',
     "fallas", "kicker o rol"),
    ("MV4-lugar-sin-depto", "V", "MV4", "un mapa de Guatemala sin `depto`", 'golpe("e2", "lugar").pop("depto")', "fallas", "lleva `depto`"),
    ("MV4-fecha-sin-grande", "V", "MV4", "una fecha sin `grande`", 'golpe("e2", "fecha").pop("grande")', "fallas", "lleva `grande`"),
    ("MV4-cifra-sin-rotulo", "V", "MV4", "una cifra sin `rotulo`", 'golpe("e6", "cifra").pop("rotulo")', "fallas", "`valor` y `rotulo`"),
    ("MV4-cifra-sin-respaldo", "V", "MV4", "una cifra que la voz no dice y sin respaldo en los datos", 'golpe("e6", "cifra")["rotulo"] = "de 98,765 panes"', "fallas", "no lo dice la voz"),
    ("MV4-termino-de-7-palabras", "V", "MV4", "un término de 7 palabras", 'golpe("e2", "termino")["texto"] = palabras(7)', "fallas", "`texto` de 1 a 6 palabras"),
    ("MV4-cita-sin-autor", "V", "MV4", "una cita sin `autor`", 'golpe("e3", "cita").pop("autor")', "fallas", "`texto` literal y `autor`"),
    ("MV4-lista-de-un-item", "V", "MV4", "una lista de un solo elemento", 'M["golpes"].append(dict(tipo="lista", dice=M["golpes"][-1]["dice"], items=[dict(texto="Zzz")]))',
     "fallas", "`items` son 2 a 6"),
    ("MV4-recorte-sin-nota", "V", "MV4", "un recorte de una nota que no se leyó",
     'M["golpes"].append(dict(tipo="recorte", dice=M["golpes"][-1]["dice"], url="https://zzz.invalid/nota", medio="Zzz", fecha="1968", titular="Zzz"))', "fallas", "nota ya leída"),
    ("MV4-tipo-desconocido", "V", "MV4", "un tipo de pieza que no existe", 'M["golpes"][0]["tipo"] = "zoom"', "fallas", "tipo desconocido"),
    ("MV4-golpe-de-otra-mesa", "V", "MV4", "una pieza cuya escena no es de su mesa", 'golpe("e2", "fecha")["escena"] = "e3"', "fallas", "no es de esta mesa"),
    ("MV4-escena-que-no-existe", "V", "MV4", "una mesa sobre una escena que no existe", 'mesa("e2")["escenas"] = ["e99"]', "fallas", "que no existe"),
    ("MV4-red-de-un-nodo", "V", "MV4", "una jerarquía de un solo nodo",
     'd = M["golpes"][-1]["dice"]; M["golpes"].append(dict(tipo="red", dice=d, nodos=[dict(id="a", nombre="Marta Pérez", nivel=0, dice=d)]))', "fallas", "de 2 nodos en adelante"),
    ("MV5-tres-textos-seguidos", "V", "MV5", "tres rótulos de solo texto seguidos (las fotos de e3 pasan a término)", 'cambia("e3", ("foto",), dict(tipo="termino", texto="Zzz"))',
     "fallas", "rótulos de solo texto seguidos"),
    ("MV5-sin-pieza-nueva", "V", "MV5", "menos de la mitad de las oraciones trae una pieza nueva (una pieza por mesa)", _UNA_POR_MESA, "fallas", "traen una pieza nueva"),
    ("MV5-poco-archivo-real", "V", "MV5", "menos del 35 % de archivo real (fotos y mapas pasan a término)", _SIN_ARCHIVO, "fallas", "son archivo real"),
    ("MV5-pocos-tipos", "V", "MV5", "menos de 4 tipos de pieza (todo pasa a término)", _TODO_TERMINO, "fallas", "tipos de pieza"),
    ("MV5-aviso-bajo-50", "V", "MV5", "AVISO: archivo real entre 35 y 50 % (un mapa pasa a término)", 'cambia("e1", ("lugar",), dict(tipo="termino", texto="Xela"))',
     "avisos", "la meta es 50"),
    ("MV6-mesa-de-mas-de-24-s", "V", "MV6", "una mesa de más de 24 s (e2 y e3 en una sola)",
     'a, b = mesa("e2"), mesa("e3"); P["mesas"].remove(b); a["golpes"] = [dict(g, escena="e2") for g in a["golpes"]] + [dict(g, escena="e3") for g in b["golpes"]]; '
     'a["escenas"] = ["e2", "e3"]', "fallas", "la mesa dura"),
    ("MV6-siete-piezas", "V", "MV6", "7 piezas en una mesa (máximo 6)",
     'mesa("e3")["golpes"] = [dict(tipo="termino", dice=w["text"], texto="Zzz") for w in escena("e3")["palabras"][:14:2]]', "fallas", "piezas en una mesa"),
    ("MV6-dos-piezas-a-la-vez", "V", "MV6", "dos piezas que entran con la misma palabra", 'M["golpes"].append(dict(tipo="termino", dice=M["golpes"][-1]["dice"], texto="Zzz"))',
     "fallas", "dos piezas entran"),
    ("MV6-cierre-en-el-plano", "V", "MV6", "el cierre (lo arma el script) puesto en el plano", 'P["mesas"].append(dict(escenas=["e8"], golpes=[]))', "fallas", "los arma el script"),
    ("MV6-escena-en-dos-mesas", "V", "MV6", "una escena en dos mesas", 'P["mesas"].append(copia(mesa("e2")))', "fallas", "no va en dos mesas"),
    ("MV6-escenas-salteadas", "V", "MV6", "una mesa con escenas que no van seguidas", 'P["mesas"].remove(mesa("e4")); mesa("e2")["escenas"] = ["e2", "e4"]', "fallas", "van seguidas"),
    ("MV6-golpe-de-tablero", "V", "MV6", "el golpe de un tablero entra antes de su último paso (e6 pasa a ser una tarjeta con un paso a los 2 s)",
     'escena("e6").update(tipo="tarjeta", eventos=[dict(t=2.0, tipo="paso")])', "fallas", "tablero"),
    ("MV6-tablero-con-otra-escena", "V", "MV6", "un tablero (e6 pasa a ser una tarjeta) compartiendo mesa con otra escena",
     'escena("e6")["tipo"] = "tarjeta"; a, b = mesa("e6"), mesa("e7"); P["mesas"].remove(b); a["escenas"] = ["e6", "e7"]', "fallas", "va sola en su mesa"),
    ("MV8-doce-palabras-en-tres-segundos", "V", "MV8", "una ficha con 12 palabras que la voz no dice, replegada a los ≈ 3 s por la pieza siguiente (pide 0.5 + 0.3 × palabras)",
     'golpe("e7", "fecha").update(tipo="institucion", nombre="Zzz", kicker="Qué es", rol=palabras(12))', "fallas", re.compile(r"queda [1-9]\.\d s al frente y pide [4-9]\.\d s")),
    ("MV8-ocho-palabras-al-final-de-la-mesa", "V", "MV8", "una ficha con 8 palabras que la voz no dice entra a ≈ 2 s de que la mesa se barra",
     'm = mesa("e2"); m["golpes"][-1] = dict(tipo="institucion", dice=m["golpes"][-1]["dice"], nombre="Zzz", kicker="Qué es", rol=palabras(8))', "fallas",
     re.compile(r"queda [1-9]\.\d s al frente y pide [2-9]\.\d s")),
    ("MV10-ni-al-40-por-ciento", "V", "MV10", "una pieza que ni al 40 % cabe en la zona segura (cita de 400 palabras)",
     'M["golpes"].insert(0, dict(tipo="cita", dice=M["golpes"][0]["dice"], autor="Zzz", texto=palabras(400)))'),
    ("MV12-hilo-a-quien-no-esta", "V", "MV12", "un hilo hacia alguien que no es un nodo de la jerarquía", _RED % ("zzz", ', etiqueta="Según la acusación"'), "fallas", "un hilo une dos nodos"),
    ("MV12-voz-no-atribuye", "V", "MV12", "un alegato con su etiqueta pero la voz de la mesa no lo atribuye", _RED % ("b", ', etiqueta="Según la acusación"'), "fallas", "no atribuye"),
    ("MV13-dos-acentos-al-frente", "V", "MV13", "una nota en acento y la cifra, las dos al frente (la foto de e6 pasa a nota)",
     'cambia("e6", ("foto",), dict(tipo="termino", texto="Un fuego"))', "fallas", "un solo acento a la vez"),
    ("MV13-subrayado-y-cifra", "V", "MV13", "AVISO: un recorte con su frase subrayada y la cifra, los dos al frente (una marca junto a un dato no bloquea)",
     'cambia("e6", ("foto",), dict(tipo="recorte", medio="Zzz", fecha="1968", extracto="un solo fuego para todo el pan", resalta="un solo fuego"))', "avisos", "el subrayado del recorte"),
    ("MV13-dos-notas", "V", "MV13", "AVISO: dos notas en acento al frente (dos bloques no bloquean: así salieron los pilotos aprobados)",
     'cambia("e6", ("foto",), dict(tipo="termino", texto="Un fuego")); cambia("e6", ("cifra",), dict(tipo="termino", texto="Cuatro mil"))', "avisos", "dos acentos a la vez"),
    ("MV13-crema-donde-no-vale", "V", "MV13", "`crema` en una foto (el motor no sabe dibujarla distinta)", 'golpe("e2", "foto")["crema"] = True', "fallas", "solo vale en"),
    ("MV14-cuadro-0-con-una-pieza", "V", "MV14", "el cuadro 0 abre con una sola pieza (la otra espera a la voz)", 'golpe("e1", "termino")["dice"] = "La Espiga:"'),
    # --- vertical con maqueta: los de mq_neg (test.sh) ---
    ("MV15-estilo-fuera-del-catalogo", "Q", "MV15", "test.sh · un estilo que no está en el catálogo", 'Q["estilo"] = "zzz"'),
    ("MV15-camara-1-con-dice", "Q", "MV15", "test.sh · la primera clave de cámara con dice", 'Q["camara"][0]["dice"] = "Pero el salto"'),
    ("MV16-dice-que-la-mesa-no-dice", "Q", "MV16", "test.sh · un dice que la voz de la mesa no dice", 'Q["marcas"][0]["dice"] = "cinco sucursales"'),
    ("MV17-dos-estilos", "Q", "MV17", "test.sh · dos maquetas de estilos distintos",
     'P["mesas"] = [m for m in P["mesas"] if m["escenas"] != ["e7"]] + [dict(escenas=["e7"], titulo="Otra", golpes=[], '
     'maqueta=dict(Q, estilo="color", marcas=[], eventos=[], camara=Q["camara"][:1]))]'),
    ("MV18-maqueta-de-menos-de-5-s", "Q", "MV18", "test.sh · una maqueta de menos de 5 s (y en el gancho)", _MAQ_GANCHO),
    ("MV19-camara-que-el-motor-rechaza", "Q", "MV19", "test.sh · una cámara que el motor rechaza (M3D3)", 'Q["camara"][1]["dist_km"] = 5'),
    ("MV1-cifra-sin-golpe-en-la-maqueta", "Q", "MV1", "test.sh · la cifra que la voz dice, sin su golpe", 'M["golpes"] = M["golpes"][:1]'),
    ("MV11-pieza-que-tapa-la-maqueta", "Q", "MV11", "test.sh · una pieza que taparía la maqueta",
     'M["golpes"][1] = dict(tipo="cita", dice="4,500 panes", autor="Zzz", texto=" ".join("palabra%d" % i for i in range(60)))'),
    # --- vertical con maqueta: nuevos ---
    ("MV14-gancho-con-maqueta", "Q", "MV14", "la maqueta en el gancho (el cuadro 0 abre con el sujeto)", _MAQ_GANCHO, "fallas", "el gancho no lleva maqueta"),
    ("MV15-maqueta-sobre-un-tablero", "Q", "MV15", "una maqueta en la mesa de un tablero (e5 pasa a ser una tarjeta, que ya trae su animación)",
     'escena("e5")["tipo"] = "tarjeta"', "fallas", "es un tablero"),
    ("MV15-maqueta-sin-piezas", "Q", "MV15", "una maqueta sin `piezas` (lo que hay sobre el mundo)", 'Q["piezas"] = []', "fallas", "`piezas` son una o más"),
    ("MV16-camara-sin-dice", "Q", "MV16", "una clave de cámara (que no es la primera) sin `dice` ni `al`", 'Q["camara"][1].pop("dice")', "fallas", "falta `dice`"),
    ("MV4-pin-con-numero-sin-respaldo", "Q", "MV4", "un pin de la maqueta con un número sin respaldo", 'Q["marcas"][0]["sub"] = "98,765 habitantes"', "fallas", "marca 1"),
    ("MV18-cinco-piezas-sobre-la-maqueta", "Q", "MV18", "5 piezas con la maqueta (máximo 3)",
     'M["golpes"] = [dict(tipo="termino", dice=d, texto="Zzz") for d in ("Pero el", "diez años", "el barrio", "en 1968")] + M["golpes"][1:]', "fallas", "piezas con la maqueta"),
    ("MV18-tres-maquetas", "Q", "MV18", "una tercera maqueta en un vertical (máximo 2)",
     'P["mesas"] = [m for m in P["mesas"] if m["escenas"] not in (["e4"], ["e7"])] + [dict(escenas=[c], golpes=[], maqueta=dict(Q, marcas=[], eventos=[], camara=Q["camara"][:1])) '
     'for c in ("e4", "e7")]', "fallas", "n.º 3 del video"),
    # --- 16:9: los de yp_neg (test.sh) ---
    ("YT14-mesa-sin-piezas", "L", "YT14", "test.sh · una mesa sin piezas (ninguna oración trae un golpe)", 'M["golpes"] = []'),
    ("YT14-dice-que-no-se-dice", "L", "YT14", "test.sh · un «dice» que la voz no dice", 'M["golpes"][0]["dice"] = "zzz qqq"'),
    ("YT16-cifra-sin-respaldo", "L", "YT16", "test.sh · una cifra que la voz no dice y sin respaldo",
     'M["golpes"].append(dict(tipo="cifra", escena=M["golpes"][-1].get("escena", M["escenas"][0]), dice=M["golpes"][-1]["dice"], valor="98,765", rotulo="panes"))'),
    ("YT16-foto-sin-ficha", "L", "YT16", "test.sh · una foto sin ficha", _FOTO_SIN_FICHA),
    ("YT16-tipo-desconocido", "L", "YT16", "test.sh · un tipo de pieza desconocido", 'M["golpes"][0]["tipo"] = "zoom"'),
    ("YT16-documento-sin-pagina", "L", "YT16", "un documento cuya página no está en paginas.json",
     'M["golpes"].append(dict(tipo="documento", escena=M["golpes"][-1]["escena"], dice=M["golpes"][-1]["dice"], pagina="zzz-p1", titulo="Zzz"))', "fallas", "paginas.json"),
    ("YT19-saltos-de-camara", "L", "YT19", "test.sh · una escena con saltos de cámara", 'E["escenas"][1]["saltos"] = [2.0]'),
    # --- 16:9: nuevos ---
    ("YT13-anio-sin-pieza", "L", "YT13", "el año que la voz dice (1971) se queda sin la pieza que lo muestra", 'mesa("P2.e7")["golpes"].remove(golpe("P2.e7", "fecha"))'),
    ("YT14-escena-sin-mesa", "L", "YT14", "una escena que ninguna mesa cubre", 'P["mesas"].remove(mesa("P1.e4"))', "fallas", "ninguna mesa del plano la cubre"),
    ("YT14-hueco", "L", "YT14", "más de 6 s sin que entre nada", 'm = mesa("P1.e3"); m["golpes"] = [m["golpes"][0], m["golpes"][-1]]', "fallas", "sin que entre nada"),
    ("YT15-foto-que-vuelve-pronto", "L", "YT15", "la misma foto dos veces a menos de 180 s", 'golpe("P2.e7", "foto")["foto"] = golpe("P1.e2", "foto")["foto"]',
     "fallas", "vuelve a los"),
    ("YT15-foto-tres-veces", "L", "YT15", "la misma foto tres veces (máximo 2)",
     'golpe("P2.e7", "foto")["foto"] = golpe("P1.e4", "foto")["foto"] = golpe("P1.e2", "foto")["foto"]', "fallas", "sale 3 veces"),
    ("YT17-tres-textos-seguidos", "L", "YT17", "tres rótulos de solo texto seguidos", 'cambia("P1.e3", ("foto",), dict(tipo="termino", texto="Zzz"))',
     "fallas", "rótulos de solo texto seguidos"),
    ("YT17-sin-pieza-nueva", "L", "YT17", "menos de la mitad de las oraciones trae una pieza nueva (una pieza por mesa)", _UNA_POR_MESA, "fallas", "traen una pieza nueva"),
    ("YT17-poco-archivo-real", "L", "YT17", "un capítulo con menos del 35 % de archivo real", _SIN_ARCHIVO, "fallas", "son archivo real"),
    ("YT17-pocos-tipos", "L", "YT17", "un capítulo con menos de 4 tipos de pieza", _TODO_TERMINO, "fallas", "tipos de pieza"),
    ("YT17-aviso-bajo-50", "L", "YT17", "AVISO: un capítulo con archivo real entre 35 y 50 %", 'cambia("P2.e7", ("foto",), dict(tipo="termino", texto="Zzz"))',
     "avisos", "la meta es 50"),
    ("YT18-mesa-de-menos-de-4-s", "L", "YT18", "una mesa de menos de 4 s (su primera pieza entra tarde)", 'm = mesa("P2.e7"); m["golpes"] = m["golpes"][-1:]', "fallas", "la mesa dura"),
    ("YT18-trece-piezas", "L", "YT18", "13 piezas en una mesa (máximo 12)",
     'mesa("P1.e3")["golpes"] = [dict(tipo="termino", dice=w["text"], texto="Zzz") for w in escena("P1.e3")["palabras"][:26:2]]', "fallas", "piezas en una mesa"),
    ("YT18-dos-piezas-a-la-vez", "L", "YT18", "dos piezas que entran con la misma palabra",
     'M["golpes"].append(dict(tipo="termino", escena=M["golpes"][-1]["escena"], dice=M["golpes"][-1]["dice"], texto="Zzz"))', "fallas", "dos piezas entran"),
    ("YT18-capitulo-en-el-plano", "L", "YT18", "un rótulo de capítulo (lo arma el script) puesto en el plano", 'P["mesas"].append(dict(escenas=["capitulo-1"], golpes=[]))',
     "fallas", "los arma el script"),
    ("YT18-escena-en-dos-mesas", "L", "YT18", "una escena en dos mesas", 'P["mesas"].append(copia(mesa("P1.e2")))', "fallas", "no va en dos mesas"),
    ("YT18-escenas-salteadas", "L", "YT18", "una mesa con escenas que no van seguidas", 'P["mesas"].remove(mesa("P1.e4")); mesa("P1.e2")["escenas"] = ["P1.e2", "P1.e4"]',
     "fallas", "van seguidas"),
]
SIN_NEGATIVO = [
    ("MV9", "no es un gate: no hay `FALLA MV9` en el código; la pila sale de cómo `componer` coloca las piezas (la prueba `MV9-pila` fija el número)"),
]


def nuevas(antes, despues):
    """Lo que `despues` trae y `antes` no (por mensaje, con su cuenta)."""
    from collections import Counter
    return list((Counter(despues) - Counter(antes)).elements())


def correr_mutacion(nombre, familia, codigo, que, cambio, donde="fallas", contiene=None):
    B = banco(familia)
    P, E = copy.deepcopy(B.P), copy.deepcopy(B.E)
    try:
        exec(cambio, espacio(B, P, E))
    except Exception as ex:   # una mutación que no se aplicó no prueba nada
        return ok(False, "%s: la mutación no se pudo aplicar sobre %s (%s: %s): %s" % (nombre, B.plano, type(ex).__name__, ex, cambio))
    if not ok(P != B.P or E != B.E, "%s: la mutación no cambió nada: %s" % (nombre, cambio)):
        return False
    R = B.correr(P, E)
    mas = nuevas(B.base[donde], R[donde])
    suyas = [x for x in mas if x.startswith(codigo + " ") and (contiene is None or (contiene.search(x) if hasattr(contiene, "search") else contiene in x))]
    if VERBOSO:
        for x in mas:
            print("      %s %s %s" % ("+" if x in suyas else "·", "FALLA" if donde == "fallas" else "AVISO", x[:230]))
    return ok(suyas, "%s: la mutación no añadió %s %s%s (%s) al plano %s. Añadió: %s" % (
        nombre, "una falla" if donde == "fallas" else "un aviso", codigo, " con «%s»" % getattr(contiene, "pattern", contiene) if contiene else "", que, B.plano,
        "; ".join(x[:110] for x in mas[:4]) or "nada"))


# ---------- las pruebas que no son una mutación ----------
def prueba_base(familia):
    def correr():
        B = banco(familia)
        ok(not B.base["fallas"], "base: %s ya no pasa sin mutar (%d fallas): %s" % (B.plano, len(B.base["fallas"]), "; ".join(x[:140] for x in B.base["fallas"][:5])))
        ok(B.base["mesas"] and sum(len(M["golpes"]) for M in B.base["mesas"]) >= 15, "base: %s casi no trae piezas" % B.plano)
        if familia == "Q":   # test.sh: «la mesa de la maqueta no añade avisos (MV15–MV19 en 0)»
            M = next((M for M in B.base["mesas"] if M["clase"] == "maqueta"), None)
            ok(M is not None, "base: %s no trae la mesa con maqueta 3D" % B.plano)
            malos = [x for x in B.base["fallas"] + B.base["avisos"] if re.match(r"MV1[5-9] ", x) or (M and re.match(r"MV\d+ %s " % M["id"], x))]
            ok(not malos, "base: la mesa de la maqueta añade avisos: %s" % "; ".join(malos[:3]))
        else:
            ok(not B.base["avisos"], "base: %s trae avisos sin mutar: %s" % (B.plano, "; ".join(x[:140] for x in B.base["avisos"][:3])))
    return correr


def pila(B, R):
    """Cuántas piezas hay al frente a la vez, y cuántas compactas arriba, en cada mesa de piezas y en cada formato → (máx. frente, máx. compactas)."""
    VD, MS, VH, YT, YH = modulos()
    ctx = R["ctx"]
    Fi = MS.fichas(ctx["trabajo"])
    frente = compactas = 0
    for M in R["mesas"]:
        if M["clase"] != "mesa" or not M["golpes"]:
            continue
        for fmt in VH.FORMATOS:
            with callado():
                C = VH.componer(ctx, M, fmt, Fi, ctx["elenco"])
            for p in C["piezas"]:
                t = p["t"]
                frente = max(frente, sum(1 for q in C["piezas"] if q["t"] <= t and (q["hasta"] is None or q["hasta"] > t)))
                compactas = max(compactas, sum(1 for c in C["compactas"] if c["desde"] <= t and (c["hasta"] is None or c["hasta"] > t)))
    return frente, compactas


def prueba_mv9():
    """MV9 no es un gate: es lo que `componer` deja al frente. El código deja PILA_LEGIBLES (3) en fila más una chica al lado
    de la tercera = 4, y PILA_COMPACTAS (2) arriba; la guía dice lo mismo."""
    VD, MS, VH, YT, YH = modulos()
    ok((VH.PILA_LEGIBLES, VH.PILA_COMPACTAS) == (3, 2), "MV9: PILA_LEGIBLES, PILA_COMPACTAS = %s, %s (la guía y esta prueba dicen 3 y 2)" % (VH.PILA_LEGIBLES, VH.PILA_COMPACTAS))
    tope = VH.PILA_LEGIBLES + 1
    B = banco("V")
    f0, c0 = pila(B, B.base)
    ok(1 <= f0 <= tope and c0 <= VH.PILA_COMPACTAS, "MV9: el plano curado deja %d piezas al frente y %d compactas (tope %d y %d)" % (f0, c0, tope, VH.PILA_COMPACTAS))
    # la mesa más cargada posible: 12 piezas chicas seguidas en e3 (una cada dos palabras)
    P, E = copy.deepcopy(B.P), copy.deepcopy(B.E)
    exec('mesa("e3")["golpes"] = [dict(tipo="termino", dice=w["text"], texto="Zzz") for w in escena("e3")["palabras"][:24:2]]', espacio(B, P, E))
    R = B.correr(P, E)
    f1, c1 = pila(B, R)
    ok(f1 == tope, "MV9: con 12 piezas chicas seguidas quedan %d al frente a la vez; el código deja %d (PILA_LEGIBLES + 1: tres en fila y una chica al lado)" % (f1, tope))
    ok(c1 == VH.PILA_COMPACTAS, "MV9: con 12 piezas chicas seguidas quedan %d compactas arriba; van %d (PILA_COMPACTAS)" % (c1, VH.PILA_COMPACTAS))
    # 12 piezas grandes: nunca más de PILA_LEGIBLES
    P, E = copy.deepcopy(B.P), copy.deepcopy(B.E)
    exec('mesa("e3")["golpes"] = [dict(tipo="institucion", dice=w["text"], nombre="Zzz zzz zzz zzz zzz", rol="Qué es") for w in escena("e3")["palabras"][:24:2]]', espacio(B, P, E))
    f2, c2 = pila(B, B.correr(P, E))
    ok(f2 <= VH.PILA_LEGIBLES and c2 <= VH.PILA_COMPACTAS, "MV9: con 12 piezas anchas quedan %d al frente y %d compactas (tope %d y %d)" % (f2, c2, VH.PILA_LEGIBLES, VH.PILA_COMPACTAS))
    # no es un gate: ninguna falla lleva ese código, ni cargando la mesa
    ok(not any(x.startswith("MV9 ") for x in R["fallas"] + R["avisos"]), "MV9: ahora hay una falla MV9: es un gate; ponle su negativo y corrige la guía")
    fuente = open(os.path.join(RAIZ, "scripts", "video_hf.py"), encoding="utf-8").read() + open(os.path.join(RAIZ, "scripts", "mesa.py"), encoding="utf-8").read()
    ok(not re.search(r'"MV9[ :]', fuente), "MV9: el código ya emite un mensaje «MV9 …»: es un gate; ponle su negativo y corrige la guía")
    # la guía dice lo que el código hace
    guia = open(os.path.join(RAIZ, "referencias", "flujo-mesa.md"), encoding="utf-8").read()
    fila = next((ln for ln in guia.splitlines() if ln.startswith("| MV9 |")), "")
    m1, m2 = re.search(r"≤ (\d+) piezas al frente", fila), re.search(r"≤ (\d+) compactas", fila)
    ok(m1 and int(m1.group(1)) == tope, "MV9: referencias/flujo-mesa.md dice «%s» y el código deja %d piezas al frente" % (fila[:90], tope))
    ok(m2 and int(m2.group(1)) == VH.PILA_COMPACTAS, "MV9: referencias/flujo-mesa.md no dice «≤ %d compactas»: %s" % (VH.PILA_COMPACTAS, fila[:90]))
    ok("no es un gate" in fila, "MV9: referencias/flujo-mesa.md no dice que MV9 no es un gate")


def prueba_fixture():
    """El fixture está completo, es chico y no apunta fuera de sí mismo."""
    faltan = [d for d, _, _ in piezas_del_fixture() if not os.path.exists(os.path.join(FIX, d))] + [c for c in CURADOS + DERIVADOS if not os.path.exists(os.path.join(FIX, c))]
    ok(not faltan, "fixture: faltan %s (python3 scripts/pruebas/mesa_congelada.py --congelar)" % ", ".join(faltan[:6]))
    peso = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(FIX) for f in fs)
    ok(peso <= 160 * 1024, "fixture: pesa %.0f KB (va en ≈ 130 KB: sin imágenes ni audio)" % (peso / 1024.0))
    grandes = [f for d, _, fs in os.walk(FIX) for f in fs if f.endswith((".jpg", ".png")) and os.path.getsize(os.path.join(d, f)) > 1024]
    ok(not grandes, "fixture: hay imágenes de verdad (%s): las fichas llevan un JPG de 1 px" % ", ".join(grandes[:4]))
    if not faltan:
        st, Y = leer(os.path.join(FIX, "vertical/video.json")), leer(os.path.join(FIX, "largo/youtube.json"))
        fuera = [x for x in [st.get("hilo"), Y.get("base")] + [p.get("trabajo") for p in Y.get("partes") or []] if not str(x).startswith(FIX_REL + "/")]
        ok(not fuera, "fixture: video.json o youtube.json apuntan fuera del fixture congelado: %s" % fuera)
        ok(st.get("realizacion") == "mesa", "fixture: vertical/video.json no dice realizacion: mesa")
        ok(derivado_al_dia() is not False, "fixture: %s ya no es vertical/plano.json + %s (cambió uno de los dos): python3 scripts/pruebas/mesa_congelada.py --congelar"
           % (DERIVADOS[0], ORIGEN_MAQUETA))


PRUEBAS = [("fixture", "el fixture congelado está completo, pesa ≤ 160 KB y no apunta a ningún trabajo generado", prueba_fixture),
           ("base-vertical", "vertical/plano.json sin mutar: 0 fallas y 0 avisos (MV1–MV14)", prueba_base("V")),
           ("base-maqueta", "vertical/plano_maqueta.json sin mutar: 0 fallas; la mesa con maqueta no añade avisos (MV15–MV19)", prueba_base("Q")),
           ("base-largo", "largo/plano.json sin mutar: 0 fallas y 0 avisos (YT13–YT19)", prueba_base("L")),
           ("MV9-pila", "MV9 no es un gate: el código deja 4 piezas al frente (3 + 1 al lado) y 2 compactas, y la guía dice lo mismo", prueba_mv9)]
PRUEBAS += [(m[0], "%s → %s" % (m[3], m[2]), (lambda m=m: correr_mutacion(*m))) for m in MUTACIONES]


def cmd_lista():
    porque = {m[0]: m for m in MUTACIONES}
    for nombre, que, _ in PRUEBAS:
        print("%-34s %s" % (nombre, que))
        if nombre in porque:
            m = porque[nombre]
            print("%-34s   [%s] %s" % ("", Banco.PLANOS[m[1]][0] + "/" + Banco.PLANOS[m[1]][1], m[4]))
    for cod, por in SIN_NEGATIVO:
        print("%-34s sin negativo: %s" % ("(" + cod + ")", por))
    return 0


def main():
    global VERBOSO
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pruebas", nargs="*", help="nombres de pruebas (o un prefijo: «MV4», «YT1», «base»); sin nombres, todas")
    ap.add_argument("--lista", action="store_true", help="los nombres de las pruebas con su mutación, y los gates que quedan sin negativo")
    ap.add_argument("--congelar", action="store_true", help="regenera el fixture desde los trabajos recién generados (no toca los planos curados)")
    ap.add_argument("--deriva", action="store_true", help="compara el fixture con los trabajos recién generados; sin trabajos lo dice y sale 0")
    ap.add_argument("-v", "--verboso", action="store_true", help="enseña lo que cada mutación añadió (+ = lo que se esperaba)")
    a = ap.parse_args()
    VERBOSO = a.verboso
    if a.lista:
        return cmd_lista()
    if a.congelar:
        return cmd_congelar()
    if a.deriva:
        return cmd_deriva()
    nombres = [n for n, _, _ in PRUEBAS]
    pedidas = []
    for p in a.pruebas or nombres:
        suyas = [n for n in nombres if n == p] or [n for n in nombres if n.startswith(p)]
        if not suyas:
            print("no hay ninguna prueba «%s» (python3 scripts/pruebas/mesa_congelada.py --lista)" % p, file=sys.stderr)
            return 2
        pedidas += [n for n in suyas if n not in pedidas]
    if not os.path.isdir(FIX):
        print("FALLA no existe %s (python3 scripts/pruebas/mesa_congelada.py --congelar, tras `make serie-fixture` y `make youtube-fixture`)" % FIX_REL)
        return 1
    t0 = time.time()
    por_nombre = {n: fn for n, _, fn in PRUEBAS}
    malas = 0
    try:
        for n in pedidas:
            n0 = len(F)
            try:
                por_nombre[n]()
            except Exception as ex:   # una prueba que revienta es una falla con su causa, y las demás siguen
                import traceback
                F.append("%s: reventó: %s: %s\n%s" % (n, type(ex).__name__, ex, traceback.format_exc(limit=5)))
            mal = len(F) - n0
            malas += bool(mal)
            if mal or VERBOSO or a.pruebas:
                print("%-34s %s" % (n, "ok" if not mal else "%d falla(s)" % mal))
    finally:
        for d in _TMP:
            shutil.rmtree(d, ignore_errors=True)
    for x in F:
        print("FALLA", x)
    print("[mesa congelada] %d pruebas · %s (%.1f s)" % (len(pedidas), "ok" if not F else "%d con fallas" % malas, time.time() - t0))
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
