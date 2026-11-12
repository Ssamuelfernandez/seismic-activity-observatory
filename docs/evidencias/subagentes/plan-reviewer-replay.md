Revisión de specs/009-replay: no hay hallazgos bloqueantes ni importantes.

- Cobertura: F9, J1–J8, G10, F12, G12 (metadata.mode) y prueba 11 tienen tarea y prueba en tasks.md. Recuentos coherentes: 26 mensajes, 22/24/0, 2 reenvíos, 1 versión posterior, 1 tardía.
- Contratos: plan.md los cita sin copiarlos ni cambiarlos. KAFKA_CONSUMER_TOPICS va en specs/002-infra-compose/contracts/config.md (no es de 001). Sin cambios en sql/ ni docs/enunciado/.
- Constitución: comprobadas §1–§3, §5, §7, §9, §10, §12–§17 y §19; sin contradicciones. §16: T057/T058 cubren pruebas, evidencia, CODEMAP y README. §19: T058 espera revisión sin commits.
- Alcance: 18 tareas en 5 bloques (tope 25/5). Sin servicios nuevos; panel solo si T056 lo exige.
- Orden de tareas correcto. Sin TBD; las 5 preguntas del alumno tienen respuesta provisional (D1–D11).

Límites conocidos:
- El bloque controlado tiene 6 mensajes y la FAQ 12 tiene 5; el sexto ejercita "versión antigua tardía no vista antes". Hay que saber explicarlo en la defensa.
- La cabecera de spec.md sigue en "Status: Draft".
- La spec dice que el consumidor "registra" reenvíos/posteriores/tardías y T053 lo comprueba en el log; esas métricas deben existir ya en el consumidor, si no T053 fallaría ahí.

Veredicto: Listo para tu revisión
