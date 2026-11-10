/** Texto de atribución (FR-025): fuentes y licencias de lo que muestra el panel. */
export const ATTRIBUTION_TEXT = 'Sismos: USGS · Fronteras: Natural Earth (dominio público) · Globo: react-globe.gl y three (MIT) · Sin textura';

/**
 * Qué hace:
 *     Línea fija de atribución de las fuentes y licencias, siempre visible y sin pulsar nada.
 * Recibe:
 *     variant: `desktop` (abajo a la derecha, por encima del cajón de estadísticas, sin tapar su flecha) o `mobile` (franja en el pie del diseño).
 * Devuelve:
 *     El elemento con el texto de `ATTRIBUTION_TEXT` a 11 px y color `hud-dim` (contraste alto sobre el fondo oscuro).
 * Por qué existe:
 *     USGS, Natural Earth, react-globe.gl y three exigen o piden atribución visible (G11, G14, FR-025, SC-010).
 */
export function Attribution({ variant = 'desktop', className = '' }: { variant?: 'desktop' | 'mobile'; className?: string }) {
  if (variant === 'mobile') {
    return (
      <p className={`shrink-0 border-t border-hud-line bg-hud-bg px-3 py-1 text-center text-[11px] leading-snug text-hud-dim ${className}`}>{ATTRIBUTION_TEXT}</p>
    );
  }
  // Escritorio: encima del cajón (z-30 > z-20) y sin recibir clics, así no tapa ni bloquea la flecha del cajón (centrada).
  return (
    <p className={`pointer-events-none absolute bottom-1 right-3 z-30 max-w-[calc(50%-5rem)] bg-hud-bg/90 px-2 py-0.5 text-right text-[11px] leading-snug text-hud-dim ${className}`}>
      {ATTRIBUTION_TEXT}
    </p>
  );
}
