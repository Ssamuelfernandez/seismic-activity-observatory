# Modelo de datos: despliegue-tunel (010)

No hay tablas, columnas ni mensajes nuevos: el esquema SQL y los contratos (`specs/001-contratos-y-modelo/contracts/`) no cambian. Solo hay configuración y estructuras pequeñas en memoria.

## Configuración nueva

| Nombre | Dónde | Tipo y formato | Defecto | Validación |
|---|---|---|---|---|
| `CORS_ALLOWED_ORIGINS` | entorno de la API (`.env.example`, `compose.yaml` servicio `api`) | texto: orígenes separados por comas | `https://observatorio.ssamuelfernandez.net,http://localhost:4200` | cada elemento `http(s)://host[:puerto]`, sin barra final ni ruta; `*` y lista vacía rechazados con `ConfigError` que nombra la variable |

No es secreto. Para un origen temporal de Netlify se añade `https://<sitio>.netlify.app` a la lista y se recrea la API.

## Estructuras en memoria (puras, `common/api_config.py`)

- `parse_cors_origins(raw: str) -> tuple[str, ...]`: divide por comas, recorta espacios, ignora elementos vacíos, valida cada uno y devuelve los orígenes sin duplicados en el orden dado. Lanza `ConfigError` en los casos de la tabla.
- `load_cors_origins() -> tuple[str, ...]`: `parse_cors_origins(read_str("CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS))`. No se mete en `ApiSettings`: ese objeto se carga en `lifespan` y el middleware se monta antes (research D1).

## Configuración del panel (`frontend/public/config.json`)

| Campo | Valor entregado | Regla |
|---|---|---|
| `mode` | `"api"` | `"mock"` nunca en el sitio desplegado |
| `apiBaseUrl` | `https://observatorio-api.ssamuelfernandez.net/api` | termina en `/api`, sin barra final, sin secretos; el cliente forma `<apiBaseUrl>/eventos`, `/estadisticas`, `/salud` |
| `refreshSeconds` | `60` (sin cambio) | entero > 0 |
| `timeoutMs` | `15000` (sin cambio) | entero > 0 |

## Configuración de Netlify (`netlify.toml`, raíz)

| Clave | Valor |
|---|---|
| `build.base` | `frontend` |
| `build.command` | `npm run build` |
| `build.publish` | `dist` (relativo a `base`) |
| `build.environment.NODE_VERSION` | `24.18.0` (igual que `frontend/.nvmrc`) |
| `redirects` | `/*` → `/index.html`, estado `200` |

## Evidencia (ficheros de `docs/evidencias/despliegue-tunel/`)

| Fichero | Contenido | Quién |
|---|---|---|
| `README.md` | índice y veredicto SC-001 a SC-008 | agente |
| `T0xx_*.txt` | salida de cada prueba o comprobación | agente |
| `exposicion.md` | revisión de exposición: comando, resultado esperado y observado por fila | agente (túnel real: alumno) |
| `H1_movil.md`, `prueba-09_cierre-tunel.md`, `prueba-10_reapertura-tunel.md` | plantillas: pasos, resultado esperado, hora, hueco de captura con URL visible; marcadas «pendiente del alumno» | alumno rellena |

## Estados del túnel (para las pruebas 9 y 10)

`abierto` → (se cierra `cloudflared`) → `cerrado`: el panel recibe un fallo de red o 5xx de pasarela en el siguiente refresco, muestra aviso y la última lectura marcada como antigua → (se reabre) → `abierto`: el siguiente refresco automático recupera datos y quita el aviso, sin recargar. Todo el comportamiento del panel ya existe (`008`); aquí solo se observa.
