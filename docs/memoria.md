# Memoria — Observatorio de actividad sísmica

## 1. Objetivo, flujo de datos y alcance
## 2. Diccionario de datos

Fuente: feed `all_day.geojson` de USGS, según `docs/evidencias/f1/explore_usgs_salida.txt` (210 eventos). Los tiempos vienen en milisegundos Unix UTC y se convierten a UTC conservando el valor original. Los nulos no se rellenan con 0 y las magnitudes o profundidades negativas no se rechazan por serlo.

| Campo | Significado | Tipo / unidad | Si falta |
|---|---|---|---|
| `id` (raíz del Feature) | Identificador del evento (p. ej. `ci41570768`). Es único en la muestra (0 duplicados). | Texto | No faltó en la muestra (0 nulos). Un evento sin id es inválido y va a cuarentena. |
| `time` | Instante de origen del sismo. | Entero, milisegundos Unix (UTC) | No faltó (210/210). Un evento sin tiempo es inválido y va a cuarentena. |
| `updated` | Última actualización del evento. En la muestra nunca es anterior a `time`. | Entero, milisegundos Unix (UTC) | No faltó (210/210). Sirve para decidir qué versión es la más reciente. |
| `mag` | Magnitud del sismo. | Decimal, sin unidad (escala según `magType`) | No faltó en la muestra, pero el feed puede traerla nula: se guarda NULL, nunca 0. Hay un valor negativo (-0,06) y es válido. |
| `magType` | Tipo de escala de la magnitud. Valores vistos: `ml`, `md`, `mb`, `mww`, `mwr`. | Texto | No faltó (210/210); por confirmar su comportamiento si falta. |
| `place` | Descripción textual del lugar (p. ej. "3 km WSW of Anza, CA"). | Texto | No faltó (210/210). No se usa para obtener el país. |
| `type` | Tipo de evento. En la muestra todos son `earthquake`. | Texto | No faltó (210/210). Otros valores posibles: por confirmar. |
| `status` | Estado de revisión del evento. Valor visto: `automatic`; otros valores: por confirmar. | Texto | No faltó (210/210). |
| `coordinates[2]` (profundidad) | Profundidad del foco, tercera coordenada de la geometría. Hay 2 valores negativos (mínimo -0,18), válidos. | Decimal, kilómetros (unidad por confirmar con la documentación de USGS) | No faltó (0 nulos). Si falta se guarda NULL, nunca 0. |
## 3. Procedencia y registro de consultas
## 4. Calidad
## 5. Modelo conceptual, lógico y físico
## 6. Análisis y conclusiones
## 7. Complejidad, mediciones y costes
## 8. Evidencias de las 11 pruebas
## 9. Reproducción histórica
## 10. Limitaciones