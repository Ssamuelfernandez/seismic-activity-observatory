# Quickstart: verificar el productor en vivo

Guía de comprobación (sin código). Contratos: [`kafka-message.md`](../001-contratos-y-modelo/contracts/kafka-message.md), [`db-schema.md`](../001-contratos-y-modelo/contracts/db-schema.md). Variables: [data-model.md](data-model.md) §5. Todos los comandos se ejecutan desde la raíz del repositorio; los de SQL, con el administrador del contenedor `postgres`.

## 0. Preparación

1. `.env` copiado de `.env.example` (con las variables nuevas).
2. Si el volumen de PostgreSQL ya existía, reaplicar el permiso nuevo (`postgres_init.sh` solo corre con volumen nuevo):
   `docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "GRANT SELECT, DELETE ON ingest.raw_response TO observatory_producer"`.
   O bien `docker compose down -v` (borra los datos). `db-schema.md` no se edita: este `GRANT` está en `sql/002_roles.sql` (no es contrato).
   Nota: `CODEMAP.md` se actualiza una sola vez en T021. Límites conocidos: el timeout de `urllib` es por operación de socket, y los eventos sin `id`/`updated` se republican en cada ciclo.
3. `docker compose build producer` y `docker compose up -d`.

## 1. Pruebas automáticas

| Qué | Comando | Resultado esperado |
|---|---|---|
| Unitarias (sin red ni servicios) | `uv run pytest -m "not integration" -q` | pasan; incluyen funciones puras, cliente contra el mock, ciclo con dobles y bucle |
| Integración (PostgreSQL real, mock USGS) | `docker compose up -d postgres`, `docker compose --profile test build tests`, `docker compose --profile test run --rm tests pytest -m integration -q` | pasan: fallos 500/429/timeout/JSON, segundo ciclo, reinicio, corte entre ack y marca, permisos, purga |
| Variables | `python scripts/check_env_example.py` | termina con código 0 |

## 2. Ejecución real contra USGS (prueba 1 hasta PostgreSQL y prueba 2)

1. Tras `docker compose up -d`, esperar dos ciclos y ver el log: `docker compose logs producer` muestra líneas `cycle=… published=… skipped=…`. El primero publica los terremotos de la ventana de 24 h; el segundo, 0 o unos pocos.
2. SC-001: el número de filas reales coincide con los `earthquake` de la última respuesta:
   `SELECT count(*) FROM live.current_event WHERE is_synthetic = false;` frente a
   `SELECT count(*) FROM ingest.raw_response r, jsonb_array_elements(r.body->'features') f WHERE r.id = (SELECT max(id) FROM ingest.raw_response) AND f->'properties'->>'type' = 'earthquake';`
   (puede diferir en eventos publicados en medio; la diferencia se explica en la evidencia).
3. Reinicio sin republicar: `docker compose kill producer` y `docker compose up -d producer`; el primer ciclo debe mostrar `published=0` (salvo eventos nuevos de USGS en ese minuto).
4. Evento nuevo (prueba 1): anotar el recuento, esperar a que `published` sea > 0 en un ciclo posterior y comprobar la fila nueva con su `event_id` en `live.current_event`.
5. Reenvío (prueba 2): `SELECT (SELECT count(*) FROM live.current_event), (SELECT count(*) FROM live.event_version);` antes y después del reenvío forzado por la prueba de integración del corte entre ack y marca; los recuentos no cambian.
6. Trazabilidad: `SELECT status, latency_ms, event_count, left(sha256,8), error FROM ingest.ingest_run ORDER BY id DESC LIMIT 5;` y `SELECT count(*) FROM ingest.raw_response;` (menos filas que consultas si el contenido repetía).
7. Regresión: `python scripts/verify_stack.py` (A1 ya comprueba filas reales) y `docker compose ps` con los cinco servicios `healthy`.

## 3. Evidencias

Todo lo anterior se guarda en `docs/evidencias/productor-live/` (salidas de pytest, logs del productor, SQL antes y después, estado de `docker compose ps`). Los datos del mock son sintéticos y las evidencias lo indican.
