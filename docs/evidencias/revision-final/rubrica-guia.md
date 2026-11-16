# Comprobación de `docs/rubrica-y-guia-video.md` (revision-final, T133)

> **Documento histórico del 2026-11-15.** Comprobó la versión anterior de la guía, que desde entonces se ha reescrito. La guía vigente es [`docs/rubrica-y-guia-video.md`](../../rubrica-y-guia-video.md), a fecha 2026-11-16; lo que dice este archivo sobre el estado de la guía ya no es aplicable.

Fecha: 2026-11-15. Solo lectura: el documento **no se ha modificado** (`git diff docs/rubrica-y-guia-video.md` vacío). Regla de la feature: se corrige únicamente lo que deje un [OBL] sin evidencia; lo demás queda como pendiente no bloqueante (también anotado en `specs/013-revision-final/spec.md`, «Pendientes no bloqueantes»). Comprobación de rutas: cada ruta citada se resolvió contra el disco y contra `git ls-files`; los nombres cortos (`costes.md`, `tablas.md`…) se resolvieron en `docs/evidencias/mediciones/`. Estado de cada prueba: `docs/evidencias/pruebas/README.md` y `auditoria.md`.

Resultado global: **ninguna ruta citada apunta a una evidencia inexistente o sin versionar**; hay dos rutas con el directorio equivocado, varias cifras y frases anteriores al estado final y una ausencia (comparación en replay). Ninguna deja un [OBL] sin evidencia, así que no se corrige nada.

## Una fila por criterio de la rúbrica

| Criterio | Hallazgo | Ruta | Acción |
|---|---|---|---|
| Extracción | Coherente con las evidencias: histórico 18 302 únicos, manifiesto, catálogo de 177 países, apuntes B2/B11/B12 y B18. La cifra «54 exclusiones» es del 13-nov; hoy `live.exclusion` tiene 95 (el productor sigue ingiriendo) | `data/historical/manifest.json`; `docs/borradores/productor-live.md`; `docs/borradores/historico-2025.md`; `docs/evidencias/productor-live/ciclo1_consultas.out` | Ninguna. No bloqueante: actualizar la cifra si se cita en el vídeo |
| Calidad | El documento dice que el análisis de las 6 dimensiones no está escrito. Es cierto para la memoria §4, pero desde esta feature existe el análisis sobre datos reales; el texto del documento (§2, §3.1 y §5.1) queda desactualizado | `docs/evidencias/revision-final/calidad-live.md`; `docs/memoria.md` (§4) | No bloqueante: pasar `calidad-live.md` a la memoria §4 (lo decide el alumno) y actualizar §2/§3 del documento después |
| Modelado | Coherente: memoria §5, `indices.md` y pruebas 2, 3, 4, 6, 8 y 11 con evidencia existente y versionada | `docs/memoria.md` (§5); `docs/evidencias/mediciones/indices.md`; `sql/001_schema.sql` | Ninguna |
| Análisis | Coherente: la memoria §6 sigue vacía (confirmado, la sección no tiene texto) y no hay conclusiones escritas; las cifras candidatas (sin país, comparación 24 h, distribuciones) existen en la API | `docs/memoria.md` (§6); `docs/evidencias/api/recorrido_08_estadisticas.txt`; `docs/evidencias/api/T016_pytest_api_comparison.txt` | No bloqueante: redactar ≥3 conclusiones (alumno) |
| Reflexión | Coherente: `tablas.md`, `escalado.md`, `costes.md`, `equipo.md`, `transferencia.md` y la auditoría del verificador existen y están versionados | `docs/evidencias/mediciones/`; `docs/evidencias/subagentes/verificador-auditoria-mediciones-costes.md` | Ninguna |

## Una fila por prueba citada (§4.3)

| Prueba | Hallazgo | Ruta | Acción |
|---|---|---|---|
| 1 Evento nuevo | Correcto: figura con «Falta la captura de API, mapa y análisis» | `docs/evidencias/productor-live/prueba1_evento_nuevo.out`; `docs/evidencias/pruebas/01_captura_pendiente.md` | Ninguna (captura pendiente del alumno) |
| 2 Reenvío | Ruta `consumidor-idempotente/prueba2_reenvio.out` existe y está versionada | `docs/evidencias/consumidor-idempotente/prueba2_reenvio.out` | Ninguna |
| 3 Versión posterior | Ruta existe. El documento no la marca como pendiente de captura; la auditoría la da como parcial (SQL y API observados, captura sin hacer; los datos son sintéticos y no se ven en el panel público) | `docs/evidencias/consumidor-idempotente/prueba3_4_versiones.out`; `docs/evidencias/pruebas/03_captura_pendiente.md` | No bloqueante: añadir «captura pendiente (sintética)» a la fila |
| 4 Versión tardía | Correcto («Ídem» a la 3) | `docs/evidencias/consumidor-idempotente/prueba3_4_versiones.out` | Ninguna |
| 5 Magnitud nula | Correctamente pendiente de captura y sin nulos reales. **Ruta con directorio equivocado**: cita `consumidor-idempotente/geografia_prueba5.out`; el archivo está en `geografia-pais/` | `docs/evidencias/geografia-pais/geografia_prueba5.out` | No bloqueante: corregir el directorio (la evidencia existe; ningún [OBL] se queda sin ella) |
| 6 Coordenadas inválidas | Ruta existe | `docs/evidencias/consumidor-idempotente/prueba6_cuarentena.out` | Ninguna |
| 7 Evento marítimo | Correctamente pendiente de captura. **Ruta sin directorio**: cita `geografia_prueba7.out`; el archivo está en `geografia-pais/`. La cifra «14 429 reales sin país» es del 13-nov (hoy 14 502 de 19 208 sin país) | `docs/evidencias/geografia-pais/geografia_prueba7.out`; `docs/evidencias/pruebas/07_captura_pendiente.md` | No bloqueante: corregir el directorio y la cifra |
| 8 Reinicio del consumidor | Ruta existe | `docs/evidencias/consumidor-idempotente/prueba8_reinicio.out` | Ninguna |
| 9 Cierre del túnel | Correctamente pendiente. Cita `prueba-09_*.md` con comodín; el archivo existe (`prueba-09_cierre-tunel.md`) y hay otra ficha en `docs/evidencias/pruebas/` | `docs/evidencias/despliegue-tunel/prueba-09_cierre-tunel.md`; `docs/evidencias/pruebas/09-cierre-tunel.md` | Ninguna (acción del alumno) |
| 10 Reapertura del túnel | Correctamente pendiente; igual que la 9 | `docs/evidencias/despliegue-tunel/prueba-10_reapertura-tunel.md`; `docs/evidencias/pruebas/10-reapertura-tunel.md` | Ninguna (acción del alumno) |
| 11 Reproducción histórica | Ruta existe. El documento no dice que en replay la comparación es nula (`comparison` nulo): la comparación figura implícitamente como disponible en §4.2 (Análisis) sin esa salvedad | `docs/evidencias/replay/README.md`; `docs/evidencias/replay/T055_estadisticas_replay.json` | No bloqueante: añadir «sin comparación en replay» a la fila 11 o al bloque Análisis. Ya figura en `README.md` («Limitaciones conocidas») |

## Otros hallazgos del documento (no son criterios ni pruebas)

| Hallazgo | Ruta | Acción |
|---|---|---|
| §2 «Hallazgos reales» son del 13-nov (18 809 eventos, 18 909 versiones, 14 429 sin país). Hoy: 19 208 eventos, 19 509 versiones (301 más que eventos), 14 502 sin país; 0 sintéticos, 0 nulos en `mag` y 0 en cuarentena siguen igual (`calidad-live.md`) | `docs/evidencias/revision-final/calidad-live.md` | No bloqueante: citar la fecha o actualizar |
| §2, §3.6 y §5.6 dicen que el README es un diario de features y que falta la tabla rúbrica→evidencia; ya existe en `README.md` | `README.md` («Rúbrica → evidencia (M10)») | No bloqueante: actualizar el texto |
| §5 (última línea) cita las features `pruebas-aceptacion` 014 y `readme-video` 017, que ya no se llaman así | `README.md` («Estado actual») | No bloqueante: actualizar la numeración |
| §3.8 habla de 15 archivos de evidencia sin seguir en `git status`; el estado actual es otro | — | No bloqueante: revisar |
| Las referencias a `ENUNCIADO.md` y `README-paquete.md` apuntan a `docs/enunciado/` (existen) | `docs/enunciado/ENUNCIADO.md`; `docs/enunciado/README-paquete.md` | Ninguna |
