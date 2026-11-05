# Bitácora — 008-panel-base-mock

| fase | paso | hallazgos | corrección | estado |
|------|------|-----------|------------|--------|
| diseno | preflight | árbol limpio; rama 008-panel-base-mock creada desde main | — | cerrado |
| diseno | specify + clarify | D1 mapa, D2 store, D3 src/ sin fijar (pendientes del alumno); P1-P5 abiertas; G17 añadido a checklist y 03 | — | cerrado |
| diseno | plan + tasks + analyze | plan, research, data-model, quickstart y 21 tareas en 5 bloques; D1-D3 siguen pendientes (solo T007 y T015 dependen de D1); corregidos 3 textos en el análisis | aplicada | abierto: espera decisiones del alumno |
| diseno | plan + tasks + analyze | D1-D3 siguen pendientes; 21 tareas en 5 bloques; 3 textos corregidos por analyze | corregidos por el disenador | cerrado |
| diseno | revisión plan-reviewer | sin bloqueantes ni importantes; límite: versiones no verificadas por el revisor (el disenador las comprobó con npm view) | no hace falta ronda de corrección | cerrado |
| diseno | respuestas del alumno | 2026-11-05: D2 Zustand, D3 opción C, D1 candidatas react-globe.gl y MapLibre (elección final en T007), Q1-Q5, P2, P3, P5 resueltas; TypeScript 6.0.3 (comprobado con npm view); regla de versión anterior si T001 no instala | aplicadas en spec, plan, tasks, research, data-model y checklist | cerrado |
| implementar | bloque 1 (T001–T004) | verificador: sin bloqueantes ni importantes; límites: emisión de JSON aparte en dist/ no reproducida (T009 la ejercita), dev HTTP 200 no reejecutado; aviso: npm run usa Node 20.13.1 por un paquete node en la carpeta de usuario | — | verificado |
