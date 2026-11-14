# pruebas-aceptacion — fase implementar (resumen)

Rama 012-pruebas-aceptacion. 24/24 tareas (T094–T117) verificadas por el verificador (informes: docs/evidencias/subagentes/verificador-pruebas-aceptacion-b1.md y -b2-5.md). 0 bloqueantes/importantes.

## Decisiones
- Captura con navegador imposible (extensión de Chrome no conectada): capturas 1, 3, 5 y 7 = plantillas con huecos (`docs/evidencias/pruebas/NN_captura_pendiente.md`).
- 9 y 10: fichas con procedimiento y plantilla; «Pendiente del alumno». Texto de despliegue-tunel corregido (README l.16-17, plantillas 09/10 l.3).
- Huecos del panel (solo reportados, sin corregir): refresco 60 s + timeout 15 s (~75 s), sin refetchIntervalInBackground, refetchOnWindowFocus false, T036 probó API local no túnel. Por código el panel sí muestra «Datos antiguos» con hora de última lectura y se recupera solo.

## Tareas / evidencia
- Nuevo test: tests/integration/test_acceptance_api.py (5 passed; pruebas 1, 3, 4, 5, 7 en TempDatabase, ids synthetic-acc-*).
- Pruebas 1–4: 13 passed; 5–8: 45 passed; 11: 8 passed.
- Suite completa: unitarias 829 passed, 3 failed (test_netlify_config.py: FileNotFoundError, el servicio `tests` no monta netlify.toml ni frontend/.nvmrc; preexistentes, de despliegue-tunel); integración 232 passed.
- Aislamiento: live 0 sintéticos antes y después, mismo md5; n_current 18855→18858 por el productor real.
- consumidor-idempotente restaurado con git checkout. CODEMAP actualizado.

## Qué comprobar
Los 3 fallos netlify (decidir: montar los archivos en compose en otra feature o aceptar la salvedad); capturas y pruebas 9/10 te tocan a ti.

Fase terminada.
