# T030–T033: comprobaciones visuales pendientes (para el alumno)

No hay navegador en este entorno; no se adjuntan capturas. Lo comprobado por código y prueba temporal está en `T030_T033_vitest_temporal.txt` (texto de los avisos renderizado con `react-dom/server`).

Con `mode: "mock"` en `public/config.json` y `npm run dev` en un puerto libre (p. ej. `npx vite --port 4300 --strictPort`; el 4200 lo usa otro servidor):

1. `?scenario=truncated`: aviso «Mostrando 5000 de 6213 eventos» bajo la barra de filtros (escritorio) y como línea plegable en móvil (375 px). En el desplegable del estado, «Mostrados 5000 de 6213» y «Truncado: Sí».
2. `?scenario=replay`: aviso «REPRODUCCIÓN» visible. Abrir los filtros: el periodo muestra un botón desactivado «2025» y no hay fechas; la barra resumida dice «Reproducción · 2025 · …».
3. `?scenario=empty`: «Sin eventos en el intervalo» (sin rojo, no es error) y la lista dice «mostrados 0 · total 0 (API)».
4. Modo «Reproducción» con `?scenario=realistic` (el mock aplica `start`/`end` de 2025 y no hay eventos de 2025 en ese escenario): «REPRODUCCIÓN» + «Sin eventos reproducidos», sin banner rojo.
5. `?scenario=realistic`: cambiar magnitud mínima o país cambia a la vez globo, lista, tabla y estadísticas; la ficha abierta se cierra.
6. Lista «Eventos recientes», tabla y lista móvil: rótulos «mostrados N · total M (API)». Cajón de estadísticas: sin «máx.»; el panel de países dice «mostrados 6 de N países» solo si hay más de 6.
7. Estado desactualizado (solo con la API real, T036): «hace X min (calculado en el panel)» en el desplegable y en el aviso.
