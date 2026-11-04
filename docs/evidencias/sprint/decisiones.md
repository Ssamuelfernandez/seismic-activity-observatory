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
