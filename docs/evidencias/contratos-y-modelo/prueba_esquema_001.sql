\set ON_ERROR_STOP off
\pset pager off
\set t 1793528210440
\set u 1793528420510

\echo '=== Catalogo y fechas (precarga)'
INSERT INTO public.country VALUES
  ('ESP','España','Spain','Europe','Southern Europe'),
  ('USA','Estados Unidos','United States of America','North America','Northern America');
INSERT INTO public.date_dim
  SELECT d::date, extract(year from d), extract(month from d), extract(day from d), extract(isodow from d)
  FROM generate_series('2026-10-29'::date, '2026-11-04'::date, '1 day') d;

CREATE FUNCTION pg_temp.ev(p_id text, p_time bigint, p_updated bigint, p_mag numeric, p_depth numeric,
                           p_lat double precision DEFAULT 33.54, p_country text DEFAULT 'USA',
                           p_source text DEFAULT 'usgs_feed') RETURNS void LANGUAGE sql AS $$
  INSERT INTO live.current_event (event_id,event_time,event_time_ms,updated_at,updated_ms,mag,depth_km,lon,lat,
                                  country_id,date_id,source,ingested_at)
  VALUES (p_id, timestamptz 'epoch' + p_time*interval '1 millisecond', p_time,
          timestamptz 'epoch' + p_updated*interval '1 millisecond', p_updated, p_mag, p_depth, -116.7, p_lat,
          p_country, ((timestamptz 'epoch' + p_time*interval '1 millisecond') AT TIME ZONE 'UTC')::date,
          p_source, now())
$$;

\echo '=== T1 valido con mag -0.06 y profundidad -0.18 (esperado: OK)'
SELECT pg_temp.ev('ci1', :t, :u, -0.06, -0.18);
\echo '=== T2 magnitud nula y profundidad nula (esperado: OK)'
SELECT pg_temp.ev('ci_null', :t, :u, NULL, NULL);
\echo '=== T3 lat 145 (esperado: ERROR current_event_lat_range)'
SELECT pg_temp.ev('bad_lat', :t, :u, 2.0, 5.0, 145);
\echo '=== T4 mag NaN (esperado: ERROR current_event_mag_range)'
SELECT pg_temp.ev('bad_nan', :t, :u, 'NaN'::numeric, 5.0);
\echo '=== T5 source invalido (esperado: ERROR current_event_source_values)'
SELECT pg_temp.ev('bad_src', :t, :u, 2.0, 5.0, 33.54, 'USA', 'foo');
\echo '=== T6 pais inexistente (esperado: ERROR FK country)'
SELECT pg_temp.ev('bad_cty', :t, :u, 2.0, 5.0, 33.54, 'ZZZ');
\echo '=== T7 ms no coincide con el timestamptz (esperado: ERROR current_event_time_matches_ms)'
INSERT INTO live.current_event (event_id,event_time,event_time_ms,updated_at,updated_ms,lon,lat,date_id,source,ingested_at)
VALUES ('bad_ms', timestamptz 'epoch' + 1793528210441*interval '1 millisecond', 1793528210440,
        timestamptz 'epoch' + :u*interval '1 millisecond', :u, 0, 0, '2026-11-01', 'usgs_feed', now());
\echo '=== T8 date_id incoherente (esperado: ERROR current_event_date_matches_time)'
INSERT INTO live.current_event (event_id,event_time,event_time_ms,updated_at,updated_ms,lon,lat,date_id,source,ingested_at)
VALUES ('bad_date', timestamptz 'epoch' + :t*interval '1 millisecond', :t,
        timestamptz 'epoch' + :u*interval '1 millisecond', :u, 0, 0, '2026-10-30', 'usgs_feed', now());

\echo '=== T9 version antes que el estado actual en la misma transaccion (esperado: OK, FK diferida)'
BEGIN;
INSERT INTO live.event_version (event_id,updated_ms,updated_at,event_time,mag,original,source,received_at)
VALUES ('ci2', :u, timestamptz 'epoch' + :u*interval '1 millisecond', timestamptz 'epoch' + :t*interval '1 millisecond', 3.1, '{"id":"ci2"}', 'usgs_feed', now());
SELECT pg_temp.ev('ci2', :t, :u, 3.1, 8.0);
COMMIT;
\echo '=== T10 version sin estado actual (esperado: ERROR FK al hacer COMMIT)'
BEGIN;
INSERT INTO live.event_version (event_id,updated_ms,updated_at,event_time,original,source,received_at)
VALUES ('ghost', :u, timestamptz 'epoch' + :u*interval '1 millisecond', timestamptz 'epoch' + :t*interval '1 millisecond', '{"id":"ghost"}', 'usgs_feed', now());
COMMIT;

\echo '=== T11 reglas de versiones sobre ci1 (updated inicial = 1793528420510, mag -0.06)'
CREATE FUNCTION pg_temp.upsert(p_updated bigint, p_mag numeric) RETURNS void LANGUAGE sql AS $$
  INSERT INTO live.event_version (event_id,updated_ms,updated_at,event_time,mag,original,source,received_at)
  VALUES ('ci1', p_updated, timestamptz 'epoch' + p_updated*interval '1 millisecond', timestamptz 'epoch' + 1793528210440*interval '1 millisecond', p_mag, '{"id":"ci1"}', 'usgs_feed', now())
  ON CONFLICT (event_id, updated_ms) DO NOTHING;
  INSERT INTO live.current_event (event_id,event_time,event_time_ms,updated_at,updated_ms,mag,lon,lat,date_id,source,ingested_at)
  VALUES ('ci1', timestamptz 'epoch' + 1793528210440*interval '1 millisecond', 1793528210440,
          timestamptz 'epoch' + p_updated*interval '1 millisecond', p_updated, p_mag, -116.7, 33.54, '2026-11-01', 'usgs_feed', now())
  ON CONFLICT (event_id) DO UPDATE SET mag = EXCLUDED.mag, updated_ms = EXCLUDED.updated_ms, updated_at = EXCLUDED.updated_at
  WHERE EXCLUDED.updated_ms > live.current_event.updated_ms;
$$;
BEGIN; SELECT pg_temp.upsert(1793528420510, 9.0); COMMIT;
SELECT 'igual -> mag debe seguir en -0.06' AS caso, mag, updated_ms FROM live.current_event WHERE event_id='ci1';
BEGIN; SELECT pg_temp.upsert(1793528520510, 1.5); COMMIT;
SELECT 'mayor -> mag debe pasar a 1.5' AS caso, mag, updated_ms FROM live.current_event WHERE event_id='ci1';
BEGIN; SELECT pg_temp.upsert(1793528320510, 7.0); COMMIT;
SELECT 'antigua tardia -> mag sigue en 1.5' AS caso, mag, updated_ms FROM live.current_event WHERE event_id='ci1';
SELECT 'versiones de ci1 (esperado 3: inicial no existe, 420510 reenvio, 520510, 320510)' AS caso, updated_ms, mag FROM live.event_version WHERE event_id='ci1' ORDER BY updated_ms;
\echo '--- reenvio idempotente: insertar de nuevo la misma version devuelve 0 filas'
INSERT INTO live.event_version (event_id,updated_ms,updated_at,event_time,original,source,received_at)
VALUES ('ci1', 1793528520510, timestamptz 'epoch' + 1793528520510*interval '1 millisecond', timestamptz 'epoch' + 1793528210440*interval '1 millisecond', '{}', 'usgs_feed', now())
ON CONFLICT (event_id, updated_ms) DO NOTHING RETURNING updated_ms;

\echo '=== T12 cuarentena'
INSERT INTO live.quarantine (event_id,reason,raw_text,original_sha256,received_at)
VALUES (NULL,'invalid_json','{no json',repeat('a',64),now());
\echo '--- mismo original y motivo con ON CONFLICT DO NOTHING (0 filas)'
INSERT INTO live.quarantine (event_id,reason,raw_text,original_sha256,received_at)
VALUES (NULL,'invalid_json','{no json',repeat('a',64),now()) ON CONFLICT (original_sha256, reason) DO NOTHING RETURNING id;
\echo '--- mismo original y motivo sin ON CONFLICT (esperado: ERROR unique)'
INSERT INTO live.quarantine (event_id,reason,raw_text,original_sha256,received_at)
VALUES (NULL,'invalid_json','{no json',repeat('a',64),now());
\echo '--- sin original ni raw_text (esperado: ERROR quarantine_has_original)'
INSERT INTO live.quarantine (reason,original_sha256,received_at) VALUES ('invalid_json',repeat('b',64),now());

\echo '=== T13 exclusion unica (esperado: 2o insert ERROR)'
INSERT INTO live.exclusion (event_id,updated_ms,kind,reason,observed_type,fetched_at) VALUES ('q1',:u,'non_earthquake_type','tipo','quarry blast',now());
INSERT INTO live.exclusion (event_id,updated_ms,kind,reason,observed_type,fetched_at) VALUES ('q1',:u,'non_earthquake_type','tipo','quarry blast',now());

\echo '=== T14 aislamiento: replay independiente de live'
INSERT INTO replay.current_event (event_id,event_time,event_time_ms,updated_at,updated_ms,lon,lat,date_id,source,ingested_at,replay_at)
VALUES ('r1', timestamptz 'epoch' + :t*interval '1 millisecond', :t, timestamptz 'epoch' + :u*interval '1 millisecond', :u, 0, 0, '2026-11-01', 'replay_demo', now(), now());
SELECT (SELECT count(*) FROM live.current_event) AS live_events, (SELECT count(*) FROM replay.current_event) AS replay_events;

\echo '=== T15 ingest'
INSERT INTO ingest.ingest_run (run_at,url,status,latency_ms,event_count,sha256,error) VALUES (now(),'u',200,120,210,repeat('c',64),NULL);
INSERT INTO ingest.ingest_run (run_at,url,error) VALUES (now(),'u','timeout');
\echo '--- latencia negativa (esperado: ERROR)'
INSERT INTO ingest.ingest_run (run_at,url,status,latency_ms) VALUES (now(),'u',200,-5);
SELECT 'last_ingestion (ultima correcta)' AS caso, max(run_at) IS NOT NULL AS ok FROM ingest.ingest_run WHERE error IS NULL AND status = 200;

\echo '=== T16 consulta Q1 (paginacion por cursor) y Q4 (conteo por hora UTC)'
SELECT event_id, event_time FROM live.current_event
WHERE event_time >= '2026-10-29' AND event_time < '2026-11-05'
  AND (event_time, event_id) < (timestamptz 'epoch' + :t*interval '1 millisecond', 'zzzz')
ORDER BY event_time DESC, event_id DESC LIMIT 2;
SELECT date_trunc('hour', event_time AT TIME ZONE 'UTC') AS hora_utc, count(*) FROM live.current_event GROUP BY 1 ORDER BY 1;

\echo '=== T17 evento nuevo: una fila en current_event y una en event_version (esperado: 1 y 1)'
BEGIN;
INSERT INTO live.event_version (event_id,updated_ms,updated_at,event_time,mag,original,source,received_at)
VALUES ('ci_new', :u, timestamptz 'epoch' + :u*interval '1 millisecond', timestamptz 'epoch' + :t*interval '1 millisecond', 2.5, '{"id":"ci_new","v":"primera"}', 'usgs_feed', now())
ON CONFLICT (event_id, updated_ms) DO NOTHING;
SELECT pg_temp.ev('ci_new', :t, :u, 2.5, 5.0);
COMMIT;
SELECT (SELECT count(*) FROM live.current_event WHERE event_id = 'ci_new') AS filas_current_event,
       (SELECT count(*) FROM live.event_version WHERE event_id = 'ci_new') AS filas_event_version;

\echo '=== T18 mismo (event_id, updated_ms) con original distinto: ON CONFLICT DO NOTHING conserva la primera (esperado: 0 filas insertadas y original = primera)'
INSERT INTO live.event_version (event_id,updated_ms,updated_at,event_time,mag,original,source,received_at)
VALUES ('ci_new', :u, timestamptz 'epoch' + :u*interval '1 millisecond', timestamptz 'epoch' + :t*interval '1 millisecond', 9.9, '{"id":"ci_new","v":"segunda"}', 'usgs_feed', now())
ON CONFLICT (event_id, updated_ms) DO NOTHING RETURNING updated_ms;
SELECT count(*) AS versiones, min(original->>'v') AS original_conservado, min(mag) AS mag_conservada
FROM live.event_version WHERE event_id = 'ci_new' AND updated_ms = :u;

\echo '=== Inventario: tablas por esquema e indices'
SELECT table_schema, count(*) AS tablas FROM information_schema.tables
WHERE table_schema IN ('public','live','replay','ingest') AND table_type='BASE TABLE' GROUP BY 1 ORDER BY 1;
SELECT schemaname, indexname FROM pg_indexes WHERE schemaname IN ('live','replay','ingest') AND indexname LIKE 'ix_%' ORDER BY 1,2;
