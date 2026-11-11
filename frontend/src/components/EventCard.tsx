import { ND, formatCountry, formatDecimal, formatMagnitude, formatPlace, formatUtc } from '@/shared/lib/format';
import type { EventFeature } from '@/shared/types/contract';
import { Row } from './SidebarParts';

/**
 * Qué hace:
 *     Muestra la ficha del evento seleccionado, sin caja, sobre el fondo del globo.
 * Recibe:
 *     Evento seleccionado y la función de cierre.
 * Devuelve:
 *     La ficha con magnitud y su tipo, profundidad, lugar, país, fechas UTC y enlace si lo hay.
 * Por qué existe:
 *     Es el detalle de un evento; los nulos salen como «ND» y nunca como 0 (G2, G12).
 */
export function EventCard({
  event,
  onClose,
  leaving = false,
  className = '',
}: {
  event: EventFeature;
  onClose: () => void;
  /** Se está cerrando: se desvanece (la desmonta quien la usa al terminar). */
  leaving?: boolean;
  className?: string;
}) {
  const p = event.properties;
  const depth = event.geometry.coordinates[2];
  return (
    <div
      className={`relative text-hud-text transition-opacity duration-500 ease-out [text-shadow:0_1px_4px_#000] ${leaving ? 'opacity-0' : 'opacity-100'} ${className}`}
    >
      <button onClick={onClose} aria-label="Cerrar ficha" className="absolute right-0 top-0 text-hud-dim hover:text-hud-text">
        ✕
      </button>
      <div className="mt-1 text-[11px] uppercase tracking-[0.2em] text-hud-accent">Evento seleccionado</div>
      <div className="mt-2 text-4xl font-semibold text-hud-accent">{formatDecimal(p.mag)}</div>
      <div className="text-[11px] uppercase tracking-[0.12em] text-hud-dim">{formatMagnitude(p.mag, p.magType)}</div>
      <p className="my-2 text-sm">{formatPlace(p.place)}</p>
      <Row k="Profundidad" v={depth == null ? ND : `${formatDecimal(depth)} km`} />
      <Row k="Fecha" v={formatUtc(p.time)} />
      <Row k="Actualizado" v={formatUtc(p.updated)} />
      <Row k="País" v={formatCountry(p.country_name)} />
      <Row k="Estado" v={p.status ?? ND} />
      <Row k="Significancia" v={p.sig == null ? ND : String(p.sig)} />
      {p.url && (
        <a href={p.url} target="_blank" rel="noreferrer" className="mt-1 block text-xs text-hud-accent underline">
          Ver detalle
        </a>
      )}
      {p.is_synthetic && <div className="mt-2 text-[10px] uppercase tracking-[0.15em] text-hud-dim">Dato marcado como sintético</div>}
    </div>
  );
}
