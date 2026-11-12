# Verificación replay, bloques 4 y 5 (T050-T058)
Comprobado yo mismo: SQL real: replay 22/24/0, 0 filas con replay_at nulo o source distinto de replay_demo; live 213/213/0 (creció desde 211 porque el productor live corre de nuevo; coherente). curl: mode=replay -> metadata.mode=replay, 22 eventos; sin mode -> live, 0 de replay en 2025.
Log T053: 26 líneas topic replay = 22 new_event + 1 newer_version + 1 late_old_version + 2 redelivery_ignored. T054: repetición idéntica y archivo alterado -> exit 1 con sha256 y nombre. Capturas leídas: banner "REPRODUCCIÓN" + "DATOS SINTÉTICOS", total 22 (API); En vivo sin banner de replay (muestra "DATOS DESACTUALIZADOS" por el productor parado entonces, ajeno).
Diff de contratos, sql, enunciado y consumer/pipeline.py vacío; sin cambios en frontend ni consumidor-idempotente; sin atribución a Claude. CODEMAP: rutas existen. README «Replay», borrador y CODEMAP coherentes (22/24/0, 51 s, 211 antes/después).
verify_stack 14/16: compose.override.yaml está en .gitignore y publica 127.0.0.1:5433; los 2 fallos son solo de puertos, ajenos a la feature.
| Tarea | Veredicto |
|---|---|
| T050 README | verificada |
| T051 borrador | verificada |
| T052 antes | verificada |
| T053 replay | verificada |
| T054 repetición/alterado | verificada |
| T055 API | verificada |
| T056 panel | verificada |
| T057 regresión | verificada (756 + 210 pasan según evidencia; verify_stack 14/16 ajeno) |
| T058 evidencia/CODEMAP | verificada (README SC-001..007 y CODEMAP correctos) |
Hallazgos bloqueantes/importantes: ninguno. Menor (no listado salvo esto): T052-T058 siguen sin [x] en tasks.md; lo marca quien corresponda.
