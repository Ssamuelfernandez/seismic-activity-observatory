import { keepPreviousData, useQuery } from '@tanstack/react-query';
import type { ApiError } from '@/shared/api/client';
import { fetchEvents, fetchHealth, fetchStats } from '@/shared/api/dataSource';
import { getConfig } from '@/shared/api/runtimeConfig';
import type { ApiFilters, EventsResponse, HealthResponse, StatsResponse } from '@/shared/types/contract';
import { useFilters, type Filters } from '@/store/filters';

const HOUR_MS = 3_600_000;
const DAY_MS = 24 * HOUR_MS;
const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;

/** Filtros válidos para la API; un país mal escrito se omite en vez de provocar un 400. */
function buildFilters(s: Filters): { mode: ApiFilters['mode']; min_mag?: number; country_id?: string; hours: number; custom: { from: string; to: string } | null } {
  const c = s.country.trim();
  const validCountry = /^([a-z]{3}|none)$/i.test(c) ? c : undefined;
  return {
    mode: s.mode,
    min_mag: s.minMag > 0 ? s.minMag : undefined,
    country_id: validCountry,
    hours: s.hours === 0 ? 24 : s.hours,
    // Rango por fechas solo si es válido; si no, se usan las últimas 24 h.
    custom: s.hours === 0 && DAY_RE.test(s.dateFrom) && DAY_RE.test(s.dateTo) && s.dateFrom <= s.dateTo ? { from: s.dateFrom, to: s.dateTo } : null,
  };
}

export interface ObservatoryData {
  response: EventsResponse | null;
  /** Error de la API (eventos), si lo hay. */
  error: ApiError | null;
  isFetching: boolean;
  /** Cuándo llegaron los últimos eventos al navegador (ms; 0 si aún no). */
  updatedAt: number;
  stats: StatsResponse | null;
  statsError: ApiError | null;
  health: HealthResponse | null;
  healthError: ApiError | null;
}

/**
 * Qué hace:
 *     Pide eventos, estadísticas y salud con los filtros del store y los refresca periódicamente.
 * Recibe:
 *     Nada (lee el store de filtros).
 * Devuelve:
 *     Los datos, el estado de carga y los errores.
 * Por qué existe:
 *     Es la única puerta de datos del panel; no calcula estadísticas (G1, G6, G9).
 */
export function useObservatory(): ObservatoryData {
  const { mode, hours, dateFrom, dateTo, minMag, country } = useFilters();
  const f = buildFilters({ mode, hours, dateFrom, dateTo, minMag, country });
  const refetchInterval = getConfig().refreshSeconds * 1000;

  // El inicio relativo se calcula al pedir, no en la clave, para que la clave no cambie cada segundo.
  const range = () =>
    f.custom
      ? { start: `${f.custom.from}T00:00:00.000Z`, end: new Date(Date.parse(`${f.custom.to}T00:00:00.000Z`) + DAY_MS).toISOString() }
      : { start: new Date(Date.now() - f.hours * HOUR_MS).toISOString() };
  const common = { mode: f.mode, min_mag: f.min_mag, country_id: f.country_id };

  const events = useQuery({
    queryKey: ['events', f],
    queryFn: ({ signal }) => fetchEvents({ ...common, ...range() }, signal),
    refetchInterval,
    placeholderData: keepPreviousData,
  });
  const stats = useQuery({
    queryKey: ['stats', f],
    queryFn: ({ signal }) => fetchStats({ ...common, ...range() }, signal),
    refetchInterval,
    placeholderData: keepPreviousData,
  });
  const health = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
    refetchInterval: 30_000,
  });

  return {
    response: events.data ?? null,
    error: events.error as ApiError | null,
    isFetching: events.isFetching,
    updatedAt: events.dataUpdatedAt,
    stats: stats.data ?? null,
    statsError: stats.error as ApiError | null,
    health: health.data ?? null,
    healthError: health.error as ApiError | null,
  };
}
