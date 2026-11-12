# Borrador: Complejidad, mediciones y costes (README §7; K1–K7, E6)

Material para el README y la defensa. Cifras copiadas de `docs/evidencias/mediciones/` (el origen de cada una está en `teoria_vs_observado.md`, `escalado.md`, `indices.md`, `almacenamiento.md`, `transferencia.md`, `costes.md` y `tablas.md`). Las cifras de `bench` son SINTÉTICO (esquema temporal `bench`, semilla 20251113, eliminado al terminar); las de las tablas reales llevan REAL. Los tiempos son milisegundos (mediana de 15 repeticiones) medidos en la VM de Docker Desktop, no en el equipo anfitrión. Tamaños medidos: 1.000, 10.000 y 100.000 filas; 102 mediciones. Procedimiento: `docs/evidencias/mediciones/procedimiento.md`.

## Operaciones medidas

| Operación | Estrategias comparadas | Teoría (medio / peor) |
|---|---|---|
| a. Búsqueda por id | lista, `dict`, Postgres sin índice y con índice | lista O(n); `dict` O(1); `Seq Scan` O(n); B-tree O(log n) |
| b. Integración geográfica (punto en 177 polígonos) | bucle ingenuo y `STRtree` | lineal en puntos; el `STRtree` reduce los polígonos candidatos |
| c. Agregación por ventanas (Q2, Q3, Q4 de `db-schema.md` §4) | sin índice y con índice | `Seq Scan` O(n); con índice depende de las filas devueltas |

## Equipo (REAL, leído de la máquina)

AMD Ryzen 9 9900X, 12 núcleos físicos y 24 lógicos, 15,17 GiB de RAM, PostgreSQL 16.15, Python 3.12.16. Es la VM de Docker Desktop (WSL2). Modelo y potencia del equipo anfitrión: PENDIENTE (alumno).

## Resultados clave (SINTÉTICO, 100.000 filas)

| Operación | Medido |
|---|---|
| Búsqueda por id ausente | lista 2,058552 ms; `dict` 0,000062 ms; Postgres sin índice 4,799034 ms; con índice 0,146670 ms |
| Construir el `dict` | 6,512775 ms y 5632,09 KiB de pico |
| Geografía, puntos mezclados | bucle ingenuo 1.919,619815 ms; `STRtree` 610,28769 ms; 0 de 100000 puntos con resultado distinto entre métodos |
| Q2 (un mes) | 5,358898 ms sin índice; 0,182825 ms con `ix_current_event_country_time` |
| Q4 (un día) | 3,526351 ms sin índice; 0,375212 ms con `ix_current_event_time` |
| Q4 (toda la tabla) | 17,246617 ms sin índice; 17,316232 ms con índice |

Teoría frente a observado: a 1.000 filas el `Seq Scan` no es peor que el índice, porque domina la ida y vuelta al servidor; el índice parece constante, compatible con O(log n) pero sin demostrarlo; la lista crece algo más deprisa que lineal en este rango (`teoria_vs_observado.md`).

## Veredictos de índices (E6, PROPUESTA al alumno; SINTÉTICO)

No se edita el DDL ni el contrato; decide el alumno.

- `ix_current_event_country_time`: justificado en los 6 casos de Q2.
- `ix_current_event_time`: justificado para un día a 10.000 y 100.000 filas; no concluyente a 1.000; no justificado con la ventana de toda la tabla.
- `ix_current_event_mag`: depende del umbral y del tamaño; `mag >= 4` selecciona casi todas las filas (selectividad 0,9458) y mejora de 5,956245 a 4,00266 ms solo a 100.000 filas; en la base real (REAL) tiene 9 lecturas y 560,0 KiB. Ni conservarlo ni descartarlo queda demostrado.

## Tamaños

- `bench` con los 4 índices (SINTÉTICO): 363,2 bytes por fila a 100.000 filas (466,9 a 1.000 y 398,1 a 10.000).
- Tablas reales (REAL): `live.current_event` 475,2 bytes por fila; `live.event_version` 1.090,3 bytes por fila; base completa 47160343 bytes.
- Transferencia (REAL): 109996 bytes por visita (eventos 107162, estadísticas 2762, salud 72).

## Costes

Solo se mide el almacenamiento (0,0439215 GiB, MEDIDO) y los bytes por visita (0,000102442 GiB, MEDIDO). El resto (hardware, electricidad, tarifas, visitas, mantenimiento, horas de desarrollo y límites de las cuotas gratuitas de Netlify y Cloudflare Tunnel) es SUPUESTO y está PENDIENTE (alumno): mientras falte una entrada el resultado es «no calculable», nunca 0. Una cuota gratuita no es coste cero: superar el límite puede generar un cobro.

## Razonamiento a 100 millones de filas (SUPUESTO, extrapolado)

Se parte de cifras medidas hasta 100.000 filas; no se midió 10^8.

1. Almacenamiento: 363,2 bytes por fila de `bench` darían 33,8 GiB con índices; `live.event_version` con 1.090,3 bytes por fila, 101,5 GiB.
2. Coste lineal: la integración geográfica con `STRtree` serían 10,2 min y con bucle ingenuo 32 min; sin índice, la búsqueda por id pasa de 0,146670 ms con índice a unos 4.799 ms.
3. Particionado por `event_time`: con selectividad 0,0184, una ventana de un día leería 54 veces menos filas con poda; obliga a cambiar la clave primaria, así que toca el contrato (decisión del alumno).
4. Índices: se conservan los que bajan una consulta usada; los índices de `bench` a 100.000 filas, escalados, ocupan entre 2,1 y 4,6 GiB cada uno.
5. Lotes: una transacción por mensaje serían 4,0 h solo de ida y vuelta; con lotes de 1.000, 14,5 s.
6. Varios consumidores: con 12 consumidores la integración geográfica bajaría a 51 s; hacen falta al menos tantas particiones como consumidores (cambio de contrato, decisión del alumno).

## Pendiente del alumno

Rellenar las entradas PENDIENTE (alumno) de `costes.md`, `transferencia.md` (visitas por mes) y `equipo.md`; decidir sobre los índices y las propuestas de `escalado.md`.
