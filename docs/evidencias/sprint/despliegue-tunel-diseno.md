# Resumen fase diseño — despliegue-tunel (rama 010-despliegue-tunel)

Artefactos: specs/010-despliegue-tunel/{spec,plan,research,data-model,quickstart,tasks,bitacora,checklists/requirements}.md. Revisión: docs/evidencias/subagentes/plan-reviewer-despliegue-tunel.md (0 bloqueantes/importantes). Contratos, sql/001 y enunciado sin cambios (git diff vacío).

## Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| apiBaseUrl | https://observatorio-api.ssamuelfernandez.net/api (termina en /api) | client.ts concatena base + /eventos sin prefijo; hoy "/api" funciona solo por el proxy de Vite (el brief suponía que el panel añade /api) | sí |
| Variable CORS | CORS_ALLOWED_ORIGINS, orígenes exactos por comas, defecto los 2 del brief; "*" hace fallar el arranque; sin Allow-Credentials | exactitud, F9 | sí |
| Origen Netlify temporal | origen exacto del sitio por la variable, no patrón *.netlify.app | evita comodín | sí |
| Cabecera ngrok-skip-browser-warning | se mantiene permitida | la exige el contrato | sí |
| netlify.toml publish | "dist" (relativo a base=frontend); T070 corrige 02 y 03 §8.4 que dicen frontend/dist | semántica de Netlify | sí |
| Puertos | evidencia con docker compose -f compose.yaml config (ignora compose.override.yaml, que publica Postgres en 5433) | override local del alumno | sí |
| Dev local | con config.json público, npm run dev deja de usar el proxy; se documenta poner "/api" solo en local sin commitear (pregunta 7) | alcance | sí |
| .gitignore | añade credenciales de cloudflared (FR-016) | secretos fuera del repo | sí |

## Preguntas para el alumno (7, todas con decisión provisional en spec.md)
1 ediciones de código en implementación; 2 contracts/api.md y enunciado mencionan ngrok y no se editan (README dirá "ngrok u otro equivalente"); 3 texto reformulado de H3, G13, F9, H2 (no se edita el checklist); 4 03 §4 llama a la feature 015, la carpeta real es 010; 5 compose.override.yaml; 6 dominio sin www; 7 dev local con config.json.
IDs: el brief citaba F9, F10, F5, H3; en el checklist real F10 y F5 ya están [x] (se re-evidencian) y el resto son G13, H1–H4, pruebas 9 y 10.

## Tareas
14 activas T059–T072 en 5 bloques (CORS 4, panel y build 3, exposición 2, documentación 3, cierre 2). Pasos manuales P1–P9 del alumno, no son tareas.
Límites conocidos: 500 sin cabeceras CORS; preflight POST devuelve 400.

Fase terminada.
