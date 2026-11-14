-- [1] Madrid: país por geometría
SELECT event_id, country_id, place FROM live.current_event WHERE event_id = 'synthetic-geo-madrid';

-- [2] Atlántico: fila con country_id vacío (NULL) y sin cuarentena
SELECT event_id, country_id, place FROM live.current_event WHERE event_id LIKE 'synthetic-geo-%' ORDER BY event_id;

-- [3] total = con país + sin país
SELECT count(*) AS total, count(country_id) AS con_pais, count(*) - count(country_id) AS sin_pais FROM live.current_event;

-- [4] Filas de los casos geográficos
SELECT event_id, country_id, place FROM live.current_event WHERE event_id LIKE 'synthetic-geo-%' ORDER BY event_id;

