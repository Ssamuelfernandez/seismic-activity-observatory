# Transferencia medida

MEDIDO: bytes del cuerpo de cada respuesta de `http://api:8000` (nombre de servicio de Compose), sin compresión, con los datos reales del stack en el momento de la medición. El límite por defecto de `/api/eventos` coincide con el máximo (`API_MAX_EVENTS`).

| Ruta | Estado HTTP | Bytes | KiB |
|---|---|---|---|
| /api/eventos (limit por defecto) | 200 | 107162 | 104.7 |
| /api/eventos?limit=5000 (máximo) | 200 | 107162 | 104.7 |
| /api/estadisticas | 200 | 2762 | 2.7 |
| /api/salud | 200 | 72 | 0.1 |

SUPUESTO: una visita carga eventos (límite por defecto), estadísticas y salud.

| Concepto | Valor |
|---|---|
| Bytes por visita (MEDIDO) | 109996 |
| Visitas por mes | PENDIENTE (alumno) |
| Volumen mensual = visitas x bytes por visita (SUPUESTO) | no calculable |
