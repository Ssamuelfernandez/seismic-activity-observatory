/**
 * Comprobación de conformidad de una respuesta de eventos con el contrato.
 *
 * Fuente: `specs/001-contratos-y-modelo/contracts/api.md` §3.2 (`metadata`) y
 * §3.4 (`properties`). Este módulo comprueba el contrato, no lo redefine.
 */

/** Opciones de la comprobación. */
export interface ValidateOptions {
  /** Exige `is_synthetic` verdadero e `id` con prefijo `mock-` (mock del panel). */
  requireMock?: boolean;
}

type Json = Record<string, unknown>;

const METADATA_KEYS = [
  'generated', 'last_ingestion', 'mode', 'count', 'total',
  'truncated', 'next_cursor', 'null_mag_excluded',
];
const PROPERTIES_KEYS = [
  'mag', 'magType', 'place', 'time', 'updated', 'country_id',
  'country_name', 'is_synthetic', 'status', 'url', 'sig',
];
const MOCK_ID_PREFIX = 'mock-';
const COORDINATES_LENGTH = 3;

const isObject = (v: unknown): v is Json => typeof v === 'object' && v !== null && !Array.isArray(v);
const isFiniteNumber = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isInt = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v);
const isTextOrNull = (v: unknown) => v === null || typeof v === 'string';

function sameKeys(obj: Json, expected: string[]): string | null {
  const keys = Object.keys(obj);
  const missing = expected.filter((k) => !keys.includes(k));
  const extra = keys.filter((k) => !expected.includes(k));
  if (missing.length === 0 && extra.length === 0) return null;
  return `faltan [${missing.join(', ')}] sobran [${extra.join(', ')}]`;
}

function checkMetadata(meta: unknown, featureCount: number, errors: string[]): void {
  if (!isObject(meta)) {
    errors.push('metadata: no es un objeto');
    return;
  }
  const keyProblem = sameKeys(meta, METADATA_KEYS);
  if (keyProblem) errors.push(`metadata: ${keyProblem}`);
  if (!isInt(meta.generated)) errors.push('metadata.generated: debe ser entero (ms)');
  if (meta.last_ingestion !== null && !isInt(meta.last_ingestion)) {
    errors.push('metadata.last_ingestion: debe ser entero (ms) o null');
  }
  if (meta.mode !== 'live' && meta.mode !== 'replay') errors.push('metadata.mode: debe ser live o replay');
  if (!isInt(meta.count)) errors.push('metadata.count: debe ser entero');
  else if (meta.count !== featureCount) {
    errors.push(`metadata.count (${meta.count}) distinto de features.length (${featureCount})`);
  }
  if (!isInt(meta.total)) errors.push('metadata.total: debe ser entero');
  if (typeof meta.truncated !== 'boolean') errors.push('metadata.truncated: debe ser booleano');
  if (!isTextOrNull(meta.next_cursor)) errors.push('metadata.next_cursor: debe ser texto o null');
  if (!isInt(meta.null_mag_excluded)) errors.push('metadata.null_mag_excluded: debe ser entero');
}

function checkProperties(props: unknown, where: string, opts: ValidateOptions, errors: string[]): void {
  if (!isObject(props)) {
    errors.push(`${where}.properties: no es un objeto`);
    return;
  }
  const keyProblem = sameKeys(props, PROPERTIES_KEYS);
  if (keyProblem) errors.push(`${where}.properties: ${keyProblem}`);
  if (props.mag !== null && !isFiniteNumber(props.mag)) errors.push(`${where}.mag: número finito o null`);
  if (!isTextOrNull(props.magType)) errors.push(`${where}.magType: texto o null`);
  if (!isTextOrNull(props.place)) errors.push(`${where}.place: texto o null`);
  if (!isInt(props.time)) errors.push(`${where}.time: entero (ms)`);
  if (!isInt(props.updated)) errors.push(`${where}.updated: entero (ms)`);
  if (!isTextOrNull(props.country_id)) errors.push(`${where}.country_id: texto o null`);
  if (!isTextOrNull(props.country_name)) errors.push(`${where}.country_name: texto o null`);
  if (typeof props.is_synthetic !== 'boolean') errors.push(`${where}.is_synthetic: booleano`);
  else if (opts.requireMock && props.is_synthetic !== true) errors.push(`${where}.is_synthetic: debe ser true`);
  if (!isTextOrNull(props.status)) errors.push(`${where}.status: texto o null`);
  if (!isTextOrNull(props.url)) errors.push(`${where}.url: texto o null`);
  if (props.sig !== null && !isInt(props.sig)) errors.push(`${where}.sig: entero o null`);
}

function checkGeometry(geo: unknown, where: string, errors: string[]): void {
  if (!isObject(geo) || geo.type !== 'Point' || !Array.isArray(geo.coordinates)) {
    errors.push(`${where}.geometry: debe ser un Point con coordinates`);
    return;
  }
  const [lon, lat, depth] = geo.coordinates as unknown[];
  if (geo.coordinates.length !== COORDINATES_LENGTH) errors.push(`${where}.coordinates: deben ser 3 valores`);
  if (!isFiniteNumber(lon) || !isFiniteNumber(lat)) errors.push(`${where}.coordinates: lon/lat finitos`);
  if (depth !== null && !isFiniteNumber(depth)) errors.push(`${where}.coordinates[2]: finito o null`);
}

function checkFeature(feature: unknown, index: number, opts: ValidateOptions, errors: string[]): void {
  const where = `features[${index}]`;
  if (!isObject(feature)) {
    errors.push(`${where}: no es un objeto`);
    return;
  }
  if (feature.type !== 'Feature') errors.push(`${where}.type: debe ser Feature`);
  if (typeof feature.id !== 'string' || feature.id === '') errors.push(`${where}.id: texto no vacío`);
  else if (opts.requireMock && !feature.id.startsWith(MOCK_ID_PREFIX)) {
    errors.push(`${where}.id: debe empezar por ${MOCK_ID_PREFIX}`);
  }
  checkGeometry(feature.geometry, where, errors);
  checkProperties(feature.properties, where, opts, errors);
}

/**
 * Valida una respuesta de eventos y devuelve la lista de errores.
 *
 * Qué hace:
 *     Comprueba campos, tipos, nulos permitidos, tiempos enteros, geometría
 *     `Point` finita y `count === features.length`; con `requireMock`, además
 *     `is_synthetic` verdadero e `id` con prefijo `mock-`.
 * Recibe:
 *     data: el JSON ya parseado.
 *     opts: opciones (por defecto ninguna).
 * Devuelve:
 *     Lista de mensajes de error; vacía si la respuesta es conforme.
 * Por qué existe:
 *     Garantiza que el mock tiene la forma del contrato (G15, FR-010).
 */
export function validateEventsResponse(data: unknown, opts: ValidateOptions = {}): string[] {
  const errors: string[] = [];
  if (!isObject(data)) return ['raíz: no es un objeto'];
  if (data.type !== 'FeatureCollection') errors.push('type: debe ser FeatureCollection');
  const features = Array.isArray(data.features) ? data.features : null;
  if (features === null) errors.push('features: debe ser una lista');
  checkMetadata(data.metadata, features ? features.length : -1, errors);
  (features ?? []).forEach((f, i) => checkFeature(f, i, opts, errors));
  return errors;
}
