import { ApiError } from './client';

const MESSAGE = 'mock no disponible en este build';

/** Sustituto de las funciones de `mock/backend.ts` en producción: todas fallan con un mensaje claro. */
const unavailable = (): never => {
  throw new ApiError(MESSAGE, 0, 'unknown');
};

/**
 * Qué hace:
 *     Reemplaza al servidor simulado en el build de producción (alias `@mock`).
 * Recibe:
 *     Cualquier argumento (se ignora).
 * Devuelve:
 *     Nunca: lanza «mock no disponible en este build».
 * Por qué existe:
 *     Garantiza que en producción no hay camino a datos sintéticos (G15; constitución §7).
 */
export const mockEvents = unavailable;
export const mockStats = unavailable;
export const mockHealth = unavailable;
