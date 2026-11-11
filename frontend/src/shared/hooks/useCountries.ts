import { useQuery } from '@tanstack/react-query';
const landUrl = '/datos/paises.geojson';

export interface CountryOption {
  /** `ADM0_A3`, el mismo código que usa la API en `country_id`. */
  id: string;
  /** `NAME_ES`, el mismo nombre que devuelve la API en `country_name`. */
  name: string;
}

/**
 * Qué hace:
 *     Lee la lista de países de /datos/paises.geojson y la ordena por nombre.
 * Recibe:
 *     Nada.
 * Devuelve:
 *     La lista de opciones de país (vacía mientras carga).
 * Por qué existe:
 *     Alimenta el filtro de país con el mismo catálogo que el globo (G6, G14).
 */
export function useCountries(): CountryOption[] {
  const { data } = useQuery({
    queryKey: ['countries'],
    staleTime: Infinity,
    queryFn: async (): Promise<CountryOption[]> => {
      const res = await fetch(landUrl);
      const geo = (await res.json()) as { features: { properties: { ADM0_A3?: string; NAME_ES?: string; NAME?: string } }[] };
      return geo.features
        .map((f) => ({ id: f.properties.ADM0_A3 ?? '', name: f.properties.NAME_ES ?? f.properties.NAME ?? '' }))
        .filter((c) => /^[A-Z]{3}$/.test(c.id) && c.name)
        .sort((a, b) => a.name.localeCompare(b.name, 'es'));
    },
  });
  return data ?? [];
}
