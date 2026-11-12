# Informe plan-reviewer — despliegue-tunel (010)

Veredicto: Listo para revisión. 0 bloqueantes, 0 importantes.

- Cobertura: F9, F10, F5, G13, H1–H4, A8, G9 y pruebas 9 y 10 tienen tarea (T059–T072) o fila "pendiente del alumno" (P1–P9). Pruebas 9, 10 y H1 solo a mano con el túnel real; plantillas en T069.
- Contratos: CORS y `ngrok-skip-browser-warning` salen de CONTRATO-API.md ("Acceso desde Netlify"); spec y plan citan api.md sin copiarlo. Sin cambios en contrato, enunciado, constitución ni SQL.
- Constitución: §7 (T065), §10 (T061, T067), §11 (T063), §12, §16 (T071, T072), §19 cumplidas. T070 no toca checklist, constitución, contratos, enunciado ni specs 002 y 007.
- Hechos del repo verificados: client.ts concatena apiBaseUrl + /eventos (apiBaseUrl con /api correcto); create_app() desactiva /docs, /redoc, /openapi.json; errors.py traduce 404/405; compose publica solo 127.0.0.1:8000 y API_MAX_EVENTS=5000; existen frontend/mock y .nvmrc; vite.config.ts excluye el mock del build de producción.
- 14 tareas en 5 bloques (máx. 25 y 5). 7 preguntas del alumno, todas con decisión provisional.

Límites conocidos:
- Los 500 los genera el middleware exterior de Starlette y no llevan cabeceras CORS; el panel los trata como fallo de la API.
- La revisión no verifica que las capturas manuales de las pruebas 9 y 10 se hagan.
