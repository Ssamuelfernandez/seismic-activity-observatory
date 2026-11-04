# Borrador: productor-live

Apuntes para la memoria y la defensa. Cubre B2, B11 y B12. Las cifras proceden de una única exploración del feed, guardada en `docs/evidencias/f1/explore_usgs_salida.txt` (generada con `scripts/explore_usgs.py`, respuesta del 2026-11-01 a las 14:33 UTC). Es una muestra de un momento: otras horas darán otros recuentos. Lo que no se midió se dice como tal.

## B2. Respuesta del feed: estructura, tipos, unidades, opcionales, frecuencia, errores y latencia

**Origen.** `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson` (eventos de las últimas 24 horas). Fuente: ENUNCIADO §4.1 y la salida de la exploración.

**Estructura de primer nivel.** Un objeto GeoJSON con las claves `type`, `metadata`, `features` y `bbox`. `metadata` trae `generated` (milisegundos Unix), `url`, `title`, `status` (200), `api` (2.8.2) y `count`. En la muestra, `count` fue 210 y `features` tuvo 210 elementos. Cada elemento es un `Feature` con `id`, `properties` y `geometry`.

**Tipos y unidades.**

| Campo | Tipo observado | Unidad o significado |
|---|---|---|
| `properties.time`, `properties.updated` | entero | Milisegundos desde 1970 en UTC. En la muestra `updated` nunca fue anterior a `time` (0 casos) |
| `properties.mag` | número (entero o decimal) | Magnitud, sin unidad; `magType` indica la escala (`ml`, `md`, `mb`, `mww`, `mwr` en la muestra) |
| `geometry.coordinates` | lista de 3 números | Longitud, latitud (grados) y profundidad (kilómetros, según la documentación de USGS) |
| `properties.place`, `title`, `url`, `detail`, `net`, `code`, `ids`, `sources`, `types`, `status`, `type` | texto | Descriptivos |
| `properties.nst`, `sig`, `tsunami`, `felt` | entero | Número de estaciones, significancia, indicador de tsunami, informes de percepción |
| `properties.gap`, `dmin`, `rms`, `cdi`, `mmi` | número | Parámetros de calidad e intensidad de la localización |

**Opcionales y casos raros observados (de 210 eventos).**

- Presentes en los 210: `code`, `detail`, `dmin`, `gap`, `ids`, `mag`, `magType`, `net`, `nst`, `place`, `rms`, `sig`, `sources`, `status`, `time`, `title`, `tsunami`, `type`, `types`, `updated`, `url`.
- Opcionales (a menudo nulos): `alert` (4 de 210), `cdi` (14), `felt` (14), `mmi` (10). `tz` fue nulo en los 210.
- `mag` negativa: 1 caso (mínimo -0.06); no hubo `mag` nula en esta respuesta, aunque el contrato debe tolerarla.
- Profundidad negativa: 2 casos (mínimo -0,180000007152557).
- Tipo de evento: los 210 fueron `earthquake`; no apareció ningún otro tipo en esta muestra.
- Geometría: 210 `Point` con 3 coordenadas, ninguna nula ni fuera de rango.
- Identificadores: sin nulos ni duplicados dentro de la respuesta.

**Frecuencia de actualización.** Las cabeceras de la muestra fueron `Cache-Control: public, max-age=60`, `Last-Modified: Sun, 01 Nov 2026 14:33:01 GMT` y `Expires: Sun, 01 Nov 2026 14:34:01 GMT`, con `Age: 23`. Es decir, el feed se regenera aproximadamente cada 60 segundos, y por eso `POLL_SECONDS` vale 60 por defecto: consultar más a menudo devolvería casi siempre lo mismo. Además, `metadata.generated` cambia en cada regeneración aunque no haya eventos nuevos, por lo que el hash para detectar una respuesta distinta se calcula solo sobre `features`.

**Cuándo cambia un evento ya publicado.** `updated - time` fue, en minutos, de 0.6 (mínimo), 3.5 (mediana) y 1125.1 (máximo). Un evento puede revisarse de nuevo mucho después de ocurrir; por eso el productor compara `updated` con la última versión publicada y republica solo si es mayor.

**Errores.** En la exploración la respuesta fue HTTP 200 y no se provocó ni observó ningún error. Los comportamientos de fallo que el productor contempla (HTTP 429 y 5xx, tiempo de espera agotado, cuerpo que no es JSON) no están medidos contra USGS real; se prueban con un servidor simulado en `tests/support/mock_usgs.py` y se tratan con espera creciente entre intentos (valores de configuración, no medidos: 2 s inicial, 60 s máxima, con aleatoriedad). El productor no lee la cabecera `Retry-After` (ver «Límites conocidos» en `specs/004-productor-live/research.md` §10).

**Latencia y tamaño.** En la muestra: 223 ms de latencia y 150724 bytes de cuerpo. Es una sola medición; no se calcula una distribución. El tiempo de espera por operación de socket es `HTTP_TIMEOUT_SECONDS` (10 s por defecto).

## B11. Un evento que sale de la ventana no está eliminado

El feed `all_day` solo muestra las últimas 24 horas. Si un evento deja de aparecer en una respuesta posterior, el productor **no puede concluir que USGS lo haya eliminado**: lo más probable es que simplemente haya salido de la ventana. Por eso el productor no borra ni marca nada por ausencia; solo publica eventos nuevos o con `updated` mayor.

Detectar eliminaciones reales exigiría reconciliar de forma exhaustiva el contenido guardado con el catálogo de USGS (por ejemplo, consultando cada evento por su `id` o por intervalos de fechas y comparando). Esa reconciliación **es una ampliación fuera de alcance de esta feature**: quedan sin detectar los eventos que USGS retire del feed. Fuentes: ENUNCIADO §5 y `specs/004-productor-live/spec.md` (casos límite).

## B12. Hueco tras una parada de más de 24 horas

Si el productor está parado más de 24 horas, los eventos ocurridos durante la parada y que ya salieron de la ventana de `all_day` no volverán a aparecer en el feed. Hay un hueco en los datos.

**Procedimiento de recuperación (documentado, no automatizado):**

1. Determinar el intervalo sin cubrir: desde el `time` más reciente en `live.current_event` (o desde el último `fetched_at` correcto de `ingest.ingest_run`) hasta el momento del reinicio.
2. Consultar el catálogo histórico de USGS (servicio FDSN de eventos, `https://earthquake.usgs.gov/fdsnws/event/1/query`) con los parámetros `format=geojson`, `starttime` y `endtime` del intervalo. Para intervalos largos, dividir en tramos menores, porque el servicio limita el número de eventos por respuesta.
3. Pasar cada evento obtenido por las mismas reglas que el feed en vivo: exclusión de los que no son `earthquake`, comparación de `updated` con la última versión conocida, publicación en Kafka y validación por el consumidor. Así el hueco se rellena sin duplicar ni perder versiones, porque la clave `(event_id, updated_ms)` es idempotente.
4. Comprobar los recuentos de `live.current_event` y `live.event_version` antes y después.

No se ha automatizado ni ejecutado en esta feature: la carga de datos históricos y su aislamiento de los datos en vivo pertenecen a las features `historico-2025` y `replay`. Fuentes: ENUNCIADO §5 y documentación pública del servicio de eventos de USGS.

## Qué no se hizo

- No se midió la distribución de latencia ni el comportamiento de USGS ante 429 o caídas.
- No se detectan eventos eliminados por USGS (B11).
- No se automatiza la recuperación del hueco (B12).

## Límites conocidos

- El reenvío por corte entre el ack de Kafka y la marca en PostgreSQL solo se probó en test (publicador falso), no en vivo.
- T010 se hizo sin TDD estricto: no se comprobó que la prueba fallara antes de implementar.
- Tres rutas futuras de `CODEMAP.md` apuntan a archivos aún inexistentes (situación preexistente, no causada por esta feature).
