# Borrador: histórico 2025 (B12, B16, B18)

Material para la memoria y la defensa. Datos reales de USGS; los fixtures de prueba son sintéticos (`synthetic-…`, `is_synthetic=true`).

## Por qué lote y no Kafka (B16)

El contrato ya lo prevé: `kafka-message.md` §1 define `usgs_historical` como origen de un mensaje con el mismo sobre, y `db-schema.md` §1 lo admite como `source` de `live.current_event`. Se elige lote porque son 18 302 eventos de una sola vez, muy por encima del ritmo del feed y de la retención de 7 días del tema; no hay requisito de tiempo real; y el cargador llama a la misma función que el consumidor (`consumer.pipeline.process_record`), por lo que validación, versión, cuarentena y país son idénticas. Coste asumido: no se ejerce el camino Kafka en esta carga (research D10).

## Instantánea a la fecha de extracción (B18)

El histórico es una instantánea: cada evento tiene la versión (`updated`) que USGS devolvía el día de la descarga, registrada en `manifest.json`. No contiene todas las revisiones pasadas ni reconcilia las posteriores. Descarga: 12 consultas mensuales (M≥4, `eventtype=earthquake`), dedup por `id` y contraste del total único (18 302) con el `count` anual de USGS.

## Recuperar un hueco de más de 24 h (B12)

El feed en vivo cubre 24 h; si el productor se detiene más tiempo, los eventos intermedios se recuperan por lote con el mismo mecanismo. Comando ensayado en T021 con datos reales (30 eventos, 2025-12-30 a 2025-12-31):

```bash
uv run python -m historical.download_main --start 2025-12-30T00:00:00 --end 2025-12-31T00:00:00
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v ./data/historical:/app/data/historical:ro consumer python -m historical.load_main
```

El archivo `usgs_gap_<inicio>_<fin>.geojson` se añade a `gaps` del manifiesto sin alterar los totales de 2025. Resultado del ensayo: huella de `current_event` idéntica antes y después (`docs/evidencias/historico-2025/hueco_ensayo.out`); lo ya presente no se duplica y una versión con `updated` menor no retrocede.

## Decisiones

- **`source=usgs_historical`, no `'historical'`**: el brief decía `historical`, pero el contrato y `sql/001_schema.sql` fijan `usgs_historical`; se usa el del contrato, sin cambiarlo.
- **La cuarentena la cuenta el cargador (Q) desde `process_record`**: el rol `observatory_consumer` solo tiene INSERT en `live.quarantine`, no SELECT, así que el recuento se obtiene de lo que devuelve `process_record`. La verificación es `|U| − |Q|` eventos en `current_event`.
- **`MessageRef` con `None`**: el histórico no pasa por Kafka; `partition` y `offset` admiten `None` y `kafka_columns(ref)` deja las columnas `kafka_*` nulas. Es el único cambio en código compartido; las pruebas de 003–005 siguen pasando.
- **Archivos versionados** en `data/historical/` (14 MB), de modo que un clon reproduce la carga sin red; el sha256 del manifiesto se comprueba antes de escribir nada.

## Límites conocidos

- Carrera entre `count` y descarga: si USGS publica una revisión entre ambas, el total puede no cuadrar y el error pide repetir.
- `carga1.out` no muestra `new=18302` porque se ejecutó con una imagen anterior del consumidor; la cifra se comprueba en la verificación SQL.
- La verificación de Q no es independiente: sale del mismo procesamiento que se verifica.
- País con el catálogo simplificado `ne_110m` (límite de `geografia-pais`); sin fuzz de archivos corruptos más allá de sha256 distinto o ausente.
