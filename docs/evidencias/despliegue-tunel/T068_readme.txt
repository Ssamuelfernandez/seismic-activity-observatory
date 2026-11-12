# T068: README, procedimiento de activación
## grep -n -i -E 'token|authtoken' README.md
174:3. **`cloudflared`.** Con el túnel con nombre ya creado en tu cuenta, ejecútalo en el equipo, por ejemplo `cloudflared tunnel run --token <TOKEN>`. El token (marcador `<TOKEN>` en esta documentación) vive **solo e
191:| Token y arranque del túnel, sitio y dominio de Netlify, DNS, `curl` público, H1, pruebas 9 y 10 | Pendiente del alumno (plantillas en `docs/evidencias/despliegue-tunel/`) |

## grep -n ngrok README.md
166:- **(a) Cloudflare Tunnel con dominio propio.** La API queda en una URL estable (`https://observatorio-api.ssamuelfernandez.net`), sin página intermedia de aviso y sin la cuota mensual de peticiones (20 000 al mes) 

## patrones de token real (esperado: 0)
0

## pasos y comprobacion presentes
17:| `api` | Implementada y verificada (2026-11-05), pendiente de la revisión del alumno: API de consulta de solo lectu
39:| [`api/`](api/) | API FastAPI de consulta, solo lectura: `/api/eventos`, `/api/estadisticas` y `/api/salud` |
96:curl http://127.0.0.1:8000/api/salud                  # {"status":"ok","last_ingestion":null,"generated":...}
170:**Orden de arranque.**
172:1. **Compose.** Antes de abrir el túnel, retira `compose.override.yaml` si existe (publica Postgres en `127.0.0.1:5
173:2. **API sana.** `curl http://127.0.0.1:8000/api/salud` devuelve 200 con `status`, `last_ingestion` y `generated`.
174:3. **`cloudflared`.** Con el túnel con nombre ya creado en tu cuenta, ejecútalo en el equipo, por ejemplo `cloudfl
175:4. **Comprobación por la URL pública.** `curl https://observatorio-api.ssamuelfernandez.net/api/salud` debe devolv
176:5. **Panel público.** Abre `https://observatorio.ssamuelfernandez.net`; debe mostrar datos y recargar una ruta inte
180:**Aviso de disponibilidad.** La URL pública de la API **solo existe mientras `cloudflared` y la API están encendid
318:| `GET /api/salud` | `status`, `last_ingestion` y `generated` |
332:curl http://127.0.0.1:8000/api/salud
