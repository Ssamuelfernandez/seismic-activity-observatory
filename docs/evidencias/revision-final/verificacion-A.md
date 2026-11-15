# Verificación A (T119): contraste independiente de auditoria.md

1. Recuento: 93 [OBL] en el checklist (`[OBL]` y `[OBL, EVAL]`) y 93 filas en la auditoría; `diff` de IDs vacío. Verificado.
2. Rutas: todas las citadas existen (`ls`) y están en `git ls-files` (incl. `data/historical/*`). `data/raw/`, `.env` y `compose.override.yaml` son ignorados por diseño. Verificado.
3. Muestra abierta: A1-A11 (`compose.yaml` 127.0.0.1:8000 y 0.0.0.0 en uvicorn), B1-B17, G1-G10, G13, M1-M5, C14, J, K. Ninguna fila «cumple» se apoya en plantilla (`*_captura_pendiente.md`, `H1_movil.md`, fichas 9/10 solo respaldan filas parcial/no). 0 «cumple» sin evidencia versionada.
4. Discrepancias (veredicto por fila):
   - **G2: cumple -> parcial, responsable alumno.** El checklist exige ficha y ND visibles comprobados con datos reales. `2026-11-12_panel-publico.png` muestra leyenda con «ND» pero ningún evento ND ni ficha abierta; `T026_comprobacion_simbologia.txt` es una prueba provisional de clases. La propia fila admite el hueco. Afecta a la prueba 5 y al criterio visual del vídeo.
   - **B11: cumple -> parcial, responsable 013 (T126).** El checklist pide «párrafo en memoria»; `docs/memoria.md` §10 está vacía y `README.md` (l. 278) solo resume y remite al borrador. Una fila con hueco y responsable no puede ser «cumple».
   - **C14: responsable «alumno» -> «013 (T126)»** (spec FR-003 y T126 listan C14 como texto de 013). Si el análisis de las 6 dimensiones sale del alcance, debe constar como decisión del alumno; hoy auditoría y spec se contradicen.
   - **G1, K2, K6, M2, M5, G13: se mantienen «cumple».** Los huecos anotados no afectan al requisito. G5 (7 passed, incluye `test_zero_mean_gives_null_variation`; `recent_incomplete true` real), G10 (captura con banner), B12 (`hueco_ensayo.out`) y B2/G9/A2/H1/H3/M3 (parcial) están bien clasificadas.
5. Todo parcial/no tiene responsable (alumno, 013 o T126). Verificado.
Límite conocido: M3 mezcla 013 (T126) y alumno (clon limpio, T131 diferido); se resuelve con una nota en la fila.
