// Apariencia del globo: valores fijos del diseño (ya no hay panel de ajustes).

export interface Appearance {
  // Fondo y globo
  bgColor: string;
  showGlobe: boolean;
  globeColor: string;
  globeEmissive: string;
  globeSpecular: string;
  globeShininess: number;
  showGraticules: boolean;
  showAtmosphere: boolean;
  atmosphereColor: string;
  atmosphereAltitude: number;
  // Luces
  ambient: number;
  directional: number;
  // Tierra
  landMode: 'hex' | 'polygons' | 'off';
  landRes: number;
  landMargin: number;
  landColor: string;
  landDots: boolean;
  landAltitude: number;
  polySideColor: string;
  polyStrokeColor: string;
  // Sismos como prismas
  showPoints: boolean;
  pointRadius: number;
  pointSides: number;
  heightScale: number;
  pointOpacity: number;
  colorMode: 'depth' | 'mag' | 'single';
  pointColor: string;
  pointMerge: boolean;
  /** Distancia máxima (px) entre el clic y el pilar para seleccionarlo. */
  pickTolerance: number;
  /** Opacidad según antigüedad del evento. */
  fadeByAge: boolean;
  /** Ventana (h) en la que la opacidad baja de 1 a 0,25. */
  fadeHours: number;
  // Anillos
  showRings: boolean;
  ringMinMag: number;
  ringMaxRadius: number;
  ringSpeed: number;
  ringPeriod: number;
  ringColor: string;
  /** Radio de la onda proporcional a la magnitud. */
  ringBySize: boolean;
  /** Grados de radio por unidad de magnitud. */
  ringRadiusPerMag: number;
  // Etiquetas 3D
  showLabels: boolean;
  labelMinMag: number;
  labelSize: number;
  labelColor: string;
  labelDot: boolean;
  // Cámara y animación
  autoRotate: boolean;
  rotateSpeed: number;
  /** Segundos sin tocar el globo tras los que vuelven el zoom y el giro (0 = no vuelven). */
  idleReturnSeconds: number;
  /** Duración (ms) de la vuelta suave al zoom predeterminado. */
  zoomReturnMs: number;
  /** Duración (ms) en que el giro acelera hasta su velocidad al reanudarse. */
  rotateRampMs: number;
  /** Grados que se desplaza hacia arriba a la derecha un sismo seleccionado (0 = centrado). */
  selectOffset: number;
  /** Cuánto se atenúan los demás sismos mientras uno está seleccionado (0 = nada, 1 = casi invisibles). */
  dimOthers: number;
  /** Distancia de cámara al elegir un sismo (zoom in; 0 = no cambiar el zoom). */
  selectZoomAlt: number;
  /** Segundos sin actividad tras los que se cierra sola la ficha (0 = no se cierra). */
  cardAutoCloseSeconds: number;
  view: 'libre' | 'chile' | 'japon' | 'indonesia' | 'mexico' | 'mediterraneo';
  zoomAlt: number;
  transitionMs: number;
  // Grano de fondo
  /** Intensidad del grano (0 = sin grano); sube el brillo de los puntos sobre el color de fondo. */
  grainOpacity: number;
  /** Tamaño de cada punto de grano, en píxeles CSS (0,5 = un píxel físico en pantallas de doble densidad). */
  grainSize: number;
  // Calidad de imagen
  antialias: boolean;
  pixelRatio: number;
  curvature: number;
}

export const APPEARANCE: Appearance = {
  bgColor: '#070a0e',
  showGlobe: true,
  globeColor: '#060606',
  globeEmissive: '#000000',
  globeSpecular: '#3a3a3a',
  globeShininess: 13,
  showGraticules: true,
  showAtmosphere: true,
  atmosphereColor: '#ffffff',
  atmosphereAltitude: 0.1,
  ambient: 0.8,
  directional: 0.3,
  landMode: 'polygons',
  landRes: 4,
  landMargin: 0.22,
  landColor: '#333333',
  landDots: false,
  landAltitude: 0.011,
  polySideColor: '#232323',
  polyStrokeColor: '#5d5d5d',
  showPoints: true,
  pointRadius: 0.2,
  pointSides: 7,
  heightScale: 3.7,
  pointOpacity: 0.9,
  colorMode: 'depth',
  pointColor: '#ff7a1a',
  pointMerge: false,
  pickTolerance: 18,
  fadeByAge: true,
  fadeHours: 24,
  showRings: true,
  ringMinMag: 4,
  ringMaxRadius: 4,
  ringSpeed: 2.5,
  ringPeriod: 1500,
  ringColor: '#ea7e2f',
  ringBySize: true,
  ringRadiusPerMag: 0.8,
  showLabels: true,
  labelMinMag: 5,
  labelSize: 1.3,
  labelColor: '#e5e7eb',
  labelDot: false,
  autoRotate: true,
  rotateSpeed: 0.3,
  idleReturnSeconds: 3,
  zoomReturnMs: 1600,
  rotateRampMs: 1200,
  selectOffset: 22,
  dimOthers: 0.85,
  selectZoomAlt: 1,
  cardAutoCloseSeconds: 10,
  view: 'mediterraneo',
  zoomAlt: 2,
  transitionMs: 1400,
  grainOpacity: 0.09,
  grainSize: 1,
  antialias: true,
  pixelRatio: 2,
  curvature: 2,
};

/** Puntos de vista de la cámara para el selector «Ir a». */
export const VIEWS: Record<string, { lat: number; lng: number }> = {
  chile: { lat: -33.4, lng: -70.6 },
  japon: { lat: 35.7, lng: 139.7 },
  indonesia: { lat: -2, lng: 115 },
  mexico: { lat: 19.4, lng: -99.1 },
  mediterraneo: { lat: 38, lng: 20 },
};
