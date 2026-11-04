Revisión CLARIFY, vuelta 1 tras reanudación, consumidor-idempotente (solo lectura, sin cambios ni commits).

**Qué leí.** Constitución (§1, §6, §14, §15, §16), CLAUDE.md (por el contexto recibido), spec.md, checklists/requirements.md y bitacora.md completos, informe v3, kafka-message.md y db-schema.md completos, y `sql/001_schema.sql` (tabla `quarantine`, líneas 140-159). Del procedimiento leí la fila del §4 y la semilla del §4.2 (por grep) y el flujo de pasos. También leí roadmap F3, checklist C1–C8 y C13 y los FR-008 y FR-009 de 002. No existen plan.md ni tasks.md. No toqué `specs/001-contratos-y-modelo/contracts/` ni `docs/enunciado/` (diff vacío, dato del orquestador).

**Estado de los 7 hallazgos del informe v3**
- **1 (saneado de `event_id` y `source`):** resuelto en texto (FR-011, FR-014, US3.9, Edge Cases).
- **2 (cualquier motivo):** resuelto (US3.9 y Pregunta 5).
- **3 (detección antes del `INSERT`, sin recursión):** resuelto.
- **4 (tombstone):** resuelto (US3.10), con un matiz de numeración (ver abajo).
- **5 (casos de SC-009):** resuelto (FR-036), con matices.
- **6 (error persistente 54\*):** resuelto como límite aceptado, y consistente en Q4, FR-014, Edge Cases y Preguntas.
- **7 (checklist):** resuelto. Solo quedan abiertas las Preguntas 2 y 3, y la nota del checklist lo refleja.

**Veredicto por punto**
1. **Saneado frente a los contratos: encaja, pero queda un camino de bloqueo nuevo (hallazgo A).**
   - `original` NULL más `raw_text` saneado cumple el CHECK `quarantine_has_original`.
   - `original_sha256` sobre los bytes originales respeta `UNIQUE (original_sha256, reason)` y el CHECK `^[0-9a-f]{64}$`, siempre que el hex sea en minúsculas.
   - `event_id` y `source` son nulables según db-schema.md §3.5.
   - No cambia ningún contrato.
2. **Tombstone o valor vacío: coherente.**
   - `invalid_json` es el motivo que corresponde a "el valor no es JSON válido" (kafka-message.md §6).
   - `raw_text = ''` no es NULL, así que cumple el CHECK. El hash de 0 bytes (`e3b0c442…`) cumple el regex.
   - Nulo y vacío colapsan en una fila por `(hash, invalid_json)`. La spec lo declara consecuencia aceptada.
   - Los repetidos pierden su (tema, partición, offset) propio, igual que cualquier duplicado por bytes.
3. **FR-036 y SC-009: las cuentas cuadran.**
   - FAQ 12: 5 − 0 = 5, y 2+1+0+2+0+0 = 5.
   - Inválido repetido: 7 − (1+1) = 5, y la segunda fórmula también da 5.
   - `db_constraint_violation` repetido: 7 − 0 = 7, y 2+1+0+2+0 + (1+1) = 7. Es coherente con FR-023, porque el duplicado de ese motivo sí cuenta conversión.
   - No encontré referencias huérfanas a FR-023b. Solo queda el aviso histórico "(Antes FR-023b…)" dentro de FR-036.
4. **Coherencia de Clarifications, FR-014, US3.x, Edge Cases y Preguntas:** consistente. Detalles en la tabla.

| Hallazgo | Gravedad | Dónde | Regla o ID afectado |
|---|---|---|---|
| **A.** Camino de bloqueo no cubierto: el DDL tiene `CONSTRAINT quarantine_source_values CHECK (source IS NULL OR source IN ('usgs_feed','usgs_historical','replay_demo'))` (`sql/001_schema.sql` líneas 155-156, también en `replay.quarantine`). Un mensaje con `source` fuera de la lista (`invalid_envelope`, que el contrato prevé) falla en el `INSERT` de cuarentena con SQLSTATE 23514. US3.8 y FR-014 lo tratan como "error de base, reintento sin límite" y la partición queda bloqueada para siempre. El saneado solo detecta NUL y bytes no UTF-8, y "saneado o a NULL" para `source` no basta: un texto escapado sigue incumpliendo el CHECK. Lo mismo ocurre con `is_synthetic` no booleano o ausente (columna NOT NULL) y con `event.id` o `source` que no sean cadena (p. ej. un entero). Falta la regla: en cuarentena, `source` solo se copia si es uno de los tres valores y si no va a NULL; `event_id` solo si es cadena; `is_synthetic` solo si es booleano y si no va a `false`. Todo cabe en db-schema.md §3.5 (nulabilidad), sin tocar el contrato. | importante | spec.md: FR-011, FR-014, US3.8, US3.9, Edge Cases | Constitución §6; kafka-message.md §6 (`invalid_envelope`) |
| **B.** Otros dos caminos que rompen o bloquean al consumidor y no están nombrados. (i) Un JSON válido con un escape `\ud800` (sustituto suelto) da una cadena Python que no se puede codificar a UTF-8: falla en el cliente (`UnicodeEncodeError`), no en la base. (ii) Un JSON anidado con unos 1000 niveles lanza `RecursionError`, que no es el error de JSON inválido habitual. La spec dice "NUL o bytes no UTF-8" y "valor que no es JSON válido", pero no que estos casos entren por la misma vía: saneado en (i) e `invalid_json` en (ii). Sin esa regla el consumidor cae en bucle de reinicios sobre ese offset. El detalle va al plan, pero la regla debe estar en la spec. | menor | spec.md: FR-011, Edge Cases | Constitución §6 |
| **C.** FR-014 clasifica "por SQLSTATE clase 22/23", pero el rechazo del NUL lo suele dar el cliente (`DataError` de psycopg, a menudo sin SQLSTATE). Conviene decir "clase 22/23 o excepción equivalente del cliente de datos". | menor | spec.md: FR-014, Notas para el plan | FR-014 |
| **D.** Un JSON válido que no es objeto (`null`, `[]`, `123`) no tiene motivo explícito. Lo natural es `invalid_envelope` ("carece de campos de primer nivel"), pero conviene dejarlo escrito. | menor | spec.md: US3, Edge Cases | kafka-message.md §3 y §6 |
| **E.** Numeración. La lista de US3 está en el orden 1, 2, 3, **10**, 4…9. En Markdown renderizado las listas ordenadas se renumeran en secuencia, así que "10." se ve como 4 y "US3.5" apunta al escenario de `mode_topic_mismatch` o al duplicado según el visor. Es un defecto real (FR-036 cita "US3.5" y Edge Cases cita "US3.10"). Hay que moverlo al final como 10. FR-036 está al final de "Documentación y cierre", cuando por tema pertenece a "Datos sintéticos y contadores". No es un defecto funcional, pero el aviso "(Antes FR-023b; …)" es historial de edición y debería quitarse (para eso está la bitácora). | menor | spec.md: US3.10, FR-036 | Legibilidad y trazabilidad de referencias |
| **F.** El tercer caso de FR-036 (`db_constraint_violation` repetido) no tiene sus cifras en la spec (7 recibidos → 7 conversiones). Solo están las de los otros dos casos, en FR-023. Conviene añadirlas a FR-036. La spec tampoco dice cómo se provoca ese caso en una prueba (p. ej. un NUL en `place`, clase 22). Eso es del plan. | menor | spec.md: FR-023 (comprobaciones), FR-036, SC-009 | C8; SC-009 |
| **G.** El hex de `original_sha256` debe ser en minúsculas por el CHECK `^[0-9a-f]{64}$`. La spec dice "hex" a secas. | menor (plan) | spec.md: FR-011 | db-schema.md §3.5 |

**Decisiones que debe tomar el alumno**
- Hallazgo A: ¿se aceptan las reglas de copia a cuarentena (`source` solo si está en los tres valores, si no NULL; `event_id` solo si es cadena; `is_synthetic` solo si es booleano, si no `false`)? La alternativa sería dejar el bloqueo como otro límite documentado, algo difícil de defender porque es un caso de validación común (`invalid_envelope`), no un fallo del sistema.
- Hallazgos B y D (opcional): ¿se escriben en la spec o se delegan al plan?
- Siguen abiertas las Preguntas 2 (contadores solo en memoria) y 3 (solo `earthquakes.live`). Ninguna cambia contratos ni constitución.

**Veredicto:** Corregir antes de revisar. El hallazgo A es una edición puntual de texto en FR-011, FR-014 y US3.9. Con E (renumerar US3.10) y F, el resto son aclaraciones menores.
