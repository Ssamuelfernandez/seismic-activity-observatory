# seismic-activity-observatory

Observatorio de actividad sísmica: un sistema que consulta el feed de terremotos de USGS, lo publica en Kafka, lo guarda en PostgreSQL sin duplicados ni pérdida de versiones y lo expone mediante una API a un panel con mapa. También permite reproducir un histórico, aislado de los datos en vivo. Proyecto de curso.

## Estado actual

Se trabaja con Spec Kit, una feature cada vez y con revisión antes de avanzar.

| Feature | Estado |
|---|---|
| `contratos-y-modelo` | Cerrada (2026-11-02): contratos, DDL, modelo de datos y evidencias |
| Resto de features | No empezadas |

El orden de las fases está en [`docs/planificacion/02-roadmap-implementacion.md`](docs/planificacion/02-roadmap-implementacion.md).

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| [`docs/planificacion/`](docs/planificacion/) | Checklist de requisitos ([01](docs/planificacion/01-checklist-requisitos.md)), roadmap ([02](docs/planificacion/02-roadmap-implementacion.md)), procedimiento de ejecución ([03](docs/planificacion/03-procedimiento-ejecucion.md)), glosario ([04](docs/planificacion/04-glosario-nomenclatura.md)) y [decisiones abiertas del contrato](docs/planificacion/decisiones-abiertas-contrato.md) |
| `docs/enunciado/` | Material del profesor (solo lectura) |
| `docs/evidencias/` | Salidas de pruebas y de revisiones |
| `docs/memoria.md` | Memoria del proyecto (en redacción) |
| `specs/001-contratos-y-modelo/` | Spec, plan, tareas y los tres contratos (`contracts/`) |
| `sql/001_schema.sql` | Esquema de base de datos |
| `data/catalogo/` | Catálogo de países (`paises.geojson`) |
| `scripts/` | Script de exploración del feed |
| `CODEMAP.md` | Mapa de dónde está cada cosa |
| `.specify/` | Configuración y plantillas de Spec Kit |

## Contratos y esquema

Los contratos viven solo en `specs/001-contratos-y-modelo/contracts/`:

- [`kafka-message.md`](specs/001-contratos-y-modelo/contracts/kafka-message.md): mensaje productor → consumidor, versiones y cuarentena.
- [`db-schema.md`](specs/001-contratos-y-modelo/contracts/db-schema.md): tablas, claves e índices.
- [`api.md`](specs/001-contratos-y-modelo/contracts/api.md): API → panel.

El DDL es [`sql/001_schema.sql`](sql/001_schema.sql). Para repetir la validación, sigue [`quickstart.md`](specs/001-contratos-y-modelo/quickstart.md) (requiere Docker).

## Herramientas

- Spec Kit CLI (`specify`): versión 1.2.4, obtenida con `specify --version`.
- Python 3.12 es la versión fijada para el proyecto. Las demás versiones se fijarán en la feature `infra-compose`.

## Ejecución

Se completará en la feature `infra-compose`.
