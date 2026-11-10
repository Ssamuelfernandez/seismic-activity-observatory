import { useMemo } from 'react';
import type { Appearance } from '@/shared/lib/appearance';
import { formatDecimal, formatPlace } from '@/shared/lib/format';
import { colorForEvent } from '@/shared/lib/symbology';
import type { EventFeature } from '@/shared/types/contract';

/** Cuántos eventos recientes se listan. */
const MAX_ROWS = 12;

interface RecentEventsProps {
  events: EventFeature[];
  selected: EventFeature | null;
  /** Ajustes visuales: el color de cada fila debe coincidir con el del globo. */
  settings: Appearance;
  onSelect: (event: EventFeature | null) => void;
  /** Abre la tabla con todos los eventos. */
  onShowAll: () => void;
  /** No hay lectura de la API (error): no se muestra «0 eventos». */
  unavailable?: boolean;
  className?: string;
}

/**
 * Qué hace:
 *     Lista los eventos más recientes, de más nuevo a más antiguo; un clic equivale a pinchar su pilar.
 * Recibe:
 *     events, selected, settings, onSelect, onShowAll, unavailable y className.
 * Devuelve:
 *     La lista flotante con el acceso a la tabla.
 * Por qué existe:
 *     Da una lectura rápida de lo último que ha pasado (G2, G8).
 */
export function RecentEvents({ events, selected, settings, onSelect, onShowAll, unavailable = false, className = '' }: RecentEventsProps) {
  // Ordenar por fecha es presentación, no estadística.
  const recent = useMemo(
    () => [...events].sort((a, b) => b.properties.time - a.properties.time).slice(0, MAX_ROWS),
    [events],
  );
  const colorFor = (e: EventFeature) => colorForEvent(e, settings.colorMode);

  return (
    <div className={`flex flex-col text-xs [text-shadow:0_1px_4px_#000] ${className}`}>
      <div className="mb-2 flex items-baseline justify-between text-[11px] uppercase tracking-[0.2em]">
        <span className="text-hud-accent">Eventos recientes</span>
        <span className="flex items-baseline gap-3 text-[10px] tracking-[0.12em] text-hud-dim">
          {unavailable ? 'Sin datos' : `${recent.length} de ${events.length}`}
          <button onClick={onShowAll} className="uppercase text-hud-accent underline-offset-2 hover:underline">
            Ver todos
          </button>
        </span>
      </div>
      <ul className="min-h-0 overflow-y-auto">
        {recent.map((e) => (
          <li key={e.id}>
            <button
              onClick={() => onSelect(e)}
              className={`flex w-full items-center gap-2 py-1 text-left hover:bg-white/5 ${selected?.id === e.id ? 'text-hud-accent' : ''}`}
            >
              <span className="size-2 shrink-0" style={{ background: colorFor(e) }} />
              <span className="w-10 shrink-0 font-semibold">{formatDecimal(e.properties.mag)}</span>
              <span className="truncate text-hud-dim">{formatPlace(e.properties.place)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
