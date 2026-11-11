import { describe, expect, it } from 'vitest';
import { colorByDepth, colorByMag, colorForEvent, depthClassFor, DEPTH_CLASSES, heightFor, ND_GRAY } from '@/shared/lib/symbology';

/** Pruebas de `symbology.ts` (T038): cinco clases de profundidad, altura y color ND (G2, SC-005, SC-006). */
const idx = (d: number | null) => {
  const c = depthClassFor(d);
  return c === null ? null : DEPTH_CLASSES.indexOf(c) + 1;
};

describe('clases de profundidad', () => {
  it.each([
    [9.99, 1], [10, 2], [10.01, 2],
    [34.99, 2], [35, 3], [35.01, 3],
    [69.99, 3], [70, 4], [70.01, 4],
    [299.99, 4], [300, 5], [300.01, 5],
    [0, 1], [-1, 1], [-50, 1], [700, 5],
  ])('%s km -> clase %i', (d, expected) => {
    expect(idx(d)).toBe(expected);
  });

  it('profundidad nula -> ND (sin clase y gris)', () => {
    expect(depthClassFor(null)).toBeNull();
    expect(colorByDepth(null)).toBe(ND_GRAY);
  });

  it('hay cinco clases con color distinto', () => {
    expect(DEPTH_CLASSES).toHaveLength(5);
    expect(new Set(DEPTH_CLASSES.map((c) => c.color)).size).toBe(5);
  });
});

describe('altura y color por magnitud', () => {
  it('heightFor: nula, negativa y 0 dan la mínima; 8 es el tope', () => {
    expect(heightFor(null)).toBe(0.01);
    expect(heightFor(-1)).toBe(0.01);
    expect(heightFor(0)).toBe(0.01);
    expect(heightFor(8)).toBeCloseTo(0.1);
    expect(heightFor(9.5)).toBe(heightFor(8));
    expect(heightFor(5)).toBeGreaterThan(heightFor(3));
  });

  it('magnitud nula -> gris ND (no el color de M 0)', () => {
    const e = (mag: number | null) => ({ properties: { mag }, geometry: { coordinates: [0, 0, 5] as [number, number, number | null] } });
    expect(colorByMag(null)).toBe(ND_GRAY);
    expect(colorForEvent(e(null), 'depth')).toBe(ND_GRAY);
    expect(colorForEvent(e(null), 'mag')).toBe(ND_GRAY);
    expect(colorForEvent(e(4), 'depth')).toBe(DEPTH_CLASSES[0].color);
  });
});
