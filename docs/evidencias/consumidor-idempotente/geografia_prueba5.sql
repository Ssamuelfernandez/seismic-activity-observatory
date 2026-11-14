-- [1] current_event: mag NULL, país ESP
SELECT event_id, mag, depth_km, country_id, is_synthetic FROM live.current_event WHERE event_id = 'synthetic-geo-mag-nula';

-- [2] event_version: mag NULL
SELECT event_id, mag FROM live.event_version WHERE event_id = 'synthetic-geo-mag-nula';

-- [3] filas con mag = 0
SELECT (SELECT count(*) FROM live.current_event WHERE mag = 0) AS current_mag_cero, (SELECT count(*) FROM live.event_version WHERE mag = 0) AS version_mag_cero;

-- [4] negativos: mag y profundidad tal cual
SELECT event_id, mag, depth_km, country_id, is_synthetic FROM live.current_event WHERE event_id = 'synthetic-geo-negativos';

