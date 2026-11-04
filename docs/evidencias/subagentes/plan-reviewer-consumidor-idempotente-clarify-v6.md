**Veredicto: Listo para tu revisión.** No encuentro bloqueantes ni importantes. Los tres hallazgos de v5 están resueltos, no se cambia ningún contrato y los contadores siguen cuadrando. Solo quedan observaciones menores.

Alcance de la revisión: solo existen `spec.md`, `checklists/requirements.md` y `bitacora.md`; no reclamo `plan.md` ni `tasks.md`. He leído la constitución, `kafka-message.md` §3–§6, `sql/001_schema.sql`, `spec.md` y el informe v5 completos. De `db-schema.md` solo he leído por búsqueda las líneas de `quarantine` (§3.5). No he releído `CLAUDE.md`, `03-procedimiento` §4/§4.2, el roadmap F3, el checklist C1–C8/C13 ni `specs/002-infra-compose`, y no he abierto `bitacora.md` ni `checklists/requirements.md`. Para las comprobaciones de rango y mapeo me he apoyado en el informe v5 y en la spec.

## 1. Resolución de los hallazgos de v5

| v5 | Estado | Dónde |
|---|---|---|
| 1 (bloqueante) NaN, Infinity y enteros enormes en cuarentena | Resuelto | FR-011 («Regla general») y FR-014 punto 2. Se detectan antes del `INSERT`, incluido `1e999999`. La cuarentena guarda `original` a `NULL`, `raw_text` saneado y el hash de los bytes recibidos. US3.11 lo cubre. |
| 2 (importante) Tipo de todas las columnas | Resuelto | FR-014 punto 1 enumera las cadenas y los numéricos, exige `bool` por tipo exacto y `is_synthetic` exacto, y asigna un motivo del contrato a cada caso. |
| 3 (importante) `event_id` largo | Resuelto | FR-014 punto 3 fija 512 caracteres, con `value_out_of_range` en el mensaje y `event_id` a `NULL` en cuarentena. US3.12 comprueba el borde de 512. |

Aritmética del índice: 512 caracteres × 4 bytes = 2048 bytes. Cabe en la PK `(event_id, updated_ms)`, en `ix_current_event_time` y en `ix_quarantine_event_id`.

## 2. Coherencia con el contrato

- **Contratos:** el diff de `contracts/` y `docs/enunciado/` está vacío, según el orquestador. Todos los motivos usados existen entre los 14 de `kafka-message.md` §6. FR-035 prohíbe tocar `kafka-message.md`, `db-schema.md` y `api.md`.
- **`mag` NaN:** va a `mag_out_of_range`, que el contrato define así («incluye `NaN` e infinitos»). Se guarda con `original` `NULL`, `raw_text` informado y hash. Cumple `quarantine_has_original`, `^[0-9a-f]{64}$` y `UNIQUE(original_sha256, reason)`. Funciona.
- **Prevalencia:** cada mapeo cae en el orden de §6.
  - `event.id` no cadena → `invalid_field_type`, que va después de los rangos. Un `id` numérico con latitud 145 da `coordinates_out_of_range`, coherente.
  - `time` o `updated` booleanos → `missing_time` / `missing_updated`. Es una lectura razonable de «no entero».
  - `source`, `mode`, `ingested_at`, `replay_at` e `is_synthetic` con fallo → `invalid_envelope`.
  - Válido por contrato pero no almacenable como `jsonb` → `db_constraint_violation`, el último de la lista.
- **Cobertura de columnas:**
  - `quarantine`: el informe v5 §1 la cubre completa (`id` identity, `event_id`, `reason`, `original`, `raw_text`, hash, `source` con CHECK, referencia Kafka, `received_at`, `is_synthetic`). Con las comprobaciones nuevas se cierran los huecos `original` y `event_id`.
  - `current_event` y `event_version`: FR-014 punto 1 cubre las columnas que vienen del mensaje. El resto sale del consumidor (`received_at`, `kafka_*`, `date_id`, `country_id` `NULL`). Los CHECK de rango y de coherencia ms/UTC los garantizan la validación y la conversión.
  - `date_dim`: `year` es `smallint`. FR-014 punto 2 lo cubre con un rango que es un subconjunto de `timestamptz`.

## 3. Contadores (FR-023 / FR-036)

Siguen cuadrando con los mapeos nuevos.
- FAQ 12: 5 − 0 = 5, y 2+1+0+2+0+0 = 5.
- Con un inválido repetido: 7 − (1+1) = 5.
- Con un `db_constraint_violation` repetido: 7 − 0 = 7, y 2+1+0+2+0+(1+1) = 7.

## 4. Hallazgos

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| La justificación de FR-023 para contar la conversión en `db_constraint_violation` está desfasada: dice «se transforman antes de fallar en la base». Ahora el caso «válido por contrato pero no almacenable» se decide sin tocar la BD, y FR-001 pone validar antes de transformar. La cifra es correcta (ese mensaje ya tiene `time` y `updated` válidos). Falta decir que la conversión se calcula antes de decidir ese motivo, o reformular la razón. | Menor | spec.md FR-023 frente a FR-001 y FR-014 punto 2 | FR-023, FR-036 |
| Contar «enteros de más de 4300 dígitos» como `invalid_json` estira el motivo: es JSON válido, y es el límite de Python, no del formato. Está abierto en la pregunta 1(b), así que es decisión del alumno. | Menor | FR-014 punto 2; Preguntas 1(b) | `kafka-message.md` §6 |
| `1e400` da `inf` en Python pero PostgreSQL lo acepta como `numeric`. La regla «NaN o infinito tras deserializar» rechazaría un original que `jsonb` sí guardaría. Es un caso exótico, y si hay que ajustarlo es decisión del plan. | Menor | FR-014 punto 2 | FR-011, FR-013 |
| US3.9 y los Edge Cases citan solo NUL y bytes no UTF-8; NaN e infinitos aparecen en US3.11 y FR-014 punto 2. Es coherente, pero el texto repartido invita a omitir casos en tareas. | Menor | US3.9, Edge Cases | — |
| El párrafo de `Q: db_constraint_violation` en Clarifications no menciona la vía previa al `INSERT` que añade FR-014. | Menor | Clarifications, 2.º punto | — |
| En «Preguntas para el alumno» falta una línea en blanco antes de «Pendientes» y la numeración mezcla viñetas con 1–4. | Menor | Preguntas para el alumno | — |
| FR-036 sigue fuera de secuencia, con nota explícita. Aceptable. | Menor | FR-036 | — |

Los hallazgos segundo y tercero (`invalid_json` por enteros largos y `1e400`) son decisiones o detalles de plan. Ninguno bloquea.

## 5. Decisiones que el alumno debe tomar (siguen pendientes, no bloqueantes)

1. Confirmar la regla general de FR-014 (tres comprobaciones previas) y sus motivos, incluidos:
   - `db_constraint_violation` para lo no almacenable como `jsonb`;
   - `invalid_json` para enteros de más de 4300 dígitos;
   - `value_out_of_range` para un `event.id` de más de 512 caracteres.
   La alternativa es ampliar el contrato con un motivo propio, y eso es decisión tuya.
2. Confirmar la regla de copia a cuarentena (`source`, `event_id`, `is_synthetic`).

**Veredicto: Listo para tu revisión.**
