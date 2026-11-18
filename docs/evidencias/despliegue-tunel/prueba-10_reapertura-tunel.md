# Prueba 10: reapertura del túnel

**Estado: parcial. No hay captura de la reapertura; la evidencia es la revisión de código, en `docs/evidencias/pruebas/`, y no se grabó demostración en vivo.** Cubre prueba 10, SC-006. Las capturas de `README.md` se tomaron desde la misma red del servidor y no sustituyen esta prueba. Se hace a continuación de la prueba 9, con el panel aún abierto.

## Pasos

1. Con el panel mostrando el aviso de la prueba 9, vuelve a lanzar `cloudflared`.
2. Comprueba `curl https://observatorio-api.ssamuelfernandez.net/api/salud` con 200. Anota la hora.
3. Sin recargar la página, espera al siguiente refresco.
4. Captura con la URL visible, el aviso retirado, datos actualizados y la hora.

## Esperado

El panel se recupera solo en el siguiente refresco, sin recargar: desaparece el aviso y se actualiza la lectura.

## Registro

Horas de reapertura y de recuperación: no registradas (no se grabó demostración en vivo).

**Evidencia:** la revisión de código, en [`../pruebas/10-reapertura-tunel.md`](../pruebas/10-reapertura-tunel.md).
