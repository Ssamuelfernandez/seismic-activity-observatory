import type { ApiFilters, EventsResponse, HealthResponse, StatsResponse } from '@/shared/types/contract';
import { apiEvents, apiHealth, apiStats } from './client';
import { parseEvents, parseHealth, parseStats } from './parse';
import { getConfig } from './runtimeConfig';

/** Escenario pedido en la URL (`?scenario=`); solo lo usa el servidor simulado. */
const scenarioFromUrl = (): string | null => new URLSearchParams(window.location.search).get('scenario');

/**
 * Qué hace:
 *     Pide /eventos a la API real o, con `mode: "mock"`, al servidor simulado.
 * Recibe:
 *     filters: filtros y límite opcional. signal: cancelación opcional.
 * Devuelve:
 *     La respuesta de eventos.
 * Por qué existe:
 *     Único punto donde se elige el origen (la respuesta del mock también pasa por `parse`); el mock se carga con `import()` solo en modo mock
 *     y en producción `@mock` apunta a un módulo que falla (G15, FR-005).
 */
export async function fetchEvents(filters: ApiFilters & { limit?: number; cursor?: string }, signal?: AbortSignal): Promise<EventsResponse> {
  if (getConfig().mode === 'mock') return parseEvents(await (await import('@mock/backend')).mockEvents(filters, scenarioFromUrl(), signal));
  return apiEvents(filters, signal);
}

/**
 * Qué hace:
 *     Pide /estadisticas a la API real o al servidor simulado según `config.mode`.
 * Recibe:
 *     filters: filtros. signal: cancelación opcional.
 * Devuelve:
 *     La respuesta de estadísticas.
 * Por qué existe:
 *     Mismo origen que `fetchEvents` (G15).
 */
export async function fetchStats(filters: ApiFilters, signal?: AbortSignal): Promise<StatsResponse> {
  if (getConfig().mode === 'mock') return parseStats(await (await import('@mock/backend')).mockStats(filters, scenarioFromUrl(), signal));
  return apiStats(filters, signal);
}

/**
 * Qué hace:
 *     Pide /salud a la API real o al servidor simulado según `config.mode`.
 * Recibe:
 *     signal: cancelación opcional.
 * Devuelve:
 *     La respuesta de salud.
 * Por qué existe:
 *     Mismo origen que `fetchEvents` (G15).
 */
export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  if (getConfig().mode === 'mock') return parseHealth(await (await import('@mock/backend')).mockHealth(scenarioFromUrl(), signal));
  return apiHealth(signal);
}
