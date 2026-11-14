# Prueba 11: reproducción histórica

## 1. Objetivo y requisito

Tabla I, prueba 11 (J1 a J8). La reproducción histórica escribe solo en el esquema `replay`, no toca `live` y los duplicados y revisiones controlados dan 22 eventos actuales, 24 versiones y 0 en cuarentena. Constitución §7. FR-004, SC-003.

## 2. Procedimiento

1. Huella de `live` antes (`T052_antes.out`: recuentos y md5).
2. Reproducir la selección de 2025: 26 mensajes por el topic `earthquakes.replay` (duplicados, 1 versión posterior y 1 tardía controlados).
3. Contar en `replay` y volver a medir `live`.
4. Repetir la reproducción y comprobar que los recuentos y `replay_at` no cambian.
5. API con `mode=replay` y panel con el banner «REPRODUCCIÓN».

## 3. Esperado

26 mensajes a 22 / 24 / 0 en `replay`; `live` idéntico (mismo recuento y md5); la API devuelve `metadata.mode = "replay"` y el panel muestra «REPRODUCCIÓN».

## 4. Observado

- **Replay real (2026-11-12, `T053_despues.out`)**: `replay` con `current` 22, `version` 24, `quarantine` 0. `live` en 211 / 211 / 0 con md5 de `current` `5a51932f2d25...`, igual que antes (SC-002 de `replay/README.md`; productor live parado). Duración del replay 51 s.
- **Repetición (`T054_repeticion.out`)**: `live` otra vez 211 / 211 / 0 con los mismos md5 y `replay` 22 / 24 / 0; README de `replay`: SC-006 cumple.
- **Panel (`T056_panel.md`, 2026-11-12)**: banner «REPRODUCCIÓN» y «DATOS SINTÉTICOS», total 22 (API); en «En vivo», sin banner ni eventos de replay.
- **Ejecución 2026-11-14**: `test_replay_consumer.py` y `test_api_replay_real.py`: 8 passed (`11_pytest.txt`, 0 fallos), incluidos los 26 mensajes a 22 / 24 / 0 en `replay` y nada en `live`.
- **Huella de `live` 2026-11-14 (`00_live_antes.txt`)**: 0 sintéticos, `current_event` 18855, md5 de sintéticos `d41d8cd98f00b204e9800998ecf8427e` (md5 de la cadena vacía). El recuento total sube porque el productor sigue ingiriendo; lo que no debe cambiar es el recuento y el md5 de sintéticos.

## 5. Evidencia

- [`../replay/README.md`](../replay/README.md).
- [`../replay/T052_antes.out`](../replay/T052_antes.out), [`../replay/T053_despues.out`](../replay/T053_despues.out), [`../replay/T054_repeticion.out`](../replay/T054_repeticion.out).
- [`../replay/T055_comprobacion.txt`](../replay/T055_comprobacion.txt), [`../replay/T055_eventos_replay.json`](../replay/T055_eventos_replay.json).
- Capturas T056: [`../replay/T056_reproduccion.png`](../replay/T056_reproduccion.png), [`../replay/T056_en_vivo.png`](../replay/T056_en_vivo.png) y [`../replay/T056_panel.md`](../replay/T056_panel.md).
- [`11_pytest.txt`](11_pytest.txt) y [`00_live_antes.txt`](00_live_antes.txt).

## 6. Cómo repetir y estado

```
MSYS_NO_PATHCONV=1 docker compose --profile test run --rm tests pytest tests/integration/test_replay_consumer.py tests/integration/test_api_replay_real.py -q
```

La reproducción real con contenedores está descrita en `../replay/README.md` (sección «Replay» del README raíz).

**Estado: Observada** (replay real con datos de 2025, marcados como sintéticos en el esquema `replay`).
