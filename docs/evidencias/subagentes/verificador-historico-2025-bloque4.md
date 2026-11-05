# Verificación bloque 4 (T019-T021) historico-2025

Veredicto: T019, T020, T021 verificadas. Sin hallazgos bloqueantes ni importantes.

- Archivos: 12 usgs_2025-MM.geojson + manifest.json + 1 archivo de hueco; los 12 sha256 coinciden con el manifiesto, registros por archivo coinciden; 18302 eventos únicos por id (suma 18302, 0 duplicados); usgs_count_year=18302; total 14 MB (versionable); manifiesto `gaps` contiene usgs_gap_20251230..31 (30 registros).
- BD (consulta propia como admin, mismo script verificacion.sql): salida idéntica a docs/evidencias/historico-2025/verificacion.out: usgs_historical=18302 en current_event y event_version, quarantine=0, kafka_* no nulos=0, huella md5 igual en ambas tablas; verificacion_tras_reinicio.out idéntico.
- Logs: descarga_2025.log (unique=18302), descarga_2025_segunda.log sin ninguna petición (0 fetch_interval), carga2.out new=0 unchanged=18302 ok=true, hueco_ensayo.out con gap registrado. Sin secretos (solo coincidencia "token" del pull de Docker en build_imagen.log).
- git: contratos, sql/ y docs/enunciado sin diff; git status solo muestra lo esperado (más el accidente ajeno de consumidor-idempotente).
- Límite conocido: carga1.out ya muestra new=0; no consta la inserción inicial new=18302 (la existencia de 18302 filas y la idempotencia sí constan).
