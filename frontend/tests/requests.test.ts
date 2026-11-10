import { describe, expect, it } from 'vitest';
import { buildRequest, REPLAY_END, REPLAY_START, resolveFilters, type RequestFilters } from '@/shared/api/requests';

/** Pruebas de `requests.ts` (T038): ventana de replay, periodo en vivo y parámetros (G6, FR-014, SC-009). */
const NOW = Date.parse('2026-11-10T12:00:00.000Z');
const base: RequestFilters = { mode: 'live', hours: 24, dateFrom: '', dateTo: '', minMag: 0, country: '' };
const req = (p: Partial<RequestFilters>) => buildRequest(resolveFilters({ ...base, ...p }), NOW);

describe('requests', () => {
  it('replay usa 2025 fijo e ignora el periodo', () => {
    const r = req({ mode: 'replay', hours: 1, dateFrom: '2024-01-01', dateTo: '2024-01-02' });
    expect(r).toMatchObject({ mode: 'replay', start: REPLAY_START, end: REPLAY_END });
    expect(REPLAY_START).toBe('2025-01-01T00:00:00.000Z');
    expect(REPLAY_END).toBe('2026-01-01T00:00:00.000Z');
  });

  it('live con ventana de horas: start = ahora - horas y sin end', () => {
    const r = req({ hours: 6 });
    expect(r.start).toBe('2026-11-10T06:00:00.000Z');
    expect(r.end).toBeUndefined();
  });

  it('live con rango de fechas: end = día final + 1 día (UTC)', () => {
    const r = req({ hours: 0, dateFrom: '2026-03-01', dateTo: '2026-03-03' });
    expect(r.start).toBe('2026-03-01T00:00:00.000Z');
    expect(r.end).toBe('2026-03-04T00:00:00.000Z');
  });

  it('rango inválido, invertido o incompleto -> 24 h', () => {
    for (const p of [{ dateFrom: '2026-03-05', dateTo: '2026-03-01' }, { dateFrom: '2026-03-01', dateTo: '' }, { dateFrom: 'x', dateTo: 'y' }]) {
      const r = req({ hours: 0, ...p });
      expect(r.start).toBe('2026-11-09T12:00:00.000Z');
      expect(r.end).toBeUndefined();
    }
  });

  it('min_mag solo si es > 0', () => {
    expect(req({ minMag: 0 }).min_mag).toBeUndefined();
    expect(req({ minMag: 4.5 }).min_mag).toBe(4.5);
  });

  it('country_id solo none o tres letras', () => {
    expect(req({ country: 'CHL' }).country_id).toBe('CHL');
    expect(req({ country: 'none' }).country_id).toBe('none');
    expect(req({ country: '' }).country_id).toBeUndefined();
    expect(req({ country: 'CH' }).country_id).toBeUndefined();
    expect(req({ country: 'CHL;x' }).country_id).toBeUndefined();
  });

  it('la clave resuelta no contiene instantes (estable para la caché)', () => {
    expect(JSON.stringify(resolveFilters({ ...base, hours: 6 }))).not.toMatch(/2026/);
  });
});
