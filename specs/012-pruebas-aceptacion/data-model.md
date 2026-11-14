# Modelo de datos: Pruebas de aceptación (012)

No hay tablas ni columnas nuevas (DDL y contratos no cambian). El modelo describe los documentos que produce la feature.

## Ficha de prueba (`docs/evidencias/pruebas/NN-<nombre>.md`)

Nombres fijos: `01-evento-nuevo`, `02-reenvio`, `03-version-posterior`, `04-version-tardia`, `05-magnitud-nula`, `06-coordenadas-invalidas`, `07-evento-maritimo`, `08-reinicio-consumidor`, `09-cierre-tunel`, `10-reapertura-tunel`, `11-reproduccion-historica`.

| Apartado | Regla |
|---|---|
| Objetivo y requisito | Fila de la tabla I del checklist y requisitos relacionados (C, G9, J) |
| Precondiciones | Stack levantado o base temporal; qué datos son reales y cuáles sintéticos |
| Procedimiento | Pasos numerados y repetibles |
| Esperado | Una frase medible (recuentos, valores, texto en el panel) |
| Observado | Solo lo ejecutado, con fecha y origen; en 9 y 10, «pendiente de la demostración del alumno» |
| Evidencia | Enlaces a archivos que existen |
| Cómo repetir | Comando exacto (`docker compose --profile test run --rm tests pytest ... -q`) |
| Estado | `Observada`, `Observada (sintética)` o `Pendiente del alumno` |

Transición: «Pendiente del alumno» pasa a «Observada» solo cuando el alumno rellena horas y capturas (fuera de esta feature).

## Resumen (`docs/evidencias/pruebas/README.md`)

Tabla de 11 filas: prueba, esperado, observado (una línea), evidencia (enlace), cómo repetir, estado. Más las secciones «Huecos del panel en 9 y 10» y «Aislamiento de live» (huella antes y después).

## Caso sintético controlado

Evento `synthetic-acc-NN`, `is_synthetic = true`, solo en `TempDatabase`. Se envía por `process_message` y se lee por `request_api`. Nunca en `live` real.

## Plantilla del alumno (9 y 10)

Huecos: URL pública, hora de la última lectura, hora del cierre, hora del aviso, captura 1 (inicial), captura 2 (aviso o recuperación), hora de la reapertura, hora de la recuperación. Vacíos hasta que los rellene el alumno.

## Huella de `live`

`n_sinteticos` (count de `is_synthetic`), `n_current` y md5 de los `event_id || updated_ms` de las filas sintéticas, antes y después. Criterio: `n_sinteticos` y md5 iguales.
