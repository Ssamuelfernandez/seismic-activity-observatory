Revisión independiente de CLARIFY, feature consumidor-idempotente (solo lectura). Archivo revisado: C:\Users\Samuel\Desktop\Proyectos Curso\seismic-activity-observatory\specs\003-consumidor-idempotente\spec.md. También leí bitacora.md, la constitución, los contratos y 002 FR-008/FR-009. No he leído checklists/requirements.md, 02-roadmap F3, el checklist C1–C8/C13 ni el §4/§4.2 del procedimiento, y tampoco he comprobado los informes previos de `docs/evidencias/subagentes/`. Mi comprobación de cobertura y alcance no se apoya en ellos. No reclamo plan.md ni tasks.md. No he hecho commits ni modificado nada.

**Resultado:** las 5 clarificaciones no contradicen kafka-message.md §6, db-schema.md ni la constitución, salvo los puntos de la tabla. No amplían el alcance: sin DLQ, sin tablas nuevas y sin cambio de contrato. Sí hay huecos de coherencia interna y un riesgo en la clarificación 2.

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| Clase 23 es demasiado estrecha. Un error de datos de clase 22 (p. ej. `\u0000` en jsonb/text, 22021 o 22P05, overflow numérico o de fecha que escape a la validación) no es de integridad, así que cae en "reintento infinito sin cuarentena". Un mensaje no válido bloquea la partición para siempre. El contrato dice "la base rechaza el `INSERT`" sin limitar la clase, y el brief dice "mensaje inválido → quarantine + commit offset". | importante | Clarifications Q2 y Q4; FR-014; Preguntas punto 0(b)(c) | kafka-message.md §6 (último recurso); constitución §6 ("no bloquean la cola"); brief |
| Los contadores se incrementan "tras el commit en PostgreSQL", pero el offset se confirma después. Si falla el commit del offset (Kafka caído, US2.5) o hay rebalanceo en la misma sesión, el mensaje se reentrega y cuenta otra vez como "recibido" y "reenvío ignorado". Eso contradice "una sola vez por mensaje" y rompe la conciliación de SC-009. | importante | FR-023; Clarifications Q1; US2 escenario 5 | C8; SC-009 |
| FR-023 dice que "los mensajes en cuarentena no la cuentan" (la conversión a UTC), pero la segunda fórmula suma `db_constraint_violation` a las conversiones. Ese mensaje está en cuarentena y sí se transformó. El texto se contradice, aunque las dos fórmulas son coherentes entre sí. | menor | FR-023 | C8; SC-009 |
| No se dice si un duplicado de cuarentena (`ON CONFLICT DO NOTHING`, sin fila nueva) incrementa "cuarentenas por motivo". Si lo hace, el contador no coincide con el recuento SQL de SC-009. Con Q5 (dedup por bytes) el caso es explícito en US3.5. | menor | FR-012; FR-023; US3 escenario 5; Clarifications Q5 | SC-009 |
| Un `INSERT` en cuarentena que falle con clase 23 (o clase 22) durante el camino `db_constraint_violation` no tiene tratamiento. Podría entrar en bucle. | menor | FR-014; Edge Cases ("Fallo al escribir en cuarentena") | constitución §6 |
| La "espera creciente acotada" está en Q3, pero FR-014 solo dice "espera". El tope no está en un requisito. Además, el reintento por mensaje venenoso genera un registro por intento sin límite. | menor | Clarifications Q3; FR-014 | 002 FR-008/FR-009 |
| No se dice si durante el reintento infinito se renueva el latido. Con "saludable = sigue procesando" (FR-029; 002 A4: latido tras cada vuelta correcta), un mensaje venenoso deja el contenedor `unhealthy`. Es plausible, pero es decisión de plan y debe quedar escrita. | menor | FR-029; Clarifications Q4 | A4 |
| US3 escenario 6 no menciona SQLSTATE clase 23 ni el momento del `COMMIT`. Solo FR-014 y las Notas lo cubren, y no hay criterio de aceptación para el caso "otro error de base → reintento sin cuarentena". Esto último cubre solo parcialmente US2.3 (base caída). | menor | US3 escenario 6; US2 | FR-014 |
| El punto 0 afirma "ninguna cumple criterio de escalado". Q2(b) acota la lectura del contrato (§6 no limita la clase de error). Debería quedar como pregunta explícita al alumno, no como aceptada. | menor | Preguntas punto 0 | kafka-message.md §6 |

**Contradicciones con el contrato**
- `db_constraint_violation` en la prevalencia (último motivo, tras `value_out_of_range`) es coherente.
- La extensión al `COMMIT` (FK diferida, db-schema §3) es una lectura razonable, no un cambio.
- Dedup por `(original_sha256, reason)` coincide con db-schema §3.5 y Q10.
- La regla "offset sin confirmar si falla la BD" se cumple.

**Coherencia interna**
- FR-014, FR-023, SC-009, US1, US2 y US5 son coherentes, salvo lo anotado arriba.
- La secuencia FAQ 12 cuadra: 5 recibidos, 2 nuevos, 1 reciente, 2 reenvíos y 5 conversiones.
- No quedan marcadores sin resolver: solo el texto "Sin marcadores [NEEDS CLARIFICATION]" en el checklist, y ningún TBD ni "a decidir".

**Decisiones que debe tomar el alumno**
1. ¿Ampliar `db_constraint_violation` a SQLSTATE clase 22 (data exception) además de la 23, para que ningún mensaje de datos no válido bloquee la partición? Sería una interpretación de §6, no un cambio de contrato, pero hay que confirmarlo.
2. ¿Los contadores se incrementan tras el commit del offset, o se acepta el posible doble conteo en redelivery y se documenta?
3. ¿Un duplicado de cuarentena cuenta en el contador?
4. ¿El latido se renueva durante el reintento infinito?

**Veredicto:** Corregir antes de revisar (2 importantes: hueco de clase 22 y el momento de incremento de los contadores frente al commit del offset).
