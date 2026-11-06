// Medicion automatica de T022 (prisma hexagonal + celdas) con Edge headless.
// Uso: node scripts/measure-hex.mjs <carpeta de salida>   (requiere `build` de globe-hex)
import puppeteer from 'puppeteer-core'
import { spawn } from 'node:child_process'
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const out = resolve(process.argv[2] ?? 'medidas-hex')
mkdirSync(out, { recursive: true })
const ONLY = process.argv[3] ?? 'all' // 'all' | 'clicks' | 'colors'
const BASE = 'http://127.0.0.1:5183/'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const VPS = [
  { label: '1280', width: 1280, height: 800, mobile: false },
  { label: '375', width: 375, height: 812, mobile: true },
]
const CLASS_TOKENS = { d1: '#FFF1A6', d2: '#FDB347', d3: '#F26A5A', d4: '#D2468C', d5: '#7C4DCB', nd: '#8A93A0' }

const server = spawn('node', ['node_modules/vite/bin/vite.js', 'preview', '--config', 'globe-hex/vite.config.js'], { stdio: 'ignore' })
await sleep(3000)
const browser = await puppeteer.launch({ executablePath: EDGE, headless: true, args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] })
const result = { fecha: new Date().toISOString(), paint: {}, pan: {}, cells: {}, clicks: [], colors: [] }

async function open(vp, query, dsf = 1) {
  const page = await browser.newPage()
  await page.setViewport({ width: vp.width, height: vp.height, isMobile: vp.mobile, hasTouch: vp.mobile, deviceScaleFactor: dsf })
  await page.goto(BASE + (query ? '?' + query : ''), { waitUntil: 'load' })
  await page.waitForFunction('window.__paintMs !== undefined', { timeout: 60000 })
  return page
}

// Datos del mock dentro de la pagina: clase de profundidad y objetivo por magnitud.
const FIND = `(async () => {
  const d = await fetch('/data/truncated.json').then((r) => r.json())
  const cls = (f) => { const z = f.geometry.coordinates[2], m = f.properties.mag; if (m == null || z == null) return 'nd'; return z < 10 ? 'd1' : z < 35 ? 'd2' : z < 70 ? 'd3' : z < 300 ? 'd4' : 'd5' }
  const pick = {}
  for (const f of d.features) {
    const c = cls(f); const m = f.properties.mag
    if (c === 'nd') { if (!pick.nd_mag && f.properties.mag == null) pick.nd_mag = f; continue }
    // la de mayor magnitud de cada clase (prisma alto, bien visible)
    if (!pick[c] || m > pick[c].properties.mag) pick[c] = f
  }
  const withMag = d.features.filter((f) => f.properties.mag != null).sort((a, b) => a.properties.mag - b.properties.mag)
  pick.small = withMag[0]
  pick.mid = withMag.find((f) => f.properties.mag >= 4 && f.properties.mag < 4.2)
  return { pick, ndCount: d.features.filter((f) => f.properties.mag == null).length }
})()`

const PAN = `(async () => {
  const frames = []; let last = performance.now(); const start = last
  await new Promise((done) => { const step = (t) => { frames.push(t - last); last = t
    window.__globe.pointOfView({ lat: 20, lng: -60 + 120 * ((t - start) / 3000), altitude: 1.2 }, 0)
    if (t - start < 3000) requestAnimationFrame(step); else done() }; requestAnimationFrame(step) })
  frames.shift(); const s = [...frames].sort((a, b) => a - b)
  return { frames: frames.length, meanMs: frames.reduce((a, b) => a + b, 0) / frames.length, p95Ms: s[Math.floor(s.length * 0.95)] }
})()`

// Histograma de colores de un recorte de captura (decodificado en la pagina).
async function histogram(page, buf) {
  const b64 = Buffer.from(buf).toString('base64')
  return page.evaluate(async (b64) => {
    const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode()
    const c = document.createElement('canvas'); c.width = img.width; c.height = img.height
    const x = c.getContext('2d'); x.drawImage(img, 0, 0)
    const px = x.getImageData(0, 0, c.width, c.height).data
    const cnt = new Map()
    for (let i = 0; i < px.length; i += 4) {
      const k = ((px[i] << 16) | (px[i + 1] << 8) | px[i + 2]); if (k === 0) continue
      cnt.set(k, (cnt.get(k) ?? 0) + 1)
    }
    return [...cnt.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k, n]) => ({ hex: '#' + k.toString(16).padStart(6, '0').toUpperCase(), n }))
  }, b64)
}

try {
  // 1. Tiempo hasta pintar (3 corridas por resolucion y viewport) y celdas.
  if (ONLY === 'all') for (const vp of VPS) for (const res of [3, 4]) {
    const times = []
    for (let i = 0; i < 3; i++) {
      const page = await open(vp, `res=${res}`)
      times.push(Math.round(await page.evaluate('window.__paintMs')))
      if (i === 2) {
        await sleep(2500)
        result.cells[`res${res}`] = await page.evaluate(() => document.querySelector('#controls .row:last-child').textContent)
        result.scrollOk = result.scrollOk ?? {}
        result.scrollOk[vp.label] = await page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        if (res === 3) await page.screenshot({ path: `${out}/hex_${vp.label}_inicial_res3.png` })
        if (res === 4) await page.screenshot({ path: `${out}/hex_${vp.label}_inicial_res4.png` })
        const pans = []
        for (let k = 0; k < 3; k++) pans.push(await page.evaluate(PAN))
        result.pan[`${vp.label}_res${res}`] = pans.map((p) => ({ frames: p.frames, meanMs: +p.meanMs.toFixed(1), p95Ms: +p.p95Ms.toFixed(1), fps: +(1000 / p.meanMs).toFixed(1) }))
        await sleep(500)
        if (res === 3) await page.screenshot({ path: `${out}/hex_${vp.label}_escala_globo.png` })
      }
      await page.close()
    }
    result.paint[`${vp.label}_res${res}`] = times
  }

  // 2. Clic sobre un prisma pequeno: 0, 3, 6 y 12 px del centro, con y sin «el mas cercano».
  const OFFS = [
    ['0', [[0, 0], [0, 0], [0, 0], [0, 0]]],
    ['3', [[3, 0], [-3, 0], [0, 3], [0, -3]]],
    ['6', [[6, 0], [-6, 0], [0, 6], [0, -6]]],
    ['12', [[12, 0], [-12, 0], [0, 12], [0, -12]]],
  ]
  const configs = [
    { vp: VPS[0], q: 'near=0&w=0.45' }, { vp: VPS[0], q: 'near=1&tol=12&w=0.45' }, { vp: VPS[0], q: 'near=1&tol=22&w=0.45' },
    { vp: VPS[0], q: 'near=0&w=0.6' }, { vp: VPS[0], q: 'near=0&w=0.8' },
    { vp: VPS[1], q: 'near=0&w=0.45' }, { vp: VPS[1], q: 'near=1&tol=12&w=0.45' }, { vp: VPS[1], q: 'near=1&tol=22&w=0.45' },
    { vp: VPS[1], q: 'near=0&w=0.8' },
  ]
  if (ONLY !== 'colors') for (const cf of configs) {
    const page = await open(cf.vp, cf.q)
    const { pick } = await page.evaluate(FIND)
    const target = pick.small
    const [lng, lat] = target.geometry.coordinates
    await page.evaluate(`window.__globe.pointOfView({ lat: ${lat}, lng: ${lng}, altitude: 1.2 }, 0)`)
    await sleep(1500)
    const pt = await page.evaluate(`window.__globe.getScreenCoords(${lat}, ${lng}, 0.005)`)
    const expected = target.properties.place
    const row = { viewport: cf.vp.label, query: cf.q, mag: target.properties.mag }
    for (const [label, offs] of OFFS) {
      let opened = 0, right = 0
      for (const [dx, dy] of offs) {
        if (cf.vp.mobile) await page.touchscreen.tap(pt.x + dx, pt.y + dy)
        else { await page.mouse.move(pt.x + dx, pt.y + dy); await sleep(200); await page.mouse.click(pt.x + dx, pt.y + dy) } // el raton se mueve antes: three-globe detecta el objeto al mover
        await sleep(350)
        const txt = await page.evaluate("document.getElementById('card').style.display === 'block' ? document.getElementById('card').innerText : ''")
        if (txt) { opened++; if (txt.includes(expected)) right++ }
        await page.evaluate("document.getElementById('card').style.display = 'none'")
      }
      row[`px${label}`] = `${right}/${offs.length}` + (opened !== right ? ` (abre otra ficha: ${opened - right})` : '')
    }
    result.clicks.push(row)
    await page.close()
  }

  // 3. Prismas de cerca y color visible frente al token (1280 px, factor de escala 2 para ampliar).
  if (ONLY !== 'clicks') for (const light of (process.env.LIGHTS ?? 'defecto,suave,plana').split(',')) {
    const page = await open(VPS[0], `light=${light}&w=0.45`, 2)
    const { pick } = await page.evaluate(FIND)
    const jobs = [['d1', pick.d1], ['d2', pick.d2], ['d3', pick.d3], ['d4', pick.d4], ['d5', pick.d5], ['nd', pick.nd_mag]]
    for (const [cls, f] of jobs) {
      if (!f) continue
      const [lng, lat] = f.geometry.coordinates
      for (const view of ['cenital', 'oblicuo']) {
        const off = view === 'cenital' ? 0 : -1.2
        await page.evaluate(`window.__globe.pointOfView({ lat: ${lat + off}, lng: ${lng}, altitude: ${view === 'cenital' ? 0.4 : 0.25} }, 0)`)
        await sleep(900)
        const c = await page.evaluate(`window.__globe.getScreenCoords(${lat}, ${lng}, 0.005)`)
        const clip = { x: Math.max(0, c.x - 60), y: Math.max(0, c.y - 90), width: 120, height: 150 }
        const buf = await page.screenshot({ clip })
        if (light === 'defecto' || cls === 'd3') writeFileSync(`${out}/cerca_${light}_${cls}_M${f.properties.mag ?? 'ND'}_${view}.png`, buf)
        result.colors.push({ light, cls, token: CLASS_TOKENS[cls], mag: f.properties.mag, view, top: await histogram(page, buf) })
      }
    }
    if (light === 'defecto') {
      // Prismas de distinta altura (M0, M4, M8) en vista oblicua, recortes ampliados.
      for (const [name, f] of [['M-0,5', pick.small], ['M4', pick.mid], ['M6,5', pick.d1]]) {
        if (!f) continue
        const [lng, lat] = f.geometry.coordinates
        await page.evaluate(`window.__globe.pointOfView({ lat: ${lat - 1.0}, lng: ${lng}, altitude: 0.2 }, 0)`)
        await sleep(900)
        const c = await page.evaluate(`window.__globe.getScreenCoords(${lat}, ${lng}, 0.005)`)
        await page.screenshot({ path: `${out}/cerca_altura_${name.replace(",", "c")}.png`, clip: { x: Math.max(0, c.x - 150), y: Math.max(0, c.y - 150), width: 300, height: 300 } })
      }
      await page.evaluate(`window.__globe.pointOfView({ lat: 20, lng: -60, altitude: 0.5 }, 0)`)
      await sleep(900)
      await page.screenshot({ path: `${out}/hex_1280_zoom_regional.png` })
    }
    await page.close()
  }
} finally {
  await browser.close()
  server.kill()
}
writeFileSync(`${out}/medidas-hex${ONLY === 'all' ? '' : '-' + ONLY}.json`, JSON.stringify(result, null, 2))
console.log(JSON.stringify({ ...result, colors: undefined }, null, 2))
