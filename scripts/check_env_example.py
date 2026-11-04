"""Comprueba que `.env.example` coincide con las variables que usan compose.yaml y el código (A10).

Reglas:
  1. Las variables que `compose.yaml` interpola con ${NOMBRE...} son exactamente las claves de .env.example.
  2. Toda variable que el código lee con read_str/read_int está definida en el bloque `environment:`
     de algún servicio de compose.yaml.
  3. .env.example no contiene secretos reales: las contraseñas llevan el prefijo de ejemplo.

Uso: python scripts/check_env_example.py   (código de salida 0 si todo coincide)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_DIRS = ("common", "producer", "consumer", "api")
EXAMPLE_PASSWORD_PREFIX = "cambia-esta-clave"

INTERPOLATION = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")
ENV_KEY = re.compile(r"^\s{2,}([A-Z][A-Z0-9_]*):", re.MULTILINE)
CODE_READ = re.compile(r"""read_(?:str|int)\(\s*["']([A-Z][A-Z0-9_]*)["']""")


def read_example_keys(path: Path) -> dict[str, str]:
    """Devuelve las variables de .env.example con su valor."""
    pairs = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            pairs[key.strip()] = value.strip()
    return pairs


def read_code_variables() -> set[str]:
    """Devuelve los nombres de variable que lee el código Python de los servicios."""
    names: set[str] = set()
    for directory in CODE_DIRS:
        for file in (ROOT / directory).rglob("*.py"):
            names |= set(CODE_READ.findall(file.read_text(encoding="utf-8")))
    return names


def main() -> int:
    """Aplica las reglas y devuelve el código de salida."""
    compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    example = read_example_keys(ROOT / ".env.example")
    problems: list[str] = []

    interpolated = set(INTERPOLATION.findall(compose_text))
    for name in sorted(interpolated - set(example)):
        problems.append(f"compose.yaml usa ${{{name}}} pero falta en .env.example")
    for name in sorted(set(example) - interpolated):
        problems.append(f"{name} está en .env.example pero compose.yaml no lo usa")

    compose_env_keys = set(ENV_KEY.findall(compose_text))
    for name in sorted(read_code_variables() - compose_env_keys):
        problems.append(f"el código lee {name} pero ningún servicio de compose.yaml lo define")

    for name, value in example.items():
        if "PASSWORD" in name and not value.startswith(EXAMPLE_PASSWORD_PREFIX):
            problems.append(f"{name} no parece un valor de ejemplo (debe empezar por '{EXAMPLE_PASSWORD_PREFIX}')")

    for problem in problems:
        print(f"FAIL  {problem}")
    if not problems:
        print(f"PASS  .env.example coincide: {len(example)} variables, "
              f"{len(read_code_variables())} leídas por el código, sin secretos reales.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
