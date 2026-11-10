import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Globe, { type GlobeMethods } from 'react-globe.gl';
import { AmbientLight, DirectionalLight, MeshPhongMaterial } from 'three';
import { Grain } from '@/components/Grain';
import { VIEWS, type Appearance } from '@/shared/lib/appearance';
import { hexToRgba } from '@/shared/lib/color';
import { ND, formatDecimal, formatPlace } from '@/shared/lib/format';
import { ND_GRAY, ageOpacity, colorByDepth, colorByMag, heightFor } from '@/shared/lib/symbology';
import type { EventFeature } from '@/shared/types/contract';

/** Ruta pública del catálogo de países (copia verificada por scripts/copy-countries.mjs). */
const landUrl = '/datos/paises.geojson';

interface LandFeature {
  properties: { ADM0_A3: string };
}

/** Evento ya preparado para dibujar. */
interface QuakePoint {
  id: string;
  lat: number;
  lng: number;
  mag: number | null;
  depth: number | null;
  height: number;
  time: number;
  feature: EventFeature;
}

/** Sismo con magnitud conocida: el único que lleva anillo o etiqueta (constitución §5). */
type MagPoint = QuakePoint & { mag: number };

/** Un sismo tiene magnitud si `mag` no es nulo; un nulo nunca se trata como 0. */
const hasMag = (q: QuakePoint): q is MagPoint => q.mag !== null;

interface GlobeViewProps {
  /** Eventos a dibujar. */
  events: EventFeature[];
  /** Ajustes visuales del laboratorio. */
  settings: Appearance;
  /** Id del evento seleccionado (se resalta y la cámara se centra en él). */
  selectedId: string | null;
  /** Se emite al hacer clic en un sismo (la selección completa llega en un paso posterior). */
  onSelect?: (event: EventFeature | null) => void;
}

/** Radio del globo en unidades de three-globe. */
const GLOBE_RADIUS = 100;
/** Si el puntero se mueve más que esto entre pulsar y soltar, es un arrastre, no un clic. */
const DRAG_THRESHOLD_PX = 5;

/** Vector unitario de una posición (convención de three-globe), para saber si da la cara a la cámara. */
function unitVector(lat: number, lng: number): [number, number, number] {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((90 - lng) * Math.PI) / 180;
  return [Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta)];
}

const HOUR_MS = 3_600_000;

/** Escapa texto de la API antes de meterlo en el HTML del tooltip. */
const escapeHtml = (t: string) =>
  t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Tooltip al pasar el ratón: magnitud («ND» si es nula), profundidad y lugar. */
function tooltipHtml(q: QuakePoint): string {
  const depth = q.depth == null ? ND : `${formatDecimal(q.depth)} km`;
  return (
    '<div style="font:12px ui-monospace,Consolas,monospace;padding:4px 8px;background:#0b0d10;' +
    'border:1px solid #6b7280;color:#e5e7eb;max-width:260px">' +
    `<b style="color:#ff7a1a">${q.mag === null ? ND : `M${escapeHtml(formatDecimal(q.mag))}`}</b> · ${escapeHtml(depth)}<br/>` +
    `${escapeHtml(formatPlace(q.feature.properties.place))}</div>`
  );
}

/** Distancia de un punto (px,py) al segmento (ax,ay)-(bx,by). */
function distToSegment(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy;
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

/** Duración (ms) del viaje de cámara al elegir un sismo; la atenuación del resto dura lo mismo. */
const SELECT_TRAVEL_MS = 1400;

/**
 * Globo 3D de sismos.
 *
 * Qué hace:
 *     Dibuja la tierra (países extruidos), un prisma por evento (largo = magnitud, color =
 *     profundidad), anillos y etiquetas solo para eventos con magnitud conocida por encima de
 *     su umbral, y gestiona cámara, giro, enfoque y selección por el pilar más cercano.
 * Recibe:
 *     events: eventos a dibujar (GeoJSON del contrato).
 *     settings: apariencia fija del globo.
 *     selectedId: id del evento seleccionado, o null.
 *     onSelect: se llama con el evento pulsado, o con null si no se acierta ninguno.
 * Devuelve:
 *     El elemento del globo; vacío hasta que el contenedor tiene tamaño.
 * Por qué existe:
 *     Es el único componente que usa `react-globe.gl` y `three`, de modo que se puede cambiar
 *     la librería sin tocar el resto. No calcula estadísticas (G2, G14, FR-017, FR-031).
 */
export function GlobeView({ events, settings: s, selectedId, onSelect }: GlobeViewProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [land, setLand] = useState<LandFeature[]>([]);
  const [ready, setReady] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  /** El usuario está arrastrando o haciendo zoom (o acaba de hacerlo). */
  const [userActive, setUserActive] = useState(false);
  const selectedRef = useRef(selectedId);
  selectedRef.current = selectedId;

  // Zoom propio con curva «ease-out» (arranca enseguida y se asienta suave). La del tween de la
  // librería arranca muy lenta y se notaba como retraso. Conserva la latitud/longitud de cada instante.
  const zoomRaf = useRef(0);
  const animateZoom = useCallback((toAlt: number, ms: number) => {
    const g = globeRef.current;
    if (!g) return;
    cancelAnimationFrame(zoomRaf.current);
    const from = g.pointOfView().altitude;
    const t0 = performance.now();
    const step = (now: number) => {
      const p = Math.min(1, (now - t0) / ms);
      const e = 1 - Math.pow(1 - p, 3);
      const cur = g.pointOfView();
      g.pointOfView({ lat: cur.lat, lng: cur.lng, altitude: from + (toAlt - from) * e }, 0);
      if (p < 1) zoomRaf.current = requestAnimationFrame(step);
    };
    zoomRaf.current = requestAnimationFrame(step);
  }, []);

  // `onGlobeReady` no se dispara sin textura: se da por listo cuando el globo ya está montado.
  const mounted = size.width > 0;
  useEffect(() => {
    setReady(mounted);
  }, [mounted]);

  // Países sin la Antártida (ADM0_A3 = ATA).
  useEffect(() => {
    fetch(landUrl)
      .then((r) => r.json())
      .then((geo: { features: LandFeature[] }) =>
        setLand(geo.features.filter((f) => f.properties.ADM0_A3 !== 'ATA')),
      );
  }, []);

  // El globo ocupa todo el contenedor.
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setSize({ width: e.contentRect.width, height: e.contentRect.height }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const quakes = useMemo<QuakePoint[]>(
    () =>
      events.map((f) => ({
        id: f.id,
        lng: f.geometry.coordinates[0],
        lat: f.geometry.coordinates[1],
        depth: f.geometry.coordinates[2],
        mag: f.properties.mag,
        height: heightFor(f.properties.mag) * s.heightScale,
        time: f.properties.time,
        feature: f,
      })),
    [events, s.heightScale],
  );

  const rings = useMemo(() => quakes.filter(hasMag).filter((q) => q.mag >= s.ringMinMag), [quakes, s.ringMinMag]);
  const labels = useMemo(() => quakes.filter(hasMag).filter((q) => q.mag >= s.labelMinMag), [quakes, s.labelMinMag]);

  const pointColor = (d: object) => {
    const q = d as QuakePoint;
    if (q.id === hoveredId) return hexToRgba('#ffffff', 0.85);
    // Magnitud nula: barra ND gris (salvo en color único).
    const base =
      s.colorMode === 'single'
        ? s.pointColor
        : q.mag === null
          ? ND_GRAY
          : s.colorMode === 'mag'
            ? colorByMag(q.mag)
            : colorByDepth(q.depth);
    const age = s.fadeByAge ? ageOpacity(Date.now() - q.time, s.fadeHours * HOUR_MS) : 1;
    const alpha = s.pointOpacity * age * dimFactor(q);
    // El seleccionado sube hacia opacidad plena con el enfoque, para destacar más.
    return hexToRgba(base, q.id === selectedId ? alpha + (1 - alpha) * focus : alpha);
  };

  // Luces.
  useEffect(() => {
    globeRef.current?.lights([new AmbientLight(0xffffff, s.ambient * Math.PI), new DirectionalLight(0xffffff, s.directional * Math.PI)]);
  }, [ready, s.ambient, s.directional]);

  // Material de la esfera: color, autoiluminación y reflejo (se pasa como prop).
  const globeMaterial = useMemo(
    () =>
      new MeshPhongMaterial({
        color: s.globeColor,
        emissive: s.globeEmissive,
        specular: s.globeSpecular,
        shininess: s.globeShininess,
      }),
    [s.globeColor, s.globeEmissive, s.globeSpecular, s.globeShininess],
  );

  // Altura de los anillos: sobre la tierra elevada, para que no queden enterrados.
  const ringAltitude = s.landMode === 'off' ? 0.001 : s.landAltitude + 0.002;

  // Resolución de píxel del lienzo (clave contra el efecto sierra).
  useEffect(() => {
    const g = globeRef.current as (GlobeMethods & { renderer?: () => { setPixelRatio: (r: number) => void } }) | undefined;
    g?.renderer?.().setPixelRatio(s.pixelRatio);
  }, [ready, s.pixelRatio, s.antialias]);

  // Giro automático: se pausa mientras el usuario mueve el globo, mientras hay una ficha abierta
  // y mientras el puntero está sobre un sismo (para poder pincharlo). La velocidad no salta:
  // acelera y frena con una curva suave (ease-out: arranca enseguida y se asienta) en lugar de saltar.
  const targetSpeed = s.autoRotate && !userActive && !selectedId && !hoveredId ? s.rotateSpeed : 0;
  const speedRef = useRef(0);
  useEffect(() => {
    const c = globeRef.current?.controls() as { autoRotate: boolean; autoRotateSpeed: number } | undefined;
    if (!c) return;
    const from = speedRef.current;
    const duration = targetSpeed > from ? s.rotateRampMs : 300; // frena más rápido de lo que acelera
    const t0 = performance.now();
    let raf = 0;
    const step = (now: number) => {
      const p = Math.min(1, (now - t0) / duration);
      speedRef.current = from + (targetSpeed - from) * (1 - (1 - p) * (1 - p)); // ease-out
      c.autoRotateSpeed = speedRef.current;
      c.autoRotate = speedRef.current > 0.001;
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [ready, targetSpeed, s.rotateRampMs]);

  // Modo enfoque: con un sismo seleccionado y el globo quieto, el resto se atenúa; al mover el globo
  // o cerrar la ficha vuelven a su aspecto normal. `focus` va de 0 a 1 y se anima de forma
  // sincronizada con la cámara: al elegir dura lo mismo que el viaje con zoom (misma curva), y al
  // cerrar dura lo mismo que la vuelta del zoom, de modo que la atenuación y el zoom son un solo efecto.
  const focusTarget = selectedId && !userActive ? 1 : 0;
  const [focus, setFocus] = useState(0);
  const focusRef = useRef(0);
  useEffect(() => {
    const from = focusRef.current;
    if (from === focusTarget) return;
    const closing = focusTarget === 0 && selectedRef.current === null;
    const duration = focusTarget === 1 ? SELECT_TRAVEL_MS : closing ? s.zoomReturnMs : 450;
    const t0 = performance.now();
    let raf = 0;
    const step = (now: number) => {
      const p = Math.min(1, (now - t0) / duration);
      // Entrada: ease-in-out cúbica (como el tween de la cámara); salida: ease-out (como la vuelta del zoom).
      const e = focusTarget === 1 ? (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2) : closing ? 1 - Math.pow(1 - p, 3) : p;
      focusRef.current = from + (focusTarget - from) * e;
      setFocus(focusRef.current);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [focusTarget, s.zoomReturnMs]);
  /** Factor de opacidad de un sismo según el enfoque: el seleccionado no se atenúa. */
  const dimFactor = (q: QuakePoint) => (q.id === selectedId ? 1 : 1 - s.dimOthers * focus);

  // Al dejar de arrastrar o hacer zoom, pasado un tiempo vuelve el zoom predeterminado y el giro.
  useEffect(() => {
    const g = globeRef.current;
    const c = g?.controls() as
      | { addEventListener: (t: string, f: () => void) => void; removeEventListener: (t: string, f: () => void) => void }
      | undefined;
    if (!g || !c) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const settle = () => {
      setUserActive(false);
      if (s.idleReturnSeconds > 0 && !selectedRef.current) {
        animateZoom(s.zoomAlt, s.zoomReturnMs);
      }
    };
    const onStart = () => {
      clearTimeout(timer);
      cancelAnimationFrame(zoomRaf.current);
      setUserActive(true);
    };
    const onEnd = () => {
      clearTimeout(timer);
      timer = setTimeout(settle, s.idleReturnSeconds * 1000);
    };
    c.addEventListener('start', onStart);
    c.addEventListener('end', onEnd);
    return () => {
      clearTimeout(timer);
      c.removeEventListener('start', onStart);
      c.removeEventListener('end', onEnd);
    };
  }, [ready, s.idleReturnSeconds, s.zoomAlt, s.zoomReturnMs]);

  // Al cerrar la ficha (a mano o sola) el zoom vuelve enseguida al predeterminado, de forma progresiva.
  const prevSelected = useRef<string | null>(null);
  useEffect(() => {
    const closed = prevSelected.current !== null && selectedId === null;
    prevSelected.current = selectedId;
    const g = globeRef.current;
    if (!closed || !g || s.idleReturnSeconds <= 0) return;
    animateZoom(s.zoomAlt, s.zoomReturnMs);
  }, [selectedId, s.idleReturnSeconds, s.zoomAlt, s.zoomReturnMs]);

  // Cámara: «ir a» y distancia.
  useEffect(() => {
    const g = globeRef.current;
    if (!g) return;
    const target = VIEWS[s.view];
    const now = g.pointOfView();
    g.pointOfView({ lat: target?.lat ?? now.lat, lng: target?.lng ?? now.lng, altitude: s.zoomAlt }, 800);
  }, [ready, s.view, s.zoomAlt]);

  // Elegir sismo: se mide la distancia del puntero al PILAR entero (de la base a la punta),
  // no solo a su centro, y gana el más cercano dentro de la tolerancia. Así un pilar fino se acierta
  // pinchando en cualquier punto de su largo.
  const pickables = useMemo(() => (s.showPoints ? quakes : []), [s.showPoints, quakes]);
  useEffect(() => {
    const el = wrapRef.current;
    if (!el || !ready) return;
    const tolerance = s.pickTolerance;

    const pickAt = (clientX: number, clientY: number): QuakePoint | null => {
      const g = globeRef.current;
      if (!g) return null;
      const rect = el.getBoundingClientRect();
      const x = clientX - rect.left;
      const y = clientY - rect.top;
      const cam = g.camera().position;
      let best: QuakePoint | null = null;
      let bestDist = tolerance;
      for (const q of pickables) {
        const n = unitVector(q.lat, q.lng);
        if (n[0] * cam.x + n[1] * cam.y + n[2] * cam.z <= GLOBE_RADIUS) continue; // cara oculta
        const base = g.getScreenCoords(q.lat, q.lng, 0);
        const tip = g.getScreenCoords(q.lat, q.lng, q.height);
        const d = distToSegment(x, y, base.x, base.y, tip.x, tip.y);
        if (d < bestDist) {
          bestDist = d;
          best = q;
        }
      }
      return best;
    };

    let down: [number, number] | null = null;
    const onDown = (e: PointerEvent) => {
      down = [e.clientX, e.clientY];
    };
    const onUp = (e: PointerEvent) => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > DRAG_THRESHOLD_PX) return;
      // Un clic no es mover el globo: la cámara lo registra como interacción al pulsar, y eso mantendría
      // apagado el modo enfoque (y parado el giro) 3 s. Se anula aquí para que el efecto empiece ya.
      setUserActive(false);
      const hit = pickAt(e.clientX, e.clientY);
      onSelect?.(hit ? hit.feature : null);
    };

    // Al pasar el ratón: cursor de mano y el pilar se ilumina (una vez por fotograma como máximo).
    let frame = 0;
    const onMove = (e: PointerEvent) => {
      if (e.buttons !== 0) return; // arrastrando el globo
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const hit = pickAt(e.clientX, e.clientY);
        el.style.cursor = hit ? 'pointer' : '';
        setHoveredId((prev) => (prev === (hit?.id ?? null) ? prev : (hit?.id ?? null)));
      });
    };
    const onLeave = () => {
      el.style.cursor = '';
      setHoveredId(null);
    };

    el.addEventListener('pointerdown', onDown);
    el.addEventListener('pointerup', onUp);
    el.addEventListener('pointermove', onMove);
    el.addEventListener('pointerleave', onLeave);
    return () => {
      cancelAnimationFrame(frame);
      el.removeEventListener('pointerdown', onDown);
      el.removeEventListener('pointerup', onUp);
      el.removeEventListener('pointermove', onMove);
      el.removeEventListener('pointerleave', onLeave);
    };
  }, [ready, pickables, onSelect, s.pickTolerance]);

  // Encuadra el evento seleccionado sin cambiar la distancia. Se centra la cámara en un punto
  // desplazado hacia el suroeste del evento, para que el evento quede arriba a la derecha y se
  // vea el pilar de lado (con el evento justo en el centro solo se ve su punta).
  // Se depende de la posición (números) y no del objeto, para que un refresco de datos no mueva la cámara.
  const selected = quakes.find((x) => x.id === selectedId);
  const selLat = selected?.lat;
  const selLng = selected?.lng;
  useEffect(() => {
    const g = globeRef.current;
    if (!g || selLat === undefined || selLng === undefined) return;
    cancelAnimationFrame(zoomRaf.current);
    // Zoom in al elegir (si está activo); si no, se conserva la distancia actual.
    const altitude = s.selectZoomAlt > 0 ? s.selectZoomAlt : g.pointOfView().altitude;
    // El desplazamiento se escala con la distancia: más cerca, el mismo ángulo sacaría el evento de pantalla.
    const d = s.selectOffset * (altitude / s.zoomAlt);
    const lat = Math.max(-85, Math.min(85, selLat - d));
    // La longitud se compensa por la latitud para que el desplazamiento sea similar en pantalla.
    const lng = selLng - d / Math.max(0.35, Math.cos((selLat * Math.PI) / 180));
    g.pointOfView({ lat, lng, altitude }, SELECT_TRAVEL_MS);
  }, [selLat, selLng, s.selectOffset, s.selectZoomAlt, s.zoomAlt]);

  const hexLand = s.landMode === 'hex' ? land : [];
  const polyLand = s.landMode === 'polygons' ? land : [];

  return (
    <div ref={wrapRef} className="relative h-full w-full overflow-hidden" style={{ background: s.bgColor }}>
      <Grain settings={s} />
      {size.width > 0 && (
        <div className="relative z-[1]">
        <Globe
          // El antialiasing solo se fija al crear el renderizador: cambiarlo remonta el globo.
          key={String(s.antialias)}
          ref={globeRef}
          rendererConfig={{ antialias: s.antialias, alpha: true }}
          globeCurvatureResolution={s.curvature}
          hexPolygonCurvatureResolution={s.curvature}
          polygonCapCurvatureResolution={s.curvature}
          width={size.width}
          height={size.height}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl={null}
          globeMaterial={globeMaterial}
          showGlobe={s.showGlobe}
          showGraticules={s.showGraticules}
          showAtmosphere={s.showAtmosphere}
          atmosphereColor={s.atmosphereColor}
          atmosphereAltitude={s.atmosphereAltitude}
          // Tierra en celdas H3
          hexPolygonsData={hexLand}
          hexPolygonResolution={s.landRes}
          hexPolygonMargin={s.landMargin}
          hexPolygonUseDots={s.landDots}
          hexPolygonColor={() => s.landColor}
          hexPolygonAltitude={s.landAltitude}
          hexPolygonsTransitionDuration={s.transitionMs}
          // Tierra como países extruidos
          polygonsData={polyLand}
          polygonCapColor={() => s.landColor}
          polygonSideColor={() => s.polySideColor}
          polygonStrokeColor={() => s.polyStrokeColor}
          polygonAltitude={s.landAltitude}
          polygonsTransitionDuration={s.transitionMs}
          // Sismos como prismas
          pointsData={s.showPoints ? quakes : []}
          pointLat="lat"
          pointLng="lng"
          pointAltitude="height"
          pointRadius={s.pointRadius}
          pointResolution={s.pointSides}
          pointColor={pointColor}
          pointLabel={(d) => tooltipHtml(d as QuakePoint)}
          pointsMerge={s.pointMerge}
          pointsTransitionDuration={s.transitionMs}
          // Anillos
          ringsData={s.showRings ? rings : []}
          ringLat="lat"
          ringLng="lng"
          ringAltitude={ringAltitude}
          ringColor={(d: object) => (t: number) => hexToRgba(s.ringColor, (1 - t) * dimFactor(d as QuakePoint))}
          ringMaxRadius={(d) => (s.ringBySize ? (d as MagPoint).mag * s.ringRadiusPerMag : s.ringMaxRadius)}
          ringPropagationSpeed={s.ringSpeed}
          ringRepeatPeriod={s.ringPeriod}
          // Etiquetas 3D
          labelsData={s.showLabels ? labels : []}
          labelLat="lat"
          labelLng="lng"
          labelText={(d) => `M${(d as MagPoint).mag}`}
          labelSize={s.labelSize}
          labelColor={(d) => hexToRgba(s.labelColor, dimFactor(d as QuakePoint))}
          labelAltitude={(d) => (d as QuakePoint).height + 0.005}
          labelIncludeDot={s.labelDot}
          labelResolution={2}
        />
        </div>
      )}
    </div>
  );
}
