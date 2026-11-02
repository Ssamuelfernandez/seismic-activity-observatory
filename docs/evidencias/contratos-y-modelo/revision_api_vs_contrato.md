# Revisión de `api.md` frente a `CONTRATO-API.md` (T016, SC-005)

- **Fecha:** 2026-11-02
- **Revisado:** `specs/001-contratos-y-modelo/contracts/api.md` (§1–§7) contra `docs/enunciado/CONTRATO-API.md` (solo lectura, no modificado).
- **Método:** lectura manual de cada afirmación del contrato del profesor y localización de la sección de `api.md` que la recoge, comprobando que no la contradice. La tabla de `api.md` §7 se contrastó línea a línea.

## Resultado

**Sin contradicciones.** Todo lo que exige el contrato del profesor está recogido; `api.md` solo añade campos y reglas en lo que el contrato deja abierto.

## Revisión línea a línea

| # | Contrato del profesor | `api.md` | Resultado |
|---|---|---|---|
| 1 | `/api/eventos`: HTTP 200, `application/json`, `FeatureCollection` | §3, §1 (todos los endpoints responden JSON) | Cumple |
| 2 | Sin eventos: `features: []`, no un error | §3 | Cumple |
| 3 | Cada evento una sola vez, versión actual | §3 (una fila actual por evento) | Cumple |
| 4 | Por defecto, últimas 24 horas | §3, §3.1 (rango por defecto: ahora − 24 h … ahora) | Cumple |
| 5 | `metadata`: `generated`, `last_ingestion`, `mode`, `count`, `truncated` | §3.2 (los cinco, más `total`, `next_cursor`, `null_mag_excluded`) | Cumple y amplía |
| 6 | `generated` = generación de la respuesta, sin implicar ingesta activa; `last_ingestion` = última consulta correcta a USGS | §3.2 | Cumple |
| 7 | `properties`: `mag`, `magType`, `place`, `time`, `updated`, `country_id`, `country_name` | §3.4 (los siete, más `is_synthetic`, `status`, `url`, `sig`) | Cumple y amplía |
| 8 | Fechas en milisegundos Unix UTC | §1 | Cumple |
| 9 | Coordenadas `[longitud, latitud, profundidad_km]` | §1, §3.5 | Cumple |
| 10 | `null`, nunca NaN/Infinity, para magnitud, profundidad o país desconocidos | §1, §3.4 | Cumple |
| 11 | Geometría válida obligatoria | §3.4 (siempre un `Point` válido); inválidos van a cuarentena (`kafka-message.md` §6) | Cumple |
| 12 | Filtros `start` (ISO 8601, inclusive), `end` (exclusive), `min_mag`, `country_id` | §3.1 | Cumple |
| 13 | La magnitud nula no cumple `min_mag` y se contabiliza aparte | §3.1, §3.2 (`null_mag_excluded`) | Cumple |
| 14 | Máximo documentado de puntos; si trunca: `truncated: true`, total completo y paginación | §3.1 (`limit` máx. 5 000), §3.2 (`truncated`, `total`, `next_cursor`), §3.3 | Cumple |
| 15 | El panel no calcula estadísticas sobre una muestra truncada | §1 (la API calcula), §5 (sin `limit`/`cursor`; se calcula sobre todos los eventos) | Cumple |
| 16 | `/api/salud`: estado de la API y fecha de última ingesta; sin credenciales | §4 | Cumple |
| 17 | `/api/estadisticas`: conteos por hora UTC y por país, distribuciones, comparación histórica | §5.1 (`by_hour`, `by_country`, `histograms`, `comparison`) | Cumple |
| 18 | Filtros de estadísticas equivalentes a los del mapa | §5 (mismos `start`, `end`, `min_mag`, `country_id`, `mode`) | Cumple |
| 19 | Cada resultado indica periodo, filtros, unidad y registros sin valor | §5.1 (`period`, `filters`; `unit` y `no_value` en cada bloque) | Cumple |
| 20 | Si la base falla, error explícito; no cero eventos como resultado válido | §6 (503 `database_unavailable` en los tres endpoints) | Cumple |
| 21 | CORS (origen de la web y `http://localhost:4200`; GET y OPTIONS; cabecera `ngrok-skip-browser-warning`) | §1 (solo GET y OPTIONS; remite al contrato) | Cumple (no se redefine) |
| 22 | Transporte: servicio Docker, Uvicorn en `0.0.0.0:8000`, ngrok | §1 (remite al contrato) | Cumple (no se redefine) |

## Lo que `api.md` añade (no contradice nada)

- `metadata.total` y `metadata.next_cursor` se devuelven siempre, aunque no haya truncado; el ejemplo del profesor solo muestra los cinco campos mínimos y no prohíbe más.
- `truncated` es `true` en cada página con `count < total`, también en la última; coincide con la definición del contrato («no contiene todos los eventos») y el final lo marca `next_cursor: null`.
- Cuatro campos extra en `properties` (`is_synthetic`, `status`, `url`, `sig`).
- Parámetros `mode`, `limit` y `cursor`; valor reservado `country_id=none`.
- Formato de error común y códigos (§6), que el contrato deja sin definir.
- `/api/salud` con `status: "ok"` y error 503 si falla la base.

## Observaciones

- El contrato dice que el mapa inicial aún no envía filtros y que el componente inicial espera una colección pequeña y completa: sin filtros, `api.md` devuelve las últimas 24 h, y mientras `total ≤ 5 000` la respuesta es completa y `truncated` es `false`.
- Ningún cambio necesario en `api.md` ni en `docs/enunciado/`.
