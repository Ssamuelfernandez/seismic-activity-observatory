# Plan de implementación: Revisión final (013)

**Rama**: `013-revision-final` | **Spec**: [spec.md](spec.md) | **Fecha**: 2026-11-14
**Checklist**: transversal, todos los [OBL] (A1–A11, B1–B17, C1–C14, E1/E2/E4–E6, F1–F10, G1–G9/G13, H1–H5, I 1–11, J1–J7, K1–K7, M1–M5, M10). El checklist no se marca: lo hace el alumno.

## Resumen

Dejar el repositorio entregable sin añadir funcionalidad. Cuatro bloques: (1) auditoría de solo lectura, (2) higiene de tests, comprobador de enlaces y `docs/README.md`, (3) inventario de lo dudoso con parada P1 y limpieza condicionada, (4) clon limpio tras la parada P2. Este documento es solo diseño: no contiene código, Dockerfile ni compose (constitución §19). Las decisiones de investigación y el modelo de datos van en este mismo documento (feature pequeña; no hay `research.md` ni `data-model.md` aparte).

## Contexto técnico

- Python 3.12, pytest, servicio `tests` de Compose; el comprobador de enlaces es un script de `scripts/` que se ejecuta en el host (necesita `git`, que el servicio `tests` no tiene) y se prueba con una función pura que recibe el conjunto de rutas versionadas.
- Sin base de datos nueva, sin contratos, sin DDL, sin API ni panel nuevos.
- Sin `NEEDS CLARIFICATION`; las 6 preguntas del spec mantienen su decisión provisional.

## Comprobación de la constitución

| Principio | Cumplimiento |
|---|---|
| §10 Secretos | El clon usa `.env.example` copiado; ninguna evidencia incluye contraseñas ni tokens |
| §13 Idioma | Script y tests con identificadores en inglés, docstrings y comentarios en español |
| §14 Una responsabilidad | El comprobador se divide en extraer, clasificar y escribir informe |
| §15 Contratos únicos | No se tocan ni se copian |
| §16 Cierre | Tests ejecutados, evidencia en `docs/evidencias/revision-final/`, `CODEMAP.md` actualizado |
| §18 Enunciado de solo lectura | Se lee, no se modifica; se clasifica «mantener» |
| §19 Una feature, sin código en el plan | Paradas P1, P2 y tras cada bloque; sin commit sin aprobación |
| §20 Commits | Sin trailers de atribución |

Sin violaciones; sin tabla de complejidad.

## Estructura

```text
specs/013-revision-final/            spec.md, plan.md, tasks.md, bitacora.md
scripts/check_links.py               (nuevo) comprobador de enlaces de evidencia
tests/scripts/test_check_links.py    (nuevo) pruebas sin Docker del comprobador
tests/scripts/test_evidence_dir.py   (nuevo) prueba de la ruta de salida de evidencias
tests/support/evidence.py            (editado) ruta de salida temporal por defecto
tests/scripts/test_netlify_config.py (editado) skip con motivo
docs/README.md                       (nuevo) mapa de docs/
docs/evidencias/revision-final/      auditoria.md, ids-propuestos.md, verificacion-A.md, enlaces.md, inventario.md, clon-limpio.md, higiene-tests.md
CODEMAP.md                           filas del script, tests y limpieza
```

## Decisiones de diseño

1. **Auditoría (bloque 1)**. Se parte de la trazabilidad §7 del checklist y de los README de `docs/evidencias/` para rellenar una fila por [OBL]. Estados: cumple (evidencia existente y versionada que coincide con el requisito), parcial, no. Hueco con responsable: «alumno» o feature (`readme-video` para el texto del README: B2, B11, B12, B18, M10, bloque L, D, C14, pregunta 3). Pendientes humanos (H4, H5, M4, capturas 1, 3, 5, 7, pruebas 9 y 10): «parcial» o «no», responsable «alumno». La redacta el implementador y la contrasta el agente `verificador` de forma independiente (solo lectura; escribe su informe `verificacion-A.md`); las discrepancias se corrigen en `auditoria.md`. `ids-propuestos.md` lista ID → estado propuesto sin tocar el checklist.
2. **Salida de evidencias de los tests (FR-005)**. `compose.yaml` fija `EVIDENCE_DIR=/app/evidence` (montaje de escritura sobre `docs/evidencias/consumidor-idempotente`) y compose no se toca. Diseño: `tests/support/evidence.py` solo escribe en `EVIDENCE_DIR` si además existe `EVIDENCE_KEEP=1`; en otro caso escribe en una carpeta temporal del sistema (por ejemplo `<tmp>/observatory-evidence`). Así la ejecución normal no ensucia el repositorio y regenerar evidencias es una decisión explícita. La evidencia ya versionada no cambia; se documenta en `higiene-tests.md`.
3. **Skip de netlify (FR-006)**. `skipif` a nivel de módulo, condicionado a que existan `netlify.toml` y `frontend/.nvmrc` en la raíz que ve la prueba, con motivo explícito («no montados en el servicio `tests`»). En el host siguen ejecutándose.
4. **Comprobador de enlaces (FR-008, FR-009)**. Entradas: `README.md`, checklist, `docs/rubrica-y-guia-video.md`, `docs/borradores/*.md`, README de `docs/evidencias/**`. Extrae rutas entre comillas inversas o enlaces Markdown relativos que empiezan por una carpeta conocida o son un archivo de raíz conocido; ignora URLs y bloques de código; comodines como patrón con al menos una coincidencia. Un archivo existente pero no versionado cuenta como roto, salvo `data/raw/` si el README lo declara regenerable («no versionada por diseño»). Salida: `enlaces.md` con rutas comprobadas, rotas y archivo que las cita; código de salida distinto de cero si hay rotas. El comprobador solo informa: las rotas en `docs/borradores/`, README de `docs/evidencias/`, checklist o `docs/rubrica-y-guia-video.md` se anotan para el alumno o `readme-video` y no se editan; solo se corrigen documentos propios de la feature. Las evidencias pendientes del alumno (plantillas) cuentan como correctas (pregunta 4).
5. **Inventario (bloque 3)**. Candidatos iniciales a mirar (se confirman con `git ls-files` y `git status --ignored`): `docs/evidencias/f1/`, `docs/evidencias/sprint/`, `docs/evidencias/subagentes/` (rutas protegidas: solo «mantener» o «propuesta para tu decisión»), `scripts/explore_usgs.py`, `scripts/geo_real_day.py`, `scripts/verify_stack.py`, `scripts/verify_consumer.py`, `historical/` en la raíz frente a la carpeta de servicio, `.vscode/settings.json` y `.claude/commands/`, `docs/memoria.md`, `frontend/mock/`, `netlify.toml`, `compose.override.yaml` y `.env` (ignorados, no se versionan). Cada ítem: clasificación, motivo, quién lo referencia (`grep`). Un ítem referenciado no pasa a «borrar» sin corregir la referencia (US3.4). Parada P1; la limpieza aprobada se prepara para un commit propio que solo se hace cuando el alumno lo indique.
6. **Clon limpio (bloque 4)**. Precondición P3: lo de los bloques 1 a 3 está confirmado en la rama `013-revision-final` (pregunta 1) y P2: stack y `cloudflared` parados. Clon de esa rama en una carpeta fuera del proyecto (en el directorio temporal del sistema); `.env` desde `.env.example`; pasos tal cual el README con cronómetro por paso: build y arranque, carga del catálogo y del histórico (muestra reducida si el README la documenta; si no, completa solo si cabe, pregunta 6), `/api/salud`, build del panel, tests. Un fallo de texto se corrige en el documento y se repite; un fallo de código se reporta. Al final: `docker compose down -v` del clon (el proyecto del clon usa otro nombre de proyecto para no tocar los volúmenes del alumno), borrado de la carpeta y aviso al alumno.

## Modelo de datos (documentos)

| Entidad | Campos |
|---|---|
| Fila de auditoría | id, requisito, evidencia (ruta), estado (cumple/parcial/no), hueco, responsable |
| Referencia de evidencia | ruta, archivo que la cita, estado (ok / no existe / no versionada / no versionada por diseño) |
| Ítem de inventario | ruta, clasificación (mantener/mover/archivar/borrar), motivo, referenciado por |
| Paso de clon limpio | n.º, comando, tiempo, resultado, salida relevante |

## Riesgos

- El clon usa los mismos puertos que el stack del alumno: P2 obligatoria; además el proyecto de Compose del clon debe llamarse distinto para no compartir volúmenes ni contenedores.
- La suite de integración necesita el stack levantado; los bloques 2 y 3 se hacen con el stack del alumno en marcha, el bloque 4 con el stack del clon.
- La carga completa del histórico puede tardar: se prefiere la muestra reducida documentada.
- Cambiar la ruta de evidencias puede romper una prueba que lea la salida escrita: la tarea de código incluye ejecutar la suite completa antes de dar el bloque por cerrado.
