import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import type { Appearance } from '@/shared/lib/appearance';
import { ND, formatCountry, formatDecimal, formatFixed, formatPlace, formatUtc } from '@/shared/lib/format';
import { colorForEvent } from '@/shared/lib/symbology';
import type { EventFeature } from '@/shared/types/contract';

export type SortKey = 'mag' | 'magType' | 'depth' | 'place' | 'time' | 'country' | 'status' | 'sig';

export const COLUMNS: { key: SortKey; label: string; align?: 'right'; text?: boolean }[] = [
  { key: 'mag', label: 'Mag.', align: 'right' },
  { key: 'magType', label: 'Tipo', text: true },
  { key: 'depth', label: 'Prof. (km)', align: 'right' },
  { key: 'place', label: 'Lugar', text: true },
  { key: 'time', label: 'Fecha (UTC)' },
  { key: 'country', label: 'País', text: true },
  { key: 'status', label: 'Estado', text: true },
  { key: 'sig', label: 'Sig.', align: 'right' },
];

/** Valor de ordenación de una columna; los nulos se agrupan siempre al final. */
function sortValue(e: EventFeature, key: SortKey): number | string | null {
  const p = e.properties;
  switch (key) {
    case 'mag': return p.mag;
    case 'magType': return p.magType;
    case 'depth': return e.geometry.coordinates[2];
    case 'place': return p.place;
    case 'time': return p.time;
    case 'country': return p.country_name;
    case 'status': return p.status;
    case 'sig': return p.sig;
  }
}

/**
 * Qué hace:
 *     Ordena los eventos por una columna; los nulos van siempre al final.
 * Recibe:
 *     events: lista. key: columna. dir: ascendente o descendente.
 * Devuelve:
 *     Una copia ordenada; no modifica la entrada.
 * Por qué existe:
 *     La tabla y la lista móvil comparten el mismo orden (G8).
 */
export function sortEvents(events: EventFeature[], key: SortKey, dir: 'asc' | 'desc'): EventFeature[] {
  const sign = dir === 'asc' ? 1 : -1;
  return [...events].sort((a, b) => {
    const x = sortValue(a, key);
    const y = sortValue(b, key);
    if (x === null && y === null) return 0;
    if (x === null) return 1;
    if (y === null) return -1;
    return (typeof x === 'string' ? x.localeCompare(y as string, 'es') : x - (y as number)) * sign;
  });
}

interface EventsTableProps {
  events: EventFeature[];
  selected: EventFeature | null;
  settings: Appearance;
  onSelect: (event: EventFeature | null) => void;
  onClose: () => void;
  className?: string;
  style?: CSSProperties;
}

/**
 * Qué hace:
 *     Muestra todos los campos del contrato en una tabla ordenable; pulsar una fila selecciona el evento.
 * Recibe:
 *     events, evento seleccionado, apariencia, onSelect, onClose y estilo opcional.
 * Devuelve:
 *     La tabla.
 * Por qué existe:
 *     Es la alternativa accesible al globo y al color (G8, G12).
 */
export function EventsTable({ events, selected, settings, onSelect, onClose, className = '', style }: EventsTableProps) {
  const [sort, setSort] = useState<{ key: SortKey; dir: 'asc' | 'desc' }>({ key: 'time', dir: 'desc' });
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  // Ordenar es presentación, no estadística.
  const rows = useMemo(() => sortEvents(events, sort.key, sort.dir), [events, sort]);

  const toggleSort = (key: SortKey, text?: boolean) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: text ? 'asc' : 'desc' }));

  return (
    <section
      aria-label="Tabla de eventos"
      style={style}
      className={`flex flex-col bg-gradient-to-r from-hud-bg via-hud-bg/90 to-transparent text-xs [text-shadow:0_1px_4px_#000] ${className}`}
    >
      <div className="mb-2 flex items-baseline justify-between text-[11px] uppercase tracking-[0.2em]">
        <span className="text-hud-accent">Todos los eventos</span>
        <span className="flex items-baseline gap-4">
          <span className="text-[10px] tracking-[0.12em] text-hud-dim">{events.length} eventos</span>
          <button ref={closeRef} onClick={onClose} className="text-hud-dim hover:text-hud-accent">
            Cerrar ✕
          </button>
        </span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full border-collapse text-left">
          <caption className="sr-only">
            Eventos sísmicos del periodo. Pulsa un encabezado para ordenar; pulsa una fila para ver su ficha.
          </caption>
          <thead className="sticky top-0 bg-hud-bg">
            <tr className="text-[10px] uppercase tracking-[0.12em] text-hud-dim">
              {COLUMNS.map((c) => (
                <th
                  key={c.key}
                  scope="col"
                  aria-sort={sort.key === c.key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
                  className={`whitespace-nowrap px-2 py-1.5 font-normal ${c.align === 'right' ? 'text-right' : ''}`}
                >
                  <button onClick={() => toggleSort(c.key, c.text)} className={sort.key === c.key ? 'text-hud-accent' : 'hover:text-hud-text'}>
                    {c.label}
                    {sort.key === c.key && <span aria-hidden>{sort.dir === 'asc' ? ' ▲' : ' ▼'}</span>}
                  </button>
                </th>
              ))}
              <th scope="col" className="px-2 py-1.5 font-normal">
                Enlace
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => {
              const p = e.properties;
              const isSel = selected?.id === e.id;
              return (
                <tr
                  key={e.id}
                  onClick={() => onSelect(e)}
                  aria-selected={isSel}
                  className={`cursor-pointer border-t border-hud-line/40 hover:bg-white/5 ${isSel ? 'bg-white/10 text-hud-accent' : ''}`}
                >
                  <td className="whitespace-nowrap px-2 py-1 text-right font-semibold tabular-nums">
                    <button
                      onClick={(ev) => {
                        ev.stopPropagation();
                        onSelect(e);
                      }}
                      className="inline-flex items-center gap-2"
                      aria-label={`Seleccionar evento de magnitud ${formatDecimal(p.mag)}, ${formatPlace(p.place)}`}
                    >
                      <span className="size-2 shrink-0" style={{ background: colorForEvent(e, settings.colorMode) }} aria-hidden />
                      {formatDecimal(p.mag)}
                    </button>
                  </td>
                  <td className="px-2 py-1 text-hud-dim">{p.magType ?? ND}</td>
                  <td className="px-2 py-1 text-right tabular-nums">{formatFixed(e.geometry.coordinates[2], 1)}</td>
                  <td className="px-2 py-1">
                    {formatPlace(p.place)}
                    {p.is_synthetic && <span className="ml-2 text-[9px] uppercase tracking-[0.12em] text-hud-dim">(sintético)</span>}
                  </td>
                  <td className="whitespace-nowrap px-2 py-1 tabular-nums text-hud-dim">{formatUtc(p.time)}</td>
                  <td className="whitespace-nowrap px-2 py-1">{formatCountry(p.country_name)}</td>
                  <td className="px-2 py-1 text-hud-dim">{p.status ?? ND}</td>
                  <td className="px-2 py-1 text-right tabular-nums">{p.sig == null ? ND : p.sig}</td>
                  <td className="px-2 py-1">
                    {p.url ? (
                      <a href={p.url} target="_blank" rel="noreferrer" onClick={(ev) => ev.stopPropagation()} className="text-hud-accent underline">
                        USGS
                      </a>
                    ) : (
                      ND
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
