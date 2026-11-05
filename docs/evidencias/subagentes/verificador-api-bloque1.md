# Verificación api, bloque 1 (T001-T005)
Pruebas ejecutadas por mí: `pytest -m "not integration" -x -q` = 699 passed; `tests/api` + `test_api_config.py` = 90 passed; `docker compose --profile test run --rm tests pytest tests/integration/test_api_harness.py -q` = 1 passed (el pool del rol observatory_api lee los eventos sembrados en live y replay). `check_env_example.py` rc=0; `docker compose config` rc=0.
`git diff --stat` sobre contracts/, docs/enunciado/ y sql/001_schema.sql: vacío.
Nota: el test de integración no corre con el venv local (falta DB_HOST); corre bien por compose, como pide la tarea.

| Tarea | Veredicto | Motivo |
|---|---|---|
| T001 | VERIFICADA | api_config con tests en verde; httpx==0.28.1 en dev; variables en api/tests de compose y en .env.example |
| T002 | VERIFICADA | tests/api/test_params.py en verde; params/timeutil sin importar fastapi ni asyncpg (grep) |
| T003 | VERIFICADA | tests/api/test_cursor.py en verde |
| T004 | VERIFICADA | test_errors.py en verde; main.py con openapi_url=None, docs/redoc None y manejadores registrados |
| T005 | VERIFICADA | prueba de integración por compose en verde; conftest, temp_database y api_seed presentes |

Hallazgos bloqueantes o importantes: ninguno.
Límite conocido: CODEMAP.md aún no recoge los archivos nuevos (api/cursor.py, errors.py, params.py, timeutil.py, common/api_config.py); CLAUDE.md lo exige al terminar la tarea, conviene hacerlo al cerrar la feature.
