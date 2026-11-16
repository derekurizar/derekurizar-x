#!/usr/bin/env python3
"""Pruebas del resto de mejoras de video (2026-11-14), sin render, sin red, sin whisper y sin créditos:
  1. MV13 (un solo acento al frente): qué piezas llevan el acento y cuánto pesa (dato, bloque, marca), cuándo coinciden,
     qué falla (un dato con otro dato o con un bloque) y qué solo avisa, y las salidas del plano (`crema`, `limpia`); el
     borrador ya no lo incumple por construcción. Los negativos del gate sobre el plano congelado van en mesa_congelada.py.
  2. V11, la escucha: la caché por huella (una voz que no cambió no se vuelve a transcribir; `--de-nuevo`), los nombres
     propios como glosario de whisper (nunca cifras ni el texto de la escena) y el cotejo con Scribe antes de fallar (m161:
     «quetzales» → «que sales» baja a aviso; un número distinto se queda FALLA).
  3. Los cierres: `--opciones` prueba cada opción con el gate completo en una copia (m062) y la forma obligatoria de una
     parte de serie que no es la última (m079, m151); los tres workflows la piden y devuelven solo opciones elegibles.
  4. caption.md: el título corto para quien lo teclea (m215), sin tocar los bloques por plataforma.
Todo lo que escribe va a un directorio temporal. Exit 0 ok · 1 falla."""
import argparse
import contextlib
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
sys.path.insert(0, os.path.join(RAIZ, "scripts", "pruebas"))
import video as VD  # noqa: E402
import mesa as MS  # noqa: E402
import video_hf as VH  # noqa: E402
import mesa_congelada as MC  # noqa: E402

F = []
TMP = tempfile.mkdtemp(prefix="resto_video_")


def ok(cond, que):
    if not cond:
        F.append(que)
    return bool(cond)


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def correr(*args):
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", args[0])] + [str(x) for x in args[1:]], cwd=RAIZ, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def dicho(fn, *a, **k):
    """Lo que una función imprime y devuelve → (retorno, texto)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# ================= 1. MV13: un solo acento al frente =================
# qué piezas llevan el color de acento (lo mismo que el motor pinta con $acento), leído de sus datos
SI = [dict(tipo="cifra", valor="4,500", rotulo="panes"), dict(tipo="termino", texto="La Espiga"),
      dict(tipo="barra", barras=[dict(etiqueta="A", valor=1), dict(etiqueta="B", valor=2)]),
      dict(tipo="recorte", extracto="un solo fuego para todo", resalta="un solo fuego"), dict(tipo="documento", pagina="pl-p1"),
      dict(tipo="lista", items=[dict(texto="a"), dict(texto="b")], acento=0), dict(tipo="lista", items=[dict(texto="a"), dict(texto="b")], lazo=dict(dice="x")),
      dict(tipo="red", etiqueta="Según la acusación", nodos=[]), dict(tipo="red", nodos=[dict(nombre="X", clave="El Uno")])]
NO = [dict(tipo="foto", foto="f1"), dict(tipo="persona", persona="Marta"), dict(tipo="institucion", nombre="SIB"), dict(tipo="fecha", grande="1952"),
      dict(tipo="lugar", mapa="guatemala", depto="Petén"), dict(tipo="cita", texto="x", autor="y"), dict(tipo="termino", texto="Encaje", definicion="lo que guarda el banco"),
      dict(tipo="recorte", extracto="un solo fuego", titular="x"), dict(tipo="recorte", extracto="otra cosa", resalta="un solo fuego"), dict(tipo="documento", portada={}),
      dict(tipo="lista", items=[dict(texto="a"), dict(texto="b")]), dict(tipo="lista", items=[dict(texto="a")], acento=False), dict(tipo="red", nodos=[dict(nombre="X")]),
      dict(tipo="cifra", valor="4,500", crema=True), dict(tipo="termino", texto="La Espiga", crema=True),
      dict(tipo="barra", crema=True, barras=[dict(etiqueta="A", valor=1), dict(etiqueta="B", valor=2)])]
for g in SI:
    ok(MS.en_acento(g), "MV13: esta pieza lleva el acento y en_acento dice que no: %s" % g)
for g in NO:
    ok(MS.en_acento(g) == "", "MV13: esta pieza NO lleva el acento y en_acento dice «%s»: %s" % (MS.en_acento(g), g))
ok(MS.en_acento(dict(tipo="recorte", extracto="un solo fuego", resalta="un solo fuego", crema=True)) != "",
   "MV13: `crema` no quita el subrayado de un recorte (el motor no sabe dibujarlo sin acento): debe seguir contando")
ok(MS.CREMA_TIPOS == ("cifra", "termino", "barra"), "MV13: CREMA_TIPOS cambió (%s): revisa el CSS .cr de video_hf.py y la guía" % (MS.CREMA_TIPOS,))


# cuánto pesa cada acento, y qué pareja bloquea: un dato (cifra, barra) con otro dato o con un bloque; lo demás solo avisa
PESOS = {"dato": [SI[0], SI[2]], "bloque": [SI[1], SI[5], SI[7], SI[8]], "marca": [SI[3], SI[4], SI[6]]}
for peso, gs in PESOS.items():
    for g in gs:
        ok(MS.peso_acento(g) == peso, "MV13: el acento de %s pesa «%s» y peso_acento dice «%s»" % (g, peso, MS.peso_acento(g)))
ok(all(MS.peso_acento(g) == "" for g in NO), "MV13: una pieza sin acento no pesa")
BLOQUEA = {("dato", "dato"): True, ("dato", "bloque"): True, ("dato", "marca"): False, ("bloque", "bloque"): False, ("bloque", "marca"): False, ("marca", "marca"): False}
for (pa, pb), bloquea in BLOQUEA.items():
    for a_, b_ in ((PESOS[pa][0], PESOS[pb][-1]), (PESOS[pb][-1], PESOS[pa][0])):
        ok(MS.acento_compite(a_, b_) is bloquea, "MV13: %s con %s %s" % (pa, pb, "debe FALLAR" if bloquea else "solo avisa"))
ok(not MS.acento_compite(SI[0], NO[0]) and not MS.acento_compite(dict(SI[0], crema=True), SI[1]), "MV13: sin acento (o en crema) no hay competencia")


def pz(k, t, hasta, **g):
    return {"g": g, "t": t, "hasta": hasta, "k": k}


nota, cifra, foto = pz(0, 1.0, None, tipo="termino", texto="Nota"), pz(2, 5.0, None, tipo="cifra", valor="9"), pz(1, 3.0, None, tipo="foto", foto="f")
r = MS.acentos_a_la_vez([nota, foto, cifra], 20.0)
ok(len(r) == 1 and r[0][0] is cifra and r[0][1] == [nota], "MV13: nota y cifra al frente a la vez = una coincidencia (la que entra, con la que seguía): %s" % r)
ok(MS.acentos_a_la_vez([dict(nota, hasta=4.7), foto, cifra], 20.0) == [], "MV13: una nota ya replegada cuando entra la cifra no cuenta")
ok(MS.acentos_a_la_vez([dict(nota, hasta=5.02), cifra], 20.0) == [], "MV13: el corte del repliegue (± 0.05 s) no cuenta como coincidir")
ok(MS.acentos_a_la_vez([nota, foto], 20.0) == [] and MS.acentos_a_la_vez([cifra], 20.0) == [], "MV13: una sola pieza en acento nunca falla")
ok(MS.acentos_a_la_vez([pz(0, 1.0, None, tipo="termino", texto="Nota", crema=True), cifra], 20.0) == [], "MV13: la nota en crema no compite con la cifra")
tres = MS.acentos_a_la_vez([nota, cifra, pz(3, 8.0, None, tipo="barra", barras=[dict(etiqueta="A", valor=1)])], 20.0)
ok(len(tres) == 2 and len(tres[1][1]) == 2, "MV13: la tercera pieza en acento se reporta con las dos que seguían: %s" % tres)

# sobre el plano congelado (el mismo banco de mesa_congelada.py): el gate y sus tres salidas
B = MC.banco("V")


def plano_con(cambio, donde="fallas"):
    P, E = copy.deepcopy(B.P), copy.deepcopy(B.E)
    exec(cambio, MC.espacio(B, P, E))
    return [x for x in B.correr(P, E)[donde] if x.startswith("MV13 ")]


_NOTA = 'cambia("e6", ("foto",), dict(tipo="termino", texto="Un fuego")); '
ok(not [x for x in B.base["fallas"] if x.startswith("MV13")], "MV13: el plano curado ya no pasa: %s" % B.base["fallas"][:2])
f = plano_con(_NOTA)
ok(len(f) == 1 and "la cifra «4,500» entra" in f[0] and "la nota «Un fuego» (golpe 1) sigue al frente en acento" in f[0] and '"crema": true' in f[0],
   "MV13: nota + cifra al frente debe dar UNA falla que nombre las dos piezas y diga cómo se arregla: %s" % f)
ok(plano_con(_NOTA + 'golpe("e6", "termino")["crema"] = True') == [], "MV13: con `crema` en la nota ya no falla")
ok(plano_con(_NOTA + 'golpe("e6", "cifra")["crema"] = True') == [], "MV13: con `crema` en la cifra ya no falla")
ok(plano_con(_NOTA + 'golpe("e6", "cifra")["limpia"] = True') == [], "MV13: con `limpia` en la que entra, la nota se repliega y ya no falla")
ok(plano_con(_NOTA, "avisos") == [], "MV13: la nota con la cifra es FALLA, no además un aviso")
# lo que solo avisa (no bloquea): dos notas, o la cifra junto a la frase subrayada de un recorte
_DOS = _NOTA + 'cambia("e6", ("cifra",), dict(tipo="termino", texto="Cuatro mil"))'
ok(plano_con(_DOS) == [] and len(plano_con(_DOS, "avisos")) == 1 and "dos acentos a la vez" in plano_con(_DOS, "avisos")[0], "MV13: dos notas al frente avisan y no fallan: %s %s"
   % (plano_con(_DOS), plano_con(_DOS, "avisos")))
_SUB = 'cambia("e6", ("foto",), dict(tipo="recorte", medio="Zzz", fecha="1968", extracto="un solo fuego para todo el pan", resalta="un solo fuego"))'
ok(plano_con(_SUB) == [] and len(plano_con(_SUB, "avisos")) == 1 and "el subrayado del recorte" in plano_con(_SUB, "avisos")[0], "MV13: una cifra junto a un subrayado avisa y no falla")
ok(plano_con(_SUB.replace(', resalta="un solo fuego"', ""), "avisos") == [], "MV13: sin el subrayado ya no hay aviso")
f = plano_con('golpe("e6", "foto")["crema"] = True')
ok(len(f) == 1 and "`crema` solo vale en cifra, termino, barra" in f[0], "MV13: `crema` en una foto debe fallar (no cambia nada): %s" % f)
# la versión compacta (replegada) respeta `crema`, y la barra en crema no destaca ninguna
ok('class="cm osc cr"' in VH.compacta({}, dict(tipo="cifra", valor="9", rotulo="x", crema=True), {}, [])[2]
   and 'class="cm osc"' in VH.compacta({}, dict(tipo="cifra", valor="9", rotulo="x"), {}, [])[2], "MV13: la cifra replegada no lleva la clase de crema")
ok('class="cm"' in VH.compacta({}, dict(tipo="termino", texto="Nota", crema=True), {}, [])[2]
   and 'class="cm ac"' in VH.compacta({}, dict(tipo="termino", texto="Nota"), {}, [])[2], "MV13: la nota replegada en crema sigue en acento")
ok(all(x in VH.CSS for x in (".cifra.cr .v{color:$papel}", ".nota.cr{background:$papel}", ".cm.osc.cr .n{color:$papel}")), "MV13: falta el CSS de `crema` en video_hf.CSS")
# el borrador no lo incumple por construcción: en el gancho de texto cinético, la nota que acompaña a la barra va en crema
pal = [{"text": w, "start": 0.3 * i, "end": 0.3 * i + 0.25} for i, w in enumerate("El galón pasó de 26 a 46 quetzales en Guatemala.".split())]
S = {"tipo": "gancho", "palabras": pal, "T": {"pant": {"texto": "El galón casi se duplicó"}, "linea": [{"text": w} for w in "De Q26 a Q46".split()]},
     "V": {"tipo": "pareja", "a": {"etiqueta": "2020", "valor": 26}, "b": {"etiqueta": "2026", "valor": 46}}}
gs = VH.texto_pantalla(S, 0, lambda k0, n=2: " ".join(w["text"] for w in pal[k0:k0 + n]), {})
ok({g["tipo"] for g in gs} == {"termino", "barra"} and all(g.get("crema") for g in gs if g["tipo"] == "termino") and sum(1 for g in gs if MS.en_acento(g)) == 1,
   "MV13: el borrador del gancho (nota + barra) debe dejar UN solo acento: %s" % gs)
S2 = {"tipo": "golpe", "palabras": [{"text": w, "start": 0.3 * i, "end": 0.3 * i + 0.25} for i, w in enumerate("Nadie lo vio venir y solo quedó un horno encendido.".split())],
      "T": {"pant": {"texto": "Nadie lo vio"}, "linea": [{"text": w} for w in "solo quedó un horno".split()]}}
gs = VH.texto_pantalla(S2, 3, lambda k0, n=2: "Nadie lo", {})
ok(len(gs) == 2 and sum(1 for g in gs if MS.en_acento(g)) == 1 and gs[1].get("crema"), "MV13: el borrador de un golpe con su línea deja UN solo acento: %s" % gs)
guia = open(os.path.join(RAIZ, "referencias", "flujo-mesa.md"), encoding="utf-8").read()
fila = next((ln for ln in guia.splitlines() if ln.startswith("| MV13 |")), "")
ok(fila and "pendiente" not in fila and "MV13 (un solo acento a la vez)" not in guia and "### 5b. MV13" in guia, "MV13: referencias/flujo-mesa.md lo sigue dando por pendiente: %s" % fila)
ok("MV13" in open(os.path.join(RAIZ, "referencias", "roles", "video-realizador.md"), encoding="utf-8").read(), "MV13: la guía del realizador no lo nombra")
ok(not any(c == "MV13" for c, _ in MC.SIN_NEGATIVO) and sum(1 for m in MC.MUTACIONES if m[2] == "MV13") >= 3, "MV13: mesa_congelada.py lo sigue listando sin negativo")
ok("dato" in guia[guia.index("### 5b. MV13"):] and "mesa.acento_compite" in guia, "MV13: la guía no dice qué falla y qué solo avisa")

# ================= 2. V11: la escucha =================
# --- c) el cotejo con Scribe antes de fallar (m161) ---
SEG = [{"v": "Cobran ", "num": False}, {"v": "doscientos quetzales", "num": True}, {"v": " al mes en Xela.", "num": False}]
SCRIBE = "Cobran doscientos quetzales al mes en Xela."
f, av, _ = VD.comparar_escucha(SEG, "Cobran 200 que sales al mes en Xela", scribe=SCRIBE)
ok(f == [] and len(av) == 1 and "esperaba «quetzales», oyó «que sales»" in av[0] and "Scribe oyó lo esperado" in av[0],
   "V11/m161: «quetzales» → «que sales» con el número bien oído y Scribe de acuerdo debe ser AVISO: %s %s" % (f, av))
f, av, _ = VD.comparar_escucha(SEG, "Cobran 200 que sales al mes en Xela")
ok(len(f) == 1 and "quetzales" in f[0], "V11/m161: sin las palabras de Scribe sigue siendo FALLA (como antes): %s %s" % (f, av))
f, av, _ = VD.comparar_escucha(SEG, "Cobran 300 que sales al mes en Xela", scribe=SCRIBE)
ok(len(f) == 1 and "trescientos" in f[0], "V11/m161: si whisper difiere en el NÚMERO se queda FALLA aunque Scribe diga lo esperado: %s %s" % (f, av))
f, av, _ = VD.comparar_escucha(SEG, "Cobran 200 dólares al mes en Xela", scribe=SCRIBE)
ok(len(f) == 1 and "dolares" in f[0], "V11/m161: otra palabra que no suena parecido (dólares por quetzales) se queda FALLA: %s %s" % (f, av))
f, av, _ = VD.comparar_escucha(SEG, "Cobran 200 al mes en Xela", scribe=SCRIBE)
ok(len(f) == 1, "V11/m161: si whisper no oyó nada en lugar de la unidad (la voz pudo saltársela) se queda FALLA: %s %s" % (f, av))
f, av, _ = VD.comparar_escucha(SEG, "Cobran 200 que sales al mes en Xela", scribe="Cobran doscientos al mes en Xela.")
ok(len(f) == 1, "V11/m161: si Scribe NO trae la palabra esperada se queda FALLA: %s %s" % (f, av))
f, av, _ = VD.comparar_escucha(SEG, "Cobran 200 que sales que sales al mes en Xela", scribe=SCRIBE)
ok(len(f) == 1, "V11: un titubeo junto a la cifra sigue siendo FALLA aunque Scribe diga lo esperado: %s %s" % (f, av))
SEG2 = [{"v": "El ", "num": False}, {"v": "cuarenta y seis punto uno por ciento", "num": True}, {"v": " vive así.", "num": False}]
f, av, _ = VD.comparar_escucha(SEG2, "El 46,7 por ciento vive así", scribe="El cuarenta y seis punto uno por ciento vive así.")
ok(len(f) == 1, "V11/m161: un decimal mal dicho (46.1 → 46.7) es FALLA aunque Scribe, que alinea el prompt, diga lo esperado: %s %s" % (f, av))
for t, es in (("doscientos", True), ("mil", True), ("un", True), ("punto", True), ("ciento", True), ("46", True), ("quetzales", False), ("por", False),
              ("y", False), ("kilometros", False), ("xela", False)):
    ok(VD.es_numeral(t) is es, "V11: es_numeral(«%s») debe ser %s" % (t, es))
ok(VD.solo_palabra_junto_a_cifra(["quetzales"], ["que", "sales"]) and not VD.solo_palabra_junto_a_cifra(["quetzales"], [])
   and not VD.solo_palabra_junto_a_cifra(["doscientos", "quetzales"], ["trescientos", "que", "sales"])
   and not VD.solo_palabra_junto_a_cifra(["quetzales"], ["200"]) and not VD.solo_palabra_junto_a_cifra(["quetzales"], ["dolares"]),
   "V11/m161: solo_palabra_junto_a_cifra")

# --- b) los nombres propios como glosario de whisper (m071) ---
VOCES = ["Cobran mil quinientos quetzales al mes en Xela. Pero Zacapa no. La CICIG llegó en dos mil siete.",
         "Marta Pérez, la fundadora, abrió su panadería. Años después, el ron de Zacapa lo compró Diageo: Cada pan sale. El Banco de Guatemala dijo que no.",
         "En el siglo XIX, Otto Pérez Molina y Roxana Baldetti. ¿Sabías que el SAT y el IGSS existen? Trescientos Veinte no es un nombre."]
N = VD.nombres_propios(VOCES)
for x in ("Xela", "Zacapa", "CICIG", "Diageo", "Banco de Guatemala", "Otto Pérez Molina", "Roxana Baldetti", "SAT", "IGSS"):
    ok(x in N, "V11/m071: falta el nombre propio «%s» en %s" % (x, N))
for x in ("Cobran", "Pero", "La", "Años", "Cada", "En", "XIX", "Trescientos", "Veinte", "Marta"):
    ok(x not in N and not any(n.split()[0] == x for n in N), "V11/m071: «%s» abre oración o es un número: no es un nombre propio (%s)" % (x, N))
ok(not any(any(c.isdigit() for c in n) or any(VD.es_numeral(t) for t in VD.tokens_escucha(n)) for n in N), "V11/m071: el glosario trae un número: %s" % N)
LOC = {"escenas": [{"n": k + 1, "voz": v} for k, v in enumerate(VOCES)]}
PROMPT = VD.prompt_nombres(LOC)
ok(PROMPT.startswith("Xela, Zacapa") and PROMPT.endswith(".") and len(PROMPT) <= VD.PROMPT_NOMBRES_MAX + 2, "V11/m071: el glosario: %s" % PROMPT)
ok(not re.search(r"\d", PROMPT) and not any(x in PROMPT.lower() for x in ("quinientos", "quetzales", "siete", "cobran", "panadería", "fundadora")),
   "V11/m071: el glosario lleva cifras o texto de la escena (la escucha es sin el guion): %s" % PROMPT)
ok(VD.prompt_nombres({"escenas": [{"n": 1, "voz": "Hoy llueve mucho. Nadie sale."}]}) == "", "V11/m071: sin nombres propios no hay glosario")
ok(len(VD.prompt_nombres({"escenas": [{"n": 1, "voz": "Fue en " + ", en ".join("Lugar%s Largo" % chr(97 + i % 26) * 3 for i in range(80)) + "."}]})) <= VD.PROMPT_NOMBRES_MAX + 2,
   "V11/m071: el glosario no pasa de %d caracteres" % VD.PROMPT_NOMBRES_MAX)


# la bandera --prompt solo si este whisper-cli la tiene, y nunca con otra cosa que el glosario
@contextlib.contextmanager
def whisper_falso(acepta):
    """transcribir_whisper sin ffmpeg ni whisper: registra la orden y deja el .json que whisper-cli escribiría."""
    ordenes, real_run, real_ff, tenia, previo = [], VD.subprocess.run, VD.ff, hasattr(VD.whisper_acepta_prompt, "v"), getattr(VD.whisper_acepta_prompt, "v", None)

    def run(cmd, **k):
        ordenes.append(cmd)
        escribir(cmd[cmd.index("-of") + 1] + ".json", {"transcription": [{"text": " hola"}, {"text": " mundo"}]})
        return argparse.Namespace(returncode=0, stdout="", stderr="")
    VD.subprocess.run, VD.ff, VD.whisper_acepta_prompt.v = run, (lambda *a: None), acepta
    try:
        yield ordenes
    finally:
        VD.subprocess.run, VD.ff = real_run, real_ff
        if tenia:
            VD.whisper_acepta_prompt.v = previo
        else:
            del VD.whisper_acepta_prompt.v


with whisper_falso(True) as ordenes:
    oido, error = VD.transcribir_whisper("x.mp3", os.path.join(TMP, "w1"), "m.bin", "Xela, Zacapa.")
ok((oido or "").split() == ["hola", "mundo"] and error is None, "V11: transcribir_whisper debe devolver lo oído: %r %r" % (oido, error))
ok(len(ordenes) == 1 and ordenes[0][-2:] == ["--prompt", "Xela, Zacapa."] and ordenes[0][ordenes[0].index("-l") + 1] == "es", "V11/m071: la orden de whisper debe llevar --prompt con el glosario: %s" % ordenes)
with whisper_falso(False) as ordenes:
    VD.transcribir_whisper("x.mp3", os.path.join(TMP, "w2"), "m.bin", "Xela, Zacapa.")
ok("--prompt" not in ordenes[0], "V11/m071: un whisper-cli sin --prompt no debe recibirla: %s" % ordenes)
with whisper_falso(True) as ordenes:
    VD.transcribir_whisper("x.mp3", os.path.join(TMP, "w3"), "m.bin", "")
ok("--prompt" not in ordenes[0], "V11/m071: sin glosario no se pasa --prompt")

# --- a) la caché por huella ---
T = os.path.join(TMP, "escucha")
E1 = {"n": 1, "voz": "Cobran doscientos quetzales al mes en Xela.", "segmentos": SEG}
E2 = {"n": 2, "voz": "En mil novecientos setenta y seis tembló en Zacapa.",
      "segmentos": [{"v": "En ", "num": False}, {"v": "mil novecientos setenta y seis", "num": True}, {"v": " tembló en Zacapa.", "num": False}]}
escribir(os.path.join(T, "locucion.json"), {"escenas": [E1, E2]})
os.makedirs(os.path.join(T, "audio"))
for n, e in ((1, E1), (2, E2)):
    with open(os.path.join(T, "audio", "voz_%d.mp3" % n), "wb") as fh:
        fh.write(b"voz %d" % n)
    escribir(os.path.join(T, "audio", "palabras_%d.json" % n), [{"text": w, "start": 0.3 * i, "end": 0.3 * i + 0.2} for i, w in enumerate(e["voz"].split())])
OIDO = {"voz_1.mp3": "Cobran 200 que sales al mes en Xela.", "voz_2.mp3": "En 1977 tembló en Zacapa."}   # la 2: la cifra mal dicha
llamadas = []


def transcribe(voz, base, modelo, prompt=""):
    llamadas.append((os.path.basename(voz), prompt))
    return OIDO[os.path.basename(voz)], None


def escuchar(**k):
    del llamadas[:]
    a = argparse.Namespace(trabajo=T, modelo=os.path.join(TMP, "modelo.bin"), solo=k.get("solo"), de_nuevo=k.get("de_nuevo", False))
    listo, tr = VD.whisper_listo, VD.transcribir_whisper
    VD.whisper_listo, VD.transcribir_whisper = (lambda m: True), transcribe
    try:
        rc, out = dicho(VD.cmd_escuchar, a)
    finally:
        VD.whisper_listo, VD.transcribir_whisper = listo, tr
    return rc, out, [x[0] for x in llamadas]


rc, out, quien = escuchar()
ok(rc == 1 and quien == ["voz_1.mp3", "voz_2.mp3"] and "E2  FALLA V11" in out and "E1  ok" in out, "caché: la primera escucha transcribe todo y falla por la cifra de E2: rc=%s %s\n%s" % (rc, quien, out))
ok(llamadas and all(p == "Xela, Zacapa." for _, p in llamadas), "caché/m071: whisper debe recibir el glosario de nombres de la locución: %s" % llamadas)
inf = leer(os.path.join(T, "audio", "escucha.json"))
ok(all(inf["escenas"][k].get("huella") and inf["escenas"][k].get("huella_audio") for k in ("1", "2")) and inf.get("prompt") == "Xela, Zacapa.", "caché: escucha.json no guarda las huellas: %s" % inf)
rc, out, quien = escuchar()
ok(rc == 1 and quien == [] and "E2  FALLA V11" in out and out.count("sin volver a escuchar") >= 2, "caché: sin cambios no se vuelve a correr whisper y el resultado (ok y FALLA) se repite: rc=%s %s\n%s" % (rc, quien, out))
ok(leer(os.path.join(T, "audio", "escucha.json"))["escenas"] == inf["escenas"], "caché: reusar no debe cambiar escucha.json")
rc, out, quien = escuchar(de_nuevo=True)
ok(quien == ["voz_1.mp3", "voz_2.mp3"], "caché: --de-nuevo vuelve a escuchar todo: %s" % quien)
with open(os.path.join(T, "audio", "voz_2.mp3"), "wb") as fh:   # la retoma de E2: otra voz, ahora bien dicha
    fh.write(b"voz 2 retoma")
OIDO["voz_2.mp3"] = "En 1976 tembló en Zacapa."
rc, out, quien = escuchar()
ok(rc == 0 and quien == ["voz_2.mp3"] and "E2  ok" in out, "caché: tras rehacer la voz de E2 solo se escucha E2 (y ya pasa): rc=%s %s\n%s" % (rc, quien, out))
# cambia el texto esperado y la voz es la misma: no se corre whisper, pero se vuelve a cotejar lo ya oído
loc = leer(os.path.join(T, "locucion.json"))
loc["escenas"][1]["segmentos"][1]["v"] = "mil novecientos setenta y siete"
loc["escenas"][1]["voz"] = "En mil novecientos setenta y siete tembló en Zacapa."
escribir(os.path.join(T, "locucion.json"), loc)
rc, out, quien = escuchar()
ok(rc == 1 and quien == [] and "E2  FALLA V11" in out and "se cotejó lo ya oído" in out, "caché: con otro texto esperado y la misma voz se coteja lo ya oído sin whisper (y falla): rc=%s %s\n%s" % (rc, quien, out))
# otro modelo: lo oído ya no vale
h1 = VD.huellas_escucha(os.path.join(T, "audio", "voz_1.mp3"), "a.bin", E1, "x")
ok(h1 != VD.huellas_escucha(os.path.join(T, "audio", "voz_1.mp3"), "b.bin", E1, "x") and h1[0] == VD.huellas_escucha(os.path.join(T, "audio", "voz_1.mp3"), "a.bin", E2, "x")[0]
   and h1[1] != VD.huellas_escucha(os.path.join(T, "audio", "voz_1.mp3"), "a.bin", E1, "y")[1], "caché: la huella depende del mp3, del modelo, del texto esperado y de Scribe")
# sin whisper: avisa y sale 0, como siempre
rc, out = dicho(VD.cmd_escuchar, argparse.Namespace(trabajo=T, modelo=os.path.join(TMP, "no-existe.bin"), solo=None, de_nuevo=False))
ok(rc == 0 and "AVISO V11" in out, "V11: sin modelo la escucha avisa y sigue: rc=%s %s" % (rc, out))

# ================= 3. los cierres =================
ok(VD.forma_obligatoria({"serie": {"parte": 2, "de": 5, "siguiente": {"titulo": "La caída"}}})[0] == "puente"
   and "SE6 la parte 2 de 5" in VD.forma_obligatoria({"serie": {"parte": 2, "de": 5}})[1], "cierres: una parte que no es la última obliga «puente» (SE6)")
ok(VD.forma_obligatoria({"serie": {"parte": 5, "de": 5}}) == (None, "") and VD.forma_obligatoria({"serie": "departamentos"}) == (None, "") and VD.forma_obligatoria({}) == (None, ""),
   "cierres: la última parte, /departamento y un video suelto no obligan una forma")
ok(VD.gates_de({"tipo": "historia"}) == (os.path.join(RAIZ, "scripts", "historia.py"), ("narracion", "guion"))
   and VD.gates_de({"tipo": "explica"})[0].endswith("explica.py") and VD.gates_de({})[0].endswith("video.py") and VD.gates_de({"tipo": "sabias"})[1] == ("guion",),
   "cierres: el gate completo de cada flujo")
# probar_cierres: cada opción puesta en una COPIA junto al TRABAJO (el original no se toca) con el gate que se le pase
TC = os.path.join(TMP, "serie-x", "parte-2")
G0 = {"escenas": [{"tipo": "gancho", "texto": "Uno."}], "narracion": [{"acto": 3, "texto": "Uno. Así quedó todo. Y nadie volvió."}],
      "cierre": {"texto": "Así quedó todo. Y nadie volvió.", "final": "Y nadie volvió.", "tipo": "remate", "forma": "consecuencia", "consecuencia": {"quien": "nadie", "verbo": "volvió"}}}
escribir(os.path.join(TC, "guion.json"), G0)
escribir(os.path.join(TC, "video.json"), {"tipo": "historia", "slug": "x"})
escribir(os.path.join(TC, "audio", "voz_1.json"), {})
vistos = []


def gates_falsos(copia, script, cmds):
    g = leer(os.path.join(copia, "guion.json"))
    vistos.append({"copia": copia, "script": os.path.basename(script), "cmds": cmds, "final": g["cierre"]["final"], "narr": g["narracion"][0]["texto"],
                   "audio": os.path.isdir(os.path.join(copia, "audio")), "consecuencia": "consecuencia" in g["cierre"]})
    return ["guion · H16 al acto 3 le queda 1 conector causal"] if "malo" in g["cierre"]["final"] else []


CANDS = [dict(G0["cierre"], id="c1"),
         {"id": "c2", "texto": "Así quedó todo. ¿Quién abriría el horno malo?", "final": "¿Quién abriría el horno malo?", "tipo": "pregunta", "forma": "puente"},
         {"id": "c3", "texto": "Así quedó todo. ¿Quién abriría el horno?", "final": "¿Quién abriría el horno?", "tipo": "pregunta", "forma": "puente"}]
res = VD.probar_cierres(TC, CANDS, {"tipo": "historia"}, gates=gates_falsos)
ok(res == {"c1": [], "c2": ["guion · H16 al acto 3 le queda 1 conector causal"], "c3": []}, "cierres: probar_cierres devuelve las fallas del gate por opción: %s" % res)
ok([v["final"] for v in vistos] == [c["final"] for c in CANDS] and vistos[2]["narr"].endswith("Así quedó todo. ¿Quién abriría el horno?") and not vistos[2]["consecuencia"],
   "cierres: cada opción se prueba PUESTA en el guion (cierre y narración de corrido): %s" % vistos)
ok(all(os.path.dirname(v["copia"]) == os.path.dirname(TC) and not v["audio"] and v["script"] == "historia.py" and v["cmds"] == ("narracion", "guion") for v in vistos),
   "cierres: la copia va junto al TRABAJO (una parte de serie se mide contra sus hermanas), sin audio, con el gate del flujo: %s" % vistos)
ok(leer(os.path.join(TC, "guion.json")) == G0 and sorted(os.listdir(os.path.dirname(TC))) == ["parte-2"], "cierres: la prueba tocó el TRABAJO o dejó la copia: %s" % os.listdir(os.path.dirname(TC)))
g_sin = dict(G0, narracion=[{"acto": 3, "texto": "Otra narración que no trae el cierre."}])
escribir(os.path.join(TC, "guion.json"), g_sin)
res = VD.probar_cierres(TC, CANDS[1:2], {"tipo": "historia"}, gates=gates_falsos)
ok(res["c2"] and "no está literal en guion.narracion" in res["c2"][0], "cierres: un cierre que no se puede poner (la narración no trae el de antes) es una opción rechazada: %s" % res)

# la maqueta de /historia: una ✓ de solo F1–F9 (--check) que el gate completo rechaza (--opciones) · m062
TH = os.path.join(TMP, "historia")
rc, out = correr("historia.py", "preparar", "La Espiga (maqueta)", "--slug", "la-espiga-maqueta", "--trabajo", TH, "--fixture")
rc = rc or correr("historia.py", "consolidar", TH)[0] or correr("historia.py", "ganchos", TH, "--usar")[0] or correr("historia.py", "guion", TH, "--check")[0]
if ok(rc == 0, "cierres: la maqueta de /historia no se arma: %s" % out[-400:]):
    g = leer(os.path.join(TH, "guion.json"))
    c1 = dict({k: g["cierre"][k] for k in ("texto", "final", "tipo", "forma", "consecuencia") if k in g["cierre"]}, id="c1")
    c2 = dict(c1, id="c2", texto=c1["texto"].replace("25 sucursales", "99 sucursales").replace(c1["final"], "En Xela, sus trabajadores todavía encienden esos hornos de La Espiga."),
              final="En Xela, sus trabajadores todavía encienden esos hornos de La Espiga.")
    c3 = dict(c1, id="c3", texto=c1["texto"].replace(c1["final"], "En Xela, sus trabajadores hoy encienden el pan de La Espiga."), final="En Xela, sus trabajadores hoy encienden el pan de La Espiga.")
    ok("99 sucursales" in c2["texto"], "cierres: la maqueta cambió (el cierre ya no dice «25 sucursales»): ajusta esta prueba: %s" % c1["texto"])
    escribir(os.path.join(TH, "cierres.json"), {"candidatos": [c1, c2, c3]})
    antes = open(os.path.join(TH, "guion.json"), encoding="utf-8").read()
    rc, out = correr("historia.py", "cierres", TH, "--check")
    linea = lambda o, cid: next((ln for ln in o.splitlines() if re.match(r"\d+\. %s\b" % cid, ln)), "")
    ok(linea(out, "c2").endswith("✓"), "cierres/m062: con --check (solo F1–F9) la opción c2 sale con ✓ (ese era el problema): %s" % out[-600:])
    rc, out = correr("historia.py", "cierres", TH, "--opciones")
    ok("✗ guion · V2" in linea(out, "c2") and "99" in linea(out, "c2"), "cierres/m062: --opciones debe probar c2 con el gate completo y enseñar su primera FALLA al lado: %s" % linea(out, "c2"))
    ok(linea(out, "c1").endswith("✓") and linea(out, "c3").endswith("✓"), "cierres: las opciones que pasan el gate completo llevan ✓: %s" % out[-900:])
    ret = next((json.loads(ln[len("RETORNO "):]) for ln in out.splitlines() if ln.startswith("RETORNO ")), {})
    ok(ret.get("elegibles") == ["c1", "c3"] and [x["id"] for x in ret.get("rechazadas") or []] == ["c2"] and ret.get("forma_obligatoria") is None, "cierres: RETORNO de --opciones: %s" % ret)
    ok("AVISO solo 2 opción(es) de cierre elegible(s)" in out, "cierres: con menos de 3 elegibles, --opciones lo avisa: %s" % out[-500:])
    ok(open(os.path.join(TH, "guion.json"), encoding="utf-8").read() == antes and not [x for x in os.listdir(TMP) if x.startswith("_cierres-")],
       "cierres: --opciones cambió guion.json o dejó su copia: %s" % os.listdir(TMP))
    # --usar de la rechazada: el gate la sigue rechazando y el guion queda como estaba (lo de siempre)
    rc, out = correr("historia.py", "cierres", TH, "--usar", "c2")
    ok(rc != 0 and leer(os.path.join(TH, "guion.json"))["cierre"]["final"] == c1["final"], "cierres: --usar de una opción que el gate rechaza deja el guion como estaba: rc=%s %s" % (rc, out[-300:]))
    rc, out = correr("historia.py", "cierres", TH, "--usar", "c3")
    ok(rc == 0 and leer(os.path.join(TH, "guion.json"))["cierre"]["final"] == c3["final"], "cierres: --usar de una opción elegible sí entra: rc=%s %s" % (rc, out[-300:]))
    # la forma obligatoria (m079, m151): en una parte de serie que no es la última, una opción que no es «puente» falla ya en --check
    st = leer(os.path.join(TH, "video.json"))
    escribir(os.path.join(TH, "video.json"), dict(st, serie={"parte": 1, "de": 3, "siguiente": {"n": 2, "titulo": "El terremoto"}}))
    escribir(os.path.join(TH, "cierres.json"), {"candidatos": [c1, dict(c3, id="c2", tipo="pregunta", forma="puente", texto=c1["texto"].replace(c1["final"], "¿Qué quedó de La Espiga en Xela?"),
                                                                 final="¿Qué quedó de La Espiga en Xela?")]})
    rc, out = correr("video.py", "cierres", TH, "--check")
    se6 = [ln for ln in out.splitlines() if ln.startswith("FALLA c") and "SE6 la parte 1 de 3 cierra con forma «puente»" in ln]
    ok(rc != 0 and len(se6) == 1 and se6[0].startswith("FALLA c1:") and "«legado» no lo es" in se6[0], "cierres/m151: un cierre «legado» en la parte 1 de 3 debe fallar con SE6 y el puente no: %s" % out[-700:])
    ok(linea(out, "c2").endswith("✓") or "c2:" not in "\n".join(se6), "cierres/m151: el puente no debe llevar la falla de forma")

# los tres workflows: piden la forma obligatoria, prueban con --opciones y devuelven solo opciones elegibles
for wf, script in (("historia.js", "historia.py"), ("explica.js", "explica.py"), ("video.js", "video.py")):
    js = open(os.path.join(RAIZ, ".claude", "workflows", wf), encoding="utf-8").read()
    bloque = js[js.index("phase('Cierres')"):]
    bloque = bloque[:bloque.index("\n// ── ", 10) if "\n// ── " in bloque[10:] else len(bloque)]
    ok("scripts/%s cierres ${trabajo} --opciones" % script in bloque and "elegibles[]" in bloque, "%s: la fase Cierres no manda a probar con `cierres --opciones`" % wf)
    ok("candidatos: eleg(CIERRES)" in bloque and "CIERRES_MIN" in bloque and "vueltaCierres < 1" in bloque, "%s: la fase Cierres no descarta las no elegibles (o no las manda a rehacer una vez)" % wf)
    ok(re.search(r"required: \['archivo', 'gate', 'fallas', 'candidatos', 'elegibles'\]", js), "%s: S.cierres no exige `elegibles`" % wf)
    if wf != "video.js":
        ok("const CIERRE_FORMA = PARTE && PARTE.de && PARTE.parte < PARTE.de ? 'puente' : null" in bloque and "FORMA OBLIGATORIA" in bloque,
           "%s: la fase Cierres no pasa la forma obligatoria de una parte de serie (SE6)" % wf)
ok(VD.CIERRES_ELEGIBLES_MIN == 3, "cierres: CIERRES_ELEGIBLES_MIN cambió: es el CIERRES_MIN de los tres workflows")

# ================= 4. caption.md: el título para teclear (m215) =================
PROHIBIDOS = "«»“”\"'–—·…#*"
CASOS = [
    ({"shorts": "MAQUETA · La panadería que llegó a 25 sucursales #Shorts\nHistoria de ejemplo.", "tiktok": "MAQUETA · La Espiga: de un horno de leña a 25 sucursales. Historia."},
     None, "MAQUETA, La panadería que llegó a 25 sucursales", None),
    ({"shorts": "Serie · Parte 2 de 5: «El Uno» y la red que cobraba Q25 millones en la aduana (2/5) #Shorts", "tiktok": "Serie · Parte 2 de 5: La Línea. ¿Quién era «El Uno»? – la pregunta."},
     None, "Serie, Parte 2 de 5: La Línea", None),
    ({"tiktok": "Huehuetenango: 7 de cada 10 viven en pobreza. Para alguien de Huehuetenango.", "shorts": "El departamento con más pobreza… ¿sabes cuál es? #Shorts"},
     ["Huehuetenango", "Huehue"], "Huehuetenango: 7 de cada 10 viven en pobreza", True),
    ({"tiktok": "São Paulo façade — café ☕ “único”"}, None, "Sao Paulo facade, café único", None),
    ({"shorts": "El \"Uno\" y *la red* de «La Línea» #Shorts"}, None, "El Uno y la red de La Línea", None),
    ({"shorts": "Guatemala: 1,911 casos de niñas embarazadas y solo 102 sentencias #Shorts"}, None, "Guatemala: 1,911 casos de niñas embarazadas", None),
]
for cap, clave, espera, con in CASOS:
    t, c = VD.titulo_para_teclear(cap, clave)
    ok((t, c) == (espera, con), "caption: título para teclear de %s: llegó %r (%s), va %r (%s)" % (list(cap.values())[0][:40], t, c, espera, con))
t, c = VD.titulo_para_teclear({"tiktok": "¿Sabías que en Guatemala el 46.1 % de los niños menores de 5 años sufre desnutrición crónica según la ENSMI?"}, "desnutrición")
ok(len(t) <= VD.TECLEAR_MAX and c is False and "¿" not in t and not t.endswith((" de", " 5", " los")), "caption: una oración larga se recorta sin palabra a medias ni cifra colgando, y dice que perdió la clave: %r %s" % (t, c))
ok(VD.titulo_para_teclear({}, None) == ("", None) and VD.titulo_para_teclear({"tiktok": "#Shorts"}, None)[0] == "", "caption: sin caption no hay título")
for f in sorted(x for x in os.listdir(os.path.join(RAIZ, "sesiones")) if x.startswith("_fixture")):
    for gj in (os.path.join(RAIZ, "sesiones", f, "guion.json"), os.path.join(RAIZ, "sesiones", f, "parte-1", "guion.json")):
        if not os.path.exists(gj) or not isinstance(leer(gj).get("caption"), dict):
            continue
        t, _ = VD.titulo_para_teclear(leer(gj)["caption"], leer(gj).get("palabra_clave"))
        ok(0 < len(t) <= VD.TECLEAR_MAX and not any(ch in PROHIBIDOS for ch in t) and all(ord(ch) < 128 or ch in VD.TECLEAR_ESPANOL for ch in t) and t == t.strip(" ,;:-."),
           "caption: el título para teclear de %s no cumple (≤ %d, sin signos difíciles): %r" % (os.path.relpath(gj, RAIZ), VD.TECLEAR_MAX, t))
ok(VD.TECLEAR_MAX == 60, "caption: el tope del título para teclear es 60 (m215)")
# caption.md: el bloque va arriba de todo, y las secciones por plataforma quedan como estaban
CAP = {"tiktok": "Huehuetenango: 7 de cada 10 viven en pobreza. «Para alguien de Huehuetenango».\n#Guatemala", "instagram": "Huehuetenango en 5 cifras – guárdalo.",
       "facebook": "Huehuetenango frente al país.", "shorts": "Huehuetenango: el departamento con más pobreza y menos violencia de Guatemala (7/22) #Shorts\nPerfil."}
nuevo, viejo = os.path.join(TMP, "caption.md"), os.path.join(TMP, "caption_sin.md")
VD.escribir_caption(nuevo, CAP, "TikTok @x", 95.0, ["Huehuetenango", "Huehue"])
txt = open(nuevo, encoding="utf-8").read()
ls = txt.splitlines()
ok(ls[0] == "# Texto para publicar" and ls[2].startswith("**Si lo vas a teclear**") and ls[3] == "```" and ls[5] == "```", "caption.md: el bloque «Si lo vas a teclear» va arriba de todo:\n%s" % "\n".join(ls[:8]))
ok(ls[4] == "Huehuetenango: 7 de cada 10 viven en pobreza" and "Tiene %d caracteres (máximo 60)" % len(ls[4]) in ls[2], "caption.md: el título corto: %r" % ls[4])
ok(ls[6] == "Palabra clave (que no falte al teclear): **Huehuetenango**", "caption.md: la palabra clave del guion: %r" % ls[6])
ok(txt.index("**Si lo vas a teclear**") < txt.index("Un solo video para las cuatro apps") < txt.index("## TikTok"), "caption.md: el orden (teclear → cómo publicar → las apps)")
# lo que leen agenda.py y metricas.py (las secciones «## <app>» con su bloque) no cambia: el mismo patrón que agenda.caption_de
bloques = {m.group(1): re.search(r"```\n(.*?)\n```", m.group(2), re.S).group(1) for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", txt, re.S | re.M)}
ok([k.split()[0] for k in bloques] == ["TikTok", "Instagram", "Facebook", "YouTube"], "caption.md: las secciones por plataforma: %s" % list(bloques))
ok(bloques["TikTok"] == CAP["tiktok"] and bloques["Instagram Reels (y feed con video_4x5.mp4)"] == CAP["instagram"] and bloques["YouTube Shorts"] == CAP["shorts"],
   "caption.md: los bloques por plataforma deben quedar tal cual el caption del guion: %s" % bloques)
# sin los captions no hay bloque y lo demás es idéntico a como era antes (lo de abajo no cambió)
VD.escribir_caption(viejo, CAP, "TikTok @x", 95.0)
sin = open(viejo, encoding="utf-8").read()
ok("Palabra clave" not in sin and "**Si lo vas a teclear**" in sin, "caption.md: sin palabra clave no sale su línea (y el título sí)")
ok(txt[txt.index("Un solo video para las cuatro apps"):] == sin[sin.index("Un solo video para las cuatro apps"):], "caption.md: el resto del archivo no depende de la palabra clave")
VD.escribir_caption(viejo, {"tiktok": "#x"}, "TikTok @x", 95.0)
ok("**Si lo vas a teclear**" not in open(viejo, encoding="utf-8").read(), "caption.md: sin título posible no sale el bloque")
VD.escribir_caption(viejo, {"tiktok": "La pobreza del altiplano en 5 cifras.", "shorts": "El altiplano en 5 cifras #Shorts"}, "TikTok @x", 95.0, "Huehuetenango")
ok("el título corto no la trae: escríbela también" in open(viejo, encoding="utf-8").read(), "caption.md: si el título corto no trae la palabra clave, lo dice")

for d in MC._TMP:
    shutil.rmtree(d, ignore_errors=True)
shutil.rmtree(TMP, ignore_errors=True)
for x in F:
    print("FALLA", x)
print("resto de video (MV13, escucha V11, cierres, caption): %s" % ("ok" if not F else "%d falla(s)" % len(F)))
sys.exit(1 if F else 0)
