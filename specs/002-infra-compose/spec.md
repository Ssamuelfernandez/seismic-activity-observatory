# Feature Specification: Infraestructura Compose y verificación de punta a punta

**Feature Branch**: `002-infra-compose`

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "Feature: infra-compose. Poder levantar el sistema completo con un solo comando en Docker Compose y comprobar de punta a punta que los cinco servicios se comunican: un productor mínimo publica un evento ficticio marcado como sintético, un consumidor mínimo lo recibe, PostgreSQL conserva los datos tras reiniciar los contenedores y la API responde. Cubre A1–A12 (M7–M9 solo se verifican)."

## User Scenarios & Testing *(mandatory)*

Los "usuarios" de esta feature son quienes construyen y evalúan el sistema: la persona que implementa las demás features (el alumno, con su agente) y el profesor que levanta la entrega en su equipo. Esta feature entrega la base de ejecución sobre la que se apoyan las demás: un entorno que arranca con un solo comando y un recorrido mínimo de punta a punta con un evento ficticio. No entrega lógica de negocio.

### User Story 1 - Arranque completo con un solo comando (Priority: P1)

Quien clona el repositorio por primera vez ejecuta un único comando de arranque y obtiene los cinco servicios (productor, broker de mensajes, consumidor, base de datos y API) funcionando y en estado saludable, sin pasos manuales intermedios ni depender del orden en que arrancan.

**Why this priority**: Es el requisito obligatorio del enunciado (§2) y la condición para que cualquier otra feature pueda desarrollarse y evaluarse. Sin esto no hay sistema.

**Independent Test**: Desde un clon limpio (sin imágenes, volúmenes ni archivo de entorno previos más allá de copiar `.env.example`), ejecutar `docker compose up --build -d` y consultar el estado de los servicios hasta que los cinco figuren como saludables.

**Acceptance Scenarios**:

1. **Given** un clon limpio del repositorio con el archivo de entorno creado a partir de `.env.example`, **When** se ejecuta `docker compose up --build -d`, **Then** los cinco servicios llegan al estado saludable sin intervención manual.
2. **Given** que la base de datos o el broker tardan más que los servicios Python en estar listos, **When** el productor, el consumidor o la API arrancan antes, **Then** reintentan la conexión hasta que el servicio esté disponible y no terminan con error de forma definitiva.
3. **Given** el sistema en marcha, **When** se consulta la API desde el equipo anfitrión en `127.0.0.1:8000`, **Then** responde correctamente.

---

### User Story 2 - Evento sintético de punta a punta (Priority: P1)

Quien verifica el sistema comprueba que los servicios realmente se comunican: el productor mínimo publica un evento ficticio marcado como sintético, y el consumidor mínimo lo recibe y lo muestra en su registro.

**Why this priority**: Demuestra que la ruta productor → broker → consumidor funciona y que los nombres de servicio y los temas del contrato están bien configurados. Es el "hola mundo" del que dependen las features de productor y consumidor reales.

**Independent Test**: Con el sistema levantado, leer el registro del consumidor y encontrar el evento ficticio publicado por el productor, con la marca de sintético visible.

**Acceptance Scenarios**:

1. **Given** el sistema recién levantado, **When** el productor mínimo publica su evento ficticio, **Then** el registro del consumidor muestra ese evento, identificable como sintético.
2. **Given** el evento publicado, **When** se inspecciona su contenido, **Then** cumple la estructura del mensaje definida en `specs/001-contratos-y-modelo/contracts/kafka-message.md` (incluido `is_synthetic = true`) y viaja por el tema correspondiente de ese contrato.
3. **Given** que el consumidor aún no estaba listo cuando el productor publicó, **When** el consumidor termina de arrancar, **Then** recibe igualmente el evento, porque el broker lo conserva.

---

### User Story 3 - Persistencia tras reinicio (Priority: P1)

Quien verifica el sistema comprueba que los datos guardados en la base de datos sobreviven a detener y volver a arrancar los contenedores.

**Why this priority**: Es un requisito obligatorio (enunciado §9, A5): el estado persistente y los originales no pueden perderse al reiniciar.

**Independent Test**: Escribir un dato de prueba en la base de datos, reiniciar los contenedores y comprobar que el dato sigue presente.

**Acceptance Scenarios**:

1. **Given** un dato de prueba guardado en la base de datos, **When** se detienen y se vuelven a arrancar los contenedores sin eliminar los volúmenes, **Then** el dato sigue presente y consultable.
2. **Given** el sistema reiniciado, **When** los servicios vuelven a arrancar, **Then** alcanzan de nuevo el estado saludable sin intervención manual.
3. **Given** una base de datos nueva, **When** arranca por primera vez, **Then** se crea con el esquema definido en `specs/001-contratos-y-modelo/contracts/db-schema.md`, y los arranques posteriores no lo duplican ni lo dañan.

---

### User Story 4 - Aislamiento y mínimo privilegio (Priority: P2)

Quien evalúa la seguridad comprueba que desde fuera de la red de Compose solo se puede llegar a la API, y que la API accede a la base de datos con una cuenta de solo lectura.

**Why this priority**: Es obligatorio (A8 y enunciado §9) pero no bloquea el recorrido funcional de las historias anteriores; se verifica una vez que el sistema arranca.

**Independent Test**: Desde el equipo anfitrión, intentar conectar al broker y a la base de datos (debe fallar), y comprobar con la cuenta de la API que puede leer pero no escribir.

**Acceptance Scenarios**:

1. **Given** el sistema en marcha, **When** se intenta conectar desde el equipo anfitrión al broker o a la base de datos, **Then** la conexión no es posible porque no se publican puertos.
2. **Given** el sistema en marcha, **When** se listan los puertos publicados al exterior, **Then** el único es el de la API, ligado a `127.0.0.1:8000`.
3. **Given** la cuenta de base de datos que usa la API, **When** intenta leer `current_event`, `country` e `ingest_run`, **Then** puede; **When** intenta escribir en cualquier tabla, **Then** la base de datos lo rechaza.
4. **Given** las cuentas de productor y consumidor, **When** escriben, **Then** solo pueden hacerlo en las tablas que el contrato asigna a cada una (sección «Quién escribe y quién lee» de `db-schema.md`).

---

### User Story 5 - Configuración sin secretos y versiones fijadas (Priority: P2)

Quien revisa el repositorio comprueba que no hay credenciales en él, que `.env.example` documenta todas las variables que usa el código y que las versiones de runtime y las dependencias están fijadas, de modo que otra persona obtiene el mismo resultado.

**Why this priority**: Obligatorio (A10, A11, constitución §10 y §11). Se puede verificar de forma independiente del arranque.

**Independent Test**: Buscar secretos en el repositorio y comparar mecánicamente las variables de entorno que lee el código y la configuración de los servicios con las de `.env.example`.

**Acceptance Scenarios**:

1. **Given** el repositorio completo, **When** se buscan credenciales reales, **Then** no aparece ninguna; `.env.example` solo contiene valores de ejemplo no sensibles y el archivo de entorno real está ignorado por Git.
2. **Given** `.env.example`, **When** se compara con las variables que leen el código y `compose.yaml`, **Then** coinciden: no falta ninguna ni sobra ninguna.
3. **Given** el repositorio, **When** se inspeccionan las versiones, **Then** la versión de Python, la de PostgreSQL (16) y las dependencias de Python están fijadas con valores exactos y un archivo de bloqueo.
4. **Given** el productor mínimo, **When** se cambian por entorno la dirección del broker, el tema y la frecuencia de publicación, **Then** su comportamiento cambia sin tocar el código.

---

### User Story 6 - Retención limitada del broker (Priority: P3)

Quien evalúa la operación comprueba que el broker no acumula mensajes indefinidamente: los temas del contrato tienen una retención limitada y documentada.

**Why this priority**: Obligatorio (A6), pero es una configuración que se comprueba una vez y no afecta al recorrido básico.

**Independent Test**: Consultar la configuración de los temas en el broker en marcha y comprobar la retención.

**Acceptance Scenarios**:

1. **Given** el sistema levantado, **When** se consulta la configuración de los temas `earthquakes.live` y `earthquakes.replay`, **Then** ambos tienen 1 partición, factor de replicación 1 y retención de 7 días, tal como fija `kafka-message.md` §1.
2. **Given** la documentación del repositorio, **When** se busca la retención, **Then** el valor y su motivo están documentados.

---

### Edge Cases

- **Orden de arranque adverso**: los servicios Python arrancan antes que el broker o la base de datos. Deben reintentar con espera y no abortar; el orden de arranque por sí solo no se considera suficiente.
- **Broker o base de datos no disponibles durante la ejecución** (no solo al arrancar): los servicios afectados reintentan y se recuperan cuando vuelven, sin quedar bloqueados de forma permanente.
- **Segundo arranque sobre volúmenes existentes**: la inicialización de la base de datos no debe fallar ni duplicar objetos al repetirse.
- **Eliminación de volúmenes** (`docker compose down -v`): es el único caso en que se pierden los datos; debe quedar documentado que es deliberado.
- **Archivo de entorno ausente o incompleto**: el sistema debe fallar de forma clara y temprana indicando qué variable falta, no arrancar con valores por defecto sensibles.
- **Puerto 8000 ocupado en el equipo anfitrión**: el arranque de la API falla con un error comprensible; se documenta cómo diagnosticarlo.
- **Productor mínimo reiniciado**: puede volver a publicar su evento ficticio; no es un comportamiento de producción y no se exige idempotencia (queda para `productor-live` y `consumidor-idempotente`).
- **Evento sintético en datos reales**: el evento ficticio debe ir siempre marcado como sintético y no mezclarse con datos reales (constitución §7).

## Requirements *(mandatory)*

### Functional Requirements

**Servicios y arranque (A1, A2, A3, A12)**

- **FR-001**: El sistema MUST definirse como cinco servicios independientes en una única definición de Compose: productor, broker de mensajes, consumidor, base de datos y API.
- **FR-002**: El sistema MUST poder levantarse desde un clon limpio con el comando `docker compose up --build -d`, sin pasos manuales adicionales salvo crear el archivo de entorno a partir de `.env.example`.
- **FR-003**: Productor, consumidor y API MUST construirse a partir de una única imagen reproducible compartida, diferenciándose por el comando de inicio.
- **FR-004**: El código compartido (`common/`) MUST poder importarlo cualquier servicio Python del sistema.
- **FR-005**: El frontend NO MUST tener contenedor en esta feature; ngrok queda fuera de Compose y fuera de esta feature (se ejecuta en el equipo anfitrión).

**Salud y reintentos (A4)**

- **FR-006**: Cada uno de los cinco servicios MUST tener una comprobación de salud, y el estado «saludable» MUST significar que el servicio está realmente listo para atender, no solo que el proceso existe.
- **FR-007**: Los servicios que dependen de otros MUST declarar esa dependencia en función de su salud, no solo de su orden de arranque.
- **FR-008**: Productor, consumidor y API MUST reintentar la conexión al broker o a la base de datos con espera entre intentos, tanto al arrancar como si la conexión se pierde después, sin terminar de forma definitiva por indisponibilidad temporal.
- **FR-009**: Cada reintento fallido MUST dejar constancia en el registro con el servicio al que se intenta conectar.

**Recorrido de punta a punta**

- **FR-010**: El productor mínimo MUST publicar un evento ficticio con la estructura de `kafka-message.md` §3, con `is_synthetic = true`, `mode = live` y `source = replay_demo`, en el tema `earthquakes.live`, y con clave igual a `event.id`.
- **FR-011**: El consumidor mínimo MUST recibir los mensajes de `earthquakes.live` y mostrar en su registro el evento, de modo que se distinga que es sintético.
- **FR-012**: El productor mínimo MUST ser configurable por entorno en, al menos, la dirección del broker, el tema y la frecuencia de publicación (A10).
- **FR-013**: El consumidor mínimo MUST NOT validar con reglas de negocio, transformar ni escribir en tablas de eventos; esa lógica pertenece a `consumidor-idempotente`.
- **FR-014**: La API MUST responder a una petición de comprobación de estado indicando si la API y la base de datos responden, sin implementar los endpoints de datos (fuera de alcance).
- **FR-015**: Los datos de prueba sintéticos MUST estar etiquetados como tales y mantenerse separados de los reales (constitución §7).

**Contratos (no se redefinen)**

- **FR-016**: Los temas `earthquakes.live` y `earthquakes.replay` MUST existir al arrancar el sistema con 1 partición, factor de replicación 1 y retención de 7 días, según `kafka-message.md` §1.
- **FR-017**: El mensaje publicado MUST respetar `kafka-message.md` sin añadir ni cambiar campos; esta feature MUST NOT modificar ese contrato ni `db-schema.md`.

**Persistencia (A5)**

- **FR-018**: Los datos de PostgreSQL MUST residir en un volumen persistente que sobreviva a detener y recrear los contenedores.
- **FR-019**: Los datos del broker MUST residir en un volumen persistente para que los mensajes pendientes sobrevivan a un reinicio dentro de su retención. Los originales de USGS viven en PostgreSQL (`ingest.raw_response`), por lo que no requieren un volumen aparte.
- **FR-020**: Al crear la base de datos por primera vez, el sistema MUST aplicar `sql/001_schema.sql`; aplicarlo de nuevo sobre una base ya inicializada MUST NOT fallar ni duplicar objetos.

**Retención (A6)**

- **FR-021**: La retención de 7 días de los temas MUST estar configurada de forma explícita y documentada, con su motivo.

**Red, nombres y exposición (A7, A8, A9)**

- **FR-022**: Entre contenedores MUST usarse nombres de servicio, nunca `localhost` (constitución §9).
- **FR-023**: Solo la API MUST publicarse al exterior, exclusivamente en `127.0.0.1:8000`. El broker y la base de datos MUST NOT publicar ningún puerto.
- **FR-024**: La API MUST escuchar en todas las interfaces dentro del contenedor (`0.0.0.0:8000`) para ser alcanzable desde el puerto publicado.
- **FR-025**: Los cinco servicios MUST compartir una red interna de Compose que permita la comunicación por nombre de servicio.
- **FR-026**: Si en algún momento se desea acceso al broker desde el equipo anfitrión, los listeners MUST estar documentados; el acceso por defecto no se habilita.

**Roles de base de datos (mínimo privilegio)**

- **FR-027**: Se MUST definir un rol de base de datos de solo lectura para la API, con permiso de lectura sobre `live.current_event`, `replay.current_event`, `public.country` e `ingest.ingest_run` y sin ningún permiso de escritura (`db-schema.md` §1.1).
- **FR-028**: Se MUST definir roles para productor y consumidor cuyos permisos de escritura se derivan de la tabla «Quién escribe y quién lee» de `db-schema.md` §1.1, sin conceder más de lo necesario.
- **FR-029**: Los roles MUST crearse en la inicialización de infraestructura, no en `sql/001_schema.sql`, que no crea roles.
- **FR-030**: Cada servicio MUST conectarse con su propio rol, no con el administrador de la base de datos.

**Configuración, secretos y versiones (A10, A11, M7–M9)**

- **FR-031**: Toda la configuración variable MUST proceder de variables de entorno documentadas en `.env.example`, que MUST contener solo valores de ejemplo no sensibles.
- **FR-032**: `.env.example` MUST coincidir con las variables que usan el código y `compose.yaml`: ninguna ausente y ninguna sobrante.
- **FR-033**: El archivo de entorno real MUST estar ignorado por Git y el repositorio MUST NOT contener secretos.
- **FR-034**: La versión de Python MUST fijarse con valor exacto, y las dependencias de Python MUST declararse con versiones concretas más un archivo de bloqueo reproducible.
- **FR-035**: Las imágenes de PostgreSQL (16) y del broker MUST usar versiones concretas, no etiquetas flotantes como `latest`.
- **FR-036**: Si falta una variable de entorno obligatoria, el servicio MUST fallar con un mensaje que nombre la variable.
- **FR-037**: Los requisitos M7–M9 (Git y estructura del repositorio) MUST solo verificarse, no rehacerse: historial sin trailers de coautoría ni líneas de «generado por», `CLAUDE.md`, `CODEMAP.md` y constitución versionados y `docs/enunciado/` intacto.

**Documentación y cierre**

- **FR-038**: La feature MUST dejar documentado cómo levantar el sistema, cómo verificarlo y cómo reiniciarlo, y MUST guardar la evidencia de las verificaciones en `docs/evidencias/`.
- **FR-039**: Al cerrar la feature, `README.md` y `CODEMAP.md` MUST estar actualizados (constitución §16).

### Fuera de alcance

Lógica real del productor (consulta a USGS), validación y escritura idempotente del consumidor, país por polígono, histórico, endpoints reales de la API, frontend, ngrok y Netlify.

### Key Entities *(include if feature involves data)*

- **Servicio**: cada uno de los cinco componentes (productor, broker, consumidor, base de datos, API). Atributos relevantes: estado de salud, dependencias, red a la que pertenece y, en su caso, puerto publicado.
- **Evento sintético de prueba**: mensaje ficticio que cumple el contrato de `kafka-message.md`, marcado `is_synthetic = true`. No representa un terremoto real y no debe mezclarse con datos reales.
- **Tema de mensajes**: canal `earthquakes.live` o `earthquakes.replay` con retención de 7 días. Definido por el contrato, no por esta feature.
- **Volumen persistente**: almacenamiento que conserva los datos de la base de datos y del broker entre reinicios.
- **Rol de base de datos**: cuenta con permisos mínimos para un servicio (API: solo lectura; productor y consumidor: escritura limitada a lo que fija el contrato).
- **Variable de entorno**: parámetro de configuración documentado en `.env.example` y leído por servicios o por la definición de Compose.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde un clon limpio, un único comando de arranque deja los 5 de 5 servicios en estado saludable en menos de 5 minutos (sin contar la descarga inicial de imágenes), sin ninguna intervención manual.
- **SC-002**: En el 100 % de los arranques de prueba, incluidos los que arrancan los servicios Python antes que el broker o la base de datos, el sistema alcanza el estado saludable sin reinicios manuales.
- **SC-003**: Tras el arranque, el registro del consumidor muestra el evento sintético del productor en menos de 60 segundos, identificado como sintético.
- **SC-004**: Tras detener y volver a arrancar los contenedores sin borrar volúmenes, el 100 % de los datos de prueba guardados en la base de datos siguen presentes y los 5 servicios vuelven a estado saludable.
- **SC-005**: Desde el equipo anfitrión, 0 de los servicios distintos de la API aceptan conexiones, y exactamente 1 puerto queda publicado, ligado únicamente a la dirección local.
- **SC-006**: La cuenta de la API consigue 0 escrituras exitosas en la base de datos en las pruebas de escritura y sí consigue las lecturas que fija el contrato.
- **SC-007**: Una búsqueda de secretos sobre el repositorio devuelve 0 credenciales reales, y la comparación entre `.env.example` y las variables usadas arroja 0 diferencias.
- **SC-008**: El 100 % de las versiones de runtime y de dependencias de Python están fijadas con valor exacto; una reconstrucción en otro equipo produce el mismo resultado.
- **SC-009**: Los dos temas del contrato aparecen configurados con 1 partición, factor de replicación 1 y 7 días de retención.
- **SC-010**: Una persona que no ha participado en el desarrollo puede levantar, verificar y reiniciar el sistema siguiendo solo la documentación, sin consultar a nadie.

## Assumptions

- El equipo anfitrión tiene Docker con Compose v2 instalado y los recursos suficientes para cinco contenedores; el puerto 8000 está libre.
- El archivo de entorno real lo crea cada persona copiando `.env.example` y ajustando valores de ejemplo; en desarrollo local las credenciales de ejemplo no son sensibles, pero no se versionan en un archivo de entorno real.
- El esquema `sql/001_schema.sql` ya existe (feature `001-contratos-y-modelo`) y esta feature solo lo aplica; las migraciones futuras quedan para las features que las necesiten.
- El evento ficticio usa `source = replay_demo`, valor ya permitido por el contrato para eventos fabricados para demostración, porque el contrato no define un origen específico para pruebas de infraestructura y esta feature no debe ampliarlo.
- El consumidor mínimo no escribe en tablas de eventos: la prueba de persistencia se hace con un dato de prueba escrito por el procedimiento de verificación, no por la lógica del consumidor.
- Los roles de productor y consumidor se definen ahora porque la tabla de `db-schema.md` §1.1 ya fija sus permisos; las features posteriores no deben ampliarlos sin actualizar esa tabla.
- La retención de 7 días se aplica a los dos temas del contrato; el replay se usa más adelante, pero su tema existe desde el principio para evitar reconfigurar el broker.
- La versión exacta de Python, del broker y de las dependencias se decide en el plan de esta feature (`/speckit-plan`), no en esta spec.
- ngrok se ejecuta en el equipo anfitrión con `ngrok http 8000`; su authtoken nunca entra en el repositorio.
