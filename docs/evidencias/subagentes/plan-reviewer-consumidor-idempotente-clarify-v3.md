Revisión CLARIFY, vuelta 3, consumidor-idempotente (solo lectura, sin cambios ni commits).

**Qué leí.** Constitución (§1, §6, §14, §15 y §16 como reglas afectadas), CLAUDE.md, spec.md y checklists/requirements.md completos, informe de la vuelta 2, y los contratos db-schema.md y kafka-message.md completos. De 002 leí FR-008, FR-009 y el bloque A4 del spec.md, pero no research.md §7 ni plan.md. Del procedimiento solo hice grep de la fila y la semilla del §4/§4.2; no leí roadmap F3 ni checklist C1–C8/C13 por separado. No existen plan.md ni tasks.md. No leí bitacora.md. `git diff` de contratos y enunciado está vacío (dato del orquestador).

**Veredicto de los tres puntos pedidos**

1. **Saneado frente a los contratos: encaja.**
   - `raw_text` saneado y `original` NULL cumplen el CHECK de `db-schema.md` §3.5 (al menos uno de los dos).
   - `original_sha256` sobre los bytes originales respeta la unicidad `(original_sha256, reason)`.
   - `kafka-message.md` §6 dice "la base rechaza el INSERT" y "sin bloquear la cola".
   - No cambia ningún contrato.
   - Quedan dos huecos en los que la cuarentena aún puede bloquear la partición (hallazgos 1 y 2).
2. **Fórmulas de FR-023: recalculadas, cuadran.**
   - FAQ 12 (5/5): 5 − 0 = 5 conversiones, y 2 + 1 + 0 + 2 + 0 + 0 = 5.
   - Inválido repetido: 7 recibidos − (1 nueva + 1 duplicada) = 5. La segunda fórmula también da 5.
   - `db_constraint_violation` repetido (1 nueva + 1 duplicada): 7 recibidos − 0 = 7 conversiones, y 5 + 2 = 7.
   - El hallazgo de la vuelta 2 está resuelto.
3. **Coherencia US3.8, US3.9, FR-014, Edge Cases y Preguntas 0, 4 y 5:** consistente salvo los hallazgos 1 y 3.

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| 1. El saneado solo cubre `original` y `raw_text`. `quarantine.event_id` y `quarantine.source` también son `text`. Un `event.id` con `\u0000` (por ejemplo `"a\u0000b"`) pasa `missing_id` por no estar vacío, y el `INSERT` en cuarentena falla igual. Hay que decir que esos campos se saneados o se dejan en NULL. Si no, el reintento es infinito y la partición queda bloqueada. | importante | spec.md: FR-011, FR-014, US3.9, Edge Cases | Constitución §6; db-schema.md §3.5 (`event_id` y `source` admiten NULL) |
| 2. US3.9 restringe el motivo a "`db_constraint_violation` o `invalid_json`". Un JSON válido con `\u0000` y además latitud 145 va a `coordinates_out_of_range`, o a `invalid_envelope`, `invalid_field_type`, etc. Su `original` jsonb falla igual, y FR-011 y FR-014 sí lo cubren (cualquier motivo). Lo mismo en la Pregunta 5: "pero sí para `invalid_json`" omite los demás motivos de validación. | importante | spec.md: US3.9, Preguntas punto 5 | FR-011; constitución §6 |
| 3. La excepción de FR-014 es "SQLSTATE clase 22 provocado por el contenido", pero no dice cómo se distingue de otra clase 22 en el `INSERT` de cuarentena. Además psycopg rechaza el NUL en el cliente (`DataError`, a menudo sin SQLSTATE). Conviene que la spec diga que el saneado se detecta antes de escribir (NUL o bytes no UTF-8 en el contenido), y no por el SQLSTATE devuelto. También falta decir qué pasa si el intento saneado vuelve a fallar: reintento sin recursión. | menor (el detalle va al plan, pero la regla debe estar en la spec) | spec.md: FR-011, FR-014 | FR-014 |
| 4. El valor de Kafka nulo (tombstone) o vacío no está cubierto. `raw_text` vacío cumpliría el CHECK, pero no está dicho qué motivo ni qué hash lleva. | menor | spec.md: Edge Cases, FR-011 | kafka-message.md §6 |
| 5. SC-009 y US5.3 dicen "casos inválidos", pero la spec no enumera los casos concretos que exige FR-023b. Pide el inválido repetido; el `db_constraint_violation` repetido queda sin exigir. El nombre "FR-023b" es irregular (el resto de FR son enteros). | menor | spec.md: FR-023b, SC-009, US5.3 | C8; SC-009 |
| 6. El mensaje venenoso con un error persistente de otra clase (por ejemplo `54*`, límite de programa) sigue bloqueando la partición por diseño (Q4 y punto 0c). Es una tensión conocida con "no bloquean la cola", ya declarada como provisional. | menor (pregunta para el alumno) | spec.md: Q4, FR-014, Preguntas 0c | Constitución §6 |
| 7. El tope de espera y la tasa de registro se delegan al plan. El checklist marca los requisitos como "sin ambigüedad" aunque los puntos 4 y 5 están abiertos. | menor | spec.md: FR-014, FR-029; checklists/requirements.md | 002 FR-008 y FR-009 |

**Decisiones que debe tomar el alumno**
- Punto 4: clases 22 y 23, o solo 23.
- Punto 5: aceptar la excepción de saneado y confirmar que alcanza a `event_id` y `source`, y a cualquier motivo de cuarentena.
- Punto 0c: ¿se acepta que un error persistente de otra clase bloquee la partición, o se quiere un límite de intentos?

Ninguna decisión exige cambiar contratos ni constitución.

**Veredicto:** Corregir antes de revisar. Son dos ediciones puntuales de texto (hallazgos 1 y 2), más aclaraciones menores. Es la última vuelta permitida, así que si no se corrigen, conviene llevar los hallazgos 1 y 2 al alumno como preguntas.
