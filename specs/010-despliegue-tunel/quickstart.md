# Guía de validación: despliegue-tunel (010)

Pasos para comprobar la feature una vez implementada. Lo marcado **(alumno)** no lo puede hacer el agente. Resultados esperados en `spec.md` (SC-001 a SC-008). Cada salida se guarda en `docs/evidencias/despliegue-tunel/`.

## Requisitos previos

- `.env` copiado de `.env.example` (contraseñas de ejemplo cambiadas) y Docker en marcha.
- Node `24.18.0` (`frontend/.nvmrc`) y las dependencias del panel instaladas (`npm ci` en `frontend/`).
- Para la parte real: cuenta de Cloudflare con el túnel con nombre ya creado y DNS, y sitio de Netlify (alumno).

## 1. Pruebas sin Docker

```
.venv/Scripts/python.exe -m pytest -m "not integration" tests/common/test_api_config.py tests/api/test_cors.py tests/scripts/test_netlify_config.py
.venv/Scripts/python.exe scripts/check_env_example.py
cd frontend && npm test
```

Esperado: CORS 3 de 3 más los casos de rechazo (SC-001); `netlify.toml` coherente con `.nvmrc`; `check_env_example.py` con código 0; la prueba del cliente real con las 3 URLs sin `/api/api` (SC-002).

## 2. Build de producción sin mock

```
cd frontend
npm run build
node scripts/check-dist.mjs
```

Esperado: build sin errores; `dist/config.json` idéntico a `public/config.json` con `mode = "api"` y la URL pública; `check-dist` sin ficheros ni cadenas del mock (SC-003).

## 3. CORS contra la API de Compose

```
docker compose build producer
docker compose up -d api
curl -si -X OPTIONS http://127.0.0.1:8000/api/eventos -H "Origin: https://observatorio.ssamuelfernandez.net" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: ngrok-skip-browser-warning"
curl -si http://127.0.0.1:8000/api/salud -H "Origin: http://localhost:4200"
curl -si http://127.0.0.1:8000/api/salud -H "Origin: https://otro.example"
```

Esperado: 200 con `Access-Control-Allow-Origin` igual al origen enviado en los dos primeros, sin él en el tercero, y sin `Access-Control-Allow-Credentials` ni `*` (SC-001). Con `CORS_ALLOWED_ORIGINS=*` la API no arranca y el log nombra la variable.

## 4. Revisión de exposición

Comandos y tabla en `docs/evidencias/despliegue-tunel/exposicion.md` (rutas, 4 métodos de escritura con 405, sin secretos, límite, `docker compose -f compose.yaml config`). Esperado: SC-005. Si existe `compose.override.yaml` local, el `docker ps` real mostrará `127.0.0.1:5433`: se anota como hallazgo local y se retira antes de abrir el túnel.

## 5. Túnel y panel público (alumno)

Seguir «Procedimiento de activación» del README. Esperado: `curl https://observatorio-api.ssamuelfernandez.net/api/salud` responde 200 con el cuerpo del contrato (SC-004); el panel en `https://observatorio.ssamuelfernandez.net` muestra datos; recargar una ruta interna no da 404.

## 6. Pruebas desde fuera (alumno)

Plantillas en `docs/evidencias/despliegue-tunel/`: H1 (móvil con datos móviles), prueba 9 (cerrar `cloudflared`: aviso y última lectura) y prueba 10 (reabrir: recuperación en el siguiente refresco sin recargar), con capturas con la URL visible y la hora (SC-006).

## 7. Cierre

Búsqueda de secretos sobre lo añadido (SC-008), `CODEMAP.md` y README actualizados, `docs/evidencias/despliegue-tunel/README.md` con el veredicto de SC-001 a SC-008 (los del alumno, «pendiente»).
