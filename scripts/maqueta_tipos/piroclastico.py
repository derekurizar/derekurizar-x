"""Evento «piroclastico»: un flujo piroclástico DE CERCA sobre una pieza `aldeabarranca` (o `faldavolcan`). Pulsos de
nube gris turbulenta, con la base densa, bajan por la barranca uno tras otro y dejan su depósito en el fondo; el último
sube hasta la orilla junto al puente (en la falda: al pie del cono), se sale del cauce, pasa sobre la carretera y entra a
la aldea por el lado de la barranca: entierra las casas hasta el techo con ceniza gris y bloques, y el depósito echa humo.
La gente que pone el evento deja la calle antes de que llegue; nadie queda alcanzado. Lo enterrado queda así.

Todo en METROS LOCALES de la pieza (u: hacia el volcán; v: a su izquierda); el módulo lo lleva al mundo con el mismo
`rumbo`, `tamano` y centro que la pieza (la misma cuenta que aldeabarranca.py / faldavolcan.py).

- EL CAUCE: el de la pieza (aldeabarranca.Geo.va / faldavolcan.cauce_local), de arriba abajo, con su medio ancho.
- EL DESBORDE: el último pulso sube por encima de la orilla en `s_spill` (aguas arriba del puente: el puente queda a la
  vista, entero) y se abre en un lóbulo cuyo frente avanza por un campo de distancias `d` medido desde la orilla del lado
  de la aldea (cada punto de la orilla con su castigo `pen`: el material sale del desborde y corre orilla abajo). `R_fin`
  es la distancia que deja enterrada la fracción `cubre` de la aldea (medida sobre una muestra de sus calles y lotes).
- LA GENTE: `gente` vecinos sobre las calles; salen en `t_sale` (antes del desborde, con margen) y se van; con `vacia`
  no vuelven; sin `vacia`, dos quedan al final fuera del depósito, mirándolo.
Resuelto: {pieza, fx, fy, rumbo, k, tamano, base, cauce [[u, v, s, hw]], lado, s_spill, s_fin, fuente [[u, v, pen]],
r_fin, caja [u0, u1, v0, v1], pulsos, desborde, cubre, bloques, humo, vacia, queda, semilla, gente [[u, v, du, dv, sale]],
miran [[u, v, du, dv]], x_desb}."""
import math

from maqueta_tipos import aldeabarranca as AB
from maqueta_tipos import faldavolcan as FV

X_DESB = 0.6        # fracción de `dur` en que el último pulso llega al desborde (la misma constante que piroclastico.js)
X_LOBULO = 0.95     # fracción de `dur` en que el lóbulo se detiene
SALE_ANTES = 3.2    # s: la gente ya se fue este tanto antes del desborde (camina y se desvanece en ≈ 2.6 s)


def _s(pts):
    S = [0.0]
    for i in range(1, len(pts)):
        S.append(S[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return S


def _cerca(pts, u, v):
    best, bi = 1e18, 0
    for i, (a, b) in enumerate(pts):
        d = (a - u) ** 2 + (b - v) ** 2
        if d < best:
            best, bi = d, i
    return bi


def _d(fuente, u, v):
    return min(math.hypot(u - a, v - b) + p for a, b, p in fuente)


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    tipo = (pz or {}).get("tipo")
    if not pz or tipo not in ("aldeabarranca", "faldavolcan") or "rumbo" not in pz:
        raise X.m3.Falla("M3D2", "%s: `pieza` tiene que ser una aldeabarranca o una faldavolcan (el flujo baja por su cauce)" % que)
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    tam = float(pz["tamano"])
    k = tam / um
    desborde = float(e.get("desborde", 0.8))
    cubre = float(e.get("cubre", 0.6))
    D = max(0.5, float(e.get("dur", 8.0)))

    if tipo == "aldeabarranca":
        G = AB.Geo(float(pz["ancho_barranca_m"]), AB.fase(int(pz["semilla"])))
        cl, u = [], AB.UTOP - 40
        while u > AB.UBOT:
            cl.append((u, G.va(u)))
            u -= 12
        S = _s(cl)
        hw = [G.hw(p[0]) for p in cl]
        vb, _, _ = G.cruce()
        ib = _cerca(cl, G.ur(vb), vb)
        s_b = S[ib]
        s_spill = max(60.0, s_b - 45.0)
        lado = -1                                   # la aldea queda a v menor que el eje (a la derecha de quien baja)
        fuente = []
        for (uu, vv), s, h in zip(cl, S, hw):
            if s_spill - 10 <= s <= s_spill + 300:
                fuente.append((uu, vv - 1.2 * h - 4, 0.7 * max(0.0, s - s_spill) + 0.35 * max(0.0, s_spill - s)))
        # la muestra de la aldea (calles y lotes): lo que `cubre` mide
        muestra = []
        for uu in range(-200, 111, 10):
            for vv in range(-170, 100, 10):
                if vv < G.va(uu) - 1.2 * G.hw(uu) - 8:
                    muestra.append((uu, vv))
        # la gente: sobre la calle principal (sale hacia −u) y las tres que la cruzan (salen hacia −v)
        def en_calle(i, h):
            if i % 3 == 0:
                return (-170 + 270 * h, -10.0, -1.0, 0.0)
            uu = (72.0, -38.0, -142.0)[(i // 3 + i) % 3]
            top = G.va(uu) - G.hw(uu) * 1.25 - 26
            return (uu, -150 + (top + 150) * h, 0.0, -1.0)
        caja = [-330.0, 330.0, -260.0, 0.0]
        caja[3] = max(G.va(uu) + G.hw(uu) * 1.3 for uu in range(-330, 331, 30))
        s_fin = min(S[-1] - 20, s_b + 320)
    else:
        ph = FV.fase(int(pz["semilla"]))
        cl = FV.cauce_local(ph)
        S = _s(cl)
        hw = [max(10.0, FV.ancho(0, min(1.0, math.hypot(uu - FV.US, vv) / FV.RB)) * 0.9) for uu, vv in cl]
        ip = len(cl) - 1
        for i, (uu, vv) in enumerate(cl):
            if math.hypot(uu - FV.US, vv) >= FV.RB * 0.86:
                ip = i
                break
        s_spill = S[ip]
        lado = 0
        fuente = [(uu, vv, 0.6 * max(0.0, s - s_spill)) for (uu, vv), s in zip(cl, S) if s >= s_spill - 5]
        muestra = [(uu, vv) for uu in range(-160, 61, 10) for vv in range(-120, 121, 10)]

        def en_calle(i, h):
            a = (i * 2.399) % (2 * math.pi)
            r = 30 + 60 * h
            uu, vv = FV.PUEBLO[0] + 0.6 * r * math.cos(a), FV.PUEBLO[1] + r * math.sin(a)
            return (uu, vv, -1.0, 0.0)
        caja = [-300.0, 260.0, -260.0, 260.0]
        s_fin = S[-1]

    # el alcance del lóbulo: la fracción `cubre` de la aldea queda dentro
    if desborde < 0.15:
        r_fin = 0.0
    else:
        ds = sorted(_d(fuente, uu, vv) for uu, vv in muestra)
        r_fin = max(35.0, ds[min(len(ds) - 1, int(round(cubre * (len(ds) - 1))))] if ds else 35.0)
    if desborde < 0.15:
        s_fin = min(s_fin, s_spill + 120)

    # la gente: sale antes del desborde con margen (si `dur` es corto, sale antes de que empiece el evento)
    n = int(e.get("gente", 8))
    sale0 = min(0.12 * D, X_DESB * D - SALE_ANTES)
    gente = []
    for i in range(n):
        h = ((i * 0.6180339887 + 0.37 * (int(e.get("semilla", 1)) % 7)) % 1.0)
        uu, vv, du, dv = en_calle(i, h)
        gente.append([round(uu, 2), round(vv, 2), du, dv, round(sale0 + 0.11 * i % 0.9, 3)])
    miran = []
    if not e.get("vacia", True) and r_fin > 0:
        lejos = sorted(((_d(fuente, uu, vv), uu, vv) for uu, vv in muestra), reverse=True)
        for dd, uu, vv in lejos[:40]:
            if dd > r_fin + 25 and len(miran) < 2:
                # mira hacia la fuente más cercana
                a, b, _ = min(fuente, key=lambda f: math.hypot(uu - f[0], vv - f[1]) + f[2])
                L = math.hypot(a - uu, b - vv) or 1.0
                miran.append([round(uu + 1.2 * len(miran), 2), round(vv, 2), round((a - uu) / L, 3), round((b - vv) / L, 3)])
    if pz.get("personas"):
        X.avisos.append("%s: «%s» trae personas: %d; siguen caminando sobre el depósito. Ponle personas: 0 (la gente que sale "
                        "la pone este evento con `gente`)" % (que, pid, int(pz["personas"])))
    if pz.get("vehiculos"):
        X.avisos.append("%s: «%s» trae vehiculos: %d; siguen pasando sobre el depósito. Ponle vehiculos: 0" % (que, pid, int(pz["vehiculos"])))

    return {"pieza": pid, "fx": pz["x"], "fy": pz["y"], "rumbo": float(pz["rumbo"]), "tamano": tam, "k": k, "base": tipo,
            "cauce": [[round(a, 2), round(b, 2), round(s, 2), round(h, 2)] for (a, b), s, h in zip(cl, S, hw)],
            "lado": lado, "s_spill": round(s_spill, 2), "s_fin": round(s_fin, 2),
            "fuente": [[round(a, 2), round(b, 2), round(p, 2)] for a, b, p in fuente],
            "r_fin": round(r_fin, 2), "caja": [round(c, 1) for c in caja],
            "pulsos": int(e.get("pulsos", 3)), "desborde": desborde, "cubre": cubre, "bloques": int(e.get("bloques", 15)),
            "humo": e.get("humo", True) is not False, "vacia": e.get("vacia", True) is not False,
            "queda": e.get("queda", True) is not False, "semilla": int(e.get("semilla", 1)),
            "gente": gente, "miran": miran, "x_desb": X_DESB}


def _mundo(e, u, v):
    a = math.radians(e["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    return e["fx"] + (u * ux - v * uy) * e["k"], e["fy"] + (u * uy + v * ux) * e["k"]


def _en(e, s):
    C = e["cauce"]
    for i in range(1, len(C)):
        if C[i][2] >= s:
            a, b = C[i - 1], C[i]
            f = (s - a[2]) / ((b[2] - a[2]) or 1e-9)
            return _mundo(e, a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    return _mundo(e, C[-1][0], C[-1][1])


def puntos(e, u, G):
    """El frente del último pulso en la fracción u; desde el desborde, también el centro del lóbulo (M3D6)."""
    xd = e["x_desb"]
    s = e["s_spill"] * min(1.0, 0.15 + 0.85 * u / xd)
    p = [_en(e, s)]
    if u >= xd and e["r_fin"] > 0 and e["fuente"]:
        f = e["fuente"][0]
        p.append(_mundo(e, f[0], f[1]))
    return p


def origen(e, G):
    return _en(e, 0.0)
