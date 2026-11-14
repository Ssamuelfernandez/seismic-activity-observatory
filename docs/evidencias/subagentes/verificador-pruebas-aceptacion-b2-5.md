# Verificación bloques 2-5 (T099-T117), pruebas-aceptacion

Veredicto global: todas las tareas verificadas; sin hallazgos bloqueantes ni importantes.

| Tarea | Veredicto | Prueba ejecutada |
|---|---|---|
| T099/T116 | verificada | `00_live_antes/despues.txt` con fecha y comando; SQL propio de solo lectura: 0 sintéticos en `live`, md5 igual (d41d8...), `n_current` ahora 18859: sube por el productor real, coherente con 18855 a 18858 |
| T100-T102 | verificada | Cabeceras con comando y fecha; 13, 45 y 8 passed. Re-ejecutado: test_acceptance_api 5 passed; replay 8 passed |
| T103-T104 | verificada | 4 plantillas `*_captura_pendiente.md` declaran pendiente y origen (la 03, sintética en TempDatabase) |
| T105 | verificada | Citas comprobadas contra el código: useObservatory.ts:43,49-51,67,73; StatusBanners.tsx:82-89 y 90-100; main.tsx:9; client.ts:26 y 55; config.json 60 s y 15000 ms; grep refetchIntervalInBackground sin resultados. Huecos confirmados |
| T106-T107 | verificada | 6 apartados, estado «Pendiente del alumno»; grep de «verifica en vivo» sin coincidencias en despliegue-tunel ni pruebas |
| T108 | verificada | `git diff`: solo cambia el texto de estado en README (línea 17) y fichas 9 y 10 |
| T109-T111 | verificada | 11 fichas, cada una con 6 apartados |
| T112-T113 | verificada | README con 11 filas, estados válidos; `00_enlaces.txt` 91 OK |
| T114-T115 | verificada | `suite_unitarias.txt`: 829 passed y 3 failed; `suite_integracion.txt`: 232 passed; `consumidor-idempotente` limpio en `git status` |
| T117 | verificada | CODEMAP con una fila coherente; sin diff en contratos, sql, enunciado, .specify; sin atribución a Claude |

Los 3 fallos de `tests/scripts/test_netlify_config.py` son preexistentes y de entorno. Los reproduje en solitario. El error es `FileNotFoundError: /app/frontend/.nvmrc`: el servicio `tests` no monta `netlify.toml` ni `frontend/`. Los dos archivos existen en el host. El test viene del commit `599b0c1` (despliegue-tunel) y esta feature no lo toca. Debe presentarse como «3 fallos de entorno, no causados por 012».

Hallazgos importantes: ninguno.

Límite conocido: el aviso y la recuperación en el túnel real (pruebas 9 y 10) siguen sin demostrar. Según el código, el aviso con hora y la recuperación solos funcionan. Con 60 s de refresco más 15 s de timeout pueden tardar unos 75 s. Con la pestaña oculta el refresco se pausa y volver a ella no lo fuerza, porque `refetchOnWindowFocus` es false. Los huecos están bien reportados.

Nota: las tareas marcadas `[x]` son solo T094-T098 (bloque 1); T099-T117 siguen sin marcar.
