# Plan de implementación: Pruebas de aceptación (012)

**Rama**: `012-pruebas-aceptacion` | **Spec**: [spec.md](spec.md) | **Fecha**: 2026-11-14
**Checklist**: tabla I (pruebas 1 a 11), G9, entregable I-resumen. El checklist no se marca (lo hace el alumno).

## Resumen

Formalizar las 11 pruebas con ficha propia, reutilizando pruebas y evidencias de 003, 004, 005, 009 y 010 (inventario real en [research.md](research.md)). Se añade un único archivo de pruebas de integración (5 pruebas puente consumidor a API para 1, 3, 4, 5, 7), la ejecución y registro de las pruebas 1 a 8 y 11, la revisión de código y plantilla de 9 y 10 (pendientes del alumno), las capturas 1, 5 y 7 si hay navegador, el resumen y la corrección de `despliegue-tunel`. Este documento es solo diseño: no contiene código, Dockerfile ni compose (constitución §19).

## Contexto técnico

- Lenguaje y pruebas: Python 3.12 en el servicio `tests` de Compose (pytest, `TempDatabase`, `request_api`); Vitest solo se lee, no se amplía.
- Almacenamiento: PostgreSQL 16 real, base temporal por prueba; `live` real solo se lee con SQL de solo lectura.
- Plataforma: Windows con Docker Compose; capturas con navegador sobre `https://observatorio.ssamuelfernandez.net/` (sin cuentas) o mock local.
- Alcance: 11 fichas y un resumen; sin fuzz, sin pruebas de carga, sin cambios de contratos, DDL, API ni panel.
- Sin `NEEDS CLARIFICATION`.

## Comprobación de la constitución

| Principio | Cumplimiento |
|---|---|
| §1 y §2 Idempotencia y versionado | Se prueba, no se cambia; se reutilizan las pruebas 2, 3, 4 y 8 |
| §5 Nulos | Prueba 5 comprueba NULL, `null` en API y ND en panel, nunca 0 |
| §6 Cuarentena | Prueba 6 reutiliza `test_quarantine.py` |
| §7 Sintéticos separados | Todo dato inyectado en `TempDatabase` o `replay`, con `synthetic-` e `is_synthetic`; huella de `live` antes y después |
| §8 Agregaciones desde el estado actual | Las pruebas puente leen `/api/estadisticas` |
| §10 Secretos | Sin credenciales en evidencias; la URL pública no lleva cuentas |
| §13 Idioma | Identificadores en inglés, docstrings y comentarios en español |
| §14 Una responsabilidad | Una prueba por caso en `test_acceptance_api.py` |
| §15 Contratos únicos | No se modifican ni se copian |
| §16 Cierre | Tests ejecutados, evidencias, `CODEMAP.md` |
| §17 Frontend sin cálculo | Solo se revisa; las capturas muestran lo que devuelve la API |
| §18 y §19 | `docs/enunciado/` intacto; una feature, sin código en el plan |

Sin violaciones; sin tabla de complejidad. Reevaluado tras el diseño: sin cambios.

## Estructura

```text
specs/012-pruebas-aceptacion/   spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md
tests/integration/test_acceptance_api.py   (nuevo, T094 a T098)
docs/evidencias/pruebas/        README.md, 00_live_antes/despues.txt, NN-<nombre>.md (11), NN_*.txt (salidas), capturas
docs/evidencias/despliegue-tunel/   solo texto de estado (README.md, prueba-09 y prueba-10)
CODEMAP.md                      filas del archivo de pruebas y de docs/evidencias/pruebas/
```

Archivos existentes que se editan solo en texto: `docs/evidencias/despliegue-tunel/README.md`, `prueba-09_cierre-tunel.md`, `prueba-10_reapertura-tunel.md`, `CODEMAP.md`.

## Diseño por bloques

1. **Pruebas puente** (T094 a T098): cada una procesa mensajes sintéticos por el consumidor real en `TempDatabase` y comprueba SQL y API a la vez (1 fila actual y recuento; cambios de agregación por país y por hora; versión tardía sin cambio; NULL a `null` sin pasar a 0; sin país contado en totales y por hora). Se escriben antes de ejecutarlas y se comprueba que pasan contra el código existente (no hay código de aplicación que implementar).
2. **Ejecución y capturas** (T099 a T104): huella de `live`, ejecución y registro de 1 a 8 y 11, capturas.
3. **Pruebas 9 y 10** (T105 a T108): revisión de código con archivo y línea, fichas con plantilla, corrección de `despliegue-tunel`. Estado: pendiente de la demostración del alumno.
4. **Fichas y resumen** (T109 a T113): 11 fichas y `README.md`.
5. **Cierre** (T114 a T117): suite completa, restaurar `consumidor-idempotente`, huella final, `CODEMAP.md`.

## Riesgos

- El panel público puede no mostrar un evento marítimo en la ventana por defecto: se filtra por «Sin país asignado» y se amplía el periodo; si no hay, plantilla.
- Sin herramienta de navegador: capturas como plantilla con huecos (no bloquea el cierre).
- Refresco de 60 s y pestaña oculta: documentados como límites de 9 y 10, no corregidos.
- La suite de integración reescribe evidencias de `consumidor-idempotente`: se restauran con `git checkout`.
