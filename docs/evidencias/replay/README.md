# Evidencias de la feature `replay` (009)

Recorrido real con contenedores el 2026-11-12. Los recuentos esperados son N = 20: 26 mensajes, 22 / 24 / 0.

## Veredicto SC-001 a SC-007

| SC | Veredicto | Archivos |
|---|---|---|
| SC-001 (26 mensajes; 22 / 24 / 0; 2 reenvíos, 1 posterior, 1 tardía; E1 con `updated` 10:09 y 3 versiones) | Cumple | `T053_despues.out`, `T053_despues_detalle.out`, `T053_consumer.log`, `T053_replay.log` |
| SC-002 (`live` idéntico con el productor live parado: 211 / 211 / 0, misma huella md5) | Cumple | `T052_antes.out`, `T053_despues.out`, `T054_repeticion.out` |
| SC-003 (API `mode=replay`: `metadata.mode = "replay"`, total 22, `time` originales; sin `mode`, ningún evento de replay) | Cumple | `T055_comprobacion.txt`, `T055_eventos_replay.json`, `T055_eventos_sin_mode.json`, `T055_estadisticas_replay.json` |
| SC-004 (`replay_at` no nulo, `source = replay_demo`, `replay_at` crecientes; `live` con `replay_at` nulo) | Cumple | `T053_replay_at_base.txt`, `T053_despues_detalle.out`, `T049_integracion.txt` |
| SC-005 (panel: banner «REPRODUCCIÓN» y 22 eventos; «En vivo» sin banner ni eventos de replay) | Cumple | `T056_panel.md`, `T056_reproduccion.png`, `T056_en_vivo.png`, `T056_texto_reproduccion.txt` |
| SC-006 (repetir deja 22 / 24 / 0 y los mismos `replay_at`) | Cumple | `T054_repeticion.log`, `T054_repeticion.out`; archivo alterado: `T054_archivo_alterado.out` |
| SC-007 (README con recuentos reales; replay en 51 s, menos de 90 s) | Cumple | `T053_replay_at_base.txt` (`duracion_s=51`), `T057_*.txt`; README, sección «Replay» |

## Índice de archivos

- Bloque 1 a 3 (pruebas): `T041_pytest.txt`, `T042_pytest.txt`, `T043_pytest.txt`, `T044_T045_pytest.txt`, `T046_pytest.txt`, `T047_compose_env.txt`, `T048_integracion.txt`, `T049_integracion.txt`, `bloque1_pytest.txt`, `bloque2_pytest.txt`, `bloque3_unitarias_completas.txt`, `bloque3_integracion_completa.txt`.
- Bloque 5 (contenedores): `T052_antes.out`, `T053_*`, `T054_*`, `T055_*`, `T056_*`.
- Regresión (T057): `T057_unitarias.txt` (756 pasan, 210 deseleccionadas; en el servicio `tests`, porque el equipo no tiene Python 3.12), `T057_integracion.txt` (210 pasan en 112 s), `T057_check_env.txt` (en verde), `T057_verify_stack.txt` (14 de 16).

## Nota sobre T057_verify_stack

Los 2 fallos («Solo la API publica un puerto» y «postgres no tiene puertos enlazados») vienen del `compose.override.yaml` local (ignorado por Git), que publica PostgreSQL en 127.0.0.1:5433 para un cliente gráfico. No tienen relación con el replay; sin el override pasarían.

## Cobertura de IDs del checklist

| ID | Evidencia |
|---|---|
| J1, J2 | `T042_pytest.txt` (orden por fecha), `T053_replay_at_base.txt` (tiempo original y `replay_at`) |
| J3 | `T048_integracion.txt`, `T053_despues.out` (topic `earthquakes.replay`, esquema `replay`; `live` intacto) |
| J4, G10 | `T056_panel.md`, `T056_reproduccion.png` |
| J5 | `T046_pytest.txt`, `T048_integracion.txt`: el consumidor procesa los mensajes de replay con el mismo `pipeline`/`common` (`consumer/pipeline.py` sin cambios) |
| J6 | `T053_consumer.log`, `T054_repeticion.out` |
| J7, F12 | `T055_comprobacion.txt`, `T049_integracion.txt` |
| J8 | README raíz «Replay», `docs/borradores/replay.md` |
| G12 (`metadata.mode`) | `T055_eventos_replay.json`, `T056_reproduccion.png` (solo este campo; los demás campos de G12 son de `panel-base-mock`) |
| Prueba 11 | `T052_antes.out`, `T053_despues.out`, `T054_*`, `T056_*` |
