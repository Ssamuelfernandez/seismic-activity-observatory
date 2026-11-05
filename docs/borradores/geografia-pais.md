# Apuntes: geografía y país (C9–C12)

Material para la memoria y la defensa. Cifras tomadas de `docs/evidencias/geografia-pais/`.

## Reglas

- **Frontera**: el borde cuenta como dentro (`covered_by` de Shapely, no `within`). Así un punto exactamente sobre una frontera no cae en «sin país». Lo confirma una prueba con la arista compartida de dos cuadrados.
- **Empates**: si el punto está en varios polígonos, gana el `ADM0_A3` menor en orden alfabético. Es determinista y no depende del orden del archivo ni del `STRtree` (la prueba invierte el catálogo). Se deja una línea de log `country_tie event_id=… candidates=… chosen=…`.
- **Sin polígono**: `country_id = NULL`, mostrado como «Sin país asignado». No se asigna el país más cercano ni se trata como error (enunciado; FAQ 19). El evento se guarda y cuenta.
- **Unicidad**: el catálogo `data/catalogo/paises.geojson` tiene 177 `ADM0_A3` únicos; el parseo lo comprueba antes de tocar la base y un duplicado detiene el arranque con error que nombra el código.
- **Origen del país**: solo la geometría (`lon`/`lat`), nunca el texto `place` (hay una prueba con un `place` que dice otro país).

## Resultado de la muestra real de un día

`geo_real_day.out` (feed `all_day` real guardado, sin red ni base): 181 eventos, 0 sin geometría válida, 153 con país y 28 sin país. 6 códigos distintos (USA=147, CAN=2, CHN=1, TUR=1, NIC=1, AFG=1) y ninguno fuera del catálogo. Es una muestra de un momento, no una cobertura general.

## Limitación del catálogo 110m

El catálogo es Natural Earth 1:110.000.000 (`docs/enunciado/FUENTES-Y-LICENCIAS.md`): costas y territorios pequeños pueden salir sin país aunque no sean mar abierto. La FAQ 19 pide documentar esto y no afirmar precisión cartográfica. Parte de los 28 sin país de la muestra pueden ser mar, parte simplificación; no se ha desglosado.

## Decisiones

- Shapely 2 sin GeoPandas: `STRtree` y los predicados bastan; GeoPandas arrastraría pandas a la imagen compartida.
- `type != earthquake` solo se excluye en el productor (`live.exclusion`); el consumidor no añade regla ni motivo de cuarentena, para no tocar el contrato.
- Esquema y catálogo se comprueban/cargan al arrancar; si fallan, el consumidor no consume y Compose lo reinicia.

## Límites conocidos

- Sin recálculo retroactivo: las filas anteriores solo cambian con una versión de `updated` mayor.
- USA y SDN del catálogo tienen autointersecciones menores; se usan tal cual, sin `buffer(0)`.
- Si `start_consumer` falla después de abrir el pool, el pool no se cierra explícitamente (lo cierra el fin del proceso).
- En esta máquina `uv` necesita `UV_PYTHON=3.12`, y `uv.lock` pasó a `revision 5`.
- El servicio `tests` monta `docs/evidencias/consumidor-idempotente`; la evidencia de geografía se movió a mano a `docs/evidencias/geografia-pais/`.
- Cambiar el catálogo entre arranques actualiza pero no borra filas de `public.country`; solo se comprueba que existan las tablas, no sus columnas.

## Resultados de pruebas

534 unitarias y 73 de integración sin fallos; `verify_consumer.py geo` 16/16 (catálogo 177 al primer arranque y `inserted=0 updated=0` tras reiniciar).
