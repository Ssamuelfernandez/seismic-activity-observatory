# Guía de validación: Pruebas de aceptación (012)

Prerrequisitos: stack levantado (`docker compose up -d`), imagen `tests` construida, `.env` con las contraseñas. En Git Bash de Windows, prefija `MSYS_NO_PATHCONV=1`. Contratos de referencia: `specs/001-contratos-y-modelo/contracts/` (no se repiten aquí). Abreviatura: `T = docker compose --profile test run --rm tests pytest`.

## 1. Huella de `live` antes

Consulta SQL de solo lectura (`docker compose exec postgres psql ...`): `count(*) FILTER (WHERE is_synthetic)`, `count(*)` y md5 de los sintéticos en `live.current_event`. Guardar en `docs/evidencias/pruebas/00_live_antes.txt`.

## 2. Pruebas 1 a 8 y 11 (base temporal o esquema `replay`)

| Prueba | Comando |
|---|---|
| 1, 3, 4, 5, 7 (consumidor a API) | `T tests/integration/test_acceptance_api.py -q` (nombres en `tasks.md`, T094 a T098) |
| 2 | `T tests/integration/test_idempotence.py tests/integration/test_producer_cycles.py -q` |
| 3 y 4 (BD) | `T tests/integration/test_faq12.py -q` |
| 5 (BD y API) | `T tests/integration/test_nulls_times.py tests/integration/test_api_events.py -q` |
| 6 | `T tests/integration/test_quarantine.py -q` |
| 7 (BD) | `T tests/integration/test_geography.py -q` |
| 8 | `T tests/integration/test_restart_crash.py -q` |
| 11 | `T tests/integration/test_replay_consumer.py tests/integration/test_api_replay_real.py -q` |

Esperado: todas pasan; 0 filas sintéticas nuevas en `live` real.

## 3. Pruebas 9 y 10 (las hace el alumno)

Seguir `docs/evidencias/pruebas/09-cierre-tunel.md` y `10-reapertura-tunel.md`: panel público abierto y pestaña visible, cerrar `cloudflared`, esperar hasta 60 s más el timeout, ver «Datos antiguos» con la hora de la última lectura; reabrir y ver que el aviso desaparece sin recargar. Rellenar horas y capturas.

## 4. Cierre

Repetir la huella (`00_live_despues.txt`) y comparar. Suite completa (`T -m "not integration"` en el servicio `tests` y `T -m integration`), después `git checkout -- docs/evidencias/consumidor-idempotente`. Comprobar con `ls` los enlaces de `docs/evidencias/pruebas/README.md`.
