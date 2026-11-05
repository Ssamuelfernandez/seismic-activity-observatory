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
