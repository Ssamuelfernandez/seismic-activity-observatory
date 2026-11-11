import { validateConfig, type ConfigResult } from '@/shared/lib/validateConfig';

/**
 * Qué hace:
 *     Pide `/config.json` al servidor y lo valida.
 * Recibe:
 *     url: ruta del archivo (por defecto `/config.json`).
 * Devuelve:
 *     El resultado de `validateConfig`; si no se puede leer o no es JSON, `{ ok: false, field: 'config', … }`.
 * Por qué existe:
 *     El único I/O de la configuración; la validación es pura y está aparte (G15, FR-003).
 */
export async function loadConfig(url = '/config.json'): Promise<ConfigResult> {
  let raw: unknown;
  try {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return { ok: false, field: 'config', message: `no se pudo leer ${url} (HTTP ${res.status})` };
    raw = await res.json();
  } catch {
    return { ok: false, field: 'config', message: `${url} no existe o no es un JSON válido` };
  }
  return validateConfig(raw);
}
