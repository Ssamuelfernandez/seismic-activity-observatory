## Revisión ANALYZE, vuelta 2 — consumidor-idempotente

Veredicto: **Listo para tu revisión.** Sin bloqueantes ni importantes. Los 2 importantes y los 5 menores del informe previo están resueltos y no veo contradicciones nuevas. No ejecuté nada; solo leí.

### Verificación punto por punto

| Punto | Resultado |
|---|---|
| (e) de `test_roles` frente a los GRANT | OK. `sql/002_roles.sql:62` concede `SELECT, INSERT` sobre `live/replay.event_version`. T037 (e), plan §8 y plan §13.11(b) dicen INSERT y SELECT permitidos y UPDATE denegado con `42501`. Los demás permisos de (e) también coinciden con el archivo: `current_event` con INSERT/UPDATE (línea 61), `date_dim` con INSERT (línea 60) y `country` con INSERT/UPDATE (línea 59). Es coherente con FR-027 y US6.4, y T037 sigue marcando que no se concede ningún permiso nuevo. |
| Nombres base de tests únicos | OK. Existentes: `test_config`, `test_health`, `test_logging_setup`, `test_retry`, `test_synthetic_event`, `test_broker_probe` y `tests/producer/test_loop`. Nuevos de tasks.md y plan §8/§10: `test_records`, `test_kafka_topics`, `test_decode`, `test_storable`, `test_transform`, `test_validation`, `test_validation_hostile`, `test_quarantine_row`, `test_processing`, `test_purity`, `test_catalog`, `test_db_errors`, `test_queries`, `test_writer_inconsistent`, `test_resilience`, `test_reporting`, `test_counters`, `test_fault_hook`, `test_pipeline`, `test_consumer_loop`, `test_schema_check`, `test_roles`, `test_schema_parity`, `test_faq12`, `test_idempotence`, `test_nulls_times`, `test_quarantine`, `test_quarantine_retry`, `test_restart_crash`, `test_counters_reconcile`, `test_catalog_load`, `test_date_dim`, `test_verify_consumer_helpers`. No hay duplicados. `tests/integration/conftest.py` es el único `conftest`. `pyproject.toml` tiene `pythonpath=["."]` y no tiene `importmode`; T003 prohíbe añadir `__init__.py`. |
| Referencias a `test_consumer_loop` | OK. tasks.md (T003, T055, T069, decisión 11), plan §10 (líneas 301 y 302) y plan §13.11(a). Ya no queda un `tests/consumer/test_loop.py` como archivo nuevo: las menciones de `test_loop` en tasks.md y plan §13.11 son el existente `tests/producer/test_loop.py`. CODEMAP.md y README.md no mencionan ninguno de los dos nombres. |
| Criterio `pytest --collect-only` | Presente en T003, T012, T057 y T087, y en plan §13.11(a). |
| T047, T048, T055, T056 | Consistentes. El volcado final lo escribe solo la corrutina de `reporting`, una vez, al ser cancelada por el bucle. El bucle la cancela y la espera después de confirmar el último mensaje, y no escribe otro `COUNTERS`. Coincide con plan §13.11(c). |
| T001b y T001c frente a las frases residuales | Cubren plan §1 paso 7, «Garantías», «Consecuencia aceptada» y plan §13.10(c), además de plan §4 y consumer-runtime §2 (hook antes de la línea de decisión). T001c cubre consumer-runtime §4 y quién emite cada línea. Las frases viejas siguen en los documentos (plan:148, 152, 199, 355; consumer-runtime:59), como corresponde antes de ejecutar T001. El `grep` del criterio de T001 las detectaría. Son coherentes con T076, T059 y T053 (hook antes de la decisión, primera entrega con `FAULT` y sin `decision=`, una sola línea `decision=` tras la reentrega) y con plan §13.11(d). |
| Quickstart con `--yes` | OK. Líneas 48, 74 y 78–83 llevan `--yes`; `kafka-down` no lo lleva, igual que en T073. Es coherente con T073, T071 y T091. |
| Plan §13.11 | Coherente con tasks.md en sus cuatro puntos (a)–(d). |
| Numeración y casillas | 93 líneas `- [ ] T###` y 0 casillas `[x]`. La numeración T001–T093 está intacta, con T093 ejecutada tras T011. |
| Alcance | No se introdujo alcance nuevo. Las ediciones de T001a–d son de documentación de diseño. |
| Contratos y enunciado | El diff que pasó el orquestador estaba vacío. T088 y el criterio de T001 lo siguen comprobando. |

### Hallazgos

**BLOQUEANTE:** ninguno.

**IMPORTANTE:** ninguno.

**MENOR**

| # | Hallazgo | Dónde | Regla o ID |
|---|---|---|---|
| 1 | Hasta que se ejecute T001, plan §13.11(d) ya tiene la garantía corregida (muerte entre 5 y 7 sin línea, entre 7 y 8 duplicada). Plan §1 (pasos 7, «Garantías», «Consecuencia aceptada»), plan §13.10(c) y consumer-runtime §4 dicen todavía «se cumple siempre» y «una reentrega duplica la línea». Es transitorio y T001b/T001c lo resuelven. El alumno lee documentos que se contradicen, así que conviene decírselo al presentarlos. | plan.md §1, §13.10(c) y §13.11(d); consumer-runtime.md §4 | FR-003, prueba 8 |
| 2 | En «Escalados y decisiones propias», la decisión (10) aparece después de la (11) y la (12). Es solo de orden y redacción. | tasks.md, última sección | formato |
| 3 | Plan §12 todavía deja abierta la opción de `cache_dir` o `PYTEST_ADDOPTS` para la caché de pytest. T007 fija `-p no:cacheprovider` como decisión única, así que no hay contradicción de tareas. | plan.md §12, tasks.md T007 | ambigüedad menor |

### Decisiones que el alumno debe tomar

Ninguna nueva. Siguen vigentes las decisiones provisionales de tasks.md, en especial la (6) (evidencias por bloque, desviación literal de CLAUDE.md) y la (10) (T093 con número fuera de orden).
