# Verificación bloque 5 (T091–T093), mediciones-costes

| Tarea | Veredicto | Prueba |
|---|---|---|
| T091 | VERIFICADA | Los comandos de procedimiento.md coinciden con quickstart.md (líneas 30 y 38) y T087_corrida.txt. Tiempo 117 s y 102 mediciones coinciden con la corrida. No ejecuté el ensayo porque sobrescribe tablas definitivas. |
| T092 | VERIFICADA | Script propio: las 50 cifras del borrador están en la evidencia (0 sin respaldo). SINTÉTICO, SUPUESTO y REAL bien puestos. Modelo y potencia del anfitrión figuran como PENDIENTE (alumno), sin cifras inventadas. README.md solo ganó un párrafo con el enlace, que resuelve. docs/memoria.md intacto. |
| T093 | VERIFICADA | Sin Docker: 832 passed. Servicio tests: 227 passed y 1 error de recogida. Existen todas las rutas de CODEMAP (los "MISSING" de mi grep eran fragmentos de texto). |

Comprobaciones transversales
- Compose tiene 5 servicios, todos healthy.
- `git diff --stat` de specs/001, sql, docs/enunciado, pyproject.toml y uv.lock está vacío.
- `to_regnamespace('bench')` es NULL en la base real (18636 filas en current_event).
- git status no muestra .env ni archivos grandes.
- El error de recogida en tests/common/test_api_config.py es PREEXISTENTE y ajeno a la feature. `load_cors_origins` llegó con la feature 010 (commit 599b0c1, 12-nov 19:34). La imagen `tests` es de 12-nov 17:45, anterior. common/api_config.py no tiene cambios locales.
- README de evidencias: los veredictos SC-001..SC-007 son honestos. SC-007 "Parcial" es acertado: falta repetir desde un clon limpio.

Hallazgos bloqueantes o importantes: ninguno.
Límite conocido: la imagen `tests` está desactualizada. Reconstruirla con `--build` queda a decisión del alumno.
