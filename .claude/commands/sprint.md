---
description: "Modo sprint: ejecuta una feature completa (diseno, implementar, cierre) con el supervisor tomando las decisiones entre fases; commits en la rama de la feature, sin merge ni push"
argument-hint: <nombre-feature> <brief con tope de tareas>
---

Eres el ORQUESTADOR en modo sprint. Argumentos: $ARGUMENTS

Formato: `<nombre-feature> <brief>`. El brief debe incluir un tope de tareas; si no lo trae, aplica máximo 25.

## Autorización expresa del alumno (válida solo para esta ejecución)

El alumno autoriza, en modo sprint y en la rama de la feature:
- `git commit` al final de cada fase, sin atribución a Claude, sin `--no-verify`, sin tocar `.git/hooks`;
- crear la rama de la feature desde la rama actual (ramas apiladas, sin merge).

NO autoriza: `merge`, `push`, `rebase`, `reset`, `stash`, cambiar a otra rama, `down -v` fuera de la verificación del último bloque, ni tocar contratos, `sql/001_schema.sql` o `docs/enunciado/`.

## Procedimiento

1. Lee `.claude/commands/feature.md` y sigue sus reglas, su criterio de proporcionalidad y la descripción de cada fase. Ahí está cómo se hace cada fase; aquí solo cambia qué pasa entre fases.
2. Ejecuta las fases en orden: `diseno` → `implementar` → `cierre`. Al terminar cada una **no te detengas**: haz esto:
   a) Guarda el resumen final de la fase tal cual en `docs/evidencias/sprint/<feature>-<fase>.md`.
   b) Lanza el agente `supervisor` indicándole esa ruta. Te devuelve VEREDICTO, decisiones e instrucciones.
   c) Si el veredicto es **ESCALAR**: escribe `docs/evidencias/sprint/estado.md` (feature, fase, motivo, qué falta), haz el commit del estado actual si el árbol lo permite, y PARA entregando la pregunta al alumno.
   d) Si es **CONTINUAR**: aplica las instrucciones del supervisor **una sola vez** con el agente que indique (`disenador`, `corrector` o `doc-keeper`), sin segunda revisión.
   e) Antes del commit comprueba `git status --short`: si aparece `.env`, claves o archivos grandes de datos, PARA. Haz el commit con un mensaje corto (`docs: diseño de <feature>`, `feat: <feature>`, `docs: cierre de <feature>`), sin atribución.
   f) Actualiza `docs/evidencias/sprint/estado.md` con la fase terminada, para que una sesión nueva pueda reanudar.
3. Si es una **reanudación** (existe `estado.md` de esta feature), retoma desde la primera fase no terminada, sin repetir lo ya hecho.
4. Al final de `cierre` no hagas merge ni cambies de rama: deja la rama de la feature como actual, para que la siguiente feature se apile sobre ella.

## Resumen final del sprint (máximo 25 líneas)

- Feature, rama, commits creados (hash y mensaje).
- Veredicto del supervisor en cada fase y decisiones tomadas (remite a `docs/evidencias/sprint/decisiones.md`).
- Tareas verificadas / diferidas y evidencia clave.
- Lo que el alumno debe leer antes de defender: decisiones de `decisiones.md` y límites conocidos.
- IDs del checklist con evidencia, para marcar.
- Estado: COMPLETA | ESCALADA (con la pregunta).
