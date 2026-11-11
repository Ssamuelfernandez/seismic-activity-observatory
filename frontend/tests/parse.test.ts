import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { mockEvents, mockHealth, mockStats, SCENARIOS } from '../mock/backend';
import { ApiError } from '@/shared/api/apiError';
import { parseEvents, parseHealth, parseStats } from '@/shared/api/parse';

/**
 * Pruebas de `parse.ts` (T038): respuestas buenas de los cinco escenarios, nulos conservados
 * y formas malas rechazadas con `ApiError` `invalid_response` (G12, FR-011, SC-009).
 */
const readJson = (rel: string) => JSON.parse(readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf8'));
const clone = <T>(v: T): T => structuredClone(v);

describe('parse: respuestas buenas', () => {
  it.each([...SCENARIOS])('%s: eventos, estadísticas y salud pasan la guarda', async (name) => {
    const ev = await mockEvents({ mode: name === 'replay' ? 'replay' : 'live' }, name);
    expect(parseEvents(ev)).toBe(ev);
    expect(parseStats(await mockStats({}, name))).toBeTruthy();
    expect(parseHealth(await mockHealth(name))).toBeTruthy();
  });
});

describe('parse: los nulos se conservan', () => {
  it('base trae nulos y salen iguales (nunca 0)', () => {
    const base = parseEvents(readJson('../mock/base.json'));
    const p = base.features.map((f) => f.properties);
    expect(p.some((x) => x.mag === null)).toBe(true);
    expect(p.some((x) => x.magType === null)).toBe(true);
    expect(p.some((x) => x.place === null)).toBe(true);
    expect(p.some((x) => x.country_id === null && x.country_name === null)).toBe(true);
    expect(base.features.some((f) => f.geometry.coordinates[2] === null)).toBe(true);
  });

  it('un evento con todos los campos anulables a null es válido', () => {
    const r = clone(readJson('../mock/base.json'));
    const f = r.features[0];
    Object.assign(f.properties, { mag: null, magType: null, place: null, country_id: null, country_name: null, status: null, url: null, sig: null });
    f.geometry.coordinates[2] = null;
    const out = parseEvents(r);
    expect(out.features[0].properties.mag).toBeNull();
    expect(out.features[0].geometry.coordinates[2]).toBeNull();
  });
});

function invalid(fn: () => unknown): ApiError {
  try {
    fn();
  } catch (e) {
    expect(e).toBeInstanceOf(ApiError);
    return e as ApiError;
  }
  throw new Error('no lanzó');
}

describe('parse: formas malas -> invalid_response', () => {
  it('no es un objeto', () => {
    expect(invalid(() => parseEvents(null)).code).toBe('invalid_response');
    expect(invalid(() => parseStats([])).code).toBe('invalid_response');
    expect(invalid(() => parseHealth('ok')).code).toBe('invalid_response');
  });

  it('eventos: tipo, metadata, geometría y nulo no permitido', () => {
    const good = readJson('../mock/base.json');
    const bad = (mut: (r: any) => void) => {
      const r = clone(good);
      mut(r);
      return invalid(() => parseEvents(r));
    };
    expect(bad((r) => (r.type = 'Otra')).code).toBe('invalid_response');
    expect(bad((r) => delete r.metadata.truncated).message).toMatch(/metadata\.truncated/);
    expect(bad((r) => (r.metadata.mode = 'otro')).message).toMatch(/metadata\.mode/);
    expect(bad((r) => (r.features[0].geometry.coordinates = [1, 2])).message).toMatch(/coordinates/);
    expect(bad((r) => (r.features[0].properties.time = null)).message).toMatch(/time/);
    expect(bad((r) => (r.features = 'x')).code).toBe('invalid_response');
  });

  it('el archivo estropeado de tests/fixtures falla', () => {
    expect(invalid(() => parseEvents(readJson('./fixtures/bad-response.json'))).code).toBe('invalid_response');
  });

  it('salud: estado distinto de ok', () => {
    expect(invalid(() => parseHealth({ status: 'down', last_ingestion: null, generated: 1 })).message).toMatch(/status/);
  });

  it('estadísticas: falta un bloque', async () => {
    const s: any = clone(await mockStats({}, 'base'));
    delete s.histograms.depth;
    expect(invalid(() => parseStats(s)).code).toBe('invalid_response');
  });
});
