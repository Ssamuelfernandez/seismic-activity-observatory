Revisión CLARIFY, vuelta 2, consumidor-idempotente (solo lectura, sin cambios ni commits). Leí: constitución, CLAUDE.md, procedimiento §4/§4.2, roadmap F3, checklist C1–C8/C13, los tres contratos, 002 FR-008/FR-009, checklists/requirements.md, bitacora.md, spec.md y el informe de la vuelta 1. Para A4 de 002 solo leí la cabecera de la sección, no su texto completo. `git diff --stat` de contratos y enunciado está vacío, según el orquestador. No existen plan.md ni tasks.md.

**Resultado:** los 9 hallazgos de la vuelta 1 están resueltos en spec.md. Las ediciones introducen un hueco importante y dos menores.

**Comprobación de la vuelta 1**
- **Clase 22/23:** resuelto (Clarifications Q2, FR-014, US3.6/3.7, Notas para el plan, Preguntas punto 4).
- **Incremento de contadores tras el commit del offset:** resuelto (Q1, FR-023, US2.5, SC-009).
- **Contradicción de FR-023 sobre la conversión:** resuelta en el texto. Los mensajes de `db_constraint_violation` sí cuentan la conversión.
- **Contador de cuarentenas duplicadas:** resuelto (FR-023, US5.2).
- **Fallo de INSERT en cuarentena sin recursión:** resuelto (FR-014, US3.8, Edge Cases). Genera el hallazgo 1.
- **Tope de espera en FR-014:** resuelto. El valor concreto queda para el plan.
- **Latido sin renovar durante el reintento:** resuelto (FR-029, Q4).
- **Criterio de aceptación para otro error de base:** resuelto (US2.6, US3.7).
- **Punto 0 y pregunta explícita:** resuelto (punto 0 y punto 4).

**Recálculo con la secuencia FAQ 12**
- **Contadores:** recibidos 5, eventos nuevos 2, versión más reciente 1 (10:09), reenvíos ignorados 2 (mensajes 2 y 4), antiguas tardías 0, conflictos 0, conversiones 5. Coincide con US5.3 y SC-001.
- **Fórmula 1:** conversiones = recibidos − cuarentenas por validación = 5 − 0 = 5.
- **Fórmula 2:** 2 + 1 + 0 + 2 + 0 + 0 = 5.
- **Caso con un inválido (latitud 145):** recibidos 6, conversiones 5, cuarentena 1. Cuadra.
- **Caso con `db_constraint_violation`:** cuadra en ambas fórmulas.

**Clase 22 frente a los contratos**
- No contradice `kafka-message.md` §6 ni `db-schema.md` §2. Ambos dicen "la base rechaza el `INSERT`" sin limitar la clase.
- Es una lectura, no un cambio. Además se extiende al `COMMIT`, justificado por la FK diferida de `db-schema.md` §3.4.
- Está marcada como pendiente de confirmar por el alumno (punto 4).

**Numeración y referencias cruzadas**
- Correctas: US2.6, US3.7 y US3.8 son consecutivos. Las remisiones a FR-023, SC-009, "Historia 5, escenario 2" y "Preguntas, punto 4" apuntan a lo que dicen.

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| **Mensaje venenoso por caracteres nulos.** Un JSON válido con `\u0000` en un texto pasa la validación y falla al insertar en `jsonb` con 22P05 (clase 22). Eso va a `db_constraint_violation`, pero la cuarentena guarda `original` también como `jsonb`, así que su INSERT falla igual. US3.8 y FR-014 mandan tratarlo como error transitorio ("cualquier clase de error"), y el consumidor reintenta para siempre. Pasa lo mismo con un `invalid_json` cuyo `raw_text` contenga un byte nulo. La spec no dice cómo se decodifican los bytes que no son UTF-8 válido. Es el caso que la propia Q2 cita como motivo de la clase 22, y queda sin resolver: la partición se bloquea. | importante | spec.md: FR-014, US3.8, Edge Cases ("Fallo al escribir en cuarentena"), Notas para el plan | constitución §6 ("no bloquean la cola"); `kafka-message.md` §6; `db-schema.md` §3.5 (`original` jsonb o `raw_text`, con CHECK de al menos uno) |
| **La conciliación de FR-023 no cuenta los duplicados.** "Cuarentenas por motivo" excluye los duplicados, pero las fórmulas usan "cuarentenas por validación" y `db_constraint_violation` sin precisar si incluyen duplicados. Con un inválido repetido se obtiene recibidos 7, cuarentenas por validación 1 y duplicadas 1. La fórmula 1 da 6, pero las conversiones reales son 5. La fórmula 2 falla igual si el `db_constraint_violation` se repite. Hay que decir que "cuarentenas por validación" y `db_constraint_violation` incluyen los duplicados, o restar el contador aparte. | menor (importante si SC-009 incluye el caso duplicado de US3.5) | spec.md: FR-023 (conciliación), US5.2/5.3, SC-009 | C8; SC-009 |
| **El punto 4 sigue abierto y checklists/requirements.md lo trata como no bloqueante.** El checklist marca "Requisitos comprobables y sin ambigüedad" y dice que las preguntas no bloquean. Es coherente con la política de la spec, pero el plan depende de la respuesta (clase 22 y 23, o solo 23). | menor | checklists/requirements.md (Notes); spec.md, Preguntas punto 4 | `kafka-message.md` §6 |
| **El tope de espera y la tasa de log en el reintento de FR-014 no tienen valor.** Es aceptable como decisión de plan, pero debe quedar fijado ahí. | menor | spec.md: FR-014, FR-029 | 002 FR-008/FR-009 |

**Decisiones que debe tomar el alumno**
1. Punto 4: ¿`db_constraint_violation` cubre las clases 22 y 23, o solo la 23? La respuesta cambia el hallazgo 1. Con solo la clase 23, un `\u0000` bloquea la partición por diseño. Con ambas, hay que definir qué guarda la cuarentena cuando ni `jsonb` ni `text` admiten el valor. Una opción es guardar `raw_text` saneado (por ejemplo, con escape del nulo) o una representación escapada, siempre con el hash de los bytes originales. Si el alumno acepta una excepción a "cualquier clase de error" (US3.8), esa excepción debe quedar escrita.
2. Contadores: ¿los duplicados de cuarentena se restan o se incluyen en las fórmulas de conciliación? Es una cuestión de redacción, sin cambio de contrato.

Ninguna de las dos decisiones requiere cambiar contratos ni constitución.

**Veredicto:** Corregir antes de revisar. Hay un hallazgo importante (el cuarentena-fallido por caracteres nulos reabre el bloqueo de partición que la clase 22 quería evitar) y uno menor de coherencia aritmética en FR-023.
