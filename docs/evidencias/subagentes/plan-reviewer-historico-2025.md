Sin hallazgos bloqueantes ni importantes. Veredicto: Listo para tu revisión.

Comprobaciones hechas:
- Cambio compartido MessageRef.partition/offset None: no rompe db-schema. En sql/001_schema.sql, kafka_topic, kafka_partition y kafka_offset son nullable en current_event, event_version y quarantine (líneas 123-125, 149-151, 236-238, 258-260). La clave única de cuarentena (original_sha256, reason) no usa las columnas kafka_*. kafka-message.md §1 reserva `usgs_historical` para la carga por lote.
- Tests 003–005: T010 ejecuta la suite completa antes y después, exige 0 pruebas rotas y vuelve a pasar la integración. Con referencia real el comportamiento queda igual.
- B12–B18: todos están en la spec y tienen tarea y prueba (tabla de trazabilidad coherente entre plan, spec y tasks).
- Constitución: §1, §2, §4–§7 y §14 tienen prueba (T014–T018). No hay replay, API, frontend ni Kafka. `source` va como `usgs_historical`, que es el valor del contrato, aunque el brief diga `historical`. Hay 25 tareas en 5 bloques.
- Contratos: ninguna tarea los modifica. T025 comprueba que el diff queda vacío.

Límites conocidos (una línea cada uno, no son hallazgos):
- T011 usa partition=None y depende de T010, pero la nota de dependencias solo cita T010 antes de T014–T016. Basta ejecutar T010 antes de T011.
- Si USGS revisa un evento entre `count` y la descarga, T007 termina con error y pide repetir. No reintenta solo, y es una decisión ya documentada.

Decisiones del alumno: las tres preguntas de la spec (opción --start/--end, process_record tal cual, versionar o no los archivos según el tamaño) están resueltas o tienen regla en FR-019. Solo hay que confirmarlas.
