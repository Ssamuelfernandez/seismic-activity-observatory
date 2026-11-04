REVISIÓN DEL PLAN: consumidor-idempotente (specs/003-consumidor-idempotente/). No existe tasks.md y no se reclama. Los contratos de 001 y docs/enunciado no están modificados (diff vacío, según el orquestador). No se encontraron bloqueantes.

## 1. Hallazgos

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| Regresión no planificada de 002. `scripts/verify_stack.py::check_synthetic_event_in_consumer_log` (líneas 90-99) busca en el log del consumidor las cadenas `[SINTÉTICO]` y `synthetic-`. El plan retira `describe_message` y sus líneas de log, y las nuevas líneas `decision=… event_id=…` (consumer-runtime §4) no llevan `[SINTÉTICO]`. El check A1 de 002 pasaría a FAIL. El §12 del plan no lista `scripts/verify_stack.py` ni una tarea de regresión de 002. | Importante | plan.md §12 y structure; contracts/consumer-runtime.md §4 | A1 (002); §16 |
| `ON CONFLICT (original_sha256, reason) DO NOTHING` sobre `quarantine` puede exigir SELECT. En PostgreSQL las columnas del `conflict_target` se marcan con privilegio SELECT, y el rol solo tiene INSERT (`sql/002_roles.sql` línea 63). Si es así, el primer mensaje inválido daría `42501`. Esa clase se reintenta sin límite y bloquearía la partición. Research §8 lo deja como "verificar… si no, escalar". Hay una alternativa sin coste que debería fijarse ya: `ON CONFLICT DO NOTHING` sin destino, o `ON CONFLICT ON CONSTRAINT quarantine_original_reason_key DO NOTHING`. Ambas cubren la única restricción única y no necesitan SELECT. | Importante | research.md §8; plan.md §9 (fila "Cuarentena sin SELECT"); spec Notas para el plan | C5, FR-012, FR-027; §6 |
| US2.5 (Kafka no disponible: reintento, retoma el consumo, sin perder ni duplicar) no tiene prueba prevista. Los escenarios de `verify_consumer.py` (plan §8 y quickstart §6) son faq12, quarantine, restart, pg-down, counters y catalog. No hay `kafka-down`. Solo se cubre el reintento del commit de offset en unitarias con dobles. Hay que añadir un escenario o citar explícitamente la evidencia de 002 y justificar por qué basta. | Importante | plan.md §8 y §10; quickstart.md §6 | C2, US2.5, FR-029 |
| FR-034 y C1 ("reglas listadas en memoria") no tienen entregable fuera de specs/. `docs/memoria.md` §4 "Calidad" está vacío. La tabla del Constitution Check dice que la memoria "resume las reglas", pero ni §11 (evidencias) ni §12 (archivos que se tocan) incluyen `docs/memoria.md`. Constitución §18 impide copiar specs/ a docs/. | Importante | plan.md §11, §12 y Constitution Check §18 | C1, FR-034, §16 |
| El `Dockerfile` actual tiene una sola etapa. Añadir una etapa `test` después de la de producción la convierte en la última, es decir, en el target por defecto. Entonces `docker compose build` del `producer` (que construye la imagen compartida) generaría la imagen con dependencias de desarrollo. El plan dice "sin cambiar la etapa de producción" pero no menciona nombrar las etapas ni fijar `target:` en compose. Además, el servicio `tests` no debe heredar el ancla `x-python-service`, que fija `image: seismic-observatory-python:0.1.0`, `pull_policy: never` y `restart`. | Menor (silencioso si se olvida) | plan.md §12 | A3, A11 |
| `original` re-serializado con `json.dumps` del objeto Python (research §13). §13.7 solo menciona el formato (`1E5` pasa a `100000.0`). Un `float` pierde precisión por encima de ~17 dígitos y un `1e-400` pasa a `0.0` sin aviso. FR-020 y kafka-message §3 dicen "íntegro y sin modificar". Es práctico para USGS, pero el plan declara "Escalados: ninguno". Conviene que §13.7 lo diga con esta amplitud, o usar `parse_float=Decimal`. | Menor | plan.md §13.7; research.md §13 | FR-020, §3 |
| Falta decidir cómo trata `decode_value` el BOM y los UTF-16. `json.loads(bytes)` autodetecta UTF-16 y acepta el BOM; el plan dice "UTF-8 estricto" y prueba el BOM, pero no fija el resultado esperado (se sugiere `invalid_json`, decodificando primero con `utf-8` estricto). | Menor | plan.md §2; research.md §3 y §5 | FR-014 |
| Ambigüedad de módulo: ¿quién hace el commit de offset (paso 7) y quién llama a counters (paso 8)? §1 y la estructura dicen que `pipeline.process_record` termina en el hook y devuelve `ProcessingResult`. En §8 el test de pipeline comprueba el orden "write → hook → commit offset → counters" con un consumidor doble. | Menor | plan.md §1, §2 y §8 | FR-001, FR-002 |
| La documentación de las variables nuevas aparece dos veces: `contracts/consumer-runtime.md` §1 y `config.md` (002). Es duplicación documental en espíritu de §15. Mejor que consumer-runtime §1 remita a `config.md`. | Menor | consumer-runtime.md §1; plan.md §12 | §15 |
| Detalles para `tasks.md`: (a) `verify_consumer.py` publica "con el servicio tests", pero `scripts/` no se monta en `tests` y la imagen no lo incluye, así que hay que decidir dónde vive el publicador (¿`tests/`?). (b) SC-008 pide "0 filas reales con la marca" y los fixtures son todos sintéticos, así que falta un caso con `is_synthetic=false`. (c) FR-035 (no tocar `kafka-message.md`, `db-schema.md`, `api.md`) no tiene comprobación explícita; bastaría un `git diff --stat` en el cierre. | Menor | plan.md §8, §10 | SC-008, FR-035 |
| Docs desalineados. `checklists/requirements.md` habla de "Preguntas 2 y 3 abiertas", pero en la spec ahora son la 3 y la 4. El quickstart usa `grep` (§2), que no existe en PowerShell (el equipo es Windows). Roadmap F3/F6 nombra `common.processing.process_event()` como lógica reutilizable por el histórico, y el plan no lo menciona: la escritura vive en `consumer/writer.py`, que `historico-2025` tendría que importar. | Menor | checklists/requirements.md; quickstart.md §2; plan.md §2 | FR-030 |
| Hook de crash (`os._exit(137)`) en el servicio de producción, desactivado por defecto. El riesgo es bajo. Si alguien lo activa por error, mata el proceso como mucho una vez por contenedor. El marcador de `/tmp` se pierde al recrear el contenedor (`up` tras cambiar la config), y entonces podría morir otra vez en ese offset. Una salvaguarda barata: que solo dispare con mensajes `is_synthetic=true`. Además, la variable queda visible en `.env.example`. | Menor | plan.md §4; consumer-runtime.md §2 | §7, §10 |
| `23505` o `23503` por una carrera con una instancia zombi se enviaría a cuarentena como `db_constraint_violation`. Es muy improbable con 1 consumidor y 1 partición, y el `FOR UPDATE` lo mitiga. Se anota solo como límite. | Menor | plan.md §4 y §6 | FR-014 |

## 2. Valoraciones pedidas

**(5) Tocar archivos de specs/002 e infraestructura.**
- Es legítimo y no requiere escalar. El "no los cambies sin avisar" de CLAUDE.md y la §15 se refieren a los tres contratos de 001 (mensaje Kafka, esquema de BD, API).
- `config.md`, `compose.yaml`, `Dockerfile`, `.env.example` y `check_env_example.py` son la infraestructura viva. El propio `check_env_example.py` exige mantener `config.md` sincronizado.
- El plan ya los avisa en §12 y §13.1.
- Sí hace falta incluirlos como tareas explícitas de ese cambio, con regresión de 002: `verify_stack.py`, `check_env_example.py` y los tests existentes. `config.md` también necesita la fila de `KAFKA_GROUP_ID` y el total "15 variables".
- El perfil `test` mantiene los 5 servicios con `up`; no publica puertos (§10).

**(6) Viabilidad técnica.**
- Mapa asyncpg: verificado en `.venv`. `asyncpg.exceptions.DataError` es la clase 22 del servidor, y `CharacterNotInRepertoireError` y `UntranslatableCharacterError` heredan de ella. `IntegrityConstraintViolationError` también existe. El mapa por `isinstance` y por prefijo de `sqlstate` es correcto.
- Falla con `InterfaceError` en reintento infinito. Si es un error de programación y no de conexión, se reintenta sin fin en lugar de terminar. Es consecuencia aceptada.
- Orden de la transacción: coherente con `db-schema.md` §5 y §8(b). La FK diferida permite insertar la versión antes del estado actual. El `SELECT … FOR UPDATE` es posible porque el rol tiene UPDATE sobre `current_event`. `IS DISTINCT FROM $::jsonb` implementa bien la decisión "mismo updated, distinto contenido". La etiqueta `INSERT 0 0/1` de `conn.execute` sirve para distinguir reenvío de versión nueva.
- Rol propio `observatory_consumer`: ya está en compose; coherente.
- Rango 1000-2999: constantes recalculadas por mí.
  - `MIN_EPOCH_MS=-30610224000000` es 1000-01-01 y `MAX_EPOCH_MS=32503680000000` es 3000-01-01. Ambas son correctas.
  - La razón del CHECK es válida. `1000·ms` es exacto en `double` si `125·ms < 2^53` (ms < 7,2e13).
  - Cabe en `date_dim.year smallint`. Es un subconjunto del `timestamptz`.
- Aislamiento y arranque: `tests` en perfil, `max_poll_interval_ms` (existe en aiokafka 0.15) y `getmany(max_records=1)` son viables.
- El `unhealthy` de 90-105 s por el latido que no se renueva es coherente con `config.md` §E.

**(7) FAQ 12.**
- Todos los ms están bien calculados. 2026-11-04T00:00Z es 1793750400 s.
  - 10:00 → 1793786400000.
  - 10:05 → 1793786700000.
  - 10:07 → 1793786820000.
  - 10:09 → 1793786940000.
  - 10:11 → 1793787060000.
  - 10:12 → 1793787120000.
- Contadores caso 1: 5 recibidos, 2 nuevos, 1 más reciente, 0 antiguas, 2 reenvíos, 0 conflictos y 5 conversiones. Las dos identidades dan 5 = 5.
- Caso 2 (7/5): 7 − (1+1) = 5; 2+1+0+2+0+0 = 5.
- Caso 3 (7/7): 7 − 0 = 7; 2+1+0+2+0+(1+1) = 7.
- Todo consistente entre spec, data-model, plan §7 y quickstart.

**(3)(4)(8) Constitución, alcance y valores concretos.**
- Constitución §1-§21 revisada punto por punto: sin violaciones. Los matices son los hallazgos de arriba (§7 y §10 en el hook, §15 en la variable duplicada, §16 en memoria).
- Alcance: no hay país, productor real, USGS, histórico, replay, API ni frontend. El código solo se describe, no se escribe (§19). `replay` solo aparece en paridad de esquema y `topic_mode`.
- Valores concretos y presentes:
  - reintentos: 1, 2, 4, 8, 16 y 30 s, sin límite;
  - registro: una línea WARNING por intento, ≤200 caracteres, ≤2 por minuto en régimen;
  - contadores: cada 60 s;
  - tope de `event.id`: 512;
  - profundidad JSON: 64;
  - saneado exacto en research §4.
- Trazabilidad: FR-001..036, SC-001..012, US1-6, C1-C8, C13 y pruebas 2, 3, 4, 6, 8 están en la tabla del plan §10. Las lagunas son las de los hallazgos.

## 3. Decisiones que el alumno debe tomar
1. ¿Confirma que editar `compose.yaml`, `Dockerfile`, `.env.example`, `check_env_example.py` y `specs/002-infra-compose/contracts/config.md` (más la regresión de `verify_stack.py`) es aceptable dentro de esta feature?
2. ¿Acepta un sexto servicio `tests` bajo perfil Compose, dado que A1 habla de "5 servicios" (con `up` siguen siendo 5)?
3. ¿Acepta el hook `CONSUMER_FAULT_CRASH_AT_OFFSET` en la imagen de producción, con la salvaguarda opcional de que solo dispare con mensajes sintéticos?
4. ¿Acepta que el `original` de `event_version` pierda precisión de `float` y la forma numérica (§13.7), o prefiere `parse_float=Decimal`?
5. Si el test de roles demostrara que hace falta SELECT en `quarantine`, la respuesta es no conceder permisos y usar la forma sin destino (`ON CONFLICT DO NOTHING`). Se pide confirmarlo.

**Veredicto: Corregir antes de revisar.** No hay bloqueantes. Hay 4 importantes, todos de edición pequeña en el plan: regresión de `verify_stack.py`, forma del `ON CONFLICT`, escenario `kafka-down` y `docs/memoria.md`.
