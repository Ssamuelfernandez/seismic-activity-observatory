# Transferencia medida

MEDIDO: bytes del cuerpo de cada respuesta de `http://api:8000` (nombre de servicio de Compose), sin compresión, con los datos reales del stack en el momento de la medición. El límite por defecto de `/api/eventos` coincide con el máximo (`API_MAX_EVENTS`).

| Ruta | Estado HTTP | Bytes | KiB |
|---|---|---|---|
| /api/eventos (limit por defecto) | 200 | 107162 | 104.7 |
| /api/eventos?limit=5000 (máximo) | 200 | 107162 | 104.7 |
| /api/estadisticas | 200 | 2762 | 2.7 |
| /api/salud | 200 | 72 | 0.1 |

SUPUESTO: una petición del panel carga eventos (límite por defecto), estadísticas y salud.

| Concepto | Valor | Etiqueta |
|---|---|---|
| Bytes por petición = 107162 + 2762 + 72 | 109996 | MEDIDO |
| Duración de una visita | 10 min | SUPUESTO |
| Frecuencia | 1 petición por minuto | SUPUESTO |
| Peticiones por visita = 10 min x 1/min | 10 | SUPUESTO |
| Bytes por visita = 109996 x 10 | 1 099 960 B (≈ 1,05 MiB; 0,00102442 GiB) | SUPUESTO (cálculo a partir de lo medido) |
| Visitas por mes | 5 a 10 | SUPUESTO |

| Escenario | Fórmula | Volumen mensual |
|---|---|---|
| 5 visitas/mes | 5 x 1 099 960 B | 5 499 800 B ≈ 5,2 MiB ≈ 0,00512 GiB |
| 10 visitas/mes | 10 x 1 099 960 B | 10 999 600 B ≈ 10,5 MiB ≈ 0,01024 GiB |

Coste en EUR: **0 en efectivo**, porque el hosting (Netlify) y el túnel (Cloudflare) son gratuitos; no se imputa ninguna tarifa por GiB (ver `costes.md`). Las cifras suponen que cada petición descarga la respuesta completa de eventos; el panel no hace cacheo ni peticiones condicionales en este cálculo.
