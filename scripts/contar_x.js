#!/usr/bin/env node
/*
 * Hilos · Peso de un texto según X (twitter-text), sin dependencias.
 * ==================================================================
 * Misma lógica que scripts/contar_x.py (peso_x). La función pesoX se puede
 * pegar tal cual dentro de otro archivo (templates/hilo.html la lleva inline).
 *
 * Uso:
 *   node scripts/contar_x.js "texto"      → imprime el peso
 *   node scripts/contar_x.js --vectores   → valida scripts/pruebas/contar_x.json
 * Salida: 0 ok · 1 algún vector falla · 2 uso incorrecto
 */

/* ---- INICIO pesoX (pegable) ---------------------------------------------- */
function pesoX(texto) {
  // Reglas: NFC; cada URL pesa 23; puntos de código en 0–4351, 8192–8205,
  // 8208–8223 y 8242–8247 pesan 1; el resto 2; los emoji compuestos
  // (FE0F, ZWJ+siguiente, tono 1F3FB–1F3FF, keycap 20E3, par regional) son uno y pesan 2.
  var t = String(texto == null ? "" : texto).normalize("NFC");
  var reUrl = /https?:\/\/\S+|www\.\S+|(?<![\p{L}\p{N}\p{M}_])[a-z0-9-]+(\.[a-z0-9-]+)*\.(com|gt|org|net|io|edu|gov|mx|sv|hn|es|info|co)(\/\S*)?/giu;
  var rangos1 = [[0, 4351], [8192, 8205], [8208, 8223], [8242, 8247]];
  var pesoCp = function (cp) {
    for (var k = 0; k < rangos1.length; k++) if (cp >= rangos1[k][0] && cp <= rangos1[k][1]) return 1;
    return 2;
  };
  var esTono = function (cp) { return cp >= 0x1f3fb && cp <= 0x1f3ff; };
  var esRegional = function (cp) { return cp >= 0x1f1e6 && cp <= 0x1f1ff; };
  var pesoPlano = function (s) {
    var cps = Array.from(s, function (c) { return c.codePointAt(0); });
    var i = 0, n = cps.length, total = 0;
    while (i < n) {
      var j = i + 1;
      if (esRegional(cps[i]) && j < n && esRegional(cps[j])) j += 1; // bandera
      while (j < n) {
        if (cps[j] === 0xfe0f || cps[j] === 0x20e3 || esTono(cps[j])) j += 1;
        else if (cps[j] === 0x200d && j + 1 < n) j += 2; // ZWJ + siguiente
        else break;
      }
      total += j - i > 1 ? 2 : pesoCp(cps[i]);
      i = j;
    }
    return total;
  };
  var total = 0, pos = 0, m;
  while ((m = reUrl.exec(t)) !== null) {
    total += pesoPlano(t.slice(pos, m.index)) + 23;
    pos = m.index + m[0].length;
    if (m[0].length === 0) reUrl.lastIndex++;
  }
  return total + pesoPlano(t.slice(pos));
}
/* ---- FIN pesoX ------------------------------------------------------------ */

if (typeof module !== "undefined") module.exports = { pesoX: pesoX };

if (typeof require !== "undefined" && typeof module !== "undefined" && require.main === module) {
  var fs = require("fs");
  var path = require("path");
  var args = process.argv.slice(2);
  if (args[0] === "--vectores") {
    var ruta = args[1] || path.join(__dirname, "pruebas", "contar_x.json");
    var vectores = JSON.parse(fs.readFileSync(ruta, "utf8"));
    var fallos = 0;
    for (var i = 0; i < vectores.length; i++) {
      var v = vectores[i], got = pesoX(v.texto), ok = got === v.peso;
      if (!ok) fallos++;
      console.log((ok ? "OK   " : "FALLO") + " " + String(got).padStart(3) + " (esperado " + String(v.peso).padStart(3) + ")  " + JSON.stringify(v.texto).slice(0, 70));
    }
    console.log("[contar_x.js] " + vectores.length + " vectores · " + fallos + " fallo(s)");
    process.exit(fallos ? 1 : 0);
  }
  if (args.length && args[0] !== "-") {
    console.log(pesoX(args.join(" ")));
  } else if (!process.stdin.isTTY) {
    var texto = fs.readFileSync(0, "utf8");
    if (texto.endsWith("\n")) texto = texto.slice(0, -1);
    console.log(pesoX(texto));
  } else {
    console.error("Uso: node scripts/contar_x.js \"texto\" | --vectores [ruta.json]");
    process.exit(2);
  }
}
