import { useEffect, useRef, useState, type ReactNode } from 'react';
import type { ApiError } from '@/shared/api/client';
import { useNow } from '@/shared/hooks/useNow';
import { formatAge, formatUtc } from '@/shared/lib/format';
import { ingestionLag } from '@/shared/lib/feedHealth';
import type { HealthResponse, Metadata, Period } from '@/shared/types/contract';

interface FeedStatusProps {
  metadata: Metadata | null;
  /** Error al pedir los eventos, si lo hay. */
  error: ApiError | null;
  health: HealthResponse | null;
  healthError: ApiError | null;
  /** Periodo efectivo de las estadísticas, si ya hay. */
  period: Period | null;
  /** Última vez que esta pantalla recibió eventos correctamente (ms), o 0. */
  updatedAt: number;
  /** Hay eventos marcados como sintéticos. */
  hasSynthetic: boolean;
  className?: string;
  /** `mobile`: indicador compacto y detalles a todo el ancho, sobre fondo opaco. */
  variant?: 'desktop' | 'mobile';
}

const Row = ({ k, v }: { k: string; v: ReactNode }) => (
  <div className="flex justify-between gap-4 py-0.5 text-xs">
    <span className="text-hud-dim">{k}</span>
    <span className="text-right text-hud-text">{v}</span>
  </div>
);

const GroupTitle = ({ children }: { children: ReactNode }) => (
  <div className="mb-1 mt-3 text-[10px] uppercase tracking-[0.18em] text-hud-dim first:mt-0">{children}</div>
);

/** Llave inglesa (trazo, 24×24). */
const WrenchIcon = () => (
  <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
  </svg>
);

/**
 * Qué hace:
 *     Resume el estado del feed (punto verde o rojo, modo, última ingesta) y abre un desplegable con el detalle.
 * Recibe:
 *     metadata, error, health, healthError, period, updatedAt, hasSynthetic y variante de diseño.
 * Devuelve:
 *     La línea de estado con su desplegable.
 * Por qué existe:
 *     El usuario debe distinguir la última consulta del panel de la última ingesta (G7, G12).
 */
export function FeedStatus({ metadata, error, health, healthError, period, updatedAt, hasSynthetic, className = '', variant = 'desktop' }: FeedStatusProps) {
  const mobile = variant === 'mobile';
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const now = useNow(15_000);

  // El desplegable se cierra al pulsar fuera o con Escape.
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

  // Datos desactualizados: lo decide el frontend con la constante STALE_THRESHOLD_SECONDS (la API no lo calcula).
  const { lagSeconds: lag, stale } = ingestionLag(health, metadata?.mode);
  const problem = Boolean(error || healthError || stale);
  const connecting = !problem && !health;

  const ingestion = health?.last_ingestion ?? metadata?.last_ingestion ?? null;
  const problemText = healthError ? 'Sin respuesta de la API' : error ? 'Error al pedir datos' : stale ? 'Datos desactualizados' : null;
  const mode = metadata ? (metadata.mode === 'live' ? 'Live' : 'Replay') : null;

  const dotClass = problem ? 'bg-hud-bad shadow-[0_0_8px_var(--color-hud-bad)]' : connecting ? 'bg-hud-dim animate-pulse' : 'bg-hud-ok shadow-[0_0_8px_var(--color-hud-ok)]';

  return (
    <div ref={rootRef} className={mobile ? `pointer-events-none ${className}` : `pointer-events-none relative w-max ${className}`}>
      {mobile ? (
        <div className="pointer-events-auto flex items-center gap-2 whitespace-nowrap text-[11px] uppercase tracking-[0.1em] text-hud-dim">
          <span className={`size-2.5 rounded-full ${dotClass}`} aria-hidden />
          <span className={problem ? 'text-hud-bad' : 'text-hud-accent'}>
            {mode ?? '…'}
            {problem ? ' · Aviso' : ''}
          </span>
          <button
            onClick={() => setOpen(!open)}
            aria-label="Más opciones del estado"
            aria-expanded={open}
            className={`grid size-9 place-items-center transition-colors ${open ? 'text-hud-accent' : ''}`}
          >
            <WrenchIcon />
          </button>
        </div>
      ) : (
      <div className="pointer-events-auto flex items-center justify-end gap-3 whitespace-nowrap text-[11px] uppercase tracking-[0.15em] text-hud-dim [text-shadow:0_1px_4px_#000]">
        <span className="flex items-center gap-2" title={problemText ?? (connecting ? 'Conectando…' : 'Todo correcto')}>
          Estado
          <span className={`size-2.5 rounded-full ${dotClass}`} />
        </span>
        {mode && (
          <>
            <span className="text-hud-line-strong">|</span>
            <span className="text-hud-accent">{mode}</span>
          </>
        )}
        <span className="text-hud-line-strong">|</span>
        <span className={problem ? 'text-hud-bad' : ''}>
          {problemText ?? (ingestion === null ? 'Sin ingesta' : `Última ingesta ${formatAge(now - ingestion)}`)}
        </span>
        <button
          onClick={() => setOpen(!open)}
          aria-label="Más opciones del estado"
          aria-expanded={open}
          className={`grid size-7 place-items-center transition-colors hover:text-hud-accent ${open ? 'text-hud-accent' : ''}`}
        >
          <WrenchIcon />
        </button>
      </div>
      )}

      {open && (
        <div
          className={
            mobile
              ? 'pointer-events-auto absolute inset-x-0 top-full z-40 max-h-[80dvh] overflow-y-auto border-b border-hud-line bg-hud-panel p-4 shadow-lg shadow-black/60'
              : 'pointer-events-auto absolute right-0 top-full z-20 mt-2 w-[24rem] border border-hud-line bg-hud-panel/95 p-4 shadow-lg shadow-black/60 backdrop-blur-sm'
          }
        >
          <GroupTitle>Conexión</GroupTitle>
          <Row
            k="API"
            v={healthError ? <span className="text-hud-bad">Sin respuesta</span> : health ? <span className="text-hud-ok">En línea</span> : '…'}
          />
          {error && <Row k="Eventos" v={<span className="text-hud-bad">{error.message}</span>} />}
          {stale && (
            <Row
              k="Ingesta"
              v={<span className="text-hud-bad">{lag === null ? 'Aún no hay ingesta' : `hace ${Math.round(lag / 60)} min (calculado en el panel)`}</span>}
            />
          )}
          <Row k="Última ingesta de USGS" v={ingestion === null ? 'ND' : formatUtc(ingestion, true)} />
          <Row k="Última consulta correcta" v={updatedAt ? formatUtc(updatedAt, true) : 'ND'} />
          <Row k="Respuesta generada" v={metadata ? formatUtc(metadata.generated, true) : 'ND'} />
          <Row k="Periodo" v={period ? `${formatUtc(period.start)} → ${formatUtc(period.end)}` : 'ND'} />

          <GroupTitle>Datos</GroupTitle>
          {metadata ? (
            <>
              <Row k="Mostrados" v={`${metadata.count} de ${metadata.total}`} />
              <Row k="Truncado" v={metadata.truncated ? 'Sí' : 'No'} />
              <Row k="Sin magnitud (excl.)" v={metadata.null_mag_excluded} />
              {hasSynthetic && <Row k="Sintéticos" v="Incluye datos de prueba" />}
            </>
          ) : (
            <p className="text-xs text-hud-dim">{error ? 'Sin datos' : 'Cargando…'}</p>
          )}

          <ul className="mt-3 space-y-1.5 border-t border-hud-line pt-3 text-[11px] leading-snug text-hud-dim">
            <li className="flex gap-2">
              <span aria-hidden>-</span>
              <span>
                <span className="text-hud-text">Ingesta:</span> la última vez que el servidor descargó datos de USGS. El «hace X min» de una ingesta atrasada se calcula en el panel (respuesta generada − última ingesta).
              </span>
            </li>
            <li className="flex gap-2">
              <span aria-hidden>-</span>
              <span>
                <span className="text-hud-text">Consulta:</span> la última vez que este panel recibió datos correctos del servidor. «Respuesta generada» es cuándo la preparó la API.
              </span>
            </li>
          </ul>
          <p className="mt-3 text-center text-[10px] uppercase tracking-[0.18em] text-hud-dim">Horas en UTC</p>
        </div>
      )}
    </div>
  );
}
