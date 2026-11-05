# Guía de comprobación: Histórico 2025

Pasos para comprobar la feature una vez implementada (T001–T025). Los nombres de módulo son los del plan §4. Comandos en Git Bash (en Windows, `MSYS_NO_PATHCONV=1` evita que Git Bash reescriba la ruta del volumen); los de Docker y `uv` son iguales en PowerShell.

## 1. Unitarias (sin Docker ni red)

```bash
uv run pytest -m "not integration" -q
uv run pytest tests/historical -q
```

Esperado: todo en verde; incluye mes simulado de >20000 eventos sin pérdida, dedup con un `id` repetido entre dos archivos, reutilización por sha256 sin petición, y error con código distinto de 0 si el recuento no cuadra.

## 2. Integración con PostgreSQL real (fixtures sintéticos)

```bash
docker compose up -d postgres
docker compose --profile test build tests
docker compose --profile test run --rm tests pytest -m integration -q -k historical
```

Esperado: `current_event` = únicos − cuarentena; recarga x3 sin diferencias; `source=usgs_historical`, `mode=live`, `kafka_*` nulos; `mag` nula conservada; `lat 145` en cuarentena; Atlántico con `country_id` nulo.

## 3. Descarga real de 2025 (una vez; necesita red)

```bash
uv run python -m historical.download_main
```

Esperado: 12 archivos `data/historical/usgs_2025-MM.geojson` y `manifest.json`; el log muestra registros por consulta, duplicados descartados, total único y `count` de USGS iguales. Segunda ejecución: no hace peticiones. `--force` vuelve a descargar.

## 4. Carga en la base del stack

```bash
docker compose build producer   # la imagen es compartida; `build consumer` no hace nada
docker compose up -d postgres
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v ./data/historical:/app/data/historical:ro consumer python -m historical.load_main
```

Esperado: línea `historical_summary ... ok=true`; la consulta de verificación (data-model §6) da `|U| − |Q|` eventos. Repetir el comando: `new=0 newer=0` y huella idéntica. `docker compose restart postgres` y volver a consultar: mismo recuento.

## 5. Hueco de más de 24 h (B12)

```bash
uv run python -m historical.download_main --start 2025-12-30T00:00:00 --end 2025-12-31T00:00:00
MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v ./data/historical:/app/data/historical:ro consumer python -m historical.load_main
```

Esperado: `usgs_gap_20251230T000000_20251231T000000.geojson` en el manifiesto; la carga no duplica ni retrocede eventos ya presentes.

## 6. Contratos intactos

```bash
git diff --stat -- specs/001-contratos-y-modelo/contracts sql/001_schema.sql docs/enunciado
```

Esperado: vacío.
