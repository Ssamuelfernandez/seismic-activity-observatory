# Tareas: Revisión final (013)

**Entrada**: [spec.md](spec.md), [plan.md](plan.md).
**Numeración**: continúa desde T117 (`pruebas-aceptacion`). Alcance reducido por decisión del alumno (2026-11-14): **9 tareas activas** (T118 a T120, T126 a T129, T132, T133) en 4 bloques y **7 tareas diferidas** (T121 a T125, T130, T131, marcadas `- [-]`, conservan su ID y no se ejecutan). Sin fuzz ni exhaustividad: lo mínimo que demuestra cada requisito.
**IDs**: los de los FR y SC de esta feature, y los [OBL] del checklist 01 que cada tarea toca. No se marca el checklist.
**Convenciones**: `RF` = `docs/evidencias/revision-final/`. Marcas: `- [ ]` activa, `- [-]` diferida (no se hace; ver «Pendientes no bloqueantes» del spec).
**Regla**: se arregla únicamente lo que deje un [OBL] sin evidencia; el resto se anota en «Pendientes no bloqueantes» del spec para que decida el alumno. Solo la limpieza aprobada en P1 puede mover o borrar.
**Regla de parada**: al terminar cada bloque el agente se detiene y espera la revisión del alumno (constitución §19). Nada de commit ni merge sin que el alumno lo indique, y sin trailers de atribución. No hay parada P2.

## Bloque 1: auditoría de lectura (A)

- [x] **T118** Redactar `RF/auditoria.md`: una fila por cada [OBL] del checklist (requisito, evidencia, cumple/parcial/no, hueco, responsable), a partir de la trazabilidad §7 y los README de `docs/evidencias/`. Lista explícitamente qué [OBL] no tiene evidencia. Pendientes humanos (H4, H5, M4, capturas 1, 3, 5, 7, pruebas 9 y 10) como parcial o no con responsable «alumno»; huecos de texto de README con responsable `013` (T126). No arregla nada. Prueba: el número de filas es igual al de [OBL] del checklist (`grep` de `[OBL]`) y toda fila «cumple» cita una ruta. IDs: FR-001, FR-003, SC-001; todos los [OBL].
- [x] **T119** Llamar al agente `verificador` (solo lectura) para contrastar de forma independiente `auditoria.md`: cada ruta existe y está en `git ls-files`, el requisito coincide con la evidencia y ningún «cumple» es una plantilla. Informe en `RF/verificacion-A.md`. Prueba: informe con veredicto por fila y 0 filas «cumple» sin evidencia versionada. IDs: FR-002, FR-004, SC-001. Depende de T118.
- [x] **T120** Aplicar las discrepancias del informe a `auditoria.md` (sin tocar el checklist ni corregir nada más) y crear `RF/ids-propuestos.md` con ID → estado propuesto. Prueba: `git diff --stat docs/planificacion/01-checklist-requisitos.md` vacío; todo parcial o no tiene responsable. IDs: FR-003, FR-004, SC-001. Depende de T119.

**Parada tras el bloque 1**: revisión del alumno de la auditoría.

## Bloque 2: CODEMAP, README final y rúbrica-guía (E)

Orden: T132 → T126 → T133. T126 y T133 dependen de T120 (auditoría).

- [x] **T132** Poner `CODEMAP.md` al día con el árbol real del repositorio (`git ls-files` y `ls`): añadir lo que falte, quitar lo que ya no exista, sin inventar rutas. Prueba: cada ruta citada en `CODEMAP.md` existe (`ls`) y cada carpeta de primer nivel versionada figura en él. IDs: FR-024, SC-006, M6, M8.
- [x] **T126** Rellenar `README.md` (mínimo, sin reescribirlo entero): (a) enlace al vídeo arriba con el marcador «PENDIENTE: enlace de YouTube»; (b) tabla rúbrica→evidencia (M10), una fila por criterio (Extracción, Calidad, Modelado, Análisis, Reflexión), con rutas reales y estado tomado de `RF/auditoria.md`; (c) recorrido del evento `us6000pms8` (citar `docs/evidencias/replay/T053_replay.log`, `T053_consumer.log`, `T053_despues_detalle.out`) por productor, Kafka, consumidor, base de datos, API y panel; (d) decisión propia; (e) limitaciones: sin comparación en replay, comparación siempre últimas 24 h frente a la media de 2025, periodo reciente posiblemente incompleto, `tracemalloc`, medición dentro de la VM de Docker, error 500 sin cabeceras CORS; (f) cómo ejecutar (`.env.example` → `.env`, build, carga, `/api/salud`, panel, tests; muestra reducida declarada, sin probarla en clon). Actualizar el estado de features (sin «Pendiente» ni «en curso» para 013) y quitar la referencia a `memoria-defensa (017)` / `readme-video` en `README.md` (solo `README.md`; `.claude/` no se toca). Rellenar `docs/borradores/` solo si un [OBL] de texto de la auditoría queda sin cubrir. Prueba: las seis partes existen (`grep` del marcador, de `us6000pms8` y de cada limitación); cada ruta citada en la tabla y el recorrido existe (`ls`) y está en `git ls-files`; `git diff --stat -- .claude/` vacío. Depende de T120. IDs: FR-021, SC-006, M10, B2, B11, B12, B18, C14, bloque L, D, M6, M8.
- [x] **T133** Comprobar (solo lectura) que `docs/rubrica-y-guia-video.md` está completo y coherente con las evidencias: cada criterio y cada prueba citada apunta a una evidencia existente y versionada; las pruebas 1, 5, 7, 9 y 10 figuran como pendientes de captura; la comparación figura como ausente en replay. Resultado en `RF/rubrica-guia.md` (hallazgo, ruta, acción). Se corrige en el documento únicamente lo que deje un [OBL] sin evidencia; el resto va a pendientes no bloqueantes. Prueba: `rubrica-guia.md` con una fila por criterio y por prueba citada; toda ruta citada existe (`ls`); `git diff docs/rubrica-y-guia-video.md` vacío o limitado a un [OBL] sin evidencia, justificado. Depende de T120. IDs: FR-025, SC-006, M10, bloque I (pruebas 1, 5, 7, 9, 10).

**Parada tras el bloque 2**: revisión del alumno.

## Bloque 3: inventario y parada P1 (C, paso 1)

- [x] **T127** Crear `RF/inventario.md` con los candidatos del plan (decisión 5) y los que surjan de `git ls-files` y `git status --ignored`: candidatos a mover, renombrar o eliminar, con clasificación, motivo, quién lo referencia (`grep`), y «propuesta para tu decisión» para lo que está dentro de rutas protegidas. Prueba: `git status --porcelain` sin borrados ni movimientos; todo ítem referenciado propuesto como «borrar» o «mover» lleva su corrección de referencia. IDs: FR-011, FR-012, FR-013, FR-015, SC-005, M5, M6, M8.
- [x] **T128** **PARADA P1**: el agente se detiene, entrega `inventario.md` y no borra ni mueve nada hasta la aprobación expresa del alumno (por ítem o en bloque). Si el alumno no aprueba nada, T129 se cierra como «sin cambios». Prueba: la aprobación queda registrada en `inventario.md` (fecha y ítems). IDs: FR-013, SC-005.

**Parada tras el bloque 3**: espera de la aprobación P1.

## Bloque 4: limpieza condicionada y cierre (C, paso 2)

- [x] **T129** *(Limpieza condicionada a P1; el cierre no lo está.)* Aplicar solo lo aprobado, corregir las referencias afectadas (comprobadas con `grep` y `git ls-files`), actualizar `CODEMAP.md` si algo se movió o borró, y dejar los cambios listos para un commit propio y reversible que hace el alumno o el agente solo si el alumno lo indica. Cierre: comprobar que no cambian contratos, `docs/enunciado/`, `sql/001_schema.sql`, constitución ni checklist y entregar el resumen con la lista de `ids-propuestos.md`. Prueba: sin referencias colgantes a lo movido o borrado (`grep`), `git status` solo con lo aprobado y rutas permitidas, sin commit. IDs: FR-014, FR-015, FR-022, FR-024, SC-005.

**Parada final**: el agente se detiene y espera la revisión.

## Tareas diferidas (no se ejecutan; no bloquean el cierre)

Decisión del alumno (2026-11-14). Cada una conserva su ID y su descripción original resumida, y se recoge en «Pendientes no bloqueantes» del spec.

- [-] **T121** *Diferido*: salida de evidencias de los tests a carpeta temporal (`tests/support/evidence.py`, `EVIDENCE_KEEP`). Motivo: no se cambia código de tests ni se ejecuta la suite de integración en esta feature. FR-005, FR-010, M3, M8.
- [-] **T122** *Diferido*: skip de los 3 tests de `test_netlify_config.py` si faltan `netlify.toml` o `frontend/.nvmrc`. Motivo: cambio de código de tests fuera del alcance. FR-006, FR-007, SC-003.
- [-] **T123** *Diferido*: `scripts/check_links.py` y `tests/scripts/test_check_links.py`. Motivo: no se crea código; las rutas se comprueban a mano. FR-008, FR-009, FR-010, M5, SC-002.
- [-] **T124** *Diferido*: ejecución de unitarios e integración con `git status` antes y después (`RF/higiene-tests.md`). Motivo: no se ejecuta la suite de integración. FR-005, FR-007, SC-003, M3.
- [-] **T125** *Diferido*: ejecución del comprobador de enlaces y `RF/enlaces.md`. Motivo: depende de T123. FR-009, SC-002, M5, M8.
- [-] **T130** *Diferido*: parada P2 del stack y `cloudflared`. Motivo: no hay clon limpio ni parada del stack. FR-016, A2, A10.
- [-] **T131** *Diferido*: clon limpio, `docker compose config` y `RF/clon-limpio.md`. Motivo: reducido de alcance; la reproducibilidad desde clon queda como pendiente para el alumno. FR-017, FR-018, FR-019, SC-004, A2, A10, B17, G0, G13, H2, M3.

## Orden y paralelismo

B1 → B2 → B3 → B4, con las paradas indicadas. Dentro de B2: T132, T126 y T133 en ese orden (T126 y T133 también tras T120).

## Cobertura

| Requisito | Tareas |
|---|---|
| Todos los [OBL] | T118 a T120 |
| FR-001, FR-003 | T118, T120 |
| FR-002, FR-004 | T119, T120 |
| FR-005 a FR-010 | **Diferidos** (T121 a T125) |
| FR-011, FR-012 | T127 |
| FR-013 | T127, T128 |
| FR-014 | T129 |
| FR-015 | T127, T129 |
| FR-016 a FR-020 | **Diferidos** (T130, T131) |
| FR-021 | T126 |
| FR-022 | T129 (y las tareas que editan) |
| FR-023 | Límite de alcance (todas) |
| FR-024 | T132, T129 |
| FR-025 | T133 |
| SC-001 | T118 a T120 |
| SC-002, SC-003, SC-004 | **Diferidos** |
| SC-005 | T127 a T129 |
| SC-006 | T126, T132, T133 |
| SC-007 | T118 a T120, T126 a T129, T132, T133 (9 tareas activas, 4 bloques) |
