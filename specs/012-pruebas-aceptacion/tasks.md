# Tareas: Pruebas de aceptación (012)

**Entrada**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md).
**Numeración**: continúa desde T093 (`mediciones-costes`). 24 tareas activas en 5 bloques. Sin fuzz ni exhaustividad: un caso por comportamiento.
**IDs**: I1 a I11 son las pruebas 1 a 11 de la tabla I del checklist; I-resumen es el entregable 8. No se marca el checklist.
**Comando base** `T`: `docker compose --profile test run --rm tests pytest` (en Git Bash de Windows, `MSYS_NO_PATHCONV=1`). `AC` = `docs/evidencias/pruebas/`.
**Regla de aislamiento**: todo dato inyectado es `synthetic-acc-*` con `is_synthetic = true` y solo en `TempDatabase` (o `replay`); nunca en `live` real (FR-005).

## Bloque 1: pruebas puente consumidor a API (nuevo archivo `tests/integration/test_acceptance_api.py`)

Dependencias: ninguna entre ellas; T094 crea el archivo (fixtures y funciones auxiliares), las demás lo amplían.

- [x] **T094** Prueba 1. `test_new_event_is_one_current_row_visible_in_api_and_stats`: un mensaje nuevo por `process_message`; SQL con 1 fila en `current_event` para su `event_id`; `/api/eventos` lo lista y `/api/estadisticas` suma 1 al total. Prueba: `T tests/integration/test_acceptance_api.py -q -k new_event` pasa. IDs: I1, FR-004, FR-005, SC-003.
- [x] **T095** Prueba 3. `test_later_version_changes_current_and_aggregates`: versión inicial y otra con `updated` posterior y otro país y otra hora; la API muestra los datos nuevos, el recuento por país y por hora cambia, y `event_version` conserva ambas. Prueba: `-k later_version`. IDs: I3, FR-004, SC-003.
- [x] **T096** Prueba 4. `test_late_older_version_keeps_current_and_api_unchanged`: versión reciente y luego otra con `updated` menor; la API y las estadísticas son idénticas antes y después, y la tardía queda en el historial. Prueba: `-k late_older`. IDs: I4, FR-004, SC-003.
- [x] **T097** Prueba 5. `test_null_magnitude_stays_null_in_db_and_api`: `mag` nula (sin pasar a 0); `mag IS NULL` en SQL, `null` en la API, `mag = 0` sin filas, y con `min_mag=0` el evento se cuenta como nulo según el contrato `api.md`. Prueba: `-k null_magnitude`. IDs: I5, FR-004, FR-005, SC-003.
- [x] **T098** Prueba 7. `test_sea_event_has_no_country_and_is_counted`: coordenadas en el mar (localizador sin país); `country_id` NULL, sin cuarentena, `country_id=none` en la API lo devuelve, y entra en el total y en el recuento por hora de `/api/estadisticas`. Prueba: `-k sea_event`. IDs: I7, FR-004, SC-003.

**Punto de control B1**: `T tests/integration/test_acceptance_api.py -q` con 5 pruebas en verde; salida guardada en T100.

## Bloque 2: ejecución, huella de `live` y capturas

Dependencias: B1 completo para T100.

- [x] **T099** Huella inicial de `live` real con SQL de solo lectura (recuento de sintéticos, de `current_event` y md5 de los sintéticos, según [data-model.md](data-model.md)). Prueba: `AC/00_live_antes.txt` existe y tiene la fecha. IDs: FR-006, SC-003.
- [x] **T100** Ejecutar y guardar las pruebas 1 a 4: T094 a T096, `test_idempotence.py`, `test_producer_cycles.py`, `test_faq12.py`. Salidas en `AC/01-04_pytest.txt`. Prueba: 0 fallos, comando y fecha en cabecera. IDs: I1, I2, I3, I4, FR-001, FR-002, FR-004.
- [x] **T101** Ejecutar y guardar las pruebas 5 a 8: T097, T098, `test_nulls_times.py`, `test_api_events.py`, `test_quarantine.py`, `test_geography.py`, `test_restart_crash.py`. Salidas en `AC/05-08_pytest.txt`. Prueba: 0 fallos. IDs: I5, I6, I7, I8, FR-004.
- [x] **T102** Ejecutar y guardar la prueba 11: `test_replay_consumer.py` y `test_api_replay_real.py` (22 / 24 / 0 en `replay`, nada en `live`). Salida en `AC/11_pytest.txt`. Prueba: 0 fallos. IDs: I11, FR-004, SC-003.
- [x] **T103** *(Plantillas hechas; capturas reales pendientes del alumno.)* Capturas 1, 3 y 7 sobre `https://observatorio.ssamuelfernandez.net/` con navegador (sin cuentas): 1, un evento real reciente en mapa y análisis; 7, filtro «Sin país asignado» con datos reales; 3 (versión posterior): decidido: sus datos son sintéticos y viven en TempDatabase, y no se toca la base real para mostrarlos, así que el panel público no puede mostrarlos; la captura 3 es siempre plantilla con huecos (`AC/03_captura_pendiente.md`), que dice explícitamente «datos sintéticos (TempDatabase), no visibles en el panel público; evidencia principal: SQL de T095». Cada captura en `AC/` con fecha, URL y origen (1 y 7 «datos reales»). Sin herramienta: plantilla `.md` con huecos (`AC/01_captura_pendiente.md`, `AC/07_captura_pendiente.md`). Prueba: archivos existen y declaran el origen. IDs: I1, I3, I7, FR-010, SC-005.
- [x] **T104** *(Plantilla hecha; captura real pendiente del alumno.)* Captura 5 (ND): panel local en modo mock (sintético, con la etiqueta visible) mostrando una magnitud nula como ND; sin herramienta, plantilla (`AC/05_captura_pendiente.md`). No se inyecta nada en la base real. Prueba: archivo existe, declara «datos sintéticos (mock)». IDs: I5, FR-010, SC-005.

**Punto de control B2**: tres salidas de pytest sin fallos, huella inicial guardada, capturas o plantillas.

## Bloque 3: pruebas 9 y 10 (pendientes del alumno)

Dependencias: independiente de B1 y B2; T108 es independiente de T105 a T107.

- [x] **T105** Revisión del código del panel con archivo y línea: `useObservatory.ts` (`refetchInterval`, `retry: false`, `keepPreviousData`), `StatusBanners.tsx` líneas 82 a 89, `main.tsx` línea 9, `frontend/public/config.json`; y `grep` de `refetchIntervalInBackground` en `frontend/src` (sin resultados). Guardar `AC/09-10_revision_codigo.txt` con las citas y los huecos (60 s más timeout; pestaña oculta; sin refresco al volver a la pestaña; T036 probó la API local, no el túnel). Prueba: las líneas citadas coinciden con el código leído. IDs: I9, I10, G9, FR-008, SC-004.
- [x] **T106** *(Ficha y plantilla hechas; la prueba 9 queda pendiente del alumno.)* Ficha `AC/09-cierre-tunel.md`: procedimiento paso a paso, esperado, plantilla con huecos (URL, horas, dos capturas o clip), estado «Pendiente del alumno». Prueba: tiene los 6 apartados y ninguna afirmación de «verificada». IDs: I9, G9, FR-007, FR-009, SC-004.
- [x] **T107** *(Ficha y plantilla hechas; la prueba 10 queda pendiente del alumno.)* Ficha `AC/10-reapertura-tunel.md`: igual que T106 para la reapertura y la recuperación sin recargar. Prueba: ídem. IDs: I10, G9, FR-007, FR-009, SC-004.
- [x] **T108** Corregir solo el texto de estado en `docs/evidencias/despliegue-tunel/README.md` (línea 17), `prueba-09_cierre-tunel.md` y `prueba-10_reapertura-tunel.md` (línea 3): «pendiente de la demostración del alumno». Prueba: `grep -in "verifica en vivo" docs/evidencias/despliegue-tunel/` no devuelve coincidencias sobre 9 y 10. IDs: I9, I10, FR-012, SC-004.

**Punto de control B3**: dos fichas con plantilla, revisión de código guardada, 0 afirmaciones de «verificada» sin captura del alumno.

## Bloque 4: fichas de las pruebas de datos y resumen

Dependencias: T100 a T104 para las observadas; T105 a T108 para el resumen.

- [x] **T109** Fichas `01-evento-nuevo`, `02-reenvio`, `03-version-posterior`, `04-version-tardia` en `AC/`, con los 6 apartados, enlaces a las evidencias de [research.md](research.md) y al resultado de T100. Estado: 1 «Observada» (parte real) y «Observada (sintética)» (API); 2 a 4 según origen. La ficha 03 enlaza `AC/03_captura_pendiente.md` (plantilla, datos sintéticos). Prueba: cada enlace existe (`ls`). IDs: I1, I2, I3, I4, FR-001, FR-002, FR-003, SC-001.
- [x] **T110** Fichas `05-magnitud-nula`, `06-coordenadas-invalidas`, `07-evento-maritimo`, `08-reinicio-consumidor`. La 5 declara que no hay nulos reales y que ND sale del mock; la 7 usa datos reales en el panel; la 8 enlaza `prueba8_reinicio.log/.out` (real). Prueba: enlaces existen. IDs: I5, I6, I7, I8, FR-001, FR-002, FR-003, SC-001.
- [x] **T111** Ficha `11-reproduccion-historica`: procedimiento de replay, 26 mensajes a 22 / 24 / 0, huella de `live`, enlaza `docs/evidencias/replay/README.md` y las capturas T056. Prueba: enlaces existen. IDs: I11, FR-001, FR-002, FR-003, SC-001.
- [x] **T112** `AC/README.md`: tabla de 11 filas (esperado, observado, evidencia, cómo repetir, estado), secciones «Huecos del panel en 9 y 10» y «Aislamiento de live». Prueba: 11 filas; estados solo Observada, Observada (sintética) o Pendiente del alumno. IDs: I-resumen, FR-011, SC-002, SC-004.
- [x] **T113** Comprobar con `ls` el 100 % de los enlaces de `AC/README.md` y de las fichas; guardar el resultado en `AC/00_enlaces.txt`. Prueba: 0 enlaces rotos. IDs: I-resumen, FR-011, SC-002.

**Punto de control B4**: 11 fichas, resumen y enlaces comprobados.

## Bloque 5: cierre (constitución §16)

Dependencias: B1 a B4 completos; orden T114, T115, T116, T117.

- [x] **T114** Ejecutar la suite completa: `T -m "not integration" -q` (en el servicio `tests`) y `T -m integration -q`. Salidas en `AC/suite_unitarias.txt` y `AC/suite_integracion.txt`. Prueba: 0 fallos. IDs: FR-014, SC-006.
- [x] **T115** Restaurar las evidencias reescritas por la suite: `git checkout -- docs/evidencias/consumidor-idempotente`. Prueba: `git status --short docs/evidencias/consumidor-idempotente` sin cambios. IDs: FR-014, SC-006.
- [x] **T116** Huella final de `live` y comparación con T099: `AC/00_live_despues.txt` con `n_sinteticos` y md5 iguales; lo resumido en la sección «Aislamiento de live» de `AC/README.md`. Prueba: sin diferencias. IDs: FR-006, SC-003.
- [x] **T117** Actualizar `CODEMAP.md` (fila de `tests/integration/test_acceptance_api.py` y de `docs/evidencias/pruebas/`, con rutas comprobadas con `ls`) y comprobar con `git status` que no cambian contratos, `docs/enunciado/`, `sql/001_schema.sql`, constitución ni checklist. Prueba: `git status` solo lista rutas permitidas; sin commit. IDs: FR-013, FR-014, SC-006.

## Orden y paralelismo

B1 (T094 primero y T095 a T098 después, secuenciales porque comparten archivo) y B3 pueden ir en paralelo; B2 sigue a B1 (T099 puede ir antes); B4 sigue a B2 y B3; B5 al final.

## Cobertura

| Requisito | Tareas |
|---|---|
| I1 | T094, T100, T103, T109 |
| I2 | T100, T109 |
| I3 | T095, T100, T103, T109 |
| I4 | T096, T100, T109 |
| I5 | T097, T101, T104, T110 |
| I6 | T101, T110 |
| I7 | T098, T101, T103, T110 |
| I8 | T101, T110 |
| I9, I10, G9 | T105 a T108 |
| I11 | T102, T111 |
| I-resumen | T112, T113 |
| FR-001 a FR-003 | T109 a T111 |
| FR-004, FR-005 | T094 a T098, T100 a T102 |
| FR-006 | T099, T116 |
| FR-007 a FR-009 | T105 a T107 |
| FR-010 | T103, T104 |
| FR-011 | T112, T113 |
| FR-012 | T108 |
| FR-013, FR-014 | T114 a T117 |
| SC-001 a SC-006 | T109 a T113, T116, T117, T103 a T105 |
