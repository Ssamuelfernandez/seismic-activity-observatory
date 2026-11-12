# Verificador replay, bloque 3 (T046-T049)

Todas verificadas. Sin hallazgos bloqueantes ni importantes.
- T046 verificada: pytest -m "not integration" tests/consumer tests/common tests/producer = 530 passed. consumer/pipeline.py sin diff.
- T047 verificada: compose.yaml con KAFKA_CONSUMER_TOPICS por defecto y volumen ro en producer; check_env_example rc=0; 5 servicios mas tests; config.md de 002 y contratos sin diff; README y .env.example documentan la variable.
- T048 verificada: integracion en Docker, 8 passed (con T049). Recuentos 26 / 22 / 24 / 0, live.* en 0, mode_topic_mismatch a cuarentena.
- T049 verificada: mode=replay con metadata.mode=replay y total 22, tiempos reales, comparison null, esquema vacio sin error; sin mode o live sin eventos replay.
- Volumen anadido al servicio tests (data/historical, ro): aprobado; coherente con el de producer y solo lectura.
- CODEMAP actualizado. git status sin cambios en docs/evidencias/consumidor-idempotente/.
- Limite conocido: G10 y prueba 11 (contenedores completos) quedan para el bloque 5.
