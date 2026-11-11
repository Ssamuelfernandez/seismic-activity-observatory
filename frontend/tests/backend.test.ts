import { describe, expect, it } from 'vitest';
import { mockEvents, mockStats, resolveScenario } from '../mock/backend';

/** Pruebas mínimas del servidor simulado (T038): filtros de `realistic` e histograma de profundidad de cinco tramos. */
describe('mock/backend', () => {
  it('escenario desconocido -> base', () => {
    expect(resolveScenario('xx')).toBe('base');
    expect(resolveScenario(null)).toBe('base');
    expect(resolveScenario('realistic')).toBe('realistic');
  });

  it('realistic: min_mag y country_id filtran y el total coincide con las estadísticas', async () => {
    const start = new Date(Date.now() - 7 * 864e5).toISOString();
    const all = await mockEvents({ start }, 'realistic');
    const f = { start, min_mag: 4, country_id: 'CHL' };
    const some = await mockEvents(f, 'realistic');
    expect(some.metadata.total).toBeLessThan(all.metadata.total);
    for (const e of some.features) {
      expect(e.properties.mag).not.toBeNull();
      expect(e.properties.mag as number).toBeGreaterThanOrEqual(4);
      expect(e.properties.country_id).toBe('CHL');
    }
    expect((await mockStats(f, 'realistic')).total).toBe(some.metadata.total);
  });

  it('el histograma de profundidad tiene cinco tramos con los cortes 10/35/70/300', async () => {
    const s = await mockStats({}, 'base');
    const b = s.histograms.depth.bins;
    expect(b).toHaveLength(5);
    expect(b.map((x) => x.lower)).toEqual([null, 10, 35, 70, 300]);
    expect(b.map((x) => x.upper)).toEqual([10, 35, 70, 300, null]);
  });
});
