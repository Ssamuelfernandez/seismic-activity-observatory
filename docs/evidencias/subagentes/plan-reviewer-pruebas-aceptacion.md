Revisión de 012-pruebas-aceptacion

Veredicto: Listo para tu revisión, con una corrección menor-importante.

Lo que comprobé y está bien:
- Cobertura: I1 a I11, G9 e I-resumen tienen criterio en la spec y al menos una tarea. La matriz de cobertura de tasks.md es coherente con spec y plan.
- Tareas y bloques: hay 24 tareas (T094 a T117) en 5 bloques, dentro del tope de 25 y 5.
- Rutas reales: existen todos los tests reutilizados (`test_faq12`, `test_geography`, `test_restart_crash`, `test_replay_consumer`, `test_api_replay_real` y los demás) y los helpers `TempDatabase`, `process_message` y `request_api`. También existen las evidencias citadas: `prueba1_evento_nuevo.out`, `bloque3_*`, `bloque4_prueba8_*`, `prueba8_reinicio.*`, `geografia_prueba5/7` y `replay/README.md`.
- Líneas citadas: `StatusBanners.tsx:86` ("Datos antiguos"), `main.tsx:9` y `useObservatory.ts` coinciden con la spec. Los textos "se verifica en vivo" están en `despliegue-tunel/README.md:17`, `prueba-09:3` y `prueba-10:3`, y T108 los corrige.
- Aislamiento: los datos se inyectan solo en `TempDatabase` o `replay`, con huella de `live` antes y después (T099 y T116).
- Pruebas 9 y 10: no se declaran verificadas; quedan "Pendiente del alumno".
- Constitución: se citan §7, §5, §6 y §16 sin contradecirlas. Contratos y `sql/001_schema.sql` no se tocan. T097 se ajusta al contrato `api.md` (`min_mag` y `null_mag_excluded`) y T098 al valor `country_id=none`.

| Hallazgo | Gravedad | Dónde | ID |
|---|---|---|---|
| La prueba 3 pide "SQL + captura" en el checklist. Ninguna tarea ni FR-010 prevé captura de la prueba 3: solo hay SQL y pytest. Ejemplo: en el README de la prueba 3 el alumno no podría enseñar la captura que pide el checklist. | Importante (afecta a la evidencia exigida, no a la lógica) | spec.md FR-010; tasks.md T103 y T109 | I3 |

Corrección mínima para el alumno: añadir la prueba 3 a T103, o escribir en la ficha de la prueba 3 que la evidencia es solo SQL más API y que la captura queda como plantilla.

Decisiones que el alumno debe tomar: las 5 de la sección "Preguntas para el alumno" de la spec ya tienen opción provisional y recomendada.

Límite conocido: el aviso y la recuperación de las pruebas 9 y 10 tardan hasta 60 s más el timeout, y con la pestaña oculta puede no haber refresco. Está documentado y no se corrige.
