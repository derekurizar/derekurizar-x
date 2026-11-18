#!/usr/bin/env python3
"""La maqueta 3D de /video-3d: valida, saca cuadros y renderiza un `maqueta.json`.

Contrato: referencias/diseno/maqueta3d.md. El ESTILO decide el motor (design/sets3d/estilos.json → motor):
  three    three.js dentro de HyperFrames (video/maqueta/motor.js): color, noche, contorno, voxel, plano
  blender  Blender sin ventana renderiza la PLACA del mundo (scripts/maqueta_blender.py) y la capa 2D de HyperFrames va
           encima (video/maqueta/placa.js): arquitecto, diorama, papel. Necesita Blender ≥ 5.0 ($BLENDER o /Applications)
Este script RESUELVE el maqueta.json (lugares → km, cadenas de falla, alturas, tiempos del cierre) y se lo entrega al
motor ya masticado, de modo que la geometría vive en un solo sitio. Los gates M3D revisan los datos (reimplementan la
cámara y la proyección): nunca miden píxeles, y valen igual para los dos motores.

  maqueta3d.py check MAQUETA [--formato 9:16|4:5|ambos]          gates M3D1–M3D12
  maqueta3d.py cuadro MAQUETA --t S [--t S …] --salida DIR [--formato F] [--hoja]   PNG de cuadros sueltos
  maqueta3d.py proyecto MAQUETA --dir DIR [--formato F]           el proyecto de HyperFrames
  maqueta3d.py render MAQUETA --dir DIR [--formato F]             DIR/<9x16|4x5>/video.mp4 + DIR/efectos.json
  maqueta3d.py pieza MAQUETA --lienzo ANCHOxALTO --salida ARCHIVO.mp4 [--borrador]
        MODO PIEZA: la maqueta alojada en el cuadro de otro flujo (solo el mundo y sus pines, en un lienzo libre)
        check y cuadro lo aceptan con --pieza --lienzo ANCHOxALTO
  maqueta3d.py estilos | sets                                     los catálogos (sets: con su escala, pais o ciudad)
  maqueta3d.py catalogo [--para sesion|realizador|critico] [--escala E] [--motor M]   el VOCABULARIO legible
  maqueta3d.py catalogo --registrar | --check                     escribe (o comprueba) design/sets3d/vocabulario.json
        el vocabulario (piezas, eventos, objetos, mundos) son módulos video/maqueta/<clase>/<tipo>.js con su ficha
        <tipo>.json y sus reglas opcionales scripts/maqueta_tipos/<tipo>.py; aquí no se nombra ningún tipo
  maqueta3d.py prueba [--dir DIR] [--formato F]                   check + hoja + render del fixture (+ un cuadro en Blender)
  maqueta3d.py prueba --blender-render ESTILO                     el fixture completo en un estilo de Blender (lento)

Salida: 0 ok · 1 gate o paso fallido · 2 uso incorrecto. Python stdlib; HyperFrames por npx (su versión: scripts/versiones.py), un solo proceso.
"""
import argparse, datetime, html, json, math, os, re, shutil, subprocess, sys, time, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import build_set3d as SET3D  # noqa: E402  (lector del PNG del relieve)
import versiones             # noqa: E402  (la versión de HyperFrames, en un solo sitio: scripts/versiones.py)
import maqueta_tramos as TR  # noqa: E402  (varios mundos en un video: tramos)
import maqueta_escena as ESC  # noqa: E402  (la escena viva: M3D15–M3D19)
from maqueta_tipos import _movimiento as MV  # noqa: E402  (lo que se mueve: actor, flujo; la cámara que sigue)
from maqueta_tipos import _relieve as RL     # noqa: E402  (el relieve de pieza: `_alturas`)

HF = list(versiones.HF)      # ["npx", "--yes", "hyperframes@<versión>"]
MOTOR = os.path.join(RAIZ, "video", "maqueta")
SETS = os.path.join(RAIZ, "design", "sets3d")
FIXTURE = os.path.join(MOTOR, "fixture", "maqueta.json")
FIXTURES_MUNDOS = [os.path.join(MOTOR, "fixture", f) for f in ("esquema_carretera.json", "ciudad_capital.json", "trafico.json", "tramos.json", "escena_viva.json")]   # un caso por mundo nuevo (y el de lo que se mueve, y el de varios mundos)
FIXTURE_TRAMOS = os.path.join(MOTOR, "fixture", "tramos.json")
MOTORES = ("three", "blender")     # el estilo decide el motor: three.js en HyperFrames, o Blender (la placa) + la capa 2D de HyperFrames
BLENDER_PY = os.path.join(AQUI, "maqueta_blender.py")
RUMBOS = {"este": (1, 0), "oeste": (-1, 0), "norte": (0, 1), "sur": (0, -1)}
NC_MAX, NR_MAX, NO_MAX, FALLAS_MAX = 56, 4, 4, 4      # topes del shader (motor.js)
# El cuadro 0 es la portada: un titular con t ≤ PORTADA_T está completo desde el cuadro 0 y un evento con t ≤ PORTADA_T
# ya se ve en él: el motor lo dibuja como si llevara este avance (segundos) y termina cuando dice el maqueta.json.
# Cuánto adelanta cada tipo lo dice su ficha (`adelanto`: {"s": segundos} o {"dur": fracción de la duración}).
PORTADA_T = 0.1

# ---------- el vocabulario: piezas, eventos, objetos y mundos ----------
# Cada entrada es un MÓDULO de motor.js (video/maqueta/<clase>/<tipo>.js) con su FICHA (<tipo>.json: parámetros, cuándo
# sirve, escalas, motores, ejemplo) y, si sus reglas no caben en la ficha, sus reglas en scripts/maqueta_tipos/<tipo>.py.
# El CATÁLOGO design/sets3d/vocabulario.json reúne las fichas; lo escribe SOLO `maqueta3d.py catalogo --registrar`.
# Aquí, los gates y la orquestación lo leen del mismo sitio. Cómo añadir una entrada: referencias/diseno/maqueta3d.md.
VOCABULARIO = os.path.join(SETS, "vocabulario.json")
CLASES = {"pieza": "piezas", "evento": "eventos", "objeto": "objetos", "anotacion": "anotaciones", "mundo": "mundos"}   # clase → carpeta en video/maqueta/
ESCALAS = ("pais", "ciudad", "esquema")
TIPOS_PARAM = ("numero", "entero", "texto", "bool", "lugar", "lugares", "pieza", "puntos", "lista", "posicion", "ancla", "anclas", "claves", "mezcla", "circulos")
COMUNES = {"pieza": ("id", "tipo"), "evento": ("tipo", "t", "dur", "sfx"), "anotacion": ("tipo", "t", "hasta", "sfx"),   # campos comunes (no van en la ficha)
           "mundo": ("escala", "lugares", "piezas", "capas", "escena", "hora", "hora_razon", "ambiente")}   # escena: la ficha de la escena viva (video3d.py, C3D14)
# capas del dibujo del terreno que el guion puede apagar (mundo.capas; por defecto todas encendidas). Hoy las usa el
# estilo `plano`: curvas de nivel, líneas del fondo del mar y retícula de paralelos y meridianos (usuario, 2026-11-15:
# con `plano` se pregunta siempre si se quieren todas o una versión limpia)
CAPAS_MUNDO = ("curvas", "batimetria", "reticula")
REGLAS_DIR = os.path.join(AQUI, "maqueta_tipos")
_VOCAB, _REGLAS = {}, {}


def vocabulario():
    """El catálogo (design/sets3d/vocabulario.json) → {tipo: ficha}. Vacío si no se ha registrado."""
    if "v" not in _VOCAB:
        try:
            _VOCAB["v"] = {f["tipo"]: f for f in cargar_json(VOCABULARIO)["entradas"]}
        except (OSError, ValueError, KeyError):
            _VOCAB["v"] = {}
    return _VOCAB["v"]


def tipos(clase):
    """Los tipos de una clase del catálogo, en orden alfabético."""
    return tuple(sorted(t for t, f in vocabulario().items() if f["clase"] == clase))


def ficha(tipo, clase=None):
    f = vocabulario().get(tipo)
    return f if f and (clase is None or f["clase"] == clase) else None


def reglas(tipo):
    """Las reglas de un tipo que no caben en su ficha (scripts/maqueta_tipos/<tipo>.py) o None."""
    if tipo not in _REGLAS:
        _REGLAS[tipo] = None
        if re.fullmatch(r"[a-z][a-z0-9_]*", str(tipo)) and os.path.isfile(os.path.join(REGLAS_DIR, tipo + ".py")):
            import importlib
            _REGLAS[tipo] = importlib.import_module("maqueta_tipos." + tipo)
    return _REGLAS[tipo]


def tiene_regla(tipo, nombre):
    rg = reglas(tipo)
    return bool(rg and hasattr(rg, nombre))


def adelanto_de(tipo, dur):
    """Cuánto avance lleva un evento que empieza en la portada (None: el tipo no se ve en el cuadro 0)."""
    a = (ficha(tipo) or {}).get("adelanto")
    if not a:
        return None
    return float(a.get("s", 0)) + float(a.get("dur", 0)) * dur


def validar_campos(o, f, que, por_id=None, avisos=None):
    """El validador GENÉRICO: revisa `o` contra los parámetros de su ficha (requerido, tipo, rango, valores, mínimo de
    elementos, a qué pieza apunta) → copia de `o` con los defectos. Lanza Falla("M3D2", …) con la descripción del
    parámetro; lo que la ficha no declara va a `avisos` (no rompe una maqueta vieja)."""
    P, r = f.get("parametros") or {}, dict(o)

    def mal(nombre, como):
        raise Falla("M3D2", "%s: `%s` %s (%s)" % (que, nombre, como, P[nombre]["descripcion"]))

    def es_lugar(v):
        return isinstance(v, str) and v or (isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v))
    for nombre, d in P.items():
        v = o.get(nombre)
        if v is None:
            if d.get("requerido"):
                raise Falla("M3D2", "%s: falta `%s` (%s)" % (que, nombre, d["descripcion"]))
            if "defecto" in d:
                r[nombre] = d["defecto"]
            continue
        t = d["tipo"]
        if t in ("numero", "entero"):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or (t == "entero" and v != int(v)):
                mal(nombre, "es un número%s y vale %r" % (" entero" if t == "entero" else "", v))
            rg = d.get("rango")
            if rg and not rg[0] <= v <= rg[1]:
                mal(nombre, "vale %g y va de %g a %g" % (v, rg[0], rg[1]))
        elif t == "texto":
            if not isinstance(v, str):
                mal(nombre, "es un texto y vale %r" % (v,))
        elif t == "bool":
            if not isinstance(v, bool):
                mal(nombre, "es true o false y vale %r" % (v,))
        elif t == "lugar":
            if not es_lugar(v):
                mal(nombre, "es un lugar: un id del set o de mundo.lugares, o [lon, lat]; vale %r" % (v,))
        elif t in ("lugares", "puntos", "lista"):
            if not (d.get("todos") and v == "todos"):
                if not isinstance(v, list):
                    mal(nombre, "es una lista%s y vale %r" % (" (o «todos»)" if d.get("todos") else "", v))
                ok = {"lugares": es_lugar, "lista": lambda x: isinstance(x, str) and x,
                      "puntos": lambda x: isinstance(x, (list, tuple)) and len(x) == 2 and all(isinstance(y, (int, float)) for y in x)}[t]
                if not all(ok(x) for x in v):
                    mal(nombre, "lleva %s" % {"lugares": "lugares (ids o [lon, lat])", "lista": "textos", "puntos": "puntos [lon, lat]"}[t])
                if len(v) < d.get("min", 0):
                    mal(nombre, "necesita al menos %d y trae %d" % (d["min"], len(v)))
        elif t == "circulos":   # [[x, y, radio], …] en la unidad del mundo (zonas que algo esquiva)
            if not (isinstance(v, list) and all(isinstance(x, (list, tuple)) and len(x) == 3 and all(isinstance(y, (int, float)) and not isinstance(y, bool) for y in x) for x in v)):
                mal(nombre, "es una lista de [x, y, radio]; vale %r" % (v,))
        elif t == "posicion":   # sobre un camino: metros desde su inicio, «NN%» del largo o un lugar (su proyección)
            if not ((isinstance(v, (int, float)) and not isinstance(v, bool)) or es_lugar(v)):
                mal(nombre, "es una posición sobre el camino: metros desde su inicio, «40%%» o un lugar; vale %r" % (v,))
        elif t in ("ancla", "anclas"):   # un lugar, o algo que se mueve: {actor: id} · {flujo: id, n | carril, cerca, t[, cuantos]}
            for x in (v if t == "anclas" and isinstance(v, list) else [v]):
                movil = isinstance(x, dict) and ("actor" in x or "flujo" in x)
                if not (movil or es_lugar(x)):
                    mal(nombre, "es %s: un lugar, {\"actor\": id} o {\"flujo\": id, \"n\": k} / {\"flujo\": id, \"cerca\": lugar, \"t\": s}; vale %r"
                        % ("una lista de anclas" if t == "anclas" else "un ancla", x))
                ref = x.get("actor", x.get("flujo")) if movil else None
                if movil and por_id is not None and ref not in por_id:
                    mal(nombre, "«%s» no es el id de una pieza de esta maqueta (hay: %s)" % (ref, ", ".join(por_id) or "ninguna"))
            if t == "anclas" and (not isinstance(v, list) or len(v) < d.get("min", 1)):
                mal(nombre, "es una lista de al menos %d ancla(s)" % d.get("min", 1))
        elif t == "claves":     # [{t, …}, …] crecientes en t
            if not (isinstance(v, list) and v and all(isinstance(x, dict) and isinstance(x.get("t"), (int, float)) for x in v)):
                mal(nombre, "es una lista de claves {\"t\": segundos, …}; vale %r" % (v,))
            if [x["t"] for x in v] != sorted(x["t"] for x in v):
                mal(nombre, "va ordenada por `t`")
        elif t == "mezcla":     # {tipo: proporción}
            if not (isinstance(v, dict) and v and all(isinstance(k, str) and isinstance(p, (int, float)) and not isinstance(p, bool) and p >= 0 for k, p in v.items())
                    and sum(v.values()) > 0):
                mal(nombre, "es {tipo: proporción ≥ 0, …} con alguna mayor que 0; vale %r" % (v,))
            if d.get("valores") and set(v) - set(d["valores"]):
                mal(nombre, "lleva %s y va de: %s" % (", ".join(sorted(set(v) - set(d["valores"]))), ", ".join(d["valores"])))
        elif t == "pieza":
            if por_id is not None and v not in por_id:
                mal(nombre, "«%s» no es el id de una pieza de esta maqueta (hay: %s)" % (v, ", ".join(por_id) or "ninguna"))
            if por_id is not None and d.get("piezas") and por_id[v]["tipo"] not in d["piezas"]:
                raise Falla("M3D2", "%s: `%s` «%s» no es una pieza de tipo %s" % (que, nombre, v, " o ".join(d["piezas"])))
        if d.get("valores") and t != "mezcla" and v not in d["valores"]:
            mal(nombre, "vale %r y va uno de: %s" % (v, ", ".join(map(str, d["valores"]))))
    extra = [k for k in o if k not in P and k not in COMUNES.get(f["clase"], ()) and not str(k).startswith("_")]
    if extra and avisos is not None:
        avisos.append("%s: %s no %s parámetro de «%s» (maqueta3d.py catalogo): se ignora" % (que, ", ".join("`%s`" % k for k in extra), "es" if len(extra) == 1 else "son", f["tipo"]))
    return r


def textos_anotacion(o, escala=None):
    """Lo que una anotación pone en pantalla como texto (reglas → textos): para el tiempo de lectura (M3D4) y para el
    respaldo de sus números (C3D5 en video3d.py). Un reloj `ilustrativo` sobre un esquema no pide respaldo."""
    rg = reglas(o.get("tipo"))
    # en una anotación «5 m» son metros (el verificador de cifras leería «m» como millones)
    return [re.sub(r"(\d)\s*m\b", r"\1 metros", x) for x in (rg.textos(o, escala) if rg and hasattr(rg, "textos") else []) if x]


def tipo_conocido(tipo, clase, est, que, escala=None):
    """La ficha de un tipo usado en el maqueta.json; FALLA M3D2 si no está en el catálogo, si el motor del estilo no lo
    dibuja o si no sirve en la escala del mundo (su ficha → `escalas`)."""
    f = ficha(tipo, clase)
    if not f:
        raise Falla("M3D2", "%s: el %s «%s» no está en el catálogo (maqueta3d.py catalogo; hay: %s); si hace falta, pídelo al constructor con un brief"
                    % (que, "tipo de pieza" if clase == "pieza" else "tipo de " + clase, tipo, ", ".join(tipos(clase)) or "ninguno: maqueta3d.py catalogo --registrar"))
    if est["motor"] not in f["motores"]:
        raise Falla("M3D2", "%s: el estilo «%s» (motor %s) no dibuja «%s»: usa un estilo de three.js (%s)"
                    % (que, est["id"], est["motor"], tipo, ", ".join(k for k, e in catalogo_estilos().items() if e["motor"] in f["motores"])))
    if escala and escala not in f["escalas"]:
        raise Falla("M3D2", "%s: «%s» no se dibuja en un mundo de escala %s (sirve en: %s; lo de esta escala: maqueta3d.py catalogo --escala %s)"
                    % (que, tipo, escala, ", ".join(f["escalas"]), escala))
    return f


def mundo_de(mundo, est, avisos):
    """El MUNDO del maqueta.json (`mundo.escala`: pais por defecto) → el objeto que lo resuelve, con su ficha
    (video/maqueta/mundos/<escala>.json) y sus reglas (scripts/maqueta_tipos/<escala>.py → mundo(o, ficha, m3)). Lo que
    ofrece (lo usan el resolver, los gates y las reglas de cada tipo): escala, id, unidad_m (metros por unidad de la
    escena), km (unidad_m / 1000), exag, caja (x0, y0, x1, y1), dentro(x, y), suelo(x, y) (la altura de la maqueta en
    unidades, ya exagerada), punto(a, b) ([lon, lat] o, en esquema, [x, y] en metros → unidades), lugares (los suyos:
    {id: {nombre, lon, lat | x, y, peso}}), lugar_xy(l), como_lugar (cómo se declara un lugar), fuente (pie y pie_claves),
    caminos ({nombre: [[x, y, s, 0], …]}), archivos() ([(origen, nombre en assets/set/)]), datos_R() (lo que va al primer
    nivel del maqueta resuelto: relieve, frontera) y datos_mundo() (lo que va en MAQUETA.mundo para su módulo de motor.js)."""
    escala = mundo.get("escala", "pais")
    f = tipo_conocido(escala, "mundo", est, "mundo")
    o = validar_campos(mundo, f, "mundo", avisos=avisos)
    rg = reglas(escala)
    if not rg or not hasattr(rg, "mundo"):
        raise Falla("M3D1", "mundo «%s»: sin reglas (scripts/maqueta_tipos/%s.py → mundo(o, ficha, m3))" % (escala, escala))
    W = rg.mundo(o, f, sys.modules[__name__])
    W.ficha = f
    return W


def resolver_entrada(o, f, que, X, base):
    """Una pieza o un evento ya validado → lo resuelto: `base` + lo que dicen las reglas del tipo; sin reglas, los
    parámetros tal cual, con cada lugar en km ([x, y]; en una lista: [x, y, id])."""
    rg = reglas(f["tipo"])
    if rg and hasattr(rg, "resolver"):
        base.update(rg.resolver(o, X, que))
        return base
    for nombre, d in (f.get("parametros") or {}).items():
        v = o.get(nombre)
        if v is None:
            continue
        if d["tipo"] == "lugar":
            l = X.lugar(v, que); base[nombre] = [l["x"], l["y"]]
        elif d["tipo"] == "lugares" and v != "todos":
            base[nombre] = [[l["x"], l["y"], ref if isinstance(ref, str) else ""] for ref, l in ((ref, X.lugar(ref, que)) for ref in v)]
        elif d["tipo"] == "ancla":     # → {x, y} o {movil, n, desfase, lev} (_movimiento.resolver_ancla)
            base[nombre] = MV.resolver_ancla(v, X, que + " → " + nombre)[0]
        elif d["tipo"] == "anclas":    # una ref con `cuantos` se vuelve varias
            base[nombre] = [a for x in v for a in MV.resolver_ancla(x, X, que + " → " + nombre, varias=True)]
        else:
            base[nombre] = v
    return base

# La zona de cada formato: de aquí salen las variables CSS de la capa y lo que miden los gates (una sola verdad).
# 9:16 respeta la zona segura de TikTok, Reels y Shorts (video/comun.css: columna x 85–876, y ≥ 215, iconos x ≥ 900
# desde y ≈ 1070, subtítulos en 1400, texto de la app desde y ≈ 1645). 4:5 es el feed: sin zona de teléfono.
# centro_y: el centro de la zona libre (entre un titular de dos renglones y la banda de abajo). El 3D ocupa TODO el
# lienzo, pero el punto que mira la cámara cae ahí y no en el centro geométrico (desplazamiento de lente, sin cambiar
# el plano): motor.js con camera.setViewOffset y proyector() aquí.
ZONAS = {
    "9:16": {"W": 1080, "H": 1920, "izq": 85, "der": 876, "corte": 57, "sup": 215, "iconos_x": 900, "iconos_y": 1070,
             "barra_y": 222, "tit_y": 256, "tit_px": 84, "banda_sin": 300, "cifra_fin": 1270, "cifra_px": 190, "rotulo_px": 44,
             "cifra_ancho": 620, "fila_y": 1300, "fin_marcas": 1282, "subs_y": 1400, "subs_px": 60, "pie_y": 1574, "marca_px": 34,
             "seguir_y": 272, "seguir_der": 62, "cierre_y": 430, "cierre_gap": 96, "frase_px": 88, "red_px": 64, "red_txt": 52,
             "red_gap": 22, "sombra_arriba": 600, "sombra_abajo": 900, "centro_y": 880},
    "4:5": {"W": 1080, "H": 1350, "izq": 85, "der": 995, "corte": 0, "sup": 0, "iconos_x": 99999, "iconos_y": 99999,
            "barra_y": 56, "tit_y": 86, "tit_px": 72, "banda_sin": 120, "cifra_fin": 1000, "cifra_px": 150, "rotulo_px": 38,
            "cifra_ancho": 620, "fila_y": 1026, "fin_marcas": 1008, "subs_y": 1100, "subs_px": 54, "pie_y": 1284, "marca_px": 32,
            "seguir_y": 84, "seguir_der": 85, "cierre_y": 190, "cierre_gap": 56, "frase_px": 72, "red_px": 52, "red_txt": 42,
            "red_gap": 14, "sombra_arriba": 420, "sombra_abajo": 620, "centro_y": 650},
}
CARPETA = {"9:16": "9x16", "4:5": "4x5"}
MARGEN_PIEZA = 40      # px: en modo pieza las marcas guardan este margen con los bordes del lienzo
TRABADO_S = 1.5       # M3D14: lo que la cámara sigue no se queda quieto más de esto
SEPARACION_PX = 60     # M3D11: lo mínimo entre el ancla de una marca y la pieza de la que se declara separada


def es_pieza(formato):
    return formato not in ZONAS


def lienzo_de(texto):
    """«950x1040» → (950, 1040). Lados pares (H.264 yuv420p) entre 320 y 3840."""
    mo = re.fullmatch(r"(\d+)[xX×](\d+)", str(texto or "").strip())
    if not mo:
        raise Falla("M3D1", "lienzo «%s»: se escribe ANCHOxALTO, p. ej. 950x1040" % texto)
    w, h = int(mo.group(1)), int(mo.group(2))
    if w % 2 or h % 2 or not (320 <= w <= 3840 and 320 <= h <= 3840):
        raise Falla("M3D1", "lienzo %dx%d: los lados van de 320 a 3840 px y son pares (H.264 yuv420p)" % (w, h))
    return w, h


def zona_de(formato):
    """La zona de un formato: 9:16 y 4:5 son las de ZONAS; cualquier otro es un lienzo de MODO PIEZA («950x1040»):
    la maqueta alojada en el cuadro de otro flujo. Ahí el mundo llena el lienzo, el punto que mira la cámara cae en su
    centro y las marcas solo guardan MARGEN_PIEZA con los bordes (sin bandas de titular ni de pie). Lo demás de la capa
    es opcional; si viene, usa estas medidas (pie y aviso abajo, pequeños)."""
    if formato in ZONAS:
        return dict(ZONAS[formato])
    W, H = lienzo_de(formato)
    g = MARGEN_PIEZA
    return {"pieza": True, "W": W, "H": H, "izq": g + 25, "der": W - g - 25, "corte": g - 3, "sup": 0, "iconos_x": 99999, "iconos_y": 99999,
            "barra_y": g, "tit_y": g + 24, "tit_px": 64, "banda_sin": g, "cifra_fin": H - 150, "cifra_px": 130, "rotulo_px": 34,
            "cifra_ancho": min(620, W - 2 * (g + 25)), "fila_y": H - 122, "fin_marcas": H - g, "subs_y": H - 230, "subs_px": 48, "pie_y": H - 72,
            "marca_px": 32, "seguir_y": g + 24, "seguir_der": g + 25, "cierre_y": int(H * 0.2), "cierre_gap": 48, "frase_px": 64, "red_px": 48,
            "red_txt": 38, "red_gap": 12, "sombra_arriba": 0, "sombra_abajo": 0, "centro_y": H / 2}


def carpeta_de(formato):
    return CARPETA.get(formato) or "pieza_%dx%d" % lienzo_de(formato)
ICONOS = {
    "tiktok": '<path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>',
    "instagram": '<rect x="2.6" y="2.6" width="18.8" height="18.8" rx="5.4" fill="none" stroke-width="2.2"/><circle cx="12" cy="12" r="4.3" fill="none" stroke-width="2.2"/><circle cx="17.5" cy="6.5" r="1.4"/>',
    "facebook": '<path d="M14.2 8.1h3V4.2h-3.1c-3 0-4.6 1.9-4.6 4.8v2.3H7v3.9h2.5V24h4.1v-8.8h3.1l.5-3.9h-3.6V9.4c0-.8.3-1.3 1.1-1.3z"/>',
    "youtube": '<path fill-rule="evenodd" d="M23.5 7.2a3 3 0 0 0-2.1-2.1C19.5 4.6 12 4.6 12 4.6s-7.5 0-9.4.5A3 3 0 0 0 .5 7.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-4.8zM9.6 15.6V8.4l6.2 3.6z"/>',
    "x": '<path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/>',
}


class Falla(Exception):
    """Un gate o un paso que no pasa: (gate, mensaje)."""


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def normal(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def palabras_de(s):
    return len(str(s or "").split())


def lectura_s(*textos):
    """Tiempo mínimo para leer un texto en pantalla: 0.5 s + 0.3 s por palabra, mínimo 1.2 s."""
    return max(1.2, 0.5 + 0.3 * sum(palabras_de(t) for t in textos))


def catalogo_estilos():
    return {e["id"]: e for e in cargar_json(os.path.join(SETS, "estilos.json"))["estilos"]}


def escala_set(sid):
    """La escala de un set (fuente.json → `escala`; los de antes de la Fase 1 son de escala pais)."""
    try:
        return cargar_json(os.path.join(SETS, sid, "fuente.json")).get("escala", "pais")
    except (OSError, ValueError):
        return None


def lista_sets(escala=None):
    """Los sets de design/sets3d/ (los que tienen fuente.json); con `escala`, solo los de esa escala."""
    return sorted(d for d in os.listdir(SETS) if os.path.isfile(os.path.join(SETS, d, "fuente.json")) and (escala is None or escala_set(d) == escala))


def set_de(o, escala, m3=None):
    """El id del set de un mundo (`mundo.set`) ya comprobado: existe y es de esa escala. FALLA M3D1 si no."""
    sid = o.get("set")
    if sid not in lista_sets():
        raise Falla("M3D1", "set «%s» no existe en design/sets3d/ (hay de escala %s: %s; se arma con scripts/build_set3d.py)" % (sid, escala, ", ".join(lista_sets(escala)) or "ninguno"))
    if escala_set(sid) != escala:
        raise Falla("M3D1", "el set «%s» es de escala %s y el mundo es de escala %s: pon `mundo.escala` «%s» o usa un set de escala %s (%s)"
                    % (sid, escala_set(sid), escala, escala_set(sid), escala, ", ".join(lista_sets(escala)) or "ninguno"))
    return sid


# ---------- el set de escala pais (el mundo «pais»): relieve, lugares, fallas, frontera; unidad: km ----------
class Set:
    escala, unidad_m, km = "pais", 1000.0, 1.0
    como_lugar = "decláralo con lon y lat, o usa [lon, lat]"

    def __init__(self, sid, exag=5.0):
        self.exag = float(exag)
        self.caminos = {}
        self.id, self.dir = sid, os.path.join(SETS, sid)
        self.relieve = cargar_json(os.path.join(self.dir, "relieve.json"))
        self.fuente = cargar_json(os.path.join(self.dir, "fuente.json"))
        self.lugares = cargar_json(os.path.join(self.dir, "lugares.json"))["lugares"]
        self.fallas = cargar_json(os.path.join(self.dir, "fallas.json"))
        fr = cargar_json(os.path.join(self.dir, "frontera.json"))
        self.frontera = fr["anillos"]
        self.vecinos = (fr.get("vecinos") or {}).get("lineas") or []   # bordes y costas de los países vecinos (build_set3d.py)
        R, P, c = self.relieve, self.relieve["proyeccion"], self.relieve["caja"]
        self.P, self.caja_geo = P, c
        self.x0, self.x1 = (c["lon_min"] - P["lon0"]) * P["km_lon"], (c["lon_max"] - P["lon0"]) * P["km_lon"]
        self.y0, self.y1 = (c["lat_min"] - P["lat0"]) * P["km_lat"], (c["lat_max"] - P["lat0"]) * P["km_lat"]
        self.cx, self.cy = (self.x1 - self.x0) / R["ancho"], (self.y1 - self.y0) / R["alto"]
        self._filas = None

    def xy(self, lon, lat):
        return (lon - self.P["lon0"]) * self.P["km_lon"], (lat - self.P["lat0"]) * self.P["km_lat"]

    punto = xy

    def lugar_xy(self, l):
        return self.xy(l["lon"], l["lat"])

    @property
    def caja(self):
        """(x0, y0, x1, y1) en unidades de la escena (la caja del relieve; la de lon/lat es caja_geo)."""
        return (self.x0, self.y0, self.x1, self.y1)

    def dentro(self, x, y, margen=0.0):
        return self.x0 + margen <= x <= self.x1 - margen and self.y0 + margen <= y <= self.y1 - margen

    def suelo(self, x, y):
        """La altura de la maqueta (km, ya exagerada) en (x, y): la misma cuenta que motor.js (mundos/pais.js)."""
        return self.metros(x, y) / 1000.0 * self.exag

    def archivos(self):
        return [(os.path.join(self.dir, self.relieve["archivo"]), self.relieve["archivo"])]

    def datos_R(self):
        return {"relieve": {k: self.relieve[k] for k in ("archivo", "ancho", "alto", "caja", "desfase_m", "proyeccion", "muestras", "max_m")},
                "frontera": [[[round(v, 3) for v in self.xy(q[0], q[1])] for q in an] for an in self.frontera]}

    def datos_mundo(self):
        return {}

    def metros(self, x, y):
        """Altura real (m, el mar en 0) con la misma interpolación bilineal que motor.js."""
        if self._filas is None:
            self._filas = SET3D.png_leer(os.path.join(self.dir, self.relieve["archivo"]))[2]
        R, d = self.relieve, self.relieve["desfase_m"]
        fi = min(max((x - self.x0) / self.cx - 0.5, 0), R["ancho"] - 1.001)
        fj = min(max((self.y1 - y) / self.cy - 0.5, 0), R["alto"] - 1.001)
        i, j = int(fi), int(fj)
        u, v = fi - i, fj - j
        a, b = self._filas[j], self._filas[j + 1]
        h = lambda f, k: f[3 * k] * 256 + f[3 * k + 1] - d
        return max(0.0, (h(a, i) * (1 - u) + h(a, i + 1) * u) * (1 - v) + (h(b, i) * (1 - u) + h(b, i + 1) * u) * v)


# ---------- geometría de las cadenas de falla ----------
def encadenar(polilineas):
    """Varias polilíneas [[x, y], …] → una cadena [[x, y, s, salto]] ordenada a lo largo de su eje (oeste → este, o
    sur → norte si corre más en vertical). `salto` = 1 en el último punto de un trazo si el siguiente empieza lejos;
    s (km) cuenta también los saltos, para que el frente de una ruptura tarde en cruzarlos."""
    pts = [p for ln in polilineas for p in ln]
    eje_x = (max(p[0] for p in pts) - min(p[0] for p in pts)) >= (max(p[1] for p in pts) - min(p[1] for p in pts))
    k = 0 if eje_x else 1
    orden = []
    for ln in polilineas:
        ln = [list(p[:2]) for p in ln]
        if ln[0][k] > ln[-1][k]:
            ln = ln[::-1]
        orden.append(ln)
    orden.sort(key=lambda ln: ln[0][k])
    cad, s = [], 0.0
    for n, ln in enumerate(orden):
        for i, p in enumerate(ln):
            if cad:
                d = math.hypot(p[0] - cad[-1][0], p[1] - cad[-1][1])
                if i == 0:
                    cad[-1][3] = 1 if d > 0.5 else 0
                    if d < 1e-6:
                        continue
                s += d
            cad.append([round(p[0], 3), round(p[1], 3), round(s, 3), 0])
    return cad


def suavizar(pts, paso=3.0):
    """Curva de Catmull-Rom centrípeta por los puntos [[x, y], …], muestreada cada ≈ `paso` km: un trazo dado con
    pocos puntos (la traza publicada de una ruptura) no se dibuja con quiebres."""
    if len(pts) < 3:
        return [list(p) for p in pts]
    P = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + [tuple(p) for p in pts] + [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        d = lambda a, b: max(1e-6, math.hypot(b[0] - a[0], b[1] - a[1])) ** 0.5
        t0 = 0.0; t1 = t0 + d(p0, p1); t2 = t1 + d(p1, p2); t3 = t2 + d(p2, p3)
        n = max(1, int(math.ceil(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / paso)))
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            L = lambda a, b, ta, tb: tuple(((tb - t) * a[j] + (t - ta) * b[j]) / (tb - ta) for j in (0, 1))
            a1, a2, a3 = L(p0, p1, t0, t1), L(p1, p2, t1, t2), L(p2, p3, t2, t3)
            b1, b2 = L(a1, a2, t0, t2), L(a2, a3, t1, t3)
            out.append(list(L(b1, b2, t1, t2)))
    out.append(list(pts[-1]))
    return out


def simplificar(cad, tol):
    """Douglas-Peucker por tramos (los puntos con salto y el siguiente se conservan)."""
    def dp(a, b, fijos):
        if b <= a + 1:
            return
        ax, ay, bx, by = cad[a][0], cad[a][1], cad[b][0], cad[b][1]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy or 1e-9
        peor, cual = 0.0, None
        for i in range(a + 1, b):
            h = min(1, max(0, ((cad[i][0] - ax) * dx + (cad[i][1] - ay) * dy) / L))
            d = math.hypot(cad[i][0] - ax - dx * h, cad[i][1] - ay - dy * h)
            if d > peor:
                peor, cual = d, i
        if peor > tol:
            fijos.add(cual); dp(a, cual, fijos); dp(cual, b, fijos)
    fijos, ini = {0, len(cad) - 1}, 0
    for i, p in enumerate(cad):
        if p[3] or i == len(cad) - 1:
            fijos.update((ini, i)); dp(ini, i, fijos); ini = i + 1
    return [cad[i] for i in sorted(fijos)]


def mas_cercano(cad, x, y):
    """→ (s, distancia) del punto de la cadena más cercano a (x, y)."""
    mejor = (0.0, 1e18)
    for a, b in zip(cad, cad[1:]):
        if a[3]:
            continue
        dx, dy = b[0] - a[0], b[1] - a[1]
        h = min(1, max(0, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy or 1e-9)))
        d = math.hypot(x - a[0] - dx * h, y - a[1] - dy * h)
        if d < mejor[1]:
            mejor = (a[2] + (b[2] - a[2]) * h, d)
    return mejor


def punto_en_s(cad, s):
    if s <= cad[0][2]:
        return cad[0][0], cad[0][1]
    for a, b in zip(cad, cad[1:]):
        if s <= b[2]:
            u = (s - a[2]) / max(1e-6, b[2] - a[2])
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
    return cad[-1][0], cad[-1][1]


# ---------- cámara y proyección (la misma función que motor.js) ----------
def camara_en(claves, t):
    i = 0
    while i < len(claves) - 2 and t > claves[i + 1]["t"]:
        i += 1
    a, b = claves[i], claves[min(i + 1, len(claves) - 1)]
    u = min(1, max(0, (t - a["t"]) / (b["t"] - a["t"]))) if b["t"] > a["t"] else 0
    e = -(math.cos(math.pi * u) - 1) / 2
    c = {k: a[k] + (b[k] - a[k]) * e for k in ("dist", "dist_km", "azimut", "elevacion", "fov")}
    # el punto que mira: el de la clave, o —si la clave sigue algo que se mueve (`_pos`)— dónde está eso en t
    pa, pb = (a["_pos"](t) if a.get("_pos") else (a["x"], a["y"], a["alt"])), (b["_pos"](t) if b.get("_pos") else (b["x"], b["y"], b["alt"]))
    for i, k in enumerate(("x", "y", "alt")):
        c[k] = pa[i] + (pb[i] - pa[i]) * e
    c["cerca"] = a.get("cerca", 0.5)
    return c


def ojo_de(c):
    az, el = math.radians(c["azimut"]), math.radians(c["elevacion"])
    hd = c["dist"] * math.cos(el)
    return c["x"] + math.sin(az) * hd, c["y"] - math.cos(az) * hd, c["alt"] + c["dist"] * math.sin(el)


def proyector(c, W, H, sube=0.0):
    """→ función (x, y, z) → (px, py) | None (detrás de la cámara). Mundo: x este, y norte, z arriba (unidades del mundo).
    `sube`: píxeles que la imagen entera sube (H/2 − centro_y de la zona): el desplazamiento de lente del motor."""
    ex, ey, ez = ojo_de(c)
    fx, fy, fz = c["x"] - ex, c["y"] - ey, c["alt"] - ez
    n = math.sqrt(fx * fx + fy * fy + fz * fz); fx, fy, fz = fx / n, fy / n, fz / n
    rx, ry, rz = fy, -fx, 0.0                                   # f × (0, 0, 1)
    n = math.hypot(rx, ry) or 1e-9; rx, ry = rx / n, ry / n
    ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx   # r × f
    foco, cerca = 1 / math.tan(math.radians(c["fov"]) / 2), max(c.get("cerca", 0.5), c["dist"] * 0.02)

    def p(x, y, z):
        dx, dy, dz = x - ex, y - ey, z - ez
        zc = dx * fx + dy * fy + dz * fz
        if zc <= cerca:
            return None
        return ((dx * rx + dy * ry + dz * rz) * foco / (W / H * zc) + 1) / 2 * W, (1 - (dx * ux + dy * uy + dz * uz) * foco / zc) / 2 * H - sube
    return p


# ---------- resolver: maqueta.json → lo que dibuja el motor ----------
def resolver(m, formato, avisos=None):
    """Convierte el maqueta.json en la estructura resuelta (window.MAQUETA). Lanza Falla(gate, mensaje) si algo que
    se referencia no existe. `avisos` recibe lo que no falla pero conviene saber."""
    avisos = avisos if avisos is not None else []
    est = catalogo_estilos().get(m.get("estilo"))
    if not est:
        raise Falla("M3D1", "estilo «%s» no está en design/sets3d/estilos.json (hay: %s)" % (m.get("estilo"), ", ".join(catalogo_estilos())))
    if est["motor"] not in MOTORES:
        raise Falla("M3D1", "estilo «%s»: motor «%s» desconocido (hay: %s)" % (est["id"], est["motor"], ", ".join(MOTORES)))
    tokens = cargar_json(os.path.join(RAIZ, "design", "tokens.json"))
    pal = tokens["noche"]["paletas"].get(m.get("paleta"))
    if not pal:
        raise Falla("M3D1", "paleta «%s» no está en design/tokens.json → noche.paletas (hay: %s)" % (m.get("paleta"), ", ".join(tokens["noche"]["paletas"])))
    mundo = m.get("mundo") or {}
    S = mundo_de(mundo, est, avisos)                     # el mundo de su escala (pais: el Set de siempre)
    # EL RELIEVE DE PIEZA (`_alturas`, maqueta_tipos/_relieve.py): S.suelo = el suelo del mundo + lo que publican las piezas
    S.alturas = []
    if not hasattr(S, "suelo_base"):
        S.suelo_base = S.suelo
        S.suelo = (lambda W: lambda x, y: W.suelo_base(x, y) + RL.en(W.alturas, x, y))(S)
    exag = S.exag
    roles = {"@fondo": pal["fondo"], "@fondo2": pal["fondo_acto2"], "@fondo3": pal["fondo_golpe"], "@acento": pal["acento"],
             "@texto": tokens["noche"]["texto"], "@tinta": tokens["noche"]["tinta_sobre_acento"]}
    color = lambda v: roles.get(v, v)
    Z = zona_de(formato); Z["velo"] = est["capa"]["velo"]
    alt_km = S.suelo                                     # altura del suelo en unidades del mundo (pais: km), ya exagerada

    # lugares: los del set, los que PUBLICAN las piezas (`_lugares`: «<id de la pieza>.<lugar>» siempre y «<lugar>» si
    # nadie más lo usa) y los de mundo.lugares (que mandan sobre todos)
    propios = mundo.get("lugares") or {}
    publicados = {}

    def lugar(ref, que):
        if isinstance(ref, (list, tuple)) and len(ref) == 2 and all(isinstance(v, (int, float)) for v in ref):
            (x, y), nombre, donde = S.punto(ref[0], ref[1]), "", tuple(ref)
        elif isinstance(ref, str) and ref in publicados and ref not in propios:
            l = publicados[ref]
            return {"x": l["x"], "y": l["y"], "nombre": l["nombre"], "peso": l["peso"]}
        elif isinstance(ref, str) and (ref in propios or ref in S.lugares):
            l = propios.get(ref) or S.lugares[ref]
            try:
                x, y = S.lugar_xy(l)
            except (KeyError, TypeError):
                raise Falla("M3D2", "%s: el lugar «%s» de mundo.lugares está mal declarado (%s)" % (que, ref, S.como_lugar))
            nombre, donde = l.get("nombre", ref), (l.get("lon", l.get("x")), l.get("lat", l.get("y")))
        else:
            raise Falla("M3D2", "%s: el lugar «%s» no está en mundo.lugares ni en el %s (%s)" % (que, ref, "mundo %s" % S.id if S.escala == "esquema" else "set %s" % S.id, S.como_lugar))
        if not S.dentro(x, y):
            raise Falla("M3D2", "%s: el lugar «%s» (%.3f, %.3f) cae fuera de la caja del %s" % (que, ref, donde[0], donde[1], "mundo %s" % S.id if S.escala == "esquema" else "set %s" % S.id))
        return {"x": round(x, 3), "y": round(y, 3), "nombre": nombre, "peso": (propios.get(ref) or S.lugares.get(ref) or {}).get("peso", 0.4) if isinstance(ref, str) else 0.4}

    # piezas: cada una contra su ficha (validador genérico) y las reglas de su tipo (scripts/maqueta_tipos/<tipo>.py)
    import types
    X = types.SimpleNamespace(m3=sys.modules[__name__], S=S, lugar=lugar, propios=propios, publicados=publicados, avisos=avisos, alt_km=alt_km, piezas=[], por_id={},
                              eventos=[], moviles={}, dur=float(m.get("duracion_s", 0) or 0))
    piezas, ids = X.piezas, set()
    # EL AMBIENTE: un esquema nace vestido (vegetación, cercas, postes, farolas: la pieza `ambiente`). Si el mundo no la
    # trae, se añade sola con el de su receta (`"ambiente": false` en el mundo la quita); va al final y esquiva las demás
    # piezas (sus cajas van en `evitar`).
    lista_piezas = list(mundo.get("piezas") or [])
    if S.escala == "esquema" and ficha("ambiente", "pieza") and mundo.get("ambiente") is not False and not any(p.get("tipo") == "ambiente" for p in lista_piezas):
        amb = {"ciudad": "ciudad", "carretera": "ciudad", "campo": "campo", "costa": "costa", "plaza": "plaza"}.get(mundo.get("receta"), "campo")
        lista_piezas.append({"id": "_ambiente", "tipo": "ambiente", "ambiente": amb, "densidad": 0.5, "semilla": int(mundo.get("semilla", 1) or 1)})
    lista_piezas.sort(key=lambda p: p.get("tipo") == "ambiente")   # el ambiente, al final (estable)
    for n, p in enumerate(lista_piezas):
        pid, tipo = p.get("id"), p.get("tipo")
        if tipo == "ambiente" and p.get("evitar") is None:   # lo que ya está puesto no se pisa
            ev = []
            for q in piezas:
                fq = ficha(q["tipo"], "pieza") or {}
                if "x" in q and "y" in q and q["tipo"] not in ESC.PLANAS:
                    cj = ESC._caja_de(fq, float(q.get("tamano", 1)))
                    ev.append([round(q["x"] * S.unidad_m, 1), round(q["y"] * S.unidad_m, 1), round(max(cj[0], cj[1]) * 0.62 + 2, 1)])
            for aid, a in (getattr(X, "actores", None) or {}).items():
                if a.get("quieto"):
                    fo = ficha(a["p"].get("objeto"), "objeto") or {}
                    cj = ESC._caja_de(fo, float(a["p"].get("tamano", 1) or 1))
                    x0, y0 = a["cad"][0][0], a["cad"][0][1]
                    ev.append([round(x0 * S.unidad_m, 1), round(y0 * S.unidad_m, 1), round(max(cj[0], cj[1]) * 0.62 + 1.5, 1)])
            if ev:
                p = dict(p, evitar=ev)
        que = "pieza «%s»" % pid
        if not pid or pid in ids:
            raise Falla("M3D2", "la pieza %d no tiene `id` o lo repite (%r)" % (n, pid))
        ids.add(pid)
        f = tipo_conocido(tipo, "pieza", est, que, S.escala)
        pz = resolver_entrada(validar_campos(p, f, que, avisos=avisos), f, que, X, {"id": pid, "tipo": tipo})
        if pz.get("_alturas"):                              # su relieve: desde aquí lo pisa todo lo demás
            RL.revisar(pz["_alturas"], que, Falla)
            S.alturas.extend(pz["_alturas"])
            pz["relieve"] = True                            # (los gates la miden desde el suelo del mundo, no desde el suyo)
        for i, l in (pz.get("_lugares") or {}).items():     # sus lugares con nombre, en unidades de la escena
            try:
                l = {"x": round(float(l["x"]), 3), "y": round(float(l["y"]), 3), "nombre": str(l.get("nombre") or i), "peso": float(l.get("peso", 0.5))}
            except (KeyError, TypeError, ValueError):
                raise Falla("M3D2", "%s: publica el lugar «%s» mal formado (va {x, y, nombre, peso} en unidades de la escena)" % (que, i))
            if not S.dentro(l["x"], l["y"]):
                continue
            publicados["%s.%s" % (pid, i)] = l
            publicados.setdefault(i, l)
        piezas.append(pz)
    for tipo in dict.fromkeys(p["tipo"] for p in piezas):
        rg = reglas(tipo)
        if rg and hasattr(rg, "cerrar"):
            rg.cerrar([p for p in piezas if p["tipo"] == tipo], X)
    fallas = [p for p in piezas if p["tipo"] == "falla"]
    por_id = X.por_id
    por_id.update((p["id"], p) for p in piezas)
    prota = m.get("protagonista")
    if prota is None:
        prota = fallas[0]["id"] if fallas else None
        if prota:
            avisos.append("sin `protagonista`: el acento va a la primera falla («%s»)" % prota)
    elif prota not in por_id:
        raise Falla("M3D2", "`protagonista` «%s» no es el id de ninguna pieza (hay: %s)" % (prota, ", ".join(por_id) or "ninguna"))
    for p in piezas:
        p["protagonista"] = p["id"] == prota
    X.protagonista = prota

    # eventos: igual que las piezas (ficha + reglas del tipo); el adelanto de la portada lo dice la ficha
    catalogo_sfx = {e["id"] for e in cargar_json(os.path.join(RAIZ, "design", "sfx", "catalogo.json"))["efectos"]}

    def sfx_ok(o, que):
        if o.get("sfx") and o["sfx"] not in catalogo_sfx:
            raise Falla("M3D2", "%s: el efecto «%s» no está en design/sfx/catalogo.json" % (que, o["sfx"]))

    eventos = X.eventos
    for n, e in enumerate(m.get("eventos") or []):
        tipo = e.get("tipo")
        que = "evento %d (%s)" % (n, tipo)
        f = tipo_conocido(tipo, "evento", est, que, S.escala)
        sfx_ok(e, que)
        r = {"tipo": tipo, "t": float(e.get("t", -1)), "dur": float(e.get("dur", 0))}
        if e.get("sfx"):
            r["sfx"] = e["sfx"]
        r = resolver_entrada(validar_campos(e, f, que, por_id, avisos), f, que, X, r)
        ad = adelanto_de(tipo, r["dur"])
        if r["t"] <= PORTADA_T and ad is not None:
            r["adelanto"] = round(ad, 3)
        eventos.append(r)
    for tipo in dict.fromkeys(e["tipo"] for e in eventos):
        rg = reglas(tipo)
        if rg and hasattr(rg, "cerrar"):
            rg.cerrar([e for e in eventos if e["tipo"] == tipo], X)
    # lo que se mueve se resuelve con los eventos ya leídos (frenar, acelerar, mover, aparecer…): reglas → con_eventos;
    # dejan en X.moviles[id] su Movil (scripts/maqueta_tipos/_movimiento.py), que la cámara y las anotaciones siguen
    for tipo in dict.fromkeys(p["tipo"] for p in piezas):
        rg = reglas(tipo)
        if rg and hasattr(rg, "con_eventos"):
            rg.con_eventos([p for p in piezas if p["tipo"] == tipo], eventos, X)

    # cámara
    # la distancia va en la unidad de la escala (la ficha del mundo → camara.campo: dist_km en pais, dist_m en ciudad y
    # esquema); resuelta: `dist` en unidades de la escena (la que usan motor.js y los gates) y `dist_km` (la de Blender).
    # `mira` también puede ser algo que se mueve ({actor: id} · {flujo: id, n | carril, cerca, t}, con `desfase_m`): la
    # clave lleva `sigue` (lo lee motor.js) y `_pos` (t → (x, y, alt), para los gates; no viaja); `cenital: true` = elevación 89
    CF = S.ficha["camara"]
    campo, otro = CF["campo"], ("dist_m" if CF["campo"] == "dist_km" else "dist_km")
    camara = []
    for n, k in enumerate(m.get("camara") or []):
        que_c = "cámara, clave %d" % n
        sigue = None
        if MV.es_ref_movil(k.get("mira")):
            sigue = MV.resolver_ancla(k["mira"], X, que_c)[0]
            x0, y0 = MV.ancla_en(sigue, float(k.get("t", 0)), X.moviles)[:2]
            l = {"x": round(x0, 3), "y": round(y0, 3)}
        else:
            l = lugar(k.get("mira"), que_c)
        if k.get(campo) is None and k.get(otro) is not None:
            raise Falla("M3D3", "cámara, clave %d: en un mundo de escala %s la distancia va en `%s` (%s), no en `%s`" % (n, S.escala, campo, CF["unidad"], otro))
        d = float(k.get(campo, 0))
        el = 89.0 if k.get("cenital") is True else float(k.get("elevacion", 0))
        # `mira_lev_m`: la cámara mira a esa altura sobre el suelo (la copa de un árbol, la pluma de una grúa, media ladera)
        lev_c = float(k.get("mira_lev_m", 0) or 0) / S.unidad_m
        if sigue and not MV.ancla_en(sigue, float(k.get("t", 0)), X.moviles)[4]:
            raise Falla("M3D3", "cámara, clave %d: lo que sigue (%s) no está en su camino en t = %.2f s: elige otro vehículo (`cerca: <lugar>, t: s`) o mueve la clave" % (n, json.dumps(k.get("mira"), ensure_ascii=False), float(k.get("t", 0))))
        clave = {"t": float(k.get("t", -1)), "x": l["x"], "y": l["y"], "alt": round(alt_km(l["x"], l["y"]) + lev_c, 3), "lev": round(lev_c, 4),
                 "dist": d, "dist_km": d * S.km, "cerca": CF["cerca"], "azimut": float(k.get("azimut", 0)), "elevacion": el,
                 "fov": float(k.get("fov", 50))}
        if sigue:
            clave["sigue"] = sigue
            clave["_pos"] = (lambda A, lv: (lambda t: (lambda q: (q[0], q[1], alt_km(q[0], q[1]) + lv))(MV.ancla_en(A, t, X.moviles))))(sigue, lev_c)
        camara.append(clave)

    # marcas
    marcas = []
    for n, k in enumerate(m.get("marcas") or []):
        que = "marca %d «%s»" % (n, k.get("texto"))
        l = lugar(k.get("lugar"), que); sfx_ok(k, que)
        sep = k.get("separada_de")
        if sep is not None and (sep not in por_id or not tiene_regla(por_id[sep]["tipo"], "tramos")):
            raise Falla("M3D2", "%s: `separada_de` «%s» no es el id de una pieza que sea una línea (%s)" % (que, sep, ", ".join(t for t in tipos("pieza") if tiene_regla(t, "tramos"))))
        marcas.append({"t": float(k.get("t", -1)), "hasta": float(k.get("hasta", -1)), "x": l["x"], "y": l["y"], "z": round(alt_km(l["x"], l["y"]) + 0.3, 3),
                       "texto": str(k.get("texto") or ""), "sub": str(k.get("sub") or ""), "alto": int(k.get("alto", 110)), "sfx": k.get("sfx"),
                       "separada_de": sep})

    # anotaciones: la capa 2D atada al 3D (clase «anotacion» del catálogo: pulso, medida, etiqueta, reloj…), con `t` y
    # `hasta` como las marcas; sus anclas pueden ser lugares o algo que se mueve (se resuelven a {x, y} o {movil, n})
    anotaciones = []
    for n, o in enumerate(m.get("anotaciones") or []):
        tipo = o.get("tipo")
        que = "anotación %d (%s)" % (n, tipo)
        f = tipo_conocido(tipo, "anotacion", est, que, S.escala)
        sfx_ok(o, que)
        r = {"tipo": tipo, "t": float(o.get("t", -1)), "hasta": float(o.get("hasta", -1))}
        if o.get("sfx"):
            r["sfx"] = o["sfx"]
        anotaciones.append(resolver_entrada(validar_campos(o, f, que, por_id, avisos), f, que, X, r))

    # [motor blender, relieve «base»] el diorama recorta la caja del país: lo que cae fuera queda sobre el piso del estudio
    if est["motor"] == "blender" and (est.get("blender") or {}).get("relieve") == "base":
        cj, mg = S.fuente["caja"], float(est["blender"].get("base_margen_km", 30))
        (bx0, by0), (bx1, by1) = S.xy(cj["lon_min"], cj["lat_min"]), S.xy(cj["lon_max"], cj["lat_max"])
        dentro_base = lambda o: bx0 - mg <= o["x"] <= bx1 + mg and by0 - mg <= o["y"] <= by1 + mg
        fuera_b = ["la marca «%s»" % k["texto"] for k in marcas if not dentro_base(k)] + ["la clave de cámara %d" % n for n, k in enumerate(camara) if not dentro_base(k)]
        if fuera_b:
            avisos.append("estilo %s: la base del diorama es la caja del país (más %g km) y %s cae(n) fuera de ella, sobre el piso del estudio" % (est["id"], mg, ", ".join(fuera_b)))

    # capa
    C = m.get("capa") or {}
    dur = float(m.get("duracion_s", 0))
    capa = {"titulares": [dict(o) for o in C.get("titulares") or []], "cifras": [dict(o) for o in C.get("cifras") or []],
            "palabras": C.get("palabras") or [],
            "progreso": None if (Z.get("pieza") and not C.get("progreso")) else {"actos": (C.get("progreso") or {}).get("actos") or [0.0]},
            "seguir": C.get("seguir"), "aviso": C.get("aviso") or "", "pie": C.get("pie") or "", "handle": C.get("handle") or "", "subs_hasta": dur + 1,
            "aviso_ventanas": C.get("aviso_ventanas"),   # video con tramos: el aviso «Esquema» solo mientras se ve un esquema
            "pie_ventanas": C.get("pie_ventanas")}       # … y el pie de fuentes solo mientras se ve un mapa
    for o in capa["titulares"] + capa["cifras"] + ([C["seguir"]] if C.get("seguir") else []) + ([C["cierre"]] if C.get("cierre") else []):
        sfx_ok(o, "capa")
    ci = C.get("cierre")
    if ci:
        ws, t0 = str(ci.get("frase") or "").split(), float(ci.get("t", dur))
        # la frase se enciende con la voz si las últimas palabras de `palabras` son la frase; si no, a ritmo parejo
        cola = [p for p in capa["palabras"] if p["start"] >= t0 - 0.05][-len(ws):] if ws else []
        if ws and len(cola) == len(ws) and all(normal(a["text"]) == normal(b) for a, b in zip(cola, ws)):
            pal_c = [{"text": w, "start": p["start"], "end": p["end"]} for w, p in zip(ws, cola)]
            capa["subs_hasta"] = t0
        else:
            paso = min(0.34, max(0.12, (dur - t0) * 0.5 / max(1, len(ws))))
            pal_c = [{"text": w, "start": round(t0 + 0.35 + i * paso, 3), "end": round(t0 + 0.35 + (i + 1) * paso, 3)} for i, w in enumerate(ws)]
            if any(p["start"] >= t0 for p in capa["palabras"]):
                capa["subs_hasta"] = t0   # la pantalla ya dice la frase: sin subtítulo debajo
        fin_frase = pal_c[-1]["end"] if pal_c else t0 + 0.3
        capa["cierre"] = {"t": t0, "frase": ci.get("frase") or "", "palabras": pal_c, "redes": ci.get("redes") or [],
                          "t_redes": round(float(ci.get("t_redes", fin_frase + 0.35)), 3), "sfx": ci.get("sfx")}
    cfg = dict(est["cfg"])
    # LA HORA (mundo.hora, sobre un estilo que declare `horas`): el cielo, la luz, el tinte, las luces encendidas, las estrellas
    hora = mundo.get("hora")
    colores_est = dict(est["colores"])
    if hora is not None:
        horas = est.get("horas") or {}
        if hora not in horas:
            raise Falla("M3D1", "mundo.hora «%s»: el estilo «%s» %s" % (hora, est["id"], "tiene las horas %s" % ", ".join(horas) if horas else
                        "no tiene horas (usa un estilo de escena de cerca: %s)" % ", ".join(k for k, e2 in catalogo_estilos().items() if e2.get("horas"))))
        H = horas[hora]
        colores_est.update(H.get("colores") or {})
        cfg["luz"] = dict(cfg["luz"], **(H.get("luz") or {}))
        for k in ("tinte", "noche", "estrellas", "sombra_contacto", "nubes", "sombras", "resplandor"):
            if H.get(k) is not None:
                cfg[k] = H[k]
        cfg["hora"] = hora
    capas = mundo.get("capas") or {}
    malas = [k for k in capas if k not in CAPAS_MUNDO] if isinstance(capas, dict) else ["(no es un objeto)"]
    if malas:
        raise Falla("M3D1", "mundo.capas: «%s» no existe (hay: %s)" % (", ".join(malas), ", ".join(CAPAS_MUNDO)))
    cfg["capas"] = {k: bool(capas.get(k, True)) for k in CAPAS_MUNDO}
    col = {k: color(v) for k, v in colores_est.items()}
    return {
        "version": 1, "formato": formato, "W": Z["W"], "H": Z["H"], "fps": int(m.get("fps", 30)), "dur": dur, "estilo": est["id"], "paleta": m["paleta"],
        "motor": est["motor"], "blender": est.get("blender"),
        "col": col, "estilo_cfg": cfg, "capa_col": {k: color(v) for k, v in est["capa"].items() if isinstance(v, str)}, "radio": est["capa"]["radio"],
        "capa_num": {k: est["capa"].get(k, 1) for k in ("sombra_op", "vineta_op")},
        "exageracion": exag, "zona": Z, "protagonista": prota, "pieza": bool(Z.get("pieza")), "anfitrion": pal["fondo"],
        "solo_mundo": bool(m.get("_tramo")),
        **S.datos_R(),
        "mundo": dict(S.datos_mundo(), escala=S.escala, set=S.id, unidad_m=S.unidad_m, km=S.km, caja=[round(v, 3) for v in S.caja],
                      camara={"cerca": CF["cerca"], "lejos": CF["lejos"], "niebla": CF["niebla"]}, plano=S.ficha["plano"],
                      caminos=dict(S.caminos, **{k: v for p in piezas for k, v in (p.get("_caminos") or {}).items()}),
                      alturas=list(S.alturas), lugares=lugares_ctx(S, propios, lugar, publicados)),
        "piezas": [{k: v for k, v in p.items() if k not in ("_caminos", "_alturas", "_lugares")} for p in piezas], "camara": camara, "eventos": eventos, "marcas": marcas, "capa": capa,
        "anotaciones": anotaciones, "_set": S, "_pie_claves": S.fuente.get("pie_claves", {}), "_moviles": X.moviles,
    }


def lugares_ctx(S, propios, lugar, publicados=None):
    """Los lugares con nombre que el mundo le da a las piezas (ctx.lugares: {id: {x, y, nombre}}): los del mundo de
    esquema y de ciudad (los de un set de país son cientos: las piezas ya los reciben resueltos), los que publican las
    piezas (`_lugares`) y los de mundo.lugares."""
    ids = list(S.lugares) if S.escala != "pais" else []
    out = {}
    for i in dict.fromkeys(ids + list(publicados or {}) + list(propios)):
        l = lugar(i, "mundo.lugares «%s»" % i)
        out[i] = {"x": l["x"], "y": l["y"], "nombre": l["nombre"]}
    return out


# ---------- gates ----------
def caja_tarjeta(R, k, px, py):
    """La tarjeta de una marca con su ancla en (px, py): (x0, y0, x1, y1), estimada con las medidas de capa.css."""
    Z = R["zona"]
    ancho = max(0.56 * Z["marca_px"] * len(k["texto"]), 14.5 * len(k["sub"])) + 44
    alto = 26 + Z["marca_px"] + (30 if k["sub"] else 0)
    izq, der = Z["izq"] - 25, (Z["iconos_x"] - 10 if py - k["alto"] > Z["iconos_y"] else Z["W"] - Z["corte"] - 3)
    x0 = min(max(px - ancho / 2, izq), der - ancho)
    return x0, py - k["alto"] - alto, x0 + ancho, py - k["alto"]


def banda_titular(R, t):
    """Hasta dónde baja el titular vivo en t (estimado: kicker + renglones); sin titular, la barra de progreso."""
    Z, y = R["zona"], R["zona"]["banda_sin"]
    for o in R["capa"]["titulares"]:
        if o.get("t", 0) <= t < o.get("hasta", 0):
            por_renglon = max(8, int((Z["der"] - Z["izq"]) / (Z["tit_px"] * 0.44)))
            renglones = max(1, math.ceil(len(str(o.get("texto") or "")) / por_renglon))
            y = max(y, Z["tit_y"] + (40 if o.get("kicker") else 0) + renglones * Z["tit_px"] * 0.94 + 30)
    return y


def caja_cifra(R, o):
    Z = R["zona"]
    ancho = min(Z["cifra_ancho"], max(Z["cifra_px"] * 0.47 * len(str(o.get("valor") or "")), Z["rotulo_px"] * 0.52 * len(str(o.get("rotulo") or ""))))
    alto = Z["cifra_px"] * 0.84 + (10 + Z["rotulo_px"] * 1.05 if o.get("rotulo") else 0) + (34 if o.get("fuente") else 0)
    return Z["izq"], Z["cifra_fin"] - alto, Z["izq"] + ancho, Z["cifra_fin"]


def se_pisan(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def gates_formato(m, R):
    """Gates que dependen del encuadre (M3D3–M3D6, M3D9 y M3D11 en un formato). → lista de (gate, mensaje).
    En modo pieza (un lienzo libre) no aplican M3D5 ni M3D9."""
    out, Z, S, dur, fps = [], R["zona"], R["_set"], R["dur"], R["fps"]
    pieza = R["pieza"]
    W, H, cam = Z["W"], Z["H"], R["camara"]
    CF = S.ficha["camara"]
    F = lambda g, msg: out.append((g, msg))
    if dur <= 0:
        F("M3D1", "`duracion_s` debe ser mayor que 0"); return out

    # M3D3 · cámara
    if not cam:
        F("M3D3", "no hay claves de cámara: `camara` necesita al menos una clave en t = 0"); return out
    if abs(cam[0]["t"]) > 1e-6:
        F("M3D3", "la primera clave de cámara está en t = %.2f: debe empezar en t = 0" % cam[0]["t"])
    for n, (a, b) in enumerate(zip(cam, cam[1:])):
        if b["t"] <= a["t"]:
            F("M3D3", "las claves de cámara %d y %d no crecen en t (%.2f → %.2f): ordénalas" % (n, n + 1, a["t"], b["t"]))
    if out:
        return out
    if cam[-1]["t"] > dur + 1e-6:
        F("M3D3", "la última clave de cámara (t = %.2f) cae después del final (%.2f s)" % (cam[-1]["t"], dur))
    # el rango de la distancia es de la escala del mundo (su ficha → camara: pais 15–1600 km; ciudad y esquema en metros)
    rangos = {"dist": (CF["rango"][0], CF["rango"][1], CF["unidad"], CF["campo"]), "elevacion": (8, 89, "°", "elevacion"), "fov": (20, 75, "°", "fov")}
    for n, k in enumerate(cam):
        for campo, (lo, hi, u, nombre) in rangos.items():
            if not lo <= k[campo] <= hi:
                F("M3D3", "clave %d: `%s` = %g fuera de rango (%g–%g %s%s)" % (n, nombre, k[campo], lo, hi, u, "" if campo != "dist" else " en un mundo de escala %s" % S.escala))
    # velocidad tope por tramo (el pico de la curva es π/2 veces la media) y el ojo por encima del relieve
    for n, (a, b) in enumerate(zip(cam, cam[1:])):
        dt, pico = b["t"] - a["t"], math.pi / 2
        dmed = math.sqrt(a["dist"] * b["dist"])
        v = {"paneo": (math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / dmed / dt * pico, 0.85, "aleja las claves en t o acerca los puntos que mira"),
             "giro": (abs(b["azimut"] - a["azimut"]) / dt * pico, 45, "reparte el giro de azimut en más segundos (tope 45°/s)"),
             "cabeceo": (abs(b["elevacion"] - a["elevacion"]) / dt * pico, 30, "reparte el cambio de elevación en más segundos (tope 30°/s)"),
             "zoom": (abs(math.log(b["dist"] / a["dist"])) / dt * pico, 1.1, "reparte el cambio de %s en más segundos (tope ×3 por segundo)" % CF["campo"])}
        for nombre, (val, tope, arreglo) in v.items():
            if val > tope * 1.001:
                F("M3D3", "cámara, de la clave %d a la %d (%.1f s): %s demasiado rápido (%.2f, tope %.2f): marea; %s" % (n, n + 1, dt, nombre, val, tope, arreglo))
    paso = 0.1
    bajo = None
    for i in range(int(dur / paso) + 1):
        c = camara_en(cam, i * paso); ex, ey, ez = ojo_de(c)
        if S.dentro(ex, ey) and ez < S.suelo(ex, ey) + CF["despeje"]:
            bajo = i * paso; break
    if bajo is not None:
        F("M3D3", "la cámara se mete en el %s hacia t = %.1f s: sube `elevacion` o `%s`%s" % ("relieve" if S.escala == "pais" else "suelo", bajo, CF["campo"],
                                                                                        ", o baja `mundo.exageracion`" if S.escala != "esquema" else ""))

    proy = lambda t: proyector(camara_en(cam, t), W, H, H / 2 - Z["centro_y"])
    en_cuadro = lambda p, m_=0: p is not None and m_ <= p[0] <= W - m_ and Z["sup"] <= p[1] <= (H if pieza else Z["subs_y"])
    alt = lambda x, y: S.suelo(x, y) + 0.3

    # M3D4 · marcas
    marcas, cifras = R["marcas"], R["capa"]["cifras"]
    for n, k in enumerate(marcas):
        que = "marca «%s»" % k["texto"]
        if not (0 <= k["t"] < k["hasta"] <= dur + 1e-6):
            F("M3D4", "%s: su ventana (%.2f → %.2f) no cabe en el video (0 → %.2f)" % (que, k["t"], k["hasta"], dur)); continue
        nec = lectura_s(k["texto"], k["sub"])
        if k["hasta"] - k["t"] < nec - 1e-6:
            F("M3D4", "%s: dura %.1f s y se lee en %.1f s (0.5 s + 0.3 s por palabra): alarga `hasta`" % (que, k["hasta"] - k["t"], nec))
        ok = tot = 0; motivo = {}
        t = k["t"]
        while t < k["hasta"]:
            tot += 1
            p = proy(t)(k["x"], k["y"], k["z"])
            if p is None or not (Z["corte"] + 20 <= p[0] <= W - Z["corte"] - 20 and 0 <= p[1] <= H):
                motivo["el ancla sale del cuadro"] = motivo.get("el ancla sale del cuadro", 0) + 1
            else:
                c = caja_tarjeta(R, k, p[0], p[1])
                arriba = "la tarjeta queda a menos de %d px del borde de arriba" % MARGEN_PIEZA if pieza and c[1] < Z["banda_sin"] + 1 else "la tarjeta pisa la banda del titular"
                abajo = "el ancla queda a menos de %d px del borde de abajo" % MARGEN_PIEZA if pieza else "el ancla cae en la banda del pie"
                if c[1] < banda_titular(R, t):
                    motivo[arriba] = motivo.get(arriba, 0) + 1
                elif p[1] > Z["fin_marcas"]:
                    motivo[abajo] = motivo.get(abajo, 0) + 1
                else:
                    ok += 1
            t += 0.1
        if tot and ok / tot < 0.8:
            peor = max(motivo, key=motivo.get)
            F("M3D4", "%s: solo se ve bien %d %% de su ventana (mínimo 80 %%): %s. Mueve su ventana a cuando la cámara lo encuadra, cambia la clave de cámara, o ajusta `alto`"
              % (que, round(100 * ok / tot), peor))
    # M3D20 (aviso) · el rótulo no tapa lo que señala: la tarjeta de una marca no cubre al actor que la cámara sigue, al
    # protagonista ni a un actor que está junto a su ancla más de la mitad del tiempo que comparten en pantalla
    actores = [pz for pz in R["piezas"] if pz["tipo"] == "actor" and pz["id"] in R["_moviles"]]
    um = 1.0 / R["mundo"]["unidad_m"]
    for k in marcas if actores else ():
        if not (0 <= k["t"] < k["hasta"] <= dur + 1e-6):
            continue
        cuenta = {}
        t = k["t"]
        while t < k["hasta"]:
            c = camara_en(cam, t); pr = proyector(c, W, H, H / 2 - Z["centro_y"])
            p = pr(k["x"], k["y"], k["z"])
            if p is not None:
                tj = caja_tarjeta(R, k, p[0], p[1])
                sigue = next((q["sigue"].get("movil") for q in reversed(cam) if q["t"] <= t + 1e-6 and q.get("sigue")), None) if any(q.get("sigue") for q in cam) else None
                for pz in actores:
                    x, y, dx, dy, v, vis = R["_moviles"][pz["id"]].en(t, 0)
                    if not vis or not (pz["id"] == sigue or pz.get("protagonista") or math.hypot(x - k["x"], y - k["y"]) <= 0.15 * c["dist"]):
                        continue
                    l, a, h = (d * um for d in ESC._caja_de(ficha(pz["objeto"], "objeto") or {}, float(pz.get("tamano", 1))))
                    r = ESC._rect({"x": x, "y": y, "l": l, "a": a, "h": h, "dx": dx, "dy": dy, "lev": float(pz.get("lev", 0)) * um}, pr, S)
                    if not r or r[2] < 0 or r[0] > W or r[3] < 0 or r[1] > H:
                        continue
                    area = max(1.0, (r[2] - r[0]) * (r[3] - r[1]))
                    comun = max(0.0, min(r[2], tj[2]) - max(r[0], tj[0])) * max(0.0, min(r[3], tj[3]) - max(r[1], tj[1]))
                    n_v, n_c = cuenta.get(pz["id"], (0, 0))
                    cuenta[pz["id"]] = (n_v + 1, n_c + (comun / area >= 0.5))
            t += 0.1
        for pid, (n_v, n_c) in cuenta.items():
            if n_v >= 3 and n_c / float(n_v) > 0.5:
                R.setdefault("_avisos_formato", []).append("M3D20 la marca «%s» tapa a «%s» %d %% del tiempo que comparten en pantalla: sube su `alto` (p. ej. %d) o ánclala a un lugar al lado"
                                                           % (k["texto"], pid, round(100 * n_c / float(n_v)), int(k["alto"]) + 120))
    t = 0.0
    while t < dur:
        vivas = [k for k in marcas if k["t"] <= t < k["hasta"]]
        if len(vivas) > 3:
            F("M3D4", "hay %d marcas a la vez en t = %.1f s (máximo 3): escalona sus ventanas" % (len(vivas), t)); break
        t += 0.25
    for a in range(len(marcas)):
        for b in range(a + 1, len(marcas)):
            ka, kb = marcas[a], marcas[b]
            t0, t1 = max(ka["t"], kb["t"]), min(ka["hasta"], kb["hasta"])
            if t1 - t0 <= 0.3:
                continue
            pisa = tot = 0; t = t0
            while t < t1:
                tot += 1; pr = proy(t)
                pa, pb = pr(ka["x"], ka["y"], ka["z"]), pr(kb["x"], kb["y"], kb["z"])
                if pa and pb and se_pisan(caja_tarjeta(R, ka, *pa), caja_tarjeta(R, kb, *pb)):
                    pisa += 1
                t += 0.1
            if tot and pisa / tot > 0.25:
                F("M3D4", "las marcas «%s» y «%s» se pisan %d %% del tiempo que comparten: cambia el `alto` de una (p. ej. 190) o separa sus ventanas"
                  % (ka["texto"], kb["texto"], round(100 * pisa / tot)))

    # M3D4 · anotaciones (pulso, medida, etiqueta, reloj…): su ventana cabe, lo que dicen se alcanza a leer (sus reglas →
    # textos) y, si están atadas al 3D (reglas → anclas), al menos la mitad de sus anclas se ve en cuadro ≥ 80 % de su ventana
    for n, o in enumerate(R.get("anotaciones") or []):
        que = "anotación %d (%s)" % (n, o["tipo"])
        if not (0 <= o["t"] < o["hasta"] <= dur + 1e-6):
            F("M3D4", "%s: su ventana (%.2f → %.2f) no cabe en el video (0 → %.2f)" % (que, o["t"], o["hasta"], dur)); continue
        rg = reglas(o["tipo"])
        txt = [x for x in (rg.textos(o) if rg and hasattr(rg, "textos") else []) if x]
        if txt and o["hasta"] - o["t"] < lectura_s(*txt) - 1e-6:
            F("M3D4", "%s: «%s» dura %.1f s y se lee en %.1f s: alarga `hasta`" % (que, " · ".join(txt), o["hasta"] - o["t"], lectura_s(*txt)))
        anc = rg.anclas(o) if rg and hasattr(rg, "anclas") else []
        if not anc:
            continue
        ok = tot = 0; t = o["t"]
        while t < o["hasta"]:
            tot += 1; pr = proy(t); vistas = 0
            for A in anc:
                x, y, _, _, vis = MV.ancla_en(A, t, R["_moviles"])
                vistas += 1 if vis and en_cuadro(pr(x, y, S.suelo(x, y) + (A.get("lev") or 0) + 0.3)) else 0
            ok += vistas >= max(1, math.ceil(len(anc) / 2))
            t += 0.1
        if tot and ok / tot < 0.8:
            F("M3D4", "%s: lo que señala solo está en cuadro %d %% de su ventana (mínimo 80 %%): encuádralo con la cámara (o sigue al móvil con `mira`) o mueve su ventana"
              % (que, round(100 * ok / tot)))

    # M3D11 · separación: una marca que se declara `separada_de` una pieza no puede dibujarse pegada a ella
    por_id = {p["id"]: p for p in R["piezas"]}

    def linea_de(pz):   # la pieza como polilínea [(x, y, z, salto)] a pasos de ≤ 4 km, posada en el relieve (sus `tramos`)
        tramos = reglas(pz["tipo"]).tramos(pz)
        pts = []
        for tr in tramos:
            for (ax, ay, salto), (bx, by, _) in zip(tr, tr[1:]):
                n = 1 if salto else max(1, int(math.ceil(math.hypot(bx - ax, by - ay) / 4.0)))
                for i in range(n):
                    x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
                    pts.append((x, y, alt(x, y), salto and i == n - 1))
            pts.append((tr[-1][0], tr[-1][1], alt(tr[-1][0], tr[-1][1]), True))
        return pts
    for k in R["marcas"]:
        if not k.get("separada_de") or not (0 <= k["t"] < k["hasta"]):
            continue
        linea, ok, dists, t = linea_de(por_id[k["separada_de"]]), 0, [], k["t"]
        while t < k["hasta"]:
            pr = proy(t); a = pr(k["x"], k["y"], k["z"]); t += 0.1
            if a is None:
                continue
            P, d = [pr(x, y, z) for x, y, z, _ in linea], 1e9
            for i in range(len(P) - 1):
                if linea[i][3] or P[i] is None or P[i + 1] is None:
                    continue
                (x0, y0), (x1, y1) = P[i], P[i + 1]
                dx, dy = x1 - x0, y1 - y0
                h = min(1, max(0, ((a[0] - x0) * dx + (a[1] - y0) * dy) / (dx * dx + dy * dy or 1e-9)))
                d = min(d, math.hypot(a[0] - x0 - dx * h, a[1] - y0 - dy * h))
            dists.append(d); ok += d >= SEPARACION_PX
        if dists and ok / len(dists) < 0.8:
            dists.sort()
            F("M3D11", "marca «%s»: se declara separada de «%s» pero su ancla queda a %d px de ella en pantalla (lo normal en su ventana; %d px lo mínimo) y solo guarda ≥ %d px "
                       "el %d %% del tiempo (mínimo 80 %%): con la cámara rasante las distancias se aplastan. Usa una cámara más cenital (sube `elevacion`) o más cercana (baja `dist_km`)"
              % (k["texto"], k["separada_de"], round(dists[len(dists) // 2]), round(dists[0]), SEPARACION_PX, round(100 * ok / len(dists))))

    # M3D5 · titulares y cifras
    tit = sorted(R["capa"]["titulares"], key=lambda o: o.get("t", 0))
    for n, o in enumerate(tit):
        que = "titular «%s»" % o.get("texto")
        if not (0 <= o.get("t", -1) < o.get("hasta", -1) <= dur + 1e-6):
            F("M3D5", "%s: su ventana no cabe en el video" % que); continue
        nec = lectura_s(o.get("kicker"), o.get("texto"))
        if o["hasta"] - o["t"] < nec - 1e-6:
            F("M3D5", "%s: dura %.1f s y se lee en %.1f s: alarga `hasta`" % (que, o["hasta"] - o["t"], nec))
        if n and o["t"] < tit[n - 1]["hasta"] - 1e-6:
            F("M3D5", "%s empieza (%.2f) antes de que termine «%s» (%.2f): dos titulares no se pisan" % (que, o["t"], tit[n - 1].get("texto"), tit[n - 1]["hasta"]))
        por_renglon = max(8, int((Z["der"] - Z["izq"]) / (Z["tit_px"] * 0.44)))
        if len(str(o.get("texto") or "")) > por_renglon * 3:
            F("M3D5", "%s: no cabe en 3 renglones (≈ %d caracteres por renglón en %s): acórtalo" % (que, por_renglon, R["formato"]))
    ci, sg = R["capa"].get("cierre"), R["capa"].get("seguir")
    for o in cifras:
        que = "cifra «%s»" % o.get("valor")
        if not (0 <= o.get("t", -1) < o.get("hasta", -1) <= dur + 1e-6):
            F("M3D5", "%s: su ventana no cabe en el video" % que); continue
        nec = lectura_s(o.get("valor"), o.get("rotulo"))
        if o["hasta"] - o["t"] < nec - 1e-6:
            F("M3D5", "%s: dura %.1f s y se lee en %.1f s: alarga `hasta`" % (que, o["hasta"] - o["t"], nec))
        caja = caja_cifra(R, o)
        for k in marcas:
            t0, t1 = max(k["t"], o["t"]), min(k["hasta"], o["hasta"])
            if t1 - t0 <= 0.2:
                continue
            pisa = tot = 0; t = t0
            while t < t1:
                tot += 1; p = proy(t)(k["x"], k["y"], k["z"])
                if p and (se_pisan(caja, caja_tarjeta(R, k, *p)) or (caja[0] <= p[0] <= caja[2] and caja[1] <= p[1] <= caja[3])):
                    pisa += 1
                t += 0.1
            if tot and pisa / tot > 0.2:
                F("M3D5", "%s tapa la marca «%s» %d %% del tiempo que comparten: separa sus ventanas o cambia el encuadre" % (que, k["texto"], round(100 * pisa / tot)))
    for a in range(len(cifras)):
        for b in range(a + 1, len(cifras)):
            if min(cifras[a].get("hasta", 0), cifras[b].get("hasta", 0)) - max(cifras[a].get("t", 0), cifras[b].get("t", 0)) > 1e-6:
                F("M3D5", "las cifras «%s» y «%s» están a la vez en pantalla: una cifra por vez" % (cifras[a].get("valor"), cifras[b].get("valor")))
    if ci:
        for o in tit + cifras + marcas + list(R.get("anotaciones") or []):
            if o.get("hasta", 0) > ci["t"] + 1e-6:
                F("M3D5", "«%s» sigue en pantalla cuando entra el cierre (t = %.2f): termínalo antes" % (o.get("texto") or o.get("valor") or "anotación " + o.get("tipo", ""), ci["t"]))
    if sg:
        if not (0 <= sg.get("t", -1) and sg.get("t", 0) + sg.get("dur", 0) <= (ci["t"] if ci else dur) + 1e-6 and sg.get("dur", 0) >= 2):
            F("M3D5", "`seguir`: debe durar ≥ 2 s y terminar antes del cierre")
        elif R["formato"] == "9:16":
            for o in tit:
                if min(o["hasta"], sg["t"] + sg["dur"]) - max(o["t"], sg["t"]) > 1e-6 and len(str(o.get("texto") or "")) > 14:
                    F("M3D5", "`seguir` (%.1f → %.1f s) coincide con el titular «%s», que llega al botón: muévelo a un hueco entre titulares" % (sg["t"], sg["t"] + sg["dur"], o.get("texto")))

    # M3D9 · el gancho es un evento que se VE en el cuadro 0 (los tipos con `adelanto` en su ficha; de dónde sale: `origen`)
    G = {"R": R, "por_id": por_id, "m3": sys.modules[__name__]}
    visto, hay = False, False
    for e in R["eventos"]:
        if e["t"] > PORTADA_T or adelanto_de(e["tipo"], e["dur"]) is None:
            continue
        hay = True
        rg = reglas(e["tipo"])
        o = rg.origen(e, G) if rg and hasattr(rg, "origen") else None
        if o is None:
            visto = True; continue
        x, y = o
        visto = visto or en_cuadro(proy(0.0)(x, y, alt(x, y)))
    if not hay:
        F("M3D9", "el cuadro 0 es la portada y el gancho es un evento que se ve en él: ningún evento visible (%s) empieza en t ≤ %.1f s"
          % (", ".join(t for t in tipos("evento") if adelanto_de(t, 1) is not None), PORTADA_T))
    elif not visto:
        F("M3D9", "el evento del gancho empieza en t ≤ %.1f s pero su origen no está en cuadro en t = 0: encuádralo con la primera clave de cámara" % PORTADA_T)

    # M3D6 · eventos (dónde pasa cada uno en cada momento: `puntos` de las reglas de su tipo; sin ellos no se mide)
    for n, e in enumerate(R["eventos"]):
        que = "evento %d (%s)" % (n, e["tipo"])
        if not (e["t"] >= 0 and e["dur"] > 0 and e["t"] + e["dur"] <= dur + 1e-6):
            F("M3D6", "%s: de %.2f a %.2f s no cabe en la duración (%.2f s)" % (que, e["t"], e["t"] + e["dur"], dur)); continue
        rg = reglas(e["tipo"])
        ok, N = 0, 9
        for i in range(N):
            u = i / (N - 1); t = e["t"] + e["dur"] * u; pr = proy(t)
            pts = rg.puntos(e, u, G) if rg and hasattr(rg, "puntos") else []
            if not pts:
                ok += 1; continue
            vistos = sum(1 for (x, y) in pts if en_cuadro(pr(x, y, alt(x, y))))
            ok += 1 if vistos >= max(1, math.ceil(len(pts) / 2)) else 0
        if ok / N < 0.6:
            F("M3D6", "%s: su centro solo está en cámara %d %% del tiempo que dura (mínimo 60 %%): encuádralo con una clave de cámara o mueve el evento"
              % (que, round(100 * ok / N)))
    # M3D14 · lo que la cámara sigue no se traba: si la cámara va tras un actor (mira {actor: …}) y ese actor, que se venía
    # moviendo, se queda quieto más de TRABADO_S con la cámara todavía encima, se ve congelado (el barco que se detiene en
    # medio del mar porque su `mover` termina antes que el tramo). Arreglo: alargar el `mover` hasta que la cámara lo suelte.
    sigue_prev, quieto, se_movia, avisado = None, 0.0, False, set()
    for n, (a, b) in enumerate(zip(cam, cam[1:] + [None])):
        mov_id = (a.get("sigue") or {}).get("movil") if a.get("_pos") else None
        if mov_id != sigue_prev:          # la cámara empieza a seguir a otro (o a nadie): se cuenta de cero
            quieto, se_movia, sigue_prev = 0.0, False, mov_id
        if not mov_id or mov_id in avisado:
            continue
        fin = b["t"] if b else dur
        t, paso = a["t"], 0.25
        while t < fin - 1e-6:
            p0, p1 = a["_pos"](t), a["_pos"](min(t + paso, dur))
            mov = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * S.unidad_m > 0.05   # más de 5 cm en 0.25 s
            se_movia = se_movia or mov
            quieto = 0.0 if mov else quieto + paso
            if se_movia and quieto > TRABADO_S:
                avisado.add(mov_id)
                F("M3D14", "la cámara sigue a algo que se detuvo: desde %.1f s está quieto y la cámara sigue encima (clave %d): alarga su `mover` o su "
                  "movimiento hasta que la cámara lo suelte, o suelta la cámara" % (t - quieto + paso, n)); break
            t += paso
    # M3D15–M3D19 · la escena viva (scripts/maqueta_escena.py): un tramo de cerca está lleno, es variado y tiene vida
    if m.get("video") and not any(g in ("M3D1", "M3D3") for g, _ in out):   # `video: true` lo pone video3d.py: un video de /video-3d (no una pieza ni un caso de prueba); con la cámara mal no se mide
        out += ESC.gates(sys.modules[__name__], m, R)
    if pieza:   # el cuadro (titular, cifras, portada) es del anfitrión
        out = [x for x in out if x[0] not in ("M3D5", "M3D9")]
    tramo = m.get("_tramo")
    if tramo:   # un tramo (maqueta_tramos.py): la capa se revisa una vez, entera; aquí solo que una cifra no tape una marca, y
        # el gancho (M3D9) solo en el primer tramo
        out = [x for x in out if not (x[0] == "M3D5" and "tapa la marca" not in x[1]) and not (x[0] == "M3D9" and tramo.get("n", 0) > 0)]
    if m.get("_capa_global"):   # la capa de un video con tramos: solo sus gates (el mundo se revisa en cada tramo)
        out = [x for x in out if x[0] == "M3D5"]
    return out


def gates_comunes(m, R, avisos):
    """M3D1, M3D2 (ya revisados al resolver), M3D7, M3D8 y M3D12. → lista de (gate, mensaje). En modo pieza no aplica
    M3D7 y `capa` es opcional."""
    out, pieza = [], R["pieza"]
    F = lambda g, msg: out.append((g, msg) if not (pieza and g == "M3D7") else ("", ""))
    if m.get("version") != 1:
        F("M3D1", "`version` debe ser 1")
    if not (10 <= int(m.get("fps", 30)) <= 60):
        F("M3D1", "`fps` fuera de rango (10–60)")
    for k in ("mundo", "camara", "eventos") + (() if pieza else ("capa",)):
        if k not in m:
            F("M3D1", "falta `%s`" % k)
    C = m.get("capa") or {}
    tramo = bool(m.get("_tramo"))   # un tramo de un video con tramos: la capa (seguir, cierre) se revisa una vez, entera
    for k in ("pie", "handle") + (() if tramo else ("seguir", "cierre")):   # el aviso «Maqueta · no a escala» es opcional (usuario, 2026-11-14)
        if k == "pie" and tramo and R["mundo"]["escala"] == "esquema":
            continue   # un tramo de esquema no usa geodatos: el pie sale solo en los tramos de mapa (maqueta_tramos.partir)
        if not C.get(k):
            F("M3D7", "falta `capa.%s`" % k)
    ci = C.get("cierre") or {}
    if C.get("cierre") and not (ci.get("frase") and ci.get("redes") and 0 < ci.get("t", -1) < R["dur"]):
        F("M3D7", "`capa.cierre` necesita `t` dentro del video, `frase` y `redes`")
    if C.get("cierre") and R["dur"] - ci.get("t", 0) < 3:
        F("M3D7", "el cierre dura %.1f s: «Sígueme en» necesita al menos 3 s en pantalla" % (R["dur"] - ci.get("t", 0)))
    # las capas de geodatos que la maqueta usa: las del mundo (su ficha → `capas`: el relieve en pais y ciudad), los lugares
    # si hay marcas, y las que declaran las fichas de sus piezas (`capas`, siempre; o un parámetro con `capa`, si la pieza lo
    # trae o tiene defecto): el pie nombra la fuente de cada una (las claves del set: fuente.json → pie_claves; un esquema
    # no tiene geodatos)
    usadas = capas_usadas(m["mundo"], R["mundo"]["escala"], bool(R["marcas"]))
    for capa in sorted(usadas):
        clave = R["_pie_claves"].get(capa)
        if clave and clave.lower() not in str(C.get("pie") or "").lower():
            F("M3D7", "el pie no nombra la fuente de la capa «%s» (debe decir «%s»; texto sugerido en design/sets3d/%s/fuente.json → pie)" % (capa, clave, R["_set"].id))
    if len(str(C.get("pie") or "")) > 132:
        F("M3D7", "el pie tiene %d caracteres y caben ≈ 132 (dos renglones): abrévialo" % len(C["pie"]))

    def busca_estilo(o, ruta):   # M3D8: ningún `estilo` fuera del de primer nivel
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "estilo" and ruta:
                    F("M3D8", "hay un `estilo` en %s: el estilo es uno solo por video (el de primer nivel)" % ruta)
                busca_estilo(v, (ruta + "." if ruta else "") + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                busca_estilo(v, "%s[%d]" % (ruta, i))
    busca_estilo(m, "")
    out += esquema_honesto(m, R, avisos)
    if not pieza and not any(o.get("t", 9) <= PORTADA_T for o in R["capa"]["titulares"]):
        avisos.append("ningún titular empieza en t ≤ %.1f: el cuadro 0 (la portada) sale sin titular" % PORTADA_T)
    pal = R["capa"]["palabras"]
    if any(not (isinstance(p, dict) and "text" in p and p.get("start", -1) >= 0 and p.get("end", 0) >= p.get("start", 0)) for p in pal):
        F("M3D1", "`capa.palabras`: cada palabra lleva text, start y end (segundos)")
    actos = (R["capa"]["progreso"] or {}).get("actos") or [0.0]
    if actos != sorted(actos) or (actos and abs(actos[0]) > 1e-6) or (actos and actos[-1] >= R["dur"]):
        F("M3D1", "`capa.progreso.actos` son los segundos en que empieza cada acto: crecientes, desde 0 y antes del final")
    return [x for x in out if x[0]]


NOMBRES_REALES = {}


def nombres_reales():
    """Los nombres de los lugares reales de los sets de escala pais (design/sets3d/guatemala/lugares.json), normalizados
    con espacios entre palabras: lo que un esquema no puede nombrar (M3D12)."""
    if "n" not in NOMBRES_REALES:
        def norm(t):
            t = unicodedata.normalize("NFD", str(t).lower())
            return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(c for c in t if unicodedata.category(c) != "Mn")).split())
        nombres = set()
        for sid in lista_sets("pais"):
            try:
                L = cargar_json(os.path.join(SETS, sid, "lugares.json"))["lugares"]
            except (OSError, ValueError, KeyError):
                continue
            nombres.update(norm(l.get("nombre", "")) for l in L.values())
        NOMBRES_REALES["n"], NOMBRES_REALES["norm"] = {x for x in nombres if x}, norm
    return NOMBRES_REALES["n"], NOMBRES_REALES["norm"]


def esquema_honesto(m, R, avisos):
    """M3D12 · un mundo de escala ESQUEMA es un lugar genérico: no afirma geografía. Lleva `capa.aviso` con «Esquema» (en
    modo pieza sin capa, el aviso lo pone el anfitrión) y ni sus lugares (los de la receta y los de mundo.lugares: id y
    nombre) ni el texto de sus marcas llevan el nombre de un lugar real (design/sets3d/guatemala/lugares.json)."""
    if R["mundo"]["escala"] != "esquema":
        return []
    out, C = [], m.get("capa")
    reales, norm = nombres_reales()
    if C is not None or not R["pieza"]:
        if "esquema" not in norm((C or {}).get("aviso") or ""):
            out.append(("M3D12", "un mundo de escala esquema no es un lugar real: lleva `capa.aviso` con «Esquema» (p. ej. «Esquema · no es un lugar real»)"))
    else:
        avisos.append("M3D12 modo pieza sin capa: la mesa que aloja este esquema debe decir «Esquema» en pantalla")
    for lid, l in sorted(R["mundo"].get("lugares", {}).items()):
        for t in dict.fromkeys((lid.replace("-", " "), l.get("nombre") or "")):
            if norm(t) in reales:
                out.append(("M3D12", "el lugar «%s» del esquema se llama como un lugar real («%s»): un esquema usa nombres genéricos (centro, norte, plaza, pueblo…)" % (lid, t)))
                break
    for k in R["marcas"]:
        txt = " %s %s " % (norm(k.get("texto")), norm(k.get("sub")))
        real = next((r for r in sorted(reales) if len(r) >= 4 and " %s " % r in txt), None)
        if real:
            out.append(("M3D12", "la marca «%s» nombra un lugar real («%s») sobre un esquema: el esquema no es ese lugar; usa un mundo de ciudad o de país, o un nombre genérico" % (k["texto"], real)))
    return out


def revisar(ruta, formatos):
    """→ (fallas, avisos). fallas: lista de cadenas «M3Dn [formato] …»."""
    try:
        m = cargar_json(ruta)
    except (OSError, ValueError) as e:
        return ["M3D1 no se pudo leer %s: %s" % (ruta, e)], []
    return revisar_m(m, formatos)


def revisar_m(m, formatos):
    fallas, avisos = [], []
    if not isinstance(m, dict):
        return ["M3D1 el maqueta.json debe ser un objeto"], avisos
    if TR.es_tramos(m):    # varios mundos: M3D13 y los gates de cada tramo y de la capa (scripts/maqueta_tramos.py)
        return TR.revisar_m(m, formatos, sys.modules[__name__])
    comunes = False
    for f in formatos:
        try:
            R = resolver(m, f, avisos if not comunes else [])
        except Falla as e:
            return ["%s %s" % (e.args[0], e.args[1])], avisos
        except (KeyError, TypeError, ValueError) as e:
            return ["M3D1 forma inválida: %s (%s)" % (e, type(e).__name__)], avisos
        if not comunes:
            fallas += ["%s %s" % x for x in gates_comunes(m, R, avisos)]
            comunes = True
        fallas += ["%s [%s] %s" % (g, f, msg) for g, msg in gates_formato(m, R)]
        # lo que los gates de este formato avisan sin fallar (M3D18: fuera de su distancia; M3D20: un rótulo que tapa)
        avisos += ["%s [%s] %s" % (x.split(" ", 1)[0], f, x.split(" ", 1)[1]) for x in (R.get("_avisos_escena") or []) + (R.get("_avisos_formato") or [])]
    if len(formatos) < 2 and not es_pieza(formatos[0]):
        avisos.append("M3D10 pide los dos formatos: se revisó solo %s (corre check sin --formato o con --formato ambos)" % formatos[0])
    return fallas, list(dict.fromkeys(avisos))


# ---------- proyecto de HyperFrames ----------
def escribir_proyecto(m, formato, destino, fotos=None, placa_externa=False):
    """El proyecto de HyperFrames. Motor three: el lienzo WebGL (motor.js). Motor blender (MODO PLACA): el mundo llega ya
    renderizado y aquí solo va la capa 2D encima: un <video> (assets/placa.mp4, lo pone el render) o, para cuadros
    sueltos, las `fotos` (números de cuadro → assets/placa/c_NNNNN.png); las marcas, ya proyectadas por cuadro."""
    R = resolver(m, formato)
    S = R.pop("_set"); R.pop("_pie_claves"); R.pop("_moviles", None)
    for k in R["camara"]:
        k.pop("_pos", None)
    Z, C, D, esc = R["zona"], R["capa"], R["dur"], lambda s: html.escape(str(s), quote=True)
    placa = R["motor"] == "blender" or placa_externa   # placa_externa: la capa de un video con tramos (el mundo ya viene grabado)
    solo_mundo = R["solo_mundo"]                       # un tramo: el mundo, sus marcas y sus anotaciones; la capa va aparte, encima
    if solo_mundo:   # el tramo no dibuja la capa: los titulares van ocultos (capa.js los mide para que las marcas no los pisen)
        R["capa"] = C = dict(C, cifras=[], palabras=[], progreso=None, seguir=None, cierre=None, aviso="", pie="", handle="")
    A = os.path.join(destino, "assets")
    shutil.rmtree(A, ignore_errors=True)
    for d in ("fonts",) + (("placa",) if placa else ("three", "set")):
        os.makedirs(os.path.join(A, d))
    V = os.path.join(RAIZ, "design", "vendor")
    shutil.copyfile(versiones.GSAP_JS, os.path.join(A, "gsap.min.js"))
    for f in ("archivo-wdth.woff2", "jetbrains-mono-var.woff2"):
        shutil.copyfile(os.path.join(RAIZ, "design", "fonts", f), os.path.join(A, "fonts", f))
    if placa:
        R["anclas"] = anclas_de(R)
        R["placa"] = {"fotos": sorted(fotos)} if fotos else {"video": "assets/placa.mp4"}
        for k in ("piezas", "eventos", "camara", "relieve", "frontera", "blender", "estilo_cfg", "mundo"):   # la capa no los usa: el mundo ya viene dibujado
            R.pop(k, None)
        if fotos:
            fondo = '<div id="placa" class="clip" data-start="0" data-duration="@D@" data-track-index="0">%s</div>' % "".join(
                '<img class="placa-foto" data-n="%d" src="assets/placa/c_%05d.png" alt="" />' % (n, n) for n in sorted(fotos))
        else:
            fondo = '<video id="placa" class="clip" data-start="0" data-duration="@D@" data-track-index="0" muted playsinline src="assets/placa.mp4"></video>'
        guion_motor = '<script src="assets/placa.js"></script>'
    else:
        for f in ("three.module.js", "three.core.js", "LICENSE"):
            shutil.copyfile(os.path.join(versiones.THREE_DIR, f), os.path.join(A, "three", f))
        for origen, nombre in S.archivos():                # los archivos del mundo (pais: relieve.png)
            shutil.copyfile(origen, os.path.join(A, "set", nombre))
        fondo = '<canvas id="gl" class="clip" width="@W@" height="@H@" data-start="0" data-duration="@D@" data-track-index="0"></canvas>'
        # el vocabulario: SOLO los módulos que usa esta maqueta, que se registran en window.MAQ antes de motor.js (módulo, diferido)
        mods = modulos_de(R)
        for rel_m in mods:
            os.makedirs(os.path.join(A, "modulos", os.path.dirname(rel_m)), exist_ok=True)
            shutil.copyfile(os.path.join(MOTOR, rel_m), os.path.join(A, "modulos", rel_m))
        guion_motor = "".join('<script src="assets/modulos/%s"></script>\n    ' % x for x in mods) + '<script type="module" src="assets/motor.js"></script>'
    for f in ("placa.js" if placa else "motor.js", "capa.js"):
        shutil.copyfile(os.path.join(MOTOR, f), os.path.join(A, f))
    with open(os.path.join(A, "datos.js"), "w", encoding="utf-8") as f:
        f.write("window.MAQUETA = " + json.dumps(R, ensure_ascii=False, separators=(",", ":")) + ";\n")

    cc = R["capa_col"]
    vars_css = {"w": "%dpx" % Z["W"], "h": "%dpx" % Z["H"], "bg": R["col"]["fondo"], "ink": cc["ink"], "tinta": cc["tinta"], "sombra": cc["sombra"],
                "tarjeta-bg": cc["tarjeta_bg"], "tarjeta-ink": cc["tarjeta_ink"], "radio": "%dpx" % R["radio"], "izq": "%dpx" % Z["izq"],
                "col": "%dpx" % (Z["der"] - Z["izq"]), "sombra-op": R["capa_num"]["sombra_op"], "vineta-op": R["capa_num"]["vineta_op"],
                "anfitrion": R["anfitrion"]}
    for k in ("barra_y", "tit_y", "tit_px", "cifra_fin", "cifra_px", "rotulo_px", "cifra_ancho", "fila_y", "subs_y", "subs_px", "pie_y", "marca_px", "seguir_y",
              "seguir_der", "cierre_y", "cierre_gap", "frase_px", "red_px", "red_txt", "red_gap", "sombra_arriba", "sombra_abajo"):
        vars_css[k.replace("_", "-")] = "%dpx" % Z[k]
    raiz_css = ":root { " + " ".join("--%s: %s;" % kv for kv in vars_css.items()) + " }"

    def clip(i, ini, d, pista, dentro, clase="marco"):
        return '      <div id="%s" class="clip %s" data-start="%s" data-duration="%s" data-track-index="%d">%s</div>' % (i, clase, round(ini, 3), round(max(0.04, d), 3), pista, dentro)
    pieza = R["pieza"]
    # modo pieza: sin degradados para el texto; una viñeta que funde los bordes con el fondo del anfitrión (el de la paleta)
    L = [] if solo_mundo else [clip("sombras", 0, D, 1, '<div class="borde"></div>' if pieza else '<div class="sombra vineta"></div><div class="sombra arriba"></div><div class="sombra abajo"></div>')]
    ci = C.get("cierre")
    if ci:
        L.append(clip("velo", ci["t"], D - ci["t"], 2, '<div class="velo"></div>'))
    if C["progreso"]:
        L.append(clip("arriba", 0, D, 3, '<div id="progreso">%s</div>' % ("<i><b></b></i>" * len(C["progreso"]["actos"]))))
    for n, o in enumerate(C["titulares"]):
        k = '<div class="kicker">%s</div>' % esc(o["kicker"]) if o.get("kicker") else ""
        L.append(clip("tit-%d" % n, o["t"], o["hasta"] - o["t"], 4, '<div class="titulo">%s<div class="texto">%s</div></div>' % (k, esc(o.get("texto", "")))).replace(
            'class="clip marco"', 'class="clip marco" style="visibility: hidden"' if solo_mundo else 'class="clip marco"'))
    for n, o in enumerate(C["cifras"]):
        r = '<div class="rotulo">%s</div>' % esc(o["rotulo"]) if o.get("rotulo") else ""
        fu = '<div class="fuente">Fuente: %s</div>' % esc(o["fuente"]) if o.get("fuente") else ""
        L.append(clip("cifra-%d" % n, o["t"], o["hasta"] - o["t"], 5, '<div class="cifra"><div class="valor">%s</div>%s%s</div>' % (esc(o.get("valor", "")), r, fu)))
    libres = []   # pistas de las marcas: las que se solapan van en pistas distintas
    for n, k in sorted(enumerate(R["marcas"]), key=lambda x: x[1]["t"]):
        pista = next((i for i, fin in enumerate(libres) if fin <= k["t"]), len(libres))
        libres[pista:pista + 1] = [k["hasta"]]
        sub = "<i>%s</i>" % esc(k["sub"]) if k["sub"] else ""
        L.append(clip("marca-%d" % n, k["t"], k["hasta"] - k["t"], 6 + pista,
                      '<div class="pin" style="--alto: %dpx"><div class="stem"></div><div class="dot"></div><div class="card"><b>%s</b>%s</div></div>' % (k["alto"], esc(k["texto"]), sub)))
    p0 = 6 + max(1, len(libres))
    fila = ('<span class="aviso">%s</span>' % esc(C["aviso"]) if C["aviso"] else "") + ('<span class="handle">%s</span>' % esc(C["handle"]) if C["handle"] else "")
    D_fila = ci["t"] if ci else D   # el cierre ya muestra las redes: la fila (aviso y handle) se va cuando entra
    if C.get("aviso_ventanas") is not None and C["aviso"]:   # tramos: el aviso solo en sus ventanas; fuera, el handle solo
        solo = '<span class="handle">%s</span>' % esc(C["handle"]) if C["handle"] else ""
        cortes = sorted({0.0, D_fila} | {min(D_fila, max(0.0, float(x))) for v in C["aviso_ventanas"] for x in v})
        for i, (a0, a1) in enumerate(zip(cortes, cortes[1:])):
            con = any(v[0] <= (a0 + a1) / 2 < v[1] for v in C["aviso_ventanas"])
            if a1 - a0 > 1e-3 and (con or solo):
                L.append(clip("filac-%d" % i, a0, a1 - a0, p0, '<div id="fila">%s</div>' % (fila if con else solo)))
    elif fila:   # sin aviso, el handle ocupa su lugar
        L.append(clip("filac", 0, D_fila, p0, '<div id="fila">%s</div>' % fila))
    if C["palabras"]:
        L.append(clip("subsc", 0, D, p0 + 1, '<div id="subs"></div>'))
    if C["pie"] and C.get("pie_ventanas") is not None:   # tramos: el pie solo sobre los mapas (ventanas seguidas, una sola)
        juntas = []
        for v0, v1 in sorted((max(0.0, float(v[0])), min(D, float(v[1]))) for v in C["pie_ventanas"]):
            if juntas and v0 - juntas[-1][1] < 1e-3:
                juntas[-1][1] = max(juntas[-1][1], v1)
            elif v1 - v0 > 1e-3:
                juntas.append([v0, v1])
        for i, (v0, v1) in enumerate(juntas):
            L.append(clip("piec-%d" % i, v0, v1 - v0, p0 + 2, '<div id="pie">%s</div>' % esc(C["pie"])))
    elif C["pie"]:
        L.append(clip("piec", 0, D, p0 + 2, '<div id="pie">%s</div>' % esc(C["pie"])))
    boton = ('<div class="bt"><span class="lbl">Seguir</span><span class="ya"><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Siguiendo</span></div>')
    if C.get("seguir"):
        sg = C["seguir"]
        L.append(clip("seguir", sg["t"], sg["dur"], p0 + 3, '<div class="vseguir">%s<div class="cam"><svg viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>'
                      '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg></div></div>' % boton))
    if ci:
        frase = "".join("<span>%s</span>" % esc(p["text"]) for p in ci["palabras"])
        redes = "".join('<div class="c">%s<span class="h">%s</span></div>' % (
            '<div class="i"><svg viewBox="0 0 24 24">%s</svg></div>' % ICONOS[normal(r.get("nombre"))] if normal(r.get("nombre")) in ICONOS else "", esc(r.get("handle", ""))) for r in ci["redes"])
        L.append(clip("cierre", ci["t"], D - ci["t"], p0 + 4, '<div class="col"><div class="frase">%s</div><div class="sigue%s"><div class="fila"><span class="t">Sígueme en</span>%s</div>%s</div></div>'
                      % (frase, " enfila" if formato == "4:5" else "", boton, redes)))
    if R.get("anotaciones"):   # las anotaciones (pulso, medida, etiqueta, reloj) las dibuja capa.js con sus módulos: una capa SVG
        # y una de texto, debajo de titulares, cifras y subtítulos (van justo tras las sombras en el DOM; su pista, aparte)
        L.insert(1, clip("anot", 0, D, p0 + 5, '<div id="anot"><svg class="anot-svg" width="%d" height="%d" viewBox="0 0 %d %d"></svg><div class="anot-txt"></div></div>'
                         % (Z["W"], Z["H"], Z["W"], Z["H"])))
    doc = cargar_texto(os.path.join(MOTOR, "plantilla.html"))
    for k, v in (("@FONDO@", fondo), ("@MOTOR@", guion_motor), ("@RAIZ_CSS@", raiz_css), ("@CSS@", cargar_texto(os.path.join(MOTOR, "capa.css"))), ("@W@", str(Z["W"])), ("@H@", str(Z["H"])),
                 ("@D@", str(D)), ("@FPS@", str(R["fps"])), ("@ESTILO@", R["estilo"]), ("@CAPA@", "\n".join(L))):
        doc = doc.replace(k, v)
    with open(os.path.join(destino, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    return R


def blender_bin():
    """El ejecutable de Blender: $BLENDER, la app de macOS o `blender` en el PATH. None si no está instalado."""
    for c in (os.environ.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender"), shutil.which("Blender")):
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def motor_de(m):
    return (catalogo_estilos().get((m or {}).get("estilo")) or {}).get("motor", "three")


def anclas_de(R):
    """MODO PLACA: dónde cae cada marca en cada cuadro de su ventana, con la MISMA cámara y proyección que los gates (y
    que la cámara de Blender, que maqueta_blender.py comprueba al píxel). → [{n0, p: [[px, py] | None, …]}] por marca."""
    Z, fps, out = R["zona"], R["fps"], []
    sube, nmax = Z["H"] / 2 - Z["centro_y"], int(round(R["dur"] * R["fps"]))
    for k in R["marcas"]:
        n0, n1 = max(0, int(math.floor(k["t"] * fps)) - 1), min(nmax, int(math.ceil(k["hasta"] * fps)) + 1)
        pts = []
        for n in range(n0, n1 + 1):
            q = proyector(camara_en(R["camara"], n / fps), Z["W"], Z["H"], sube)(k["x"], k["y"], k["z"])
            pts.append([round(q[0], 2), round(q[1], 2)] if q else None)
        out.append({"n0": n0, "p": pts})
    return out


def placa_blender(ruta_maqueta, formato, destino, registro, cuadros=None, total=0):
    """Lanza Blender sin ventana y deja en `destino` los PNG de la placa (c_NNNNN.png): los `cuadros` pedidos, o todos
    (`total` cuadros; con MAQUETA_BLENDER_PROCESOS=N se reparten en N procesos de Blender a la vez: cada cuadro es
    independiente, así que el resultado es el mismo). → (0 ok | 1 falla, segundos, cuántos PNG)."""
    exe = blender_bin()
    if not exe:
        print("FALLA motor blender: no encuentro Blender (≥ 5.0). Instálalo en /Applications o apunta $BLENDER a su ejecutable; "
              "o usa un estilo de three (color, noche, contorno, voxel, plano)")
        return 1, 0.0, 0
    shutil.rmtree(destino, ignore_errors=True)
    os.makedirs(destino)
    cmd = [exe, "-b", "--factory-startup", "--python-exit-code", "1", "--python", BLENDER_PY, "--", "--maqueta", os.path.abspath(ruta_maqueta),
           "--formato", formato, "--salida", os.path.abspath(destino)]
    try:
        procesos = max(1, min(4, int(os.environ.get("MAQUETA_BLENDER_PROCESOS", "1"))))
    except ValueError:
        procesos = 1
    if cuadros is not None:
        tandas = [["--cuadros", ",".join(str(n) for n in cuadros)]]
    elif procesos > 1 and total >= 4 * procesos:
        cortes = [round(total * k / procesos) for k in range(procesos + 1)]
        tandas = [["--todo", "--desde", str(a), "--hasta", str(b)] for a, b in zip(cortes, cortes[1:])]
    else:
        tandas = [["--todo"]]
    t0 = time.time()
    vivos = []
    for k, tanda in enumerate(tandas):
        reg = registro if k == 0 else "%s.%d" % (registro, k + 1)
        fh = open(reg, "w", encoding="utf-8")
        vivos.append((subprocess.Popen(cmd + tanda, cwd=os.path.dirname(os.path.abspath(ruta_maqueta)), stdout=fh, stderr=subprocess.STDOUT, text=True), fh, reg))
    mal = None
    for pr, fh, reg in vivos:
        rc = pr.wait()
        fh.close()
        if rc != 0 and mal is None:
            mal = (rc, reg)
    seg = time.time() - t0
    pngs = [x for x in os.listdir(destino) if re.fullmatch(r"c_\d{5}\.png", x)]
    if mal:
        lineas = [l for l in cargar_texto(mal[1]).splitlines() if re.search(r"FALLA|Error|Traceback", l)]
        print("FALLA placa de Blender (%s): devolvió %d%s (ver %s)" % (formato, mal[0], ": " + lineas[-1].strip() if lineas else "", mal[1]))
        return 1, seg, len(pngs)
    return 0, seg, len(pngs)


def cargar_texto(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def efectos_de(m):
    if TR.es_tramos(m):
        return TR.efectos(m)
    C = m.get("capa") or {}
    lista = [[e["t"], e["sfx"]] for e in m.get("eventos") or [] if e.get("sfx")]
    lista += [[o["t"], o["sfx"]] for k in ("titulares", "cifras") for o in C.get(k) or [] if o.get("sfx")]
    lista += [[o["t"], o["sfx"]] for k in ("marcas", "anotaciones") for o in m.get(k) or [] if o.get("sfx")]
    lista += [[C[k]["t"], C[k]["sfx"]] for k in ("seguir", "cierre") if (C.get(k) or {}).get("sfx")]
    return sorted([round(float(t), 3), s] for t, s in lista)


RENDER_LIMITE_BASE_S, RENDER_LIMITE_POR_S = 600, 40   # un render 3D va a ≈ 2–4× la duración; a 40× (más lo fijo) está colgado


def limite_render(dur_s):
    """Cuánto puede tardar un render antes de darlo por colgado (m234). MAQUETA_RENDER_LIMITE_S lo fija a mano."""
    try:
        return max(1.0, float(os.environ["MAQUETA_RENDER_LIMITE_S"]))
    except (KeyError, ValueError):
        return RENDER_LIMITE_BASE_S + RENDER_LIMITE_POR_S * max(0.0, float(dur_s or 0))


def capas_usadas(mundo, escala, hay_marcas):
    """Las capas de geodatos que un mundo usa: las de su escala, los lugares si hay marcas y las de las fichas de sus piezas
    (`capas`, o un parámetro con `capa` que la pieza trae o tiene por defecto). De aquí salen el gate M3D7 y el pie."""
    usadas = set((ficha(escala, "mundo") or {}).get("capas") or []) | ({"lugares"} if hay_marcas else set())
    for mp in mundo.get("piezas") or []:
        fp = ficha(mp.get("tipo"), "pieza") or {}
        usadas.update(fp.get("capas") or [])
        for nombre, d in (fp.get("parametros") or {}).items():
            if d.get("capa") and (mp.get(nombre) if mp.get(nombre) is not None else d.get("defecto")):
                usadas.add(d["capa"])
    return usadas


def correr(cmd, cwd, registro=None, limite=None):
    """Corre `cmd` y guarda su salida en `registro`. Con `limite` (segundos), si se pasa se detiene con todo lo que lanzó
    (npx → node → Chrome → ffmpeg: si queda vivo, sostiene el candado de HyperFrames) y devuelve código 124."""
    import signal
    t0 = time.time()
    if limite is None:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    else:
        pr = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            out, err = pr.communicate(timeout=limite)
            p = subprocess.CompletedProcess(cmd, pr.returncode, out, err)
        except subprocess.TimeoutExpired:
            for senal in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(pr.pid, senal)
                except OSError:
                    break
                try:
                    pr.wait(timeout=8)
                    break
                except subprocess.TimeoutExpired:
                    pass
            out, err = pr.communicate()
            p = subprocess.CompletedProcess(cmd, 124, out or "", (err or "") + "\nLÍMITE: el render pasó %.0f s y se detuvo (MAQUETA_RENDER_LIMITE_S=<segundos> lo sube)" % limite)
    if registro:
        with open(registro, "w", encoding="utf-8") as f:
            f.write(p.stdout + "\n" + p.stderr)
    return p, time.time() - t0


# ---------- comandos ----------
def formatos_de(a):
    if getattr(a, "pieza", False) or (getattr(a, "lienzo", None) and a.cmd == "pieza"):
        if not getattr(a, "lienzo", None):
            raise Falla("M3D1", "--pieza necesita --lienzo ANCHOxALTO (p. ej. 950x1040)")
        return ["%dx%d" % lienzo_de(a.lienzo)]
    if getattr(a, "lienzo", None):
        raise Falla("M3D1", "--lienzo solo vale con --pieza")
    return ["9:16", "4:5"] if a.formato == "ambos" else [a.formato]


def cmd_check(a):
    fallas, avisos = revisar(a.maqueta, formatos_de(a))
    for x in avisos:
        print("  aviso · " + x)
    for x in fallas:
        print("  FALLA " + x)
    que = "modo pieza, lienzo %s: M3D1–M3D4, M3D6, M3D8, M3D11 y M3D12 OK" % formatos_de(a)[0] if es_pieza(formatos_de(a)[0]) else "M3D1–M3D%s OK (%s)%s" % (("19" if cargar_json(a.maqueta).get("video") else "14") if TR.es_tramos(cargar_json(a.maqueta)) else "12, M3D14", ", ".join(formatos_de(a)), " · %d tramos" % len(cargar_json(a.maqueta)["tramos"]) if TR.es_tramos(cargar_json(a.maqueta)) else "")
    print("%s: %s" % (a.maqueta, que if not fallas else "%d falla(s)" % len(fallas)))
    return 1 if fallas else 0


def exigir_check(a, formatos):
    fallas, _ = revisar(a.maqueta, formatos)
    if fallas:
        for x in fallas:
            print("  FALLA " + x)
        print("la maqueta no pasa los gates: corrige y vuelve a correr (maqueta3d.py check %s)" % a.maqueta)
        return False
    return True


def cmd_proyecto(a):
    m = cargar_json(a.maqueta)
    for f in formatos_de(a):
        try:
            d = os.path.join(a.dir, CARPETA[f], "proyecto")
            os.makedirs(d, exist_ok=True)
            R = escribir_proyecto(m, f, d)
        except Falla as e:
            print("  FALLA %s %s" % e.args); return 1
        print("proyecto %s: %s%s" % (f, d, "  (motor blender: solo la capa 2D; la placa assets/placa.mp4 la pone `render`)" if R["motor"] == "blender" else ""))
    return 0


def cmd_cuadro(a):
    m = cargar_json(a.maqueta)
    os.makedirs(a.salida, exist_ok=True)
    tiempos = sorted(set(round(float(t), 3) for t in a.t))
    if TR.es_tramos(m):
        return TR.cuadro(m, tiempos, formatos_de(a), a.salida, a.hoja, sys.modules[__name__])
    # motor blender: el cuadro de la placa es el más cercano a t (n = round(t·fps)); la capa 2D se dibuja en t
    fotos = sorted(set(int(round(t * int(m.get("fps", 30)))) for t in tiempos)) if motor_de(m) == "blender" else None
    for f in formatos_de(a):
        try:
            proy = os.path.join(a.salida, "_proyecto", carpeta_de(f))
            os.makedirs(proy, exist_ok=True)
            R = escribir_proyecto(m, f, proy, fotos)
        except Falla as e:
            print("  FALLA %s %s" % e.args); return 1
        malos = [t for t in tiempos if not 0 <= t <= R["dur"]]
        if malos:
            print("--t fuera del video (0–%.2f s): %s" % (R["dur"], malos)); return 2
        if fotos:
            rc, seg_b, n = placa_blender(a.maqueta, f, os.path.join(proy, "assets", "placa"), os.path.join(proy, "blender.log"), fotos)
            if rc or n != len(fotos):
                if not rc:
                    print("FALLA placa de Blender (%s): salieron %d de %d cuadros (ver %s)" % (f, n, len(fotos), os.path.join(proy, "blender.log")))
                return 1
            print("placa %s (Blender, estilo %s): %d cuadro(s) en %.1f s" % (f, R["estilo"], n, seg_b))
        snap = os.path.abspath(os.path.join(proy, "_cuadros"))
        shutil.rmtree(snap, ignore_errors=True)
        p, seg = correr(HF + ["snapshot", "--at", ",".join("%g" % t for t in tiempos), "--no-end", "--keep", "--browser-gpu", "--timeout", "120000", "-o", snap],
                        proy, os.path.join(proy, "cuadro.log"))
        pngs = sorted((x for x in os.listdir(snap) if x.endswith(".png")), key=lambda x: float(re.sub(r"[^0-9.]", "", x.rsplit("s.", 1)[0]) or 0)) if os.path.isdir(snap) else []
        if p.returncode != 0 or len(pngs) != len(tiempos):
            print("FALLA cuadro %s: hyperframes snapshot devolvió %d y %d de %d cuadros (ver %s)" % (f, p.returncode, len(pngs), len(tiempos), os.path.join(proy, "cuadro.log")))
            return 1
        salidas = []
        for t, png in zip(tiempos, pngs):
            dst = os.path.join(a.salida, "%s_t%07.3f.png" % (carpeta_de(f), t))
            shutil.move(os.path.join(snap, png), dst); salidas.append(dst)
        print("cuadros %s (%.1f s): %s" % (f, seg, " ".join(salidas)))
        if a.hoja:
            hoja = os.path.join(a.salida, "hoja_%s.jpg" % carpeta_de(f))
            hoja_de(salidas, hoja, 360 if len(salidas) > 3 else 540)
            print("hoja %s: %s  (en orden: %s s)" % (f, hoja, ", ".join("%g" % t for t in tiempos)))
    return 0


def fijar_vara(a, m, partes):
    """`escena MAQUETA --vara PIEZA`: el video de referencia que el usuario aprobó fija la vara de la escena viva →
    referencias/diseno/vara3d.json {pieza, fecha, regla, umbral, tramos[]}. Mide cada tramo de cerca en 9:16 y 4:5 con los
    umbrales de partida (sin la vara anterior) y aplica la regla de maqueta_escena.vara_de sobre el tramo más flojo."""
    M3, base, medidas, tramos = sys.modules[__name__], ESC.umbrales(base=True), [], []
    for info, sub in partes:
        fila = {"id": info["id"], "mundo": info["mundo"], "dur_s": round(info["hasta"] - info["desde"], 2)}
        for fmt in ("9:16", "4:5"):
            R = resolver(sub, fmt)
            if R["mundo"]["escala"] not in ESC.ESCALAS_CERCA:
                fila["escala"] = R["mundo"]["escala"]
                break
            r = ESC.medir(M3, sub, R, base)
            medidas.append(r)
            fila.setdefault("escala", R["mundo"]["escala"])
            if (m.get("mundos") or {}).get(info["mundo"], {}).get("hora"):
                fila["hora"] = m["mundos"][info["mundo"]]["hora"]
            fila[fmt] = {k: r[k] for k in ("ocupacion", "lleno", "variedad", "variado", "vida", "gente_max")}
        tramos.append(fila)
    if not medidas:
        print("  FALLA la referencia no tiene ningún tramo de cerca: no fija la vara"); return 1
    u = ESC.vara_de(medidas)
    vara = {"version": 1, "pieza": a.vara, "fecha": datetime.date.today().isoformat(),
            "regla": "sobre el tramo más flojo de la referencia: ocupación = 70 % de su mediana (y baja de punto en punto hasta que la referencia cumpla con 5 puntos de holgura); variedad = la suya − 1; parte del tramo que cumple = la suya − 5 puntos (70–90 %); nunca por debajo de los umbrales de partida",
            "umbral": {k: u[k] for k in ("ocupacion", "variedad", "muestras_ok")}, "partida": {k: base[k] for k in ("ocupacion", "variedad", "muestras_ok")},
            "tramos": tramos}
    ruta = a.vara_salida or ESC.ruta_vara()
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(vara, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("vara: %s · ocupación ≥ %d %% · variedad ≥ %d · en ≥ %d %% del tramo (de partida: %d %%, %d, %d %%) · %d tramos de cerca"
          % (os.path.relpath(ruta, RAIZ) if ruta.startswith(RAIZ) else ruta, round(100 * u["ocupacion"]), u["variedad"], round(100 * u["muestras_ok"]),
             round(100 * base["ocupacion"]), base["variedad"], round(100 * base["muestras_ok"]), sum(1 for t in tramos if t.get("9:16"))))
    return 0


def cmd_escena(a):
    """LA ESCENA VIVA: la medida de cada tramo de cerca (cuánto cuadro llenan sus cosas, cuántas distintas se ven, si algo se
    mueve: scripts/maqueta_escena.py) y, con --hoja, 6 cuadros de cada mundo para mirarlo (el director, el crítico, el usuario)."""
    m = cargar_json(a.maqueta)
    partes = TR.partir(m) if TR.es_tramos(m) else [({"id": "único", "mundo": "mundo", "desde": 0.0, "hasta": float(m.get("duracion_s", 0)), "off": 0.0}, m)]
    rc = 0
    for info, sub in partes:
        if a.mundo and info["mundo"] != a.mundo:
            continue
        try:
            R = resolver(sub, a.formato)
        except Falla as e:
            print("  FALLA %s %s" % e.args); return 1
        if R["mundo"]["escala"] not in ESC.ESCALAS_CERCA:
            print("%-16s (%s, %.1f–%.1f s): mapa (escala %s): no se mide como escena de cerca" % (info["id"], info["mundo"], info["desde"], info["hasta"], R["mundo"]["escala"]))
            continue
        txt, r = ESC.resumen(sys.modules[__name__], sub, R)
        fallas = sorted({"%s %s" % g for g in ESC.gates(sys.modules[__name__], dict(sub, video=True), R)})
        print("%-16s (%s, %.1f–%.1f s): %s%s" % (info["id"], info["mundo"], info["desde"], info["hasta"], txt, "" if not fallas else "  ← %d falla(s)" % len(fallas)))
        for x in fallas:
            print("    FALLA " + x)
        rc |= 1 if fallas else 0
    if getattr(a, "vara", None):
        if rc:
            print("  FALLA la referencia no pasa sus propios gates: no fija la vara"); return 1
        return fijar_vara(a, m, partes)
    if a.hoja:
        os.makedirs(a.salida, exist_ok=True)
        for info, sub in partes:
            if a.mundo and info["mundo"] != a.mundo:
                continue
            a0, a1 = info["desde"], info["hasta"]
            ts = [round(a0 + (a1 - a0) * u, 2) for u in (0.04, 0.22, 0.4, 0.58, 0.76, 0.94)]
            d = os.path.join(a.salida, "%s" % info["id"])
            shutil.rmtree(d, ignore_errors=True)
            if cmd_cuadro(argparse.Namespace(maqueta=a.maqueta, t=ts, salida=d, formato=a.formato, hoja=True, cmd="cuadro", pieza=False, lienzo=None)):
                return 1
    return rc


def hoja_de(pngs, destino, ancho=360):
    cols = min(len(pngs), 6)
    filas = math.ceil(len(pngs) / cols)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p in pngs:
        cmd += ["-i", p]
    fc = "".join("[%d]scale=%d:-2,setsar=1[v%d];" % (i, ancho, i) for i in range(len(pngs)))
    fc += "".join("[v%d]" % i for i in range(len(pngs))) + "concat=n=%d:v=1:a=0,tile=%dx%d:padding=6" % (len(pngs), cols, filas)
    subprocess.run(cmd + ["-filter_complex", fc, "-frames:v", "1", "-q:v", "3", destino], check=True)


def cmd_render(a):
    m = cargar_json(a.maqueta)
    formatos = formatos_de(a)
    if getattr(a, "borrador", False):
        # un gancho candidato (una sola escena, sin cierre): se renderiza para verlo en movimiento; nunca para entregar
        print("AVISO render --borrador: sin gates M3D; solo para mirar un candidato")
    elif not exigir_check(a, ["9:16", "4:5"]):
        return 1
    os.makedirs(a.dir, exist_ok=True)
    with open(os.path.join(a.dir, "efectos.json"), "w", encoding="utf-8") as f:
        json.dump(efectos_de(m), f, ensure_ascii=False)
    for f in formatos:
        base = os.path.join(a.dir, CARPETA[f])
        if renderizar(m, f, os.path.join(base, "proyecto"), os.path.join(base, "video.mp4"), os.path.join(base, "render.log")):
            return 1
    print("efectos: %s (%d)" % (os.path.join(a.dir, "efectos.json"), len(efectos_de(m))))
    return 0


def renderizar(m, f, proy, final, registro, placa=None):
    """Un formato (o un lienzo de pieza) → `final` (H.264 yuv420p, sin audio, duracion_s ± 1 cuadro). → 0 ok · 1 falla.
    Con `tramos` (varios mundos) lo hace maqueta_tramos.py; `placa` = el mp4 de los tramos ya encadenados (la capa encima)."""
    if TR.es_tramos(m):
        return TR.renderizar(m, f, proy, final, registro, sys.modules[__name__])
    if True:
        os.makedirs(proy, exist_ok=True)
        R = escribir_proyecto(m, f, proy, placa_externa=bool(placa))
        crudo = final + "._hf.mp4"
        for x in (crudo, final):
            if os.path.exists(x):
                os.remove(x)
        seg_placa, extra = 0.0, []
        if placa:
            shutil.copyfile(placa, os.path.join(proy, "assets", "placa.mp4"))
            extra = ["--video-frame-format", "png"]
        elif R["motor"] == "blender":
            # la placa: Blender renderiza el mundo cuadro a cuadro → assets/placa.mp4 (casi sin pérdida); HyperFrames pone la capa 2D
            rc, seg_placa = placa_video(m, f, proy, registro, R)
            if rc:
                return 1
            extra = ["--video-frame-format", "png"]
        # un solo proceso de Chrome SIEMPRE: con varios, el video tiembla
        p, seg = correr(HF + ["render", "--fps", str(R["fps"]), "--workers", "1", "--crf", "18", "--quality", "delivery", "--browser-gpu"] + extra + ["-o", os.path.abspath(crudo)],
                        proy, registro, limite=limite_render(R["dur"]))
        if p.returncode == 124:
            print("FALLA render %s: pasó su límite de %.0f s para %.1f s de video y se detuvo (ver %s; en una máquina lenta, MAQUETA_RENDER_LIMITE_S=<segundos>)" % (f, limite_render(R["dur"]), R["dur"], registro)); return 1
        if p.returncode != 0 or not os.path.exists(crudo):
            print("FALLA render %s: hyperframes devolvió %d (ver %s)" % (f, p.returncode, registro)); return 1
        info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=codec_name,pix_fmt,width,height,nb_read_frames",
                               "-of", "json", crudo], capture_output=True, text=True).stdout
        st = json.loads(info)["streams"][0]
        audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", crudo], capture_output=True, text=True).stdout.strip()
        if (st["codec_name"], st["pix_fmt"], st["width"], st["height"]) == ("h264", "yuv420p", R["W"], R["H"]) and not audio:
            os.replace(crudo, final)
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", crudo, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-r", str(R["fps"]), "-movflags", "+faststart", final], check=True)
            os.remove(crudo)
        cuadros, espera = int(st["nb_read_frames"]), round(R["dur"] * R["fps"])
        shutil.rmtree(os.path.join(proy, "renders"), ignore_errors=True)
        if abs(cuadros - espera) > 1:
            print("FALLA render %s: salieron %d cuadros y se esperaban %d (±1)" % (f, cuadros, espera)); return 1
        if R["motor"] == "blender":
            print("render %s: %s · %d×%d · %d cuadros (%.2f s a %d fps) · placa de Blender %.1f s (%.2f s por cuadro) + capa 2D %.1f s = %.1f s (%.1f s por segundo de video)"
                  % (f, final, R["W"], R["H"], cuadros, cuadros / R["fps"], R["fps"], seg_placa, seg_placa / max(1, cuadros), seg, seg + seg_placa, (seg + seg_placa) / R["dur"]))
        else:
            print("render %s: %s · %d×%d · %d cuadros (%.2f s a %d fps) · %.1f s de render (%.2f s por segundo de video)" % (f, final, R["W"], R["H"], cuadros, cuadros / R["fps"], R["fps"], seg, seg / R["dur"]))
    return 0


def placa_video(m, f, proy, registro, R):
    """MODO PLACA: Blender → PNG de todos los cuadros → proy/assets/placa.mp4 (H.264 crf 8, BT.709; los PNG se borran).
    → (0 ok | 1 falla, segundos)."""
    t0 = time.time()
    ruta = os.path.join(proy, "maqueta.json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False)
    tmp = os.path.join(proy, "_placa")
    reg_b = registro[:-len("render.log")] + "blender.log" if registro.endswith("render.log") else registro + ".blender.log"
    espera = int(round(R["dur"] * R["fps"]))
    rc, _, n = placa_blender(ruta, f, tmp, reg_b, None, espera)
    if rc or n != espera:
        if not rc:
            print("FALLA placa de Blender (%s): salieron %d cuadros y se esperaban %d (ver %s)" % (f, n, espera, reg_b))
        return 1, time.time() - t0
    placa = os.path.join(proy, "assets", "placa.mp4")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(R["fps"]), "-start_number", "0", "-i", os.path.join(tmp, "c_%05d.png"),
                        "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "8", "-g", "10",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", placa], capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0 or not os.path.exists(placa):
        print("FALLA placa (%s): ffmpeg no armó assets/placa.mp4: %s" % (f, " ".join(r.stderr.split())[-200:])); return 1, time.time() - t0
    return 0, time.time() - t0


def cmd_pieza(a):
    """MODO PIEZA: el mundo y sus pines en un lienzo libre, para alojarlo en el cuadro de otro flujo."""
    m = cargar_json(a.maqueta)
    f = formatos_de(a)[0]
    if not a.salida.lower().endswith(".mp4"):
        print("--salida debe terminar en .mp4"); return 2
    if a.borrador:
        print("AVISO pieza --borrador: sin gates M3D; solo para mirar")
    elif not exigir_check(a, [f]):
        return 1
    final = os.path.abspath(a.salida)
    base = final[:-4]
    os.makedirs(os.path.dirname(final), exist_ok=True)
    if renderizar(m, f, base + "_proyecto", final, base + ".render.log"):
        return 1
    efectos = sorted([round(float(o["t"]), 3), o["sfx"]] for o in (m.get("eventos") or []) + (m.get("marcas") or []) if o.get("sfx"))
    with open(base + ".efectos.json", "w", encoding="utf-8") as fh:
        json.dump(efectos, fh, ensure_ascii=False)
    print("efectos: %s (%d)" % (base + ".efectos.json", len(efectos)))
    return 0


# ---------- el catálogo del vocabulario (design/sets3d/vocabulario.json) ----------
CLAVES_FICHA = ("tipo", "clase", "cuando", "parametros", "escalas", "motores", "ejemplo")
CLAVES_PARAM = {"tipo", "requerido", "descripcion", "rango", "valores", "defecto", "min", "todos", "piezas", "capa", "valores_de"}   # valores_de: "objetos" (los del catálogo, con usa_objetos)
REGISTRO_JS = {"pieza": "PIEZAS", "evento": "EVENTOS", "objeto": "OBJETOS", "anotacion": "ANOTACIONES", "mundo": "MUNDOS"}


def revisar_ficha(fi, clase, tipo, ruta_js):
    """Una ficha y su módulo → fallas (lista de textos)."""
    f, que = [], "%s/%s" % (CLASES[clase], tipo)
    if not re.fullmatch(r"[a-z][a-z0-9_]*", tipo):
        f.append("%s: el nombre va en minúsculas, sin tildes ni guiones (es el `tipo`)" % que)
    if not isinstance(fi, dict):
        return f + ["%s.json: la ficha es un objeto" % que]
    faltan = [k for k in CLAVES_FICHA if k not in fi]
    if faltan:
        f.append("%s.json: faltan %s" % (que, ", ".join("`%s`" % k for k in faltan)))
    if fi.get("tipo") != tipo:
        f.append("%s.json: `tipo` es «%s» y el archivo se llama %s" % (que, fi.get("tipo"), tipo))
    if fi.get("clase") != clase:
        f.append("%s.json: `clase` es «%s» y está en %s/ (va «%s»)" % (que, fi.get("clase"), CLASES[clase], clase))
    if not (isinstance(fi.get("cuando"), str) and 10 <= len(fi["cuando"]) <= 160):
        f.append("%s.json: `cuando` es UNA línea (10–160 caracteres): para qué historia sirve" % que)
    if not (isinstance(fi.get("escalas"), list) and fi["escalas"] and set(fi["escalas"]) <= set(ESCALAS)):
        f.append("%s.json: `escalas` es una lista no vacía de %s" % (que, ", ".join(ESCALAS)))
    if not (isinstance(fi.get("motores"), list) and fi["motores"] and set(fi["motores"]) <= set(MOTORES)):
        f.append("%s.json: `motores` es una lista no vacía de %s" % (que, ", ".join(MOTORES)))
    P = fi.get("parametros")
    if not isinstance(P, dict):
        f.append("%s.json: `parametros` es un objeto {nombre: {tipo, requerido, descripcion, …}} (vacío si no lleva)" % que); P = {}
    for nombre, d in P.items():
        q = "%s.json → parametros.%s" % (que, nombre)
        if nombre in COMUNES.get(clase, ()):
            f.append("%s: `%s` es común a toda %s y no va en la ficha" % (q, nombre, clase))
        if not isinstance(d, dict):
            f.append("%s: es un objeto" % q); continue
        if d.get("tipo") not in TIPOS_PARAM:
            f.append("%s: `tipo` es uno de %s" % (q, ", ".join(TIPOS_PARAM)))
        if not isinstance(d.get("requerido"), bool) or not (isinstance(d.get("descripcion"), str) and d["descripcion"].strip()):
            f.append("%s: lleva `requerido` (true/false) y `descripcion`" % q)
        if set(d) - CLAVES_PARAM:
            f.append("%s: claves desconocidas %s (van: %s)" % (q, ", ".join(sorted(set(d) - CLAVES_PARAM)), ", ".join(sorted(CLAVES_PARAM))))
        rg = d.get("rango")
        if rg is not None and not (isinstance(rg, list) and len(rg) == 2 and all(isinstance(x, (int, float)) for x in rg) and rg[0] <= rg[1]):
            f.append("%s: `rango` es [mínimo, máximo]" % q)
        if d.get("valores") is not None and not (isinstance(d["valores"], list) and d["valores"]):
            f.append("%s: `valores` es una lista no vacía" % q)
    ad = fi.get("adelanto")
    if ad is not None and (clase != "evento" or not isinstance(ad, dict) or not ad or set(ad) - {"s", "dur"}):
        f.append("%s.json: `adelanto` (solo eventos) es {\"s\": segundos} o {\"dur\": fracción de la duración}: cuánto lleva un evento que empieza en la portada" % que)
    # la escena viva (scripts/maqueta_escena.py): lo que cada tipo declara para medir si un tramo está lleno y vivo
    if clase in ("pieza", "objeto"):
        if fi.get("nivel") not in ("objeto", "escenario", "fondo"):
            f.append("%s.json: `nivel` es «objeto» (una cosa suelta), «escenario» (un lugar completo) o «fondo» (el tejido del mundo)" % que)
        if not (isinstance(fi.get("contiene"), list) and all(isinstance(c, str) and c for c in fi["contiene"])):
            f.append("%s.json: `contiene` es la lista de lo que muestra, en palabras (vacía si es una sola cosa)" % que)
        if not (fi.get("animado") is False or (isinstance(fi.get("animado"), str) and fi["animado"].strip())):
            f.append("%s.json: `animado` dice qué se mueve solo (un texto), o false" % que)
        if not isinstance(fi.get("gente"), bool):
            f.append("%s.json: `gente` es true si es o incluye personas que hacen algo" % que)
        for k, n in (("distancia_m", 2), ("caja_m", 3)):
            v = fi.get(k)
            if v is not None and not (isinstance(v, list) and len(v) == n and all(isinstance(x, (int, float)) and x >= 0 for x in v)):
                f.append("%s.json: `%s` es una lista de %d números (%s)" % (que, k, n, "[mín, máx] a la que se lee" if n == 2 else "[largo, ancho, alto] en metros"))
        if fi.get("nivel") == "escenario" and not fi.get("contiene"):
            f.append("%s.json: un `escenario` dice lo que `contiene` (≥ 3 cosas): un lugar completo no es una sola cosa" % que)
    if fi.get("capas") is not None and not (isinstance(fi["capas"], list) and all(isinstance(c, str) and c for c in fi["capas"])):
        f.append("%s.json: `capas` (opcional) es la lista de capas del set que el tipo usa siempre (el pie nombra su fuente, M3D7)" % que)
    if clase == "mundo":
        f += revisar_ficha_mundo(fi, que, tipo)
    ej = fi.get("ejemplo")
    llave = "escala" if clase == "mundo" else "tipo"
    if not isinstance(ej, dict) or (clase in ("pieza", "evento", "anotacion", "mundo") and ej.get(llave) != tipo):
        f.append("%s.json: `ejemplo` es un objeto con `%s` «%s», tal como va en el maqueta.json" % (que, llave, tipo))
    elif not f:
        try:
            validar_campos(ej, fi, "%s.json → ejemplo" % que)
        except Falla as e:
            f.append(e.args[1])
    try:
        js = cargar_texto(ruta_js)
    except OSError:
        return f + ["%s.js: no se puede leer" % que]
    if not re.search(r"MAQ\.%s\.%s\s*=|MAQ\.%s\[\s*[\"']%s[\"']\s*\]\s*=" % (REGISTRO_JS[clase], tipo, REGISTRO_JS[clase], tipo), js):
        f.append("%s.js: el módulo no se registra (falta `MAQ.%s.%s = {…}`)" % (que, REGISTRO_JS[clase], tipo))
    if re.search(r"#[0-9a-fA-F]{3,8}\b", re.sub(r"//[^\n]*", "", js)):
        f.append("%s.js: un color escrito a mano: los colores llegan del estilo (ctx.COL, ctx.lin)" % que)
    if re.search(r"https?://|\bfetch\(|XMLHttpRequest|\bimport\s*\(", js):
        f.append("%s.js: el módulo no usa la red ni carga nada: todo llega en ctx" % que)
    if re.search(r"Math\.random|Date\.now|performance\.now|new Date\b", js):
        f.append("%s.js: nada de azar ni reloj: cada cuadro es función pura de t (usa ctx.hash)" % que)
    return f


def revisar_ficha_mundo(fi, que, tipo):
    """Lo propio de la ficha de un MUNDO: su escala, su unidad y su cámara (el rango de la distancia es por escala)."""
    f = []
    if fi.get("escalas") != [tipo]:
        f.append("%s.json: un mundo sirve en su propia escala: `escalas` es [\"%s\"]" % (que, tipo))
    if tipo not in ESCALAS:
        f.append("%s: un mundo se llama como su escala (%s)" % (que, ", ".join(ESCALAS)))
    if not (isinstance(fi.get("unidad_m"), (int, float)) and fi["unidad_m"] > 0):
        f.append("%s.json: `unidad_m` es cuántos metros mide una unidad de la escena (pais: 1000; ciudad y esquema: 1)" % que)
    c = fi.get("camara")
    if not (isinstance(c, dict) and c.get("campo") in ("dist_km", "dist_m") and isinstance(c.get("unidad"), str)
            and isinstance(c.get("rango"), list) and len(c["rango"]) == 2 and 0 < c["rango"][0] < c["rango"][1]
            and all(isinstance(c.get(k), (int, float)) and c[k] > 0 for k in ("despeje", "cerca", "lejos"))
            and isinstance(c.get("niebla"), list) and len(c["niebla"]) == 4):
        f.append("%s.json: `camara` es {campo: dist_km|dist_m, unidad, rango: [mín, máx], despeje, cerca, lejos, niebla: [mín inicio, × dist, mín fin, × dist]}" % que)
    pl = fi.get("plano")
    if not (isinstance(pl, dict) and isinstance(pl.get("y"), (int, float)) and isinstance(pl.get("lado"), (int, float)) and pl["lado"] > 0):
        f.append("%s.json: `plano` es {y, lado}: el plano exterior que sigue más allá de la caja del mundo" % que)
    return f


def expandir_objetos(entradas):
    """`usa_objetos`: la pieza acepta CUALQUIER objeto del catálogo (actor, flujo): su `usa` y los parámetros con
    `valores_de: "objetos"` salen de los objetos registrados (también al inyectar uno nuevo en memoria: maqueta_modulo.py)."""
    objetos = sorted(e["tipo"] for e in entradas if e["clase"] == "objeto")
    for e in entradas:
        if e.get("usa_objetos"):
            e["usa"] = list(objetos)
            for d in (e.get("parametros") or {}).values():
                if isinstance(d, dict) and d.get("valores_de") == "objetos":
                    d["valores"] = list(objetos)


def generar_catalogo(a_medias=None):
    """Las fichas de video/maqueta/<clase>/ → (catálogo, fallas). Cada módulo con su ficha y cada ficha con su módulo.
    a_medias (una lista): lo que está A MEDIO HACER (un módulo sin ficha, una ficha sin módulo, unas reglas sin ninguno de
    los dos: lo que deja otra sesión que construye en paralelo) va ahí y no a las fallas; nunca está en el catálogo, así
    que dejarlo fuera no quita nada (m305). Una ficha con errores sigue fallando."""
    entradas, f, vistos = [], [], {}
    pend = a_medias if isinstance(a_medias, list) else f
    for clase, carpeta in CLASES.items():
        d = os.path.join(MOTOR, carpeta)
        if not os.path.isdir(d):
            continue
        nombres = sorted(os.listdir(d))
        js, fj = {n[:-3] for n in nombres if n.endswith(".js")}, {n[:-5] for n in nombres if n.endswith(".json")}
        pend += ["%s/%s.js no tiene ficha (%s.json)" % (carpeta, t, t) for t in sorted(js - fj)]
        pend += ["%s/%s.json no tiene módulo (%s.js)" % (carpeta, t, t) for t in sorted(fj - js)]
        for t in sorted(js & fj):
            try:
                fi = cargar_json(os.path.join(d, t + ".json"))
            except (OSError, ValueError) as e:
                f.append("%s/%s.json: no se puede leer (%s)" % (carpeta, t, e)); continue
            ff = revisar_ficha(fi, clase, t, os.path.join(d, t + ".js"))
            if t in vistos:
                ff.append("%s/%s: el tipo «%s» ya está en %s/ (un tipo por catálogo)" % (carpeta, t, t, vistos[t]))
            vistos[t] = carpeta
            f += ff
            if not ff:
                e = dict(fi)
                e["modulo"] = "%s/%s.js" % (carpeta, t)
                e["reglas"] = "scripts/maqueta_tipos/%s.py" % t if os.path.isfile(os.path.join(REGLAS_DIR, t + ".py")) else None
                entradas.append(e)
    # `usa_objetos`: la pieza acepta CUALQUIER objeto del catálogo (actor, flujo): su lista de objetos y su `usa` salen de lo
    # registrado, así un objeto nuevo del constructor sirve sin tocar la ficha a mano
    expandir_objetos(entradas)
    for e in entradas:
        f += ["%s: `usa` «%s», que no está en el catálogo" % (e["modulo"], u) for u in e.get("usa") or [] if u not in vistos]
    sueltas = sorted(n[:-3] for n in os.listdir(REGLAS_DIR) if n.endswith(".py") and not n.startswith("_") and n[:-3] not in vistos) if os.path.isdir(REGLAS_DIR) else []
    pend += ["scripts/maqueta_tipos/%s.py no tiene módulo ni ficha en video/maqueta/" % t for t in sueltas]
    orden = list(CLASES)
    entradas.sort(key=lambda e: (orden.index(e["clase"]), e["tipo"]))
    return {"version": 1, "nota": "Lo escribe SOLO `python3 scripts/maqueta3d.py catalogo --registrar` desde las fichas video/maqueta/<clase>/<tipo>.json "
                                  "(no se edita a mano). Cómo añadir una entrada: referencias/diseno/maqueta3d.md («Añadir vocabulario»).",
            "entradas": entradas}, f


def texto_catalogo(cat):
    return json.dumps(cat, ensure_ascii=False, indent=1) + "\n"


def modulos_de(R):
    """Los módulos de motor.js que usa una maqueta resuelta (su mundo, sus piezas y eventos, y lo que ellos `usa`n) → rutas relativas
    a video/maqueta/, en orden estable."""
    V, usados = vocabulario(), set()
    pend = [R["mundo"]["escala"]] + [p["tipo"] for p in R["piezas"]] + [e["tipo"] for e in R["eventos"]] + [o["tipo"] for o in R.get("anotaciones") or []]
    pend += [u for p in R["piezas"] for u in p.get("usa") or []]   # lo que una pieza resuelta dice que usa (los objetos de un flujo)
    while pend:
        t = pend.pop()
        if t in usados or t not in V:
            continue
        usados.add(t); pend += V[t].get("usa") or []
    orden = list(CLASES)
    return [V[t]["modulo"] for t in sorted(usados, key=lambda t: (orden.index(V[t]["clase"]), t))]


def fmt_param(nombre, d):
    s = nombre + ("*" if d.get("requerido") else "")
    if d.get("valores"):
        s += " (%s)" % "|".join(map(str, d["valores"]))
    elif d.get("rango"):
        s += " %g–%g" % tuple(d["rango"])
    if "defecto" in d and d["defecto"] not in (None, ""):
        s += "=%s" % (json.dumps(d["defecto"], ensure_ascii=False) if not isinstance(d["defecto"], str) else d["defecto"])
    if d["tipo"] == "pieza" and d.get("piezas"):
        s += " →%s" % "|".join(d["piezas"])
    return s


def lineas_catalogo(para="sesion", escala=None, motor=None):
    """El catálogo legible (≤ 1 página por escala): una línea por entrada con sus parámetros clave y un ejemplo mínimo.
    para: sesion (todo) · realizador (la maqueta dentro de la mesa: `dice` en vez de `t`) · critico (qué hay y para qué)."""
    V = vocabulario()
    if not V:
        return ["(el catálogo está vacío: python3 scripts/maqueta3d.py catalogo --registrar)"]
    sel = [f for f in V.values() if (not escala or escala in f["escalas"]) and (not motor or motor in f["motores"])]
    L = ["## Vocabulario de la maqueta 3D (design/sets3d/vocabulario.json%s%s; `*` = requerido)" % (
        " · escala %s" % escala if escala else "", " · motor %s" % motor if motor else "")]
    titulos = {"pieza": "Piezas (mundo.piezas: {id, tipo, …})",
               "evento": "Eventos (eventos: {%s, dur, tipo, …})" % ("dice" if para == "realizador" else "t"),
               "objeto": "Objetos (`objeto` de actor y `tipos` de flujo)",
               "anotacion": "Anotaciones (anotaciones: {%s, hasta, tipo, …}: la capa 2D atada al 3D)" % ("dice" if para == "realizador" else "t"),
               "mundo": "Mundos"}
    for clase in CLASES:
        fs = sorted((f for f in sel if f["clase"] == clase), key=lambda f: f["tipo"])
        if not fs:
            continue
        L.append("### " + titulos[clase])
        for f in fs:
            extra = "" if motor else " · " + "/".join(f["motores"])
            ln = "- `%s` [%s%s] %s" % (f["tipo"], "/".join(f["escalas"]), extra, f["cuando"])
            if para != "critico":
                ps = [fmt_param(n, d) for n, d in f["parametros"].items()]
                ej = dict(f["ejemplo"])
                if para == "realizador" and clase in ("evento", "anotacion"):
                    ej.pop("t", None); ej = dict({"dice": "…"}, **ej)
                ln += ". %s Ej.: %s" % ("Parámetros: " + ", ".join(ps) + "." if ps else "Sin parámetros.", json.dumps(ej, ensure_ascii=False))
            L.append(ln)
    if escala:
        fm = V.get(escala) or {}
        cam = fm.get("camara") or {}
        sets = lista_sets(escala) if escala != "esquema" else []
        L.append("Mundo: {\"escala\": \"%s\"%s, …} · cámara en `%s` (%s–%s %s)%s" % (
            escala, ", \"set\": \"%s\"" % sets[0] if sets else ", \"receta\": …", cam.get("campo", "?"), *(cam.get("rango") or ["?", "?"]), cam.get("unidad", ""),
            " · sets: %s" % ", ".join(sets) if sets else (" · sin set: lleva capa.aviso con «Esquema» y nombres genéricos (M3D12)" if escala == "esquema" else "")))
    if not sel:
        L.append("(nada todavía con ese filtro)")
    L.append("Lo que no está aquí no se dibuja: no se inventa un tipo. Si la historia lo necesita, pídelo al constructor con un brief "
             "(qué tiene que verse y cuándo).")
    return L


def cmd_catalogo(a):
    if a.registrar or a.check:
        medias = [] if getattr(a, "ignorar_a_medias", False) else None
        cat, fallas = generar_catalogo(medias)
        for x in medias or []:
            print("  AVISO catálogo (a medio hacer, fuera del catálogo) %s" % x)
        for x in fallas:
            print("  FALLA catálogo %s" % x)
        if fallas:
            print("catálogo: %d falla(s); %s" % (len(fallas), "no se escribió" if a.registrar else "revisa las fichas"))
            return 1
        nuevo = texto_catalogo(cat)
        viejo = cargar_texto(VOCABULARIO) if os.path.isfile(VOCABULARIO) else ""
        if a.check:
            if nuevo != viejo:
                print("FALLA catálogo: design/sets3d/vocabulario.json no está al día con las fichas: python3 scripts/maqueta3d.py catalogo --registrar")
                return 1
            print("catálogo al día: %d entradas" % len(cat["entradas"]))
            return 0
        with open(VOCABULARIO, "w", encoding="utf-8") as fh:
            fh.write(nuevo)
        _VOCAB.clear()
        cuenta = {c: sum(1 for e in cat["entradas"] if e["clase"] == c) for c in CLASES}
        print("catálogo %s: %s (%s)" % ("sin cambios" if nuevo == viejo else "escrito", os.path.relpath(VOCABULARIO, RAIZ),
                                        ", ".join("%d %s" % (n, CLASES[c]) for c, n in cuenta.items() if n)))
        return 0
    print("\n".join(lineas_catalogo(a.para, a.escala, a.motor)))
    return 0


def cmd_estilos(a):
    for e in catalogo_estilos().values():
        print("%-11s motor %-8s %s%s" % (e["id"], e["motor"], e["cuando"], "" if e["motor"] == "three" or blender_bin() else "  [falta Blender ≥ 5.0: $BLENDER o /Applications]"))
    return 0


def cmd_sets(a):
    for s in lista_sets():
        esc = escala_set(s)
        if esc == "pais":
            S = Set(s)
            print("%s [escala pais, km]: relieve %d×%d · %d lugares · %d trazos de falla (%d con nombre)\n  pie: %s" % (
                s, S.relieve["ancho"], S.relieve["alto"], len(S.lugares), len(S.fallas["trazos"]), len(S.fallas["nombres"]), S.fuente.get("pie", "")))
        else:
            S = reglas(esc).mundo({"set": s}, ficha(esc, "mundo"), sys.modules[__name__])
            c = lambda n: S.capa(n)
            print("%s [escala %s, m]: caja %.1f × %.1f km · relieve %d×%d (%d a %d m) · %d calles (%d arterias: %s) · %d edificios · %d zonas · %d lugares\n  pie: %s" % (
                s, esc, (S.x1 - S.x0) / 1000, (S.y1 - S.y0) / 1000, S.relieve["ancho"], S.relieve["alto"], S.relieve["min_m"], S.relieve["max_m"],
                len(c("calles")["calles"]), len(c("calles")["arterias"]), ", ".join(c("calles")["arterias"]), len(c("edificios")["edificios"]),
                len(c("zonas")["zonas"]), len(S.lugares), S.fuente.get("pie", "")))
    rg = reglas("esquema")
    if rg:
        print("esquema [escala esquema, m, sin set]: recetas %s (mundo.receta; maqueta3d.py catalogo --escala esquema)" % ", ".join(rg.RECETAS))
    return 0


# Negativos: cada cambio al fixture debe hacer saltar SU gate (prueba de que los gates muerden).
NEGATIVOS = [
    ("M3D1", "estilo que no está en el catálogo", lambda m: m.update(estilo="acuarela")),
    ("M3D1", "paleta que no existe", lambda m: m.update(paleta="fucsia")),
    ("M3D2", "trazo que no está en el set", lambda m: m["mundo"]["piezas"][0].update(trazos=["Falla de Mentira"])),
    ("M3D2", "lugar que no existe", lambda m: m["marcas"][0].update(lugar="atlantida")),
    ("M3D2", "protagonista que no es una pieza", lambda m: m.update(protagonista="nadie")),
    ("M3D3", "cámara que no empieza en 0", lambda m: m["camara"][0].update(t=0.5)),
    ("M3D3", "giro que marea", lambda m: m["camara"][1].update(t=0.6)),
    ("M3D3", "cámara dentro del relieve", lambda m: m["camara"][1].update(dist_km=30, elevacion=9)),
    ("M3D4", "marca que la cámara no encuadra", lambda m: m["marcas"][1].update(lugar="flores")),
    ("M3D4", "marca que no da tiempo de leer", lambda m: m["marcas"][0].update(hasta=2.6)),
    ("M3D5", "dos titulares a la vez", lambda m: m["capa"]["titulares"][1].update(t=3.0)),
    ("M3D5", "«Sígueme» sobre un titular", lambda m: m["capa"]["seguir"].update(t=6.5)),
    ("M3D6", "evento fuera de cámara", lambda m: m["eventos"].append({"t": 4.5, "dur": 1.5, "tipo": "onda", "centro": "quetzaltenango", "radio_km": 40})),
    ("M3D6", "evento que no cabe", lambda m: m["eventos"][2].update(dur=9)),
    ("M3D7", "sin pie (las fuentes de los geodatos)", lambda m: m["capa"].pop("pie")),
    ("M3D11", "pin que se declara separado de la falla y está sobre ella", lambda m: m["marcas"][0].update(separada_de="motagua")),
    ("M3D2", "separada_de una pieza que no es línea", lambda m: m["marcas"][0].update(separada_de="pueblos")),
    ("M3D7", "pie sin la fuente de las fallas", lambda m: m["capa"].update(pie="Relieve: Mapzen")),
    ("M3D8", "un estilo por pieza", lambda m: m["mundo"]["piezas"][1].update(estilo="voxel")),
    ("M3D7", "sin «Sígueme» a mitad", lambda m: m["capa"].pop("seguir")),
    ("M3D9", "el evento del gancho no empieza en el cuadro 0", lambda m: m["eventos"][0].update(t=0.5)),
    ("M3D9", "el evento del gancho fuera de cuadro en t = 0", lambda m: m["camara"][0].update(mira="quetzaltenango", dist_km=200)),
]


def negativos():
    base, mal = cargar_json(FIXTURE), 0
    for gate, nombre, cambio in NEGATIVOS:
        m = json.loads(json.dumps(base)); cambio(m)
        fallas, _ = revisar_m(m, ["9:16", "4:5"])
        if not any(f.startswith(gate + " ") for f in fallas):
            mal += 1; print("  FALLA negativo «%s»: debía saltar %s y saltó: %s" % (nombre, gate, "; ".join(fallas)[:200] or "nada"))
    print("negativos de gate: %d de %d muerden" % (len(NEGATIVOS) - mal, len(NEGATIVOS)))
    # positivos: con aviso también pasa, una marca bien separada pasa M3D11, y el fixture sin capa pasa en modo pieza
    def pasa(nombre, cambio, formatos):
        m = json.loads(json.dumps(base)); cambio(m)
        fallas, _ = revisar_m(m, formatos)
        if fallas:
            print("  FALLA positivo «%s»: debía pasar y saltó: %s" % (nombre, "; ".join(fallas)[:300]))
        return 1 if fallas else 0
    mal += pasa("con aviso", lambda m: m["capa"].update(aviso="Maqueta · no a escala"), ["9:16", "4:5"])
    for est in ("arquitecto", "diorama", "papel"):   # los gates son sobre los datos: valen igual con el motor blender
        mal += pasa("estilo %s (motor blender)" % est, lambda m: m.update(estilo=est), ["9:16", "4:5"])
    mal += pasa("marca separada de la frontera", lambda m: m["marcas"][1].update(separada_de="frontera"), ["9:16", "4:5"])
    for lienzo in ("950x1040", "1120x1080", "1920x1080"):
        mal += pasa("modo pieza %s sin capa" % lienzo, lambda m: m.pop("capa"), [lienzo])
    m = json.loads(json.dumps(base)); m.pop("capa"); m["marcas"][0].update(separada_de="motagua")
    if not any(f.startswith("M3D11 ") for f in revisar_m(m, ["950x1040"])[0]):
        mal += 1; print("  FALLA negativo «pieza: pin pegado a la falla»: debía saltar M3D11")
    print("positivos y modo pieza: %s" % ("OK" if not mal else "con fallas"))
    return mal


def fixture_en(estilo, carpeta):
    """El fixture con otro estilo, en un archivo de trabajo."""
    m = cargar_json(FIXTURE); m["estilo"] = estilo
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "maqueta_%s.json" % estilo)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False)
    return ruta


def prueba_blender(a):
    """El caso corto del motor Blender: el fixture en `arquitecto` → check y UN cuadro (placa + capa 2D). El render
    completo es lento y no entra aquí: `prueba --blender-render ESTILO`."""
    if not blender_bin():
        print("AVISO prueba: no encuentro Blender ($BLENDER o /Applications/Blender.app): se salta el caso del motor blender")
        return 0
    d = os.path.join(a.dir, "blender")
    ruta = fixture_en("arquitecto", d)
    if cmd_check(argparse.Namespace(maqueta=ruta, formato="ambos", cmd="check")):
        return 1
    r = cmd_cuadro(argparse.Namespace(maqueta=ruta, t=[2.6], salida=os.path.join(d, "cuadros"), formato="9:16", hoja=False, cmd="cuadro"))
    print("motor blender: %s  (el render completo no entra en `prueba`: python3 scripts/maqueta3d.py prueba --blender-render arquitecto|diorama|papel [--formato 9:16])" % ("OK" if not r else "con fallas"))
    return r


def cmd_prueba(a):
    if getattr(a, "blender_render", None):   # el fixture completo en un estilo de Blender (minutos)
        d = os.path.join(a.dir, "blender", a.blender_render)
        return cmd_render(argparse.Namespace(maqueta=fixture_en(a.blender_render, os.path.join(a.dir, "blender")), dir=d, formato=a.formato, borrador=False, cmd="render"))
    a.maqueta = FIXTURE
    if cmd_check(argparse.Namespace(maqueta=FIXTURE, formato="ambos", cmd="check")) or negativos():
        return 1
    for caso in FIXTURES_MUNDOS:   # los mundos ciudad y esquema (sus negativos: scripts/pruebas/maqueta_mundos.py)
        if cmd_check(argparse.Namespace(maqueta=caso, formato="ambos", cmd="check")):
            return 1
    dur = cargar_json(FIXTURE)["duracion_s"]
    r = cmd_cuadro(argparse.Namespace(maqueta=FIXTURE, t=[0.0, dur * 0.2, dur * 0.4, dur * 0.6, dur * 0.78, dur - 0.5], salida=os.path.join(a.dir, "cuadros"), formato=a.formato, hoja=True, cmd="cuadro"))
    return r or cmd_render(a) or prueba_tramos(a) or prueba_blender(a)


def prueba_tramos(a):
    """Varios mundos en un video: el render de tramos.json (campo → país → costa, fundido y corte) dura lo que dice."""
    d = os.path.join(a.dir, "tramos")
    if cmd_render(argparse.Namespace(maqueta=FIXTURE_TRAMOS, dir=d, formato=a.formato, borrador=False, cmd="render")):
        return 1
    print("tramos: OK (%s)" % d)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Maqueta 3D de /video-3d: gates M3D, cuadros sueltos y render. El estilo decide el motor: three.js en HyperFrames, o Blender (la placa) + la capa 2D de HyperFrames.",
                                 epilog="Contrato: referencias/diseno/maqueta3d.md · Sets: scripts/build_set3d.py")
    sub = ap.add_subparsers(dest="cmd")
    fmt = dict(choices=["9:16", "4:5", "ambos"], help="formato (por defecto: %(default)s)")
    lz = dict(metavar="ANCHOxALTO", help="lienzo del modo pieza (p. ej. 950x1040, 1120x1080, 1920x1080)")
    pz = dict(action="store_true", help="modo pieza: solo el mundo y sus pines, en el lienzo de --lienzo")
    p = sub.add_parser("check", help="gates M3D1–M3D12 sobre los datos"); p.add_argument("maqueta"); p.add_argument("--formato", default="ambos", **fmt)
    p.add_argument("--pieza", **pz); p.add_argument("--lienzo", **lz)
    p = sub.add_parser("cuadro", help="PNG de cuadros sueltos (y hoja de contacto)"); p.add_argument("maqueta")
    p.add_argument("--t", action="append", type=float, required=True, help="segundo del cuadro (se repite)"); p.add_argument("--salida", required=True)
    p.add_argument("--formato", default="9:16", **fmt); p.add_argument("--hoja", action="store_true", help="arma hoja_<formato>.jpg con todos los cuadros")
    p.add_argument("--pieza", **pz); p.add_argument("--lienzo", **lz)
    p = sub.add_parser("pieza", help="modo pieza: ARCHIVO.mp4 del tamaño del lienzo + ARCHIVO.efectos.json"); p.add_argument("maqueta")
    p.add_argument("--lienzo", required=True, **lz); p.add_argument("--salida", required=True, metavar="ARCHIVO.mp4")
    p.add_argument("--borrador", action="store_true", help="sin gates: para mirar, nunca para entregar")
    p = sub.add_parser("escena", help="la escena viva: mide cada tramo de cerca (M3D15–M3D19) y, con --hoja, 6 cuadros por mundo"); p.add_argument("maqueta")
    p.add_argument("--mundo", help="solo ese mundo"); p.add_argument("--formato", default="9:16", **fmt)
    p.add_argument("--hoja", action="store_true", help="dibuja 6 cuadros de cada mundo en --salida/<tramo>/"); p.add_argument("--salida", default=os.path.join(RAIZ, "sesiones", "_video3d", "escenas"))
    p.add_argument("--vara", metavar="PIEZA", help="el video de referencia aprobado por el usuario fija la vara (referencias/diseno/vara3d.json); PIEZA = su carpeta de entrega")
    p.add_argument("--vara-salida", help="otra ruta para la vara (pruebas)")
    p = sub.add_parser("proyecto", help="escribe el proyecto de HyperFrames"); p.add_argument("maqueta"); p.add_argument("--dir", required=True); p.add_argument("--formato", default="ambos", **fmt)
    p = sub.add_parser("render", help="DIR/<9x16|4x5>/video.mp4 + DIR/efectos.json"); p.add_argument("maqueta"); p.add_argument("--dir", required=True); p.add_argument("--formato", default="ambos", **fmt)
    p.add_argument("--borrador", action="store_true", help="sin gates: un candidato para mirar, nunca para entregar")
    p = sub.add_parser("catalogo", help="el vocabulario (piezas, eventos, objetos, mundos): legible, --registrar o --check")
    p.add_argument("--para", choices=["sesion", "realizador", "critico"], default="sesion", help="para quién (por defecto: %(default)s)")
    p.add_argument("--escala", choices=list(ESCALAS), help="solo lo de esa escala"); p.add_argument("--motor", choices=list(MOTORES), help="solo lo que dibuja ese motor")
    p.add_argument("--registrar", action="store_true", help="revisa las fichas y escribe design/sets3d/vocabulario.json (el único escritor)")
    p.add_argument("--check", action="store_true", help="falla si vocabulario.json no está al día con las fichas")
    p.add_argument("--ignorar-a-medias", dest="ignorar_a_medias", action="store_true",
                   help="con --registrar: un módulo sin ficha, una ficha sin módulo o unas reglas sueltas (otra sesión construyendo) avisan y quedan fuera, en vez de fallar")
    sub.add_parser("estilos", help="el catálogo de estilos")
    sub.add_parser("sets", help="los sets de geodatos")
    p = sub.add_parser("prueba", help="check + hoja + render del fixture (y un cuadro del motor blender, si Blender está instalado)")
    p.add_argument("--dir", default=os.path.join(RAIZ, "sesiones", "_video3d", "prueba")); p.add_argument("--formato", default="ambos", **fmt)
    p.add_argument("--blender-render", metavar="ESTILO", choices=["arquitecto", "diorama", "papel"], help="solo el render completo del fixture en ese estilo de Blender (lento: minutos)")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help(); return 2
    if getattr(a, "maqueta", None) and not os.path.isfile(a.maqueta):
        print("no existe %s" % a.maqueta, file=sys.stderr); return 2
    try:
        return {"check": cmd_check, "cuadro": cmd_cuadro, "escena": cmd_escena, "proyecto": cmd_proyecto, "render": cmd_render, "pieza": cmd_pieza, "estilos": cmd_estilos, "sets": cmd_sets,
                "prueba": cmd_prueba, "catalogo": cmd_catalogo}[a.cmd](a)
    except Falla as e:
        print("  FALLA %s %s" % e.args); return 1


if __name__ == "__main__":
    sys.exit(main())
