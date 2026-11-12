# Plan de implementación: despliegue-tunel (010)

**Rama**: `010-despliegue-tunel` | **Fecha**: 2026-11-12 | **Spec**: `specs/010-despliegue-tunel/spec.md`
**Requisitos**: F9, F10, F5, G13, H1 a H4, A8, G9 (prueba real), pruebas 9 y 10.

Solo documentos de diseño (constitución §19). Los contratos de `specs/001-contratos-y-modelo/contracts/` se citan, no se copian ni se modifican. Es trabajo de clase: se corrige lo que haga fallar un criterio de aceptación, contradiga un contrato o la constitución, o pierda datos; lo demás va como límite conocido de una línea.

## Resumen

La API pasa de local a pública por un Cloudflare Tunnel (`https://observatorio-api.ssamuelfernandez.net` → `http://localhost:8000`) y el panel se publica como sitio estático en Netlify (`https://observatorio.ssamuelfernandez.net`). Esta feature añade lo que falta en el repo: CORS acotado en la API (variable `CORS_ALLOWED_ORIGINS`), `netlify.toml`, `config.json` con la URL pública incluyendo `/api`, pruebas de CORS, del cliente real y del build sin mock, una revisión de exposición con evidencia, `.gitignore` para credenciales del túnel, el procedimiento de activación en el README y las plantillas de evidencia de H1 y de las pruebas 9 y 10. El túnel, Netlify y el DNS son pasos manuales del alumno.

Sin cambios de contrato, de esquema SQL, de Compose (ningún servicio nuevo) ni de `docs/enunciado/`. Decisiones y alternativas: `research.md` (D1 a D11).

## Technical Context

| Pieza | Valor |
|---|---|
| Lenguaje | Python 3.12.16 (API, `CORSMiddleware` de FastAPI/Starlette, sin dependencias nuevas); TypeScript/vitest y Node 24.18.0 en el panel |
| Almacenamiento | Ninguno nuevo |
| Pruebas | `pytest` sin Docker (`httpx` con `ASGITransport`, como `tests/api/test_errors.py`); `vitest` para el cliente; `check-dist.mjs` sobre `dist/`; `curl` contra Compose para la evidencia |
| Despliegue | Cloudflare Tunnel con nombre en el equipo del alumno (fuera de Compose); Netlify con `netlify.toml` |
| Restricciones | Una feature cada vez; sin servicios en Compose (FR-019); código nuevo con docstrings de `03 §7.4`, funciones de unas 30 líneas, archivos de 250 como máximo; token y credenciales fuera de Git |

## Constitución (comprobación)

| Principio | Cumple | Cómo |
|---|---|---|
| §7 Mock separado | Sí | `check-dist.mjs` demuestra que `dist/` no contiene el mock |
| §9 Nombres de servicio | Sí | Sin cambios entre contenedores; el túnel apunta al puerto publicado en el anfitrión |
| §10 Exposición y secretos | Sí | Solo `127.0.0.1:8000`; sin docs automáticos; sin token en repo; `.env.example` y compose con la variable nueva; `.gitignore` de credenciales |
| §11 Versiones fijadas | Sí | `NODE_VERSION` igual que `.nvmrc`, con prueba; sin dependencias nuevas |
| §12 Alcance cerrado | Sí | Sin autenticación, tasa, caché, WAF, endpoints nuevos ni contenedor de `cloudflared` |
| §13 Idioma | Sí | Identificadores en inglés; docstrings y documentación en español; `ngrok-skip-browser-warning` es nombre fijado por el contrato |
| §14 Una responsabilidad | Sí | Validación de orígenes pura en `common/api_config.py`; montaje del middleware en `api/main.py` |
| §15 Contratos únicos | Sí | CORS y cabecera se citan de `api.md` §1; no se copian |
| §16 Cierre | Sí | Pruebas ejecutadas, evidencias, README y `CODEMAP.md` (T072) |
| §17 Frontend sin estadísticas | Sí | El panel no cambia salvo `config.json` |
| §18 Enunciado de solo lectura | Sí | Lo que diga ngrok en enunciado, constitución y contratos no se toca |
| §19 Una feature cada vez | Sí | Implementar solo tras la revisión del alumno |
| §20 Commits | Sí | Sin commits ni trailers |

Resultado del gate: sin violaciones. Se repite tras el diseño: igual.

## Cambios por archivo (diseño)

### Código y configuración que cambian en la implementación

| Archivo | Cambio | Tarea |
|---|---|---|
| `common/api_config.py` | `DEFAULT_CORS_ORIGINS`, `parse_cors_origins`, `load_cors_origins` (puras salvo la lectura del entorno) | T059 |
| `api/main.py` | `create_app()` añade `CORSMiddleware` con la lista, `GET`/`OPTIONS`, la cabecera permitida y sin credenciales | T060 |
| `.env.example`, `compose.yaml` (servicio `api`) | variable `CORS_ALLOWED_ORIGINS` con defecto, sin secretos | T061 |
| `netlify.toml` (nuevo, raíz) | base, comando, publicación, Node, redirección SPA | T063 |
| `frontend/public/config.json` | `apiBaseUrl` = URL pública con `/api` | T064 |
| `frontend/scripts/check-dist.mjs` (nuevo) | comprobación del build sin mock y de `config.json` | T065 |
| `.gitignore` | credenciales de `cloudflared` | T067 |
| `README.md`, `frontend/README.md`, `docs/planificacion/02, 03, 04` | procedimiento de activación y sustitución de ngrok por «túnel (Cloudflare Tunnel)» | T068, T070 |

### Pruebas nuevas

`tests/common/test_api_config.py` (ampliado, orígenes), `tests/api/test_cors.py`, `tests/scripts/test_netlify_config.py`, `frontend/tests/apiUrl.test.ts`.

### Documentos y evidencias

`docs/evidencias/despliegue-tunel/` (salidas por tarea, `exposicion.md`, plantillas H1, 9 y 10, `README.md`); `CODEMAP.md`; `bitacora.md`. `frontend/README.md` recibe la nota de desarrollo con proxy y el uso de `check-dist.mjs` (T064, T065).

### Lo que NO cambia

Contratos, `docs/enunciado/`, constitución, esquema SQL, servicios de Compose, `frontend/src/` (cliente, validación y panel), `docs/planificacion/01-checklist-requisitos.md` (lo marca el alumno; pregunta 3), specs cerradas `002` y `007` (su texto sobre ngrok describe lo que se decidió entonces; no se reescribe).

## Flujo

```
navegador (panel en observatorio.ssamuelfernandez.net)
  -> GET https://observatorio-api.ssamuelfernandez.net/api/eventos   (preflight OPTIONS si lleva cabecera propia)
  -> Cloudflare Tunnel (HTTPS termina en Cloudflare) -> cloudflared en el PC -> http://localhost:8000
  -> contenedor api (CORSMiddleware: ¿Origin en la lista?) -> routers -> PostgreSQL (rol de solo lectura)
```

El panel envía la cabecera `ngrok-skip-browser-warning` solo si el cliente la añade; el preflight la admite por contrato.

## Verificación (resumen; detalle en `quickstart.md`)

Pruebas sin Docker y de vitest → build y `check-dist` → CORS con `curl` contra Compose → revisión de exposición → (alumno) túnel, panel público, H1, 9 y 10.

## Riesgos y límites

- **Desarrollo con proxy**: `config.json` entregado apunta a la URL pública (pregunta 7 de la spec).
- **Pasos manuales** (token, DNS, Netlify, móvil): SC-004, SC-006 y parte de SC-007 quedan «pendiente del alumno»; el agente no puede dar esos criterios por cumplidos.
- **`compose.override.yaml`** local publica Postgres en 5433: el README manda retirarlo antes del túnel; la evidencia estática usa `-f compose.yaml`.
- **Redacción de planificación**: 01 queda intacto; H3, G13 y H2 conservan la palabra ngrok hasta que el alumno adopte la propuesta de la spec.
