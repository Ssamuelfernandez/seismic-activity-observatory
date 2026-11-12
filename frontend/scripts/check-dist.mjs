// Comprueba que el build de producción no incluye el mock y que config.json es el entregado (T065, G13/G15).
// Uso: node scripts/check-dist.mjs [directorio_dist]   (por defecto ./dist). Sin dependencias.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const dist = process.argv[2] ?? join(root, 'dist');
// Marcas distintivas del mock: constante de mock/backend.ts e identificadores sintéticos de mock/*.json.
const MARKERS = ['mock-backend', 'mock-base-', 'mock-replay-', 'Sintético:'];

/** Lista todos los ficheros bajo `dir` (rutas completas). */
function walk(dir) {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

const mockNames = new Set(readdirSync(join(root, 'mock')).filter((n) => n.endsWith('.json')));
const files = walk(dist);
const problems = [];

for (const f of files) {
  if (mockNames.has(basename(f))) problems.push(`fichero del mock en dist: ${f}`);
  if (f.endsWith('.js')) {
    const text = readFileSync(f, 'utf-8');
    for (const m of MARKERS) if (text.includes(m)) problems.push(`marca del mock «${m}» en ${f}`);
  }
}
const cfgDist = readFileSync(join(dist, 'config.json'), 'utf-8');
const cfgSrc = readFileSync(join(root, 'public', 'config.json'), 'utf-8');
if (cfgDist !== cfgSrc) problems.push('dist/config.json difiere de public/config.json');

console.log(`dist: ${dist}\nficheros revisados: ${files.length}`);
console.log(`ficheros del mock encontrados: ${problems.filter((p) => p.startsWith('fichero')).length}`);
if (problems.length) {
  for (const p of problems) console.error(`FALLO: ${p}`);
  process.exit(1);
}
console.log('OK: sin mock y config.json idéntico.');
