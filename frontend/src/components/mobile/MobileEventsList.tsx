import { useMemo, useState } from 'react';
import type { Appearance } from '@/shared/lib/appearance';
import { ND, formatCountry, formatDecimal, formatFixed, formatPlace, formatUtc } from '@/shared/lib/format';
import { colorForEvent } from '@/shared/lib/symbology';
import type { EventFeature } from '@/shared/types/contract';
import { COLUMNS, sortEvents, type SortKey } from '../EventsTable';

/**
 * Qué hace:
 *     Muestra una tarjeta por evento con todos los campos del contrato, ordenable, sin scroll horizontal.
 * Recibe:
 *     events, evento seleccionado, apariencia y onSelect.
 * Devuelve:
 *     La lista de tarjetas.
 * Por qué existe:
 *     Es la alternativa a la tabla en pantallas estrechas (G8, G17).
 */
export function MobileEventsList({
  events,
  selected,
  settings,
  onSelect,
  onClose,
}: {
  events: EventFeature[];
  selected: EventFeature | null;
  settings: Appearance;
  onSelect: (event: EventFeature | null) => void;
  onClose: () => void;
}) {
  const [key, setKey] = useState<SortKey>('time');
  const [dir, setDir] = useState<'asc' | 'desc'>('desc');
  const rows = useMemo(() => sortEvents(events, key, dir), [events, key, dir]);

  return (
    <section aria-label="Todos los eventos" className="absolute inset-0 z-30 flex flex-col bg-hud-bg text-xs">
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-hud-line px-3 py-2">
        <span className="text-[11px] uppercase tracking-[0.15em] text-hud-accent">Todos · {events.length}</span>
        <button onClick={onClose} className="px-2 py-1 text-[11px] uppercase tracking-[0.1em] text-hud-dim">
          Cerrar ✕
        </button>
      </div>
      <div className="flex shrink-0 items-center gap-2 border-b border-hud-line px-3 py-2 text-[11px] text-hud-dim">
        <label htmlFor="mobile-sort">Ordenar por</label>
        <select
          id="mobile-sort"
          value={key}
          onChange={(e) => setKey(e.target.value as SortKey)}
          className="min-w-0 flex-1 border border-hud-line bg-hud-panel px-2 py-1.5 text-xs text-hud-text"
        >
          {COLUMNS.map((c) => (
            <option key={c.key} value={c.key}>
              {c.label}
            </option>
          ))}
        </select>
        <button
          onClick={() => setDir(dir === 'asc' ? 'desc' : 'asc')}
          aria-label={dir === 'asc' ? 'Orden ascendente' : 'Orden descendente'}
          className="border border-hud-line px-3 py-1.5 text-hud-text"
        >
          {dir === 'asc' ? '▲' : '▼'}
        </button>
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto">
        {rows.map((e) => {
          const p = e.properties;
          const isSel = selected?.id === e.id;
          return (
            <li key={e.id} className={`border-b border-hud-line/40 ${isSel ? 'bg-white/10' : ''}`}>
              <button onClick={() => onSelect(e)} className="block w-full px-3 pb-1 pt-2.5 text-left">
                <span className="flex items-center gap-2">
                  <span className="size-2.5 shrink-0" style={{ background: colorForEvent(e, settings.colorMode) }} aria-hidden />
                  <span className={`font-semibold ${isSel ? 'text-hud-accent' : ''}`}>{formatDecimal(p.mag)}</span>
                  <span className="text-hud-dim">{p.magType ?? ND}</span>
                  <span className="min-w-0 flex-1 truncate">{formatPlace(p.place)}</span>
                </span>
                <span className="mt-1 block pl-[18px] text-[11px] leading-snug text-hud-dim">
                  {formatUtc(p.time)} · Prof. {formatFixed(e.geometry.coordinates[2], 1)} km
                  <br />
                  {formatCountry(p.country_name)} · Estado: {p.status ?? ND} · Sig.: {p.sig == null ? ND : p.sig}
                  {p.is_synthetic && ' · (sintético)'}
                </span>
              </button>
              {p.url && (
                <a href={p.url} target="_blank" rel="noreferrer" className="mb-2 ml-[30px] inline-block text-[11px] text-hud-accent underline">
                  Ver en USGS
                </a>
              )}
              {!p.url && <div className="pb-1" />}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
