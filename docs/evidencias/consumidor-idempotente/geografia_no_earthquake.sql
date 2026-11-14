-- [1] exclusión del tipo distinto de earthquake
SELECT event_id, updated_ms, kind, reason, observed_type, is_synthetic FROM live.exclusion ORDER BY event_id;

