-- Verificación como administrador de la carga histórica 2025 (data-model §6).
SELECT source, is_synthetic, count(*) FROM live.current_event GROUP BY 1,2 ORDER BY 1,2;
SELECT count(*) AS historical_current FROM live.current_event WHERE source = 'usgs_historical';
SELECT count(*) AS historical_versions FROM live.event_version WHERE source = 'usgs_historical';
SELECT count(*) AS historical_quarantine FROM live.quarantine WHERE source = 'usgs_historical';
SELECT count(*) AS historical_with_null_country FROM live.current_event WHERE source = 'usgs_historical' AND country_id IS NULL;
SELECT count(*) AS historical_kafka_not_null FROM live.event_version WHERE source = 'usgs_historical' AND (kafka_topic IS NOT NULL OR kafka_offset IS NOT NULL);
SELECT to_char(event_time AT TIME ZONE 'UTC','YYYY-MM') AS month, count(*) FROM live.current_event WHERE source = 'usgs_historical' GROUP BY 1 ORDER BY 1;
SELECT count(*) AS n, md5(string_agg(event_id||'|'||updated_ms::text, '#' ORDER BY event_id)) AS fingerprint_historical FROM live.current_event WHERE source = 'usgs_historical';
SELECT count(*) AS n, md5(string_agg(event_id||'|'||updated_ms::text, '#' ORDER BY event_id, updated_ms)) AS fingerprint_versions FROM live.event_version WHERE source = 'usgs_historical';
