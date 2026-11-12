# Verificación replay, bloque 1 (T041–T043)

Ejecutado por mí: pytest -x -q -m "not integration" tests/common/test_replay_message.py tests/producer/ -> 27 passed.
Contratos: `git diff --stat -- specs` vacío. Sin secretos ni atribución en el código revisado.

| Tarea | Veredicto | Prueba y resultado |
|---|---|---|
| T041 | verificada | Sobre con source=replay_demo, mode=replay, replay_at con Z, is_synthetic, ingested_at y `event` sin tocar: conforme a kafka-message.md §3. Bloque de 6 elementos E1v1, E1v1, E1v2, E1v1, E2, E1 intermedia, sintéticos, enero 2025. |
| T042 | verificada | Con datos reales y chile-norte/20: 20 eventos, ids únicos, orden ascendente, primero 2025-01-01 08:08 UTC, último 2025-01-29 03:44 UTC, M mínima 4. |
| T043 | verificada | Directorio real: 18 302 eventos, extracted_at en formato Z. verify_file por archivo; ReplaySourceError nombra el archivo (tests de byte alterado y archivo ausente en verde). |

Desviación declarada (solo manifest.files, sin usgs_gap_*): aceptable, coincide con research D10.
CODEMAP.md: fila nueva del bloque 1 con los archivos y los IDs J1, J2, J6, J7. Correcto.
Hallazgos bloqueantes o importantes: ninguno.
Límite conocido: `tasks.md` aún con T041–T043 sin marcar (lo hace quien cierre el bloque).
