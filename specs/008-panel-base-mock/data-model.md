# Data Model: Panel base con mock y mapa

No hay base de datos. Son los tipos del frontend. Los de contrato se citan de `specs/001-contratos-y-modelo/contracts/api.md` (§3.2 y §3.4) y no se redefinen; aquí solo se anota lo que el panel hace con ellos. Ubicación (D3 opción C, decidida por el alumno el 2026-11-05): `src/shared/types/contract.ts` los de contrato; el resto, junto a quien los usa.

## Entidades del contrato (resumen, fuente: `api.md`)

**EventsResponse** (`FeatureCollection`): `type`, `metadata`, `features: EventFeature[]`.

**Metadata** (ocho campos): `generated` (ms), `last_ingestion` (ms o `null`), `mode` (`live`/`replay`), `count`, `total`, `truncated`, `next_cursor` (texto o `null`), `null_mag_excluded`. El panel solo muestra `count` y `total` tal cual; el resto se conserva sin uso (lo usan `009`, `011` y `013`).

**EventFeature**: `type: "Feature"`, `id` (texto), `geometry` (`Point`, `coordinates: [lon, lat, depth_km | null]`), `properties: EventProperties`.

**EventProperties** (once campos): `mag` (número o `null`), `magType` (texto o `null`), `place` (texto o `null`), `time` (ms), `updated` (ms), `country_id` / `country_name` (texto o `null`), `is_synthetic` (booleano), `status` / `url` (texto o `null`), `sig` (entero o `null`).

Reglas que el panel aplica:

| Valor | Regla |
|---|---|
| `mag` nula | Símbolo ND de magnitud (V3); ficha «ND». Nunca 0 |
| `mag` negativa | Válida; radio mínimo (3 px); la ficha muestra el valor real |
| profundidad nula | Color ND (V4); ficha «ND» |
| profundidad negativa | Válida; clase 1; la ficha muestra el valor real |
| `magType` nulo | Ficha «ND» |
| `place` nulo | Ficha «Sin descripción» |
| `country_id`/`country_name` nulos | Ficha «Sin país asignado» |
| `url` nula | Sin enlace; si existe, abre en pestaña nueva |
| `is_synthetic` verdadero | Etiqueta «Sintético» en la ficha |
| `time`, `updated` | Se formatean «AAAA-MM-DD HH:mm UTC»; el entero original no se altera |

## Entidades propias del panel

**AppConfig** (de `public/config.json`; sin secretos)

| Campo | Tipo | Validación |
|---|---|---|
| `mode` | `"mock"` \| `"api"` | cualquier otro valor: error que nombra `mode` |
| `apiBaseUrl` | texto | obligatorio; puede ser vacío solo si `mode` es `mock` (decisión provisional) |
| `refreshSeconds` | entero > 0 | se valida, no se aplica (P3) |
| `timeoutMs` | entero > 0 | se valida, no se aplica (P3) |

Resultado de validar: `{ ok: true, config }` o `{ ok: false, field, message }`.

**Scenario**: `base` \| `truncated` \| `replay` \| `empty`. Origen: parámetro `?scenario=` de la URL, solo con `mode: "mock"`. Por defecto `base`. Un valor desconocido se trata como `base` y se avisa en consola de desarrollo (decidido por el alumno, 2026-11-05, Q2).

**DataState** (lo que devuelve `useEvents`): una de estas formas.

| Estado | Contenido | Pantalla |
|---|---|---|
| `loading` | — | indicador de carga |
| `ready` | `EventsResponse` con ≥ 1 feature | mapa |
| `empty` | `EventsResponse` con `features: []` | mapa con fronteras + «Sin eventos en el intervalo» |
| `error` | mensaje | mensaje visible (mock ilegible) |
| `api-unavailable` | — | «Modo api: la conexión con la API todavía no está disponible»; sin eventos |

Transiciones: `loading` → `ready` \| `empty` \| `error`; con `mode: "api"` se pasa directo a `api-unavailable`.

**DepthClass** (V2, lógica pura): 

| Clase | Rango (km) | Color |
|---|---|---|
| 1 | < 10 (incluye negativas) | `#FDE725` |
| 2 | 10 a < 35 | `#5EC962` |
| 3 | 35 a < 70 | `#21918C` |
| 4 | 70 a < 300 | `#3B528B` |
| 5 | ≥ 300 | `#440154` |
| ND | nula | `#9CA3AF` |

**Símbolo de evento** (resultado de `symbolFor(properties, depth)`): `{ radius, fill | null, stroke, strokeWidth }`. Radio: 3 + 1,5 × clamp(mag, 0, 8); magnitud nula: radio 5, `fill: null`, contorno de 2 px con el color de profundidad (o gris si ambas faltan). Cada evento deriva su símbolo; no se guarda.

**MapView (contrato de aislamiento, 03 §7.5)**

| Dirección | Elemento | Tipo |
|---|---|---|
| Entrada | `events` | `EventFeature[]` |
| Entrada | `selectedId` | texto o `null` (para resaltar el círculo) |
| Salida | `onSelect` | recibe el `EventFeature` pulsado, o `null` al pulsar fuera |

El mapa no lee config, mock, ficha ni leyenda. El orden de dibujo (magnitud descendente, nulas al final de debajo) se hace dentro y no altera `events`.

**Evento seleccionado**: estado local de `App` (`EventFeature | null`). No es un filtro y no va al store de D2.

## Relaciones

`AppConfig` + `Scenario` → capa de datos → `DataState` → (`EventsResponse.features` → `MapView`) y (`metadata` → contadores). El evento seleccionado va de `MapView` a la ficha.
