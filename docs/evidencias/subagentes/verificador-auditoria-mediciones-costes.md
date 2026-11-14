# Auditoría independiente: complejidad, rendimiento y costes (feature 011 mediciones-costes)

Alcance: solo lectura. No se ha ejecutado la suite de integración, no se ha tocado `docs/evidencias/consumidor-idempotente/` ni se ha corregido nada. Rutas relativas a la raíz del repositorio.

Verificado por mí (scripts de lectura sobre `resultados.json`, no tomado del implementador):
- `resultados.json` tiene 102 mediciones (etiqueta SINTETICO, semilla 20251113, tamaños 1.000/10.000/100.000, 15 repeticiones); `planes/` tiene 60 archivos.
- Las 102 filas de `tablas.md` coinciden con la mediana de `resultados.json` (0 discrepancias) y cada mediana coincide con la recalculada desde `samples_ms`.
- Todos los ids citados entre corchetes en `escalado.md` y `teoria_vs_observado.md` existen; las cifras citadas coinciden (los pocos avisos del script eran falsos positivos de listas de ids con `server_ms` o selectividad).
- Razones recalculadas: lista ×10,7 y ×16,4; construcción del `dict` ×12,3 y ×21,6 en tiempo, ×8,0 y ×18,5 en memoria (pico 5.632,09 KiB); pg_seq/pg_index 32,7; naive/STRtree 3,15 (mixto), 3,75 y 3,91 (océano); 10^8 puntos = 32,0 min naive y 10,2 min STRtree; 163.857 puntos/s; ida y vuelta 0,1446 ms y 4,0 h con lote 1; 33,8 GiB, 20,3 GiB, 13,5 GiB, 44,3 GiB y 101,5 GiB a 10^8 filas; Q4 de un día a 10^8 filas = 199 ms. Todo cuadra.
- `git diff` de `specs/001-contratos-y-modelo/contracts` y `docs/enunciado`: vacío. Lo único modificado en el árbol es `docs/planificacion/01-checklist-requisitos.md`; lo no rastreado son los archivos previos de `docs/evidencias/consumidor-idempotente/` (anteriores a esta auditoría).

## Recálculo de costes

| Cifra | Cálculo mío | Documento | Resultado |
|---|---|---|---|
| Tarifa | (0,11321+0,01986) x 1,0511 x 1,21 = 0,16924 | 0,169 | coincide |
| Hardware | 1100/48 = 22,917 | 22,92 | coincide |
| Electricidad A / B | 0,1 kW x 360 h x 0,169 = 6,084; x 720 h = 12,168 | 6,08 / 12,17 | coincide |
| Almacenamiento | 47.160.343 B = 0,043922 GiB = 0,04716 GB; /1820 x 22,9 = 0,00059 | 0,0006 | coincide |
| Dominio | 22/12 = 1,833 | 1,83 | coincide |
| Total imputado A | 22,917+6,084+0,0006+30+1,833 = 60,835 | 60,8 | coincide |
| Total imputado B | 22,917+12,168+0,0006+30+1,833 = 66,919 | 66,9 | coincide |
| Efectivo A / B | 6,084+1,833 = 7,917; 12,168+1,833 = 14,001 | 7,9 / 14,0 | coincide |
| Transferencia | 107162+2762+72 = 109.996 B/petición; x10 = 1.099.960 B/visita (1,049 MiB; 0,0010244 GiB) | idem | coincide |
| 5 / 10 visitas | 5.499.800 B = 5,245 MiB = 0,00512 GiB; 10.999.600 B = 10,49 MiB = 0,01024 GiB | 5,2 / 10,5 MiB | coincide |
| Desarrollo | 72 h x 15 = 1.080; rango 54-90 h = 810-1.350 | idem | coincide |

## Tabla requisito, evidencia, veredicto, hueco

| Requisito | Evidencia (archivo:línea) | Veredicto | Hueco y cómo cerrarlo |
|---|---|---|---|
| >=3 operaciones y medio vs peor caso | `docs/evidencias/mediciones/teoria_vs_observado.md:5` (definición de medio/peor), `:9-15` (búsqueda), `:28-32` (geografía), `:48-52` (ventanas) | Cumple | Ninguno. El caso `dict` y STRtree dice con honestidad que el peor caso teórico no se observa (`:22`, `:40`). |
| Tiempo y memoria con >=3 tamaños, equipo, procedimiento, resultados | `tablas.md:3-5`, `:67-80`; `equipo.md:5-39`; `procedimiento.md:12-37`; `resultados.json` (102 mediciones) | Cumple (memoria parcial en alcance) | La memoria (tracemalloc) solo se mide en construcción del `dict` y en geografía; consultas SQL y búsquedas con lista no tienen pico (`no aplica`). Declararlo en una línea en `procedimiento.md` o `tablas.md`. |
| Comparación secuencial vs diccionario y sin/con índice | `teoria_vs_observado.md:9-15` (lista, dict, pg_seq, pg_index); `:48-52`; `indices.md`; `planes/` | Cumple | Ninguno. |
| Sintéticos marcados y aparte; datos reales intactos | `README.md:3`; `tablas.md:1-3`; `aislamiento.md:1-18`; `T093_comprobaciones.txt` (`bench` NULL, 0 filas de bench, 18302); `T087_corrida.txt:30` | Cumple | Ninguno. |
| Razonamiento a 10^8 | `escalado.md:12-89` (6 puntos con fórmula, SUPUESTO) | Cumple | Ninguno. Declara que no se midió disco ni escrituras (`escalado.md:9-10`, `:106`). |
| Costes: 6 categorías, etiqueta medido/supuesto/estimado y efectivo/imputado, gratuito != cero | `costes.md:3-8`, `:12-20`, `:26-35`, `:43`; `transferencia.md:28` | Cumple en lo numérico; parcial en cuotas gratuitas | Ver hallazgo I-1 (Netlify sin límite ni fuente). No se inventan beneficios ni se contratan servicios (ROI ausente, K8 fuera de alcance). |
| Supuestos explícitos y escalado con mejoras ligadas a problemas | `escalado.md:91-102` (8 propuestas: problema con id y cifra, mejora, medición que la confirma); `:3` | Cumple | Ninguno; las propuestas que tocan contrato se marcan como decisión del alumno. |
| Sin PENDIENTE ni «no calculable» | grep en `docs/evidencias/mediciones/`: ninguno. En `docs/borradores/mediciones-costes.md:15`, `:46`, `:61`: sí (ver B-1) | Parcial | Actualizar el borrador y el README raíz. |
| Cifras del README coherentes con `resultados.json` y `tablas.md` | `README.md:9-10` (117 s, 102, 60), `:19` (227), `:33` (832) | Cumple | 117 s, 102, 60 planes, 227 y 832 comprobados contra `T087_corrida.txt:32`, `T094_*`, `T093_unitarias_completas.txt`. |
| Limitaciones declaradas | VM de Docker: `equipo.md:3`, `procedimiento.md:33`; tracemalloc: solo en `tablas.md:3` (cabecera, no como limitación); atípico `pg_seq.100000.first`: `teoria_vs_observado.md:24`; N=1.000 como ruido: `teoria_vs_observado.md:19`, `:56`, `procedimiento.md:34` | Parcial | Falta decir qué mide tracemalloc (solo asignaciones de Python, no memoria de Postgres ni RSS). Ver M-2. |
| Enlaces entre archivos | Todos los `T0xx_*`, `planes/`, `aislamiento.md`, `escalado.md`, `specs/011-mediciones-costes/quickstart.md` y `docs/borradores/mediciones-costes.md` existen (comprobado con `ls`) | Cumple | Ver M-4 sobre la numeración 011/016. |
| Rúbrica Reflexión 9-10 | Evidencia sólida: análisis teoría vs observado con discrepancias explicadas, extrapolación con fórmulas, 8 propuestas, costes completos | Cumple en evidencias; parcial en entregable | Memoria §7 está vacía (ver I-2). |

## Hallazgos

### Bloqueantes
Ninguno. Las cifras son internamente coherentes y recalculables, y no hay secretos ni contratos modificados.

### Importantes

- I-1. Cuota gratuita de Netlify sin límite cuantificado ni fuente. `costes.md:47`: plan «Plan gratuito.» sin cifras y consecuencia «Se paraliza el servicio si la tasa es alta», sin fecha de verificación real ni enlace; `costes.md:48` Cloudflare: «No consta». `README.md` (mediciones):13 y `:29` lo reconocen («un dato aún por verificar»). La afirmación de consecuencia parece no verificada. Cerrar: el alumno consulta el panel o la documentación oficial, anota límite, fecha y fuente; o, si no puede, reescribir la celda como «no verificado; ver panel de Netlify» en lugar de afirmar una consecuencia. Con 10 MiB/mes frente a un límite de cientos de GB, la conclusión (efectivo 0) no cambia.
- I-2. `docs/memoria.md:141-145` (sección 7, Complejidad, mediciones y costes) no contiene aún el informe: solo un párrafo ajeno sobre mares y océanos. El enunciado §12 pide «Informe de complejidad, mediciones, costes y propuestas de mejora». Hoy el material está en `docs/evidencias/mediciones/` y en el borrador, pero no en la memoria. Cerrar: en la fase `readme-video`, trasladar el borrador actualizado a la sección 7 (resumen y enlaces a `tablas.md`, `escalado.md`, `costes.md`).
- I-3. Cobertura de la rúbrica sin comprobar contra el texto de `docs/rubrica-y-guia-video.md:42` y `:66`: siguen diciendo que los costes salen «PENDIENTE (alumno)» y «no calculable», y que el nivel es «Notable». Es obsoleto ahora que los valores están rellenos; el alumno podría defender 9-10 en Reflexión. Cerrar: actualizar esas filas (nivel y «qué falta»: solo la memoria §7 y la verificación de la cuota).

### Menores

- M-1 (B-1). Textos obsoletos en `docs/borradores/mediciones-costes.md`: `:15` «Modelo y potencia del equipo anfitrión: PENDIENTE (alumno)» (están en `equipo.md:34-39`); `:46` «PENDIENTE (alumno) ... no calculable» (hay totales en `costes.md:34-35`); `:59-64` «Pendientes del alumno» (a) y (b) (ya resueltos: imagen reconstruida en `T094_*`), y `:68` «imagen `tests` desactualizada». Además el borrador no contiene las cifras de costes (60,8/7,9 y 66,9/14,0) ni la tabla de transferencia.
- M-2. Error de etiqueta en el borrador `:46`: «bytes por visita (0,000102442 GiB)». Eso es por petición (109.996 B); por visita son 0,00102442 GiB (`transferencia.md:20`).
- M-3. README raíz (`README.md:22`) lista `mediciones-costes` (016) como «Pendientes» y `:28` la da «en curso»; la feature está implementada y verificada, pendiente de revisión. Además el número 016 (roadmap y README raíz) difiere de la carpeta real `specs/011-mediciones-costes`.
- M-4. `costes.md:14`: hardware se imputa con fracción de uso 1 y el mismo 22,92 EUR/mes en los escenarios A (12 h/día) y B (24/7); es coherente con el documento, pero puede sobrestimar el coste del PC, que se usa para otras cosas. Declarar la fracción como parte del supuesto (ya hay una nota de fracción implícita) y, si se quiere, mostrar una sensibilidad (p. ej. fracción 0,5 = 11,46 EUR/mes).
- M-5. `transferencia.md:3-9`: `/api/eventos` y `?limit=5000` dan los mismos 107.162 B porque el rango por defecto es de 24 h (`README.md:322`), no por el límite. Añadir una línea que diga que la cifra depende de la ventana por defecto y de la actividad de las últimas 24 h en ese momento.
- M-6. `escalado.md:34`/`:36` usan «×16,4» y «×21,6» ya calculados; correcto, pero la memoria del `dict` crece ×18,5 (`:37`) y `escalado.md:37` la llama «mínimo si sigue lineal»; es razonable y está dicho.
- M-7. `indices.md:72`: las recomendaciones de la parte final son manuales y se pierden si se regenera el documento; está avisado en `procedimiento.md:37`. Sin acción salvo cuidado.

## Resumen

El apartado cumple el §10 del enunciado y los requisitos K1-K7 y E6 con evidencia comprobada: 102 mediciones con id citable, tres tamaños, comparaciones lista/diccionario y sin/con índice, aislamiento de datos sintéticos demostrado, razonamiento a 10^8 con fórmulas, ocho propuestas ligadas a hallazgos y costes recalculados sin error. Los totales (60,8/7,9 y 66,9/14,0 EUR/mes) y la transferencia (109.996 B por petición, 1,05 MiB por visita) son correctos. Lo que queda es de redacción y datos del alumno: verificar la cuota de Netlify (I-1), trasladar el informe a `docs/memoria.md` §7 (I-2), y actualizar textos obsoletos en el borrador, el README raíz y `docs/rubrica-y-guia-video.md` (I-3, M-1 a M-3). Hasta que el alumno decida, no se ha corregido nada.
