# Captura 3 (prueba 3, versión posterior): plantilla pendiente

**Estado: pendiente de captura del alumno.** Sin herramienta de navegador (T103). Además, esta captura es siempre plantilla por decisión de la spec: **datos sintéticos (TempDatabase), no visibles en el panel público; evidencia principal: SQL de T095** (`test_later_version_changes_current_and_aggregates`, salida en [`01-04_pytest.txt`](01-04_pytest.txt)) y [`../consumidor-idempotente/bloque3_prueba3_4_versiones.out`](../consumidor-idempotente/bloque3_prueba3_4_versiones.out).

- **Origen de los datos: datos sintéticos** (`synthetic-acc-*`, `is_synthetic = true`, solo en `TempDatabase`). No se toca la base real para mostrarlos.
- **URL**: `https://observatorio.ssamuelfernandez.net/` (el panel público no puede mostrar estos datos; solo se rellenaría si el alumno monta un panel local con datos sintéticos etiquetados).
- **Fecha y hora de la captura (UTC)**: ______

## Qué debería verse (si el alumno la hace en un panel local etiquetado)

Tras una versión con `updated` posterior: los datos actuales del evento cambian (otro país y otra hora), el recuento por país y por hora cambia, y la etiqueta «Datos sintéticos» es visible.

## Imagen

![Captura 3: versión posterior (sintética)](03_captura.png)

(hueco: guardar como `docs/evidencias/pruebas/03_captura.png`).
