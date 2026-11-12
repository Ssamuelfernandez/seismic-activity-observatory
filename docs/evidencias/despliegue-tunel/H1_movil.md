# H1: panel accesible desde otro dispositivo

**Estado: pendiente del alumno.** Cubre H1, SC-006.

## Pasos

1. Con Compose, la API y `cloudflared` encendidos (README, «Procedimiento de activación»), confirma `curl https://observatorio-api.ssamuelfernandez.net/api/salud` con 200.
2. En un móvil, desactiva el wifi y usa datos móviles.
3. Abre `https://observatorio.ssamuelfernandez.net`.
4. Espera a que cargue y comprueba que se ven el mapa y los datos (sin error de red ni de CORS).
5. Haz una captura con la URL visible en la barra y la hora del dispositivo.

## Esperado

El panel carga desde datos móviles y muestra eventos reales (o el aviso de la última lectura si no hay).

## Registro

| Campo | Valor |
|---|---|
| Fecha y hora | (pendiente) |
| Dispositivo y red | (pendiente) |
| Resultado | (pendiente) |

**Captura (URL visible):** (pendiente del alumno)
