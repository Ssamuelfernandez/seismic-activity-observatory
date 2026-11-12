# Evidencias de despliegue-tunel (010)

Índice inicial. El veredicto de SC-001 a SC-008 se añade al cerrar la feature.

## Índice

- Pruebas y salidas: `T059_*` a `T067_*` (`.txt`), `T068_readme.txt`, `T070_menciones.txt`.
- Revisión de exposición: [`exposicion.md`](exposicion.md).
- Plantillas del alumno: [`H1_movil.md`](H1_movil.md), [`prueba-09_cierre-tunel.md`](prueba-09_cierre-tunel.md), [`prueba-10_reapertura-tunel.md`](prueba-10_reapertura-tunel.md).

## Pendiente del alumno

- Token y arranque del túnel (`cloudflared`).
- Sitio, dominio y certificado de Netlify.
- DNS (CNAME `observatorio`, proxy desactivado).
- `curl` público a `/api/salud` (SC-004).
- H1 (móvil con datos móviles).
- Pruebas 9 y 10.
- Captura de la configuración del túnel con `http://localhost:8000` como único destino, con el token tapado.
