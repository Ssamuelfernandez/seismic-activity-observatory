/** Configuración en tiempo de ejecución del panel (`public/config.json`; sin secretos). */
export interface AppConfig {
  /** `api`: datos de la API real; `mock`: servidor simulado (solo desarrollo y pruebas). */
  mode: 'mock' | 'api';
  /** URL base de la API: `/api` (proxy) o una URL absoluta. */
  apiBaseUrl: string;
  /** Segundos entre refrescos de los datos. */
  refreshSeconds: number;
  /** Tiempo máximo de cada petición, en milisegundos. */
  timeoutMs: number;
}

/** Resultado de validar: la configuración o el campo que falla con su motivo. */
export type ConfigResult = { ok: true; config: AppConfig } | { ok: false; field: string; message: string };

const isPositiveInt = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && v > 0;

/**
 * Qué hace:
 *     Valida los cuatro campos de la configuración y devuelve el primero que falla.
 * Recibe:
 *     raw: el JSON leído de `config.json` (sin tipar). Los campos desconocidos se ignoran.
 * Devuelve:
 *     `{ ok: true, config }` o `{ ok: false, field, message }`.
 * Por qué existe:
 *     Un `config.json` mal escrito debe mostrar un error que nombre el campo, no un panel roto (G15, FR-004).
 */
export function validateConfig(raw: unknown): ConfigResult {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
    return { ok: false, field: 'config', message: 'el archivo debe ser un objeto JSON' };
  }
  const c = raw as Record<string, unknown>;
  if (c.mode !== 'mock' && c.mode !== 'api') {
    return { ok: false, field: 'mode', message: 'debe ser "mock" o "api"' };
  }
  if (typeof c.apiBaseUrl !== 'string') {
    return { ok: false, field: 'apiBaseUrl', message: 'debe ser un texto' };
  }
  if (c.mode === 'api' && !/^(\/|https?:\/\/)/.test(c.apiBaseUrl)) {
    return { ok: false, field: 'apiBaseUrl', message: 'en modo api no puede estar vacío y debe empezar por "/", "http://" o "https://"' };
  }
  if (!isPositiveInt(c.refreshSeconds)) {
    return { ok: false, field: 'refreshSeconds', message: 'debe ser un entero mayor que 0' };
  }
  if (!isPositiveInt(c.timeoutMs)) {
    return { ok: false, field: 'timeoutMs', message: 'debe ser un entero mayor que 0' };
  }
  return { ok: true, config: { mode: c.mode, apiBaseUrl: c.apiBaseUrl, refreshSeconds: c.refreshSeconds, timeoutMs: c.timeoutMs } };
}
