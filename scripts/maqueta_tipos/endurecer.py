"""Evento «endurecer»: llueve sobre el depósito que dejó un `piroclastico` en una pieza `aldeabarranca` (o
`faldavolcan`): la ceniza gris suelta se moja, se oscurece y se parte en placas de costra dura, con grietas que se abren
una tras otra y charcos que se secan al escampar. Ilustra un proceso: no afirma un espesor ni un tiempo.

El depósito es EL MISMO que dibujó el piroclastico: estas reglas copian lo que resolvió el último piroclastico de la
misma pieza que va antes en `eventos` (su cauce, su desborde, su lóbulo, su semilla y su índice entre los piroclasticos,
que fija su azar). Sin piroclastico antes, resuelven uno con sus valores por defecto (aviso): la costra aparece sola.
Va DESPUÉS de que el piroclastico termina y se oscurece (t ≥ su t + dur + 4 s) y con su `queda: true`.
Resuelto: {pieza, fx, fy, rumbo, tamano, k, base, cauce, lado, s_spill, s_fin, fuente, r_fin, caja, pulsos, desborde,
p_semilla, ie, lluvia, costra, grietas, semilla}."""
from maqueta_tipos import piroclastico as PI

COPIA = ("fx", "fy", "rumbo", "tamano", "k", "base", "cauce", "lado", "s_spill", "s_fin", "fuente", "r_fin", "caja",
         "pulsos", "desborde")


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz or pz.get("tipo") not in ("aldeabarranca", "faldavolcan"):
        raise X.m3.Falla("M3D2", "%s: `pieza` tiene que ser una aldeabarranca o una faldavolcan (la del piroclastico)" % que)
    piros = [ev for ev in X.eventos if ev.get("tipo") == "piroclastico"]
    mios = [(i, ev) for i, ev in enumerate(piros) if ev.get("pieza") == pid]
    if mios:
        ie, P = mios[-1]
        fin = float(P.get("t", 0)) + float(P.get("dur", 8)) + 4.0
        if float(e.get("t", 0)) < fin - 0.05:
            X.avisos.append("%s: empieza en %.2f s, antes de que el piroclastico de «%s» termine y se oscurezca (%.2f s): "
                            "la costra se ve antes que el depósito. Muévelo a t ≥ %.2f" % (que, float(e.get("t", 0)), pid, fin, fin))
        if not P.get("queda", True):
            X.avisos.append("%s: el piroclastico de «%s» va con queda: false; su depósito se va y esta costra queda sola" % (que, pid))
    else:
        ie = len(piros)
        avisos = list(X.avisos)
        P = PI.resolver({"pieza": pid, "dur": 8.0, "pulsos": 3, "desborde": 0.8, "cubre": 0.6, "bloques": 0, "gente": 0,
                         "semilla": int(e.get("semilla", 1))}, X, que)
        X.avisos[:] = avisos
        X.avisos.append("%s: no hay un piroclastico antes sobre «%s»: la costra se dibuja sobre el depósito que dejaría uno "
                        "por defecto (pulsos 3, desborde 0.8, cubre 0.6)" % (que, pid))
    out = {"pieza": pid}
    out.update({k: P[k] for k in COPIA})
    out.update({"p_semilla": int(P.get("semilla", 1)), "ie": ie,
                "lluvia": float(e.get("lluvia", 0.8)), "costra": float(e.get("costra", 0.85)),
                "grietas": float(e.get("grietas", 0.6)), "semilla": int(e.get("semilla", 1))})
    return out


def puntos(e, u, G):
    """El depósito: el cauce junto al desborde y, si hay lóbulo, su arranque en la aldea (M3D6)."""
    p = [PI._en(e, e["s_spill"])]
    if e["r_fin"] > 0 and e["fuente"]:
        f = e["fuente"][len(e["fuente"]) // 3]
        p.append(PI._mundo(e, f[0], f[1]))
    return p
