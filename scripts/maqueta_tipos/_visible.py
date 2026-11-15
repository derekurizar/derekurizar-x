"""Lo común de `aparecer` y `desaparecer`: dónde está la pieza que entra o sale (para M3D6: que se vea mientras pasa)."""


def puntos(e, u, G):
    pz = G["por_id"].get(e["pieza"])
    rg = G["m3"].reglas(pz["tipo"]) if pz else None
    M = G["R"]["_moviles"].get(e["pieza"])
    if M and len(M):
        t = e["t"] + e["dur"] * u
        if len(M) == 1:
            return [M.en(t, 0)[:2]]
        vis = [M.en(t, n)[:2] for n in range(0, len(M), max(1, len(M) // 12)) if M.en(t, n)[5]]
        return vis[:1] or []
    c = rg.centro(pz, G) if rg and hasattr(rg, "centro") else None
    return [c] if c else []
