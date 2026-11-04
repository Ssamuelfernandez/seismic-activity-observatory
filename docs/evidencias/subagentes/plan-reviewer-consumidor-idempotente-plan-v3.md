REVISIÓN DEL PLAN, vuelta 3 (última): consumidor-idempotente (specs/003-consumidor-idempotente/). No reclamo tasks.md. Los contratos de 001 y docs/enunciado no cambian (diff vacío, según el orquestador). Solo he podido leer archivos, no ejecutar nada.

## 1. Resolución de lo señalado en la vuelta 2

El importante (imagen desfasada) está resuelto. Los 10 menores están resueltos, con matices menores que aparecen en la tabla del §3.

- **Imagen al día (importante).** Plan §8 «Imagen al día», quickstart §2, §4 y §6, y plan §13.10(a) hacen `docker compose build producer` como primer paso de cada escenario. Antes de pytest hacen `--profile test build tests`. Solo `producer` conserva `build:` con `target: production` (§12), así que no reaparece el conflicto de etiqueta que avisa el comentario de `compose.yaml` (líneas 7-9).
- **§12 decía que los tres servicios llevan `build:`.** Corregido: dice «solo `producer`».
- **`ON CONSTRAINT`.** Eliminado como alternativa. Solo queda mencionado como descartado, en plan §9 y §13.10(b) y en research §8. Spec y consumer-runtime no lo citan. `test_roles` (c) y research §8 coinciden: se prueba que el destino con columnas da `42501`.
- **Dockerfile y compose.** §12 recoge `USER root` y volver a `USER observatory` en la etapa `test`. También el `networks: [backend]` explícito, la interpolación `${CONSUMER_FAULT_CRASH_AT_OFFSET:-}`, la caché de pytest y `check_env_example.py`. Es coherente con el `Dockerfile` actual, que no tiene etapas nombradas, y con el ancla `x-python-service` de `compose.yaml`.
- **Tabla de §2.** Ya no queda cortada. Las filas `catalog`, `db_errors` y `counters` se renderizan dentro de la tabla.
- **Referencias cruzadas.** Constitution Check apunta a §2. La nota de §8 remite a «Project Structure». El paso 4 de §1 remite a §5. Las verifiqué una a una y son válidas.
- **`broker_unreachable`.** Definida en consumer-runtime §4 (WARNING, la emite `broker_reachable`). La usan plan §8 (`kafka-down`) y la trazabilidad de FR-029.
- **Línea de decisión.** Va tras el commit de PostgreSQL y antes del commit del offset. Los contadores van tras el commit del offset. Plan §1, §5, §7, §8, consumer-runtime §4 y quickstart §3 dicen lo mismo.
- **`loop.py`.** Dividido en `loop.py`, `reporting.py` y `resilience.py`.
- **Memoria y README.** §11 de `docs/memoria.md` incluye transacción, orden de commits y secuencia de la FAQ 12. §12 nombra el cambio de `[SINTÉTICO]` en el README (línea ~80) y la dependencia de A1 de un evento nuevo del productor.

## 2. Coherencia de la estructura de módulos y del flujo

- **Módulos.** El reparto `common/*` y `consumer/{main, loop, reporting, pipeline, writer, queries, db_errors, resilience, counters, catalog_loader, schema_check, fault_hook}` es el mismo en Project Structure, §1, §2, §5, §7, §8, §10, §11 y §12. También coincide con consumer-runtime §4 y con data-model. `reporting.py` y `resilience.py` aparecen con las mismas responsabilidades en todos esos sitios. Los tests de `reporting`, `resilience` y `loop` están en §8 y en la trazabilidad de §10.
- **Flujo de 9 pasos.** Es coherente con:
  - FR-001/FR-002: el offset se confirma tras el commit de PostgreSQL.
  - FR-003: hay una línea por decisión.
  - FR-023/FR-036 y SC-009: los contadores cambian solo tras el commit del offset.
  - La reentrega no cuenta como contador nuevo, salvo la limitación documentada de `CommitFailedError`.
- **Aritmética de la FAQ 12.** Comprobada: los ms Unix del data-model, 1793786400000 (10:00) a 1793787120000 (10:12), y las cifras de los tres casos de FR-036 (5, 5 y 7 conversiones) cuadran.
- **Cobertura.** C1–C8 y C13 tienen módulo y prueba en la tabla de plan §10. Las pruebas 2, 3, 4, 6 y 8 también. Cubre además FR-001 a FR-036, SC-001 a SC-012, US2.5 y US6.
- **Cierre de feature.** Previsto en §11 y §12 para `tasks.md`: pruebas ejecutadas, evidencias, README y CODEMAP.
- **Contratos.** Referenciados, no copiados. FR-035 se comprueba con `git diff --stat`. Escalados al alumno: ninguno.

### Constitution Check, verificado regla a regla

- §1: orden fijo y `enable_auto_commit=False`.
- §2: upsert con `WHERE EXCLUDED.updated_ms >`.
- §3: `ms_to_utc` con aritmética entera.
- §4: `country_id` queda `NULL`.
- §5: nulos y negativos se conservan.
- §6: cuarentena sin bloqueo, con el límite `54*` aceptado por el alumno.
- §7: `is_synthetic` se copia a las tres tablas.
- §8: los contadores no los lee la API.
- §9: nombres de servicio.
- §10: ningún puerto nuevo, y `.env.example` se actualiza.
- §11: cero dependencias nuevas.
- §12: sin país, productor, replay, DLQ ni panel.
- §13: identificadores en inglés, documentación en español.
- §14: ≤250 líneas conseguido con la división en tres módulos.
- §15: `consumer-runtime` solo cubre lo que ningún contrato cubre.
- §16: previsto para `tasks.md`.
- §17: no aplica.
- §18: la memoria usa referencias, no copias.
- §19 y §20: el plan no contiene código y no hace commits.
- §21: sin lenguaje de predicción ni de riesgo.

No hay violaciones.

## 3. Hallazgos

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| Sin hallazgos bloqueantes ni importantes. | — | — | — |
| `ProcessingResult` no incluye `event_id` ni la referencia al mensaje (`MessageRef`). `log_decision(result)` y la línea `retry` los necesitan, y el plan dice que el bucle recibe solo el resultado. Basta añadirlos al record o pasar `ref` a `log_decision`. Es un detalle de diseño, no una decisión. | Menor | data-model.md §1 (fila `ProcessingResult`); plan.md §1 paso 7 | FR-003 |
| Dos frases de plan §1 son imprecisas y no cuadran con los 9 pasos. (a) «FR-003 se cumple siempre»: si el proceso muere entre los pasos 5 y 7, la línea no se escribe. Eso incluye el hook `os._exit(137)` del paso 6, que se ejecuta antes de la línea de decisión. Entonces la primera entrega de la prueba 8 no deja `decision=`, solo `FAULT`, y la «duplicación de línea» aplica solo si la muerte ocurre entre los pasos 7 y 8, por ejemplo con `CommitFailedError`. (b) «Ningún contador cambia antes de 8» debería decir «hasta completar el paso 8». | Menor | plan.md §1 (pasos 7 y 9, «Garantías»); consumer-runtime.md §4 («Cuándo se escribe…») | FR-003, FR-023 |
| Plan §4 dice que el hook se invoca «justo antes de que el bucle llame a `consumer.commit`». Entre ambos está ahora `log_decision` (paso 7). Debería decir «antes de la línea de decisión y del commit del offset». | Menor | plan.md §4 (Hook de corte) | C2, prueba 8 |
| Falta decir quién emite algunas líneas: `validation_gap`, `inconsistent_state`, `FAULT` y `catalog loaded`. Además, el WARNING de `same_updated_conflict` convive con la línea de decisión INFO que escribe `reporting`. `decide_version_outcome` es pura (`common/`) y no puede registrar la línea `inconsistent_state` que data-model §3 le atribuye. Es una tarea de `tasks.md`, no una decisión del alumno. | Menor | consumer-runtime.md §4 (última frase); data-model.md §3 | FR-003, §14 |
| Research §12 da `docker compose --profile test run --rm tests pytest …` sin el `build` previo. Plan §8 y quickstart §4 sí lo incluyen, y prevalecen. Conviene alinear la frase. | Menor | research.md §12 | SC-009 (fiabilidad de la evidencia) |

## 4. Decisiones que debe tomar el alumno

Ninguna nueva. Siguen vigentes las provisionales de plan §13 (13.7 `float` frente a `Decimal`, 13.9 y 13.10) y las preguntas pendientes de la spec. No las cuento como hallazgos.

**Veredicto: Listo para tu revisión.** Los cinco menores restantes se pueden resolver al redactar `tasks.md` o con ediciones de una línea.
