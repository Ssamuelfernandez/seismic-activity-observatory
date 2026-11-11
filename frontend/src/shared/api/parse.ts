import type { EventsResponse, HealthResponse, StatsResponse } from '@/shared/types/contract';
import { ApiError } from './apiError';

type Obj = Record<string, unknown>;

/** Fallo interno de forma; las funciones públicas lo convierten en `ApiError`. */
class ShapeError extends Error {}

const fail = (path: string, expected: string): never => {
  throw new ShapeError(`${path}: se esperaba ${expected}`);
};
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v);
const obj = (v: unknown, path: string): Obj => (isObj(v) ? v : fail(path, 'un objeto'));
const num = (v: unknown, path: string): number => (typeof v === 'number' && Number.isFinite(v) ? v : fail(path, 'un número'));
const str = (v: unknown, path: string): string => (typeof v === 'string' ? v : fail(path, 'un texto'));
const bool = (v: unknown, path: string): boolean => (typeof v === 'boolean' ? v : fail(path, 'un booleano'));
const arr = (v: unknown, path: string): unknown[] => (Array.isArray(v) ? v : fail(path, 'una lista'));
/** Número o `null`: el nulo se conserva tal cual, nunca pasa a 0. */
const numOrNull = (v: unknown, path: string): number | null => (v === null ? null : num(v, path));
/** Texto o `null`: el nulo se conserva tal cual. */
const strOrNull = (v: unknown, path: string): string | null => (v === null ? null : str(v, path));
const mode = (v: unknown, path: string): 'live' | 'replay' => (v === 'live' || v === 'replay' ? v : fail(path, '«live» o «replay»'));

/** Comprueba `metadata` de /eventos (api.md §3.2): los ocho campos con su tipo. */
function checkMetadata(raw: unknown): void {
  const m = obj(raw, 'metadata');
  num(m.generated, 'metadata.generated');
  numOrNull(m.last_ingestion, 'metadata.last_ingestion');
  mode(m.mode, 'metadata.mode');
  num(m.count, 'metadata.count');
  num(m.total, 'metadata.total');
  bool(m.truncated, 'metadata.truncated');
  strOrNull(m.next_cursor, 'metadata.next_cursor');
  num(m.null_mag_excluded, 'metadata.null_mag_excluded');
}

/** Comprueba un `Feature` de /eventos (api.md §3.4): punto con coordenadas finitas y once propiedades. */
function checkFeature(raw: unknown, i: number): void {
  const at = `features[${i}]`;
  const f = obj(raw, at);
  if (f.type !== 'Feature') fail(`${at}.type`, '«Feature»');
  str(f.id, `${at}.id`);
  const g = obj(f.geometry, `${at}.geometry`);
  if (g.type !== 'Point') fail(`${at}.geometry.type`, '«Point»');
  const c = arr(g.coordinates, `${at}.geometry.coordinates`);
  if (c.length !== 3) fail(`${at}.geometry.coordinates`, 'tres valores [lon, lat, profundidad]');
  num(c[0], `${at}.geometry.coordinates[0]`);
  num(c[1], `${at}.geometry.coordinates[1]`);
  numOrNull(c[2], `${at}.geometry.coordinates[2]`);
  const p = obj(f.properties, `${at}.properties`);
  numOrNull(p.mag, `${at}.properties.mag`);
  strOrNull(p.magType, `${at}.properties.magType`);
  strOrNull(p.place, `${at}.properties.place`);
  num(p.time, `${at}.properties.time`);
  num(p.updated, `${at}.properties.updated`);
  strOrNull(p.country_id, `${at}.properties.country_id`);
  strOrNull(p.country_name, `${at}.properties.country_name`);
  bool(p.is_synthetic, `${at}.properties.is_synthetic`);
  strOrNull(p.status, `${at}.properties.status`);
  strOrNull(p.url, `${at}.properties.url`);
  numOrNull(p.sig, `${at}.properties.sig`);
}

function checkPeriod(raw: unknown, path: string): void {
  const p = obj(raw, path);
  num(p.start, `${path}.start`);
  num(p.end, `${path}.end`);
}

function checkBlock(raw: unknown, path: string): Obj {
  const b = obj(raw, path);
  str(b.unit, `${path}.unit`);
  num(b.no_value, `${path}.no_value`);
  return b;
}

function checkHistogram(raw: unknown, path: string): void {
  const h = checkBlock(raw, path);
  arr(h.bins, `${path}.bins`).forEach((raw2, i) => {
    const b = obj(raw2, `${path}.bins[${i}]`);
    numOrNull(b.lower, `${path}.bins[${i}].lower`);
    numOrNull(b.upper, `${path}.bins[${i}].upper`);
    num(b.count, `${path}.bins[${i}].count`);
  });
}

/** Comprueba `comparison` de /estadisticas (api.md §5.1); admite `null` (replay). */
function checkComparison(raw: unknown): void {
  if (raw === null) return;
  const c = obj(raw, 'comparison');
  str(c.unit, 'comparison.unit');
  for (const k of ['min_mag_applied', 'n_recent', 'n_2025', 'daily_mean_2025', 'diff_abs']) num(c[k], `comparison.${k}`);
  numOrNull(c.variation_pct, 'comparison.variation_pct');
  checkPeriod(c.recent_period, 'comparison.recent_period');
  checkPeriod(c.reference_period, 'comparison.reference_period');
  bool(c.recent_incomplete, 'comparison.recent_incomplete');
}

/** Ejecuta una guarda y traduce su fallo de forma a `ApiError` con código `invalid_response`. */
function guard<T>(raw: unknown, what: string, check: (o: Obj) => void): T {
  try {
    check(obj(raw, what));
  } catch (e) {
    if (e instanceof ShapeError) throw new ApiError(`Respuesta de ${what} con forma inesperada (${e.message}).`, 200, 'invalid_response');
    throw e;
  }
  return raw as T;
}

/**
 * Qué hace:
 *     Comprueba la forma de una respuesta de `/eventos` (FeatureCollection, `metadata` de ocho campos y once propiedades por evento).
 * Recibe:
 *     raw: el JSON ya decodificado.
 * Devuelve:
 *     La misma respuesta, tipada y sin tocar: los nulos se conservan.
 * Por qué existe:
 *     Una respuesta malformada es un error visible, no un panel vacío (FR-011, G12).
 */
export function parseEvents(raw: unknown): EventsResponse {
  return guard<EventsResponse>(raw, '/eventos', (o) => {
    if (o.type !== 'FeatureCollection') fail('type', '«FeatureCollection»');
    checkMetadata(o.metadata);
    arr(o.features, 'features').forEach(checkFeature);
  });
}

/**
 * Qué hace:
 *     Comprueba la forma de una respuesta de `/estadisticas`.
 * Recibe:
 *     raw: el JSON ya decodificado.
 * Devuelve:
 *     La misma respuesta, tipada y sin tocar.
 * Por qué existe:
 *     Las cifras las calcula la API; aquí solo se asegura que el panel pueda mostrarlas (FR-011).
 */
export function parseStats(raw: unknown): StatsResponse {
  return guard<StatsResponse>(raw, '/estadisticas', (o) => {
    const m = obj(o.metadata, 'metadata');
    num(m.generated, 'metadata.generated');
    numOrNull(m.last_ingestion, 'metadata.last_ingestion');
    mode(m.mode, 'metadata.mode');
    checkPeriod(o.period, 'period');
    const fl = obj(o.filters, 'filters');
    numOrNull(fl.min_mag, 'filters.min_mag');
    strOrNull(fl.country_id, 'filters.country_id');
    num(o.total, 'total');
    const hours = checkBlock(o.by_hour, 'by_hour');
    arr(hours.buckets, 'by_hour.buckets').forEach((raw2, i) => {
      const b = obj(raw2, `by_hour.buckets[${i}]`);
      num(b.hour_start, `by_hour.buckets[${i}].hour_start`);
      num(b.count, `by_hour.buckets[${i}].count`);
    });
    const countries = checkBlock(o.by_country, 'by_country');
    arr(countries.items, 'by_country.items').forEach((raw2, i) => {
      const it = obj(raw2, `by_country.items[${i}]`);
      strOrNull(it.country_id, `by_country.items[${i}].country_id`);
      strOrNull(it.country_name, `by_country.items[${i}].country_name`);
      strOrNull(it.subregion, `by_country.items[${i}].subregion`);
      num(it.count, `by_country.items[${i}].count`);
    });
    const hs = obj(o.histograms, 'histograms');
    checkHistogram(hs.magnitude, 'histograms.magnitude');
    checkHistogram(hs.depth, 'histograms.depth');
    checkComparison(o.comparison);
  });
}

/**
 * Qué hace:
 *     Comprueba la forma de una respuesta de `/salud`.
 * Recibe:
 *     raw: el JSON ya decodificado.
 * Devuelve:
 *     La misma respuesta, tipada y sin tocar.
 * Por qué existe:
 *     Alimenta el estado del feed y el aviso de desactualizado (G7).
 */
export function parseHealth(raw: unknown): HealthResponse {
  return guard<HealthResponse>(raw, '/salud', (o) => {
    if (o.status !== 'ok') fail('status', '«ok»');
    numOrNull(o.last_ingestion, 'last_ingestion');
    num(o.generated, 'generated');
  });
}
