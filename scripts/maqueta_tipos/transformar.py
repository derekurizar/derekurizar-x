"""Evento «transformar»: una pieza con épocas pasa de una (`de`) a otra (`a`) mientras dura el evento, como una obra:
lo viejo se desvanece por partes, la tierra se mueve, las pilas suben, los tableros se tienden tramo a tramo y al final
llegan los carros de la época nueva. Sin números en el 3D: los años van en la capa.

El centro de la obra es el `lugar` del evento o el de su `pieza` (x, y); `rumbo` el del evento o el de la pieza (0).
Resuelto: {pieza, pieza_tipo, x, y, rumbo, k (unidades por metro), radio_m, alto_m, de, a, orden, cuerpo (None: lo
decide el módulo según la pieza), autos, obreros, volteos, gente_tamano, semilla}.
`cerrar`: un solo `transformar` por pieza dibuja la obra (el primero); los demás avisan y se ignoran. El que queda PUBLICA
en `_cosas` de su pieza (M3D15–M3D16, maqueta_escena; un evento no tiene `_cosas` propias) lo que dibuja mientras dura,
con las medidas de transformar.js: lo viejo (casas, la fábrica, su chimenea, árboles, paseantes; `cuerpo`), la obra
(montículos, volteos, obreros) y lo nuevo (tableros, rampas, pilas, postes y carros de los tres puentes; `cuerpo`). Cada
parte lleva `desde`/`hasta` (s): la escena de hoy no los lee (mide la unión), quedan para cuando el núcleo los lea. Lo
que la pieza ya publicaba dentro de la obra lleva `hasta` = cuando se hunde (trebol.js lo hunde con
ctx.cuadro.epoca[pieza].hunde)."""
import math
import random

import maqueta_escena as ME


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no está en mundo.piezas (transformar cambia la época de esa pieza)" % (que, pid))
    if e.get("lugar") is not None:
        l = X.lugar(e["lugar"], que + " → lugar")
        x, y = l["x"], l["y"]
    elif _num(pz.get("x")) is not None and _num(pz.get("y")) is not None:
        x, y = float(pz["x"]), float(pz["y"])
    else:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» (%s) no tiene un lugar: da `lugar` (dónde pasa la obra)" % (que, pid, pz.get("tipo")))
    de, a = str(e["de"]).strip(), str(e["a"]).strip()
    if not de or not a:
        raise X.m3.Falla("M3D2", "%s: `de` y `a` son las épocas (no pueden ir vacías)" % que)
    if de == a:
        X.avisos.append("%s: `de` y `a` son la misma época («%s»): la obra pasa igual" % (que, de))
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    rb = _num(e.get("rumbo"))
    if rb is None:
        rb = _num(pz.get("rumbo")) or 0.0
    cu = e.get("cuerpo")
    D = float(e.get("dur", 0) or 0)
    hd = float(e.get("hundir_desde_s", 0) or 0)
    if hd > 0 and D and hd > D - 1.5:
        raise X.m3.Falla("M3D2", "%s: `hundir_desde_s` (%.1f s) no deja tiempo a la obra dentro de `dur` (%.1f s): hace falta ≥ 1.5 s después (sube `dur` o baja `hundir_desde_s`)" % (que, hd, D))
    ul = e.get("ultimo") or []
    ul = [ul] if isinstance(ul, str) else list(ul)
    malos = [u for u in ul if u not in ("fabrica", "casas", "gente", "cerca", "arboles")]
    if malos:
        raise X.m3.Falla("M3D2", "%s: `ultimo` lleva %s; va una lista de: fabrica, casas, gente, cerca, arboles" % (que, ", ".join(map(str, malos))))
    return {
        "pieza": pid, "pieza_tipo": pz.get("tipo", ""), "x": round(x, 4), "y": round(y, 4), "rumbo": rb % 360,
        "k": 1.0 / um, "radio_m": float(e.get("radio_m", 150)), "alto_m": float(e.get("alto_m", 6.5)),
        "de": de, "a": a, "orden": e.get("orden", "centro-afuera"),
        "cuerpo": None if cu is None else bool(cu),
        "autos": int(e.get("autos", 4)), "obreros": int(e.get("obreros", 10)), "volteos": int(e.get("volteos", 2)),
        "gente_tamano": float(e.get("gente_tamano", 1.6)), "semilla": int(e.get("semilla", 1) or 1),
        "hundir_desde_s": hd, "ultimo": ul, "volteos_tamano": float(e.get("volteos_tamano", 1) or 1),
    }


def cerrar(lista, X):
    vistos = set()
    for e in sorted(lista, key=lambda q: float(q["t"])):
        if e["pieza"] in vistos:
            X.avisos.append("transformar en t=%.2f sobre «%s»: ya hay uno antes en esa pieza; manda el primero (una obra por pieza)" % (float(e["t"]), e["pieza"]))
            e["ignorar"] = True
        vistos.add(e["pieza"])
        pz = X.por_id.get(e["pieza"])
        if pz is not None and not e.get("ignorar"):
            pz["_cosas"] = list(pz.get("_cosas") or []) + _cosas(e, X, pz)


# las fases (fracción de la duración), como transformar.js
F = {"viejo": (0.02, 0.24), "dv": 0.08, "mont": (0.1, 0.62), "volteos": (0.08, 0.76), "obreros": (0.2, 0.86),
     "pilas": (0.3, 0.5), "tableros": (0.48, 0.78), "carros": (0.84, 0.97)}


def _cosas(e, X, pz):
    """Lo que dibuja la obra, con volumen (unidades de la escena; medidas en metros), cada parte con su ventana."""
    k, R, H, D = e["k"], e["radio_m"], e["alto_m"], max(0.5, float(e["dur"]))
    ro = math.radians(e["rumbo"])
    cr, sr = math.cos(ro), math.sin(ro)
    hd = min(float(e.get("hundir_desde_s") or 0), max(0.0, D - 1.5))
    if hd > 0:                                   # como transformar.js: lo viejo en pie hasta hd; la obra cabe en lo que queda
        D = (D - hd) / (1 - F["viejo"][0])
        t0 = float(e["t"]) + hd - F["viejo"][0] * D
    else:
        t0 = float(e["t"]) - (0.1 * D if float(e["t"]) <= 0.1 else 0.0)
    tU = lambda u: round(t0 + u * D, 2)
    W = lambda u, v: (e["x"] + (u * cr - v * sr) * k, e["y"] + (u * sr + v * cr) * k)
    rnd = random.Random(int(e["semilla"]) * 7919 + 17)
    fin = float(X.dur or 0) or 1e9
    co = []
    fi = X.m3.ficha(e["pieza_tipo"], "pieza") or {}
    cuerpo = e["cuerpo"] if e["cuerpo"] is not None else not fi.get("epocas")
    ult = set(e.get("ultimo") or [])
    aj = lambda o, cl: (0.86 + 0.14 * o if cl in ult else 0.8 * o) if ult else o
    vh = lambda d, cl="casas": tU(F["viejo"][0] + (F["viejo"][1] - F["viejo"][0]) * aj(min(1.0, d * 0.9 + 0.05), cl) + F["dv"])   # cuándo acaba de hundirse
    # lo que la pieza ya publicaba dentro de la obra se hunde con lo viejo (trebol.js: ctx.cuadro.epoca[pieza].hunde)
    for c in pz.get("_cosas") or []:
        d = math.hypot(c["x"] - e["x"], c["y"] - e["y"]) / k
        if d <= R + 12 and c["clave"] in ("casa", "gente", "nave industrial", "chimenea", "cajas y tambos"):
            c["hasta"] = vh(d / R, "fabrica" if c["clave"] in ("nave industrial", "chimenea") else "gente" if c["clave"] == "gente" else "casas")
    if cuerpo:
        sv, su, aC = (-0.45 * R, 0.1 * R), (-0.4 * R, 0.42 * R), 7
        pu0, pu1, pv0, pv1 = -0.88 * R, su[0] - aC, sv[1] + aC, 0.82 * R
        fu, fv = 0.02 * R, -0.18 * R
        fL, fW = min(56, 0.62 * (su[1] - su[0]) - 6), min(24, 0.4 * (sv[1] - sv[0]))
        x, y = W(fu, fv)
        co.append(ME.cosas_pieza("fábrica", x, y, fL + 0.6, fW + 0.6, 10.1, cr, sr, desde=0.0, hasta=vh(math.hypot(fu, fv) / R, "fabrica"),
                                 contiene=["techo de dientes de sierra"]))
        x, y = W(fu + fL / 2 - 3, fv - fW / 2 - 4)
        co.append(ME.cosas_pieza("chimenea", x, y, 4, 4, 22.6, desde=0.0, hasta=vh(math.hypot(fu, fv) / R, "fabrica"), animado=True))

        def fuera(u, v, a, b):
            if math.hypot(u, v) > 0.88 * R:
                return True
            if any(abs(v - c) < aC / 2 + b + 2 for c in sv) or any(abs(u - c) < aC / 2 + a + 2 for c in su):
                return True
            if abs(u - fu) < fL / 2 + a + 5 and abs(v - fv) < fW / 2 + b + 8:
                return True
            return pu0 - a - 3 < u < pu1 + a + 3 and pv0 - b - 3 < v < pv1 + b + 3
        nc, gu = 0, -0.9 * R
        while gu <= 0.9 * R:
            gv = -0.9 * R
            while gv <= 0.9 * R:
                a, b = 3.5 + 2.2 * rnd.random(), 3 + 1.4 * rnd.random()
                u, v = gu + (rnd.random() - 0.5) * 4, gv + (rnd.random() - 0.5) * 4
                if rnd.random() >= 0.22 and not fuera(u, v, a, b) and nc < 46:
                    x, y = W(u, v)
                    co.append(ME.cosas_pieza("casa", x, y, 2 * a + 1.2, 2 * b + 1.2, 4.4 if rnd.random() > 0.18 else 7.6, cr, sr,
                                             desde=0.0, hasta=vh(math.hypot(u, v) / R)))
                    nc += 1
                gv += 14
            gu += 15
        arb = []
        for i in range(10):
            u, v = pu0 + (pu1 - pu0) * rnd.random(), (pv0 + 2) if i % 2 else (pv1 - 2)
            if math.hypot(u, v) <= 0.92 * R:
                arb.append(W(u, v) + (u, v))
        for q in ME.agrupar(arb, 40 * k, lambda q: "árbol", 9.0, 6.0, 1.0 / k):
            co.append(dict(q, desde=0.0, hasta=vh(0.8)))
        co.append(ME.cosas_pieza("cerca del potrero", *W((pu0 + pu1) / 2, (pv0 + pv1) / 2), pu1 - pu0, pv1 - pv0, 1.3, cr, sr, desde=0.0, hasta=vh(0.6)))
        for i in range(8):
            c = sv[0 if i % 4 < 2 else 1] if i % 2 == 0 else su[0 if i % 4 < 2 else 1]
            s = (rnd.random() - 0.5) * 1.2 * R
            x, y = W(s, c) if i % 2 == 0 else W(c, s)
            co.append(ME.cosas_pieza("gente", x, y, 0.5 * e["gente_tamano"], 0.5 * e["gente_tamano"], 1.75 * e["gente_tamano"], gente=True,
                                     animado=True, desde=0.0, hasta=tU(0.2)))
        # lo nuevo: tres puentes (tramo elevado + rampas), sus pilas, postes y carros
        rO, Ld = 0.42 * R, 0.95 * R
        Lf = 0.42 * Ld
        Lr = (Ld - Lf) / 2
        sh, Wd = Lf / 2 + 0.5 * Lr, 15
        for q in range(3):
            al = ro + q * 2 * math.pi / 3
            phi = al + math.pi / 2
            cx, cy = e["x"] + math.cos(al) * rO * k, e["y"] + math.sin(al) * rO * k
            dx, dy = math.cos(phi), math.sin(phi)
            P = lambda s: (cx + dx * s * k, cy + dy * s * k)
            co.append(ME.cosas_pieza("tablero", *P(0), 2 * sh, Wd, H + 0.3 + 0.95, dx, dy, desde=tU(F["tableros"][0]), hasta=fin,
                                     contiene=["pretil", "vigas"]))
            for sg in (1, -1):
                co.append(ME.cosas_pieza("rampa", *P(sg * (sh + (Ld / 2 - sh) / 2)), Ld / 2 - sh, Wd, H * 0.45 + 1.25, dx, dy,
                                         desde=tU(F["tableros"][0] + 0.15), hasta=fin))
            nE = max(2, round(sh / 16))
            for i in range(nE):
                for sg in ((1, -1) if i else (1,)):
                    co.append(ME.cosas_pieza("pila", *P(sg * sh * i / nE), 3.4, Wd - 1.8, H - 1.5, dx, dy, desde=tU(F["pilas"][0]), hasta=fin,
                                             contiene=["viga cabezal"]))
                    if i % 2 == 0:
                        co.append(ME.cosas_pieza("poste de luz", *P(sg * sh * i / nE), 0.6, 2.8, H + 0.3 + 9.5, dx, dy,
                                                 desde=tU(F["tableros"][1]), hasta=fin))
            n = max(0, int(e["autos"]))
            for j in range(n):
                s = (-0.5 + (j + 0.5) / n) * (Ld + 0.28 * R)
                co.append(ME.cosas_pieza("carro", *P(s), 4.5, 1.8, H * (1 if abs(s) < sh else 0.4) + 1.8, dx, dy, animado=True,
                                         desde=tU(F["carros"][0]), hasta=fin))
            for j in range(2):
                r_ = (0.3 + 0.4 * j) * R
                co.append(ME.cosas_pieza("carro", e["x"] + math.cos(al) * r_ * k, e["y"] + math.sin(al) * r_ * k, 4.5, 1.8, 1.8,
                                         math.cos(al), math.sin(al), animado=True, desde=tU(F["carros"][0]), hasta=fin))
    # la obra (siempre): montones de tierra sacada (quietos hasta que se siembra), montículos, volteos y obreros
    for i in range(16):
        a, r_, sc = 2 * math.pi * rnd.random(), (0.18 + 0.68 * rnd.random()) * R, 1 + 0.7 * rnd.random()
        co.append(ME.cosas_pieza("montón de tierra", e["x"] + math.cos(a) * r_ * k, e["y"] + math.sin(a) * r_ * k, 17 * sc, 12 * sc, 2.6 * sc,
                                 desde=tU(F["viejo"][0] + 0.1), hasta=tU(0.95)))
    for i in range(9):
        a, r_ = 2 * math.pi * rnd.random(), (0.15 + 0.6 * rnd.random()) * R
        sc = 0.9 + 0.6 * rnd.random()
        co.append(ME.cosas_pieza("montículo", e["x"] + math.cos(a) * r_ * k, e["y"] + math.sin(a) * r_ * k, 14 * sc, 12 * sc, 2.8 * sc,
                                 animado=True, desde=tU(F["mont"][0]), hasta=tU(F["mont"][1])))
    for i in range(max(0, int(e["volteos"]))):
        r_, a, gv = (0.5 + 0.1 * i) * R, math.pi * i + 0.7, float(e.get("volteos_tamano") or 1)
        co.append(ME.cosas_pieza("volteo", e["x"] + math.cos(a) * r_ * k, e["y"] + math.sin(a) * r_ * k, 8.6 * gv, 2.5 * gv, 3.3 * gv,
                                 -math.sin(a), math.cos(a), animado=True, desde=float(e["t"]) if hd > 0 else tU(F["volteos"][0]), hasta=tU(F["volteos"][1])))
    for i in range(max(0, int(e["obreros"]))):
        a, r_ = 2 * math.pi * (i + rnd.random()) / max(1, int(e["obreros"])), 0.42 * R + (rnd.random() - 0.5) * 0.5 * R
        g = e["gente_tamano"]
        co.append(ME.cosas_pieza("obrero", e["x"] + math.cos(a) * r_ * k, e["y"] + math.sin(a) * r_ * k, 0.5 * g, 0.5 * g, 1.75 * g,
                                 gente=True, animado=True, desde=tU(F["obreros"][0]), hasta=tU(F["obreros"][1])))
    return co


def puntos(e, u, G):
    return [(e["x"], e["y"])]


def origen(e, G):
    return e["x"], e["y"]
