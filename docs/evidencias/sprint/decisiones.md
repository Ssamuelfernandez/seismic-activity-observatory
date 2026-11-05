# Decisiones para la defensa oral

| Feature | Decisión | Alternativa descartada | Motivo |
|---|---|---|---|
| productor-live | Retirar sintéticos del productor y adaptar el check A1 de `scripts/verify_stack.py` a `is_synthetic=false`; se conserva `common/synthetic_event.py` | Mantener un modo sintético en el productor | El productor live debe publicar solo datos reales de USGS; el módulo sintético sigue disponible para pruebas |
| productor-live | `GRANT SELECT, DELETE` sobre `ingest.raw_response` en `sql/002_roles.sql`; no se edita `db-schema.md` | Modificar el contrato `db-schema.md` §1.1 | `002_roles.sql` no es contrato; db-schema §3.9 delega la retención en la feature; evita tocar contratos |
| productor-live | Retención de 7 días y hash de `raw_response` sobre `features` en JSON canónico | Hash del cuerpo completo; retención indefinida | `metadata.generated` cambia cada minuto y rompería la deduplicación; 7 días acota el almacenamiento |
| productor-live | Fallo de Kafka a mitad de ciclo solo en log, sin segunda fila en `ingest_run` | Registrar una segunda fila de fallo | Ack antes de marca garantiza no perder ni duplicar; simplicidad |
| productor-live | Volumen PostgreSQL existente: reaplicar el GRANT (quickstart §0) o `down -v` | Migración automática | Proyecto de clase; basta documentarlo |
| productor-live | CODEMAP se actualiza una sola vez al final (T021), desviación declarada de CLAUDE.md | Actualizar tras cada tarea | Proporcionalidad: 22 tareas, el mapa solo importa al cierre |
| productor-live | Feed `all_day.geojson` configurable por `USGS_FEED_URL`; backoff exponencial con jitter 2-60 s y timeout 10 s; solo urllib, sin dependencias nuevas | Librería `requests`/`httpx` | Cumple enunciado y latido máx. 120 s; constitución §11 |
| productor-live | Criterio de grep `synthetic` en `producer/`: sin lógica sintética, queda solo la columna `is_synthetic` | Renombrar la columna o vaciar el grep | La columna es del contrato y renombrarla lo rompería |
| productor-live | La `key` de `publisher.py` pasa a `str \| None`, con `acks=all` e idempotencia intactos | Descartar los eventos sin `id` | No perder eventos reales |
| geografia-pais | Geometría con Shapely 2 (STRtree, covered_by) sin GeoPandas | GeoPandas, citado en el roadmap | Más ligera, sin pandas; basta para punto-en-polígono |
| geografia-pais | `type != earthquake` no tiene motivo nuevo de cuarentena en el consumidor; se demuestra en el productor (exclusión) | Añadir motivo de rechazo en el consumidor | kafka-message.md §3/§6 no lo definen; no se toca el contrato |
| geografia-pais | Catálogo de países cargado en el consumidor al arrancar | Carga en el productor o por consulta | Lo permite db-schema.md §1.1 y evita lecturas repetidas |
| geografia-pais | El borde cuenta como dentro (covers) | Excluir el borde | Criterio del roadmap F5; evita perder eventos en frontera |
| geografia-pais | Empate entre polígonos: menor ADM0_A3 y log `country_tie` | Elección arbitraria o duplicar el evento | Resultado determinista y reproducible |
| geografia-pais | Sin polígono: `country_id` NULL, sin cuarentena, cuenta en totales | Mandar a cuarentena | Prueba 7: eventos oceánicos son válidos y no se pierden |
| geografia-pais | No se validan geometrías del catálogo (USA y SDN tienen autointersecciones menores); solo se rechazan las vacías, sin buffer(0) | Validar y reparar con buffer(0) o rechazar geometrías inválidas | Validar bloquearía el arranque con el catálogo real; el archivo se usa tal cual (research.md D6) |
| geografia-pais | T010 reescribe dos pruebas de 003 que esperaban el comportamiento anterior | Mantenerlas y forzar el comportamiento antiguo | El comportamiento esperado cambia por diseño de esta feature |
| historico-2025 | `source = usgs_historical` en la carga | `historical` (valor del brief) | Es el valor que permiten el CHECK de `sql/001_schema.sql` y kafka-message.md §1; usar otro rompería el contrato |
| historico-2025 | Carga por lote directa a `live`, sin pasar por Kafka | Publicar el histórico en Kafka | kafka-message.md §1 y db-schema.md §1 reservan el lote para el histórico; evita saturar el broker |
| historico-2025 | El cargador reutiliza `consumer.pipeline.process_record` con `partition`/`offset` = None (`MessageRef` los admite) | Duplicar la lógica de validación/transformación en el cargador | Cambio mínimo, una sola lógica; las columnas kafka_* son nullable en el esquema |
| historico-2025 | Hueco >24 h cubierto con `--start/--end` en el descargador, registrado en `gaps` del manifiesto | Procedimiento manual o ignorar el hueco | Mismo mecanismo reproducible y trazable |
| historico-2025 | Archivos en `data/historical/`; se versionan si pesan <50 MB (medido en T019), si no `.gitignore` | Versionar siempre o nunca | Regla del brief; reproducibilidad sin inflar el repositorio |
| historico-2025 | Deduplicación por `id` conservando el `updated` mayor; sin id/updated va a cuarentena | Conservar la primera aparición | Evita perder revisiones y duplicar eventos |
| historico-2025 | Mes con >20000 eventos: partición recursiva por punto medio, fusionada en el mismo archivo mensual | Descargar por semanas siempre | Solo se subdivide cuando el límite de USGS lo obliga |
| historico-2025 | Si USGS revisa un evento entre `count` y la descarga, error y repetición manual | Reintento automático | Caso raro; simplicidad |
