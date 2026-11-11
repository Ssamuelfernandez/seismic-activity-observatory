import type { ApiFilters, EventsMode } from '@/shared/types/contract';

/** Inicio del intervalo de reproducción: el `reference_period` de api.md §5 (2025 entero). */
export const REPLAY_START = '2025-01-01T00:00:00.000Z';
/** Fin (exclusivo) del intervalo de reproducción. */
export const REPLAY_END = '2026-01-01T00:00:00.000Z';

const HOUR_MS = 3_600_000;
const DAY_MS = 24 * HOUR_MS;
const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;
const COUNTRY_RE = /^([a-z]{3}|none)$/i;

/** Filtros del store que importan a la petición (el store los cumple por forma). */
export interface RequestFilters {
  mode: EventsMode;
  /** Horas hacia atrás desde ahora; 0 = rango de fechas. */
  hours: number;
  /** Rango personalizado `AAAA-MM-DD` (UTC). */
  dateFrom: string;
  dateTo: string;
  /** 0 = sin filtro. */
  minMag: number;
  /** `none`, tres letras o vacío (todos). */
  country: string;
}

/** Periodo ya resuelto: ventana relativa, rango de fechas o 2025 fijo (reproducción). */
export type ResolvedPeriod = { kind: 'hours'; hours: number } | { kind: 'range'; from: string; to: string } | { kind: 'replay' };

/** Filtros normalizados; es estable (sin «ahora»), así que sirve de clave de la caché. */
export interface ResolvedFilters {
  mode: EventsMode;
  period: ResolvedPeriod;
  min_mag?: number;
  country_id?: string;
}

/**
 * Qué hace:
 *     Normaliza los filtros del store: elige el periodo efectivo y descarta valores no válidos.
 * Recibe:
 *     f: filtros del store.
 * Devuelve:
 *     Filtros resueltos sin ningún instante calculado.
 * Por qué existe:
 *     En `replay` el periodo del filtro se ignora; un rango incompleto o invertido cae a 24 h;
 *     `min_mag` solo se envía si es > 0 y `country_id` solo si es `none` o tres letras (G6, FR-014).
 */
export function resolveFilters(f: RequestFilters): ResolvedFilters {
  const country = f.country.trim();
  const base = {
    mode: f.mode,
    min_mag: f.minMag > 0 ? f.minMag : undefined,
    country_id: COUNTRY_RE.test(country) ? country : undefined,
  };
  if (f.mode === 'replay') return { ...base, period: { kind: 'replay' } };
  const validRange = f.hours === 0 && DAY_RE.test(f.dateFrom) && DAY_RE.test(f.dateTo) && f.dateFrom <= f.dateTo;
  if (validRange) return { ...base, period: { kind: 'range', from: f.dateFrom, to: f.dateTo } };
  return { ...base, period: { kind: 'hours', hours: f.hours === 0 ? 24 : f.hours } };
}

/**
 * Qué hace:
 *     Convierte filtros resueltos en los parámetros de `/eventos` y `/estadisticas`.
 * Recibe:
 *     r: filtros resueltos. now: instante actual en ms (se inyecta para poder probarla).
 * Devuelve:
 *     `ApiFilters`: `live` con `start` = ahora − horas (sin `end`) o con el rango UTC (`end` = día final + 1 día);
 *     `replay` con `start`/`end` de 2025.
 * Por qué existe:
 *     El `start` relativo se calcula al pedir, no en la clave de la caché (FR-010, FR-014).
 */
export function buildRequest(r: ResolvedFilters, now: number): ApiFilters {
  const common: ApiFilters = { mode: r.mode, min_mag: r.min_mag, country_id: r.country_id };
  const p = r.period;
  if (p.kind === 'replay') return { ...common, start: REPLAY_START, end: REPLAY_END };
  if (p.kind === 'range') {
    return { ...common, start: `${p.from}T00:00:00.000Z`, end: new Date(Date.parse(`${p.to}T00:00:00.000Z`) + DAY_MS).toISOString() };
  }
  return { ...common, start: new Date(now - p.hours * HOUR_MS).toISOString() };
}
