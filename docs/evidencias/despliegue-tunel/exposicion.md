# Revisión de exposición de la API (T066, T067)

Fecha: 2026-11-12. API de Compose en `http://127.0.0.1:8000` (misma imagen que vería el túnel). No se abrió ningún túnel.
Salidas brutas: `T066_respuestas_brutas.txt`, `T066_limite_y_recuentos.txt`, `T067_puertos_secretos.txt`.

**Desviación (T066(3)):** sin lectura de `.env` por regla del alumno; comprobación por patrones genéricos, no por los valores reales de `POSTGRES_*` / `DB_*`.

## T066

| # | Comprobación | Comando | Esperado | Observado | Veredicto |
|---|---|---|---|---|---|
| 1a | GET a las 3 rutas | `curl $B/api/salud`, `/api/eventos`, `/api/estadisticas` | 200 | 200 en las tres (`/api/salud` `{"status":"ok",...}`) | OK |
| 1b | Rutas no publicadas | `curl $B/docs`, `/redoc`, `/openapi.json`, `/admin`, `/api/admin` | 404 con cuerpo común | 404 `{"error":{"code":"not_found",...}}` en todas (ver brutas) | OK |
| 2 | Escritura rechazada | `curl -X POST/PUT/PATCH/DELETE` a las 3 rutas (12 peticiones) | 405 `{"error":...}` | 405 `method_not_allowed` en las 12 | OK |
| 2b | Datos sin cambios | `total` de `/api/estadisticas` (rango 2000-2100) antes y después de las 12 escrituras | igual | 18554 antes y 18554 después | OK |
| 3 | Sin secretos en respuestas | `grep -c -i -E 'password\|passwd\|secret\|token\|POSTGRES_\|DB_PASSWORD\|postgres://\|postgresql://\|Traceback\|File "\|usuario:clave@'` sobre respuestas 200 (salud, eventos, estadísticas) y de error (400 mode, 400 cursor, 400 limit, 404, 405) | 0 | 0 coincidencias en todos los ficheros | OK (por patrones) |
| 4a | Sin `limit`, rango amplio (2000-2100, total 18554) | `GET /api/eventos?start=...&end=...` | ≤ 5000 | 5000 features, `truncated=true`, `next_cursor` presente; la página 2 con ese cursor devuelve 5000 y `truncated=true` | OK |
| 4b | `limit=999999` | igual con `&limit=999999` | ≤ 5000 | **400** `invalid_parameter` (máx. 5000), 0 eventos. Se rechaza en lugar de recortar | OK (hallazgo menor, ver abajo) |
| 4c | `limit=5000` / `5001` | idem | 5000 / rechazo | 5000 con `truncated=true` / 400 | OK |

Argumento por código (sin leer `.env`): `api/errors.py` construye todos los errores solo con código y mensaje fijos en español (sin `detail`, sin texto de excepción); los 500 y 503 usan mensajes constantes. Los routers (`events.py`, `health.py`, `stats.py`) no importan ni serializan variables de entorno; solo usan `api_settings.db_timeout_seconds` internamente. No se devuelve ningún campo de configuración.

## T067

| Fila | Comprobación | Observado | Veredicto |
|---|---|---|---|
| (a) | `.gitignore` con `.cloudflared/`, `cert.pem`, `cloudflared*.yml`, `cloudflared*.yaml`, `cloudflared-credentials*.json` junto al bloque de ngrok (que se mantiene) | `git check-ignore -v` reconoce `.cloudflared/x`, `cert.pem`, `cloudflared-credentials-x.json`, `cloudflared.yml`, `cloudflared-x.yaml` | OK |
| (b1) | `docker compose -f compose.yaml config` (ignora el override) | Único puerto publicado: `host_ip 127.0.0.1`, `target 8000`, `published "8000"` (servicio `api`). `postgres`, `kafka`, `producer`, `consumer` sin `ports`; no hay 5432 ni 9092 publicados | OK |
| (b2) | `docker ps` real | `api` `127.0.0.1:8000->8000/tcp`; `kafka` solo `9092/tcp` (sin publicar); **`postgres` `127.0.0.1:5433->5432/tcp`** | Hallazgo local |
| (b3) | `git ls-files \| grep -i -E "cloudflared\|cert.pem\|credentials"` | 0 resultados | OK |
| (c) | Patrones de token y nombres de credenciales sobre `git ls-files -o -m --exclude-standard` (25 ficheros; `.env` real excluido sin abrir) | Solo placeholders de `.env.example` (`cambia-esta-clave-*`), una mención de «authtoken» en un comentario de `.gitignore` y texto de `tasks.md`. Sin tokens ni ficheros de credenciales | OK |
| (d) | Captura de la configuración del túnel con `http://localhost:8000` como único destino, token tapado | | **Pendiente del alumno** |

## Hallazgos

1. **Local, no del repo:** `compose.override.yaml` (ignorado por Git, no se borra) publica PostgreSQL en `127.0.0.1:5433`. Solo escucha en loopback y no entra en lo entregado; el túnel solo debe apuntar a `localhost:8000`. Para quitarlo en la sesión de túnel: borrar el override y `docker compose up -d postgres` (README, «Acceso a la base de datos»).
2. `limit` por encima de 5000 se responde con 400 y no se recorta; el máximo de 5000 se cumple en ambos casos.
3. Sin cambios de código de la API: ninguna comprobación F9, F10 ni F5 falló.
