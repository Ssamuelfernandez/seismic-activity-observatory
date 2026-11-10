import { create } from 'zustand';

/** Filtros compartidos: alimentan a la vez /api/eventos y /api/estadisticas. */
export interface Filters {
  mode: 'live' | 'replay';
  /** Ventana hacia atrás desde ahora, en horas; 0 = rango de fechas (`dateFrom`–`dateTo`). */
  hours: number;
  /** Rango personalizado, `AAAA-MM-DD` en UTC; el día final se incluye entero. */
  dateFrom: string;
  dateTo: string;
  /** Magnitud mínima; 0 = sin filtro. */
  minMag: number;
  /** Código ADM0_A3 de tres letras, `none` (sin país) o vacío (todos). */
  country: string;
}

export const DEFAULT_FILTERS: Filters = { mode: 'live', hours: 24, dateFrom: '', dateTo: '', minMag: 0, country: '' };

interface FiltersStore extends Filters {
  set: (patch: Partial<Filters>) => void;
  reset: () => void;
}

/**
 * Qué hace:
 *     Guarda los filtros compartidos y sus acciones `set` y `reset`.
 * Recibe:
 *     Se usa como hook de Zustand.
 * Devuelve:
 *     Los filtros y las acciones.
 * Por qué existe:
 *     Un único estado de filtros para globo, tabla y estadísticas (G6; constitución §17).
 */
export const useFilters = create<FiltersStore>((set) => ({
  ...DEFAULT_FILTERS,
  set: (patch) => set(patch),
  reset: () => set(DEFAULT_FILTERS),
}));
