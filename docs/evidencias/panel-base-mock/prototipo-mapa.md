# Prototipo de la librería del mapa (T005 y T006, decisión D1)

Fecha: 2026-11-05. Equipo: Windows 11 Pro, Node 24.18.0, Microsoft Edge 156 headless (puppeteer-core 25.16.0) con GPU real (ANGLE, NVIDIA GeForce RTX 3060 Ti). Datos: `frontend/mock/truncated.json` (5 000 eventos sintéticos) y `data/catalogo/paises.geojson`. Versiones: `react-globe.gl` 2.38.0 (con React 19.3.1), `maplibre-gl` 6.16.0, Vite 8.3.6. Se midió el build de producción servido con `vite preview` en local (los datos no pasan por red; el fondo sí: teselas OSM y textura del globo por Internet).

Medición automática: `frontend/prototipo-mapa/scripts/measure.mjs`; salida cruda en `prototipo-mapa/medidas.json` y `medicion_log.txt`; pesos en `pesos_gzip.txt`; capturas `*_1280.png`, `*_375.png` y `*_ficha.png` en la misma carpeta (`docs/evidencias/panel-base-mock/prototipo-mapa/`).

## Tabla

| Criterio (spec D1) | react-globe.gl (globo 3D) | MapLibre GL JS (mapa 2D) |
|---|---|---|
| Tiempo hasta pintar los 5 000, PC 1280 px (3 corridas, ms; ref. ≤ 3 s) | 293 / 486 / 407 (mediana 407) | 562 / 398 / 405 (mediana 405) |
| Tiempo hasta pintar los 5 000, 375 px (3 corridas, ms) | 517 / 426 / 423 (mediana 426) | 386 / 367 / 366 (mediana 367) |
| Fluidez al mover (3 s de desplazamiento programático, 1280 px) | 26,8 ms/fotograma de media (~37 fps), p95 30,1 ms | 10,0 ms/fotograma (~100 fps), p95 10,1 ms |
| Fluidez al mover, 375 px | 22,0 ms de media (~46 fps), p95 30 ms | 10,0 ms, p95 10,1 ms |
| Fluidez real con ratón o dedo, ampliar | **A valorar por el alumno**: mover y ampliar en el navegador y ver si hay tirones | **A valorar por el alumno**: igual |
| Clic sobre el círculo más pequeño (M −0,5), clic centrado, 1280 px | 5/5 abren la ficha | 5/5 |
| Clic a 6 px del centro (dedo o ratón poco preciso), 1280 px | 0/4 | 4/4 |
| Pulsar un círculo pequeño, 375 px (toque emulado) | centro 5/5; a 6 px 0/4 | centro 3/5; a 6 px 1/4 (el toque emulado resultó irregular, no concluyente) |
| Dificultad real de pulsar un círculo pequeño con el dedo | **A valorar por el alumno**: probar en un móvil o en el modo móvil de Edge e intentar abrir la ficha de un círculo pequeño y de uno en zona densa | **A valorar por el alumno**: igual |
| Uso en 375 px | Sin scroll horizontal. Se ve el globo completo y pequeño; para ver una zona hay que girar y ampliar. Ficha en hoja inferior. A valorar por el alumno si es cómodo | Sin scroll horizontal. Mapa a pantalla completa con botones +/−; ficha en hoja inferior. A valorar por el alumno si es cómodo |
| Atribución legible | Visible sin pulsar nada, 11 px, a 375 px ocupa 3 líneas (40 px de alto) | Visible sin pulsar nada, 11 px, a 375 px ocupa 2 líneas (28 px de alto); el enlace a OSM es pulsable |
| Peso del build comprimido (gzip, kB; JS + CSS + HTML, sin datos) | **612,4** (JS 611,7; 2 170 kB sin comprimir) | **435,8** (JS 280,5, worker 144,9, CSS 10,1; 1 619 kB sin comprimir) |

## Cómo se midió y límites (sin inventar nada)

- **Tiempo hasta pintar:** desde que arranca el script de la página (`performance.now()`) hasta el primer fotograma tras entregar los 5 000 puntos (globo, dos `requestAnimationFrame`; no incluye la descarga de la textura) o hasta el evento `idle` del mapa (MapLibre, que incluye las teselas del fondo visibles). No son medidas idénticas, pero ambas están muy por debajo de la referencia de 3 s. En un móvil real irá más lento; no se ha medido.
- **Fluidez:** movimiento de cámara programático durante 3 s y recuento de fotogramas; sirve para comparar, no sustituye probarlo a mano. El monitor/headless parece ir a 100 Hz, por eso MapLibre marca 10 ms. El globo dibuja cada punto como una malla propia (`pointsMerge: false`, necesario para poder pulsarlo); con `pointsMerge: true` iría más rápido pero no admitiría clic por punto.
- **Clics:** en el prototipo MapLibre se dejó una tolerancia de 8 px alrededor del toque (`queryRenderedFeatures` con caja); el globo no tiene tolerancia propia (hay que acertar el punto, de ~3 px). Es una diferencia de lo que ofrece cada librería sin más código, pero se puede añadir lógica de punto más cercano en el globo. El toque en 375 px está emulado con Puppeteer: el 3/5 y 1/4 de MapLibre es probablemente ruido de la emulación (gestos táctiles del mapa), por eso se deja a valorar a mano.
- **Simbología (V1–V4):** ambas usan los mismos radios y colores (lógica local en `shared/symbology.js`). Diferencias por la librería: el globo no dibuja círculos huecos, así que la magnitud ND se pinta semitransparente (V3 no se cumple del todo) y el tamaño es una aproximación en grados (0,06° por px), no píxeles; MapLibre sí admite hueco (contorno de 2 px) y radios en píxeles reales.
- **Atribución:** una sola barra fija abajo a la derecha en ambas (OSM o NASA Blue Marble, Natural Earth, librería, aviso de datos sintéticos).
- **Leaflet con canvas:** no se probó; solo se exige si ninguna candidata cumple y ambas pintan en menos de 0,6 s.
- **Observación visual (capturas):** a 1280 px el globo muestra solo un hemisferio a la vez (lectura global incompleta, 5 000 puntos repartidos en una esfera) y el mapa 2D muestra todo el mundo a la vez, con muchos círculos solapados (los datos sintéticos están repartidos al azar por el planeta).

## Recomendación (no es la decisión; esa es del alumno en T007)

MapLibre GL JS cumple todos los criterios medidos con margen (pinta en ~0,4 s, pesa un 29 % menos, más fluido y con mejor tolerancia al pulsar) y, al ser 2D, es el que mejor encaja con G17 (PC primero, móvil usable); el globo también cumple el tiempo, pero pesa más, rinde menos y es más difícil de pulsar en 375 px.

## Qué debe mirar el alumno antes de T007

1. Arrancar las dos páginas (ver `frontend/prototipo-mapa/LEEME.md`): http://127.0.0.1:5181 (globo) y http://127.0.0.1:5182 (MapLibre).
2. Mover y ampliar en cada una: ¿hay tirones?
3. Intentar abrir la ficha de un círculo pequeño (morado o amarillo de 3 px) y de uno en zona densa, con ratón y con el modo móvil de Edge (F12, 375 px).
4. Comprobar si el globo le parece útil o solo vistoso para el panel (G17).
