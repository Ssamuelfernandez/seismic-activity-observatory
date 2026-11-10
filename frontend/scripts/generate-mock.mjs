// Generador determinista del mock SINTÉTICO del panel (G15, FR-008, FR-009).
// Semilla fija y sin dependencias: dos ejecuciones dan archivos idénticos.
// Escribe mock/base.json, truncated.json, replay.json, empty.json y realistic.json
// con la forma de specs/001-contratos-y-modelo/contracts/api.md §3.2 y §3.4.
// Uso: node scripts/generate-mock.mjs
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'mock');
const SEED = 20261105;
// Instante fijo de "generación": así el resultado no depende del reloj.
const GENERATED_MS = 1793700000000;
const BASE_TIME_MS = 1793600000000;
const TRUNCATED_COUNT = 5000;
const TRUNCATED_TOTAL = 6213;
const BASE_COUNT = 30;
// 2025-06-15: con seis eventos un día aparte quedan todos dentro de 2025.
const REPLAY_BASE_MS = 1750000000000;
const REALISTIC_COUNT = 400;
const HOUR_MS = 3600000;

/** Generador pseudoaleatorio mulberry32 (determinista a partir de la semilla). */
function makeRng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const round = (value, decimals) => Number(value.toFixed(decimals));

/** Países usados solo para etiquetar el mock (no es una asignación real por geometría). */
const COUNTRIES = [
  ['CHL', 'Chile'], ['JPN', 'Japón'], ['USA', 'Estados Unidos'], ['IDN', 'Indonesia'],
  ['MEX', 'México'], ['TUR', 'Turquía'], ['NZL', 'Nueva Zelanda'], ['PER', 'Perú'],
  ['GRC', 'Grecia'], ['PHL', 'Filipinas'],
];
const MAG_TYPES = ['ml', 'md', 'mb', 'mww', 'mwr', 'mwc'];

function makeFeature({ id, lon, lat, depth, mag, magType, place, time, country, url = null, sig = null }) {
  return {
    type: 'Feature',
    id,
    geometry: { type: 'Point', coordinates: [lon, lat, depth] },
    properties: {
      mag,
      magType,
      place,
      time,
      updated: time + 60000,
      country_id: country ? country[0] : null,
      country_name: country ? country[1] : null,
      is_synthetic: true,
      status: 'automatic',
      url,
      sig,
    },
  };
}

function makeMetadata(mode, features, extra = {}) {
  return {
    generated: GENERATED_MS,
    last_ingestion: GENERATED_MS - 30000,
    mode,
    count: features.length,
    total: features.length,
    truncated: false,
    next_cursor: null,
    null_mag_excluded: 0,
    ...extra,
  };
}

function makeResponse(mode, features, extra) {
  return { type: 'FeatureCollection', metadata: makeMetadata(mode, features, extra), features };
}

/** Caso `base`: casos límite escritos a mano + relleno con la semilla (~30 features). */
function buildBase() {
  const c = Object.fromEntries(COUNTRIES.map((x) => [x[0], x]));
  const hand = [
    // Una por clase de profundidad (V2): <10, 10-35, 35-70, 70-300, >=300.
    { lon: -70.6, lat: -33.4, depth: 5, mag: 3.1, magType: 'ml', place: 'Sintético: cerca de una ciudad costera A', country: c.CHL },
    { lon: 139.7, lat: 35.7, depth: 22.5, mag: 4.2, magType: 'mb', place: 'Sintético: golfo de ejemplo B', country: c.JPN },
    { lon: -118.2, lat: 34.0, depth: 48, mag: 5.4, magType: 'mww', place: 'Sintético: valle de ejemplo C', country: c.USA, url: true, sig: 449 },
    { lon: 106.8, lat: -6.2, depth: 150, mag: 6.1, magType: 'mww', place: 'Sintético: isla de ejemplo D', country: c.IDN },
    { lon: -99.1, lat: 19.4, depth: 520, mag: 6.8, magType: 'mwr', place: 'Sintético: altiplano de ejemplo E', country: c.MEX },
    // Casos límite (FR-008).
    { lon: -150.0, lat: 10.0, depth: 12, mag: null, magType: 'ml', place: 'Sintético: océano sin magnitud', country: null },
    { lon: 28.9, lat: 41.0, depth: null, mag: 3.8, magType: 'md', place: 'Sintético: estrecho sin profundidad', country: c.TUR },
    { lon: -116.7, lat: 33.5, depth: 6.39, mag: -0.06, magType: 'ml', place: 'Sintético: magnitud negativa', country: c.USA },
    { lon: -119.1, lat: 33.4, depth: -0.01, mag: 2.64, magType: 'ml', place: 'Sintético: profundidad negativa', country: null },
    { lon: -30.0, lat: -20.0, depth: 10, mag: 4.9, magType: null, place: 'Sintético: dorsal sin tipo de magnitud', country: null },
    { lon: 170.5, lat: -43.5, depth: 30, mag: 4.4, magType: 'mb', place: null, country: c.NZL },
    { lon: 100.0, lat: -40.0, depth: null, mag: null, magType: null, place: 'Sintético: sin magnitud ni profundidad', country: null },
    { lon: 0.0, lat: 0.0, depth: 69.99, mag: 8.0, magType: 'mww', place: 'Sintético: magnitud máxima de la escala', country: null },
    { lon: 23.7, lat: 37.9, depth: 9.99, mag: 0, magType: 'md', place: 'Sintético: magnitud cero real', country: c.GRC },
    { lon: 121.0, lat: 14.6, depth: 299.99, mag: 5.0, magType: 'mwc', place: 'Sintético: borde de clase de profundidad', country: c.PHL },
    { lon: -77.0, lat: -12.0, depth: 300, mag: 4.0, magType: 'mb', place: 'Sintético: borde de 300 km', country: c.PER },
  ];
  const rng = makeRng(SEED);
  const features = hand.map((h, i) => {
    const id = `mock-base-${String(i + 1).padStart(3, '0')}`;
    const url = h.url ? `https://example.org/mock/${id}` : null;
    return makeFeature({ ...h, id, time: BASE_TIME_MS - i * 3600000, url });
  });
  // Relleno con la semilla hasta BASE_COUNT features, repartido por el mundo.
  for (let i = features.length; i < BASE_COUNT; i += 1) {
    const country = rng() < 0.7 ? COUNTRIES[Math.floor(rng() * COUNTRIES.length)] : null;
    features.push(makeFeature({
      id: `mock-base-${String(i + 1).padStart(3, '0')}`,
      lon: round(rng() * 360 - 180, 3),
      lat: round(rng() * 140 - 70, 3),
      depth: round(rng() * 400, 1),
      mag: round(1 + rng() * 5, 1),
      magType: MAG_TYPES[Math.floor(rng() * MAG_TYPES.length)],
      place: `Sintético: punto de relleno ${i + 1}`,
      time: BASE_TIME_MS - i * 3600000,
      country,
    }));
  }
  return makeResponse('live', features);
}

/** Caso `truncated`: 5 000 features, `total` 6213 y cursor no nulo. */
function buildTruncated() {
  const rng = makeRng(SEED + 1);
  const features = [];
  for (let i = 0; i < TRUNCATED_COUNT; i += 1) {
    const nullMag = rng() < 0.01;
    const nullDepth = rng() < 0.01;
    const country = rng() < 0.7 ? COUNTRIES[Math.floor(rng() * COUNTRIES.length)] : null;
    features.push(makeFeature({
      id: `mock-truncated-${String(i + 1).padStart(4, '0')}`,
      lon: round(rng() * 360 - 180, 3),
      lat: round(rng() * 140 - 70, 3),
      depth: nullDepth ? null : round(rng() ** 2 * 600, 1),
      mag: nullMag ? null : round(rng() ** 2 * 7 - 0.5, 1),
      magType: rng() < 0.05 ? null : MAG_TYPES[Math.floor(rng() * MAG_TYPES.length)],
      place: `Sintético: punto ${i + 1}`,
      time: BASE_TIME_MS - i * 60000,
      country,
    }));
  }
  return makeResponse('live', features, {
    total: TRUNCATED_TOTAL,
    truncated: true,
    next_cursor: 'bW9jay1jdXJzb3Itc2ludGV0aWNv',
  });
}

/** Caso `replay`: pocas features con `metadata.mode: "replay"`. */
function buildReplay() {
  const rng = makeRng(SEED + 2);
  const features = [];
  for (let i = 0; i < 6; i += 1) {
    features.push(makeFeature({
      id: `mock-replay-${String(i + 1).padStart(3, '0')}`,
      lon: round(rng() * 360 - 180, 3),
      lat: round(rng() * 140 - 70, 3),
      depth: round(rng() * 200, 1),
      mag: round(4 + rng() * 3, 1),
      magType: 'mww',
      place: `Sintético: reproducción ${i + 1}`,
      time: REPLAY_BASE_MS - i * 86400000, // todas dentro de 2025, como un histórico
      country: COUNTRIES[i % COUNTRIES.length],
    }));
  }
  return makeResponse('replay', features);
}

/**
 * Zonas sísmicas del caso `realistic` (tomadas del mock en memoria del front externo):
 * centro, dispersión en grados y peso. `id: null` es mar abierto, sin país.
 */
const ZONES = [
  { id: 'CHL', name: 'Chile', lat: -30, lon: -71, spread: 6, w: 5 },
  { id: 'JPN', name: 'Japón', lat: 36, lon: 140, spread: 4, w: 5 },
  { id: 'IDN', name: 'Indonesia', lat: -3, lon: 118, spread: 8, w: 4 },
  { id: 'MEX', name: 'México', lat: 17, lon: -99, spread: 4, w: 3 },
  { id: 'USA', name: 'Estados Unidos', lat: 60, lon: -150, spread: 7, w: 5 },
  { id: 'GRC', name: 'Grecia', lat: 38.5, lon: 23, spread: 2.5, w: 3 },
  { id: 'ESP', name: 'España', lat: 37, lon: -3.5, spread: 1.5, w: 1 },
  { id: null, name: null, lat: -10, lon: -110, spread: 12, w: 3 },
];
const TOTAL_WEIGHT = ZONES.reduce((a, z) => a + z.w, 0);

/**
 * Caso `realistic`: unos 400 eventos por zonas, de hasta 30 días de antigüedad respecto a
 * `metadata.generated`. `backend.ts` desplaza todas las fechas para que `generated` sea «ahora».
 * Cada 50 eventos se reparten casos de borde (magnitud nula o negativa, profundidad nula o
 * negativa, `place` nulo, `magType` nulo); la zona de mar abierto da eventos sin país.
 */
function buildRealistic() {
  const rng = makeRng(SEED + 3);
  const raw = [];
  for (let i = 0; i < REALISTIC_COUNT; i += 1) {
    let pick = rng() * TOTAL_WEIGHT;
    const zone = ZONES.find((z) => (pick -= z.w) < 0) ?? ZONES[0];
    const mag = round(1 + rng() ** 2.2 * 6.5, 1);
    const depthRoll = rng();
    const ageH = rng() ** 1.6 * 720;
    const lon = round(zone.lon + (rng() - 0.5) * 2 * zone.spread, 3);
    const lat = round(Math.max(-85, Math.min(85, zone.lat + (rng() - 0.5) * 2 * zone.spread)), 3);
    const depth = round(depthRoll < 0.8 ? rng() * 60 : rng() * 600, 1);
    const magType = MAG_TYPES[Math.floor(rng() * MAG_TYPES.length)];
    const km = Math.round(5 + mag * 6);
    const edge = i % 50;
    raw.push({
      i,
      zone,
      lon,
      lat,
      time: GENERATED_MS - Math.round(ageH * HOUR_MS),
      mag: edge === 3 ? null : edge === 7 ? -0.4 : mag,
      depth: edge === 11 ? null : edge === 17 ? -0.5 : depth,
      magType: edge === 29 ? null : magType,
      place: edge === 23 ? null : `Sintético: a ${km} km de ${zone.name ?? 'mar abierto'}`,
    });
  }
  raw.sort((a, b) => b.time - a.time);
  const features = raw.map((r) => makeFeature({
    id: `mock-realistic-${String(r.i + 1).padStart(4, '0')}`,
    lon: r.lon,
    lat: r.lat,
    depth: r.depth,
    mag: r.mag,
    magType: r.magType,
    place: r.place,
    time: r.time,
    country: r.zone.id ? [r.zone.id, r.zone.name] : null,
  }));
  return makeResponse('live', features);
}

/** Caso `empty`: ninguna feature. */
function buildEmpty() {
  return makeResponse('live', []);
}

mkdirSync(OUT_DIR, { recursive: true });
const files = {
  'base.json': [buildBase(), 2],
  'truncated.json': [buildTruncated(), 0],
  'replay.json': [buildReplay(), 2],
  'empty.json': [buildEmpty(), 2],
  'realistic.json': [buildRealistic(), 0],
};
for (const [name, [data, indent]] of Object.entries(files)) {
  writeFileSync(join(OUT_DIR, name), `${JSON.stringify(data, null, indent)}\n`, 'utf8');
  console.log(`escrito mock/${name} (${data.features.length} features)`);
}
