import { useEffect, useRef, useState } from 'react';
import { AppShell } from '@/components/AppShell';
import { Attribution } from '@/components/Attribution';
import { MobileLayout } from '@/components/mobile/MobileLayout';
import { useIsMobile } from '@/shared/hooks/useMediaQuery';
import { FiltersBar } from '@/components/FiltersBar';
import { EventsTable } from '@/components/EventsTable';
import { EventCard } from '@/components/EventCard';
import { FeedStatus } from '@/components/FeedStatus';
import { GlobeView } from '@/components/GlobeView';
import { Legend } from '@/components/Legend';
import { RecentEvents } from '@/components/RecentEvents';
import { StatusBanners } from '@/components/StatusBanners';
import { StatsDrawer } from '@/components/StatsDrawer';
import { APPEARANCE } from '@/shared/lib/appearance';
import { useObservatory } from '@/shared/hooks/useObservatory';
import { useFilters } from '@/store/filters';
import type { EventFeature } from '@/shared/types/contract';

/** Duración del desvanecimiento de la ficha al cerrarse sola (ms); coincide con la clase de EventCard. */
const CARD_FADE_MS = 500;

/**
 * Qué hace:
 *     Compone la pantalla del panel: globo, leyenda, eventos recientes, estado, filtros, avisos, ficha, tabla y estadísticas (o el diseño móvil).
 * Recibe:
 *     Nada.
 * Devuelve:
 *     El elemento raíz de la aplicación.
 * Por qué existe:
 *     Es la composición única del panel; la lógica vive en hooks y componentes (G0, G2, G17).
 */
export function App() {
  const settings = APPEARANCE;
  const isMobile = useIsMobile();
  const data = useObservatory();
  const response = data.response;
  const [selected, setSelected] = useState<EventFeature | null>(null);
  const [showTable, setShowTable] = useState(false);

  // La tabla empieza justo debajo de la barra de filtros y sus avisos (su altura cambia), para no taparlos ni que le roben los clics.
  const centerRef = useRef<HTMLDivElement>(null);
  const [centerHeight, setCenterHeight] = useState(0);
  useEffect(() => {
    const el = centerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setCenterHeight(el.offsetHeight));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const events = response?.features ?? [];

  // La ficha se cierra sola tras N segundos sin actividad (ratón, rueda o teclado): se desvanece
  // y al desmontarse el globo vuelve a girar y recupera el zoom. Cualquier actividad reinicia la cuenta.
  const [leaving, setLeaving] = useState(false);
  const selectedKey = selected?.id ?? null;
  const autoClose = isMobile ? 0 : settings.cardAutoCloseSeconds;
  useEffect(() => {
    setLeaving(false);
    if (selectedKey === null || autoClose <= 0) return;
    let fadeTimer: ReturnType<typeof setTimeout> | undefined;
    let closeTimer: ReturnType<typeof setTimeout> | undefined;
    const arm = () => {
      clearTimeout(fadeTimer);
      clearTimeout(closeTimer);
      setLeaving(false);
      fadeTimer = setTimeout(() => {
        setLeaving(true);
        closeTimer = setTimeout(() => setSelected(null), CARD_FADE_MS);
      }, autoClose * 1000);
    };
    const events = ['pointermove', 'pointerdown', 'wheel', 'keydown'] as const;
    events.forEach((e) => window.addEventListener(e, arm, { passive: true }));
    arm();
    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(closeTimer);
      events.forEach((e) => window.removeEventListener(e, arm));
    };
  }, [selectedKey, autoClose]);

  // Al cambiar un filtro se pierde la selección (el evento puede ya no estar).
  const filterKey = useFilters((f) => `${f.mode}|${f.hours}|${f.dateFrom}|${f.dateTo}|${f.minMag}|${f.country}`);
  useEffect(() => setSelected(null), [filterKey]);

  if (isMobile) {
    return <MobileLayout settings={settings} data={data} events={events} selected={selected} onSelect={setSelected} />;
  }

  return (
    <AppShell>
      <div className="relative h-full">
        <GlobeView events={events} settings={settings} selectedId={leaving ? null : (selected?.id ?? null)} onSelect={setSelected} />
        {/* Izquierda: la leyenda y, debajo, los eventos recientes (la lista hace scroll si falta altura). */}
        <div className={`pointer-events-none absolute bottom-16 left-4 top-4 z-[5] flex w-80 flex-col gap-7 ${showTable ? 'invisible' : ''}`}>
          <Legend settings={settings} />
          {/* Separador: línea fina que se desvanece hacia la derecha (sin caja). */}
          <div className="h-px w-full shrink-0 bg-gradient-to-r from-hud-line-strong/80 to-transparent" />
          <RecentEvents
            className="pointer-events-auto min-h-0"
            events={events}
            selected={selected}
            settings={settings}
            onSelect={setSelected}
            onShowAll={() => setShowTable(true)}
            unavailable={!response}
            loading={data.state === 'loading'}
            total={response?.metadata.total ?? null}
          />
        </div>
        {showTable && (
          <EventsTable
            className="absolute bottom-16 left-4 z-[6] w-[min(62rem,calc(100%-22rem))] pr-6"
            style={{ top: `calc(1rem + ${centerHeight}px + 0.75rem)` }}
            events={events}
            selected={selected}
            settings={settings}
            onSelect={setSelected}
            onClose={() => setShowTable(false)}
            total={response?.metadata.total ?? null}
          />
        )}
        {/* Centro arriba: barra de filtros y, debajo, los avisos (replay, fallos de la API, datos antiguos o sintéticos). */}
        <div ref={centerRef} className="pointer-events-none absolute left-1/2 top-4 z-10 flex w-[min(36rem,calc(100%-46rem))] -translate-x-1/2 flex-col gap-3">
          <FiltersBar />
          <StatusBanners
            metadata={response?.metadata ?? null}
            error={data.error}
            health={data.health}
            healthError={data.healthError}
            updatedAt={data.updatedAt}
            hasData={Boolean(response)}
            hasSynthetic={events.some((e) => e.properties.is_synthetic)}
            state={data.state}
          />
        </div>
        {/* Columna derecha: estado del feed arriba, mucho aire y debajo la ficha (si hay). */}
        <div className="pointer-events-none absolute bottom-4 right-4 top-4 z-10 flex w-80 flex-col gap-12">
          <FeedStatus
            className="shrink-0 self-end"
            metadata={response?.metadata ?? null}
            error={data.error}
            health={data.health}
            healthError={data.healthError}
            period={data.stats?.period ?? null}
            updatedAt={data.updatedAt}
            hasSynthetic={events.some((e) => e.properties.is_synthetic)}
          />
          {selected && (
            <EventCard event={selected} leaving={leaving} onClose={() => setSelected(null)} className="pointer-events-auto shrink-0" />
          )}
        </div>
        {/* Cajón inferior: una flechita sube las estadísticas desde abajo. */}
        <StatsDrawer className="z-20" stats={data.stats} error={data.statsError} />
        {/* Atribución fija abajo a la derecha, por encima del cajón. */}
        <Attribution />
      </div>
    </AppShell>
  );
}
