"""Mundo «ciudad»: un lugar REAL de pocos km de un set de escala ciudad (design/sets3d/<set>/, scripts/build_set3d.py),
en METROS: x = (lon − lon0)·m_lon (este), y = (lat − lat0)·m_lat (norte), con lon0, lat0, m_lon, m_lat de relieve.json →
proyeccion. El suelo es el relieve a zoom alto con su punto más bajo en 0 (relieve.json → base_m), exagerado
`exageracion` veces. Las capas que dibujan las piezas (calles, edificios, agua, zonas) se leen al pedirlas (`capa`)."""
import json
import os


class Ciudad:
    escala, unidad_m, km = "ciudad", 1.0, 0.001
    como_lugar = "decláralo con lon y lat, o usa [lon, lat]"

    def __init__(self, m3, sid, exag=1.5):
        self.m3, self.id, self.dir, self.exag = m3, sid, os.path.join(m3.SETS, sid), float(exag)
        self.relieve = m3.cargar_json(os.path.join(self.dir, "relieve.json"))
        self.fuente = m3.cargar_json(os.path.join(self.dir, "fuente.json"))
        self.lugares = m3.cargar_json(os.path.join(self.dir, "lugares.json"))["lugares"]
        R, P, c = self.relieve, self.relieve["proyeccion"], self.relieve["caja"]
        self.P, self.caja_geo, self.base_m = P, c, float(R["base_m"])
        self.x0, self.x1 = (c["lon_min"] - P["lon0"]) * P["m_lon"], (c["lon_max"] - P["lon0"]) * P["m_lon"]
        self.y0, self.y1 = (c["lat_min"] - P["lat0"]) * P["m_lat"], (c["lat_max"] - P["lat0"]) * P["m_lat"]
        self.cx, self.cy = (self.x1 - self.x0) / R["ancho"], (self.y1 - self.y0) / R["alto"]
        self.caminos, self._filas, self._capas = {}, None, {}

    def xy(self, lon, lat):
        return (lon - self.P["lon0"]) * self.P["m_lon"], (lat - self.P["lat0"]) * self.P["m_lat"]

    punto = xy

    def lugar_xy(self, l):
        return self.xy(l["lon"], l["lat"])

    @property
    def caja(self):
        return (self.x0, self.y0, self.x1, self.y1)

    def dentro(self, x, y, margen=0.0):
        return self.x0 + margen <= x <= self.x1 - margen and self.y0 + margen <= y <= self.y1 - margen

    def metros(self, x, y):
        """Altura real (m sobre el mar) con la misma interpolación bilineal que mundos/ciudad.js."""
        if self._filas is None:
            self._filas = self.m3.SET3D.png_leer(os.path.join(self.dir, self.relieve["archivo"]))[2]
        R, d = self.relieve, self.relieve["desfase_m"]
        fi = min(max((x - self.x0) / self.cx - 0.5, 0), R["ancho"] - 1.001)
        fj = min(max((self.y1 - y) / self.cy - 0.5, 0), R["alto"] - 1.001)
        i, j = int(fi), int(fj)
        u, v = fi - i, fj - j
        a, b = self._filas[j], self._filas[j + 1]
        h = lambda f, k: f[3 * k] * 256 + f[3 * k + 1] - d
        return (h(a, i) * (1 - u) + h(a, i + 1) * u) * (1 - v) + (h(b, i) * (1 - u) + h(b, i + 1) * u) * v

    def suelo(self, x, y):
        """La altura de la maqueta (m, ya exagerada): el punto más bajo de la caja es 0."""
        return max(0.0, self.metros(x, y) - self.base_m) * self.exag

    def capa(self, nombre):
        if nombre not in self._capas:
            self._capas[nombre] = self.m3.cargar_json(os.path.join(self.dir, nombre + ".json"))
        return self._capas[nombre]

    def archivos(self):
        return [(os.path.join(self.dir, self.relieve["archivo"]), self.relieve["archivo"])]

    def datos_R(self):
        return {}

    def datos_mundo(self):
        return {"relieve": {k: self.relieve[k] for k in ("archivo", "ancho", "alto", "caja", "desfase_m", "proyeccion", "muestras", "min_m", "max_m", "base_m")},
                "exageracion": self.exag}


def mundo(o, f, m3):
    return Ciudad(m3, m3.set_de(o, "ciudad"), o.get("exageracion", 1.5))
