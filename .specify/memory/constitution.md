# Observatorio de actividad sísmica Constitution

## Datos y consistencia

### 1. Procesamiento al menos una vez e idempotente
El procesamiento MUST ser al menos una vez, con escritura idempotente (restricciones únicas
y upsert). El offset de Kafka MUST confirmarse después del commit en PostgreSQL, nunca antes.

### 2. Versionado por "updated"
Una versión con `updated` menor o igual NUNCA sustituye a una mayor. Un evento MUST
corresponder a una única fila actual.

### 3. Tiempos de USGS
Los tiempos de USGS vienen en milisegundos Unix. MUST convertirse a UTC conservando el valor
original.

### 4. País por geometría
El país MUST obtenerse por punto dentro de polígono (EPSG:4326, `ADM0_A3`), nunca del texto
`place`. Sin polígono el país es NULL y se muestra como "Sin país asignado".

### 5. Nulos y valores negativos
Los nulos MUST NOT rellenarse con 0. Una magnitud o profundidad negativa MUST NOT rechazarse
solo por ser negativa.

### 6. Cuarentena de datos inválidos
Los datos inválidos MUST ir a cuarentena con el motivo y una referencia al original. No se
pierden ni bloquean la cola.

### 7. Datos sintéticos separados
Los datos sintéticos y de mock MUST etiquetarse y mantenerse separados de los reales.

### 8. Agregaciones desde el estado actual
Las agregaciones MUST calcularse desde la tabla de estado actual, nunca con contadores por
mensaje.

## Infraestructura y seguridad

### 9. Nombres de servicio
Entre contenedores MUST usarse nombres de servicio, nunca `localhost`.

### 10. Exposición y secretos
Solo la API MUST exponerse. No MUST haber secretos en Git ni en Angular. `.env.example` MUST
estar siempre actualizado.

### 11. Versiones fijadas
Las dependencias y las versiones de runtime (Python, Node, Angular) MUST estar fijadas
(requirements/lock y `package-lock`).

### 12. Alcance cerrado
MUST NOT ampliarse el alcance: sin Spark, Flink, Kubernetes, ML, informes de calidad
automáticos ni panel de calidad.

## Código

### 13. Idioma
Los identificadores (funciones, variables, archivos de código, tablas, columnas, topics) MUST
estar en inglés. Docstrings, comentarios y documentación MUST estar en español. Excepción:
rutas y campos fijados por el contrato del profesor (`/api/eventos`, `country_id`,
`country_name`…).

### 14. Funciones de una sola responsabilidad
Cada función MUST hacer una sola cosa. La lógica pura (validar, transformar) MUST estar
separada del I/O (BD, Kafka, HTTP).

### 15. Contratos únicos
Los contratos (mensaje Kafka, esquema de BD, API) MUST vivir en
`specs/001-contratos-y-modelo` y no duplicarse. El contrato mínimo del profesor en
`docs/enunciado` MUST NOT modificarse.

### 16. Cierre de feature
Cada feature MUST terminar con prueba ejecutada, evidencia guardada, y `README` y `CODEMAP.md`
actualizados.

## Frontend

### 17. Frontend sin cálculo de estadísticas
El frontend MUST NOT calcular estadísticas: muestra lo que devuelve la API. MUST existir un
único estado de filtros compartido por mapa, tabla y gráficos. Los datos del mock son
sintéticos y MUST estar etiquetados.

## Documentación y proceso

### 18. Enunciado de solo lectura
`docs/enunciado/` es de solo lectura. Si el enunciado choca con la implementación, MUST
corregirse la implementación o consultarse al profesor. `specs/` (herramienta) MUST NOT
copiarse tal cual a `docs/` (entregables).

### 19. Una feature cada vez
MUST trabajarse una feature cada vez. MUST NOT implementarse sin spec, plan y tareas revisados
por el alumno. Al terminar una feature, el agente MUST detenerse y esperar revisión; MUST NOT
hacer commits ni merges sin aprobación.

## Git

### 20. Commits
Los commits MUST tener mensajes descriptivos. MUST NOT incluir trailers `Co-Authored-By` ni
líneas de "generado por" herramientas de IA, ni en commits ni en PRs.

## Lenguaje de resultados

### 21. Sin predicción ni riesgo
Las conclusiones MUST NOT usar lenguaje de predicción ni de riesgo.

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Una violación de un
principio MUST corregirse en spec, plan o tareas; no se reinterpreta ni se ignora.

- **Enmiendas**: se proponen por escrito, las aprueba el alumno y se registran en esta
  constitución con su versión y fecha.
- **Versionado** (semántico): MAJOR para eliminar o redefinir un principio de forma
  incompatible; MINOR para añadir un principio o ampliar materialmente su guía; PATCH para
  aclaraciones y correcciones de redacción.
- **Revisión de cumplimiento**: `/speckit-analyze` y la revisión de cada feature MUST
  verificar el cumplimiento de los principios.

**Version**: 1.0.0 | **Ratified**: 2026-11-01 | **Last Amended**: 2026-11-01
