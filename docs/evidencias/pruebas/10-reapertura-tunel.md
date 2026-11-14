# Prueba 10: reapertura del túnel

## 1. Objetivo y requisito

Tabla I, prueba 10; G9 (el panel se recupera solo). Requisitos FR-007 y FR-009, SC-004.

## 2. Procedimiento

A continuación de la prueba 9, con el panel aún abierto, mostrando el aviso «Datos antiguos» y la pestaña **visible**.

1. Vuelve a lanzar `cloudflared`. Anota la hora de reapertura (hueco D).
2. Comprueba `curl https://observatorio-api.ssamuelfernandez.net/api/salud` con 200 y anota la hora.
3. **Sin recargar la página**, espera al siguiente refresco: hasta 60 s (`refreshSeconds`) más hasta 15 s de timeout, unos 75 s.
4. Cuando desaparezca el aviso, anota la hora (hueco E) y captura con la URL visible, el aviso retirado y la lectura actualizada (hueco: captura 3 o clip).

## 3. Esperado

En el siguiente refresco desaparece el aviso «Datos antiguos» y la hora de la última lectura se actualiza, sin recargar la página. Según el código: `refetchInterval` sigue activo tras el error (`frontend/src/shared/hooks/useObservatory.ts:49`), y las condiciones de `frontend/src/components/StatusBanners.tsx:82-89` dejan de cumplirse cuando `error` es nulo. Huecos en [`09-10_revision_codigo.txt`](09-10_revision_codigo.txt): `refetchOnWindowFocus: false` (volver a la pestaña no fuerza refresco) y sin `refetchIntervalInBackground`.

## 4. Observado

**Pendiente de la demostración del alumno.** No se ha ejecutado.

| Dato | Valor |
|---|---|
| URL pública | ______ |
| Hora de la reapertura (D) | ______ |
| `curl /api/salud` con 200 a las | ______ |
| Hora de la recuperación (E) | ______ |
| Nueva hora de última lectura | ______ |
| Captura 3 (aviso retirado) o clip | ______ |
| Captura 4 (opcional, lectura actualizada) | ______ |

## 5. Evidencia

- Revisión del código: [`09-10_revision_codigo.txt`](09-10_revision_codigo.txt).
- Ficha de despliegue: [`../despliegue-tunel/prueba-10_reapertura-tunel.md`](../despliegue-tunel/prueba-10_reapertura-tunel.md).
- Antecedente (API local, no el túnel): [`../panel-base-mock/T036_ciclo_refresco.txt`](../panel-base-mock/T036_ciclo_refresco.txt).
- Capturas del alumno: pendientes.

## 6. Cómo repetir y estado

Cómo repetir: los pasos de la sección 2, a continuación de la ficha [`09-cierre-tunel.md`](09-cierre-tunel.md). No hay comando automático.

**Estado: Pendiente del alumno.** Hasta que el alumno rellene horas y capturas, no se afirma que esté comprobada en el túnel real.
