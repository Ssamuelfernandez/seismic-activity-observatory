// Medicion automatica (T006) con Edge headless: tiempo de pintado, fluidez aproximada,
// clic sobre un circulo pequeno, scroll horizontal, atribucion y capturas a 1280 y 375 px.
// Uso: node scripts/measure.mjs <carpeta de salida>   (requiere los builds dist-globe y dist-maplibre)
import puppeteer from 'puppeteer-core'
import { spawn } from 'node:child_process'
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const out = resolve(process.argv[2] ?? 'medidas')
mkdirSync(out, { recursive: true })

const CANDIDATES = [
  { name: 'globe', port: 5181, config: 'globe/vite.config.js' },
  { name: 'maplibre', port: 5182, config: 'maplibre/vite.config.js' },
]
const VIEWPORTS = [
  { label: '1280', width: 1280, height: 800, mobile: false },
  { label: '375', width: 375, height: 812, mobile: true },
]
const RUNS = 3

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function startPreview(c) {
  const p = spawn('node', ['node_modules/vite/bin/vite.js', 'preview', '--config', c.config], { stdio: 'ignore' })
  return p
}

// Corre dentro de la pagina: panea 3 s y devuelve fotogramas y ms medios por fotograma.
const PAN_FN = `(async (name) => {
  const frames = []
  let last = performance.now()
  const start = last
  await new Promise((done) => {
    const step = (t) => {
      frames.push(t - last); last = t
      const k = (t - start) / 3000
      if (name === 'maplibre') window.__map.jumpTo({ center: [-60 + 120 * k, 20], zoom: 2.5 })
      else window.__globe.pointOfView({ lat: 20, lng: -60 + 120 * k, altitude: 1.2 }, 0)
      if (t - start < 3000) requestAnimationFrame(step); else done()
    }
    requestAnimationFrame(step)
  })
  frames.shift()
  const sorted = [...frames].sort((a, b) => a - b)
  return { frames: frames.length, meanMs: frames.reduce((a, b) => a + b, 0) / frames.length, p95Ms: sorted[Math.floor(sorted.length * 0.95)] }
})`

async function measure(browser, c, vp) {
  const result = { candidate: c.name, viewport: vp.label, paintMs: [] }
  for (let i = 0; i < RUNS; i++) {
    const page = await browser.newPage()
    await page.setViewport({ width: vp.width, height: vp.height, isMobile: vp.mobile, hasTouch: vp.mobile, deviceScaleFactor: 1 })
    await page.goto(`http://127.0.0.1:${c.port}/`, { waitUntil: 'load' })
    await page.waitForFunction('window.__paintMs !== undefined', { timeout: 60000 })
    result.paintMs.push(Math.round(await page.evaluate('window.__paintMs')))
    result.count = await page.evaluate('window.__paintCount')
    if (i < RUNS - 1) { await page.close(); continue }
    await sleep(4000) // tiempo para texturas y teselas del fondo
    result.webgl = await page.evaluate(() => {
      const gl = document.createElement('canvas').getContext('webgl')
      const ext = gl && gl.getExtension('WEBGL_debug_renderer_info')
      return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'sin WebGL'
    })
    result.scrollOk = await page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    result.attribution = await page.evaluate(() => {
      const r = document.getElementById('attrib').getBoundingClientRect()
      return { visible: r.bottom <= window.innerHeight && r.right <= window.innerWidth && r.width > 0, fontPx: getComputedStyle(document.getElementById('attrib')).fontSize, height: Math.round(r.height) }
    })
    await page.screenshot({ path: `${out}/${c.name}_${vp.label}.png` })
    result.pan = await page.evaluate(`${PAN_FN}('${c.name}')`)
    // Clic centrado sobre el circulo mas pequeno (M <= 0): comprueba que se abre la ficha.
    const ok = await page.evaluate(async (name) => {
      const data = await fetch('/data/truncated.json').then((r) => r.json())
      const small = data.features.filter((f) => f.properties.mag != null).sort((a, b) => a.properties.mag - b.properties.mag)[0]
      const [lng, lat] = small.geometry.coordinates
      let pt
      if (name === 'maplibre') { window.__map.jumpTo({ center: [lng, lat], zoom: 3 }); await new Promise((r) => setTimeout(r, 1500)); pt = window.__map.project([lng, lat]) }
      else { window.__globe.pointOfView({ lat, lng, altitude: 1.2 }, 0); await new Promise((r) => setTimeout(r, 1500)); pt = window.__globe.getScreenCoords(lat, lng, 0.004) }
      return { x: pt.x, y: pt.y, mag: small.properties.mag }
    }, c.name)
    // 5 intentos en el centro y 4 a 6 px del centro (dedo poco preciso); se cierra la ficha entre intentos.
    const tap = async (x, y) => (vp.mobile ? page.touchscreen.tap(x, y) : page.mouse.click(x, y))
    const opened = () => page.evaluate("document.getElementById('card').style.display === 'block'")
    const reset = () => page.evaluate("document.getElementById('card').style.display = 'none'")
    const groups = [['clickCenterHits', [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]], ['clickOffset6pxHits', [[6, 0], [-6, 0], [0, 6], [0, -6]]]]
    for (const [label, offsets] of groups) {
      let hits = 0
      for (const [dx, dy] of offsets) {
        await tap(ok.x + dx, ok.y + dy)
        await sleep(400)
        if (await opened()) hits++
        await reset()
      }
      result[label] = hits + '/' + offsets.length
    }
    result.clickedMag = ok.mag
    await tap(ok.x, ok.y)
    await sleep(500)
    await page.screenshot({ path: `${out}/${c.name}_${vp.label}_ficha.png` })
    await page.close()
  }
  return result
}

const servers = CANDIDATES.map(startPreview)
await sleep(3000)
const browser = await puppeteer.launch({ executablePath: EDGE, headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] })
const results = []
try {
  for (const c of CANDIDATES) for (const vp of VIEWPORTS) {
    try { results.push(await measure(browser, c, vp)) } catch (e) { results.push({ candidate: c.name, viewport: vp.label, error: String(e) }) }
  }
} finally {
  await browser.close()
  servers.forEach((s) => s.kill())
}
writeFileSync(`${out}/medidas.json`, JSON.stringify({ edge: await browserVersion(), results }, null, 2))
console.log(JSON.stringify(results, null, 2))

async function browserVersion() { return 'Edge 156 headless (puppeteer-core)' }
