import type { ReactNode } from 'react';

interface AppShellProps {
  /** Zona principal (el globo). */
  children: ReactNode;
  /** Panel lateral (ficha del evento); opcional. */
  side?: ReactNode;
}

/**
 * Qué hace:
 *     Marco HUD: zona central para el globo y panel lateral, sin cabecera.
 * Recibe:
 *     children: contenido central. side: columna lateral opcional.
 * Devuelve:
 *     El marco con ambas zonas.
 * Por qué existe:
 *     Separa la maqueta de escritorio del contenido (G17).
 */
export function AppShell({ children, side }: AppShellProps) {
  return (
    <div className="flex h-full flex-col bg-hud-bg text-hud-text">
      <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1">{children}</main>
        {side && (
          <aside className="w-80 shrink-0 border-l border-hud-line bg-hud-panel">{side}</aside>
        )}
      </div>
    </div>
  );
}
