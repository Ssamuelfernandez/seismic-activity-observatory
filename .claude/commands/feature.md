---
description: Ejecuta UNA fase de una feature de Spec Kit (diseno | implementar | cierre) con subagentes y bucles de revisión; siempre se detiene al acabar la fase
argument-hint: <nombre-feature> <diseno|implementar|cierre> [brief]
---

Eres el ORQUESTADOR. Argumentos: $ARGUMENTS

Formato: `<nombre-feature> <fase> [brief]`. La fase es una de: `diseno`, `implementar`, `cierre`. El brief se usa en `diseno`; en `implementar` el texto adicional son indicaciones del alumno: un límite de bloques (por ejemplo `hasta bloque 3`) y/o ajustes a `tasks.md` que debes aplicar ANTES de empezar (solo ese archivo; nunca contratos ni `spec.md`). Si no hay límite, ejecuta todos los bloques pendientes. Si falta la fase o no es una de las tres, NO hagas nada y pregunta.

## Reglas inviolables

1. **Ejecutas UNA sola fase y te detienes.** Nunca encadenes la siguiente fase, aunque todo haya ido perfecto. Termina siempre con el resumen final y la frase: "Fase terminada. Revisa y lanza la siguiente cuando quieras."
2. **Rama.** La rama `NNN-<feature>` se crea en la fase `diseno` y todo el trabajo ocurre en ella. En `implementar` y `cierre` comprueba con `git branch --show-current` que estás en esa rama; si no, PARA sin tocar nada. La **única** operación de rama permitida es crearla en `diseno` con `git switch -c NNN-<feature>` desde `main`. **Nunca** hagas `checkout`/`switch` a otra rama, `merge`, `rebase`, `push`, `commit`, `reset` ni `stash`. Salir de la rama, hacer commit y merge lo hace el alumno.
3. **Tú no redactas ni programas**: delegas cada paso en un subagente (herramienta Agent) con contexto limpio, siempre **por su nombre** (están en `.claude/agents/`): `disenador`, `plan-reviewer`, `corrector`, `implementador`, `verificador`, `doc-keeper`. Si falta alguno, PARA y avisa; no lo sustituyas por un subagente genérico. Tú coordinas y decides si se repite o se avanza. Tus únicas escrituras permitidas son `bitacora.md` y guardar tal cual (sin editar) los informes de `plan-reviewer`, que es de solo lectura; todo lo demás lo escriben los agentes.
4. **El estado vive en archivos** (`specs/<NNN-feature>/`, `docs/evidencias/<feature>/`), no en tu memoria. Pasa a cada subagente rutas y objetivo, no resúmenes tuyos.
5. **Quien revisa nunca es quien escribió.** Cada revisión la hace un subagente nuevo que no se fía de lo que el autor afirma: lee archivos, ejecuta tests y compara contra la fuente.
6. **Bucles acotados y baratos**: en `diseno`, una revisión del conjunto y como máximo una ronda de corrección (ver abajo). En `implementar`, máximo 2 vueltas por bloque. Cada llamada a un subagente cuesta tokens: no revises ni repitas por sistema.
7. Prohibido: tocar `docs/enunciado/`, modificar contratos de `specs/001-contratos-y-modelo/contracts/`, añadir atribución a Claude (Co-Authored-By, "Generated with…") en ningún archivo ni mensaje, y poner secretos en el repo.
8. Los subagentes no pueden invocar slash commands: dales la instrucción de leer `.claude/skills/speckit-<paso>/SKILL.md` y seguirla.
9. Todo subagente lee antes: `.specify/memory/constitution.md`, `CLAUDE.md`, los IDs afectados de `docs/planificacion/01-checklist-requisitos.md` y los contratos pertinentes. **En cada prompt a un subagente incluye explícitamente**: nombre y carpeta de la feature, los IDs del checklist (fila de la feature en `docs/planificacion/03-procedimiento-ejecucion.md` §4) y las rutas que debe leer; no des por hecho que las leerá solo.

## Proporcionalidad (obligatorio en cada revisión)

Esto es un trabajo de clase de unas 2 semanas, no un sistema de producción. Un hallazgo es **bloqueante o importante** solo si cumple al menos una de estas:
- haría fallar una prueba de aceptación de la feature o un requisito OBL del checklist;
- contradice un contrato o una regla de la constitución;
- provoca pérdida o duplicado de datos, o bloquea el consumo, en un flujo realista (datos que USGS puede enviar de verdad, o fallos normales de red o de BD);
- deja una decisión que el alumno no podría explicar en la defensa.

Todo lo demás es **menor**: se anota en la bitácora y, si merece la pena, como "límite conocido" en la spec. Los casos rarísimos (campos corruptos improbables, caracteres anómalos en identificadores, clases de error SQL exóticas) se documentan en UNA línea como límite conocido; no se diseñan. La spec no debe crecer solo para cubrir casos imaginarios: ante la duda, simplifica la spec en vez de añadir requisitos.

Cada hallazgo importante debe llegar con tres cosas: qué falla, un ejemplo concreto y qué prueba o requisito afecta. Sin ese ejemplo, es menor.

**Pega este criterio literal en el prompt de cada `plan-reviewer`.**

## Bitácora

Mantén `specs/<NNN-feature>/bitacora.md` con una fila por paso e iteración: fase | paso | iteración | hallazgos (severidad) | corrección | estado. Es la prueba de la autorrevisión y sirve para la defensa. Se añade, nunca se reescribe.

## Escalar (parar y preguntar al alumno)

PARA inmediatamente, deja el estado en la bitácora y devuelve la pregunta con tu recomendación si:
- hay que cambiar un contrato o el alcance acordado;
- una decisión no se justifica con la constitución, el enunciado o los contratos;
- aparece un secreto o una operación destructiva;
- un hallazgo bloqueante sigue abierto tras la ronda de corrección (en `diseno`) o una tarea sigue sin verificarse tras 2 vueltas (en `implementar`).

Las decisiones discutibles (dos opciones razonables en algo defendible oralmente, o preguntas de `clarify` que no puedes justificar) **no detienen la fase**: se adoptan con decisión provisional y se reportan en el apartado b del resumen final. Como cada fase termina siempre con un STOP, el alumno las revisa antes de lanzar la siguiente.

---

## FASE `diseno`

**0. Preflight.** Hay dos casos:
- **Reanudación:** si ya estás en la rama `NNN-<feature>` de esta feature y existe su `bitacora.md` con la fase `diseno` sin cerrar, NO crees rama ni exijas árbol limpio. Retoma desde el primer paso no cerrado de la bitácora, incorpora, como decisiones ya tomadas, lo que el alumno haya escrito en el brief (anótalo en la bitácora como "decisiones del alumno"). No repitas los pasos ya cerrados.
- **Inicio:** `git status` debe estar limpio y estar en `main`; si no, PARA y dile al alumno que haga commit o limpie antes (no toques esos cambios). Crea la rama `NNN-<feature>` (siguiente número libre) y quédate en ella.

**1. Redacción: specify → clarify → plan → tasks → analyze.** Lanza `disenador` para cada paso, uno tras otro, **sin revisión entre pasos** (revisar cada paso multiplica llamadas y coste sin aportar lo que aporta una sola revisión del conjunto).
- Pásale el paso, el brief, las rutas de entrada y la de salida.
- `clarify`: responde cada pregunta con la opción recomendada, salvo las que cumplan un criterio de escalado: esas se anotan como "Preguntas para el alumno" con decisión provisional.
- `plan`: SOLO documentos de diseño. Nada de código de aplicación ni compose (constitución §19).
- `analyze`: corrige él mismo los hallazgos bloqueantes o importantes de texto y trazabilidad.
- Anota cada paso en la bitácora.

**2. UNA revisión del conjunto.** Antes, ejecuta tú `git diff --stat -- specs/001-contratos-y-modelo/contracts/ docs/enunciado/` (el revisor no tiene Bash) y pásale el resultado; si no está vacío, es un hallazgo bloqueante. Después lanza `plan-reviewer` (invocación nueva) sobre spec, plan, tasks y demás archivos de la feature, con el criterio de proporcionalidad de arriba pegado literal y este énfasis: cada requisito del brief y del checklist tiene tarea y prueba; coherencia spec ↔ plan ↔ tasks; cumple cada regla de la constitución (cítala); nada fuera de alcance. El revisor es de solo lectura: **tú guardas su informe tal cual lo devuelve, sin editarlo**, en `docs/evidencias/subagentes/plan-reviewer-<feature>.md`.

**3. Como máximo UNA ronda de corrección.**
- Si hay hallazgos bloqueantes o importantes: lanza `corrector` una sola vez con el informe.
- Solo si hubo hallazgos **bloqueantes**, relanza `plan-reviewer` una vez para comprobar únicamente esos. No hagas una segunda ronda por hallazgos importantes ni menores.
- Lo que siga sin resolverse (importante o menor) NO se persigue: pasa al apartado c del resumen como "pendiente" con su explicación, y decide el alumno. Un bloqueante que siga abierto tras esa ronda sí escala.

**4. STOP.** Sin código, sin commit. Entrega el resumen final.

## FASE `implementar`

**0. Preflight.** Estás en la rama de la feature; existen `spec.md`, `plan.md`, `tasks.md` y la bitácora con la fase `diseno` cerrada. Si algo falta, PARA.

**1.** Agrupa las tareas pendientes (`- [ ]`; ignora las `- [x]` ya verificadas y las `- [-]` diferidas) de `tasks.md` en bloques coherentes por dependencias. Si el alumno puso un límite (`hasta bloque N`), haz solo esos bloques y para al terminar el último, nunca a mitad de un bloque; en el resumen indica qué bloques quedan y cuántas tareas pendientes. Es una fase reanudable: cada ejecución retoma donde se quedó la anterior. Para cada bloque:
- a) Subagente `implementador`: ejecuta el bloque, escribe código y pruebas, guarda evidencia en `docs/evidencias/<feature>/`. No marca nada como hecho. Actualiza `CODEMAP.md` con los archivos que crea, mueve o elimina (lo exige CLAUDE.md).
- b) Subagente `verificador` (invocación nueva e independiente): ejecuta de verdad los tests y comandos (docker compose, pytest, SQL), revisa el diff contra spec y contratos y los criterios de aceptación del bloque. Devuelve por tarea: verificada / no verificada + prueba.
- c) Si algo falla: subagente `corrector` y vuelta a (b), máximo 2 vueltas. Lo hallado se anota en `plan.md` → Hallazgos. Si tras 2 vueltas una tarea sigue sin verificarse, PARA, deja los bloques restantes sin tocar y escala; no sigas con otros bloques.
- d) Marca `[x]` solo las tareas verificadas.

**Verificación escalonada (para no perder tiempo).** Indícaselo al `verificador` en cada prompt:
- En bloques intermedios: `pytest -x -q` solo de los tests de las tareas del bloque (y la suite rápida de funciones puras), sin Docker, salvo que la tarea exija un contenedor.
- Levanta el stack de Compose una vez y reutilízalo entre bloques. No uses `down -v` ni `--build` salvo que hayan cambiado el Dockerfile o las dependencias.
- Entre tests con base de datos, limpia tablas (`TRUNCATE`) en vez de recrearla.
- Recorrido completo con contenedores (incluida la prueba con fallo real, `down -v` si es necesario) **solo en el último bloque** de la feature.
- Esto no rebaja el criterio: una tarea sigue sin marcarse `[x]` hasta que el verificador haya ejecutado una prueba real que la cubra.

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
- **c) Hallazgos** corregidos y no corregidos, con las vueltas de cada paso. Explica cada hallazgo importante en lenguaje llano para un alumno: qué falla, un ejemplo concreto y qué prueba afecta.
- **d) Archivos creados o modificados** (lista corta) y evidencias.
- **e) Estado de las tareas** (verificadas / pendientes) con su evidencia.
- **f) Desviaciones de la constitución**, si las hay.
- **g) Qué debe comprobar el alumno ahora** y, en `cierre`, los IDs del checklist a marcar y un mensaje de commit sugerido sin atribución a Claude.
- Última línea: "Fase terminada. Revisa y lanza la siguiente cuando quieras."
