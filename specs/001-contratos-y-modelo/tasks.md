---

description: "Lista de tareas de la feature contratos-y-modelo"
---

# Tasks: Contratos y modelo de datos

**Input**: Documentos de diseño en `specs/001-contratos-y-modelo/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`).

**Prerequisites**: `plan.md` y `spec.md` (ambos presentes y con las aclaraciones de las sesiones 2026-11-01 y 2026-11-02).

**Tests**: esta feature no tiene código de aplicación. Las «pruebas» son las comprobaciones de `quickstart.md`; sus tareas están incluidas porque la spec las exige (E5, SC-005) y `CLAUDE.md` pide tests ejecutados y evidencia al cerrar.

**Estado**: las tareas marcadas `[x]` ya están hechas y verificadas (los entregables existen en el repositorio y las pruebas están en `docs/evidencias/contratos-y-modelo/`). Las tareas sin marcar son lo que falta para cerrar la feature.

## Format: `[ID] [P?] [Story] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias).
- **[Story]**: historia de usuario de `spec.md` (US1–US4).
- Identificadores en inglés; documentación y comentarios en español.

---

## Phase 1: Setup

**Purpose**: estructura y entradas de solo lectura.

- [x] T001 Crear `specs/001-contratos-y-modelo/contracts/` y `sql/` (esta feature solo añade `sql/001_schema.sql` fuera de `specs/`).
- [x] T002 Comprobar las entradas de solo lectura: `docs/enunciado/CONTRATO-API.md`, `docs/planificacion/decisiones-abiertas-contrato.md`, `docs/evidencias/f1/explore_usgs_salida.txt` y `data/catalogo/paises.geojson` (177 entidades, `ADM0_A3` único, sin nulos en `NAME_ES`, `ADMIN`, `CONTINENT`, `SUBREGION`; sin modificarlo). Resultado en `research.md` R10.

---

## Phase 2: Foundational (bloquea todas las historias)

**Purpose**: decisiones que los contratos necesitan.

- [x] T003 Registrar las decisiones técnicas en `specs/001-contratos-y-modelo/research.md` (R1–R13).
- [x] T004 Registrar las aclaraciones en `specs/001-contratos-y-modelo/spec.md`, sección Clarifications (sesiones 2026-11-01 y 2026-11-02).

**Checkpoint**: decisiones de la API, del mensaje y de los límites de cordura aprobadas.

---

## Phase 3: User Story 1 - Contrato del mensaje y reglas de versiones (Priority: P1) 🎯 MVP

**Goal**: definición única del mensaje productor → consumidor y de la regla de versiones (C4).

**Independent Test**: cada campo de `kafka-message.md` tiene nombre, tipo, obligatoriedad y valores permitidos, y los cinco casos de versiones se resuelven sin ambigüedad.

- [x] T005 [P] [US1] Escribir `specs/001-contratos-y-modelo/contracts/kafka-message.md`: topics `earthquakes.live` y `earthquakes.replay` (1 partición, factor de replicación 1, retención 7 días), clave `event.id` (nula si falta, con motivo `missing_id`), campos `source`, `mode`, `ingested_at`, `replay_at`, `is_synthetic`, `event`, y aislamiento del replay (J3).
- [x] T006 [US1] Documentar en `kafka-message.md` §5 las reglas de versiones (los cinco casos: evento nuevo, reenvío, versión más reciente, versión antigua tardía, mismo `updated` con contenido distinto) y en §6 los motivos de cuarentena con su orden de prevalencia (C4, C8).
- [x] T007 [US1] Incluir en `kafka-message.md` §4 un mensaje de ejemplo con el evento real `ci41570768` del feed.
- [x] T008 [US1] Ejecutar la comprobación de `quickstart.md` §1 (parsear todos los bloques JSON de `contracts/kafka-message.md` y `contracts/api.md`) y guardar la salida en `docs/evidencias/contratos-y-modelo/ejemplos_json_salida.txt`.

**Checkpoint**: US1 verificable por revisión y por T008.

---

## Phase 4: User Story 2 - Esquema de base de datos y modelo de datos (Priority: P1)

**Goal**: esquema completo con grano, claves, relaciones e índices justificados (E2, E4, E5, E7).

**Independent Test**: el DDL se aplica dos veces sin errores en PostgreSQL 16, `live` y `replay` son idénticos y las restricciones rechazan lo que deben.

- [x] T009 [P] [US2] Escribir `sql/001_schema.sql`: esquemas `public`, `live`, `replay`, `ingest`; 13 tablas y 11 índices; `timestamptz` más ms originales con `CHECK` de coherencia; `is_synthetic`; `status`, `url`, `sig` (FR-007b); `country` con `country_id` (`ADM0_A3`), `name_es` (`NAME_ES`), `admin` (`ADMIN`), `continent` (`CONTINENT`), `subregion` (`SUBREGION`).
- [x] T010 [P] [US2] Escribir `specs/001-contratos-y-modelo/contracts/db-schema.md`: grano, clave y relaciones de cada tabla, índices ligados a las consultas Q1–Q13, tabla «Quién escribe y quién lee» (§1.1), equivalencia con el enunciado (E3) y notas para features posteriores (§8).
- [x] T011 [US2] Aplicar `sql/001_schema.sql` dos veces en PostgreSQL 16, comprobar `live` ≡ `replay` (columnas y restricciones) y contar tablas e índices; salida en `docs/evidencias/contratos-y-modelo/prueba_esquema_001_ddl_salida.txt`.
- [x] T012 [US2] Probar restricciones, reglas de versiones, cuarentena, exclusión, aislamiento `live`/`replay`, ingesta y consultas Q1/Q4 con `docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql`; salida en `prueba_esquema_001_salida.txt`.
- [x] T013 [US2] P14 aprobada por el alumno el 2026-11-02 (unicidad de cuarentena `(original_sha256, reason)` y de exclusión `(event_id, updated_ms, kind)`): marca de pendiente retirada en `plan.md` y registrada en `spec.md` (Clarifications). El DDL no cambia (solo un comentario), así que T011 y T012 siguen vigentes.

**Checkpoint**: US2 verificado por T011 y T012; T013 hecha (el DDL solo ha cambiado en comentarios desde la evidencia, comprobado con `git diff`).

---

## Phase 5: User Story 3 - Contrato de la API con las decisiones propias (Priority: P2)

**Goal**: `api.md` parte del contrato del profesor y resuelve los seis puntos abiertos.

**Independent Test**: nada del contrato mínimo se contradice y los ejemplos coinciden con valores reales del feed.

- [x] T014 [P] [US3] Escribir `specs/001-contratos-y-modelo/contracts/api.md`: `/api/eventos` (parámetros, `metadata`, orden y cursor, once campos de `properties`), `/api/salud`, `/api/estadisticas`, errores y tabla de conformidad con `CONTRATO-API.md`; todas las decisiones en estado DECIDIDO.
- [x] T015 [US3] Validar los ejemplos de `api.md` contra `docs/evidencias/f1/explore_usgs_salida.txt` y el feed guardado (sumas de `by_hour`, `by_country` e histogramas = `total`; `n_2025` marcado como ilustrativo); tabla en `api.md` §8.
- [x] T016 [US3] Revisar a mano la tabla de conformidad de `api.md` §7 línea a línea contra `docs/enunciado/CONTRATO-API.md` (SC-005) y guardar el resultado en `docs/evidencias/contratos-y-modelo/revision_api_vs_contrato.md`.

**Checkpoint**: US3 verificable por T016.

---

## Phase 6: User Story 4 - Borrador de modelos para la memoria (Priority: P3)

**Goal**: modelos conceptual, lógico y físico y equivalencia de nombres (E1, E3).

**Independent Test**: los tres niveles describen la misma base de datos y la tabla de equivalencias cubre las 5 tablas orientativas del enunciado.

- [x] T017 [P] [US4] Escribir `specs/001-contratos-y-modelo/data-model.md` con los tres niveles, la equivalencia de nombres (E3) y la trazabilidad.
- [x] T018 [US4] Reescribir el contenido de `specs/001-contratos-y-modelo/data-model.md` en `docs/memoria.md` §5 (modelo conceptual, lógico y físico, equivalencia de nombres y enlace a `sql/001_schema.sql`, E5), adaptado a la memoria y sin copiar `specs/` tal cual (constitución §18).

**Checkpoint**: US4 completo con T018.

---

## Phase 7: Polish y cierre de la feature

**Purpose**: cumplir constitución §16 y `CLAUDE.md` (tests ejecutados, evidencia, `CODEMAP.md` y `README.md`).

- [x] T019 [P] Añadir a `specs/001-contratos-y-modelo/spec.md` la sección «Criterios de aceptación» con los IDs E1–E5, E7 y C4 y la evidencia de cada uno.
- [x] T020 [P] Actualizar `specs/001-contratos-y-modelo/checklists/requirements.md`: notas obsoletas corregidas (tipos de evento y decisiones de `api.md` ya resueltos).
- [x] T021 [P] Actualizar `CODEMAP.md`: filas en «Dónde está cada cosa» para `specs/001-contratos-y-modelo/contracts/` (mensaje Kafka, esquema de base de datos y API), `sql/001_schema.sql` (esquema de base de datos), `specs/001-contratos-y-modelo/data-model.md` (modelos conceptual, lógico y físico) y `docs/evidencias/contratos-y-modelo/` (pruebas del esquema en PostgreSQL 16), con sus requisitos (E1–E5, E7, C4).
- [x] T022 [P] Actualizar `README.md` (hoy solo tiene el título) con una sección que indique dónde están los contratos y el DDL y cómo repetir la validación de `quickstart.md`.
- [x] T023 Aplicar las decisiones del alumno (P14, motivos de cuarentena con validación previa del consumidor, campos de estadísticas en inglés, `truncated`, normalización de `country_id`, `ingest.*` compartido) y las correcciones del informe `plan-reviewer` (`docs/evidencias/subagentes/plan-reviewer-001-contratos-y-modelo.md`) en spec, plan, research, data-model, quickstart, checklist de calidad, contratos y DDL.
- [x] T024 Ejecutar `/speckit-analyze` sobre spec, plan y tareas (después de T023) y corregir las incoherencias que señale.
- [x] T025 Volver a pasar el agente `plan-reviewer` tras T024 y resolver sus hallazgos bloqueantes; informe en `docs/evidencias/subagentes/plan-reviewer-001-contratos-y-modelo-final.md`.
- [x] T026 Al cerrar la feature, añadir su fila a «Historial de features cerradas» de `CODEMAP.md`, detenerse y esperar la revisión del alumno. No hacer commits ni merges sin su aprobación (constitución §19).

---

## Dependencies & Execution Order

- **Setup (Phase 1)** y **Foundational (Phase 2)**: hechas.
- **US1 y US2 (P1)**: independientes entre sí; T008 depende de T005–T007 y de T014; T013 (hecha) dependía de T010.
- **US3 (P2)**: T016 depende de T014.
- **US4 (P3)**: T018 depende de T010 y T017.
- **Polish**: T019–T026 hechas, en este orden: T021 y T022 en paralelo tras T009–T010; T023; T024 (`/speckit-analyze`) después de T023; T025 (`plan-reviewer`) después de T024; T026 al final. La revisión del alumno y cualquier commit quedan a su criterio (constitución §19).

### Parallel Opportunities

```text
T008, T016, T018                # historias, archivos distintos (hechas)
T021, T022                      # cierre, archivos distintos (hechas)
```

## Implementation Strategy

- **MVP**: US1 + US2 (las dos P1). Escritas y verificadas (T008 incluida).
- **Cierre**: todas las tareas (T001–T026) están hechas; queda la revisión del alumno.
- Tras cada tarea que cambie el DDL o un contrato, repetir T011 y T012 y revisar la coherencia entre `db-schema.md`, `sql/001_schema.sql` y `spec.md`.

## Notes

- Un contrato solo vive en `specs/001-contratos-y-modelo/contracts/`; no se duplica en otras features.
- `docs/enunciado/` no se modifica.
- Sin commits ni merges sin aprobación del alumno.
