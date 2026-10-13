/*
 * Ruta de Playwright común a scripts/render.js (tarjetas) y scripts/render_informe.js (informes).
 *
 * Sirve `**\/fonts/*.woff2` desde design/fonts/ con cabeceras CORS (Chromium aplica CORS a las
 * fuentes de file://) y aborta cualquier otra petición que no sea file:/data:/blob:/about:.
 * Devuelve las listas que el llamador revisa al terminar: `externas` (URLs bloqueadas, prohibidas)
 * y `fuentesFaltantes` (woff2 pedidos que no están en design/fonts/).
 */
const path = require("path");
const fs = require("fs");

const FONTS_DIR = path.join(path.dirname(__dirname), "design", "fonts");
const PROTOCOLOS_LOCALES = /^(file|data|blob|about):/;
const RE_FUENTE = /\/fonts\/([^/?#]+\.woff2)(\?.*)?$/;

async function rutaFuentes(page) {
  const externas = [], fuentesFaltantes = [];
  await page.route("**", (route) => {
    const url = route.request().url();
    const mf = url.match(RE_FUENTE);
    if (mf) {
      const archivo = path.join(FONTS_DIR, mf[1]);
      if (!fs.existsSync(archivo)) { fuentesFaltantes.push(mf[1]); return route.abort(); }
      return route.fulfill({ status: 200, contentType: "font/woff2", body: fs.readFileSync(archivo), headers: { "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store" } });
    }
    if (PROTOCOLOS_LOCALES.test(url)) return route.continue();
    externas.push(url);
    return route.abort();
  });
  return { externas, fuentesFaltantes };
}

module.exports = { rutaFuentes, FONTS_DIR };
