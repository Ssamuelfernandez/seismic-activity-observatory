# Research: Productor en vivo

Decisiones de diseño con su alternativa descartada. Las ya fijadas en las Clarifications de la spec (feed, hash sobre `features`, retención de 7 días, backoff 2 s a 60 s con jitter, timeout 10 s, latido, `POLL_SECONDS`) no se repiten aquí; solo se citan cuando el plan añade detalle.

## 1. Cliente HTTP: `urllib` de la biblioteca estándar en un hilo

- **Decisión**: `urllib.request.urlopen(..., timeout)` ejecutado con `asyncio.to_thread`, igual que `scripts/explore_usgs.py`.
- **Motivo**: cero dependencias nuevas (constitución §11: `uv.lock` no cambia). Una consulta por minuto no necesita cliente asíncrono.
- **Descartado**: `httpx`/`aiohttp` (dependencia nueva sin beneficio a esta escala).
- **Detalle**: `HTTPError` aporta el código (429, 5xx) y se registra con `status`; `TimeoutError`/`URLError` se registran sin `status`. El cuerpo se lee entero en bytes y se decodifica después.

## 2. Orden de operaciones de un ciclo

1. `GET` al feed. El instante de recepción es `ingested_at` de todos los mensajes del ciclo.
2. Validar el cuerpo (JSON, objeto con lista `features`). Si falla: fila de error en `ingest_run` y fin.
3. **Una transacción**: calcular el hash de `features`, insertar el cuerpo en `raw_response` solo si el hash difiere del de la última consulta correcta, e insertar la fila de `ingest_run`. Es el "guardar el original antes de transformar" de B4. Ambas escrituras juntas evitan una consulta registrada sin su original.
4. Clasificar cada elemento (puro): excluido, publicable con marca, publicable sin marca u omitido. Insertar las exclusiones (`ON CONFLICT DO NOTHING`).
5. Leer `ingest_state` de los `id` publicables en **una** consulta (`event_id = ANY($1)`).
6. Para cada evento a publicar: `send_and_wait` (ack) y **después** `UPSERT` en `ingest_state` (B9). Un evento, un ack, una marca.
7. Fin de ciclo correcto: renovar el latido, purgar `raw_response` antiguas (un fallo de purga solo se registra en el log), esperar `POLL_SECONDS`.

- **Fallo de Kafka a mitad del paso 6**: el ciclo se interrumpe en ese evento; los anteriores ya están marcados. Se registra el error en el **log** y se aplica backoff. No se añade una segunda fila a `ingest_run`: esa tabla describe la consulta al feed, que fue correcta (el contrato la define así, `db-schema.md` §3.8). La Clarification de la spec decía "el ciclo se registra con error"; se entiende como registro en el log y la spec se ha ajustado en ese sentido.
- **Fallo de PostgreSQL** en cualquier paso: ciclo fallido, sin latido, backoff. El pool de `asyncpg` reconecta solo.
- **Alternativa descartada**: escribir `ingest_run` al final del ciclo. Un corte durante la publicación dejaría el original guardado sin consulta registrada, y el siguiente ciclo guardaría un duplicado de `raw_response`.

## 3. Tabla de decisión por evento (B6, FR-005)

Función pura `decide_publication(feature, last_updated_ms)`:

| Caso | `type` | `id` y `updated` válidos | Estado previo | Resultado |
|---|---|---|---|---|
| a | distinto de `earthquake` (o ausente) | sí | cualquiera | `EXCLUDE` (fila en `exclusion`, `observed_type` nulo si falta) |
| b | cualquiera | no (falta `id` o `updated`, o tipo incorrecto) | — | `PUBLISH_UNMARKED` (clave nula si falta `id`; el consumidor lo lleva a cuarentena; sin fila en `ingest_state`) |
| c | `earthquake` | sí | sin fila | `PUBLISH` |
| d | `earthquake` | sí | `updated` > `last_updated_ms` | `PUBLISH` |
| e | `earthquake` | sí | `updated` <= `last_updated_ms` | `SKIP` |

- "Válido" aquí es solo "se puede comparar": `id` es texto no vacío y `updated` es entero (no booleano). La validación completa (rangos, geometría) es del consumidor.
- Prevalece la invalidez sobre la exclusión por tipo (caso b antes que a), como fija `kafka-message.md` §3.
- Un elemento de `features` que no es un objeto JSON se descarta con un aviso en el log (límite conocido; no ocurre en el feed real).

## 4. Hash de `features` y comparación

- **Formato canónico**: `json.dumps(features, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` codificado en UTF-8, SHA-256 en hexadecimal (64 caracteres, `db-schema.md` §3.9).
- **Comparación**: con el `sha256` de la última fila de `ingest_run` con `error IS NULL AND status = 200` (índice `ix_ingest_run_last_ok`, Q8). Es una consulta de lectura sobre `ingest_run`, que el rol ya puede hacer.
- **Cuerpo guardado**: la respuesta completa tal cual llegó, como `jsonb` (se pasa como texto con `$n::jsonb`, sin códec). `jsonb` normaliza espacios y orden de claves; es el tipo que fija el contrato.
- **Cuerpo "idéntico" y tiempo**: `metadata.generated` cambia cada minuto, por eso el hash no lo incluye (Clarification).

## 5. Purga de `raw_response` y permisos

- Consulta Q9: `DELETE FROM ingest.raw_response WHERE fetched_at < now() - retención AND id <> (SELECT max(id) ...)`. Conservar siempre la fila más reciente evita que, con un feed idéntico durante más de la retención, el hash de referencia apunte a una fila ya borrada. Es una línea en la consulta, no un mecanismo.
- **Permisos**: `DELETE ... WHERE fetched_at < ...` y la subconsulta `max(id)` necesitan también `SELECT` sobre la tabla. Hay que conceder `SELECT, DELETE` (no solo `DELETE`) a `observatory_producer`. El cambio va en `sql/002_roles.sql` (no es contrato).
- **Sincronía de redacción, sin cambio de contrato (`db-schema.md` §1.1)**: esa tabla da a `raw_response` solo "Escribe: Productor; Lee: consultas de evidencia". Con `SELECT` y `DELETE` el productor también lee y borra su propia tabla; la feature solo concreta §3.9 (retención). `db-schema.md` NO se edita; el `GRANT` vive en `sql/002_roles.sql`, que no es contrato.
- **Volumen existente**: `postgres_init.sh` solo corre con volumen nuevo. Para uno existente se reaplica el `GRANT` con `psql` (quickstart §0) o se hace `down -v`.
- Para `live.exclusion` basta `INSERT ... ON CONFLICT DO NOTHING` (sin objetivo de conflicto y sin `RETURNING`), que no necesita `SELECT`.

## 6. Dónde vive cada cosa (constitución §14)

- Puro, en `common/` (lo reutilizan `historico-2025` y `replay`): `usgs_feed.py` (validar el cuerpo, hash), `ingest_decision.py` (clasificar, fila de exclusión), `live_message.py` (construir el mensaje), `backoff.py` (cálculo de la espera).
- E/S, en `producer/`: `usgs_client.py` (HTTP), `ingest_queries.py` (SQL) y `ingest_store.py` (funciones asyncpg), `cycle.py` (un ciclo, orquestación), `loop.py` (bucle, backoff, latido), `publisher.py` (se conserva), `main.py` (solo configura).
- La configuración nueva va en `common/config.py` (`FeedSettings`, `load_feed_settings`).
- El backoff recibe sus parámetros en un objeto (`BackoffSettings`) para que las pruebas usen esperas de milisegundos. Los valores de producción (2 s y 60 s) son constantes con nombre, no variables de entorno.

## 7. Simular USGS (FR-014)

- **Decisión**: servidor `http.server` de la biblioteca estándar en un hilo, dentro de las pruebas (`tests/support/mock_usgs.py`). Escucha en el puerto 0 del propio proceso de pruebas; no es un servicio de Compose ni se publica nada (constitución §9 y §10: el productor de la prueba y el mock están en el mismo proceso).
- Sabe responder: cuerpo correcto con los `features` que se le indiquen, 500, 429, espera mayor que el timeout y cuerpo no JSON. Los eventos del mock son sintéticos y llevan `id` `synthetic-…` (constitución §7, CLAUDE.md); nunca llegan a una base real.
- **Descartado**: servicio mock en `compose.yaml` (más infraestructura sin necesitarla: las pruebas de fallo no requieren Kafka real; la parte con Kafka real se ejecuta contra USGS de verdad).

## 8. Pruebas de reinicio, corte y reenvío

- **Reinicio sin republicar y segundo ciclo ≈ 0** (SC-002, SC-003): prueba de integración con PostgreSQL real (base temporal, rol `observatory_producer`), mock de USGS y publicador falso que cuenta mensajes. "Reinicio" = construir de nuevo el ciclo contra la misma base.
- **Corte entre ack y marca** (SC-004): el publicador falso confirma y el marcado falla; en el ciclo siguiente se republica ese mensaje una vez. Los dos mensajes se pasan por la canalización del consumidor ya existente (`tests/support/db_helpers.py`, sin modificarla) y se comprueban los recuentos de `current_event` y `event_version`.
- **Con el sistema completo**: se hace con USGS real (bloque 5): `docker compose kill producer` y arranque, comprobando en el log del productor `published=0` en el primer ciclo.
- **Descartado**: gancho de fallo dentro del productor (como el del consumidor); la prueba de integración reproduce el corte sin código de producción añadido.

## 9. Eventos sintéticos y verificación A1

- El productor deja de generar sintéticos. `common/synthetic_event.py` se conserva (lo usan pruebas del consumidor y `tests/support`).
- `scripts/verify_stack.py` A1 pasa a comprobar datos reales: tras un ciclo, `live.current_event` tiene al menos una fila con `is_synthetic = false` y `source = 'usgs_feed'`. Se actualiza `tests/scripts/test_verify_stack_a1.py`. Afecta a la evidencia de `002` y `003`, que son históricas y no se reescriben; la regresión de esta feature queda en `docs/evidencias/productor-live/`.

## 10. Límites conocidos (una línea cada uno)

- No se respeta `Retry-After`.
- Un solo productor; dos a la vez no están soportados.
- Un evento sin `id` o sin `updated` se republica en cada ciclo.
- El ciclo tarda lo que tarde más `POLL_SECONDS` de espera (periodo real algo mayor de 60 s); basta para B1 ("cada ~60 s").
- Si USGS tarda más del timeout, el ciclo cuenta como fallo aunque el servicio funcione.
- Los eventos que USGS elimine del feed no se detectan (B11, texto en el borrador de memoria).
