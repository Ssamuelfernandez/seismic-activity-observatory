# T027–T029: comprobaciones pendientes del alumno (necesitan navegador)

No hay capturas: el implementador no tiene navegador. Se dejan los pasos; lo comprobado por código y por pruebas está en los archivos `T027_*`, `T028_*` y `T029_*` de esta carpeta.

1. **Mensaje de configuración inválida (T027).** `npm run build`, editar `dist/config.json` con `"mode": "otro"` y servir `dist/` (`npm run preview`): debe verse «Configuración no válida · Campo mode: debe ser "mock" o "api"». Repetir con `refreshSeconds: 0` y `apiBaseUrl: "api"` (debe nombrar cada campo). El validador ya devuelve `mode` en `T027_validateConfig_dist_otro.txt`.
2. **Mock no disponible en producción (T029).** Con `dist/config.json` en `"mode": "mock"` y `npm run preview`: el panel debe mostrar el aviso «Sin datos» con el texto «mock no disponible en este build» y ningún evento.
3. **Escenarios en desarrollo (T029).** `npm run dev` con `public/config.json` en `"mode": "mock"` y abrir `http://localhost:4200/?scenario=base`, `truncated`, `replay`, `empty`, `realistic`, y un valor desconocido (`?scenario=zzz`: carga `base` y la consola de desarrollo avisa). Comprobar: banner «Datos sintéticos» en todos; en `realistic`, cambiar periodo, magnitud y país cambia globo, tabla y estadísticas a la vez. Nota: `truncated` y `replay` no aplican los filtros (se devuelven tal cual).
4. **Interfaz sin origen (T029).** En el panel de filtros no hay «Origen de datos» ni etiqueta «Mock» en la barra (comprobado por grep en `T029_grep_interfaz_sin_origen.txt`).
5. **Restaurar** `public/config.json` a `"mode": "api"` tras las pruebas (el repo lo deja en `api`).
