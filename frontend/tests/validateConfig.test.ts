import { describe, expect, it } from 'vitest';
import { validateConfig } from '@/shared/lib/validateConfig';

/** Pruebas de `validateConfig.ts` (T038): cada caso de data-model.md devuelve el campo que falla (G15, FR-004). */
const ok = { mode: 'api', apiBaseUrl: '/api', refreshSeconds: 60, timeoutMs: 15000 };
const field = (patch: Record<string, unknown>) => {
  const r = validateConfig({ ...ok, ...patch });
  return r.ok ? null : r.field;
};

describe('validateConfig', () => {
  it('una config buena se devuelve tal cual', () => {
    expect(validateConfig(ok)).toEqual({ ok: true, config: ok });
  });

  it('mode inválido o ausente', () => {
    expect(field({ mode: 'otro' })).toBe('mode');
    expect(field({ mode: undefined })).toBe('mode');
  });

  it('apiBaseUrl en modo api: vacío, sin / ni http(s)://', () => {
    expect(field({ apiBaseUrl: '' })).toBe('apiBaseUrl');
    expect(field({ apiBaseUrl: 'api' })).toBe('apiBaseUrl');
    expect(field({ apiBaseUrl: 'ftp://x' })).toBe('apiBaseUrl');
    expect(field({ apiBaseUrl: undefined })).toBe('apiBaseUrl');
    expect(field({ apiBaseUrl: 'http://localhost:8000/api' })).toBeNull();
    expect(field({ apiBaseUrl: 'https://x.org' })).toBeNull();
  });

  it('apiBaseUrl vacío es válido en modo mock', () => {
    expect(field({ mode: 'mock', apiBaseUrl: '' })).toBeNull();
  });

  it.each(['refreshSeconds', 'timeoutMs'])('%s: 0, negativo, decimal, texto y ausente', (k) => {
    for (const v of [0, -5, 1.5, '60', undefined]) expect(field({ [k]: v })).toBe(k);
  });

  it('no es un objeto', () => {
    expect(validateConfig(null)).toMatchObject({ ok: false, field: 'config' });
    expect(validateConfig([])).toMatchObject({ ok: false, field: 'config' });
  });
});
