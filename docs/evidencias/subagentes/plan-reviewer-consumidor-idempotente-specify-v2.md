**Revisión SPECIFY, vuelta 2, `consumidor-idempotente` (`specs/003-consumidor-idempotente/spec.md`)**

Solo existen spec.md, checklists/requirements.md y bitacora.md. No reclamo plan.md ni tasks.md. Según lo que me indicaste, `git diff` de contratos y enunciado está vacío. Yo no lo he ejecutado.

**Verificación de los hallazgos de la vuelta 1**

| Hallazgo previo | Estado | Dónde se comprueba |
|---|---|---|
| Hash de cuarentena (importante) | Resuelto | FR-011 fija `original_sha256` como SHA-256 hex de los bytes recibidos, sin deserializar ni re-serializar, también para `invalid_json`. FR-012 lo usa como clave de idempotencia y Assumptions lo repite. Los tres textos coinciden y no contradicen `db-schema.md` §3.5 ni la unicidad `(original_sha256, reason)`. |
| Pregunta 1 y SC-001 | Resuelto | La Pregunta 1 aparece como "Cerrada" y SC-001 cita la FAQ 12. La FAQ 12 (líneas 186-194) dice "tres versiones distintas observadas en total" y su columna acumulada acaba en 3, igual que la spec. |
| E2 con 10:12 y mag 3.1 | Resuelto | Están en US1.5 y SC-001. |
| Unidad del contador de conversiones | Resuelto | FR-023 la define: un incremento por mensaje válido transformado, incluidos reenvíos y conflictos, y sin contar la cuarentena. |
| Base limpia para C8 | Resuelto en Assumptions | Ver el hallazgo menor 1 más abajo. |
| Notas para el plan | Resuelto | La sección "Notas para el plan" recoge: sin `RETURNING` ni `DO UPDATE` en cuarentena; `db_constraint_violation` puede saltar en el `COMMIT` por la FK diferida; el mecanismo de corte de la prueba 8 queda para el plan. |

**Recálculo de conciliación con la secuencia FAQ 12**

| Mensaje | Conversión | Clasificación |
|---|---|---|
| 1. E1 10:05 | sí (1) | evento nuevo |
| 2. E1 10:05 repetido | sí (2) | reenvío |
| 3. E1 10:09 | sí (3) | versión más reciente aplicada |
| 4. E1 10:05 repetido | sí (4) | reenvío, porque ya estaba en el historial |
| 5. E2 10:12 | sí (5) | evento nuevo |

- Los contadores salen: 5 recibidos, 2 eventos nuevos, 1 más reciente, 2 reenvíos, 0 antiguas tardías, 0 conflictos y 5 conversiones. Coinciden con US5.3.
- Primera fórmula de FR-023: recibidos − cuarentenas por validación = 5 − 0 = 5. Cuadra.
- Segunda fórmula: 2 + 1 + 0 + 2 + 0 + 0 = 5, con `db_constraint_violation` = 0. Cuadra.
- El estado de la base sale de 2 eventos actuales y 3 versiones (E1×2 + E2×1), como pide SC-001.
- La exclusión de `db_constraint_violation` de la primera fórmula es coherente. Ese motivo se produce después de transformar, así que sí cuenta como conversión, y la segunda fórmula lo suma.
- La FAQ 12 no incluye una antigua tardía no vista. FR-031 y US5.3 la tratan como caso aparte.

**Hallazgos**

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| 1. La condición de "base y grupo de consumo limpios" para reconciliar contadores solo está en Assumptions. FR-023 y SC-009 hablan de coincidencia al 100 % sin mencionarla. | menor | spec.md, FR-023, SC-009 y Assumptions (último punto) | C8 |
| 2. FR-012 deduplica por bytes idénticos. Un mismo mensaje inválido con distinta serialización generaría otra fila de cuarentena. Es consecuencia aceptable de la decisión del hash, pero conviene que el plan lo documente. | menor | FR-011 y FR-012 | C5, `db-schema.md` §3.5 |
| 3. La redacción "3 versiones guardadas entre las dos tablas de evento y versión" en la intro de US1 es confusa. Las 3 filas son solo de `event_version`. | menor | US1, párrafo inicial | claridad |
| 4. Los contadores de "recibidos" y de conversiones, en reintentos por caída de base de datos o de Kafka, podrían contar un mismo mensaje dos veces. La spec no fija si se cuenta por mensaje o por intento. Es un detalle para el plan. | menor | FR-023 y US2.3 | C8 |

No hay hallazgos bloqueantes ni importantes. La corrección no introdujo incoherencias. Las preguntas 2 y 3 siguen abiertas como recomendación, lo cual es adecuado.

**Decisiones que el alumno debe tomar**
1. Aprobar el hash como SHA-256 de los bytes recibidos.
2. Confirmar que los contadores de C8 queden solo en memoria y registro (Pregunta 2).
3. Confirmar que solo se consume `earthquakes.live` (Pregunta 3).

**Veredicto:** Listo para tu revisión.
