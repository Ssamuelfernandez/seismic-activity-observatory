# Despliegue con túnel: apuntes para la memoria y la defensa

Feature `010-despliegue-tunel`. Evidencias: `docs/evidencias/despliegue-tunel/`.

## Qué se hizo (comprobado en local)

- CORS en la API (`common/api_config.py`, `api/main.py`): orígenes exactos de `CORS_ALLOWED_ORIGINS`, solo `GET` y `OPTIONS`, cabecera `ngrok-skip-browser-warning`, sin credenciales; `*` impide arrancar.
- `frontend/public/config.json` con `mode = "api"` y la URL pública con `/api`; `netlify.toml`; `frontend/scripts/check-dist.mjs` (el build no lleva mock).
- Revisión de exposición con comandos y resultados, y procedimiento de activación en el README.

## Decisiones

- **(a) Cloudflare Tunnel con dominio propio** en lugar de ngrok: URL estable, sin página intermedia de aviso ni cuota de peticiones. El enunciado permite «ngrok u otro servicio equivalente». La cabecera de ngrok se mantiene en CORS porque la exige el contrato.
- **(b) API pública y de solo lectura**: el panel estático llama directamente a la API; los datos son públicos de USGS. No hay autenticación, limitación de tasa ni caché (fuera de alcance).
- **(c) Pasos manuales** de DNS (CNAME `observatorio`, proxy desactivado) y Netlify (dominio y certificado): los hace el alumno; el token del túnel vive solo en su máquina.
- `apiBaseUrl` lleva `/api`: el cliente concatena con `/eventos`, `/estadisticas` y `/salud`; antes funcionaba solo por el proxy de Vite. Lo fija una prueba con el cliente real.
- `publish = "dist"` relativo a `base = "frontend"` (se corrigió el texto de 02 y 03 §8.4).
- Evidencia de puertos con `docker compose -f compose.yaml config`, porque el override local publica Postgres en 5433.

## CORS no es una barrera de seguridad

CORS solo decide qué páginas pueden leer la respuesta desde un navegador; `curl` o cualquier script con la URL consulta la API igual. La protección real es que la API es de solo lectura (405 en escritura, 12 de 12 comprobadas), no publica `/docs` ni rutas de administración, no devuelve secretos, limita a 5000 eventos y solo se expone el puerto 8000.

## Exposición y límites

- Un único puerto publicado (`127.0.0.1:8000`); Postgres y Kafka no.
- Hallazgo local: el override del alumno publica Postgres en 127.0.0.1:5433; se retira antes de abrir el túnel.
- `limit` > 5000 devuelve 400 (no recorta en silencio).
- Un 500 no lleva cabeceras CORS: el navegador lo ve como fallo de red. El preflight de `POST` devuelve 400.
- Revisión de secretos por patrones genéricos, sin leer `.env` (desviación T066(3)).
- La disponibilidad depende de que el PC, la API y `cloudflared` estén encendidos; sin alta disponibilidad.

## Qué es del alumno (no comprobado)

Token y arranque del túnel, sitio, dominio y certificado de Netlify, DNS, `curl` público (SC-004), H1 desde móvil, pruebas 9 y 10 reales (SC-006) y la captura del destino del túnel. Plantillas en `docs/evidencias/despliegue-tunel/`.

## Posibles preguntas

- ¿Por qué no `*` en CORS? Orígenes exactos y sin cookies; `*` se rechaza al arrancar.
- ¿Por qué sigue la cabecera de ngrok si el túnel es otro? Lo exige el contrato y no cuesta nada.
- ¿Qué pasa si se cae el túnel? El panel avisa y conserva la última lectura (G9, implementado en `008`); la prueba real es la 9.
