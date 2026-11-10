import { useMemo } from 'react';
import type { Appearance } from '@/shared/lib/appearance';

const TILE = 256;
/** Niveles de brillo (0-255) que puede subir un punto de grano con intensidad 1. */
const MAX_LEVELS = 60;

/**
 * Genera el patrón de ruido a partir del color de fondo: cada punto es ese mismo color con un poco
 * más de brillo (más o menos según la intensidad), así el grano es del mismo tono que el fondo.
 */
function makeNoiseUrl(bgHex: string, intensity: number): string {
  const n = parseInt(bgHex.slice(1), 16);
  const base = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  const amp = intensity * MAX_LEVELS;
  const canvas = document.createElement('canvas');
  canvas.width = TILE;
  canvas.height = TILE;
  const ctx = canvas.getContext('2d')!;
  const img = ctx.createImageData(TILE, TILE);
  for (let i = 0; i < img.data.length; i += 4) {
    // Producto de dos azares: muchos puntos casi sin cambio y pocos más claros, como un grano real.
    const lift = Math.random() * Math.random() * amp;
    for (let c = 0; c < 3; c += 1) img.data[i + c] = Math.min(255, Math.round(base[c] + lift));
    img.data[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return canvas.toDataURL('image/png');
}

/**
 * Qué hace:
 *     Dibuja un grano estático detrás del globo.
 * Recibe:
 *     settings: apariencia (intensidad y tamaño).
 * Devuelve:
 *     La capa de grano.
 * Por qué existe:
 *     Es un detalle de diseño del alumno; no cubre paneles ni el globo (G17).
 */
export function Grain({ settings: s }: { settings: Appearance }) {
  const url = useMemo(() => (s.grainOpacity > 0 ? makeNoiseUrl(s.bgColor, s.grainOpacity) : null), [s.bgColor, s.grainOpacity]);
  if (!url) return null;
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden" aria-hidden>
      <div
        className="absolute inset-0"
        style={{ backgroundImage: `url(${url})`, backgroundSize: `${TILE * s.grainSize}px`, imageRendering: 'pixelated' }}
      />
    </div>
  );
}
