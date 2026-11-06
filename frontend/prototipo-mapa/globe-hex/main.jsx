import { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { createPortal } from 'react-dom'
import * as THREE from 'three'
import { polygonToCells } from 'h3-js'
import Globe from 'react-globe.gl'
import './style.css'
import { heightFor, colorFor, cardLines } from './symbology.js'

const t0 = performance.now()
const q = new URLSearchParams(location.search)
const num = (k, d) => (q.has(k) ? Number(q.get(k)) : d)
// Valores iniciales desde la URL (para medir) y editables en vivo desde el panel.
const INIT = { res: num('res', 3), width: num('w', 0.45), near: num('near', 0), tol: num('tol', 12), light: q.get('light') ?? 'defecto' }
const RES_OPTS = [3, 4]
const WIDTH_OPTS = [0.3, 0.45, 0.6, 0.8]
const TOL_OPTS = [8, 12, 22]
const LIGHT_OPTS = ['defecto', 'suave', 'alta', 'plana']
const HEX_COLOR = '#151A20' // token hud-land (diseno-visual.md)
const R = 100 // radio del globo en unidades de three-globe

// Luces: 'defecto' replica las de globe.gl; 'suave' y 'plana' son ajustes para ver el color del token.
function makeLights(kind) {
  if (kind === 'suave') return [new THREE.AmbientLight(0xffffff, 0.65 * Math.PI), new THREE.DirectionalLight(0xffffff, 0.55 * Math.PI)]
  if (kind === 'alta') return [new THREE.AmbientLight(0xffffff, 0.9 * Math.PI), new THREE.DirectionalLight(0xffffff, 0.3 * Math.PI)]
  if (kind === 'plana') return [new THREE.AmbientLight(0xffffff, Math.PI)]
  return [new THREE.AmbientLight(0xcccccc, Math.PI), new THREE.DirectionalLight(0xffffff, 0.6 * Math.PI)]
}

// Vector unitario de una posicion (misma convencion que three-globe) para saber si da la cara a la camara.
function unitVec(lat, lng) {
  const phi = ((90 - lat) * Math.PI) / 180
  const theta = ((90 - lng) * Math.PI) / 180
  return [Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta)]
}

/** Abre la ficha minima de un evento. */
function showCard(feature) {
  const card = document.getElementById('card')
  card.innerHTML =
    '<button id="close" aria-label="Cerrar">x</button><div class="t">FICHA (MINIMA)</div>' +
    cardLines(feature).map((l) => `<div>${l}</div>`).join('')
  card.style.display = 'block'
  document.getElementById('close').onclick = () => (card.style.display = 'none')
}

function Opts({ label, value, options, onPick, fmt = String }) {
  return (
    <div className="row">
      <div className="lbl">{label}</div>
      <div className="opts">
        {options.map((o) => (
          <button key={o} className={o === value ? 'on' : ''} onClick={() => onPick(o)}>{fmt(o)}</button>
        ))}
      </div>
    </div>
  )
}

function App() {
  const [points, setPoints] = useState([])
  const [land, setLand] = useState([])
  const [p, setP] = useState(INIT)
  const [cells, setCells] = useState(null)
  const [size, setSize] = useState({ w: window.innerWidth, h: window.innerHeight })
  const painted = useRef(false)
  const globeRef = useRef()
  const down = useRef(null)
  const set = (k) => (v) => setP((s) => ({ ...s, [k]: v }))

  useEffect(() => {
    Promise.all([fetch('/data/truncated.json').then((r) => r.json()), fetch('/data/paises.geojson').then((r) => r.json())]).then(([events, geo]) => {
      // Continentes sin la Antartida (ADM0_A3 = ATA); el archivo original no se modifica.
      setLand(geo.features.filter((f) => f.properties.ADM0_A3 !== 'ATA'))
      setPoints(
        events.features.map((f) => {
          const [lng, lat] = f.geometry.coordinates
          const alt = heightFor(f.properties.mag)
          return { lat, lng, alt, f, color: colorFor(f.properties.mag, f.geometry.coordinates[2]), n: unitVec(lat, lng) }
        }),
      )
    })
    const onResize = () => setSize({ w: window.innerWidth, h: window.innerHeight })
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  // Contador de tiempo hasta pintar: dos fotogramas despues de entregar puntos y celdas.
  useEffect(() => {
    if (points.length && land.length && !painted.current) {
      painted.current = true
      requestAnimationFrame(() =>
        requestAnimationFrame(() => {
          const ms = performance.now() - t0
          window.__paintMs = ms
          window.__paintCount = points.length
          document.getElementById('timer').textContent = `${points.length} eventos pintados en ${(ms / 1000).toFixed(2)} s`
        }),
      )
    }
  }, [points, land])

  // Numero de celdas dibujadas (suma por pais, como dibuja la capa) y distintas; se calcula despues de pintar.
  useEffect(() => {
    if (!land.length || !points.length) return
    const id = setTimeout(() => {
      const all = []
      for (const f of land) {
        const g = f.geometry
        const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates
        polys.forEach((c) => polygonToCells(c, p.res, true).forEach((i) => all.push(i)))
      }
      setCells({ res: p.res, drawn: all.length, unique: new Set(all).size })
    }, 600)
    return () => clearTimeout(id)
  }, [land, p.res, points])

  useEffect(() => {
    const g = globeRef.current
    if (g) g.lights(makeLights(p.light))
  }, [p.light, points])

  // Clic con «el mas cercano»: de los prismas visibles elige el de centro mas cercano al clic dentro de la tolerancia.
  const pick = (x, y) => {
    const g = globeRef.current
    const cam = g.camera().position
    let best = null
    let bestD = p.tol
    for (const pt of points) {
      if (pt.n[0] * cam.x + pt.n[1] * cam.y + pt.n[2] * cam.z <= R) continue // cara oculta del globo
      const s = g.getScreenCoords(pt.lat, pt.lng, pt.alt / 2)
      const d = Math.hypot(s.x - x, s.y - y)
      if (d < bestD) { bestD = d; best = pt }
    }
    return best
  }
  useEffect(() => {
    if (!p.near || !points.length) return
    const el = document.getElementById('root')
    const onDown = (e) => (down.current = [e.clientX, e.clientY])
    const onUp = (e) => {
      const d = down.current
      if (!d || Math.hypot(e.clientX - d[0], e.clientY - d[1]) > 5) return // arrastre, no clic
      const r = el.getBoundingClientRect()
      const hit = pick(e.clientX - r.left, e.clientY - r.top)
      if (hit) showCard(hit.f)
    }
    el.addEventListener('pointerdown', onDown)
    el.addEventListener('pointerup', onUp)
    return () => { el.removeEventListener('pointerdown', onDown); el.removeEventListener('pointerup', onUp) }
  })

  const ctl = useMemo(
    () => (
      <>
        <Opts label="Celdas (resolucion H3)" value={p.res} options={RES_OPTS} onPick={set('res')} />
        <Opts label="Anchura prisma (grados)" value={p.width} options={WIDTH_OPTS} onPick={set('width')} fmt={(v) => String(v).replace('.', ',')} />
        <Opts label="Clic" value={p.near} options={[0, 1]} onPick={set('near')} fmt={(v) => (v ? 'MAS CERCANO' : 'EXACTO')} />
        <Opts label="Tolerancia (px)" value={p.tol} options={TOL_OPTS} onPick={set('tol')} />
        <Opts label="Luces" value={p.light} options={LIGHT_OPTS} onPick={set('light')} fmt={(v) => v.toUpperCase()} />
        <div className="row lbl">{cells ? `Celdas res ${cells.res}: ${cells.drawn} dibujadas (${cells.unique} distintas)` : 'Celdas: calculando'}</div>
      </>
    ),
    [p, cells],
  )

  return (
    <>
      <Globe
        ref={(g) => { globeRef.current = g; window.__globe = g }}
        width={size.w}
        height={size.h}
        backgroundColor="#000000"
        globeImageUrl={null}
        showAtmosphere={false}
        pointsData={points}
        pointLat="lat"
        pointLng="lng"
        pointAltitude="alt"
        pointRadius={p.width}
        pointColor="color"
        pointResolution={6}
        pointsMerge={false}
        onPointClick={p.near ? undefined : (pt) => showCard(pt.f)}
        hexPolygonsData={land}
        hexPolygonResolution={p.res}
        hexPolygonMargin={0.2}
        hexPolygonColor={() => HEX_COLOR}
        hexPolygonAltitude={0.001}
      />
      {createPortal(ctl, document.getElementById('controls'))}
    </>
  )
}

createRoot(document.getElementById('root')).render(<App />)
