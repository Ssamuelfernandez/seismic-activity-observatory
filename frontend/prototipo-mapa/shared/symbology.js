// Simbologia local y simple del prototipo (V1-V4). El T010 real vendra despues.
export const ND_GRAY = '#9CA3AF'
const COLORS = ['#FDE725', '#5EC962', '#21918C', '#3B528B', '#440154']
const CUTS = [10, 35, 70, 300]

/** Radio en px: 3 + 1,5 * M con M acotada entre 0 y 8; ND = 5. */
export function radiusFor(mag) {
  if (mag == null) return 5
  return 3 + 1.5 * Math.min(8, Math.max(0, mag))
}

/** Color por clase de profundidad; nula = gris. */
export function colorFor(depth) {
  if (depth == null) return ND_GRAY
  const i = CUTS.findIndex((c) => depth < c)
  return COLORS[i === -1 ? 4 : i]
}

/** Simbolo de una feature: radio, color y si es hueco (magnitud ND). */
export function symbolFor(feature) {
  const mag = feature.properties.mag
  const depth = feature.geometry.coordinates[2]
  return { radius: radiusFor(mag), color: colorFor(depth), hollow: mag == null }
}

const nd = (v, f) => (v == null ? 'ND' : f(v))

/** Texto de la ficha minima. */
export function cardLines(feature) {
  const p = feature.properties
  return [
    p.place ?? 'Sin descripcion',
    'Magnitud: ' + nd(p.mag, (m) => String(m).replace('.', ',')) + (p.magType ? ' (' + p.magType + ')' : ''),
    'Profundidad: ' + nd(feature.geometry.coordinates[2], (d) => String(d).replace('.', ',') + ' km'),
    'Fecha: ' + new Date(p.time).toISOString().slice(0, 16).replace('T', ' ') + ' UTC',
    'Pais: ' + (p.country_name ?? 'Sin pais asignado'),
    'SINTETICO (mock)',
  ]
}

/** Muestra el contador de tiempo hasta pintar. */
export function showPaintTime(ms, count) {
  window.__paintMs = ms
  window.__paintCount = count
  document.getElementById('timer').textContent = `${count} eventos pintados en ${(ms / 1000).toFixed(2)} s`
}

/** Abre la ficha minima de un evento. */
export function showCard(feature) {
  const card = document.getElementById('card')
  card.innerHTML = '<button id="close" aria-label="Cerrar">x</button>' + cardLines(feature).map((l) => `<div>${l}</div>`).join('')
  card.style.display = 'block'
  document.getElementById('close').onclick = () => (card.style.display = 'none')
}
