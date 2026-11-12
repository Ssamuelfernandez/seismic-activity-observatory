"""Pruebas sin Docker de `netlify.toml` (T063): valores de despliegue y coherencia con `.nvmrc`."""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load() -> dict:
    """Qué hace: lee y parsea `netlify.toml` de la raíz. Devuelve: el diccionario del TOML."""
    return tomllib.loads((ROOT / "netlify.toml").read_text(encoding="utf-8"))


def test_build_section_has_the_expected_values() -> None:
    build = _load()["build"]
    assert build["base"] == "frontend"
    assert build["command"] == "npm run build"
    assert build["publish"] == "dist"


def test_spa_redirect_is_a_200_rewrite_to_index() -> None:
    redirects = _load()["redirects"]
    assert {"from": "/*", "to": "/index.html", "status": 200} in redirects


def test_node_version_matches_nvmrc() -> None:
    nvmrc = (ROOT / "frontend" / ".nvmrc").read_text(encoding="utf-8").strip()
    assert _load()["build"]["environment"]["NODE_VERSION"] == nvmrc == "24.18.0"
