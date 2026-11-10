# Data Model: Panel completo

No hay base de datos. Son los tipos del frontend. Los de contrato se citan de `specs/001-contratos-y-modelo/contracts/api.md` (§3.2, §3.4 y §5) y no se redefinen; aquí solo se anota lo que el panel hace con ellos. Ubicación: `src/shared/types/contract.ts` los de contrato; el resto, junto a quien los usa (D3: estructura del front externo, P1). **Reescrito el 2026-11-10** por la enmienda de alcance.

## Entidades del contrato (resumen, fuente: `api.md`)

- **EventsResponse** (`FeatureCollection`): `metadata` de ocho campos (`generated`, `last_ingestion`, `mode`, `count`, `total`, `truncated`, `next_cursor`, `null_mag_excluded`) y `features: EventFeature[]`.
- **EventFeature**: `id`, `geometry` (`Point`, `[lon, lat, depth_km | null]`) y `properties` de once campos (`mag`, `magType`, `place`, `time`, `updated`, `country_id`, `country_name`, `is_synthetic`, `status`, `url`, `sig`).
- **StatsResponse** (`api.md` §5): `metadata`, `period`, `filters`, `total`, `by_hour`, `by_country`, `histograms.magnitude` (ocho tramos), `histograms.depth` (**cinco** tramos `<10`, `10–35`, `35–70`, `70–300`, `≥300`) y `comparison` (o `null` en `mode=replay`).
- **HealthResponse**: `status`, `last_ingestion`, `generated`.
- **Error** (`api.md` §1): `{"error": {"code", "message"}}`.

Reglas de visualización:

| Valor | Regla |
|---|---|
| `mag` nula | Barra ND gris de altura mínima, **sin anillo ni etiqueta**; ficha y tabla «ND». Nunca 0 |
| `mag` negativa | Válida; altura mínima; se muestra el valor real |
| profundidad nula | Gris ND con la altura de su magnitud; «ND» |
| profundidad negativa | Válida; clase 1; valor real |
| `magType`, `status`, `sig` nulos | «ND» |
| `place` nulo | «Sin descripción» |
| `country_id`/`country_name` nulos | «Sin país asignado» (en el filtro, el valor `none`) |
| `url` nula | Sin enlace |
| `is_synthetic` verdadero | Etiqueta de sintético y banner |
| `time`, `updated`, `generated`, `last_ingestion` | «AAAA-MM-DD HH:mm UTC»; el entero original no se altera |
| `variation_pct` nulo | «ND» |

## Entidades propias del panel

**AppConfig** (de `public/config.json`; sin secretos)

| Campo | Tipo | Validación |
|---|---|---|
| `mode` | `"mock"` \| `"api"` | cualquier otro valor: error que nombra `mode` |
| `apiBaseUrl` | texto | en modo `api` no vacío y empieza por `/`, `http://` o `https://` |
| `refreshSeconds` | entero > 0 | se aplica al refresco |
| `timeoutMs` | entero > 0 | se aplica al tiempo máximo de cada petición |

Resultado de validar: `{ ok: true, config }` o `{ ok: false, field, message }`.

**Filtros** (store único, Zustand): `mode` (`live`\|`replay`), `hours` (1, 6, 24, 168, 720, 8760 o `0` = rango de fechas), `dateFrom`/`dateTo` (`AAAA-MM-DD` UTC, el día final se incluye entero), `minMag` (0 = sin filtro) y `country` (`ADM0_A3`, `none` o vacío). No contiene el origen de los datos. Cambiar cualquiera limpia la selección.

**Petición** (resultado de `buildRequest(filters, now)`): `mode`, `min_mag?`, `country_id?` y el intervalo. `live`: `start` = ahora − horas (sin `end`) o `start`/`end` del rango de fechas. `replay`: `start = 2025-01-01T00:00:00.000Z`, `end = 2026-01-01T00:00:00.000Z` (el `reference_period` de `api.md` §5) y el periodo del filtro se ignora.

**Escenario del mock**: `base` \| `truncated` \| `replay` \| `empty` \| `realistic`. Origen: `?scenario=` de la URL, solo con `mode: "mock"` y solo en desarrollo; por defecto `base`; un valor desconocido cae a `base` con aviso en la consola de desarrollo.

**DataState** (lo que expone `useObservatory`):

| Estado | Contenido | Pantalla |
|---|---|---|
| `loading` | — | indicador de carga |
| `ready` | `EventsResponse` con ≥ 1 feature | globo, lista, tabla |
| `empty` | `EventsResponse` con `features: []` | globo vacío y «Sin eventos en el intervalo» (en replay: «Sin eventos reproducidos») |
| `error` sin datos | `ApiError` | aviso «Sin datos»; nunca «0 eventos» |
| `error` con datos | `ApiError` + última lectura | aviso «Datos antiguos» con la hora de `updatedAt` |

`ApiError`: `status`, `code` (los del contrato más `network`, `timeout`, `invalid_response`, `unknown`) y `message`.

**DepthClass** (lógica pura, `shared/lib/symbology.ts`; colores por defecto, `spec.md`):

| Clase | Rango (km) | Color |
|---|---|---|
| 1 | < 10 (incluye negativas) | `#ffd23f` |
| 2 | 10 a < 35 | `#ff963a` |
| 3 | 35 a < 70 | `#ff5a36` |
| 4 | 70 a < 300 | `#d7539a` |
| 5 | ≥ 300 | `#b04cff` |
| ND | nula | `#8a93a0` |

**Altura del prisma**: máx(0,010; 0,0125 × clamp(mag, 0, 8)); magnitud nula o negativa → 0,010; el factor de escala visual (× 3,7) lo aplica `GlobeView`.

**GlobeView (contrato de aislamiento, 03 §7.5)**: entrada `events`, `selectedId` y los ajustes visuales; salida `onSelect(EventFeature | null)`. No lee config, mock ni store.

**Evento seleccionado**: estado local de `App` (`EventFeature | null`); no es un filtro.

## Relaciones

`AppConfig` → `dataSource` (mock o API) → `parse` → `DataState` (`EventsResponse`, `StatsResponse`, `HealthResponse`) → globo, lista, tabla, estadísticas, estado y avisos. `Filtros` → `buildRequest` → `dataSource`. `StatsResponse.total` debe coincidir con `EventsResponse.metadata.total` para los mismos filtros (SC-007).
