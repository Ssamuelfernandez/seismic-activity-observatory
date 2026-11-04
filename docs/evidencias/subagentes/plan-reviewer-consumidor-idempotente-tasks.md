REVISIÓN DE TASKS: consumidor-idempotente (specs/003-consumidor-idempotente/tasks.md). No he modificado nada ni ejecutado comandos; solo he leído archivos.

Comprobado sin hallazgos:
- Las 92 tareas T001-T092 están en `[ ]` y ninguna lleva `[x]`.
- La cobertura de C1-C8 y C13, de las pruebas 2, 3, 4, 6 y 8 y de las historias US1-US6 es correcta.
- Cada FR-001..036 y SC-001..012 tiene tarea y prueba, salvo FR-020 (ver I-1).
- Rutas, módulos y estructura loop/reporting/resilience/pipeline/writer coinciden con plan, data-model y consumer-runtime.
- El orden pruebas antes que implementación es correcto. `resilience` (T046) va antes de `pipeline` (T054) y no hay ciclos.
- Las ediciones a archivos de 002 están listadas (Dockerfile, compose.yaml, .env.example, check_env_example, config.md, verify_stack, README, test_broker_probe), salvo la excepción de M-1.
- El alcance es correcto: sin país por polígono, productor real, histórico, replay, API ni frontend. T088 vigila contratos, enunciado y `sql/`.
- La aritmética de la FAQ 12 es correcta: los ms Unix (10:00 = 1793786400000, etc.) y los rangos 1000-01-01 y 3000-01-01 cuadran.
- Los 5 menores del informe v3 están recogidos en T001 (data-model, plan §1 y §4, consumer-runtime §4, research §12), T029, T043 y T054.

## Veredicto: Corregir antes de revisar
No hay bloqueantes. Hay 5 importantes, que son correcciones de redacción y diseño de tarea, no de alcance.

## BLOQUEANTES
Ninguno.

## IMPORTANTES

| Id | Hallazgo | Dónde | Regla / ID |
|---|---|---|---|
| I-1 | **FR-020 sin prueba verificable.** Ninguna tarea comprueba que `source`, `replay_at` e `ingested_at` se copian del sobre a las tablas. Tampoco hay aserción de que el `original` guardado en la base coincide con el `event` recibido (US4.5). T021 y T041 solo miran `received_at`, `ingested_at ≠ tiempo del evento` e `is_synthetic`. Añadir esas aserciones en T021 (unitaria) y T041 (integración). | T021, T041; trazabilidad «C6, C7, FR-016 a FR-021» | C7, FR-020, US4.5 |
| I-2 | **El criterio de T074 se contradice.** Pide que, tras `docker compose stop consumer`, la última línea `COUNTERS` tenga `received=5`, `new_events=2` y `redeliveries_ignored=2`. Pero antes ese mismo escenario reenvía el mensaje 1 cien veces (prueba 2) y publica la versión tardía (prueba 4). El `COUNTERS` final tendría `received` ≈ 106 y no 5. Hay que fijar de dónde sale la lectura (p. ej. capturar `COUNTERS` o el SQL justo tras los 5 mensajes, o dejar el contador final a T079) y decirlo. | T074 (Criterio) frente a T079 | C8, SC-001, SC-009 |
| I-3 | **T044 pide evidencias que ningún test genera.** `faq12_antes_despues.out` (vistas antes y después), `prueba2_reenvio.out`, `prueba3_4_versiones.out` y `prueba6_cuarentena.out` salen de una única ejecución de pytest con `-s`. La base temporal se borra al terminar la sesión, y T039, T040 y T042 no dicen que impriman consultas ni resultados. Opciones: añadir a esas tareas una función que imprima las consultas de quickstart §5, o retirar esas evidencias del bloque 3 y dejarlas a T074/T075. | T044, T039, T040, T042 | FR-034, SC-001, SC-002, SC-004 |
| I-4 | **T041 (condición de escalado) está mal definida.** Dice «se reduce el rango y se anota». El apartado «Escalados» dice que se escala al alumno. Reducir el rango cambia `MIN_EPOCH_MS` y `MAX_EPOCH_MS`, que ya usan T021-T025, research §6, consumer-runtime §1 y plan §13.2, y no se lista qué rehacer. Además se descubre en el bloque 3, con el bloque 2 ya construido. Conviene decidir una de dos cosas: que la comprobación de extremos del `CHECK` se haga antes (en T036/T037, solo con SQL), o que T041 diga explícitamente «detener y escalar» y enumere las tareas a rehacer. | T041 frente a «Escalados» (b) | §12 (alcance), FR-014 punto 2 |
| I-5 | **`ProcessingResult` no puede alimentar la línea `same_updated_conflict`.** consumer-runtime §4 exige `updated_ms=…` en esa línea y T047 la hace salir de `log_decision(result)`. Pero T001 y T013 solo añaden `event_id`, `ref` e `is_synthetic` al `ProcessingResult`. Falta `updated_ms` (T001, T013), o que T047 indique de dónde sale. | T001, T013, T047; consumer-runtime §4 | FR-003, FR-009 |

Hay además un punto de aislamiento entre tests, que valoro como importante-menor. T040 y T042 añaden `CHECK` y disparadores diferidos a la base temporal. La base es de sesión, y T058 revoca permisos sobre ella. Solo T058 exige restaurar el estado. T040 y T042 deberían exigir lo mismo, con `DROP` en un `finally` o con una base por prueba. Si no, el resultado depende del orden de ejecución.

## MENORES
- **M-1: archivo de 002 sin editar.** `specs/002-infra-compose/quickstart.md` línea 26 sigue citando «Evento recibido [SINTÉTICO]», que desaparece con `describe_message`. Está fuera de T082, T083 y T010. Se puede añadir a T083 o anotar que queda como histórico.
- **M-2: `.env` local.** T008 solo cambia `.env.example`. El `.env` real del alumno conservará `KAFKA_GROUP_ID=consumer-minimal`, que Compose no lee de `.env.example`. Añadir una nota o paso (no se comitea). Afecta a T002, T011 y T086, que no usan `down -v`.
- **M-3: servicio `tests` incompleto.** T007 solo cita las credenciales de la base. El publicador T072 y los tests de integración necesitan también `KAFKA_BOOTSTRAP_SERVERS` y los datos de host/puerto de PostgreSQL. Tampoco se fija el nombre de la imagen («otro nombre») ni la opción de caché (`cache_dir` «o» `no:cacheprovider`). Esto son decisiones abiertas de poco peso.
- **M-4: dependencia no declarada.** T037 usa la sentencia de `queries.py` (T035), pero la sección de dependencias solo dice «T036 precede a T037-T042». Debería decir también «T035 precede a T037».
- **M-5: «si T037 (c) no diera `42501`».** La tarea no dice qué hacer. Es una prueba negativa documentada y el criterio es que pase. Conviene decir si en ese caso se escala o solo se anota.
- **M-6: contradicciones de redacción.**
  - T064 dice «las cuatro de live y replay». Plan §3 define 8 tablas: `country`, `date_dim` y 3 de `live` + 3 de `replay`.
  - T089 pide «0 `print(`» y a la vez «sin resultados nuevos respecto a 002».
  - CC-DOC prohíbe `print`, pero T072 y T073 son scripts CLI que sí lo necesitan.
  - T086 y T087 repiten la suite de integración.
- **M-7: `inconsistent_state` sin test.** El WARNING que emite `writer.py` (T043) no tiene prueba. Tampoco la tienen el volcado periódico y final de `COUNTERS` (T048, T056). Los cubre solo la ejecución real de T074 y T079. Basta un test unitario con un doble.
- **M-8: CLAUDE.md a nivel de bloque.** CLAUDE.md pide tests, evidencia y `CODEMAP.md` por tarea que cree código. T012, T031, T044, T061, T070 y T081 lo aplican por bloque (decisión (6) de «Escalados»). Es razonable, pero es una desviación literal y debería confirmarla el alumno.
- **M-9: `down -v` destructivo.** `verify_consumer.py` ejecuta `down -v`, que borra los volúmenes locales de Kafka y PostgreSQL del alumno, incluido lo que dejó 002. Conviene una advertencia o una confirmación en T073.
- **M-10: T076.** No dice cómo se pasa `CONSUMER_FAULT_CRASH_AT_OFFSET` (¿variable de entorno del script o edición de `.env`?). Tampoco que hay que recrear el contenedor para dejarla vacía, ya que el marcador vive en `/tmp`. «Queda vacía en `.env`/entorno» es ambiguo.
- **M-11: comandos Unix.** Los criterios usan `grep`, `wc`, `awk` y `ls`, y el equipo del alumno es Windows con PowerShell. Aclarar que se ejecutan en Git Bash o con el equivalente.
- **M-12: T088 con `git diff --stat`.** No ve cambios ya en el índice ni archivos sin seguimiento. Sería más fiable `git diff HEAD --stat` más `git status --short -- <rutas>`.
- **M-13: producto sintético de 002.** Nada comprueba antes del bloque 7 (T082) que el evento de `common/synthetic_event.py` pasa `validate_message`. Si no pasara, la cuarentena se llenaría con el productor de 002 en marcha. Añadir un test unitario en el bloque 2 (T023).
- **M-14: tamaño de T001.** Mezcla cuatro ediciones de documentos de diseño distintos en una sola tarea.
- **M-15: T055.** Una prueba que asegura que `describe_message` «ya no existe» es poco útil.

## Condiciones de escalado
- **T037(b):** bien definida (detener, no conceder `SELECT`, escalar).
- **T088:** bien definida en la condición (diff no vacío → detener y escalar). Ver M-12 para fiabilidad.
- **T041:** mal definida (ver I-4).

## Decisiones que debe tomar el alumno
1. T041: si el `CHECK` no acepta los extremos, ¿se reduce el rango y se rehacen las tareas dependientes (propuesta) o se escala siempre? ¿Se adelanta la comprobación al bloque 3 inicial?
2. Evidencias del bloque 3 (I-3): ¿se generan desde tests con `-s` o se dejan solo a las ejecuciones con Kafka real del bloque 6?
3. Aplicación de CLAUDE.md por bloque en vez de por tarea (M-8).
4. `docker compose down -v` en `verify_consumer.py` sobre su stack local (M-9).
