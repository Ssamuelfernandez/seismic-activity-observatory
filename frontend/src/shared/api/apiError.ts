import type { ApiErrorCode } from '@/shared/types/contract';

/** Código de un `ApiError`: los del contrato más los que genera el propio panel. */
export type ApiErrorKind = ApiErrorCode | 'network' | 'timeout' | 'invalid_response' | 'unknown';

/**
 * Qué hace:
 *     Error de la API o de red, con el código del contrato cuando existe.
 * Recibe:
 *     message: texto para el usuario. status: estado HTTP (0 si no hubo respuesta). code: código del error.
 * Devuelve:
 *     Una instancia de `Error` con `status` y `code`.
 * Por qué existe:
 *     `client.ts` y `parse.ts` lanzan el mismo tipo de error y el panel lo muestra sin confundirlo con «0 eventos» (G9, FR-011).
 */
export class ApiError extends Error {
  constructor(
    message: string,
    /** Estado HTTP; 0 si no hubo respuesta (red caída, API apagada). */
    readonly status: number,
    readonly code: ApiErrorKind,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
