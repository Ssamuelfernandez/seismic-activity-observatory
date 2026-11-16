# Auditoría de requisitos [OBL] (revision-final, T118)

> **Estado actualizado a hoy (2026-11-16).** Este documento es el histórico de la fecha indicada y no se reescribe. Desde entonces: B2 cumple (memoria §2.1), B11 cumple (memoria §10, que ya no está vacía) y C14 cumple (memoria §4.4, con las consultas en `docs/evidencias/revision-final/calidad-live.md`). M3 sigue parcial porque el clon limpio no se repite (A2 también parcial, decisión aceptada del alumno); el README ya tiene el marcador del vídeo, el recorrido de un evento, la decisión propia y la tabla rúbrica→evidencia. Recuento actualizado: 93 [OBL] = 86 cumple, 4 parcial (A2, G9, H3 y M3) y 3 no (H4, H5 y M4). Los motivos de G9, H3, H4 y H5 siguen en el texto de abajo; el alumno aceptó H3 con la captura existente y cubrirá G9 y H4 en el vídeo, y las filas de abajo no se han modificado.

Fecha: 2026-11-14. Rama `013-revision-final`. Solo lectura: no se ha corregido nada ni se ha tocado el checklist (`docs/planificacion/01-checklist-requisitos.md`). Fuente de los requisitos: ese checklist, bloques A a M, filas marcadas [OBL] (93). Fuente de las evidencias: los README de `docs/evidencias/`, la trazabilidad §7 de `docs/planificacion/03-procedimiento-ejecucion.md` y la comprobación directa de cada ruta (`ls` y `git ls-files`).

Criterio: **cumple** = la evidencia citada existe, está versionada y no es una plantilla sin rellenar; **parcial** = parte comprobada y parte pendiente; **no** = sin evidencia. La columna «Evidencia» no repite todo lo que hay: da la ruta principal. «Responsable»: «alumno» (acción humana, o texto fuera del alcance de 013), «013 (T126)» (hueco de texto de `README.md`) o una feature.

## [OBL] sin evidencia o con evidencia incompleta

Recuento: 93 [OBL] = 83 cumple, 7 parcial, 3 no (tras T119/T120, T126 y las capturas del 2026-11-15).

Sin evidencia (**no**): H4 (equipo, contenedores y túnel encendidos en la demo), H5 (vídeo de 5 min), M4 (acceso del profesor al repositorio).

Con evidencia incompleta (**parcial**): A2 (clon limpio solo probado en la feature 002), B2 (respuesta, errores y latencia del feed: solo en el borrador), B11 (limitación solo en el README, memoria §10 vacía), C14 (análisis hecho en `calidad-live.md`; falta pasarlo a la memoria), G9 (prueba real con túnel pendiente), H3 (captura del panel de Cloudflare sin el destino `http://localhost:8000`), M3 (sin repetir desde un clon limpio).

Pendientes humanos relacionados con la tabla I (no [OBL] en el checklist, ver la segunda tabla): prueba 9 (parcial: falta demostrar la última lectura conservada) y prueba 10 (reapertura, sin captura).

## Tabla de [OBL]

| ID | Requisito | Evidencia (ruta) | Estado | Hueco | Responsable |
|---|---|---|---|---|---|
| A1 | 5 servicios separados en Compose, healthy | `docs/evidencias/infra-compose/verificacion_completa.txt`; `compose.yaml` | cumple | — | — |
| A2 | `docker compose up --build -d` desde un clon limpio | `docs/evidencias/infra-compose/clon_limpio.txt`; `docs/evidencias/infra-compose/clon_limpio_verify.txt` | parcial | El clon limpio se probó en la feature 002 (2026-11-03), antes de productor, API y panel. No se ha repetido con el estado final (T131 diferido; lo recoge `docs/evidencias/mediciones/README.md` SC-007) | alumno |
| A3 | Imagen reproducible por servicio Python, dependencias fijadas | `Dockerfile`; `uv.lock`; `docs/evidencias/infra-compose/python_en_contenedor.txt` | cumple | — | — |
| A4 | Healthchecks y reintentos | `docs/evidencias/infra-compose/reintentos_y_configuracion.txt`; `docs/evidencias/infra-compose/arranque_sin_postgres.txt`; `docs/evidencias/infra-compose/latido_caduca.txt` | cumple | — | — |
| A5 | Volúmenes persistentes: reiniciar no pierde datos | `docs/evidencias/infra-compose/verificacion_completa.txt`; `docs/evidencias/historico-2025/verificacion_tras_reinicio.out` | cumple | — | — |
| A6 | Retención limitada de Kafka, configurada y documentada | `docs/evidencias/infra-compose/verificacion_completa.txt` (retention.ms=604800000); `README.md` («Retención de Kafka») | cumple | — | — |
| A7 | Nombres de servicio en vez de `localhost`; listeners documentados | `docs/evidencias/infra-compose/config_por_entorno.txt`; `README.md` («Listeners de Kafka») | cumple | — | — |
| A8 | Solo la API se expone | `docs/evidencias/despliegue-tunel/T067_puertos_secretos.txt`; `docs/evidencias/infra-compose/verificacion_completa.txt` | cumple | — | — |
| A9 | Uvicorn en `0.0.0.0:8000` dentro del contenedor | `compose.yaml` (línea 155); `docs/evidencias/infra-compose/verificacion_completa.txt` | cumple | — | — |
| A10 | `.env.example` sin credenciales reales y coherente con el código | `docs/evidencias/infra-compose/check_env_example.txt`; `docs/evidencias/despliegue-tunel/T071_check_env_example.txt`; `.env.example` | cumple | — | — |
| A11 | Dependencias fijadas | `pyproject.toml`; `uv.lock`; `frontend/package-lock.json` | cumple | — | — |
| B1 | Productor consulta el feed cada ~60 s | `docs/evidencias/productor-live/ciclo1.log` | cumple | — | — |
| B2 | Documentar respuesta, tipos, unidades, opcionales, frecuencia, errores y latencia | `docs/borradores/productor-live.md`; `docs/memoria.md` (§2, tipos y unidades) | parcial | Opcionales, frecuencia, errores y latencia (223 ms) solo están en el borrador; la memoria §2 solo tiene el diccionario y el `README.md` solo menciona los límites | 013 (T126) |
| B3 | Filtrar `type == earthquake` y guardar el motivo de exclusión | `docs/evidencias/productor-live/ciclo1_consultas.out` (`live.exclusion`: explosion 7, quarry blast 5) | cumple | — | — |
| B4 | Guardar el GeoJSON original y metadatos de extracción antes de transformar | `docs/evidencias/productor-live/ciclo1_consultas.out` (`raw_response`, `ingest_run`) | cumple | — | — |
| B5 | Retención de copias idénticas y registro de consultas | `README.md` («Política de raw_response»); `docs/evidencias/productor-live/pytest_integracion.txt` | cumple | — | — |
| B6 | `id` + `updated` con estado persistente (`ingest_state`) | `docs/evidencias/productor-live/reinicio.log`; `docs/evidencias/productor-live/prueba2_reenvio.out` | cumple | — | — |
| B7 | Clave Kafka = id del evento | `docs/evidencias/productor-live/bloque1_pytest.txt`; `docs/evidencias/productor-live/prueba1_evento_nuevo.out` | cumple | — | — |
| B8 | Mensaje con `source`, `ingested_at`, `mode` y evento original | `docs/evidencias/productor-live/bloque1_pytest.txt`; `docs/evidencias/infra-compose/mensaje_crudo.txt`; `specs/001-contratos-y-modelo/contracts/kafka-message.md` | cumple | — | — |
| B9 | Ack de Kafka antes de marcar publicado | `docs/evidencias/productor-live/bloque2_pytest_unitarias.txt`; `docs/evidencias/productor-live/bloque3_unitarias_completas.txt` | cumple | — | — |
| B10 | Timeout, 429/5xx, backoff, JSON inválido sin borrar el estado | `docs/evidencias/productor-live/bloque3_T012_integracion_failures.txt` | cumple | — | — |
| B11 | Limitación: salir de la ventana no es eliminado | `README.md` («Productor en vivo», límites conocidos); `docs/borradores/productor-live.md` | parcial | El párrafo está en el `README.md`; la memoria §10 (Limitaciones) está vacía y el checklist pide el párrafo en memoria | 013 (T126) |
| B12 | Recuperar el hueco tras una parada de más de 24 h | `README.md` («Hueco de más de 24 h»); `docs/evidencias/historico-2025/hueco_ensayo.out` | cumple | — | — |
| B13 | Histórico 2025, M≥4, por meses, sin truncar en silencio | `docs/evidencias/historico-2025/descarga_2025.log`; `data/historical/manifest.json` | cumple | — | — |
| B14 | Deduplicar eventos compartidos entre intervalos | `docs/evidencias/historico-2025/descarga_2025.log`; `docs/evidencias/historico-2025/historico_recarga_huella.out` | cumple | — | — |
| B15 | Guardar consultas, fecha y nº de registros; descargar una vez | `data/historical/manifest.json`; `docs/evidencias/historico-2025/descarga_2025_segunda.log` | cumple | — | — |
| B16 | Histórico con las mismas reglas que el live | `docs/evidencias/historico-2025/historico_reglas.out`; `tests/historical/test_no_duplicated_logic.py` | cumple | — | — |
| B17 | El histórico no se pierde al reiniciar; carga reproducible | `docs/evidencias/historico-2025/verificacion_tras_reinicio.out`; `README.md` («Histórico 2025») | cumple | — | — |
| C1 | Validar, limpiar, enriquecer y escribir; reglas listadas | `docs/memoria.md` (§4.1); `docs/evidencias/consumidor-idempotente/pytest_unitarias.txt` | cumple | — | — |
| C2 | Transacción en PG y después commit del offset | `docs/evidencias/consumidor-idempotente/bloque4_prueba8_corte_simulado.out`; `docs/evidencias/consumidor-idempotente/prueba8_reinicio.out` | cumple | — | — |
| C3 | Al menos una vez más escritura idempotente | `docs/evidencias/consumidor-idempotente/bloque3_prueba2_reenvio.out` | cumple | — | — |
| C4 | Estado actual solo con `updated` más reciente | `docs/evidencias/consumidor-idempotente/bloque3_prueba3_4_versiones.out` | cumple | — | — |
| C5 | Cuarentena duradera con motivo y referencia | `docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out` | cumple | — | — |
| C6 | No rellenar nulos con 0; negativos no se rechazan | `docs/evidencias/geografia-pais/geografia_prueba5.out`; `docs/memoria.md` (§4.1) | cumple | — | — |
| C7 | Fechas a UTC conservando el original en ms | `tests/integration/test_nulls_times.py`; `docs/evidencias/pruebas/suite_integracion.txt` | cumple | — | — |
| C8 | Registrar transformaciones y a cuántos registros afectan | `docs/evidencias/consumidor-idempotente/bloque4_contadores_integracion.out` | cumple | — | — |
| C9 | País por punto en polígono, no por `place` | `docs/evidencias/geografia-pais/geografia_pruebas5_7_kafka.out`; `docs/evidencias/geografia-pais/geo_real_day.out` | cumple | — | — |
| C10 | Unicidad de `ADM0_A3` antes de usarlo como ID | `docs/evidencias/geografia-pais/geografia_catalogo.out` (177 países); `docs/evidencias/geografia-pais/geografia_catalogo_carga.out` | cumple | — | — |
| C11 | Regla para puntos en frontera y múltiples coincidencias | `README.md` («País por geometría»); `docs/evidencias/geografia-pais/T005_pytest_geo_completo.txt` | cumple | — | — |
| C12 | «Sin país asignado» se conserva y permanece en el análisis | `docs/evidencias/geografia-pais/geografia_prueba7.out`; `docs/evidencias/geografia-pais/geo_real_day.out` | cumple | — | — |
| C13 | Casos de prueba artificiales separados e identificados | `docs/evidencias/pruebas/00_live_despues.txt` (0 sintéticos en `live`); `docs/evidencias/api/recorrido_11_paginacion_y_sinteticos.txt` | cumple | — | — |
| C14 | Apartado de calidad con consultas, antes/después, decisiones y ejemplos | `docs/memoria.md` (§4.1 a §4.3, solo reglas) | parcial | Las reglas y la cuarentena están; falta el análisis de las 6 dimensiones (completitud, unicidad, validez, consistencia, actualidad, exactitud) con consultas, resultados y denominador. Es el hueco que `docs/rubrica-y-guia-video.md` §2 señala como el mayor. Alineado con FR-003/T126; si el análisis sale del alcance de 013, es decisión del alumno | 013 (T126) |
| E1 | Modelo conceptual, lógico y físico | `docs/memoria.md` (§5.1 a §5.3); `docs/evidencias/contratos-y-modelo/prueba_esquema_001_salida.txt` | cumple | — | — |
| E2 | Grano, claves, relaciones e índices por tabla | `docs/memoria.md` (§5.2 y §5.3) | cumple | — | — |
| E4 | Integrar terremotos con el catálogo de países | `docs/memoria.md` (§5.2); `docs/evidencias/api/recorrido_03_country_jpn.txt` | cumple | — | — |
| E5 | SQL de creación de tablas e índices enlazado desde la memoria | `sql/001_schema.sql`; `sql/002_roles.sql`; `docs/memoria.md` (§5) | cumple | — | — |
| E6 | Índices justificados por consulta y medidos antes/después | `docs/evidencias/mediciones/indices.md`; `docs/evidencias/mediciones/tablas.md` | cumple | — | — |
| F1 | `GET /api/eventos` conforme al contrato | `docs/evidencias/api/recorrido_01_eventos_sin_parametros.txt`; `docs/evidencias/contratos-y-modelo/revision_api_vs_contrato.md` | cumple | — | — |
| F2 | `metadata` con `generated`, `last_ingestion`, `mode`, `count`, `truncated` | `docs/evidencias/api/recorrido_01_eventos_sin_parametros.txt`; `docs/evidencias/api/T009_pytest_api_events.txt` | cumple | — | — |
| F3 | Filtros `start`, `end`, `min_mag`, `country_id` | `docs/evidencias/api/recorrido_02_min_mag.txt`; `docs/evidencias/api/recorrido_03_country_jpn.txt`; `docs/evidencias/api/recorrido_05_dia_2025.txt` | cumple | — | — |
| F4 | `null` y nunca NaN/Infinity | `docs/evidencias/api/T009_pytest_api_events.txt`; `docs/evidencias/api/recorrido_04_country_none.txt` | cumple | — | — |
| F5 | Truncado con total y paginación documentados | `docs/evidencias/api/recorrido_11_paginacion_y_sinteticos.txt`; `docs/evidencias/api/recorrido_01b_segunda_pagina.txt` | cumple | — | — |
| F6 | `GET /api/salud` | `docs/evidencias/api/recorrido_06_salud.txt` | cumple | — | — |
| F7 | `GET /api/estadisticas` con los mismos filtros que el mapa | `docs/evidencias/api/recorrido_08_estadisticas.txt`; `docs/evidencias/api/recorrido_09_estadisticas_filtros.txt`; `docs/evidencias/api/coherencia_real.txt` | cumple | — | — |
| F8 | Fallo de BD → error explícito, nunca «0 eventos» | `docs/evidencias/api/fallo_bd_503.txt`; `docs/evidencias/api/bloque4_database_down.out` | cumple | — | — |
| F9 | CORS: origen de Netlify y `localhost:4200`, GET y OPTIONS | `docs/evidencias/despliegue-tunel/T062_cors_curl.txt`; `docs/evidencias/despliegue-tunel/T060_cors.txt` | cumple | — | — |
| F10 | Sin rutas de administración ni secretos expuestos | `docs/evidencias/despliegue-tunel/exposicion.md`; `docs/evidencias/despliegue-tunel/T066_respuestas.txt` | cumple | — | — |
| G1 | El panel consulta nuestra API, no USGS | `docs/evidencias/panel-base-mock/contraste-mock-api.md`; `docs/evidencias/panel-base-mock/T034_curl_proxy_4300.txt`; `frontend/public/config.json` | cumple | Las comprobaciones visuales de `docs/evidencias/panel-base-mock/T034_T037_comprobaciones_pendientes.md` no se capturaron; la captura pública de H1 muestra datos reales | — |
| G2 | Globo: fronteras, tamaño ∝ magnitud, color ∝ profundidad, leyenda y ND | `docs/evidencias/pruebas/capturas/01_evento_nuevo.png`; `docs/evidencias/pruebas/capturas/05_magnitud_nula_nd.png`; `docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png` | cumple | Matiz: la ficha abierta es de un evento real (captura 1); el ND se ve en modo mock, **sintético** y etiquetado, porque no hay magnitudes nulas reales en `live` | — |
| G3 | Recuentos por país (incl. «Sin país asignado») y por hora UTC | `docs/evidencias/panel-base-mock/T035_tabla_filtros_totales.md`; `docs/evidencias/api/recorrido_08_estadisticas.txt` | cumple | — | — |
| G4 | Distribuciones de magnitud y profundidad con registros sin valor | `docs/evidencias/api/recorrido_08_estadisticas.txt`; `docs/evidencias/api/T014_pytest_api_stats.txt` | cumple | — | — |
| G5 | Comparación 24 h M≥4 frente a la media diaria de 2025, con aviso de periodo incompleto | `docs/evidencias/api/T016_pytest_api_comparison.txt`; `docs/evidencias/panel-base-mock/contraste-mock-api.md` (`recent_incomplete`) | cumple | — | — |
| G6 | Filtros coherentes entre mapa, tabla y gráficos | `docs/evidencias/panel-base-mock/T035_tabla_filtros_totales.md`; `docs/evidencias/api/T015_pytest_api_coherence.txt`; `frontend/src/store/filters.ts` | cumple | — | — |
| G7 | Estado del sistema: última ingesta, periodo y avisos | `docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png`; `docs/evidencias/panel-base-mock/T036_ciclo_refresco.txt` | cumple | — | — |
| G8 | Tabla consultable de eventos | `frontend/src/components/EventsTable.tsx`; `docs/evidencias/panel-base-mock/T037_render_estatico.txt` | cumple | — | — |
| G9 | Fallo de la API: aviso, última lectura identificada | `docs/evidencias/panel-base-mock/T036_curl_api_parada.txt`; `docs/evidencias/pruebas/09-10_revision_codigo.txt` | parcial | Probado con la API local parada y por revisión de código; no con el túnel real (pruebas 9 y 10 pendientes). Huecos del panel anotados en `docs/evidencias/pruebas/README.md` | alumno |
| G10 | Modo «REPRODUCCIÓN» etiquetado | `docs/evidencias/replay/T056_reproduccion.png`; `docs/evidencias/replay/T056_panel.md` | cumple | — | — |
| G13 | Netlify: `config.json` con la URL HTTPS del túnel antes de compilar | `docs/evidencias/despliegue-tunel/T065_build_dist.txt`; `docs/evidencias/despliegue-tunel/T063_netlify.txt`; `netlify.toml`; `docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png` | cumple | El despliegue real lo hizo el alumno a mano; la evidencia es la captura pública y las comprobaciones locales | — |
| H1 | Panel de Netlify accesible desde otro dispositivo | `docs/evidencias/despliegue-tunel/H1_movil_datos_moviles.jpg`; `docs/evidencias/despliegue-tunel/H1_movil.md` | cumple | Matiz: la URL sale recortada por la izquierda y la hora del móvil (8:24) no lleva fecha | — |
| H2 | Procedimiento de activación para la demo en el README | `README.md` («Túnel público y panel (Procedimiento de activación)»); `docs/evidencias/despliegue-tunel/T068_readme.txt` | cumple | — | — |
| H3 | Túnel HTTPS que expone solo `http://localhost:8000`; token fuera de Git | `docs/evidencias/despliegue-tunel/T067_puertos_secretos.txt`; `docs/evidencias/despliegue-tunel/2026-11-12_respuestas-publicas.txt` | parcial | El token no está en Git y el túnel responde en público, pero falta la captura de la configuración de `cloudflared` con `http://localhost:8000` como único destino (paso P1 de `docs/evidencias/despliegue-tunel/README.md`) | alumno |
| H4 | Equipo, contenedores y túnel encendidos durante la demo | (ninguna; es un estado que solo existe durante la demo) | no | Sin evidencia posible hasta la demo. `README.md` lista las comprobaciones previas | alumno |
| H5 | Vídeo de 5 min con recorrido de un evento y decisión propia en el README | (ninguna) | no | Vídeo sin grabar. `README.md` aún no tiene el marcador del enlace, el recorrido del evento ni la decisión propia (T126 añade el texto y el marcador «PENDIENTE: enlace de YouTube»; el vídeo es del alumno) | alumno |
| J1 | Reproducción acelerada ordenada por fecha | `docs/evidencias/replay/T042_pytest.txt` | cumple | — | — |
| J2 | Tiempo original y de reproducción | `docs/evidencias/replay/T053_replay_at_base.txt` | cumple | — | — |
| J3 | Topic y esquema separados | `docs/evidencias/replay/T053_despues.out`; `docs/evidencias/replay/T048_integracion.txt` | cumple | — | — |
| J4 | Etiqueta «REPRODUCCIÓN» | `docs/evidencias/replay/T056_reproduccion.png` | cumple | — | — |
| J5 | El replay reutiliza el procesamiento del consumidor | `docs/evidencias/replay/T046_pytest.txt`; `docs/evidencias/replay/T048_integracion.txt` | cumple | — | — |
| J6 | Duplicados y revisiones controlados | `docs/evidencias/replay/T053_consumer.log`; `docs/evidencias/replay/T054_repeticion.out` | cumple | — | — |
| J7 | Fechas originales; la vista de replay consulta el intervalo de 2025 | `docs/evidencias/replay/T055_comprobacion.txt`; `docs/evidencias/replay/T055_eventos_replay.json` | cumple | — | — |
| K1 | ≥3 operaciones: coste medio frente a peor caso | `docs/evidencias/mediciones/teoria_vs_observado.md`; `docs/memoria.md` (§7.1) | cumple | — | — |
| K2 | Tiempo y memoria con ≥3 tamaños de entrada | `docs/evidencias/mediciones/tablas.md`; `docs/evidencias/mediciones/equipo.md`; `docs/evidencias/mediciones/procedimiento.md` | cumple | La memoria con `tracemalloc` solo se midió en dos operaciones (`docs/memoria.md` §7.6) | — |
| K3 | Secuencial frente a diccionario, o sin/con índice | `docs/evidencias/mediciones/tablas.md`; `docs/evidencias/mediciones/indices.md` | cumple | — | — |
| K4 | Datos replicados marcados como sintéticos | `docs/evidencias/mediciones/aislamiento.md` | cumple | — | — |
| K5 | Razonar con 100 millones de registros | `docs/evidencias/mediciones/escalado.md`; `docs/memoria.md` (§7.3) | cumple | — | — |
| K6 | Costes: medido frente a supuesto | `docs/evidencias/mediciones/costes.md`; `docs/memoria.md` (§7.4) | cumple | El límite de la cuota gratuita de Netlify no está verificado (anotado en el propio `costes.md`) | — |
| K7 | Propuesta de escalado y mejoras ligadas a problemas concretos | `docs/evidencias/mediciones/escalado.md`; `docs/memoria.md` (§7.5) | cumple | — | — |
| M1 | Código: productor, consumidor, API, frontend, carga histórica y replay | `producer/loop.py`; `consumer/loop.py`; `api/main.py`; `frontend/src/App.tsx`; `historical/load_main.py`; `producer/replay.py` | cumple | — | — |
| M2 | Distinguir material reutilizado de lo desarrollado | `README.md` («Material reutilizado»); `docs/evidencias/panel-base-mock/T037_licencias.txt` | cumple | Ambos citan `react-globe.gl`, `three`, `paises.geojson` y el front externo del alumno; no hay teselas OSM ni Chart.js en el panel final | — |
| M3 | README reproducible | `README.md`; `specs/002-infra-compose/quickstart.md` | parcial | Cubre requisitos, `.env`, build, carga, logs, panel, túnel, replay y parada. Falta el recorrido del evento, el enlace al vídeo y la tabla de evidencias (T126), y no se ha seguido desde un clon limpio (T131 diferido). Estado de features aún con «Pendiente». Nota: responsable mixto, 013 (T126) para el texto y alumno para el clon limpio (T131 diferido) | 013 (T126) y alumno |
| M4 | El profesor tiene acceso al repositorio | (ninguna; es una acción en el servidor del repositorio) | no | No verificable desde el repo | alumno |
| M5 | Sin `node_modules`, secretos, token, volúmenes ni descargas regenerables | `.gitignore`; `frontend/.gitignore`; `docs/evidencias/infra-compose/busqueda_secretos.txt`; `docs/evidencias/despliegue-tunel/T067_puertos_secretos.txt` | cumple | `git ls-files` sin `node_modules`; `data/raw/`, `.env` y `compose.override.yaml` ignorados. `data/historical/` (14 MB) sí está versionado por decisión documentada en `README.md` | — |
| M10 | Tabla rúbrica→evidencia en el README | `docs/borradores/pruebas-aceptacion.md` (filas candidatas, sección M10) | no | `README.md` no tiene la tabla. Las filas candidatas están en el borrador | 013 (T126) |

## Pruebas de aceptación (tabla I; no llevan [OBL] en el checklist, se auditan aparte)

| Prueba | Evidencia (ruta) | Estado | Hueco | Responsable |
|---|---|---|---|---|
| Prueba 1 Evento nuevo | `docs/evidencias/pruebas/01-evento-nuevo.md`; `docs/evidencias/pruebas/capturas/01_evento_nuevo.png` | cumple | Captura real hecha (2026-11-15, evento `ci41362543`) | — |
| Prueba 2 Reenvío | `docs/evidencias/pruebas/02-reenvio.md`; `docs/evidencias/consumidor-idempotente/bloque3_prueba2_reenvio.out` | cumple | — | — |
| Prueba 3 Versión posterior | `docs/evidencias/pruebas/03-version-posterior.md`; `docs/evidencias/pruebas/capturas/03_version_posterior.png` | cumple | Captura real (`uw714139501`, 2 versiones 1,5758 → 1,38). Matiz: la magnitud cae en el mismo tramo del histograma; el caso con cambio de país y hora sigue siendo sintético (SQL de T095) | — |
| Prueba 4 Versión tardía | `docs/evidencias/pruebas/04-version-tardia.md`; `docs/evidencias/consumidor-idempotente/bloque3_prueba3_4_versiones.out` | cumple | — | — |
| Prueba 5 Magnitud nula | `docs/evidencias/pruebas/05-magnitud-nula.md`; `docs/evidencias/pruebas/capturas/05_magnitud_nula_nd.png` | cumple | Captura en modo mock (**sintética**, etiquetada): no hay nulos reales | — |
| Prueba 6 Coordenadas inválidas | `docs/evidencias/pruebas/06-coordenadas-invalidas.md`; `docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out` | cumple | — | — |
| Prueba 7 Evento marítimo | `docs/evidencias/pruebas/07-evento-maritimo.md`; `docs/evidencias/pruebas/capturas/07_evento_maritimo.png` | cumple | Captura real hecha (30 eventos «Sin país asignado», 2026-11-15) | — |
| Prueba 8 Reinicio del consumidor | `docs/evidencias/pruebas/08-reinicio-consumidor.md`; `docs/evidencias/consumidor-idempotente/prueba8_reinicio.out` | cumple | — | — |
| Prueba 9 Cierre del túnel | `docs/evidencias/pruebas/09-cierre-tunel.md`; `docs/evidencias/pruebas/capturas/09_cierre_tunel_sin_respuesta.png` | parcial | El panel muestra «SIN RESPUESTA DE LA API» sin presentarlo como 0 eventos, pero no demuestra que conserva la última lectura («Datos antiguos» con hora): falta la secuencia con datos previos | alumno |
| Prueba 10 Reapertura del túnel | `docs/evidencias/pruebas/10-reapertura-tunel.md`; `docs/evidencias/pruebas/09-10_revision_codigo.txt` | no | No ejecutada: la ficha es plantilla y solo hay revisión de código | alumno |
| Prueba 11 Reproducción histórica | `docs/evidencias/pruebas/11-reproduccion-historica.md`; `docs/evidencias/replay/T053_despues.out` | cumple | — | — |
