// Suma el tamano comprimido (gzip) de todos los archivos de un build (sin los datos de public/data).
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { gzipSync } from 'node:zlib'
import { join } from 'node:path'

function walk(dir) {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    return statSync(p).isDirectory() ? walk(p) : [p]
  })
}

for (const dir of process.argv.slice(2)) {
  let raw = 0
  let gz = 0
  for (const f of walk(dir).filter((p) => !p.split('\\').join('/').includes('/data/'))) {
    const b = readFileSync(f)
    const g = gzipSync(b).length
    raw += b.length
    gz += g
    console.log(`${dir}: ${f.slice(dir.length)} ${(b.length / 1024).toFixed(1)} kB -> ${(g / 1024).toFixed(1)} kB gzip`)
  }
  console.log(`${dir}: TOTAL ${(raw / 1024).toFixed(1)} kB sin comprimir, ${(gz / 1024).toFixed(1)} kB gzip`)
}
