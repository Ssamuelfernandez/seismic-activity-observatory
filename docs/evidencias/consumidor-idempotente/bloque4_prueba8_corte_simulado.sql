-- [1] event_version tras corte en el offset 2 y reinicio
SELECT event_id, updated_ms, mag, kafka_offset FROM live.event_version ORDER BY 1, 2;

-- [2] current_event tras corte en el offset 2 y reinicio
SELECT event_id, mag, updated_ms FROM live.current_event ORDER BY 1;

