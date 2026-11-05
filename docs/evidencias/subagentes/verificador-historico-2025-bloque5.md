# Verificación bloque 5 (T022–T025), historico-2025

| Tarea | Veredicto | Prueba y resultado |
|---|---|---|
| T022 README | verificada | Sección «Histórico 2025» presente; comandos coherentes con `--help` de download_main (`--force`, `--start`, `--end`) y load_main; usa `build producer` y `MSYS_NO_PATHCONV=1`; incluye comando del hueco. |
| T023 borrador | verificada | Cita `kafka-message.md` §1 y `db-schema.md` §1, sección B18 (instantánea), hueco >24 h con comando real, límites conocidos; sin lenguaje de predicción/riesgo (grep vacío). |
| T024 evidencias/CODEMAP | verificada | Todas las rutas citadas en CODEMAP (historical/, tests/historical, tests/integration, tests/support, data/historical con 14 archivos) existen. Re-ejecuté `pytest -m "not integration" -q` (UV_PYTHON=3.12): 609 passed. T024_* guardan 609 y 85 passed. |
| T025 cierre | verificada | `git diff --stat` sobre contratos, sql/001_schema.sql y docs/enunciado: vacío. `grep -i "password\|secret" historical/`: vacío. `.env` está ignorado por git (no versionado). data/historical = 14 MB, sin ficheros >5 MB. `git status`: solo cambios esperados más los 7 de consumidor-idempotente (ajenos, no tocados). |

Hallazgos bloqueantes/importantes: ninguno.
Nota de proceso: las casillas T001–T025 de tasks.md siguen sin marcar (`[ ]`); lo hace quien coordina, no el verificador.
