# Tareas: Revisión final (013)

**Entrada**: [spec.md](spec.md), [plan.md](plan.md).
**Numeración**: continúa desde T117 (`pruebas-aceptacion`). 15 tareas activas (T118 a T132) en 4 bloques. Sin fuzz ni exhaustividad: lo mínimo que demuestra cada requisito.
**IDs**: los de los FR y SC de esta feature, y los [OBL] del checklist 01 que cada tarea toca. No se marca el checklist.
**Comando base** `T`: `docker compose --profile test run --rm tests pytest` (en Git Bash de Windows, `MSYS_NO_PATHCONV=1`). `RF` = `docs/evidencias/revision-final/`.
**Regla de parada**: al terminar cada bloque el agente se detiene y espera la revisión del alumno (constitución §19). Nada de commit ni merge sin que el alumno lo indique, y sin trailers de atribución.

## Bloque 1: auditoría (solo lectura)

- [ ] **T118** Redactar `RF/auditoria.md`: una fila por cada [OBL] del checklist (requisito, evidencia, cumple/parcial/no, hueco, responsable), a partir de la trazabilidad §7 y los README de `docs/evidencias/`. Pendientes humanos (H4, H5, M4, capturas 1, 3, 5, 7, pruebas 9 y 10) como parcial o no con responsable «alumno»; huecos de texto de README con responsable `readme-video`. Prueba: el número de filas es igual al de [OBL] del checklist (`grep` de `[OBL]`) y toda fila «cumple» cita una ruta. IDs: FR-001, FR-003, SC-001; todos los [OBL].
- [ ] **T119** Llamar al agente `verificador` (solo lectura) para contrastar de forma independiente `auditoria.md`: cada ruta existe y está en `git ls-files`, el requisito coincide con la evidencia y ningún «cumple» es una plantilla. Informe en `RF/verificacion-A.md`. Prueba: informe con veredicto por fila y 0 filas «cumple» sin evidencia versionada. IDs: FR-002, FR-004, SC-001. Depende de T118.
- [ ] **T120** Aplicar las discrepancias del informe a `auditoria.md` (sin tocar el checklist ni corregir nada más) y crear `RF/ids-propuestos.md` con ID → estado propuesto. Prueba: `git diff --stat docs/planificacion/01-checklist-requisitos.md` vacío; todo parcial o no tiene responsable. IDs: FR-003, FR-004, SC-001. Depende de T119.

**Parada tras el bloque 1**: revisión del alumno de la auditoría.

## Bloque 2: higiene de tests, enlaces y mapa de docs (B + E)

Dependencias: T121 y T122 antes de T124; T123 antes de T125; T126 puede ir antes de T125 (el mapa se incluye en la comprobación).

- [ ] **T121** `tests/support/evidence.py`: solo escribe en `EVIDENCE_DIR` si hay `EVIDENCE_KEEP=1`; por defecto, carpeta temporal del sistema (plan, decisión 2). Prueba nueva `tests/scripts/test_evidence_dir.py`: sin `EVIDENCE_KEEP` el directorio elegido no es el de `EVIDENCE_DIR`; con `EVIDENCE_KEEP=1` sí. `T tests/scripts/test_evidence_dir.py -q` pasa. IDs: FR-005, FR-010, M3, M8.
- [ ] **T122** `tests/scripts/test_netlify_config.py`: `skipif` a nivel de módulo si falta `netlify.toml` o `frontend/.nvmrc`, con motivo explícito. Prueba: `T tests/scripts/test_netlify_config.py -q -rs` en el servicio `tests` da 3 skipped y 0 fallos; en el host (`pytest` con `.venv`) siguen los 3 pasando. IDs: FR-006, FR-007, SC-003.
- [ ] **T123** Crear `scripts/check_links.py` (extraer rutas, clasificar con el conjunto de rutas versionadas, escribir `enlaces.md`, código de salida ≠ 0 si hay rotas) y `tests/scripts/test_check_links.py` con un árbol temporal: ruta existente y versionada → ok; inexistente → rota con el archivo que la cita; existe sin versionar → rota; URL y bloque de código ignorados; `data/raw/` declarada regenerable → «no versionada por diseño»; comodín con coincidencia. Prueba: `T tests/scripts/test_check_links.py -q` pasa. IDs: FR-008, FR-009, FR-010, M5, SC-002.
- [ ] **T124** Ejecutar `git status --porcelain` (guardar como «antes»), `T -m "not integration" -q` y `T -m integration -q` (stack del alumno en marcha) y de nuevo `git status --porcelain` («después»). Guardar en `RF/higiene-tests.md` comandos, resultados y la nota sobre la evidencia ya versionada. Prueba: unitarios 0 fallos, integración sin fallos nuevos, `git status --porcelain` idéntico antes y después y `git diff --stat -- docs/evidencias` vacío (los archivos propios aún sin confirmar no cuentan). IDs: FR-005, FR-007, SC-003, M3.
- [ ] **T125** Ejecutar `python scripts/check_links.py` (host) y escribir `RF/enlaces.md`. El comprobador solo informa. Las rotas que caigan en `docs/borradores/`, README de `docs/evidencias/`, checklist o `docs/rubrica-y-guia-video.md` se ANOTAN en `enlaces.md` para el alumno o `readme-video` y no se editan; solo se corrigen documentos propios de esta feature (`docs/README.md`, `specs/013-revision-final/`) y se repite. Prueba: `RF/enlaces.md` con 0 rotas en documentos propios; las anotadas para el alumno figuran separadas con su archivo de origen. IDs: FR-009, SC-002, M5, M8.
- [ ] **T126** Crear `docs/README.md` (una línea por entrada: `borradores`, `enunciado` solo lectura, `evidencias` con `revision-final`, `planificacion`, `memoria.md`, `rubrica-y-guia-video.md`; distinción entregables frente a `specs/`, `.specify/`, `.claude/` según §18; enlace al README raíz). Prueba: cada entrada de primer nivel de `docs/` (`ls docs`) aparece en el archivo y `check_links.py` sigue en 0 rotas. IDs: FR-021, SC-006, M6, M8.

**Parada tras el bloque 2**: revisión del alumno.

## Bloque 3: inventario y limpieza (C)

- [ ] **T127** Crear `RF/inventario.md` con los candidatos del plan (decisión 5) y los que surjan de `git ls-files` y `git status --ignored`: clasificación, motivo, quién lo referencia (`grep`), y «propuesta para tu decisión» para lo que está dentro de rutas protegidas. Prueba: `git status --porcelain` sin borrados ni movimientos; todo ítem referenciado propuesto como «borrar» o «mover» lleva su corrección de referencia. IDs: FR-011, FR-012, FR-013, FR-015, SC-005, M5, M6, M8.
- [ ] **T128** **PARADA P1**: el agente se detiene, entrega `inventario.md` y no borra ni mueve nada hasta la aprobación expresa del alumno (por ítem o en bloque). Si el alumno no aprueba nada, T129 se cierra como «sin cambios». Prueba: la aprobación queda registrada en `inventario.md` (fecha y ítems). IDs: FR-013, SC-005.
- [ ] **T129** *(Condicionada a P1.)* Aplicar solo lo aprobado, corregir las referencias afectadas, volver a ejecutar `check_links.py` y la suite unitaria; dejar los cambios listos para un commit propio y reversible que hace el alumno o el agente solo si el alumno lo indica. Prueba: `enlaces.md` con 0 rotas, unitarios 0 fallos y `git status` solo con lo aprobado. IDs: FR-014, FR-015, SC-002, SC-005, M5, M8.

**Parada tras el bloque 3**: revisión del alumno; confirmar (P3) que los bloques 1 a 3 están confirmados en la rama antes del clon (pregunta 1).

## Bloque 4: clon limpio (D)

Dependencias: T128 (y T129 si hubo aprobación) y los commits de P3 antes de T130.

- [ ] **T130** **PARADA P2**: pedir al alumno que pare su stack y `cloudflared` (`docker compose down` sin `-v`) y esperar su confirmación; comprobar que los puertos están libres. Prueba: confirmación del alumno registrada en `RF/clon-limpio.md`; el agente no continúa sin ella. IDs: FR-016, A2, A10.
- [ ] **T131** Clonar la rama `013-revision-final` fuera del proyecto, copiar `.env.example` a `.env` y seguir el README tal cual: build y arranque, catálogo e histórico (reducida o completa, declarado), `/api/salud`, build del panel y tests, con tiempo por paso. Corregir solo texto del README si falla por documentación y repetir; reportar sin tocar código si falla el código. Prueba: `RF/clon-limpio.md` con comandos exactos, tiempos, salida relevante y resultado global pass o fail. IDs: FR-017, FR-018, FR-019, SC-004, A2, A10, B17, G0, G13, H2, M3.
- [ ] **T132** Cierre: `docker compose down -v` del clon y borrado de su carpeta; avisar al alumno de que puede levantar su stack; actualizar `CODEMAP.md` (filas de `scripts/check_links.py`, de los tres archivos de tests y de lo que haya movido la limpieza; rutas comprobadas con `ls`); comprobar que no cambian contratos, `docs/enunciado/`, `sql/001_schema.sql`, constitución ni checklist; entregar el resumen y la lista de IDs de `ids-propuestos.md` actualizada con el resultado del clon. Prueba: `git status` solo lista rutas permitidas; el clon ya no existe; sin commit. IDs: FR-020, FR-022, FR-024, SC-006, SC-007.

**Parada final**: el agente se detiene y espera la revisión.

## Orden y paralelismo

B1 → B2 → B3 → B4, con las paradas indicadas. Dentro de B2: T121 y T122 y T123 son independientes (archivos distintos) y van antes de T124 y T125.

## Cobertura

| Requisito | Tareas |
|---|---|
| Todos los [OBL] | T118 a T120 |
| FR-001, FR-003 | T118, T120 |
| FR-002, FR-004 | T119, T120 |
| FR-005 | T121, T124 |
| FR-006, FR-007 | T122, T124 |
| FR-008, FR-009 | T123, T125 |
| FR-010 | T121, T123 |
| FR-011, FR-012 | T127 |
| FR-013 | T127, T128 |
| FR-014 | T129 |
| FR-015 | T127, T129 |
| FR-016 | T130 |
| FR-017 a FR-019 | T131 |
| FR-020 | T132 |
| FR-021 | T126 |
| FR-022 a FR-024 | T132 (y las tareas que editan) |
| SC-001 | T118 a T120 |
| SC-002 | T123, T125, T129 |
| SC-003 | T122, T124 |
| SC-004 | T131 |
| SC-005 | T127 a T129 |
| SC-006 | T126, T132 |
| SC-007 | T118 a T132 (15 tareas, 4 bloques) |
