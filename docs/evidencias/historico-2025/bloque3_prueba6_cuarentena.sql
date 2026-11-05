-- [1] un caso por motivo
SELECT 'live' AS schema, reason, kafka_topic, kafka_partition, kafka_offset, original_sha256 FROM live.quarantine UNION ALL SELECT 'replay', reason, kafka_topic, kafka_partition, kafka_offset, original_sha256 FROM replay.quarantine ORDER BY 1, 5;

-- [2] latitud 145 (prueba 6)
SELECT reason, event_id, kafka_topic, kafka_partition, kafka_offset, original_sha256 FROM live.quarantine;

