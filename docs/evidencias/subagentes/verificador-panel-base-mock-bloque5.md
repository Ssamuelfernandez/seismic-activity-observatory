# Verificación Bloque 5 — panel-base-mock (T038, T039, T040 implementación)

Sin hallazgos bloqueantes ni importantes. Todo ejecutado por mí en copia limpia (`git ls-files --cached --others --exclude-standard`, Node 24.18.0) en `scratchpad/verif5/`.

- `npm ci` (0 vulnerabilidades), `npx tsc --noEmit` = 0, `npm run build` = 0, `npm test` = 8 archivos, 70 tests pasan (coincide con el implementador).
- Mutaciones manuales (restauradas): corte de profundidad 35 a 36 en `symbology.ts` hace fallar 2 tests; `REPLAY_START` a 2024 hace fallar 1; `numOrNull` rechazando `null` hace fallar 7; `deriveDataState` con vacío igual a error hace fallar 1. Los tests no son tautológicos. Nota: `parse.ts` es una guarda que devuelve el mismo objeto, por lo que "convertir null en 0" dentro de `numOrNull` no cambia nada observable (la mutación equivalente es rechazar null, que sí se detecta).
- `dist/`: `__MOCK_BACKEND__` y `Sintético:` sin resultados; sin JSON en `dist/assets`; `config.json` con 4 campos y `mode: "api"`; el chunk `mockUnavailable-*.js` contiene «mock no disponible en este build». SHA de `paises.geojson` (public y data/catalogo) = 6866c877...c977f. Sin `formatMadrid` ni `h3-js` en src/tests/package.json; versiones exactas, `three`, `@types/three`, `zustand` presentes; `.nvmrc` y `engines` 24.18.0.
- Dev en copia a 4300: `/`, `/config.json`, `/datos/paises.geojson` y proxy `/api/salud` dan 200 con la API real.
- Sin cambios en contratos, `docs/enunciado/`, `sql/001_schema.sql`, `api/`. Checklist `01` sin diff (ninguna marca). `_import-front/` sigue y `.gitignore` conserva su línea. Sin atribución a Claude (solo rutas de scratchpad en evidencias, que contienen la cadena del directorio de trabajo). CODEMAP: todas las rutas `frontend/…` existen; no hay "previstas" obsoletas. README raíz enlaza a `frontend/README.md`, cuyo contenido (comandos, 4 campos, `?scenario=` solo con el mock, material reutilizado con SHA, estructura, límites) es correcto.
- Límites conocidos (no bloquean): no hay capturas ni recorrido visual 375/768/1280 (pendiente del alumno, SC-007 visual, SC-010, SC-012, SC-017 visual); tasks.md T038–T040 aún sin marcar (correcto).

## Anexo: SC-001 a SC-017
| SC | Estado | Evidencia |
|---|---|---|
| SC-002, SC-015 | cumple | tests de `validateConfig` y resto pasan (70/70) |
| SC-003 | cumple | greps de `dist/` vacíos; mensaje del mock no disponible presente |
| SC-004 | cumple | cinco escenarios pasan `mock.test.ts`/`parse.test.ts`; fixture estropeado falla |
| SC-005, SC-006 | cumple (tests y código); visual pendiente | `symbology.test.ts`, mutación 35 a 36 detectada |
| SC-007 | cumple en datos; capturas pendientes | 4 combinaciones con `buildRequest` contra la API real: stats.total = metadata.total (211/211, 110/110, 71/71, 2/2) |
| SC-008 | cumple por evidencia T036; no repetido aquí (no se paran servicios) | `T036_*` |
| SC-009 | cumple | replay real: 0 eventos, total 0, sin error; `dataState` y `requests` con tests; REPLAY_START mutado se detecta |
| SC-010 | texto cumple; medición 11 px en captura pendiente | `Attribution.tsx` |
| SC-011 | cumple | `auditoria-calculos-cliente.md` existe; los recuentos restantes en `src/` van con «mostrados» |
| SC-012 | pendiente del alumno (visual) | sin navegador |
| SC-013 | cumple | greps vacíos, `three`/`@types/three` declarados |
| SC-014 | cumple | SHA coincide; README documenta origen y licencias |
| SC-016 | cumple | evidencias, README y CODEMAP; G16/G18/G13/G10 no marcados; checklist sin diff |
| SC-017 | grep cumple; capturas pendientes | `showArcs/showHexBin/showHeatmap/showMarkers` sin resultados en `src/` |

T038: verificada
T039: verificada (salvo el recorrido visual en navegador y capturas, pendientes del alumno)
T040 (parte de implementación): verificada
