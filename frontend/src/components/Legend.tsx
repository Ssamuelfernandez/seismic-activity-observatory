import type { Appearance } from '@/shared/lib/appearance';
import { formatDecimal } from '@/shared/lib/format';
import { DEPTH_CLASSES, MAG_LABELS, MAX_MAG, ND_GRAY, WARM_RAMP, heightFor } from '@/shared/lib/symbology';

const SAMPLE_MAGS = [2, 4, 6, 8];
/** Alto en píxeles del prisma de ejemplo de M 8. */
const SAMPLE_MAX_PX = 48;

const TITLE = 'mb-1.5 whitespace-nowrap text-[10px] uppercase tracking-[0.18em] text-hud-dim';

/**
 * Qué hace:
 *     Explica la simbología: largo = magnitud, color = profundidad (cinco clases con su rango y el gris ND), ondas y antigüedad.
 * Recibe:
 *     settings: apariencia. className: posición.
 * Devuelve:
 *     La leyenda.
 * Por qué existe:
 *     Sin leyenda el color y el largo no se pueden leer (G2, SC-005).
 */
export function Legend({ settings: s, className = '' }: { settings: Appearance; className?: string }) {
  const top = heightFor(MAX_MAG);

  const colorItems =
    s.colorMode === 'depth'
      ? DEPTH_CLASSES.map((c) => ({ key: c.range, color: c.color, label: c.range, sub: '' }))
      : s.colorMode === 'mag'
        ? WARM_RAMP.map((c, i) => ({ key: c, color: c, label: `M ${MAG_LABELS[i]}`, sub: '' }))
        : [];

  return (
    <div className={`pointer-events-none w-80 text-xs [text-shadow:0_1px_4px_#000] ${className}`}>
      <div className="text-[11px] uppercase tracking-[0.2em] text-hud-accent">Leyenda</div>

      <div className="mt-3 space-y-3">
        <div className="grid grid-cols-[auto_1fr] gap-x-5">
          <div>
            <div className={TITLE}>Largo · magnitud</div>
            <div className="flex items-end gap-3">
              {SAMPLE_MAGS.map((m) => (
                <div key={m} className="flex flex-col items-center gap-1">
                  <div
                    className="w-2.5 bg-gradient-to-t from-hud-text/50 to-hud-text"
                    style={{ height: `${(heightFor(m) / top) * SAMPLE_MAX_PX}px` }}
                  />
                  <span className="text-[10px] text-hud-dim">M{m}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className={TITLE}>
              {s.colorMode === 'depth' ? 'Color · profundidad' : s.colorMode === 'mag' ? 'Color · magnitud' : 'Color único'}
            </div>
            {colorItems.map((c) => (
              <div key={c.key} className="flex items-center gap-2 whitespace-nowrap py-px">
                <span className="size-2.5" style={{ background: c.color }} />
                <span>{c.label}</span>
                {c.sub && <span className="text-hud-dim">{c.sub}</span>}
              </div>
            ))}
            <div className="flex items-center gap-2 py-px text-hud-dim">
              <span className="size-2.5" style={{ background: ND_GRAY }} />
              ND
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="relative inline-flex size-4 shrink-0 items-center justify-center">
              <span className="absolute size-4 rounded-full border border-hud-accent/40" />
              <span className="size-2 rounded-full border border-hud-accent" />
            </span>
            <span className="text-hud-dim">
              Ondas desde M ≥ {formatDecimal(s.ringMinMag)}
              {s.ringBySize ? ' · radio según magnitud' : ''}
            </span>
          </div>
          {s.fadeByAge && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-hud-dim">ahora</span>
              <span className="h-1.5 flex-1 bg-gradient-to-r from-hud-text to-hud-text/25" />
              <span className="text-[10px] text-hud-dim">{s.fadeHours} h</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
