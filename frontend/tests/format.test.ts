import { describe, expect, it } from 'vitest';
import {
  formatCountry,
  formatDecimal,
  formatFixed,
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

describe('formatFixed', () => {
  it('redondea a dos decimales con coma', () => {
    expect(formatFixed(50.14246575342466)).toBe('50,14');
    expect(formatFixed(13)).toBe('13,00');
  });

  it('usa el signo menos tipografico y no deja -0,00', () => {
    expect(formatFixed(-37.14246575342466)).toBe('\u221237,14');
    expect(formatFixed(-0.001)).toBe('0,00');
  });

  it('muestra ND para nulo', () => {
    expect(formatFixed(null)).toBe('ND');
    expect(formatFixed(undefined)).toBe('ND');
    expect(formatFixed(Number.NaN)).toBe('ND');
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
