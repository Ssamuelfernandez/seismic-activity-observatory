import type { ApiErrorCode, ApiFilters, EventsResponse, HealthResponse, StatsResponse } from '@/shared/types/contract';
import { ApiError } from './apiError';
import { parseEvents, parseHealth, parseStats } from './parse';
import { getConfig } from './runtimeConfig';

export { ApiError } from './apiError';

/** URL base de la API (`apiBaseUrl` de config.json). En desarrollo `/api` se reenvía por el proxy de Vite. */
const baseUrl = () => getConfig().apiBaseUrl.replace(/\/$/, '');

/** Construye la query omitiendo los parámetros vacíos. */
function toQuery(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

/**
 * GET con timeout (`timeoutMs`), cuerpo de error del contrato (`{"error": {"code", "message"}}`)
 * y comprobación de la forma de la respuesta con `parser` antes de devolverla.
 */
async function get<T>(path: string, params: Record<string, string | number | undefined>, parser: (raw: unknown) => T, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(getConfig().timeoutMs);
  const sig = signal ? AbortSignal.any([signal, timeout]) : timeout;
  try {
    const res = await fetch(`${baseUrl()}${path}${toQuery(params)}`, { signal: sig });
    if (!res.ok) {
      let code: ApiError['code'] = 'unknown';
      let message = `Error HTTP ${res.status}`;
      try {
        const body = (await res.json()) as { error?: { code?: ApiErrorCode; message?: string } };
        if (body.error) {
          code = body.error.code ?? 'unknown';
          message = body.error.message ?? message;
        }
      } catch {
        /* cuerpo no JSON (p. ej. el proxy sin API detrás): se queda el mensaje por defecto */
      }
      throw new ApiError(message, res.status, code);
    }
    let body: unknown;
    try {
      body = await res.json();
    } catch (e) {
      if (e instanceof SyntaxError) throw new ApiError('La API respondió con un cuerpo que no es JSON.', res.status, 'invalid_response');
      throw e;
    }
    return parser(body);
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof DOMException && e.name === 'TimeoutError') {
      throw new ApiError(`La API no respondió en ${Math.round(getConfig().timeoutMs / 1000)} s.`, 0, 'timeout');
    }
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw new ApiError('No se pudo conectar con la API.', 0, 'network');
  }
}

/**
 * Qué hace:
 *     Pide /eventos a la API real.
 * Recibe:
 *     filters: filtros y límite opcional. signal: cancelación opcional.
 * Devuelve:
 *     La respuesta de eventos ya comprobada (`ApiError` `invalid_response` si la forma no cuadra).
 * Por qué existe:
 *     Es el único punto de acceso HTTP a /eventos (G1); el origen lo elige `dataSource.ts`.
 */
export const apiEvents = (filters: ApiFilters & { limit?: number; cursor?: string }, signal?: AbortSignal) =>
  get<EventsResponse>('/eventos', { ...filters }, parseEvents, signal);

/**
 * Qué hace:
 *     Pide /estadisticas a la API real.
 * Recibe:
 *     filters: filtros. signal: cancelación opcional.
 * Devuelve:
 *     La respuesta de estadísticas ya comprobada.
 * Por qué existe:
 *     Las estadísticas las calcula la API (G1, G3).
 */
export const apiStats = (filters: ApiFilters, signal?: AbortSignal) => get<StatsResponse>('/estadisticas', { ...filters }, parseStats, signal);

/**
 * Qué hace:
 *     Pide /salud a la API real.
 * Recibe:
 *     signal: cancelación opcional.
 * Devuelve:
 *     La respuesta de salud ya comprobada.
 * Por qué existe:
 *     Alimenta el estado del feed y el aviso de datos desactualizados (G7).
 */
export const apiHealth = (signal?: AbortSignal) => get<HealthResponse>('/salud', {}, parseHealth, signal);
