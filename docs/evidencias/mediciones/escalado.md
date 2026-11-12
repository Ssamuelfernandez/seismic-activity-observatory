# Razonamiento a 100 millones de filas (K5) y propuestas de mejora (K7)

Todo lo de este documento es una extrapolación de cifras medidas a un tamaño que NO se ha medido (10^8 filas). Cada extrapolación lleva su fórmula y la marca SUPUESTO; las cifras de partida llevan su id de `resultados.json` entre corchetes o el nombre del documento de origen (`almacenamiento.md`, `indices.md`, `transferencia.md`). Se redondea y no se afirma nada sobre lo que ocurriría fuera del rango medido (1.000 a 100.000 filas).

Qué significan las cifras de partida:

- Son SINTÉTICAS: tablas `bench` generadas con la semilla 20251113 (`tablas.md`). La distribución de magnitudes, países y fechas es la del generador, no la de los datos reales; por eso las selectividades (p. ej. 0,0184 en [agg.q4_noindex.100000.day]) son de esta muestra.
- Se midieron en la VM de Docker Desktop (WSL2, 24 hilos lógicos y 15,17 GiB de RAM según `equipo.md`), no en el equipo anfitrión: los milisegundos absolutos son de ese entorno; la comparación entre estrategias dentro de la misma corrida es la parte reutilizable.
- El mayor tamaño (100.000 filas) cabe en memoria del servidor (36,3 MB con índices, ver punto 1): no se midió ningún caso con lecturas de disco. Las extrapolaciones a 10^8 filas (≈34 GiB) salen de ese rango.
- Los costes de escritura (INSERT con y sin cada índice) no se midieron.

## Puntos de razonamiento

### 1. Almacenamiento (bytes por fila medidos × 10^8, con índices)

Fórmula: bytes_10^8 = bytes_por_fila × 10^8, con bytes_por_fila = (montón + 4 índices) / filas (`almacenamiento.md`, tabla `bench`).

| Cálculo | Entrada medida | Resultado | Etiqueta |
|---|---|---|---|
| `bench` a 100.000 filas, con los 4 índices | 36.315.136 B / 10^5 = 363,2 B por fila (`almacenamiento.md`) | 363,2 × 10^8 = 3,63 × 10^10 B = 33,8 GiB | SUPUESTO |
| de ellos, montón | 21.823.488 B / 10^5 = 218,2 B por fila (`almacenamiento.md`) | 2,18 × 10^10 B = 20,3 GiB | SUPUESTO |
| de ellos, índices | (4.087.808 + 3.104.768 + 2.277.376 + 4.980.736) B / 10^5 = 144,5 B por fila (`indices.md`, tamaño de índices) | 1,45 × 10^10 B = 13,5 GiB | SUPUESTO |
| `live.current_event` real | 475,2 B por fila, 18.635 filas (`almacenamiento.md`) | 475,2 × 10^8 = 4,75 × 10^10 B = 44,3 GiB | SUPUESTO |
| `live.event_version` real | 1.090,3 B por fila, 18.701 filas (`almacenamiento.md`) | 1.090,3 × 10^8 = 1,09 × 10^11 B = 101,5 GiB | SUPUESTO |

Observaciones: (a) los bytes por fila de `bench` bajan con el tamaño: 466,9 (1.000 filas), 398,1 (10.000), 363,2 (100.000), porque parte del coste es fijo por tabla e índice; la cifra de 100.000 es la más cercana a un valor asintótico, no hay garantía de que se estabilice ahí. (b) Las tablas reales miden más por fila (475,2 y 1.090,3 B) con pocas filas; el montón y los índices reales no se separan igual que en `bench`. (c) `event_version` guarda una fila por versión (constitución §2), así que a igual número de eventos ocupa más que `current_event`; la fórmula usa filas de esa tabla, no eventos. (d) Los dos índices mayores de `bench` son `ix_current_event_time_s100000` (4.980.736 B) y `current_event_pkey_s100000` (4.087.808 B); el de magnitud es el menor (2.277.376 B, `indices.md`).

### 2. Coste por operación según la tendencia medida

Fórmula: coste(10^8) = coste(10^5) × (10^8 / 10^5) = coste(10^5) × 1.000 si el coste crece linealmente con n (tendencia medida entre 10^3, 10^4 y 10^5); si el coste es constante en el rango medido, se mantiene constante, y si es logarítmico, coste(10^5) × log(10^8) / log(10^5) = × 1,6.

| Operación | Tendencia medida (ids) | Cálculo | Resultado SUPUESTO |
|---|---|---|---|
| Lista, id ausente | 0,011748 → 0,125709 → 2,058552 ms: lineal o algo mayor ([search.list.1000.absent], [search.list.10000.absent], [search.list.100000.absent]) | 2,058552 ms × 1.000 | 2.059 ms (2,1 s) por búsqueda; si el crecimiento sigue por encima de lineal (×16,4 entre 10^4 y 10^5), es más |
| `dict` | constante, 0,000062–0,000072 ms [search.dict.100000.absent] | constante | sin cambio en la búsqueda |
| Construcción del `dict`, tiempo | 0,024549 → 0,301899 → 6,512775 ms ([search.dict_build.1000.build], [search.dict_build.10000.build], [search.dict_build.100000.build]) | 6,512775 ms × 1.000 | 6.513 ms × 10^3 = 6.513 s, sin contar el crecimiento superlineal medido (×21,6) |
| Construcción del `dict`, memoria | pico 5.632,09 KiB a 100.000 filas [search.dict_build.100000.build] | 5.632,09 KiB × 1.000 | 5.632.094 KiB = 5,4 GiB (mínimo si sigue lineal; el último tramo fue ×18,5) |
| Postgres sin índice, id ausente | 0,169676 → 0,445746 → 4,799034 ms ([search.pg_seq.1000.absent], [search.pg_seq.10000.absent], [search.pg_seq.100000.absent]) | 4,799034 ms × 1.000 | 4.799 ms (4,8 s) por búsqueda |
| Postgres con índice, id ausente | constante, 0,146670 ms a 100.000 filas [search.pg_index.100000.absent], servidor 0,011 ms | 0,146670 ms × 1,6 (si es logarítmico) | 0,23 ms |
| Integración geográfica, bucle ingenuo, 10^8 puntos | 1.919,619815 ms por 10^5 puntos, lineal ([geo.naive.100000.mixed]) | 1.919,619815 ms × 1.000 | 1,92 × 10^6 ms = 32 min |
| Integración geográfica, `STRtree`, 10^8 puntos | 610,28769 ms por 10^5 puntos, lineal ([geo.strtree.100000.mixed]) | 610,28769 ms × 1.000 | 6,10 × 10^5 ms = 10,2 min |
| Q2 (mes) sin índice | 0,200038 → 0,657134 → 5,358898 ms ([agg.q2_noindex.1000.month], [agg.q2_noindex.10000.month], [agg.q2_noindex.100000.month]) | 5,358898 ms × 1.000 | 5.359 ms (5,4 s) |
| Q2 (mes) con índice | 0,155059 → 0,194722 → 0,182825 ms ([agg.q2_country_index.1000.month], [agg.q2_country_index.10000.month], [agg.q2_country_index.100000.month]) | 0,182825 ms × 1,6 (logarítmico, filas devueltas con selectividad constante no incluidas) | 0,29 ms; con selectividad 0,0058 [agg.q2_country_index.100000.month], 5,8 × 10^5 filas devueltas, el coste de devolverlas no está en esta cifra |
| Q3 (p99) sin índice | 5,50291 ms a 100.000 filas [agg.q3_noindex.100000.p99] | × 1.000 | 5.503 ms (5,5 s) |
| Q3 (p99) con índice | constante, 0,202031 ms [agg.q3_mag_index.100000.p99] | × 1,6 | 0,32 ms, sin contar filas devueltas (selectividad 0,0102: 1,0 × 10^6 filas) |
| Q4 ventana toda la tabla | 0,694267 → 3,810659 → 17,246617 ms, lineal con y sin índice ([agg.q4_noindex.1000.all], [agg.q4_noindex.10000.all], [agg.q4_noindex.100000.all]; con índice [agg.q4_time_index.100000.all] 17,316232 ms) | 17,246617 ms × 1.000 | 17.247 ms (17,2 s) |
| Q4 ventana de un día con índice | 0,181868 → 0,229941 → 0,375212 ms con 43, 359 y 1.840 filas devueltas ([agg.q4_time_index.1000.day], [agg.q4_time_index.10000.day], [agg.q4_time_index.100000.day]) | pendiente = (0,375212 − 0,181868) ms / (1.840 − 43 filas) = 1,08 × 10^-4 ms por fila; con selectividad 0,0184 [agg.q4_time_index.100000.day], 1,84 × 10^6 filas: 0,18 + 1,08 × 10^-4 × 1,84 × 10^6 | 199 ms |

Qué dicen estos números: lo que dependía de recorrer todo (lista, `Seq Scan`, bucle ingenuo, agregaciones sin índice) escala con n; lo que usa el índice depende del número de filas que devuelve. La integración geográfica por punto (610 s por 10^8 puntos con `STRtree`, 3,1 veces menos que el bucle ingenuo) es el coste de CPU mayor con diferencia de los medidos (≈6 µs por punto frente a ≈0,15 ms de una consulta por id, `search.pg_index`, que es sobre todo ida y vuelta).

### 3. Particionado por `event_time`

Fórmula: filas_leídas_con_poda = N × selectividad_ventana (solo se abren las particiones que intersectan la ventana, suponiendo particiones alineadas con la ventana); sin poda y sin índice, filas_leídas = N.

- Cifras de partida: Q4 de un día pasa de 3,526351 ms sin índice a 0,375212 ms con `ix_current_event_time` a 100.000 filas ([agg.q4_noindex.100000.day], [agg.q4_time_index.100000.day]), con selectividad 0,0184. Q4 sobre toda la tabla cuesta lo mismo con y sin índice, 17,246617 y 17,316232 ms ([agg.q4_noindex.100000.all], [agg.q4_time_index.100000.all]).
- SUPUESTO: con selectividad constante 0,0184 a 10^8 filas, una ventana de un día lee 10^8 × 0,0184 = 1,84 × 10^6 filas con poda de particiones, frente a 10^8 de un `Seq Scan` (reducción de 54 veces = 1 / 0,0184).
- Lo que la medición NO muestra: que particionar mejore frente a un índice ya existente. A 100.000 filas, el índice ya baja la ventana de un día a 0,375212 ms; el beneficio de la partición frente al índice no se midió. Las ventanas que abarcan toda la tabla no se benefician de la poda ([agg.q4_time_index.100000.all]: el plan lee todo).
- Condición de diseño (hecho de PostgreSQL, no medido aquí): en una tabla particionada, la clave primaria y los índices únicos deben incluir la columna de partición. La clave actual es `event_id` (idempotencia por `ON CONFLICT`, constitución §1), por lo que particionar por `event_time` obliga a cambiar la clave o la forma de la idempotencia. Eso toca el contrato de datos: es una decisión del alumno, no una medida que se aplique sola.
- Mantenimiento: las particiones antiguas se podrían separar o eliminar con una sola operación; no se ha medido ni es necesario para los tamaños actuales.

### 4. Índices que se conservan o se descartan según E6

Veredictos reales en `indices.md` (E6). Resumen con los ids de las mediciones:

| Índice | Resultado de las mediciones | Qué se conserva |
|---|---|---|
| `ix_current_event_country_time` | justificado en los 6 casos (Q2, mes e intervalo, a 1.000, 10.000 y 100.000 filas): p. ej. 5,358898 → 0,182825 ms [agg.q2_noindex.100000.month, agg.q2_country_index.100000.month] | se conserva |
| `ix_current_event_time` | justificado en Q4 de un día a 10.000 y 100.000 filas (0,505452 → 0,229941 ms; 3,526351 → 0,375212 ms: [agg.q4_noindex.10000.day, agg.q4_time_index.10000.day], [agg.q4_noindex.100000.day, agg.q4_time_index.100000.day]); no concluyente a 1.000 filas [agg.q4_time_index.1000.day]; no justificado con la ventana de toda la tabla en los 3 tamaños (p. ej. [agg.q4_time_index.100000.all]) | se conserva para ventanas estrechas; sin efecto en ventanas que abarcan la tabla |
| `ix_current_event_mag` | `mag >= 4`: no justificado con estos datos a 1.000 y 10.000 filas (el planificador no usa el índice, [agg.q3_mag_index.1000.mag4], [agg.q3_mag_index.10000.mag4]), justificado a 100.000 (5,956245 → 4,00266 ms con `Index Only Scan`, selectividad 0,9458: [agg.q3_mag_index.100000.mag4]); umbral selectivo p99: no concluyente a 1.000 filas [agg.q3_mag_index.1000.p99], justificado a 10.000 y 100.000 (0,635278 → 0,184493 ms; 5,50291 → 0,202031 ms) | el veredicto global es «justificado», pero depende del umbral y del tamaño; en la base real, `ix_current_event_mag` tiene 9 lecturas (`idx_scan`) frente a 6.124 de `ix_current_event_time` (`indices.md`) |

Para 10^8 filas, razonamiento SUPUESTO: tamaño de cada índice = bytes de índice a 100.000 filas × 1.000: tiempo 4.980.736 × 1.000 = 4,98 × 10^9 B (4,6 GiB); país+tiempo 3.104.768 × 1.000 = 2,9 GiB; magnitud 2.277.376 × 1.000 = 2,1 GiB; clave primaria 4.087.808 × 1.000 = 3,8 GiB (`indices.md`). Cada índice añadido es espacio y trabajo en cada escritura (no medido); el criterio de E6 es conservar el que baja el coste de una consulta usada.

### 5. Carga por lotes frente a una transacción por mensaje

Cifra de partida: una consulta por id a un Postgres tiene 0,157592 ms de mediana en el cliente y 0,013 ms en el servidor ([search.pg_index.100000.middle]); la diferencia, 0,1446 ms, es ida y vuelta y gestión de la sentencia, y es igual en los tres tamaños (0,155182 ms con 1.000 filas, [search.pg_index.1000.middle]). No se ha medido un INSERT, de modo que se usa esa ida y vuelta como cota de lo que cuesta cada sentencia suelta.

- Fórmula: tiempo_de_ida_y_vuelta = mensajes × 0,1446 ms / tamaño_de_lote.
- SUPUESTO, 10^8 mensajes, una transacción por mensaje (lote = 1): 10^8 × 0,1446 ms = 1,446 × 10^7 ms = 14.460 s = 4,0 h solo de ida y vuelta, sin contar el trabajo del INSERT ni el fsync de cada commit.
- SUPUESTO, lotes de 1.000 mensajes: 14.460 s / 1.000 = 14,5 s de ida y vuelta.
- La constitución §1 exige procesamiento al menos una vez e idempotente: el commit del offset va después de escribir; con lotes, un fallo a mitad reprocesa el lote entero, lo cual es seguro porque la escritura es idempotente. El tamaño de lote es una decisión de diseño que no se midió.

### 6. Varios consumidores (partición de Kafka por clave)

Cifra de partida: el trabajo de CPU dominante por mensaje es la integración geográfica: 610,28769 ms por 10^5 puntos con `STRtree` [geo.strtree.100000.mixed], es decir, 163.900 puntos por segundo por proceso.

- Fórmula: tiempo_total = (mensajes / puntos_por_segundo) / consumidores = 10^8 / 163.900 / k.
- SUPUESTO (reparto equilibrado por clave, consumidores independientes, sin contención de la base de datos): con k = 1, 610 s; k = 4, 152 s; k = 12 (núcleos físicos de `equipo.md`), 51 s. La integración geográfica no es el único coste por mensaje, de modo que el total es mayor.
- Condición del contrato: el topic `earthquakes.live` tiene hoy 1 partición y la clave es `event.id` (`kafka-message.md` §2). Con más de una partición, la misma clave va a la misma partición, y el orden entre versiones de un evento se conserva dentro de ella; para tener k consumidores en paralelo hacen falta al menos k particiones. Cambiar el número de particiones toca el contrato: decisión del alumno.
- No se midió ningún caso con dos consumidores.

## Propuestas ligadas a hallazgos (K7)

Formato: problema observado (id y cifra) → mejora → medición que la confirmaría. Todas están dentro del alcance de la constitución §12 (sin Spark, Flink, Kubernetes ni ML). Las que tocan contrato, DDL o configuración son propuestas al alumno, no cambios hechos.

1. Problema: la búsqueda por id sin índice cuesta 4,799034 ms a 100.000 filas, 32,7 veces más que con índice (0,146670 ms) ([search.pg_seq.100000.absent], [search.pg_index.100000.absent]). → Mejora: mantener la clave primaria `event_id` para toda búsqueda por id y no sustituirla por un recorrido ni por un `dict` construido en cada consulta. → Medición: repetir `search.pg_seq` y `search.pg_index` en `bench` con 1.000.000 filas y comprobar que la proporción se mantiene o crece.
2. Problema: construir un `dict` de ids con 100.000 filas cuesta 6,512775 ms y un pico de 5.632,09 KiB [search.dict_build.100000.build], con crecimiento superlineal entre tamaños (×21,6 en tiempo). → Mejora: no cargar todos los ids en memoria en el consumidor y comprobar duplicados con la consulta por clave primaria (0,157592 ms, [search.pg_index.100000.middle]). → Medición: comparar el pico de memoria (`tracemalloc`) y el tiempo por mensaje de ambas estrategias con 1.000.000 de ids.
3. Problema: la integración geográfica con `STRtree` tarda 610,28769 ms por 100.000 puntos, y es el mayor coste de CPU medido ([geo.strtree.100000.mixed]; naive 1.919,619815 ms, [geo.naive.100000.mixed]). → Mejora: repartir los mensajes entre varios consumidores por clave (punto 6). → Medición: ejecutar `geo.strtree` con 2 y 4 procesos sobre los mismos 100.000 puntos y comprobar que el tiempo total baja en la proporción de la fórmula.
4. Problema: Q4 sobre toda la tabla tarda 17,316232 ms con índice y 17,246617 ms sin él a 100.000 filas, con crecimiento lineal desde 0,669548 ms a 1.000 filas ([agg.q4_time_index.100000.all], [agg.q4_noindex.100000.all], [agg.q4_time_index.1000.all]). → Mejora: no añadir índices para ventanas que abarcan toda la tabla; si este tipo de consulta es frecuente, limitar la ventana máxima que acepta la API (decisión del alumno, toca el contrato de la API). → Medición: tiempo de Q4 con la ventana máxima propuesta frente a la de toda la tabla, a 100.000 filas.
5. Problema: `ix_current_event_mag` ocupa 560 KiB en la base real y tiene 9 lecturas (`idx_scan`) frente a 6.124 de `ix_current_event_time` (`indices.md`); en las mediciones `mag >= 4` no usa el índice a 1.000 y 10.000 filas ([agg.q3_mag_index.1000.mag4], [agg.q3_mag_index.10000.mag4]) y a 100.000 mejora de 5,956245 a 4,00266 ms ([agg.q3_mag_index.100000.mag4]). → Mejora: mantener el índice hasta medir su coste de escritura y su uso con consultas reales; el alumno decide (no se edita el DDL). → Medición: tiempo de INSERT de 100.000 filas con y sin `ix_current_event_mag` en `bench`, más `idx_scan` de la base real tras un periodo de uso con el frontend.
6. Problema: una sentencia suelta cuesta 0,1446 ms de ida y vuelta (0,157592 ms en el cliente y 0,013 ms en el servidor, [search.pg_index.100000.middle]), el 92 % del tiempo medido. → Mejora: escribir por lotes en una transacción (punto 5). → Medición: insertar 10.000 filas en `bench` con una transacción por fila y con lotes de 100 y de 1.000, cronometrando cada variante.
7. Problema: la respuesta de `/api/eventos` es de 107.162 bytes sin compresión, el 97,4 % de los 109.996 bytes de una visita (`transferencia.md`). → Mejora: activar la compresión en el servicio de la API (decisión del alumno). → Medición: repetir la medición de `transferencia.md` con `Accept-Encoding: gzip` y comparar los bytes por visita.
8. Problema: `ingest.raw_response` ocupa 8.871.936 bytes con 204 filas (43.489,9 B por fila), el 18,8 % de los 47.160.343 bytes de la base (`almacenamiento.md`). → Mejora: definir una retención para `raw_response` (decisión del alumno; toca DDL y contrato). → Medición: tamaño de `ingest.raw_response` antes y después de aplicar la retención sobre los mismos datos.

## Límites

- Sin datos de disco, de concurrencia de escrituras ni de Kafka: los puntos 5 y 6 usan como cota la ida y vuelta de una consulta y la integración geográfica medidas, y se marcan como SUPUESTO.
- La precisión de las extrapolaciones a 10^8 filas depende de que la tendencia medida (tres tamaños, tres decenas) se mantenga; las fórmulas permiten reemplazar los valores si se vuelve a medir con un tamaño mayor.
- Las tarifas, visitas por mes y demás entradas de coste monetario siguen PENDIENTES del alumno (`costes.md`); no se calcula ningún importe en euros aquí.
