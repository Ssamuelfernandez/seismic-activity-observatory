# Pruebas de aceptación: apuntes para el README y el vídeo

Feature `012-pruebas-aceptacion`. Evidencias: `docs/evidencias/pruebas/` (resumen en `README.md`, una ficha por prueba).

## Estado de las 11 pruebas

| Prueba | Estado | Evidencia principal |
|---|---|---|
| 1 Evento nuevo | Real hasta PostgreSQL y API sintética; captura de panel pendiente del alumno | `docs/evidencias/pruebas/01-evento-nuevo.md`, `01_captura_pendiente.md` |
| 2 Reenvío | Completa (sintética) | `docs/evidencias/pruebas/02-reenvio.md` |
| 3 Versión posterior | SQL y API completas (sintéticas); captura: plantilla pendiente (datos sintéticos, no visibles en el panel público) | `docs/evidencias/pruebas/03-version-posterior.md`, `03_captura_pendiente.md` |
| 4 Versión tardía | Completa (sintética) | `docs/evidencias/pruebas/04-version-tardia.md` |
| 5 Magnitud nula | Sintética; captura de ND (mock) pendiente del alumno | `docs/evidencias/pruebas/05-magnitud-nula.md`, `05_captura_pendiente.md` |
| 6 Coordenadas inválidas | Completa (sintética) | `docs/evidencias/pruebas/06-coordenadas-invalidas.md` |
| 7 Evento marítimo | Sintética más feed real (28 de 181 sin país); captura pendiente del alumno | `docs/evidencias/pruebas/07-evento-maritimo.md`, `07_captura_pendiente.md` |
| 8 Reinicio del consumidor | Completa (real) | `docs/evidencias/pruebas/08-reinicio-consumidor.md` |
| 9 Cierre del túnel | Pendiente del alumno (solo revisión de código) | `docs/evidencias/pruebas/09-cierre-tunel.md`, `09-10_revision_codigo.txt` |
| 10 Reapertura del túnel | Pendiente del alumno (solo revisión de código) | `docs/evidencias/pruebas/10-reapertura-tunel.md` |
| 11 Reproducción histórica | Completa (real): `replay` 22 / 24 / 0, `live` intacto | `docs/evidencias/pruebas/11-reproduccion-historica.md` |

Con evidencia completa: 2, 3 (en SQL y API), 4, 6, 8 y 11. Con plantilla de captura pendiente: 1, 3, 5 y 7. Pendientes: 9 y 10.

## Qué contar en el vídeo

- Los casos que los datos reales no ofrecen (nulos, versión tardía, coordenadas inválidas) se inyectan sintéticos, etiquetados `synthetic-acc-*` y solo en base temporal; la huella de `live` no cambia (`00_live_antes.txt`, `00_live_despues.txt`).
- Suites: unitarias 829 passed más 3 fallos de entorno (`test_netlify_config.py`: el servicio `tests` no monta `netlify.toml` ni `frontend/.nvmrc`); integración 232 passed.
- Límites del panel para 9 y 10: el refresco es de 60 s más 15 s de timeout, así que el aviso y la recuperación tardan hasta unos 75 s; sin `refetchIntervalInBackground`, con la pestaña oculta el refresco puede detenerse; volver a la pestaña no fuerza refresco. El código conserva la última lectura y muestra «Datos antiguos» con su hora, pero no está demostrado en la URL pública.

## Filas para la tabla rúbrica→evidencia (M10)

La tabla aún no existe en el README (la hará `readme-video`). Aportación de esta feature:

| Criterio | Afirmación | Evidencia |
|---|---|---|
| Extracción | Un evento real llega hasta PostgreSQL y a la API | `docs/evidencias/pruebas/01-evento-nuevo.md` |
| Calidad | Cuarentena, nulos, versión tardía y evento marítimo comprobados | `docs/evidencias/pruebas/06-coordenadas-invalidas.md`, `05-magnitud-nula.md`, `04-version-tardia.md`, `07-evento-maritimo.md` |
| Modelado | Reenvío idempotente, versiones y reinicio sin duplicar efectos | `docs/evidencias/pruebas/02-reenvio.md`, `03-version-posterior.md`, `08-reinicio-consumidor.md` |
| Análisis | Los agregados cambian con la versión posterior; replay aislado de `live` | `docs/evidencias/pruebas/03-version-posterior.md`, `11-reproduccion-historica.md` |
| Reflexión | Sin evidencia todavía de esta feature | sin evidencia todavía |
