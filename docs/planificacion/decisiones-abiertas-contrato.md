# Decisiones abiertas del contrato de la API

Fuente: `docs/enunciado/CONTRATO-API.md` (solo lectura). Este documento solo recoge lo que el contrato deja sin definir. No decide nada: cada punto queda pendiente de resolver y de avisar antes de tocar los contratos de `specs/001-contratos-y-modelo/contracts/`.

## 1. GET /api/salud

- **Dice el contrato:** "Estado API y fecha de última ingesta; no credenciales".
- **Queda por decidir:**
  - Nombres y tipos de los campos de la respuesta (estado, fecha de última ingesta).
  - Valores posibles del estado (por ejemplo, qué significa "degradado").
  - Formato de la fecha de ingesta (el contrato fija milisegundos Unix UTC solo para `/api/eventos`; aquí no lo dice).
  - Si comprueba la base de datos y qué código HTTP devuelve cuando falla.
  - Qué valor lleva la fecha si todavía no ha habido ninguna ingesta.

## 2. GET /api/estadisticas

- **Dice el contrato:** "Conteos por hora UTC/país, distribuciones y comparación histórica". Los filtros "deben equivaler a los del mapa". Cada resultado "debe indicar periodo, filtros, unidad y registros sin valor". Si la base falla, "devuelve un error explícito; no cero eventos".
- **Queda por decidir:**
  - Estructura exacta de la respuesta y nombres de los campos.
  - Qué distribuciones se ofrecen (magnitud, profundidad u otras) y con qué intervalos.
  - Qué es la "comparación histórica": con qué periodo se compara y cómo se expresa.
  - Cómo se representan "periodo", "filtros", "unidad" y "registros sin valor".
  - Formato del error explícito (código HTTP y cuerpo).
  - Qué ocurre si se piden estadísticas sobre un conjunto que `/api/eventos` truncaría (el contrato dice que el panel no calcula estadísticas globales sobre una muestra truncada, pero no cómo las calcula la API).

## 3. Paginación y límite de puntos

- **Dice el contrato:** "la API puede aplicar un máximo documentado de puntos. Si trunca, debe indicar `truncated: true`, el total completo y un mecanismo de paginación".
- **Queda por decidir:**
  - Si se aplica un máximo o no, y su valor (el contrato solo dice "puede").
  - Mecanismo de paginación (offset/limit, cursor, enlaces u otro) y nombres de sus parámetros.
  - Dónde va el total completo (el ejemplo de `metadata` solo tiene `generated`, `last_ingestion`, `mode`, `count` y `truncated`) y su nombre.
  - Si `count` es el número de la página o el total.
  - Orden de los eventos, necesario para que la paginación sea estable.
  - Cómo se informa de la siguiente página.

## 4. Modo (live/replay)

- **Dice el contrato:** `metadata.mode` aparece con el valor `"live"` en el ejemplo. No hay ningún otro texto sobre modos.
- **Queda por decidir:**
  - Valores permitidos de `mode` (el contrato solo muestra `live`; `replay` no aparece).
  - Si el modo se elige con un parámetro de consulta, y cuál, o si lo fija el servidor.
  - Qué cambia en `generated` y `last_ingestion` en modo replay.
  - Si `/api/salud` y `/api/estadisticas` también informan del modo.

## 5. Campos adicionales y nulos

- **Dice el contrato:** las `properties` del ejemplo son `mag`, `magType`, `place`, `time`, `updated`, `country_id` y `country_name`. Usa `null` para "magnitud, profundidad o país desconocidos". Ejemplo: `country_id` `"ESP"`, `country_name` `"España"`.
- **Queda por decidir:**
  - Si el ejemplo es la lista completa de campos o solo un mínimo. Campos observados en USGS (`type`, `status`, etc.) no aparecen en el contrato.
  - Cómo se representa un evento sin país: el contrato dice `null` para país desconocido, pero no si afecta a `country_id`, a `country_name` o a ambos.
  - Origen y idioma de `country_name` (el ejemplo está en español).
  - Si el campo `id` del evento coincide con el de USGS.
  - Si `magType` puede ser nulo.

## 6. Filtros de /api/eventos

- **Dice el contrato:** filtros `start` (ISO8601, inclusive), `end` (ISO8601, exclusive), `min_mag` y `country_id`. La magnitud nula no cumple `min_mag` y "debe contabilizarse por separado".
- **Queda por decidir:**
  - Dónde se informa del conteo de magnitudes nulas (campo y ubicación en la respuesta).
  - Si `start` y `end` sin zona horaria se interpretan como UTC.
  - Respuesta ante parámetros inválidos (código HTTP y cuerpo).
  - Si `country_id` admite uno o varios valores y cómo se trata el "Sin país asignado".
  - Qué ocurre con el rango por defecto de 24 horas cuando solo se envía uno de `start` o `end`.

## 7. Errores generales y otros

- **Dice el contrato:** "Si la base falla, devuelve un error explícito" (solo en estadísticas). No define formato de error.
- **Queda por decidir:**
  - Formato común de error para todos los endpoints.
  - Si `/api/eventos` devuelve también error explícito cuando la base falla.
  - Origen exacto de la web para CORS en producción (el contrato dice "el origen exacto de la web" sin darlo).
