"""Lo que se mueve en la maqueta (piezas `actor` y `flujo`, eventos `frenar`, `acelerar`, `mover`): el MODELO, en un solo
sitio. Lo calcula Python una vez al resolver el maqueta.json; motor.js recibe el resultado (tramos de cada trayectoria)
y solo lo evalúa: así los gates (la cámara que sigue a un carro, las anotaciones que se pegan a él) y el dibujo ven
exactamente lo mismo, y el cuadro de t sale de t (seek puro).

Trayectoria = s(t) LINEAL POR TRAMOS sobre un camino: dos listas T (s, crecientes) y S (metros desde el inicio del
camino); fuera de [T0, Tn] se extiende con la pendiente del extremo. Lo que se dibuja es la trayectoria SUAVIZADA con
una ventana de 2h segundos (media móvil):

    s̄(t) = (F(t + h) − F(t − h)) / 2h,   F = ∫ s dt   (cuadrática por tramos: forma cerrada)
    v̄(t) = (s(t + h) − s(t − h)) / 2h

El tráfico (`flujo`) es el modelo de Newell (2002) de seguimiento, que es LWR con diagrama triangular:

    x_i(t) = min( libre_i(t),  x_{i−1}(t − τ) − δ_i )

- libre_i: la trayectoria del vehículo i SOLO en el campo de velocidades del carril: la velocidad base (que `acelerar`
  sin tramo cambia) y los TRAMOS [a, b) con su velocidad en el tiempo (`frenar` crea uno; `acelerar` sobre él lo
  suelta). Cada cambio de velocidad en el tiempo es una escalera de PASOS escalones en `transicion` segundos. Se calcula
  por eventos (llegar a un borde de tramo o a un cambio de tiempo): exacto, sin pasos de simulación.
- x_{i−1}(t − τ) − δ_i: la del de adelante corrida τ s (reacción) y δ_i m (los dos medios largos + 2 m de hueco). El
  mínimo de dos lineales por tramos es lineal por tramos: se calcula una vez por vehículo, del primero al último.
- La COLA: cuando un tramo frena, el primero que llega frena; el de atrás queda τ s y δ m detrás de él, y así: la cola
  crece hacia atrás a w = δ/τ m/s (≈ 8 m/s con un carro de 4.5 m y τ = 0.8 s) mientras lleguen más rápido de lo que salen.
- NUNCA SE ATRAVIESAN: x_i ≤ x_{i−1}(t − τ) − δ ≤ x_{i−1}(t) − δ (la posición no decrece) y la media móvil, que es
  lineal y monótona, conserva la desigualdad: también en lo suavizado hay ≥ δ entre centros.
- Arranque: el hueco inicial entre vehículos es ≥ δ + v·τ (si no, el de atrás saltaría hacia atrás en t0): por eso la
  densidad tiene tope (lo dice el error).
"""
import bisect
import math

KMH = 1 / 3.6
PASOS = 6            # escalones de una transición de velocidad (con la ventana de suavizado ya no se notan)
HUECO_M = 2.0        # metros entre parachoques en la cola
T_ANTES = 4.0        # la trayectoria empieza este tanto antes de 0 (lo de antes no se ve: absorbe el arranque)
T_DESPUES = 4.0
REDONDEO = 3         # decimales de T y S que viajan al motor (Python evalúa los MISMOS números)


def hash_(i, k=0):
    """El azar fijo de motor.js (ctx.hash) en Python: el mismo (i, k) da el mismo número en [0, 1)."""
    M = 0xFFFFFFFF

    def imul(a, b):
        return (a * b) & M
    h = imul((int(i) + 0x9E3779B9) & M, 0x85EBCA6B) ^ imul((int(k) + 0x7F4A7C15) & M, 0xC2B2AE35)
    h ^= h >> 15
    h = imul(h, 0x2C1B3C6D)
    h ^= h >> 12
    return (h & M) / 4294967296.0


# ---------- trayectorias lineales por tramos ----------
def pendiente(T, S, k):
    return (S[k + 1] - S[k]) / (T[k + 1] - T[k]) if T[k + 1] > T[k] else 0.0


def tramo(T, t):
    """Índice k del tramo [T[k], T[k+1]] que contiene t (−1 antes del inicio, n−1 después del final)."""
    if t < T[0]:
        return -1
    return min(len(T) - 2, bisect.bisect_right(T, t) - 1) if len(T) > 1 else -1


def pos(T, S, t):
    if len(T) == 1:
        return S[0]
    if t <= T[0]:
        return S[0] + pendiente(T, S, 0) * (t - T[0])
    if t >= T[-1]:
        return S[-1] + pendiente(T, S, len(T) - 2) * (t - T[-1])
    k = tramo(T, t)
    return S[k] + pendiente(T, S, k) * (t - T[k])


def integral(T, S):
    """F en cada punto de quiebre (F[0] = 0): la integral de s(t)."""
    F = [0.0]
    for k in range(len(T) - 1):
        F.append(F[-1] + (S[k] + S[k + 1]) / 2 * (T[k + 1] - T[k]))
    return F


def integral_en(T, S, F, t):
    if len(T) == 1:
        return S[0] * (t - T[0])
    if t <= T[0]:
        v, d = pendiente(T, S, 0), t - T[0]
        return S[0] * d + v * d * d / 2
    if t >= T[-1]:
        v, d = pendiente(T, S, len(T) - 2), t - T[-1]
        return F[-1] + S[-1] * d + v * d * d / 2
    k = tramo(T, t)
    v, d = pendiente(T, S, k), t - T[k]
    return F[k] + S[k] * d + v * d * d / 2


def suave(T, S, F, h, t):
    """(s̄, v̄) en t: posición y velocidad de la trayectoria suavizada con la ventana ±h."""
    if h <= 0:
        k = max(0, tramo(T, t)) if len(T) > 1 else 0
        return pos(T, S, t), (pendiente(T, S, min(k, len(T) - 2)) if len(T) > 1 else 0.0)
    return (integral_en(T, S, F, t + h) - integral_en(T, S, F, t - h)) / (2 * h), (pos(T, S, t + h) - pos(T, S, t - h)) / (2 * h)


def simplificar(T, S, tol=1e-4):
    """Quita los puntos de quiebre colineales y los repetidos en t."""
    oT, oS = [T[0]], [S[0]]
    for k in range(1, len(T)):
        if T[k] - oT[-1] < 1e-7:
            oS[-1] = min(oS[-1], S[k]); continue
        oT.append(T[k]); oS.append(S[k])
        while len(oT) >= 3:
            t0, t1, t2 = oT[-3:]
            s0, s1, s2 = oS[-3:]
            if abs(s0 + (s2 - s0) * (t1 - t0) / (t2 - t0) - s1) < tol:
                del oT[-2], oS[-2]
            else:
                break
    return oT, oS


def minimo(A, B):
    """El mínimo de dos trayectorias lineales por tramos (A y B: (T, S)), en la unión de sus dominios."""
    (TA, SA), (TB, SB) = A, B
    ts = sorted(set(TA) | set(TB))
    oT, oS = [], []
    for i, t in enumerate(ts):
        a, b = pos(TA, SA, t), pos(TB, SB, t)
        if i:
            tp = ts[i - 1]
            ap, bp = pos(TA, SA, tp), pos(TB, SB, tp)
            if (ap - bp) * (a - b) < 0:          # se cruzan dentro del intervalo: el punto de cruce
                u = (ap - bp) / ((ap - bp) - (a - b))
                tc = tp + (t - tp) * u
                oT.append(tc); oS.append(ap + (a - ap) * u)
        oT.append(t); oS.append(min(a, b))
    return simplificar(oT, oS)


def redondear(T, S):
    T, S = [round(x, REDONDEO) for x in T], [round(x, REDONDEO) for x in S]
    return simplificar(T, S, 0.0)


# ---------- funciones del tiempo constantes por tramos: [(t, v)] = v desde t (v None = tramo inactivo) ----------
def valor_en(esc, t, antes):
    v = antes
    for tk, vk in esc:
        if tk <= t + 1e-9:
            v = vk
        else:
            break
    return v


def escalera(desde_v, hasta_v, t0, dur, final=None):
    """Los escalones de un cambio de velocidad de desde_v a hasta_v que empieza en t0 y dura `dur` → [(t, v)]. `final`:
    lo que queda al terminar (None = el tramo se apaga)."""
    if dur <= 1e-6:
        return [(t0, hasta_v)] + ([(t0 + 1e-3, final)] if final is not False else [])
    out = [(t0 + dur * k / PASOS, desde_v + (hasta_v - desde_v) * (k + 1) / PASOS) for k in range(PASOS)]
    if final is not False:
        out.append((t0 + dur, final))
    return out


class Carril:
    """El campo de velocidades de un carril: la base (m/s en el tiempo) y sus tramos [a, b) con su velocidad en el tiempo."""

    def __init__(self, nombre, largo, v_base):
        self.nombre, self.largo = nombre, largo
        self.base = []                 # [(t, v)]; antes del primero, v0
        self.v0 = v_base
        self.tramos = []               # [{a, b, esc: [(t, v|None)]}]

    def base_en(self, t):
        return valor_en(self.base, t, self.v0)

    def tramo_en(self, z, t):
        return valor_en(z["esc"], t, None)

    def vel(self, s, t):
        """La velocidad en (s, t): la del tramo activo que contiene s (si hay dos, la menor) o la base."""
        vs = [vz for vz in (self.tramo_en(z, t) for z in self.tramos if z["a"] <= s < z["b"]) if vz is not None]
        return min(vs) if vs else self.base_en(t)

    def cambios(self):
        ts = {tk for tk, _ in self.base}
        for z in self.tramos:
            ts |= {tk for tk, _ in z["esc"]}
        return sorted(ts)

    def vmax(self):
        return max([self.v0] + [v for _, v in self.base] + [v for z in self.tramos for _, v in z["esc"] if v is not None])


def libre(car, s0, t0, t1):
    """La trayectoria de UN vehículo solo en el campo de velocidades del carril, de t0 a t1 → (T, S). Por eventos: cambia
    de velocidad al cruzar un borde de tramo o al llegar un cambio de tiempo."""
    cambios = [c for c in car.cambios() if t0 < c < t1]
    T, S, t, s = [t0], [s0], t0, s0
    guarda = 0
    while t < t1 - 1e-9 and guarda < 10000:
        guarda += 1
        v = car.vel(s, t)
        tb = next((c for c in cambios if c > t + 1e-9), t1)
        ts, borde = math.inf, None
        if v > 1e-9:
            for z in car.tramos:
                for e in (z["a"], z["b"]):
                    if e > s + 1e-7:
                        te = t + (e - s) / v
                        if te < ts:
                            ts, borde = te, e
        tn = min(tb, ts, t1)
        s = borde if (tn == ts and borde is not None) else s + v * (tn - t)
        t = tn
        T.append(t); S.append(s)
    return simplificar(T, S)


# ---------- el flujo: vehículos por carril (Newell) ----------
def generar(carriles, tipos_mezcla, medidas, densidad, reaccion, dur, semilla, hash_):
    """Los vehículos de cada carril en t = −T_ANTES (posiciones y tipos), con el hueco mínimo que exige el modelo.
    → [{c, o, var, s0, largo}] por carril (del primero, el de más adelante, al último) y el tope de densidad si no cabe."""
    out, tope = [], math.inf
    nombres = list(tipos_mezcla)
    pesos = [max(0.0, float(tipos_mezcla[k])) for k in nombres]
    tot = sum(pesos) or 1.0
    acum, a = [], 0.0
    for p in pesos:
        a += p / tot; acum.append(a)
    largo_max = max(medidas[k]["largo_m"] for k in nombres)
    for ci, car in enumerate(carriles):
        v = car.vmax()
        dmin = largo_max + HUECO_M + v * reaccion + 1.0
        tope = min(tope, 1000.0 / dmin)
        dmed = 1000.0 / densidad
        lista, s = [], car.largo + hash_(ci, 101) * dmed
        lejos = -(car.vmax() * (dur + T_ANTES + T_DESPUES) + 60.0)
        i = 0
        while s > lejos:
            u = hash_(ci * 7919 + i, semilla)
            k = next(j for j, x in enumerate(acum) if u <= x + 1e-12)
            o = nombres[k]
            lista.append({"c": ci, "o": o, "var": int(hash_(ci * 7919 + i, semilla + 3) * 1000), "s0": s, "largo": medidas[o]["largo_m"]})
            paso = dmin + max(0.0, dmed - dmin) * 2 * hash_(ci * 7919 + i, semilla + 1)
            s -= paso
            i += 1
        out.append(lista)
    return out, tope


def flujo(carriles, vehiculos, reaccion, dur):
    """Newell por carril: cada vehículo = min(libre, el de adelante corrido τ y δ) → la misma lista con T y S."""
    t0, t1 = -T_ANTES, dur + T_DESPUES
    for car, lista in zip(carriles, vehiculos):
        prev = None
        for veh in lista:
            # el libre arranca en t0 desde s0 − v·T_ANTES… s0 es su lugar en t = −T_ANTES (generar lo dejó así)
            L = libre(car, veh["s0"], t0, t1)
            if prev is not None:
                delta = (prev["largo"] + veh["largo"]) / 2 + HUECO_M
                lider = ([x + reaccion for x in prev["T"]], [x - delta for x in prev["S"]])
                L = minimo(L, lider)
            veh["T"], veh["S"] = redondear(*L)
            prev = veh
    return vehiculos


# ---------- caminos (el mismo cálculo que enCadena de motor.js) ----------
def en_cadena(cad, s):
    """(x, y, dx, dy) del punto a s del inicio de la cadena [[x, y, s, salto], …] (s fuera de rango: el extremo)."""
    L = cad[-1][2]
    sc = min(max(s, 0.0), L)
    i = 0
    while i < len(cad) - 2 and sc > cad[i + 1][2]:
        i += 1
    a, b = cad[i], cad[i + 1]
    d = max(1e-9, math.hypot(b[0] - a[0], b[1] - a[1]))
    u = (sc - a[2]) / max(1e-6, b[2] - a[2])
    u = min(1.0, max(0.0, u))
    return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, (b[0] - a[0]) / d, (b[1] - a[1]) / d


def proyectar(cad, x, y):
    """La s del punto de la cadena más cercano a (x, y) y la distancia."""
    mejor = (math.inf, 0.0)
    for a, b in zip(cad, cad[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        h = min(1.0, max(0.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        d = math.hypot(x - a[0] - dx * h, y - a[1] - dy * h)
        if d < mejor[0]:
            mejor = (d, a[2] + (b[2] - a[2]) * h)
    return mejor[1], mejor[0]


def caminos_de(X):
    """Todos los caminos con nombre que hay hasta ahora: los del mundo y los que publican las piezas ya resueltas."""
    out = dict(getattr(X.S, "caminos", {}) or {})
    for p in X.piezas:
        out.update(p.get("_caminos") or {})
    return out


def camino(X, nombre, que):
    C = caminos_de(X)
    if nombre not in C:
        raise X.m3.Falla("M3D2", "%s: «%s» no es un camino con nombre de este mundo (hay: %s)" % (que, nombre, ", ".join(sorted(C)) or "ninguno"))
    return C[nombre]


def posicion_en(X, ref, cad, que):
    """Una POSICIÓN sobre un camino → s (metros, en unidades de la escena): un número (s desde el inicio), «NN%» (fracción
    del largo) o un lugar (id o [x, y]: su proyección sobre el camino)."""
    L = cad[-1][2]
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        return min(max(float(ref) / X.S.unidad_m, 0.0), L)
    if isinstance(ref, str) and ref.strip().endswith("%"):
        try:
            f = float(ref.strip()[:-1]) / 100
        except ValueError:
            raise X.m3.Falla("M3D2", "%s: «%s» no es una fracción (va «40%%»)" % (que, ref))
        return min(max(f, 0.0), 1.0) * L
    l = X.lugar(ref, que)
    return proyectar(cad, l["x"], l["y"])[0]


# ---------- móviles: lo que la cámara y las anotaciones siguen ----------
class Movil:
    """Lo que se mueve de una pieza: n trayectorias (actor: 1; flujo: sus vehículos) sobre sus caminos.
    en(t, n) → (x, y, dx, dy, v, visible) con la trayectoria suavizada (la misma que dibuja motor.js)."""

    def __init__(self, cadenas, tray, h, unidad_m=1.0):
        self.cad, self.tray, self.h, self.u = cadenas, tray, h, unidad_m   # tray: [(i_cadena, T, S, F)]

    def __len__(self):
        return len(self.tray)

    def s_en(self, t, n):
        c, T, S, F = self.tray[n]
        return suave(T, S, F, self.h, t)

    def en(self, t, n=0):
        c, T, S, F = self.tray[n]
        s, v = suave(T, S, F, self.h, t)
        cad = self.cad[c]
        x, y, dx, dy = en_cadena(cad, s)
        return x, y, dx, dy, v, -1e-6 <= s <= cad[-1][2] + 1e-6

    def cerca(self, t, x, y, carriles=None, cuantos=1):
        """Los índices de los `cuantos` vehículos visibles en t más cercanos a (x, y) (en esos carriles)."""
        dist = []
        for n, (c, T, S, F) in enumerate(self.tray):
            if carriles is not None and c not in carriles:
                continue
            px, py, _, _, _, vis = self.en(t, n)
            if vis:
                dist.append((math.hypot(px - x, py - y), n))
        dist.sort()
        return [n for _, n in dist[:cuantos]]


def movil_de(lista_tray, cadenas, h, X):
    return Movil(cadenas, [(c, T, S, integral(T, S)) for c, T, S in lista_tray], h, X.S.unidad_m)


# ---------- referencias a algo que se mueve (cámara que sigue, anotaciones) ----------
CLAVES_ANCLA = ("actor", "flujo", "n", "carril", "cerca", "t", "cuantos", "desfase_m", "lev_m")


def es_ref_movil(ref):
    return isinstance(ref, dict) and ("actor" in ref or "flujo" in ref)


def resolver_ancla(ref, X, que, varias=False):
    """Un ancla del maqueta.json → lista de anclas resueltas: {x, y} (un lugar fijo) o {movil, n, desfase: [adelante, izq]}.
    Formas: un lugar (id o [x, y]); {actor: id}; {flujo: id, n: k}; {flujo: id, carril: «carril-1», cerca: lugar, t: s,
    cuantos: k} (los k vehículos de ese carril —o de todos— más cercanos a ese lugar en ese segundo). `desfase_m`: metros
    por delante del móvil (o [adelante, a su izquierda]); `lev_m`: metros sobre el suelo."""
    if not es_ref_movil(ref):
        l = X.lugar(ref, que)
        return [{"x": l["x"], "y": l["y"]}]
    if not isinstance(ref, dict):
        raise X.m3.Falla("M3D2", "%s: un ancla es un lugar o {actor: id} / {flujo: id, …}" % que)
    extra = [k for k in ref if k not in CLAVES_ANCLA]
    if extra:
        raise X.m3.Falla("M3D2", "%s: el ancla lleva claves desconocidas %s (van: %s)" % (que, ", ".join(extra), ", ".join(CLAVES_ANCLA)))
    pid = ref.get("actor") or ref.get("flujo")
    tipo = "actor" if "actor" in ref else "flujo"
    pz = X.por_id.get(pid)
    if not pz or pz["tipo"] != tipo:
        raise X.m3.Falla("M3D2", "%s: «%s» no es el id de una pieza %s (hay: %s)" % (que, pid, tipo, ", ".join(p["id"] for p in X.piezas if p["tipo"] == tipo) or "ninguna"))
    M = X.moviles[pid]
    d = ref.get("desfase_m", 0)
    d = [float(d), 0.0] if isinstance(d, (int, float)) else [float(d[0]), float(d[1])]
    d = [v / X.S.unidad_m for v in d]
    lev = float(ref.get("lev_m", 0)) / X.S.unidad_m
    if tipo == "actor":
        ns = [0]
    elif "n" in ref:
        n = ref["n"]
        if not (isinstance(n, int) and 0 <= n < len(M)):
            raise X.m3.Falla("M3D2", "%s: `n` %r no es un vehículo del flujo «%s» (0–%d)" % (que, n, pid, len(M) - 1))
        ns = [n]
    else:
        if ref.get("cerca") is None or ref.get("t") is None:
            raise X.m3.Falla("M3D2", "%s: un vehículo del flujo «%s» se elige con `n` o con `cerca` (un lugar) y `t` (el segundo)" % (que, pid))
        cs = None
        if ref.get("carril") is not None:
            car = ref["carril"]
            nombres = pz["carriles"]
            if isinstance(car, int) and 1 <= car <= len(nombres):
                cs = [car - 1]
            elif car in nombres:
                cs = [nombres.index(car)]
            else:
                raise X.m3.Falla("M3D2", "%s: `carril` «%s» no es un carril del flujo «%s» (%s, o su número 1–%d)" % (que, car, pid, ", ".join(nombres), len(nombres)))
        l = X.lugar(ref["cerca"], que)
        k = int(ref.get("cuantos", 1))
        if not varias and k != 1:
            raise X.m3.Falla("M3D2", "%s: aquí va UN vehículo (sin `cuantos`)" % que)
        ns = M.cerca(float(ref["t"]), l["x"], l["y"], cs, k)
        if not ns:
            raise X.m3.Falla("M3D2", "%s: no hay ningún vehículo del flujo «%s» en pantalla en t = %g" % (que, pid, float(ref["t"])))
    return [{"movil": pid, "n": n, "desfase": [round(d[0], 3), round(d[1], 3)], "lev": round(lev, 3)} for n in ns]


def ancla_en(A, t, moviles):
    """(x, y, dx, dy, visible) de un ancla resuelta en t."""
    if "movil" not in A:
        return A["x"], A["y"], 1.0, 0.0, True
    x, y, dx, dy, v, vis = moviles[A["movil"]].en(t, A["n"])
    a, l = A.get("desfase") or [0.0, 0.0]
    return x + dx * a - dy * l, y + dy * a + dx * l, dx, dy, vis
