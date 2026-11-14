# Prueba 9: cierre del túnel

## 1. Objetivo y requisito

Tabla I, prueba 9; G9 (el panel muestra el fallo y conserva la última lectura). Requisitos FR-007 y FR-009, SC-004.

## 2. Procedimiento

Con el servidor en marcha y el panel público abierto en una pestaña **visible** (no en segundo plano).

1. Abre `https://observatorio.ssamuelfernandez.net/` y espera a ver datos reales. Anota la hora de la última lectura que indica el panel (hueco A).
2. Captura inicial con la URL visible (hueco: captura 1).
3. Cierra `cloudflared` (Ctrl+C) **sin recargar** el panel. Anota la hora de cierre (hueco B).
4. Espera al siguiente refresco: hasta 60 s (`refreshSeconds`) más 15 s (`timeoutMs`), unos 75 s. No recargues ni cambies de pestaña.
5. Cuando aparezca el aviso, anota la hora (hueco C) y captura con la URL visible (hueco: captura 2).

## 3. Esperado

El panel muestra el aviso «Datos antiguos» («No se pudo actualizar (...) Se muestra la última lectura correcta, de {edad} ({hora UTC})»), la hora de la última lectura coincide con la del paso 1, y los datos anteriores siguen visibles (no queda en blanco ni muestra «0 eventos»). Según el código: `frontend/src/components/StatusBanners.tsx:82-89` y `frontend/src/shared/hooks/useObservatory.ts:49-51`. Detalle y huecos en [`09-10_revision_codigo.txt`](09-10_revision_codigo.txt).

## 4. Observado

**Pendiente de la demostración del alumno.** No se ha ejecutado. Solo hay revisión de código (que dice que el comportamiento existe), no observación en el túnel real.

Plantilla a rellenar:

| Dato | Valor |
|---|---|
| URL pública | ______ |
| Hora de la última lectura (A) | ______ |
| Hora del cierre (B) | ______ |
| Hora del aviso (C) | ______ |
| Hora de la última lectura mostrada en el aviso | ______ |
| Captura 1 (inicial) o clip | ______ |
| Captura 2 (aviso) | ______ |

## 5. Evidencia

- Revisión del código: [`09-10_revision_codigo.txt`](09-10_revision_codigo.txt).
- Prueba de estado derivado del panel (Vitest): `frontend/tests/dataState.test.ts`.
- Antecedente (API local parada, no el túnel): [`../panel-base-mock/T036_ciclo_refresco.txt`](../panel-base-mock/T036_ciclo_refresco.txt).
- Ficha de despliegue: [`../despliegue-tunel/prueba-09_cierre-tunel.md`](../despliegue-tunel/prueba-09_cierre-tunel.md).
- Capturas del alumno: pendientes.

## 6. Cómo repetir y estado

Cómo repetir: los pasos de la sección 2, con el túnel real (`cloudflared`). No hay comando automático.

**Estado: Pendiente del alumno.** Pasa a «Observada» solo cuando el alumno rellene horas y capturas. Hasta entonces no se afirma que esté comprobada en el túnel real.
