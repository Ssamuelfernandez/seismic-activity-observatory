# Verificación de los documentos finales (README, memoria, rúbrica y guía del vídeo)

Fecha: 2026-11-16. Solo lectura sobre el código y los documentos; este informe es lo único escrito. Sin commits. Comprobado con `grep`, `git ls-files` y lectura directa contra `docs/enunciado/Guia-entregables-observatorio-sismico.md`, `docs/planificacion/01-checklist-requisitos.md` y las evidencias en `docs/evidencias/`.

Resumen: **4 bloqueantes, 8 importantes, 5 menores**.

## 1. README.md

| Elemento exigido | Resultado |
|---|---|
| Marcador del vídeo arriba | Cumple: `README.md:5` (único «PENDIENTE» permitido). |
| Aviso de que el panel requiere equipo y `cloudflared` encendidos | Cumple: `README.md:7`, `:103`, `:273`. |
| Tabla rúbrica→evidencia (M10) | Existe (`README.md:42-48`, cinco criterios en el orden pedido). Todas las rutas citadas existen y están versionadas. Pero el estado de varias filas está obsoleto (ver hallazgos). |
| Recorrido de un evento con `event_id` real | Cumple: `us6000pms8` (`README.md:56-67`). Verificado en `T053_replay.log`, `T053_consumer.log:326` (offset 18, partición 0), `T053_despues_detalle.out:36` y `T055_eventos_replay.json` (mag 4.4, CHL). Es un evento de replay, no en vivo; el README lo dice. |
| Decisión propia | Cumple: `README.md:69-71` (aislamiento en tres capas, con motivo y comprobación). |
| Limitaciones | Cumple: `README.md:73-84`. |
| Cómo ejecutar | Cumple: `README.md:86-103` y secciones siguientes. |
| Procedimiento de activación del túnel | Cumple: `README.md:253-284` (orden de arranque, parada, CORS, comprobaciones previas). El token solo aparece como marcador `<TOKEN>`. |
| Estado de features sin «en curso» ni «Pendiente» obsoletos | **No cumple** (ver H-I1, H-I2, H-I3). No hay ningún «en curso», pero sí «pendiente» desfasado. |

## 2. docs/memoria.md

Comparado con las secciones 2.1 a 2.9 de la guía del profesor y con los [OBL] del checklist que se responden en la memoria.

| Sección de la memoria | Exige la guía | Estado real |
|---|---|---|
| §1 Objetivo, flujo y alcance (2.1) | Pregunta, flujo de datos, decisiones de alcance | **Vacía**: solo el encabezado (`memoria.md:3`). |
| §2 Diccionario de datos (2.2) | Campos, significado, tipo/unidad, ausencias | Presente pero solo de los campos del feed de USGS (`:8-18`); no describe los campos del modelo (`event_id`, `mag_type`, `depth_km`, `updated_ms`, `country_id`, `is_synthetic`…). Contiene varios «por confirmar» (`:14`, `:16`, `:17`, `:18`). B2 (`:19-49`) cumple. |
| §3 Procedencia y registro de consultas (2.3) | Tabla de fuentes, URLs, filtros, nº de registros, fecha de extracción | **Vacía**: solo el encabezado (`:51`). |
| §4 Calidad (2.4, C14) | Consultas, resultados, antes/después, decisiones | Cumple: §4.4 (`:88-115`) con las 6 dimensiones, denominadores, decisiones, «antes y después» y límites. Las consultas están en `calidad-live.md`. |
| §5 Modelo (2.5, E1, E2, E5, E6) | Conceptual, lógico, físico, índices justificados | Cumple en contenido, pero lleva un aviso «Borrador» obsoleto (`:119`). Enlaza `sql/001_schema.sql`. |
| §6 Análisis y ≥3 conclusiones (2.6) | Conclusiones con periodo, filtros, denominador y capturas | **Vacía** (`:201`). Es un criterio de la rúbrica (Análisis). |
| §7 Complejidad, mediciones, costes, mejoras (K1 a K7) | Tres tamaños, 100 M, costes medido/supuesto, propuestas | Cumple: §7.1 a §7.6 con cifras y enlaces. Al final queda un párrafo «Mejoras propuestas» con «cifra pendiente» (`:268`). |
| §8 Evidencias de las 11 pruebas (2.8) | Tabla esperado/observado/evidencia | **Vacía** (`:269`). Existen fichas en `docs/evidencias/pruebas/`, pero la memoria no las resume ni enlaza. |
| §9 Reproducción histórica (2.9) | Selección, comando, velocidad, aislamiento, banner, resultados | **Vacía** (`:270`). El contenido está en el README (sección «Replay») y en `docs/borradores/replay.md`. |
| §10 Limitaciones (B11, B12) | Párrafo de B11, recuperación del hueco | Cumple: B11 en `:275`; B12 se remite a `docs/borradores/productor-live.md` (procedimiento fuera de la memoria). |

Requisitos [OBL] concretos: B2 cumple (§2.1); B11 cumple (§10); B12 solo por remisión; C14 cumple (§4.4); E1, E2, E5, E6 cumplen (§5 y §7.2); K1 a K7 cumplen (§7). B18 (el histórico es una instantánea a la fecha de extracción) no está en la memoria (solo en el README, `README.md:371`).

## 3. docs/rubrica-y-guia-video.md

El documento cubre los cinco criterios en el orden Extracción, Calidad, Modelado, Análisis, Reflexión (tabla `:11-17`, estado `:36-42`, guion `:89-97`), pero **está escrito como diagnóstico del 13-nov y no refleja el estado real del 16-nov**. Ya lo advertía `docs/evidencias/revision-final/rubrica-guia.md`, que dejó el documento sin corregir. Como guion del vídeo es poco fiable.

- Rutas: todas las rutas existen y están versionadas (comprobadas una a una, de forma exacta). Solo hay un comodín `prueba-09_*.md` (`:56`) que resuelve a un archivo existente.
- El guion de 5 minutos (`:89-97`) es coherente en estructura (un criterio por bloque, tiempos que suman 5:00) y las advertencias sobre qué no enseñar con datos reales (magnitud nula, cuarentena) siguen siendo ciertas. Pero:
  - Dice que Calidad es «Insuficiente en lo escrito» (`:39`) y que es «el hueco más importante»; ya existe §4.4 de la memoria.
  - Dice que memoria §1, §3, §6, §7, §8, §9, §10 están vacías o a medias (`:67`, `:138`); §7 y §10 y §4.4 ya están, pero §1, §3, §6, §8, §9 siguen vacías (el documento acierta en estas).
  - Dice que túnel y Netlify «no verificados» y que H1 está sin marcar (`:56`, `:70`); hay capturas del panel público, `H1_movil.md` y `H3_cloudflared_tunel.png`.
  - Marca como pendientes las capturas de las pruebas 1, 5 y 7 (`:105`, `:109`, `:111`) y no menciona la 3; existen `docs/evidencias/pruebas/capturas/01_`, `03_`, `05_`, `07_` y `09_`.
  - El README es descrito como «diario de features» sin la tabla M10 (`:69`); ya tiene la tabla, el recorrido y la decisión.
  - Dice que quedan por hacer features `pruebas-aceptacion` 014 y `readme-video` 017 (`:143`); la numeración real es 012 y 013.
  - Cita rutas sin el directorio correcto en prosa (p. ej. `consumidor-idempotente/geografia_prueba5.out`): existen igualmente (copias en dos directorios), pero la guía no indica la de `geografia-pais/`.
- El guion no incluye el recorrido real (`us6000pms8`) ni la decisión propia concreta (aislamiento del replay en tres capas); dice «un `id` de USGS» (`:97`).
- No menciona la limitación de que el panel público depende del PC y `cloudflared` encendidos en la grabación, ni el cierre de túnel para las pruebas 9 y 10 con el estado real (captura parcial «SIN RESPUESTA DE LA API», sin lectura previa).

## 4. Transversal

- **Rutas citadas**: de todas las rutas citadas en enlaces y entre comillas invertidas en los tres documentos, ninguna falta ni está sin versionar. Excepciones legítimas: `compose.override.yaml` (ignorado por `.gitignore` a propósito) y `.git/hooks/commit-msg` (no se versiona, documentado). `git status` estaba limpio al empezar.
- **Cifras entre documentos**: 18 302 únicos (histórico), 177 países, 210 eventos de la muestra y 22/24/0 del replay coinciden entre README, memoria y evidencias. **No coinciden** las cifras de `live`: la memoria §4.4 y `calidad-live.md` dan 19 208 eventos actuales, 19 509 versiones y 24,50 % con país (75,50 % sin país); la guía da 18 809 eventos, 18 909 versiones, 14 429 sin país (≈ 77 %) y «54 exclusiones» (`rubrica-y-guia-video.md:50-52`, `:111`, `:123`). Son de fechas distintas (13-nov y 15-nov), pero la guía no lo indica como desfasado.
- **Secretos y datos personales**: sin tokens, contraseñas ni claves. El token aparece solo como `<TOKEN>`. Los dominios `observatorio.ssamuelfernandez.net` y `observatorio-api.ssamuelfernandez.net` están en el README: son datos del propietario (el nombre aparece en el dominio) y son necesarios para el panel público; es una decisión del alumno si los quiere públicos.
- **Idioma**: texto en español; identificadores en inglés según la constitución.
- **Marcadores «PENDIENTE»**: solo el del enlace de YouTube (`README.md:5`). Queda otro «Pendiente del alumno» legítimo (`README.md:105`, `:284`) y los «pendiente» desfasados de H-I1.
- **Atribución a Claude**: no se encontró en los tres documentos.

## Hallazgos por gravedad

### Bloqueantes

- **H-B1** `docs/memoria.md:201` (§6): sección vacía; falta el criterio de rúbrica «Análisis» (≥3 conclusiones con periodo, filtros, denominador y capturas).
- **H-B2** `docs/memoria.md:269` (§8): sección vacía; la guía (2.8) exige presentar las pruebas con esperado/observado/evidencia, y las 11 fichas ya existen.
- **H-B3** `docs/memoria.md:3` (§1) y `:51` (§3): vacías; la guía (2.1 y 2.3) exige objetivo, flujo, alcance y registro de procedencia (URLs, filtros, número de registros, fecha de extracción).
- **H-B4** `docs/memoria.md:270` (§9): sección vacía; la guía (2.9) exige documentar el replay en la memoria.

### Importantes

- **H-I1** `README.md:44`, `:45`, `:46`, `:47`: la columna «Estado» de la tabla M10 dice «B2 parcial», «C14 parcial … falta pasarlo a la memoria», «prueba 1 sin captura», «pruebas 5 y 7 sin captura», «prueba 3 sin captura» y «conclusiones … sin escribir». B2 y C14 ya están en la memoria (§2.1, §4.4) y las capturas 1, 3, 5, 7 existen (`docs/evidencias/pruebas/capturas/`). Contradice `README.md:107`, que dice que están hechas.
- **H-I2** `README.md:18`, `:27`, `:119`: «B2, B11 y B12 pendientes de pasar … a la memoria», «capturas reales de 1, 3, 5 y 7 … pendientes del alumno» y «el análisis de calidad hay que pasarlo a la memoria (§4 y §6)». Obsoletos (B2, B11, C14 ya pasados; capturas hechas). Solo §6 sigue siendo cierto.
- **H-I3** `README.md:139`: «Memoria del proyecto (en redacción)» y `docs/memoria.md:119`: «> Borrador. Se completará…» (§5), y `docs/memoria.md:268` «cifra pendiente».
- **H-I4** `docs/rubrica-y-guia-video.md:36-143`: diagnóstico desfasado (ver sección 3): afirma que Calidad es insuficiente, que faltan capturas 1/3/5/7, que el túnel no está verificado y que el README no tiene la tabla M10. Un alumno que grabe siguiendo el guion mostraría o diría cosas falsas.
- **H-I5** `docs/rubrica-y-guia-video.md:50-52`, `:111`, `:123`: cifras de `live` del 13-nov (18 809 eventos, 14 429 sin país, ≈ 77 %, 54 exclusiones) que no coinciden con README y memoria (19 208 eventos, 24,5 % con país; 95 exclusiones según la revisión previa).
- **H-I6** `docs/memoria.md:8-18` (§2): el diccionario solo cubre el feed; faltan los campos del modelo realmente usados (guía 2.2 pide «los campos realmente utilizados») y quedan «por confirmar».
- **H-I7** `docs/rubrica-y-guia-video.md:97`: el cierre no usa el recorrido real ni la decisión propia concretos; no hay minuto de vídeo en la tabla M10 del README (el checklist M10 admite «minuto del vídeo»).
- **H-I8** `docs/memoria.md` no contiene B18 (instantánea a la fecha de extracción) ni material reutilizado (M2); ambos solo están en el README.

### Menores

- **H-M1** `docs/rubrica-y-guia-video.md:143`: numeración de features (014 y 017) distinta de la real (012 y 013).
- **H-M2** `README.md:119` y `:28`: la frase «revision-final … Las acciones que solo puede hacer el alumno» no menciona que memoria §1, §3, §6, §8 y §9 siguen vacías.
- **H-M3** `docs/rubrica-y-guia-video.md:56`: comodín `prueba-09_*.md`; mejor ruta exacta.
- **H-M4** `README.md:71`, `:451`: la cifra «211 / 211 / 0» del estado de `live` es del 2026-11-12 y difiere de las del 15-nov (19 208); está fechada en `:451` pero no en `:71`.
- **H-M5** `README.md` mezcla en el mismo archivo diario de features y documento final; el enlace al vídeo y la tabla M10 están arriba, así que no impide la lectura, pero es largo (498 líneas).

## Qué me falta a mí (alumno)

Acciones que no puede hacer Code:

1. Grabar el vídeo de 5 minutos (H5) y poner el enlace de YouTube en `README.md:5`.
2. Dar acceso de lectura al profesor en el servidor del repositorio (M4) y comprobarlo.
3. Prueba 9: con el panel mostrando datos, cerrar `cloudflared` y capturar el aviso «Datos antiguos» con la hora de la última lectura (G9). Prueba 10: reabrir el túnel y comprobar que el panel se recupera sola.
4. H3: captura de la pestaña «Rutas» del túnel con `http://localhost:8000` como único destino y el token tapado.
5. H4: ejecutar la demo con el equipo, los contenedores y el túnel encendidos, con el PC sin suspender, y comprobar `nslookup observatorio.ssamuelfernandez.net`.
6. Decidir y redactar (o autorizar a Code a redactar) las conclusiones de §6 con capturas del panel con filtros visibles, y comprobar con tus propios ojos las cifras.
7. Decidir si el dominio con tu nombre en el README es aceptable para entrega pública.
8. Repetir `docker compose up --build -d` desde un clon limpio con el estado final (A2/SC-007) y verificar la cuota gratuita de Netlify.
9. Ensayo con cronómetro del guion de 5 minutos.
10. Pedir a Code la corrección de H-B1 a H-B4 y H-I1 a H-I8 antes del 19 de noviembre.
