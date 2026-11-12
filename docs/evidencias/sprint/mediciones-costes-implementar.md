# mediciones-costes — fase implementar (resumen)

**a) Decisiones por defecto**
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Índices en bench | localizados por columnas; definiciones leídas de pg_indexes | robusto, sin teclear nombres | sí |
| Veredicto de índice | «no concluyente» si N<3 o IQR solapados; «no justificado» si el plan no usa el índice | honesto con los datos | sí |
| replay.* con observatory_api | «no disponible» salvo replay.current_event; comparación completa con admin en take_snapshot | no escalar privilegios | sí |
| url en filas sintéticas | NULL | no enlazar eventos reales | sí |
| Costes | 6 categorías, todo PENDIENTE (alumno) salvo tamaños y bytes medidos | sin cifras inventadas | sí |

**b) Preguntas para el alumno**: reconstruir imagen `tests` (error preexistente de recogida en tests/common/test_api_config.py, falta load_cors_origins de la 010); rellenar costes/equipo/transferencia; repetir desde clon limpio (SC-007 parcial).

**c) Hallazgos**: 0 bloqueantes/importantes en los 5 bloques (informes verificador-mediciones-costes-bloque1..5). Límites: mediciones en la VM de Docker, no en el anfitrión; server_ms 7,057 ms en search.pg_seq.100000.first sin explicar (reconocido en teoria_vs_observado.md); cifra de escalado.md punto 5 (0,153964 ms) no coincide con la mediana middle (menor); el ensayo reducido sobrescribe tablas.

**d) Tareas**: T073–T093 verificadas (21/21). Corrida completa: 102 mediciones, 3 tamaños, N=15, 117 s, código 0, 60 planes EXPLAIN. 832 pruebas sin integración; 227 de integración + 1 error de recogida preexistente. bench eliminado; usgs_historical=18302.

**e) Comprobar**: decisiones provisionales de la spec; campos PENDIENTE (alumno).

Fase terminada.
