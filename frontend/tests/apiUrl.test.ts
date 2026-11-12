import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { apiEvents, apiHealth, apiStats } from '@/shared/api/client';
import { setConfig } from '@/shared/api/runtimeConfig';
import { validateConfig } from '@/shared/lib/validateConfig';

/** Pruebas de T064 (G13, FR-006, FR-009): URLs finales del cliente real con el `config.json` entregado. */
const raw = readFileSync(new URL('../public/config.json', import.meta.url), 'utf-8');
const parsed: unknown = JSON.parse(raw);
const PUBLIC_BASE = 'https://observatorio-api.ssamuelfernandez.net/api';

afterEach(() => vi.unstubAllGlobals());

/** Sustituye `fetch` por un doble que registra la URL y devuelve un 500 (basta con ver la URL pedida). */
function stubFetch(): string[] {
  const urls: string[] = [];
  vi.stubGlobal('fetch', async (url: string) => {
    urls.push(url);
    return new Response('{}', { status: 500 });
  });
  return urls;
}

describe('config.json entregado', () => {
  it('lo acepta validateConfig y trae modo api con la URL pública exacta', () => {
    const r = validateConfig(parsed);
    expect(r.ok).toBe(true);
    expect(parsed).toMatchObject({ mode: 'api', apiBaseUrl: PUBLIC_BASE });
    expect(PUBLIC_BASE.endsWith('/')).toBe(false);
  });

  it('no contiene claves de tipo token o secreto', () => {
    const keys = Object.keys(parsed as Record<string, unknown>).join(' ');
    expect(keys).not.toMatch(/token|secret|secreto|password|key/i);
  });
});

describe('URLs del cliente real', () => {
  it('apiEvents, apiStats y apiHealth piden base + ruta, sin /api/api', async () => {
    const r = validateConfig(parsed);
    if (!r.ok) throw new Error('config.json inválido');
    setConfig(r.config);
    const urls = stubFetch();
    await Promise.allSettled([apiEvents({} as never), apiStats({} as never), apiHealth()]);
    expect(urls).toEqual([`${PUBLIC_BASE}/eventos`, `${PUBLIC_BASE}/estadisticas`, `${PUBLIC_BASE}/salud`]);
    expect(urls.some((u) => u.includes('/api/api'))).toBe(false);
  });
});
