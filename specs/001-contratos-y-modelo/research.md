# Investigación y decisiones técnicas (Fase 0)

No quedan marcadores `NEEDS CLARIFICATION`. Las decisiones de la sección Clarifications de `spec.md` se respetan y no se reabren. Esta tabla recoge las decisiones **del plan**; las que la spec dejaba sin decidir fueron aprobadas por el alumno el 2026-11-02 y figuran como **DECIDIDO**.

## R1. Versión de Python

- **Decisión:** Python **3.12** para productor, consumidor, API y scripts.
- **Justificación:** versión estable con ruedas (wheels) disponibles para las dependencias previstas; `uv` puede instalarla y fijarla en `.python-version`. En el equipo del alumno hay Python 3.13.5, que no se usa para el proyecto: se evita depender de la versión instalada en el sistema (constitución §11).
- **Alternativas:** 3.11 (mínimo del roadmap, más antigua); 3.13 (más nueva, menos madura para geopandas/shapely/aiokafka).
- **Pendiente para otras features:** el archivo `.python-version`, `requirements`/lock y la imagen Docker se crean en `infra-compose`.

## R2. Versiones del resto del stack

- **Decisión:** aiokafka, FastAPI, PostgreSQL 16 y Kafka en modo KRaft (imagen oficial de Apache). Esta feature fija la **línea mayor**; la versión exacta se fija junto a cada dependencia en `infra-compose` y en cada feature que la use (constitución §11).
- **Justificación:** esta feature no ejecuta código ni arranca servicios; fijar aquí un parche exacto sin poder probarlo sería arbitrario.
- **Frontend:** fuera de esta feature. No se fijan librerías de mapas ni de gráficos; se decidirán en `panel-base-mock`.

## R3. Una sola forma de escribir los esquemas `live` y `replay`

- **Decisión:** el DDL repite las cuatro tablas de eventos para `live` y `replay` de forma explícita (sin bucle `DO $$`).
- **Justificación:** legible para quien evalúa (E2, E5) y fácil de buscar. El riesgo de que diverjan se cubre en `quickstart.md` con una comprobación de columnas idénticas.
- **Alternativa:** generar ambos con un bloque `DO` y `format()`: garantiza igualdad pero oculta el DDL.

## R4. Vocabulario de `source`

- **Decisión:** la columna `source` de la base usa los mismos tres valores que el mensaje Kafka (`usgs_feed`, `usgs_historical`, `replay_demo`).
- **Justificación:** el roadmap proponía dos vocabularios (`feed | historical | replay` en BD y `usgs_feed | usgs_historical | replay_demo` en el mensaje); uno solo evita una tabla de traducción.

## R5. Marca de sintético en el mensaje — DECIDIDO

- **Decisión:** el mensaje Kafka lleva `is_synthetic` (booleano obligatorio).
- **Justificación:** sin ese campo, un evento sintético y uno real tendrían el mismo mensaje y el consumidor no podría cumplir la constitución §7. Es un campo añadido respecto al roadmap §1.
- **Alternativa:** deducirlo de `source`: no sirve para eventos sintéticos en modo `live` (p. ej. el evento ficticio de `infra-compose`).

## R6. Historial: clave foránea diferida

- **Decisión:** `event_version.event_id` referencia `current_event.event_id` con `DEFERRABLE INITIALLY DEFERRED`.
- **Justificación:** declara la relación (E2) sin imponer un orden de inserción dentro de la transacción del consumidor (versión primero, luego estado actual).

## R7. Idempotencia de la cuarentena y de las exclusiones

- **Decisión:** `quarantine` es única por `(original_sha256, reason)` y `exclusion` por `(event_id, updated_ms, kind)`.
- **Justificación:** el consumo es «al menos una vez» (constitución §1) y el feed repite los mismos eventos cada minuto; sin restricciones únicas, un reintento o una nueva consulta duplicarían filas.
- **Consecuencia:** dos mensajes distintos con el mismo contenido inválido y el mismo motivo comparten una fila de cuarentena (el offset guardado es el del primero).

## R8. Rangos de cordura en `CHECK`

- **Decisión:** `mag` entre −10 y 15, `depth_km` entre −100 y 1000, `lon`/`lat` en su rango geográfico — **DECIDIDO** (aprobado por el alumno el 2026-11-02).
- **Justificación:** `numeric` y `double precision` aceptan `NaN` e infinitos, que el contrato de la API prohíbe. Un `BETWEEN` los rechaza sin descartar negativos (constitución §5). Los valores observados (mag −0,06…6; profundidad −0,18…377,9) caben con holgura.
- **Validación previa:** el consumidor valida estos límites antes de insertar y manda a cuarentena lo que no los cumpla (`mag_out_of_range`, `depth_out_of_range`, `invalid_field_type`, `value_out_of_range`, `replay_at_missing`); el `CHECK` es la última barrera: si aun así la base rechaza el `INSERT`, se aplica el motivo de último recurso `db_constraint_violation` (rollback del mensaje, cuarentena y offset confirmado, sin bloquear la cola). Un mensaje genera una sola fila, con el primer motivo según el orden de prevalencia de `kafka-message.md` §6.
- **Alternativa:** sin `CHECK` y validar solo en el consumidor: más flexible, pero la base no se protege.

## R9. Conversión de tiempos comprobada en la base

- **Decisión:** `CHECK (event_time = timestamptz 'epoch' + event_time_ms * interval '1 millisecond')` y equivalente para `updated`, más `date_id` = día UTC de `event_time`.
- **Justificación:** hace imposible guardar un instante convertido que no corresponda al original en ms (constitución §3, E7).

## R10. Tabla `date_dim` y catálogo

- **Decisión:** el DDL crea `country` y `date_dim` vacías. El consumidor (`consumidor-idempotente`) carga el catálogo de países desde `data/catalogo/paises.geojson` (campos `ADM0_A3`→`country_id`, `NAME_ES`→`name_es`, `ADMIN`→`admin`, `CONTINENT`→`continent`, `SUBREGION`→`subregion`) e inserta cada día de evento si no existe.
- **Comprobado:** el archivo tiene 177 entidades; `ADM0_A3` único, tres letras mayúsculas en las 177; `NAME_ES`, `ADMIN`, `CONTINENT` y `SUBREGION` sin nulos. Por eso esas cinco columnas son `NOT NULL`. El archivo no se modifica.
- **Nota:** `CONTINENT` incluye el valor `Seven seas (open ocean)`; no afecta al esquema.

## R11. Paginación por cursor tipo «keyset»

- **Decisión:** el cursor codifica `(event_time_ms, id)` del último evento devuelto y se resuelve con `(event_time, event_id) < (:t, :id)` en orden descendente, apoyado en `ix_current_event_time`. Sentido descendente y nombres (`limit`, `cursor`, `total`, `next_cursor`) — **DECIDIDO**.
- **Justificación:** coste constante por página y orden estable aunque lleguen revisiones; el desplazamiento (`OFFSET`) se degrada con páginas profundas y no es estable si cambian los datos.

## R12. Comparación histórica con M ≥ 4 — DECIDIDO

- **Decisión:** la comparación usa `max(min_mag solicitado, 4.0)` en las últimas 24 h y en 2025, y lo declara en `comparison.min_mag_applied`.
- **Justificación:** el histórico cargado es de M ≥ 4 (roadmap F6) y el enunciado §8 compara «magnitud ≥ 4». Sin ese umbral la variación compararía poblaciones distintas.
- **Relación con la aclaración:** concreta «con los filtros pedidos» añadiendo el mínimo de 4; aprobado por el alumno el 2026-11-02.

## R13. Comprobación del DDL en esta feature

- **Hecho:** el 2-nov-2026 `sql/001_schema.sql` se aplicó dos veces sin errores en PostgreSQL 16 y se probaron sus restricciones, las reglas de versiones y el aislamiento `live`/`replay` (evidencia: `docs/evidencias/contratos-y-modelo/prueba_esquema_001.sql`). `infra-compose` debe usar PostgreSQL 16.
- **Pendiente:** la comprobación en `consumidor-idempotente` se mantiene como prueba de integración (E5).
- **Reproducción:** `quickstart.md` describe cómo repetirla en un PostgreSQL desechable.
