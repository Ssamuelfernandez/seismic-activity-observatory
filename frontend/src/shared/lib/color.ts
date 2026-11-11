/**
 * Qué hace:
 *     Convierte un color hexadecimal y una opacidad en `rgba(...)`.
 * Recibe:
 *     hex: «#rrggbb». alpha: opacidad de 0 a 1.
 * Devuelve:
 *     El texto `rgba(r,g,b,a)` que entiende three.js.
 * Por qué existe:
 *     El globo necesita colores con opacidad por antigüedad y enfoque (G2).
 */
export function hexToRgba(hex: string, alpha: number): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`;
}
