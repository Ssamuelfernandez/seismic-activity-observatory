/** Estado de los datos que ve la pantalla (data-model.md, DataState). */
export type DataState = 'loading' | 'ready' | 'empty' | 'error';

/**
 * Qué hace:
 *     Deriva el estado de los datos a partir de la lectura de eventos y del error.
 * Recibe:
 *     featureCount: número de eventos de la última lectura, o null si no hay ninguna.
 *     hasError: la última consulta falló.
 * Devuelve:
 *     `error` (sin datos, o con la última lectura buena), `loading` (aún sin nada), `empty` (`features: []`) o `ready`.
 * Por qué existe:
 *     Un error nunca es «0 eventos» y un `features: []` (también en replay) nunca es un error (G9, FR-014).
 */
export function deriveDataState(featureCount: number | null, hasError: boolean): DataState {
  if (hasError) return 'error';
  if (featureCount === null) return 'loading';
  return featureCount === 0 ? 'empty' : 'ready';
}
