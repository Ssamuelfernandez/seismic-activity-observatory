**Informe de revisión, paso SPECIFY, feature `consumidor-idempotente` (`specs/003-consumidor-idempotente/spec.md`)**

Solo existen `spec.md` y `checklists/requirements.md`. Hay además un `bitacora.md` en la carpeta que no estaba en la lista de artefactos. `git diff` de contratos y enunciado está vacío.

**Punto crítico: "3 versiones" de la FAQ 12**

No hay contradicción y no hace falta escalar.
- `docs/enunciado/FAQ-ALUMNADO.md` (FAQ 12, líneas 186-194) tiene una columna "Versiones distintas guardadas" que vale 1, 1, 2, 2 y 3 tras procesar E2. Su resultado final dice "tres versiones distintas observadas en total".
- Eso es lo que implementa la spec: E1×2 + E2×1, con clave (`event_id`, `updated_ms`) según `db-schema.md` §3.4 y §5.
- La lectura "3 solo para E1" no encaja con la clave del contrato ni con la FAQ.
- La Pregunta 1 del alumno y la frase condicional de SC-001 pueden cerrarse citando la FAQ 12. Como están escritas dejan abierta una duda que ya está resuelta.

**Hallazgos**

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| Pregunta 1 y SC-001 plantean un posible cambio de contrato que la FAQ 12 ya descarta. Conviene citar la FAQ y cerrarla. | menor | spec.md, "Preguntas para el alumno" 1 y SC-001 | FAQ 12, constitución §15 y §18 |
| La spec no fija el cálculo del hash de cuarentena y lo delega al plan. Es la clave de idempotencia (`original_sha256`, `reason`), así que debe quedar decidido. Propuesta: SHA-256 de los bytes del valor tal como llegó, sin re-serializar. Eso sirve igual para `invalid_json` y evita depender de la normalización de jsonb. | importante | Assumptions, penúltimo punto de la lista; FR-011 y FR-012 | C5, constitución §1 y §6, `db-schema.md` §3.5 |
| Los contadores de C8 solo viven en memoria y se reinician con el proceso. Es coherente con no ampliar el esquema (§12) y con la Pregunta 2. Pero "reconciliarlos con la base" (FR-023, SC-009) solo es exacto en una sesión limpia. La spec lo reconoce en Assumptions. Falta fijar en el plan que la verificación parte de una base y un grupo limpios. | menor | FR-023, SC-009, Assumptions | C8, constitución §8 |
| El contador "conversiones ms a UTC" no tiene definición. No se sabe si cuenta mensajes, campos o versiones nuevas. El ejemplo de US5.3 no lo incluye. Hay que definir la unidad para poder reconciliarlo. | menor | US5 escenario 2 y 3 | C8 |
| Los permisos de `observatory_consumer` bastan para el flujo. | informativo | `sql/002_roles.sql` líneas 59-64 | FR-027, `db-schema.md` §1.1 |
| El rol de cuarentena no tiene `SELECT`. Por tanto el plan no puede usar `RETURNING` ni `ON CONFLICT DO UPDATE` en `quarantine`. Debe usar `ON CONFLICT DO NOTHING` simple. Las pruebas que lean la cuarentena deben usar otro rol. Conviene anotarlo en el plan. | menor | FR-011, FR-012, FR-027 | C5 |
| Nada en la spec fija que `db_constraint_violation` incluya el error de la FK diferida de `event_version`, que salta en el `COMMIT` y no en el `INSERT`. Es un detalle de plan, pero hay que tenerlo en cuenta al diseñar el rollback. | menor | FR-014, US3.6 | `kafka-message.md` §6 |
| La prueba 8 exige "forzar un corte entre commit PG y commit del offset". La spec lo pide pero no indica el mecanismo (hook de prueba o similar). Es decisión del plan. No es bloqueante. | menor | US2.1, SC-005 | Prueba 8, C2 |
| La numeración 003/004 queda explicada en la spec y en el glosario. Cuando se cree `productor-live` habrá que actualizar `03-procedimiento-ejecucion.md` §4, que hoy usa `004-consumidor-idempotente`. | menor | Nota de numeración | Constitución §19 (trazabilidad) |
| La FAQ 12 incluye E2 (10:12, mag 3.1) y la spec no fija esos datos. Conviene incluirlos en el escenario 5 para que la prueba pueda comprobar "E2 mag 3.1". | menor | US1.5, SC-001 | FAQ 12 |

**Cobertura (sin hallazgos)**
- **C1:** FR-001, FR-003, FR-004.
- **C2:** FR-001, FR-002, US2.4.
- **C3:** FR-005, FR-006, SC-002.
- **C4:** FR-005, FR-007, FR-009, FR-010, SC-003.
- **C5:** FR-011 a FR-015.
- **C6:** FR-016, FR-017.
- **C7:** FR-018, FR-019.
- **C8:** FR-023, FR-024.
- **C13:** FR-022, SC-008.
- **Pruebas:** la 2 (SC-002), la 3 y la 4 (SC-003, FR-031), la 6 (SC-004) y la 8 (SC-005, SC-006) están cubiertas.
- **Prueba 4:** la secuencia de la FAQ 12 no contiene una antigua tardía no vista. La spec lo detecta y añade un caso aparte en FR-031.
- **Contadores de la FAQ 12:** los de US5.3 (5 recibidos, 2 nuevos, 1 más reciente, 2 reenvíos, 0 antiguas tardías) son correctos.
- **Contrato Kafka:** el orden de prevalencia (14 motivos) y la regla "una fila por mensaje" coinciden con `kafka-message.md` §6. La regla `mode_topic_mismatch` va a la cuarentena del esquema del tema. Los casos de versiones coinciden con §5.
- **Contrato de BD:** FR-005, FR-009 y FR-019 coinciden con `db-schema.md` §5 y §8.

**Constitución y alcance**
- **Constitución:** cumple §1, §2, §3, §4 (`country_id` queda NULL, FR-021), §5, §6, §7, §8 (FR-024), §12, §14 (FR-030, FR-033), §15 (FR-035 impide tocar contratos), §16 y §19. En §13 no hay infracción detectada.
- **Alcance:** nada fuera de alcance. País por polígono, productor real, USGS, histórico, replay (solo `mode_topic_mismatch`), API y frontend quedan excluidos explícitamente.
- **Carga del catálogo:** FR-025 queda dentro de alcance. `db-schema.md` §1.1 asigna esa escritura al consumidor, y el roadmap F3 la incluye. La frase de §3.1 "no es parte de esta feature" se refiere a `contratos-y-modelo`, no a esta.

**Decisiones que el alumno debe tomar**
1. Confirmar la lectura de "3 versiones" como total (la FAQ 12 la respalda) y cerrar la Pregunta 1.
2. Aprobar el hash de cuarentena como SHA-256 de los bytes recibidos.
3. Confirmar que los contadores de C8 queden solo en memoria y registro (Pregunta 2).
4. Confirmar que solo se consume `earthquakes.live` (Pregunta 3).

**Veredicto:** Listo para tu revisión (sin hallazgos bloqueantes; conviene fijar el hash de cuarentena antes del plan).
