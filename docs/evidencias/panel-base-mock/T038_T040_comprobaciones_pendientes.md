# T038–T040: comprobaciones que quedan para el alumno

Sin navegador no se hicieron las capturas ni el recorrido visual. Lo automático (tests, build, `dist/` sin mock, SHA, dev 4300, 4200 ocupado) está en `T038_*` y `T039_*`.

## Recorrido en navegador (T039)

Arrancar `npm run dev` en `frontend/` (puerto 4200, libre) y abrir DevTools. Con una **ficha de evento abierta** (clic en un evento del globo o de la tabla), para cada ancho 375, 768 y 1280 px (modo dispositivo de DevTools):

1. Consola: `document.documentElement.scrollWidth <= window.innerWidth` debe dar `true`.
2. Pestaña Console sin errores (rojo) tras cargar y tras abrir la ficha.
3. Guardar una captura por ancho en `docs/evidencias/panel-base-mock/` (`T039_<escenario>_<ancho>.png`).

### Con el mock (`public/config.json` con `"mode": "mock"`; restaurar `"api"` después)

| URL | Qué comprobar |
|---|---|
| `http://localhost:4200/?scenario=base` | Banner «DATOS SINTÉTICOS»; eventos con magnitud o profundidad nulas (barra gris ND, sin anillo ni etiqueta, tooltip «ND»); leyenda de cinco clases |
| `?scenario=realistic` | Cambiar periodo, magnitud mínima y país: globo, tabla y estadísticas cambian a la vez |
| `?scenario=truncated` | Aviso «Mostrando N de M eventos» |
| `?scenario=replay` (o modo REPRODUCCIÓN) | Banner REPRODUCCIÓN; selector de periodo desactivado mostrando «2025» |
| `?scenario=empty` | Estado vacío «Sin eventos reproducidos» / sin datos, no es error ni «0» |
| `?scenario=xx` | Cae a `base` y avisa en la consola (solo desarrollo) |

### Con la API real (`"mode": "api"`, `apiBaseUrl: "/api"`, stack de Docker levantado)

Misma comprobación de ancho y consola a 375, 768 y 1280 px con una ficha abierta. Sin banner sintético; no existe forma de ver datos del mock; los totales visibles salen de la API.

## Otras pruebas visuales ya pendientes de bloques anteriores

Ver `T024_T026_capturas_pendientes.md`, `T027_T029_comprobaciones_pendientes.md`, `T030_T033_comprobaciones_pendientes.md` y `T034_T037_comprobaciones_pendientes.md`.

## Comprobación de «4200 ocupado»

El 4200 lo tiene un servidor ajeno, así que `npm run dev` falla con «Port 4200 is already in use» (`T039_dev_4200_ocupado.txt`). Si se quiere repetir con el 4200 libre: dos `npm run dev` seguidos, el segundo debe fallar.
