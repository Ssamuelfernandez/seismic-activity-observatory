# Panel del observatorio sísmico (frontend)

Panel web con globo 3D, filtros, tabla, estadísticas y estado del feed. Lee la API de consulta (`/api/eventos`, `/api/estadisticas`, `/api/salud`) y **no calcula estadísticas**: muestra lo que devuelve la API. Feature `panel-base-mock` (`specs/008-panel-base-mock/`).

## Cómo ejecutarlo

Requiere Node 24.18.0 (ver `.nvmrc`). Desde `frontend/`:

| Comando | Qué hace |
|---|---|
| `npm ci` | Instala las dependencias exactas del lock |
| `npm run dev` | Servidor de desarrollo en `http://localhost:4200` (puerto fijo: falla si está ocupado) |
| `npm run build` | Comprueba tipos (`tsc --noEmit`) y genera `dist/` de producción |
| `npm run preview` | Sirve `dist/` para probarlo |
| `npm test` | Pruebas (Vitest, entorno node) |

`predev` y `prebuild` copian `data/catalogo/paises.geojson` a `public/datos/paises.geojson` comprobando su SHA-256 (ver «Material reutilizado»). En desarrollo, `/api` se reenvía a `http://127.0.0.1:8000` (el puerto que publica Compose); se cambia con la variable `API_PROXY_TARGET`.

## Configuración: `public/config.json`

Se lee al arrancar (no está compilada), se valida y, si un campo falla, el panel muestra un mensaje que nombra ese campo. No lleva secretos.

| Campo | Valor por defecto | Significado |
|---|---|---|
| `mode` | `"api"` | `"api"`: datos de la API real. `"mock"`: servidor simulado (solo desarrollo) |
| `apiBaseUrl` | `"/api"` | `/api` (proxy) o URL absoluta `http(s)://...`; puede ir vacío solo en `mock` |
| `refreshSeconds` | `60` | Segundos entre refrescos (entero > 0) |
| `timeoutMs` | `15000` | Tiempo máximo de cada petición en ms (entero > 0) |

## Mock y datos sintéticos

Con `"mode": "mock"` en `config.json`, `npm run dev` usa datos del mock de `mock/`. El escenario se elige con `?scenario=` en la URL: `base` (por defecto, ~30 eventos con casos de borde), `truncated`, `replay`, `empty` y `realistic` (~400 eventos que admiten filtros). Un valor desconocido usa `base` y avisa en la consola.

**Los datos del mock son sintéticos** (`is_synthetic: true`, ids `mock-…`, lugares «Sintético: …») y el panel los rotula con un banner. El mock solo funciona en desarrollo y pruebas: en el build de producción queda fuera de `dist/` (el alias `@mock/backend` apunta a un módulo que falla con «mock no disponible en este build»). En modo `api` no hay forma de ver datos sintéticos. Los JSON se regeneran con `node scripts/generate-mock.mjs` (semilla fija).

## Estructura de `src/`

```
src/
  main.tsx, App.tsx, index.css   arranque, composición y estilos
  components/                    pantalla: globo (único que importa react-globe.gl y three), tabla, filtros,
                                 estadísticas, estado, avisos, ficha, leyenda, atribución
    mobile/                      diseño móvil
  shared/
    api/                         cliente HTTP, petición, parseo (guardas), config y origen de datos
    hooks/                       datos (TanStack Query), país, medios, reloj
    lib/                         lógica pura: simbología, formato, estado, validación de config
    types/                       tipos del contrato
  store/                         filtros (Zustand)
mock/                            servidor simulado y escenarios (solo desarrollo)
tests/                           pruebas Vitest
```

## Material reutilizado

- **Natural Earth, Admin 0 Countries**: `data/catalogo/paises.geojson`, copiado sin modificar a `public/datos/paises.geojson`. Dominio público, escala 1:110 m, 177 entidades. SHA-256: `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`. Detalles en `docs/enunciado/FUENTES-Y-LICENCIAS.md`.
- **react-globe.gl** 2.38.0 y **three** 0.187.0: licencia MIT.
- **USGS Earthquake Hazards Program**: fuente de los sismos (vía la API del proyecto).
- El código del panel parte de un prototipo externo del propio alumno, portado y adaptado a la spec.

## Límites conocidos

- Accesibilidad (G16: foco de teclado y no depender solo del color) **no cubierta**, decisión propia.
- Rendimiento con 5 000 eventos **sin medir**.
- En modo `replay` el periodo es fijo (2025) y el selector queda desactivado; el cierre de `replay` es de la feature `013-replay`.
- El retraso de ingesta («hace X min») lo calcula el panel con `generated` y `last_ingestion`; se rotula «calculado en el panel».
