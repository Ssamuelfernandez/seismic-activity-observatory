# Bitácora — 007-api

| fase | paso | hallazgos | corrección | estado |
|------|------|-----------|------------|--------|
| diseno | specify + clarify | P1 (CORS/F9), P2 (rango replay), P3 (variables) como decisiones provisionales | — | cerrado |
| diseno | plan + tasks + analyze | /openapi.json expuesto, httpx fuera del lock, orden de ApiError, F1–F11 vs F9 | corregidos por el disenador | cerrado |
| diseno | revisión plan-reviewer | sin bloqueantes ni importantes | no hace falta ronda de corrección | cerrado |
| implementar | bloque 1 (T001–T005) | verificador: sin hallazgos | — | verificado |
| implementar | bloque 2 (T006–T011) | verificador: sin hallazgos; límite: cursor falsificado con t fuera de rango da 500 | — | verificado |
| implementar | bloque 3 (T012–T016) | verificador: sin hallazgos | — | verificado |
| implementar | bloque 4 (T017–T020) | verificador: sin hallazgos | — | verificado |
| implementar | bloque 5 (T021–T025) | verificador: sin hallazgos | — | verificado |
| cierre | límite conocido | cursor falsificado con `t` fuera de rango da 500 | no se corrige (fuera de alcance) | abierto |
| cierre | límite conocido | cursor falsificado con NUL en el id da 503 | no se corrige (fuera de alcance) | abierto |
| cierre | límite conocido | `by_hour` sin tope en rangos enormes | no se corrige (fuera de alcance) | abierto |
| cierre | límite conocido | `OPTIONS` responde 405 hasta la feature de despliegue (CORS, P1) | se resuelve en despliegue | abierto |
| cierre | límite conocido | un error SQL imprevisto sale como 503, no como 500 | no se corrige (fuera de alcance) | abierto |
| cierre | aviso de commit | la suite de integración reescribe `docs/evidencias/consumidor-idempotente/`; esos archivos se excluyen del commit; los `geografia_*` e `historico_*` sin seguimiento son de features anteriores | excluir del commit | abierto |
