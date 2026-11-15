# Inventario de limpieza (T127, FR-011 a FR-015)

Fecha de elaboración: 2026-11-15. Rama `013-revision-final`. Solo lectura: no se ha borrado, movido ni renombrado nada. Fuentes: `git ls-files`, `git status --ignored` y `grep -rIn` sobre el repositorio (sin `.git`, `node_modules`, `.venv`, cachés).

## Resumen

| Clasificación | Ítems |
|---|---|
| mantener | 28 |
| mover | 0 |
| renombrar | 0 |
| archivar | 0 |
| borrar | 1 (I-01, solo del índice de Git) |
| propuesta para tu decisión | 0 |

Ítems propuestos para cambiar (aprueba por número en «Aprobación P1»):

- **I-01** `.vscode/settings.json`: dejar de versionarlo (`git rm --cached`; el archivo se conserva en tu disco). Motivo: `.gitignore` ya lista `.vscode/` pero el archivo está en Git; es configuración personal del editor.

Hallazgos sin acción: no hay ficheros `*.pyc`, backups (`*.bak`, `*.orig`, `*~`) ni duplicados versionados; el único archivo vacío versionado es `tests/support/__init__.py` (marcador de paquete, necesario). Los `__pycache__/`, `.pytest_cache/`, `.venv/`, `frontend/dist/` y `frontend/node_modules/` están ignorados y no entran en Git. Las demás rutas de `git ls-files` (código de servicios, tests, `sql/`, `data/`, `frontend/src`, etc.) no son dudosas según FR-012 y no se listan.

## Tabla

Leyenda de referencias: «código/test/compose/README/CLAUDE.md» indica los usos que obligan a mantener.

| ID | Ruta | Clasificación | Motivo | Quién lo referencia (`grep`) | Corrección de referencias si cambia |
|---|---|---|---|---|---|
| I-01 | `.vscode/settings.json` | borrar (solo del índice de Git) | Versionado pese a que `.gitignore` (línea 47) ignora `.vscode/`; solo contiene `python.terminal.useEnvFile`, ajuste personal. No lo usa compose, ningún test, README ni CLAUDE.md | `.gitignore`, `CODEMAP.md` (línea 148, lo cita), `.claude/skills/speckit-implement/SKILL.md` (solo como patrón genérico), `specs/013-revision-final/plan.md` | Quitar la mención `.vscode/settings.json` de la fila de `CODEMAP.md` (línea 148). El resto no la requiere |
| I-02 | `scripts/explore_usgs.py` | mantener | Reproduce la exploración del feed (evidencia F1); lo usan README y la evidencia `docs/evidencias/f1/explore_usgs_salida.txt` | `README.md`, `CODEMAP.md`, `.gitignore`, `docs/memoria.md`, `docs/borradores/productor-live.md`, `docs/planificacion/02-roadmap-implementacion.md`, `docs/planificacion/03-procedimiento-ejecucion.md`, `specs/001-contratos-y-modelo/contracts/api.md` | n/a |
| I-03 | `scripts/geo_real_day.py` | mantener | Prueba 7 con un día real; tiene test | `tests/scripts/test_geo_real_day.py`, `README.md`, `CODEMAP.md`, `docs/evidencias/pruebas/README.md` y `07-evento-maritimo.md`, `docs/borradores/geografia-pais.md`, `specs/005-geografia-pais/{plan,quickstart,research}.md` | n/a |
| I-04 | `scripts/verify_stack.py` | mantener | Verificación del stack; tiene test | `tests/scripts/test_verify_stack_a1.py`, `README.md`, `CODEMAP.md`, `docs/borradores/replay.md`, `docs/evidencias/replay/README.md` | n/a |
| I-05 | `scripts/verify_consumer.py` | mantener | Escenarios del consumidor; importado por el paquete `scripts/consumer_scenarios/` y citado en el código | `scripts/consumer_scenarios/{__init__,helpers,report,stack}.py`, `consumer/counters.py`, `tests/scripts/test_geo_scenario.py`, `README.md`, `CODEMAP.md` | n/a |
| I-06 | `historical/` (raíz) frente a `data/historical/` | mantener | No hay duplicado: `historical/` es el paquete Python del cargador (la imagen lo copia) y `data/historical/` son los datos montados por compose | `Dockerfile` (`COPY historical ./historical`), `compose.yaml` (módulo y volumen `./data/historical`), `common/`, `consumer/queries.py`, `tests/historical/`, `CODEMAP.md`, `README.md` | n/a |
| I-07 | `netlify.toml` (raíz) | mantener | Configuración de despliegue del panel; la comprueba un test | `tests/scripts/test_netlify_config.py`, `README.md`, `CODEMAP.md`, `docs/borradores/despliegue-tunel.md` | n/a |
| I-08 | `docs/memoria.md` | mantener | Entregable (memoria); citada por README y la guía | `README.md`, `CODEMAP.md`, `docs/enunciado/Guia-entregables-observatorio-sismico.md`, `docs/evidencias/revision-final/{auditoria,rubrica-guia}.md` | n/a |
| I-09 | `frontend/mock/` (6 archivos, 1,8 MB; `truncated.json` 1,6 MB) | mantener | Mock sintético etiquetado que exige CLAUDE.md; lo cargan el cliente en modo mock y los tests; generado de forma determinista, pero versionado a propósito (hash en las evidencias) | `frontend/src/shared/api/{dataSource,mockUnavailable}.ts`, `frontend/tests/{backend,mock}.test.ts`, `frontend/scripts/{generate-mock,check-dist}.mjs`, `frontend/README.md`, `CODEMAP.md`, `CLAUDE.md` (regla del mock) | n/a |
| I-10 | `compose.override.yaml` (ignorado, existe en local) | mantener (ignorado, no se versiona) | Override local que publica PostgreSQL en 127.0.0.1 para desarrollo; `.gitignore` línea 17 lo declara «no se entrega» | `.gitignore`, `CODEMAP.md`, `docs/evidencias/despliegue-tunel/README.md`, `docs/evidencias/replay/README.md`, `docs/borradores/replay.md` | n/a |
| I-11 | `.env` (ignorado, existe en local) | mantener (ignorado, no se versiona) | Valores reales locales; la plantilla versionada es `.env.example` (sin secretos) | `.gitignore`, `scripts/check_env_example.py` (compara con `.env.example`), `compose.yaml`, `README.md` | n/a |
| I-12 | `.claude/commands/` (`feature.md`, `sprint.md`) | mantener (ruta protegida) | Comandos del flujo de trabajo; FR-015 los protege | `.claude/commands/sprint.md`, `CODEMAP.md`, `CLAUDE.md` (flujo), `specs/013-revision-final/plan.md` | n/a |
| I-13 | `docs/evidencias/f1/` (1 archivo) | mantener (ruta protegida) | Salida de `explore_usgs.py` citada como fuente del feed | `README.md`, `docs/memoria.md`, `docs/borradores/productor-live.md`, `CODEMAP.md`, `specs/001-contratos-y-modelo/{spec,tasks,quickstart}.md`, `specs/004-productor-live/tasks.md` | n/a |
| I-14 | `docs/evidencias/sprint/` (26 archivos) | mantener (ruta protegida) | Actas del modo sprint (diseño, implementación y cierre por feature) | `.claude/commands/sprint.md`, `.claude/agents/supervisor.md`, `CODEMAP.md`, `specs/007-api/{plan,spec,tasks}.md`, `specs/010-despliegue-tunel/{bitacora,spec}.md`, `specs/012-pruebas-aceptacion/spec.md` | n/a |
| I-15 | `docs/evidencias/subagentes/` (61 archivos) | mantener (ruta protegida) | Informes de los agentes revisores y verificadores | `.claude/commands/feature.md`, `CODEMAP.md`, `docs/borradores/{contratos-y-modelo,panel-base-mock}.md`, `docs/evidencias/sprint/*.md`, `docs/evidencias/revision-final/rubrica-guia.md` | n/a |
| I-16 | `docs/evidencias/**/*.log` y `*.txt` (salidas de pruebas, p. ej. `replay/T053_*.log`, `historico-2025/descarga_2025*.log`) | mantener (ruta protegida) | Evidencia de ejecución; citada por los README de cada carpeta de evidencias | README de cada carpeta de `docs/evidencias/`, `CODEMAP.md` | n/a |
| I-17 | `data/raw/` (ignorado, existe en local; 1 GeoJSON de `explore_usgs.py`) | mantener (ignorado) | Salida regenerable de `explore_usgs.py`; ya ignorada | `.gitignore`, `scripts/explore_usgs.py`, `docs/planificacion/{01,02,03,04}*.md` | n/a |
| I-18 | `.specify/feature.json` (ignorado, existe en local) | mantener (ignorado; ruta protegida) | Puntero local de Spec Kit; lo ignora `.specify/.gitignore` | `.specify/.gitignore`, `.claude/skills/speckit-specify/SKILL.md`, `.specify/scripts/powershell/common.ps1` | n/a |
| I-19 | `uv.lock`, `.python-version`, `.dockerignore`, `.gitattributes`, `frontend/package-lock.json` | mantener | Reproducibilidad de dependencias y de la imagen; no son restos | `Dockerfile`, `README.md`, `CODEMAP.md`, `frontend/README.md` | n/a |
| I-20 | `scripts/postgres_init.sh` y `scripts/check_env_example.py` | mantener | Los usa compose / comprobación de `.env.example` | `compose.yaml` (`postgres_init`), `README.md`, `CODEMAP.md`, `specs/002-infra-compose/*` | n/a |
| I-21 | `docs/borradores/` | mantener (ruta protegida) | Apuntes por feature para la memoria; citados por CODEMAP y README | `CODEMAP.md`, `README.md`, `docs/memoria.md` | n/a |
| I-22 | `docs/planificacion/`, `docs/rubrica-y-guia-video.md`, `docs/enunciado/` | mantener (rutas protegidas) | Plan, rúbrica y material del profesor (solo lectura) | `CLAUDE.md`, `CODEMAP.md`, `README.md` | n/a |
| I-23 | `specs/`, `.specify/` (salvo `feature.json`), `.claude/` (agents, skills, settings.json) | mantener (rutas protegidas) | Flujo Spec Kit y agentes | `CLAUDE.md`, `CODEMAP.md` | n/a |
| I-24 | `sql/001_schema.sql`, `sql/002_roles.sql` | mantener | Esquema y roles que carga compose; `001_schema.sql` es ruta protegida | `compose.yaml`, `README.md`, `CODEMAP.md`, `specs/001-contratos-y-modelo/` | n/a |
| I-25 | `specs/001-contratos-y-modelo/contracts/` | mantener (ruta protegida) | Contratos | `CLAUDE.md`, `CODEMAP.md`, `api/`, `common/` | n/a |
| I-26 | `__pycache__/`, `.pytest_cache/`, `.venv/` (ignorados) | mantener (ignorados) | Cachés y entorno local regenerables, fuera de Git | `.gitignore` | n/a |
| I-27 | `frontend/dist/`, `frontend/node_modules/` (ignorados) | mantener (ignorados) | Artefactos de compilación e instalación, fuera de Git | `.gitignore`, `frontend/.gitignore` | n/a |
| I-28 | `tests/support/__init__.py` (único archivo vacío versionado) | mantener | Marcador de paquete necesario para importar los helpers de tests | `tests/` (imports `tests.support.*`) | n/a |
| I-29 | `data/historical/` (13 GeoJSON + `manifest.json`) y `data/catalogo/paises.geojson` | mantener | Datos de entrada del histórico y del catálogo de países; los montan compose y los usa el cargador | `compose.yaml`, `historical/`, `README.md`, `CODEMAP.md` | n/a |

Las referencias de la columna 5 salen de `grep -rIln` ejecutados el 2026-11-15; en los candidatos «mantener» no se enumeran todas las menciones dentro de `docs/evidencias/`, solo los usos que obligan a conservar el archivo.

## Aprobación P1

(Aprobado por el alumno en chat.)

- Fecha: 2026-11-15
- Ítems aprobados (por número, p. ej. I-01): I-01
