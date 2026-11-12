# mediciones-costes — fase diseno (resumen)

Rama 011-mediciones-costes (desde main; 03 §4 la numera 016, carpeta real 011). Checklist: K1–K7, E6 (K8 fuera).

**a) Decisiones por defecto**
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Carpeta de scripts | scripts/benchmarks/, tests en tests/scripts/ | CODEMAP | sí |
| Memoria | tracemalloc, sin psutil | constitución §11, sin dependencias nuevas | sí |
| Dónde corre | servicio `tests` con admin; esquema `bench` en la base del stack | roles de servicio no crean esquemas; `DROP SCHEMA` en finally + comprobación | sí |
| Estructura bench | `LIKE live.current_event INCLUDING DEFAULTS`, sin constraints ni índices | CHECK de source rechazaría sintéticos; medir sin índice | sí |
| Estadística | N=15 (mín. 3), mediana e IQR, calentamiento descartado, tiempo y memoria en pasadas separadas | tracemalloc distorsiona el tiempo | sí |
| Presupuesto | 90 s por combinación | bucle ingenuo a 100.000 | sí |
| Q3 | dos umbrales (mag>=4 y p99) | semilla M>=4 haría trivial el veredicto | sí |
| Índices | veredicto solo como recomendación, sin editar DDL/contrato | alcance | sí |
| compose.yaml | único cambio previsto: montaje de escritura de docs/evidencias/mediciones en `tests` | guardar resultados | sí |

**b) Preguntas para el alumno** (6, todas con decisión provisional): dónde se ejecuta; psutil (no); bench en la base del stack; veredicto de índices; stack en marcha; presupuesto con N reducida.

**c) Hallazgos**: plan-reviewer sin bloqueantes ni importantes (informe en docs/evidencias/subagentes/plan-reviewer-mediciones-costes.md). Menores: 0 listados. Límites: corrida completa ~1 h; prueba de `compose config --services` con perfiles por comprobar; costes dependen de datos del alumno.

**d) Tareas**: 21 (T073–T093), 5 bloques, cada una con prueba e IDs. Sin código.

**e) Comprobar**: las 6 decisiones provisionales; campos «PENDIENTE (alumno)» (modelo/potencia del PC, horas, tarifas).

Fase terminada.
