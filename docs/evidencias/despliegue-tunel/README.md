# Evidencias de despliegue-tunel (010)

Cierre de la feature (T072), 2026-11-12. Todo lo marcado «Cumplido» está comprobado en local (API de Compose en `127.0.0.1:8000`, panel construido, pruebas automáticas). No se abrió ningún túnel ni se tocó Cloudflare, Netlify ni DNS: lo que depende de eso queda «pendiente del alumno».

## Índice

- Pruebas y salidas: `T059_api_config.txt`, `T060_cors.txt`, `T061_env.txt`, `T062_cors_curl.txt`, `T063_netlify.txt`, `T064_vitest.txt`, `T065_build_dist.txt`, `T066_respuestas.txt`, `T066_respuestas_brutas.txt`, `T066_limite_y_recuentos.txt`, `T067_puertos_secretos.txt`, `T068_readme.txt`, `T070_menciones.txt`, `T071_*.txt` (regresión).
- Revisión de exposición: [`exposicion.md`](exposicion.md).
- Plantillas del alumno: [`H1_movil.md`](H1_movil.md), [`prueba-09_cierre-tunel.md`](prueba-09_cierre-tunel.md), [`prueba-10_reapertura-tunel.md`](prueba-10_reapertura-tunel.md).
- Capturas en vivo (2026-11-12): **no se hicieron**. No había herramienta de navegador disponible (la conexión se cerró) y no se instaló nada. Quedan pendientes: el panel en `https://observatorio.ssamuelfernandez.net`, `/api/salud` y un fragmento de `/api/eventos` en la URL pública.
- Verificación en vivo (alumno, a mano): panel y API desplegados (Cloudflare Tunnel y Netlify) y el panel muestra datos reales.
- Pruebas 9 y 10: se verifican en vivo en la URL pública y su evidencia en vídeo irá en `readme-video`. Cualquier captura tomada desde la misma red del servidor no sustituye la prueba 9 desde fuera de la red (H1 con datos móviles sigue como captura pendiente).
- Apuntes de defensa: `docs/borradores/despliegue-tunel.md`.

## Veredicto de SC-001 a SC-008

| SC | Veredicto | Evidencia |
|---|---|---|
| SC-001 CORS 3 de 3 y 0 `Allow-Credentials`/`*` | Cumplido | `T060_cors.txt` (7 pruebas de CORS, 139 de `tests/api` y `common` en verde); `T062_cors_curl.txt` (curl real: origen público y `localhost:4200` con `access-control-allow-origin`, métodos `GET, OPTIONS`, cabecera `ngrok-skip-browser-warning`; origen no listado sin cabecera; `CORS_ALLOWED_ORIGINS=*` hace fallar el arranque con `ConfigError` que nombra la variable); `T059_api_config.txt` (18 pruebas) |
| SC-002 `dist/config.json` y URLs sin `/api/api` | Cumplido | `T064_vitest.txt` (73 pruebas, incluida `apiUrl.test.ts`); `T065_build_dist.txt` (`dist/config.json` idéntico a `public/config.json`) |
| SC-003 `dist/` sin mock, build con Node fijado | Cumplido | `T065_build_dist.txt` (6 ficheros revisados, 0 del mock, salida 0; negativa con `base.json` sale con 1); `T063_netlify.txt` (3 pruebas: `NODE_VERSION` igual a `frontend/.nvmrc`) |
| SC-004 `curl` público a `/api/salud` | **Pendiente del alumno** | Solo se comprobó en local (`T062_cors_curl.txt`, 200 en `127.0.0.1:8000`); la URL pública requiere túnel real |
| SC-005 exposición | Cumplido | `exposicion.md` y `T066_*`, `T067_puertos_secretos.txt`: 3 rutas con 200; `/docs`, `/redoc`, `/openapi.json` y rutas de administración con 404; 12 peticiones de escritura (4 métodos x 3 rutas) con 405 y total de datos sin cambios (18554); 0 coincidencias de secretos por patrones (desviación T066(3), sin leer `.env`); sin `limit`: 5000 eventos con `truncated` y `next_cursor`; `limit` mayor de 5000: 400; 1 único puerto publicado en `compose.yaml` (`127.0.0.1:8000`) |
| SC-006 H1, prueba 9 y prueba 10 con capturas | **Pendiente del alumno** | Plantillas listas; sin capturas |
| SC-007 README | Parcial: lectura cumplida, prueba real pendiente | `T068_readme.txt` (4 pasos de activación, comprobación pública, aviso de disponibilidad, apagado). Que una persona llegue al panel público con datos siguiendo solo el README exige túnel y Netlify reales: pendiente del alumno |
| SC-008 sin secretos | Cumplido | `T067_puertos_secretos.txt` y `exposicion.md` (fila c): 0 tokens ni ficheros de credenciales; `git check-ignore` reconoce los nombres nuevos del `.gitignore`; `git ls-files` sin `cloudflared`, `cert.pem` ni credenciales |

Regresión (T071): 776 pruebas unitarias, 73 de Vitest, 121 de integración de la API y `check_env_example.py` en verde; cinco servicios sanos (`T071_*.txt`).

## Hallazgos

- `compose.override.yaml` local del alumno publica PostgreSQL en `127.0.0.1:5433` (no entra en el repositorio; retirar antes de abrir el túnel).
- `limit` por encima de 5000 se rechaza con 400 en lugar de recortarse (contrato `api.md` §3.1).
- Límites de la spec: un 500 de la API no lleva cabeceras CORS; el preflight de `POST` devuelve 400.

## Pendiente del alumno

IDs del checklist: **con evidencia** F9, F10, F5, A8 (parte local: un único puerto publicado y revisión), G13 (parte local: `config.json`, build sin mock, `netlify.toml`; el despliegue real en Netlify queda pendiente); **pendientes** H1, pruebas 9 y 10, G9 (prueba real), H3 (token y destino del túnel), H4 y la parte real de H2.

Pasos P1 a P9 de `specs/010-despliegue-tunel/tasks.md`:

- P1 Token y arranque del túnel (`cloudflared`), con captura de su configuración y `http://localhost:8000` como único destino, token tapado.
- P2 Sitio, dominio y certificado de Netlify; CNAME `observatorio` en Cloudflare con el proxy desactivado.
- P3 `curl https://observatorio-api.ssamuelfernandez.net/api/salud` (SC-004).
- P4 Abrir el panel público y recargar una ruta interna sin 404.
- P5 H1: móvil con datos móviles, captura con la URL visible.
- P6 Prueba 9: cerrar el túnel, aviso y última lectura, con hora.
- P7 Prueba 10: reabrir el túnel, recuperación en el siguiente refresco sin recargar, con hora.
- P8 Retirar `compose.override.yaml` y recrear `postgres` antes de abrir el túnel.
- P9 Marcar el checklist con evidencia y decidir si adopta la propuesta de redacción de la spec.
