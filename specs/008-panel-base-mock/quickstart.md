# Quickstart: validar el panel base con mock

Guía de validación al cerrar la feature. Rutas relativas a la raíz del repositorio. Detalle de datos: `data-model.md`. Contrato: `specs/001-contratos-y-modelo/contracts/api.md`.

## Requisitos

- Node 24.18.0 (`frontend/.nvmrc`) y npm. Sin Internet para el fondo: desde el 2026-11-06 es negro, sin textura ni teselas.
- Sin claves ni variables de entorno.

## 1. Instalación y build (G0, SC-001)

```
cd frontend
npm ci
npm run build
npm test
```

Esperado: los tres terminan con código 0; existe `frontend/dist/` con `config.json`, `datos/paises.geojson` y los cuatro JSON del mock como archivos aparte en `dist/assets/`. Guardar la salida en `docs/evidencias/panel-base-mock/`.

## 2. Servidor de desarrollo (SC-001)

```
npm run dev
```

Esperado: HTTP 200 en la URL que imprime Vite (por defecto `http://localhost:5173/`).

## 3. Casos del mock (G2, G15, SC-002, SC-005, SC-006, SC-007)

Abrir, con `mode: "mock"` en `public/config.json`:

| URL | Esperado |
|---|---|
| `/` (caso `base`) | Globo negro con continentes en celdas hexagonales (sin Antártida), ~30 prismas de largos y colores distintos, cabecera, leyenda, atribución, banner «DATOS SINTÉTICOS (MOCK)», y a 1280 px las dos columnas reservadas vacías |
| `/?scenario=truncated` | 5 000 prismas en ≤ 3 s y ≥ 30 fps al mover; ficha abre; `metadata.total` 6 213 en el JSON |
| `/?scenario=replay` | Se pinta como el resto; sin texto de modo |
| `/?scenario=empty` | Globo con continentes y «Sin eventos en el intervalo» |

Pulsar: el evento con `mww` (panel lateral de ficha «Magnitud 5,4 (mww)»), el de `magType` nulo («ND»), el de magnitud nula (barra gris de altura mínima; «ND»), el del mar («Sin país asignado») y el de magnitud −0,06 / profundidad −0,01 (valores tal cual). En todas las fichas «Ver en mapa 2D» está visible y muestra «próximamente». A 375 px la ficha es un cajón inferior. Esc cierra la ficha. Consola del navegador: cero errores en el recorrido; ninguna pantalla muestra «NaN» ni «undefined».

## 4. Configuración en tiempo de ejecución (G15, SC-011)

```
npm run build
npm run preview
```

Editar `frontend/dist/config.json`: `"mode": "api"` y recargar → mensaje de modo api no disponible y ningún evento. Poner `"mode": "otro"` → mensaje que nombra `mode` y sin mapa. Restaurar el archivo.

## 5. Fronteras y copia del catálogo (G14, SC-009)

```
sha256sum data/catalogo/paises.geojson frontend/public/datos/paises.geojson
```

Esperado: ambos `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`.

## 6. Responsive (G17, SC-003, SC-010)

Con las herramientas del navegador, emular 375 × 667, 768 y 1280 de ancho. Para cada caso, con la leyenda abierta y con una ficha abierta, ejecutar en la consola:

```
document.documentElement.scrollWidth <= window.innerWidth
```

Esperado: `true`. Capturas en `docs/evidencias/panel-base-mock/` (mínimo: `base` a 1280 px, `base` a 375 px con ficha, `truncated` a 375 px, `empty`, mensaje api). La atribución (Natural Earth, librería, «Fondo: negro, sin textura») se lee sin pulsar nada. Las columnas reservadas solo aparecen desde 1024 px.

## 7. Pruebas automáticas (SC-008, SC-013)

`npm test` incluye: validación de config, conformidad del mock (más un archivo estropeado que debe fallar), escalas de radio/color/ND y formato de ND y fechas UTC.

## 8. Ausencias (SC-014)

Comprobar que `frontend/` no contiene Dockerfile, compose, filtros, tabla, gráficos ni código de replay.

## Límites conocidos

Con 5 000 prismas el globo rinde menos que un mapa 2D y el prisma pequeño es difícil de pulsar; `truncated` no avisa del truncado; `refreshSeconds` y `timeoutMs` no se aplican; fronteras 1:110 m simplificadas.
