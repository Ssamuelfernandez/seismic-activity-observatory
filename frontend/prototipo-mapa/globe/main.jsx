import { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import Globe from 'react-globe.gl'
import '../shared/style.css'
import { symbolFor, showCard, showPaintTime } from '../shared/symbology.js'

const t0 = performance.now()
// Los puntos del globo miden grados; 1 px de V1 se aproxima a 0,06 grados (limite del globo, ver LEEME).
const DEG_PER_PX = 0.06

function App() {
  const [points, setPoints] = useState([])
  const [countries, setCountries] = useState([])
  const [size, setSize] = useState({ w: window.innerWidth, h: window.innerHeight })
  const painted = useRef(false)
  const globeRef = useRef()

  useEffect(() => {
    Promise.all([
      fetch('/data/truncated.json').then((r) => r.json()),
      fetch('/data/paises.geojson').then((r) => r.json()),
    ]).then(([events, geo]) => {
      setCountries(geo.features)
      setPoints(
        events.features
          .map((f) => {
            const s = symbolFor(f)
            const [lng, lat] = f.geometry.coordinates
            // El globo no dibuja puntos huecos: los de magnitud ND se pintan semitransparentes.
            return { lat, lng, f, r: s.radius * DEG_PER_PX, color: s.hollow ? s.color + '66' : s.color, mag: f.properties.mag ?? -99 }
          })
          .sort((a, b) => b.mag - a.mag),
      )
    })
    const onResize = () => setSize({ w: window.innerWidth, h: window.innerHeight })
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    if (points.length && !painted.current) {
      painted.current = true
      // Dos fotogramas despues de entregar los datos = ya pintados.
      requestAnimationFrame(() => requestAnimationFrame(() => showPaintTime(performance.now() - t0, points.length)))
    }
  }, [points])

  return (
    <Globe
      ref={(g) => { globeRef.current = g; window.__globe = g }}
      width={size.w}
      height={size.h}
      globeImageUrl="https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-blue-marble.jpg"
      pointsData={points}
      pointLat="lat"
      pointLng="lng"
      pointRadius="r"
      pointColor="color"
      pointAltitude={0.004}
      pointsMerge={false}
      onPointClick={(p) => showCard(p.f)}
      polygonsData={countries}
      polygonCapColor={() => 'rgba(0,0,0,0)'}
      polygonSideColor={() => 'rgba(0,0,0,0)'}
      polygonStrokeColor={() => '#e2e8f0'}
      polygonAltitude={0.001}
    />
  )
}

createRoot(document.getElementById('root')).render(<App />)
