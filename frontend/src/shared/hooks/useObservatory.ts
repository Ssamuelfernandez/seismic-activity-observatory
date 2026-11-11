import { keepPreviousData, useQuery } from '@tanstack/react-query';
import type { ApiError } from '@/shared/api/client';
import { fetchEvents, fetchHealth, fetchStats } from '@/shared/api/dataSource';
import { buildRequest, resolveFilters } from '@/shared/api/requests';
import { getConfig } from '@/shared/api/runtimeConfig';
import { deriveDataState, type DataState } from '@/shared/lib/dataState';
import type { EventsResponse, HealthResponse, StatsResponse } from '@/shared/types/contract';
import { useFilters } from '@/store/filters';

/** Cada cuánto se consulta /salud (ms). */
const HEALTH_REFRESH_MS = 30_000;

export interface ObservatoryData {
  /** `loading` | `ready` | `empty` | `error`; `error` puede convivir con la última lectura buena (`response`). */
  state: DataState;
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
 *     Pide eventos, estadísticas y salud con los filtros del store y los refresca cada `refreshSeconds`.
 * Recibe:
 *     Nada (lee el store de filtros y la config cargada).
 * Devuelve:
 *     Los datos, el estado derivado (`loading`/`ready`/`empty`/`error`) y los errores.
 * Por qué existe:
 *     Es la única puerta de datos del panel; no calcula estadísticas (G1, G6, G9). TanStack Query no lanza otra
 *     consulta mientras una sigue en vuelo, así que el refresco no se solapa; `retry: false` evita reintentos
 *     ocultos y `keepPreviousData` mantiene la última lectura buena (`updatedAt` la marca como antigua).
 */
export function useObservatory(): ObservatoryData {
  const { mode, hours, dateFrom, dateTo, minMag, country } = useFilters();
  const filters = resolveFilters({ mode, hours, dateFrom, dateTo, minMag, country });
  const refetchInterval = getConfig().refreshSeconds * 1000;

  // La clave lleva los filtros resueltos (sin «ahora»): el `start` relativo se calcula al pedir, no cada segundo.
  const events = useQuery({
    queryKey: ['events', filters],
    queryFn: ({ signal }) => fetchEvents(buildRequest(filters, Date.now()), signal),
    refetchInterval,
    retry: false,
    placeholderData: keepPreviousData,
  });
  const stats = useQuery({
    queryKey: ['stats', filters],
    queryFn: ({ signal }) => fetchStats(buildRequest(filters, Date.now()), signal),
    refetchInterval,
    retry: false,
    placeholderData: keepPreviousData,
  });
  const health = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
    refetchInterval: HEALTH_REFRESH_MS,
    retry: false,
  });

  const response = events.data ?? null;
  return {
    state: deriveDataState(response ? response.features.length : null, events.error !== null),
    response,
    error: events.error as ApiError | null,
    isFetching: events.isFetching,
    updatedAt: events.dataUpdatedAt,
    stats: stats.data ?? null,
    statsError: stats.error as ApiError | null,
    health: health.data ?? null,
    healthError: health.error as ApiError | null,
  };
}
