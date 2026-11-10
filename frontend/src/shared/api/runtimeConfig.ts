import type { AppConfig } from '@/shared/lib/validateConfig';

let current: AppConfig | null = null;

/**
 * Qué hace:
 *     Guarda la configuración ya validada para el resto de módulos.
 * Recibe:
 *     config: la configuración válida cargada por `ConfigGate`.
 * Devuelve:
 *     Nada.
 * Por qué existe:
 *     El cliente, el hook de datos y el origen de datos leen la misma config cargada (G15).
 */
export function setConfig(config: AppConfig): void {
  current = config;
}

/**
 * Qué hace:
 *     Devuelve la configuración cargada.
 * Recibe:
 *     Nada.
 * Devuelve:
 *     La configuración válida; lanza error si aún no se cargó (no debería ocurrir: `ConfigGate` no monta el panel antes).
 * Por qué existe:
 *     Evita leer valores por defecto inventados si la carga falló.
 */
export function getConfig(): AppConfig {
  if (current === null) throw new Error('La configuración aún no está cargada.');
  return current;
}
