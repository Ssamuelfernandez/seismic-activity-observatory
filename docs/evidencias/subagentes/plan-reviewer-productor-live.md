**Revisión de la feature productor-live (specs/004-productor-live/)**

No encuentro hallazgos bloqueantes ni importantes. Contratos, `sql/001_schema.sql` y `docs/enunciado/` quedan intactos.

**Cobertura:** B1–B12, A10 y las pruebas 1 y 2 tienen tarea y prueba.
- La tabla de trazabilidad de `tasks.md` cubre todos los IDs.
- B9 y la prueba 2 se prueban en T010 y T013 (corte entre ack y marca, con recuentos de `current_event` y `event_version`).
- B10 se prueba en T007 y T012 (500, 429, timeout y JSON inválido).
- B2, B11 y B12 están en T015.
- La prueba 1 llega hasta PostgreSQL con USGS real (T018 y T020), y T020 prevé el caso de que no aparezca ningún evento nuevo.

**Constitución:** sin violaciones.
- §1/§2 (idempotencia): el estado se marca solo tras el ack.
- §7 (sintéticos separados): el mock lleva `synthetic-…` y no usa base real.
- §11 (versiones fijadas): no hay dependencias nuevas.
- §13 (idioma): CC-DOC lo recoge.
- §14 (lógica pura separada de E/S): la lógica pura está en `common/`.
- §16 (cierre): T017–T022.
- §19: T022 se detiene a esperar revisión.

**Pregunta sobre `db-schema.md` §1.1 y `GRANT SELECT, DELETE`: no contradice el contrato.**
- §3.9 delega la retención en esta feature y la consulta Q9 del contrato ya es una purga.
- El productor ya lee `ingest_run` e `ingest_state`.
- El comentario de `sql/002_roles.sql` (líneas 43-44) anticipa este caso: "leer raw_response o purgarla".
- Lo único que queda es que la tabla de §1.1 diría "Lee: consultas de evidencia" sin mencionar al productor. Es una sincronización de redacción, no un conflicto de diseño.
- `plan.md` §5 y `research.md` §5 lo llaman "Discrepancia", y ese término exagera. Basta con que el alumno decida si quiere esa línea en §1.1; no bloquea nada.

**Decisiones del alumno antes de implementar:**
1. ¿Edita §1.1 de `db-schema.md` para añadir lectura y purga del productor sobre `raw_response`, o deja el contrato como está? Esto es una pregunta, no una propuesta de cambio.
2. T021 aplaza `CODEMAP.md` al final de la feature. `CLAUDE.md` lo pide al terminar cada tarea que cree archivos. `tasks.md` (CC-MAP) lo declara como desviación y pide confirmación; hay que confirmarla.
3. Las preguntas 1, 3 y 4 de `plan.md` §5 (retirar los sintéticos y adaptar el check A1, retención de 7 días con hash sobre `features`, y no insertar fila en `ingest_run` si falla Kafka) tienen decisión provisional razonable y se pueden confirmar al revisar.

**Límite conocido:** `urllib` aplica el timeout por operación de socket, no al total de la respuesta. Un servidor que envíe el cuerpo a goteo podría alargar un ciclo. Es irrelevante en la práctica con USGS.

**Veredicto:** Listo para tu revisión.
