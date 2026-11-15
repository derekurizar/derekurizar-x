// Motor de la maqueta 3D (/video-3d): three.js dibujado cuadro a cuadro por HyperFrames.
// Entrada única: window.MAQUETA, el maqueta.json ya RESUELTO por scripts/maqueta3d.py (lugares en unidades de la escena,
// cadenas de falla, caminos, cámara con su altura, colores del estilo y de la paleta, zona del formato). Aquí no hay red,
// reloj ni azar: cada cuadro es una función pura de t (el mismo t da el mismo cuadro).
//   1) mundo:   un MÓDULO de video/maqueta/mundos/<escala>.js (MAQ.MUNDOS: pais · ciudad · esquema; M.mundo.escala) que
//               construye el suelo y le da a las piezas ctx.altura(x, y), ctx.geo(lon, lat), la escala (ctx.unidad_m:
//               metros por unidad) y sus caminos y lugares con nombre (ctx.caminos, ctx.lugares). El núcleo no sabe de relieves
//   2) estilo:  un registro ESTILOS (modo del shader del suelo, cubos, brillos aditivos); cada mundo lo pinta a su modo
//   3) vocabulario: las piezas, los eventos, los objetos y los mundos son MÓDULOS (video/maqueta/<clase>/<tipo>.js, con su
//      ficha <tipo>.json; catálogo: design/sets3d/vocabulario.json) que se registran solos en window.MAQ antes de este
//      archivo. Aquí no hay ningún `tipo ===`: el núcleo los arma por su `orden` y en cada cuadro corre inicio → aplicar
//      (cada evento, en el orden del maqueta.json) → en. Contrato: referencias/diseno/maqueta3d.md («Añadir vocabulario»)
//   4) cuadro:  cámara por claves → vocabulario → render → capa 2D (capa.js)
// La escena: x = este, y = norte, altura hacia arriba → three (x, altura, −y), en la unidad del mundo (pais: km; ciudad y
// esquema: metros). Ningún color escrito aquí: todos llegan en MAQUETA.col (design/sets3d/estilos.json + design/tokens.json).
import * as THREE from "./three/three.module.js";

const M = window.MAQUETA;
const W = M.W, H = M.H, EXAG = M.exageracion, MU = M.mundo;
const COL = M.col, CFG = M.estilo_cfg;
const lin = (hex) => new THREE.Color(hex);                       // sRGB → lineal (ColorManagement)
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const suave = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
const hash = (i, k = 0) => { let h = Math.imul((i | 0) + 0x9e3779b9, 0x85ebca6b) ^ Math.imul((k | 0) + 0x7f4a7c15, 0xc2b2ae35); h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 12; return (h >>> 0) / 4294967296; };

// ---------- estilos: lo que cambia de uno a otro (el resto es el mismo código) ----------
// modo: rama del shader del relieve · cubos: relieve en columnas · aditivo: brillos que suman luz (de noche)
const ESTILOS = {
  color:    { modo: 0, cubos: false, aditivo: false },
  noche:    { modo: 1, cubos: false, aditivo: true },
  contorno: { modo: 2, cubos: false, aditivo: false },
  voxel:    { modo: 3, cubos: true,  aditivo: false },
  plano:    { modo: 4, cubos: false, aditivo: true },
};
const ES = ESTILOS[M.estilo];
if (!ES) throw new Error("estilo sin motor three: " + M.estilo);

const MUNDO = window.MAQ && window.MAQ.MUNDOS && window.MAQ.MUNDOS[MU.escala];
if (!MUNDO) throw new Error("mundo sin módulo: " + MU.escala + " (video/maqueta/mundos/" + MU.escala + ".js)");
const altura = (x, y) => ctx.altura(x, y);                       // la pone el mundo (unidades de la escena, ya exagerada)
const V3 = (x, y, lev = 0) => new THREE.Vector3(x, altura(x, y) + lev, -y);

// ---------- render ----------
const canvas = document.getElementById("gl");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.setClearColor(lin(COL.fondo), 1);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, W / H, 1, 4000);
camera.setViewOffset(W, H, 0, H / 2 - M.zona.centro_y, W, H);
const RES = new THREE.Vector2(W, H);

// GLSL común: ruido fijo por píxel (grano y tramado), fondo y niebla (la «encendida» de las fallas es del mundo pais)
const GLSL_COMUN = `
  uniform vec3 cFondo, cFondo2; uniform vec2 uRes; uniform float uGrano;
  float ruido(vec2 p) { return fract(sin(dot(floor(p), vec2(12.9898, 78.233))) * 43758.5453); }
  vec3 fondoEn(vec2 frag) { float v = frag.y / uRes.y; return mix(cFondo2, cFondo, smoothstep(0.0, 1.0, v)); }
  uniform vec2 uNiebla;                                  // unidades desde la cámara: dónde empieza y dónde termina de fundirse con el fondo
  vec3 niebla(vec3 c, vec3 pos, vec2 frag) { return mix(c, fondoEn(frag), smoothstep(uNiebla.x, uNiebla.y, distance(pos, cameraPosition))); }
  vec3 salida(vec3 c, vec2 frag) {   // lineal → sRGB + grano fijo
    c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));
    return c + (ruido(frag) - 0.5) * uGrano;
  }`;
const NIEBLA = new THREE.Vector2(3000, 9000);
const uComun = () => ({ cFondo: { value: lin(COL.fondo) }, cFondo2: { value: lin(COL.fondo2) }, uRes: { value: RES }, uGrano: { value: CFG.grano }, uNiebla: { value: NIEBLA } });

// fondo: un triángulo a pantalla completa (degradado del estilo + grano)
{
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
  const m = new THREE.ShaderMaterial({ uniforms: uComun(), depthTest: false, depthWrite: false,
    vertexShader: "void main(){ gl_Position = vec4(position.xy, 1.0, 1.0); }",
    fragmentShader: GLSL_COMUN + "void main(){ gl_FragColor = vec4(salida(fondoEn(gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
  const q = new THREE.Mesh(g, m); q.frustumCulled = false; q.renderOrder = -10; scene.add(q);
  // el plano exterior: el mundo sigue más allá de la caja del relieve (mar hondo) hasta fundirse con el fondo a lo lejos,
  // para que el 3D llegue a los bordes del lienzo
  const gp = new THREE.PlaneGeometry(MU.plano.lado, MU.plano.lado); gp.rotateX(-Math.PI / 2);
  const mp = new THREE.ShaderMaterial({ uniforms: { ...uComun(), cExterior: { value: lin(COL.exterior) } }, depthTest: false, depthWrite: false,
    vertexShader: "varying vec3 vPos; void main(){ vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: GLSL_COMUN + "uniform vec3 cExterior; varying vec3 vPos; void main(){ gl_FragColor = vec4(salida(niebla(cExterior, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
  const plano = new THREE.Mesh(gp, mp); plano.position.y = MU.plano.y; plano.frustumCulled = false; plano.renderOrder = -9; scene.add(plano);
}

// ---------- geometría de polilíneas (la usan los módulos) ----------
function puntoEnS(cad, s) {                                      // [x, y] en la cadena a s (unidades) de su inicio
  if (s <= cad[0][2]) return [cad[0][0], cad[0][1]];
  for (let i = 0; i < cad.length - 1; i++) { const a = cad[i], b = cad[i + 1];
    if (s <= b[2]) { const u = (s - a[2]) / Math.max(1e-6, b[2] - a[2]); return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]; } }
  const z = cad[cad.length - 1]; return [z[0], z[1]];
}
function distCadena(cad, x, y) {                                 // distancia (unidades) de un punto a la cadena (sin los saltos)
  let m = 1e9;
  for (let i = 0; i < cad.length - 1; i++) { const a = cad[i], b = cad[i + 1]; if (a[3]) continue;
    const dx = b[0] - a[0], dy = b[1] - a[1], h = clamp(((x - a[0]) * dx + (y - a[1]) * dy) / Math.max(1e-9, dx * dx + dy * dy));
    m = Math.min(m, Math.hypot(x - a[0] - dx * h, y - a[1] - dy * h)); }
  return m;
}
function enCadena(cad, s) {                                      // {x, y, dx, dy}: punto a s y su dirección (unitaria); null sin cadena
  if (!cad || cad.length < 2) return null;
  const L = cad[cad.length - 1][2], sc = clamp(s, 0, L);
  let i = 0; while (i < cad.length - 2 && sc > cad[i + 1][2]) i++;
  const a = cad[i], b = cad[i + 1], d = Math.max(1e-9, Math.hypot(b[0] - a[0], b[1] - a[1])), [x, y] = puntoEnS(cad, sc);
  return { x, y, dx: (b[0] - a[0]) / d, dy: (b[1] - a[1]) / d };
}

// ---------- cintas: líneas con ancho en píxeles, pegadas al relieve (las usan falla, frontera, ruta…) ----------
const VERT_CINTA = `
  attribute vec3 aPrev, aNext; attribute float aLado, aS;
  uniform vec2 uRes; uniform float uAncho;
  varying float vLado, vS;
  void main() {
    mat4 pv = projectionMatrix * modelViewMatrix;
    vec4 c = pv * vec4(position, 1.0), a = pv * vec4(aPrev, 1.0), b = pv * vec4(aNext, 1.0);
    vec2 d = b.xy / max(b.w, 1e-3) * uRes - a.xy / max(a.w, 1e-3) * uRes;
    float l = length(d); d = l > 1e-5 ? d / l : vec2(1.0, 0.0);
    c.xy += vec2(-d.y, d.x) * aLado * uAncho * 2.0 / uRes * c.w;
    gl_Position = c; vLado = aLado; vS = aS;
  }`;
function geoCinta(pts) {   // pts: [{v: Vector3, s, salto}] (salto: después de este punto no hay tramo)
  const n = pts.length, pos = [], prev = [], next = [], lado = [], ss = [], idx = [];
  for (let i = 0; i < n; i++) {
    const p = pts[i].v;
    const a = i > 0 && !pts[i - 1].salto ? pts[i - 1].v : null, b = i < n - 1 && !pts[i].salto ? pts[i + 1].v : null;
    const pa = a || p.clone().multiplyScalar(2).sub(b || p), pb = b || p.clone().multiplyScalar(2).sub(a || p);
    for (const l of [1, -1]) { pos.push(p.x, p.y, p.z); prev.push(pa.x, pa.y, pa.z); next.push(pb.x, pb.y, pb.z); lado.push(l); ss.push(pts[i].s); }
    if (b) idx.push(2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 1, 2 * i + 3, 2 * i + 2);
  }
  const g = new THREE.BufferGeometry(), F = (a, k) => new THREE.BufferAttribute(new Float32Array(a), k);
  g.setAttribute("position", F(pos, 3)); g.setAttribute("aPrev", F(prev, 3)); g.setAttribute("aNext", F(next, 3));
  g.setAttribute("aLado", F(lado, 1)); g.setAttribute("aS", F(ss, 1)); g.setIndex(idx);
  return g;
}
// densifica una polilínea [[x, y, s?, salto?]] a pasos de ≤ `paso` (unidades de la escena) y la pega al suelo
function pegar(cad, paso, lev) {
  const out = []; let s = 0;
  for (let i = 0; i < cad.length; i++) {
    const a = cad[i], b = cad[i + 1];
    out.push({ v: V3(a[0], a[1], lev), s: a[2] !== undefined ? a[2] : s, salto: !!a[3] || !b });
    if (!b) break;
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (!a[3]) { const k = Math.ceil(L / paso);
      for (let j = 1; j < k; j++) { const u = j / k, x = a[0] + (b[0] - a[0]) * u, y = a[1] + (b[1] - a[1]) * u;
        out.push({ v: V3(x, y, lev), s: a[2] !== undefined ? a[2] + (b[2] - a[2]) * u : s + L * u, salto: false }); } }
    s += L;
  }
  return out;
}
const cintas = [];   // {mat, base, alfa}: el núcleo les ajusta el ancho a la distancia en cada cuadro
function cintaSimple(pts, color, ancho, alfa, orden, extra = {}) {
  const mat = new THREE.ShaderMaterial({
    uniforms: { ...uComun(), uAncho: { value: ancho }, cColor: { value: lin(color) }, uAlfa: { value: alfa }, uRaya: { value: extra.raya || 0 } },
    vertexShader: VERT_CINTA, transparent: true, depthWrite: false, depthTest: extra.oculta !== false,
    fragmentShader: `uniform vec3 cColor; uniform float uAlfa, uRaya; varying float vLado, vS;
      void main(){ float a = uAlfa * smoothstep(0.0, 0.5, 1.0 - abs(vLado)); if (uRaya > 0.0) a *= step(fract(vS / uRaya), 0.55);
        vec3 c = cColor; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }` });
  const m = new THREE.Mesh(geoCinta(pts), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m);
  const c = { mat, base: ancho, alfa }; cintas.push(c); return c;
}

const LINEAS = {};    // id de pieza → cinta: «resaltar» la pieza sube su alfa (ctx.linea(id, cinta))

// ---------- superficies de mundo (las usan los mundos ciudad y esquema y sus piezas: calles, edificios, agua, zona,
// carretera): geometría en unidades de la escena posada sobre el suelo, con color por vértice. Nada de esto se crea en
// un mundo «pais» si sus piezas no lo piden.
// TONOS: los colores de una ciudad en cada estilo, mezclados de los del estilo (ningún color nuevo)
const TONOS = (() => {
  const C = (k) => lin(COL[k]), T = {};
  if (ES.modo === 1) {                 // noche: suelo casi negro, calles que apenas brillan, techos claros
    T.suelo = C("exterior").lerp(C("tierra_baja"), 0.16); T.verde = T.suelo.clone().lerp(C("tierra_media"), 0.2);
    T.calle = T.suelo.clone().lerp(C("costa"), 0.22); T.calle_mayor = T.suelo.clone().lerp(C("costa"), 0.5);
    T.muro = C("exterior").lerp(C("tierra_baja"), 0.32); T.techo = C("tierra_baja").lerp(C("tierra_media"), 0.45);
    T.asfalto = C("exterior").lerp(C("linea"), 0.6); T.raya = C("costa"); T.central = C("luces"); T.borde = C("costa");
    T.agua = C("mar").lerp(C("costa"), 0.1); T.arena = C("tierra_media").lerp(C("exterior"), 0.55); T.pavimento = T.suelo.clone().lerp(C("costa"), 0.08);
    T.campo = T.suelo.clone().lerp(C("tierra_baja"), 0.25); T.campo2 = T.suelo.clone().lerp(C("tierra_media"), 0.3);
  } else if (ES.modo === 4) {          // plano: caras del color del fondo y todo en línea clara
    T.suelo = C("tierra_baja"); T.verde = T.suelo.clone().lerp(C("linea"), 0.1);
    T.calle = T.suelo.clone().lerp(C("linea"), 0.22); T.calle_mayor = T.suelo.clone().lerp(C("linea"), 0.45);
    T.muro = C("tierra_baja").lerp(C("linea"), 0.05); T.techo = C("tierra_baja").lerp(C("linea"), 0.12);
    T.asfalto = C("tierra_baja").lerp(C("linea"), 0.08); T.raya = C("linea"); T.central = C("linea"); T.borde = C("linea");
    T.agua = C("mar_hondo"); T.arena = T.suelo.clone().lerp(C("linea"), 0.06); T.pavimento = T.suelo.clone().lerp(C("linea"), 0.04);
    T.campo = T.suelo.clone().lerp(C("linea"), 0.05); T.campo2 = T.suelo.clone().lerp(C("linea"), 0.1);
  } else {                             // color, contorno, voxel: suelo claro, calles más claras, edificios de papel
    T.suelo = C("tierra_media").lerp(C("fondo"), 0.62); T.verde = C("tierra_baja");
    T.calle = C("fondo").lerp(C("costa"), 0.6); T.calle_mayor = C("costa");
    T.muro = C("fondo").lerp(C("linea"), 0.1); T.techo = C("fondo").lerp(C("costa"), 0.6);
    T.asfalto = C("linea").lerp(C("fondo"), 0.3); T.raya = C("costa"); T.central = C("luces"); T.borde = C("costa");
    T.agua = C("mar"); T.arena = C("tierra_media").lerp(C("costa"), 0.45); T.pavimento = T.suelo.clone().lerp(C("costa"), 0.4);
    T.campo = C("tierra_baja"); T.campo2 = C("tierra_baja").lerp(C("tierra_media"), 0.55);
  }
  T.acento = C("acento"); T.secundario = C("secundario"); T.linea = C("linea");
  return T;
})();
// la luz de las superficies de mundo: la del estilo (CFG.luz), estilizada para que las caras de un edificio se separen
const LUZ_DIR = (() => { const az = CFG.luz.azimut * Math.PI / 180, el = CFG.luz.elevacion * Math.PI / 180;
  return new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)); })();
function sombra(nx, ny, nz) {        // factor de luz de una cara con normal (nx, ny, nz) en three (y arriba)
  const lam = Math.max(0, nx * LUZ_DIR.x + ny * LUZ_DIR.y + nz * LUZ_DIR.z);
  if (ES.modo === 2) return lam < 0.22 ? 0.62 : lam < 0.62 ? 0.82 : 1.0;      // contorno: tres tonos
  return 0.5 + 0.62 * lam;
}
const malla = {
  // un acumulador: posiciones, colores e índices; `geometria(acc)` lo vuelve BufferGeometry
  nueva: () => ({ pos: [], col: [], idx: [] }),
  // una banda de `ancho` (unidades) a lo largo de pts [[x, y], …], densificada cada ≤ `paso` y posada sobre el suelo + lev
  banda(acc, pts, ancho, lev, paso, color) {
    const d = [];
    for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), k = Math.max(1, Math.ceil(L / paso));
      for (let j = 0; j < k; j++) d.push([a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k]); }
    d.push(pts[pts.length - 1]);
    if (d.length < 2) return;
    const base = acc.pos.length / 3, h = ancho / 2;
    for (let i = 0; i < d.length; i++) {
      const a = d[Math.max(0, i - 1)], b = d[Math.min(d.length - 1, i + 1)], L = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      const nx = -(b[1] - a[1]) / L * h, ny = (b[0] - a[0]) / L * h, [x, y] = d[i];
      for (const s of [1, -1]) { const px = x + nx * s, py = y + ny * s; acc.pos.push(px, ctx.altura(px, py) + lev, -py); acc.col.push(color.r, color.g, color.b); }
      if (i) { const q = base + 2 * i; acc.idx.push(q - 2, q - 1, q, q - 1, q + 1, q); }
    }
  },
  // un polígono [x0, y0, x1, y1, …] relleno, posado sobre el suelo + lev (cada vértice a su altura)
  poligono(acc, flat, lev, color) {
    const pts = []; for (let i = 0; i + 1 < flat.length; i += 2) pts.push(new THREE.Vector2(flat[i], flat[i + 1]));
    if (pts.length < 3) return;
    if (THREE.ShapeUtils.isClockWise(pts)) pts.reverse();
    const base = acc.pos.length / 3;
    for (const p of pts) { acc.pos.push(p.x, ctx.altura(p.x, p.y) + lev, -p.y); acc.col.push(color.r, color.g, color.b); }
    for (const t of THREE.ShapeUtils.triangulateShape(pts, [])) acc.idx.push(base + t[0], base + t[1], base + t[2]);
  },
  geometria(acc) {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(acc.pos), 3));
    g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(acc.col), 3));
    g.setIndex(acc.pos.length / 3 > 65535 ? new THREE.BufferAttribute(new Uint32Array(acc.idx), 1) : new THREE.BufferAttribute(new Uint16Array(acc.idx), 1));
    return g;
  },
  // material de superficie: color por vértice × uBrillo, con niebla y el grano del estilo; alfa < 1 = transparente.
  // desfase: polygonOffset (lo de encima del suelo gana sin subirlo de más)
  material({ alfa = 1, orden = 0, desfase = 0, aditivo = false } = {}) {
    return new THREE.ShaderMaterial({ uniforms: { ...uComun(), uBrillo: { value: 1 }, uAlfa: { value: alfa }, cTinte: { value: new THREE.Color(0, 0, 0) }, uTinte: { value: 0 } },
      transparent: alfa < 1 || aditivo, depthWrite: alfa >= 1 && !aditivo, side: THREE.DoubleSide, blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
      polygonOffset: desfase !== 0, polygonOffsetFactor: -desfase, polygonOffsetUnits: -desfase * 2,
      vertexShader: "attribute vec3 color; varying vec3 vCol, vPos; void main(){ vCol = color; vPos = (modelMatrix * vec4(position, 1.0)).xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: GLSL_COMUN + "uniform float uBrillo, uAlfa, uTinte; uniform vec3 cTinte; varying vec3 vCol, vPos;" +
        "void main(){ vec3 c = mix(vCol, cTinte, uTinte) * uBrillo; gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), uAlfa); }" });
  },
  // una malla lista en la escena
  poner(acc, mat, orden = 0) { const m = new THREE.Mesh(malla.geometria(acc), mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m); return m; },
};

// ---------- cámara: la función del contrato (cada parámetro con e = −(cos(πu) − 1)/2 entre claves) ----------
// `dist` en unidades de la escena (pais: dist_km; ciudad y esquema: dist_m); cerca, lejos y niebla, por mundo (MU.camara)
const CL = M.camara;
function camaraEn(t) {
  let i = 0; while (i < CL.length - 2 && t > CL[i + 1].t) i++;
  const a = CL[i], b = CL[Math.min(i + 1, CL.length - 1)];
  const u = b.t > a.t ? clamp((t - a.t) / (b.t - a.t)) : 0, e = -(Math.cos(Math.PI * u) - 1) / 2;
  const L = (k) => a[k] + (b[k] - a[k]) * e;
  return { x: L("x"), y: L("y"), alt: L("alt"), dist: L("dist"), az: L("azimut"), el: L("elevacion"), fov: L("fov") };
}
let CAM = null;
function ponerCamara(t) {
  const c = CAM = camaraEn(t), az = c.az * Math.PI / 180, el = c.el * Math.PI / 180, hd = c.dist * Math.cos(el);
  const CN = MU.camara;
  camera.fov = c.fov; camera.near = Math.max(CN.cerca, c.dist * 0.02); camera.far = CN.lejos; camera.updateProjectionMatrix();
  NIEBLA.set(Math.max(CN.niebla[0], c.dist * CN.niebla[1]), Math.max(CN.niebla[2], c.dist * CN.niebla[3]));
  camera.position.set(c.x + Math.sin(az) * hd, c.alt + c.dist * Math.sin(el), -(c.y - Math.cos(az) * hd));
  camera.up.set(0, 1, 0); camera.lookAt(c.x, c.alt, -c.y); camera.updateMatrixWorld(true);
}

// ---------- el vocabulario: registro de módulos ----------
// Cada módulo (video/maqueta/<clase>/<tipo>.js) se registra solo en window.MAQ.<PIEZAS|EVENTOS|OBJETOS|MUNDOS>[tipo]:
//   pieza:  { orden, armar(ctx, lista) → estado, inicio(t, estado, ctx), en(t, estado, ctx) }                  (todo opcional)
//   evento: { orden, armar(ctx, lista) → estado, inicio(t, estado, ctx), aplicar(t, e, ctx, estado), en(t, estado, ctx) }
//   mundo:  { async cargar(ctx) → estado, armar(ctx, estado), en(t, estado, ctx) }   (UNO por maqueta: MU.escala)
// `lista`: las piezas (o los eventos) de ese tipo, en el orden del maqueta.json. Los OBJETOS los usan las piezas
// (ctx.MAQ.OBJETOS[id]); el núcleo no los recorre.
const MAQ = window.MAQ = window.MAQ || {};
for (const k of ["PIEZAS", "EVENTOS", "OBJETOS", "MUNDOS"]) MAQ[k] = MAQ[k] || {};
const EV = M.eventos;
for (const e of EV) if (e.adelanto) { e.t -= e.adelanto; e.dur += e.adelanto; }   // como si ya llevara ese avance
for (const p of M.piezas) if (!MAQ.PIEZAS[p.tipo]) throw new Error("pieza sin módulo: " + p.tipo + " (video/maqueta/piezas/" + p.tipo + ".js)");
for (const e of EV) if (!MAQ.EVENTOS[e.tipo] || !MAQ.EVENTOS[e.tipo].aplicar) throw new Error("evento sin módulo: " + e.tipo + " (video/maqueta/eventos/" + e.tipo + ".js)");
// los módulos que usa esta maqueta, en su orden de armado (empate: piezas antes que eventos, luego por tipo)
const MODS = [];
for (const [clase, reg, lista] of [["pieza", MAQ.PIEZAS, M.piezas], ["evento", MAQ.EVENTOS, EV]]) {
  for (const tipo of [...new Set(lista.map((o) => o.tipo))]) MODS.push({ clase, tipo, def: reg[tipo], lista: lista.filter((o) => o.tipo === tipo), estado: null });
}
MODS.sort((a, b) => (a.def.orden || 0) - (b.def.orden || 0) || (a.clase === b.clase ? 0 : a.clase === "pieza" ? -1 : 1) || (a.tipo < b.tipo ? -1 : a.tipo > b.tipo ? 1 : 0));
const ESTADO_EV = {};

// lo que el núcleo comparte con los módulos (lo de un cuadro va en ctx.cuadro)
const ctx = {
  THREE, M, MAQ, W, H, COL, CFG, ES, EXAG,
  lin, clamp, suave, hash,
  scene, renderer, camera,
  // el MUNDO (lo pone su módulo en cargar): altura(x, y) → unidades de la escena (ya exagerada) · geo(lon, lat) → [x, y]
  // (pais y ciudad; null en esquema) · km = geo (nombre de antes). Lo que el resolver ya trae: unidad_m (metros por
  // unidad), caja [x0, y0, x1, y1], caminos {nombre: [[x, y, s, 0], …]} y lugares {id: {x, y, nombre}}
  altura: null, geo: null, km: null, V3,                         // V3(x, y, lev) → Vector3 sobre el suelo
  escala: MU.escala, unidad_m: MU.unidad_m, metros: (v) => v / MU.unidad_m,   // metros reales → unidades de la escena
  caja: MU.caja, caminos: MU.caminos || {}, lugares: MU.lugares || {},
  camino: (nombre) => (MU.caminos || {})[nombre] || null,
  enCamino: (nombre, s) => enCadena(ctx.camino(nombre), s),      // {x, y, dx, dy}: el punto a s de su inicio y hacia dónde va
  puntoEnS, distCadena,
  GLSL_COMUN, VERT_CINTA, uComun,                                // (el mundo pais añade NR, NC, NO, GLSL_RUPTURA, uRuptura, superficie)
  geoCinta, pegar, cinta: cintaSimple,
  tonos: TONOS, sombra, malla,                                   // superficies de mundo (ciudad, esquema): colores, luz y geometría
  linea: (id, cn) => { LINEAS[id] = cn; },                       // una cinta que «resaltar» sube por el id de su pieza
  fallas: [], idxFalla: () => -1,                                // los pone piezas/falla.js (la superficie y voxel los leen)
  luces: [],                                                     // los pone piezas/luces.js: [{x, y, peso, id, pieza, on, ac, v}]
  proyectar: null,                                               // (x, y, z) → [px, py] | null (la misma que recibe la capa 2D)
  cuadro: null,                                                  // {t, k, pxKm, dist, dist_km, brillo, elementos, ondas, rupturas}: se rehace en cada cuadro
};
let MUNDO_EST = null;
function armarVocabulario() {
  for (const m of MODS) {
    m.estado = m.def.armar ? m.def.armar(ctx, m.lista) : null;
    if (m.clase === "evento") ESTADO_EV[m.tipo] = m.estado;
  }
}

// ---------- el estado del mundo en t ----------
function mundoEn(t) {
  const c = CAM, pxKm = H / (2 * Math.tan(c.fov * Math.PI / 360));   // px por unidad a 1 unidad de distancia
  const dk = c.dist * MU.km;                                         // la distancia en km (pais: la misma)
  const k = clamp(1 + 70 / dk, 1, 2.4);                              // las líneas engordan al acercarse
  // brillo: id de pieza → factor (resaltar) · elementos: id de pieza → [{x, y, k}] (resaltar con `elemento`: un edificio,
  // una calle) · ondas: [{x, y, pieza, r, k}] · rupturas: las que ya empezaron (voxel)
  ctx.cuadro = { t, k, pxKm, dist: c.dist, dist_km: dk, brillo: {}, elementos: {}, ondas: [], rupturas: [] };
  for (const m of MODS) if (m.def.inicio) m.def.inicio(t, m.estado, ctx);
  for (const e of EV) MAQ.EVENTOS[e.tipo].aplicar(t, e, ctx, ESTADO_EV[e.tipo]);
  for (const m of MODS) if (m.def.en) m.def.en(t, m.estado, ctx);
  const brillo = ctx.cuadro.brillo;
  for (const cn of cintas) cn.mat.uniforms.uAncho.value = cn.base * clamp(1 + 30 / dk, 1, 1.8);
  for (const id in LINEAS) LINEAS[id].mat.uniforms.uAlfa.value = Math.min(1, LINEAS[id].alfa * (brillo[id] || 1) * (brillo[id] ? 1.3 : 1));
  if (MUNDO.en) MUNDO.en(t, MUNDO_EST, ctx);                       // el mundo, al final (voxel: la falla y las ondas tiñen los cubos)
}

// ---------- cuadro ----------
const _v = new THREE.Vector3();
// proyección de un punto del mundo (unidades de la escena, con su altura ya exagerada) → píxeles; null si queda detrás de la cámara
function proyectar(x, y, z) {
  _v.set(x, z, -y).applyMatrix4(camera.matrixWorldInverse);
  if (_v.z > -camera.near) return null;
  _v.set(x, z, -y).project(camera);
  return [(_v.x + 1) / 2 * W, (1 - _v.y) / 2 * H];
}
ctx.proyectar = proyectar;
function renderAt(t) {
  ponerCamara(t);
  mundoEn(t);
  renderer.render(scene, camera);
  if (window.__capa) window.__capa(t, proyectar);
}

// ---------- contrato HyperFrames ----------
window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};
window.__hf.buildReady["maqueta"] = (async () => {
  const [est] = await Promise.all([MUNDO.cargar ? MUNDO.cargar(ctx) : null, ...(window.__capaFuentes || []).map((f) => document.fonts.load(f))]);
  MUNDO_EST = est;
  await document.fonts.ready;
  if (MUNDO.armar) MUNDO.armar(ctx, MUNDO_EST);
  armarVocabulario();
  ponerCamara(0);
  await renderer.compileAsync(scene, camera);
  renderAt(0);
  const px = new Uint8Array(4), gl = renderer.getContext(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);   // termina el primer cuadro
  window.__maquetaLista = true;
})();
window.addEventListener("hf-seek", (e) => { if (window.__maquetaLista) renderAt(e.detail.time); });
window.__renderAt = renderAt;
