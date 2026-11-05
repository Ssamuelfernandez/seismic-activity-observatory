# geografia-pais — fase implementar (resumen)

**Decisiones por defecto**
| pregunta | decisión | motivo | ¿defenderla? |
|---|---|---|---|
| Geometrías inválidas (USA, SDN con autointersección) | No se validan; solo se rechazan las vacías; sin buffer(0) | Validar bloquearía el arranque con el catálogo real; el archivo se usa tal cual | Sí (research.md D6 actualizado) |
| Evidencia del servicio tests va a docs/evidencias/consumidor-idempotente (montaje compose) | No tocar compose.yaml; mover geografia_* a mano y restaurar archivos de 003 | Fuera de alcance | No |
| `.env` creado desde `.env.example` (ignorado por git) para construir imágenes | Solo claves de ejemplo | Necesario para docker compose build | No |
| T023–T025 (docs y comprobaciones finales) | Se hacen en la fase cierre con doc-keeper | feature.md: cierre = doc-keeper | No |

**Preguntas para el alumno**: ninguna.

**Hallazgos**: 0 bloqueantes/importantes en los 4 bloques verificados. Límites conocidos: USA/SDN con autointersecciones menores; si start_consumer falla tras abrir el pool, no se cierra explícitamente (el proceso termina); `uv` requiere UV_PYTHON=3.12 en esta máquina (.python-version pide 3.12.16); uv.lock pasa a revision 5.

**Tareas**: T001–T022 verificadas (unitarias 534 passed; integración 73 passed; verify_consumer geo 16/16). Pendientes T023–T025 (documentación y comprobaciones finales, en cierre). Evidencia clave: docs/evidencias/geografia-pais/ (geo_real_day.out: 181 eventos, 153 con país, 28 sin país; geografia_prueba7.out; geografia_catalogo.out).

**Qué debe comprobar el alumno**: regla de frontera (borde incluido) y empates (ADM0_A3 menor); NULL = sin país; 177 países únicos.

Fase terminada.
