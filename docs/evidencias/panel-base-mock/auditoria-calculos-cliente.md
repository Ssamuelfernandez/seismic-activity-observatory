# Auditoría de cálculos en el cliente (T032, lista FINAL)

Fecha: 2026-11-10 · Feature `panel-base-mock` · Sobre el código real de `frontend/src/` (FR-029, SC-011, constitución §17).
Búsqueda: `length`, `reduce`, `Math.`, restas de timestamps, `filter`, `some`, `Date.now()` y `.count` en `src/components`, `src/shared`, `src/store` (salida de los `grep` en `T032_greps.txt`). No hay ningún `reduce` ni suma de recuentos.

Criterio: el cliente no calcula estadísticas. Lo que cuenta él se rotula «mostrados»; los totales salen de `metadata` o `stats`; formatear un timestamp o escalar una barra no es estadística.

| # | Dónde | Qué calcula | Veredicto | Acción tomada |
|---|---|---|---|---|
| 1 | `RecentEvents.tsx` | Filas listadas (`recent.length`) | Recuento propio | Rotulado `mostrados N · total M (API)` (M = `metadata.total`; sin `metadata` solo «mostrados N») |
| 2 | `EventsTable.tsx` | `events.length` | Recuento propio | Rotulado `mostrados N · total M (API)` |
| 3 | `MobileEventsList.tsx` | `events.length` | Recuento propio | Rotulado `Todos · mostrados N · total M (API)` |
| 4 | `StatsPanel.tsx` | Países pintados (6) frente a los de la API (`items.length`) | Longitud de listas | Rotulado `mostrados 6 de N países` (N = elementos que entrega la API) |
| 5 | `StatsPanel.tsx` | `máx. {maxHour}` | Derivado de cifras de la API | **Quitado** el rótulo; la barra sigue escalando |
| 6 | `StatsPanel.tsx` | Alturas/anchos de barras (`count / max`, `Math.max`) en histogramas, por hora y por país | Escala visual de recuentos de la API | Aceptado |
| 7 | `feedHealth.ts` → `FeedStatus`, `StatusBanners` | Retraso de ingesta = `generated − last_ingestion` de `/salud` y umbral 300 s | Diferencia de timestamps de la API | **Aceptado (P3)**: se rotula «hace X min (calculado en el panel)» en el desplegable del estado y «…hace X min (calculado en el panel: respuesta generada − última ingesta)» en el aviso de desactualizado; sin cambio de contrato |
| 8 | `FeedStatus.tsx` | `formatAge(now − last_ingestion)` («Última ingesta hace…») | Formato relativo con el reloj del navegador | Aceptado (formatear un timestamp) |
| 9 | `StatusBanners.tsx` | `formatAge(now − updatedAt)` | Hora de la última consulta propia del panel | Aceptado |
| 10 | `requests.ts` (antes en `useObservatory`) | `start = ahora − horas`; `end = día final + 1 d` | Construcción de la petición | Aceptado; ahora función pura con «ahora» inyectado |
| 11 | `GlobeView.tsx` | Filtrar anillos y etiquetas por magnitud; alturas por magnitud | Selección visual; los nulos ya no pasan a 0 (T026) | Aceptado |
| 12 | `RecentEvents`, `EventsTable`, `MobileEventsList` | Ordenar por fecha o columna; `slice(0, 12)` | Presentación | Aceptado (la lista dice «mostrados») |
| 13 | `FeedStatus.tsx` | `Mostrados {count} de {total}` | Valores de `metadata` | Aceptado (vienen de la API) |
| 14 | `StatsPanel.tsx` | `stats.total`, `n_recent`, `variation_pct`, `diff_abs`, etc. | Valores de la API | Aceptado (solo se formatean) |
| 15 | `mock/backend.ts` | Filtros y estadísticas del servidor simulado | Es el servidor | Aceptado **solo** fuera de `src/` y del build de producción (T029; `grep` en `dist/` sin resultados) |
| 16 | `StatusBanners.tsx` | `items.length`, `items.length − 1` («+N» del aviso móvil) | Cuenta de avisos de interfaz, no de datos | Aceptado |
| 17 | `StatusBanners.tsx` | `Mostrando {count} de {total} eventos` (truncado) | Valores de `metadata` | Aceptado (nuevo en T033; no calcula) |
| 18 | `App.tsx`, `MobileLayout.tsx` | `events.some(is_synthetic)` | Indicador booleano para el aviso de sintéticos | Aceptado (no es recuento) |
| 19 | `FiltersPanel.tsx`, `useCountries.ts` | `filter` del buscador de países y del catálogo; `Date.now()` para proponer fechas | Interfaz de filtros, no estadística | Aceptado |
| 20 | `useObservatory.ts` | `deriveDataState`: `features.length === 0` → `empty` | Distingue vacío de error; no se muestra como cifra | Aceptado |

Resultado: no queda ningún recuento propio sin «mostrados»; todo total visible (`total`, `count`, `stats.total`, histogramas, por país) sale de `metadata` o `stats`. Límite conocido: el panel de países pinta 6 de los N que entrega la API (rotulado).
