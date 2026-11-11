import { useState, type ReactNode } from 'react';
import { useCountries } from '@/shared/hooks/useCountries';
import { NO_COUNTRY_TEXT } from '@/shared/lib/format';
import { useFilters } from '@/store/filters';

const HOURS: [number, string][] = [[1, '1 h'], [6, '6 h'], [24, '24 h'], [168, '7 d'], [720, '30 d'], [8760, '1 año'], [0, 'Fechas']];
const MAGS: [number, string][] = [[0, 'Todas'], [2, '≥2'], [3, '≥3'], [4, '≥4'], [5, '≥5'], [6, '≥6']];
const MODES: ['live' | 'replay', string][] = [['live', 'En vivo'], ['replay', 'Reproducción']];

const DAY_MS = 86_400_000;
const isoDay = (ms: number) => new Date(ms).toISOString().slice(0, 10);

const LABEL = 'text-[10px] uppercase tracking-[0.15em] text-hud-dim';

/** Fila de filtro: etiqueta arriba y, debajo, botones de opción (la activa en naranja). */
function Chips<T extends string | number>({ label, options, value, onChange }: { label: string; options: [T, string][]; value: T; onChange: (v: T) => void }) {
  return (
    <div className="py-1.5" role="group" aria-label={label}>
      <div className={`mb-1 ${LABEL}`}>{label}</div>
      <div className="flex flex-wrap gap-1">
        {options.map(([v, l]) => (
          <button
            key={String(v)}
            onClick={() => onChange(v)}
            aria-pressed={v === value}
            className={`border px-2 py-0.5 text-[11px] transition-colors ${
              v === value ? 'border-hud-accent bg-hud-accent/15 text-hud-accent' : 'border-hud-line text-hud-dim hover:border-hud-line-strong hover:text-hud-text'
            }`}
          >
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Minúsculas y sin tildes, para buscar «mexico» y encontrar «México». */
const plain = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Selector de país con búsqueda: lista de paises.geojson más «Sin país asignado». Teclado: Tab recorre las opciones. */
function CountryPicker() {
  const country = useFilters((f) => f.country);
  const set = useFilters((f) => f.set);
  const countries = useCountries();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);

  const all = [{ id: 'none', name: NO_COUNTRY_TEXT }, ...countries];
  const selected = country ? (all.find((c) => c.id.toLowerCase() === country.toLowerCase()) ?? { id: country, name: country }) : null;
  const q = plain(query.trim());
  const options = q ? all.filter((c) => plain(c.name).includes(q) || c.id.toLowerCase().includes(q)) : all;

  const pick = (id: string) => {
    set({ country: id });
    setQuery('');
    setOpen(false);
  };

  return (
    <div className="py-1.5">
      <div className={`mb-1 ${LABEL}`}>País</div>
      {selected ? (
        <div className="flex items-center justify-between border border-hud-accent bg-hud-accent/15 px-2 py-0.5 text-[11px] text-hud-accent">
          <span>
            {selected.name}
            {selected.id !== 'none' && <span className="ml-2 text-hud-dim">{selected.id}</span>}
          </span>
          <button onClick={() => set({ country: '' })} aria-label="Quitar filtro de país" className="text-hud-dim hover:text-hud-text">
            ✕
          </button>
        </div>
      ) : (
        <div
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
          }}
        >
          <input
            className="w-full border-b border-hud-line bg-transparent py-0.5 text-xs text-hud-text outline-none placeholder:text-hud-dim/60 focus:border-hud-accent"
            placeholder="Todos · escribe para buscar…"
            value={query}
            onFocus={() => setOpen(true)}
            onChange={(e) => {
              setQuery(e.target.value);
              setOpen(true);
            }}
            aria-label="Buscar país"
          />
          {open && (
            <ul className="mt-1 max-h-36 overflow-y-auto border border-hud-line bg-hud-bg">
              {options.length === 0 && <li className="px-2 py-1 text-[11px] text-hud-dim">Sin resultados</li>}
              {options.map((c) => (
                <li key={c.id}>
                  <button onClick={() => pick(c.id)} className="flex w-full justify-between px-2 py-1 text-left text-[11px] text-hud-text hover:bg-white/10 focus:bg-white/10">
                    <span>{c.name}</span>
                    {c.id !== 'none' && <span className="text-hud-dim">{c.id}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

/** Dos fechas (UTC) para el periodo personalizado; el día final se incluye entero. */
function DateRange() {
  const { dateFrom, dateTo, set } = useFilters();
  const today = isoDay(Date.now());
  const invalid = !dateFrom || !dateTo || dateFrom > dateTo;
  const input = 'border border-hud-line bg-transparent px-1 py-0.5 text-[11px] text-hud-text outline-none [color-scheme:dark] focus:border-hud-accent';
  return (
    <div className="pb-1.5">
      <div className="flex flex-wrap items-center gap-2 text-[11px] text-hud-dim">
        <label className="flex items-center gap-1">
          Desde
          <input type="date" className={input} value={dateFrom} max={dateTo || today} onChange={(e) => set({ dateFrom: e.target.value })} />
        </label>
        <label className="flex items-center gap-1">
          Hasta
          <input type="date" className={input} value={dateTo} min={dateFrom} max={today} onChange={(e) => set({ dateTo: e.target.value })} />
        </label>
      </div>
      <p className={`mt-1 text-[10px] leading-snug ${invalid ? 'text-hud-bad' : 'text-hud-dim'}`}>
        {invalid ? 'Elige las dos fechas (la primera no puede ser posterior a la segunda); mientras tanto se usan las últimas 24 h.' : 'Fechas en UTC; el día final se incluye entero.'}
      </p>
    </div>
  );
}

const Title = ({ children }: { children: ReactNode }) => (
  <div className="mb-1 text-[10px] uppercase tracking-[0.18em] text-hud-dim">{children}</div>
);

/**
 * Qué hace:
 *     Edita los filtros compartidos (modo, periodo, magnitud mínima y país) en el store.
 * Recibe:
 *     Nada.
 * Devuelve:
 *     El panel de filtros.
 * Por qué existe:
 *     Un único estado de filtros para globo, tabla y estadísticas (G6; constitución §17).
 */
export function FiltersPanel() {
  const f = useFilters();
  const choosePeriod = (hours: number) => {
    // Al pasar a «Fechas» se propone una semana, para que ya sea un rango válido.
    if (hours === 0 && (!f.dateFrom || !f.dateTo)) f.set({ hours, dateFrom: isoDay(Date.now() - 7 * DAY_MS), dateTo: isoDay(Date.now()) });
    else f.set({ hours });
  };
  return (
    <div className="grid grid-cols-1 gap-x-8 lg:grid-cols-2">
      <div className="flex items-baseline justify-between lg:col-span-2">
        <Title>Filtros y tipo de datos</Title>
        <button onClick={f.reset} className="text-[10px] uppercase tracking-[0.12em] text-hud-dim hover:text-hud-accent">
          Restablecer
        </button>
      </div>
      <div>
        <Chips label="Modo" options={MODES} value={f.mode} onChange={(mode) => f.set({ mode })} />
        {f.mode === 'replay' ? (
          // En reproducción el periodo es fijo (2025, api.md §5): el selector queda desactivado.
          <div className="py-1.5" role="group" aria-label="Periodo">
            <div className={`mb-1 ${LABEL}`}>Periodo</div>
            <button disabled aria-disabled="true" className="cursor-not-allowed border border-hud-line px-2 py-0.5 text-[11px] text-hud-dim opacity-70">
              2025
            </button>
            <p className="mt-1 text-[10px] leading-snug text-hud-dim">La reproducción cubre todo 2025; el periodo no se puede cambiar.</p>
          </div>
        ) : (
          <Chips label="Periodo (hacia atrás desde ahora)" options={HOURS} value={f.hours} onChange={choosePeriod} />
        )}
        {f.mode === 'live' && f.hours === 0 && <DateRange />}
      </div>
      <div>
        <Chips label="Magnitud mínima" options={MAGS} value={f.minMag} onChange={(minMag) => f.set({ minMag })} />
        <CountryPicker />
      </div>
      <p className="mt-1 text-[10px] lg:col-span-2 leading-snug text-hud-dim">Se aplican al instante al globo, a la tabla y a las estadísticas.</p>
    </div>
  );
}
