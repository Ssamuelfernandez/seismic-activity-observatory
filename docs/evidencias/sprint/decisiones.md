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
