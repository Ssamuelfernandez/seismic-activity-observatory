# Evidencias de mediciones-costes (011)

Datos de `bench` SINTÉTICO (semilla 20251113, esquema temporal eliminado al terminar); lo REAL se indica. Procedimiento: `procedimiento.md`. Borrador del README: `docs/borradores/mediciones-costes.md`.

## Índice

| Archivo | Contenido |
|---|---|
| `procedimiento.md` | comandos, orden, requisitos, tiempo real (117 s) y fuentes de ruido |
| `resultados.json`, `tablas.md`, `planes/` (60 planes `EXPLAIN`) | las 102 mediciones con id citable y sus planes |
| `teoria_vs_observado.md` | K1: teoría frente a observado de las 3 operaciones |
| `indices.md` | E6: veredictos y recomendaciones (PROPUESTA al alumno) |
| `almacenamiento.md`, `transferencia.md`, `costes.md`, `equipo.md` | tamaños y bytes MEDIDOS; costes, tarifas y equipo anfitrión aportados por el alumno (SUPUESTO/ESTIMADO, en efectivo o imputado); cuotas de servicios con un dato aún por verificar |
| `escalado.md` | K5 y K7: razonamiento a 10^8 filas (SUPUESTO) y propuestas |
| `aislamiento.md` | antes/después de la corrida: 0 filas de bench fuera de `bench` |
| `T073_*` a `T090_*`, `bloque1_unitarias_completas.txt` | salidas de pruebas y de la corrida por tarea |
| `T092_cifras_y_enlace.txt` | comprobación de cifras del borrador y del enlace del README |
| `T093_unitarias_completas.txt`, `T093_integracion_completa.txt`, `T093_comprobaciones.txt` | cierre: suites completas, servicios de Compose, `git diff --stat`, `to_regnamespace` |
| `T094_integracion_completa_imagen_nueva.txt` | suite de integración completa del servicio `tests` con la imagen reconstruida (227 pasan, sin errores) |

## Veredicto SC-001 a SC-007

| SC | Veredicto | Evidencia |
|---|---|---|
| SC-001 | Cumplido | `tablas.md` (3 tamaños, pares lista/`dict`, sin/con índice, Q2, Q3, Q4); `planes/`; `T087_corrida.txt` (102 mediciones) |
| SC-002 | Cumplido | `tablas.md` (mediana, IQR, N real, unidad, memoria); `equipo.md` leído de la máquina; modelo del anfitrión y potencia (100 W, SUPUESTO) aportados por el alumno; límites de CPU y memoria de los contenedores leídos con `docker inspect` |
| SC-003 | Cumplido | `aislamiento.md` (violaciones: ninguna); `T087_corrida.txt`; `T093_comprobaciones.txt` (`to_regnamespace('bench')` NULL, 0 filas de bench, 18302) |
| SC-004 | Cumplido | `tablas.md` y documentos con etiqueta SINTÉTICO; `T092_cifras_y_enlace.txt`; prueba de la semilla real (archivos verificados por sha256, eventos únicos) en `T076_seed_sin_docker.txt` |
| SC-005 | Cumplido | `costes.md` (hardware, electricidad, almacenamiento, transferencia, mantenimiento, dominio y desarrollo, con fórmula, origen y naturaleza efectivo/imputado; tabla resumen mensual); queda por verificar en el panel de Netlify el límite que aplica a la cuenta y su consecuencia |
| SC-006 | Cumplido | `escalado.md` (6 puntos de razonamiento, 8 propuestas con id); `T088-T090_comprobaciones.txt` |
| SC-007 | Parcial | `T087_corrida.txt` y `procedimiento.md`; falta repetir desde un clon limpio, y las suites: ver abajo |

Suites del cierre: 832 pruebas sin Docker en verde (`T093_unitarias_completas.txt`). En el servicio `tests`, con la imagen reconstruida, **227 pruebas de integración en verde y ningún error de recogida** (`T094_integracion_completa_imagen_nueva.txt`). La corrida anterior (`T093_integracion_completa.txt`, imagen antigua) tenía el mismo recuento de 227 más 1 error de recogida en `tests/common/test_api_config.py` por la imagen desactualizada; está resuelto.
