# Borrador: panel web (G0–G9, G11, G12, G14, G15, G17; G10/J7 parcial)

Material para la memoria y la defensa. Feature `panel-base-mock` (`specs/008-panel-base-mock/`), enmendada el 2026-11-10. Los datos del mock son sintéticos (`is_synthetic: true`, ids `mock-…`); el contraste usa la API real con los datos cargados.

## Qué hace

Panel en `frontend/` (React, TypeScript, Vite, Tailwind, Zustand) con globo 3D (un prisma por evento: largo según magnitud, color según clase de profundidad), filtros de periodo, magnitud y país, tabla ordenable, estadísticas con comparación con 2025, estado del feed, avisos y diseño móvil. Solo consulta nuestra API y no calcula estadísticas (constitución §17): muestra lo que devuelve.

## Por qué se adoptó el front externo

El alumno ya tenía un front (`globo-lab`, inventariado en `inventario-front-externo.md`) con el aspecto que quería. Se decidió conservarlo tal como se ve y corregirlo, en lugar de rehacer un diseño HUD. Esto absorbió las features 009–012 (filtros y tabla, gráficos, estado y fallos, conexión con la API) y aplazó el mapa 2D (G18).

## Qué se corrigió

- **Configuración en tiempo de ejecución**: `public/config.json` (`mode`, `apiBaseUrl`, `refreshSeconds`, `timeoutMs`) se lee al arrancar y se valida; el campo que falla se nombra. Sustituye al `config.json` compilado.
- **Mock fuera de producción**: vive en `frontend/mock/`; un alias de Vite lo sustituye en producción por un módulo que dice «mock no disponible en este build». `dist/` no contiene `__MOCK_BACKEND__` ni «Sintético:». No hay selector en la interfaz.
- **Cinco clases de profundidad** con los cortes de la API (`<10`, `10–35`, `35–70`, `70–300`, `≥300`, límite inferior inclusivo), conservando el estilo de color del front.
- **Atribución visible** de 11 px (USGS, Natural Earth, react-globe.gl y three), fuera de cualquier desplegable.
- **Auditoría de cálculos del cliente** (`auditoria-calculos-cliente.md`, 20 filas): lo que cuenta el cliente se rotula «mostrados»; los totales vienen de `metadata`/`stats`. Veredicto de P3: el retraso de ingesta (`generated − last_ingestion`) lo calcula el panel y se rotula «calculado en el panel»; sin cambio de contrato.
- **Magnitud nula sin `mag ?? 0`**: se queda nula (barra gris ND de altura mínima, sin anillo ni etiqueta, «ND» en la ficha).
- **Replay**: con `mode=replay` pide el intervalo de 2025 (`2025-01-01` a `2026-01-01`), el periodo queda fijo y una respuesta vacía es un estado vacío, no un error.
- Se quitó `h3-js` y el código muerto de fechas de Madrid, se borraron las capas apagadas del globo (P5) y se declaró `three`.

## Cómo se contrastó con la API real

- Tabla de 16 combinaciones de filtros (periodo, magnitud, país, rango, truncado con `limit=50`): `stats.total = metadata.total` en todas (`T035_tabla_filtros_totales.md`).
- Contraste de la forma de las respuestas mock/API: sin divergencias (`contraste-mock-api.md`).
- 503 con PostgreSQL parado y error de red con la API parada: el panel avisa, conserva la última lectura marcada como antigua y se recupera solo (`T036_*`). Con la API parada, el proxy de Vite devuelve 502.
- Comparación con 2025: `n_2025 = 18302`, coherente con el histórico cargado. Replay real: 0 eventos, sin error.
- Pruebas: 70 en Vitest, 8 archivos; el verificador comprobó 4 mutaciones (corte de profundidad, inicio de replay, nulos en `parse`, vacío tratado como error) y `dist/` sin mock.

## Decisiones del alumno

- P1 estructura de `src/` la del front externo; P2 comparación con 2025 en el cajón inferior y G5b reformulado como decisión propia; P3 retraso de ingesta calculado en el panel; P4 sin Chart.js; P5 borrar capas apagadas sin cambio visible; P6 valores por defecto aceptados (sin choque con la constitución).
- Instrucciones del 2026-11-10: config en tiempo de ejecución, mock con cinco escenarios y fuera de producción, cinco clases de profundidad, atribución, auditoría, magnitud nula, replay con 2025, G16 fuera de alcance y puerto 4200 con `strictPort`.

## Límites conocidos

- G16 (accesibilidad) no cubierta, decisión propia; G13 (despliegue y CORS) es de `despliegue-tunel`; G18 (mapa 2D) aplazada.
- Rendimiento con 5 000 eventos sin medir (el globo recorre todos los pilares para elegir el más cercano).
- En replay el periodo es fijo (2025) y `/api/estadisticas` trae 8 760 buckets horarios a cero que se pintan como barras vacías.
- El proxy de Vite devuelve 502 con la API parada («Error HTTP 502»); hasta 15 s en «Cargando…» con una API colgada.
- En móvil plegado solo se ve el primer aviso (en replay vacío «REPRODUCCIÓN +1»).
- Chunk principal de unos 2,3 MB (globo y three), sin dividir.
- Entre 768 y 1023 px se ve el diseño móvil.
- Sin navegador durante la implementación: capturas y recorrido a 375/768/1280 px pendientes del alumno (`T024_T026_capturas_pendientes.md`, `T027_T029_…`, `T030_T033_…`, `T034_T037_…`, `T038_T040_comprobaciones_pendientes.md`, todos en `docs/evidencias/panel-base-mock/`).

## Preguntas típicas de defensa

- **¿Por qué el panel no calcula estadísticas?** Porque la API las calcula en SQL con una sola transacción y así coinciden con los eventos; el cliente solo formatea y escala barras.
- **¿Cómo sabes que el mock no llega a producción?** `grep` de `__MOCK_BACKEND__` y «Sintético:» en `dist/` sin resultados (`T029_grep_dist.txt`, `T039_dist_sin_mock.txt`).
- **¿Qué pasa si la API cae?** Aviso, última lectura marcada como antigua, nunca «0 eventos»; se recupera sola.
- **¿Por qué una magnitud nula no es 0?** Un 0 es un valor real y falsearía el dato; se dibuja gris y «ND».
- **¿Y replay?** Hoy `replay.current_event` está vacío: el panel lo muestra como vacío; el cierre es de `013-replay`.
- **¿Por qué `config.json` y no variables de build?** Cambiar de mock a API o de URL no exige recompilar.

## Evidencias

- `docs/evidencias/panel-base-mock/`: `contraste-mock-api.md`, `auditoria-calculos-cliente.md`, `T035_tabla_filtros_totales.md`, `T036_*`, `T037_licencias.txt`, `T038_npm_test.txt`, `T039_*` (copia limpia con Node 24.18.0), más las comprobaciones pendientes citadas arriba.
- `docs/evidencias/subagentes/`: `verificador-panel-base-mock-bloque1.md` a `bloque5.md`, `plan-reviewer-panel-base-mock.md` y `plan-reviewer-panel-base-mock-enmienda.md`.
