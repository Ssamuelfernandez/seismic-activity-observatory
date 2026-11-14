-- [1] current_event: únicos - cuarentena, origen y marca sintética
SELECT count(*), count(*) FILTER (WHERE source = 'usgs_historical'), count(*) FILTER (WHERE is_synthetic), count(*) FILTER (WHERE replay_at IS NULL), count(DISTINCT ingested_at), min(ingested_at) FROM live.current_event;

-- [2] event_version y cuarentena: una fila por (id, updated); kafka_* nulos
SELECT (SELECT count(*) FROM live.event_version), (SELECT count(*) FROM live.event_version WHERE kafka_topic IS NOT NULL OR kafka_partition IS NOT NULL OR kafka_offset IS NOT NULL), (SELECT count(*) FROM live.quarantine), (SELECT count(*) FROM live.quarantine WHERE kafka_topic IS NOT NULL OR kafka_partition IS NOT NULL OR kafka_offset IS NOT NULL);

-- [3] cuarentena por evento inválido
SELECT event_id, reason FROM live.quarantine ORDER BY event_id;

