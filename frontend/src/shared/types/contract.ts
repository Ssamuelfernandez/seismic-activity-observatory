/**
 * Tipos del contrato de `GET /api/eventos`.
 *
 * Fuente única: `specs/001-contratos-y-modelo/contracts/api.md` §3.2 (`metadata`)
 * y §3.4 (`properties`). Aquí solo se transcriben como tipos; no se redefinen
 * reglas (G2, G12 `magType`).
 */

/** Modo servido por la API. */
export type EventsMode = 'live' | 'replay';

/** Metadatos de la respuesta (api.md §3.2). Los ocho campos son obligatorios. */
export interface Metadata {
  /** Instante de generación (ms Unix UTC). */
  generated: number;
  /** Última ingesta correcta del modo en vivo (ms) o `null`. */
  last_ingestion: number | null;
  mode: EventsMode;
  /** Número de eventos de esta respuesta. */
  count: number;
  /** Número de eventos que cumplen los filtros (todas las páginas). */
  total: number;
  truncated: boolean;
  /** Cursor opaco de la página siguiente o `null` en la última. */
  next_cursor: string | null;
  null_mag_excluded: number;
}

/** Propiedades de un evento (api.md §3.4): lista cerrada de once campos. */
export interface EventProperties {
  /** Magnitud; `null` si es desconocida. Negativa es válida. */
  mag: number | null;
  /** Tipo de magnitud (`ml`, `mb`, `mww`...) o `null`. */
  magType: string | null;
  place: string | null;
  /** Instante del terremoto (ms Unix UTC). */
  time: number;
  /** Última actualización (ms Unix UTC). */
  updated: number;
  /** `ADM0_A3` o `null` (sin país). */
  country_id: string | null;
  /** `NAME_ES` o `null` (sin país). */
  country_name: string | null;
  is_synthetic: boolean;
  status: string | null;
  url: string | null;
  sig: number | null;
}

/** Geometría `Point`: `[lon, lat, profundidad_km | null]`. */
export interface EventGeometry {
  type: 'Point';
  coordinates: [number, number, number | null];
}

/** Un evento sísmico como `Feature` de GeoJSON. */
export interface EventFeature {
  type: 'Feature';
  id: string;
  geometry: EventGeometry;
  properties: EventProperties;
}

/** Respuesta completa de `GET /api/eventos`. */
export interface EventsResponse {
  type: 'FeatureCollection';
  metadata: Metadata;
  features: EventFeature[];
}

// ---------------------------------------------------------------------------
// `GET /api/estadisticas` y `GET /api/salud`. Las cifras las calcula SQL en la
// API; el cliente solo las muestra (nunca las recalcula).
// ---------------------------------------------------------------------------

/** Periodo efectivo [start, end) en ms Unix UTC. */
export interface Period {
  start: number;
  end: number;
}

/** Bloque con unidad y recuento de registros sin valor. */
export interface StatsBlock {
  unit: string;
  /** Registros sin valor para esta dimensión. */
  no_value: number;
}

export interface HourBucket {
  /** Inicio de la hora UTC (ms). */
  hour_start: number;
  count: number;
}

export interface CountryItem {
  /** `null` en el elemento «sin país». */
  country_id: string | null;
  country_name: string | null;
  subregion: string | null;
  count: number;
}

/** Tramo de un histograma: límite inferior inclusivo, superior exclusivo. */
export interface HistogramBin {
  /** `null` en el primer tramo (abierto por abajo). */
  lower: number | null;
  /** `null` en el último tramo (abierto por arriba). */
  upper: number | null;
  count: number;
}

export interface Histogram extends StatsBlock {
  bins: HistogramBin[];
}

/** Últimas 24 h frente a la media diaria de 2025. */
export interface Comparison {
  unit: string;
  /** max(min_mag, 4.0): el histórico de 2025 solo tiene M ≥ 4. */
  min_mag_applied: number;
  recent_period: Period;
  reference_period: Period;
  n_recent: number;
  n_2025: number;
  daily_mean_2025: number;
  diff_abs: number;
  /** `null` si la media de 2025 es 0. */
  variation_pct: number | null;
  /** Siempre `true`: USGS puede retrasar datos recientes. */
  recent_incomplete: boolean;
}

export interface StatsResponse {
  metadata: { generated: number; last_ingestion: number | null; mode: EventsMode };
  period: Period;
  filters: { min_mag: number | null; country_id: string | null };
  total: number;
  by_hour: StatsBlock & { buckets: HourBucket[] };
  by_country: StatsBlock & { items: CountryItem[] };
  histograms: { magnitude: Histogram; depth: Histogram };
  /** `null` en `mode=replay`. */
  comparison: Comparison | null;
}

/** Respuesta de `GET /api/salud` (no informa del modo). */
export interface HealthResponse {
  status: 'ok';
  last_ingestion: number | null;
  generated: number;
}

/** Códigos de error de la API (mismo cuerpo en todos los endpoints). */
export type ApiErrorCode =
  | 'invalid_parameter'
  | 'invalid_cursor'
  | 'not_found'
  | 'method_not_allowed'
  | 'internal_error'
  | 'database_unavailable';

/** Filtros comunes a `/api/eventos` y `/api/estadisticas`. */
export interface ApiFilters {
  /** ISO 8601; sin zona se toma como UTC. */
  start?: string;
  end?: string;
  min_mag?: number;
  /** Código ADM0_A3 de tres letras, o `none` para eventos sin país. */
  country_id?: string;
  mode?: EventsMode;
}
