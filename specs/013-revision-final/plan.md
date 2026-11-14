# Plan de implementación: Revisión final (013)

**Rama**: `013-revision-final` | **Spec**: [spec.md](spec.md) | **Fecha**: 2026-11-14
**Checklist**: transversal, todos los [OBL] (A1–A11, B1–B17, C1–C14, E1/E2/E4–E6, F1–F10, G1–G9/G13, H1–H5, I 1–11, J1–J7, K1–K7, M1–M5, M10). El checklist no se marca: lo hace el alumno.

## Resumen

Dejar el repositorio entregable sin añadir funcionalidad. Alcance reducido por decisión del alumno (2026-11-14), cuatro bloques: (1) auditoría de lectura (T118 a T120), (2) `CODEMAP.md` al día, README final mínimo y comprobación de `docs/rubrica-y-guia-video.md` (T132, T126, T133), (3) inventario de candidatos con parada P1 (T127, T128), (4) limpieza condicionada a P1 y cierre (T129). **Diferido** (sección «Pendientes no bloqueantes» del spec): clon limpio, `docker compose config`, parada del stack o `cloudflared` (sin P2), suite de integración en carpeta temporal, skip de Netlify, comprobador de enlaces, `docs/README.md` y el resto del bloque de limpieza. Las decisiones 2, 3, 4 y 6 siguientes quedan **diferidas** y se conservan solo como diseño para cuando el alumno las retome. Este documento es solo diseño: no contiene código, Dockerfile ni compose (constitución §19). Las decisiones de investigación y el modelo de datos van en este mismo documento (feature pequeña; no hay `research.md` ni `data-model.md` aparte).

## Contexto técnico

- Sin código nuevo en el alcance activo. (Diferido: el comprobador de enlaces sería un script de `scripts/` en el host, probado con una función pura que recibe el conjunto de rutas versionadas.)
- Sin base de datos nueva, sin contratos, sin DDL, sin API ni panel nuevos.
- Sin `NEEDS CLARIFICATION`; las 6 preguntas del spec mantienen su decisión provisional.

## Comprobación de la constitución

| Principio | Cumplimiento |
|---|---|
| §10 Secretos | Ninguna evidencia ni el README incluye contraseñas ni tokens (el clon queda diferido) |
| §13 Idioma | Script y tests con identificadores en inglés, docstrings y comentarios en español |
| §14 Una responsabilidad | El comprobador se divide en extraer, clasificar y escribir informe |
| §15 Contratos únicos | No se tocan ni se copian |
| §16 Cierre | Evidencia en `docs/evidencias/revision-final/`, `CODEMAP.md` al día; sin código nuevo, no hay tests que ejecutar salvo si la limpieza aprobada mueve código |
| §18 Enunciado de solo lectura | Se lee, no se modifica; se clasifica «mantener» |
| §19 Una feature, sin código en el plan | Parada P1 y tras cada bloque (P2 diferida); sin commit sin aprobación |
| §20 Commits | Sin trailers de atribución |

Sin violaciones; sin tabla de complejidad.

## Estructura

```text
specs/013-revision-final/            spec.md, plan.md, tasks.md, bitacora.md
(DIFERIDO) scripts/check_links.py, tests/scripts/test_check_links.py, tests/scripts/test_evidence_dir.py, tests/support/evidence.py, tests/scripts/test_netlify_config.py: no se crean ni se editan
README.md                            (editado) vídeo (marcador), tabla rúbrica→evidencia, recorrido, decisión, limitaciones, cómo ejecutar, estado
(.claude/ fuera de alcance: no se edita)
docs/evidencias/revision-final/      auditoria.md, ids-propuestos.md, verificacion-A.md, rubrica-guia.md, inventario.md  (diferidos: enlaces.md, clon-limpio.md, higiene-tests.md)
CODEMAP.md                           al día con el árbol real y con la limpieza aprobada
```

## Decisiones de diseño

1. **Auditoría (bloque 1)**. Se parte de la trazabilidad §7 del checklist y de los README de `docs/evidencias/` para rellenar una fila por [OBL]. Estados: cumple (evidencia existente y versionada que coincide con el requisito), parcial, no. Hueco con responsable: «alumno» o feature (`013`, tarea del README final, para el texto: B2, B11, B12, B18, M10, bloque L, D, C14, pregunta 3; ya no hay `readme-video`). Pendientes humanos (H4, H5, M4, capturas 1, 3, 5, 7, pruebas 9 y 10): «parcial» o «no», responsable «alumno». La redacta el implementador y la contrasta el agente `verificador` de forma independiente (solo lectura; escribe su informe `verificacion-A.md`); las discrepancias se corrigen en `auditoria.md`. `ids-propuestos.md` lista ID → estado propuesto sin tocar el checklist.
2. **(DIFERIDO) Salida de evidencias de los tests (FR-005)**. `compose.yaml` fija `EVIDENCE_DIR=/app/evidence` (montaje de escritura sobre `docs/evidencias/consumidor-idempotente`) y compose no se toca. Diseño: `tests/support/evidence.py` solo escribe en `EVIDENCE_DIR` si además existe `EVIDENCE_KEEP=1`; en otro caso escribe en una carpeta temporal del sistema (por ejemplo `<tmp>/observatory-evidence`). Así la ejecución normal no ensucia el repositorio y regenerar evidencias es una decisión explícita. La evidencia ya versionada no cambia; se documenta en `higiene-tests.md`.
3. **(DIFERIDO) Skip de netlify (FR-006)**. `skipif` a nivel de módulo, condicionado a que existan `netlify.toml` y `frontend/.nvmrc` en la raíz que ve la prueba, con motivo explícito («no montados en el servicio `tests`»). En el host siguen ejecutándose.
4. **(DIFERIDO) Comprobador de enlaces (FR-008, FR-009)**. En su lugar, la existencia de rutas se comprueba a mano con `ls` y `git ls-files`. Entradas: `README.md`, checklist, `docs/rubrica-y-guia-video.md`, `docs/borradores/*.md`, README de `docs/evidencias/**`. Extrae rutas entre comillas inversas o enlaces Markdown relativos que empiezan por una carpeta conocida o son un archivo de raíz conocido; ignora URLs y bloques de código; comodines como patrón con al menos una coincidencia. Un archivo existente pero no versionado cuenta como roto, salvo `data/raw/` si el README lo declara regenerable («no versionada por diseño»). Salida: `enlaces.md` con rutas comprobadas, rotas y archivo que las cita; código de salida distinto de cero si hay rotas. El comprobador solo informa: las rotas en `docs/borradores/`, README de `docs/evidencias/`, checklist o `docs/rubrica-y-guia-video.md` se anotan para el alumno y no se editan; solo se corrigen documentos propios de la feature (incluido `README.md`). Las evidencias pendientes del alumno (plantillas) cuentan como correctas (pregunta 4).
5. **Inventario (bloque 3)**. Candidatos iniciales a mirar (se confirman con `git ls-files` y `git status --ignored`): `docs/evidencias/f1/`, `docs/evidencias/sprint/`, `docs/evidencias/subagentes/` (rutas protegidas: solo «mantener» o «propuesta para tu decisión»), `scripts/explore_usgs.py`, `scripts/geo_real_day.py`, `scripts/verify_stack.py`, `scripts/verify_consumer.py`, `historical/` en la raíz frente a la carpeta de servicio, `.vscode/settings.json` y `.claude/commands/`, `docs/memoria.md`, `frontend/mock/`, `netlify.toml`, `compose.override.yaml` y `.env` (ignorados, no se versionan). Cada ítem: clasificación, motivo, quién lo referencia (`grep`). Un ítem referenciado no pasa a «borrar» sin corregir la referencia (US3.4). Parada P1; la limpieza aprobada se prepara para un commit propio que solo se hace cuando el alumno lo indique. Las referencias afectadas se comprueban con `grep` (no hay comprobador).
6. **(DIFERIDO) Clon limpio y parada P2**. Ya no hay bloque 4 de clon: el bloque 4 es la limpieza condicionada. Diseño original conservado: Precondición P3: lo de los bloques 1 a 3 está confirmado en la rama `013-revision-final` (pregunta 1) y P2: stack y `cloudflared` parados. Clon de esa rama en una carpeta fuera del proyecto (en el directorio temporal del sistema); `.env` desde `.env.example`; pasos tal cual el README con cronómetro por paso: build y arranque, carga del catálogo y del histórico (muestra reducida si el README la documenta; si no, completa solo si cabe, pregunta 6), `/api/salud`, build del panel, tests. Un fallo de texto se corrige en el documento y se repite; un fallo de código se reporta. Al final: `docker compose down -v` del clon (el proyecto del clon usa otro nombre de proyecto para no tocar los volúmenes del alumno), borrado de la carpeta y aviso al alumno.

7. **README final mínimo (FR-021)**. Sustituye al mapa `docs/README.md`. Se escribe después de la auditoría (T120) para que la tabla rúbrica→evidencia (M10) refleje el estado real (cumple/parcial). Contenido: marcador «PENDIENTE: enlace de YouTube» arriba; tabla de los 5 criterios con rutas de evidencia; recorrido del evento real `us6000pms8` (evidencias `docs/evidencias/replay/T053_replay.log`, `T053_consumer.log`, `T053_despues_detalle.out`); decisión propia; limitaciones; cómo ejecutar. Se reutiliza el texto ya escrito en `docs/borradores/` y en las secciones del README; `docs/borradores/` solo se toca si un [OBL] de texto queda sin cubrir. El clon limpio (diferido) seguiría este README ya final. La comprobación de `docs/rubrica-y-guia-video.md` (T133, solo lectura, resultado en `rubrica-guia.md`) va tras el README; `CODEMAP.md` (T132) va antes.

## Modelo de datos (documentos)

| Entidad | Campos |
|---|---|
| Fila de auditoría | id, requisito, evidencia (ruta), estado (cumple/parcial/no), hueco, responsable |
| Ítem de inventario | ruta, clasificación (mantener/mover/archivar/borrar), motivo, referenciado por |

## Riesgos

- Sin comprobador de enlaces, una ruta mal citada en el README puede pasar: mitigación, `ls` y `git ls-files` en T126, T132 y T133.
- Riesgos del clon, de la suite de integración y de la ruta de evidencias: diferidos con sus tareas.
- Tentación de arreglar huecos no [OBL] al auditar: regla del alumno, solo se arregla lo que deje un [OBL] sin evidencia; lo demás va a pendientes no bloqueantes.
