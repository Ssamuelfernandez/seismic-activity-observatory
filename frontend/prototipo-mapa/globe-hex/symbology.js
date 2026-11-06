// Simbologia local del prototipo T022 segun V1-V4 de la spec (el T010 real vendra despues).
export const ND_GRAY = '#8A93A0'
export const DEPTH_COLORS = ['#FFF1A6', '#FDB347', '#F26A5A', '#D2468C', '#7C4DCB']
export const DEPTH_CUTS = [10, 35, 70, 300]
export const MIN_HEIGHT = 0.01

/** V1: largo del prisma (fraccion del radio del globo) = max(0,010; 0,0125 x M), M acotada a 0-8; ND = minimo. */
export function heightFor(mag) {
  if (mag == null) return MIN_HEIGHT
  return Math.max(MIN_HEIGHT, 0.0125 * Math.min(8, Math.max(0, mag)))
}

/** V2-V4: color por clase de profundidad; magnitud o profundidad nulas = gris ND. */
export function colorFor(mag, depth) {
  if (mag == null || depth == null) return ND_GRAY
  const i = DEPTH_CUTS.findIndex((c) => depth < c)
  return DEPTH_COLORS[i === -1 ? 4 : i]
}

const nd = (v, f) => (v == null ? 'ND' : f(v))
const comma = (n) => String(n).replace('.', ',')

/** Lineas de la ficha minima (nulos = ND, nunca 0). */
export function cardLines(feature) {
  const p = feature.properties
  return [
    p.place ?? 'Sin descripcion',
    'Magnitud: ' + nd(p.mag, comma) + (p.mag != null && p.magType ? ' (' + p.magType + ')' : ''),
    'Profundidad: ' + nd(feature.geometry.coordinates[2], (d) => comma(d) + ' km'),
    'Fecha: ' + new Date(p.time).toISOString().slice(0, 16).replace('T', ' ') + ' UTC',
    'Pais: ' + (p.country_name ?? 'Sin pais asignado'),
    'SINTETICO (mock)',
  ]
}
