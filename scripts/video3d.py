#!/usr/bin/env python3
"""/video-3d: un video vertical 100 % en 3D, la «maqueta que vuela» (9:16 + 4:5).

Un mundo 3D simple (relieve, lugares, piezas) recorrido por una cámara mientras la voz cuenta, con una capa 2D encima
(titular, pines que siguen al 3D, cifras, subtítulos). Decisiones del usuario (2026-11-14): three.js dentro de
HyperFrames o Blender + HyperFrames según el estilo; UN solo estilo por video, que elige el orquestador entre los ocho
(si no está seguro, pregunta); dentro de la maqueta la cámara se mueve; el gancho manda y todo concuerda: lo que se ve
es lo que la voz está diciendo.

Este script conoce el guion y la voz; el motor solo conoce `maqueta.json` (referencias/diseno/maqueta3d.md), que aquí se
escribe con cada `dice` del guion ya convertido en su segundo. La voz y Scribe salen del MCP de ElevenLabs con los
mismos comandos de scripts/video.py (locucion.json tiene su misma forma). Guía: referencias/flujo-video3d.md.

Subcomandos (TRABAJO = sesiones/video3d-<slug>):
  preparar SLUG --tema "…" [--desde CARPETA] [--paleta P] [--musica-tema T] [--duracion S]
        crea TRABAJO; --desde copia las cifras verificadas (base/datos.json) de un trabajo o una entrega anterior
  datos TRABAJO --sumar ARCHIVO      añade a base/datos.json las cifras verificadas de un verificacion_*.json
  digesto TRABAJO                    lo que necesita quien escribe: cifras, lugares, piezas, eventos, estilos, reglas
  ganchos TRABAJO --check [--cuadros] [--clips] | --usar ID
        ganchos.json (5 candidatos a escena 1): reglas del gancho; cuadros y clip mudo de cada candidato; copia el elegido;
        avisa si la familia repite la de los últimos 2 videos 3D (rotación)
  guion TRABAJO --check              gates C3D1–C3D11 (concordancia) + V2–V5 (un caption por plataforma) → locucion.json
                                     y maqueta.json (estimado)
  storyboard TRABAJO                 un cuadro por clave de cámara y por evento → storyboard/hoja.jpg (antes de la voz)
  voz | voz-falsa | descargar | partir | escuchar TRABAJO […]    → scripts/video.py (los mismos comandos de /video;
                                     escuchar = V11, la escucha independiente con whisper)
  tiempos TRABAJO                    la voz real → maqueta.json con los segundos reales (V6) + gates M3D
  render TRABAJO [--formato 9:16|4:5|ambos]           → render3d/<formato>/video.mp4 (scripts/maqueta3d.py)
  montar TRABAJO [--formato 9:16|4:5|ambos] [--sin-portada]   voz + música con ducking + efectos, −14 LUFS → salida/ (la mezcla
                                     de youtube.pista_final y el .srt de video.texto_srt: los de los demás flujos); con
                                     el 9:16, la portada (salida/portada.png)
  portada TRABAJO                    el cuadro cero en 9:16, sin subtítulos → salida/portada.png (lo llama montar)
  entregar TRABAJO [--salida DIR] [--sin-4x5]
        → videos3d/<fecha>-<slug>/ (video, 4:5, portada, guion, tiempos.json, fuentes.md, caption.md); sin el 4:5 falla,
        salvo con --sin-4x5

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402
import video as VD  # noqa: E402
import maqueta3d as M3  # noqa: E402  (el catálogo del vocabulario: maqueta3d.py catalogo)

FPS = 30
OBJETIVO_S, TOL = 45, 0.2            # duración por defecto y tolerancia de C3D9
DURACION_MIN_S, DURACION_MAX_S = 20, 180   # C3D9: de 20 s a 3 min, como los demás videos (el tope de Shorts; usuario, 2026-11-15)
ESCENAS = (4, 9)                     # contando el gancho y el cierre; el tope crece con la duración (SEG_POR_ESCENA)
SEG_POR_ESCENA = 7                   # un video largo lleva las escenas que necesite: ≈ una cada 7 s del objetivo
GANCHO_VOZ_S = 6.0                   # la voz del gancho (medido con /analyze-improve: ≤ 6 s)
GUATEMALA_S = 6.0                    # «Guatemala» se oye antes de este segundo
EVENTO_GANCHO_S = 1.0                # el gancho es un evento 3D: algo pasa antes de este segundo (M3D9)
RITMO_AVISO_S, RITMO_S = 6.0, 9.0    # C3D7: segundos sin nada nuevo en pantalla (la cámara sigue moviéndose)
CIERRE_VOZ = 160                     # F9: la voz del cierre, de 160 caracteres para abajo
ADELANTO = 0.25                      # marcas y cifras empiezan a entrar un poco antes de la palabra
COLA_CORTE, COLA_CIERRE = 0.45, 2.8  # aire tras una escena que cierra secuencia; «Sígueme en» se queda en pantalla
SEGUIR_S = 3.0                       # el botón «Sígueme» a mitad del video
ESTILOS = os.path.join(RAIZ, "design", "sets3d", "estilos.json")
MAQUETA3D = os.path.join(RAIZ, "scripts", "maqueta3d.py")
REENVIO = ("voz", "voz-falsa", "descargar", "partir", "escuchar")   # escuchar = V11 (whisper): solo usa locucion.json y audio/
ROTACION_GANCHOS = 2                 # la familia del gancho de los últimos 2 videos 3D no se repite (aviso)
REGISTRO = os.path.join(RAIZ, "memoria", "videos3d.json")
RE_DISTANCIA = re.compile(r"\b\d[\d.,]*\s*(?:km|kil[oó]metros?|m|metros?)\b", re.I)   # C3D11: un pin que dice una distancia
HANDLE = "@DerekUrizar"


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def falla(msg):
    print("ERROR: " + msg, file=sys.stderr)
    return 1


def rel(p):
    return os.path.relpath(p, RAIZ)


def cuadro(s):
    return round(round(s * FPS) / FPS, 4)


def estado(trabajo):
    return leer(os.path.join(trabajo, "video3d.json"))


# ---------- datos: las cifras verificadas que respaldan cada número ----------
def cifras_ok(trabajo):
    """(valores [(número, factor)], cifras verificadas por id) de base/datos.json: lo único que respalda un número."""
    datos = leer(os.path.join(trabajo, "base", "datos.json"))
    valores, por_id = set(), {}
    for c in datos.get("cifras") or []:
        if c.get("veredicto") not in ("verificada", "ajustada"):
            continue
        v = c.get("valor_final", c.get("valor"))
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            valores.add((round(float(v), 6), VM.factor_unidad(c.get("unidad"))))
        por_id[c["id"]] = c
    return sorted(valores, key=lambda x: (x[0], str(x[1]))), por_id


ESCALAS_CERCA = ("esquema", "ciudad")     # los mundos de cerca: cada uno es una ESCENA VIVA (C3D14–C3D18, M3D15–M3D19)
CLAVES_ESCENA = ("que_pasa", "quien", "con_que", "se_mueve")
NADIE = ("", "nadie", "ninguno", "ninguna", "no hay")
HORAS = ("amanecer", "dia", "atardecer", "noche")   # mundo.hora (C3D19; las resuelve el estilo: design/sets3d/estilos.json → horas)
NOMBRA_S = 3.0                            # C3D16: cada tramo dice dónde estamos en sus primeros segundos


def hechos_ok(trabajo):
    """Los ids que sostienen lo que se dibuja: hechos (confirmado | una_fuente) y cifras (verificada | ajustada) de los
    verificacion_*.json del TRABAJO, más las cifras de base/datos.json."""
    ids = set(cifras_ok(trabajo)[1])
    try:
        nombres = sorted(n for n in os.listdir(trabajo) if n.startswith("verificacion") and n.endswith(".json"))
    except OSError:
        nombres = []
    for n in nombres:
        try:
            d = leer(os.path.join(trabajo, n))
        except (OSError, ValueError):
            continue
        ids.update(h["id"] for h in d.get("hechos") or [] if h.get("id") and h.get("estado") in ("confirmado", "una_fuente"))
        ids.update(c["id"] for c in d.get("cifras") or [] if c.get("id") and c.get("veredicto") in ("verificada", "ajustada"))
    return ids


def revisar_escenas(g, MUNDOS, trabajo):
    """C3D14 la ficha de escena de cada mundo de cerca · C3D15 lo que se dibuja se sostiene · C3D17 gente · C3D18 un
    objeto, un papel. → (fallas, avisos)."""
    fallas, avisos = [], []
    ok_ids = hechos_ok(trabajo)
    papeles = {}    # objeto → {texto de la marca que lo nombra}
    for mid, mu in MUNDOS.items():
        mu = mu or {}
        if (mu.get("escala") or "pais") not in ESCALAS_CERCA:
            continue
        esc = mu.get("escena")
        if not isinstance(esc, dict) or any(not isinstance(esc.get(k), str) or not esc[k].strip() for k in CLAVES_ESCENA):
            fallas.append("C3D14 el mundo «%s» es una escena de cerca y lleva su ficha `escena`: {que_pasa (lo que ocurre ahí en la realidad), quien "
                          "(quién lo hace, o «nadie»), con_que (con qué: herramientas, máquinas, vehículos), se_mueve (qué se mueve en pantalla), "
                          "sostiene: [{que, hecho | generico}]}" % mid)
            continue
        sos = esc.get("sostiene")
        if not isinstance(sos, list) or not sos:
            fallas.append("C3D15 el mundo «%s»: `escena.sostiene` lista lo que se dibuja y qué lo sostiene ([{que, hecho: <id verificado>} | {que, generico: true}])" % mid)
        else:
            for it in sos:
                if not isinstance(it, dict) or not (it.get("que") or "").strip():
                    fallas.append("C3D15 el mundo «%s»: cada entrada de `sostiene` dice `que` se dibuja" % mid)
                elif it.get("hecho"):
                    if it["hecho"] not in ok_ids:
                        fallas.append("C3D15 el mundo «%s»: «%s» se apoya en «%s», que no es un hecho ni una cifra verificados del TRABAJO "
                                      "(verificacion_*.json, base/datos.json)" % (mid, it["que"], it["hecho"]))
                elif it.get("generico") is not True:
                    fallas.append("C3D15 el mundo «%s»: «%s» lleva `hecho` (el id que lo sostiene) o `generico: true` (ilustración que no afirma nada)" % (mid, it["que"]))
            if all(isinstance(it, dict) and it.get("generico") is True for it in sos):
                if not (esc.get("ilustrativa") or "").strip():
                    fallas.append("C3D15 el mundo «%s»: nada de lo que dibuja se apoya en un hecho verificado; o verifica cómo es el lugar (la fase "
                                  "«Referencia visual») o declara `escena.ilustrativa` con la razón (un mecanismo, un lugar cualquiera)" % mid)
        # C3D17 · gente: si alguien hace lo que pasa, se ve gente haciéndolo
        gente = 0
        for pz in mu.get("piezas") or []:
            if pz.get("tipo") == "actor":
                gente += bool((M3.ficha(pz.get("objeto"), "objeto") or {}).get("gente"))
            else:
                fp = M3.ficha(pz.get("tipo"), "pieza") or {}
                if fp.get("gente"):
                    dp = (fp.get("parametros") or {}).get("personas") or {}
                    gente += int(pz.get("personas", dp.get("defecto", 1)) or 0)
        if esc["quien"].strip().lower() not in NADIE and gente < 2:
            fallas.append("C3D17 el mundo «%s»: `escena.quien` dice «%s» y en la escena hay %d persona(s): pon al menos 2 haciendo algo "
                          "(objetos con `gente` del catálogo, o piezas con `personas`)" % (mid, esc["quien"], gente))
    # C3D18 · un objeto, un papel: el mismo objeto no se rotula como dos cosas distintas
    for e in escenas_de(g):
        mundos_e = [mundo_de_escena(g, e)] + [cb.get("mundo") for cb in e.get("cambios") or []]
        for mk in e.get("marcas") or []:
            clave = json.dumps(mk.get("lugar"), sort_keys=True)
            for mid in mundos_e:
                for pz in (MUNDOS.get(mid) or {}).get("piezas") or []:
                    if pz.get("tipo") == "actor" and pz.get("lugar") is not None and json.dumps(pz["lugar"], sort_keys=True) == clave:
                        if not (M3.ficha(pz.get("objeto"), "objeto") or {}).get("gente"):
                            papeles.setdefault(pz["objeto"], set()).add((mk.get("texto") or "").strip().lower())
    for obj, textos in sorted(papeles.items()):
        if len(textos) > 1:
            fallas.append("C3D18 el objeto «%s» hace de %d cosas distintas (%s): cada cosa de la historia, su propio objeto (pídelo al constructor "
                          "con un brief)" % (obj, len(textos), ", ".join("«%s»" % t for t in sorted(textos))))
    return fallas, avisos


def lugares_del_set(nombre_set):
    """{id: {nombre, lon, lat}} del set (design/sets3d/<set>/lugares.json; admite lista o dict)."""
    ruta = os.path.join(RAIZ, "design", "sets3d", nombre_set or "", "lugares.json")
    if not os.path.exists(ruta):
        return {}
    d = leer(ruta)
    d = d.get("lugares", d) if isinstance(d, dict) else d
    if isinstance(d, list):
        return {x["id"]: x for x in d if isinstance(x, dict) and x.get("id")}
    return {k: v for k, v in d.items() if isinstance(v, dict)}


def mundos_de(g):
    """Los mundos del guion: {id: mundo}. Un guion con un solo `mundo` es un mundo llamado «principal»; con `mundos`
    (varios mundos en un video, usuario 2026-11-15) cada escena dice el suyo con `mundo: <id>`."""
    if isinstance(g.get("mundos"), dict) and g["mundos"]:
        return g["mundos"]
    return {"principal": g.get("mundo") or {}}


def mundo_de_escena(g, e):
    M = mundos_de(g)
    return e.get("mundo") if isinstance(g.get("mundos"), dict) else "principal" if "principal" in M else next(iter(M))


_LUGARES_MUNDO = {}


def lugares_de_mundo(mundo, estilo_id=None):
    """{id: {nombre, …}} de un mundo: los del set (pais, ciudad) o los de su receta (esquema), más mundo.lugares."""
    clave = json.dumps([mundo.get("escala"), mundo.get("set"), mundo.get("receta"), mundo.get("semilla"), mundo.get("tamano_m"),
                        mundo.get("carriles"), mundo.get("manzana_m")], sort_keys=True)
    if clave not in _LUGARES_MUNDO:
        base = {}
        if (mundo.get("escala") or "pais") == "pais":
            base = lugares_del_set(mundo.get("set"))
        else:
            try:   # ciudad y esquema: los lugares los arma su módulo (la receta, el set de la ciudad)
                est = M3.catalogo_estilos().get(estilo_id) or next(e for e in M3.catalogo_estilos().values() if e["motor"] == "three")
                W = M3.mundo_de({k: v for k, v in mundo.items() if k not in ("lugares", "piezas", "protagonista", "capas")}, est, [])
                base = {k: dict(v) for k, v in (W.lugares or {}).items()}
            except Exception:    # noqa: BLE001 — el mundo mal declarado lo dice M3D2 en `guion --check`
                base = {}
        _LUGARES_MUNDO[clave] = base
    return dict(_LUGARES_MUNDO[clave], **(mundo.get("lugares") or {}))


def pie_de_capas(nombre_set, usadas):
    """El pie de UN set con solo las capas que el video usa (m256), agrupadas por fuente: «Lugares, ríos y lagos: ©
    OpenStreetMap». Sin fuente.json o sin capas con atribución → el pie entero del set."""
    ruta = os.path.join(RAIZ, "design", "sets3d", nombre_set or "", "fuente.json")
    if not os.path.exists(ruta):
        return ""
    capas = leer(ruta).get("capas")
    if not isinstance(capas, dict):
        return pie_del_set(nombre_set)
    por = {}
    for k, c in capas.items():
        if k in usadas and isinstance(c, dict) and ": " in (c.get("atribucion") or ""):
            etiqueta, _, fuente = c["atribucion"].partition(": ")
            por.setdefault(fuente, []).append(etiqueta)
    partes = []
    for fuente, ets in por.items():
        ets = [ets[0]] + [e[:1].lower() + e[1:] for e in ets[1:]]
        partes.append("%s: %s" % (ets[0] if len(ets) == 1 else ", ".join(ets[:-1]) + " y " + ets[-1], fuente))
    return " · ".join(partes)


def pie_del_set(nombre_set):
    ruta = os.path.join(RAIZ, "design", "sets3d", nombre_set or "", "fuente.json")
    if not os.path.exists(ruta):
        return ""
    d = leer(ruta)
    if d.get("pie"):
        return d["pie"]
    capas = d.get("capas") or d
    capas = capas.values() if isinstance(capas, dict) else capas
    return " · ".join(x["atribucion"] for x in capas if isinstance(x, dict) and x.get("atribucion"))


# ---------- la voz: texto con cifras en dígitos → pantalla, voz en palabras y prompt ----------
def segmentar(texto):
    """Como video.py: (pantalla, voz en palabras, prompt de ElevenLabs, segmentos p/v/num)."""
    NE.AVISOS.clear()
    segs = NE.segmentos(texto)
    VD.mayuscula_inicial(segs)
    prompt = VD.sin_comillas(VD.con_breaks("".join(s["v"] for s in segs)))
    for s in segs:
        s["p"], s["v"] = VD.sin_pausas(s["p"]), VD.sin_pausas(s["v"])
    segs[0]["p"], segs[0]["v"] = segs[0]["p"].lstrip(), segs[0]["v"].lstrip()
    return "".join(s["p"] for s in segs), "".join(s["v"] for s in segs), prompt, segs


def fichas(frase):
    """Una frase (con cifras en dígitos o en palabras) como la dice la voz: palabras normalizadas."""
    return [w for w in (VD._norm(x) for x in VD.dicho(frase).split()) if w]


def estimadas(voz):
    """Las palabras de una voz con el tiempo que tendrían (CPS ya acelerado): lo que se usa antes de grabar."""
    t, ws = 0.0, []
    for w in voz.split():
        d = (len(w) + 1) / VD.CPS
        ws.append({"text": w, "start": round(t, 3), "end": round(t + d * 0.85, 3)})
        t += d
    return ws


def buscar(habladas, frase, vez=1):
    """(índice inicial, índice final) de la `vez`-ésima aparición de la frase en las palabras habladas, o None."""
    toks = fichas(frase)
    if not toks:
        return None
    norm = [VD._norm(w["text"]) for w in habladas]
    vistas = 0
    for i in range(len(norm) - len(toks) + 1):
        if norm[i:i + len(toks)] == toks:
            vistas += 1
            if vistas == vez:
                return i, i + len(toks) - 1
    return None


# ---------- el guion ----------
def escenas_de(g):
    return [e for e in g.get("escenas") or [] if isinstance(e, dict)]


def elementos(e):
    """Todo lo que una escena pone en pantalla, con su clase: [(clase, objeto)]."""
    out = [("camara", x) for x in e.get("camara") or []] + [("evento", x) for x in e.get("eventos") or []]
    out += [("marca", x) for x in e.get("marcas") or []] + [("cifra", x) for x in e.get("cifras") or []]
    out += [("anotacion", x) for x in e.get("anotaciones") or []]   # pulso, medida, etiqueta, reloj (capa 2D atada al 3D)
    if e.get("titular"):
        out.append(("titular", e["titular"]))
    return out


def locucion_de(g):
    """[{n, tipo, acto, secuencia, texto, pantalla, voz, prompt, segmentos, cola}] + fallas V3."""
    loc, fallas = [], []
    escenas = escenas_de(g)
    for k, e in enumerate(escenas):
        try:
            pantalla, voz, prompt, segs = segmentar(e.get("texto") or "")
        except ValueError as ex:
            fallas.append("V3 escena %d: %s" % (e.get("n", k + 1), ex))
            continue
        for av in NE.AVISOS:
            fallas.append("V3 escena %d: %s" % (e.get("n", k + 1), av))
        NE.AVISOS.clear()
        sec = e.get("secuencia")
        sigue = bool(sec) and k + 1 < len(escenas) and escenas[k + 1].get("secuencia") == sec
        cola = COLA_CIERRE if e.get("tipo") == "cierre" else (0.0 if sigue else COLA_CORTE)
        loc.append({"n": e.get("n", k + 1), "tipo": e.get("tipo") or "toma", "acto": e.get("acto"), "secuencia": sec,
                    "plantilla": "maqueta", "tuit": None, "pantalla": pantalla, "voz": voz, "prompt": prompt, "segmentos": segs,
                    "cola": cola, "estimado_s": round(VD.segundos_voz(voz) + cola, 2)})   # el estimador de todos los flujos
    return loc, fallas


def hechos_3d():
    """Los videos 3D ya registrados (memoria/videos3d.json), del más viejo al más nuevo."""
    return (leer(REGISTRO).get("videos3d") or []) if os.path.exists(REGISTRO) else []


def familias_recientes(st):
    """Las familias de gancho de los últimos ROTACION_GANCHOS videos 3D (sin contar este): no se repiten. Una maqueta de
    prueba (`fixture`) no rota."""
    if st.get("fixture"):
        return []
    hechos = [v for v in hechos_3d() if v.get("slug") != st.get("slug")]
    return [f for f in ((v.get("gancho") or {}).get("familia") for v in hechos[-ROTACION_GANCHOS:]) if f]


def revisar_caption(g):
    """V5 de los demás flujos (scripts/video.py, cmd_guion) sobre `guion.caption`: un caption por plataforma, el de Shorts
    con su título de ≤ SHORTS_TITULO caracteres en la primera línea y #Shorts, ninguna cifra en palabras, sin anunciar el
    video y sin «en suma». Las reglas están escritas dentro de video.cmd_guion (no se pueden llamar): aquí se repiten con
    sus mismas constantes. → fallas."""
    cap = g.get("caption") if isinstance(g.get("caption"), dict) else {}
    fallas = ["V5 falta caption.%s" % k for k, _ in VD.PLATAFORMAS if not (cap.get(k) or "").strip()]
    sh = (cap.get("shorts") or "").strip()
    if sh:
        titulo = sh.splitlines()[0].strip()
        if len(titulo) > VD.SHORTS_TITULO:
            fallas.append("V5 caption.shorts: la primera línea es el título de YouTube (≤ %d caracteres; llegó %d)" % (VD.SHORTS_TITULO, len(titulo)))
        if "#shorts" not in sh.lower():
            fallas.append("V5 caption.shorts lleva #Shorts")
    for k, v in cap.items():
        if not isinstance(v, str):
            continue
        if VD.RE_CIFRA_EN_PALABRAS.search(v):
            fallas.append("V5 caption.%s escribe una cifra en palabras («%s»): en el texto para publicar va en dígitos, como en "
                          "pantalla" % (k, VD.RE_CIFRA_EN_PALABRAS.search(v).group(0)))
        if VD.PROMESA_PROHIBIDA.search(v):
            fallas.append("V5 caption.%s anuncia el video («%s»): la intriga sale del tema (referencias/promesas.md)"
                          % (k, VD.PROMESA_PROHIBIDA.search(v).group(0)))
        if re.search(r"\ben suma\b", v, re.I):
            fallas.append("V5 caption.%s: «en suma» está prohibido" % k)
    return fallas


def secuencias_de(loc):
    grupos, out, fallas = {}, [], []
    for x in loc:
        if x.get("secuencia"):
            grupos.setdefault(x["secuencia"], []).append(x)
    for k in sorted(grupos):
        xs = grupos[k]
        car = sum(len(x["voz"]) for x in xs)
        if car > VD.SECUENCIA_CARACTERES:
            fallas.append("V9 secuencia %d: %d caracteres de voz; van ≤ %d por nodo (parte la secuencia)" % (k, car, VD.SECUENCIA_CARACTERES))
        if [x["n"] for x in xs] != list(range(xs[0]["n"], xs[0]["n"] + len(xs))):
            fallas.append("V9 secuencia %d: sus escenas van seguidas (%s)" % (k, ", ".join(str(x["n"]) for x in xs)))
        out.append({"k": k, "escenas": [x["n"] for x in xs], "prompt": VD.unir_secuencia([x["prompt"] for x in xs]), "caracteres": car})
    return out, fallas


def revisar_guion(g, st, trabajo):
    """C3D1–C3D11 y V2–V4 sobre guion.json → (fallas, avisos, locución)."""
    fallas, avisos = [], []
    escenas = escenas_de(g)
    valores, por_id = cifras_ok(trabajo)
    MUNDOS = mundos_de(g)
    est_id = (g.get("estilo") or {}).get("id")
    lug_m = {k: lugares_de_mundo(v or {}, est_id) for k, v in MUNDOS.items()}
    pie_m = {k: {p.get("id"): p for p in (v or {}).get("piezas") or []} for k, v in MUNDOS.items()}
    # C3D12 · mundos: cada escena dice un mundo que existe (con `mundos`) y cada mundo se usa
    if isinstance(g.get("mundos"), dict):
        if g.get("mundo"):
            fallas.append("C3D12 el guion trae `mundo` y `mundos`: con varios mundos van todos en `mundos` ({id: mundo})")
        for e in escenas:
            if e.get("mundo") not in MUNDOS:
                fallas.append("C3D12 escena %s: `mundo` «%s» no está en `mundos` (hay: %s)" % (e.get("n"), e.get("mundo"), ", ".join(MUNDOS)))
            if e.get("transicion") is not None and e.get("transicion") not in ("corte", "fundido", "oscuro"):
                fallas.append("C3D12 escena %s: `transicion` «%s» (hay: corte, fundido, oscuro)" % (e.get("n"), e.get("transicion")))
        sobran = [k for k in MUNDOS if k not in {e.get("mundo") for e in escenas} | {cb.get("mundo") for e in escenas for cb in e.get("cambios") or []}]
        if sobran:
            fallas.append("C3D12 los mundos %s no se usan en ninguna escena: quítalos" % ", ".join("«%s»" % k for k in sobran))
        # C3D13 · dinamismo: no se vuelve a un mundo a mitad del video (cada paso de la historia, su mundo); solo el cierre
        # puede volver a uno ya visto (el bucle). Usuario, 2026-11-16: «re usaste muchas escenas».
        rachas, entradas = [], []   # entradas: (mundo, escena, transición con la que se entra, la escena) por racha
        for e in escenas:
            for mid_r, trans in [(e.get("mundo"), e.get("transicion"))] + [(cb.get("mundo"), cb.get("transicion")) for cb in e.get("cambios") or []]:
                if not rachas or rachas[-1][0] != mid_r:
                    rachas.append((mid_r, e.get("n"), e.get("tipo")))
                    entradas.append((mid_r, e.get("n"), trans, e))
        # C3D19 · la hora cuenta algo: una hora distinta del día lleva su razón, y un salto de hora entre escenas de cerca
        # seguidas se ve (transición `oscuro`) o se oye (`salto_hora`: la frase de la voz que lo dice)
        for mid_h, mu_h in MUNDOS.items():
            h = (mu_h or {}).get("hora")
            if h is not None and h not in HORAS:
                fallas.append("C3D19 el mundo «%s»: `hora` «%s» (hay: %s)" % (mid_h, h, ", ".join(HORAS)))
            elif h not in (None, "dia") and not ((mu_h or {}).get("hora_razon") or "").strip():
                fallas.append("C3D19 el mundo «%s» va de «%s»: di por qué en `hora_razon` (eso pasa a esa hora en la realidad, o marca el paso del tiempo)" % (mid_h, h))
        hora_prev = None
        for mid_h, n_h, trans, e_h in entradas:
            mu_h = MUNDOS.get(mid_h) or {}
            if (mu_h.get("escala") or "pais") not in ESCALAS_CERCA:
                continue
            h = mu_h.get("hora") or "dia"
            if hora_prev is not None and h != hora_prev and trans != "oscuro":
                dicho = e_h.get("salto_hora")
                if not (dicho and VD._norm(dicho) in VD._norm(e_h.get("texto") or "")):
                    fallas.append("C3D19 escena %s: se pasa de «%s» a «%s» sin que se note: entra con `transicion: \"oscuro\"` o pon en `salto_hora` la "
                                  "frase de la voz que lo dice" % (n_h, hora_prev, h))
            hora_prev = h
        vistos = set()
        for i, (mid, n, tipo) in enumerate(rachas):
            if mid in vistos and not (i == len(rachas) - 1 and tipo == "cierre"):
                fallas.append("C3D13 escena %s vuelve al mundo «%s», ya visto: cada paso va en su mundo (solo el cierre puede volver al del "
                              "gancho, el bucle); si es otro lugar, que sea otro mundo con su propio aspecto" % (n, mid))
            vistos.add(mid)
    elif any(e.get("mundo") for e in escenas):
        fallas.append("C3D12 una escena dice `mundo` y el guion tiene uno solo: con varios mundos van en `mundos` ({id: mundo})")
    f_esc, a_esc = revisar_escenas(g, MUNDOS, trabajo)
    fallas += f_esc
    avisos += a_esc
    todas = {pid: p for d in pie_m.values() for pid, p in d.items()}
    piezas, lugares, mundo = todas, {}, {}

    # C3D1 forma: un estilo con su razón, el protagonista, el gancho primero y el cierre al final
    est = g.get("estilo") or {}
    catalogo = {x["id"]: x for x in leer(ESTILOS)["estilos"]} if os.path.exists(ESTILOS) else {}
    if not est.get("id") or not (est.get("razon") or "").strip():
        fallas.append("C3D1 falta estilo.id y estilo.razon (un solo estilo por video, con el porqué)")
    elif catalogo and est["id"] not in catalogo:
        fallas.append("C3D1 estilo «%s» no está en design/sets3d/estilos.json (%s)" % (est["id"], ", ".join(sorted(catalogo))))
    if est.get("confianza") == "baja" and not est.get("elegido_por_usuario"):
        fallas.append("C3D1 estilo.confianza es «baja»: pregunta al usuario cuál estilo va (con cuadros de los candidatos) y "
                      "anota estilo.elegido_por_usuario: true")
    if any("estilo" in x for e in escenas for _, x in elementos(e)) or any("estilo" in e for e in escenas):
        fallas.append("C3D1 un solo estilo por video: ninguna escena ni pieza lleva `estilo` propio")
    if not (g.get("idea_visual") or "").strip():
        fallas.append("C3D1 falta idea_visual: la imagen del video en una oración (de ahí salen el gancho, el estilo y el cierre)")
    prota = g.get("protagonista")
    protas = [(v or {}).get("protagonista") for v in MUNDOS.values() if (v or {}).get("protagonista")]
    if prota not in piezas and not protas:
        fallas.append("C3D1 protagonista «%s» no es una pieza de mundo.piezas: es lo único que va en el acento" % prota)
    for k, v in MUNDOS.items():
        pv = (v or {}).get("protagonista")
        if pv and pv not in pie_m[k]:
            fallas.append("C3D1 el protagonista «%s» del mundo «%s» no es una de sus piezas" % (pv, k))
    tope = max(ESCENAS[1], int(float(st.get("duracion_s") or OBJETIVO_S) // SEG_POR_ESCENA))   # las que el video necesite
    if not ESCENAS[0] <= len(escenas) <= tope:
        fallas.append("C3D1 %d escenas; van %d–%d contando el gancho y el cierre (≈ una cada %d s del objetivo)" % (len(escenas), ESCENAS[0], tope, SEG_POR_ESCENA))
    if escenas and (escenas[0].get("tipo") != "gancho" or escenas[-1].get("tipo") != "cierre"):
        fallas.append("C3D1 la primera escena es `gancho` y la última `cierre`")
    if [e.get("n") for e in escenas] != list(range(1, len(escenas) + 1)):
        fallas.append("C3D1 las escenas se numeran 1…N en orden (`n`)")

    loc, f3 = locucion_de(g)
    fallas += f3
    if len(loc) != len(escenas):
        return fallas, avisos, loc
    secuencias, fs = secuencias_de(loc)
    fallas += fs

    t0, cambios = 0.0, []
    vivas, mundo_prev = [], None   # marcas de escenas anteriores (del mismo mundo) que siguen en pantalla
    for e, x in zip(escenas, loc):
        n, hab = x["n"], estimadas(x["voz"])
        mid = mundo_de_escena(g, e)
        mundo, lugares, piezas = MUNDOS.get(mid) or {}, lug_m.get(mid) or {}, pie_m.get(mid) or {}
        nuevo_mundo = mid != mundo_prev
        if mid != mundo_prev:
            vivas, mundo_prev = [], mid    # al cambiar de mundo, las marcas del anterior se van
        # CAMBIOS de mundo a mitad de la escena (`cambios: [{dice, mundo, transicion?}]`): cada cosa va al mundo vivo en su frase
        cambios_e = []
        for cb in e.get("cambios") or []:
            pos = buscar(hab, cb.get("dice")) if cb.get("dice") else None
            if not pos:
                fallas.append("C3D12 escena %d: el cambio de mundo va anclado a una frase que la voz de la escena dice (`dice`; hoy «%s»)" % (n, cb.get("dice")))
            elif cb.get("mundo") not in MUNDOS:
                fallas.append("C3D12 escena %d: el cambio va al mundo «%s», que no está en `mundos`" % (n, cb.get("mundo")))
            else:
                cambios_e.append((pos[0], cb["mundo"]))
        if e.get("cambios") and not isinstance(g.get("mundos"), dict):
            fallas.append("C3D12 escena %d: `cambios` de mundo pide un guion con `mundos`" % n)
        cambios_e.sort()

        def mundo_en(o, base=mid):
            if not cambios_e:
                return base
            p_o = buscar(hab, o["dice"], o.get("vez", 1)) if o.get("dice") else None
            i_o = p_o[0] if p_o else (len(hab) if o.get("al") == "fin" else 0)
            return ([m for i, m in cambios_e if i <= i_o] or [base])[-1]
        nombres = {}
        for w_id in [mid] + [m for _, m in cambios_e]:
            for k, v in (lug_m.get(w_id) or {}).items():
                toks = tuple(fichas(v.get("nombre") or ""))
                if toks and toks != ("guatemala",):
                    nombres.setdefault(toks, set()).add(k)
        lugares_e = dict(lugares)
        for _, w_id in cambios_e:
            lugares_e.update(lug_m.get(w_id) or {})
        norm = [VD._norm(w["text"]) for w in hab]
        # V2 cada número de la voz con respaldo
        sin = VM.sueltos(x["pantalla"], valores, ())
        if sin:
            fallas.append("V2 escena %d: números sin respaldo en la voz: %s (falta la cifra verificada en base/datos.json)"
                          % (n, ", ".join(map(str, sin))))
        for clase, o in elementos(e):
            mid_o = mundo_en(o)
            mundo, lugares, piezas = MUNDOS.get(mid_o) or {}, lug_m.get(mid_o) or {}, pie_m.get(mid_o) or {}
            # C3D2 cada cosa que entra nace en una frase que la voz dice (o al empezar la escena)
            for clave in ("dice", "hasta_dice"):
                if o.get(clave) and not buscar(hab, o[clave], o.get("vez", 1) if clave == "dice" else 1):
                    fallas.append("C3D2 escena %d: %s con %s «%s», que la voz de esa escena no dice" % (n, clase, clave, o[clave]))
            pos = buscar(hab, o.get("dice"), o.get("vez", 1)) if o.get("dice") else None
            cambios.append((t0 + (hab[pos[0]]["start"] if pos else 0.0), "%s E%d" % (clase, n)))
            # C3D5 lo que se lee en pantalla también lleva respaldo
            textos = (M3.textos_anotacion(o, mundo.get("escala") or "pais") if clase == "anotacion"   # sus reglas dicen qué se lee
                      else [o.get(c) for c in ("texto", "sub", "kicker", "valor", "rotulo") if isinstance(o.get(c), str)])
            for texto in textos:
                sin = VD.sin_respaldo(texto, valores)
                if sin:
                    fallas.append("C3D5 escena %d: «%s» lleva un número sin respaldo (%s)" % (n, texto, ", ".join(map(str, sin))))
            if clase == "camara":
                m = o.get("mira")
                if isinstance(m, str) and m not in lugares:
                    fallas.append("C3D3 escena %d: la cámara mira «%s», que no es un lugar del mundo «%s» (su set o receta, o mundo.lugares)" % (n, m, mid_o))
            if clase == "marca" and isinstance(o.get("lugar"), str) and o["lugar"] not in lugares:
                fallas.append("C3D3 escena %d: marca en «%s», que no es un lugar del mundo «%s» (su set o receta, o mundo.lugares)" % (n, o.get("lugar"), mid_o))
            if clase == "marca":
                dice_distancia = RE_DISTANCIA.search("%s %s" % (o.get("texto", ""), o.get("sub", "")))
                if dice_distancia and o.get("separada_de") not in piezas:
                    fallas.append("C3D11 escena %d: la marca «%s» dice una distancia («%s»): declara `separada_de` con la pieza de la que "
                                  "está a esa distancia, para que el gate M3D11 mida que en pantalla no queden pegadas"
                                  % (n, o.get("texto"), dice_distancia.group()))
                elif o.get("separada_de") and o["separada_de"] not in piezas:
                    fallas.append("C3D11 escena %d: `separada_de` «%s» no es una pieza de mundo.piezas" % (n, o["separada_de"]))
            if clase == "evento":
                if o.get("tipo") not in M3.tipos("evento"):
                    fallas.append("C3D6 escena %d: el evento «%s» no está en el catálogo (maqueta3d.py catalogo; hay: %s); si hace falta, pídelo al "
                                  "constructor con un brief" % (n, o.get("tipo"), ", ".join(M3.tipos("evento"))))
                if not isinstance(o.get("dur"), (int, float)) and not o.get("hasta_dice"):
                    fallas.append("C3D6 escena %d: el evento %s lleva `dur` (segundos) o `hasta_dice`" % (n, o.get("tipo")))
                if o.get("pieza") and o["pieza"] not in piezas:
                    fallas.append("C3D6 escena %d: el evento usa la pieza «%s», que no está en mundo.piezas" % (n, o["pieza"]))
            if clase == "cifra":
                # C3D4 la cifra entra cuando la voz la dice, con su id verificado; una sola fuente va con su fuente
                c = por_id.get(o.get("cifra"))
                if not c:
                    fallas.append("C3D4 escena %d: la cifra «%s» no tiene `cifra` (id verificado de base/datos.json)" % (n, o.get("valor")))
                if not o.get("dice"):
                    fallas.append("C3D4 escena %d: la cifra «%s» lleva `dice`: entra cuando la voz la dice" % (n, o.get("valor")))
                if not (o.get("rotulo") or "").strip():
                    fallas.append("C3D4 escena %d: la cifra «%s» lleva `rotulo` (qué cuenta)" % (n, o.get("valor")))
                if c and c.get("una_fuente") and not (o.get("fuente") or "").strip():
                    fallas.append("C3D4 escena %d: «%s» sale de una sola fuente: lleva `fuente` en pantalla" % (n, o.get("valor")))
        # C3D3 cada lugar que la voz nombra tiene su marca (en esta escena o viva de antes) o es adonde mira la cámara;
        # vale la marca puesta en ese lugar o la que lo nombra en su tarjeta (varios pueblos comparten nombre)
        marcas_e = list(e.get("marcas") or []) + vivas
        ids_e = {m.get("lugar") for m in marcas_e if isinstance(m.get("lugar"), str)} | \
                {c.get("mira") for c in e.get("camara") or [] if isinstance(c.get("mira"), str)}
        rotulos = [fichas("%s %s" % (m.get("texto", ""), m.get("sub", ""))) for m in marcas_e]
        for toks, ids in nombres.items():
            toks = list(toks)
            dicho = any(norm[i:i + len(toks)] == toks for i in range(len(norm) - len(toks) + 1))
            escrito = any(r[i:i + len(toks)] == toks for r in rotulos for i in range(len(r) - len(toks) + 1))
            if dicho and not (ids & ids_e) and not escrito:
                fallas.append("C3D3 escena %d: la voz nombra «%s» y no hay marca ni la cámara lo mira: lo que se oye se ve"
                              % (n, lugares_e[sorted(ids)[0]].get("nombre")))
        vivas = [m for m in marcas_e if isinstance(m.get("hasta"), int) and m["hasta"] > n]
        # C3D16 · se explica: cada tramo de cerca dice dónde estamos en sus primeros segundos (un titular o una marca)
        if e.get("tipo") != "cierre":
            inicios = ([(0, mid)] if nuevo_mundo else []) + list(cambios_e)
            rotulos_t = []    # (índice de la palabra en que entra, es titular)
            for clase, o in elementos(e):
                if clase in ("marca", "titular"):
                    p_o = buscar(hab, o["dice"], o.get("vez", 1)) if o.get("dice") else None
                    rotulos_t.append(p_o[0] if p_o else 0)
            for i0, w_id in inicios:
                if ((MUNDOS.get(w_id) or {}).get("escala") or "pais") not in ESCALAS_CERCA:
                    continue
                t_i = hab[i0]["start"] if i0 < len(hab) else 0.0
                if not any(i >= i0 and (hab[i]["start"] if i < len(hab) else 0.0) - t_i <= NOMBRA_S for i in rotulos_t):
                    fallas.append("C3D16 escena %d: al entrar al mundo «%s» nada dice dónde estamos en sus primeros %.0f s: un titular o una marca "
                                  "que lo nombre (y cada paso de un proceso, su rótulo)" % (n, w_id, NOMBRA_S))
        if cambios_e:   # la escena termina en otro mundo: lo que sigue vivo es de ese
            vivas, mundo_prev = [], cambios_e[-1][1]
        t0 += x["estimado_s"]

    # C3D6 el gancho: un evento en el segundo cero, voz corta y «Guatemala» pronto
    if escenas and loc:
        g1, x1 = escenas[0], loc[0]
        if not any(not ev.get("dice") for ev in g1.get("eventos") or []):
            fallas.append("C3D6 el gancho es un evento: la escena 1 lleva un evento sin `dice` (pasa en el segundo cero, "
                          "antes del segundo %.0f)" % EVENTO_GANCHO_S)
        if not g1.get("camara") or g1["camara"][0].get("dice"):
            fallas.append("C3D6 la escena 1 abre con una clave de cámara sin `dice` (el cuadro cero)")
        s1 = VD.segundos_voz(x1["voz"])
        if s1 > GANCHO_VOZ_S:
            fallas.append("C3D6 la voz del gancho dura ≈ %.1f s; va ≤ %.0f s" % (s1, GANCHO_VOZ_S))
        t, oido = 0.0, None
        for x in loc:
            for w in estimadas(x["voz"]):
                if oido is None and VD._norm(w["text"]).startswith("guatemal"):
                    oido = t + w["start"]
            t += x["estimado_s"]
        if oido is None or oido > GUATEMALA_S:
            fallas.append("C3D6 «Guatemala» se oye en los primeros %.0f s (hoy: %s)" % (GUATEMALA_S, "nunca" if oido is None else "≈ %.1f s" % oido))
        if not (g1.get("titular") or {}).get("texto"):
            fallas.append("C3D6 el gancho lleva titular: se entiende sin sonido")

    # C3D7 ritmo: algo nuevo entra en pantalla cada pocos segundos
    cambios.sort()
    for (a, qa), (b, qb) in zip(cambios, cambios[1:] + [(t0, "fin")]):
        if b - a > RITMO_S:
            fallas.append("C3D7 ≈ %.0f s sin nada nuevo entre %s y %s (tope %.0f s): añade una clave de cámara, una marca o una cifra"
                          % (b - a, qa, qb, RITMO_S))
        elif b - a > RITMO_AVISO_S:
            avisos.append("C3D7 ≈ %.0f s sin nada nuevo entre %s y %s" % (b - a, qa, qb))

    # C3D8 el cierre: la consecuencia, sin despedirse, corto
    if escenas and escenas[-1].get("tipo") == "cierre":
        c, xc = escenas[-1], loc[-1]
        fin = (c.get("final") or "").strip()
        if not fin:
            fallas.append("C3D8 el cierre lleva `final`: la frase que queda en pantalla")
        elif VD.palabras(fin) > VD.FINAL_PALABRAS or len(fin) > VD.FINAL_CARACTERES:
            fallas.append("C3D8 la frase final tiene más de %d palabras o %d caracteres" % (VD.FINAL_PALABRAS, VD.FINAL_CARACTERES))
        anuncia = VD.anuncia_fin(c.get("texto"))
        if anuncia:
            fallas.append("C3D8 (F9) el cierre anuncia que el video se acabó («%s»)" % anuncia)
        if VD.PROHIBIDO_CIERRE.search(c.get("texto") or ""):
            fallas.append("C3D8 el cierre no nombra fuentes ni dice «sígueme»: eso va en pantalla")
        if len(xc["voz"]) > CIERRE_VOZ:
            fallas.append("C3D8 (F9) la voz del cierre tiene %d caracteres; va ≤ %d" % (len(xc["voz"]), CIERRE_VOZ))
        # C3D10 el bucle: el cierre vuelve a mirar lo que abrió el gancho
        m0 = ((escenas[0].get("camara") or [{}])[0]).get("mira")
        mf = ((c.get("camara") or [{}])[-1]).get("mira")
        if not c.get("camara"):
            fallas.append("C3D10 el cierre lleva su clave de cámara: el último cuadro encuadra al protagonista")
        elif mundo_de_escena(g, escenas[0]) != mundo_de_escena(g, c):
            avisos.append("C3D10 el gancho abre en el mundo «%s» y el cierre está en «%s»: el bucle se nota si el último cuadro vuelve a lo que abrió"
                          % (mundo_de_escena(g, escenas[0]), mundo_de_escena(g, c)))
        elif m0 != mf:
            avisos.append("C3D10 el gancho mira «%s» y el cierre «%s»: si el último cuadro se parece al primero, el bucle no se nota" % (m0, mf))

    # V5 el texto para publicar: un caption por plataforma (sin él, entregar no escribe caption.md)
    fallas += revisar_caption(g)
    # rotación: la familia del gancho elegido no repite la de los últimos videos 3D (aviso, como R9 en /video)
    fam = (g.get("gancho") or {}).get("familia") if isinstance(g.get("gancho"), dict) else None
    if fam and fam in familias_recientes(st):
        avisos.append("G3D2 el gancho es de la familia «%s», la de uno de los últimos %d videos 3D: no se repite (elige otro "
                      "candidato, salvo que el usuario haya elegido este a sabiendas)" % (fam, ROTACION_GANCHOS))

    # C3D9 (V4) duración
    objetivo = st.get("duracion_s") or OBJETIVO_S
    estimado = sum(x["estimado_s"] for x in loc)
    if not objetivo * (1 - TOL) <= estimado <= objetivo * (1 + TOL):
        fallas.append("C3D9 duración estimada %.0f s; el objetivo es %d s (±%d %%)" % (estimado, objetivo, TOL * 100))
    if estimado > DURACION_MAX_S:
        fallas.append("C3D9 duración estimada %.0f s: un video 3D dura a lo más %d s (3 min)" % (estimado, DURACION_MAX_S))
    return fallas, avisos, {"voz": VD.VOZ, "caracteres": sum(len(x["voz"]) for x in loc), "estimado_s": round(estimado, 1),
                            "objetivo_s": objetivo, "n_escenas": len(loc), "voz_continua": bool(secuencias),
                            "secuencias": secuencias, "escenas": loc}


# ---------- maqueta.json: cada `dice` en su segundo ----------
def linea_de_tiempo(trabajo, loc, real):
    """Por escena: desfase global, duración, palabras habladas y fichas de pantalla (con tiempos locales)."""
    out, off, avisos = [], 0.0, []
    for e in loc["escenas"]:
        if real:
            habladas, _, av = VD.voz_de_escena(trabajo, e)
            avisos += av
            dur_voz = VD.ffprobe_dur(os.path.join(trabajo, "audio", "voz_%d_r.mp3" % e["n"]))
        else:
            habladas = estimadas(e["voz"])
            dur_voz = habladas[-1]["end"] if habladas else 0.0
        pantalla = VD.alinear(e, habladas)   # ValueError = V6: lo grabado no es lo escrito
        dur = cuadro(dur_voz + e["cola"])
        out.append({"n": e["n"], "tipo": e["tipo"], "acto": e.get("acto"), "off": cuadro(off), "dur": dur, "habladas": habladas,
                    "pantalla": pantalla, "fin_voz": habladas[-1]["end"] if habladas else 0.0})
        off = cuadro(off) + dur
    return out, cuadro(off), avisos


def en_tramos(maqueta, g, segmentos, total, de_escena):
    """La maqueta de un mundo → la de varios (scripts/maqueta_tramos.py): un tramo por cada racha del mismo mundo (las
    escenas seguidas en él, partidas también donde una escena declara un `cambio` de mundo a mitad de su voz); cada cosa
    va al tramo de su ancla (el segundo en que la voz la dice) y se recorta a él."""
    rachas, mundo_seg = [], []   # mundo_seg: (escena, segundo, mundo) de cada segmento, para repartir lo de cada escena
    for t0, mid, trans, fs, n_e in segmentos:
        mundo_seg.append((n_e, t0, mid))
        if rachas and rachas[-1]["mundo"] == mid:
            continue
        if rachas and t0 - rachas[-1]["t0"] < 1e-3:   # un cambio justo al empezar su escena: manda el cambio
            rachas[-1].update(mundo=mid, trans=trans, fs=fs)
            continue
        rachas.append({"mundo": mid, "t0": t0, "trans": trans, "fs": fs})
    tramos = []
    for i, r in enumerate(rachas):
        a = 0.0 if i == 0 else r["t0"]
        b = total if i == len(rachas) - 1 else rachas[i + 1]["t0"]
        tr = {"id": "%s-%d" % (r["mundo"], i + 1), "mundo": r["mundo"], "desde": cuadro(a), "hasta": cuadro(b),
              "camara": [], "eventos": [], "marcas": [], "anotaciones": [], "_t0": a}   # _t0: sin redondear al cuadro
        if i > 0:
            tr["transicion"] = r["trans"] or "fundido"
            if r["fs"] is not None:
                tr["fundido_s"] = r["fs"]
        tramos.append(tr)

    def tramo_de(ancla):
        # el mundo de una cosa: entre los segmentos de SU escena, el último que ya empezó en su ancla (lo anclado a la frase
        # de un cambio va al mundo nuevo; la clave `al: fin` de una escena se queda en su mundo aunque caiga en el borde)
        n_e, t = ancla
        suyos = [(t0, mid) for n2, t0, mid in mundo_seg if n2 == n_e]
        mid = ([m for t0, m in suyos if t + 1e-6 >= t0] or [suyos[0][1]])[-1]
        cand = [i for i, tr in enumerate(tramos) if tr["mundo"] == mid and tr["_t0"] <= t + 1e-6]
        return cand[-1] if cand else next(i for i, tr in enumerate(tramos) if tr["mundo"] == mid)
    for clave, lista in (("camara", maqueta["camara"]), ("eventos", maqueta["eventos"]), ("marcas", maqueta["marcas"]),
                         ("anotaciones", maqueta.get("anotaciones") or [])):
        for o in lista:
            tr = tramos[tramo_de(de_escena[id(o)])]
            o = dict(o, t=cuadro(min(max(o["t"], tr["desde"]), tr["hasta"])))
            if clave == "eventos":
                o["dur"] = round(max(0.1, min(o["dur"], tr["hasta"] - o["t"])), 3)
            elif "hasta" in o:
                o["hasta"] = cuadro(min(o["hasta"], tr["hasta"]))
            tr[clave].append(o)
    for tr in tramos:
        tr.pop("_t0", None)
        tr["camara"].sort(key=lambda c: c["t"])
        if tr["camara"] and tr["camara"][0]["t"] > tr["desde"]:   # el tramo abre en su primera clave
            tr["camara"].insert(0, dict(tr["camara"][0], t=tr["desde"]))
        tr["eventos"].sort(key=lambda v: v["t"])
        for k in ("marcas", "anotaciones"):
            if not tr[k]:
                tr.pop(k)
    out = {k: v for k, v in maqueta.items() if k not in ("mundo", "camara", "eventos", "marcas", "anotaciones")}
    out["mundos"] = mundos_de(g)
    out["tramos"] = tramos
    if out.get("protagonista") and not any(out["protagonista"] in {p.get("id") for p in m.get("piezas") or []} for m in out["mundos"].values()):
        out.pop("protagonista")
    return out


def construir(trabajo, g, loc, real, solo_escenas=None):
    """maqueta.json (referencias/diseno/maqueta3d.md) desde el guion y la línea de tiempo."""
    st = estado(trabajo)
    tl, total, avisos = linea_de_tiempo(trabajo, loc, real)
    por_n = {x["n"]: x for x in tl}
    escenas = [e for e in escenas_de(g) if not solo_escenas or e["n"] in solo_escenas]

    def momento(x, o, clave="dice", al=None):
        # `al: "fin"`: al terminar la frase (o, sin `dice`, al terminar la voz de la escena): una clave de cámara así
        # hace que el vuelo dure toda la escena y LLEGUE a ese encuadre al final
        al = al or (o.get("al") if clave == "dice" else None) or "inicio"
        if not o.get(clave):
            return (x["off"] + (x["fin_voz"] if al == "fin" else 0.0)) if clave == "dice" else None
        pos = buscar(x["habladas"], o[clave], o.get("vez", 1) if clave == "dice" else 1)
        if not pos:
            raise ValueError("escena %d: la voz no dice «%s»" % (x["n"], o[clave]))
        return x["off"] + (x["habladas"][pos[0]]["start"] if al == "inicio" else x["habladas"][pos[1]]["end"])

    def fin_de(x, o):
        if o.get("hasta_dice"):
            return momento(x, o, "hasta_dice", "fin") + 0.4
        if isinstance(o.get("dura"), (int, float)):
            return None
        hasta = por_n.get(o["hasta"]) if isinstance(o.get("hasta"), int) else x
        return (hasta or x)["off"] + (hasta or x)["dur"]

    camara, eventos, marcas, cifras, titulares, anotaciones = [], [], [], [], [], []
    de_escena = {}   # id(objeto) → segundo de su ancla (para repartir cámara, eventos, marcas y anotaciones en tramos)
    anclas = []      # el segundo del ancla de cada cosa, en el orden en que entra (lo usa en_tramos)
    segmentos = []   # (segundo, mundo, transicion, fundido_s): dónde empieza cada mundo (la escena, o un `cambio` a mitad de ella)
    for e in escenas:
        x = por_n[e["n"]]
        segmentos.append((x["off"], mundo_de_escena(g, e), e.get("transicion"), e.get("fundido_s"), e["n"]))
        for cb in e.get("cambios") or []:   # CAMBIO DE MUNDO a mitad de la escena, anclado a una frase de su voz
            segmentos.append((momento(x, cb), cb.get("mundo"), cb.get("transicion"), cb.get("fundido_s"), e["n"]))
        antes = {k: len(v) for k, v in (("c", camara), ("e", eventos), ("m", marcas), ("a", anotaciones))}
        anclas_e = []
        for c in e.get("camara") or []:
            camara.append(dict({k: v for k, v in c.items() if k not in ("dice", "vez", "al")}, t=cuadro(momento(x, c))))
            anclas_e.append(("c", momento(x, c)))
        for ev in e.get("eventos") or []:
            anclas_e.append(("e", momento(x, ev)))
            t = max(0.0, momento(x, ev) - float(ev.get("adelanto", 0.0)))
            dur = ev["dur"] if isinstance(ev.get("dur"), (int, float)) else momento(x, ev, "hasta_dice", "fin") - t
            eventos.append(dict({k: v for k, v in ev.items() if k not in ("dice", "vez", "al", "hasta_dice", "adelanto")}, t=cuadro(t), dur=round(dur, 3)))
        for clase, lista, dst in (("marca", e.get("marcas") or [], marcas), ("cifra", e.get("cifras") or [], cifras),
                                  ("anotacion", e.get("anotaciones") or [], anotaciones)):
            for o in lista:
                if clase != "cifra":
                    anclas_e.append(({"marca": "m", "anotacion": "a"}[clase], momento(x, o)))
                t = max(x["off"], momento(x, o) - ADELANTO)
                fin = fin_de(x, o)
                fin = t + o["dura"] if fin is None else fin
                dst.append(dict({k: v for k, v in o.items() if k not in ("dice", "vez", "al", "hasta_dice", "hasta", "dura", "cifra")},
                                t=cuadro(t), hasta=cuadro(min(fin, total))))
        for k, v in (("c", camara), ("e", eventos), ("m", marcas), ("a", anotaciones)):
            ts = [t for kk, t in anclas_e if kk == k]
            for o, ta in zip(v[antes[k]:], ts):
                de_escena[id(o)] = (e["n"], ta)
        if e.get("titular"):
            ti = e["titular"]
            t = max(x["off"], momento(x, ti) - (ADELANTO if ti.get("dice") else 0.0))
            fin = fin_de(x, ti)
            titulares.append({"t": cuadro(t), "kicker": ti.get("kicker", ""), "texto": ti["texto"],
                              "hasta": t + ti["dura"] if fin is None else fin})
    camara.sort(key=lambda c: c["t"])
    cierre_x = next((x for x in tl if x["tipo"] == "cierre"), None)
    fin_titulares = cierre_x["off"] if cierre_x else total
    # un titular vive lo que su escena (o `hasta: N` / `dura`), nunca pisa al siguiente ni llega al cierre
    for a, b in zip(titulares, titulares[1:] + [None]):
        a["hasta"] = cuadro(min(a["hasta"], b["t"] if b else fin_titulares, fin_titulares))
    # «Sígueme» a mitad: el hueco sin titular largo más cercano al 50 % (en 9:16 el botón va a la altura del titular)
    def libre(t):
        return not any(len(ti["texto"]) > 14 and min(ti["hasta"], t + SEGUIR_S) - max(ti["t"], t) > 0 for ti in titulares)
    candidatos = [total * (0.25 + 0.01 * k) for k in range(51)]
    t_seguir = min([t for t in candidatos if libre(t) and t + SEGUIR_S <= fin_titulares] or [total * 0.5], key=lambda t: abs(t - total * 0.5))
    palabras = [{"text": w["text"], "start": round(x["off"] + w["start"], 3), "end": round(x["off"] + w["end"], 3)}
                for x in tl for w in x["pantalla"]]
    actos, visto = [], set()
    for x in tl:
        if x.get("acto") not in visto:
            visto.add(x.get("acto"))
            actos.append(x["off"])
    MUNDOS = mundos_de(g)
    mundo = MUNDOS.get("principal") or next(iter(MUNDOS.values()))
    # el pie nombra SOLO las fuentes de lo que el video dibuja (m256): por set, las capas de todos sus mundos
    hay_marcas = any(e.get("marcas") for e in escenas_de(g))
    por_set = {}
    for v in MUNDOS.values():
        if (v.get("escala") or "pais") != "esquema" and v.get("set"):
            por_set.setdefault(v["set"], set()).update(M3.capas_usadas(v, v.get("escala") or "pais", hay_marcas))
            por_set[v["set"]].update(p_.get("tipo") for p_ in v.get("piezas") or [])   # una pieza que se llama como su capa (frontera, fallas…)
    pies = list(dict.fromkeys(p for p in (pie_de_capas(s_, u) for s_, u in por_set.items()) if p))
    if len(" · ".join(pies)) > 132:
        pies = [p.replace("Mapzen Terrain Tiles", "Mapzen") for p in pies]
    capa = {"titulares": titulares, "cifras": cifras, "palabras": palabras, "progreso": {"actos": actos},
            "seguir": {"t": cuadro(t_seguir), "dur": SEGUIR_S},
            "pie": g.get("pie") or " · ".join(pies), "handle": HANDLE}
    if (g.get("aviso") or "").strip():   # «Maqueta · no a escala», «Traza esquemática»…: solo cuando el guion lo pide
        capa["aviso"] = g["aviso"].strip()
    elif any(v.get("escala") == "esquema" for v in MUNDOS.values()):   # M3D12: un esquema no es un lugar real
        capa["aviso"] = "Esquema · no es un lugar real"
    if cierre_x:
        ce = next(e for e in escenas_de(g) if e.get("tipo") == "cierre")
        capa["cierre"] = {"t": cuadro(cierre_x["off"] + min(cierre_x["fin_voz"] * 0.35, 1.2)), "frase": ce.get("final", ""),
                          "redes": [{"nombre": r["nombre"], "handle": r["handle"]} for r in VD.REDES]}
    maqueta = {"version": 1, "video": True, "estilo": (g.get("estilo") or {}).get("id"), "paleta": st.get("paleta"), "fps": FPS,
               "duracion_s": total, "protagonista": g.get("protagonista"), "mundo": mundo, "camara": camara,
               "eventos": sorted(eventos, key=lambda v: v["t"]), "marcas": marcas, "capa": capa}
    if anotaciones:
        maqueta["anotaciones"] = anotaciones
    if isinstance(g.get("mundos"), dict):   # varios mundos: las escenas seguidas del mismo mundo forman un TRAMO
        maqueta = en_tramos(maqueta, g, segmentos, total, de_escena)
    tiempos = {"real": real, "total_s": total,
               "escenas": [{"n": x["n"], "off": x["off"], "dur": x["dur"], "fin_voz": round(x["fin_voz"], 3)} for x in tl]}
    return maqueta, tiempos, avisos


def revisar_maqueta(ruta, formato="ambos"):
    if not os.path.exists(MAQUETA3D):
        print("AVISO: falta scripts/maqueta3d.py; no se corrieron los gates M3D")
        return 0
    return subprocess.call([sys.executable, MAQUETA3D, "check", ruta, "--formato", formato])


# ---------- comandos ----------
def cmd_preparar(a):
    if not DURACION_MIN_S <= a.duracion <= DURACION_MAX_S:
        print("ERROR: --duracion %d: un video 3D dura de %d a %d s (3 min)" % (a.duracion, DURACION_MIN_S, DURACION_MAX_S), file=sys.stderr)
        return 2
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "video3d-" + a.slug))
    os.makedirs(os.path.join(trabajo, "base"), exist_ok=True)
    os.makedirs(os.path.join(trabajo, "audio"), exist_ok=True)
    datos = os.path.join(trabajo, "base", "datos.json")
    if a.desde:
        origen = next((p for p in (os.path.join(a.desde, "base", "datos.json"), os.path.join(a.desde, "datos.json")) if os.path.exists(p)), None)
        if not origen:
            return falla("«%s» no tiene base/datos.json ni datos.json" % a.desde)
        shutil.copyfile(origen, datos)
    elif not os.path.exists(datos):
        escribir(datos, {"slug": a.slug, "fecha": datetime.date.today().isoformat(), "cifras": []})
    pista = VD.elegir_musica_tema(a.musica_tema, a.slug) if a.musica_tema else None
    if a.musica_tema and not pista:
        return falla("no hay música del tema «%s» (%s)" % (a.musica_tema, ", ".join(VD.MUSICA_TEMAS)))
    paletas = leer(os.path.join(RAIZ, "design", "tokens.json"))["noche"]["paletas"]
    paleta = a.paleta or (pista or {}).get("paleta")
    if paleta not in paletas:
        return falla("paleta «%s» no existe (%s)" % (paleta, ", ".join(paletas)))
    escribir(os.path.join(trabajo, "video3d.json"), {
        "tipo": "video3d", "slug": a.slug, "tema": a.tema, "fecha": datetime.date.today().isoformat(), "paleta": paleta,
        "musica": (pista or VD.elegir_musica(paleta, None))["id"], "musica_tema": a.musica_tema, "duracion_s": a.duracion,
        "desde": rel(os.path.abspath(a.desde)) if a.desde else None, "estado": "preparado"})
    print("TRABAJO %s · paleta %s · música %s · objetivo %d s" % (rel(trabajo), paleta, estado(trabajo)["musica"], a.duracion))
    print(rel(trabajo))
    return 0


def cmd_datos(a):
    trabajo = os.path.abspath(a.trabajo)
    ruta = os.path.join(trabajo, "base", "datos.json")
    datos, nuevo = leer(ruta), leer(a.sumar)
    ids, n = {c["id"] for c in datos["cifras"]}, 0
    for c in nuevo.get("cifras") or []:
        if c.get("veredicto") not in ("verificada", "ajustada") or c["id"] in ids:
            continue
        if not (c.get("url") and c.get("cita")):
            print("AVISO: %s sin url o cita: no entra" % c["id"])
            continue
        datos["cifras"].append(c)
        n += 1
    escribir(ruta, datos)
    print("%d cifra(s) añadidas a %s (%d en total)" % (n, rel(ruta), len(datos["cifras"])))
    return 0


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    _, por_id = cifras_ok(trabajo)
    print("# /video-3d · %s\n\nTema: %s · objetivo %d s (≈ %d caracteres de voz) · paleta %s · música %s\n"
          % (st["slug"], st["tema"], st["duracion_s"], st["duracion_s"] * VD.CPS, st["paleta"], st["musica"]))
    print("## Cifras verificadas (solo estas respaldan un número)\n")
    for c in por_id.values():
        print("- `%s` · %s %s · %s%s" % (c["id"], c.get("valor_final", c.get("valor")), c.get("unidad", ""), c.get("concepto", ""),
                                       " · UNA FUENTE: lleva la fuente en pantalla" if c.get("una_fuente") else ""))
    if os.path.exists(ESTILOS):
        print("\n## Estilos (uno solo por video)\n")
        for e in leer(ESTILOS)["estilos"]:
            print("- `%s` (%s): %s" % (e["id"], e.get("motor"), e.get("cuando", "")))
    sets = os.path.join(RAIZ, "design", "sets3d")
    for s in sorted(d for d in os.listdir(sets) if os.path.isdir(os.path.join(sets, d))) if os.path.isdir(sets) else []:
        lug = lugares_del_set(s)
        print("\n## Set `%s`: %d lugares\n\n%s" % (s, len(lug), ", ".join("`%s` (%s)" % (k, v.get("nombre")) for k, v in sorted(lug.items()))))
    hechos = [v for v in hechos_3d() if v.get("slug") != st["slug"]]
    bloqueadas = familias_recientes(st)
    if hechos:
        print("\n## Videos 3D ya hechos (rota la familia del gancho; el estilo se elige por la idea visual, no por costumbre)\n")
        for v in hechos[-5:]:
            fam = (v.get("gancho") or {}).get("familia")
            print("- %s · %s · estilo `%s` · gancho `%s`%s: «%s»" % (v["fecha"], v["slug"], v.get("estilo"), fam,
                                                                " (NO REPETIR)" if fam in bloqueadas and v in hechos[-ROTACION_GANCHOS:] else "",
                                                                (v.get("gancho") or {}).get("texto", "")))
    print("\n## Rotación del gancho\n\n- Familias bloqueadas (las de los últimos %d videos 3D; `ganchos --check` y `guion --check` avisan "
          "si se repiten): %s" % (ROTACION_GANCHOS, ", ".join("`%s`" % f for f in dict.fromkeys(bloqueadas)) or
                                 ("ninguna (prueba: sin rotación)" if st.get("fixture") else "ninguna")))
    # lo medido con /analyze-improve: las familias y visuales son las de los demás flujos (referencia: qué retiene en esta
    # cuenta); las de los ganchos 3D aparecerán aquí cuando haya videos 3D publicados y medidos
    print("\n## Rendimiento real (TikTok, YouTube; /analyze-improve)\n")
    print("\n".join(VD.lineas_rendimiento_real(("familia", "visual", "cierre", "duracion"))))
    print("\n" + "\n".join(M3.lineas_catalogo("sesion")) + "\n\nContrato de la maqueta: referencias/diseno/maqueta3d.md · reglas del guion: referencias/flujo-video3d.md"
          "\n\n`caption` (obligatorio, V5): tiktok, instagram, facebook y shorts (título ≤ %d caracteres en la primera línea + #Shorts); "
          "las cifras en dígitos, sin anunciar el video." % VD.SHORTS_TITULO)
    return 0


def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    g, st = leer(os.path.join(trabajo, "guion.json")), estado(trabajo)
    fallas, avisos, loc = revisar_guion(g, st, trabajo)
    if isinstance(loc, dict):
        print("escenas %d · voz %d caracteres · estimado %.0f s (objetivo %d s)" % (loc["n_escenas"], loc["caracteres"], loc["estimado_s"], loc["objetivo_s"]))
        for x in loc["escenas"]:
            print("E%-2d %-7s %5.1fs  %s" % (x["n"], x["tipo"], x["estimado_s"], x["voz"]))
    for x in avisos:
        print("AVISO", x)
    if fallas:
        for f in fallas:
            print("FALLA", f)
        return 1
    escribir(os.path.join(trabajo, "locucion.json"), loc)
    try:
        maqueta, tiempos, _ = construir(trabajo, g, loc, real=False)
    except ValueError as ex:
        return falla("C3D2 %s" % ex)
    ruta = os.path.join(trabajo, "maqueta.json")
    escribir(ruta, maqueta)
    escribir(os.path.join(trabajo, "tiempos.json"), tiempos)
    print("→ %s y %s (tiempos estimados) · C3D1–C3D11, V2–V5 ok" % (rel(os.path.join(trabajo, "locucion.json")), rel(ruta)))
    return revisar_maqueta(ruta)


def tiempos_clave(maqueta):
    """Los segundos que vale la pena mirar: cada clave de cámara, la mitad de cada evento y el cierre."""
    T = maqueta.get("tramos") or [maqueta]   # con varios mundos, lo de cada tramo (y el inicio de cada uno)
    ts = [c["t"] for tr in T for c in tr.get("camara") or []] + [e["t"] + e["dur"] * 0.6 for tr in T for e in tr.get("eventos") or []]
    ts += [m["t"] + 0.6 for tr in T for m in tr.get("marcas") or []] + [tr["desde"] + 0.4 for tr in maqueta.get("tramos") or []]
    if maqueta["capa"].get("cierre"):
        ts.append(min(maqueta["duracion_s"] - 0.2, maqueta["capa"]["cierre"]["t"] + 1.5))
    out = []
    for t in sorted(min(max(0.0, t), maqueta["duracion_s"] - 0.05) for t in ts):
        if not out or t - out[-1] >= 0.8:
            out.append(round(t, 2))
    # un fundido se mira cerca de la mitad de su cruce (se ven los dos mundos); un corte o un paso por negro no tienen qué mostrar
    cruces = [round(tr["desde"] - 0.08 * float(tr.get("fundido_s", 0.5)), 2) for tr in (maqueta.get("tramos") or [])[1:]
              if tr.get("transicion", "fundido") == "fundido"]
    return sorted(set(out + cruces))


def cuadros(ruta_maqueta, tiempos, salida, formato="9:16", hoja=True):
    cmd = [sys.executable, MAQUETA3D, "cuadro", ruta_maqueta, "--salida", salida, "--formato", formato] + (["--hoja"] if hoja else [])
    for t in tiempos:
        cmd += ["--t", "%.2f" % t]
    return subprocess.call(cmd)


def cmd_storyboard(a):
    trabajo = os.path.abspath(a.trabajo)
    ruta = os.path.join(trabajo, "maqueta.json")
    if not os.path.exists(ruta):
        return falla("falta maqueta.json: corre guion --check primero")
    maqueta = leer(ruta)
    # se limpia antes de escribir: los cuadros de una versión anterior del guion no se mezclan con los de esta
    for nombre in ("storyboard", "escenas"):
        shutil.rmtree(os.path.join(trabajo, nombre), ignore_errors=True)
    rc = cuadros(ruta, tiempos_clave(maqueta), os.path.join(trabajo, "storyboard"), a.formato)
    if rc == 0 and maqueta.get("tramos") and not getattr(a, "sin_escenas", False):
        # una hoja por mundo (6 cuadros de cada tramo) y su medida: lo que miran el director, el crítico y el usuario
        subprocess.call([sys.executable, MAQUETA3D, "escena", ruta, "--formato", a.formato, "--hoja", "--salida", os.path.join(trabajo, "escenas")])
    return rc


def cmd_ganchos(a):
    """ganchos.json: {estilo, idea_visual, protagonista, mundo, candidatos: [{id, familia, porque, escena}]} donde
    `escena` es la escena 1 completa (texto, titular, camara, eventos, marcas, cifras)."""
    trabajo = os.path.abspath(a.trabajo)
    ruta = os.path.join(trabajo, "ganchos.json")
    G, st = leer(ruta), estado(trabajo)
    cands = G.get("candidatos") or []
    bloqueadas = familias_recientes(st)
    cierre = {"n": 2, "tipo": "cierre", "texto": "Y esto sigue ahí.", "final": "Esto sigue ahí.",
              "camara": [dict((c.get("escena", {}).get("camara") or [{}])[0]) for c in cands[:1]] or [{}]}
    if a.usar:
        c = next((x for x in cands if x["id"] == a.usar), None)
        if not c:
            return falla("no hay candidato «%s» (%s)" % (a.usar, ", ".join(x["id"] for x in cands)))
        rg = os.path.join(trabajo, "guion.json")
        g = leer(rg) if os.path.exists(rg) else {"tipo": "video3d", "version": 1, "escenas": []}
        for k in ("estilo", "idea_visual", "protagonista", "mundo", "mundos", "pie", "aviso"):
            if G.get(k) is not None:
                g.setdefault(k, G[k])
        esc = dict(c["escena"], n=1, tipo="gancho")
        g["gancho"] = {"id": c["id"], "familia": c.get("familia"), "elegido_por": a.por}
        g["escenas"] = [esc] + [e for e in g.get("escenas") or [] if e.get("n") != 1 and e.get("tipo") != "gancho"]
        escribir(rg, g)
        print("gancho %s → escena 1 de %s" % (c["id"], rel(rg)))
        if c.get("familia") in bloqueadas:
            print("AVISO G3D2 el gancho elegido es de la familia «%s», la de uno de los últimos %d videos 3D: no se repite"
                  % (c["familia"], ROTACION_GANCHOS))
        return 0
    fallas = []
    for c in cands:   # rotación: se avisa aquí, antes de que el usuario elija
        if c.get("familia") in bloqueadas:
            print("AVISO G3D2 %s · familia «%s»: es la de uno de los últimos %d videos 3D (no repetir)" % (c.get("id"), c["familia"], ROTACION_GANCHOS))
    if not 4 <= len(cands) <= 6:
        fallas.append("G3D1 %d candidatos; van 4–6 (5 es lo normal)" % len(cands))
    fam = [c.get("familia") for c in cands]
    if len(set(fam)) < min(len(fam), 4):
        fallas.append("G3D1 los candidatos son de familias distintas (hoy: %s)" % ", ".join(map(str, fam)))
    rc = 0
    for c in cands:
        g = {"estilo": G.get("estilo"), "idea_visual": G.get("idea_visual"), "protagonista": G.get("protagonista"),
             "mundo": G.get("mundo"), "pie": G.get("pie"), "aviso": G.get("aviso"), "escenas": [dict(c["escena"], n=1, tipo="gancho", acto=1), dict(cierre, acto=1)]}
        if isinstance(G.get("mundos"), dict):   # varios mundos: el candidato abre en el suyo (y el cierre de prueba, ahí mismo)
            mid = c["escena"].get("mundo") or next(iter(G["mundos"]))
            g = dict(g, mundos={mid: G["mundos"].get(mid) or {}}, mundo=None)
            g["escenas"][1]["mundo"] = mid
            g.pop("mundo")
        f, _, loc = revisar_guion(g, dict(st, duracion_s=0), trabajo)
        f = [x for x in f if not x.startswith(("C3D1 %d escenas" % 2, "C3D9", "C3D7", "V5 "))]   # el caption es del guion entero
        for x in f:
            fallas.append("%s · %s" % (c["id"], x))
        if (a.cuadros or a.clips) and not f and isinstance(loc, dict):
            maqueta, _, _ = construir(trabajo, g, loc, real=False)
            if maqueta.get("tramos"):   # un candidato abre en UN mundo: su maqueta es la de ese mundo, sin tramos
                tr = maqueta.pop("tramos")[0]
                maqueta["mundo"] = maqueta.pop("mundos")[tr["mundo"]]
                maqueta.update({k: tr.get(k) or [] for k in ("camara", "eventos", "marcas", "anotaciones")})
                maqueta["protagonista"] = maqueta["mundo"].pop("protagonista", maqueta.get("protagonista"))
                maqueta["mundo"] = {k: v for k, v in maqueta["mundo"].items()}
            carpeta = os.path.join(trabajo, "ganchos", c["id"])
            rm = os.path.join(carpeta, "maqueta.json")
            fin = loc["escenas"][0]["estimado_s"]
            # la maqueta de una sola escena: sin «Sígueme» ni cierre, y solo lo que dura el gancho
            for k in ("seguir", "cierre"):
                maqueta["capa"].pop(k, None)
            maqueta["duracion_s"] = cuadro(fin + 0.6)
            maqueta["camara"] = [k for k in maqueta["camara"] if k["t"] <= fin + 0.01]
            maqueta["capa"]["palabras"] = [w for w in maqueta["capa"]["palabras"] if w["start"] < fin]
            for lista in (maqueta["marcas"], maqueta["capa"]["cifras"], maqueta["capa"]["titulares"]):
                for o in lista:
                    o["hasta"] = min(o["hasta"], maqueta["duracion_s"])
            escribir(rm, maqueta)
            if a.clips:   # el gancho en movimiento, sin voz y con los tiempos estimados
                rc_c = subprocess.call([sys.executable, MAQUETA3D, "render", rm, "--dir", os.path.join(carpeta, "render"),
                                        "--formato", a.formato, "--borrador"])
                if not rc_c:
                    shutil.copyfile(os.path.join(carpeta, "render", FORMATOS[a.formato][0], "video.mp4"), os.path.join(carpeta, "gancho.mp4"))
                rc |= rc_c
            if a.cuadros:
                ts = sorted({0.0, round(min(1.0, fin), 2), round(fin * 0.5, 2), round(max(0.0, fin - 0.3), 2)})
                rc |= cuadros(rm, ts, carpeta, a.formato)
    for x in fallas:
        print("FALLA", x)
    if not fallas:
        print("%d candidatos ok%s" % (len(cands), " · cuadros y clips en %s" % rel(os.path.join(trabajo, "ganchos")) if a.cuadros or a.clips else ""))
    return 1 if fallas or rc else 0


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    g, loc = leer(os.path.join(trabajo, "guion.json")), leer(os.path.join(trabajo, "locucion.json"))
    VD.V20_FALLAS.clear()
    try:
        maqueta, tiempos, avisos = construir(trabajo, g, loc, real=True)
    except ValueError as ex:
        return falla("V6 %s · rehaz la voz de esa escena (video3d.py voz %s --sueltas N)" % (ex, rel(trabajo)))
    ruta = os.path.join(trabajo, "maqueta.json")
    escribir(ruta, maqueta)
    escribir(os.path.join(trabajo, "tiempos.json"), tiempos)
    for x in avisos:
        print("AVISO", x)
    for x in VD.V20_FALLAS:
        print("FALLA", x)
    objetivo = estado(trabajo).get("duracion_s") or OBJETIVO_S
    print("voz real: %.1f s (objetivo %d s) → %s" % (tiempos["total_s"], objetivo, rel(ruta)))
    if tiempos["total_s"] > DURACION_MAX_S + 0.5:
        print("FALLA C3D9 la voz real dura %.1f s: un video 3D dura a lo más %d s (3 min); acorta la narración y regraba esas escenas"
              % (tiempos["total_s"], DURACION_MAX_S))
        return 1
    rc = revisar_maqueta(ruta)
    return 1 if VD.V20_FALLAS or rc else 0


FORMATOS = {"9:16": ("9x16", "video.mp4", (1080, 1920)), "4:5": ("4x5", "video_4x5.mp4", (1080, 1350))}


def formatos(a):
    return list(FORMATOS) if a.formato == "ambos" else [a.formato]


def cmd_render(a):
    trabajo = os.path.abspath(a.trabajo)
    ruta = os.path.join(trabajo, "maqueta.json")
    if not leer(os.path.join(trabajo, "tiempos.json")).get("real") and not a.estimado:
        return falla("maqueta.json tiene tiempos estimados: corre tiempos tras la voz (o render --estimado para una prueba)")
    for f in formatos(a):
        rc = subprocess.call([sys.executable, MAQUETA3D, "render", ruta, "--dir", os.path.join(trabajo, "render3d"), "--formato", f])
        if rc:
            return rc
    return 0


def escenas_srt(maqueta, T):
    """La entrada de video.texto_srt (el .srt de todos los flujos: por oración, 2 líneas de ≤ 42 caracteres, sin solapes):
    las fichas de pantalla de `capa.palabras` (segundos del video) repartidas por escena con los cortes de tiempos.json y
    devueltas a segundos de su escena. → (escenas [{n, palabras}], desfases)."""
    cortes = [(e["n"], float(e["off"])) for e in T["escenas"]]
    escenas = [{"n": n, "palabras": []} for n, _ in cortes]
    k = 0
    for w in maqueta["capa"].get("palabras") or []:
        while k + 1 < len(cortes) and w["start"] >= cortes[k + 1][1] - 0.002:   # las palabras van a 3 decimales; el corte, a 4
            k += 1
        off = cortes[k][1] if cortes else 0.0
        escenas[k]["palabras"].append({"text": w["text"], "start": round(max(0.0, w["start"] - off), 3), "end": round(max(0.0, w["end"] - off), 3)})
    return escenas, [off for _, off in cortes]


def efectos_de(trabajo, maqueta):
    """[(segundo, id)] de los efectos del video: los que el render dejó en render3d/efectos.json o, sin render, los `sfx`
    de los eventos de la maqueta."""
    fe = os.path.join(trabajo, "render3d", "efectos.json")
    return [(t, i) for t, i in (leer(fe) if os.path.exists(fe) else M3.efectos_de(maqueta))]


def portada(trabajo):
    """salida/portada.png: el cuadro cero del video en 9:16 (por contrato ya trae el titular y el evento del gancho,
    M3D9), sin subtítulos, dibujado por el motor (`maqueta3d.py cuadro`): el mismo archivo que entregan los demás flujos
    y el que caption.md pide como miniatura. → 0 ok."""
    carpeta = os.path.join(trabajo, "portada")
    maqueta = leer(os.path.join(trabajo, "maqueta.json"))
    maqueta["capa"] = dict(maqueta["capa"], palabras=[])   # la portada va limpia: sin el subtítulo de la primera palabra
    rm = os.path.join(carpeta, "maqueta.json")
    escribir(rm, maqueta)
    if cuadros(rm, [0.0], carpeta, "9:16", hoja=False):
        return falla("la portada no se dibujó (maqueta3d.py cuadro --t 0)")
    png = os.path.join(carpeta, "%s_t%07.3f.png" % (FORMATOS["9:16"][0], 0.0))
    if not os.path.exists(png):
        return falla("la portada no se dibujó: falta %s" % rel(png))
    dst = os.path.join(trabajo, "salida", "portada.png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(png, dst)
    print("portada: el cuadro cero en 9:16, sin subtítulos → %s" % rel(dst))
    return 0


def cmd_portada(a):
    return portada(os.path.abspath(a.trabajo))


def cmd_montar(a):
    """La pista: la voz en su segundo, la música del tema con ducking y los efectos de la maqueta, a −14 LUFS (V8). La
    mezcla es la de los videos de mesa (youtube.mezclar_voz + youtube.pista_final: mismos fundidos, las tres tomas de cada
    efecto y el limitador) y el .srt, el de video.texto_srt."""
    import youtube as YT
    trabajo = os.path.abspath(a.trabajo)
    st, T = estado(trabajo), leer(os.path.join(trabajo, "tiempos.json"))
    maqueta = leer(os.path.join(trabajo, "maqueta.json"))
    segs, sal = os.path.join(trabajo, "segs"), os.path.join(trabajo, "salida")
    os.makedirs(segs, exist_ok=True)
    os.makedirs(sal, exist_ok=True)
    fallas = []
    maestro = os.path.join(segs, "mezcla_final.wav")
    for f in formatos(a):
        carpeta, nombre, lados = FORMATOS[f]
        mudo = os.path.join(trabajo, "render3d", carpeta, "video.mp4")
        if not os.path.exists(mudo):
            return falla("falta %s: corre render --formato %s" % (rel(mudo), f))
        D = VD.ffprobe_dur(mudo)
        if abs(D - T["total_s"]) > 2.0 / FPS + 0.01:
            fallas.append("V8 %s dura %.2f s y la voz %.2f s: vuelve a renderizar tras tiempos" % (f, D, T["total_s"]))
        if not os.path.exists(maestro) or f == "9:16":
            # 1. la voz, cada escena en su segundo
            voz = YT.mezclar_voz(trabajo, {"escenas": [{"n": e["n"]} for e in T["escenas"]]}, [e["off"] for e in T["escenas"]], D, segs)
            # 2. música del tema, en bucle
            pista = next(p for p in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"] if p["id"] == st["musica"])
            fondo = os.path.join(segs, "musica.wav")
            VD.musica_bucle(os.path.join(RAIZ, "design", "musica", pista["archivo"]), D, fondo)
            # 3. los efectos que la maqueta declara en sus eventos y 4. la mezcla con ducking a −14 LUFS (dos pasadas de
            #    loudnorm; limitador si el pico se pasa) → segs/mezcla_final.wav
            maestro, _, n_efectos = YT.pista_final(voz, fondo, efectos_de(trabajo, maqueta), D, segs)
            print("audio: %d voces · música %s · %d efectos" % (len(T["escenas"]), st["musica"], n_efectos))
        video = os.path.join(sal, nombre)
        VD.ff("-i", mudo, "-i", maestro, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
              "-shortest", "-movflags", "+faststart", video)
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", video],
                                       capture_output=True, text=True).stdout)["streams"]
        v = next((s for s in pr if s["codec_type"] == "video"), {})
        if (v.get("width"), v.get("height")) != lados:
            fallas.append("V8 %s mide %sx%s (se espera %d×%d)" % (f, v.get("width"), v.get("height"), *lados))
        mf = VD.medir(video)
        if abs(mf["input_i"] - VD.LUFS) > VD.LUFS_TOL or mf["input_tp"] > VD.TP_MAX:
            fallas.append("V8 %s sonoridad %.1f LUFS / %.1f dBTP (se espera %.0f ±%.1f, ≤ %.0f)" % (f, mf["input_i"], mf["input_tp"], VD.LUFS, VD.LUFS_TOL, VD.TP_MAX))
        print("video %s %.1f s · %.1f LUFS · %.1f dBTP → %s" % (f, VD.ffprobe_dur(video), mf["input_i"], mf["input_tp"], rel(video)))
    with open(os.path.join(sal, "subtitulos.srt"), "w", encoding="utf-8") as fh:
        fh.write(VD.texto_srt(*escenas_srt(maqueta, T)))
    if "9:16" in formatos(a) and not a.sin_portada and portada(trabajo):
        fallas.append("la portada (salida/portada.png) no se dibujó: video3d.py portada %s" % rel(trabajo))
    for x in fallas:
        print("FALLA", x)
    return 1 if fallas else 0


def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st, g = estado(trabajo), leer(os.path.join(trabajo, "guion.json"))
    sal = os.path.join(trabajo, "salida")
    if not os.path.exists(os.path.join(sal, "video.mp4")):
        return falla("falta salida/video.mp4: corre montar")
    if not leer(os.path.join(trabajo, "tiempos.json")).get("real"):
        return falla("el video se montó con tiempos estimados: corre tiempos, render y montar con la voz real")
    cred = os.path.join(trabajo, "audio", "creditos.json")
    if not (os.path.exists(cred) and leer(cred).get("total")) and not a.salida:
        return falla("sin créditos de voz (voz falsa): una maqueta de prueba no se entrega; para verla usa --salida DIR")
    # un video sale en 9:16 y 4:5, con su caption por plataforma y su portada: lo que falte es una falla, no un hueco
    faltan = revisar_caption(g)
    if not os.path.exists(os.path.join(sal, "video_4x5.mp4")) and not a.sin_4x5:
        faltan.append("falta salida/video_4x5.mp4 (el 4:5 del feed): corre render y montar con --formato 4:5 (o entrega solo el "
                      "9:16 con --sin-4x5)")
    if not os.path.exists(os.path.join(sal, "portada.png")):
        faltan.append("falta salida/portada.png: corre montar (o video3d.py portada %s)" % rel(trabajo))
    if not os.path.exists(os.path.join(sal, "subtitulos.srt")):
        faltan.append("falta salida/subtitulos.srt: corre montar")
    if faltan:
        for x in faltan:
            print("FALLA", x)
        return 1
    # la carpeta lleva la fecha de la ENTREGA (m257); si el video ya se entregó, se vuelve a entregar en su carpeta
    base3d = os.path.join(RAIZ, "videos3d")
    previas = sorted(d for d in (os.listdir(base3d) if os.path.isdir(base3d) else []) if re.fullmatch(r"\d{4}-\d{2}-\d{2}-" + re.escape(st["slug"]), d))
    fecha_entrega = previas[-1][:10] if previas else datetime.date.today().isoformat()
    destino = os.path.abspath(a.salida or os.path.join(base3d, "%s-%s" % (fecha_entrega, st["slug"])))
    os.makedirs(destino, exist_ok=True)
    for f in ("video.mp4", "video_4x5.mp4", "subtitulos.srt", "portada.png"):
        if os.path.exists(os.path.join(sal, f)):
            shutil.copyfile(os.path.join(sal, f), os.path.join(destino, f))
    shutil.copyfile(os.path.join(trabajo, "maqueta.json"), os.path.join(destino, "maqueta.json"))
    shutil.copyfile(os.path.join(trabajo, "tiempos.json"), os.path.join(destino, "tiempos.json"))   # los cortes reales por escena (metricas.py alinear)
    estilos = {e["id"]: e for e in leer(ESTILOS)["estilos"]} if os.path.exists(ESTILOS) else {}
    escribir(os.path.join(destino, "guion.json"), dict(g, **{
        "tipo": "video3d", "id": "video3d-" + st["slug"], "slug": st["slug"], "tema": st["tema"], "fecha": fecha_entrega,
        "paleta": st["paleta"], "musica": st["musica"], "desde": st.get("desde"),
        "motor": (estilos.get((g.get("estilo") or {}).get("id")) or {}).get("motor"),
        "duracion_s": round(leer(os.path.join(trabajo, "tiempos.json"))["total_s"], 1),
        "creditos_voz": leer(cred)["total"] if os.path.exists(cred) else None}))
    _, por_id = cifras_ok(trabajo)
    usadas = [c.get("cifra") for e in escenas_de(g) for c in e.get("cifras") or []] + list(g.get("cifras_voz") or [])
    lineas = ["# Fuentes · %s" % st["tema"], ""]
    for i in dict.fromkeys(x for x in usadas if x in por_id):
        c = por_id[i]
        lineas += ["- **%s %s** · %s · %s%s" % (c.get("valor_final", c.get("valor")), c.get("unidad", ""), c.get("concepto", ""), c.get("url", ""),
                                            "\n  > %s" % c["cita"] if c.get("cita") else "")]
    pie = leer(os.path.join(trabajo, "maqueta.json"))["capa"].get("pie")
    lineas += ["", "Geodatos: %s" % pie] if pie else []
    with open(os.path.join(destino, "fuentes.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    redes = " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES)
    VD.escribir_caption(os.path.join(destino, "caption.md"), g["caption"], redes, VD.ffprobe_dur(os.path.join(sal, "video.mp4")),
                        clave=g.get("palabra_clave"))
    with open(os.path.join(os.path.dirname(destino), ".gitignore"), "w") as fh:
        fh.write("*.mp4\n")
    st["estado"], st["ruta"] = "listo", rel(destino)
    escribir(os.path.join(trabajo, "video3d.json"), st)
    print("→ %s" % rel(destino))
    print("registra: python3 scripts/memoria.py --video3d %s" % rel(destino))
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "producir":   # la cadena de producción común y reanudable (scripts/producir.py)
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "producir.py")] + sys.argv[2:], cwd=RAIZ).returncode
    if len(sys.argv) > 2 and sys.argv[1] in REENVIO:
        return subprocess.call([sys.executable, os.path.join(RAIZ, "scripts", "video.py")] + sys.argv[1:])
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("preparar")
    s.add_argument("slug")
    s.add_argument("--tema", required=True)
    s.add_argument("--desde")
    s.add_argument("--paleta")
    s.add_argument("--musica-tema", dest="musica_tema")
    s.add_argument("--duracion", type=int, default=OBJETIVO_S)
    s.add_argument("--trabajo")
    s = sub.add_parser("datos")
    s.add_argument("trabajo")
    s.add_argument("--sumar", required=True)
    for nombre in ("digesto", "tiempos", "entregar", "portada"):
        s = sub.add_parser(nombre)
        s.add_argument("trabajo")
        if nombre == "entregar":
            s.add_argument("--salida")
            s.add_argument("--sin-4x5", dest="sin_4x5", action="store_true",
                           help="entrega solo el 9:16 (sin esta bandera, que falte video_4x5.mp4 es una falla)")
    s = sub.add_parser("guion")
    s.add_argument("trabajo")
    s.add_argument("--check", action="store_true")
    s = sub.add_parser("ganchos")
    s.add_argument("trabajo")
    s.add_argument("--check", action="store_true")
    s.add_argument("--cuadros", action="store_true")
    s.add_argument("--clips", action="store_true")
    s.add_argument("--usar")
    s.add_argument("--por", default="usuario")
    s.add_argument("--formato", default="9:16")
    s = sub.add_parser("storyboard")
    s.add_argument("--sin-escenas", action="store_true", help="solo la hoja del storyboard, sin la hoja ni la medida de cada mundo")
    s.add_argument("trabajo")
    s.add_argument("--formato", default="9:16")
    for nombre in ("render", "montar"):
        s = sub.add_parser(nombre)
        s.add_argument("trabajo")
        s.add_argument("--formato", default="ambos", choices=("9:16", "4:5", "ambos"))
        if nombre == "render":
            s.add_argument("--estimado", action="store_true")
        else:
            s.add_argument("--sin-portada", dest="sin_portada", action="store_true", help="no vuelve a dibujar salida/portada.png")
    a = p.parse_args()
    if not a.cmd:
        p.print_help()
        return 2
    return {"preparar": cmd_preparar, "datos": cmd_datos, "digesto": cmd_digesto, "guion": cmd_guion, "ganchos": cmd_ganchos,
            "storyboard": cmd_storyboard, "tiempos": cmd_tiempos, "render": cmd_render, "montar": cmd_montar,
            "portada": cmd_portada, "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
