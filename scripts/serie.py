#!/usr/bin/env python3
"""/serie: un tema contado en 3–5 partes de ≈ 90 s, una investigación compartida y un plan versionado. Solo stdlib.

Motor: /historia (una historia por periodos) o /explica (un temario: un mecanismo por parte). La serie reutiliza el
motor entero (editor, investigador y verificador por eje, consolidar, ganchos, guionista, oyente, crítico, voz, render)
y añade el plan, la cadena de puentes entre partes y los gates SE1–SE9.

Estado de la serie (versionado): series/<fecha>-<slug>/serie.json + serie.md (orden, captions, playlist, qué fijar).
  {version, slug, tema, motor, fecha, carpeta, trabajo, n_partes, paleta, musica, plan_aprobado, estado,
   partes[] {n, titulo, pregunta, periodo {desde, hasta} | mecanismo, puente, hilos[], revelaciones[], estado
   (plan|lista|guion|entregada), trabajo, ruta, duracion_s}, historial[] {version, fecha, nota, partes}}

Subcomandos:
  preparar TEMA [--partes 3] [--motor historia|explica] [--slug S] [--paleta P] [--carpeta DIR] [--fixture]
      crea serie.json (estado plan) y el TRABAJO de la investigación compartida (sesiones/serie-<slug>) con el preparar del
      motor; imprime SERIE y TRABAJO (la última línea).
  plan TRABAJO --check [--aprobar]
      SE1 (3–5 partes, cada una con título, pregunta, periodo o mecanismo, actos y espina, hilos y revelaciones) y SE2 (la
      cadena de puentes: el puente de la parte N lo abre la pregunta de la N+1; ningún puente dice un número de una
      revelación de una parte posterior; los periodos van en orden y no se pisan) sobre encuadre.json → serie; con
      --aprobar (el usuario vio el plan) lo marca aprobado. Un plan que cambia sube la versión.
  cobertura TRABAJO --check
      consolida la investigación y comprueba SE3: ≥ 4 hechos publicables por parte (en su periodo; con /explica, ≥ 2
      afirmaciones o cifras por parte) y la foto del protagonista (/historia).
  parte SERIE N
      arma sesiones/serie-<slug>/parte-N: la investigación copiada, el encuadre de la parte, video.json con formato
      historia-serie | explica-serie (≈ 90 s), la paleta y la música de la serie y la parte siguiente; consolida (una
      parte de /historia solo ve los hechos hasta el fin de su periodo). Imprime el TRABAJO de la parte.
  digesto SERIE        el plan legible (para mostrárselo al usuario antes de producir).
  estado SERIE         las partes, su estado y si ya se pueden publicar.
  guion-aprobado TRABAJO_PARTE   el crítico aprobó el guion de esa parte: pasa a «guion» (habilita publicar la anterior).
  entregar-parte TRABAJO_PARTE [--salida DIR]
      entrega la parte con el entregar del motor en series/<fecha>-<slug>/parte-N y rehace serie.json y serie.md.
  --revisar SERIE      M16: el esquema de serie.json (también lo corre validate.py).

Gates de cada parte (los llama historia.py / explica.py en guion --check):
  SE4 cada parte se entiende sola: sin «como vimos», «en la parte anterior», «en el video anterior»
  SE5 la paleta y la música son las de la serie
  SE6 cierre «puente» en las partes 1…M−1 (la pregunta que abre la siguiente, sin anunciarla); en la última, ningún
      hilo pasa_a y el cierre no es puente
  SE7 75–110 s estimados (< 61 s falla; 61–75 aviso)
  SE8 captions que abren con «Serie · Parte N de M: <título>» y título de Shorts con «(N/M)»; en las partes 2…M, los de
      TikTok, Instagram y Facebook dicen que la Parte 1 está fijada en el perfil
  SE9 partes 1…M−1: cierre.invitacion, la última oración de la voz (tras la frase final): pide seguir la cuenta
      («Sígueme»), nombra la parte siguiente en palabras («en la segunda parte») y dice qué cuenta (comparte una raíz con
      su título o su pregunta); ≤ 18 palabras, sin cifras; en la última parte no hay invitación
Regla de publicación: la parte N no se publica hasta que la N+1 tenga el guion aprobado (serie.md lo dice).

Exit: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402

MOTORES = ("historia", "explica")
PARTES = (3, 5)
PARTES_CASO = (3, 8)          # modo caso (/serie <tema> 7 caso): un caso complejo contado por temas, más partes y más largas
FORMATO_DE = {"historia": "historia-serie", "explica": "explica-serie"}
OBJETIVO_S, DURACION = 90, (75, 110)
OBJETIVO_CASO_S, DURACION_CASO = 130, (115, 150)
DURACION_DE = {"historia-serie": DURACION, "explica-serie": DURACION, "historia-caso": DURACION_CASO}
INVENTARIO_MIN, HECHOS_CASO_MIN, DENSIDAD_MIN = 0.85, 8, 0.60   # SE10, SE12
PISO_S = 61
# SE14 (decisión del usuario, 2026-11-07): la última parte lleva un resumen de toda la serie, simple y con impacto, para
# recordar lo que pasó: UNA escena con `resumen_serie: true` en el acto 3 (antes de la última cita o del cierre), de 20–30 s
# de voz, que repasa en orden hechos que ya contaron las partes anteriores (≥ 1 de RESUMEN_PARTES_MIN de ellas; nada
# nuevo). Queda fuera de SE13 (repetir es su trabajo) y su duración se suma al límite de la parte (SE7, H5).
RESUMEN_S, RESUMEN_EXTRA_S, RESUMEN_PARTES_MIN = (20, 30), 30, 5
HECHOS_POR_PARTE = 4          # SE3 (historia); con /explica, afirmaciones o cifras por parte
AFIRMACIONES_POR_PARTE = 2
TITULO_PALABRAS = 6
ESTADOS_PARTE = ("plan", "lista", "guion", "entregada")
NO_SOLA = re.compile(r"\b(como\s+(?:ya\s+)?vimos|como\s+te\s+cont[eé]|en\s+la\s+parte\s+anterior|en\s+el\s+(?:video|cap[ií]tulo)\s+anterior|"
                     r"en\s+la\s+primera\s+parte|en\s+la\s+parte\s+\w+\s+(?:vimos|contamos))\b", re.I)
# SE9 (decisión del usuario, 2026-11-05): al terminar cada parte que no es la última, la voz invita a seguir la cuenta
# para la siguiente y dice qué cuenta; en las partes 2…M la pantalla final y los captions mandan a la Parte 1 (fijada)
ORDINAL = {2: "segunda", 3: "tercera", 4: "cuarta", 5: "quinta", 6: "sexta", 7: "séptima", 8: "octava"}
CARDINAL = {2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho"}
INVITACION_PALABRAS = 18
RE_SIGUEME = re.compile(r"\bs[ií]gue(?:me|nos)\b|\bsigue\s+(?:la|esta)\s+cuenta\b", re.I)
RE_PARTE1_PERFIL = re.compile(r"parte\s*(?:1|uno)\b.{0,60}\bperfil|\bperfil\b.{0,60}parte\s*(?:1|uno)\b", re.I | re.S)
FIXTURE = {"historia": os.path.join(RAIZ, "sesiones", "_fixture_serie"),
           "explica": os.path.join(RAIZ, "sesiones", "_fixture_serie_explica")}


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def rel(p):
    return os.path.relpath(p, RAIZ)


def falla(m):
    print("ERROR:", m, file=sys.stderr)
    return 1


def motor_mod(motor):
    if motor == "explica":
        import explica as M  # noqa: E402
    else:
        import historia as M  # noqa: E402
    return M


def slug_de(s):
    import historia as HI  # noqa: E402
    return HI.slug_de(s)


# ---------- serie.json ----------
def ruta_serie(arg):
    """serie.json desde: la carpeta de la serie, su serie.json, el TRABAJO (base o parte) o el slug."""
    if not arg:
        return None
    p = os.path.abspath(arg)
    if os.path.isfile(p) and p.endswith("serie.json"):
        return p
    if os.path.isfile(os.path.join(p, "serie.json")):
        return os.path.join(p, "serie.json")
    for d in (p, os.path.dirname(p)):
        st = os.path.join(d, "video.json")
        if os.path.isfile(st):
            car = VD.serie_de(leer(st)).get("carpeta")
            if car and os.path.isfile(os.path.join(RAIZ, car, "serie.json")):
                return os.path.join(RAIZ, car, "serie.json")
    hits = sorted(glob.glob(os.path.join(RAIZ, "series", "*-%s" % arg, "serie.json")))
    return hits[-1] if hits else None


def cargar_serie(arg):
    r = ruta_serie(arg)
    if not r:
        raise SystemExit(falla("no encuentro serie.json para «%s» (corre serie.py preparar)" % arg))
    return r, leer(r)


def guardar_serie(ruta, S, nota=None):
    """Escribe serie.json; un cambio de plan (nota) sube la versión y guarda las partes de ese momento en historial."""
    if nota:
        S["version"] = int(S.get("version") or 0) + 1
        S.setdefault("historial", []).append({"version": S["version"], "fecha": datetime.date.today().isoformat(), "nota": nota,
                                              "partes": [{k: p.get(k) for k in ("n", "titulo", "pregunta", "periodo", "mecanismo", "puente")}
                                                         for p in S.get("partes") or []]})
    escribir(ruta, S)
    escribir_md(ruta, S)


def publicable(S, p):
    """La parte N se publica cuando la N+1 ya tiene el guion aprobado (o es la última)."""
    sig = next((x for x in S["partes"] if x["n"] == p["n"] + 1), None)
    return p.get("estado") == "entregada" and (sig is None or sig.get("estado") in ("guion", "entregada"))


def escribir_md(ruta, S):
    M = S.get("n_partes") or len(S.get("partes") or [])
    L = ["# Serie · %s" % S.get("tema"), "",
         "Motor: /%s · %d partes · versión %s del plan%s · paleta %s · música %s" % (
             S.get("motor"), M, S.get("version"), " (aprobado)" if S.get("plan_aprobado") else " (por aprobar)",
             S.get("paleta"), S.get("musica")), "",
         "**Publicación**: la parte N sale cuando la N+1 ya tiene el guion aprobado. Fija la Parte 1 en el perfil y arma una "
         "playlist (YouTube) o una lista (TikTok) con las partes en orden: «%s»." % S.get("tema"), "",
         "| Parte | Título | Pregunta | Puente | Estado | Publicar |", "|---|---|---|---|---|---|"]
    for p in S.get("partes") or []:
        L.append("| %d de %d | %s | %s | %s | %s | %s |" % (p["n"], M, p.get("titulo") or "", p.get("pregunta") or "",
                                                        p.get("puente") or "—", p.get("estado") or "plan",
                                                        "sí" if publicable(S, p) else "no"))
    for p in S.get("partes") or []:
        if p.get("ruta") and os.path.exists(os.path.join(RAIZ, p["ruta"], "caption.md")):
            L += ["", "## Parte %d · %s" % (p["n"], p.get("titulo") or ""), "", "Video: `%s/video.mp4` (9:16) y `video_4x5.mp4`; "
                  "captions en `%s/caption.md`." % (p["ruta"], p["ruta"])]
    open(os.path.join(os.path.dirname(ruta), "serie.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


# ---------- preparar ----------
def dibujar_fotos(fx, trabajo):
    """Fotos de la maqueta (fractales de ffmpeg, sin web), como copiar_fixture de historia.py."""
    tonos = (20, 90, 160, 230, 300)
    for k, rec in enumerate(leer(os.path.join(fx, "fotos.json"))["fotos"]):
        rec = dict(rec, archivo="fotos/%s.jpg" % rec["id"], url=None)
        os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
        VD.ff("-f", "lavfi", "-i", "mandelbrot=s=1600x1200:start_scale=%.2f:end_scale=0.3:start_x=%.3f:start_y=%.3f:maxiter=600" % (
            2.2 - 0.3 * (k % 4), -0.743 + 0.012 * (k % 4), 0.131 - 0.018 * (k % 4)),   # k % 4: más hondo el fractal queda negro (sin detalle)
            "-vf", "hue=h=%d:s=0.5,eq=brightness=-0.05:saturation=0.75,noise=alls=12:allf=t" % tonos[k % len(tonos)],
            "-frames:v", "1", "-q:v", "3", os.path.join(trabajo, rec["archivo"]))
        escribir(os.path.join(trabajo, "fotos", rec["id"] + ".json"), rec)


def cmd_preparar(a):
    slug = slug_de(a.slug or a.tema)
    if not slug:
        return falla("el tema no da un slug")
    rango = PARTES_CASO if getattr(a, "caso", False) else PARTES
    if not rango[0] <= a.partes <= rango[1]:
        print("--partes: %d–%d" % rango, file=sys.stderr)
        return 2
    if getattr(a, "caso", False) and a.motor != "historia":
        print("--caso va con el motor historia", file=sys.stderr)
        return 2
    hoy = datetime.date.today().isoformat()
    carpeta = os.path.abspath(a.carpeta or os.path.join(RAIZ, "series", "%s-%s" % (hoy, slug)))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "serie-" + slug))
    M = motor_mod(a.motor)
    os.makedirs(trabajo, exist_ok=True)
    if a.motor == "historia":
        rc = M.cmd_preparar(argparse.Namespace(tema=a.tema, slug=slug, trabajo=trabajo, paleta=a.paleta, musica=None, fixture=a.fixture))
    else:
        rc = M.cmd_preparar(argparse.Namespace(tema=a.tema, slug=slug, trabajo=trabajo, paleta=a.paleta, musica=None, fixture=False,
                                               duracion="corto", modo="explica"))   # explica.py preparar (motor temario)
    if rc:
        return rc
    st = VD.estado(trabajo)
    st["serie"] = {"carpeta": rel(carpeta), "partes": a.partes, "motor": a.motor}
    escribir(os.path.join(trabajo, "video.json"), st)
    if a.fixture:
        fx = FIXTURE[a.motor]
        for f in glob.glob(os.path.join(fx, "*.json")):
            if os.path.basename(f) not in ("fotos.json",) and not os.path.basename(f).startswith("parte"):
                shutil.copy(f, os.path.join(trabajo, os.path.basename(f)))
        if os.path.exists(os.path.join(fx, "fotos.json")):
            dibujar_fotos(fx, trabajo)
    ruta = os.path.join(carpeta, "serie.json")
    previo = leer(ruta) if os.path.exists(ruta) else {}
    S = {"version": previo.get("version") or 0, "slug": slug, "tema": a.tema, "motor": a.motor, "fecha": previo.get("fecha") or hoy,
         "carpeta": rel(carpeta), "trabajo": rel(trabajo), "n_partes": a.partes, "paleta": st.get("paleta"),
         "musica": st.get("musica"), "plan_aprobado": False, "estado": "plan", "partes": previo.get("partes") or [],
         "historial": previo.get("historial") or [], "fixture": bool(a.fixture),
         "modo": "caso" if getattr(a, "caso", False) else "serie"}
    guardar_serie(ruta, S)
    print("serie «%s» · %d partes · motor /%s · %s" % (a.tema, a.partes, a.motor, rel(ruta)))
    print("SERIE %s" % rel(carpeta))
    print(rel(trabajo))
    return 0


# ---------- plan: SE1, SE2 ----------
def raices(t):
    return {w[:6] for w in re.findall(r"[a-zñ]+", VD._plano(t or "")) if len(w) >= 4 and w not in VD.STOP}


def numeros(t):
    return {x.replace(",", "") for x in re.findall(r"\d[\d,]*(?:\.\d+)?", t or "")}


def fecha_clave(x):
    return str(x or "").strip()


def revisar_plan(enc, motor, M_esperado=None, caso=False):
    """SE1 + SE2 sobre encuadre.json → serie.partes. → (fallas, partes normalizadas). En modo caso las partes van por
    tema: los periodos pueden pisarse (SE2 no lo mira) y el reparto lo revisan SE10–SE11 (revisar_inventario)."""
    f = []
    partes = ((enc.get("serie") or {}).get("partes")) or []
    rango = PARTES_CASO if caso else PARTES
    if not rango[0] <= len(partes) <= rango[1]:
        return ["SE1 encuadre.serie.partes: %d partes (van %d–%d)" % (len(partes), *rango)], []
    if M_esperado and len(partes) != M_esperado:
        f.append("SE1 el plan trae %d partes y la serie se preparó con %d (serie.py preparar --partes)" % (len(partes), M_esperado))
    for k, p in enumerate(partes, 1):
        tag = "SE1 parte %d" % k
        if p.get("n") != k:
            f.append("%s: «n» = %s (van en orden 1…%d)" % (tag, p.get("n"), len(partes)))
        tit = (p.get("titulo") or "").strip()
        if not tit or VD.palabras(tit) > TITULO_PALABRAS:
            f.append("%s: «titulo» de 1–%d palabras" % (tag, TITULO_PALABRAS))
        if not (p.get("pregunta") or "").strip().endswith("?"):
            f.append("%s: «pregunta» (la que abre esa parte, con «?»)" % tag)
        if motor == "historia":
            pe = p.get("periodo") or {}
            if not (re.match(r"^\d{4}(-\d{2})?$", fecha_clave(pe.get("desde"))) and re.match(r"^\d{4}(-\d{2})?$", fecha_clave(pe.get("hasta")))
                    and fecha_clave(pe.get("desde")) <= fecha_clave(pe.get("hasta"))):
                f.append("%s: «periodo» {desde, hasta} en AAAA o AAAA-MM, desde ≤ hasta" % tag)
            if len(p.get("actos") or []) != 3:
                f.append("%s: «actos» = 3 (planteamiento, nudo, desenlace de la parte)" % tag)
            esp = p.get("espina") or {}
            if any(not ((esp.get(x) or {}).get("frase") or "").strip() for x in ("detonante", "punto_medio", "climax", "resolucion")):
                f.append("%s: «espina» con detonante, punto_medio, climax y resolucion ({frase, acto})" % tag)
        else:
            if not (p.get("mecanismo") or "").strip():
                f.append("%s: «mecanismo» (el de esa parte: %s)" % (tag, "|".join(VD.MECANISMOS_EXPLICA)))
            elif p["mecanismo"] not in VD.MECANISMOS_EXPLICA:
                f.append("%s: mecanismo «%s» no es uno de %s" % (tag, p["mecanismo"], "|".join(VD.MECANISMOS_EXPLICA)))
            if not (p.get("intuicion") or "").strip():
                f.append("%s: «intuicion» (la idea equivocada de esa parte)" % tag)
            if not 30 <= len((p.get("mecanismo_frase") or "").strip()) <= 220:
                f.append("%s: «mecanismo_frase» (la oración que el oyente devuelve, 30–220 caracteres)" % tag)
            ejes_enc = {x.get("id") for x in enc.get("ejes") or [] if isinstance(x, dict)}
            if not p.get("ejes") or any(x not in ejes_enc for x in p.get("ejes") or []):
                f.append("%s: «ejes» (los ejes de la investigación que la sostienen: %s)" % (tag, ", ".join(sorted(ejes_enc))))
        hil = [h for h in p.get("hilos") or [] if isinstance(h, dict) and (h.get("id") or "").strip()]
        if motor == "historia" and not 1 <= len(hil) <= 4:
            f.append("%s: «hilos» 1–4 {id, pregunta}" % tag)
        if not 1 <= len(p.get("revelaciones") or []) <= 3:
            f.append("%s: «revelaciones» 1–3 (lo que paga ESA parte)" % tag)
        pu = (p.get("puente") or "").strip() if p.get("puente") else ""
        if k < len(partes) and not pu:
            f.append("SE2 parte %d: «puente» (la pregunta que deja abierta y abre la parte %d)" % (k, k + 1))
        if k == len(partes) and pu:
            f.append("SE2 parte %d es la última: «puente» null (todo se paga)" % k)
    # SE2 la cadena: el puente de N lo abre la pregunta de N+1; ningún puente adelanta una revelación posterior
    for k in range(len(partes) - 1):
        pu, sig = partes[k].get("puente") or "", partes[k + 1]
        comunes = raices(pu) & raices(sig.get("pregunta"))
        if pu and len(comunes) < 1:
            f.append("SE2 el puente de la parte %d («%s») no lo abre la pregunta de la parte %d («%s»): la parte siguiente "
                     "empieza donde la anterior dejó la pregunta" % (k + 1, pu[:60], k + 2, (sig.get("pregunta") or "")[:60]))
        posteriores = numeros(" ".join(" ".join(x.get("revelaciones") or []) for x in partes[k + 1:]))
        sueltos = numeros(pu) & posteriores
        if sueltos:
            f.append("SE2 el puente de la parte %d dice %s, que revela una parte posterior: el puente pregunta, no responde"
                     % (k + 1, ", ".join(sorted(sueltos))))
        if motor == "historia" and not caso:
            h1, d2 = fecha_clave((partes[k].get("periodo") or {}).get("hasta")), fecha_clave((sig.get("periodo") or {}).get("desde"))
            if h1 and d2 and d2 < h1:
                f.append("SE2 los periodos se pisan: la parte %d termina en %s y la %d empieza en %s" % (k + 1, h1, k + 2, d2))
    ids = [h.get("id") for p in partes for h in p.get("hilos") or [] if isinstance(h, dict)]
    if len(ids) != len(set(ids)):
        f.append("SE1 ids de hilo repetidos entre partes (cada hilo vive en una parte; el que sigue abierto pasa con pasa_a)")
    norm = []
    for p in partes:
        norm.append({"n": p.get("n"), "titulo": (p.get("titulo") or "").strip(), "pregunta": (p.get("pregunta") or "").strip(),
                     "periodo": p.get("periodo"), "mecanismo": p.get("mecanismo"), "ejes": p.get("ejes"), "puente": p.get("puente") or None,
                     "hilos": [h.get("id") for h in p.get("hilos") or [] if isinstance(h, dict)],
                     "revelaciones": p.get("revelaciones") or [], "tema": p.get("tema"), "hechos": p.get("hechos") or [],
                     "obligatorio": p.get("obligatorio") or []})
    return f, norm


def revisar_inventario(enc, H):
    """SE10 inventario y SE11 columna (modo caso). SE10: cada hecho, cifra o cita publicable de la investigación va a
    una parte (`partes[].hechos`, ids) o a `serie.fuera` {id: motivo}; ≥ 85 % repartido y ≥ 8 hechos por parte; un id
    no se reparte en dos partes. SE11: `serie.columna` (los temas del caso, en orden) y cada parte declara su `tema`
    de la columna; cada tema lo cubre al menos una parte."""
    f = []
    ser = enc.get("serie") or {}
    partes = ser.get("partes") or []
    pub = {x["id"]: k for k in ("hechos", "cifras", "citas") for x in H.get(k) or []}
    fuera = ser.get("fuera") or {}
    vistos = {}
    for p in partes:
        for i in p.get("hechos") or []:
            if i not in pub:
                f.append("SE10 parte %s: «%s» no es un hecho, cifra o cita publicable" % (p.get("n"), i))
            elif i in vistos:
                f.append("SE10 «%s» está en las partes %s y %s: cada id va a una sola parte" % (i, vistos[i], p.get("n")))
            vistos.setdefault(i, p.get("n"))
        n_h = sum(1 for i in p.get("hechos") or [] if pub.get(i) == "hechos")
        if n_h < HECHOS_CASO_MIN:
            f.append("SE10 parte %s: %d hechos repartidos (van ≥ %d)" % (p.get("n"), n_h, HECHOS_CASO_MIN))
    sin = [i for i in pub if i not in vistos and i not in fuera]
    cubierto = (len(pub) - len(sin)) / max(1, len(pub))
    if cubierto < INVENTARIO_MIN:
        f.append("SE10 inventario: %.0f %% de lo publicable va a una parte o tiene motivo (van ≥ %.0f %%); sin repartir: %s"
                 % (100 * cubierto, 100 * INVENTARIO_MIN, ", ".join(sin[:12]) + (" …" if len(sin) > 12 else "")))
    col = [c for c in ser.get("columna") or [] if (c or "").strip()]
    if not col:
        f.append("SE11 serie.columna: los temas del caso en orden (cómo se descubrió, cómo cobraban, quiénes eran…)")
    temas = [p.get("tema") for p in partes]
    for k, p in enumerate(partes, 1):
        if col and p.get("tema") not in col:
            f.append("SE11 parte %d: «tema» de la columna (%s)" % (k, " · ".join(col)))
    for c in col:
        if c not in temas:
            f.append("SE11 el tema «%s» de la columna no lo cubre ninguna parte" % c)
    return f


def cmd_plan(a):
    trabajo = os.path.abspath(a.trabajo)
    ruta, S = cargar_serie(trabajo)
    enc_r = os.path.join(trabajo, "encuadre.json")
    if not os.path.exists(enc_r):
        return falla("falta %s (el editor escribe el encuadre con el plan de la serie)" % rel(enc_r))
    caso = S.get("modo") == "caso"
    f, norm = revisar_plan(leer(enc_r), S["motor"], S.get("n_partes"), caso=caso)
    if caso:
        hj = os.path.join(trabajo, "historia.json")
        f += revisar_inventario(leer(enc_r), leer(hj) if os.path.exists(hj) else {})
    for x in f:
        print("FALLA", x)
    if f:
        print("[serie plan] %d fallas" % len(f))
        return 1
    previo = [{k: p.get(k) for k in ("n", "titulo", "pregunta", "periodo", "mecanismo", "puente")} for p in S.get("partes") or []]
    nuevo = [{k: p.get(k) for k in ("n", "titulo", "pregunta", "periodo", "mecanismo", "puente")} for p in norm]
    estados = {p["n"]: p for p in S.get("partes") or []}
    for p in norm:
        viejo = estados.get(p["n"]) or {}
        p.update({k: viejo.get(k) for k in ("estado", "trabajo", "ruta", "duracion_s") if viejo.get(k)})
        p.setdefault("estado", "plan")
    S["partes"] = norm
    cambio = previo != nuevo
    if cambio and S.get("plan_aprobado") and not a.aprobar:
        S["plan_aprobado"] = False
        print("AVISO el plan cambió después de aprobado: vuelve a mostrárselo al usuario (serie.py digesto) y apruébalo con --aprobar")
    if a.aprobar:
        S["plan_aprobado"] = True
        S["estado"] = "plan_aprobado" if S.get("estado") in (None, "plan") else S["estado"]
    guardar_serie(ruta, S, nota=("plan %s" % ("aprobado por el usuario" if a.aprobar else "nuevo")) if (cambio or a.aprobar) else None)
    for p in norm:
        print("parte %d · %s · %s · puente: %s" % (p["n"], p["titulo"], p.get("periodo") or p.get("mecanismo"), p.get("puente") or "—"))
    print("[serie plan] ok · versión %s%s" % (S.get("version"), " · aprobado" if S.get("plan_aprobado") else " · falta que el usuario lo apruebe (--aprobar)"))
    return 0


# ---------- cobertura: SE3 ----------
def en_periodo(fecha, pe):
    fe = fecha_clave(fecha)
    d, h = fecha_clave(pe.get("desde")), fecha_clave(pe.get("hasta"))
    return bool(re.match(r"\d{4}", fe)) and fe[:len(d)] >= d and fe[:len(h)] <= h


def cmd_cobertura(a):
    trabajo = os.path.abspath(a.trabajo)
    ruta, S = cargar_serie(trabajo)
    M = motor_mod(S["motor"])
    if hasattr(M, "aplicar_formato"):
        M.aplicar_formato(trabajo)
    rc = M.cmd_consolidar(argparse.Namespace(trabajo=trabajo))
    if rc:
        return falla("consolidar falló: arregla la investigación antes de partirla")
    f = []
    if S["motor"] == "historia":
        H = leer(os.path.join(trabajo, "historia.json"))
        for p in S["partes"]:
            n = sum(1 for h in H["hechos"] if en_periodo(h.get("fecha"), p.get("periodo") or {}))
            print("parte %d · %s · %d hechos en %s–%s" % (p["n"], p["titulo"], n, (p.get("periodo") or {}).get("desde"), (p.get("periodo") or {}).get("hasta")))
            if n < HECHOS_POR_PARTE:
                f.append("SE3 parte %d: %d hechos publicables en su periodo (van ≥ %d): investiga más ese periodo o júntala con otra"
                         % (p["n"], n, HECHOS_POR_PARTE))
    else:
        E = leer(os.path.join(trabajo, "explicacion.json")) if os.path.exists(os.path.join(trabajo, "explicacion.json")) else {}
        items = (E.get("afirmaciones") or []) + (E.get("cifras") or [])
        for p in S["partes"]:
            n = sum(1 for x in items if x.get("eje") in (p.get("ejes") or []))
            print("parte %d · %s · %d afirmaciones o cifras" % (p["n"], p["titulo"], n))
            if n < AFIRMACIONES_POR_PARTE:
                f.append("SE3 parte %d: %d afirmaciones o cifras verificadas para su mecanismo (van ≥ %d)" % (p["n"], n, AFIRMACIONES_POR_PARTE))
    for x in f:
        print("FALLA", x)
    st = VD.estado(trabajo)   # consolidar fija la paleta del encuadre: la de toda la serie
    S["paleta"], S["musica"] = st.get("paleta"), st.get("musica")
    if not f:
        S["estado"] = "investigada"
    guardar_serie(ruta, S)
    print("[serie cobertura] %s" % ("ok" if not f else "%d fallas" % len(f)))
    return 1 if f else 0


# ---------- parte ----------
def familias_previas(S, n):
    """Las familias de gancho que ya usaron las partes anteriores (la serie no repite gancho)."""
    out = []
    for p in S["partes"]:
        if S.get("modo") == "caso" and p["n"] < n - 2:   # en un caso largo, una familia vuelve a 3 partes de distancia
            continue
        if p["n"] < n and p.get("trabajo"):
            sel = os.path.join(RAIZ, p["trabajo"], "ganchos.json")
            if os.path.exists(sel):
                G = leer(sel)
                c = next((x for x in G.get("candidatos") or [] if x.get("id") == G.get("elegido")), None)
                if c and c.get("familia"):
                    out.append(c["familia"])
    return out


def cmd_parte(a):
    ruta, S = cargar_serie(a.serie)
    if not S.get("plan_aprobado") and not S.get("fixture"):
        return falla("el plan no está aprobado: muéstraselo al usuario (serie.py digesto) y corre serie.py plan <TRABAJO> --check --aprobar")
    p = next((x for x in S["partes"] if x["n"] == a.n), None)
    if not p:
        return falla("la serie no tiene parte %d" % a.n)
    base = os.path.join(RAIZ, S["trabajo"])
    destino = os.path.join(base, "parte-%d" % a.n)
    os.makedirs(destino, exist_ok=True)
    for pat in ("verificacion_*.json", "hallazgos_*.json", "afirmaciones_*.json"):
        for f in glob.glob(os.path.join(base, pat)):
            shutil.copy(f, os.path.join(destino, os.path.basename(f)))
    for d in ("fotos", "tomas", "videos"):  # las tomas de video también (consolidar deja fuera las de partes siguientes)
        if os.path.isdir(os.path.join(base, d)):
            shutil.copytree(os.path.join(base, d), os.path.join(destino, d), dirs_exist_ok=True)
    for d in ("audio", "salida", "revision", "base"):
        os.makedirs(os.path.join(destino, d), exist_ok=True)
    enc = leer(os.path.join(base, "encuadre.json"))
    plan = next(x for x in (enc.get("serie") or {}).get("partes") or [] if x.get("n") == a.n)
    M = len(S["partes"])
    sig = next((x for x in S["partes"] if x["n"] == a.n + 1), None)
    enc_p = {k: v for k, v in enc.items() if k != "serie"}
    enc_p.update({k: plan[k] for k in ("actos", "espina", "hilos", "revelaciones") if plan.get(k)})
    enc_p.update(pregunta=plan.get("pregunta"), resumen=plan.get("pregunta"), paleta=S["paleta"],
                 serie={"parte": a.n, "de": M, "titulo": plan.get("titulo"), "puente": plan.get("puente")})
    if S["motor"] == "explica":
        enc_p.update({k: plan[k] for k in ("mecanismo", "mecanismo_frase", "intuicion") if plan.get(k)})
        enc_p.pop("hilos", None)
    escribir(os.path.join(destino, "encuadre.json"), enc_p)
    st = dict(VD.estado(base))
    st.pop("serie", None)
    st.update({"slug": "%s-parte-%d" % (S["slug"], a.n), "hilo": rel(os.path.join(destino, "base")),
               "formato": "historia-caso" if S.get("modo") == "caso" else FORMATO_DE[S["motor"]],
               "objetivo_s": OBJETIVO_CASO_S if S.get("modo") == "caso" else OBJETIVO_S, "piso_s": PISO_S,
               **({"duracion": "explica-serie"} if S["motor"] == "explica" else {}),
               "paleta": S["paleta"], "musica": S["musica"], "musica_forzada": S["musica"],
               "serie": {"carpeta": S["carpeta"], "slug": S["slug"], "parte": a.n, "de": M, "titulo": plan.get("titulo"),
                         "periodo": plan.get("periodo"), "mecanismo": plan.get("mecanismo"), "puente": plan.get("puente"),
                         "siguiente": {"n": sig["n"], "titulo": sig["titulo"], "pregunta": sig.get("pregunta")} if sig else None,
                         "paleta": S["paleta"], "musica": S["musica"], "modo": S.get("modo") or "serie",
                         # modo caso: lo que cuenta esta parte (sus ids) y lo que no puede adelantar (los de las siguientes)
                         "hechos": plan.get("hechos") or [], "obligatorio": plan.get("obligatorio") or [],
                         "reservar": [i for x in (enc.get("serie") or {}).get("partes") or [] if x.get("n", 0) > a.n
                                      for i in x.get("hechos") or [] if i not in (plan.get("hechos") or [])]}})
    rec = st.get("ganchos_recientes") or {"familias": [], "visuales": []}
    rec["familias"] = list(dict.fromkeys(familias_previas(S, a.n) + (rec.get("familias") or [])))
    st["ganchos_recientes"] = rec
    escribir(os.path.join(destino, "video.json"), st)
    Mm = motor_mod(S["motor"])
    if hasattr(Mm, "aplicar_formato"):
        Mm.aplicar_formato(destino)
    rc = Mm.cmd_consolidar(argparse.Namespace(trabajo=destino))
    if rc:
        return falla("consolidar de la parte %d falló" % a.n)
    p.update(estado="lista" if p.get("estado") in (None, "plan") else p["estado"], trabajo=rel(destino))
    S["estado"] = "en_produccion"
    guardar_serie(ruta, S)
    print("parte %d de %d · «%s» · formato %s · paleta %s · música %s%s" % (a.n, M, plan.get("titulo"), st["formato"], S["paleta"],
                                                                       S["musica"], " · siguiente: «%s»" % sig["titulo"] if sig else " · última"))
    print(rel(destino))
    return 0


# ---------- SE4–SE9 (los llama el gate del motor) ----------
def revisar_parte(g, st, trabajo):
    """SE4–SE9 de una parte → fallas (los avisos se imprimen)."""
    ser = VD.serie_de(st)
    n, M = ser.get("parte"), ser.get("de")
    f = []
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    inv = (cierre.get("invitacion") or "").strip()
    voces = [VD.sin_pausas(e.get("texto") or "") for e in escenas] + [VD.sin_pausas(cierre.get("texto") or "")]
    todo = " ".join(voces + [str(e.get("pantalla") or "") for e in escenas])
    if inv:
        voces[-1] = (voces[-1] + " " + VD.sin_pausas(inv)).strip()
    m = NO_SOLA.search(todo)
    if m:
        f.append("SE4 «%s»: cada parte se entiende sola (quien llega por la parte %d no vio las otras): cuenta en una oración "
                 "lo que hace falta, sin remitir a otra parte" % (m.group(), n))
    if st.get("paleta") != ser.get("paleta") or st.get("musica") != ser.get("musica"):
        f.append("SE5 paleta %s y música %s; la serie va con %s y %s (las mismas en todas las partes)"
                 % (st.get("paleta"), st.get("musica"), ser.get("paleta"), ser.get("musica")))
    hilos_pasan = [h.get("id") for h in g.get("hilos") or [] if isinstance(h, dict) and h.get("pasa_a") is not None]
    if n and M and n < M:
        if cierre.get("forma") != "puente":
            f.append("SE6 la parte %d de %d cierra con forma «puente»: la pregunta que abre la parte %d (%s), sin anunciarla"
                     % (n, M, n + 1, ((ser.get("siguiente") or {}).get("titulo") or "")))
        else:
            pu = ser.get("puente") or ((ser.get("siguiente") or {}).get("pregunta")) or ""
            if pu and not (raices(VD.final_de(cierre)) & raices(pu + " " + ((ser.get("siguiente") or {}).get("pregunta") or ""))):
                f.append("SE6 la frase final («%s») no deja la pregunta del puente («%s»)" % (VD.final_de(cierre)[:60], pu[:60]))
    elif n and M and n == M:
        if cierre.get("forma") == "puente":
            f.append("SE6 la última parte no cierra con puente: paga (legado o consecuencia)")
        if hilos_pasan:
            f.append("SE6 la última parte no pasa hilos (%s): se pagan o se declaran sin respuesta" % ", ".join(hilos_pasan))
    f += revisar_invitacion(inv, n, M, ser)
    est = sum(VD.segundos_voz(t) for t in voces) + VD.COLA * (len(escenas) + 1)
    dur_r = DURACION_DE.get(st.get("formato"), DURACION)
    if n and M and n == M:   # SE14: el resumen de la última parte se suma al límite
        dur_r = (dur_r[0], dur_r[1] + RESUMEN_EXTRA_S)
    if est < PISO_S:
        f.append("SE7 la parte dura ≈ %.0f s estimados: menos de %d s no cuenta para Creator Rewards; van %d–%d" % (est, PISO_S, *dur_r))
    elif est < dur_r[0]:
        print("AVISO SE7 la parte dura ≈ %.0f s estimados (van %d–%d)" % (est, *dur_r))
    elif est > dur_r[1]:
        f.append("SE7 la parte dura ≈ %.0f s estimados (van %d–%d): recorta" % (est, *dur_r))
    if ser.get("modo") == "caso" and ser.get("hechos"):   # SE12 densidad: la parte cuenta lo que se le repartió
        citados = {h for e in escenas for h in (e.get("hechos") or []) + (e.get("cifras") or [])} | \
                  {x for e in escenas for x in (e.get("cita"), (e.get("cifra") or {}).get("id")) if x}
        rep_ids = ser["hechos"]
        hechos_rep = [i for i in rep_ids if "-h" in i]
        dens = sum(1 for i in hechos_rep if i in citados) / max(1, len(hechos_rep))
        if dens < DENSIDAD_MIN:
            f.append("SE12 la parte cita %.0f %% de sus hechos repartidos (van ≥ %.0f %%): faltan %s"
                     % (100 * dens, 100 * DENSIDAD_MIN, ", ".join(i for i in hechos_rep if i not in citados)[:200]))
        for i in ser.get("obligatorio") or []:
            if i not in citados:
                f.append("SE12 la parte no cuenta «%s» (obligatorio en su reparto)" % i)
        adelanta = [i for i in ser.get("reservar") or [] if i in citados]
        if adelanta:
            f.append("SE12 la parte usa %s, que se reparte a una parte siguiente (no la adelantes)" % ", ".join(adelanta))
    cap = g.get("caption") or {}
    prefijo = "Serie · Parte %d de %d: " % (n or 0, M or 0)
    for k in ("tiktok", "instagram", "facebook"):
        t = (cap.get(k) or "").strip()
        if not t.startswith(prefijo) or len(t.splitlines()[0]) <= len(prefijo) + 2:
            f.append("SE8 caption.%s abre con «%s<título>»" % (k, prefijo))
        if n and n > 1 and t and not RE_PARTE1_PERFIL.search(t):
            f.append("SE8 caption.%s de la parte %d: una línea que mande al inicio («¿Llegaste por aquí? La Parte 1 está "
                     "fijada en mi perfil»): quien no vio la Parte 1 la busca ahí" % (k, n))
    sh = (cap.get("shorts") or "").splitlines()[0] if cap.get("shorts") else ""
    if "(%d/%d)" % (n or 0, M or 0) not in sh:
        f.append("SE8 el título de Shorts (1.ª línea de caption.shorts) lleva «(%d/%d)»" % (n or 0, M or 0))
    f += citas_repetidas(g, n, trabajo)
    f += revisar_resumen(g, n, M, trabajo)
    return f


def hechos_de_partes(trabajo, hasta):
    """{parte: ids de hechos y citas que usa su guion} de las partes 1…hasta−1 con guion (para SE14)."""
    base, out = os.path.dirname(os.path.abspath(trabajo)), {}
    for d in sorted(glob.glob(os.path.join(base, "parte-*"))):
        try:
            k = int(d.rsplit("-", 1)[1])
        except ValueError:
            continue
        gp = os.path.join(d, "guion.json")
        if k >= hasta or not os.path.exists(gp):
            continue
        otra = json.load(open(gp, encoding="utf-8"))
        out[k] = {h for e in otra.get("escenas") or [] for h in (e.get("hechos") or []) + [e.get("cita")] if h}
    return out


def revisar_resumen(g, n, M, trabajo):
    """SE14: la última parte de la serie lleva el resumen de toda la serie (ver RESUMEN_S) → fallas."""
    escenas = g.get("escenas") or []
    res = [(i, e) for i, e in enumerate(escenas, 1) if e.get("resumen_serie")]
    if not (n and M):
        return []
    if n < M:
        return ["SE14 el resumen de la serie va solo en la última parte (escena %d)" % i for i, _ in res]
    if len(res) != 1:
        return ["SE14 la última parte lleva UNA escena `resumen_serie: true` (hay %d): 20–30 s que repasan en orden lo que pasó en "
                "toda la serie, simple y con impacto, antes de la última cita o del cierre" % len(res)]
    i, e = res[0]
    f = []
    if e.get("acto") != 3:
        f.append("SE14 el resumen (escena %d) va en el acto 3" % i)
    s = VD.segundos_voz(VD.sin_pausas(e.get("texto") or ""))
    if not RESUMEN_S[0] <= s <= RESUMEN_S[1]:
        f.append("SE14 el resumen dura ≈ %.0f s de voz (van %d–%d): %s" % (s, *RESUMEN_S, "acórtalo a una oración por momento"
                 if s > RESUMEN_S[1] else "dale los momentos que faltan"))
    previas = hechos_de_partes(trabajo, n) if trabajo else {}
    mios = set(e.get("hechos") or [])
    if previas:
        aqui = {h for x in escenas if x is not e for h in (x.get("hechos") or []) + [x.get("cita")] if h}
        nuevos = sorted(mios - set().union(aqui, *previas.values()))
        if nuevos:
            f.append("SE14 el resumen usa %s, que ninguna parte contó antes: el resumen solo repasa (nada nuevo)" % ", ".join(nuevos))
        cubre = sorted(k for k, ids in previas.items() if mios & ids)
        pide = min(RESUMEN_PARTES_MIN, len(previas))
        if len(cubre) < pide:
            f.append("SE14 el resumen repasa %d parte(s) (%s); van ≥ %d: un hecho (su id en `hechos`) de cada momento de la serie"
                     % (len(cubre), ", ".join(map(str, cubre)) or "ninguna", pide))
    return f


FRASE_REPETIDA_PALABRAS = 8   # SE13: una frase de la voz de ≥ 8 palabras ya dicha en otra parte


def _frases_largas(g):
    out = set()
    for e in (g.get("escenas") or []) + [g.get("cierre") or {}]:
        if e.get("resumen_serie"):   # SE14: el resumen de la última parte repasa a propósito
            continue
        for fr in re.split(r"(?<=[.:?!;])\s+", VD.sin_pausas(e.get("texto") or "")):
            w = re.sub(r"[^\wáéíóúüñ ]", "", fr.lower()).split()
            if len(w) >= FRASE_REPETIDA_PALABRAS:
                out.add(" ".join(w))
    return out


def citas_repetidas(g, n, trabajo):
    """SE13 (decisión del usuario, 2026-11-06): una cita (su id) o una frase larga de la voz que ya salió en otra parte
    de la serie no se repite: quien ve las dos la oye dos veces. Compara contra las partes ANTERIORES con guion."""
    if not n or not trabajo:
        return []
    base, f = os.path.dirname(os.path.abspath(trabajo)), []
    mias_c = {e.get("cita") for e in g.get("escenas") or [] if e.get("tipo") == "cita" and e.get("cita")}
    mias_f = _frases_largas(g)
    for d in sorted(glob.glob(os.path.join(base, "parte-*"))):
        try:
            k = int(d.rsplit("-", 1)[1])
        except ValueError:
            continue
        gp = os.path.join(d, "guion.json")
        if k >= n or not os.path.exists(gp):   # contra las partes anteriores: la que llega después cambia
            continue
        otra = json.load(open(gp, encoding="utf-8"))
        for c in sorted(mias_c & {e.get("cita") for e in otra.get("escenas") or [] if e.get("tipo") == "cita"}):
            f.append("SE13 la cita %s ya sale en la parte %d: usa otra frase o cuéntalo en la voz sin citarla" % (c, k))
        for fr in sorted(mias_f & _frases_largas(otra)):
            f.append("SE13 la voz repite una frase de la parte %d («%s…»): dila distinto o quítala" % (k, fr[:60]))
    return f


def revisar_invitacion(inv, n, M, ser):
    """SE9: la invitación a la parte siguiente (cierre.invitacion) → fallas."""
    if not (n and M):
        return []
    if n >= M:
        return ["SE9 la última parte no invita a otra parte (cierre.invitacion va solo en las partes 1…M−1)"] if inv else []
    sig = ser.get("siguiente") or {}
    if not inv:
        return ["SE9 falta cierre.invitacion: tras la frase final, una oración que pida seguir la cuenta para la parte %d y "
                "diga qué cuenta («Sígueme: en la %s parte, %s…»)" % (n + 1, ORDINAL.get(n + 1, ""), (sig.get("titulo") or "").lower())]
    f = []
    plano = VD.sin_pausas(inv)
    if not RE_SIGUEME.search(plano):
        f.append("SE9 la invitación («%s») pide seguir la cuenta: «Sígueme…»" % inv[:60])
    nombra = re.search(r"\b%s\s+parte\b|\bparte\s+%s\b" % (ORDINAL.get(n + 1, "@"), CARDINAL.get(n + 1, "@")), plano, re.I)
    if not nombra:
        f.append("SE9 la invitación nombra la parte siguiente en palabras: «la %s parte» (o «la parte %s»)"
                 % (ORDINAL.get(n + 1, ""), CARDINAL.get(n + 1, "")))
    if re.search(r"\d", plano):
        f.append("SE9 la invitación no lleva cifras (ni el número de la parte en dígitos ni un dato de la parte siguiente)")
    if len(plano.split()) > INVITACION_PALABRAS:
        f.append("SE9 la invitación tiene %d palabras (≤ %d): una sola oración corta" % (len(plano.split()), INVITACION_PALABRAS))
    if not (raices(plano) & raices("%s %s %s" % (sig.get("titulo") or "", sig.get("pregunta") or "", ser.get("puente") or ""))):
        f.append("SE9 la invitación no dice qué cuenta la parte %d («%s»: %s): nombra su tema" % (n + 1, sig.get("titulo") or "", sig.get("pregunta") or ""))
    m = VD.CEBO.search(plano)
    if m:
        f.append("SE9 «%s» es cebo de interacción: la invitación solo pide seguir la cuenta" % m.group())
    return f


# ---------- digesto, estado, entregar ----------
def cmd_digesto(a):
    ruta, S = cargar_serie(a.serie)
    enc_r = os.path.join(RAIZ, S["trabajo"], "encuadre.json")
    enc = leer(enc_r) if os.path.exists(enc_r) else {}
    planes = {p.get("n"): p for p in (enc.get("serie") or {}).get("partes") or []}
    print("# Plan de la serie «%s» (versión %s, motor /%s, %d partes, paleta %s)" % (S["tema"], S.get("version"), S["motor"], len(S["partes"]), S["paleta"]))
    for p in S["partes"]:
        pl = planes.get(p["n"]) or {}
        print("\n## Parte %d · %s" % (p["n"], p["titulo"]))
        print("- Pregunta: %s" % p["pregunta"])
        print("- %s" % ("Periodo: %s–%s" % ((p.get("periodo") or {}).get("desde"), (p.get("periodo") or {}).get("hasta")) if p.get("periodo") else "Mecanismo: %s" % p.get("mecanismo")))
        for k in ("detonante", "punto_medio", "climax", "resolucion"):
            if ((pl.get("espina") or {}).get(k) or {}).get("frase"):
                print("- %s: %s" % (k, pl["espina"][k]["frase"]))
        print("- Revela: %s" % "; ".join(p.get("revelaciones") or []))
        print("- Puente: %s" % (p.get("puente") or "— (última parte)"))
    return 0


def cmd_estado(a):
    ruta, S = cargar_serie(a.serie)
    print("serie «%s» · v%s · %s · plan %s" % (S["tema"], S.get("version"), S.get("estado"), "aprobado" if S.get("plan_aprobado") else "por aprobar"))
    for p in S["partes"]:
        print("  %d/%d %-28s %-10s %s%s" % (p["n"], len(S["partes"]), p["titulo"][:28], p.get("estado") or "plan",
                                           p.get("trabajo") or "", " · publicar: sí" if publicable(S, p) else ""))
    return 0


def marcar_guion(trabajo):
    """Tras un guion aprobado (el crítico dio «pasa»), la parte pasa a «guion»: habilita publicar la anterior."""
    try:
        ruta, S = cargar_serie(trabajo)
    except SystemExit:
        return
    n = VD.serie_de(VD.estado(trabajo)).get("parte")
    for p in S["partes"]:
        if p["n"] == n and p.get("estado") in (None, "plan", "lista"):
            p["estado"] = "guion"
            guardar_serie(ruta, S)


def cmd_entregar_parte(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    ser = VD.serie_de(st)
    if not ser.get("parte"):
        return falla("%s no es una parte de una serie (serie.py parte)" % rel(trabajo))
    ruta, S = cargar_serie(trabajo)
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, S["carpeta"], "parte-%d" % ser["parte"]))
    Mm = motor_mod(S["motor"])
    rc = Mm.cmd_entregar(argparse.Namespace(trabajo=trabajo, salida=destino))
    if rc:
        return rc
    g = leer(os.path.join(destino, "guion.json")) if os.path.exists(os.path.join(destino, "guion.json")) else {}
    p = next(x for x in S["partes"] if x["n"] == ser["parte"])
    p.update(estado="entregada", ruta=rel(destino), duracion_s=g.get("duracion_s"))
    S["estado"] = "completa" if all(x.get("estado") == "entregada" for x in S["partes"]) else "en_produccion"
    guardar_serie(ruta, S)
    print("parte %d de %d entregada → %s · %s" % (ser["parte"], ser["de"], rel(destino), "se puede publicar" if publicable(S, p)
                                                 else "NO se publica todavía: espera el guion aprobado de la parte %d" % (ser["parte"] + 1)))
    return 0


# ---------- M16 ----------
def revisar_serie(S, raiz_rel=None):
    f = []
    for k in ("version", "slug", "tema", "motor", "fecha", "carpeta", "trabajo", "paleta", "musica", "partes"):
        if k not in S:
            f.append("M16 serie.json sin %s" % k)
    if S.get("motor") not in MOTORES:
        f.append("M16 motor %r (historia|explica)" % S.get("motor"))
    ps = S.get("partes") or []
    rango = PARTES_CASO if S.get("modo") == "caso" else PARTES
    if ps and not rango[0] <= len(ps) <= rango[1]:
        f.append("M16 %d partes (van %d–%d)" % (len(ps), *rango))
    for i, p in enumerate(ps, 1):
        if p.get("n") != i:
            f.append("M16 partes[%d].n = %r" % (i - 1, p.get("n")))
        if p.get("estado", "plan") not in ESTADOS_PARTE:
            f.append("M16 parte %d estado %r" % (i, p.get("estado")))
        if p.get("estado") == "entregada" and not (p.get("ruta") and os.path.isfile(os.path.join(RAIZ, p["ruta"], "guion.json"))):
            f.append("M16 parte %d entregada sin %s/guion.json" % (i, p.get("ruta")))
    return f


def cmd_check(a):
    ruta, S = cargar_serie(a.revisar)
    f = revisar_serie(S)
    for x in f:
        print("FALLA", x)
    print("[M16] %s" % ("ok" if not f else "%d fallas" % len(f)))
    return 1 if f else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revisar", metavar="SERIE", help="M16: el esquema de serie.json")
    sub = ap.add_subparsers(dest="cmd")
    q = sub.add_parser("preparar")
    q.add_argument("tema")
    q.add_argument("--partes", type=int, default=3)
    q.add_argument("--caso", action="store_true", help="modo caso: 3–8 partes de ≈ 130 s repartidas por temas (SE10–SE12)")
    q.add_argument("--motor", choices=MOTORES, default="historia")
    q.add_argument("--slug")
    q.add_argument("--paleta")
    q.add_argument("--carpeta", help="otra carpeta para la serie (pruebas y maqueta)")
    q.add_argument("--trabajo", help="otro TRABAJO para la investigación (pruebas y maqueta)")
    q.add_argument("--fixture", action="store_true")
    q = sub.add_parser("plan")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--aprobar", action="store_true", help="el usuario aprobó el plan")
    q = sub.add_parser("cobertura")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q = sub.add_parser("parte")
    q.add_argument("serie")
    q.add_argument("n", type=int)
    sub.add_parser("digesto").add_argument("serie")
    sub.add_parser("estado").add_argument("serie")
    sub.add_parser("guion-aprobado", help="el crítico aprobó el guion de la parte (habilita publicar la anterior)").add_argument("trabajo")
    q = sub.add_parser("entregar-parte")
    q.add_argument("trabajo")
    q.add_argument("--salida")
    a = ap.parse_args()
    if a.revisar:
        return cmd_check(a)
    fn = {"preparar": cmd_preparar, "plan": cmd_plan, "cobertura": cmd_cobertura, "parte": cmd_parte, "digesto": cmd_digesto,
          "estado": cmd_estado, "entregar-parte": cmd_entregar_parte,
          "guion-aprobado": lambda a: marcar_guion(os.path.abspath(a.trabajo)) or 0}.get(a.cmd)
    if not fn:
        ap.print_help()
        return 2
    return fn(a)


if __name__ == "__main__":
    sys.exit(main())
