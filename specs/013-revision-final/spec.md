# Feature Specification: Revisión final

**Feature Branch**: `013-revision-final` (feature transversal; no tiene fila en `docs/planificacion/03-procedimiento-ejecucion.md` §4)

**Created**: 2026-11-14

**Status**: Implemented (2026-11-15, alcance reducido: solo documentación; 9 tareas activas hechas, 7 diferidas; pendiente de la revisión del alumno)

**Input**: Dejar el repositorio entregable: verificado y ordenado. Límite: 4 bloques de ejecución, un día de trabajo. Lo que no esté en este alcance no se hace.

> **Alcance TOTAL (decisión del alumno, 2026-11-14)**: solo (1) auditoría de lectura (T118 a T120: rúbrica y checklist frente a evidencias; lista los [OBL] sin evidencia; no arregla nada), (2) `CODEMAP.md` al día con el árbol real, (3) limpieza ligera en dos pasos: propuesta de candidatos a mover, renombrar o eliminar con motivo y **PARADA P1** (no se borra ni mueve nada antes de la aprobación), (4) comprobar que `docs/rubrica-y-guia-video.md` está completo y coherente con las evidencias (pruebas 1, 5, 7, 9 y 10 pendientes de captura; comparación ausente en replay) y (5) README final mínimo (a) a (f). **DIFERIDO** (ver «Pendientes no bloqueantes»): clon limpio, `docker compose config`, parada del stack o `cloudflared` (no hay parada P2), suite de integración en carpeta temporal, skip de tests de Netlify, comprobador de enlaces, `docs/README.md` y el resto del bloque de limpieza. Regla: se arregla únicamente lo que deje un [OBL] sin evidencia; el resto va a pendientes no bloqueantes para que decida el alumno. La limpieza (tras P1 y solo si el alumno aprueba) es lo único que puede mover o borrar.

> Contratos de referencia, **sin modificar**: `specs/001-contratos-y-modelo/contracts/` (esta feature no cambia ninguno). `docs/enunciado/`, `sql/001_schema.sql`, la constitución y el checklist no se tocan: **el checklist no se marca**; al final se entrega al alumno una lista de IDs con su estado para que los marque él.

## Cobertura de requisitos

Feature transversal: no tiene fila en §4. Verifica, sin marcar nada, todos los requisitos **[OBL]** de `docs/planificacion/01-checklist-requisitos.md` (bloques A a M y tabla I de pruebas).

| Bloque del alcance | Qué hace | Requisitos que toca | Dónde se comprueba |
|---|---|---|---|
| A. Auditoría | Comprueba que cada [OBL] tiene evidencia existente y versionada | Todos los [OBL] (A1–A11, B1–B17, C1–C14, E1/E2/E4–E6, F1–F10, G1–G9/G13, H1–H5, I 1–11, J1–J7, K1–K7, M1–M5, M10) | US1, FR-001 a FR-004, SC-001 |
| B. Higiene | **DIFERIDO**: suite de integración sin ensuciar el repo; skip de netlify; comprobador de enlaces | M3, M5, M8; Constitución §16 | US2 (diferida), FR-005 a FR-010 (diferidos), SC-002, SC-003 (diferidos) |
| C. Inventario y limpieza (ligera) | Candidatos a mover, renombrar o eliminar con motivo; parada P1; limpieza solo si el alumno aprueba | M5, M6, M8 | US3, FR-011 a FR-015, SC-005 |
| D. Clon limpio | **DIFERIDO**: seguir el README en un clon fuera del proyecto | A2, A10, B17, G0, G13, H2, M3 | US4 (diferida), FR-016 a FR-020 (diferidos), SC-004 (diferido) |
| E. README final, CODEMAP y rúbrica-guía | `CODEMAP.md` al día; comprobación de `docs/rubrica-y-guia-video.md` (solo lectura); `README.md` mínimo: enlace al vídeo (marcador), tabla rúbrica→evidencia, recorrido de un evento, decisión propia, limitaciones, cómo ejecutar | M10, B2, B11, B12, B18, C14, bloque L, D, M6, M8 | US5, FR-021, FR-024, FR-025, SC-006 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auditoría de cumplimiento (Priority: P1)

El alumno (o un revisor) abre `docs/evidencias/revision-final/auditoria.md` y ve, para cada requisito [OBL] del checklist, la evidencia que lo respalda, si cumple, cumple en parte o no, y el hueco con su responsable.

**Why this priority**: es lo que dice qué falta antes de entregar; las demás partes dependen de saberlo.

**Independent Test**: tomar 5 [OBL] al azar del checklist; cada uno aparece en `auditoria.md` con una ruta de evidencia que existe y está versionada (`git ls-files`).

**Acceptance Scenarios**:

1. **Given** el checklist 01, **Then** `auditoria.md` tiene una fila por cada [OBL] con las columnas requisito, evidencia, cumple/parcial/no, hueco y responsable.
2. **Given** una fila «parcial» o «no», **Then** el hueco nombra un responsable: «alumno» o una feature concreta (por ejemplo `013`, tarea del README).
3. **Given** un requisito cuya prueba depende de una acción humana (M4 acceso del profesor, H4 equipo encendido, H5 vídeo, pruebas 9 y 10), **Then** figura con responsable «alumno» y no se da por cumplido.
4. **Given** la auditoría terminada, **Then** el checklist no ha cambiado (`git diff` vacío sobre `01-checklist-requisitos.md`) y se entrega aparte la lista de IDs con estado propuesto.

---

### User Story 2 - Higiene de tests y enlaces (**DIFERIDA**: no entra en el alcance activo; ver «Pendientes no bloqueantes»)

Tras ejecutar los tests, el repositorio queda limpio, y todas las rutas de evidencia citadas en los documentos de entrega existen y están versionadas.

**Why this priority**: un `git status` sucio tras la suite y un enlace roto en el README son lo primero que ve el profesor.

**Independent Test**: ejecutar la suite de integración y `git status`: sin cambios. Ejecutar el comprobador de enlaces: 0 rotos.

**Acceptance Scenarios**:

1. **Given** la suite de integración, **When** termina, **Then** `git status --porcelain` es idéntico antes y después de ejecutar la suite y `git diff --stat -- docs/evidencias` queda vacío (los archivos propios aún sin confirmar no cuentan); nada se escribió en `docs/evidencias/` durante la ejecución (la salida va a una carpeta temporal).
2. **Given** el servicio `tests` sin `netlify.toml` o sin `frontend/.nvmrc` montados, **Then** los 3 tests de `test_netlify_config.py` se saltan (skip) y los unitarios dan 0 fallos.
3. **Given** README, checklist, `docs/rubrica-y-guia-video.md`, `docs/borradores/` y los README de `docs/evidencias/`, **When** se ejecuta el comprobador, **Then** cada ruta de evidencia citada existe y está en `git ls-files`, y el resultado queda en `docs/evidencias/revision-final/enlaces.md` con 0 rotos.
4. **Given** una ruta citada que no existe, **Then** el comprobador la lista con el archivo que la cita y termina con código distinto de cero.

---

### User Story 3 - Inventario y limpieza ligera en dos pasos (Priority: P1)

Primero el alumno recibe un informe de lo dudoso; solo después de aprobarlo expresamente se aplica la limpieza, en un commit aparte y reversible.

**Why this priority**: borrar o mover sin revisión puede perder datos o romper enlaces.

**Independent Test**: `inventario.md` existe y `git status` no muestra borrados ni movimientos antes de la aprobación.

**Acceptance Scenarios**:

1. **Given** los archivos y carpetas dudosos, **Then** `inventario.md` clasifica cada uno en mantener, mover, archivar o borrar, con motivo y con la lista de quién lo referencia (o «nadie»).
2. **Given** el informe, **Then** la feature **se detiene** (punto de aprobación P1) y no borra ni mueve nada hasta que el alumno lo apruebe de forma expresa, ítem por ítem o en bloque.
3. **Given** la aprobación, **Then** solo se aplica lo aprobado, dejado listo para un commit propio reversible con `git revert` (lo hace el alumno o el agente si el alumno lo indica), y las referencias afectadas se corrigen y se comprueban con `grep` y `git ls-files` (el comprobador de enlaces está diferido). Si el alumno no aprueba nada, la limpieza se cierra «sin cambios».
4. **Given** un ítem referenciado por algún documento, **Then** no se propone «borrar» sin proponer a la vez la corrección de la referencia.

---

### User Story 4 - Prueba de clon limpio (**DIFERIDA**: sin clon, sin `docker compose config` y sin parada P2; ver «Pendientes no bloqueantes»)

Se clona el repositorio fuera del proyecto y se sigue el README tal cual; el resultado queda documentado con comandos, tiempos y pass/fail.

**Why this priority**: A2, A10, B17, G0 y M3 exigen que funcione desde un clon limpio; es la prueba más cercana a lo que hará el profesor.

**Independent Test**: leer `clon-limpio.md` y poder repetir cada paso con el comando indicado.

**Acceptance Scenarios**:

1. **Given** el stack del alumno y `cloudflared` en marcha, **Then** antes de empezar el agente **se detiene y pide al alumno que los pare** (punto de aprobación P2) porque los puertos chocarían; no continúa hasta la confirmación.
2. **Given** el clon en una carpeta fuera del proyecto, **Then** se ejecutan, tal cual el README: build y arranque, carga del catálogo e histórico (o su muestra reducida, declarando cuál), comprobación de `/api/salud`, build del panel y tests.
3. **Given** un paso del README que falla por un error del texto (comando equivocado, dato que falta), **Then** se corrige solo la documentación y se repite el paso.
4. **Given** un paso que falla por un error del código, **Then** se reporta en `clon-limpio.md` y en el resumen, y no se toca el código.
5. **Given** el final de la prueba, **Then** `clon-limpio.md` recoge los comandos, el tiempo de cada paso y un resultado global pass o fail; el clon se elimina y el alumno puede volver a levantar su stack.

---

### User Story 5 - README final mínimo (Priority: P1)

Quien abre el repositorio encuentra en `README.md` lo necesario para evaluarlo sin leer nada más: dónde está el vídeo, qué evidencia respalda cada criterio de la rúbrica, un evento seguido de punta a punta, una decisión propia, los límites conocidos y cómo ejecutarlo.

**Independent Test**: el README contiene las seis partes (a) a (f) de FR-021 y cada ruta de la tabla existe y está versionada (comprobación manual con `ls` y `git ls-files`; el comprobador automático está diferido).

**Acceptance Scenarios**:

1. **Given** el README, **Then** arriba figura el enlace al vídeo con el marcador visible «PENDIENTE: enlace de YouTube», que rellenará el alumno (H5 sigue como «parcial», responsable «alumno»).
2. **Given** la auditoría terminada (T120), **Then** la tabla rúbrica→evidencia (M10) tiene una fila por criterio (Extracción, Calidad, Modelado, Análisis, Reflexión) con rutas de evidencia reales y su estado según `auditoria.md`; lo «parcial» se dice como parcial.
3. **Given** el recorrido, **Then** sigue un evento con un `event_id` real citado de una evidencia versionada (`us6000pms8`, de `docs/evidencias/replay/T053_*`) por productor, Kafka, consumidor, base de datos, API y panel, sin cifras inventadas.
4. **Given** las limitaciones, **Then** constan: sin comparación en replay, comparación siempre últimas 24 h frente a la media de 2025, periodo reciente posiblemente incompleto, `tracemalloc` como medida de memoria, mediciones dentro de la VM de Docker y error 500 sin cabeceras CORS.
5. **Given** el estado de features, **Then** ya no figura «Pendiente» ni «en curso» para esta feature ni para `readme-video`, y no queda ninguna referencia a `memoria-defensa (017)` en `README.md` (solo `README.md`; `.claude/` queda fuera de esta feature).
6. **Given** `docs/rubrica-y-guia-video.md`, **Then** está completo y coherente con las evidencias: cada criterio y cada prueba citada apunta a una evidencia real y versionada, las pruebas 1, 5, 7, 9 y 10 figuran como pendientes de captura y la comparación figura como ausente en replay; el resultado queda en `docs/evidencias/revision-final/rubrica-guia.md`. Solo se corrige en el documento lo que deje un [OBL] sin evidencia; el resto se anota en pendientes no bloqueantes.

---

### Puntos de aprobación y fases

La feature se ejecuta en fases con parada y revisión entre ellas.

| Punto | Cuándo | Qué se necesita |
|---|---|---|
| Parada tras cada bloque | Al terminar cada bloque de ejecución | El agente se detiene y espera la revisión del alumno (constitución §19) |
| **P1** Aprobación de limpieza | Tras entregar `inventario.md` | Aprobación expresa del alumno antes de borrar o mover nada |
| ~~P2~~ Parada del stack | **DIFERIDO** (no hay clon limpio; el agente no para el stack ni `cloudflared`) | No aplica |
| P3 Commit | Cada bloque, cuando el alumno lo indique | El agente no hace commit ni merge por su cuenta; los commits no llevan trailers de atribución |

## Edge Cases

> Los casos de borde del comprobador de enlaces, del clon limpio, de puertos y de la suite de integración quedan **diferidos** con sus historias; solo aplican los de auditoría y evidencia pendiente.

- **Evidencia versionada pero vacía o plantilla**: las plantillas pendientes del alumno (capturas 1, 3, 5, 7 y pruebas 9 y 10) existen y están versionadas, pero la evidencia es parcial; la auditoría las marca «parcial» con responsable «alumno», no «cumple».
- **Rutas con formato distinto**: el comprobador acepta rutas entre comillas inversas y enlaces Markdown relativos; ignora URLs externas (`http…`) y rutas de ejemplo en bloques de código.
- **Evidencia no versionada**: un archivo que existe en disco pero no está en `git ls-files` cuenta como roto.
- *(Diferido con US4)* **Clon desde un estado sin confirmar**: el clon solo contiene lo que está en Git; si el alumno no ha confirmado los cambios previos, el clon no los refleja (ver pregunta 1).
- *(Diferido con US4)* **`.env` ausente en el clon**: el README debe decir copiar `.env.example`; si no lo dice, es un fallo de documentación (se corrige).
- *(Diferido con US4)* **Puertos ocupados**: no se ejecuta clon, así que no se toca el stack del alumno (P2 diferida).
- *(Diferido con US4)* **Histórico completo lento**: si la carga completa es demasiado larga para un día, se usa la muestra reducida y se declara en `clon-limpio.md`.
- **Suite de integración durante el stack en marcha**: usa su propia base temporal; la comprobación de limpieza es solo sobre `git status`.

## Límites conocidos

- Es un trabajo de clase: se verifica por muestreo razonable de rutas y comandos, no se audita el contenido de cada evidencia línea a línea.
- La auditoría comprueba que la evidencia existe y es coherente con el requisito; no sustituye la revisión del alumno ni marca el checklist.
- Lo que depende del alumno (vídeo, acceso del profesor, túnel real, capturas del panel público) se señala, no se ejecuta.

## Requirements *(mandatory)*

### Functional Requirements

**A. Auditoría (solo lectura)**

- **FR-001**: Se produce `docs/evidencias/revision-final/auditoria.md` con una fila por cada requisito [OBL] del checklist 01: requisito (ID) → evidencia (ruta) → cumple / parcial / no → hueco → responsable.
- **FR-002**: Cada ruta de evidencia citada existe y aparece en `git ls-files`; si no, el requisito no puede figurar como «cumple».
- **FR-003**: Cada hueco tiene un responsable: «alumno» o el nombre de una feature (por ejemplo `013`, tarea del README, para el texto de B2, B11, B12, B18, M10, bloque L, D y C14).
- **FR-004**: La auditoría no corrige nada y no modifica el checklist; entrega aparte una lista de IDs con estado propuesto para que el alumno los marque. Se hace con el agente verificador.

**B. Higiene de tests y enlaces (DIFERIDO: FR-005 a FR-010 no se ejecutan; ver «Pendientes no bloqueantes»)**

- **FR-005**: La suite de integración escribe sus evidencias en una carpeta temporal fuera de `docs/evidencias/`; tras ejecutarla, `git status` queda limpio. El efecto sobre la evidencia ya versionada se documenta.
- **FR-006**: Los 3 tests de `tests/scripts/test_netlify_config.py` se saltan (skip) con motivo explícito si faltan `netlify.toml` o `frontend/.nvmrc` en el servicio `tests`; cuando existen, siguen comprobando lo mismo que antes.
- **FR-007**: Los tests unitarios dan 0 fallos en el servicio `tests`.
- **FR-008**: Se añade un script comprobador de enlaces que verifica que todas las rutas de evidencia citadas en `README.md`, el checklist, `docs/rubrica-y-guia-video.md`, `docs/borradores/` y los README de `docs/evidencias/` existen y están versionadas.
- **FR-009**: El comprobador escribe su resultado en `docs/evidencias/revision-final/enlaces.md` (rutas comprobadas, rotas, archivo que las cita) y devuelve código distinto de cero si hay alguna rota.
- **FR-010**: Los cambios de código de esta feature se limitan a la ruta de salida de las evidencias de tests, los skip de netlify y el script comprobador; ninguna funcionalidad nueva, refactor ni actualización de dependencias.

**C. Inventario y limpieza ligera**

- **FR-011**: Se produce `docs/evidencias/revision-final/inventario.md` que clasifica cada archivo o carpeta dudosa en mantener / mover / archivar / borrar, con motivo y con la lista de quién lo referencia.
- **FR-012**: El criterio de «dudoso» es: archivos en la raíz o fuera de su carpeta de servicio, ficheros generados o regenerables que estén en Git, duplicados, restos de pruebas o de la herramienta, y cualquier cosa que el alumno no sepa explicar al abrir el repositorio.
- **FR-013**: **Hasta la aprobación expresa del alumno (P1) no se borra ni se mueve nada.**
- **FR-014**: La limpieza aprobada (solo si el alumno aprueba) se deja lista para un commit separado y reversible; después se comprueban con `grep` y `git ls-files` las referencias afectadas (el comprobador de enlaces está diferido).
- **FR-015**: (Las referencias rotas que se detecten en esas rutas protegidas solo se anotan, no se editan.) No se mueven ni se borran `docs/planificacion/`, `specs/`, `.specify/`, `.claude/`, `docs/evidencias/`, `docs/borradores/` ni `docs/rubrica-y-guia-video.md`; esos elementos solo se clasifican como «mantener».

**D. Prueba de clon limpio (DIFERIDO: FR-016 a FR-020 no se ejecutan; ver «Pendientes no bloqueantes»)**

- **FR-016**: Antes de clonar, el agente pide al alumno parar su stack y `cloudflared` (P2) y no continúa sin confirmación.
- **FR-017**: El repositorio se clona en una carpeta fuera del proyecto y se siguen los pasos del README tal cual: configuración de `.env`, build y arranque, carga de catálogo e histórico (completo o muestra reducida, declarado), `/api/salud`, build del panel y tests.
- **FR-018**: Se escribe `docs/evidencias/revision-final/clon-limpio.md` con comandos, tiempo de cada paso, salida relevante y resultado global pass o fail.
- **FR-019**: Si un paso falla por la documentación, se corrige solo el texto del README u otro documento y se repite; si falla el código, se reporta sin tocarlo.
- **FR-020**: Al terminar se elimina el clon y se detiene su stack, de modo que el alumno pueda volver a levantar el suyo.

**E. README final mínimo, CODEMAP y rúbrica-guía**

- **FR-021**: `README.md` incluye: (a) enlace al vídeo arriba con el marcador visible «PENDIENTE: enlace de YouTube»; (b) tabla rúbrica→evidencia (M10) basada en `auditoria.md`; (c) recorrido de un evento con un `event_id` real citado de una evidencia versionada; (d) decisión propia; (e) limitaciones conocidas (las de US5.4); (f) cómo ejecutar. Actualiza el estado de features y quita la referencia a `memoria-defensa (017)` / `readme-video` en `README.md` (solo `README.md`; `.claude/` queda fuera). Rellena `docs/borradores/` solo si queda un hueco [OBL] de texto. El mapa `docs/README.md` no se crea (diferido).

**Transversales**

- **FR-022**: No se modifican contratos, `sql/001_schema.sql`, `docs/enunciado/`, la constitución ni el checklist; no se reescriben specs.
- **FR-025**: Se comprueba (solo lectura) que `docs/rubrica-y-guia-video.md` está completo y coherente con las evidencias, con resultado en `docs/evidencias/revision-final/rubrica-guia.md`. Se arregla únicamente lo que deje un [OBL] sin evidencia; el resto va a pendientes no bloqueantes.
- **FR-023**: No entra: guion o vídeo (no hay feature `readme-video`: el enlace lo pone el alumno); funcionalidad nueva, refactors, actualización de dependencias, reformateos masivos y todo lo marcado como diferido.
- **FR-024**: `CODEMAP.md` queda al día con el árbol real del repositorio (rutas comprobadas con `ls` y `git ls-files`) y de nuevo tras cualquier limpieza aprobada. Cierre (constitución §16): evidencia en `docs/evidencias/revision-final/`; esta feature no crea código nuevo. Sin commits ni merges sin aprobación y sin trailers de atribución (constitución §19 y §20).

### Key Entities

- **Requisito auditado**: un ID [OBL] del checklist con evidencia, estado (cumple/parcial/no), hueco y responsable.
- **Ítem del inventario**: archivo o carpeta dudosa con clasificación, motivo y referencias.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `auditoria.md` cubre el 100 % de los [OBL] del checklist; cada hueco «parcial» o «no» tiene responsable; el checklist queda sin cambios (0 líneas modificadas).
- **SC-002** *(Diferido: comprobador de enlaces)*: sin medir en esta feature.
- **SC-003** *(Diferido: higiene de tests)*: sin medir en esta feature. Criterio original: los unitarios dan 0 fallos y, tras ejecutar la suite de integración, `git status --porcelain` es idéntico al de antes de ejecutarla y `git diff --stat -- docs/evidencias` queda vacío (los archivos propios aún sin confirmar no cuentan).
- **SC-004** *(Diferido: clon limpio)*: sin medir en esta feature. Criterio original: `clon-limpio.md` recoge el resultado pass o fail, y el 100 % de los pasos con su comando exacto y su tiempo, repetibles por otra persona.
- **SC-005**: Antes de P1 `git status` no muestra borrados ni movimientos; la limpieza se aplica solo con aprobación expresa registrada en `inventario.md`, dejada para un commit propio, con las referencias afectadas corregidas (`grep`).
- **SC-006**: `README.md` contiene las seis partes de FR-021, la tabla M10 cubre los 5 criterios con todas sus rutas existentes y versionadas (comprobación manual), `docs/rubrica-y-guia-video.md` está comprobado (`rubrica-guia.md`) y `CODEMAP.md` queda al día.
- **SC-007**: El conjunto se completa en un día de trabajo con 9 tareas activas (T118 a T120, T126 a T129, T132 y T133) y 4 bloques de ejecución; 7 tareas diferidas (T121 a T125, T130, T131).

## Assumptions

- Las features 001 a 012 están cerradas y sus evidencias existen; esta feature las verifica, no las rehace.
- El alumno revisa y aprueba al final de cada bloque; la limpieza requiere su respuesta explícita (P1).
- Fuera de alcance: lo listado en FR-023 y todo lo marcado en el brief como «NO ENTRA».

## Clarifications

### Session 2026-11-14

- Q *(histórico, superado por el recorte de alcance del 2026-11-14: ver «Alcance TOTAL» y tasks.md)*: ¿Cómo se agrupan los 5 bloques del brief en 4 bloques de ejecución y 15 tareas? → A: Bloque 1 = A (auditoría, solo lectura); bloque 2 = B + E (higiene de tests, comprobador de enlaces y README final, este último tras la auditoría); bloque 3 = C paso 1 (inventario) y parada P1, y C paso 2 solo tras aprobación; bloque 4 = D (clon limpio) tras P2. Es el reparto que respeta el tope de 4 bloques y deja las paradas obligatorias entre fases; el plan lo concreta en tareas (máximo 15).
- Q *(histórico, superado por el recorte de alcance)*: ¿En qué orden van los bloques? → A: A, B+E, C paso 1, parada P1, C paso 2 (si se aprueba), P2, D. El comprobador de enlaces (B) debe existir antes de la limpieza (comprobar 0 rotos después) y la prueba de clon limpio va al final para probar el repositorio ya limpio.
- Q: ¿Qué se audita en un [OBL] que depende de una acción humana (H4, H5, M4, pruebas 9 y 10)? → A: Se marca «parcial» o «no» con responsable «alumno» y el hueco explica qué falta; nunca «cumple» sin evidencia versionada (constitución §16).
- Q: ¿Cómo se redirige la salida de la suite de integración? → A: A una carpeta temporal por variable de entorno que lee el soporte de evidencias de los tests (el servicio `tests` ya monta la ruta de evidencias en lectura y escritura solo para ese soporte); el valor por defecto en ejecución normal es la carpeta temporal. Los detalles son del plan.
- Q: ¿Los skip de netlify ocultan un problema real? → A: No: el test sigue ejecutándose donde los archivos existen (host o CI con el repositorio completo) y se salta con motivo explícito solo donde el servicio `tests` no los monta. Es un cambio acotado en tests, dentro del alcance B.
- Q: ¿Qué cuenta como «ruta de evidencia citada» para el comprobador? → A: Cualquier ruta relativa al repositorio, entre comillas inversas o en un enlace Markdown, que empiece por una carpeta conocida (`docs/`, `specs/`, `tests/`, `scripts/`, `sql/`, `data/`, `frontend/`, etc.) o sea un archivo de raíz conocido; se ignoran URLs externas y bloques de código de ejemplo. Rutas con comodín se comprueban como patrón con al menos una coincidencia.
- Q: ¿Qué hace el comprobador con enlaces a archivos regenerables que no se versionan a propósito (por ejemplo `data/raw/`)? → A: Se reportan aparte como «no versionada por diseño» si el README la declara regenerable (M5); no cuentan como rotos. Cualquier otra ruta no versionada cuenta como rota.
- Q: ¿Qué es «dudoso» para el inventario? → A: Ver FR-012; el plan lista los candidatos concretos tras mirar el árbol (`git ls-files` y archivos sin versionar). Lo que está bajo las rutas protegidas de FR-015 solo se clasifica «mantener».
- Q: ¿Pasa/falla el clon limpio si la carga del histórico completo se sustituye por la muestra reducida? → A: Pasa, siempre que el README ofrezca la muestra reducida como alternativa documentada y `clon-limpio.md` declare cuál se usó. Si el README no la documenta, es un hueco de documentación que se corrige.
- Q: ¿Se marca el checklist? → A: No; se entrega la lista de IDs con estado propuesto y lo marca el alumno.
- Q: ¿El agente verificador puede corregir? → A: No; la auditoría es solo lectura y los huecos se reportan con responsable. Las correcciones de texto o código fuera de B, D y E quedan para la feature responsable o para el alumno.

### Preguntas para el alumno

Decisiones provisionales; la 2 afecta al alcance. Las preguntas 1, 4, 5 y 6 quedan **diferidas** con el clon limpio, el comprobador y el skip de Netlify.

1. **Estado de lo que se clona (alcance de D)**. Un clon contiene solo lo confirmado en Git, y esta rama tendrá cambios sin confirmar (bloque B, README final). Decisión provisional: confirmar los bloques A a E (con tu aprobación) en la rama `013-revision-final` y clonar esa rama; la prueba de clon limpio va después de la limpieza. Recomendación: esa, para probar exactamente lo que se entrega. Alternativa: clonar `main`, lo que probaría una versión anterior a esta feature.
2. **Alcance de la limpieza frente a la prohibición de mover `docs/evidencias/` y `docs/borradores/`** (FR-015). El brief permite clasificar cualquier cosa «dudosa» pero prohíbe mover esas carpetas. Decisión provisional: esas rutas solo se clasifican «mantener»; si dentro de ellas hay duplicados o restos, se listan en el inventario como «propuesta para tu decisión» sin entrar en la limpieza automática. Recomendación: esa. Alternativa: permitir borrar archivos sueltos dentro de `docs/evidencias/` con tu aprobación ítem a ítem.
3. **Responsable de los huecos de texto de README** (B2, B11, B12, B18, M10, bloque L, D, C14). Decisión (cambio de plan del alumno: no habrá `readme-video`): los resuelve esta feature en la tarea del README final (FR-021). Recomendación: esa; son solo texto.
4. **Comprobador de enlaces y evidencias pendientes del alumno**. Las plantillas «captura_pendiente» y las de pruebas 9 y 10 existen pero no son la captura real. Decisión provisional: el comprobador las da por correctas (el archivo existe y está versionado) y la auditoría las marca «parcial» con responsable «alumno». Recomendación: esa; no confundir enlace roto con evidencia incompleta.
5. **Cómo se hace el skip de netlify**. Decisión provisional: `pytest.mark.skipif` o `pytest.skip` condicionado a la existencia de ambos archivos, con motivo. Recomendación: esa, porque conserva la comprobación en el host. Alternativa: montar los archivos en el servicio `tests` (toca `compose.yaml`, que no entra en el alcance).
6. **Tamaño de la muestra del histórico en el clon**. Decisión provisional: usar lo que el README llame «muestra reducida» y, si no existe, la carga completa solo si cabe en el día; en caso contrario, documentar el hueco. Recomendación: confirmar si prefieres siempre la carga completa aunque tarde.

## Pendientes no bloqueantes

Lo que sigue queda **Diferido** por decisión del alumno (2026-11-14): no se ejecuta en esta feature, no bloquea su cierre y lo decide el alumno más adelante. Solo se arregla lo que deje un [OBL] sin evidencia; lo demás se anota aquí.

| Elemento diferido | Motivo | Antes cubierto por |
|---|---|---|
| Clon limpio en carpeta fuera del proyecto | Alcance reducido a auditoría de lectura, CODEMAP, limpieza ligera, comprobación de rúbrica-guía y README mínimo | US4, FR-016 a FR-020, SC-004, T130, T131 |
| `docker compose config` y parada de stack o `cloudflared` (no hay parada P2) | Dependía del clon limpio; evita tocar el entorno del alumno | FR-016, FR-020, T130, T132 |
| Suite de integración en carpeta temporal (`EVIDENCE_KEEP`) | No se ejecuta suite de integración ni se cambia código de tests | FR-005, SC-003, T121, T124 |
| Skip de los tests de Netlify | Cambio de código de tests fuera del alcance | FR-006, FR-007, T122 |
| Comprobador de enlaces (`scripts/check_links.py`) y su informe `enlaces.md` | No se crea código; la existencia de rutas se comprueba a mano con `ls` y `git ls-files` | FR-008, FR-009, FR-010, SC-002, T123, T125 |
| `docs/README.md` (mapa) | Sustituido por el README final mínimo | FR-021 |
| Resto del bloque de limpieza (todo lo que no sea el inventario, P1 y lo aprobado en P1) | Alcance ligero | FR-011 a FR-015 solo en su parte aprobada |
| Huecos no [OBL] detectados en la auditoría, en la comprobación de `docs/rubrica-y-guia-video.md` o en el inventario | Regla: solo se arregla lo que deje un [OBL] sin evidencia | T118 a T120, T127, T133 |
| `docs/rubrica-y-guia-video.md`: rutas de las pruebas 5 y 7 sin el directorio `geografia-pais/`, prueba 3 sin «captura pendiente», comparación sin la salvedad «ausente en replay», y cifras y frases anteriores al estado final (calidad, tabla M10 del README, numeración 014/017) | Ninguno deja un [OBL] sin evidencia; el detalle está en `docs/evidencias/revision-final/rubrica-guia.md` | T133 |
| Pasar `docs/evidencias/revision-final/calidad-live.md` (C14) y las conclusiones del análisis a `docs/memoria.md` (§4 y §6) | La memoria queda fuera del alcance de la feature; el análisis existe como evidencia | T126 |

## Diferido

Por recorte de alcance del alumno (2026-11-14), las tareas T121 a T125, T130 y T131 (marcadas `- [-]` en `tasks.md`) no se ejecutan en esta feature: no se cambia código, no se ejecuta la suite de integración ni se toca el stack del alumno. No bloquean el cierre y pasan a «Pendientes no bloqueantes» (tabla anterior), a decidir por el alumno.

| Tarea | Qué era | Motivo | Dónde pasa |
|---|---|---|---|
| T121 | Salida de evidencias de los tests a carpeta temporal (`EVIDENCE_KEEP`) | No se cambia código de tests | Pendientes no bloqueantes |
| T122 | Skip de los 3 tests de `test_netlify_config.py` | Cambio de código de tests fuera del alcance | Pendientes no bloqueantes |
| T123 | `scripts/check_links.py` y su test | No se crea código; rutas comprobadas a mano | Pendientes no bloqueantes |
| T124 | Unitarios e integración con `git status` antes y después | No se ejecuta la integración | Pendientes no bloqueantes |
| T125 | Ejecución del comprobador y `enlaces.md` | Depende de T123 | Pendientes no bloqueantes |
| T130 | Parada P2 del stack y `cloudflared` | Sin clon limpio | Pendientes no bloqueantes |
| T131 | Clon limpio, `docker compose config` y `clon-limpio.md` | Alcance reducido; la reproducibilidad desde clon queda para el alumno | Pendientes no bloqueantes (A2 sigue «parcial», responsable alumno) |

## Histórico

| Feature | Estado | Fecha | Evidencias |
|---|---|---|---|
| `revision-final` (013) | Implemented (alcance reducido, solo documentación) | 2026-11-15 | `docs/evidencias/revision-final/` (`auditoria.md`, `verificacion-A.md`, `ids-propuestos.md`, `inventario.md`, `calidad-live.md`, `rubrica-guia.md`, `verificacion-B2.md`, `T132_T126_T133_comprobaciones.txt`); apuntes en `docs/borradores/revision-final.md` |
