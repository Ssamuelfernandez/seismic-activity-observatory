/**
 * Utilidades de formato para mostrar valores del contrato.
 *
 * Reglas (constitución §5, data-model.md): un valor nulo se muestra como «ND»
 * y nunca como 0; el decimal lleva coma; los negativos se muestran tal cual
 * (con el signo menos tipográfico «−»); las fechas se muestran en UTC.
 */

/** Texto que representa un dato no disponible. */
export const ND = 'ND';
/** Texto fijo cuando un evento no tiene país. */
export const NO_COUNTRY_TEXT = 'Sin país asignado';
/** Texto fijo cuando un evento no tiene descripción de lugar. */
export const NO_PLACE_TEXT = 'Sin descripción';

const MINUS_SIGN = '\u2212';

/**
 * Formatea un número con coma decimal y signo menos tipográfico.
 *
 * Qué hace:
 *     Convierte `-0.06` en «−0,06»; un nulo o no finito da «ND», nunca «0».
 * Recibe:
 *     value: número a mostrar, o null/undefined si no hay dato.
 * Devuelve:
 *     El texto listo para la interfaz.
 * Por qué existe:
 *     Garantiza que los nulos no se confundan con ceros (G2, SC-005, SC-013).
 */
export function formatDecimal(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return ND;
  }
  return String(value).replace('-', MINUS_SIGN).replace('.', ',');
}

/**
 * Formatea milisegundos Unix como «AAAA-MM-DD HH:mm UTC».
 *
 * Qué hace:
 *     Convierte un instante en ms a texto en UTC, sin segundos.
 * Recibe:
 *     ms: instante en milisegundos Unix, o null.
 * Devuelve:
 *     El texto, o «ND» si el valor falta o no es válido.
 * Por qué existe:
 *     La ficha muestra `time` y `updated` sin alterar el entero original (FR-014).
 */
export function formatUtc(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || !Number.isFinite(ms)) {
    return ND;
  }
  const iso = new Date(ms).toISOString();
  return `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC`;
}

/**
 * Devuelve el país a mostrar, o el texto fijo si no hay.
 *
 * Recibe:
 *     countryName: `country_name` del evento (puede ser null).
 * Devuelve:
 *     El nombre, o «Sin país asignado».
 * Por qué existe:
 *     Un evento en el mar no tiene país y no debe mostrarse vacío (FR-014).
 */
export function formatCountry(countryName: string | null): string {
  return countryName ? countryName : NO_COUNTRY_TEXT;
}

/**
 * Devuelve la descripción del lugar, o el texto fijo si no hay.
 *
 * Recibe:
 *     place: `place` del evento (puede ser null).
 * Devuelve:
 *     El texto, o «Sin descripción».
 * Por qué existe:
 *     `place` es nulable en el contrato (api.md §3.4).
 */
export function formatPlace(place: string | null): string {
  return place ? place : NO_PLACE_TEXT;
}

/**
 * Formatea la magnitud con su tipo, p. ej. «Magnitud 5,4 (mww)».
 *
 * Recibe:
 *     mag: magnitud o null.
 *     magType: tipo de magnitud o null.
 * Devuelve:
 *     El texto; cada dato ausente se muestra como «ND».
 * Por qué existe:
 *     Muestra `magType` en la ficha (G12).
 */
export function formatMagnitude(mag: number | null, magType: string | null): string {
  return `Magnitud ${formatDecimal(mag)} (${magType ?? ND})`;
}
