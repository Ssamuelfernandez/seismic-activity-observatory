import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import 'maplibre-gl/dist/maplibre-gl.css'
import '../shared/style.css'
import { symbolFor, showCard, showPaintTime } from '../shared/symbology.js'

maplibregl.setWorkerUrl(workerUrl) // MapLibre 6: el worker se sirve como archivo aparte
const t0 = performance.now()
const map = new maplibregl.Map({
  container: 'map',
  attributionControl: false,
  center: [0, 20],
  zoom: 1.5,
  style: {
    version: 8,
    sources: { osm: { type: 'raster', tileSize: 256, tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], maxzoom: 19 } },
    layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
  },
})
map.addControl(new maplibregl.NavigationControl({ showCompass: false }))
window.__map = map // expuesto para la medicion automatica

map.on('load', async () => {
  const [events, countries] = await Promise.all([
    fetch('/data/truncated.json').then((r) => r.json()),
    fetch('/data/paises.geojson').then((r) => r.json()),
  ])
  const byId = new Map(events.features.map((f) => [f.id, f]))
  // Se copian las propiedades de simbolo en cada feature para declarar la capa con expresiones.
  const data = {
    type: 'FeatureCollection',
    features: events.features.map((f) => {
      const s = symbolFor(f)
      return {
        type: 'Feature',
        geometry: f.geometry,
        properties: { eid: f.id, mag: f.properties.mag ?? -99, r: s.radius, c: s.color, hollow: s.hollow },
      }
    }),
  }
  map.addSource('countries', { type: 'geojson', data: countries })
  map.addLayer({ id: 'countries-line', type: 'line', source: 'countries', paint: { 'line-color': '#334155', 'line-width': 0.8 } })
  map.addSource('events', { type: 'geojson', data })
  map.addLayer({
    id: 'events',
    type: 'circle',
    source: 'events',
    // Dibujo por magnitud descendente: los pequenos quedan encima.
    layout: { 'circle-sort-key': ['-', 0, ['get', 'mag']] },
    paint: {
      'circle-radius': ['get', 'r'],
      'circle-color': ['case', ['get', 'hollow'], 'rgba(0,0,0,0)', ['get', 'c']],
      'circle-stroke-color': ['get', 'c'],
      'circle-stroke-width': ['case', ['get', 'hollow'], 2, 1],
    },
  })
  map.once('idle', () => showPaintTime(performance.now() - t0, data.features.length))

  // Tolerancia de 8 px alrededor del toque para pulsar circulos pequenos.
  map.on('click', (e) => {
    const r = 8
    const box = [[e.point.x - r, e.point.y - r], [e.point.x + r, e.point.y + r]]
    const hit = map.queryRenderedFeatures(box, { layers: ['events'] })
    if (hit.length) showCard(byId.get(hit[0].properties.eid))
  })
})
