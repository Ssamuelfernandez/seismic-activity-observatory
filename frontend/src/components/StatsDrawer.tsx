import { useEffect, useState } from 'react';
import type { ApiError } from '@/shared/api/client';
import type { StatsResponse } from '@/shared/types/contract';
import { StatsPanel } from './StatsPanel';

/** Flechita (chevron) que apunta hacia arriba; se gira al abrir. */
const Chevron = ({ open }: { open: boolean }) => (
  <svg
    viewBox="0 0 24 24"
    className={`size-4 transition-transform duration-500 ${open ? 'rotate-180' : ''}`}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M6 15l6-6 6 6" />
  </svg>
);

/**
 * Qué hace:
 *     Cajón inferior que muestra las estadísticas al desplegarlo.
 * Recibe:
 *     stats: respuesta de /api/estadisticas o null. error: error de la API o null.
 * Devuelve:
 *     El cajón.
 * Por qué existe:
 *     Muestra las cifras de la API sin ocupar espacio sobre el globo (G3, G4, G5b).
 */
export function StatsDrawer({ stats, error, className = '' }: { stats: StatsResponse | null; error: ApiError | null; className?: string }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    // Cerrado, el cajón queda desplazado fuera de la pantalla por su propia altura; la flecha va pegada a su borde superior.
    <div
      className={`pointer-events-none absolute inset-x-0 bottom-0 transition-transform duration-500 ease-out ${open ? 'translate-y-0' : 'translate-y-full'} ${className}`}
    >
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label={open ? 'Ocultar estadísticas' : 'Mostrar estadísticas'}
        className="pointer-events-auto absolute -top-9 left-1/2 flex -translate-x-1/2 items-center gap-2 px-3 py-2 text-[11px] uppercase tracking-[0.2em] text-hud-dim transition-colors [text-shadow:0_1px_4px_#000] hover:text-hud-accent"
      >
        Estadísticas
        <Chevron open={open} />
      </button>

      <div className="pointer-events-auto max-h-[70vh] overflow-y-auto bg-gradient-to-t from-hud-bg via-hud-bg/90 to-transparent px-8 pb-8 pt-12">
        <StatsPanel stats={stats} error={error} />
      </div>
    </div>
  );
}
