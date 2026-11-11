// SERVIDOR SIMULADO (solo desarrollo y pruebas). Responde /eventos, /estadisticas y /salud con la
// forma de api.md sobre un escenario sintético de `mock/*.json`. Nunca entra en el build de
// producción: allí el alias `@mock/backend` apunta a `src/shared/api/mockUnavailable.ts` (G15; constitución §7).
// Aquí SÍ se filtra y se cuenta, porque esto hace de servidor: el panel real no calcula nada.
import type {
  ApiFilters,
  Comparison,
  CountryItem,
  EventFeature,
  EventsResponse,
  HealthResponse,
  Histogram,
  Metadata,
  StatsResponse,
} from '@/shared/types/contract';

/** Marcador que comprueba que este módulo no aparece en `dist/` (SC-003). */
export const __MOCK_BACKEND__ = 'mock-backend';

/** Escenarios disponibles; `base` es el valor por defecto. */
export const SCENARIOS = ['base', 'truncated', 'replay', 'empty', 'realistic'] as const;
export type Scenario = (typeof SCENARIOS)[number];

const HOUR_MS = 3_600_000;
const DAY_MS = 24 * HOUR_MS;
const PAUSE_MS = 150;
/** Cortes de los histogramas de api.md §5.1: ocho tramos de magnitud y cinco de profundidad. */
const MAG_CUTS = [1, 2, 3, 4, 5, 6, 7];
const DEPTH_CUTS = [10, 35, 70, 300];
/** Media diaria de 2025 inventada para la comparación (el mock no tiene histórico). */
const DAILY_MEAN_2025 = 6.4;

/** Subregión de los países que usan los escenarios (el JSON no la trae). */
const SUBREGIONS: Record<string, string> = {
  CHL: 'Sudamérica', PER: 'Sudamérica', JPN: 'Asia oriental', IDN: 'Sudeste asiático', PHL: 'Sudeste asiático',
  MEX: 'Norteamérica', USA: 'Norteamérica', GRC: 'Europa meridional', ESP: 'Europa meridional',
  TUR: 'Asia occidental', NZL: 'Oceanía',
};

/** Los JSON se cargan bajo demanda (un módulo aparte cada uno). */
const loaders = import.meta.glob<EventsResponse>('./*.json', { import: 'default' });

/**
 * Qué hace:
 *     Convierte el valor de `?scenario=` en un escenario conocido.
 * Recibe:
 *     raw: texto de la URL o null.
 * Devuelve:
 *     El escenario; `base` si falta o es desconocido (con aviso en la consola de desarrollo).
 * Por qué existe:
 *     Un valor erróneo no debe romper el panel (FR-006).
 */
export function resolveScenario(raw: string | null | undefined): Scenario {
  if (raw && (SCENARIOS as readonly string[]).includes(raw)) return raw as Scenario;
  if (raw && import.meta.env.DEV) console.warn(`[mock] escenario desconocido «${raw}»; se usa «base». Válidos: ${SCENARIOS.join(', ')}.`);
  return 'base';
}

/** Pausa corta que imita la latencia; se cancela con `signal`. */
const pause = (signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    if (signal?.aborted) return reject(signal.reason);
    const t = setTimeout(resolve, PAUSE_MS);
    signal?.addEventListener('abort', () => {
      clearTimeout(t);
      reject(signal.reason);
    });
  });

/** Escenario cargado: `realistic` es filtrable y con fechas reubicadas a «ahora»; los demás van tal cual. */
interface Loaded {
  response: EventsResponse;
  filterable: boolean;
  /** Instante de referencia: «ahora» en `realistic`, `metadata.generated` en los fijos. */
  now: number;
}

/** Lee el JSON del escenario; en `realistic` desplaza `time`, `updated` y las marcas de `metadata` para que `generated` sea ahora. */
async function load(scenario: Scenario): Promise<Loaded> {
  const data = await loaders[`./${scenario}.json`]();
  if (scenario !== 'realistic') return { response: data, filterable: false, now: data.metadata.generated };
  const now = Date.now();
  const shift = now - data.metadata.generated;
  const features = data.features.map((e) => ({
    ...e,
    properties: { ...e.properties, time: e.properties.time + shift, updated: e.properties.updated + shift },
  }));
  const metadata = {
    ...data.metadata,
    generated: now,
    last_ingestion: data.metadata.last_ingestion === null ? null : data.metadata.last_ingestion + shift,
  };
  return { response: { ...data, metadata, features }, filterable: true, now };
}

/** Eventos de `realistic` que cumplen los filtros (`min_mag` opcional para contar los nulos excluidos). */
function applyFilters(events: EventFeature[], f: ApiFilters, now: number, useMinMag = true): { events: EventFeature[]; start: number; end: number } {
  const start = f.start ? Date.parse(f.start) : now - DAY_MS;
  const end = f.end ? Date.parse(f.end) : now;
  const country = f.country_id?.toUpperCase();
  const kept = events
    .filter((e) => e.properties.time >= start && e.properties.time < end)
    .filter((e) => !useMinMag || f.min_mag === undefined || (e.properties.mag ?? -Infinity) >= f.min_mag)
    .filter((e) => (country === undefined ? true : country === 'NONE' ? e.properties.country_id === null : e.properties.country_id === country))
    .sort((a, b) => b.properties.time - a.properties.time);
  return { events: kept, start, end };
}

/**
 * Qué hace:
 *     Simula `GET /api/eventos` sobre un escenario.
 * Recibe:
 *     f: filtros y límite opcional. scenario: valor de `?scenario=`. signal: cancelación.
 * Devuelve:
 *     Una respuesta conforme a api.md §3: `base`, `truncated`, `replay` y `empty` tal cual; `realistic` filtrada por
 *     `start`, `end`, `min_mag` y `country_id`.
 * Por qué existe:
 *     Permite desarrollar sin API y probar todos los estados; es SINTÉTICO (G15, FR-006).
 */
export async function mockEvents(f: ApiFilters & { limit?: number }, scenario: string | null, signal?: AbortSignal): Promise<EventsResponse> {
  await pause(signal);
  const loaded = await load(resolveScenario(scenario));
  if (!loaded.filterable) return loaded.response;
  const { events } = applyFilters(loaded.response.features, f, loaded.now);
  const page = events.slice(0, f.limit ?? 1000);
  const withoutMinMag = f.min_mag === undefined ? events : applyFilters(loaded.response.features, f, loaded.now, false).events;
  const metadata: Metadata = {
    ...loaded.response.metadata,
    last_ingestion: f.mode === 'replay' ? null : loaded.response.metadata.last_ingestion,
    mode: f.mode ?? 'live',
    count: page.length,
    total: events.length,
    truncated: events.length > page.length,
    next_cursor: null,
    null_mag_excluded: withoutMinMag.filter((e) => e.properties.mag === null).length - events.filter((e) => e.properties.mag === null).length,
  };
  return { type: 'FeatureCollection', metadata, features: page };
}

/** Histograma con límite inferior inclusivo y superior exclusivo; el primer tramo es abierto por abajo y el último por arriba. */
function histogram(values: (number | null)[], cuts: number[], unit: string): Histogram {
  const bins = [...cuts, null].map((upper, i) => ({ lower: i === 0 ? null : cuts[i - 1], upper, count: 0 }));
  let noValue = 0;
  for (const v of values) {
    if (v === null) noValue += 1;
    else bins[bins.findIndex((b) => b.upper === null || v < b.upper)].count += 1;
  }
  return { unit, no_value: noValue, bins };
}

/** Comparación de las últimas 24 h con la media diaria de 2025 (api.md §5.1); `null` en replay. */
function buildComparison(pool: EventFeature[], f: ApiFilters, now: number): Comparison {
  const minMagApplied = Math.max(f.min_mag ?? 0, 4);
  const recentStart = now - DAY_MS;
  const country = f.country_id?.toUpperCase();
  const nRecent = pool.filter((e) => {
    const p = e.properties;
    const inCountry = country === undefined ? true : country === 'NONE' ? p.country_id === null : p.country_id === country;
    return p.time >= recentStart && p.time < now && (p.mag ?? -Infinity) >= minMagApplied && inCountry;
  }).length;
  const diff = nRecent - DAILY_MEAN_2025;
  return {
    unit: 'events',
    min_mag_applied: minMagApplied,
    recent_period: { start: recentStart, end: now },
    reference_period: { start: Date.UTC(2025, 0, 1), end: Date.UTC(2026, 0, 1) },
    n_recent: nRecent,
    n_2025: Math.round(DAILY_MEAN_2025 * 365),
    daily_mean_2025: DAILY_MEAN_2025,
    diff_abs: Number(diff.toFixed(2)),
    variation_pct: Number(((diff / DAILY_MEAN_2025) * 100).toFixed(2)),
    recent_incomplete: true,
  };
}

/**
 * Qué hace:
 *     Simula `GET /api/estadisticas` sobre un escenario.
 * Recibe:
 *     f: filtros. scenario: valor de `?scenario=`. signal: cancelación.
 * Devuelve:
 *     Estadísticas conformes a api.md §5: histograma de profundidad de cinco tramos, de magnitud de ocho,
 *     `by_hour`, `by_country` (con el elemento sin país) y `comparison` (o `null` en replay). En los escenarios
 *     fijos se calculan sobre todos sus eventos (los filtros no se aplican) y `total` es `metadata.total`.
 * Por qué existe:
 *     El servidor simulado calcula; el panel solo muestra (G15; constitución §17).
 */
export async function mockStats(f: ApiFilters, scenario: string | null, signal?: AbortSignal): Promise<StatsResponse> {
  await pause(signal);
  const loaded = await load(resolveScenario(scenario));
  const meta = loaded.response.metadata;
  const all = loaded.response.features;
  const mode = loaded.filterable ? (f.mode ?? 'live') : meta.mode;

  let events = all;
  let start: number;
  let end: number;
  if (loaded.filterable) {
    ({ events, start, end } = applyFilters(all, f, loaded.now));
  } else if (all.length > 0) {
    const times = all.map((e) => e.properties.time);
    start = Math.min(...times);
    end = Math.max(...times) + 1;
  } else {
    start = loaded.now - DAY_MS;
    end = loaded.now;
  }

  // Una entrada por cada hora UTC fija que se solape con el periodo, incluidas las de 0 eventos.
  const first = Math.floor(start / HOUR_MS) * HOUR_MS;
  const buckets: { hour_start: number; count: number }[] = [];
  for (let h = first; h < end; h += HOUR_MS) buckets.push({ hour_start: h, count: 0 });
  for (const e of events) buckets[Math.floor((e.properties.time - first) / HOUR_MS)].count += 1;

  const byCountry = new Map<string | null, CountryItem>();
  for (const e of events) {
    const id = e.properties.country_id;
    const item = byCountry.get(id) ?? { country_id: id, country_name: e.properties.country_name, subregion: id ? (SUBREGIONS[id] ?? null) : null, count: 0 };
    item.count += 1;
    byCountry.set(id, item);
  }
  const items = [...byCountry.values()].sort((a, b) => b.count - a.count || (a.country_id ?? '~').localeCompare(b.country_id ?? '~'));

  // `no_value` de magnitud: nulos que cumplen los demás filtros, sin contar `min_mag` (api.md §5.1).
  const magPool = loaded.filterable && f.min_mag !== undefined ? applyFilters(all, f, loaded.now, false).events : events;
  const magnitude = histogram(events.map((e) => e.properties.mag), MAG_CUTS, 'dimensionless');
  magnitude.no_value = magPool.filter((e) => e.properties.mag === null).length;

  return {
    metadata: { generated: meta.generated, last_ingestion: mode === 'replay' ? null : meta.last_ingestion, mode },
    period: { start, end },
    filters: { min_mag: loaded.filterable ? (f.min_mag ?? null) : null, country_id: loaded.filterable ? (f.country_id ?? null) : null },
    total: loaded.filterable ? events.length : meta.total,
    by_hour: { unit: 'events', no_value: 0, buckets },
    by_country: { unit: 'events', no_value: byCountry.get(null)?.count ?? 0, items },
    histograms: { magnitude, depth: histogram(events.map((e) => e.geometry.coordinates[2]), DEPTH_CUTS, 'km') },
    comparison: mode === 'replay' ? null : buildComparison(all, f, loaded.now),
  };
}

/**
 * Qué hace:
 *     Simula `GET /api/salud` sobre un escenario.
 * Recibe:
 *     scenario: valor de `?scenario=`. signal: cancelación.
 * Devuelve:
 *     `{ status: "ok", last_ingestion, generated }` con los valores del escenario.
 * Por qué existe:
 *     Completa el servidor simulado y alimenta el estado del feed (G15, G7).
 */
export async function mockHealth(scenario: string | null, signal?: AbortSignal): Promise<HealthResponse> {
  await pause(signal);
  const meta = (await load(resolveScenario(scenario))).response.metadata;
  return { status: 'ok', last_ingestion: meta.last_ingestion, generated: meta.generated };
}
