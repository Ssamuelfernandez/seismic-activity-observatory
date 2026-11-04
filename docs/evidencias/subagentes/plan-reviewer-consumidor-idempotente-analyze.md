## Revisión del paso ANALYZE — consumidor-idempotente

Revisé constitución, CLAUDE.md, CODEMAP, spec, plan, tasks, research, data-model, quickstart, consumer-runtime y los tres sitios del repositorio donde se apoyan las tareas: `sql/002_roles.sql`, `Dockerfile` y `tests/`. No ejecuté nada. `analysis.md` no aparece en ningún documento salvo en la bitácora, que es lo esperado. El `git diff` de contratos y enunciado que me pasó el orquestador estaba vacío.

### Verificación de las correcciones de analyze

| Corrección | Resultado |
|---|---|
| A1 (FR-003 en la trazabilidad) | OK. Aparece en la fila «C1, FR-003, FR-004» de tasks (T001, T047, T048, T082, T084). |
| B1 (volcado final de COUNTERS) | OK con un matiz, ver hallazgo 3. T048, T055 y T056 dicen lo mismo. Es compatible con el orden de FR-001 y FR-023: el bucle confirma el último mensaje, aplica los contadores, y luego cancela y espera a la corrutina. |
| B2 (marcadores de research) | OK. §6 → T093 y T041; §7 → T032 y T042; §8 → T037. T021–T025 también es correcto. |
| B3 (plan) | Parcial. El hook `after_db_commit(ref, is_synthetic)` aparece en plan §4. El plan ya no dice que tasks.md no existe: indica 93 tareas. El contenido de `test_roles` (a)–(e) tiene un error, ver hallazgo 1. |
| M-1 a M-7 | OK. Cumplen todas: data-model §3 nombra `writer.py`; `evidence.record_*` trunca en la primera llamada y añade bloques con cabecera; regla de imagen `tests` al día; T002 registra `published:` y los archivos de prueba; T012 lista 7 resultados; CC-DOC con el `print` heredado en `common/health.py` líneas 86 y 90, que he comprobado en el código; T034 sin etiqueta M-7. |
| T001a–d | Siguen siendo la tarea que alinea. Data-model §1 aún no tiene `event_id`/`ref`/`is_synthetic` y plan §4 aún dice «justo antes de que el bucle llame a `consumer.commit`». T001 lo corrige y no queda una incoherencia irresoluble. Quedan frases residuales, ver hallazgo 4. |
| Cifras | Sin contradicciones nuevas. Revisé FAQ 12 con los ms (10:00 = 1793786400000, etc., calculados), contadores 5/5, 7/5 y 7/7, 5/2/1/2, 101, 512, 64 y 1000–2999. Los extremos de T093 también coinciden: 32503679999999 y −30610224000000. Las esperas 1, 2, 4, 8, 16, 30, 30 coinciden en plan §5 y T045. Los totales también (93 tareas, 7 subcomandos, 9 ejecuciones, 7 archivos de T044, 16 variables). La numeración T0xx es coherente entre documentos. |

### Hallazgos

**BLOQUEANTE:** ninguno.

**IMPORTANTE**

| # | Hallazgo | Dónde | Regla o ID |
|---|---|---|---|
| 1 | La aserción (e) de `test_roles` dice que el rol puede `INSERT`/`UPDATE` en `live.event_version`. `sql/002_roles.sql:62` concede solo `SELECT, INSERT` sobre `event_version`; el `UPDATE` es solo de `current_event` y `country`. La prueba fallaría con `42501`. Si el alumno intenta arreglarlo concediendo `UPDATE`, rompe FR-027. | `tasks.md` T037 (e); `plan.md` §8 `test_roles` (e) | FR-027, US6.4, constitución §6 |
| 2 | Los nombres de archivo de prueba chocan: T055 y T069 crean `tests/consumer/test_loop.py` y ya existe `tests/producer/test_loop.py`. No hay ningún `__init__.py` en `tests/` y `pyproject.toml` no define `importmode`. Pytest en modo «prepend» daría *import file mismatch* al correr la suite completa (T057, T061, T070, T087). Por carpeta, `uv run pytest tests/consumer` sí funciona. T003 y T014 solo mencionan `tests/support/__init__.py`. | `tasks.md` T003, T014, T055, T069 | FR-033, SC-010 |

**MENOR**

| # | Hallazgo | Dónde | Regla o ID |
|---|---|---|---|
| 3 | T047 dice que la corrutina vuelca «al cancelarse **o al activarse `stop_event`**». T048, T055 y T056 dicen que vuelca solo al ser cancelada por el bucle. Si reacciona sola a `stop_event` puede volcar antes de que termine el mensaje en curso, o escribir dos veces. Plan §7 y consumer-runtime §4 («al detenerse») no dicen quién escribe, y eso es compatible. | `tasks.md` T047 | FR-023 |
| 4 | T001b solo cambia la línea «Garantías» de plan §1. Siguen diciendo que FR-003 «se cumple siempre» y que «una reentrega duplica la línea» el paso 7 de plan §1, la «Consecuencia aceptada» de plan §1, plan §13.10(c) y el párrafo «Cuándo se escribe…» de consumer-runtime §4. Chocan con la nueva garantía y con T076, donde tras el corte no hay `decision=` previa del offset 2. Conviene que T001b y T001c las nombren. | `tasks.md` T001b y T001c; `plan.md` §1 y §13.10; `consumer-runtime.md` §4 | FR-003, prueba 8 |
| 5 | Quickstart §5 y §6 muestran `python scripts/verify_consumer.py faq12` y los demás sin `--yes`. T073 hace que terminen con código 2. El criterio de T091 («los comandos de quickstart §2–§8 funcionan tal cual están escritos») falla. Se corrige en T091, pero es mejor decirlo ya. | `quickstart.md` §5/§6; `tasks.md` T091 | SC-012 |
| 6 | El criterio de T034 es «falla antes de T035 y pasa después», pero `test_writer_inconsistent.py` solo puede pasar tras T043, porque `writer.py` no existe antes. El texto aclara en parte que esa parte falla antes de T043. | `tasks.md` T034 | consistencia |
| 7 | El criterio de T044 tiene una frase repetida y confusa: «`-- [n] despues` y «después»». | `tasks.md` T044 | redacción |

### Decisiones que el alumno debe tomar

- **Hallazgo 2.** Elegir una de estas tres vías para evitar la colisión de `test_loop.py`: renombrar el nuevo a `test_consumer_loop.py` (la más simple), añadir `__init__.py` en cada carpeta de `tests/`, o fijar `importmode=importlib` en `pyproject.toml`.
- **Hallazgo 1.** Confirmar que (e) pasa a «`INSERT` y `SELECT` en `event_version`, y `UPDATE` denegado con `42501`». Es una corrección de la prueba, no de los permisos.

### Veredicto

Corregir antes de revisar. Los hallazgos 1 y 2 son ediciones breves de tasks y plan; los menores pueden arreglarse en la misma pasada.
