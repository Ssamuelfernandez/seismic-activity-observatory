import type { ReactNode } from 'react';

/**
 * Qué hace:
 *     Pinta una fila «clave … valor».
 * Recibe:
 *     k: clave. v: valor.
 * Devuelve:
 *     La fila.
 * Por qué existe:
 *     Evita repetir el mismo marcado en ficha y estado (G12).
 */
export const Row = ({ k, v }: { k: string; v: ReactNode }) => (
  <div className="flex justify-between gap-3 py-0.5 text-xs">
    <span className="text-hud-dim">{k}</span>
    <span className="text-right text-hud-text">{v}</span>
  </div>
);
