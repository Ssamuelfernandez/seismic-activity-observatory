# Verificador replay, bloque 2 (T044, T045)
Prueba ejecutada: pytest -x -q -m "not integration" tests/producer tests/common/test_replay_message.py -> 38 passed.
git diff de specs/001-contratos-y-modelo/contracts/ vacio. CODEMAP actualizado (fila del bloque 2).

| Tarea | Veredicto | Comprobacion |
|---|---|---|
| T044 | verificada | run_replay publica solo con TOPIC_REPLAY (no hay referencia a TOPIC_LIVE), clave message_key(event.id), mode=replay, replay_at = clock() leido en cada intento justo antes de publish, sleep(interval) solo si no es el ultimo (25 esperas), producer.stop() en finally, reintento via retry_forever. Tests: 26 envios, replay_at creciente, orden, 25 esperas, reintento. |
| T045 | verificada | Defaults 2/chile-norte/20/data/historical; zona desconocida, ReplaySourceError y seleccion vacia -> codigo 1 sin publicar; aviso si hay menos que --count; resumen "Publicados: 26 (20 reales + 6 del bloque controlado)"; KAFKA_BOOTSTRAP_SERVERS del entorno. |

Hallazgos bloqueantes/importantes: ninguno.
Limite conocido: --interval negativo o --count <= 0 no se validan (no afecta a la defensa ni a las pruebas).
Nota: tasks.md aun tiene T044/T045 sin [x] (corresponde al orquestador).
