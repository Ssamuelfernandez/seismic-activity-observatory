# Conclusiones del análisis sobre 2025 (memoria §6, H-B1)

Fecha de ejecución: 2026-11-16. Base: el PostgreSQL del stack levantado, solo lectura (`default_transaction_read_only=on`). Conjunto: `live.current_event` con `is_synthetic = false` y `event_time` entre 2025-01-01 y 2026-01-01 (UTC): **18 302 eventos** (M≥4, mundial, `eventtype=earthquake`; carga del histórico, `data/historical/manifest.json`). Es el mismo total que da la API (`GET /api/estadisticas?start=2025-01-01&end=2026-01-01`: `total` 18 302). El frontend no calcula nada: las cifras son de SQL y de la API. Ninguna consulta escribe.

## Cómo reproducir

```bash
docker compose exec -T postgres sh -c 'PGOPTIONS="-c default_transaction_read_only=on" psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < consulta.sql
curl "http://127.0.0.1:8000/api/estadisticas?start=2025-01-01&end=2026-01-01"
```

## Conclusiones (periodo 2025-01-01 a 2026-01-01 UTC, denominador 18 302 salvo indicación)

| # | Conclusión | Filtros | Denominador | Consulta |
|---|---|---|---|---|
| 1 | Julio y agosto concentran el 26,8 % de los eventos del año (2 684 y 2 222, frente a 1 156 a 1 604 en los demás meses). Casi todo el exceso está en la zona de Kamchatka (caja lat 48 a 58, lon 155 a 165): 1 361 y 1 239 eventos en esos dos meses, frente a 7 a 16 al mes de enero a junio. El mayor evento del año, `us6000qw60` (M 8,8, 2025-07-29 23:24 UTC), es de esa zona. Lectura: una réplica prolongada de un terremoto grande distorsiona el recuento mensual. La caja es un filtro geográfico mío, no un país, y no se ha contrastado con otra fuente. | Sin filtro de magnitud ni país; caja de Kamchatka solo en Q7 | 18 302 (mes: 1 156 a 2 684) | Q2, Q6, Q7, Q8; API: `start=2025-07-01&end=2025-08-01` da `total` 2 684 |
| 2 | El 78,4 % de los eventos (14 350 de 18 302) queda «Sin país asignado»; los países con más eventos son China (354, 1,9 %), Chile (348, 1,9 %), Indonesia (306, 1,7 %), Etiopía (265, 1,4 %) y Argentina (236, 1,3 %). Lectura: la mayoría de los sismos M≥4 cae en el mar o fuera de los polígonos del catálogo de 110 m, así que un ranking por país describe solo una minoría y debe leerse junto a «Sin país asignado». No es un fallo de los datos (ver memoria §4.4). | Sin filtro; `country_id=none` en la API | 18 302 | Q1; API: `by_country.no_value` 14 350 y `country_id=none` da `total` 14 350 |
| 3 | Los eventos son sobre todo pequeños y someros: el 88,4 % tiene magnitud entre 4,0 y 4,9 (16 173); solo el 0,79 % llega a M≥6 (145: 129 entre 6 y 6,9 y 16 de 7 o más; máximo 8,8), y el 74,8 % está a menos de 70 km (13 689; mediana 20,9 km); el 6,0 % a 300 km o más (1 102). Lectura: la distribución es muy asimétrica, de modo que la media de magnitud ocultaría los pocos eventos grandes; conviene mirar los tramos. | Sin filtro; `min_mag=6` en la API | 18 302 (los 145 con M≥6 en la API) | Q3, Q4; API: `histograms.magnitude` (4 a 5: 16 173; 5 a 6: 1 984; 6 a 7: 129; 7 o más: 16) y `min_mag=6` da `total` 145 |

## Comparación de las últimas 24 h con la media de 2025: no se saca conclusión

La API devuelve, en la consulta hecha el 2026-11-16, `n_recent` 16 frente a una media diaria de 2025 de 50,14 (`variation_pct` -68,09) con `recent_incomplete: true`. Como la propia API marca el periodo reciente como posiblemente incompleto y no se ha investigado por qué, **no se usa como conclusión**; es una limitación declarada en la memoria §10.

## Captura del panel con filtros

No se ha generado una captura nueva: las herramientas de esta sesión no dejan guardar en el repositorio una imagen del navegador. Existe la captura del panel público del 2026-11-12 ([`docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png`](../despliegue-tunel/2026-11-12_panel-publico.png)) y, para mostrar los filtros en el vídeo, la coherencia entre mapa, tabla y gráficos está comprobada en [`docs/evidencias/api/coherencia_real.txt`](../api/coherencia_real.txt). El directorio `docs/evidencias/analisis/` queda sin imágenes.

## Consultas SQL (solo SELECT)

```sql
\echo === Q0 denominador
SELECT count(*) AS eventos_2025, min(event_time) AS primero, max(event_time) AS ultimo FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01';
\echo === Q1 por pais (top 6)
SELECT coalesce(c.name_es,'Sin país asignado') AS pais, count(*) AS n, round(100.0*count(*)/sum(count(*)) OVER (),1) AS pct FROM live.current_event e LEFT JOIN public.country c ON c.country_id=e.country_id WHERE NOT e.is_synthetic AND e.event_time >= '2025-01-01' AND e.event_time < '2026-01-01' GROUP BY 1 ORDER BY n DESC LIMIT 6;
\echo === Q2 por mes
SELECT to_char(date_trunc('month',event_time),'YYYY-MM') AS mes, count(*) AS n FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01' GROUP BY 1 ORDER BY 1;
\echo === Q3 magnitud
SELECT count(*) AS total, count(*) FILTER (WHERE mag < 5) AS m4_a_49, count(*) FILTER (WHERE mag >= 5 AND mag < 6) AS m5_a_59, count(*) FILTER (WHERE mag >= 6 AND mag < 7) AS m6_a_69, count(*) FILTER (WHERE mag >= 7) AS m7_o_mas, round(100.0*count(*) FILTER (WHERE mag < 5)/count(*),1) AS pct_m4, round(100.0*count(*) FILTER (WHERE mag >= 6)/count(*),2) AS pct_m6_o_mas, max(mag) AS mag_max FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01';
\echo === Q4 profundidad
SELECT count(*) AS total, count(*) FILTER (WHERE depth_km < 70) AS superficiales_lt70, round(100.0*count(*) FILTER (WHERE depth_km < 70)/count(*),1) AS pct_lt70, count(*) FILTER (WHERE depth_km >= 300) AS profundos_ge300, round(100.0*count(*) FILTER (WHERE depth_km >= 300)/count(*),1) AS pct_ge300, round((percentile_cont(0.5) WITHIN GROUP (ORDER BY depth_km))::numeric,1) AS mediana_km FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01';
\echo === Q5 pais por hora UTC (hora con mas eventos)
SELECT extract(hour FROM event_time AT TIME ZONE 'UTC')::int AS hora_utc, count(*) AS n FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01' GROUP BY 1 ORDER BY n DESC LIMIT 3;

\echo === Q6 julio y agosto vs resto: Rusia por mes
SELECT to_char(date_trunc('month',e.event_time),'YYYY-MM') AS mes, count(*) AS n_total, count(*) FILTER (WHERE e.country_id='RUS') AS n_rus, count(*) FILTER (WHERE e.country_id IS NULL) AS n_sin_pais FROM live.current_event e WHERE NOT e.is_synthetic AND e.event_time >= '2025-01-01' AND e.event_time < '2026-01-01' GROUP BY 1 ORDER BY 1;
\echo === Q7 caja Kamchatka (lat 48-58, lon 155-165) por mes
SELECT to_char(date_trunc('month',event_time),'YYYY-MM') AS mes, count(*) AS n FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01' AND lat BETWEEN 48 AND 58 AND lon BETWEEN 155 AND 165 GROUP BY 1 ORDER BY 1;
\echo === Q8 evento mayor
SELECT event_id, mag, mag_type, event_time, place FROM live.current_event WHERE NOT is_synthetic AND event_time >= '2025-01-01' AND event_time < '2026-01-01' ORDER BY mag DESC LIMIT 1;
```

## Resultados (salida literal de psql, 2026-11-16)

```text
=== Q0 denominador
 eventos_2025 |          primero          |           ultimo           
--------------+---------------------------+----------------------------
        18302 | 2025-01-01 00:13:22.65+00 | 2025-12-31 23:52:11.327+00
(1 row)

=== Q1 por pais (top 6)
       pais        |   n   | pct  
-------------------+-------+------
 Sin país asignado | 14350 | 78.4
 China             |   354 |  1.9
 Chile             |   348 |  1.9
 Indonesia         |   306 |  1.7
 Etiopía           |   265 |  1.4
 Argentina         |   236 |  1.3
(6 rows)

=== Q2 por mes
   mes   |  n   
---------+------
 2025-01 | 1413
 2025-02 | 1394
 2025-03 | 1178
 2025-04 | 1316
 2025-05 | 1228
 2025-06 | 1156
 2025-07 | 2684
 2025-08 | 2222
 2025-09 | 1604
 2025-10 | 1509
 2025-11 | 1321
 2025-12 | 1277
(12 rows)

=== Q3 magnitud
 total | m4_a_49 | m5_a_59 | m6_a_69 | m7_o_mas | pct_m4 | pct_m6_o_mas | mag_max 
-------+---------+---------+---------+----------+--------+--------------+---------
 18302 |   16173 |    1984 |     129 |       16 |   88.4 |         0.79 |     8.8
(1 row)

=== Q4 profundidad
 total | superficiales_lt70 | pct_lt70 | profundos_ge300 | pct_ge300 | mediana_km 
-------+--------------------+----------+-----------------+-----------+------------
 18302 |              13689 |     74.8 |            1102 |       6.0 |       20.9
(1 row)

=== Q5 pais por hora UTC (hora con mas eventos)
 hora_utc |  n  
----------+-----
        3 | 832
       23 | 831
        4 | 814
(3 rows)


=== Q6 julio y agosto vs resto: Rusia por mes
   mes   | n_total | n_rus | n_sin_pais 
---------+---------+-------+------------
 2025-01 |    1413 |     3 |        803
 2025-02 |    1394 |     9 |       1125
 2025-03 |    1178 |     2 |        830
 2025-04 |    1316 |     1 |       1054
 2025-05 |    1228 |    10 |        931
 2025-06 |    1156 |     7 |        884
 2025-07 |    2684 |    19 |       2364
 2025-08 |    2222 |    29 |       1925
 2025-09 |    1604 |    28 |       1270
 2025-10 |    1509 |    21 |       1173
 2025-11 |    1321 |    12 |       1044
 2025-12 |    1277 |     9 |        947
(12 rows)

=== Q7 caja Kamchatka (lat 48-58, lon 155-165) por mes
   mes   |  n   
---------+------
 2025-01 |    8
 2025-02 |   16
 2025-03 |    7
 2025-04 |    9
 2025-05 |   12
 2025-06 |   13
 2025-07 | 1361
 2025-08 | 1239
 2025-09 |  586
 2025-10 |  265
 2025-11 |  217
 2025-12 |  104
(12 rows)

=== Q8 evento mayor
  event_id  | mag | mag_type |         event_time         |                    place                    
------------+-----+----------+----------------------------+---------------------------------------------
 us6000qw60 | 8.8 | mww      | 2025-07-29 23:24:52.483+00 | 2025 Kamchatka Peninsula, Russia Earthquake
(1 row)

```
