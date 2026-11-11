# Contraste mock / API real / parse.ts (T034)

Fecha: 2026-11-10. API real de Compose en `http://127.0.0.1:8000` y a través del proxy de Vite (`http://localhost:4300/api`, ya con `mode: "api"`).
Salidas: `T034_curl_directo_8000.txt`, `T034_curl_proxy_4300.txt`, `T034_contraste_salida.txt`, respuestas `T034_resp_*.json` (eventos recortada a 5 features), y el script temporal `T034_prueba_temporal.test.ts.txt` (no queda en el repo).
Los tres endpoints pasan `parseHealth`/`parseEvents`/`parseStats` sin `ApiError`, tanto en directo como por el proxy (mismas respuestas).

| Aspecto | API real | Mock (`base`) | Acción |
|---|---|---|---|
| `/salud` | `{status:"ok", last_ingestion:<ms>, generated:<ms>}` | igual | Ninguna |
| `metadata` de eventos | 8 campos: `generated, last_ingestion, mode, count, total, truncated, next_cursor, null_mag_excluded` | los mismos 8 | Ninguna |
| `truncated` | `true` si `count < total` (comprobado con `limit=3`: count 3, total 205, `next_cursor` con texto) | `truncated.json` con `truncated: true` y cursor | Ninguna |
| Orden | `time` descendente (206 eventos) | `time` descendente | Ninguna |
| `id` | texto (`nc75464922`, `ok2026wbhv`) | texto (`mock-base-001`) | Ninguna |
| Coordenadas | `[lon, lat, depth]`, 3 valores finitos; profundidad con muchos decimales (`1.55999994277954`); 2 profundidades negativas en la muestra | 3 valores; profundidad `null` en 2 eventos | Ninguna (el front formatea los decimales) |
| Propiedades | 11 claves exactas (`country_id, country_name, is_synthetic, mag, magType, place, sig, status, time, updated, url`) | las mismas 11 | Ninguna |
| Nulos en eventos | en la muestra real: 1 `place` nulo, 0 `mag`/`magType`/profundidad nulos; el contrato los admite y `parse` los conserva | `mag` nulo (2), `magType` nulo (2), profundidad nula (2), `place` nulo (1), `url`/`sig` nulos | Ninguna: el mock cubre los casos que la muestra real no trae |
| Sin país | 37 eventos con `country_id` y `country_name` ambos `null` (coherentes) | 9 sin país, ambos `null` | Ninguna |
| `is_synthetic` | `false` en todos | `true` en todos (etiquetado «Sintético») | Ninguna (esperado) |
| `/estadisticas` claves | `metadata, period, filters, total, by_hour, by_country, histograms, comparison` | las mismas | Ninguna |
| `by_hour` | `unit:"events"`, 25 buckets en 24 h, `no_value 0`, suma = `total` | buckets por hora, suma = total | Ninguna |
| `by_country` | 8 ítems, orden `count` desc, elemento propio con país `null` (37) y `no_value` = 37 (informativo, no suma aparte) | idem | Ninguna |
| Histograma de magnitud | 8 tramos: `[null,1)`, 1–2 … 6–7, `[7,null)`; suma = total | 8 tramos | Ninguna |
| Histograma de profundidad | 5 tramos: `[null,10)`, 10–35, 35–70, 70–300, `[300,null)`; suma = total | 5 tramos | Ninguna |
| `comparison` | objeto completo: `min_mag_applied 4`, `n_recent 21`, `n_2025 18302` (histórico 006 cargado), `daily_mean_2025 50.14…`, `variation_pct -58.12`, `recent_incomplete true` | mismos campos | Ninguna |
| `comparison` en replay | `null` (ver T035) | `replay.json` con `null` | Ninguna |
| `last_ingestion` | número (ms); `generated − last_ingestion` ≈ 4 s en la muestra | número | Ninguna |
| Cabeceras | `application/json`; por el proxy añade `Vary: Origin` | n/a | Ninguna |

Resultado: no hay divergencias que obliguen a tocar el mock ni el front. El contrato y la API coinciden en lo comprobado.

Límites conocidos: (1) la muestra real de este momento no trae magnitud, `magType` ni profundidad nulas; esos caminos se prueban con el mock y con `parse`; (2) en `replay` las estadísticas devuelven 8 760 buckets horarios a cero (2025 entero) y el gráfico por hora los pinta como 8 760 barras vacías; se anota, no se cambia.
