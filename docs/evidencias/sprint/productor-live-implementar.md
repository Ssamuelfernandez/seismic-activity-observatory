# Resumen fase `implementar` — productor-live (rama 004-productor-live)

## a) Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| uv no funciona en el entorno | pytest con `.venv/Scripts/python` | mismo pytest del proyecto | no |
| Cambio transitorio en producer/loop.py en bloque 1 | mínimo, reescrito en T011 | quitar constantes de config | no |
| `grep synthetic producer/` no vacío | solo columna `is_synthetic`; criterio = sin lógica sintética | no renombrar | sí |
| `.env` local (ignorado) | añadidas 4 líneas no secretas de .env.example | necesario para compose | no |
| GRANT en volumen existente | reaplicado con psql, sin down -v | quickstart §0 | sí |
| publisher.py: key `str|None` | acks=all e idempotencia intactos | eventos sin id | sí |
| B2, B11, B12 no marcadas | evidencia = sección en memoria; solo hay borrador | decisión del alumno | sí |
| Verificación de bloques 4 y 5 juntos | un solo verificador | bloque 4 es solo documentación | no |

## b) Preguntas para el alumno
Marcar B2/B11/B12 cuando pase el borrador a la memoria. Prueba 1 queda para `pruebas-aceptacion` (API/mapa/análisis).

## c) Hallazgos
0 bloqueantes/importantes en los 5 bloques. Menores: T010 sin TDD «falla antes»; 3 rutas futuras en CODEMAP apuntan a archivos aún inexistentes (preexistente); config.md muestra "18 variables" (recuento antiguo).

## d) Tareas
22/22 verificadas. Evidencia clave (USGS real, 2026-11-04): ciclo1 published=191, ciclo2 published=1 skipped=191, ciclo3 published=0 skipped=192; tras kill+up published=0 skipped=192; evento nuevo real ok2026vqse (current_event 192→193, event_version 196→198). Tests: 487 unitarias, 53 integración, verify_stack 16/16. Contratos intactos. Límite: el reenvío por corte ack/marca solo se probó en test, no en vivo.

## e) Qué debe comprobar el alumno
docs/evidencias/productor-live/, docs/evidencias/subagentes/verificador-productor-live-bloque*.md, README sección «Productor en vivo», ingest_store/cycle.

Fase terminada.
