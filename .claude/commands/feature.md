---
description: Ejecuta UNA fase de una feature de Spec Kit (diseno | implementar | cierre) en modo ágil, con subagentes; se detiene al acabar la fase
argument-hint: <nombre-feature> <diseno|implementar|cierre> [brief o indicaciones]
---

Eres el ORQUESTADOR. Argumentos: $ARGUMENTS

Formato: `<nombre-feature> <fase> [texto]`. Fases: `diseno`, `implementar`, `cierre`. Si falta la fase o no es válida, NO hagas nada y pregunta. El texto adicional es el brief en `diseno`; en `implementar` y `cierre` son indicaciones del alumno (límite de bloques como `hasta bloque 3`, o ajustes a documentos que aplicas ANTES de empezar, nunca a contratos).

## Reglas

1. **Una fase y te detienes**, con el resumen final. (Si te invoca `/sprint`, es `/sprint` quien decide si se continúa.)
2. **Rama.** `diseno` crea `NNN-<feature>` con `git switch -c` (siguiente número libre) desde `main`, o desde la rama de la feature anterior si el alumno lo indica. Es la única operación de rama permitida. En `implementar` y `cierre` comprueba con `git branch --show-current` que estás en la rama de la feature; si no, PARA. Nunca `merge`, `push`, `rebase`, `reset`, `stash` ni cambiar de rama. Los `commit` los hace el alumno, salvo que `/sprint` te los autorice expresamente.
3. **No redactas ni programas**: delegas por su nombre en `disenador`, `plan-reviewer`, `corrector`, `implementador`, `verificador` y `doc-keeper` (`.claude/agents/`). Si falta uno, PARA. Tus únicas escrituras: `bitacora.md` y guardar tal cual (sin editar) los informes de `plan-reviewer`.
4. **El estado vive en archivos** (`specs/<NNN-feature>/`, `docs/evidencias/<feature>/`). Pasa a cada subagente rutas y objetivo, no resúmenes tuyos. **En cada prompt incluye**: nombre y carpeta de la feature, los IDs del checklist (fila de la feature en `docs/planificacion/03-procedimiento-ejecucion.md` §4), el criterio de proporcionalidad y las rutas a leer (`.specify/memory/constitution.md`, `CLAUDE.md`, contratos pertinentes).
5. Los subagentes no invocan slash commands: dales la orden de leer `.claude/skills/speckit-<paso>/SKILL.md` y seguirla.
6. Prohibido: tocar `docs/enunciado/`, modificar contratos de `specs/001-contratos-y-modelo/contracts/` o `sql/001_schema.sql`, secretos en el repo, y cualquier atribución a Claude (Co-Authored-By, "Generated with…").
7. **Economía.** Cada llamada a un subagente cuesta tokens. Una revisión por fase, una ronda de corrección, sin repetir por sistema.

## Proporcionalidad (pégalo literal en el prompt de revisores y verificadores)

Trabajo de clase de unas 2 semanas, no producción. Es **bloqueante o importante** solo lo que: haría fallar una prueba de aceptación o un requisito obligatorio del checklist; contradice un contrato o la constitución; pierde o duplica datos, o bloquea el consumo, con datos que USGS puede enviar de verdad; o deja una decisión que el alumno no podría explicar en el README o en el vídeo. Todo lo demás es **menor**: NO se lista en el informe ni se corrige; como mucho, una línea de "límite conocido". No añadas requisitos para casos imaginarios. Cada hallazgo importante lleva: qué falla, un ejemplo concreto y qué prueba o requisito afecta; sin ejemplo, no se reporta. **El informe ocupa como máximo 15 líneas.**

## Escalar (PARA y devuelve la pregunta con tu recomendación)

Cambio de contrato o de alcance; decisión no justificable con la constitución, el enunciado o los contratos; secreto u operación destructiva no autorizada; un bloqueante abierto tras la ronda de corrección; una tarea sin verificar tras 2 vueltas. Las decisiones discutibles NO paran: se adoptan como provisionales y se reportan en el resumen.

## Bitácora

`specs/<NNN-feature>/bitacora.md`, una fila por paso (no por iteración): fase | paso | hallazgos | corrección | estado. Solo se añade.

---

## FASE `diseno`

**0. Preflight.** *Reanudación:* si ya estás en la rama de la feature y la bitácora tiene `diseno` sin cerrar, no crees rama ni exijas árbol limpio; retoma en el primer paso no cerrado e incorpora como decididas las indicaciones del alumno. *Inicio:* `git status` limpio (si no, PARA y dilo); crea la rama.

**1. Redacción en DOS llamadas a `disenador`:** (A) specify + clarify; (B) plan + tasks + analyze.
- `clarify`: responde con la opción recomendada; lo que toque contratos o alcance, o no se justifique, va a "Preguntas para el alumno" con decisión provisional.
- `plan`: solo documentos de diseño; nada de código ni compose (constitución §19).
- `tasks`: respeta el **tope de tareas del brief** (por defecto, máximo 25 activas), sin fuzz ni pruebas exhaustivas ni auditorías; cada tarea con su prueba y los IDs que cubre; agrúpalas en un máximo de 5 bloques.
- `analyze`: corrige él mismo los hallazgos importantes de texto y trazabilidad.

**2. UNA revisión.** Antes, ejecuta tú `git diff --stat -- specs/001-contratos-y-modelo/contracts/ docs/enunciado/ sql/001_schema.sql` y pásale el resultado (no vacío = bloqueante). Lanza `plan-reviewer` una vez sobre todos los archivos de la feature, con el criterio de proporcionalidad pegado y este foco: cada requisito del brief y del checklist tiene tarea y prueba; coherencia spec ↔ plan ↔ tasks; constitución (cítala); nada fuera de alcance. Guarda su informe tal cual en `docs/evidencias/subagentes/plan-reviewer-<feature>.md`.

**3. UNA ronda de corrección.** Si hay bloqueantes o importantes: `corrector` una vez. Sin segunda revisión (el `verificador` lo cazará en la implementación). Lo que quede, a "pendientes" del resumen.

**4. STOP.** Sin código. Resumen final.

## FASE `implementar`

**0. Preflight.** Rama de la feature; existen `spec.md`, `plan.md`, `tasks.md` y `diseno` cerrada en la bitácora; si no, PARA. Aplica las indicaciones del alumno sobre `tasks.md`.

**1. Bloques.** Toma las tareas `- [ ]` (ignora `- [x]` y `- [-]`) en los bloques de `tasks.md` (máximo 5; fusiona si hay más). Si hay límite (`hasta bloque N`), para tras ese bloque, nunca a mitad. Para cada bloque:
- a) `implementador`: código, pruebas y evidencia en `docs/evidencias/<feature>/`; actualiza `CODEMAP.md`; no marca nada.
- b) `verificador` (invocación nueva, criterio de proporcionalidad pegado), **verificación escalonada**: `pytest -x -q` solo del bloque y suite rápida, sin Docker salvo que la tarea lo exija; stack levantado una vez y reutilizado, sin `down -v` ni `--build` salvo cambio de Dockerfile o dependencias; `TRUNCATE` entre tests; recorrido completo con contenedores solo en el último bloque.
- c) Si falla: `corrector` y vuelta a (b), máximo 2 vueltas. Si una tarea sigue sin verificarse, PARA y escala.
- d) Marca `[x]` solo lo verificado con una prueba real.

**2. STOP.** Resumen final.

## FASE `cierre`

**0. Preflight.** Rama de la feature y tareas activas verificadas; si no, PARA. Aplica las indicaciones del alumno.

**1.** Ejecuta tú `git diff --stat` de contratos (vacío esperado). Lanza **solo `doc-keeper`**: CODEMAP, README, `docs/borradores/<feature>.md` (material para el README y el vídeo, breve), estado de la spec → Implemented, tareas diferidas marcadas "Diferido" en la spec con su motivo, fila del histórico y rutas de evidencias. No hay segunda revisión: la implementación ya la verificó el `verificador`.

**2. STOP.** Sin commit ni merge. Dile al alumno los IDs del checklist a marcar (solo los que tienen evidencia) y un mensaje de commit sugerido sin atribución.

---

## Resumen final (máximo 30 líneas)

- **a) Decisiones por defecto**: `pregunta | decisión | motivo | ¿defenderla?`.
- **b) Preguntas para el alumno**, con tu recomendación.
- **c) Hallazgos importantes**, explicados en lenguaje llano (qué falla, ejemplo, qué prueba afecta); menores: solo cuántos hay.
- **d) Tareas**: verificadas / pendientes / diferidas, con evidencia clave.
- **e) Qué debe comprobar el alumno**, y en `cierre` los IDs del checklist y el mensaje de commit.
- Última línea: "Fase terminada."
