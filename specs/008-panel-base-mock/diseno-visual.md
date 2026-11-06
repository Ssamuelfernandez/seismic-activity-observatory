# Diseño visual del panel (dirección HUD)

**Creado**: 2026-11-06, por cambio de diseño del alumno. **Feature**: `008-panel-base-mock`. **Aplica a**: todo el panel; las features `009` en adelante y `panel-mapa-2d` heredan estos tokens y reglas.
**Ubicación**: `CODEMAP.md` no tenía ninguna ruta para un documento de diseño visual; se deja junto a la spec de la feature que lo crea (mismo patrón que «spec, plan, tareas» en `CODEMAP.md`). **Decidido por el alumno, 2026-11-06 (P12): el documento se queda aquí.**

Los valores marcados *(por defecto, revisable)* los propone el diseñador; el alumno decidió la dirección (HUD oscuro, un acento naranja), no los números. Este documento no contiene código: los tokens se declararán en el CSS del frontend en la tarea `T023`.

## 1. Principios

1. **Fondo negro** y líneas finas grises (1 px). Sin sombras, degradados ni esquinas redondeadas.
2. **Etiquetas pequeñas en mayúsculas** con espaciado entre letras para títulos de panel, ejes y leyenda. Los **valores** (cifras, texto de ficha) van en tamaño normal y legible.
3. **Un solo acento: el naranja.** Solo para foco, selección, el elemento activo y el botón principal. No se usa para datos.
4. **El color de los datos no es el acento.** La rampa de profundidad (ver spec V2) y el gris ND son tokens aparte.
5. **El color nunca es el único canal** (G16): la magnitud va en la altura, la profundidad en el color más su rango escrito y su número en la ficha, y ND en gris más el texto «ND».
6. **Sin lenguaje de predicción ni riesgo** en ningún rótulo (constitución §21).

## 2. Tokens de Tailwind (v4, bloque `@theme`) *(por defecto, revisable)*

Contraste calculado con la fórmula de luminancia relativa de WCAG sobre `#000000`.

| Token | Valor | Uso | Contraste sobre negro |
|---|---|---|---|
| `--color-hud-bg` | `#000000` | Fondo de página y del globo | — |
| `--color-hud-surface` | `#0B0D10` | Fondo de paneles (ficha, cajón, columnas) | — |
| `--color-hud-land` | `#151A20` | Celdas hexagonales de los continentes | decorativo (ver §5) |
| `--color-hud-line` | `#3A3F47` | Separadores y bordes decorativos de 1 px | decorativo |
| `--color-hud-line-strong` | `#6B7280` | Borde de controles (botones, cajón) | 4,3 : 1 |
| `--color-hud-text` | `#E5E7EB` | Texto principal y valores | 17,0 : 1 |
| `--color-hud-text-dim` | `#9CA3AF` | Etiquetas y texto secundario | 8,3 : 1 |
| `--color-hud-accent` | `#FF7A1A` | Acento naranja: foco, selección, botón principal | 8,1 : 1 |
| `--color-hud-nd` | `#8A93A0` | Gris de ND (magnitud o profundidad) | 6,8 : 1 |
| `--color-depth-1` … `--color-depth-5` | los de la spec V2 (única fuente) | Rampa de profundidad (rampa cálida confirmada por el alumno, 2026-11-06) | ≥ 3,8 : 1 |
| `--font-hud` | pila del sistema: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` | Etiquetas y cifras (sin descargar fuentes) | — |
| `--text-hud-label` | `0.6875rem` (11 px), mayúsculas, `--tracking-hud: 0.12em` | Etiquetas de panel, leyenda, ejes | — |
| `--text-hud-value` | `0.875rem` (14 px) | Valores y texto de ficha | — |
| `--spacing-hud` | `0.75rem` | Hueco estándar entre paneles | — |
| `--border-width-hud` | `1px` | Todos los bordes | — |
| `--radius-hud` | `0` | Sin esquinas redondeadas | — |
| `--size-touch` | `2.75rem` (44 px) | Alto/ancho mínimo de controles pulsables | — |

Reglas de uso: ningún componente escribe un color, tamaño de letra o borde a mano; usa la clase generada por un token. El **foco de teclado** es un contorno de 2 px de `hud-accent` con separación de 2 px, siempre visible.

## 3. Esqueleto de pantalla

Cuatro zonas: **cabecera**, **globo central**, **columnas laterales reservadas** (izquierda y derecha) y **panel lateral de ficha**.

| Ancho | Cabecera | Globo | Columnas reservadas | Ficha |
|---|---|---|---|---|
| **< 768 px (375 px de referencia)** | Una fila: título, banner de sintético, botón «Leyenda» | Ocupa el ancho y la altura restante; sin scroll horizontal | No se muestran (colapsadas; el espacio queda reservado en el código, no en pantalla) | **Cajón inferior**: ancho completo, hasta el 50 % de la altura, scroll interno, botón de cerrar ≥ 44 × 44 px |
| **768 a 1023 px** | Igual, con rótulos más largos | Ancho completo | Colapsadas (no se muestran) | **Panel lateral** de 20 rem anclado al borde derecho, sobre el globo |
| **≥ 1024 px** | Una fila | Zona central, ocupa lo que dejan las columnas | Dos marcos, izquierda y derecha, de 16 rem cada uno | **Panel lateral** de 20 rem, sobre el borde derecho de la zona del globo; no tapa las columnas |

- La **leyenda** es una tarjeta en la esquina inferior izquierda del globo desde `md`; por debajo, se abre desde el botón de la cabecera.
- La **atribución** es una línea fija en la esquina inferior derecha del globo, siempre visible, fuera de la leyenda y de la ficha (si la ficha la tapa en móvil, la atribución va en el pie de la propia página, no dentro del cajón).
- El cuerpo de la página no hace scroll: la cabecera y las zonas se reparten la altura de la ventana. Comprobación: `scrollWidth <= innerWidth` en 375, 768 y 1280 px.

## 4. Herencia por los demás paneles

Las features futuras (`009` filtros y tabla, `010` gráficos y comparación, `011` estado, `013` replay, `panel-mapa-2d`) usan **solo estos tokens**. Si una necesita un valor nuevo (por ejemplo un color de aviso), se añade primero a este documento y a `@theme`, no en su componente. Ubicación prevista de cada una: filtros en la columna izquierda; panel lateral de comparación (G5b) en la columna derecha; estado en la cabecera. El mapa 2D de `panel-mapa-2d` aplica la misma paleta (fondo negro, mismas clases de profundidad).

## 5. Contraste y accesibilidad mínima (G16, contexto)

- Texto y valores: contraste ≥ 4,5 : 1 sobre `hud-bg` y `hud-surface` (los tokens de texto dan ≥ 8 : 1).
- Elementos gráficos con información (prismas, borde de controles): ≥ 3 : 1 sobre su fondo. La rampa de profundidad cumple 3,8 : 1 o más sobre negro y 3,1 : 1 o más sobre `hud-land`.
- Las celdas `hud-land` y los separadores `hud-line` son decorativos: la información nunca depende de verlos.
- La rampa está ordenada por luminancia (la clase más superficial, la más clara): el orden se conserva en escala de grises, y además cada clase lleva su rango escrito en la leyenda.
- Etiquetas de 11 px solo en mayúsculas cortas (títulos y leyenda); ningún dato ni texto de ficha baja de 14 px.
- Controles alcanzables con teclado, foco visible y ≥ 44 × 44 px en pantallas táctiles.
- El globo no sustituye a la tabla accesible (G8, G16): llega con `009`.

## 6. Estados vacíos de las columnas reservadas

Las columnas no tienen contenido en esta feature y **no se inventa funcionalidad**: son un marco vacío (`hud-line`, fondo `hud-surface`) con una sola etiqueta en `hud-text-dim`: «RESERVADO». Sin botones, sin textos de ejemplo, sin datos falsos. Por debajo de 1024 px no se muestran. Decidido por el alumno, 2026-11-06 (P8): marcos «RESERVADO» desde 1024 px.

## 7. Globo (resumen visual; detalle en `plan.md`)

- **Fondo negro**, sin textura ni atmósfera de color; los continentes son **celdas hexagonales** (`hud-land`) calculadas a partir de `paises.geojson`, con la **Antártida oculta**.
- Cada sismo es un **prisma hexagonal**: largo ∝ magnitud, color por profundidad, ND en gris con la altura mínima fija. Valores en la spec (V1 a V4).
- Seleccionado: el prisma se resalta con el acento naranja y la ficha se abre.
