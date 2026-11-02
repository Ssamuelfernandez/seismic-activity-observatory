# Guía de validación — contratos-y-modelo

Cómo comprobar que los entregables de esta feature son coherentes. Esta feature no arranca servicios; el DDL ya se probó en PostgreSQL 16 el 2-nov-2026 (evidencia en `docs/evidencias/contratos-y-modelo/`); la comprobación posterior en `consumidor-idempotente` es una prueba de integración. Detalles de campos y tablas: `contracts/` y `data-model.md` (no se repiten aquí).

## 1. Los ejemplos JSON son válidos y coherentes con el feed real

Desde la raíz del repositorio. Extrae los bloques JSON de los contratos y comprueba que se parsean:

```bash
python -I - <<'EOF'
import json, re, pathlib
for name in ("kafka-message.md", "api.md"):
    text = pathlib.Path("specs/001-contratos-y-modelo/contracts", name).read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)```", text, re.S)
    for i, b in enumerate(blocks, 1):
        json.loads(b)
    print(name, len(blocks), "bloques JSON válidos")
EOF
```

Resultado esperado: todos los bloques válidos. Contraste manual con `docs/evidencias/f1/explore_usgs_salida.txt` según la tabla de `contracts/api.md` §8.

## 2. El DDL se aplica y es idempotente

Requiere Docker en marcha (PostgreSQL desechable, sin datos del proyecto):

```bash
docker run -d --name pg-schema-check -e POSTGRES_PASSWORD=check -e POSTGRES_DB=check postgres:16
docker exec -i pg-schema-check psql -U postgres -d check -v ON_ERROR_STOP=1 < sql/001_schema.sql
docker exec -i pg-schema-check psql -U postgres -d check -v ON_ERROR_STOP=1 < sql/001_schema.sql   # 2.ª vez: sin errores
```

Resultado esperado: ambas ejecuciones terminan sin error.

## 3. `live` y `replay` son idénticos

```bash
docker exec pg-schema-check psql -U postgres -d check -At -c "
SELECT count(*) FROM (
  SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'live'
  EXCEPT
  SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'replay'
) d;"
```

Resultado esperado: `0` (y lo mismo invirtiendo el orden de los `SELECT`).

## 4. Tablas e índices coinciden con `db-schema.md`

```bash
docker exec pg-schema-check psql -U postgres -d check -At -c "
SELECT schemaname || '.' || tablename FROM pg_tables WHERE schemaname IN ('public','live','replay','ingest') ORDER BY 1;"
docker exec pg-schema-check psql -U postgres -d check -At -c "
SELECT schemaname || '.' || indexname FROM pg_indexes WHERE schemaname IN ('live','replay','ingest') ORDER BY 1;"
```

Resultado esperado: 13 tablas (2 en `public`, 4 en `live`, 4 en `replay`, 3 en `ingest`) y los índices de `db-schema.md` §4.

## 5. El esquema acepta los casos del feed real

Ejecutar el script `docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql` (T1–T18) y contrastar con la salida guardada en `prueba_esquema_001_salida.txt`:

```bash
docker exec -i pg-schema-check psql -U postgres -d check < docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql
```

Cubre: valores del feed (magnitud −0,06, profundidad negativa, nulos), rechazo de latitud 145, `NaN`, `source` inválido, país inexistente, ms que no coinciden con el `timestamptz` y `date_id` incoherente; clave foránea diferida; reglas de versiones (igual, mayor, antigua tardía, reenvío); cuarentena y exclusión únicas; aislamiento `live`/`replay`; ingesta; y las consultas Q1 y Q4. La salida de las dos aplicaciones del DDL está en `prueba_esquema_001_ddl_salida.txt`.

Limpieza: `docker rm -f pg-schema-check`.

## 6. Revisión cruzada

- `/speckit-analyze` sobre spec, plan y tareas.
- Revisión con el agente `plan-reviewer` antes de implementar.
- Comprobar a mano que `api.md` no contradice `docs/enunciado/CONTRATO-API.md` (tabla de `contracts/api.md` §7).
