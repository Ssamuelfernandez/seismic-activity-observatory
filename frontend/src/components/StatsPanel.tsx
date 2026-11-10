import { useState, type ReactNode } from 'react';
import type { ApiError } from '@/shared/api/client';
import { NO_COUNTRY_TEXT, formatDecimal, formatFixed, formatUtc, formatUtcTime } from '@/shared/lib/format';
import type { Histogram, HistogramBin, StatsResponse } from '@/shared/types/contract';

interface StatsPanelProps {
  stats: StatsResponse | null;
  error: ApiError | null;
}

const LABEL = 'text-[10px] uppercase tracking-[0.18em] text-hud-dim';

/** Bloque con título en naranja y una línea fina que se desvanece; plegable. Sin caja ni bordes. */
function Block({ title, unit, defaultOpen = true, children }: { title: string; unit?: string; defaultOpen?: boolean; children: ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section>
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 text-[11px] uppercase tracking-[0.2em] text-hud-accent"
      >
        <span className="whitespace-nowrap">{title}</span>
        {unit && <span className="whitespace-nowrap normal-case tracking-normal text-hud-dim">({unit})</span>}
        <span className="h-px flex-1 bg-gradient-to-r from-hud-line-strong/70 to-transparent" />
        <span className="text-hud-dim">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="mt-3">{children}</div>}
    </section>
  );
}

/** Etiqueta compacta de un tramo: `<3`, `3–4` o `≥7` (límite inferior inclusivo, superior exclusivo). */
function binLabel(b: HistogramBin): string {
  if (b.lower === null) return `<${formatDecimal(b.upper)}`;
  if (b.upper === null) return `≥${formatDecimal(b.lower)}`;
  return `${formatDecimal(b.lower)}–${formatDecimal(b.upper)}`;
}

/** Histograma en columnas: recuento sobre cada barra y el tramo debajo. Solo escala los recuentos de la API. */
function Columns({ h }: { h: Histogram }) {
  const max = Math.max(1, ...h.bins.map((b) => b.count));
  return (
    <>
      <div className="flex h-24 items-stretch gap-1">
        {h.bins.map((b) => (
          <div key={binLabel(b)} className="flex flex-1 flex-col">
            <span className="h-3 text-center text-[9px] tabular-nums text-hud-dim">{b.count > 0 ? b.count : ''}</span>
            <div className="flex flex-1 items-end">
              <div
                className={`w-full ${b.count > 0 ? 'bg-gradient-to-t from-hud-accent/30 to-hud-accent' : 'bg-white/10'}`}
                style={{ height: b.count > 0 ? `${Math.max(3, (b.count / max) * 100)}%` : '1px' }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-1 flex gap-1">
        {h.bins.map((b) => (
          <span key={binLabel(b)} className="flex-1 text-center text-[9px] text-hud-dim">
            {binLabel(b)}
          </span>
        ))}
      </div>
      <p className="mt-1 text-[10px] text-hud-dim">Sin valor: {h.no_value}</p>
    </>
  );
}

/**
 * Qué hace:
 *     Presenta las estadísticas tal como las entrega la API: totales, por país, por hora, distribuciones y comparación.
 * Recibe:
 *     stats y error de la API.
 * Devuelve:
 *     El panel en columnas.
 * Por qué existe:
 *     El frontend no calcula estadísticas, solo las muestra (G3, G4, G5; constitución §17).
 */
export function StatsPanel({ stats, error }: StatsPanelProps) {
  if (error && !stats) {
    return <p className="text-xs text-hud-bad [text-shadow:0_1px_4px_#000]">{error.message}</p>;
  }
  if (!stats) {
    return <p className="text-xs text-hud-dim [text-shadow:0_1px_4px_#000]">Cargando estadísticas…</p>;
  }

  const c = stats.comparison;
  const buckets = stats.by_hour.buckets;
  const maxHour = Math.max(1, ...buckets.map((b) => b.count));
  const countries = stats.by_country.items.slice(0, 6);
  const maxCountry = Math.max(1, ...countries.map((i) => i.count));

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(13rem,1fr))] gap-x-10 gap-y-8 text-xs [text-shadow:0_1px_4px_#000]">
      <Block title="Estadísticas">
        <div className="text-5xl font-semibold leading-none text-hud-accent">{stats.total}</div>
        <div className={`mt-2 ${LABEL}`}>eventos en el periodo</div>
        <p className="mt-1 text-[10px] text-hud-dim">
          {formatUtc(stats.period.start)} → {formatUtc(stats.period.end)}
        </p>
        {error && <p className="mt-1 text-[10px] text-hud-bad">Última actualización fallida: {error.message}</p>}
      </Block>

      <Block title="Por hora · UTC" unit={stats.by_hour.unit}>
        <div className="flex h-20 items-end gap-[3px]">
          {buckets.map((b, i) => (
            <div
              key={b.hour_start}
              className={`flex-1 bg-gradient-to-t from-hud-accent/30 to-hud-accent ${i === buckets.length - 1 ? 'opacity-50' : ''}`}
              style={{ height: `${Math.max(3, (b.count / maxHour) * 100)}%` }}
              title={`${formatUtc(b.hour_start)}: ${b.count}`}
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between text-[9px] tabular-nums text-hud-dim">
          <span>{formatUtcTime(buckets[0].hour_start)}</span>
          <span>máx. {maxHour}</span>
          <span>{formatUtcTime(buckets[buckets.length - 1].hour_start)}</span>
        </div>
        <p className="mt-1 text-[10px] text-hud-dim">La última barra (más tenue) puede estar incompleta.</p>
      </Block>

      <Block title="Por país" unit={stats.by_country.unit}>
        <ul className="space-y-2">
          {countries.map((i) => (
            <li key={i.country_id ?? 'none'} title={i.subregion ?? undefined}>
              <div className="flex justify-between gap-3">
                <span className={`truncate ${i.country_id ? 'text-hud-text' : 'text-hud-dim'}`}>{i.country_name ?? NO_COUNTRY_TEXT}</span>
                <span className="tabular-nums">{i.count}</span>
              </div>
              <div className="mt-1 h-[3px] bg-white/10">
                <div
                  className={`h-full ${i.country_id ? 'bg-hud-accent' : 'bg-hud-dim'}`}
                  style={{ width: `${(i.count / maxCountry) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
        {stats.by_country.items.length > countries.length && (
          <p className="mt-2 text-[10px] text-hud-dim">+{stats.by_country.items.length - countries.length} países más</p>
        )}
      </Block>

      <Block title="Magnitud" unit={stats.histograms.magnitude.unit}>
        <Columns h={stats.histograms.magnitude} />
      </Block>

      <Block title="Profundidad" unit={stats.histograms.depth.unit}>
        <Columns h={stats.histograms.depth} />
      </Block>

      <Block title="Últimas 24 h vs 2025" unit={c?.unit}>
        {c ? (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-2xl font-semibold leading-none">{c.n_recent}</div>
                <div className={`mt-1.5 ${LABEL}`}>Últimas 24 h · M ≥ {formatDecimal(c.min_mag_applied)}</div>
              </div>
              <div>
                <div className="text-2xl font-semibold leading-none">{formatFixed(c.daily_mean_2025)}</div>
                <div className={`mt-1.5 ${LABEL}`}>Media diaria 2025</div>
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-3xl font-semibold leading-none text-hud-accent">
                {c.variation_pct === null ? 'ND' : `${formatFixed(c.variation_pct)} %`}
              </span>
              <span className="text-[11px] text-hud-dim">{formatFixed(c.diff_abs)} eventos / día</span>
            </div>
            <p className="mt-3 text-[10px] leading-snug text-hud-dim">
              {c.n_2025} eventos en 2025 (el histórico solo tiene M ≥ 4).
            </p>
            <p className="mt-1 text-[10px] leading-snug text-hud-dim">
              Fórmula: diferencia = n_recent − media diaria 2025; variación = diferencia / media diaria 2025 × 100.
            </p>
            {c.recent_incomplete && (
              <p className="mt-1 text-[10px] leading-snug text-hud-accent">
                Periodo reciente incompleto: USGS puede retrasar datos recientes.
              </p>
            )}
          </>
        ) : (
          <p className="text-hud-dim">No disponible en modo reproducción.</p>
        )}
      </Block>
    </div>
  );
}
