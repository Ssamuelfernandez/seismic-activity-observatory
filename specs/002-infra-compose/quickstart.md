# Quickstart: levantar, verificar y reiniciar

Guía de ejecución y validación de `infra-compose`. Los detalles de diseño están en [plan.md](plan.md) y [research.md](research.md); las variables, en [contracts/config.md](contracts/config.md).

## Requisitos

- Docker con Compose v2 (probado con Docker 29.1.5 y Compose v5.0.1).
- Puerto `8000` libre en el equipo.
- Para la verificación: Python 3 en el equipo (solo biblioteca estándar). Para las pruebas unitarias: `uv`.

## 1. Levantar

```bash
cp .env.example .env          # en PowerShell: Copy-Item .env.example .env
# Edita .env y cambia las contraseñas de ejemplo (no lo subas a Git).
docker compose up --build -d
docker compose ps
```

Esperado: `kafka`, `postgres`, `producer`, `consumer` y `api` en `healthy` (la primera vez, el tiempo incluye la descarga de imágenes; con ellas descargadas, unos 15–60 s). Sin `.env` o con una variable ausente, `docker compose` falla nombrando la variable.

## 2. Comprobaciones a mano

| Qué | Comando | Esperado |
|---|---|---|
| Evento sintético en el consumidor | `docker compose logs consumer --no-log-prefix --tail 5` | Líneas `decision=… event_id=synthetic-…` (una por mensaje) |
| API | `curl http://127.0.0.1:8000/api/salud` | `{"status":"ok","last_ingestion":null,"generated":…}` |
| Solo la API publica puertos | `docker compose ps` | Solo `127.0.0.1:8000->8000/tcp`, en `api` |
| Temas y retención | `docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic earthquakes.live` | `PartitionCount: 1`, `ReplicationFactor: 1`, `retention.ms=604800000` |

Los eventos llegan al arrancar y después cada `PRODUCER_INTERVAL_SECONDS` (30 s por defecto).

## 3. Verificación automática de punta a punta

```bash
python scripts/verify_stack.py                # incluye detener y volver a arrancar los contenedores
python scripts/verify_stack.py --skip-restart # sin detener nada
python scripts/check_env_example.py           # .env.example ↔ compose.yaml ↔ código
uv run pytest                                 # pruebas unitarias (sin Docker)
```

`verify_stack.py` comprueba: cinco servicios sanos; evento sintético en el log del consumidor; `GET /api/salud`; un único puerto publicado y sin enlaces para Kafka y PostgreSQL; temas con 1 partición, factor 1 y 7 días; permisos de escritura por rol según el contrato; escritura de la API rechazada; y persistencia (crea `public.zz_infra_check`, ejecuta `down` y `up -d`, lee el dato y elimina la tabla). Termina con código 0 solo si todo pasa. La salida de referencia está en `docs/evidencias/infra-compose/verificacion_completa.txt`.

Nota: si el equipo ya tiene un PostgreSQL local en el 5432, la sonda TCP puede responder; el script lo avisa con `INFO` y no es un fallo (la comprobación se basa en que Docker no enlaza ningún puerto de Kafka ni de PostgreSQL).

## 4. Probar los reintentos

```bash
docker compose stop kafka
docker compose restart producer consumer
docker compose logs producer --no-log-prefix --tail 10   # líneas «Reintento N: no se pudo conectar con Kafka…»
docker compose ps                                        # producer y consumer en «health: starting», no «healthy»
docker compose start kafka                               # al volver Kafka, los cinco vuelven a «healthy»
```

## 5. Reiniciar

| Quiero… | Comando | Efecto sobre los datos |
|---|---|---|
| Parar y volver a arrancar | `docker compose down` y `docker compose up -d` | Se conservan (volúmenes) |
| Reiniciar un servicio | `docker compose restart <servicio>` | Se conservan |
| Reconstruir tras cambiar código | `docker compose up --build -d` | Se conservan |
| **Empezar de cero** | `docker compose down -v` | **Borra** PostgreSQL y Kafka; el siguiente `up` recrea esquema y roles |

El esquema y los roles se aplican **solo cuando el volumen de PostgreSQL está vacío** (primera inicialización). **Cambiar las contraseñas de la base de datos (o `sql/002_roles.sql`) sobre un volumen ya inicializado no tiene efecto: hay que ejecutar `docker compose down -v`** (borra los datos) y volver a levantar. Si solo cambias el `.env`, los servicios Python usarán la contraseña nueva y no podrán conectar.

## 6. Ver la base (opcional)

```bash
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt live.*"'
```

PostgreSQL no se publica en el equipo: se entra por el contenedor.

## 7. Parar

```bash
docker compose down
```

## Documentación automática de la API

La API **no sirve** `/docs` ni `/redoc` (`docs_url` y `redoc_url` desactivados): es una decisión de esta feature para no ampliar la superficie expuesta. El contrato de la API está en `specs/001-contratos-y-modelo/contracts/api.md`.

## ngrok (fuera de esta feature)

Se ejecuta en el equipo con `ngrok http 8000`; el authtoken nunca va al repositorio.

## Resolución de problemas

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `required variable … is missing a value` | Falta una variable en `.env` | Copia de nuevo `.env.example` o añade la variable que nombra el error |
| `Bind for 127.0.0.1:8000 failed: port is already allocated` | Otro programa usa el 8000 | Libera el puerto y repite `docker compose up -d` |
| `api` queda en `starting` | PostgreSQL aún no está listo o la contraseña de `.env` no coincide con la del volumen | `docker compose logs api`; si cambiaste contraseñas tras la primera inicialización, `docker compose down -v` |
| `producer` o `consumer` en `unhealthy` | El broker o la base llevan más de 60–120 s sin responder | `docker compose logs <servicio>` y busca «Reintento»; revisa `kafka` y `postgres` |
| Cambios en `.sh` o `.sql` no surten efecto | La inicialización solo corre con el volumen vacío | `docker compose down -v` |
