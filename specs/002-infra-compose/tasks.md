---

description: "Lista de tareas de la feature infra-compose"
---

# Tasks: Infraestructura Compose y verificación de punta a punta

**Input**: Documentos de diseño en `specs/002-infra-compose/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/config.md`, `quickstart.md`).

**Prerequisites**: `plan.md` y `spec.md` (con las aclaraciones de la sesión 2026-11-03 y las seis decisiones aprobadas). La trazabilidad A1–A12 → criterio → tarea → evidencia está en `plan.md`.

**Tests**: la spec exige verificación de punta a punta y `CLAUDE.md` pide tests ejecutados y evidencia al cerrar. Las pruebas unitarias (pytest) y los scripts `scripts/verify_stack.py` y `scripts/check_env_example.py` ya existen; las tareas nuevas son verificaciones manuales o con comandos, con su salida guardada en `docs/evidencias/infra-compose/`.

**Estado**: la infraestructura existe como **borrador adelantado** (commit `33e1fc7`) y se probó parcialmente. Estas tareas **no la regeneran**: las marcadas `[x]` ya están hechas y verificadas (con el archivo de evidencia que se indica); las `[ ]` son lo que falta para completar y verificar. Si una verificación detecta un fallo, se corrige el archivo afectado, se repite la verificación y se anota en `plan.md`.

## Format: `[ID] [P?] [Story] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias).
- **[Story]**: historia de usuario de `spec.md` (US1–US6).
- Identificadores en inglés; documentación y comentarios en español.
- Solo puede haber **un stack de Compose a la vez** (el proyecto se llama `seismic-observatory` y los volúmenes y la red comparten nombre): antes de levantar uno, `docker compose down` en el otro. Las verificaciones sobre un clon se hacen **desde la carpeta del clon**.
- Ningún commit ni push lo hace el agente: si una precondición exige commit o push, se pide al alumno (constitución §19).

---

## Phase 1: Setup

**Purpose**: archivos base del proyecto (ya existen).

- [x] T001 Crear los archivos base: `pyproject.toml` (versiones `==`), `uv.lock`, `.python-version` (3.12.16), `Dockerfile` (contexto de build en la raíz; `uv sync --frozen`), `.dockerignore` y `.gitattributes` (LF en `.sh`, `.sql`, `.py`, `.yaml` y `Dockerfile`; `data/catalogo/paises.geojson -text`).
- [x] T002 [P] Crear `.env.example` (15 variables de ejemplo, contraseñas con prefijo `cambia-esta-clave`) y `scripts/check_env_example.py`; resultado en `docs/evidencias/infra-compose/check_env_example.txt`.

---

## Phase 2: Foundational (bloquea todas las historias)

**Purpose**: código compartido, base de datos y definición de Compose (ya existen; 22 pruebas unitarias superadas en `docs/evidencias/infra-compose/pytest.txt`).

- [x] T003 [P] Escribir `common/config.py`, `common/logging_setup.py`, `common/retry.py`, `common/health.py`, `common/db.py`, `common/kafka_topics.py` y `common/synthetic_event.py`, con sus pruebas en `tests/common/` y `tests/producer/test_loop.py`.
- [x] T004 [P] Escribir `sql/002_roles.sql` (roles `observatory_api`, `observatory_producer`, `observatory_consumer`, con los permisos **exactamente** de `db-schema.md` §1.1) y `scripts/postgres_init.sh` (aplica `sql/001_schema.sql` tal cual y después `002_roles.sql`, contraseñas por `psql -v` desde el entorno).
- [x] T005 Escribir `compose.yaml` (cinco servicios, red `seismic-observatory-backend`, volúmenes `postgres-data` y `kafka-data`, healthchecks, solo `127.0.0.1:8000:8000` publicado) con las imágenes `python:3.12.16-slim-bookworm`, `apache/kafka:4.1.2` y `postgres:16.15-bookworm`.

**Checkpoint**: el borrador arranca (T007) y pasa `scripts/verify_stack.py` (T016, T018, T020, T021, T025).

---

## Phase 3: User Story 1 - Arranque completo con un solo comando (Priority: P1) 🎯 MVP

**Goal**: desde un clon limpio, un solo comando deja los cinco servicios saludables, sin depender del orden de arranque.

**Independent Test**: clon nuevo + copiar `.env.example` a `.env` + `docker compose up --build -d` → cinco servicios `healthy` en menos de 5 minutos (SC-001) y `GET /api/salud` responde `ok`.

- [x] T006 [US1] Escribir el productor, el consumidor y la API mínimos: `producer/{main,loop,publisher}.py`, `consumer/{main,loop}.py`, `api/main.py`, `api/queries.py` y `api/routers/health.py` (solo `GET /api/salud`, según `contracts/api.md` §4).
- [x] T007 [US1] Arranque desde cero con la caché de Docker caliente: `docker compose down -v` + `up --build -d`; cinco servicios `healthy` en 15 s. Evidencia: `docs/evidencias/infra-compose/arranque_desde_cero.txt`.
- [x] T008 [US1] Reintentos con Kafka detenido mientras productor y consumidor arrancan: registran «Reintento N» y quedan en `starting`; al volver Kafka, los cinco `healthy`. Variable ausente: el error nombra la variable. Evidencia: `docs/evidencias/infra-compose/reintentos_y_configuracion.txt`.
- [x] T009 [US1] **Arranque adverso sin PostgreSQL (A4, FR-008, SC-002).** Con el stack parado (`docker compose down`, sin `-v`), levantar todo **menos** PostgreSQL: `docker compose up -d --no-deps kafka producer consumer api`. Durante al menos 60 s comprobar con `docker compose ps --all` y `docker inspect --format '{{.State.Status}} {{.RestartCount}}' <contenedor>` que `producer`, `consumer` y `api` siguen `running` con `RestartCount` 0 (no terminan ni entran en bucle de reinicios), que sus registros (`docker compose logs --no-log-prefix`) muestran líneas «Reintento N: no se pudo conectar con PostgreSQL (postgres)» con espera creciente, y que ninguno figura `healthy`. Después `docker compose up -d postgres` y medir cuánto tardan los cinco en estar `healthy` **sin reiniciar nada a mano**; criterio: todos `healthy` y `GET /api/salud` con `status: "ok"` en menos de 120 s desde que PostgreSQL está `healthy`. Guardar la salida y los tiempos en `docs/evidencias/infra-compose/arranque_sin_postgres.txt`. Si algún servicio termina o no se recupera, corregir `common/db.py`, `api/main.py` o el bucle afectado, repetir y anotarlo en `plan.md`.
- [x] T010 [US1] **Clon limpio real.** Precondición: el código está commiteado y subido, es decir, `git status --short` solo muestra cambios en `docs/evidencias/infra-compose/` y `git diff origin/002-infra-compose --stat` está vacío. Si no se cumple, **pedir al alumno** que haga commit y push antes de seguir (el agente no los hace). Con el stack del repositorio parado (`docker compose down`), clonar la rama publicada en una carpeta nueva y vacía **fuera** del repositorio (`git clone --branch 002-infra-compose https://github.com/Ssamuelfernandez/seismic-activity-observatory.git <carpeta>`) y trabajar desde ella; no copiar `.env` del repositorio original. Anotar la ruta, el resultado de las dos comprobaciones y el commit (`git rev-parse HEAD`) en `docs/evidencias/infra-compose/clon_limpio.txt`.
- [x] T011 [US1] **Checkout nuevo en Windows con LF.** En el clon de T010, **antes** de levantar nada, ejecutar `git ls-files --eol scripts/postgres_init.sh sql/001_schema.sql sql/002_roles.sql compose.yaml Dockerfile data/catalogo/paises.geojson` y comprobar que todos muestran `w/lf` (sin `w/crlf`), que el recuento binario de bytes CR (Python, `data.count(b"\r")`; no usar `grep -c $'\r'`, que en este entorno recibe el patrón vacío y devuelve el número de líneas) da 0 en `scripts/postgres_init.sh`, `sql/001_schema.sql`, `sql/002_roles.sql`, `compose.yaml` y `Dockerfile` y que `sha256sum data/catalogo/paises.geojson` es `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f` (el de `docs/enunciado/FUENTES-Y-LICENCIAS.md`). Guardar la salida en `docs/evidencias/infra-compose/checkout_lf.txt`. Si algún archivo sale con CRLF, corregir `.gitattributes`, repetir y anotarlo en `plan.md`.
- [x] T012 [US1] **Descarga en frío (SC-001, SC-002, SC-010).** Seguir **solo** las instrucciones de `specs/002-infra-compose/quickstart.md` §1, desde el clon de T010, sin consultar nada más. Antes, comprobar que ninguna otra cosa usa las imágenes (`docker ps -a --filter ancestor=<imagen>`) y eliminarlas para forzar la descarga: `docker rmi python:3.12.16-slim-bookworm apache/kafka:4.1.2 postgres:16.15-bookworm ghcr.io/astral-sh/uv:0.12.13 seismic-observatory-python:0.1.0` (sin purgar la caché global de Docker; usar `docker compose build --no-cache` si hace falta). Medir **dos tiempos** con `time`: (1) la descarga de imágenes (`docker pull python:3.12.16-slim-bookworm`, `docker pull ghcr.io/astral-sh/uv:0.12.13`, `docker pull apache/kafka:4.1.2` y `docker pull postgres:16.15-bookworm`); (2) `docker compose up --build -d` hasta que `docker compose ps` muestre los cinco `healthy`. Como la caché de BuildKit sigue caliente tras eliminar las imágenes, ejecutar antes `docker compose build --no-cache` con `time` y sumar su tiempo al del segundo paso. Registrar ambos y el total con descarga (la suma). **El criterio de SC-001 es el segundo tiempo: menos de 5 minutos sin contar la descarga de imágenes**; el total es informativo. Comprobar en `docker compose logs postgres` que `10-init.sh` se ejecutó sin errores de `\r` ni de sintaxis. Guardar los tiempos y la salida en `docs/evidencias/infra-compose/clon_limpio.txt`.
- [x] T013 [US1] En el clon de T012, ejecutar `python scripts/verify_stack.py` completo (incluye reiniciar) y guardar la salida en `docs/evidencias/infra-compose/clon_limpio_verify.txt`; deben pasar las 16 comprobaciones.
- [x] T014 [US1] **Caducidad del latido.** Los umbrales están en `specs/002-infra-compose/contracts/config.md` sección E (consumidor 60 s, productor 120 s; healthcheck cada 15 s con 3 reintentos). Con el stack sano, `docker compose stop kafka` y consultar `docker compose ps --format '{{.Service}} {{.Status}}'` cada 10 s durante 5 minutos como máximo. Esperado (según `config.md` §E): el consumidor pasa a `unhealthy` en 90–120 s y el productor en 120–180 s desde que se paró Kafka. Luego `docker compose start kafka` y comprobar que ambos vuelven a `healthy` sin intervención. Anotar los instantes de cada transición en `docs/evidencias/infra-compose/latido_caduca.txt`. **Fallo** = alguno no pasa a `unhealthy` dentro de 5 minutos, pasa antes de 60 s, o no se recupera tras volver Kafka; en ese caso revisar `common/health.py` y los `healthcheck` de `compose.yaml`, y corregir `config.md` §E si los tiempos reales difieren del cálculo.
- [x] T015 [US1] **`/api/salud` con la base caída.** Con el stack sano, `docker compose stop postgres` y ejecutar `curl -i --max-time 15 http://127.0.0.1:8000/api/salud`. Esperado: HTTP 503, `Content-Type: application/json` y cuerpo exactamente `{"error": {"code": "database_unavailable", "message": "No se pudo consultar la base de datos. Inténtalo de nuevo más tarde."}}` (`contracts/api.md` §6). **Cuenta como fallo** cualquiera de estos: (a) código HTTP distinto de 503; (b) cuerpo o `Content-Type` distintos de los indicados; (c) respuesta tardía (más de 10 s) o sin respuesta; (d) el cuerpo o el registro de la API contienen credenciales, SQL o trazas; (e) el contenedor `api` termina o se reinicia (`RestartCount` > 0); (f) tras `docker compose start postgres`, `/api/salud` no vuelve a responder 200 con `status: "ok"` en 60 s **sin reiniciar la API** (el pool debe recuperarse). Además, mientras la base está parada, el estado de `api` debe pasar a `unhealthy`. Si hay un fallo, corregir `api/routers/health.py` o `common/db.py`, repetir y anotarlo en `plan.md`. Guardar la salida en `docs/evidencias/infra-compose/salud_503.txt`.

**Checkpoint**: US1 verificable con T009–T015.

---

## Phase 4: User Story 2 - Evento sintético de punta a punta (Priority: P1)

**Goal**: el productor publica un evento ficticio marcado como sintético y el consumidor lo muestra en su registro.

**Independent Test**: con el sistema levantado, el log del consumidor contiene una línea `[SINTÉTICO]` con un `event_id` que empieza por `synthetic-`.

- [x] T016 [US2] El consumidor muestra el evento sintético del productor, también tras reiniciar los contenedores (relee los mensajes retenidos). Evidencia: `docs/evidencias/infra-compose/verificacion_completa.txt`.
- [x] T017 [US2] **Mensaje crudo frente al contrato.** Leer un mensaje real del tema con `docker compose exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic earthquakes.live --from-beginning --max-messages 1 --timeout-ms 20000 --property print.key=true` y comprobar contra `contracts/kafka-message.md` §3: la clave es igual a `event.id` y empieza por `synthetic`; `source = replay_demo`, `mode = live`, `replay_at = null`, `is_synthetic = true`; `ingested_at` en ISO 8601 UTC con `Z`; `event.properties.time` y `updated` enteros en milisegundos; `event.geometry.type = Point` con 3 coordenadas. Guardar el mensaje y el resultado de cada comprobación en `docs/evidencias/infra-compose/mensaje_crudo.txt`. No se modifica el contrato: si no coincide, se corrige `common/synthetic_event.py`.

---

## Phase 5: User Story 3 - Persistencia tras reinicio (Priority: P1)

**Goal**: PostgreSQL conserva los datos al detener y volver a arrancar los contenedores.

**Independent Test**: escribir un dato, `docker compose down` + `up -d`, comprobar que sigue ahí.

- [x] T018 [US3] Persistencia tras `down` + `up -d` con la tabla temporal `public.zz_infra_check` (creada y eliminada por el script) y los cinco servicios `healthy` de nuevo. Evidencia: `docs/evidencias/infra-compose/verificacion_completa.txt`.
- [x] T019 [US3] **Reaplicar el esquema sobre una base ya inicializada (FR-020).** Con el stack sano, guardar una «huella»: número de objetos por esquema (`pg_class` + `pg_namespace` para `public`, `live`, `replay` e `ingest`), lista de roles `observatory_%` (`pg_roles`) y un resumen ordenado de `information_schema.role_table_grants` para esos roles. Luego ejecutar dentro del contenedor, con el administrador, `psql -v ON_ERROR_STOP=1 -f /sql/001_schema.sql` y `psql -v ON_ERROR_STOP=1 -v api_password="$DB_API_PASSWORD" -v producer_password="$DB_PRODUCER_PASSWORD" -v consumer_password="$DB_CONSUMER_PASSWORD" -f /sql/002_roles.sql`. Esperado: código de salida 0 en ambos (solo avisos «ya existe, se omite»), huella idéntica antes y después, y `python scripts/verify_stack.py --skip-restart` sigue pasando. Guardar todo en `docs/evidencias/infra-compose/reaplicar_esquema.txt`. No se modifica `sql/001_schema.sql`.

---

## Phase 6: User Story 4 - Aislamiento y mínimo privilegio (Priority: P2)

**Goal**: solo la API es accesible desde fuera de Compose y lo hace con un rol de solo lectura.

**Independent Test**: `docker compose ps` muestra un único puerto publicado y la cuenta de la API es rechazada al escribir.

- [x] T020 [US4] Un único puerto publicado (`127.0.0.1:8000`), sin enlaces de puertos en Kafka ni PostgreSQL (`HostConfig.PortBindings` vacío), permisos de escritura de los tres roles según `db-schema.md` §1.1 y `INSERT` de la API rechazado. Evidencia: `docs/evidencias/infra-compose/verificacion_completa.txt`.
- [x] T021 [P] [US4] Permisos de lectura y de secuencias tras ajustar los roles a la tabla §1.1 (el productor no lee `exclusion` ni `raw_response` y no borra; el consumidor no lee `quarantine`). Evidencia: `docs/evidencias/infra-compose/permisos_lectura_y_secuencias.txt`.

---

## Phase 7: User Story 5 - Configuración sin secretos y versiones fijadas (Priority: P2)

**Goal**: ningún secreto en el repositorio, `.env.example` coincide con el código y las versiones están fijadas.

**Independent Test**: la búsqueda de secretos da 0 resultados reales y `python scripts/check_env_example.py` termina con código 0.

- [x] T022 [US5] `.env.example` coincide con `compose.yaml` y el código (15 variables, 14 leídas por el código) y las contraseñas son de ejemplo. Evidencia: `docs/evidencias/infra-compose/check_env_example.txt`.
- [x] T023 [P] [US5] **Búsqueda de secretos (SC-007).** Sobre el árbol versionado (`git ls-files`) y sobre el historial de la rama (`git log -p origin/main..HEAD`), buscar contraseñas, claves, `authtoken`, `BEGIN PRIVATE KEY` y asignaciones `PASSWORD=`/`SECRET=`/`TOKEN=` con valor; revisar cada coincidencia. Esperado: solo aparecen los cuatro valores `cambia-esta-clave-*` de `.env.example` y el nombre de variable en el código. Comprobar también que `git log --all -- .env` está vacío y que los archivos de `docs/evidencias/infra-compose/` no contienen contraseñas. Comprobar además (FR-034, A11) que la versión de Python 3.12.16 coincide: `FROM python:3.12.16-slim-bookworm` en `Dockerfile`, el contenido de `.python-version`, que `requires-python` de `pyproject.toml` (`>=3.12,<3.13`, decisión del plan) admite 3.12.16 y que `docker compose exec -T api python --version` muestra `Python 3.12.16`. Guardar los patrones usados y el resultado en `docs/evidencias/infra-compose/busqueda_secretos.txt`.
- [x] T024 [P] [US5] **Verificar M7–M9 sin rehacerlos (FR-037).** M7: contar trailers `Co-Authored-By` y líneas «generado por» en `git log --all --format=%B` (esperado 0) y **comprobar que existen** `.claude/settings.json` y el hook `commit-msg` (`.git/hooks/commit-msg` o el directorio de `core.hooksPath`, ejecutable); registrar el resultado tal cual, aunque sea «no existe». **M7 lo resuelve a mano el alumno**: esta tarea no crea ni modifica ninguno de los dos archivos. M8: `CLAUDE.md`, `CODEMAP.md` y `.specify/memory/constitution.md` están versionados (`git ls-files`) y `docs/` está separado de `specs/`. M9: `git diff origin/main -- docs/enunciado` vacío, existe `docs/enunciado/README-paquete.md` y `git show HEAD:data/catalogo/paises.geojson | sha256sum` coincide con `FUENTES-Y-LICENCIAS.md`. Guardar el resultado en `docs/evidencias/infra-compose/m7_m9.txt`. **Resultado (2026-11-03): M7 cumplido y M9 cumplido; M8 «al día» queda pendiente del cierre (README en T028, CODEMAP en T030).**

- [x] T033 [US5] **Configuración por entorno (C1, A10, FR-012, US5-4).** Con el stack sano en el repositorio de trabajo: (1) crear un tema de prueba que **no** es del contrato: `docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic config-test --partitions 1 --replication-factor 1`; (2) recrear solo el productor con otra configuración, sin tocar `.env` ni el código: `PRODUCER_INTERVAL_SECONDS=5 KAFKA_TOPIC=config-test docker compose up -d --no-deps --force-recreate producer` (las variables del shell tienen prioridad sobre `.env` en la interpolación) y comprobar con `docker compose exec -T producer env` que ve `PRODUCER_INTERVAL_SECONDS=5` y `KAFKA_TOPIC=config-test`; (3) esperar 40 s, contar los mensajes con `kafka-get-offsets.sh` y leer los 9 primeros con `kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic config-test --from-beginning --max-messages 9 --property print.key=true --property print.timestamp=true` (con `--timeout-ms` solo, el consumidor no termina porque llegan mensajes cada 5 s); esperado: al menos 6 mensajes con claves `synthetic-…` en el tema indicado (**tema**) y **cadencia** de 5 s medida con criterios robustos al reloj de la máquina virtual de Docker, cuyo reloj de pared da saltos hacia atrás de hasta ~1,3 s: mediana de las separaciones entre 4,5 y 5,5 s, al menos el 75 % de las separaciones entre 4 y 6 s y 8–10 mensajes en ~40–45 s (no exigir que cada separación esté entre 4 y 6 s); (4) comprobar que `earthquakes.live` no recibe mensajes en esa ventana (offset final leído **después** de recrear el productor, para no contar un último mensaje del productor antiguo); (5) **restaurar la configuración original**: `docker compose up -d --no-deps --force-recreate producer` (sin variables), comprobar que `env` vuelve a mostrar `PRODUCER_INTERVAL_SECONDS=30` y `KAFKA_TOPIC=earthquakes.live`, que el productor vuelve a `healthy` y que publica de nuevo en `earthquakes.live`; (6) eliminar el tema de prueba (`kafka-topics.sh --delete --topic config-test`). Guardar todo en `docs/evidencias/infra-compose/config_por_entorno.txt`. Si el comportamiento no cambia, corregir `producer/loop.py` o `common/config.py`.

---

## Phase 8: User Story 6 - Retención limitada del broker (Priority: P3)

**Goal**: los temas del contrato tienen retención limitada y documentada.

**Independent Test**: `kafka-topics.sh --describe` muestra 1 partición, factor 1 y `retention.ms=604800000`.

- [x] T025 [US6] Temas `earthquakes.live` y `earthquakes.replay` con 1 partición, factor de replicación 1 y `retention.ms=604800000`; broker con `KAFKA_LOG_RETENTION_HOURS=168` y creación automática desactivada. Evidencia: `docs/evidencias/infra-compose/verificacion_completa.txt`. La documentación de la retención y su motivo se cierra en T028.

---

## Phase 9: Polish & Cross-Cutting (cierre)

**Purpose**: cumplir constitución §16 y `CLAUDE.md` (tests ejecutados, evidencia, `CODEMAP.md` y `README.md`) y trasladar pendientes.

- [ ] T026 [P] Medir el tamaño del código (constitución §14; `CODEMAP.md`, Convenciones): con un script ad hoc **no versionado** en el directorio temporal de la sesión (módulo `ast`), listar funciones de más de ~30 líneas, archivos de más de ~250 líneas y funciones con más de 4 parámetros en `common/`, `producer/`, `consumer/`, `api/` y `scripts/`. Dividir o justificar cada exceso con un comentario; repetir `uv run pytest` y `python scripts/check_env_example.py`. Guardar el resultado en `docs/evidencias/infra-compose/tamanos_codigo.txt`.
- [ ] T027 [P] **Pendiente trasladado a la feature api (`007-api`).** Con el stack levantado comprobar que `curl -i http://127.0.0.1:8000/noexiste` devuelve el cuerpo por defecto de FastAPI (`{"detail":"Not Found"}`) y `curl -i -X POST http://127.0.0.1:8000/api/salud` devuelve `{"detail":"Method Not Allowed"}`, es decir, **no** el cuerpo de error común de `contracts/api.md` §6. Anotarlo como pendiente en `docs/planificacion/02-roadmap-implementacion.md`, sección F7 (añadir un punto: «Pendiente heredado de `002-infra-compose`: los 404 `not_found` y 405 `method_not_allowed` deben devolver `{"error": {"code", "message"}}`; hoy usan el cuerpo por defecto de FastAPI; añadir manejadores globales en `api/main.py`»), y comprobar que la sección «Pendientes trasladados a otras features» de `specs/002-infra-compose/plan.md` lo recoge. No cambiar `api/main.py` en esta feature.
- [ ] T028 [P] Actualizar `README.md` en una sola pasada: fila de `infra-compose` en «Estado actual»; filas nuevas en «Estructura del repositorio» (`compose.yaml`, `Dockerfile`, `.env.example`, `common/`, `producer/`, `consumer/`, `api/`, `sql/002_roles.sql`, `scripts/`, `tests/`); una sección «Ejecución con Docker Compose» con levantar, verificar (`scripts/verify_stack.py`, `scripts/check_env_example.py`, `uv run pytest`), reiniciar y `down -v`, y enlace a `specs/002-infra-compose/quickstart.md`. Incluir también: (1) la **retención de Kafka**: 7 días en los dos temas (`retention.ms=604800000`, más `KAFKA_LOG_RETENTION_HOURS=168` en el broker) y su motivo (cubre una caída del consumidor de varios días; el estado vive en PostgreSQL) (FR-021, FR-038); (2) que cambiar contraseñas sobre un volumen ya inicializado exige `docker compose down -v`; (3) que **ngrok se ejecuta en el equipo anfitrión** (`ngrok http 8000`) y su authtoken nunca va al repositorio; (4) un **aviso de que el hook `commit-msg` no se versiona** (vive en `.git/hooks/`) y debe instalarse en cada clon; (5) los **listeners de Kafka** (FR-026, A7): hoy solo existe el listener interno `kafka:9092`, anunciado por nombre de servicio, sin acceso desde el anfitrión, y **cómo habilitar ese acceso** (segundo listener `EXTERNAL` anunciado como `localhost:9094`, puerto publicado solo en `127.0.0.1:9094`, ajustes de `KAFKA_LISTENERS`, `KAFKA_ADVERTISED_LISTENERS` y `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP` en `compose.yaml`, manteniendo `kafka:9092` para los contenedores y explicando que `localhost` dentro de un contenedor no apunta al anfitrión). Documentar los puntos (3) y (5) también en `specs/002-infra-compose/quickstart.md`.
- [ ] T029 [P] **Verificar A12.** Comprobar y guardar en `docs/evidencias/infra-compose/a12.txt`: (1) `docker compose config --services` devuelve **exactamente cinco** servicios (`api`, `consumer`, `kafka`, `postgres`, `producer`); (2) `grep -n -i -w -E "ngrok|frontend|angular|netlify|node" compose.yaml` (con `-w`: sin él coincide con `KAFKA_NODE_ID`, una variable del broker) no encuentra ningún servicio ni imagen de frontend o ngrok; (3) `README.md` (T028) indica que ngrok se ejecuta en el equipo anfitrión. Depende de T028.
- [ ] T030 [P] Actualizar `CODEMAP.md`: filas en «Dónde está cada cosa» para `compose.yaml` (A1, A2, A8, A9), `Dockerfile` y `pyproject.toml`/`uv.lock` (A3, A11), `.env.example` y `specs/002-infra-compose/contracts/config.md` (A10), `common/retry.py` y `common/health.py` (A4), `common/kafka_topics.py` (A6), `producer/` (A1, A4), `consumer/` (A1, A4), `api/` (A1, A9), `sql/002_roles.sql` y `scripts/postgres_init.sh` (roles y primera inicialización), `tests/` (pruebas unitarias de `common/` y `producer/`), `scripts/verify_stack.py` y `scripts/check_env_example.py` (verificación), y `docs/evidencias/infra-compose/` (evidencias de la feature); actualizar la frase de «Estado».
- [ ] T031 Actualizar `specs/002-infra-compose/plan.md`, secciones «Verificación realizada» y «Hallazgos», con las evidencias nuevas (T009–T015, T017, T019, T023, T024, T026, T027, T029 y T033, esta última con `config_por_entorno.txt`) y el resultado de cada una; actualizar `spec.md` (`Status: Implemented`) y `checklists/requirements.md` si algo cambió. **Si T009, T014, T015, T026 o T027 modifican código** (cualquier archivo de `common/`, `producer/`, `consumer/`, `api/`, `compose.yaml`, `Dockerfile` o `scripts/`), repetir `python scripts/verify_stack.py` completo, `uv run pytest` y `python scripts/check_env_example.py` y actualizar las evidencias afectadas en `docs/evidencias/infra-compose/` (`verificacion_completa.txt`, `check_env_example.txt`, `pytest.txt` y las específicas de la tarea que cambió el código).
- [ ] T032 Al cerrar la feature, añadir su fila a «Historial de features cerradas» de `CODEMAP.md`, detenerse y esperar la revisión del alumno. No hacer commits ni merges sin su aprobación (constitución §19).

---

## Dependencies & Execution Order

- **Setup (Phase 1)** y **Foundational (Phase 2)**: hechas.
- **US1**: T009 (arranque adverso) puede hacerse en el repositorio de trabajo, antes del clon. T010 → T011 → T012 → T013 en este orden, sobre el mismo clon; T011 antes de levantar nada. T014 y T015 se hacen con el stack sano y **no** en paralelo entre sí ni con T009 (todos paran servicios).
- **US2 (T017)**, **US3 (T019)**: con el stack sano; T019 no para contenedores y puede ir en paralelo con T017. **T033** (US5) recrea solo el productor: con el stack sano, no en paralelo con T009, T014, T015 ni T017.
- **US5 (T023, T024)**: no necesitan Docker; en cualquier momento y en paralelo con todo lo demás. T024 solo registra el estado de M7; el alumno lo resuelve a mano.
- **Polish**: T026 y T027 [P] tras T015; T028 [P] (README) tras obtener los resultados que cita (T012, T014, T015, T019); **T029 depende de T028**; T030 [P] tras T028; T031 después de todas las verificaciones; T032 al final.

### Parallel Opportunities

```text
T023, T024                      # verificaciones sin Docker
T026, T027                      # medición y pendiente de la API
T028, T030                      # README y CODEMAP (archivos distintos); T029 después de T028
```

## Implementation Strategy

- **MVP**: US1 + US2 + US3 (las tres P1). El borrador ya las cumple en el repositorio de trabajo; falta demostrarlo en un **clon limpio con descarga en frío** (T010–T013) y con el arranque adverso (T009).
- **Orden recomendado**: T023 y T024 (sin Docker) → T009 → T010–T013 (clon limpio; requiere commit y push del alumno antes de T010) → T014 y T015 → T017 y T019 → T033 → T026–T030 → T031 → T032.
- Tras cualquier corrección de código, repetir `uv run pytest`, `python scripts/check_env_example.py` y `python scripts/verify_stack.py`, y actualizar las evidencias afectadas (T031).

## Notes

- **Pendiente trasladado a `007-api`** (T027): cuerpo de error común (`{"error": {"code", "message"}}`) en 404 y 405.
- **M7** (falta `.claude/settings.json` y el hook `commit-msg`) lo resuelve a mano el alumno; T024 solo lo verifica y registra.
- Un contrato solo vive en `specs/001-contratos-y-modelo/contracts/`; no se duplica ni se modifica aquí. `sql/001_schema.sql` y `docs/enunciado/` no se tocan.
- Los permisos de los roles siguen exactamente `db-schema.md` §1.1; los que falten los añadirá la feature que los necesite, actualizando esa tabla.
- Sin commits ni merges sin aprobación del alumno.
