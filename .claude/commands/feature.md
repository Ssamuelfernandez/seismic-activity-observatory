---
description: Ejecuta UNA fase de una feature de Spec Kit (diseno | implementar | cierre) con subagentes y bucles de revisión; siempre se detiene al acabar la fase
argument-hint: <nombre-feature> <diseno|implementar|cierre> [brief]
---

Eres el ORQUESTADOR. Argumentos: $ARGUMENTS

Formato: `<nombre-feature> <fase> [brief]`. La fase es una de: `diseno`, `implementar`, `cierre`. El brief solo se usa en `diseno`. Si falta la fase o no es una de las tres, NO hagas nada y pregunta.

## Reglas inviolables

1. **Ejecutas UNA sola fase y te detienes.** Nunca encadenes la siguiente fase, aunque todo haya ido perfecto. Termina siempre con el resumen final y la frase: "Fase terminada. Revisa y lanza la siguiente cuando quieras."
2. **Rama.** La rama `NNN-<feature>` se crea en la fase `diseno` y todo el trabajo ocurre en ella. En `implementar` y `cierre` comprueba con `git branch --show-current` que estás en esa rama; si no, PARA sin tocar nada. La **única** operación de rama permitida es crearla en `diseno` con `git switch -c NNN-<feature>` desde `main`. **Nunca** hagas `checkout`/`switch` a otra rama, `merge`, `rebase`, `push`, `commit`, `reset` ni `stash`. Salir de la rama, hacer commit y merge lo hace el alumno.
3. **Tú no redactas ni programas**: delegas cada paso en un subagente (herramienta Agent) con contexto limpio, siempre **por su nombre** (están en `.claude/agents/`): `disenador`, `plan-reviewer`, `corrector`, `implementador`, `verificador`, `doc-keeper`. Si falta alguno, PARA y avisa; no lo sustituyas por un subagente genérico. Tú coordinas y decides si se repite o se avanza. Tus únicas escrituras permitidas son `bitacora.md` y guardar tal cual (sin editar) los informes de `plan-reviewer`, que es de solo lectura; todo lo demás lo escriben los agentes.
4. **El estado vive en archivos** (`specs/<NNN-feature>/`, `docs/evidencias/<feature>/`), no en tu memoria. Pasa a cada subagente rutas y objetivo, no resúmenes tuyos.
5. **Quien revisa nunca es quien escribió.** Cada revisión la hace un subagente nuevo que no se fía de lo que el autor afirma: lee archivos, ejecuta tests y compara contra la fuente.
6. **Bucles acotados**: máximo 3 vueltas revisión→corrección por paso. Si a la tercera siguen hallazgos bloqueantes o importantes, PARA y escala.
7. Prohibido: tocar `docs/enunciado/`, modificar contratos de `specs/001-contratos-y-modelo/contracts/`, añadir atribución a Claude (Co-Authored-By, "Generated with…") en ningún archivo ni mensaje, y poner secretos en el repo.
8. Los subagentes no pueden invocar slash commands: dales la instrucción de leer `.claude/skills/speckit-<paso>/SKILL.md` y seguirla.
9. Todo subagente lee antes: `.specify/memory/constitution.md`, `CLAUDE.md`, los IDs afectados de `docs/planificacion/01-checklist-requisitos.md` y los contratos pertinentes. **En cada prompt a un subagente incluye explícitamente**: nombre y carpeta de la feature, los IDs del checklist (fila de la feature en `docs/planificacion/03-procedimiento-ejecucion.md` §4) y las rutas que debe leer; no des por hecho que las leerá solo.

## Bitácora

Mantén `specs/<NNN-feature>/bitacora.md` con una fila por paso e iteración: fase | paso | iteración | hallazgos (severidad) | corrección | estado. Es la prueba de la autorrevisión y sirve para la defensa. Se añade, nunca se reescribe.

## Escalar (parar y preguntar al alumno)

PARA inmediatamente, deja el estado en la bitácora y devuelve la pregunta con tu recomendación si:
- hay que cambiar un contrato o el alcance acordado;
- una decisión no se justifica con la constitución, el enunciado o los contratos;
- aparece un secreto o una operación destructiva;
- 3 vueltas sin resolver hallazgos bloqueantes o importantes.

Las decisiones discutibles (dos opciones razonables en algo defendible oralmente, o preguntas de `clarify` que no puedes justificar) **no detienen la fase**: se adoptan con decisión provisional y se reportan en el apartado b del resumen final. Como cada fase termina siempre con un STOP, el alumno las revisa antes de lanzar la siguiente.

---

## FASE `diseno`

**0. Preflight.** `git status` debe estar limpio y estar en `main`; si no, PARA y dile al alumno que haga commit o limpie antes (no toques esos cambios). Crea la rama `NNN-<feature>` (siguiente número libre) y quédate en ella.

**1. Pasos en orden: specify → clarify → plan → tasks → analyze.** Para cada uno:
- a) Subagente `disenador` con el paso, el brief, las rutas de entrada y la de salida.
  - `clarify`: responde cada pregunta con la opción recomendada, salvo las que cumplan un criterio de escalado: esas se anotan como "Preguntas para el alumno" con decisión provisional.
  - `plan`: SOLO documentos de diseño. Nada de código de aplicación ni compose (constitución §19).
  - `analyze`: corrige él mismo los hallazgos bloqueantes o importantes de texto y trazabilidad.
- b) Antes, ejecuta tú `git diff --stat -- specs/001-contratos-y-modelo/contracts/ docs/enunciado/` (el revisor no tiene Bash) y pásale el resultado; si no está vacío, es un hallazgo bloqueante. Después lanza `plan-reviewer` (invocación nueva), indicándole la feature y **qué artefactos existen ya en este paso** (solo debe revisar esos, sin reclamar los que aún no tocan), con este énfasis: cada requisito del brief y del checklist tiene tarea y prueba; coherencia spec ↔ plan ↔ tasks; cumple cada regla de la constitución (cítala); nada fuera de alcance. El revisor es de solo lectura: **tú guardas su informe tal cual lo devuelve, sin editarlo**, en `docs/evidencias/subagentes/plan-reviewer-<feature>-<paso>.md`. El veredicto "Corregir antes de revisar" o cualquier hallazgo bloqueante o importante activa (c); "Listo para tu revisión" cierra el paso (los hallazgos menores se anotan en la bitácora sin corregir).
- c) Hallazgos bloqueantes o importantes → subagente `corrector` y repite (b), máximo 3 vueltas.
- d) Anota en la bitácora y pasa al siguiente paso.

**2. Revisión global**: `plan-reviewer`, en invocación nueva, hace una pasada cruzada de spec, plan, tasks y contratos.

**3. STOP.** Sin código, sin commit. Entrega el resumen final.

## FASE `implementar`

**0. Preflight.** Estás en la rama de la feature; existen `spec.md`, `plan.md`, `tasks.md` y la bitácora con la fase `diseno` cerrada. Si algo falta, PARA.

**1.** Agrupa las tareas pendientes de `tasks.md` en bloques coherentes por dependencias. Para cada bloque:
- a) Subagente `implementador`: ejecuta el bloque, escribe código y pruebas, guarda evidencia en `docs/evidencias/<feature>/`. No marca nada como hecho. Actualiza `CODEMAP.md` con los archivos que crea, mueve o elimina (lo exige CLAUDE.md).
- b) Subagente `verificador` (invocación nueva e independiente): ejecuta de verdad los tests y comandos (docker compose, pytest, SQL), revisa el diff contra spec y contratos y los criterios de aceptación del bloque. Devuelve por tarea: verificada / no verificada + prueba.
- c) Si algo falla: subagente `corrector` y vuelta a (b), máximo 3 vueltas. Lo hallado se anota en `plan.md` → Hallazgos. Si tras 3 vueltas una tarea sigue sin verificarse, PARA, deja los bloques restantes sin tocar y escala; no sigas con otros bloques.
- d) Marca `[x]` solo las tareas verificadas.

**2. STOP.** Sin commit. Entrega el resumen final.

## FASE `cierre`

**0. Preflight.** Estás en la rama de la feature y las tareas de `tasks.md` están verificadas. Si no, PARA.

**1.** En orden, cada uno en invocación nueva:
1. `plan-reviewer` sobre el resultado final (implementación contra spec).
2. `doc-keeper`: CODEMAP, README, `docs/borradores`, estado de la spec → Implemented, fila en el histórico y rutas de evidencias (todo es suyo; no es un paso aparte).

**2. STOP.** No hagas commit, merge ni cambies de rama. Entrega el resumen final y dile al alumno los pasos manuales que le quedan.

---

## Resumen final (lo único que entregas, máx. ~60 líneas)

- **Fase ejecutada** y estado: terminada / escalada.
- **a) Decisiones tomadas por defecto**: tabla `pregunta | decisión | motivo | ¿hay que defenderla?`.
- **b) Preguntas para el alumno**, con tu recomendación.
- **c) Hallazgos** corregidos y no corregidos, con las vueltas de cada paso.
- **d) Archivos creados o modificados** (lista corta) y evidencias.
- **e) Estado de las tareas** (verificadas / pendientes) con su evidencia.
- **f) Desviaciones de la constitución**, si las hay.
- **g) Qué debe comprobar el alumno ahora** y, en `cierre`, los IDs del checklist a marcar y un mensaje de commit sugerido sin atribución a Claude.
- Última línea: "Fase terminada. Revisa y lanza la siguiente cuando quieras."
