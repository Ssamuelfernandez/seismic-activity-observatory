# Cuadernos Jupyter

Servidor Jupyter en un contenedor de la misma red que PostgreSQL, para consultar la base desde VS Code. Es un añadido independiente: no forma parte de ninguna feature ni del pipeline.

## Preparar (una vez)

1. En `.env`, rellena `JUPYTER_TOKEN` (valor largo y aleatorio) y `DB_JUPYTER_PASSWORD`. Las dos están en `.env.example`. Para generar un valor: `python -c "import secrets; print(secrets.token_hex(24))"`.
2. Levanta el servicio (arranca también `postgres` si estaba parado):

   ```bash
   docker compose up -d --build jupyter
   ```

3. Crea el rol de solo lectura:

   ```bash
   python scripts/apply_jupyter_role.py
   ```

   Repítelo si cambias `DB_JUPYTER_PASSWORD` (y recrea el contenedor con el paso 2) o tras un `docker compose down -v`.

## Conectar VS Code

Con las extensiones de Python y Jupyter instaladas, abre un cuaderno de `notebooks/` y elige **Select Kernel > Existing Jupyter Server >** `http://localhost:8888/?token=<tu JUPYTER_TOKEN>`. Después selecciona el kernel de Python 3.

Prueba: ejecuta [`notebooks/00_prueba_conexion.ipynb`](../notebooks/00_prueba_conexion.ipynb). El código se ejecuta en el contenedor; la carpeta `notebooks/` del equipo aparece allí como `/home/jovyan/work`.

## Parar

```bash
docker compose stop jupyter
```

`docker compose down` no detiene los servicios de un perfil: para eliminar también Jupyter usa `docker compose --profile jupyter down`.

## Límites y seguridad

- El puerto se publica solo en `127.0.0.1:8888`. La constitución (regla 10) dice que solo la API se expone: por eso el servicio está en el perfil `jupyter` y `docker compose up -d` no lo arranca. No lo publiques en `0.0.0.0` ni lo metas en el túnel.
- Quien tenga el token puede ejecutar código en el contenedor, que está en la red `backend`: además de PostgreSQL alcanza Kafka (sin autenticación) y la API.
- El rol `observatory_jupyter` solo tiene `SELECT` sobre `public.country`, `public.date_dim`, `ingest.ingest_run` y las tablas `current_event`, `event_version`, `quarantine` y `exclusion` de `live` y `replay`.
- Las salidas de las celdas se guardan dentro del `.ipynb`: bórralas antes de versionar un cuaderno.
- La imagen y los paquetes tienen la versión fijada en [`jupyter/Dockerfile`](../jupyter/Dockerfile).
