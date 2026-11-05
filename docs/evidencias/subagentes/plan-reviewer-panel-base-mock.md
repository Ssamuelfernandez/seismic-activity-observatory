Revisión de 008-panel-base-mock (spec, plan y tasks): no encuentro hallazgos bloqueantes ni importantes.

- **Cobertura:** G0, G2, G11 (parcial), G12 (`magType`), G14, G15 y G17 aparecen cada uno en la spec (FR y SC) y tienen tarea y prueba.
  - G0: T001 y T019.
  - G2: T010, T013, T014, T015 y T018.
  - G11 (parcial): T012, T017 y T020.
  - G12 (`magType`): T002, T013 y T016.
  - G14: T012 y T020.
  - G15: T003, T004, T008 y T009.
  - G17: T013, T014, T017 y T018.
  - P3 evita marcar G11 como hecho al cerrar la feature (T021).
- **Contratos:** el plan los cita y no los redefine. Los cortes de profundidad 10/35/70/300 coinciden con `api.md` §5.1. La forma del caso `truncated` (5 000 de 6 213, `next_cursor` no nulo) coincide con `api.md` §3.2. `git diff` de contratos, enunciado y schema sale vacío.
- **Constitución:** no hay contradicciones.
  - §5: los nulos se muestran como ND y nunca como 0.
  - §7: los datos sintéticos van marcados y el modo `api` no cae al mock.
  - §10: sin secretos ni claves.
  - §11: versiones exactas con lock.
  - §13: identificadores en inglés y textos en español.
  - §14: la lógica pura (`lib/`) va separada de la lectura y el dibujo.
  - §16: T018 a T021 guardan evidencias y actualizan `CODEMAP.md` y los README.
  - §17: el frontend no calcula estadísticas; `count` y `total` salen del JSON.
  - §19: el plan no incluye código.
  - §21: sin lenguaje de predicción.
- **Alcance:** no hay filtros, tabla, gráficos, conexión real, estado, replay ni despliegue. T019 y SC-014 comprueban su ausencia. D2 no instala nada.
- **Tamaño y dependencias:** 21 tareas en 5 bloques. La cadena T007 → T015 → T016 espera la decisión D1, pero el plan lo asume y deja el resto en paralelo.
- **Decisiones del alumno:** D1, D2 y D3 siguen sin fijar y aparecen como "provisional, no fijada". No hay "TBD" sueltos.

**Decisiones que debe tomar el alumno:**
- D1: librería del mapa. La decide en T007, tras la tabla de T006.
- D2: librería del store. No bloquea esta feature.
- D3: estructura de `src/`. Las rutas de las tareas son provisionales.
- Q1 a Q5 de `tasks.md`: candidatas del prototipo, `?scenario=` desconocido, capturas manuales, ubicación del mock (P4) y TypeScript 7.0.2 frente a 6.0.3.

**Límite conocido:** no pude verificar con `npm view` que las versiones fijadas (TypeScript 7.0.2, Vite 8.3.6, Vitest 5.1.0) existan. El plan ya tiene plan B para TypeScript.

Veredicto: Listo para tu revisión.
