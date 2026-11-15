#!/usr/bin/env python3
"""mesa.py — el núcleo de la «mesa de archivo»: lo que comparten el 16:9 de /youtube-long (scripts/youtube_hf.py) y el
vertical de los demás videos (scripts/video_hf.py). No tiene CLI.

Dinamismo es que ENTRE en pantalla lo que la voz nombra (usuario, 2026-11-13): cada pieza cae sobre una mesa cuando la voz
la dice y, una vez puesta, se queda quieta. La cámara no se mueve. Aquí viven el plano (golpes con `dice` → segundos y
mesas), los gates sobre los datos (nunca sobre píxeles), la clase Mesa (clips y línea de tiempo de una composición de
HyperFrames) y los recursos comunes (mapas, páginas de documento, colores, enlaces).

La MAQUETA 3D es la única excepción a la cámara quieta: una mesa puede llevar `maqueta` (un render 3D de la situación,
scripts/maqueta3d.py en modo pieza) que entra como un tablero; aquí viven sus tiempos (`maqueta_tiempos`), su maqueta.json
(`maqueta_json`), sus gates YT20–YT24 (`revisar_maqueta`, `revisar_maquetas`) y su render con caché (`grabar_maquetas`).

Cada formato pone lo suyo: tamaños, colocación, dibujo de cada pieza y comandos. Las reglas que cambian por formato
llegan en ctx["reglas"] ({nombre de constante: valor}); lo que el 16:9 saca de la serie (elenco, respaldo, hechos) puede
llegar ya resuelto en ctx["elenco"], ctx["respaldo"], ctx["hechos"] y ctx["hechos_de"].
"""
import glob
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD   # noqa: E402
from versiones import HF, HF_VERSION, GSAP_JS   # noqa: E402,F401  (las versiones fijadas viven en scripts/versiones.py, y solo ahí)

FPS = 30
# Lo que de verdad pasa al leer los datos de un gate: el archivo no está (OSError), no es JSON (ValueError) o es JSON con otra
# forma (falta una clave, llega una lista donde iba un objeto). Se atrapa SOLO eso y siempre con `aviso_datos`: un gate sin
# datos no se calla. Un error de programación (NameError, ImportError…) no se atrapa: revienta a la vista.
DATOS_ILEGIBLES = (OSError, ValueError, LookupError, TypeError, AttributeError)
CARPETAS_NOTAS = tuple(os.path.join(RAIZ, "sesiones", "_descargas", d) for d in ("historia", "congreso"))   # `historia.py leer` y `congreso.py leer`
RENDER_LIMITE_BASE_S = 600   # lo fijo de un render de HyperFrames: bajar el paquete la primera vez, arrancar Chrome, codificar
RENDER_LIMITE_POR_S = 20     # y por segundo de video: con un proceso va a ≈ 1.6× la duración (medido); a 20× está colgado
LEAD = 0.30            # la pieza empieza a caer 0.3 s antes de su palabra y aterriza en ella
ENTRA = 0.5
VISIBLES = 3           # YT18: con 3 piezas nuevas encima, la de abajo se atenúa
MESA_S = (4.0, 45.0)   # YT18: lo que dura una mesa
MESA_PIEZAS = 12       # YT18
HUECO_MAX_S = 6.0      # YT14: ningún tramo de voz de más de esto sin un golpe
HUECO_TABLERO_S = None  # el hueco que se tolera dentro de un tablero (None = el mismo); el vertical pone el suyo
TABLERO_SOLO = False    # el vertical: un tablero va solo en su mesa y sus oraciones no piden pieza
ENTRE_GOLPES_S = 0.3   # YT18: dos piezas no entran a menos de esto
PIEZA_NUEVA_MIN = 0.5  # YT17: fracción de oraciones con pieza nueva
ARCHIVO_MIN = 0.35     # YT17: fracción de piezas que son archivo real (aviso bajo 0.5)
TIPOS_MIN = 4          # YT17: tipos distintos por capítulo
TEXTO_SEGUIDOS = 2     # YT17: rótulos de solo texto seguidos
FOTO_USOS_MAX = 2      # YT15
FOTO_SEPARACION_S = 180
TIPOS = ("foto", "recorte", "documento", "persona", "institucion", "lugar", "fecha", "cifra", "termino", "cita", "lista")
ARCHIVO = ("foto", "recorte", "documento", "lugar")   # archivo real (más la persona con retrato y los tableros)
SOLO_TEXTO = ("termino", "lista")
TABLERO = ("explica", "tarjeta")
PROPIAS = ("capitulo", "cierre")
EVENTOS_TABLERO = ("paso", "foco", "cifra", "nodo", "entra", "golpe_arriba", "acto", "nota", "lienzo")
INSTITUCION = re.compile(r"\b(banco|junta|superintendencia|ministerio|fondo|tribunal|juzgado|corte|sala|congreso|fiscalia|comision|grupo|bolsa|sociedad|empresa)\b")
JUDICIAL = re.compile(r"\b(audiencia|capturad|detenid|procesad|ligad[oa]s? a proceso|esposad|primera declaraci[oó]n|sindicad|acusad|imputad)", re.I)
EN_PALABRAS = dict({w: str(i) for i, w in enumerate("cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete "
                                                     "dieciocho diecinueve veinte".split())},
                   un="1", una="1", treinta="30", cuarenta="40", cincuenta="50", sesenta="60", setenta="70", ochenta="80", noventa="90", cien="100", mil="1000",
                   primer="1", primero="1", primera="1", segundo="2", segunda="2", tercer="3", tercero="3", tercera="3", cuarto="4", cuarta="4", quinto="5",
                   quinta="5", sexto="6", septimo="7", octavo="8", noveno="9", decimo="10", doble="2", triple="3", mitad="2")
# La MAQUETA 3D (usuario, 2026-11-14): cuando el lugar es la información (una ruta, una falla, una cuenca, dónde queda algo),
# una mesa puede llevar un render 3D de la situación. Entra como un tablero (un clip aparte que la mesa aloja), pero lo
# decide el realizador DESPUÉS de la voz: `maqueta` a nivel de mesa en plano.json, con `dice` en cámara, eventos y marcas.
# Dentro de la maqueta la cámara SÍ se mueve (la única excepción a la cámara quieta). Motor: scripts/maqueta3d.py en modo
# pieza (contrato: referencias/diseno/maqueta3d.md). Gates YT20–YT24 (MV15–MV19 en vertical).
MAQUETA_LIENZO = (1120, 1080)          # el lienzo del clip: el del tablero del 16:9 (el vertical pone 950×1040)
MAQUETA_CARPETA = "clips_maqueta_16x9"  # TRABAJO/<carpeta>/<mesa>.mp4 (el vertical: clips_maqueta)
MAQUETA_MIN_S = 5.0                    # YT23: una maqueta de menos no se entiende (la cámara apenas llega)
MAQUETAS_MAX = 4                       # YT23: maquetas por video (el vertical: 2)
MAQUETAS_CAP_MAX = 2                   # YT23: y por capítulo (None = sin tope por capítulo)
MAQUETA_GOLPES = 3                     # YT23: piezas de la mesa encima (o al lado) de una maqueta
MAQUETA_MOTORES = ("three",)           # los motores con render si scripts/maqueta3d.py no declara los suyos (MOTORES): ver motores_maqueta()
MAQUETA_FPS = (10, 60)                 # los fps que acepta el motor (M3D1): una maqueta de prueba a 6 fps renderiza su maqueta a 10
MAQUETA_AVISO = ""   # «Maqueta · no a escala» ya no va por costumbre (usuario, 2026-11-14): solo si el bloque trae `aviso`
MAQUETA_SOLO_PLANO = ("dice", "vez", "al", "escena", "hasta_dice", "dura", "adelanto")   # lo que no pasa al maqueta.json
LUGARES = {   # (lon, lat) de los lugares que suelen salir; otro lugar lleva lon y lat en el golpe
    "guatemala": (-90.52, 14.63), "ciudad de guatemala": (-90.52, 14.63), "barbados": (-59.62, 13.10), "bridgetown": (-59.62, 13.10),
    "nueva york": (-74.00, 40.71), "panama": (-79.52, 8.98), "ciudad de panama": (-79.52, 8.98), "gran caiman": (-81.38, 19.29),
    "islas caiman": (-81.38, 19.29), "miami": (-80.19, 25.76), "washington": (-77.04, 38.90), "mexico": (-99.13, 19.43),
    "el salvador": (-89.19, 13.69), "san salvador": (-89.19, 13.69), "honduras": (-87.20, 14.07), "tegucigalpa": (-87.20, 14.07),
    "costa rica": (-84.09, 9.93), "nicaragua": (-86.25, 12.13), "belice": (-88.77, 17.25), "bahamas": (-77.35, 25.05),
    "madrid": (-3.70, 40.42), "espana": (-3.70, 40.42), "houston": (-95.37, 29.76), "los angeles": (-118.24, 34.05),
    "colombia": (-74.07, 4.71), "bogota": (-74.07, 4.71), "suiza": (8.54, 47.37), "londres": (-0.13, 51.51)}


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    """Escritura atómica: varios realizadores corren `plano --check` a la vez sobre el mismo plano.json."""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = "%s.%d.tmp" % (p, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, p)


def rel(p):
    return os.path.relpath(p, RAIZ)


def falla(m):
    print("ERROR: " + m, file=sys.stderr)
    return 1


_AVISADOS = set()


def avisar(m):
    """Un AVISO por stderr, una sola vez por proceso (las medidas de una pieza se piden muchas veces)."""
    if m not in _AVISADOS:
        _AVISADOS.add(m)
        print("AVISO " + m, file=sys.stderr)
    return m


def aviso_datos(avisos, gate, que, ex):
    """Un gate se queda sin sus datos (DATOS_ILEGIBLES): se dice cuál y por qué, nunca se calla. El aviso queda en `avisos`
    (la lista de ctx["avisos"]: `revisar` la suma a los suyos y sale en `plano --check`) y además sale por stderr, una vez
    por proceso, para los comandos que arman el contexto sin correr el gate (digesto, proyecto). → el texto."""
    m = "%s sin datos: %s (%s: %s)" % (gate, que, type(ex).__name__, ex)
    if avisos is not None and m not in avisos:
        avisos.append(m)
    return avisar(m)


def numeros_respaldo(vals):
    """Los valores con respaldo como números sueltos, para cotejar lo que una pieza pone en pantalla: de cada (valor, factor
    de la unidad) —lo que da VD.valores_respaldo— el valor y el valor por su factor, y cada uno también como lo redondea una
    tarjeta (entero y a un decimal). Un número suelto pasa tal cual."""
    nums = []
    for v in vals or []:
        if isinstance(v, (tuple, list)) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
            nums += [v[0], v[0] * v[1]]
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            nums.append(v)
    return nums + [round(v) for v in nums] + [round(v, 1) for v in nums]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cuadro(t):
    return round(round(t * FPS) / FPS, 4)


def regla(ctx, nombre):
    """Una constante de los gates, o la que el formato pone en ctx["reglas"] (el vertical tiene las suyas)."""
    return (ctx.get("reglas") or {}).get(nombre, globals()[nombre])


def cap_de(ctx, i):
    return next(c["numero"] for c in ctx["caps"] if i in c["idx"])


def fichas(trabajo):
    out = {}
    for f in glob.glob(os.path.join(trabajo, "fotos", "*.json")):
        try:
            d = leer(f)
            out[d.get("id") or os.path.basename(f)[:-5]] = d
        except (OSError, ValueError):
            pass
    return out


def toks_de(S):
    """Las palabras de la voz en fichas normalizadas: [(ficha, índice de palabra)] («US$256» son dos fichas de una palabra)."""
    out = []
    for i, w in enumerate(S.get("palabras") or []):
        for t in VD._plano(w["text"]).split():
            out.append((t, i))
    return out


def buscar(S, dice, desde=0):
    """Dónde dice la voz de la escena la frase `dice`, desde la ficha `desde` → (ficha inicial, palabra inicial, palabra final) o None."""
    T = toks_de(S)
    ws = [t for t, _ in T]
    literal = VD._plano(dice).split()
    en_palabras = VD._plano(VD.dicho(dice)).split()   # «1995» → como lo dice la voz (la misma conversión que /video-3d)
    for q in ([literal] if en_palabras == literal else [literal, en_palabras]):
        if not q:
            continue
        for j in range(desde, len(ws) - len(q) + 1):
            if ws[j:j + len(q)] == q:
                return j, T[j][1], T[j + len(q) - 1][1]
    return None


def segmentos(S):
    import youtube as YT
    return YT.segmentos(S)


def resolver(ctx, P):
    """Pone a cada golpe su segundo global (`_t`), el fin de su frase (`_fin`) y su escena (`_i`); arma las mesas del video en
    orden (las del plano, más los rótulos de capítulo, el cierre y lo que falte). → (mesas, fallas)."""
    es, offs, fallas = ctx["es"], ctx["offs"], []
    PROPIAS, TABLERO = regla(ctx, "PROPIAS"), regla(ctx, "TABLERO")
    cubiertas, mesas = {}, []
    for k, M in enumerate((P or {}).get("mesas") or []):
        claves = [c for c in M.get("escenas") or [] if isinstance(c, str)]
        idx = [ctx["por_clave"].get(c) for c in claves]
        nom = "mesa %d (%s)" % (k + 1, ", ".join(claves)[:60])
        if not idx or any(i is None for i in idx):
            fallas.append("YT16 %s: escena que no existe en el montaje: %s" % (nom, [c for c, i in zip(claves, idx) if i is None]))
            continue
        if idx != list(range(idx[0], idx[0] + len(idx))):
            fallas.append("YT18 %s: sus escenas van seguidas y en orden" % nom)
            continue
        if any(i in cubiertas for i in idx):
            fallas.append("YT18 %s: una escena no va en dos mesas" % nom)
            continue
        tipos = {es[i]["tipo"] for i in idx}
        if tipos & set(PROPIAS):
            fallas.append("YT18 %s: los rótulos de capítulo y el cierre los arma el script: quítalos del plano" % nom)
            continue
        if tipos & set(TABLERO) and len(idx) > 1:
            fallas.append("YT18 %s: una escena %s (tablero) va sola en su mesa" % (nom, "/".join(sorted(tipos & set(TABLERO)))))
            continue
        maq = None
        if M.get("maqueta") is not None:
            if tipos & set(TABLERO):
                fallas.append("YT20 %s: la escena %s ya trae su animación (es un tablero): la maqueta va en una mesa de escenas sin tablero"
                              % (nom, "/".join(sorted(tipos & set(TABLERO)))))
            else:
                maq, fm = maqueta_tiempos(ctx, M["maqueta"], claves, nom)
                fallas += fm
        cursor, golpes = {}, []
        for j, g in enumerate(M.get("golpes") or []):
            if not isinstance(g, dict):
                continue
            g = dict(g)
            cl = g.get("escena") or claves[0]
            if cl not in claves:
                fallas.append("YT16 %s golpe %d: su escena «%s» no es de esta mesa" % (nom, j + 1, cl))
                continue
            i = ctx["por_clave"][cl]
            S = es[i]
            dice = (g.get("dice") or "").strip()
            if not dice:
                if i == 0 and all(x.get("_ya") for x in golpes) and len(golpes) < 3:   # el primer cuadro del video no espera a la voz
                    g.update(_t=0.0, _fin=0.6, _i=i, _ya=True)
                    golpes.append(g)
                    continue
                fallas.append("YT14 %s golpe %d (%s): falta `dice` (las palabras de la voz que lo hacen entrar)" % (nom, j + 1, g.get("tipo")))
                continue
            r = buscar(S, dice, cursor.get(i, 0))
            if not r:
                antes = buscar(S, dice, 0)
                fallas.append("YT14 %s golpe %d: la voz de %s no dice «%s»%s" % (nom, j + 1, cl, dice, " después del golpe anterior (van en orden)" if antes else ""))
                continue
            cursor[i] = r[0]
            pal = S["palabras"]
            g.update(_t=round(offs[i] + pal[r[1]]["start"], 3), _fin=round(offs[i] + pal[r[2]]["end"], 3), _i=i)
            golpes.append(g)
        golpes.sort(key=lambda x: x["_t"])
        for i in idx:
            cubiertas[i] = True
        mesas.append(dict({"idx": idx, "golpes": golpes, "clase": "tablero" if tipos & set(TABLERO) else "maqueta" if maq else "mesa", "titulo": M.get("titulo") or ""},
                          **({"maqueta": maq} if maq else {})))
    for i, S in enumerate(es):
        if i in cubiertas:
            continue
        if S["tipo"] in PROPIAS:
            mesas.append({"idx": [i], "golpes": [], "clase": S["tipo"]})
        elif S["tipo"] in TABLERO:
            mesas.append({"idx": [i], "golpes": [], "clase": "tablero"})
        else:
            fallas.append("YT14 E%d (%s, %s): ninguna mesa del plano la cubre" % (S["n"], S["clave"], S["tipo"]))
            mesas.append({"idx": [i], "golpes": [], "clase": "mesa", "vacia": True})
    mesas.sort(key=lambda m: m["idx"][0])
    for k, M in enumerate(mesas):
        o = offs[M["idx"][0]]
        g1 = M["golpes"][0]["_t"] if M["golpes"] else o
        # la mesa anterior se queda hasta que la primera pieza de esta va a caer (sin mesa vacía entre las dos)
        M["ini"] = cuadro(o if (k == 0 or M["clase"] != "mesa" or mesas[k - 1]["clase"] in PROPIAS) else max(o, g1 - LEAD - 0.15))
        M["cap"] = cap_de(ctx, M["idx"][0])
    for k, M in enumerate(mesas):
        M["fin"] = mesas[k + 1]["ini"] if k + 1 < len(mesas) else ctx["total"]
        M["id"] = "m%d" % (k + 1)
    return mesas, fallas


def eventos_de(ctx, M):
    """Los segundos en que ENTRA algo en una mesa: [(t, 'pieza'|'marca'|'tablero', tipo)]."""
    ev = []
    for g in M["golpes"]:
        ev.append((g["_t"], "pieza", g.get("tipo")))
        for sub in subgolpes(ctx, g):
            ev.append((sub, "marca", g.get("tipo")))
    if M["clase"] == "tablero":
        i = M["idx"][0]
        for x in ctx["es"][i].get("eventos") or []:
            if x.get("tipo") in regla(ctx, "EVENTOS_TABLERO"):
                ev.append((round(ctx["offs"][i] + x["t"], 3), "tablero", x["tipo"]))
    if M["clase"] == "maqueta":   # lo que pasa en la maqueta cuenta como entrada: la cámara que llega a un lugar, un evento, una marca
        ev += [(t, "maqueta", que) for t, que, _ in entradas_maqueta(ctx, M)]
    return sorted(ev)


def subgolpes(ctx, g):
    """Los segundos de lo que una pieza hace después de entrar (un subrayado, cada elemento de una lista, el lazo)."""
    S = ctx["es"][g["_i"]]
    o, out = ctx["offs"][g["_i"]], []

    def t_de(frase):
        r = buscar(S, frase or "", 0)
        return round(o + S["palabras"][r[1]]["start"], 3) if r else None
    if g.get("tipo") in ("documento", "cita"):
        a_, b_ = lectura(ctx, g)
        t = a_
        while a_ is not None and t < b_:
            if t > g["_t"] + 0.2:
                out.append(round(t, 3))
            t += 2.6
    if g.get("resalta_dice") and g.get("tipo") == "recorte":
        t = t_de(g["resalta_dice"])
        if t is not None and t > g["_t"] + 0.2:
            out.append(t)
    for it in (g.get("items") or [])[1:]:
        t = t_de(it.get("dice")) if isinstance(it, dict) else None
        if t is not None:
            out.append(t)
    if isinstance(g.get("lazo"), dict):
        t = t_de(g["lazo"].get("dice"))
        if t is not None:
            out.append(t)
    for grupo in ("nodos", "aristas", "acusadores", "pasos", "barras"):   # las piezas compuestas del vertical: cada parte entra con su `dice`
        for it in g.get(grupo) or []:
            for c in ("clave_dice", "dice"):
                t = t_de(it.get(c)) if isinstance(it, dict) and it.get(c) else None
                if t is not None and t > g["_t"] + 0.2:
                    out.append(t)
    return out


def lectura(ctx, g):
    """De cuándo a cuándo la voz LEE un documento (`lee` … `lee_hasta`) o una cita (su texto): (t0, t1) o (None, None)."""
    S = ctx["es"][g["_i"]]
    o = ctx["offs"][g["_i"]]
    if g.get("tipo") == "documento":
        ini, fin = g.get("lee"), g.get("lee_hasta") or g.get("lee")
    else:
        pal = (g.get("texto") or "").split()
        ini, fin = " ".join(pal[:3]), " ".join(pal[-3:])
    a = buscar(S, ini or "", 0)
    if not a:
        return None, None
    b = buscar(S, fin or "", a[0]) or a
    return round(o + S["palabras"][a[1]]["start"], 3), round(o + S["palabras"][b[2]]["end"], 3)


def numeros(txt):
    return {re.sub(r"[.,]", "", x) for x in re.findall(r"\d[\d.,]*\d|\d", txt or "")}


def textos_de(g):
    """Todo el texto que una pieza pone en pantalla (para YT13 y para el respaldo de sus números)."""
    partes = [g.get(c) for c in ("valor", "rotulo", "grande", "chico", "arriba", "texto", "definicion", "pie", "nombre", "kicker", "rol", "titulo",
                                 "subtitulo", "extracto", "titular", "persona", "cargo", "autor")]
    partes += [it.get("texto") for it in g.get("items") or [] if isinstance(it, dict)]
    partes += [p.get("nombre") for p in g.get("puntos") or [] if isinstance(p, dict)]
    partes += [n.get(c) for grupo in ("nodos", "acusadores", "pasos") for n in g.get(grupo) or [] if isinstance(n, dict) for c in ("nombre", "cargo", "texto", "anio")]
    partes += ["%s %s" % (b.get("etiqueta") or "", b.get("texto") or b.get("valor") or "") for b in g.get("barras") or [] if isinstance(b, dict)]
    return " ".join(str(x) for x in partes if x)


def notas_de(carpeta):
    """Las notas guardadas en una carpeta de descargas: {url: ficha}. `historia.py leer` deja la ficha <hash>.json junto a su
    texto; `congreso.py leer` deja solo <hash>.txt (línea 1 la url; línea 2 el titular, vacía si es un PDF) y, de una
    iniciativa, <hash>.pdf: su ficha se arma aquí, con las claves que usan `texto_nota` y `pdf_de`."""
    out = {}
    for f in sorted(glob.glob(os.path.join(carpeta, "*.json"))):
        try:
            d = leer(f)
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and d.get("url"):
            d["_json"] = f
            out[d["url"]] = d
    for f in sorted(glob.glob(os.path.join(carpeta, "*.txt"))):
        if os.path.exists(f[:-4] + ".json"):
            continue   # el texto de una ficha ya leída
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                url, titulo = fh.readline().strip(), fh.readline().strip()
        except OSError:
            continue
        if re.match(r"https?://\S+$", url) and url not in out:
            out[url] = {"url": url, "titulo": titulo, "archivo": f, "_json": f[:-4] + ".json"}
    return out


def notas_leidas(carpetas=None):
    """Las notas ya leídas: {url: ficha}. Las de `historia.py leer` (sesiones/_descargas/historia) y las de `congreso.py leer`
    (sesiones/_descargas/congreso); si una url está en las dos, vale la primera. Con `carpetas` (las pruebas) no usa la caché."""
    if carpetas is None and hasattr(notas_leidas, "c"):
        return notas_leidas.c
    out = {}
    for carpeta in (CARPETAS_NOTAS if carpetas is None else carpetas):
        for url, d in notas_de(carpeta).items():
            out.setdefault(url, d)
    if carpetas is None:
        notas_leidas.c = out
    return out


def texto_nota(n):
    for p in (n.get("archivo"), n["_json"][:-5] + ".txt"):
        if p and os.path.exists(p if os.path.isabs(p) else os.path.join(RAIZ, p)):
            return open(p if os.path.isabs(p) else os.path.join(RAIZ, p), encoding="utf-8", errors="ignore").read()
    return ""


def revisar(ctx, P, mesas=None, f0=None):
    """YT13–YT19 sobre el plano → (fallas, avisos, medidas)."""
    import youtube as YT
    es, offs = ctx["es"], ctx["offs"]
    (MESA_S, MESA_PIEZAS, HUECO_MAX_S, ENTRE_GOLPES_S, PIEZA_NUEVA_MIN, ARCHIVO_MIN, TIPOS_MIN, TEXTO_SEGUIDOS, FOTO_USOS_MAX, FOTO_SEPARACION_S, TIPOS, ARCHIVO,
     SOLO_TEXTO, PROPIAS) = (regla(ctx, n) for n in ("MESA_S", "MESA_PIEZAS", "HUECO_MAX_S", "ENTRE_GOLPES_S", "PIEZA_NUEVA_MIN", "ARCHIVO_MIN", "TIPOS_MIN",
                                                    "TEXTO_SEGUIDOS", "FOTO_USOS_MAX", "FOTO_SEPARACION_S", "TIPOS", "ARCHIVO", "SOLO_TEXTO", "PROPIAS"))
    if mesas is None:
        mesas, f0 = resolver(ctx, P)
    f, av = list(f0 or []), []
    F = fichas(ctx["trabajo"])
    elenco = ctx["elenco"] if "elenco" in ctx else YT.elenco_serie(ctx["Y"])
    nombres = {VD._plano(c) for p in elenco for c in p["claves"]} | {VD._plano(p["nombre"]) for p in elenco}
    for m in ctx.get("avisos") or []:   # lo que el contexto no pudo leer (aviso_datos): el gate lo dice, no se calla
        if m not in av:
            av.append(m)
    if "respaldo" in ctx:   # el vertical lo trae resuelto (números sueltos)
        vals = ctx["respaldo"]
    else:                   # el 16:9: las cifras verificadas de cada parte de la serie
        sin_leer = []
        try:
            vals = numeros_respaldo(YT.valores_de(ctx["Y"], sin_leer))
        except DATOS_ILEGIBLES as ex:
            vals, sin_leer = [], [("la serie (su estado no trae las partes)", ex)]
        for donde, ex in sin_leer:
            aviso_datos(av, "YT16", "no se pudo leer el respaldo de las cifras de %s; un número en pantalla solo pasa si la voz lo dice "
                                    "o está en los hechos de la mesa" % donde, ex)
    respaldo = {re.sub(r"\.0+$", "", ("%f" % v).rstrip("0").rstrip(".")) for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)}
    PG = leer(os.path.join(ctx["trabajo"], "paginas.json")) if os.path.exists(os.path.join(ctx["trabajo"], "paginas.json")) else {}
    # lo que respalda un número o un nombre además de la voz de la mesa: todo lo que la voz dice en el video y los hechos
    # verificados de las escenas de la mesa (su texto, su fecha, sus citas, sus actores)
    todo_dicho = {x for S in es for w in S.get("palabras") or [] for x in numeros(w["text"])} | {EN_PALABRAS[t] for S in es for t, _ in toks_de(S) if t in EN_PALABRAS}
    try:
        H = ctx["hechos"] if "hechos" in ctx else YT.hechos_serie(ctx["Y"])
        hechos_de = ctx["hechos_de"] if "hechos_de" in ctx else {
            e.get("id"): e.get("hechos") or [] for e in leer(os.path.join(ctx["trabajo"], "indice.json")).get("escenas") or []}
    except DATOS_ILEGIBLES as ex:
        H, hechos_de = {}, {}
        aviso_datos(av, "YT16", "no se pudieron leer los hechos verificados de las escenas (%s); un número o un nombre en pantalla solo "
                                "pasa si la voz lo dice" % rel(os.path.join(ctx["trabajo"], "indice.json")), ex)

    def hechos_mesa(M):
        return [H[h] for i in M["idx"] for h in hechos_de.get(es[i]["clave"]) or [] if h in H]

    def personas_de(hs):
        out = set()
        for h in hs:
            for a_ in h.get("actores") or []:
                k = VD._plano(a_)
                if 2 <= len(k.split()) <= 6 and not INSTITUCION.search(k):
                    out |= {t for t in k.split() if len(t) > 3}
        return out
    voz_video = " ".join(VD._plano(w["text"]) for S in es for w in S.get("palabras") or [])
    usos, por_cap = {}, {}
    n_seg = n_nueva = 0
    for M in mesas:
        if M["clase"] in PROPIAS:
            continue
        nom = "%s E%s" % (M["id"], "–".join(str(es[i]["n"]) for i in (M["idx"][0], M["idx"][-1])) if len(M["idx"]) > 1 else es[M["idx"][0]]["n"])
        d = M["fin"] - M["ini"]
        if M["clase"] == "mesa" and not MESA_S[0] <= d <= MESA_S[1] and not M.get("vacia"):
            f.append("YT18 %s: la mesa dura %.1f s; va de %.0f a %.0f s (parte la mesa por tema, o únela a la vecina)" % (nom, d, *MESA_S))
        if len(M["golpes"]) > MESA_PIEZAS:
            f.append("YT18 %s: %d piezas en una mesa (máximo %d): parte la mesa" % (nom, len(M["golpes"]), MESA_PIEZAS))
        ev = eventos_de(ctx, M)
        voz_mesa = " ".join(VD._plano(w["text"]) for i in M["idx"] for w in es[i]["palabras"])
        dichos = {x for i in M["idx"] for w in es[i]["palabras"] for x in numeros(w["text"])}
        dichos |= {EN_PALABRAS[t] for i in M["idx"] for t, _ in toks_de(es[i]) if t in EN_PALABRAS}
        hs = hechos_mesa(M)
        de_hechos = numeros(" ".join(" ".join(str(x) for x in (h.get("texto"), h.get("fecha"))) + " " + " ".join(fu.get("cita") or "" for fu in h.get("fuentes") or []) for h in hs))
        apellidos = personas_de(hs)
        # YT14: cada oración trae un golpe; ningún hueco largo
        for i in M["idx"]:
            S = es[i]
            for sg in segmentos(S):
                if not (sg.get("texto") or "").strip():
                    continue
                a, b = offs[i] + sg["t"], offs[i] + sg["hasta"]
                dentro = [e for e in ev if a - 0.6 <= e[0] < b]
                n_seg += 1
                n_nueva += any(e[1] in ("pieza", "tablero", "maqueta") for e in dentro)
                if not dentro and M["clase"] == "tablero" and regla(ctx, "TABLERO_SOLO"):
                    n_nueva += 1   # en vertical el tablero va solo: su animación ya aprobada es lo que se ve
                    continue
                if not dentro:
                    f.append("YT14 %s %s %.1f s: ninguna pieza entra con «%s»" % (nom, S["clave"], a, sg["texto"][:70]))
        ts = [M["ini"]] + [e[0] for e in ev] + [min(M["fin"], offs[M["idx"][-1]] + es[M["idx"][-1]].get("fin_voz", es[M["idx"][-1]]["dur"]))]
        for a, b in zip(ts, ts[1:]):
            if b - a > (regla(ctx, "HUECO_TABLERO_S") or HUECO_MAX_S if M["clase"] in ("tablero", "maqueta") else HUECO_MAX_S):
                f.append("YT14 %s: %.1f s sin que entre nada (de %.1f a %.1f s; máximo %.0f s)" % (nom, b - a, a, b, HUECO_MAX_S))
        ent = [g["_t"] for g in M["golpes"] if not g.get("_acto")]   # el rótulo de acto lo pone el motor: no cuenta como entrada del plano
        for a, b in zip(ent, ent[1:]):
            if b - a < ENTRE_GOLPES_S and b > 0.01:
                f.append("YT18 %s: dos piezas entran con %.2f s de diferencia en %.1f s (mínimo %.1f s): una lista, o separa los `dice`" % (nom, b - a, a, ENTRE_GOLPES_S))
        # YT13: cada cifra o año dicho se ve cuando se dice
        if M["clase"] in ("mesa", "maqueta"):   # la maqueta no trae cifras: las pone un golpe de la mesa (o el texto de una marca)
            marcas = [k for k in (M.get("maqueta") or {}).get("marcas") or [] if isinstance(k, dict) and k.get("_t") is not None]
            for i in M["idx"]:
                for w in es[i]["palabras"]:
                    if not w.get("num"):
                        continue
                    t = offs[i] + w["start"]
                    ns = numeros(w["text"])
                    if not any(ns & numeros(textos_de(g)) and g["_t"] <= t + 1.0 for g in M["golpes"]) and \
                            not any(ns & numeros("%s %s" % (k.get("texto") or "", k.get("sub") or "")) and k["_t"] <= t + 1.0 for k in marcas):
                        f.append("YT13 %s %s %.1f s: la voz dice «%s» y ninguna pieza lo muestra" % (nom, es[i]["clave"], t, w["text"]))
        seguidos = 0
        for j, g in enumerate(M["golpes"]):
            t = g.get("tipo")
            q = "%s golpe %d (%s, %.1f s)" % (nom, j + 1, t, g["_t"])
            if t not in TIPOS:
                f.append("YT16 %s: tipo desconocido; van %s" % (q, " · ".join(TIPOS)))
                continue
            por_cap.setdefault(M["cap"], []).append(g)
            seguidos = seguidos + 1 if t in SOLO_TEXTO else 0
            if seguidos > TEXTO_SEGUIDOS:
                f.append("YT17 %s: %d rótulos de solo texto seguidos (máximo %d): pon un archivo real entre ellos" % (q, seguidos, TEXTO_SEGUIDOS))
            # los números que una pieza pone en pantalla: dichos por la voz de la mesa o con respaldo
            if t not in ("recorte", "documento", "cita"):
                propios = numeros(" ".join(str(g.get(c) or "") for c in ("valor", "grande", "chico", "arriba", "rotulo", "texto", "definicion", "rol"))
                                  + " " + " ".join("%s %s" % (b.get("etiqueta") or "", b.get("texto") or b.get("valor") or "") for b in g.get("barras") or [] if isinstance(b, dict)))
                sin = sorted(x for x in propios if x not in dichos and x not in respaldo and x not in todo_dicho and x not in de_hechos
                             and not (t == "fecha" and len(x) <= 2))
                if sin:
                    f.append("YT16 %s: «%s» no lo dice la voz, no está en los hechos de la mesa ni tiene respaldo en los datos" % (q, ", ".join(sin)))
            if t == "foto":
                r = F.get(g.get("foto"))
                if not r or not r.get("credito") or not os.path.exists(os.path.join(ctx["trabajo"], r.get("archivo") or "x")):
                    f.append("YT16 %s: la foto «%s» no tiene ficha, crédito o archivo (historia.py foto)" % (q, g.get("foto")))
                    continue
                usos.setdefault(g["foto"], []).append(g["_t"])
                if not (g.get("pie") or "").strip() or len(g["pie"].split()) > 9:
                    f.append("YT16 %s: `pie` de 1 a 9 palabras que diga qué se ve" % q)
                oracion = VD._plano(" ".join(w["text"] for w in es[g["_i"]]["palabras"]))
                if (JUDICIAL.search(r.get("descripcion") or "") or r.get("retrato_de")) and not any(n and n in oracion for n in nombres) \
                        and not (apellidos & set(oracion.split())):
                    f.append("YT16 %s: «%s» muestra a personas en un proceso o es un retrato, y la voz de %s no nombra a nadie: ahí da a entender "
                             "que son los acusados; usa un edificio, un documento o un recorte" % (q, g["foto"], es[g["_i"]]["clave"]))
            elif t == "recorte":
                n = notas_leidas().get(g.get("url"))
                if not n:
                    f.append("YT16 %s: `url` de una nota ya leída con historia.py leer" % q)
                    continue
                cuerpo = VD._plano(texto_nota(n))
                if g.get("titular") and VD._plano(g["titular"]) != VD._plano(n.get("titulo") or ""):
                    f.append("YT16 %s: el titular no es el de la nota («%s»)" % (q, (n.get("titulo") or "")[:80]))
                if g.get("extracto") and VD._plano(g["extracto"]) not in cuerpo:
                    f.append("YT16 %s: el extracto no está literal en la nota guardada" % q)
                if g.get("resalta") and g["resalta"] not in (g.get("extracto") or ""):
                    f.append("YT16 %s: `resalta` es un trozo literal del extracto" % q)
                if not (g.get("medio") and g.get("fecha") and (g.get("titular") or g.get("extracto"))):
                    f.append("YT16 %s: lleva medio, fecha y titular o extracto" % q)
            elif t == "documento":
                if g.get("pagina"):
                    if g["pagina"] not in PG:
                        f.append("YT16 %s: la página «%s» no está en paginas.json (historia.py pagina)" % (q, g["pagina"]))
                elif not (isinstance(g.get("portada"), dict) and notas_leidas().get(g["portada"].get("url")) and g.get("titulo")):
                    f.append("YT16 %s: lleva `pagina` (historia.py pagina) o `portada` {url de un PDF ya leído, pagina} con `titulo`" % q)
            elif t == "persona":
                p = next((p for p in elenco if VD._plano(g.get("persona") or "") in [VD._plano(p["nombre"])] + [VD._plano(c) for c in p["claves"]]), None)
                # alguien que no es del elenco: su nombre lo dice la voz (en esta mesa o antes, con nombre y apellido)
                if not p and not (g.get("cargo") and (VD._plano(g.get("persona") or "") in voz_mesa or VD._plano(g.get("persona") or "") in voz_video)):
                    f.append("YT16 %s: «%s» no es del elenco: lleva el nombre como lo dice la voz y su `cargo`" % (q, g.get("persona")))
            elif t == "institucion":
                if not (g.get("nombre") and (g.get("kicker") or g.get("rol"))):
                    f.append("YT16 %s: lleva nombre y kicker o rol (qué es)" % q)
            elif t == "lugar":
                if g.get("mapa") == "guatemala":
                    if not g.get("depto"):
                        f.append("YT16 %s: el mapa de Guatemala lleva `depto`" % q)
                elif g.get("mapa") == "mundo":
                    for p in g.get("puntos") or []:
                        if not (isinstance(p, dict) and p.get("nombre") and (VD._plano(p["nombre"]) in LUGARES or ("lon" in p and "lat" in p))):
                            f.append("YT16 %s: el punto «%s» no está en la lista de lugares: ponle lon y lat" % (q, (p or {}).get("nombre")))
                    if not g.get("puntos"):
                        f.append("YT16 %s: el mapa del mundo lleva `puntos`" % q)
                else:
                    f.append("YT16 %s: `mapa` es «guatemala» o «mundo»" % q)
            elif t == "fecha" and not g.get("grande"):
                f.append("YT16 %s: lleva `grande` (el año o el día)" % q)
            elif t == "cifra" and not (g.get("valor") and g.get("rotulo")):
                f.append("YT16 %s: lleva `valor` y `rotulo` (de qué es la cifra)" % q)
            elif t == "termino" and (not g.get("texto") or len(g["texto"].split()) > 6):
                f.append("YT16 %s: `texto` de 1 a 6 palabras" % q)
            elif t == "cita" and not (g.get("texto") and g.get("autor")):
                f.append("YT16 %s: lleva `texto` literal y `autor`" % q)
            elif t == "lista" and not (isinstance(g.get("items"), list) and 2 <= len(g["items"]) <= 6):
                f.append("YT16 %s: `items` son 2 a 6 {texto, dice}" % q)
        if M["clase"] == "maqueta":   # YT20–YT24: la maqueta 3D de la mesa
            fm, am = revisar_maqueta(ctx, M, nom, lambda x: x in dichos or x in respaldo or x in todo_dicho or x in de_hechos)
            f += fm
            av += am
    f += revisar_maquetas(ctx, mesas)
    # YT15: una foto, pocas veces y lejos
    for fid, ts in sorted(usos.items()):
        if len(ts) > FOTO_USOS_MAX:
            f.append("YT15 la foto %s sale %d veces (máximo %d): %s" % (fid, len(ts), FOTO_USOS_MAX, ", ".join(VD.mmss(t) if hasattr(VD, "mmss") else "%.0f s" % t for t in ts)))
        for a, b in zip(ts, ts[1:]):
            if b - a < FOTO_SEPARACION_S:
                f.append("YT15 la foto %s vuelve a los %.0f s (mínimo %d s entre una y otra): %.0f s y %.0f s" % (fid, b - a, FOTO_SEPARACION_S, a, b))
    # YT17: que no sea relleno
    medidas = {"oraciones": n_seg, "con_pieza_nueva": n_nueva, "capitulos": {}, "maquetas": sum(1 for M in mesas if M["clase"] == "maqueta")}
    if n_seg and n_nueva / n_seg < PIEZA_NUEVA_MIN:
        f.append("YT17 solo %d de %d oraciones traen una pieza nueva (mínimo %.0f %%)" % (n_nueva, n_seg, 100 * PIEZA_NUEVA_MIN))
    tab = {}
    for M in mesas:
        if M["clase"] == "tablero":
            tab[M["cap"]] = tab.get(M["cap"], 0) + 1
    for cap, gs in sorted(por_cap.items()):
        tipos = sorted({g["tipo"] for g in gs})
        real = sum(1 for g in gs if g["tipo"] in ARCHIVO or (g["tipo"] == "persona" and retrato_de(elenco, g))) + tab.get(cap, 0)
        n = len(gs) + tab.get(cap, 0)
        medidas["capitulos"][cap] = {"piezas": n, "archivo_real": real, "tipos": tipos}
        if len(tipos) < TIPOS_MIN:
            f.append("YT17 capítulo %d: %d tipos de pieza (%s); van al menos %d distintos" % (cap, len(tipos), ", ".join(tipos), TIPOS_MIN))
        if n and real / n < ARCHIVO_MIN:
            f.append("YT17 capítulo %d: %d de %d piezas son archivo real (%.0f %%; mínimo %.0f %%): más fotos, recortes, documentos y mapas"
                     % (cap, real, n, 100 * real / n, 100 * ARCHIVO_MIN))
        elif n and real / n < 0.5:
            av.append("YT17 capítulo %d: %.0f %% de archivo real (%d de %d); la meta es 50 %%" % (cap, 100 * real / n, real, n))
    # YT19: nada de cámara para aparentar ritmo
    for S in es:
        if S.get("saltos"):
            f.append("YT19 E%d lleva saltos de cámara: en el 16:9 la cámara no se mueve" % S["n"])
    return f, av, medidas


def retrato_de(elenco, g):
    k = VD._plano(g.get("persona") or "")
    p = next((p for p in elenco if k in [VD._plano(p["nombre"])] + [VD._plano(c) for c in p["claves"]]), None)
    return p if p and p.get("foto") else None


def renglones(txt, px, ancho, cond=True):
    """Cuántos renglones ocupa un texto (estimado: la condensada mide ≈ 0.40 em por carácter; la normal, 0.52)."""
    por = max(4, int(ancho / (px * (0.455 if cond else 0.52))))
    n, linea = 1, 0
    for p in (txt or "").split():
        if linea and linea + 1 + len(p) > por:
            n, linea = n + 1, len(p)
        else:
            linea += (1 if linea else 0) + len(p)
    return n


def tam_nombre(txt, ancho, maximo=104, minimo=64):
    """El cuerpo de un nombre: en un renglón si cabe a ≥ 72 px; si no, el mayor que quepa en dos."""
    for px in range(maximo, 71, -6):
        if renglones(txt, px, ancho) == 1:
            return px
    for px in range(maximo, minimo - 1, -6):
        if renglones(txt, px, ancho) <= 2:
            return px
    return minimo


def atlas(puntos, ancho=1150):
    """Un mapa del mundo (Natural Earth 50 m, dominio público: design/mapas/paises-50m.json) encuadrado en sus puntos."""
    pts = []
    for p in puntos:
        if not isinstance(p, dict):
            continue
        lo, la = (p["lon"], p["lat"]) if "lon" in p and "lat" in p else LUGARES.get(VD._plano(p.get("nombre") or ""), (None, None))
        if lo is not None:
            pts.append((p.get("nombre") or "", float(lo), float(la)))
    if not pts:
        pts = [("Guatemala", -90.52, 14.63)]
    lons, lats = [p[1] for p in pts], [p[2] for p in pts]
    L0, L1, B0, B1 = min(lons) - 5, max(lons) + 5, min(lats) - 5.5, max(lats) + 5.5
    phi = math.radians((B0 + B1) / 2)
    if (L1 - L0) * math.cos(phi) / (B1 - B0) < 1.9:   # proporción ≈ 2:1 (una tira de atlas)
        extra = (1.9 * (B1 - B0) / math.cos(phi) - (L1 - L0)) / 2
        L0, L1 = L0 - extra, L1 + extra
    else:
        extra = ((L1 - L0) * math.cos(phi) / 1.9 - (B1 - B0)) / 2
        B0, B1 = B0 - extra, B1 + extra
    k = ancho / ((L1 - L0) * math.cos(phi))
    alto = int((B1 - B0) * k)

    def P(lon, lat):
        return ((lon - L0) * math.cos(phi) * k, (B1 - lat) * k)
    if not hasattr(atlas, "T"):
        T = leer(os.path.join(RAIZ, "design", "mapas", "paises-50m.json"))
        sx, sy = T["transform"]["scale"]
        tx, ty = T["transform"]["translate"]
        arcs = []
        for a in T["arcs"]:
            x = y = 0
            ps = []
            for dx, dy in a:
                x += dx
                y += dy
                ps.append((x * sx + tx, y * sy + ty))
            arcs.append(ps)
        atlas.T = (T, arcs)
    T, arcs = atlas.T
    tierra, gt = [], []
    for geo in T["objects"]["countries"]["geometries"]:
        polys = [geo["arcs"]] if geo["type"] == "Polygon" else geo["arcs"] if geo["type"] == "MultiPolygon" else []
        for poly in polys:
            for ring in poly:
                ps = []
                for i in ring:
                    a = arcs[i] if i >= 0 else arcs[~i][::-1]
                    ps += a if not ps else a[1:]
                if not any(L0 - 4 < lo < L1 + 4 and B0 - 4 < la < B1 + 4 for lo, la in ps):
                    continue
                paso = max(1, len(ps) // 900)
                d = "M" + "L".join("%.1f %.1f" % P(lo, la) for lo, la in ps[::paso]) + "Z"
                (gt if geo.get("id") == "320" else tierra).append(d)
    return {"w": int(ancho), "h": alto, "tierra": "".join(tierra), "gt": "".join(gt), "pts": [(n, *P(lo, la)) for n, lo, la in pts]}


def deptos():
    """Los 22 departamentos (design/mapa_geometria.svg): [(d, id, nombre, (cx, cy))]."""
    if not hasattr(deptos, "c"):
        s = open(os.path.join(RAIZ, "design", "mapa_geometria.svg"), encoding="utf-8").read()
        out = []
        for m in re.finditer(r"<path\b([^>]*)>", s):
            at = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            if not re.fullmatch(r"GT\d\d", at.get("id") or ""):
                continue
            x = y = 0.0
            pts, cmd, buf = [], None, []
            for t in re.findall(r"[MmLlZz]|-?\d+\.?\d*", at["d"]):
                if t in "MmLlZz":
                    cmd, buf = t, []
                    continue
                buf.append(float(t))
                if len(buf) == 2:
                    x, y = (buf[0], buf[1]) if cmd in "ML" else (x + buf[0], y + buf[1])
                    pts.append((x, y))
                    buf = []
                    cmd = "L" if cmd == "M" else "l" if cmd == "m" else cmd
            out.append((at["d"], at["id"], at.get("name") or "", (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))))
        deptos.c = out
    return deptos.c


def pdf_de(url):
    n = notas_leidas().get(url)
    if not n:
        return None
    p = n["_json"][:-5] + ".pdf"
    return p if os.path.exists(p) else None


def pagina_png(trabajo, url, pagina, dpi=200):
    """La página de un PDF ya leído como imagen (fotos/_doc-<hash>-p<N>.jpg, con poppler). → (ruta relativa al TRABAJO, ancho, alto) o None."""
    pdf = pdf_de(url)
    if not pdf:
        return None   # no es un PDF ya leído: la pieza se dibuja sin la imagen de la página
    base = "_doc-%s-p%d" % (hashlib.sha1(url.encode()).hexdigest()[:8], pagina)
    dst = os.path.join(trabajo, "fotos", base + ".jpg")
    if not os.path.exists(dst):
        if not shutil.which("pdftoppm"):
            avisar("falta pdftoppm (brew install poppler): la página %d de %s no se puede sacar como imagen y el documento sale sin ella" % (pagina, rel(pdf)))
            return None
        tmp = os.path.join(trabajo, "fotos", base)
        r = subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(pagina), "-l", str(pagina), "-jpeg", "-jpegopt", "quality=88", "-singlefile", pdf, tmp],
                           check=False, capture_output=True, text=True)
        if not os.path.exists(dst):
            avisar("pdftoppm no sacó la página %d de %s (código %d%s): el documento sale sin la imagen de la página"
                   % (pagina, rel(pdf), r.returncode, ": " + (r.stderr.strip().splitlines() or ["sin detalle"])[-1][:160] if r.stderr.strip() else ""))
    if not os.path.exists(dst):
        return None
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout.strip().split(",")
    return "fotos/" + base + ".jpg", int(r[0]), int(r[1])


class Mesa:
    def __init__(self, mid, ini, fin, barrer, css, ancho=1920, alto=1080, centro=(760, 1160), medio_y=520, barrido=-2400):
        self.id, self.ini, self.fin, self.barrer, self.css = mid, ini, fin, barrer, css
        self.ancho, self.alto, self.centro, self.medio_y, self.barrido = ancho, alto, centro, medio_y, barrido
        self.html, self.tl, self.piezas, self.sfx, self.k, self.extra, self.f = [], [], [], [], 0, [], 1.0

    def loc(self, g):
        return round(max(0.0, g - self.ini), 3)

    def pieza(self, g, x, y, w, giro, dentro, sfx="papel", ya=False, sombra=True, velo=True):
        if self.f != 1:   # la mesa va llena: todo a escala (zoom de Chrome: el texto se vuelve a dibujar nítido)
            dentro = '<div style="zoom:%.3f;width:%dpx">%s</div>' % (self.f, w, dentro)
            w = int(w * self.f)
        self.k += 1
        pid = "%s-p%d" % (self.id, self.k)
        t0 = 0.0 if ya else self.loc(g - LEAD)
        dx = -130 if x + w / 2 < self.centro[0] else 130 if x + w / 2 > self.centro[1] else 0
        dy = 100 if y > self.medio_y else -90
        self.html.append(
            '<div id="%s" class="clip pz" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-layout-allow-overlap '
            'data-layout-allow-occlusion style="left:%dpx;top:%dpx;width:%dpx;z-index:%d"><div id="%s-mov" class="mov">'
            '<div id="%s-pila" class="pila"%s>%s%s</div></div></div>'
            % (pid, t0, max(0.1, round(self.fin - self.ini - t0, 3)), 1 + self.k % 6, x, y, w, 10 + self.k, pid, pid,
               "" if sombra else ' style="box-shadow:none"', dentro, '<i id="%s-velo" class="velo"></i>' % pid if velo else ""))
        if ya:
            self.tl.append('tl.set("#%s-mov",{rotation:%s},0);' % (pid, giro))
        else:
            self.tl.append('tl.fromTo("#%s-mov",{x:%d,y:%d,rotation:%s,scale:1.1,opacity:0},{x:0,y:0,rotation:%s,scale:1,opacity:1,duration:%.2f,'
                           'ease:"power3.out"},%.3f);' % (pid, dx, dy, giro + (5 if giro >= 0 else -5), giro, ENTRA, t0))
            if sfx:
                self.sfx.append((round(self.ini + t0 + ENTRA * 0.55, 3), sfx))
        self.piezas.append({"id": pid, "t0": t0, "giro": giro, "velo": velo})
        return pid

    def cerrar(self):
        P = self.piezas
        for i, p in enumerate(P):
            if p["velo"] and i + VISIBLES < len(P):
                self.tl.append('tl.fromTo("#%s-velo",{opacity:0},{opacity:.5,duration:.45,ease:"power1.out"},%.3f);' % (p["id"], P[i + VISIBLES]["t0"] + 0.1))
        if self.barrer:
            t = round(self.fin - self.ini - 0.46, 3)
            if t > 0.2:
                for i, p in enumerate(P):
                    self.tl.append('tl.fromTo("#%s-mov",{x:0,y:0,rotation:%s},{x:%d,y:%d,rotation:%s,duration:.42,ease:"power2.in",immediateRender:false},%.3f);'
                                   % (p["id"], p["giro"], self.barrido, 30 + 12 * (i % 3), p["giro"] - 9, t + 0.012 * i))
                for sel in self.extra:
                    self.tl.append('tl.fromTo("%s",{x:0},{x:%d,duration:.42,ease:"power2.in",immediateRender:false},%.3f);' % (sel, self.barrido, t))
                self.sfx.append((round(self.fin - 0.34, 3), "whoosh"))
        return ('<template>\n<style>%s</style>\n<div id="root" data-composition-id="%s" data-width="%d" data-height="%d">\n%s\n</div>\n'
                '<script>\n(function(){\nconst tl = gsap.timeline({paused:true});\n%s\nwindow.__timelines["%s"] = tl;\n})();\n</script>\n</template>\n'
                % (self.css, self.id, self.ancho, self.alto, "\n".join(self.html), "\n".join(self.tl), self.id))


def colores(E):
    c = E.get("colores") or {}
    return {"mesa": c.get("bg") or "#1E130E", "mesa2": c.get("fondo_acto2") or "#0F0A07", "papel": c.get("ink") or "#F6F2E8", "papel2": "#E9E1CF",
            "tinta": c.get("tinta_acento") or "#1A1208", "acento": c.get("a1") or "#D9A66B", "gris": c.get("a2") or "#958E86", "cafe": c.get("a3") or "#856441"}


def enlazar(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def VD_mmss(t):
    return "%d:%02d" % (int(t) // 60, int(t) % 60)


def gsap_local(P):
    """GSAP del repositorio en el proyecto P (assets/vendor/gsap.min.js) → la etiqueta que lo carga. El render no llama a la
    red: ningún proyecto de la mesa (vertical o 16:9) trae un <script> de un CDN."""
    enlazar(GSAP_JS, os.path.join(P, "assets", "vendor", "gsap.min.js"))
    return '<script src="assets/vendor/gsap.min.js"></script>'


def hf(P, *args, timeout=3600):
    return subprocess.run(HF + list(args), cwd=P, capture_output=True, text=True, timeout=timeout)


# ---------- el render de HyperFrames: un proceso y un límite de tiempo ----------
def limite_render(dur_s):
    """Cuánto puede tardar un render antes de darlo por colgado (segundos): proporcional a lo que dura el video
    (RENDER_LIMITE_BASE_S + RENDER_LIMITE_POR_S por segundo). MESA_RENDER_LIMITE_S lo fija a mano (una máquina lenta)."""
    env = os.environ.get("MESA_RENDER_LIMITE_S")
    if env:
        try:
            return max(1.0, float(env))
        except ValueError:
            avisar("MESA_RENDER_LIMITE_S=%r no es un número de segundos: vale el límite por duración" % env)
    return RENDER_LIMITE_BASE_S + RENDER_LIMITE_POR_S * max(0.0, float(dur_s or 0))


def texto_limite(que, limite, dur_s, log):
    """El mensaje de un render que pasó su límite: qué se detuvo, cuánto se le dio y qué hacer."""
    return ("%s pasó su límite de %s (%.0f s para %.1f s de video; lo normal es ≈ 1.6× la duración) y se detuvo. Mira %s; si la máquina "
            "de verdad va así de lenta, vuelve a correrlo con MESA_RENDER_LIMITE_S=<segundos>" % (que, VD_mmss(limite), limite, dur_s, rel(log)))


def lanzar_render(P, args, log):
    """`hyperframes render` en el proyecto P, en su propio grupo de procesos (para poder detenerlo entero) → Popen.
    SIEMPRE con un proceso (--workers 1 va en `args`): con varios el video tiembla."""
    return subprocess.Popen(HF + ["render"] + list(args), cwd=P, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def detener_render(pr):
    """Termina un render y todo lo que lanzó (npx → node → Chrome → ffmpeg): si queda vivo, sostiene el candado global de
    HyperFrames y el siguiente render se queda en fila."""
    for senal in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pr.pid, senal)
        except OSError:
            break   # ya no queda nadie en el grupo
        try:
            pr.wait(timeout=8)
        except subprocess.TimeoutExpired:
            pass
    if pr.poll() is None:
        pr.kill()
        pr.wait()


def render_hf(P, args, limite, ruta_log):
    """Un render con límite de tiempo → (código de salida, vencido). Si pasa `limite` segundos se detiene con todos sus
    procesos y devuelve (None, True); el registro queda en `ruta_log`."""
    with open(ruta_log, "w") as log:
        pr = lanzar_render(P, args, log)
        try:
            return pr.wait(timeout=limite), False
        except subprocess.TimeoutExpired:
            return None, True
        finally:
            if pr.poll() is None:   # venció, o se interrumpió a mano: no queda huérfano
                detener_render(pr)


def hoja_de(ctx, mesas):
    es, offs = ctx["es"], ctx["offs"]
    L = ["# Hoja de golpes\n", "Cada fila es una oración de la voz y lo que entra en pantalla con ella.\n"]
    cap = None
    for M in mesas:
        if M["cap"] != cap:
            cap = M["cap"]
            c = next(c for c in ctx["caps"] if c["numero"] == cap)
            L.append("\n## Capítulo %d%s\n\n| Tiempo | La voz dice | Entra en pantalla |\n|---|---|---|" % (cap, " · " + c["titulo"] if c["titulo"] else ""))
        if M["clase"] in PROPIAS:
            L.append("| %s | (sin voz) | %s |" % (VD_mmss(M["ini"]), "Rótulo del capítulo" if M["clase"] == "capitulo" else "Cierre y «Suscríbete»"))
            continue
        ev = eventos_de(ctx, M)
        for i in M["idx"]:
            for sg in segmentos(es[i]):
                if not (sg.get("texto") or "").strip():
                    continue
                a, b = offs[i] + sg["t"], offs[i] + sg["hasta"]
                gs = [g for g in M["golpes"] if a - 0.6 <= g["_t"] < b]
                txt = "; ".join("**%s**: %s" % (g["tipo"], resumen_golpe(g)) for g in gs)
                if not txt:
                    dentro = [e for e in ev if a - 0.6 <= e[0] < b]
                    if any(e[1] == "tablero" for e in dentro):
                        txt = "un paso de la animación ya hecha (%s)" % es[i]["tipo"]
                    elif any(e[1] == "maqueta" for e in dentro):
                        txt = ""
                    elif dentro:
                        txt = "sigue el subrayado o la lista de la pieza anterior"
                txt = "; ".join(x for x in (txt, resumen_maqueta(ctx, M, a - 0.6, b)) if x)
                L.append("| %s | %s | %s |" % (VD_mmss(a), sg["texto"].replace("|", "/"), txt or "—"))
    return "\n".join(L) + "\n"


def resumen_golpe(g):
    t = g["tipo"]
    if t == "foto":
        return "%s («%s»)" % (g.get("foto"), g.get("pie"))
    if t == "recorte":
        return "%s, %s: %s" % (g.get("medio"), g.get("fecha"), (g.get("titular") or g.get("extracto") or "")[:70])
    if t == "documento":
        return g.get("titulo") or g.get("pagina") or ""
    if t == "persona":
        return "%s (%s)" % (g.get("persona"), g.get("cargo") or "")
    if t == "institucion":
        return g.get("nombre") or ""
    if t == "lugar":
        return g.get("rotulo") or g.get("depto") or " → ".join(p.get("nombre", "") for p in g.get("puntos") or [])
    if t == "fecha":
        return " ".join(str(x) for x in (g.get("chico"), g.get("grande")) if x)
    if t == "cifra":
        return "%s %s" % (g.get("valor"), g.get("rotulo"))
    if t == "lista":
        return ", ".join(it.get("texto", "") for it in g.get("items") or [])
    return (g.get("texto") or "")[:70]


DOC_ANCHOS = {"pagina": 1040, "portada": 640, "portada_h": 600, "tab": (44, 700)}


def doc_de(ctx, g):
    """Lo que hace falta para dibujar un documento: la imagen de la página, el recorte que se ve y los renglones a subrayar."""
    trabajo = ctx["trabajo"]
    DW = dict(DOC_ANCHOS, **(ctx.get("doc") or {}))   # los anchos del formato (16:9 por defecto)
    if g.get("pagina"):
        PG = leer(os.path.join(trabajo, "paginas.json"))[g["pagina"]]
        img = pagina_png(trabajo, PG.get("url") or "", int(PG.get("pagina") or 1)) if PG.get("url") else None
        if not img:
            arch = os.path.join(trabajo, PG["archivo"])
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", arch], capture_output=True, text=True).stdout.strip().split(",")
            img = (PG["archivo"], int(r[0]), int(r[1]))
        L = PG.get("lineas") or []
        y0 = max(0.0, min(l[1] for l in L) - 0.12) if L else 0.1
        y1 = min(1.0, max(l[1] + l[3] for l in L) + 0.08) if L else 0.45
        x0, x1 = 0.08, 0.92
        w = DW["pagina"]
        k = w / ((x1 - x0) * img[1])
        tit = g.get("titulo") or ""
        tab_h = 40 + DW["tab"][0] * renglones(tit, DW["tab"][0], DW["tab"][1]) + 16   # la pestaña va abajo: la página se alarga para que no tape lo subrayado
        return {"img": img[0], "w": w, "h": int((y1 - y0) * img[2] * k) + tab_h, "k": k, "x0": x0, "y0": y0, "pw": img[1], "ph": img[2], "lineas": L,
                "tab": ((PG.get("fuente") or "")[:60], tit), "frase": PG.get("frase") or ""}
    po = g.get("portada") or {}
    img = pagina_png(trabajo, po.get("url") or "", int(po.get("pagina") or 1))
    if not img:
        return {"img": None, "w": DW["portada"], "h": DW["portada_h"], "k": 1, "x0": 0, "y0": 0, "pw": DW["portada"], "ph": DW["portada_h"], "lineas": [], "tab": (g.get("kicker") or "", g.get("titulo") or ""), "sub": g.get("subtitulo") or ""}
    x0, x1, y0 = 0.09, 0.91, 0.045
    w = DW["portada"]
    k = w / ((x1 - x0) * img[1])
    return {"img": img[0], "w": w, "h": DW["portada_h"], "k": k, "x0": x0, "y0": y0, "pw": img[1], "ph": img[2], "lineas": [], "tab": (g.get("kicker") or "", g.get("titulo") or ""),
            "sub": g.get("subtitulo") or "", "abajo": True}


# ---------- el acento: qué piezas lo llevan (MV13 del vertical: un solo acento al frente a la vez) ----------
CREMA_TIPOS = ("cifra", "termino", "barra")   # las que el motor sabe dibujar sin acento: `"crema": true` en el golpe


def en_acento(g):
    """Lo que una pieza lleva en el color de acento, leído de sus datos (lo mismo que `dibujar` pinta con `$acento`), o "" si no
    lleva nada. Es la regla Noche «acento = una sola cosa» (referencias/diseno/sistema.md) llevada a la mesa:
      cifra      el valor (y sus `cuadros`)             termino   la nota entera (sin `definicion`; con ella es una ficha de papel)
      barra      la barra destacada y su valor          recorte   el subrayado de `resalta`
      documento  el marcador sobre la página (`pagina`; una `portada` no lleva)
      lista      el chip de `acento` o el `lazo`        red       la `etiqueta` «Según…» o una `clave`
    `"crema": true` en una cifra, una nota o una barra la deja sin acento (el motor la dibuja en crema: CREMA_TIPOS). No cuentan
    las marcas chicas que no se leen como acento (los puntos de un mapa del mundo, la línea de crédito de la pestaña de un
    documento) ni el cuadro (kicker, palabra activa del subtítulo), que no son piezas."""
    t = g.get("tipo")
    if g.get("crema") and t in CREMA_TIPOS:
        return ""
    if t == "cifra":
        return "la cifra «%s»" % g.get("valor")
    if t == "termino" and not g.get("definicion"):
        return "la nota «%s»" % (g.get("texto") or "")[:40]
    if t == "barra":
        bs = [b for b in g.get("barras") or [] if isinstance(b, dict)]
        b = next((b for b in bs if b.get("acento")), bs[-1] if bs else None)
        return "la barra «%s»" % (b or {}).get("etiqueta") if b else ""
    if t == "recorte" and g.get("resalta") and g["resalta"] in (g.get("extracto") or ""):
        return "el subrayado del recorte"
    if t == "documento" and g.get("pagina"):
        return "el marcador del documento"
    if t == "lista":
        n = len([it for it in g.get("items") or [] if isinstance(it, dict)])
        if isinstance(g.get("lazo"), dict) or (isinstance(g.get("acento"), int) and not isinstance(g.get("acento"), bool) and 0 <= g["acento"] < n):
            return "la lista (su %s)" % ("lazo" if isinstance(g.get("lazo"), dict) else "chip de `acento`")
        return ""
    if t == "red" and (g.get("etiqueta") or any(isinstance(n, dict) and n.get("clave") for n in g.get("nodos") or [])):
        return "la jerarquía (su %s)" % ("etiqueta «%s»" % g["etiqueta"] if g.get("etiqueta") else "clave")
    return ""


def peso_acento(g):
    """Cuánto pesa el acento de una pieza: «dato» (el acento ES la cifra: `cifra`, `barra`), «bloque» (una caja entera en
    acento: la nota, el chip de una lista, la etiqueta o la clave de una jerarquía), «marca» (un trazo de marcador sobre papel:
    el subrayado de un recorte, el marcador de un documento, el lazo de una lista) o "" (no lleva acento)."""
    que = en_acento(g)
    if not que:
        return ""
    t = g.get("tipo")
    if t in ("cifra", "barra"):
        return "dato"
    if t in ("recorte", "documento") or (t == "lista" and "lazo" in que):
        return "marca"
    return "bloque"


def acento_compite(a, b):
    """¿Dos piezas en acento al frente BLOQUEAN (MV13 falla) o solo se avisan? Bloquea cuando una es un dato (cifra o barra) y
    la otra es otro dato o un bloque: con una cifra en pantalla el acento es solo suyo (la regla Noche: la cifra, no la cifra y
    su nota). Lo demás (dos notas, una nota junto a un subrayado, una cifra junto a la frase subrayada de la que sale) solo se
    avisa: así salieron los dos pilotos que el usuario aprobó (Bancafé parte 1 y La Línea parte 3: 9 coincidencias de esas y
    ninguna de dato con bloque), y un gate no rechaza la referencia aprobada."""
    pa, pb = peso_acento(a), peso_acento(b)
    return bool(pa and pb) and "dato" in (pa, pb) and "marca" not in (pa, pb)


def acentos_a_la_vez(piezas, fin):
    """MV13 sobre una mesa ya compuesta: las piezas en acento (`en_acento`) que coinciden AL FRENTE. `piezas` = [{g, t, hasta, k}]
    (t = cuando entra; hasta = cuando se repliega o se va, None = sigue hasta `fin`). Una pieza replegada (su compacta va
    atenuada) ya no cuenta. → [(la que entra, [las que seguían al frente en acento])], una entrada por pieza que entra."""
    ac = sorted(((p, en_acento(p["g"])) for p in piezas), key=lambda x: (x[0]["t"], x[0]["k"]))
    ac = [(p, q) for p, q in ac if q]
    out = []
    for i, (b, _) in enumerate(ac):
        antes = [a for a, _ in ac[:i] if (a["hasta"] if a["hasta"] is not None else fin) > b["t"] + 0.05]
        if antes:
            out.append((b, antes))
    return out


GIROS = [-2, 3, -1.5, 2, -3, 1.5, -2.5, 2.5, -1, 3.5, -3.5, 1]


def dibujar(ctx, m, g, x, y, w, h, ex, k, F, usados):
    """Una pieza del plano → su HTML dentro de la mesa `m` (y sus animaciones propias)."""
    t, T = g["tipo"], g["_t"]
    C = ctx["C"]
    giro = g.get("giro", GIROS[k % len(GIROS)])
    ya = bool(g.get("_ya"))
    pid = "%s-p%d" % (m.id, m.k + 1)
    S = ctx["es"][g["_i"]]
    o = ctx["offs"][g["_i"]]

    def t_de(frase, por=None):
        r = buscar(S, frase or "", 0)
        return round(o + S["palabras"][r[1]]["start"], 3) if r else por

    def fin_de(frase, por=None):
        r = buscar(S, frase or "", 0)
        return round(o + S["palabras"][r[2]]["end"], 3) if r else por
    if t == "foto":
        r = F[g["foto"]]
        usados.add(r["archivo"])
        rc, hi, wi = ex["rc"], ex["hi"], w - 28
        tw, th = (r.get("tamano") or [1600, 1000])[:2]
        cw, ch = tw * rc[2], th * rc[3]
        s = max(wi / cw, hi / ch)
        fx, fy = (g.get("pos") or [0.5, 0.4])[:2]
        ix = -(rc[0] * tw * s) - max(0, cw * s - wi) * fx
        iy = -(rc[1] * th * s) - max(0, ch * s - hi) * fy
        cred = (r.get("credito") or "") + (" · %s" % str(r["fecha"])[:4] if r.get("fecha") and str(r["fecha"])[:4] not in (g.get("pie") or "") else "")
        dentro = ('<div class="foto"><div class="im" style="width:%dpx;height:%dpx"><img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx" alt=""></div>'
                  '<div class="pie"><b>%s</b><span data-layout-ignore>%s</span></div></div>' % (wi, hi, r["archivo"], ix, iy, tw * s, th * s, esc(g.get("pie")), esc(cred)))
        m.pieza(T, x, y, w, giro, dentro, ya=ya)
    elif t == "recorte":
        ext = g.get("extracto") or ""
        if g.get("resalta") and g["resalta"] in ext:
            a, b = ext.split(g["resalta"], 1)
            cuerpo = "«%s<span id=\"%s-hl\" class=\"hl\">%s</span>%s»" % (esc(a), pid, esc(g["resalta"]), esc(b))
        else:
            cuerpo = "«%s»" % esc(ext)
        dentro = ('<div class="recorte"><div class="cab"><div class="m cond">%s</div><div class="d" data-layout-ignore>%s</div></div>%s%s</div>'
                  % (esc(g.get("medio")), esc(g.get("fecha")), '<div class="t cond">%s</div>' % esc(g["titular"]) if g.get("titular") else "",
                     '<div class="x">%s</div>' % cuerpo if ext else ""))
        m.pieza(T, x, y, w, giro, dentro, ya=ya)
        if g.get("resalta") and g["resalta"] in ext:
            t0 = max(T + 0.35, t_de(g.get("resalta_dice"), T + 0.5))
            t1 = max(t0 + 0.8, fin_de(g.get("resalta_dice"), t0 + 1.4))
            m.tl.append('tl.fromTo("#%s-hl",{backgroundSize:"0%% 100%%"},{backgroundSize:"100%% 100%%",duration:%.2f,ease:"none"},%.3f);' % (pid, min(t1 - t0, 2.4), m.loc(t0)))
            m.sfx.append((t0, "marcador"))
    elif t in ("persona", "institucion") or (t == "termino" and g.get("definicion")):
        if t == "persona":
            kicker, nombre, rol = g.get("kicker") or "", g.get("persona") or "", g.get("cargo") or ""
            ret = ex.get("ret")
            if ret and not kicker:
                kicker = ""
        elif t == "institucion":
            kicker, nombre, rol, ret = g.get("kicker") or "", g.get("nombre") or "", g.get("rol") or "", None
        else:
            kicker, nombre, rol, ret = g.get("kicker") or "Para entender", g.get("texto") or "", g.get("definicion") or "", None
        cuerpo = ('%s<div class="n cond" style="font-size:%dpx">%s</div>%s%s' % (
            '<div class="k mono">%s</div>' % esc(kicker) if kicker else "", ex.get("px", 78), esc(nombre), '<div class="r">%s</div>' % esc(rol) if rol else "",
            '<div class="f" data-layout-ignore>%s</div>' % esc(g["fuente"]) if g.get("fuente") else ""))
        if ret:
            usados.add(ret["foto"])
            fo = ret.get("foco") or {}
            rr = next((r for r in F.values() if r.get("archivo") == ret["foto"]), {})
            tw, th = (rr.get("tamano") or [800, 800])[:2]
            if fo and "x" in fo:
                s = 210 / max(1.0, fo["w"] * tw * 1.9)
                ix, iy = 105 - (fo["x"] + fo["w"] / 2) * tw * s, 110 - (fo["y"] + fo["h"] / 2) * th * s
            else:
                s = max(210 / tw, 250 / th)
                ix, iy = (210 - tw * s) / 2, (250 - th * s) / 2
            dentro = ('<div class="ficha per"><div class="ret"><img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx" alt=""></div><div>%s</div></div>'
                      % (ret["foto"], ix, iy, tw * s, cuerpo))
        else:
            dentro = '<div class="ficha">%s</div>' % cuerpo
        m.pieza(T, x, y, w, giro, dentro, ya=ya)
    elif t == "lugar":
        if g.get("mapa") == "guatemala":
            D = deptos()
            k_ = VD._plano(g.get("depto") or "")
            sel = next((d for d in D if VD._plano(d[2]) == k_), None) or next((d for d in D if VD._plano(d[2]) == "guatemala"), D[0])
            cx, cy = sel[3]
            dentro = ('<div class="mapa"><svg viewBox="40 40 860 900" width="400" height="418">%s<g id="%s-pin"><circle cx="%.0f" cy="%.0f" r="34" fill="none" stroke="%s" '
                      'stroke-width="9"/><circle cx="%.0f" cy="%.0f" r="13" fill="%s"/></g></svg><div class="cond" style="font-size:40px;padding:12px 4px 2px">%s</div></div>'
                      % ("".join('<path class="%s" d="%s"/>' % ("gt" if d is sel else "tierra", d[0]) for d in D), pid, cx, cy, C["tinta"], cx, cy, C["tinta"],
                         esc(g.get("rotulo") or sel[2])))
            m.pieza(T, x, y, w, giro if abs(giro) <= 3 else 3, dentro, ya=ya)
            m.tl.append('tl.fromTo("#%s-pin",{opacity:0,scale:2.2,transformOrigin:"%.0fpx %.0fpx"},{opacity:1,scale:1,duration:.3,ease:"power3.out"},%.3f);' % (pid, cx, cy, m.loc(T + 0.05)))
        else:
            A = ex["A"]
            pts = A["pts"]
            marcas, anim = "", []
            fs = int(max(30, min(50, 50 * A["w"] / 1150.0)))
            cajas = []
            for j, (nombre, px_, py_) in enumerate(pts):
                der = px_ > A["w"] * 0.55
                ancho_t = len(nombre) * fs * 0.5
                tx = px_ + (-22 if der else 22)
                ops = [py_ + fs * 1.35, py_ - fs * 0.6, py_ + fs * 2.3, py_ - fs * 1.5]
                ty = next((y_ for y_ in ops if fs < y_ < A["h"] - 8 and not any(abs(y_ - cy_) < fs and min(tx, tx - ancho_t if der else tx + ancho_t) < cx1 and
                                                                                 max(tx, tx - ancho_t if der else tx + ancho_t) > cx0 for cx0, cx1, cy_ in cajas)), ops[0])
                cajas.append((min(tx, tx - ancho_t if der else tx + ancho_t), max(tx, tx - ancho_t if der else tx + ancho_t), ty))
                marcas += ('<g id="%s-pt%d"><circle cx="%.1f" cy="%.1f" r="13" fill="%s" stroke="%s" stroke-width="5"/><text x="%.0f" y="%.0f" font-size="%d" text-anchor="%s">%s</text></g>'
                           % (pid, j, px_, py_, C["acento"], C["tinta"], tx, ty, fs, "end" if der else "start", esc(nombre)))
                tj = t_de(nombre, T + 0.25 + 0.5 * j) if j else T
                anim.append((j, max(T + 0.1, tj)))
            ruta = ""
            if g.get("ruta") and len(pts) >= 2:
                d = "M%.1f %.1f" % (pts[0][1], pts[0][2])
                for a, b in zip(pts, pts[1:]):
                    d += " Q%.1f %.1f %.1f %.1f" % ((a[1] + b[1]) / 2, min(a[2], b[2]) - abs(b[1] - a[1]) * 0.22, b[1], b[2])
                ruta = ('<path id="%s-ruta" d="%s" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="110"/>'
                        % (pid, d, C["tinta"]))
            dentro = ('<div class="mapa"><svg viewBox="0 0 %d %d" width="%d" height="%d"><path class="tierra" d="%s"/><path class="gt" d="%s"/>%s%s</svg></div>'
                      % (A["w"], A["h"], A["w"], A["h"], A["tierra"], A["gt"], ruta, marcas))
            m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
            ult = max(t_ for _, t_ in anim)
            if ruta:
                t0 = anim[1][1] - 0.6 if len(anim) > 1 else T + 0.2
                m.tl.append('tl.fromTo("#%s-ruta",{strokeDashoffset:110},{strokeDashoffset:0,duration:%.2f,ease:"power1.inOut"},%.3f);' % (pid, max(0.6, ult - t0), m.loc(max(T, t0))))
                m.sfx.append((max(T, t0), "marcador"))
            for j, tj in anim[1:]:
                m.tl.append('tl.fromTo("#%s-pt%d",{opacity:0,scale:.6,transformOrigin:"%.0fpx %.0fpx"},{opacity:1,scale:1,duration:.3,ease:"back.out(2)"},%.3f);'
                            % (pid, j, pts[j][1], pts[j][2], m.loc(tj)))
    elif t == "fecha":
        if g.get("estilo") == "calendario":
            dentro = '<div class="cal"><div class="top cond">%s</div><div class="mes cond">%s</div><div class="sub mono">%s</div></div>' % (esc(g.get("arriba")), esc(g.get("grande")), esc(g.get("chico")))
        else:
            dentro = '<div class="fecha"><div class="in"><div class="s mono">%s</div><div class="b cond">%s</div></div></div>' % (esc(g.get("chico") or "año"), esc(str(g.get("grande"))))
        m.pieza(T, x, y, w, -5 if k % 2 else 4, dentro, sfx="sello", ya=ya)
    elif t == "cifra":
        v = str(g.get("valor"))
        cu = int(g.get("cuadros") or 0)
        dentro = ('<div class="cifra%s"><div id="%s-v" class="v cond" style="font-size:%dpx">%s</div><div class="l cond">%s</div>%s%s</div>'
                  % (" cr" if g.get("crema") else "", pid, ex["px"], esc(v), esc(g.get("rotulo")), '<div class="cuad">%s</div>' % "".join('<i id="%s-c%d"></i>' % (pid, i) for i in range(cu)) if cu else "",
                     '<div class="f" data-layout-ignore>%s</div>' % esc(g["fuente"]) if g.get("fuente") else ""))
        mm = re.match(r"^(\D*)(\d[\d,]*)(.*)$", v)
        cuenta = g.get("cuenta") if isinstance(g.get("cuenta"), int) and g.get("cuenta") > 3 and mm else None
        m.pieza(T, x, y, w, giro, dentro, sfx=None if cuenta else "impacto", ya=ya)
        if cuenta:
            t1 = max(T + 0.7, min(g["_fin"], T + 1.5))
            m.tl.append('(function(){const o={v:0},el=document.querySelector("#%s-v");tl.fromTo(o,{v:0},{v:%d,duration:%.2f,ease:"power2.out",onUpdate:function(){'
                        'el.textContent=%s+Math.round(o.v).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,",")+%s;}},%.3f);})();'
                        % (pid, cuenta, t1 - T, json.dumps(mm.group(1)), json.dumps(mm.group(3)), m.loc(T)))
            m.sfx.append((t1, "tic"))
        for i in range(cu):
            m.tl.append('tl.fromTo("#%s-c%d",{opacity:0},{opacity:1,duration:.08},%.3f);' % (pid, i, m.loc(T + i * 0.05)))
    elif t == "termino":
        m.pieza(T, x, y, w, giro, '<div class="nota%s"><div class="cond">%s</div></div>' % (" cr" if g.get("crema") else "", esc(g.get("texto"))), sfx="papel", ya=ya)
    elif t == "cita":
        # la cita entra atenuada y cada palabra se entinta cuando la voz la lee (la voz dice quién habla y luego la lee)
        pal = (g.get("texto") or "").split()
        cuerpo = "«" + " ".join('<span id="%s-w%d" class="w">%s</span>' % (pid, j, esc(w)) for j, w in enumerate(pal)) + "»"
        dentro = ('<div class="cita"><div class="q">%s</div><div class="a cond">%s</div>%s</div>'
                  % (cuerpo, esc(g.get("autor")), '<div class="c">%s</div>' % esc(g["cargo"]) if g.get("cargo") else ""))
        m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
        t0, t1 = lectura(ctx, g)
        if t0 is None:
            t0, t1 = T + 0.4, T + 0.4 + 0.28 * len(pal)
        T_ = toks_de(S)
        cur = (buscar(S, " ".join(pal[:3]), 0) or (0, 0, 0))[0]
        for j, w in enumerate(pal):
            q = VD._plano(w).split()
            tj = None
            if q:
                for c in range(cur, min(len(T_), cur + 8)):
                    if T_[c][0] == q[0]:
                        tj, cur = o + S["palabras"][T_[c][1]]["start"], c + len(q)
                        break
            if tj is None:
                tj = t0 + (t1 - t0) * j / max(1, len(pal))
            m.tl.append('tl.fromTo("#%s-w%d",{color:"%s"},{color:"%s",duration:.18,ease:"none"},%.3f);' % (pid, j, "#a89a80", "#1f160d", m.loc(max(tj, T + 0.3))))
        m.sfx.append((max(t0, T + 0.3), "marcador"))
    elif t == "documento" and ex.get("texto"):
        D = ex["D"]
        dentro = ('<div class="recorte doc-txt"><div class="cab"><div class="m cond" style="font-size:30px">Documento</div><div class="d" data-layout-ignore>%s</div></div>'
                  '<div class="t cond" style="font-size:50px">%s</div><div class="x" style="font-size:34px">«<span id="%s-hl" class="hl">%s</span>»</div></div>'
                  % (esc(D["tab"][0])[:44], esc(g.get("titulo") or D["tab"][0]), pid, esc(D["frase"])))
        m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
        t0 = max(T + 0.4, t_de(g.get("lee"), T + 0.6))
        m.tl.append('tl.fromTo("#%s-hl",{backgroundSize:"0%% 100%%"},{backgroundSize:"100%% 100%%",duration:1.6,ease:"none"},%.3f);' % (pid, m.loc(t0)))
        m.sfx.append((t0, "marcador"))
    elif t == "documento":
        D, kk = ex["D"], ex["k"]
        e = D["k"] * kk
        marcas = ""
        for j, (lx, ly, lw, lh) in enumerate(D["lineas"]):
            marcas += ('<div id="%s-l%d" class="marca" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx"></div>'
                       % (pid, j, (lx - D["x0"]) * D["pw"] * e - 4, (ly - D["y0"]) * D["ph"] * e - 3, lw * D["pw"] * e + 8, lh * D["ph"] * e + 6))
        if D.get("img"):
            usados.add(D["img"])
        tab = ('<div class="tab" style="%s"><div class="mono" data-layout-ignore>%s</div><div class="cond">%s</div>%s</div>'
               % ("bottom:0;left:0;right:0" if D.get("abajo") else "bottom:0;right:0", esc(D["tab"][0]), esc(D["tab"][1]),
                  '<div class="cond" style="font-size:30px;color:%s;margin-top:4px">%s</div>' % (C["papel2"], esc(D["sub"])) if D.get("sub") else "")
               if D["tab"][0] or D["tab"][1] else "")
        img = ('<img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx" alt="">' % (D["img"], -D["x0"] * D["pw"] * e, -D["y0"] * D["ph"] * e, D["pw"] * e)) if D.get("img") else ""
        dentro = '<div class="doc" style="width:%dpx;height:%dpx">%s%s%s</div>' % (w, h, img, marcas, tab)
        m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
        if D["lineas"]:
            t0 = max(T + 0.4, t_de(g.get("lee"), T + 0.6))
            t1 = max(t0 + 1.0, fin_de(g.get("lee_hasta") or g.get("lee"), t0 + 2.2 * len(D["lineas"])))
            largo = [l[2] for l in D["lineas"]]
            acum = 0.0
            for j, lw in enumerate(largo):
                d = (t1 - t0) * lw / sum(largo)
                m.tl.append('tl.fromTo("#%s-l%d",{scaleX:0,transformOrigin:"0%% 50%%"},{scaleX:1,duration:%.2f,ease:"none"},%.3f);' % (pid, j, d, m.loc(t0 + acum)))
                m.sfx.append((t0 + acum, "marcador"))
                acum += d
    elif t == "lista":
        items = [it for it in g.get("items") or [] if isinstance(it, dict)]
        ult = T
        for j, it in enumerate(items):
            tj = T if j == 0 else max(ult + 0.22, t_de(it.get("dice"), ult + 0.5))
            ult = tj
            cx = x + int((20 if j % 2 == 0 else 20 + ex.get("corr", 200)) * m.f)
            m.pieza(tj, cx, y + int((20 + j * 100) * m.f), ex.get("ficha_w", 260), [-3, 4, 2, -3, 3, -2][j % 6],
                    '<div class="chip%s"><div class="cond">%s</div></div>' % (" ac" if g.get("acento") == j else "", esc(it.get("texto"))), sombra=False,
                    sfx="papel" if j == 0 else None, velo=False, ya=ya and j == 0)
        if isinstance(g.get("lazo"), dict):
            tl_ = max(ult + 0.3, t_de(g["lazo"].get("dice"), ult + 0.6))
            hh = 100 * len(items) + 60
            sid = "%s-lz%d" % (m.id, m.k)
            m.html.append('<svg id="%s" class="pz" style="left:%dpx;top:%dpx;z-index:60" width="%d" height="%d" viewBox="0 0 560 %d" preserveAspectRatio="none" data-layout-ignore>'
                          '<path id="%s-p" d="M70 30 C210 -12 480 6 530 %d C585 %d 525 %d 335 %d C150 %d 22 %d 22 %d C22 %d 36 60 70 30" fill="none" stroke="%s" '
                          'stroke-width="7" stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="110"/></svg>'
                          % (sid, x - int(30 * m.f), y - int(26 * m.f), int((w + 60) * m.f), int((hh + 20) * m.f), hh + 20, sid, int(hh * .28), int(hh * .6), int(hh * .94), hh, hh + 8, int(hh * .88), int(hh * .52), int(hh * .3), C["acento"]))
            m.tl.append('tl.fromTo("#%s-p",{strokeDashoffset:110},{strokeDashoffset:0,duration:.8,ease:"power1.inOut"},%.3f);' % (sid, m.loc(tl_)))
            m.sfx.append((tl_, "marcador"))
            m.extra.append("#" + sid)


# ---------- la maqueta 3D: una mesa con un render 3D de la situación (scripts/maqueta3d.py en modo pieza) ----------
def sets_maqueta():
    d = os.path.join(RAIZ, "design", "sets3d")
    return sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x, "fuente.json"))) if os.path.isdir(d) else []


def estilos_maqueta():
    """El catálogo de estilos de la maqueta: {id: {motor, cuando, …}} (design/sets3d/estilos.json)."""
    try:
        return {e["id"]: e for e in leer(os.path.join(RAIZ, "design", "sets3d", "estilos.json"))["estilos"]}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def motores_maqueta():
    """Los motores con los que la maqueta renderiza hoy: los que declara scripts/maqueta3d.py (`MOTORES`); si no los declara
    (o no carga), three.js. El catálogo de estilos dice el motor de cada uno."""
    try:
        import maqueta3d
        return tuple(getattr(maqueta3d, "MOTORES", MAQUETA_MOTORES))
    except Exception:
        return MAQUETA_MOTORES


def lugares_maqueta(sid):
    """Los lugares de un set: {id: {nombre, lon, lat, …}} (design/sets3d/<set>/lugares.json)."""
    try:
        return leer(os.path.join(RAIZ, "design", "sets3d", sid or "", "lugares.json"))["lugares"]
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def pie_maqueta(q):
    """La atribución de los geodatos que una maqueta USA (fuente.json del set → capas[].atribucion): el relieve siempre, las
    fallas y la frontera si son piezas, los lugares si hay luces, rutas, marcas o un lugar por su id. Va dentro del clip, al pie."""
    try:
        d = leer(os.path.join(RAIZ, "design", "sets3d", q.get("set") or "", "fuente.json"))
    except (OSError, ValueError):
        return ""
    capas = d.get("capas") if isinstance(d.get("capas"), dict) else {}
    tipos = {p.get("tipo") for p in q.get("piezas") or [] if isinstance(p, dict)}
    por_id = bool(q.get("marcas")) or any(isinstance(x.get(k), str) for grupo in ("camara", "eventos") for x in q.get(grupo) or [] if isinstance(x, dict)
                                          for k in ("mira", "lugar", "centro", "desde", "en"))
    usa = ["relieve"] + [k for k, si in (("fallas", "falla" in tipos), ("frontera", "frontera" in tipos), ("lugares", bool(tipos & {"luces", "ruta"}) or por_id)) if si]
    partes = [capas[k]["atribucion"] for k in usa if isinstance(capas.get(k), dict) and capas[k].get("atribucion")]
    return " · ".join(partes) or d.get("pie") or ""


def credito_maqueta(q):
    """El pie del marco de una maqueta: la atribución de sus geodatos y, solo si el bloque lo pide (`aviso`), un aviso
    como «Maqueta · no a escala» o «Traza esquemática». Lo dibuja la mesa (el anfitrión), a su tamaño de crédito, no el
    clip: el contrato del modo pieza deja la atribución al anfitrión."""
    return " · ".join(x for x in (q["aviso"] if isinstance(q.get("aviso"), str) else MAQUETA_AVISO, q["pie"] if isinstance(q.get("pie"), str) else pie_maqueta(q)) if x)


def credito_maqueta_alto(q, ancho, px):
    """(renglones, alto en px) del pie del marco con letra mono de `px` en un ancho dado."""
    n = max(1, -(-len(credito_maqueta(q)) // max(8, int(ancho / (px * 0.605)))))
    return n, int(n * px * 1.3) + 12


def maqueta_tiempos(ctx, q, claves, nom):
    """Los `dice` de la maqueta de una mesa → segundos del video. Cada clave de cámara, evento y marca recibe `_t` (y `_fin`;
    `_hasta` con `hasta_dice`): el `dice` se busca en la voz de las escenas de la mesa, en orden (o en su `escena`; `vez: N`
    = la N.ª vez que se dice). Sin `dice`, al empezar la mesa. → (maqueta resuelta o None, fallas)."""
    if not isinstance(q, dict):
        return None, ["YT20 %s: `maqueta` es un objeto {set, estilo, protagonista, piezas, camara, eventos, marcas}" % nom]
    es, offs, f = ctx["es"], ctx["offs"], []
    o0 = offs[ctx["por_clave"][claves[0]]]

    def donde(x, campo, que, desde=None):
        frase = (x.get(campo) or "").strip()
        if x.get("escena") and x["escena"] not in claves:
            f.append("YT21 %s %s: su escena «%s» no es de esta mesa" % (nom, que, x["escena"]))
            return None
        vez, n = (int(x["vez"]) if campo == "dice" and isinstance(x.get("vez"), int) and x["vez"] > 0 else 1), 0
        for c in ([x["escena"]] if x.get("escena") else claves):
            i = ctx["por_clave"][c]
            S, j = es[i], 0
            while True:
                r = buscar(S, frase, j)
                if not r:
                    break
                j = r[0] + 1
                a, b = offs[i] + S["palabras"][r[1]]["start"], offs[i] + S["palabras"][r[2]]["end"]
                if desde is not None and a < desde - 0.01:
                    continue
                n += 1
                if n >= vez:
                    return round(a, 3), round(b, 3)
        f.append("YT21 %s %s: la voz de %s no dice «%s»%s: `%s` son palabras literales de la voz de esta mesa"
                 % (nom, que, ", ".join(claves), frase, " %d veces" % vez if vez > 1 else " después de su `dice`" if desde is not None else "", campo))
        return None

    out = dict(q)
    for grupo, uno in (("camara", "cámara"), ("eventos", "evento"), ("marcas", "marca")):
        lista = []
        for j, x in enumerate(q.get(grupo) or [] if isinstance(q.get(grupo) or [], list) else []):
            if not isinstance(x, dict):
                continue
            x = dict(x)
            que = "%s %d" % (uno, j + 1)
            if (x.get("dice") or "").strip() and not (grupo == "camara" and j == 0):
                r = donde(x, "dice", que)
                if r:
                    x.update(_t=r[1] if grupo == "camara" and x.get("al") == "fin" else r[0], _fin=r[1])
                else:
                    x.update(_t=None, _falla=True)
            elif grupo == "camara" and j and x.get("al") == "fin":
                x.update(_t=None, _al_fin=True)   # sin `dice` y `al: "fin"`: el encuadre al que la cámara llega cuando termina la mesa
            elif grupo == "camara" and j:
                f.append("YT21 %s %s: falta `dice` (las palabras de la voz con las que la cámara llega a ese encuadre; o `\"al\": \"fin\"` "
                         "para que llegue al terminar la mesa)" % (nom, que))
                x.update(_t=None, _falla=True)
            else:
                x.update(_t=round(o0, 3), _fin=round(o0, 3))
            if x.get("hasta_dice") and x.get("_t") is not None:
                r = donde(x, "hasta_dice", que, desde=x["_t"])
                if r:
                    x["_hasta"] = r[1]
                else:
                    x["_falla"] = True
            lista.append(x)
        out[grupo] = lista
    out["_fallas"] = len(f)
    return out, f


def entradas_maqueta(ctx, M):
    """Lo que ENTRA en una maqueta y cuándo: [(segundo del video, 'camara'|'marca'|tipo de evento, texto para la hoja)]."""
    q, out = M["maqueta"], []

    def lugar(v):
        return v if isinstance(v, str) else "(%s)" % ", ".join(str(x) for x in v) if isinstance(v, (list, tuple)) else ""
    for j, c in enumerate(q.get("camara") or []):
        if c.get("_t") is not None and not c.get("_falla"):
            out.append((c["_t"], "camara", "la cámara %s %s" % ("abre en" if j == 0 else "llega a", lugar(c.get("mira")))))
    for x in q.get("eventos") or []:
        if x.get("_t") is not None and not x.get("_falla"):
            sobre = x.get("lugar") or x.get("pieza") or x.get("centro") or x.get("desde")
            out.append((x["_t"], x.get("tipo") or "evento", "%s%s" % (x.get("tipo"), " (%s)" % lugar(sobre) if sobre else "")))
    for k in q.get("marcas") or []:
        if k.get("_t") is not None and not k.get("_falla"):
            out.append((k["_t"], "marca", "marca «%s»" % (k.get("texto") or "")))
    return sorted(out, key=lambda e: e[0])


def resumen_maqueta(ctx, M, a, b):
    """Para la hoja de golpes: lo que pasa en la maqueta de la mesa entre dos segundos."""
    if M.get("clase") != "maqueta":
        return ""
    xs = [txt for t, _, txt in entradas_maqueta(ctx, M) if a <= t < b]
    return "**maqueta 3D** (%s): %s" % (M["maqueta"].get("estilo"), "; ".join(xs)) if xs else ""


def paleta_maqueta(ctx):
    return (ctx.get("st") or {}).get("paleta") or (ctx.get("Y") or {}).get("paleta") or (ctx.get("E") or {}).get("paleta")


def maqueta_json(ctx, M, fps=FPS):
    """El maqueta.json de una mesa (referencias/diseno/maqueta3d.md, modo pieza): los segundos son relativos al inicio de la
    mesa y dura lo que la mesa; la paleta es la del video; va sin `capa`: el golpe de arriba, las cifras, los subtítulos y el
    pie con la atribución de los geodatos (`credito_maqueta`) son de la mesa."""
    q, ini = M["maqueta"], M["ini"]
    D = round(M["fin"] - M["ini"], 3)

    def limpio(x):
        return {k: v for k, v in x.items() if k not in MAQUETA_SOLO_PLANO and not k.startswith("_")}

    def t_de(t):
        return round(min(max(0.0, t - ini), D), 3)
    cam, ev, mk = [], [], []
    for j, c in enumerate(q.get("camara") or []):
        if c.get("_falla"):
            continue
        cam.append(dict(limpio(c), t=0.0 if j == 0 else round(max(0.0, D - 0.2), 3) if c.get("_al_fin") else t_de(c["_t"])))
    for x in q.get("eventos") or []:
        if x.get("_falla") or x.get("_t") is None:
            continue
        t = t_de(x["_t"] - float(x.get("adelanto") or 0.0))
        dur = float(x["dur"]) if isinstance(x.get("dur"), (int, float)) else (t_de(x["_hasta"] + 0.3) - t if x.get("_hasta") is not None else 2.0)
        ev.append(dict(limpio(x), t=t, dur=round(max(0.2, min(dur, D - t)), 3)))
    for k in q.get("marcas") or []:
        if k.get("_falla") or k.get("_t") is None:
            continue
        t = t_de(k["_t"] - LEAD)
        hasta = t + float(k["dura"]) if isinstance(k.get("dura"), (int, float)) else t_de(k["_hasta"] + 0.4) if k.get("_hasta") is not None else D
        mk.append(dict(limpio(k), t=t, hasta=round(min(max(hasta, t + 0.2), D), 3)))
    mundo = {"set": q.get("set"), "lugares": q.get("lugares") or {}, "piezas": q.get("piezas") or []}
    if isinstance(q.get("exageracion"), (int, float)):
        mundo["exageracion"] = q["exageracion"]
    mj = {"version": 1, "estilo": q.get("estilo"), "paleta": paleta_maqueta(ctx), "fps": min(MAQUETA_FPS[1], max(MAQUETA_FPS[0], int(fps))), "duracion_s": D, "mundo": mundo,
          "camara": cam, "eventos": sorted(ev, key=lambda x: x["t"]), "marcas": mk}
    if q.get("protagonista"):
        mj["protagonista"] = q["protagonista"]
    return mj


def maqueta_ruta(ctx, M):
    return os.path.join(ctx["trabajo"], "maquetas", M["id"], "maqueta.json")


def maqueta_huella(ctx, mj):
    """La huella de un maqueta.json y su lienzo (sin los fps: como los tableros, un clip a otros fps se rehace con --todo)."""
    return hashlib.sha1(("v1|%dx%d|" % tuple(regla(ctx, "MAQUETA_LIENZO")) + json.dumps({k: v for k, v in mj.items() if k != "fps"}, sort_keys=True,
                                                                                    ensure_ascii=False)).encode("utf-8")).hexdigest()[:16]


def nombre_mesa(ctx, M):
    es = ctx["es"]
    return "%s E%s" % (M["id"], "–".join(str(es[i]["n"]) for i in (M["idx"][0], M["idx"][-1])) if len(M["idx"]) > 1 else es[M["idx"][0]]["n"])


def revisar_maqueta(ctx, M, nom, respaldado):
    """Los gates de la maqueta de UNA mesa → (fallas, avisos). YT20 forma · YT21 concordancia con la voz (lo demás lo vio
    `maqueta_tiempos`) · YT23 carga · YT24 `maqueta3d.py check --pieza` (los gates M3D del motor, reenviados) · YT16 los
    números de una marca. Sobre los datos: nada de píxeles."""
    q, f, av = M["maqueta"], [], []
    E = estilos_maqueta()
    con_motor = [k for k, e in E.items() if e.get("motor") in motores_maqueta()]
    extra = sorted(k for k in q if not k.startswith("_") and k not in ("set", "estilo", "protagonista", "piezas", "lugares", "camara", "eventos", "marcas", "exageracion", "pie", "aviso"))
    if extra:
        f.append("YT20 %s: la maqueta no lleva %s: el golpe de arriba es el `titulo` de la mesa, las cifras son golpes y los subtítulos los pone la mesa "
                 "(van: set, estilo, protagonista, piezas, lugares, camara, eventos, marcas)" % (nom, ", ".join("`%s`" % k for k in extra)))
    if q.get("set") not in sets_maqueta():
        f.append("YT20 %s: el set «%s» no existe en design/sets3d/ (hay: %s; uno nuevo se arma con scripts/build_set3d.py)" % (nom, q.get("set"), ", ".join(sets_maqueta()) or "ninguno"))
    if q.get("estilo") not in E:
        f.append("YT20 %s: el estilo «%s» no está en el catálogo (design/sets3d/estilos.json); van: %s" % (nom, q.get("estilo"), " · ".join(con_motor)))
    elif q["estilo"] not in con_motor:
        f.append("YT20 %s: el estilo «%s» es de motor %s, que aún no renderiza; van: %s" % (nom, q["estilo"], E[q["estilo"]].get("motor"), " · ".join(con_motor)))
    pz = q.get("piezas")
    if not (isinstance(pz, list) and pz and all(isinstance(p, dict) and p.get("id") and p.get("tipo") for p in pz)):
        f.append("YT20 %s: `piezas` son una o más {id, tipo, …}: lo que hay sobre el mundo (los tipos: maqueta3d.py catalogo --para realizador)" % nom)
        pz = []
    if q.get("protagonista") and q["protagonista"] not in {p["id"] for p in pz}:
        f.append("YT20 %s: `protagonista` («%s») es el id de una de sus piezas (%s): la única que va en el acento"
                 % (nom, q["protagonista"], ", ".join(p["id"] for p in pz) or "no hay"))
    cam = q.get("camara") or []
    if not cam:
        f.append("YT20 %s: `camara` son una o más claves {mira, dist_km, azimut, elevacion}; la primera sin `dice`: es el encuadre con que abre la mesa" % nom)
    elif (cam[0].get("dice") or "").strip() or cam[0].get("al"):
        f.append("YT20 %s cámara 1: la primera clave va sin `dice` (ni `al`): es el encuadre con que abre la mesa; el movimiento empieza en la segunda" % nom)
    for j, c in enumerate(cam):
        faltan = [k for k in ("mira", "dist_km", "elevacion") if c.get(k) is None]
        if faltan:
            f.append("YT20 %s cámara %d: falta %s (mira = un lugar del set o [lon, lat]; dist_km = del ojo al punto; elevacion = grados sobre el horizonte)"
                     % (nom, j + 1, ", ".join("`%s`" % k for k in faltan)))
    for j, x in enumerate(q.get("eventos") or []):
        if not x.get("tipo") or not (isinstance(x.get("dur"), (int, float)) or x.get("hasta_dice")):
            f.append("YT20 %s evento %d: lleva `tipo` y `dur` (segundos) o `hasta_dice` (las palabras con las que termina)" % (nom, j + 1))
    for j, k in enumerate(q.get("marcas") or []):
        if not k.get("lugar") or not (k.get("texto") or "").strip():
            f.append("YT20 %s marca %d: lleva `lugar` (del set, de `lugares` o [lon, lat]) y `texto` (lo que dice el pin)" % (nom, j + 1))
            continue
        sin = sorted(x for x in numeros("%s %s" % (k.get("texto") or "", k.get("sub") or "")) if not respaldado(x))
        if sin:
            f.append("YT16 %s marca %d («%s»): «%s» no lo dice la voz, no está en los hechos de la mesa ni tiene respaldo en los datos" % (nom, j + 1, k["texto"], ", ".join(sin)))
    # YT21: la cámara llega a sus encuadres en el orden en que la voz los dice
    ts = [(j + 1, c["_t"]) for j, c in enumerate(cam) if c.get("_t") is not None and not c.get("_falla")]
    for (ja, ta), (jb, tb) in zip(ts, ts[1:]):
        if tb - ta < 1.0 / FPS:
            f.append("YT21 %s cámara %d: llega a los %.1f s y la clave %d a los %.1f s: las claves van en el orden en que la voz las dice (y no dos en la misma palabra)"
                     % (nom, jb, tb, ja, ta))
    # YT23: carga
    d = M["fin"] - M["ini"]
    lo, hi = regla(ctx, "MAQUETA_MIN_S"), regla(ctx, "MESA_S")[1]
    if not lo <= d <= hi:
        f.append("YT23 %s: la mesa de la maqueta dura %.1f s; va de %.0f a %.0f s (%s)" % (
            nom, d, lo, hi, "una maqueta corta no se entiende: súmale la escena vecina, o cuenta eso con piezas" if d < lo else "pártela: la maqueta para una parte y piezas para lo demás"))
    n = sum(1 for g in M["golpes"] if not g.get("_acto"))
    if n > regla(ctx, "MAQUETA_GOLPES"):
        f.append("YT23 %s: %d piezas con la maqueta (máximo %d): la maqueta es lo que se mira; lo demás va en otra mesa" % (nom, n, regla(ctx, "MAQUETA_GOLPES")))
    # YT24: los gates del motor (M3D), sobre el maqueta.json ya con sus segundos
    if not f and not q.get("_fallas"):
        ruta = maqueta_ruta(ctx, M)
        escribir(ruta, maqueta_json(ctx, M))
        W, H = regla(ctx, "MAQUETA_LIENZO")
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "maqueta3d.py"), "check", ruta, "--pieza", "--lienzo", "%dx%d" % (W, H)],
                           cwd=RAIZ, capture_output=True, text=True)
        desde = " (sus segundos cuentan desde el inicio de la mesa, %s; el json: %s)" % (VD_mmss(M["ini"]), rel(ruta))
        n0 = len(f)
        for ln in r.stdout.splitlines():
            ln = ln.strip()
            if ln.startswith("FALLA "):
                f.append("YT24 %s: %s%s" % (nom, ln[6:], desde))
            elif ln.startswith("aviso · "):
                av.append("YT24 %s: %s" % (nom, ln[8:]))
        if r.returncode and len(f) == n0:
            f.append("YT24 %s: `maqueta3d.py check --pieza` no corrió: %s" % (nom, " ".join((r.stderr or r.stdout).split())[-240:]))
    return f, av


def revisar_maquetas(ctx, mesas):
    """YT22 (un solo estilo de maqueta por video) y YT23 (cuántas maquetas caben en un video y en un capítulo) → fallas."""
    ms = [M for M in mesas if M["clase"] == "maqueta"]
    f = []
    tope, tope_cap = regla(ctx, "MAQUETAS_MAX"), regla(ctx, "MAQUETAS_CAP_MAX")
    por_cap = {}
    for k, M in enumerate(ms):
        nom = nombre_mesa(ctx, M)
        e0, e = ms[0]["maqueta"].get("estilo"), M["maqueta"].get("estilo")
        if e != e0:
            f.append("YT22 %s: su maqueta va en estilo «%s» y la primera del video (%s), en «%s»: un solo estilo de maqueta por video" % (nom, e, ms[0]["id"], e0))
        if k >= tope:
            f.append("YT23 %s: es la maqueta n.º %d del video (máximo %d): la maqueta es para cuando el lugar es la información; lo demás, con piezas" % (nom, k + 1, tope))
        por_cap[M["cap"]] = por_cap.get(M["cap"], 0) + 1
        if tope_cap and por_cap[M["cap"]] > tope_cap and k < tope:
            f.append("YT23 %s: es la maqueta n.º %d del capítulo %d (máximo %d por capítulo)" % (nom, por_cap[M["cap"]], M["cap"], tope_cap))
    return f


def clip_maqueta(ctx, M):
    """El clip ya renderizado de la maqueta de una mesa → (ruta, al día). «Al día» = su huella es la del plano de ahora."""
    cd = os.path.join(ctx["trabajo"], regla(ctx, "MAQUETA_CARPETA"))
    ruta = os.path.join(cd, M["id"] + ".mp4")
    try:
        h = leer(os.path.join(cd, "huellas.json")).get(M["id"]) or {}
    except (OSError, ValueError):
        h = {}
    return ruta, os.path.exists(ruta) and h.get("huella") == maqueta_huella(ctx, maqueta_json(ctx, M))


def efectos_maqueta(ctx, M):
    """Los efectos de sonido de una maqueta, en segundos del video: [(t, id)] (lo que escribió el render, o los `sfx` del plano)."""
    fe = os.path.join(ctx["trabajo"], regla(ctx, "MAQUETA_CARPETA"), M["id"] + ".efectos.json")
    try:
        lista = leer(fe)
    except (OSError, ValueError):
        mj = maqueta_json(ctx, M)
        lista = [[o["t"], o["sfx"]] for o in mj["eventos"] + mj["marcas"] if o.get("sfx")]
    return [(round(M["ini"] + float(t), 3), i) for t, i in lista]


def grabar_maquetas(ctx, mesas, fps=FPS, todo=False):
    """Los clips de las mesas con maqueta 3D: TRABAJO/maquetas/<mesa>/maqueta.json → `maqueta3d.py pieza` → TRABAJO/<carpeta>/
    <mesa>.mp4, del lienzo del formato y de la duración exacta de la mesa (con un cuadro clave por segundo: HyperFrames busca
    dentro del clip) y <mesa>.efectos.json. Solo se renderiza la que cambió (huellas.json; un clip se reusa por su contenido
    aunque la mesa cambie de número). MESA_RENDER=0 (maquetas de prueba): un doble del tamaño y la duración exactos, sin
    llamar al motor; un doble nunca cuenta como render. → 0 ok · 1 falla."""
    trabajo = ctx["trabajo"]
    W, H = regla(ctx, "MAQUETA_LIENZO")
    cd = os.path.join(trabajo, regla(ctx, "MAQUETA_CARPETA"))
    ms = [M for M in mesas if M["clase"] == "maqueta"]
    for d in glob.glob(os.path.join(trabajo, "maquetas", "*")):   # lo de una mesa que ya no lleva maqueta (o cambió de número)
        if os.path.basename(d) not in {M["id"] for M in ms}:
            shutil.rmtree(d, ignore_errors=True)
    if not ms:
        shutil.rmtree(cd, ignore_errors=True)
        return 0
    os.makedirs(cd, exist_ok=True)
    fh = os.path.join(cd, "huellas.json")
    antes = leer(fh) if os.path.exists(fh) else {}
    doble = os.environ.get("MESA_RENDER") == "0"
    viejos = {v.get("huella"): (mid, v) for mid, v in antes.items() if os.path.exists(os.path.join(cd, mid + ".mp4")) and (doble or not v.get("doble"))}
    tmp = os.path.join(cd, ".reuso")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    ahora, faltan = {}, []
    for M in ms:
        mj = maqueta_json(ctx, M, fps)
        escribir(maqueta_ruta(ctx, M), mj)
        h = maqueta_huella(ctx, mj)
        if h in viejos and not todo:
            mid, v = viejos[h]
            for ext in (".mp4", ".efectos.json"):
                if os.path.exists(os.path.join(cd, mid + ext)):
                    shutil.copy2(os.path.join(cd, mid + ext), os.path.join(tmp, M["id"] + ext))
            ahora[M["id"]] = dict(v)
        else:
            faltan.append((M, mj, h))
    for g in glob.glob(os.path.join(cd, "*.mp4")) + glob.glob(os.path.join(cd, "*.efectos.json")):
        os.remove(g)
    for g in glob.glob(os.path.join(tmp, "*")):
        os.replace(g, os.path.join(cd, os.path.basename(g)))
    os.rmdir(tmp)
    escribir(fh, ahora)
    for M, mj, h in faltan:
        dst = os.path.join(cd, M["id"] + ".mp4")
        D, fps = mj["duracion_s"], mj["fps"]
        if doble:
            VD.ff("-f", "lavfi", "-i", "color=c=0x14100d:s=%dx%d:r=%d:d=%.4f" % (W, H, int(fps), D), "-g", str(int(fps)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", dst)
            escribir(dst[:-4] + ".efectos.json", sorted([o["t"], o["sfx"]] for o in mj["eventos"] + mj["marcas"] if o.get("sfx")))
        else:
            crudo = os.path.join(trabajo, "maquetas", M["id"], "pieza.mp4")
            for viejo in (crudo, crudo[:-4] + ".efectos.json"):
                if os.path.exists(viejo):
                    os.remove(viejo)
            rc = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "maqueta3d.py"), "pieza", maqueta_ruta(ctx, M), "--lienzo", "%dx%d" % (W, H),
                                 "--salida", crudo], cwd=RAIZ).returncode
            if rc or not os.path.exists(crudo):
                return falla("la maqueta de %s no se renderizó: lo que dijo el motor está arriba (maqueta3d.py pieza %s --lienzo %dx%d; sus gates: `plano --check`; el registro del render: %s)"
                             % (nombre_mesa(ctx, M), rel(maqueta_ruta(ctx, M)), W, H, rel(crudo[:-4] + ".render.log")))
            VD.ff("-i", crudo, "-g", str(int(fps)), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-an", dst)
            if os.path.exists(crudo[:-4] + ".efectos.json"):
                shutil.copy2(crudo[:-4] + ".efectos.json", dst[:-4] + ".efectos.json")
            os.remove(crudo)   # queda el clip con sus cuadros clave; el proyecto y el registro del render siguen en maquetas/<mesa>/
        d = VD.ffprobe_dur(dst)
        if abs(d - D) > 2.0 / int(fps) + 0.05:
            return falla("el clip de la maqueta de %s dura %.2f s y su mesa %.2f s" % (nombre_mesa(ctx, M), d, D))
        ahora[M["id"]] = {"huella": h, "doble": doble, "dur": D, "lienzo": "%dx%d" % (W, H)}
        escribir(fh, ahora)
    if faltan:
        print("maquetas: %d de %d %s (%s) → %s" % (len(faltan), len(ms), "dobles sin render (MESA_RENDER=0)" if doble else "renderizadas",
                                                    ", ".join(M["id"] for M, _, _ in faltan), rel(cd)))
    else:
        print("maquetas: nada que renderizar (%d al día) → %s" % (len(ms), rel(cd)))
    return 0


def digesto_maqueta(ctx):
    """Lo que el realizador necesita para decidir una maqueta 3D: cuándo va, los estilos, los sets y los lugares del set que la
    voz nombra (con su id). → renglones para el digesto."""
    E = estilos_maqueta()
    L = ["", "## Maqueta 3D (opcional: solo cuando el LUGAR es la información; ≤ %d por video%s, un solo estilo; mesa de ≥ %.0f s)" % (
        regla(ctx, "MAQUETAS_MAX"), " y ≤ %d por capítulo" % regla(ctx, "MAQUETAS_CAP_MAX") if regla(ctx, "MAQUETAS_CAP_MAX") else "", regla(ctx, "MAQUETA_MIN_S")),
        "  bloque `maqueta` a nivel de mesa: referencias/flujo-mesa.md («La maqueta»). Los ids de lugar: minúsculas, sin tildes y con guiones."]
    L.append("  estilos: %s" % " · ".join("%s (%s)" % (k, (e.get("cuando") or "").split(":")[0].split(".")[0][:60]) for k, e in E.items() if e.get("motor") in motores_maqueta()))
    for sid in sets_maqueta():
        lug = lugares_maqueta(sid)
        dichos = []
        for lid, l in lug.items():
            nombre = l.get("nombre") or lid
            if len(VD._plano(nombre)) < 5:
                continue
            for i, S in enumerate(ctx["es"]):
                r = buscar(S, nombre, 0) if S.get("palabras") else None
                if r:
                    dichos.append("%s («%s», %s a los %.1f s)" % (lid, nombre, S["clave"], ctx["offs"][i] + S["palabras"][r[1]]["start"]))
                    break
        L.append("  set %s: %d lugares (las 22 cabeceras y los pueblos de OpenStreetMap). La voz nombra: %s" % (sid, len(lug), "; ".join(dichos[:14]) or "ninguno por su nombre"))
    L += ["  " + x for x in catalogo_maqueta()]
    return L


def catalogo_maqueta():
    """El vocabulario de la maqueta para el realizador (maqueta3d.py catalogo --para realizador), solo lo que dibujan los
    motores con render (motores_maqueta). → renglones; vacío si no se puede leer."""
    try:
        import maqueta3d
        mot = motores_maqueta()
        return maqueta3d.lineas_catalogo("realizador", motor=mot[0] if len(mot) == 1 else None)
    except Exception as e:   # el digesto no se cae por el catálogo
        return ["(no se pudo leer el catálogo de la maqueta: %s; python3 scripts/maqueta3d.py catalogo --para realizador)" % e]
