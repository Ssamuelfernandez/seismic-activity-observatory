# Costes (K6)

MEDIDO solo lo que se mide (tamaños, bytes de transferencia). Todo lo demás es SUPUESTO y queda como `PENDIENTE (alumno)`; mientras falte una entrada, el resultado es «no calculable» (nunca 0).

| Categoría | Etiqueta | Fórmula | Entradas (valor; origen; unidad) | Resultado |
|---|---|---|---|---|
| hardware | SUPUESTO | precio / vida_útil_meses x fracción_de_uso | precio = PENDIENTE (alumno); SUPUESTO; EUR<br>vida_util = PENDIENTE (alumno); SUPUESTO; meses<br>fraccion = PENDIENTE (alumno); SUPUESTO; 0-1 | no calculable |
| electricidad | SUPUESTO | potencia_W / 1000 x horas_encendido_mes x EUR_por_kWh | potencia = PENDIENTE (alumno); SUPUESTO; W<br>horas = PENDIENTE (alumno); SUPUESTO; h/mes<br>tarifa = PENDIENTE (alumno); SUPUESTO; EUR/kWh | no calculable |
| almacenamiento | SUPUESTO | GiB medidos x EUR_por_GiB_mes | gib = 0.0439215; MEDIDO; GiB (base 1024, `pg_database_size`)<br>tarifa = PENDIENTE (alumno); SUPUESTO; EUR/GiB-mes | no calculable |
| transferencia | SUPUESTO | GiB por visita medidos x visitas_mes x EUR_por_GiB | gib_visita = 0.000102442; MEDIDO; GiB por visita<br>visitas = PENDIENTE (alumno); SUPUESTO; visitas/mes<br>tarifa = PENDIENTE (alumno); SUPUESTO; EUR/GiB | no calculable |
| mantenimiento | SUPUESTO | horas_mes x EUR_por_hora | horas = PENDIENTE (alumno); SUPUESTO; h/mes<br>tarifa = PENDIENTE (alumno); SUPUESTO; EUR/h | no calculable |
| horas de desarrollo | SUPUESTO | horas_totales x EUR_por_hora | horas = PENDIENTE (alumno); SUPUESTO; h<br>tarifa = PENDIENTE (alumno); SUPUESTO; EUR/h | no calculable |

## Cuotas gratuitas (hosting estático, túnel y demás servicios)

cuota gratuita ≠ coste cero: superar el límite puede generar un cobro.

| Servicio | Límite | Fecha de consulta | Consecuencia de superarlo |
|---|---|---|---|
| hosting estático (Netlify) | PENDIENTE (alumno) | PENDIENTE (alumno) | PENDIENTE (alumno) |
| túnel (Cloudflare Tunnel) | PENDIENTE (alumno) | PENDIENTE (alumno) | PENDIENTE (alumno) |
| otros servicios usados | PENDIENTE (alumno) | PENDIENTE (alumno) | PENDIENTE (alumno) |
