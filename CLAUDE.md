# Observatorio sísmico — instrucciones para el agente

- Lee `.specify/memory/constitution.md` antes de cualquier cambio: son las reglas no negociables.
- Los contratos están en `specs/001-contratos-y-modelo/contracts/`. No los dupliques ni los cambies sin avisar.
- `docs/enunciado/` es SOLO LECTURA (material del profesor). No lo modifiques.
- Procedimiento y reglas de código: `docs/planificacion/03-procedimiento-ejecucion.md` (plantilla de docstring en §7.4). Orden de fases: `02-roadmap-implementacion.md`. Requisitos: `01-checklist-requisitos.md`.
- Identificadores en inglés; docstrings y comentarios en español.
- Antes de crear un archivo nuevo, consulta `CODEMAP.md` y úsalo para decidir dónde va.
- Una feature cada vez. No implementes sin spec, plan y tareas revisados. Al terminar una feature, detente y espera revisión; no hagas commits ni merges sin aprobación.
- Al terminar una tarea: tests ejecutados, evidencia en `docs/evidencias/`, `CODEMAP.md` actualizado.
- El frontend no calcula estadísticas: muestra lo que devuelve la API. Los datos de mock son sintéticos y van etiquetados.
- Nunca añadas trailers Co-Authored-By ni líneas de "generado por" en commits o PRs.
- No amplíes el alcance: nada fuera de lo que pide la spec de la feature activa.