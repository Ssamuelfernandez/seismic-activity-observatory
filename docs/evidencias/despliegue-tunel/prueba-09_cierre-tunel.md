# Prueba 9: cierre del túnel

**Estado: parcial. La evidencia es la captura del panel con el túnel cerrado y la revisión de código, en `docs/evidencias/pruebas/`; no se grabó demostración en vivo.** Cubre prueba 9, G9 (prueba real), SC-006. No hay capturas en esta carpeta: las capturas de `README.md` desde la misma red del servidor no sustituyen esta prueba.

## Pasos

1. Con el túnel abierto, abre el panel público y espera a ver datos (anota la hora de la última lectura).
2. Captura inicial con la URL visible.
3. Cierra `cloudflared` (Ctrl+C) sin recargar el panel. Anota la hora.
4. Espera al siguiente refresco del panel (`refreshSeconds` de `config.json`).
5. Captura con la URL visible, el aviso de fallo y la hora.

## Esperado

El panel muestra el aviso de fallo de conexión y conserva e identifica la última lectura correcta, sin quedarse en blanco.

## Registro

Horas de cierre y de recuperación: no registradas (no se grabó demostración en vivo).

**Evidencia:** la captura de la prueba 9 y la revisión de código, en [`../pruebas/09-cierre-tunel.md`](../pruebas/09-cierre-tunel.md).
