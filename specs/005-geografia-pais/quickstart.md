# Guía de comprobación: Geografía y país

Pasos para comprobar la feature una vez implementada (T001–T025). Comandos en Git Bash; los de Docker y `uv` son iguales en PowerShell.

## 1. Unitarias (sin Docker)

```bash
uv run pytest -m "not integration" -q
uv run pytest tests/common/test_geo.py -q
```

Esperado: todo en verde; `test_geo.py` incluye 177 entidades con `ADM0_A3` único, Madrid -> `ESP`, Atlántico -> `None`, frontera y empate estables.

## 2. Integración con PostgreSQL real

```bash
docker compose up -d postgres
docker compose --profile test build tests
docker compose --profile test run --rm tests pytest -m integration -q -s
```

Esperado: catálogo de 177 filas, carga repetida sin cambios, y los casos sintéticos de `tests/integration/test_geography*.py`.

## 3. Escenario con Kafka real (pruebas 5 y 7)

```bash
docker compose build producer
python scripts/verify_consumer.py geo --yes
```

Hace `down -v`, levanta Kafka, PostgreSQL y el consumidor, comprueba `catalog loaded total=177 inserted=177 updated=0`, publica los casos sintéticos y consulta la base. Esperado:

| Caso (id `synthetic-geo-…`) | Resultado |
|---|---|
| `madrid` (lon -3,70 lat 40,42) | `country_id = 'ESP'` |
| `atlantico` (lon -30 lat 35) | fila en `current_event`, `country_id` nulo, 0 filas en cuarentena |
| `mag-nula` (en Madrid) | `mag` nulo (no 0) y `country_id = 'ESP'` |
| `lat-145` | 1 fila en cuarentena `coordinates_out_of_range`, 0 en `current_event` |

Después `docker compose restart consumer` debe registrar `catalog loaded total=177 inserted=0 updated=0` y `public.country` sigue con 177.

## 4. Recuentos con y sin país

```sql
SELECT count(*) AS total, count(country_id) AS con_pais, count(*) - count(country_id) AS sin_pais
FROM live.current_event;
```

`con_pais + sin_pais = total`.

## 5. Muestra real de un día (SC-007)

```bash
uv run python scripts/geo_real_day.py docs/evidencias/geografia-pais/feed_all_day.geojson
```

Escribe cuántos eventos tienen país, cuántos no y confirma que todo código asignado está en el catálogo.

## 6. Contratos intactos (SC-009)

```bash
git diff --stat -- specs/001-contratos-y-modelo/contracts sql/001_schema.sql docs/enunciado
```

Esperado: vacío.
