# Tareas: despliegue-tunel (010)

**Entrada**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md` (esta carpeta). **IDs**: F9, F10, F5, G13, H1 a H4, A8, G9 (prueba real), pruebas 9 y 10.

14 tareas activas en 5 bloques (máximo 25 y 5), numeradas **T059–T072** para continuar la numeración de `009` (T041–T058). Formato: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = en paralelo (archivos distintos). Cada tarea lleva **Prueba** y **Cubre**. Todo código nuevo sigue `03 §7.4` (docstrings en español con la plantilla, identificadores en inglés, funciones de unas 30 líneas, archivos de 250 como máximo, lógica pura separada del I/O). Una prueba por comportamiento que pida un criterio de la spec; sin pruebas exhaustivas. Cualquier archivo de código nuevo se anota en `CODEMAP.md` en T072.

Notación: «sin Docker» = `.venv/Scripts/python.exe -m pytest -m "not integration" <ruta>` (donde `uv run` no funcione); «vitest» = `npm test` en `frontend/`. Cada ejecución se guarda en `docs/evidencias/despliegue-tunel/T0##_*.txt`. El agente no abre el túnel ni toca Cloudflare, Netlify ni DNS; no borra el `compose.override.yaml` local del alumno.

## Bloque 1 — CORS en la API (F9)

- [ ] T059 [US1] **Orígenes permitidos (puro)**: en `common/api_config.py`, `DEFAULT_CORS_ORIGINS = "https://observatorio.ssamuelfernandez.net,http://localhost:4200"`, `parse_cors_origins(raw)` y `load_cors_origins()` (`read_str("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS)`). Reglas de `data-model.md`: cada elemento `http(s)://host[:puerto]` sin barra final ni ruta; espacios recortados, vacíos por coma ignorados, duplicados eliminados; `*`, elemento sin esquema, con ruta o barra final, y lista vacía lanzan `ConfigError` que nombra la variable. Tests en `tests/common/test_api_config.py`.
  - **Prueba (sin Docker)**: por defecto devuelve los dos orígenes; dos orígenes con espacios y un duplicado; `*`, `observatorio.example.com`, `http://localhost:4200/` y `https://x.netlify.app/api` dan `ConfigError` con `CORS_ALLOWED_ORIGINS` en el mensaje; variable ausente → defecto; variable vacía → `ConfigError` (viene de `read_str`).
  - **Cubre**: F9; FR-001, FR-003 (sin `*`), FR-004.

- [ ] T060 [US1] **Middleware CORS**: `api/main.py::create_app()` añade `CORSMiddleware(allow_origins=list(load_cors_origins()), allow_methods=["GET", "OPTIONS"], allow_headers=["ngrok-skip-browser-warning"], allow_credentials=False)`. Sin tocar routers, errores ni contratos. Tests en `tests/api/test_cors.py` (`httpx.ASGITransport` sobre `create_app()`, como `tests/api/test_errors.py`; el `lifespan` no se ejecuta, no hace falta BD; ruta de prueba añadida a la app de la prueba si hace falta).
  - **Prueba (sin Docker)**: los 6 escenarios de US1: (1) preflight `OPTIONS /api/eventos` con el origen público, `Access-Control-Request-Method: GET` y `Access-Control-Request-Headers: ngrok-skip-browser-warning` → 200, `Allow-Origin` igual al origen, `Allow-Methods` con `GET` y `OPTIONS` y la cabecera permitida; (2) lo mismo con `http://localhost:4200`; (3) `https://otro.example` en `GET` y en preflight sin `Access-Control-Allow-Origin`; (4) ninguna respuesta con `Access-Control-Allow-Credentials` ni `Allow-Origin: *`; (5) con `CORS_ALLOWED_ORIGINS` ampliada con `https://sitio.netlify.app` (monkeypatch + nueva `create_app()`), ese origen se permite, y al quitarlo no; (6) preflight con `Access-Control-Request-Method: POST`: `POST` no aparece en `Allow-Methods`. Además: con `CORS_ALLOWED_ORIGINS=*`, `create_app()` lanza `ConfigError`. Las pruebas existentes de `tests/api` siguen en verde.
  - **Cubre**: F9; FR-001 a FR-003; SC-001. Depende de T059.

- [ ] T061 [P] [US1] **Variable en entorno y Compose**: añadir `CORS_ALLOWED_ORIGINS` a `.env.example` (con comentario: orígenes exactos, sin barra final, un origen temporal de Netlify se añade aquí y se recrea la API) y al bloque `environment` del servicio `api` en `compose.yaml` como `${CORS_ALLOWED_ORIGINS:-https://observatorio.ssamuelfernandez.net,http://localhost:4200}`. Sin otros cambios en Compose (cinco servicios).
  - **Prueba**: `python scripts/check_env_example.py` con código 0; `docker compose config --services` sigue con exactamente 5 servicios; `docker compose config` muestra `CORS_ALLOWED_ORIGINS` con el defecto en `api`. Salida en `T061_env.txt`.
  - **Cubre**: F9; FR-005, FR-019; constitución §10.

- [ ] T062 [US1] **CORS contra la API real de Compose**: reconstruir y recrear (`docker compose build producer`, `docker compose up -d api`) y ejecutar con `curl -si` los casos de `quickstart.md` §3: preflight con el origen público, `GET /api/salud` con `http://localhost:4200`, `GET` con `https://otro.example`. Después, con `CORS_ALLOWED_ORIGINS=*` en un `.env` temporal o `docker compose run --rm -e CORS_ALLOWED_ORIGINS='*' api ...` comprobar que la API no arranca y el log nombra la variable (restaurar el estado normal). Guardar comandos y cabeceras en `T062_cors_curl.txt`.
  - **Prueba**: 200 con `Access-Control-Allow-Origin` en los dos primeros, sin él en el tercero, sin `Allow-Credentials`; arranque con `*` falla con mensaje claro; la API vuelve a quedar sana (`/api/salud` 200).
  - **Cubre**: F9; SC-001; FR-001 a FR-003. Depende de T060 y T061.

## Bloque 2 — Panel y build (G13)

- [ ] T063 [P] [US2] **`netlify.toml`**: archivo en la raíz con `[build] base = "frontend"`, `command = "npm run build"`, `publish = "dist"`, `[build.environment] NODE_VERSION = "24.18.0"` y `[[redirects]] from = "/*" to = "/index.html" status = 200`. Test en `tests/scripts/test_netlify_config.py` (`tomllib`).
  - **Prueba (sin Docker)**: el test comprueba los cinco valores y que `NODE_VERSION` es igual al contenido (recortado) de `frontend/.nvmrc`.
  - **Cubre**: G13; FR-007; US2.4 y US2.5; constitución §11.

- [ ] T064 [P] [US2] **`config.json` y prueba del cliente real**: `frontend/public/config.json` con `mode = "api"`, `apiBaseUrl = "https://observatorio-api.ssamuelfernandez.net/api"`, `refreshSeconds` y `timeoutMs` sin cambio. Añadir a `frontend/README.md` la nota de desarrollo con proxy (cambiar `apiBaseUrl` a `/api` solo en local, sin confirmarlo en Git). Test `frontend/tests/apiUrl.test.ts`: con `setConfig` de ese `config.json`, `fetch` sustituido por un doble y `apiEvents`, `apiStats` y `apiHealth` reales, las URLs son `.../api/eventos`, `.../api/estadisticas`, `.../api/salud`.
  - **Prueba (vitest)**: las 3 URLs exactas y ninguna contiene `/api/api`; `validateConfig` acepta el contenido de `public/config.json`; este lleva `mode = "api"`, la URL exacta sin barra final y ninguna clave tipo token o secreto. `npm test` completo sigue en verde.
  - **Cubre**: G13; FR-006, FR-009; SC-002; US2.1 y US2.2.

- [ ] T065 [US2] **Build de producción sin mock**: `frontend/scripts/check-dist.mjs` (Node sin dependencias): falla si `dist/` contiene ficheros con nombre de `frontend/mock/*.json` o una cadena distintiva del mock en el JS compilado (se elige al implementar mirando `mock/backend.ts` y `mock/base.json`), o si `dist/config.json` difiere de `public/config.json`. Ejecutar con Node `24.18.0`: `npm run build` y `node scripts/check-dist.mjs`. Anotar en `frontend/README.md` cómo ejecutarlo.
  - **Prueba**: build sin errores; `check-dist` sale con 0 y lista 0 ficheros del mock; como comprobación negativa, una copia temporal de `dist/` con un `base.json` añadido hace que salga con código distinto de 0. Salida en `T065_build_dist.txt`.
  - **Cubre**: G13, G15 (re-comprobación); FR-008; SC-002 y SC-003; constitución §7. Depende de T064.

## Bloque 3 — Revisión de exposición (F10, F5, A8)

- [ ] T066 [US3] **Rutas, métodos, secretos y límite**: con la pila de Compose y la API sana, ejecutar y guardar en `docs/evidencias/despliegue-tunel/exposicion.md` (comando, esperado, observado, veredicto por fila): (1) `GET` a `/api/salud`, `/api/eventos`, `/api/estadisticas` → 200 y `/docs`, `/redoc`, `/openapi.json` y una ruta de administración inventada → 404 con el cuerpo común; (2) `POST`, `PUT`, `PATCH` y `DELETE` a las 3 rutas → 405 `{"error": ...}`, sin cambios en los datos (recuento antes y después); (3) búsqueda en las respuestas de 200 y de errores de los valores de `POSTGRES_USER`, `POSTGRES_PASSWORD` y las contraseñas de `DB_*` de `.env` (sin imprimirlos) y de textos como `Traceback` → 0 coincidencias; (4) petición con `limit=999999` y otra sin `limit` en un rango amplio → como mucho `API_MAX_EVENTS` (5 000) eventos, con `truncated` y `next_cursor` coherentes. Anotar los hallazgos tal cual (FR-011); solo se corrige lo que falle F9, F10 o F5.
  - **Prueba**: SC-005 (3 rutas, 4 métodos con 405, 0 secretos, ≤ 5 000 eventos); cada fila con salida real; `T066_*.txt` con la salida bruta.
  - **Cubre**: F10, F5; FR-010, FR-011; SC-005; US3.1 a US3.4 y US3.6.

- [ ] T067 [US3] **Puertos, túnel y credenciales**: (a) añadir a `.gitignore` `.cloudflared/`, `cert.pem`, `cloudflared*.yml`, `cloudflared*.yaml` y `cloudflared-credentials*.json` junto al bloque de ngrok (que se mantiene); (b) añadir a `exposicion.md`: `docker compose -f compose.yaml config` (ignora el override local) con un único puerto publicado, `127.0.0.1:8000`, y sin 5432 ni 9092; `docker ps` real, y si el `compose.override.yaml` del alumno publica `127.0.0.1:5433`, anotarlo como hallazgo local con la instrucción del README (no se borra el fichero); `git ls-files | grep -i -E "cloudflared|cert.pem|credentials"` sin resultados (no hay configuración de túnel en el repo); (c) búsqueda de secretos (SC-008): patrones de token y ficheros de credenciales sobre `git ls-files -o -m --exclude-standard`, y `git check-ignore -v` de los nombres nuevos del `.gitignore`; (d) fila **pendiente del alumno**: captura de la configuración del túnel que muestre `http://localhost:8000` como único destino, con el token tapado.
  - **Prueba**: SC-005 (1 puerto publicado) y SC-008 (0 resultados); `git check-ignore` reconoce `.cloudflared/x`, `cert.pem` y `cloudflared-credentials-x.json`. Salida en `T067_puertos_secretos.txt`.
  - **Cubre**: A8, F10; FR-012, FR-013, FR-016; SC-005, SC-008; US3.5.

## Bloque 4 — Documentación y plantillas (H2, H3, H4, H1, pruebas 9 y 10)

- [ ] T068 [US5] **README: «Procedimiento de activación»**: sustituir la subsección «ngrok» (`README.md`, dentro de «Ejecución con Docker Compose») por un apartado «Túnel público y panel (Procedimiento de activación)» con: orden de arranque Compose (sin `compose.override.yaml`: retirarlo y `docker compose up -d postgres`) → API sana → `cloudflared` → `curl` a `/api/salud` por la URL pública → panel público (→ replay opcional); orden de parada; decisiones (a), (b), (c) de FR-015 con los pasos manuales de DNS (CNAME `observatorio`, proxy desactivado) y Netlify (dominio personalizado, certificado); la variable `CORS_ALLOWED_ORIGINS` y el origen temporal de Netlify; que el panel se recompila si cambia `config.json`; el aviso de que la API solo existe con `cloudflared` y la API encendidos; comprobaciones previas (suspensión del PC, DNS, dominio por defecto de Netlify); nota de desarrollo con proxy (T064); fila de estado de la feature. Solo `<TOKEN>` como marcador. Actualizar la línea de la tabla de «Estado actual» y «Estructura del repositorio» si procede.
  - **Prueba**: lectura contra US5 y SC-007 (4 pasos de activación + comprobación + aviso); `grep -n -i -E "token|authtoken" README.md` sin valores reales; `grep -n "ngrok" README.md` solo en la explicación de «equivalente» y en lo heredado de la cabecera por contrato. Salida en `T068_readme.txt`.
  - **Cubre**: H2, H3, H4, M3 (parte); FR-014, FR-015; SC-007; US5.

- [ ] T069 [P] [US4] **Plantillas de evidencia**: en `docs/evidencias/despliegue-tunel/`, `H1_movil.md`, `prueba-09_cierre-tunel.md`, `prueba-10_reapertura-tunel.md` (pasos, resultado esperado según US4, hora, hueco para capturas con la URL visible, estado «pendiente del alumno») y un `README.md` inicial con el índice y la lista de lo pendiente del alumno (token y arranque del túnel; sitio, dominio y certificado de Netlify; DNS; `curl` público SC-004; H1; pruebas 9 y 10; captura del destino del túnel).
  - **Prueba**: las tres plantillas existen, cada una con pasos numerados, esperado, hueco de captura con URL y marca «pendiente del alumno»; el índice las enlaza.
  - **Cubre**: H1, pruebas 9 y 10, G9 (prueba real); FR-017; SC-006 (plantilla); US4.

- [ ] T070 [US5] **Menciones a ngrok (redacción propia)**: sustituir por «túnel (Cloudflare Tunnel)» o equivalente, de forma mínima, en `docs/planificacion/02-roadmap-implementacion.md` (F11, riesgos, verificación), `03-procedimiento-ejecucion.md` (§4 nombre y nota «carpeta real `010`», §8.4 y la fila de `despliegue-tunel`; corregir `publish = dist` con `base = frontend`), `04-glosario-nomenclatura.md` y `CODEMAP.md` (si aparece). No se editan `01-checklist-requisitos.md` (lo marca el alumno; pregunta 3), `.specify/memory/constitution.md`, `specs/001-contratos-y-modelo/contracts/`, `docs/enunciado/`, `specs/002-infra-compose/`, `specs/007-api/` ni evidencias ya generadas. `frontend/vite.config.ts` queda como está.
  - **Prueba**: `grep -rn -i ngrok docs/planificacion CODEMAP.md README.md` listado en `T070_menciones.txt`: cada resto está justificado (enunciado o contrato citado, «ngrok u otro equivalente», cabecera `ngrok-skip-browser-warning`, `01-checklist`); `git diff --stat` no muestra los archivos prohibidos.
  - **Cubre**: FR-018; H3 (coherencia).

## Bloque 5 — Regresión y cierre

- [ ] T071 [US1][US2][US3] **Regresión**: ejecutar la suite sin Docker completa, `npm test`, `scripts/check_env_example.py`, la suite de integración de la API en el servicio `tests` (`docker compose --profile test run --rm tests` limitado a `tests/integration/test_api_*`), y repetir `docker compose ps` para confirmar los cinco servicios sanos con la API recreada.
  - **Prueba**: todo en verde; salidas en `T071_*.txt`; `git status` sin archivos inesperados (solo los listados en el plan).
  - **Cubre**: F9, F10, F5; SC-001, SC-002; constitución §16.

- [ ] T072 [US1][US2][US3][US4][US5] **Cierre y `CODEMAP.md`**: `docs/evidencias/despliegue-tunel/README.md` con el índice y el veredicto de SC-001 a SC-008 (SC-004, SC-006 y la parte real de SC-007 como «pendiente del alumno»); actualizar `CODEMAP.md` (filas nuevas: orígenes CORS y middleware, `netlify.toml`, `config.json`, `check-dist.mjs`, pruebas, evidencias, README; línea de estado y fila en el historial de features); marcar las tareas hechas aquí; anotar en `bitacora.md` las preguntas aún abiertas y la lista «pendiente del alumno». La feature se detiene aquí a la espera de revisión (constitución §19, sin commits).
  - **Prueba**: cada SC con su fichero de evidencia; `CODEMAP.md` lista cada archivo nuevo (`ls` de cada ruta existe); `bitacora.md` actualizada.
  - **Cubre**: constitución §16; H2, M3 (parte); todos los SC.

## Pendiente del alumno (no son tareas activas)

Manuales; el agente deja las plantillas y el procedimiento. Los resultados se anotan en `docs/evidencias/despliegue-tunel/`.

- **P1** Crear/arrancar el túnel con nombre con su token (fuera de Git) y comprobar que su único destino es `http://localhost:8000`. (H3, A8, FR-012)
- **P2** Crear el sitio de Netlify, el dominio `observatorio.ssamuelfernandez.net`, el certificado y el CNAME en Cloudflare con el proxy desactivado. (G13, FR-015)
- **P3** `curl https://observatorio-api.ssamuelfernandez.net/api/salud` → 200 con el cuerpo del contrato. (SC-004)
- **P4** Abrir el panel público; recargar una ruta interna sin 404. (G13, US2.4)
- **P5** H1: móvil con datos móviles ve el panel con datos; captura con la URL visible. (H1, SC-006)
- **P6** Prueba 9: cerrar `cloudflared`; aviso y última lectura; captura con hora. (SC-006)
- **P7** Prueba 10: reabrir; recuperación en el siguiente refresco sin recargar; captura con hora. (SC-006)
- **P8** Retirar `compose.override.yaml` y recrear `postgres` antes de abrir el túnel; probar suspensión del PC si se quiere. (H4, FR-015)
- **P9** Marcar G13, H1 a H4 y F9 en el checklist cuando haya evidencia; decidir si adopta la «Propuesta de redacción».

## Dependencias y orden

- Bloque 1: T059 → T060; T061 en paralelo con T059/T060; T062 al final del bloque.
- Bloque 2: T063 y T064 en paralelo; T065 después de T064.
- Bloque 3: T066 necesita T060 y T061 (API recreada); T067 después de T066 (mismo `exposicion.md`).
- Bloque 4: T069 en paralelo con T068 y T070; T068 después de T064 (nota de desarrollo) y T067 (`.gitignore`).
- Bloque 5: T071 al final del código; T072 último.
- Los bloques 2 y 3 no dependen entre sí y pueden ir en cualquier orden tras el bloque 1.

## Trazabilidad

| ID | Tareas |
|---|---|
| F9 | T059 a T062, T071 |
| G13 | T063 a T065 |
| F10, F5 | T066, T067, T071 |
| A8 | T067 |
| H1 | T069, P5 |
| H2, H4 | T068, T072, P8 |
| H3 | T067, T068, T070 |
| G9 (prueba real), pruebas 9 y 10 | T069, P6, P7 |
