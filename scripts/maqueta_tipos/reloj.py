"""Anotación «reloj»: una hora que corre (de `de` a `a`, p. ej. de «8:14:21» a «8:14:22») mientras dura, en una esquina
de la zona libre o encima de un ancla (`en`). Sirve para decir «todo esto pasa en un segundo». La hora es un número en
pantalla: pasa por el respaldo de las cifras (C3D5), salvo que el mundo sea un ESQUEMA y la hora se declare `ilustrativa`
(un esquema no es un lugar ni un momento real: la voz no la dice como dato). Resuelto: {de, a, de_s, a_s, corre: [t0, t1], …}."""
import re

RE_HORA = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2})(?:[.,](\d))?)?$")


def segundos(txt):
    m = RE_HORA.match(str(txt).strip())
    if not m or int(m.group(2)) > 59 or int(m.group(3) or 0) > 59:
        return None
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3) or 0) + int(m.group(4) or 0) / 10


def resolver(a, X, que):
    de, hasta = segundos(a["de"]), segundos(a.get("a") or a["de"])
    if de is None or hasta is None:
        raise X.m3.Falla("M3D2", "%s: `de` y `a` son horas «H:MM:SS» (o «H:MM», «H:MM:SS.d»); llegó %r → %r" % (que, a["de"], a.get("a")))
    if hasta < de:
        raise X.m3.Falla("M3D2", "%s: el reloj corre hacia adelante (`a` ≥ `de`)" % que)
    corre = [a.get("corre_desde", a["t"]), a.get("corre_hasta", a["hasta"])]
    if not corre[0] < corre[1]:
        raise X.m3.Falla("M3D2", "%s: `corre_desde` (%g) va antes que `corre_hasta` (%g)" % (que, corre[0], corre[1]))
    r = {"de": a["de"], "a": a.get("a") or a["de"], "ilustrativo": bool(a.get("ilustrativo")), "de_s": de, "a_s": hasta, "corre": [float(corre[0]), float(corre[1])], "rotulo": a.get("rotulo") or "", "decimas": bool(a.get("decimas")),
         "segundos": ":" in str(a["de"])[str(a["de"]).index(":") + 1:], "pos": a["pos"]}
    if a.get("en") is not None:
        from maqueta_tipos import _movimiento as MV
        r["en"] = MV.resolver_ancla(a["en"], X, que + " → en")[0]
    return r


def anclas(a):
    return [a["en"]] if a.get("en") else []


def textos(a, escala=None):
    """Lo que se lee (para el tiempo de lectura y el respaldo). Un reloj `ilustrativo` sobre un esquema no pide respaldo."""
    if a.get("ilustrativo") and escala == "esquema":
        return [a.get("rotulo") or ""]
    return [x for x in (a.get("rotulo"), a.get("de")) if x]
