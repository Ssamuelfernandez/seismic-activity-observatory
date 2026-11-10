import { useMemo, useState, type ReactNode } from 'react';
import type { ObservatoryData } from '@/shared/hooks/useObservatory';
import { useViewport } from '@/shared/hooks/useMediaQuery';
import type { Appearance } from '@/shared/lib/appearance';
import type { EventFeature } from '@/shared/types/contract';
import { EventCard } from '../EventCard';
import { FeedStatus } from '../FeedStatus';
import { FiltersBar } from '../FiltersBar';
import { GlobeView } from '../GlobeView';
import { Legend } from '../Legend';
import { RecentEvents } from '../RecentEvents';
import { StatsPanel } from '../StatsPanel';
import { StatusBanners } from '../StatusBanners';
import { MobileEventsList } from './MobileEventsList';

type Panel = 'events' | 'stats' | 'legend';

const TABS: [Panel, string][] = [
  ['events', 'Eventos'],
  ['stats', 'Estadísticas'],
  ['legend', 'Leyenda'],
];

/** Hoja inferior opaca (sin transparencias, que en móvil estorban) con botón de cierre. */
function Sheet({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  return (
    <div className="absolute inset-x-0 bottom-0 z-10 flex max-h-[72%] flex-col border-t border-hud-line bg-hud-panel">
      <div className="flex shrink-0 justify-end">
        <button onClick={onClose} className="px-4 py-2 text-[11px] uppercase tracking-[0.1em] text-hud-dim">
          Cerrar ✕
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">{children}</div>
    </div>
  );
}

const round = (n: number, step: number) => Math.round(n / step) * step;

/**
 * Qué hace:
 *     Monta el diseño móvil (< 1024 px): barra superior, globo y hojas inferiores de eventos, estadísticas y leyenda.
 * Recibe:
 *     Los datos del panel, la selección y las funciones de selección y cierre.
 * Devuelve:
 *     El diseño móvil completo.
 * Por qué existe:
 *     El panel debe ser usable a 375 px sin scroll horizontal (G17).
 */
export function MobileLayout({
  settings,
  data,
  events,
  selected,
  onSelect,
}: {
  settings: Appearance;
  data: ObservatoryData;
  events: EventFeature[];
  selected: EventFeature | null;
  onSelect: (event: EventFeature | null) => void;
}) {
  const [panel, setPanel] = useState<Panel | null>(null);
  const [listOpen, setListOpen] = useState(false);
  const response = data.response;
  const { width, height } = useViewport();

  // Ajustes del globo para pantalla estrecha: se aleja la cámara hasta que la esfera entre en el ancho,
  // el evento elegido se centra (la ficha va abajo, no a un lado) y solo se etiquetan los sismos grandes.
  const globeSettings = useMemo<Appearance>(() => {
    const aspect = width / Math.max(1, height - 120);
    const alt = Math.min(4.2, Math.max(2, round(2.25 / aspect - 1, 0.25)));
    return { ...settings, zoomAlt: alt, selectZoomAlt: round(alt * 0.55, 0.25), selectOffset: 0, labelMinMag: 6, pickTolerance: 28 };
  }, [settings, width, height]);

  // Elegir un evento (desde el globo, la lista o la tabla) cierra lo que estuviera abierto para ver su ficha.
  const pick = (event: EventFeature | null) => {
    onSelect(event);
    setPanel(null);
    setListOpen(false);
  };

  const hasSynthetic = events.some((e) => e.properties.is_synthetic);

  return (
    <div className="flex h-dvh flex-col bg-hud-bg text-hud-text">
      {/* Barra superior: filtros (resumen) y estado. Sus desplegables ocupan todo el ancho. */}
      <header className="relative z-40 flex shrink-0 items-center gap-2 border-b border-hud-line bg-hud-panel px-3">
        <FiltersBar variant="mobile" />
        <FeedStatus
          variant="mobile"
          className="shrink-0"
          metadata={response?.metadata ?? null}
          error={data.error}
          health={data.health}
          healthError={data.healthError}
          period={data.stats?.period ?? null}
          updatedAt={data.updatedAt}
          hasSynthetic={hasSynthetic}
        />
      </header>

      {/* Zona del globo */}
      <div className="relative min-h-0 flex-1">
        <GlobeView events={events} settings={globeSettings} selectedId={selected?.id ?? null} onSelect={pick} />

        <StatusBanners
          variant="mobile"
          className="absolute inset-x-0 top-0 z-20"
          metadata={response?.metadata ?? null}
          error={data.error}
          health={data.health}
          healthError={data.healthError}
          updatedAt={data.updatedAt}
          hasData={Boolean(response)}
          hasSynthetic={hasSynthetic}
        />

        {selected && !panel && !listOpen && (
          <div className="absolute inset-x-0 bottom-0 z-10 max-h-[60%] overflow-y-auto border-t border-hud-line bg-hud-panel px-4 pb-4 pt-3">
            <EventCard event={selected} onClose={() => onSelect(null)} />
          </div>
        )}

        {panel === 'events' && (
          <Sheet onClose={() => setPanel(null)}>
            <RecentEvents
              events={events}
              selected={selected}
              settings={settings}
              onSelect={pick}
              onShowAll={() => {
                setPanel(null);
                setListOpen(true);
              }}
              unavailable={!response}
            />
          </Sheet>
        )}
        {panel === 'stats' && (
          <Sheet onClose={() => setPanel(null)}>
            <StatsPanel stats={data.stats} error={data.statsError} />
          </Sheet>
        )}
        {panel === 'legend' && (
          <Sheet onClose={() => setPanel(null)}>
            <Legend settings={settings} />
          </Sheet>
        )}

        {listOpen && <MobileEventsList events={events} selected={selected} settings={settings} onSelect={pick} onClose={() => setListOpen(false)} />}
      </div>

      {/* Barra inferior */}
      <nav aria-label="Paneles" className="grid shrink-0 grid-cols-3 border-t border-hud-line bg-hud-panel">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            onClick={() => {
              setListOpen(false);
              setPanel(panel === id ? null : id);
            }}
            aria-pressed={panel === id}
            className={`py-3 text-[11px] uppercase tracking-[0.12em] ${panel === id ? 'text-hud-accent' : 'text-hud-dim'}`}
          >
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
}
