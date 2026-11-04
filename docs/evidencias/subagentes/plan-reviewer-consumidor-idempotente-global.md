## Revisión global de diseño — 003-consumidor-idempotente

**Veredicto: Listo para tu revisión.** No hay bloqueantes. Los dos puntos "importantes" son decisiones o riesgos tuyos, no defectos de documento. El resto son menores.

No modifiqué ningún archivo. Lo que sigue lo contrasté yo mismo con los documentos, el DDL, `sql/002_roles.sql`, `compose.yaml`, `Dockerfile`, `common/` y `consumer/loop.py`. Aparte de lo que sale en la tabla, comprobé tres cosas:
- Los ms Unix de la FAQ 12 (…786400000/700/940/820, …787120000) corresponden a 2026-11-04 10:00/10:05/10:09/10:07/10:12 UTC.
- `MIN_EPOCH_MS` y `MAX_EPOCH_MS` corresponden a 1000-01-01 y 3000-01-01.
- El argumento de exactitud del `CHECK` (`125·ms < 2^53`) es correcto.

### 1. Hallazgos

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| Volumen y calendario: 93 tareas, 7 bloques, 7 escenarios Docker y una infraestructura de pruebas nueva (servicio `tests`, etapa `test` del Dockerfile, `schema_guard`, fuzz de ~2000 mutaciones). El roadmap asigna a F4+F3+F5(+F6) los días 4–7 nov, con entrega el 19 nov, y `productor-live` aún no existe. | Importante (riesgo) | `tasks.md` completo; `02-roadmap` "Calendario orientativo" | Constitución §12 (alcance) y roadmap |
| Hay decisiones provisionales de las que cuelgan decenas de tareas y que siguen sin confirmar. Si alguna cambia, se rehacen T021–T027, T041, T042 y los documentos de diseño. Las decisiones son estas: regla general FR-014 y regla de copia a cuarentena (spec "Pendientes" 1–2), rango 1000–2999 (plan §13.2), profundidad JSON 64 (§13.3), hook de crash por variable de entorno (§13.4), `original` re-serializado con pérdida de precisión (§13.7), servicio `tests` en perfil de Compose (§13.1), evidencias por bloque y no por tarea (tasks, decisión 6), y T093 numerada fuera de orden. | Importante (decisión del alumno) | `spec.md` "Preguntas"; `plan.md` §13; `tasks.md` "Escalados y decisiones" | Constitución §19; CLAUDE.md |
| Desviación respecto al procedimiento: no existe `common.processing.process_event()`. La parte pura vive en `common/` y la transacción en `consumer/writer.py`, junto con `pipeline`, `resilience` y `counters`. `historico-2025` y `replay` tendrán que importar de `consumer/`, o mover `writer.py` después. Es defendible, pero el procedimiento §7.1 y el roadmap F3/F6 prometen una función única compartida. | Menor (decisión ya marcada como provisional) | `plan.md` §2 y §13.9(b); `03-procedimiento` §7.1 | FR-030; constitución §14; B16/J5 |
| Firma incoherente de `validate_message`. Plan y research dicen `validate_message(decoded, topic_mode)` (un modo). T025 dice `(decoded, topic: str)` y T023 pasa `"earthquakes.live"` (un nombre de tema). El implementador debe elegir. | Menor | `plan.md` §1 paso 2 y §2; `research.md` §3; `tasks.md` T023, T025 | FR-004, FR-015 |
| No se verifica `auto_offset_reset="earliest"` ni el `group_id` propio. T055/T056 no comprueban los kwargs de `start_consumer`, y ningún escenario arranca un grupo nuevo con mensajes ya publicados. | Menor | `tasks.md` T055, T056; `plan.md` §10 (FR-028) | FR-028; edge "grupo nuevo" |
| Posible carrera al publicar. El consumidor es quien crea el tema (`ensure_topics`; `KAFKA_AUTO_CREATE_TOPICS_ENABLE=false`). T072/T073 publican tras `up -d` sin exigir esperar a "healthy" ni crear el tema (solo T080 espera "healthy"). | Menor | `tasks.md` T072–T079 | SC-001, SC-009 |
| T089 (auditoría de tamaño/docstrings) y T090 (secretos) corren después de T087, que es la "única ejecución completa" de pytest. Si la auditoría obliga a refactorizar, `pytest_unitarias.txt` y `pytest_integracion.txt` quedan obsoletos. | Menor | `tasks.md` T087–T090 | Constitución §16, §14 |
| Dependencias no listadas. T009 necesita T005/T007/T008. T013 necesita T001a. T057 fija `main.py` ≤ 60 líneas, pero T069 le añade la ruta del catálogo. | Menor | `tasks.md` "Dependencias", T057, T069 | — |
| Contadores bajo fallos: si el `COMMIT` de PostgreSQL falla de forma ambigua (cae la conexión) y se reintenta, el resultado sale `REDELIVERY` en vez de `NEW_EVENT`. La limitación documentada solo menciona el fallo del commit del offset. SC-009 se verifica sin fallos, así que no afecta a la prueba. | Menor | `spec.md` FR-023; `plan.md` §7 | C8 |
| Las claves de `COUNTERS` están fijadas en T074 y T079, pero `consumer-runtime.md` §4 dice "las claves exactas se fijan al implementar". | Menor | `consumer-runtime.md` §3–§4 frente a `tasks.md` T074, T079 | FR-023 |
| `plan.md` §11 y T092 no listan todas las evidencias que generan las tareas (`rango_tiempos_check.txt`, `regresion_002_base.txt`, `bloque*_*.out`, `tamanos_codigo.txt`, `busqueda_secretos.txt`). | Menor | `plan.md` §11; `tasks.md` T092 | FR-034; constitución §16 |
| `tests/scripts/test_verify_consumer_helpers.py` (T071) importa `scripts/`, que no se monta en el servicio `tests`. Cuando T044 o un uso posterior ejecute `pytest -m "not integration"` dentro del contenedor, fallará la recolección de esa prueba. | Menor | `tasks.md` T071 frente a T007 y T044 | FR-033 |
| La evidencia se escribe en un montaje de lectura y escritura con el usuario uid 10001. En Docker Desktop de Windows funciona. En un host Linux podría no ser escribible, y el helper lo omite en silencio hasta que T044 lo detecta. | Menor | `tasks.md` T007, T036 | — |
| `research.md` §3 reproduce las 14 condiciones del contrato y las extiende sin marcar cuáles son extensiones: `event.id` > 512 → `value_out_of_range`, el paso 13 y el rango de años. Las marcas sí están en spec FR-014/FR-011, research §5 y plan §13.8. Riesgo de deriva respecto de `kafka-message.md` §6. | Menor | `research.md` §3 | Constitución §15 |
| Los textos dicen que añadir un motivo propio de longitud exigiría "cambiar el contrato". Pero `kafka-message.md` §6 dice textualmente "lista inicial, **ampliable en las features `consumidor-idempotente`**…". FR-035 prohíbe modificarlo igualmente; es solo una pregunta para ti (ver abajo). | Menor | `spec.md` Preguntas 1(c); `kafka-message.md` §6 | FR-035; constitución §15 |
| T001 edita `plan.md`, `data-model.md`, `consumer-runtime.md` y `research.md`, que tú ya habrás revisado. Los cambios son de redacción (listados en T001a–d), pero conviene que lo sepas. | Menor | `tasks.md` T001, T091 | Constitución §19 |

### 2. Verificaciones que pasan

- **Cobertura.**
  - C1–C8 y C13 tienen spec, FR/SC y tareas.
  - Las pruebas 2, 3, 4, 6 y 8 tienen test de integración (T040, T039, T042, T059) y escenario Docker (T074, T075, T076).
  - El brief completo está cubierto.
  - La secuencia FAQ 12 suma 2 actuales, E1 con 4.6 y 3 versiones.
  - Las cifras de contadores (5/5/2/1/2; 7→5; 7→7) son coherentes entre spec, data-model, plan y tasks.
  - El alcance excluido (país, productor real, USGS, histórico, replay, API, frontend) no aparece en ninguna tarea.
- **Contratos.**
  - `git diff --stat` de `specs/001-contratos-y-modelo/contracts/` y de `docs/enunciado/` vacío (lo ejecutó el orquestador); no lo repetí.
  - T088 lo comprueba también para `sql/`.
  - Ningún documento redefine los contratos.
  - "Mismo `updated`, distinto contenido" cumple `kafka-message.md` §5.
  - Marcados como decisión dentro de lo permitido: clase 22+23 → `db_constraint_violation`, saneado, tope 512, rango 1000–2999, tombstone → `invalid_json`, `ingested_at` → `invalid_envelope`, y `db_constraint_violation` previo a la base.
- **GRANTs reales (`sql/002_roles.sql`).**
  - `current_event`: S/I/U.
  - `event_version`: S/I.
  - `quarantine`: solo I, más USAGE de la secuencia.
  - `date_dim`: S/I.
  - `country`: S/I/U.
  - Son coherentes con el SQL del plan: `FOR UPDATE`, `ON CONFLICT` sin destino en cuarentena, `UPSERT` de país y `test_roles` (a)–(e).
- **Constitución.**
  - §1, §2, §3, §5, §6, §7, §8, §13, §14, §16, §18, §19, §20 y §21 se cumplen.
  - §4 queda fuera: `country_id` es `NULL`, se carga solo el catálogo.
  - §9 y §10: el servicio `tests` usa nombres de servicio y no publica puertos.
  - §11: cero dependencias nuevas.
  - §12: nada de lo prohibido. El perfil `test`, el hook y `verify_consumer.py` son infraestructura de apoyo, no están en la lista de prohibidos.
  - §15: `config.md` de 002 es el contrato de 002, no de 001.
  - §6 admite el límite `54*` aceptado por ti (errores de entorno, no datos inválidos).
- **CLAUDE.md.** Se cumple salvo la desviación ya declarada de aplicar tests/evidencia/CODEMAP por bloque en vez de por tarea (decisión 6 de tasks).
- **tasks.md ejecutable en orden.**
  - Hay 93 tareas T001–T093, ninguna marcada `[x]`.
  - Las pruebas van antes de la implementación.
  - Escalados claros y sin ambigüedad: T037(b) (no se concede SELECT), T093/T041 (no se reduce el rango ni se toca el DDL) y T088.
  - Las esperas de `unhealthy` (90–105 s) y el máximo de 2 líneas `retry` por minuto concuerdan con `compose.yaml` y con `RETRY_MAX_SECONDS`.
  - El texto tampoco contiene "TBD" ni "a decidir".

### 3. Decisiones que el alumno debe tomar

1. ¿Confirmas, o recortas, el volumen de 93 tareas dado el calendario? Candidatos si quieres recortar sin perder C1–C8/C13: fuzz de 2000 mutaciones, escenario `kafka-down` (aunque US2.5 lo pide), auditoría T089, `scripts/consumer_scenarios/`.
2. ¿Confirmas las decisiones provisionales, una por una?
   - Regla general de no fallo por contenido.
   - Regla de copia a cuarentena.
   - Rango 1000–2999.
   - Profundidad JSON 64.
   - `original` re-serializado con `float` (frente a `Decimal`).
   - Hook de crash por variable de entorno.
   - Servicio `tests` en perfil de Compose.
   - Evidencias por bloque.
   - Numeración T093.
   - Sin `process_event()`.
3. Para longitud de `event.id` y rango de años, ¿usas `value_out_of_range` (decisión actual) o amplías la lista de motivos, dado que `kafka-message.md` §6 la declara "ampliable en esta feature"? Eso sí tocaría el contrato y requeriría tu aprobación explícita.
4. Preguntas 3 y 4 de la spec (contadores solo en memoria; solo `earthquakes.live`), todavía abiertas: ¿mantener la recomendación?
5. Antes de implementar, actualiza tu `.env` local (`KAFKA_GROUP_ID=consumer-live`, `CONSUMER_FAULT_CRASH_AT_OFFSET=`) y asume que `verify_consumer.py` ejecuta `down -v` (borra volúmenes locales; exige `--yes`).

### 4. Riesgos a conocer antes de implementar

- T037(b), la sentencia `ON CONFLICT DO NOTHING` sin destino con el rol real, es la primera comprobación crítica. Si falla, se detiene y se escala.
- T093 también es un punto de parada: si el `CHECK` rechaza los extremos del rango, se rehacen T021–T025 y varios documentos.
- Un error persistente de otra clase (p. ej. `54*`) bloquea la partición por diseño. Es un límite que ya aceptaste.
- La cuarentena deduplica por bytes: una segunda copia idéntica conserva solo la referencia (topic/partición/offset) de la primera.
- Los contadores viven en memoria y solo concilian con SQL en una sesión limpia y sin fallos inyectados.
- `command_timeout=5 s` del pool (`common/db.py`) aplica también a `COMMIT`. Un timeout se trataría como transitorio y se reintentaría. Con mensajes de Kafka ≤ 1 MB es poco probable.
- El hook de crash viaja en la imagen de producción. Está desactivado por defecto y limitado a `is_synthetic=true`.
- La verificación de `asyncpg.exceptions.DataError` (cliente frente a servidor) se apoya en T032/T042 con excepciones reales. No pude confirmarla en `.venv` porque `Grep` no devolvió resultados sobre esa carpeta; tómalo como pendiente de T032.
