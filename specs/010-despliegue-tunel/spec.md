# Feature Specification: Despliegue con túnel — API pública por Cloudflare Tunnel y panel en Netlify

**Feature Branch**: `010-despliegue-tunel` (en `docs/planificacion/03-procedimiento-ejecucion.md` §4 figura como `015-despliegue-tunel`; se usa el nombre `despliegue-tunel`, el número es orientativo)

**Created**: 2026-11-12

**Status**: Draft (specify + clarify hechos; pendiente la revisión del alumno)

**Input**: Feature `despliegue-tunel` (F11): publicar la API de consulta por un túnel HTTPS y el panel como sitio estático, con CORS acotado, la configuración del panel apuntando a la API pública, una revisión de la exposición, el procedimiento de activación documentado y las evidencias de las pruebas 9 y 10. Datos ya decididos: API pública `https://observatorio-api.ssamuelfernandez.net` (Cloudflare Tunnel con nombre hacia `http://localhost:8000`, ya probado a mano); panel `https://observatorio.ssamuelfernandez.net` (Netlify con dominio propio; DNS en Cloudflare). El túnel ya no es ngrok: el enunciado permite «ngrok u otro servicio equivalente».

> Contratos de referencia, **sin modificar**: `specs/001-contratos-y-modelo/contracts/api.md` (§1: solo `GET` y `OPTIONS`; CORS y cabecera `ngrok-skip-browser-warning` según `CONTRATO-API.md`, sección «Acceso desde Netlify»; §3 límite y `truncated`). Esta spec no los repite: los cita. `docs/enunciado/` y `.specify/memory/constitution.md` no se tocan.

## Cobertura de requisitos

| ID | Qué cubre `despliegue-tunel` | Dónde se comprueba |
|---|---|---|
| F9 (☐) | CORS: orígenes exactos (panel público y `http://localhost:4200`), `GET` y `OPTIONS`, cabecera `ngrok-skip-browser-warning`, sin cookies | US1, FR-001 a FR-005, SC-001 |
| F10, F5 (ya [x]) | Se re-evidencian con la API ya publicada: sin rutas de administración ni de escritura, sin secretos en respuestas, límite activo | US3, FR-012, FR-013, SC-005 |
| G13 (☐) | `config.json` con la URL HTTPS pública **antes de compilar**; sin secretos en config; build y deploy OK | US2, FR-006 a FR-009, SC-002, SC-003 |
| H1 (☐) | Panel accesible desde otro dispositivo | US4, SC-006 |
| H2 (☐) | Procedimiento breve de activación en el README | US5, FR-014, FR-015, SC-007 |
| H3 (☐) | Túnel con el token fuera de Git y del frontend (texto reformulado, ver «Propuesta de redacción») | FR-016, SC-008 |
| H4 (☐) | Equipo, contenedores y túnel encendidos durante la demo | FR-015, SC-007 |
| G9 (parte de la prueba real) | Con la API caída el panel avisa y conserva la última lectura (ya implementado en `008`; aquí se prueba con el túnel real) | US4, SC-006 |
| A8 | Solo la API se expone; el túnel apunta solo al puerto 8000 | US3, FR-012, SC-005 |
| Prueba 9 | Cerrar el túnel: el panel muestra el fallo y conserva/identifica la última lectura | US4, FR-017, SC-006 |
| Prueba 10 | Reabrir el túnel: se recupera solo en el siguiente refresco | US4, FR-017, SC-006 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El navegador del panel público puede consultar la API (Priority: P1)

El panel servido desde su dominio público llama a la API pública y el navegador no lo bloquea. Un origen que no está en la lista no recibe permiso.

**Why this priority**: sin CORS correcto el panel desplegado no muestra nada, aunque la URL de la API abra (F9, obligatorio).

**Independent Test**: con la API en marcha, una petición `OPTIONS` (preflight) con `Origin: https://observatorio.ssamuelfernandez.net` y una petición `GET` con el mismo origen devuelven la cabecera de permiso para ese origen; con `Origin: https://otro.example` no la devuelven.

**Acceptance Scenarios**:

1. **Given** la API con la configuración por defecto, **When** llega un preflight `OPTIONS /api/eventos` con el origen del panel público, `Access-Control-Request-Method: GET` y `Access-Control-Request-Headers: ngrok-skip-browser-warning`, **Then** responde 200 con ese origen permitido, los métodos `GET` y `OPTIONS` y la cabecera `ngrok-skip-browser-warning` permitida.
2. **Given** lo mismo con el origen `http://localhost:4200`, **Then** también se permite.
3. **Given** un origen no listado (por ejemplo `https://otro.example`), **When** hace `GET` o preflight, **Then** la respuesta no lleva `Access-Control-Allow-Origin`.
4. **Given** cualquier respuesta CORS, **Then** no incluye `Access-Control-Allow-Credentials` (sin cookies) ni el comodín `*` como origen.
5. **Given** que el alumno añade temporalmente un origen `https://<sitio>.netlify.app` a la variable de orígenes y reinicia la API, **When** ese origen hace preflight, **Then** se permite sin cambiar código; al quitarlo de la variable, deja de permitirse.
6. **Given** un preflight con método no permitido (`POST`), **Then** no se concede ese método.

---

### User Story 2 - El panel desplegado se compila contra la API pública y no contiene el mock (Priority: P1)

El sitio estático se construye con una configuración que apunta a la URL HTTPS pública y funciona como aplicación de una sola página (recargar una ruta interna no da 404).

**Why this priority**: G13 es obligatorio; una `apiBaseUrl` mal compuesta (prefijo duplicado o ausente) hace que el panel pida rutas que no existen.

**Independent Test**: construir el panel de producción y comprobar que `dist/config.json` lleva `mode = "api"` y la URL pública, que ninguna petición del código compuesto se forma con `/api/api/`, y que `dist/` no contiene los datos ni el código del mock.

**Acceptance Scenarios**:

1. **Given** `frontend/public/config.json` con `mode = "api"` y la URL pública, **When** se construye con el comando de producción, **Then** `dist/config.json` es idéntico y el panel válida la configuración sin error.
2. **Given** el cliente HTTP del panel, que concatena `apiBaseUrl` con rutas como `/eventos`, `/estadisticas` y `/salud` (sin prefijo `/api`), **When** `apiBaseUrl` termina en `/api`, **Then** las URLs finales son `https://observatorio-api.ssamuelfernandez.net/api/eventos`, `/api/estadisticas` y `/api/salud`, sin duplicar el prefijo.
3. **Given** el build de producción, **Then** `dist/` no contiene los JSON sintéticos del mock ni la cadena del servidor simulado (el alias de producción apunta a un módulo que falla; constitución §7).
4. **Given** el despliegue en Netlify, **When** se recarga una ruta interna del panel, **Then** devuelve la aplicación (redirección de SPA con código 200), no un 404.
5. **Given** el repositorio, **Then** el fichero de configuración de Netlify fija directorio base, comando de build, directorio de publicación y versión de Node coherente con `frontend/.nvmrc`.

---

### User Story 3 - Revisión de lo que expone la API pública (Priority: P1)

Antes de publicar, se comprueba y se deja por escrito qué puede ver y hacer cualquiera que conozca la URL.

**Why this priority**: F10, F5 y A8 son obligatorios y la API pasa de local a pública; es el momento de re-evidenciarlos.

**Independent Test**: seguir la lista de comprobación de la evidencia contra la API pública (o local con la misma imagen) y obtener los resultados esperados en cada fila.

**Acceptance Scenarios**:

1. **Given** la API, **When** se enumeran sus rutas, **Then** solo existen `/api/salud`, `/api/eventos` y `/api/estadisticas`; no hay documentación automática (`/docs`, `/openapi.json`) ni rutas de administración.
2. **Given** las rutas existentes, **When** se prueba `POST`, `PUT`, `PATCH` y `DELETE`, **Then** responden 405 con el cuerpo de error común y no modifican datos.
3. **Given** las respuestas de los tres endpoints y de los errores, **Then** no contienen contraseñas, tokens ni nombres de usuario de base de datos, ni trazas internas.
4. **Given** una petición con `limit` por encima del máximo configurado (5 000) o sin `limit`, **Then** la respuesta no supera el máximo y marca `truncated` con `next_cursor` cuando procede.
5. **Given** el túnel, **Then** su configuración apunta solo al servicio local del puerto 8000; Postgres (5432) y Kafka (9092) no están publicados en el anfitrión ni alcanzables por el túnel (en el compose del repo; el `compose.override.yaml` local que publica Postgres en 5433 se desactiva antes de abrir el túnel).
6. **Given** el hallazgo de la revisión, **When** algo no cumple, **Then** se **reporta** en la evidencia; no se amplía el alcance para corregirlo salvo que sea un fallo de F9/F10/F5.

---

### User Story 4 - Probar desde fuera, cerrar y reabrir el túnel (Priority: P1)

El alumno comprueba que el panel desplegado funciona desde un móvil con datos y que sobrevive a un corte del túnel.

**Why this priority**: H1 y las pruebas 9 y 10 son obligatorias y requieren pasos manuales del alumno con la API real.

**Independent Test**: seguir la plantilla de evidencias: móvil con datos móviles abre el panel y ve datos; se cierra `cloudflared`, el panel muestra el aviso y conserva la última lectura marcada como antigua; se reabre y el siguiente refresco recupera los datos sin recargar.

**Acceptance Scenarios**:

1. **Given** el túnel y la API encendidos, **When** un móvil con datos móviles (no la red del PC) abre el panel público, **Then** carga y muestra eventos desde la API pública (H1).
2. **Given** el panel abierto, **When** se cierra el túnel (prueba 9), **Then** en el siguiente refresco muestra un aviso claro de fallo, identifica la última lectura con su hora y no la presenta como recién obtenida.
3. **Given** el túnel cerrado, **When** se reabre (prueba 10), **Then** en el siguiente refresco automático el panel vuelve a mostrar datos nuevos y quita el aviso, sin recargar la página.
4. **Given** las capturas, **Then** cada una muestra la URL visible en el navegador.

---

### User Story 5 - Procedimiento de activación en el README (Priority: P2)

Quien prepara la defensa sigue un procedimiento corto y reproducible, y conoce las limitaciones del túnel.

**Why this priority**: H2, H4 y M3; depende de que lo anterior funcione.

**Independent Test**: una persona que solo lee el README llega, en el orden indicado, a ver el panel público con datos y sabe cómo apagarlo todo.

**Acceptance Scenarios**:

1. **Given** el README, **When** se sigue el apartado «Procedimiento de activación», **Then** el orden es Compose → API → `cloudflared` → comprobación de `/api/salud` por la URL pública → panel; y la parada tiene su propio orden.
2. **Given** el apartado, **Then** avisa de que la API pública solo existe mientras `cloudflared` y la API estén encendidos en el PC del alumno.
3. **Given** el apartado, **Then** recoge las decisiones propias (a), (b), (c) del brief y los pasos manuales de DNS y Netlify, sin ningún token real.

---

### Edge Cases

- El origen llega con barra final o con otro puerto (`http://localhost:4200/`, `http://localhost:3000`): no coincide con el origen exacto y no se permite (el navegador nunca envía barra final; se documenta el formato esperado en la variable).
- La variable de orígenes está vacía o ausente: se aplican los dos orígenes por defecto del brief; un valor con comodín `*` como origen único se rechaza al arrancar (decisión D-3 de Clarifications).
- `*.netlify.app` temporal: se añade el origen exacto del sitio de previsualización, no un patrón; se retira al terminar.
- El túnel está abierto pero la API apagada: el panel recibe un error de pasarela del servicio de túnel (no JSON del contrato) y debe tratarlo como fallo de la API (aviso y última lectura), no como dato.
- Petición del navegador sin cabecera `Origin` (curl, comprobaciones de salud): se atiende normal; CORS solo afecta a navegadores.
- `apiBaseUrl` con barra final: el cliente ya la recorta; la configuración documentada no la lleva.
- Cuenta de Cloudflare o Netlify caída, o DNS sin propagar: no se resuelve en código; el README indica cómo comprobar con `curl` la URL pública y con el dominio de Netlify por defecto.
- El PC se suspende o cambia de red: el túnel se reconecta solo al volver la red; se anota en el README como comprobación previa a la defensa.

### Límites conocidos (una línea cada uno)

- La API es pública y de solo lectura: cualquiera con la URL puede consultarla; CORS no es una barrera de seguridad, solo decide qué páginas pueden leerla desde un navegador.
- No hay autenticación, limitación de tasa ni caché propios (fuera de alcance, como en `007-api`).
- La disponibilidad del túnel depende de que el PC y `cloudflared` estén encendidos; no hay alta disponibilidad.
- El panel solo se puede probar de extremo a extremo con los pasos manuales del alumno (sitio Netlify, DNS, token del túnel).

## Requirements *(mandatory)*

### Functional Requirements

**CORS (F9)**

- **FR-001**: La API MUST aplicar CORS con una lista de orígenes exactos leída de una variable de entorno, con valor por defecto `https://observatorio.ssamuelfernandez.net` y `http://localhost:4200`.
- **FR-002**: La API MUST permitir solo los métodos `GET` y `OPTIONS` y la cabecera de petición `ngrok-skip-browser-warning` (se mantiene aunque el túnel ya no sea ngrok: lo exige el contrato y el panel puede enviarla).
- **FR-003**: Las respuestas CORS MUST NOT llevar `Access-Control-Allow-Credentials` ni permitir `*` como origen (sin cookies, enunciado §9).
- **FR-004**: Debe poder añadirse temporalmente un origen exacto `https://<sitio>.netlify.app` solo editando la variable y reiniciando la API, sin tocar código.
- **FR-005**: La nueva variable MUST estar en `.env.example` y en `compose.yaml` con valor por defecto, sin secretos (constitución §10), y pasar `scripts/check_env_example.py`. No se cambian las rutas, los cuerpos ni los códigos de `api.md`.

**Panel y build (G13)**

- **FR-006**: `frontend/public/config.json` MUST tener `mode = "api"` y `apiBaseUrl` apuntando a la URL pública HTTPS de la API **incluyendo el prefijo `/api`** (ver Clarifications), sin barra final ni secretos.
- **FR-007**: El fichero de configuración de Netlify MUST fijar directorio base `frontend`, comando `npm run build`, directorio de publicación `dist`, la versión de Node de `frontend/.nvmrc` y la redirección de SPA `/* /index.html 200`.
- **FR-008**: El build de producción MUST NOT incluir el mock (JSON sintéticos ni servidor simulado) en `dist/` (constitución §7; G15 ya implementado, se re-comprueba).
- **FR-009**: Las URLs finales que forma el panel MUST ser `<apiBaseUrl>/eventos`, `/estadisticas` y `/salud` sin duplicar `/api`; se comprueba con una prueba que use el cliente real.

**Exposición (F10, F5, A8)**

- **FR-010**: Debe existir una revisión escrita con evidencia (comandos y resultados) de: rutas existentes, rechazo de métodos de escritura (405), ausencia de secretos en respuestas, límite de resultados activo y puertos publicados.
- **FR-011**: La revisión MUST reportar sus hallazgos; no se añaden endpoints, autenticación ni limitación de tasa (alcance cerrado, constitución §12).
- **FR-012**: El túnel MUST exponer solo `http://localhost:8000`. La configuración del túnel que viva en el repo (si la hay) no contiene token; el token vive solo en la máquina del alumno.
- **FR-013**: `docker compose config` MUST mostrar publicado en el anfitrión únicamente `127.0.0.1:8000`.

**Documentación y evidencias (H2, H3, H4)**

- **FR-014**: El README MUST incluir el apartado «Procedimiento de activación» con el orden Compose → API → `cloudflared` → panel, comprobación de `/api/salud` por la URL pública, apagado y el aviso de disponibilidad (US5).
- **FR-015**: El apartado MUST documentar las decisiones propias: (a) Cloudflare Tunnel con dominio propio (URL estable, sin página intermedia de aviso ni cuota mensual de peticiones; ngrok es equivalente); (b) API pública y de solo lectura (panel estático llama directo, datos públicos de USGS, CORS no es barrera de seguridad); (c) pasos manuales de DNS y Netlify (CNAME `observatorio` hacia el sitio de Netlify, proxy de Cloudflare desactivado, dominio personalizado y certificado en Netlify). Incluye que el panel debe recompilarse si cambia `config.json`.
- **FR-016**: Ningún token, authtoken, credencial ni `.env` real MUST entrar en el repo ni en el frontend. `.gitignore` MUST cubrir los ficheros de credenciales de `cloudflared` además de los de ngrok ya cubiertos.
- **FR-017**: `docs/evidencias/despliegue-tunel/` MUST contener: plantillas para las pruebas 9 y 10 y para H1 con espacio para capturas con URL visible; la salida de las pruebas de CORS; y la revisión de exposición. Lo que solo puede hacer el alumno queda marcado «pendiente del alumno».
- **FR-018**: Las menciones a ngrok que sean redacción propia (`docs/planificacion/02`, `03` y `04`, `CODEMAP.md`, README) MUST pasar a «túnel (Cloudflare Tunnel)» o equivalente donde proceda, con cambios mínimos. NO se editan `.specify/memory/constitution.md`, `specs/001-contratos-y-modelo/contracts/`, `docs/enunciado/`, `docs/planificacion/01-checklist-requisitos.md` (lo marca el alumno; pregunta 3) ni las specs ya cerradas `002` y `007` (describen lo decidido entonces); lo que ahí diga ngrok se anota en «Preguntas para el alumno».
- **FR-019**: Al cerrar la feature MUST actualizarse `CODEMAP.md` y el README (constitución §16). La feature MUST NOT añadir servicios a Compose ni ampliar el alcance.

### Propuesta de redacción (sin editar el checklist; el alumno decide si la adopta)

- **H3 reformulado**: «Túnel HTTPS (Cloudflare Tunnel con nombre; ngrok u otro servicio equivalente según el enunciado) que expone solo `http://localhost:8000`; el token o authtoken del túnel queda fuera de Git y del frontend».
- **G13**: «`config.json` con la URL HTTPS pública del túnel (incluido el prefijo `/api` si el cliente no lo añade) antes de compilar; sin secretos».
- **F9**: «origen exacto del panel público + `http://localhost:4200`…» (ya vale; solo cambia la explicación de que la cabecera de ngrok se mantiene por contrato).
- **H2**: «… Compose → API → túnel → comprobación de `/api/salud` pública → panel → replay».

### Key Entities

- **Lista de orígenes permitidos**: orígenes exactos que pueden leer la API desde un navegador; configurable por entorno.
- **Configuración del panel** (`config.json`): modo y URL base de la API, fijada antes de compilar.
- **Túnel**: canal HTTPS público hacia `localhost:8000`, con vida ligada a `cloudflared` y la API.
- **Evidencia de despliegue**: capturas y salidas que prueban H1, 9 y 10 y la exposición.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las pruebas de CORS dan 3 de 3: preflight del origen del panel público (200 con origen, métodos y cabecera permitidos), origen `http://localhost:4200` permitido, origen no listado sin cabecera de permiso; y 0 respuestas con `Allow-Credentials` o `*`.
- **SC-002**: El panel de producción construido tiene en `dist/config.json` modo `api` y la URL pública; la prueba del cliente real genera las 3 URLs finales sin `/api/api` y la validación de configuración las acepta.
- **SC-003**: `dist/` contiene 0 ficheros del mock; el build de producción termina sin errores con la versión de Node fijada.
- **SC-004**: `curl https://observatorio-api.ssamuelfernandez.net/api/salud` responde 200 con el cuerpo del contrato mientras el túnel y la API están encendidos (pendiente del alumno con el túnel real).
- **SC-005**: La revisión de exposición lista 3 rutas, 4 métodos de escritura rechazados con 405, 0 secretos en las respuestas revisadas, una respuesta sin `limit` con como máximo 5 000 eventos y exactamente 1 puerto publicado en el anfitrión (`127.0.0.1:8000`).
- **SC-006**: Con las capturas de la plantilla (URL visible) quedan registradas H1 (móvil con datos móviles ve el panel), prueba 9 (aviso y última lectura al cerrar) y prueba 10 (recuperación en el siguiente refresco, sin recargar), cada una con la hora (pendiente del alumno).
- **SC-007**: Una persona que siga solo el README levanta el entorno y llega al panel público con datos en el orden documentado, y sabe apagarlo; el apartado tiene los 4 pasos de activación, el de comprobación y el aviso de disponibilidad.
- **SC-008**: Una búsqueda de secretos sobre lo añadido por la feature (patrones de token, `.env`, ficheros de credenciales del túnel) da 0 resultados.

## Assumptions

- La API actual de `007-api` ya implementa los tres endpoints, el límite configurable y los errores comunes; no tiene CORS (se añade aquí).
- El panel de `008-panel-base-mock` ya trae G7/G9 (aviso y última lectura), el refresco automático, la validación de `config.json` y el alias que excluye el mock en producción.
- El túnel de Cloudflare con nombre ya existe y fue probado a mano contra `http://localhost:8000`; su creación, el token y los registros DNS son pasos manuales del alumno y no los hace el agente.
- `frontend/.nvmrc` fija Node `24.18.0`; el fichero de Netlify lo reutiliza.
- El dominio del panel se configura en Netlify y en DNS (CNAME, proxy desactivado) a mano.
- Fuera de alcance: autenticación, limitación de tasa, caché, WAF de Cloudflare, nuevos endpoints, contenedor para `cloudflared`, cambios de contratos, panel de calidad, alta disponibilidad.

## Clarifications

### Session 2026-11-12

- Q: ¿Cómo debe quedar `apiBaseUrl`, con o sin `/api`? → A: Con `/api` (`https://observatorio-api.ssamuelfernandez.net/api`). El cliente del panel concatena `apiBaseUrl` con `/eventos`, `/estadisticas`, `/salud` (rutas sin prefijo), por lo que el prefijo `/api` de la API tiene que estar en la base. Hoy vale `/api` porque el proxy de Vite lo reenvía; en producción no hay proxy. Una prueba del cliente real lo fija (FR-009). El brief suponía que el panel añadía `/api/...`; la comprobación del código dice lo contrario y no hace falta cambiar el cliente.
- Q: ¿Cómo se configura la lista de orígenes? → A: Variable `CORS_ALLOWED_ORIGINS`, orígenes exactos separados por comas, con valor por defecto los dos del brief. El nombre es propuesta (decisión de diseño menor; se confirma en el plan).
- Q: ¿Se mantiene la cabecera `ngrok-skip-browser-warning` si el túnel ya no es ngrok? → A: Sí. Lo exige el contrato (`CONTRATO-API.md` y `api.md` §1, que no se pueden cambiar) y no cuesta nada; el panel puede enviarla y debe pasar el preflight.
- Q: ¿Qué se acepta como valor de la variable? → A: Orígenes exactos con esquema y sin barra final; `*` aislado no se acepta (el arranque falla con mensaje claro, coherente con «sin cookies» y origen exacto). Un origen `*.netlify.app` temporal se añade como origen exacto del sitio de previsualización, no como patrón.
- Q: ¿La API pública requiere autenticación? → A: No. Es de solo lectura y sus datos son públicos de USGS; CORS no es seguridad. Es la decisión (b) del brief; se documenta en el README.
- Q: ¿Qué hace el agente y qué el alumno? → A: El agente deja CORS, `netlify.toml`, `config.json`, README y plantillas de evidencia y ejecuta las pruebas locales. El alumno crea/enciende el túnel y su token, el sitio y dominio de Netlify, el DNS, las capturas desde el móvil y las pruebas 9 y 10 reales. Todo lo manual queda marcado «pendiente del alumno».

### Preguntas para el alumno

Todas **Resueltas** por el supervisor (decisiones en `docs/evidencias/sprint/decisiones.md`, filas `despliegue-tunel`). El alumno puede revisarlas en la revisión final.

1. **Ediciones fuera de `specs/`**: **Resuelta**. Ediciones de código limitadas a CORS en la API, `config.json`, `netlify.toml`, `.gitignore` y README, hechas en implementación tras revisar plan y tareas.
2. **Menciones a ngrok en textos que no son nuestros**: **Resuelta**. `contracts/api.md` (línea 15, remite a `CONTRATO-API.md`), la constitución y `docs/enunciado/` no se editan; el README dice «ngrok u otro equivalente». Si el profesor exigiera ngrok literal, se consultaría según la constitución §18.
3. **Texto del checklist (H3, G13, H2)**: **Resuelta**. No se edita `01-checklist-requisitos.md`; el texto reformulado vive en esta spec y el alumno marca las casillas con evidencia.
4. **Nombre y número de la feature**: **Resuelta**. Carpeta real `010`; se alinea el texto de `03 §4` y `02` F11 (nota «carpeta real `010`»); no se renombra la carpeta.
5. **`compose.override.yaml` local con Postgres en 5433**: **Resuelta**. No se toca; el procedimiento manda desactivarlo antes de abrir el túnel y la evidencia de puertos usa `docker compose -f compose.yaml config`.
6. **Nombre de la variable de orígenes y dominio del panel**: **Resuelta**. `CORS_ALLOWED_ORIGINS` (orígenes exactos, `*` hace fallar el arranque, sin Allow-Credentials); dominio `https://observatorio.ssamuelfernandez.net` sin `www`.
7. **`config.json` entregado y desarrollo con proxy**: **Resuelta**. `config.json` apunta a la URL pública (con `/api`); `npm run dev` deja de usar el proxy y se documenta en `frontend/README.md` y en el README poner `/api` solo en local sin commitearlo. `localhost:4200` ya está permitido por CORS.

### Límites conocidos

- Un error 500 de la API no lleva cabeceras CORS: el navegador lo muestra como fallo de red, no como error HTTP.
- El preflight `OPTIONS` de una ruta con método `POST` devuelve 400 (la API es de solo lectura, no hay POST publicados).
- Las pruebas 9 (túnel cerrado) y 10 (móvil real) y la hipótesis H1 son solo manuales: las ejecuta el alumno («pendiente del alumno»).
- `contracts/api.md`, `CONTRATO-API.md` y el enunciado siguen citando ngrok; no se editan (pregunta 2).
