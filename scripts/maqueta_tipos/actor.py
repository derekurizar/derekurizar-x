"""Pieza «actor»: UN objeto (carro, persona, bus…) que sigue un camino con claves en el tiempo, orientado en la dirección
de marcha. El camino: `camino` (un camino con nombre del mundo), `desde` + `hacia` (dos lugares: una recta) o `puntos`
(una polilínea propia); o `lugar` (quieto, mirando a `rumbo`).

Las CLAVES ([{t, s | lugar | vel_kmh}], crecientes en t) fijan el estado en su segundo:
- con posición (`s`: metros desde el inicio del camino o «40%»; o `lugar`: su proyección sobre el camino), el actor está
  ahí en t: entre dos claves va en línea recta en el tiempo (la velocidad que haga falta para llegar);
- con `vel_kmh` (y sin posición), sigue desde donde iba a esa velocidad hasta la siguiente clave;
- después de la última, sigue a su última velocidad (0 si la última fijó posición sin velocidad) y se detiene al final del
  camino. Sin claves: quieto en el inicio. Un evento `mover` añade dos claves (de donde esté a su lugar en `dur`).
La trayectoria que se dibuja va suavizada (`suavizado_s`): arranca y frena sin saltos. Resuelta: {objeto, camino, T, S, h,
tamano, variante, usa}."""
import math

from maqueta_tipos import _movimiento as MV
from maqueta_tipos.esquema import cadena


def resolver(p, X, que):
    u = X.S.unidad_m
    publicar = {}
    formas = [k for k in ("camino", "desde", "puntos", "lugar") if p.get(k) is not None]
    if len(formas) != 1:
        raise X.m3.Falla("M3D2", "%s: el actor lleva UNA forma de camino: `camino`, `desde` + `hacia`, `puntos` o `lugar` (trae: %s)" % (que, ", ".join(formas) or "ninguna"))
    if p.get("camino") is not None:
        nombre, cad = p["camino"], MV.camino(X, p["camino"], que)
    else:
        nombre = p["id"]
        if p.get("desde") is not None:
            if p.get("hacia") is None:
                raise X.m3.Falla("M3D2", "%s: con `desde` va `hacia` (el lugar al que llega)" % que)
            a, b = X.lugar(p["desde"], que + " → desde"), X.lugar(p["hacia"], que + " → hacia")
            pts = [[a["x"], a["y"]], [b["x"], b["y"]]]
        elif p.get("puntos") is not None:
            pts = [list(X.S.punto(q[0], q[1])) for q in p["puntos"]]
        else:
            l = X.lugar(p["lugar"], que + " → lugar")
            r = math.radians(float(p.get("rumbo", 0)))
            d = 0.5 / u
            pts = [[l["x"] - math.cos(r) * d, l["y"] - math.sin(r) * d], [l["x"] + math.cos(r) * d, l["y"] + math.sin(r) * d]]
        cad = cadena(pts)
        if cad[-1][2] <= 0:
            raise X.m3.Falla("M3D2", "%s: el camino del actor no tiene largo (desde y hacia son el mismo punto)" % que)
        publicar = {nombre: cad}
    if not X.m3.ficha(p["objeto"], "objeto"):
        raise X.m3.Falla("M3D2", "%s: «%s» no es un objeto del catálogo (hay: %s)" % (que, p["objeto"], ", ".join(X.m3.tipos("objeto"))))
    X.__dict__.setdefault("actores", {})[p["id"]] = {"cad": cad, "p": p, "quieto": p.get("lugar") is not None}
    r = {"objeto": p["objeto"], "camino": nombre, "h": round(p["suavizado_s"] / 2, 3), "tamano": p["tamano"],
         "variante": int(p.get("variante", MV.hash_(len(X.piezas), 41) * 1000)), "lev": p.get("lev_m", 0), "usa": [p["objeto"]]}
    if publicar:
        r["_caminos"] = publicar
    return r


def trayectoria(claves, cad, u, t1, X, que):
    """Las claves → (T, S) lineal por tramos (ver la cabecera)."""
    L = cad[-1][2]
    T, S = [], []
    s, v, t = 0.0, 0.0, None
    for k in claves:
        tk = float(k["t"])
        tiene = k.get("s") is not None or k.get("lugar") is not None
        if t is None:
            s = MV.posicion_en(X, k["s"] if k.get("s") is not None else k["lugar"], cad, que) if tiene else 0.0
        elif tiene:
            s = MV.posicion_en(X, k["s"] if k.get("s") is not None else k["lugar"], cad, que)
        else:
            s = S[-1] + v * (tk - t)
        if T and tk - T[-1] < 1e-6:
            S[-1] = s
        else:
            T.append(tk); S.append(s)
        v = float(k["vel_kmh"]) * MV.KMH / u if k.get("vel_kmh") is not None else (0.0 if tiene else v)
        t = tk
    if not T:
        return [0.0], [0.0]
    if t1 > T[-1]:
        T.append(t1); S.append(S[-1] + v * (t1 - T[-2]))
    # el camino se acaba: ahí se queda
    oT, oS = [T[0]], [min(max(S[0], 0.0), L)]
    for a in range(1, len(T)):
        t0, s0, ta, sa = T[a - 1], S[a - 1], T[a], S[a]
        for borde in (L, 0.0):
            if (s0 - borde) * (sa - borde) < 0:
                tc = t0 + (ta - t0) * (borde - s0) / (sa - s0)
                oT.append(tc); oS.append(borde)
        oT.append(ta); oS.append(min(max(sa, 0.0), L))
    return MV.redondear(oT, oS)


def con_eventos(lista, eventos, X):
    u = X.S.unidad_m
    for pz in lista:
        info = X.actores[pz["id"]]
        p, cad = info["p"], info["cad"]
        que = "pieza «%s»" % pz["id"]
        claves = [dict(k) for k in p.get("claves") or []]
        if info["quieto"]:
            claves = [{"t": 0, "s": 0.5}]
        for e in eventos:
            if e["tipo"] == "mover" and e.get("actor") == pz["id"]:
                claves.append({"t": e["t"], "_mover": True})
                claves.append({"t": e["t"] + e["dur"], "s": e["s"] * u, "vel_kmh": 0})
        claves.sort(key=lambda k: (float(k["t"]), 0 if k.get("_mover") else 1))
        T, S = trayectoria(claves, cad, u, X.dur + MV.T_DESPUES, X, que)
        pz["T"], pz["S"] = T, S
        X.moviles[pz["id"]] = MV.movil_de([(0, T, S)], [cad], pz["h"], X)


def centro(pz, G):
    M = G["R"]["_moviles"].get(pz["id"])
    return M.en(G["R"]["dur"] / 2, 0)[:2] if M else None
