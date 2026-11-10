import { useEffect, useRef, useState } from 'react';
import { useCountries } from '@/shared/hooks/useCountries';
import { NO_COUNTRY_TEXT } from '@/shared/lib/format';
import { useFilters } from '@/store/filters';
import { FiltersPanel } from './FiltersPanel';

const PERIODS: Record<number, string> = { 1: '1 h', 6: '6 h', 24: '24 h', 168: '7 días', 720: '30 días', 8760: '1 año' };

const Chevron = ({ open }: { open: boolean }) => (
  <svg viewBox="0 0 24 24" className={`size-3.5 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M6 9l6 6 6-6" />
  </svg>
);

/**
 * Qué hace:
 *     Muestra una línea con los filtros aplicados que al pulsarla despliega el panel de filtros.
 * Recibe:
 *     variant: diseño de escritorio o móvil.
 * Devuelve:
 *     La barra con su panel desplegable.
 * Por qué existe:
 *     Da acceso a los filtros sin ocupar espacio sobre el globo (G6).
 */
export function FiltersBar({ variant = 'desktop' }: { variant?: 'desktop' | 'mobile' }) {
  const mobile = variant === 'mobile';
  const f = useFilters();
  const countries = useCountries();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    window.addEventListener('pointerdown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('pointerdown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const countryName = !f.country
    ? 'Todos los países'
    : f.country === 'none'
      ? NO_COUNTRY_TEXT
      : (countries.find((c) => c.id.toLowerCase() === f.country.toLowerCase())?.name ?? f.country);
  const period = f.mode === 'replay' ? '2025' : f.hours === 0 ? (f.dateFrom && f.dateTo ? `${f.dateFrom} → ${f.dateTo} UTC` : 'Fechas…') : (PERIODS[f.hours] ?? `${f.hours} h`);
  const parts = [
    f.mode === 'live' ? 'En vivo' : 'Reproducción',
    period,
    f.minMag > 0 ? `Mag. ≥ ${f.minMag}` : 'Mag. todas',
    countryName,
  ];

  return (
    <div ref={rootRef} className={mobile ? 'pointer-events-none min-w-0 flex-1' : 'pointer-events-none relative'}>
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="Filtros y tipo de datos"
        className={
          mobile
            ? 'pointer-events-auto flex w-full items-center justify-between gap-2 px-1 py-2.5 text-[11px] uppercase tracking-[0.08em] text-hud-dim'
            : 'pointer-events-auto mx-auto flex max-w-full items-center gap-3 px-3 py-1.5 text-[11px] uppercase tracking-[0.1em] text-hud-dim transition-colors [text-shadow:0_1px_4px_#000] hover:text-hud-text'
        }
      >
        {mobile ? (
          // Móvil: dos líneas (modo · periodo · magnitud / país) para que no se corte nada.
          <span className="flex min-w-0 flex-1 flex-col items-start gap-0.5 text-left leading-tight">
            <span className="flex max-w-full flex-wrap items-center gap-x-1.5 gap-y-0.5">
              <span className={f.mode === 'replay' ? 'text-hud-accent' : 'text-hud-text'}>{parts[0]}</span>
              <span className="text-hud-line-strong">·</span>
              <span>{parts[1]}</span>
              <span className="text-hud-line-strong">·</span>
              <span>{parts[2]}</span>
            </span>
            <span className="max-w-full truncate text-[10px] tracking-[0.06em]">{parts[3]}</span>
          </span>
        ) : (
          <span className="flex min-w-0 items-center gap-2 whitespace-nowrap">
            {parts.map((p, i) => (
              <span key={i} className="flex min-w-0 items-center gap-2">
                {i > 0 && <span className="text-hud-line-strong">·</span>}
                <span className={`truncate ${i === 0 && f.mode === 'replay' ? 'text-hud-accent' : ''}`}>{p}</span>
              </span>
            ))}
          </span>
        )}
        <span className={open ? 'text-hud-accent' : ''}>
          <Chevron open={open} />
        </span>
      </button>
      {open && (
        <div
          className={
            mobile
              ? 'pointer-events-auto absolute inset-x-0 top-full z-40 max-h-[80dvh] overflow-y-auto border-b border-hud-line bg-hud-panel p-4 shadow-lg shadow-black/60'
              : 'pointer-events-auto absolute left-0 right-0 top-full z-20 mt-1 border border-hud-line bg-hud-panel/95 p-4 shadow-lg shadow-black/60 backdrop-blur-sm'
          }
        >
          <FiltersPanel />
        </div>
      )}
    </div>
  );
}
