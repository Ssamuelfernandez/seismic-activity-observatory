# Teoría frente a observado (K1)

Origen de todas las cifras: `resultados.json` (SINTÉTICO, `bench`, semilla 20251113, 15 repeticiones por serie, mediana en ms; Postgres 16.15 en la VM de Docker Desktop, ver `equipo.md`). Cada cifra lleva entre corchetes el id de la medición. Los ids siguen el patrón `<operación>.<estrategia>.<tamaño>.<caso>`. Las columnas teóricas son las anotadas en el campo `theory` de cada medición. Las tablas completas están en `tablas.md`.

Definición de «medio» y «peor caso» (spec, aclaraciones): lista, `dict` y Postgres: medio = id en el medio, peor = id ausente; integración geográfica: medio = puntos mezclados, peor = puntos en el océano (recorren los 177 polígonos); agregación: medio = ventana selectiva, peor = ventana que abarca (casi) toda la tabla.

## A. Búsqueda por id

| Estrategia | Coste medio teórico | Peor caso teórico | Observado medio (1.000 / 10.000 / 100.000 filas) | Observado peor (1.000 / 10.000 / 100.000 filas) |
|---|---|---|---|---|
| lista (recorrido secuencial) | O(n) | O(n) | 0,006390 [search.list.1000.middle] / 0,064047 [search.list.10000.middle] / 0,843322 [search.list.100000.middle] | 0,011748 [search.list.1000.absent] / 0,125709 [search.list.10000.absent] / 2,058552 [search.list.100000.absent] |
| `dict` | O(1) | O(n) teórico | 0,000072 [search.dict.1000.middle] / 0,000072 [search.dict.10000.middle] / 0,000072 [search.dict.100000.middle] | 0,000062 [search.dict.1000.absent] / 0,000072 [search.dict.10000.absent] / 0,000062 [search.dict.100000.absent] |
| construcción del `dict` | O(n) | O(n) | 0,024549 [search.dict_build.1000.build] / 0,301899 [search.dict_build.10000.build] / 6,512775 [search.dict_build.100000.build] | no aplica |
| Postgres sin índice (`Seq Scan`) | O(n) | O(n) | 0,168922 [search.pg_seq.1000.middle] / 0,320151 [search.pg_seq.10000.middle] / 2,331618 [search.pg_seq.100000.middle] | 0,169676 [search.pg_seq.1000.absent] / 0,445746 [search.pg_seq.10000.absent] / 4,799034 [search.pg_seq.100000.absent] |
| Postgres con índice (B-tree) | O(log n) | O(log n) | 0,155182 [search.pg_index.1000.middle] / 0,159941 [search.pg_index.10000.middle] / 0,157592 [search.pg_index.100000.middle] | 0,154016 [search.pg_index.1000.absent] / 0,147244 [search.pg_index.10000.absent] / 0,146670 [search.pg_index.100000.absent] |

Discrepancias y su explicación:

1. **`Seq Scan` no es peor que el índice a 1.000 filas.** Sin índice, el id ausente cuesta 0,169676 ms [search.pg_seq.1000.absent] y con índice 0,154016 ms [search.pg_index.1000.absent]: una diferencia de 0,016 ms, del orden del rango intercuartílico de la serie sin índice (0,001502 ms, mismo id, en una serie de 15 repeticiones). El tiempo en el servidor sí las distingue (0,033 ms [search.pg_seq.1000.absent] frente a 0,010 ms [search.pg_index.1000.absent]), pero la mediana del cliente incluye la ida y vuelta, que a este tamaño domina. A 100.000 filas la teoría sí se ve: 4,799034 ms [search.pg_seq.100000.absent] frente a 0,146670 ms [search.pg_index.100000.absent].
2. **El índice parece constante, no logarítmico.** Entre 1.000 y 100.000 filas la mediana con índice queda entre 0,146670 y 0,159941 ms (extremos [search.pg_index.100000.absent] y [search.pg_index.10000.middle]); el servidor mide 0,010–0,013 ms en los tres tamaños (p. ej. [search.pg_index.100000.middle]). El crecimiento logarítmico existe pero es menor que la resolución de la medición con estos tamaños: lo observado es compatible con O(log n), no lo demuestra.
3. **Lista: el crecimiento no es exactamente lineal.** Peor caso: ×10,7 de 1.000 a 10.000 filas ([search.list.1000.absent] → [search.list.10000.absent]) y ×16,4 de 10.000 a 100.000 ([search.list.10000.absent] → [search.list.100000.absent]). Con 10 veces más filas, el recorrido tarda más de 10 veces. No se investigó la causa; la medición solo permite decir que en este rango crece más deprisa que lineal.
4. **`dict`: no hay peor caso observable.** Medio y ausente son indistinguibles (0,000062–0,000072 ms en todos los tamaños, p. ej. [search.dict.100000.absent]); el O(n) teórico por colisiones no aparece con claves de texto. La resolución del reloj (del orden de 0,00001 ms) limita estas cifras.
5. **El coste del `dict` está en construirlo.** 6,512775 ms [search.dict_build.100000.build] y un pico de 5632,09 KiB (campo `peak_kib` de la misma medición) a 100.000 filas, frente a 0,024549 ms y 38,09 KiB a 1.000 [search.dict_build.1000.build]. Crece ×12,3 y ×21,6 en tiempo por cada ×10 de filas; la memoria, ×8,0 y ×18,5: más que lineal en este rango. Una consulta con `dict` solo compensa si se reutiliza el `dict` construido.
6. **Primer elemento en Postgres sin índice.** El caso `first` es casi plano en el cliente (0,148111 [search.pg_seq.1000.first] → 0,175688 ms [search.pg_seq.100000.first]), lo que encaja con parar al encontrar el id. Pero el tiempo de servidor de esa misma serie a 100.000 filas es 7,057 ms [search.pg_seq.100000.first], mayor que su mediana de cliente (0,175688 ms). Los dos valores no cuadran y no se ha investigado el origen; por eso no se usa `server_ms` de esta serie como cifra de comparación.

## B. Integración geográfica (punto en polígono, 177 polígonos)

| Estrategia | Coste medio teórico | Peor caso teórico | Observado medio, puntos mezclados (1.000 / 10.000 / 100.000 puntos) | Observado peor, puntos en el océano (1.000 / 10.000 / 100.000 puntos) |
|---|---|---|---|---|
| bucle ingenuo | O(n·p) | O(n·p) | 19,145102 [geo.naive.1000.mixed] / 194,084956 [geo.naive.10000.mixed] / 1919,619815 [geo.naive.100000.mixed] | 21,133017 [geo.naive.1000.ocean] / 212,972772 [geo.naive.10000.ocean] / 2130,540027 [geo.naive.100000.ocean] |
| `STRtree` | O(n·(log p + candidatos)) | O(n·(log p + candidatos)) | 5,856506 [geo.strtree.1000.mixed] / 59,81775 [geo.strtree.10000.mixed] / 610,28769 [geo.strtree.100000.mixed] | 5,628615 [geo.strtree.1000.ocean] / 54,407719 [geo.strtree.10000.ocean] / 568,379718 [geo.strtree.100000.ocean] |
| construcción del `STRtree` | O(p log p) | O(p log p) | 0,01913 [geo.strtree_build.1000.build] | no aplica (no depende de n: 0,019016 [geo.strtree_build.10000.build], 0,018994 [geo.strtree_build.100000.build]) |

Ambos métodos devuelven el mismo país en todos los puntos (0 diferencias de 100.000, nota de [geo.naive.100000.mixed] y de [geo.strtree.100000.mixed]).

Discrepancias y su explicación:

1. **Crecimiento lineal en n, como indica la teoría:** ×10,1 y ×9,9 para el bucle ingenuo ([geo.naive.1000.mixed] → [geo.naive.10000.mixed] → [geo.naive.100000.mixed]); ×10,2 y ×10,2 para `STRtree` ([geo.strtree.1000.mixed] → [geo.strtree.10000.mixed] → [geo.strtree.100000.mixed]).
2. **El peor caso del bucle ingenuo es solo ~11 % más lento que el caso mezclado** (2130,540027 ms [geo.naive.100000.ocean] frente a 1919,619815 ms [geo.naive.100000.mixed]), no una diferencia grande. La proporción de puntos del océano dentro del caso mezclado no se midió aquí, así que no se afirma el motivo exacto.
3. **En `STRtree` el caso océano es más rápido que el mezclado** (568,379718 ms [geo.strtree.100000.ocean] frente a 610,28769 ms [geo.strtree.100000.mixed]): no se comporta como «peor caso» para este método. HIPÓTESIS, sin medir: un punto en el océano no tiene candidatos que verificar en el árbol; el peor caso del `STRtree` sería el de muchos candidatos, que estas series no aíslan.
4. **La mejora medida es ×3,1 a ×3,9** (p. ej. 1919,619815 [geo.naive.100000.mixed] / 610,28769 [geo.strtree.100000.mixed] = 3,1; océano: 2130,540027 [geo.naive.100000.ocean] / 568,379718 [geo.strtree.100000.ocean] = 3,7; el máximo, 3,9, sale de [geo.naive.10000.ocean] / [geo.strtree.10000.ocean]), muy por debajo de «177 polígonos frente a log p». HIPÓTESIS, sin medir: el `STRtree` verifica además los candidatos con la geometría exacta, y con p = 177 el factor logarítmico aporta poco. Sin medición adicional no se separan ambos efectos.
5. **Memoria:** el pico es el mismo para ambos métodos (782,99 KiB [geo.naive.100000.mixed] frente a 783,17 KiB [geo.strtree.100000.mixed]); depende de n, no del método.

## C. Agregación por ventanas (Q2, Q3, Q4 de `db-schema.md` §4)

Las filas «sin índice» y «con índice» son las del veredicto E6 (ver `indices.md`). Todas las consultas se anotan como O(n) en el campo `theory` (`Seq Scan` más ordenación o HashAggregate); con índice, el plan usa `Index Scan` o `Index Only Scan` cuando el planificador lo elige (campo `index_used` de cada medición).

| Consulta (índice) | Teoría (medio y peor) | Observado medio: ventana selectiva, sin índice → con índice, a 1.000 / 10.000 / 100.000 filas | Observado peor: ventana que abarca la tabla, sin índice → con índice |
|---|---|---|---|
| Q4 por tiempo (`ix_current_event_time`), ventana de un día | O(n) | 0,224390 → 0,181868 [agg.q4_noindex.1000.day, agg.q4_time_index.1000.day]; 0,505452 → 0,229941 [agg.q4_noindex.10000.day, agg.q4_time_index.10000.day]; 3,526351 → 0,375212 [agg.q4_noindex.100000.day, agg.q4_time_index.100000.day] | todo el rango: 0,694267 → 0,669548 [agg.q4_noindex.1000.all, agg.q4_time_index.1000.all]; 3,810659 → 3,862444 [agg.q4_noindex.10000.all, agg.q4_time_index.10000.all]; 17,246617 → 17,316232 [agg.q4_noindex.100000.all, agg.q4_time_index.100000.all] |
| Q3 por magnitud (`ix_current_event_mag`), umbral selectivo (p99) | O(n) | 0,205138 → 0,196517 [agg.q3_noindex.1000.p99, agg.q3_mag_index.1000.p99]; 0,635278 → 0,184493 [agg.q3_noindex.10000.p99, agg.q3_mag_index.10000.p99]; 5,50291 → 0,202031 [agg.q3_noindex.100000.p99, agg.q3_mag_index.100000.p99] | `mag >= 4` (casi todas las filas): 0,220467 → 0,203145 [agg.q3_noindex.1000.mag4, agg.q3_mag_index.1000.mag4]; 0,715621 → 0,718848 [agg.q3_noindex.10000.mag4, agg.q3_mag_index.10000.mag4]; 5,956245 → 4,00266 [agg.q3_noindex.100000.mag4, agg.q3_mag_index.100000.mag4] |
| Q2 por país y tiempo (`ix_current_event_country_time`), mes | O(n) | 0,200038 → 0,155059 [agg.q2_noindex.1000.month, agg.q2_country_index.1000.month]; 0,657134 → 0,194722 [agg.q2_noindex.10000.month, agg.q2_country_index.10000.month]; 5,358898 → 0,182825 [agg.q2_noindex.100000.month, agg.q2_country_index.100000.month] | intervalo mayor (~2 % de las filas): 0,218548 → 0,157401 [agg.q2_noindex.1000.range, agg.q2_country_index.1000.range]; 0,68724 → 0,237399 [agg.q2_noindex.10000.range, agg.q2_country_index.10000.range]; 5,810273 → 0,247712 [agg.q2_noindex.100000.range, agg.q2_country_index.100000.range] |

Discrepancias y su explicación:

1. **Sin índice la teoría O(n) se ve a 100.000 filas** (Q2 mes 5,358898 ms [agg.q2_noindex.100000.month], Q3 p99 5,50291 ms [agg.q3_noindex.100000.p99]), pero **a 1.000 filas no**: 0,200038 ms [agg.q2_noindex.1000.month] incluye la ida y vuelta, que es casi todo el coste (servidor 0,058 ms, mismo id).
2. **Con índice, Q2 y Q3 selectivos quedan prácticamente constantes** (0,155059 [agg.q2_country_index.1000.month] a 0,182825 ms [agg.q2_country_index.100000.month]; 0,196517 [agg.q3_mag_index.1000.p99] a 0,202031 ms [agg.q3_mag_index.100000.p99]). El campo `theory` de las filas «con índice» repite O(n) y no distingue este caso; la medición muestra que con índice el coste sigue al número de filas devueltas más que a n, en el rango medido.
3. **Q4 con ventana que abarca toda la tabla: el índice no ayuda** (17,316232 ms con índice frente a 17,246617 ms sin él, ids en la tabla): el plan usa `Seq Scan` con `Sort` en ambos (nodos de [agg.q4_time_index.100000.all], `index_used` falso). Coincide con la teoría del peor caso.
4. **Q3 `mag >= 4` a 100.000 filas:** el planificador usa `Index Only Scan` (nodos e `index_used` de [agg.q3_mag_index.100000.mag4]) aunque selecciona el 94,6 % de las filas, y baja de 5,956245 a 4,00266 ms. A 1.000 y 10.000 filas no lo usa (`index_used` falso en [agg.q3_mag_index.1000.mag4]; ídem en [agg.q3_mag_index.10000.mag4]) y las medianas son equivalentes (0,715621 [agg.q3_noindex.10000.mag4] y 0,718848 ms [agg.q3_mag_index.10000.mag4]). Es un resultado de un solo tamaño y un solo plan; no se generaliza.

## Límite de estas cifras

Los datos son SINTÉTICOS (semilla fija, `bench`) y el Postgres corre en la VM de Docker Desktop (WSL2), no en el equipo anfitrión. Los tiempos absolutos no son los de otro entorno; la comparación entre estrategias dentro de la misma corrida es lo que se puede usar.

Limitaciones concretas de la medición:

- **Memoria con `tracemalloc`:** solo cuenta lo que Python reserva (campo `peak_kib`). No incluye la memoria de PostgreSQL ni la del sistema. Solo se mide al construir el `dict` y en la integración geográfica; en las consultas a la base no hay medición de memoria.
- **Valor atípico:** `server_ms` de `search.pg_seq.100000.first` (7,057 ms) queda sin explicar; no se ha usado para ninguna conclusión.
- **N = 1.000 como ruido:** con 1.000 filas domina la ida y vuelta al servidor, no el algoritmo; por eso a ese tamaño el `Seq Scan` no se distingue del índice. Las conclusiones sobre el coste del algoritmo se apoyan en 10.000 y 100.000 filas.
- **Tres tamaños:** con tres puntos solo se puede decir si la tendencia es compatible con la teoría, no demostrarla.
