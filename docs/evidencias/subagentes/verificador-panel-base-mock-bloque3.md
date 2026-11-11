# Verificación independiente, panel-base-mock, Bloque 3 (T030-T033)

Ejecutado: `tsc --noEmit` 0 errores; `npm run build` OK; `npm test` 20/20 (2 ficheros). `grep -r __MOCK_BACKEND__ dist` y `grep -r "Sintético:" dist` vacíos. `git diff --stat` de contratos, `docs/enunciado/` y `sql/001_schema.sql`: vacío.
Script temporal propio (11 casos, borrado al terminar), todos en verde:
- T030 `requests.ts`: live 1/24/8760 h sin `end`; rango válido con `end` = día final + 1 d UTC; rango vacío, de una sola fecha o invertido da 24 h; `replay` da `2025-01-01T00:00:00.000Z` / `2026-01-01T00:00:00.000Z` ignorando periodo y fechas; `min_mag` solo si > 0; `country_id` rechaza «ES», «ESPA», «» y acepta `none`, `ESP`, `esp`.
- T030 `parse.ts`: acepta los cinco escenarios del mock en `/eventos`, `/estadisticas` y `/salud`; conserva `mag`, `magType`, `place`, profundidad y `country_*` nulos (nunca 0); acepta `url`, `status`, `sig`, `last_ingestion` y `next_cursor` nulos, y exige lo que `api.md` §3.2, §3.4, §5.1 garantiza; rechaza sin `metadata`, `features` no array, coordenadas NaN, Infinity o longitud ≠ 3, `mag` texto e `id` numérico, siempre con `ApiError` `invalid_response`. `client.ts` lee `apiBaseUrl` y `timeoutMs` de la config y mapea `{error:{code,message}}` (lectura de código).
- T031 `useObservatory` (lectura): clave con filtros resueltos sin «ahora»; `refetchInterval = refreshSeconds*1000`; `retry:false`; `keepPreviousData`; `updatedAt` = `dataUpdatedAt`; salud cada 30 s; TanStack no lanza otra consulta con una en vuelo. `deriveDataState`: `features: []` es `empty` (también en replay), error con datos previos es `error` y conserva `response`. El store no tiene `source`; `App.tsx` limpia la selección al cambiar cualquier filtro; en replay `FiltersPanel` muestra «2025» desactivado y `FiltersBar` (escritorio y móvil) rotula «2025».
- T032: mi grep de `.length`, `Math.`, `.filter(`, `.reduce(` y restas de timestamps solo halla recuentos rotulados «mostrados N · total M (API)» (total de `metadata`), «mostrados 6 de N países» y escalas de barras; todo está en `auditoria-calculos-cliente.md` (31 líneas). Retraso «hace X min (calculado en el panel)» en `FeedStatus` y `StatusBanners`; no queda «máx.» ni «+N países más».
- T033 (render con `react-dom/server`, escritorio): `truncated` da «Mostrando 5000 de 6213 eventos»; replay da REPRODUCCIÓN; replay vacío da «Sin eventos reproducidos» + REPRODUCCIÓN; live vacío da «Sin eventos en el intervalo»; ambos sin `role="alert"` ni cifras. Error con datos da «Datos antiguos» y sin datos da «Sin datos» (sin «Sin eventos»). Móvil: mismos ítems, plegados en una línea.
- Constitución: §5 sin nulos a 0; §7 sin camino al mock en `api`; §15 tipos coherentes con `api.md`; `shared/` no importa de `components/`; solo `GlobeView` importa `react-globe.gl`/`three`; rutas de `CODEMAP.md` existen; docstrings con la plantilla en lo muestreado.
Hallazgos bloqueantes o importantes: ninguno. Límite conocido: en móvil plegado solo se ve el primer aviso (en replay vacío, «REPRODUCCIÓN» +1; el texto «Sin eventos reproducidos» queda tras expandir).
Pendiente del alumno (visual, navegador): aspecto de banners, FiltersBar «2025» y lista de estadísticas en escritorio y móvil, y comportamiento del refresco contra la API real (bloque 4).

T030: verificada
T031: verificada
T032: verificada
T033: verificada
