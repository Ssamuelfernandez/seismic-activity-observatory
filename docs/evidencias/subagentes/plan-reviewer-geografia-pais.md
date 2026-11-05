# Informe plan-reviewer — geografia-pais

Revisión de geografia-pais (solo lectura). No hay hallazgos bloqueantes ni importantes.

- Contratos: el diff de contratos, enunciado y `sql/001_schema.sql` está vacío, y T025 lo vuelve a comprobar. El plan no redefine contratos.
- Constitución: cumple §1, §2, §4, §5, §6, §7, §8, §11, §12, §14, §15, §16 y §19. No hay motivos de cuarentena ni contadores nuevos. El país sale de la geometría y nunca de `place`.
- Tope: 25 tareas en 5 bloques, como pide el brief.
- Cobertura: C9: T001, T003–T005, T010–T013, T016, T017, T019, T021. C10: T002, T003, T008, T009, T021. C11: T004, T012. C12: T004, T016, T017. Prueba 5: T017, T021. Prueba 7: T004, T016, T021. Retoma de 003: T062–T067 → T002/T003 y T006–T009; T069 → T014; T080 → T020/T021.
- Alcance: sin tareas de histórico, replay, API ni frontend.
- Límite conocido, sin acción: geometría con menos de dos coordenadas no se prueba como caso propio (la cubre `invalid_geometry`).
- Decisiones para el alumno: Shapely sin GeoPandas; sin motivo nuevo para type != earthquake en el consumidor; catálogo cargado por el consumidor al arrancar.

Veredicto: Listo para tu revisión.
