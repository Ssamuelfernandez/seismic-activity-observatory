# Verificación B1 (T094-T098), pruebas-aceptacion

Ejecutado: `docker compose --profile test run --rm tests pytest tests/integration/test_acceptance_api.py -x -q` -> 5 passed en 2,63 s.

| Tarea | Veredicto | Prueba y resultado |
|---|---|---|
| T094 (I1) | verificada | SQL `current_event` = 1 fila; lista /api/eventos solo con synthetic-acc-01; total de estadísticas = antes + 1. |
| T095 (I3) | verificada | País ESP a JPN, hora 10:00 a 14:00, mag 3.0 a 4.5; recuentos por país y por hora cambian; `event_version` con ambas `updated`. |
| T096 (I4) | verificada | Lista y estadísticas idénticas antes y después (solo se excluyen `generated` y `recent_period`, que dependen del reloj); historial con las 2 versiones. |
| T097 (I5) | verificada | `mag IS NULL`=1, `mag = 0`=0, API `null`; con `min_mag=0` features vacías, `null_mag_excluded`=1 (contrato api.md §3.1); `no_value`=1. |
| T098 (I7) | verificada | `country_id` NULL, cuarentena = 0, `country_id=none` lo devuelve, total 1, recuento por hora y por país `None`=1. |

Comprobaciones: las pruebas usan el fixture `db` (TempDatabase) y ids `synthetic-acc-NN`; no tocan `live` real. Los diffs de `specs/` y `sql/` están vacíos. Solo hay cambios en CODEMAP.md (1 línea), el nuevo test y `docs/evidencias/pruebas/`. No hay hallazgos bloqueantes ni importantes.

Límite conocido: `db` es de sesión; la independencia entre pruebas (totales == 1) depende de la limpieza entre pruebas. En esta ejecución, en orden, pasa.
