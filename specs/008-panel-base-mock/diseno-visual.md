# Diseño visual del panel (el front tal como está)

**Reescrito**: 2026-11-10, por decisión del alumno de adoptar el front externo (`globo-lab`) **sin cambiar su apariencia**. Sustituye al diseño HUD del 2026-11-06 (celdas hexagonales, columnas «RESERVADO», botón «Ver en mapa 2D», ficha con borde), que queda retirado. **Feature**: `008-panel-base-mock`. Las features futuras (`013-replay` y siguientes) heredan estos tokens y reglas.

Este documento **describe** lo que hay; no es un diseño nuevo. Los valores salen de `_import-front/globo-lab/src/index.css` y `shared/lib/appearance.ts` (ya afinados por el alumno). Si algo no coincide con la pantalla, manda la pantalla y se corrige aquí.

## 1. Principios (los que el front ya cumple)

1. **Fondo oscuro** y texto monoespaciado. El panel flota **sin cajas** sobre el globo: textos con sombra suave para leerse, líneas finas que se desvanecen y pocos bordes.
2. **Etiquetas pequeñas en mayúsculas** con espaciado entre letras para títulos; los valores van en tamaño normal.
3. **Un acento naranja** (`hud-accent`) para selección, elemento activo, valores destacados y títulos de bloque. Los datos usan su propia paleta de profundidad.
4. **Verde y rojo solo para estado**: `hud-ok` (en línea) y `hud-bad` (error o aviso grave).
5. El color de los datos nunca es el acento: la magnitud va en el largo, la profundidad en el color más su rango escrito en la leyenda, y ND en gris más el texto «ND».
6. Sin lenguaje de predicción ni riesgo en ningún rótulo (constitución §21).

## 2. Tokens de Tailwind (bloque `@theme` de `src/index.css`)

| Token | Valor | Uso |
|---|---|---|
| `--color-hud-bg` | `#000000` | Fondo de página |
| `--color-hud-panel` | `#0b0d10` | Fondo de hojas y cajones opacos (móvil) y desplegables |
| `--color-hud-land` | `#151a20` | Espejo para el globo (`shared/lib/tokens.ts`) |
| `--color-hud-line` | `#3a3f47` | Separadores y bordes finos |
| `--color-hud-line-strong` | `#6b7280` | Bordes de controles y separadores con degradado |
| `--color-hud-text` | `#e5e7eb` | Texto principal |
| `--color-hud-dim` | `#9ca3af` | Etiquetas y texto secundario |
| `--color-hud-accent` | `#ff7a1a` | Acento naranja |
| `--color-hud-ok` / `--color-hud-bad` | `#4ade80` / `#f87171` | Estado correcto / error |
| `--font-family-hud` | `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` | Toda la interfaz |

Los colores de **profundidad** y el gris ND son constantes de `shared/lib/symbology.ts` (ver §4), no tokens. Hay valores del globo escritos en hexadecimal en `appearance.ts` y en el tooltip del globo: es una decisión consciente (three.js no lee las clases de Tailwind). Los tamaños de letra se escriben con valores concretos de Tailwind (10 y 11 px en etiquetas, 12 px en cuerpo).

## 3. Apariencia del globo (`APPEARANCE`, valores del alumno)

| Aspecto | Valor |
|---|---|
| Fondo / esfera | `#070a0e` / `#060606`, sin textura; retícula y atmósfera blanca (altitud 0,1) |
| Grano | Superposición con opacidad 0,09 y tamaño 1 px |
| Luces | Ambiente 0,8; direccional 0,3 |
| Tierra | **Países extruidos** (`paises.geojson`, sin Antártida): tapa `#333333`, lado `#232323`, borde `#5d5d5d`, altitud 0,011 |
| Sismos | **Prisma de 7 lados**, radio 0,2°, opacidad 0,9, altura × 3,7 sobre la altura base (largo ∝ magnitud, mínimo para nula o negativa) |
| Color | Por profundidad (§4); gris ND `#8a93a0` |
| Antigüedad | La opacidad baja de 1 a 0,25 a lo largo de 24 h |
| Anillos | Para M ≥ 4, color `#ea7e2f`, radio según magnitud (0,8° por unidad), no para magnitud nula |
| Etiquetas | «M…» para M ≥ 5 (M ≥ 6 en móvil), nunca para magnitud nula |
| Cámara | Giro automático lento que se detiene al interactuar; vuelve al zoom 2 a los 3 s; vista inicial Mediterráneo; al elegir un evento se acerca (zoom 1) y lo desplaza arriba a la derecha |
| Selección | El resto de eventos se atenúa (0,85) mientras hay uno elegido; tolerancia de clic 18 px (28 px en móvil) midiendo contra todo el pilar |
| Ficha | En escritorio se cierra sola a los 10 s sin actividad y se desvanece; en móvil no |

Parámetros ya fijados por el alumno tras su laboratorio de diseño; este documento no los reabre.

## 4. Profundidad: cinco clases con los cortes de la API

Los cortes son los de `histograms.depth` de la API (`api.md` §5.1). Límite inferior inclusivo; las profundidades negativas caen en la clase 1; nula → ND. Conservan el estilo de color del front: las clases 1, 3 y 5 son los tres colores que ya tenía (amarillo, rojo anaranjado, violeta) y las clases 2 y 4 son el punto medio entre vecinas. **Por defecto, revisable** (pregunta P6 de la spec).

| Clase | Profundidad (km) | Color |
|---|---|---|
| 1 | < 10 | `#ffd23f` |
| 2 | 10 a < 35 | `#ff963a` |
| 3 | 35 a < 70 | `#ff5a36` |
| 4 | 70 a < 300 | `#d7539a` |
| 5 | ≥ 300 | `#b04cff` |
| ND | nula | `#8a93a0` |

La luminancia desciende de la clase 1 a la 5, así que el orden se conserva en escala de grises. La leyenda escribe el rango de cada clase; la ficha da la profundidad en km.

## 5. Layout de escritorio (≥ 1024 px)

- **Izquierda** (anclada, 20 rem): leyenda (largo = magnitud con prismas M 2, 4, 6 y 8; color = profundidad con las cinco clases y el ND; anillos y antigüedad) y, debajo, **Eventos recientes** (12 filas, «mostrados») con «Ver todos», que abre la **tabla** sobre la zona izquierda y central (mientras está abierta, la columna de leyenda y eventos recientes se oculta; se cierra con Esc).
- **Centro arriba**: **barra de filtros** de una línea («En vivo · 24 h · Mag. todas · Todos los países») que despliega el panel de filtros (modo en vivo/reproducción, periodo de 1 h a 1 año o fechas UTC, magnitud mínima, país con búsqueda y «Sin país asignado», «Restablecer»); se cierra con Esc o al pulsar fuera. Debajo, los **avisos** (reproducción, datos antiguos, sin datos, backend sin respuesta, desactualizado, sintético, truncado), centrados y sin caja.
- **Derecha arriba**: **estado del feed** (indicador, modo, última ingesta) con un desplegable de detalle («Conexión» y «Datos»). Debajo, la **ficha** del evento seleccionado.
- **Abajo**: **cajón de estadísticas** que sube desde el borde inferior con una flechita (total, por hora UTC, por país, magnitud, profundidad y «Últimas 24 h vs 2025»). Esc lo cierra.
- **Atribución**: línea permanente de al menos 11 px, abajo a la derecha, por encima del cajón (FR-025). Antes estaba en 9 px dentro del desplegable del estado.

## 6. Layout móvil (< 1024 px)

- Barra superior opaca con el resumen de filtros (dos líneas) y el estado; los desplegables ocupan todo el ancho.
- El globo ocupa el resto, con la cámara más lejos según el aspecto y la ficha **abajo**, centrando el evento.
- Barra inferior con tres hojas opacas desplegables: **Eventos** (con lista de tarjetas ordenable), **Estadísticas** y **Leyenda**; la ficha va en una hoja inferior de hasta el 60 % de la altura.
- Avisos en una sola línea plegable («● Aviso +1»). Sin transparencias a propósito.
- La atribución se ve en una franja fija en el pie, fuera de las hojas.
- Entre 768 y 1023 px se ve este mismo diseño.

## 7. Estados y textos fijos

«ND» para cualquier dato nulo; «Sin país asignado»; «Sin descripción»; fechas «AAAA-MM-DD HH:mm UTC»; decimal con coma y signo menos tipográfico; «REPRODUCCIÓN» en el aviso de modo replay; «Sin eventos reproducidos» para un replay vacío; «mostrados» para todo recuento que haga el propio panel.

## 8. Fuera de este diseño

Celdas hexagonales para los continentes, columnas laterales «RESERVADO», botón «Ver en mapa 2D» y ficha en panel lateral con borde (todo eso era del diseño del 2026-11-06). Accesibilidad de teclado y tamaño táctil de 44 px: **no cubiertas, decisión propia** (G16).
