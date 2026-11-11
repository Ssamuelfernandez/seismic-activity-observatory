# Capturas pendientes (T024, T025, T026)

No hay navegador en el entorno del agente, así que **no se ha hecho ninguna captura**. Las hace el alumno a mano. Todo lo demás de T024, T025 y T026 se probó con comandos (ver `T024_*`, `T025_*`, `T026_*` en esta carpeta).

Escenario común: `npm run dev` en `frontend/` (puerto 4200) con `src/config.json` en `"dataSource": "mock"` (el mock en memoria del front externo; el `config.json` compilado sigue siendo el del origen hasta T027). Abrir `http://localhost:4200/`, ventana de 1280 × 800, sin tocar el globo (vista inicial Mediterráneo, zoom 2, giro automático parado con el puntero sobre el globo si se quiere la misma cámara).

| Tarea | Captura que falta | Cómo |
|---|---|---|
| T024 («antes» de T025) | Globo con el mock, referencia de apariencia | Hacerla **con el código de `_import-front/globo-lab/`** (`npm run dev` allí) o con el commit anterior a T025: el árbol actual ya tiene T025/T026 aplicados. Guardar como `T024_globo_antes.png`. |
| T025 («después») | Mismo escenario y cámara que la «antes» | Con el código actual. `T025_globo_despues.png`. Debe verse igual (SC-017): prismas, anillos M ≥ 4, etiquetas M ≥ 5, tierra, retícula. |
| T026 | Leyenda con las cinco clases de profundidad con su rango (`< 10 km`, `10–35 km`, `35–70 km`, `70–300 km`, `≥ 300 km`) y el gris ND | `T026_leyenda.png` |
| T026 | Un evento de magnitud nula (sin anillo ni etiqueta, barra gris, tooltip «ND») | El mock en memoria **no genera magnitud nula** (T028 crea ese caso en `realistic`). Hasta entonces, comprobarlo tras T028/T029 o editando a mano un evento de `mock.ts`. `T026_magnitud_nula.png` |

Diferencia esperada entre «antes» y «después»: el árbol actual ya incluye T026, así que cambian a propósito (a) la leyenda (cinco clases en lugar de tres) y (b) el color de los prismas de 10 a 300 km (las clases intermedias son nuevas). SC-017 se comprueba sobre lo demás: mismas capas, mismos anillos y etiquetas, misma tierra y retícula, sin arcos, celdas, mapa de calor ni marcadores. Si se quiere una comparación pura de T025, hacer la «después» antes de aplicar T026 no es posible ya; basta con que lo demás coincida.
