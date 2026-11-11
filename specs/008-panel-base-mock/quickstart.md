# Quickstart: validar el panel completo

Guía de validación al cerrar la feature. Rutas relativas a la raíz del repositorio. Detalle de datos: `data-model.md`. Contrato: `specs/001-contratos-y-modelo/contracts/api.md`. **Reescrito el 2026-11-10** por la enmienda de alcance.

## Requisitos

- Node 24.18.0 (`frontend/.nvmrc`) y npm. Sin Internet para el fondo (sin textura) ni para el mock.
- Para el apartado 4: Docker con el stack de Compose levantado (`docker compose up -d`), con eventos reales y, para la comparación, el histórico de 2025.
- Sin claves ni variables de entorno (opcional: `API_PROXY_TARGET` para cambiar el destino del proxy de desarrollo).

## 1. Instalación, build y pruebas (G0, SC-001, SC-015)

```
cd frontend
npm ci
npm run build
npm test
```

Esperado: los tres con código 0. Guardar la salida en `docs/evidencias/panel-base-mock/`.

## 2. Servidor de desarrollo (SC-001)

```
npm run dev
```

Esperado: HTTP 200 en `http://localhost:4200/`. Un segundo `npm run dev` con el primero activo **falla** (`strictPort`) en vez de usar otro puerto.

## 3. Mock en desarrollo (G15, SC-004, SC-006, SC-009)

Con `"mode": "mock"` en `frontend/public/config.json`:

| URL | Esperado |
|---|---|
| `/` (`base`) | ~30 prismas con colores de las cinco clases, leyenda de cinco clases, banner de datos sintéticos, atribución visible |
| `/?scenario=realistic` | ~400 eventos; al cambiar periodo, magnitud o país cambian globo, tabla y estadísticas |
| `/?scenario=truncated` | 5 000 eventos y aviso «Mostrando 5000 de 6213» |
| `/?scenario=replay` | Eventos de 2025 y banner **REPRODUCCIÓN** |
| `/?scenario=empty` | Globo vacío y «Sin eventos en el intervalo» |

Pulsar un evento con `mww` («Magnitud 5,4 (mww)»), uno de magnitud nula (barra gris sin anillo ni etiqueta; «ND»), uno sin país («Sin país asignado») y uno de magnitud −0,06 y profundidad −0,01 (valores tal cual). Consola: cero errores; ninguna pantalla muestra «NaN» ni «undefined». La interfaz no ofrece ningún control para cambiar mock/API. Restaurar `config.json` a `"mode": "api"`.

## 4. Con la API real (G1, G3–G9, G12, SC-007, SC-008)

```
docker compose up -d
curl http://localhost:8000/api/salud
npm run dev          # en frontend/, con "mode": "api" y "apiBaseUrl": "/api"
```

1. Globo, lista, tabla, estadísticas y estado muestran datos reales. Cambiar periodo, magnitud y país: todo cambia a la vez y `stats.total` coincide con `metadata.total` (anotar los valores en una tabla).
2. Replay: sin datos reproducidos la pantalla muestra «Sin eventos reproducidos» y el banner REPRODUCCIÓN, sin error.
3. Fallo: `docker compose stop api` → en un ciclo de refresco aparece el aviso y la última lectura queda marcada como antigua con su hora; nunca «0 eventos». `docker compose start api` → se recupera sin recargar. Repetir parando solo PostgreSQL (503 `database_unavailable`).
4. En la pestaña de red: peticiones a `/api/eventos`, `/api/estadisticas` y `/api/salud` cada `refreshSeconds`, sin solaparse; ninguna a `earthquake.usgs.gov`.

## 5. Configuración y producción (G15, SC-002, SC-003)

```
npm run build
npm run preview
```

- Editar `frontend/dist/config.json`: `"mode": "otro"` → mensaje que nombra `mode`; `"refreshSeconds": 0` → mensaje que nombra `refreshSeconds`; `"mode": "mock"` → «mock no disponible en este build». Restaurar.
- `grep -r __MOCK_BACKEND__ frontend/dist` y `grep -r "Sintético:" frontend/dist` no devuelven nada; `frontend/dist/assets` no contiene los JSON del mock.

## 6. Fronteras y copia del catálogo (G14, SC-014)

```
sha256sum data/catalogo/paises.geojson frontend/public/datos/paises.geojson
```

Esperado: ambos `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`.

## 7. Responsive y atribución (G17, SC-010, SC-012)

Con las herramientas del navegador, emular 375 × 667, 768 y 1280 de ancho, con el mock y con la API real, con una ficha abierta. En la consola:

```
document.documentElement.scrollWidth <= window.innerWidth
```

Esperado: `true`. Capturas en `docs/evidencias/panel-base-mock/` (mínimo: 1280 px con filtros visibles, 375 px con ficha, cada aviso, la leyenda de cinco clases). La atribución (USGS, Natural Earth, `react-globe.gl` y `three`) se lee sin pulsar nada.

## 8. Calidad del código (SC-011, SC-013)

- `grep -rn "formatMadrid\|h3-js" frontend/src frontend/tests frontend/package.json` sin resultados.
- `docs/evidencias/panel-base-mock/auditoria-calculos-cliente.md` existe y no hay recuento propio sin «mostrados».

## Límites conocidos

G16 no cubierta; el rendimiento con 5 000 eventos no está medido; el periodo en replay es fijo (2025); sin datos de replay reales hasta `013-replay`; el CORS real es de `015-despliegue-tunel`.
