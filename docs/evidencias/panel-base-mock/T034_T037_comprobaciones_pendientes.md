# Comprobaciones visuales pendientes del alumno (T034–T037)

No hay navegador en el entorno del implementador: nada de lo siguiente está comprobado a la vista. Arranque: `cd frontend && npx vite --port 4300 --strictPort` (o 4200 si está libre) con `public/config.json` en `mode: "api"` y el stack de Compose levantado.

## T034 — eventos reales con el proxy
- URL `http://localhost:4300/`. Se espera: globo con puntos reales (sin la etiqueta «Sintético»), lista de recientes y tabla con los mismos eventos, cajón «Estadísticas» con las cifras de la API, sin banner de error. Fuera de pantalla ya comprobado: `curl` y parse de las respuestas reales (`contraste-mock-api.md`).
- Guardar una captura con eventos reales.

## T035 — filtros a la vez (capturas con los filtros visibles)
- Cambiar periodo (1 h, 24 h, 7 d, 30 d, 1 año, rango), magnitud mínima (0, 2, 4) y país (uno con eventos como USA, «Sin país», uno sin eventos): globo, lista, tabla, estadísticas y estado deben cambiar a la vez. Los totales esperados de cada combinación están en `T035_tabla_filtros_totales.md` (p. ej. 24 h: 206 aprox.; 24 h M≥4: 21 aprox.; los valores varían con el tiempo, lo que importa es que lista, tabla y estadísticas coincidan con `stats.total`).
- Truncado: con los datos actuales no se trunca (máximo 5 000); no se puede ver el aviso «Mostrando N de M» con la API real salvo bajando `limit` (solo probado con `limit=50` por script). Verlo con `?scenario=truncated` en modo mock.
- Comparación con 2025 (cajón inferior): histórico cargado (`n_2025` 18 302 con M≥4); se espera una variación negativa parecida a -58 % y la nota de periodo incompleto; con `min_mag` 5 la comparación usa M≥5.
- Replay (conmutador de modo): se espera el aviso «REPRODUCCIÓN» y «Sin eventos reproducidos», sin error. Nota: en replay `/estadisticas` trae 8 760 buckets horarios a cero; comprobar que el gráfico por hora no se ve roto.

## T036 — fallo provocado (en pantalla)
- Con el panel abierto y datos: `docker compose stop api` → aviso de error, la última lectura se conserva marcada como antigua con su hora, nunca «0 eventos»; `docker compose start api` → se recupera en el siguiente refresco (60 s por defecto; bajar `refreshSeconds` para verlo antes) sin recargar.
- Con la API parada y recargando la página: «Sin datos» (no «0 eventos»). Con el proxy de Vite el fallo llega como HTTP 502 (mensaje genérico «Error HTTP 502»), no como «No se pudo conectar».
- `docker compose stop postgres` → aviso con el mensaje del 503 `database_unavailable`; `start postgres` y recuperación.
- Guardar capturas y la pestaña Red (una sola petición en vuelo por tipo, sin solapes).
- Límite conocido: sin lectura previa y con la API parada, TanStack pone el estado en «cargando» mientras dura cada reintento (con la API apagada falla en milisegundos; con un timeout de 15 s sería hasta 15 s de «cargando» antes de volver a «Sin datos»).

## T037 — atribución
- A 1280 px: línea de 11 px abajo a la derecha, legible sin pulsar nada, por encima del cajón abierto y sin tapar la flecha «Estadísticas» (centrada). A 375 px: franja fija en el pie bajo la barra de pestañas (2 líneas aprox.), fuera de las hojas; comprobar que no hay scroll horizontal. Ya comprobado por código: texto exacto, 11 px, contraste 7,7 : 1 (`T037_render_estatico.txt`).
- En el desplegable del estado ya no existe la línea de 9 px.
