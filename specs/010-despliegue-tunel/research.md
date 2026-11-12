# Investigación: despliegue-tunel (010)

Decisiones de diseño con su porqué. Las de la fase de clarify (`spec.md`, «Clarifications») no se repiten salvo para aterrizarlas.

## D1. CORS con el middleware de FastAPI/Starlette, configurado en `create_app`

- **Decisión**: `CORSMiddleware` añadido en `api/main.py::create_app()` con `allow_origins` = lista de la variable, `allow_methods=["GET", "OPTIONS"]`, `allow_headers=["ngrok-skip-browser-warning"]`, `allow_credentials=False`. No se usa `allow_origin_regex` (solo orígenes exactos).
- **Porqué**: ya está en FastAPI (sin dependencias nuevas, constitución §11); `allow_credentials=False` hace que no salga `Access-Control-Allow-Credentials` (FR-003); un origen no listado no recibe `Access-Control-Allow-Origin` (US1.3).
- **Dónde se lee la lista**: en `create_app()` (al importar `api.main`), no en `lifespan`, porque los middleware se fijan antes de arrancar. Un valor inválido lanza `ConfigError` al importar y Uvicorn no arranca (FR-001, decisión D-3). Lógica pura en `common/api_config.py` (`parse_cors_origins`), sin FastAPI (constitución §14).
- **Alternativas**: regex para `*.netlify.app` (descartada: permitiría cualquier sitio de Netlify); cabeceras CORS escritas a mano (más código y más fallos que el middleware).

## D2. Variable `CORS_ALLOWED_ORIGINS`

- **Decisión**: orígenes separados por comas, cada uno `http://` o `https://` + host (+ puerto), sin barra final ni ruta; se recortan espacios y se ignoran vacíos por comas sobrantes. Defecto: `https://observatorio.ssamuelfernandez.net,http://localhost:4200`. Rechazo con `ConfigError` que nombra la variable si: algún elemento es `*`, no tiene esquema, lleva ruta o barra final, o la lista queda vacía tras limpiar.
- **Porqué el defecto está en código y en `compose.yaml`**: igual que `API_MAX_EVENTS` (007): `${CORS_ALLOWED_ORIGINS:-...}` en compose y `read_str(..., default)` en el código, para no obligar a editar `.env` en clones antiguos. Está también en `.env.example` (A10, `check_env_example.py`). No es secreto.
- **Una variable vacía** (`CORS_ALLOWED_ORIGINS=`): en Compose, `${...:-defecto}` trata el vacío como ausente y pasa el defecto al contenedor (spec, «Edge Cases»). En el código, `read_str` ya lanza `ConfigError` si llega vacía, así que no hace falta lógica propia; una prueba fija ambos comportamientos (ausente → defecto; vacío directo → `ConfigError`).
- **Origen temporal de Netlify** (FR-004): el alumno añade `https://<sitio>.netlify.app` a la variable en `.env` y ejecuta `docker compose up -d api`; al quitarlo, lo mismo.

## D3. `apiBaseUrl` incluye `/api`

- **Decisión** (ya tomada en clarify): `https://observatorio-api.ssamuelfernandez.net/api`. El cliente (`frontend/src/shared/api/client.ts`) hace `apiBaseUrl` sin barra final + `/eventos` etc. No se cambia el cliente.
- **Prueba** (FR-009): un test de vitest fija `setConfig` con esa URL, sustituye `fetch` por un doble y comprueba las tres URLs finales con `apiEvents`, `apiStats` y `apiHealth` (cliente real, no copia de la lógica). Otro test lee `frontend/public/config.json` y comprueba `mode = "api"`, la URL exacta, que `validateConfig` la acepta y que no contiene `/api/api`.
- **Consecuencia para desarrollo**: el `config.json` entregado apunta a la URL pública, así que `npm run dev` ya no usa el proxy de Vite salvo que se cambie `apiBaseUrl` a `/api` en local. Pregunta 7 de la spec (resuelta: se documenta en el README y en `frontend/README.md`).

## D4. `netlify.toml` en la raíz del repositorio

- **Decisión**: `[build]` con `base = "frontend"`, `command = "npm run build"`, `publish = "dist"` (relativo a `base`) y `[build.environment]` con `NODE_VERSION = "24.18.0"`; `[[redirects]]` con `from = "/*"`, `to = "/index.html"`, `status = 200`.
- **Coherencia con `.nvmrc`**: una prueba Python sin Docker (`tests/scripts/test_netlify_config.py`, con `tomllib`) comprueba los cinco valores y que `NODE_VERSION` coincide con `frontend/.nvmrc` (constitución §11).
- **Nota**: `03 §8.4` y `02` F11 decían `publish = frontend/dist`; con `base = "frontend"` en Netlify el directorio de publicación es relativo a la base, así que `dist` es lo correcto. Se corrige esa redacción al actualizar la planificación.

## D5. Comprobar que el build de producción no incluye el mock

- **Decisión**: `frontend/scripts/check-dist.mjs` (Node, sin dependencias) que, tras `npm run build`, recorre `dist/` y falla si encuentra (a) un fichero cuyo nombre coincida con los de `frontend/mock/*.json` o (b) en el JavaScript compilado, una cadena distintiva del mock (se fija al implementar mirando `mock/backend.ts` y los JSON, p. ej. un identificador sintético de `mock/base.json`). Comprueba además que `dist/config.json` es idéntico a `public/config.json`.
- **Porqué**: la exclusión ya existe (alias `@mock/backend`, G15) pero solo se había probado con el build; SC-003 pide un resultado medible repetible. Se ejecuta a mano y su salida va a evidencias; no se engancha al `build` (no se toca el flujo de Netlify).
- **Alternativa**: inspección manual con `grep` (sin repetibilidad); descartada.

## D6. Revisión de exposición: comandos, no código de aplicación

- **Decisión**: la revisión se hace con comandos (`curl`, `docker compose config`, `git`) contra la API local de Compose, que es la misma imagen que ve el túnel, y se guarda con los comandos y sus salidas en `docs/evidencias/despliegue-tunel/exposicion.md`. No se añade script de aplicación. Comprobaciones: las 3 rutas y que `/docs`, `/redoc`, `/openapi.json` dan 404; `POST`, `PUT`, `PATCH`, `DELETE` a las tres rutas dan 405 con cuerpo `{"error": ...}`; ninguna respuesta (200 y errores) contiene las contraseñas ni usuarios de BD de `.env` (búsqueda de los valores sin imprimirlos); una petición sin `limit` en un rango grande devuelve como mucho `API_MAX_EVENTS` eventos y `truncated`/`next_cursor` coherentes.
- **Puertos y `compose.override.yaml`**: la prueba de FR-013 se hace con `docker compose -f compose.yaml config`, que **ignora el override** automático y por tanto muestra lo que entrega el repo: solo `127.0.0.1:8000`. El `docker ps` real del equipo del alumno enseñará `127.0.0.1:5433` mientras exista el override local; no se borra (es un fichero local del alumno) y se anota como hallazgo local con la instrucción del README de retirarlo antes de abrir el túnel. Aun así el túnel solo apunta a `localhost:8000`, así que Postgres no es alcanzable por él.
- **Túnel**: no hay configuración de `cloudflared` en el repo (FR-012); la evidencia lo comprueba con `git ls-files` y la búsqueda de secretos. La comprobación del destino real del túnel (`http://localhost:8000` y nada más) es **pendiente del alumno** (captura del panel de Cloudflare o de `config.yml` con el token tapado).

## D7. `.gitignore` y secretos (FR-016)

- **Decisión**: añadir `.cloudflared/`, `cert.pem` y `cloudflared*.yml`/`cloudflared*.yaml` y `cloudflared-credentials*.json` junto al bloque de ngrok, que se mantiene (ngrok sigue siendo equivalente permitido). No se ignora `*.json` en general. SC-008: búsqueda de patrones de token y de ficheros de credenciales sobre lo añadido por la feature (`git ls-files -o --exclude-standard` y `git diff`).
- **Token**: el túnel con nombre se ejecuta con `cloudflared tunnel run` y credenciales locales o con token en variable de entorno de la sesión; en ningún caso en `.env.example`, compose ni README (en el README solo `<TOKEN>`).

## D8. Orden y mensajes del procedimiento de activación

- Orden (US5): 1 Compose (sin `compose.override.yaml`) → 2 API sana (`curl 127.0.0.1:8000/api/salud`) → 3 `cloudflared` → 4 `curl https://observatorio-api.ssamuelfernandez.net/api/salud` → 5 abrir el panel público → (replay de `009` opcional). Parada en orden inverso: cerrar `cloudflared`, luego `docker compose down` (sin `-v`).
- Decisiones (a), (b), (c) de FR-015 con una frase cada una y el aviso de que el panel se recompila (nuevo despliegue en Netlify) si cambia `config.json`.
- Comprobaciones previas a la defensa: suspensión del PC y reconexión del túnel; DNS (`nslookup`), certificado de Netlify, y probar también con el dominio por defecto de Netlify si el DNS no propaga.

## D9. Comportamiento de CORS en errores (límites conocidos)

- El preflight con método no permitido (`POST`) lo contesta el middleware con 400 de texto plano (no con el cuerpo común); no lleva `POST` en `Access-Control-Allow-Methods`. Es el comportamiento estándar y solo ocurre con navegadores ajenos al panel; se acepta como límite, no se personaliza.
- Un 500 no controlado queda fuera del middleware CORS (lo emite la capa exterior de Starlette) y no lleva `Access-Control-Allow-Origin`: el navegador lo ve como fallo de red, que el panel ya trata como fallo de la API (aviso y última lectura). No se corrige: `api/errors.py` ya devuelve el cuerpo común para casi todo y el panel no distingue.
- Una respuesta de error de pasarela del túnel (API apagada con el túnel abierto) tampoco tiene cabeceras CORS ni JSON del contrato; es el mismo caso de fallo de red y lo cubre la prueba 9.

## D10. Qué es automatizable y qué es del alumno

| Automatizable por el agente | Pendiente del alumno |
|---|---|
| CORS y sus pruebas; `netlify.toml` y su prueba; `config.json` y la prueba del cliente; build y `check-dist`; revisión de exposición local; README; plantillas; menciones | Token y arranque de `cloudflared`; sitio, dominio y certificado de Netlify; DNS; `curl` público (SC-004); H1 desde el móvil; pruebas 9 y 10 reales; comprobar el destino del túnel; origen temporal `netlify.app` si se usa |

## D11. Límites conocidos (una línea cada uno)

- El `config.json` entregado apunta a la API pública; el desarrollo con proxy exige un cambio local no versionado.
- Preflight rechazado y 500 sin cabeceras CORS (D9).
- La revisión de exposición se hace en local con la misma imagen; la parte del túnel real depende del alumno.
- No hay limitación de tasa ni autenticación (alcance cerrado, constitución §12).
