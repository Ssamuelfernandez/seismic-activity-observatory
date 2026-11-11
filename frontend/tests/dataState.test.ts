import { describe, expect, it } from 'vitest';
import { deriveDataState } from '@/shared/lib/dataState';

/** Pruebas de `deriveDataState` (T038): un error no es «0 eventos» y `features: []` no es un error (G9). */
describe('deriveDataState', () => {
  it('estados', () => {
    expect(deriveDataState(null, false)).toBe('loading');
    expect(deriveDataState(0, false)).toBe('empty');
    expect(deriveDataState(12, false)).toBe('ready');
    expect(deriveDataState(null, true)).toBe('error');
    expect(deriveDataState(12, true)).toBe('error');
  });
});
