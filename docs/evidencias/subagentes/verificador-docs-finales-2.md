# Verificación de los documentos finales, segunda pasada (README, memoria, rúbrica y guía del vídeo)

Fecha: 2026-11-16. Rama `013-revision-final`. Solo lectura sobre el código y los documentos; este informe es lo único escrito. Sin commits. Comprobado con `git log 8a0d1a8..HEAD`, `git ls-files`, `git status`, `grep`, un script que resuelve cada ruta citada (enlaces y comillas invertidas) contra `git ls-files`, lectura directa y comparación de cifras con `docs/evidencias/revision-final/conclusiones-analisis.md`, `procedencia-live.md`, `calidad-live.md`, `data/historical/manifest.json` y las evidencias de `replay`, `historico-2025`, `productor-live` y `pruebas`. La primera pasada es `docs/evidencias/subagentes/verificador-docs-finales.md`.

Resumen: **0 bloqueantes, 2 importantes, 8 menores.** Los 4 bloqueantes y los 8 importantes de la primera pasada están resueltos; queda abierto solo un menor antiguo (H-M5, longitud del README).

Las decisiones aceptadas por el alumno se han tratado como aceptadas (H3 con la captura existente, vídeo y enlace a mano, pruebas 9 y 10, M4, H4, Netlify gratuito, clon limpio, sin captura nueva en §6, dominio con el nombre). Las he comprobado solo en cuanto a precisión de la redacción: la documentación las refleja con exactitud (ver §5).

## 1. Estado de los hallazgos de la primera pasada

| Hallazgo | Estado | Prueba |
|---|---|---|
| H-B1 memoria §6 vacía | **Resuelto** | `docs/memoria.md:269-281`: tres conclusiones con periodo, filtros, denominador y límite. Todas las cifras coinciden con `conclusiones-analisis.md` (18 302; 2 684 y 2 222; 26,8 %; Kamchatka 1 361 y 1 239; `us6000qw60` M 8,8; sin país 14 350 = 78,4 %; China 354, Chile 348, Indonesia 306, Etiopía 265, Argentina 236; 16 173 / 1 984 / 129 / 16; 0,79 %; 13 689 = 74,8 %; mediana 20,9 km; 1 102 = 6,0 %). Comprobado: 26,8 % = (2 684 + 2 222) / 18 302 y el rango 1 156 a 1 604 de los otros diez meses. |
| H-B2 memoria §8 vacía | **Resuelto** | `docs/memoria.md:350-368`: tabla de las 11 pruebas (esperado, observado, ficha) con enlaces que existen. Las cifras (829 y 3 fallos de entorno, 232 de integración, `ci41362543`, `uw714139501`, 1,5758 a 1,38, 30 eventos sin país, 28 de 181) coinciden con `docs/evidencias/pruebas/README.md` y las fichas `*_captura_pendiente.md`. |
| H-B3 memoria §1 y §3 vacías | **Resuelto** | §1 (`:3-33`): pregunta, diagrama de flujo, alcance dentro y fuera. §3 (`:103-120`): tabla de fuentes con URL, filtros, registros y fecha. Comprobado contra `procedencia-live.md` (1 762 consultas, todas 200, del 2026-11-12 16:38 al 2026-11-16 18:10; 774 respuestas; 1 083 eventos del feed; 95 exclusiones; 177 países) y contra `manifest.json` (18 302 únicos, 0 duplicados, `usgs_count_year` 18 302, extracción 11:40:17 a 11:40:33 del 2026-11-05, hueco de 30 registros el 2026-11-05 11:47:12). Registros mensuales (1 413 … 1 277) suman 18 302. Ciclo 1 (203 / 12 / 191) en `ciclo1.log:3`. |
| H-B4 memoria §9 vacía | **Resuelto** | `docs/memoria.md:370-400`: selección, comando, velocidad, aislamiento en tres capas, banner y tabla esperado/observado. Coincide con `docs/evidencias/replay/` (26 mensajes, 22 / 24 / 0, 51 s, `T053_replay.log:40-41`, 211 / 211 / 0). La cifra «267 eventos en la zona» está en `docs/borradores/replay.md:11`. |
| H-I1 estado de la tabla M10 obsoleto | **Resuelto** | `README.md:44-48`: B2, C14, pruebas 1, 3, 5 y 7 con captura, conclusiones en §6; ya no hay «sin captura» ni «sin escribir». |
| H-I2 «pendiente» desfasado en README:18, :27, :119 | **Resuelto** | `README.md:18` (B2, B11 y B12 pasados a la memoria), `:27` (capturas hechas), `:107-113` (pendientes reales). |
| H-I3 «en redacción», «Borrador» y «cifra pendiente» | **Resuelto** | `README.md:133` dice «secciones 1 a 10»; `grep` de «Borrador», «cifra pendiente», «por confirmar», «TODO» en `memoria.md` no devuelve ninguno (solo referencias legítimas a `docs/borradores/`). |
| H-I4 guía desfasada | **Resuelto** | `docs/rubrica-y-guia-video.md` reescrita con fecha 2026-11-16 (ver §3 de este informe). |
| H-I5 cifras de `live` del 13-nov en la guía | **Resuelto** | `docs/rubrica-y-guia-video.md:38,48-55`: 19 208 (15-nov) y 19 385 (16-nov), 95 exclusiones, 75,50 % y 24,50 %, todas con fecha. Coinciden con `calidad-live.md` y `procedencia-live.md`; 18 302 + 906 = 19 208 y 18 302 + 1 083 = 19 385. |
| H-I6 diccionario solo del feed y «por confirmar» | **Resuelto** | `docs/memoria.md:82-101` (§2.2) describe los campos del modelo (`event_id`, `event_time(_ms)`, `updated_at/_ms`, `mag`, `mag_type`, `depth_km`, `country_id`, `is_synthetic`, `replay_at`…) con tipo, unidad y tratamiento de ausencias. Los valores de `status` (18 789 / 596) y los 0 nulos coinciden con `procedencia-live.md`. |
| H-I7 cierre sin recorrido real y sin minuto en M10 | **Resuelto** | `docs/rubrica-y-guia-video.md:85` (`us6000pms8` con partición 0 offset 18 y decisión en tres capas) y `README.md:42-48` (columna «Minuto del vídeo»). |
| H-I8 B18 y M2 ausentes de la memoria | **Resuelto** | B18 en `docs/memoria.md:118`; M2 en `:421-425`. |
| H-M1 numeración 014 y 017 en la guía | **Resuelto** | `grep -n "014\|017"` en guía y README sin resultados. |
| H-M2 frase sobre pendientes sin mencionar memoria vacía | **Resuelto** | La memoria está completa; `README.md:28` ya no afirma nada falso sobre ella. |
| H-M3 comodín `prueba-09_*.md` | **Resuelto** | Ningún `*` en los tres documentos; el script solo señala `compose.override.yaml` (ignorado a propósito). |
| H-M4 «211 / 211 / 0» sin fecha en README:71 | **Resuelto** | `README.md:71` lo fecha (2026-11-12) y aclara que `live` hoy tiene más filas. |
| H-M5 README largo (493 líneas) | **Abierto (menor, sin cambios)** | El tope (marcador, aviso, tabla M10, recorrido, decisión, limitaciones, cómo ejecutar) está en las primeras 115 líneas; no impide la lectura. |

## 2. README.md

| Elemento exigido | Resultado |
|---|---|
| Marcador del vídeo arriba | Cumple: `README.md:5`, único «PENDIENTE» (más «Pendientes del alumno» como título legítimo en `:105`, `:279`, y las palabras «pendiente de la revisión del alumno» de las filas de feature). |
| Aviso de PC y `cloudflared` encendidos | Cumple: `:7`, `:103`, `:267`, `:273`. |
| Tabla rúbrica→evidencia (M10) | Cumple: `:42-48`, cinco criterios en el orden Extracción, Calidad, Modelado, Análisis, Reflexión, con minutos que coinciden con el guion (0:20–1:05, 1:05–1:55, 1:55–2:40, 2:40–4:10, 4:10–4:40). Todas las rutas existen y están versionadas. Pero ver H-N1 sobre la fuente «auditoría». |
| Recorrido con `event_id` real | Cumple: `:56-67`, `us6000pms8`, verificado en `T053_replay.log`, `T053_consumer.log:326` (partición 0, offset 18), `T053_despues_detalle.out:36` (`2026-11-12 16:39:41+00`) y `T055_eventos_replay.json`. Declara que es de replay, no en vivo. |
| Decisión propia | Cumple: `:69-71` (tres capas, motivo y comprobación). |
| Limitaciones | Cumple: `:73-84`. |
| Cómo ejecutar | Cumple: `:86-103` y las secciones siguientes. |
| Procedimiento del túnel | Cumple: `:247-279` (decisiones, orden de arranque, parada, CORS, aviso de disponibilidad, comprobaciones previas). El token solo aparece como `<TOKEN>`. Cubre los cinco pasos de la guía del profesor §3.2 (el de «comprobar que la base contiene datos» se reduce a `/api/salud`, suficiente). |
| Estado de features sin «en curso» ni «Pendiente» obsoletos | Cumple. No hay «en curso». Las filas con «pendiente de la revisión del alumno» (`:16-22`, `:25`, `:27`) hablan de la revisión humana de cada feature y siguen siendo coherentes (no bloqueante). |

## 3. docs/memoria.md

| Sección | Guía del profesor | Resultado |
|---|---|---|
| §1 (2.1) | Pregunta, flujo, alcance | Cumple. Incluye periodo histórico, ámbito (mundial, M≥4) y filtros. |
| §2 (2.2) y §2.1, §2.2 | Campos realmente usados, unidades, ausencias; B2 | Cumple. B2: estructura, tipos y unidades, opcionales, frecuencia, errores y latencia (223 ms, 150 724 bytes), con lo no medido dicho como tal. |
| §3 (2.3) y B18 | Fuentes, URL, filtros, registros, fecha | Cumple. |
| §4 y §4.4 (2.4, C14) | Consultas, resultados, antes/después, decisiones | Cumple. Cifras del 2026-11-15 (19 208, 19 509, 149, 24,50 %, 906 / 18 302) coinciden con `calidad-live.md` y están fechadas. |
| §5 (2.5, E1 a E5) | Tres niveles, fila de cada tabla, SQL enlazado, índices por consulta, equivalencia de nombres | Cumple. Ya no lleva aviso «Borrador». |
| §6 (2.6) | ≥3 conclusiones con periodo, ámbito, filtros y denominador; capturas | Cumple en contenido (ver H-B1). La falta de captura nueva está declarada en `:281` (limitación aceptada). |
| §7 (2.7, K1 a K7, E6) | Complejidad, tres tamaños, 100 M, costes medido/supuesto, mejoras | Cumple. «Mejoras propuestas» (`:347-349`) enlaza con una cifra real (14 350 de 18 302). |
| §8 (2.8) | Esperado, observado, evidencia | Cumple. Las pruebas 9 y 10 dicen con precisión qué muestra la captura (`:364-365`): «SIN RESPUESTA DE LA API», no «Datos antiguos», sin captura de la 10. |
| §9 (2.9) | Selección, comando, velocidad, aislamiento, banner, resultados | Cumple. |
| §10 (B11, B12, M2) | Limitaciones y material reutilizado | Cumple: B11 `:406`, B12 `:408` (con ensayo 3 / 4 / 1, comprobado en `historico_hueco.out:4`), M2 `:421-425`. |

Sin secciones vacías, con plantilla ni TODO.

## 4. docs/rubrica-y-guia-video.md

- Orden Extracción, Calidad, Modelado, Análisis, Reflexión: cumple en la tabla de la rúbrica (`:11-17`), en el estado (`:36-42`) y en el guion (`:79-84`).
- Guion de 5:00 (`:76-85`), duraciones: 0:20 + 0:45 + 0:50 + 0:45 + 0:55 + 0:35 + 0:30 + 0:20 = 300 s = 5:00. Los tramos son contiguos (0:00 a 5:00) y coinciden con la columna de minutos del README.
- Coherente con el estado real: dice que el panel público depende del PC y `cloudflared` (`:65`), que las pruebas 9 y 10 se hacen en vivo (`:83`, `:89-98`), que la captura actual es parcial y no muestra «Datos antiguos» (`:98`, `:112`), que no hay captura nueva del panel con los filtros de §6 (`:41`), y que Calidad se enseña con casos controlados porque en `live` no hay nada que limpiar. Las cifras llevan fecha.
- El cierre usa el recorrido de `us6000pms8` y la decisión propia, con la tabla M10 del README (`:85`).
- Rutas: exactas, con directorio completo (`docs/evidencias/geografia-pais/geografia_prueba5.out`, etc.), sin comodines ni abreviaturas. La única «ausente» del script es `compose.override.yaml`, ignorado por `.gitignore` a propósito.
- «Lo que queda» (`:130-132`) se limita a lo del alumno: grabar el vídeo y poner el enlace.

## 5. Transversal

- **Rutas.** Script sobre 346 candidatos del README, 274 de la memoria y 60 de la guía: todos los enlaces y rutas completas existen y están en `git ls-files`. Las demás «ausentes» son nombres cortos usados como texto de enlace o dentro de tablas (`api.md`, `manifest.json`, `settings.json`, `all_day.geojson`…), la ruta `.git/hooks/` (no versionable, documentada), `compose.override.yaml` (ignorado) y la excepción de H-N2 (informe sin versionar).
- **Cifras repetidas.** Coinciden entre README, memoria, guía y evidencias: 18 302; 177 países; 210 eventos y 223 ms de la muestra; 22 / 24 / 0, 26 mensajes, 51 s y 211 / 211 / 0 del replay; 1 762 consultas; 95 exclusiones; 19 208 (15-nov) y 19 385 (16-nov); 16 frente a 50,14 con `recent_incomplete`.
- **Secretos y datos personales.** Sin tokens, contraseñas ni claves; el token solo como `<TOKEN>`. Sin atribución a Claude en los tres documentos (las apariciones de «Claude Code» en `README.md:146` y `:482` describen configuración, no atribución). El dominio con el nombre del alumno es decisión aceptada.
- **Idioma.** Español, con identificadores en inglés.
- **«PENDIENTE».** Solo el del enlace de YouTube (`README.md:5`; la guía lo cita en `:132`).
- **Decisiones aceptadas del alumno: redacción.** H3 (`README.md:107`) describe bien la captura: se comprobó la imagen `H3_cloudflared_tunel.png` y muestra el túnel `observatorio-api` en «Buen estado» con su ruta pública y la pestaña «Resumen», no «Rutas»; el README lo dice. Pruebas 9 y 10 (`README.md:112`, memoria `:364-368`, guía `:98`): precisas. Netlify (`README.md:48`, memoria `:344`, guía `:42`): «plan gratuito, según indica el alumno», sin afirmar comprobación. Clon limpio (`README.md:81`, `:102`): declarado como limitación. H4 y M4: no aparecen como pendientes engañosos.

## 6. Hallazgos nuevos

### Bloqueantes

Ninguno.

### Importantes

- **H-N1** `README.md:40` y `:107` (también `:28`): el README dice que el «Estado (auditoría)» de la tabla M10 «está tomado de» `docs/evidencias/revision-final/auditoria.md` y remite a ella para el detalle de las decisiones del 2026-11-16, pero esa auditoría es del 2026-11-15 y contradice al README: recuento «83 cumple, 7 parcial, 3 no» (`auditoria.md:9`); B2, B11 y C14 como «parcial» (`:33`, `:42`, `:62`), con «memoria §10 vacía»; H5 «`README.md` aún no tiene el marcador del enlace, el recorrido del evento ni la decisión propia» (`:93`); M3 «falta el recorrido… y la tabla» (`:110`). Quien siga el enlace para verificar la columna encuentra un estado contrario. Conviene actualizar la auditoría (o cambiar la redacción del README para decir que la columna refleja el estado a 2026-11-16 y la auditoría es la foto del 15-nov).
- **H-N2** `README.md:28`: enlaza `docs/evidencias/subagentes/verificador-docs-finales.md`, que hoy está sin versionar (`git status`: `??`). En un clon el enlace daría 404. Hay que versionarlo antes de entregar (y este segundo informe, si se quiere conservar).

### Menores

- **H-N3** `README.md:28` y `docs/evidencias/revision-final/rubrica-guia.md`: el README cita esa comprobación como si fuera vigente, pero dice que la guía «no se ha modificado» y lista cifras y frases desfasadas que ya se corrigieron. Es una foto del 2026-11-15; conviene fecharla o anotar que se superó.
- **H-N4** `README.md:83` y `docs/memoria.md:404`: «24,5 % de eventos con país» sin fecha; es la cifra del 2026-11-15 (la guía sí la fecha, `:50`). Cambia con el tiempo porque el productor sigue ingiriendo.
- **H-N5** `README.md:267`: afirma que el panel «conserva la última lectura» y «se recupera solo» como comportamiento, sin aclarar que está verificado solo por código (la memoria `:364-365` y las fichas 9 y 10 sí lo dicen). Lo matiza `README.md:279` y `:112`; es solo una frase poco precisa.
- **H-N6** `README.md:23`: «`009` filtros y tabla, `010` gráficos…, `011`, `012`» usa los mismos números que `replay (009)`, `despliegue-tunel (010)`, `mediciones-costes (011)` y `pruebas-aceptacion (012)` en las filas siguientes. Confuso para el lector; no afecta a ninguna cifra.
- **H-N7** `docs/memoria.md:157` frente a `:352`: «412 pruebas unitarias y 35 de integración» (cifra de la feature del consumidor) sin fecha, junto a «829 unitarias» y «232 de integración» (2026-11-14) en §8. Son conjuntos distintos, pero no se aclara en §4.3.
- **H-N8** `docs/memoria.md:285` y `:303` y similares (`aislamiento.md`, `equipo.md`, `resultados.json`, `procedimiento.md`, `costes.md`, `indices.md`…): nombres cortos sin directorio, en contraste con las rutas completas de otras secciones. El enlace de cabecera (`evidencias/mediciones/README.md`) las localiza, así que es solo estilo. Además faltan líneas en blanco antes de `### 2.1` (`:50`), `### 4.4` (`:158`) y `## 8.` (`:350`); se renderizan bien.
- **H-N9** `docs/planificacion/01-checklist-requisitos.md:79` (B12): conserva la anotación «pasar docs/borradores/productor-live.md a la memoria)», ya hecha (`memoria.md:406-408`); y B18 (`:85`) sigue en ☐ aunque ya está en memoria §3 y README. Fuera de los tres documentos revisados.
- **H-N10** `docs/evidencias/despliegue-tunel/H3_cloudflared_tunel.png`: la captura muestra el nombre del equipo (`PC-SAMUEL`) y el ID del túnel. No es un secreto (el token no sale), pero es un dato personal en el repositorio; misma categoría que el dominio con el nombre del alumno, decisión suya.

## 7. Qué sigue abierto

De verdad queda esto:

1. **Del alumno: grabar el vídeo de 5 minutos** siguiendo el guion de `docs/rubrica-y-guia-video.md` (con las pruebas 9 y 10 en vivo y la demo H4, con el PC sin suspender, los contenedores y `cloudflared` encendidos) y **poner el enlace de YouTube** en `README.md:5`, sustituyendo el marcador PENDIENTE.
2. **Del alumno: ensayo con cronómetro** del guion de 5:00, que suma 5:00 exactos pero con esperas de las pruebas 9 y 10 (unos 75 s cada una) que hay que acortar al montar.
3. **Corrección de documentación** (corrector): H-N1 (auditoría desfasada frente al README) y H-N2 (versionar el informe enlazado en `README.md:28`). Los menores H-N3 a H-N10 son opcionales.
4. **Limitaciones ya aceptadas** (no son hallazgos): clon limpio (A2, M3) sin repetir; H3 con captura de «Resumen»; sin captura nueva del panel con los filtros de §6; capturas de las pruebas 9 y 10 parciales (con demostración en el vídeo).
