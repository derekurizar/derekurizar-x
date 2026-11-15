"""Evento «ruptura»: el punto de la traza donde nace (s0) y cuántos km rompe hacia cada lado (sin pasarse del trazo)."""


def resolver(e, X, que):
    M3 = X.m3
    f = X.por_id[e["pieza"]]
    cad = f["cadena"]
    l = X.lugar(e.get("desde"), que)
    s0, d0 = M3.mas_cercano(cad, l["x"], l["y"])
    if d0 > 40:
        X.avisos.append("%s: `desde` queda a %.0f km del trazo de «%s»; la ruptura nace en el punto más cercano del trazo" % (que, d0, f["id"]))
    pide = {"mas": 0.0, "menos": 0.0}
    ext = (cad[-1][0] - cad[0][0], cad[-1][1] - cad[0][1])

    def lado(rumbo):   # ¿hacia dónde crece s respecto de un rumbo?
        d = M3.RUMBOS[rumbo]
        return "mas" if ext[0] * d[0] + ext[1] * d[1] >= 0 else "menos"
    dados = [k for k in M3.RUMBOS if e.get("km_" + k) is not None]
    if dados:
        for k in dados:
            pide[lado(k)] += float(e["km_" + k])
    else:
        hacia, km = e.get("hacia", "ambos"), float(e.get("km", 0))
        if hacia == "ambos":
            pide = {"mas": km / 2, "menos": km / 2}
        else:
            pide[lado(hacia)] = km
    if pide["mas"] + pide["menos"] <= 0:
        raise M3.Falla("M3D2", "%s: sin kilómetros: usa `km` (con `hacia`) o `km_oeste` / `km_este`" % que)
    hay = {"mas": cad[-1][2] - s0, "menos": s0 - cad[0][2]}
    for k in ("mas", "menos"):
        if pide[k] > hay[k] + 1.0:
            X.avisos.append("%s: pide %.0f km hacia %s y el trazo de «%s» solo tiene %.0f km desde «%s»: llega hasta el final del trazo"
                            % (que, pide[k], "donde crece el trazo (este/norte)" if k == "mas" else "donde empieza (oeste/sur)", f["id"], hay[k], e.get("desde")))
    return {"pieza": f["id"], "s0": round(s0, 3), "km_mas": round(min(pide["mas"], hay["mas"]), 3), "km_menos": round(min(pide["menos"], hay["menos"]), 3)}


def cerrar(rupturas, X):
    if len(rupturas) > X.m3.NR_MAX:
        raise X.m3.Falla("M3D2", "hay más de %d eventos `ruptura` (tope del motor)" % X.m3.NR_MAX)


def puntos(e, u, G):
    cad = G["por_id"][e["pieza"]]["cadena"]
    return [G["m3"].punto_en_s(cad, e["s0"] + sg * km * u) for sg, km in ((1, e["km_mas"]), (-1, e["km_menos"])) if km > 0]


def origen(e, G):
    return G["m3"].punto_en_s(G["por_id"][e["pieza"]]["cadena"], e["s0"])
