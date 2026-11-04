SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY event_id;
SELECT event_id, updated_ms, mag FROM live.event_version ORDER BY event_id, updated_ms;
SELECT count(*) AS current_rows FROM live.current_event;
SELECT count(*) AS version_rows FROM live.event_version;
