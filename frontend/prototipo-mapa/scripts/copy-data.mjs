// Copia (sin tocar los originales) el mock y las fronteras a public/data del prototipo.
import { copyFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const out = resolve(here, '../public/data')
mkdirSync(out, { recursive: true })
copyFileSync(resolve(here, '../../mock/truncated.json'), resolve(out, 'truncated.json'))
copyFileSync(resolve(here, '../../../data/catalogo/paises.geojson'), resolve(out, 'paises.geojson'))
console.log('Datos copiados a public/data')
