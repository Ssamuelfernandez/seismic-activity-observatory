# Rúbrica del proyecto, estado de cumplimiento y guía del vídeo

Este documento no añade requisitos: resume lo que puntúa según `ENUNCIADO.md` §13 y `README-paquete.md`, dice si ya lo tienes y cómo enseñarlo en el vídeo de 5 minutos.

---

## 1. La rúbrica real (lo único que puntúa)

Son **5 criterios**, heredados del ejercicio de supermercados de la sesión 8. Cada uno tiene cuatro niveles: Insuficiente (0–4), Suficiente (5–6), Notable (7–8), Sobresaliente (9–10).

| Criterio | Notable (7–8) | **Sobresaliente (9–10)** | Qué lo demuestra en este proyecto |
|---|---|---|---|
| **Extracción** | Carga + exploración | **Carga + análisis de tipos** | Histórico 2025, feed en vivo y catálogo de países; tipos, unidades, límites y automatización |
| **Calidad** | 4+ dimensiones | **Análisis completo + acciones** | Apartado en memoria o notebook con consultas, resultados antes/después y decisiones |
| **Modelado** | Modelo correcto | **Modelo optimizado** | Modelo conceptual/lógico/físico, grano, claves, revisiones, idempotencia, índices medidos |
| **Análisis** | 3+ análisis | **Análisis + insights** | Ventanas por hora, distribuciones, comparación histórica equivalente, ≥3 conclusiones con cifras |
| **Reflexión** | Buena reflexión | **Excelente + propuestas** | Complejidad, mediciones con 3 tamaños, costes, 100 M de registros, limitaciones y mejoras |

Reglas que el enunciado repite y que conviene tener presentes en el vídeo:

- «Más infraestructura no da más nota». No se evalúa la complejidad técnica por sí misma.
- El mapa entregado no sustituye las evidencias. El mapa es solo una parte del resultado.
- **No son obligatorios, ni puntúan:** generador automático de informe de calidad, panel de calidad en la web, ROI, 24/7, Spark/Flink/Kubernetes, machine learning.
- Nada de lenguaje de predicción ni de riesgo en las conclusiones.
- **Cambio de evaluación que consta en tu checklist** (rev. 8, 13-nov): no hay defensa oral. Se entrega **README + vídeo de 5 min**. El vídeo debe explicar cómo se cumple cada criterio, y el README debe llevar la tabla rúbrica→evidencia (M10), un recorrido de un evento y una decisión técnica propia.
- Entrega: **19 de noviembre de 2026**, trabajo individual.

Además hay un bloque de requisitos de «aceptación» (las 11 pruebas del enunciado §11) y de despliegue (§9). No son criterios de la rúbrica, pero son la prueba de que el sistema funciona. Sirven como evidencia dentro de Modelado y Extracción.

---

## 2. ¿La cumples hoy? Veredicto honesto

**Resumen:** el sistema (código, datos y mediciones) está construido y funciona. **Lo que falta es, sobre todo, escrito y demostrable**: el análisis de calidad por dimensiones, las conclusiones, las secciones de la memoria, el README final con la tabla rúbrica→evidencia, los datos de costes, el túnel/Netlify en vivo y el propio vídeo.

| Criterio | Nivel que puedes defender hoy | Por qué | Qué falta para el 9–10 |
|---|---|---|---|
| **Extracción** | **Sobresaliente, casi cerrado** | Productor cada 60 s con reintentos y backoff, filtro `type=earthquake` con motivo de exclusión (54 exclusiones en la base), originales guardados, histórico 2025 por meses (18 302 únicos, conciliado con el `count` anual de USGS), manifiesto con consultas y SHA-256, catálogo de 177 países. | Pasar a la memoria el diccionario de datos completo (§2 está a medias), el registro de procedencia (§3 vacío) y los apuntes de `docs/borradores/productor-live.md` (B2, B11, B12) e `historico-2025.md` (B18). |
| **Calidad** | **Suficiente-Notable en código; Insuficiente en lo escrito** | Las reglas existen y funcionan (14 motivos de cuarentena, nulos sin rellenar, negativos válidos, `is_synthetic`, contadores de transformaciones). La memoria §4 documenta las **reglas**, pero **no contiene todavía el análisis**: porcentajes de completitud, duplicados, anomalías, actualidad, antes/después. Es lo que puntúa y no lo tienes escrito. | Redactar §4 con las 6 dimensiones (completitud, unicidad, validez, consistencia, actualidad, exactitud), cada una con su consulta, resultado, denominador y acción. **Es el hueco más importante.** |
| **Modelado** | **Sobresaliente en el diseño** | Modelo conceptual, lógico y físico en `docs/memoria.md` §5, con equivalencia de nombres. Hecho actual + historial de versiones, país por punto-en-polígono, upsert idempotente, offset tras el commit, esquemas `live`/`replay` aislados. Pruebas 2, 3, 4, 6, 8 y 11 ejecutadas con evidencia. | Que la memoria cite los resultados de las mediciones de índices (`docs/evidencias/mediciones/indices.md`) para justificar los índices («modelo optimizado»). Cerrar las pruebas 1, 5 y 7 con capturas. |
| **Análisis** | **Funcional, sin redactar** | El panel y la API ya calculan lo exigido: recuentos por hora UTC y país (incluido «Sin país asignado»), distribuciones, comparación 24 h M≥4 frente a la media diaria de 2025, filtros coherentes, tabla. Pero la memoria §6 está vacía: **no hay ninguna conclusión escrita** y la rúbrica pide ≥3 con cifras. | Escribir ≥3 conclusiones con periodo, filtros, denominador y captura con los filtros visibles. |
| **Reflexión** | **Sobresaliente en el material; falta pasarlo a la memoria** | Mediciones con 3 tamaños, comparaciones lista/diccionario y sin/con índice, razonamiento a 10⁸ filas, 8 propuestas de escalado ligadas a cifras, costes completos (hardware, electricidad, almacenamiento, transferencia, mantenimiento, dominio y desarrollo) con origen medido/supuesto y naturaleza efectivo/imputado, y limitaciones declaradas (`docs/evidencias/mediciones/`; auditoría sin bloqueantes en `docs/evidencias/subagentes/verificador-auditoria-mediciones-costes.md`). | La memoria §7 ya lo resume; queda la cuota de Netlify sin verificar y repetir desde un clon limpio (SC-007). |

### Hallazgos reales que debes conocer antes de grabar

Medidos en la base el 13-nov:

| Dato | Valor | Qué implica para el vídeo |
|---|---|---|
| Eventos actuales en `live` | 18 809 (2025-01-01 a 2026-11-13), 0 sintéticos | Hay datos reales de sobra para el mapa y el análisis. |
| Versiones guardadas | 18 909 (100 más que eventos) | Evidencia viva de que las **revisiones** se guardan sin duplicar eventos. |
| Sin país asignado | 14 429 (≈ 77 %) | Es plausible (la mayoría de los sismos ocurren en el mar y la costa del catálogo está simplificada), pero debes **explicarlo con cifra**: no es un error. Es una buena conclusión y una limitación honesta. |
| Magnitud nula en `live` | **0** | La prueba 5 (magnitud nula → ND) **no se puede enseñar con datos reales**. Usa el caso controlado de replay o el mock sintético etiquetado. |
| Cuarentena en `live` | **0** | La prueba 6 (coordenadas inválidas) se enseña con la evidencia ya guardada (`docs/evidencias/consumidor-idempotente/prueba6_cuarentena.out`) o ejecutándola en vivo con el script de verificación. No con datos reales. |
| Replay | 22 eventos en `replay.current_event` | Hay una reproducción ya cargada y aislada. |
| Túnel y Netlify | **No verificados por ti** (pruebas 9 y 10, H1, H3, H4 sin marcar) | Hay que hacerlo en vivo antes de grabar. Hay plantillas en `docs/evidencias/despliegue-tunel/prueba-09_*.md` y `prueba-10_*.md`. |

---

## 3. Lista de lo que falta (ordenada por impacto en la nota)

Para que el vídeo tenga algo sólido que enseñar. Cada punto indica el criterio que sostiene.

1. **Análisis de calidad por dimensiones** (Calidad). Son 6 consultas SQL sobre `live.*` y `quarantine`, con denominador y acción. Puntúa mucho y es lo que más falta. Reglas de redacción en el checklist (§D): indicar el conjunto y el denominador, no sumar incidencias solapadas, no inventar errores en datos reales.
2. **≥3 conclusiones con cifras** (Análisis). Candidatas con datos que ya tienes: porcentaje sin país y su explicación; comparación de las últimas 24 h con M≥4 frente a la media diaria de 2025 (con días a cero en el denominador); distribución de profundidad y de magnitud; recuentos por país.
3. **Costes** (Reflexión). **Hecho** (`costes.md`, `equipo.md`, `transferencia.md`). Queda sin verificar el límite de Netlify.
4. **Memoria §1, §3, §6, §7, §8, §9, §10** vacías o a medias. Basta con trasladar los borradores de `docs/borradores/` y las tablas de `docs/evidencias/mediciones/`.
5. **Pruebas de aceptación 1, 5, 7, 9 y 10** con evidencia propia (checklist §I). Las 2, 3, 4, 6, 8 y 11 ya tienen evidencia.
6. **README final** con la tabla rúbrica→evidencia (M10) y el recorrido de un evento y la decisión propia. El README actual es un diario de features, no el documento final.
7. **Túnel y Netlify en vivo** (H1, H3, H4). Sin esto, no puedes enseñar el panel desde otro dispositivo.
8. Housekeeping: reconstruir la imagen `tests` (un error de recogida en `tests/common/test_api_config.py` por imagen antigua) y decidir qué hacer con los 15 archivos de evidencia sin seguir en `git status`.

---

## 4. Guía para el vídeo de 5 minutos

Idea central: **un criterio de la rúbrica por bloque, y en cada bloque, «lo que dice el enunciado → lo que hice → la prueba en pantalla»**. El evaluador busca los 5 criterios; no le interesa el tour del código.

### 4.1 Preparación (antes de pulsar «grabar»)

1. `docker compose up --build -d` y `docker compose ps`: los cinco servicios en *healthy*.
2. Túnel Cloudflare abierto y `curl https://TU-DOMINIO/api/salud` respondiendo. Panel de Netlify abierto en otra pestaña y, si puedes, en el móvil.
3. Terminal con `psql` abierta: `docker compose exec postgres psql -U observatory_admin -d observatory`.
4. Pestañas listas: `docs/memoria.md` (modelo y calidad), `docs/evidencias/mediciones/tablas.md`, `indices.md` y `costes.md`.
5. Hacer un ensayo completo con el cronómetro. El límite son 5 minutos. Guarda un plan B (capturas) por si el túnel falla.

### 4.2 Guion con tiempos

| Min | Bloque | Qué decir (idea) | Qué enseñar en pantalla | Criterio |
|---|---|---|---|---|
| 0:00–0:20 | Qué es | «Pregunta: ¿dónde hay actividad sísmica y cómo se compara con un periodo histórico equivalente?». Flujo: USGS → productor → Kafka → consumidor → PostgreSQL → API → túnel → panel. | Diagrama del flujo o `docker compose ps` con los 5 servicios healthy. | Contexto |
| 0:20–1:10 | **Extracción** | Tres fuentes: feed de 24 h cada 60 s, histórico 2025 por meses (M≥4) y catálogo de países. Qué hace el productor: compara `id` + `updated` con el estado persistente, espera el ack de Kafka, reintenta con espera progresiva y registra el motivo de exclusión de lo que no es terremoto. Tipos y unidades: coordenadas lon/lat/profundidad km, tiempos en ms Unix UTC. | Log del productor (`docker compose logs producer --tail 5`). `data/historical/manifest.json` (consultas, fechas, 18 302 únicos y conciliación con USGS). Tabla de tipos del diccionario de datos. | Extracción |
| 1:10–2:10 | **Calidad** | «Seis dimensiones, no una». Muestra 2–3 con su consulta y su porcentaje, y di la **acción** tomada. Resalta las decisiones: no relleno nulos con 0, una magnitud o profundidad negativa no es un error, lo inválido va a cuarentena con motivo y original. | Memoria §4: la tabla de dimensiones y una fila de `quarantine` con su motivo (`SELECT reason, count(*) FROM live.quarantine GROUP BY 1`, o la evidencia guardada de la prueba 6). | Calidad |
| 2:10–3:10 | **Modelado** | Grano y claves: `current_event` (1 fila por `event_id`), `event_version` (único `(event_id, updated)`). Qué pasa con un duplicado y con una versión vieja tardía. Cómo se integra el país (punto en polígono, `ADM0_A3`, «Sin país asignado» conservado). Un índice con su medición antes/después. | Diagrama del modelo (memoria §5). Demostración corta de las pruebas 2 y 4: reenviar la misma versión no cambia el recuento; una versión antigua no pisa a la nueva (evidencia en `docs/evidencias/consumidor-idempotente/`). `indices.md` con el «sin/con índice». | Modelado |
| 3:10–4:10 | **Análisis** | Abre el panel real (URL de Netlify). Aplica un filtro y enseña que **mapa, gráficos y tabla cambian a la vez**. Lee **una** conclusión con cifra, periodo y filtros: la comparación de las últimas 24 h M≥4 frente a la media diaria de 2025, o el porcentaje sin país. Enseña un evento nulo como ND. | Panel: mapa/globo con leyenda, filtro por país y magnitud, gráfico por hora UTC, comparación histórica, tabla. Estado del sistema (última ingesta). Opcional y breve: **replay etiquetado «REPRODUCCIÓN»**, para enseñar que va por Kafka y está aislado. | Análisis |
| 4:10–4:50 | **Reflexión** | Complejidad (diccionario O(1) frente a recorrido O(n), integración geográfica, agregación por ventanas), mediciones con tres tamaños, qué ocurriría con 100 M de filas (índices, particionado, más particiones en Kafka), costes y que «gratis» no es coste cero. Una limitación honesta. | `tablas.md` (tamaños y tiempos), `escalado.md`, `costes.md` con tus cifras ya rellenas. | Reflexión |
| 4:50–5:00 | Cierre | Recorrido de un evento (un `id` de USGS, de principio a fin) y **una decisión técnica propia** con su motivo. Dónde está la tabla rúbrica→evidencia en el README. | README (tabla M10). | Cierre |

Si te pasas de tiempo, **recorta Extracción y el cierre**; deja Calidad, Modelado y Análisis, que son los que tienen más hueco hasta el 9–10.

### 4.3 Qué mostrar para cada una de las 11 pruebas (si las incluyes en el README o el vídeo)

| # | Prueba | Cómo enseñarla | Evidencia que ya existe |
|---|---|---|---|
| 1 | Evento nuevo | Un `id` del feed en vivo: `SELECT * FROM live.current_event WHERE event_id = '…'`, luego `GET /api/eventos` y el panel | `docs/evidencias/productor-live/prueba1_evento_nuevo.out` (hasta PostgreSQL). **Falta la captura de API, mapa y análisis.** |
| 2 | Reenviar la misma versión | Recuento antes y después | `consumidor-idempotente/prueba2_reenvio.out` |
| 3 | Versión posterior | Cambian los datos actuales y las agregaciones | `consumidor-idempotente/prueba3_4_versiones.out` |
| 4 | Versión antigua tardía | No sustituye a la más reciente | Ídem |
| 5 | Magnitud nula | ND en el panel. **No hay nulos en datos reales**, usa el caso controlado de replay o el mock sintético etiquetado | `consumidor-idempotente/geografia_prueba5.out`. **Falta la captura del panel con ND.** |
| 6 | Coordenadas inválidas | Fila en cuarentena con motivo; ningún punto inventado | `consumidor-idempotente/prueba6_cuarentena.out` |
| 7 | Evento marítimo | «Sin país asignado» sigue en el análisis (hay 14 429 reales) | `geografia_prueba7.out`. **Falta la captura.** |
| 8 | Reiniciar consumidor | `docker compose restart consumer` y el recuento no cambia | `prueba8_reinicio.out` |
| 9 | Cerrar el túnel | Cierra `cloudflared` y espera al siguiente refresco: el panel avisa y conserva la última lectura | **Pendiente: plantilla `despliegue-tunel/prueba-09_cierre-tunel.md`** |
| 10 | Reabrir el túnel | Se recupera solo | **Pendiente: plantilla `prueba-10_reapertura-tunel.md`** |
| 11 | Reproducción histórica | Lanza el replay; banner «REPRODUCCIÓN»; datos aislados de `live` | `docs/evidencias/replay/` |

Las pruebas 9 y 10 se hacen **mejor en el propio vídeo**: son visuales y tu plantilla ya dice que su evidencia irá en el vídeo. Ocupan unos 20 segundos si las ensayas.

### 4.4 Errores que te quitarían nota

- Enseñar solo el mapa. El enunciado dice explícitamente que no basta.
- Decir «0 duplicados» sin enseñar la consulta ni el denominador.
- Presentar el 77 % sin país como un fallo, o llamar «error» a los nulos o a las magnitudes negativas.
- Dar una conclusión sin periodo, filtros ni denominador, o con lenguaje de predicción o de riesgo.
- Comparar el recuento reciente con el histórico sin los mismos filtros (M≥4 y mismo ámbito), o dividir solo entre los días con eventos.
- Mezclar replay y datos reales. Si lo enseñas, el banner «REPRODUCCIÓN» debe verse.
- Presentar datos sintéticos o del mock como si fueran reales. Deben ir etiquetados.
- Enseñar costes sin distinguir lo **medido** de lo **supuesto**.
- Mostrar el authtoken o token del túnel, o credenciales del `.env`, en pantalla.

---

## 5. Orden de trabajo recomendado hasta el 19 de noviembre

1. **Calidad** (consultas + redacción en la memoria §4). Es el mayor impacto.
2. **Análisis**: 3 conclusiones y sus capturas con los filtros visibles.
3. ~~Costes: rellenar `costes.md` y `equipo.md`~~ (hecho; resumen en la memoria §7).
4. Memoria: trasladar los borradores a §1, §3, §6, §7, §8, §9 y §10.
5. Túnel + Netlify en vivo, pruebas 9 y 10 y capturas de 1, 5 y 7.
6. README final con la tabla rúbrica→evidencia, el recorrido de un evento y la decisión propia.
7. Ensayo con cronómetro y grabación (el roadmap reserva el 17–18 de noviembre).

Según `CLAUDE.md`, cada una de estas piezas es una feature (`pruebas-aceptacion` 014, `readme-video` 017) que necesita spec, plan y tareas revisados antes de implementarse. Los puntos 1, 2 y 4 son texto y consultas; los puntos 3, 5 y 6 requieren tus datos y tu equipo.
