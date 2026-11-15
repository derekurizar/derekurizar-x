// MODO PLACA de la maqueta 3D (/video-3d): el motor de los estilos de Blender (arquitecto, diorama, papel).
// El mundo no se dibuja aquí: llega ya renderizado por scripts/maqueta_blender.py como #placa, que es
//   · un <video> (assets/placa.mp4) en el render: HyperFrames lo lleva cuadro a cuadro, como cualquier clip de video, o
//   · fotos apiladas (.placa-foto, una por cuadro pedido) en los cuadros sueltos de `maqueta3d.py cuadro`.
// Este archivo solo mueve la capa 2D (capa.js) como función pura de t, igual que motor.js: window.__capa(t, proyectar).
// Las marcas no se proyectan con una cámara: scripts/maqueta3d.py ya calculó dónde cae cada una en cada cuadro de su
// ventana (MAQUETA.anclas: [{n0, p: [[px, py] | null, …]}], con la misma cámara que Blender, comprobada al píxel).
(function () {
  const M = window.MAQUETA, FPS = M.fps, A = M.anclas || [];
  const fotos = [...document.querySelectorAll('.placa-foto')].map((el) => ({ el, n: +el.dataset.n }));
  let cuadro = 0;
  // el cuadro n de la placa está en t = n / fps: la marca i cae en A[i].p[n − n0]
  const proyectar = (x, y, z, i) => { const a = A[i]; if (!a) return null; const p = a.p[cuadro - a.n0]; return p || null; };
  function renderAt(t) {
    cuadro = Math.round(t * FPS);
    if (fotos.length) {   // cuadros sueltos: se ve la foto del cuadro más cercano
      let mejor = fotos[0];
      for (const f of fotos) if (Math.abs(f.n - cuadro) < Math.abs(mejor.n - cuadro)) mejor = f;
      for (const f of fotos) f.el.style.visibility = f === mejor ? 'visible' : 'hidden';
      cuadro = mejor.n;
    }
    if (window.__capa) window.__capa(t, proyectar);
  }
  // contrato HyperFrames (el mismo que motor.js): listo cuando cargaron las fuentes y las fotos
  window.__hf = window.__hf || {};
  window.__hf.buildReady = window.__hf.buildReady || {};
  window.__hf.buildReady['maqueta'] = (async () => {
    await Promise.all([...(window.__capaFuentes || []).map((f) => document.fonts.load(f)), ...fotos.map((f) => f.el.decode().catch(() => {}))]);
    await document.fonts.ready;
    renderAt(0);
    window.__maquetaLista = true;
  })();
  window.addEventListener('hf-seek', (e) => { if (window.__maquetaLista) renderAt(e.detail.time); });
  window.__renderAt = renderAt;
})();
