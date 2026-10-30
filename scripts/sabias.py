#!/usr/bin/env python3
"""/sabias: un dato entregado (datos/<fecha>-<slug>/) → video vertical «¿Sabías que…?» de 20–30 s (TikTok / Reels /
Shorts) y su 4:5.

El video clásico «¿Sabías que en Guatemala…?»: el gancho con la pregunta en pantalla y la cifra animada, la tarjeta Noche
del dato con zoom a la cifra (o su escena a pantalla completa: tiempo, ranking, mapa), a lo más un visual de apoyo
(golpe, escala o explica) y el cierre en una sola pantalla: la consecuencia del dato y «Sígueme en». Escribe el MISMO
trabajo que /video: arma en TRABAJO/base/ un «hilo base» de una tarjeta (hilo.json desde dato.json, datos.json y
tuit_1.html), así que el gate del guion (V1–V5, V9, F1–F8), los tiempos, la voz, la grabación, el montaje y la revisión
salen de scripts/video.py con la estructura de /sabias enchufada (S1–S3). Guía: referencias/flujo-sabias.md.

Subcomandos (TRABAJO = sesiones/<slug>/sabias):
  preparar <slug|ultimo|carpeta> [--trabajo DIR] [--musica ID] [--fixture]
        crea TRABAJO (base/, video.json, tarjeta rearmada en Noche), elige la música y escribe digesto.md (también lo
        imprime); --fixture admite un dato en borrador y no rota contra lo producido
  digesto TRABAJO              vuelve a imprimir digesto.md
  guion TRABAJO --check        S1–S3 (estructura, gancho «¿Sabías que…?», rotación) + video.py guion (V1–V5, V9, F1–F8)
        → locucion.json
  tiempos TRABAJO              video.py tiempos → escenas.json
  entregar TRABAJO [--salida DIR]   → datos/<fecha>-<slug>/video/ (video, 4:5, caption, portadas, guion.json de entrega)
  voz | voz-falsa | descargar | escuchar | grabar | montar | revisar TRABAJO [...]   → video.py

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import contextlib
import datetime
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402

# ---- formato (decisiones del usuario, 2026-10-29): «no tiene que durar mucho», 20–30 s, siempre animado ----
OBJETIVO_S, TOL = 25, 0.2                      # V4: 20–30 s estimados
VD.DURACIONES["sabias"] = {"s": OBJETIVO_S, "tarjetas": (1, 1), "golpes": (0, 1), "tol": TOL}
ESCENAS = (2, 3)                               # gancho + la tarjeta del dato + a lo más un apoyo (más el cierre)
CIFRA_TARJETA_S = 2.5                          # la cifra de la tarjeta entra cuando la voz la dice: si llega tarde, la tarjeta queda vacía
TARJETA_TIPOS = ("tarjeta", "tiempo", "ranking", "mapa")   # la escena 2: la tarjeta del dato o su escena a pantalla completa
APOYO_TIPOS = ("golpe", "escala", "explica")   # la escena 3 (opcional): traduce la cifra a escala humana o explica por qué
PANTALLA_GANCHO = "¿Sabías que…?"              # S2: la pregunta clásica, grande en el cuadro 0
RE_ABRE = re.compile(r"^[¿«\s]*sab[ií]as\s+que\b", re.I)
GANCHO_ORACION_S = 6.5                         # «¿Sabías que en Guatemala…?» es una oración larga: ≤ 6.5 s (≈ 100 caracteres)
SABIAS = os.path.join(RAIZ, "memoria", "sabias.json")
FRASES_USADAS = 6
ORIGINALES = {}


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def falla(msg):
    print("ERROR: " + msg, file=sys.stderr)
    return 1


# ---------- el dato ----------
def resolver_dato(arg):
    """La carpeta del dato entregado: «ultimo» (memoria/datos.json), una carpeta con dato.json, o el slug en datos/."""
    if arg == "ultimo":
        regs = [d for d in leer(os.path.join(RAIZ, "memoria", "datos.json"))["datos"] if d.get("estado") in ("listo", "publicado")]
        return os.path.join(RAIZ, sorted(regs, key=lambda d: (d["fecha"], d["id"]))[-1]["ruta"]) if regs else None
    for cand in (arg, os.path.join(RAIZ, arg), os.path.join(RAIZ, "datos", arg)):
        if os.path.isfile(os.path.join(cand, "dato.json")):
            return os.path.abspath(cand)
    hits = sorted(glob.glob(os.path.join(RAIZ, "datos", "*-" + arg)))
    return hits[-1] if hits else None


def hilo_base(dato, base):
    """TRABAJO/base/: el dato como un hilo de una tarjeta (lo que video.py lee: hilo.json, datos.json, tuit_1.html)."""
    os.makedirs(base, exist_ok=True)
    d = leer(os.path.join(dato, "dato.json"))
    t = d.get("tuit") or {}
    shutil.copyfile(os.path.join(dato, "tarjeta.html"), os.path.join(base, "tuit_1.html"))
    shutil.copyfile(os.path.join(dato, "datos.json"), os.path.join(base, "datos.json"))
    if os.path.exists(os.path.join(dato, "dato.png")):
        shutil.copyfile(os.path.join(dato, "dato.png"), os.path.join(base, "tuit_1.png"))
    escribir(os.path.join(base, "hilo.json"), {
        "slug": d["slug"], "fecha": d["fecha"], "tema": d.get("tema", ""), "tesis": d.get("tesis", ""), "paleta": d["paleta"],
        "estado": d.get("estado"), "modo": "dato", "hook_tipo": d.get("hook_tipo"), "no_afirma": d.get("no_afirma") or [],
        "tuits": [{"n": 1, "imagen": "tuit_1.png", "plantilla": t.get("plantilla"), "cifra_ids": t.get("cifra_ids") or [d.get("cifra_id")],
                   "beat": "impacto", "texto": t.get("texto", ""), "alt_text": t.get("alt_text", "")}]})
    return d


# ---------- memoria: rotación y frases de los «¿Sabías que…?» anteriores ----------
def registrados(slug_actual=None):
    regs = leer(SABIAS)["sabias"] if os.path.exists(SABIAS) else []
    return sorted([r for r in regs if r.get("slug") != slug_actual], key=lambda r: (r.get("fecha", ""), r.get("id", "")))


def recientes(slug):
    """S3: el visual del gancho y el apoyo del último «¿Sabías que…?»; F7: su cierre (la misma forma que video.py)."""
    fr = [r.get("frases") or {} for r in registrados(slug)]
    return ({"familias": [], "visuales": [x.get("visual") or "cifra" for x in fr[-1:]], "apoyos": [x.get("apoyo") or "ninguno" for x in fr[-1:]]},
            {"tipos": [x.get("cierre_tipo") for x in fr[-1:] if x.get("cierre_tipo")],
             "formas": [x.get("cierre_forma") for x in fr[-VD.ROTACION_CIERRES:] if x.get("cierre_forma")],
             "mecanismos": [x["cierre_mecanismo"] for x in fr[-1:] if x.get("cierre_mecanismo")]})


def elegir_musica(paleta, forzada):
    """Como video.py, pero la pista usada hace más tiempo cuenta también los «¿Sabías que…?» y las historias."""
    if forzada:
        return VD.elegir_musica(paleta, forzada)
    cat = [x for x in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"] if x["paleta"] == paleta]
    if not cat:
        raise ValueError("el catálogo no tiene música para la paleta «%s»" % paleta)
    usos = {}
    for ruta, clave in (("videos.json", "videos"), ("historias.json", "historias"), ("sabias.json", "sabias")):
        p = os.path.join(RAIZ, "memoria", ruta)
        for v in (leer(p).get(clave) or []) if os.path.exists(p) else []:
            usos[v.get("musica")] = max(usos.get(v.get("musica"), ""), v.get("fecha", ""))
    return sorted(cat, key=lambda x: (usos.get(x["id"], ""), x["id"]))[0]


# ---------- preparar ----------
def cmd_preparar(a):
    dato = resolver_dato(a.dato)
    if not dato:
        return falla("no encuentro el dato «%s» (slug de datos/, carpeta con dato.json o «ultimo»)" % a.dato)
    d = leer(os.path.join(dato, "dato.json"))
    if d.get("estado") not in ("listo", "publicado") and not a.fixture:
        return falla("el dato está «%s»: /sabias solo convierte datos listos o publicados" % d.get("estado"))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", d["slug"], "sabias"))
    base = os.path.join(trabajo, "base")
    hilo_base(dato, base)
    try:
        musica = elegir_musica(d["paleta"], a.musica)
    except (ValueError, FileNotFoundError) as ex:
        return falla(str(ex))
    with contextlib.redirect_stdout(io.StringIO()):   # el digesto de /video no sirve aquí: se escribe el de /sabias
        rc = VD.cmd_preparar(argparse.Namespace(hilo=base, duracion="sabias", musica=musica["id"], trabajo=trabajo,
                                                permitir_borrador=True, sin_rotacion=a.fixture))
    if rc:
        return rc
    st = VD.estado(trabajo)
    rec_g, rec_c = ({"familias": [], "visuales": [], "apoyos": []}, {"tipos": [], "formas": [], "mecanismos": []}) if a.fixture \
        else recientes(d["slug"])
    st.update({"tipo": "sabias", "dato": VD.rel(dato), "fecha": datetime.date.today().isoformat(), "tema": d.get("tema", ""),
               "ganchos_recientes": rec_g, "cierres_recientes": rec_c, "fixture": bool(a.fixture)})
    escribir(os.path.join(trabajo, "video.json"), st)
    texto = digesto(trabajo, st, d, musica, a.fixture)
    open(os.path.join(trabajo, "digesto.md"), "w", encoding="utf-8").write(texto)
    print(texto)
    if any(r.get("slug") == d["slug"] for r in registrados()):
        print("AVISO este dato ya tiene su «¿Sabías que…?» (memoria/sabias.json): entregar lo reemplaza")
    print("→ %s · trabajo: %s" % (VD.rel(os.path.join(trabajo, "digesto.md")), VD.rel(trabajo)))
    return 0


def frases_usadas(slug):
    regs = registrados(slug)[-FRASES_USADAS:]
    if not regs:
        return ["- (ningún «¿Sabías que…?» anterior registrado)"]
    return ["- **%s** · gancho: «%s» · apoyo: %s · cierre (%s · %s): «%s»" % (
        r["slug"], r["frases"].get("gancho", ""), r["frases"].get("apoyo") or "ninguno", r["frases"].get("cierre_tipo"),
        r["frases"].get("cierre_forma"), r["frases"].get("cierre", "")) for r in reversed(regs)]


def digesto(trabajo, st, d, musica, fixture):
    t1 = st["tarjetas"][0]
    datos = leer(os.path.join(trabajo, "base", "datos.json"))
    cifras = {c["id"]: c for c in datos["cifras"] if c.get("veredicto") in ("verificada", "ajustada")}
    pl, dat = t1.get("plantilla"), t1.get("datos") or {}
    completas = [k for k, pls in VD.PLANTILLAS_DE.items() if pl in pls and k != "escala"]
    if "tiempo" in completas and len(VD.puntos_de(dat)) < 2:
        completas.remove("tiempo")
    if "ranking" in completas and len(VD.items_de(dat)) < VD.RANKING_TOP[0]:
        completas.remove("ranking")
    lineas = []
    for cid, c in cifras.items():
        serie = ", ".join("%s: %s" % (p.get("p"), p.get("v")) for p in (c.get("serie") or [])[-9:])
        partes = ", ".join("%s: %s" % (p.get("nombre", p.get("etiqueta", "")), p.get("valor")) for p in c.get("partes") or [])
        lineas.append("- %s%s: %s = %s %s (%s)%s%s" % (cid, " (la del dato)" if cid == d.get("cifra_id") else "", c.get("concepto", ""),
                      c.get("valor"), c.get("unidad", ""), c.get("periodo") or c.get("anio", ""),
                      " · serie: " + serie if serie else "", " · partes: " + partes if partes else ""))
        lineas += ["  - escala humana posible: %s" % eh for eh in VD.escala_humana(cid, c) if not eh.startswith("×1.0 ")]
    rec_g, rec_c = st["ganchos_recientes"], st["cierres_recientes"]
    cat_iconos = VD.iconos_catalogo()
    car = int((OBJETIVO_S - VD.COLA * 3 - VD.COLA_CIERRE) * VD.CPS)
    return "\n".join([
        "# Digesto para el «¿Sabías que…?» · %s" % d["slug"], "",
        "- Dato: %s" % d.get("dato", ""), "- Tema: %s" % d.get("tema", ""), "- Tesis: %s" % d.get("tesis", ""),
        "- Por qué impacta: %s" % d.get("por_que_impacta", ""),
        "- No afirma: %s" % "; ".join(d.get("no_afirma") or []),
        "- Paleta: %s · música: %s (%s)" % (d["paleta"], musica["id"], musica.get("ambiente", "")),
        "", "## Cifras verificadas (las únicas que la voz y la pantalla pueden decir; V2)"] + lineas + [
        "", "## La tarjeta del dato (T1)",
        "- %s · titular: %s · %s" % (pl, t1.get("titular", ""), "animada" if pl in VD.PLANTILLAS_ANIMADAS else "aparece entera"),
        "- Escena 2: `tarjeta` (zoom a la cifra que dice la voz)%s." % (
            " o a pantalla completa: " + ", ".join("`%s`" % k for k in completas) if completas else ""),
        "- Texto del tuit (contexto, no se lee): %s" % (d.get("tuit") or {}).get("texto", "").replace("\n", " "),
        "", "## Presupuesto",
        "- %d s ±%d %% (%d–%d s): gancho + escena del dato + a lo más un apoyo + cierre · voz total ≈ %d caracteres con las cifras "
        "ya en palabras (%.1f car/s)." % (OBJETIVO_S, TOL * 100, OBJETIVO_S * (1 - TOL), OBJETIVO_S * (1 + TOL), car, VD.CPS),
        "- Voz por escena: gancho %d–%d (su oración ≤ %.1f s ≈ %d caracteres) · tarjeta %d–%d · golpe %d–%d · cierre %d–%d."
        % (*VD.CARACTERES["gancho"], GANCHO_ORACION_S, int(GANCHO_ORACION_S * VD.CPS), *VD.CARACTERES["tarjeta"],
           *VD.CARACTERES["golpe"], *VD.CARACTERES["cierre"]),
        "- Ritmo: ≤ %.0f s entre eventos dentro de cada escena (la cifra, pronto)." % VD.RITMO_MAX_S,
        "", "## Estructura (la comprueba el gate S1–S3 + V1–V5, V9, F1–F8)",
        "1. **Gancho** (`tipo: gancho`, `familia: \"sabias\"`): `pantalla` = «%s» (fija, grande); `linea` (≤ %d palabras, ≤ %d "
        "caracteres) = el dato con su cifra, palabras que la voz dice; `visual` %s con `visual_datos` con respaldo (cifra "
        "admite `icono`); `verbo`; `texto` = UNA oración que abre con «¿Sabías que…» y dice «Guatemala» («¿Sabías que en "
        "Guatemala…?», «¿Sabías que el lago más visitado de Guatemala…?»)."
        % (PANTALLA_GANCHO, VD.LINEA_PALABRAS, VD.LINEA_CARACTERES, "|".join(VD.VISUALES)),
        "2. **El dato** (`tipo` %s, `tuit: 1`, `golpe` ≤ %d palabras que no repite el titular): la voz dice la cifra con su "
        "referente (el año, el antes, el de cada) y de dónde sale." % (" | ".join(TARJETA_TIPOS), VD.GOLPE_PALABRAS),
        "3. **Apoyo** (opcional, ≤ 1): `golpe` (la cifra a escala humana con `calculo`), `escala` (`de_cada: [K, N]`, `calculo`) "
        "o `explica` (una animación YA hecha de la biblioteca con el `mecanismo` del fenómeno; aquí no se escriben nuevas). "
        "Sin «pero» suelto: si la escena gira, `enlace: \"pero\"`.",
        "4. **Cierre** de una sola pantalla: `texto` = `final` (≤ %d palabras), `resumen: []`, `tipo` remate · `forma` "
        "consecuencia con `consecuencia` {mecanismo %s, quien (gente), verbo}: lo que el dato le hace a quien lo vive, no el dato "
        "otra vez; sin «sígueme» en la voz (va solo en pantalla)." % (VD.FINAL_PALABRAS, "|".join(VD.MECANISMOS)),
        "- Sin `promesa` ni `narracion` (en 25 s no hay nada que esperar). `contexto_superior` (≤ 40): el tema y el año "
        "(«Lago de Atitlán · 2025»). `caption`: tiktok, instagram, facebook y shorts (título ≤ %d + #Shorts)." % VD.SHORTS_TITULO,
        ("- Iconos (`icono` en el gancho con visual cifra o en un golpe, solo si nombra el tema): " +
         " · ".join(sorted(cat_iconos))) if cat_iconos else "- Iconos: sin biblioteca (make iconos); no uses `icono`.",
        *[x if k != 1 else "- En /sabias solo se reutiliza una animación de la biblioteca que muestre ESE mecanismo y no esté "
          "bloqueada; si ninguna lo muestra, el apoyo es un golpe o una escala." for k, x in
          enumerate(VD.lineas_animaciones(st.get("animaciones_recientes") or [], fixture))],
        "", "## Rotación (S3, F7)",
        "- %s" % ("(prueba: sin rotación)" if fixture else "Visual del gancho bloqueado: %s · apoyo bloqueado: %s · cierre "
                  "anterior: %s · formas bloqueadas: %s · mecanismo bloqueado: %s" % (
                      ", ".join(rec_g["visuales"]) or "ninguno", ", ".join(rec_g["apoyos"]) or "ninguno",
                      ", ".join(rec_c["tipos"]) or "—", ", ".join(x for x in rec_c["formas"] if x != "consecuencia") or "ninguna",
                      ", ".join(rec_c["mecanismos"]) or "ninguno")),
        "", "## Frases ya usadas (no las repitas)"] + frases_usadas(d["slug"]) + [
        "", "## Plantilla de guion.json",
        "```json",
        json.dumps({"contexto_superior": "<tema · año>", "escenas": [
            {"tipo": "gancho", "familia": "sabias", "visual": "cifra", "visual_datos": {}, "pantalla": PANTALLA_GANCHO,
             "linea": "<el dato con su cifra>", "verbo": "<verbo>", "texto": "¿Sabías que en Guatemala …?"},
            {"tipo": "tarjeta", "tuit": 1, "golpe": "<re-gancho>", "texto": "<la cifra con su referente>"},
            {"tipo": "golpe", "pantalla": "<cifra>", "linea": "<a escala humana>", "calculo": "<ids>", "verbo": "<verbo>", "texto": "…"}],
            "cierre": {"texto": "<frase final>", "final": "<frase final>", "resumen": [], "tipo": "remate", "forma": "consecuencia",
                       "consecuencia": {"mecanismo": "quien", "quien": "<gente>", "verbo": "<verbo>"}},
            "caption": {"tiktok": "…", "instagram": "…", "facebook": "…", "shorts": "<título>\n… #Shorts"}},
            ensure_ascii=False, indent=1), "```", ""])


def cmd_digesto(a):
    print(open(os.path.join(os.path.abspath(a.trabajo), "digesto.md"), encoding="utf-8").read())
    return 0


# ---------- extensión de video.py: la estructura de /sabias ----------
def aplicar_extension():
    """Enchufa en video.py lo propio de /sabias (una vez por proceso): sin narración por actos (V17–V18), sin promesa ni
    conclusiones, la oración del gancho más larga, la estructura S1 y el gancho S2–S3 en lugar de los de /video."""
    if ORIGINALES:
        return
    ORIGINALES.update(estructura=VD.validar_estructura, reglas=VD.reglas_gancho)
    VD.NARRACION_VIDEO = False
    VD.CIERRE_ANTES_S = 0.0           # el cierre es una sola pantalla: la frase final es toda su voz
    VD.GANCHO_ORACION_S = GANCHO_ORACION_S
    VD.validar_estructura = estructura
    VD.reglas_gancho = reglas_gancho


def de_video_que_no_aplica(x):
    """Las líneas de V1/V9 de /video que /sabias no hereda: la promesa, las conclusiones del cierre y la escena 2 fija
    como `tarjeta` (aquí puede ir a pantalla completa)."""
    return x.startswith(("V9 promesa", "V1 cierre.resumen", "V9 la escena 2 debe ser la tarjeta T1"))


def segundos_hasta_cifra(texto):
    """Segundos estimados de voz (ya en palabras) antes del primer número de la escena que no es un año, o None."""
    texto = VD.sin_pausas(texto or "")
    for m in re.finditer(VD.NE.NUM, texto):
        if re.fullmatch(r"(?:19|20)\d\d", m.group()):
            continue
        antes = texto[:m.start()].strip()
        VD.NE.AVISOS.clear()
        try:
            n = len(VD.NE.convertir(antes)[1]) if antes else 0
        except ValueError:
            n = len(antes)
        VD.NE.AVISOS.clear()
        return n / VD.CPS
    return None


def estructura(g, st, dur, tarjetas):
    """V1/V9 de /video sin lo que no aplica + S1: gancho → el dato (T1) → a lo más un apoyo → cierre de una pantalla."""
    f = [x for x in ORIGINALES["estructura"](g, st, dur, tarjetas) if not de_video_que_no_aplica(x)]
    escenas, cierre = g.get("escenas") or [], g.get("cierre") or {}
    tipos = [e.get("tipo") for e in escenas]
    if not ESCENAS[0] <= len(escenas) <= ESCENAS[1]:
        f.append("S1 %d escenas: van %d–%d (gancho, el dato y a lo más un apoyo) más el cierre" % (len(escenas), *ESCENAS))
    if len(escenas) >= 2 and (tipos[1] not in TARJETA_TIPOS or escenas[1].get("tuit") != 1):
        f.append("S1 la escena 2 es el dato: %s con tuit 1 (llegó %s)" % ("|".join(TARJETA_TIPOS), tipos[1]))
    if len(escenas) == 3 and tipos[2] not in APOYO_TIPOS:
        f.append("S1 la escena 3 es el apoyo: %s (llegó %s)" % ("|".join(APOYO_TIPOS), tipos[2]))
    for i, e in enumerate(escenas, 1):
        if e.get("tipo") == "explica" and not e.get("animacion"):
            f.append("S1 escena %d (explica): en /sabias solo una animación ya hecha de la biblioteca (`animacion` con su id)" % i)
    if g.get("promesa"):
        f.append("S1 sin `promesa`: en 25 s no hay nada que esperar; el dato se dice entero en las dos primeras escenas")
    if cierre.get("resumen"):
        f.append("S1 cierre.resumen va vacío ([]): el cierre es una sola pantalla (la frase final y «Sígueme en»)")
    if (cierre.get("texto") or "").strip() != (cierre.get("final") or "").strip():
        f.append("S1 cierre.texto = cierre.final: la voz del cierre es solo la frase final")
    if len(escenas) >= 2 and tipos[1] in TARJETA_TIPOS:
        s_cifra = segundos_hasta_cifra(escenas[1].get("texto"))
        if s_cifra is None or s_cifra > CIFRA_TARJETA_S:
            f.append("S1 escena 2: la voz dice la cifra a los %s (máximo %.0f s): la tarjeta la anima cuando suena y hasta entonces "
                     "queda vacía; abre con ella («Son 3 metros menos en…»)"
                     % ("%.1f s" % s_cifra if s_cifra is not None else "— (no la dice)", CIFRA_TARJETA_S))
    rec = st.get("ganchos_recientes") or {}
    apoyo = tipos[2] if len(tipos) == 3 else "ninguno"
    if apoyo != "ninguno" and apoyo in (rec.get("apoyos") or []):
        f.append("S3 el apoyo «%s» salió en el «¿Sabías que…?» anterior: usa otro (%s) o ninguno"
                 % (apoyo, "|".join(x for x in APOYO_TIPOS if x != apoyo)))
    return f


def reglas_gancho(e, voz_p, ctx):
    """S2 + las reglas de /video que aplican (R4 visual dicho, R7 «hoy», R10 cifra) sobre el gancho «¿Sabías que…?»."""
    f, av = [], []
    vis = e.get("visual") or "cifra"
    if e.get("familia") != "sabias":
        f.append("S2 familia «%s»: el gancho de /sabias es `familia: \"sabias\"`" % e.get("familia"))
    if VD._plano(e.get("pantalla")) != VD._plano(PANTALLA_GANCHO):
        f.append("S2 la pantalla del gancho es «%s» (llegó «%s»): la cifra va en la línea y el visual" % (PANTALLA_GANCHO, e.get("pantalla")))
    texto = VD.sin_pausas(e.get("texto") or "").strip()
    if not RE_ABRE.match(texto):
        f.append("S2 la voz abre con «¿Sabías que…» (llegó «%s…»)" % " ".join(texto.split()[:3]))
    o1 = re.split(r"(?<=[.?!…])\s+", texto)[0] if texto else ""
    if not VD.RE_GUATEMALA.search(o1):
        f.append("S2 la primera oración no dice «Guatemala»: «¿Sabías que en Guatemala…?»")
    if not VD.numeros_sin_anios(" ".join((e.get("linea") or "", voz_p))) and not (ctx.get("visual") or {}).get("numeros"):
        f.append("S2 la línea no trae la cifra del dato: el gancho dice el número, no lo esconde")
    if vis in (ctx.get("recientes") or {}).get("visuales", []):
        f.append("S3 el visual «%s» abrió el «¿Sabías que…?» anterior: usa otro (%s)"
                 % (vis, "|".join(x for x in VD.VISUALES if x != vis)))
    # las de /video, con una familia que admite el visual (R2 no: el referente es la línea; R6 y R9 son de /sabias)
    fam = next((k for k, vs in VD.VISUALES_DE.items() if vis in vs and k != "pregunta"), "resultado")
    rf, rav = ORIGINALES["reglas"](dict(e, familia=fam), voz_p, dict(ctx, recientes={}))
    f += [x for x in rf if not x.startswith(("R2 ", "R3 ", "R6 ", "R9 "))]
    return f, av + rav


# ---------- guion, tiempos y entrega ----------
def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension()
    return VD.cmd_guion(argparse.Namespace(trabajo=trabajo, check=True))


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension()
    rc = VD.cmd_tiempos(argparse.Namespace(trabajo=trabajo))
    if rc:
        return rc
    ruta = os.path.join(trabajo, "escenas.json")
    E = leer(ruta)
    E["tipo"] = "sabias"
    escribir(ruta, E)
    return 0


def cmd_entregar(a):
    """Copia el video a datos/<fecha>-<slug>/video/ (o --salida) con el guion.json de entrega de video.py más lo de
    /sabias (tipo, dato, apoyo). Una voz falsa solo se entrega con --salida."""
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    if not os.path.exists(os.path.join(trabajo, "audio", "creditos.json")) and not a.salida:
        return falla("sin audio/creditos.json: la voz no salió de ElevenLabs (una voz falsa solo se entrega con --salida)")
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, st["dato"], "video"))
    rc = VD.cmd_entregar(argparse.Namespace(trabajo=trabajo, salida=destino))
    if rc:
        return rc
    ruta = os.path.join(destino, "guion.json")
    ent, g = leer(ruta), leer(os.path.join(trabajo, "guion.json"))
    tipos = [e.get("tipo") for e in g.get("escenas") or []]
    ent.update({"id": "sabias-%s" % st["slug"], "tipo": "sabias", "fecha": st["fecha"], "tema": st.get("tema", ""),
                "dato": st["dato"], "apoyo": tipos[2] if len(tipos) == 3 else None})
    escribir(ruta, ent)
    print("→ %s (%s s)" % (VD.rel(destino), ent.get("duracion_s")))
    return 0


REENVIO = ("voz", "voz-falsa", "descargar", "escuchar", "grabar", "montar", "revisar")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in REENVIO:
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video.py")] + sys.argv[1:], cwd=RAIZ).returncode
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("preparar")
    q.add_argument("dato", help="slug de datos/, carpeta con dato.json o «ultimo»")
    q.add_argument("--trabajo")
    q.add_argument("--musica")
    q.add_argument("--fixture", action="store_true", help="pruebas: admite un dato en borrador y no rota contra lo producido")
    sub.add_parser("digesto").add_argument("trabajo")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    sub.add_parser("tiempos").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida")
    a = p.parse_args()
    return {"preparar": cmd_preparar, "digesto": cmd_digesto, "guion": cmd_guion, "tiempos": cmd_tiempos,
            "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
