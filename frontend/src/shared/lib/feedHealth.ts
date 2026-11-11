/** Retraso de ingesta (s) a partir del cual los datos se consideran desactualizados (la API no lo calcula). */
export const STALE_THRESHOLD_SECONDS = 300;

import type { EventsMode, HealthResponse } from '@/shared/types/contract';

/**
 * Qué hace:
 *     Calcula el retraso de ingesta como `generated − last_ingestion` y si supera el umbral.
 * Recibe:
 *     health: respuesta de /salud o null. mode: modo de los eventos.
 * Devuelve:
 *     lagSeconds (o null) y stale.
 * Por qué existe:
 *     Avisa de datos desactualizados; en reproducción no hay ingesta que vigilar (G7, G12).
 */
export function ingestionLag(health: HealthResponse | null, mode: EventsMode | undefined): { lagSeconds: number | null; stale: boolean } {
  if (!health || mode === 'replay') return { lagSeconds: null, stale: false };
  const lagSeconds = health.last_ingestion === null ? null : (health.generated - health.last_ingestion) / 1000;
  return { lagSeconds, stale: lagSeconds === null || lagSeconds > STALE_THRESHOLD_SECONDS };
}
