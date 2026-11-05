-- [1] antes
SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY event_id;

-- [2] antes
SELECT event_id, updated_ms, mag FROM live.event_version ORDER BY event_id, updated_ms;

-- [3] antes
SELECT count(*) AS current_rows FROM live.current_event;

-- [4] antes
SELECT count(*) AS version_rows FROM live.event_version;

-- [5] despues
SELECT event_id, mag, updated_ms, is_synthetic FROM live.current_event ORDER BY event_id;

-- [6] despues
SELECT event_id, updated_ms, mag FROM live.event_version ORDER BY event_id, updated_ms;

-- [7] despues
SELECT count(*) AS current_rows FROM live.current_event;

-- [8] despues
SELECT count(*) AS version_rows FROM live.event_version;

