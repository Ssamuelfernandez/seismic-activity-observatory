Informe de revisión de 013-revision-final. Veredicto: Corregir antes de revisar (2 puntos importantes, ambos de texto).

| Hallazgo | Gravedad | Dónde | Regla o ID |
|---|---|---|---|
| El criterio "`git status --porcelain` vacío tras la integración" no se puede cumplir tal cual. En el bloque 2 ya hay archivos nuevos sin versionar (`scripts/check_links.py`, `docs/README.md`, `RF/*`). Ejemplo: tras T124 `git status` muestra `?? scripts/check_links.py` y el criterio "vacío" falla. T124 dice "sin cambios en docs/evidencias por la ejecución", más débil que SC-003 y US2.1. Falta fijar una forma medible: comparar `git status --porcelain` antes y después de la suite, o `git diff --stat docs/evidencias` vacío. | importante | spec.md SC-003, US2.1; tasks.md T124 | Brief: "git status limpio tras integración"; FR-005 |
| T125 permite corregir rutas citadas "en texto de los documentos propios". Ese conjunto incluye `docs/borradores/` y los README de `docs/evidencias/`, que el brief declara fuera de alcance ("no tocar"). Ejemplo: una ruta rota en `docs/evidencias/geografia-pais/README.md` obligaría a editarlo. Hay que decidir si esos casos se anotan para el alumno (como ya se hace con el checklist) o se permite editarlos. | importante | tasks.md T125; plan decisión 4; spec FR-015 y FR-023 | Brief "No entra" (docs/evidencias, docs/borradores) |

Decisiones que el alumno debe tomar:
- Si T125 puede editar `docs/borradores/` y los README de evidencias, o solo anotar las rutas rotas (recomendado, coherente con el brief).
- Cómo se mide "git status limpio" mientras haya cambios propios sin confirmar (antes/después de la suite).
- Preguntas 1 a 6 de la spec: aceptables, con recomendación incluida. La 1 sigue abierta y la prueba de clon depende de ella.

Límite conocido (no es hallazgo): la constitución §16 pide README actualizado al cerrar. T132 solo actualiza `CODEMAP.md` porque el README final es de `readme-video`.

Sin hallazgos en el resto: cobertura (15 tareas T118–T132 en 4 bloques; los 90 [OBL] cubiertos por T118–T120), contratos y alcance protegido, constitución (§13, §15, §16, §18, §19, §20), paradas P1/P2 y salida de los tests.
