# Glosario y nomenclatura — Observatorio de actividad sísmica

Chuleta para tener a mano. Explica qué significa cada sigla, ID y término que aparece en `01-checklist-requisitos.md`, `02-roadmap-implementacion.md` y `03-procedimiento-ejecucion.md`.

> **Entrega: 19 de noviembre de 2026 · trabajo individual.**

---

## 0. Lo primero: las cuatro cosas que más se confunden

| Palabra | Qué es | Ejemplo | Dónde vive |
|---|---|---|---|
| **Requisito** | Algo que hay que **cumplir**. Va con letra + número | `B6`, `C4`, `G2` | `01-checklist` |
| **Fase** | Un **paso del orden de trabajo**. Va con `F` + número | `F1`, `F3`, `F8a` | `02-roadmap` |
| **Feature** | Un **ciclo completo de Spec Kit** que ejecuta una fase. Va con nombre | `consumidor-idempotente` | `03-procedimiento` y carpeta `specs/` |
| **Prueba** | Uno de los **11 casos de aceptación**, numerados | prueba 4 | bloque I del checklist |

```
Requisito  ->  qué hay que cumplir          (B6: guardar el estado de ingesta)
Fase       ->  en qué orden se hace         (F4: productor real)
Feature    ->  cómo se construye con Spec Kit (productor-live)
Prueba     ->  cómo se demuestra que funciona (prueba 2: reenviar la misma versión)
```

> ⚠️ **"F1" puede ser dos cosas distintas.**
> - **Fase F1** = explorar USGS (roadmap).
> - **Requisito F1** = `GET /api/eventos` (bloque F, la API, del checklist).
>
> Al hablar con Claude Code escribe siempre **"fase F1"** o **"requisito F1 (API)"**.

---

## 1. Requisitos: cómo leer un ID

```
   B 6
   │ └── número dentro del bloque (el sexto requisito)
   └──── bloque (B = Extracción e ingesta)
```

Un rango como `C1–C8` significa "del C1 al C8, ambos incluidos".

### Bloques

| Bloque | De qué trata | Ejemplos |
|---|---|---|
| **A** | Arquitectura y Docker | A1 los 5 servicios · A8 solo se expone la API |
| **B** | Extracción e ingesta (productor e histórico) | B6 estado persistente · B13 histórico por meses |
| **C** | Consumidor, calidad y país | C4 versión antigua no pisa a la nueva · C9 país por polígono |
| **D** | Las 6 dimensiones de calidad (no tiene IDs) | completitud, unicidad, validez, consistencia, actualidad, exactitud |
| **E** | Modelo de datos y SQL | E1 modelo conceptual, lógico y físico |
| **F** | API FastAPI | F1 `/api/eventos` · F8 error explícito si cae la BD |
| **G** | Panel React | G2 mapa · G5 comparación histórica |
| **H** | Despliegue y vídeo | H2 procedimiento de activación · H5 vídeo de 5 min |
| **I** | Las 11 pruebas de aceptación | numeradas 1 a 11 |
| **J** | Replay (reproducción histórica) | J4 etiqueta "REPRODUCCIÓN" |
| **K** | Complejidad, mediciones y costes | K5 razonar con 100 millones de registros |
| **L** | Índice del README (secciones 1 a 10) | 1 a 10 |
| **M** | Repositorio | M7 historial sin trailers de coautoría |

### Etiquetas

| Etiqueta | Significa |
|---|---|
| **[OBL]** | Obligatorio |
| **[EVAL]** | Puntúa en la rúbrica |
| **[OPC]** | Opcional (no hacerlo si falta tiempo) |
| **[?]** | Ambiguo: confirmar con el profesor |

### Los 5 criterios de nota

| Criterio | Qué mira |
|---|---|
| Extracción | Carga de datos y análisis de tipos |
| Calidad | Análisis completo y acciones tomadas |
| Modelado | Modelo optimizado, claves, índices, país por polígono |
| Análisis | Gráficos, comparación histórica, ≥ 3 conclusiones |
| Reflexión | Complejidad, mediciones, costes, mejoras |

Más infraestructura **no** da más nota. Prioridad si falta tiempo: pipeline correcto → pruebas → memoria.

---

## 2. Fases (roadmap) y su feature de Spec Kit

Cada fase la ejecuta una feature. En los prompts usa el **nombre**, no el número: Spec Kit numera por orden de creación y el número puede cambiar.

| Fase | Qué es | Feature (nombre) | Requisitos que cubre |
|---|---|---|---|
| **F0** | Repo, docs y Spec Kit, a mano | — | M1, M5–M9 |
| **F1** | Explorar USGS y leer el contrato | — (script suelto) | B2 |
| **F1b** | Contratos y modelo de datos | `contratos-y-modelo` | E1–E5, E7 |
| **F2** | Docker Compose base | `infra-compose` | A1–A12 |
| **F3** | Consumidor idempotente | `consumidor-idempotente` | C1–C8, C13 |
| **F4** | Productor real | `productor-live` | B1–B12 |
| **F5** | País y calidad | `geografia-pais` | C9–C12 |
| **F6** | Histórico 2025 | `historico-2025` | B13–B18 |
| **F7** | API | `api` | F1–F12 |
| **F8a** | Panel: esqueleto y mapa con mock | `panel-base-mock` | G0, G2, G11, G14, G15 |
| **F8b** | Panel: filtros y tabla | `panel-filtros-tabla` | G6, G8, G16 |
| **F8c** | Panel: gráficos y comparación histórica | `panel-graficos-comparacion` | G3, G4, G5, G5b |
| **F8d** | Panel: estado del sistema y fallos | `panel-estado-fallos` | G7, G9 |
| **F8e** | Panel: conexión a la API real | `panel-conexion-api` | G1 |
| **F9** | Replay | `replay` | J1–J8, G10 |
| **F10** | Pruebas de aceptación | `pruebas-aceptacion` | bloque I |
| **F11** | Túnel (Cloudflare Tunnel) y Netlify | `despliegue-tunel` | G13, H1–H4 |
| **F12** | Mediciones y costes | `mediciones-costes` | K1–K8, E6 |
| **F13** | README final, guion y vídeo | `readme-video` | bloque L, H5, M10 |

> Ojo al orden: **F3 es el consumidor** y su feature es la `003`; **F4 es el productor** y su feature es la `004`. Conviene usar siempre el nombre.

### Calendario orientativo

| Días | Trabajo |
|---|---|
| 1–3 nov | F0, F1, F1b, F2 |
| 4–7 nov | F4, F3, F5 (y F6 en paralelo) |
| 8–11 nov | F7, F8a, F8b |
| 12–15 nov | F8c, F8d, F8e, F9 |
| 16–17 nov | F10, F12; README en continuo |
| 17–18 nov | Grabar el vídeo de 5 min |
| 19 nov | Entrega |

Si el tiempo aprieta, se fusionan features pequeñas y se recorta lo no obligatorio. Nunca se recortan las pruebas de aceptación, el README ni el vídeo.

---

## 3. Las 11 pruebas de aceptación (bloque I)

| # | Prueba | Debe pasar así |
|---|---|---|
| 1 | Evento nuevo | 1 fila actual visible en API, mapa y análisis |
| 2 | Reenviar la misma versión | El recuento no aumenta |
| 3 | Versión posterior | Cambian los datos actuales |
| 4 | Versión antigua tardía | No sustituye a la reciente |
| 5 | Magnitud nula | Se conserva y se ve como **ND** |
| 6 | Coordenadas inválidas | Va a cuarentena con motivo |
| 7 | Evento marítimo | "Sin país asignado", sigue en el análisis |
| 8 | Reiniciar el consumidor | Reanuda sin duplicar |
| 9 | Cerrar el túnel | El panel avisa y conserva la última lectura |
| 10 | Reabrir el túnel | Se recupera solo en el siguiente refresco |
| 11 | Reproducción histórica | Aislada, etiquetada, con duplicados y revisiones |

---

## 4. Secciones de la memoria (`docs/memoria.md`)

| § | Contenido | Se rellena en |
|---|---|---|
| 1 | Objetivo, flujo de datos y alcance | F13 (borrador antes) |
| 2 | Diccionario de datos | **F1** (ahora) |
| 3 | Procedencia y registro de consultas | F1, F6 |
| 4 | Calidad (consultas y antes/después) | F3, F5, F6 |
| 5 | Modelo conceptual, lógico y físico | F1b |
| 6 | Análisis y ≥ 3 conclusiones | F8c |
| 7 | Complejidad, mediciones y costes | F12 |
| 8 | Evidencias de las 11 pruebas | F10 |
| 9 | Reproducción histórica | F9 |
| 10 | Limitaciones | F13 |

Regla: **cada feature deja su parte escrita al cerrarse**; no se deja todo para el final.

---

## 5. Cómo se citan los documentos

| Escribes… | Significa |
|---|---|
| `01`, `02`, `03` | Los tres documentos de `docs/planificacion/` (checklist, roadmap, procedimiento) |
| `§` | Apartado. "03 §6" = apartado 6 del documento 03 |
| `Enunc. §4.2` | Apartado 4.2 del `ENUNCIADO.md` del profesor |
| `FAQ 12` | Pregunta 12 de `FAQ-ALUMNADO.md` |
| `Guía 2.3` | Apartado 2.3 de la guía de entregables |
| `rev. 3` | Revisión 3 del documento (la vigente, del 1-nov) |

### Si dos documentos se contradicen, manda este orden

```
1. Enunciado  >  2. Guía de entregables  >  3. FAQ
   (y el checklist es un resumen: si choca con el enunciado, gana el enunciado)
4. Constitución (reglas del proyecto)
5. Roadmap (orden de trabajo)
6. Documento 03 (cómo se trabaja)
```

---

## 6. Carpetas clave

| Carpeta o archivo | Para qué | ¿Se edita? |
|---|---|---|
| `docs/enunciado/` | Material del profesor | ❌ Solo lectura |
| `docs/planificacion/` | Estos documentos | ✅ |
| `docs/evidencias/` | Pruebas y resultados por feature | ✅ |
| `docs/memoria.md` | Entregable principal | ✅ |
| `specs/` | Specs, planes y tareas de Spec Kit (herramienta) | Lo genera Spec Kit |
| `.specify/` y `.claude/` | Herramientas | Solo la constitución y `settings.json` |
| `data/catalogo/paises.geojson` | Catálogo de países entregado | ❌ Sin modificar |
| `data/raw/` | Descargas regenerables | Fuera de Git |
| `CLAUDE.md` | Instrucciones para el agente | ✅ Breve |
| `CODEMAP.md` | Índice "qué archivo hace qué" (uno solo, en la raíz) | ✅ Al cerrar cada tarea con código |

---

## 7. Ciclo de trabajo de cada feature (Spec Kit)

```
specify -> clarify -> plan -> tasks -> analyze -> [PARAR Y LEER] -> implement -> verificar -> documentar -> cerrar
```

| Paso | Qué haces | Qué sale |
|---|---|---|
| 1. Rama | La crea `specify` o tú | Rama limpia desde `main` |
| 2. Specify | Qué y por qué, sin tecnologías, con los IDs del checklist | `spec.md` |
| 3. Clarify | Respondes las preguntas (si tu versión lo trae) | Spec sin ambigüedades |
| 4. Plan | Stack fijado y ruta de los contratos | `plan.md` |
| 5. Tasks | Lista de tareas | `tasks.md` |
| 6. Analyze | Revisión de incoherencias + **lectura tuya** | Plan y tareas revisados |
| 7. Implement | Por bloques de tareas | Código y tests |
| 8. Verificar | Ejecutar las pruebas de la feature | Evidencia en `docs/evidencias/<feature>/` |
| 9. Documentar | `CODEMAP.md`, README y memoria | Docs al día |
| 10. Cerrar | Marcar IDs en el checklist, commit **tuyo**, merge | Feature terminada |

> **Regla de oro:** antes de `implement`, lee `plan.md` y `tasks.md`. Si no sabes explicar con tus palabras qué va a pasar, pregunta hasta entenderlo.
>
> Según la versión de Spec Kit, los comandos se escriben `/speckit.xxx` (punto) o `/speckit-xxx` (guion). Usa el que veas al escribir `/speckit` en Claude Code.

---

## 8. Términos técnicos

| Término | Qué es |
|---|---|
| **Constitución** | Reglas no negociables del proyecto (`.specify/memory/constitution.md`) |
| **Spec / Plan / Tasks** | Qué y por qué / cómo se construye / lista de tareas |
| **Contrato** | Acuerdo exacto entre dos partes. Hay tres: mensaje Kafka, esquema de BD y API |
| **Mock** | Datos falsos de prueba, etiquetados como sintéticos, para desarrollar el panel sin backend |
| **Sintético** | Dato fabricado para pruebas; siempre separado e identificado, nunca mezclado con los reales |
| **Live / replay** | Datos en tiempo real / reproducción acelerada del histórico |
| **Idempotente** | Repetir la operación no cambia el resultado (reenviar un mensaje no duplica nada) |
| **Upsert** | Insertar, o actualizar si ya existe |
| **Al menos una vez** | Un mensaje puede llegar repetido, pero nunca se pierde; la idempotencia lo compensa |
| **Offset** | Posición de lectura en Kafka; se confirma **después** de guardar en la BD |
| **Ack** | Confirmación de Kafka de que recibió el mensaje |
| **Cuarentena** | Tabla donde van los datos inválidos, con motivo y referencia al original |
| **Estado actual / versión** | `current_event` = una fila por evento (la versión más reciente); `event_version` = todas las versiones recibidas |
| **ND** | "No disponible": cómo se muestra un valor nulo en el panel |
| **`ADM0_A3`** | Código de país de 3 letras (ej. `ESP`); es el `country_id` |
| **Punto en polígono** | Método para saber en qué país cae una coordenada |
| **ms Unix** | Fecha como milisegundos desde 1970; así vienen `time` y `updated` de USGS |
| **`time` / `updated`** | Cuándo ocurrió el evento / cuándo se revisó por última vez |
| **PG** | PostgreSQL |
| **CORS** | Permiso del navegador para que el panel (Netlify) consulte tu API (túnel) |
| **Backoff** | Esperar cada vez más entre reintentos tras un error |
| **SPA** | Aplicación web de una sola página (el panel React) |

---

## 9. Cómo pedirle algo a Claude Code

```
1. Qué quieres, en una frase.
2. Qué archivos lee y cuáles escribe (rutas exactas).
3. Qué NO debe hacer (no inventar datos, no tocar docs/enunciado/, no hacer commit).
4. Qué te devuelve (un resumen corto de lo que cambió).
```

- Fases sin feature (F0, F1): puedes decirle "ejecuta la fase F1 del roadmap". Pídele antes que te resuma el plan y espere tu "adelante".
- Fases con feature (F1b en adelante): **no** le pidas "haz la F2". Sigue el ciclo de la sección 7 y pídele que te redacte el texto de cada comando.
- Después de cada tarea: `git status`, `git diff`, y el commit lo haces tú.
