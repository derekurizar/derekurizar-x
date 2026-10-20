# Remesas frente a todo lo que recauda la SAT

- **Fecha:** 2026-10-11
- **Slug:** remesas-vs-recaudacion-sat
- **Tipo:** dato (una tarjeta)
- **Paleta:** cielo
- **Gancho:** giro_inversion
- **Dato:** Las remesas ya son 1.69 veces lo que cobra la SAT; hasta 2016 eran menos
- **Plantilla:** linea
- **Tesis:** En 2025 las remesas, convertidas a quetzales, fueron 1.69 veces la recaudación tributaria de la SAT; de 2004 a 2016 fueron menos que los impuestos y desde 2017 los superan.
- **Gate mecánico:** ok
- **Estado:** listo (la publicación en X es manual)

## Tuit (232 de peso X)

Hasta 2016, Guatemala cobraba más en impuestos de lo que recibía en remesas.

Desde entonces la balanza se volteó y no ha vuelto atrás: lo que mandan los migrantes a sus familias ya pesa más que todo lo que recauda la SAT en un año.

[📸 dato.png — Gráfico de línea con la razón entre las remesas familiares (convertidas a quetzales) y la recaudación tributaria de la SAT, por año, de 2004 a 2025. De 2004 a 2016 la razón estuvo por debajo de 1 (mínimo de 0.81 veces en 2011); en 2017 pasó a 1.03 veces y subió hasta 1.69 veces en 2025, el valor más alto de la serie. Fuente: cálculo propio con datos de Banguat (remesas y tipo de cambio) y SAT (recaudación tributaria).]

## Alt-text

Gráfico de línea con la razón entre las remesas familiares (convertidas a quetzales) y la recaudación tributaria de la SAT, por año, de 2004 a 2025. De 2004 a 2016 la razón estuvo por debajo de 1 (mínimo de 0.81 veces en 2011); en 2017 pasó a 1.03 veces y subió hasta 1.69 veces en 2025, el valor más alto de la serie. Fuente: cálculo propio con datos de Banguat (remesas y tipo de cambio) y SAT (recaudación tributaria).

## Por qué impacta

Durante 13 años la SAT recaudó más de lo que mandaban los migrantes; desde 2017 la relación se invirtió y en 2025 llegó a su punto más alto en 22 años.

## Candidatas consideradas

- **elegida** · Razón remesas (en Q) / recaudación tributaria SAT, anual 2004-2025 — La serie de 22 años muestra el giro: por debajo de 1 hasta 2016, encima desde 2017 y máximo en 2025. Contiene el 1.69 de dat-c01 y además el cruce. Segunda fuente no independiente. (dat-c02, puntaje 19)
- Remesas familiares 2025 convertidas a quetzales como múltiplo de la recaudación tributaria SAT 2025 — Mismo 1.69 que dat-c02, pero solo un año: pierde el cruce de 2017. Su cifra va dentro de la tarjeta como último punto de la serie. (dat-c01, puntaje 19)
- Remesas 2025 en quetzales frente al presupuesto vigente del Estado 2026 — Mezcla remesas 2025 con el presupuesto vigente 2026 (años distintos) y el presupuesto llega por prensa, no por la fuente primaria. (dat-c06, puntaje 18)
- Remesas enero-agosto 2026 en quetzales como múltiplo de la recaudación tributaria SAT enero-agosto 2026 — Año parcial (enero-agosto 2026) sin el par comparable de 2025: no dice si la brecha crece o se cierra. (dat-c05, puntaje 17)
- Remesas acumuladas enero-septiembre 2026 frente al total de 2023 — Actual pero comparación débil: superar un año entero con nueve meses es esperable cuando las remesas crecen cada año. (dat-c07, puntaje 17)
- Ingreso de divisas por remesas familiares, total 2025 — Cifra macro suelta en dólares, ya muy difundida; sin comparación no sorprende. (dat-c03, puntaje 12)
- Tipo de cambio compra promedio ponderado del Mercado Institucional de Divisas, promedio 2025 — Es un insumo de la conversión (tipo de cambio), no un hallazgo. (dat-c04, puntaje 9)

## Datos clave (cifras usadas en la tarjeta)

| id | Concepto | Valor | Unidad | Año | Veredicto | Fuente | Aparece en |
|---|---|---|---|---|---|---|---|
| dat-c01 | Remesas familiares 2025 convertidas a quetzales como múltiplo de la recaudación tributaria SAT 2025 | 1.694 | veces la recaudación SAT | 2025 | verificada · 2ª fuente no indep. | Cálculo propio con Banguat (remesas familiares, Cuadro 1; tipo de cambio imm02) y SAT (rimpa.xlsx) | dato.png |
| dat-c02 | Razón remesas (en Q) / recaudación tributaria SAT, anual 2004-2025 | 1.694 | veces | 2025 | verificada · 2ª fuente no indep. | Cálculo propio con Banguat (remesas, TC imm02) y SAT (rimpa.xlsx) | dato.png |

<details><summary>Cifras verificadas no usadas (5)</summary>

| id | Concepto | Valor | Unidad | Año | Fuente |
|---|---|---|---|---|---|
| dat-c03 | Ingreso de divisas por remesas familiares, total 2025 | 25530.23 | millones de US$ | 2025 | Banco de Guatemala, Cuadro 1 Ingreso de Divisas por Remesas Familiares (remfam2002_2026.xlsx) |
| dat-c04 | Tipo de cambio compra promedio ponderado del Mercado Institucional de Divisas, promedio 2025 | 7.66134 | Q por US$ | 2025 | Banco de Guatemala, imm02 (Tipo de cambio compra promedio ponderado, promedio del mes 1995-2026) |
| dat-c05 | Remesas enero-agosto 2026 en quetzales como múltiplo de la recaudación tributaria SAT enero-agosto 2026 | 1.59 | veces la recaudación SAT | 2026 | Cálculo propio con Banguat (remesas, TC imm02) y SAT (rimpa.xlsx, columna 2026 'Datos a agosto') |
| dat-c06 | Remesas 2025 en quetzales frente al presupuesto vigente del Estado 2026 | 1.17 | veces el presupuesto vigente 2026 | 2025/2026 | Cálculo propio con Banguat (remesas, TC) y Prensa Libre con datos de Transparencia Presupuestaria (Minfin) |
| dat-c07 | Remesas acumuladas enero-septiembre 2026 frente al total de 2023 | 20015.7 | millones de US$ | 2026 | Banco de Guatemala, Cuadro 1 Ingreso de Divisas por Remesas Familiares (remfam2002_2026.xlsx) |

</details>

## Lo que este dato NO afirma

- No afirma que las remesas sean ingresos del Estado ni que sustituyan a los impuestos: son transferencias privadas a hogares.
- No atribuye la subida de la razón a una causa (migración, tipo de cambio o recaudación).
- No compara poder adquisitivo: es una razón entre montos corrientes en quetzales de cada año.

## Incertidumbre declarada

- La segunda fuente reproduce la primaria; sin verificación independiente.
- Banguat no publica remesas en quetzales: la conversión con el tipo de cambio promedio mensual es cálculo propio.
- 2026 (enero-agosto, 1.59 veces) queda fuera de la serie por ser año parcial.

## Fuentes

**En el pie de la tarjeta:**

- Cálculo propio con Banguat (remesas y tipo de cambio) y SAT

**De las cifras usadas:**

- Cálculo propio con Banguat (remesas familiares, Cuadro 1; tipo de cambio imm02) y SAT (rimpa.xlsx)
- Cálculo propio con Banguat (remesas, TC imm02) y SAT (rimpa.xlsx)

**Otras consultadas:**

- Banco de Guatemala — Ingreso de divisas por remesas familiares (remfam2002_2026.xlsx) — https://banguat.gob.gt/sites/default/files/banguat/estaeco/remesas/remfam2002_2026.xlsx
- Banco de Guatemala — Tipo de cambio compra promedio ponderado MID, promedio del mes (imm02) — https://banguat.gob.gt/sites/default/files/banguat/imm/imm02.htm
- SAT — Recaudación de Ingresos Tributarios 2004-2026 (rimpa.xlsx) — https://portal.sat.gob.gt/portal/descarga/1741/estadisticas-tributarias/5151/rimpa.xlsx
- Prensa Libre — ejecución presupuestaria primer trimestre 2026 (presupuesto vigente) — https://www.prensalibre.com/guatemala/politica/ejecucion-presupuestaria-del-organismo-ejecutivo-alcanza-el-18-62-en-primer-trimestre-del-2026/
