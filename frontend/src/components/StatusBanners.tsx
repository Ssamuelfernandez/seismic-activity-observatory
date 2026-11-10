import { useState, type ReactNode } from 'react';
import type { ApiError } from '@/shared/api/client';
import { useNow } from '@/shared/hooks/useNow';
import { formatAge, formatUtc } from '@/shared/lib/format';
import { ingestionLag } from '@/shared/lib/feedHealth';
import type { HealthResponse, Metadata } from '@/shared/types/contract';

interface StatusBannersProps {
  metadata: Metadata | null;
  /** Error al pedir los eventos, si lo hay. */
  error: ApiError | null;
  health: HealthResponse | null;
  healthError: ApiError | null;
  /** Última vez que llegaron eventos correctamente (ms), o 0. */
  updatedAt: number;
  /** Hay una lectura de eventos (buena o antigua) en pantalla. */
  hasData: boolean;
  hasSynthetic: boolean;
  className?: string;
  /** `mobile`: una sola línea plegable («● Aviso +1»), sobre fondo opaco. */
  variant?: 'desktop' | 'mobile';
}

type Tone = 'info' | 'warn' | 'bad';

const TONE: Record<Tone, string> = {
  info: 'text-hud-accent',
  warn: 'text-hud-text',
  bad: 'text-hud-bad',
};

function Banner({ tone, title, children }: { tone: Tone; title: string; children?: ReactNode }) {
  return (
    <div role={tone === 'bad' ? 'alert' : 'status'} className={`flex items-start justify-center gap-2 px-3 py-1 text-center text-[11px] leading-snug [text-shadow:0_1px_4px_#000] ${TONE[tone]}`}>
      <span className="mt-[5px] size-1.5 shrink-0 rounded-full bg-hud-accent" aria-hidden />
      <span>
        <span className="font-semibold uppercase tracking-[0.15em]">{title}</span>
        {children && <span className="ml-2 text-hud-text">{children}</span>}
      </span>
    </div>
  );
}

/**
 * Qué hace:
 *     Muestra los avisos: reproducción, fallo de la API con la última lectura marcada como antigua, ingesta desactualizada y datos sintéticos.
 * Recibe:
 *     metadata, error, health, healthError, updatedAt, hasData, hasSynthetic y variante.
 * Devuelve:
 *     Los avisos que correspondan, o nada.
 * Por qué existe:
 *     Un error nunca debe presentarse como «0 eventos» (G7, G9, G10).
 */
export function StatusBanners({ metadata, error, health, healthError, updatedAt, hasData, hasSynthetic, className = '', variant = 'desktop' }: StatusBannersProps) {
  const now = useNow(15_000);
  const [open, setOpen] = useState(false);
  const { lagSeconds, stale } = ingestionLag(health, metadata?.mode);
  const backendDown = Boolean(healthError);

  const items: { key: string; tone: Tone; title: string; body: ReactNode }[] = [];
  if (metadata?.mode === 'replay') {
    items.push({ key: 'replay', tone: 'info', title: 'Modo reproducción', body: 'Datos históricos reproducidos, no son en vivo.' });
  }
  if (error && hasData) {
    items.push({
      key: 'old',
      tone: 'bad',
      title: 'Datos antiguos',
      body: `No se pudo actualizar (${error.message})${backendDown ? ' El backend no responde.' : ''} Se muestra la última lectura correcta, de ${formatAge(now - updatedAt)} (${formatUtc(updatedAt, true)}).`,
    });
  }
  if (error && !hasData) {
    items.push({
      key: 'nodata',
      tone: 'bad',
      title: 'Sin datos',
      body: `${error.message}${backendDown ? ' El backend no responde.' : ''} No significa que haya 0 eventos: simplemente no se han podido obtener.`,
    });
  }
  if (!error && backendDown) {
    items.push({ key: 'backend', tone: 'bad', title: 'Backend sin respuesta', body: 'No responde al comprobar su estado; los datos mostrados pueden no estar al día.' });
  }
  if (stale) {
    items.push({
      key: 'stale',
      tone: 'bad',
      title: 'Datos desactualizados',
      body: lagSeconds === null ? 'Aún no hay ninguna ingesta de USGS.' : `La última ingesta de USGS iba ${Math.round(lagSeconds / 60)} min por detrás de la respuesta.`,
    });
  }
  if (hasSynthetic) {
    items.push({ key: 'synthetic', tone: 'warn', title: 'Datos sintéticos', body: 'Datos de prueba, no son sismos reales.' });
  }

  if (variant === 'mobile') {
    if (items.length === 0) return null;
    return (
      <div className={`pointer-events-auto border-b border-hud-line bg-hud-panel ${className}`}>
        <button
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          className={`flex w-full items-center gap-2 px-3 py-2 text-left text-[11px] uppercase tracking-[0.1em] ${items.some((i) => i.tone === 'bad') ? 'text-hud-bad' : 'text-hud-accent'}`}
        >
          <span className="size-1.5 shrink-0 rounded-full bg-hud-accent" aria-hidden />
          <span className="min-w-0 flex-1 truncate font-semibold">{items[0].title}</span>
          {items.length > 1 && <span className="text-hud-dim">+{items.length - 1}</span>}
          <span className="text-hud-dim" aria-hidden>
            {open ? '▴' : '▾'}
          </span>
        </button>
        {open && (
          <div className="flex max-h-[50dvh] flex-col gap-2 overflow-y-auto pb-3">
            {items.map((i) => (
              <Banner key={i.key} tone={i.tone} title={i.title}>
                {i.body}
              </Banner>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`pointer-events-none flex max-w-xl flex-col gap-1.5 ${className}`}>
      {items.map((i) => (
        <Banner key={i.key} tone={i.tone} title={i.title}>
          {i.body}
        </Banner>
      ))}
    </div>
  );
}
