# Feature Specification: Revisión final

**Feature Branch**: `013-revision-final` (feature transversal; no tiene fila en `docs/planificacion/03-procedimiento-ejecucion.md` §4)

**Created**: 2026-11-14

**Status**: Draft (specify + clarify hechos; pendiente de la revisión del alumno)

**Input**: Dejar el repositorio entregable: verificado, enlazado, reproducible y ordenado. Límite: 15 tareas como máximo, 4 bloques de ejecución, un día de trabajo. Lo que no esté en este alcance no se hace.

> Contratos de referencia, **sin modificar**: `specs/001-contratos-y-modelo/contracts/` (esta feature no cambia ninguno). `docs/enunciado/`, `sql/001_schema.sql`, la constitución y el checklist no se tocan: **el checklist no se marca**; al final se entrega al alumno una lista de IDs con su estado para que los marque él.

## Cobertura de requisitos

Feature transversal: no tiene fila en §4. Verifica, sin marcar nada, todos los requisitos **[OBL]** de `docs/planificacion/01-checklist-requisitos.md` (bloques A a M y tabla I de pruebas).

| Bloque del alcance | Qué hace | Requisitos que toca | Dónde se comprueba |
|---|---|---|---|
| A. Auditoría | Comprueba que cada [OBL] tiene evidencia existente y versionada | Todos los [OBL] (A1–A11, B1–B17, C1–C14, E1/E2/E4–E6, F1–F10, G1–G9/G13, H1–H5, I 1–11, J1–J7, K1–K7, M1–M5, M10) | US1, FR-001 a FR-004, SC-001 |
| B. Higiene | Suite de integración sin ensuciar el repo; skip de netlify; comprobador de enlaces | M3, M5, M8; Constitución §16 | US2, FR-005 a FR-010, SC-002, SC-003 |
| C. Inventario y limpieza | Informe de archivos dudosos; limpieza solo tras aprobación | M5, M6, M8 | US3, FR-011 a FR-015, SC-005 |
| D. Clon limpio | Seguir el README en un clon fuera del proyecto | A2, A10, B17, G0, G13, H2, M3 | US4, FR-016 a FR-020, SC-004 |
| E. Mapa de docs | `docs/README.md` corto | M6, M8 | US5, FR-021, SC-006 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auditoría de cumplimiento (Priority: P1)

El alumno (o un revisor) abre `docs/evidencias/revision-final/auditoria.md` y ve, para cada requisito [OBL] del checklist, la evidencia que lo respalda, si cumple, cumple en parte o no, y el hueco con su responsable.

**Why this priority**: es lo que dice qué falta antes de entregar; las demás partes dependen de saberlo.

**Independent Test**: tomar 5 [OBL] al azar del checklist; cada uno aparece en `auditoria.md` con una ruta de evidencia que existe y está versionada (`git ls-files`).

**Acceptance Scenarios**:

1. **Given** el checklist 01, **Then** `auditoria.md` tiene una fila por cada [OBL] con las columnas requisito, evidencia, cumple/parcial/no, hueco y responsable.
2. **Given** una fila «parcial» o «no», **Then** el hueco nombra un responsable: «alumno» o una feature concreta (por ejemplo `readme-video`).
3. **Given** un requisito cuya prueba depende de una acción humana (M4 acceso del profesor, H4 equipo encendido, H5 vídeo, pruebas 9 y 10), **Then** figura con responsable «alumno» y no se da por cumplido.
4. **Given** la auditoría terminada, **Then** el checklist no ha cambiado (`git diff` vacío sobre `01-checklist-requisitos.md`) y se entrega aparte la lista de IDs con estado propuesto.

---

### User Story 2 - Higiene de tests y enlaces (Priority: P1)

Tras ejecutar los tests, el repositorio queda limpio, y todas las rutas de evidencia citadas en los documentos de entrega existen y están versionadas.

**Why this priority**: un `git status` sucio tras la suite y un enlace roto en el README son lo primero que ve el profesor.

**Independent Test**: ejecutar la suite de integración y `git status`: sin cambios. Ejecutar el comprobador de enlaces: 0 rotos.

**Acceptance Scenarios**:

1. **Given** la suite de integración, **When** termina, **Then** `git status --porcelain` es idéntico antes y después de ejecutar la suite y `git diff --stat -- docs/evidencias` queda vacío (los archivos propios aún sin confirmar no cuentan); nada se escribió en `docs/evidencias/` durante la ejecución (la salida va a una carpeta temporal).
2. **Given** el servicio `tests` sin `netlify.toml` o sin `frontend/.nvmrc` montados, **Then** los 3 tests de `test_netlify_config.py` se saltan (skip) y los unitarios dan 0 fallos.
3. **Given** README, checklist, `docs/rubrica-y-guia-video.md`, `docs/borradores/` y los README de `docs/evidencias/`, **When** se ejecuta el comprobador, **Then** cada ruta de evidencia citada existe y está en `git ls-files`, y el resultado queda en `docs/evidencias/revision-final/enlaces.md` con 0 rotos.
4. **Given** una ruta citada que no existe, **Then** el comprobador la lista con el archivo que la cita y termina con código distinto de cero.

---

### User Story 3 - Inventario y limpieza en dos pasos (Priority: P1)

Primero el alumno recibe un informe de lo dudoso; solo después de aprobarlo expresamente se aplica la limpieza, en un commit aparte y reversible.

**Why this priority**: borrar o mover sin revisión puede perder datos o romper enlaces.

**Independent Test**: `inventario.md` existe y `git status` no muestra borrados ni movimientos antes de la aprobación.

**Acceptance Scenarios**:

1. **Given** los archivos y carpetas dudosos, **Then** `inventario.md` clasifica cada uno en mantener, mover, archivar o borrar, con motivo y con la lista de quién lo referencia (o «nadie»).
2. **Given** el informe, **Then** la feature **se detiene** (punto de aprobación P1) y no borra ni mueve nada hasta que el alumno lo apruebe de forma expresa, ítem por ítem o en bloque.
3. **Given** la aprobación, **Then** la limpieza se aplica en un commit propio, que se puede revertir con `git revert`, y el comprobador de enlaces vuelve a dar 0 rotos.
4. **Given** un ítem referenciado por algún documento, **Then** no se propone «borrar» sin proponer a la vez la corrección de la referencia.

---

### User Story 4 - Prueba de clon limpio (Priority: P1)

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

### User Story 5 - Mapa de documentación (Priority: P2)

Un `docs/README.md` corto explica qué hay en cada carpeta de `docs/`.

**Independent Test**: cada carpeta y archivo de primer nivel de `docs/` aparece descrito en una línea.

**Acceptance Scenarios**:

1. **Given** `docs/`, **Then** `docs/README.md` lista cada carpeta (`borradores`, `enunciado`, `evidencias`, `planificacion`) y archivo de primer nivel (`memoria.md`, `rubrica-y-guia-video.md`, y la propia carpeta `revision-final` dentro de `evidencias`) con una línea sobre su función y si es de solo lectura.
2. **Given** el mapa, **Then** distingue entregables (`docs/`) de herramienta de trabajo (`specs/`, `.specify/`, `.claude/`) según la constitución §18.

---

### Puntos de aprobación y fases

La feature se ejecuta en fases con parada y revisión entre ellas.

| Punto | Cuándo | Qué se necesita |
|---|---|---|
| Parada tras cada bloque | Al terminar cada bloque de ejecución | El agente se detiene y espera la revisión del alumno (constitución §19) |
| **P1** Aprobación de limpieza | Tras entregar `inventario.md` | Aprobación expresa del alumno antes de borrar o mover nada |
| **P2** Parada del stack | Antes de la prueba de clon limpio | El alumno confirma que ha parado su stack y `cloudflared` |
| P3 Commit | Cada bloque, cuando el alumno lo indique | El agente no hace commit ni merge por su cuenta; los commits no llevan trailers de atribución |

## Edge Cases

- **Evidencia versionada pero vacía o plantilla**: las plantillas pendientes del alumno (capturas 1, 3, 5, 7 y pruebas 9 y 10) existen y están versionadas, pero la evidencia es parcial; la auditoría las marca «parcial» con responsable «alumno», no «cumple».
- **Rutas con formato distinto**: el comprobador acepta rutas entre comillas inversas y enlaces Markdown relativos; ignora URLs externas (`http…`) y rutas de ejemplo en bloques de código.
- **Evidencia no versionada**: un archivo que existe en disco pero no está en `git ls-files` cuenta como roto.
- **Clon desde un estado sin confirmar**: el clon solo contiene lo que está en Git; si el alumno no ha confirmado los cambios previos, el clon no los refleja (ver pregunta 1).
- **`.env` ausente en el clon**: el README debe decir copiar `.env.example`; si no lo dice, es un fallo de documentación (se corrige).
- **Puertos ocupados**: sin parar el stack del alumno, el clon no puede arrancar; por eso P2.
- **Histórico completo lento**: si la carga completa es demasiado larga para un día, se usa la muestra reducida y se declara en `clon-limpio.md`.
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
- **FR-003**: Cada hueco tiene un responsable: «alumno» o el nombre de una feature (por ejemplo `readme-video`).
- **FR-004**: La auditoría no corrige nada y no modifica el checklist; entrega aparte una lista de IDs con estado propuesto para que el alumno los marque. Se hace con el agente verificador.

**B. Higiene de tests y enlaces**

- **FR-005**: La suite de integración escribe sus evidencias en una carpeta temporal fuera de `docs/evidencias/`; tras ejecutarla, `git status` queda limpio. El efecto sobre la evidencia ya versionada se documenta.
- **FR-006**: Los 3 tests de `tests/scripts/test_netlify_config.py` se saltan (skip) con motivo explícito si faltan `netlify.toml` o `frontend/.nvmrc` en el servicio `tests`; cuando existen, siguen comprobando lo mismo que antes.
- **FR-007**: Los tests unitarios dan 0 fallos en el servicio `tests`.
- **FR-008**: Se añade un script comprobador de enlaces que verifica que todas las rutas de evidencia citadas en `README.md`, el checklist, `docs/rubrica-y-guia-video.md`, `docs/borradores/` y los README de `docs/evidencias/` existen y están versionadas.
- **FR-009**: El comprobador escribe su resultado en `docs/evidencias/revision-final/enlaces.md` (rutas comprobadas, rotas, archivo que las cita) y devuelve código distinto de cero si hay alguna rota.
- **FR-010**: Los cambios de código de esta feature se limitan a la ruta de salida de las evidencias de tests, los skip de netlify y el script comprobador; ninguna funcionalidad nueva, refactor ni actualización de dependencias.

**C. Inventario y limpieza**

- **FR-011**: Se produce `docs/evidencias/revision-final/inventario.md` que clasifica cada archivo o carpeta dudosa en mantener / mover / archivar / borrar, con motivo y con la lista de quién lo referencia.
- **FR-012**: El criterio de «dudoso» es: archivos en la raíz o fuera de su carpeta de servicio, ficheros generados o regenerables que estén en Git, duplicados, restos de pruebas o de la herramienta, y cualquier cosa que el alumno no sepa explicar al abrir el repositorio.
- **FR-013**: **Hasta la aprobación expresa del alumno (P1) no se borra ni se mueve nada.**
- **FR-014**: La limpieza aprobada se aplica en un commit separado, reversible, y después se vuelve a ejecutar el comprobador de enlaces (0 rotos).
- **FR-015**: (Las rotas que detecte el comprobador en esas rutas protegidas solo se anotan, no se editan.) No se mueven ni se borran `docs/planificacion/`, `specs/`, `.specify/`, `.claude/`, `docs/evidencias/`, `docs/borradores/` ni `docs/rubrica-y-guia-video.md`; esos elementos solo se clasifican como «mantener».

**D. Prueba de clon limpio**

- **FR-016**: Antes de clonar, el agente pide al alumno parar su stack y `cloudflared` (P2) y no continúa sin confirmación.
- **FR-017**: El repositorio se clona en una carpeta fuera del proyecto y se siguen los pasos del README tal cual: configuración de `.env`, build y arranque, carga de catálogo e histórico (completo o muestra reducida, declarado), `/api/salud`, build del panel y tests.
- **FR-018**: Se escribe `docs/evidencias/revision-final/clon-limpio.md` con comandos, tiempo de cada paso, salida relevante y resultado global pass o fail.
- **FR-019**: Si un paso falla por la documentación, se corrige solo el texto del README u otro documento y se repite; si falla el código, se reporta sin tocarlo.
- **FR-020**: Al terminar se elimina el clon y se detiene su stack, de modo que el alumno pueda volver a levantar el suyo.

**E. Mapa de documentación**

- **FR-021**: `docs/README.md` (corto, una línea por entrada) describe cada carpeta y archivo de primer nivel de `docs/`, indica cuáles son de solo lectura y enlaza al README raíz.

**Transversales**

- **FR-022**: No se modifican contratos, `sql/001_schema.sql`, `docs/enunciado/`, la constitución ni el checklist; no se reescriben specs.
- **FR-023**: No entra: contenido final del README raíz, tabla rúbrica→evidencia, recorrido de un evento, guion o vídeo (feature `readme-video`); funcionalidad nueva, refactors, actualización de dependencias, reformateos masivos.
- **FR-024**: Cierre (constitución §16): tests ejecutados, evidencia en `docs/evidencias/revision-final/` y `CODEMAP.md` actualizado con los archivos de código nuevos o movidos (script comprobador, cambios de tests y cualquier limpieza). Sin commits ni merges sin aprobación y sin trailers de atribución (constitución §19 y §20).

### Key Entities

- **Requisito auditado**: un ID [OBL] del checklist con evidencia, estado (cumple/parcial/no), hueco y responsable.
- **Referencia de evidencia**: ruta citada en un documento, con el archivo que la cita y su estado (existe y versionada, o rota).
- **Ítem del inventario**: archivo o carpeta dudosa con clasificación, motivo y referencias.
- **Ejecución de clon limpio**: lista de pasos con comando, tiempo y resultado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `auditoria.md` cubre el 100 % de los [OBL] del checklist; cada hueco «parcial» o «no» tiene responsable; el checklist queda sin cambios (0 líneas modificadas).
- **SC-002**: El comprobador de enlaces informa 0 rutas rotas sobre todos los documentos de entrega listados.
- **SC-003**: Los unitarios dan 0 fallos y, tras ejecutar la suite de integración, `git status --porcelain` es idéntico al de antes de ejecutarla y `git diff --stat -- docs/evidencias` queda vacío (los archivos propios aún sin confirmar no cuentan).
- **SC-004**: `clon-limpio.md` recoge el resultado pass o fail, y el 100 % de los pasos con su comando exacto y su tiempo, repetibles por otra persona.
- **SC-005**: La limpieza se aplica solo con aprobación expresa registrada, en un commit propio, con 0 enlaces rotos después.
- **SC-006**: `docs/README.md` describe el 100 % de las entradas de primer nivel de `docs/` y `CODEMAP.md` queda actualizado.
- **SC-007**: El conjunto se completa en un día de trabajo con 15 tareas como máximo y 4 bloques de ejecución.

## Assumptions

- Las features 001 a 012 están cerradas y sus evidencias existen; esta feature las verifica, no las rehace.
- El alumno revisa y aprueba al final de cada bloque; la limpieza y la parada del stack requieren su respuesta explícita.
- El servicio `tests` de Compose monta `tests/` y solo algunas rutas del repositorio, por lo que `netlify.toml` y `frontend/.nvmrc` pueden no estar visibles dentro.
- El clon se hace desde el estado confirmado en Git; si hay trabajo previo sin confirmar, ese trabajo no se prueba (ver pregunta 1).
- Fuera de alcance: lo listado en FR-023 y todo lo marcado en el brief como «NO ENTRA».

## Clarifications

### Session 2026-11-14

- Q: ¿Cómo se agrupan los 5 bloques del brief en 4 bloques de ejecución y 15 tareas? → A: Bloque 1 = A (auditoría, solo lectura); bloque 2 = B + E (higiene de tests, comprobador de enlaces y `docs/README.md`); bloque 3 = C paso 1 (inventario) y parada P1, y C paso 2 solo tras aprobación; bloque 4 = D (clon limpio) tras P2. Es el reparto que respeta el tope de 4 bloques y deja las paradas obligatorias entre fases; el plan lo concreta en tareas (máximo 15).
- Q: ¿En qué orden van los bloques? → A: A, B+E, C paso 1, parada P1, C paso 2 (si se aprueba), P2, D. El comprobador de enlaces (B) debe existir antes de la limpieza (comprobar 0 rotos después) y la prueba de clon limpio va al final para probar el repositorio ya limpio.
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

Decisiones provisionales; la 1 y la 2 afectan al alcance.

1. **Estado de lo que se clona (alcance de D)**. Un clon contiene solo lo confirmado en Git, y esta rama tendrá cambios sin confirmar (bloque B, `docs/README.md`). Decisión provisional: confirmar los bloques A a E (con tu aprobación) en la rama `013-revision-final` y clonar esa rama; la prueba de clon limpio va después de la limpieza. Recomendación: esa, para probar exactamente lo que se entrega. Alternativa: clonar `main`, lo que probaría una versión anterior a esta feature.
2. **Alcance de la limpieza frente a la prohibición de mover `docs/evidencias/` y `docs/borradores/`** (FR-015). El brief permite clasificar cualquier cosa «dudosa» pero prohíbe mover esas carpetas. Decisión provisional: esas rutas solo se clasifican «mantener»; si dentro de ellas hay duplicados o restos, se listan en el inventario como «propuesta para tu decisión» sin entrar en la limpieza automática. Recomendación: esa. Alternativa: permitir borrar archivos sueltos dentro de `docs/evidencias/` con tu aprobación ítem a ítem.
3. **Responsable de los huecos de texto de README** (B2, B11, B12, B18, M10, bloque L, D, C14). Decisión provisional: se asignan a `readme-video` (según la trazabilidad §7 del checklist) y no se corrigen aquí. Recomendación: esa; corregirlos aquí sería ampliar el alcance (FR-023).
4. **Comprobador de enlaces y evidencias pendientes del alumno**. Las plantillas «captura_pendiente» y las de pruebas 9 y 10 existen pero no son la captura real. Decisión provisional: el comprobador las da por correctas (el archivo existe y está versionado) y la auditoría las marca «parcial» con responsable «alumno». Recomendación: esa; no confundir enlace roto con evidencia incompleta.
5. **Cómo se hace el skip de netlify**. Decisión provisional: `pytest.mark.skipif` o `pytest.skip` condicionado a la existencia de ambos archivos, con motivo. Recomendación: esa, porque conserva la comprobación en el host. Alternativa: montar los archivos en el servicio `tests` (toca `compose.yaml`, que no entra en el alcance).
6. **Tamaño de la muestra del histórico en el clon**. Decisión provisional: usar lo que el README llame «muestra reducida» y, si no existe, la carga completa solo si cabe en el día; en caso contrario, documentar el hueco. Recomendación: confirmar si prefieres siempre la carga completa aunque tarde.
