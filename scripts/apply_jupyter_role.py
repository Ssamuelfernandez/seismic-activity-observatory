"""Crea o actualiza el rol de solo lectura de los cuadernos (sql/003_jupyter_role.sql).

Lee DB_JUPYTER_PASSWORD de `.env` y la entrega al contenedor de PostgreSQL como variable de
entorno, de modo que la contraseña no aparece en la línea de comandos. Requiere que el
servicio `postgres` esté en marcha.

Uso: python scripts/apply_jupyter_role.py   (código de salida 0 si el rol queda aplicado)
"""
import os
import subprocess
import sys
from pathlib import Path

from check_env_example import read_example_keys

ROOT = Path(__file__).resolve().parent.parent
PASSWORD_VARIABLE = "DB_JUPYTER_PASSWORD"
# Las variables POSTGRES_* se expanden dentro del contenedor, no en el equipo anfitrión.
PSQL_COMMAND = 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /sql/003_jupyter_role.sql'


def build_command() -> list[str]:
    """Devuelve la orden que ejecuta el script SQL; `-e NOMBRE` toma el valor del entorno."""
    return ["docker", "compose", "exec", "-T", "-e", PASSWORD_VARIABLE,
            "postgres", "sh", "-c", PSQL_COMMAND]


def main() -> int:
    """Aplica el rol y devuelve el código de salida."""
    env_file = ROOT / ".env"
    password = read_example_keys(env_file).get(PASSWORD_VARIABLE, "") if env_file.exists() else ""
    if not password:
        print(f"FAIL  Falta {PASSWORD_VARIABLE} en .env")
        return 1
    result = subprocess.run(build_command(), cwd=ROOT, env={**os.environ, PASSWORD_VARIABLE: password})
    if result.returncode == 0:
        print("PASS  Rol observatory_jupyter aplicado (solo lectura).")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
