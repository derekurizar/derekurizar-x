// Motor de la maqueta 3D (/video-3d): three.js dibujado cuadro a cuadro por HyperFrames.
// Entrada única: window.MAQUETA, el maqueta.json ya RESUELTO por scripts/maqueta3d.py (lugares en km, cadenas de
// falla, cámara con su altura, colores del estilo y de la paleta, zona del formato). Aquí no hay red, reloj ni azar:
// cada cuadro es una función pura de t (el mismo t da el mismo cuadro).
//   1) mundo:   relieve (malla + textura de normales), máscara del país, piezas (falla, luces, frontera, ruta)
//   2) estilo:  un registro ESTILOS; el relieve se pinta en un solo shader con un modo por estilo (voxel: cubos)
//   3) cuadro:  cámara por claves → eventos (ruptura, onda, deslizar, luces, resaltar) → render → capa 2D (capa.js)
// Mundo en km: x = este, y = norte, altura hacia arriba → three (x, altura, −y). Ningún color escrito aquí: todos
// llegan en MAQUETA.col (design/sets3d/estilos.json + design/tokens.json).
import * as THREE from "./three/three.module.js";

const M = window.MAQUETA;
const W = M.W, H = M.H, R = M.relieve, P = R.proyeccion, EXAG = M.exageracion;
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

// ---------- relieve: imagen → alturas ----------
const RW = R.ancho, RH = R.alto, CAJA = R.caja;
const X0 = (CAJA.lon_min - P.lon0) * P.km_lon, X1 = (CAJA.lon_max - P.lon0) * P.km_lon;
const Y0 = (CAJA.lat_min - P.lat0) * P.km_lat, Y1 = (CAJA.lat_max - P.lat0) * P.km_lat;
const CX = (X1 - X0) / RW, CY = (Y1 - Y0) / RH;                  // km por celda
let ALT = null;                                                  // metros reales, fila 0 = norte
async function cargarRelieve() {
  const img = new Image(); img.src = "assets/set/" + R.archivo; await img.decode();
  const c = document.createElement("canvas"); c.width = RW; c.height = RH;
  const g = c.getContext("2d", { willReadFrequently: true, colorSpace: "srgb" });
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, RW, RH).data;
  ALT = new Float32Array(RW * RH);
  for (let i = 0; i < RW * RH; i++) ALT[i] = d[4 * i] * 256 + d[4 * i + 1] - R.desfase_m;
  for (const [i, j, v] of R.muestras) if (ALT[j * RW + i] !== v) console.error("relieve: la imagen se leyó con conversión de color (muestra " + i + "," + j + ")");
}
// altura de la maqueta (km, ya exagerada) en un punto del mundo; el mar queda en 0
function altura(x, y) {
  const fi = clamp((x - X0) / CX - 0.5, 0, RW - 1.001), fj = clamp((Y1 - y) / CY - 0.5, 0, RH - 1.001);
  const i = Math.floor(fi), j = Math.floor(fj), u = fi - i, v = fj - j, k = j * RW + i;
  const h = (ALT[k] * (1 - u) + ALT[k + 1] * u) * (1 - v) + (ALT[k + RW] * (1 - u) + ALT[k + RW + 1] * u) * v;
  return Math.max(0, h) / 1000 * EXAG;
}
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

// GLSL común: ruido fijo por píxel (grano y tramado), fondo, y «encendida» (qué tramo de una falla ya se rompió)
const NR = 4, NC = 56, NO = 4;
const GLSL_COMUN = `
  uniform vec3 cFondo, cFondo2; uniform vec2 uRes; uniform float uGrano;
  float ruido(vec2 p) { return fract(sin(dot(floor(p), vec2(12.9898, 78.233))) * 43758.5453); }
  vec3 fondoEn(vec2 frag) { float v = frag.y / uRes.y; return mix(cFondo2, cFondo, smoothstep(0.0, 1.0, v)); }
  uniform vec2 uNiebla;                                  // km desde la cámara: dónde empieza y dónde termina de fundirse con el fondo
  vec3 niebla(vec3 c, vec3 pos, vec2 frag) { return mix(c, fondoEn(frag), smoothstep(uNiebla.x, uNiebla.y, distance(pos, cameraPosition))); }
  vec3 salida(vec3 c, vec2 frag) {   // lineal → sRGB + grano fijo
    c = mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(0.41666)) - 0.055, step(0.0031308, c));
    return c + (ruido(frag) - 0.5) * uGrano;
  }`;
const GLSL_RUPTURA = `
  uniform vec4 uRup[${NR}]; uniform vec2 uRupT[${NR}];   // (s0, km hacia −s, km hacia +s, dur) · (segundos desde que empezó, pieza)
  float encendida(float s, float pieza, out float calor) {
    float L = 0.0; calor = 0.0;
    for (int i = 0; i < ${NR}; i++) {
      float tr = uRupT[i].x;
      if (abs(uRupT[i].y - pieza) > 0.25 || tr <= 0.0) continue;
      float d = s - uRup[i].x, ad = abs(d);
      float alc = d < 0.0 ? uRup[i].y : uRup[i].z;
      float frente = alc * min(tr / uRup[i].w, 1.0);          // cada frente avanza a su ritmo; los dos llegan en dur
      float l = alc > 0.0 ? 1.0 - smoothstep(frente - 1.2, frente + 0.4, ad) : 0.0;
      float c = exp(-max(tr - ad / max(alc, 0.001) * uRup[i].w, 0.0) / 1.4);   // recién roto: más caliente
      L = max(L, l); calor = max(calor, l * c);
    }
    return L;
  }`;
const NIEBLA = new THREE.Vector2(3000, 9000);
const uComun = () => ({ cFondo: { value: lin(COL.fondo) }, cFondo2: { value: lin(COL.fondo2) }, uRes: { value: RES }, uGrano: { value: CFG.grano }, uNiebla: { value: NIEBLA } });
const uRuptura = { uRup: { value: Array.from({ length: NR }, () => new THREE.Vector4()) }, uRupT: { value: Array.from({ length: NR }, () => new THREE.Vector2(0, -1)) } };

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
  const gp = new THREE.PlaneGeometry(30000, 30000); gp.rotateX(-Math.PI / 2);
  const mp = new THREE.ShaderMaterial({ uniforms: { ...uComun(), cExterior: { value: lin(COL.exterior) } }, depthTest: false, depthWrite: false,
    vertexShader: "varying vec3 vPos; void main(){ vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: GLSL_COMUN + "uniform vec3 cExterior; varying vec3 vPos; void main(){ gl_FragColor = vec4(salida(niebla(cExterior, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0); }" });
  const plano = new THREE.Mesh(gp, mp); plano.position.y = -0.15; plano.frustumCulled = false; plano.renderOrder = -9; scene.add(plano);
}

// ---------- piezas resueltas ----------
const FALLAS = M.piezas.filter((p) => p.tipo === "falla");       // cada una con .cadena [[x, y, s, salto]] y .simple
const LUCES = M.piezas.filter((p) => p.tipo === "luces");
const idxFalla = (id) => FALLAS.findIndex((p) => p.id === id);
function puntoEnS(cad, s) {                                      // [x, y] en la cadena a s km de su inicio
  if (s <= cad[0][2]) return [cad[0][0], cad[0][1]];
  for (let i = 0; i < cad.length - 1; i++) { const a = cad[i], b = cad[i + 1];
    if (s <= b[2]) { const u = (s - a[2]) / Math.max(1e-6, b[2] - a[2]); return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]; } }
  const z = cad[cad.length - 1]; return [z[0], z[1]];
}
function distCadena(cad, x, y) {                                 // distancia (km) de un punto a la cadena (sin los saltos)
  let m = 1e9;
  for (let i = 0; i < cad.length - 1; i++) { const a = cad[i], b = cad[i + 1]; if (a[3]) continue;
    const dx = b[0] - a[0], dy = b[1] - a[1], h = clamp(((x - a[0]) * dx + (y - a[1]) * dy) / Math.max(1e-9, dx * dx + dy * dy));
    m = Math.min(m, Math.hypot(x - a[0] - dx * h, y - a[1] - dy * h)); }
  return m;
}

// ---------- el relieve ----------
let matRelieve = null, cubos = null;
const uRelieve = {
  ...uComun(), ...uRuptura,
  tNormal: { value: null }, tPais: { value: null }, uModo: { value: ES.modo },
  cMar: { value: lin(COL.mar) }, cMarHondo: { value: lin(COL.mar_hondo) }, cExterior: { value: lin(COL.exterior) }, uMarRel: { value: CFG.mar.relieve }, uMarLuz: { value: CFG.mar.luz }, cBaja: { value: lin(COL.tierra_baja) }, cMedia: { value: lin(COL.tierra_media) }, cAlta: { value: lin(COL.tierra_alta) },
  cLuz: { value: lin(COL.luz) }, cAmb: { value: lin(COL.ambiente) }, cOnda: { value: lin(COL.onda) },
  cPieza: { value: [0, 1, 2, 3].map((i) => (FALLAS[i] && FALLAS[i].protagonista ? lin(COL.acento) : lin(COL.secundario).multiplyScalar(CFG.falla.secundaria))) },
  cLinea: { value: lin(COL.linea) }, cCosta: { value: lin(COL.costa) },
  uLuzDir: { value: new THREE.Vector3() }, uLuzK: { value: CFG.luz.fuerza }, uAmbK: { value: CFG.luz.ambiente }, uRel: { value: CFG.luz.relieve },
  uFuera: { value: CFG.fuera }, uCosta: { value: CFG.costa }, uAltMax: { value: R.max_m / 1000 * EXAG }, uExag: { value: EXAG },
  uCaja: { value: new THREE.Vector4(X0, X1, -Y1, -Y0) }, uBorde: { value: CFG.borde_km },
  uCad: { value: Array.from({ length: NC }, () => new THREE.Vector4()) }, uCadN: { value: 0 },
  uBrillo: { value: [1, 1, 1, 1] }, uGlow: { value: CFG.falla.suelo }, uSigma: { value: CFG.falla.suelo_km },
  uOnda: { value: Array.from({ length: NO }, () => new THREE.Vector4()) }, uOndaPieza: { value: [-1, -1, -1, -1] },
};
{ const az = CFG.luz.azimut * Math.PI / 180, el = CFG.luz.elevacion * Math.PI / 180;   // de dónde viene la luz (0 = norte, 90 = este)
  uRelieve.uLuzDir.value.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)); }
// cadenas simplificadas de todas las fallas en un solo arreglo (x, z, s, pieza [+0.5 si después hay un salto])
{ let n = 0;
  FALLAS.forEach((f, ip) => { for (const p of f.simple) { if (n >= NC) break; uRelieve.uCad.value[n++].set(p[0], -p[1], p[2], ip + (p[3] ? 0.5 : 0)); } });
  uRelieve.uCadN.value = n; }

const FRAG_RELIEVE = GLSL_COMUN + GLSL_RUPTURA + `
  uniform sampler2D tNormal, tPais; uniform int uModo;
  uniform vec3 cMar, cMarHondo, cExterior, cBaja, cMedia, cAlta, cLuz, cAmb, cOnda, cLinea, cCosta, uLuzDir; uniform vec3 cPieza[4]; uniform float uMarRel, uMarLuz;
  uniform float uLuzK, uAmbK, uRel, uFuera, uCosta, uAltMax, uExag, uBorde, uGlow, uSigma;
  uniform vec4 uCaja; uniform vec4 uCad[${NC}]; uniform int uCadN; uniform float uBrillo[4];
  uniform vec4 uOnda[${NO}]; uniform float uOndaPieza[${NO}];
  varying vec2 vUv; varying vec3 vPos; varying float vAlt;
  void main() {
    vec4 tn = texture2D(tNormal, vUv);
    vec2 nh = tn.xy * 2.0 - 1.0; vec3 n0 = vec3(nh.x, sqrt(max(1.0 - dot(nh, nh), 0.0)), nh.y);   // textura: normal (x, z), fondo del mar, tierra
    float tierra = smoothstep(0.35, 0.65, tn.a);
    vec3 n = normalize(vec3(n0.x * uRel, n0.y, n0.z * uRel));
    // el mar: más claro en lo somero, más oscuro en lo hondo, con el relieve del fondo apenas insinuado
    vec3 nm = normalize(vec3(n0.x * uRel * uMarRel, n0.y, n0.z * uRel * uMarRel));
    float sm = smoothstep(-0.35, 1.0, dot(nm, uLuzDir));
    vec3 mar = mix(cMar, cMarHondo, smoothstep(0.0, 0.62, tn.b)) * mix(1.0, 0.45 + 1.1 * sm * sm, uMarLuz);
    float pais = texture2D(tPais, vUv).r;
    float hN = clamp(vAlt / uAltMax, 0.0, 1.0);
    float metros = vAlt / uExag * 1000.0;
    float lam = max(dot(n, uLuzDir), 0.0);
    vec3 base = mix(cBaja, cMedia, smoothstep(0.0, 0.38, hN)); base = mix(base, cAlta, smoothstep(0.38, 1.0, hN));
    float costa = (1.0 - abs(tn.a * 2.0 - 1.0)) * uCosta;
    vec3 col;
    if (uModo == 1) {                       // noche: luz rasante tenue, mar más oscuro, el país un poco más claro que lo de afuera
      float sl = smoothstep(-0.35, 1.0, dot(n, uLuzDir));
      col = base * (cAmb * uAmbK + cLuz * uLuzK * sl * sl);
      float gris = dot(col, vec3(0.3, 0.5, 0.2));
      col = mix(mix(vec3(gris), col, 0.45) * uFuera, col, pais);
      col = mix(mar, col, tierra);
      col += cCosta * costa * mix(0.4, 1.0, pais);
    } else if (uModo == 2) {                // contorno: tres tonos, bandas de altura y línea de tinta
      float q = lam < 0.22 ? 0.56 : (lam < 0.62 ? 0.8 : 1.0);
      float banda = floor(metros / 600.0);
      vec3 b = mix(cBaja, cMedia, clamp(banda / 3.0, 0.0, 1.0)); b = mix(b, cAlta, clamp((banda - 3.0) / 3.0, 0.0, 1.0));
      col = mix(mix(cMar, cMarHondo, step(0.25, tn.b) * 0.5 + step(0.5, tn.b) * 0.5), b * q, step(0.5, tn.a));
      col = mix(col, mix(col, cMar, 0.35), (1.0 - pais) * uFuera);
      float fb = metros / 600.0; float lc = abs(fract(fb - 0.5) - 0.5) / max(fwidth(fb), 1e-5);
      float tinta = (1.0 - smoothstep(0.7, 1.6, lc)) * tierra * 0.55;
      float fc = abs(tn.a - 0.5) / max(fwidth(tn.a), 1e-5);
      tinta = max(tinta, 1.0 - smoothstep(1.0, 2.2, fc));
      col = mix(col, cLinea, tinta);
    } else if (uModo == 4) {                // plano: caras del color del fondo, curvas de nivel y retícula en línea clara
      col = mix(mix(cMar, cMarHondo, smoothstep(0.0, 0.62, tn.b)), cBaja, tierra);
      { float fd = tn.b * 8.0; float ld = abs(fract(fd - 0.5) - 0.5) / max(fwidth(fd), 1e-5); col = mix(col, cLinea, (1.0 - smoothstep(0.5, 1.5, ld)) * (1.0 - tierra) * 0.12); }
      float fb = metros / 400.0; float lc = abs(fract(fb - 0.5) - 0.5) / max(fwidth(fb), 1e-5);
      float l = (1.0 - smoothstep(0.5, 1.5, lc)) * tierra * step(40.0, metros) * 0.5;
      vec2 gr = vUv * vec2(10.4, 9.6); vec2 fg = abs(fract(gr - 0.5) - 0.5) / max(fwidth(gr), vec2(1e-5));
      l = max(l, (1.0 - smoothstep(0.5, 1.4, min(fg.x, fg.y))) * 0.28);
      float fc = abs(tn.a - 0.5) / max(fwidth(tn.a), 1e-5);
      l = max(l, (1.0 - smoothstep(0.8, 2.0, fc)) * 0.9);
      col = mix(col, cLinea, l * mix(uFuera, 1.0, pais));
    } else {                                // color: tinta hipsométrica con sol
      col = base * (cAmb * uAmbK + cLuz * uLuzK * lam);
      col = mix(mar, col, tierra);
      col += cCosta * costa;
      col = mix(mix(col, cFondo, (1.0 - uFuera) * tierra), col, pais);
    }
    // la falla encendida alumbra el suelo; las ondas son anillos que crecen
    vec2 p = vPos.xz; float glow = 0.0, cal = 0.0; vec3 cg = cPieza[0]; float dP[4]; dP[0] = 1e6; dP[1] = 1e6; dP[2] = 1e6; dP[3] = 1e6;
    for (int i = 0; i < ${NC - 1}; i++) {
      if (i >= uCadN - 1) break;
      vec4 a = uCad[i], b = uCad[i + 1];
      float pa = floor(a.w);
      if (pa != floor(b.w) || fract(a.w) > 0.25) continue;
      vec2 ab = b.xy - a.xy; float h = clamp(dot(p - a.xy, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
      float d = length(p - (a.xy + ab * h));
      int ip = int(pa); if (ip == 0) dP[0] = min(dP[0], d); else if (ip == 1) dP[1] = min(dP[1], d); else if (ip == 2) dP[2] = min(dP[2], d); else dP[3] = min(dP[3], d);
      float ds = max(b.z - a.z, 1e-4), br = ip == 0 ? uBrillo[0] : ip == 1 ? uBrillo[1] : ip == 2 ? uBrillo[2] : uBrillo[3];
      for (int j = 0; j < ${NR}; j++) {
        float tr = uRupT[j].x;
        if (abs(uRupT[j].y - pa) > 0.25 || tr <= 0.0) continue;
        float u = min(tr / uRup[j].w, 1.0), lo = uRup[j].x - uRup[j].y * u, hi = uRup[j].x + uRup[j].z * u;
        if (hi < a.z || lo > b.z) continue;
        float hh = clamp(h, clamp((lo - a.z) / ds, 0.0, 1.0), clamp((hi - a.z) / ds, 0.0, 1.0));
        float dl = length(p - (a.xy + ab * hh)), sl = mix(a.z, b.z, hh) - uRup[j].x;
        float alc = sl < 0.0 ? uRup[j].y : uRup[j].z;
        float g = (exp(-dl / uSigma) * 0.75 + exp(-dl / (uSigma * 0.22)) * 0.6) * br * smoothstep(0.0, 0.25, tr);
        if (g > glow) { glow = g; cg = ip == 0 ? cPieza[0] : ip == 1 ? cPieza[1] : ip == 2 ? cPieza[2] : cPieza[3]; }
        cal = max(cal, exp(-max(tr - abs(sl) / max(alc, 0.001) * uRup[j].w, 0.0) / 1.4) * exp(-dl / uSigma));
      }
    }
    col += cg * glow * uGlow * (1.0 + cal * 0.9);
    for (int i = 0; i < ${NO}; i++) {
      float k = uOnda[i].w; if (k <= 0.0) continue;
      int ip = int(uOndaPieza[i]);
      float d = ip < 0 ? length(p - uOnda[i].xy) : (ip == 0 ? dP[0] : ip == 1 ? dP[1] : ip == 2 ? dP[2] : dP[3]);
      float r = uOnda[i].z, w = 1.3 + r * 0.016;
      float anillo = exp(-((d - r) / w) * ((d - r) / w)) + 0.10 * (1.0 - smoothstep(r - 14.0 * w, r, d)) * step(d, r);
      col = uModo == 1 || uModo == 4 ? col + cOnda * anillo * k * 0.55 : mix(col, cOnda, clamp(anillo * k, 0.0, 0.9));
    }
    // el borde de la maqueta se funde con el fondo
    float bd = min(min(vPos.x - uCaja.x, uCaja.y - vPos.x), min(vPos.z - uCaja.z, uCaja.w - vPos.z));
    col = mix(cExterior, col, smoothstep(0.0, uBorde, bd));   // la orilla de la caja se funde con el plano exterior
    gl_FragColor = vec4(salida(niebla(col, vPos, gl_FragCoord.xy), gl_FragCoord.xy), 1.0);
  }`;

function armarRelieve() {
  // textura: normal (RGB, con exageración fija 4) y tierra/mar (A), a resolución completa con mipmaps
  const S0 = 4, tex = new Uint8Array(RW * RH * 4);
  for (let j = 0; j < RH; j++) for (let i = 0; i < RW; i++) {
    const h = (ii, jj) => ALT[clamp(jj, 0, RH - 1) * RW + clamp(ii, 0, RW - 1)] / 1000 * S0;
    const dx = (h(i + 1, j) - h(i - 1, j)) / (2 * CX), dz = (h(i, j + 1) - h(i, j - 1)) / (2 * CY);
    const l = Math.hypot(dx, 1, dz), k = (j * RW + i) * 4;
    tex[k] = (-dx / l * 0.5 + 0.5) * 255; tex[k + 1] = (-dz / l * 0.5 + 0.5) * 255; tex[k + 2] = clamp(-ALT[j * RW + i] / 8000) * 255;
    tex[k + 3] = ALT[j * RW + i] > 0 ? 255 : 0;
  }
  const tN = new THREE.DataTexture(tex, RW, RH, THREE.RGBAFormat, THREE.UnsignedByteType);
  tN.colorSpace = THREE.NoColorSpace; tN.generateMipmaps = true; tN.minFilter = THREE.LinearMipmapLinearFilter; tN.magFilter = THREE.LinearFilter;
  tN.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy()); tN.needsUpdate = true;
  uRelieve.tNormal.value = tN; uRelieve.uRel.value = CFG.luz.relieve * EXAG / S0;
  // máscara del país (1 adentro): el contorno relleno en un lienzo 2D
  const c = document.createElement("canvas"); c.width = 2048; c.height = 2048; const g = c.getContext("2d");
  g.fillStyle = "black"; g.fillRect(0, 0, 2048, 2048); g.fillStyle = "white"; g.filter = "blur(1.5px)";
  for (const an of M.frontera) { g.beginPath(); an.forEach(([x, y], k) => { const u = (x - X0) / (X1 - X0) * 2048, v = (Y1 - y) / (Y1 - Y0) * 2048; k ? g.lineTo(u, v) : g.moveTo(u, v); }); g.closePath(); g.fill(); }
  const tP = new THREE.CanvasTexture(c); tP.flipY = false; tP.colorSpace = THREE.NoColorSpace; tP.minFilter = THREE.LinearMipmapLinearFilter; tP.generateMipmaps = true;
  uRelieve.tPais.value = tP;

  if (ES.cubos) return armarCubos(g);
  const PASO = 2, nx = Math.floor((RW - 1) / PASO) + 1, ny = Math.floor((RH - 1) / PASO) + 1;
  const pos = new Float32Array(nx * ny * 3), uv = new Float32Array(nx * ny * 2);
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    const ci = i * PASO, cj = j * PASO, k = j * nx + i;
    const x = X0 + (ci + 0.5) * CX, y = Y1 - (cj + 0.5) * CY;
    pos[3 * k] = x; pos[3 * k + 1] = Math.max(0, ALT[cj * RW + ci]) / 1000 * EXAG; pos[3 * k + 2] = -y;
    uv[2 * k] = (ci + 0.5) / RW; uv[2 * k + 1] = (cj + 0.5) / RH;
  }
  const idx = new Uint32Array((nx - 1) * (ny - 1) * 6); let q = 0;
  for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) { const a = j * nx + i, b = a + 1, c2 = a + nx, d = c2 + 1; idx[q++] = a; idx[q++] = c2; idx[q++] = b; idx[q++] = b; idx[q++] = c2; idx[q++] = d; }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3)); geo.setAttribute("uv", new THREE.BufferAttribute(uv, 2)); geo.setIndex(new THREE.BufferAttribute(idx, 1));
  matRelieve = new THREE.ShaderMaterial({ uniforms: uRelieve, 
    vertexShader: "varying vec2 vUv; varying vec3 vPos; varying float vAlt; void main(){ vUv = uv; vPos = position; vAlt = position.y; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: FRAG_RELIEVE });
  const malla = new THREE.Mesh(geo, matRelieve); malla.frustumCulled = false; scene.add(malla);
}

// [estilo:voxel] el relieve en columnas: una por cada bloque de 6×6 celdas, altura en escalones, tono por altura
function armarCubos(gPais) {
  const B = 6, nx = Math.floor(RW / B), ny = Math.floor(RH / B), paso = 0.3 * EXAG;   // escalón: 300 m reales
  const pais = gPais.getImageData(0, 0, 2048, 2048).data;
  const cBaja = lin(COL.tierra_baja), cMedia = lin(COL.tierra_media), cAlta = lin(COL.tierra_alta), cMar = lin(COL.mar), cHondo = lin(COL.mar_hondo), cF = lin(COL.exterior);
  const lista = [];
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    let s = 0, t = 0, fondo = 0; for (let b = 0; b < B; b++) for (let a = 0; a < B; a++) { const v = ALT[(j * B + b) * RW + i * B + a]; s += Math.max(0, v); fondo += Math.min(0, v); if (v > 0) t++; }
    const m = s / (B * B), x = X0 + (i + 0.5) * B * CX, y = Y1 - (j + 0.5) * B * CY;
    const borde = suave(0, CFG.borde_km, Math.min(x - X0, X1 - x, y - Y0, Y1 - y));
    if (borde <= 0.02) continue;
    const tierra = t > B * B / 2;
    const alto = tierra ? Math.max(1, Math.round(m / 1000 * EXAG / paso)) * paso : paso * 0.35;
    const hN = clamp(m / R.max_m), col = new THREE.Color();
    if (tierra) { col.copy(cBaja).lerp(cMedia, suave(0, 0.38, hN)).lerp(cAlta, suave(0.38, 1, hN)); col.multiplyScalar(0.92 + 0.16 * hash(i, j)); }
    else col.copy(cMar).lerp(cHondo, suave(0, 5000, -fondo / (B * B))).multiplyScalar(0.95 + 0.1 * hash(i, j));
    const dentro = pais[(Math.floor((Y1 - y) / (Y1 - Y0) * 2048) * 2048 + Math.floor((x - X0) / (X1 - X0) * 2048)) * 4] > 127;
    if (!dentro && tierra) col.lerp(cF, 1 - CFG.fuera);
    col.lerp(cF, 1 - borde);
    lista.push({ x, y, alto, col });
  }
  const geo = new THREE.BoxGeometry(B * CX * 0.96, 1, B * CY * 0.96); geo.translate(0, 0.5, 0);
  const mat = new THREE.MeshLambertMaterial();
  cubos = new THREE.InstancedMesh(geo, mat, lista.length); cubos.frustumCulled = false;
  const m4 = new THREE.Matrix4();
  lista.forEach((c, k) => { m4.makeScale(1, c.alto, 1); m4.setPosition(c.x, 0, -c.y); cubos.setMatrixAt(k, m4); cubos.setColorAt(k, c.col); });
  cubos.userData = { lista, base: lista.map((c) => c.col.clone()) };
  scene.add(cubos);
  const az = CFG.luz.azimut * Math.PI / 180, el = CFG.luz.elevacion * Math.PI / 180;
  const sol = new THREE.DirectionalLight(lin(COL.luz), CFG.luz.fuerza * Math.PI); sol.position.set(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
  scene.add(sol, new THREE.AmbientLight(lin(COL.ambiente), CFG.luz.ambiente * Math.PI));
}
// [/estilo:voxel]

// ---------- cintas: líneas con ancho en píxeles, pegadas al relieve (falla, frontera, ruta, flechas) ----------
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
// densifica una polilínea [[x, y, s?, salto?]] a pasos de ≤ `paso` km y la pega al relieve
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
const cintas = [];   // {mat, ancho(dist) → px}
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

// frontera y rutas
const PIEZAS_LINEA = {};   // id → cinta (para «resaltar»)
function armarLineas() {
  for (const p of M.piezas) {
    if (p.tipo === "frontera") {
      for (const an of p.anillos) { const cad = an.map(([x, y]) => [x, y]); cad.push(cad[0]);
        if (CFG.frontera.borde) cintaSimple(pegar(cad, 1.5, 0.35), COL.linea, CFG.frontera.ancho + CFG.frontera.borde, 1, 2);
        PIEZAS_LINEA[p.id] = p.protagonista ? cintaSimple(pegar(cad, 1.5, 0.35), COL.acento, CFG.frontera.ancho * 1.7, 1, 3)
          : cintaSimple(pegar(cad, 1.5, 0.35), COL.frontera, CFG.frontera.ancho, CFG.frontera.alfa, 3); }
    } else if (p.tipo === "ruta") {
      PIEZAS_LINEA[p.id] = cintaSimple(pegar(p.puntos, 1.5, 0.4), p.protagonista ? COL.acento : COL.ruta, CFG.ruta.ancho * (p.protagonista ? 1.5 : 1), p.protagonista ? 1 : CFG.ruta.alfa, 4, { raya: CFG.ruta.raya_km });
    }
  }
}

// la falla: dormida (línea fina), y al romperse halo + núcleo en el acento; las flechas del corrimiento encima
const fallas3d = [];
function armarFallas() {
  FALLAS.forEach((f, ip) => {
    const pts = pegar(f.cadena, 1.0, 0.3), geo = geoCinta(pts);
    const capa = (n, ancho, orden, aditivo, oculta) => {
      const mat = new THREE.ShaderMaterial({
        uniforms: { ...uComun(), ...uRuptura, uAncho: { value: ancho }, uCapa: { value: n }, uPieza: { value: ip }, uBrillo: { value: 1 },
          cAcento: { value: lin(f.protagonista ? COL.acento : COL.secundario) }, cCaliente: { value: lin(COL.caliente) }, cDormida: { value: lin(COL.falla_dormida) }, cBorde: { value: lin(COL.linea) },
          uDormida: { value: CFG.falla.dormida }, uHalo: { value: CFG.falla.halo * (f.protagonista ? 1 : CFG.falla.secundaria) } },
        vertexShader: VERT_CINTA, transparent: true, depthWrite: false, depthTest: oculta,
        blending: aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
        fragmentShader: GLSL_RUPTURA + `uniform int uCapa; uniform float uPieza, uBrillo, uDormida, uHalo; uniform vec3 cAcento, cCaliente, cDormida, cBorde;
          varying float vLado, vS;
          vec3 srgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); }
          void main() {
            float cal; float L = encendida(vS, uPieza, cal); float p = 1.0 - abs(vLado); vec3 c; float a;
            if (uCapa == 0) { a = clamp(uDormida * (1.0 + 1.6 * (uBrillo - 1.0)), 0.0, 1.0) * (1.0 - L) * smoothstep(0.0, 0.5, p); c = cDormida; }
            else if (uCapa == 1) { a = L * pow(p, 2.6) * uHalo * (1.0 + cal * 0.9) * uBrillo; c = cAcento; }
            else if (uCapa == 3) { a = L * smoothstep(0.0, 0.25, p); c = cBorde; }
            else { a = L * smoothstep(0.0, 0.4, p); c = mix(cAcento, cCaliente, clamp(0.04 + 0.6 * cal * cal + 0.25 * (uBrillo - 1.0), 0.0, 0.85)); }
            if (a < 0.003) discard;
            gl_FragColor = vec4(srgb(c), a);
          }` });
      const m = new THREE.Mesh(geo, mat); m.frustumCulled = false; m.renderOrder = orden; scene.add(m);
      return { mat, base: ancho };
    };
    const o = { f, ip, capas: [capa(0, CFG.falla.dormida_px, 5, false, true)] };
    if (CFG.falla.halo > 0) o.capas.push(capa(1, CFG.falla.halo_px, 6, ES.aditivo, false));
    if (CFG.falla.borde_px) o.capas.push(capa(3, CFG.falla.nucleo_px + CFG.falla.borde_px, 7, false, false));
    o.capas.push(capa(2, CFG.falla.nucleo_px, 8, false, false));
    // flechas del corrimiento (evento «deslizar»): dos carriles de galones, uno a cada lado, en sentidos opuestos
    const mf = new THREE.ShaderMaterial({
      uniforms: { ...uComun(), uAncho: { value: CFG.falla.flechas_px }, cColor: { value: lin(COL.flechas) }, uSentido: { value: 1 },
        uCentro: { value: 0 }, uMedio: { value: 30 }, uPeriodo: { value: 7 }, uFase: { value: 0 }, uAlfa: { value: 0 } },
      vertexShader: VERT_CINTA, transparent: true, depthWrite: false, depthTest: false,
      fragmentShader: `uniform vec3 cColor; uniform float uSentido, uCentro, uMedio, uPeriodo, uFase, uAlfa; varying float vLado, vS;
        void main() {
          float q = (abs(vLado) - 0.6) / 0.34; if (abs(q) > 1.0 || uAlfa <= 0.0) discard;
          float dir = -sign(vLado) * uSentido;                       // corrimiento izquierdo: el lado a la izquierda del trazo va hacia −s (el norte, al oeste)
          float m = dir * (vS - uCentro) / uPeriodo - uFase;
          float galon = 1.0 - smoothstep(0.27, 0.34, fract(m + abs(q) * 0.6));
          float env = 1.0 - smoothstep(uMedio * 0.72, uMedio, abs(vS - uCentro));
          float a = galon * env * uAlfa * (1.0 - smoothstep(0.8, 1.0, abs(q)));
          if (a < 0.003) discard;
          vec3 c = cColor; c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a);
        }` });
    const flechas = new THREE.Mesh(geo, mf); flechas.frustumCulled = false; flechas.renderOrder = 9; flechas.visible = false; scene.add(flechas);
    o.flechas = flechas;
    fallas3d.push(o);
  });
}
// la cabeza de la ruptura: un destello en cada frente mientras avanza
let cabezas = null;
function armarCabezas() {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NR * 2 * 3), 3));
  g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(NR * 2), 1)); g.setAttribute("aAc", new THREE.BufferAttribute(new Float32Array(NR * 2), 1));
  const m = new THREE.ShaderMaterial({ uniforms: { cAcento: { value: lin(COL.acento) }, cSec: { value: lin(COL.secundario) }, cCaliente: { value: lin(COL.caliente) }, uTam: { value: CFG.falla.cabeza_px } },
    transparent: true, depthWrite: false, depthTest: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
    vertexShader: "attribute float aK, aAc; uniform float uTam; varying float vK, vAc; void main(){ vK = aK; vAc = aAc; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_PointSize = uTam * (0.6 + 0.4 * aK); }",
    fragmentShader: `uniform vec3 cAcento, cSec, cCaliente; varying float vK, vAc;
      void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; float a = (exp(-r * r * 7.0) * 0.9 + exp(-r * r * 60.0)) * vK * (1.0 - smoothstep(0.85, 1.0, r)); if (a < 0.003) discard;
        vec3 c = mix(mix(cSec, cAcento, vAc), cCaliente, exp(-r * r * 30.0) * 0.8); c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }` });
  cabezas = new THREE.Points(g, m); cabezas.frustumCulled = false; cabezas.renderOrder = 10; scene.add(cabezas);
}

// ---------- «resaltar» un lugar: se lee con el país entero en cuadro ----------
const NRES = 6; let resaltes = null;
function armarResaltes() {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(NRES * 3), 3));
  g.setAttribute("aK", new THREE.BufferAttribute(new Float32Array(NRES), 1)); g.setAttribute("aFase", new THREE.BufferAttribute(new Float32Array(NRES), 1));
  const m = new THREE.ShaderMaterial({ uniforms: { cSec: { value: lin(COL.secundario) }, cLuz: { value: lin(COL.luces) }, cBorde: { value: lin(COL.linea) }, uTam: { value: CFG.resalte_px }, uAditivo: { value: ES.aditivo ? 1 : 0 } },
    transparent: true, depthWrite: false, depthTest: false, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
    vertexShader: "attribute float aK, aFase; uniform float uTam; varying float vK, vFase; void main(){ vK = aK; vFase = aFase; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_PointSize = aK > 0.0 ? uTam : 0.0; }",
    fragmentShader: `uniform vec3 cSec, cLuz, cBorde; uniform float uAditivo; varying float vK, vFase;
      float anillo(float r, float ph) { float rr = 0.14 + 0.8 * ph, q = (r - rr) / 0.03; return exp(-q * q) * pow(1.0 - ph, 1.3); }
      void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;
        float nucleo = exp(-r * r * 260.0) * 1.2 + exp(-r * r * 38.0) * 0.75 + exp(-r * r * 9.0) * 0.22;
        float an = anillo(r, fract(vFase)) + anillo(r, fract(vFase + 0.5));
        vec3 c = uAditivo > 0.5 ? cSec : mix(cBorde, cLuz, clamp(nucleo, 0.0, 1.0));
        float a = clamp((nucleo + an * 0.95) * vK, 0.0, 1.0) * (1.0 - smoothstep(0.92, 1.0, r)); if (a < 0.003) discard;
        c = mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); gl_FragColor = vec4(c, a); }` });
  resaltes = new THREE.Points(g, m); resaltes.frustumCulled = false; resaltes.renderOrder = 11; scene.add(resaltes);
}

// ---------- luces de los pueblos ----------
let luces = null; const LZ = [];   // {x, y, peso, pieza, id}
function armarLuces() {
  LUCES.forEach((p, ip) => p.puntos.forEach((q) => LZ.push({ x: q[0], y: q[1], peso: q[2], id: q[3], pieza: ip, on: p.encendidas !== false, ac: p.protagonista ? 1 : 0 })));
  if (!LZ.length) return;
  const pos = new Float32Array(LZ.length * 3), peso = new Float32Array(LZ.length), acs = new Float32Array(LZ.length);
  LZ.forEach((l, i) => { const v = V3(l.x, l.y, 0.35); pos.set([v.x, v.y, v.z], 3 * i); peso[i] = l.peso; acs[i] = l.ac; });
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aPeso", new THREE.BufferAttribute(peso, 1));
  g.setAttribute("aInt", new THREE.BufferAttribute(new Float32Array(LZ.length), 1)); g.setAttribute("aAc", new THREE.BufferAttribute(acs, 1));
  const m = new THREE.ShaderMaterial({
    uniforms: { cLuz: { value: lin(COL.luces) }, cAcento: { value: lin(COL.acento) }, cBorde: { value: lin(COL.linea) }, uEsc: { value: 1 }, uKm: { value: CFG.luces.km }, uMin: { value: CFG.luces.min_px }, uMax: { value: CFG.luces.max_px },
      uAditivo: { value: ES.aditivo ? 1 : 0 }, uFuerza: { value: CFG.luces.fuerza } },
    transparent: true, depthWrite: false, depthTest: true, blending: ES.aditivo ? THREE.AdditiveBlending : THREE.NormalBlending,
    vertexShader: `attribute float aPeso, aInt, aAc; uniform float uEsc, uKm, uMin, uMax; varying float vInt, vAc;
      void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv; vInt = aInt; vAc = aAc;
        gl_PointSize = aInt <= 0.001 ? 0.0 : clamp(uKm * (0.45 + 0.75 * aPeso) * uEsc / max(-mv.z, 1.0), uMin, uMax) * (1.0 + 0.18 * max(aInt - 1.0, 0.0)); }`,
    fragmentShader: `uniform vec3 cLuz, cAcento, cBorde; uniform float uAditivo, uFuerza; varying float vInt, vAc;
      vec3 srgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(0.41666)) - 0.055, step(0.0031308, c)); }
      void main(){ float r = length(gl_PointCoord - 0.5) * 2.0; if (r > 1.0) discard;
        if (uAditivo > 0.5) { float a = (exp(-r * r * 4.0) * 0.5 + exp(-r * r * 34.0) * 1.0) * min(vInt, 2.6) * uFuerza * (1.0 - smoothstep(0.8, 1.0, r)); gl_FragColor = vec4(srgb(mix(cLuz, cAcento, vAc)), a); }
        else { float a = (1.0 - smoothstep(0.42, 0.5, r)) * min(vInt, 1.0); vec3 c = mix(mix(cLuz, cAcento, vAc), cBorde, smoothstep(0.26, 0.32, r)); if (a < 0.01) discard; gl_FragColor = vec4(srgb(c), a); } }` });
  luces = new THREE.Points(g, m); luces.frustumCulled = false; luces.renderOrder = 4; scene.add(luces);
}

// ---------- cámara: la función del contrato (cada parámetro con e = −(cos(πu) − 1)/2 entre claves) ----------
const CL = M.camara;
function camaraEn(t) {
  let i = 0; while (i < CL.length - 2 && t > CL[i + 1].t) i++;
  const a = CL[i], b = CL[Math.min(i + 1, CL.length - 1)];
  const u = b.t > a.t ? clamp((t - a.t) / (b.t - a.t)) : 0, e = -(Math.cos(Math.PI * u) - 1) / 2;
  const L = (k) => a[k] + (b[k] - a[k]) * e;
  return { x: L("x"), y: L("y"), alt: L("alt"), dist: L("dist_km"), az: L("azimut"), el: L("elevacion"), fov: L("fov") };
}
let CAM = null;
function ponerCamara(t) {
  const c = CAM = camaraEn(t), az = c.az * Math.PI / 180, el = c.el * Math.PI / 180, hd = c.dist * Math.cos(el);
  camera.fov = c.fov; camera.near = Math.max(0.5, c.dist * 0.02); camera.far = 40000; camera.updateProjectionMatrix();
  NIEBLA.set(Math.max(700, c.dist * 3.2), Math.max(2200, c.dist * 10));
  camera.position.set(c.x + Math.sin(az) * hd, c.alt + c.dist * Math.sin(el), -(c.y - Math.cos(az) * hd));
  camera.up.set(0, 1, 0); camera.lookAt(c.x, c.alt, -c.y); camera.updateMatrixWorld(true);
}

// ---------- eventos: el estado del mundo en t ----------
const EV = M.eventos;
for (const e of EV) if (e.adelanto) { e.t -= e.adelanto; e.dur += e.adelanto; }   // como si ya llevara ese avance
function mundoEn(t) {
  const c = CAM, pxKm = H / (2 * Math.tan(c.fov * Math.PI / 360));   // px por km a 1 km de distancia
  const k = clamp(1 + 70 / c.dist, 1, 2.4);                          // las líneas engordan al acercarse
  // rupturas → uniformes (compartidos por el relieve y las cintas de la falla) y cabezas
  const rup = EV.filter((e) => e.tipo === "ruptura").slice(0, NR);
  const cab = cabezas.geometry.attributes.position, cabK = cabezas.geometry.attributes.aK, cabA = cabezas.geometry.attributes.aAc; cabK.array.fill(0);
  for (let i = 0; i < NR; i++) {
    const e = rup[i];
    if (!e) { uRuptura.uRupT.value[i].set(0, -1); continue; }
    const tr = t - e.t, ip = idxFalla(e.pieza), u = clamp(tr / e.dur);
    uRuptura.uRup.value[i].set(e.s0, e.km_menos, e.km_mas, e.dur); uRuptura.uRupT.value[i].set(Math.max(0, tr), ip);
    if (tr > 0 && tr < e.dur + 0.5) {
      const cad = FALLAS[ip].cadena, fin = suave(e.dur + 0.5, e.dur - 0.1, tr), ini = suave(0, 0.15, tr);
      [[-1, e.km_menos], [1, e.km_mas]].forEach(([sg, alc], j) => {
        if (alc <= 0) return;
        const s = e.s0 + sg * alc * u, [x, y] = puntoEnS(cad, s), p = V3(x, y, 0.4);
        cab.setXYZ(2 * i + j, p.x, p.y, p.z); cabK.setX(2 * i + j, ini * fin); cabA.setX(2 * i + j, FALLAS[ip].protagonista ? 1 : 0);
      });
    }
  }
  cab.needsUpdate = true; cabK.needsUpdate = true; cabA.needsUpdate = true;
  cabezas.material.uniforms.uTam.value = CFG.falla.cabeza_px * k;
  // resaltar una pieza: sube su brillo con un pulso
  const brillo = {};
  for (const e of EV) if (e.tipo === "resaltar" && e.pieza && t >= e.t && t <= e.t + e.dur) {
    const tr = t - e.t; brillo[e.pieza] = 1 + 0.9 * suave(0, 0.3, tr) * suave(e.dur, e.dur - 0.4, tr) * (0.8 + 0.2 * Math.cos(tr / 1.2 * Math.PI * 2));
  }
  fallas3d.forEach((o) => { const b = brillo[o.f.id] || 1; uRelieve.uBrillo.value[o.ip] = b;
    o.capas.forEach((cp, i) => { cp.mat.uniforms.uAncho.value = cp.base * k * (i === 0 ? 1 + 1.8 * (b - 1) : 1); cp.mat.uniforms.uBrillo.value = b; }); });
  for (const cn of cintas) cn.mat.uniforms.uAncho.value = cn.base * clamp(1 + 30 / c.dist, 1, 1.8);
  for (const id in PIEZAS_LINEA) PIEZAS_LINEA[id].mat.uniforms.uAlfa.value = Math.min(1, PIEZAS_LINEA[id].alfa * (brillo[id] || 1) * (brillo[id] ? 1.3 : 1));
  // deslizar: las flechas a los dos lados
  fallas3d.forEach((o) => { o.flechas.visible = false; });
  for (const e of EV) if (e.tipo === "deslizar" && t >= e.t && t <= e.t + e.dur) {
    const o = fallas3d[idxFalla(e.pieza)], U = o.flechas.material.uniforms, tr = t - e.t;
    o.flechas.visible = true; U.uCentro.value = e.s0; U.uSentido.value = e.sentido; U.uMedio.value = e.km / 2; U.uPeriodo.value = e.periodo_km;
    U.uFase.value = tr * e.vel / e.periodo_km; U.uAlfa.value = suave(0, 0.35, tr) * suave(e.dur, e.dur - 0.35, tr); U.uAncho.value = CFG.falla.flechas_px * k;
  }
  // ondas (y los pulsos de «resaltar» un lugar, que son ondas pequeñas)
  const ondas = [];
  for (const e of EV) {
    if (e.tipo === "onda" && t >= e.t && t <= e.t + e.dur) { const u = (t - e.t) / e.dur;
      ondas.push({ x: e.x, y: e.y, pieza: e.pieza ? idxFalla(e.pieza) : -1, r: e.radio_km * (1 - Math.pow(1 - u, 1.6)), k: Math.pow(1 - u, 0.8) * suave(0, 0.06, u) * CFG.onda }); }
  }
  { const P = resaltes.geometry.attributes.position, K = resaltes.geometry.attributes.aK, F = resaltes.geometry.attributes.aFase; K.array.fill(0); let n = 0;
    for (const e of EV) if (e.tipo === "resaltar" && e.pieza === undefined && n < NRES && t >= e.t && t <= e.t + e.dur) {
      const tr = t - e.t, p = V3(e.x, e.y, 0.5);
      P.setXYZ(n, p.x, p.y, p.z); F.setX(n, tr / 1.25); K.setX(n, suave(0, 0.25, tr) * suave(e.dur, e.dur - 0.4, tr)); n++;
    }
    P.needsUpdate = K.needsUpdate = F.needsUpdate = true; }
  for (let i = 0; i < NO; i++) { const o = ondas[i];
    if (o) { uRelieve.uOnda.value[i].set(o.x, -o.y, o.r, o.k); uRelieve.uOndaPieza.value[i] = o.pieza; } else uRelieve.uOnda.value[i].set(0, 0, 0, 0); }
  // luces: encender, apagar, parpadear, resaltar; la onda las aviva al pasar
  if (luces) {
    const A = luces.geometry.attributes.aInt;
    LZ.forEach((l, i) => {
      let v = l.on ? 1 : 0;
      for (const e of EV) {
        const mia = (e.lugares === "todos" || (e.lugares && e.lugares.includes(l.id)));
        if (e.tipo === "encender" && mia) v = v + (1 - v) * suave(0, 1, (t - e.t - hash(i, 3) * e.dur * 0.7) / Math.max(0.05, e.dur * 0.3));
        else if (e.tipo === "apagar" && mia) v = v * (1 - suave(0, 1, (t - e.t - hash(i, 5) * e.dur * 0.7) / Math.max(0.05, e.dur * 0.3)));
        else if (e.tipo === "parpadear" && mia && t >= e.t && t <= e.t + e.dur) { const u = (t - e.t) / e.dur, env = Math.sin(Math.PI * u);
          v = v * (1 - env) + v * env * (hash(i, Math.floor(t * 14)) < 0.45 ? 0.12 : 1.25); }
        else if (e.tipo === "resaltar" && e.lugar && e.lugar === l.id && t >= e.t && t <= e.t + e.dur) v = Math.max(v, 1) + 1.2;
      }
      for (const o of ondas) { const d = o.pieza < 0 ? Math.hypot(l.x - o.x, l.y - o.y) : distCadena(FALLAS[o.pieza].cadena, l.x, l.y), w = 5 + o.r * 0.05;
        v *= 1 + 1.5 * Math.exp(-Math.pow((d - o.r) / w, 2)) * Math.min(1, o.k * 2); }
      A.array[i] = v;
    });
    A.needsUpdate = true; luces.material.uniforms.uEsc.value = pxKm;
  }
  if (cubos) cubosEn(t, ondas);
}
// [estilo:voxel] la falla y las ondas tiñen los cubos (lo que en los demás estilos hace el shader del relieve)
function cubosEn(t, ondas) {
  const { lista, base } = cubos.userData, rup = EV.filter((e) => e.tipo === "ruptura" && t > e.t);
  if (!rup.length && !ondas.length && !cubos.userData.sucio) return;
  const ac = lin(COL.acento), se = lin(COL.secundario), on = lin(COL.onda), c = new THREE.Color();
  lista.forEach((q, i) => {
    c.copy(base[i]);
    for (const e of rup) { const f = FALLAS[idxFalla(e.pieza)]; let g = 0;
      for (let j = 0; j < f.simple.length - 1; j++) { const a = f.simple[j], b = f.simple[j + 1]; if (a[3]) continue;
        const dx = b[0] - a[0], dy = b[1] - a[1], h = clamp(((q.x - a[0]) * dx + (q.y - a[1]) * dy) / Math.max(1e-9, dx * dx + dy * dy));
        const d = Math.hypot(q.x - a[0] - dx * h, q.y - a[1] - dy * h); if (d > 14) continue;
        const s = a[2] + (b[2] - a[2]) * h - e.s0, alc = s < 0 ? e.km_menos : e.km_mas;
        if (Math.abs(s) <= alc * clamp((t - e.t) / e.dur)) g = Math.max(g, Math.exp(-d / 4.5)); }
      if (g > 0) c.lerp(f.protagonista ? ac : se, Math.min(1, g * 1.3)); }
    for (const o of ondas) { const d = o.pieza < 0 ? Math.hypot(q.x - o.x, q.y - o.y) : distCadena(FALLAS[o.pieza].simple, q.x, q.y), w = 4 + o.r * 0.04;
      c.lerp(on, Math.min(0.8, Math.exp(-Math.pow((d - o.r) / w, 2)) * o.k)); }
    cubos.setColorAt(i, c);
  });
  cubos.instanceColor.needsUpdate = true; cubos.userData.sucio = rup.length > 0 || ondas.length > 0;
}
// [/estilo:voxel]

// ---------- cuadro ----------
const _v = new THREE.Vector3();
// proyección de un punto del mundo (km, con su altura ya exagerada) → píxeles; null si queda detrás de la cámara
function proyectar(x, y, z) {
  _v.set(x, z, -y).applyMatrix4(camera.matrixWorldInverse);
  if (_v.z > -camera.near) return null;
  _v.set(x, z, -y).project(camera);
  return [(_v.x + 1) / 2 * W, (1 - _v.y) / 2 * H];
}
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
  await Promise.all([cargarRelieve(), ...(window.__capaFuentes || []).map((f) => document.fonts.load(f))]);
  await document.fonts.ready;
  armarRelieve(); armarLineas(); armarFallas(); armarCabezas(); armarResaltes(); armarLuces();
  ponerCamara(0);
  await renderer.compileAsync(scene, camera);
  renderAt(0);
  const px = new Uint8Array(4), gl = renderer.getContext(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);   // termina el primer cuadro
  window.__maquetaLista = true;
})();
window.addEventListener("hf-seek", (e) => { if (window.__maquetaLista) renderAt(e.detail.time); });
window.__renderAt = renderAt;
