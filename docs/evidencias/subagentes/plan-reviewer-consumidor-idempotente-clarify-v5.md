REVISIÓN CLARIFY v5 (vuelta 2 desde reanudación) – 003-consumidor-idempotente

Alcance: solo existen spec.md, checklists/requirements.md y bitacora.md; no he buscado plan.md ni tasks.md. He leído la constitución, CLAUDE.md, los contratos, sql/001_schema.sql, sql/002_roles.sql, 03 §4 y §4.2, el roadmap F3, el checklist C1–C8 y C13, y specs/002 (FR-008/009). Los contratos y docs/enunciado no tienen diff, según el orquestador. Ninguna regla de la spec exige cambiar un contrato. Las reglas de cuarentena de la constitución §6 son las que importan aquí.

## 1. Verificación campo a campo del INSERT en live.quarantine
La tabla replay.quarantine es idéntica, con los mismos CHECK y el mismo UNIQUE.

| Campo | Restricción en el DDL | Con las reglas de la spec |
|---|---|---|
| id | identity, GENERATED ALWAYS | Hay que no insertarlo. El consumidor tiene USAGE sobre la secuencia (002_roles L64). OK. |
| event_id | text, nullable | Solo se copia si es cadena, saneada. Hay un hueco (hallazgo 3). |
| reason | NOT NULL | Valor de la lista de 14 motivos. OK. |
| original | jsonb, nullable | **Hueco**: NaN, Infinity y números enormes (hallazgo 1). Lo cubren el NUL y el `\ud800` por la vía de saneado. |
| raw_text | text, nullable | Con el decodificado saneado, OK. El `''` del tombstone cumple `IS NOT NULL`. |
| original_sha256 | NOT NULL, `^[0-9a-f]{64}$` | `hashlib.hexdigest()` en minúsculas, calculado sobre los bytes. El tombstone usa los 0 bytes. OK. |
| source | CHECK NULL o uno de los 3 valores | Resuelto por la regla de copia. OK. |
| kafka_topic / partition / offset | text / integer / bigint, nullable | Siempre salen del consumidor. OK. |
| received_at | timestamptz NOT NULL | Reloj del consumidor. OK. |
| is_synthetic | boolean NOT NULL | Solo se copia si es booleano; si no, `false`. OK. El plan debe usar `type(x) is bool`, y que `1` no cuente como booleano. |
| quarantine_has_original | `original` o `raw_text` no nulos | El saneado deja `original` en NULL y `raw_text` informado. OK. |
| UNIQUE(original_sha256, reason) | | `ON CONFLICT DO NOTHING` simple. El consumidor solo tiene INSERT, y eso encaja. OK. |

Sin los huecos de abajo, la regla de copia de FR-011 sí evita violar el CHECK de source, el NOT NULL de is_synthetic y el tipo de event_id.

## 2. Hallazgos

| # | Hallazgo | Gravedad | Dónde | Regla afectada |
|---|---|---|---|---|
| 1 | NaN, Infinity, -Infinity y números fuera de rango de `numeric`, p. ej. `1e999999`, no se detectan como contenido no almacenable. Python `json.loads` acepta NaN e Infinity, y `json.dumps` los emite. `jsonb` los rechaza con 22P02 o 22003, que son clase 22. El contrato exige que `mag` NaN vaya a `mag_out_of_range`, así que ese mensaje llega a cuarentena con `original` que contiene NaN, y el INSERT de cuarentena falla. Según FR-014 eso es "error de base, reintento sin recursión", es decir, bloqueo permanente de la partición con un mensaje del contrato. Pasa igual con NaN en un campo no validado (p. ej. `dmin`): el mensaje pasa la validación, falla en `event_version.original` y vuelve a fallar en la cuarentena `db_constraint_violation`. | **Bloqueante** para el objetivo "el INSERT no puede violar nada por el contenido" | spec.md FR-011 (detección solo de NUL y no UTF-8), FR-014, US3.9, Edge Cases | Constitución §6; FR-011/014 |
| 2 | No se exige validar el tipo de todas las columnas que se escriben. `place`, `url`, `mag_type`, `status`, `event.id` de tipo numérico, `time`/`sig` booleanos (bool es subclase de int en Python) o `lon`/`lat` no numéricos pasan si `invalid_field_type` solo se aplica a unos pocos campos. El driver los envía a una columna `text` y falla con SQLSTATE 42804 o `ProgrammingError`. Eso no es clase 22/23, así que se reintenta sin fin. | Importante | FR-004, FR-016, contrato §6 `invalid_field_type`; la spec solo cita `sig`, `status`, `mag` | Constitución §6; FR-014 |
| 3 | Un `event_id` muy largo, de más de unos 2,7 KB, rompe el índice con 54000 (`index row size exceeds maximum`). Afecta al índice parcial `ix_quarantine_event_id` en la cuarentena y a la PK de `current_event` y `event_version` en los mensajes válidos. El fallo depende del contenido del mensaje, no del entorno. En cuarentena se evita con un tope de longitud en la regla de copia. En mensajes válidos hoy cae en el "límite 54*" aceptado, pero ese límite se pensó para errores de entorno. | Importante (pregunta al alumno) | FR-011 regla de copia, FR-014, Edge Cases (límite 54*) | Constitución §6 |
| 4 | Excepciones de Python no listadas. `json.loads` con enteros de más de 4300 dígitos lanza `ValueError`, que no es `JSONDecodeError` ni `RecursionError`. La "excepción equivalente del cliente" depende del driver: psycopg3 da `DataError`, psycopg2 da `ValueError` para NUL. | Menor para la spec, pero hay que fijarlo en el plan | FR-011 (casos que no pueden tumbar), FR-014 | Constitución §6 |
| 5 | FR-036 está fuera de secuencia, entre FR-024 y FR-025, con nota explícita de que la numeración se mantiene. Sus referencias (SC-009, bitácora L16-17) son correctas. No es un defecto real. Renumerar rompería las referencias de bitácora e informes sin ganar nada. | Menor, aceptable | spec.md FR-036 | — |
| 6 | La sección de preguntas abiertas numera "2." y "3." sin "1.", y el punto pendiente de la regla de copia no tiene número. | Menor | spec.md Preguntas para el alumno | — |
| 7 | La regla de copia figura como MUST en FR-011, FR-014, US3.8 y US3.9 pero está "pendiente de confirmar". Es coherente, pero hay que cerrarla antes del plan. | Menor | FR-011, Preguntas | — |

## 3. Otros caminos de bloqueo de partición
- **Resto de clases:** salvo 1 a 3, solo quedan los errores de entorno (08*, 40*, 53*, 57*), que el diseño reintenta a propósito. Los desbordes de `timestamptz` y de `smallint` en `date_dim` son clase 22 y van a `db_constraint_violation`. Los cubre `value_out_of_range` o el CHECK.
- **Profundidad de anidado:** por debajo del límite de Python no hay problema en PostgreSQL.
- **Coherencia FR-023 y FR-036:** las fórmulas y las cifras cuadran. FAQ 12: 5 = 2+1+0+2+0 = 5. Con inválido repetido: 7−2 = 5. Con db_constraint_violation repetido: 7−0 = 7 = 2+1+0+2+0+2.
- **Otras referencias cruzadas:** US3.9, US3.10, FR-011 y FR-014 son coherentes entre sí. Los contratos no cambian.
- **Pendiente en la spec:** el orden del insert de `date_dim` frente al rollback es un detalle del plan.

## 4. Decisiones que el alumno debe tomar
1. **NaN, Infinity y números enormes.** El contrato manda a `mag_out_of_range` los `mag` NaN. ¿Se amplía la detección previa al INSERT para estos casos, de modo que `original` quede NULL y `raw_text` guarde el texto, igual que con NUL? Es la opción coherente con el contrato.
2. **Validación de tipos de todas las columnas escritas.** ¿Se fija como MUST que cada columna que se escribe tenga su tipo validado, mapeando a `invalid_field_type`? Incluye excluir bool como entero y exigir `event.id` cadena.
3. **`event_id` demasiado largo.** ¿Se pone un tope de longitud en la regla de copia, con NULL si lo supera? ¿Qué se hace con un `event.id` largo en un mensaje válido: `invalid_field_type`, `value_out_of_range`, o se acepta el bloqueo como el límite 54* ya documentado?
4. **Confirmar la regla de copia** (`source`, `event_id`, `is_synthetic`), que sigue pendiente.

## 5. Veredicto
**Corregir antes de revisar.** El hallazgo 1 sigue permitiendo que un mensaje cubierto por el contrato, un `mag` NaN, bloquee la partición. Los hallazgos 2 y 3 son del mismo tipo. El resto es menor.
