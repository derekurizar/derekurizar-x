#!/usr/bin/env python3
"""Auditoría de un plan de gobierno: inventario de compromisos → evaluación por eje → puntaje.

Variante «auditoría» de /investigacion (args.auditoria). El inventario
(`compromisos.json`, uno por plan en investigacion/auditorias/<plan>/) lista cada
compromiso con su id (S1-02, F-19), semilla, eje, medida (meta|monto|hito|tendencia|
declarativo), meta {valor, unidad, base, sentido, techo?, nivel?}, monto_mq y
espejo_de (el mismo compromiso repetido en otra semilla: se evalúa una vez).

Cada investigador escribe <sesion>/evaluacion_<eje>.json:
  {"eje", "corte": "YYYY-MM-DD", "items": [{"id", "estado", "medida_usada": meta|monto|hito,
    "observado", "base_obs", "base_fecha", "fecha_dato", "cifra_ids": [], "resumen" (≤260), "fuente" (≤90),
    "evidencia": [{"url", "cita", "archivo_local"}], "nota"}]}
y el verificador añade a verificacion_<eje>.json la clave
  "compromisos": [{"id", "veredicto": confirmado|corregido|sin_sustento, "estado"?, "observado"?,
    "base_obs"?, "base_fecha"?, "medida_usada"?, "fecha_dato"?, "url_2", "nota"}].

Atribución (regla para todo compromiso): solo cuenta lo que pasó en el mandato.
  fecha_dato  fecha del dato o del hecho; debe caer dentro del mandato (≥ su inicio).
  base_fecha  desde cuándo se mide el cambio. Metas: la línea base es el nivel de 2023 (o el primer dato del
          mandato), nunca uno anterior a 2023, y nunca la base del plan; los conteos acumulados empiezan en el
          mandato (base_fecha "2024-01", base_obs null o 0). Montos: ejecución desde el inicio del mandato.
          Sin línea base válida, el compromiso queda no_verificable.

Puntaje (método mixto, declarado en el informe):
  meta    avance = observado ÷ meta (acumulativa), (observado − base_obs) ÷ meta (incremento «X más» con base_obs)
          o (observado − base_obs) ÷ (meta − base_obs) (nivel: tasa, cobertura, base en el plan o sentido baja; base_obs
          es el nivel de 2023 o del inicio del mandato; la base del plan no se usa). techo: 100 si observado ≤ meta.
          Meta que ya se cumplía al inicio del mandato: no atribuible (cuenta 0) si se sostiene, retroceso si se pierde.
  monto   avance = ejecutado (millones de Q, en `observado`) ÷ monto_mq.
  tendencia  cambio relativo en el sentido deseado frente a base_obs: ≥10 % → 100, >0 → 50, 0 → 0,
          en contra → 0 (retroceso).
  hito    por estado: cumplido 100 · en_proceso 50 · anunciado 25 · no_iniciado / incumplido / retroceso 0.
  no_atribuible: hay dato, pero lo que existe o la meta ya se cumplía antes del mandato y no hay un hecho del
  mandato que lo amplíe (programa o norma anterior que solo sigue operando; meta ya alcanzada en 2023): cuenta 0,
  y entra en el avance «con dato» (no resta en aud-c08).
  Tope 100. no_verificable (sin dato oficial, sin línea base atribuible o con su cifra sin confirmar)
  cuenta 0: lo que no se puede comprobar no se da por logrado. Se publica aparte el avance «con dato»
  (solo los verificables) y los puntos que restan los no verificables (aud-c08).
  Un número (meta, monto, tendencia) solo vale si alguna de sus cifra_ids es verificada|ajustada; si no,
  el compromiso queda no_verificable. Semilla = promedio simple de sus compromisos (los espejos cuentan
  en las dos); global = promedio de las semillas (ejes 1–10 del plan); el marco fiscal (F) se informa aparte.
  Retroceso: peor que la línea base de 2023, aunque sea por poco; exactamente igual = sin iniciar.
  No atribuible: existe_desde (fecha anterior al mandato) obligatorio; una meta ya cumplida en 2023 lo es sola.
  --validar coteja observado y base_obs con los valores de sus cifra_ids (redondeo, escala, operación simple o
  suma de hasta 4: acumulados del mandato); si no, declara calculo_observado / calculo_base_obs.
  Ritmo (metas acumulativas y montos): avance frente al % del mandato transcurrido a la fecha del dato.

Uso:
  python3 scripts/auditoria.py --inventario <compromisos.json> --ejes          ejes en JSON (para args)
  python3 scripts/auditoria.py <sesion> --eje <eje>                           compromisos del eje (agentes)
  python3 scripts/auditoria.py <sesion> --plantilla <eje>                     esqueleto de evaluacion_<eje>.json
  python3 scripts/auditoria.py <sesion> --validar <eje> [--verificacion]      valida la evaluación (y la revisión)
  python3 scripts/auditoria.py <sesion> --calcular                            auditoria.json + hallazgos_aud/verificacion_aud
  python3 scripts/auditoria.py <sesion> --resumen [--para guionista|redactor] digesto del puntaje
  python3 scripts/auditoria.py <sesion> --insertar <informe.json>             expande las páginas "auto" (fichas con hallazgo,
                                                                            fuente y cálculo de cada barra) y remite cada gráfico a ellas
  python3 scripts/auditoria.py <sesion> --justificar <informe.json>           gate J1–J5: ninguna barra sin de dónde sale
Salida: 0 ok · 1 fallo · 2 uso incorrecto.
"""
import argparse
import calendar
import datetime as dt
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import verificacion as VM  # noqa: E402  (coincide, derivable, evaluar: el mismo cotejo numérico que la verificación)
ESTADOS = ["cumplido", "en_proceso", "anunciado", "no_iniciado", "incumplido", "retroceso", "no_atribuible", "no_verificable"]
ETIQUETA = {"cumplido": "Cumplido", "en_proceso": "En proceso", "anunciado": "Anunciado", "no_iniciado": "Sin iniciar",
            "incumplido": "Incumplido", "retroceso": "Retroceso", "no_atribuible": "No atribuible", "no_verificable": "No verificable"}
PUNTOS_HITO = {"cumplido": 100, "en_proceso": 50, "anunciado": 25, "no_iniciado": 0, "incumplido": 0, "retroceso": 0, "no_atribuible": 0}
MEDIDAS = ["meta", "monto", "hito"]
VEREDICTOS_OK = {"verificada", "ajustada"}
VEREDICTOS_COMP = {"confirmado", "corregido", "sin_sustento"}
UMBRAL_TENDENCIA = 0.10
TOL_IGUAL = 1e-9  # «exactamente igual» (sin iniciar): |cambio| por debajo de esto; cualquier empeoramiento mayor es retroceso
PREFIJO_AUD = "aud"
MESES_AUD = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FUENTE_AUD = "Cálculo propio sobre el Plan de Gobierno y fuentes oficiales"


RE_PREVIO = re.compile(r"anterior al mandato|gobierno anterior|heredad[oa]|antes del mandato|antes de este gobierno", re.I)
AVISOS_VALIDAR = []


class Uso(Exception):
    pass


def leer(ruta, defecto=None):
    if not os.path.exists(ruta):
        if defecto is not None:
            return defecto
        raise Uso("no existe %s" % ruta)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def escribir(ruta, obj):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def inventario_de(sesion, ruta=None):
    ruta = ruta or os.path.join(sesion, "compromisos.json")
    inv = leer(ruta)
    por_id = {c["id"]: c for c in inv["compromisos"]}
    if len(por_id) != len(inv["compromisos"]):
        raise Uso("ids repetidos en %s" % ruta)
    for c in inv["compromisos"]:
        if c.get("espejo_de") and c["espejo_de"] not in por_id:
            raise Uso("%s: espejo_de %s no existe" % (c["id"], c["espejo_de"]))
    return inv, por_id


def fmt(v, dec=None):
    if v is None:
        return "—"
    if isinstance(v, float) and dec is None:
        # Los decimales de la fuente hasta 2 (102.13 y 102.11 nunca se imprimen igual); miles sin decimales.
        dec = 0 if (v.is_integer() or abs(v) >= 1000) else min(2, max(1, VM.decimales(v)))
    if dec is None:
        dec = 0
    s = "{:,.{d}f}".format(v, d=dec)
    return s.replace("-", "−")


def fin_de(fecha):
    """'2025' → 2025-12-31 · '2025-06' → 2025-06-30 · '2025-06-15' tal cual."""
    s = str(fecha or "").strip()
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$", s)
    if not m:
        return None
    a, mes, dia = int(m.group(1)), m.group(2), m.group(3)
    if not mes:
        return dt.date(a, 12, 31)
    mes = int(mes)
    if not dia:
        return dt.date(a, mes, calendar.monthrange(a, mes)[1])
    return dt.date(a, mes, int(dia))


def inicio_de(fecha):
    """'2025' → 2025-01-01 · '2025-06' → 2025-06-01 · '2025-06-15' tal cual."""
    f = fin_de(fecha)
    if not f:
        return None
    s = str(fecha).strip()
    return dt.date(f.year, 1, 1) if len(s) == 4 else (dt.date(f.year, f.month, 1) if len(s) == 7 else f)


def inicio_mandato(inv):
    return dt.date.fromisoformat(inv["plan"]["mandato"]["inicio"])


def base_min(ini):
    """Línea base más antigua admitida: el 1 de enero del año anterior al inicio del mandato (2023 para 2024)."""
    return dt.date(ini.year - 1, 1, 1)


def problema_atribucion(it, c, ini):
    """Motivo por el que el dato no mide a este gobierno (o None). Común a --validar y a puntuar."""
    med = it.get("medida_usada")
    m = c.get("meta") or {}
    fd = fin_de(it.get("fecha_dato"))
    if fd and fd < ini:
        return "dato de %s, anterior al mandato" % it.get("fecha_dato")
    if med == "hito" or (med == "meta" and m.get("techo")):
        return None
    bf = it.get("base_fecha")
    b0 = inicio_de(bf)
    if not b0:
        return "sin base_fecha (desde cuándo se mide el cambio)"
    if med == "monto" and b0 < dt.date(ini.year, ini.month, 1):
        return "ejecución contada desde %s, antes del mandato" % bf
    if med == "meta" and b0 < base_min(ini):
        return "línea base de %s: anterior a %d, el cambio no es atribuible al gobierno" % (bf, base_min(ini).year)
    if fd and b0 > fd:
        return "base_fecha %s posterior a fecha_dato %s" % (bf, it.get("fecha_dato"))
    if med == "meta" and m.get("base") not in (None, 0) and not es_numero(it.get("base_obs")):
        return "sin línea base de 2023 o del inicio del mandato (la base del plan no se usa)"
    return None


def transcurrido(inv, fecha):
    ini = dt.date.fromisoformat(inv["plan"]["mandato"]["inicio"])
    fin = dt.date.fromisoformat(inv["plan"]["mandato"]["fin"])
    f = fecha if isinstance(fecha, dt.date) else fin_de(fecha)
    if not f:
        return None
    return max(0.0, min(1.0, (f - ini).days / float((fin - ini).days)))


def es_numero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ---------------------------------------------------------------- consulta por eje
def cmd_eje(sesion, eje):
    inv, por_id = inventario_de(sesion)
    ej = next((e for e in inv["ejes"] if e["id"] == eje), None)
    if not ej:
        raise Uso("eje %s no existe (hay %s)" % (eje, ", ".join(e["id"] for e in inv["ejes"])))
    corte = inv["plan"]["mandato"]
    print("# eje %s · %s · %d compromisos · mandato %s → %s" % (eje, ej["nombre"], len(ej["compromisos"]), corte["inicio"], corte["fin"]))
    for cid in ej["compromisos"]:
        c = por_id[cid]
        if c.get("espejo_de"):
            print("\n%s · %s · ESPEJO de %s (se evalúa allí; NO lo incluyas en evaluacion_%s.json)" % (cid, c["corto"], c["espejo_de"], eje))
            continue
        print("\n%s · %s · medida %s · p. %s" % (cid, c["corto"], c["medida"], c["pagina"]))
        print("  plan: %s" % c["texto"])
        if c.get("meta"):
            m = c["meta"]
            extra = [x for x in ("techo", "nivel") if m.get(x)]
            print("  meta: %s %s · base %s · sentido %s%s" % (fmt(m["valor"]) if m["valor"] is not None else "(sin cifra: tendencia)", m["unidad"],
                                                            fmt(m["base"]) if m.get("base") is not None else "— (si es un nivel, da base_obs)", m["sentido"],
                                                            " · " + ", ".join(extra) if extra else ""))
        if c.get("monto_mq") is not None:
            print("  monto prometido: Q%s millones (2024–2027)" % fmt(c["monto_mq"]))
        if c.get("indicador"):
            print("  indicador: %s" % c["indicador"])
        if c.get("fuentes_sugeridas"):
            print("  fuentes: %s" % "; ".join(c["fuentes_sugeridas"]))
        if c.get("nota"):
            print("  nota: %s" % c["nota"])
    return 0


def medida_defecto(c):
    if c["medida"] in ("hito", "declarativo"):
        return "hito"
    if c["medida"] == "tendencia":
        return "meta"
    return c["medida"]


def cmd_plantilla(sesion, eje):
    inv, por_id = inventario_de(sesion)
    ej = next((e for e in inv["ejes"] if e["id"] == eje), None)
    if not ej:
        raise Uso("eje %s no existe" % eje)
    items = []
    for cid in ej["compromisos"]:
        c = por_id[cid]
        if c.get("espejo_de"):
            continue
        items.append({"id": cid, "estado": "", "medida_usada": medida_defecto(c), "observado": None, "base_obs": None, "base_fecha": "",
                      "fecha_dato": "", "cifra_ids": [], "resumen": "", "fuente": "", "evidencia": [{"url": "", "cita": "", "archivo_local": ""}], "nota": ""})
    print(json.dumps({"eje": eje, "corte": "", "items": items}, ensure_ascii=False, indent=1))
    return 0


# ---------------------------------------------------------------- validación
def cifras_de_sesion(sesion):
    cif, ver = {}, {}
    for ruta in sorted(glob.glob(os.path.join(sesion, "hallazgos_*.json"))):
        for c in leer(ruta).get("cifras", []):
            cif[c["id"]] = c
    for ruta in sorted(glob.glob(os.path.join(sesion, "verificacion_*.json"))):
        v = leer(ruta)
        for it in (v.get("items") or v.get("cifras") or []):
            ver[it["id"]] = it
    return cif, ver


def valores_cifras(ids, cif, ver):
    """[(valor, tolerancia)] que respaldan un observado: valor_final (o valor), puntos de serie y partes de sus cifras."""
    out = []
    for x in ids or []:
        c, v = cif.get(x) or {}, (ver or {}).get(x) or {}
        vf = v.get("valor_final", c.get("valor"))
        serie = v.get("serie_final") or c.get("serie") or []
        partes = v.get("partes_final") or c.get("partes") or []
        for n in [vf] + [p.get("v") for p in serie] + [p.get("valor") for p in partes]:
            if es_numero(n):
                out.append((float(n), 0.0))
    return out


def respaldado(valor, ids, cif, ver, calculo=None, ini=None):
    """True si `valor` es (redondeado) uno de los valores de sus cifras, a cualquier escala, sale de dos de ellos con
    una operación simple, es la suma de sus valores titulares, o lo da `calculo` (operación declarada)."""
    if not es_numero(valor):
        return True
    if calculo:
        r = VM.evaluar(calculo)
        return r is not None and VM.coincide(float(valor), [(r, 0.5 * 10 ** (-VM.decimales(float(valor))))], escalas=(1,))
    vals = valores_cifras(ids, cif, ver)
    if not vals:
        return True
    if VM.coincide(float(valor), vals) or VM.derivable(float(valor), vals, max_n=40):
        return True
    # Sumas (acumulados del mandato): los valores titulares y los puntos de serie desde el año de inicio, de 2 a 4.
    import itertools
    cand = []
    for x in ids or []:
        c, v = cif.get(x) or {}, (ver or {}).get(x) or {}
        n = v.get("valor_final", c.get("valor"))
        if es_numero(n):
            cand.append(float(n))
        for pt in v.get("serie_final") or c.get("serie") or []:
            m = re.match(r"(\d{4})", str(pt.get("p")))
            if m and ini and int(m.group(1)) >= ini.year and es_numero(pt.get("v")):
                cand.append(float(pt["v"]))
    cand = cand[:16]  # sin quitar repetidos: 11 M en 2025 y 11 M en 2026 son dos sumandos
    for k in range(2, min(4, len(cand)) + 1):
        for comb in itertools.combinations(cand, k):
            if VM.coincide(float(valor), [(sum(comb), 0.0)]):
                return True
    return False


def validar_item(it, c, cif, F, ini, ver=None):
    cid = it.get("id")
    est = it.get("estado")
    if est not in ESTADOS:
        F.append("%s: estado %r (debe ser %s)" % (cid, est, "|".join(ESTADOS)))
        return
    med = it.get("medida_usada")
    if med not in MEDIDAS:
        F.append("%s: medida_usada %r (meta|monto|hito)" % (cid, med))
        return
    if med == "meta" and not c.get("meta"):
        F.append("%s: medida meta pero el plan no le fija meta numérica (usa monto o hito)" % cid)
    if med == "monto" and c.get("monto_mq") is None:
        F.append("%s: medida monto pero el plan no le asigna monto (usa meta o hito)" % cid)
    if len(str(it.get("resumen") or "")) < 20 or len(str(it.get("resumen") or "")) > 260:
        F.append("%s: resumen de 20–260 caracteres (lleva %d)" % (cid, len(str(it.get("resumen") or ""))))
    if est == "no_verificable":
        return
    if est == "no_atribuible":
        ed = inicio_de(it.get("existe_desde"))
        if not ed:
            F.append("%s: no_atribuible exige existe_desde (YYYY | YYYY-MM | YYYY-MM-DD: desde cuándo existe o se cumplía) y nota con la fuente" % cid)
        elif ed >= ini:
            F.append("%s: existe_desde %s no es anterior al mandato (%s): si es del mandato, el estado no es no_atribuible" % (cid, it.get("existe_desde"), ini.isoformat()))
    if not str(it.get("fuente") or "").strip() or len(str(it.get("fuente"))) > 90:
        F.append("%s: fuente corta (1–90) obligatoria" % cid)
    ev = [e for e in (it.get("evidencia") or []) if isinstance(e, dict) and e.get("url") and e.get("cita")]
    if not ev:
        F.append("%s: evidencia [{url, cita, archivo_local}] obligatoria salvo no_verificable" % cid)
    if not fin_de(it.get("fecha_dato")):
        F.append("%s: fecha_dato YYYY | YYYY-MM | YYYY-MM-DD obligatoria (fecha del dato o del hecho)" % cid)
    pa = problema_atribucion(it, c, ini) if est != "no_atribuible" else None
    if pa and med == "hito" and pa.endswith("anterior al mandato"):
        F.append("%s: %s. Un hito vale por un hecho del mandato: usa su fecha; si solo sigue operando lo que ya existía, "
                 "estado no_atribuible con existe_desde (si lo único del mandato es un anuncio, anunciado)" % (cid, pa))
    elif pa:
        F.append("%s: %s. Busca el dato de %d o del inicio del mandato; si no existe, estado no_verificable" % (cid, pa, base_min(ini).year))
    if med in ("meta", "monto"):
        if not es_numero(it.get("observado")):
            F.append("%s: medida %s exige observado numérico (o estado no_verificable)" % (cid, med))
        if not it.get("cifra_ids"):
            F.append("%s: medida %s exige cifra_ids (la cifra que respalda el observado)" % (cid, med))
        m = c.get("meta") or {}
        necesita_base = med == "meta" and (c["medida"] == "tendencia" or m.get("base") not in (None, 0) or (m.get("sentido") == "baja" and not m.get("techo")))
        if necesita_base and not es_numero(it.get("base_obs")):
            F.append("%s: esta meta exige base_obs (nivel de 2023 o del inicio del mandato, con su cifra)" % cid)
    for x in it.get("cifra_ids") or []:
        if x not in cif:
            F.append("%s: cifra %s no está en ningún hallazgos_*.json" % (cid, x))
    if med in ("meta", "monto") and it.get("cifra_ids"):
        for k in ("observado", "base_obs"):
            if es_numero(it.get(k)) and not respaldado(it[k], it["cifra_ids"], cif, ver, it.get("calculo_" + k), ini):
                F.append("%s: %s %s no es un valor de sus cifra_ids (%s) ni sale de ellos con una operación simple o su suma; "
                         "copia el valor de la cifra o declara calculo_%s con la operación" % (cid, k, it[k], ", ".join(it["cifra_ids"]), k))
    texto = "%s %s" % (it.get("resumen") or "", it.get("nota") or "")
    if med == "hito" and est in ("cumplido", "en_proceso", "anunciado") and RE_PREVIO.search(texto):
        AVISOS_VALIDAR.append("%s: hito %s cuyo texto habla de algo anterior al mandato («%s»): fecha_dato debe ser la de un hecho del mandato; "
                              "si solo sigue operando lo que ya existía, el estado es no_atribuible (nota «existe desde …»)" % (cid, est, RE_PREVIO.search(texto).group(0)))


def cmd_validar(sesion, eje, con_verificacion):
    inv, por_id = inventario_de(sesion)
    ej = next((e for e in inv["ejes"] if e["id"] == eje), None)
    if not ej:
        raise Uso("eje %s no existe" % eje)
    ev = leer(os.path.join(sesion, "evaluacion_%s.json" % eje))
    cif, ver_cif = cifras_de_sesion(sesion)
    F = []
    esperados = [cid for cid in ej["compromisos"] if not por_id[cid].get("espejo_de")]
    vistos = [it.get("id") for it in ev.get("items", [])]
    falt = [x for x in esperados if x not in vistos]
    sobr = [x for x in vistos if x not in esperados]
    rep = sorted({x for x in vistos if vistos.count(x) > 1})
    if falt:
        F.append("faltan compromisos: %s" % ", ".join(falt))
    if sobr:
        F.append("compromisos ajenos al eje o espejos: %s" % ", ".join(sobr))
    if rep:
        F.append("compromisos repetidos: %s" % ", ".join(rep))
    if not fin_de(ev.get("corte")):
        F.append("corte (fecha de la evaluación) obligatorio")
    for it in ev.get("items", []):
        if it.get("id") in por_id:
            validar_item(it, por_id[it["id"]], cif, F, inicio_mandato(inv), ver_cif)
    if con_verificacion:
        v = leer(os.path.join(sesion, "verificacion_%s.json" % eje))
        rev = {r.get("id"): r for r in v.get("compromisos", [])}
        sin = [x for x in esperados if x not in rev]
        if sin:
            F.append("verificacion_%s.json: compromisos sin revisar: %s" % (eje, ", ".join(sin)))
        for cid, r in rev.items():
            if r.get("veredicto") not in VEREDICTOS_COMP:
                F.append("revisión %s: veredicto %r (confirmado|corregido|sin_sustento)" % (cid, r.get("veredicto")))
            if r.get("veredicto") == "corregido" and not any(k in r for k in ("estado", "observado", "base_obs", "base_fecha", "medida_usada", "fecha_dato", "resumen", "existe_desde")):
                F.append("revisión %s: corregido sin campos corregidos" % cid)
            if r.get("estado") and r["estado"] not in ESTADOS:
                F.append("revisión %s: estado %r" % (cid, r["estado"]))
            if r.get("veredicto") == "corregido" and r.get("estado") == "no_atribuible":
                ed = inicio_de(r.get("existe_desde"))
                if not ed or ed >= inicio_mandato(inv):
                    F.append("revisión %s: no_atribuible exige existe_desde anterior al mandato (%s)" % (cid, inicio_mandato(inv).isoformat()))
            base_it = next((x for x in ev.get("items", []) if x.get("id") == cid), {})
            ids_r = r.get("cifra_ids") or base_it.get("cifra_ids")
            for k in ("observado", "base_obs"):
                if r.get("veredicto") == "corregido" and es_numero(r.get(k)) and ids_r and not respaldado(r[k], ids_r, cif, ver_cif, r.get("calculo_" + k), inicio_mandato(inv)):
                    F.append("revisión %s: %s corregido %s no es un valor de sus cifra_ids (%s) ni sale de ellos; declara calculo_%s" % (cid, k, r[k], ", ".join(ids_r), k))
    n = len(ev.get("items", []))
    est = {}
    for it in ev.get("items", []):
        est[it.get("estado")] = est.get(it.get("estado"), 0) + 1
    for a_ in AVISOS_VALIDAR:
        print("AVISO " + a_)
    if F:
        print("FALLA evaluacion_%s.json (%d de %d compromisos):" % (eje, n, len(esperados)))
        for f in F:
            print(" - " + f)
        return 1
    print("OK evaluacion_%s.json: %d compromisos · %s%s" % (eje, n, " · ".join("%s %d" % (k, v) for k, v in sorted(est.items())), " · revisión completa" if con_verificacion else ""))
    return 0


# ---------------------------------------------------------------- cálculo
def puntuar(c, it, inv, cif_ok):
    """Devuelve el registro final de un compromiso evaluado."""
    r = {"id": c["id"], "corto": c["corto"], "semilla": c["semilla"], "eje": c["eje"], "medida_plan": c["medida"]}
    est = it.get("estado") if it else "no_verificable"
    med = (it or {}).get("medida_usada") or medida_defecto(c)
    obs, base_obs = (it or {}).get("observado"), (it or {}).get("base_obs")
    r.update({"estado_declarado": est, "medida_usada": med, "observado": obs, "base_obs": base_obs,
              "base_fecha": (it or {}).get("base_fecha") or "", "fecha_dato": (it or {}).get("fecha_dato") or "", "cifra_ids": (it or {}).get("cifra_ids") or [],
              "resumen": (it or {}).get("resumen") or "", "fuente": (it or {}).get("fuente") or "",
              "evidencia": (it or {}).get("evidencia") or [], "revision": (it or {}).get("_revision")})
    motivo = None
    if est == "no_atribuible":
        # Existe o se cumplía antes del mandato y no hay un hecho del mandato que lo amplíe: hay dato, pero no es logro del gobierno.
        r.update({"estado": "no_atribuible", "avance": 0.0, "puntos": 0.0, "ritmo": None, "regla": "no_atribuible",
                  "motivo": "no atribuible: " + re.sub(r"^no (es )?atribuible( al mandato)?:?\s*", "", (it.get("nota") or "").strip(), flags=re.I)})
        return r
    if not it:
        motivo = "sin evaluación"
    elif est == "no_verificable":
        motivo = (it.get("nota") or "sin información pública suficiente")
    elif med in ("meta", "monto"):
        if not es_numero(obs):
            motivo = "sin dato numérico"
        elif not any(x in cif_ok for x in r["cifra_ids"]):
            motivo = "su cifra no se confirmó (" + ", ".join(r["cifra_ids"]) + ")"
    if not motivo:
        motivo = problema_atribucion(it, c, inicio_mandato(inv))
    if motivo:
        # Sin dato comprobable no hay logro: cuenta 0 (el motivo va en la ficha y en el anexo).
        r.update({"estado": "no_verificable", "avance": 0.0, "puntos": 0.0, "motivo": motivo, "ritmo": None, "regla": "sin_dato"})
        return r
    avance = None
    bruto = None
    if med == "hito":
        r["estado"] = est
        r["puntos"] = PUNTOS_HITO[est]
        r["avance"] = r["puntos"]
        r["ritmo"] = None
        r["regla"] = "hito"
        return r
    m = c.get("meta") or {}
    if med == "monto":
        bruto = 100.0 * obs / c["monto_mq"]
        r["regla"] = "monto"
    elif c["medida"] == "tendencia":
        base = base_obs
        signo = 1 if m.get("sentido") == "sube" else -1
        cambio = signo * (obs - base) / abs(base) if base else 0.0
        r["cambio_rel"] = round(100 * cambio, 2 if abs(100 * cambio) < 1 else 1)  # «−0.02%», nunca «−0.0%»
        r["regla"] = "tendencia"
        if cambio >= UMBRAL_TENDENCIA:
            r.update({"estado": "cumplido", "puntos": 100})
        elif cambio > 0:
            r.update({"estado": "en_proceso", "puntos": 50})
        elif abs(cambio) < TOL_IGUAL:  # exactamente igual que en la base: sin iniciar; peor, aunque sea por poco: retroceso
            r.update({"estado": "no_iniciado", "puntos": 0})
        else:
            r.update({"estado": "retroceso", "puntos": 0})
        r["avance"] = r["puntos"]
        r["ritmo"] = None
        return r
    elif m.get("techo"):
        ok = obs <= m["valor"]
        r.update({"estado": "cumplido" if ok else "incumplido", "puntos": 100 if ok else 0, "avance": 100 if ok else 0, "ritmo": None, "regla": "techo"})
        return r
    else:
        # La línea base es el nivel de 2023 o del inicio del mandato (base_obs), nunca la del plan.
        # Metas de cambio relativo (base 0 en el plan): observado ya es el cambio desde base_fecha.
        base = base_obs if es_numero(base_obs) and m.get("base") != 0 else None
        signo = -1 if m.get("sentido") == "baja" else 1
        # Nivel (a alcanzar: tasa, cobertura, «cero muertes», base en el plan, nivel: true) frente a incremento
        # (conteo de «X más» desde el inicio: con base_obs, el avance es lo sumado en el mandato ÷ meta).
        nivel = m.get("base") not in (None, 0) or m.get("nivel") or m.get("sentido") == "baja" or str(m.get("unidad", "")).startswith("%")
        if base is not None and not nivel:
            bruto = 100.0 * (obs - base) / m["valor"] if m["valor"] else 0.0
            r["base_usada"] = base
            r["regla"] = "incremento"
        elif base is not None and m.get("valor") is not None and signo * (base - m["valor"]) >= 0:
            # La meta ya se cumplía al inicio del mandato: no es un logro del gobierno (regla de atribución).
            # Sostenerla no suma (no atribuible, cuenta 0); perderla es retroceso (también 0).
            ok = signo * (obs - m["valor"]) >= 0
            nota = "la meta ya se cumplía al inicio del mandato (%s en %s); %s" % (
                fmt(float(base)), r["base_fecha"] or "2023", "se sostiene, pero no es atribuible al gobierno" if ok else "se perdió")
            r.update({"base_usada": base, "estado": "no_atribuible" if ok else "retroceso", "puntos": 0.0, "avance": 0.0, "ritmo": None,
                      "regla": "ya_cumplida", "nota_base": nota})
            if ok:
                r["motivo"] = "no atribuible: " + nota
            return r
        elif base is None:
            bruto = 100.0 * obs / m["valor"] if m["valor"] else 0.0
            r["base_usada"] = None
            r["regla"] = "acumulada"
        else:
            bruto = 100.0 * (obs - base) / (m["valor"] - base)
            r["base_usada"] = base
            r["regla"] = "nivel"
    avance = max(0.0, min(100.0, bruto))
    r["avance_bruto"] = round(bruto, 1)
    r["avance"] = round(avance, 1)
    r["puntos"] = r["avance"]
    if bruto >= 100:
        r["estado"] = "cumplido"
    elif bruto > 0:
        r["estado"] = "en_proceso"
    elif bruto < -TOL_IGUAL:  # peor que la línea base de 2023, aunque sea por poco
        r["estado"] = "retroceso"
    else:  # exactamente igual que la línea base
        r["estado"] = "no_iniciado"
    if not m.get("nivel"):
        t = transcurrido(inv, r["fecha_dato"])
        if t:
            r["esperado"] = round(100 * t, 1)
            q = avance / r["esperado"] if r["esperado"] else 0
            r["ritmo"] = "en ritmo" if q >= 0.9 else ("rezagado" if q >= 0.5 else "muy rezagado")
        else:
            r["ritmo"] = None
    else:
        r["ritmo"] = None
    return r


def promedio(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 1) if xs else None


def cmd_calcular(sesion, salida_json=True):
    inv, por_id = inventario_de(sesion)
    cif, ver = cifras_de_sesion(sesion)
    cif_ok = {k for k, v in ver.items() if v.get("veredicto") in VEREDICTOS_OK}
    evals, faltan, cortes = {}, [], []
    for e in inv["ejes"]:
        ruta = os.path.join(sesion, "evaluacion_%s.json" % e["id"])
        if not os.path.exists(ruta):
            faltan.append(e["id"])
            continue
        ev = leer(ruta)
        if ev.get("corte"):
            cortes.append(ev["corte"])
        rev = {r.get("id"): r for r in leer(os.path.join(sesion, "verificacion_%s.json" % e["id"]), {}).get("compromisos", [])}
        for it in ev.get("items", []):
            it = dict(it)
            r = rev.get(it.get("id"))
            if r:
                it["_revision"] = {"veredicto": r.get("veredicto"), "nota": r.get("nota") or "", "url_2": r.get("url_2") or ""}
                if r.get("veredicto") == "corregido":
                    for k in ("estado", "observado", "base_obs", "base_fecha", "medida_usada", "fecha_dato", "cifra_ids", "resumen", "nota", "existe_desde"):
                        if k in r and r[k] not in (None, ""):
                            it[k] = r[k]
                elif r.get("veredicto") == "sin_sustento":
                    it["estado"] = "no_verificable"
                    it["nota"] = "la verificación no encontró sustento: " + (r.get("nota") or "")
            evals[it.get("id")] = it
    registros = {}
    for c in inv["compromisos"]:
        if c.get("espejo_de"):
            continue
        registros[c["id"]] = puntuar(c, evals.get(c["id"]), inv, cif_ok)
    filas = []
    for c in inv["compromisos"]:
        if c.get("espejo_de"):
            o = registros[c["espejo_de"]]
            r = dict(o, id=c["id"], corto=c["corto"], semilla=c["semilla"], eje=c["eje"], espejo_de=c["espejo_de"])
        else:
            r = registros[c["id"]]
        r["texto"] = c["texto"]
        r["pagina"] = c["pagina"]
        orig = por_id[c["espejo_de"]] if c.get("espejo_de") else {}
        r["meta_plan"] = c.get("meta") or orig.get("meta")
        r["monto_mq"] = c.get("monto_mq") if c.get("monto_mq") is not None else orig.get("monto_mq")
        r["bloque"] = c.get("bloque")
        filas.append(r)
    semillas = []
    for s in inv["semillas"]:
        fs = [f for f in filas if f["semilla"] == s["id"]]
        ver_ = [f for f in fs if f["estado"] != "no_verificable"]
        conteo = {k: sum(1 for f in fs if f["estado"] == k) for k in ESTADOS}
        semillas.append({"id": s["id"], "nombre": s["nombre"], "n": len(fs), "verificables": len(ver_),
                         "cobertura": round(100.0 * len(ver_) / len(fs), 1) if fs else None,
                         "avance": promedio([f["puntos"] for f in fs]),
                         "con_dato": promedio([f["puntos"] for f in ver_]),
                         "estados": conteo})
    diez = [s for s in semillas if s["id"] != "F"]
    unicos = [f for f in filas if not f.get("espejo_de")]
    corte = max(cortes) if cortes else dt.date.today().isoformat()
    res = {
        "plan": inv["plan"], "corte": corte, "mandato": inv["plan"]["mandato"],
        "transcurrido": round(100 * transcurrido(inv, dt.date.fromisoformat(corte)), 1),
        "global": promedio([s["avance"] for s in diez]),
        "global_con_dato": promedio([s["con_dato"] for s in diez]),
        "global_compromisos": promedio([f["puntos"] for f in unicos if f["semilla"] != "F"]),
        "fiscal": next((s for s in semillas if s["id"] == "F"), None),
        "n_compromisos": len(filas), "n_unicos": len(unicos),
        "n_verificables": sum(1 for f in unicos if f["estado"] != "no_verificable"),
        "estados": {k: sum(1 for f in unicos if f["estado"] == k) for k in ESTADOS},
        "ejes_sin_evaluacion": faltan,
        "semillas": semillas, "compromisos": filas,
    }
    escribir(os.path.join(sesion, "auditoria.json"), res)
    escribir_cifras(sesion, res)
    if salida_json:
        print(json.dumps(resumen_corto(res), ensure_ascii=False))
    return 0 if not faltan else 1


def nombre_semilla(s):
    return "Marco fiscal" if s["id"] == "F" else "Semilla %s" % s["id"]


def escribir_cifras(sesion, res):
    """Cifras derivadas (cálculo propio) para que el hilo y el informe las citen con id (I2/G4)."""
    arch = os.path.relpath(os.path.join(sesion, "auditoria.json"), RAIZ)
    anio = int(res["corte"][:4])
    ev = {"url": "local:" + arch, "cita": "Cálculo determinista de scripts/auditoria.py sobre las evaluaciones verificadas", "archivo_local": arch}
    C = []

    def cifra(n, concepto, valor, unidad, tipo, partes=None, nota=""):
        c = {"id": "%s-c%02d" % (PREFIJO_AUD, n), "concepto": concepto, "valor": valor, "unidad": unidad, "anio": anio,
             "fuente": FUENTE_AUD, "url": "", "tipo": tipo, "periodo": res["mandato"]["inicio"] + " a " + res["corte"],
             "evidencia": ev, "nota": nota or "Derivado: promedio de puntajes por compromiso (método mixto)."}
        if partes is not None:
            c["partes"] = partes
        C.append(c)

    diez = [s for s in res["semillas"] if s["id"] != "F" and s["avance"] is not None]
    raros = [s["id"] for s in res["semillas"] if s["id"] != "F" and not (str(s["id"]).isdigit() and 1 <= int(s["id"]) <= 10)]
    if raros:
        raise Uso("la numeración aud-cNN admite ejes de plan con id 1–10 (y F); ids fuera de rango: %s" % ", ".join(map(str, raros)))
    nd = len(diez)
    ini_m = dt.date.fromisoformat(res["mandato"]["inicio"])
    dias_m = (dt.date.fromisoformat(res["mandato"]["fin"]) - ini_m).days
    cifra(1, "Avance promedio por semilla del Plan de Gobierno", res["global"], "% de avance", "desglose",
          [{"nombre": nombre_semilla(s), "valor": s["avance"]} for s in diez])
    cifra(2, "Avance global del Plan de Gobierno (promedio de las %d semillas; sin dato oficial = 0)" % nd, res["global"], "% de avance", "puntual")
    cifra(3, "Avance global si solo contaran los compromisos con dato oficial", res["global_con_dato"], "% de avance", "puntual",
          nota="Derivado: promedio de las %d semillas sin los compromisos no verificables. No es el resultado del plan: el resultado es aud-c02." % nd)
    cifra(4, "Compromisos por estado de cumplimiento", res["n_unicos"], "compromisos", "desglose",
          [{"nombre": ETIQUETA[k], "valor": v} for k, v in res["estados"].items() if v])
    cifra(5, "Mandato transcurrido a la fecha de corte", res["transcurrido"], "% del periodo 2024–2028", "puntual",
          nota="Días desde el %d de %s de %d ÷ %s días del mandato." % (ini_m.day, MESES_AUD[ini_m.month - 1], ini_m.year, "{:,}".format(dias_m)))
    cifra(6, "Cobertura de verificación por semilla", res["n_verificables"], "% de compromisos verificables", "desglose",
          [{"nombre": nombre_semilla(s), "valor": s["cobertura"]} for s in res["semillas"]])
    cifra(7, "Compromisos verificables", res["n_verificables"], "compromisos", "puntual")
    if res["global"] is not None and res["global_con_dato"] is not None:
        cifra(8, "Puntos de avance que restan los compromisos sin dato oficial", round(res["global_con_dato"] - res["global"], 1), "puntos porcentuales", "puntual",
              nota="Derivado: aud-c03 − aud-c02. Lo que el plan pierde por compromisos que no se pueden comprobar con datos oficiales.")
    nu = res["n_unicos"]
    cum = res["estados"].get("cumplido", 0)
    unicos_semillas = [f for f in res["compromisos"] if not f.get("espejo_de") and f["semilla"] != "F"]
    if nu:
        cifra(9, "Compromisos cumplidos, sin contar el avance parcial", round(100.0 * cum / nu, 1), "% de los compromisos distintos", "puntual",
              nota="Derivado: %d cumplidos ÷ %d compromisos distintos. No toma en cuenta el avance parcial de los demás." % (cum, nu))
        cifra(10, "Compromisos no cumplidos (en proceso, anunciados, sin iniciar, incumplidos, en retroceso o sin dato)", round(100.0 * (nu - cum) / nu, 1),
              "% de los compromisos distintos", "puntual", nota="Derivado: 100 − aud-c09.")
    tipos = [("monto", "Montos (dinero ejecutado)"), ("meta", "Metas con número"), ("hito", "Hitos (leyes, programas, instituciones)")]
    por_tipo = [(nom, [f["puntos"] for f in unicos_semillas if f["medida_usada"] == k]) for k, nom in tipos]
    por_tipo = [(nom, xs) for nom, xs in por_tipo if xs]
    if por_tipo:
        cifra(22, "Avance promedio por tipo de compromiso (las %d semillas, sin espejos ni marco fiscal)" % nd, promedio([f["puntos"] for f in unicos_semillas]),
              "% de avance", "desglose", [{"nombre": nom, "valor": promedio(xs)} for nom, xs in por_tipo],
              nota="Derivado: promedio simple de los compromisos de cada tipo (%s). Sin dato oficial o no atribuible = 0." % ", ".join("%s: %d" % (nom.split(" (")[0], len(xs)) for nom, xs in por_tipo))
    for s in res["semillas"]:
        fs = [f for f in res["compromisos"] if f["semilla"] == s["id"]]
        if fs:
            n = 41 if s["id"] == "F" else 30 + int(s["id"])
            cifra(n, "Compromisos por estado · %s" % nombre_semilla(s), len(fs), "compromisos", "desglose",
                  [{"nombre": ETIQUETA[k], "valor": v} for k, v in s["estados"].items() if v],
                  nota="Derivado: estado de cada compromiso de la semilla (los espejos cuentan en las dos semillas).")
    for s in res["semillas"]:
        n = 21 if s["id"] == "F" else 10 + int(s["id"])
        fs = [f for f in res["compromisos"] if f["semilla"] == s["id"]]
        if not fs:
            continue
        cifra(n, "Avance por compromiso · %s" % nombre_semilla(s), s["avance"], "% de avance", "desglose",
              [{"nombre": f["corto"], "valor": f["puntos"]} for f in fs])
    escribir(os.path.join(sesion, "hallazgos_%s.json" % PREFIJO_AUD),
             {"eje": PREFIJO_AUD, "n_busquedas": 0, "n_fetch": 0, "cifras": C,
              "fuentes": [{"nombre": FUENTE_AUD, "url": "", "nivel": "propia"}], "vacios": []})
    escribir(os.path.join(sesion, "verificacion_%s.json" % PREFIJO_AUD),
             {"eje": PREFIJO_AUD, "items": [{"id": c["id"], "veredicto": "verificada", "valor_final": c["valor"],
                                              "fuente_2": "Recálculo determinista (scripts/auditoria.py)", "url_2": "",
                                              "independencia": "baja", "nota": "Cálculo propio: no es un dato publicado por una fuente."} for c in C]})


def resumen_corto(res):
    return {"global": res["global"], "global_con_dato": res["global_con_dato"], "global_compromisos": res["global_compromisos"],
            "transcurrido": res["transcurrido"], "corte": res["corte"], "n_compromisos": res["n_compromisos"],
            "n_unicos": res["n_unicos"], "n_verificables": res["n_verificables"], "estados": res["estados"],
            "fiscal": res["fiscal"]["avance"] if res["fiscal"] else None, "ejes_sin_evaluacion": res["ejes_sin_evaluacion"],
            "semillas": [{"id": s["id"], "avance": s["avance"], "con_dato": s["con_dato"], "n": s["n"], "verificables": s["verificables"]} for s in res["semillas"]],
            "cifras_aud": [c["id"] for c in leer_aud_ids(res)]}


def leer_aud_ids(res):
    return [{"id": "%s-c%02d" % (PREFIJO_AUD, n)} for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 22)] + \
        [{"id": "%s-c%02d" % (PREFIJO_AUD, 21 if s["id"] == "F" else 10 + int(s["id"]))} for s in res["semillas"] if s["n"]] + \
        [{"id": "%s-c%02d" % (PREFIJO_AUD, 41 if s["id"] == "F" else 30 + int(s["id"]))} for s in res["semillas"] if s["n"]]


# ---------------------------------------------------------------- textos de celda
def txt_meta(f):
    m = f.get("meta_plan") or {}
    if f["medida_usada"] == "monto" and f.get("monto_mq") is not None:
        return "Q%s M" % fmt(f["monto_mq"])
    if f["medida_usada"] == "meta" and m:
        if m.get("valor") is None:
            return "Que %s" % ("baje" if m["sentido"] == "baja" else "suba")
        u = m["unidad"]
        if u.startswith("%"):
            s = "%s%s" % (fmt(m["valor"]), u.split(" ")[0])
        else:
            s = fmt(m["valor"])
        b = f.get("base_usada")
        if f.get("nota_base"):
            return s + " (ya alcanzada en %s)" % ((f.get("base_fecha") or "2023")[:4])
        if es_numero(b) and b != 0 and not u.startswith("% de aumento") and not u.startswith("% de reducción"):
            s = "%s (%s) → %s" % (fmt(float(b)), (f.get("base_fecha") or "")[:4], s)
        return s + (" (techo)" if m.get("techo") else "")
    return "Hito"


def txt_obs(f):
    if f["estado"] == "no_verificable":
        return "Sin dato oficial"
    if f["medida_usada"] == "hito":
        return ETIQUETA[f["estado"]]
    o = f.get("observado")
    a = (" (%s)" % f["fecha_dato"][:7]) if f.get("fecha_dato") else ""
    if f["medida_usada"] == "monto":
        return "Q%s M%s" % (fmt(float(o)), a)
    m = f.get("meta_plan") or {}
    u = m.get("unidad", "")
    if u.startswith("%"):
        return "%s%%%s" % (fmt(float(o)), a)
    return "%s%s" % (fmt(float(o)), a)


def txt_avance(f):
    """El avance con los decimales de la barra (entero si lo es)."""
    if f["puntos"] is None:
        return "—"
    if f["estado"] == "no_verificable":
        return "0%*"
    p = float(f["puntos"])
    return "%s%%" % fmt(p, 0 if p.is_integer() else 1)


def _n(v):
    """El número como lo da la fuente (hasta 3 decimales, sin ceros de relleno), con separador de miles."""
    if not es_numero(v):
        return "—"
    s = "{:,.3f}".format(float(v)).rstrip("0").rstrip(".")
    return s.replace("-", "−")


def txt_calculo(f):
    """De dónde sale el avance de la barra: la operación con sus números, o la regla que lo fija."""
    regla, est = f.get("regla"), f["estado"]
    if regla == "ya_cumplida":
        m0, b0, a0 = f.get("meta_plan") or {}, f.get("base_usada", f.get("base_obs")), (f.get("base_fecha") or "2023")[:4]
        return "Ya en meta en %s (%s); hoy %s: %s → 0" % (a0, _n(b0), _n(f.get("observado")), "no atribuible" if est == "no_atribuible" else "retroceso")
    if est == "no_atribuible":
        return "No atribuible: cuenta 0"
    if est == "no_verificable" or regla == "sin_dato":
        return "No verificable: cuenta 0"
    if regla == "hito" or f["medida_usada"] == "hito":
        return "Hito: %s = %s" % (ETIQUETA[est].lower(), PUNTOS_HITO[est])
    m = f.get("meta_plan") or {}
    obs, base, bruto = f.get("observado"), f.get("base_usada", f.get("base_obs")), f.get("avance_bruto")
    anio = (f.get("base_fecha") or "2023")[:4]
    if regla == "tendencia":
        return "De %s (%s) a %s: %s%s%% en el sentido de la meta → %s" % (_n(f.get("base_obs")), anio, _n(obs), "+" if (f.get("cambio_rel") or 0) > 0 else "",
                                                fmt(float(f.get("cambio_rel") or 0), 1), fmt(float(f["puntos"]), 0))
    if regla == "techo":
        return "%s %s %s (techo) → %s" % (_n(obs), "≤" if f["puntos"] else ">", _n(m.get("valor")), fmt(float(f["puntos"]), 0))
    if regla == "monto":
        op = "Q%s M ÷ Q%s M" % (_n(obs), _n(f.get("monto_mq")))
    elif regla == "incremento":
        op = "(%s − %s) ÷ %s" % (_n(obs), _n(base), _n(m.get("valor")))
    elif regla == "nivel":
        op = "(%s − %s) ÷ (%s − %s)" % (_n(obs), _n(base), _n(m.get("valor")), _n(base))
    else:
        op = "%s ÷ %s" % (_n(obs), _n(m.get("valor")))
    if not es_numero(bruto):
        return op
    s = "%s = %s%%" % (op, fmt(float(bruto), 1))
    if bruto > 100:
        s += " → 100 (tope)"
    elif bruto < 0:
        s += " → 0"
    return s


def txt_detalle(f):
    """Qué encontramos: el hallazgo, la línea base o el motivo del 0, la fuente y la fecha del dato."""
    que = (f.get("resumen") or "").strip()
    if f.get("nota_base"):
        que += " %s%s." % (f["nota_base"][0].upper(), f["nota_base"][1:])
    if f["estado"] == "no_verificable" and f.get("motivo") and f["motivo"] not in que:
        que += " No verificable: %s." % f["motivo"].rstrip(".")
    if f["estado"] == "no_atribuible" and f.get("motivo") and not f.get("nota_base"):
        que += " %s%s." % (f["motivo"][0].upper(), f["motivo"][1:].rstrip("."))
    if f.get("ritmo") and f.get("esperado") is not None:
        que += " Ritmo: %s (con %s%% del mandato a la fecha del dato)." % (f["ritmo"], fmt(float(f["esperado"]), 1))
    if f.get("fuente"):
        que += " Fuente: %s%s." % (f["fuente"].rstrip("."), (" · " + f["fecha_dato"]) if f.get("fecha_dato") else "")
    return que.strip() or "Sin evaluación."


# ---------------------------------------------------------------- páginas generadas
# Reparto por líneas estimadas (medido con render_informe.js: P2 sin desborde).
LINEAS_FICHA = 42
RESERVA_FICHA = 6
LINEAS_EVIDENCIA = 36
PIE_FICHAS = ("Cada fila es una barra del capítulo: debajo, qué encontramos y la fuente; «Cálculo», de dónde sale el avance. "
              "Meta = logrado ÷ meta (o desde el nivel de 2023); monto = ejecutado desde 2024 ÷ prometido; hito = 0, 25, 50 o 100 según estado "
              "(cumplido 100, en proceso 50, anunciado 25); tendencia: +10% o más = 100, mejora menor = 50. Tope 100. "
              "*Sin dato oficial cuenta 0. ≡ = el mismo compromiso evaluado en otra semilla. Cálculo propio.")


def lineas(*pares):
    """Líneas de una fila: el máximo de ceil(len(texto) / caracteres por línea) entre sus celdas."""
    return max(-(-len(t) // n) if t else 1 for t, n in pares)


def repartir(filas, peso, tope):
    trozos, actual, usado = [], [], 0.0
    for f in filas:
        w = peso(f)
        if actual and usado + w > tope:
            trozos.append(actual)
            actual, usado = [], 0.0
        actual.append(f)
        usado += w
    if actual:
        trozos.append(actual)
    return trozos


def id_fichas(semilla, k=0):
    """id de la tabla de fichas de una semilla (la primera: fichas-<s>; las siguientes: fichas-<s>-<k+1>)."""
    return "fichas-%s%s" % (str(semilla).lower(), "-%d" % (k + 1) if k else "")


def paginas_fichas(res, semilla, key, tope=None):
    fs = [f for f in res["compromisos"] if str(f["semilla"]) == str(semilla)]
    s = next(x for x in res["semillas"] if str(x["id"]) == str(semilla))
    if not fs:
        return []
    cols = [{"t": "ID", "ancho": 50}, {"t": "Compromiso"}, {"t": "Estado", "ancho": 92},
            {"t": "Cálculo", "ancho": 196}, {"t": "Avance", "num": True, "ancho": 54}]

    def nombre(f):
        return f["corto"] + (" (≡ %s)" % f["espejo_de"] if f.get("espejo_de") else "")

    def peso(f):
        return 1.0 + lineas((nombre(f), 20), (ETIQUETA[f["estado"]], 11), (txt_calculo(f), 26)) + lineas((txt_detalle(f), 96))
    tope = tope or LINEAS_FICHA
    # La última hoja lleva además la fila del promedio y el pie con el método (RESERVA_FICHA líneas): cuenta como
    # una fila más al final; si queda sola, se lleva consigo la última ficha.
    trozos = repartir(fs + [None], lambda f: RESERVA_FICHA if f is None else peso(f), tope)
    if trozos[-1] == [None] and len(trozos) > 1:
        trozos[-1].insert(0, trozos[-2].pop())
    trozos[-1].pop()
    trozos = [t for t in trozos if t]
    out = []
    for k, tr in enumerate(trozos):
        filas = []
        for f in tr:
            filas.append({"c": [f["id"], nombre(f), ETIQUETA[f["estado"]], txt_calculo(f), txt_avance(f)],
                          "detalle": txt_detalle(f), "dest": f["estado"] == "cumplido", "b": [0]})
        if k == len(trozos) - 1:
            filas.append({"c": ["", ("%s · promedio de los %d (%d con dato; sin dato = 0)" % (nombre_semilla(s), s["n"], s["verificables"]) if s["verificables"] < s["n"] else "%s · promedio de los %d" % (nombre_semilla(s), s["n"])), "", "",
                                "%s%%" % fmt(float(s["avance"]), 1) if s["avance"] is not None else "—"], "total": True})
        tabla = {"b": "tabla", "id": id_fichas(semilla, k),
                 "indice": "Fichas de cumplimiento · %s" % nombre_semilla(s) if k == 0 else False,
                 "columnas": cols, "filas": filas, "fuente": "%s (%s); evaluación propia con fuentes oficiales" % (res["plan"].get("titulo", "Plan de Gobierno").split(" · ")[0], res["plan"].get("autor", "")),
                 "pie": PIE_FICHAS if k == len(trozos) - 1 else "Sigue en la página siguiente. *Sin dato oficial cuenta 0."}
        bloques = [{"b": "titulo", "texto": "%s · de dónde sale cada barra%s" % (nombre_semilla(s), " (continuación)" if k else "")}, tabla]
        out.append({"tipo": "cuerpo", "auto": key, "seccion": "%s · fichas" % nombre_semilla(s), "bloques": bloques})
    return out


def dominio(url):
    m = re.match(r"^https?://(?:www\.)?([^/]+)", str(url or ""))
    return m.group(1) if m else ""


def paginas_evidencias(res, semilla, key, tope=None):
    """Anexo de trazabilidad: el hallazgo ya va en las fichas; aquí, dónde se comprueba (enlace y verificación)."""
    fs = [f for f in res["compromisos"] if (semilla == "todas" or str(f["semilla"]) == str(semilla)) and not f.get("espejo_de")]
    cols = [{"t": "ID", "ancho": 50}, {"t": "Compromiso", "ancho": 150}, {"t": "Sitio del documento"}, {"t": "Verificación", "ancho": 190}]

    def celdas(f):
        rev = f.get("revision") or {}
        urls = []
        for e in f.get("evidencia") or []:
            u = e.get("url") if isinstance(e, dict) else None
            if u and not u.startswith("local:") and u not in urls:
                urls.append(u)
        doms = []
        for u in urls:
            if dominio(u) and dominio(u) not in doms:
                doms.append(dominio(u))
        # Sin URL en el cuerpo (I3): el sitio del documento; la URL completa queda en la sesión de trabajo.
        donde = " · ".join(doms[:3]) or "Sin documento oficial que lo mida"
        ver = {"confirmado": "Confirmado", "corregido": "Corregido", "sin_sustento": "Sin sustento"}.get(rev.get("veredicto"), "Sin revisión")
        if rev.get("url_2") and dominio(rev["url_2"]):
            ver += " con " + dominio(rev["url_2"])
        return [f["id"], f["corto"], donde, ver]
    trozos = repartir(fs, lambda f: 0.6 + lineas((celdas(f)[1], 20), (celdas(f)[2], 30), (celdas(f)[3], 26)), tope or LINEAS_EVIDENCIA)
    out = []
    for k, tr in enumerate(trozos):
        filas = [{"c": celdas(f), "b": [0]} for f in tr]
        tabla = {"b": "tabla", "id": "evid-%s-%d" % (str(semilla).lower(), k + 1),
                 "indice": "Enlaces y verificación%s" % ("" if semilla == "todas" else " · " + nombre_semilla({"id": semilla})) if k == 0 else False,
                 "columnas": cols, "filas": filas, "fuente": "Evaluaciones y verificaciones por compromiso (sesión de trabajo del informe)",
                 "pie": "El hallazgo, la fuente, la fecha y el cálculo de cada compromiso están en las fichas de su semilla. Aquí, el sitio del "
                        "documento que lo sostiene y la revisión con una segunda fuente (confirmado, corregido o sin sustento). Los espejos se evalúan una vez."}
        out.append({"tipo": "anexo", "auto": key, "titulo": "Enlaces y verificación" + (" (sigue)" if k else ""),
                     "seccion": "Anexo · evidencias", "bloques": [tabla],
                     **({"indice": {"titulo": "Enlaces y verificación por compromiso", "clase": "anexo"}} if k == 0 else {})})
    return out


def semilla_de_cifra(cid):
    """aud-c11…aud-c20 → semilla 1…10 · aud-c21 → F (avance por compromiso); None si no es una de ellas."""
    m = re.match(r"^%s-c(\d\d)$" % PREFIJO_AUD, str(cid or ""))
    if not m:
        return None
    n = int(m.group(1))
    return "F" if n == 21 else (str(n - 10) if 11 <= n <= 20 else None)


def figuras_por_compromiso(R):
    """[(página 1-based, figura, semilla)] de las figuras con el avance por compromiso (aud-c1N, aud-c21)."""
    out = []
    for i, P in enumerate(R.get("paginas", []), 1):
        for B in P.get("bloques") or []:
            for f in ([B] if B.get("b") == "figura" else (B.get("items") or []) if B.get("b") == "figuras" else []):
                s_ = semilla_de_cifra((f.get("grafico") or {}).get("id"))
                if s_:
                    out.append((i, f, s_))
    return out


def ref_fichas(semilla):
    return "Cada barra, con su hallazgo, su fuente y su cálculo, en la {tabla:%s} (p. {pag:%s})." % (id_fichas(semilla), id_fichas(semilla))


def cmd_insertar(sesion, ruta_inf):
    res = leer(os.path.join(sesion, "auditoria.json"))
    R = leer(ruta_inf)
    nuevas, vistas, n_gen = [], set(), 0
    for P in R["paginas"]:
        key = P.get("auto")
        if not key:
            nuevas.append(P)
            continue
        if key in vistas:
            continue  # páginas ya generadas de la misma clave: se regeneran juntas
        vistas.add(key)
        m = re.match(r"^(fichas|evidencias):(\w+)$", key)
        if not m:
            raise Uso("auto %r desconocido (fichas:<1..10|F> · evidencias:<1..10|F|todas>)" % key)
        tope = P.get("lineas")  # si P2 salta en una página generada, baja este tope en el placeholder
        gen = (paginas_fichas if m.group(1) == "fichas" else paginas_evidencias)(res, m.group(2), key, tope)
        for g_ in gen:
            if tope:
                g_["lineas"] = tope
        for k in ("id", "indice") if m.group(1) == "fichas" else ():
            if k in P and gen:
                gen[0][k] = P[k]
        if P.get("id") and gen:
            gen[0]["id"] = P["id"]
        nuevas.extend(gen)
        n_gen += len(gen)
    R["paginas"] = nuevas
    # Cada gráfico de avance por compromiso remite a las fichas de su semilla (de dónde sale cada barra).
    con_fichas = {str(P["auto"]).split(":")[1] for P in nuevas if str(P.get("auto", "")).startswith("fichas:")}
    n_ref = 0
    for _, f, s_ in figuras_por_compromiso(R):
        if s_ in con_fichas and "{tabla:%s}" % id_fichas(s_) not in (f.get("pie") or ""):
            f["pie"] = ((f.get("pie") or "").rstrip() + " " + ref_fichas(s_)).strip()
            n_ref += 1
    escribir(ruta_inf, R)
    print("insertadas %d páginas generadas (%s) · total %d páginas · %d gráfico(s) remitidos a sus fichas" % (
        n_gen, ", ".join(sorted(vistas)) or "ninguna", len(nuevas), n_ref))
    return 0


def cmd_justificar(sesion, ruta_inf):
    """Gate J1–J5: cada barra de un gráfico de avance por compromiso tiene de dónde sale (ficha con hallazgo, fuente y cálculo)."""
    res = leer(os.path.join(sesion, "auditoria.json"))
    R = leer(ruta_inf)
    F, avisos = [], []
    ini_j = dt.date.fromisoformat((res.get("mandato") or res["plan"]["mandato"])["inicio"])
    paginas = R.get("paginas", [])
    fichas = {}  # semilla → página 1-based de su primera ficha
    for i, P in enumerate(paginas, 1):
        k = str(P.get("auto", ""))
        if k.startswith("fichas:"):
            fichas.setdefault(k.split(":")[1], i)
    por_sem = {}
    for f in res["compromisos"]:
        por_sem.setdefault(str(f["semilla"]), []).append(f)
    figs = figuras_por_compromiso(R)
    vistas = set()
    for pag, fig, s_ in figs:
        vistas.add(s_)
        g_ = fig.get("grafico") or {}
        nombres = {f["corto"]: f for f in por_sem.get(s_, [])}
        if s_ not in fichas:
            F.append("J1 pág. %d: el gráfico %s (%s) no tiene fichas en el informe: pon {\"tipo\": \"cuerpo\", \"auto\": \"fichas:%s\"} en su capítulo" % (pag, fig.get("id"), g_.get("id"), s_))
        elif fichas[s_] < pag:
            avisos.append("J1 pág. %d: las fichas de %s (p. %d) van antes que su gráfico" % (pag, nombre_semilla({"id": s_}), fichas[s_]))
        for it in g_.get("items") or []:
            if it.get("nombre") not in nombres:
                F.append("J2 pág. %d: barra «%s» sin compromiso en la auditoría (usa el nombre corto tal cual)" % (pag, it.get("nombre")))
        if "{tabla:%s}" % id_fichas(s_) not in (fig.get("pie") or ""):
            F.append("J3 pág. %d: el pie del gráfico %s no remite a sus fichas ({tabla:%s}); corre --insertar" % (pag, fig.get("id"), id_fichas(s_)))
    for s_, fs in por_sem.items():
        if s_ not in vistas and s_ in fichas:
            avisos.append("J1 %s: tiene fichas pero ningún gráfico de avance por compromiso" % nombre_semilla({"id": s_}))
        if s_ not in vistas and s_ not in fichas:
            F.append("J1 %s: ni gráfico de avance por compromiso ni fichas: sus %d compromisos no se explican" % (nombre_semilla({"id": s_}), len(fs)))
        for f in fs:
            det = txt_detalle(f)
            if f["estado"] in ("no_verificable", "no_atribuible"):
                if not f.get("motivo"):
                    F.append("J4 %s: %s sin motivo (qué se buscó o desde cuándo existe)" % (f["id"], ETIQUETA[f["estado"]].lower()))
            elif len(f.get("resumen") or "") < 40 or not f.get("fuente"):
                F.append("J4 %s: hallazgo de menos de 40 caracteres o sin fuente: la barra no se justifica" % f["id"])
            elif f["medida_usada"] == "hito" and f["estado"] in ("cumplido", "en_proceso", "anunciado") and not any(int(a) >= ini_j.year for a in re.findall(r"\b((?:19|20)\d\d)\b", f.get("resumen") or "")):
                # El año del hecho va en el hallazgo mismo (no basta la fecha_dato que la ficha añade siempre).
                F.append("J5 %s: hito %s sin el año del hecho del mandato en el hallazgo (qué pasó y cuándo)" % (f["id"], ETIQUETA[f["estado"]].lower()))
            if txt_calculo(f).count("—"):
                F.append("J4 %s: cálculo incompleto («%s»)" % (f["id"], txt_calculo(f)))
    for a_ in avisos:
        print("AVISO " + a_)
    if F:
        print("FALLA justificación (%d):" % len(F))
        for x in F:
            print(" - " + x)
        return 1
    print("OK justificación: %d gráficos de avance por compromiso · %d compromisos con hallazgo, fuente y cálculo en sus fichas" % (
        len(figs), sum(len(v) for v in por_sem.values())))
    return 0


# ---------------------------------------------------------------- resumen para agentes
def cmd_resumen(sesion, para):
    res = leer(os.path.join(sesion, "auditoria.json"))
    print("# auditoría · corte %s · mandato transcurrido %s%% · global %s%% (sin dato oficial = 0) · con dato %s%% (los no verificables restan %s puntos) · promedio simple de compromisos %s%%" % (
        res["corte"], res["transcurrido"], res["global"], res["global_con_dato"],
        fmt(round(res["global_con_dato"] - res["global"], 1), 1) if res["global"] is not None and res["global_con_dato"] is not None else "—", res["global_compromisos"]))
    print("compromisos: %d (%d únicos) · verificables %d · estados: %s" % (res["n_compromisos"], res["n_unicos"], res["n_verificables"],
                                                                         ", ".join("%s %d" % (ETIQUETA[k], v) for k, v in res["estados"].items() if v)))
    print("cifras derivadas (fuente «%s»): %s" % (FUENTE_AUD, ", ".join(x["id"] for x in leer_aud_ids(res))))
    print("\n## semillas (aud-c01 / aud-c06; por compromiso aud-c11…aud-c20, fiscal aud-c21; por estado aud-c31…aud-c40, fiscal aud-c41; cumplidos aud-c09 / no cumplidos aud-c10; por tipo de compromiso aud-c22)")
    tipos = {}
    for f in res["compromisos"]:
        if not f.get("espejo_de") and f["semilla"] != "F":
            tipos.setdefault(f["medida_usada"], []).append(f["puntos"])
    print("por tipo (aud-c22): " + " · ".join("%s %s%% (%d)" % (k, promedio(v), len(v)) for k, v in sorted(tipos.items())))
    for s in res["semillas"]:
        print("%s · %s · avance %s%% · con dato %s%% · %d/%d verificables · %s" % (
            nombre_semilla(s), s["nombre"], s["avance"], s["con_dato"], s["verificables"], s["n"],
            ", ".join("%s %d" % (ETIQUETA[k], v) for k, v in s["estados"].items() if v)))
    print("\n## compromisos")
    for f in res["compromisos"]:
        linea = "%s | %s | %s | meta %s | obs %s | avance %s%s%s" % (
            f["id"], f["corto"], ETIQUETA[f["estado"]], txt_meta(f), txt_obs(f), txt_avance(f),
            (" | ritmo %s (esperado %s%%)" % (f["ritmo"], f["esperado"])) if f.get("ritmo") else "",
            (" | ≡ %s" % f["espejo_de"]) if f.get("espejo_de") else "")
        if f.get("motivo"):
            linea += " | motivo: %s" % f["motivo"][:160]
        if f.get("nota_base"):
            linea += " | %s" % f["nota_base"]
        if para == "redactor" and not f.get("espejo_de"):
            linea += " | base %s | cifras %s | %s | %s" % (f.get("base_fecha") or "—", ",".join(f["cifra_ids"]) or "—", f["fuente"] or "—", (f["resumen"] or "")[:200])
        print(linea)
    if para == "redactor":
        print("\n## páginas generadas (auditoria.py --insertar)")
        print('Pon en informe.json {"tipo": "cuerpo", "auto": "fichas:<1..10|F>"} donde vaya la tabla de fichas de cada semilla '
              'y {"tipo": "anexo", "auto": "evidencias:todas"} (o evidencias:<semilla>) donde vaya el anexo de evidencias; '
              'corre python3 scripts/auditoria.py %s --insertar %s/informe.json ANTES de cada informe.py --check (es idempotente). '
              'Si P2 salta en una página generada, añade "lineas": <menor que %d (fichas) o %d (evidencias)> a sus páginas auto y repite.' % (sesion, sesion, LINEAS_FICHA, LINEAS_EVIDENCIA))
    return 0


def cmd_ejes(ruta):
    inv, por_id = inventario_de(None, ruta)
    out = [{"id": e["id"], "nombre": e["nombre"], "prefijo": e["prefijo"],
            "compromisos": [c for c in e["compromisos"] if not por_id[c].get("espejo_de")]} for e in inv["ejes"]]
    print(json.dumps(out, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Auditoría de cumplimiento de un plan de gobierno (variante de /investigacion).")
    ap.add_argument("sesion", nargs="?", help="sesiones/<slug> (con compromisos.json)")
    ap.add_argument("--inventario", help="ruta de compromisos.json (con --ejes)")
    ap.add_argument("--ejes", action="store_true", help="imprime los ejes y sus compromisos evaluables en JSON")
    ap.add_argument("--eje", help="imprime los compromisos de un eje para el investigador/verificador")
    ap.add_argument("--plantilla", metavar="EJE", help="esqueleto de evaluacion_<eje>.json")
    ap.add_argument("--validar", metavar="EJE", help="valida evaluacion_<eje>.json")
    ap.add_argument("--verificacion", action="store_true", help="con --validar: exige la revisión del verificador")
    ap.add_argument("--calcular", action="store_true", help="calcula auditoria.json y las cifras derivadas aud-cNN")
    ap.add_argument("--resumen", action="store_true", help="digesto del puntaje")
    ap.add_argument("--para", choices=["guionista", "redactor"], default="guionista")
    ap.add_argument("--insertar", metavar="INFORME", help="expande las páginas {auto: fichas:N | evidencias:N|todas}")
    ap.add_argument("--justificar", metavar="INFORME", help="gate J1–J5: cada barra de avance por compromiso con hallazgo, fuente y cálculo")
    a = ap.parse_args()
    try:
        if a.ejes:
            if not a.inventario:
                raise Uso("--ejes requiere --inventario")
            return cmd_ejes(a.inventario)
        if not a.sesion:
            raise Uso("falta la sesión")
        if a.eje:
            return cmd_eje(a.sesion, a.eje)
        if a.plantilla:
            return cmd_plantilla(a.sesion, a.plantilla)
        if a.validar:
            return cmd_validar(a.sesion, a.validar, a.verificacion)
        if a.calcular:
            return cmd_calcular(a.sesion)
        if a.resumen:
            return cmd_resumen(a.sesion, a.para)
        if a.insertar:
            return cmd_insertar(a.sesion, a.insertar)
        if a.justificar:
            return cmd_justificar(a.sesion, a.justificar)
        raise Uso("indica una acción (--eje, --plantilla, --validar, --calcular, --resumen, --insertar, --justificar)")
    except Uso as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
