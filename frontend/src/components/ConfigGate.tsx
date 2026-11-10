import { useEffect, useState, type ReactNode } from 'react';
import { loadConfig } from '@/shared/api/loadConfig';
import { setConfig } from '@/shared/api/runtimeConfig';

type GateState = { status: 'loading' } | { status: 'ready' } | { status: 'error'; field: string; message: string };

/**
 * Qué hace:
 *     Carga y valida `config.json` antes de montar el panel; mientras tanto muestra «Cargando» y, si falla, el campo que falla.
 * Recibe:
 *     children: el panel, que solo se monta con la configuración válida.
 * Devuelve:
 *     El panel, el mensaje de carga o el mensaje de error.
 * Por qué existe:
 *     Un `config.json` inválido debe ser visible y nombrar el campo (G15, FR-004).
 */
export function ConfigGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GateState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    loadConfig().then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setConfig(result.config);
        setState({ status: 'ready' });
      } else {
        setState({ status: 'error', field: result.field, message: result.message });
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === 'ready') return <>{children}</>;
  return (
    <div className="flex h-full items-center justify-center bg-hud-bg p-6 text-hud-text">
      {state.status === 'loading' ? (
        <p className="text-[11px] uppercase tracking-[0.15em] text-hud-dim">Cargando configuración…</p>
      ) : (
        <div role="alert" className="max-w-md border border-hud-bad p-4 text-sm">
          <p className="mb-2 text-[11px] uppercase tracking-[0.15em] text-hud-bad">Configuración no válida</p>
          <p>
            Campo <code className="text-hud-accent">{state.field}</code>: {state.message}.
          </p>
          <p className="mt-2 text-[11px] text-hud-dim">Revisa public/config.json (o dist/config.json) y recarga la página.</p>
        </div>
      )}
    </div>
  );
}
