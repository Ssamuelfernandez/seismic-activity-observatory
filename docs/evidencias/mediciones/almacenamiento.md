# Almacenamiento medido

Tablas REALES: `pg_total_relation_size` (incluye índices y TOAST) y `pg_indexes_size`, con recuento real `count(*)`; bytes por fila = tamaño total / filas. Unidades: bytes (KiB = 1024 B).

| Esquema | Tabla | Filas | Total (bytes) | Índices (bytes) | Bytes por fila |
|---|---|---|---|---|---|
| ingest | ingest_run | 415 | 188416 | 65536 | 454.0 |
| ingest | ingest_state | 333 | 98304 | 40960 | 295.2 |
| ingest | raw_response | 204 | 8871936 | 73728 | 43,489.9 |
| live | current_event | 18635 | 8855552 | 3833856 | 475.2 |
| live | event_version | 18701 | 20389888 | 1138688 | 1,090.3 |
| live | exclusion | 3 | 49152 | 32768 | 16,384.0 |
| live | quarantine | 0 | 32768 | 24576 | no disponible |
| public | country | 177 | 65536 | 16384 | 370.3 |
| public | date_dim | 367 | 57344 | 16384 | 156.3 |
| replay | current_event | 22 | 81920 | 65536 | 3,723.6 |
| replay | event_version | 24 | 73728 | 16384 | 3,072.0 |
| replay | exclusion | 0 | 24576 | 16384 | no disponible |
| replay | quarantine | 0 | 32768 | 24576 | no disponible |

| Esquema | Total (bytes) |
|---|---|
| ingest | 9158656 |
| live | 29327360 |
| public | 122880 |
| replay | 212992 |

Tamaño de la base completa (`pg_database_size`): 47160343 bytes.

| Directorio | Bytes |
|---|---|
| data/historical | 14196282 |
| data/catalogo | 838726 |

Volumen de Docker de Postgres/Kafka: no disponible (el volumen de Docker no se lee desde el contenedor `tests`).

## Tablas de `bench` (SINTÉTICO)

| Filas | Montón (bytes) | Con los 4 índices (bytes) | Bytes por fila (con índices) | Índice: bytes |
|---|---|---|---|---|
| 1000 | 212992 | 466944 | 466.9 | current_event_pkey_s1000: 57344; ix_current_event_country_time_s1000: 49152; ix_current_event_mag_s1000: 40960; ix_current_event_time_s1000: 73728 |
| 10000 | 2424832 | 3981312 | 398.1 | current_event_pkey_s10000: 425984; ix_current_event_country_time_s10000: 335872; ix_current_event_mag_s10000: 245760; ix_current_event_time_s10000: 516096 |
| 100000 | 21823488 | 36315136 | 363.2 | current_event_pkey_s100000: 4087808; ix_current_event_country_time_s100000: 3104768; ix_current_event_mag_s100000: 2277376; ix_current_event_time_s100000: 4980736 |
