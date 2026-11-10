# Inventario del front externo (`globo-lab`)

**Fecha**: 2026-11-09. **Origen**: `_import-front/globo-lab/` (carpeta ignorada por git; repositorio propio sin commits). **Criterio del alumno**: este front es **como quiere que quede**; lo que difiere de la spec se hizo a propósito. Este documento **apunta las diferencias** para decidir después qué cambia la spec y qué cambia el código. No se ha modificado ni `spec.md`, ni `plan.md`, ni `tasks.md`, ni nada de `frontend/`.

## 1. Qué es

Panel completo (globo, filtros, tabla, estadísticas, comparación, estado del feed, avisos de fallo, layout móvil). Stack igual que `frontend/` (React 19.3.1, Vite 8.3.6, TypeScript 6.0.3, Tailwind 4.3.4, Vitest 5.1.0, TanStack Query 5.106.1, `react-globe.gl` 2.38.0, Node 24.18.0), más `zustand` 5.0.8, `three` 0.187.0 y `h3-js` 4.5.0.

Comprobado hoy en la carpeta: `tsc --noEmit` sale con 0 y `vitest run` pasa 12 de 12 (solo hay pruebas de `format.ts`). Tamaño del código fuente: unos 45 archivos en `src/`; `GlobeView.tsx` pesa 22 KB. Su propia bitácora (`BITACORA.md`) cuenta la historia y los pendientes.

**No importar**: `node_modules/`, `dist/`, `.git/`, `.claude/settings.json` (permisos propios del otro proyecto), `prototipo-mapa/` (dentro hay builds de más de 10 MB; es el prototipo que ya se borró de `frontend/`) y `package-lock.json` (se regenera).

## 2. Qué parte de la 008 cubre y qué es de otras features

| Pieza del front externo | Tarea 008 equivalente | Estado |
|---|---|---|
| `shared/types/contract.ts` | T002 (ya hecha) | Igual y ampliado con estadísticas, salud y `ApiFilters` (api.md §4-§5). |
| `shared/lib/format.ts` | T002 (ya hecha) | Copia de la nuestra, con `formatFixed`, `formatAge`, `formatUtcTime`, `seconds` y `formatMadrid*` (sin uso, ver 4.9). |
| `tests/support/validateEventsResponse.ts`, `fixtures/bad-response.json` | T004 (ya hecha) | Iguales; **falta `mock.test.ts`** porque ya no hay JSON de mock. |
| `index.css` (`@theme`), `AppShell`, `Legend`, `EventCard`, `GlobeView`, `App`, `symbology.ts`, `appearance.ts` | T023, T014, T013, T015, T016, T010 | Cubiertas, con diferencias (sección 4). |
| `mobile/*`, `useMediaQuery` | T017 | Cubierta de otra forma (4.7). |
| `StatusBanners`, `FeedStatus`, `feedHealth.ts` | T011 (parcial) y feature de estado (G10-G12) | Mucho más de lo que pide la 008. |
| `FiltersBar`, `FiltersPanel`, `store/filters.ts`, `EventsTable`, `RecentEvents`, `useCountries` | `009-panel-filtros-tabla` | **Fuera del alcance** (SC-014, FR-006). |
| `StatsPanel`, `StatsDrawer` | `010` (gráficos y comparación) | **Fuera del alcance.** |
| `shared/api/client.ts`, `hooks/useObservatory.ts`, timeouts, refresco | `panel-conexion-api` (T009 solo la rama mock) | **Fuera del alcance.** |
| Modo `replay` y su aviso en `StatusBanners` | feature `replay` | **Fuera del alcance** (P2). |
| No existe | T008 (config en tiempo de ejecución con validación), T012 (script `copy-countries.mjs`), T018-T021 (evidencias, README, cierre) | Sin hacer. |

Consecuencia: el front externo cubre de un golpe lo que el roadmap reparte en 008, 009, 010, 011, replay y conexión con la API. La spec 008 (alcance cerrado, SC-014) y la constitución §19 (una feature cada vez) chocan con traerlo entero. Es la decisión nº 1 de la sección 6.

## 3. Lo que coincide con la spec

- Nulos como «ND», nunca 0; «Sin país asignado»; «Sin descripción»; coma decimal; signo menos tipográfico; fechas en UTC (`format.ts`, mismas reglas que T002).
- Ficha con `magType` («Magnitud 5,4 (mww)»), `time` y `updated` en UTC, país, enlace solo si hay `url`, etiqueta de sintético.
- Un prisma por evento con largo = máx(0,010; 0,0125 × M acotada a 8) (V1) y ND gris con altura mínima (V3, V4). Gris ND `#8a93a0`.
- Antártida (`ADM0_A3 = ATA`) excluida de la capa de tierra. `paises.geojson` **idéntico** al del repo (SHA-256 `6866c877…c977f`).
- `GlobeView` aislado; solo él importa `react-globe.gl` y `three`. Estadísticas desde la API (`/api/estadisticas`), no calculadas en el cliente (salvo lo de 5.2).
- Selección por el pilar más cercano al clic con `getScreenCoords` y tolerancia de 18 px: es, de hecho, la opción A de **P9**.
- Identificadores en inglés y comentarios en español. Sin Dockerfile ni despliegue.
- Tokens HUD con el naranja `#ff7a1a` como acento.

## 4. Diferencias con la spec (hechas a propósito, a confirmar)

| Nº | Tema | Spec 008 | Front externo |
|---|---|---|---|
| 4.1 | Configuración | `public/config.json` en **tiempo de ejecución**, cuatro campos (`mode`, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`), validada, con pantalla de error que nombra el campo (FR-003, FR-004, SC-011) | `src/config.json` **compilado** con otros campos (`apiBaseUrl`, `dataSource`, `staleThresholdSeconds`, `refreshIntervalSeconds`, `requestTimeoutSeconds`). Cambiarlo exige recompilar; sin validación. Su bitácora ya avisa de poner la URL real antes del build. |
| 4.2 | Origen de datos | El mock vive en `frontend/mock/*.json` (cuatro casos, `?scenario=`); en modo `api` no se cae al mock | Mock **en memoria** (`shared/api/mock.ts`, 420 eventos con semilla, fechas relativas a «ahora», filtra y calcula estadísticas como si fuera el servidor). El usuario cambia entre mock/live/replay en la interfaz (`source` y `mode` dentro del store de filtros). Por defecto `api`. |
| 4.3 | Casos del mock (FR-008) | Magnitud nula, profundidad nula, magnitud y profundidad negativas, `place` nulo, `magType` nulo, `truncated` (5 000), `replay`, `empty` | El mock **no genera** magnitud nula, magnitud/profundidad negativas ni `place` nulo; `url` siempre nula; el truncado y el vacío solo salen por filtros. `place` termina en «(mock)» en vez de empezar por «Sintético:». Faltan los casos de borde que la spec usa para probar. |
| 4.4 | Profundidad (V2) | Cinco clases con cortes 10/35/70/300 y rampa cálida; mismos cortes que los histogramas de la API (`api.md` §5.1) | **Tres** clases con nombre: Superficial < 70, Intermedio 70-300, Profundo ≥ 300 (`#ffd23f`, `#ff5a36`, `#b04cff`). La rampa cálida de cinco colores existe pero se usa para un modo «color por magnitud». El mock genera el histograma de profundidad con cortes 10/70/300 (cuatro tramos), distinto del contrato (cinco). |
| 4.5 | Globo (FR-011, FR-012, diseno-visual §7) | Fondo negro sin atmósfera ni textura; continentes en **celdas hexagonales**; prisma de **6** caras, radio 0,45° | Fondo `#070a0e`, atmósfera blanca, retícula, **grano** de fondo y luces; continentes como **países extruidos** (`landMode: 'polygons'`; la rama hex existe y no se usa); prisma de **7** lados, radio 0,2; altura × 3,7. Extras: anillos pulsantes desde M ≥ 4, opacidad por antigüedad, etiquetas M ≥ 5, giro automático, enfoque con atenuación del resto, cámara que se desplaza al elegir un evento, tooltip al pasar el ratón, modos de color `depth`/`mag`/`single`. Los anillos estaban **fuera** por decisión del alumno (2026-11-06); ahora entran. |
| 4.6 | Esqueleto (FR-020, diseno-visual §3) | Cabecera, globo, **dos columnas reservadas «RESERVADO»**, panel lateral de ficha de 20 rem con borde | Sin cabecera ni marcos reservados. Izquierda: leyenda + eventos recientes + «ver todos» (tabla). Centro arriba: barra de filtros y avisos. Derecha: estado del feed y ficha **sin caja**. Abajo: cajón de estadísticas. |
| 4.7 | Responsive (FR-018, V7) | Columnas desde 1024; ficha en cajón inferior < 768 y panel lateral ≥ 768 | Un solo corte a **1024 px**: por debajo se monta `MobileLayout` entero (hojas inferiores opacas para eventos, estadísticas y leyenda; ficha en hoja; lista de tarjetas). Entre 768 y 1023 px se ve el diseño móvil. No toca el diseño de escritorio (restricción del alumno). |
| 4.8 | Ficha | Cerrar con botón o **Esc**; botón «Ver en mapa 2D» siempre visible (FR-021); controles ≥ 44 px | Se **cierra sola** a los 10 s en escritorio (no en móvil); sin cierre con Esc en la ficha; **no hay** botón «Ver en mapa 2D»; el botón de cerrar es un «✕» sin tamaño táctil. Añade `status` y `sig`. |
| 4.9 | Fechas | UTC (spec y constitución §3) | UTC en pantalla. Quedan `formatMadrid` y `formatMadridTime` sin uso (y un test de `formatMadrid`): su bitácora los marca para borrar. |
| 4.10 | Leyenda (FR-015) | Ejemplos M 2, 4, 6; «ND: sin magnitud» y «ND: sin profundidad» por separado | Ejemplos M 2, 4, 6, 8; un único «ND»; añade ondas y degradado de antigüedad. |
| 4.11 | Estructura de `src/` (D3, opción C) | `config/`, `api/`, `store/`, `features/<x>/{components,hooks,lib}`, `shared/` | `components/` plano (con `mobile/`), `shared/{api,hooks,lib,types}`, `store/`. No hay `features/` ni `config/`. |
| 4.12 | Tokens (`@theme`) | Nombres de `diseno-visual.md`: `hud-surface`, `hud-text-dim`, `hud-nd`, `depth-1…5`, tamaños, `--size-touch`, etc. | Otros nombres: `hud-panel`, `hud-dim`, añade `hud-ok` y `hud-bad`; **faltan** `depth-*`, `hud-nd` y los tokens de tamaño. Hay hexadecimales fuera de `@theme` (`appearance.ts`, `symbology.ts`, `tokens.ts`, tooltip del globo); SC-016 lo prohíbe salvo las constantes de profundidad. |
| 4.13 | Estilo (diseno-visual §1) | Sin sombras, degradados ni esquinas redondeadas; etiquetas de 11 px y datos de ≥ 14 px | Usa `text-shadow`, degradados y `rounded-full`; hay textos de 9 y 10 px. |
| 4.14 | Atribución (FR-016, SC-010) | Línea **permanente** abajo a la derecha: Natural Earth, librería del globo y «Fondo: negro, sin textura» | Solo «Sismos: USGS · Fronteras: Natural Earth» en 9 px **dentro del desplegable** del estado del feed. Falta la librería y el fondo; no se ve sin pulsar. |
| 4.15 | Tests (SC-013) | Pruebas de `heightFor`, clases de profundidad, rampa (SC-016), `format`, mock | Solo `format.test.ts` (12). Sin pruebas de simbología, mock, cliente ni hooks. |
| 4.16 | Dependencias | `three` y `h3-js` declarados si se importan (nota de T015) | `three` se importa; **`h3-js` está declarado y no se importa** en `src/`. `zustand` sí se usa (store de filtros, que la spec posponía a 009). |

## 5. Puntos que chocan con la constitución o con el enunciado

1. **§7 / §17, datos sintéticos en el build de producción.** El mock (con filtrado y estadísticas propias) va dentro del bundle y se activa desde la interfaz. Está etiquetado (`is_synthetic` y aviso en `StatusBanners`), pero un visitante puede ver estadísticas sintéticas con la API real configurada. La spec lo evitaba con `config.json` y sin mezcla.
2. **§17, cifras que se calculan en el cliente.** El panel cuenta eventos en `RecentEvents` («N de M») y `EventsTable` («N eventos») en lugar de mostrar `metadata.count` y `total` (spec, Clarifications); calcula «+N países más» y los minutos de retraso (`generated − last_ingestion`, umbral `staleThresholdSeconds` en el cliente). Son recuentos de lo mostrado y un indicador de estado, no estadísticas de negocio, pero la spec dice «el frontend no cuenta, no agrupa ni promedia». A decidir.
3. **§5, `magOf = mag ?? 0`** en `GlobeView` para decidir qué eventos llevan anillo o etiqueta. No se muestra un 0, pero sí se trata un nulo como 0 al filtrar. Mejor excluir explícitamente los nulos.
4. **Enunciado, replay** (`FAQ-ALUMNADO.md:496`). En `mode=replay` el panel pide la misma ventana relativa (últimas 24 h desde ahora, o el rango de fechas elegido). Los eventos reproducidos conservan su fecha original, así que con esa ventana **no se ven**; el aviso «sin datos de reproducción» sigue pendiente en su bitácora. Es el síntoma que comentabas antes.
5. **G16 (accesibilidad)**: foco de teclado visible y no depender solo del color están **aparcados** (su bitácora, punto 3). La spec lo da como contexto para 009 (FR-017, FR-019), no como cierre de 008.
6. **Reglas del repo**: faltan docstrings con la plantilla de 03 §7.4 (solo `format.ts` los tiene) y no hay evidencias ni `CODEMAP.md` para nada de esto.

## 6. Decisiones que necesito del alumno

1. **Alcance.** (a) El front externo pasa a ser el objetivo de todo el panel y se reparte por features (008 solo el globo, la ficha, la leyenda y el esqueleto; el resto entra en 009, 010, 011, replay y conexión con la API, ya diseñado y listo para portar); o (b) se amplía la spec 008 para que cubra todo y se actualizan spec, plan y tareas. La opción (a) respeta la constitución §19 y el alcance cerrado (§12); la (b) hay que decidirla de forma expresa.
2. **Para cada fila de la sección 4**: «el front manda» (se reescribe la spec) o «la spec manda» (se corrige el código). Mi lectura de lo que parece deliberado: 4.5, 4.6, 4.7, 4.8 (cierre automático) y 4.10. Lo que parece desvío no buscado: 4.3, 4.9, 4.14, 4.16 y buena parte de 4.12.
3. **Configuración (4.1) y mock (4.2).** Son las que más afectan al despliegue (G13) y a la regla de no mezclar datos sintéticos con reales.
4. **Qué hacer con los extras del globo (4.5)**: unos 60 ajustes en `appearance.ts` y capas apagadas (arcos, densidad por celdas, mapa de calor, marcadores, grano) son código sin uso en la práctica. Propongo no portarlos.

## 7. Orden de trabajo propuesto (cuando se decida lo anterior)

1. Resolver las decisiones de la sección 6 y reflejarlas en spec, plan y tareas (`speckit-clarify` o edición directa, con tu revisión).
2. Portar por bloques, empezando por T010 (simbología con las clases decididas), T023 (tokens), T012 (continentes y atribución), T013-T016 (ficha, leyenda, globo, integración) y T017 (responsive).
3. Dejar para las features siguientes: filtros y tabla (009), estadísticas (010), estado (011), replay y conexión con la API.
4. Añadir lo que falta: T008 (config), pruebas de simbología y de la rampa, evidencias, README y `CODEMAP.md`.
5. Borrar `_import-front/` al terminar.
