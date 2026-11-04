# Contrato de ejecución del consumidor (variables, contadores y registro)

Documenta lo que **ningún contrato de `001` ni de `002` cubre** y que otras personas leerán o ejecutarán: las variables de entorno nuevas, los contadores de C8, el formato de las líneas de registro y el hook de prueba. **No** redefine el mensaje Kafka (`specs/001-contratos-y-modelo/contracts/kafka-message.md`), el esquema (`db-schema.md`) ni la configuración ya existente (`specs/002-infra-compose/contracts/config.md`).

## 1. Variables de entorno nuevas o cambiadas

La definición de cada variable (dónde se define, valor, lectura y descripción) vive en `specs/002-infra-compose/contracts/config.md`, que se actualiza al implementar (constitución §15). Aquí solo se listan los cambios, sin duplicar sus columnas:

- `KAFKA_GROUP_ID`: pasa de `consumer-minimal` a `consumer-live` (FR-028).
- `COUNTRY_CATALOG_PATH`: nueva, constante de diseño de `compose.yaml` (`/app/data/catalogo/paises.geojson`, montaje de solo lectura).
- `CONSUMER_FAULT_CRASH_AT_OFFSET`: nueva, opcional y vacía por defecto (lectura con la nueva `read_optional_int`); solo para la prueba 8.

Sin variables nuevas para los reintentos: se reutilizan `RETRY_INITIAL_SECONDS` (1) y `RETRY_MAX_SECONDS` (30) de `002`. Constantes con nombre en el código (no configurables): `COUNTERS_LOG_INTERVAL_SECONDS = 60`, `MAX_POLL_INTERVAL_MS = 86_400_000`, `MAX_EVENT_ID_CHARS = 512`, `MAX_JSON_DEPTH = 64`, `MIN_EPOCH_MS = -30610224000000`, `MAX_EPOCH_MS = 32503680000000`, `ERROR_TEXT_MAX_CHARS = 200`.

Al implementar hay que mantener coherentes `.env.example`, `compose.yaml`, `config.md` y `scripts/check_env_example.py` (constitución §10).

## 2. Hook de prueba (prueba 8)

- Punto de invocación: **después** del commit de PostgreSQL y **antes** del commit del offset (plan §4).
- Activación en producción: solo con `CONSUMER_FAULT_CRASH_AT_OFFSET` no vacía **y solo si el mensaje de ese offset es `is_synthetic=true`** (salvaguarda: con un mensaje real no hace nada aunque coincida el offset). Efecto: al terminar de guardar el mensaje de ese offset, escribe el marcador `/tmp/consumer_fault_done`, registra `FAULT crash_after_db_commit offset=N` y termina con `os._exit(137)`. Si el marcador ya existe, no hace nada (el reinicio no vuelve a morir).
- Activación en pytest: parámetro `after_db_commit` de `process_record` con un doble que lanza `SimulatedCrash(BaseException)`.
- Con la variable vacía no existe ningún camino de código activo distinto del normal.

## 3. Contadores (C8, FR-023)

Solo en memoria, una sesión; se incrementan una vez por mensaje, **tras el commit del offset**. Los reintentos no los tocan.

| Contador | Se incrementa cuando… |
|---|---|
| `received` | termina de procesarse un mensaje (cualquier resultado, incluidos cuarentena y duplicados de cuarentena). |
| `new_events` | resultado `NEW_EVENT`. |
| `newer_versions_applied` | resultado `NEWER_VERSION`. |
| `late_old_versions` | resultado `LATE_OLD_VERSION`. |
| `redeliveries_ignored` | resultado `REDELIVERY`. |
| `same_updated_conflicts` | resultado `SAME_UPDATED_CONFLICT`. |
| `ms_to_utc_conversions` | el mensaje superó la validación y se transformó (incluye reenvíos, conflictos y `db_constraint_violation`; excluye el resto de cuarentenas). |
| `nulls_kept` (mapa por campo: `mag`, `depth_km`, `place`, `status`, `url`, `sig`, `mag_type`) | el mensaje transformado trae ese campo nulo y se guarda `NULL`. |
| `quarantined` (mapa por motivo) | la fila de cuarentena es **nueva** (`INSERT 0 1`). |
| `quarantine_duplicates` (mapa por motivo) | la sentencia no insertó (`INSERT 0 0`). No suma a `quarantined`. |

Las tres identidades que los relacionan con SQL están en [data-model.md](../data-model.md) §4.

## 4. Líneas de registro

Formato general: el de `common/logging_setup.py` (`%(asctime)s %(levelname)s [%(name)s] %(message)s`). El mensaje usa pares `clave=valor` para poder filtrarlo con cualquier herramienta de texto. Estas líneas sustituyen a las de `describe_message` de `002`; `scripts/verify_stack.py` (check A1) se actualiza para reconocerlas (plan §12).

| Evento | Nivel | Mensaje (campos) |
|---|---|---|
| Decisión por mensaje | INFO | `decision=<new_event\|newer_version\|late_old_version\|redelivery_ignored\|quarantined\|quarantine_duplicate> event_id=<id\|-> topic=… partition=… offset=…` (con `reason=<motivo>` si es cuarentena) |
| Conflicto «mismo `updated`, contenido distinto» | WARNING | `decision=same_updated_conflict event_id=… updated_ms=… topic=… partition=… offset=…` |
| Reintento de base o de commit | WARNING | `retry attempt=N wait_s=… op=<write_event\|write_quarantine\|commit_offset> event_id=… topic=… partition=… offset=… error=<Clase> sqlstate=<xxxxx\|-> detail="<≤200 caracteres>"` — sin traceback |
| Defecto de validación previa | ERROR | `validation_gap event_id=… sqlstate=… …` (un error de clase 22/23 llegó a la base) |
| Estado inconsistente | WARNING | `inconsistent_state event_id=…` |
| Commit del offset omitido | WARNING | `commit_skipped event_id=… topic=… partition=… offset=… error=CommitFailedError` — el grupo perdió la partición; el mensaje se reentregará y se ignorará como reenvío (lo emite `consumer/resilience.py`) |
| Broker no alcanzable | WARNING | `broker_unreachable bootstrap=<host:puerto> error=<Clase>` — una línea por sondeo fallido, sin traceback; la emite `broker_reachable` (`consumer/loop.py`). El escenario `kafka-down` la comprueba (FR-029, US2.5) |
| Catálogo | INFO | `catalog loaded total=177 inserted=… updated=…` |
| Contadores | INFO | `COUNTERS {…json con claves ordenadas…}` cada 60 s y al detenerse |
| Hook de prueba | WARNING | `FAULT crash_after_db_commit offset=N` |

**Cuándo se escribe la línea de decisión.** Justo después del commit de PostgreSQL y **antes** del commit del offset (plan §1, paso 7), de modo que FR-003 se cumple siempre, incluso si el commit del offset se salta; los contadores, en cambio, cambian después del commit del offset. Consecuencia aceptada: una **reentrega duplica la línea de decisión** del mismo `topic/partition/offset` (p. ej. `new_event` y luego `redelivery_ignored`); quien lea el registro debe contar mensajes con los contadores, no con las líneas. El `updated_ms` de la línea `same_updated_conflict` sale de `ProcessingResult.updated_ms` ([data-model.md](../data-model.md) §1). Las emite `consumer/reporting.py` (decisión y `COUNTERS`); `broker_unreachable`, `loop.py`; `retry`, `resilience.py`.

Ejemplo de la línea de contadores tras la FAQ 12 (campos agrupados; las claves exactas se fijan al implementar y los tests las leen del objeto, no de la cadena):

```text
COUNTERS {"late_old_versions":0,"ms_to_utc_conversions":5,"new_events":2,"newer_versions_applied":1,"nulls_kept":{},"quarantine_duplicates":{},"quarantined":{},"received":5,"redeliveries_ignored":2,"same_updated_conflicts":0}
```
