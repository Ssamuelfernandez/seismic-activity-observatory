# seismic-activity-observatory

Observatorio de actividad sísmica: un sistema que consulta el feed de terremotos de USGS, lo publica en Kafka, lo guarda en PostgreSQL sin duplicados ni pérdida de versiones y lo expone mediante una API a un panel con mapa. También permite reproducir un histórico, aislado de los datos en vivo. Proyecto de curso.

**Vídeo de 5 minutos: PENDIENTE: enlace de YouTube** (lo rellena el alumno tras grabarlo).

**Aviso: el panel público solo está disponible con el equipo del alumno y `cloudflared` encendidos.** La API pública sale de un túnel que se ejecuta en el PC del alumno; con el PC apagado o el túnel cerrado, el panel (que sigue en Netlify) no recibe datos. Para comprobar el sistema sin el túnel, ver «Cómo ejecutar» más abajo.

## Estado actual

Se trabaja con Spec Kit, una feature cada vez y con revisión antes de avanzar.

| Feature | Estado |
|---|---|
| `contratos-y-modelo` | Cerrada (2026-11-02): contratos, DDL, modelo de datos y evidencias |
| `infra-compose` | Implementada y verificada (2026-11-04), pendiente de la revisión del alumno: Compose con cinco servicios, "hola mundo" de punta a punta con un evento sintético, roles de base de datos y evidencias en `docs/evidencias/infra-compose/` |
| `consumidor-idempotente` | Implementada y verificada (2026-11-04), pendiente de la revisión del alumno: consumidor con validación, cuarentena, versiones, reintentos y contadores (C1–C8, C13; pruebas 2, 3, 4, 6 y 8). Evidencias en `docs/evidencias/consumidor-idempotente/`. Queda diferida la prueba de caída de PostgreSQL/Kafka con Docker (ver «Diferidas» en `specs/003-consumidor-idempotente/tasks.md`); el catálogo de países y la comprobación de esquema al arrancar los resuelve `geografia-pais` |
| `productor-live` | Implementada y verificada (2026-11-05), pendiente de la revisión del alumno: productor real que consulta USGS cada `POLL_SECONDS` y publica en `earthquakes.live` sin duplicar (B1–B12, A10; pruebas 1, hasta PostgreSQL, y 2). Evidencias en `docs/evidencias/productor-live/`. Sin diferidas; B2 (memoria §2.1), B11 (§10) y B12 (resumen en §10) pasados a la memoria; el borrador sigue en `docs/borradores/productor-live.md` |
| `geografia-pais` | Implementada y verificada (2026-11-05), pendiente de la revisión del alumno: país por geometría (`ADM0_A3`), catálogo de 177 países cargado al arrancar, comprobación de esquema y reglas de validez (C9–C12, C13; pruebas 5 y 7). Evidencias en `docs/evidencias/geografia-pais/`. Sin tareas diferidas; apuntes en `docs/borradores/geografia-pais.md` |
| `historico-2025` | Implementada y verificada (2026-11-05), pendiente de la revisión del alumno: descarga de 2025 (M≥4, mundial, por meses), deduplicación, carga en la base con el procesamiento común y procedimiento de hueco (B12–B18). Evidencias en `docs/evidencias/historico-2025/`; apuntes en `docs/borradores/historico-2025.md` |
| `api` | Implementada y verificada (2026-11-05), pendiente de la revisión del alumno: API de consulta de solo lectura (`/api/eventos`, `/api/estadisticas`, `/api/salud`; F1–F8, F10, F11, F12 parcial). Evidencias en `docs/evidencias/api/`; CORS (F9) queda en `despliegue` |
| `panel-base-mock` | **Completada** (2026-11-10), pendiente de la comprobación visual del alumno: panel React con el front externo del alumno adoptado y corregido, conectado a la API real, con mock sintético de cinco escenarios y 70 pruebas Vitest. Ver [`frontend/README.md`](frontend/README.md) y [`docs/evidencias/panel-base-mock/`](docs/evidencias/panel-base-mock/) |
| `009` filtros y tabla, `010` gráficos y comparación, `011` estado y fallos, `012` conexión con la API | Absorbidas por `panel-base-mock` (no se ejecutan por separado) |
| `replay` (009) | Completada (implementada y comprobada de extremo a extremo): reproducción acelerada de una selección de 2025 por Kafka, aislada de `live` (J1–J8, F12, G10). Ver la sección «Replay»; apuntes en [`docs/borradores/replay.md`](docs/borradores/replay.md) |
| `despliegue-tunel` (010) | Implementada y verificada en local (2026-11-12), pendiente de la revisión del alumno: CORS, `netlify.toml`, build sin mock, revisión de exposición y procedimiento de activación; túnel, Netlify, DNS y H1 hechos por el alumno (capturas del 2026-11-12 y 2026-11-15); pruebas 9 y 10 con captura parcial y demostración en el vídeo. Ver «Túnel público y panel» |
| `mediciones-costes` (011) | Cerrada (2026-11-13): costes y equipo rellenados por el alumno, auditoría sin bloqueantes, K1–K7 y E6 marcados. Evidencias en `docs/evidencias/mediciones/`; resumen en la sección 7 de la memoria. Solo falta repetir desde un clon limpio (SC-007) |
| `pruebas-aceptacion` (012) | Implementada y verificada (2026-11-14), pendiente de la revisión del alumno: 11 fichas y resumen en [`docs/evidencias/pruebas/README.md`](docs/evidencias/pruebas/README.md); capturas reales de 1, 3, 5 y 7 hechas (2026-11-15); pruebas 9 y 10 con captura parcial y demostración en el vídeo. Apuntes: [`docs/borradores/pruebas-aceptacion.md`](docs/borradores/pruebas-aceptacion.md) |
| `revision-final` (013) | Documentación final entregada (2026-11-15), sin cambios de código: auditoría de los requisitos obligatorios ([`auditoria.md`](docs/evidencias/revision-final/auditoria.md)), `CODEMAP.md` al día, este README con la tabla rúbrica→evidencia, análisis de calidad sobre datos reales ([`calidad-live.md`](docs/evidencias/revision-final/calidad-live.md)) y comprobación de la rúbrica-guía ([`rubrica-guia.md`](docs/evidencias/revision-final/rubrica-guia.md)). Memoria completa (§1 a §10, con análisis y conclusiones en §6), guía del vídeo vigente ([`docs/rubrica-y-guia-video.md`](docs/rubrica-y-guia-video.md)) y verificación de los documentos finales ([`verificador-docs-finales.md`](docs/evidencias/subagentes/verificador-docs-finales.md)). Lo que queda para el alumno está en «Pendientes del alumno» |

La API es la **API de consulta**, el productor es el **productor en vivo** y el consumidor es el **consumidor idempotente** (cada uno tiene su sección más abajo).

El orden de las fases está en [`docs/planificacion/02-roadmap-implementacion.md`](docs/planificacion/02-roadmap-implementacion.md).

Mapa de dónde está cada cosa: [`CODEMAP.md`](CODEMAP.md). Rúbrica, estado de cumplimiento y guion del vídeo: [`docs/rubrica-y-guia-video.md`](docs/rubrica-y-guia-video.md).

Mediciones de complejidad y costes (`mediciones-costes`, 011, cerrada): resumen en la sección 7 de [`docs/memoria.md`](docs/memoria.md), borrador en [`docs/borradores/mediciones-costes.md`](docs/borradores/mediciones-costes.md) y evidencias en [`docs/evidencias/mediciones/`](docs/evidencias/mediciones/README.md).

## Rúbrica → evidencia (M10)

Una fila por criterio de la rúbrica (Extracción, Calidad, Modelado, Análisis, Reflexión). El estado está tomado de [`docs/evidencias/revision-final/auditoria.md`](docs/evidencias/revision-final/auditoria.md); la rúbrica y el guion del vídeo, en [`docs/rubrica-y-guia-video.md`](docs/rubrica-y-guia-video.md). La última columna da el minuto del vídeo de 5:00 donde se enseña cada criterio; el cierre (4:40–5:00) usa el recorrido de `us6000pms8` y la decisión propia de más abajo.

| Criterio | Qué se afirma | Evidencia | Estado (auditoría) | Minuto del vídeo |
|---|---|---|---|---|
| Extracción | Feed de USGS cada 60 s con filtro `type=earthquake` y motivo de exclusión, originales guardados, histórico 2025 por meses (18 302 únicos) y catálogo de 177 países | [`docs/evidencias/productor-live/ciclo1.log`](docs/evidencias/productor-live/ciclo1.log), [`docs/evidencias/productor-live/ciclo1_consultas.out`](docs/evidencias/productor-live/ciclo1_consultas.out), [`data/historical/manifest.json`](data/historical/manifest.json), [`docs/evidencias/historico-2025/descarga_2025.log`](docs/evidencias/historico-2025/descarga_2025.log), [`docs/evidencias/geografia-pais/geografia_catalogo.out`](docs/evidencias/geografia-pais/geografia_catalogo.out) | B1 a B17 cumplen; B2 (respuesta, tipos, errores y latencia del feed) en la memoria §2.1, con resumen abajo; procedencia y registro de consultas en la memoria §3; prueba 1 con captura del panel con un evento real (`capturas/01_evento_nuevo.png`) | 0:20–1:05 |
| Calidad | Reglas de validación y cuarentena con motivo; análisis de las 6 dimensiones sobre datos reales de `live` con consultas SQL y resultados | [`docs/evidencias/revision-final/calidad-live.md`](docs/evidencias/revision-final/calidad-live.md), [`docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out`](docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out), [`docs/evidencias/pruebas/05-magnitud-nula.md`](docs/evidencias/pruebas/05-magnitud-nula.md), [`docs/evidencias/pruebas/07-evento-maritimo.md`](docs/evidencias/pruebas/07-evento-maritimo.md) | C1 a C13 cumplen; C14 en la memoria §4.4 (consultas en `calidad-live.md`; el «antes y después» se enseña con la evidencia de las reglas, porque en datos reales no hay nada que limpiar); pruebas 5 y 7 con captura (la 5, del mock sintético; la 7, real) | 1:05–1:55 |
| Modelado | Modelo conceptual, lógico y físico; `current_event` más historial de versiones; escritura idempotente; índices medidos sin y con índice | [`docs/memoria.md`](docs/memoria.md) (§5), [`sql/001_schema.sql`](sql/001_schema.sql), [`docs/evidencias/mediciones/indices.md`](docs/evidencias/mediciones/indices.md), [`docs/evidencias/pruebas/02-reenvio.md`](docs/evidencias/pruebas/02-reenvio.md), [`docs/evidencias/pruebas/04-version-tardia.md`](docs/evidencias/pruebas/04-version-tardia.md), [`docs/evidencias/pruebas/08-reinicio-consumidor.md`](docs/evidencias/pruebas/08-reinicio-consumidor.md) | E1 a E6 cumplen; pruebas 2, 4 y 8 observadas; prueba 3 con captura real (`capturas/03_version_posterior.png`) | 1:55–2:40 |
| Análisis | Estadísticas en SQL por hora UTC y por país (con «Sin país asignado»), distribuciones, comparación 24 h M≥4 frente a la media diaria de 2025, filtros coherentes entre mapa, tabla y gráficos | [`docs/evidencias/api/recorrido_08_estadisticas.txt`](docs/evidencias/api/recorrido_08_estadisticas.txt), [`docs/evidencias/api/coherencia_real.txt`](docs/evidencias/api/coherencia_real.txt), [`docs/evidencias/api/T016_pytest_api_comparison.txt`](docs/evidencias/api/T016_pytest_api_comparison.txt), [`docs/evidencias/panel-base-mock/T035_tabla_filtros_totales.md`](docs/evidencias/panel-base-mock/T035_tabla_filtros_totales.md), [`docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png`](docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png) | F7 y G3 a G8 cumplen; G2 cumple (ficha real; el ND, en modo mock sintético); 3 conclusiones con periodo, filtros y denominador en la memoria §6 ([`conclusiones-analisis.md`](docs/evidencias/revision-final/conclusiones-analisis.md)) | 2:40–4:10 (incluye las pruebas 9 y 10 en vivo, 3:35–4:10) |
| Reflexión | Complejidad con 3 tamaños, secuencial frente a diccionario y sin/con índice, razonamiento a 100 millones de registros, costes medido frente a supuesto y propuestas de escalado | [`docs/evidencias/mediciones/teoria_vs_observado.md`](docs/evidencias/mediciones/teoria_vs_observado.md), [`docs/evidencias/mediciones/tablas.md`](docs/evidencias/mediciones/tablas.md), [`docs/evidencias/mediciones/escalado.md`](docs/evidencias/mediciones/escalado.md), [`docs/evidencias/mediciones/costes.md`](docs/evidencias/mediciones/costes.md) | K1 a K7 cumplen; cuota de Netlify: plan gratuito, según indica el alumno | 4:10–4:40 |

La auditoría completa (una fila por cada requisito obligatorio, con huecos y responsable) está en `docs/evidencias/revision-final/auditoria.md`; las pruebas de aceptación 1 a 11, en [`docs/evidencias/pruebas/README.md`](docs/evidencias/pruebas/README.md).

### Respuesta del feed de USGS (B2, resumen)

El feed `all_day.geojson` es un GeoJSON con `metadata`, `features` y `bbox`; en la muestra del 2026-11-01 (210 eventos) las claves obligatorias estuvieron en todos, `mag` y la profundidad pueden ser negativas (no son errores), `alert`, `cdi`, `felt` y `mmi` son opcionales y a menudo nulos, y no hubo `mag` nula (el contrato la tolera). Tiempos en ms Unix UTC, profundidad en km. El feed se regenera cada unos 60 s (`Cache-Control: max-age=60`), por eso `POLL_SECONDS` es 60. En la muestra, latencia de 223 ms y 150 724 bytes (una sola medición). Los errores (429, 5xx, timeout, JSON inválido) no se midieron contra USGS real: se prueban con un servidor simulado. Detalle y fuentes: [`docs/borradores/productor-live.md`](docs/borradores/productor-live.md) y [`docs/evidencias/f1/explore_usgs_salida.txt`](docs/evidencias/f1/explore_usgs_salida.txt).

## Recorrido de un evento: `us6000pms8`

Es un evento **real de 2025** (terremoto M 4.4 `mb`, a 37 km SSW de Calama, Chile, 2025-01-28 12:26:19 UTC, profundidad 107,8 km) que se ha seguido **reproducido por replay** el 2026-11-12: no es un evento en vivo, entró por `earthquakes.replay` y vive en el esquema `replay`. El evento en vivo sigue el mismo camino, pero con el productor que consulta USGS y el topic `earthquakes.live`.

| Paso | Qué pasa con `us6000pms8` | Evidencia |
|---|---|---|
| Productor | `python -m producer.replay` lee `data/historical/` (comprobando el sha256 de cada archivo) y publica el mensaje con clave `us6000pms8` en `earthquakes.replay` (16:39:41 UTC) | [`docs/evidencias/replay/T053_replay.log`](docs/evidencias/replay/T053_replay.log) |
| Kafka | Topic `earthquakes.replay`, partición 0, offset 18 | [`docs/evidencias/replay/T053_consumer.log`](docs/evidencias/replay/T053_consumer.log) |
| Consumidor | Valida, asigna país por geometría y escribe en una transacción; línea `decision=new_event event_id=us6000pms8 topic=earthquakes.replay partition=0 offset=18`; después confirma el offset | [`docs/evidencias/replay/T053_consumer.log`](docs/evidencias/replay/T053_consumer.log) |
| Base de datos | Fila en `replay.current_event` con `event_time` 2025-01-28 12:26:19.97+00, `replay_at` 2026-11-12 16:39:41+00 y `is_synthetic` falso | [`docs/evidencias/replay/T053_despues_detalle.out`](docs/evidencias/replay/T053_despues_detalle.out) |
| API | `GET /api/eventos?mode=replay&start=2025-01-01&end=2026-01-01` devuelve el evento con `mag` 4.4, `country_id` `CHL` y los `time` originales | [`docs/evidencias/replay/T055_eventos_replay.json`](docs/evidencias/replay/T055_eventos_replay.json) |
| Panel | Con «Reproducción» elegido el panel muestra el banner «REPRODUCCIÓN» y los 22 eventos de 2025 (entre ellos este); la captura no lo señala individualmente | [`docs/evidencias/replay/T056_reproduccion.png`](docs/evidencias/replay/T056_reproduccion.png) |

## Decisión propia: el replay aislado de `live` en tres capas

Para tener actividad que enseñar sin esperar a un terremoto y sin contaminar los datos reales, el replay solo publica en `earthquakes.replay`, el consumidor guarda lo de ese topic únicamente en el esquema `replay` y además comprueba que el campo `mode` del mensaje coincide con el topic (si no, cuarentena con `mode_topic_mismatch`). **Motivo:** una sola barrera (por ejemplo solo el topic) dejaría que un error de configuración mezclara datos de demostración con datos reales sin que nadie lo notara; con tres capas independientes, el panel puede etiquetar «REPRODUCCIÓN» con seguridad. **Comprobado:** `live` quedó idéntico antes y después del replay el 2026-11-12 (211 / 211 / 0 con la misma huella `md5`, productor live parado; el `live` actual tiene más filas porque el productor sigue ingiriendo), ver [`docs/evidencias/replay/T053_despues.out`](docs/evidencias/replay/T053_despues.out).

## Limitaciones conocidas

- **Sin comparación en replay:** `GET /api/estadisticas?mode=replay` devuelve `comparison` nulo; la comparación histórica solo existe en modo en vivo.
- **Comparación fija:** siempre son las últimas 24 h frente a la media diaria de 2025 (M≥4), no hay periodos a elegir.
- **Periodo reciente posiblemente incompleto:** el periodo comparado puede no estar completo y la API lo avisa (`recent_incomplete`).
- **`tracemalloc`:** la memoria medida solo cuenta lo que reserva Python y solo se midió al construir el diccionario y en la integración geográfica.
- **Medición dentro de la VM de Docker:** los tiempos se tomaron en la VM de Docker Desktop (WSL2), no en el anfitrión; el equipo del anfitrión es supuesto ([`docs/evidencias/mediciones/equipo.md`](docs/evidencias/mediciones/equipo.md)).
- **Error 500 sin cabeceras CORS:** un error 500 de la API no lleva cabeceras CORS, así que el navegador lo ve como fallo de red ([`docs/borradores/despliegue-tunel.md`](docs/borradores/despliegue-tunel.md)).
- **Clon limpio verificado en la feature 002, no repetido con el estado final (A2):** la prueba de `docker compose up --build -d` desde un clon limpio es de 2026-11-03, antes del productor real, la API y el panel ([`docs/evidencias/infra-compose/clon_limpio.txt`](docs/evidencias/infra-compose/clon_limpio.txt)).
- **Un evento que sale de la ventana de 24 h del feed no está eliminado** (B11): el productor no puede distinguirlo y la reconciliación exhaustiva con USGS no está implementada (ver los límites del productor más abajo).
- **Sin país asignado:** la proporción es alta (24,5 % de eventos con país) por el catálogo de 110 m y el mar; no es un fallo (ver [`calidad-live.md`](docs/evidencias/revision-final/calidad-live.md)).
- **Datos del mock y del replay:** los sintéticos (`synthetic-…`, mock del panel) van etiquetados y no se mezclan con `live`.

## Cómo ejecutar

Guía detallada en «Ejecución con Docker Compose» más abajo y en [`specs/002-infra-compose/quickstart.md`](specs/002-infra-compose/quickstart.md). Resumen:

```bash
cp .env.example .env                 # en PowerShell: Copy-Item .env.example .env; cambia las contraseñas de ejemplo
docker compose build                 # construye la imagen Python compartida
docker compose up -d                 # arranca los cinco servicios
docker compose ps                    # deben figurar como healthy
curl http://127.0.0.1:8000/api/salud # 200 con status, last_ingestion y generated
```

- **Carga del histórico 2025:** ver «Histórico 2025» (`historical.load_main`, repetible; `data/historical/` ya está en el repositorio y no hace falta descargar).
- **Replay (opcional):** `docker compose run --rm producer python -m producer.replay --interval 2 --zone chile-norte --count 20` (ver «Replay»).
- **Panel local:** `cd frontend && npm ci && npm run dev` (http://localhost:4200, necesita Node 24.18.0 y la API en `127.0.0.1:8000`).
- **Pruebas:** `uv run pytest -m "not integration" -q` (unitarias) y, con PostgreSQL levantado, `docker compose --profile test build tests` seguido de `docker compose --profile test run --rm tests pytest -m integration -q` (integración); en el panel, `npm test`.
- **Muestra reducida declarada:** el repositorio trae el histórico completo de 2025 (18 302 eventos); para una demostración rápida basta el replay de 26 mensajes. Esta guía no se ha probado en un clon limpio con el estado final (A2).
- **Panel público:** `https://observatorio.ssamuelfernandez.net` **solo está disponible con el equipo del alumno y `cloudflared` encendidos** (ver «Túnel público y panel»). Sin ellos, usa el panel local.

## Pendientes del alumno

Hechas: G2, H1 y las capturas de las pruebas 1, 3, 5 y 7 (2026-11-15, en `docs/evidencias/pruebas/capturas/` y `docs/evidencias/despliegue-tunel/`). Decisiones aceptadas por el alumno (2026-11-16): H3 se da por cumplida con la captura existente ([`H3_cloudflared_tunel.png`](docs/evidencias/despliegue-tunel/H3_cloudflared_tunel.png), que muestra el túnel `observatorio-api` sano con su ruta pública, pero **no** la pestaña «Rutas» ni el destino `http://localhost:8000`); las pruebas 9 y 10 se dan por suficientes con las capturas existentes más la demostración en vivo en el vídeo; H4 se cumplirá al grabar el vídeo; el clon limpio (A2, M3) no se repite y queda como limitación (ver «Limitaciones conocidas»). Detalle en [`docs/evidencias/revision-final/auditoria.md`](docs/evidencias/revision-final/auditoria.md).

| ID | Qué falta | Dónde se rellena |
|---|---|---|
| H5 | Grabar el vídeo de 5 minutos y poner el enlace en el marcador de arriba | este README |
| Pruebas 9 y 10 | Se mostrarán en vivo en el vídeo (con el túnel real, cerrar `cloudflared`, esperar el refresco y reabrirlo); hoy hay una captura del panel «SIN RESPUESTA DE LA API», que no muestra «Datos antiguos» | [`docs/evidencias/pruebas/09-cierre-tunel.md`](docs/evidencias/pruebas/09-cierre-tunel.md), [`docs/evidencias/pruebas/10-reapertura-tunel.md`](docs/evidencias/pruebas/10-reapertura-tunel.md) |
| H4 | Se mostrará en el vídeo: demo con el equipo, los contenedores y el túnel encendidos (comprobaciones previas en «Túnel público y panel») | durante la grabación |

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| [`compose.yaml`](compose.yaml) | Los cinco servicios: Kafka, PostgreSQL, productor, consumidor y API |
| [`Dockerfile`](Dockerfile) | Imagen Python compartida por productor, consumidor y API |
| [`.env.example`](.env.example) | Variables de ejemplo, sin credenciales reales (se copia a `.env`) |
| `pyproject.toml`, `uv.lock`, `.python-version` | Python 3.12.16 y dependencias con versiones exactas y bloqueo |
| [`common/`](common/) | Código compartido por todos los servicios Python (configuración, reintentos, latido, conexión a PostgreSQL, temas de Kafka, evento sintético) |
| [`producer/`](producer/) | Productor en vivo (consulta USGS y publica en Kafka) y publicador del replay (`python -m producer.replay`) |
| [`consumer/`](consumer/) | Consumidor idempotente: valida, guarda en PostgreSQL y envía a cuarentena |
| [`api/`](api/) | API FastAPI de consulta, solo lectura: `/api/eventos`, `/api/estadisticas` y `/api/salud` |
| [`sql/`](sql/) | `001_schema.sql` (esquema) y `002_roles.sql` (roles y permisos) |
| [`scripts/`](scripts/) | `postgres_init.sh` (inicialización de la base), `verify_stack.py` y `check_env_example.py` (verificación) y `explore_usgs.py` (exploración del feed) y `verify_consumer.py` (escenarios del consumidor; usa `down -v`) |
| [`tests/`](tests/) | Pruebas unitarias de `common/`, `producer/` y `consumer/` (pytest) y pruebas de integración con PostgreSQL real (`tests/integration/`, servicio `tests`) |
| [`docs/planificacion/`](docs/planificacion/) | Checklist de requisitos ([01](docs/planificacion/01-checklist-requisitos.md)), roadmap ([02](docs/planificacion/02-roadmap-implementacion.md)), procedimiento de ejecución ([03](docs/planificacion/03-procedimiento-ejecucion.md)), glosario ([04](docs/planificacion/04-glosario-nomenclatura.md)) y [decisiones abiertas del contrato](docs/planificacion/decisiones-abiertas-contrato.md) |
| `docs/enunciado/` | Material del profesor (solo lectura) |
| `docs/evidencias/` | Salidas de pruebas y de revisiones; las de esta feature, en [`docs/evidencias/infra-compose/`](docs/evidencias/infra-compose/) |
| [`docs/memoria.md`](docs/memoria.md) | Memoria del proyecto (secciones 1 a 10) |
| [`specs/001-contratos-y-modelo/`](specs/001-contratos-y-modelo/) | Spec, plan, tareas y los tres contratos (`contracts/`) |
| [`specs/002-infra-compose/`](specs/002-infra-compose/) | Spec, plan, tareas, investigación, modelo de infraestructura, contrato de variables de entorno y [quickstart](specs/002-infra-compose/quickstart.md) |
| [`specs/003-consumidor-idempotente/`](specs/003-consumidor-idempotente/) | Spec, plan, investigación, tareas, bitácora, modelo de datos, [quickstart](specs/003-consumidor-idempotente/quickstart.md) y contrato de ejecución del consumidor (`contracts/consumer-runtime.md`) |
| [`specs/005-geografia-pais/`](specs/005-geografia-pais/) | Spec, plan, investigación, modelo de datos, tareas, bitácora y quickstart de la asignación de país |
| `data/catalogo/` | Catálogo de países (`paises.geojson`) |
| [`historical/`](historical/) | Descarga y carga del histórico 2025 (módulos `historical.download_main` y `historical.load_main`) |
| `data/historical/` | Archivos GeoJSON de USGS de 2025, `manifest.json` y el archivo del ensayo de hueco (14 MB, versionados) |
| [`specs/006-historico-2025/`](specs/006-historico-2025/) | Spec, plan, investigación, modelo de datos, tareas, bitácora y quickstart del histórico |
| [`specs/007-api/`](specs/007-api/) | Spec, plan, investigación, modelo de datos, tareas, bitácora y quickstart de la API de consulta |
| [`frontend/`](frontend/README.md) | Panel web (globo 3D, filtros, tabla, estadísticas): cómo ejecutarlo, configuración, mock y material reutilizado en [`frontend/README.md`](frontend/README.md) |
| [`netlify.toml`](netlify.toml) | Compilación y publicación del panel en Netlify |
| `CODEMAP.md` | Mapa de dónde está cada cosa |
| `.specify/`, `.claude/` | Configuración y plantillas de Spec Kit; agentes, habilidades y `settings.json` de Claude Code |

## Contratos y esquema

Los contratos viven solo en `specs/001-contratos-y-modelo/contracts/`:

- [`kafka-message.md`](specs/001-contratos-y-modelo/contracts/kafka-message.md): mensaje productor → consumidor, versiones y cuarentena.
- [`db-schema.md`](specs/001-contratos-y-modelo/contracts/db-schema.md): tablas, claves e índices.
- [`api.md`](specs/001-contratos-y-modelo/contracts/api.md): API → panel.

El DDL es [`sql/001_schema.sql`](sql/001_schema.sql); los roles de base de datos y sus permisos (exactamente los de la tabla «Quién escribe y quién lee» de `db-schema.md`) están en [`sql/002_roles.sql`](sql/002_roles.sql). Las variables de entorno y su correspondencia con el código están en [`specs/002-infra-compose/contracts/config.md`](specs/002-infra-compose/contracts/config.md).

## Herramientas

- Spec Kit CLI (`specify`): versión 1.2.4, obtenida con `specify --version`.
- Python 3.12.16 (imagen `python:3.12.16-slim-bookworm`, `.python-version`), dependencias bloqueadas con `uv` 0.12.13 (`uv.lock`).
- Docker con Compose v2 (probado con Docker 29.1.5 y Compose v5.0.1).
- Imágenes: `apache/kafka:4.1.2` (modo KRaft, un nodo) y `postgres:16.15-bookworm`.

## Ejecución con Docker Compose

Guía completa, con resolución de problemas: [`specs/002-infra-compose/quickstart.md`](specs/002-infra-compose/quickstart.md).

### Levantar

```bash
cp .env.example .env          # en PowerShell: Copy-Item .env.example .env
# Edita .env y cambia las contraseñas de ejemplo; .env está ignorado por Git.
docker compose up --build -d
docker compose ps             # los cinco servicios deben figurar como healthy
```

Solo la API se publica en el equipo, y solo en `127.0.0.1:8000`. Kafka y PostgreSQL no publican ningún puerto; entre contenedores se usan los nombres de servicio (`kafka`, `postgres`), nunca `localhost`.

### Comprobar

```bash
curl http://127.0.0.1:8000/api/salud                  # {"status":"ok","last_ingestion":null,"generated":...}
docker compose logs consumer --no-log-prefix --tail 5 # líneas «decision=… event_id=synthetic-…»
python scripts/verify_stack.py                        # verificación completa de punta a punta (reinicia los contenedores)
python scripts/verify_stack.py --skip-restart         # sin detener nada
python scripts/check_env_example.py                   # .env.example ↔ compose.yaml ↔ código
uv run pytest                                         # pruebas unitarias (no necesitan Docker)
```

### Reiniciar y parar

| Quiero… | Comando | Datos |
|---|---|---|
| Parar y volver a arrancar | `docker compose down` y `docker compose up -d` | Se conservan (volúmenes) |
| Reconstruir tras cambiar código | `docker compose up --build -d` | Se conservan |
| **Empezar de cero** | `docker compose down -v` | **Se borran** PostgreSQL y Kafka |

**Cambiar las contraseñas de la base de datos sobre un volumen ya inicializado exige `docker compose down -v`.** El esquema y los roles (con sus contraseñas) se aplican solo la primera vez, cuando el volumen de PostgreSQL está vacío; si cambias el `.env` después, los servicios usarán la contraseña nueva y no podrán conectar con las del volumen.

### Retención de Kafka

Los dos temas del contrato, `earthquakes.live` y `earthquakes.replay`, se crean con 1 partición, factor de replicación 1 y **retención de 7 días** (`retention.ms=604800000`); el broker además tiene `KAFKA_LOG_RETENTION_HOURS=168` como valor por defecto. **Motivo:** 7 días cubren una caída del consumidor de varios días sin perder mensajes, y el límite evita que el broker crezca sin control; el estado definitivo vive en PostgreSQL, no en Kafka. El valor está en `common/kafka_topics.py` y en `compose.yaml`.

### Listeners de Kafka y acceso desde el equipo anfitrión

Hoy el broker tiene **un solo listener de clientes**, interno: `kafka:9092`, anunciado por nombre de servicio y sin puerto publicado en el equipo (más el listener del controlador, `9093`, también interno). Dentro de un contenedor `localhost` apunta al propio contenedor, no al equipo, por eso los servicios usan `kafka:9092`.

Si en algún momento quieres leer Kafka desde el equipo anfitrión, el cambio es **añadir un segundo listener** en el servicio `kafka` de `compose.yaml`, sin tocar el interno:

```yaml
KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093,EXTERNAL://:9094
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:9094
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
ports:
  - "127.0.0.1:9094:9094"
```

Los contenedores siguen usando `kafka:9092`; los programas del equipo usan `localhost:9094`. **Advertencias:** (1) esta configuración **no se ha probado** en esta feature; (2) publica un puerto de Kafka, lo que contradice la regla «solo la API se expone» (constitución §10, requisito A8): úsala solo de forma temporal y en local, ligada a `127.0.0.1`, **nunca a través de un túnel**, y revierte el cambio antes de entregar.

### Acceso a la base de datos

PostgreSQL **no publica puertos** en el equipo (5432 es interno), de acuerdo con «solo la API se expone» (constitución §10, requisito A8). Hay dos formas de inspeccionarla.

**1. Consola `psql` dentro del contenedor (la vía oficial, sin cambios de configuración).** Usuario y base de datos son los de tu `.env` (en `.env.example`: `observatory_admin` y `observatory`); no pide contraseña porque la conexión es local al contenedor:

```bash
docker compose exec postgres psql -U observatory_admin -d observatory
# Dentro de psql: \dn (esquemas) · \dt *.* (tablas) · \d live.current_event (estructura) · \q (salir)
# Sin consola interactiva:
docker compose exec postgres psql -U observatory_admin -d observatory -c "SELECT count(*) FROM live.current_event;"
```

**2. Cliente gráfico (DBeaver, pgAdmin…) — solo desarrollo local.** Se usa el archivo `compose.override.yaml` de la raíz, que Compose carga solo y que **está en `.gitignore`**: publica Postgres únicamente en `127.0.0.1`, en el puerto **5433** del equipo (el 5432 puede estar reservado por Windows o por un Postgres local), por lo que no es accesible desde la red.

```yaml
services:
  postgres:
    ports:
      - "127.0.0.1:5433:5432"
```

Para activarlo, recrea solo ese servicio (se reinicia unos segundos; los datos están en el volumen): `docker compose up -d postgres`. Conexión desde el cliente: host `127.0.0.1`, puerto `5433`, base de datos, usuario y contraseña de tu `.env`. Para desactivarlo, borra `compose.override.yaml` y ejecuta de nuevo `docker compose up -d postgres`.

**Advertencias:** (1) es una herramienta local, **no forma parte de la arquitectura entregada** ni debe usarse en un despliegue; (2) como no viaja con el repositorio, en la nube no tendría efecto; (3) nunca publiques Postgres en `0.0.0.0` ni lo pases por un túnel. En un servidor propio, entra por SSH con `docker compose exec` o con un túnel SSH desde tu cliente.

### Túnel público y panel (Procedimiento de activación)

El túnel (Cloudflare Tunnel) **se ejecuta en el equipo anfitrión** con `cloudflared` y **queda fuera de Compose**: el repositorio no contiene configuración de túnel. Publica la API, que ya está en `127.0.0.1:8000` (único destino del túnel: `http://localhost:8000`). Evidencias y plantillas de las pruebas desde fuera: [`docs/evidencias/despliegue-tunel/`](docs/evidencias/despliegue-tunel/).

**Decisiones.**

- **(a) Cloudflare Tunnel con dominio propio.** La API queda en una URL estable (`https://observatorio-api.ssamuelfernandez.net`), sin página intermedia de aviso y sin la cuota mensual de peticiones (20 000 al mes) del plan gratuito de ngrok. ngrok u otro servicio equivalente serviría igual: en ese caso solo cambian la URL de `apiBaseUrl` y el origen permitido.
- **(b) API pública y de solo lectura.** El panel es estático y llama directamente a la API desde el navegador. Los datos son públicos (feed de USGS) y la API solo admite `GET` y `OPTIONS`. CORS no es una barrera de seguridad (solo lo aplican los navegadores; `curl` lo ignora): la protección es que la API es de solo lectura, sin secretos en las respuestas y con límite de eventos (`API_MAX_EVENTS`). Kafka y PostgreSQL nunca pasan por el túnel.
- **(c) DNS y Netlify, a mano.** En Cloudflare DNS, un CNAME `observatorio` hacia el sitio de Netlify con el **proxy desactivado** (nube gris, «solo DNS»). En Netlify, dominio personalizado `observatorio.ssamuelfernandez.net` y certificado HTTPS. La configuración de la compilación está en [`netlify.toml`](netlify.toml) (base `frontend`, `npm run build`, publicación `dist`, Node 24.18.0).

**Orden de arranque.**

1. **Compose.** Antes de abrir el túnel, retira `compose.override.yaml` si existe (publica Postgres en `127.0.0.1:5433`) y recrea la base: `docker compose up -d postgres`. Después `docker compose up -d` y `docker compose ps` con los cinco servicios `healthy`.
2. **API sana.** `curl http://127.0.0.1:8000/api/salud` devuelve 200 con `status`, `last_ingestion` y `generated`.
3. **`cloudflared`.** Con el túnel con nombre ya creado en tu cuenta, ejecútalo en el equipo, por ejemplo `cloudflared tunnel run --token <TOKEN>`. El token (marcador `<TOKEN>` en esta documentación) vive **solo en tu máquina**: nunca en Git, en `.env.example` ni en el frontend. `.gitignore` cubre los ficheros de credenciales habituales de `cloudflared`.
4. **Comprobación por la URL pública.** `curl https://observatorio-api.ssamuelfernandez.net/api/salud` debe devolver 200 con el mismo cuerpo.
5. **Panel público.** Abre `https://observatorio.ssamuelfernandez.net`; debe mostrar datos y recargar una ruta interna sin 404. Opcional: lanzar el replay (ver «Replay») para tener actividad que mostrar.

**Orden de parada.** Cierra `cloudflared` (Ctrl+C o parar su servicio), luego `docker compose down` (conserva los datos; `-v` los borra).

**Aviso de disponibilidad.** La URL pública de la API **solo existe mientras `cloudflared` y la API están encendidos en este PC**. Con el PC apagado, suspendido o sin red, el panel (que sigue en Netlify) no recibe datos: muestra el aviso de fallo y conserva la última lectura, y se recupera solo en el siguiente refresco cuando el túnel vuelve.

**CORS.** La API acepta los orígenes de `CORS_ALLOWED_ORIGINS` (por defecto `https://observatorio.ssamuelfernandez.net` y `http://localhost:4200`; exactos, sin barra final; `*` se rechaza y la API no arranca). Para probar con un dominio temporal de Netlify (`https://<sitio>.netlify.app`), añádelo a la variable en `.env` y recrea la API con `docker compose up -d api`; quítalo después.

**Configuración del panel.** `frontend/public/config.json` lleva `mode: "api"` y `apiBaseUrl` con la URL pública terminada en `/api`. Se lee en la compilación y se publica con el panel: **si cambia `config.json`, hay que volver a compilar y desplegar en Netlify**. Para desarrollo local con proxy, ver [`frontend/README.md`](frontend/README.md) (cambiar `apiBaseUrl` a `/api` solo en local, sin confirmarlo en Git).

**Comprobaciones previas a la defensa.** Que el PC no se suspenda (ajustes de energía); que el CNAME resuelva (`nslookup observatorio.ssamuelfernandez.net`); que el dominio por defecto de Netlify siga disponible como alternativa; que no exista `compose.override.yaml`.

| Elemento | Estado |
|---|---|
| CORS, `netlify.toml`, `config.json`, build sin mock, revisión de exposición | Implementado y comprobado en local (feature `despliegue-tunel`) |
| Token y arranque del túnel, sitio y dominio de Netlify, DNS, `curl` público y H1 | Hecho por el alumno (2026-11-12 y 2026-11-15): capturas y respuestas públicas en `docs/evidencias/despliegue-tunel/` |
| Pruebas 9 y 10 | Captura parcial; la demostración completa irá en el vídeo (ver «Pendientes del alumno») |

## Consumidor idempotente

El consumidor se suscribe a los topics de `KAFKA_CONSUMER_TOPICS` (lista separada por comas; por defecto `earthquakes.live,earthquakes.replay`; cada nombre se valida contra los topics del contrato y un nombre desconocido impide arrancar). `KAFKA_TOPIC` ya no sirve para suscribirlo: es el topic del productor live. Valida cada mensaje, lo guarda en PostgreSQL en una transacción por mensaje (sin duplicados, conservando todas las versiones) y envía a cuarentena lo que no se puede guardar. Escribe una línea `decision=… event_id=…` por mensaje y un resumen `COUNTERS {…}` cada 60 s y al parar. Los contratos están en `specs/001-contratos-y-modelo/contracts/` y los del consumidor en [`specs/003-consumidor-idempotente/contracts/`](specs/003-consumidor-idempotente/contracts/).

**Configuración del `.env` local** (no se comitea): además de las contraseñas, debe contener `KAFKA_GROUP_ID=consumer-live` (el grupo ya no se llama `consumer-minimal`), opcionalmente `KAFKA_CONSUMER_TOPICS` (si falta, `compose.yaml` usa `earthquakes.live,earthquakes.replay`) y `CONSUMER_FAULT_CRASH_AT_OFFSET=` (vacía; solo la usa la prueba 8). `.env.example` ya trae ambas.

**Pruebas unitarias** (sin Docker; el entorno virtual con las dependencias de desarrollo):

```bash
.venv/Scripts/python -m pytest -m "not integration" -q   # en Linux/macOS: .venv/bin/python; con uv: uv run pytest -m "not integration" -q
```

**Pruebas de integración** (PostgreSQL real, dentro del servicio `tests`, que no arranca con `up`): el `build` previo es necesario porque la imagen copia `common/` y `consumer/`; `tests/`, `sql/` y `scripts/` se montan en solo lectura (`scripts/` solo para que `tests/scripts/` pueda importarlo).

```bash
docker compose up -d postgres
docker compose --profile test build tests
docker compose --profile test run --rm tests pytest -m integration -q   # en Git Bash de Windows, prefija MSYS_NO_PATHCONV=1
```

**Verificación con Kafka y PostgreSQL reales** (escenarios `faq12`, `quarantine` y `restart`):

```bash
docker compose build producer          # imagen al día: consumer y api reutilizan la imagen del productor
python scripts/verify_consumer.py faq12 --yes
```

**Advertencia:** `verify_consumer.py` ejecuta `docker compose down -v`, que **borra los volúmenes locales** de Kafka y PostgreSQL del proyecto. Por eso pide `--yes` (o `VERIFY_CONSUMER_CONFIRM=yes`); sin él avisa y termina con código 2 sin hacer nada. Ejecuta `docker compose build producer` antes de cada escenario (el script también lo hace como primer paso). Los datos son sintéticos (`is_synthetic = true`).

Las salidas de las pruebas y de los escenarios están en [`docs/evidencias/consumidor-idempotente/`](docs/evidencias/consumidor-idempotente/).

### País por geometría y catálogo al arrancar

- **País**: el consumidor asigna `country_id` (`ADM0_A3`) a cada evento válido por punto en polígono con las coordenadas del mensaje (`common/geo.py`); nunca usa el texto `place`. El borde cuenta como dentro; si el punto cae en varios polígonos gana el `ADM0_A3` menor; si no cae en ninguno, `country_id` queda `NULL` («Sin país asignado») y el evento se guarda igualmente.
- **Arranque**: antes de consumir comprueba que existen las 8 tablas que usa (`consumer/schema_check.py`) y carga `data/catalogo/paises.geojson` (ruta en `COUNTRY_CATALOG_PATH`, ya en `compose.yaml`; sin variable nueva) en `public.country` de forma repetible (`consumer/catalog_loader.py`; línea `catalog loaded total=… inserted=… updated=…`). Si falta una tabla o el catálogo es inválido (código repetido, campo ausente, geometría no poligonal), termina con error y Compose lo reinicia.
- **Dependencia nueva**: `shapely` (2.x, versión exacta en `pyproject.toml`/`uv.lock`); no se usa GeoPandas.
- **Límites**: no hay recálculo retroactivo (las filas guardadas antes solo cambian si llega una versión con `updated` mayor; se parte de base limpia); el catálogo es 110m, así que costas y territorios pequeños pueden salir sin país.
- **Verificación**: `python scripts/verify_consumer.py geo --yes` (usa `down -v`, como los demás escenarios) y `uv run python scripts/geo_real_day.py docs/evidencias/geografia-pais/feed_all_day.geojson` (sin red ni base). Evidencias en [`docs/evidencias/geografia-pais/`](docs/evidencias/geografia-pais/).

## Productor en vivo

El productor consulta cada `POLL_SECONDS` (60 por defecto) el feed de USGS `USGS_FEED_URL` (por defecto `summary/all_day.geojson`, eventos de las últimas 24 horas) y publica en `earthquakes.live` solo lo nuevo o revisado: un evento se publica si no tiene estado previo o si su `updated` es mayor que el último publicado; los que no son `earthquake` se registran en `live.exclusion`. Cada consulta deja una fila en `ingest.ingest_run`. Los contratos del mensaje y de las tablas siguen en `specs/001-contratos-y-modelo/contracts/`; el diseño está en [`specs/004-productor-live/`](specs/004-productor-live/) y la guía de comprobación en su [quickstart](specs/004-productor-live/quickstart.md).

**Variables nuevas** (`.env.example` las trae con valores por defecto):

| Variable | Valor por defecto | Significado |
|---|---|---|
| `POLL_SECONDS` | 60 | Segundos entre consultas (entre 1 y 60) |
| `USGS_FEED_URL` | `.../summary/all_day.geojson` | Feed que se consulta (`http://` o `https://`) |
| `HTTP_TIMEOUT_SECONDS` | 10 | Espera máxima por operación de socket (entre 1 y 60) |
| `RAW_RETENTION_DAYS` | 7 | Días que se conservan las respuestas originales |

**Ver el log de ciclos:**

```bash
docker compose logs producer --no-log-prefix --tail 5
# cycle=3 status=ok http=200 latency_ms=... fetched=... excluded=... published=... skipped=... unmarked=... next_wait_s=60.0
```

Un ciclo con el feed sin cambios debe mostrar `published=0`. Tras un fallo (USGS caído, 429, tiempo agotado) la espera crece entre 2 s y 60 s, con aleatoriedad, y vuelve a `POLL_SECONDS` al recuperarse.

**Política de `raw_response`** (respuesta original de cada consulta, `ingest.raw_response`):

- Se guarda el cuerpo completo solo si su hash SHA-256, calculado **sobre `features`** (no sobre `metadata`, que cambia en cada regeneración), difiere del de la última consulta correcta.
- Retención de 7 días por defecto, configurable con `RAW_RETENTION_DAYS`. La purga se ejecuta al terminar cada ciclo correcto y siempre conserva la fila más reciente.
- Estimación: unos 150 KB por respuesta distinta (en la exploración del feed pesó 150724 bytes, ver `docs/evidencias/f1/explore_usgs_salida.txt`). Es una estimación de una sola medición, no un límite.
- `ingest.ingest_run` **no se purga**: es el registro de todas las consultas.

**Volúmenes de PostgreSQL ya existentes:** la purga necesita que el rol `observatory_producer` tenga `SELECT` y `DELETE` sobre `ingest.raw_response`. `sql/002_roles.sql` lo concede, pero solo se aplica con un volumen nuevo. En uno existente, aplica el `GRANT` a mano (o haz `docker compose down -v`, que borra los datos):

```bash
docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "GRANT SELECT, DELETE ON ingest.raw_response TO observatory_producer"
```

**Límites conocidos** (detalle en `specs/004-productor-live/research.md` §10):

- No se respeta la cabecera `Retry-After`.
- Un solo productor; dos a la vez no están soportados.
- Un evento sin `id` o sin `updated` se republica en cada ciclo.
- El periodo real entre consultas es algo mayor que `POLL_SECONDS`, porque la espera se suma a la duración del ciclo.
- Si USGS tarda más del tiempo de espera, el ciclo cuenta como fallo aunque el servicio funcione.
- Los eventos que USGS elimine del feed no se detectan: salir de la ventana de 24 h no equivale a ser eliminado, y la reconciliación exhaustiva es una ampliación. La recuperación de un hueco tras una parada de más de 24 h con el catálogo histórico está explicada, sin automatizar, en [`docs/borradores/productor-live.md`](docs/borradores/productor-live.md) (B2, B11 y B12).

## Histórico 2025

El histórico (2025, mundial, M≥4, `eventtype=earthquake`, por meses) se carga **por lote**, no por Kafka, con la misma función de procesamiento que el consumidor (`consumer.pipeline.process_record`), así que las reglas de validación, versión, cuarentena y país son idénticas. Es una **instantánea a la fecha de extracción**: no se reconcilian revisiones posteriores de USGS. Los eventos quedan con `source=usgs_historical` y `mode=live`.

**Dónde quedan los archivos.** `data/historical/` contiene 12 archivos `usgs_2025-MM.geojson`, `manifest.json` (consultas, fecha de extracción, registros y sha256 de cada archivo) y `usgs_gap_20251230T000000_20251231T000000.geojson` (ensayo del hueco). Ocupan unos 14 MB y están en el repositorio, así que **un clon no necesita descargar**; la carga comprueba el sha256 de cada archivo y se detiene si falta o cambió alguno.

**Descargar** (solo si se quiere rehacer; necesita red y no usa la base):

```bash
uv run python -m historical.download_main            # reutiliza lo ya descargado y verificado (0 peticiones)
uv run python -m historical.download_main --force    # vuelve a pedir todo
```

Qué esperar: línea `download_summary files=12 … unique=18302 … usgs_count_year=18302`. Si el total único no coincide con el `count` anual de USGS, termina con código distinto de 0 con ambas cifras.

**Cargar** (repetible; la imagen es compartida, por eso se construye con `producer`):

```bash
docker compose build producer
docker compose up -d postgres
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v ./data/historical:/app/data/historical:ro consumer python -m historical.load_main
```

(`MSYS_NO_PATHCONV=1` solo hace falta en Git Bash de Windows.) Qué esperar: `historical_summary unique=18302 new=… quarantined=0 ok=true`. Repetir el comando da `new=0 newer=0 unchanged=18302` y las mismas huellas; los datos sobreviven a `docker compose restart postgres`. Comprobación SQL en `docs/evidencias/historico-2025/verificacion.sql`.

**Hueco de más de 24 h** (parada del productor): descargar el intervalo perdido y volver a cargar; lo ya presente no se duplica ni retrocede.

```bash
uv run python -m historical.download_main --start 2025-12-30T00:00:00 --end 2025-12-31T00:00:00
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v ./data/historical:/app/data/historical:ro consumer python -m historical.load_main
```

Guía completa: [`specs/006-historico-2025/quickstart.md`](specs/006-historico-2025/quickstart.md). Evidencias: [`docs/evidencias/historico-2025/`](docs/evidencias/historico-2025/).

## API de consulta

API de solo lectura (rol `observatory_api`) sobre `live.current_event` y `replay.current_event`. Contrato: [`specs/001-contratos-y-modelo/contracts/api.md`](specs/001-contratos-y-modelo/contracts/api.md). Solo se publica en `127.0.0.1:8000`. Guía de validación: [`specs/007-api/quickstart.md`](specs/007-api/quickstart.md).

| Endpoint | Qué devuelve |
|---|---|
| `GET /api/eventos` | `FeatureCollection` GeoJSON con `metadata` (`count`, `total`, `truncated`, `next_cursor`, `null_mag_excluded`…) |
| `GET /api/estadisticas` | Total, eventos por hora y por país, histogramas de magnitud y profundidad y comparación con 2025, calculados en SQL |
| `GET /api/salud` | `status`, `last_ingestion` y `generated` |

**Parámetros** (eventos y estadísticas): `start` y `end` (ISO 8601, intervalo `[start, end)`; sin ellos, las últimas 24 h; sin zona se entiende UTC), `min_mag`, `country_id` (`jpn` o `JPN`; `none` = sin país), `mode` (`live` por defecto o `replay`). Solo eventos: `limit` (entre 1 y `API_MAX_EVENTS`) y `cursor` (el `next_cursor` de la respuesta anterior). Un parámetro inválido da 400 con `{"error": {"code", "message"}}`; sin base de datos, 503 `database_unavailable` en menos de 10 s; ruta inexistente 404 y método distinto de GET 405. No hay `/docs` ni `/openapi.json`.

**Variables** (en `.env.example` y en el servicio `api` de `compose.yaml`):

| Variable | Defecto | Significado |
|---|---|---|
| `API_MAX_EVENTS` | 5000 | Máximo de eventos por respuesta; si hay más, `truncated` es `true` y se pagina con `next_cursor` |
| `API_DB_TIMEOUT_SECONDS` | 5 | Espera máxima para obtener una conexión (de 1 a 9, para responder 503 en menos de 10 s) |

```bash
curl "http://127.0.0.1:8000/api/eventos?min_mag=4&country_id=jpn&limit=20"
curl "http://127.0.0.1:8000/api/estadisticas?start=2025-03-01&end=2025-04-01"
curl http://127.0.0.1:8000/api/salud
uv run pytest -m "not integration" -q                                              # unitarias
docker compose up -d postgres && docker compose --profile test build tests
docker compose --profile test run --rm tests pytest -m integration -q              # integración (rol real)
```

**Límites conocidos.** CORS (F9) lo añade `despliegue-tunel` (ver «Túnel público y panel»). El modo `replay` lee `replay.current_event`, que está vacío hasta que se lanza el replay (ver «Replay»). Un cursor reutilizado con otros filtros no se detecta; los parámetros desconocidos se ignoran; un error SQL no previsto sale como 503; un año completo en `by_hour` son unas 8 760 entradas. Si PostgreSQL está parado al arrancar, la API reintenta y no atiende hasta que vuelva. Evidencias: [`docs/evidencias/api/`](docs/evidencias/api/).

## Replay

Reproduce por Kafka una selección de eventos reales de 2025, a ritmo configurable, para tener actividad que mostrar sin esperar a un terremoto. Va aislado de `live` y etiquetado como «REPRODUCCIÓN». Guía paso a paso: [`specs/009-replay/quickstart.md`](specs/009-replay/quickstart.md); decisiones: [`specs/009-replay/research.md`](specs/009-replay/research.md); apuntes de defensa: [`docs/borradores/replay.md`](docs/borradores/replay.md).

**Selección por defecto.** Los 20 primeros eventos (por `time`, desempate por `id`) de la caja `chile-norte` (lat −27 a −18, lon −72 a −68,5), del 2025-01-01 08:08 UTC al 2025-01-29 03:44 UTC, leídos de `data/historical/` tras verificar el sha256 de cada archivo. Se eligió porque tiene más de 20 eventos M ≥ 4 y un país reconocible (18 en Chile, 1 en Bolivia, 1 sin país: enseña país por geometría y «Sin país asignado»). La otra zona disponible es `japon-honshu`, pero 9 de sus 20 primeros caen en el mar. A los 20 se añade un **bloque controlado** de 6 mensajes sobre dos eventos sintéticos (`synthetic-replay-e1`, `synthetic-replay-e2`, `is_synthetic = true`): reenvíos, una versión posterior y una versión antigua tardía.

**Comando** (el servicio `producer` monta `data/historical/` en solo lectura; no hay servicio nuevo):

```bash
docker compose run --rm producer python -m producer.replay --interval 2 --zone chile-norte --count 20
```

`--interval` son los segundos entre mensajes (por defecto 2, no es «el doble de rápido»); `--zone` y `--count` tienen los valores indicados y `--data-dir` por defecto `data/historical`. Con el intervalo por defecto dura unos 52 s. Termina con «Publicados: 26 (20 reales + 6 del bloque controlado)». Si falta o está alterado un archivo, la zona no existe o la selección queda vacía, sale con código 1 y no publica nada.

**Aislamiento.** Tres capas: el replay solo publica en `earthquakes.replay`; el consumidor guarda lo de ese topic únicamente en el esquema `replay`; y comprueba que el campo `mode` del mensaje coincide con el topic (si no, va a `replay.quarantine` con `mode_topic_mismatch`). Para comprobar que `live` no cambia, hay que parar antes el productor live (`docker compose stop producer`), porque este sigue ingiriendo USGS.

**Qué se espera ver** (esquema `replay` vacío, un solo replay): 26 mensajes; `replay.current_event` = 22 filas, `replay.event_version` = 24, `replay.quarantine` = 0; el consumidor registra 2 reenvíos ignorados, 1 versión posterior y 1 antigua tardía; `synthetic-replay-e1` conserva la versión con `updated` 10:09 y 3 versiones; todas las filas con `source = replay_demo` y `replay_at` no nulo. En la API, `GET /api/eventos?mode=replay&start=2025-01-01&end=2026-01-01` da `metadata.mode = "replay"` y `total = 22`, con los `time` originales; sin `mode` no sale ningún evento de replay; en `/api/estadisticas?mode=replay`, `comparison` es `null`. En el panel (`config.json` con `mode: "api"`), elegir «Reproducción» muestra el banner «REPRODUCCIÓN» y los 22 eventos con fechas de 2025; «En vivo» los oculta.

**Repetir.** Es idempotente: relanzar el replay sin vaciar nada deja los mismos 22 / 24 / 0 y los mismos `replay_at` de las filas existentes (todo son reenvíos). **Resultados medidos** (demo completa con contenedores, 2026-11-12): 26 mensajes publicados en 51 s con `--interval 2`; `replay.current_event` = 22, `replay.event_version` = 24, `replay.quarantine` = 0; 2 reenvíos ignorados, 1 versión posterior, 1 antigua tardía; `live` intacto (211 / 211 / 0 con la misma huella `md5` antes y después, con el productor live parado). Evidencias: [`docs/evidencias/replay/`](docs/evidencias/replay/).

**Límites conocidos.**

- No hay borrado de las tablas de replay (ningún rol tiene `DELETE`): empezar de cero exige recrear el volumen de PostgreSQL (`docker compose down -v`).
- La velocidad es un intervalo fijo entre mensajes, no una compresión proporcional del tiempo original.
- La selección y el bloque controlado son fijos: no hay modo aleatorio.
- El replay usa los archivos de `historico-2025`; no reproduce la ingesta real de USGS.
- El grupo del consumidor sigue llamándose `consumer-live` aunque ahora lee los dos topics (renombrarlo reprocesaría `live` entero).
- El bloque controlado tiene 6 mensajes, una variante propia de la secuencia de la FAQ 12 (que tiene 5).
- `specs/002-infra-compose/contracts/config.md` no recoge `KAFKA_CONSUMER_TOPICS`: la fuente es `.env.example` y este README.
- `verify_stack.py` da 14/16 por un `compose.override.yaml` local (puerto 5433) ajeno a la feature.
- `uv run` no funciona en el equipo: se usó `.venv` y el servicio `tests` de Docker.
- El panel se verificó solo con Edge headless por CDP, sin la extensión de Chrome.
- El replay no usa `usgs_gap_*` (research D10): solo lee los archivos mensuales del manifiesto.

## Panel web

Detalle completo en [`frontend/README.md`](frontend/README.md). Requiere Node 24.18.0 (`frontend/.nvmrc`) y, para ver datos reales, la API levantada en `127.0.0.1:8000` (`docker compose up -d`).

```bash
cd frontend
npm ci
npm run dev      # http://localhost:4200 (puerto fijo); /api se reenvía por proxy a http://127.0.0.1:8000
```

La configuración se lee al arrancar de `frontend/public/config.json` (`mode`, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`; sin secretos). Con `"mode": "mock"` usa el mock sintético, solo en desarrollo. El proxy se cambia con `API_PROXY_TARGET`. Pruebas: `npm test`.

### Material reutilizado

- **react-globe.gl** 2.38.0 y **three** 0.187.0 (licencia MIT): globo 3D.
- **`paises.geojson`** de Natural Earth (Admin 0 Countries, 1:110 m, dominio público): `data/catalogo/paises.geojson`, copiado sin modificar a `frontend/public/datos/`.
- **Front externo del alumno**: prototipo propio previo, portado y corregido para esta feature (inventario en [`specs/008-panel-base-mock/inventario-front-externo.md`](specs/008-panel-base-mock/inventario-front-externo.md)).

## Configuración de Git: el hook `commit-msg`

`.claude/settings.json` está versionado y desactiva la atribución en commits y PRs. **El hook `commit-msg` no se versiona** (vive en `.git/hooks/`, que Git no sube): **debe instalarse en cada clon**. Es un archivo `.git/hooks/commit-msg`, ejecutable, que rechaza los mensajes con trailers de coautoría o con «generated with»:

```sh
#!/bin/sh
if grep -qiE "co-authored-by|generated with" "$1"; then
  echo "Commit rechazado: sin trailers de coautoria ni lineas de herramienta." >&2
  exit 1
fi
```

Instálalo con `chmod +x .git/hooks/commit-msg`; en Windows, guárdalo con saltos de línea LF. Limitación conocida: no detecta «generado por» en español.
