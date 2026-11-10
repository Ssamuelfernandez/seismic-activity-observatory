// Simbología de los sismos.
//   Magnitud    -> largo del prisma (lineal, tope M 8); nula -> altura mínima
//   Profundidad -> color (5 clases con los cortes de la API: 10/35/70/300)
//   Antigüedad  -> opacidad
//   Ondas       -> solo eventos con magnitud (nunca nula) por encima del umbral
export const ND_GRAY = '#8a93a0';
export const MAX_MAG = 8;
const MIN_HEIGHT = 0.01;

/** Una clase de profundidad: límite superior (exclusivo), rango escrito y color. */
export interface DepthClass {
  max: number;
  range: string;
  color: string;
}

/**
 * Clases de profundidad con los cortes de `histograms.depth` de la API (api.md §5.1).
 * Límite inferior inclusivo; las profundidades negativas caen en la primera clase.
 */
export const DEPTH_CLASSES: readonly DepthClass[] = [
  { max: 10, range: '< 10 km', color: '#ffd23f' },
  { max: 35, range: '10–35 km', color: '#ff963a' },
  { max: 70, range: '35–70 km', color: '#ff5a36' },
  { max: 300, range: '70–300 km', color: '#d7539a' },
  { max: Infinity, range: '≥ 300 km', color: '#b04cff' },
];

/** Rampa cálida de 5 clases para el modo «color por magnitud». */
export const WARM_RAMP = ['#fff1a6', '#fdb347', '#f26a5a', '#d2468c', '#7c4dcb'];
export const MAG_CUTS = [3, 4, 5, 6];
export const MAG_LABELS = ['< 3', '3–4', '4–5', '5–6', '≥ 6'];

/**
 * Largo del prisma de un sismo.
 *
 * Qué hace:
 *     Lineal con la magnitud (0,0125 por unidad), con tope M 8 y mínimo 0,01.
 * Recibe:
 *     mag: magnitud, o null si no hay dato.
 * Devuelve:
 *     Fracción del radio del globo; la altura mínima si la magnitud es nula o negativa.
 * Por qué existe:
 *     Una magnitud nula no se trata como 0: se dibuja como barra mínima (G2, SC-006).
 */
export function heightFor(mag: number | null): number {
  if (mag == null) return MIN_HEIGHT;
  return Math.max(MIN_HEIGHT, 0.0125 * Math.min(MAX_MAG, Math.max(0, mag)));
}

/**
 * Clase de profundidad de un evento.
 *
 * Qué hace:
 *     Busca la primera clase cuyo límite superior es mayor que la profundidad.
 * Recibe:
 *     depthKm: profundidad en km (puede ser negativa), o null si no hay dato.
 * Devuelve:
 *     La clase (`DepthClass`), o null si la profundidad es nula (ND).
 * Por qué existe:
 *     Mismos cortes que los histogramas de la API, para que mapa y estadísticas coincidan (G2, SC-005).
 */
export function depthClassFor(depthKm: number | null): DepthClass | null {
  if (depthKm == null) return null;
  return DEPTH_CLASSES.find((c) => depthKm < c.max) ?? DEPTH_CLASSES[DEPTH_CLASSES.length - 1];
}

/**
 * Color por profundidad.
 *
 * Recibe:
 *     depthKm: profundidad en km, o null.
 * Devuelve:
 *     El color de su clase, o el gris ND si es nula.
 * Por qué existe:
 *     La profundidad se codifica en el color del prisma (G2).
 */
export function colorByDepth(depthKm: number | null): string {
  return depthClassFor(depthKm)?.color ?? ND_GRAY;
}

/**
 * Color por magnitud (rampa cálida de cinco tramos).
 *
 * Recibe:
 *     mag: magnitud, o null.
 * Devuelve:
 *     El color del tramo, o el gris ND si es nula.
 * Por qué existe:
 *     Modo opcional «color por magnitud» del globo (G2).
 */
export function colorByMag(mag: number | null): string {
  if (mag == null) return ND_GRAY;
  const i = MAG_CUTS.findIndex((c) => mag < c);
  return WARM_RAMP[i === -1 ? WARM_RAMP.length - 1 : i];
}

/**
 * Color de un evento según el modo de color elegido (el mismo en el globo, la lista y la tabla).
 *
 * Recibe:
 *     e: evento (solo se leen `mag` y la profundidad).
 *     colorMode: `depth`, `mag` o `single`.
 * Devuelve:
 *     El color en hexadecimal; con magnitud nula, el gris ND (salvo en `single`).
 * Por qué existe:
 *     Una sola regla de color para todas las vistas; la magnitud nula es una barra ND gris (G2, SC-006).
 */
export function colorForEvent(
  e: { properties: { mag: number | null }; geometry: { coordinates: [number, number, number | null] } },
  colorMode: 'depth' | 'mag' | 'single',
): string {
  if (colorMode === 'single') return '#ff7a1a';
  if (e.properties.mag === null) return ND_GRAY;
  if (colorMode === 'mag') return colorByMag(e.properties.mag);
  return colorByDepth(e.geometry.coordinates[2]);
}

/**
 * Opacidad por antigüedad.
 *
 * Recibe:
 *     ageMs: antigüedad del evento en ms.
 *     windowMs: ventana en ms en la que la opacidad baja de 1 a 0,25.
 * Devuelve:
 *     1 si es reciente y 0,25 al llegar al final de la ventana.
 * Por qué existe:
 *     Los eventos recientes destacan sobre los antiguos (G2).
 */
export function ageOpacity(ageMs: number, windowMs: number): number {
  if (windowMs <= 0) return 1;
  const t = Math.min(1, Math.max(0, ageMs / windowMs));
  return 1 - 0.75 * t;
}
