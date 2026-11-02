# Implementation Plan: Contratos y modelo de datos

**Branch**: `001-contratos-y-modelo` | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-contratos-y-modelo/spec.md`

## Summary

Esta feature es **documental**: fija los tres contratos del sistema (mensaje Kafka, esquema de base de datos y API) y el modelo de datos, para que las demás features los referencien sin redefinirlos. No implementa código de aplicación. Los entregables son archivos concretos:

| Entregable | Archivo |
|---|---|
| Contrato del mensaje Kafka | [contracts/kafka-message.md](contracts/kafka-message.md) |
| Contrato del esquema de BD | [contracts/db-schema.md](contracts/db-schema.md) |
| Contrato de la API | [contracts/api.md](contracts/api.md) |
| DDL ejecutable (esquemas `public`, `live`, `replay`, `ingest`) | [sql/001_schema.sql](../../sql/001_schema.sql) |
| Borrador de modelos conceptual, lógico y físico y equivalencia de nombres | [data-model.md](data-model.md) |
| Decisiones técnicas | [research.md](research.md) |
| Guía de validación | [quickstart.md](quickstart.md) |

Enfoque técnico: se parte de las propuestas del roadmap §1, se respetan todas las decisiones de la sección Clarifications de la spec, y lo que la spec dejaba abierto se resolvió con propuestas concretas que el alumno aprobó (ver la lista al final de este documento).

## Technical Context

**Language/Version**: Python 3.12 (fijada aquí; ver `research.md` R1). Se concreta en `.python-version`, lock e imagen Docker en `infra-compose`.

**Primary Dependencies**: aiokafka (productor y consumidor), FastAPI (API), PostgreSQL 16, Apache Kafka en modo KRaft, Docker Compose. Versiones exactas: se fijan en `infra-compose` y en cada feature que las use (constitución §11). Frontend fuera de esta feature: no se fijan librerías de mapas ni de gráficos (se deciden en `panel-base-mock`).

**Storage**: PostgreSQL 16; esquemas `public`, `live`, `replay`, `ingest`.

**Testing**: esta feature no ejecuta código de aplicación. Validación mediante `quickstart.md` (JSON válido, DDL aplicable e idempotente, `live` ≡ `replay`). El DDL se aplicó dos veces sin errores en PostgreSQL 16 el 2-nov-2026 y se probaron sus restricciones, las reglas de versiones y el aislamiento (`docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql`). La comprobación en `consumidor-idempotente` (E5) se mantiene como prueba de integración.

**Target Platform**: contenedores Linux con Docker Compose (5 servicios: `producer`, `kafka`, `consumer`, `postgres`, `api`).

**Project Type**: sistema de datos con servicio web (pipeline USGS → Kafka → PostgreSQL → API → panel).

**Performance Goals**: no aplica a esta feature. Los índices son candidatos y se miden en `mediciones-costes`.

**Constraints**: constitución v1.0.0; `docs/enunciado/` de solo lectura; contratos solo en `specs/001-contratos-y-modelo/contracts/`; alcance cerrado.

**Scale/Scope**: feed de ~210 eventos/día (muestra) y histórico 2025 M ≥ 4 (miles de eventos). Límite de la API: 5 000 eventos por respuesta.

## Constitution Check

*GATE: pasa antes de la Fase 0 y se revalida tras el diseño de la Fase 1.*

| Principio | Cumplimiento |
|---|---|
| §1 Al menos una vez e idempotente | `ON CONFLICT` en versión y estado actual; únicas en cuarentena y exclusión; offset tras commit (`db-schema.md` §5, `kafka-message.md` §5) |
| §2 Versionado por `updated` | Solo gana `updated` estrictamente mayor; una fila actual por evento (PK) |
| §3 Tiempos de USGS | `timestamptz` + ms originales, con `CHECK` de coherencia |
| §4 País por geometría | `country_id` = `ADM0_A3`; nulo = «Sin país asignado»; `place` no se usa |
| §5 Nulos y negativos | Columnas nulables sin relleno; `CHECK` de rango que admite negativos y rechaza `NaN` |
| §6 Cuarentena | `quarantine` con motivo, original (`jsonb`/`raw_text`) y referencia Kafka; el consumidor valida los límites antes de insertar (motivos `mag_out_of_range`, `depth_out_of_range`, `invalid_field_type`, `value_out_of_range`, `replay_at_missing`); si aun así la base rechaza el `INSERT`, se aplica el motivo de último recurso `db_constraint_violation` (rollback, cuarentena y offset confirmado) |
| §7 Sintéticos separados | `is_synthetic` en mensaje y en las cuatro tablas; esquema `replay` aparte |
| §8 Agregaciones desde estado actual | `api.md` §5: todo calculado desde `current_event` |
| §9 Nombres de servicio | No aplica (sin Compose en esta feature) |
| §10 Exposición y secretos | Sin secretos en los entregables; solo la API se expone (`api.md` no incluye credenciales) |
| §11 Versiones fijadas | Aplazado a `infra-compose` (versiones exactas y lockfiles); solo Python 3.12 está fijado (justificado en `research.md` R2) |
| §12 Alcance cerrado | Sin Spark/Flink/Kubernetes/ML/informes de calidad/panel de calidad |
| §13 Idioma | Identificadores (tablas, columnas, topics, campos nuevos) en inglés; documentación en español. Excepciones del contrato: `country_id`, `country_name` y rutas `/api/...`; los campos propios de las estadísticas van en inglés (`n_recent`, `daily_mean_2025`, `variation_pct`, `no_value`; `n_2025` se mantiene) |
| §14 Una responsabilidad por función | No aplica (sin código) |
| §15 Contratos únicos | Los tres contratos solo viven en `contracts/`; `docs/enunciado/` no se toca |
| §16 Cierre de feature | Ver «Cierre» más abajo |
| §17 Frontend sin estadísticas | `api.md` §5 devuelve todas las cifras calculadas |
| §18 Enunciado de solo lectura | Sin cambios en `docs/enunciado/`; `data-model.md` no se copia a `docs/` tal cual |
| §19 Una feature cada vez | Se detiene tras el plan; sin commits |
| §20 Commits | Sin commits |
| §21 Sin predicción ni riesgo | Sin lenguaje de predicción en los contratos |

**Resultado:** sin violaciones. Complexity Tracking vacío. Revalidado tras la Fase 1: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/001-contratos-y-modelo/
├── plan.md              # Este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1: modelos conceptual, lógico y físico
├── quickstart.md        # Fase 1: guía de validación
├── contracts/
│   ├── kafka-message.md
│   ├── db-schema.md
│   └── api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

Esta feature solo añade un archivo fuera de `specs/`:

```text
sql/
└── 001_schema.sql       # DDL: esquemas public, live, replay, ingest
```

**Structure Decision:** se respeta la estructura de `CODEMAP.md` y `docs/planificacion/03-procedimiento-ejecucion.md` §3. El resto de carpetas (`common/`, `producer/`, `consumer/`, `api/`, `frontend/`, `scripts/`, `tests/`) nacen con sus features. `data/catalogo/paises.geojson` se lee, no se modifica.

## Cierre de la feature (tareas T018–T026 de `tasks.md`)

Constitución §16 y `CLAUDE.md`: al cerrar, tests ejecutados (aquí, `quickstart.md`), evidencia en `docs/evidencias/contratos-y-modelo/`, `CODEMAP.md` y `README.md` actualizados (fila de `sql/001_schema.sql` y de los contratos en «Dónde está cada cosa»), y tarea de reescribir `data-model.md` en `docs/memoria.md` §5.

## Complexity Tracking

Sin violaciones de la constitución: no se rellena.

## Decisiones aprobadas por el alumno

Valores concretos que el plan propuso para lo que la spec dejaba sin decidir. **Todas (P1–P14) fueron aprobadas por el alumno el 2026-11-02** y están registradas en `spec.md` (Clarifications, sesión 2026-11-02). P15–P19 son decisiones del alumno tras el informe del `plan-reviewer`.

| # | Propuesta | Dónde |
|---|---|---|
| P1 | Nombres: `limit`, `cursor`, `metadata.total`, `metadata.next_cursor`, `metadata.null_mag_excluded` | `api.md` §3 |
| P2 | Orden descendente (más reciente primero); cursor = base64url de `(event_time_ms, id)` | `api.md` §3.3 |
| P3 | `truncated = (count < total)`; `limit` mayor que el máximo → error 400 | `api.md` §3.2, §3.1 |
| P4 | `country_id` de un solo valor; `none` = «Sin país asignado»; rango por defecto si falta `start` o `end` | `api.md` §3.1 |
| P5 | `status`, `url`, `sig` y `place` nulables | `api.md` §3.4 |
| P6 | Lista de códigos de error (`invalid_parameter`, `invalid_cursor`, `not_found`, `method_not_allowed`, `database_unavailable`, `internal_error`) | `api.md` §6 |
| P7 | `/api/salud` no informa del modo | `api.md` §4 |
| P8 | Forma completa de `/api/estadisticas` (`period`, `filters`, `total`, `by_hour`, `by_country`, `unit`, `no_value`, `diff_abs`, `recent_incomplete`, `recent_period`, `reference_period`) | `api.md` §5 |
| P9 | País nulo en estadísticas: elemento propio con `country_id`, `country_name`, `subregion` a `null`; `no_value` informativo | `api.md` §5.1 |
| P10 | La comparación usa `max(min_mag, 4.0)` y lo declara (`min_mag_applied`); en `replay`, `comparison: null` | `api.md` §5.1 |
| P11 | `is_synthetic` obligatorio en el mensaje Kafka | `kafka-message.md` §3 |
| P12 | Lista inicial de motivos de cuarentena | `kafka-message.md` §6 |
| P13 | `CHECK` de rango de cordura en `mag`, `depth_km`, `lon`, `lat` | `db-schema.md` §2 |
| P14 | Unicidad de cuarentena `(original_sha256, reason)` y de exclusión `(event_id, updated_ms, kind)` | `db-schema.md` §3.5–3.6 |
| P15 | Motivos de cuarentena añadidos: `mag_out_of_range`, `depth_out_of_range`, `invalid_field_type`, `replay_at_missing`; el consumidor valida los límites antes de insertar | `kafka-message.md` §6, `db-schema.md` §2 |
| P16 | Campos propios de estadísticas en inglés: `n_recent`, `daily_mean_2025`, `variation_pct`, `no_value` | `api.md` §5 |
| P17 | `truncated = true` en cada página con `count < total`; el final lo marca `next_cursor` `null` | `api.md` §3.2 |
| P18 | `country_id` se normaliza a mayúsculas; se rechaza lo que no sean tres letras ni `none` | `api.md` §3.1 |
| P19 | `ingest.*` es compartido; el replay no usa estado de ingesta propio | `db-schema.md` §1 |
| P20 | Motivos `value_out_of_range` y `db_constraint_violation` (último recurso: rollback del mensaje, cuarentena y offset confirmado) | `kafka-message.md` §6, `db-schema.md` §2 |
| P21 | Un mensaje genera una sola fila de cuarentena, con el primer motivo según el orden de prevalencia | `kafka-message.md` §6 |
