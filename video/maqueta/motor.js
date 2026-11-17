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
  dia:      { modo: 0, cubos: false, aditivo: false, dia: true },   // escena de cerca de día: cielo, sol y sombra de contacto
};
if (!ESTILOS[M.estilo]) throw new Error("estilo sin motor three: " + M.estilo);
// LA HORA (mundo.hora: amanecer | dia | atardecer | noche, sobre un estilo con `horas`; scripts/maqueta3d.py la resuelve en
// CFG): el cielo, de dónde viene la luz, el tinte de todo lo que no emite luz, las luces encendidas y las estrellas.
// ES.noche = «es de noche: las luces están encendidas» (el estilo noche, o la hora noche de un estilo de día). Un módulo
// pregunta ES.noche para encender ventanas y faros, y ES.modo === 1 solo para elegir la paleta del estilo noche.
const ES = Object.assign({}, ESTILOS[M.estilo], { noche: ESTILOS[M.estilo].modo === 1 || !!CFG.noche, hora: CFG.hora || (ESTILOS[M.estilo].modo === 1 ? "noche" : "dia") });

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
  uniform float uT;                                      // el segundo del cuadro
  float ruido2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);   // ruido suave (valor) de 2D
    float a = fract(sin(dot(i, vec2(127.1, 311.7))) * 43758.5453), b = fract(sin(dot(i + vec2(1.0, 0.0), vec2(127.1, 311.7))) * 43758.5453);
    float c = fract(sin(dot(i + vec2(0.0, 1.0), vec2(127.1, 311.7))) * 43758.5453), d = fract(sin(dot(i + vec2(1.0, 1.0), vec2(127.1, 311.7))) * 43758.5453);
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y); }
  uniform vec3 uHora;                                    // la hora: el color de la luz sobre todo lo que no emite (blanco de día)
  uniform sampler2D tSombra; uniform mat4 uSombraM; uniform float uSombraK, uSombraTx, uSombraTxW, uVolumen; uniform vec3 uLuzW;
  // la normal de la cara en pos, sacada de las derivadas (sin atributos) y vuelta hacia la cámara; cero en un punto sin cara
  vec3 caraN(vec3 pos) {
    vec3 dn = cross(dFdx(pos), dFdy(pos)); float ln = length(dn);
    if (ln < 1e-12) return vec3(0.0);
    vec3 n = dn / ln; return dot(n, cameraPosition - pos) < 0.0 ? -n : n;
  }
  // cuánta sombra cae en pos (0–1): la normal de la cara sale de las derivadas (sin atributos), así solo se oscurecen
  // las caras que miran a la luz (las otras ya vienen oscuras de su sombreado) y se corre el punto para no sombrearse sola
  float enSombra(vec3 pos, vec3 n) {
    if (uSombraK <= 0.0 || dot(n, n) < 0.5) return 0.0;          // un punto (un halo, una luz): sin cara, sin sombra
    float lam = dot(n, uLuzW);
    // el punto se corre por su normal (más cuanto más rasante le da la luz) y un poco hacia la luz: sin rayas en las caras
    vec4 q = uSombraM * vec4(pos + n * uSombraTxW * (1.5 + 3.0 * (1.0 - clamp(lam, 0.0, 1.0))) + uLuzW * uSombraTxW * 1.0, 1.0);
    vec3 p = q.xyz / q.w * 0.5 + 0.5;
    if (p.x < 0.002 || p.x > 0.998 || p.y < 0.002 || p.y > 0.998 || p.z > 1.0) return 0.0;
    float bias = 0.0006, s = 0.0;
    for (int i = -1; i <= 1; i++) for (int j = -1; j <= 1; j++)
      s += step(texture2D(tSombra, p.xy + vec2(float(i), float(j)) * uSombraTx * 1.3).r, p.z - bias);
    float borde = smoothstep(0.0, 0.06, min(min(p.x, 1.0 - p.x), min(p.y, 1.0 - p.y)));   // se desvanece en la orilla del mapa
    return s / 9.0 * smoothstep(0.08, 0.35, lam) * borde;
  }
  // LUZ CON VOLUMEN (uVolumen): el cielo alumbra lo que mira hacia arriba y lo que mira al suelo queda más oscuro
  vec3 niebla(vec3 c, vec3 pos, vec2 frag) {
    float luz = 1.0;
    if (uSombraK > 0.0 || uVolumen > 0.0) { vec3 n = caraN(pos);
      luz = (1.0 - uSombraK * enSombra(pos, n)) * (1.0 + uVolumen * (n.y * 0.5 - 0.16) * step(0.5, dot(n, n))); }
    return mix(c * uHora * luz, fondoEn(frag), smoothstep(uNiebla.x, uNiebla.y, distance(pos, cameraPosition)));
  }
  vec3 salida(vec3 c, vec2 frag) {   // lineal → sRGB + grano fijo
    c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));
    return c + (ruido(frag) - 0.5) * uGrano;
  }`;
const NIEBLA = new THREE.Vector2(3000, 9000);
// SOMBRAS REALES (estilos con cfg.sombras, en mundos de cerca): un mapa de profundidad desde la luz, que TODAS las
// superficies leen en niebla() (GLSL_COMUN), sin tocar los módulos. Estos uniformes se comparten (la misma referencia en
// cada material) y se llenan más abajo, cuando existen la luz y la cámara.
const U_SOMBRA = { tSombra: { value: null }, uSombraM: { value: new THREE.Matrix4() }, uSombraK: { value: 0 }, uLuzW: { value: new THREE.Vector3(0, 1, 0) }, uSombraTx: { value: 1 / 2048 }, uSombraTxW: { value: 0.1 }, uVolumen: { value: 0 } };
const UT = { value: 0 };   // el segundo del cuadro, para lo que se mueve solo en un shader (las nubes, el brillo del agua): función pura de t
const TINTE = (() => { const t = CFG.tinte || [1, 1, 1]; return new THREE.Vector3(t[0], t[1], t[2]); })();
const uComun = () => ({ cFondo: { value: lin(COL.fondo) }, cFondo2: { value: lin(COL.fondo2) }, uRes: { value: RES }, uGrano: { value: CFG.grano }, uNiebla: { value: NIEBLA }, uHora: { value: TINTE }, uT: UT, ...U_SOMBRA });

// fondo: un triángulo a pantalla completa (degradado del estilo + grano)
{
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
  // de noche (CFG.estrellas): estrellas fijas en la mitad alta del cielo (un punto por celda, por su hash; sin parpadeo)
  // de día (CFG.nubes, 0–1): nubes que derivan despacio en la parte alta del cielo (ruido suave; puras de t)
  const m = new THREE.ShaderMaterial({ uniforms: { ...uComun(), uEstrellas: { value: CFG.estrellas ? 1 : 0 }, uNubes: { value: CFG.nubes || 0 }, cNube: { value: lin(COL.costa || COL.secundario) } }, depthTest: false, depthWrite: false,
    vertexShader: "void main(){ gl_Position = vec4(position.xy, 1.0, 1.0); }",
    fragmentShader: GLSL_COMUN + `uniform float uEstrellas, uNubes; uniform vec3 cNube;
      void main(){ vec3 c = fondoEn(gl_FragCoord.xy);
        if (uNubes > 0.0) { vec2 q = gl_FragCoord.xy / uRes.x; q.x += uT * 0.004;
          float n = ruido2(q * vec2(3.0, 7.0)) * 0.6 + ruido2(q * vec2(7.0, 15.0) + 9.0) * 0.3 + ruido2(q * vec2(15.0, 31.0) + 4.0) * 0.1;
          float alto = smoothstep(0.52, 0.8, gl_FragCoord.y / uRes.y);
          c = mix(c, cNube * uHora + c * (vec3(1.0) - uHora) * 0.4, smoothstep(0.52, 0.74, n) * alto * uNubes); }
        if (uEstrellas > 0.5) { vec2 g = gl_FragCoord.xy / 9.0; vec2 id = floor(g); float h = ruido(id * 9.0 + 3.0);
          vec2 o = vec2(ruido(id * 9.0 + 17.0), ruido(id * 9.0 + 41.0)) * 0.7 + 0.15;
          float d = length(fract(g) - o), alto = smoothstep(0.45, 0.95, gl_FragCoord.y / uRes.y);
          c += vec3(0.9, 0.92, 1.0) * step(0.965, h) * (1.0 - smoothstep(0.04, 0.16, d)) * alto * (0.35 + 0.65 * ruido(id * 9.0 + 71.0)); }
        gl_FragColor = vec4(salida(c, gl_FragCoord.xy), 1.0); }` });
  const q = new THREE.Mesh(g, m); q.frustumCulled = false; q.renderOrder = -10; q.userData.cielo = true; scene.add(q);
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
  } else if (ES.dia) {                 // dia: la escena de cerca con luz de sol: pasto y tierra, caminos de tierra, muros claros, teja
    T.suelo = C("tierra_baja").lerp(C("tierra_media"), 0.22); T.verde = C("tierra_baja");
    T.calle = C("tierra_media").lerp(C("costa"), 0.3); T.calle_mayor = C("linea").lerp(C("costa"), 0.55);
    T.muro = C("costa").lerp(C("tierra_alta"), 0.18); T.techo = C("mal").lerp(C("tierra_media"), 0.45);
    T.asfalto = C("linea").lerp(C("costa"), 0.35); T.raya = C("costa"); T.central = C("luces"); T.borde = C("costa");
    T.agua = C("mar"); T.arena = C("tierra_alta").lerp(C("costa"), 0.4); T.pavimento = C("costa").lerp(C("linea"), 0.25);
    T.campo = C("tierra_baja"); T.campo2 = C("tierra_baja").lerp(C("tierra_media"), 0.4);
  } else {                             // color, contorno, voxel: suelo claro, calles más claras, edificios de papel
    T.suelo = C("tierra_media").lerp(C("fondo"), 0.62); T.verde = C("tierra_baja");
    T.calle = C("fondo").lerp(C("costa"), 0.6); T.calle_mayor = C("costa");
    T.muro = C("fondo").lerp(C("linea"), 0.1); T.techo = C("fondo").lerp(C("costa"), 0.6);
    T.asfalto = C("linea").lerp(C("fondo"), 0.3); T.raya = C("costa"); T.central = C("luces"); T.borde = C("costa");
    T.agua = C("mar"); T.arena = C("tierra_media").lerp(C("costa"), 0.45); T.pavimento = T.suelo.clone().lerp(C("costa"), 0.4);
    T.campo = C("tierra_baja"); T.campo2 = C("tierra_baja").lerp(C("tierra_media"), 0.55);
  }
  T.acento = C("acento"); T.secundario = C("secundario"); T.linea = C("linea");
  // el estado de una vía (trazo: bien · medio · mal): colores del estilo (estilos.json); sin ellos, del acento y el texto
  T.bien = COL.bien ? C("bien") : C("secundario"); T.medio = COL.medio ? C("medio") : C("luces"); T.mal = COL.mal ? C("mal") : C("acento");
  // carrocerías de los objetos que se mueven (variantes por semilla): claras sobre la noche, de tinta sobre los fondos claros
  T.vehiculos = ES.modo === 1 || ES.modo === 4
    ? [T.secundario.clone().multiplyScalar(0.8), T.techo.clone().multiplyScalar(1.25), C("costa"), C("tierra_alta").multiplyScalar(0.8), T.secundario.clone().multiplyScalar(0.5)]
    : [T.linea.clone().lerp(C("fondo"), 0.25), C("costa").multiplyScalar(0.8), C("tierra_baja"), T.linea.clone().lerp(C("costa"), 0.5), C("fondo").multiplyScalar(0.9)];
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
      for (const s of [1, -1]) { const px = x + nx * s, py = y + ny * s; acc.pos.push(px, ctx.suelo(px, py) + lev, -py); acc.col.push(color.r, color.g, color.b); }
      if (i) { const q = base + 2 * i; acc.idx.push(q - 2, q - 1, q, q - 1, q + 1, q); }
    }
  },
  // un polígono [x0, y0, x1, y1, …] relleno, posado sobre el suelo DEL MUNDO + lev (cada vértice a su altura). Las superficies
  // (banda y polígono: suelos, calles, zonas, agua) no siguen el relieve de una pieza: son triángulos grandes y saldrían como losas
  poligono(acc, flat, lev, color) {
    const pts = []; for (let i = 0; i + 1 < flat.length; i += 2) pts.push(new THREE.Vector2(flat[i], flat[i + 1]));
    if (pts.length < 3) return;
    if (THREE.ShapeUtils.isClockWise(pts)) pts.reverse();
    const base = acc.pos.length / 3;
    for (const p of pts) { acc.pos.push(p.x, ctx.suelo(p.x, p.y) + lev, -p.y); acc.col.push(color.r, color.g, color.b); }
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

// ---------- el RELIEVE DE PIEZA (MAQUETA.mundo.alturas; el mismo cálculo que scripts/maqueta_tipos/_relieve.py) ----------
// Lo que una pieza le suma al suelo del mundo (un camino que sube, una ladera sembrada, una plataforma): desde que el mundo
// carga, ctx.altura = el suelo del mundo (ctx.suelo) + el campo más alto que cubre el punto. Lo pisan la flota (que además
// inclina con la pendiente los objetos que `cabecea`n: los vehículos), la cámara que mira o sigue, las marcas y las anotaciones.
const CAMPOS = MU.alturas || [];
const dentroPol = (pol, x, y) => { let c = false; const n = pol.length >> 1;
  for (let i = 0; i < n; i++) { const j = (i + 1) % n, ax = pol[2 * i], ay = pol[2 * i + 1], bx = pol[2 * j], by = pol[2 * j + 1];
    if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / ((by - ay) || 1e-9) + ax) c = !c; }
  return c; };
function campoEn(c, x, y) {                                       // la altura del campo en (x, y); null si no lo cubre
  const [x0, y0, x1, y1] = c.caja; if (x < x0 || x > x1 || y < y0 || y > y1) return null;
  if (c.tipo === "plano") return dentroPol(c.poligono, x, y) ? c.z : null;
  if (c.tipo === "malla") { if (c.poligono && !dentroPol(c.poligono, x, y)) return null;
    const fx = (x - x0) / ((x1 - x0) || 1e-9) * (c.nx - 1), fy = (y - y0) / ((y1 - y0) || 1e-9) * (c.ny - 1);
    const i = Math.min(c.nx - 2, Math.max(0, Math.floor(fx))), j = Math.min(c.ny - 2, Math.max(0, Math.floor(fy))), u = fx - i, v = fy - j, z = c.z, k = j * c.nx + i;
    return (z[k] * (1 - u) + z[k + 1] * u) * (1 - v) + (z[k + c.nx] * (1 - u) + z[k + c.nx + 1] * u) * v; }
  if (c.tipo === "perfil") { let mejor = Infinity, zm = null; const P = c.puntos;
    for (let i = 0; i + 1 < P.length; i++) { const a = P[i], b = P[i + 1], dx = b[0] - a[0], dy = b[1] - a[1];
      const h = Math.min(1, Math.max(0, ((x - a[0]) * dx + (y - a[1]) * dy) / ((dx * dx + dy * dy) || 1e-9))), d = Math.hypot(x - a[0] - dx * h, y - a[1] - dy * h);
      if (d < mejor) { mejor = d; zm = a[2] + (b[2] - a[2]) * h; } }
    return mejor <= c.ancho ? zm : null; }
  return null;
}
function relieve(x, y) { let h = null; for (const c of CAMPOS) { const v = campoEn(c, x, y); if (v !== null && (h === null || v > h)) h = v; } return h || 0; }

// ---------- lo que se mueve (piezas actor y flujo): trayectorias, móviles y la flota de objetos ----------
// Una trayectoria es s(t) lineal por tramos (T, S: la calcula scripts/maqueta_tipos/_movimiento.py, que también la usan
// los gates); aquí solo se EVALÚA, suavizada con una ventana de ±h s: s̄(t) = (F(t+h) − F(t−h)) / 2h con F = ∫ s dt (forma
// cerrada, seek puro). Fuera de [T0, Tn] sigue con la pendiente del extremo. El mismo cálculo que _movimiento.suave.
const tray = {
  nueva(T, S) { const F = [0]; for (let k = 0; k + 1 < T.length; k++) F.push(F[k] + (S[k] + S[k + 1]) / 2 * (T[k + 1] - T[k])); return { T, S, F }; },
  _k(T, t) { let lo = 0, hi = T.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (T[m] <= t) lo = m; else hi = m; } return lo; },
  _v(r, k) { const { T, S } = r; return T[k + 1] > T[k] ? (S[k + 1] - S[k]) / (T[k + 1] - T[k]) : 0; },
  pos(r, t) { const { T, S } = r, n = T.length; if (n === 1) return S[0];
    if (t <= T[0]) return S[0] + tray._v(r, 0) * (t - T[0]);
    if (t >= T[n - 1]) return S[n - 1] + tray._v(r, n - 2) * (t - T[n - 1]);
    const k = Math.min(n - 2, tray._k(T, t)); return S[k] + tray._v(r, k) * (t - T[k]); },
  _F(r, t) { const { T, S, F } = r, n = T.length; if (n === 1) return S[0] * (t - T[0]);
    let d; if (t <= T[0]) { d = t - T[0]; const v = tray._v(r, 0); return S[0] * d + v * d * d / 2; }
    if (t >= T[n - 1]) { d = t - T[n - 1]; const v = tray._v(r, n - 2); return F[n - 1] + S[n - 1] * d + v * d * d / 2; }
    const k = Math.min(n - 2, tray._k(T, t)); d = t - T[k]; const v = tray._v(r, k); return F[k] + S[k] * d + v * d * d / 2; },
  // [s̄, v̄] en t (h: media ventana en s; 0 = sin suavizar)
  suave(r, h, t) { if (h <= 0) { const n = r.T.length, k = n > 1 ? Math.max(0, Math.min(n - 2, tray._k(r.T, t))) : 0; return [tray.pos(r, t), n > 1 ? tray._v(r, k) : 0]; }
    return [(tray._F(r, t + h) - tray._F(r, t - h)) / (2 * h), (tray.pos(r, t + h) - tray.pos(r, t - h)) / (2 * h)]; },
};
// los móviles: id de pieza → (t, n) → {x, y, dx, dy, v, vis} (los registran actor y flujo en su armar; los leen la cámara que
// sigue y las anotaciones). Un ancla resuelta es {x, y} (fija) o {movil, n, desfase: [adelante, izquierda], lev}
const MOVILES = {};
function anclaEn(A, t) {
  if (A.movil === undefined) return { x: A.x, y: A.y, dx: 1, dy: 0, v: 0, vis: true, lev: 0 };
  const m = MOVILES[A.movil]; if (!m) throw new Error("ancla sin móvil: " + A.movil);
  const q = m(t, A.n || 0), d = A.desfase || [0, 0];
  return { x: q.x + q.dx * d[0] - q.dy * d[1], y: q.y + q.dy * d[0] + q.dx * d[1], dx: q.dx, dy: q.dy, v: q.v, vis: q.vis, lev: A.lev || 0 };
}

// la FLOTA: n objetos de un tipo (video/maqueta/objetos/<tipo>.js) en una InstancedMesh (una malla para todos), con la luz
// del estilo calculada en el shader (el objeto gira), su color por instancia (las partes con `tinte`) y, de noche, sus luces:
// faros (puntos cálidos y un cono tenue en el suelo) y pilotos (que se avivan al frenar). Cada cuadro: poner(i, …) → listo().
// El objeto da sus partes en METROS (x adelante, y arriba, z a su derecha); aquí se escalan a la unidad de la escena.
const VERT_OBJ = `attribute vec3 color; attribute float aTinte, aLuz, aTinte2; attribute float aBr; attribute vec3 aColor2; uniform vec3 uLuz; uniform float uModo; varying vec3 vCol, vPos; varying float vLuz;
  void main(){ mat4 im = mat4(1.0);
    #ifdef USE_INSTANCING
      im = instanceMatrix;
    #endif
    vec3 n = normalize(mat3(modelMatrix * im) * normal); float lam = max(0.0, dot(n, uLuz));
    float s = (uModo > 1.5 && uModo < 2.5) ? (lam < 0.22 ? 0.62 : (lam < 0.62 ? 0.82 : 1.0)) : 0.5 + 0.62 * lam;
    vec3 c = color;
    #ifdef USE_INSTANCING_COLOR
      c = mix(c, c * instanceColor, aTinte);
      c = mix(c, c * aColor2, aTinte2);          // el segundo color de la instancia (partes con tinte2: el toldo aparte de la fachada)
    #endif
    vCol = mix(c * s, c * 1.25 * aBr, aLuz); vLuz = aLuz;   // aBr: el brillo de lo que emite, por instancia y grupo (una vitrina que titila)
    vec4 wp = modelMatrix * im * vec4(position, 1.0); vPos = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`;
// lo que emite luz (aLuz: ventanas, faros, pantallas) no se tiñe con la hora: de noche es lo que brilla
const FRAG_OBJ = GLSL_COMUN + "uniform float uBrillo; varying vec3 vCol, vPos; varying float vLuz; void main(){ vec3 c = vCol * uBrillo; c *= mix(vec3(1.0), vec3(1.0) / max(uHora, vec3(0.05)), clamp(vLuz, 0.0, 1.0)); gl_FragColor = vec4(salida(niebla(c, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }";
const SRGB = "c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));";
function geoObjeto(partes) {           // las partes [{geo, color, tinte, luz}] → una geometría no indexada con color, aTinte y aLuz
  const pos = [], nor = [], col = [], tin = [], luz = [], tin2 = [];
  for (const p of partes) {
    const g = p.geo.index ? p.geo.toNonIndexed() : p.geo; g.computeVertexNormals();
    const P = g.attributes.position.array, N = g.attributes.normal.array;
    for (let i = 0; i < P.length; i += 3) { pos.push(P[i], P[i + 1], P[i + 2]); nor.push(N[i], N[i + 1], N[i + 2]);
      col.push(p.color.r, p.color.g, p.color.b); tin.push(p.tinte ? 1 : 0); luz.push(p.luz || 0); tin2.push(p.tinte2 ? 1 : 0); }
  }
  const g = new THREE.BufferGeometry(), F = (a, k) => new THREE.BufferAttribute(new Float32Array(a), k);
  g.setAttribute("position", F(pos, 3)); g.setAttribute("normal", F(nor, 3)); g.setAttribute("color", F(col, 3));
  g.setAttribute("aTinte", F(tin, 1)); g.setAttribute("aLuz", F(luz, 1)); g.setAttribute("aTinte2", F(tin2, 1));
  return g;
}
function flota(tipo, n, op = {}) {
  const O = MAQ.OBJETOS[tipo];
  if (!O) throw new Error("objeto sin módulo: " + tipo + " (video/maqueta/objetos/" + tipo + ".js)");
  const um = 1 / MU.unidad_m, tam = op.tamano || 1, k0 = tam * um, N1 = Math.max(1, n);
  const mat = new THREE.ShaderMaterial({ uniforms: { ...uComun(), uLuz: { value: LUZ_DIR.clone().normalize() }, uModo: { value: ES.modo }, uBrillo: { value: 1 } },
    vertexShader: VERT_OBJ, fragmentShader: FRAG_OBJ });
  // OBJETO ARTICULADO (2026-11-16): las partes con `grupo` forman piezas que se mueven solas con el tiempo (un brazo que
  // cosecha, una pierna que camina, el brazo de una grúa, el tambor de una tostadora). El objeto declara
  // `grupos: {nombre: {pivote: [x, y, z]}}` (metros, ejes del objeto) y `pose(t, i, ctx)` → {nombre: [rx, ry, rz, dx?, dy?, dz?]}
  // (radianes alrededor de su pivote y metros), función pura de t: cada grupo es otra InstancedMesh con la misma instancia.
  // `op.adjuntos`: partes de más que la pieza le pone al objeto, atadas a uno de sus grupos (la herramienta en la mano: un
  // rastrillo en `brazo_d`): [{geo, color, grupo, luz?}] en metros, en los ejes del objeto. `op.pose`: el nombre de la pose
  // que la pieza pide (o i → nombre): el objeto la recibe en pose(t, i, ctx, {vel, pose}).
  const todas = O.partes(ctx).concat(op.adjuntos || []), GR = O.grupos || {};
  const mallas = [["", todas.filter((p) => !p.grupo || !GR[p.grupo])]].concat(Object.keys(GR).map((g) => [g, todas.filter((p) => p.grupo === g)]))
    .filter(([, ps]) => ps.length).map(([g, ps]) => {
      const geo = geoObjeto(ps);
      geo.setAttribute("aBr", new THREE.InstancedBufferAttribute(new Float32Array(N1).fill(1), 1));
      geo.setAttribute("aColor2", new THREE.InstancedBufferAttribute(new Float32Array(N1 * 3).fill(1), 3));
      const m = new THREE.InstancedMesh(geo, mat, N1); m.frustumCulled = false; m.renderOrder = op.orden || 3; return [g, m]; });
  const im = mallas[0][1];
  const variantes = O.variantes ? O.variantes(ctx) : [TONOS.secundario];
  const variantes2 = O.variantes2 ? O.variantes2(ctx) : null;     // el segundo color (partes con `tinte2`), por instancia
  const cero = new THREE.Matrix4().makeScale(0, 0, 0);
  for (const [, m] of mallas) {
    for (let i = 0; i < N1; i++) { m.setColorAt(i, op.color ? op.color(i, variantes) : variantes[0]); m.setMatrixAt(i, cero);
      if (variantes2) { const c2 = op.color2 ? op.color2(i, variantes2) : variantes2[(i + (op.semilla || 0)) % variantes2.length]; m.geometry.attributes.aColor2.setXYZ(i, c2.r, c2.g, c2.b); } }
    m.instanceColor.needsUpdate = true; scene.add(m);
  }
  const mG = new THREE.Matrix4(), mP = new THREE.Matrix4(), mR = new THREE.Matrix4(), mS = new THREE.Matrix4(), eu = new THREE.Euler(), qS = new THREE.Quaternion();
  // la sombra de contacto (estilos con `sombra_contacto`): un disco suave bajo cada objeto, que lo asienta en el suelo
  let sombra = null;
  if ((CFG.sombra_contacto || 0) > 0) {
    const md = O.medidas || { largo_m: 2, ancho_m: 2 }, gs = new THREE.PlaneGeometry(1, 1); gs.rotateX(-Math.PI / 2);
    const sm = new THREE.ShaderMaterial({ uniforms: { uK: { value: CFG.sombra_contacto } }, transparent: true, depthWrite: false,
      vertexShader: "varying vec2 vUv; void main(){ vUv = uv; mat4 im = mat4(1.0);\n#ifdef USE_INSTANCING\n im = instanceMatrix;\n#endif\n gl_Position = projectionMatrix * viewMatrix * modelMatrix * im * vec4(position, 1.0); }",
      fragmentShader: "uniform float uK; varying vec2 vUv; void main(){ float r = length((vUv - 0.5) * 2.0); float a = uK * (1.0 - smoothstep(0.35, 1.0, r)); gl_FragColor = vec4(0.0, 0.0, 0.0, a); }" });
    const sh = new THREE.InstancedMesh(gs, sm, N1); sh.frustumCulled = false; sh.renderOrder = 2;
    for (let i = 0; i < N1; i++) sh.setMatrixAt(i, cero);
    scene.add(sh);
    // con el sol bajo (amanecer, atardecer) la sombra se alarga hacia donde no da la luz, según la altura del objeto
    const el = Math.max(8, Math.min(89, CFG.luz.elevacion)) * Math.PI / 180, largo = Math.min(3.2, 1 / Math.tan(el)) * (md.alto_m || 2) * 0.55;
    const hx = -LUZ_DIR.x, hz = -LUZ_DIR.z, hn = Math.hypot(hx, hz) || 1;
    sombra = { mesh: sh, l: (md.largo_m || 2) * 1.25, w: (md.ancho_m || 2) * 1.35, largo, dx: hx / hn, dz: hz / hn };
  }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Vector3(), sc = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0), k2 = new THREE.Vector3();
  // EL CABECEO: sobre el relieve de una pieza, un objeto que `cabecea` (los vehículos: su módulo lo dice) va posado en sus
  // dos ejes y se inclina con la pendiente. `op.cabeceo: false` lo quita (la pieza que ya lo inclina ella misma).
  const cabecea = CAMPOS.length > 0 && O.cabecea === true && op.cabeceo !== false, ejes = 0.35 * ((O.medidas || {}).largo_m || 2) * k0;
  const qC = new THREE.Quaternion(), Zd = new THREE.Vector3(0, 0, 1);
  // de noche: faros (cálidos) y pilotos (en el tono «mal», más vivos al frenar) como puntos, y el cono de los faros en el suelo
  let luces = null;
  if (ES.noche && op.luces !== false && (O.faros || []).length) {
    const NF = O.faros.length, NP = (O.pilotos || []).length, N = N1 * (NF + NP);
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(N), 1));
    g.setAttribute("aCol", new THREE.BufferAttribute(new Float32Array(N), 1));
    const pm = new THREE.ShaderMaterial({ uniforms: { cA: { value: lin(COL.luces) }, cB: { value: TONOS.mal }, uTam: { value: 0.9 * k0 }, uPx: { value: 1 } },
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: "attribute float aK, aCol; uniform float uTam, uPx; varying float vK, vC; void main(){ vK = aK; vC = aCol; vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aK > 0.0 ? clamp(uTam * uPx / max(1e-3, -mv.z) * 3.0, 3.5, 16.0) : 0.0; }",
      fragmentShader: "uniform vec3 cA, cB; varying float vK, vC; void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard; float a = (exp(-r * r * 9.0) + exp(-r * r * 60.0)) * vK; vec3 c = mix(cA, cB, vC); " + SRGB + " gl_FragColor = vec4(c * a, a); }" });
    const pts = new THREE.Points(g, pm); pts.frustumCulled = false; pts.renderOrder = 9; scene.add(pts);
    const gc = new THREE.PlaneGeometry(1, 1); gc.rotateX(-Math.PI / 2); gc.translate(0.5, 0, 0);   // de 0 a 1 hacia adelante
    const cm = new THREE.ShaderMaterial({ uniforms: { cA: { value: lin(COL.luces) }, uK: { value: 0.18 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: "varying vec2 vUv; void main(){ vUv = uv; mat4 im = mat4(1.0);\n#ifdef USE_INSTANCING\n im = instanceMatrix;\n#endif\n gl_Position = projectionMatrix * viewMatrix * modelMatrix * im * vec4(position, 1.0); }",
      fragmentShader: "uniform vec3 cA; uniform float uK; varying vec2 vUv; void main(){ float x = vUv.x, y = (vUv.y - 0.5) * 2.0, w = 0.2 + 0.8 * x; float a = uK * (1.0 - x) * smoothstep(0.0, 0.06, x) * exp(-pow(y / w, 2.0) * 2.5); vec3 c = cA; " + SRGB + " gl_FragColor = vec4(c * a, a); }" });
    const cono = new THREE.InstancedMesh(gc, cm, N1); cono.frustumCulled = false; cono.renderOrder = 4;
    for (let i = 0; i < N1; i++) cono.setMatrixAt(i, cero);
    scene.add(cono);
    luces = { pts, cono, NF, NP };
  }
  return {
    n: N1, mesh: im,
    // el objeto i en (x, y) mirando hacia (dx, dy), con escala k (0 = no se ve) y freno 0–1 (aviva los pilotos)
    poner(i, x, y, dx, dy, k = 1, freno = 0, vel = null) {   // vel: m/s de quien la lleva (la pose de un objeto articulado la puede usar)
      let z = altura(x, y) + (op.lev || 0) * um, sub = 0;         // sub: lo que sube por metro hacia adelante (la pendiente)
      q.setFromAxisAngle(Y, Math.atan2(dy, dx));
      if (cabecea && k > 0) { const h = ejes * k, za = altura(x + dx * h, y + dy * h), zb = altura(x - dx * h, y - dy * h);
        z = (za + zb) / 2 + (op.lev || 0) * um; sub = (za - zb) / (2 * h); q.multiply(qC.setFromAxisAngle(Zd, Math.atan(sub))); }
      e.set(x, z, -y); sc.setScalar(k0 * k);
      m4.compose(e, q, sc);
      // `op.semilla` (el actor la pasa desde su id): cada instancia de cada pieza con su propio desfase en la pose
      const pose = mallas.length > 1 && O.pose ? (O.pose((ctx.cuadro || {}).t || 0, i + (op.semilla || 0), ctx, { vel, pose: typeof op.pose === "function" ? op.pose(i) : op.pose || null }) || {}) : {};
      // cada grupo gira en su pivote; con `padre`, encima del giro de su padre (el brazo sigue al torso, el codo al brazo)
      const loc = {};
      const local = (g) => {
        if (loc[g]) return loc[g];
        const r = pose[g] || [0, 0, 0], pv = GR[g].pivote || [0, 0, 0], L = new THREE.Matrix4();
        mP.makeTranslation(pv[0] + (r[3] || 0), pv[1] + (r[4] || 0), pv[2] + (r[5] || 0));
        mR.makeRotationFromEuler(eu.set(r[0] || 0, r[1] || 0, r[2] || 0));
        if (r[6] !== undefined && r[6] !== null) mR.multiply(mS.makeScale(Math.max(0, r[6]), Math.max(0, r[6]), Math.max(0, r[6])));   // 7.º valor: escala (0 = no se ve)
        L.copy(mP).multiply(mR).multiply(mP.makeTranslation(-pv[0], -pv[1], -pv[2]));
        const pa = GR[g].padre;
        return (loc[g] = pa && GR[pa] && pa !== g ? local(pa).clone().multiply(L) : L);
      };
      for (const [g, m] of mallas) {
        if (k <= 0) { m.setMatrixAt(i, cero); continue; }
        const br = g && pose[g] && pose[g][7] !== undefined && pose[g][7] !== null ? pose[g][7] : (pose._brillo !== undefined ? pose._brillo : 1);
        if (m.geometry.attributes.aBr.getX(i) !== br) { m.geometry.attributes.aBr.setX(i, br); m.geometry.attributes.aBr.needsUpdate = true; }
        if (!g || (!pose[g] && !GR[g].padre)) { m.setMatrixAt(i, m4); continue; }
        m.setMatrixAt(i, mG.copy(m4).multiply(local(g)));
      }
      if (sombra) { const L = sombra.largo * k0 * k;   // el disco, corrido medio largo hacia la sombra y estirado en esa dirección
        k2.set(x + sombra.dx * L * 0.5, z + 0.04 * um, -y + sombra.dz * L * 0.5);
        const base = Math.max(sombra.l, sombra.w) * k0 * k; sc.set(base + L, 1, base * 0.9);
        qS.setFromAxisAngle(Y, Math.atan2(-sombra.dz, sombra.dx));
        sombra.mesh.setMatrixAt(i, k > 0 ? mS.compose(k2, L > base * 0.15 ? qS : q, sc) : cero); sc.setScalar(k0 * k); }
      if (!luces) return;
      const A = luces.pts.geometry.attributes, base = i * (luces.NF + luces.NP);
      const pon = (j, l, kk, cc) => { const lx = l[0] * k0, ly = l[1] * k0, lz = l[2] * k0;   // local (adelante, arriba, derecha) → escena
        A.position.setXYZ(base + j, x + dx * lx + dy * lz, z + ly + lx * sub, -(y + dy * lx - dx * lz)); A.aK.setX(base + j, kk); A.aCol.setX(base + j, cc); };
      O.faros.forEach((l, j) => pon(j, l, k > 0 ? 0.85 : 0, 0));
      (O.pilotos || []).forEach((l, j) => pon(luces.NF + j, l, k > 0 ? 0.22 + 0.78 * freno : 0, 1));
      const f = O.faros[0][0] * k0;
      k2.set(x + dx * f, z + f * sub + 0.08 * um, -(y + dy * f)); sc.set(18 * k0, 1, 7 * k0);
      luces.cono.setMatrixAt(i, k > 0 ? m4.compose(k2, q, sc) : cero);
    },
    listo() {
      for (const [, m] of mallas) m.instanceMatrix.needsUpdate = true;
      if (sombra) sombra.mesh.instanceMatrix.needsUpdate = true;
      if (luces) { const A = luces.pts.geometry.attributes; A.position.needsUpdate = A.aK.needsUpdate = A.aCol.needsUpdate = true;
        luces.pts.material.uniforms.uPx.value = ctx.cuadro ? ctx.cuadro.pxKm : 1; luces.cono.instanceMatrix.needsUpdate = true; }
    },
    brillo(b) { mat.uniforms.uBrillo.value = b; },
  };
}

// ---------- cámara: la función del contrato (cada parámetro con e = −(cos(πu) − 1)/2 entre claves) ----------
// `dist` en unidades de la escena (pais: dist_km; ciudad y esquema: dist_m); cerca, lejos y niebla, por mundo (MU.camara)
const CL = M.camara;
// una clave con `sigue` (un actor o un vehículo de un flujo) mira donde está ese móvil en t (el mismo cálculo que
// maqueta3d.camara_en con la `_pos` de la clave); las demás, su punto fijo
function miraDe(k, t) {
  if (!k.sigue) return [k.x, k.y, k.alt];
  const q = anclaEn(k.sigue, t); return [q.x, q.y, altura(q.x, q.y) + (k.lev || 0)];   // lev: `mira_lev_m` de la clave
}
function camaraEn(t) {
  let i = 0; while (i < CL.length - 2 && t > CL[i + 1].t) i++;
  const a = CL[i], b = CL[Math.min(i + 1, CL.length - 1)];
  const u = b.t > a.t ? clamp((t - a.t) / (b.t - a.t)) : 0, e = -(Math.cos(Math.PI * u) - 1) / 2;
  const L = (k) => a[k] + (b[k] - a[k]) * e;
  const pa = miraDe(a, t), pb = miraDe(b, t), P = (j) => pa[j] + (pb[j] - pa[j]) * e;
  return { x: P(0), y: P(1), alt: P(2), dist: L("dist"), az: L("azimut"), el: L("elevacion"), fov: L("fov") };
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
//   mundo:  { async cargar(ctx) → estado, armar(ctx, estado), en(t, estado, ctx) }   (UNO por maqueta: MU.escala; un video con varios mundos se graba por tramos, scripts/maqueta_tramos.py)
// `lista`: las piezas (o los eventos) de ese tipo, en el orden del maqueta.json. Los OBJETOS los usan las piezas
// (ctx.MAQ.OBJETOS[id]); el núcleo no los recorre.
const MAQ = window.MAQ = window.MAQ || {};
for (const k of ["PIEZAS", "EVENTOS", "OBJETOS", "ANOTACIONES", "MUNDOS"]) MAQ[k] = MAQ[k] || {};
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
  hora: ES.hora, noche: ES.noche, luzDir: LUZ_DIR,                  // la hora del mundo; noche = luces encendidas; luzDir: de dónde viene la luz (Vector3, y arriba)
  lin, clamp, suave, hash,
  scene, renderer, camera,
  // el MUNDO (lo pone su módulo en cargar): altura(x, y) → unidades de la escena (ya exagerada) · geo(lon, lat) → [x, y]
  // (pais y ciudad; null en esquema) · km = geo (nombre de antes). Lo que el resolver ya trae: unidad_m (metros por
  // unidad), caja [x0, y0, x1, y1], caminos {nombre: [[x, y, s, 0], …]} y lugares {id: {x, y, nombre}}
  altura: null, geo: null, km: null, V3,                         // V3(x, y, lev) → Vector3 sobre el suelo
  suelo: null, relieve,                                          // suelo(x, y): el del mundo SIN el relieve de pieza (altura = suelo + relieve)
  escala: MU.escala, unidad_m: MU.unidad_m, metros: (v) => v / MU.unidad_m,   // metros reales → unidades de la escena
  caja: MU.caja, caminos: MU.caminos || {}, lugares: MU.lugares || {},
  camino: (nombre) => (MU.caminos || {})[nombre] || null,
  enCamino: (nombre, s) => enCadena(ctx.camino(nombre), s),      // {x, y, dx, dy}: el punto a s de su inicio y hacia dónde va
  puntoEnS, distCadena,
  GLSL_COMUN, VERT_CINTA, uComun,                                // (el mundo pais añade NR, NC, NO, GLSL_RUPTURA, uRuptura, superficie)
  geoCinta, pegar, cinta: cintaSimple,
  tonos: TONOS, sombra, malla,                                   // superficies de mundo (ciudad, esquema): colores, luz y geometría
  // lo que se mueve: tray (evaluar una trayectoria T/S suavizada), moviles (id → (t, n) → {x, y, dx, dy, v, vis}: lo registran
  // actor y flujo; lo siguen la cámara y las anotaciones), ancla(A, t) y flota(tipo, n, {tamano, lev, luces, color, orden, cabeceo})
  tray, moviles: MOVILES, ancla: (A, t) => anclaEn(A, t), flota,
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
// lo que la capa 2D (y sus anotaciones) necesita del mundo: dónde está un ancla en t y la altura del suelo (unidades de la escena)
const CAPA_MUNDO = { ancla: (A, t) => anclaEn(A, t), altura: (x, y) => altura(x, y), metros: (v) => v / MU.unidad_m };
// ---------- sombras reales: el pase de profundidad desde la luz (función pura del cuadro) ----------
const SOMBRAS = (() => {
  const k = MU.escala !== "pais" ? (CFG.sombras || 0) : 0;      // solo en mundos de cerca (en el mapa, el relieve ya trae su sombreado)
  if (!(k > 0)) return null;
  const tam = 2048, rt = new THREE.WebGLRenderTarget(tam, tam, { depthBuffer: true });
  rt.depthTexture = new THREE.DepthTexture(tam, tam); rt.depthTexture.type = THREE.UnsignedIntType;
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10), mat = new THREE.MeshDepthMaterial({ side: THREE.DoubleSide });
  mat.polygonOffset = true; mat.polygonOffsetFactor = 2; mat.polygonOffsetUnits = 4;
  U_SOMBRA.uSombraK.value = k; U_SOMBRA.uLuzW.value.copy(LUZ_DIR).normalize(); U_SOMBRA.uSombraTx.value = 1 / tam;
  U_SOMBRA.uVolumen.value = CFG.volumen || 0;
  return { rt, cam, mat, tam, ocultos: [] };
})();
function proyectaSombra(o) {   // ¿este objeto tapa la luz? mallas opacas con volumen (ni líneas, ni puntos, ni lo transparente, ni el fondo)
  const m = o.material;
  return o.isMesh && m && !m.transparent && m.depthWrite !== false && m.depthTest !== false && !(m.uniforms && m.uniforms.uAncho) && !o.userData.sinSombra;
}
function pasarSombras() {
  if (!SOMBRAS) return;
  const S = SOMBRAS, c = CAM, R = Math.max(c.dist * 1.7, 45 / MU.unidad_m), L = U_SOMBRA.uLuzW.value;
  // la luz, ortográfica y centrada en lo que mira la cámara (alineada a su rejilla de texeles: sin temblor al mover la cámara)
  const up = Math.abs(L.y) > 0.98 ? new THREE.Vector3(0, 0, -1) : new THREE.Vector3(0, 1, 0);
  const ejeX = new THREE.Vector3().crossVectors(up, L).normalize(), ejeY = new THREE.Vector3().crossVectors(L, ejeX).normalize();
  const obj = new THREE.Vector3(c.x, c.alt, -c.y), tex = 2 * R / S.tam;
  U_SOMBRA.uSombraTxW.value = tex;
  const ux = Math.round(obj.dot(ejeX) / tex) * tex, uy = Math.round(obj.dot(ejeY) / tex) * tex, uz = obj.dot(L);
  obj.copy(ejeX).multiplyScalar(ux).addScaledVector(ejeY, uy).addScaledVector(L, uz);
  S.cam.left = -R; S.cam.right = R; S.cam.top = R; S.cam.bottom = -R; S.cam.near = R * 0.05; S.cam.far = R * 8;
  S.cam.position.copy(obj).addScaledVector(L, R * 4); S.cam.up.copy(up); S.cam.lookAt(obj); S.cam.updateProjectionMatrix(); S.cam.updateMatrixWorld(true);
  S.ocultos.length = 0;
  scene.traverse((o) => { if ((o.isMesh || o.isPoints || o.isLine) && o.visible && !proyectaSombra(o)) { o.visible = false; S.ocultos.push(o); } });
  const fondo0 = scene.background; scene.overrideMaterial = S.mat;
  renderer.setRenderTarget(S.rt); renderer.clear(); renderer.render(scene, S.cam); renderer.setRenderTarget(null);
  scene.overrideMaterial = null; scene.background = fondo0;
  for (const o of S.ocultos) o.visible = true;
  U_SOMBRA.tSombra.value = S.rt.depthTexture;
  U_SOMBRA.uSombraM.value.multiplyMatrices(S.cam.projectionMatrix, S.cam.matrixWorldInverse);
}

// ---------- resplandor (CFG.resplandor, de noche en mundos de cerca): lo que brilla deja un halo suave ----------
// La imagen NO cambia: sobre ella se SUMA la escena a un cuarto de tamaño, cortada a lo más brillante y desenfocada
// (cuatro pasadas). Función pura del cuadro; el cielo queda fuera (sus estrellas se dibujan por píxel).
const RESPLANDOR = (() => {
  const k = MU.escala !== "pais" ? (CFG.resplandor || 0) : 0;
  if (!(k > 0)) return null;
  const w = Math.round(W / 4), h = Math.round(H / 4);
  const a = new THREE.WebGLRenderTarget(w, h, { depthBuffer: true }), b = new THREE.WebGLRenderTarget(w, h, { depthBuffer: false }), c = new THREE.WebGLRenderTarget(w, h, { depthBuffer: false });
  const vs = "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }";
  const blur = new THREE.ShaderMaterial({ uniforms: { tex: { value: null }, dir: { value: new THREE.Vector2() }, umbral: { value: 2 } }, vertexShader: vs, depthTest: false, depthWrite: false,
    fragmentShader: `uniform sampler2D tex; uniform vec2 dir; uniform float umbral; varying vec2 vUv;
      vec3 toma(vec2 uv) { vec3 x = texture2D(tex, uv).rgb; return x * smoothstep(umbral, umbral + 0.22, max(x.r, max(x.g, x.b))); }
      void main(){ vec3 s = toma(vUv) * 0.227 + (toma(vUv + dir * 1.385) + toma(vUv - dir * 1.385)) * 0.316 + (toma(vUv + dir * 3.231) + toma(vUv - dir * 3.231)) * 0.070;
        gl_FragColor = vec4(s, 1.0); }` });
  const suma = new THREE.ShaderMaterial({ uniforms: { tex: { value: null }, k: { value: k } }, vertexShader: vs, depthTest: false, depthWrite: false, transparent: true, blending: THREE.AdditiveBlending,
    fragmentShader: "uniform sampler2D tex; uniform float k; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(tex, vUv).rgb * k, 1.0); }" });
  const escena = new THREE.Scene(), quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), blur); quad.frustumCulled = false; escena.add(quad);
  return { a, b, c, w, h, blur, suma, escena, quad, cam: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), cielo: scene.children.find((o) => o.userData.cielo) };
})();
function pasarResplandor() {
  if (!RESPLANDOR) return;
  const R = RESPLANDOR, u = R.blur.uniforms, negro = renderer.getClearColor(new THREE.Color()).clone();
  if (R.cielo) R.cielo.visible = false;
  RES.set(R.w, R.h); renderer.setClearColor(0x000000, 1);
  renderer.setRenderTarget(R.a); renderer.clear(); renderer.render(scene, camera);
  RES.set(W, H); renderer.setClearColor(negro, 1);
  if (R.cielo) R.cielo.visible = true;
  R.quad.material = R.blur;
  const paso = (de, a, dx, dy, umbral) => { u.tex.value = de.texture; u.dir.value.set(dx / R.w, dy / R.h); u.umbral.value = umbral; renderer.setRenderTarget(a); renderer.render(R.escena, R.cam); };
  paso(R.a, R.b, 1, 0, 0.6); paso(R.b, R.c, 0, 1, -1); paso(R.c, R.b, 2.4, 0, -1); paso(R.b, R.c, 0, 2.4, -1);
  renderer.setRenderTarget(null);
  const ac = renderer.autoClear; renderer.autoClear = false;
  R.quad.material = R.suma; R.suma.uniforms.tex.value = R.c.texture; renderer.render(R.escena, R.cam);
  renderer.autoClear = ac;
}

function renderAt(t) {
  UT.value = t;
  ponerCamara(t);
  mundoEn(t);
  pasarSombras();
  renderer.render(scene, camera);
  pasarResplandor();
  if (window.__capa) window.__capa(t, proyectar, CAPA_MUNDO);
}

// ---------- contrato HyperFrames ----------
window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};
window.__hf.buildReady["maqueta"] = (async () => {
  const [est] = await Promise.all([MUNDO.cargar ? MUNDO.cargar(ctx) : null, ...(window.__capaFuentes || []).map((f) => document.fonts.load(f))]);
  MUNDO_EST = est;
  ctx.suelo = ctx.altura;                                         // el suelo del mundo, sin el relieve de pieza
  if (CAMPOS.length) ctx.altura = (x, y) => ctx.suelo(x, y) + relieve(x, y);
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
