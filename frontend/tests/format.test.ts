import { describe, expect, it } from 'vitest';
import {
  formatCountry,
  formatDecimal,
  formatMagnitude,
  formatPlace,
  formatUtc,
} from '@/shared/lib/format';

describe('formatDecimal', () => {
  it('muestra ND para nulo y nunca 0', () => {
    expect(formatDecimal(null)).toBe('ND');
    expect(formatDecimal(undefined)).toBe('ND');
    expect(formatDecimal(null)).not.toBe('0');
  });

  it('usa coma decimal y signo menos tipografico', () => {
    expect(formatDecimal(-0.06)).toBe('\u22120,06');
    expect(formatDecimal(5.4)).toBe('5,4');
    expect(formatDecimal(0)).toBe('0');
  });
});

describe('formatUtc', () => {
  it('formatea ms conocidos en UTC', () => {
    expect(formatUtc(1793536750750)).toBe('2026-11-01 12:39 UTC');
    expect(formatUtc(0)).toBe('1970-01-01 00:00 UTC');
  });

  it('da ND si falta', () => {
    expect(formatUtc(null)).toBe('ND');
  });
});

describe('textos fijos', () => {
  it('sin pais y sin descripcion', () => {
    expect(formatCountry(null)).toBe('Sin país asignado');
    expect(formatCountry('Chile')).toBe('Chile');
    expect(formatPlace(null)).toBe('Sin descripción');
  });

  it('magnitud con su tipo y ND en lo que falte', () => {
    expect(formatMagnitude(5.4, 'mww')).toBe('Magnitud 5,4 (mww)');
    expect(formatMagnitude(5.4, null)).toBe('Magnitud 5,4 (ND)');
    expect(formatMagnitude(null, 'ml')).toBe('Magnitud ND (ml)');
  });
});
