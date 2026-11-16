"""Pieza «flujo»: el tráfico. N vehículos (tipos mezclados por proporción) en uno o varios carriles (caminos con nombre del
mundo: los de la receta `carretera` de un esquema o los de una pieza `carretera`), con densidad, velocidad base y semilla.
Los eventos `frenar` y `acelerar` cambian la velocidad de un tramo (o de todo el flujo) y la cola se forma sola: el modelo
de Newell de scripts/maqueta_tipos/_movimiento.py (lo explica su cabecera). Todo se calcula aquí, una vez (con_eventos),
y viaja resuelto a motor.js: por vehículo, su carril, su tipo, su variante de color y su trayectoria (T, S).

Resuelta: {carriles: [nombres], largos, tipos: [objetos], vehiculos: [[carril, tipo, variante, T, S]], h, tamano, luces, usa}.
"""
import math

from maqueta_tipos import _movimiento as MV


def resolver(p, X, que):
    nombres = p["carriles"]
    cads = [MV.camino(X, c, que + " → carriles") for c in nombres]
    for o in p["tipos"]:
        if not X.m3.ficha(o, "objeto"):
            raise X.m3.Falla("M3D2", "%s: «%s» no es un objeto del catálogo (hay: %s)" % (que, o, ", ".join(X.m3.tipos("objeto"))))
    X.__dict__.setdefault("flujos", {})[p["id"]] = {"cads": cads, "p": p}
    tipos = sorted(p["tipos"])
    return {"carriles": list(nombres), "largos": [round(c[-1][2], 3) for c in cads], "tipos": tipos,
            "h": round(p["suavizado_s"] / 2, 3), "tamano": p["tamano"], "luces": p["luces"], "usa": tipos}


def carriles_de(pz, e, que, X):
    """Los índices de los carriles del flujo que toca un evento (`carriles`: nombres o números 1…N; sin él, todos)."""
    if not e.get("carriles"):
        return list(range(len(pz["carriles"])))
    out = []
    for c in e["carriles"]:
        if isinstance(c, str) and c.isdigit():
            c = int(c)
        if isinstance(c, int) and 1 <= c <= len(pz["carriles"]):
            out.append(c - 1)
        elif c in pz["carriles"]:
            out.append(pz["carriles"].index(c))
        else:
            raise X.m3.Falla("M3D2", "%s: `carriles` «%s» no es un carril del flujo «%s» (%s)" % (que, c, pz["id"], ", ".join(pz["carriles"])))
    return out


def tramo_de(car, cad, e, X):
    """[a, b) del evento sobre este carril: la proyección de su punto `en` y su largo (en el sentido de la marcha)."""
    a = MV.proyectar(cad, e["x"], e["y"])[0]
    return a, min(cad[-1][2], a + e["largo"])


def con_eventos(lista, eventos, X):
    for pz in lista:
        info = X.flujos[pz["id"]]
        p, cads = info["p"], info["cads"]
        u = X.S.unidad_m
        carriles = [MV.Carril(n, cad[-1][2], p["vel_kmh"] * MV.KMH / u) for n, cad in zip(pz["carriles"], cads)]
        for n_e, e in enumerate(eventos):
            if e.get("flujo") != pz["id"] or e["tipo"] not in ("frenar", "acelerar"):
                continue
            v = e["vel_kmh"] * MV.KMH / u
            for ci in e["_carriles"]:
                car, cad = carriles[ci], cads[ci]
                if e.get("x") is None:                      # acelerar sin tramo: la base de todo el carril
                    car.base += MV.escalera(car.base_en(e["t"]), v, e["t"], e["dur"], final=False)
                    continue
                a, b = tramo_de(car, cad, e, X)
                z = next((z for z in car.tramos if z["a"] < b and a < z["b"]), None)
                if e["tipo"] == "frenar" or z is None:
                    if z is None:
                        z = {"a": a, "b": b, "esc": []}
                        car.tramos.append(z)
                    desde = car.tramo_en(z, e["t"])
                    z["esc"] += MV.escalera(car.base_en(e["t"]) if desde is None else desde, v, e["t"], e["dur"], final=False)
                else:                                       # acelerar sobre un tramo frenado: lo suelta
                    desde = car.tramo_en(z, e["t"])
                    fin = None if v >= car.base_en(e["t"] + e["dur"]) - 1e-9 else False
                    z["esc"] += MV.escalera(car.base_en(e["t"]) if desde is None else desde, v, e["t"], e["dur"], final=fin)
        medidas = {o: X.m3.ficha(o, "objeto")["medidas"] for o in pz["tipos"]}
        vehs, tope = MV.generar(carriles, p["tipos"], medidas, p["densidad"], p["reaccion_s"], X.dur, p["semilla"], MV.hash_)
        if p["densidad"] > tope + 1e-9:
            raise X.m3.Falla("M3D2", "pieza «%s»: densidad %g vehículos por km y carril no cabe a %g km/h (con τ = %g s, el tope es %.1f): bájala o baja `vel_kmh`"
                             % (pz["id"], p["densidad"], max(c.vmax() for c in carriles) * u / MV.KMH, p["reaccion_s"], tope))
        MV.flujo(carriles, vehs, p["reaccion_s"], X.dur)
        planos = [v for lista_c in vehs for v in lista_c]
        tipos = pz["tipos"]
        pz["vehiculos"] = [[v["c"], tipos.index(v["o"]), v["var"], v["T"], v["S"]] for v in planos]
        X.moviles[pz["id"]] = MV.movil_de([(v["c"], v["T"], v["S"]) for v in planos], cads, pz["h"], X)


def centro(pz, G):
    M = G["R"]["_moviles"].get(pz["id"])
    if not M or not len(M):
        return None
    x, y, *_ = M.en(G["R"]["dur"] / 2, len(M) // 2)
    return x, y
