REVISIÓN DEL PLAN, vuelta 2: consumidor-idempotente (specs/003-consumidor-idempotente/). No reclamo tasks.md, que aún no existe. Los contratos de 001 y docs/enunciado no cambian (diff vacío, según el orquestador). No he podido ejecutar nada: no tengo Bash. Lo de PostgreSQL lo razono desde el comportamiento conocido del servidor y está marcado donde no es seguro.

## 1. Los 4 importantes y los 9 menores de la vuelta 1

Los 4 importantes están resueltos en los documentos.

- **verify_stack.py / A1.** Resuelto. El plan §12 elige actualizar `check_synthetic_event_in_consumer_log` (líneas 90-99) para reconocer `decision=… event_id=synthetic-…`. Incluye la tarea de regresión y `regresion_002.txt` (§11). El evento sintético de `common/synthetic_event.py` (id `synthetic-<ts>`, `time` y `updated` en ms, geometría Point, `mag` 1.0) pasa la validación y daría `decision=new_event`.
- **ON CONFLICT sin destino.** Resuelto, con una matización (hallazgo 3). La forma `ON CONFLICT DO NOTHING` sin destino es válida con solo `INSERT` (`sql/002_roles.sql` línea 63). Sin cláusula de inferencia, PostgreSQL no marca columnas con privilegio SELECT. Sí lo hace con `(original_sha256, reason)`, y por eso daría 42501. La tabla tiene una única restricción única, `quarantine_original_reason_key` (`sql/001_schema.sql` líneas 158 y 266), y la PK es una identidad. La forma sin destino cubre el mismo caso. `test_roles.py` (b) la prueba con el rol real. Nada exige SELECT en las demás sentencias: `event_version`, `current_event`, `date_dim` y `country` tienen SELECT, INSERT y UPDATE donde hace falta, y `FOR UPDATE` necesita UPDATE sobre `current_event`.
- **kafka-down.** Resuelto. Está en plan §8, en quickstart §6, en la trazabilidad (C2/FR-029) y en las evidencias (`kafka_caida.log`).
- **docs/memoria.md.** Resuelto. Existe el encabezado `## 4. Calidad`, hoy vacío. El plan lo recoge en §11, §12, la fila C1 de §10 y el Constitution Check §18.

Los menores también están atendidos:

- BOM y UTF-16 dan `invalid_json` (plan §2, research §3).
- Quién hace el commit del offset y quién actualiza contadores queda fijado (plan §1).
- `consumer-runtime` §1 remite a `config.md`.
- El publicador vive en `tests/support/`, hay un caso `is_synthetic=false` y FR-035 se comprueba con `git diff --stat`.
- El quickstart ya trae el comando de PowerShell.
- `checklists/requirements.md` ya dice «3 y 4».
- El roadmap `process_event()` tiene su párrafo.
- §13.7 explica la pérdida de precisión del `float`.
- El hook solo actúa con `is_synthetic=true`.

## 2. Hallazgos nuevos o que siguen abiertos

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| **Imagen obsoleta, sin avisar.** Solo `producer` tiene `build:`. `consumer` y `api` reutilizan la imagen por nombre (`pull_policy: never`). El quickstart §2 y los escenarios de `verify_consumer.py` hacen `docker compose up --build -d kafka postgres consumer`. Con `--build` solo se reconstruyen los servicios nombrados o sus `depends_on` que tengan `build`, y `consumer` no depende de `producer`. Tras `down -v` (que no borra imágenes) el consumidor arrancaría con la imagen vieja, es decir, el consumidor mínimo de 002, o fallaría en una máquina sin imagen. Pasa lo mismo con `docker compose --profile test run --rm tests` (quickstart §4): sin `--build`, el `common/` y el `consumer/` copiados en la etapa `test` pueden estar desfasados. Las evidencias de SC-009 y SC-011 podrían salir de código antiguo. | Importante | plan.md §8 y §12; quickstart.md §2, §4, §5, §6 | SC-009, SC-011, C1–C8 (fiabilidad de la evidencia), §16 |
| §12 dice que `producer`, `consumer` y `api` fijan `build: target: production`. Solo `producer` tiene `build`, y el comentario de `compose.yaml` (líneas 7-9) advierte de que construir la misma etiqueta tres veces provoca un conflicto. Leído literalmente, la tarea reintroduce ese conflicto. Debe decir «solo `producer`». | Menor | plan.md §12 | A3 (002) |
| La alternativa «equivalente» `ON CONFLICT ON CONSTRAINT quarantine_original_reason_key` no lo es, con bastante probabilidad. A mi entender, el analizador de PostgreSQL (≥ 12, incluido el 16) también marca como SELECT las columnas de la restricción nombrada. Si es así, daría 42501 y un reintento sin fin. Solo la forma sin destino es segura. Conviene quitar la alternativa o añadirla a `test_roles` (c), que hoy solo prueba el destino con columnas. No pongo importante porque la forma elegida es la correcta. | Menor | plan.md §9 (fila «Cuarentena sin SELECT»); research.md §8; spec.md «Notas para el plan» | FR-012, FR-027, C5 |
| Faltan detalles de infraestructura para `tasks.md`. (a) `FROM production AS test` hereda `USER observatory`, y `uv sync` sobre `/opt/venv` necesita root: hace falta `USER root` y volver a `observatory`. (b) El servicio `tests` no hereda el ancla, así que debe declarar `networks: [backend]`. (c) `CONSUMER_FAULT_CRASH_AT_OFFSET` debe interpolarse como `${…:-}`: con `:?` una variable vacía rompe `compose`. `check_env_example.py` exige que quede en `.env.example` y en `compose.yaml`. (d) Los montajes en solo lectura impiden escribir `.pytest_cache`. | Menor | plan.md §12 | A3, A10, §10 |
| La tabla de funciones de §2 queda cortada por el párrafo «Relación con el roadmap». Las filas `catalog`, `db_errors` y `counters` se renderizan como texto suelto. | Menor | plan.md §2 | Legibilidad |
| Referencias cruzadas erróneas. El Constitution Check (filas 13 y 14) remite a «§3» y los módulos están en §2. Una nota de §8 dice «(§2 estructura)» y esa estructura está en «Project Structure». El paso 4 de §1 remite a §6 para el reintento y está en §5. | Menor | plan.md Constitution Check, §1, §8 | Trazabilidad |
| El escenario `kafka-down` exige que el consumidor «registre el fallo del broker». `broker_reachable` actual devuelve `False` sin loguear, y `consumer-runtime` §4 no define ninguna línea para ello. | Menor | plan.md §8; contracts/consumer-runtime.md §4 | FR-029, US2.5 |
| La línea de decisión se escribe después del commit del offset. Si ese commit se salta por `CommitFailedError`, la base queda escrita sin línea de decisión ni contador. La señal SIGTERM no debería interrumpir el hueco entre el commit y `apply_result`. Conviene dejarlo escrito (race con `lag = 0` en `counters`). | Menor | plan.md §1 (pasos 7-8) y §5 | FR-003, FR-023 |
| Tras `down`/`up`, el check A1 de `verify_stack.py` ya no relee desde el principio. El grupo conserva el offset, así que depende de un evento nuevo. `PRODUCER_INTERVAL_SECONDS` admite hasta 60 y `EVENT_TIMEOUT_SECONDS` es 60. Además, `README.md` línea 80 cita `[SINTÉTICO]`: conviene nombrarlo en la tarea de README. | Menor | plan.md §12; scripts/verify_stack.py línea 22 | A1, §16 |
| El resumen de `docs/memoria.md` §4 lista validación, nulos, cuarentena e idempotencia. FR-034 también pide transacción, orden de commits y secuencia de la FAQ 12, y no dicen dónde van. | Menor | plan.md §11 | FR-034, C1 |
| `loop.py` acumula ahora bucle, sondeo, latido, commit con reintento, contadores, línea de decisión, volcado cada 60 s y parada. Hay riesgo con el límite de 250 líneas y con una sola responsabilidad. Valdría extraer el volcado y el registro de decisiones. | Menor | plan.md Project Structure | Constitución §14 |

## 3. Cobertura y Constitution Check, revisados por mi cuenta

**Cobertura.** Los IDs C1–C8 y C13 y las pruebas 2, 3, 4, 6 y 8 tienen módulo y prueba en la tabla del plan §10. Esa tabla cubre también FR-001 a FR-036, SC-001 a SC-012, US2.5, US6.3 y US6.4. Las cifras de la FAQ 12 y los tres casos de FR-036 cuadran entre spec, data-model §4, plan §7 y quickstart. Los 14 motivos de research §3 coinciden con kafka-message §6. El reparto commit-offset/contadores en `loop.py` es coherente con FR-001, FR-002 y FR-023:

- `process_record` termina en el hook.
- `loop.py` hace después el commit del offset y, solo entonces, `apply_result` y la línea de registro.
- Los tests de §8 (`test_pipeline` y `test_loop`) y la trazabilidad de C1/C2/C8 reflejan ese reparto.

**Prueba 8 con el hook.** El escenario `restart` publica mensajes sintéticos, así que la salvaguarda `is_synthetic=true` no la impide. El marcador en `/tmp` sobrevive al reinicio de `unless-stopped`, y el offset 2 correspondería al mensaje E1 10:09. Tras el reinicio daría `decision=redelivery_ignored`.

**Servicios y puertos.** Con el perfil `test`, `up` sigue creando 5 servicios. `verify_stack` usa la lista `SERVICES` y `ps --all`, y los contenedores `run --rm` desaparecen. El servicio `tests` no publica puertos (§10).

**Constitución §1 a §21.** Sin violaciones. §1 (orden y `enable_auto_commit=False`), §2 (upsert condicional), §3 (`ms_to_utc` entero), §4 (`country_id` NULL), §5 (nulos y negativos), §6 (cuarentena; el bloqueo por `54*` es un límite aceptado por el alumno), §7 (sintéticos), §8 (contadores solo como registro), §9 (nombres de servicio), §10 (sin puertos nuevos; `.env.example`), §11 (cero dependencias nuevas), §12 (sin país, productor, replay, DLQ ni panel), §13 (inglés/español), §14 (matices en la tabla), §15 (contratos referenciados; `consumer-runtime` solo cubre lo que ningún contrato cubre), §16 (previsto en `tasks.md`), §17 (n/a), §18 (memoria con referencias), §19 (sin código), §20 y §21 (n/a).

## 4. Decisiones que debe tomar el alumno

1. Cómo garantizar que la imagen sea nueva. Opciones: `docker compose build producer` antes de cada escenario, o `up --build` incluyendo `producer` y luego `stop producer`, o un `build:` también en `consumer` (que choca con el comentario de `compose.yaml`). Y para `tests`: `run --build`, o montar `./common` y `./consumer`.
2. ¿Quita la alternativa `ON CONSTRAINT` de spec, research y plan, o prefiere probarla en `test_roles`?
3. ¿Se escribe la línea de decisión antes del commit del offset (cumple FR-003 siempre), o se acepta que se pierda si el commit se salta?
4. Siguen en pie las decisiones provisionales de plan §13 (incluida 13.9). No las cuento como hallazgos.

**Veredicto: Corregir antes de revisar.** No hay bloqueantes. Hay un importante nuevo, la imagen desfasada, que se arregla con una edición pequeña en §12 y en el quickstart. Los 4 importantes de la vuelta 1 están cerrados.
