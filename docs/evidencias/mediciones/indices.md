# Índices de `live.current_event` (E6)

Los veredictos son una PROPUESTA al alumno: no se edita el DDL ni el contrato. Criterio de `verdicts.py`: «justificado» si el plan usa el índice y baja la mediana sin solape de rangos intercuartílicos.

## Referencia REAL de `live.current_event` (solo lectura, rol `observatory_api`)

| Índice | Definición | Tamaño (KiB) | idx_scan |
|---|---|---|---|
| current_event_pkey | `CREATE UNIQUE INDEX current_event_pkey ON live.current_event USING btree (event_id)` | 888.0 | 56111 |
| ix_current_event_country_time | `CREATE INDEX ix_current_event_country_time ON live.current_event USING btree (country_id, event_time DESC)` | 968.0 | 1161 |
| ix_current_event_mag | `CREATE INDEX ix_current_event_mag ON live.current_event USING btree (mag)` | 560.0 | 9 |
| ix_current_event_time | `CREATE INDEX ix_current_event_time ON live.current_event USING btree (event_time DESC, event_id DESC)` | 1328.0 | 6124 |

| Recuento real | Filas |
|---|---|
| live.current_event con source = usgs_historical | 18302 |
| replay.current_event | 22 |
| replay.event_version | no disponible |
| replay.quarantine | no disponible |
| replay.exclusion | no disponible |

## Veredicto por índice (SINTÉTICO)

| Índice | Veredicto global |
|---|---|
| ix_current_event_country_time | justificado |
| ix_current_event_mag | justificado |
| ix_current_event_time | justificado |

## Detalle por consulta y caso (SINTÉTICO)

| Índice | Consulta | Caso | Tamaño | Veredicto | Ids citados | Selectividad | Motivo |
|---|---|---|---|---|---|---|---|
| ix_current_event_time | q4 | day | 1000 | no concluyente | agg.q4_noindex.1000.day; agg.q4_time_index.1000.day | 0.0430 | los rangos intercuartílicos se solapan |
| ix_current_event_time | q4 | all | 1000 | no justificado con estos datos | agg.q4_noindex.1000.all; agg.q4_time_index.1000.all | 1.0000 | el planificador no usa el índice |
| ix_current_event_mag | q3 | mag4 | 1000 | no justificado con estos datos | agg.q3_noindex.1000.mag4; agg.q3_mag_index.1000.mag4 | 1.0000 | el planificador no usa el índice |
| ix_current_event_mag | q3 | p99 | 1000 | no concluyente | agg.q3_noindex.1000.p99; agg.q3_mag_index.1000.p99 | 0.0120 | los rangos intercuartílicos se solapan |
| ix_current_event_country_time | q2 | month | 1000 | justificado | agg.q2_noindex.1000.month; agg.q2_country_index.1000.month | 0.0050 | usa el índice y baja la mediana de 0.200 a 0.155 ms |
| ix_current_event_country_time | q2 | range | 1000 | justificado | agg.q2_noindex.1000.range; agg.q2_country_index.1000.range | 0.0200 | usa el índice y baja la mediana de 0.219 a 0.157 ms |
| ix_current_event_time | q4 | day | 10000 | justificado | agg.q4_noindex.10000.day; agg.q4_time_index.10000.day | 0.0359 | usa el índice y baja la mediana de 0.505 a 0.230 ms |
| ix_current_event_time | q4 | all | 10000 | no justificado con estos datos | agg.q4_noindex.10000.all; agg.q4_time_index.10000.all | 1.0000 | el planificador no usa el índice |
| ix_current_event_mag | q3 | mag4 | 10000 | no justificado con estos datos | agg.q3_noindex.10000.mag4; agg.q3_mag_index.10000.mag4 | 1.0000 | el planificador no usa el índice |
| ix_current_event_mag | q3 | p99 | 10000 | justificado | agg.q3_noindex.10000.p99; agg.q3_mag_index.10000.p99 | 0.0079 | usa el índice y baja la mediana de 0.635 a 0.184 ms |
| ix_current_event_country_time | q2 | month | 10000 | justificado | agg.q2_noindex.10000.month; agg.q2_country_index.10000.month | 0.0067 | usa el índice y baja la mediana de 0.657 a 0.195 ms |
| ix_current_event_country_time | q2 | range | 10000 | justificado | agg.q2_noindex.10000.range; agg.q2_country_index.10000.range | 0.0196 | usa el índice y baja la mediana de 0.687 a 0.237 ms |
| ix_current_event_time | q4 | day | 100000 | justificado | agg.q4_noindex.100000.day; agg.q4_time_index.100000.day | 0.0184 | usa el índice y baja la mediana de 3.526 a 0.375 ms |
| ix_current_event_time | q4 | all | 100000 | no justificado con estos datos | agg.q4_noindex.100000.all; agg.q4_time_index.100000.all | 1.0000 | el planificador no usa el índice |
| ix_current_event_mag | q3 | mag4 | 100000 | justificado | agg.q3_noindex.100000.mag4; agg.q3_mag_index.100000.mag4 | 0.9458 | usa el índice y baja la mediana de 5.956 a 4.003 ms |
| ix_current_event_mag | q3 | p99 | 100000 | justificado | agg.q3_noindex.100000.p99; agg.q3_mag_index.100000.p99 | 0.0102 | usa el índice y baja la mediana de 5.503 a 0.202 ms |
| ix_current_event_country_time | q2 | month | 100000 | justificado | agg.q2_noindex.100000.month; agg.q2_country_index.100000.month | 0.0058 | usa el índice y baja la mediana de 5.359 a 0.183 ms |
| ix_current_event_country_time | q2 | range | 100000 | justificado | agg.q2_noindex.100000.range; agg.q2_country_index.100000.range | 0.0196 | usa el índice y baja la mediana de 5.810 a 0.248 ms |

## Tamaño de los índices en `bench` (SINTÉTICO)

| Filas | Índice (en `bench`) | Bytes |
|---|---|---|
| 1000 | current_event_pkey_s1000 | 57344 |
| 1000 | ix_current_event_country_time_s1000 | 49152 |
| 1000 | ix_current_event_mag_s1000 | 40960 |
| 1000 | ix_current_event_time_s1000 | 73728 |
| 10000 | current_event_pkey_s10000 | 425984 |
| 10000 | ix_current_event_country_time_s10000 | 335872 |
| 10000 | ix_current_event_mag_s10000 | 245760 |
| 10000 | ix_current_event_time_s10000 | 516096 |
| 100000 | current_event_pkey_s100000 | 4087808 |
| 100000 | ix_current_event_country_time_s100000 | 3104768 |
| 100000 | ix_current_event_mag_s100000 | 2277376 |
| 100000 | ix_current_event_time_s100000 | 4980736 |

## Recomendaciones por índice (PROPUESTA al alumno)

Redactadas a mano a partir de las tablas anteriores; no cambian el DDL ni el contrato, y la decisión es del alumno. Se añadieron tras generar este documento: si se vuelve a generar `indices.md` con el comando de la corrida, hay que reponerlas. Los veredictos por caso son los de la tabla de detalle: no todos son «justificado», y se cuentan tal cual.

Qué significan estas cifras: son SINTÉTICAS (tablas `bench`, semilla 20251113, hasta 100.000 filas) y se midieron en la VM de Docker Desktop, no en el equipo anfitrión. Con 1.000 filas el coste lo domina la ida y vuelta al servidor, y por eso los rangos intercuartílicos se solapan; las cifras de la base real (`idx_scan`, tamaños) son una referencia de uso, no una medición de coste.

| Índice | Casos «justificado» | Casos «no justificado» / «no concluyente» | Propuesta |
|---|---|---|---|
| `ix_current_event_country_time` | 6 de 6 (Q2, mes e intervalo, a 1.000, 10.000 y 100.000 filas): p. ej. de 5,359 a 0,183 ms a 100.000 filas (`agg.q2_noindex.100000.month`, `agg.q2_country_index.100000.month`) | ninguno | Conservar. Es la consulta de estadísticas por país y el índice la baja en todos los tamaños. |
| `ix_current_event_time` | Q4 de un día a 10.000 y 100.000 filas: de 3,526 a 0,375 ms a 100.000 (`agg.q4_noindex.100000.day`, `agg.q4_time_index.100000.day`) | Q4 de un día a 1.000 filas: no concluyente (`agg.q4_time_index.1000.day`); Q4 sobre toda la tabla, en los 3 tamaños: no justificado con estos datos (el planificador no usa el índice, p. ej. `agg.q4_time_index.100000.all`) | Conservar para ventanas estrechas. No se puede atribuir a este índice ninguna mejora en ventanas que abarcan toda la tabla. |
| `ix_current_event_mag` | `mag >= 4` a 100.000 filas (de 5,956 a 4,003 ms, `agg.q3_noindex.100000.mag4`, `agg.q3_mag_index.100000.mag4`, selectividad 0,9458); umbral selectivo (p99) a 10.000 y 100.000 filas (de 5,503 a 0,202 ms a 100.000, `agg.q3_noindex.100000.p99`, `agg.q3_mag_index.100000.p99`) | `mag >= 4` a 1.000 y 10.000 filas: no justificado con estos datos (el planificador no usa el índice, `agg.q3_mag_index.1000.mag4`, `agg.q3_mag_index.10000.mag4`); umbral p99 a 1.000 filas: no concluyente (`agg.q3_mag_index.1000.p99`) | Decisión del alumno. El veredicto global sale «justificado», pero solo para un umbral selectivo o para el tamaño mayor; con `mag >= 4` (que selecciona casi todas las filas porque la semilla es M ≥ 4) la mejora aparece solo a 100.000 filas y es moderada. En la base real tiene 9 lecturas (`idx_scan`) y 560 KiB. Mantenerlo hasta medir su coste de escritura y su uso real (ver `escalado.md`, propuesta 5) es compatible con los datos; descartarlo también lo es, y ninguna de las dos opciones queda demostrada por estas mediciones. |
| `current_event_pkey` | no se evalúa en E6 | no se evalúa en E6 | Conservar: sostiene la búsqueda por id (0,147 ms frente a 4,799 ms a 100.000 filas, `search.pg_index.100000.absent`, `search.pg_seq.100000.absent`) y la idempotencia por `event_id`. |
