#!/usr/bin/env python3
"""Pruebas de las reglas del 2026-11-10 (sin render): .srt sin solapes, «Sígueme» de la mitad (V25), la pregunta en
pantalla (P6), cifras en palabras en un caption (V5), tics sueltos, la escalera (H25), la imagen (H26), la promesa de la
serie (SE1) y los efectos y las transiciones del video largo. Exit 0 ok · 1 falla."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import video as VD  # noqa: E402
import historia as HI  # noqa: E402
import serie as SE  # noqa: E402
import youtube as YT  # noqa: E402

F = []


def ok(cond, que):
    if not cond:
        F.append(que)


def pal(texto, t0=0.0, paso=0.3):
    return [{"text": w, "start": round(t0 + i * paso, 3), "end": round(t0 + i * paso + 0.25, 3)} for i, w in enumerate(texto.split())]


def escena(n, tipo, dur, texto="uno dos tres cuatro cinco seis.", **kw):
    return dict({"n": n, "tipo": tipo, "dur": dur, "palabras": pal(texto), "eventos": [], "sfx": []}, **kw)


# .srt: nunca un bloque termina después de que empieza el siguiente; sin sobras de 1–2 palabras si caben con el vecino
E = [escena(1, "foto", 6, "Era el 21 de octubre de 2006, y los clientes llegaban a cajeros y agencias de la SIB."),
     escena(2, "foto", 5, "En juego estaba el dinero. Guatemala.")]
B = VD.bloques_srt(E, [0, 5.7])
ok(not VD.revisar_srt(B), "srt: hay solapes o líneas largas: %s" % VD.revisar_srt(B))
ok(all(a["end"] <= b["start"] for a, b in zip(B, B[1:])), "srt: un bloque pisa al siguiente")
ok(not any(len(b["texto"].split()) <= 2 for b in B), "srt: queda una sobra de ≤ 2 palabras")

# V5: una cifra en palabras en un caption
ok(VD.RE_CIFRA_EN_PALABRAS.search("puso mil seiscientos millones de quetzales"), "V5: no ve «mil seiscientos millones»")
ok(not VD.RE_CIFRA_EN_PALABRAS.search("un millón de cuentas y Q1,600 millones"), "V5: marca prosa normal")

# V25: el «Sígueme» cae en la escena del medio, no en gancho, cierre ni una escena con chip arriba
E = [escena(1, "gancho", 6), escena(2, "foto", 12), escena(3, "foto", 14, chip={"texto": "Ejemplo"}), escena(4, "foto", 14),
     escena(5, "golpe", 10), escena(6, "cierre", 12)]
ok(VD.marcar_seguir(E) == [], "V25: no encontró dónde poner el «Sígueme»")
con = [S["n"] for S in E if S.get("seguir")]
ok(len(con) == 1 and con[0] not in (1, 3, 6), "V25: quedó en %s" % con)
ok(VD.marcar_seguir([escena(1, "gancho", 8), escena(2, "cierre", 10)]) == [], "V25: un video corto no lo lleva")
E2 = [escena(1, "gancho", 20), escena(2, "foto", 4), escena(3, "foto", 4), escena(4, "cierre", 30)]
ok(any("V25" in x for x in VD.marcar_seguir(E2)), "V25: no falla cuando ninguna escena puede llevarlo")

# P6: sin pregunta falla (trabajo nuevo), con pregunta pasa; la promesa después del segundo 10 falla
st = {"tipo": "historia", "fecha": VD.P6_DESDE}
esc = [{"texto": "La Espiga reabrió bajo una carpa en Guatemala."}, {"texto": "¿Cómo se quedó sin sucursales? Fue en 1976."}]
p = {"texto": "¿Cómo se quedó sin sucursales?", "en": 2, "pago": 9}
ok(any("P6" in x for x in VD.revisar_pregunta({}, st, p, esc)), "P6: no exige promesa.pregunta")
ok(VD.revisar_pregunta({}, st, dict(p, pregunta="¿Cómo se quedó La Espiga sin sucursales?"), esc) == [], "P6: rechaza una pregunta buena")
ok(any("P6" in x for x in VD.revisar_pregunta({}, st, dict(p, pregunta="¿Qué pasó después de todo esto que nadie esperaba ver venir?"), esc)),
   "P6: acepta una pregunta larga y sin sujeto")
largo = [{"texto": "La Espiga reabrió bajo una carpa en Guatemala."},
         {"texto": "Fue en 1976, cuando el terremoto tiró el horno y la familia entera tuvo que sacar las bandejas a la calle durante "
                   "semanas para que el barrio no se quedara sin pan. ¿Cómo se quedó sin sucursales?"}]
ok(any("empieza a los" in x for x in VD.revisar_pregunta({}, st, dict(p, pregunta="¿Cómo se quedó La Espiga sin sucursales?"), largo)),
   "P6: no ve la promesa después del segundo 10")
ok(VD.revisar_pregunta({}, dict(st, fecha="2026-11-01"), p, esc) == [], "P6: un trabajo anterior a la regla debe dar solo aviso")
# la pregunta en pantalla: promesa, bisagra y pago (este con check)
E = [escena(k, "foto", 10) for k in range(1, 8)]
n = VD.marcar_pregunta(E, {"promesa": {"pregunta": "¿Cómo cayó?", "texto": "uno dos", "en": 2, "pago": 6},
                           "bisagra": {"texto": "tres cuatro", "en": 4, "pago": 6}})
ok(n == 3 and E[5]["pregunta"]["pagada"] and not E[1]["pregunta"]["pagada"], "P6: la pregunta no quedó en promesa, bisagra y pago")

# tics sueltos
E = [escena(1, "foto", 10, sfx=[{"t": 1, "id": "tic"}, {"t": 3, "id": "tic"}, {"t": 8, "id": "tic"}])]
ok(VD.ralear_tics(E) == 1 and len(E[0]["sfx"]) == 2, "tics: no quitó el tic suelto a 2 s del anterior")

# H25: un tercio sin nada falla; con un peldaño por tercio pasa
HI.TRABAJO_ACTUAL = None
esc9 = [{"texto": "Una oración corta de prueba."} for _ in range(9)]
g = {"promesa": {"en": 2, "pago": 9}, "bisagra": {"en": 2, "pago": 9}}
ok(any("H25" in x for x in HI.escalera(g, {}, esc9)), "H25: no ve el tercio vacío")
esc9[4]["giro"] = True
ok(HI.escalera(g, {}, esc9) == [], "H25: rechaza un guion con un peldaño por tercio")

# H26: una foto fija de más de 12 s
larga = [{"tipo": "foto", "texto": " ".join(["palabra"] * 45) + "."}, {"tipo": "cita", "texto": "Dijo algo."}]
ok(any("H26" in x for x in HI.variedad_de_imagen(larga, {})), "H26: acepta una foto fija de más de 12 s")

# SE1: el plan sin promesa de la serie ni en_juego falla
partes = [{"n": k, "titulo": "Parte %d" % k, "pregunta": "¿Qué pasó %d?" % k} for k in (1, 2, 3)]
f, _ = SE.revisar_plan({"serie": {"partes": partes}}, "historia")
ok(any("serie.promesa" in x for x in f) and any("en_juego" in x for x in f), "SE1: no exige serie.promesa ni en_juego")

# el video largo: sin efecto de entrada entre escenas de la misma parte y un tope por minuto
E = [escena(k, "foto", 10, origen="P1.e%d" % k, sfx=[{"t": 0.0, "id": "whoosh"}, {"t": 2.0, "id": "tic"}]) for k in range(1, 7)]
antes, despues = YT.ralear_sfx_largo(E, 60)
ok(antes == 12 and despues <= 6 and not any(x["id"] == "whoosh" for S in E[1:] for x in S["sfx"]), "largo: efectos %d → %d" % (antes, despues))
# transiciones con sentido: el año avanza → empuja a la izquierda; un documento → hoja encima
E = [escena(1, "foto", 8, origen="P1.e1", transicion=None), escena(2, "foto", 8, origen="P1.e2", transicion="fade"),
     escena(3, "cita", 8, origen="P1.e3", transicion="fade", H={"documento": True})]
YT.transiciones_con_sentido(E, {"P1.e1": {"hechos": ["a"]}, "P1.e2": {"hechos": ["b"]}}, {"a": {"fecha": "2014-05"}, "b": {"fecha": "2015"}})
ok(E[1]["transicion"] == VD.TRANSICIONES["avanza"] and E[2]["transicion"] == "coverup", "largo: transiciones %s" % [S["transicion"] for S in E])

# V26: una cifra dicha sin señal en pantalla se avisa; con un evento a su lado, no; los años no cuentan
S = escena(2, "foto", 10)
S["palabras"] = [{"text": "debía", "start": 1.0, "end": 1.3}, {"text": "US$180", "start": 4.0, "end": 4.5, "num": True},
                 {"text": "2006,", "start": 6.0, "end": 6.4, "num": True}]
S["eventos"] = [{"t": 0.4, "tipo": "titular"}]
ok(VD.sin_senal(S) == [("US$180", 4.0)], "V26: %s" % VD.sin_senal(S))
S["eventos"].append({"t": 4.2, "tipo": "cifra"})
ok(VD.sin_senal(S) == [], "V26: avisa de una cifra que sí se señala")

# H26: `ruta` son 2–4 departamentos distintos en una escena foto
ok(any("ruta" in x for x in HI.variedad_de_imagen([{"tipo": "foto", "texto": "Corto.", "ruta": ["Escuintla"]}], {})), "H26: acepta una ruta de un solo lugar")
ok(not any("ruta" in x for x in HI.variedad_de_imagen([{"tipo": "foto", "texto": "Corto.", "ruta": ["Escuintla", "Guatemala"]}], {})),
   "H26: rechaza una ruta válida")
# el adelanto del largo: una frase literal de una escena que queda en el video, de 3–9 s
S0 = {"dur": 14.0, "palabras": pal("antes de eso yo le entregué cinco millones de quetzales al presidente en su casa y luego nada", 0.4, 0.5)}
it, f_ = YT.adelanto_de({"adelanto": {"ref": "P6.e5", "texto": "yo le entregué cinco millones de quetzales al presidente"}},
                        {"P6.e5": {"parte": 6, "n": 5, "tipo": "cita"}}, {(6, 5): S0}, [{"k": "escena", "ref": "P6.e5"}])
ok(it and not f_ and 3 <= it["dur"] <= 9 and it["k"] == "adelanto", "adelanto: %s %s" % (it, f_))
_, f_ = YT.adelanto_de({"adelanto": {"ref": "P6.e5", "texto": "le entregué 5,000,000"}}, {"P6.e5": {"parte": 6, "n": 5, "tipo": "cita"}},
                       {(6, 5): S0}, [{"k": "escena", "ref": "P6.e5"}])
ok(any("literal" in x for x in f_), "adelanto: acepta un texto que la voz no dice")

# m093: «dijo esto:» antes de una cita no deja «:.» en el prompt de la secuencia
u = VD.unir_secuencia(["Monzón lo dijo así:", "Yo le entregué cinco millones."])
ok(":." not in u and u == "Monzón lo dijo así: Yo le entregué cinco millones.", "m093: %r" % u)
# m089: una sigla al final de una oración tiene su margen (V20)
ok(VD.SIGLA_S_FINAL > 0, "m089: SIGLA_S_FINAL")
# m098: SE13 existe y compara contra las partes anteriores
ok(callable(SE.citas_repetidas) and SE.citas_repetidas({}, 1, None) == [], "m098: SE13")

for x in F:
    print("FALLA", x)
print("[reglas 2026-11-10] %s" % ("ok" if not F else "%d fallas" % len(F)))
sys.exit(1 if F else 0)
