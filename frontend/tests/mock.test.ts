import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import type { EventsResponse } from '@/shared/types/contract';
import { validateEventsResponse } from './support/validateEventsResponse';

const read = (rel: string): EventsResponse =>
  JSON.parse(readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf8'));

const mock = (name: string) => read(`../mock/${name}.json`);
const CASES = ['base', 'truncated', 'replay', 'empty', 'realistic'];

describe('conformidad del mock con api.md', () => {
  it.each(CASES)('%s cumple el contrato', (name) => {
    expect(validateEventsResponse(mock(name), { requireMock: true })).toEqual([]);
  });

  it('el 100 % de las features es sintético con id mock- y place Sintético:', () => {
    for (const name of CASES) {
      for (const f of mock(name).features) {
        expect(f.properties.is_synthetic).toBe(true);
        expect(f.id.startsWith('mock-')).toBe(true);
        if (f.properties.place !== null) expect(f.properties.place.startsWith('Sintético:')).toBe(true);
      }
    }
  });

  it('el archivo estropeado falla', () => {
    const errors = validateEventsResponse(read('./fixtures/bad-response.json'), { requireMock: true });
    expect(errors.length).toBeGreaterThan(0);
    expect(errors.join('\n')).toMatch(/metadata.mode/);
    expect(errors.join('\n')).toMatch(/count/);
    expect(errors.join('\n')).toMatch(/is_synthetic/);
  });

  it('un nulo donde no se permite se detecta', () => {
    const data = mock('base');
    (data.features[0].properties as unknown as Record<string, unknown>).time = null;
    expect(validateEventsResponse(data).join()).toMatch(/time/);
  });
});

describe('casos del mock (FR-008)', () => {
  it('base: unas 30 features con los casos límite', () => {
    const f = mock('base').features;
    expect(f.length).toBe(30);
    const has = (fn: (e: (typeof f)[number]) => boolean) => f.some(fn);
    expect(has((e) => e.properties.mag === null)).toBe(true);
    expect(has((e) => e.geometry.coordinates[2] === null)).toBe(true);
    expect(has((e) => (e.properties.mag ?? 0) < 0)).toBe(true);
    expect(has((e) => (e.geometry.coordinates[2] ?? 0) < 0)).toBe(true);
    expect(has((e) => e.properties.country_id === null && e.properties.country_name === null)).toBe(true);
    expect(has((e) => e.properties.magType === null)).toBe(true);
    expect(has((e) => e.properties.place === null)).toBe(true);
    expect(new Set(f.map((e) => e.properties.magType).filter(Boolean)).size).toBeGreaterThanOrEqual(3);
    const d = f.map((e) => e.geometry.coordinates[2]).filter((x): x is number => x !== null);
    expect(d.some((x) => x < 10)).toBe(true);
    expect(d.some((x) => x >= 10 && x < 35)).toBe(true);
    expect(d.some((x) => x >= 35 && x < 70)).toBe(true);
    expect(d.some((x) => x >= 70 && x < 300)).toBe(true);
    expect(d.some((x) => x >= 300)).toBe(true);
  });

  it('truncated: 5000 features, total 6213, truncado y cursor', () => {
    const m = mock('truncated');
    expect(m.features.length).toBe(5000);
    expect(m.metadata).toMatchObject({ count: 5000, total: 6213, truncated: true });
    expect(m.metadata.next_cursor).not.toBeNull();
  });

  it('replay y empty', () => {
    expect(mock('replay').metadata.mode).toBe('replay');
    expect(mock('replay').features.length).toBeGreaterThan(0);
    expect(mock('empty').features).toEqual([]);
    expect(mock('empty').metadata.count).toBe(0);
  });
});
