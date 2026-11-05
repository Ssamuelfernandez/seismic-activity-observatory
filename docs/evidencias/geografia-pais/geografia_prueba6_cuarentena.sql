-- [1] cuarentena de los casos inválidos (referencia Kafka y hash)
SELECT event_id, reason, kafka_topic, kafka_partition, kafka_offset, left(original_sha256, 12) AS sha FROM live.quarantine ORDER BY kafka_offset;

-- [2] eventos guardados: todos sintéticos
SELECT event_id, is_synthetic FROM live.current_event ORDER BY event_id;

