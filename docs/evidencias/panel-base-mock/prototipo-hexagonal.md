# Prototipo del prisma hexagonal y las celdas (T022; G2, G17; FR-011, FR-012; SC-012)

Fecha: 2026-11-06. Equipo: Windows 11 Pro, Node 24.18.0, Microsoft Edge 156 headless (puppeteer-core 25.16.0) con GPU real (ANGLE, NVIDIA GeForce RTX 3060 Ti); el monitor/headless va a 100 Hz, así que 100 fps es el techo medible. Versiones: `react-globe.gl` 2.38.0 sobre `three-globe` 2.45.6, `h3-js` 4.5.0, Vite 8.3.6. Datos: `mock/truncated.json` (5 000 eventos sintéticos) y `data/catalogo/paises.geojson` sin `ADM0_A3 = ATA`. Se midió el build de producción servido con `vite preview` (sin Internet: ya no hay textura ni teselas).

Página: `frontend/prototipo-mapa/globe-hex/` (http://127.0.0.1:5183, ver `LEEME.md`). La página del globo anterior (`globe/`, :5181) queda intacta para comparar. Medición: `frontend/prototipo-mapa/scripts/measure-hex.mjs`; salidas crudas en `prototipo-hexagonal/` (`medidas-hex.json`, `medidas-hex-clicks.json`, `medidas-hex-colors.json`, logs y capturas).

Configuración medida: `pointsData` con `pointResolution = 6`, `pointsMerge: false`, altura V1, color V2, ND gris `#8A93A0`; `hexPolygonsData` con margen 0,2, color `#151A20`, altura 0,001; fondo `#000000`, sin textura, sin atmósfera. Anchura por defecto 0,45°.

## Tabla

| Criterio | Resultado | ¿Cumple? |
|---|---|---|
| Tiempo hasta pintar 5 000 prismas + celdas, 1280 px, res 3 (3 corridas, ms; ref. ≤ 3 s) | 484 / 465 / 477 | Sí |
| Ídem, res 4 | 1 969 / 1 917 / 1 669 | Sí, pero 3-4 veces más lento que res 3 |
| Ídem, 375 px, res 3 / res 4 | 515 / 496 / 508 y 1 798 / 1 891 / 1 585 | Sí |
| Fluidez al mover (3 s programáticos, 3 repeticiones), 1280 y 375 px, res 3 y res 4 | 10,0 ms por fotograma, p95 10,1 ms, ~100 fps en las 12 repeticiones (ref. ≥ 30 fps; T006 con puntos de 12 lados: ~37 fps) | Sí, pero topado por el refresco del monitor: no se sabe cuánto margen real hay |
| Fluidez real con ratón o dedo | A valorar por el alumno (moverlo en el navegador) | — |
| Número de celdas (el prototipo no deduplica; todas son distintas) | res 3: 10 744; res 4: 75 237 | Dato |
| Color visible frente al token | Ver tabla de color abajo | Parcial (clase 5, luces por defecto) |
| Lectura del prisma de 6 caras de cerca | Se ve como prisma hexagonal: tapa hexagonal y dos caras laterales visibles en vista oblicua (capturas `cerca_*`) | A valorar por el alumno (mi observación: bien) |
| Lectura a escala de globo (solo dato) | Cada prisma es una barra fina: no se distingue el hexágono (`hex_*_escala_globo.png`) | Dato, no cuenta |
| 375 px | Sin scroll horizontal (`scrollWidth <= innerWidth`). A la altura por defecto de cámara el globo desborda el ancho por los lados; el panel de pruebas tapa parte | A valorar por el alumno |

### Pulsar un prisma pequeño (M −0,5, el menor del mock; centro tomado a media altura; 4 intentos por distancia; solo cuenta si se abre la ficha de ese evento; ratón a 1280 px, toque emulado a 375 px)

Altura de cámara 1,2 (globo grande en pantalla), como en T006.

| Variante | Viewport | 0 px | 3 px | 6 px | 12 px |
|---|---|---|---|---|---|
| Exacto, anchura 0,45° | 1280 | 4/4 | 4/4 | 0/4 | 0/4 |
| Exacto, anchura 0,6° | 1280 | 4/4 | 4/4 | 4/4 | 0/4 |
| Exacto, anchura 0,8° | 1280 | 4/4 | 4/4 | 4/4 | 0/4 |
| Más cercano, tolerancia 12 px, 0,45° | 1280 | 4/4 | 4/4 | 4/4 | 2/4 |
| Más cercano, tolerancia 22 px, 0,45° | 1280 | 4/4 | 4/4 | 4/4 | 4/4 |
| Exacto, 0,45° | 375 | 3/4 | 4/4 | 0/4 | 0/4 |
| Exacto, 0,8° | 375 | 3/4 (+1 abrió otra ficha) | 4/4 | 4/4 | 1/4 |
| Más cercano, 12 px, 0,45° | 375 | 4/4 | 4/4 | 4/4 | 1/4 |
| Más cercano, 22 px, 0,45° | 375 | 4/4 | 4/4 | 4/4 | 4/4 |

Notas: la «tolerancia» del más cercano es estricta (`< tol`), por eso a 12 px con 12 px de tolerancia acierta a medias. En la primera corrida (`medidas-hex.json`, sección `clicks`) el ratón hacía clic sin moverse antes y fallaba hasta a 0 px (3/4): three-globe detecta el objeto al mover el ratón. Esa sección se descartó y se repitió moviendo el ratón y esperando 200 ms (`medidas-hex-clicks.json`). Con el toque emulado el fallo de 3/4 a 0 px con exacto no se pudo explicar con certeza (posible ruido del toque emulado). El mock es aleatorio y no tiene zonas densas: la prueba «en zona densa» queda sin medir y es lo que más puede favorecer a «exacto» frente a «más cercano» (el más cercano elige por distancia al centro y puede abrir un vecino).

### Color visible (muestreo de píxeles de capturas a 1280 px; sesgo de las luces)

Color dominante de la cara superior (vista cenital) y de la cara lateral más clara/oscura (vista oblicua). Los tokens son los de la spec V2. Contraste sobre negro calculado con WCAG.

| Clase | Token | Luces `defecto` (cara frontal / lateral) | Luces `alta` (ambiente 0,9 π + direccional 0,3 π) | Luces `plana` (solo ambiente 1,0 π) |
|---|---|---|---|---|
| 1 | `#FFF1A6` | `#FFFFB1` / `#CCC184` (11,5 : 1) | `#FFFFB2` / `#F3E69E` | exacto `#FFF1A6` |
| 2 | `#FDB347` | `#FFBA4A` / `#CA8E37` | `#FFBE4C` / sin lateral oscuro medido | exacto `#FDB347` |
| 3 | `#F26A5A` | `#FF7160` / `#C15346` | `#FF7261` / `#E76555` | exacto `#F26A5A` |
| 4 | `#D2468C` | `#A8366F` / (misma, 3,4 : 1) | `#C84285` (4,6 : 1) | exacto `#D2468C` |
| 5 | `#7C4DCB` | `#623CA2` (**2,7 : 1**) | `#7649C2` (3,5 : 1) | exacto `#7C4DCB` (3,8 : 1) |
| ND | `#8A93A0` | `#6D747F` (4,5 : 1) | `#838C98` (6,2 : 1) | exacto `#8A93A0` |

Lectura: con las luces por defecto de globe.gl, la luz ambiente deja las caras sin sol al 80 % del token (`#623CA2` = 0,8 × `#7C4DCB`) y las caras soleadas se saturan por encima del token. La clase 5 en una cara oscura baja a 2,7 : 1, por debajo del 3 : 1 de SC-016/WCAG 1.4.11. Con luces `alta` (ambiente 0,9 π + direccional 0,3 π) todas las caras quedan por encima de 3 : 1 y aún se distinguen las caras laterales. Con `plana` el color es exacto pero las caras se funden en una silueta (no se lee el volumen). Observación adicional: con las luces por defecto la esfera sin textura se ve gris muy oscuro (`#151515`–`#1C1C1C`, brillo especular del material), no negro puro; con `plana` no ocurre. Las celdas dibujadas valen `#171C23` frente al token `#151A20` (1,1 veces).

## Parámetros recomendados

- `pointResolution = 6`, `pointsMerge: false`, altura V1 y colores V2/V3/V4 tal cual la spec.
- Anchura del prisma: 0,45° se queda como valor base; sube a 0,6° si se prefiere acertar sin «más cercano» hasta 6 px (con 0,6° acierta a 6 px en 1280 px, pero a 0,8° el toque a 375 px ya abre prismas vecinos).
- Celdas: resolución 3 (10 744 celdas, 0,48 s). La 4 también cumple el tiempo (1,7-2,0 s) pero 7 veces más celdas y ya cerca del límite de 3 s en un equipo más lento; no aporta nada que haga falta.
- Luces: no usar las de por defecto; usar `alta` (o ajustar a esos valores) para que la clase 5 supere 3 : 1.
- Selección del más cercano: sí, con tolerancia de 12 px (22 px si se quiere cubrir un dedo de 44 px; riesgo de abrir un vecino en zona densa, sin medir).

## Recomendación para P9 (no es la decisión: es del alumno, que quiere verlo en el navegador)

Cómo hacer pulsable el prisma pequeño: **selección del más cercano con `getScreenCoords`, tolerancia 12 px** (22 px en pantallas táctiles), con anchura 0,45°. Motivo: con clic exacto a 6 px se falla (0/4) y con el más cercano se acierta 4/4 a 0, 3 y 6 px en 1280 y 375 px. Es una función de unas 15 líneas que solo elige qué ficha abrir (no calcula estadísticas). Ensanchar el prisma (0,6°) también ayuda, pero a costa de solaparse y de abrir fichas vecinas con el dedo. Valorar en el navegador con «MÁS CERCANO» y tolerancias 8/12/22 y en una zona con prismas juntos.

**D1 y P9 no están cerradas por esta evidencia.**

## Observación honesta sobre el prisma (plan B)

De cerca, el prisma de 6 caras se lee claramente como prisma hexagonal: tapa hexagonal limpia y, en vista oblicua, dos caras laterales de tono distinto; el vértice no queda orientado de forma problemática (la tapa se ve con vértice arriba y abajo). Es decir, **no queda claramente mal**, así que el plan B (malla propia con `customLayerData`) no hace falta y no se ha implementado. Dos limitaciones honestas: (1) a escala de globo es solo una barra fina (esperado, el criterio del alumno lo admite); (2) las barras de M alta atraviesan el límite del globo y dan al conjunto el aspecto de «erizo» a escala global (visible en `hex_1280_inicial_res3.png`): es el diseño V1, no un fallo. Lo subjetivo («se ve bien de cerca») queda **a valorar por el alumno** en el navegador.

## Límites y lo que queda para el alumno

- Fluidez topada a 100 fps: no se sabe el margen real; probarlo a mano. No se midió en móvil real.
- Los continentes se dibujan por país (el prototipo no deduplica ni une polígonos), no se revisaron huecos ni solapes entre países; en 375 px las celdas de res 3 apenas se leen. No se comparó el aspecto de las celdas en detalle: a valorar.
- No se probó el resaltado naranja del prisma seleccionado (no era parte de T022) ni la zona densa de eventos.
- Dependencias: la página importa `three` y `h3-js`, que no están en el `package.json` del prototipo (llegan como dependencias de `react-globe.gl`); en `T015` se deben usar solo las que ya instale `T007` o añadirlas de forma explícita.
- `npm ci` hubo que repetirlo en `frontend/prototipo-mapa/` porque a mitad de la medición desapareció `node_modules/puppeteer-core/package.json` (causa desconocida; se restauró con `npm ci`).

## Capturas (`prototipo-hexagonal/`)

- A 1280 y 375 px: `hex_1280_inicial_res3.png`, `hex_1280_inicial_res4.png`, `hex_375_inicial_res3.png`, `hex_375_inicial_res4.png`; a escala de globo: `hex_1280_escala_globo.png`, `hex_375_escala_globo.png` (altura de cámara 1,2); regional: `hex_1280_zoom_regional.png`.
- Ampliadas (factor 2) del prisma: `cerca_defecto_d1..d5_*`, `cerca_defecto_nd_*` (cenital y oblicuo), `cerca_suave_d3_*`, `cerca_plana_d3_*`, `cerca_alta_d3_*`, y `cerca_altura_M-0c5.png`, `cerca_altura_M4.png`, `cerca_altura_M6c5.png` (la magnitud máxima del mock es 6,5, no 8).
