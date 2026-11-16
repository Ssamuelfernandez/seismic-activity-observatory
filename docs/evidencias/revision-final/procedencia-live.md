# Procedencia de `live` y valores observados del modelo (memoria §2 y §3)

Fecha de ejecución: 2026-11-16. Base: el PostgreSQL del stack levantado, solo lectura (`default_transaction_read_only=on`). Origen de las consultas: completar §2 (valores vistos de `status` y `mag_type`, nulos del modelo) y §3 (fuentes, nº de registros y fechas) de `docs/memoria.md`. Las cifras cambian con el tiempo porque el productor sigue ingiriendo; estas son las del 2026-11-16 (la memoria §4.4 usa las del 2026-11-15 y lo indica).

Nota: el registro `ingest.ingest_run` empieza el 2026-11-12 16:38 UTC; antes de esa fecha la base de `live` se creó de nuevo, por lo que las cifras del feed son desde entonces.

## Reproducir

```bash
docker compose exec -T postgres sh -c 'PGOPTIONS="-c default_transaction_read_only=on" psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < consulta.sql
```

## Consultas (solo SELECT)

```sql
\echo === P1 eventos actuales reales de live por fuente
SELECT source, count(*) AS n, min(event_time) AS primero, max(event_time) AS ultimo FROM live.current_event WHERE NOT is_synthetic GROUP BY source ORDER BY source;
\echo === P2 consultas al feed (ingest.ingest_run)
SELECT url, count(*) AS consultas, count(*) FILTER (WHERE status = 200 AND error IS NULL) AS correctas, count(*) FILTER (WHERE error IS NOT NULL OR status IS DISTINCT FROM 200) AS con_fallo, min(run_at) AS primera, max(run_at) AS ultima FROM ingest.ingest_run GROUP BY url;
\echo === P3 respuestas originales guardadas
SELECT count(*) AS respuestas, min(fetched_at) AS la_mas_antigua, max(fetched_at) AS la_mas_reciente FROM ingest.raw_response;
\echo === P4 exclusiones reales y sinteticos en live
SELECT is_synthetic, kind, count(*) FROM live.exclusion GROUP BY 1,2;
SELECT is_synthetic, count(*) AS eventos_actuales FROM live.current_event GROUP BY 1;
\echo === P5 catalogo de paises
SELECT count(*) AS paises FROM public.country;
\echo === D1 valores de status y mag_type en eventos reales de live
SELECT status, count(*) FROM live.current_event WHERE NOT is_synthetic GROUP BY 1 ORDER BY 2 DESC;
SELECT mag_type, count(*) FROM live.current_event WHERE NOT is_synthetic GROUP BY 1 ORDER BY 2 DESC;
SELECT count(*) FILTER (WHERE mag_type IS NULL) AS sin_mag_type, count(*) FILTER (WHERE status IS NULL) AS sin_status, count(*) FILTER (WHERE url IS NULL) AS sin_url, count(*) FILTER (WHERE sig IS NULL) AS sin_sig, count(*) FILTER (WHERE place IS NULL) AS sin_place FROM live.current_event WHERE NOT is_synthetic;
```

## Resultados (salida literal de psql)

```text
=== P1 eventos actuales reales de live por fuente
     source      |   n   |          primero          |           ultimo           
-----------------+-------+---------------------------+----------------------------
 usgs_feed       |  1083 | 2026-11-11 16:43:22.69+00 | 2026-11-16 17:37:56.26+00
 usgs_historical | 18302 | 2025-01-01 00:13:22.65+00 | 2025-12-31 23:52:11.327+00
(2 rows)

=== P2 consultas al feed (ingest.ingest_run)
                                    url                                    | consultas | correctas | con_fallo |            primera            |            ultima             
---------------------------------------------------------------------------+-----------+-----------+-----------+-------------------------------+-------------------------------
 https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson |      1762 |      1762 |         0 | 2026-11-12 16:38:13.403305+00 | 2026-11-16 18:10:14.387564+00
(1 row)

=== P3 respuestas originales guardadas
 respuestas |        la_mas_antigua         |        la_mas_reciente        
------------+-------------------------------+-------------------------------
        774 | 2026-11-12 16:38:13.403305+00 | 2026-11-16 18:07:13.767988+00
(1 row)

=== P4 exclusiones reales y sinteticos en live
 is_synthetic |        kind         | count 
--------------+---------------------+-------
 f            | non_earthquake_type |    95
(1 row)

 is_synthetic | eventos_actuales 
--------------+------------------
 f            |            19385
(1 row)

=== P5 catalogo de paises
 paises 
--------
    177
(1 row)

=== D1 valores de status y mag_type en eventos reales de live
  status   | count 
-----------+-------
 reviewed  | 18789
 automatic |   596
(2 rows)

 mag_type | count 
----------+-------
 mb       | 16428
 mww      |  1488
 ml       |   808
 mwr      |   355
 md       |   269
 mw       |    29
 mwb      |     6
 mb_lg    |     2
(8 rows)

 sin_mag_type | sin_status | sin_url | sin_sig | sin_place 
--------------+------------+---------+---------+-----------
            0 |          0 |       0 |       0 |         0
(1 row)

```
