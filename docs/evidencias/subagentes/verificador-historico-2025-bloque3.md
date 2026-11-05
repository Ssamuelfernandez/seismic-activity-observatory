# Verificación historico-2025 bloque 3 (T010–T018)
Pruebas ejecutadas por mí: `pytest -m "not integration"` = 609 passed, 0 rotas; integración completa en Docker (evidencia redirigida a historico-2025) = 85 passed (12 son las nuevas T014–T016, T018). `git diff --stat` sobre contratos, sql/001_schema.sql y docs/enunciado: vacío.

| Tarea | Veredicto | Prueba / resultado |
|---|---|---|
| T010 | verificada | suites 003–005 y unitarias en verde; test_transform pasa de 19 a 20 pruebas, ninguna eliminada; integración previa (idempotencia, cuarentena, restart) pasa |
| T011 | verificada | test_loader pasa; usa `build_message_bytes` + `process_record` con `RawRecord(partition=None, offset=None)` |
| T012 | verificada | test_verify y test_queries pasan; SQL solo sobre `live` |
| T013 | verificada | test_load_main pasa; Dockerfile con `COPY historical` |
| T014 | verificada | integración: únicos − cuarentena, `source=usgs_historical`, `kafka_*` NULL en event_version, verify_load verdadero |
| T015 | verificada | 3 cargas, la 2.ª y la 3.ª con misma huella (0 filas nuevas/modificadas) |
| T016 | verificada | mag nula, lat 145 → cuarentena, país ESP/nulo, no retrocede ante `updated` mayor |
| T017 | verificada | revisión estática pasa; única excepción acotada: `load_main.py` importa `common.geo` solo para cablear `PipelineDeps` (igual que consumer/loop.py) |
| T018 | verificada | hueco: 4 iguales sin cambio, 1 menor no retrocede, 3 nuevos una vez |

Decisión Q desde resultados de `process_record`: defendible. El rol solo tiene INSERT sobre `live.quarantine`, y Q son los ids que el propio pipeline mandó a cuarentena en esa carga. La comparación `count(current_event ∈ U) == |U| − |Q|` sigue detectando pérdidas o duplicados en `current_event`. Límite conocido: no comprueba de forma independiente que la cuarentena se haya escrito (eso lo cubre la huella de un administrador en los tests). No hay hallazgos bloqueantes ni importantes.
