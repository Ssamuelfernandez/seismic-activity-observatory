# Contrato del mensaje Kafka (productor → consumidor)

Fuente de verdad del mensaje que viaja del productor al consumidor. Las demás features lo referencian y no lo redefinen (constitución §15). Parte de la propuesta del roadmap §1 y la confirma o ajusta; cada ajuste está marcado.

El campo `is_synthetic` y la lista de motivos de cuarentena (§6) están **DECIDIDOS** (aprobados por el alumno el 2026-11-02) y registrados en `spec.md`, sección Clarifications.

## 1. Topics

| Topic | Modo | Particiones | Factor de replicación | Retención | Quién publica | Quién consume |
|---|---|---|---|---|---|---|
| `earthquakes.live` | `live` | 1 | 1 | 7 días (`retention.ms=604800000`) | productor en vivo | consumidor (esquema `live`) |
| `earthquakes.replay` | `replay` | 1 | 1 | 7 días (`retention.ms=604800000`) | productor de replay | consumidor (esquema `replay`) |

- **1 partición:** el orden por clave queda garantizado. El orden no sustituye la comparación de `updated` (ENUNCIADO §7).
- **Factor de replicación 1:** hay un único broker (Docker Compose, 5 servicios).
- **7 días de retención:** cubre una caída del consumidor de varios días sin perder mensajes; el estado vive en PostgreSQL, no en Kafka.
- El histórico 2025 se carga por lote directamente en el esquema `live` (feature `historico-2025`) y no pasa por Kafka. El valor `usgs_historical` de `source` queda reservado para ese origen (ver §3).

### Aislamiento del replay (J3)

1. **Canal separado:** el replay solo publica en `earthquakes.replay`.
2. **Espacio de datos separado:** el consumidor enruta por el topic de origen a PostgreSQL: `earthquakes.live` → esquema `live`; `earthquakes.replay` → esquema `replay` (ver `db-schema.md`).
3. **Comprobación cruzada:** el campo `mode` del mensaje debe coincidir con el modo del topic del que se lee. Si no coincide, el mensaje no se escribe en ninguna tabla de eventos: va a `quarantine` del esquema que corresponde al **topic** con motivo `mode_topic_mismatch`.

## 2. Clave y valor

- **Clave:** `event.id` (identificador de USGS, p. ej. `ci41570768`), cadena UTF-8. Se usa para el orden por evento; no es única por mensaje (un evento tiene varias versiones). Si falta `event.id`, la clave del mensaje es nula y el consumidor lo lleva a `quarantine` con motivo `missing_id`.
- **Valor:** JSON UTF-8 con la estructura de §3.
- **Cabeceras Kafka:** ninguna.
- **Garantía de entrega:** al menos una vez. El consumidor es idempotente (`db-schema.md` §5), por lo que un mensaje repetido no cambia el resultado.

## 3. Campos del valor

| Campo | Tipo | Obligatorio | Valores / formato | Significado |
|---|---|---|---|---|
| `source` | cadena | sí | `usgs_feed` \| `usgs_historical` \| `replay_demo` | Origen del evento. `usgs_feed`: consulta al feed reciente. `usgs_historical`: archivos del histórico 2025 (reservado, ver §1). `replay_demo`: evento reproducido o fabricado para la demostración. |
| `mode` | cadena | sí | `live` \| `replay` | Modo de procesamiento. `live` solo viaja por `earthquakes.live`; `replay`, solo por `earthquakes.replay`. |
| `ingested_at` | cadena | sí | ISO 8601 UTC con sufijo `Z`, p. ej. `2026-11-01T14:33:24Z` (se admiten fracciones de segundo) | Instante en que el productor obtuvo el evento de su origen (respuesta del feed o archivo). Es tiempo de procesamiento, no del evento. |
| `replay_at` | cadena o `null` | sí | ISO 8601 UTC con `Z`, o `null` | Instante en que el replay publicó el mensaje. `null` si `mode = live`; obligatorio (no nulo) si `mode = replay`. Si falta, el consumidor lo lleva a `quarantine` con motivo `replay_at_missing`. |
| `is_synthetic` | booleano | sí | `true` \| `false` | **DECIDIDO.** Marca el evento como sintético o de prueba (constitución §7). El consumidor la copia a `is_synthetic` de las tablas. Sin este campo el consumidor no podría distinguir un evento sintético de uno real. Es un campo añadido respecto al roadmap §1. |
| `event` | objeto | sí | Feature GeoJSON **tal como lo entrega USGS, sin modificar** | Evento original: `id`, `geometry`, `properties` completos. Se conserva íntegro en `event_version.original`. |

Reglas del valor:

- **`event` no se transforma.** Los tiempos siguen en milisegundos Unix; la conversión a UTC la hace el consumidor conservando el original (constitución §3).
- **Nulos:** `event.properties.mag` y `event.geometry.coordinates[2]` pueden ser `null`; el productor no los rellena con 0 (constitución §5). Magnitudes y profundidades negativas son válidas.
- **Campos desconocidos** de primer nivel: el consumidor los ignora; los de `event` se conservan en el original.
- **Eventos con `event.properties.type` distinto de `earthquake`:** el productor no los publica; los registra en `exclusion` (B3).
- **Eventos inválidos** (sin `id`, sin `time` o `updated`, geometría ausente o fuera de rango): el productor sí los publica y el consumidor los lleva a `quarantine` con motivo y referencia al original. La invalidez tiene prioridad sobre la exclusión por tipo.
- **Mensaje que no es JSON válido o carece de campos de primer nivel obligatorios:** va a `quarantine` con `raw_text` y motivo `invalid_json` o `invalid_envelope`. No bloquea la cola.

## 4. Ejemplo (evento real del feed, `docs/evidencias/f1/explore_usgs_salida.txt`)

Clave: `ci41570768`. Topic: `earthquakes.live`.

```json
{
  "source": "usgs_feed",
  "mode": "live",
  "ingested_at": "2026-11-01T14:33:24Z",
  "replay_at": null,
  "is_synthetic": false,
  "event": {
    "type": "Feature",
    "properties": {
      "mag": -0.06,
      "place": "3 km WSW of Anza, CA",
      "time": 1793528210440,
      "updated": 1793528420510,
      "tz": null,
      "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci41570768",
      "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/ci41570768.geojson",
      "felt": null,
      "cdi": null,
      "mmi": null,
      "alert": null,
      "status": "automatic",
      "tsunami": 0,
      "sig": 0,
      "net": "ci",
      "code": "41570768",
      "ids": ",ci41570768,",
      "sources": ",ci,",
      "types": ",nearby-cities,origin,phase-data,",
      "nst": 16,
      "dmin": 0.03898,
      "rms": 0.13,
      "gap": 54,
      "magType": "ml",
      "type": "earthquake",
      "title": "M -0.1 - 3 km WSW of Anza, CA"
    },
    "geometry": {
      "type": "Point",
      "coordinates": [-116.701666666667, 33.5401666666667, 6.39]
    },
    "id": "ci41570768"
  }
}
```

Ejemplo de mensaje de replay (mismo evento, otro canal): `mode = "replay"`, `source = "replay_demo"`, `replay_at = "2026-11-02T09:00:02Z"`, topic `earthquakes.replay`. El resto de campos no cambia; `event.properties.time` conserva el instante original del terremoto.

## 5. Reglas de versiones (C4)

Se aplican en el consumidor, sobre `(event_id, updated_ms)`. El detalle de SQL está en `db-schema.md` §5.

| Caso | Condición | Estado actual (`current_event`) | Historial (`event_version`) |
|---|---|---|---|
| Evento nuevo | `event_id` no existe | se inserta | se inserta |
| Reenvío | mismo `event_id` y mismo `updated` | no cambia | no se duplica |
| Versión más reciente | `updated` entrante **estrictamente mayor** que el guardado | se sustituye | se inserta |
| Versión antigua tardía | `updated` entrante menor que el guardado y no visto antes | no cambia | se inserta (se conserva sin pisar la posterior) |
| Mismo `updated`, contenido distinto | igual `updated`, `original` distinto | no cambia | no cambia: se conserva la primera recibida |

- Solo gana una versión con `updated` **estrictamente mayor**. Una versión con `updated` menor o igual nunca sustituye a una mayor.
- Un evento = una fila actual.
- Toda versión con un `updated` no visto antes para ese evento se conserva.
- Caso «mismo `updated`, contenido distinto»: la segunda versión se ignora, se anota en el log con el `event_id` y se cuenta en los contadores de transformaciones del consumidor (C8).
- El offset de Kafka se confirma **después** del commit en PostgreSQL (constitución §1).

## 6. Motivos de cuarentena originados por este contrato

**DECIDIDO** (lista inicial, ampliable en las features `consumidor-idempotente` y `geografia-pais`):

| `reason` | Cuándo |
|---|---|
| `invalid_json` | El valor no es JSON válido. |
| `invalid_envelope` | Falta `source`, `mode`, `ingested_at`, `is_synthetic` o `event`, o tienen valores no permitidos. |
| `mode_topic_mismatch` | `mode` no coincide con el modo del topic. |
| `missing_id` | `event.id` ausente o vacío. |
| `missing_time` | `event.properties.time` ausente o no entero. |
| `missing_updated` | `event.properties.updated` ausente o no entero. |
| `invalid_geometry` | Geometría ausente, no `Point` o con menos de 2 coordenadas. |
| `coordinates_out_of_range` | Longitud fuera de [-180, 180] o latitud fuera de [-90, 90], o no finitas. |
| `mag_out_of_range` | `mag` fuera de −10…15 (incluye `NaN` e infinitos). |
| `depth_out_of_range` | Profundidad (`coordinates[2]`) fuera de −100…1000 (incluye `NaN` e infinitos). |
| `invalid_field_type` | Campo con tipo incorrecto (p. ej. `sig` no entero, `status` no texto, `mag` no numérico). |
| `replay_at_missing` | `mode = replay` sin `replay_at`. |
| `value_out_of_range` | `sig` fuera del rango de `integer`, o `time`/`updated` que desbordan `timestamptz`. |
| `db_constraint_violation` | Motivo de último recurso: la base rechaza el `INSERT` aunque el mensaje pasó todas las validaciones anteriores. |

**Un mensaje, una fila de cuarentena.** Si un mensaje incumple varias validaciones, se registra una sola fila con el **primer** motivo que falle en este orden de prevalencia: `invalid_json`, `invalid_envelope`, `mode_topic_mismatch`, `missing_id`, `missing_time`, `missing_updated`, `invalid_geometry`, `coordinates_out_of_range`, `mag_out_of_range`, `depth_out_of_range`, `invalid_field_type`, `value_out_of_range`, `db_constraint_violation`.

**Validación previa a la base:** el consumidor valida estos límites y tipos **antes** de insertar y lleva a cuarentena lo que no los cumpla. Los `CHECK` de la base son la última barrera (ver `db-schema.md` §2). Si aun así la base rechaza el `INSERT`, se aplica el motivo de último recurso `db_constraint_violation`: el consumidor hace `rollback` de ese mensaje, lo lleva a `quarantine` con ese motivo y confirma el offset, sin bloquear la cola.

## 7. Cambios respecto al roadmap §1

| Cambio | Motivo |
|---|---|
| Se añade `is_synthetic` al mensaje | La spec exige separar y etiquetar datos sintéticos; el mensaje es el único canal hacia el consumidor. |
| Se fija el factor de replicación en 1 | Un solo broker. |
| Se define la comprobación `mode` ↔ topic | Refuerza el aislamiento del replay (J3). |
