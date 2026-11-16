// Pieza «edificios» (ficha: edificios.json): cada edificio extruido con su altura real (m) desde el suelo, en una sola
// malla: muros y techo con la luz del estilo horneada en el color (sin luces en la escena: el cuadro es puro), un tono
// por edificio (más claro el techo cuanto más alto) y, en los estilos de línea (contorno, plano), sus aristas en línea.
// `destacado` (el edificio de `destacar`) va en el acento todo el video; «resaltar» con `elemento` enciende UNO en el
// acento mientras dura (ctx.cuadro.elementos[id] = [{i, k}]); «resaltar» la pieza entera la aclara.
(function (MAQ) {
  MAQ.PIEZAS.edificios = {
    orden: 8,
    armar(ctx, piezas) {
      const { THREE, malla, tonos, sombra, hash, ES, scene, lin, COL } = ctx;
      return piezas.map((p, np) => {
        const acc = malla.nueva(), rangos = [], aristas = [], luz = [], c = new THREE.Color(), hmax = Math.max(12, ...p.edificios.map((e) => e[0]));
        p.edificios.forEach((e, i) => {
          const h = e[0], pts = [];
          for (let k = 1; k + 1 < e.length; k += 2) pts.push(new THREE.Vector2(e[k], e[k + 1]));
          if (pts.length < 3) { rangos.push([acc.pos.length / 3, 0]); return; }
          if (THREE.ShapeUtils.isClockWise(pts)) pts.reverse();          // antihorario: las normales de los muros miran afuera
          let base = Infinity; for (const q of pts) base = Math.min(base, ctx.altura(q.x, q.y));
          base -= 0.5;
          const top = base + 0.5 + h, ini = acc.pos.length / 3, var_ = 0.9 + 0.2 * hash(i, 17 + np);
          const muro = (i === p.destacado ? tonos.acento.clone().multiplyScalar(0.75) : tonos.muro.clone()).multiplyScalar(var_);
          const techo = i === p.destacado ? tonos.acento.clone() : tonos.techo.clone().lerp(tonos.muro, 0.35 * (1 - Math.min(1, h / hmax))).multiplyScalar(var_);
          // muros: un cuadrilátero por lado
          for (let k = 0; k < pts.length; k++) {
            const a = pts[k], b = pts[(k + 1) % pts.length], dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy) || 1;
            const s = sombra(dy / L, 0, dx / L);                            // normal afuera (dy, −dx) en el plano → three (x, 0, −y)
            c.copy(muro).multiplyScalar(s);
            const q = acc.pos.length / 3;
            acc.pos.push(a.x, base, -a.y, b.x, base, -b.y, b.x, top, -b.y, a.x, top, -a.y);
            for (let r = 0; r < 4; r++) { acc.col.push(c.r, c.g, c.b); luz.push(s); }
            acc.idx.push(q, q + 1, q + 2, q, q + 2, q + 3);
            if (ES.modo === 2 || ES.modo === 4) aristas.push(a.x, base, -a.y, a.x, top, -a.y, a.x, top, -a.y, b.x, top, -b.y);
          }
          // techo
          const st = sombra(0, 1, 0); c.copy(techo).multiplyScalar(st);
          const q = acc.pos.length / 3;
          for (const v of pts) { acc.pos.push(v.x, top, -v.y); acc.col.push(c.r, c.g, c.b); luz.push(st * 1.1); }
          for (const tr of THREE.ShapeUtils.triangulateShape(pts, [])) acc.idx.push(q + tr[0], q + tr[1], q + tr[2]);
          rangos.push([ini, acc.pos.length / 3 - ini]);
        });
        const mat = malla.material(), mesh = malla.poner(acc, mat, 2);
        if (aristas.length) {
          const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(aristas), 3));
          const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: lin(COL.linea), transparent: true, opacity: ES.modo === 4 ? 0.85 : 0.7 }));
          l.frustumCulled = false; l.renderOrder = 3; scene.add(l);
        }
        const atr = mesh.geometry.attributes.color;
        return { id: p.id, mat, atr, base: Float32Array.from(atr.array), rangos, luz, pintados: [] };
      });
    },
    en(t, lista, ctx) {
      const { tonos } = ctx;
      for (const s of lista) {
        s.mat.uniforms.uBrillo.value = ctx.cuadro.brillo[s.id] ? 1 + 0.25 * (ctx.cuadro.brillo[s.id] - 1) : 1;
        const els = ctx.cuadro.elementos[s.id] || [];
        if (!els.length && !s.pintados.length) continue;
        const A = s.atr.array;
        for (const i of s.pintados) { const [a, n] = s.rangos[i]; A.set(s.base.subarray(3 * a, 3 * (a + n)), 3 * a); }   // lo de antes vuelve a su color
        s.pintados = [];
        for (const el of els) {
          const r = s.rangos[el.i]; if (!r) continue;
          const [a, n] = r, k = Math.min(1, el.k);
          const ac = [tonos.acento.r, tonos.acento.g, tonos.acento.b];
          for (let v = a; v < a + n; v++) for (let j = 0; j < 3; j++) A[3 * v + j] = s.base[3 * v + j] + (ac[j] * s.luz[v] - s.base[3 * v + j]) * k;
          s.pintados.push(el.i);
        }
        s.atr.needsUpdate = true;
      }
    },
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
