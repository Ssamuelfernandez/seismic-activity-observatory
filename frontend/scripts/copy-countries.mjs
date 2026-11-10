/**
 * Copia el catálogo de países al directorio público del panel y verifica su huella.
 *
 * Qué hace:
 *     Copia `data/catalogo/paises.geojson` a `frontend/public/datos/paises.geojson` y comprueba
 *     que el SHA-256 de la copia coincide con el de `FUENTES-Y-LICENCIAS.md`.
 * Recibe:
 *     Nada (rutas relativas a este archivo).
 * Devuelve:
 *     Código de salida 0 si la copia es idéntica; 1 si el SHA-256 no coincide.
 * Por qué existe:
 *     El globo carga `/datos/paises.geojson` y debe ser el mismo material reutilizado
 *     (Natural Earth) que usa el resto del proyecto (G0, G14; FR-019).
 */
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const EXPECTED_SHA256 = '6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f';
const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, '../../data/catalogo/paises.geojson');
const target = resolve(here, '../public/datos/paises.geojson');

mkdirSync(dirname(target), { recursive: true });
copyFileSync(source, target);

const actual = createHash('sha256').update(readFileSync(target)).digest('hex');
if (actual !== EXPECTED_SHA256) {
  console.error(`SHA-256 distinto en ${target}\n  esperado: ${EXPECTED_SHA256}\n  obtenido: ${actual}`);
  process.exit(1);
}
console.log(`paises.geojson copiado y verificado (SHA-256 ${actual})`);
