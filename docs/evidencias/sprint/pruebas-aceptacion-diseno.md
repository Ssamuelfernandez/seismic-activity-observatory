# pruebas-aceptacion — fase diseño (resumen)

Rama: 012-pruebas-aceptacion (desde main). Checklist: tabla I (1–11), G9, entregable "evidencias de las 11 pruebas".

## a) Decisiones por defecto
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Prueba 5 (ND) | SQL+API sobre TempDatabase sintético; captura del panel en modo mock etiquetado | no hay nulos reales; no tocar live | sí |
| Prueba 7 | captura del panel público filtrando «Sin país asignado» (datos reales) | evidencia real sin inyectar | sí |
| Prueba 1 | evidencia real existente (productor-live/prueba1_evento_nuevo.out) + captura real + comprobación sintética API | reutilizar | sí |
| Prueba 3 | captura = plantilla (datos sintéticos en TempDatabase, no visibles en panel público); evidencia principal SQL+pytest | no contaminar live | sí |
| Textos "verificado en vivo" de despliegue-tunel | corregir a "pendiente de demostración del alumno" (README l.17, plantillas 09/10 l.3) | no está verificado | sí |
| Límites del panel (9/10) | documentar, no corregir: refresco 60 s + timeout 15 s, sin refetchIntervalInBackground, T036 probó API local no túnel | alcance | sí |
| Aislamiento | solo TempDatabase/replay; huella de live antes/después | constitución §7 | sí |

## b) Preguntas para el alumno
Las 5 de spec.md, con decisión provisional arriba. Ninguna toca contratos.

## c) Hallazgos
1 importante (prueba 3 sin captura) corregido. Menores: 0 listados.

## d) Tareas
24 (T094–T117), 5 bloques, ninguna implementada aún. Revisión: docs/evidencias/subagentes/plan-reviewer-pruebas-aceptacion.md.

## e) Qué comprobar
Que las decisiones de arriba te parecen defendibles; en 9/10 te tocará la demostración con cloudflared.

Fase terminada.
