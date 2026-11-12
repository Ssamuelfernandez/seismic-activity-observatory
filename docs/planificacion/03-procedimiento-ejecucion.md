# Observatorio de actividad sísmica — Procedimiento de ejecución

Complementa `01-checklist-requisitos.md` (qué hay que entregar) y `02-roadmap-implementacion.md` (en qué orden). Este documento dice **cómo se trabaja**: flujo con GitHub Spec Kit y Claude Code, features, organización del repositorio, reglas para que el código sea legible y procedimiento para ejecutar el sistema.

Los IDs (A1, B6, C4, F8, G5…) remiten al checklist; las fases (F0–F13) remiten al roadmap.

**Registro de cambios**
- 1-nov-2026 (rev. 3): reconciliación de los tres documentos. **El frontend se construye desde cero** (el proyecto Angular del paquete es solo un ejemplo): la feature del panel se divide en cinco. Tabla de features única (§4) con las semillas de spec integradas (antes estaban en el roadmap). Identificadores de código, BD y topics en inglés. Constitución ampliada (§5). Comandos de Spec Kit con nota de versión. Se añade la fuente de verdad por tema (§0).
- 2-nov-2026 (rev. 4): la librería del mapa es libre (el profesor confirmó por correo el 2-nov-2026 que Leaflet era una guía, no una obligación). Candidata: Globe.gl; alternativas: MapLibre o Leaflet; se decide en el plan de `panel-base-mock`. Afecta a §0, §3 (árbol de carpetas), §4.2, §6 y §7.5.
- Nov-2026 (rev. 5): el profesor permite cambiar el frontend; decisión del alumno: **React + TypeScript + Vite + Tailwind** en lugar de Angular (mapa `react-globe.gl`, plan B MapLibre o Leaflet; TanStack Query; Chart.js; store único de filtros). Afecta a §0, §3, §4.2, §5 y §7.5. El alcance de las features no cambia.
- 5-nov-2026 (rev. 6): se añade el requisito G17 (diseño responsive) a la fila `008-panel-base-mock` de §4.
- 6-nov-2026 (rev. 7): se añade a §4 la feature `panel-mapa-2d` (F8f, G18): vista de mapa 2D con MapLibre, nacida del cambio de diseño visual de `008-panel-base-mock` (globo HUD). Se identifica por su nombre y no por número (los números de §4 son orientativos), sin renumerar las demás.
- 10-nov-2026 (rev. 8): **enmienda de alcance de `008-panel-base-mock`** (decisión del alumno): adopta el front externo con correcciones y absorbe las features `009-panel-filtros-tabla`, `010-panel-graficos-comparacion`, `011-panel-estado-fallos` y `012-panel-conexion-api` (§4 y §4.2). `panel-mapa-2d` queda aplazada. `013-replay` no cambia. Se aplica la fusión que §4 ya preveía como recurso si el tiempo apretaba.
- 10-nov-2026 (rev. 9): **estructura de `src/` del frontend** (§7.5): se conserva la del front externo (`components/`, `shared/{api,hooks,lib,types}`, `store/`) en lugar de `api/`, `config/`, `features/`; el mock vive en `frontend/mock/` fuera del build de producción. Decisión del alumno al contestar la pregunta P1 de `008-panel-base-mock`.

---

## 0. Decisiones tomadas y fuente de verdad

| Tema | Decisión |
|---|---|
| SDD | GitHub Spec Kit como base del flujo (constitution → specify → clarify → plan → tasks → analyze → implement; ver nota de comandos en §2) |
| Agente | Claude Code |
| Idioma | **Identificadores en inglés** (funciones, variables, archivos de código, tablas, columnas, topics). Docstrings, comentarios y documentación en español. Excepciones: rutas y campos fijados por el contrato del profesor (`/api/eventos`, `/api/salud`, `/api/estadisticas`, `country_id`, `country_name`…). El nombre de las carpetas de features en `specs/` va en español |
| Claridad del código | Reglas de estructura y funciones + docstrings explicativos + mapa del código (`CODEMAP.md`) |
| Contratos | La feature `001-contratos-y-modelo` es la **fuente de verdad** de los tres contratos. Las demás features los referencian y nunca los duplican |
| Frontend | React + TypeScript + Vite + Tailwind, con mapa `react-globe.gl` (plan B MapLibre o Leaflet; se confirma en el plan de panel-base-mock) **desde cero** (el ejemplo del paquete solo se consulta). Se desarrolla primero contra un **mock** del contrato y se reconecta a la API real |
| Documentación | `docs/enunciado/` (material del profesor) es **solo lectura**. `docs/` (entregables) y `specs/` (herramienta) son cosas distintas (§1) |

### Fuente de verdad por tema (si dos documentos discrepan, manda este orden)

| Tema | Manda | Derivados |
|---|---|---|
| Qué hay que entregar y cómo se evalúa | `docs/enunciado/` (Enunciado > Guía de entregables > FAQ) | `01-checklist-requisitos.md` (resumen derivado: si choca con el enunciado, gana el enunciado) |
| Contrato de la API con el panel | `docs/enunciado/CONTRATO-API.md` (mínimo) + su ampliación en `specs/001-contratos-y-modelo/contracts/api.md` | Mock del frontend, tests de la API |
| Contratos Kafka y esquema de BD | `specs/001-contratos-y-modelo/contracts/` | `sql/`, código |
| Reglas del proyecto | Constitución (`.specify/memory/constitution.md`, borrador en §5) | `CLAUDE.md`, roadmap §0 |
| Orden de trabajo y contenido de cada fase | `02-roadmap-implementacion.md` | — |
| Cómo se trabaja, features y reglas de código | Este documento | `CLAUDE.md` |

---

## 1. Dos carpetas con dos funciones distintas

Spec Kit crea `specs/` y `.specify/`. El roadmap ya define `docs/`. No son lo mismo:

| Carpeta | Para quién | Qué contiene |
|---|---|---|
| `specs/` (Spec Kit) | Tú y Claude Code | Cómo se construye cada feature: spec, plan, tareas, contratos de esa feature |
| `docs/` | El profesor | Entregables: memoria, evidencias de pruebas, diagramas finales. Además `docs/enunciado/` (material del profesor, solo lectura) y `docs/planificacion/` (estos tres documentos) |
| `.specify/` y `.claude/` | Herramientas | Plantillas, constitución y comandos. No se tocan a mano salvo la constitución |

Regla: **nada de `specs/` se copia tal cual a `docs/`**. Lo que sirva para la memoria se reescribe pensando en quien lo evalúa.

---

## 2. Instalación y arranque (una sola vez)

### Paso 0 — Andamiaje previo (F0, a mano, antes de Spec Kit)

1. Crear en el repo: `docs/enunciado/` (todo el paquete del profesor tal cual, `README.md` renombrado a `README-paquete.md`, guía de entregables incluida), `docs/planificacion/` (los tres documentos), `data/catalogo/paises.geojson` (sin modificar), `.gitignore`, `README.md` de una línea.
2. **No** copiar el frontend de ejemplo al repo (guárdalo fuera si quieres consultarlo) y **no** crear carpetas de servicio todavía.
3. Primer commit manual, sin trailers de coautoría, y `git push`.

### Requisitos y arranque

Requisitos: Python 3.11+, `uv`, Git, Node LTS, Docker Desktop y Claude Code instalado.

```bash
# 1. Instalar el CLI de Spec Kit (fijar una versión concreta de la página de Releases)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
#   La página oficial muestra también la forma simple:  uv tool install specify-cli

# 2. Comprobar herramientas
specify check

# 3. En la raíz del repositorio, inicializar para Claude Code
specify init . --integration claude
#   Versiones anteriores usaban:  specify init . --ai claude
#   Ante dudas:                   specify init --help

# 4. Abrir Claude Code en la raíz y comprobar qué comandos de Spec Kit aparecen
```

Después de `init` deberían existir `.specify/` (plantillas, scripts, memoria de la constitución) y los comandos del agente en `.claude/`. **Revisa lo generado antes de hacer commit.**

> **Nota de versión.** Este documento escribe los comandos como `/speckit.xxx`. Según la versión instalada pueden llamarse `/speckit-xxx` (la página oficial de Spec Kit mostraba guiones). Además, algunas versiones traen `/speckit-converge` (comprobar lo implementado y repetir implement/converge hasta converger), y los pasos `clarify` y `analyze` pueden no existir en todas: si no están, equivalen a revisión manual. La fuente de verdad es el README del repositorio `github/spec-kit` y `specify --help`. Si algo de este documento no coincide con la herramienta instalada, manda la herramienta. Anota en el README la versión de la CLI que uses.

### Sin atribución a Claude en Git

Tienes tres barreras:

1. **Constitución** (apartado 5): prohíbe trailers `Co-Authored-By` y líneas de "generado por" en commits y PRs.
2. **Configuración de Claude Code** en `.claude/settings.json`. Los nombres de las claves han cambiado entre versiones; comprueba la documentación de tu versión. Hoy se usa:

```json
{ "attribution": { "commit": "", "pr": "" } }
```

(En versiones antiguas la opción era `"includeCoAuthoredBy": false`.)

3. Un hook `commit-msg` que rechaza el trailer (`.git/hooks/commit-msg`, con permiso de ejecución):

```bash
#!/bin/sh
if grep -qiE "co-authored-by|generated with" "$1"; then
  echo "Commit rechazado: sin trailers de coautoría ni líneas de herramienta." >&2
  exit 1
fi
```

Antes del primer commit real tras `specify init`, haz uno de prueba y revisa el mensaje con `git log -1`. Revisa también cada commit antes de `git push`.

---

## 3. Estructura del repositorio

```
observatorio-sismico/
├── CLAUDE.md                  # reglas cortas para el agente (apartado 9)
├── CODEMAP.md                 # mapa del código (apartado 7.6)
├── README.md                  # ejecución reproducible (entregable)
├── compose.yaml
├── .env.example
├── .gitignore
├── .specify/                  # Spec Kit (plantillas, constitución)
├── .claude/                   # comandos de Claude Code + settings
├── specs/                     # una carpeta por feature (apartado 4)
├── common/                    # código compartido por varios servicios
├── producer/                  # productor live y replay
├── consumer/                  # consumidor
├── api/                       # FastAPI
├── frontend/                  # React + TS + Vite + Tailwind (desde cero)
├── sql/                       # DDL e índices
├── scripts/                   # exploración USGS, histórico: descarga y carga
├── data/
│   ├── catalogo/              # paises.geojson (catálogo entregado; SÍ versionado)
│   └── raw/                   # histórico descargado (fuera de Git)
├── notebooks/                 # calidad, análisis, mediciones
├── tests/                     # espejo de la estructura del código
└── docs/
    ├── enunciado/             # material del profesor (SOLO LECTURA)
    ├── planificacion/         # 01, 02 y 03
    ├── evidencias/            # evidencias por feature
    └── memoria.md             # entregable
```

La imagen Docker compartida y su contexto de build se deciden en la feature `002-infra-compose`. Lo único fijo es que `common/` debe poder importarlo cualquier servicio Python.

---

## 4. Features de Spec Kit ↔ fases del roadmap ↔ checklist

Una feature = un ciclo completo de Spec Kit = una rama. Spec Kit numera las carpetas por orden de creación (`001-…`, `002-…`): **los números de la tabla son orientativos; en los documentos y prompts usa el nombre (slug)**, que es estable aunque cambie el orden (por ejemplo, el panel puede empezarse antes que `006-historico-2025`).

| Feature (`specs/…`) | Fase roadmap | Qué cubre del checklist | Pruebas de aceptación que la cierran |
|---|---|---|---|
| `001-contratos-y-modelo` | F1b | E1–E5, E7; contrato Kafka; esquema BD (`sql/001_schema.sql`); `api.md`; reglas de versiones (C4) | — (se valida con `004`) |
| `002-infra-compose` | F2 (el andamiaje F0 va a mano antes) | A1–A12, M7–M9 (configuración de Git y estructura) | — (arranca limpio, persiste tras reiniciar) |
| `003-productor-live` | F4 | B1–B12 | 1 (evento nuevo, real), 2 (reenvío) |
| `004-consumidor-idempotente` | F3 | C1–C8, C13 | 2 (reenvío), 3, 4, 6, 8 |
| `005-geografia-pais` | F5 | C9–C12 | 5 (magnitud nula), 7 (evento marítimo) |
| `006-historico-2025` | F6 | B13–B18 | — (conteos cuadran con los archivos) |
| `007-api` | F7 | F1–F12 (F12 se completa con `013`) | — (tests con httpx, 503 con BD parada) |
| `008-panel-base-mock` (**enmendada el 10-nov-2026**: adopta el front externo y absorbe `009`–`012`) | F8a–F8e | G0, G1, G2, G3, G4, G5, G5b, G6, G7, G8, G9, G11, G14, G15, G17; G12 (`magType`, `country_id`, `country_name`, `truncated`, `last_ingestion`). G16 **no cubierta** (decisión propia). G10 y G12 (`metadata.mode`) se cierran en `013-replay` (el banner y la vista de replay viajan en `008`) | — (capturas con el mock y con la API real, filtros visibles, fallo provocado, una captura a 375 px) |
| `009-panel-filtros-tabla` | F8b | **ABSORBIDA por `008-panel-base-mock`**: G6, G8, G16 (no cubierta); parte de G12 (`country_id`, `country_name`, `truncated`) | — |
| `010-panel-graficos-comparacion` | F8c | **ABSORBIDA por `008-panel-base-mock`**: G3, G4, G5, G5b | — |
| `011-panel-estado-fallos` | F8d | **ABSORBIDA por `008-panel-base-mock`**: G7, G9; parte de G12 (`last_ingestion`) | — |
| `012-panel-conexion-api` | F8e | **ABSORBIDA por `008-panel-base-mock`**: G1 | — |
| `013-replay` | F9 | J1–J8, G10, F12; parte de G12 (`metadata.mode`) | 11 |
| `014-pruebas-aceptacion` | F10 | Tabla I completa | Las 11 (formalización y evidencia) |
| `015-despliegue-tunel` | F11 | G13, H1–H4 | 9 y 10 (cerrar y reabrir túnel) |
| `016-mediciones-costes` | F12 | K1–K8, E6 | — |
| `017-memoria-defensa` | F13 | Bloque L, D y C14 (calidad), M, H5 | — |
| `panel-mapa-2d` | F8f | G18 | **APLAZADA** (10-nov-2026): no se ejecuta salvo que sobre tiempo. — (captura del mapa 2D con eventos ya cargados y aviso de truncado; sin peticiones nuevas) |

Notas:
- `006` es independiente y puede ir en paralelo a `003`–`005` (el roadmap lo permite desde F1). `008` puede empezar en cuanto exista `002`, porque solo necesita el contrato.
- Si una feature crece demasiado, divídela (por ejemplo `004` en validación, transformación y escritura transaccional). Si el tiempo aprieta (quedan ~18 días desde el 1-nov), **fusiona** features pequeñas: `001`+`002`; `008`+`009`; `010`+`011`+`012`; `014`+`015`. Mejor menos ciclos completos que ciclos a medias.
- La documentación (memoria, README, `CODEMAP.md`) **no espera a `017`**: cada feature deja su parte al cerrarse (apartado 6, paso 9). El apartado de calidad (C14) se prepara en `notebooks/` durante `004`–`006`.
- Pasos sin feature: F0 (andamiaje, a mano, §2 paso 0), F1 (script `scripts/explore_usgs.py` de exploración de USGS y lectura del contrato) y F13 (a mano, `017` solo organiza la memoria).

### 4.1 Los tres contratos (feature `001`)

`specs/001-contratos-y-modelo/contracts/` contiene:

| Contrato | Entre quién y quién | Base de partida |
|---|---|---|
| `kafka-message.md` | Productor → consumidor | Mensaje del roadmap §1 (`source`, `mode`, `ingested_at`, `replay_at`, `event`; clave = `event.id`) |
| `db-schema.md` | Consumidor → API | Esquema SQL del roadmap §1 (`current_event`, `event_version`, `quarantine`, `exclusion`, tablas de ingesta) |
| `api.md` | API → panel | `docs/enunciado/CONTRATO-API.md` del profesor (contrato **mínimo**), ampliado con las decisiones propias de abajo |

Lo que el contrato mínimo del profesor **no define** y se decide en `api.md`:
1. Forma exacta de la respuesta de `GET /api/salud` y `GET /api/estadisticas` (el profesor solo dice qué deben contener).
2. Mecanismo de paginación y límite máximo de puntos por respuesta.
3. Parámetro de modo (`mode=live|replay`) para el replay, y rango de fechas del histórico.
4. `country_name` en `properties` (sí está en el ejemplo del contrato) y cualquier campo adicional.

Regla: **el contrato se cambia antes que el código**. Si una feature necesita otro campo, se edita el contrato en `001`, se ejecuta `/speckit.analyze` (o revisión manual) y se ajustan las features afectadas. El `CONTRATO-API.md` del profesor no se modifica nunca.

### 4.2 Contenido mínimo de cada spec (semillas)

| Feature | Contenido mínimo |
|---|---|
| `contratos-y-modelo` | Mensaje Kafka, DDL, claves, grano, índices candidatos, `api.md` con las decisiones propias, modelo conceptual/lógico/físico (borrador) |
| `infra-compose` | Servicios, redes, volúmenes, healthchecks, variables de entorno, puertos expuestos, versiones de runtime |
| `productor-live` | Entradas/salidas, estado persistente, tabla de decisión id+updated, errores y backoff, formato de mensaje, retención de originales |
| `consumidor-idempotente` | Pipeline de validación, reglas de calidad, transacción y orden de commits, cuarentena, enrutado por `mode`, secuencia de la FAQ 12 |
| `geografia-pais` | Carga del catálogo, regla de frontera/empates, `NULL` = sin país, unicidad de `ADM0_A3` |
| `historico-2025` | Particionado temporal, manifiesto, dedup, carga, procedimiento de hueco >24 h |
| `api` | Endpoints, parámetros, esquemas de respuesta, errores, CORS, paginación/truncado |
| `panel-base-mock` (enmendada 10-nov-2026) | Adoptar el front externo con correcciones: proyecto React (Vite + TS + Tailwind, puerto 4200), `config.json` en tiempo de ejecución (`mode: mock|api`), mock con escenarios fuera del build de producción, globo `react-globe.gl`, leyenda de 5 clases, atribución visible, filtros, tabla, estadísticas y comparación, estado del feed y fallos, vista de replay sobre 2025, conexión con la API real. **Absorbe las cuatro filas siguientes.** |
| `panel-filtros-tabla` (absorbida por `panel-base-mock`) | Estado único de filtros, tabla, truncado, uso de `country_id`/`country_name` |
| `panel-graficos-comparacion` (absorbida por `panel-base-mock`) | Gráficos (hora UTC, país, distribuciones), comparación histórica |
| `panel-estado-fallos` (absorbida por `panel-base-mock`) | Estado del sistema, refresco sin solape, timeout, última lectura conservada, aviso de desactualizado |
| `panel-conexion-api` (absorbida por `panel-base-mock`) | Paso de mock a API real, contraste de respuestas, corrección de divergencias |
| `replay` | Selección, velocidad, aislamiento (topic y esquema), etiquetado y banner, casos controlados, selector de modo en el panel |
| `pruebas-aceptacion` | Las 11 pruebas con procedimiento y evidencia |
| `despliegue-tunel` | ngrok, Netlify, CORS, procedimiento de activación, pruebas del túnel |
| `mediciones-costes` | Operaciones, tamaños, métricas, procedimiento, costes |
| `memoria-defensa` | Índice de memoria, README, evidencias, recorrido de un evento, decisión propia |

Cada spec termina con **criterios de aceptación** copiados de los IDs del checklist que cubre.

---

## 5. Constitución (borrador para `/speckit.constitution`)

Pega esto como entrada del comando y deja que Spec Kit lo formatee. Sale de las reglas no negociables del roadmap y de las decisiones de este documento. Revísala línea a línea antes de aceptarla.

```
Principios del proyecto "Observatorio de actividad sísmica":

Datos y consistencia
1. Procesamiento al menos una vez con escritura idempotente (restricciones únicas + upsert). El offset de Kafka se confirma después del commit en PostgreSQL.
2. Una versión con "updated" menor o igual nunca sustituye a una mayor. Un evento = una fila actual.
3. Los tiempos de USGS están en milisegundos Unix: se convierten a UTC conservando el original.
4. El país se obtiene por punto dentro de polígono (EPSG:4326, ADM0_A3), nunca del texto "place". Sin polígono = NULL = "Sin país asignado".
5. No se rellenan nulos con 0. Magnitud o profundidad negativas no se rechazan solo por serlo.
6. Los datos inválidos van a cuarentena con motivo y referencia al original; no se pierden ni bloquean la cola.
7. Los datos sintéticos y de mock se etiquetan y se mantienen separados de los reales.
8. Las agregaciones se calculan desde la tabla de estado actual, nunca con contadores por mensaje.

Infraestructura y seguridad
9. Entre contenedores se usan nombres de servicio, nunca localhost.
10. Solo la API se expone. Sin secretos en Git ni en el frontend. .env.example siempre actualizado.
11. Dependencias y versiones de runtime (Python, Node, React/Vite) fijadas (requirements/lock y package-lock).
12. No ampliar alcance: sin Spark, Flink, Kubernetes, ML, informes de calidad automáticos ni panel de calidad.

Código
13. Identificadores en inglés (funciones, variables, archivos de código, tablas, columnas, topics); docstrings, comentarios y documentación en español. Excepción: rutas y campos fijados por el contrato del profesor (/api/eventos, country_id, country_name…).
14. Una función hace una sola cosa. La lógica pura (validar, transformar) está separada del I/O (BD, Kafka, HTTP).
15. Los contratos (mensaje Kafka, esquema de BD, API) viven en specs/001-contratos-y-modelo y no se duplican. El contrato mínimo del profesor en docs/enunciado no se modifica.
16. Cada feature termina con prueba ejecutada, evidencia guardada, README y CODEMAP.md actualizados.

Frontend
17. El frontend no calcula estadísticas: muestra lo que devuelve la API. Un único estado de filtros compartido por mapa, tabla y gráficos. Los datos del mock son sintéticos y están etiquetados.

Documentación y proceso
18. docs/enunciado/ es solo lectura. Si el enunciado choca con la implementación, se corrige la implementación o se consulta al profesor. specs/ (herramienta) no se copia tal cual a docs/ (entregables).
19. Una feature cada vez. No se implementa sin spec, plan y tareas revisados por el alumno. Al terminar una feature, el agente se detiene y espera revisión; no hace commits ni merges sin aprobación.

Git
20. Commits con mensajes descriptivos. Sin trailers Co-Authored-By ni líneas de "generado por" herramientas de IA, ni en commits ni en PRs.

Lenguaje de resultados
21. Sin lenguaje de predicción ni de riesgo en conclusiones.
```

---

## 6. Ciclo de trabajo de cada feature

Es el procedimiento que repites en cada feature. Los pasos 1–6 son planificación, 7 es construcción, 8–10 son cierre.

| # | Paso | Cómo | Salida |
|---|---|---|---|
| 1 | Rama | `/speckit.specify` la crea (`NNN-nombre`) o la creas tú | Rama limpia desde `main` |
| 2 | Especificar | `/speckit.specify` con el **qué y el porqué**, sin tecnologías. Incluye los IDs del checklist que cubre | `spec.md` |
| 3 | Aclarar | `/speckit.clarify` (si tu versión lo trae). Responde tú las preguntas: son las decisiones que dices que quieres tomar | `spec.md` sin ambigüedades |
| 4 | Planificar | `/speckit.plan` con el stack fijado y la ruta de los contratos | `plan.md`, `data-model.md`, `quickstart.md` |
| 5 | Tareas | `/speckit.tasks` | `tasks.md` |
| 6 | Revisar | `/speckit.analyze` (si existe) y **lectura tuya** del plan y las tareas | Incoherencias resueltas |
| 7 | Implementar | `/speckit.implement`. Mejor por bloques de tareas que todo de golpe; si tu versión trae `/speckit-converge`, úsalo después para comprobar | Código + tests |
| 8 | Verificar | Ejecutar las pruebas de la feature y guardar la evidencia en `docs/evidencias/<feature>/` | SQL, logs o capturas |
| 9 | Documentar | Actualizar `CODEMAP.md`, el README (si cambia la ejecución) y el borrador de la memoria (`docs/memoria.md`) | Docs al día |
| 10 | Cerrar | Marcar IDs en el checklist, commit descriptivo (revisado), merge a `main` | Feature terminada |

### Plantilla de prompt para `/speckit.specify`

```
Feature: <nombre>
Objetivo: <qué debe poder hacer el sistema al terminar, en una frase>
Requisitos del checklist que cubre: <IDs, p. ej. C1–C5, C8>
Contratos que usa (no redefinir): specs/001-contratos-y-modelo/contracts/<archivo>
Fuente de requisitos (solo lectura): docs/enunciado/<archivo y apartado>
Fuera de alcance: <qué NO entra en esta feature>
Criterios de aceptación: <pruebas de aceptación que debe pasar y cómo se comprueban>
```

### Plantilla de prompt para `/speckit.plan`

```
Stack: Python (versión fijada en esta feature), aiokafka, FastAPI, PostgreSQL, Docker Compose; en el frontend, React + TypeScript + Vite + Tailwind (versiones estables vigentes, fijadas en el plan de panel-base-mock) + `react-globe.gl` (o la librería de mapa confirmada en panel-base-mock) + TanStack Query + Chart.js.
Estructura: respeta la del repositorio (CODEMAP.md) y las reglas de código de la constitución (identificadores en inglés, docstrings en español).
Contratos: usa los de specs/001-contratos-y-modelo/contracts/; si hace falta cambiarlos, indícalo en el plan antes de tocar código.
```

### Regla de oro para ti

Después del paso 6 y antes del 7, **para**: lee `plan.md` y `tasks.md`. Si no sabes explicar con tus palabras qué va a pasar, pregunta a Claude hasta entenderlo. Esa es la forma de "dirigir" y no solo recibir código.

---

## 7. Organización del código

### 7.1 Estructura por servicio (esqueleto, no obligatorio al milímetro)

```
common/
  config.py          # lectura de variables de entorno
  logging_setup.py   # configuración de logs
  models.py          # estructuras de datos: mensaje, evento, versión
  validation.py      # reglas de validación (funciones puras)
  timeutils.py       # ms Unix <-> UTC
  geo.py             # catálogo de países y asignación por polígono
  db.py              # conexión y transacciones
  processing.py      # process_event(): lógica única compartida (consumidor, histórico, replay)

producer/
  main.py            # solo arranque y bucle
  usgs_client.py     # GET al feed con timeout y reintentos
  ingest_state.py    # lectura/escritura del estado persistente
  publisher.py       # envío a Kafka y espera de confirmación
  replay.py          # modo replay

consumer/
  main.py            # solo arranque y bucle de consumo
  pipeline.py        # orquesta validar -> transformar -> enriquecer -> escribir
  writer.py          # transacción y upsert

api/
  main.py            # creación de la app, CORS
  routers/           # events.py, health.py, stats.py
  schemas.py         # modelos de respuesta
  queries.py         # consultas SQL de lectura

scripts/
  explore_usgs.py
  download_historical.py
  load_historical.py
```

### 7.2 Separar lo puro de lo que toca el exterior

| Tipo | Ejemplos | Característica | Cómo se prueba |
|---|---|---|---|
| **Lógica pura** | validar coordenadas, convertir tiempos, decidir si publicar, comparar versiones | Entra un dato, sale un dato, sin red ni BD | Test unitario directo |
| **I/O (adaptadores)** | consulta HTTP, publicar en Kafka, escribir en PostgreSQL | Toca el exterior | Test de integración o con simulación |

Esto es lo que más ayuda a entender el código: la decisión importante (por ejemplo, "¿esta versión es más reciente?") está en una función pequeña que se lee de una vez, separada del código de conexión.

### 7.3 Reglas para funciones y archivos

1. **Una función, una responsabilidad.** Si necesitas la palabra "y" para describirla, son dos funciones.
2. **Tamaño orientativo:** función ≤ ~30 líneas; archivo ≤ ~250 líneas. Si se pasa, hay que justificar o dividir.
3. **Pocos parámetros:** hasta 4. Más, agrúpalos en un objeto (dataclass o modelo Pydantic).
4. **Nombres que se leen solos:** verbo + objeto (`is_newer_version`, `assign_country`, `to_utc`). Nada de `process`, `handle`, `data`, `tmp`.
5. **`main.py` no contiene lógica.** Solo configura y arranca.
6. **Sin números ni textos mágicos.** Umbrales, nombres de topic y tiempos van a `config.py` o a constantes con nombre.
7. **Tipos en todas las funciones públicas** (type hints).
8. **Errores explícitos.** Excepciones con nombre (`InvalidCoordinatesError`). Prohibido `except Exception: pass`.
9. **Logging, no `print`.** Cada decisión relevante (publicado, omitido, cuarentena, error) deja una línea de log con el `event_id`.
10. **SQL en archivos** (`sql/`) o en `queries.py`, no esparcido en cadenas por el código.
11. **Nada duplicado entre servicios:** si dos servicios necesitan lo mismo, va a `common/`.
12. **Tests espejo:** `tests/consumer/test_validation.py` prueba `common/validation.py`. Nombre: `test_<regla>_<caso>`.

### 7.4 Plantilla de docstring (español)

```python
def is_newer_version(incoming_updated_ms: int, stored_updated_ms: int | None) -> bool:
    """Decide si una versión recibida debe sustituir al estado actual.

    Qué hace:
        Compara el `updated` entrante con el guardado. Solo gana si es estrictamente mayor.
    Recibe:
        incoming_updated_ms: `updated` de la versión recibida (ms Unix).
        stored_updated_ms: `updated` guardado, o None si el evento no existe.
    Devuelve:
        True si hay que actualizar; False si es igual o más antigua.
    Por qué existe:
        Evita que una versión antigua que llega tarde pise a la reciente (C4, prueba 4).
    """
```

Reglas del docstring: siempre incluye **por qué existe** y el **ID del checklist** cuando aplique. Los comentarios `#` explican el motivo de una decisión, no repiten lo que hace la línea.

### 7.5 React (frontend, desde cero)

```
frontend/
  public/config.json     # mode (mock|api), apiBaseUrl, refreshSeconds, timeoutMs. Sin secretos
  public/datos/          # paises.geojson (copia verificada con SHA-256)
  mock/                  # JSON conforme al contrato y servidor simulado (backend.ts); SINTÉTICO, solo desarrollo, fuera del build de producción
  scripts/               # generate-mock.mjs, copy-countries.mjs
  tests/                 # Vitest
  src/                   # estructura del front externo (decisión del alumno, 10-nov-2026)
    main.tsx, App.tsx, index.css
    components/          # GlobeView, filtros, tabla, estadísticas, estado, avisos, ficha, leyenda, atribución
      mobile/            # diseño móvil (< 1024 px)
    shared/
      api/               # cliente HTTP, construcción de la petición (pura), parseo (puro) y origen de datos
      hooks/             # useObservatory (TanStack Query), useCountries, useMediaQuery, useNow
      lib/               # format, symbology, appearance, color, tokens, feedHealth, validateConfig
      types/             # contract.ts
    store/               # store único de filtros (Zustand)
```

- Un único store de filtros compartido (G6), no uno por componente.
- `shared/` no importa de `components/`; `components/` usa `shared/` y `store/`. Solo `GlobeView` importa la librería del globo y `three`.
- Los componentes muestran; el cálculo vive en la API (el frontend no calcula estadísticas).
- El mapa vive en un componente aislado (entrada: lista de eventos; salida: evento seleccionado) para poder cambiar de librería.
- Mock fiel al contrato, con casos límite: magnitud nula, sin país, truncado, modo replay, intervalo vacío.
- `paises.geojson` se copia a los assets desde `data/catalogo/` (material reutilizado, documentado; comprobar el SHA-256 de `FUENTES-Y-LICENCIAS.md`).
- Mismo criterio de nombres: un componente por responsabilidad, comentarios en español.

### 7.6 `CODEMAP.md` (plantilla)

Es el índice que te dice qué archivo mirar para cada cosa. **Se actualiza al cerrar cada feature** (paso 9).

```markdown
# Mapa del código

## Dónde está cada cosa
| Quiero entender… | Mira… | Requisito |
|---|---|---|
| Cómo se decide qué se publica | producer/ingest_state.py, producer/main.py | B6 |
| Qué versión gana | common/processing.py::is_newer_version | C4 |
| Cómo se asigna el país | common/geo.py | C9–C12 |
| Qué va a cuarentena y por qué | common/validation.py, consumer/writer.py | C5 |
| Qué devuelve la API de eventos | api/routers/events.py, api/queries.py | F1–F3 |
| Cómo el panel consume la API | frontend/src/app/core/api.service.ts | G1, G9 |

## Flujo de un evento (de USGS al mapa)
USGS -> producer/usgs_client.py -> producer/publisher.py -> Kafka
     -> consumer/pipeline.py -> common/validation.py -> common/geo.py
     -> consumer/writer.py -> PostgreSQL -> api/queries.py -> frontend/features/map

## Convenciones
(Resumen de 5 líneas de las reglas del apartado 7.3)

## Historial de features cerradas
| Feature | Qué añadió | Fecha |
|---|---|---|
```

Úsalo también para la defensa oral (H5): el recorrido de un evento ya está escrito.

---

## 8. Procedimiento de ejecución del sistema (borrador para el README)

Es un borrador. Los nombres exactos de scripts y variables se fijan al implementar `002`, `006`, `013` y `015`; el README final debe reflejar lo que de verdad funcione desde un clon limpio (M3).

### 8.1 Primera vez

```bash
git clone <repo> && cd observatorio-sismico
cp .env.example .env            # rellenar valores locales; nunca subir .env
docker compose up --build -d
docker compose ps               # los cinco servicios deben estar "healthy"
```

### 8.2 Cargar el histórico (una vez)

```bash
python scripts/download_historical.py     # genera data/raw/ y manifest.json (consultas, fechas, nº registros)
python scripts/load_historical.py         # carga en PostgreSQL usando la lógica compartida; repetible sin duplicar
```

### 8.3 Comprobar que hay ingesta

```bash
docker compose logs -f producer          # un ciclo cada ~60 s
docker compose logs -f consumer
curl http://127.0.0.1:8000/api/salud     # estado y última ingesta
```

### 8.4 Activar el panel para la defensa (H2)

1. Compose arriba y datos cargados (8.1 y 8.2).
2. Túnel: `ngrok http 8000` (en el equipo) o `ngrok http http://api:8000` (en contenedor). El authtoken solo en tu configuración local de ngrok.
3. Poner la URL HTTPS de ngrok en `frontend/public/config.json` (con `mode: api`).
4. Compilar y publicar en Netlify (directorio base `frontend`; directorio de publicación `frontend/dist`, comando `npm run build`; `netlify.toml` con la regla de SPA `/* /index.html 200`).
5. Comprobar CORS con el origen exacto de Netlify.
6. Abrir el panel desde otro dispositivo.
7. Si usas un dominio ngrok que cambia, repetir 3–4 en cada sesión.

### 8.5 Replay para la demo

```bash
# comando definitivo se fija en la feature replay
docker compose run --rm producer python -m producer.replay --interval 2
```

El panel debe mostrar el banner "REPRODUCCIÓN" y los datos live no deben cambiar.

### 8.6 Parar

```bash
docker compose down        # conserva datos (volúmenes)
docker compose down -v     # BORRA los volúmenes: solo si quieres empezar de cero
```

Qué persiste: PostgreSQL (volumen) y los archivos de `data/raw/`. Qué se regenera: todo lo demás.

---

## 9. `CLAUDE.md` (contenido sugerido, corto)

Claude Code lo lee en cada sesión. Mantenlo breve y apunta a lo demás.

```markdown
# Observatorio sísmico — instrucciones para el agente

- Lee `.specify/memory/constitution.md` antes de cualquier cambio: son las reglas no negociables.
- Los contratos están en `specs/001-contratos-y-modelo/contracts/`. No los dupliques ni los cambies sin avisar.
- `docs/enunciado/` es SOLO LECTURA (material del profesor). No lo modifiques.
- Procedimiento y reglas de código: `docs/planificacion/03-procedimiento-ejecucion.md` (plantilla de docstring en §7.4). Orden de fases: `02-roadmap-implementacion.md`. Requisitos: `01-checklist-requisitos.md`.
- Identificadores en inglés; docstrings y comentarios en español.
- Antes de crear un archivo nuevo, consulta `CODEMAP.md` y úsalo para decidir dónde va.
- Una feature cada vez. No implementes sin spec, plan y tareas revisados. Al terminar una feature, detente y espera revisión; no hagas commits ni merges sin aprobación.
- Al terminar una tarea: tests ejecutados, evidencia en `docs/evidencias/`, `CODEMAP.md` actualizado.
- El frontend no calcula estadísticas: muestra lo que devuelve la API. Los datos de mock son sintéticos y van etiquetados.
- Nunca añadas trailers Co-Authored-By ni líneas de "generado por" en commits o PRs.
- No amplíes el alcance: nada fuera de lo que pide la spec de la feature activa.
```

---

## 10. Relación con los otros documentos (ya reconciliados)

| Documento | Estado |
|---|---|
| `01-checklist-requisitos.md` | Contiene la trazabilidad ID → feature (§7 del checklist) y los requisitos de frontend desde cero (G0–G16). Es un resumen derivado del enunciado |
| `02-roadmap-implementacion.md` | Cada fase indica su feature. Sus "semillas de spec" se han movido al §4.2 de este documento. Su §0 remite a la constitución para las reglas |
| Este documento | Fuente de verdad del proceso, las features y las reglas de código (ver tabla de fuente de verdad en §0) |

Si algún día un documento discrepa de otro, aplica la tabla de §0 y corrige el derivado el mismo día.

---

## 11. Orden de arranque recomendado (resumen)

1. **Paso 0 (a mano):** andamiaje, documentación en `docs/`, catálogo en `data/catalogo/`, primer commit (apartado 2).
2. Instalar Spec Kit, inicializar, escribir la constitución (apartado 5), `CLAUDE.md` (apartado 9), `CODEMAP.md` vacío (apartado 7.6) y la configuración de atribución de Git (apartado 2). Script `scripts/explore_usgs.py` (F1) y lectura completa de `CONTRATO-API.md`.
3. Feature `001-contratos-y-modelo`: es la que más decisiones tuyas contiene.
4. `002` → `003` → `004` → `005`: el pipeline extremo a extremo con datos reales. `006` en paralelo.
5. `008` (panel contra mock) puede empezar en cuanto exista `002`; luego `009` → `010` → `011`, y `007` (API) en paralelo; `012` conecta panel y API.
6. `013` a `017`.

Prioridad si falta tiempo (del roadmap §5): pipeline correcto → pruebas → memoria. Los extras no puntúan. Ver el calendario orientativo del roadmap §5.
