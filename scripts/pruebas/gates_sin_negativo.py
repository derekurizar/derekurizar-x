#!/usr/bin/env python3
"""Negativos de gates que no tenían ninguno en scripts/test.sh (sin render, sin red, sin créditos; corre en RAPIDO).

Como scripts/pruebas/mesa_congelada.py: cada prueba parte de algo que PASA (o de sus fallas de partida) y aplica una
mutación que tiene que AÑADIR una falla de su código; no basta con que el código salga en la salida.

  SE17  serie.revisar_completa: faltan guiones · el puente de una parte no lo abre la siguiente (datos de juguete)
  SE18  serie.revisar_parte: la última parte sin `responde_serie` (el guion de sesiones/_fixture_serie/parte-1)
  SE19  serie.fotos_repetidas: una foto que ya salió en 2 partes (datos de juguete)
  CG8   congreso.py guion --check: sin «pero / por eso» · el gancho sin «Congreso» (sesiones/_fixture_congreso)
  CG9   congreso.py guion --check: 3 escenas · cierre con resumen · cierre.texto ≠ cierre.final
  C3D5  video3d.revisar_guion: un pin con un número sin respaldo (sesiones/_fixture_video3d)
  C3D7  video3d.revisar_guion: 10 s sin nada nuevo (falla) y 7 s (aviso)
  M3D7  maqueta3d.NEGATIVOS ya lo trae (3 negativos, los corre ola1_video3d.py): aquí solo se comprueba que siguen ahí y muerden

Sin negativo posible aquí: CA10 y CA11 (scripts/carrusel.js los mide dentro de la página, con Playwright).

Uso: python3 scripts/pruebas/gates_sin_negativo.py [prueba … | prefijo] [--lista] [-v]. Exit 0 ok · 1 falla · 2 uso.
"""
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
import time
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

F = []
VERBOSO = False
TMP = tempfile.mkdtemp(prefix="gates_sin_negativo_")


def ok(cond, que):
    if not cond:
        F.append(que)
    return bool(cond)


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


@contextlib.contextmanager
def callado():
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        yield out


def anade(nombre, codigo, antes, despues, contiene=None, que="una falla"):
    """La mutación añadió una falla (o un aviso) de su código que antes no estaba."""
    mas = list((Counter(despues) - Counter(antes)).elements())
    suyas = [x for x in mas if x.startswith(codigo + " ") and (contiene is None or contiene in x)]
    if VERBOSO:
        for x in mas:
            print("      %s %s" % ("+" if x in suyas else "·", x[:230]))
    return ok(suyas, "%s: la mutación no añadió %s %s%s. Añadió: %s" % (nombre, que, codigo, " con «%s»" % contiene if contiene else "",
                                                                      "; ".join(x[:120] for x in mas[:4]) or "nada"))


# ---------- /serie: SE17, SE18, SE19 ----------
def guion_de(textos, final="", invitacion="", foto=None):
    return {"escenas": [dict({"tipo": "foto", "texto": t}, **({"foto": foto} if foto else {})) for t in textos],
            "cierre": {"texto": final, "final": final, "invitacion": invitacion}}


def serie_de_juguete(nombre, guiones):
    """Una serie con sus partes en TMP/<nombre>/parte-N (guion.json donde se da uno) → (S, carpeta)."""
    base = os.path.join(TMP, nombre)
    partes = []
    for n, g in enumerate(guiones, 1):
        d = os.path.join(base, "parte-%d" % n)
        os.makedirs(d, exist_ok=True)
        if g is not None:
            escribir(os.path.join(d, "guion.json"), g)
        partes.append({"n": n, "titulo": "Parte %d" % n, "trabajo": d})   # una ruta absoluta: os.path.join(RAIZ, …) la deja tal cual
    return {"tema": "La Espiga (juguete)", "partes": partes}, base


def prueba_se17():
    import serie as SE
    uno = guion_de(["El horno de Marta abrió en Xela.", "Vendía pan en la puerta."], "¿Qué pasó cuando llegó el terremoto?")
    dos_bien = guion_de(["El terremoto llegó de madrugada.", "El horno quedó en pie."], "La Espiga siguió abierta.")
    dos_mal = guion_de(["La harina subió de precio.", "Nadie compraba."], "La Espiga siguió abierta.")
    S, _ = serie_de_juguete("se17-base", [uno, dos_bien])
    with callado():
        base, md = SE.revisar_completa(S)
    ok(not base, "SE17: una serie de dos partes cuyo puente la segunda abre ya no pasa: %s" % base)
    ok(any("terremoto" in ln for ln in md), "SE17: el markdown de la serie completa no trae la narración")
    S, _ = serie_de_juguete("se17-faltan", [uno, dos_bien, None])
    with callado():
        f = SE.revisar_completa(S)[0]
    anade("SE17-faltan-guiones", "SE17", base, f, "faltan los guiones de las partes 3")
    S, _ = serie_de_juguete("se17-puente", [uno, dos_mal])
    with callado():
        f = SE.revisar_completa(S)[0]
    anade("SE17-puente-sin-abrir", "SE17", base, f, "el puente de la parte 1")


def prueba_se18():
    import serie as SE
    g = leer(os.path.join(RAIZ, "sesiones", "_fixture_serie", "parte-1", "guion.json"))
    st = {"tipo": "historia", "paleta": "terracota", "musica": "terracota-1", "fecha": "2026-11-14",
          "serie": {"parte": 3, "de": 3, "paleta": "terracota", "musica": "terracota-1", "titulo": "El cierre",
                    "promesa": "¿Cómo cayó una panadería que llenó Xela de pan?"}}
    with callado():
        base = SE.revisar_parte(dict(g, responde_serie=len(g["escenas"])), st, None)
        sin = SE.revisar_parte({k: v for k, v in g.items() if k != "responde_serie"}, st, None)
        fuera = SE.revisar_parte(dict(g, responde_serie=1), st, None)
        no_ultima = SE.revisar_parte({k: v for k, v in g.items() if k != "responde_serie"}, dict(st, serie=dict(st["serie"], parte=2)), None)
    ok(not any(x.startswith("SE18 ") for x in base), "SE18: la última parte con responde_serie = %d (una escena suya) falla SE18" % len(g["escenas"]))
    anade("SE18-ultima-sin-responde", "SE18", base, sin)
    anade("SE18-responde-en-el-gancho", "SE18", base, fuera)
    ok(not any(x.startswith("SE18 ") for x in no_ultima), "SE18: lo pide a una parte que no es la última")


def prueba_se19():
    import serie as SE
    ok(SE.FOTO_PARTES_MAX == 2, "SE19: FOTO_PARTES_MAX = %s (la prueba y la guía dicen 2)" % SE.FOTO_PARTES_MAX)
    _, base = serie_de_juguete("se19", [guion_de(["Uno."], foto="ori-f01"), guion_de(["Dos."], foto="ori-f01"), None])
    t3 = os.path.join(base, "parte-3")
    antes = SE.fotos_repetidas(guion_de(["Tres."], foto="ori-f02"), 3, t3)
    ok(not antes, "SE19: una foto nueva en la parte 3 falla: %s" % antes)
    anade("SE19-foto-en-tres-partes", "SE19", antes, SE.fotos_repetidas(guion_de(["Tres."], foto="ori-f01"), 3, t3), "ori-f01")
    gancho = {"escenas": [{"tipo": "gancho", "visual_datos": {"foto": "ori-f01"}, "texto": "Tres."}]}
    anade("SE19-foto-del-gancho", "SE19", antes, SE.fotos_repetidas(gancho, 3, t3), "ori-f01")
    ok(not SE.fotos_repetidas(guion_de(["Dos."], foto="ori-f01"), 2, os.path.join(base, "parte-2")), "SE19: la segunda parte que usa una foto ya falla (van ≤ 2 partes)")


# ---------- /congreso: CG8, CG9 (el gate corre como en test.sh: preparar con la semilla → ley --check → guion --check) ----------
_CG = {}


def congreso(*args):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "congreso.py")] + list(args), cwd=RAIZ, capture_output=True, text=True)
    return r.returncode, [ln[6:] for ln in r.stdout.splitlines() if ln.startswith("FALLA ")], (r.stdout + r.stderr)[-400:]


def congreso_base():
    """El TRABAJO de la maqueta de /congreso (la Ley de Ciberseguridad) con su guion fijo → (carpeta, guion, fallas de partida)."""
    if not _CG:
        T = os.path.join(TMP, "congreso")
        rc, _, sal = congreso("preparar", "6347", "--semilla", "sesiones/_fixture_congreso", "--trabajo", T, "--paleta", "obsidiana", "--fixture")
        rc2, _, sal2 = congreso("ley", T, "--check")
        g = leer(os.path.join(RAIZ, "sesiones", "_fixture_congreso", "guion.json"))
        escribir(os.path.join(T, "guion.json"), g)
        rc3, f, sal3 = congreso("guion", T, "--check")
        _CG.update(T=T, g=g, f=f, ok=(rc, rc2, rc3) == (0, 0, 0), sal=(sal if rc else sal2 if rc2 else sal3))
    return _CG


def congreso_neg(nombre, codigo, cambio, contiene):
    B = congreso_base()
    if not ok(B["ok"], "%s: el guion fijo de la maqueta de /congreso ya no pasa sin mutar: %s" % (nombre, B["sal"])):
        return
    g = copy.deepcopy(B["g"])
    exec(cambio, {"g": g})
    if not ok(g != B["g"], "%s: la mutación no cambió nada: %s" % (nombre, cambio)):
        return
    escribir(os.path.join(B["T"], "guion.json"), g)
    rc, f, _ = congreso("guion", B["T"], "--check")
    escribir(os.path.join(B["T"], "guion.json"), B["g"])
    if anade(nombre, codigo, B["f"], f, contiene):
        ok(rc != 0, "%s: el gate dijo la falla pero salió 0" % nombre)


CONGRESO = [
    ("CG8-sin-pero-ni-por-eso", "CG8", "ninguna escena encadena con «pero / por eso»",
     'g["escenas"][4]["texto"] = g["escenas"][4]["texto"].replace("Pero la", "La"); g["escenas"][5]["texto"] = g["escenas"][5]["texto"].replace("Por eso, en", "En")',
     "van ≥ 2"),
    ("CG8-gancho-sin-congreso", "CG8", "el gancho no dice «Congreso», «diputados» ni «pleno»",
     'g["escenas"][0].update(texto="La urgencia de esta ley pasó por 2 votos en Guatemala.", linea="la urgencia de esta ley")', "el gancho no dice"),
    ("CG9-tres-escenas", "CG9", "3 escenas (van 4–8 más el cierre)", 'g["escenas"] = g["escenas"][:3]', "3 escenas"),
    ("CG9-cierre-con-resumen", "CG9", "un cierre con resumen (es una sola pantalla)", 'g["cierre"]["resumen"] = ["Una fiscalía nueva"]', "cierre.resumen"),
    ("CG9-cierre-con-mas-voz", "CG9", "cierre.texto con algo más que la frase final", 'g["cierre"]["texto"] = g["cierre"]["final"] + " Y eso cambia todo en el Congreso."',
     "cierre.texto = cierre.final"),
]


# ---------- /video-3d: C3D5, C3D7 ----------
_V3 = {}


def video3d_base():
    if not _V3:
        import video3d as V3
        fx = os.path.join(RAIZ, "sesiones", "_fixture_video3d")
        T = os.path.join(TMP, "video3d")
        os.makedirs(os.path.join(T, "base"))
        os.makedirs(os.path.join(T, "audio"))
        shutil.copy(os.path.join(fx, "datos.json"), os.path.join(T, "base", "datos.json"))
        g, st = leer(os.path.join(fx, "guion.json")), leer(os.path.join(fx, "video3d.json"))
        with callado():
            f, av, _ = V3.revisar_guion(copy.deepcopy(g), st, T)
        _V3.update(V3=V3, T=T, g=g, st=st, f=f, av=av)
    return _V3


def video3d_neg(nombre, codigo, cambio, contiene, donde="fallas"):
    B = video3d_base()
    if not ok(not B["f"], "%s: el guion de la maqueta de /video-3d ya no pasa sin mutar: %s" % (nombre, B["f"][:3])):
        return
    g = copy.deepcopy(B["g"])
    exec(cambio, {"g": g})
    with callado():
        f, av, _ = B["V3"].revisar_guion(g, B["st"], B["T"])
    if donde == "fallas":
        anade(nombre, codigo, B["f"], f, contiene)
    else:
        anade(nombre, codigo, B["av"], av, contiene, que="un aviso")


_LARGA = " Nadie en los pueblos del valle esperaba que la tierra se abriera de esa manera mientras todos dormían en sus casas de adobe."
VIDEO3D = [
    ("C3D5-pin-con-numero-sin-respaldo", "C3D5", "un pin cuyo texto lleva un número sin respaldo", 'g["escenas"][1]["marcas"][0]["sub"] = "98,765 habitantes"', "98,765", "fallas"),
    ("C3D5-cifra-sin-respaldo", "C3D5", "una cifra en pantalla sin respaldo", 'g["escenas"][1]["cifras"][0]["rotulo"] = "de magnitud entre 98,765"', "98,765", "fallas"),
    ("C3D7-diez-segundos-sin-nada", "C3D7", "≈ 10 s sin nada nuevo en pantalla (una escena que sigue hablando sin que entre nada)",
     'g["escenas"][1]["texto"] += %r' % _LARGA, "sin nada nuevo", "fallas"),
    ("C3D7-aviso-siete-segundos", "C3D7", "AVISO: ≈ 7 s sin nada nuevo (entre 6 y 9 s)",
     'g["escenas"][1].update(marcas=[], eventos=[], cifras=[]); g["escenas"][1]["camara"] = g["escenas"][1]["camara"][:1]', "sin nada nuevo", "avisos"),
]


def prueba_m3d7():
    """M3D7 ya tiene negativos en maqueta3d.NEGATIVOS (los corre ola1_video3d.py con `negativos()`): que no se pierdan."""
    import maqueta3d as M3
    suyos = [(n, c) for gate, n, c in M3.NEGATIVOS if gate == "M3D7"]
    ok(len(suyos) >= 3, "M3D7: maqueta3d.NEGATIVOS trae %d negativos de M3D7 (eran 3: sin pie, pie sin una fuente, sin «Sígueme»)" % len(suyos))
    base = M3.cargar_json(M3.FIXTURE)
    with callado():
        f0 = M3.revisar_m(json.loads(json.dumps(base)), ["9:16", "4:5"])[0]
    ok(not f0, "M3D7: la maqueta del motor ya no pasa sin mutar: %s" % f0[:3])
    for nombre, cambio in suyos:
        m = json.loads(json.dumps(base))
        cambio(m)
        with callado():
            f = M3.revisar_m(m, ["9:16", "4:5"])[0]
        anade("M3D7 «%s»" % nombre, "M3D7", f0, f)


PRUEBAS = [("SE17", "serie.revisar_completa: faltan guiones · el puente de una parte no lo abre la siguiente", prueba_se17),
           ("SE18", "serie.revisar_parte: la última parte sin responde_serie (o apuntando al gancho)", prueba_se18),
           ("SE19", "serie.fotos_repetidas: una foto que ya salió en 2 partes (también la del gancho)", prueba_se19)]
PRUEBAS += [(c[0], "%s → %s · %s" % (c[2], c[1], c[3]), (lambda c=c: congreso_neg(c[0], c[1], c[3], c[4]))) for c in CONGRESO]
PRUEBAS += [(c[0], "%s → %s · %s" % (c[2], c[1], c[3]), (lambda c=c: video3d_neg(c[0], c[1], c[3], c[4], c[5]))) for c in VIDEO3D]
PRUEBAS += [("M3D7", "maqueta3d.NEGATIVOS conserva los negativos de M3D7 y muerden", prueba_m3d7)]
SIN_NEGATIVO = [("CA10", "scripts/carrusel.js lo mide dentro de la página (tamaños y cajas de lo dibujado): hace falta Playwright; lo cubre `make carrusel-fixture` en positivo"),
                ("CA11", "igual que CA10 (un solo texto en el acento, medido en la página); su lint de templates/carrusel/ (sin hex ni https) corre en el mismo render")]


def main():
    global VERBOSO
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pruebas", nargs="*", help="nombres de pruebas o un prefijo («CG», «C3D7»); sin nombres, todas")
    ap.add_argument("--lista", action="store_true", help="los nombres de las pruebas y los gates que quedan sin negativo")
    ap.add_argument("-v", "--verboso", action="store_true", help="enseña lo que cada mutación añadió (+ = lo que se esperaba)")
    a = ap.parse_args()
    VERBOSO = a.verboso
    if a.lista:
        for n, que, _ in PRUEBAS:
            print("%-34s %s" % (n, que))
        for cod, por in SIN_NEGATIVO:
            print("%-34s sin negativo: %s" % ("(" + cod + ")", por))
        return 0
    nombres = [n for n, _, _ in PRUEBAS]
    pedidas = []
    for p in a.pruebas or nombres:
        suyas = [n for n in nombres if n == p] or [n for n in nombres if n.startswith(p)]
        if not suyas:
            print("no hay ninguna prueba «%s» (python3 scripts/pruebas/gates_sin_negativo.py --lista)" % p, file=sys.stderr)
            return 2
        pedidas += [n for n in suyas if n not in pedidas]
    por_nombre = {n: fn for n, _, fn in PRUEBAS}
    t0, malas = time.time(), 0
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
        shutil.rmtree(TMP, ignore_errors=True)
    for x in F:
        print("FALLA", x)
    print("[gates sin negativo] %d pruebas · %s (%.1f s)" % (len(pedidas), "ok" if not F else "%d con fallas" % malas, time.time() - t0))
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
