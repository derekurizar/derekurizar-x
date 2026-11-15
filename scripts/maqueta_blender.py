#!/usr/bin/env python3
"""Motor Blender de la maqueta 3D (/video-3d): la PLACA (el mundo sin texto) de los estilos `arquitecto`, `diorama` y `papel`.

Corre DENTRO de Blender sin ventana; lo lanza scripts/maqueta3d.py (cuadro, render, pieza), que después pone encima la
capa 2D de HyperFrames (video/maqueta/capa.js en modo placa). A mano:

  Blender -b --factory-startup --python scripts/maqueta_blender.py -- \\
      --maqueta MAQUETA.json --formato 9:16|4:5|ANCHOxALTO --salida DIR (--cuadros 0,45,90 | --todo [--desde N] [--hasta N])

Sale DIR/c_NNNNN.png (el cuadro N está en t = N / fps). Contrato: referencias/diseno/maqueta3d.md («Motor Blender»).

La geometría NO se duplica: este script importa de maqueta3d.py la resolución del maqueta.json (lugares → km, cadenas
de falla, cámara con su altura, colores del estilo y de la paleta), la función de cámara (`camara_en`, `ojo_de`) y la
proyección (`proyector`, con la que comprueba que la cámara de Blender cae en el mismo píxel). Aquí solo se DIBUJA:

  1) relieve: el PNG del set → malla (numpy), con una forma por estilo (`blender.relieve` en design/sets3d/estilos.json):
     liso (arquitecto: maqueta blanca, el mar un escalón abajo) · base (diorama: el país recortado en una base con canto
     sobre un fondo de estudio, foco corto) · capas (papel: curvas de nivel recortadas en cartulina)
  2) piezas: falla (tubo o cinta posado en el terreno), frontera, ruta (rayas), luces (bloques por pueblo)
  3) cuadro: `mundo_en(t)` pone la cámara del contrato y el estado de cada evento (ruptura, onda, deslizar, encender,
     apagar, parpadear, resaltar) como función pura de t: sin curvas de animación, sin reloj y sin azar

Salida: 0 ok · 1 fallo · 2 uso incorrecto. Python stdlib + bpy y numpy (los de Blender ≥ 5.0).
"""
import argparse, math, os, sys, time, warnings

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import maqueta3d as M3D  # noqa: E402

M32 = 0xFFFFFFFF


def leer_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(prog="maqueta_blender.py", description="Placa 3D de la maqueta en Blender (estilos arquitecto, diorama y papel).",
                                 epilog="Corre dentro de Blender: Blender -b --factory-startup --python scripts/maqueta_blender.py -- …  "
                                        "Lo normal es no llamarlo a mano: python3 scripts/maqueta3d.py cuadro|render|pieza lo lanza y pone la capa 2D.")
    ap.add_argument("--maqueta", required=True, help="el maqueta.json (referencias/diseno/maqueta3d.md)")
    ap.add_argument("--formato", required=True, help="9:16, 4:5 o ANCHOxALTO (modo pieza)")
    ap.add_argument("--salida", required=True, help="carpeta donde quedan los PNG (c_NNNNN.png)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cuadros", help="cuadros sueltos, separados por coma (el cuadro N está en t = N / fps)")
    g.add_argument("--todo", action="store_true", help="todos los cuadros (o el tramo --desde … --hasta)")
    ap.add_argument("--desde", type=int, default=0, help="primer cuadro con --todo (por defecto 0)")
    ap.add_argument("--hasta", type=int, help="último cuadro con --todo, sin incluirlo (por defecto, el final)")
    ap.add_argument("--muestras", type=int, help="muestras del render (por defecto, las del estilo)")
    ap.add_argument("--escala", type=int, default=100, help="porcentaje de la resolución (solo para probar; por defecto 100)")
    ap.add_argument("--blend", help="guarda la escena en este .blend (para abrirla y mirar)")
    return ap.parse_args(argv)


def lin(hexa):
    """«#RRGGBB» (sRGB) → (r, g, b, 1) lineal."""
    h = hexa.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))


def suave(a, b, x):
    u = clamp((x - a) / (b - a)) if b != a else (1.0 if x >= b else 0.0)
    return u * u * (3 - 2 * u)


def azar(i, k=0):
    """El mismo ruido fijo por índice que video/maqueta/motor.js (`hash`): sin `random`."""
    h = ((((i + 0x9e3779b9) & M32) * 0x85ebca6b) & M32) ^ ((((k + 0x7f4a7c15) & M32) * 0xc2b2ae35) & M32)
    h ^= h >> 15
    h = (h * 0x2c1b3c6d) & M32
    h ^= h >> 12
    return h / 4294967296


def main():
    A = leer_args()
    try:
        import bpy, bmesh
        import numpy as np
        from mathutils import Vector
        from bpy_extras.object_utils import world_to_camera_view
    except ImportError:
        print("maqueta_blender.py corre dentro de Blender (≥ 5.0). Usa: python3 scripts/maqueta3d.py cuadro|render|pieza MAQUETA …, que lo lanza con Blender -b", file=sys.stderr)
        return 2
    warnings.filterwarnings("ignore", category=DeprecationWarning)   # `use_nodes` (Blender 5.x lo anuncia para 6.0)
    T0 = time.time()
    try:
        m = M3D.cargar_json(A.maqueta)
        R = M3D.resolver(m, A.formato)
    except M3D.Falla as e:
        print("FALLA %s %s" % e.args)
        return 1
    except (OSError, ValueError) as e:
        print("FALLA no se pudo leer %s: %s" % (A.maqueta, e))
        return 2
    if R.get("motor") != "blender":
        print("FALLA el estilo «%s» no es de motor blender (lo dibuja video/maqueta/motor.js)" % R["estilo"])
        return 2
    S, Z, COL, CFG, BL = R["_set"], R["zona"], R["col"], R["estilo_cfg"], R["blender"]
    W, H, FPS, DUR, EXAG = Z["W"], Z["H"], R["fps"], R["dur"], R["exageracion"]
    N = int(round(DUR * FPS))
    FORMA = BL["relieve"]                       # liso | base | capas
    CYCLES = BL["motor"].upper() == "CYCLES"
    MUESTRAS = A.muestras or BL["muestras"]
    if A.todo:
        cuadros = list(range(max(0, A.desde), min(N, A.hasta if A.hasta is not None else N)))
        if not cuadros:
            print("--desde/--hasta: no queda ningún cuadro (el video tiene %d)" % N, file=sys.stderr)
            return 2
    else:
        try:
            cuadros = sorted(set(int(c) for c in A.cuadros.split(",")))
        except ValueError:
            print("--cuadros: enteros separados por coma", file=sys.stderr)
            return 2
        if any(not 0 <= c <= N for c in cuadros):
            print("--cuadros fuera del video (0–%d)" % N, file=sys.stderr)
            return 2

    bpy.ops.wm.read_factory_settings(use_empty=True)
    SC = bpy.context.scene

    # ------------------------------------------------------------------ materiales
    def material(nombre, hexa, emision=0.0, difuso=1.0, rugosidad=1.0, especular=0.0):
        """Color plano mate. `emision` > 0: parte del color sale como luz propia (se lee igual a la sombra)."""
        mt = bpy.data.materials.new(nombre)
        mt.use_nodes = True
        b = mt.node_tree.nodes.get("Principled BSDF")
        c = lin(hexa)
        b.inputs["Base Color"].default_value = tuple(v * difuso for v in c[:3]) + (1.0,)
        b.inputs["Roughness"].default_value = rugosidad
        b.inputs["Specular IOR Level"].default_value = especular
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = emision
        return mt

    def objeto(nombre, me, mat=None, sombra=True):
        if mat is not None:
            me.materials.append(mat)
        ob = bpy.data.objects.new(nombre, me)
        SC.collection.objects.link(ob)
        ob.visible_shadow = sombra
        return ob

    def malla_caras(nombre, verts, caras):
        me = bpy.data.meshes.new(nombre)
        me.from_pydata([tuple(v) for v in verts], [], [tuple(c) for c in caras])
        me.update()
        return me

    # ------------------------------------------------------------------ relieve: PNG del set → alturas (numpy)
    S.metros(0.0, 0.0)                                           # carga las filas del PNG
    RW, RH = S.relieve["ancho"], S.relieve["alto"]
    crudo = np.frombuffer(b"".join(S._filas), dtype=np.uint8).reshape(RH, RW, 3)
    ALT = crudo[..., 0].astype(np.float32) * 256 + crudo[..., 1] - S.relieve["desfase_m"]    # metros reales; fila 0 = norte
    XS = S.x0 + (np.arange(RW) + 0.5) * S.cx                     # km (este) del centro de cada celda
    YS = S.y1 - (np.arange(RH) + 0.5) * S.cy                     # km (norte); decrece con la fila

    def desenfocar(G, sigma):
        if sigma <= 0:
            return G
        r = max(1, int(math.ceil(3 * sigma)))
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
        k /= k.sum()
        for eje in (0, 1):
            P = np.pad(G, [(r, r) if e == eje else (0, 0) for e in (0, 1)], mode="edge")
            G = sum(k[d] * (P[d:d + G.shape[0], :] if eje == 0 else P[:, d:d + G.shape[1]]) for d in range(2 * r + 1))
        return G.astype(np.float32)

    def mascara_pais():
        """1 dentro del país (el borde del set relleno), a la resolución del relieve, con el filo suavizado."""
        Mk = np.zeros((RH, RW), np.float32)
        for an in R["frontera"]:
            q = np.asarray(an, dtype=np.float64)
            px, py = (q[:, 0] - S.x0) / S.cx - 0.5, (S.y1 - q[:, 1]) / S.cy - 0.5
            x2, y2 = np.roll(px, -1), np.roll(py, -1)
            for j in range(max(0, int(py.min())), min(RH, int(py.max()) + 2)):
                c = (py <= j) != (y2 <= j)
                if not c.any():
                    continue
                xs = np.sort(px[c] + (j - py[c]) * (x2[c] - px[c]) / (y2[c] - py[c]))
                for a, b in zip(xs[::2], xs[1::2]):
                    i0, i1 = max(0, int(math.ceil(a))), min(RW, int(math.floor(b)) + 1)
                    if i1 > i0:
                        Mk[j, i0:i1] = 1 - Mk[j, i0:i1]
        return desenfocar(Mk, 0.8)
    PAIS = mascara_pais()
    TIERRA = (ALT > 0).astype(np.float32)

    class Rejilla:
        """Un campo sobre un recorte de la rejilla del relieve (cada `paso` celdas): la superficie que de verdad se ve."""
        def __init__(self, G, i0=0, j0=0, paso=1):
            self.G, self.paso = np.ascontiguousarray(G, dtype=np.float32), paso
            self.ny, self.nx = self.G.shape
            self.x = XS[i0:i0 + self.nx * paso:paso]
            self.y = YS[j0:j0 + self.ny * paso:paso]
            self.dx, self.dy = S.cx * paso, S.cy * paso

        def en(self, x, y):
            """Bilineal en (x, y) km (vale con arreglos)."""
            fi = np.clip((np.asarray(x, dtype=np.float64) - self.x[0]) / self.dx, 0, self.nx - 1.001)
            fj = np.clip((self.y[0] - np.asarray(y, dtype=np.float64)) / self.dy, 0, self.ny - 1.001)
            i, j = fi.astype(int), fj.astype(int)
            u, v = fi - i, fj - j
            G = self.G
            return (G[j, i] * (1 - u) + G[j, i + 1] * u) * (1 - v) + (G[j + 1, i] * (1 - u) + G[j + 1, i + 1] * u) * v

    def mezcla(a, b, f):
        """Mezcla dos colores lineales (tuplas) con un campo f → arreglo (…, 3)."""
        a, b = np.asarray(a[:3], np.float32), np.asarray(b[:3], np.float32)
        return a + (b - a) * f[..., None]

    PASO = int(BL.get("paso", 2))
    i0 = j0 = 0
    i1, j1 = RW, RH
    ALTV = ALT
    if FORMA == "capas":
        # papel: el relieve suavizado (el recorte a mano redondea) y partido en niveles; cada nivel es una cartulina
        ALTV = desenfocar(ALT, float(BL.get("redondeo", 1.4)))
        d_t, d_m, n_mar = float(BL["capa_m"]), float(BL["capa_mar_m"]), int(BL["capas_mar"])
        U = np.where(ALTV > 0, ALTV / d_t, np.maximum(ALTV / d_m, -(n_mar - 0.001))).astype(np.float32)   # «coordenada de nivel»
        gy, gx = np.gradient(U)
        ancho = np.clip(0.5 * float(BL.get("canto_celdas", 2.0)) * np.hypot(gx, gy) * PASO, 0.03, 0.5)   # el canto ocupa ≈ 2 celdas de malla: curva limpia
        q = U - np.round(U)
        dz = d_t / 1000.0 * EXAG                                             # grosor de una cartulina (km de maqueta)
        ZV = (dz * (np.round(U) - 0.5 + np.clip(q / (2 * ancho) + 0.5, 0, 1))).astype(np.float32)   # la meseta del nivel k queda a (k + 0.5)·dz
        NIVEL = np.floor(U)
        z_base = float(dz * (-n_mar + 0.5))
    else:
        ZV = (np.maximum(ALT, 0) / 1000.0 * EXAG).astype(np.float32)
        esc = float(BL.get("escalon_mar_km", 0.0))
        if esc:                                                              # el mar, un escalón por debajo de la costa
            ZV = np.where(ALT > 0, ZV, -esc).astype(np.float32)
        z_base = -esc
        if FORMA == "base":
            c, mg = S.fuente["caja"], float(BL.get("base_margen_km", 30))
            bx0, by0 = S.xy(c["lon_min"], c["lat_min"])
            bx1, by1 = S.xy(c["lon_max"], c["lat_max"])
            i0 = max(0, int((bx0 - mg - S.x0) / S.cx)); i1 = min(RW, int((bx1 + mg - S.x0) / S.cx) + 1)
            j0 = max(0, int((S.y1 - by1 - mg) / S.cy)); j1 = min(RH, int((S.y1 - by0 + mg) / S.cy) + 1)
            z_base = -float(BL["base_grosor_km"])
    SUP = Rejilla(ZV[j0:j1:PASO, i0:i1:PASO], i0, j0, PASO)                  # la superficie visible: en ella se posan las piezas

    def sup(x, y, lev=0.0):
        return float(SUP.en(x, y)) + lev

    # ------------------------------------------------------------------ el color del relieve: una textura por estilo
    hN = np.clip(ALTV / float(S.relieve["max_m"]), 0, 1)
    hondo = np.clip(-ALT / 6000.0, 0, 1)
    sm = lambda a, b, x: (lambda u: u * u * (3 - 2 * u))(np.clip((x - a) / (b - a), 0, 1))
    if FORMA == "capas":
        kmax = max(1, int(float(S.relieve["max_m"]) / d_t))
        tk = np.clip(NIVEL / kmax, 0, 1)
        tierra_c = np.where((tk > 0.42)[..., None], mezcla(lin(COL["tierra_media"]), lin(COL["tierra_alta"]), np.clip((tk - 0.42) / 0.58, 0, 1)),
                            mezcla(lin(COL["tierra_baja"]), lin(COL["tierra_media"]), np.clip(tk / 0.42, 0, 1)))
        mar_c = mezcla(lin(COL["mar"]), lin(COL["mar_hondo"]), np.clip((-NIVEL - 1) / max(1, n_mar - 1), 0, 1))
        es_tierra = (NIVEL >= 0).astype(np.float32)
    else:
        tierra_c = mezcla(lin(COL["tierra_baja"]), lin(COL["tierra_media"]), sm(0.0, 0.38, hN))
        tierra_c = tierra_c + (np.asarray(lin(COL["tierra_alta"])[:3], np.float32) - tierra_c) * sm(0.38, 1.0, hN)[..., None]
        mar_c = mezcla(lin(COL["mar"]), lin(COL["mar_hondo"]), sm(0.0, 0.62, hondo))
        es_tierra = TIERRA
    fuera = (1 - PAIS) * (1 - float(CFG.get("fuera", 0.5)))                  # cuánto se va la tierra de fuera del país hacia `fuera`
    tierra_c = tierra_c + (np.asarray(lin(COL["fuera"])[:3], np.float32) - tierra_c) * fuera[..., None]
    TEX = np.empty((RH, RW, 4), np.float32)
    TEX[..., :3] = mar_c + (tierra_c - mar_c) * es_tierra[..., None]
    if FORMA != "base" and float(CFG.get("borde_km", 0)) > 0:    # la orilla de la caja se funde con la mesa (el diorama se corta: no)
        orilla = np.minimum(np.minimum(XS - S.x0, S.x1 - XS)[None, :], np.minimum(YS - S.y0, S.y1 - YS)[:, None])
        mesa3 = np.asarray(lin(COL["mesa"])[:3], np.float32)
        TEX[..., :3] = mesa3 + (TEX[..., :3] - mesa3) * sm(0.0, float(CFG["borde_km"]), orilla)[..., None]
    TEX[..., 3] = es_tierra
    img = bpy.data.images.new("relieve_color", RW, RH, alpha=True, float_buffer=True, is_data=True)
    img.alpha_mode = "CHANNEL_PACKED"
    img.pixels.foreach_set(TEX[::-1].ravel())                                # la fila 0 de Blender es la de abajo (sur)
    img.pack()

    # distancia (km) de cada punto del relieve a una cadena de falla: para las ondas que salen «de todo el trazo»
    def textura_distancia(nombre, cad):
        gx, gy = XS[::2][None, :], YS[::2][:, None]
        D = np.full((gy.shape[0], gx.shape[1]), 1e9, np.float32)
        for a, b in zip(cad, cad[1:]):
            if a[3]:
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            h = np.clip(((gx - a[0]) * dx + (gy - a[1]) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
            D = np.minimum(D, np.hypot(gx - a[0] - dx * h, gy - a[1] - dy * h).astype(np.float32))
        im = bpy.data.images.new(nombre, D.shape[1], D.shape[0], alpha=False, float_buffer=True, is_data=True)
        px = np.empty(D.shape + (4,), np.float32)
        px[..., 0] = px[..., 1] = px[..., 2] = D[::-1]
        px[..., 3] = 1
        im.pixels.foreach_set(px.ravel())
        im.pack()
        return im

    # ------------------------------------------------------------------ eventos (como si los de la portada ya llevaran su avance)
    EV = [dict(e) for e in R["eventos"]]
    for e in EV:
        if e.get("adelanto"):
            e["t"] -= e["adelanto"]; e["dur"] += e["adelanto"]
    PIEZAS = R["piezas"]
    POR_ID = {p["id"]: p for p in PIEZAS}
    FALLAS = [p for p in PIEZAS if p["tipo"] == "falla"]
    ONDAS = [e for e in EV if e["tipo"] == "onda"]

    # ------------------------------------------------------------------ material del relieve
    mr = bpy.data.materials.new("relieve")
    mr.use_nodes = True
    nt = mr.node_tree
    nn, une = nt.nodes, nt.links.new
    bsdf = nn.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0

    def mate(op, a, b=None, c=None):
        n = nn.new("ShaderNodeMath")
        n.operation = op
        for k, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = v
            else:
                une(v, n.inputs[k])
        return n.outputs[0]

    def mezclar(f, a, b):
        """Nodo Mix de color: a → b con el factor f (enchufes por índice: 0 factor, 6 A, 7 B; salida 2)."""
        n = nn.new("ShaderNodeMix")
        n.data_type = "RGBA"
        for k, v in ((0, f), (6, a), (7, b)):
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = v
            elif isinstance(v, tuple):
                n.inputs[k].default_value = v
            else:
                une(v, n.inputs[k])
        return n.outputs[2]

    def valor(v=0.0):
        n = nn.new("ShaderNodeValue")
        n.outputs[0].default_value = v
        return n

    tc = nn.new("ShaderNodeTexCoord")

    def mapeo():
        mp = nn.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / (S.x1 - S.x0), 1 / (S.y1 - S.y0), 1)
        mp.inputs["Location"].default_value = (-S.x0 / (S.x1 - S.x0), -S.y0 / (S.y1 - S.y0), 0)
        une(tc.outputs["Object"], mp.inputs["Vector"])
        return mp.outputs["Vector"]

    def textura(im, cubica=False):
        t = nn.new("ShaderNodeTexImage")
        t.image, t.extension = im, "EXTEND"
        t.interpolation = "Cubic" if cubica else "Linear"
        une(mapeo(), t.inputs["Vector"])
        return t
    tex = textura(img)
    color = tex.outputs["Color"]
    if FORMA == "capas":
        # cartulina: grano fino que mueve el valor, canto claro en el corte de cada capa y sombra de contacto (oclusión)
        geo = nn.new("ShaderNodeNewGeometry")
        sx = nn.new("ShaderNodeSeparateXYZ")
        une(geo.outputs["True Normal"], sx.inputs[0])
        rg = nn.new("ShaderNodeMapRange")                         # 1 en el corte (la cara casi vertical), 0 en la meseta
        rg.interpolation_type = "SMOOTHSTEP"
        rg.inputs["From Min"].default_value, rg.inputs["From Max"].default_value = float(BL.get("canto_desde", 0.55)), float(BL.get("canto_hasta", 0.93))
        rg.inputs["To Min"].default_value, rg.inputs["To Max"].default_value = 1.0, 0.0
        une(sx.outputs["Z"], rg.inputs["Value"])
        f_canto = rg.outputs["Result"]
        gr = nn.new("ShaderNodeTexNoise")
        gr.inputs["Scale"].default_value = float(BL.get("grano_escala", 0.9))
        gr.inputs["Detail"].default_value = 4.0
        gr.inputs["Roughness"].default_value = 0.75
        une(tc.outputs["Object"], gr.inputs["Vector"])
        g = float(BL.get("grano", 0.1))
        v = mate("MULTIPLY_ADD", gr.outputs[0], g, 1 - g * 0.5)
        if float(BL.get("oclusion", 0)) > 0:
            ao = nn.new("ShaderNodeAmbientOcclusion")
            ao.samples = 8
            ao.inputs["Distance"].default_value = float(BL.get("oclusion_km", 8))
            v = mate("MULTIPLY", v, mate("POWER", ao.outputs["AO"], float(BL["oclusion"])))
        esc_c = nn.new("ShaderNodeVectorMath")
        esc_c.operation = "SCALE"
        une(color, esc_c.inputs[0]); une(v, esc_c.inputs["Scale"])
        color = mezclar(f_canto, esc_c.outputs["Vector"], lin(COL["canto"]))
        bsdf.inputs["Emission Color"].default_value = lin(COL["canto"])
        une(mate("MULTIPLY", f_canto, float(BL.get("canto_emision", 0.3))), bsdf.inputs["Emission Strength"])
    if FORMA == "base":                                           # diorama: el mar es resina (brilla un poco), la tierra mate
        une(mate("MULTIPLY_ADD", tex.outputs["Alpha"], 1.0 - float(BL.get("mar_rugosidad", 0.3)), float(BL.get("mar_rugosidad", 0.3))), bsdf.inputs["Roughness"])
        bsdf.inputs["Specular IOR Level"].default_value = float(BL.get("especular", 0.3))
    # ondas: un anillo pintado que crece (radio y fuerza los pone mundo_en en cada cuadro)
    geo_p = nn.new("ShaderNodeNewGeometry")
    plano = nn.new("ShaderNodeVectorMath")
    plano.operation = "MULTIPLY"
    plano.inputs[1].default_value = (1, 1, 0)
    une(geo_p.outputs["Position"], plano.inputs[0])
    tex_dist, suma = {}, None
    for e in ONDAS:
        if e.get("pieza"):
            if e["pieza"] not in tex_dist:
                tex_dist[e["pieza"]] = textura(textura_distancia("dist_" + e["pieza"], POR_ID[e["pieza"]]["cadena"]), cubica=True).outputs["Color"]
            d = tex_dist[e["pieza"]]
        else:
            dn = nn.new("ShaderNodeVectorMath")
            dn.operation = "DISTANCE"
            dn.inputs[1].default_value = (e["x"], e["y"], 0)
            une(plano.outputs["Vector"], dn.inputs[0])
            d = dn.outputs["Value"]
        e["_r"], e["_w"], e["_k"] = valor(0), valor(1), valor(0)
        g = mate("DIVIDE", mate("SUBTRACT", d, e["_r"].outputs[0]), e["_w"].outputs[0])
        anillo = mate("MULTIPLY", mate("EXPONENT", mate("MULTIPLY", mate("MULTIPLY", g, g), -1.0)), e["_k"].outputs[0])
        suma = anillo if suma is None else mate("MAXIMUM", suma, anillo)
    if suma is not None:
        color = mezclar(mate("MINIMUM", suma, 0.92), color, lin(COL["onda"]))
    une(color, bsdf.inputs["Base Color"])

    # ------------------------------------------------------------------ la malla del relieve (numpy → foreach_set)
    def malla_rejilla(nombre, G):
        nx, ny = G.nx, G.ny
        co = np.empty((ny, nx, 3), np.float32)
        co[..., 0], co[..., 1], co[..., 2] = G.x[None, :], G.y[:, None], G.G
        idx = np.arange(nx * ny, dtype=np.int32).reshape(ny, nx)
        q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], axis=-1).reshape(-1)   # NO → SO → SE → NE: normal hacia arriba
        nq = (nx - 1) * (ny - 1)
        me = bpy.data.meshes.new(nombre)
        me.vertices.add(nx * ny); me.loops.add(nq * 4); me.polygons.add(nq)
        me.vertices.foreach_set("co", co.ravel())
        me.polygons.foreach_set("loop_start", np.arange(0, nq * 4, 4, dtype=np.int32))
        try:
            me.polygons.foreach_set("loop_total", np.full(nq, 4, dtype=np.int32))
        except Exception:
            pass
        me.loops.foreach_set("vertex_index", q)
        me.update(calc_edges=True)
        try:
            me.shade_smooth()
        except Exception:
            me.polygons.foreach_set("use_smooth", np.ones(nq, dtype=bool))
        return me

    objeto("relieve", malla_rejilla("relieve", SUP), mr)

    def faldon(G, zb, mat):
        """Las cuatro paredes del borde de la malla, hasta zb: el canto de la maqueta."""
        orillas = [[(G.x[i], G.y[0], G.G[0, i]) for i in range(G.nx)], [(G.x[-1], G.y[j], G.G[j, -1]) for j in range(G.ny)],
                   [(G.x[i], G.y[-1], G.G[-1, i]) for i in range(G.nx - 1, -1, -1)], [(G.x[0], G.y[j], G.G[j, 0]) for j in range(G.ny - 1, -1, -1)]]
        V, C = [], []
        for o in orillas:
            b = len(V)
            for (x, y, z) in o:
                V.append((x, y, float(z))); V.append((x, y, zb))
            for k in range(len(o) - 1):
                C.append((b + 2 * k, b + 2 * k + 2, b + 2 * k + 3, b + 2 * k + 1))
        return objeto("canto", malla_caras("canto", V, C), mat)

    def marco(x0, y0, x1, y1, z, mat, lejos=20000.0, nombre="mesa"):
        """Un plano enorme con el hueco de la maqueta: la mesa (o el piso del estudio) llega a los bordes del cuadro."""
        V = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), (-lejos, -lejos, z), (lejos, -lejos, z), (lejos, lejos, z), (-lejos, lejos, z)]
        return objeto(nombre, malla_caras(nombre, V, [(4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)]), mat)

    ex0, ey0, ex1, ey1 = float(SUP.x[0]), float(SUP.y[-1]), float(SUP.x[-1]), float(SUP.y[0])
    if FORMA == "base":
        # el canto de la base en estratos (por altura) y el piso del estudio, más claro cerca de la base
        mc = bpy.data.materials.new("canto")
        mc.use_nodes = True
        n2, u2 = mc.node_tree.nodes, mc.node_tree.links.new
        b2 = n2.get("Principled BSDF")
        b2.inputs["Roughness"].default_value = 1.0
        b2.inputs["Specular IOR Level"].default_value = 0.0
        g2, s2, rp = n2.new("ShaderNodeNewGeometry"), n2.new("ShaderNodeSeparateXYZ"), n2.new("ShaderNodeValToRGB")
        mr2 = n2.new("ShaderNodeMapRange")
        mr2.inputs["From Min"].default_value, mr2.inputs["From Max"].default_value = z_base, 0.0
        u2(g2.outputs["Position"], s2.inputs[0]); u2(s2.outputs["Z"], mr2.inputs["Value"]); u2(mr2.outputs["Result"], rp.inputs["Fac"])
        rp.color_ramp.interpolation = "CONSTANT"
        est = [COL["canto_zocalo"], COL["canto_bajo"], COL["canto"]]
        rp.color_ramp.elements[0].position, rp.color_ramp.elements[0].color = 0.0, lin(est[0])
        rp.color_ramp.elements[1].position, rp.color_ramp.elements[1].color = 0.22, lin(est[1])
        e3 = rp.color_ramp.elements.new(0.62)
        e3.color = lin(est[2])
        u2(rp.outputs["Color"], b2.inputs["Base Color"])
        faldon(SUP, z_base, mc)
        objeto("fondo_base", malla_caras("fondo_base", [(ex0, ey0, z_base), (ex1, ey0, z_base), (ex1, ey1, z_base), (ex0, ey1, z_base)], [(0, 3, 2, 1)]), mc)
        mp = bpy.data.materials.new("estudio")
        mp.use_nodes = True
        n3, u3 = mp.node_tree.nodes, mp.node_tree.links.new
        b3 = n3.get("Principled BSDF")
        b3.inputs["Roughness"].default_value = 1.0
        b3.inputs["Specular IOR Level"].default_value = 0.0
        g3, d3, m3, x3 = n3.new("ShaderNodeNewGeometry"), n3.new("ShaderNodeVectorMath"), n3.new("ShaderNodeMapRange"), n3.new("ShaderNodeMix")
        d3.operation = "DISTANCE"
        d3.inputs[1].default_value = ((ex0 + ex1) / 2, (ey0 + ey1) / 2, z_base)
        medio = 0.5 * math.hypot(ex1 - ex0, ey1 - ey0)
        m3.inputs["From Min"].default_value, m3.inputs["From Max"].default_value = medio * 0.8, medio * 3.2
        m3.interpolation_type = "SMOOTHSTEP"
        x3.data_type = "RGBA"
        x3.inputs[6].default_value, x3.inputs[7].default_value = lin(COL["mesa"]), lin(COL["fondo"])
        u3(g3.outputs["Position"], d3.inputs[0]); u3(d3.outputs["Value"], m3.inputs["Value"]); u3(m3.outputs["Result"], x3.inputs[0]); u3(x3.outputs[2], b3.inputs["Base Color"])
        objeto("estudio", malla_caras("estudio", [(-20000, -20000, z_base), (20000, -20000, z_base), (20000, 20000, z_base), (-20000, 20000, z_base)], [(0, 1, 2, 3)]), mp)
    else:
        mm = material("mesa", COL["mesa"])
        faldon(SUP, z_base - 0.02, mm if FORMA == "liso" else material("canto_mesa", COL["canto"]))
        marco(ex0, ey0, ex1, ey1, z_base - 0.02, mm)

    # ------------------------------------------------------------------ luz: sol + ambiente parejo (vista Standard)
    LZ = CFG["luz"]
    wd = bpy.data.worlds.new("mundo")
    SC.world = wd
    wd.use_nodes = True
    wn, wu = wd.node_tree.nodes, wd.node_tree.links.new
    for n in list(wn):
        wn.remove(n)
    w_out, w_cam, w_amb, w_lp, w_mix = (wn.new(k) for k in ("ShaderNodeOutputWorld", "ShaderNodeBackground", "ShaderNodeBackground", "ShaderNodeLightPath", "ShaderNodeMixShader"))
    w_cam.inputs["Color"].default_value = lin(COL["fondo"])
    w_amb.inputs["Color"].default_value = lin(COL.get("ambiente", "#FFFFFF"))
    w_amb.inputs["Strength"].default_value = float(LZ["ambiente"])
    wu(w_lp.outputs["Is Camera Ray"], w_mix.inputs["Fac"]); wu(w_amb.outputs[0], w_mix.inputs[1]); wu(w_cam.outputs[0], w_mix.inputs[2]); wu(w_mix.outputs[0], w_out.inputs["Surface"])
    az, el = math.radians(LZ["azimut"]), math.radians(LZ["elevacion"])      # de dónde viene la luz: 0 = norte, 90 = este
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy, sol.angle = float(LZ["sol"]), math.radians(float(LZ.get("angulo", 6)))
    sol.color = lin(COL.get("luz", "#FFF8EE"))[:3]
    so = bpy.data.objects.new("sol", sol)
    so.rotation_mode = "QUATERNION"
    so.rotation_quaternion = (-Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))).to_track_quat("-Z", "Y")
    SC.collection.objects.link(so)

    # ------------------------------------------------------------------ cámara: la del contrato, puesta cuadro a cuadro
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "VERTICAL"
    cam = bpy.data.objects.new("cam", cd)
    cam.rotation_mode = "QUATERNION"
    SC.collection.objects.link(cam)
    SC.camera = cam
    SUBE = H / 2 - Z["centro_y"]                                 # el desplazamiento de lente del contrato (px que sube la imagen)
    cd.shift_y = -SUBE / H
    DOF = BL.get("foco")
    if DOF:
        cd.dof.use_dof = True

    def poner_camara(t):
        c = M3D.camara_en(R["camara"], t)
        ojo = Vector(M3D.ojo_de(c))
        cam.location = ojo
        cam.rotation_quaternion = (Vector((c["x"], c["y"], c["alt"])) - ojo).to_track_quat("-Z", "Y")
        cd.angle_y = math.radians(c["fov"])
        cd.clip_start, cd.clip_end = max(0.5, c["dist_km"] * 0.02), 40000.0
        if DOF:
            # foco en lo que mira la cámara; la apertura se calcula para que el desenfoque en el infinito sea de `px` píxeles
            f_m = cd.sensor_height / 2 / math.tan(math.radians(c["fov"]) / 2) / 1000.0
            cd.dof.focus_distance = c["dist_km"]
            cd.dof.aperture_fstop = f_m ** 2 / ((float(DOF["px"]) * H / 1920.0 / H * cd.sensor_height / 1000.0) * c["dist_km"])
        return c

    # ------------------------------------------------------------------ líneas posadas en el relieve
    def pegar(cad, paso, lev=0.0):
        """Densifica una polilínea [[x, y, s?, salto?]] a pasos de ≤ `paso` km → (x, y, z, s, salto) sobre la superficie."""
        xs, ys, ss, sl, s = [], [], [], [], 0.0
        for i, a in enumerate(cad):
            b = cad[i + 1] if i + 1 < len(cad) else None
            xs.append(a[0]); ys.append(a[1]); ss.append(a[2] if len(a) > 2 else s); sl.append(bool(len(a) > 3 and a[3]) or b is None)
            if b is None:
                break
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if not (len(a) > 3 and a[3]):
                k = int(math.ceil(L / paso))
                for j in range(1, k):
                    u = j / k
                    xs.append(a[0] + (b[0] - a[0]) * u); ys.append(a[1] + (b[1] - a[1]) * u)
                    ss.append(a[2] + (b[2] - a[2]) * u if len(a) > 2 else s + L * u); sl.append(False)
            s += L
        xs, ys = np.asarray(xs), np.asarray(ys)
        return xs, ys, SUP.en(xs, ys) + lev, np.asarray(ss, dtype=np.float64), sl

    class Cinta:
        """Una línea como malla de sección fija («tubo» de n lados o «cinta» plana). La topología no cambia: en cada
        cuadro solo se mueven los vértices (`poner`): el radio (px → km según la cámara) y, si es una ruptura, el tramo
        encendido [lo, hi] (los anillos de fuera se pliegan sobre el frente: caras de área cero)."""
        def __init__(self, nombre, linea, mat, forma="tubo", lados=8, cerrada=False, sombra=True):
            x, y, z, s, salto = linea
            self.n, self.s, self.salto, self.cerrada = len(x), np.asarray(s, dtype=np.float64), list(salto), cerrada
            if forma == "tubo":
                a = np.arange(lados) * 2 * math.pi / lados
                self.pa, self.pz = np.cos(a), np.sin(a)
            else:                                                 # cinta: un rectángulo acostado (ancho 2r, alto 0.3r)
                self.pa, self.pz = np.array([-1.0, 1.0, 1.0, -1.0]), np.array([0.0, 0.0, 0.3, 0.3])
            L = len(self.pa)
            self.linea(x, y, z)
            caras = []
            for i in range(self.n - (0 if cerrada else 1)):
                if self.salto[i] and not cerrada:
                    continue
                j = (i + 1) % self.n
                caras += [(i * L + k, i * L + (k + 1) % L, j * L + (k + 1) % L, j * L + k) for k in range(L)]
            self.me = malla_caras(nombre, np.zeros((self.n * L, 3)), caras)
            self.ob = objeto(nombre, self.me, mat, sombra)

        def linea(self, x, y, z):
            n = self.n
            self.P = np.stack([np.asarray(x, np.float64), np.asarray(y, np.float64), np.asarray(z, np.float64)], axis=1)
            T = np.zeros((n, 2))
            for i in range(n):
                if self.cerrada:
                    a, b = (i - 1) % n, (i + 1) % n
                else:
                    a = i - 1 if i > 0 and not self.salto[i - 1] else i
                    b = i + 1 if i < n - 1 and not self.salto[i] else i
                T[i] = self.P[b, :2] - self.P[a, :2]
            T /= np.maximum(np.hypot(T[:, 0], T[:, 1]), 1e-9)[:, None]
            self.Nr = np.stack([-T[:, 1], T[:, 0]], axis=1)       # a la izquierda del sentido en que crece s

        def poner(self, r, lo=None, hi=None, sube=0.0):
            if r <= 0 or (lo is not None and hi <= lo):
                self.ob.hide_render = True
                return
            self.ob.hide_render = False
            if lo is None:
                C, Nr = self.P, self.Nr
            else:
                sc = np.clip(self.s, lo, hi)
                C = np.stack([np.interp(sc, self.s, self.P[:, k]) for k in range(3)], axis=1)
                Nr = np.stack([np.interp(sc, self.s, self.Nr[:, k]) for k in range(2)], axis=1)
                Nr /= np.maximum(np.hypot(Nr[:, 0], Nr[:, 1]), 1e-9)[:, None]
            co = np.empty((self.n, len(self.pa), 3))
            co[..., 0] = C[:, None, 0] + r * self.pa[None, :] * Nr[:, None, 0]
            co[..., 1] = C[:, None, 1] + r * self.pa[None, :] * Nr[:, None, 1]
            co[..., 2] = C[:, None, 2] + r * self.pz[None, :] + sube
            self.me.vertices.foreach_set("co", co.astype(np.float32).ravel())
            self.me.update()

    FORMA_LINEA = BL.get("linea", "tubo")
    EMI = float(CFG["falla"].get("emision", 0.0))
    DIF = float(CFG["falla"].get("difuso", 1.0))
    m_acento = material("acento", COL["acento"], EMI, DIF)
    m_sec = material("secundario", COL["secundario"], EMI * 0.5, 1.0)
    m_dormida = material("falla_dormida", COL["falla_dormida"])

    fallas3d = {}
    for f in FALLAS:
        ln = pegar(f["cadena"], 1.0)
        mat_f = m_acento if f["protagonista"] else m_sec
        o = {"f": f, "dormida": Cinta("falla_" + f["id"], ln, m_dormida, FORMA_LINEA, 6, sombra=False), "rupturas": []}
        for k, e in enumerate([e for e in EV if e["tipo"] == "ruptura" and e["pieza"] == f["id"]]):
            cabezas = []
            for j in range(2):
                bm = bmesh.new()
                bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
                me = bpy.data.meshes.new("cabeza_%s_%d_%d" % (f["id"], k, j))
                bm.to_mesh(me); bm.free()
                try:
                    me.shade_smooth()
                except Exception:
                    pass
                ob = objeto(me.name, me, mat_f, sombra=False)
                ob.hide_render = True
                cabezas.append(ob)
            o["rupturas"].append({"e": e, "cinta": Cinta("ruptura_%s_%d" % (f["id"], k), ln, mat_f, FORMA_LINEA, 10), "cabezas": cabezas})
        fallas3d[f["id"]] = o

    lineas = {}                                                  # id → [cintas] de frontera y rutas
    for p in PIEZAS:
        if p["tipo"] == "frontera":
            mat_l = m_acento if p["protagonista"] else material("frontera", COL["frontera"])
            lineas[p["id"]] = {"p": p, "px": CFG["frontera"]["ancho"] * (1.7 if p["protagonista"] else 1.0), "cintas":
                               [Cinta("frontera_%s_%d" % (p["id"], k), pegar([[q[0], q[1]] for q in an] + [[an[0][0], an[0][1]]], 1.5), mat_l, FORMA_LINEA, 5, sombra=False)
                                for k, an in enumerate(p["anillos"])]}
        elif p["tipo"] == "ruta":
            # rayas: cada raya es un tramo propio (55 % del periodo), cortado con un «salto»
            x, y, z, s, _ = pegar(p["puntos"], 0.75)
            raya = float(CFG["ruta"].get("raya_km", 6))
            idx = [i for i in range(len(s)) if (s[i] / raya) % 1 <= 0.55]
            ln = (x[idx], y[idx], z[idx], s[idx], [k == len(idx) - 1 or idx[k + 1] != idx[k] + 1 for k in range(len(idx))])
            mat_l = m_acento if p["protagonista"] else material("ruta", COL["ruta"])
            lineas[p["id"]] = {"p": p, "px": CFG["ruta"]["ancho"] * (1.5 if p["protagonista"] else 1.0), "cintas": [Cinta("ruta_" + p["id"], ln, mat_l, FORMA_LINEA, 5, sombra=False)]}

    # ------------------------------------------------------------------ luces: un bloque por pueblo, en una sola malla
    LUZ = []                                                     # {x, y, z, peso, id, on, ac}
    for p in PIEZAS:
        if p["tipo"] == "luces":
            for q in p["puntos"]:
                LUZ.append({"x": q[0], "y": q[1], "peso": q[2], "id": q[3], "on": p.get("encendidas", True) is not False, "ac": bool(p["protagonista"])})
    luces_ob = None
    if LUZ:
        LX, LY = np.array([l["x"] for l in LUZ]), np.array([l["y"] for l in LUZ])
        LZb, LP = SUP.en(LX, LY), np.array([l["peso"] for l in LUZ])
        for f in FALLAS:                                         # distancia de cada pueblo a cada falla (para las ondas que salen del trazo)
            f["_dluz"] = np.array([M3D.mas_cercano(f["cadena"], l["x"], l["y"])[1] for l in LUZ])
        nl = len(LUZ)
        caras = []
        for i in range(nl):
            b = 8 * i
            caras += [(b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5), (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
        me_l = malla_caras("pueblos", np.zeros((nl * 8, 3)), caras)
        at = me_l.attributes.new("enc", "FLOAT", "POINT")
        ml = bpy.data.materials.new("pueblos")
        ml.use_nodes = True
        n4, u4 = ml.node_tree.nodes, ml.node_tree.links.new
        b4 = n4.get("Principled BSDF")
        b4.inputs["Roughness"].default_value = 1.0
        b4.inputs["Specular IOR Level"].default_value = 0.0
        a4, x4 = n4.new("ShaderNodeAttribute"), n4.new("ShaderNodeMix")
        a4.attribute_name = "enc"
        x4.data_type = "RGBA"
        x4.inputs[6].default_value = lin(COL["luces_apagadas"])
        x4.inputs[7].default_value = lin(COL["acento"] if any(l["ac"] for l in LUZ) else COL["luces"])
        u4(a4.outputs["Fac"], x4.inputs[0]); u4(x4.outputs[2], b4.inputs["Base Color"])
        if float(CFG["luces"].get("emision", 0)) > 0:
            em = n4.new("ShaderNodeMath")
            em.operation = "MULTIPLY"
            em.inputs[1].default_value = float(CFG["luces"]["emision"])
            u4(a4.outputs["Fac"], em.inputs[0]); u4(x4.outputs[2], b4.inputs["Emission Color"]); u4(em.outputs[0], b4.inputs["Emission Strength"])
        luces_ob = objeto("pueblos", me_l, ml)
        ESQ = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]], dtype=np.float64)

    # ------------------------------------------------------------------ flechas del corrimiento (evento «deslizar»)
    DESL = [e for e in EV if e["tipo"] == "deslizar"]
    GAL = [(0.5, 0.0), (-0.5, 0.5), (-0.5, 0.5), (-0.18, 0.0), (-0.5, -0.5), (-0.5, -0.5)]    # una punta de flecha (largo, ancho) hacia +largo
    m_flechas = material("flechas", COL["flechas"], float(CFG["falla"].get("flechas_emision", 0.0)))
    for ne, e in enumerate(DESL):
        e["_n"] = int(math.ceil(e["km"] / e["periodo_km"])) + 2
        caras = []
        for k in range(2 * e["_n"]):
            b = 12 * k
            caras += [(b + 6, b + 9, b + 8, b + 7), (b + 6, b + 11, b + 10, b + 9)] + [(b + i, b + (i + 1) % 6, b + 6 + (i + 1) % 6, b + 6 + i) for i in range(6)]
        e["_me"] = malla_caras("flechas_%d" % ne, np.zeros((12 * 2 * e["_n"], 3)), caras)
        e["_ob"] = objeto(e["_me"].name, e["_me"], m_flechas)
        e["_ob"].hide_render = True

    # ------------------------------------------------------------------ «resaltar» un lugar: núcleo y dos anillos que se abren
    m_resalte = material("resalte", COL["resalte"], float(CFG.get("resalte_emision", 0.0)))
    RES = [e for e in EV if e["tipo"] == "resaltar" and not e.get("pieza")]
    ANG = np.arange(72) * 2 * math.pi / 72
    for k, e in enumerate(RES):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        me = bpy.data.meshes.new("resalte_%d" % k)
        bm.to_mesh(me); bm.free()
        e["_nucleo"] = objeto(me.name, me, m_resalte, sombra=False)
        e["_nucleo"].hide_render = True
        cero = (np.zeros(72), np.zeros(72), np.zeros(72), ANG, [False] * 72)
        e["_anillos"] = [Cinta("resalte_%d_%d" % (k, j), cero, m_resalte, "cinta", cerrada=True, sombra=False) for j in range(2)]

    # ------------------------------------------------------------------ el mundo en t: cámara + eventos (puro: mismo t, mismo cuadro)
    def mundo_en(t):
        c = poner_camara(t)
        kpp = 2 * c["dist_km"] * math.tan(math.radians(c["fov"]) / 2) / H        # km por píxel a la distancia de lo que mira la cámara
        k = clamp(1 + 70 / c["dist_km"], 1, 2.4)                                  # las líneas engordan al acercarse (como en three)
        kl = clamp(1 + 30 / c["dist_km"], 1, 1.8)
        FA = CFG["falla"]
        brillo = {}
        for e in EV:
            if e["tipo"] == "resaltar" and e.get("pieza") and e["t"] <= t <= e["t"] + e["dur"]:
                tr = t - e["t"]
                brillo[e["pieza"]] = 1 + 0.9 * suave(0, 0.3, tr) * suave(e["dur"], e["dur"] - 0.4, tr) * (0.8 + 0.2 * math.cos(tr / 1.2 * math.pi * 2))
        # fallas: la línea dormida, el tramo roto de cada ruptura y la cabeza de cada frente
        for fid, o in fallas3d.items():
            b = brillo.get(fid, 1.0)
            o["dormida"].poner(FA["dormida_px"] * k * kpp * (1 + 1.8 * (b - 1)), sube=FA["dormida_px"] * k * kpp * 0.35)
            for r in o["rupturas"]:
                e, tr = r["e"], t - r["e"]["t"]
                u = clamp(tr / e["dur"])
                rn = FA["nucleo_px"] * k * kpp * (1 + 0.5 * (b - 1)) * suave(0, 0.2, tr)
                r["cinta"].poner(rn if tr > 0 else 0, e["s0"] - e["km_menos"] * u, e["s0"] + e["km_mas"] * u, sube=rn * 0.55)
                viva = 0 < tr < e["dur"] + 0.5
                fin, ini = suave(e["dur"] + 0.5, e["dur"] - 0.1, tr), suave(0, 0.15, tr)
                for j, (sg, alc) in enumerate(((-1, e["km_menos"]), (1, e["km_mas"]))):
                    ob = r["cabezas"][j]
                    ob.hide_render = not (viva and alc > 0 and ini * fin > 0.02)
                    if not ob.hide_render:
                        x, y = M3D.punto_en_s(o["f"]["cadena"], e["s0"] + sg * alc * u)
                        rc = FA["cabeza_px"] * k * kpp * (0.6 + 0.4 * ini * fin)
                        ob.location, ob.scale = (x, y, sup(x, y) + rn * 0.55), (rc, rc, rc)
        for lid, o in lineas.items():
            b = brillo.get(lid, 1.0)
            for cn in o["cintas"]:
                r = o["px"] * kl * kpp * (1 + 0.8 * (b - 1))
                cn.poner(r, sube=r * 0.4)
        # deslizar: galones a los dos lados, en sentidos opuestos
        for e in DESL:
            tr = t - e["t"]
            vivo = 0 <= tr <= e["dur"]
            e["_ob"].hide_render = not vivo
            if not vivo:
                continue
            alfa = suave(0, 0.35, tr) * suave(e["dur"], e["dur"] - 0.35, tr)
            cad, medio, per = POR_ID[e["pieza"]]["cadena"], e["km"] / 2, e["periodo_km"]
            ancho = 0.62 * FA["flechas_px"] * k * kpp
            carril, largo = 0.77 * FA["flechas_px"] * k * kpp, min(0.62 * per, 1.25 * ancho)
            fase = (tr * e["vel"] / per) % 1.0
            V = np.zeros((12 * 2 * e["_n"], 3))
            q = 0
            for lado in (1, -1):                                  # +1: a la izquierda del trazo (el norte en un trazo oeste → este)
                dr = -lado * e["sentido"]                         # corrimiento izquierdo: el lado izquierdo va hacia −s
                for j in range(e["_n"]):
                    s = e["s0"] + dr * per * (j - e["_n"] / 2 + fase)
                    env = (1 - suave(medio * 0.72, medio, abs(s - e["s0"]))) * alfa
                    x, y = M3D.punto_en_s(cad, s)
                    x2, y2 = M3D.punto_en_s(cad, s + 0.6)
                    x1, y1 = M3D.punto_en_s(cad, s - 0.6)
                    tx, ty = x2 - x1, y2 - y1
                    n_ = math.hypot(tx, ty) or 1.0
                    tx, ty = tx / n_, ty / n_
                    cx_, cy_ = x - ty * lado * carril, y + tx * lado * carril
                    zs = sup(cx_, cy_) + 0.06 * ancho
                    for kk, (a_, b_) in enumerate(GAL):
                        px_ = cx_ + (tx * dr * a_ * largo - ty * b_ * ancho) * env
                        py_ = cy_ + (ty * dr * a_ * largo + tx * b_ * ancho) * env
                        V[q + kk] = (px_, py_, zs)
                        V[q + 6 + kk] = (px_, py_, zs + 0.22 * ancho * env)
                    q += 12
            e["_me"].vertices.foreach_set("co", V.astype(np.float32).ravel())
            e["_me"].update()
        # ondas: el anillo pintado en el relieve
        ondas = []
        for e in ONDAS:
            if e["t"] <= t <= e["t"] + e["dur"]:
                u = (t - e["t"]) / e["dur"]
                r = e["radio_km"] * (1 - (1 - u) ** 1.6)
                kk = (1 - u) ** 0.8 * suave(0, 0.06, u) * float(CFG.get("onda", 0.7))
                ondas.append({"e": e, "r": r, "k": kk})
                e["_r"].outputs[0].default_value, e["_w"].outputs[0].default_value, e["_k"].outputs[0].default_value = r, float(CFG.get("onda_ancho", 1.0)) * (1.3 + r * 0.016), kk
            else:
                e["_k"].outputs[0].default_value = 0.0
        # resaltar un lugar
        for e in RES:
            tr = t - e["t"]
            vivo = 0 <= tr <= e["dur"]
            e["_nucleo"].hide_render = not vivo
            if not vivo:
                for cn in e["_anillos"]:
                    cn.ob.hide_render = True
                continue
            K = suave(0, 0.25, tr) * suave(e["dur"], e["dur"] - 0.4, tr)
            Rm = float(CFG.get("resalte_px", 320)) / 2 * kpp
            rn = 0.085 * Rm * K
            zc = sup(e["x"], e["y"])
            e["_nucleo"].location, e["_nucleo"].scale = (e["x"], e["y"], zc + rn * 0.5), (rn, rn, rn * 0.7)
            for j, cn in enumerate(e["_anillos"]):
                ph = (tr / 1.25 + 0.5 * j) % 1.0
                rr = (0.14 + 0.8 * ph) * Rm
                xs, ys = e["x"] + rr * np.cos(ANG), e["y"] + rr * np.sin(ANG)
                cn.linea(xs, ys, np.full(len(ANG), max(zc, float(SUP.en(xs, ys).max())) + 0.2))   # plano: posado en un terreno quebrado sale torcido
                cn.poner(0.02 * Rm * K * (1 - ph) ** 0.8)
        # luces: encender, apagar, parpadear, resaltar; la onda las aviva al pasar
        if luces_ob:
            v = np.array([1.0 if l["on"] else 0.0 for l in LUZ])
            for e in EV:
                tp = e["tipo"]
                if tp not in ("encender", "apagar", "parpadear") and not (tp == "resaltar" and e.get("lugar")):
                    continue
                for i, l in enumerate(LUZ):
                    if tp == "resaltar":
                        if e["lugar"] == l["id"] and e["t"] <= t <= e["t"] + e["dur"]:
                            v[i] = max(v[i], 1) + 1.2
                        continue
                    if not (e["lugares"] == "todos" or l["id"] in e["lugares"]):
                        continue
                    if tp == "encender":
                        v[i] += (1 - v[i]) * suave(0, 1, (t - e["t"] - azar(i, 3) * e["dur"] * 0.7) / max(0.05, e["dur"] * 0.3))
                    elif tp == "apagar":
                        v[i] *= 1 - suave(0, 1, (t - e["t"] - azar(i, 5) * e["dur"] * 0.7) / max(0.05, e["dur"] * 0.3))
                    elif e["t"] <= t <= e["t"] + e["dur"]:
                        env = math.sin(math.pi * (t - e["t"]) / e["dur"])
                        v[i] = v[i] * (1 - env) + v[i] * env * (0.12 if azar(i, int(math.floor(t * 14))) < 0.45 else 1.25)
            for o in ondas:
                e = o["e"]
                d = POR_ID[e["pieza"]]["_dluz"] if e.get("pieza") else np.hypot(LX - e["x"], LY - e["y"])
                v *= 1 + 1.5 * np.exp(-((d - o["r"]) / (5 + o["r"] * 0.05)) ** 2) * min(1, o["k"] * 2)
            LU = CFG["luces"]
            lado = np.clip(LU["km"] * (0.45 + 0.75 * LP), LU["min_px"] * kpp, LU["max_px"] * kpp) / 2 * np.where(v > 0.001, 1, 0)
            lado = lado * (1 + 0.18 * np.maximum(v - 1, 0))
            alto = 2 * lado * float(LU.get("alto", 0.8)) * (0.15 + 0.85 * np.minimum(v, 1) + 0.6 * np.maximum(v - 1, 0))
            co = np.empty((len(LUZ), 8, 3))
            for q in range(4):
                co[:, q, 0] = co[:, q + 4, 0] = LX + ESQ[q, 0] * lado
                co[:, q, 1] = co[:, q + 4, 1] = LY + ESQ[q, 1] * lado
            co[:, :4, 2] = (LZb - 0.3)[:, None]
            co[:, 4:, 2] = (LZb + alto)[:, None]
            luces_ob.data.vertices.foreach_set("co", co.astype(np.float32).ravel())
            luces_ob.data.attributes["enc"].data.foreach_set("value", np.repeat(np.clip(v, 0, 1.3), 8).astype(np.float32))
            luces_ob.data.update()
        return c

    # ------------------------------------------------------------------ render: vista Standard, sin desenfoque de movimiento
    RN = SC.render
    RN.resolution_x, RN.resolution_y, RN.resolution_percentage = W, H, A.escala
    RN.use_motion_blur = False
    RN.film_transparent = False
    RN.image_settings.file_format = "PNG"
    RN.image_settings.color_mode = "RGB"
    RN.image_settings.color_depth = "8"
    RN.image_settings.compression = 15
    SC.view_settings.view_transform = "Standard"
    SC.view_settings.look = "None"
    SC.view_settings.exposure, SC.view_settings.gamma = 0, 1
    RN.use_persistent_data = True
    RN.fps = FPS
    if CYCLES:
        # Cycles en la GPU (Metal) con pocas muestras y denoise: la oclusión y la penumbra son las del trazado de rayos
        RN.engine = "CYCLES"
        pr = bpy.context.preferences.addons["cycles"].preferences
        pr.compute_device_type = "METAL"
        pr.get_devices()
        for d in pr.devices:
            d.use = d.type == "METAL"
        cy = SC.cycles
        cy.device = "GPU"
        cy.samples = MUESTRAS
        cy.use_adaptive_sampling = False
        cy.use_denoising = True
        cy.denoiser = "OPENIMAGEDENOISE"
        cy.denoising_use_gpu = True
        cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        cy.max_bounces = cy.diffuse_bounces = int(BL.get("rebotes", 1))
        cy.glossy_bounces = cy.transmission_bounces = 0
        cy.caustics_reflective = cy.caustics_refractive = False
        cy.sample_clamp_indirect = 3.0
        cy.use_animated_seed = False
        cy.seed = 7
    else:
        RN.engine = "BLENDER_EEVEE"
        ee = SC.eevee
        ee.taa_render_samples = MUESTRAS
        ee.use_shadows = True
        ee.shadow_ray_count, ee.shadow_step_count = 1, 6
        ee.use_raytracing = ee.use_fast_gi = False
        sol.use_shadow_jitter = True
        sol.shadow_jitter_overblur = float(BL.get("sombra_suave", 10))
        if DOF:
            ee.bokeh_max_size = 160.0
            ee.use_bokeh_jittered = True
            ee.bokeh_overblur = 8.0
        if float(BL.get("oclusion", 0)) > 0:   # el nodo de oclusión del material lee el horizonte en pantalla
            ee.use_raytracing = True
            ee.ray_tracing_method = "SCREEN"
            ee.use_fast_gi = True
            ee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
            ee.fast_gi_distance = float(BL.get("oclusion_km", 8)) * 1.5
            ee.fast_gi_ray_count, ee.fast_gi_step_count = 4, 16
            ee.fast_gi_resolution = "1"

    # la cámara de Blender cae en el mismo píxel que la proyección de maqueta3d.py (con la que se proyectan las marcas)
    def desfase_px(t):
        c = mundo_en(t)
        bpy.context.view_layer.update()
        pr, peor = M3D.proyector(c, W, H, SUBE), 0.0
        for dx, dy in ((0, 0), (0.25, 0.1), (-0.3, 0.2), (0.1, -0.3), (-0.2, -0.25)):
            x, y = c["x"] + dx * c["dist_km"], c["y"] + dy * c["dist_km"]
            p = pr(x, y, c["alt"])
            v = world_to_camera_view(SC, cam, Vector((x, y, c["alt"])))
            if p:
                peor = max(peor, math.hypot(v.x * W - p[0], (1 - v.y) * H - p[1]))
        return peor
    peor = max(desfase_px(n / FPS) for n in {cuadros[0], cuadros[len(cuadros) // 2], cuadros[-1]})
    print("BUILD %s · %.2f s · malla %d×%d (paso %d) · %s %d muestras · cámara ↔ proyección: %.2f px" % (R["estilo"], time.time() - T0, SUP.nx, SUP.ny, PASO, "Cycles" if CYCLES else "Eevee", MUESTRAS, peor))
    if peor > 1.5:
        print("FALLA la cámara de Blender no coincide con la proyección de maqueta3d.py (%.1f px): las marcas no caerían en su lugar" % peor)
        return 1
    if A.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(A.blend))

    os.makedirs(A.salida, exist_ok=True)
    T1 = time.time()
    for n in cuadros:
        tc = time.time()
        mundo_en(n / FPS)
        RN.filepath = os.path.join(os.path.abspath(A.salida), "c_%05d.png" % n)
        bpy.ops.render.render(write_still=True)
        if not A.todo or n % 30 == 0:
            print("CUADRO %d · %.2f s" % (n, time.time() - tc), flush=True)
    dt = time.time() - T1
    print("RENDER3D %s · %d cuadros · %.1f s · %.3f s/cuadro" % (R["estilo"], len(cuadros), dt, dt / max(1, len(cuadros))), flush=True)
    return 0


if __name__ == "__main__":
    try:
        codigo = main()
    except SystemExit as e:
        codigo = e.code if isinstance(e.code, int) else 2
    sys.stdout.flush()
    sys.exit(codigo or 0)
