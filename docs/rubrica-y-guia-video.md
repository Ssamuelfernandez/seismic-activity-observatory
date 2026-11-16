# Rúbrica del proyecto, estado de cumplimiento y guía del vídeo

Guía vigente a 2026-11-16. Este documento no añade requisitos: resume lo que puntúa según `docs/enunciado/ENUNCIADO.md` §13 y `docs/enunciado/README-paquete.md`, dice dónde está cada evidencia y cómo enseñarla en el vídeo de 5 minutos. Las cifras que cambian con el tiempo llevan su fecha: el productor sigue ingiriendo, así que al grabar las de la base serán mayores.

---

## 1. La rúbrica real (lo único que puntúa)

Son **5 criterios**, heredados del ejercicio de supermercados de la sesión 8. Cada uno tiene cuatro niveles: Insuficiente (0–4), Suficiente (5–6), Notable (7–8), Sobresaliente (9–10).

| Criterio | Notable (7–8) | **Sobresaliente (9–10)** | Qué lo demuestra en este proyecto |
|---|---|---|---|
| **Extracción** | Carga + exploración | **Carga + análisis de tipos** | Histórico 2025, feed en vivo y catálogo de países; tipos, unidades, límites y automatización |
| **Calidad** | 4+ dimensiones | **Análisis completo + acciones** | Apartado en memoria con consultas, resultados antes/después y decisiones |
| **Modelado** | Modelo correcto | **Modelo optimizado** | Modelo conceptual/lógico/físico, grano, claves, revisiones, idempotencia, índices medidos |
| **Análisis** | 3+ análisis | **Análisis + insights** | Ventanas por hora, distribuciones, comparación histórica equivalente, ≥3 conclusiones con cifras |
| **Reflexión** | Buena reflexión | **Excelente + propuestas** | Complejidad, mediciones con 3 tamaños, costes, 100 M de registros, limitaciones y mejoras |

Reglas que el enunciado repite y que conviene tener presentes en el vídeo:

- «Más infraestructura no da más nota». No se evalúa la complejidad técnica por sí misma.
- El mapa entregado no sustituye las evidencias. El mapa es solo una parte del resultado.
- **No son obligatorios, ni puntúan:** generador automático de informe de calidad, panel de calidad en la web, ROI, 24/7, Spark/Flink/Kubernetes, machine learning.
- Nada de lenguaje de predicción ni de riesgo en las conclusiones.
- No hay defensa oral (rev. 8 del checklist, 13-nov). Se entrega **README + vídeo de 5 min**. El vídeo debe explicar cómo se cumple cada criterio, y el README lleva la tabla rúbrica→evidencia (M10), un recorrido de un evento y una decisión técnica propia.
- Entrega: **19 de noviembre de 2026**, trabajo individual.

Además hay un bloque de requisitos de «aceptación» (las 11 pruebas del enunciado §11) y de despliegue (§9). No son criterios de la rúbrica, pero son la prueba de que el sistema funciona. Sirven como evidencia dentro de Modelado y Extracción.

---

## 2. Estado de cumplimiento a 2026-11-16

El sistema (código, datos y mediciones) está construido y los documentos finales están escritos: memoria §1 a §10, README con la tabla M10, el recorrido y la decisión propia. Lo que queda es grabar el vídeo y poner su enlace.

| Criterio | Estado | Dónde está |
|---|---|---|
| **Extracción** | Cumple. Productor cada 60 s con reintentos y espera progresiva, filtro `type=earthquake` con motivo de exclusión (95 exclusiones `non_earthquake_type` el 2026-11-16), originales guardados, histórico 2025 por meses (18 302 únicos, conciliado con el recuento anual de USGS), manifiesto con consultas y sha256, catálogo de 177 países. Diccionario de datos con los campos del feed y del modelo; B2, B18 y procedencia con URLs, filtros, registros y fechas. | Memoria §2, §2.1 y §3; `data/historical/manifest.json`; `docs/evidencias/productor-live/ciclo1.log` |
| **Calidad** | Cumple. Reglas y cuarentena (14 motivos) en §4.1 a §4.3; análisis de las 6 dimensiones sobre datos reales de `live` con consulta, denominador y decisión en §4.4 (cifras del 2026-11-15). Como en datos reales no hay nada que limpiar (0 duplicados, 0 fuera de rango, 0 reales en cuarentena), el «antes y después» se enseña con evidencia de las reglas aplicadas a casos controlados. | Memoria §4; [`docs/evidencias/revision-final/calidad-live.md`](evidencias/revision-final/calidad-live.md); `docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out` |
| **Modelado** | Cumple. Modelo conceptual, lógico y físico, con equivalencia de nombres; hecho actual + historial de versiones; país por punto en polígono; escritura idempotente; offset tras el commit; esquemas `live` y `replay` aislados; índices justificados con medición (`ix_current_event_country_time` justificado en los 6 casos de Q2; el de magnitud, no concluyente). | Memoria §5 y §7.2; `sql/001_schema.sql`; [`docs/evidencias/mediciones/indices.md`](evidencias/mediciones/indices.md) |
| **Análisis** | Cumple. API y panel calculan por hora UTC y país (con «Sin país asignado»), distribuciones, comparación 24 h M≥4 frente a la media diaria de 2025 y filtros coherentes. Tres conclusiones con periodo, filtros, denominador y consulta en la memoria §6. No hay captura nueva del panel con esos filtros: se mostrarán en el vídeo. | Memoria §6; [`docs/evidencias/revision-final/conclusiones-analisis.md`](evidencias/revision-final/conclusiones-analisis.md) |
| **Reflexión** | Cumple. Mediciones con 3 tamaños, lista frente a diccionario y sin/con índice, razonamiento a 10⁸ filas, 8 propuestas de escalado, costes con origen (medido, supuesto o estimado) y naturaleza (efectivo o imputado). Netlify: plan gratuito, según indica el alumno. | Memoria §7 y §10; `docs/evidencias/mediciones/` |

### Cifras de la base que conviene saber antes de grabar

| Dato | Valor y fecha | Qué implica para el vídeo |
|---|---|---|
| Eventos actuales reales en `live` | 19 208 el 2026-11-15 (18 302 del histórico y 906 del feed); 19 385 el 2026-11-16 (1 083 del feed). 0 sintéticos | Hay datos de sobra. Di la fecha de la cifra que enseñes. |
| Versiones guardadas | 19 509 el 2026-11-15, con 149 eventos con más de una versión | Evidencia viva de que las revisiones se guardan sin duplicar eventos. |
| Sin país asignado | 75,50 % de los eventos de `live` el 2026-11-15 (24,50 % con país); 78,4 % en el histórico de 2025 (14 350 de 18 302) | Explícalo con cifra: la mayoría de los sismos ocurren en el mar y el catálogo es de 110 m. No es un error; es una conclusión y una limitación. |
| Magnitud nula en `live` | 0 | La prueba 5 no se puede enseñar con datos reales: usa la captura del mock sintético etiquetado (`docs/evidencias/pruebas/capturas/05_magnitud_nula_nd.png`). |
| Cuarentena real en `live` | 0 | La prueba 6 se enseña con la evidencia guardada (`docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out`), no con datos reales. |
| Consultas al feed | 1 762, todas con HTTP 200, del 2026-11-12 16:38 UTC al 2026-11-16 18:10 UTC | Prueba de que el productor lleva días funcionando sin fallos. |
| Replay | 22 eventos en `replay.current_event`, 24 versiones, 0 en cuarentena (2026-11-12) | Reproducción cargada y aislada; `live` tuvo la misma huella antes y después. |
| Comparación 24 h frente a 2025 | La API marca `recent_incomplete: true` (16 eventos recientes frente a 50,14 por día el 2026-11-16) | No la uses como conclusión; si la enseñas, di que el periodo reciente puede estar incompleto. |

---

## 3. Guía para el vídeo de 5 minutos

Idea central: **un criterio de la rúbrica por bloque, y en cada bloque, «lo que dice el enunciado → lo que hice → la prueba en pantalla»**. El evaluador busca los 5 criterios; no le interesa el tour del código.

### 3.1 Preparación (antes de pulsar «grabar»)

Limitación que hay que tener presente: **el panel público solo funciona con el PC del alumno y `cloudflared` encendidos**. Sin ellos, el panel de Netlify no recibe datos.

1. `docker compose up --build -d` y `docker compose ps`: los cinco servicios en *healthy*. Que no exista `compose.override.yaml`.
2. El PC no debe suspenderse (ajustes de energía) y `nslookup observatorio.ssamuelfernandez.net` debe resolver.
3. `cloudflared` encendido siguiendo «Túnel público y panel» del README y `curl https://observatorio-api.ssamuelfernandez.net/api/salud` respondiendo 200. Panel de Netlify abierto en una pestaña **visible**. No mostrar nunca el token del túnel ni el `.env`.
4. Terminal con `psql` abierta: `docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>` (los valores están en tu `.env`; no los enseñes en pantalla).
5. Pestañas listas: `docs/memoria.md` (§4.4, §5, §6), `docs/evidencias/mediciones/tablas.md`, `docs/evidencias/mediciones/indices.md` y `docs/evidencias/mediciones/costes.md`, y el README con la tabla M10.
6. Ensayo completo con cronómetro. Plan B si el túnel falla: las capturas de `docs/evidencias/despliegue-tunel/2026-11-12_panel-publico.png` y `docs/evidencias/pruebas/capturas/`.

### 3.2 Guion con tiempos (5:00 exactos)

| Minuto | Bloque | Qué decir (idea) | Qué enseñar en pantalla | Criterio |
|---|---|---|---|---|
| 0:00–0:20 | Qué es | «Pregunta: ¿qué actividad sísmica hay ahora y cómo se compara con 2025?». Flujo: USGS → productor → Kafka → consumidor → PostgreSQL → API → túnel → panel. Aviso: el panel público requiere mi PC y `cloudflared` encendidos. | Diagrama de la memoria §1 o `docker compose ps` con los cinco servicios healthy | Contexto |
| 0:20–1:05 | **Extracción** | Tres fuentes: feed de 24 h cada 60 s, histórico 2025 por meses (M≥4) y catálogo de países. El productor compara `id` y `updated` con el estado guardado, reintenta con espera progresiva y registra el motivo de exclusión de lo que no es terremoto. Tipos y unidades: lon/lat/profundidad en km, tiempos en ms Unix UTC. | `docker compose logs producer --tail 5`; `data/historical/manifest.json` (18 302 únicos, coincide con USGS); tabla del diccionario (memoria §2) | Extracción |
| 1:05–1:55 | **Calidad** | «Seis dimensiones, no una». Enseña 2 o 3 con consulta y porcentaje, y la **acción** tomada. Decisiones: no relleno nulos con 0, una magnitud o profundidad negativa no es un error, lo inválido va a cuarentena con motivo y original. «En datos reales no hay nada que limpiar; lo muestro con casos controlados». | Memoria §4.4 (tabla de dimensiones) y `docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out` (6 inválidos → 6 filas con motivo) | Calidad |
| 1:55–2:40 | **Modelado** | Grano y claves: `current_event` (1 fila por `event_id`) y `event_version` (único `(event_id, updated_ms)`). Duplicado y versión vieja tardía no cambian nada. País por punto en polígono; «Sin país asignado» se conserva. Un índice con su medición sin/con. | Diagrama del modelo (memoria §5); pruebas 2 y 4 en `docs/evidencias/consumidor-idempotente/bloque3_prueba2_reenvio.out` y `docs/evidencias/consumidor-idempotente/bloque3_prueba3_4_versiones.out`; `docs/evidencias/mediciones/indices.md` | Modelado |
| 2:40–3:35 | **Análisis** (filtros y conclusión) | Abre el panel público. Aplica un filtro y enseña que mapa, gráficos y tabla cambian a la vez. Lee **una** conclusión con cifra, periodo y filtros: el 78,4 % de los eventos de 2025 queda sin país (14 350 de 18 302), o julio y agosto concentran el 26,8 % por la secuencia de Kamchatka. Enseña un evento con ND como mock sintético etiquetado. | Panel público: mapa, filtro por país y magnitud, gráfico por hora UTC, tabla; memoria §6 | Análisis |
| 3:35–4:10 | **Análisis** (pruebas 9 y 10 en vivo) | «El panel avisa cuando falla la conexión y se recupera solo». Cierra `cloudflared`, espera el aviso «Datos antiguos» con la hora de la última lectura, reábrelo y espera a que desaparezca. | Ver el procedimiento de 3.3. Se graba aparte y se acortan las esperas en el montaje, con el reloj a la vista | Análisis (aceptación) |
| 4:10–4:40 | **Reflexión** | Complejidad: diccionario O(1) frente a lista O(n), integración geográfica con árbol, agregación por ventanas; mediciones con 3 tamaños; qué pasaría con 10⁸ filas (particionado, lotes, más particiones en Kafka); costes con lo medido frente a lo supuesto («gratis» no es coste cero). Limitación honesta: sin país 75,5 %, panel dependiente de mi PC. | `docs/evidencias/mediciones/tablas.md`, `docs/evidencias/mediciones/escalado.md` y `docs/evidencias/mediciones/costes.md`; memoria §7 y §10 | Reflexión |
| 4:40–5:00 | Cierre | Recorrido de `us6000pms8` (M 4,4 cerca de Calama; evento real de 2025 reproducido por replay: productor → Kafka partición 0 offset 18 → consumidor → `replay.current_event` → API → panel). Decisión propia: el replay aislado de `live` en **tres capas** (topic, esquema y comprobación de `mode`), con `live` idéntico antes y después (211 / 211 / 0, misma huella `md5`). Señala la tabla M10 del README. | README: «Recorrido de un evento», «Decisión propia» y la tabla M10 | Cierre |

Si te pasas de tiempo, recorta Extracción y el cierre; deja Calidad, Modelado y Análisis.

### 3.3 Pruebas 9 y 10 en vivo: pasos

Con el panel público abierto en una pestaña **visible** (con la pestaña oculta el refresco puede detenerse):

1. Espera a ver datos reales y anota la hora de la última lectura que indica el panel.
2. Cierra `cloudflared` (Ctrl+C) **sin recargar** el panel y anota la hora.
3. Espera al siguiente refresco: hasta 60 s (`refreshSeconds`) más 15 s (`timeoutMs`), unos 75 s. No recargues ni cambies de pestaña. Debe aparecer «Datos antiguos» con la última lectura conservada y los datos anteriores visibles.
4. Vuelve a lanzar `cloudflared`, comprueba `curl https://observatorio-api.ssamuelfernandez.net/api/salud` con 200 y, **sin recargar**, espera otros ~75 s: el aviso desaparece y la hora de lectura se actualiza.

Cada espera dura más de lo que cabe en el guion: graba aparte y acorta las esperas al montar, dejando el reloj a la vista. Fichas completas: [`docs/evidencias/pruebas/09-cierre-tunel.md`](evidencias/pruebas/09-cierre-tunel.md) y [`docs/evidencias/pruebas/10-reapertura-tunel.md`](evidencias/pruebas/10-reapertura-tunel.md). Hoy solo hay una captura parcial (`docs/evidencias/pruebas/capturas/09_cierre_tunel_sin_respuesta.png`: «SIN RESPUESTA DE LA API», sin lectura previa); no muestra «Datos antiguos».

### 3.4 Qué mostrar para cada una de las 11 pruebas (si las incluyes)

| # | Prueba | Cómo enseñarla | Evidencia que existe |
|---|---|---|---|
| 1 | Evento nuevo | Un `id` del feed en vivo: `SELECT * FROM live.current_event WHERE event_id = '…'`, luego `GET /api/eventos` y el panel | `docs/evidencias/productor-live/prueba1_evento_nuevo.out`; captura `docs/evidencias/pruebas/capturas/01_evento_nuevo.png` (evento real `ci41362543`) |
| 2 | Reenviar la misma versión | Recuento antes y después | `docs/evidencias/consumidor-idempotente/bloque3_prueba2_reenvio.out` |
| 3 | Versión posterior | Cambian los datos actuales y las agregaciones | `docs/evidencias/consumidor-idempotente/bloque3_prueba3_4_versiones.out`; captura `docs/evidencias/pruebas/capturas/03_version_posterior.png` (`uw714139501`) |
| 4 | Versión antigua tardía | No sustituye a la más reciente | Ídem la 3 |
| 5 | Magnitud nula | ND en el panel; no hay nulos reales, se usa el mock sintético etiquetado | `docs/evidencias/geografia-pais/geografia_prueba5.out`; captura `docs/evidencias/pruebas/capturas/05_magnitud_nula_nd.png` |
| 6 | Coordenadas inválidas | Fila en cuarentena con motivo; ningún punto inventado | `docs/evidencias/consumidor-idempotente/bloque3_prueba6_cuarentena.out` |
| 7 | Evento marítimo | «Sin país asignado» sigue en el análisis | `docs/evidencias/geografia-pais/geografia_prueba7.out`; captura real `docs/evidencias/pruebas/capturas/07_evento_maritimo.png` (30 eventos sin país) |
| 8 | Reiniciar consumidor | `docker compose restart consumer` y el recuento no cambia | `docs/evidencias/consumidor-idempotente/bloque4_prueba8_corte_simulado.out` y `docs/evidencias/consumidor-idempotente/prueba8_reinicio.out` |
| 9 | Cerrar el túnel | Pasos de 3.3 | Captura parcial `docs/evidencias/pruebas/capturas/09_cierre_tunel_sin_respuesta.png`; demostración en el vídeo |
| 10 | Reabrir el túnel | Pasos de 3.3 | Sin captura; demostración en el vídeo |
| 11 | Reproducción histórica | Lanza el replay; banner «REPRODUCCIÓN»; datos aislados de `live` | `docs/evidencias/replay/README.md`, `docs/evidencias/replay/T056_reproduccion.png`, `docs/evidencias/replay/T056_en_vivo.png` |

### 3.5 Errores que te quitarían nota

- Enseñar solo el mapa. El enunciado dice explícitamente que no basta.
- Decir «0 duplicados» sin enseñar la consulta ni el denominador.
- Presentar el 75,5 % (o el 78,4 %) sin país como un fallo, o llamar «error» a los nulos o a las magnitudes negativas.
- Dar una conclusión sin periodo, filtros ni denominador, o con lenguaje de predicción o de riesgo.
- Comparar el recuento reciente con el histórico sin los mismos filtros (M≥4 y mismo ámbito), o dividir solo entre los días con eventos. Y recordar que la comparación reciente sale marcada como posiblemente incompleta.
- Mezclar replay y datos reales. Si lo enseñas, el banner «REPRODUCCIÓN» debe verse.
- Presentar datos sintéticos o del mock como si fueran reales. Deben ir etiquetados.
- Enseñar costes sin distinguir lo **medido** de lo **supuesto**.
- Mostrar el token del túnel o las credenciales del `.env` en pantalla.

---

## 4. Lo que queda

Solo lo que depende del alumno: grabar el vídeo (con las pruebas 9 y 10 y la demo H4 en vivo, según 3.3) y poner su enlace en el marcador `PENDIENTE: enlace de YouTube` del README. Las demás decisiones (captura H3 aceptada, pruebas 9 y 10 por vídeo, clon limpio no repetido) están registradas en «Pendientes del alumno» y «Limitaciones conocidas» del README.
