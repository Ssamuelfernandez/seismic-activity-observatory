Veredicto: Listo para tu revisión. No encuentro hallazgos bloqueantes ni importantes.

Comprobado:
- **Cobertura:** K1–K7 y E6 aparecen en la spec (tabla de cobertura, FR y SC) y tienen tarea y prueba. K1 → T080–T082 y T088. K2 → T073–T075. K3 → T079 y T080. K4 → T076–T078. K5 → T089. K6 → T084–T086. K7 → T090. E6 → T079, T082, T083 y T090. K8 queda fuera y está indicado.
- **E6 y el PK:** los 4 índices de `pg_indexes` son el PK de `event_id` más `ix_current_event_time`, `ix_current_event_country_time` e `ix_current_event_mag`. El PK se mide en `op_search` y los otros tres en `op_agg`, así que E6 queda completo.
- **Contratos:** el plan cita `db-schema.md` y no los copia. La estructura de `bench` sale de `LIKE live.current_event` y los índices de `pg_indexes`. El veredicto de índices es solo una recomendación (prov. 4). El `git diff --stat` indicado está vacío.
- **Constitución:** cumple §4 (reutiliza `common/geo.py`), §7, §11 (sin `psutil` ni dependencias nuevas), §12, §14, §15, §16, §19 y §21. Los identificadores van en inglés.
- **Seguridad de `bench`:** nunca toca `live` ni `replay`, porque las escrituras se limitan a una lista cerrada con prefijo `bench.` y hay una prueba estática (T078). El esquema se crea con el rol administrador, se elimina siempre con `DROP SCHEMA … CASCADE` en `finally`, y se comprueba al final con `to_regnamespace('bench')` (T087). `--clean` solo borra un esquema con la marca del script. Las lecturas reales usan `observatory_api` con `DB_API_PASSWORD`, que el servicio `tests` ya recibe en `compose.yaml`.
- **Entorno:** `asyncpg`, `shapely` y `httpx` están fijados en `pyproject.toml`. `common` y `historical` están en la imagen, y `scripts` y `data/` se montan en `tests`.
- **Tope de tareas:** hay 21 tareas (T073–T093) en 5 bloques, dentro del máximo de 25 y 5. El orden de dependencias es coherente.
- **Alcance y cierre:** no hay tareas fuera de la spec. T092 y T093 cubren las pruebas, la evidencia en `docs/evidencias/mediciones/`, `CODEMAP.md` y el README.
- **Ambigüedad:** las 6 decisiones están adoptadas como provisionales, y `research.md` D6 fija `BUDGET_SECONDS = 90`.

Límites conocidos (una línea cada uno, no se corrigen):
- La corrida completa puede acercarse a una hora, por el bucle ingenuo a 100.000 puntos.
- La prueba de T087 sobre `docker compose config --services` depende de cómo trate Compose los servicios con perfil; conviene ejecutarla una vez para ver el resultado.
- Las cifras de costes dependen de datos que solo conoce el alumno (marcados como «PENDIENTE (alumno)»).

Decisiones del alumno: confirmar las 6 provisionales de la spec («Preguntas para el alumno»).
