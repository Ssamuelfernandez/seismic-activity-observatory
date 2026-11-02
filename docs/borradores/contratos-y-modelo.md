# Borrador — contratos-y-modelo

Resumen de lo que entrega la feature `contratos-y-modelo`, para reutilizarlo en la memoria. No sustituye a los contratos: los enlaza.

## Qué se entrega

| Entregable | Dónde |
|---|---|
| Contrato del mensaje Kafka (topics, clave, campos, versiones, motivos de cuarentena) | `specs/001-contratos-y-modelo/contracts/kafka-message.md` |
| Contrato de la base de datos (grano, claves, relaciones, índices por consulta) | `specs/001-contratos-y-modelo/contracts/db-schema.md` |
| Contrato de la API (parte del contrato mínimo del profesor) | `specs/001-contratos-y-modelo/contracts/api.md` |
| DDL | `sql/001_schema.sql` |
| Modelos conceptual, lógico y físico | `specs/001-contratos-y-modelo/data-model.md` y `docs/memoria.md` §5 |
| Pruebas del esquema, validación de los JSON y revisión de la API | `docs/evidencias/contratos-y-modelo/` |
| Informes de revisión | `docs/evidencias/subagentes/` |

## Decisiones principales

- Solo una versión con `updated` estrictamente mayor sustituye al estado actual; toda versión con un `updated` no visto se conserva.
- Cada instante se guarda como `timestamptz` UTC y como milisegundos originales.
- Nulos y negativos no se sustituyen por 0; país sin polígono = «Sin país asignado».
- `live` y `replay` son esquemas separados con las mismas tablas; `ingest` es compartido.
- Un mensaje inválido genera una sola fila de cuarentena, con el primer motivo según un orden de prevalencia fijo.
- La API pagina por cursor, con un máximo de 5 000 eventos por respuesta.

## Pruebas realizadas

- DDL aplicado dos veces en PostgreSQL 16 sin errores; `live` y `replay` idénticos; 18 pruebas de restricciones y versiones (salidas en `docs/evidencias/contratos-y-modelo/`).
- Bloques JSON de los contratos parseados correctamente.
- `api.md` revisada contra `CONTRATO-API.md` sin contradicciones.

## Pendiente

- Comprobar el esquema en la ejecución real de `consumidor-idempotente`: SIN EVIDENCIA todavía.
