# Costes (K6)

Cada cifra lleva dos etiquetas independientes:

- **Origen del dato:** MEDIDO (leído del sistema), SUPUESTO (lo aporta el alumno sin medirlo) o ESTIMADO (esfuerzo estimado).
- **Naturaleza del coste:** **en efectivo** (dinero que sale de verdad) o **imputado** (coste de oportunidad o reparto de algo que ya se posee; no sale dinero). Que algo sea imputado no lo hace cero: el equipo y el tiempo del alumno tienen valor aunque no se facturen.

Un mes se toma de 30 días (SUPUESTO). Tarifa eléctrica: 0,169 EUR/kWh = (0,11321 + 0,01986) x 1,0511 x 1,21; fuente: factura de comercializadora, jul-ago 2026 (sin datos personales ni el PDF).

## Detalle por categoría

| Categoría | Origen | Naturaleza | Fórmula | Entradas | Resultado |
|---|---|---|---|---|---|
| hardware | SUPUESTO | imputado | precio / vida_útil_meses x fracción_de_uso | precio = 1100 EUR (aprox.); vida_util = 48 meses; fraccion = 1 (implícita en la cifra de 22,9 EUR/mes) | 1100 / 48 x 1 = **22,92 EUR/mes** |
| electricidad | SUPUESTO | **en efectivo** | potencia_W / 1000 x horas_mes x EUR_por_kWh | potencia = 100 W; tarifa = 0,169 EUR/kWh; A: 12 h/día = 360 h/mes; B: 24/7 = 720 h/mes | A: 36 kWh x 0,169 = **6,08 EUR/mes**<br>B: 72 kWh x 0,169 = **12,17 EUR/mes** |
| almacenamiento | tamaño MEDIDO; tarifa SUPUESTA | efectivo = **0 EUR**; imputado | tamaño_BD_GB / 1820 GB x 22,9 EUR/mes (parte proporcional del disco del equipo) | tamaño = 0.0439215 GiB (MEDIDO, `pg_database_size`) = 0,04716 GB; disco = 1820 GB; 22,9 EUR/mes = hardware | **≈ 0,0006 EUR/mes** (despreciable) |
| transferencia | volumen MEDIDO/SUPUESTO (ver `transferencia.md`) | efectivo = **0 EUR** (hosting y túnel gratuitos); no se imputa | volumen = bytes por petición x 10 peticiones x visitas | 5 a 10 visitas/mes → 5,2 a 10,5 MiB/mes | sin coste monetario: no se aplica ninguna tarifa por GiB |
| mantenimiento | SUPUESTO | imputado (coste de oportunidad; no es cero aunque lo haga el alumno) | horas_mes x EUR_por_hora | horas = 2 h/mes; tarifa = 15 EUR/h | **30,00 EUR/mes** |
| dominio | SUPUESTO (importe anual aportado) | **en efectivo**; real y compartido, imputado entero a este proyecto | precio_anual / 12 | 22 EUR/año | **1,83 EUR/mes** |
| horas de desarrollo | ESTIMADO (horas) y SUPUESTO (tarifa, perfil junior) | imputado; **coste único**, no mensual | horas_totales x EUR_por_hora | 72 h (3 semanas x 3 días x 8 h; rango 54-90 h); 15 EUR/h | **1.080 EUR** (rango 810 a 1.350 EUR) |

## Tabla resumen (mensual)

Lo no mensual (desarrollo, 1.080 EUR) queda fuera de los totales. Todos los importes son SUPUESTOS; solo el tamaño de la base de datos y los bytes de transferencia son MEDIDOS.

| Concepto | Naturaleza | A: 12 h/día (EUR/mes) | B: 24/7 (EUR/mes) |
|---|---|---|---|
| Hardware | imputado | 22,92 | 22,92 |
| Electricidad | efectivo | 6,08 | 12,17 |
| Almacenamiento | imputado (efectivo 0) | 0,0006 | 0,0006 |
| Transferencia | efectivo 0, no imputada | 0 | 0 |
| Mantenimiento | imputado | 30,00 | 30,00 |
| Dominio | efectivo | 1,83 | 1,83 |
| **Total imputado** (suma de todo) | imputado | **≈ 60,8** | **≈ 66,9** |
| **Total en efectivo** (electricidad + dominio) | efectivo | **≈ 7,9** | **≈ 14,0** |

Comprobación: A = 22,92 + 6,08 + 0,0006 + 30,00 + 1,83 = 60,83; efectivo = 6,08 + 1,83 = 7,91. B = 22,92 + 12,17 + 0,0006 + 30,00 + 1,83 = 66,92; efectivo = 12,17 + 1,83 = 14,00.

Lectura: el coste en efectivo es pequeño; la mayor parte del coste total es el tiempo del alumno (mantenimiento) y la amortización del equipo, que no suponen un desembolso adicional pero sí un coste real. Una cuota gratuita no equivale a coste cero (ver abajo).

## Supuestos explícitos

- **Fracción de uso del hardware = 1** en los dos escenarios (A y B): todo el coste del equipo se imputa a este proyecto, aunque el equipo se use también para otras cosas. Es una cota superior del coste imputado del hardware.
- **Electricidad:** A = 12 h/día y B = 24/7 con 100 W constantes (SUPUESTO, no medidos); el consumo real varía con la carga.
- **Transferencia:** los 109.996 B por petición se midieron con la ventana de 24 h que devuelve `/api/eventos` por defecto y con el stack tal como estaba el 2026-11-13; con otro periodo o más eventos, la cifra cambia. Peticiones por visita = 10 min x 1 petición/min y 5 a 10 visitas al mes (SUPUESTO).
- **Tarifa de 15 EUR/h** para mantenimiento y desarrollo: perfil junior, SUPUESTO; es un coste de oportunidad, no un pago.
- No se contrata ningún servicio de pago ni se atribuye ningún beneficio económico al observatorio; el ROI (K8) no se calcula.

## Cuotas gratuitas (hosting estático, túnel y demás servicios)

cuota gratuita ≠ coste cero: superar el límite puede generar un cobro.

| Servicio | Plan y límite | Fecha de consulta | Consecuencia de superarlo |
|---|---|---|---|
| hosting estático (Netlify) | Plan gratuito. | 2026-11-13 | Se paraliza el servicio si la tasa es alta |
| túnel (Cloudflare Tunnel) | Gratuito. Límites no documentados en las fuentes consultadas | 2026-11-13 | No consta en las fuentes consultadas |
| dominio | 22 EUR/año (pago real), compartido con otros usos; imputado entero a este proyecto | 2026-11-13 | Si no se renueva, el túnel con dominio propio deja de funcionar |
