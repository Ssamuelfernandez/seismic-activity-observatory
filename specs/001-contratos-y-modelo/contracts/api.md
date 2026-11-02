# Contrato de la API (API → panel)

Fuente de verdad de la API del proyecto. Parte del contrato mínimo del profesor (`docs/enunciado/CONTRATO-API.md`, solo lectura) **sin contradecirlo** y resuelve lo que ese contrato deja abierto (`docs/planificacion/decisiones-abiertas-contrato.md`). Las demás features lo referencian y no lo redefinen (constitución §15).

Todas las decisiones están **DECIDIDAS** y registradas en `spec.md`, sección Clarifications. Se fijaron en dos pasos: en `/speckit-clarify` y, el 2026-11-02, con la aprobación por el alumno de todas las propuestas del plan para lo que la spec dejaba sin decidir. Ninguna se reabre sin avisar.

Convención de nombres: los campos fijados por el profesor o por una aclaración se respetan tal cual (`country_id`, `n_reciente`, `media_diaria_2025`, `variacion_pct`, `sin_valor`…). Los campos nuevos que propone este documento van en inglés (constitución §13).

## 1. Reglas generales

- Fechas y horas: **milisegundos Unix UTC** (entero) en toda respuesta. **DECIDIDO** para `/api/eventos` (contrato); aplicado igual a `/api/salud` y `/api/estadisticas` por coherencia (decisión propia para la parte no cubierta por el contrato del profesor).
- Desconocido = `null`; nunca `NaN`, `Infinity` ni 0 de relleno (constitución §5).
- Coordenadas en orden `[longitud, latitud, profundidad_km]`; la profundidad puede ser `null` y puede ser negativa.
- Magnitudes y profundidades negativas son válidas.
- Solo métodos `GET` y `OPTIONS`. CORS, cabecera `ngrok-skip-browser-warning` y transporte: según `CONTRATO-API.md` (sección «Acceso desde Netlify» y «Transporte»); no se redefinen aquí.
- Todos los endpoints responden `Content-Type: application/json`.
- La API calcula; el frontend no calcula estadísticas (constitución §17).

## 2. Resumen de decisiones sobre los puntos abiertos

| Punto abierto | Decisión | Estado |
|---|---|---|
| 1. Forma de `/api/salud` | `status`, `last_ingestion`, `generated`; 503 si falla la base; umbral de desactualizado en `config.json` del panel | DECIDIDO |
| 1. Forma de `/api/salud`: ¿informa del modo? | No | DECIDIDO |
| 1. Forma completa de `/api/estadisticas` | Ver §5 | DECIDIDO |
| 2. Paginación | Cursor opaco; orden `event_time` + `id`; máximo 5 000 configurable; `limit` menor permitido | DECIDIDO |
| 2. Nombres: `limit`, `cursor`, `total`, `next_cursor`; sentido del orden; `truncated` | Ver §3 | DECIDIDO |
| 3. Modo | Parámetro `mode=live\|replay`, por defecto `live`, `metadata.mode`; `generated`/`last_ingestion` en replay | DECIDIDO |
| 3. Estadísticas de comparación en `replay` | `comparison: null` | DECIDIDO |
| 4. País y campos | País nulo → ambos `null`; `properties` de once campos; `magType` puede ser `null` | DECIDIDO |
| 4. Nulabilidad de `status`, `url`, `sig` | Pueden ser `null` | DECIDIDO |
| 5. Filtros | Magnitudes nulas en `metadata`; `start`/`end` sin zona = UTC | DECIDIDO |
| 5. Nombre del campo de nulos (`null_mag_excluded`); `country_id` único y valor `none`; rangos incompletos; parámetros inválidos | Ver §3.1 | DECIDIDO |
| 6. Error común | `{"error":{"code","message"}}`; 400 y 503 | DECIDIDO |
| 6. Lista de códigos de error | Ver §6 | DECIDIDO |

## 3. `GET /api/eventos`

Devuelve un GeoJSON `FeatureCollection` con la versión actual de cada evento (una sola vez). Sin eventos: `features: []`, HTTP 200. Por defecto, terremotos de las últimas 24 horas.

### 3.1 Parámetros de consulta

| Parámetro | Tipo | Obligatorio | Descripción | Estado |
|---|---|---|---|---|
| `start` | ISO 8601 | no | Inicio inclusivo. Sin zona horaria = UTC; solo fecha = 00:00 UTC de ese día | contrato + DECIDIDO |
| `end` | ISO 8601 | no | Fin exclusivo. Misma interpretación | contrato + DECIDIDO |
| `min_mag` | número | no | Magnitud mínima (inclusive). La magnitud nula **no** la cumple y se cuenta aparte | contrato |
| `country_id` | texto | no | Un único `ADM0_A3` (p. ej. `ESP`). Se admite un solo valor; el valor reservado `none` selecciona los eventos «Sin país asignado» | DECIDIDO |
| `mode` | `live` \| `replay` | no | Por defecto `live`. Otro valor → error 400 | DECIDIDO |
| `limit` | entero ≥ 1 | no | Máximo de eventos en la respuesta. Por defecto y máximo: 5 000 (constante configurable). Un valor mayor → error 400 | DECIDIDO |
| `cursor` | texto opaco | no | Valor de `metadata.next_cursor` de la respuesta anterior; se repiten los mismos filtros | DECIDIDO |

Rango por defecto cuando faltan `start` o `end` (**DECIDIDO**; usa la hora del servidor):

| Se envía | `start` efectivo | `end` efectivo |
|---|---|---|
| Ninguno | ahora − 24 h | ahora |
| Solo `start` | `start` | ahora |
| Solo `end` | `end` − 24 h | `end` |
| Ambos | `start` | `end` |

Si `start >= end`, error 400 `invalid_parameter`. `min_mag` no numérico, `country_id` que no cumple `^[A-Za-z]{3}$|^none$`, fecha no ISO 8601, `limit` fuera de rango o `mode` desconocido → error 400 `invalid_parameter`. Un `country_id` con forma válida que no exista en el catálogo no es un error: devuelve `features: []`.

### 3.2 `metadata`

| Campo | Tipo | Descripción | Estado |
|---|---|---|---|
| `generated` | entero (ms) | Instante de generación de esta respuesta. Siempre hora real, también en `replay` | contrato + DECIDIDO |
| `last_ingestion` | entero (ms) o `null` | Última consulta correcta a USGS **del modo en vivo**, también en `replay`. `null` si aún no hubo ingesta | contrato + DECIDIDO |
| `mode` | `"live"` \| `"replay"` | Modo servido | contrato + DECIDIDO |
| `count` | entero | Número de eventos **de esta respuesta** | DECIDIDO |
| `total` | entero | Número de eventos que cumplen los filtros (en todas las páginas) | DECIDIDO |
| `truncated` | booleano | `true` si esta respuesta no contiene todos los eventos que cumplen los filtros (`count < total`). En la última página de una consulta paginada sigue siendo `true`; `next_cursor` indica si hay más | contrato + DECIDIDO |
| `next_cursor` | texto o `null` | Cursor de la página siguiente; `null` en la última | DECIDIDO |
| `null_mag_excluded` | entero | Eventos con magnitud nula que cumplen el resto de filtros y se excluyen por `min_mag`. `0` si no se envía `min_mag` | DECIDIDO |

### 3.3 Orden y cursor

- Orden estable: `event_time` **descendente** y, a igualdad, `id` descendente (más reciente primero). **DECIDIDO** (criterio: tiempo del evento + `id`; sentido descendente).
- Paginación por clave (`keyset`): el cursor identifica la posición `(event_time, id)` del último evento devuelto; la página siguiente son los eventos estrictamente posteriores en ese orden (`ix_current_event_time`, consulta Q1).
- **DECIDIDO** el formato: cadena opaca (base64url de un JSON con el instante en ms y el `id`). El cliente no la interpreta ni la modifica; un cursor mal formado → error 400 `invalid_cursor`.
- Un evento que recibe una revisión conserva su `time` e `id`, así que no cambia de posición entre páginas.

### 3.4 `properties` (lista cerrada de once campos — DECIDIDO)

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| `mag` | número | sí | `null` si desconocida; −0,06 es válido |
| `magType` | texto | sí | `ml`, `md`, `mb`, `mww`, `mwr`… |
| `place` | texto | no\* | Descripción de USGS; no se usa para el país |
| `time` | entero (ms) | no | Instante del terremoto |
| `updated` | entero (ms) | no | Última actualización |
| `country_id` | texto | sí | `ADM0_A3`; `null` = sin país |
| `country_name` | texto | sí | `NAME_ES` del catálogo; `null` = sin país |
| `is_synthetic` | booleano | no | `true` en datos sintéticos o de mock |
| `status` | texto | sí\*\* | Estado de revisión de USGS (`automatic`, …) |
| `url` | texto | sí\*\* | Página del evento en USGS |
| `sig` | entero | sí\*\* | Significancia de USGS |

\* `place` es texto en los 210 eventos de la muestra; si faltara, se serializa `null`. \*\* **DECIDIDO:** nulable (el feed de la muestra los trae siempre, pero el contrato no lo garantiza).

`id` de la Feature = `id` del evento en USGS. La geometría es siempre un `Point` válido.

### 3.5 Ejemplo completo

Dos eventos reales de `docs/evidencias/f1/explore_usgs_salida.txt` (`ci41570832`, profundidad negativa, que cae en el mar según el catálogo; y `ci41570768`, magnitud negativa, en EE. UU.). El primero tiene `country_id` y `country_name` a `null`. `generated`/`last_ingestion` son los del momento de la muestra (`2026-11-01T14:34:00Z` y `14:33:24Z`).

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generated": 1793543640000,
    "last_ingestion": 1793543604000,
    "mode": "live",
    "count": 2,
    "total": 2,
    "truncated": false,
    "next_cursor": null,
    "null_mag_excluded": 0
  },
  "features": [
    {
      "type": "Feature",
      "id": "ci41570832",
      "geometry": {
        "type": "Point",
        "coordinates": [-119.087833333333, 33.4166666666667, -0.01]
      },
      "properties": {
        "mag": 2.64,
        "magType": "ml",
        "place": "7 km SSW of Santa Barbara Is., CA",
        "time": 1793536750750,
        "updated": 1793536964214,
        "country_id": null,
        "country_name": null,
        "is_synthetic": false,
        "status": "automatic",
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci41570832",
        "sig": 107
      }
    },
    {
      "type": "Feature",
      "id": "ci41570768",
      "geometry": {
        "type": "Point",
        "coordinates": [-116.701666666667, 33.5401666666667, 6.39]
      },
      "properties": {
        "mag": -0.06,
        "magType": "ml",
        "place": "3 km WSW of Anza, CA",
        "time": 1793528210440,
        "updated": 1793528420510,
        "country_id": "USA",
        "country_name": "Estados Unidos",
        "is_synthetic": false,
        "status": "automatic",
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci41570768",
        "sig": 0
      }
    }
  ]
}
```

Ejemplo de respuesta truncada (solo `metadata`, con 5 000 de 6 213 eventos): `"count": 5000, "total": 6213, "truncated": true, "next_cursor": "<cadena opaca>"`.

Con `min_mag=4` y 3 eventos de magnitud nula en el intervalo: `"null_mag_excluded": 3`.

## 4. `GET /api/salud`

Estado de la API y fecha de la última ingesta. No devuelve credenciales ni datos de conexión.

| Campo | Tipo | Descripción | Estado |
|---|---|---|---|
| `status` | `"ok"` | `"ok"` si la API y la base responden. No existe otro valor: si la base falla se devuelve un error 503, no un estado degradado | DECIDIDO |
| `last_ingestion` | entero (ms) o `null` | Última consulta correcta a USGS; `null` si aún no hubo ingesta | DECIDIDO |
| `generated` | entero (ms) | Generación de esta respuesta | DECIDIDO |

- El umbral de «datos desactualizados» **no** lo calcula la API: vive en el `config.json` del panel y el panel compara `generated − last_ingestion` con fechas del servidor. **DECIDIDO.**
- **DECIDIDO:** `/api/salud` **no** informa del modo. `last_ingestion` es siempre el del modo en vivo (aclaración), así que el modo no cambia su significado.
- Si la base falla: HTTP 503 con el cuerpo de error común (§6).

```json
{
  "status": "ok",
  "last_ingestion": 1793543604000,
  "generated": 1793543640000
}
```

## 5. `GET /api/estadisticas`

Mismos filtros que `/api/eventos`: `start`, `end`, `min_mag`, `country_id`, `mode`, con las mismas reglas de §3.1. **No** admite `limit` ni `cursor`: las cifras se calculan en SQL sobre **todos** los eventos que cumplen los filtros, no sobre una muestra truncada (constitución §8). Todo se calcula desde `current_event` del esquema del modo.

### 5.1 Estructura (DECIDIDA)

| Bloque | Contenido |
|---|---|
| `metadata` | `generated`, `last_ingestion`, `mode` (mismo significado que en `/api/eventos`) |
| `period` | `{"start", "end"}` en ms, rango efectivo `[start, end)` tras aplicar los valores por defecto |
| `filters` | Filtros aplicados: `min_mag` (número o `null`), `country_id` (texto o `null`) |
| `total` | Eventos que cumplen los filtros |
| `by_hour` | Recuento por hora UTC fija, según `event_time`; incluye las horas con cero eventos |
| `by_country` | Recuento por país, con la categoría «Sin país asignado» |
| `histograms.magnitude` / `histograms.depth` | Distribuciones (DECIDIDO: tramos y «sin valor») |
| `comparison` | Últimas 24 h frente a la media diaria de 2025 (DECIDIDO: campos principales) |

Cada bloque con resultados lleva `unit` (unidad) y `sin_valor` (registros sin valor), como exige el contrato del profesor.

**`by_hour`** — `unit: "events"`. `buckets`: lista de `{"hour_start": <ms>, "count": <entero>}`. Una entrada por cada hora UTC fija `[h, h+1)` que se solape con `period`; el recuento solo incluye eventos dentro de `period`. `sin_valor`: `0` (`event_time` no admite nulo).

**`by_country`** — `unit: "events"`. `items`: lista de `{"country_id", "country_name", "subregion", "count"}` ordenada por `count` descendente y `country_id` ascendente. Los eventos sin país forman **un elemento propio** con `country_id`, `country_name` y `subregion` a `null` (el panel lo muestra como «Sin país asignado»). `sin_valor` = recuento de ese elemento (informativo; **no se suma** a `items`). **DECIDIDO** para el país nulo.

**`histograms.magnitude`** — `unit: "dimensionless"` (la escala depende de `magType`). `bins`: lista de `{"lower", "upper", "count"}` con límite inferior inclusivo y superior exclusivo; **DECIDIDO:** ocho tramos `<1` (`lower: null`, incluye negativos), `1–2`, `2–3`, `3–4`, `4–5`, `5–6`, `6–7` y `≥7` (`upper: null`). `sin_valor`: eventos con magnitud nula que cumplen los demás filtros **sin contar `min_mag`**; con `min_mag` enviado coincide con `null_mag_excluded` de `/api/eventos` (**DECIDIDO** el concepto).

**`histograms.depth`** — `unit: "km"`. **DECIDIDO:** cinco tramos `<10` (`lower: null`, incluye profundidades negativas), `10–35`, `35–70`, `70–300` y `≥300` (`upper: null`). `sin_valor`: eventos con profundidad nula.

**`comparison`** — **DECIDIDO:** compara las **últimas 24 horas** con la **media diaria de 2025**.

| Campo | Tipo | Descripción | Estado |
|---|---|---|---|
| `n_reciente` | entero | Eventos de las últimas 24 h con los filtros pedidos, salvo las fechas | DECIDIDO |
| `n_2025` | entero | Eventos de 2025 con los mismos filtros, salvo las fechas | DECIDIDO |
| `media_diaria_2025` | número | `n_2025 / 365` (incluye los días con cero eventos) | DECIDIDO |
| `diff_abs` | número | `n_reciente − media_diaria_2025` (con signo) | DECIDIDO |
| `variacion_pct` | número o `null` | `diff_abs / media_diaria_2025 × 100`, 2 decimales; `null` si no hay base de comparación (media 0) | DECIDIDO |
| `recent_incomplete` | booleano | `true` siempre: el periodo reciente puede estar incompleto por retrasos de USGS (`updated − time` llegó a 1 125 min en la muestra) | DECIDIDO |
| `min_mag_applied` | número | Magnitud mínima efectiva de la comparación: `max(min_mag solicitado, 4.0)` | DECIDIDO |
| `recent_period` | `{"start","end"}` (ms) | Últimas 24 h hasta `generated` | DECIDIDO |
| `reference_period` | `{"start","end"}` (ms) | `2025-01-01T00:00Z` (incl.) – `2026-01-01T00:00Z` (excl.) | DECIDIDO |
| `unit` | texto | `"events"` (`media_diaria_2025` y `diff_abs` en eventos por día) | DECIDIDO |

- **`min_mag_applied`:** el histórico cargado solo contiene M ≥ 4 (roadmap F6). Comparar sin límite inferior las últimas 24 h (todas las magnitudes) con un 2025 de M ≥ 4 daría una variación sin sentido, y el enunciado §8 compara «magnitud ≥ 4». Por eso ambos lados usan al menos M ≥ 4 y `min_mag_applied` lo declara. Esta decisión **concreta** la aclaración «con los filtros pedidos» (aprobada el 2026-11-02).
- **DECIDIDO:** en `mode=replay`, `comparison` es `null` (la reproducción no tiene «últimas 24 horas» ni histórico propio).

### 5.2 Ejemplo completo

Calculado sobre los 210 eventos reales de la muestra del feed (`docs/evidencias/f1/explore_usgs_salida.txt`, ventana de 24 h hasta `2026-11-01T14:34:00Z`), con el catálogo de países real (punto en polígono). Sin filtros. **`n_2025` es ilustrativo**: todavía no hay histórico cargado; el resto de cifras es real.

```json
{
  "metadata": {
    "generated": 1793543640000,
    "last_ingestion": 1793543604000,
    "mode": "live"
  },
  "period": {"start": 1793457240000, "end": 1793543640000},
  "filters": {"min_mag": null, "country_id": null},
  "total": 210,
  "by_hour": {
    "unit": "events",
    "sin_valor": 0,
    "buckets": [
      {"hour_start": 1793455200000, "count": 3},
      {"hour_start": 1793458800000, "count": 9},
      {"hour_start": 1793462400000, "count": 9},
      {"hour_start": 1793466000000, "count": 7},
      {"hour_start": 1793469600000, "count": 5},
      {"hour_start": 1793473200000, "count": 6},
      {"hour_start": 1793476800000, "count": 5},
      {"hour_start": 1793480400000, "count": 12},
      {"hour_start": 1793484000000, "count": 13},
      {"hour_start": 1793487600000, "count": 13},
      {"hour_start": 1793491200000, "count": 6},
      {"hour_start": 1793494800000, "count": 9},
      {"hour_start": 1793498400000, "count": 11},
      {"hour_start": 1793502000000, "count": 12},
      {"hour_start": 1793505600000, "count": 5},
      {"hour_start": 1793509200000, "count": 10},
      {"hour_start": 1793512800000, "count": 9},
      {"hour_start": 1793516400000, "count": 8},
      {"hour_start": 1793520000000, "count": 7},
      {"hour_start": 1793523600000, "count": 8},
      {"hour_start": 1793527200000, "count": 11},
      {"hour_start": 1793530800000, "count": 13},
      {"hour_start": 1793534400000, "count": 14},
      {"hour_start": 1793538000000, "count": 5},
      {"hour_start": 1793541600000, "count": 0}
    ]
  },
  "by_country": {
    "unit": "events",
    "sin_valor": 47,
    "items": [
      {"country_id": "USA", "country_name": "Estados Unidos", "subregion": "Northern America", "count": 151},
      {"country_id": null, "country_name": null, "subregion": null, "count": 47},
      {"country_id": "IRN", "country_name": "Irán", "subregion": "Southern Asia", "count": 3},
      {"country_id": "MEX", "country_name": "México", "subregion": "Central America", "count": 2},
      {"country_id": "PRI", "country_name": "Puerto Rico", "subregion": "Caribbean", "count": 2},
      {"country_id": "AFG", "country_name": "Afganistán", "subregion": "Southern Asia", "count": 1},
      {"country_id": "ARG", "country_name": "Argentina", "subregion": "South America", "count": 1},
      {"country_id": "CHL", "country_name": "Chile", "subregion": "South America", "count": 1},
      {"country_id": "JPN", "country_name": "Japón", "subregion": "Eastern Asia", "count": 1},
      {"country_id": "PAN", "country_name": "Panamá", "subregion": "Central America", "count": 1}
    ]
  },
  "histograms": {
    "magnitude": {
      "unit": "dimensionless",
      "sin_valor": 0,
      "bins": [
        {"lower": null, "upper": 1, "count": 65},
        {"lower": 1, "upper": 2, "count": 64},
        {"lower": 2, "upper": 3, "count": 48},
        {"lower": 3, "upper": 4, "count": 9},
        {"lower": 4, "upper": 5, "count": 17},
        {"lower": 5, "upper": 6, "count": 5},
        {"lower": 6, "upper": 7, "count": 2},
        {"lower": 7, "upper": null, "count": 0}
      ]
    },
    "depth": {
      "unit": "km",
      "sin_valor": 0,
      "bins": [
        {"lower": null, "upper": 10, "count": 103},
        {"lower": 10, "upper": 35, "count": 65},
        {"lower": 35, "upper": 70, "count": 18},
        {"lower": 70, "upper": 300, "count": 22},
        {"lower": 300, "upper": null, "count": 2}
      ]
    }
  },
  "comparison": {
    "unit": "events",
    "min_mag_applied": 4.0,
    "recent_period": {"start": 1793457240000, "end": 1793543640000},
    "reference_period": {"start": 1735689600000, "end": 1767225600000},
    "n_reciente": 24,
    "n_2025": 12410,
    "media_diaria_2025": 34.0,
    "diff_abs": -10.0,
    "variacion_pct": -29.41,
    "recent_incomplete": true
  }
}
```

## 6. Errores (todos los endpoints)

Cuerpo común (**DECIDIDO**):

```json
{"error": {"code": "invalid_parameter", "message": "El parámetro 'min_mag' debe ser un número; se recibió 'abc'."}}
```

| HTTP | `code` | Cuándo | Estado |
|---|---|---|---|
| 400 | `invalid_parameter` | Parámetro con valor no válido (incluye `mode` desconocido, `limit` mayor que el máximo y `start >= end`) | DECIDIDO |
| 400 | `invalid_cursor` | `cursor` mal formado | DECIDIDO |
| 404 | `not_found` | Ruta inexistente | DECIDIDO |
| 405 | `method_not_allowed` | Método distinto de `GET`/`OPTIONS` | DECIDIDO |
| 503 | `database_unavailable` | Falla la base de datos | DECIDIDO |
| 500 | `internal_error` | Error inesperado de la API | DECIDIDO |

- `message` está en español, es legible y nunca incluye credenciales, consultas SQL ni trazas.
- **Nunca** se devuelve `features: []` ni cero eventos como si fuera un resultado válido cuando la base falla (contrato del profesor): `/api/eventos`, `/api/estadisticas` y `/api/salud` devuelven 503.

Ejemplo `503`:

```json
{"error": {"code": "database_unavailable", "message": "No se pudo consultar la base de datos. Inténtalo de nuevo más tarde."}}
```

## 7. Conformidad con el contrato mínimo del profesor

| Contrato del profesor (`CONTRATO-API.md`) | Cumplimiento |
|---|---|
| `/api/eventos`: 200, JSON, `FeatureCollection`; sin eventos `features: []` | §3 |
| Una vez por evento, versión actual; últimas 24 h por defecto | §3, §3.1 |
| `metadata`: `generated`, `last_ingestion`, `mode`, `count`, `truncated` | §3.2 (se añaden `total`, `next_cursor`, `null_mag_excluded`) |
| `properties`: `mag`, `magType`, `place`, `time`, `updated`, `country_id`, `country_name` | §3.4 (se añaden `is_synthetic`, `status`, `url`, `sig`) |
| Fechas en ms Unix UTC; `[lon, lat, depth_km]`; `null` nunca NaN | §1 |
| Geometría válida obligatoria | §3.4 |
| Filtros `start` (incl.), `end` (excl.), `min_mag`, `country_id`; magnitud nula no cumple `min_mag` y se cuenta aparte | §3.1, §3.2 |
| Máximo documentado, `truncated: true`, total completo y paginación | §3.2, §3.3 |
| `/api/salud`: estado y fecha de última ingesta, sin credenciales | §4 |
| `/api/estadisticas`: conteos por hora UTC/país, distribuciones, comparación histórica; periodo, filtros, unidad y sin valor; error explícito | §5, §6 |
| Filtros de estadísticas equivalentes a los del mapa | §5 |
| CORS y transporte | Sin cambios (§1) |

## 8. Validación de los ejemplos contra el feed real

Valores comprobados contra `docs/evidencias/f1/explore_usgs_salida.txt` y `data/raw/explore/all_day_20261101T143324Z_86304f0d5f55.geojson`:

| Comprobación | Resultado |
|---|---|
| `ci41570768`: `mag −0.06`, `time 1793528210440`, `updated 1793528420510`, `sig 0`, profundidad `6.39` | Idéntico a la evidencia |
| `ci41570832`: `mag 2.64`, profundidad `−0.01`, `time 1793536750750`, `updated 1793536964214`, `sig 107` | Idéntico a la evidencia |
| `updated ≥ time` en ambos eventos | Sí (el feed tiene 0 casos de `updated < time`) |
| Suma de `by_hour`, `by_country` y de cada histograma = `total` (210) | Sí |
| Suma de los tramos de magnitud con ≥ 4 (17 + 5 + 2) = `n_reciente` (24) | Sí |
| Magnitud negativa (−0,06) en el primer tramo; profundidad negativa (−0,18) en el primero | Sí |
| `time` mínimo y máximo de la muestra dentro de `period` | Sí (2026-10-31T14:37 – 2026-11-01T13:52 UTC) |
| Países asignados por punto en polígono sobre `paises.geojson` (10 valores distintos; 47 eventos sin país) | Calculado con el catálogo real |
| Eventos con `type` ≠ `earthquake` | 0 en la muestra (no hay ejemplo real; ver `exclusion`) |
| Magnitud nula | 0 en la muestra; el contrato del profesor y el esquema la admiten (`null`) |
| `n_2025 = 12 410` | **Ilustrativo** (no hay histórico cargado) |
